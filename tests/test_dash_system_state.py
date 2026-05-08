"""Tests for PRD-055 — dashboard renderer: System state, action line, decision title, posture labels."""

from __future__ import annotations

from cuttingboard.delivery.dashboard_renderer import render_dashboard_html

from tests.dash_helpers import _payload, _run


# ---------------------------------------------------------------------------
# R2 / R2.1 — System State Block
# ---------------------------------------------------------------------------

def test_system_state_block_fields() -> None:
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run(posture="CONTROLLED_LONG", confidence=0.75))
    state = html.split('id="system-state"', 1)[1]
    assert "RISK_ON" in state
    assert "0.75" in state
    assert 'class="action-line"' in state


def test_system_state_regime_badge_class() -> None:
    html = render_dashboard_html(_payload(market_regime="RISK_OFF"), _run())
    assert 'class="badge RISK_OFF"' in html


def test_system_state_regime_badge_risk_on_class() -> None:
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run())
    assert 'class="badge RISK_ON"' in html


def test_system_state_permission_shows_dash_when_none() -> None:
    r = _run(permission=None)
    html = render_dashboard_html(_payload(), r)
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Permission" in state
    assert "&#8212;" in state


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


def test_action_line_stay_flat() -> None:
    r = _run(outcome="STAY_FLAT")
    html = render_dashboard_html(_payload(), r)
    assert "ACTION: WAIT" in html
    assert "NO VALID SETUPS" in html


def test_action_line_blocked() -> None:
    r = _run(permission=False)
    html = render_dashboard_html(_payload(), r)
    assert "ACTION: WATCH" in html
    assert "SETUPS PRESENT BUT BLOCKED" in html


def test_action_line_active() -> None:
    r = _run(permission=True)
    html = render_dashboard_html(_payload(), r)
    assert "ACTION: ACTIVE" in html
    assert "TRADE CONDITIONS MET" in html


def test_action_line_monitor_default() -> None:
    r = _run(outcome="NO_TRADE", permission=None)
    html = render_dashboard_html(_payload(), r)
    assert "ACTION: MONITOR" in html
    assert "SYSTEM ACTIVE" in html


def test_action_line_is_first_in_system_state() -> None:
    html = render_dashboard_html(_payload(), _run())
    state_start = html.index('id="system-state"')
    action_pos  = html.index('class="action-line"')
    regime_pos  = html.index('class="badge ')
    assert state_start < action_pos < regime_pos


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


def test_posture_label_aggressive_long_in_history() -> None:
    hr = _run(posture="AGGRESSIVE_LONG")
    hr["timestamp"] = "2026-04-28T12:00:00Z"
    html = render_dashboard_html(_payload(), _run(), history_runs=[hr])
    assert "Aggressive Long" in html.split('id="run-history"', 1)[1]


def test_posture_label_defensive_short_in_history() -> None:
    hr = _run(posture="DEFENSIVE_SHORT")
    hr["timestamp"] = "2026-04-28T12:00:00Z"
    html = render_dashboard_html(_payload(), _run(), history_runs=[hr])
    assert "Defensive Short" in html.split('id="run-history"', 1)[1]


def test_posture_label_unknown_passthrough() -> None:
    hr = _run(posture="UNKNOWN_POSTURE_XYZ")
    hr["timestamp"] = "2026-04-28T12:00:00Z"
    html = render_dashboard_html(_payload(), _run(), history_runs=[hr])
    assert "UNKNOWN_POSTURE_XYZ" in html.split('id="run-history"', 1)[1]


def test_posture_label_in_run_delta() -> None:
    current  = _run(posture="AGGRESSIVE_LONG")
    previous = _run(posture="STAY_FLAT")
    html = render_dashboard_html(_payload(), current, previous_run=previous)
    delta = html.split('id="run-delta"', 1)[1]
    assert "Aggressive Long" in delta
    assert "Stay Flat" in delta
    assert "AGGRESSIVE_LONG" not in delta
    assert "STAY_FLAT" not in delta


def test_posture_label_in_run_history() -> None:
    hr = _run(posture="NEUTRAL_PREMIUM")
    hr["timestamp"] = "2026-04-28T12:00:00Z"
    html = render_dashboard_html(_payload(), _run(), history_runs=[hr])
    history = html.split('id="run-history"', 1)[1]
    assert "Neutral Premium" in history
    assert "NEUTRAL_PREMIUM" not in history


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
