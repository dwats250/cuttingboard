"""Tests for PRD-074 — Level diagram."""

from __future__ import annotations

import copy

from cuttingboard.delivery.dashboard_renderer import render_dashboard_html

from tests.dash_helpers import _market_map, _mm_symbol, _payload, _run


# ---------------------------------------------------------------------------
# PRD-074 — Level diagram helpers (local)
# ---------------------------------------------------------------------------

def _mm_with_levels(
    sym: str = "SPY",
    grade: str = "A+",
    fib_levels: dict | None = None,
    watch_zones: list | None = None,
) -> dict:
    s = _mm_symbol(sym, grade=grade)
    s["fib_levels"] = fib_levels
    s["watch_zones"] = watch_zones if watch_zones is not None else []
    return _market_map({sym: s})


# ---------------------------------------------------------------------------
# PRD-074 — Level diagram tests
# ---------------------------------------------------------------------------

def test_level_diagram_entry_line_present_when_entry_provided() -> None:
    mm = _mm_with_levels("SPY", grade="A+")
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert 'class="lvl-diagram"' in html
    assert "ENTRY" in html


def test_level_diagram_unavailable_when_no_entry() -> None:
    mm = _mm_with_levels("SPY", grade="A+")
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={},
    )
    assert "lvl-unavail" in html
    assert "Chart unavailable" in html


def test_level_diagram_no_diagram_when_no_candidates() -> None:
    mm = _market_map({})
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert 'class="lvl-diagram"' not in html
    assert 'class="lvl-unavail"' not in html


def test_level_diagram_vwap_rendered_when_present() -> None:
    wz = [{"type": "VWAP", "level": 499.5, "context": "session vwap"}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert 'stroke-dasharray="4,2"' in html
    assert ">VWAP</text>" in html


def test_level_diagram_vwap_absent_when_no_vwap_zone() -> None:
    wz = [{"type": "ORB_HIGH", "level": 502.0, "context": "opening range high"}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert 'stroke-dasharray="4,2"' not in html
    assert ">VWAP</text>" not in html


def test_level_diagram_fib_levels_rendered() -> None:
    fibs = {
        "source": "last_50_bars",
        "swing_high": 510.0,
        "swing_low": 490.0,
        "retracements": {"0.618": 497.6, "0.5": 500.0, "0.382": 502.4},
    }
    mm = _mm_with_levels("SPY", grade="A+", fib_levels=fibs)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert "0.618" in html
    assert "0.5" in html
    assert "0.382" in html


def test_level_diagram_no_fib_markers_when_fib_levels_null() -> None:
    mm = _mm_with_levels("SPY", grade="A+", fib_levels=None)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert "0.618" not in html
    assert 'stroke="#3a3a3a"' not in html


def test_level_diagram_no_zone_markers_when_watch_zones_empty() -> None:
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=[])
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert 'stroke="#1a4a5a"' not in html


def test_level_diagram_deterministic() -> None:
    wz = [{"type": "VWAP", "level": 499.5, "context": "session vwap"}]
    fibs = {
        "source": "x", "swing_high": 510.0, "swing_low": 490.0,
        "retracements": {"0.618": 497.6, "0.5": 500.0},
    }
    mm = _mm_with_levels("SPY", grade="A+", fib_levels=fibs, watch_zones=wz)
    h1 = render_dashboard_html(
        _payload(), _run(), market_map=mm, contract_entry_map={"SPY": 500.0},
    )
    h2 = render_dashboard_html(
        _payload(), _run(), market_map=mm, contract_entry_map={"SPY": 500.0},
    )
    assert h1 == h2


def test_level_diagram_no_error_on_missing_fields() -> None:
    mm = _mm_with_levels("SPY", grade="A+", fib_levels=None, watch_zones=None)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert "lvl-diagram" in html


def test_level_diagram_no_decision_field_changes() -> None:
    p = _payload()
    r = _run()
    mm = _mm_with_levels("SPY", grade="A+")
    p_before = copy.deepcopy(p)
    r_before = copy.deepcopy(r)
    render_dashboard_html(p, r, market_map=mm, contract_entry_map={"SPY": 500.0})
    assert p == p_before
    assert r == r_before
