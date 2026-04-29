"""
Tests for Layer 6 — Structure Engine (cuttingboard/structure.py).
All tests are offline — inject synthetic DerivedMetrics, no network calls.
"""

from datetime import datetime, timezone

from cuttingboard.derived import DerivedMetrics
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.structure import (
    classify_structure,
    classify_all_structure,
    classify_iv_environment,
    StructureResult,
    TREND, PULLBACK, BREAKOUT, REVERSAL, CHOP,
    LOW_IV, NORMAL_IV, ELEVATED_IV, HIGH_IV,
    _BREAKOUT_MOMENTUM_MIN, _BREAKOUT_VOLUME_MIN,
    _REVERSAL_MOMENTUM_MIN,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc)


def _dm(
    symbol="TEST",
    ema9=110.0, ema21=105.0, ema50=100.0,
    ema_aligned_bull=True, ema_aligned_bear=False,
    ema_spread_pct=0.047,
    atr14=2.0, atr_pct=0.018,
    momentum_5d=0.01, volume_ratio=1.0,
    sufficient_history=True,
) -> DerivedMetrics:
    return DerivedMetrics(
        symbol=symbol,
        ema9=ema9, ema21=ema21, ema50=ema50,
        ema_aligned_bull=ema_aligned_bull,
        ema_aligned_bear=ema_aligned_bear,
        ema_spread_pct=ema_spread_pct,
        atr14=atr14, atr_pct=atr_pct,
        momentum_5d=momentum_5d,
        volume_ratio=volume_ratio,
        computed_at_utc=_NOW,
        sufficient_history=sufficient_history,
    )


def _quote(symbol="TEST", price=112.0) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=price,
        pct_change_decimal=0.005,
        volume=1_000_000,
        fetched_at_utc=_NOW,
        source="yfinance",
        units="USD",
        age_seconds=10.0,
    )


def _insufficient(symbol="TEST") -> DerivedMetrics:
    return DerivedMetrics(
        symbol=symbol,
        ema9=None, ema21=None, ema50=None,
        ema_aligned_bull=False, ema_aligned_bear=False,
        ema_spread_pct=None,
        atr14=None, atr_pct=None,
        momentum_5d=None, volume_ratio=None,
        computed_at_utc=_NOW,
        sufficient_history=False,
    )


# ---------------------------------------------------------------------------
# IV environment classification
# ---------------------------------------------------------------------------

class TestClassifyIvEnvironment:
    def test_none_returns_normal(self):
        assert classify_iv_environment(None) == NORMAL_IV

    def test_below_15_is_low(self):
        assert classify_iv_environment(14.9) == LOW_IV

    def test_exactly_15_is_normal(self):
        assert classify_iv_environment(15.0) == NORMAL_IV

    def test_between_15_and_20_is_normal(self):
        assert classify_iv_environment(17.5) == NORMAL_IV

    def test_exactly_20_is_elevated(self):
        assert classify_iv_environment(20.0) == ELEVATED_IV

    def test_between_20_and_28_is_elevated(self):
        assert classify_iv_environment(24.0) == ELEVATED_IV

    def test_exactly_28_is_elevated(self):
        assert classify_iv_environment(28.0) == ELEVATED_IV

    def test_above_28_is_high(self):
        assert classify_iv_environment(28.1) == HIGH_IV

    def test_very_high_vix(self):
        assert classify_iv_environment(45.0) == HIGH_IV


# ---------------------------------------------------------------------------
# CHOP — no metrics / insufficient history
# ---------------------------------------------------------------------------

class TestChopClassification:
    def test_none_dm_is_chop(self):
        r = classify_structure("X", _quote(), None)
        assert r.structure == CHOP
        assert not r.is_tradeable

    def test_insufficient_history_is_chop(self):
        r = classify_structure("X", _quote(), _insufficient())
        assert r.structure == CHOP
        assert not r.is_tradeable

    def test_chop_symbol_set_correctly(self):
        r = classify_structure("AAPL", _quote("AAPL"), None)
        assert r.symbol == "AAPL"

    def test_chop_has_disqualification_reason(self):
        r = classify_structure("X", _quote(), None)
        assert r.disqualification_reason is not None
        assert len(r.disqualification_reason) > 0

    def test_insufficient_history_reason(self):
        r = classify_structure("X", _quote(), _insufficient())
        assert "insufficient" in r.disqualification_reason.lower()

    def test_ema_missing_values_is_chop(self):
        # DM has sufficient_history=True but EMA values are None
        dm = DerivedMetrics(
            symbol="X", ema9=None, ema21=105.0, ema50=100.0,
            ema_aligned_bull=False, ema_aligned_bear=False,
            ema_spread_pct=None, atr14=2.0, atr_pct=0.018,
            momentum_5d=0.01, volume_ratio=1.0,
            computed_at_utc=_NOW, sufficient_history=True,
        )
        r = classify_structure("X", _quote(), dm)
        assert r.structure == CHOP


# ---------------------------------------------------------------------------
# BREAKOUT classification
# ---------------------------------------------------------------------------

class TestBreakoutClassification:
    def test_bullish_breakout(self):
        # strong upward momentum + volume + price above ema9
        dm = _dm(
            ema9=100.0, ema21=98.0, ema50=95.0,
            ema_aligned_bull=True, ema_aligned_bear=False,
            momentum_5d=_BREAKOUT_MOMENTUM_MIN + 0.01,
            volume_ratio=_BREAKOUT_VOLUME_MIN + 0.1,
            ema_spread_pct=0.02,
        )
        r = classify_structure("X", _quote(price=102.0), dm)
        assert r.structure == BREAKOUT
        assert r.is_tradeable

    def test_bearish_breakout(self):
        # strong downward momentum + volume + price below ema9
        dm = _dm(
            ema9=100.0, ema21=102.0, ema50=105.0,
            ema_aligned_bull=False, ema_aligned_bear=True,
            momentum_5d=-(_BREAKOUT_MOMENTUM_MIN + 0.01),
            volume_ratio=_BREAKOUT_VOLUME_MIN + 0.1,
            ema_spread_pct=-0.02,
        )
        r = classify_structure("X", _quote(price=98.0), dm)
        assert r.structure == BREAKOUT

    def test_breakout_requires_strict_volume(self):
        # volume_ratio == _BREAKOUT_VOLUME_MIN (not strictly greater) → not BREAKOUT
        dm = _dm(
            ema9=100.0, ema21=98.0, ema50=95.0,
            ema_aligned_bull=True, ema_aligned_bear=False,
            momentum_5d=_BREAKOUT_MOMENTUM_MIN + 0.01,
            volume_ratio=_BREAKOUT_VOLUME_MIN,  # exactly at boundary
            ema_spread_pct=0.02,
        )
        r = classify_structure("X", _quote(price=102.0), dm)
        assert r.structure != BREAKOUT

    def test_breakout_requires_strong_momentum(self):
        # momentum at boundary (not strictly greater) → not BREAKOUT
        dm = _dm(
            ema9=100.0, ema21=98.0, ema50=95.0,
            ema_aligned_bull=True, ema_aligned_bear=False,
            momentum_5d=_BREAKOUT_MOMENTUM_MIN,  # exactly at boundary
            volume_ratio=_BREAKOUT_VOLUME_MIN + 0.1,
            ema_spread_pct=0.02,
        )
        r = classify_structure("X", _quote(price=102.0), dm)
        assert r.structure != BREAKOUT

    def test_bullish_breakout_price_must_be_above_ema9(self):
        # price below ema9 for bull breakout → not BREAKOUT
        dm = _dm(
            ema9=100.0, ema21=98.0, ema50=95.0,
            ema_aligned_bull=True, ema_aligned_bear=False,
            momentum_5d=_BREAKOUT_MOMENTUM_MIN + 0.01,
            volume_ratio=_BREAKOUT_VOLUME_MIN + 0.1,
            ema_spread_pct=0.02,
        )
        r = classify_structure("X", _quote(price=99.0), dm)  # below ema9=100
        assert r.structure != BREAKOUT


# ---------------------------------------------------------------------------
# REVERSAL classification
# ---------------------------------------------------------------------------

class TestReversalClassification:
    def test_reversal_tight_spread_with_momentum(self):
        dm = _dm(
            ema9=100.0, ema21=100.1, ema50=95.0,
            ema_aligned_bull=False, ema_aligned_bear=False,
            ema_spread_pct=-0.001,  # tight spread, below _REVERSAL_SPREAD_MAX
            momentum_5d=_REVERSAL_MOMENTUM_MIN + 0.001,
            volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=100.0), dm)
        assert r.structure == REVERSAL
        assert r.is_tradeable

    def test_reversal_tight_spread_bearish_momentum(self):
        dm = _dm(
            ema9=100.0, ema21=100.1, ema50=95.0,
            ema_aligned_bull=False, ema_aligned_bear=False,
            ema_spread_pct=0.001,
            momentum_5d=-(_REVERSAL_MOMENTUM_MIN + 0.001),
            volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=100.0), dm)
        assert r.structure == REVERSAL

    def test_reversal_not_triggered_with_flat_momentum(self):
        dm = _dm(
            ema9=100.0, ema21=100.1, ema50=95.0,
            ema_aligned_bull=False, ema_aligned_bear=False,
            ema_spread_pct=0.001,
            momentum_5d=0.0,  # flat momentum
            volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=100.0), dm)
        assert r.structure != REVERSAL

    def test_reversal_not_triggered_with_wide_spread(self):
        dm = _dm(
            ema9=100.0, ema21=103.0, ema50=95.0,
            ema_aligned_bull=False, ema_aligned_bear=False,
            ema_spread_pct=-0.029,  # wide spread
            momentum_5d=_REVERSAL_MOMENTUM_MIN + 0.001,
            volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=100.0), dm)
        assert r.structure != REVERSAL


# ---------------------------------------------------------------------------
# TREND classification
# ---------------------------------------------------------------------------

class TestTrendClassification:
    def test_bull_trend_price_at_or_above_ema9(self):
        dm = _dm(
            ema9=100.0, ema21=95.0, ema50=90.0,
            ema_aligned_bull=True, ema_aligned_bear=False,
            ema_spread_pct=0.05,
            momentum_5d=0.01, volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=102.0), dm)
        assert r.structure == TREND

    def test_bull_trend_price_exactly_at_ema9(self):
        dm = _dm(
            ema9=100.0, ema21=95.0, ema50=90.0,
            ema_aligned_bull=True, ema_aligned_bear=False,
            ema_spread_pct=0.05,
            momentum_5d=0.01, volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=100.0), dm)  # price == ema9
        assert r.structure == TREND

    def test_bear_trend_price_at_or_below_ema9(self):
        dm = _dm(
            ema9=100.0, ema21=105.0, ema50=110.0,
            ema_aligned_bull=False, ema_aligned_bear=True,
            ema_spread_pct=-0.047,
            momentum_5d=-0.01, volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=98.0), dm)
        assert r.structure == TREND

    def test_bear_trend_price_exactly_at_ema9(self):
        dm = _dm(
            ema9=100.0, ema21=105.0, ema50=110.0,
            ema_aligned_bull=False, ema_aligned_bear=True,
            ema_spread_pct=-0.047,
            momentum_5d=-0.01, volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=100.0), dm)  # price == ema9
        assert r.structure == TREND


# ---------------------------------------------------------------------------
# PULLBACK classification
# ---------------------------------------------------------------------------

class TestPullbackClassification:
    def test_bull_pullback_price_between_ema9_and_ema21(self):
        dm = _dm(
            ema9=110.0, ema21=105.0, ema50=100.0,
            ema_aligned_bull=True, ema_aligned_bear=False,
            ema_spread_pct=0.047,
            momentum_5d=0.005, volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=107.0), dm)  # between ema9 and ema21
        assert r.structure == PULLBACK

    def test_bull_pullback_price_at_ema21(self):
        dm = _dm(
            ema9=110.0, ema21=105.0, ema50=100.0,
            ema_aligned_bull=True, ema_aligned_bear=False,
            ema_spread_pct=0.047,
            momentum_5d=0.005, volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=105.0), dm)  # price == ema21
        assert r.structure == PULLBACK

    def test_bear_pullback_price_between_ema9_and_ema21(self):
        dm = _dm(
            ema9=90.0, ema21=95.0, ema50=100.0,
            ema_aligned_bull=False, ema_aligned_bear=True,
            ema_spread_pct=-0.052,
            momentum_5d=-0.005, volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=93.0), dm)  # between ema9 and ema21
        assert r.structure == PULLBACK


# ---------------------------------------------------------------------------
# CHOP fallthrough in alignment-based zone
# ---------------------------------------------------------------------------

class TestChopFallthrough:
    def test_bull_aligned_price_below_ema21_is_chop(self):
        # Bull-aligned but price degraded below EMA21
        dm = _dm(
            ema9=110.0, ema21=105.0, ema50=100.0,
            ema_aligned_bull=True, ema_aligned_bear=False,
            ema_spread_pct=0.047,
            momentum_5d=0.005, volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=103.0), dm)  # below ema21=105
        assert r.structure == CHOP
        assert not r.is_tradeable

    def test_bear_aligned_price_above_ema21_is_chop(self):
        # Bear-aligned but price bounced above EMA21
        dm = _dm(
            ema9=90.0, ema21=95.0, ema50=100.0,
            ema_aligned_bull=False, ema_aligned_bear=True,
            ema_spread_pct=-0.052,
            momentum_5d=-0.005, volume_ratio=1.0,
        )
        r = classify_structure("X", _quote(price=97.0), dm)  # above ema21=95
        assert r.structure == CHOP

    def test_not_aligned_not_breakout_not_reversal_is_chop(self):
        # Neither bull nor bear aligned, no breakout/reversal conditions
        dm = _dm(
            ema9=100.0, ema21=100.5, ema50=99.0,
            ema_aligned_bull=False, ema_aligned_bear=False,
            ema_spread_pct=-0.005,
            momentum_5d=0.001, volume_ratio=0.8,
        )
        r = classify_structure("X", _quote(price=100.0), dm)
        assert r.structure == CHOP


# ---------------------------------------------------------------------------
# classify_structure — return type and IV passthrough
# ---------------------------------------------------------------------------

class TestClassifyStructureReturnType:
    def test_returns_structure_result(self):
        r = classify_structure("X", _quote(), _dm())
        assert isinstance(r, StructureResult)

    def test_iv_environment_from_vix_level(self):
        r = classify_structure("X", _quote(), _dm(), vix_level=12.0)
        assert r.iv_environment == LOW_IV

    def test_iv_environment_explicit_takes_precedence(self):
        # iv_environment arg overrides vix_level
        r = classify_structure("X", _quote(), _dm(), iv_environment=HIGH_IV, vix_level=12.0)
        assert r.iv_environment == HIGH_IV

    def test_no_disqualification_reason_when_tradeable(self):
        r = classify_structure("X", _quote(price=112.0), _dm())
        assert r.is_tradeable
        assert r.disqualification_reason is None


# ---------------------------------------------------------------------------
# classify_all_structure
# ---------------------------------------------------------------------------

class TestClassifyAllStructure:
    def test_all_symbols_in_result(self):
        quotes = {"A": _quote("A"), "B": _quote("B")}
        dm_map = {"A": _dm("A"), "B": _dm("B")}
        results = classify_all_structure(quotes, dm_map)
        assert set(results.keys()) == {"A", "B"}

    def test_missing_dm_is_chop(self):
        quotes = {"A": _quote("A")}
        dm_map: dict = {}  # A has no derived metrics
        results = classify_all_structure(quotes, dm_map)
        assert results["A"].structure == CHOP

    def test_vix_level_propagates_to_all(self):
        quotes = {"A": _quote("A"), "B": _quote("B")}
        dm_map = {"A": _dm("A"), "B": _dm("B")}
        results = classify_all_structure(quotes, dm_map, vix_level=14.0)
        assert results["A"].iv_environment == LOW_IV
        assert results["B"].iv_environment == LOW_IV

    def test_chop_symbol_is_not_tradeable(self):
        quotes = {"A": _quote("A")}
        dm_map = {"A": _insufficient("A")}
        results = classify_all_structure(quotes, dm_map)
        assert not results["A"].is_tradeable

    def test_empty_quotes(self):
        results = classify_all_structure({}, {})
        assert results == {}
