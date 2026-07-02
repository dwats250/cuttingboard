"""Tests for PRD-074 — Level diagram."""

from __future__ import annotations

import copy
import re

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
    assert ">VWAP 499.50" in html  # may carry a % suffix (PRD-221)


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
    assert ">NOW 75.00" in diagram  # PRD-222: anchor labelled NOW
    assert ">PRIOR_LOW 74.95" in diagram
    assert ">VWAP 75.05" in diagram
    assert ">0.618 74.62" in diagram


def test_prd222_now_anchor_and_pct_distance() -> None:
    # PRD-222: the anchor IS current price -> labelled NOW (0% reference, no
    # suffix); every other level carries its signed % distance from it. The
    # redundant separate NOW marker and the always-empty band were removed.
    fib = {"retracements": {"0.618": 99.40}}
    zones = [{"type": "PRIOR_LOW", "level": 99.00}]
    mm = _mm_with_levels("GDX", grade="A+", fib_levels=fib, watch_zones=zones)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm, contract_entry_map={"GDX": 100.00},
    )
    diagram = html.split('class="lvl-diagram"', 1)[1].split("</svg>", 1)[0]
    assert ">NOW 100.00</text>" in diagram          # anchor labelled NOW
    assert ">PRIOR_LOW 99.00 -1.0%</text>" in diagram  # % distance from NOW
    assert 'stroke="#ffffff"' not in diagram         # no separate white NOW marker
    assert 'opacity="0.06"' not in diagram           # no band


# ---------------------------------------------------------------------------
# PRD-223 — Numeric entry→stop risk band (from contract trade_candidates)
# ---------------------------------------------------------------------------

_BAND_RECT = re.compile(
    r'<rect x="0" y="(?P<y>\d+)" width="160" height="(?P<h>\d+)" '
    r'fill="#e05252" opacity="0.08"/>'
)
_STOP_LINE = re.compile(
    r'<line x1="0" y1="(?P<y>\d+)" x2="160" y2="\d+" '
    r'stroke="#e05252" stroke-width="1.5" stroke-dasharray="5,3"/>'
)
_ANCHOR_LINE = re.compile(
    r'<line x1="0" y1="(?P<y>\d+)" x2="160" y2="\d+" stroke="#f5c518"'
)


def _diagram(html: str) -> str:
    return html.split('class="lvl-diagram"', 1)[1].split("</svg>", 1)[0]


def _assert_no_band(html_or_diagram: str) -> None:
    assert 'opacity="0.08"' not in html_or_diagram
    assert 'stroke="#e05252"' not in html_or_diagram
    assert ">STOP " not in html_or_diagram


def test_prd223_risk_band_renders_between_entry_and_stop() -> None:
    # Contract entry 510 (the anchor) / stop 505: a soft risk zone spans
    # exactly the mapped anchor→stop y-range, behind the level lines, with a
    # dashed STOP edge labelled with price and % distance.
    wz = [{"type": "PRIOR_LOW", "level": 508.0}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 510.0},
        contract_stop_map={"SPY": 505.0},
    )
    diagram = _diagram(html)
    rect = _BAND_RECT.search(diagram)
    stop_line = _STOP_LINE.search(diagram)
    anchor_line = _ANCHOR_LINE.search(diagram)
    assert rect is not None, "risk-zone rect missing"
    assert stop_line is not None, "dashed STOP edge missing"
    assert anchor_line is not None, "anchor line missing"
    y_anchor = int(anchor_line.group("y"))
    y_stop = int(stop_line.group("y"))
    assert int(rect.group("y")) == min(y_anchor, y_stop)
    assert int(rect.group("h")) == abs(y_anchor - y_stop)
    # The rect renders BEFORE (behind) every level line.
    assert diagram.index(rect.group(0)) < diagram.index("<line")
    assert ">STOP 505.00 -1.0%</text>" in diagram
    assert ">NOW 510.00</text>" in diagram


def test_prd223_stop_joins_the_y_scale() -> None:
    # A stop below every other level widens the scale instead of mapping
    # off-canvas: the stop edge and all labels stay within 0..110.
    wz = [{"type": "PRIOR_LOW", "level": 509.0}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 510.0},
        contract_stop_map={"SPY": 495.0},
    )
    diagram = _diagram(html)
    stop_line = _STOP_LINE.search(diagram)
    assert stop_line is not None
    assert 0 <= int(stop_line.group("y")) <= 110
    ys = [int(m) for m in re.findall(r'<text x="\d+" y="(-?\d+)"', diagram)]
    assert ys and all(0 <= y <= 110 for y in ys)


def test_prd223_no_band_when_stop_absent() -> None:
    wz = [{"type": "PRIOR_LOW", "level": 508.0}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 510.0},
    )
    _assert_no_band(_diagram(html))


def test_prd223_no_band_when_stop_equals_entry() -> None:
    wz = [{"type": "PRIOR_LOW", "level": 508.0}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 510.0},
        contract_stop_map={"SPY": 510.0},
    )
    _assert_no_band(_diagram(html))


def test_prd223_no_band_on_invalid_stop_values() -> None:
    # Non-finite, non-positive, and non-coercible stops must not draw —
    # deleting any input guard makes one of these variants render a band.
    wz = [{"type": "PRIOR_LOW", "level": 508.0}]
    for bad_stop in (float("nan"), float("inf"), 0.0, -5.0, "not-a-price", True):
        mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
        html = render_dashboard_html(
            _payload(), _run(), market_map=mm,
            contract_entry_map={"SPY": 510.0},
            contract_stop_map={"SPY": bad_stop},
        )
        _assert_no_band(_diagram(html))


def test_prd223_no_band_without_contract_entry() -> None:
    # A stop never draws against the current_price fallback anchor — the risk
    # zone is the contract's entry→stop pair, not current-price→stop.
    s = _mm_symbol("SPY", grade="A+")
    s["current_price"] = 510.0
    s["watch_zones"] = [{"type": "PRIOR_LOW", "level": 508.0}]
    mm = _market_map({"SPY": s})
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_stop_map={"SPY": 505.0},
    )
    _assert_no_band(_diagram(html))
