"""
Tests for PRD-023 — Trade Policy Layer.

Covers: PolicyContext output for all three states, no qualification mutation.
"""

from __future__ import annotations

from cuttingboard import config
from cuttingboard.correlation import (
    ALIGNED,
    CONFLICT,
    NEUTRAL,
    CorrelationResult,
)
from cuttingboard.trade_policy import PolicyContext, evaluate_policy


def _corr(state: str) -> CorrelationResult:
    score = {ALIGNED: 1, NEUTRAL: 0, CONFLICT: -1}[state]
    modifier = {
        ALIGNED:  config.CORRELATION_RISK_MODIFIER_ALIGNED,
        NEUTRAL:  config.CORRELATION_RISK_MODIFIER_NEUTRAL,
        CONFLICT: config.CORRELATION_RISK_MODIFIER_CONFLICT,
    }[state]
    return CorrelationResult(
        gold_symbol="GLD",
        dollar_symbol="DX-Y.NYB",
        state=state,
        score=score,
        risk_modifier=modifier,
    )


class TestPolicyContextShape:
    def test_aligned_modifier(self):
        ctx = evaluate_policy(_corr(ALIGNED))
        assert ctx.risk_modifier == config.CORRELATION_RISK_MODIFIER_ALIGNED

    def test_aligned_note(self):
        ctx = evaluate_policy(_corr(ALIGNED))
        assert ctx.policy_note == "correlation_aligned"

    def test_neutral_modifier(self):
        ctx = evaluate_policy(_corr(NEUTRAL))
        assert ctx.risk_modifier == config.CORRELATION_RISK_MODIFIER_NEUTRAL

    def test_neutral_note(self):
        ctx = evaluate_policy(_corr(NEUTRAL))
        assert ctx.policy_note == "correlation_neutral"

    def test_conflict_modifier(self):
        ctx = evaluate_policy(_corr(CONFLICT))
        assert ctx.risk_modifier == config.CORRELATION_RISK_MODIFIER_CONFLICT

    def test_conflict_note(self):
        ctx = evaluate_policy(_corr(CONFLICT))
        assert ctx.policy_note == "correlation_conflict"

    def test_returns_policy_context(self):
        ctx = evaluate_policy(_corr(ALIGNED))
        assert isinstance(ctx, PolicyContext)

    def test_policy_context_is_frozen(self):
        import pytest
        ctx = evaluate_policy(_corr(ALIGNED))
        with pytest.raises((AttributeError, TypeError)):
            ctx.risk_modifier = 0.0  # type: ignore[misc]


class TestNoQualificationMutation:
    """AC3: correlation must not change qualification outputs."""

    def test_policy_context_has_no_qualification_fields(self):
        ctx = evaluate_policy(_corr(ALIGNED))
        for qual_attr in ("qualified", "rejected", "watchlist", "gates_passed", "gates_failed"):
            assert not hasattr(ctx, qual_attr), f"unexpected attr: {qual_attr}"

    def test_evaluate_policy_does_not_modify_correlation(self):
        corr = _corr(CONFLICT)
        original_state = corr.state
        original_score = corr.score
        evaluate_policy(corr)
        assert corr.state == original_state
        assert corr.score == original_score
