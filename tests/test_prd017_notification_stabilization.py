"""
PRD-017: Notification Delivery Stabilization tests.

Verifies:
  - Single notification per run (R1/R5)
  - build_notification_message aggregation (R2)
  - Rate-limit enforcement (R3)
  - Retry on 429 and timeout (R4)
  - Exactly one audit record per run (R6)
  - Notification failure does not crash pipeline (R9)
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from cuttingboard import config
from cuttingboard.output import (
    _MIN_SEND_INTERVAL,
    build_notification_message,
    send_notification,
    send_telegram,
)


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
    market_regime: str = "RISK_ON",
    tradable: bool = True,
    trade_candidates: list | None = None,
    generated_at: str = "2026-04-24T14:00:00Z",
    status: str = "OK",
    outcome: str = "NO_TRADE",
) -> dict:
    return {
        "generated_at": generated_at,
        "status": status,
        "outcome": outcome,
        "system_state": {
            "market_regime": market_regime,
            "tradable": tradable,
        },
        "trade_candidates": trade_candidates or [],
    }


# ---------------------------------------------------------------------------
# R2 — build_notification_message aggregation
# ---------------------------------------------------------------------------

class TestBuildNotificationMessage:
    def test_includes_timestamp(self):
        _, body = build_notification_message(_make_contract(generated_at="2026-04-24T14:35:00Z"))
        assert "2026-04-24T14:35" in body

    def test_includes_market_regime(self):
        _, body = build_notification_message(_make_contract(market_regime="RISK_OFF"))
        assert "RISK_OFF" in body

    def test_trade_outcome_gives_trade_ready_title(self):
        candidates = [{"symbol": "SPY", "setup_quality": "TOP_TRADE_VALIDATED"}]
        title, _ = build_notification_message(
            _make_contract(tradable=True, outcome="TRADE", trade_candidates=candidates)
        )
        assert title == "TRADE READY"

    def test_tradable_true_no_trade_never_gives_trade_ready_title(self):
        title, _ = build_notification_message(_make_contract(tradable=True, outcome="NO_TRADE"))
        assert title == "NO TRADE - SYSTEM ACTIVE"

    def test_not_tradable_no_candidates_gives_no_trade_title(self):
        title, _ = build_notification_message(
            _make_contract(tradable=False, outcome="NO_TRADE", trade_candidates=[])
        )
        assert title == "NO TRADE - SYSTEM ACTIVE"

    def test_not_tradable_with_candidates_gives_watchlist_title(self):
        candidates = [{"symbol": "SPY", "direction": "LONG", "strategy_tag": "BULL_CALL"}]
        title, _ = build_notification_message(
            _make_contract(tradable=False, outcome="NO_TRADE", trade_candidates=candidates)
        )
        assert title == "WATCHLIST - SETUPS FORMING"

    def test_fail_status_gives_halt_title(self):
        title, _ = build_notification_message(_make_contract(status="FAIL", outcome="HALT"))
        assert title == "HALT - SYSTEM ERROR"

    def test_error_status_gives_halt_title(self):
        title, _ = build_notification_message(_make_contract(status="ERROR", outcome="HALT"))
        assert title == "HALT - SYSTEM ERROR"

    def test_includes_tradable_in_body(self):
        _, body = build_notification_message(_make_contract(tradable=True))
        assert "Tradable:" in body

    def test_setups_count_in_body(self):
        candidates = [{"symbol": f"SYM{i}"} for i in range(5)]
        _, body = build_notification_message(_make_contract(trade_candidates=candidates))
        assert "Setups: 5" in body

    def test_setups_zero_when_no_candidates(self):
        _, body = build_notification_message(_make_contract(trade_candidates=[]))
        assert "Setups: 0" in body

    def test_body_line_order(self):
        _, body = build_notification_message(_make_contract())
        keys = [line.split(":")[0] for line in body.splitlines() if ":" in line]
        assert keys[:5] == ["Time", "Regime", "Tradable", "Setups", "Status"]

    def test_reason_no_qualifying_setups(self):
        _, body = build_notification_message(_make_contract(outcome="NO_TRADE", tradable=False, trade_candidates=[]))
        assert "Reason: no qualifying setups" in body

    def test_reason_setups_present_but_not_tradable(self):
        candidates = [{"symbol": "SPY"}]
        _, body = build_notification_message(_make_contract(outcome="NO_TRADE", tradable=False, trade_candidates=candidates))
        assert "Reason: setups forming but no validated trade" in body

    def test_reason_pipeline_failure(self):
        _, body = build_notification_message(_make_contract(status="FAIL", outcome="HALT"))
        assert "Reason: pipeline failure" in body

    def test_ascii_only_output(self):
        title, body = build_notification_message(_make_contract())
        assert (title + body).isascii()

    def test_returns_tuple_of_strings(self):
        result = build_notification_message(_make_contract())
        assert isinstance(result, tuple)
        title, body = result
        assert isinstance(title, str) and len(title) > 0
        assert isinstance(body, str) and len(body) > 0

    def test_empty_contract_does_not_raise(self):
        title, body = build_notification_message({})
        assert isinstance(title, str)
        assert isinstance(body, str)


# ---------------------------------------------------------------------------
# R3 — rate limit enforcement
# ---------------------------------------------------------------------------

class TestRateLimitEnforced:
    def test_second_call_triggers_sleep(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        sleep_calls: list[float] = []
        monkeypatch.setattr("cuttingboard.output.time.sleep", lambda s: sleep_calls.append(s))

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    send_telegram("FIRST", "body1")   # sets _LAST_SEND_TS
                    send_telegram("SECOND", "body2")  # must sleep

        rate_limit_sleeps = [s for s in sleep_calls if 0 < s <= _MIN_SEND_INTERVAL]
        assert rate_limit_sleeps, (
            f"Expected at least one rate-limit sleep <= {_MIN_SEND_INTERVAL}s, got: {sleep_calls}"
        )

    def test_first_call_never_sleeps_for_rate_limit(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        sleep_calls: list[float] = []
        monkeypatch.setattr("cuttingboard.output.time.sleep", lambda s: sleep_calls.append(s))

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    send_telegram("FIRST", "body")

        # _LAST_SEND_TS was 0 → elapsed >> 1.1s → no rate-limit sleep
        rate_limit_sleeps = [s for s in sleep_calls if 0 < s <= _MIN_SEND_INTERVAL]
        assert not rate_limit_sleeps, f"Unexpected rate-limit sleep on first call: {sleep_calls}"


# ---------------------------------------------------------------------------
# R4 — retry on 429
# ---------------------------------------------------------------------------

class TestRetryOn429:
    def test_retries_once_on_429_then_succeeds(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.text = "Too Many Requests"

        resp_200 = MagicMock()
        resp_200.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", side_effect=[resp_429, resp_200]) as mock_post:
                    result = send_telegram("TITLE", "body")

        assert result is True
        assert mock_post.call_count == 2

    def test_retry_429_writes_success_audit_with_retry_count_1(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.text = "Too Many Requests"

        resp_200 = MagicMock()
        resp_200.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", side_effect=[resp_429, resp_200]):
                    send_telegram("TITLE", "body")

        record = _notification_records(tmp_path / "logs" / "audit.jsonl")[-1]
        assert record["success"] is True
        assert record["retry_count"] == 1

    def test_429_twice_fails_with_retry_count_1(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.text = "rate limited"

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=resp_429) as mock_post:
                    result = send_telegram("TITLE", "body")

        assert result is False
        assert mock_post.call_count == 2

        record = _notification_records(tmp_path / "logs" / "audit.jsonl")[-1]
        assert record["success"] is False
        assert record["retry_count"] == 1

    def test_max_2_attempts_total(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.text = "rate"

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=resp_429) as mock_post:
                    send_telegram("T", "b")

        assert mock_post.call_count == 2, "Must not exceed 2 total attempts"


# ---------------------------------------------------------------------------
# R4 — retry on timeout / 5xx
# ---------------------------------------------------------------------------

class TestRetryOnTimeout:
    def test_retries_once_on_timeout_then_succeeds(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        resp_200 = MagicMock()
        resp_200.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch(
                    "requests.post",
                    side_effect=[__import__("requests").exceptions.Timeout("timed out"), resp_200],
                ) as mock_post:
                    result = send_telegram("TITLE", "body")

        assert result is True
        assert mock_post.call_count == 2

    def test_timeout_retry_audit_shows_retry_count_1(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        resp_200 = MagicMock()
        resp_200.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch(
                    "requests.post",
                    side_effect=[__import__("requests").exceptions.Timeout("timed out"), resp_200],
                ):
                    send_telegram("TITLE", "body")

        record = _notification_records(tmp_path / "logs" / "audit.jsonl")[-1]
        assert record["success"] is True
        assert record["retry_count"] == 1

    def test_retries_once_on_5xx(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        resp_500 = MagicMock()
        resp_500.status_code = 500
        resp_500.text = "Internal Server Error"

        resp_200 = MagicMock()
        resp_200.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", side_effect=[resp_500, resp_200]) as mock_post:
                    result = send_telegram("TITLE", "body")

        assert result is True
        assert mock_post.call_count == 2

    def test_non_retryable_error_stops_after_one_attempt(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        resp_400 = MagicMock()
        resp_400.status_code = 400
        resp_400.text = "Bad Request"

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=resp_400) as mock_post:
                    result = send_telegram("TITLE", "body")

        assert result is False
        assert mock_post.call_count == 1

        record = _notification_records(tmp_path / "logs" / "audit.jsonl")[-1]
        assert record["retry_count"] == 0


# ---------------------------------------------------------------------------
# R6 — exactly one audit record per run
# ---------------------------------------------------------------------------

class TestSingleAuditRecordPerRun:
    def test_single_audit_record_on_success(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    send_telegram("TITLE", "body")

        records = _notification_records(tmp_path / "logs" / "audit.jsonl")
        assert len(records) == 1

    def test_single_audit_record_on_failure(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        resp_500 = MagicMock()
        resp_500.status_code = 500
        resp_500.text = "error"

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=resp_500):
                    send_telegram("TITLE", "body")

        records = _notification_records(tmp_path / "logs" / "audit.jsonl")
        assert len(records) == 1

    def test_single_audit_record_on_429_retry(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.text = "rate"

        resp_200 = MagicMock()
        resp_200.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", side_effect=[resp_429, resp_200]):
                    send_telegram("TITLE", "body")

        records = _notification_records(tmp_path / "logs" / "audit.jsonl")
        assert len(records) == 1, f"Expected 1 audit record, got {len(records)}"

    def test_audit_record_includes_retry_count(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    send_telegram("TITLE", "body")

        record = _notification_records(tmp_path / "logs" / "audit.jsonl")[-1]
        assert "retry_count" in record
        assert record["retry_count"] == 0


# ---------------------------------------------------------------------------
# R1/R5 — single notification per run (execute_notify_run path)
# ---------------------------------------------------------------------------

class TestSingleNotificationPerRun:
    def test_execute_notify_run_sends_exactly_one_notification(self, tmp_path, monkeypatch):
        from cuttingboard.runtime import _execute_notify_run, MODE_LIVE
        from cuttingboard.notifications import NOTIFY_HOURLY

        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        with (
            patch("cuttingboard.runtime.fetch_all", side_effect=RuntimeError("fail")),
            patch("cuttingboard.runtime.send_notification", return_value=True) as mock_send,
        ):
            _execute_notify_run(
                mode=MODE_LIVE,
                run_date=date(2026, 4, 24),
                notify_mode=NOTIFY_HOURLY,
            )

        assert mock_send.call_count == 1, (
            f"Expected exactly 1 send_notification call, got {mock_send.call_count}"
        )

    def test_no_multi_send_loop_in_run_pipeline(self):
        import inspect
        from cuttingboard.runtime import _run_pipeline
        src = inspect.getsource(_run_pipeline)
        # Count occurrences of send_notification calls
        send_calls = src.count("send_notification(")
        assert send_calls <= 1, (
            f"_run_pipeline must call send_notification at most once, found {send_calls} calls"
        )


# ---------------------------------------------------------------------------
# R9 — notification failure does not crash pipeline
# ---------------------------------------------------------------------------

class TestNotificationFailureResiliency:
    def test_send_telegram_never_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", side_effect=OSError("network unreachable")):
                    result = send_telegram("TITLE", "body")

        assert result is False

    def test_send_notification_never_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", side_effect=RuntimeError("fatal")):
                    result = send_notification("HALT", "macro data invalid")

        assert result is False

    def test_skipped_send_writes_audit_with_reason(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        with patch.object(config, "TELEGRAM_BOT_TOKEN", None):
            with patch.object(config, "TELEGRAM_CHAT_ID", None):
                result = send_telegram("TITLE", "body")

        assert result is False
        record = _notification_records(tmp_path / "logs" / "audit.jsonl")[-1]
        assert record["attempted"] is False
        assert record["reason"] == "not_configured"
