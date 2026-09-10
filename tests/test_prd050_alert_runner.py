from __future__ import annotations

import json
import subprocess
import sys
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


def test_alert_runner_success_return_exits_zero(monkeypatch):
    """PRD-287: a healthy completion (_execute_notify_run status SUCCESS) exits 0."""
    from cuttingboard import alert_runner

    def ok_execute_notify_run(*, mode: str, run_date: date, notify_mode: str, **kwargs) -> dict:
        return {"status": "SUCCESS", "suppressed": False}

    monkeypatch.setattr("cuttingboard.runtime._execute_notify_run", ok_execute_notify_run)
    assert alert_runner.main(["--force-slot"]) == 0


def test_alert_runner_in_run_system_failure_exits_nonzero(monkeypatch):
    """PRD-287: a non-throwing in-run system failure (_execute_notify_run returns
    status FAIL) exits 1 — the runner no longer converts it to exit 0."""
    from cuttingboard import alert_runner

    def fail_status_execute_notify_run(*, mode: str, run_date: date, notify_mode: str, **kwargs) -> dict:
        return {"status": "FAIL", "suppressed": False}

    monkeypatch.setattr("cuttingboard.runtime._execute_notify_run", fail_status_execute_notify_run)
    assert alert_runner.main(["--force-slot"]) == 1


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
        # PRD-287: a runner-level exception now exits 1 (was 0) — AFTER the
        # notification/diagnostic attempt asserted below still runs.
        assert alert_runner.main(["--force-slot"]) == 1

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
        # PRD-287: --force-slot pins the backstop path deterministically (the
        # PT-window gate is time-dependent); the runner never raises even when
        # the failure notification itself raises, and now exits 1 (was 0).
        assert alert_runner.main(["--force-slot"]) == 1


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
        datetime(2026, 5, 19, 13, 30, 0, tzinfo=timezone.utc),  # 06:30 PT PDT
        datetime(2026, 5, 19, 13, 45, 0, tzinfo=timezone.utc),  # 06:45 PT PDT (PRD-319)
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


def test_prd149_six_thirty_and_six_forty_five_have_distinct_slot_utc(tmp_path, monkeypatch):
    from cuttingboard import alert_runner

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    calls = _capture_execute(monkeypatch)

    _patch_now(monkeypatch, datetime(2026, 5, 19, 13, 30, 0, tzinfo=timezone.utc))
    alert_runner.main()
    _patch_now(monkeypatch, datetime(2026, 5, 19, 13, 45, 0, tzinfo=timezone.utc))
    alert_runner.main()

    assert len(calls) == 2
    assert calls[0]["slot_utc"] != calls[1]["slot_utc"]


# ---- PRD-319 R2: --routine-slot explicit identity ---------------------------

def test_prd319_routine_slot_sends_named_slot(tmp_path, monkeypatch):
    from cuttingboard import alert_runner
    from cuttingboard.notifications.hourly_slot import _PT_TZ

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    _patch_now(monkeypatch, datetime(2026, 5, 19, 13, 32, 0, tzinfo=timezone.utc))
    calls = _capture_execute(monkeypatch)

    assert alert_runner.main(["--routine-slot", "06:30"]) == 0
    assert len(calls) == 1
    slot_pt = calls[0]["slot_utc"].astimezone(_PT_TZ)
    assert (slot_pt.hour, slot_pt.minute) == (6, 30)


def test_prd319_routine_slot_identity_never_shifts(tmp_path, monkeypatch):
    """A delayed 06:30 routine dispatch starting at 06:46 PT still sends AS
    06:30 -- the mutation (falling back to inference) would send 06:45."""
    from cuttingboard import alert_runner
    from cuttingboard.notifications.hourly_slot import _PT_TZ

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    _patch_now(monkeypatch, datetime(2026, 5, 19, 13, 46, 0, tzinfo=timezone.utc))
    calls = _capture_execute(monkeypatch)

    assert alert_runner.main(["--routine-slot", "06:30"]) == 0
    assert len(calls) == 1
    slot_pt = calls[0]["slot_utc"].astimezone(_PT_TZ)
    assert (slot_pt.hour, slot_pt.minute) == (6, 30)


@pytest.mark.parametrize(
    "now_utc, label",
    [
        # off-season twin: 40 13 cron in PST = 05:40 PT, intended 06:30 (future)
        (datetime(2026, 1, 12, 13, 40, 0, tzinfo=timezone.utc), "06:30"),
        # off-season twin: 40 14 cron in PDT = 07:40 PT, intended 06:30 (lag 70)
        (datetime(2026, 5, 19, 14, 40, 0, tzinfo=timezone.utc), "06:30"),
        # retired slot named explicitly
        (datetime(2026, 5, 19, 13, 5, 0, tzinfo=timezone.utc), "06:00"),
    ],
)
def test_prd319_routine_slot_out_of_window_noops(tmp_path, monkeypatch, now_utc, label):
    from cuttingboard import alert_runner

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    _patch_now(monkeypatch, now_utc)
    calls = _capture_execute(monkeypatch)

    assert alert_runner.main(["--routine-slot", label]) == 0
    assert calls == []


def test_prd319_routine_slot_deduped_like_cron_arrival(tmp_path, monkeypatch):
    from cuttingboard import alert_runner

    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    calls = _capture_execute(monkeypatch)

    _patch_now(monkeypatch, datetime(2026, 5, 19, 13, 30, 0, tzinfo=timezone.utc))
    assert alert_runner.main(["--routine-slot", "06:30"]) == 0
    assert len(calls) == 1
    # the real _execute_notify_run persists the slot post-send; the capture
    # stub does not, so persist it the way the runtime would before the
    # late heartbeat arrives for the same slot -- suppressed_same_slot
    from cuttingboard.notifications.hourly_slot import save_last_slot

    save_last_slot(calls[0]["slot_utc"])
    _patch_now(monkeypatch, datetime(2026, 5, 19, 13, 42, 0, tzinfo=timezone.utc))
    assert alert_runner.main(["--routine-slot", "06:30"]) == 0
    assert len(calls) == 1


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



# ---- Completion PR (2026-09-09): runner exit diagnostics, fresh-process ------
#
# The hourly job's process entrypoint is alert_runner (no cli_main), so the
# runner must configure logging itself or every INFO suppression line is
# dropped from the Actions log. caplog cannot prove that; these tests run the
# runner in a FRESH PROCESS with a fixed clock and a stubbed
# _execute_notify_run, and assert on the process's actual stderr.

_DRIVER = r'''
import json, sys
from datetime import datetime
from cuttingboard import alert_runner, config
cfg = json.loads(sys.argv[1])
fixed = datetime.fromisoformat(cfg["now"])
class _Fixed(datetime):
    @classmethod
    def now(cls, tz=None):
        return fixed if tz is None else fixed.astimezone(tz)
alert_runner.datetime = _Fixed
import cuttingboard.runtime as rt
def fake(*, mode, run_date, notify_mode, slot_utc=None, **kw):
    if cfg["behavior"] == "raise":
        raise RuntimeError("boom")
    return {"status": cfg["behavior"], "suppressed": False}
rt._execute_notify_run = fake
config.TELEGRAM_BOT_TOKEN = None
config.TELEGRAM_CHAT_ID = None
sys.exit(alert_runner.main(cfg["argv"]))
'''


def _fresh_run(tmp_path: Path, *, now: str, argv: list[str], behavior: str = "SUCCESS") -> tuple[int, str]:
    import os

    (tmp_path / "logs").mkdir(exist_ok=True)
    cfg = json.dumps({"now": now, "argv": argv, "behavior": behavior})
    # Pin the import to THIS checkout (an editable install elsewhere must not
    # shadow it in the fresh process).
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent)}
    proc = subprocess.run(
        [sys.executable, "-c", _DRIVER, cfg],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.returncode, proc.stderr


# Tue 2026-05-19 (PDT): 07:00 PT == 14:00Z.
_PDT_0700Z = "2026-05-19T14:00:00+00:00"


def test_runner_late_named_slot_logs_reason_slot_pt_time_and_signed_lag(tmp_path):
    rc, err = _fresh_run(tmp_path, now="2026-05-19T14:40:00+00:00", argv=["--routine-slot", "07:00"])
    assert rc == 0
    assert "hourly alert suppressed: reason=outside_routine_window" in err
    assert "intended_slot=07:00 PT (2026-05-19T07:00:00-07:00)" in err
    assert "now_pt=2026-05-19T07:40:00-07:00" in err
    assert "lag=+40m" in err
    assert "admission_window=+25m" in err and "exit=0" in err
    rows = _notification_records(tmp_path / "logs" / "audit.jsonl")
    assert rows[-1]["reason"] == "outside_routine_window"  # audit token unchanged
    assert rows[-1]["state_key"].endswith(":named=07:00")


def test_runner_exact_plus_25m_is_admitted_and_completes(tmp_path):
    rc, err = _fresh_run(tmp_path, now="2026-05-19T14:25:00+00:00", argv=["--routine-slot", "07:00"])
    assert rc == 0
    assert "hourly alert admitted: slot_utc=2026-05-19T14:00:00+00:00" in err
    assert "hourly alert completed: status=SUCCESS slot_utc=2026-05-19T14:00:00+00:00 exit=0" in err
    assert "suppressed" not in err


def test_runner_plus_26m_is_rejected_with_lag(tmp_path):
    rc, err = _fresh_run(tmp_path, now="2026-05-19T14:26:00+00:00", argv=["--routine-slot", "07:00"])
    assert rc == 0
    assert "reason=outside_routine_window" in err and "lag=+26m" in err
    assert "hourly alert completed" not in err


def test_runner_early_named_arrival_has_negative_lag(tmp_path):
    rc, err = _fresh_run(tmp_path, now="2026-05-19T13:57:00+00:00", argv=["--routine-slot", "07:00"])
    assert rc == 0
    assert "reason=outside_routine_window" in err and "lag=-3m" in err


@pytest.mark.parametrize(
    "label, fragment",
    [
        ("07:30", "intended_slot=invalid ('07:30' not an allowed PT slot)"),
        ("xx", "intended_slot=invalid ('xx')"),
    ],
)
def test_runner_invalid_named_slot_is_explicitly_invalid_never_invented(tmp_path, label, fragment):
    rc, err = _fresh_run(tmp_path, now="2026-05-19T14:40:00+00:00", argv=["--routine-slot", label])
    assert rc == 0
    assert "reason=outside_routine_window" in err and fragment in err
    assert "lag=" not in err


def test_runner_unnamed_inference_outside_window_reports_unavailable(tmp_path):
    rc, err = _fresh_run(tmp_path, now="2026-05-19T21:00:00+00:00", argv=[])  # 14:00 PT
    assert rc == 0
    assert "reason=outside_routine_window intended_slot=unavailable (inferred arrival" in err
    assert "now_pt=2026-05-19T14:00:00-07:00" in err


def test_runner_duplicate_slot_logs_reason_and_prior_delivery(tmp_path):
    from cuttingboard.notifications.hourly_slot import save_last_slot

    (tmp_path / "logs").mkdir()
    save_last_slot(datetime.fromisoformat(_PDT_0700Z), path=str(tmp_path / "logs" / "last_hourly_slot.json"))
    rc, err = _fresh_run(tmp_path, now="2026-05-19T14:10:00+00:00", argv=["--routine-slot", "07:00"])
    assert rc == 0
    assert "hourly alert suppressed: reason=suppressed_same_slot slot_utc=2026-05-19T14:00:00+00:00" in err
    assert "saved_at_utc=" in err and "exit=0" in err
    rows = _notification_records(tmp_path / "logs" / "audit.jsonl")
    assert rows[-1]["reason"] == "suppressed_same_slot"


def test_runner_forced_dispatch_bypasses_window_and_logs_it(tmp_path):
    rc, err = _fresh_run(tmp_path, now="2026-05-19T22:00:00+00:00", argv=["--force-slot"])
    assert rc == 0
    assert "hourly alert forced: slot_utc=2026-05-19T22:00:00+00:00" in err
    assert "hourly alert completed: status=SUCCESS" in err


def test_runner_healthy_halt_status_success_exits_zero(tmp_path):
    """A market-stress safety HALT returns SUMMARY_STATUS_SUCCESS (PRD-287);
    the runner's contract is status-only, so it completes healthy."""
    rc, err = _fresh_run(tmp_path, now="2026-05-19T14:05:00+00:00", argv=["--routine-slot", "07:00"])
    assert rc == 0 and "hourly alert completed: status=SUCCESS" in err


def test_runner_non_success_return_logs_failure_and_exits_one(tmp_path):
    rc, err = _fresh_run(tmp_path, now="2026-05-19T14:05:00+00:00", argv=["--routine-slot", "07:00"], behavior="FAIL")
    assert rc == 1
    assert "hourly alert failed: reason=non_success_return status=FAIL" in err and "exit=1" in err


def test_runner_exception_logs_backstop_reason_and_exits_one(tmp_path):
    rc, err = _fresh_run(tmp_path, now="2026-05-19T14:05:00+00:00", argv=["--force-slot"], behavior="raise")
    assert rc == 1
    assert "alert runner backstop caught exception" in err
    assert "hourly alert failed: reason=runner_level_exception error_type=RuntimeError exit=1" in err
    rows = _notification_records(tmp_path / "logs" / "audit.jsonl")
    assert rows[-1]["reason"] == "runner_level_exception"


def test_runner_configures_logging_only_when_no_handler_exists(monkeypatch):
    """basicConfig is a no-op under an existing handler (pytest/caplog, embedding)."""
    import logging

    from cuttingboard import alert_runner

    root = logging.getLogger()
    before = list(root.handlers)
    alert_runner._configure_logging()
    if before:
        assert root.handlers == before
