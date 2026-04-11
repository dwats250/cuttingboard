"""
Tests for Phase 5 — Options, Audit, Output (cuttingboard/options.py,
cuttingboard/audit.py, cuttingboard/output.py).

All tests are offline — no network calls, no disk writes in most tests.
Audit write tests use a tmp_path fixture to sandbox the file.
"""

import json
import os
import math
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

from cuttingboard import config
from cuttingboard.audit import write_audit_record, _build_record, AUDIT_LOG_PATH
from cuttingboard.derived import DerivedMetrics
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.options import (
    generate_candidates,
    build_option_setups,
    _select_strategy,
    _select_dte,
    _format_strikes,
    _estimated_debit,
    OptionSetup,
    BULL_CALL_SPREAD, BULL_PUT_SPREAD,
    BEAR_PUT_SPREAD, BEAR_CALL_SPREAD,
    _INDEX_ETFS, _MAX_STRIKE_DIST_ETF, _MAX_STRIKE_DIST_STK,
    _DTE_FAST, _DTE_SHORT, _DTE_MEDIUM,
)
from cuttingboard.output import (
    render_report,
    send_pushover,
    OUTCOME_TRADE, OUTCOME_NO_TRADE, OUTCOME_HALT,
)
from cuttingboard.qualification import (
    QualificationResult,
    QualificationSummary,
    TradeCandidate,
    GATE_REGIME,
)
from cuttingboard.regime import (
    RegimeState,
    RISK_ON, RISK_OFF, TRANSITION,
    AGGRESSIVE_LONG, DEFENSIVE_SHORT, STAY_FLAT, NEUTRAL_PREMIUM,
)
from cuttingboard.structure import (
    StructureResult,
    TREND, PULLBACK, BREAKOUT, REVERSAL, CHOP,
    LOW_IV, NORMAL_IV, ELEVATED_IV, HIGH_IV,
)
from cuttingboard.validation import ValidationSummary


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc)


def _regime(
    regime=RISK_ON, posture=AGGRESSIVE_LONG,
    confidence=0.75, net_score=6, vix_level=14.0,
) -> RegimeState:
    return RegimeState(
        regime=regime, posture=posture,
        confidence=confidence, net_score=net_score,
        risk_on_votes=6, risk_off_votes=0, neutral_votes=2, total_votes=8,
        vote_breakdown={}, vix_level=vix_level, vix_pct_change=-0.01,
        computed_at_utc=_NOW,
    )


def _stay_flat() -> RegimeState:
    return RegimeState(
        regime=TRANSITION, posture=STAY_FLAT,
        confidence=0.25, net_score=2,
        risk_on_votes=3, risk_off_votes=1, neutral_votes=4, total_votes=8,
        vote_breakdown={}, vix_level=22.0, vix_pct_change=0.0,
        computed_at_utc=_NOW,
    )


def _structure(symbol="TEST", structure=TREND, iv=NORMAL_IV) -> StructureResult:
    return StructureResult(
        symbol=symbol, structure=structure, iv_environment=iv,
        is_tradeable=(structure != CHOP),
        disqualification_reason=None if structure != CHOP else "CHOP",
    )


def _quote(symbol="TEST", price=100.0) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol, price=price, pct_change_decimal=0.005,
        volume=1_000_000, fetched_at_utc=_NOW,
        source="yfinance", units="USD", age_seconds=10.0,
    )


def _dm(symbol="TEST", atr14=2.0, momentum_5d=0.01) -> DerivedMetrics:
    return DerivedMetrics(
        symbol=symbol, ema9=105.0, ema21=102.0, ema50=98.0,
        ema_aligned_bull=True, ema_aligned_bear=False,
        ema_spread_pct=0.029, atr14=atr14, atr_pct=0.02,
        momentum_5d=momentum_5d, volume_ratio=1.2,
        computed_at_utc=_NOW, sufficient_history=True,
    )


def _qual_result(
    symbol="TEST", direction="LONG",
    max_contracts=3, dollar_risk=150.0,
) -> QualificationResult:
    return QualificationResult(
        symbol=symbol, qualified=True, watchlist=False,
        direction=direction,
        gates_passed=["REGIME", "CONFIDENCE", "DIRECTION", "STRUCTURE",
                      "STOP_DEFINED", "STOP_DISTANCE", "RR_RATIO",
                      "MAX_RISK", "EARNINGS"],
        gates_failed=[], hard_failure=None, watchlist_reason=None,
        max_contracts=max_contracts, dollar_risk=dollar_risk,
    )


def _val_summary(validated=20, attempted=20, failed=0) -> ValidationSummary:
    return ValidationSummary(
        system_halted=False, halt_reason=None,
        failed_halt_symbols=[], results={}, valid_quotes={},
        invalid_symbols={},
        symbols_attempted=attempted,
        symbols_validated=validated,
        symbols_failed=failed,
    )


def _qual_summary(
    qualified=None, watchlist=None, excluded=None,
    short_circuited=False, failure_reason=None,
) -> QualificationSummary:
    q = qualified or []
    w = watchlist or []
    e = excluded or {}
    return QualificationSummary(
        regime_passed=not short_circuited,
        regime_short_circuited=short_circuited,
        regime_failure_reason=failure_reason,
        qualified_trades=q,
        watchlist=w,
        excluded=e,
        symbols_evaluated=len(q) + len(w) + len(e),
        symbols_qualified=len(q),
        symbols_watchlist=len(w),
        symbols_excluded=len(e),
    )


# ---------------------------------------------------------------------------
# options.py — strategy selection
# ---------------------------------------------------------------------------

class TestSelectStrategy:
    def test_long_low_iv_is_bull_call(self):
        assert _select_strategy("LONG", LOW_IV) == BULL_CALL_SPREAD

    def test_long_normal_iv_is_bull_call(self):
        assert _select_strategy("LONG", NORMAL_IV) == BULL_CALL_SPREAD

    def test_long_elevated_iv_is_bull_put(self):
        assert _select_strategy("LONG", ELEVATED_IV) == BULL_PUT_SPREAD

    def test_long_high_iv_is_bull_put(self):
        assert _select_strategy("LONG", HIGH_IV) == BULL_PUT_SPREAD

    def test_short_low_iv_is_bear_put(self):
        assert _select_strategy("SHORT", LOW_IV) == BEAR_PUT_SPREAD

    def test_short_normal_iv_is_bear_put(self):
        assert _select_strategy("SHORT", NORMAL_IV) == BEAR_PUT_SPREAD

    def test_short_elevated_iv_is_bear_call(self):
        assert _select_strategy("SHORT", ELEVATED_IV) == BEAR_CALL_SPREAD

    def test_short_high_iv_is_bear_call(self):
        assert _select_strategy("SHORT", HIGH_IV) == BEAR_CALL_SPREAD


# ---------------------------------------------------------------------------
# options.py — DTE selection
# ---------------------------------------------------------------------------

class TestSelectDte:
    def test_breakout_is_fast(self):
        assert _select_dte(BREAKOUT, None) == _DTE_FAST

    def test_reversal_is_fast(self):
        assert _select_dte(REVERSAL, None) == _DTE_FAST

    def test_breakout_strong_momentum_still_fast(self):
        dm = _dm(momentum_5d=0.05)
        assert _select_dte(BREAKOUT, dm) == _DTE_FAST

    def test_pullback_no_momentum_is_short(self):
        dm = _dm(momentum_5d=0.01)
        assert _select_dte(PULLBACK, dm) == _DTE_SHORT

    def test_pullback_strong_momentum_is_fast(self):
        dm = _dm(momentum_5d=0.04)
        assert _select_dte(PULLBACK, dm) == _DTE_FAST

    def test_trend_no_momentum_is_medium(self):
        dm = _dm(momentum_5d=0.01)
        assert _select_dte(TREND, dm) == _DTE_MEDIUM

    def test_trend_strong_momentum_is_short(self):
        dm = _dm(momentum_5d=0.04)
        assert _select_dte(TREND, dm) == _DTE_SHORT

    def test_none_dm_returns_valid_dte(self):
        dte = _select_dte(TREND, None)
        assert dte > 0


# ---------------------------------------------------------------------------
# options.py — strike formatting
# ---------------------------------------------------------------------------

class TestFormatStrikes:
    def test_bull_call_spread_strikes(self):
        long_s, short_s = _format_strikes(BULL_CALL_SPREAD, 5.0)
        assert long_s == "1_ITM"
        assert short_s == "ATM"

    def test_bull_put_spread_strikes_contain_width(self):
        long_s, short_s = _format_strikes(BULL_PUT_SPREAD, 5.0)
        assert "5.00" in long_s
        assert short_s == "ATM"

    def test_bear_put_spread_strikes(self):
        long_s, short_s = _format_strikes(BEAR_PUT_SPREAD, 2.5)
        assert long_s == "1_ITM"
        assert short_s == "ATM"

    def test_bear_call_spread_strikes_contain_width(self):
        long_s, short_s = _format_strikes(BEAR_CALL_SPREAD, 5.0)
        assert long_s == "ATM"
        assert "5.00" in short_s


# ---------------------------------------------------------------------------
# options.py — estimated debit
# ---------------------------------------------------------------------------

class TestEstimatedDebit:
    def test_etf_debit(self):
        debit = _estimated_debit(_MAX_STRIKE_DIST_ETF)
        assert debit == pytest.approx(_MAX_STRIKE_DIST_ETF * 0.30, rel=1e-3)

    def test_stock_debit(self):
        debit = _estimated_debit(_MAX_STRIKE_DIST_STK)
        assert debit == pytest.approx(_MAX_STRIKE_DIST_STK * 0.30, rel=1e-3)

    def test_etf_debit_fits_gate8(self):
        # spread_cost = debit × 100; max_c = floor(150 / spread_cost) must be ≥ 1
        debit = _estimated_debit(_MAX_STRIKE_DIST_ETF)
        spread_cost = debit * 100
        max_c = math.floor(config.TARGET_DOLLAR_RISK / spread_cost)
        assert max_c >= 1, f"ETF debit ${debit} fails gate 8 (max_c={max_c})"

    def test_stock_debit_fits_gate8(self):
        debit = _estimated_debit(_MAX_STRIKE_DIST_STK)
        spread_cost = debit * 100
        max_c = math.floor(config.TARGET_DOLLAR_RISK / spread_cost)
        assert max_c >= 1, f"Stock debit ${debit} fails gate 8 (max_c={max_c})"


# ---------------------------------------------------------------------------
# options.py — generate_candidates
# ---------------------------------------------------------------------------

class TestGenerateCandidates:
    def _make_inputs(self, symbol="AAPL"):
        sr = {"AAPL": _structure("AAPL", TREND)}
        dm = {"AAPL": _dm("AAPL", atr14=2.0)}
        vq = {"AAPL": _quote("AAPL", price=150.0)}
        return sr, dm, vq

    def test_returns_candidate_for_non_chop(self):
        sr, dm, vq = self._make_inputs()
        result = generate_candidates(sr, dm, vq, _regime())
        assert "AAPL" in result

    def test_chop_excluded(self):
        sr = {"AAPL": _structure("AAPL", CHOP)}
        dm = {"AAPL": _dm("AAPL")}
        vq = {"AAPL": _quote("AAPL")}
        result = generate_candidates(sr, dm, vq, _regime())
        assert "AAPL" not in result

    def test_no_direction_returns_empty(self):
        # TRANSITION regime → no directional bias → empty
        regime = _regime(regime=TRANSITION, posture=NEUTRAL_PREMIUM, net_score=1)
        sr = {"AAPL": _structure("AAPL", TREND)}
        dm = {"AAPL": _dm("AAPL")}
        vq = {"AAPL": _quote("AAPL")}
        result = generate_candidates(sr, dm, vq, regime)
        assert result == {}

    def test_long_direction_in_risk_on(self):
        sr, dm, vq = self._make_inputs()
        result = generate_candidates(sr, dm, vq, _regime(regime=RISK_ON))
        assert result["AAPL"].direction == "LONG"

    def test_short_direction_in_risk_off(self):
        sr, dm, vq = self._make_inputs()
        regime = _regime(regime=RISK_OFF, posture=DEFENSIVE_SHORT, net_score=-6)
        result = generate_candidates(sr, dm, vq, regime)
        assert result["AAPL"].direction == "SHORT"

    def test_stop_below_entry_for_long(self):
        sr, dm, vq = self._make_inputs()
        cand = generate_candidates(sr, dm, vq, _regime())["AAPL"]
        assert cand.stop_price < cand.entry_price

    def test_stop_above_entry_for_short(self):
        sr, dm, vq = self._make_inputs()
        regime = _regime(regime=RISK_OFF, posture=DEFENSIVE_SHORT, net_score=-6)
        cand = generate_candidates(sr, dm, vq, regime)["AAPL"]
        assert cand.stop_price > cand.entry_price

    def test_rr_is_exactly_2_when_atr_available(self):
        sr, dm, vq = self._make_inputs()
        cand = generate_candidates(sr, dm, vq, _regime())["AAPL"]
        risk   = abs(cand.entry_price - cand.stop_price)
        reward = abs(cand.target_price - cand.entry_price)
        assert reward / risk == pytest.approx(2.0)

    def test_etf_spread_width(self):
        sr = {"SPY": _structure("SPY", TREND)}
        dm = {"SPY": _dm("SPY")}
        vq = {"SPY": _quote("SPY", price=560.0)}
        cand = generate_candidates(sr, dm, vq, _regime())["SPY"]
        expected = _estimated_debit(_MAX_STRIKE_DIST_ETF)
        assert cand.spread_width == pytest.approx(expected)

    def test_stock_spread_width(self):
        sr, dm, vq = self._make_inputs()
        cand = generate_candidates(sr, dm, vq, _regime())["AAPL"]
        expected = _estimated_debit(_MAX_STRIKE_DIST_STK)
        assert cand.spread_width == pytest.approx(expected)

    def test_fallback_stop_when_no_dm(self):
        sr = {"AAPL": _structure("AAPL", TREND)}
        dm: dict = {}  # no derived metrics
        vq = {"AAPL": _quote("AAPL", price=100.0)}
        cand = generate_candidates(sr, dm, vq, _regime())["AAPL"]
        # Fallback = 2% stop
        assert cand.stop_price == pytest.approx(100.0 * (1 - 0.02))


# ---------------------------------------------------------------------------
# options.py — build_option_setups
# ---------------------------------------------------------------------------

class TestBuildOptionSetups:
    def test_returns_one_setup_per_qualified(self):
        results = [_qual_result("SPY")]
        sr = {"SPY": _structure("SPY", TREND, LOW_IV)}
        dm = {"SPY": _dm("SPY")}
        setups = build_option_setups(results, sr, dm)
        assert len(setups) == 1

    def test_setup_symbol_matches(self):
        results = [_qual_result("SPY")]
        sr = {"SPY": _structure("SPY", TREND, LOW_IV)}
        dm = {"SPY": _dm("SPY")}
        setups = build_option_setups(results, sr, dm)
        assert setups[0].symbol == "SPY"

    def test_etf_strike_distance(self):
        results = [_qual_result("SPY")]
        sr = {"SPY": _structure("SPY", TREND, NORMAL_IV)}
        dm = {"SPY": _dm("SPY")}
        setups = build_option_setups(results, sr, dm)
        assert setups[0].strike_distance == _MAX_STRIKE_DIST_ETF

    def test_stock_strike_distance(self):
        results = [_qual_result("AAPL")]
        sr = {"AAPL": _structure("AAPL", TREND, NORMAL_IV)}
        dm = {"AAPL": _dm("AAPL")}
        setups = build_option_setups(results, sr, dm)
        assert setups[0].strike_distance == _MAX_STRIKE_DIST_STK

    def test_exit_fields(self):
        results = [_qual_result("SPY")]
        sr = {"SPY": _structure("SPY", TREND, NORMAL_IV)}
        dm = {"SPY": _dm("SPY")}
        setup = build_option_setups(results, sr, dm)[0]
        assert setup.exit_profit_pct == 0.50
        assert setup.exit_loss == "full_debit"

    def test_long_low_iv_gets_bull_call(self):
        results = [_qual_result("SPY", direction="LONG")]
        sr = {"SPY": _structure("SPY", TREND, LOW_IV)}
        dm = {"SPY": _dm("SPY")}
        setup = build_option_setups(results, sr, dm)[0]
        assert setup.strategy == BULL_CALL_SPREAD

    def test_long_high_iv_gets_bull_put(self):
        results = [_qual_result("SPY", direction="LONG")]
        sr = {"SPY": _structure("SPY", TREND, HIGH_IV)}
        dm = {"SPY": _dm("SPY")}
        setup = build_option_setups(results, sr, dm)[0]
        assert setup.strategy == BULL_PUT_SPREAD

    def test_short_normal_iv_gets_bear_put(self):
        results = [_qual_result("NVDA", direction="SHORT")]
        sr = {"NVDA": _structure("NVDA", TREND, NORMAL_IV)}
        dm = {"NVDA": _dm("NVDA")}
        setup = build_option_setups(results, sr, dm)[0]
        assert setup.strategy == BEAR_PUT_SPREAD

    def test_missing_structure_skips(self):
        results = [_qual_result("SPY")]
        setups = build_option_setups(results, {}, {})
        assert setups == []

    def test_empty_input(self):
        assert build_option_setups([], {}, {}) == []


# ---------------------------------------------------------------------------
# audit.py — record builder
# ---------------------------------------------------------------------------

class TestBuildAuditRecord:
    def _base_record(self, outcome=OUTCOME_NO_TRADE):
        val = _val_summary()
        qual = _qual_summary(short_circuited=True, failure_reason="STAY_FLAT")
        return _build_record(
            run_at_utc=_NOW,
            date_str="2026-04-10",
            outcome=outcome,
            regime=_stay_flat(),
            validation_summary=val,
            qualification_summary=qual,
            option_setups=[],
            halt_reason=None,
            pushover_sent=False,
            report_path="reports/2026-04-10.md",
        )

    def test_record_is_dict(self):
        assert isinstance(self._base_record(), dict)

    def test_required_fields_present(self):
        record = self._base_record()
        required = [
            "run_at_utc", "date", "outcome",
            "regime", "posture", "confidence", "net_score", "vix_level",
            "symbols_validated", "symbols_total", "symbols_failed",
            "symbols_qualified", "symbols_watchlist", "symbols_excluded",
            "regime_short_circuited", "regime_failure_reason",
            "qualified_trades", "watchlist", "excluded_symbols",
            "halt_reason", "pushover_sent", "report_path",
        ]
        for field in required:
            assert field in record, f"Missing field: {field}"

    def test_outcome_set_correctly(self):
        assert self._base_record(OUTCOME_NO_TRADE)["outcome"] == OUTCOME_NO_TRADE
        assert self._base_record(OUTCOME_TRADE)["outcome"] == OUTCOME_TRADE
        assert self._base_record(OUTCOME_HALT)["outcome"] == OUTCOME_HALT

    def test_regime_fields_from_state(self):
        record = self._base_record()
        assert record["regime"] == TRANSITION
        assert record["posture"] == STAY_FLAT
        assert record["vix_level"] == pytest.approx(22.0)

    def test_validation_counts(self):
        record = self._base_record()
        assert record["symbols_validated"] == 20
        assert record["symbols_total"] == 20

    def test_qualified_trades_empty_on_no_trade(self):
        record = self._base_record()
        assert record["qualified_trades"] == []

    def test_halt_reason_null_on_no_trade(self):
        assert self._base_record()["halt_reason"] is None

    def test_pushover_sent_false(self):
        assert self._base_record()["pushover_sent"] is False

    def test_none_regime_serializes(self):
        val = _val_summary()
        record = _build_record(
            run_at_utc=_NOW, date_str="2026-04-10",
            outcome=OUTCOME_HALT, regime=None,
            validation_summary=val, qualification_summary=None,
            option_setups=[], halt_reason="test halt",
            pushover_sent=False, report_path="reports/2026-04-10.md",
        )
        assert record["regime"] is None
        assert record["halt_reason"] == "test halt"

    def test_record_is_json_serializable(self):
        record = self._base_record()
        dumped = json.dumps(record, sort_keys=True)
        loaded = json.loads(dumped)
        assert loaded["outcome"] == OUTCOME_NO_TRADE


# ---------------------------------------------------------------------------
# audit.py — file writer
# ---------------------------------------------------------------------------

class TestAuditFileWriter:
    def test_write_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        val = _val_summary()
        qual = _qual_summary(short_circuited=True, failure_reason="STAY_FLAT")
        write_audit_record(
            run_at_utc=_NOW, date_str="2026-04-10",
            outcome=OUTCOME_NO_TRADE,
            regime=_stay_flat(), validation_summary=val,
            qualification_summary=qual, option_setups=[],
            halt_reason=None, pushover_sent=False,
            report_path="reports/2026-04-10.md",
        )
        log_file = tmp_path / "logs" / "audit.jsonl"
        assert log_file.exists()

    def test_write_appends_not_overwrites(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        val = _val_summary()
        qual = _qual_summary(short_circuited=True, failure_reason="STAY_FLAT")

        for _ in range(3):
            write_audit_record(
                run_at_utc=_NOW, date_str="2026-04-10",
                outcome=OUTCOME_NO_TRADE,
                regime=_stay_flat(), validation_summary=val,
                qualification_summary=qual, option_setups=[],
                halt_reason=None, pushover_sent=False,
                report_path="reports/2026-04-10.md",
            )

        lines = (tmp_path / "logs" / "audit.jsonl").read_text().splitlines()
        assert len(lines) == 3

    def test_each_line_is_valid_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "logs").mkdir()
        val = _val_summary()
        qual = _qual_summary(short_circuited=True, failure_reason="STAY_FLAT")
        write_audit_record(
            run_at_utc=_NOW, date_str="2026-04-10",
            outcome=OUTCOME_NO_TRADE,
            regime=_stay_flat(), validation_summary=val,
            qualification_summary=qual, option_setups=[],
            halt_reason=None, pushover_sent=False,
            report_path="reports/2026-04-10.md",
        )
        line = (tmp_path / "logs" / "audit.jsonl").read_text().strip()
        record = json.loads(line)
        assert record["outcome"] == OUTCOME_NO_TRADE


# ---------------------------------------------------------------------------
# output.py — render_report
# ---------------------------------------------------------------------------

class TestRenderReport:
    def _no_trade_report(self):
        val = _val_summary()
        qual = _qual_summary(short_circuited=True, failure_reason="STAY_FLAT posture")
        return render_report(
            date_str="2026-04-10", run_at_utc=_NOW,
            regime=_stay_flat(), validation_summary=val,
            qualification_summary=qual, option_setups=[],
            outcome=OUTCOME_NO_TRADE,
        )

    def test_no_trade_contains_date(self):
        assert "2026-04-10" in self._no_trade_report()

    def test_no_trade_contains_regime(self):
        report = self._no_trade_report()
        assert TRANSITION in report
        assert STAY_FLAT in report

    def test_no_trade_contains_no_trade_label(self):
        assert "NO TRADE" in self._no_trade_report()

    def test_no_trade_contains_data_status(self):
        assert "Validated" in self._no_trade_report()

    def test_halt_report_contains_halt_label(self):
        val = _val_summary(validated=17, failed=3)
        report = render_report(
            date_str="2026-04-10", run_at_utc=_NOW,
            regime=None, validation_summary=val,
            qualification_summary=None, option_setups=[],
            outcome=OUTCOME_HALT,
            halt_reason="Failed: ^VIX (fetch error)",
        )
        assert "HALT" in report
        assert "^VIX" in report

    def test_trade_report_contains_strategy(self):
        result = _qual_result("SPY")
        qual = _qual_summary(qualified=[result])
        sr = {"SPY": _structure("SPY", TREND, NORMAL_IV)}
        dm = {"SPY": _dm("SPY")}
        setups = build_option_setups([result], sr, dm)
        val = _val_summary()

        report = render_report(
            date_str="2026-04-10", run_at_utc=_NOW,
            regime=_regime(), validation_summary=val,
            qualification_summary=qual, option_setups=setups,
            outcome=OUTCOME_TRADE,
        )
        assert "SPY" in report
        assert "BULL_CALL_SPREAD" in report
        assert "TRADES" in report
        assert "Exit:" in report

    def test_watchlist_section_appears(self):
        watchlist_result = QualificationResult(
            symbol="NVDA", qualified=False, watchlist=True,
            direction="LONG",
            gates_passed=["REGIME", "CONFIDENCE", "DIRECTION", "STRUCTURE",
                          "STOP_DEFINED", "STOP_DISTANCE", "RR_RATIO", "MAX_RISK"],
            gates_failed=["EARNINGS"],
            hard_failure=None,
            watchlist_reason="earnings within 5 calendar days",
            max_contracts=None, dollar_risk=None,
        )
        qual = _qual_summary(watchlist=[watchlist_result])
        report = render_report(
            date_str="2026-04-10", run_at_utc=_NOW,
            regime=_regime(), validation_summary=_val_summary(),
            qualification_summary=qual, option_setups=[],
            outcome=OUTCOME_NO_TRADE,
        )
        assert "WATCHLIST" in report
        assert "NVDA" in report

    def test_excluded_section_appears(self):
        qual = _qual_summary(excluded={"AAPL": "CHOP", "MSTR": "CHOP"})
        report = render_report(
            date_str="2026-04-10", run_at_utc=_NOW,
            regime=_regime(), validation_summary=_val_summary(),
            qualification_summary=qual, option_setups=[],
            outcome=OUTCOME_NO_TRADE,
        )
        assert "EXCLUDED" in report
        assert "AAPL" in report

    def test_confidence_in_header(self):
        report = self._no_trade_report()
        assert "conf=0.25" in report

    def test_vix_in_footer(self):
        report = self._no_trade_report()
        assert "22.0" in report


# ---------------------------------------------------------------------------
# output.py — send_pushover
# ---------------------------------------------------------------------------

class TestSendPushover:
    def test_skips_when_no_credentials(self):
        with patch.object(config, "PUSHOVER_USER_KEY", None):
            with patch.object(config, "PUSHOVER_APP_TOKEN", None):
                result = send_pushover("report text", "2026-04-10", OUTCOME_NO_TRADE)
        assert result is False

    def test_returns_true_on_200(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch.object(config, "PUSHOVER_USER_KEY", "test_user"):
            with patch.object(config, "PUSHOVER_APP_TOKEN", "test_token"):
                with patch("requests.post", return_value=mock_resp):
                    result = send_pushover("report", "2026-04-10", OUTCOME_NO_TRADE)
        assert result is True

    def test_returns_false_on_non_200(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "rate limited"
        with patch.object(config, "PUSHOVER_USER_KEY", "test_user"):
            with patch.object(config, "PUSHOVER_APP_TOKEN", "test_token"):
                with patch("requests.post", return_value=mock_resp):
                    result = send_pushover("report", "2026-04-10", OUTCOME_NO_TRADE)
        assert result is False

    def test_returns_false_on_exception(self):
        with patch.object(config, "PUSHOVER_USER_KEY", "test_user"):
            with patch.object(config, "PUSHOVER_APP_TOKEN", "test_token"):
                with patch("requests.post", side_effect=ConnectionError("timeout")):
                    result = send_pushover("report", "2026-04-10", OUTCOME_NO_TRADE)
        assert result is False
