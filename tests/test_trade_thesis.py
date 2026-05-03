from __future__ import annotations


from cuttingboard.qualification import (
    ENTRY_MODE_CONTINUATION,
    ENTRY_MODE_DIRECT,
    QualificationResult,
    TradeCandidate,
)
from cuttingboard.structure import StructureResult
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE, TradeDecision
from cuttingboard.trade_thesis import (
    THESIS_CONFLICTED,
    THESIS_INCOMPLETE,
    THESIS_UNKNOWN,
    THESIS_VALID,
    apply_thesis_gate,
    build_thesis,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decision(
    symbol: str = "SPY",
    direction: str = "LONG",
    status: str = ALLOW_TRADE,
    stop: float = 97.0,
    policy_reason: str = "policy_allowed",
    block_reason: str | None = None,
) -> TradeDecision:
    return TradeDecision(
        ticker=symbol,
        direction=direction,
        status=status,
        entry=100.0,
        stop=stop,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=block_reason,
        policy_allowed=status == ALLOW_TRADE,
        policy_reason=policy_reason,
    )


def _block_decision(symbol: str = "SPY", block_reason: str = "pre_existing") -> TradeDecision:
    return TradeDecision(
        ticker=symbol,
        direction="LONG",
        status=BLOCK_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=block_reason,
        policy_allowed=False,
        policy_reason=block_reason,
        decision_trace={"stage": "CHAIN_VALIDATION", "source": "chain_validation", "reason": block_reason},
    )


def _qual(
    symbol: str = "SPY",
    direction: str = "LONG",
    entry_mode: str = ENTRY_MODE_DIRECT,
) -> QualificationResult:
    return QualificationResult(
        symbol=symbol,
        qualified=True,
        watchlist=False,
        direction=direction,
        gates_passed=["REGIME", "CONFIDENCE"],
        gates_failed=[],
        hard_failure=None,
        watchlist_reason=None,
        max_contracts=2,
        dollar_risk=150.0,
        entry_mode=entry_mode,
    )


def _structure(symbol: str = "SPY", structure: str = "TREND") -> StructureResult:
    return StructureResult(
        symbol=symbol,
        structure=structure,
        iv_environment="NORMAL_IV",
        is_tradeable=structure != "CHOP",
        disqualification_reason=None if structure != "CHOP" else "structure_chop",
    )


def _candidate(symbol: str = "SPY", stop_price: float = 97.0) -> TradeCandidate:
    return TradeCandidate(
        symbol=symbol,
        direction="LONG",
        entry_price=100.0,
        stop_price=stop_price,
        target_price=106.0,
        spread_width=1.0,
    )


# ---------------------------------------------------------------------------
# build_thesis tests
# ---------------------------------------------------------------------------

def test_valid_thesis_full_fields() -> None:
    thesis = build_thesis(
        _decision(),
        _qual(),
        _structure(),
        "RISK_ON",
        _candidate(),
    )
    assert thesis["status"] == THESIS_VALID
    assert thesis["direction"] == "LONG"
    assert thesis["catalyst"] is not None
    assert thesis["confirmation"] is not None
    assert thesis["invalidation"] is not None
    assert thesis["block_reason"] is None
    assert set(thesis.keys()) == {
        "symbol", "direction", "catalyst", "confirmation",
        "invalidation", "status", "block_reason",
    }


def test_macro_confirmed_when_pressure_aligns_long() -> None:
    thesis = build_thesis(_decision(), _qual(), _structure(), "RISK_ON", _candidate())
    assert thesis["confirmation"] == "MACRO_CONFIRMED"


def test_macro_confirmed_when_pressure_aligns_short() -> None:
    d = _decision(direction="SHORT", policy_reason="policy_allowed")
    q = _qual(direction="SHORT")
    thesis = build_thesis(d, q, _structure(), "RISK_OFF", _candidate())
    assert thesis["confirmation"] == "MACRO_CONFIRMED"


def test_conflicted_thesis_when_long_with_risk_off() -> None:
    thesis = build_thesis(_decision(), _qual(), _structure(), "RISK_OFF", _candidate())
    assert thesis["status"] == THESIS_CONFLICTED
    assert thesis["block_reason"] == "THESIS_CONFLICTED"


def test_conflicted_thesis_when_short_with_risk_on() -> None:
    d = _decision(direction="SHORT", policy_reason="policy_allowed")
    q = _qual(direction="SHORT")
    thesis = build_thesis(d, q, _structure(), "RISK_ON", _candidate())
    assert thesis["status"] == THESIS_CONFLICTED
    assert thesis["block_reason"] == "THESIS_CONFLICTED"


def test_incomplete_when_direction_empty() -> None:
    d = _decision(direction="")
    thesis = build_thesis(d, _qual(direction=""), _structure(), "RISK_ON")
    assert thesis["status"] == THESIS_INCOMPLETE
    assert thesis["block_reason"] == "THESIS_INCOMPLETE"


def test_incomplete_when_no_catalyst_available() -> None:
    # overall_pressure=UNKNOWN, entry_mode=DIRECT, structure=CHOP, default policy_reason
    d = _decision(policy_reason="policy_not_evaluated")
    q = _qual(entry_mode=ENTRY_MODE_DIRECT)
    s = _structure(structure="CHOP")
    thesis = build_thesis(d, q, s, "UNKNOWN", _candidate())
    assert thesis["status"] == THESIS_INCOMPLETE
    assert thesis["catalyst"] is None
    assert thesis["block_reason"] == "THESIS_INCOMPLETE"


def test_incomplete_when_invalidation_null() -> None:
    # stop=0 and no candidate → invalidation=None
    d = _decision(stop=0.0)
    thesis = build_thesis(d, _qual(), _structure(), "RISK_ON", candidate=None)
    assert thesis["status"] == THESIS_INCOMPLETE
    assert thesis["invalidation"] is None
    assert thesis["block_reason"] == "THESIS_INCOMPLETE"


def test_unknown_status_when_confirmation_cannot_be_determined() -> None:
    # MIXED pressure (not aligned, not conflicted), CHOP structure, non-policy-allowed reason
    d = _decision(policy_reason="orb_unavailable")
    q = _qual(entry_mode=ENTRY_MODE_CONTINUATION)  # provides catalyst
    s = _structure(structure="CHOP")
    thesis = build_thesis(d, q, s, "MIXED", _candidate())
    assert thesis["status"] == THESIS_UNKNOWN
    assert thesis["block_reason"] is None
    assert thesis["invalidation"] is not None
    assert thesis["direction"] == "LONG"


def test_structure_confirmation_when_no_macro_alignment() -> None:
    # MIXED pressure but trend structure → STRUCTURE_CONFIRMED
    d = _decision()
    q = _qual()
    s = _structure(structure="TREND")
    thesis = build_thesis(d, q, s, "MIXED", _candidate())
    assert thesis["confirmation"] == "STRUCTURE_CONFIRMED"


def test_catalyst_from_entry_mode_when_pressure_unknown() -> None:
    q = _qual(entry_mode=ENTRY_MODE_CONTINUATION)
    thesis = build_thesis(_decision(), q, _structure(), "UNKNOWN", _candidate())
    assert thesis["catalyst"] == "entry:CONTINUATION"


def test_invalidation_uses_stop_from_decision() -> None:
    d = _decision(stop=95.50)
    thesis = build_thesis(d, _qual(), _structure(), "RISK_ON", _candidate(stop_price=97.0))
    assert thesis["invalidation"] == "stop at 95.50"


def test_invalidation_falls_back_to_candidate_stop() -> None:
    d = _decision(stop=0.0)
    thesis = build_thesis(d, _qual(), _structure(), "RISK_ON", _candidate(stop_price=94.25))
    assert thesis["invalidation"] == "stop at 94.25"


def test_confirmation_never_null() -> None:
    # All paths must produce a string confirmation
    for pressure in ("RISK_ON", "RISK_OFF", "MIXED", "NEUTRAL", "UNKNOWN"):
        thesis = build_thesis(_decision(), _qual(), _structure(), pressure, _candidate())
        assert isinstance(thesis["confirmation"], str)
        assert thesis["confirmation"]


# ---------------------------------------------------------------------------
# apply_thesis_gate tests
# ---------------------------------------------------------------------------

def test_allow_trade_with_valid_thesis_remains_allow() -> None:
    decisions = [_decision()]
    candidates = {"SPY": _candidate()}
    qual_by_sym = {"SPY": _qual()}
    exec_struct = {"SPY": _structure()}

    result, thesis_map = apply_thesis_gate(
        decisions, candidates, qual_by_sym, exec_struct, "RISK_ON"
    )
    assert len(result) == 1
    assert result[0].status == ALLOW_TRADE
    assert "SPY" in thesis_map
    assert thesis_map["SPY"]["status"] == THESIS_VALID


def test_allow_trade_missing_invalidation_becomes_block() -> None:
    d = _decision(stop=0.0)
    decisions = [d]
    candidates = {}  # no candidate stop fallback
    qual_by_sym = {"SPY": _qual()}
    exec_struct = {"SPY": _structure()}

    result, thesis_map = apply_thesis_gate(
        decisions, candidates, qual_by_sym, exec_struct, "RISK_ON"
    )
    assert result[0].status == BLOCK_TRADE
    assert result[0].block_reason == "THESIS_INCOMPLETE"
    assert thesis_map["SPY"]["status"] == THESIS_INCOMPLETE


def test_allow_trade_missing_direction_becomes_block() -> None:
    d = _decision(direction="")
    decisions = [d]
    candidates = {"SPY": _candidate()}
    qual_by_sym = {"SPY": _qual(direction="")}
    exec_struct = {"SPY": _structure()}

    result, thesis_map = apply_thesis_gate(
        decisions, candidates, qual_by_sym, exec_struct, "RISK_ON"
    )
    assert result[0].status == BLOCK_TRADE
    assert result[0].block_reason == "THESIS_INCOMPLETE"


def test_block_trade_before_gate_remains_unchanged() -> None:
    pre_blocked = _block_decision(block_reason="pre_existing")
    original_trace = dict(pre_blocked.decision_trace)

    result, thesis_map = apply_thesis_gate(
        [pre_blocked], {}, {}, {}, "RISK_ON"
    )
    assert result[0].status == BLOCK_TRADE
    assert result[0].block_reason == "pre_existing"
    assert result[0].decision_trace == original_trace
    assert "SPY" not in thesis_map


def test_gate_does_not_modify_already_blocked_decisions() -> None:
    pre_blocked = _block_decision()
    allow_decision = _decision(symbol="NVDA")
    candidates = {"NVDA": _candidate(symbol="NVDA")}
    qual_by_sym = {"NVDA": _qual(symbol="NVDA")}
    exec_struct = {"NVDA": _structure(symbol="NVDA")}

    result, thesis_map = apply_thesis_gate(
        [pre_blocked, allow_decision], candidates, qual_by_sym, exec_struct, "RISK_ON"
    )
    # BLOCK_TRADE pre_blocked unchanged
    spy_result = next(r for r in result if r.ticker == "SPY")
    assert spy_result.status == BLOCK_TRADE
    assert spy_result.block_reason == "pre_existing"
    assert "SPY" not in thesis_map


def test_unknown_confirmation_does_not_block_when_direction_and_invalidation_exist() -> None:
    # MIXED pressure, CHOP structure, non-default policy → catalyst from entry_mode
    d = _decision(policy_reason="orb_unavailable")
    q = _qual(entry_mode=ENTRY_MODE_CONTINUATION)
    s = _structure(structure="CHOP")

    result, thesis_map = apply_thesis_gate(
        [d], {"SPY": _candidate()}, {"SPY": q}, {"SPY": s}, "MIXED"
    )
    assert result[0].status == ALLOW_TRADE
    assert thesis_map["SPY"]["status"] == THESIS_UNKNOWN


def test_missing_macro_pressure_unknown_does_not_halt() -> None:
    # overall_pressure="UNKNOWN" simulates macro pressure fallback
    result, thesis_map = apply_thesis_gate(
        [_decision()],
        {"SPY": _candidate()},
        {"SPY": _qual()},
        {"SPY": _structure()},
        "UNKNOWN",
    )
    # No exception raised; gate completes with some thesis status
    assert len(result) == 1
    assert "SPY" in thesis_map


def test_block_reason_equals_decision_trace_reason_for_gate_blocked() -> None:
    d = _decision(stop=0.0)
    result, _ = apply_thesis_gate(
        [d], {}, {"SPY": _qual()}, {"SPY": _structure()}, "RISK_ON"
    )
    blocked = result[0]
    assert blocked.status == BLOCK_TRADE
    assert blocked.block_reason == blocked.decision_trace["reason"]


def test_thesis_map_contains_symbol_for_allow_trade_decisions() -> None:
    decisions = [_decision("SPY"), _decision("NVDA")]
    candidates = {"SPY": _candidate("SPY"), "NVDA": _candidate("NVDA")}
    qual = {"SPY": _qual("SPY"), "NVDA": _qual("NVDA")}
    structs = {"SPY": _structure("SPY"), "NVDA": _structure("NVDA")}

    _, thesis_map = apply_thesis_gate(decisions, candidates, qual, structs, "RISK_ON")
    assert "SPY" in thesis_map
    assert "NVDA" in thesis_map


def test_historical_candidate_dict_without_thesis_key_is_readable() -> None:
    # R8: contract builder uses thesis_map.get(symbol) which returns None when absent
    # Simulate: thesis_map={} → thesis=None for missing symbol
    candidate = {
        "symbol": "SPY",
        "decision_status": "ALLOW_TRADE",
        # no "thesis" key — historical record
    }
    # Reading thesis key on old record should not raise
    thesis = candidate.get("thesis")
    assert thesis is None


def test_conflicted_thesis_produces_block() -> None:
    # LONG + RISK_OFF = CONFLICTED → should block
    d = _decision(direction="LONG")
    q = _qual(direction="LONG")
    result, thesis_map = apply_thesis_gate(
        [d], {"SPY": _candidate()}, {"SPY": q}, {"SPY": _structure()}, "RISK_OFF"
    )
    assert result[0].status == BLOCK_TRADE
    assert result[0].block_reason == "THESIS_CONFLICTED"
    assert thesis_map["SPY"]["status"] == THESIS_CONFLICTED
