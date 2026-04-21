"""
Tests for Phase 6 — run_premarket.py and run_intraday.py.

All tests are offline — no network, no disk side-effects in most cases.
File-writing tests use tmp_path to sandbox state and commit message files.
"""

import json
import os
import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from cuttingboard.regime import (
    RegimeState,
    RISK_ON, RISK_OFF, TRANSITION, CHAOTIC,
    AGGRESSIVE_LONG, DEFENSIVE_SHORT, STAY_FLAT, NEUTRAL_PREMIUM,
)
from cuttingboard.run_intraday import (
    _detect_trigger,
    _within_dedup_window,
    _load_state,
    _update_state,
    _send_alert,
    ALERT_CHAOTIC,
    ALERT_REGIME_SHIFT,
    ALERT_VIX_SPIKE,
    _DEDUP_MINUTES,
    _VIX_SPIKE_LIMIT,
)
from cuttingboard.run_premarket import _write_commit_msg, _COMMIT_MSG_PATH, _AUDIT_LOG_PATH


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc)


def _regime(
    regime=RISK_ON, posture=AGGRESSIVE_LONG,
    confidence=0.75, net_score=6,
    vix_level=14.0, vix_pct_change=-0.01,
) -> RegimeState:
    return RegimeState(
        regime=regime, posture=posture,
        confidence=confidence, net_score=net_score,
        risk_on_votes=6, risk_off_votes=0, neutral_votes=2, total_votes=8,
        vote_breakdown={}, vix_level=vix_level, vix_pct_change=vix_pct_change,
        computed_at_utc=_NOW,
    )


# ---------------------------------------------------------------------------
# run_intraday — _detect_trigger
# ---------------------------------------------------------------------------

class TestDetectTrigger:
    def test_chaotic_regime_triggers_chaotic(self):
        r = _regime(regime=CHAOTIC, posture=STAY_FLAT, confidence=0.0, net_score=0)
        assert _detect_trigger(r, {}) == ALERT_CHAOTIC

    def test_chaotic_overrides_vix_spike(self):
        # CHAOTIC + high VIX change → CHAOTIC takes priority
        r = _regime(regime=CHAOTIC, posture=STAY_FLAT, confidence=0.0,
                    vix_pct_change=0.25)
        assert _detect_trigger(r, {"last_regime": RISK_ON}) == ALERT_CHAOTIC

    def test_risk_on_to_risk_off_triggers_shift(self):
        r = _regime(regime=RISK_OFF, posture=DEFENSIVE_SHORT, net_score=-6)
        state = {"last_regime": RISK_ON}
        assert _detect_trigger(r, state) == ALERT_REGIME_SHIFT

    def test_risk_off_to_risk_on_triggers_shift(self):
        r = _regime(regime=RISK_ON, posture=AGGRESSIVE_LONG)
        state = {"last_regime": RISK_OFF}
        assert _detect_trigger(r, state) == ALERT_REGIME_SHIFT

    def test_same_regime_no_shift(self):
        r = _regime(regime=RISK_ON)
        state = {"last_regime": RISK_ON}
        assert _detect_trigger(r, state) != ALERT_REGIME_SHIFT

    def test_transition_to_risk_on_not_a_shift(self):
        # Shift only from RISK_ON ↔ RISK_OFF (not from TRANSITION)
        r = _regime(regime=RISK_ON)
        state = {"last_regime": TRANSITION}
        result = _detect_trigger(r, {})
        # No last_regime in state, so shift can't be detected
        assert result != ALERT_REGIME_SHIFT

    def test_no_last_regime_no_shift(self):
        # First run — no previous state
        r = _regime(regime=RISK_ON)
        assert _detect_trigger(r, {}) != ALERT_REGIME_SHIFT

    def test_vix_spike_triggers_vix_spike(self):
        r = _regime(vix_pct_change=_VIX_SPIKE_LIMIT + 0.01)
        assert _detect_trigger(r, {}) == ALERT_VIX_SPIKE

    def test_vix_at_threshold_triggers(self):
        r = _regime(vix_pct_change=_VIX_SPIKE_LIMIT + 0.001)
        assert _detect_trigger(r, {}) == ALERT_VIX_SPIKE

    def test_vix_below_threshold_no_trigger(self):
        r = _regime(vix_pct_change=_VIX_SPIKE_LIMIT - 0.01)
        assert _detect_trigger(r, {}) is None

    def test_normal_market_no_trigger(self):
        # RISK_ON, same regime as before, VIX calm
        r = _regime(regime=RISK_ON, vix_pct_change=-0.01)
        state = {"last_regime": RISK_ON}
        assert _detect_trigger(r, state) is None

    def test_no_state_no_trigger(self):
        r = _regime(regime=RISK_ON, vix_pct_change=-0.01)
        assert _detect_trigger(r, {}) is None

    def test_vix_pct_none_no_spike(self):
        r = _regime(vix_pct_change=None)
        assert _detect_trigger(r, {}) is None


# ---------------------------------------------------------------------------
# run_intraday — _within_dedup_window
# ---------------------------------------------------------------------------

class TestWithinDedupWindow:
    def test_no_last_alert_not_in_window(self):
        assert _within_dedup_window({}, _NOW) is False

    def test_recent_alert_in_window(self):
        recent = _NOW - timedelta(minutes=30)
        state = {"last_alert_at_utc": recent.isoformat()}
        assert _within_dedup_window(state, _NOW) is True

    def test_old_alert_not_in_window(self):
        old = _NOW - timedelta(minutes=_DEDUP_MINUTES + 1)
        state = {"last_alert_at_utc": old.isoformat()}
        assert _within_dedup_window(state, _NOW) is False

    def test_exactly_at_boundary_not_in_window(self):
        # timedelta(minutes=90) is NOT < timedelta(minutes=90)
        boundary = _NOW - timedelta(minutes=_DEDUP_MINUTES)
        state = {"last_alert_at_utc": boundary.isoformat()}
        assert _within_dedup_window(state, _NOW) is False

    def test_just_inside_boundary_in_window(self):
        inside = _NOW - timedelta(minutes=_DEDUP_MINUTES - 1)
        state = {"last_alert_at_utc": inside.isoformat()}
        assert _within_dedup_window(state, _NOW) is True

    def test_corrupt_timestamp_not_in_window(self):
        state = {"last_alert_at_utc": "not-a-timestamp"}
        assert _within_dedup_window(state, _NOW) is False


# ---------------------------------------------------------------------------
# run_intraday — _load_state / _update_state
# ---------------------------------------------------------------------------

class TestStateIO:
    def test_load_returns_empty_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Patch _STATE_PATH to use tmp directory
        with patch("cuttingboard.run_intraday._STATE_PATH", str(tmp_path / "state.json")):
            from cuttingboard.run_intraday import _load_state
            assert _load_state() == {}

    def test_load_returns_empty_on_corrupt_json(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text("{ invalid json }")
        with patch("cuttingboard.run_intraday._STATE_PATH", str(state_file)):
            from cuttingboard.run_intraday import _load_state
            assert _load_state() == {}

    def test_update_creates_state_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        state_path = str(tmp_path / "logs" / "state.json")
        with patch("cuttingboard.run_intraday._STATE_PATH", state_path):
            _update_state(_NOW, _regime())
        assert os.path.exists(state_path)

    def test_update_writes_regime_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        state_path = str(tmp_path / "logs" / "state.json")
        with patch("cuttingboard.run_intraday._STATE_PATH", state_path):
            _update_state(_NOW, _regime(regime=RISK_ON))
        with open(state_path) as f:
            state = json.load(f)
        assert state["last_regime"] == RISK_ON

    def test_update_sets_last_alert_when_provided(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        state_path = str(tmp_path / "logs" / "state.json")
        alert_time = _NOW
        with patch("cuttingboard.run_intraday._STATE_PATH", state_path):
            _update_state(_NOW, _regime(), last_alert_at=alert_time)
        with open(state_path) as f:
            state = json.load(f)
        assert state["last_alert_at_utc"] == alert_time.isoformat()

    def test_update_does_not_overwrite_alert_when_not_provided(self, tmp_path, monkeypatch):
        """If no new alert, existing last_alert_at_utc is preserved."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        state_path = str(tmp_path / "logs" / "state.json")
        old_alert = (_NOW - timedelta(hours=1)).isoformat()
        initial_state = {"last_alert_at_utc": old_alert, "last_regime": RISK_ON}
        with open(state_path, "w") as f:
            json.dump(initial_state, f)

        with patch("cuttingboard.run_intraday._STATE_PATH", state_path):
            _update_state(_NOW, _regime(), last_alert_at=None)
        with open(state_path) as f:
            state = json.load(f)
        assert state["last_alert_at_utc"] == old_alert  # preserved

    def test_update_none_regime_does_not_overwrite_regime(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        state_path = str(tmp_path / "logs" / "state.json")
        initial = {"last_regime": RISK_ON}
        with open(state_path, "w") as f:
            json.dump(initial, f)

        with patch("cuttingboard.run_intraday._STATE_PATH", state_path):
            _update_state(_NOW, regime=None)
        with open(state_path) as f:
            state = json.load(f)
        assert state["last_regime"] == RISK_ON  # preserved


# ---------------------------------------------------------------------------
# run_intraday — _send_alert
# ---------------------------------------------------------------------------

class TestSendAlert:
    def test_skips_when_not_configured(self):
        from cuttingboard import config
        with patch.object(config, "TELEGRAM_BOT_TOKEN", None):
            with patch.object(config, "TELEGRAM_CHAT_ID", None):
                result = _send_alert(_regime(), ALERT_CHAOTIC, _NOW)
        assert result is False

    def test_returns_true_on_200(self):
        from cuttingboard import config
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch.object(config, "TELEGRAM_BOT_TOKEN", "bot-token"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "12345"):
                with patch("requests.post", return_value=mock_resp):
                    result = _send_alert(_regime(), ALERT_CHAOTIC, _NOW)
        assert result is True

    def test_returns_false_on_non_200(self):
        from cuttingboard import config
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "error"
        with patch.object(config, "TELEGRAM_BOT_TOKEN", "bot-token"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "12345"):
                with patch("requests.post", return_value=mock_resp):
                    result = _send_alert(_regime(), ALERT_CHAOTIC, _NOW)
        assert result is False

    def test_delegates_message_formatting_to_shared_formatter(self):
        captured = {}

        def capture_send(title, body):
            captured["title"] = title
            captured["body"] = body
            return True

        with patch("cuttingboard.run_intraday.format_intraday_alert", return_value=("REGIME SHIFT", "10:12 AM\n\nRisk improving")) as mock_format:
            with patch("cuttingboard.run_intraday.send_notification", side_effect=capture_send):
                _send_alert(
                    _regime(regime=RISK_ON, posture=AGGRESSIVE_LONG),
                    ALERT_REGIME_SHIFT, _NOW,
                )
        mock_format.assert_called_once_with(
            alert_type=ALERT_REGIME_SHIFT,
            asof_utc=_NOW,
            regime=_regime(regime=RISK_ON, posture=AGGRESSIVE_LONG),
        )
        assert captured["title"] == "REGIME SHIFT"
        assert captured["body"] == "10:12 AM\n\nRisk improving"

    def test_regime_shift_body_drops_legacy_phrasing(self):
        from cuttingboard import config
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch.object(config, "TELEGRAM_BOT_TOKEN", "bot-token"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "12345"):
                with patch("requests.post", return_value=mock_resp) as mock_post:
                    _send_alert(
                        _regime(regime=RISK_ON, posture=AGGRESSIVE_LONG),
                        ALERT_REGIME_SHIFT, _NOW,
                    )
        _, kwargs = mock_post.call_args
        sent_text = kwargs["json"]["text"]
        assert "REGIME SHIFT" in sent_text
        assert "CUTTINGBOARD" not in sent_text.split("\n")[0]
        assert "REGIME SHIFT ->" not in sent_text
        assert "New regime:" not in sent_text


# ---------------------------------------------------------------------------
# run_premarket — _write_commit_msg
# ---------------------------------------------------------------------------

class TestWriteCommitMsg:
    def _make_audit_record(self, **overrides) -> dict:
        base = {
            "date": "2026-04-11",
            "regime": "RISK_ON",
            "outcome": "TRADE",
            "qualified_trades": [
                {"symbol": "SPY", "direction": "LONG"},
                {"symbol": "QQQ", "direction": "LONG"},
            ],
        }
        base.update(overrides)
        return base

    def test_writes_commit_msg_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        audit = tmp_path / "logs" / "audit.jsonl"
        audit.write_text(json.dumps(self._make_audit_record()) + "\n")

        with patch("cuttingboard.run_premarket._AUDIT_LOG_PATH", str(audit)):
            with patch("cuttingboard.run_premarket._COMMIT_MSG_PATH",
                       str(tmp_path / ".cb_commit_msg")):
                _write_commit_msg()

        assert (tmp_path / ".cb_commit_msg").exists()

    def test_commit_msg_format_with_trades(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        audit = tmp_path / "logs" / "audit.jsonl"
        audit.write_text(json.dumps(self._make_audit_record()) + "\n")
        msg_path = tmp_path / ".cb_commit_msg"

        with patch("cuttingboard.run_premarket._AUDIT_LOG_PATH", str(audit)):
            with patch("cuttingboard.run_premarket._COMMIT_MSG_PATH", str(msg_path)):
                _write_commit_msg()

        msg = msg_path.read_text().strip()
        assert msg.startswith("CB report: 2026-04-11")
        assert "RISK_ON" in msg
        assert "2 trades" in msg
        assert "SPY" in msg
        assert "QQQ" in msg

    def test_commit_msg_format_no_trades(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        audit = tmp_path / "logs" / "audit.jsonl"
        record = self._make_audit_record(
            regime="TRANSITION", outcome="NO_TRADE", qualified_trades=[],
        )
        audit.write_text(json.dumps(record) + "\n")
        msg_path = tmp_path / ".cb_commit_msg"

        with patch("cuttingboard.run_premarket._AUDIT_LOG_PATH", str(audit)):
            with patch("cuttingboard.run_premarket._COMMIT_MSG_PATH", str(msg_path)):
                _write_commit_msg()

        msg = msg_path.read_text().strip()
        assert "0 trades []" in msg
        assert "TRANSITION" in msg

    def test_uses_last_record_when_multiple_present(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        audit = tmp_path / "logs" / "audit.jsonl"
        # Two records — only last should be used
        r1 = self._make_audit_record(date="2026-04-10", regime="TRANSITION",
                                     qualified_trades=[])
        r2 = self._make_audit_record(date="2026-04-11", regime="RISK_ON")
        audit.write_text(
            json.dumps(r1) + "\n" + json.dumps(r2) + "\n"
        )
        msg_path = tmp_path / ".cb_commit_msg"

        with patch("cuttingboard.run_premarket._AUDIT_LOG_PATH", str(audit)):
            with patch("cuttingboard.run_premarket._COMMIT_MSG_PATH", str(msg_path)):
                _write_commit_msg()

        msg = msg_path.read_text()
        assert "2026-04-11" in msg
        assert "RISK_ON" in msg

    def test_fallback_on_missing_audit_log(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        msg_path = tmp_path / ".cb_commit_msg"

        with patch("cuttingboard.run_premarket._AUDIT_LOG_PATH",
                   str(tmp_path / "nonexistent.jsonl")):
            with patch("cuttingboard.run_premarket._COMMIT_MSG_PATH", str(msg_path)):
                _write_commit_msg()  # must not raise

        # Fallback file should be written
        assert msg_path.exists()

    def test_fallback_on_empty_audit_log(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        audit = tmp_path / "logs" / "audit.jsonl"
        audit.write_text("")  # empty
        msg_path = tmp_path / ".cb_commit_msg"

        with patch("cuttingboard.run_premarket._AUDIT_LOG_PATH", str(audit)):
            with patch("cuttingboard.run_premarket._COMMIT_MSG_PATH", str(msg_path)):
                _write_commit_msg()

        assert msg_path.exists()

    def test_commit_msg_has_newline(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        audit = tmp_path / "logs" / "audit.jsonl"
        audit.write_text(json.dumps(self._make_audit_record()) + "\n")
        msg_path = tmp_path / ".cb_commit_msg"

        with patch("cuttingboard.run_premarket._AUDIT_LOG_PATH", str(audit)):
            with patch("cuttingboard.run_premarket._COMMIT_MSG_PATH", str(msg_path)):
                _write_commit_msg()

        content = msg_path.read_text()
        assert content.endswith("\n"), "Commit message must end with newline for git -F"
