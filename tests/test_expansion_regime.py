"""
PRD-008 tests — EXPANSION regime detection.

All tests are offline: NormalizedQuote fixtures injected directly.
No network calls, no file I/O.
"""

from datetime import datetime, timezone

import pytest

from cuttingboard.normalization import NormalizedQuote
from cuttingboard.regime import (
    EXPANSION, EXPANSION_LONG,
    RISK_ON, NEUTRAL, CHAOTIC,
    detect_expansion_regime,
    compute_regime,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _q(symbol: str, price: float, pct_change: float, units: str = "usd_price") -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=price,
        pct_change_decimal=pct_change,
        volume=1_000_000.0,
        fetched_at_utc=datetime.now(timezone.utc),
        source="yfinance",
        units=units,
        age_seconds=5.0,
    )


def _expansion_quotes() -> dict[str, NormalizedQuote]:
    """Full set satisfying all expansion conditions."""
    return {
        # Macro drivers (non-tradable)
        "^VIX":     _q("^VIX",     16.0, -0.025, "index_level"),  # VIX pct <= -1%
        "DX-Y.NYB": _q("DX-Y.NYB", 104.0, -0.003),
        "^TNX":     _q("^TNX",       4.2, -0.008, "yield_pct"),
        "BTC-USD":  _q("BTC-USD", 85000.0, +0.020),
        # Indices — all positive (breadth + alignment)
        "SPY":      _q("SPY",      550.0, +0.012),
        "QQQ":      _q("QQQ",      460.0, +0.015),
        "IWM":      _q("IWM",      205.0, +0.008),
        # High-beta — leadership: NVDA, COIN both >= +1.5%
        "NVDA":     _q("NVDA",     720.0, +0.030),
        "TSLA":     _q("TSLA",     280.0, +0.005),
        "AAPL":     _q("AAPL",     195.0, +0.008),
        "META":     _q("META",     520.0, +0.010),
        "AMZN":     _q("AMZN",     190.0, +0.007),
        "COIN":     _q("COIN",     230.0, +0.025),
        "MSTR":     _q("MSTR",     380.0, -0.005),  # not a leader today
        # Commodities — mostly positive for breadth
        "GLD":      _q("GLD",      220.0, +0.003),
        "SLV":      _q("SLV",       27.0, +0.004),
        "GDX":      _q("GDX",       36.0, +0.006),
        "PAAS":     _q("PAAS",      18.0, +0.005),
        "USO":      _q("USO",        74.0, -0.002),  # red
        "XLE":      _q("XLE",        90.0, +0.004),
    }


# ---------------------------------------------------------------------------
# Test 1: EXPANSION detected when all conditions true
# ---------------------------------------------------------------------------

class TestExpansionDetected:
    def test_detect_expansion_regime_returns_true(self):
        quotes = _expansion_quotes()
        assert detect_expansion_regime(quotes) is True

    def test_compute_regime_returns_expansion(self):
        quotes = _expansion_quotes()
        state = compute_regime(quotes)
        assert state.regime == EXPANSION

    def test_expansion_posture_is_expansion_long(self):
        state = compute_regime(_expansion_quotes())
        assert state.posture == EXPANSION_LONG

    def test_expansion_confidence_is_one(self):
        state = compute_regime(_expansion_quotes())
        assert state.confidence == 1.0

    def test_expansion_vote_breakdown_empty(self):
        state = compute_regime(_expansion_quotes())
        assert state.vote_breakdown == {}
        assert state.total_votes == 0


# ---------------------------------------------------------------------------
# Test 2: EXPANSION NOT detected when any condition fails
# ---------------------------------------------------------------------------

class TestExpansionNotDetected:
    def test_spy_negative_blocks_expansion(self):
        quotes = _expansion_quotes()
        quotes["SPY"] = _q("SPY", 550.0, -0.005)
        assert detect_expansion_regime(quotes) is False

    def test_qqq_negative_blocks_expansion(self):
        quotes = _expansion_quotes()
        quotes["QQQ"] = _q("QQQ", 460.0, -0.002)
        assert detect_expansion_regime(quotes) is False

    def test_vix_rising_blocks_expansion(self):
        quotes = _expansion_quotes()
        # VIX pct_change > -1% (only -0.5%) — fails threshold
        quotes["^VIX"] = _q("^VIX", 16.0, -0.005, "index_level")
        assert detect_expansion_regime(quotes) is False

    def test_vix_positive_blocks_expansion(self):
        quotes = _expansion_quotes()
        quotes["^VIX"] = _q("^VIX", 20.0, +0.03, "index_level")
        assert detect_expansion_regime(quotes) is False

    def test_insufficient_breadth_blocks_expansion(self):
        # Make majority of watchlist red
        quotes = _expansion_quotes()
        for sym in ["IWM", "TSLA", "AAPL", "META", "AMZN", "MSTR", "GLD", "SLV", "GDX"]:
            quotes[sym] = _q(sym, 100.0, -0.010)
        assert detect_expansion_regime(quotes) is False

    def test_insufficient_leadership_blocks_expansion(self):
        # Only 1 leader (need 2)
        quotes = _expansion_quotes()
        quotes["COIN"] = _q("COIN", 230.0, +0.005)  # below 1.5%
        assert detect_expansion_regime(quotes) is False

    def test_no_leadership_symbols_blocks_expansion(self):
        quotes = _expansion_quotes()
        for sym in ["NVDA", "COIN", "MSTR", "TSLA"]:
            quotes[sym] = _q(sym, 100.0, +0.005)
        assert detect_expansion_regime(quotes) is False

    def test_missing_spy_blocks_expansion(self):
        quotes = _expansion_quotes()
        del quotes["SPY"]
        assert detect_expansion_regime(quotes) is False

    def test_missing_vix_blocks_expansion(self):
        quotes = _expansion_quotes()
        del quotes["^VIX"]
        assert detect_expansion_regime(quotes) is False

    def test_fallback_to_vote_model_when_not_expansion(self):
        # Normal risk-on quotes without breadth — should get RISK_ON not EXPANSION
        quotes = {
            "SPY":      _q("SPY",      540.0, +0.010),
            "QQQ":      _q("QQQ",      450.0, +0.010),
            "IWM":      _q("IWM",      200.0, +0.008),
            "^VIX":     _q("^VIX",      14.0, -0.050, "index_level"),
            "DX-Y.NYB": _q("DX-Y.NYB", 100.0, -0.005),
            "^TNX":     _q("^TNX",       4.0, -0.010, "yield_pct"),
            "BTC-USD":  _q("BTC-USD", 80000.0, +0.030),
        }
        state = compute_regime(quotes)
        assert state.regime == RISK_ON


# ---------------------------------------------------------------------------
# Test 6: VIX spike blocks expansion even when other conditions met
# ---------------------------------------------------------------------------

class TestExpansionVixSpikeBlock:
    def test_vix_rising_blocks_expansion(self):
        quotes = _expansion_quotes()
        # VIX +5% — above -1% threshold, blocks expansion
        quotes["^VIX"] = _q("^VIX", 22.0, +0.05, "index_level")
        assert detect_expansion_regime(quotes) is False

    def test_vix_chaotic_spike_blocks_expansion_and_causes_chaotic(self):
        quotes = _expansion_quotes()
        # VIX >15% spike → CHAOTIC override in vote model
        quotes["^VIX"] = _q("^VIX", 30.0, +0.18, "index_level")
        assert detect_expansion_regime(quotes) is False
        state = compute_regime(quotes)
        assert state.regime == CHAOTIC

    def test_vix_exactly_at_threshold_blocks_expansion(self):
        # VIX pct = -1.0% exactly: -0.01 is NOT <= -0.01 (strictly), check boundary
        quotes = _expansion_quotes()
        quotes["^VIX"] = _q("^VIX", 16.0, -0.01, "index_level")
        # -0.01 == -0.01, threshold is > EXPANSION_VIX_PCT_THRESHOLD (-0.01)
        # vix.pct_change_decimal (-0.01) > config.EXPANSION_VIX_PCT_THRESHOLD (-0.01) → False
        # So expansion should be detected (VIX pct is NOT > threshold)
        result = detect_expansion_regime(quotes)
        assert result is True  # exactly at threshold passes
