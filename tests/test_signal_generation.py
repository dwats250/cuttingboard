from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from cuttingboard.policy.models import TradeCandidate
from cuttingboard.signals import MarketData, ScanContext, generate_candidates


UTC_NOW = datetime(2026, 4, 13, 14, 30, tzinfo=timezone.utc)


def _context(**overrides) -> ScanContext:
    values = {
        "timestamp": UTC_NOW,
        "timeframe": "5m",
        "session_type": "intraday",
    }
    values.update(overrides)
    return ScanContext(**values)


def _market_data(**overrides) -> MarketData:
    values = {
        "ticker": "AAPL",
        "price": 103.0,
        "prev_price": 101.0,
        "ema9": 102.0,
        "ema21": 100.0,
        "ema50": 98.0,
        "atr14": 2.0,
        "volume": 1_000_000.0,
    }
    values.update(overrides)
    return MarketData(**values)


def test_generates_correct_breakout_long_candidate():
    result = generate_candidates([_market_data()], _context())
    assert result == [
        TradeCandidate(
            ticker="AAPL",
            direction="long",
            entry_price=103.0,
            stop_price=100.0,
            target_price=109.0,
            ema9=102.0,
            ema21=100.0,
            ema50=98.0,
            atr14=2.0,
            structure="breakout",
        )
    ]


def test_generates_correct_breakout_short_candidate():
    result = generate_candidates(
        [
            _market_data(
                ticker="TSLA",
                price=97.0,
                prev_price=99.0,
                ema9=98.0,
                ema21=100.0,
                ema50=102.0,
            )
        ],
        _context(),
    )
    assert result == [
        TradeCandidate(
            ticker="TSLA",
            direction="short",
            entry_price=97.0,
            stop_price=100.0,
            target_price=91.0,
            ema9=98.0,
            ema21=100.0,
            ema50=102.0,
            atr14=2.0,
            structure="breakout",
        )
    ]


def test_generates_correct_pullback_long_candidate():
    result = generate_candidates(
        [
            _market_data(
                ticker="NVDA",
                price=101.0,
                prev_price=101.5,
                ema9=102.0,
                ema21=100.0,
                ema50=98.0,
            )
        ],
        _context(),
    )
    assert result == [
        TradeCandidate(
            ticker="NVDA",
            direction="long",
            entry_price=101.0,
            stop_price=99.0,
            target_price=105.0,
            ema9=102.0,
            ema21=100.0,
            ema50=98.0,
            atr14=2.0,
            structure="pullback",
        )
    ]


def test_generates_correct_pullback_short_candidate():
    result = generate_candidates(
        [
            _market_data(
                ticker="META",
                price=99.0,
                prev_price=98.5,
                ema9=98.0,
                ema21=100.0,
                ema50=102.0,
            )
        ],
        _context(),
    )
    assert result == [
        TradeCandidate(
            ticker="META",
            direction="short",
            entry_price=99.0,
            stop_price=101.0,
            target_price=95.0,
            ema9=98.0,
            ema21=100.0,
            ema50=102.0,
            atr14=2.0,
            structure="pullback",
        )
    ]


def test_generates_correct_reversal_long_candidate():
    result = generate_candidates(
        [
            _market_data(
                ticker="AMZN",
                price=101.0,
                prev_price=97.0,
                ema9=99.0,
                ema21=98.0,
                ema50=100.0,
            )
        ],
        _context(),
    )
    assert result == [
        TradeCandidate(
            ticker="AMZN",
            direction="long",
            entry_price=101.0,
            stop_price=98.0,
            target_price=107.0,
            ema9=99.0,
            ema21=98.0,
            ema50=100.0,
            atr14=2.0,
            structure="reversal",
        )
    ]


def test_generates_correct_reversal_short_candidate():
    result = generate_candidates(
        [
            _market_data(
                ticker="MSFT",
                price=99.0,
                prev_price=103.0,
                ema9=101.0,
                ema21=102.0,
                ema50=100.0,
            )
        ],
        _context(),
    )
    assert result == [
        TradeCandidate(
            ticker="MSFT",
            direction="short",
            entry_price=99.0,
            stop_price=102.0,
            target_price=93.0,
            ema9=101.0,
            ema21=102.0,
            ema50=100.0,
            atr14=2.0,
            structure="reversal",
        )
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("price", 0.0),
        ("prev_price", 0.0),
        ("atr14", 0.0),
        ("volume", 499_999.0),
    ],
)
def test_rejects_tickers_that_fail_pre_filter(field: str, value: float):
    assert generate_candidates([_market_data(**{field: value})], _context()) == []


def test_rejects_candidates_that_fail_sanity_check():
    result = generate_candidates(
        [
            _market_data(
                ticker="QQQ",
                price=103.0,
                prev_price=101.0,
                ema9=102.0,
                ema21=102.1,
                ema50=98.0,
                atr14=2.0,
            )
        ],
        _context(),
    )
    assert result == []


def test_deduplicates_so_breakout_beats_pullback_for_same_ticker():
    result = generate_candidates(
        [_market_data(ticker="SPY", price=102.0, prev_price=100.0, ema9=101.0)],
        _context(),
    )
    assert len(result) == 1
    assert result[0].ticker == "SPY"
    assert result[0].structure == "breakout"


def test_deduplicates_so_long_beats_short_at_equal_structure_priority():
    long_candidate = TradeCandidate(
        ticker="DUAL",
        direction="long",
        entry_price=101.0,
        stop_price=99.0,
        target_price=105.0,
        ema9=100.0,
        ema21=99.0,
        ema50=98.0,
        atr14=2.0,
        structure="reversal",
    )
    short_candidate = TradeCandidate(
        ticker="DUAL",
        direction="short",
        entry_price=99.0,
        stop_price=101.0,
        target_price=95.0,
        ema9=100.0,
        ema21=101.0,
        ema50=100.0,
        atr14=2.0,
        structure="reversal",
    )

    from cuttingboard.signals.scanner import _select_candidate

    assert _select_candidate([short_candidate, long_candidate]) == long_candidate


def test_returns_empty_list_when_no_signals_match():
    result = generate_candidates(
        [
            _market_data(
                price=100.0,
                prev_price=100.5,
                ema9=102.0,
                ema21=101.0,
                ema50=99.0,
            )
        ],
        _context(),
    )
    assert result == []


def test_produces_identical_output_for_identical_input():
    market_data = [
        _market_data(ticker="AAPL"),
        _market_data(
            ticker="TSLA",
            price=97.0,
            prev_price=99.0,
            ema9=98.0,
            ema21=100.0,
            ema50=102.0,
        ),
    ]
    context = _context()
    assert generate_candidates(market_data, context) == generate_candidates(
        market_data,
        context,
    )


def test_raises_value_error_on_non_finite_numeric_fields():
    with pytest.raises(ValueError):
        generate_candidates([_market_data(price=float("nan"))], _context())


@dataclass
class IncompleteMarketData:
    ticker: str = "AAPL"
    price: float = 103.0
    prev_price: float = 101.0
    ema9: float = 102.0
    ema21: float = 100.0
    ema50: float = 98.0
    atr14: float = 2.0


def test_raises_value_error_on_missing_required_fields():
    with pytest.raises(ValueError):
        generate_candidates([IncompleteMarketData()], _context())


@pytest.mark.parametrize(
    "context",
    [
        _context(timestamp=datetime(2026, 4, 13, 14, 30)),
        _context(
            timestamp=datetime(2026, 4, 13, 7, 30, tzinfo=timezone.utc).astimezone()
        ),
        _context(timeframe="30m"),
        _context(session_type="overnight"),
    ],
)
def test_raises_value_error_on_invalid_scan_context(context: ScanContext):
    with pytest.raises(ValueError):
        generate_candidates([_market_data()], context)
