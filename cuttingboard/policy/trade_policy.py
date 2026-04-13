"""Deterministic trade policy entry point."""

from cuttingboard.policy.mapper import map_options_expression
from cuttingboard.policy.models import MacroState, MarketQuality, TradeCandidate, TradeDecision
from cuttingboard.policy.rules import (
    check_market_gate,
    determine_posture,
    direction_matches_posture,
    is_mean_reversion_exception,
    risk_reward_is_valid,
    structure_is_valid,
    validate_candidate,
    validate_macro_state,
    validate_market_quality,
    validate_price_relationships,
)


def evaluate_trade(
    macro: MacroState,
    quality: MarketQuality,
    candidate: TradeCandidate,
) -> TradeDecision:
    validate_macro_state(macro)
    validate_market_quality(quality)
    validate_candidate(candidate)

    posture = determine_posture(macro)
    market_reason = check_market_gate(quality)
    if market_reason is not None:
        return _reject(posture, market_reason, candidate)

    if posture == "NEUTRAL":
        return _reject(posture, "NEUTRAL_POSTURE", candidate)

    price_reason = validate_price_relationships(candidate)
    if price_reason is not None:
        return _reject(posture, price_reason, candidate)

    mean_reversion = is_mean_reversion_exception(posture, candidate)
    if not direction_matches_posture(posture, candidate.direction) and not mean_reversion:
        return _reject(posture, "MACRO_CONFLICT", candidate)

    if not structure_is_valid(candidate):
        return _reject(posture, "NO_STRUCTURE", candidate)

    if not risk_reward_is_valid(candidate, require_high_rr=mean_reversion):
        return _reject(posture, "RR_INVALID", candidate)

    options_plan = map_options_expression(posture, candidate, macro.vix_regime)
    return TradeDecision(
        candidate=candidate,
        posture=posture,
        decision="APPROVED",
        reason=None,
        options_plan=options_plan,
    )


def _reject(posture: str, reason: str, candidate: TradeCandidate) -> TradeDecision:
    return TradeDecision(
        candidate=candidate,
        posture=posture,
        decision="REJECTED",
        reason=reason,
        options_plan=None,
    )
