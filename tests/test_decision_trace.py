from __future__ import annotations

import pytest

from cuttingboard.chain_validation import ChainValidationResult, MANUAL_CHECK, VALIDATED
from cuttingboard.options import OptionSetup
from cuttingboard.qualification import QualificationResult, TradeCandidate
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE, TradeDecision, create_trade_decision


def _candidate() -> TradeCandidate:
    return TradeCandidate(
        symbol="SPY",
        direction="LONG",
        entry_price=100.0,
        stop_price=97.0,
        target_price=106.0,
        spread_width=0.75,
    )


def _result() -> QualificationResult:
    return QualificationResult(
        symbol="SPY",
        qualified=True,
        watchlist=False,
        direction="LONG",
        gates_passed=["REGIME"],
        gates_failed=[],
        hard_failure=None,
        watchlist_reason=None,
        max_contracts=2,
        dollar_risk=150.0,
    )


def _setup() -> OptionSetup:
    return OptionSetup(
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
        max_contracts=2,
        dollar_risk=150.0,
        exit_profit_pct=0.5,
        exit_loss="full_debit",
    )


def _chain(classification: str, reason: str | None) -> ChainValidationResult:
    return ChainValidationResult(
        symbol="SPY",
        classification=classification,
        reason=reason,
        spread_pct=None,
        open_interest=None,
        volume=None,
        expiry_used=None,
        data_source=None,
    )


def test_allow_trade_uses_canonical_trace():
    decision = create_trade_decision(_candidate(), _result(), _setup(), _chain(VALIDATED, None))
    assert decision.status == ALLOW_TRADE
    assert decision.block_reason is None
    assert decision.decision_trace == {
        "stage": "CHAIN_VALIDATION",
        "source": "chain_validation",
        "reason": "TOP_TRADE_VALIDATED",
    }


def test_block_trade_uses_chain_reason_in_trace():
    decision = create_trade_decision(
        _candidate(),
        _result(),
        _setup(),
        _chain(MANUAL_CHECK, "fixture mode skips live chain validation"),
    )
    assert decision.status == BLOCK_TRADE
    assert decision.block_reason == "fixture mode skips live chain validation"
    assert decision.decision_trace == {
        "stage": "CHAIN_VALIDATION",
        "source": "chain_validation",
        "reason": "fixture mode skips live chain validation",
    }


def test_block_trade_falls_back_to_chain_classification():
    decision = create_trade_decision(
        _candidate(),
        _result(),
        _setup(),
        _chain(MANUAL_CHECK, None),
    )
    assert decision.block_reason == MANUAL_CHECK
    assert decision.decision_trace["reason"] == MANUAL_CHECK


def test_decision_trace_requires_exact_keys():
    with pytest.raises(ValueError, match="decision_trace"):
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
            decision_trace={"stage": "CHAIN_VALIDATION", "reason": "TOP_TRADE_VALIDATED"},
        )


def test_decision_trace_requires_non_empty_string_values():
    with pytest.raises(ValueError, match="decision_trace.reason"):
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
            decision_trace={
                "stage": "CHAIN_VALIDATION",
                "source": "chain_validation",
                "reason": "",
            },
        )
