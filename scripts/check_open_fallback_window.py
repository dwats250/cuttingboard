#!/usr/bin/env python3
"""PRD-319 R5: season gate for the dual-seasonal OPEN fallback crons.

The pipeline's delayed OPEN fallback is a PAIR of fixed-UTC crons so its PT
wall-clock holds year-round (owner ruling 2026-08-28 Q2, option iii-adjacent):
``20 13 * * 1-5`` is the PDT-season fallback (06:20 PT) and ``20 14 * * 1-5``
the PST-season fallback (06:20 PT). Each weekday BOTH fire; exactly one is in
season. This gate no-ops the off-season twin.

The gate is keyed on SEASON (the current America/Los_Angeles UTC offset), not
on a wall-clock window, deliberately: GitHub cron delivery is observed 45-55
minutes late, and a wall-clock window would gate off a late IN-SEASON fallback
— an availability regression. An offset match is immune to delivery delay,
while the off-season twin (a full hour off) can never match.

Contract (mirrors ``resolve_run_mode.py``: stdlib only, pure ``check`` for
tests, fail-closed ``main``):

  check(cron, now_utc) -> "IN_SEASON" | "OFF_SEASON_NOOP"; raises
  UnknownCronError for a cron not in the pair.

  main() reads the fired cron from ``CB_EVENT_SCHEDULE`` (the workflow passes
  ``github.event.schedule``), prints the verdict for ``$GITHUB_OUTPUT``
  consumption, exit 0. An unknown cron or unresolvable offset exits NON-ZERO
  (fail-closed; PRD-198 invariant 1) — the workflow then fails visibly rather
  than silently running or skipping.

Only schedule-event OPEN fallback runs consult this gate. ``workflow_dispatch``
(the Cloudflare OPEN), Sunday, and prefetch never do.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_PT = ZoneInfo("America/Los_Angeles")

# cron string (as github.event.schedule reports it) -> the PT UTC-offset hours
# under which that cron is the IN-SEASON 06:20 PT fallback.
_CRON_SEASON_OFFSET_HOURS: dict[str, int] = {
    "20 13 * * 1-5": -7,  # PDT
    "20 14 * * 1-5": -8,  # PST
}

IN_SEASON = "IN_SEASON"
OFF_SEASON_NOOP = "OFF_SEASON_NOOP"


class UnknownCronError(ValueError):
    """A cron not in the fallback pair reached the gate -> fail closed."""


def check(cron: str, now_utc: datetime) -> str:
    """Pure season verdict for ``cron`` at ``now_utc`` (tz-aware)."""
    if now_utc.tzinfo is None:
        raise ValueError("check requires a tz-aware datetime")
    expected = _CRON_SEASON_OFFSET_HOURS.get((cron or "").strip())
    if expected is None:
        raise UnknownCronError(
            f"unknown OPEN fallback cron {cron!r} (expected one of "
            f"{sorted(_CRON_SEASON_OFFSET_HOURS)})"
        )
    offset = now_utc.astimezone(_PT).utcoffset()
    if offset is None:  # pragma: no cover - zoneinfo always yields an offset
        raise UnknownCronError("unresolvable America/Los_Angeles offset")
    return IN_SEASON if offset.total_seconds() == expected * 3600 else OFF_SEASON_NOOP


def main() -> int:
    cron = os.environ.get("CB_EVENT_SCHEDULE", "")
    try:
        verdict = check(cron, datetime.now(timezone.utc))
    except (UnknownCronError, ValueError) as exc:
        print(f"open-fallback-gate: FAIL-CLOSED: {exc}", file=sys.stderr)
        return 2
    print(verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
