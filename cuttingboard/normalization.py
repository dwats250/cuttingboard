"""
Layer 2 — Normalization.

Converts RawQuotes into NormalizedQuotes with:
  - pct_change always in decimal form (5.2% → 0.052)
  - timestamps always UTC-aware
  - units assigned per-symbol
  - age_seconds computed at normalization time

No business logic lives here. This layer only enforces unit contracts.
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from cuttingboard import config
from cuttingboard.ingestion import RawQuote

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NormalizedQuote:
    symbol: str
    price: float
    pct_change_decimal: float   # ALWAYS decimal: 5.2% is 0.052
    volume: Optional[float]
    fetched_at_utc: datetime    # UTC with tzinfo — never naive
    source: str
    units: str                  # "usd_price" | "index_level" | "yield_pct"
    age_seconds: float          # seconds elapsed since fetched_at_utc, at normalization time


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_quotes(raw_quotes: dict[str, RawQuote]) -> dict[str, NormalizedQuote]:
    """Normalize all raw quotes.

    Symbols whose fetch failed are excluded from the result. The caller can
    detect which symbols were dropped by comparing keys with the input dict.
    """
    result: dict[str, NormalizedQuote] = {}
    for symbol, raw in raw_quotes.items():
        normalized = normalize_quote(raw)
        if normalized is not None:
            result[symbol] = normalized
        else:
            logger.debug(f"{symbol}: excluded from normalization — fetch_succeeded=False")
    return result


# Short alias for interactive / pipeline use
normalize_all = normalize_quotes


def normalize_quote(raw: RawQuote) -> Optional[NormalizedQuote]:
    """Normalize a single RawQuote.

    Returns None if the quote did not succeed (fetch_succeeded=False).
    Never raises — normalization errors are logged and return None.
    """
    if not raw.fetch_succeeded:
        return None

    try:
        price = _validated_float(raw.price, f"{raw.symbol} price")
        pct_change = _to_decimal(raw.pct_change_raw, raw.symbol)
        fetched_at_utc = _ensure_utc(raw.fetched_at_utc, raw.symbol)
        age_seconds = (datetime.now(timezone.utc) - fetched_at_utc).total_seconds()
        units = config.SYMBOL_UNITS.get(raw.symbol, config.DEFAULT_UNITS)

        return NormalizedQuote(
            symbol=raw.symbol,
            price=price,
            pct_change_decimal=pct_change,
            volume=raw.volume,
            fetched_at_utc=fetched_at_utc,
            source=raw.source,
            units=units,
            age_seconds=age_seconds,
        )
    except Exception as exc:
        logger.error(f"{raw.symbol}: normalization failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_decimal(pct_change_raw: float, symbol: str) -> float:
    """Return pct_change as a decimal fraction.

    Ingestion always computes pct_change as (price - prev) / prev, which is
    already decimal. This function is a pass-through with an explicit
    sanity guard: if the raw value exceeds ±2.0, it was almost certainly
    formatted as a percentage (e.g., 52.0 instead of 0.52) and we correct it.
    Values in [-2.0, 2.0] cover ±200% daily moves — well beyond any realistic
    single-session change for the symbols in our universe.
    """
    val = float(pct_change_raw)
    if math.isnan(val):
        logger.warning(f"{symbol}: pct_change_raw is NaN — defaulting to 0.0")
        return 0.0
    if abs(val) > 2.0:
        logger.warning(
            f"{symbol}: pct_change_raw={val:.4f} appears to be percentage-formatted "
            f"(|value| > 2.0) — dividing by 100"
        )
        return val / 100.0
    return val


def _ensure_utc(dt: datetime, symbol: str) -> datetime:
    """Guarantee the datetime carries UTC timezone info."""
    if dt.tzinfo is None:
        logger.warning(f"{symbol}: fetched_at_utc is naive — assuming UTC")
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _validated_float(value: float, label: str) -> float:
    """Cast to float and reject NaN/Inf."""
    f = float(value)
    if math.isnan(f) or math.isinf(f):
        raise ValueError(f"{label} is {f}")
    return f
