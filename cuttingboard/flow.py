"""
PRD-013 — Flow Alignment Soft Gate.

Downgrades an already-qualified PASS candidate to WATCHLIST when dominant
speculative options flow opposes the candidate direction.

Entry point: apply_flow_gate(result, flow_snapshot)
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from cuttingboard import config
from cuttingboard.universe import is_tradable_symbol

if TYPE_CHECKING:
    from cuttingboard.qualification import QualificationResult

FlowAlignment = str  # "SUPPORTS" | "OPPOSES" | "NEUTRAL" | "NO_DATA"


@dataclass(frozen=True)
class FlowPrint:
    symbol: str
    strike: float
    option_type: str        # "CALL" | "PUT"
    premium: float
    side: str               # "ASK" | "BID" | "MID"
    is_sweep: bool
    underlying_price: float


def apply_flow_gate(
    result: QualificationResult,
    flow_snapshot: dict[str, list[FlowPrint]],
) -> tuple[QualificationResult, FlowAlignment]:
    """Apply the flow alignment soft gate to a single QualificationResult.

    Only acts on qualified (PASS) results. Returns the (possibly downgraded)
    result and the computed FlowAlignment label.
    """
    if not result.qualified:
        return result, "NO_DATA"

    symbol = result.symbol

    # Step 1 — symbol print set
    if not is_tradable_symbol(symbol):
        return result, "NO_DATA"

    prints = [
        p for p in flow_snapshot.get(symbol, [])
        if p.premium >= config.FLOW_MIN_PREMIUM
    ]
    if not prints:
        return result, "NO_DATA"

    # Step 2 — classify each print's strike location
    # Step 3 — aggregate flow type
    total_premium = sum(p.premium for p in prints)
    itm_premium = 0.0
    otm_ask_premium = 0.0

    for p in prints:
        loc = _classify_strike(p.strike, p.underlying_price, p.option_type)
        if loc == "ITM":
            itm_premium += p.premium
        elif loc == "OTM" and p.side == "ASK":
            otm_ask_premium += p.premium

    if itm_premium / total_premium > 0.50:
        aggregate_flow_type = "HEDGE"
    elif otm_ask_premium / total_premium >= config.FLOW_MIN_SPEC_SHARE:
        aggregate_flow_type = "SPECULATIVE"
    else:
        aggregate_flow_type = "MIXED"

    # Step 4 — non-speculative exit
    if aggregate_flow_type != "SPECULATIVE":
        return result, "NEUTRAL"

    # Step 5 — speculative direction
    bullish_spec = sum(
        p.premium for p in prints
        if p.option_type == "CALL"
        and p.side == "ASK"
        and _classify_strike(p.strike, p.underlying_price, p.option_type) == "OTM"
    )
    bearish_spec = sum(
        p.premium for p in prints
        if p.option_type == "PUT"
        and p.side == "ASK"
        and _classify_strike(p.strike, p.underlying_price, p.option_type) == "OTM"
    )

    threshold = config.FLOW_RATIO_THRESHOLD
    if bullish_spec >= bearish_spec * threshold:
        dominant = "BULLISH"
    elif bearish_spec >= bullish_spec * threshold:
        dominant = "BEARISH"
    else:
        dominant = "NEUTRAL"

    # Step 6 — alignment
    if dominant == "NEUTRAL":
        return result, "NEUTRAL"

    opposes = (
        (result.direction == "LONG" and dominant == "BEARISH")
        or (result.direction == "SHORT" and dominant == "BULLISH")
    )

    if opposes:
        downgraded = replace(
            result,
            qualified=False,
            watchlist=True,
            watchlist_reason="FLOW_ALIGNMENT: opposing speculative flow",
            flow_alignment="OPPOSES",
        )
        return downgraded, "OPPOSES"

    return replace(result, flow_alignment="SUPPORTS"), "SUPPORTS"


def _classify_strike(strike: float, underlying_price: float, option_type: str) -> str:
    distance = (strike - underlying_price) / underlying_price
    if option_type == "CALL":
        if distance > 0.005:
            return "OTM"
        if distance < -0.005:
            return "ITM"
        return "ATM"
    # PUT
    if distance < -0.005:
        return "OTM"
    if distance > 0.005:
        return "ITM"
    return "ATM"
