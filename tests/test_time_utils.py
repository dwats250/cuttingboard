"""
Tests for cuttingboard/time_utils.py.

All 8 PRD-009 validation scenarios, plus function contract checks.
"""

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from cuttingboard import time_utils

_ET = ZoneInfo("America/New_York")
_UTC = timezone.utc

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc(year, month, day, hour, minute, second=0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=_UTC)


def _et(year, month, day, hour, minute, second=0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=_ET)


# ---------------------------------------------------------------------------
# PRD-009 Validation Case 1
# GIVEN now = 2026-04-22 13:45 UTC  (April → EDT, -4)
# EXPECT now_et = 09:45 ET, is_after_cutoff = False
# ---------------------------------------------------------------------------

def test_case1_utc_to_et_conversion():
    now_utc = _utc(2026, 4, 22, 13, 45)
    now_et = time_utils.convert_utc_to_et(now_utc)
    assert now_et.hour == 9
    assert now_et.minute == 45


def test_case1_not_after_cutoff():
    now_utc = _utc(2026, 4, 22, 13, 45)
    now_et = time_utils.convert_utc_to_et(now_utc)
    assert not time_utils.is_after_entry_cutoff(now_et, time(15, 30))


# ---------------------------------------------------------------------------
# PRD-009 Validation Case 2
# GIVEN now = 2026-04-22 19:31 UTC  (April → EDT, -4)
# EXPECT now_et = 15:31 ET, is_after_cutoff = True
# ---------------------------------------------------------------------------

def test_case2_utc_to_et_conversion():
    now_utc = _utc(2026, 4, 22, 19, 31)
    now_et = time_utils.convert_utc_to_et(now_utc)
    assert now_et.hour == 15
    assert now_et.minute == 31


def test_case2_is_after_cutoff():
    now_utc = _utc(2026, 4, 22, 19, 31)
    now_et = time_utils.convert_utc_to_et(now_utc)
    assert time_utils.is_after_entry_cutoff(now_et, time(15, 30))


# ---------------------------------------------------------------------------
# PRD-009 Validation Case 3 — Winter EST (-5 offset)
# GIVEN now = 2026-01-15 18:45 UTC
# EXPECT correct -5 offset → 13:45 ET
# ---------------------------------------------------------------------------

def test_case3_winter_offset():
    now_utc = _utc(2026, 1, 15, 18, 45)
    now_et = time_utils.convert_utc_to_et(now_utc)
    assert now_et.utcoffset().total_seconds() == -5 * 3600
    assert now_et.hour == 13
    assert now_et.minute == 45


# ---------------------------------------------------------------------------
# PRD-009 Validation Case 4 — Summer EDT (-4 offset)
# GIVEN now = 2026-07-15 17:45 UTC
# EXPECT correct -4 offset → 13:45 ET
# ---------------------------------------------------------------------------

def test_case4_summer_offset():
    now_utc = _utc(2026, 7, 15, 17, 45)
    now_et = time_utils.convert_utc_to_et(now_utc)
    assert now_et.utcoffset().total_seconds() == -4 * 3600
    assert now_et.hour == 13
    assert now_et.minute == 45


# ---------------------------------------------------------------------------
# PRD-009 Validation Case 5 — 09:29 ET → market_open = False
# ---------------------------------------------------------------------------

def test_case5_market_not_open_before_930():
    now_et = _et(2026, 4, 22, 9, 29)
    assert not time_utils.is_market_open(now_et)


# ---------------------------------------------------------------------------
# PRD-009 Validation Case 6 — 09:30 ET → market_open = True
# ---------------------------------------------------------------------------

def test_case6_market_open_at_930():
    now_et = _et(2026, 4, 22, 9, 30)
    assert time_utils.is_market_open(now_et)


# ---------------------------------------------------------------------------
# PRD-009 Validation Case 7 — 16:01 ET → market_open = False
# ---------------------------------------------------------------------------

def test_case7_market_closed_after_1600():
    now_et = _et(2026, 4, 22, 16, 1)
    assert not time_utils.is_market_open(now_et)


# ---------------------------------------------------------------------------
# Additional correctness tests
# ---------------------------------------------------------------------------

def test_market_open_16_00_is_closed():
    # Market closes at the 4:00 PM bell — 16:00 itself is closed
    now_et = _et(2026, 4, 22, 16, 0)
    assert not time_utils.is_market_open(now_et)


def test_cutoff_exactly_at_1530_is_blocked():
    now_et = _et(2026, 4, 22, 15, 30)
    assert time_utils.is_after_entry_cutoff(now_et, time(15, 30))


def test_cutoff_one_minute_before_is_not_blocked():
    now_et = _et(2026, 4, 22, 15, 29)
    assert not time_utils.is_after_entry_cutoff(now_et, time(15, 30))


def test_get_now_utc_is_tz_aware():
    now = time_utils.get_now_utc()
    assert now.tzinfo is not None
    assert now.utcoffset().total_seconds() == 0


def test_get_now_et_is_tz_aware():
    now = time_utils.get_now_et()
    assert now.tzinfo is not None


def test_convert_utc_to_et_returns_tz_aware():
    result = time_utils.convert_utc_to_et(_utc(2026, 4, 22, 13, 0))
    assert result.tzinfo is not None


def test_convert_utc_to_et_result_has_eastern_zone():
    """Result must carry Eastern timezone info, not UTC."""
    result = time_utils.convert_utc_to_et(_utc(2026, 4, 22, 13, 0))
    offset = result.utcoffset().total_seconds()
    # EDT (-4h) or EST (-5h)
    assert offset in (-4 * 3600, -5 * 3600)
