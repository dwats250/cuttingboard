#!/usr/bin/env python3
"""PRD-189: resolve the pipeline run mode for a Cuttingboard workflow invocation.

Replaces the exact-minute bash matcher in ``.github/workflows/cuttingboard.yml``,
which matched ``date -u +%H%M`` against literal cron minutes and so resolved
every queue-delayed scheduled run to ``noop`` and SUCCESS -- the pipeline did
zero work for ~33 days while reporting green.

The fix keys resolution on ``github.event.schedule`` (the cron string GitHub
reports) instead of wall-clock minutes, so a late start still resolves
correctly::

    5 13 * * 1-5   -> live      (PRD-299: the delayed OPEN fallback cron)
    30 23 * * 0    -> sunday

PRD-299 (CF clock / GitHub executor coordination): the OPEN/live heartbeat moved
from ``0 13`` to ``5 13`` -- a delayed coordinated fallback firing ~5 min after
the preferred Cloudflare OPEN dispatch (owner ruling 2026-08-11, CF-D4
SUPERSEDED-IN-PART). This module also validates ``slot``<->``mode`` consistency
for ``workflow_dispatch`` invocations (``validate_slot_mode``): a malformed
OPEN/PRE dispatch fails closed here, BEFORE the workflow's first-success no-op
decision, so it can never become a satisfying no-op.

Scope: the dedicated premarket crons that write fresh, publish-safe artifacts via
``cli_main`` (``python -m cuttingboard --mode ...``): live, sunday, and (PRD-193)
the 12:50 ``prefetch`` cache-warm slot. PRD-193 made prefetch publish-safe
(cache-warm only -- it sets no PUBLISH_READY, so it cannot trip the PRD-119
freshness gate) and persists its OHLCV warm-up cache (``data/cache``) via
``actions/cache`` so the 13:00 live run reads it warm; the trading-day freshness
fix is what makes that reuse real. The intraday/orb slots (orb_trajectory /
post_orb / midmorning / power_hour) are
likewise NOT resolved here: their real behavior lives in ``_execute_notify_run``
(the ``alert_runner`` / ``hourly_alert.yml`` path), not ``cli_main``, and the
intraday window is already covered by ``hourly_alert.yml``. PRD-189 removed
those intraday/orb crons from ``cuttingboard.yml``, and PRD-192 ratified the
``hourly_alert.yml`` coverage rather than re-homing the slots here. See
``docs/PROJECT_STATE.md``.

Because only dedicated crons remain, resolution is a pure cron-string lookup:
there is no wall-clock/timezone math and no ``logs/audit.jsonl`` read. The module
exposes a pure ``resolve(...)`` for unit tests; ``main()`` reads the GitHub
context from the environment and prints the resolved mode for the workflow's
``$GITHUB_OUTPUT``.
"""
from __future__ import annotations

import os
import sys

NOOP = "noop"

# Dedicated premarket crons -> job mode. Keyed on the exact cron string GitHub
# reports in github.event.schedule, so resolution is immune to queue delay --
# the cron string is identical no matter when the run actually starts.
_DEDICATED: dict[str, str] = {
    # PRD-319 R5: dual-seasonal delayed OPEN fallbacks (was the single "5 13").
    # 20 13 = 06:20 PDT-season fallback; 20 14 = 06:20 PST-season fallback —
    # ~20 min after the preferred Cloudflare 06:00 PT dispatch, year-round.
    # The off-season twin is no-oped by scripts/check_open_fallback_window.py
    # (season gate), NOT here: mode resolution stays a pure cron lookup so a
    # queue-delayed in-season fallback still resolves live.
    "20 13 * * 1-5": "live",
    "20 14 * * 1-5": "live",
    "30 23 * * 0": "sunday",
    "50 12 * * 1-5": "prefetch",  # PRD-193: publish-safe cache-warm slot
}
# The dropped intraday crons "50 13 * * 1-5" / "*/30 14-21 * * 1-5" would resolve
# to NOOP if ever supplied. PRD-189 removed them from cuttingboard.yml;
# hourly_alert.yml covers the intraday window.

# PRD-299 R2: slot -> required mode. workflow_dispatch is the only path carrying a
# slot input; schedule crons imply their slot by the _DEDICATED map + run-name.
_SLOT_MODE: dict[str, str] = {"OPEN": "live", "PRE": "prefetch"}


class SlotModeError(ValueError):
    """A slot/mode mismatch on a dispatch -> fail closed (no execution)."""


def validate_slot_mode(slot: str, mode: str) -> None:
    """PRD-299 R2: OPEN<->live, PRE<->prefetch, fail-closed on mismatch.

    An empty slot imposes no constraint (a legacy/operator dispatch that carries
    only ``mode``). A non-empty slot MUST be EXACT-CASE ``OPEN`` or ``PRE`` and
    match its mode, else SlotModeError.

    Exact-case is deliberate (Sol connector P2): the workflow's run-name carrier,
    concurrency group expression, and OPEN first-success pre-check all consume the
    raw ``inputs.slot`` and compare case-SENSITIVELY against ``OPEN``. If this
    validator lowercased/uppercased, a ``slot=open`` dispatch would pass here but
    be treated as a NON-OPEN run by every workflow predicate -> it would carry a
    ``CB-SLOT:open`` token, enter the ordinary concurrency group, skip the
    first-success pre-check, and could execute concurrently with / duplicate the
    automatic OPEN run. Rejecting non-exact-case here keeps the whole path
    consistent and fail-closed.
    """
    slot = (slot or "").strip()  # NOTE: no case-folding -- exact-case contract
    if not slot:
        return
    expected = _SLOT_MODE.get(slot)
    if expected is None:
        raise SlotModeError(f"unknown slot {slot!r} (expected exact-case OPEN or PRE)")
    if (mode or "").strip() != expected:
        raise SlotModeError(f"slot {slot} requires mode {expected!r}, got {(mode or '').strip()!r}")


def resolve(*, event_name: str, dispatch_mode: str, schedule: str) -> str:
    """Resolve the job mode. Pure: every input is passed in explicitly."""
    if event_name == "workflow_dispatch":
        # Explicit operator intent.
        return dispatch_mode or NOOP
    if event_name != "schedule":
        return NOOP
    return _DEDICATED.get((schedule or "").strip(), NOOP)


def main() -> int:
    event_name = os.environ.get("CB_EVENT_NAME", "")
    dispatch_mode = os.environ.get("CB_DISPATCH_MODE", "")
    mode = resolve(
        event_name=event_name,
        dispatch_mode=dispatch_mode,
        schedule=os.environ.get("CB_SCHEDULE", ""),
    )
    # PRD-299 R2: fail closed on a slot/mode mismatch, BEFORE any downstream
    # first-success no-op decision. Only workflow_dispatch carries a slot input.
    if event_name == "workflow_dispatch":
        try:
            validate_slot_mode(os.environ.get("CB_SLOT", ""), dispatch_mode)
        except SlotModeError as exc:
            print(f"CB_SLOT_MODE_ERROR: {exc}", file=sys.stderr)
            return 2
    print(mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
