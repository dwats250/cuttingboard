"""PRD-334 R3 (BLOCKER) + PRD-335 R5: the visible Verdict is a faithful
TRANSLATION of the already-resolved decision state + permission, and it says each
thing exactly once. These tests assert, per resolved state, that the visible copy
does not contradict the resolved decision state / permission, and go RED if the
translation is mutated to a contradicting string (e.g. a no-trade state made to
read a trade-direction verb, or a halt made to assert a permission).

PRD-335 R5 dedup: the sys-verdict sentence is now rendered ONLY when it adds
information the decision-state word lacks (TRADE PERMITTED's direction verb;
"Inputs out of sync" for mixed artifacts) — it is "" and the div is omitted for
STAY FLAT / OBSERVE ONLY / HALT / generic-unavailable, so the duplicated
paraphrase disappears. The three canonical raw attributes (data-raw-state /
data-raw-title / data-raw-permission) now all live on the always-present
.decision-state div, so machine state is unconditional even when sys-verdict is
omitted.
"""
from __future__ import annotations

import re

from cuttingboard import config
from cuttingboard.delivery.dashboard_renderer import _verdict_sentence, render_dashboard_html
from tests.dash_helpers import _market_map, _mm_symbol, _payload, _run

# PRD-335 R5: all three raw attributes are on the decision-state div.
_STATE_RE = re.compile(
    r'<div class="decision-state[^"]*" data-raw-state="([^"]*)" '
    r'data-raw-title="([^"]*)" data-raw-permission="([^"]*)">([^<]*)</div>'
)
# The sys-verdict div is optional (rendered only when the sentence is non-empty)
# and no longer carries data attributes.
_VERDICT_RE = re.compile(r'<div class="sys-verdict[^"]*">([^<]*)</div>')

# Every trade-direction verb _regime_to_permission_verb can emit. A no-trade,
# halt, lock, or unavailable verdict must never surface one of these.
_DIRECTION_VERBS = ("Longs allowed", "Shorts allowed", "Momentum longs allowed")
_REGIME_VERB = {"RISK_ON": "Longs allowed", "RISK_OFF": "Shorts allowed",
                "EXPANSION": "Momentum longs allowed"}


def _state(html: str) -> tuple[str, str, str, str]:
    """(data-raw-state, data-raw-title, data-raw-permission, visible label)."""
    m = _STATE_RE.search(html)
    assert m is not None, "decision-state div not found / raw attributes missing"
    return m.group(1), m.group(2), m.group(3), m.group(4)


def _sentence(html: str) -> str:
    """The visible sys-verdict sentence, or "" when the div is omitted (R5)."""
    m = _VERDICT_RE.search(html)
    return m.group(1) if m else ""


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
    # PRD-335 R5: they are all carried on the decision-state div.
    _state(html)


# --- TRADE PERMITTED preserves the long / short / momentum-long distinction ----

def test_trade_permitted_surfaces_the_regime_direction_verb() -> None:
    for regime, verb in _REGIME_VERB.items():
        html = render_dashboard_html(
            _payload(market_regime=regime), _run(outcome="TRADE"), market_map=_mm())
        raw_state, _raw_title, raw_perm, label = _state(html)
        sentence = _sentence(html)
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
        raw_state, _raw_title, _raw_perm, label = _state(html)
        sentence = _sentence(html)
        assert raw_state == "TRADE PERMITTED" and label == "TRADE PERMITTED", raw_state
        assert sentence == "Trades permitted", sentence
        assert "Stand down" not in sentence            # never deny in a permitted state
        for verb in _DIRECTION_VERBS:                   # NEUTRAL has no regime direction
            assert verb not in sentence


# --- no-trade: the state word says it; the sys-verdict sentence is omitted (R5) -

def test_no_trade_reads_no_new_trades_not_a_direction() -> None:
    for regime in ("RISK_ON", "RISK_OFF", "EXPANSION", "NEUTRAL"):
        html = render_dashboard_html(
            _payload(market_regime=regime), _run(outcome="NO_TRADE"), market_map=_mm())
        raw_state, _raw_title, _raw_perm, label = _state(html)
        sentence = _sentence(html)
        assert raw_state == "STAY FLAT", (regime, raw_state)
        assert label == "STAY FLAT"
        # PRD-335 R5: the duplicated "No new trades permitted" paraphrase is gone;
        # the STAY FLAT state word already says it, so the sys-verdict div is omitted.
        assert sentence == "", (regime, sentence)
        # contradiction guard: no trade-direction verb anywhere in the verdict.
        for verb in _DIRECTION_VERBS:
            assert verb not in sentence, (regime, verb)


# --- HALT: the state word says it; no sys-verdict paraphrase, no permission -----

def test_halt_reads_system_halted_and_makes_no_permission_claim() -> None:
    html = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(system_halted=True, outcome="NO_TRADE"), market_map=_mm())
    raw_state, _raw_title, _raw_perm, label = _state(html)
    sentence = _sentence(html)
    assert raw_state == "HALT" and label == "HALT"
    # PRD-335 R5: "System halted" restated the HALT word; the div is omitted.
    assert sentence == ""
    for verb in _DIRECTION_VERBS:
        assert verb not in sentence


# --- operator lock reads OBSERVE ONLY + the single lock reason line ------------

def test_operator_lock_reads_no_new_trades() -> None:
    html = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(outcome="NO_TRADE", permission=config.OPERATOR_LOCK_PERMISSION), market_map=_mm())
    raw_state, _raw_title, raw_perm, label = _state(html)
    sentence = _sentence(html)
    assert raw_state == "OBSERVE ONLY" and label == "OBSERVE ONLY"
    # PRD-335 R5: the sys-verdict paraphrase is gone; the ONE reason line is the
    # canonical operator-lock permission, rendered once on its own line.
    assert sentence == ""
    assert f'<div class="sys-permission">{config.OPERATOR_LOCK_PERMISSION}</div>' in html
    assert raw_perm == "OPERATOR_LOCKED"           # never the regime direction verb (PRD-304 R7)
    for verb in _DIRECTION_VERBS:
        assert verb not in html


# --- halt / coherence survive an operator-lock overlap ------------------------

def test_halt_survives_operator_lock_overlap() -> None:
    html = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(system_halted=True, outcome="NO_TRADE", permission=config.OPERATOR_LOCK_PERMISSION),
        market_map=_mm())
    raw_state, _raw_title, _raw_perm, label = _state(html)
    sentence = _sentence(html)
    assert raw_state == "HALT" and label == "HALT"   # NOT masked to OBSERVE ONLY
    assert sentence == ""
    # PRD-335 R5: the halt colour moved to the always-present decision-state div
    # (the sys-verdict div it used to sit on is omitted for HALT).
    assert 'class="decision-state sys-halt"' in html


def test_mixed_artifacts_coherence_survives_lock() -> None:
    payload, run, mm = _payload(market_regime="RISK_ON"), _run(
        outcome="NO_TRADE", permission=config.OPERATOR_LOCK_PERMISSION), _mm()
    _mixed_ids(payload, run, mm)
    html = render_dashboard_html(payload, run, market_map=mm)
    raw_state, _raw_title, _raw_perm, _label = _state(html)
    sentence = _sentence(html)
    assert raw_state == "STATE UNAVAILABLE"            # coherence beats the lock label
    assert sentence == "Inputs out of sync"


# --- STATE UNAVAILABLE (mixed artifacts) reads a non-committal sentence --------

def test_mixed_artifacts_reads_inputs_out_of_sync() -> None:
    payload, run, mm = _payload(market_regime="RISK_ON"), _run(outcome="NO_TRADE"), _mm()
    _mixed_ids(payload, run, mm)
    html = render_dashboard_html(payload, run, market_map=mm)
    raw_state, _raw_title, _raw_perm, _label = _state(html)
    sentence = _sentence(html)
    assert raw_state == "STATE UNAVAILABLE"
    assert sentence == "Inputs out of sync"
    for verb in _DIRECTION_VERBS:
        assert verb not in sentence


# --- the WHY line still carries the specific reason unchanged (R3/R5) ----------

def test_why_line_carries_the_specific_reason_on_no_trade() -> None:
    # A no-trade with high-grade setups gated names the gate in WHY -- the generic
    # verdict paraphrase is gone (PRD-335 R5) but the specific causal reason
    # survives visibly in the WHY line (the veto carrier).
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A+")})
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run(outcome="NO_TRADE"), market_map=mm)
    sentence = _sentence(html)
    assert sentence == ""
    assert 'class="sys-why">WHY:' in html


# --- the translation is STATE-SPECIFIC (RED under a contradicting mutation) ----

def test_verdict_sentence_translation_is_state_specific() -> None:
    # Direct unit proof: each resolved state maps to a distinct, faithful sentence.
    # PRD-335 R5: STAY FLAT / OBSERVE ONLY / HALT / generic-unavailable return ""
    # (the state word already carries the meaning; the div is omitted). Mutating
    # any mapping to a contradicting string breaks this test AND the renders above.
    assert _verdict_sentence("TRADE PERMITTED", "Longs allowed", mixed_artifacts=False) == "Longs allowed"
    assert _verdict_sentence("TRADE PERMITTED", "Shorts allowed", mixed_artifacts=False) == "Shorts allowed"
    assert _verdict_sentence("STAY FLAT", "Longs allowed", mixed_artifacts=False) == ""
    assert _verdict_sentence("OBSERVE ONLY", "Longs allowed", mixed_artifacts=False) == ""
    assert _verdict_sentence("HALT", "Longs allowed", mixed_artifacts=False) == ""
    assert _verdict_sentence("STATE UNAVAILABLE", "Longs allowed", mixed_artifacts=True) == "Inputs out of sync"
    assert _verdict_sentence("STATE UNAVAILABLE", "Longs allowed", mixed_artifacts=False) == ""
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
        raw_state, _raw_title, _raw_perm, _label = _state(html)
        sentence = _sentence(html)
        if any(v in sentence for v in _DIRECTION_VERBS):     # a direction implies permitted
            assert raw_state == "TRADE PERMITTED", (raw_state, sentence)
        if raw_state == "TRADE PERMITTED":                   # never deny in a permitted state
            assert "Stand down" not in sentence and "No new trades" not in sentence
