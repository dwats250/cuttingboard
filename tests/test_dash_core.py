"""Tests for PRD-055 — dashboard renderer: Core rendering, blocks, section order, auto-refresh, run delta, empty candidates."""

from __future__ import annotations

import copy

from cuttingboard.delivery.dashboard_renderer import (
    _DASHBOARD_REFRESH_SECONDS,
    render_dashboard_html,
)

from tests.dash_helpers import _macro_drivers, _market_map, _mm_symbol, _payload, _run, _trade, _trade_decision


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------

def test_field_mapping_exact() -> None:
    p = _payload(
        market_regime="CHAOTIC",
        tradable=False,
        timestamp="2026-01-15T09:30:00Z",
        validation_halt_detail={"reason": "VIX_SPIKE_HALT"},
    )
    r = _run(
        status="HALT",
        posture="STAY_FLAT",
        confidence=0.625,
        system_halted=True,
        kill_switch=False,
        errors=["quota_exceeded_unique"],
        data_status="stale",
    )
    html = render_dashboard_html(p, r)

    assert "2026-01-15" in html  # timestamp displayed in PT+Original format
    assert "HALT" in html
    assert "CHAOTIC" in html
    assert "STAY_FLAT" in html
    assert "0.625" in html
    assert "VIX_SPIKE_HALT" in html
    assert "YES" in html                    # system_halted=True
    assert "quota_exceeded_unique" in html  # errors[0]


def test_no_unapproved_fields() -> None:
    html = render_dashboard_html(_payload(), _run()).lower()
    for field in (
        "net_score",
        "router_mode",
        "run_id",
        "candidates_generated",
        "energy_score",
        "index_score",
        "schema_version",
        "symbols_scanned",
        "watchlist",
        "rejected",
    ):
        assert field not in html, f"Unapproved field rendered: {field}"


def test_deterministic_output() -> None:
    p = _payload()
    r = _run()
    assert render_dashboard_html(p, r) == render_dashboard_html(p, r)


def test_no_mutation() -> None:
    p = _payload(top_trades=[_trade("NVDA")])
    r = _run(errors=["some_error"])
    p_before = copy.deepcopy(p)
    r_before = copy.deepcopy(r)
    render_dashboard_html(p, r)
    assert p == p_before
    assert r == r_before


# ---------------------------------------------------------------------------
# R9 — removed block IDs absent
# ---------------------------------------------------------------------------

def test_removed_block_ids_absent() -> None:
    html = render_dashboard_html(
        _payload(top_trades=[_trade()], trade_decision_detail=[_trade_decision()]),
        _run(),
    )
    assert 'id="decision-summary"'  not in html
    assert 'id="primary-setup"'     not in html
    assert 'id="secondary-setups"'  not in html
    assert 'id="trade-decisions"'   not in html


def test_preserved_block_ids_present() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run(), history_runs=[_run()])
    assert 'id="dashboard-header"' in html
    assert 'id="run-health"'       in html
    assert 'id="run-delta"'        in html
    assert 'id="run-history"'      in html


# ---------------------------------------------------------------------------
# PRD-055 PATCH — auto-refresh meta
# ---------------------------------------------------------------------------

def test_auto_refresh_meta_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'http-equiv="refresh"' in html
    assert 'content="30"' in html


def test_dashboard_refresh_constant_value() -> None:
    assert _DASHBOARD_REFRESH_SECONDS == 30


# ---------------------------------------------------------------------------
# PRD-041 — run delta (present/absent with previous_run)
# ---------------------------------------------------------------------------

def test_run_delta_present_with_previous_run() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run(posture="STAY_FLAT"))
    assert 'id="run-delta"' in html


def test_run_delta_source_missing_without_previous_run() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=None)
    assert 'id="run-delta"' in html
    assert "SOURCE_MISSING" in html.split('id="run-delta"', 1)[1]


# ---------------------------------------------------------------------------
# PRD-073 — R5: Section order
# ---------------------------------------------------------------------------

def test_section_order_system_state_before_candidates() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert html.index('id="system-state"') < html.index('id="candidate-board"')


def test_section_order_system_state_before_run_delta() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run())
    assert html.index('id="system-state"') < html.index('id="run-delta"')


def test_section_order_full_r5_sequence() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="B")})
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), previous_run=_run(), market_map=mm)
    system_pos     = html.index('id="system-state"')
    health_pos     = html.index('id="run-health"')
    header_pos     = html.index('id="dashboard-header"')
    tape_pos       = html.index('id="macro-tape"')
    pressure_pos   = html.index('id="macro-pressure"')
    candidates_pos = html.index('id="candidate-board"')
    delta_pos      = html.index('id="run-delta"')
    assert system_pos < health_pos < header_pos < tape_pos < pressure_pos < candidates_pos < delta_pos


# ---------------------------------------------------------------------------
# PRD-073 — R6: Section labels
# ---------------------------------------------------------------------------

def test_run_delta_section_label_changes_since_last_run() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run())
    delta = html.split('id="run-delta"', 1)[1]
    assert "Changes Since Last Run" in delta


def test_run_delta_section_label_old_delta_absent() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run())
    delta = html.split('id="run-delta"', 1)[1]
    assert "<h2>Delta</h2>" not in delta


# ---------------------------------------------------------------------------
# PRD-073 — R8: Empty candidate state
# ---------------------------------------------------------------------------

def test_empty_candidates_message() -> None:
    mm = _market_map({})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "NO_CANDIDATES" in html


def test_empty_candidates_no_error() -> None:
    mm = _market_map({})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="candidate-board"' in html
