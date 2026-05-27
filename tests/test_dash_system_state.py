"""Tests for PRD-055 — dashboard renderer: System state, action line, decision title, posture labels."""

from __future__ import annotations

from cuttingboard.delivery.dashboard_renderer import render_dashboard_html

from tests.dash_helpers import _payload, _run


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


def test_system_state_regime_badge_class() -> None:
    html = render_dashboard_html(_payload(market_regime="RISK_OFF"), _run())
    assert 'class="badge RISK_OFF"' in html


def test_system_state_regime_badge_risk_on_class() -> None:
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run())
    assert 'class="badge RISK_ON"' in html


def test_system_state_permission_shows_dash_when_none() -> None:
    # PRD-120: the former `&#8212;` Permission fallback is replaced with a
    # deterministic source-derived label. Under default _payload/_run with
    # no market_map, lineage is MISSING -> Permission renders UNKNOWN.
    r = _run(permission=None)
    html = render_dashboard_html(_payload(), r)
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Permission" in state
    perm_section = state.split("Permission", 1)[1].split("</div></div>", 1)[0]
    assert ">&#8212;<" not in perm_section
    assert "UNKNOWN" in perm_section


def test_system_state_stay_flat_omitted_when_none() -> None:
    html = render_dashboard_html(_payload(validation_halt_detail=None), _run())
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Stay Flat" not in state


def test_system_state_stay_flat_present_when_set() -> None:
    html = render_dashboard_html(
        _payload(validation_halt_detail={"reason": "STAY_FLAT posture"}), _run()
    )
    assert "STAY_FLAT posture" in html


def test_system_state_no_redundant_permission_copy() -> None:
    """Single Permission field; stay_flat_reason is the shown value, not the permission text."""
    html = render_dashboard_html(
        _payload(validation_halt_detail={"reason": "STAY_FLAT posture (regime=RISK_OFF, confidence=0.25)"}),
        _run(permission="No new trades permitted."),
    )
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    # single consolidated label
    assert "Permission" in state
    assert state.count(">Permission<") == 1
    # stay_flat_reason is the displayed value
    assert "STAY_FLAT posture" in state
    # permission text not shown separately; Stay Flat not a field label
    assert ">Stay Flat<" not in state
    assert "No new trades permitted." not in state
    # gold warn class present
    assert 'class="field warn"' in state


def test_system_state_permission_fallback_when_no_reason() -> None:
    """Shows permission text when stay_flat_reason is absent."""
    html = render_dashboard_html(
        _payload(validation_halt_detail=None),
        _run(permission="No new trades permitted."),
    )
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Permission" in state
    assert "No new trades permitted." in state


def test_system_state_permission_shows_from_run_when_non_null() -> None:
    """Permission shows the run value when run.permission is a non-null string."""
    r = _run(permission="No new trades permitted.")
    html = render_dashboard_html(_payload(), r)
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Permission" in state
    assert "No new trades permitted." in state
    assert "&#8212;" not in state


def test_system_state_permission_falls_back_to_payload_when_run_none() -> None:
    """When run.permission is None, Permission shows payload['summary']['permission'] value."""
    payload_with_perm = _payload()
    payload_with_perm["summary"]["permission"] = "No new trades permitted."
    r = _run(permission=None)
    html = render_dashboard_html(payload_with_perm, r)
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Permission" in state
    assert "No new trades permitted." in state


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
    assert "Reason" in state
    assert "no qualified candidates" in state
    assert "candidates gated" not in state


def test_system_state_reason_candidates_gated() -> None:
    """When permission=None, stay_flat=None, alert_candidates non-empty: reason is 'candidates gated'."""
    from tests.dash_helpers import _trade_decision
    gated = [_trade_decision("META", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION")]
    html = render_dashboard_html(_payload(validation_halt_detail=None), _run(permission=None), alert_candidates=gated)
    if 'id="alert-watchlist"' in html:
        state = html.split('id="system-state"', 1)[1].split('id="alert-watchlist"', 1)[0]
    else:
        state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Reason" in state
    assert "candidates gated" in state
    assert "no qualified candidates" not in state
