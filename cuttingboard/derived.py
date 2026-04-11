"""
Layer 4 — Derived Metrics.

Computed only on symbols that passed validation (valid_quotes).
Never estimated or interpolated — if history is insufficient, all metric
fields are None and sufficient_history is False.

Requires minimum OHLCV_MIN_BARS (21) bars. In practice, 6 months of daily
data (~126 bars) is fetched to ensure EMA convergence.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from cuttingboard import config
from cuttingboard.ingestion import fetch_ohlcv
from cuttingboard.normalization import NormalizedQuote

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DerivedMetrics:
    symbol: str
    ema9:              Optional[float]   # 9-period EMA of close
    ema21:             Optional[float]   # 21-period EMA of close
    ema50:             Optional[float]   # 50-period EMA of close
    ema_aligned_bull:  bool              # ema9 > ema21 > ema50
    ema_aligned_bear:  bool              # ema9 < ema21 < ema50
    ema_spread_pct:    Optional[float]   # (ema9 - ema21) / ema21
    atr14:             Optional[float]   # Wilder's RMA ATR, 14-period
    atr_pct:           Optional[float]   # atr14 / current_price
    momentum_5d:       Optional[float]   # 5-day return decimal
    volume_ratio:      Optional[float]   # today vol / 20d avg vol
    computed_at_utc:   datetime
    sufficient_history: bool             # False → all metric fields are None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_all_derived(
    valid_quotes: dict[str, NormalizedQuote],
) -> dict[str, DerivedMetrics]:
    """Compute derived metrics for every symbol in valid_quotes.

    Every symbol in valid_quotes appears in the result. Symbols without
    sufficient OHLCV history return DerivedMetrics(sufficient_history=False)
    with all metric fields as None.
    """
    results: dict[str, DerivedMetrics] = {}
    for symbol, quote in valid_quotes.items():
        results[symbol] = compute_derived(symbol, quote)
    return results


def compute_derived(symbol: str, quote: NormalizedQuote) -> DerivedMetrics:
    """Compute derived metrics for a single symbol.

    Loads OHLCV from cache (or fetches fresh). Returns an insufficient-history
    record without raising if data is unavailable or too short.
    """
    df = fetch_ohlcv(symbol)

    if df is None or len(df) < config.OHLCV_MIN_BARS:
        bars = len(df) if df is not None else 0
        logger.warning(
            f"{symbol}: insufficient OHLCV history ({bars} bars, "
            f"minimum {config.OHLCV_MIN_BARS}) — metrics unavailable"
        )
        return _insufficient(symbol)

    try:
        return _compute(symbol, quote, df)
    except Exception as exc:
        logger.error(f"{symbol}: derived metrics computation failed: {exc}", exc_info=True)
        return _insufficient(symbol)


# Short alias for interactive / pipeline use
compute_all = compute_all_derived


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def _compute(
    symbol: str,
    quote: NormalizedQuote,
    df: pd.DataFrame,
) -> DerivedMetrics:
    close = df["Close"].astype(float)

    ema9  = float(close.ewm(span=config.EMA_FAST,  adjust=False).mean().iloc[-1])
    ema21 = float(close.ewm(span=config.EMA_SLOW,  adjust=False).mean().iloc[-1])
    ema50 = float(close.ewm(span=config.EMA_TREND, adjust=False).mean().iloc[-1])

    ema_aligned_bull = ema9 > ema21 > ema50
    ema_aligned_bear = ema9 < ema21 < ema50
    ema_spread_pct   = (ema9 - ema21) / ema21 if ema21 != 0 else None

    atr14   = _wilder_atr(df)
    atr_pct = (atr14 / quote.price) if (atr14 is not None and quote.price > 0) else None

    momentum_5d  = _momentum_5d(close)
    volume_ratio = _volume_ratio(df)

    _vol_str = f"{volume_ratio:.2f}x" if volume_ratio is not None else "N/A"
    _mom_str = f"{momentum_5d:+.4f}" if momentum_5d is not None else "N/A"
    logger.info(
        f"{symbol}: EMA9={ema9:.4f} EMA21={ema21:.4f} EMA50={ema50:.4f} "
        f"ATR14={atr14:.4f} mom5d={_mom_str} vol_ratio={_vol_str}"
    )

    return DerivedMetrics(
        symbol=symbol,
        ema9=ema9,
        ema21=ema21,
        ema50=ema50,
        ema_aligned_bull=ema_aligned_bull,
        ema_aligned_bear=ema_aligned_bear,
        ema_spread_pct=ema_spread_pct,
        atr14=atr14,
        atr_pct=atr_pct,
        momentum_5d=momentum_5d,
        volume_ratio=volume_ratio,
        computed_at_utc=datetime.now(timezone.utc),
        sufficient_history=True,
    )


def _wilder_atr(df: pd.DataFrame) -> Optional[float]:
    """ATR14 using Wilder's RMA — ewm(alpha=1/14, adjust=False).

    Matches TradingView's ATR implementation exactly.
    True Range = max(H-L, |H-PrevC|, |L-PrevC|)
    """
    high  = df["High"].astype(float)
    low   = df["Low"].astype(float)
    close = df["Close"].astype(float)

    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)

    # Drop the first row whose prev_close is NaN before applying RMA
    tr = tr.dropna()
    if len(tr) < config.ATR_PERIOD:
        return None

    atr = float(tr.ewm(alpha=1 / config.ATR_PERIOD, adjust=False).mean().iloc[-1])
    return atr


def _momentum_5d(close: pd.Series) -> Optional[float]:
    """5-day return: (close[-1] - close[-6]) / close[-6]."""
    if len(close) < 6:
        return None
    prev = float(close.iloc[-6])
    if prev == 0:
        return None
    return (float(close.iloc[-1]) - prev) / prev


def _volume_ratio(df: pd.DataFrame) -> Optional[float]:
    """Today's volume divided by the prior 20-session average."""
    vol = df["Volume"].astype(float)
    if len(vol) < 21:
        return None
    today_vol   = float(vol.iloc[-1])
    avg_20d_vol = float(vol.iloc[-21:-1].mean())
    if avg_20d_vol <= 0:
        return None
    return today_vol / avg_20d_vol


# ---------------------------------------------------------------------------
# Insufficient-history sentinel
# ---------------------------------------------------------------------------

def _insufficient(symbol: str) -> DerivedMetrics:
    return DerivedMetrics(
        symbol=symbol,
        ema9=None,
        ema21=None,
        ema50=None,
        ema_aligned_bull=False,
        ema_aligned_bear=False,
        ema_spread_pct=None,
        atr14=None,
        atr_pct=None,
        momentum_5d=None,
        volume_ratio=None,
        computed_at_utc=datetime.now(timezone.utc),
        sufficient_history=False,
    )
