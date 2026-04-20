"""
Tests for intraday_state_engine.py — Phase 1 ORB classification.

The ORB classifier now sits behind the deterministic confirmation layer:
initial breaks are informational only; trades only unlock after hold or
failure confirmation.
"""

from datetime import datetime, timedelta

import pytest
import pytz

from cuttingboard.intraday_state_engine import (
    Bar,
    DownsidePermissionState,
    InsufficientDataError,
    SessionContext,
    classify_gap,
    classify_phase,
    compute_intraday_state,
    detect_acceptance_below_level,
    detect_failed_reclaim,
    downside_short_permission,
)

ET = pytz.timezone("US/Eastern")


# ---------------------------------------------------------------------------
# Bar construction helpers
# ---------------------------------------------------------------------------

def _bar(hour: int, minute: int, open_: float, high: float, low: float, close: float,
         volume: int = 1_000_000) -> Bar:
    ts = ET.localize(datetime(2026, 4, 18, hour, minute, 0))
    return Bar(timestamp=ts, open=open_, high=high, low=low, close=close, volume=volume)


def _orb_bars() -> list[Bar]:
    """5 ORB bars 09:30–09:34, building range 450.00–455.00."""
    return [
        _bar(9, 30, 451.0, 455.0, 450.0, 452.0, volume=2_000_000),
        _bar(9, 31, 452.0, 454.5, 451.0, 453.0, volume=1_800_000),
        _bar(9, 32, 453.0, 454.0, 451.5, 452.5, volume=1_900_000),
        _bar(9, 33, 452.5, 453.5, 450.5, 451.0, volume=2_100_000),
        _bar(9, 34, 451.0, 452.0, 450.0, 451.5, volume=1_700_000),
        # orb_high = 455.00, orb_low = 450.00, orb_vol_avg = 1_900_000
    ]


def _noise_bars(from_minute: int = 35, to_minute: int = 44) -> list[Bar]:
    """Bars in the noise window — close stays inside ORB."""
    return [
        _bar(9, m, 452.0, 453.0, 451.0, 452.0, volume=1_000_000)
        for m in range(from_minute, to_minute + 1)
    ]


# ---------------------------------------------------------------------------
# T01 — clean long expansion
# ---------------------------------------------------------------------------

def test_t01_clean_long_expansion():
    """
    Break above ORB at 09:45, VWAP above, volume expanding, 5 holding bars.
    Expected: EXPANSION_CONFIRMED, confidence >= 0.80
    """
    bars = _orb_bars() + _noise_bars()

    # Post-noise: break candle + 2 confirmation candles above orb_high=455
    for i in range(3):
        bars.append(_bar(9, 45 + i, 456.0, 458.0, 455.5, 457.0, volume=3_000_000))

    result = compute_intraday_state("SPY", bars)

    assert result is not None
    assert result.state == "EXPANSION_CONFIRMED"
    assert result.confidence >= 0.80
    assert result.orb_break_direction == "LONG"
    assert result.permission_state == "HOLD_CONFIRMED"
    assert result.trades_allowed is True
    assert not result.reclaimed_orb


# ---------------------------------------------------------------------------
# T02 — clean short expansion
# ---------------------------------------------------------------------------

def test_t02_clean_short_expansion():
    """
    Break below ORB at 09:45, VWAP below, volume expanding, 5 holding bars.
    Expected: EXPANSION_CONFIRMED, confidence >= 0.80
    """
    bars = _orb_bars() + _noise_bars()

    # Drive VWAP down with break candle + 2 confirmation candles below orb_low=450
    for i in range(3):
        bars.append(_bar(9, 45 + i, 449.0, 449.5, 447.0, 448.0, volume=3_000_000))

    result = compute_intraday_state("SPY", bars)

    assert result is not None
    assert result.state == "EXPANSION_CONFIRMED"
    assert result.confidence >= 0.80
    assert result.orb_break_direction == "SHORT"
    assert result.permission_state == "HOLD_CONFIRMED"
    assert result.trades_allowed is True
    assert result.vwap_position == "BELOW"
    assert not result.reclaimed_orb


# ---------------------------------------------------------------------------
# T03 — failed breakout / reclaim
# ---------------------------------------------------------------------------

def test_t03_failed_breakout_reclaim():
    """
    Break above ORB, then close back inside within 2 bars.
    Expected: FAILED_EXPANSION, confidence <= 0.35
    """
    bars = _orb_bars() + _noise_bars()

    bars.append(_bar(9, 45, 456.0, 458.0, 455.5, 457.0, volume=2_000_000))  # break
    bars.append(_bar(9, 46, 455.0, 456.0, 451.0, 452.5, volume=1_200_000))  # reclaim
    bars.append(_bar(9, 47, 452.0, 453.0, 451.0, 451.5, volume=1_000_000))  # still inside

    result = compute_intraday_state("SPY", bars)

    assert result is not None
    assert result.state == "FAILED_EXPANSION"
    assert result.confidence <= 0.35
    assert result.permission_state == "FAILURE_CONFIRMED"
    assert result.trades_allowed is True
    assert result.reclaimed_orb is True


# ---------------------------------------------------------------------------
# T04 — range day
# ---------------------------------------------------------------------------

def test_t04_range_day():
    """
    No ORB break, VWAP neutral, volume flat throughout session.
    Expected: RANGE, confidence <= 0.40
    """
    bars = _orb_bars() + _noise_bars()

    # Extend into primary window, price stays inside ORB
    for i in range(10):
        bars.append(_bar(9, 45 + i, 452.0, 453.0, 451.0, 452.0, volume=1_000_000))

    result = compute_intraday_state("SPY", bars)

    assert result is not None
    assert result.state == "RANGE"
    assert result.confidence <= 0.40
    assert result.orb_break_direction is None


# ---------------------------------------------------------------------------
# T05 — late breakout at 14:00 ET (SECONDARY window)
# ---------------------------------------------------------------------------

def test_t05_late_breakout_secondary_window():
    """
    Valid expansion signal at 14:00 ET.
    Expected: EXPANSION_CONFIRMED, confidence <= 0.70 (time penalty applied)
    """
    bars = _orb_bars() + _noise_bars()

    # Range all morning
    for h in range(10, 14):
        for m in range(0, 60, 5):
            bars.append(_bar(h, m, 452.0, 453.5, 451.0, 452.5, volume=900_000))

    # Break above ORB at 14:00, then confirm on the third close beyond ORB.
    # so confidence = 0.30+0.30+0.20-0.10 = 0.70 (no volume signal)
    for i in range(3):
        bars.append(_bar(14, i, 456.0, 458.0, 455.5, 457.5, volume=1_900_000))

    result = compute_intraday_state("SPY", bars)

    assert result is not None
    assert result.state == "EXPANSION_CONFIRMED"
    assert result.confidence <= 0.71
    assert result.time_window == "SECONDARY"


# ---------------------------------------------------------------------------
# T06 — pre-confirmation call (09:42 ET) → None
# ---------------------------------------------------------------------------

def test_t06_pre_confirmation_returns_none():
    """
    Current bar timestamp is 09:42 ET — before noise exclusion window ends.
    Expected: None
    """
    bars = _orb_bars()

    # Add bars up to 09:42 (inside noise window)
    for m in range(35, 43):
        bars.append(_bar(9, m, 452.0, 453.0, 451.0, 452.0, volume=1_000_000))

    result = compute_intraday_state("SPY", bars)
    assert result is None


# ---------------------------------------------------------------------------
# T07 — insufficient ORB data (3 bars)
# ---------------------------------------------------------------------------

def test_t07_insufficient_orb_data():
    """
    Only 3 bars in the ORB window — should raise InsufficientDataError.
    """
    bars = [
        _bar(9, 30, 451.0, 455.0, 450.0, 452.0, volume=2_000_000),
        _bar(9, 31, 452.0, 454.5, 451.0, 453.0, volume=1_800_000),
        _bar(9, 32, 453.0, 454.0, 451.5, 452.5, volume=1_900_000),
        # only 3 bars — insufficient
        _bar(9, 50, 452.0, 453.0, 451.0, 452.0, volume=1_000_000),
    ]

    with pytest.raises(InsufficientDataError):
        compute_intraday_state("SPY", bars)


# ---------------------------------------------------------------------------
# T08 — break held for only 2 bars (below 3-bar confirmation threshold)
# ---------------------------------------------------------------------------

def test_t08_break_below_confirmation_threshold():
    """
    Break above ORB at 09:45 but only held for 2 total closes beyond ORB.
    The confirmation layer requires the break candle plus 2 more closes.
    Expected: RANGE (not EXPANSION_CONFIRMED), regardless of VWAP.
    """
    bars = _orb_bars() + _noise_bars()

    # Only 2 bars above orb_high=455 — insufficient for EXPANSION_CONFIRMED
    bars.append(_bar(9, 45, 456.0, 458.0, 455.5, 457.0, volume=2_000_000))
    bars.append(_bar(9, 46, 456.0, 457.5, 455.2, 456.0, volume=1_800_000))

    result = compute_intraday_state("SPY", bars)

    assert result is not None
    assert result.state != "EXPANSION_CONFIRMED"
    assert result.holding_bars == 2
    assert result.orb_break_direction == "LONG"
    assert result.permission_state == "BREAK_ONLY"
    assert result.trades_allowed is False


def test_classify_gap_returns_down_up_or_flat():
    assert classify_gap(99.0, 100.0) == "DOWN"
    assert classify_gap(101.0, 100.0) == "UP"
    assert classify_gap(100.1, 100.0) == "FLAT"


def test_classify_phase_returns_open_early_and_post_open():
    assert classify_phase(0) == "OPEN"
    assert classify_phase(4.99) == "OPEN"
    assert classify_phase(5) == "EARLY"
    assert classify_phase(29.99) == "EARLY"
    assert classify_phase(30) == "POST_OPEN"


def test_failed_reclaim_detection_is_high_touch_with_close_back_below():
    assert detect_failed_reclaim(high=450.0, close=449.5, level=450.0) is True
    assert detect_failed_reclaim(high=449.9, close=449.5, level=450.0) is False
    assert detect_failed_reclaim(high=450.2, close=450.1, level=450.0) is False


def test_acceptance_detection_requires_two_consecutive_closes_below_level():
    accepted, count = detect_acceptance_below_level([451.0, 449.9, 449.7], 450.0)
    assert accepted is True
    assert count == 2

    accepted, count = detect_acceptance_below_level([451.0, 449.9, 450.1], 450.0)
    assert accepted is False
    assert count == 0


def test_gap_down_open_phase_blocks_short_permission():
    context = SessionContext(open_price=99.0, prev_close=100.0, gap_type="DOWN")
    state = DownsidePermissionState(
        phase="OPEN",
        or_low_broken=True,
        failed_reclaim=False,
        acceptance_below_level=False,
    )

    assert downside_short_permission(context, state) is False


def test_gap_down_failed_reclaim_enables_short_permission():
    context = SessionContext(open_price=99.0, prev_close=100.0, gap_type="DOWN")
    state = DownsidePermissionState(
        phase="EARLY",
        or_low_broken=True,
        failed_reclaim=True,
        acceptance_below_level=False,
    )

    assert downside_short_permission(context, state) is True


def test_gap_down_acceptance_enables_short_permission():
    context = SessionContext(open_price=99.0, prev_close=100.0, gap_type="DOWN")
    state = DownsidePermissionState(
        phase="EARLY",
        or_low_broken=True,
        failed_reclaim=False,
        acceptance_below_level=True,
    )

    assert downside_short_permission(context, state) is True


def test_gap_down_clean_reclaim_blocks_short_permission():
    context = SessionContext(open_price=99.0, prev_close=100.0, gap_type="DOWN")
    state = DownsidePermissionState(
        phase="EARLY",
        or_low_broken=True,
        failed_reclaim=False,
        acceptance_below_level=False,
    )

    assert downside_short_permission(context, state) is False


def test_non_gap_down_permission_is_unaffected():
    state = DownsidePermissionState(
        phase="OPEN",
        or_low_broken=True,
        failed_reclaim=False,
        acceptance_below_level=False,
    )

    assert downside_short_permission(SessionContext(101.0, 100.0, "UP"), state) is True
    assert downside_short_permission(SessionContext(100.0, 100.0, "FLAT"), state) is True


def test_gap_down_short_requires_permission_even_when_confirmation_allows_trade():
    bars = _orb_bars() + _noise_bars()
    bars.append(_bar(9, 45, 449.0, 449.5, 447.0, 448.0, volume=2_000_000))
    bars.append(_bar(9, 46, 450.2, 451.0, 449.8, 450.4, volume=1_800_000))
    bars.append(_bar(9, 47, 450.4, 450.6, 449.9, 450.1, volume=1_700_000))

    result = compute_intraday_state("SPY", bars, previous_close=455.0)

    assert result is not None
    assert result.gap_type == "DOWN"
    assert result.orb_break_direction == "SHORT"
    assert result.permission_state == "FAILURE_CONFIRMED"
    assert result.trades_allowed is False
    assert result.failed_reclaim is False
    assert result.acceptance_below_level is False


def test_gap_down_short_acceptance_sets_permission_inputs_and_preserves_trade_block_if_unconfirmed():
    bars = _orb_bars() + _noise_bars()
    bars.append(_bar(9, 45, 449.0, 449.5, 447.0, 448.0, volume=2_000_000))
    bars.append(_bar(9, 46, 448.5, 449.0, 447.2, 448.2, volume=1_900_000))

    result = compute_intraday_state("SPY", bars, previous_close=455.0)

    assert result is not None
    assert result.gap_type == "DOWN"
    assert result.phase == "EARLY"
    assert result.orb_break_direction == "SHORT"
    assert result.acceptance_below_level is True
    assert result.consecutive_closes_below_level == 2
    assert result.permission_state == "BREAK_ONLY"
    assert result.trades_allowed is False
