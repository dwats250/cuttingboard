"""Watchlist Snapshot Sidecar (PRD-114).

Observe-only producer of tickers tracked outside the primary trading
universe. Provides visibility into names being researched or monitored —
for example, names where fundamental or technical analysis is being
developed outside the Cuttingboard pipeline. Consumer is the dashboard
renderer and the human reader, not a decision module. Outputs do not
feed qualification, regime, or any decision surface.

Pure builder over the NS-4A seed registry (PRD-308) plus existing
`NormalizedQuote.price` pass-through. No I/O, no wall-clock reads, no
derived semantics.

WATCHLIST_SYMBOLS is now DERIVED from `universe_registry.UNIVERSE_REGISTRY`
rather than hand-maintained here (PRD-308); its insertion order is
serialization-only and MUST NOT imply rank, priority, conviction, trade
preference, alert order, or execution preference (R14).
"""

from __future__ import annotations

from datetime import datetime
from typing import Mapping, Optional

from cuttingboard.normalization import NormalizedQuote
from cuttingboard.universe_registry import UNIVERSE_REGISTRY, UniverseInstrument


# Representation-only normalization (PRD-308): the registry's primary_group
# vocabulary (INDEX/METALS/ENERGY/TECH/HIGH_BETA) is finer than this sidecar's
# legacy coarse theme vocabulary. This map projects each group to the existing
# theme so every unaffected row stays value-for-value identical; it changes no
# row's value. A group missing here raises KeyError (fail-loud).
_PRIMARY_GROUP_TO_THEME: dict[str, str] = {
    "INDEX": "Index",
    "METALS": "Commodities",
    "ENERGY": "Commodities",
    "TECH": "High beta",
    "HIGH_BETA": "High beta",
}


def build_watchlist_symbols(
    registry: tuple[UniverseInstrument, ...],
) -> tuple[tuple[str, str, str], ...]:
    """Project the enabled registry instruments into the watchlist's
    (symbol, theme, reason) row shape. Pure function of ``registry``; the
    watchlist is sourced here, not hand-maintained (PRD-308)."""
    return tuple(
        (inst.symbol, _PRIMARY_GROUP_TO_THEME[inst.primary_group], inst.rationale)
        for inst in registry
        if inst.enabled
    )


WATCHLIST_SYMBOLS: tuple[tuple[str, str, str], ...] = build_watchlist_symbols(
    UNIVERSE_REGISTRY
)


def build_watchlist_snapshot(
    normalized_quotes: Mapping[str, NormalizedQuote],
    generated_at: Optional[datetime],
) -> dict:
    if generated_at is not None and generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware or None")

    symbols: dict[str, dict] = {}
    for symbol, sector_theme, watch_reason in WATCHLIST_SYMBOLS:
        quote = normalized_quotes.get(symbol)
        current_price = quote.price if quote is not None else None
        symbols[symbol] = {
            "symbol": symbol,
            "sector_theme": sector_theme,
            "watch_reason": watch_reason,
            "current_price": current_price,
        }

    return {
        "schema_version": 1,
        "source": "watchlist",
        "generated_at": generated_at.isoformat() if generated_at is not None else None,
        "symbols": symbols,
    }
