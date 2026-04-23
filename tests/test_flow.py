"""
Tests for PRD-013 — Flow Alignment Soft Gate (cuttingboard/flow.py).

All tests use static fixtures. No runtime data, no I/O.
Acceptance criteria:
  1. PASS LONG + dominant bearish spec flow → WATCHLIST
  2. PASS SHORT + dominant bullish spec flow → WATCHLIST
  3. PASS + matching spec flow → PASS
  4. PASS + HEDGE flow → PASS
  5. PASS + MIXED flow → PASS
  6. PASS + no flow data → PASS
  7. WATCHLIST remains WATCHLIST
  8. REJECT remains REJECT
  9. Deterministic output
 10. HEDGE classification uses full print set (pre-speculative filter)
"""

import pytest

from cuttingboard.flow import FlowPrint, apply_flow_gate, _classify_strike
from cuttingboard.qualification import QualificationResult, ENTRY_MODE_DIRECT

# ---------------------------------------------------------------------------
# Constants for fixtures
# ---------------------------------------------------------------------------

_UNDERLYING = 450.0
_OTM_CALL_STRIKE = 460.0   # distance = +2.2%  → OTM CALL
_OTM_PUT_STRIKE  = 440.0   # distance = -2.2%  → OTM PUT
_ITM_CALL_STRIKE = 440.0   # distance = -2.2%  → ITM CALL
_ITM_PUT_STRIKE  = 460.0   # distance = +2.2%  → ITM PUT
_LARGE_PREMIUM   = 600_000
_SMALL_PREMIUM   = 300_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pass_result(symbol="SPY", direction="LONG") -> QualificationResult:
    return QualificationResult(
        symbol=symbol,
        qualified=True,
        watchlist=False,
        direction=direction,
        gates_passed=["REGIME", "CONFIDENCE", "DIRECTION", "STRUCTURE",
                      "STOP_DEFINED", "STOP_DISTANCE", "RR_RATIO",
                      "MAX_RISK", "EARNINGS", "EXTENSION", "TIME"],
        gates_failed=[],
        hard_failure=None,
        watchlist_reason=None,
        max_contracts=1,
        dollar_risk=150.0,
    )


def _watchlist_result(symbol="SPY", direction="LONG") -> QualificationResult:
    return QualificationResult(
        symbol=symbol,
        qualified=False,
        watchlist=True,
        direction=direction,
        gates_passed=["REGIME", "CONFIDENCE", "DIRECTION", "STRUCTURE"],
        gates_failed=["RR_RATIO"],
        hard_failure=None,
        watchlist_reason="R:R 1.5 below 2.0 minimum",
        max_contracts=1,
        dollar_risk=150.0,
    )


def _reject_result(symbol="SPY", direction="LONG") -> QualificationResult:
    return QualificationResult(
        symbol=symbol,
        qualified=False,
        watchlist=False,
        direction=direction,
        gates_passed=[],
        gates_failed=["REGIME"],
        hard_failure="REGIME: posture is STAY_FLAT",
        watchlist_reason=None,
        max_contracts=None,
        dollar_risk=None,
    )


def _otm_ask_call(symbol="SPY", premium=_LARGE_PREMIUM) -> FlowPrint:
    return FlowPrint(
        symbol=symbol, strike=_OTM_CALL_STRIKE, option_type="CALL",
        premium=premium, side="ASK", is_sweep=True,
        underlying_price=_UNDERLYING,
    )


def _otm_ask_put(symbol="SPY", premium=_LARGE_PREMIUM) -> FlowPrint:
    return FlowPrint(
        symbol=symbol, strike=_OTM_PUT_STRIKE, option_type="PUT",
        premium=premium, side="ASK", is_sweep=True,
        underlying_price=_UNDERLYING,
    )


def _itm_call(symbol="SPY", premium=_LARGE_PREMIUM) -> FlowPrint:
    return FlowPrint(
        symbol=symbol, strike=_ITM_CALL_STRIKE, option_type="CALL",
        premium=premium, side="ASK", is_sweep=False,
        underlying_price=_UNDERLYING,
    )


def _itm_put(symbol="SPY", premium=_LARGE_PREMIUM) -> FlowPrint:
    return FlowPrint(
        symbol=symbol, strike=_ITM_PUT_STRIKE, option_type="PUT",
        premium=premium, side="ASK", is_sweep=False,
        underlying_price=_UNDERLYING,
    )


def _snapshot(*prints: FlowPrint) -> dict[str, list[FlowPrint]]:
    result: dict[str, list[FlowPrint]] = {}
    for p in prints:
        result.setdefault(p.symbol, []).append(p)
    return result


# ---------------------------------------------------------------------------
# Strike classification unit tests
# ---------------------------------------------------------------------------

def test_classify_otm_call():
    assert _classify_strike(_OTM_CALL_STRIKE, _UNDERLYING, "CALL") == "OTM"


def test_classify_itm_call():
    assert _classify_strike(_ITM_CALL_STRIKE, _UNDERLYING, "CALL") == "ITM"


def test_classify_otm_put():
    assert _classify_strike(_OTM_PUT_STRIKE, _UNDERLYING, "PUT") == "OTM"


def test_classify_itm_put():
    assert _classify_strike(_ITM_PUT_STRIKE, _UNDERLYING, "PUT") == "ITM"


def test_classify_atm_call():
    # Strike at exactly underlying → ATM
    assert _classify_strike(_UNDERLYING, _UNDERLYING, "CALL") == "ATM"


def test_classify_atm_put():
    assert _classify_strike(_UNDERLYING, _UNDERLYING, "PUT") == "ATM"


# ---------------------------------------------------------------------------
# Acceptance criterion 1 — PASS LONG + dominant bearish spec flow → WATCHLIST
# ---------------------------------------------------------------------------

def test_long_opposes_bearish_flow():
    result = _pass_result(direction="LONG")
    # 2× bearish OTM ask put vs 1× bullish OTM ask call → bearish dominant
    snapshot = _snapshot(
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_call(premium=_SMALL_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "OPPOSES"
    assert updated.qualified is False
    assert updated.watchlist is True
    assert updated.watchlist_reason == "FLOW_ALIGNMENT: opposing speculative flow"
    assert updated.flow_alignment == "OPPOSES"


# ---------------------------------------------------------------------------
# Acceptance criterion 2 — PASS SHORT + dominant bullish spec flow → WATCHLIST
# ---------------------------------------------------------------------------

def test_short_opposes_bullish_flow():
    result = _pass_result(direction="SHORT")
    snapshot = _snapshot(
        _otm_ask_call(premium=_LARGE_PREMIUM),
        _otm_ask_call(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_SMALL_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "OPPOSES"
    assert updated.qualified is False
    assert updated.watchlist is True


# ---------------------------------------------------------------------------
# Acceptance criterion 3 — PASS + matching spec flow → PASS
# ---------------------------------------------------------------------------

def test_long_supported_by_bullish_flow():
    result = _pass_result(direction="LONG")
    snapshot = _snapshot(
        _otm_ask_call(premium=_LARGE_PREMIUM),
        _otm_ask_call(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_SMALL_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "SUPPORTS"
    assert updated.qualified is True
    assert updated.flow_alignment == "SUPPORTS"


def test_short_supported_by_bearish_flow():
    result = _pass_result(direction="SHORT")
    snapshot = _snapshot(
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_call(premium=_SMALL_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "SUPPORTS"
    assert updated.qualified is True


# ---------------------------------------------------------------------------
# Acceptance criterion 4 — PASS + HEDGE flow (ITM-dominant) → PASS
# ---------------------------------------------------------------------------

def test_hedge_flow_no_downgrade():
    result = _pass_result(direction="LONG")
    # ITM prints dominate (>50% of total premium)
    snapshot = _snapshot(
        _itm_put(premium=700_000),   # ITM premium = 700k
        _otm_ask_call(premium=300_000),  # OTM ask = 300k
    )
    # itm / total = 700k / 1000k = 70% > 50% → HEDGE
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NEUTRAL"
    assert updated.qualified is True


# ---------------------------------------------------------------------------
# Acceptance criterion 5 — PASS + MIXED flow → PASS
# ---------------------------------------------------------------------------

def test_mixed_flow_no_downgrade():
    result = _pass_result(direction="LONG")
    # OTM ask = 50% of total → below MIN_SPEC_SHARE (0.60), not ITM-dominant
    snapshot = _snapshot(
        _otm_ask_put(premium=500_000),  # OTM ask
        FlowPrint(                       # BID side (not counted as OTM ask)
            symbol="SPY", strike=_OTM_PUT_STRIKE, option_type="PUT",
            premium=500_000, side="BID", is_sweep=False,
            underlying_price=_UNDERLYING,
        ),
    )
    # itm / total = 0%, otm_ask / total = 50% < 0.60 → MIXED
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NEUTRAL"
    assert updated.qualified is True


# ---------------------------------------------------------------------------
# Acceptance criterion 6 — PASS + no flow data → PASS
# ---------------------------------------------------------------------------

def test_no_flow_data_no_effect():
    result = _pass_result(direction="LONG")
    updated, alignment = apply_flow_gate(result, {})
    assert alignment == "NO_DATA"
    assert updated.qualified is True


def test_below_premium_threshold_treated_as_no_data():
    result = _pass_result(direction="LONG")
    # Prints exist but all below MIN_PREMIUM (250k)
    snapshot = _snapshot(
        FlowPrint(
            symbol="SPY", strike=_OTM_PUT_STRIKE, option_type="PUT",
            premium=100_000, side="ASK", is_sweep=True,
            underlying_price=_UNDERLYING,
        )
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NO_DATA"
    assert updated.qualified is True


# ---------------------------------------------------------------------------
# Acceptance criterion 7 — WATCHLIST remains WATCHLIST
# ---------------------------------------------------------------------------

def test_watchlist_result_unchanged():
    result = _watchlist_result(direction="LONG")
    snapshot = _snapshot(
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_LARGE_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NO_DATA"
    assert updated.qualified is False
    assert updated.watchlist is True
    assert updated.watchlist_reason == result.watchlist_reason


# ---------------------------------------------------------------------------
# Acceptance criterion 8 — REJECT remains REJECT
# ---------------------------------------------------------------------------

def test_reject_result_unchanged():
    result = _reject_result(direction="LONG")
    snapshot = _snapshot(
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_LARGE_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NO_DATA"
    assert updated.qualified is False
    assert updated.watchlist is False
    assert updated.hard_failure == result.hard_failure


# ---------------------------------------------------------------------------
# Acceptance criterion 9 — deterministic output
# ---------------------------------------------------------------------------

def test_deterministic_output():
    result = _pass_result(direction="LONG")
    snapshot = _snapshot(
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_call(premium=_SMALL_PREMIUM),
    )
    r1, a1 = apply_flow_gate(result, snapshot)
    r2, a2 = apply_flow_gate(result, snapshot)
    assert a1 == a2
    assert r1 == r2


# ---------------------------------------------------------------------------
# Acceptance criterion 10 — HEDGE uses full print set (pre-speculative filter)
# ---------------------------------------------------------------------------

def test_hedge_classification_uses_full_print_set():
    result = _pass_result(direction="LONG")
    # ITM prints are not OTM+ASK — they'd be invisible to speculative filter.
    # Hedge classification must use all prints above threshold.
    snapshot = _snapshot(
        _itm_put(premium=700_000),    # ITM → only visible in full print set
        _otm_ask_call(premium=200_000),
        _otm_ask_put(premium=100_000),
    )
    # total = 1_000_000, itm = 700_000, itm/total = 70% > 50% → HEDGE, not SPECULATIVE
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NEUTRAL"
    assert updated.qualified is True


# ---------------------------------------------------------------------------
# Edge case — neutral spec direction (balanced bullish and bearish)
# ---------------------------------------------------------------------------

def test_balanced_speculative_flow_neutral():
    result = _pass_result(direction="LONG")
    # Equal bullish and bearish spec premium → NEUTRAL dominant
    snapshot = _snapshot(
        _otm_ask_call(premium=500_000),
        _otm_ask_put(premium=500_000),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NEUTRAL"
    assert updated.qualified is True
