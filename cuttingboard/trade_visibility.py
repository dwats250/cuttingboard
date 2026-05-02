"""Trade visibility classification (PRD-064).

Classifies each trade decision as ACTIVE, NEAR_MISS, or BLOCKED based on
execution policy outcome and market_map grade. Read-only — never mutates inputs.
"""

from __future__ import annotations

from cuttingboard.execution_policy import (
    POLICY_COOLDOWN,
    POLICY_LOW_CONFIDENCE,
    POLICY_MACRO_PRESSURE_CONFLICT,
    POLICY_ORB_INSIDE_RANGE,
)
from cuttingboard.trade_decision import TradeDecision

VISIBILITY_ACTIVE = "ACTIVE"
VISIBILITY_NEAR_MISS = "NEAR_MISS"
VISIBILITY_BLOCKED = "BLOCKED"

_HIGH_GRADES = frozenset({"A+", "A", "B"})

_ENABLE_CONDITION_MAP: dict[str, str] = {
    POLICY_MACRO_PRESSURE_CONFLICT: "macro_pressure must align with trade direction",
    POLICY_ORB_INSIDE_RANGE: "price must break ORB range",
    POLICY_COOLDOWN: "cooldown period must expire",
    POLICY_LOW_CONFIDENCE: "regime confidence must reach 0.60",
}


def build_visibility_map(
    decisions: list[TradeDecision],
    market_map: dict,
) -> dict[str, dict]:
    """Return {symbol: {visibility_status, visibility_reason, enable_conditions}}.

    Grade is sourced exclusively from market_map["symbols"][symbol]["grade"].
    Missing symbol or grade defaults to None (no exception raised).
    """
    symbols_data = market_map.get("symbols", {})
    result: dict[str, dict] = {}

    for decision in decisions:
        symbol = decision.ticker
        grade = symbols_data.get(symbol, {}).get("grade")

        if decision.policy_allowed:
            result[symbol] = {
                "visibility_status": VISIBILITY_ACTIVE,
                "visibility_reason": None,
                "enable_conditions": [],
            }
        elif grade in _HIGH_GRADES:
            reason = decision.policy_reason
            enable_str = _ENABLE_CONDITION_MAP.get(
                reason, f"blocking condition must resolve: {reason}"
            )
            result[symbol] = {
                "visibility_status": VISIBILITY_NEAR_MISS,
                "visibility_reason": reason,
                "enable_conditions": [enable_str],
            }
        else:
            result[symbol] = {
                "visibility_status": VISIBILITY_BLOCKED,
                "visibility_reason": decision.policy_reason,
                "enable_conditions": [],
            }

    return result
