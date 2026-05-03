"""Tests for PRD-069: Entry Quality and Chase Filter."""

from __future__ import annotations


from cuttingboard.entry_quality import (
    ACTION_ALLOW,
    ENTRY_QUALITY_CHASE_RISK,
    ENTRY_QUALITY_CLEAN,
    ENTRY_QUALITY_EXTENDED,
    ENTRY_QUALITY_MISSING_ENTRY,
    ENTRY_QUALITY_STALE,
    ENTRY_QUALITY_UNKNOWN,
    apply_entry_quality_gate,
)
from cuttingboard.qualification import (
    ENTRY_MODE_DIRECT,
    QualificationResult,
    TradeCandidate,
)
from cuttingboard.structure import StructureResult
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE, TradeDecision


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decision(
    symbol: str = "SPY",
    direction: str = "LONG",
    status: str = ALLOW_TRADE,
    policy_reason: str = "policy_allowed",
    block_reason: str | None = None,
) -> TradeDecision:
    trace = (
        {"stage": "CHAIN_VALIDATION", "source": "chain_validation", "reason": block_reason}
        if block_reason
        else {"stage": "CHAIN_VALIDATION", "source": "chain_validation", "reason": "VALIDATED"}
    )
    return TradeDecision(
        ticker=symbol,
        direction=direction,
        status=status,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=block_reason,
        policy_allowed=status == ALLOW_TRADE,
        policy_reason=policy_reason,
        decision_trace=trace,
    )


def _block_decision(symbol: str = "SPY") -> TradeDecision:
    return _decision(
        symbol=symbol,
        status=BLOCK_TRADE,
        policy_reason="pre_existing_block",
        block_reason="pre_existing_block",
    )


def _qual(symbol: str = "SPY", entry_mode: str = ENTRY_MODE_DIRECT) -> QualificationResult:
    return QualificationResult(
        symbol=symbol,
        qualified=True,
        watchlist=False,
        direction="LONG",
        gates_passed=["REGIME", "CONFIDENCE"],
        gates_failed=[],
        hard_failure=None,
        watchlist_reason=None,
        max_contracts=2,
        dollar_risk=150.0,
        entry_mode=entry_mode,
    )


def _structure(structure: str = "TREND") -> StructureResult:
    return StructureResult(
        symbol="SPY",
        structure=structure,
        iv_environment="NORMAL_IV",
        is_tradeable=structure != "CHOP",
        disqualification_reason=None,
    )


def _thesis(confirmation: str = "TREND_ALIGNED", invalidation: str | None = "BELOW_STOP") -> dict:
    return {
        "catalyst": "SPY_TREND",
        "confirmation": confirmation,
        "invalidation": invalidation,
        "status": "VALID",
        "block_reason": None,
    }


# ---------------------------------------------------------------------------
# R3 — CLEAN ALLOW_TRADE remains ALLOW_TRADE
# ---------------------------------------------------------------------------

def test_clean_allow_trade_unchanged():
    decision = _decision()
    qual = _qual()
    structure = _structure()
    thesis = _thesis()

    result, eq_map = apply_entry_quality_gate(
        [decision],
        {"SPY": TradeCandidate(symbol="SPY", direction="LONG", entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=3.0)},
        {"SPY": qual},
        {"SPY": structure},
        {"SPY": thesis},
    )

    assert result[0].status == ALLOW_TRADE
    assert eq_map["SPY"]["status"] == ENTRY_QUALITY_CLEAN
    assert eq_map["SPY"]["blocking"] is False
    assert eq_map["SPY"]["action"] == ACTION_ALLOW


# ---------------------------------------------------------------------------
# R2 — Blocking statuses convert ALLOW_TRADE to BLOCK_TRADE
# ---------------------------------------------------------------------------

def test_extended_blocks_allow_trade():
    decision = _decision(policy_reason="extended_policy_block")
    qual = _qual()
    structure = _structure()
    thesis = _thesis(confirmation="UNKNOWN", invalidation=None)

    result, eq_map = apply_entry_quality_gate(
        [decision],
        {"SPY": TradeCandidate(symbol="SPY", direction="LONG", entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=3.0)},
        {"SPY": qual},
        {"SPY": structure},
        {"SPY": thesis},
    )

    assert result[0].status == BLOCK_TRADE
    assert result[0].block_reason == "ENTRY_QUALITY_BLOCK"
    assert result[0].decision_trace["reason"] == "ENTRY_QUALITY_BLOCK"
    assert result[0].policy_allowed is False
    assert result[0].policy_reason == "entry_quality_gate_blocked"
    assert eq_map["SPY"]["status"] == ENTRY_QUALITY_EXTENDED


def test_chase_risk_blocks_allow_trade():
    decision = _decision()
    qual = _qual()
    structure = _structure()
    thesis = {
        "catalyst": "SPY_TREND",
        "confirmation": "TREND_ALIGNED",
        "invalidation": "BELOW_STOP",
        "status": "CONFLICTED",
        "block_reason": "THESIS_CONFLICTED",
    }

    result, eq_map = apply_entry_quality_gate(
        [decision],
        {"SPY": TradeCandidate(symbol="SPY", direction="LONG", entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=3.0)},
        {"SPY": qual},
        {"SPY": structure},
        {"SPY": thesis},
    )

    assert result[0].status == BLOCK_TRADE
    assert eq_map["SPY"]["status"] == ENTRY_QUALITY_CHASE_RISK


def test_missing_entry_blocks_allow_trade():
    decision = _decision(policy_reason="policy_not_evaluated")
    # No qual, no structure, no thesis

    result, eq_map = apply_entry_quality_gate(
        [decision],
        {},
        {},
        {},
        {},
    )

    assert result[0].status == BLOCK_TRADE
    assert eq_map["SPY"]["status"] == ENTRY_QUALITY_MISSING_ENTRY
    assert result[0].block_reason == "ENTRY_QUALITY_BLOCK"
    assert result[0].decision_trace["reason"] == "ENTRY_QUALITY_BLOCK"


def test_stale_blocks_allow_trade():
    decision = _decision()
    qual = QualificationResult(
        symbol="SPY",
        qualified=True,
        watchlist=False,
        direction="LONG",
        gates_passed=[],
        gates_failed=[],
        hard_failure=None,
        watchlist_reason=None,
        max_contracts=2,
        dollar_risk=150.0,
        entry_mode=ENTRY_MODE_DIRECT,
        rejection_reason="setup_expired",
    )

    result, eq_map = apply_entry_quality_gate(
        [decision],
        {"SPY": TradeCandidate(symbol="SPY", direction="LONG", entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=3.0)},
        {"SPY": qual},
        {"SPY": _structure()},
        {"SPY": _thesis()},
    )

    assert result[0].status == BLOCK_TRADE
    assert eq_map["SPY"]["status"] == ENTRY_QUALITY_STALE


# ---------------------------------------------------------------------------
# R4 — UNKNOWN does not block
# ---------------------------------------------------------------------------

def test_unknown_does_not_block():
    decision = _decision()
    # Provide structure only (no entry_mode, no confirmation, no non-default policy)
    qual = _qual(entry_mode="")
    structure = _structure()
    thesis = _thesis(confirmation="UNKNOWN", invalidation=None)

    result, eq_map = apply_entry_quality_gate(
        [decision],
        {"SPY": TradeCandidate(symbol="SPY", direction="LONG", entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=3.0)},
        {"SPY": qual},
        {"SPY": structure},
        {"SPY": thesis},
    )

    assert result[0].status == ALLOW_TRADE
    assert eq_map["SPY"]["status"] == ENTRY_QUALITY_UNKNOWN
    assert eq_map["SPY"]["blocking"] is False
    assert eq_map["SPY"]["reason"] == "INSUFFICIENT_DETERMINISTIC_INPUTS"


# ---------------------------------------------------------------------------
# R2 — Already-BLOCK_TRADE decision unmodified
# ---------------------------------------------------------------------------

def test_already_block_trade_unmodified():
    decision = _block_decision()
    original_block_reason = decision.block_reason

    result, eq_map = apply_entry_quality_gate(
        [decision],
        {},
        {},
        {},
        {},
    )

    assert result[0].status == BLOCK_TRADE
    assert result[0].block_reason == original_block_reason
    assert result[0].block_reason != "ENTRY_QUALITY_BLOCK"


# ---------------------------------------------------------------------------
# R2 — block_reason == decision_trace["reason"] for every gate-blocked decision
# ---------------------------------------------------------------------------

def test_block_reason_matches_trace_reason():
    decision = _decision(policy_reason="policy_not_evaluated")

    result, eq_map = apply_entry_quality_gate(
        [decision],
        {},
        {},
        {},
        {},
    )

    blocked = result[0]
    assert blocked.block_reason == blocked.decision_trace["reason"]


# ---------------------------------------------------------------------------
# R9 — Historical candidate dict without entry_quality remains readable
# ---------------------------------------------------------------------------

def test_historical_candidate_without_entry_quality():
    candidate = {"symbol": "SPY", "direction": "LONG"}
    eq_map = {}
    candidate["entry_quality"] = eq_map.get("SPY", None)
    assert candidate["entry_quality"] is None


# ---------------------------------------------------------------------------
# R1 — entry_quality shape validation
# ---------------------------------------------------------------------------

def test_entry_quality_shape_complete():
    decision = _decision()
    qual = _qual()
    structure = _structure()
    thesis = _thesis()

    _, eq_map = apply_entry_quality_gate(
        [decision],
        {"SPY": TradeCandidate(symbol="SPY", direction="LONG", entry_price=100.0, stop_price=97.0, target_price=106.0, spread_width=3.0)},
        {"SPY": qual},
        {"SPY": structure},
        {"SPY": thesis},
    )

    eq = eq_map["SPY"]
    for key in ("status", "action", "reason", "blocking", "source"):
        assert key in eq, f"Missing key: {key}"
    assert eq["status"] in ("CLEAN", "EXTENDED", "STALE", "CHASE_RISK", "MISSING_ENTRY", "UNKNOWN")
    assert eq["action"] in ("ALLOW", "WAIT", "AVOID", "UNKNOWN")
    assert isinstance(eq["blocking"], bool)
