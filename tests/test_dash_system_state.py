"""Tests for PRD-055 — dashboard renderer: System state, action line, decision title, posture labels."""

from __future__ import annotations

import re

from cuttingboard import config
from cuttingboard.delivery.dashboard_renderer import render_dashboard_html

from tests.dash_helpers import _macro_drivers, _market_map, _mm_symbol, _payload, _run


# ---------------------------------------------------------------------------
# PRD-315 depth-aware top-level extraction (test-local; replaces Candidate-
# relative substring sentinels invalidated by the Opportunity->Candidate move).
# ---------------------------------------------------------------------------

def _top_ids(html: str) -> list[str]:
    """Ordered top-level `.block` ids via depth-aware sibling scan."""
    ids: list[str] = []
    i = 0
    while True:
        j = html.find('class="block', i)
        if j == -1:
            break
        k = html.find('id="', j)
        e = html.find('"', k + 4)
        ids.append(html[k + 4:e])
        i = e
    return ids


def _top_block(html: str, block_id: str) -> str:
    """Exact `<div ... id="{block_id}"> ... </div>` fragment (matches nested divs)."""
    marker = f'id="{block_id}"'
    idx = html.find(marker)
    assert idx != -1, f"{block_id} not rendered"
    start = html.rfind("<div", 0, idx)
    i, depth = start, 0
    while i < len(html):
        nd = html.find("<div", i)
        nc = html.find("</div>", i)
        if nc == -1:
            break
        if nd != -1 and nd < nc:
            depth += 1
            i = nd + 4
        else:
            depth -= 1
            i = nc + 6
            if depth == 0:
                return html[start:i]
    return html[start:]


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
    state = _top_block(html, "system-state")
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
    state = _top_block(html, "system-state")
    # PRD-219: no Permission field / no dash placeholder; a distilled verdict.
    assert 'class="sys-verdict' in state
    assert ">&#8212;<" not in state
    assert ">Permission<" not in state


def test_system_state_stay_flat_omitted_when_none() -> None:
    html = render_dashboard_html(_payload(validation_halt_detail=None), _run())
    state = _top_block(html, "system-state")
    assert "Stay Flat" not in state


def test_system_state_stay_flat_present_when_set() -> None:
    # PRD-219: the non-halt STAY_FLAT posture string is no longer surfaced in the
    # distilled panel (the verdict + context convey the no-trade state instead).
    html = render_dashboard_html(
        _payload(validation_halt_detail={"reason": "STAY_FLAT posture"}), _run()
    )
    state = _top_block(html, "system-state")
    assert "STAY_FLAT posture" not in state


def test_system_state_no_redundant_permission_copy() -> None:
    """The authoritative permission renders once without the stale posture internals."""
    html = render_dashboard_html(
        _payload(validation_halt_detail={"reason": "STAY_FLAT posture (regime=RISK_OFF, confidence=0.25)"}),
        _run(permission="No new trades permitted."),
    )
    state = _top_block(html, "system-state")
    # PRD-318 correction: retain one authoritative permission sentence without
    # restoring the old labelled projection or confidence-laden posture string.
    assert ">Permission<" not in state
    assert "confidence=" not in state
    assert state.count('class="sys-permission"') == 1
    assert state.count("No new trades permitted.") == 1
    assert 'class="sys-verdict' in state


def test_system_state_permission_fallback_when_no_reason() -> None:
    """Shows permission text when stay_flat_reason is absent."""
    html = render_dashboard_html(
        _payload(validation_halt_detail=None),
        _run(permission="No new trades permitted."),
    )
    state = _top_block(html, "system-state")
    assert 'class="sys-verdict' in state
    assert state.count('class="sys-permission"') == 1
    assert state.count("No new trades permitted.") == 1


def test_system_state_permission_shows_from_run_when_non_null() -> None:
    """Permission shows the run value when run.permission is a non-null string."""
    r = _run(permission="No new trades permitted.")
    html = render_dashboard_html(_payload(), r)
    state = _top_block(html, "system-state")
    assert 'class="sys-verdict' in state
    assert state.count('class="sys-permission"') == 1
    assert state.count("No new trades permitted.") == 1
    assert "&#8212;" not in state


def test_system_state_permission_falls_back_to_payload_when_run_none() -> None:
    """When run.permission is None, Permission shows payload['summary']['permission'] value."""
    payload_with_perm = _payload()
    payload_with_perm["summary"]["permission"] = "No new trades permitted."
    r = _run(permission=None)
    html = render_dashboard_html(payload_with_perm, r)
    state = _top_block(html, "system-state")
    assert 'class="sys-verdict' in state
    assert state.count('class="sys-permission"') == 1
    assert state.count("No new trades permitted.") == 1


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
    state = _top_block(html, "system-state")
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
    state = _top_block(html, "system-state")
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


def test_prd281_why_line_suppressed_for_sentinel_with_regime_suffix() -> None:
    # Codex correction (P2, round 2): a sentinel combined with engine
    # metadata -- "None (regime=RISK_OFF, confidence=0.25)" -- must not
    # strip down to a bare "None"/"NULL" that then renders raw. The
    # sentinel check must re-run on the post-strip result, not just the
    # original string.
    run = _run(system_halted=True, errors=["None (regime=RISK_OFF, confidence=0.25)"])
    html = render_dashboard_html(_payload(), run)
    state = _header_block(html)
    assert not _has_why(state)
    assert "WHY: None" not in state


def test_prd281_why_line_suppressed_for_sentinel_with_confidence_suffix() -> None:
    run = _run(system_halted=True, errors=["NULL confidence=0.25"])
    html = render_dashboard_html(_payload(), run)
    state = _header_block(html)
    assert not _has_why(state)
    assert "WHY: NULL" not in state


# ---------------------------------------------------------------------------
# PRD-282 — Opportunity Survival Summary
# ---------------------------------------------------------------------------

def _survival_block(html: str) -> str | None:
    # PRD-330 R5: the opportunity funnel is ONE `<p class="screen-line">` under the
    # WATCHING heading (the old `#opportunity-survival` grid is gone). Returns the
    # line's text, or None when the fail-closed conditions suppressed it.
    m = re.search(r'<p class="screen-line">([^<]*)</p>', html)
    return m.group(1) if m else None


def _survival_pairs(html: str) -> dict[str, str]:
    # The PRD-282 counts projected out of the PRD-330 line: SURFACED / QUALIFIED
    # (or SETUPS FOUND under lock; "0" when the token is omitted) / WATCHLIST /
    # REJECTED / PRIMARY REJECTION (absent when no primary reason exists).
    line = _survival_block(html)
    assert line is not None
    pairs = {"SURFACED": re.search(r"(\d+) screened", line).group(1),
             "WATCHLIST": re.search(r"(\d+) (?:held by the 3:30 PM cutoff|on watch)", line).group(1),
             "REJECTED": re.search(r"(\d+) rejected", line).group(1)}
    q = re.search(r"(\d+) (qualified|setups found)", line)
    pairs["SETUPS FOUND" if q and q.group(2) == "setups found" else "QUALIFIED"] = q.group(1) if q else "0"
    top = re.search(r"top reason (.+) \((\d+)\)$", line)
    if top:
        pairs["PRIMARY REJECTION"] = top.group(1)
    return pairs


def _survival_label_order(html: str) -> list[str]:
    # PRD-330 R5 token order (the grammar's fixed sequence), by token kind.
    line = _survival_block(html)
    assert line is not None
    kinds = {"screened": "SURFACED", "qualified": "QUALIFIED", "setups found": "SETUPS FOUND", "held": "WATCHLIST",
             "on watch": "WATCHLIST", "rejected": "REJECTED", "top reason": "PRIMARY REJECTION"}
    return [kinds[k] for part in line.split(" · ") for k in kinds if k in part][:5]


def _coherent_survival(
    scanned: int,
    rejected_reasons: tuple[str, ...] = (),
    watchlist_n: int = 0,
) -> tuple[dict, dict, dict]:
    """Coherent-lineage payload/run/market_map with the given survival shape.

    Coherent lineage requires matching generation_ids and a non-stale market
    map, which the default fixtures already provide (all share
    generation_id "test-gen-001" and timestamp "2026-04-28T12:00:00Z").
    """
    payload = _payload()
    payload["meta"]["symbols_scanned"] = scanned
    payload["sections"]["rejected"] = [
        {"symbol": f"R{i}", "stage": "QUALIFICATION", "reason": reason, "detail": None}
        for i, reason in enumerate(rejected_reasons)
    ]
    payload["sections"]["watchlist"] = [
        {"symbol": f"W{i}", "stage": "WATCHLIST", "reason": "ONE_SOFT_MISS", "detail": None}
        for i in range(watchlist_n)
    ]
    return payload, _run(), _market_map()


def test_prd282_survival_counts_reconcile() -> None:
    # R1: coherent lineage, 12 surfaced, 3 rejected, 2 watchlist ->
    # SURFACED 12 / QUALIFIED 7 / WATCHLIST 2 / REJECTED 3. QUALIFIED is the
    # derived remainder; the four counts must reconcile with symbols_scanned.
    payload, run, mm = _coherent_survival(
        12, rejected_reasons=("CHOP", "CHOP", "EXTENDED_FROM_MEAN"), watchlist_n=2
    )
    html = render_dashboard_html(payload, run, market_map=mm)
    pairs = _survival_pairs(html)
    assert pairs["SURFACED"] == "12"
    assert pairs["QUALIFIED"] == "7"
    assert pairs["WATCHLIST"] == "2"
    assert pairs["REJECTED"] == "3"


def test_prd283_survival_counts_options_sizing_refusal() -> None:
    # PRD-283 (CB-02): an OPTIONS_SIZING refusal in sections["rejected"] is
    # counted as REJECTED (additive payload split) and surfaced as the PRIMARY
    # REJECTION reason — the survival summary agrees with the WHY line.
    payload, run, mm = _coherent_survival(5)
    payload["sections"]["rejected"] = [
        {"symbol": "SPY", "stage": "OPTIONS_SIZING",
         "reason": "SMALLEST_CONTRACT_EXCEEDS_BUDGET", "detail": None},
    ]
    html = render_dashboard_html(payload, run, market_map=mm)
    pairs = _survival_pairs(html)
    assert pairs["SURFACED"] == "5"
    assert pairs["REJECTED"] == "1"
    assert pairs["QUALIFIED"] == "4"  # 5 surfaced - 1 rejected - 0 watchlist
    block = _survival_block(html) or ""
    assert "SMALLEST_CONTRACT_EXCEEDS_BUDGET" in block


def test_prd282_survival_zero_rejections_no_primary_row() -> None:
    # R1 + R3: no rejections -> the four counts render, and NO PRIMARY
    # REJECTION row is emitted.
    payload, run, mm = _coherent_survival(5)
    html = render_dashboard_html(payload, run, market_map=mm)
    pairs = _survival_pairs(html)
    assert pairs["SURFACED"] == "5"
    assert pairs["QUALIFIED"] == "5"
    assert pairs["WATCHLIST"] == "0"
    assert pairs["REJECTED"] == "0"
    assert "PRIMARY REJECTION" not in (_survival_block(html) or "")


def test_prd282_survival_suppressed_on_zero_scan() -> None:
    # R2: symbols_scanned == 0 -> the block is absent entirely.
    payload, run, mm = _coherent_survival(0)
    html = render_dashboard_html(payload, run, market_map=mm)
    assert 'id="opportunity-survival"' not in html


def test_prd282_survival_suppressed_on_mixed_lineage() -> None:
    # R2: mixed artifacts (unhealthy lineage) -> no block even with a real
    # scan, mirroring the card/decision-state suppression.
    payload, run, mm = _coherent_survival(12, rejected_reasons=("CHOP",))
    payload["meta"]["generation_id"] = "gen-a"
    run["generation_id"] = "gen-b"
    mm["generation_id"] = "gen-a"
    html = render_dashboard_html(payload, run, market_map=mm)
    assert 'id="opportunity-survival"' not in html


def test_prd282_survival_suppressed_on_missing_market_map() -> None:
    # R2: no market_map -> MISSING lineage -> no block.
    payload, run, _mm = _coherent_survival(12, rejected_reasons=("CHOP",))
    html = render_dashboard_html(payload, run)
    assert 'id="opportunity-survival"' not in html


def test_prd282_survival_suppressed_on_non_int_scan() -> None:
    # R2: a missing or non-int symbols_scanned suppresses the block (the
    # isinstance guard), never rendering garbage or raising. payload.py always
    # emits an int, so this guards the defensive branch R2's prose names.
    payload, run, mm = _coherent_survival(5)
    del payload["meta"]["symbols_scanned"]  # missing key -> .get() returns None
    assert 'id="opportunity-survival"' not in render_dashboard_html(payload, run, market_map=mm)

    payload2, run2, mm2 = _coherent_survival(5)
    payload2["meta"]["symbols_scanned"] = "5"  # non-int
    assert 'id="opportunity-survival"' not in render_dashboard_html(payload2, run2, market_map=mm2)


def test_prd282_primary_rejection_is_modal_reason() -> None:
    # R3: the most frequent reason among rejected records wins.
    payload, run, mm = _coherent_survival(
        9, rejected_reasons=("CHOP", "CHOP", "EXTENDED_FROM_MEAN")
    )
    html = render_dashboard_html(payload, run, market_map=mm)
    assert _survival_pairs(html)["PRIMARY REJECTION"] == "CHOP"


def test_prd282_primary_rejection_tie_break_is_lexicographic() -> None:
    # R3: on a count tie, the lexicographically smallest reason wins
    # deterministically -- insertion order (B before A) must NOT decide it.
    payload, run, mm = _coherent_survival(7, rejected_reasons=("B_REASON", "A_REASON"))
    html = render_dashboard_html(payload, run, market_map=mm)
    assert _survival_pairs(html)["PRIMARY REJECTION"] == "A_REASON"


def test_prd282_primary_rejection_is_html_escaped() -> None:
    # R4: reason text passes through _esc; no raw markup leaks into the block.
    payload, run, mm = _coherent_survival(4, rejected_reasons=("<b>CHOP</b>",))
    html = render_dashboard_html(payload, run, market_map=mm)
    block = _survival_block(html)
    assert block is not None
    assert "<b>CHOP</b>" not in block
    assert "&lt;b&gt;CHOP&lt;/b&gt;" in block


# ---------------------------------------------------------------------------
# PRD-282 correction (Codex P2 findings F1/F2/F3)
# ---------------------------------------------------------------------------

# A promoted-symbol scan: PRD-260 R4 keeps the DIRECT rejection on the audit
# trail (reason marked "promoted via CONTINUATION") AND counts the symbol as
# qualified, so symbols_scanned double-counts it. NVDA alone: qualified_count=1
# and rejected_count=1 -> symbols_scanned = 2, with one promoted rejection record.
_PROMOTED = "DIRECT rejected (CHOP); promoted via CONTINUATION"


def test_prd282_promoted_continuation_counted_as_qualified_not_rejected() -> None:
    # F1: a promoted symbol is represented once, as qualified -- not as a
    # rejection, and not double-counted in surfaced.
    payload, run, mm = _coherent_survival(2, rejected_reasons=(_PROMOTED,))
    html = render_dashboard_html(payload, run, market_map=mm)
    pairs = _survival_pairs(html)
    assert pairs["SURFACED"] == "1"
    assert pairs["QUALIFIED"] == "1"
    assert pairs["WATCHLIST"] == "0"
    assert pairs["REJECTED"] == "0"
    assert "PRIMARY REJECTION" not in (_survival_block(html) or "")


def test_prd282_promoted_audit_record_not_primary_and_terminal_counts_hold() -> None:
    # F1: with one terminal rejection (CHOP) and one promoted record, the block
    # shows two distinct symbols -- SURFACED 2 / QUALIFIED 1 / REJECTED 1 -- and
    # the promoted audit line can NEVER be the primary rejection.
    # symbols_scanned = qualified(NVDA)=1 + rejected(AAA + NVDA-promoted)=2 = 3.
    payload, run, mm = _coherent_survival(3, rejected_reasons=("CHOP", _PROMOTED))
    html = render_dashboard_html(payload, run, market_map=mm)
    pairs = _survival_pairs(html)
    assert pairs["SURFACED"] == "2"
    assert pairs["QUALIFIED"] == "1"
    assert pairs["WATCHLIST"] == "0"
    assert pairs["REJECTED"] == "1"
    assert pairs["PRIMARY REJECTION"] == "CHOP"
    assert "promoted via CONTINUATION" not in (_survival_block(html) or "")


def test_prd282_ordinary_terminal_counts_unchanged_by_promotion_filter() -> None:
    # F1 (no regression): a scan with no promoted records is unaffected -- the
    # 12/3/2 reconciliation still holds exactly.
    payload, run, mm = _coherent_survival(
        12, rejected_reasons=("CHOP", "CHOP", "EXTENDED_FROM_MEAN"), watchlist_n=2
    )
    pairs = _survival_pairs(render_dashboard_html(payload, run, market_map=mm))
    assert (pairs["SURFACED"], pairs["QUALIFIED"], pairs["WATCHLIST"], pairs["REJECTED"]) == (
        "12", "7", "2", "3",
    )


def test_prd282_survival_suppressed_on_bool_scan() -> None:
    # F2: symbols_scanned = True (bool is an int subclass) must NOT render as 1.
    payload, run, mm = _coherent_survival(5)
    payload["meta"]["symbols_scanned"] = True
    assert 'id="opportunity-survival"' not in render_dashboard_html(payload, run, market_map=mm)


def test_prd282_survival_suppressed_on_non_list_sections() -> None:
    # F2: a non-list rejected/watchlist must suppress the block, never count a
    # string's length or raise.
    payload, run, mm = _coherent_survival(5)
    payload["sections"]["rejected"] = "abc"
    assert 'id="opportunity-survival"' not in render_dashboard_html(payload, run, market_map=mm)

    payload2, run2, mm2 = _coherent_survival(5)
    payload2["sections"]["watchlist"] = 5
    assert 'id="opportunity-survival"' not in render_dashboard_html(payload2, run2, market_map=mm2)


def test_prd282_survival_suppressed_on_malformed_record() -> None:
    # F2: a rejected list containing a non-dict record must suppress safely
    # (no AttributeError from .get on a str).
    payload, run, mm = _coherent_survival(5, rejected_reasons=("CHOP",))
    payload["sections"]["rejected"] = [
        {"symbol": "AAA", "stage": "QUALIFICATION", "reason": "CHOP", "detail": None},
        "not-a-dict",
    ]
    assert 'id="opportunity-survival"' not in render_dashboard_html(payload, run, market_map=mm)


def test_prd282_primary_rejection_strips_engine_metadata() -> None:
    # F3: raw engine internals (regime=/confidence=) must not leak into PRIMARY
    # REJECTION -- stripped by the same policy as the system-state WHY line.
    payload, run, mm = _coherent_survival(
        4, rejected_reasons=("bad (regime=RISK_ON, confidence=0.8)",)
    )
    html = render_dashboard_html(payload, run, market_map=mm)
    block = _survival_block(html)
    assert block is not None
    assert _survival_pairs(html)["PRIMARY REJECTION"] == "bad"
    assert "regime=" not in block
    assert "confidence=" not in block


def test_prd282_primary_rejection_sanitized_text_still_escaped() -> None:
    # F3 + R4: sanitize (strip engine metadata) and HTML-escape compose --
    # the surviving text is still escaped.
    payload, run, mm = _coherent_survival(
        4, rejected_reasons=("<b>bad</b> (regime=RISK_ON)",)
    )
    html = render_dashboard_html(payload, run, market_map=mm)
    block = _survival_block(html)
    assert block is not None
    assert "regime=" not in block
    assert "<b>bad</b>" not in block
    assert "&lt;b&gt;bad&lt;/b&gt;" in block


# ---------------------------------------------------------------------------
# PRD-314 — Opportunity child order the phone 2x2 grid depends on
# ---------------------------------------------------------------------------

def test_prd314_opportunity_child_order_primary_present() -> None:
    # PRIMARY REJECTION present -> five label/value pairs (ten children) in the
    # exact sequence the phone 2x2 grid + full-width rejection row rely on.
    payload, run, mm = _coherent_survival(10, rejected_reasons=("CHOP",) * 3, watchlist_n=1)
    html = render_dashboard_html(payload, run, market_map=mm)
    assert _survival_label_order(html) == [
        "SURFACED", "WATCHLIST", "QUALIFIED", "REJECTED", "PRIMARY REJECTION",
    ]


def test_prd314_opportunity_child_order_primary_absent() -> None:
    # No rejections -> exactly the four metric pairs (eight children), no empty
    # trailing grid row.
    payload, run, mm = _coherent_survival(5)
    html = render_dashboard_html(payload, run, market_map=mm)
    assert _survival_label_order(html) == ["SURFACED", "WATCHLIST", "QUALIFIED", "REJECTED"]
    assert "top reason" not in _survival_block(html)


# ---------------------------------------------------------------------------
# PRD-315 — Opportunity/Candidate independence under continuity adjacency.
# The move places Candidate immediately after Opportunity; adjacency must never
# read as a survivor/lineage claim (packet section 11.2 mandatory fixture).
# ---------------------------------------------------------------------------

def test_prd315_qualified_zero_with_independent_b_candidate() -> None:
    # QUALIFIED 0 funnel coexisting with an independent B DEVELOPING Candidate:
    # the Opportunity count (derived from the payload survival funnel) and the
    # Candidate population (driven by market_map) are separate carriers. Their
    # top-level adjacency communicates operator reading sequence, not data
    # lineage -- there is no carrier join and no survivor claim.
    payload, run, _empty = _coherent_survival(1, rejected_reasons=("CHOP",))  # 1 - 1 - 0
    mm = _market_map({"GLD": _mm_symbol("GLD", grade="B")})
    html = render_dashboard_html(payload, run, market_map=mm)

    # The screen line renders and its derived QUALIFIED is 0 (scanned 1 > 0 => line present);
    # PRD-330 R5 omits the zero token, so the projection reports "0".
    assert _survival_block(html) is not None and "qualified" not in _survival_block(html)
    pairs = _survival_pairs(html)
    assert pairs["SURFACED"] == "1"
    assert pairs["REJECTED"] == "1"
    assert pairs["WATCHLIST"] == "0"
    assert pairs["QUALIFIED"] == "0"

    # The Candidate board independently renders the B DEVELOPING card.
    board = _top_block(html, "candidate-board")
    assert "B — DEVELOPING" in board
    assert 'id="card-GLD"' in board

    # Continuity: Candidate is the immediate top-level successor of Opportunity;
    # nothing intervenes, and no survivor-claim copy couples them.
    # PRD-330 R5: the screen line is the WATCHING opener and the board follows it directly.
    watching = _top_block(html, "watching-zone")
    assert watching.index('<p class="screen-line">') < watching.index('id="candidate-board"')
    assert "survived" not in board.lower()


# ---------------------------------------------------------------------------
# PRD-330 R5 (D-7) — the compact screen line's grammar and closed reason policy
# ---------------------------------------------------------------------------
def _watchlist(payload: dict, reasons: tuple[str, ...]) -> None:
    payload["sections"]["watchlist"] = [
        {"symbol": f"W{i}", "stage": "WATCHLIST", "reason": r, "detail": None} for i, r in enumerate(reasons)
    ]


def test_prd330_r5_screen_line_grammar_and_reason_policy() -> None:
    cutoff = "entry blocked after 3:30 PM ET"
    payload, run, mm = _coherent_survival(23, rejected_reasons=("CHOP",) * 4 + ("EXTENDED",) * 3 + ("GAP",) * 12, watchlist_n=4)
    _watchlist(payload, (cutoff,) * 4)
    line = _survival_block(render_dashboard_html(payload, run, market_map=mm))
    assert line == "23 screened · 4 held by the 3:30 PM cutoff · 19 rejected · top reason GAP (12)"
    assert "mostly" not in line and cutoff not in line
    _watchlist(payload, (cutoff, cutoff, "some internal token", cutoff))
    line = _survival_block(render_dashboard_html(payload, run, market_map=mm))
    assert line.startswith("23 screened · 4 on watch · ") and "internal token" not in line
    payload, run, mm = _coherent_survival(5, rejected_reasons=(), watchlist_n=0)
    assert _survival_block(render_dashboard_html(payload, run, market_map=mm)) == "5 screened · 0 on watch · 5 qualified · 0 rejected"
    payload, run, mm = _coherent_survival(3, rejected_reasons=("", ""), watchlist_n=1)   # rejected without reasons
    _watchlist(payload, ("unmapped",))
    assert _survival_block(render_dashboard_html(payload, run, market_map=mm)) == "3 screened · 1 on watch · 2 rejected"
    payload, run, mm = _coherent_survival(2, rejected_reasons=("CHOP",), watchlist_n=1)
    _watchlist(payload, (cutoff,))
    locked = render_dashboard_html(payload, _run(outcome="NO_TRADE", permission=config.OPERATOR_LOCK_PERMISSION), market_map=mm)
    assert _survival_block(locked) == "2 screened · 1 held by the 3:30 PM cutoff · 1 rejected · top reason CHOP (1)"
    payload, run, mm = _coherent_survival(3, rejected_reasons=("CHOP",), watchlist_n=0)
    locked = render_dashboard_html(payload, _run(outcome="NO_TRADE", permission=config.OPERATOR_LOCK_PERMISSION), market_map=mm)
    assert _survival_block(locked) == "3 screened · 0 on watch · 2 setups found · 1 rejected · top reason CHOP (1)"
    assert 'id="opportunity-survival"' not in locked and "PRIMARY REJECTION" not in locked
