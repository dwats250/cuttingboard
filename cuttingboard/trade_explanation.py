"""Trade explanation layer (PRD-066).

Builds a deterministic explanation dict per candidate using fixed template strings.
Read-only — never mutates inputs.
"""

from __future__ import annotations

from cuttingboard.execution_policy import (
    POLICY_COOLDOWN,
    POLICY_LOW_CONFIDENCE,
    POLICY_MACRO_PRESSURE_CONFLICT,
    POLICY_ORB_INSIDE_RANGE,
)
from cuttingboard.trade_decision import TradeDecision
from cuttingboard.trade_visibility import VISIBILITY_NEAR_MISS

_REQUIRED_CHANGE_MAP: dict[str, str] = {
    POLICY_MACRO_PRESSURE_CONFLICT: "macro_pressure must align with trade direction",
    POLICY_ORB_INSIDE_RANGE: "price must break ORB range",
    POLICY_COOLDOWN: "cooldown period must expire",
    POLICY_LOW_CONFIDENCE: "regime confidence must reach 0.60",
}

_MACRO_ALIGNMENT_TABLE: dict[tuple[str, str], str] = {
    ("RISK_ON", "LONG"): "ALIGNED",
    ("RISK_ON", "SHORT"): "MISALIGNED",
    ("RISK_OFF", "SHORT"): "ALIGNED",
    ("RISK_OFF", "LONG"): "MISALIGNED",
}


def build_explanation_map(
    decisions: list[TradeDecision],
    visibility_map: dict[str, dict],
    overall_pressure: str,
) -> dict[str, dict]:
    """Return {symbol: {block_reasons, macro_alignment, required_changes}}.

    Read-only — never mutates decisions or visibility_map.
    """
    result: dict[str, dict] = {}

    for decision in decisions:
        symbol = decision.ticker

        block_reasons: list[str] = [] if decision.policy_allowed else [decision.policy_reason]

        macro_alignment = _MACRO_ALIGNMENT_TABLE.get((overall_pressure, decision.direction))

        vis_status = visibility_map.get(symbol, {}).get("visibility_status")
        if vis_status == VISIBILITY_NEAR_MISS:
            reason = decision.policy_reason
            required_changes: list[str] = [
                _REQUIRED_CHANGE_MAP.get(reason, f"blocking condition must resolve: {reason}")
            ]
        else:
            required_changes = []

        result[symbol] = {
            "block_reasons": block_reasons,
            "macro_alignment": macro_alignment,
            "required_changes": required_changes,
        }

    return result
