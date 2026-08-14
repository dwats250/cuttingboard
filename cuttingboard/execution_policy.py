"""
Execution policy materialization (PRD-051).

This layer does not execute orders. It is the final deterministic pass that
decides whether an already-created TradeDecision remains ALLOW_TRADE or is
downgraded to BLOCK_TRADE before contract and audit materialization.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from cuttingboard import config
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE, TradeDecision

POLICY_STAGE = "EXECUTION_POLICY"
POLICY_SOURCE = "execution_policy"
POLICY_ALLOWED = "policy_allowed"
POLICY_ORB_UNAVAILABLE = "orb_unavailable"
POLICY_PRE_POLICY_BLOCK = "pre_policy_block"
POLICY_LOW_CONFIDENCE = "low_confidence"
POLICY_CHAOTIC_REGIME = "chaotic_regime"
POLICY_STAY_FLAT = "stay_flat"
POLICY_SESSION_TRADE_LIMIT = "session_trade_limit"
POLICY_LOSS_LOCKOUT = "loss_lockout"
POLICY_COOLDOWN = "cooldown"
POLICY_ORB_INSIDE_RANGE = "orb_inside_range"
# PRD-271 / CB-07: the ORB carrier's session provenance is INVALID (stale prior
# session, session mismatch, malformed/impossible bounds, mixed-session or
# unordered formation bars). Distinct from POLICY_ORB_UNAVAILABLE (no range yet
# — a benign abstain that preserves the existing allow-but-flag path): an
# untrustworthy ORB fails CLOSED at the gate rather than silently allowing.
POLICY_ORB_INVALID = "orb_invalid_session"
POLICY_MACRO_PRESSURE_CONFLICT = "macro_pressure_conflict"
# PRD-284: canonical reason when an allowed decision's policy-scaled position
# floors to zero contracts. Distinct from options.py's
# SMALLEST_CONTRACT_EXCEEDS_BUDGET (OPTIONS_SIZING, pre-TradeDecision).
POLICY_SIZE_ROUNDS_TO_ZERO = "size_rounds_to_zero"
# PRD-286 / CB-05: macro-pressure COMPUTATION FAILURE. MACRO_PRESSURE_UNAVAILABLE
# is the fail-closed pressure-carrier sentinel returned by
# runtime::_compute_overall_pressure when macro-pressure computation raises —
# distinct from a genuinely computed "UNKNOWN" (drivers merely absent). It must
# never be interpreted as an unconstrained state: it blocks direction-agnostically
# with reason POLICY_MACRO_PRESSURE_UNAVAILABLE.
MACRO_PRESSURE_UNAVAILABLE = "UNAVAILABLE"
POLICY_MACRO_PRESSURE_UNAVAILABLE = "macro_pressure_unavailable"
# PRD-304: the manual operator-availability lock. When the operator cannot
# monitor, an otherwise-ALLOW decision is blocked at EXECUTION_POLICY with this
# reason. It intercepts ONLY the allow outcome: an upstream block or a natural
# in-policy block (low confidence, chaotic, macro conflict, size-to-zero, ...)
# keeps its own reason, so the lock never overwrites a more specific block.
POLICY_OPERATOR_CANNOT_MONITOR = "operator_cannot_monitor"

_VALID_PRESSURE_VALUES = frozenset(
    {"RISK_ON", "RISK_OFF", "MIXED", "NEUTRAL", "UNKNOWN", MACRO_PRESSURE_UNAVAILABLE}
)


@dataclass(frozen=True)
class OrbPolicyState:
    price: Optional[float] = None
    orb_high: Optional[float] = None
    orb_low: Optional[float] = None
    continuation_breakout: bool = False
    # PRD-271 / CB-07: transient session-provenance verdict threaded from the
    # producer. True when the ORB observation is INVALID (untrustworthy
    # provenance) and must fail closed; never persisted.
    invalid: bool = False


@dataclass(frozen=True)
class ExecutionSessionState:
    prior_trade_count: int = 0
    consecutive_losses: int = 0
    last_trade_at_utc: Optional[datetime] = None


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    size_multiplier: float


def size_multiplier_for_confidence(confidence: float) -> float:
    """Return deterministic R-size multiplier for regime confidence."""
    confidence = float(confidence)
    if confidence < 0.60:
        return 0.0
    if confidence >= 0.80:
        return 1.0
    if confidence >= 0.70:
        return 0.75
    return 0.50


def load_execution_session_state(
    *,
    run_at_utc: datetime,
    session_date: str,
    audit_log_path: str | Path,
    evaluation_log_path: str | Path,
) -> ExecutionSessionState:
    """Return dormant execution-session state (PRD-285 / CB-04).

    Actual-trades-only doctrine: an ALLOW_TRADE decision is a recommendation,
    not an executed trade or fill, and a forward hypothetical-evaluation record
    is not realized P&L. Until a trustworthy execution/fill carrier exists, no
    brake may fire on that evidence, so this function reports fully neutral
    state (``prior_trade_count=0``, ``consecutive_losses=0``,
    ``last_trade_at_utc=None``) and the daily-limit, cooldown, and loss-lockout
    predicates stay dormant.

    This function is the wiring seam for a future trustworthy carrier: the
    parameters (``run_at_utc``, ``session_date``, ``audit_log_path``,
    ``evaluation_log_path``) are retained for that carrier even though the
    dormant implementation consults neither the audit recommendations nor the
    hypothetical-evaluation log. A future carrier reading real execution
    evidence here must fail loud on malformed/unresolvable evidence rather than
    substitute neutral state.
    """
    return ExecutionSessionState()


def apply_execution_policy_to_decisions(
    decisions: list[TradeDecision],
    *,
    market_regime: Optional[str],
    posture: Optional[str],
    confidence: float,
    timestamp: datetime,
    session_state: ExecutionSessionState,
    orb_states: Optional[dict[str, OrbPolicyState]] = None,
    overall_pressure: str = "UNKNOWN",
    operator_locked: bool = False,
) -> list[TradeDecision]:
    """Apply execution policy to each decision against the supplied session state.

    PRD-285 / CB-04: no same-run accumulation. An ALLOW_TRADE decision is a
    recommendation, not an executed trade, so it must not increment an in-memory
    trade count or start a cooldown for later same-run candidates. Every
    decision is evaluated against the same supplied ``session_state``; input
    ordering is preserved. With the loader dormant (neutral state) and no
    same-run mutation, the daily-limit and cooldown predicates cannot fire in
    production, while remaining intact for a future trustworthy carrier.
    """
    return [
        apply_execution_policy(
            decision,
            market_regime=market_regime,
            posture=posture,
            confidence=confidence,
            timestamp=timestamp,
            session_state=session_state,
            orb_state=(orb_states or {}).get(decision.ticker),
            overall_pressure=overall_pressure,
            operator_locked=operator_locked,
        )
        for decision in decisions
    ]


def apply_execution_policy(
    decision: TradeDecision,
    *,
    market_regime: Optional[str],
    posture: Optional[str],
    confidence: float,
    timestamp: datetime,
    session_state: ExecutionSessionState,
    orb_state: Optional[OrbPolicyState] = None,
    overall_pressure: str = "UNKNOWN",
    operator_locked: bool = False,
) -> TradeDecision:
    """Return a decision with PRD-051 policy fields materialized."""
    result = evaluate_execution_policy(
        decision,
        market_regime=market_regime,
        posture=posture,
        confidence=confidence,
        timestamp=timestamp,
        session_state=session_state,
        orb_state=orb_state,
        overall_pressure=overall_pressure,
        operator_locked=operator_locked,
    )
    if result.allowed:
        # PRD-284: materialize the finalized size multiplier into the position.
        if result.size_multiplier == 1.0:
            # Unity short-circuit — preserve contracts and dollar_risk exactly
            # (structural R3 guarantee; never rely on (d/c)*c == d in float).
            return replace(
                decision,
                policy_allowed=True,
                policy_reason=result.reason,
                size_multiplier=result.size_multiplier,
            )
        materialized_contracts = math.floor(decision.contracts * result.size_multiplier)
        if materialized_contracts >= 1:
            dollar_risk_per_contract = decision.dollar_risk / decision.contracts
            return replace(
                decision,
                contracts=materialized_contracts,
                dollar_risk=round(dollar_risk_per_contract * materialized_contracts, 2),
                policy_allowed=True,
                policy_reason=result.reason,
                size_multiplier=result.size_multiplier,
            )
        # materialized_contracts == 0: the policy-scaled position rounds to zero.
        # Block at EXECUTION_POLICY; keep contracts at its pre-materialization
        # value (the contracts >= 1 invariant forbids 0; the block makes it moot).
        return replace(
            decision,
            status=BLOCK_TRADE,
            block_reason=POLICY_SIZE_ROUNDS_TO_ZERO,
            decision_trace={
                "stage": POLICY_STAGE,
                "source": POLICY_SOURCE,
                "reason": POLICY_SIZE_ROUNDS_TO_ZERO,
            },
            policy_allowed=False,
            policy_reason=POLICY_SIZE_ROUNDS_TO_ZERO,
            size_multiplier=0.0,
        )

    return replace(
        decision,
        status=BLOCK_TRADE,
        block_reason=result.reason,
        decision_trace={
            "stage": POLICY_STAGE,
            "source": POLICY_SOURCE,
            "reason": result.reason,
        },
        policy_allowed=False,
        policy_reason=result.reason,
        size_multiplier=0.0,
    )


def evaluate_execution_policy(
    decision: TradeDecision,
    *,
    market_regime: Optional[str],
    posture: Optional[str],
    confidence: float,
    timestamp: datetime,
    session_state: ExecutionSessionState,
    orb_state: Optional[OrbPolicyState] = None,
    overall_pressure: str = "UNKNOWN",
    operator_locked: bool = False,
) -> PolicyDecision:
    if overall_pressure not in _VALID_PRESSURE_VALUES:
        raise ValueError(f"Invalid overall_pressure: {overall_pressure!r}")
    size = size_multiplier_for_confidence(confidence)
    if decision.status != ALLOW_TRADE:
        return PolicyDecision(False, decision.block_reason or POLICY_PRE_POLICY_BLOCK, 0.0)
    if confidence < 0.60:
        return PolicyDecision(False, POLICY_LOW_CONFIDENCE, 0.0)
    if market_regime == "CHAOTIC":
        return PolicyDecision(False, POLICY_CHAOTIC_REGIME, 0.0)
    if posture == "STAY_FLAT":
        return PolicyDecision(False, POLICY_STAY_FLAT, 0.0)
    if session_state.prior_trade_count >= config.EXECUTION_POLICY_MAX_TRADES_PER_DAY:
        return PolicyDecision(False, POLICY_SESSION_TRADE_LIMIT, 0.0)
    if session_state.consecutive_losses >= 2:
        return PolicyDecision(False, POLICY_LOSS_LOCKOUT, 0.0)
    if _cooldown_active(timestamp, session_state.last_trade_at_utc):
        return PolicyDecision(False, POLICY_COOLDOWN, 0.0)

    orb_reason = _evaluate_orb_constraint(decision, orb_state)
    if orb_reason is not None and orb_reason != POLICY_ORB_UNAVAILABLE:
        return PolicyDecision(False, orb_reason, 0.0)

    base_reason = POLICY_ALLOWED if orb_reason is None else POLICY_ORB_UNAVAILABLE
    result = _apply_macro_pressure(decision.direction, overall_pressure, size, base_reason)
    # PRD-304: the operator lock intercepts ONLY the allow outcome. A would-be
    # ALLOW decision becomes a zero-size operator block; every natural block
    # above (and any upstream block handled by the != ALLOW_TRADE guard) keeps
    # its own, more specific reason. System-halt precedence is unaffected: a
    # halted run does not reach an allow here, and halt permission wins in the
    # presentation layer.
    if operator_locked and result.allowed:
        return PolicyDecision(False, POLICY_OPERATOR_CANNOT_MONITOR, 0.0)
    return result


def _apply_macro_pressure(direction: str, pressure: str, size: float, reason: str) -> PolicyDecision:
    # PRD-286 / CB-05: a macro-pressure COMPUTATION FAILURE fails CLOSED. This
    # branch MUST precede every allow/directional branch below — a failed read is
    # never unconstrained, so it blocks regardless of direction. Distinct from a
    # genuinely computed "UNKNOWN" (handled with "NEUTRAL" as full-size allow).
    if pressure == MACRO_PRESSURE_UNAVAILABLE:
        return PolicyDecision(False, POLICY_MACRO_PRESSURE_UNAVAILABLE, 0.0)
    if pressure in ("UNKNOWN", "NEUTRAL"):
        return PolicyDecision(True, reason, size)
    if pressure == "MIXED":
        return PolicyDecision(True, reason, size * 0.75)
    if pressure == "RISK_OFF":
        if direction == "LONG":
            return PolicyDecision(False, POLICY_MACRO_PRESSURE_CONFLICT, 0.0)
        return PolicyDecision(True, reason, size * 0.5)
    # RISK_ON
    if direction == "SHORT":
        return PolicyDecision(False, POLICY_MACRO_PRESSURE_CONFLICT, 0.0)
    return PolicyDecision(True, reason, size * 0.5)


def _evaluate_orb_constraint(
    decision: TradeDecision,
    orb_state: Optional[OrbPolicyState],
) -> Optional[str]:
    if orb_state is not None and orb_state.continuation_breakout:
        return None
    # PRD-271 / CB-07: an INVALID (untrustworthy-provenance) ORB fails closed —
    # distinct from UNAVAILABLE's benign allow-but-flag. Evaluated after the
    # continuation bypass (which legitimately does not gate on ORB) and before
    # the missing-value path so a mismatched session can never allow a trade.
    if orb_state is not None and orb_state.invalid:
        return POLICY_ORB_INVALID
    if (
        orb_state is None
        or orb_state.price is None
        or orb_state.orb_high is None
        or orb_state.orb_low is None
    ):
        return POLICY_ORB_UNAVAILABLE

    price = float(orb_state.price)
    if decision.direction == "LONG" and price > float(orb_state.orb_high):
        return None
    if decision.direction == "SHORT" and price < float(orb_state.orb_low):
        return None
    return POLICY_ORB_INSIDE_RANGE


def _cooldown_active(timestamp: datetime, last_trade_at_utc: Optional[datetime]) -> bool:
    if last_trade_at_utc is None:
        return False
    elapsed = timestamp - last_trade_at_utc
    return timedelta(0) <= elapsed < timedelta(minutes=config.EXECUTION_POLICY_COOLDOWN_MINUTES)
