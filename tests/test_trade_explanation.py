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
)
from cuttingboard.trade_explanation import build_explanation_map


def _decision(
    symbol: str = "SPY",
    *,
    policy_allowed: bool = True,
    policy_reason: str = "policy_allowed",
    status: str = ALLOW_TRADE,
    direction: str = "LONG",
    block_reason: str | None = None,
) -> TradeDecision:
    if status == BLOCK_TRADE and block_reason is None:
        block_reason = policy_reason
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
        policy_allowed=policy_allowed,
        policy_reason=policy_reason,
    )


def _vis(symbol: str, status: str) -> dict[str, dict]:
    return {symbol: {"visibility_status": status, "visibility_reason": None, "enable_conditions": []}}


# ---------------------------------------------------------------------------
# R1: explanation does not duplicate candidate-level fields
# ---------------------------------------------------------------------------

def test_explanation_keys_are_only_explanation_fields():
    d = _decision("SPY", policy_allowed=True)
    result = build_explanation_map([d], _vis("SPY", VISIBILITY_ACTIVE), "RISK_ON")
    expl = result["SPY"]
    assert set(expl.keys()) == {"block_reasons", "macro_alignment", "required_changes"}


# ---------------------------------------------------------------------------
# R2: block_reasons
# ---------------------------------------------------------------------------

def test_block_reasons_empty_when_active():
    d = _decision("SPY", policy_allowed=True, policy_reason="policy_allowed")
    result = build_explanation_map([d], _vis("SPY", VISIBILITY_ACTIVE), "UNKNOWN")
    assert result["SPY"]["block_reasons"] == []


def test_block_reasons_populated_when_blocked():
    d = _decision("SPY", status=BLOCK_TRADE, policy_allowed=False, policy_reason="chaotic_regime")
    result = build_explanation_map([d], _vis("SPY", VISIBILITY_BLOCKED), "UNKNOWN")
    assert result["SPY"]["block_reasons"] == ["chaotic_regime"]


def test_block_reasons_populated_when_near_miss():
    d = _decision("SPY", status=BLOCK_TRADE, policy_allowed=False, policy_reason=POLICY_COOLDOWN)
    result = build_explanation_map([d], _vis("SPY", VISIBILITY_NEAR_MISS), "UNKNOWN")
    assert result["SPY"]["block_reasons"] == [POLICY_COOLDOWN]


# ---------------------------------------------------------------------------
# R3: macro_alignment
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pressure,direction,expected", [
    ("RISK_ON",  "LONG",  "ALIGNED"),
    ("RISK_ON",  "SHORT", "MISALIGNED"),
    ("RISK_OFF", "SHORT", "ALIGNED"),
    ("RISK_OFF", "LONG",  "MISALIGNED"),
    ("MIXED",    "LONG",  None),
    ("MIXED",    "SHORT", None),
    ("NEUTRAL",  "LONG",  None),
    ("NEUTRAL",  "SHORT", None),
    ("UNKNOWN",  "LONG",  None),
    ("UNKNOWN",  "SHORT", None),
])
def test_macro_alignment_table(pressure, direction, expected):
    d = _decision("SPY", policy_allowed=True, direction=direction)
    result = build_explanation_map([d], _vis("SPY", VISIBILITY_ACTIVE), pressure)
    assert result["SPY"]["macro_alignment"] == expected


# ---------------------------------------------------------------------------
# R4: required_changes — only for NEAR_MISS
# ---------------------------------------------------------------------------

def test_required_changes_empty_for_active():
    d = _decision("SPY", policy_allowed=True)
    result = build_explanation_map([d], _vis("SPY", VISIBILITY_ACTIVE), "RISK_ON")
    assert result["SPY"]["required_changes"] == []


def test_required_changes_empty_for_blocked():
    d = _decision("SPY", status=BLOCK_TRADE, policy_allowed=False, policy_reason="chaotic_regime")
    result = build_explanation_map([d], _vis("SPY", VISIBILITY_BLOCKED), "RISK_ON")
    assert result["SPY"]["required_changes"] == []


@pytest.mark.parametrize("policy_reason,expected_str", [
    (POLICY_MACRO_PRESSURE_CONFLICT, "macro_pressure must align with trade direction"),
    (POLICY_ORB_INSIDE_RANGE,        "price must break ORB range"),
    (POLICY_COOLDOWN,                "cooldown period must expire"),
    (POLICY_LOW_CONFIDENCE,          "regime confidence must reach 0.60"),
    ("unknown_reason",               "blocking condition must resolve: unknown_reason"),
])
def test_required_changes_templates_for_near_miss(policy_reason, expected_str):
    d = _decision("SPY", status=BLOCK_TRADE, policy_allowed=False, policy_reason=policy_reason)
    result = build_explanation_map([d], _vis("SPY", VISIBILITY_NEAR_MISS), "UNKNOWN")
    assert result["SPY"]["required_changes"] == [expected_str]


# ---------------------------------------------------------------------------
# R5: function signature — no mutation
# ---------------------------------------------------------------------------

def test_does_not_mutate_visibility_map():
    d = _decision("SPY", policy_allowed=True)
    vis = _vis("SPY", VISIBILITY_ACTIVE)
    original_vis = dict(vis)
    build_explanation_map([d], vis, "RISK_ON")
    assert vis == original_vis


def test_empty_decisions_returns_empty_map():
    result = build_explanation_map([], {}, "RISK_ON")
    assert result == {}


def test_multiple_symbols():
    decisions = [
        _decision("SPY", policy_allowed=True, direction="LONG"),
        _decision("QQQ", status=BLOCK_TRADE, policy_allowed=False, policy_reason=POLICY_COOLDOWN, direction="SHORT"),
    ]
    vis = {
        "SPY": {"visibility_status": VISIBILITY_ACTIVE, "visibility_reason": None, "enable_conditions": []},
        "QQQ": {"visibility_status": VISIBILITY_NEAR_MISS, "visibility_reason": POLICY_COOLDOWN, "enable_conditions": []},
    }
    result = build_explanation_map(decisions, vis, "RISK_ON")

    assert result["SPY"]["block_reasons"] == []
    assert result["SPY"]["macro_alignment"] == "ALIGNED"
    assert result["SPY"]["required_changes"] == []

    assert result["QQQ"]["block_reasons"] == [POLICY_COOLDOWN]
    assert result["QQQ"]["macro_alignment"] == "MISALIGNED"
    assert result["QQQ"]["required_changes"] == ["cooldown period must expire"]
