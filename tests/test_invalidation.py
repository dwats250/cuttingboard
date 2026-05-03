"""Tests for invalidation gate (PRD-068)."""
from __future__ import annotations

import pytest

from cuttingboard.invalidation import (
    ACTION_AVOID_ENTRY,
    ACTION_HOLD_OK,
    ACTION_NO_ACTION,
    ACTION_UNKNOWN,
    STATUS_NOT_TRIGGERED,
    STATUS_TRIGGERED,
    STATUS_UNKNOWN,
    STATUS_WARNING,
    apply_invalidation_gate,
)
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE, TradeDecision


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _allow(symbol: str = "SPY", direction: str = "LONG") -> TradeDecision:
    return TradeDecision(
        ticker=symbol,
        direction=direction,
        status=ALLOW_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=1,
        dollar_risk=150.0,
        block_reason=None,
        policy_allowed=True,
        policy_reason="policy_allowed",
    )


def _block(symbol: str = "SPY", block_reason: str = "pre_existing") -> TradeDecision:
    return TradeDecision(
        ticker=symbol,
        direction="LONG",
        status=BLOCK_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=1,
        dollar_risk=150.0,
        block_reason=block_reason,
        policy_allowed=False,
        policy_reason=block_reason,
        decision_trace={"stage": "CHAIN_VALIDATION", "source": "chain_validation", "reason": block_reason},
    )


def _thesis(status: str, block_reason: str | None = None) -> dict:
    return {
        "symbol": "SPY",
        "direction": "LONG",
        "catalyst": "macro:RISK_ON",
        "confirmation": "MACRO_CONFIRMED",
        "invalidation": "stop at 97.00",
        "status": status,
        "block_reason": block_reason,
    }


# ---------------------------------------------------------------------------
# R1 — guidance shape
# ---------------------------------------------------------------------------

def test_guidance_shape_all_keys_present():
    decision = _allow()
    thesis_map = {"SPY": _thesis("VALID")}
    _, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    g = guidance_map["SPY"]
    for key in ("status", "action", "reason", "triggered_by", "thesis_status"):
        assert key in g, f"missing key: {key}"


def test_guidance_status_within_allowed_set():
    decision = _allow()
    thesis_map = {"SPY": _thesis("VALID")}
    _, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    from cuttingboard.invalidation import VALID_STATUSES, VALID_ACTIONS
    assert guidance_map["SPY"]["status"] in VALID_STATUSES
    assert guidance_map["SPY"]["action"] in VALID_ACTIONS


# ---------------------------------------------------------------------------
# R2 — TRIGGERED converts ALLOW_TRADE to BLOCK_TRADE
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("thesis_status", ["INCOMPLETE", "CONFLICTED"])
def test_triggered_converts_allow_to_block(thesis_status):
    decision = _allow()
    thesis_map = {"SPY": _thesis(thesis_status, block_reason=f"THESIS_{thesis_status}")}
    decisions, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    result = decisions[0]
    assert result.status == BLOCK_TRADE
    assert result.block_reason == "INVALIDATION_TRIGGERED"
    assert result.policy_allowed is False
    assert result.policy_reason == "invalidation_gate_blocked"
    assert guidance_map["SPY"]["status"] == STATUS_TRIGGERED
    assert guidance_map["SPY"]["action"] == ACTION_AVOID_ENTRY


def test_triggered_decision_trace_fields():
    decision = _allow()
    thesis_map = {"SPY": _thesis("INCOMPLETE", block_reason="THESIS_INCOMPLETE")}
    decisions, _ = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    trace = decisions[0].decision_trace
    assert trace["stage"] == "INVALIDATION_GATE"
    assert trace["source"] == "invalidation"
    assert trace["reason"] == "INVALIDATION_TRIGGERED"


def test_block_reason_equals_decision_trace_reason():
    decision = _allow()
    thesis_map = {"SPY": _thesis("CONFLICTED", block_reason="THESIS_CONFLICTED")}
    decisions, _ = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    d = decisions[0]
    assert d.block_reason == d.decision_trace["reason"]


# ---------------------------------------------------------------------------
# R3 — WARNING leaves ALLOW_TRADE unchanged
# ---------------------------------------------------------------------------

def test_warning_does_not_change_allow_decision():
    decision = _allow()
    # thesis block_reason set but status is VALID — WARNING from block_reason path
    thesis_map = {"SPY": {**_thesis("VALID"), "block_reason": "some_advisory"}}
    decisions, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    assert decisions[0].status == ALLOW_TRADE
    assert guidance_map["SPY"]["status"] == STATUS_WARNING


def test_warning_direction_pressure_conflict_no_block():
    decision = _allow(direction="LONG")
    thesis_map = {"SPY": _thesis("VALID")}
    decisions, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_OFF")
    assert decisions[0].status == ALLOW_TRADE
    assert guidance_map["SPY"]["status"] == STATUS_WARNING
    assert guidance_map["SPY"]["action"] == ACTION_NO_ACTION


# ---------------------------------------------------------------------------
# R4 — no active position assumed
# ---------------------------------------------------------------------------

def test_guidance_does_not_reference_open_position():
    decision = _allow()
    thesis_map = {"SPY": _thesis("VALID")}
    _, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    guidance_str = str(guidance_map["SPY"])
    assert "position" not in guidance_str.lower()
    assert "open" not in guidance_str.lower()


# ---------------------------------------------------------------------------
# R5 — trigger sources
# ---------------------------------------------------------------------------

def test_incomplete_thesis_triggers():
    decision = _allow()
    thesis_map = {"SPY": _thesis("INCOMPLETE", "THESIS_INCOMPLETE")}
    _, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    assert guidance_map["SPY"]["status"] == STATUS_TRIGGERED
    assert guidance_map["SPY"]["triggered_by"] == "thesis.status=INCOMPLETE"


def test_conflicted_thesis_triggers():
    decision = _allow()
    thesis_map = {"SPY": _thesis("CONFLICTED", "THESIS_CONFLICTED")}
    _, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    assert guidance_map["SPY"]["status"] == STATUS_TRIGGERED
    assert guidance_map["SPY"]["triggered_by"] == "thesis.status=CONFLICTED"


def test_pressure_conflict_long_risk_off_is_warning():
    decision = _allow("SPY", "LONG")
    thesis_map = {"SPY": _thesis("VALID")}
    _, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_OFF")
    assert guidance_map["SPY"]["status"] == STATUS_WARNING
    assert guidance_map["SPY"]["triggered_by"] == "overall_pressure"


def test_pressure_conflict_short_risk_on_is_warning():
    decision = _allow("SPY", "SHORT")
    thesis_map = {"SPY": _thesis("VALID")}
    _, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    assert guidance_map["SPY"]["status"] == STATUS_WARNING


def test_valid_thesis_aligned_pressure_is_not_triggered():
    decision = _allow("SPY", "LONG")
    thesis_map = {"SPY": _thesis("VALID")}
    _, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    assert guidance_map["SPY"]["status"] == STATUS_NOT_TRIGGERED
    assert guidance_map["SPY"]["action"] == ACTION_HOLD_OK


# ---------------------------------------------------------------------------
# R6 — UNKNOWN does not block
# ---------------------------------------------------------------------------

def test_unknown_does_not_block():
    decision = _allow()
    # No thesis for this symbol
    decisions, guidance_map = apply_invalidation_gate([decision], {}, "RISK_ON")
    assert decisions[0].status == ALLOW_TRADE
    assert guidance_map["SPY"]["status"] == STATUS_UNKNOWN
    assert guidance_map["SPY"]["action"] == ACTION_UNKNOWN
    assert guidance_map["SPY"]["reason"] == "INSUFFICIENT_DETERMINISTIC_INPUTS"
    assert guidance_map["SPY"]["triggered_by"] is None


def test_unknown_thesis_status_not_triggered():
    decision = _allow()
    thesis_map = {"SPY": _thesis("UNKNOWN")}
    decisions, guidance_map = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    assert decisions[0].status == ALLOW_TRADE
    # UNKNOWN thesis with no pressure conflict → NOT_TRIGGERED
    assert guidance_map["SPY"]["status"] == STATUS_NOT_TRIGGERED


# ---------------------------------------------------------------------------
# R7 — gate never overwrites an already-BLOCK_TRADE decision
# ---------------------------------------------------------------------------

def test_existing_block_not_modified():
    blocked = _block("SPY", "pre_existing")
    decisions, guidance_map = apply_invalidation_gate([blocked], {}, "RISK_ON")
    result = decisions[0]
    assert result.status == BLOCK_TRADE
    assert result.block_reason == "pre_existing"
    # No guidance produced for already-blocked decisions
    assert "SPY" not in guidance_map


def test_gate_does_not_touch_block_when_thesis_triggered():
    blocked = _block("SPY", "pre_existing")
    thesis_map = {"SPY": _thesis("INCOMPLETE", "THESIS_INCOMPLETE")}
    decisions, guidance_map = apply_invalidation_gate([blocked], thesis_map, "RISK_ON")
    result = decisions[0]
    assert result.block_reason == "pre_existing"
    assert result.decision_trace["stage"] == "CHAIN_VALIDATION"
    assert "SPY" not in guidance_map


# ---------------------------------------------------------------------------
# R8 — historical candidates without invalidation_guidance readable
# ---------------------------------------------------------------------------

def test_contract_candidate_without_invalidation_guidance_is_null():
    """A historical candidate dict that predates invalidation_guidance key is readable."""
    candidate: dict = {
        "symbol": "SPY",
        "decision_status": "ALLOW_TRADE",
        "block_reason": None,
    }
    # Simulate reading a legacy candidate — key may be absent
    guidance = candidate.get("invalidation_guidance", None)
    assert guidance is None  # must not raise


def test_contract_builder_missing_symbol_in_map_returns_null(monkeypatch):
    """_build_trade_candidates returns invalidation_guidance=null for missing symbol."""
    from cuttingboard.contract import _build_trade_candidates
    from unittest.mock import MagicMock

    decision = _allow("NVDA")
    mock_result = MagicMock()
    mock_result.symbol = "NVDA"
    mock_result.direction = "LONG"
    mock_result.entry_mode = "DIRECT"

    mock_setup = MagicMock()
    mock_setup.symbol = "NVDA"
    mock_setup.strategy = "CALLS"
    mock_setup.dte = 7

    qual = MagicMock()
    qual.qualified_trades = [mock_result]

    candidates = _build_trade_candidates(
        qual,
        [mock_setup],
        {},
        [decision],
        {},
        {},
        None,
        {},  # empty invalidation_guidance_map — symbol absent
    )
    assert candidates[0]["invalidation_guidance"] is None


# ---------------------------------------------------------------------------
# R9 — gate runs after thesis gate (ordering tested in test_operationalization)
# ---------------------------------------------------------------------------

def test_gate_returns_correct_tuple_shape():
    decision = _allow()
    result = apply_invalidation_gate([decision], {}, "RISK_ON")
    assert isinstance(result, tuple)
    assert len(result) == 2
    decisions, guidance_map = result
    assert isinstance(decisions, list)
    assert isinstance(guidance_map, dict)


# ---------------------------------------------------------------------------
# R10 — no new TradeDecision enum values
# ---------------------------------------------------------------------------

def test_no_new_status_values_on_blocked_decision():
    decision = _allow()
    thesis_map = {"SPY": _thesis("INCOMPLETE", "THESIS_INCOMPLETE")}
    decisions, _ = apply_invalidation_gate([decision], thesis_map, "RISK_ON")
    from cuttingboard.trade_decision import VALID_DECISION_STATUSES
    assert decisions[0].status in VALID_DECISION_STATUSES


# ---------------------------------------------------------------------------
# Multiple candidates — mixed outcomes
# ---------------------------------------------------------------------------

def test_mixed_candidates_handled_correctly():
    allow_spy = _allow("SPY", "LONG")
    allow_nvda = _allow("NVDA", "SHORT")
    block_aapl = _block("AAPL", "pre_existing")

    thesis_map = {
        "SPY": _thesis("INCOMPLETE", "THESIS_INCOMPLETE"),
        "NVDA": _thesis("VALID"),
    }

    decisions, guidance_map = apply_invalidation_gate(
        [allow_spy, allow_nvda, block_aapl], thesis_map, "RISK_ON"
    )

    spy_result = next(d for d in decisions if d.ticker == "SPY")
    nvda_result = next(d for d in decisions if d.ticker == "NVDA")
    aapl_result = next(d for d in decisions if d.ticker == "AAPL")

    assert spy_result.status == BLOCK_TRADE
    assert spy_result.block_reason == "INVALIDATION_TRIGGERED"

    assert nvda_result.status == ALLOW_TRADE

    assert aapl_result.status == BLOCK_TRADE
    assert aapl_result.block_reason == "pre_existing"

    assert "SPY" in guidance_map
    assert "NVDA" in guidance_map
    assert "AAPL" not in guidance_map
