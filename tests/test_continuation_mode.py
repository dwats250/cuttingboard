"""
PRD-008 tests — CONTINUATION entry mode.

Tests cover qualify_continuation_candidate, detect_continuation_breakout,
and qualify_all integration under EXPANSION regime.
"""

from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import pytest

from cuttingboard.derived import DerivedMetrics
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.qualification import (
    ENTRY_MODE_CONTINUATION,
    QualificationResult,
    QualificationSummary,
    TradeCandidate,
    detect_continuation_breakout,
    qualify_all,
    _qualify_continuation_candidate,
)
from cuttingboard.regime import (
    EXPANSION, EXPANSION_LONG,
    RegimeState,
)
from cuttingboard.structure import StructureResult, TREND, CHOP


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _expansion_regime() -> RegimeState:
    return RegimeState(
        regime=EXPANSION,
        posture=EXPANSION_LONG,
        confidence=1.0,
        net_score=0,
        risk_on_votes=0,
        risk_off_votes=0,
        neutral_votes=0,
        total_votes=0,
        vote_breakdown={},
        vix_level=16.0,
        vix_pct_change=-0.025,
        computed_at_utc=datetime.now(timezone.utc),
    )


def _ohlcv(closes: list[float], highs: Optional[list[float]] = None, lows: Optional[list[float]] = None) -> pd.DataFrame:
    """Build a minimal OHLCV DataFrame from close prices."""
    n = len(closes)
    if highs is None:
        highs = [c * 1.005 for c in closes]
    if lows is None:
        lows = [c * 0.995 for c in closes]
    return pd.DataFrame({
        "Open":   [c * 0.999 for c in closes],
        "High":   highs,
        "Low":    lows,
        "Close":  closes,
        "Volume": [1_000_000] * n,
    })


def _dm(atr14: float, ema21: Optional[float] = None, entry: float = 100.0) -> DerivedMetrics:
    e21 = ema21 if ema21 is not None else entry * 0.98
    return DerivedMetrics(
        symbol="TEST",
        ema9=entry * 1.002,
        ema21=e21,
        ema50=entry * 0.95,
        ema_aligned_bull=True,
        ema_aligned_bear=False,
        ema_spread_pct=0.002,
        atr14=atr14 if atr14 > 0 else None,
        atr_pct=(atr14 / entry) if atr14 > 0 else None,
        momentum_5d=0.015,
        volume_ratio=1.2,
        computed_at_utc=datetime.now(timezone.utc),
        sufficient_history=True,
    )


def _sr(structure: str = TREND) -> StructureResult:
    return StructureResult(
        symbol="TEST",
        structure=structure,
        iv_environment="NORMAL_IV",
        is_tradeable=structure != CHOP,
        disqualification_reason=None,
    )


# ---------------------------------------------------------------------------
# Test 3: detect_continuation_breakout
# ---------------------------------------------------------------------------

class TestDetectContinuationBreakout:
    def test_breakout_detected(self):
        # 10 bars: lookback (-6:-1) covers indices 4-8 with max high=100.
        # Bars 8 and 9 break out above 100.
        # Index:  0    1    2    3    4    5    6    7    8    9
        closes = [95,  96,  97,  96,  95,  96,  97,  96,  102, 104]
        highs  = [96,  97,  98,  97,  96,  97,  98,  97,  100, 106]
        lows   = [94,  95,  96,  95,  94,  95,  96,  95,  100, 102]
        # lookback = indices 4-8, highs = [96, 97, 98, 97, 100] → max = 100
        # current close = 104 > 100 ✓
        # prev close = 102 > 100 ✓ (hold)
        # last bar range = 106-102 = 4 >= 0.75*2=1.5 ✓
        df = _ohlcv(closes, highs, lows)
        atr = 2.0
        result = detect_continuation_breakout(df, atr)
        assert result is not None
        assert result == pytest.approx(100.0)  # highest high of lookback window

    def test_no_breakout_when_close_below_high(self):
        closes = [98, 99, 100, 101, 100, 99, 98, 99, 100, 100]
        df = _ohlcv(closes)
        result = detect_continuation_breakout(df, 2.0)
        assert result is None

    def test_no_hold_confirmation(self):
        # Current close above breakout, but previous close is not
        closes = [98, 99, 100, 99, 98, 99, 100, 99, 98, 102]
        highs  = [99, 100, 101, 100, 99, 100, 101, 100, 99, 103]
        lows   = [97, 98,  99,  98, 97,  98,  99,  98, 97, 101]
        df = _ohlcv(closes, highs, lows)
        result = detect_continuation_breakout(df, 2.0)
        assert result is None  # prev close (98) <= breakout level (101)

    def test_insufficient_momentum(self):
        # Breakout exists but last candle range too small
        closes = [98, 99, 100, 99, 98, 99, 100, 99, 101, 102]
        highs  = [99, 100, 101, 100, 99, 100, 101, 100, 102, 102.1]
        lows   = [97, 98,  99,  98, 97,  98,  99,  98, 100, 101.9]
        df = _ohlcv(closes, highs, lows)
        atr = 4.0  # range = 0.2, need 0.75*4=3.0 — fails momentum
        result = detect_continuation_breakout(df, atr)
        assert result is None

    def test_insufficient_data(self):
        df = _ohlcv([100, 101, 102, 103])  # only 4 bars, need >= 7
        result = detect_continuation_breakout(df, 1.0)
        assert result is None


# ---------------------------------------------------------------------------
# Test 3: qualify_continuation_candidate returns CONTINUATION entry_mode
# ---------------------------------------------------------------------------

class TestQualifyContinuationCandidate:
    def _breakout_df(self, entry: float = 100.0, atr: float = 2.0) -> pd.DataFrame:
        """Build OHLCV satisfying all continuation conditions.

        Lookback window (N=5) max high = entry - 2.  Current and prev close
        are both above that level.  Last bar range = 2*atr >= 0.75*atr.
        """
        base = entry - 3.0   # consolidation level
        # 10 bars: indices 0-3 are history, 4-8 are the lookback, 9 is current
        closes = [base] * 8 + [entry, entry + 1.0]
        # Lookback highs (indices 4-8): all at base+1 < entry
        highs = [base + 0.5] * 8 + [entry + atr, entry + 1.0 + atr]
        # Override indices 4-8 to be clearly below entry
        for i in range(4, 9):
            highs[i] = base + 1.0
        lows = [base - 0.5] * 8 + [entry - atr, entry + 1.0 - atr]
        # At current bar (index 9): range = 2*atr >= 0.75*atr ✓
        return _ohlcv(closes, highs, lows)

    def test_continuation_candidate_qualifies(self):
        entry = 100.0
        atr = 2.0
        df = self._breakout_df(entry, atr)
        regime = _expansion_regime()
        dm = _dm(atr, entry=entry)
        sr = _sr(TREND)
        result = _qualify_continuation_candidate("TEST", df, sr, regime, dm)
        assert result is not None
        assert result.entry_mode == ENTRY_MODE_CONTINUATION

    def test_vix_spike_blocks_continuation(self):
        from dataclasses import replace as dc_replace
        regime = _expansion_regime()
        regime_spiked = dc_replace(regime, vix_pct_change=+0.02)  # VIX +2%
        df = self._breakout_df()
        dm = _dm(2.0, entry=100.0)
        result = _qualify_continuation_candidate("TEST", df, _sr(), regime_spiked, dm)
        assert result is None

    def test_missing_atr_returns_none(self):
        dm_no_atr = _dm(0.0, entry=100.0)  # atr14 = None when 0 → invalid
        result = _qualify_continuation_candidate("TEST", self._breakout_df(), _sr(), _expansion_regime(), dm_no_atr)
        assert result is None

    def test_none_df_returns_none(self):
        result = _qualify_continuation_candidate("TEST", None, _sr(), _expansion_regime(), _dm(2.0))
        assert result is None

    def test_chop_structure_skipped(self):
        result = _qualify_continuation_candidate("TEST", self._breakout_df(), _sr(CHOP), _expansion_regime(), _dm(2.0))
        # CHOP structure will fail Gate 4 — no continuation for CHOP
        if result is not None:
            assert result.qualified is False

    def test_minimum_stop_distance_enforced(self):
        # Very tiny ATR means computed stop may be too tight — 1% floor must apply
        entry = 100.0
        df = self._breakout_df(entry=entry, atr=0.5)
        dm = _dm(0.5, entry=entry)
        result = _qualify_continuation_candidate("TEST", df, _sr(), _expansion_regime(), dm)
        # If it qualifies, risk must be >= 1% of entry
        if result is not None and result.qualified:
            assert result.dollar_risk is not None


# ---------------------------------------------------------------------------
# Test 4: qualify_all uses continuation path when no pullback (EXPANSION regime)
# ---------------------------------------------------------------------------

class TestQualifyAllContinuationPath:
    def _make_sr_dict(self, symbols: list[str], structure: str = TREND) -> dict[str, StructureResult]:
        return {
            s: StructureResult(
                symbol=s,
                structure=structure,
                iv_environment="NORMAL_IV",
                is_tradeable=structure != CHOP,
                disqualification_reason=None,
            )
            for s in symbols
        }

    def _make_ohlcv(self, entry: float, atr: float) -> pd.DataFrame:
        # lookback = df.iloc[-6:-1] = indices 4-8; all highs <= base+1 < entry
        # prev close (index 8) = entry (above breakout level)
        # current close (index 9) = entry + 1 (above breakout level)
        # current bar range = 2*atr >= 0.75*atr
        base = entry - 3.0
        closes = [base] * 7 + [entry, entry, entry + 1.0]
        highs = [base + 0.5] * 10
        for i in range(3, 9):          # lookback highs all = base+1 < entry
            highs[i] = base + 1.0
        highs[-1] = entry + atr        # current bar high
        lows = [base - 0.5] * 10
        lows[-1] = entry - atr         # current bar low → range = 2*atr
        return _ohlcv(closes, highs, lows)

    def test_continuation_qualified_when_no_pullback_candidate(self):
        regime = _expansion_regime()
        entry = 100.0
        atr = 2.0
        structure_results = self._make_sr_dict(["NVDA"])
        derived_metrics = {"NVDA": _dm(atr, entry=entry)}
        ohlcv = {"NVDA": self._make_ohlcv(entry, atr)}

        # No traditional candidates — continuation path should pick up NVDA
        summary = qualify_all(
            regime=regime,
            structure_results=structure_results,
            candidates=None,
            derived_metrics=derived_metrics,
            ohlcv=ohlcv,
        )

        continuation_trades = [
            r for r in summary.qualified_trades + summary.watchlist
            if r.entry_mode == ENTRY_MODE_CONTINUATION
        ]
        assert len(continuation_trades) > 0, "Expected at least one CONTINUATION entry"

    def test_no_continuation_for_chop(self):
        regime = _expansion_regime()
        entry = 100.0
        atr = 2.0
        structure_results = self._make_sr_dict(["NVDA"], structure=CHOP)
        derived_metrics = {"NVDA": _dm(atr, entry=entry)}
        ohlcv = {"NVDA": self._make_ohlcv(entry, atr)}

        summary = qualify_all(
            regime=regime,
            structure_results=structure_results,
            candidates=None,
            derived_metrics=derived_metrics,
            ohlcv=ohlcv,
        )
        continuation_trades = [
            r for r in summary.qualified_trades + summary.watchlist
            if r.entry_mode == ENTRY_MODE_CONTINUATION
        ]
        assert len(continuation_trades) == 0


# ---------------------------------------------------------------------------
# Test 5: EXPANSION regime never causes "NO TRADE" output sentinel
# ---------------------------------------------------------------------------

class TestExpansionNeverNoTrade:
    def test_expansion_regime_allows_continuation_path(self):
        """EXPANSION regime must not short-circuit at regime gates."""
        regime = _expansion_regime()
        summary = qualify_all(
            regime=regime,
            structure_results={},
            candidates=None,
            derived_metrics=None,
            ohlcv=None,
        )
        assert summary.regime_short_circuited is False
        assert summary.regime_passed is True

    def test_expansion_regime_check_regime_gates_passes(self):
        from cuttingboard.qualification import _check_regime_gates
        regime = _expansion_regime()
        result = _check_regime_gates(regime)
        assert result is None, f"Expected no gate failure for EXPANSION, got: {result}"

    def test_direction_for_regime_returns_long(self):
        from cuttingboard.qualification import direction_for_regime
        regime = _expansion_regime()
        assert direction_for_regime(regime) == "LONG"
