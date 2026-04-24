"""
Notification audit tests.

Verifies that every send_telegram() call path writes a structured record to
audit.jsonl, that no path silently swallows failures, and that pipeline
execution survives notification failures.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cuttingboard import config
from cuttingboard.output import send_telegram, send_notification


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _last_notification_record(audit_path: Path) -> dict:
    """Return the most recent notification event record from audit.jsonl."""
    records = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    notification_records = [r for r in records if r.get("event") == "notification"]
    assert notification_records, "No notification audit records found"
    return notification_records[-1]


# ---------------------------------------------------------------------------
# 1. Successful send writes success audit
# ---------------------------------------------------------------------------

class TestSuccessAudit:
    def test_successful_send_writes_success_record(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "bot-tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "12345"):
                with patch("requests.post", return_value=mock_resp):
                    result = send_telegram("TEST TITLE", "test body")

        assert result is True
        record = _last_notification_record(tmp_path / "logs" / "audit.jsonl")
        assert record["event"] == "notification"
        assert record["transport"] == "telegram"
        assert record["alert_title"] == "TEST TITLE"
        assert record["attempted"] is True
        assert record["success"] is True
        assert record["http_status"] == 200
        assert record["error"] is None
        assert record["message_preview"] is not None

    def test_successful_send_record_has_timestamp(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    send_telegram("TITLE", "body")

        record = _last_notification_record(tmp_path / "logs" / "audit.jsonl")
        assert "timestamp" in record
        ts = datetime.fromisoformat(record["timestamp"])
        assert ts.tzinfo is not None


# ---------------------------------------------------------------------------
# 2. HTTP failure writes failure audit
# ---------------------------------------------------------------------------

class TestHttpFailureAudit:
    def test_http_429_writes_failure_record(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Too Many Requests"

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    result = send_telegram("RATE LIMITED", "body")

        assert result is False
        record = _last_notification_record(tmp_path / "logs" / "audit.jsonl")
        assert record["attempted"] is True
        assert record["success"] is False
        assert record["http_status"] == 429
        assert record["error"] is not None

    def test_http_400_writes_failure_record(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad Request: chat not found"

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    result = send_telegram("BAD REQ", "body")

        assert result is False
        record = _last_notification_record(tmp_path / "logs" / "audit.jsonl")
        assert record["success"] is False
        assert record["http_status"] == 400


# ---------------------------------------------------------------------------
# 3. Exception writes failure audit
# ---------------------------------------------------------------------------

class TestExceptionAudit:
    def test_connection_error_writes_failure_record(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", side_effect=ConnectionError("timeout")):
                    result = send_telegram("CONN ERROR", "body")

        assert result is False
        record = _last_notification_record(tmp_path / "logs" / "audit.jsonl")
        assert record["attempted"] is True
        assert record["success"] is False
        assert record["error"] is not None
        assert "timeout" in record["error"]

    def test_exception_does_not_raise(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", side_effect=RuntimeError("network down")):
                    result = send_telegram("TITLE", "body")  # must not raise

        assert result is False


# ---------------------------------------------------------------------------
# 4. Not configured → writes skipped audit
# ---------------------------------------------------------------------------

class TestNotConfiguredAudit:
    def test_no_token_writes_skipped_record(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        with patch.object(config, "TELEGRAM_BOT_TOKEN", None):
            with patch.object(config, "TELEGRAM_CHAT_ID", None):
                result = send_telegram("TITLE", "body")

        assert result is False
        record = _last_notification_record(tmp_path / "logs" / "audit.jsonl")
        assert record["attempted"] is False
        assert record["success"] is False
        assert record["reason"] == "not_configured"

    def test_no_token_does_not_post(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        with patch.object(config, "TELEGRAM_BOT_TOKEN", None):
            with patch.object(config, "TELEGRAM_CHAT_ID", None):
                with patch("requests.post") as mock_post:
                    send_telegram("TITLE", "body")

        mock_post.assert_not_called()


# ---------------------------------------------------------------------------
# 5. Notification failure does not crash pipeline
# ---------------------------------------------------------------------------

class TestPipelineResiliency:
    def test_notification_failure_does_not_propagate(self, tmp_path, monkeypatch):
        """send_telegram raising internally must not propagate to the caller."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        # Patch requests.post to raise — send_telegram must catch and return False
        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", side_effect=OSError("network unreachable")):
                    result = send_notification("HALT", "macro data invalid")

        assert result is False  # did not raise

    def test_execute_notify_run_failure_handler_logs_not_silent(self, tmp_path, monkeypatch):
        """_execute_notify_run exception path must log, not silently swallow."""
        from cuttingboard.runtime import _execute_notify_run, MODE_LIVE
        from cuttingboard.notifications import NOTIFY_HOURLY

        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        with (
            patch("cuttingboard.runtime.fetch_all", side_effect=RuntimeError("boom")),
            patch("cuttingboard.runtime.send_notification", return_value=True) as mock_send,
        ):
            result = _execute_notify_run(
                mode=MODE_LIVE,
                run_date=date(2026, 4, 24),
                notify_mode=NOTIFY_HOURLY,
            )

        # Failure notification must still be attempted
        mock_send.assert_called_once()
        assert result["status"] == "FAIL"


# ---------------------------------------------------------------------------
# 6. should_suppress() is not wired into the live send path
# ---------------------------------------------------------------------------

class TestSuppressDeadCode:
    def test_should_suppress_is_not_called_by_execute_notify_run(self):
        """should_suppress() is defined but not wired in — document this explicitly."""
        import inspect
        from cuttingboard.runtime import _execute_notify_run
        src = inspect.getsource(_execute_notify_run)
        assert "should_suppress" not in src, (
            "should_suppress() is now being called — if you wire it in, "
            "ensure suppressed alerts write a notification audit record "
            "with reason='suppressed' so skips are visible in audit.jsonl."
        )

    def test_should_suppress_exists_in_notifications(self):
        from cuttingboard.notifications import should_suppress
        assert callable(should_suppress)


# ---------------------------------------------------------------------------
# 7. Audit record structure completeness
# ---------------------------------------------------------------------------

class TestAuditRecordStructure:
    _REQUIRED_FIELDS = {
        "event", "timestamp", "transport", "alert_title",
        "attempted", "success", "http_status", "error", "reason", "message_preview",
    }

    def test_success_record_has_all_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp):
                    send_telegram("T", "B")

        record = _last_notification_record(tmp_path / "logs" / "audit.jsonl")
        missing = self._REQUIRED_FIELDS - set(record)
        assert not missing, f"Missing audit fields: {missing}"

    def test_skip_record_has_all_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()

        with patch.object(config, "TELEGRAM_BOT_TOKEN", None):
            with patch.object(config, "TELEGRAM_CHAT_ID", None):
                send_telegram("T", "B")

        record = _last_notification_record(tmp_path / "logs" / "audit.jsonl")
        missing = self._REQUIRED_FIELDS - set(record)
        assert not missing, f"Missing audit fields: {missing}"
