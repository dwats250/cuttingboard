"""
PRD-107: Trend Structure Snapshot — sidecar builder.

Pure deterministic builder. No network, no file I/O, no datetime.now().
Produces one record per configured tradable symbol describing higher-timeframe
and (when available) intraday structure context for trade evaluation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping, Optional

import pandas as pd

from cuttingboard.normalization import NormalizedQuote

SCHEMA_VERSION = 1
SOURCE = "trend_structure"


def _close_series(df: Optional[pd.DataFrame]) -> Optional[pd.Series]:
    if df is None or getattr(df, "empty", True):
        return None
    if "Close" not in df.columns:
        return None
    closes = df["Close"].dropna()
    if closes.empty:
        return None
    return closes


def _sma(closes: Optional[pd.Series], window: int) -> Optional[float]:
    if closes is None or len(closes) < window:
        return None
    return float(closes.tail(window).mean())


def _is_intraday(df: pd.DataFrame) -> bool:
    if len(df.index) < 2:
        return False
    try:
        idx = pd.to_datetime(df.index)
        return (idx[-1] - idx[-2]) < pd.Timedelta(days=1)
    except Exception:
        return False


def _vwap(df: Optional[pd.DataFrame]) -> Optional[float]:
    if df is None or getattr(df, "empty", True):
        return None
    required = {"High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns):
        return None
    if not _is_intraday(df):
        return None
    try:
        idx = pd.to_datetime(df.index)
        last_date = idx[-1].date()
        mask = [ts.date() == last_date for ts in idx]
        session = df.loc[mask]
    except Exception:
        return None
    if session.empty:
        return None
    typical = (session["High"] + session["Low"] + session["Close"]) / 3.0
    volume = session["Volume"].astype(float)
    cum_vol = volume.cumsum()
    if cum_vol.iloc[-1] <= 0:
        return None
    return float((typical * volume).cumsum().iloc[-1] / cum_vol.iloc[-1])


def _relative_volume(df: Optional[pd.DataFrame]) -> Optional[float]:
    if df is None or getattr(df, "empty", True) or "Volume" not in df.columns:
        return None
    vols = df["Volume"].dropna()
    if len(vols) < 21:
        return None
    today = float(vols.iloc[-1])
    prior_20 = float(vols.iloc[-21:-1].mean())
    if prior_20 <= 0:
        return None
    return today / prior_20


# PRD-130: deterministic unknown-state tokens replacing the legacy "UNKNOWN"
# emission. `_cmp()` is a pure comparison primitive; callers own causality
# routing for missing-input cases. `SESSION_UNAVAILABLE` is renderer-only and
# is never emitted by this module.
_UNAVAILABLE_PRIORITY: tuple[str, ...] = (
    "DATA_UNAVAILABLE",
    "INSUFFICIENT_HISTORY",
    "NOT_COMPUTED",
)
_UNAVAILABLE_SET: frozenset[str] = frozenset(_UNAVAILABLE_PRIORITY)


def _propagate_unavailable(*tokens: str) -> Optional[str]:
    for priority in _UNAVAILABLE_PRIORITY:
        if priority in tokens:
            return priority
    return None


def _cmp(price: Optional[float], ref: Optional[float]) -> Optional[str]:
    # PRD-130: pure comparison primitive. Returns None sentinel when inputs
    # are missing — the caller routes the upstream cause to the correct
    # unavailable token. _cmp() never emits DATA_UNAVAILABLE,
    # INSUFFICIENT_HISTORY, or NOT_COMPUTED.
    if price is None or ref is None:
        return None
    if price > ref:
        return "ABOVE"
    if price < ref:
        return "BELOW"
    return "AT_LEVEL"


def _classify_vwap_unavailable(
    df: Optional[pd.DataFrame], vwap_value: Optional[float]
) -> str:
    # PRD-130: classify the upstream cause when _vwap() returned None.
    # Non-intraday (daily-bar) input is an intentional computation boundary
    # → NOT_COMPUTED. Every other None path is a true data outage →
    # DATA_UNAVAILABLE.
    if vwap_value is not None:
        return "OK"
    if df is None or getattr(df, "empty", True):
        return "DATA_UNAVAILABLE"
    required = {"High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns):
        return "DATA_UNAVAILABLE"
    if not _is_intraday(df):
        return "NOT_COMPUTED"
    return "DATA_UNAVAILABLE"


def _classify_sma_unavailable(
    closes: Optional[pd.Series], sma_value: Optional[float], window: int
) -> str:
    # PRD-130: classify the upstream cause when _sma() returned None.
    # _close_series() None → DATA_UNAVAILABLE; valid-but-short closes →
    # INSUFFICIENT_HISTORY.
    if sma_value is not None:
        return "OK"
    if closes is None:
        return "DATA_UNAVAILABLE"
    return "INSUFFICIENT_HISTORY"


def _resolve_vwap_field(
    price: Optional[float],
    vwap: Optional[float],
    df: Optional[pd.DataFrame],
) -> str:
    raw = _cmp(price, vwap)
    if raw is not None:
        return raw
    if price is None:
        return "DATA_UNAVAILABLE"
    return _classify_vwap_unavailable(df, vwap)


def _resolve_sma_field(
    price: Optional[float],
    sma: Optional[float],
    closes: Optional[pd.Series],
    window: int,
) -> str:
    raw = _cmp(price, sma)
    if raw is not None:
        return raw
    if price is None:
        return "DATA_UNAVAILABLE"
    return _classify_sma_unavailable(closes, sma, window)


def _trend_alignment(p_sma50: str, p_sma200: str) -> str:
    propagated = _propagate_unavailable(p_sma50, p_sma200)
    if propagated is not None:
        return propagated
    if p_sma50 == "ABOVE" and p_sma200 == "ABOVE":
        return "BULLISH"
    if p_sma50 == "BELOW" and p_sma200 == "BELOW":
        return "BEARISH"
    return "MIXED"


def _entry_context(data_status: str, alignment: str, p_vwap: str) -> str:
    if data_status == "MISSING":
        return "DATA_UNAVAILABLE"
    propagated = _propagate_unavailable(alignment, p_vwap)
    if propagated is not None:
        return propagated
    if alignment == "BULLISH" and p_vwap == "ABOVE":
        return "SUPPORTIVE"
    if alignment == "BEARISH" and p_vwap == "BELOW":
        return "AVOID"
    return "NEUTRAL"


def _reason(
    data_status: str,
    alignment: str,
    p_vwap: str,
    entry_context: str,
) -> str:
    if data_status == "MISSING":
        return "current_price unavailable"
    if entry_context == "SUPPORTIVE":
        return "BULLISH alignment with price above VWAP"
    if entry_context == "AVOID":
        return "BEARISH alignment with price below VWAP"
    if alignment in _UNAVAILABLE_SET:
        return f"trend alignment {alignment} — sma_50 or sma_200 missing"
    if p_vwap in _UNAVAILABLE_SET:
        return f"{alignment} alignment; VWAP {p_vwap}"
    if p_vwap == "AT_LEVEL":
        return f"{alignment} alignment with price at VWAP"
    return f"{alignment} alignment with price {p_vwap.lower()} VWAP"


def _data_status(
    current_price: Optional[float],
    vwap: Optional[float],
    sma_50: Optional[float],
    sma_200: Optional[float],
) -> str:
    if current_price is None:
        return "MISSING"
    if vwap is None or sma_50 is None or sma_200 is None:
        return "PARTIAL"
    return "OK"


def _format_generated_at(generated_at: Optional[datetime]) -> Optional[str]:
    if generated_at is None:
        return None
    if generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return generated_at.isoformat()


def _build_record(
    symbol: str,
    quote: Optional[NormalizedQuote],
    df: Optional[pd.DataFrame],
) -> dict[str, Any]:
    current_price = float(quote.price) if quote is not None else None

    closes = _close_series(df)
    sma_50 = _sma(closes, 50)
    sma_200 = _sma(closes, 200)
    vwap = _vwap(df)
    rel_vol = _relative_volume(df)

    p_vwap = _resolve_vwap_field(current_price, vwap, df)
    p_sma50 = _resolve_sma_field(current_price, sma_50, closes, 50)
    p_sma200 = _resolve_sma_field(current_price, sma_200, closes, 200)

    data_status = _data_status(current_price, vwap, sma_50, sma_200)
    alignment = _trend_alignment(p_sma50, p_sma200)
    entry_context = _entry_context(data_status, alignment, p_vwap)
    reason = _reason(data_status, alignment, p_vwap, entry_context)

    return {
        "symbol": symbol,
        "data_status": data_status,
        "current_price": current_price,
        "vwap": vwap,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "relative_volume": rel_vol,
        "price_vs_vwap": p_vwap,
        "price_vs_sma_50": p_sma50,
        "price_vs_sma_200": p_sma200,
        "trend_alignment": alignment,
        "entry_context": entry_context,
        "reason": reason,
    }


def build_trend_structure_snapshot(
    normalized_quotes: Mapping[str, NormalizedQuote],
    history_by_symbol: Mapping[str, pd.DataFrame],
    symbols: Iterable[str],
    generated_at: Optional[datetime] = None,
) -> dict[str, Any]:
    """Build a deterministic trend structure snapshot.

    Args:
        normalized_quotes: dict[str, NormalizedQuote]. current_price = price.
        history_by_symbol: dict[str, pandas.DataFrame] of OHLCV bars
            (columns include Open, High, Low, Close, Volume).
        symbols: iterable of tradable symbols to emit records for.
        generated_at: timezone-aware datetime, or None.

    Returns:
        dict with keys: schema_version, generated_at, source, symbols.
    """
    symbol_records: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        quote = normalized_quotes.get(symbol)
        df = history_by_symbol.get(symbol)
        symbol_records[symbol] = _build_record(symbol, quote, df)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _format_generated_at(generated_at),
        "source": SOURCE,
        "symbols": symbol_records,
    }
