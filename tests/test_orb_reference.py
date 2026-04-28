import json

import pandas as pd
import pytest

from algos.orb_reference import (
    compute_opening_range,
    detect_breakout,
    execute_trade,
    run_backtest,
    run_orb_day,
)


NY_TZ = "America/New_York"
TRADE_DATE = "2024-01-02"


def make_day() -> pd.DataFrame:
    timestamps = pd.date_range(
        f"{TRADE_DATE} 09:30:00",
        f"{TRADE_DATE} 15:55:00",
        freq="min",
        tz=NY_TZ,
    )
    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": 100.0,
            "high": 100.40,
            "low": 99.60,
            "close": 100.0,
            "volume": 1000,
        }
    )

    opening_range_values = {
        "09:30": (100.00, 100.50, 99.40, 100.10),
        "09:31": (100.10, 100.80, 99.30, 100.20),
        "09:32": (100.20, 101.00, 99.00, 100.30),
        "09:33": (100.30, 100.70, 99.20, 100.00),
        "09:34": (100.00, 100.60, 99.10, 100.20),
    }
    for minute, values in opening_range_values.items():
        set_bar(df, minute, open=values[0], high=values[1], low=values[2], close=values[3])

    return df


def set_bar(df: pd.DataFrame, hhmm: str, **values: float) -> None:
    timestamp = pd.Timestamp(f"{TRADE_DATE} {hhmm}:00", tz=NY_TZ)
    idx = df.index[df["timestamp"] == timestamp][0]
    for column, value in values.items():
        df.at[idx, column] = value


def test_opening_range_correct() -> None:
    df = make_day()

    or_high, or_low = compute_opening_range(df)

    assert or_high == 101.0
    assert or_low == 99.0


def test_entry_requires_close_confirmation_and_uses_next_open() -> None:
    df = make_day()
    set_bar(df, "09:35", open=100.20, high=101.50, low=100.10, close=100.90)
    set_bar(df, "09:36", open=100.95, high=101.30, low=100.90, close=101.10)
    set_bar(df, "09:37", open=101.40, high=101.60, low=101.10, close=101.30)

    signal = detect_breakout(df, 101.0, 99.0)

    assert signal == {
        "direction": "LONG",
        "signal_time": "2024-01-02T09:36:00-05:00",
        "entry_time": "2024-01-02T09:37:00-05:00",
        "entry_price": 101.40,
        "signal_index": 6,
        "entry_index": 7,
    }


def test_long_trade_stop_and_target_are_exact_two_r() -> None:
    df = make_day()
    set_bar(df, "09:35", open=100.40, high=101.30, low=100.20, close=101.10)
    set_bar(df, "09:36", open=101.50, high=101.60, low=101.20, close=101.40)
    set_bar(df, "09:40", open=105.80, high=106.50, low=105.20, close=106.00)

    trade = run_orb_day(df, "SPY")

    assert trade["stop_price"] == 99.0
    assert trade["target_price"] == 106.5
    assert trade["exit_reason"] == "TARGET"
    assert trade["exit_price"] == 106.5
    assert trade["R_multiple"] == 2.0


def test_short_trade_stop_and_target_are_exact_two_r() -> None:
    df = make_day()
    set_bar(df, "09:35", open=99.70, high=99.80, low=98.70, close=98.80)
    set_bar(df, "09:36", open=98.50, high=98.70, low=98.20, close=98.40)
    set_bar(df, "09:39", open=94.20, high=94.80, low=93.50, close=94.00)

    trade = run_orb_day(df, "QQQ")

    assert trade["direction"] == "SHORT"
    assert trade["stop_price"] == 101.0
    assert trade["target_price"] == 93.5
    assert trade["exit_reason"] == "TARGET"
    assert trade["exit_price"] == 93.5
    assert trade["R_multiple"] == 2.0


def test_no_breakout_returns_none() -> None:
    assert run_orb_day(make_day(), "SPY") is None


def test_exit_priority_stop_before_target_when_both_touched() -> None:
    df = make_day()
    set_bar(df, "09:35", open=100.40, high=101.30, low=100.20, close=101.10)
    set_bar(df, "09:36", open=101.50, high=101.60, low=101.20, close=101.40)
    set_bar(df, "09:37", open=101.40, high=106.50, low=98.90, close=100.00)

    trade = run_orb_day(df, "SPY")

    assert trade["exit_reason"] == "STOP"
    assert trade["exit_price"] == 99.0
    assert trade["R_multiple"] == -1.0


def test_eod_exit_if_stop_and_target_never_hit() -> None:
    df = make_day()
    set_bar(df, "09:35", open=100.40, high=101.30, low=100.20, close=101.10)
    set_bar(df, "09:36", open=101.50, high=101.60, low=101.20, close=101.40)
    set_bar(df, "15:55", open=101.80, high=102.20, low=101.60, close=102.00)

    trade = run_orb_day(df, "SPY")

    assert trade["exit_reason"] == "EOD"
    assert trade["exit_time"] == "2024-01-02T15:55:00-05:00"
    assert trade["exit_price"] == 102.0
    assert trade["R_multiple"] == pytest.approx(0.2)


def test_one_trade_per_symbol_day_ignores_later_opposite_break() -> None:
    df = make_day()
    set_bar(df, "09:35", open=100.40, high=101.30, low=100.20, close=101.10)
    set_bar(df, "09:36", open=101.50, high=101.60, low=101.20, close=101.40)
    set_bar(df, "09:45", open=99.30, high=99.40, low=98.80, close=98.90)
    set_bar(df, "15:55", open=101.80, high=102.20, low=101.60, close=102.00)

    trades = run_backtest({"SPY": df})

    assert len(trades) == 1
    assert trades[0]["direction"] == "LONG"
    assert trades[0]["entry_time"] == "2024-01-02T09:36:00-05:00"


def test_missing_candle_raises_value_error() -> None:
    df = make_day()
    missing_timestamp = pd.Timestamp(f"{TRADE_DATE} 09:40:00", tz=NY_TZ)
    df = df[df["timestamp"] != missing_timestamp]

    with pytest.raises(ValueError, match="missing candles"):
        run_orb_day(df, "SPY")


def test_backtest_is_deterministic() -> None:
    df = make_day()
    set_bar(df, "09:35", open=100.40, high=101.30, low=100.20, close=101.10)
    set_bar(df, "09:36", open=101.50, high=101.60, low=101.20, close=101.40)
    set_bar(df, "09:40", open=105.80, high=106.50, low=105.20, close=106.00)

    first = run_backtest({"SPY": df})
    second = run_backtest({"SPY": df})

    assert first == second


def test_snapshot_known_trade_output_json() -> None:
    df = make_day()
    set_bar(df, "09:35", open=100.40, high=101.30, low=100.20, close=101.10)
    set_bar(df, "09:36", open=101.50, high=101.60, low=101.20, close=101.40)
    set_bar(df, "09:40", open=105.80, high=106.50, low=105.20, close=106.00)

    trade = run_backtest({"SPY": df})[0]
    snapshot = json.dumps(trade, sort_keys=True, separators=(",", ":"))

    assert snapshot == (
        '{"R_multiple":2.0,"date":"2024-01-02","direction":"LONG",'
        '"entry_price":101.5,"entry_time":"2024-01-02T09:36:00-05:00",'
        '"exit_price":106.5,"exit_reason":"TARGET",'
        '"exit_time":"2024-01-02T09:40:00-05:00","stop_price":99.0,'
        '"symbol":"SPY","target_price":106.5}'
    )


def test_execute_trade_accepts_explicit_signal_event() -> None:
    df = make_day()
    signal_event = {
        "symbol": "SPY",
        "direction": "LONG",
        "signal_time": "2024-01-02T09:35:00-05:00",
        "entry_time": "2024-01-02T09:36:00-05:00",
        "entry_price": 101.50,
        "signal_index": 5,
        "entry_index": 6,
    }
    set_bar(df, "09:40", open=105.80, high=106.50, low=105.20, close=106.00)

    trade = execute_trade(df, signal_event, 101.0, 99.0)

    assert trade["symbol"] == "SPY"
    assert trade["exit_reason"] == "TARGET"
