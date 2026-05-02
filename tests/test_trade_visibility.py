from __future__ import annotations

import pytest

from cuttingboard.execution_policy import (
    POLICY_COOLDOWN,
    POLICY_LOW_CONFIDENCE,
    POLICY_MACRO_PRESSURE_CONFLICT,
    POLICY_ORB_INSIDE_RANGE,
)
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE, TradeDecision
from cuttingboard.trade_visibility import (
    VISIBILITY_ACTIVE,
    VISIBILITY_BLOCKED,
    VISIBILITY_NEAR_MISS,
    build_visibility_map,
)


def _decision(
    symbol: str = "SPY",
    *,
    policy_allowed: bool = True,
    policy_reason: str = "policy_allowed",
    status: str = ALLOW_TRADE,
    block_reason: str | None = None,
) -> TradeDecision:
    if status == BLOCK_TRADE and block_reason is None:
        block_reason = policy_reason
    return TradeDecision(
        ticker=symbol,
        direction="LONG",
        status=status,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=block_reason,
        policy_allowed=policy_allowed,
        policy_reason=policy_reason,
    )


def _market_map(symbol: str = "SPY", grade: str | None = "A") -> dict:
    if grade is None:
        return {"symbols": {}}
    return {"symbols": {symbol: {"grade": grade}}}


# ---------------------------------------------------------------------------
# R2 / R3: ACTIVE
# ---------------------------------------------------------------------------

def test_active_when_policy_allowed():
    result = build_visibility_map([_decision("SPY", policy_allowed=True)], _market_map("SPY", "A"))
    assert result["SPY"]["visibility_status"] == VISIBILITY_ACTIVE
    assert result["SPY"]["visibility_reason"] is None
    assert result["SPY"]["enable_conditions"] == []


def test_active_ignores_grade():
    result = build_visibility_map([_decision("SPY", policy_allowed=True)], _market_map("SPY", "F"))
    assert result["SPY"]["visibility_status"] == VISIBILITY_ACTIVE


# ---------------------------------------------------------------------------
# R2 / R3: NEAR_MISS — each known reason
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("reason,expected_enable", [
    (POLICY_MACRO_PRESSURE_CONFLICT, "macro_pressure must align with trade direction"),
    (POLICY_ORB_INSIDE_RANGE, "price must break ORB range"),
    (POLICY_COOLDOWN, "cooldown period must expire"),
    (POLICY_LOW_CONFIDENCE, "regime confidence must reach 0.60"),
])
@pytest.mark.parametrize("grade", ["A+", "A", "B"])
def test_near_miss_known_reasons(reason, expected_enable, grade):
    decision = _decision(
        "SPY",
        policy_allowed=False,
        policy_reason=reason,
        status=BLOCK_TRADE,
        block_reason=reason,
    )
    result = build_visibility_map([decision], _market_map("SPY", grade))
    vis = result["SPY"]
    assert vis["visibility_status"] == VISIBILITY_NEAR_MISS
    assert vis["visibility_reason"] == reason
    assert vis["enable_conditions"] == [expected_enable]


def test_near_miss_unknown_reason_produces_generic_enable():
    decision = _decision(
        "SPY",
        policy_allowed=False,
        policy_reason="some_novel_gate",
        status=BLOCK_TRADE,
        block_reason="some_novel_gate",
    )
    result = build_visibility_map([decision], _market_map("SPY", "A"))
    vis = result["SPY"]
    assert vis["visibility_status"] == VISIBILITY_NEAR_MISS
    assert vis["enable_conditions"] == ["blocking condition must resolve: some_novel_gate"]


# ---------------------------------------------------------------------------
# R2: BLOCKED — low grade
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grade", ["C", "D", "F"])
def test_blocked_low_grade(grade):
    decision = _decision(
        "SPY",
        policy_allowed=False,
        policy_reason=POLICY_COOLDOWN,
        status=BLOCK_TRADE,
        block_reason=POLICY_COOLDOWN,
    )
    result = build_visibility_map([decision], _market_map("SPY", grade))
    vis = result["SPY"]
    assert vis["visibility_status"] == VISIBILITY_BLOCKED
    assert vis["visibility_reason"] == POLICY_COOLDOWN
    assert vis["enable_conditions"] == []


def test_blocked_grade_none():
    decision = _decision(
        "SPY",
        policy_allowed=False,
        policy_reason=POLICY_COOLDOWN,
        status=BLOCK_TRADE,
        block_reason=POLICY_COOLDOWN,
    )
    result = build_visibility_map([decision], _market_map("SPY", None))
    assert result["SPY"]["visibility_status"] == VISIBILITY_BLOCKED


def test_blocked_symbol_not_in_market_map():
    decision = _decision(
        "NVDA",
        policy_allowed=False,
        policy_reason=POLICY_COOLDOWN,
        status=BLOCK_TRADE,
        block_reason=POLICY_COOLDOWN,
    )
    result = build_visibility_map([decision], _market_map("SPY", "A"))
    assert result["NVDA"]["visibility_status"] == VISIBILITY_BLOCKED


# ---------------------------------------------------------------------------
# R1: grade must come from market_map only
# ---------------------------------------------------------------------------

def test_grade_read_from_market_map_symbols():
    decision = _decision(
        "GLD",
        policy_allowed=False,
        policy_reason=POLICY_COOLDOWN,
        status=BLOCK_TRADE,
        block_reason=POLICY_COOLDOWN,
    )
    market_map = {"symbols": {"GLD": {"grade": "A+"}}}
    result = build_visibility_map([decision], market_map)
    assert result["GLD"]["visibility_status"] == VISIBILITY_NEAR_MISS


# ---------------------------------------------------------------------------
# R4: no mutation
# ---------------------------------------------------------------------------

def test_does_not_mutate_trade_decision():
    decision = _decision("SPY", policy_allowed=True)
    original_ticker = decision.ticker
    build_visibility_map([decision], _market_map())
    assert decision.ticker == original_ticker


def test_does_not_mutate_market_map():
    mm = {"symbols": {"SPY": {"grade": "A"}}}
    build_visibility_map([_decision("SPY")], mm)
    assert mm == {"symbols": {"SPY": {"grade": "A"}}}


# ---------------------------------------------------------------------------
# R4: return type and multi-symbol
# ---------------------------------------------------------------------------

def test_returns_dict_keyed_by_symbol():
    decisions = [
        _decision("SPY", policy_allowed=True),
        _decision(
            "NVDA",
            policy_allowed=False,
            policy_reason=POLICY_COOLDOWN,
            status=BLOCK_TRADE,
            block_reason=POLICY_COOLDOWN,
        ),
    ]
    mm = {"symbols": {"SPY": {"grade": "A"}, "NVDA": {"grade": "B"}}}
    result = build_visibility_map(decisions, mm)
    assert set(result.keys()) == {"SPY", "NVDA"}
    assert result["SPY"]["visibility_status"] == VISIBILITY_ACTIVE
    assert result["NVDA"]["visibility_status"] == VISIBILITY_NEAR_MISS


def test_empty_decisions_returns_empty_dict():
    result = build_visibility_map([], _market_map())
    assert result == {}


# ---------------------------------------------------------------------------
# enable_conditions invariants
# ---------------------------------------------------------------------------

def test_active_enable_conditions_empty():
    result = build_visibility_map([_decision("SPY", policy_allowed=True)], _market_map())
    assert result["SPY"]["enable_conditions"] == []


def test_blocked_enable_conditions_empty():
    decision = _decision(
        "SPY",
        policy_allowed=False,
        policy_reason=POLICY_COOLDOWN,
        status=BLOCK_TRADE,
        block_reason=POLICY_COOLDOWN,
    )
    result = build_visibility_map([decision], _market_map("SPY", "D"))
    assert result["SPY"]["enable_conditions"] == []


def test_enable_conditions_deterministic():
    decision = _decision(
        "SPY",
        policy_allowed=False,
        policy_reason=POLICY_MACRO_PRESSURE_CONFLICT,
        status=BLOCK_TRADE,
        block_reason=POLICY_MACRO_PRESSURE_CONFLICT,
    )
    mm = _market_map("SPY", "A")
    r1 = build_visibility_map([decision], mm)
    r2 = build_visibility_map([decision], mm)
    assert r1["SPY"]["enable_conditions"] == r2["SPY"]["enable_conditions"]
