"""Deterministic SSRN-style Opening Range Breakout reference model.

This module is intentionally standalone. It has no market-data fetching,
randomness, portfolio sizing, commissions, slippage, indicators, or external
state. Input data must be supplied as pandas DataFrames with 1-minute OHLCV
candles.
"""

from __future__ import annotations

from datetime import time
from typing import Any

import pandas as pd


UNIVERSE = ("SPY", "QQQ")
NY_TZ = "America/New_York"

RTH_OPEN = time(9, 30)
OPENING_RANGE_END = time(9, 35)
EOD_EXIT = time(15, 55)
TAKE_PROFIT_R = 2.0

REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
PRICE_COLUMNS = ("open", "high", "low", "close")


def compute_opening_range(df: pd.DataFrame) -> tuple[float, float]:
    """Return (OR_HIGH, OR_LOW) from 09:30 through 09:34 NY candles."""
    day = _prepare_day_frame(df)
    times = day["timestamp"].dt.time
    opening_range = day[(times >= RTH_OPEN) & (times < OPENING_RANGE_END)]

    if len(opening_range) != 5:
        raise ValueError("opening range must contain exactly five 1-minute candles")

    return float(opening_range["high"].max()), float(opening_range["low"].min())


def detect_breakout(
    df: pd.DataFrame, or_high: float, or_low: float
) -> dict[str, Any] | None:
    """Return the first confirmed breakout event, or None if no entry exists."""
    day = _prepare_day_frame(df)

    for idx in range(len(day) - 1):
        candle = day.iloc[idx]
        candle_time = candle["timestamp"].time()
        if candle_time < OPENING_RANGE_END:
            continue

        if float(candle["close"]) > or_high and float(candle["high"]) >= or_high:
            entry_idx = idx + 1
            entry = day.iloc[entry_idx]
            return {
                "direction": "LONG",
                "signal_time": _iso(candle["timestamp"]),
                "entry_time": _iso(entry["timestamp"]),
                "entry_price": float(entry["open"]),
                "signal_index": idx,
                "entry_index": entry_idx,
            }

        if float(candle["close"]) < or_low and float(candle["low"]) <= or_low:
            entry_idx = idx + 1
            entry = day.iloc[entry_idx]
            return {
                "direction": "SHORT",
                "signal_time": _iso(candle["timestamp"]),
                "entry_time": _iso(entry["timestamp"]),
                "entry_price": float(entry["open"]),
                "signal_index": idx,
                "entry_index": entry_idx,
            }

    return None


def execute_trade(
    df: pd.DataFrame,
    signal_event: dict[str, Any],
    or_high: float,
    or_low: float,
) -> dict[str, Any]:
    """Execute one deterministic ORB trade from a breakout signal."""
    day = _prepare_day_frame(df)
    direction = signal_event["direction"]
    entry_index = int(signal_event["entry_index"])
    entry_price = float(signal_event["entry_price"])

    if direction == "LONG":
        stop_price = float(or_low)
        risk = abs(entry_price - stop_price)
        target_price = entry_price + (TAKE_PROFIT_R * risk)
    elif direction == "SHORT":
        stop_price = float(or_high)
        risk = abs(entry_price - stop_price)
        target_price = entry_price - (TAKE_PROFIT_R * risk)
    else:
        raise ValueError(f"unsupported direction: {direction!r}")

    if risk <= 0:
        raise ValueError("risk must be greater than zero")

    exit_time = None
    exit_price = None
    exit_reason = None

    for idx in range(entry_index, len(day)):
        candle = day.iloc[idx]

        if direction == "LONG":
            if float(candle["low"]) <= stop_price:
                exit_time = candle["timestamp"]
                exit_price = stop_price
                exit_reason = "STOP"
                break
            if float(candle["high"]) >= target_price:
                exit_time = candle["timestamp"]
                exit_price = target_price
                exit_reason = "TARGET"
                break
        else:
            if float(candle["high"]) >= stop_price:
                exit_time = candle["timestamp"]
                exit_price = stop_price
                exit_reason = "STOP"
                break
            if float(candle["low"]) <= target_price:
                exit_time = candle["timestamp"]
                exit_price = target_price
                exit_reason = "TARGET"
                break

        if candle["timestamp"].time() == EOD_EXIT:
            exit_time = candle["timestamp"]
            exit_price = float(candle["close"])
            exit_reason = "EOD"
            break

    if exit_time is None or exit_price is None or exit_reason is None:
        raise ValueError("no deterministic exit found; 15:55 EOD candle is required")

    if direction == "LONG":
        r_multiple = (exit_price - entry_price) / risk
    else:
        r_multiple = (entry_price - exit_price) / risk

    date = day["timestamp"].iloc[0].date().isoformat()
    return {
        "symbol": str(signal_event.get("symbol", "")),
        "date": date,
        "direction": direction,
        "entry_time": signal_event["entry_time"],
        "entry_price": entry_price,
        "stop_price": stop_price,
        "target_price": target_price,
        "exit_time": _iso(exit_time),
        "exit_price": float(exit_price),
        "exit_reason": exit_reason,
        "R_multiple": float(r_multiple),
    }


def run_orb_day(df: pd.DataFrame, symbol: str) -> dict[str, Any] | None:
    """Run one symbol for one trading day and return at most one trade."""
    if symbol not in UNIVERSE:
        raise ValueError(f"symbol must be one of {UNIVERSE}: {symbol!r}")

    day = _prepare_day_frame(df)
    or_high, or_low = compute_opening_range(day)
    signal_event = detect_breakout(day, or_high, or_low)
    if signal_event is None:
        return None

    signal_event = {**signal_event, "symbol": symbol}
    return execute_trade(day, signal_event, or_high, or_low)


def run_backtest(data: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Run the fixed SPY/QQQ universe in deterministic symbol/date order."""
    unknown_symbols = sorted(set(data) - set(UNIVERSE))
    if unknown_symbols:
        raise ValueError(f"unsupported symbols: {unknown_symbols}")

    trades: list[dict[str, Any]] = []
    for symbol in UNIVERSE:
        if symbol not in data:
            continue

        frame = _normalize_frame(data[symbol])
        dates = sorted(frame["timestamp"].dt.date.unique())
        for trade_date in dates:
            day = frame[frame["timestamp"].dt.date == trade_date]
            trade = run_orb_day(day, symbol)
            if trade is not None:
                trades.append(trade)

    return trades


def _prepare_day_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = _normalize_frame(df)
    dates = frame["timestamp"].dt.date.unique()
    if len(dates) != 1:
        raise ValueError("run_orb_day expects exactly one trading date")

    trade_date = dates[0]
    times = frame["timestamp"].dt.time
    session = frame[(times >= RTH_OPEN) & (times <= EOD_EXIT)].copy()
    if session.empty:
        raise ValueError("input must include the 09:30 through 15:55 RTH window")

    if session["timestamp"].duplicated().any():
        raise ValueError("duplicate 1-minute candles are not allowed")

    start = pd.Timestamp.combine(trade_date, RTH_OPEN).tz_localize(NY_TZ)
    end = pd.Timestamp.combine(trade_date, EOD_EXIT).tz_localize(NY_TZ)
    expected = pd.date_range(start=start, end=end, freq="min", tz=NY_TZ)
    actual = pd.DatetimeIndex(session["timestamp"])

    if len(actual) != len(expected) or not actual.equals(expected):
        missing = expected.difference(actual)
        extra = actual.difference(expected)
        parts = []
        if len(missing):
            parts.append(f"missing candles: {[ts.isoformat() for ts in missing[:5]]}")
        if len(extra):
            parts.append(f"unexpected candles: {[ts.isoformat() for ts in extra[:5]]}")
        detail = "; ".join(parts) if parts else "non-contiguous 1-minute candles"
        raise ValueError(detail)

    return session.reset_index(drop=True)


def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"missing required columns: {missing_columns}")

    frame = df.loc[:, REQUIRED_COLUMNS].copy()
    try:
        timestamps = pd.to_datetime(frame["timestamp"], errors="raise")
    except Exception as exc:  # pragma: no cover - pandas gives version-specific errors.
        raise ValueError("timestamp column must be parseable") from exc

    try:
        tz = timestamps.dt.tz
    except AttributeError as exc:
        raise ValueError("timestamp column must contain datetime-like values") from exc

    if tz is None:
        raise ValueError("timestamp values must be tz-aware")

    frame["timestamp"] = timestamps.dt.tz_convert(NY_TZ)

    if frame[list(PRICE_COLUMNS) + ["volume"]].isna().any().any():
        raise ValueError("OHLCV values must not contain missing data")

    for column in PRICE_COLUMNS:
        frame[column] = frame[column].astype(float)
    frame["volume"] = frame["volume"].astype(float)

    frame = frame.sort_values("timestamp").reset_index(drop=True)
    return frame


def _iso(timestamp: pd.Timestamp) -> str:
    return pd.Timestamp(timestamp).isoformat()
