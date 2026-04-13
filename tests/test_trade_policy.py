from dataclasses import FrozenInstanceError

import pytest

from cuttingboard.policy import MacroState, TradeCandidate, evaluate_trade


def _macro(
    dxy_trend: str = "down",
    rates_direction: str = "down",
    vix_regime: str = "low",
    oil_shock: bool = False,
    index_structure: str = "trend",
) -> MacroState:
    return MacroState(
        dxy_trend=dxy_trend,
        rates_direction=rates_direction,
        vix_regime=vix_regime,
        oil_shock=oil_shock,
        index_structure=index_structure,
    )


def _candidate(
    direction: str = "long",
    entry_price: float = 105.0,
    stop_price: float = 103.0,
    target_price: float = 111.0,
    ema9: float = 104.0,
    ema21: float = 102.0,
    ema50: float = 100.0,
    atr14: float = 2.0,
    structure: str = "breakout",
) -> TradeCandidate:
    return TradeCandidate(
        ticker="SPY",
        direction=direction,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        ema9=ema9,
        ema21=ema21,
        ema50=ema50,
        atr14=atr14,
        structure=structure,
    )


def test_rejects_chaotic_market():
    decision = evaluate_trade(_macro(), "CHAOTIC", _candidate())
    assert decision.decision == "REJECTED"
    assert decision.reason == "MARKET_CHAOTIC"


def test_rejects_macro_conflict():
    decision = evaluate_trade(
        _macro(),
        "CLEAN",
        _candidate(direction="short", stop_price=107.0, target_price=99.0),
    )
    assert decision.decision == "REJECTED"
    assert decision.reason == "MACRO_CONFLICT"


def test_rejects_rr_below_two():
    decision = evaluate_trade(
        _macro(),
        "CLEAN",
        _candidate(target_price=108.0),
    )
    assert decision.decision == "REJECTED"
    assert decision.reason == "RR_INVALID"


def test_approves_valid_aligned_breakout():
    decision = evaluate_trade(_macro(), "CLEAN", _candidate())
    assert decision.decision == "APPROVED"
    assert decision.reason is None
    assert decision.options_plan is not None
    assert decision.options_plan.spread_type == "call_debit"
    assert decision.options_plan.duration == "weekly"


def test_every_reject_has_reason():
    decision = evaluate_trade(
        _macro(vix_regime="expanding"),
        "CLEAN",
        _candidate(),
    )
    assert decision.decision == "REJECTED"
    assert decision.reason is not None


def test_every_approval_has_options_plan():
    decision = evaluate_trade(_macro(), "MIXED", _candidate())
    assert decision.decision == "APPROVED"
    assert decision.options_plan is not None


def test_neutral_posture_always_rejects():
    decision = evaluate_trade(
        _macro(dxy_trend="flat", rates_direction="flat", vix_regime="low"),
        "CLEAN",
        _candidate(),
    )
    assert decision.posture == "NEUTRAL"
    assert decision.decision == "REJECTED"
    assert decision.reason == "NEUTRAL_POSTURE"


def test_mean_reversion_requires_rr_at_least_three():
    decision = evaluate_trade(
        _macro(),
        "CLEAN",
        _candidate(
            direction="short",
            structure="reversal",
            entry_price=105.0,
            stop_price=107.0,
            target_price=100.0,
            ema9=106.0,
            ema21=104.0,
            ema50=100.0,
        ),
    )
    assert decision.decision == "REJECTED"
    assert decision.reason == "MACRO_CONFLICT"


def test_mean_reversion_can_pass_with_rr_at_least_three():
    decision = evaluate_trade(
        _macro(),
        "CLEAN",
        _candidate(
            direction="short",
            structure="reversal",
            entry_price=105.0,
            stop_price=107.0,
            target_price=99.0,
            ema9=106.0,
            ema21=104.0,
            ema50=100.0,
        ),
    )
    assert decision.decision == "APPROVED"
    assert decision.options_plan is not None


def test_oil_shock_overrides_posture_to_short_bias():
    decision = evaluate_trade(
        _macro(dxy_trend="down", rates_direction="down", oil_shock=True),
        "CLEAN",
        _candidate(direction="short", structure="pullback", entry_price=102.0, stop_price=104.0, target_price=98.0, ema9=103.0, ema21=101.0, ema50=100.0),
    )
    assert decision.posture == "SHORT_BIAS"


def test_invalid_enum_raises_value_error():
    with pytest.raises(ValueError):
        evaluate_trade(_macro(dxy_trend="sideways"), "CLEAN", _candidate())


def test_outputs_are_frozen_dataclasses():
    decision = evaluate_trade(_macro(), "CLEAN", _candidate())
    with pytest.raises(FrozenInstanceError):
        decision.reason = "changed"
