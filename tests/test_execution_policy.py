from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from cuttingboard.execution_policy import (
    ExecutionSessionState,
    OrbPolicyState,
    apply_execution_policy,
    apply_execution_policy_to_decisions,
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


def test_first_valid_candidate_remains_allow_trade() -> None:
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
    assert decisions[0].status == ALLOW_TRADE
    assert decisions[0].policy_reason == "policy_allowed"
    assert decisions[1].status == BLOCK_TRADE
    assert decisions[1].policy_reason == "cooldown"


def test_load_session_state_counts_same_session_allow_trades(tmp_path) -> None:
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

    assert state.prior_trade_count == 2
    assert state.last_trade_at_utc == prior


def test_load_session_state_counts_consecutive_evaluated_losses(tmp_path) -> None:
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

    assert state.consecutive_losses == 2
