"""PRD-334 R3 (BLOCKER): the visible Verdict is a faithful TRANSLATION of the
already-resolved decision state + permission. These tests assert, per resolved
state, that the visible copy does not contradict the resolved decision state /
permission, and go RED if the translation is mutated to a contradicting string
(e.g. a no-trade state made to read a trade-direction verb, or a halt made to
assert a permission). The data-raw-title / data-raw-state / data-raw-permission
attributes carry the internal canonical values the copy is checked against.
"""
from __future__ import annotations

import re

from cuttingboard import config
from cuttingboard.delivery.dashboard_renderer import _verdict_sentence, render_dashboard_html
from tests.dash_helpers import _market_map, _mm_symbol, _payload, _run

_VERDICT_RE = re.compile(
    r'<div class="sys-verdict[^"]*" data-raw-title="([^"]*)" '
    r'data-raw-permission="([^"]*)">([^<]*)</div>'
)
_STATE_RE = re.compile(r'<div class="decision-state[^"]*" data-raw-state="([^"]*)">([^<]*)</div>')

# Every trade-direction verb _regime_to_permission_verb can emit. A no-trade,
# halt, lock, or unavailable verdict must never surface one of these.
_DIRECTION_VERBS = ("Longs allowed", "Shorts allowed", "Momentum longs allowed")
_REGIME_VERB = {"RISK_ON": "Longs allowed", "RISK_OFF": "Shorts allowed",
                "EXPANSION": "Momentum longs allowed"}


def _verdict(html: str) -> tuple[str, str, str]:
    """(data-raw-title, data-raw-permission, visible sentence) for the sys-verdict."""
    m = _VERDICT_RE.search(html)
    assert m is not None, "sys-verdict div not found / attributes missing"
    return m.group(1), m.group(2), m.group(3)


def _state(html: str) -> tuple[str, str]:
    """(data-raw-state, visible decision-state label)."""
    m = _STATE_RE.search(html)
    assert m is not None, "decision-state div not found / data-raw-state missing"
    return m.group(1), m.group(2)


def _mm() -> dict:
    return _market_map({"SPY": _mm_symbol("SPY", grade="A+")})


def _mixed_ids(payload: dict, run: dict, mm: dict) -> None:
    payload["meta"]["generation_id"] = "gen-a"
    run["generation_id"] = "gen-b"        # mismatch -> MIXED_ARTIFACTS
    mm["generation_id"] = "gen-a"


# --- data-raw-* presence ------------------------------------------------------

def test_all_three_raw_attributes_present() -> None:
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run(), market_map=_mm())
    assert "data-raw-title=" in html
    assert "data-raw-state=" in html
    assert "data-raw-permission=" in html


# --- TRADE PERMITTED preserves the long / short / momentum-long distinction ----

def test_trade_permitted_surfaces_the_regime_direction_verb() -> None:
    for regime, verb in _REGIME_VERB.items():
        html = render_dashboard_html(
            _payload(market_regime=regime), _run(outcome="TRADE"), market_map=_mm())
        raw_title, raw_perm, sentence = _verdict(html)
        raw_state, label = _state(html)
        assert raw_state == "TRADE PERMITTED", (regime, raw_state)
        assert label == "TRADE PERMITTED"
        assert sentence == verb, (regime, sentence)              # the exact direction verb
        assert raw_perm == verb
        # a permitted verdict must NOT deny trading or claim a halt
        assert "No new trades" not in sentence
        assert "System halted" not in sentence


def test_neutral_permitted_trade_never_says_stand_down() -> None:
    # PRD-334 review F1 (BLOCKER): a NEUTRAL-regime run can still resolve
    # outcome=TRADE (positive/negative NEUTRAL scores qualify LONG/SHORT
    # candidates). The regime helper returns the NON-directional "Stand down" for
    # NEUTRAL; surfacing it under TRADE PERMITTED would simultaneously permit and
    # deny trading. The verdict must read the faithful neutral "Trades permitted",
    # never "Stand down", and must not invent a direction the neutral regime lacks.
    for run in (_run(outcome="TRADE"),
                _run(outcome="TRADE", posture="CONTROLLED_LONG"),
                _run(outcome="TRADE", posture="DEFENSIVE_SHORT")):
        html = render_dashboard_html(_payload(market_regime="NEUTRAL"), run, market_map=_mm())
        raw_state, label = _state(html)
        _rt, _rp, sentence = _verdict(html)
        assert raw_state == "TRADE PERMITTED" and label == "TRADE PERMITTED", raw_state
        assert sentence == "Trades permitted", sentence
        assert "Stand down" not in sentence            # never deny in a permitted state
        for verb in _DIRECTION_VERBS:                   # NEUTRAL has no regime direction
            assert verb not in sentence


# --- no-trade reads "No new trades permitted", never a direction verb ----------

def test_no_trade_reads_no_new_trades_not_a_direction() -> None:
    for regime in ("RISK_ON", "RISK_OFF", "EXPANSION", "NEUTRAL"):
        html = render_dashboard_html(
            _payload(market_regime=regime), _run(outcome="NO_TRADE"), market_map=_mm())
        raw_state, label = _state(html)
        _rt, _rp, sentence = _verdict(html)
        assert raw_state == "STAY FLAT", (regime, raw_state)
        assert label == "STAY FLAT"
        assert sentence == "No new trades permitted", (regime, sentence)
        # contradiction guards: no trade-direction verb, no "nothing qualifies"
        for verb in _DIRECTION_VERBS:
            assert verb not in sentence, (regime, verb)
        assert "nothing qualif" not in sentence.lower()
        assert "no qualified" not in sentence.lower()


# --- HALT reads "System halted"; no invented cause, no permission claim --------

def test_halt_reads_system_halted_and_makes_no_permission_claim() -> None:
    html = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(system_halted=True, outcome="NO_TRADE"), market_map=_mm())
    raw_state, label = _state(html)
    _rt, _rp, sentence = _verdict(html)
    assert raw_state == "HALT" and label == "HALT"
    assert sentence == "System halted"
    for verb in _DIRECTION_VERBS:
        assert verb not in sentence
    assert "allowed" not in sentence and "permitted" not in sentence


# --- operator lock reads OBSERVE ONLY + "No new trades permitted" --------------

def test_operator_lock_reads_no_new_trades() -> None:
    html = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(outcome="NO_TRADE", permission=config.OPERATOR_LOCK_PERMISSION), market_map=_mm())
    raw_state, label = _state(html)
    raw_title, raw_perm, sentence = _verdict(html)
    assert raw_state == "OBSERVE ONLY" and label == "OBSERVE ONLY"
    assert sentence == "No new trades permitted"
    assert raw_perm == "OPERATOR_LOCKED"           # never the regime direction verb (PRD-304 R7)
    for verb in _DIRECTION_VERBS:
        assert verb not in html


# --- halt / coherence survive an operator-lock overlap ------------------------

def test_halt_survives_operator_lock_overlap() -> None:
    html = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(system_halted=True, outcome="NO_TRADE", permission=config.OPERATOR_LOCK_PERMISSION),
        market_map=_mm())
    raw_state, label = _state(html)
    _rt, _rp, sentence = _verdict(html)
    assert raw_state == "HALT" and label == "HALT"   # NOT masked to OBSERVE ONLY
    assert sentence == "System halted"
    assert 'class="sys-verdict sys-halt"' in html      # halt colour preserved


def test_mixed_artifacts_coherence_survives_lock() -> None:
    payload, run, mm = _payload(market_regime="RISK_ON"), _run(
        outcome="NO_TRADE", permission=config.OPERATOR_LOCK_PERMISSION), _mm()
    _mixed_ids(payload, run, mm)
    html = render_dashboard_html(payload, run, market_map=mm)
    raw_state, label = _state(html)
    _rt, _rp, sentence = _verdict(html)
    assert raw_state == "STATE UNAVAILABLE"            # coherence beats the lock label
    assert sentence == "Inputs out of sync"


# --- STATE UNAVAILABLE (mixed artifacts) reads a non-committal sentence --------

def test_mixed_artifacts_reads_inputs_out_of_sync() -> None:
    payload, run, mm = _payload(market_regime="RISK_ON"), _run(outcome="NO_TRADE"), _mm()
    _mixed_ids(payload, run, mm)
    html = render_dashboard_html(payload, run, market_map=mm)
    raw_state, _label = _state(html)
    _rt, _rp, sentence = _verdict(html)
    assert raw_state == "STATE UNAVAILABLE"
    assert sentence == "Inputs out of sync"
    for verb in _DIRECTION_VERBS:
        assert verb not in sentence


# --- the WHY line still carries the specific reason unchanged (R3) -------------

def test_why_line_carries_the_specific_reason_on_no_trade() -> None:
    # A no-trade with high-grade setups gated names the gate in WHY -- the generic
    # verdict copy stays "No new trades permitted" while WHY carries the specifics.
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A+")})
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run(outcome="NO_TRADE"), market_map=mm)
    _rt, _rp, sentence = _verdict(html)
    assert sentence == "No new trades permitted"
    assert 'class="sys-why">WHY:' in html


# --- the translation is STATE-SPECIFIC (RED under a contradicting mutation) ----

def test_verdict_sentence_translation_is_state_specific() -> None:
    # Direct unit proof: each resolved state maps to a distinct, faithful sentence.
    # Mutating any one mapping to another state's string (a contradiction) breaks
    # this test AND the per-state renders above.
    assert _verdict_sentence("TRADE PERMITTED", "Longs allowed", mixed_artifacts=False) == "Longs allowed"
    assert _verdict_sentence("TRADE PERMITTED", "Shorts allowed", mixed_artifacts=False) == "Shorts allowed"
    assert _verdict_sentence("STAY FLAT", "Longs allowed", mixed_artifacts=False) == "No new trades permitted"
    assert _verdict_sentence("OBSERVE ONLY", "Longs allowed", mixed_artifacts=False) == "No new trades permitted"
    assert _verdict_sentence("HALT", "Longs allowed", mixed_artifacts=False) == "System halted"
    assert _verdict_sentence("STATE UNAVAILABLE", "Longs allowed", mixed_artifacts=True) == "Inputs out of sync"
    assert _verdict_sentence("STATE UNAVAILABLE", "Longs allowed", mixed_artifacts=False) == "Board state unavailable"
    # PRD-334 review F1 mutation proof: a permitted trade whose regime verb is the
    # non-directional "Stand down" reads the neutral "Trades permitted" -- NEVER
    # "Stand down" (which would deny in a permitted state). Reverting the F1 fix
    # (returning regime_permission_text unconditionally here) fails this assertion.
    assert _verdict_sentence("TRADE PERMITTED", "Stand down", mixed_artifacts=False) == "Trades permitted"
    # a no-trade state never yields a trade-direction verb, whatever the regime verb
    for verb in _DIRECTION_VERBS:
        assert _verdict_sentence("STAY FLAT", verb, mixed_artifacts=False) not in _DIRECTION_VERBS


def test_visible_copy_never_contradicts_raw_state() -> None:
    # The faithfulness invariant across the whole matrix: a trade-direction verb is
    # visible ONLY when data-raw-state is TRADE PERMITTED (a permitted trade may
    # still read the neutral "Trades permitted" under a NEUTRAL regime -- F1); and a
    # permitted trade never visibly denies trading ("Stand down" / "No new trades").
    cases = [
        ("RISK_ON", _run(outcome="TRADE")),
        ("NEUTRAL", _run(outcome="TRADE")),          # F1: permitted but non-directional
        ("RISK_ON", _run(outcome="NO_TRADE")),
        ("RISK_ON", _run(system_halted=True, outcome="NO_TRADE")),
        ("RISK_ON", _run(outcome="NO_TRADE", permission=config.OPERATOR_LOCK_PERMISSION)),
    ]
    for regime, run in cases:
        html = render_dashboard_html(_payload(market_regime=regime), run, market_map=_mm())
        raw_state, _label = _state(html)
        _rt, _rp, sentence = _verdict(html)
        if any(v in sentence for v in _DIRECTION_VERBS):     # a direction implies permitted
            assert raw_state == "TRADE PERMITTED", (raw_state, sentence)
        if raw_state == "TRADE PERMITTED":                   # never deny in a permitted state
            assert "Stand down" not in sentence and "No new trades" not in sentence
