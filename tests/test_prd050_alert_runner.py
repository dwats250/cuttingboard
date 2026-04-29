from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

from cuttingboard import config


def _notification_records(audit_path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("event") == "notification"
    ]


def test_alert_runner_calls_execute_notify_run_once(monkeypatch):
    from cuttingboard import alert_runner

    calls = []

    def fake_execute_notify_run(*, mode: str, run_date: date, notify_mode: str) -> dict:
        calls.append((mode, run_date, notify_mode))
        return {"status": "SUCCESS", "suppressed": False}

    monkeypatch.setattr("cuttingboard.runtime._execute_notify_run", fake_execute_notify_run)

    assert alert_runner.main() == 0
    assert len(calls) == 1
    mode, run_date, notify_mode = calls[0]
    assert mode == "live"
    assert run_date == datetime.now(timezone.utc).date()
    assert notify_mode == "hourly"


def test_alert_runner_backstop_sends_one_failure_notification(tmp_path, monkeypatch):
    from cuttingboard import alert_runner

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()

    def fail_execute_notify_run(*, mode: str, run_date: date, notify_mode: str) -> dict:
        raise ValueError("test failure")

    with (
        patch("cuttingboard.runtime._execute_notify_run", fail_execute_notify_run),
        patch.object(config, "TELEGRAM_BOT_TOKEN", None),
        patch.object(config, "TELEGRAM_CHAT_ID", None),
    ):
        assert alert_runner.main() == 0

    records = _notification_records(tmp_path / "logs" / "audit.jsonl")
    assert len(records) == 1
    assert records[0]["alert_title"] == "HALT - SYSTEM ERROR"
    assert records[0]["success"] is False
    assert records[0]["reason"] == "runner_level_exception"
    assert records[0]["message_preview"].isascii()
    assert "error_type: ValueError" in records[0]["message_preview"]


def test_alert_runner_backstop_never_raises_if_send_raises(monkeypatch):
    from cuttingboard import alert_runner

    def fail_execute_notify_run(*, mode: str, run_date: date, notify_mode: str) -> dict:
        raise RuntimeError("pipeline failure")

    with (
        patch("cuttingboard.runtime._execute_notify_run", fail_execute_notify_run),
        patch("cuttingboard.alert_runner.send_notification", side_effect=RuntimeError("transport failure")),
    ):
        assert alert_runner.main() == 0


def test_failure_notification_contains_error_title_ascii_timestamp_and_truncated_message():
    from cuttingboard.notifications import NOTIFY_HOURLY, format_failure_notification

    reason = "boom-" + ("x" * 250) + "\u2014"
    title, body = format_failure_notification(NOTIFY_HOURLY, "2026-04-29", reason)

    assert "ERROR" in title or "HALT" in title
    assert (title + body).isascii()
    assert "timestamp:" in body
    rendered_reason = body.split("Failure\n", 1)[1]
    assert len(rendered_reason) <= 200
    assert rendered_reason == str(reason)[:200].encode("ascii", errors="replace").decode("ascii")


def test_send_notification_audit_reason_is_recorded(tmp_path, monkeypatch):
    from cuttingboard.output import send_notification

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()

    with (
        patch.object(config, "TELEGRAM_BOT_TOKEN", None),
        patch.object(config, "TELEGRAM_CHAT_ID", None),
    ):
        result = send_notification(
            "HALT - SYSTEM ERROR",
            "body",
            notification_audit_reason="runner_level_exception",
        )

    assert result is False
    records = _notification_records(tmp_path / "logs" / "audit.jsonl")
    assert len(records) == 1
    assert records[0]["reason"] == "runner_level_exception"
