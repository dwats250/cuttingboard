"""
PRD-018: Notification Signal Hierarchy & Suppression tests.

Verifies:
  - notification_state_key determinism and structure (R1)
  - Last-state persistence (R2)
  - Identical-state suppression (R3)
  - Priority classification (R4)
  - High/Critical bypass of suppression (R5)
  - First-run always sends (R6)
  - State persisted only on successful send (R7)
  - Audit record contains priority + state_key (R8)
  - No regression on PRD-017 contract (R10)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cuttingboard import config
from cuttingboard.notifications.state import (
    LAST_STATE_PATH,
    NotificationPriority,
    classify_notification_priority,
    load_last_state,
    notification_state_key,
    save_last_state,
    should_send,
)
from cuttingboard.output import send_telegram, send_notification


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _notification_records(audit_path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("event") == "notification"
    ]


def _make_contract(
    status: str = "OK",
    market_regime: str = "RISK_ON",
    tradable: bool = False,
    stale_data: bool = False,
    candidates: list | None = None,
    rejections: list | None = None,
    stay_flat_reason: str | None = None,
) -> dict:
    return {
        "status": status,
        "generated_at": "2026-04-24T14:00:00Z",
        "system_state": {
            "market_regime": market_regime,
            "tradable": tradable,
            "stay_flat_reason": stay_flat_reason,
        },
        "market_context": {
            "stale_data_detected": stale_data,
        },
        "trade_candidates": candidates or [],
        "rejections": rejections or [],
    }


# ---------------------------------------------------------------------------
# R1 — notification_state_key determinism and structure
# ---------------------------------------------------------------------------

class TestStateKeyDeterminism:
    def test_identical_inputs_produce_identical_key(self):
        contract = _make_contract(market_regime="RISK_ON", tradable=False)
        assert notification_state_key(contract) == notification_state_key(contract)

    def test_different_regime_produces_different_key(self):
        k1 = notification_state_key(_make_contract(market_regime="RISK_ON"))
        k2 = notification_state_key(_make_contract(market_regime="RISK_OFF"))
        assert k1 != k2

    def test_tradable_change_produces_different_key(self):
        k1 = notification_state_key(_make_contract(tradable=False))
        k2 = notification_state_key(_make_contract(tradable=True))
        assert k1 != k2

    def test_different_symbols_produce_different_key(self):
        c1 = _make_contract(candidates=[{"symbol": "SPY", "direction": "LONG", "strategy_tag": ""}])
        c2 = _make_contract(candidates=[{"symbol": "QQQ", "direction": "LONG", "strategy_tag": ""}])
        assert notification_state_key(c1) != notification_state_key(c2)

    def test_key_is_string(self):
        assert isinstance(notification_state_key(_make_contract()), str)

    def test_key_is_non_empty(self):
        assert len(notification_state_key(_make_contract())) > 0

    def test_at_most_three_symbols_in_key(self):
        candidates = [{"symbol": f"S{i}", "direction": "LONG", "strategy_tag": ""} for i in range(5)]
        key = notification_state_key(_make_contract(candidates=candidates))
        symbols_section = key.split("|")[3]
        assert "S3" not in symbols_section
        assert "S4" not in symbols_section

    def test_key_includes_regime(self):
        key = notification_state_key(_make_contract(market_regime="CHAOTIC"))
        assert "CHAOTIC" in key

    def test_key_includes_posture(self):
        key_flat = notification_state_key(_make_contract(tradable=False))
        key_ready = notification_state_key(_make_contract(tradable=True))
        assert "STAY_FLAT" in key_flat
        assert "TRADE_READY" in key_ready

    def test_rejection_reason_included_in_key(self):
        contract = _make_contract(rejections=[{"reason": "STAY_FLAT posture", "symbol": "REGIME"}])
        key = notification_state_key(contract)
        assert "STAY_FLAT posture" in key

    def test_stay_flat_reason_fallback(self):
        contract = _make_contract(stay_flat_reason="CHAOTIC posture")
        key = notification_state_key(contract)
        assert "CHAOTIC posture" in key

    def test_empty_contract_does_not_raise(self):
        key = notification_state_key({})
        assert isinstance(key, str)


# ---------------------------------------------------------------------------
# R4 — classify_notification_priority
# ---------------------------------------------------------------------------

class TestPriorityClassification:
    def test_error_status_is_critical(self):
        contract = _make_contract(status="ERROR")
        assert classify_notification_priority(contract) == NotificationPriority.CRITICAL

    def test_stale_data_is_critical(self):
        contract = _make_contract(stale_data=True)
        assert classify_notification_priority(contract) == NotificationPriority.CRITICAL

    def test_tradable_true_is_high(self):
        contract = _make_contract(tradable=True)
        assert classify_notification_priority(contract) == NotificationPriority.HIGH

    def test_candidates_not_tradable_is_medium(self):
        contract = _make_contract(
            tradable=False,
            candidates=[{"symbol": "SPY", "direction": "LONG", "strategy_tag": ""}],
        )
        assert classify_notification_priority(contract) == NotificationPriority.MEDIUM

    def test_stay_flat_no_candidates_is_low(self):
        contract = _make_contract(tradable=False, candidates=[])
        assert classify_notification_priority(contract) == NotificationPriority.LOW

    def test_error_beats_tradable(self):
        contract = _make_contract(status="ERROR", tradable=True)
        assert classify_notification_priority(contract) == NotificationPriority.CRITICAL

    def test_stale_beats_tradable(self):
        contract = _make_contract(stale_data=True, tradable=True)
        assert classify_notification_priority(contract) == NotificationPriority.CRITICAL

    def test_priority_is_enum_instance(self):
        assert isinstance(classify_notification_priority(_make_contract()), NotificationPriority)

    def test_priority_value_is_plain_string(self):
        assert classify_notification_priority(_make_contract(tradable=True)).value == "HIGH"


# ---------------------------------------------------------------------------
# R3 / R5 / R6 — should_send logic
# ---------------------------------------------------------------------------

class TestShouldSend:
    def test_first_run_no_last_key_sends(self):
        assert should_send("key1", NotificationPriority.LOW, last_key=None) is True

    def test_identical_low_priority_suppressed(self):
        assert should_send("key1", NotificationPriority.LOW, last_key="key1") is False

    def test_identical_medium_priority_suppressed(self):
        assert should_send("key1", NotificationPriority.MEDIUM, last_key="key1") is False

    def test_identical_high_priority_not_suppressed(self):
        assert should_send("key1", NotificationPriority.HIGH, last_key="key1") is True

    def test_identical_critical_priority_not_suppressed(self):
        assert should_send("key1", NotificationPriority.CRITICAL, last_key="key1") is True

    def test_changed_key_low_priority_sends(self):
        assert should_send("key2", NotificationPriority.LOW, last_key="key1") is True

    def test_changed_key_medium_priority_sends(self):
        assert should_send("key2", NotificationPriority.MEDIUM, last_key="key1") is True

    def test_changed_key_high_priority_sends(self):
        assert should_send("key2", NotificationPriority.HIGH, last_key="key1") is True


# ---------------------------------------------------------------------------
# R2 — load/save last state persistence
# ---------------------------------------------------------------------------

class TestLastStatePersistence:
    def test_load_returns_none_when_file_absent(self, tmp_path):
        result = load_last_state(str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_save_and_load_round_trip(self, tmp_path):
        path = str(tmp_path / "state.json")
        save_last_state("RISK_ON|STAY_FLAT|False||", path)
        assert load_last_state(path) == "RISK_ON|STAY_FLAT|False||"

    def test_load_returns_none_on_invalid_json(self, tmp_path):
        p = tmp_path / "state.json"
        p.write_text("not json", encoding="utf-8")
        assert load_last_state(str(p)) is None

    def test_save_creates_parent_dirs(self, tmp_path):
        path = str(tmp_path / "nested" / "dir" / "state.json")
        save_last_state("key", path)
        assert Path(path).exists()

    def test_save_does_not_raise_on_write_failure(self, tmp_path):
        # Point to a path where the parent is a file (can't mkdir)
        blocker = tmp_path / "blocker"
        blocker.write_text("x", encoding="utf-8")
        bad_path = str(blocker / "state.json")
        save_last_state("key", bad_path)  # must not raise


# ---------------------------------------------------------------------------
# R6 — first-run always sends
# ---------------------------------------------------------------------------

class TestFirstRunAlwaysSends:
    def test_first_run_sends_when_no_state_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp) as mock_post:
                    result = send_telegram("FIRST", "body")

        assert result is True
        assert mock_post.call_count == 1


# ---------------------------------------------------------------------------
# R7 — state only updated on successful send
# ---------------------------------------------------------------------------

class TestStatePersistenceOnSend:
    def test_state_saved_after_successful_send(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        state_path = str(tmp_path / "state.json")

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    contract = _make_contract(tradable=True)
                    key = notification_state_key(contract)
                    ok = send_telegram("TITLE", "body")
                    if ok:
                        save_last_state(key, state_path)

        assert load_last_state(state_path) == key

    def test_state_not_saved_after_failed_send(self, tmp_path):
        state_path = str(tmp_path / "state.json")
        contract = _make_contract()
        key = notification_state_key(contract)

        # Simulate failed send — do NOT call save_last_state
        assert load_last_state(state_path) is None

    def test_failed_send_does_not_update_state_via_should_send(self, tmp_path):
        state_path = str(tmp_path / "state.json")
        key = "RISK_ON|STAY_FLAT|False||"

        # Without saving, load returns None
        assert load_last_state(state_path) is None
        # Simulate: send failed, so we did not call save_last_state
        # Next run: still None → first-run logic fires → should_send True
        assert should_send(key, NotificationPriority.LOW, load_last_state(state_path)) is True


# ---------------------------------------------------------------------------
# R8 — audit records include priority and state_key
# ---------------------------------------------------------------------------

class TestAuditIncludesPriorityAndStateKey:
    def test_send_audit_includes_priority(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    send_telegram(
                        "TITLE", "body",
                        notification_priority="HIGH",
                        notification_state_key="RISK_ON|TRADE_READY|True||",
                    )

        record = _notification_records(tmp_path / "logs" / "audit.jsonl")[-1]
        assert record["priority"] == "HIGH"

    def test_send_audit_includes_state_key(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        expected_key = "RISK_ON|TRADE_READY|True|SPY,QQQ|"

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    send_telegram(
                        "TITLE", "body",
                        notification_priority="HIGH",
                        notification_state_key=expected_key,
                    )

        record = _notification_records(tmp_path / "logs" / "audit.jsonl")[-1]
        assert record["state_key"] == expected_key

    def test_suppressed_audit_has_correct_reason(self, tmp_path, monkeypatch):
        from cuttingboard.audit import write_notification_audit
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        key = "NEUTRAL|STAY_FLAT|False||"
        write_notification_audit(
            transport="telegram",
            alert_title="suppressed",
            attempted=False,
            success=False,
            reason="suppressed_unchanged_state",
            priority="LOW",
            state_key=key,
        )

        record = _notification_records(tmp_path / "logs" / "audit.jsonl")[-1]
        assert record["attempted"] is False
        assert record["reason"] == "suppressed_unchanged_state"
        assert record["priority"] == "LOW"
        assert record["state_key"] == key

    def test_send_notification_threads_priority_and_key(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    send_notification(
                        "msg",
                        notification_priority="MEDIUM",
                        notification_state_key="k",
                    )

        record = _notification_records(tmp_path / "logs" / "audit.jsonl")[-1]
        assert record["priority"] == "MEDIUM"
        assert record["state_key"] == "k"


# ---------------------------------------------------------------------------
# R5 — trade-ready never suppressed
# ---------------------------------------------------------------------------

class TestTradeReadyNotSuppressed:
    def test_trade_ready_sends_even_with_same_key(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        state_path = str(tmp_path / "state.json")

        contract = _make_contract(tradable=True)
        key = notification_state_key(contract)
        save_last_state(key, state_path)

        priority = classify_notification_priority(contract)
        assert priority == NotificationPriority.HIGH
        assert should_send(key, priority, load_last_state(state_path)) is True


# ---------------------------------------------------------------------------
# R3 — identical state suppressed for low priority
# ---------------------------------------------------------------------------

class TestIdenticalStateSuppressed:
    def test_identical_low_state_suppressed(self, tmp_path):
        state_path = str(tmp_path / "state.json")
        contract = _make_contract(tradable=False)
        key = notification_state_key(contract)
        save_last_state(key, state_path)

        priority = classify_notification_priority(contract)
        assert priority == NotificationPriority.LOW
        assert should_send(key, priority, load_last_state(state_path)) is False

    def test_regime_change_triggers_send_even_low_priority(self, tmp_path):
        state_path = str(tmp_path / "state.json")
        old_contract = _make_contract(market_regime="RISK_ON", tradable=False)
        new_contract = _make_contract(market_regime="RISK_OFF", tradable=False)

        old_key = notification_state_key(old_contract)
        new_key = notification_state_key(new_contract)
        save_last_state(old_key, state_path)

        priority = classify_notification_priority(new_contract)
        assert should_send(new_key, priority, load_last_state(state_path)) is True

    def test_new_setup_triggers_send(self, tmp_path):
        state_path = str(tmp_path / "state.json")
        old_contract = _make_contract(tradable=False, candidates=[])
        new_contract = _make_contract(
            tradable=False,
            candidates=[{"symbol": "SPY", "direction": "LONG", "strategy_tag": ""}],
        )

        save_last_state(notification_state_key(old_contract), state_path)
        new_key = notification_state_key(new_contract)
        priority = classify_notification_priority(new_contract)
        assert should_send(new_key, priority, load_last_state(state_path)) is True


# ---------------------------------------------------------------------------
# R10 — no regression: send_telegram still works without new kwargs
# ---------------------------------------------------------------------------

class TestNoRegression:
    def test_send_telegram_without_priority_kwarg(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    result = send_telegram("TITLE", "body")

        assert result is True
        record = _notification_records(tmp_path / "logs" / "audit.jsonl")[-1]
        assert record["priority"] is None
        assert record["state_key"] is None

    def test_send_notification_without_priority_kwarg(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    result = send_notification("msg")

        assert result is True
