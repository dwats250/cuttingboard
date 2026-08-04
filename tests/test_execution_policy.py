from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from cuttingboard.execution_policy import (
    ExecutionSessionState,
    OrbPolicyState,
    PolicyDecision,
    apply_execution_policy,
    apply_execution_policy_to_decisions,
    evaluate_execution_policy,
    load_execution_session_state,
    size_multiplier_for_confidence,
)
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE, TradeDecision


RUN_AT = datetime(2026, 4, 29, 14, 0, tzinfo=timezone.utc)


def _decision(symbol: str = "SPY", direction: str = "LONG") -> TradeDecision:
    return TradeDecision(
        ticker=symbol,
        direction=direction,
        status=ALLOW_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=None,
    )


def _apply(
    *,
    confidence: float = 0.80,
    market_regime: str = "RISK_ON",
    posture: str = "AGGRESSIVE_LONG",
    session_state: ExecutionSessionState = ExecutionSessionState(),
    orb_state: OrbPolicyState | None = None,
) -> TradeDecision:
    return apply_execution_policy(
        _decision(),
        market_regime=market_regime,
        posture=posture,
        confidence=confidence,
        timestamp=RUN_AT,
        session_state=session_state,
        orb_state=orb_state,
    )


def test_low_confidence_blocks_and_zero_sizes() -> None:
    decision = _apply(confidence=0.58)
    assert decision.status == BLOCK_TRADE
    assert decision.policy_allowed is False
    assert decision.policy_reason == "low_confidence"
    assert decision.size_multiplier == 0.0


def test_chaotic_regime_blocks() -> None:
    decision = _apply(market_regime="CHAOTIC")
    assert decision.status == BLOCK_TRADE
    assert decision.policy_reason == "chaotic_regime"


def test_stay_flat_blocks() -> None:
    decision = _apply(posture="STAY_FLAT")
    assert decision.status == BLOCK_TRADE
    assert decision.policy_reason == "stay_flat"


def test_orb_inside_range_blocks_without_continuation() -> None:
    decision = _apply(orb_state=OrbPolicyState(price=100.0, orb_high=101.0, orb_low=99.0))
    assert decision.status == BLOCK_TRADE
    assert decision.policy_reason == "orb_inside_range"


def test_orb_unavailable_preserves_existing_allow_decision() -> None:
    decision = _apply(orb_state=None)
    assert decision.status == ALLOW_TRADE
    assert decision.policy_allowed is True
    assert decision.policy_reason == "orb_unavailable"


def test_continuation_breakout_bypasses_orb_range() -> None:
    decision = _apply(
        orb_state=OrbPolicyState(
            price=100.0,
            orb_high=101.0,
            orb_low=99.0,
            continuation_breakout=True,
        )
    )
    assert decision.status == ALLOW_TRADE
    assert decision.policy_reason == "policy_allowed"


def test_size_multiplier_bands() -> None:
    assert size_multiplier_for_confidence(0.80) == 1.0
    assert size_multiplier_for_confidence(0.74) == 0.75
    assert size_multiplier_for_confidence(0.64) == 0.50
    assert size_multiplier_for_confidence(0.58) == 0.0


# --- PRD-285 / CB-04: retained-mechanism tests -----------------------------
# The daily-limit, loss-lockout, and cooldown predicates are RETAINED (dormant)
# so a future trustworthy execution/fill carrier can re-activate them by
# supplying real, non-neutral ExecutionSessionState. These tests inject
# synthetic non-neutral state DIRECTLY (not via the loader, which is now
# dormant) to prove the predicates still function. In production the loader
# returns neutral state and no same-run mutation occurs, so none of these
# predicates can fire — see the dormancy tests above.
def test_session_trade_limit_blocks_third_trade() -> None:
    decision = _apply(session_state=ExecutionSessionState(prior_trade_count=2))
    assert decision.status == BLOCK_TRADE
    assert decision.policy_reason == "session_trade_limit"


def test_loss_lockout_blocks_after_two_consecutive_losses() -> None:
    decision = _apply(session_state=ExecutionSessionState(consecutive_losses=2))
    assert decision.status == BLOCK_TRADE
    assert decision.policy_reason == "loss_lockout"


def test_cooldown_blocks_before_15_minutes() -> None:
    state = ExecutionSessionState(last_trade_at_utc=RUN_AT - timedelta(minutes=14, seconds=59))
    decision = _apply(session_state=state)
    assert decision.status == BLOCK_TRADE
    assert decision.policy_reason == "cooldown"


def test_cooldown_allows_at_15_minutes() -> None:
    state = ExecutionSessionState(last_trade_at_utc=RUN_AT - timedelta(minutes=15))
    decision = _apply(session_state=state)
    assert decision.status == ALLOW_TRADE


def test_same_run_recommendations_do_not_block_second_candidate() -> None:
    # PRD-285 / CB-04: an ALLOW_TRADE recommendation is not an executed trade,
    # so it must not increment the in-run trade count or start a cooldown for a
    # later same-run candidate. Both otherwise-valid candidates remain
    # ALLOW_TRADE, and input order is preserved (R4, R6). This inverts the
    # former defect-encoding assertion (decisions[1] blocked by cooldown).
    decisions = apply_execution_policy_to_decisions(
        [_decision("SPY"), _decision("QQQ")],
        market_regime="RISK_ON",
        posture="AGGRESSIVE_LONG",
        confidence=0.80,
        timestamp=RUN_AT,
        session_state=ExecutionSessionState(),
        orb_states={
            "SPY": OrbPolicyState(price=102.0, orb_high=101.0, orb_low=99.0),
            "QQQ": OrbPolicyState(price=202.0, orb_high=201.0, orb_low=199.0),
        },
    )
    assert [d.ticker for d in decisions] == ["SPY", "QQQ"]  # order preserved (R6)
    assert decisions[0].status == ALLOW_TRADE
    assert decisions[0].policy_reason == "policy_allowed"
    assert decisions[1].status == ALLOW_TRADE
    assert decisions[1].policy_reason == "policy_allowed"


def test_three_valid_same_run_candidates_do_not_trip_daily_limit() -> None:
    # PRD-285 / CB-04: with EXECUTION_POLICY_MAX_TRADES_PER_DAY == 2, three
    # otherwise-valid same-run recommendations would trip the daily limit only
    # if the same-run trade-count accumulation were restored. Dormant: all three
    # remain ALLOW_TRADE (discriminates the `trade_count += 1` mutation).
    decisions = apply_execution_policy_to_decisions(
        [_decision("SPY"), _decision("QQQ"), _decision("IWM")],
        market_regime="RISK_ON",
        posture="AGGRESSIVE_LONG",
        confidence=0.80,
        timestamp=RUN_AT,
        session_state=ExecutionSessionState(),
        orb_states={
            "SPY": OrbPolicyState(price=102.0, orb_high=101.0, orb_low=99.0),
            "QQQ": OrbPolicyState(price=202.0, orb_high=201.0, orb_low=199.0),
            "IWM": OrbPolicyState(price=302.0, orb_high=301.0, orb_low=299.0),
        },
    )
    assert [d.ticker for d in decisions] == ["SPY", "QQQ", "IWM"]
    assert all(d.status == ALLOW_TRADE for d in decisions)
    assert all(d.policy_reason == "policy_allowed" for d in decisions)


def test_load_session_state_ignores_prior_allow_trade_recommendations(tmp_path) -> None:
    # PRD-285 / CB-04: prior audit rows with decision_status == ALLOW_TRADE are
    # recommendations, not executed trades. They must not increment
    # prior_trade_count (R1) or establish last_trade_at_utc (R2). This inverts
    # the former defect-encoding assertion (prior_trade_count == 2 / last == prior).
    audit_path = tmp_path / "audit.jsonl"
    evaluation_path = tmp_path / "evaluation.jsonl"
    prior = RUN_AT - timedelta(hours=1)
    audit_path.write_text(
        json.dumps(
            {
                "date": "2026-04-29",
                "run_at_utc": prior.isoformat(),
                "trade_decisions": [
                    {"decision_status": ALLOW_TRADE},
                    {"decision_status": ALLOW_TRADE},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    state = load_execution_session_state(
        run_at_utc=RUN_AT,
        session_date="2026-04-29",
        audit_log_path=audit_path,
        evaluation_log_path=evaluation_path,
    )

    assert state.prior_trade_count == 0
    assert state.last_trade_at_utc is None


def test_load_session_state_ignores_hypothetical_evaluation_losses(tmp_path) -> None:
    # PRD-285 / CB-04: evaluation.jsonl carries hypothetical forward-evaluation
    # outcomes of recommendations, not realized P&L on executed positions. They
    # must not populate consecutive_losses / drive live loss lockout (R3). This
    # inverts the former defect-encoding assertion (consecutive_losses == 2).
    audit_path = tmp_path / "audit.jsonl"
    evaluation_path = tmp_path / "evaluation.jsonl"
    audit_path.write_text("", encoding="utf-8")
    rows = [
        {
            "evaluated_at_utc": (RUN_AT - timedelta(minutes=40)).isoformat(),
            "decision_run_at_utc": (RUN_AT - timedelta(minutes=50)).isoformat(),
            "symbol": "SPY",
            "evaluation": {"result": "STOP_HIT", "R_multiple": -1.0},
        },
        {
            "evaluated_at_utc": (RUN_AT - timedelta(minutes=20)).isoformat(),
            "decision_run_at_utc": (RUN_AT - timedelta(minutes=30)).isoformat(),
            "symbol": "QQQ",
            "evaluation": {"result": "STOP_HIT", "R_multiple": -1.0},
        },
    ]
    evaluation_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    state = load_execution_session_state(
        run_at_utc=RUN_AT,
        session_date="2026-04-29",
        audit_log_path=audit_path,
        evaluation_log_path=evaluation_path,
    )

    assert state.consecutive_losses == 0


def test_load_session_state_fully_neutral_with_recommendation_and_hypothetical(tmp_path) -> None:
    # PRD-285 / CB-04: even with BOTH prior ALLOW_TRADE recommendations AND
    # hypothetical losses present, the loader reports fully neutral state — no
    # trustworthy execution/fill carrier exists (R7).
    audit_path = tmp_path / "audit.jsonl"
    evaluation_path = tmp_path / "evaluation.jsonl"
    prior = RUN_AT - timedelta(hours=1)
    audit_path.write_text(
        json.dumps(
            {
                "date": "2026-04-29",
                "run_at_utc": prior.isoformat(),
                "trade_decisions": [{"decision_status": ALLOW_TRADE}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    evaluation_path.write_text(
        json.dumps(
            {
                "evaluated_at_utc": (RUN_AT - timedelta(minutes=20)).isoformat(),
                "decision_run_at_utc": (RUN_AT - timedelta(minutes=30)).isoformat(),
                "symbol": "SPY",
                "evaluation": {"result": "STOP_HIT", "R_multiple": -1.0},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    state = load_execution_session_state(
        run_at_utc=RUN_AT,
        session_date="2026-04-29",
        audit_log_path=audit_path,
        evaluation_log_path=evaluation_path,
    )

    assert state == ExecutionSessionState()


# --- PRD-063: macro pressure tests ---

def _eval_pressure(direction: str, pressure: str, confidence: float = 0.80) -> PolicyDecision:
    return evaluate_execution_policy(
        _decision(direction=direction),
        market_regime="RISK_ON",
        posture="AGGRESSIVE_LONG",
        confidence=confidence,
        timestamp=RUN_AT,
        session_state=ExecutionSessionState(),
        orb_state=None,
        overall_pressure=pressure,
    )


def test_pressure_unknown_no_change_long() -> None:
    result = _eval_pressure("LONG", "UNKNOWN")
    assert result.allowed is True
    assert result.size_multiplier == 1.0


def test_pressure_neutral_no_change_short() -> None:
    result = _eval_pressure("SHORT", "NEUTRAL")
    assert result.allowed is True
    assert result.size_multiplier == 1.0


def test_pressure_mixed_reduces_size_long() -> None:
    result = _eval_pressure("LONG", "MIXED")
    assert result.allowed is True
    assert result.size_multiplier == pytest.approx(0.75)


def test_pressure_mixed_reduces_size_short() -> None:
    result = _eval_pressure("SHORT", "MIXED")
    assert result.allowed is True
    assert result.size_multiplier == pytest.approx(0.75)


def test_pressure_risk_off_blocks_long() -> None:
    result = _eval_pressure("LONG", "RISK_OFF")
    assert result.allowed is False
    assert result.reason == "macro_pressure_conflict"


def test_pressure_risk_off_reduces_short() -> None:
    result = _eval_pressure("SHORT", "RISK_OFF")
    assert result.allowed is True
    assert result.size_multiplier == pytest.approx(0.5)


def test_pressure_risk_on_blocks_short() -> None:
    result = _eval_pressure("SHORT", "RISK_ON")
    assert result.allowed is False
    assert result.reason == "macro_pressure_conflict"


def test_pressure_risk_on_reduces_long() -> None:
    result = _eval_pressure("LONG", "RISK_ON")
    assert result.allowed is True
    assert result.size_multiplier == pytest.approx(0.5)


def test_pressure_invalid_raises_value_error() -> None:
    with pytest.raises(ValueError):
        _eval_pressure("LONG", "GARBAGE")


def test_pressure_multiplies_existing_size_not_replaces() -> None:
    # confidence 0.70 → size 0.75; MIXED → 0.75 × 0.75 = 0.5625
    result = _eval_pressure("LONG", "MIXED", confidence=0.70)
    assert result.size_multiplier == pytest.approx(0.75 * 0.75)


def test_pressure_does_not_run_on_pre_blocked_decision() -> None:
    blocked = TradeDecision(
        ticker="SPY",
        direction="LONG",
        status=BLOCK_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason="prior_block",
    )
    result = evaluate_execution_policy(
        blocked,
        market_regime="RISK_ON",
        posture="AGGRESSIVE_LONG",
        confidence=0.80,
        timestamp=RUN_AT,
        session_state=ExecutionSessionState(),
        overall_pressure="RISK_OFF",
    )
    assert result.allowed is False
    assert result.reason == "prior_block"


def test_pressure_default_unknown_preserves_existing_behavior() -> None:
    # Calling without overall_pressure should behave identically to before
    result = evaluate_execution_policy(
        _decision(),
        market_regime="RISK_ON",
        posture="AGGRESSIVE_LONG",
        confidence=0.80,
        timestamp=RUN_AT,
        session_state=ExecutionSessionState(),
    )
    assert result.allowed is True
    assert result.size_multiplier == 1.0


# ---------------------------------------------------------------------------
# PRD-284 — full A2 materialization: apply size_multiplier to the position;
# block at EXECUTION_POLICY when the position rounds to zero.
# ---------------------------------------------------------------------------

from cuttingboard.execution_policy import POLICY_SIZE_ROUNDS_TO_ZERO  # noqa: E402
from cuttingboard.trade_decision import decision_is_actionable  # noqa: E402


def _mk(contracts: int, dollar_risk: float, direction: str = "LONG") -> TradeDecision:
    return TradeDecision(
        ticker="SPY",
        direction=direction,
        status=ALLOW_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=contracts,
        dollar_risk=dollar_risk,
        block_reason=None,
    )


def _materialize(decision: TradeDecision, *, confidence: float) -> TradeDecision:
    # NEUTRAL pressure => macro factor 1.0, so the finalized multiplier is the
    # confidence-tier multiplier alone (isolates the materialization arithmetic).
    return apply_execution_policy(
        decision,
        market_regime="RISK_ON",
        posture="AGGRESSIVE_LONG",
        confidence=confidence,
        timestamp=RUN_AT,
        session_state=ExecutionSessionState(),
        overall_pressure="NEUTRAL",
    )


def test_prd284_multiplier_one_preserves_value_for_value() -> None:
    # confidence >= 0.80 => multiplier 1.0 => unity short-circuit: contracts and
    # dollar_risk untouched (structural R3). A materialization mutation must not
    # perturb the multiplier-1.0 path.
    out = _materialize(_mk(4, 800.0), confidence=0.85)
    assert out.status == ALLOW_TRADE
    assert out.contracts == 4
    assert out.dollar_risk == 800.0
    assert out.size_multiplier == 1.0
    assert out.policy_allowed is True


def test_prd284_positive_reduction_two_times_half_to_one() -> None:
    # 2 contracts x 0.5 => floor(1.0) = 1; dollar_risk 300/2*1 = 150.0.
    out = _materialize(_mk(2, 300.0), confidence=0.65)
    assert out.status == ALLOW_TRADE
    assert out.size_multiplier == 0.5
    assert out.contracts == 1
    assert out.dollar_risk == 150.0
    assert out.policy_allowed is True
    assert decision_is_actionable(out) is True


def test_prd284_multi_contract_floor() -> None:
    # 3 contracts x 0.75 => floor(2.25) = 2 (floor, not round/ceil).
    out = _materialize(_mk(3, 900.0), confidence=0.70)
    assert out.size_multiplier == 0.75
    assert out.contracts == 2
    assert out.dollar_risk == 600.0  # 900/3*2


def test_prd284_dollar_risk_proportional_cents_rounding() -> None:
    # 3 contracts $100 x 0.75 => 2 contracts; 100/3*2 = 66.666... -> round 66.67.
    out = _materialize(_mk(3, 100.0), confidence=0.70)
    assert out.contracts == 2
    assert out.dollar_risk == 66.67


def test_prd284_size_rounds_to_zero_blocks_at_execution_policy() -> None:
    # 1 contract x 0.5 => floor(0.5) = 0 => block, do NOT round up to 1.
    out = _materialize(_mk(1, 150.0), confidence=0.65)
    assert out.status == BLOCK_TRADE
    assert out.block_reason == POLICY_SIZE_ROUNDS_TO_ZERO
    assert out.block_reason == "size_rounds_to_zero"
    assert out.policy_reason == "size_rounds_to_zero"
    assert out.policy_allowed is False
    assert out.size_multiplier == 0.0
    assert out.decision_trace == {
        "stage": "EXECUTION_POLICY",
        "source": "execution_policy",
        "reason": "size_rounds_to_zero",
    }
    # contracts >= 1 invariant preserved on the blocked decision.
    assert out.contracts == 1
    # Non-actionable: excluded from run outcome and top_trades.
    assert decision_is_actionable(out) is False


def test_prd284_existing_policy_block_precedence_over_materialization() -> None:
    # A pre-materialization policy block (low_confidence) keeps its own reason;
    # materialization / size_rounds_to_zero never overrides an existing block.
    out = _materialize(_mk(1, 150.0), confidence=0.55)
    assert out.status == BLOCK_TRADE
    assert out.policy_reason == "low_confidence"
    assert out.block_reason != POLICY_SIZE_ROUNDS_TO_ZERO
    assert out.size_multiplier == 0.0


def test_prd284_reason_and_stage_distinct_from_prd283() -> None:
    # CB-03 (this PRD) vs CB-02 (PRD-283): distinct reason literal and stage.
    from cuttingboard.execution_policy import POLICY_STAGE
    from cuttingboard.options import OPTIONS_SIZING, SMALLEST_CONTRACT_EXCEEDS_BUDGET

    assert POLICY_SIZE_ROUNDS_TO_ZERO == "size_rounds_to_zero"
    assert POLICY_SIZE_ROUNDS_TO_ZERO != SMALLEST_CONTRACT_EXCEEDS_BUDGET
    assert POLICY_STAGE == "EXECUTION_POLICY"
    assert POLICY_STAGE != OPTIONS_SIZING
