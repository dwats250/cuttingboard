"""Invalidation and exit guidance layer (PRD-068).

Evaluates trade thesis data to produce deterministic invalidation_guidance
for each candidate. Converts ALLOW_TRADE decisions with TRIGGERED invalidation
to BLOCK_TRADE. BLOCK_TRADE decisions are never modified.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Optional

from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE, TradeDecision

# Invalidation status values
STATUS_NOT_TRIGGERED = "NOT_TRIGGERED"
STATUS_WARNING = "WARNING"
STATUS_TRIGGERED = "TRIGGERED"
STATUS_UNKNOWN = "UNKNOWN"

VALID_STATUSES = frozenset({STATUS_NOT_TRIGGERED, STATUS_WARNING, STATUS_TRIGGERED, STATUS_UNKNOWN})

# Action values
ACTION_HOLD_OK = "HOLD_OK"
ACTION_AVOID_ENTRY = "AVOID_ENTRY"
ACTION_REDUCE_OR_EXIT = "REDUCE_OR_EXIT"
ACTION_NO_ACTION = "NO_ACTION"
ACTION_UNKNOWN = "UNKNOWN"

VALID_ACTIONS = frozenset({ACTION_HOLD_OK, ACTION_AVOID_ENTRY, ACTION_REDUCE_OR_EXIT, ACTION_NO_ACTION, ACTION_UNKNOWN})

# Thesis statuses that trigger invalidation (from PRD-067)
_THESIS_TRIGGERED_STATUSES = frozenset({"INCOMPLETE", "CONFLICTED"})


def _build_guidance(
    status: str,
    action: str,
    reason: Optional[str],
    triggered_by: Optional[str],
    thesis_status: str,
) -> dict:
    assert status in VALID_STATUSES
    assert action in VALID_ACTIONS
    return {
        "status": status,
        "action": action,
        "reason": reason,
        "triggered_by": triggered_by,
        "thesis_status": thesis_status,
    }


def _evaluate_guidance(
    decision: TradeDecision,
    thesis: Optional[dict],
    overall_pressure: str,
) -> dict:
    """Derive invalidation_guidance from existing pipeline data."""
    if thesis is None:
        return _build_guidance(
            STATUS_UNKNOWN,
            ACTION_UNKNOWN,
            "INSUFFICIENT_DETERMINISTIC_INPUTS",
            None,
            "UNKNOWN",
        )

    thesis_status = thesis.get("status", "UNKNOWN")
    thesis_block_reason = thesis.get("block_reason")
    direction = decision.direction

    # TRIGGERED: thesis status is INCOMPLETE or CONFLICTED
    if thesis_status in _THESIS_TRIGGERED_STATUSES:
        return _build_guidance(
            STATUS_TRIGGERED,
            ACTION_AVOID_ENTRY,
            f"thesis_{thesis_status.lower()}",
            f"thesis.status={thesis_status}",
            thesis_status,
        )

    # WARNING: thesis has a block_reason set (non-TRIGGERED thesis with advisory block)
    if thesis_block_reason is not None:
        return _build_guidance(
            STATUS_WARNING,
            ACTION_REDUCE_OR_EXIT,
            f"thesis_block_reason={thesis_block_reason}",
            "thesis.block_reason",
            thesis_status,
        )

    # WARNING: overall_pressure conflicts with direction
    if direction and overall_pressure and overall_pressure not in ("UNKNOWN", ""):
        direction_upper = direction.upper()
        pressure_upper = overall_pressure.upper()
        conflict = (
            (direction_upper == "LONG" and pressure_upper == "RISK_OFF")
            or (direction_upper == "SHORT" and pressure_upper == "RISK_ON")
        )
        if conflict:
            return _build_guidance(
                STATUS_WARNING,
                ACTION_NO_ACTION,
                f"direction={direction} conflicts with overall_pressure={overall_pressure}",
                "overall_pressure",
                thesis_status,
            )

    # NOT_TRIGGERED: thesis is VALID or UNKNOWN with no adverse signals
    if thesis_status in ("VALID", "UNKNOWN"):
        return _build_guidance(
            STATUS_NOT_TRIGGERED,
            ACTION_HOLD_OK,
            None,
            None,
            thesis_status,
        )

    # Fallback: insufficient deterministic inputs
    return _build_guidance(
        STATUS_UNKNOWN,
        ACTION_UNKNOWN,
        "INSUFFICIENT_DETERMINISTIC_INPUTS",
        None,
        thesis_status,
    )


def apply_invalidation_gate(
    trade_decisions: list[TradeDecision],
    thesis_map: dict[str, dict],
    overall_pressure: str,
) -> tuple[list[TradeDecision], dict[str, dict]]:
    """Apply invalidation gate after apply_thesis_gate, before contract assembly.

    Only converts ALLOW_TRADE decisions with TRIGGERED invalidation to BLOCK_TRADE.
    BLOCK_TRADE decisions pass through unchanged.

    Returns (decisions, invalidation_guidance_map).
    """
    invalidation_guidance_map: dict[str, dict] = {}
    result_decisions: list[TradeDecision] = []

    for decision in trade_decisions:
        symbol = decision.ticker

        if decision.status != ALLOW_TRADE:
            # Never modify already-blocked decisions
            result_decisions.append(decision)
            continue

        thesis = thesis_map.get(symbol)
        guidance = _evaluate_guidance(decision, thesis, overall_pressure)
        invalidation_guidance_map[symbol] = guidance

        if guidance["status"] == STATUS_TRIGGERED:
            blocked = replace(
                decision,
                status=BLOCK_TRADE,
                block_reason="INVALIDATION_TRIGGERED",
                decision_trace={
                    "stage": "INVALIDATION_GATE",
                    "source": "invalidation",
                    "reason": "INVALIDATION_TRIGGERED",
                },
                policy_allowed=False,
                policy_reason="invalidation_gate_blocked",
            )
            result_decisions.append(blocked)
        else:
            result_decisions.append(decision)

    return result_decisions, invalidation_guidance_map
