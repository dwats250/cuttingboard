"""PRD-189: tests for scripts/resolve_run_mode.py.

Covers the four R3 cases (on-time, late-within-tolerance, late-beyond-
tolerance, already-fired-today) plus the hybrid resolver's load-bearing
guarantees: dedicated crons are delay-immune (schedule-string disambiguation),
intraday slots are queue-delay tolerant, and the audit.jsonl fired-today dedup
prevents double-fires without a prefetch run ever suppressing the live run.
"""
from __future__ import annotations

import importlib.util
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cuttingboard.runtime import build_parser

_REPO = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO / ".github" / "workflows" / "cuttingboard.yml"
_SPEC = importlib.util.spec_from_file_location(
    "resolve_run_mode", _REPO / "scripts" / "resolve_run_mode.py"
)
assert _SPEC and _SPEC.loader
rrm = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(rrm)

# A weekday and a Sunday (resolution ignores weekday — the cron string is
# authoritative — but realistic dates keep the fixtures honest).
_TUE = (2026, 6, 16)
_SUN = (2026, 6, 14)


def _utc(date: tuple[int, int, int], h: int, mi: int) -> datetime:
    return datetime(*date, h, mi, tzinfo=timezone.utc)


def _resolve(
    schedule: str,
    now: datetime,
    *,
    audit_path: str | Path = "/nonexistent/audit.jsonl",
    event: str = "schedule",
    dispatch: str = "",
) -> str:
    return rrm.resolve(
        event_name=event,
        dispatch_mode=dispatch,
        schedule=schedule,
        now=now,
        audit_path=audit_path,
    )


def _pipeline_rec(run_at: datetime, *, mode: str = "MIXED") -> dict:
    # Pipeline-shaped audit record: outcome + run_at_utc + date, no `event`.
    return {
        "outcome": "NO_TRADE",
        "run_at_utc": run_at.isoformat(),
        "date": run_at.astimezone(timezone.utc).strftime("%Y-%m-%d"),
        "router_mode": mode,
    }


def _write_audit(tmp_path: Path, records: list[dict]) -> Path:
    path = tmp_path / "audit.jsonl"
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + ("\n" if records else ""),
        encoding="utf-8",
    )
    return path


# --- R3 on-time: dedicated crons resolve by schedule string ----------------
@pytest.mark.parametrize(
    "schedule,date,h,mi,expected",
    [
        ("50 12 * * 1-5", _TUE, 12, 50, "prefetch"),
        ("0 13 * * 1-5", _TUE, 13, 0, "live"),
        ("50 13 * * 1-5", _TUE, 13, 50, "orb_trajectory"),
        ("30 23 * * 0", _SUN, 23, 30, "sunday"),
        ("*/30 14-21 * * 1-5", _TUE, 14, 30, "post_orb"),
        ("*/30 14-21 * * 1-5", _TUE, 16, 30, "midmorning"),
        ("*/30 14-21 * * 1-5", _TUE, 19, 0, "power_hour"),
        ("*/30 14-21 * * 1-5", _TUE, 20, 0, "power_hour"),
    ],
)
def test_on_time_resolves_to_slot(schedule, date, h, mi, expected) -> None:
    assert _resolve(schedule, _utc(date, h, mi)) == expected


# --- R1 dedicated crons are delay-immune -----------------------------------
@pytest.mark.parametrize(
    "schedule,h,mi,expected",
    [
        ("0 13 * * 1-5", 13, 18, "live"),       # 18 min late, still live
        ("50 12 * * 1-5", 12, 58, "prefetch"),  # 8 min late — pure-time would drift to live
        ("50 13 * * 1-5", 14, 5, "orb_trajectory"),  # 15 min late
    ],
)
def test_dedicated_cron_is_delay_immune(schedule, h, mi, expected) -> None:
    assert _resolve(schedule, _utc(_TUE, h, mi)) == expected


# --- R1 intraday queue-delay tolerance -------------------------------------
@pytest.mark.parametrize(
    "h,mi,expected",
    [
        (14, 42, "post_orb"),    # 12 min late, within ±15
        (16, 45, "midmorning"),  # 15 min late, on the boundary
        (19, 7, "power_hour"),
        (20, 12, "power_hour"),
        (19, 14, "power_hour"),  # 14 min late
    ],
)
def test_intraday_late_within_tolerance(h, mi, expected) -> None:
    assert _resolve("*/30 14-21 * * 1-5", _utc(_TUE, h, mi)) == expected


# --- R3 late-beyond-tolerance / inactive fires -> noop ---------------------
@pytest.mark.parametrize(
    "h,mi",
    [
        (15, 0),   # nearest active slot (14:30) is 30 min away
        (14, 48),  # 18 min past post_orb (> ±15)
        (14, 0),   # inactive */30 fire
        (18, 0),   # inactive */30 fire
        (16, 0),   # 30 min from midmorning
        (19, 30),  # between the two power_hour slots, 30 min from each
    ],
)
def test_intraday_beyond_tolerance_is_noop(h, mi) -> None:
    assert _resolve("*/30 14-21 * * 1-5", _utc(_TUE, h, mi)) == "noop"


# --- P2: an early/inactive */30 fire must NOT claim a later active slot ------
@pytest.mark.parametrize(
    "h,mi",
    [
        (14, 15),  # 14:00 cron delayed to 14:15 — would hit post_orb under symmetric ±15
        (14, 20),  # still before post_orb's nominal
        (14, 29),  # one minute before nominal
        (19, 45),  # 19:30 cron delayed to 19:45 — would hit 20:00 power_hour
        (16, 20),  # before midmorning
    ],
)
def test_early_fire_does_not_claim_future_slot(h, mi) -> None:
    assert _resolve("*/30 14-21 * * 1-5", _utc(_TUE, h, mi)) == "noop"


@pytest.mark.parametrize(
    "h,mi,expected",
    [
        (14, 30, "post_orb"),  # exactly nominal (delay 0)
        (14, 45, "post_orb"),  # nominal + tolerance (inclusive)
        (14, 46, "noop"),      # one minute past tolerance
    ],
)
def test_late_only_tolerance_boundary(h, mi, expected) -> None:
    assert _resolve("*/30 14-21 * * 1-5", _utc(_TUE, h, mi)) == expected


def test_late_other_slot_record_does_not_suppress(tmp_path) -> None:
    # A severely-late orb_trajectory run (nominal 13:50) records run_at_utc at
    # 14:16; that record attributes to no intraday slot under the late-only rule,
    # so it must not suppress a genuine post_orb fire.
    audit = _write_audit(tmp_path, [_pipeline_rec(_utc(_TUE, 14, 16))])
    assert _resolve("*/30 14-21 * * 1-5", _utc(_TUE, 14, 35), audit_path=audit) == "post_orb"


def test_unknown_schedule_is_noop() -> None:
    assert _resolve("0 0 * * *", _utc(_TUE, 0, 0)) == "noop"
    assert _resolve("", _utc(_TUE, 13, 0)) == "noop"


# --- workflow_dispatch: explicit operator intent, never resolved/deduped ----
def test_workflow_dispatch_returns_dispatch_mode(tmp_path) -> None:
    audit = _write_audit(tmp_path, [_pipeline_rec(_utc(_TUE, 14, 33))])
    # Returns the requested mode regardless of time or an existing record.
    assert _resolve("", _utc(_TUE, 9, 17), event="workflow_dispatch",
                    dispatch="verify", audit_path=audit) == "verify"
    assert _resolve("", _utc(_TUE, 14, 35), event="workflow_dispatch",
                    dispatch="post_orb", audit_path=audit) == "post_orb"


def test_workflow_dispatch_empty_mode_is_noop() -> None:
    assert _resolve("", _utc(_TUE, 13, 0), event="workflow_dispatch", dispatch="") == "noop"


# --- R2 fired-today dedup (intraday) ---------------------------------------
def test_intraday_fires_when_no_record(tmp_path) -> None:
    audit = _write_audit(tmp_path, [])
    assert _resolve("*/30 14-21 * * 1-5", _utc(_TUE, 14, 40), audit_path=audit) == "post_orb"


def test_intraday_deduped_when_slot_already_fired_today(tmp_path) -> None:
    # A committed post_orb-window record at 14:33 today -> a later */30 fire that
    # resolves to post_orb is suppressed (no double-fire).
    audit = _write_audit(tmp_path, [_pipeline_rec(_utc(_TUE, 14, 33))])
    assert _resolve("*/30 14-21 * * 1-5", _utc(_TUE, 14, 40), audit_path=audit) == "noop"


def test_dedup_is_scoped_to_today(tmp_path) -> None:
    # Yesterday's record in the same window must not suppress today's slot.
    yesterday = _utc(_TUE, 14, 33) - timedelta(days=1)
    audit = _write_audit(tmp_path, [_pipeline_rec(yesterday)])
    assert _resolve("*/30 14-21 * * 1-5", _utc(_TUE, 14, 40), audit_path=audit) == "post_orb"


def test_dedup_ignores_notification_records(tmp_path) -> None:
    # Notification records carry an `event` key and are not pipeline-shaped.
    notif = {"event": "notification", "run_at_utc": _utc(_TUE, 14, 33).isoformat(),
             "transport": "telegram"}
    audit = _write_audit(tmp_path, [notif])
    assert _resolve("*/30 14-21 * * 1-5", _utc(_TUE, 14, 40), audit_path=audit) == "post_orb"


def test_power_hour_slots_are_independent(tmp_path) -> None:
    # A 19:00 power_hour record must not suppress the distinct 20:00 power_hour
    # slot (disjoint dedup windows).
    audit = _write_audit(tmp_path, [_pipeline_rec(_utc(_TUE, 19, 2))])
    assert _resolve("*/30 14-21 * * 1-5", _utc(_TUE, 20, 0), audit_path=audit) == "power_hour"


def test_prefetch_record_does_not_suppress_live(tmp_path) -> None:
    # The hybrid's core guarantee: dedicated crons are NOT time-window deduped,
    # so a prefetch run at 12:52 (whose window overlaps the live window) never
    # suppresses the 13:00 live run.
    audit = _write_audit(tmp_path, [_pipeline_rec(_utc(_TUE, 12, 52))])
    assert _resolve("0 13 * * 1-5", _utc(_TUE, 13, 5), audit_path=audit) == "live"


def test_missing_audit_log_means_not_fired(tmp_path) -> None:
    missing = tmp_path / "does_not_exist.jsonl"
    assert _resolve("*/30 14-21 * * 1-5", _utc(_TUE, 14, 30), audit_path=missing) == "post_orb"


# --- Resolver outputs must map to CLI invocations the parser accepts ---------
# Guards the Codex P1: a resolved slot (e.g. orb_trajectory) is a --notify-mode,
# not a --mode, so the dispatch step must invoke `--mode live --notify-mode
# <slot>`; `--mode orb_trajectory` exits argparse with code 2 and writes no
# record. These tests fail in CI on any invalid mode/notify-mode combo.

_INVOCATION_RE = re.compile(
    r"python -m cuttingboard --mode (\S+) --notify-mode (\S+)"
)


def _scheduled_modes() -> set[str]:
    """Every job_mode the scheduled resolver can emit (excluding noop)."""
    return {mode for mode, _ in rrm._DEDICATED.values()} | set(
        rrm._INTRADAY_SLOTS.values()
    )


def test_every_workflow_invocation_is_parser_valid() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    invocations = _INVOCATION_RE.findall(text)
    assert invocations, "no `python -m cuttingboard --mode ... --notify-mode ...` lines found"
    parser = build_parser()
    for mode, notify in invocations:
        # argparse exits (SystemExit) on an invalid choice; a valid combo parses.
        parser.parse_args(["--mode", mode, "--notify-mode", notify])


def test_every_scheduled_slot_is_wired_to_a_valid_dispatch_step() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    invocations = _INVOCATION_RE.findall(text)
    notify_modes_used = {notify for _, notify in invocations}
    parser = build_parser()
    for mode in _scheduled_modes():
        if mode in {"prefetch", "live", "sunday"}:
            # Dedicated pipeline modes: dispatched as `--mode <mode>` directly.
            assert f"--mode {mode} " in text, f"{mode} has no dispatch invocation"
            parser.parse_args(["--mode", mode, "--notify-mode", "premarket"])
        else:
            # Intraday/orb slots are notify-modes run on the live base.
            assert mode in notify_modes_used, f"slot {mode} not wired to a --notify-mode invocation"
            parser.parse_args(["--mode", "live", "--notify-mode", mode])
        # The resolver's job_mode must gate a dispatch step.
        assert f"job_mode == '{mode}'" in text, f"{mode} has no dispatch `if:` guard"
