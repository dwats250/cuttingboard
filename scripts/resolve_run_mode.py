#!/usr/bin/env python3
"""PRD-189: resolve the pipeline run mode for a Cuttingboard workflow invocation.

Replaces the exact-minute bash matcher in ``.github/workflows/cuttingboard.yml``,
which matched ``date -u +%H%M`` against literal cron minutes and so resolved
every queue-delayed scheduled run to ``noop`` and SUCCESS -- the pipeline did
zero work for ~33 days while reporting green.

The fix keys resolution on ``github.event.schedule`` (the cron string GitHub
reports) instead of wall-clock minutes, so a late start still resolves
correctly::

    0 13 * * 1-5   -> live
    30 23 * * 0    -> sunday

Scope (PRD-189): only the dedicated premarket crons that write fresh,
publish-safe artifacts via ``cli_main`` (``python -m cuttingboard --mode ...``):
live and sunday. The 12:50 ``prefetch`` cron is intentionally NOT resolved here
(it resolves to ``noop``): ``execute_prefetch`` writes no fresh payload/run, so
publishing on that slot would trip the PRD-119 freshness gate, and its OHLCV
warm-up cache (``data/cache``) is not persisted across runs anyway. Re-enabling
prefetch with real cache persistence + a publish-safe path is deferred to a
follow-up PRD (cache persistence -- distinct from PRD-192's notify routing). The
intraday/orb slots (orb_trajectory / post_orb / midmorning / power_hour) are
likewise NOT resolved here: their real behavior lives in ``_execute_notify_run``
(the ``alert_runner`` / ``hourly_alert.yml`` path), not ``cli_main``, and the
intraday window is already covered by ``hourly_alert.yml``; correctly homing
those slots (plus a per-slot audit marker for dedup) is deferred to PRD-192. See
``docs/PROJECT_STATE.md``.

Because only dedicated crons remain, resolution is a pure cron-string lookup:
there is no wall-clock/timezone math and no ``logs/audit.jsonl`` read. The module
exposes a pure ``resolve(...)`` for unit tests; ``main()`` reads the GitHub
context from the environment and prints the resolved mode for the workflow's
``$GITHUB_OUTPUT``.
"""
from __future__ import annotations

import os

NOOP = "noop"

# Dedicated premarket crons -> job mode. Keyed on the exact cron string GitHub
# reports in github.event.schedule, so resolution is immune to queue delay --
# the cron string is identical no matter when the run actually starts.
_DEDICATED: dict[str, str] = {
    "0 13 * * 1-5": "live",
    "30 23 * * 0": "sunday",
}
# Parked dead-noop crons -- present in cuttingboard.yml `on.schedule` but resolved
# to NOOP, pending a future cron tidy-up: "50 12 * * 1-5" (prefetch, deferred to
# the prefetch-rework PRD) and the intraday crons "50 13 * * 1-5" /
# "*/30 14-21 * * 1-5" (deferred to PRD-192).


def resolve(*, event_name: str, dispatch_mode: str, schedule: str) -> str:
    """Resolve the job mode. Pure: every input is passed in explicitly."""
    if event_name == "workflow_dispatch":
        # Explicit operator intent.
        return dispatch_mode or NOOP
    if event_name != "schedule":
        return NOOP
    return _DEDICATED.get((schedule or "").strip(), NOOP)


def main() -> int:
    mode = resolve(
        event_name=os.environ.get("CB_EVENT_NAME", ""),
        dispatch_mode=os.environ.get("CB_DISPATCH_MODE", ""),
        schedule=os.environ.get("CB_SCHEDULE", ""),
    )
    print(mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
