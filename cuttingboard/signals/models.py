"""Models for deterministic signal generation."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Timeframe = Literal["1m", "5m", "15m"]
SessionType = Literal["premarket", "intraday", "close"]


@dataclass(frozen=True)
class MarketData:
    ticker: str
    price: float
    prev_price: float
    ema9: float
    ema21: float
    ema50: float
    atr14: float
    volume: float


@dataclass(frozen=True)
class ScanContext:
    timestamp: datetime
    timeframe: Timeframe
    session_type: SessionType
