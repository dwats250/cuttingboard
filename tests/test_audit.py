from __future__ import annotations

from datetime import datetime, timezone

from cuttingboard.audit import _build_record
from cuttingboard.options import OptionSetup
from cuttingboard.qualification import QualificationResult, QualificationSummary
from cuttingboard.trade_decision import ALLOW_TRADE, TradeDecision
from cuttingboard.validation import ValidationSummary


RUN_AT = datetime(2026, 4, 29, 14, 0, tzinfo=timezone.utc)


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


def test_audit_trade_decisions_include_execution_policy_fields() -> None:
    record = _build_record(
        run_at_utc=RUN_AT,
        date_str="2026-04-29",
        outcome="TRADE",
        regime=None,
        validation_summary=_validation_summary(),
        qualification_summary=None,
        option_setups=[],
        trade_decisions=[
            TradeDecision(
                ticker="SPY",
                direction="LONG",
                status=ALLOW_TRADE,
                entry=100.0,
                stop=97.0,
                target=106.0,
                r_r=2.0,
                contracts=2,
                dollar_risk=150.0,
                block_reason=None,
                policy_allowed=True,
                policy_reason="policy_allowed",
                size_multiplier=1.0,
            )
        ],
        halt_reason=None,
        alert_sent=False,
        report_path="reports/2026-04-29.md",
    )

    decision = record["trade_decisions"][0]
    assert decision["policy_allowed"] is True
    assert decision["policy_reason"] == "policy_allowed"
    assert decision["size_multiplier"] == 1.0


def test_audit_qualified_trades_sizing_sources_from_option_setup() -> None:
    """PRD-253 R2: qualified_trades[].contracts/.dollar_risk source from the
    correlation/strategy-adjusted OptionSetup, not the pre-adjustment
    QualificationResult, so this block agrees with trade_decisions[] for
    the same candidate (same run, same symbol).

    Fixture discriminates the two source objects: QualificationResult
    carries pre-adjustment sizing (max_contracts=2, dollar_risk=150.0)
    while OptionSetup carries distinct post-adjustment sizing
    (max_contracts=1, dollar_risk=60.0), simulating a correlation
    risk_modifier < 1.0 (PRD-023/PRD-157) or a PRD-251 strategy-aware
    max-loss cut below spread_width.
    """
    result = QualificationResult(
        symbol="SPY",
        qualified=True,
        watchlist=False,
        direction="LONG",
        gates_passed=["REGIME", "CONFIDENCE", "DIRECTION", "STRUCTURE"],
        gates_failed=[],
        hard_failure=None,
        watchlist_reason=None,
        max_contracts=2,
        dollar_risk=150.0,
    )
    setup = OptionSetup(
        symbol="SPY",
        strategy="BULL_CALL_SPREAD",
        direction="LONG",
        structure="TREND",
        iv_environment="NORMAL_IV",
        long_strike="1_ITM",
        short_strike="ATM",
        strike_distance=5.0,
        spread_width=0.75,
        dte=21,
        max_contracts=1,
        dollar_risk=60.0,
        exit_profit_pct=0.5,
        exit_loss="full_debit",
    )
    qual = QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=[result],
        watchlist=[],
        excluded={},
        symbols_evaluated=1,
        symbols_qualified=1,
        symbols_watchlist=0,
        symbols_excluded=0,
    )
    record = _build_record(
        run_at_utc=RUN_AT,
        date_str="2026-04-29",
        outcome="TRADE",
        regime=None,
        validation_summary=_validation_summary(),
        qualification_summary=qual,
        option_setups=[setup],
        trade_decisions=[],
        halt_reason=None,
        alert_sent=False,
        report_path="reports/2026-04-29.md",
    )

    entry = record["qualified_trades"][0]
    assert entry["contracts"] == 1
    assert entry["dollar_risk"] == 60.0


def _qualification_summary(
    continuation_audit: dict | None,
) -> QualificationSummary:
    return QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=[],
        watchlist=[],
        excluded={},
        symbols_evaluated=0,
        symbols_qualified=0,
        symbols_watchlist=0,
        symbols_excluded=0,
        continuation_audit=continuation_audit,
    )


def test_audit_record_persists_continuation_audit() -> None:
    # PRD-169 R1: the EXPANSION continuation-rejection tally is persisted
    # verbatim onto the canonical pipeline record.
    continuation_audit = {"total_candidates": 3, "accepted": 1, "NO_BREAKOUT": 2}
    record = _build_record(
        run_at_utc=RUN_AT,
        date_str="2026-04-29",
        outcome="TRADE",
        regime=None,
        validation_summary=_validation_summary(),
        qualification_summary=_qualification_summary(continuation_audit),
        option_setups=[],
        trade_decisions=[],
        halt_reason=None,
        alert_sent=False,
        report_path="reports/2026-04-29.md",
    )

    assert record["continuation_audit"] == continuation_audit


def test_audit_record_continuation_audit_none_when_no_summary() -> None:
    # PRD-169 R1: a None qualification summary yields a None field, not a
    # missing key.
    record = _build_record(
        run_at_utc=RUN_AT,
        date_str="2026-04-29",
        outcome="NO_TRADE",
        regime=None,
        validation_summary=_validation_summary(),
        qualification_summary=None,
        option_setups=[],
        trade_decisions=[],
        halt_reason=None,
        alert_sent=False,
        report_path="reports/2026-04-29.md",
    )

    assert record["continuation_audit"] is None
