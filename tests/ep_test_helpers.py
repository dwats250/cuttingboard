"""PRD-340 Slice 2: shared test helper for threading a session-valid, resolver-
provenanced EffectivePermission into caller tests and payload/contract fixtures.

Uses the SAME resolver production uses (never a hand-built carrier), so a test's
EP-derived authority matches the fixture's intended (outcome / halt / lock) state.
"""

from __future__ import annotations

from cuttingboard import config
from cuttingboard import effective_permission as _ep


def make_ep(
    *, outcome: str = "NO_TRADE", system_halted: bool = False,
    operator_locked: bool = False, session_date: str = "2026-01-15",
):
    """Resolve an EffectivePermission for tests. ``outcome`` in {TRADE, NO_TRADE}."""
    return _ep.resolve_effective_permission(
        mode="live", outcome_is_trade=(outcome == "TRADE"),
        system_halted=system_halted, operator_locked=operator_locked,
        session_date=session_date, run_uid="t" * 32,
        posture_permission_line=("Longs allowed." if outcome == "TRADE"
                                 else "No new trades permitted."),
        operator_lock_line=config.OPERATOR_LOCK_PERMISSION,
    )


def ep_envelope(**kw) -> dict:
    """The persisted/served envelope for a resolved test EP."""
    return make_ep(**kw).to_envelope()


def ep_for_payload(payload: dict, *, session_date: str | None = None):
    """Derive a fixture EP that matches a payload's intended state and STAMP the
    canonical envelope onto it, so a cross-process reader (render_report_from_payload,
    the board) admits it. Returns the EP object for callers that also need it."""
    sd = session_date or (payload.get("meta", {}).get("timestamp", "") or "2026-01-15")[:10] or "2026-01-15"
    run_status = payload.get("run_status")
    halted = run_status == "ERROR"
    trade = bool(payload.get("sections", {}).get("top_trades")) and not halted
    locked = payload.get("summary", {}).get("permission") == config.OPERATOR_LOCK_PERMISSION
    ep = make_ep(
        outcome="TRADE" if trade else "NO_TRADE",
        system_halted=halted, operator_locked=locked, session_date=sd)
    payload[_ep.CANONICAL_FIELD] = ep.to_envelope()
    return ep
