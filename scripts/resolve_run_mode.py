#!/usr/bin/env python3
"""PRD-189: resolve the pipeline run mode for a Cuttingboard workflow invocation.

Replaces the exact-minute bash matcher in ``.github/workflows/cuttingboard.yml``,
which resolved every queue-delayed scheduled run to ``noop`` because GitHub
Actions starts cron runs off-the-minute (the freeze hid for ~33 days behind a
pipeline that did zero work but reported SUCCESS).

Resolution (schedule events):
  * The four dedicated crons are disambiguated 1:1 by ``github.event.schedule``
    (the cron string GitHub reports), so a late start still resolves correctly::

        50 12 * * 1-5  -> prefetch          0 13 * * 1-5  -> live
        50 13 * * 1-5  -> orb_trajectory   30 23 * * 0    -> sunday

  * The intraday ``*/30 14-21`` cron shares one cron string across every fire,
    so the actual UTC start time is mapped to the nearest ACTIVE slot within
    ``TOLERANCE_MINUTES``; fires that land on no active slot resolve to ``noop``.

Dedup (intraday only): an intraday slot already represented by a committed
pipeline record for today (``logs/audit.jsonl``) resolves to ``noop`` so a late
or duplicate ``*/30`` invocation never double-fires post_orb / power_hour. The
dedicated crons need no dedup -- their unique cron string fires once per UTC day
-- and time-window dedup would be unsafe for them anyway because the prefetch
(12:50) and live (13:00) windows overlap. The active intraday windows are
disjoint, so a time-window match identifies exactly one intraday slot. Source of
truth is the committed ``audit.jsonl`` -- the same record the regime scoreboard
reads -- never a marker file.

The module exposes a pure ``resolve(...)`` for unit tests; ``main()`` reads the
GitHub context from the environment and prints the resolved mode for the
workflow's ``$GITHUB_OUTPUT``.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

NOOP = "noop"
TOLERANCE_MINUTES = 15

# Dedicated crons -> (mode, nominal minute-of-day UTC). Keyed on the exact cron
# string GitHub reports in github.event.schedule, so resolution is delay-immune.
_DEDICATED: dict[str, tuple[str, int]] = {
    "50 12 * * 1-5": ("prefetch", 12 * 60 + 50),
    "0 13 * * 1-5": ("live", 13 * 60 + 0),
    "50 13 * * 1-5": ("orb_trajectory", 13 * 60 + 50),
    "30 23 * * 0": ("sunday", 23 * 60 + 30),
}

# The intraday monitor cron, and the active slots within it (nominal -> mode).
# All other fires of this cron (15:00, 15:30, ...) carry no active slot -> noop.
_INTRADAY_CRON = "*/30 14-21 * * 1-5"
_INTRADAY_SLOTS: dict[int, str] = {
    14 * 60 + 30: "post_orb",
    16 * 60 + 30: "midmorning",
    19 * 60 + 0: "power_hour",
    20 * 60 + 0: "power_hour",
}


def _minute_of_day(dt: datetime) -> int:
    dt = dt.astimezone(timezone.utc)
    return dt.hour * 60 + dt.minute


def _nearest_intraday_slot(minute: int, tolerance: int) -> tuple[str, int] | None:
    """The active intraday ``(mode, nominal)`` whose nominal minute is within
    ``tolerance`` of ``minute`` (the closest one), or None when none is in range.
    """
    best: tuple[int, int, str] | None = None  # (distance, nominal, mode)
    for nominal, mode in _INTRADAY_SLOTS.items():
        distance = abs(minute - nominal)
        if distance <= tolerance and (best is None or distance < best[0]):
            best = (distance, nominal, mode)
    if best is None:
        return None
    return best[2], best[1]


def _parse_run_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _slot_already_fired(
    audit_path: str | Path, now: datetime, nominal_minute: int, tolerance: int
) -> bool:
    """True when a committed pipeline-shaped record for *today* (UTC) sits within
    ``tolerance`` minutes of ``nominal_minute``.

    Pipeline records carry ``outcome`` + ``run_at_utc`` + ``date`` and no
    ``event`` key (notification records are skipped) -- the same shape the
    regime-history aggregation reads. A missing/unreadable audit log means
    "not fired".
    """
    path = Path(audit_path)
    if not path.exists():
        return False
    today = now.astimezone(timezone.utc).date()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict) or "event" in rec:
            continue
        if "outcome" not in rec or "run_at_utc" not in rec or "date" not in rec:
            continue
        run_at = _parse_run_at(rec.get("run_at_utc"))
        if run_at is None or run_at.date() != today:
            continue
        if abs(_minute_of_day(run_at) - nominal_minute) <= tolerance:
            return True
    return False


def resolve(
    *,
    event_name: str,
    dispatch_mode: str,
    schedule: str,
    now: datetime,
    audit_path: str | Path,
    tolerance: int = TOLERANCE_MINUTES,
) -> str:
    """Resolve the job mode. Pure: every input is passed in explicitly."""
    if event_name == "workflow_dispatch":
        # Explicit operator intent; never deduped, never time-resolved.
        return dispatch_mode or NOOP
    if event_name != "schedule":
        return NOOP

    schedule = (schedule or "").strip()
    if schedule in _DEDICATED:
        # Delay-immune: the unique cron string fixes the slot.
        return _DEDICATED[schedule][0]
    if schedule == _INTRADAY_CRON:
        slot = _nearest_intraday_slot(_minute_of_day(now), tolerance)
        if slot is None:
            return NOOP
        mode, nominal = slot
        if _slot_already_fired(audit_path, now, nominal, tolerance):
            return NOOP
        return mode
    return NOOP


def main() -> int:
    mode = resolve(
        event_name=os.environ.get("CB_EVENT_NAME", ""),
        dispatch_mode=os.environ.get("CB_DISPATCH_MODE", ""),
        schedule=os.environ.get("CB_SCHEDULE", ""),
        now=datetime.now(timezone.utc),
        audit_path=os.environ.get("CB_AUDIT_PATH", "logs/audit.jsonl"),
    )
    print(mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
