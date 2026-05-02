"""Trade thesis gate (PRD-067).

Builds a deterministic thesis from existing pipeline inputs and converts
ALLOW_TRADE decisions with INCOMPLETE or CONFLICTED thesis to BLOCK_TRADE.
Only operates on decisions that are already ALLOW_TRADE; BLOCK_TRADE decisions
pass through unchanged.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Optional

from cuttingboard.qualification import (
    ENTRY_MODE_DIRECT,
    QualificationResult,
    TradeCandidate,
)
from cuttingboard.structure import StructureResult
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE, TradeDecision

THESIS_VALID = "VALID"
THESIS_INCOMPLETE = "INCOMPLETE"
THESIS_CONFLICTED = "CONFLICTED"
THESIS_UNKNOWN = "UNKNOWN"

_VALID_STATUSES = frozenset({THESIS_VALID, THESIS_INCOMPLETE, THESIS_CONFLICTED, THESIS_UNKNOWN})

_MACRO_ALIGNED = frozenset({("LONG", "RISK_ON"), ("SHORT", "RISK_OFF")})
_MACRO_CONFLICTED = frozenset({("LONG", "RISK_OFF"), ("SHORT", "RISK_ON")})

_POLICY_ALLOWED_REASON = "policy_allowed"
_POLICY_DEFAULT_REASON = "policy_not_evaluated"


def _derive_catalyst(
    decision: TradeDecision,
    qual: QualificationResult,
    structure: Optional[StructureResult],
    overall_pressure: str,
) -> Optional[str]:
    if overall_pressure and overall_pressure != "UNKNOWN":
        return f"macro:{overall_pressure}"
    if qual.entry_mode and qual.entry_mode != ENTRY_MODE_DIRECT:
        return f"entry:{qual.entry_mode}"
    if structure and structure.structure and structure.structure != "CHOP":
        return f"structure:{structure.structure}"
    policy_reason = decision.policy_reason
    if policy_reason and policy_reason not in (_POLICY_DEFAULT_REASON, ""):
        return f"policy:{policy_reason}"
    return None


def _derive_confirmation(
    direction: str,
    overall_pressure: str,
    structure: Optional[StructureResult],
    decision: TradeDecision,
) -> str:
    if (direction, overall_pressure) in _MACRO_ALIGNED:
        return "MACRO_CONFIRMED"
    if structure and structure.structure and structure.structure != "CHOP":
        return "STRUCTURE_CONFIRMED"
    if decision.policy_reason == _POLICY_ALLOWED_REASON:
        return "POLICY_CONFIRMED"
    return "UNKNOWN"


def _derive_invalidation(
    decision: TradeDecision,
    candidate: Optional[TradeCandidate],
) -> Optional[str]:
    if decision.stop and decision.stop != 0.0:
        return f"stop at {decision.stop:.2f}"
    if candidate is not None and candidate.stop_price:
        return f"stop at {candidate.stop_price:.2f}"
    return None


def build_thesis(
    decision: TradeDecision,
    qual: QualificationResult,
    structure: Optional[StructureResult],
    overall_pressure: str,
    candidate: Optional[TradeCandidate] = None,
) -> dict:
    """Build a thesis dict for a single ALLOW_TRADE candidate.

    Derives catalyst, confirmation, and invalidation from existing pipeline
    inputs. Returns a dict with keys: symbol, direction, catalyst,
    confirmation, invalidation, status, block_reason.
    """
    symbol = decision.ticker
    direction = decision.direction

    if not direction:
        return {
            "symbol": symbol,
            "direction": direction,
            "catalyst": None,
            "confirmation": "UNKNOWN",
            "invalidation": None,
            "status": THESIS_INCOMPLETE,
            "block_reason": "THESIS_INCOMPLETE",
        }

    catalyst = _derive_catalyst(decision, qual, structure, overall_pressure)
    confirmation = _derive_confirmation(direction, overall_pressure, structure, decision)
    invalidation = _derive_invalidation(decision, candidate)

    if catalyst is None or invalidation is None:
        status = THESIS_INCOMPLETE
        block_reason: Optional[str] = "THESIS_INCOMPLETE"
    elif (direction, overall_pressure) in _MACRO_CONFLICTED:
        status = THESIS_CONFLICTED
        block_reason = "THESIS_CONFLICTED"
    elif confirmation == "UNKNOWN":
        status = THESIS_UNKNOWN
        block_reason = None
    else:
        status = THESIS_VALID
        block_reason = None

    return {
        "symbol": symbol,
        "direction": direction,
        "catalyst": catalyst,
        "confirmation": confirmation,
        "invalidation": invalidation,
        "status": status,
        "block_reason": block_reason,
    }


def apply_thesis_gate(
    trade_decisions: list[TradeDecision],
    candidates: dict[str, TradeCandidate],
    qualified_by_symbol: dict[str, QualificationResult],
    execution_structure: dict[str, StructureResult],
    overall_pressure: str,
) -> tuple[list[TradeDecision], dict[str, dict]]:
    """Apply trade thesis gate after execution policy, before contract assembly.

    Only converts ALLOW_TRADE decisions with INCOMPLETE or CONFLICTED thesis
    to BLOCK_TRADE. BLOCK_TRADE decisions pass through unchanged.

    Returns (decisions, thesis_map) where thesis_map is {symbol: thesis_dict}.
    """
    thesis_map: dict[str, dict] = {}
    result_decisions: list[TradeDecision] = []

    for decision in trade_decisions:
        if decision.status != ALLOW_TRADE:
            result_decisions.append(decision)
            continue

        symbol = decision.ticker
        qual = qualified_by_symbol.get(symbol)
        structure = execution_structure.get(symbol)
        candidate = candidates.get(symbol)

        if qual is None:
            thesis: dict = {
                "symbol": symbol,
                "direction": decision.direction,
                "catalyst": None,
                "confirmation": "UNKNOWN",
                "invalidation": None,
                "status": THESIS_INCOMPLETE,
                "block_reason": "THESIS_INCOMPLETE",
            }
        else:
            thesis = build_thesis(decision, qual, structure, overall_pressure, candidate)

        thesis_map[symbol] = thesis

        if thesis["status"] in (THESIS_INCOMPLETE, THESIS_CONFLICTED):
            block_reason = thesis["block_reason"]
            blocked = replace(
                decision,
                status=BLOCK_TRADE,
                block_reason=block_reason,
                decision_trace={
                    "stage": "THESIS_GATE",
                    "source": "trade_thesis",
                    "reason": block_reason,
                },
                policy_allowed=False,
                policy_reason="thesis_gate_blocked",
            )
            result_decisions.append(blocked)
        else:
            result_decisions.append(decision)

    return result_decisions, thesis_map
