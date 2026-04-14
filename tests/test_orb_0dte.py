"""Fixtures for the deterministic ORB 0DTE engine.

Deterministic fixture assumptions
--------------------------------
- Fixture timestamps are built in UTC, then normalized by the engine into PT.
- `_utc_ts()` encodes PT close timestamps by adding seven hours for the April
  DST session used in this suite, so `07:15` PT is stored as `14:15` UTC.
- Candle timestamps represent 5-minute bar close times.
- The opening range therefore uses fixture close timestamps `06:35` through
  `07:00` PT to represent the `06:30` through `07:00` PT opening range.
- Synthetic sessions are intentionally self-contained and do not depend on the
  repo's spread engine, runtime, or reporting layers.
"""

from datetime import UTC, date, datetime, timedelta
import inspect

import cuttingboard.orb_0dte as orb_0dte
from cuttingboard.orb_0dte import (
    ENTRY_WINDOW_MORNING_PT,
    OPENING_RANGE_PERIOD_PT,
    OPENING_RANGE_TIMESTAMP_SEMANTICS,
    OPENING_RANGE_WINDOW_PT,
    SESSION_REFERENCE_PRICE_SEMANTICS,
    SIMULTANEOUS_KILL_POLICY,
    SIMULTANEOUS_SIGNAL_POLICY,
    TIMESTAMP_SEMANTICS,
    Candle,
    OptionSnapshot,
    SessionInput,
    evaluate_orb_0dte_session,
)


SESSION_DATE = date(2026, 4, 13)


def _utc_ts(hour: int, minute: int) -> datetime:
    return datetime(2026, 4, 13, hour + 7, minute, tzinfo=UTC)


def _time_range(start_hour: int, start_minute: int, end_hour: int, end_minute: int) -> list[tuple[int, int]]:
    current = datetime(2026, 4, 13, start_hour, start_minute)
    end = datetime(2026, 4, 13, end_hour, end_minute)
    values: list[tuple[int, int]] = []
    while current <= end:
        values.append((current.hour, current.minute))
        current += timedelta(minutes=5)
    return values


def _candle(hour: int, minute: int, open_: float, high: float, low: float, close: float, volume: float, *, headline: bool = False) -> Candle:
    return Candle(
        timestamp=_utc_ts(hour, minute),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        headline_shock=headline,
    )


def _option(hour: int, minute: int, *, symbol: str, contract_id: str, option_type: str, strike: float, delta: float, premium: float, open_premium: float) -> OptionSnapshot:
    return OptionSnapshot(
        contract_id=contract_id,
        timestamp=_utc_ts(hour, minute),
        expiry=SESSION_DATE,
        option_type=option_type,
        strike=strike,
        delta=delta,
        premium=premium,
        session_open_premium=open_premium,
        underlying_symbol=symbol,
    )


def _build_series(overrides: dict[tuple[int, int], dict[str, float | bool]], *, end: tuple[int, int]) -> list[Candle]:
    candles: list[Candle] = []
    last_close = 100.0
    for hour, minute in _time_range(6, 35, end[0], end[1]):
        spec = overrides.get((hour, minute))
        if spec is None:
            open_ = last_close
            close = last_close
            candles.append(_candle(hour, minute, open_, open_ + 0.08, open_ - 0.08, close, 90.0))
            continue
        open_ = float(spec.get("open", last_close))
        close = float(spec["close"])
        high = float(spec.get("high", max(open_, close) + 0.05))
        low = float(spec.get("low", min(open_, close) - 0.05))
        volume = float(spec.get("volume", 100.0))
        headline = bool(spec.get("headline", False))
        candles.append(_candle(hour, minute, open_, high, low, close, volume, headline=headline))
        last_close = close
    return candles


def _long_morning_overrides() -> dict[tuple[int, int], dict[str, float | bool]]:
    return {
        (6, 35): {"open": 100.00, "high": 100.25, "low": 99.85, "close": 100.10, "volume": 100},
        (6, 40): {"high": 100.35, "low": 100.00, "close": 100.30, "volume": 100},
        (6, 45): {"high": 100.55, "low": 100.20, "close": 100.50, "volume": 100},
        (6, 50): {"high": 100.75, "low": 100.40, "close": 100.70, "volume": 100},
        (6, 55): {"high": 100.95, "low": 100.60, "close": 100.80, "volume": 100},
        (7, 0): {"high": 101.10, "low": 100.70, "close": 101.00, "volume": 100},
        (7, 5): {"high": 101.60, "low": 100.95, "close": 101.55, "volume": 220},
        (7, 10): {"high": 101.95, "low": 101.45, "close": 101.90, "volume": 170},
        (7, 15): {"high": 102.25, "low": 101.80, "close": 102.20, "volume": 160},
    }


def _short_morning_overrides() -> dict[tuple[int, int], dict[str, float | bool]]:
    return {
        (6, 35): {"open": 100.00, "high": 100.10, "low": 99.70, "close": 99.90, "volume": 100},
        (6, 40): {"high": 99.95, "low": 99.55, "close": 99.70, "volume": 100},
        (6, 45): {"high": 99.75, "low": 99.35, "close": 99.50, "volume": 100},
        (6, 50): {"high": 99.55, "low": 99.10, "close": 99.25, "volume": 100},
        (6, 55): {"high": 99.35, "low": 98.95, "close": 99.10, "volume": 100},
        (7, 0): {"high": 99.20, "low": 98.80, "close": 98.95, "volume": 100},
        (7, 5): {"high": 99.00, "low": 98.30, "close": 98.35, "volume": 220},
        (7, 10): {"high": 98.45, "low": 98.00, "close": 98.05, "volume": 170},
        (7, 15): {"high": 98.10, "low": 97.70, "close": 97.75, "volume": 160},
    }


def _session(spy_candles: list[Candle], qqq_candles: list[Candle], spy_options: list[OptionSnapshot], qqq_options: list[OptionSnapshot], *, scheduled: bool = False) -> SessionInput:
    return SessionInput(
        session_date=SESSION_DATE,
        candles={"SPY": spy_candles, "QQQ": qqq_candles},
        option_snapshots={"SPY": spy_options, "QQQ": qqq_options},
        scheduled_high_impact_day=scheduled,
    )


def test_clean_long_trend_day():
    spy = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"high": 102.55, "low": 102.10, "close": 102.50, "volume": 150},
            (7, 25): {"high": 102.95, "low": 102.45, "close": 102.90, "volume": 150},
            (7, 30): {"high": 103.20, "low": 102.80, "close": 103.10, "volume": 140},
        },
        end=(7, 30),
    )
    qqq = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"high": 102.60, "low": 102.05, "close": 102.52, "volume": 150},
            (7, 25): {"high": 103.00, "low": 102.48, "close": 102.94, "volume": 150},
            (7, 30): {"high": 103.25, "low": 102.82, "close": 103.14, "volume": 140},
        },
        end=(7, 30),
    )
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-0DTE-C", option_type="call", strike=102.0, delta=0.50, premium=1.00, open_premium=0.80),
        _option(7, 20, symbol="SPY", contract_id="SPY-0DTE-C", option_type="call", strike=102.0, delta=0.55, premium=1.55, open_premium=0.80),
        _option(7, 25, symbol="SPY", contract_id="SPY-0DTE-C", option_type="call", strike=102.0, delta=0.60, premium=2.05, open_premium=0.80),
        _option(7, 30, symbol="SPY", contract_id="SPY-0DTE-C", option_type="call", strike=102.0, delta=0.62, premium=2.12, open_premium=0.80),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.entry is not None
    assert result.entry.symbol == "SPY"
    assert result.entry.direction == "LONG"
    assert result.kill_switch == "NONE"
    assert result.exit_cause == "TP2"
    assert any(item.startswith("ENTERED:SPY:breakout@") for item in result.qualification_audit)
    assert any(item.startswith("EXIT:TP1@") for item in result.exit_audit)
    assert any(item.startswith("EXIT:TP2@") for item in result.exit_audit)
    assert [exit_.reason for exit_ in result.exits] == ["TP1", "TP2"]


def test_clean_short_trend_day():
    spy = _build_series(
        {
            **_short_morning_overrides(),
            (7, 20): {"high": 97.80, "low": 97.30, "close": 97.35, "volume": 150},
            (7, 25): {"high": 97.40, "low": 96.95, "close": 97.00, "volume": 150},
            (7, 30): {"high": 97.05, "low": 96.60, "close": 96.70, "volume": 140},
        },
        end=(7, 30),
    )
    qqq = _build_series(
        {
            **_short_morning_overrides(),
            (7, 20): {"high": 97.85, "low": 97.25, "close": 97.32, "volume": 150},
            (7, 25): {"high": 97.38, "low": 96.92, "close": 96.98, "volume": 150},
            (7, 30): {"high": 97.02, "low": 96.58, "close": 96.68, "volume": 140},
        },
        end=(7, 30),
    )
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-0DTE-P", option_type="put", strike=98.0, delta=-0.51, premium=1.00, open_premium=0.75),
        _option(7, 20, symbol="SPY", contract_id="SPY-0DTE-P", option_type="put", strike=98.0, delta=-0.56, premium=1.50, open_premium=0.75),
        _option(7, 25, symbol="SPY", contract_id="SPY-0DTE-P", option_type="put", strike=98.0, delta=-0.60, premium=2.02, open_premium=0.75),
        _option(7, 30, symbol="SPY", contract_id="SPY-0DTE-P", option_type="put", strike=98.0, delta=-0.64, premium=2.10, open_premium=0.75),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.entry is not None
    assert result.entry.direction == "SHORT"
    assert result.kill_switch == "NONE"
    assert result.exit_cause == "TP2"
    assert [exit_.reason for exit_ in result.exits] == ["TP1", "TP2"]


def test_false_or_break_with_reentry():
    overrides = {
        **_long_morning_overrides(),
        (7, 10): {"high": 101.40, "low": 100.70, "close": 100.95, "volume": 140},
        (7, 15): {"high": 101.10, "low": 100.60, "close": 100.90, "volume": 120},
    }
    spy = _build_series(overrides, end=(7, 30))
    qqq = _build_series(overrides, end=(7, 30))

    result = evaluate_orb_0dte_session(_session(spy, qqq, [], []))

    assert result.entry is None
    assert result.mode == "DISABLED"
    assert result.execution_ready is False


def test_chop_day_with_no_trade():
    overrides = {
        (6, 35): {"open": 100.00, "high": 100.20, "low": 99.70, "close": 100.10, "volume": 100},
        (6, 40): {"high": 100.25, "low": 99.80, "close": 99.95, "volume": 100},
        (6, 45): {"high": 100.30, "low": 99.85, "close": 100.15, "volume": 100},
        (6, 50): {"high": 100.25, "low": 99.80, "close": 100.00, "volume": 100},
        (6, 55): {"high": 100.30, "low": 99.82, "close": 100.12, "volume": 100},
        (7, 0): {"high": 100.28, "low": 99.84, "close": 100.05, "volume": 100},
    }
    spy = _build_series(overrides, end=(12, 45))
    qqq = _build_series(overrides, end=(12, 45))

    result = evaluate_orb_0dte_session(_session(spy, qqq, [], []))

    assert result.entry is None
    assert result.mode == "DISABLED"
    assert result.kill_switch == "NONE"


def test_public_constants_document_timestamp_and_window_semantics():
    assert "5-minute bar close timestamps" in TIMESTAMP_SEMANTICS
    assert OPENING_RANGE_PERIOD_PT == (datetime(2026, 4, 13, 6, 30).time(), datetime(2026, 4, 13, 7, 0).time())
    assert OPENING_RANGE_WINDOW_PT == (datetime(2026, 4, 13, 6, 35).time(), datetime(2026, 4, 13, 7, 0).time())
    assert ENTRY_WINDOW_MORNING_PT == (datetime(2026, 4, 13, 7, 5).time(), datetime(2026, 4, 13, 7, 30).time())
    assert "06:35 through 07:00 PT" in OPENING_RANGE_TIMESTAMP_SEMANTICS
    assert "open of the first opening-range close bar" in SESSION_REFERENCE_PRICE_SEMANTICS


def test_module_is_self_contained_without_existing_runtime_or_spread_imports():
    source = inspect.getsource(orb_0dte)
    assert "from cuttingboard." not in source
    assert "import cuttingboard." not in source


def test_scheduled_event_day_skip():
    spy = _build_series(_long_morning_overrides(), end=(7, 15))
    qqq = _build_series(_long_morning_overrides(), end=(7, 15))

    result = evaluate_orb_0dte_session(_session(spy, qqq, [], [], scheduled=True))

    assert result.fail_reason == "SCHEDULED_HIGH_IMPACT_DAY"
    assert result.qualification_audit == ("SESSION_SKIPPED:SCHEDULED_HIGH_IMPACT_DAY",)
    assert result.entry is None


def test_power_hour_valid_entry():
    long_noon = {
        (12, 0): {"high": 101.55, "low": 100.95, "close": 101.50, "volume": 230},
        (12, 5): {"high": 101.90, "low": 101.35, "close": 101.85, "volume": 180},
        (12, 10): {"high": 102.20, "low": 101.70, "close": 102.15, "volume": 170},
    }
    base = {
        (6, 35): {"open": 100.00, "high": 100.25, "low": 99.85, "close": 100.10, "volume": 100},
        (6, 40): {"high": 100.35, "low": 100.00, "close": 100.30, "volume": 100},
        (6, 45): {"high": 100.55, "low": 100.20, "close": 100.50, "volume": 100},
        (6, 50): {"high": 100.75, "low": 100.40, "close": 100.70, "volume": 100},
        (6, 55): {"high": 100.95, "low": 100.60, "close": 100.80, "volume": 100},
        (7, 0): {"high": 101.10, "low": 100.70, "close": 101.00, "volume": 100},
    }
    spy = _build_series({**base, **long_noon}, end=(12, 10))
    qqq = _build_series({**base, **long_noon}, end=(12, 10))
    spy_options = [
        _option(12, 10, symbol="SPY", contract_id="SPY-NOON-C", option_type="call", strike=102.0, delta=0.49, premium=1.10, open_premium=0.70),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.entry is not None
    assert result.entry.entry_time_pt.hour == 12
    assert result.entry.entry_time_pt.minute == 10


def test_power_hour_invalid_entry_due_to_stale_trend():
    stale_noon = {
        (12, 0): {"high": 101.45, "low": 100.95, "close": 101.40, "volume": 230},
        (12, 5): {"high": 101.44, "low": 101.20, "close": 101.38, "volume": 180},
        (12, 10): {"high": 101.43, "low": 101.18, "close": 101.36, "volume": 170},
    }
    base = {
        (6, 35): {"open": 100.00, "high": 100.25, "low": 99.85, "close": 100.10, "volume": 100},
        (6, 40): {"high": 100.35, "low": 100.00, "close": 100.30, "volume": 100},
        (6, 45): {"high": 100.55, "low": 100.20, "close": 100.50, "volume": 100},
        (6, 50): {"high": 100.75, "low": 100.40, "close": 100.70, "volume": 100},
        (6, 55): {"high": 100.95, "low": 100.60, "close": 100.80, "volume": 100},
        (7, 0): {"high": 101.10, "low": 100.70, "close": 101.00, "volume": 100},
    }
    spy = _build_series({**base, **stale_noon}, end=(12, 10))
    qqq = _build_series({**base, **stale_noon}, end=(12, 10))
    spy_options = [
        _option(12, 10, symbol="SPY", contract_id="SPY-NOON-C", option_type="call", strike=102.0, delta=0.49, premium=1.10, open_premium=0.70),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.entry is None
    assert result.execution_ready is False


def test_simultaneous_signal_policy_prefers_spy_when_both_are_ready():
    spy = _build_series(_long_morning_overrides(), end=(7, 15))
    qqq = _build_series(_long_morning_overrides(), end=(7, 15))
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-FIRST-C", option_type="call", strike=102.0, delta=0.50, premium=1.00, open_premium=0.80),
    ]
    qqq_options = [
        _option(7, 15, symbol="QQQ", contract_id="QQQ-SECOND-C", option_type="call", strike=102.0, delta=0.50, premium=1.00, open_premium=0.80),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, qqq_options))

    assert result.entry is not None
    assert result.entry.symbol == "SPY"
    assert any(item.startswith("SIMULTANEOUS_SIGNAL:") for item in result.qualification_audit)
    assert any(item.startswith("SIGNAL_SUPPRESSED:QQQ:breakout@") for item in result.qualification_audit)
    assert any(SIMULTANEOUS_SIGNAL_POLICY in event for event in result.events)


def test_post_entry_headline_kill():
    spy = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"open": 102.20, "high": 103.20, "low": 102.15, "close": 103.05, "volume": 300, "headline": True},
        },
        end=(7, 20),
    )
    qqq = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"open": 102.18, "high": 103.10, "low": 102.10, "close": 102.98, "volume": 300, "headline": True},
        },
        end=(7, 20),
    )
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-HEADLINE-C", option_type="call", strike=102.0, delta=0.50, premium=1.00, open_premium=0.80),
        _option(7, 20, symbol="SPY", contract_id="SPY-HEADLINE-C", option_type="call", strike=102.0, delta=0.60, premium=1.20, open_premium=0.80),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.kill_switch == "HEADLINE"
    assert result.exit_cause == "HEADLINE"
    assert any(item.startswith("EXIT:HEADLINE@") for item in result.exit_audit)
    assert result.exits[-1].reason == "HEADLINE"


def test_stall_kill():
    spy = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"high": 102.24, "low": 101.95, "close": 102.05, "volume": 110},
            (7, 25): {"high": 102.23, "low": 101.90, "close": 102.00, "volume": 110},
            (7, 30): {"high": 102.22, "low": 101.85, "close": 101.98, "volume": 110},
        },
        end=(7, 30),
    )
    qqq = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"high": 102.24, "low": 101.95, "close": 102.05, "volume": 110},
            (7, 25): {"high": 102.23, "low": 101.90, "close": 102.00, "volume": 110},
            (7, 30): {"high": 102.22, "low": 101.85, "close": 101.98, "volume": 110},
        },
        end=(7, 30),
    )
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-STALL-C", option_type="call", strike=102.0, delta=0.50, premium=1.00, open_premium=0.80),
        _option(7, 20, symbol="SPY", contract_id="SPY-STALL-C", option_type="call", strike=102.0, delta=0.52, premium=1.05, open_premium=0.80),
        _option(7, 25, symbol="SPY", contract_id="SPY-STALL-C", option_type="call", strike=102.0, delta=0.52, premium=1.04, open_premium=0.80),
        _option(7, 30, symbol="SPY", contract_id="SPY-STALL-C", option_type="call", strike=102.0, delta=0.51, premium=1.03, open_premium=0.80),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.kill_switch == "STALL"
    assert result.exit_cause == "STALL"
    assert result.exits[-1].reason == "STALL"


def test_stop_loss_hit():
    spy = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"high": 102.30, "low": 102.00, "close": 102.10, "volume": 120},
        },
        end=(7, 20),
    )
    qqq = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"high": 102.35, "low": 102.02, "close": 102.12, "volume": 120},
        },
        end=(7, 20),
    )
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-STOP-C", option_type="call", strike=102.0, delta=0.50, premium=1.00, open_premium=0.80),
        _option(7, 20, symbol="SPY", contract_id="SPY-STOP-C", option_type="call", strike=102.0, delta=0.45, premium=0.74, open_premium=0.80),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.kill_switch == "STOP"
    assert result.exit_cause == "STOP"
    assert result.exits[-1].reason == "STOP"


def test_delta_unavailable():
    spy = _build_series(_long_morning_overrides(), end=(7, 15))
    qqq = _build_series(_long_morning_overrides(), end=(7, 15))
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-90-C", option_type="call", strike=90.0, delta=0.20, premium=1.20, open_premium=0.80),
        _option(7, 15, symbol="SPY", contract_id="SPY-95-C", option_type="call", strike=95.0, delta=0.25, premium=1.10, open_premium=0.80),
        _option(7, 15, symbol="SPY", contract_id="SPY-100-C", option_type="call", strike=100.0, delta=0.30, premium=1.00, open_premium=0.80),
        _option(7, 15, symbol="SPY", contract_id="SPY-110-C", option_type="call", strike=110.0, delta=0.70, premium=0.80, open_premium=0.80),
        _option(7, 15, symbol="SPY", contract_id="SPY-115-C", option_type="call", strike=115.0, delta=0.65, premium=0.70, open_premium=0.80),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.entry is None
    assert result.fail_reason == "DELTA_UNAVAILABLE"
    assert any(item.startswith("QUALIFICATION_REJECTED:SPY:breakout:DELTA_UNAVAILABLE@") for item in result.qualification_audit)


def test_or_too_narrow():
    narrow = {
        (6, 35): {"open": 100.00, "high": 100.05, "low": 99.95, "close": 100.01, "volume": 100},
        (6, 40): {"high": 100.06, "low": 99.96, "close": 100.00, "volume": 100},
        (6, 45): {"high": 100.04, "low": 99.97, "close": 100.01, "volume": 100},
        (6, 50): {"high": 100.05, "low": 99.98, "close": 100.00, "volume": 100},
        (6, 55): {"high": 100.04, "low": 99.97, "close": 100.02, "volume": 100},
        (7, 0): {"high": 100.05, "low": 99.98, "close": 100.01, "volume": 100},
    }
    spy = _build_series(narrow, end=(7, 0))
    qqq = _build_series(narrow, end=(7, 0))

    result = evaluate_orb_0dte_session(_session(spy, qqq, [], []))

    assert result.fail_reason == "OR_TOO_NARROW"
    assert result.qualification_audit == ("QUALIFICATION_FAILED:OR_TOO_NARROW",)
    assert result.entry is None


def test_premium_already_expanded_over_150_percent():
    spy = _build_series(_long_morning_overrides(), end=(7, 15))
    qqq = _build_series(_long_morning_overrides(), end=(7, 15))
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-RICH-C", option_type="call", strike=102.0, delta=0.50, premium=2.10, open_premium=0.80),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.entry is None
    assert result.fail_reason == "PREMIUM_EXPANDED"
    assert any(item.startswith("QUALIFICATION_REJECTED:SPY:breakout:PREMIUM_EXPANDED@") for item in result.qualification_audit)


def test_or_threshold_just_above_boundary_is_allowed():
    boundary = {
        (6, 35): {"open": 100.00, "high": 100.15, "low": 99.90, "close": 100.05, "volume": 100},
        (6, 40): {"high": 100.16, "low": 99.91, "close": 100.06, "volume": 100},
        (6, 45): {"high": 100.17, "low": 99.92, "close": 100.07, "volume": 100},
        (6, 50): {"high": 100.18, "low": 99.93, "close": 100.08, "volume": 100},
        (6, 55): {"high": 100.19, "low": 99.94, "close": 100.09, "volume": 100},
        (7, 0): {"high": 100.21, "low": 99.90, "close": 100.10, "volume": 100},
        (7, 5): {"high": 100.40, "low": 100.02, "close": 100.35, "volume": 220},
        (7, 10): {"high": 100.55, "low": 100.28, "close": 100.50, "volume": 170},
        (7, 15): {"high": 100.70, "low": 100.42, "close": 100.66, "volume": 160},
    }
    spy = _build_series(boundary, end=(7, 15))
    qqq = _build_series(boundary, end=(7, 15))
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-BOUNDARY-C", option_type="call", strike=101.0, delta=0.50, premium=1.00, open_premium=0.50),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.fail_reason is None
    assert result.entry is not None


def test_premium_expansion_exact_boundary_is_allowed():
    spy = _build_series(_long_morning_overrides(), end=(7, 15))
    qqq = _build_series(_long_morning_overrides(), end=(7, 15))
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-LIMIT-C", option_type="call", strike=102.0, delta=0.50, premium=2.00, open_premium=0.80),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.fail_reason is None
    assert result.entry is not None


def test_duplicate_timestamps_are_rejected_as_invalid_data():
    spy = _build_series(_long_morning_overrides(), end=(7, 15))
    qqq = _build_series(_long_morning_overrides(), end=(7, 15))
    spy.insert(1, spy[1])

    result = evaluate_orb_0dte_session(_session(spy, qqq, [], []))

    assert result.fail_reason == "DATA_INVALID"
    assert result.qualification_audit == ("QUALIFICATION_FAILED:DATA_INVALID",)
    assert any("candle order invalid" in event for event in result.events)


def test_malformed_candle_is_rejected_as_invalid_data():
    spy = _build_series(_long_morning_overrides(), end=(7, 15))
    qqq = _build_series(_long_morning_overrides(), end=(7, 15))
    bad = spy[2]
    spy[2] = Candle(
        timestamp=bad.timestamp,
        open=bad.open,
        high=bad.close - 0.01,
        low=bad.low,
        close=bad.close,
        volume=bad.volume,
        headline_shock=bad.headline_shock,
    )

    result = evaluate_orb_0dte_session(_session(spy, qqq, [], []))

    assert result.fail_reason == "DATA_INVALID"
    assert any("malformed candle high" in event for event in result.events)


def test_simultaneous_kill_policy_prefers_headline_over_or_reentry():
    spy = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"open": 102.20, "high": 102.25, "low": 100.90, "close": 101.00, "volume": 300, "headline": True},
        },
        end=(7, 20),
    )
    qqq = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"open": 102.20, "high": 102.25, "low": 100.90, "close": 101.00, "volume": 300, "headline": True},
        },
        end=(7, 20),
    )
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-KILL-C", option_type="call", strike=102.0, delta=0.50, premium=1.00, open_premium=0.80),
        _option(7, 20, symbol="SPY", contract_id="SPY-KILL-C", option_type="call", strike=102.0, delta=0.42, premium=0.90, open_premium=0.80),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert "HEADLINE before OR_REENTRY" in SIMULTANEOUS_KILL_POLICY
    assert result.kill_switch == "HEADLINE"
    assert result.exits[-1].reason == "HEADLINE"


def test_simultaneous_kill_policy_prefers_stop_over_stall():
    spy = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"high": 102.24, "low": 101.95, "close": 102.05, "volume": 110},
            (7, 25): {"high": 102.23, "low": 101.90, "close": 102.00, "volume": 110},
            (7, 30): {"high": 102.22, "low": 101.85, "close": 101.98, "volume": 110},
        },
        end=(7, 30),
    )
    qqq = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"high": 102.24, "low": 101.95, "close": 102.05, "volume": 110},
            (7, 25): {"high": 102.23, "low": 101.90, "close": 102.00, "volume": 110},
            (7, 30): {"high": 102.22, "low": 101.85, "close": 101.98, "volume": 110},
        },
        end=(7, 30),
    )
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-STOPSTALL-C", option_type="call", strike=102.0, delta=0.50, premium=1.00, open_premium=0.80),
        _option(7, 20, symbol="SPY", contract_id="SPY-STOPSTALL-C", option_type="call", strike=102.0, delta=0.52, premium=1.05, open_premium=0.80),
        _option(7, 25, symbol="SPY", contract_id="SPY-STOPSTALL-C", option_type="call", strike=102.0, delta=0.52, premium=1.04, open_premium=0.80),
        _option(7, 30, symbol="SPY", contract_id="SPY-STOPSTALL-C", option_type="call", strike=102.0, delta=0.51, premium=0.74, open_premium=0.80),
    ]

    result = evaluate_orb_0dte_session(_session(spy, qqq, spy_options, []))

    assert result.kill_switch == "STOP"
    assert result.exits[-1].reason == "STOP"
