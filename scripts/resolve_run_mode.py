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
    so the UTC start time is attributed to the active slot it belongs to. The
    attribution is LATE-ONLY -- a run is attributed to a slot only when it starts
    at or after that slot's nominal time, within ``TOLERANCE_MINUTES`` -- because
    queue delay only ever makes a run late, never early. A symmetric window would
    let an inactive earlier fire (14:00 delayed to 14:15) claim a later active
    slot (14:30) and run before its market-data window (Codex P2). Fires that
    attribute to no active slot resolve to ``noop``.

For the intraday start time to mean "run start" rather than "resolver execution
time", the ``Determine run mode`` workflow step runs right after Python setup,
BEFORE install/lint/test/engine-doctor -- otherwise those multi-minute pre-steps
would push the sampled time past the tolerance window and silently noop a valid
late run (Codex P1).

Dedup (intraday only): an intraday slot already represented by a committed
pipeline record for today (``logs/audit.jsonl``) resolves to ``noop`` so a late
or duplicate ``*/30`` invocation never double-fires post_orb / power_hour. A
record counts as a given slot firing only when the record's OWN ``run_at_utc``
attributes to that slot under the same late-only rule, so an earlier inactive
fire or a late different-slot run never suppresses the slot. The dedicated crons
need no dedup -- their unique cron string fires once per UTC day -- and dedup
would be unsafe for them anyway because the prefetch (12:50) and live (13:00)
windows overlap. Source of truth is the committed ``audit.jsonl`` -- the same
record the regime scoreboard reads -- never a marker file.

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


def _intraday_slot_for_start(minute: int, tolerance: int) -> tuple[str, int] | None:
    """The active intraday ``(mode, nominal)`` that a run STARTING at ``minute``
    (minute-of-day UTC) belongs to, or None.

    Attribution is LATE-ONLY: a run is attributed to a slot only when it starts
    at or after the slot's nominal time, within ``tolerance`` minutes -- queue
    delay only ever makes a run late, never early. A symmetric window would let
    an inactive earlier ``*/30`` fire (14:00 delayed to 14:15) claim a later
    active slot (14:30) and run before its market-data window, then suppress the
    correctly-timed fire via dedup (Codex P2). The active slots are >=60 min
    apart, so at most one is ever in range.
    """
    best: tuple[int, int, str] | None = None  # (delay, nominal, mode)
    for nominal, mode in _INTRADAY_SLOTS.items():
        delay = minute - nominal
        if 0 <= delay <= tolerance and (best is None or delay < best[0]):
            best = (delay, nominal, mode)
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
    """True when a committed pipeline-shaped record for *today* (UTC) attributes
    to the slot at ``nominal_minute``.

    A record counts only when its OWN ``run_at_utc`` attributes to this slot
    under the same late-only rule as resolution (``_intraday_slot_for_start``),
    so an earlier inactive fire or a late different-slot run never suppresses
    this slot. Pipeline records carry ``outcome`` + ``run_at_utc`` + ``date`` and
    no ``event`` key (notification records are skipped) -- the same shape the
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
        attributed = _intraday_slot_for_start(_minute_of_day(run_at), tolerance)
        if attributed is not None and attributed[1] == nominal_minute:
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
        slot = _intraday_slot_for_start(_minute_of_day(now), tolerance)
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
