"""
Execution policy materialization (PRD-051).

This layer does not execute orders. It is the final deterministic pass that
decides whether an already-created TradeDecision remains ALLOW_TRADE or is
downgraded to BLOCK_TRADE before contract and audit materialization.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

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
POLICY_MACRO_PRESSURE_CONFLICT = "macro_pressure_conflict"

_VALID_PRESSURE_VALUES = frozenset({"RISK_ON", "RISK_OFF", "MIXED", "NEUTRAL", "UNKNOWN"})


@dataclass(frozen=True)
class OrbPolicyState:
    price: Optional[float] = None
    orb_high: Optional[float] = None
    orb_low: Optional[float] = None
    continuation_breakout: bool = False


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
    """Derive same-session policy state from existing audit/evaluation logs."""
    prior_trade_count = 0
    last_trade_at_utc: Optional[datetime] = None
    audit_path = Path(audit_log_path)
    if audit_path.exists():
        for record in _iter_jsonl(audit_path):
            if record.get("event") is not None:
                continue
            if record.get("date") != session_date:
                continue
            record_run_at = _parse_utc(record.get("run_at_utc"), "run_at_utc")
            if record_run_at >= run_at_utc:
                continue
            trade_decisions = record.get("trade_decisions") or []
            if not isinstance(trade_decisions, list):
                raise TypeError("audit trade_decisions must be a list")
            allow_count = sum(
                1
                for decision in trade_decisions
                if isinstance(decision, dict)
                and decision.get("decision_status") == ALLOW_TRADE
            )
            if allow_count:
                prior_trade_count += allow_count
                if last_trade_at_utc is None or record_run_at > last_trade_at_utc:
                    last_trade_at_utc = record_run_at

    consecutive_losses = _load_consecutive_losses(
        run_at_utc=run_at_utc,
        session_date=session_date,
        evaluation_log_path=Path(evaluation_log_path),
    )
    return ExecutionSessionState(
        prior_trade_count=prior_trade_count,
        consecutive_losses=consecutive_losses,
        last_trade_at_utc=last_trade_at_utc,
    )


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
) -> list[TradeDecision]:
    """Apply policy sequentially so in-run trade count and cooldown are deterministic."""
    materialized: list[TradeDecision] = []
    trade_count = session_state.prior_trade_count
    last_trade_at = session_state.last_trade_at_utc

    for decision in decisions:
        effective_state = ExecutionSessionState(
            prior_trade_count=trade_count,
            consecutive_losses=session_state.consecutive_losses,
            last_trade_at_utc=last_trade_at,
        )
        materialized_decision = apply_execution_policy(
            decision,
            market_regime=market_regime,
            posture=posture,
            confidence=confidence,
            timestamp=timestamp,
            session_state=effective_state,
            orb_state=(orb_states or {}).get(decision.ticker),
            overall_pressure=overall_pressure,
        )
        materialized.append(materialized_decision)
        if materialized_decision.status == ALLOW_TRADE:
            trade_count += 1
            last_trade_at = timestamp

    return materialized


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
    )
    if result.allowed:
        return replace(
            decision,
            policy_allowed=True,
            policy_reason=result.reason,
            size_multiplier=result.size_multiplier,
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
    return _apply_macro_pressure(decision.direction, overall_pressure, size, base_reason)


def _apply_macro_pressure(direction: str, pressure: str, size: float, reason: str) -> PolicyDecision:
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


def _load_consecutive_losses(
    *,
    run_at_utc: datetime,
    session_date: str,
    evaluation_log_path: Path,
) -> int:
    if not evaluation_log_path.exists():
        return 0

    records: list[tuple[datetime, datetime, str, bool]] = []
    for record in _iter_jsonl(evaluation_log_path):
        decision_run_at = _parse_utc(record.get("decision_run_at_utc"), "decision_run_at_utc")
        if decision_run_at >= run_at_utc or decision_run_at.date().isoformat() != session_date:
            continue
        evaluated_at = _parse_utc(record.get("evaluated_at_utc"), "evaluated_at_utc")
        symbol = str(record.get("symbol") or "")
        evaluation = record.get("evaluation")
        if not isinstance(evaluation, dict):
            continue
        r_multiple = evaluation.get("R_multiple")
        result = evaluation.get("result")
        losing = result == "STOP_HIT" or (
            isinstance(r_multiple, (int, float)) and float(r_multiple) < 0.0
        )
        records.append((decision_run_at, evaluated_at, symbol, losing))

    consecutive = 0
    for _, _, _, losing in sorted(records):
        consecutive = consecutive + 1 if losing else 0
    return consecutive


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise TypeError(f"{path} contains non-object JSONL record")
            records.append(record)
    return records


def _parse_utc(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise KeyError(f"record missing required field: {field_name}")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone")
    return parsed
