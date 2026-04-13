"""Pre-filter and validation helpers for signal generation."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from numbers import Real

from cuttingboard import config
from cuttingboard.signals.models import MarketData, ScanContext

DEFAULT_SIGNAL_MIN_VOLUME = 500_000
MARKET_DATA_FIELDS = (
    "ticker",
    "price",
    "prev_price",
    "ema9",
    "ema21",
    "ema50",
    "atr14",
    "volume",
)
NUMERIC_MARKET_DATA_FIELDS = (
    "price",
    "prev_price",
    "ema9",
    "ema21",
    "ema50",
    "atr14",
    "volume",
)
VALID_TIMEFRAMES = {"1m", "5m", "15m"}
VALID_SESSION_TYPES = {"premarket", "intraday", "close"}


def signal_min_volume() -> float:
    return getattr(config, "SIGNAL_MIN_VOLUME", DEFAULT_SIGNAL_MIN_VOLUME)


def validate_market_data(item: object) -> MarketData:
    values = {field: _require_attr(item, field) for field in MARKET_DATA_FIELDS}
    ticker = values["ticker"]
    if not isinstance(ticker, str) or not ticker:
        raise ValueError("market_data.ticker is required")
    for field in NUMERIC_MARKET_DATA_FIELDS:
        values[field] = _require_finite_number(f"market_data.{field}", values[field])
    return MarketData(**values)


def validate_context(context: object) -> ScanContext:
    timestamp = _require_attr(context, "timestamp")
    timeframe = _require_attr(context, "timeframe")
    session_type = _require_attr(context, "session_type")

    if not isinstance(timestamp, datetime):
        raise ValueError("context.timestamp must be a datetime")
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("context.timestamp must be timezone-aware UTC")
    if timestamp.utcoffset() != UTC.utcoffset(timestamp):
        raise ValueError("context.timestamp must be timezone-aware UTC")
    if timeframe not in VALID_TIMEFRAMES:
        raise ValueError(f"context.timeframe must be one of {sorted(VALID_TIMEFRAMES)}")
    if session_type not in VALID_SESSION_TYPES:
        raise ValueError(
            f"context.session_type must be one of {sorted(VALID_SESSION_TYPES)}"
        )

    return ScanContext(
        timestamp=timestamp,
        timeframe=timeframe,
        session_type=session_type,
    )


def passes_pre_filter(data: MarketData) -> bool:
    return (
        data.price > 0
        and data.prev_price > 0
        and data.atr14 > 0
        and data.volume >= signal_min_volume()
    )


def _require_attr(item: object, field: str) -> object:
    if not hasattr(item, field):
        raise ValueError(f"market_data.{field} is required")
    return getattr(item, field)


def _require_finite_number(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be numeric")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return float(value)
