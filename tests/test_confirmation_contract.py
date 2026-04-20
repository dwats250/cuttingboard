from __future__ import annotations

import importlib
from datetime import datetime

import pytz

from cuttingboard.confirmation import (
    DIRECTION_DOWN,
    DIRECTION_UP,
    STATE_BREAK_ONLY,
    STATE_FAILURE_CONFIRMED,
    STATE_HOLD_CONFIRMED,
    STATE_IDLE,
    LevelConfirmation,
    evaluate_level_confirmation,
)
from cuttingboard.intraday_state_engine import Bar, compute_intraday_state

ET = pytz.timezone("US/Eastern")


def _bar(hour: int, minute: int, open_: float, high: float, low: float, close: float, volume: int = 1_000_000) -> Bar:
    return Bar(
        timestamp=ET.localize(datetime(2026, 4, 18, hour, minute, 0)),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


def _orb_bars() -> list[Bar]:
    return [
        _bar(9, 30, 451.0, 455.0, 450.0, 452.0, 2_000_000),
        _bar(9, 31, 452.0, 454.5, 451.0, 453.0, 1_800_000),
        _bar(9, 32, 453.0, 454.0, 451.5, 452.5, 1_900_000),
        _bar(9, 33, 452.5, 453.5, 450.5, 451.0, 2_100_000),
        _bar(9, 34, 451.0, 452.0, 450.0, 451.5, 1_700_000),
    ]


def _noise_bars(from_minute: int = 35, to_minute: int = 44) -> list[Bar]:
    return [_bar(9, minute, 452.0, 453.0, 451.0, 452.0) for minute in range(from_minute, to_minute + 1)]


def test_runtime_import_succeeds_with_notification_exports():
    runtime = importlib.import_module("cuttingboard.runtime")
    assert runtime is not None


def test_level_confirmation_accepts_engine_kwargs_and_exposes_required_attributes():
    confirmation = LevelConfirmation(
        level_name="OR_LOW",
        level_price=450.0,
        state=STATE_IDLE,
        direction=None,
        break_candle_index=None,
        current_candle_index=None,
        holding_closes=0,
        reclaim_active=False,
        trades_allowed=False,
        output="SYSTEM_DEFAULT",
        evaluation_candles=0,
        reclaim_candle_index=None,
    )

    assert confirmation.level_name == "OR_LOW"
    assert confirmation.level_price == 450.0
    assert confirmation.state == STATE_IDLE
    assert confirmation.direction is None
    assert confirmation.break_candle_index is None
    assert confirmation.current_candle_index is None
    assert confirmation.holding_closes == 0
    assert confirmation.reclaim_active is False
    assert confirmation.trades_allowed is False
    assert confirmation.output == "SYSTEM_DEFAULT"
    assert confirmation.evaluation_candles == 0
    assert confirmation.reclaim_candle_index is None


def test_evaluate_level_confirmation_returns_coherent_states():
    idle = evaluate_level_confirmation("OR_HIGH", 455.0, [452.0, 453.0], allowed_directions={DIRECTION_UP})
    broken = evaluate_level_confirmation("OR_HIGH", 455.0, [452.0, 456.0], allowed_directions={DIRECTION_UP})
    held = evaluate_level_confirmation("OR_HIGH", 455.0, [456.0, 456.5, 457.0], allowed_directions={DIRECTION_UP})
    failed = evaluate_level_confirmation("OR_LOW", 450.0, [449.0, 450.3], allowed_directions={DIRECTION_DOWN})

    assert idle.state == STATE_IDLE
    assert idle.direction is None
    assert broken.state == STATE_BREAK_ONLY
    assert broken.break_candle_index == 1
    assert broken.holding_closes == 1
    assert broken.trades_allowed is False
    assert held.state == STATE_HOLD_CONFIRMED
    assert held.direction == DIRECTION_UP
    assert held.holding_closes == 3
    assert held.trades_allowed is True
    assert failed.state == STATE_FAILURE_CONFIRMED
    assert failed.direction == DIRECTION_DOWN
    assert failed.reclaim_active is True
    assert failed.reclaim_candle_index == 1


def test_compute_intraday_state_pre_confirmation_path_does_not_raise():
    result = compute_intraday_state("SPY", _orb_bars() + _noise_bars(35, 42))
    assert result is None


def test_compute_intraday_state_post_break_path_does_not_raise():
    bars = _orb_bars() + _noise_bars() + [
        _bar(9, 45, 456.0, 458.0, 455.5, 457.0, 2_000_000),
        _bar(9, 46, 456.0, 457.5, 455.2, 456.0, 1_800_000),
    ]

    result = compute_intraday_state("SPY", bars)

    assert result is not None
    assert result.orb_break_direction == "LONG"
    assert result.permission_state == STATE_BREAK_ONLY


def test_compute_intraday_state_normal_path_returns_structural_result():
    bars = _orb_bars() + _noise_bars() + [
        _bar(9, 45, 452.0, 453.0, 451.0, 452.0),
        _bar(9, 46, 452.0, 453.0, 451.0, 452.1),
    ]

    result = compute_intraday_state("SPY", bars)

    assert result is not None
    assert result.permission_state == STATE_IDLE
    assert result.orb_break_direction is None


def test_compute_intraday_state_no_longer_crashes_on_constructor_or_attribute_contract():
    bars = _orb_bars() + _noise_bars() + [
        _bar(9, 45, 449.0, 449.5, 447.0, 448.0, 2_000_000),
        _bar(9, 46, 448.5, 449.0, 447.2, 448.2, 1_900_000),
    ]

    result = compute_intraday_state("SPY", bars, previous_close=455.0)

    assert result is not None
    assert result.permission_state == STATE_BREAK_ONLY
    assert result.acceptance_below_level is True
