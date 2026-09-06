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

import pytest

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


def _system_state_region(html: str) -> str:
    seg = html.split('id="system-state"', 1)[1]
    nxt = seg[10:].find('id="')
    return seg if nxt == -1 else seg[: nxt + 10]


def _verdict_lines(html: str):
    """(primary, reason, regime, kill-switch) VISIBLE line texts in #system-state.
    Reads element TEXT only — raw state carried in data-* attributes is excluded."""
    region = _system_state_region(html)

    def grab(cls):
        return [m.group(1).strip() for m in re.finditer(
            r'class="' + cls + r'[^"]*"[^>]*>([^<]*)<', region) if m.group(1).strip()]

    primary = grab("decision-state")
    reasons = grab("sys-verdict") + grab("sys-why") + grab("sys-permission")
    ctx = grab("sys-context")
    regime = [t for t in ctx if t.endswith("regime")]
    kill = [t for t in ctx if "Kill switch" in t]
    return primary, reasons, regime, kill


def _visible_text(html: str) -> str:
    primary, reasons, regime, kill = _verdict_lines(html)
    return " ".join(primary + reasons + regime + kill)


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

def test_trade_permitted_surfaces_no_second_verdict_sentence() -> None:
    # PRD-335 F3 (Helm 2026-09-05): TRADE PERMITTED renders exactly ONE primary
    # state line and NO second verdict sentence — the old "Longs allowed" /
    # "Shorts allowed" / "Momentum longs allowed" sys-verdict is removed. The raw
    # permission verb still lives in data-raw-permission; the direction lives
    # faithfully in the compact regime-context line.
    for regime, verb in _REGIME_VERB.items():
        html = render_dashboard_html(
            _payload(market_regime=regime), _run(outcome="TRADE"), market_map=_mm())
        raw_state, _raw_title, raw_perm, label = _state(html)
        sentence = _sentence(html)
        assert raw_state == "TRADE PERMITTED" and label == "TRADE PERMITTED", (regime, raw_state)
        assert sentence == "", (regime, sentence)          # no second verdict sentence
        assert raw_perm == verb                            # raw verb preserved in data-*
        assert verb not in _visible_text(html)             # never a VISIBLE direction verb


def test_neutral_permitted_trade_never_says_stand_down() -> None:
    # PRD-334 review F1 (BLOCKER), preserved under PRD-335 F3: a NEUTRAL-regime run
    # can still resolve outcome=TRADE. The verdict must NEVER surface the
    # non-directional "Stand down" (which would deny in a permitted state). Under
    # F3 no verdict sentence renders at all, so "Stand down" cannot appear.
    for run in (_run(outcome="TRADE"),
                _run(outcome="TRADE", posture="CONTROLLED_LONG"),
                _run(outcome="TRADE", posture="DEFENSIVE_SHORT")):
        html = render_dashboard_html(_payload(market_regime="NEUTRAL"), run, market_map=_mm())
        raw_state, _raw_title, _raw_perm, label = _state(html)
        sentence = _sentence(html)
        assert raw_state == "TRADE PERMITTED" and label == "TRADE PERMITTED", raw_state
        assert sentence == "", sentence
        assert "Stand down" not in _visible_text(html)   # never VISIBLY deny in a permitted state
        for verb in _DIRECTION_VERBS:                    # NEUTRAL has no visible regime direction
            assert verb not in _visible_text(html)


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
    # Direct unit proof (PRD-335 F3): the sys-verdict sentence is a SECOND line
    # ONLY for STATE UNAVAILABLE with mixed artifacts ("Inputs out of sync").
    # Every other state — INCLUDING TRADE PERMITTED — returns "" so no second
    # verdict/permission paraphrase renders. Mutating any mapping to a
    # contradicting string breaks this test AND the per-state renders above.
    assert _verdict_sentence("STATE UNAVAILABLE", "Longs allowed", mixed_artifacts=True) == "Inputs out of sync"
    assert _verdict_sentence("STATE UNAVAILABLE", "Longs allowed", mixed_artifacts=False) == ""
    for state, verb in (
        ("TRADE PERMITTED", "Longs allowed"),
        ("TRADE PERMITTED", "Shorts allowed"),
        ("TRADE PERMITTED", "Momentum longs allowed"),
        ("TRADE PERMITTED", "Stand down"),      # F1 preserved: never surface "Stand down"
        ("STAY FLAT", "Longs allowed"),
        ("OBSERVE ONLY", "Longs allowed"),
        ("HALT", "Longs allowed"),
    ):
        assert _verdict_sentence(state, verb, mixed_artifacts=False) == "", (state, verb)
    # a no-trade / permitted state never yields a trade-direction verb, whatever
    # the regime verb argument is.
    for verb in _DIRECTION_VERBS + ("Stand down",):
        assert _verdict_sentence("STAY FLAT", verb, mixed_artifacts=False) not in _DIRECTION_VERBS
        assert _verdict_sentence("TRADE PERMITTED", verb, mixed_artifacts=False) not in _DIRECTION_VERBS


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


# ---------------------------------------------------------------------------
# PRD-335 F3 (Helm 2026-09-05) — VISIBLE-LINE verdict cardinality matrix.
# Exactly ONE primary state line + ZERO-or-ONE causal reason + ONE compact regime
# line. A second verdict/reason line anywhere makes these RED. (Kill switch is a
# distinct safety indicator, not a verdict/permission paraphrase, and is allowed.)
# ---------------------------------------------------------------------------

def _mm_hg():
    return _market_map({"SPY": _mm_symbol("SPY", grade="A+")})


_CARDINALITY_CASES = {
    "trade_risk_on":  ("RISK_ON",  _run(regime="RISK_ON",  outcome="TRADE"), 0),
    "trade_risk_off": ("RISK_OFF", _run(regime="RISK_OFF", outcome="TRADE"), 0),
    "trade_neutral":  ("NEUTRAL",  _run(regime="NEUTRAL",  outcome="TRADE"), 0),
    "stay_flat":      ("NEUTRAL",  _run(regime="NEUTRAL", posture="STAY_FLAT", outcome="NO_TRADE"), 1),
    "halt":           ("RISK_ON",  _run(system_halted=True, kill_switch=True, outcome="NO_TRADE"), 1),
    "operator_lock":  ("NEUTRAL",  _run(regime="NEUTRAL", outcome="NO_TRADE",
                                        permission=config.OPERATOR_LOCK_PERMISSION), 1),
}


@pytest.mark.parametrize("name", sorted(_CARDINALITY_CASES))
def test_f3_verdict_cardinality_matrix(name) -> None:
    regime, run, expected_reasons = _CARDINALITY_CASES[name]
    html = render_dashboard_html(_payload(market_regime=regime), run, market_map=_mm_hg())
    primary, reasons, regime_lines, _kill = _verdict_lines(html)
    assert len(primary) == 1, (name, primary)                 # exactly one primary state line
    assert len(reasons) == expected_reasons, (name, reasons)  # zero-or-one causal reason
    assert len(regime_lines) == 1, (name, regime_lines)       # one compact regime line
    # a permitted trade shows NO direction verb as a VISIBLE second sentence
    # (the raw verb legitimately survives in the data-raw-permission attribute).
    if name.startswith("trade"):
        for verb in _DIRECTION_VERBS:
            assert verb not in _visible_text(html), (name, verb)
    # under the operator lock the single reason IS the lock, never a WHY line
    if name == "operator_lock":
        assert reasons == [config.OPERATOR_LOCK_PERMISSION], reasons
        assert "WHY:" not in _visible_text(html)


def test_f3_mixed_artifact_cardinality() -> None:
    payload, run, mm = _payload(market_regime="RISK_ON"), _run(outcome="TRADE"), _mm()
    _mixed_ids(payload, run, mm)
    html = render_dashboard_html(payload, run, market_map=mm)
    primary, reasons, regime_lines, _kill = _verdict_lines(html)
    assert len(primary) == 1
    assert reasons == ["Inputs out of sync"]        # exactly one explanatory reason
    assert len(regime_lines) == 1
