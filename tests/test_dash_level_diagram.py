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
    wz = [{"type": "SUPPORT", "level": 495.0}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert 'class="lvl-diagram"' in html
    assert "ENTRY" in html


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
    # PRD-216: the VWAP label now carries its dollar level.
    assert ">VWAP 499.50</text>" in html


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


def test_level_diagram_many_clustered_labels_stay_on_canvas() -> None:
    # Regression: with more level labels than fit at the nominal 11px gap in the
    # 110px canvas, the declutter pass must shrink the gap so every label stays
    # on-canvas (0 <= y <= SVG_H), never spilling to negative y off the top.
    import re
    fib = {"retracements": {"0.382": 100.47, "0.5": 100.69, "0.618": 100.91}}
    zones = [
        {"level": 100.11, "type": "PRIOR_HIGH"}, {"level": 100.16, "type": "ORB_HIGH"},
        {"level": 100.19, "type": "ORB_LOW"}, {"level": 100.99, "type": "PRIOR_LOW"},
        {"level": 100.51, "type": "EMA9"}, {"level": 100.54, "type": "EMA21"},
        {"level": 100.43, "type": "EMA50"}, {"level": 100.21, "type": "VWAP"},
    ]
    s = _mm_symbol("SPY", grade="A+")
    s["current_price"] = 100.28
    s["fib_levels"] = fib
    s["watch_zones"] = zones
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map({"SPY": s}))
    diagram = html.split('class="lvl-diagram"', 1)[1].split("</svg>", 1)[0]
    ys = [int(m) for m in re.findall(r'<text x="\d+" y="(-?\d+)"', diagram)]
    assert ys, "no level labels rendered"
    assert all(0 <= y <= 110 for y in ys), f"label off-canvas: {sorted(ys)}"


def test_prd216_level_labels_carry_dollar_values() -> None:
    # PRD-216: every level label prints its dollar value.
    fib = {"retracements": {"0.618": 74.62}}
    zones = [{"type": "PRIOR_LOW", "level": 74.95}, {"type": "VWAP", "level": 75.05}]
    mm = _mm_with_levels("GDX", grade="A+", fib_levels=fib, watch_zones=zones)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm, contract_entry_map={"GDX": 75.00},
    )
    diagram = html.split('class="lvl-diagram"', 1)[1].split("</svg>", 1)[0]
    assert ">ENTRY 75.00</text>" in diagram
    assert ">PRIOR_LOW 74.95</text>" in diagram
    assert ">VWAP 75.05</text>" in diagram
    assert ">0.618 74.62</text>" in diagram
