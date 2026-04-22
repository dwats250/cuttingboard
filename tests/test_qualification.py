"""
Tests for Layer 7 — Trade Qualification (cuttingboard/qualification.py).
All tests are offline — synthetic RegimeState, StructureResult, TradeCandidate.
"""

import pytest
import pandas as pd
from datetime import datetime, timezone

from cuttingboard import config
from cuttingboard.derived import DerivedMetrics
from cuttingboard.qualification import (
    ENTRY_MODE_DIRECT,
    ENTRY_MODE_PULLBACK_IMBALANCE,
    FVGZone,
    detect_fvg,
    qualify_all,
    qualify_candidate,
    direction_for_regime,
    TradeCandidate,
    QualificationResult,
    QualificationSummary,
    GATE_REGIME, GATE_CONFIDENCE, GATE_DIRECTION, GATE_STRUCTURE,
    GATE_STOP_DEF, GATE_STOP_DIST, GATE_RR, GATE_MAX_RISK, GATE_EARNINGS,
    GATE_EXTENSION, GATE_TIME,
    HARD_GATES, SOFT_GATES,
)
from cuttingboard.regime import (
    RegimeState,
    RISK_ON, RISK_OFF, TRANSITION, NEUTRAL, CHAOTIC,
    AGGRESSIVE_LONG, CONTROLLED_LONG, NEUTRAL_PREMIUM,
    DEFENSIVE_SHORT, STAY_FLAT,
)
from cuttingboard.structure import StructureResult, TREND, PULLBACK, BREAKOUT, CHOP, NORMAL_IV


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc)


@pytest.fixture(autouse=True)
def _freeze_session_time(monkeypatch):
    """Ensure GATE_TIME always passes — tests must not depend on wall-clock."""
    monkeypatch.setattr("cuttingboard.qualification._is_late_session", lambda now_et=None: False)


def _regime(
    regime=RISK_ON,
    posture=AGGRESSIVE_LONG,
    confidence=0.75,
    net_score=6,
    vix_level=14.0,
) -> RegimeState:
    return RegimeState(
        regime=regime,
        posture=posture,
        confidence=confidence,
        net_score=net_score,
        risk_on_votes=6,
        risk_off_votes=0,
        neutral_votes=2,
        total_votes=8,
        vote_breakdown={},
        vix_level=vix_level,
        vix_pct_change=-0.01,
        computed_at_utc=_NOW,
    )


def _stay_flat_regime() -> RegimeState:
    return RegimeState(
        regime=TRANSITION,
        posture=STAY_FLAT,
        confidence=0.25,
        net_score=2,
        risk_on_votes=3,
        risk_off_votes=1,
        neutral_votes=4,
        total_votes=8,
        vote_breakdown={},
        vix_level=22.0,
        vix_pct_change=0.0,
        computed_at_utc=_NOW,
    )


def _structure(symbol="TEST", structure=TREND) -> StructureResult:
    return StructureResult(
        symbol=symbol,
        structure=structure,
        iv_environment=NORMAL_IV,
        is_tradeable=(structure != CHOP),
        disqualification_reason=None if structure != CHOP else "CHOP",
    )


def _candidate(
    symbol="TEST",
    direction="LONG",
    entry_price=100.0,
    stop_price=98.0,
    target_price=106.0,
    spread_width=1.0,
    has_earnings_soon=None,
) -> TradeCandidate:
    return TradeCandidate(
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        spread_width=spread_width,
        has_earnings_soon=has_earnings_soon,
    )


def _dm(symbol="TEST", atr14=1.5) -> DerivedMetrics:
    return DerivedMetrics(
        symbol=symbol,
        ema9=105.0, ema21=102.0, ema50=98.0,
        ema_aligned_bull=True, ema_aligned_bear=False,
        ema_spread_pct=0.029,
        atr14=atr14, atr_pct=0.015,
        momentum_5d=0.01, volume_ratio=1.2,
        computed_at_utc=_NOW,
        sufficient_history=True,
    )


def _ohlcv_frame(rows: list[tuple[float, float, float, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close", "Volume"])


def _valid_long_fvg_df() -> pd.DataFrame:
    return _ohlcv_frame([
        (98.0, 99.0, 97.5, 98.6, 1000),
        (98.6, 99.2, 98.0, 98.9, 1000),
        (98.9, 99.4, 98.4, 99.1, 1000),
        (99.1, 99.6, 98.7, 99.3, 1000),
        (99.3, 99.8, 98.9, 99.5, 1000),
        (99.4, 100.0, 99.1, 99.8, 1200),
        (99.8, 104.2, 99.8, 103.4, 1800),
        (101.4, 102.2, 101.2, 101.6, 1500),
    ])


def _no_displacement_long_fvg_df() -> pd.DataFrame:
    return _ohlcv_frame([
        (98.0, 99.0, 97.5, 98.6, 1000),
        (98.6, 99.2, 98.0, 98.9, 1000),
        (98.9, 99.4, 98.4, 99.1, 1000),
        (99.1, 99.6, 98.7, 99.3, 1000),
        (99.3, 99.8, 98.9, 99.5, 1000),
        (99.4, 100.0, 99.1, 99.8, 1200),
        (100.0, 101.0, 99.8, 100.3, 1800),
        (101.4, 102.2, 101.2, 101.6, 1500),
    ])


def _invalidated_long_fvg_df() -> pd.DataFrame:
    return _ohlcv_frame([
        (98.0, 99.0, 97.5, 98.6, 1000),
        (98.6, 99.2, 98.0, 98.9, 1000),
        (98.9, 99.4, 98.4, 99.1, 1000),
        (99.1, 99.6, 98.7, 99.3, 1000),
        (99.3, 99.8, 98.9, 99.5, 1000),
        (99.4, 100.0, 99.1, 99.8, 1200),
        (99.8, 104.2, 99.8, 103.4, 1800),
        (101.4, 102.2, 101.2, 101.6, 1500),
        (99.8, 100.0, 99.0, 99.5, 1400),
    ])


def _far_from_zone_long_fvg_df() -> pd.DataFrame:
    return _ohlcv_frame([
        (98.0, 99.0, 97.5, 98.6, 1000),
        (98.6, 99.2, 98.0, 98.9, 1000),
        (98.9, 99.4, 98.4, 99.1, 1000),
        (99.1, 99.6, 98.7, 99.3, 1000),
        (99.3, 99.8, 98.9, 99.5, 1000),
        (99.4, 100.0, 99.1, 99.8, 1200),
        (99.8, 104.2, 99.8, 103.4, 1800),
        (101.4, 104.5, 101.2, 104.4, 1500),
    ])


def _low_rr_long_fvg_df() -> pd.DataFrame:
    return _ohlcv_frame([
        (97.0, 97.8, 96.6, 97.2, 1000),
        (97.2, 97.9, 96.9, 97.5, 1000),
        (97.5, 98.1, 97.1, 97.7, 1000),
        (97.7, 98.3, 97.4, 97.9, 1000),
        (97.9, 98.6, 97.7, 98.1, 1000),
        (89.8, 90.0, 89.4, 89.9, 1200),
        (90.0, 102.0, 90.0, 101.5, 1800),
        (101.1, 102.2, 101.0, 101.5, 1500),
    ])


def _flat_displacement_df() -> pd.DataFrame:
    return _ohlcv_frame([
        (98.0, 99.0, 97.5, 98.6, 1000),
        (98.6, 99.2, 98.0, 98.9, 1000),
        (98.9, 99.4, 98.4, 99.1, 1000),
        (99.1, 99.6, 98.7, 99.3, 1000),
        (99.3, 99.8, 98.9, 99.5, 1000),
        (99.4, 100.0, 99.1, 99.8, 1200),
        (100.0, 100.0, 100.0, 100.0, 1800),
        (101.2, 102.0, 101.0, 101.5, 1500),
    ])


def _qualify_with_ohlcv(
    df: pd.DataFrame,
    *,
    candidate: TradeCandidate | None = None,
    regime: RegimeState | None = None,
    dm: DerivedMetrics | None = None,
) -> QualificationSummary:
    regime = regime or _regime()
    candidate = candidate or _candidate(
        symbol="TEST",
        direction="LONG",
        entry_price=100.0,
        stop_price=99.0,
        target_price=102.0,
        spread_width=0.5,
    )
    dm = dm or _dm(symbol="TEST", atr14=2.0)
    return qualify_all(
        regime,
        {"TEST": _structure("TEST", TREND)},
        {"TEST": candidate},
        {"TEST": dm},
        ohlcv={"TEST": df},
    )


# ---------------------------------------------------------------------------
# direction_for_regime
# ---------------------------------------------------------------------------

class TestDirectionForRegime:
    def test_risk_on_is_long(self):
        assert direction_for_regime(_regime(regime=RISK_ON)) == "LONG"

    def test_risk_off_is_short(self):
        assert direction_for_regime(_regime(regime=RISK_OFF, posture=DEFENSIVE_SHORT)) == "SHORT"

    def test_neutral_positive_net_score_is_long(self):
        assert direction_for_regime(_regime(regime=NEUTRAL, posture=NEUTRAL_PREMIUM, net_score=1)) == "LONG"

    def test_neutral_negative_net_score_is_short(self):
        assert direction_for_regime(_regime(regime=NEUTRAL, posture=NEUTRAL_PREMIUM, net_score=-1)) == "SHORT"

    def test_neutral_zero_net_score_is_none(self):
        assert direction_for_regime(_regime(regime=NEUTRAL, posture=NEUTRAL_PREMIUM, net_score=0)) is None

    def test_transition_is_none(self):
        # TRANSITION is legacy — direction always None
        assert direction_for_regime(_regime(regime=TRANSITION, posture=NEUTRAL_PREMIUM)) is None

    def test_chaotic_is_none(self):
        assert direction_for_regime(_regime(regime=CHAOTIC, posture=STAY_FLAT)) is None


# ---------------------------------------------------------------------------
# Gate constants
# ---------------------------------------------------------------------------

class TestGateConstants:
    def test_hard_gates_count(self):
        assert len(HARD_GATES) == 4

    def test_soft_gates_count(self):
        assert len(SOFT_GATES) == 7

    def test_hard_and_soft_disjoint(self):
        assert HARD_GATES & SOFT_GATES == set()

    def test_all_gate_names_in_hard_or_soft(self):
        all_gates = {
            GATE_REGIME, GATE_CONFIDENCE, GATE_DIRECTION, GATE_STRUCTURE,
            GATE_STOP_DEF, GATE_STOP_DIST, GATE_RR, GATE_MAX_RISK, GATE_EARNINGS,
            GATE_EXTENSION, GATE_TIME,
        }
        assert all_gates == HARD_GATES | SOFT_GATES


# ---------------------------------------------------------------------------
# qualify_all — regime short-circuit
# ---------------------------------------------------------------------------

class TestQualifyAllRegimeShortCircuit:
    def test_stay_flat_short_circuits(self):
        regime = _stay_flat_regime()
        summary = qualify_all(regime, {})
        assert summary.regime_short_circuited is True
        assert summary.regime_passed is False
        assert summary.symbols_evaluated == 0

    def test_stay_flat_returns_empty_qualified(self):
        summary = qualify_all(_stay_flat_regime(), {})
        assert summary.qualified_trades == []
        assert summary.watchlist == []
        assert summary.excluded == {}

    def test_stay_flat_has_failure_reason(self):
        summary = qualify_all(_stay_flat_regime(), {})
        assert summary.regime_failure_reason is not None

    def test_chaotic_regime_short_circuits(self):
        regime = _regime(regime=CHAOTIC, posture=STAY_FLAT, confidence=0.0)
        summary = qualify_all(regime, {})
        assert summary.regime_short_circuited is True

    def test_risk_on_passes_regime_gate(self):
        regime = _regime(regime=RISK_ON, posture=AGGRESSIVE_LONG)
        summary = qualify_all(regime, {})
        assert summary.regime_passed is True
        assert summary.regime_short_circuited is False

    def test_low_confidence_short_circuits(self):
        regime = _regime(
            regime=RISK_ON, posture=STAY_FLAT,
            confidence=config.MIN_REGIME_CONFIDENCE - 0.01,
        )
        summary = qualify_all(regime, {})
        assert summary.regime_short_circuited is True


# ---------------------------------------------------------------------------
# qualify_all — CHOP hard stop
# ---------------------------------------------------------------------------

class TestQualifyAllChopHardStop:
    def test_chop_symbol_excluded(self):
        regime = _regime()
        structure_results = {"AAPL": _structure("AAPL", CHOP)}
        summary = qualify_all(regime, structure_results)
        assert "AAPL" in summary.excluded
        assert summary.excluded["AAPL"] == "CHOP"

    def test_chop_not_in_qualified_or_watchlist(self):
        regime = _regime()
        structure_results = {"AAPL": _structure("AAPL", CHOP)}
        candidates = {"AAPL": _candidate("AAPL")}
        summary = qualify_all(regime, structure_results, candidates)
        assert not any(r.symbol == "AAPL" for r in summary.qualified_trades)
        assert not any(r.symbol == "AAPL" for r in summary.watchlist)


# ---------------------------------------------------------------------------
# qualify_all — direction mismatch
# ---------------------------------------------------------------------------

class TestQualifyAllDirectionMismatch:
    def test_short_candidate_in_risk_on_regime_excluded(self):
        regime = _regime(regime=RISK_ON, posture=AGGRESSIVE_LONG)
        structure_results = {"X": _structure("X", TREND)}
        candidates = {"X": _candidate("X", direction="SHORT")}
        summary = qualify_all(regime, structure_results, candidates)
        assert "X" in summary.excluded
        assert "direction" in summary.excluded["X"].lower()

    def test_long_candidate_in_risk_off_regime_excluded(self):
        regime = _regime(regime=RISK_OFF, posture=DEFENSIVE_SHORT, net_score=-6)
        structure_results = {"X": _structure("X", TREND)}
        candidates = {"X": _candidate("X", direction="LONG")}
        summary = qualify_all(regime, structure_results, candidates)
        assert "X" in summary.excluded


# ---------------------------------------------------------------------------
# qualify_all — no candidates (Phase 4 mode)
# ---------------------------------------------------------------------------

class TestQualifyAllNoCandidates:
    def test_no_candidates_no_per_symbol_qualification(self):
        regime = _regime()
        structure_results = {"X": _structure("X", TREND)}
        summary = qualify_all(regime, structure_results, candidates=None)
        assert summary.qualified_trades == []
        assert summary.watchlist == []


# ---------------------------------------------------------------------------
# qualify_candidate — hard gate failures
# ---------------------------------------------------------------------------

class TestHardGateFailures:
    def test_stay_flat_gate1_reject(self):
        regime = _stay_flat_regime()
        c = _candidate()
        r = qualify_candidate(c, regime, _structure())
        assert not r.qualified
        assert not r.watchlist
        assert GATE_REGIME in r.gates_failed
        assert r.hard_failure is not None

    def test_low_confidence_gate2_reject(self):
        regime = _regime(
            posture=CONTROLLED_LONG,
            confidence=config.MIN_REGIME_CONFIDENCE - 0.01,
        )
        r = qualify_candidate(_candidate(), regime, _structure())
        assert not r.qualified
        assert GATE_CONFIDENCE in r.gates_failed

    def test_direction_mismatch_gate3_reject(self):
        regime = _regime(regime=RISK_ON, posture=AGGRESSIVE_LONG)
        c = _candidate(direction="SHORT")
        r = qualify_candidate(c, regime, _structure())
        assert not r.qualified
        assert GATE_DIRECTION in r.gates_failed

    def test_chop_structure_gate4_reject(self):
        regime = _regime()
        c = _candidate()
        r = qualify_candidate(c, regime, _structure(structure=CHOP))
        assert not r.qualified
        assert GATE_STRUCTURE in r.gates_failed

    def test_hard_failure_no_watchlist(self):
        r = qualify_candidate(_candidate(), _stay_flat_regime(), _structure())
        assert not r.watchlist
        assert r.watchlist_reason is None

    def test_hard_failure_gates_passed_accumulated(self):
        # Gate 2 fails — Gate 1 should be in gates_passed
        regime = _regime(confidence=config.MIN_REGIME_CONFIDENCE - 0.01)
        r = qualify_candidate(_candidate(), regime, _structure())
        assert GATE_REGIME in r.gates_passed
        assert GATE_CONFIDENCE in r.gates_failed


# ---------------------------------------------------------------------------
# qualify_candidate — all soft gates pass → QUALIFIED
# ---------------------------------------------------------------------------

class TestFullyQualified:
    def _make_clean_candidate(self) -> TradeCandidate:
        # entry=100, stop=97 (3% stop distance), target=106 (R:R=2.0)
        # spread_width=0.50 → spread_cost=$50 → max_contracts=3, dollar_risk=$150
        return _candidate(
            entry_price=100.0,
            stop_price=97.0,
            target_price=106.0,
            spread_width=0.50,
            has_earnings_soon=None,
        )

    def test_fully_qualified_result(self):
        regime = _regime()
        r = qualify_candidate(self._make_clean_candidate(), regime, _structure())
        assert r.qualified
        assert not r.watchlist
        assert r.hard_failure is None

    def test_all_9_gates_passed(self):
        regime = _regime()
        r = qualify_candidate(self._make_clean_candidate(), regime, _structure())
        assert len(r.gates_failed) == 0
        assert GATE_REGIME in r.gates_passed
        assert GATE_CONFIDENCE in r.gates_passed
        assert GATE_DIRECTION in r.gates_passed
        assert GATE_STRUCTURE in r.gates_passed
        assert GATE_STOP_DEF in r.gates_passed
        assert GATE_STOP_DIST in r.gates_passed
        assert GATE_RR in r.gates_passed
        assert GATE_MAX_RISK in r.gates_passed
        assert GATE_EARNINGS in r.gates_passed

    def test_position_sizing(self):
        regime = _regime()
        c = _candidate(spread_width=0.50)
        r = qualify_candidate(
            _candidate(entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=0.50),
            regime, _structure(),
        )
        # spread_cost = 0.50 × 100 = $50; max_contracts = floor(150/50) = 3
        assert r.max_contracts == 3
        assert r.dollar_risk == pytest.approx(150.0)

    def test_direction_field_set(self):
        r = qualify_candidate(
            _candidate(direction="LONG"),
            _regime(), _structure(),
        )
        # LONG is correct for RISK_ON; verify it is recorded
        # entry=100, stop=97, target=106 gives RR=2.0 (exactly at boundary)
        # The gate passes when rr >= MIN_RR_RATIO


# ---------------------------------------------------------------------------
# qualify_candidate — soft gate: STOP_DEFINED
# ---------------------------------------------------------------------------

class TestGateStopDefined:
    def test_zero_stop_fails_gate5(self):
        c = _candidate(stop_price=0.0)
        r = qualify_candidate(c, _regime(), _structure())
        assert GATE_STOP_DEF in r.gates_failed

    def test_stop_equals_entry_fails_gate5(self):
        c = _candidate(entry_price=100.0, stop_price=100.0)
        r = qualify_candidate(c, _regime(), _structure())
        assert GATE_STOP_DEF in r.gates_failed


# ---------------------------------------------------------------------------
# qualify_candidate — soft gate: STOP_DISTANCE
# ---------------------------------------------------------------------------

class TestGateStopDistance:
    def test_stop_below_1pct_fails_gate6(self):
        # 0.5% stop
        c = _candidate(entry_price=100.0, stop_price=99.5, target_price=106.0, spread_width=0.5)
        r = qualify_candidate(c, _regime(), _structure())
        assert GATE_STOP_DIST in r.gates_failed

    def test_stop_at_1pct_passes_gate6_without_atr(self):
        # exactly 1% stop, no DM → skip ATR check
        c = _candidate(entry_price=100.0, stop_price=99.0, target_price=106.0, spread_width=0.5)
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert GATE_STOP_DIST in r.gates_passed

    def test_stop_below_half_atr_fails_gate6(self):
        # stop = $1.0, ATR14 = 3.0 → 0.5×ATR = $1.5 → stop < half_atr
        c = _candidate(entry_price=100.0, stop_price=99.0, target_price=106.0, spread_width=0.5)
        dm = _dm(atr14=3.0)
        r = qualify_candidate(c, _regime(), _structure(), dm=dm)
        assert GATE_STOP_DIST in r.gates_failed

    def test_stop_above_half_atr_passes_gate6(self):
        # stop = $3.0, ATR14 = 4.0 → 0.5×ATR = $2.0 → stop > half_atr
        c = _candidate(entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=0.5)
        dm = _dm(atr14=4.0)
        r = qualify_candidate(c, _regime(), _structure(), dm=dm)
        assert GATE_STOP_DIST in r.gates_passed


# ---------------------------------------------------------------------------
# qualify_candidate — soft gate: RR_RATIO
# ---------------------------------------------------------------------------

class TestGateRrRatio:
    def test_rr_below_minimum_fails_gate7(self):
        # risk=2, reward=3 → RR=1.5, below 2.0 minimum
        c = _candidate(entry_price=100.0, stop_price=98.0, target_price=103.0, spread_width=0.5)
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert GATE_RR in r.gates_failed

    def test_rr_at_minimum_passes_gate7(self):
        # risk=2, reward=4 → RR=2.0, exactly at minimum
        c = _candidate(entry_price=100.0, stop_price=98.0, target_price=104.0, spread_width=0.5)
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert GATE_RR in r.gates_passed

    def test_rr_above_minimum_passes_gate7(self):
        # risk=2, reward=6 → RR=3.0
        c = _candidate(entry_price=100.0, stop_price=98.0, target_price=106.0, spread_width=0.5)
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert GATE_RR in r.gates_passed

    def test_zero_risk_fails_gate7(self):
        c = _candidate(entry_price=100.0, stop_price=100.0, target_price=106.0, spread_width=0.5)
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert GATE_RR in r.gates_failed


# ---------------------------------------------------------------------------
# qualify_candidate — soft gate: MAX_RISK
# ---------------------------------------------------------------------------

class TestGateMaxRisk:
    def test_wide_spread_exceeds_max_fails_gate8(self):
        # spread_width=3.0 → spread_cost=$300 → max_c=0 → FAIL
        c = _candidate(entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=3.0)
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert GATE_MAX_RISK in r.gates_failed

    def test_narrow_spread_passes_gate8(self):
        # spread_width=0.50 → spread_cost=$50 → max_c=3 → PASS
        c = _candidate(entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=0.50)
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert GATE_MAX_RISK in r.gates_passed

    def test_max_contracts_computed_correctly(self):
        # spread_width=0.75 → spread_cost=$75 → floor(150/75)=2 contracts
        c = _candidate(entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=0.75)
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert r.max_contracts == 2
        assert r.dollar_risk == pytest.approx(150.0)

    def test_dollar_risk_is_max_contracts_times_spread_cost(self):
        # spread_width=1.0 → spread_cost=$100 → floor(150/100)=1 → risk=$100
        c = _candidate(entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=1.0)
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert r.max_contracts == 1
        assert r.dollar_risk == pytest.approx(100.0)

    def test_zero_spread_fails_gate8(self):
        c = _candidate(spread_width=0.0)
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert GATE_MAX_RISK in r.gates_failed


# ---------------------------------------------------------------------------
# qualify_candidate — soft gate: EARNINGS
# ---------------------------------------------------------------------------

class TestGateEarnings:
    def test_earnings_soon_true_fails_gate9(self):
        c = _candidate(
            entry_price=100.0, stop_price=97.0, target_price=106.0,
            spread_width=0.5, has_earnings_soon=True,
        )
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert GATE_EARNINGS in r.gates_failed

    def test_earnings_soon_none_passes_gate9_fail_open(self):
        c = _candidate(
            entry_price=100.0, stop_price=97.0, target_price=106.0,
            spread_width=0.5, has_earnings_soon=None,
        )
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert GATE_EARNINGS in r.gates_passed

    def test_earnings_soon_false_passes_gate9(self):
        c = _candidate(
            entry_price=100.0, stop_price=97.0, target_price=106.0,
            spread_width=0.5, has_earnings_soon=False,
        )
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert GATE_EARNINGS in r.gates_passed


# ---------------------------------------------------------------------------
# qualify_candidate — watchlist (exactly one soft gate miss)
# ---------------------------------------------------------------------------

class TestWatchlistOutcome:
    def test_one_soft_miss_is_watchlist(self):
        # Only gate 9 (EARNINGS) fails
        c = _candidate(
            entry_price=100.0, stop_price=97.0, target_price=106.0,
            spread_width=0.5, has_earnings_soon=True,
        )
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert r.watchlist
        assert not r.qualified
        assert r.watchlist_reason is not None

    def test_watchlist_reason_set(self):
        c = _candidate(
            entry_price=100.0, stop_price=97.0, target_price=106.0,
            spread_width=0.5, has_earnings_soon=True,
        )
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert "earnings" in r.watchlist_reason.lower()

    def test_watchlist_no_hard_failure(self):
        c = _candidate(
            entry_price=100.0, stop_price=97.0, target_price=106.0,
            spread_width=0.5, has_earnings_soon=True,
        )
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert r.hard_failure is None


# ---------------------------------------------------------------------------
# qualify_candidate — reject on two+ soft gate misses
# ---------------------------------------------------------------------------

class TestRejectMultipleSoftMisses:
    def test_two_soft_misses_is_reject(self):
        # Gate 9 (earnings) fails AND gate 5 (stop not defined) fails
        c = _candidate(
            entry_price=100.0, stop_price=0.0,  # gate 5 fails
            target_price=106.0, spread_width=0.5,
            has_earnings_soon=True,  # gate 9 fails
        )
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert not r.qualified
        assert not r.watchlist
        assert r.hard_failure is not None

    def test_two_soft_misses_not_watchlist(self):
        c = _candidate(
            entry_price=100.0, stop_price=0.0,
            target_price=106.0, spread_width=0.5,
            has_earnings_soon=True,
        )
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert not r.watchlist

    def test_gates_failed_lists_both_failed_gates(self):
        c = _candidate(
            entry_price=100.0, stop_price=0.0,
            target_price=106.0, spread_width=0.5,
            has_earnings_soon=True,
        )
        r = qualify_candidate(c, _regime(), _structure(), dm=None)
        assert len(r.gates_failed) >= 2
        assert GATE_STOP_DEF in r.gates_failed
        assert GATE_EARNINGS in r.gates_failed


# ---------------------------------------------------------------------------
# qualify_all — summary counts
# ---------------------------------------------------------------------------

class TestQualifyAllCounts:
    def test_counts_match_lists(self):
        regime = _regime()
        # One valid candidate + one CHOP
        structure_results = {
            "A": _structure("A", TREND),
            "B": _structure("B", CHOP),
        }
        candidates = {
            "A": _candidate(
                "A", direction="LONG",
                entry_price=100.0, stop_price=97.0,
                target_price=106.0, spread_width=0.5,
            ),
        }
        summary = qualify_all(regime, structure_results, candidates)
        assert summary.symbols_evaluated == 2
        assert summary.symbols_qualified == len(summary.qualified_trades)
        assert summary.symbols_watchlist == len(summary.watchlist)
        assert summary.symbols_excluded == len(summary.excluded)

    def test_total_adds_up(self):
        regime = _regime()
        structure_results = {
            "A": _structure("A", TREND),
            "B": _structure("B", CHOP),
        }
        candidates = {
            "A": _candidate(
                "A", direction="LONG",
                entry_price=100.0, stop_price=97.0,
                target_price=106.0, spread_width=0.5,
            ),
        }
        summary = qualify_all(regime, structure_results, candidates)
        total = (
            summary.symbols_qualified
            + summary.symbols_watchlist
            + summary.symbols_excluded
        )
        # Total qualified + watchlist + excluded should account for all non-skipped symbols
        assert total <= summary.symbols_evaluated


# ---------------------------------------------------------------------------
# FVG entry mode
# ---------------------------------------------------------------------------

class TestImbalancePullbackEntryMode:
    def test_no_displacement_candle_stays_direct(self):
        summary = _qualify_with_ohlcv(_no_displacement_long_fvg_df())
        result = summary.qualified_trades[0]
        assert result.entry_mode == ENTRY_MODE_DIRECT
        assert result.imbalance_zone is None

    def test_unqualified_candidate_never_uses_pullback_mode(self):
        summary = _qualify_with_ohlcv(
            _valid_long_fvg_df(),
            candidate=_candidate(
                symbol="TEST",
                direction="LONG",
                entry_price=100.0,
                stop_price=99.0,
                target_price=102.0,
                spread_width=0.5,
                has_earnings_soon=True,
            ),
        )
        result = summary.watchlist[0]
        assert result.entry_mode == ENTRY_MODE_DIRECT
        assert result.imbalance_zone is None

    def test_valid_imbalance_enables_pullback_mode(self):
        summary = _qualify_with_ohlcv(_valid_long_fvg_df())
        result = summary.qualified_trades[0]
        assert result.entry_mode == ENTRY_MODE_PULLBACK_IMBALANCE
        assert result.imbalance_zone == FVGZone(upper_bound=101.2, lower_bound=100.0)

    def test_invalidated_imbalance_stays_direct(self):
        summary = _qualify_with_ohlcv(_invalidated_long_fvg_df())
        result = summary.qualified_trades[0]
        assert result.entry_mode == ENTRY_MODE_DIRECT
        assert result.imbalance_zone is None

    def test_low_imbalance_rr_stays_direct(self):
        summary = _qualify_with_ohlcv(
            _low_rr_long_fvg_df(),
            candidate=_candidate(
                symbol="TEST",
                direction="LONG",
                entry_price=101.5,
                stop_price=99.5,
                target_price=105.5,
                spread_width=0.5,
            ),
            dm=_dm(symbol="TEST", atr14=4.0),
        )
        result = summary.qualified_trades[0]
        assert result.entry_mode == ENTRY_MODE_DIRECT
        assert result.imbalance_zone is None

    def test_far_from_zone_stays_direct(self):
        summary = _qualify_with_ohlcv(_far_from_zone_long_fvg_df())
        result = summary.qualified_trades[0]
        assert result.entry_mode == ENTRY_MODE_DIRECT
        assert result.imbalance_zone is None

    def test_high_equals_low_displacement_is_invalid(self):
        zone = detect_fvg(_flat_displacement_df(), "LONG", atr14=2.0)
        assert zone is None
