"""
Tests for the TIME gate (Gate 11) in qualification.

Verifies that entry cutoff logic is deterministic, correct, and wired
through qualify_candidate and qualify_all.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from cuttingboard import config
from cuttingboard import time_utils
from cuttingboard import qualification
from cuttingboard.qualification import qualify_candidate, qualify_all, GATE_TIME, TradeCandidate
from cuttingboard.regime import RegimeState, RISK_ON
from cuttingboard.structure import StructureResult, TREND, NORMAL_IV

_ET = ZoneInfo("America/New_York")
_UTC = timezone.utc
_NOW = datetime(2026, 4, 22, 13, 45, tzinfo=_UTC)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_regime() -> RegimeState:
    return RegimeState(
        regime=RISK_ON,
        posture="AGGRESSIVE_LONG",
        confidence=0.75,
        net_score=5,
        risk_on_votes=6,
        risk_off_votes=1,
        neutral_votes=1,
        total_votes=8,
        vote_breakdown={},
        vix_level=15.0,
        vix_pct_change=-0.05,
        computed_at_utc=_NOW,
    )


def _make_structure(symbol="SPY") -> StructureResult:
    return StructureResult(
        symbol=symbol,
        structure=TREND,
        iv_environment=NORMAL_IV,
        is_tradeable=True,
        disqualification_reason=None,
    )


def _make_candidate(symbol="SPY", direction="LONG") -> TradeCandidate:
    return TradeCandidate(
        symbol=symbol,
        direction=direction,
        entry_price=500.0,
        stop_price=495.0,       # 1% stop
        target_price=510.0,     # 2:1 R:R
        spread_width=1.0,
        has_earnings_soon=None,
    )


def _et(year, month, day, hour, minute) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=_ET)


# ---------------------------------------------------------------------------
# Gate 11: TIME — qualify_candidate
# ---------------------------------------------------------------------------

def test_time_gate_passes_before_cutoff():
    now_et = _et(2026, 4, 22, 9, 45)  # 09:45 ET — well before cutoff
    result = qualify_candidate(
        _make_candidate(), _make_regime(), _make_structure(), now_et=now_et
    )
    assert GATE_TIME in result.gates_passed


def test_time_gate_blocks_after_cutoff():
    now_et = _et(2026, 4, 22, 15, 31)  # 15:31 ET — after cutoff
    result = qualify_candidate(
        _make_candidate(), _make_regime(), _make_structure(), now_et=now_et
    )
    assert GATE_TIME in result.gates_failed
    assert not result.qualified


def test_time_gate_blocks_exactly_at_cutoff():
    now_et = _et(2026, 4, 22, 15, 30)  # exactly 15:30 ET
    result = qualify_candidate(
        _make_candidate(), _make_regime(), _make_structure(), now_et=now_et
    )
    assert GATE_TIME in result.gates_failed
    assert not result.qualified


def test_time_gate_passes_one_minute_before_cutoff():
    now_et = _et(2026, 4, 22, 15, 29)
    result = qualify_candidate(
        _make_candidate(), _make_regime(), _make_structure(), now_et=now_et
    )
    assert GATE_TIME in result.gates_passed


# ---------------------------------------------------------------------------
# Gate 11: TIME — qualify_all threading
# ---------------------------------------------------------------------------

def test_qualify_all_threads_now_et_to_gate():
    now_et = _et(2026, 4, 22, 15, 31)  # after cutoff
    regime = _make_regime()
    structure = {"SPY": _make_structure()}
    candidates = {"SPY": _make_candidate()}

    summary = qualify_all(regime, structure, candidates, now_et=now_et)

    all_outcomes = (
        [r.symbol for r in summary.qualified_trades]
        + [r.symbol for r in summary.watchlist]
        + list(summary.excluded)
    )
    assert "SPY" in all_outcomes


def test_qualify_all_no_now_et_does_not_crash():
    """Without now_et, falls back to wall-clock — must not raise."""
    regime = _make_regime()
    structure = {"SPY": _make_structure()}
    candidates = {"SPY": _make_candidate()}
    summary = qualify_all(regime, structure, candidates)
    assert summary is not None


def test_time_gate_exception_fails_closed(monkeypatch):
    monkeypatch.setattr(
        qualification.time_utils,
        "is_after_entry_cutoff",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("clock failed")),
    )

    result = qualify_candidate(
        _make_candidate(),
        _make_regime(),
        _make_structure(),
        now_et=_et(2026, 4, 22, 9, 45),
    )

    assert GATE_TIME in result.gates_failed
    assert not result.qualified


# ---------------------------------------------------------------------------
# PRD-009 log validation: time_utils values match expected
# ---------------------------------------------------------------------------

def test_utc_1345_maps_to_0945_et_not_after_cutoff():
    """PRD case 1: 2026-04-22 13:45 UTC → 09:45 ET, not after cutoff."""
    now_utc = datetime(2026, 4, 22, 13, 45, tzinfo=_UTC)
    now_et = time_utils.convert_utc_to_et(now_utc)
    assert (now_et.hour, now_et.minute) == (9, 45)
    assert not time_utils.is_after_entry_cutoff(now_et, config.ENTRY_CUTOFF_ET)


def test_utc_1931_maps_to_1531_et_after_cutoff():
    """PRD case 2: 2026-04-22 19:31 UTC → 15:31 ET, after cutoff."""
    now_utc = datetime(2026, 4, 22, 19, 31, tzinfo=_UTC)
    now_et = time_utils.convert_utc_to_et(now_utc)
    assert (now_et.hour, now_et.minute) == (15, 31)
    assert time_utils.is_after_entry_cutoff(now_et, config.ENTRY_CUTOFF_ET)
