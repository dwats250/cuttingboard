from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from cuttingboard.derived import DerivedMetrics
from cuttingboard.output import OUTCOME_NO_TRADE, render_report
from cuttingboard.qualification import (
    CONTINUATION_REJECTION_REASONS,
    _qualify_continuation_candidate,
    qualify_all,
)
from cuttingboard.regime import EXPANSION, EXPANSION_LONG, RegimeState
from cuttingboard.runtime import _log_continuation_audit
from cuttingboard.structure import StructureResult, TREND
from cuttingboard.validation import ValidationSummary


def _expansion_regime(vix_pct_change: float = -0.02) -> RegimeState:
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
        vix_pct_change=vix_pct_change,
        computed_at_utc=datetime(2026, 4, 22, 14, 0, tzinfo=timezone.utc),
    )


def _dm(symbol: str, atr14: float = 2.0, ema21: float = 100.0) -> DerivedMetrics:
    return DerivedMetrics(
        symbol=symbol,
        ema9=101.0,
        ema21=ema21,
        ema50=95.0,
        ema_aligned_bull=True,
        ema_aligned_bear=False,
        ema_spread_pct=0.02,
        atr14=atr14,
        atr_pct=atr14 / 100.0,
        momentum_5d=0.03,
        volume_ratio=1.5,
        computed_at_utc=datetime(2026, 4, 22, 14, 0, tzinfo=timezone.utc),
        sufficient_history=True,
    )


def _sr(symbol: str) -> StructureResult:
    return StructureResult(
        symbol=symbol,
        structure=TREND,
        iv_environment="NORMAL_IV",
        is_tradeable=True,
        disqualification_reason=None,
    )


def _frame(
    closes: list[float],
    highs: list[float],
    lows: list[float],
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": closes,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": [1_000_000] * len(closes),
        }
    )


def _qualified_df() -> pd.DataFrame:
    return _frame(
        closes=[95, 96, 97, 96, 95, 96, 97, 96, 102, 104],
        highs=[96, 97, 98, 97, 96, 97, 98, 97, 100, 106],
        lows=[94, 95, 96, 95, 94, 95, 96, 95, 100, 102],
    )


def _no_breakout_df() -> pd.DataFrame:
    return _frame(
        closes=[98, 99, 100, 101, 100, 99, 98, 99, 100, 100],
        highs=[99, 100, 101, 102, 101, 100, 99, 100, 101, 101],
        lows=[97, 98, 99, 100, 99, 98, 97, 98, 99, 99],
    )


def _no_hold_df() -> pd.DataFrame:
    return _frame(
        closes=[98, 99, 100, 99, 98, 99, 100, 99, 98, 102],
        highs=[99, 100, 101, 100, 99, 100, 101, 100, 101, 103],
        lows=[97, 98, 99, 98, 97, 98, 99, 98, 97, 101],
    )


def _low_momentum_df() -> pd.DataFrame:
    return _frame(
        closes=[95, 96, 97, 96, 95, 96, 97, 96, 102, 104],
        highs=[96, 97, 98, 97, 96, 97, 98, 97, 100, 104.4],
        lows=[94, 95, 96, 95, 94, 95, 96, 95, 100, 103.8],
    )


def _rr_fail_df() -> pd.DataFrame:
    return _frame(
        closes=[96, 97, 98, 97, 96, 97, 98, 97, 104, 105],
        highs=[97, 98, 99, 98, 97, 98, 99, 98, 100, 106],
        lows=[95, 96, 97, 96, 95, 96, 97, 96, 103, 103],
    )


def _tight_stop_df() -> pd.DataFrame:
    return _frame(
        closes=[100, 100.2, 100.4, 100.2, 100.1, 100.2, 100.3, 100.4, 100.6, 100.7],
        highs=[100.3, 100.5, 100.6, 100.4, 100.3, 100.4, 100.5, 100.5, 100.55, 101.6],
        lows=[99.8, 100.0, 100.2, 100.0, 99.9, 100.0, 100.1, 100.2, 100.55, 99.6],
    )


def _validation_summary() -> ValidationSummary:
    return ValidationSummary(
        system_halted=False,
        halt_reason=None,
        failed_halt_symbols=[],
        results={},
        valid_quotes={},
        invalid_symbols={},
        symbols_attempted=0,
        symbols_validated=0,
        symbols_failed=0,
    )


def test_continuation_rejection_taxonomy_is_complete():
    assert CONTINUATION_REJECTION_REASONS == (
        "DATA_INCOMPLETE",
        "VIX_BLOCKED",
        "NO_BREAKOUT",
        "NO_HOLD_CONFIRMATION",
        "INSUFFICIENT_MOMENTUM",
        "EXTENDED_FROM_MEAN",
        "STOP_TOO_TIGHT",
        "RR_BELOW_THRESHOLD",
        "TIME_BLOCKED",
    )


def test_continuation_rejects_with_single_deterministic_reason(monkeypatch):
    monkeypatch.setattr("cuttingboard.qualification._is_late_session", lambda now_et=None: False)

    cases = [
        ("DATA_INCOMPLETE", None, _dm("A")),
        ("VIX_BLOCKED", _qualified_df(), _dm("B"), _expansion_regime(vix_pct_change=0.02)),
        ("NO_BREAKOUT", _no_breakout_df(), _dm("C")),
        ("NO_HOLD_CONFIRMATION", _no_hold_df(), _dm("D")),
        ("INSUFFICIENT_MOMENTUM", _low_momentum_df(), _dm("E")),
        ("EXTENDED_FROM_MEAN", _qualified_df(), _dm("F", ema21=95.0)),
        ("STOP_TOO_TIGHT", _tight_stop_df(), _dm("G", atr14=1.0, ema21=100.5)),
        ("RR_BELOW_THRESHOLD", _rr_fail_df(), _dm("H")),
    ]

    for item in cases:
        reason = item[0]
        df = item[1]
        dm = item[2]
        regime = item[3] if len(item) > 3 else _expansion_regime()
        result = _qualify_continuation_candidate(dm.symbol, df, _sr(dm.symbol), regime, dm)
        assert result.rejection_reason == reason
        assert result.qualified is False
        assert result.watchlist is False
        assert result.gates_failed == [reason]


def test_time_blocked_is_last_gate(monkeypatch):
    monkeypatch.setattr("cuttingboard.qualification._is_late_session", lambda now_et=None: True)
    result = _qualify_continuation_candidate("TIME", _qualified_df(), _sr("TIME"), _expansion_regime(), _dm("TIME"))
    assert result.rejection_reason == "TIME_BLOCKED"


def test_accepted_candidate_has_no_rejection_reason(monkeypatch):
    monkeypatch.setattr("cuttingboard.qualification._is_late_session", lambda now_et=None: False)
    result = _qualify_continuation_candidate("PASS", _qualified_df(), _sr("PASS"), _expansion_regime(), _dm("PASS"))
    assert result.qualified is True
    assert result.rejection_reason is None


def test_first_failure_wins(monkeypatch):
    monkeypatch.setattr("cuttingboard.qualification._is_late_session", lambda now_et=None: True)
    regime = _expansion_regime(vix_pct_change=0.02)
    result = _qualify_continuation_candidate("FIRST", _qualified_df(), _sr("FIRST"), regime, _dm("FIRST", ema21=90.0))
    assert result.rejection_reason == "VIX_BLOCKED"


def test_qualify_all_populates_expansion_audit(monkeypatch):
    monkeypatch.setattr("cuttingboard.qualification._is_late_session", lambda now_et=None: False)

    structure_results = {
        "PASS": _sr("PASS"),
        "DATA": _sr("DATA"),
        "BREAK": _sr("BREAK"),
        "HOLD": _sr("HOLD"),
    }
    derived_metrics = {
        "PASS": _dm("PASS"),
        "DATA": _dm("DATA"),
        "BREAK": _dm("BREAK"),
        "HOLD": _dm("HOLD"),
    }
    ohlcv = {
        "PASS": _qualified_df(),
        "BREAK": _no_breakout_df(),
        "HOLD": _no_hold_df(),
    }

    summary = qualify_all(
        regime=_expansion_regime(),
        structure_results=structure_results,
        candidates=None,
        derived_metrics=derived_metrics,
        ohlcv=ohlcv,
    )

    assert summary.continuation_audit is not None
    audit = summary.continuation_audit
    assert audit["total_candidates"] == 4
    assert audit["accepted"] == 1
    assert audit["DATA_INCOMPLETE"] == 1
    assert audit["NO_BREAKOUT"] == 1
    assert audit["NO_HOLD_CONFIRMATION"] == 1
    assert sum(audit[reason] for reason in CONTINUATION_REJECTION_REASONS) == audit["total_candidates"] - audit["accepted"]


def test_render_report_includes_expansion_audit_and_no_entries_message(monkeypatch):
    monkeypatch.setattr("cuttingboard.qualification._is_late_session", lambda now_et=None: False)

    summary = qualify_all(
        regime=_expansion_regime(),
        structure_results={"BREAK": _sr("BREAK")},
        candidates=None,
        derived_metrics={"BREAK": _dm("BREAK")},
        ohlcv={"BREAK": _no_breakout_df()},
    )

    report = render_report(
        date_str="2026-04-22",
        run_at_utc=datetime(2026, 4, 22, 14, 30, tzinfo=timezone.utc),
        regime=_expansion_regime(),
        validation_summary=_validation_summary(),
        qualification_summary=summary,
        option_setups=[],
        outcome=OUTCOME_NO_TRADE,
        watch_summary=None,
    )

    assert "EXPANSION MODE — No valid continuation entries yet" in report
    assert "[CONTINUATION_AUDIT]" in report
    assert "NO_BREAKOUT=1" in report


def test_runtime_logs_continuation_audit(caplog, monkeypatch):
    monkeypatch.setattr("cuttingboard.qualification._is_late_session", lambda now_et=None: False)
    summary = qualify_all(
        regime=_expansion_regime(),
        structure_results={"BREAK": _sr("BREAK")},
        candidates=None,
        derived_metrics={"BREAK": _dm("BREAK")},
        ohlcv={"BREAK": _no_breakout_df()},
    )

    with caplog.at_level("INFO"):
        _log_continuation_audit(_expansion_regime(), summary)

    text = caplog.text
    assert "[CONTINUATION_AUDIT]" in text
    assert "total_candidates=1" in text
    assert "accepted=0" in text
    assert "NO_BREAKOUT=1" in text
