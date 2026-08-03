"""Tests for PRD-055 — dashboard renderer: System state, action line, decision title, posture labels."""

from __future__ import annotations

from cuttingboard.delivery.dashboard_renderer import render_dashboard_html

from tests.dash_helpers import _macro_drivers, _market_map, _mm_symbol, _payload, _run


# ---------------------------------------------------------------------------
# R2 / R2.1 — System State Block
# ---------------------------------------------------------------------------

def test_system_state_block_fields() -> None:
    # PRD-158 § 4.2 translation 1: RISK_ON renders as "Longs allowed".
    # Translation 2 suppresses raw confidence.
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run(posture="CONTROLLED_LONG", confidence=0.75))
    state = html.split('id="system-state"', 1)[1]
    assert "Longs allowed" in state
    assert "0.75" not in state


def test_system_state_expansion_renders_momentum_longs() -> None:
    # PRD-163: EXPANSION is a first-class regime (regime.py) that previously
    # fell through _regime_to_permission_verb to the catch-all "Stand down",
    # contradicting the EXPANSION_LONG Permission line ("momentum allowed").
    # Reproduce the real pairing: regime=EXPANSION, posture=EXPANSION_LONG,
    # and the EXPANSION_LONG permission text in the Permission field. The
    # Regime field must render the long-directional verb, not "Stand down".
    expansion_permission = "EXPANSION — momentum allowed. Continuation entries. R:R >= 1.5."
    html = render_dashboard_html(
        _payload(market_regime="EXPANSION"),
        _run(posture="EXPANSION_LONG", permission=expansion_permission),
    )
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Momentum longs allowed" in state
    assert "Stand down" not in state


def test_system_state_regime_badge_class() -> None:
    # PRD-219: regime colour now rides the verdict line (no separate badge).
    html = render_dashboard_html(_payload(market_regime="RISK_OFF"), _run())
    assert 'class="sys-verdict sys-down"' in html


def test_system_state_regime_badge_risk_on_class() -> None:
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run())
    assert 'class="sys-verdict sys-up"' in html


def test_system_state_permission_shows_dash_when_none() -> None:
    # PRD-120: the former `&#8212;` Permission fallback is replaced with a
    # deterministic source-derived label. Under default _payload/_run with
    # no market_map, lineage is MISSING -> Permission renders UNKNOWN.
    r = _run(permission=None)
    html = render_dashboard_html(_payload(), r)
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    # PRD-219: no Permission field / no dash placeholder; a distilled verdict.
    assert 'class="sys-verdict' in state
    assert ">&#8212;<" not in state
    assert ">Permission<" not in state


def test_system_state_stay_flat_omitted_when_none() -> None:
    html = render_dashboard_html(_payload(validation_halt_detail=None), _run())
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Stay Flat" not in state


def test_system_state_stay_flat_present_when_set() -> None:
    # PRD-219: the non-halt STAY_FLAT posture string is no longer surfaced in the
    # distilled panel (the verdict + context convey the no-trade state instead).
    html = render_dashboard_html(
        _payload(validation_halt_detail={"reason": "STAY_FLAT posture"}), _run()
    )
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "STAY_FLAT posture" not in state


def test_system_state_no_redundant_permission_copy() -> None:
    """Single Permission field; stay_flat_reason is the shown value, not the permission text."""
    html = render_dashboard_html(
        _payload(validation_halt_detail={"reason": "STAY_FLAT posture (regime=RISK_OFF, confidence=0.25)"}),
        _run(permission="No new trades permitted."),
    )
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    # PRD-219: no Permission field; the distilled verdict replaces it, and the
    # confidence-laden posture string never appears.
    assert ">Permission<" not in state
    assert "confidence=" not in state
    assert "No new trades permitted." not in state
    assert 'class="sys-verdict' in state


def test_system_state_permission_fallback_when_no_reason() -> None:
    """Shows permission text when stay_flat_reason is absent."""
    html = render_dashboard_html(
        _payload(validation_halt_detail=None),
        _run(permission="No new trades permitted."),
    )
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    # PRD-219: the raw permission text is no longer echoed; the verdict conveys it.
    assert 'class="sys-verdict' in state
    assert "No new trades permitted." not in state


def test_system_state_permission_shows_from_run_when_non_null() -> None:
    """Permission shows the run value when run.permission is a non-null string."""
    r = _run(permission="No new trades permitted.")
    html = render_dashboard_html(_payload(), r)
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert 'class="sys-verdict' in state
    assert "No new trades permitted." not in state
    assert "&#8212;" not in state


def test_system_state_permission_falls_back_to_payload_when_run_none() -> None:
    """When run.permission is None, Permission shows payload['summary']['permission'] value."""
    payload_with_perm = _payload()
    payload_with_perm["summary"]["permission"] = "No new trades permitted."
    r = _run(permission=None)
    html = render_dashboard_html(payload_with_perm, r)
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert 'class="sys-verdict' in state
    assert "No new trades permitted." not in state


# ---------------------------------------------------------------------------
# PRD-073 — R1: Decision-first header
# ---------------------------------------------------------------------------

def _header_block(html: str) -> str:
    return html.split('id="system-state"', 1)[1].split('id="macro-tape"', 1)[0]


def test_decision_title_system_halt_status_fail() -> None:
    html = render_dashboard_html(_payload(), _run(status="FAIL"))
    assert "SYSTEM HALT" in _header_block(html)


def test_decision_title_system_halt_status_error() -> None:
    html = render_dashboard_html(_payload(), _run(status="ERROR"))
    assert "SYSTEM HALT" in _header_block(html)


def test_decision_title_system_halt_system_halted_true() -> None:
    html = render_dashboard_html(_payload(), _run(system_halted=True))
    assert "SYSTEM HALT" in _header_block(html)


# ---------------------------------------------------------------------------
# PRD-280 — halt color derives from title, not system_halted alone
# ---------------------------------------------------------------------------

def test_prd280_status_fail_system_halted_false_renders_halt_color() -> None:
    # R1 (red pre-change): a status=FAIL run with system_halted=False and a
    # RISK_ON regime must still color both verdicts sys-halt, not the
    # regime's own (green) class.
    html = render_dashboard_html(
        _payload(market_regime="RISK_ON"), _run(status="FAIL", system_halted=False)
    )
    state = _header_block(html)
    assert 'class="decision-state sys-halt">HALT</div>' in state
    assert 'class="sys-verdict sys-halt"' in state
    assert "SYSTEM HALT" in state
    assert "sys-up" not in state


def test_prd280_status_error_system_halted_false_renders_halt_color() -> None:
    # R1 (red pre-change): same as above for status=ERROR.
    html = render_dashboard_html(
        _payload(market_regime="RISK_ON"), _run(status="ERROR", system_halted=False)
    )
    state = _header_block(html)
    assert 'class="decision-state sys-halt">HALT</div>' in state
    assert 'class="sys-verdict sys-halt"' in state
    assert "SYSTEM HALT" in state
    assert "sys-up" not in state


def test_prd280_system_halted_true_still_renders_halt_color() -> None:
    # R2: explicit system_halted=True is unaffected by the R1 change.
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run(system_halted=True))
    state = _header_block(html)
    assert 'class="decision-state sys-halt">HALT</div>' in state
    assert 'class="sys-verdict sys-halt"' in state


def test_prd280_mixed_artifacts_with_explicit_halt_preserves_halt_color() -> None:
    # Codex correction (P2): when artifact generation IDs are mixed, `title`
    # is overridden to "MIXED_ARTIFACTS" even if system_halted=True -- the
    # R1 title-only check would then lose the red sys-halt signal on
    # .sys-verdict (falling to the RISK_ON regime's green sys-up) for a
    # genuinely halted run. system_halted must still force sys-halt.
    payload = _payload(market_regime="RISK_ON")
    run = _run(system_halted=True)
    mm = _market_map()
    payload["meta"]["generation_id"] = "gen-a"
    run["generation_id"] = "gen-b"
    mm["generation_id"] = "gen-a"

    html = render_dashboard_html(payload, run, market_map=mm)
    state = _header_block(html)
    assert "MIXED_ARTIFACTS" in state
    assert 'class="sys-verdict sys-halt"' in state
    assert "sys-up" not in state


def test_prd280_normal_risk_on_run_still_renders_sys_up() -> None:
    # R2: a non-halted, non-failed, no-trade run keeps its regime coloring.
    html = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(status="SUCCESS", system_halted=False, outcome="NO_TRADE"),
    )
    state = _header_block(html)
    assert 'class="decision-state sys-up">STAY FLAT</div>' in state
    assert 'class="sys-verdict sys-up"' in state


def test_prd280_trade_permitted_still_renders_its_own_color() -> None:
    # R2: TRADE PERMITTED is unaffected by the R1 change.
    html = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(status="SUCCESS", system_halted=False, outcome="TRADE"),
    )
    state = _header_block(html)
    assert 'class="decision-state sys-up">TRADE PERMITTED</div>' in state


def test_decision_title_trade() -> None:
    html = render_dashboard_html(_payload(), _run(outcome="TRADE"))
    assert "TRADE SETUP ACTIVE" in _header_block(html)


def test_decision_title_no_trade() -> None:
    html = render_dashboard_html(_payload(), _run(outcome="NO_TRADE"))
    assert "NO TRADE" in _header_block(html)


def test_decision_title_monitor_fallback() -> None:
    # Any outcome not matching a specific case falls through to MONITOR
    html = render_dashboard_html(_payload(), _run(outcome="STAY_FLAT", status="SUCCESS", system_halted=False))
    assert "MONITOR" in _header_block(html)


def test_decision_title_halt_takes_priority_over_trade_outcome() -> None:
    html = render_dashboard_html(_payload(), _run(outcome="TRADE", system_halted=True))
    assert "SYSTEM HALT" in _header_block(html)
    assert "TRADE SETUP ACTIVE" not in _header_block(html)


def test_prd162_decision_title_actionable_consistency() -> None:
    # PRD-162: the decision title follows the (now actionable-gated) outcome.
    # NO_TRADE must render the idle "NO TRADE" state, never a populated
    # "TRADE SETUP ACTIVE" card; TRADE renders the active title. This pins the
    # actionable / no-actionable consistency at the decision-title layer.
    no_trade = _header_block(render_dashboard_html(_payload(top_trades=[]), _run(outcome="NO_TRADE")))
    assert "NO TRADE" in no_trade
    assert "TRADE SETUP ACTIVE" not in no_trade

    trade = _header_block(render_dashboard_html(_payload(), _run(outcome="TRADE")))
    assert "TRADE SETUP ACTIVE" in trade


# ---------------------------------------------------------------------------
# PRD-073 — R2: Posture label mapping
# ---------------------------------------------------------------------------

def test_posture_label_controlled_long_in_delta() -> None:
    html = render_dashboard_html(_payload(), _run(posture="CONTROLLED_LONG"), previous_run=_run(posture="STAY_FLAT"))
    delta = html.split('id="run-delta"', 1)[1]
    assert "Controlled Long" in delta


def test_posture_label_stay_flat_in_delta() -> None:
    html = render_dashboard_html(_payload(), _run(posture="STAY_FLAT"), previous_run=_run(posture="CONTROLLED_LONG"))
    delta = html.split('id="run-delta"', 1)[1]
    assert "Stay Flat" in delta


def test_posture_label_in_run_delta() -> None:
    current  = _run(posture="AGGRESSIVE_LONG")
    previous = _run(posture="STAY_FLAT")
    html = render_dashboard_html(_payload(), current, previous_run=previous)
    delta = html.split('id="run-delta"', 1)[1]
    assert "Aggressive Long" in delta
    assert "Stay Flat" in delta
    assert "AGGRESSIVE_LONG" not in delta
    assert "STAY_FLAT" not in delta


def test_system_state_reason_no_candidates() -> None:
    """When permission=None, stay_flat=None, no alert_candidates: reason is 'no qualified candidates'."""
    html = render_dashboard_html(_payload(validation_halt_detail=None), _run(permission=None), alert_candidates=[])
    if 'id="alert-watchlist"' in html:
        state = html.split('id="system-state"', 1)[1].split('id="alert-watchlist"', 1)[0]
    else:
        state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    # PRD-281: the reason renders in the dedicated WHY line, not the context
    # line (supersedes PRD-219's "folds into the context line" choice).
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "no qualified setups" in why
    assert "candidates gated" not in state
    context = state.split('class="sys-context', 1)[1].split("</div>", 1)[0]
    assert "no qualified setups" not in context


def test_system_state_reason_candidates_gated() -> None:
    """When permission=None, stay_flat=None, alert_candidates non-empty: reason is 'candidates gated'."""
    from tests.dash_helpers import _trade_decision
    gated = [_trade_decision("META", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION")]
    html = render_dashboard_html(_payload(validation_halt_detail=None), _run(permission=None), alert_candidates=gated)
    if 'id="alert-watchlist"' in html:
        state = html.split('id="system-state"', 1)[1].split('id="alert-watchlist"', 1)[0]
    else:
        state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "candidates gated" in why
    assert "no qualified candidates" not in state
    context = state.split('class="sys-context', 1)[1].split("</div>", 1)[0]
    assert "candidates gated" not in context


# ---------------------------------------------------------------------------
# PRD-281 — Decision-State WHY Summary
# ---------------------------------------------------------------------------

def _has_why(state: str) -> bool:
    return 'class="sys-why"' in state


def test_prd281_halt_first_error_shows_why() -> None:
    run = _run(system_halted=True, errors=["disk full"])
    html = render_dashboard_html(_payload(), run)
    state = _header_block(html)
    assert 'class="decision-state sys-halt">HALT</div>' in state
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "disk full" in why


def test_prd281_halt_stay_flat_reason_shows_why_when_no_error() -> None:
    payload = _payload(validation_halt_detail={"reason": "STAY_FLAT regime"})
    run = _run(system_halted=True, errors=[])
    html = render_dashboard_html(payload, run)
    state = _header_block(html)
    assert 'class="decision-state sys-halt">HALT</div>' in state
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "STAY_FLAT regime" in why


def test_prd281_non_halt_explicit_error_shows_why() -> None:
    run = _run(system_halted=False, outcome="NO_TRADE", errors=["late data feed"])
    html = render_dashboard_html(_payload(), run)
    state = _header_block(html)
    assert 'class="decision-state sys-up">STAY FLAT</div>' in state
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "late data feed" in why


def test_prd281_no_qualified_setups_shows_why() -> None:
    html = render_dashboard_html(
        _payload(validation_halt_detail=None), _run(permission=None), alert_candidates=[]
    )
    state = _header_block(html)
    assert 'class="decision-state sys-up">STAY FLAT</div>' in state
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "no qualified setups" in why


def test_prd281_candidates_gated_shows_why() -> None:
    from tests.dash_helpers import _trade_decision
    gated = [_trade_decision("META", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION")]
    html = render_dashboard_html(
        _payload(validation_halt_detail=None), _run(permission=None), alert_candidates=gated
    )
    state = _header_block(html)
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "candidates gated" in why


def test_prd281_high_grade_setups_gated_shows_count_in_why() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A+"), "QQQ": _mm_symbol("QQQ", grade="A")})
    html = render_dashboard_html(
        _payload(validation_halt_detail=None), _run(permission=None, outcome="NO_TRADE"), market_map=mm
    )
    state = _header_block(html)
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "2 setups gated" in why


def test_prd281_trade_permitted_has_no_why_line() -> None:
    html = render_dashboard_html(_payload(), _run(system_halted=False, outcome="TRADE"))
    state = _header_block(html)
    assert 'class="decision-state sys-up">TRADE PERMITTED</div>' in state
    assert not _has_why(state)


def test_prd281_mixed_artifacts_no_trade_has_no_why_line() -> None:
    # The mandatory suppression: a lineage mismatch must never pair a
    # confident-looking reason (e.g. "no qualified setups") with
    # STATE UNAVAILABLE, even though outcome=NO_TRADE would otherwise
    # compute one.
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run(outcome="NO_TRADE")
    run["timestamp"] = "2026-04-28T12:00:00Z"
    mm = _market_map()
    payload["meta"]["generation_id"] = "gen-a"
    run["generation_id"] = "gen-b"
    mm["generation_id"] = "gen-a"

    html = render_dashboard_html(payload, run, market_map=mm)
    state = _header_block(html)
    assert 'class="decision-state sys-flat">STATE UNAVAILABLE</div>' in state
    assert not _has_why(state)
    assert "no qualified setups" not in state
    assert "candidates gated" not in state


def test_prd281_why_line_never_leaks_raw_internals() -> None:
    payload = _payload(
        validation_halt_detail={"reason": "STAY_FLAT posture (regime=RISK_OFF, confidence=0.25)"}
    )
    run = _run(system_halted=True, errors=[])
    html = render_dashboard_html(payload, run)
    state = _header_block(html)
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "(regime=" not in why
    assert "confidence=" not in why
    assert "None" not in why
    assert "NULL" not in why


def test_prd281_why_line_strips_bare_confidence_without_regime_prefix() -> None:
    # Codex correction (P2): a confidence=-bearing reason with no preceding
    # " (regime=" wrapper must still be sanitized, not pass through raw
    # because the old split() only fired on the combined format. Stripping
    # the entire reason here collapses it to nothing, so the WHY line is
    # correctly suppressed rather than showing an empty/raw value.
    run = _run(system_halted=True, errors=["confidence=0.25"])
    html = render_dashboard_html(_payload(), run)
    state = _header_block(html)
    assert not _has_why(state)
    assert "confidence=" not in state


def test_prd281_why_line_suppressed_for_literal_none_string() -> None:
    # Codex correction (P2): first_error/stay_flat_reason resolving to the
    # literal string "None" (e.g. str(None) from an upstream bug) must not
    # render "WHY: None" -- it is treated as no reason.
    run = _run(system_halted=True, errors=["None"])
    html = render_dashboard_html(_payload(), run)
    state = _header_block(html)
    assert not _has_why(state)


def test_prd281_why_line_suppressed_for_literal_null_string() -> None:
    payload = _payload(validation_halt_detail={"reason": "NULL"})
    run = _run(system_halted=True, errors=[])
    html = render_dashboard_html(payload, run)
    state = _header_block(html)
    assert not _has_why(state)
