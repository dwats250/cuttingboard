"""
Canonical time utilities for market session logic.

All market time decisions must go through these functions.
Source of truth: UTC. Conversion target: US/Eastern (DST-aware).
"""

from datetime import date, datetime, time, timedelta, timezone
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


def most_recent_completed_session_date(now_utc: datetime) -> date:
    """The latest weekday strictly before now_utc's UTC date.

    The daily OHLCV fetch uses end=<today UTC> (exclusive), so the newest bar it
    can return is exactly this date. A cache whose last bar is this date already
    holds the freshest data a re-fetch could produce, so the OHLCV cache
    freshness check (PRD-193) treats it as fresh and reuses it.

    Holiday-unaware by design: on a post-holiday day this returns the holiday (a
    weekday with no bar), so the cache's last real bar is older and freshness
    falls through to a safe, redundant re-fetch -- never to serving stale data. A
    naive datetime is treated as UTC.
    """
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    d = now_utc.astimezone(timezone.utc).date() - timedelta(days=1)
    while d.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        d -= timedelta(days=1)
    return d
