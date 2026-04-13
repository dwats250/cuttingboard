"""Candidate construction and sanity checks for signal generation."""

from cuttingboard.policy.models import TradeCandidate
from cuttingboard.signals.models import MarketData


def build_candidate(data: MarketData, *, direction: str, structure: str) -> TradeCandidate:
    entry_price = data.price
    if direction == "long":
        stop_price = min(data.ema21, data.price - data.atr14)
        target_price = entry_price + 2 * (entry_price - stop_price)
    else:
        stop_price = max(data.ema21, data.price + data.atr14)
        target_price = entry_price - 2 * (stop_price - entry_price)

    return TradeCandidate(
        ticker=data.ticker,
        direction=direction,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        ema9=data.ema9,
        ema21=data.ema21,
        ema50=data.ema50,
        atr14=data.atr14,
        structure=structure,
    )


def passes_sanity_checks(candidate: TradeCandidate) -> bool:
    stop_distance = abs(candidate.entry_price - candidate.stop_price)
    if stop_distance < 0.5 * candidate.atr14:
        return False
    if candidate.target_price == candidate.entry_price:
        return False

    if candidate.direction == "long":
        return (
            candidate.stop_price < candidate.entry_price
            and candidate.target_price > candidate.entry_price
        )

    return (
        candidate.stop_price > candidate.entry_price
        and candidate.target_price < candidate.entry_price
    )
