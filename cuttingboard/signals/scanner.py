"""Deterministic scan entry point for TradeCandidate generation."""

from __future__ import annotations

from collections import defaultdict

from cuttingboard.policy.models import TradeCandidate
from cuttingboard.signals.builder import build_candidate, passes_sanity_checks
from cuttingboard.signals.detectors import detect_signals
from cuttingboard.signals.filters import passes_pre_filter, validate_context, validate_market_data
from cuttingboard.signals.models import MarketData, ScanContext

STRUCTURE_PRIORITY = {
    "breakout": 0,
    "pullback": 1,
    "reversal": 2,
}
DIRECTION_PRIORITY = {
    "long": 0,
    "short": 1,
}


def generate_candidates(
    market_data: list[MarketData],
    context: ScanContext,
) -> list[TradeCandidate]:
    validate_context(context)

    candidates_by_ticker: dict[str, list[TradeCandidate]] = defaultdict(list)
    ticker_order: list[str] = []

    for item in market_data:
        data = validate_market_data(item)
        if data.ticker not in candidates_by_ticker:
            ticker_order.append(data.ticker)
        if not passes_pre_filter(data):
            continue

        for direction, structure in detect_signals(data):
            candidate = build_candidate(data, direction=direction, structure=structure)
            if passes_sanity_checks(candidate):
                candidates_by_ticker[data.ticker].append(candidate)

    return [
        _select_candidate(candidates_by_ticker[ticker])
        for ticker in ticker_order
        if candidates_by_ticker[ticker]
    ]


def _select_candidate(candidates: list[TradeCandidate]) -> TradeCandidate:
    return min(
        candidates,
        key=lambda candidate: (
            STRUCTURE_PRIORITY[candidate.structure],
            DIRECTION_PRIORITY[candidate.direction],
        ),
    )
