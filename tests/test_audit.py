from __future__ import annotations

from datetime import datetime, timezone

from cuttingboard.audit import _build_record
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
