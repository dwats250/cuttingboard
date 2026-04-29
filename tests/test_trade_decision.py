from __future__ import annotations

import math

import pytest

from cuttingboard.chain_validation import ChainValidationResult, MANUAL_CHECK, VALIDATED
from cuttingboard.options import OptionSetup
from cuttingboard.qualification import QualificationResult, TradeCandidate
from cuttingboard.trade_decision import (
    ALLOW_TRADE,
    BLOCK_TRADE,
    TradeDecision,
    create_trade_decision,
)


def _candidate() -> TradeCandidate:
    return TradeCandidate(
        symbol="SPY",
        direction="LONG",
        entry_price=100.0,
        stop_price=97.0,
        target_price=106.0,
        spread_width=0.75,
        has_earnings_soon=False,
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


def test_trade_decision_is_frozen():
    decision = create_trade_decision(_candidate(), _result(), _setup(), _chain(VALIDATED, None))
    with pytest.raises((AttributeError, TypeError)):
        decision.entry = 101.0  # type: ignore[misc]


def test_create_trade_decision_allow_trade():
    decision = create_trade_decision(_candidate(), _result(), _setup(), _chain(VALIDATED, None))
    assert decision == TradeDecision(
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
    )
    assert decision.policy_allowed is True
    assert decision.policy_reason == "policy_not_evaluated"
    assert decision.size_multiplier == 1.0


def test_create_trade_decision_block_trade_uses_reason():
    decision = create_trade_decision(
        _candidate(),
        _result(),
        _setup(),
        _chain(MANUAL_CHECK, "fixture mode skips live chain validation"),
    )
    assert decision.status == BLOCK_TRADE
    assert decision.block_reason == "fixture mode skips live chain validation"
    assert decision.policy_allowed is False


def test_create_trade_decision_block_trade_falls_back_to_classification():
    decision = create_trade_decision(
        _candidate(),
        _result(),
        _setup(),
        _chain(MANUAL_CHECK, None),
    )
    assert decision.status == BLOCK_TRADE
    assert decision.block_reason == MANUAL_CHECK


def test_trade_decision_rejects_non_finite_numeric_fields():
    with pytest.raises(ValueError, match="entry must be finite"):
        TradeDecision(
            ticker="SPY",
            direction="LONG",
            status=ALLOW_TRADE,
            entry=math.inf,
            stop=97.0,
            target=106.0,
            r_r=2.0,
            contracts=2,
            dollar_risk=150.0,
            block_reason=None,
        )


def test_trade_decision_rejects_invalid_block_reason_for_allow():
    with pytest.raises(ValueError, match="ALLOW_TRADE"):
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
            block_reason="should not exist",
        )


def test_trade_decision_requires_block_reason_for_block():
    with pytest.raises(ValueError, match="BLOCK_TRADE"):
        TradeDecision(
            ticker="SPY",
            direction="LONG",
            status=BLOCK_TRADE,
            entry=100.0,
            stop=97.0,
            target=106.0,
            r_r=2.0,
            contracts=2,
            dollar_risk=150.0,
            block_reason=None,
        )


def test_trade_decision_rejects_policy_block_with_allow_status():
    with pytest.raises(ValueError, match="policy_allowed=False"):
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
            policy_allowed=False,
            policy_reason="low_confidence",
            size_multiplier=0.0,
        )
