"""Watchlist Snapshot Sidecar (PRD-114).

Observe-only producer for `logs/watchlist_snapshot.json`. Pure builder
over a frozen curated tuple plus existing `NormalizedQuote.price`
pass-through. No I/O, no wall-clock reads, no derived semantics.

WATCHLIST_SYMBOLS insertion order is serialization-only. It MUST NOT
imply rank, priority, conviction, trade preference, alert order, or
execution preference (R14).
"""

from __future__ import annotations

from datetime import datetime
from typing import Mapping, Optional

from cuttingboard.normalization import NormalizedQuote


WATCHLIST_SYMBOLS: tuple[tuple[str, str, str], ...] = (
    ("SPY", "Index", "broad market reference"),
    ("QQQ", "Index", "tech-heavy reference"),
    ("GDX", "Commodities", "gold miners exposure"),
    ("GLD", "Commodities", "spot gold ETF"),
    ("SLV", "Commodities", "spot silver ETF"),
    ("XLE", "Commodities", "energy sector"),
    ("NVDA", "High beta", "AI/semis bellwether"),
    ("TSLA", "High beta", "retail-flow signal"),
    ("META", "High beta", "large-cap tech"),
    ("AMZN", "High beta", "large-cap tech"),
    ("AAPL", "High beta", "large-cap tech"),
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
