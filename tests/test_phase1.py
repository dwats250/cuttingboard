"""
Phase 1 tests — config, ingestion, normalization, validation.

Run with: pytest tests/test_phase1.py -v
"""

import math
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest

from cuttingboard import config
from cuttingboard.ingestion import RawQuote
from cuttingboard.normalization import NormalizedQuote, normalize_quote, normalize_quotes
from cuttingboard.validation import (
    SymbolValidation,
    ValidationSummary,
    validate_quotes,
    extract_fetch_failures,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _raw_quote(
    symbol="SPY",
    price=540.0,
    pct_change_raw=0.005,
    volume=50_000_000.0,
    source="yfinance",
    fetch_succeeded=True,
    failure_reason=None,
    age_offset_seconds=0,
) -> RawQuote:
    return RawQuote(
        symbol=symbol,
        price=price,
        pct_change_raw=pct_change_raw,
        volume=volume,
        fetched_at_utc=datetime.now(timezone.utc) - timedelta(seconds=age_offset_seconds),
        source=source,
        fetch_succeeded=fetch_succeeded,
        failure_reason=failure_reason,
    )


def _normalized(
    symbol="SPY",
    price=540.0,
    pct_change_decimal=0.005,
    age_seconds=10.0,
    units="usd_price",
) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=price,
        pct_change_decimal=pct_change_decimal,
        volume=50_000_000.0,
        fetched_at_utc=datetime.now(timezone.utc) - timedelta(seconds=age_seconds),
        source="yfinance",
        units=units,
        age_seconds=age_seconds,
    )


# ---------------------------------------------------------------------------
# config tests
# ---------------------------------------------------------------------------

class TestConfig:
    def test_halt_symbols_present(self):
        assert "^VIX" in config.HALT_SYMBOLS
        assert "DX-Y.NYB" in config.HALT_SYMBOLS
        assert "^TNX" in config.HALT_SYMBOLS
        assert "SPY" in config.HALT_SYMBOLS
        assert "QQQ" in config.HALT_SYMBOLS

    def test_all_symbols_count(self):
        assert len(config.ALL_SYMBOLS) == 20

    def test_required_symbols_subset_of_halt(self):
        for s in config.HALT_SYMBOLS:
            assert s in config.ALL_SYMBOLS

    def test_price_bounds_cover_halt_symbols(self):
        for symbol in config.HALT_SYMBOLS:
            assert symbol in config.PRICE_BOUNDS, f"{symbol} missing from PRICE_BOUNDS"

    def test_price_bounds_lo_lt_hi(self):
        for symbol, (lo, hi) in config.PRICE_BOUNDS.items():
            assert lo < hi, f"{symbol}: lo={lo} >= hi={hi}"

    def test_symbol_units(self):
        assert config.SYMBOL_UNITS["^VIX"] == "index_level"
        assert config.SYMBOL_UNITS["DX-Y.NYB"] == "index_level"
        assert config.SYMBOL_UNITS["^TNX"] == "yield_pct"

    def test_source_priority_yfinance_only_symbols(self):
        for s in ["^VIX", "DX-Y.NYB", "^TNX", "BTC-USD"]:
            assert config.SYMBOL_SOURCE_PRIORITY[s] == ["yfinance"]

    def test_freshness_seconds(self):
        assert config.FRESHNESS_SECONDS == 300

    def test_max_clock_skew_seconds(self):
        assert config.MAX_CLOCK_SKEW_SECONDS == 5

    def test_polygon_url_template(self):
        url = config.POLYGON_PREV_URL.format(symbol="SPY")
        assert "SPY" in url
        assert "api.polygon.io" in url


# ---------------------------------------------------------------------------
# normalization tests
# ---------------------------------------------------------------------------

class TestNormalization:
    def test_normalize_successful_quote(self):
        raw = _raw_quote(symbol="SPY", price=540.0, pct_change_raw=0.012)
        nq = normalize_quote(raw)
        assert nq is not None
        assert nq.symbol == "SPY"
        assert nq.price == 540.0
        assert nq.pct_change_decimal == pytest.approx(0.012)
        assert nq.units == "usd_price"
        assert nq.fetched_at_utc.tzinfo is not None

    def test_normalize_skips_failed_quote(self):
        raw = _raw_quote(fetch_succeeded=False, failure_reason="timeout")
        result = normalize_quote(raw)
        assert result is None

    def test_vix_gets_index_level_units(self):
        raw = _raw_quote(symbol="^VIX", price=18.5, pct_change_raw=-0.02)
        nq = normalize_quote(raw)
        assert nq.units == "index_level"

    def test_tnx_gets_yield_pct_units(self):
        raw = _raw_quote(symbol="^TNX", price=4.31, pct_change_raw=-0.003)
        nq = normalize_quote(raw)
        assert nq.units == "yield_pct"

    def test_dxy_gets_index_level_units(self):
        raw = _raw_quote(symbol="DX-Y.NYB", price=104.5, pct_change_raw=-0.001)
        nq = normalize_quote(raw)
        assert nq.units == "index_level"

    def test_pct_change_large_value_corrected(self):
        # Simulate a source that incorrectly returns percentage format
        raw = _raw_quote(pct_change_raw=5.2)   # should become 0.052
        nq = normalize_quote(raw)
        assert nq.pct_change_decimal == pytest.approx(0.052)

    def test_pct_change_decimal_passthrough(self):
        raw = _raw_quote(pct_change_raw=0.052)
        nq = normalize_quote(raw)
        assert nq.pct_change_decimal == pytest.approx(0.052)

    def test_naive_datetime_gets_utc(self):
        naive_dt = datetime(2026, 4, 10, 13, 0, 0)  # no tzinfo
        raw = RawQuote(
            symbol="SPY", price=540.0, pct_change_raw=0.005,
            volume=None, fetched_at_utc=naive_dt,
            source="yfinance", fetch_succeeded=True, failure_reason=None,
        )
        nq = normalize_quote(raw)
        assert nq.fetched_at_utc.tzinfo is not None

    def test_age_seconds_is_positive(self):
        raw = _raw_quote(age_offset_seconds=30)
        nq = normalize_quote(raw)
        assert nq.age_seconds >= 30

    def test_normalize_quotes_filters_failures(self):
        raw_quotes = {
            "SPY": _raw_quote("SPY", fetch_succeeded=True),
            "QQQ": _raw_quote("QQQ", fetch_succeeded=False, failure_reason="timeout"),
        }
        result = normalize_quotes(raw_quotes)
        assert "SPY" in result
        assert "QQQ" not in result


# ---------------------------------------------------------------------------
# validation tests
# ---------------------------------------------------------------------------

class TestValidation:
    def _all_halt_symbols_valid(self, **overrides) -> dict[str, NormalizedQuote]:
        """Return a dict of all HALT_SYMBOLS with valid quotes, optionally overriding."""
        base = {
            "^VIX":     _normalized("^VIX",     price=18.5,  age_seconds=10, units="index_level"),
            "DX-Y.NYB": _normalized("DX-Y.NYB", price=104.0, age_seconds=10, units="index_level"),
            "^TNX":     _normalized("^TNX",     price=4.3,   age_seconds=10, units="yield_pct"),
            "SPY":      _normalized("SPY",      price=540.0, age_seconds=10),
            "QQQ":      _normalized("QQQ",      price=450.0, age_seconds=10),
        }
        base.update(overrides)
        return base

    def test_valid_quote_passes(self):
        nqs = self._all_halt_symbols_valid()
        summary = validate_quotes(nqs)
        assert not summary.system_halted
        assert "SPY" in summary.valid_quotes

    def test_stale_quote_fails(self):
        nq = _normalized("SPY", price=540.0, age_seconds=400)  # > 300s threshold
        summary = validate_quotes({"SPY": nq})
        assert "SPY" not in summary.valid_quotes
        assert "SPY" in summary.invalid_symbols

    def test_future_quote_beyond_clock_skew_fails(self):
        nq = _normalized("SPY", price=540.0, age_seconds=-10)
        summary = validate_quotes({"SPY": nq})
        assert "SPY" not in summary.valid_quotes
        assert "future" in summary.invalid_symbols["SPY"]

    def test_future_halt_symbol_halts_system(self):
        all_halt = self._all_halt_symbols_valid(
            **{"^VIX": _normalized("^VIX", price=18.5, age_seconds=-10, units="index_level")}
        )
        summary = validate_quotes(all_halt)
        assert summary.system_halted
        assert "^VIX" in summary.failed_halt_symbols

    def test_price_out_of_bounds_fails(self):
        nq = _normalized("SPY", price=100.0, age_seconds=10)  # SPY min is 300
        summary = validate_quotes({"SPY": nq})
        assert "SPY" not in summary.valid_quotes
        reason = summary.invalid_symbols["SPY"]
        assert "bounds" in reason

    def test_extreme_pct_change_fails(self):
        nq = _normalized("SPY", price=540.0, pct_change_decimal=0.30, age_seconds=10)
        summary = validate_quotes({"SPY": nq})
        assert "SPY" not in summary.valid_quotes
        assert "suspect" in summary.invalid_symbols["SPY"]

    def test_nan_price_fails(self):
        nq = NormalizedQuote(
            symbol="SPY", price=float("nan"), pct_change_decimal=0.005,
            volume=None, fetched_at_utc=datetime.now(timezone.utc),
            source="yfinance", units="usd_price", age_seconds=10.0,
        )
        summary = validate_quotes({"SPY": nq})
        assert "SPY" not in summary.valid_quotes

    def test_system_halts_when_vix_fails(self):
        nqs = {
            symbol: _normalized(symbol, price=mid, age_seconds=10)
            for symbol, mid in [
                ("SPY", 540.0), ("QQQ", 450.0), ("^TNX", 4.3),
                ("DX-Y.NYB", 104.0), ("BTC-USD", 83000.0),
            ]
        }
        # VIX is absent — it will be treated as a fetch failure
        summary = validate_quotes(nqs, fetch_failures={"^VIX": "timeout after 10s"})
        assert summary.system_halted
        assert "^VIX" in summary.failed_halt_symbols

    def test_system_halts_when_halt_symbol_stale(self):
        # All halt symbols present but VIX is stale
        all_halt = {
            "^VIX":     _normalized("^VIX",     price=18.5, age_seconds=400),  # stale
            "DX-Y.NYB": _normalized("DX-Y.NYB", price=104.0, age_seconds=10),
            "^TNX":     _normalized("^TNX",     price=4.3,  age_seconds=10),
            "SPY":      _normalized("SPY",      price=540.0, age_seconds=10),
            "QQQ":      _normalized("QQQ",      price=450.0, age_seconds=10),
        }
        summary = validate_quotes(all_halt)
        assert summary.system_halted
        assert "^VIX" in summary.failed_halt_symbols

    def test_no_halt_when_all_halt_symbols_valid(self):
        nqs = {
            "^VIX":     _normalized("^VIX",     price=18.5,   age_seconds=10, units="index_level"),
            "DX-Y.NYB": _normalized("DX-Y.NYB", price=104.0,  age_seconds=10, units="index_level"),
            "^TNX":     _normalized("^TNX",     price=4.3,    age_seconds=10, units="yield_pct"),
            "SPY":      _normalized("SPY",      price=540.0,  age_seconds=10),
            "QQQ":      _normalized("QQQ",      price=450.0,  age_seconds=10),
        }
        summary = validate_quotes(nqs)
        assert not summary.system_halted
        assert summary.failed_halt_symbols == []

    def test_optional_symbol_failure_does_not_halt(self):
        # NVDA fails validation but it is not a halt symbol
        nqs = {
            "^VIX":     _normalized("^VIX",     price=18.5,  age_seconds=10, units="index_level"),
            "DX-Y.NYB": _normalized("DX-Y.NYB", price=104.0, age_seconds=10, units="index_level"),
            "^TNX":     _normalized("^TNX",     price=4.3,   age_seconds=10, units="yield_pct"),
            "SPY":      _normalized("SPY",      price=540.0, age_seconds=10),
            "QQQ":      _normalized("QQQ",      price=450.0, age_seconds=10),
            "NVDA":     _normalized("NVDA",     price=99999.0, age_seconds=10),  # out of bounds
        }
        summary = validate_quotes(nqs)
        assert not summary.system_halted
        assert "NVDA" in summary.invalid_symbols

    def test_extract_fetch_failures(self):
        raw_quotes = {
            "SPY": _raw_quote("SPY", fetch_succeeded=True),
            "QQQ": _raw_quote("QQQ", fetch_succeeded=False, failure_reason="timeout"),
            "^VIX": _raw_quote("^VIX", fetch_succeeded=False, failure_reason="NaN price"),
        }
        failures = extract_fetch_failures(raw_quotes)
        assert "SPY" not in failures
        assert failures["QQQ"] == "timeout"
        assert failures["^VIX"] == "NaN price"

    def test_summary_counts(self):
        nqs = {
            "^VIX":     _normalized("^VIX",     price=18.5,  age_seconds=10, units="index_level"),
            "DX-Y.NYB": _normalized("DX-Y.NYB", price=104.0, age_seconds=10, units="index_level"),
            "^TNX":     _normalized("^TNX",     price=4.3,   age_seconds=10, units="yield_pct"),
            "SPY":      _normalized("SPY",      price=540.0, age_seconds=10),
            "QQQ":      _normalized("QQQ",      price=450.0, age_seconds=10),
            "NVDA":     _normalized("NVDA",     price=400.0, age_seconds=10),
        }
        fetch_failures = {"TSLA": "timeout"}
        summary = validate_quotes(nqs, fetch_failures=fetch_failures)

        assert summary.symbols_attempted == 7  # 6 normalized + 1 fetch failure
        assert summary.symbols_validated == 6
        assert summary.symbols_failed == 1
