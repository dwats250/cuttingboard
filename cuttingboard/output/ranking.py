"""Deterministic ranking helpers for approved trades."""

from cuttingboard.output.models import TradeOutput

_STRUCTURE_WEIGHT = {
    "breakout": 3,
    "pullback": 2,
    "reversal": 1,
}

_ALIGNMENT_BONUS = {
    "CLEAN": 1,
    "MIXED": 0,
}


def score_trade(trade: TradeOutput, market_quality: str) -> float:
    structure_weight = _STRUCTURE_WEIGHT[trade.structure]
    alignment_bonus = _ALIGNMENT_BONUS[market_quality]
    return (trade.rr * 10.0) + structure_weight + alignment_bonus


def rank_approved_trades(trades: list[TradeOutput], market_quality: str) -> list[TradeOutput]:
    return sorted(
        trades,
        key=lambda trade: (
            -score_trade(trade, market_quality),
            -trade.rr,
            trade.ticker,
        ),
    )


def sort_watchlist(trades: list[TradeOutput]) -> list[TradeOutput]:
    return sorted(
        trades,
        key=lambda trade: (-trade.rr, trade.ticker),
    )
