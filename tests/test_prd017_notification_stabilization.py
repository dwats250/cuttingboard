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
) -> dict:
    return {
        "generated_at": generated_at,
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
        contract = _make_contract(generated_at="2026-04-24T14:35:00Z")
        msg = build_notification_message(contract)
        assert "2026-04-24T14:35" in msg

    def test_includes_market_regime(self):
        contract = _make_contract(market_regime="RISK_OFF")
        msg = build_notification_message(contract)
        assert "RISK_OFF" in msg

    def test_tradable_shows_trade_ready(self):
        contract = _make_contract(tradable=True)
        msg = build_notification_message(contract)
        assert "TRADE_READY" in msg

    def test_not_tradable_shows_stay_flat(self):
        contract = _make_contract(tradable=False)
        msg = build_notification_message(contract)
        assert "STAY_FLAT" in msg

    def test_includes_tradable_flag(self):
        contract = _make_contract(tradable=True)
        msg = build_notification_message(contract)
        assert "tradable" in msg.lower()

    def test_top_setups_max_three(self):
        candidates = [
            {"symbol": f"SYM{i}", "direction": "LONG", "strategy_tag": "BULL_CALL"}
            for i in range(5)
        ]
        contract = _make_contract(trade_candidates=candidates)
        msg = build_notification_message(contract)
        # Only first 3 symbols should appear
        assert "SYM0" in msg
        assert "SYM1" in msg
        assert "SYM2" in msg
        assert "SYM3" not in msg
        assert "SYM4" not in msg

    def test_no_setups_section_when_empty(self):
        contract = _make_contract(trade_candidates=[])
        msg = build_notification_message(contract)
        assert "setups" not in msg

    def test_returns_single_string(self):
        contract = _make_contract()
        msg = build_notification_message(contract)
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_empty_contract_does_not_raise(self):
        msg = build_notification_message({})
        assert isinstance(msg, str)


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
