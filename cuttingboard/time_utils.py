"""
Canonical time utilities for market session logic.

All market time decisions must go through these functions.
Source of truth: UTC. Conversion target: US/Eastern (DST-aware).
"""

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

_EASTERN = ZoneInfo("America/New_York")
_MARKET_OPEN_ET = time(9, 30)
_MARKET_CLOSE_ET = time(16, 0)


def get_now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_now_et() -> datetime:
    return datetime.now(_EASTERN)


def convert_utc_to_et(dt_utc: datetime) -> datetime:
    return dt_utc.astimezone(_EASTERN)


def is_after_entry_cutoff(now_et: datetime, cutoff: time) -> bool:
    return (now_et.hour, now_et.minute) >= (cutoff.hour, cutoff.minute)


def is_market_open(now_et: datetime) -> bool:
    t = (now_et.hour, now_et.minute)
    return _MARKET_OPEN_ET <= time(*t) < _MARKET_CLOSE_ET
