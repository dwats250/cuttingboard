"""Tests for continuation qualification and audit behavior."""

from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import pytest

from cuttingboard.derived import DerivedMetrics
from cuttingboard.qualification import (
    ENTRY_MODE_CONTINUATION,
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


@pytest.fixture(autouse=True)
def _freeze_continuation_time(monkeypatch):
    monkeypatch.setattr("cuttingboard.qualification._is_late_session", lambda now_et=None: False)

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
    e21 = ema21 if ema21 is not None else entry * 0.995
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
        # PRD-259: lookback ends strictly BEFORE the hold candle —
        # 10 bars, hold_candles=1 → window = indices 3-7, max high = 101.
        # All bars valid OHLC (High >= Close).
        # Index:  0    1    2    3    4    5    6    7    8      9
        closes = [96,  97,  98,  98,  99,  100, 99,  98,  102,   104]
        highs  = [97,  98,  99,  99,  100, 101, 100, 99,  102.5, 105]
        lows   = [95,  96,  97,  97,  98,  99,  98,  97,  100.5, 101]
        # current close = 104 > 101 ✓ (hold candle at index 8 sits outside
        # the window, so its own high cannot raise the level it is tested
        # against)
        df = _ohlcv(closes, highs, lows)
        result = detect_continuation_breakout(df)
        assert result is not None
        assert result == pytest.approx(101.0)  # highest high of lookback window

    def test_no_breakout_when_close_below_high(self):
        closes = [98, 99, 100, 101, 100, 99, 98, 99, 100, 100]
        df = _ohlcv(closes)
        result = detect_continuation_breakout(df)
        assert result is None

    def test_breakout_helper_only_checks_breakout(self):
        # Current close above breakout, but previous close is not. Hold logic
        # is now evaluated in _qualify_continuation_candidate().
        closes = [98, 99, 100, 99, 98, 99, 100, 99, 98, 102]
        highs  = [99, 100, 101, 100, 99, 100, 101, 100, 99, 103]
        lows   = [97, 98,  99,  98, 97,  98,  99,  98, 97, 101]
        df = _ohlcv(closes, highs, lows)
        result = detect_continuation_breakout(df)
        assert result == pytest.approx(101.0)

    def test_insufficient_data(self):
        df = _ohlcv([100, 101, 102, 103])  # only 4 bars, need >= 7
        result = detect_continuation_breakout(df)
        assert result is None


# ---------------------------------------------------------------------------
# Test 3: qualify_continuation_candidate returns CONTINUATION entry_mode
# ---------------------------------------------------------------------------

class TestQualifyContinuationCandidate:
    def _tight_stop_df(self) -> pd.DataFrame:
        # Valid OHLC. Last bar: close=100.7, range=2.0 (>= 0.75×ATR14=0.75),
        # close_location = (100.7-99.2)/(101.2-99.2) = 0.75 — clears the R5
        # momentum-conviction floor while the strictly-prior breakout level
        # (100.5, indices 3-7) still leaves the stop too tight.
        return _ohlcv(
            closes=[100, 100.2, 100.4, 100.2, 100.1, 100.2, 100.3, 100.4, 100.6, 100.7],
            highs=[100.3, 100.5, 100.6, 100.4, 100.3, 100.4, 100.5, 100.5, 100.7, 101.2],
            lows=[99.8, 100.0, 100.2, 100.0, 99.9, 100.0, 100.1, 100.2, 100.4, 99.2],
        )

    def _breakout_df(self, entry: float = 100.0, atr: float = 2.0) -> pd.DataFrame:
        """Build valid-OHLC bars satisfying all continuation conditions.

        Strictly-prior lookback window (PRD-259: N=5 bars ending before the
        hold candle, indices 3-7) max high = entry - 2. The hold candle
        (index 8) and current bar (index 9) both close above that level with
        High >= Close on every bar. Last bar range = 2*atr >= 0.75*atr, and
        close sits at the top of that range (close_location = 0.75) to clear
        the R5 momentum-conviction floor. Risk = (entry+1) - (entry-2) = 3.0
        = 1.5*atr at the default atr=2.0 → RR exactly 2.0.
        """
        base = entry - 3.0   # consolidation level
        # 10 bars: indices 0-2 are history, 3-7 are the lookback, 8 is the
        # hold candle, 9 is current
        closes = [base] * 8 + [entry, entry + 1.0]
        highs = [base + 0.5] * 8 + [entry + 0.5, entry + 1.0 + 0.25 * (2 * atr)]
        # Lookback (indices 3-7): all highs at base+1 < entry
        for i in range(3, 8):
            highs[i] = base + 1.0
        lows = [base - 0.5] * 8 + [entry - atr, entry + 1.0 - 0.75 * (2 * atr)]
        # At current bar (index 9): range = 2*atr >= 0.75*atr; close_location
        # = (close-low)/(high-low) = 0.75.
        return _ohlcv(closes, highs, lows)

    def test_fixtures_are_valid_ohlc_prd259(self):
        # R2 backstop: every HOLD-relevant fixture in this file stays
        # physically possible (High >= max(Open, Close), Low <= min(Open,
        # Close)) — the pre-PRD-259 fixtures passed HOLD only via
        # impossible bars, so validity is asserted, not assumed.
        frames = [
            self._breakout_df(),
            self._tight_stop_df(),
            TestQualifyAllContinuationPath()._make_ohlcv(100.0, 2.0),
        ]
        for df in frames:
            ok = ((df["High"] >= df[["Open", "Close"]].max(axis=1))
                  & (df["Low"] <= df[["Open", "Close"]].min(axis=1))).all()
            assert bool(ok), f"invalid OHLC bar in fixture:\n{df}"

    def test_valid_ohlc_sequence_clears_hold_gate_prd259(self):
        # PRD-259 R1 proving test: every bar is a VALID OHLC bar
        # (High >= max(Open, Close), Low <= min(Open, Close)). Pre-PRD-259
        # the lookback window included the hold candle itself, so the OHLC
        # invariant High >= Close made NO_HOLD_CONFIRMATION certain for any
        # valid input — this test fails there by construction.
        # Corrected window = indices 3-7, max high = 101. Hold candle
        # (index 8) closes 102 above it with High 102.5; today (index 9)
        # closes 104: risk = 104 - 101 = 3.0 = 1.5×ATR14 → RR exactly 2.0.
        closes = [96, 97, 98, 98, 99, 100, 99, 98, 102, 104]
        highs = [97, 98, 99, 99, 100, 101, 100, 99, 102.5, 105]
        lows = [95, 96, 97, 97, 98, 99, 98, 97, 100.5, 101]
        df = _ohlcv(closes, highs, lows)
        assert bool(((df["High"] >= df[["Open", "Close"]].max(axis=1))
                     & (df["Low"] <= df[["Open", "Close"]].min(axis=1))).all())
        result = _qualify_continuation_candidate(
            "TEST", df, _sr(TREND), _expansion_regime(), _dm(2.0, entry=104.0)
        )
        assert result.qualified is True
        assert result.rejection_reason is None
        assert result.entry_mode == ENTRY_MODE_CONTINUATION

    def test_intermediate_hold_dip_rejects_at_h2_prd259_r7(self, monkeypatch):
        # PRD-259 R7 red test: with CONTINUATION_HOLD_CANDLES=2, EVERY
        # completed hold candle must close above the breakout level. Window
        # (10 bars, h=2) = indices 2-6, max high = 101. Oldest hold (index
        # 7) closes 102 above it; the INTERMEDIATE hold (index 8) dips to
        # 100.5 below it. Pre-R7 the gate checked only the oldest hold, so
        # this sequence qualified; it must reject NO_HOLD_CONFIRMATION.
        monkeypatch.setattr("cuttingboard.qualification.config.CONTINUATION_HOLD_CANDLES", 2)
        closes = [96, 97, 98, 99, 100, 99, 98, 102, 100.5, 104]
        highs = [97, 98, 99, 100, 101, 100, 99, 102.5, 101, 105]
        lows = [95, 96, 97, 98, 99, 98, 97, 100.5, 100, 101]
        df = _ohlcv(closes, highs, lows)
        result = _qualify_continuation_candidate(
            "TEST", df, _sr(TREND), _expansion_regime(), _dm(2.0, entry=104.0)
        )
        assert result.qualified is False
        assert result.rejection_reason == "NO_HOLD_CONFIRMATION"

    def test_all_holds_above_level_qualify_at_h2_prd259_r7(self, monkeypatch):
        # Companion positive case: both completed hold candles close above
        # the strictly-prior level (101) -> qualifies at h=2.
        monkeypatch.setattr("cuttingboard.qualification.config.CONTINUATION_HOLD_CANDLES", 2)
        closes = [96, 97, 98, 99, 100, 99, 98, 102, 102.5, 104]
        highs = [97, 98, 99, 100, 101, 100, 99, 102.5, 103, 105]
        lows = [95, 96, 97, 98, 99, 98, 97, 100.5, 101.5, 101]
        df = _ohlcv(closes, highs, lows)
        result = _qualify_continuation_candidate(
            "TEST", df, _sr(TREND), _expansion_regime(), _dm(2.0, entry=104.0)
        )
        assert result.qualified is True

    def test_minimum_length_boundary_detects_breakout_prd259(self):
        # Exactly n + 1 + hold_candles bars (7 at h=1): the window is the
        # first 5 bars, the hold candle and current bar sit outside it.
        closes = [96, 97, 98, 97, 96, 102, 104]
        highs = [97, 98, 99, 98, 97, 102.5, 105]
        lows = [95, 96, 97, 96, 95, 100.5, 101]
        df = _ohlcv(closes, highs, lows)
        assert detect_continuation_breakout(df) == pytest.approx(99.0)

    def test_continuation_candidate_qualifies(self):
        entry = 100.0
        atr = 2.0
        df = self._breakout_df(entry, atr)
        regime = _expansion_regime()
        dm = _dm(atr, entry=entry)
        sr = _sr(TREND)
        result = _qualify_continuation_candidate("TEST", df, sr, regime, dm)
        assert result.qualified is True
        assert result.rejection_reason is None
        assert result.entry_mode == ENTRY_MODE_CONTINUATION

    def test_vix_spike_blocks_continuation(self):
        from dataclasses import replace as dc_replace
        regime = _expansion_regime()
        regime_spiked = dc_replace(regime, vix_pct_change=+0.02)  # VIX +2%
        df = self._breakout_df()
        dm = _dm(2.0, entry=100.0)
        result = _qualify_continuation_candidate("TEST", df, _sr(), regime_spiked, dm)
        assert result.qualified is False
        assert result.rejection_reason == "VIX_BLOCKED"

    def test_missing_atr_returns_data_incomplete(self):
        dm_no_atr = _dm(0.0, entry=100.0)  # atr14 = None when 0 → invalid
        result = _qualify_continuation_candidate("TEST", self._breakout_df(), _sr(), _expansion_regime(), dm_no_atr)
        assert result.rejection_reason == "DATA_INCOMPLETE"

    def test_none_df_returns_data_incomplete(self):
        result = _qualify_continuation_candidate("TEST", None, _sr(), _expansion_regime(), _dm(2.0))
        assert result.rejection_reason == "DATA_INCOMPLETE"

    def test_chop_structure_skipped(self):
        result = _qualify_continuation_candidate("TEST", self._breakout_df(), _sr(CHOP), _expansion_regime(), _dm(2.0))
        assert result.qualified is True

    def test_minimum_stop_distance_rejects_tight_stop(self):
        df = self._tight_stop_df()
        dm = _dm(1.0, ema21=100.5, entry=100.0)
        result = _qualify_continuation_candidate("TEST", df, _sr(), _expansion_regime(), dm)
        assert result.rejection_reason == "STOP_TOO_TIGHT"

    def test_continuation_sizes_against_reconverged_budget_prd256(self):
        # PRD-256 R3: continuation-path sizing now reads MAX_RISK_PCT_PER_TRADE
        # on LIVE, unmocked config -- CONTINUATION_MAX_RISK_PCT_PER_TRADE is
        # retired, proving the re-convergence, not just documenting intent.
        # Companion to test_qualification.py's
        # test_credit_bull_put_clears_gate8_at_raised_budget_prd252, which
        # proves the direct path sizes against the same ~$400 budget under
        # this same live config.
        # atr=2.0 -> spread_width=max(0.50, 2.0*0.05)=0.50 -> spread_cost=$50.
        # ~$400.005 budget -> floor(400.005/50)=8 contracts, $400 dollar_risk.
        # If the old $150 decoupled budget were still in effect: floor(150/50)
        # =3 -- would fail this.
        entry = 100.0
        atr = 2.0
        df = self._breakout_df(entry, atr)
        regime = _expansion_regime()
        dm = _dm(atr, entry=entry)
        result = _qualify_continuation_candidate("TEST", df, _sr(TREND), regime, dm)
        assert result.qualified is True
        assert result.max_contracts == 8
        assert result.dollar_risk == pytest.approx(400.0)

    def test_wick_dominated_candle_fails_momentum_r5(self):
        # PRD-240 R5 red test: last candle range clears 0.75×ATR14, but the
        # close sits at the bottom half of that range (close_location < 0.75)
        # — a wick-dominated candle is not momentum.
        entry = 100.0
        atr = 2.0
        df = self._breakout_df(entry, atr)
        last = df.index[-1]
        # range stays 4.0 (>= 0.75×2.0=1.5); close=101 → close_location
        # = (101-99)/(103-99) = 0.5.
        df.loc[last, "High"] = 103.0
        df.loc[last, "Low"] = 99.0
        dm = _dm(atr, entry=entry)
        result = _qualify_continuation_candidate("TEST", df, _sr(), _expansion_regime(), dm)
        assert result.rejection_reason == "INSUFFICIENT_MOMENTUM"


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
        # PRD-259 strictly-prior lookback = indices 3-7; all window highs
        # = base+1 < entry. Valid OHLC on every bar (High >= Close): the
        # hold candle (index 8) closes at entry with High = entry + 0.5,
        # OUTSIDE the window; current close (index 9) = entry + 1.
        # Current bar range = 2*atr >= 0.75*atr, close_location = 0.75.
        base = entry - 3.0
        closes = [base] * 8 + [entry, entry + 1.0]
        highs = [base + 0.5] * 10
        for i in range(3, 8):          # lookback highs all = base+1 < entry
            highs[i] = base + 1.0
        highs[8] = entry + 0.5         # hold candle high (valid, > close)
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
        assert summary.continuation_audit is not None
        assert summary.continuation_audit["accepted"] >= 1

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
        assert summary.continuation_audit is not None
        assert summary.continuation_audit["total_candidates"] == 0


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
        assert summary.continuation_audit is not None

    def test_expansion_regime_check_regime_gates_passes(self):
        from cuttingboard.qualification import _check_regime_gates
        regime = _expansion_regime()
        result = _check_regime_gates(regime)
        assert result is None, f"Expected no gate failure for EXPANSION, got: {result}"

    def test_direction_for_regime_returns_long(self):
        from cuttingboard.qualification import direction_for_regime
        regime = _expansion_regime()
        assert direction_for_regime(regime) == "LONG"
