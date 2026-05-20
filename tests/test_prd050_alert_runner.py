from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

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

    def fake_execute_notify_run(*, mode: str, run_date: date, notify_mode: str, **kwargs) -> dict:
        calls.append((mode, run_date, notify_mode))
        return {"status": "SUCCESS", "suppressed": False}

    monkeypatch.setattr("cuttingboard.runtime._execute_notify_run", fake_execute_notify_run)

    # PRD-149: routine path is gated on PT-window; use --force-slot to preserve
    # this test's original "main() reaches execute" contract.
    assert alert_runner.main(["--force-slot"]) == 0
    assert len(calls) == 1
    mode, run_date, notify_mode = calls[0]
    assert mode == "live"
    assert run_date == datetime.now(timezone.utc).date()
    assert notify_mode == "hourly"


def test_alert_runner_backstop_sends_one_failure_notification(tmp_path, monkeypatch):
    from cuttingboard import alert_runner

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()

    def fail_execute_notify_run(*, mode: str, run_date: date, notify_mode: str, **kwargs) -> dict:
        raise ValueError("test failure")

    with (
        patch("cuttingboard.runtime._execute_notify_run", fail_execute_notify_run),
        patch.object(config, "TELEGRAM_BOT_TOKEN", None),
        patch.object(config, "TELEGRAM_CHAT_ID", None),
    ):
        # PRD-149: --force-slot bypasses the PT-window gate so this test still
        # exercises the runner-level exception backstop.
        assert alert_runner.main(["--force-slot"]) == 0

    records = _notification_records(tmp_path / "logs" / "audit.jsonl")
    assert len(records) == 1
    assert records[0]["alert_title"] == "HALT - SYSTEM ERROR"
    assert records[0]["success"] is False
    assert records[0]["reason"] == "runner_level_exception"
    assert records[0]["message_preview"].isascii()
    assert "error_type: ValueError" in records[0]["message_preview"]


def test_alert_runner_backstop_never_raises_if_send_raises(monkeypatch):
    from cuttingboard import alert_runner

    def fail_execute_notify_run(*, mode: str, run_date: date, notify_mode: str, **kwargs) -> dict:
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


# ---- PRD-149: routine-window gating ----------------------------------------

def _patch_now(monkeypatch, fixed_utc: datetime) -> None:
    """Replace alert_runner's datetime.now in a way that ignores tz arg."""
    import cuttingboard.alert_runner as runner_mod

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return fixed_utc if tz is None else fixed_utc.astimezone(tz)

    monkeypatch.setattr(runner_mod, "datetime", _FixedDateTime)


def _capture_execute(monkeypatch) -> list[dict]:
    calls: list[dict] = []

    def fake(*, mode, run_date, notify_mode, slot_utc=None, **kwargs):
        calls.append(
            {
                "mode": mode,
                "run_date": run_date,
                "notify_mode": notify_mode,
                "slot_utc": slot_utc,
            }
        )
        return {"status": "SUCCESS", "suppressed": False}

    monkeypatch.setattr("cuttingboard.runtime._execute_notify_run", fake)
    return calls


@pytest.mark.parametrize(
    "now_utc",
    [
        datetime(2026, 5, 19, 13, 0, 0, tzinfo=timezone.utc),   # 06:00 PT PDT
        datetime(2026, 5, 19, 13, 30, 0, tzinfo=timezone.utc),  # 06:30 PT PDT
        datetime(2026, 5, 19, 14, 0, 0, tzinfo=timezone.utc),   # 07:00 PT PDT
        datetime(2026, 5, 19, 19, 0, 0, tzinfo=timezone.utc),   # 12:00 PT PDT
        datetime(2026, 5, 19, 20, 0, 0, tzinfo=timezone.utc),   # 13:00 PT PDT
    ],
)
def test_prd149_routine_in_window_sends(tmp_path, monkeypatch, now_utc):
    from cuttingboard import alert_runner

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    _patch_now(monkeypatch, now_utc)
    calls = _capture_execute(monkeypatch)

    assert alert_runner.main() == 0
    assert len(calls) == 1
    assert calls[0]["notify_mode"] == "hourly"
    assert calls[0]["slot_utc"] is not None


def test_prd149_six_and_six_thirty_have_distinct_slot_utc(tmp_path, monkeypatch):
    from cuttingboard import alert_runner

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    calls = _capture_execute(monkeypatch)

    _patch_now(monkeypatch, datetime(2026, 5, 19, 13, 0, 0, tzinfo=timezone.utc))
    alert_runner.main()
    _patch_now(monkeypatch, datetime(2026, 5, 19, 13, 30, 0, tzinfo=timezone.utc))
    alert_runner.main()

    assert len(calls) == 2
    assert calls[0]["slot_utc"] != calls[1]["slot_utc"]


@pytest.mark.parametrize(
    "now_utc",
    [
        datetime(2026, 5, 19, 20, 30, 0, tzinfo=timezone.utc),  # 13:30 PT PDT
        datetime(2026, 5, 19, 22, 0, 0, tzinfo=timezone.utc),   # 15:00 PT PDT
        datetime(2026, 5, 19, 21, 0, 0, tzinfo=timezone.utc),   # 14:00 PT PDT
    ],
)
def test_prd149_routine_outside_window_suppresses(tmp_path, monkeypatch, now_utc):
    from cuttingboard import alert_runner

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    _patch_now(monkeypatch, now_utc)
    calls = _capture_execute(monkeypatch)

    assert alert_runner.main() == 0
    assert calls == []
    records = _notification_records(tmp_path / "logs" / "audit.jsonl")
    assert len(records) == 1
    assert records[0]["status"] == "suppressed"
    assert records[0]["reason"] == "outside_routine_window"
    assert records[0]["attempted"] is False
    assert records[0]["success"] is False
    assert records[0]["alert_title"] == "hourly"
    assert records[0]["state_key"].startswith("outside:")


def test_prd149_outside_window_does_not_advance_last_slot(tmp_path, monkeypatch):
    from cuttingboard import alert_runner

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    slot_path = tmp_path / "logs" / "last_hourly_slot.json"
    pre_payload = json.dumps({"slot_utc": "PREEXISTING", "saved_at_utc": "x"})
    slot_path.write_text(pre_payload, encoding="utf-8")

    _patch_now(monkeypatch, datetime(2026, 5, 19, 22, 0, 0, tzinfo=timezone.utc))
    _capture_execute(monkeypatch)

    assert alert_runner.main() == 0
    assert slot_path.read_text(encoding="utf-8") == pre_payload


def test_prd149_force_slot_after_close_still_sends(tmp_path, monkeypatch):
    from cuttingboard import alert_runner

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    _patch_now(monkeypatch, datetime(2026, 5, 19, 22, 0, 0, tzinfo=timezone.utc))  # 15:00 PT
    calls = _capture_execute(monkeypatch)

    assert alert_runner.main(["--force-slot"]) == 0
    assert len(calls) == 1
    assert calls[0]["slot_utc"] is not None


def test_prd149_delayed_one_pm_titles_as_one_pm(tmp_path, monkeypatch):
    """Delayed 13:17 PT routine run resolves to the 13:00 PT slot.

    Title generation lives in runtime.py + notifications/__init__.py; here we
    verify the slot_utc threaded into _execute_notify_run reflects 13:00 PT,
    which by runtime.py:545-550 wiring becomes the title's PT-clock anchor.
    """
    from cuttingboard import alert_runner
    from cuttingboard.notifications.hourly_slot import _PT_TZ

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    # PDT: 13:17 PT = 20:17 UTC
    _patch_now(monkeypatch, datetime(2026, 5, 19, 20, 17, 0, tzinfo=timezone.utc))
    calls = _capture_execute(monkeypatch)

    assert alert_runner.main() == 0
    assert len(calls) == 1
    slot = calls[0]["slot_utc"]
    assert slot is not None
    slot_pt = slot.astimezone(_PT_TZ)
    assert (slot_pt.hour, slot_pt.minute) == (13, 0)


def test_prd149_alert_runner_does_not_import_is_premarket_slot():
    """R6 FAIL: alert_runner must not reference is_premarket_slot."""
    src = Path("cuttingboard/alert_runner.py").read_text(encoding="utf-8")
    assert "is_premarket_slot" not in src


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
