"""
Phase 2 tests — derived metrics.

All tests are offline: a synthetic OHLCV DataFrame is injected directly.
No network calls are made.
"""

import math
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from cuttingboard.normalization import NormalizedQuote
from cuttingboard.derived import DerivedMetrics, compute_derived, compute_all_derived


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int = 60, base_price: float = 100.0, trend: float = 0.0) -> pd.DataFrame:
    """Generate a synthetic daily OHLCV DataFrame with n bars.

    trend: daily additive drift per bar (e.g. 0.5 means price rises 0.5/day).
    """
    rng = np.random.default_rng(seed=42)
    closes = base_price + trend * np.arange(n) + rng.normal(0, 0.5, n).cumsum()
    highs  = closes + rng.uniform(0.1, 1.0, n)
    lows   = closes - rng.uniform(0.1, 1.0, n)
    opens  = closes - rng.uniform(-0.5, 0.5, n)
    vols   = rng.integers(1_000_000, 5_000_000, n).astype(float)

    idx = pd.date_range(start="2020-01-02", periods=n, freq="B")
    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": vols},
        index=idx,
    )


def _make_quote(symbol: str = "SPY", price: float = 100.0) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=price,
        pct_change_decimal=0.005,
        volume=2_000_000.0,
        fetched_at_utc=datetime.now(timezone.utc),
        source="yfinance",
        units="usd_price",
        age_seconds=5.0,
    )


# ---------------------------------------------------------------------------
# EMA tests
# ---------------------------------------------------------------------------

class TestEMA:
    def test_ema_values_are_floats(self):
        df = _make_ohlcv(60)
        quote = _make_quote(price=float(df["Close"].iloc[-1]))
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert isinstance(dm.ema9,  float)
        assert isinstance(dm.ema21, float)
        assert isinstance(dm.ema50, float)

    def test_ema_ordering_bull(self):
        # Strongly uptrending series: EMA9 > EMA21 > EMA50
        df = _make_ohlcv(120, base_price=100.0, trend=1.0)
        quote = _make_quote(price=float(df["Close"].iloc[-1]))
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert dm.ema9 > dm.ema21 > dm.ema50
        assert dm.ema_aligned_bull is True
        assert dm.ema_aligned_bear is False

    def test_ema_ordering_bear(self):
        # Strongly downtrending series: EMA9 < EMA21 < EMA50
        df = _make_ohlcv(120, base_price=200.0, trend=-1.0)
        quote = _make_quote(price=float(df["Close"].iloc[-1]))
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert dm.ema9 < dm.ema21 < dm.ema50
        assert dm.ema_aligned_bear is True
        assert dm.ema_aligned_bull is False

    def test_ema_spread_pct_sign_matches_ordering(self):
        # Bull trend → ema9 > ema21 → spread positive
        df = _make_ohlcv(120, base_price=100.0, trend=1.0)
        quote = _make_quote(price=float(df["Close"].iloc[-1]))
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert dm.ema_spread_pct is not None
        assert dm.ema_spread_pct > 0

    def test_ema_spread_pct_formula(self):
        df = _make_ohlcv(60)
        quote = _make_quote(price=float(df["Close"].iloc[-1]))
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        if dm.ema9 is not None and dm.ema21 is not None:
            expected = (dm.ema9 - dm.ema21) / dm.ema21
            assert dm.ema_spread_pct == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# ATR tests
# ---------------------------------------------------------------------------

class TestATR:
    def test_atr_is_positive(self):
        df = _make_ohlcv(60)
        quote = _make_quote(price=float(df["Close"].iloc[-1]))
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert dm.atr14 is not None
        assert dm.atr14 > 0

    def test_atr_pct_formula(self):
        df = _make_ohlcv(60, base_price=500.0)
        price = float(df["Close"].iloc[-1])
        quote = _make_quote(price=price)
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        if dm.atr14 is not None:
            expected = dm.atr14 / price
            assert dm.atr_pct == pytest.approx(expected, rel=1e-6)

    def test_atr_uses_true_range_not_just_hl(self):
        # Construct a gap-open scenario where |H-PrevC| > H-L
        n = 30
        idx = pd.date_range(start="2020-01-02", periods=n, freq="B")
        closes = np.full(n, 100.0)
        closes[-1] = 110.0      # gap up on last bar
        highs  = closes + 0.5
        lows   = closes - 0.5
        opens  = closes.copy()
        vols   = np.full(n, 1_000_000.0)
        df = pd.DataFrame(
            {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": vols},
            index=idx,
        )
        quote = _make_quote(price=110.0)
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        # ATR14 should reflect the gap, not just the narrow H-L bars
        assert dm.atr14 is not None
        assert dm.atr14 > 0.5   # pure H-L would give ~0.5; gap should inflate it


# ---------------------------------------------------------------------------
# Momentum tests
# ---------------------------------------------------------------------------

class TestMomentum:
    def test_momentum_5d_sign_up(self):
        df = _make_ohlcv(30, base_price=100.0, trend=1.0)
        quote = _make_quote(price=float(df["Close"].iloc[-1]))
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert dm.momentum_5d is not None
        assert dm.momentum_5d > 0

    def test_momentum_5d_known_value(self):
        # Flat series, last bar +10%
        n = 30
        idx = pd.date_range(start="2020-01-02", periods=n, freq="B")
        closes = np.full(n, 200.0)
        closes[-1] = 220.0  # +10% vs close[-6] which is 200.0
        df = pd.DataFrame({
            "Open": closes, "High": closes + 1, "Low": closes - 1,
            "Close": closes, "Volume": np.full(n, 1_000_000.0),
        }, index=idx)
        quote = _make_quote(price=220.0)
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert dm.momentum_5d == pytest.approx(0.10, rel=1e-6)


# ---------------------------------------------------------------------------
# Volume ratio tests
# ---------------------------------------------------------------------------

class TestVolumeRatio:
    def test_volume_ratio_above_one_high_volume(self):
        n = 30
        idx = pd.date_range(start="2020-01-02", periods=n, freq="B")
        closes = np.full(n, 100.0)
        vols = np.full(n, 1_000_000.0)
        vols[-1] = 3_000_000.0   # today 3× avg
        df = pd.DataFrame({
            "Open": closes, "High": closes + 1, "Low": closes - 1,
            "Close": closes, "Volume": vols,
        }, index=idx)
        quote = _make_quote(price=100.0)
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert dm.volume_ratio is not None
        assert dm.volume_ratio == pytest.approx(3.0, rel=0.05)

    def test_volume_ratio_below_one_low_volume(self):
        n = 30
        idx = pd.date_range(start="2020-01-02", periods=n, freq="B")
        closes = np.full(n, 100.0)
        vols = np.full(n, 2_000_000.0)
        vols[-1] = 500_000.0    # today 0.25× avg
        df = pd.DataFrame({
            "Open": closes, "High": closes + 1, "Low": closes - 1,
            "Close": closes, "Volume": vols,
        }, index=idx)
        quote = _make_quote(price=100.0)
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert dm.volume_ratio is not None
        assert dm.volume_ratio == pytest.approx(0.25, rel=0.05)


# ---------------------------------------------------------------------------
# Insufficient history tests
# ---------------------------------------------------------------------------

class TestInsufficientHistory:
    def test_fewer_than_21_bars_returns_insufficient(self):
        df = _make_ohlcv(10)  # below OHLCV_MIN_BARS=21
        quote = _make_quote(price=100.0)
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert dm.sufficient_history is False
        assert dm.ema9 is None
        assert dm.ema21 is None
        assert dm.ema50 is None
        assert dm.atr14 is None
        assert dm.atr_pct is None
        assert dm.momentum_5d is None
        assert dm.volume_ratio is None
        assert dm.ema_aligned_bull is False
        assert dm.ema_aligned_bear is False

    def test_none_ohlcv_returns_insufficient(self):
        quote = _make_quote(price=100.0)
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=None):
            dm = compute_derived("SPY", quote)
        assert dm.sufficient_history is False
        assert dm.ema9 is None

    def test_exactly_21_bars_is_sufficient(self):
        df = _make_ohlcv(21)
        quote = _make_quote(price=float(df["Close"].iloc[-1]))
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert dm.sufficient_history is True
        assert dm.ema9 is not None


# ---------------------------------------------------------------------------
# compute_all_derived tests
# ---------------------------------------------------------------------------

class TestComputeAll:
    def test_output_keys_match_input(self):
        df = _make_ohlcv(60)
        quotes = {
            "SPY": _make_quote("SPY", price=float(df["Close"].iloc[-1])),
            "QQQ": _make_quote("QQQ", price=float(df["Close"].iloc[-1])),
        }
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            results = compute_all_derived(quotes)
        assert set(results.keys()) == {"SPY", "QQQ"}

    def test_all_results_are_derived_metrics(self):
        df = _make_ohlcv(60)
        quotes = {"SPY": _make_quote("SPY", price=float(df["Close"].iloc[-1]))}
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            results = compute_all_derived(quotes)
        assert isinstance(results["SPY"], DerivedMetrics)

    def test_compute_all_alias(self):
        from cuttingboard.derived import compute_all, compute_all_derived
        assert compute_all is compute_all_derived

    def test_computed_at_utc_is_aware(self):
        df = _make_ohlcv(60)
        quote = _make_quote(price=float(df["Close"].iloc[-1]))
        with patch("cuttingboard.derived.fetch_ohlcv", return_value=df):
            dm = compute_derived("SPY", quote)
        assert dm.computed_at_utc.tzinfo is not None
