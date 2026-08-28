"""Tests for the candidate level surface.

PRD-074 introduced the level diagram; PRD-321 (owner ruling Q3) REPLACED that
full-size SVG ladder with the compact tiered ladder — the setup chart's
subordinate exact-level reference and the honest no-bars fallback. Every
semantic the old diagram carried (PRD-216 dollar values, PRD-221/222 signed
%-distance from NOW, PRD-223 entry->stop risk span, PRD-226 NOW-anchor
suppression, PRD-304 lock neutralization) is asserted here against the new
markup, in the fallback role: these renders pass no bars.
"""

from __future__ import annotations

import copy
import re

from cuttingboard.delivery.dashboard_renderer import _CSS, render_dashboard_html

from tests.dash_helpers import _market_map, _mm_symbol, _payload, _run


# ---------------------------------------------------------------------------
# helpers (local)
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


_ROW = re.compile(
    r'<div class="lvl-row (?P<cls>[^"]+)">'
    r'<span class="lvl-name">(?P<name>[^<]*)</span>'
    r'<span class="lvl-px">(?P<px>[^<]*)</span>'
    r'<span class="lvl-pct">(?P<pct>[^<]*)</span></div>'
)


def _ladder(html: str) -> str:
    """The first compact ladder block (opening tag through its close)."""
    assert 'class="lvl-ladder' in html, "no compact ladder rendered"
    return '<div class="lvl-ladder' + html.split('class="lvl-ladder', 1)[1].split(
        "\n  </div>", 1
    )[0]


def _rows(fragment: str) -> list[tuple[str, str, str, str]]:
    """(name, price, pct, css classes) for every ladder row, in DOM order."""
    return [(m["name"], m["px"], m["pct"], m["cls"]) for m in _ROW.finditer(fragment)]


def _row(fragment: str, name: str) -> tuple[str, str, str, str]:
    hits = [r for r in _rows(fragment) if r[0] == name]
    assert len(hits) == 1, f"expected exactly one {name} row, got {hits}"
    return hits[0]


def _names(fragment: str) -> list[str]:
    return [r[0] for r in _rows(fragment)]


def _assert_no_band(fragment: str) -> None:
    assert "lvl-riskband" not in fragment
    assert "lvl-inrisk" not in fragment
    assert "lvl-lockrisk" not in fragment
    assert "STOP" not in fragment
    assert "INVALIDATION" not in fragment


# ---------------------------------------------------------------------------
# Compact ladder — presence, content, determinism
# ---------------------------------------------------------------------------

def test_ladder_renders_with_entry_when_contract_entry_provided() -> None:
    wz = [{"type": "SUPPORT", "level": 495.0}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert 'class="lvl-ladder' in html
    assert "ENTRY" in _names(_ladder(html))


def test_no_ladder_when_no_candidates() -> None:
    mm = _market_map({})
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert 'class="lvl-ladder' not in html
    assert 'class="lvl-unavail"' not in html
    assert 'class="setup-chart"' not in html


def test_vwap_row_carries_the_tier2_vwap_accent() -> None:
    wz = [{"type": "VWAP", "level": 499.5, "context": "session vwap"}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    name, px, _pct, cls = _row(_ladder(html), "VWAP")
    assert px == "499.50"          # PRD-216: the dollar value
    assert "lvl-t2" in cls         # Tier 2 (structural), never Tier 1
    assert "lvl-vwap" in cls


def test_no_vwap_row_when_no_vwap_zone() -> None:
    wz = [{"type": "ORB_HIGH", "level": 502.0, "context": "opening range high"}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    ladder = _ladder(html)
    assert "VWAP" not in _names(ladder)
    assert "lvl-vwap" not in ladder


def test_fib_rows_rendered_at_tier_three() -> None:
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
    ladder = _ladder(html)
    for label in ("0.618", "0.5", "0.382"):
        assert "lvl-t3" in _row(ladder, label)[3]


def test_no_fib_rows_when_fib_levels_null() -> None:
    wz = [{"type": "PRIOR_LOW", "level": 99.0}]
    mm = _mm_with_levels("SPY", grade="A+", fib_levels=None, watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert "0.618" not in _names(_ladder(html))


def test_no_ladder_without_level_context() -> None:
    # No fib levels and no watch zones => no level context => nothing drawn.
    # (The old assertion `"lvl-diagram" in html` only ever matched the CSS rule.)
    mm = _mm_with_levels("SPY", grade="A+", fib_levels=None, watch_zones=[])
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 500.0},
    )
    assert 'class="lvl-ladder' not in html
    assert 'class="setup-chart"' not in html


def test_ladder_deterministic() -> None:
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


def test_ladder_no_decision_field_changes() -> None:
    p = _payload()
    r = _run()
    mm = _mm_with_levels("SPY", grade="A+")
    p_before = copy.deepcopy(p)
    r_before = copy.deepcopy(r)
    render_dashboard_html(p, r, market_map=mm, contract_entry_map={"SPY": 500.0})
    assert p == p_before
    assert r == r_before


def test_ladder_rows_are_strictly_price_ordered_top_down() -> None:
    # The compact ladder replaces the old canvas + label-declutter pass: every
    # level gets its own row, ordered high price -> low price. Densely clustered
    # levels can no longer overprint or spill off a canvas.
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
    rows = _rows(_ladder(html))
    assert len(rows) == 12  # NOW + 8 zones + 3 fibs
    prices = [float(r[1].replace(",", "")) for r in rows]
    assert prices == sorted(prices, reverse=True), prices


def test_prd216_rows_carry_dollar_values() -> None:
    fib = {"retracements": {"0.618": 74.62}}
    zones = [{"type": "PRIOR_LOW", "level": 74.95}, {"type": "VWAP", "level": 75.05}]
    mm = _mm_with_levels("GDX", grade="A+", fib_levels=fib, watch_zones=zones)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm, contract_entry_map={"GDX": 75.00},
    )
    ladder = _ladder(html)
    # PRD-226: NOW is the live current price (_mm_symbol default 100.00), not the
    # contract entry (75.00) — the entry gets its own ENTRY row.
    assert _row(ladder, "NOW")[1] == "100.00"
    assert _row(ladder, "ENTRY")[1] == "75.00"
    assert _row(ladder, "PRIOR_LOW")[1] == "74.95"
    assert _row(ladder, "VWAP")[1] == "75.05"
    assert _row(ladder, "0.618")[1] == "74.62"


def test_prd222_now_anchor_and_pct_distance() -> None:
    fib = {"retracements": {"0.618": 99.40}}
    zones = [{"type": "PRIOR_LOW", "level": 99.00}]
    mm = _mm_with_levels("GDX", grade="A+", fib_levels=fib, watch_zones=zones)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm, contract_entry_map={"GDX": 100.00},
    )
    ladder = _ladder(html)
    assert _row(ladder, "NOW")[1:3] == ("100.00", "")       # the 0% reference
    assert _row(ladder, "PRIOR_LOW")[1:3] == ("99.00", "-1.0%")
    assert _row(ladder, "0.618")[2] == "-0.6%"


# ---------------------------------------------------------------------------
# PRD-321 R4 — the pre-PRD-321 full-size ladder is gone everywhere
# ---------------------------------------------------------------------------

def test_prd321_old_full_size_ladder_markup_renders_nowhere() -> None:
    # Ruling Q3: the redesigned ladder REPLACES the old presentation. No render
    # may contain the retired diagram wrapper or its pinned 160/110 geometry.
    fib = {"retracements": {"0.618": 99.40}}
    zones = [{"type": "PRIOR_LOW", "level": 99.00}, {"type": "VWAP", "level": 100.5}]
    mm = _mm_with_levels("SPY", grade="A+", fib_levels=fib, watch_zones=zones)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 101.0}, contract_stop_map={"SPY": 98.0},
    )
    assert "lvl-diagram" not in html
    assert 'width="160"' not in html
    assert 'x2="160"' not in html
    assert 'stroke="#1a4a5a"' not in html
    # and with no bars there is no chart either — the ladder is the whole surface
    assert 'class="setup-chart"' not in html
    assert 'class="lvl-ladder' in html


def test_prd321_tier3_is_never_rendered_at_tier1_weight() -> None:
    # Styling assertion (R4 FAIL line). Mutation: emit "lvl-t1" for EMA50/fibs,
    # or give .lvl-t3 Tier-1 weight/opacity in _CSS -> this test goes red.
    fib = {"retracements": {"0.618": 99.40}}
    zones = [
        {"type": "EMA50", "level": 97.0},
        {"type": "EMA9", "level": 100.2},
    ]
    mm = _mm_with_levels("SPY", grade="A+", fib_levels=fib, watch_zones=zones)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm, contract_entry_map={"SPY": 101.0},
    )
    ladder = _ladder(html)
    for tier3_name in ("EMA50", "0.618"):
        cls = _row(ladder, tier3_name)[3]
        assert "lvl-t3" in cls and "lvl-t1" not in cls and "lvl-t2" not in cls
    assert "lvl-t2" in _row(ladder, "EMA9")[3]
    assert "lvl-t1" in _row(ladder, "NOW")[3]

    # The tier classes must actually SUBDUE, not merely differ in name.
    def _rule(selector: str) -> str:
        return _CSS.split(selector + "{", 1)[1].split("}", 1)[0]

    t1, t2, t3 = _rule(".lvl-t1"), _rule(".lvl-t2"), _rule(".lvl-t3")
    opacity = {
        name: float(rule.split("opacity:", 1)[1].split(";", 1)[0])
        for name, rule in (("t1", t1), ("t2", t2), ("t3", t3))
    }
    assert opacity["t1"] > opacity["t2"] > opacity["t3"]
    assert "font-weight:700" in t1
    assert "font-weight:700" not in t3


# ---------------------------------------------------------------------------
# PRD-223 — the contract entry->stop risk span, carried into the ladder
# ---------------------------------------------------------------------------

def test_prd223_risk_band_spans_entry_to_stop() -> None:
    # current price 508 (NOW anchor) / contract entry 510 / stop 505: the risk
    # span is the ENTRY(510)->STOP(505) row group, NOT NOW->STOP, and every
    # %-distance is measured from NOW.
    s = _mm_symbol("SPY", grade="A+")
    s["current_price"] = 508.0
    s["watch_zones"] = [{"type": "PRIOR_LOW", "level": 506.0}, {"type": "EMA9", "level": 502.0}]
    mm = _market_map({"SPY": s})
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 510.0},
        contract_stop_map={"SPY": 505.0},
    )
    ladder = _ladder(html)
    assert 'class="lvl-riskband lvl-inrisk"' in ladder
    band = ladder.split('class="lvl-riskband lvl-inrisk">', 1)[1].split("\n    </div>", 1)[0]
    # ENTRY, NOW and the 506 level sit inside the span; the 502 EMA9 sits below it.
    assert _names(band) == ["ENTRY", "NOW", "PRIOR_LOW", "STOP"]
    assert "EMA9" not in band
    assert "lvl-t1" in _row(band, "STOP")[3] and "lvl-stop" in _row(band, "STOP")[3]
    # %-distances measured from NOW=508: entry +0.4%, stop -0.6%.
    assert _row(ladder, "NOW")[1:3] == ("508.00", "")
    assert _row(ladder, "ENTRY")[1:3] == ("510.00", "+0.4%")
    assert _row(ladder, "STOP")[1:3] == ("505.00", "-0.6%")


def test_prd223_no_band_when_stop_absent() -> None:
    wz = [{"type": "PRIOR_LOW", "level": 508.0}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 510.0},
    )
    _assert_no_band(_ladder(html))


def test_prd223_no_band_when_stop_equals_entry() -> None:
    wz = [{"type": "PRIOR_LOW", "level": 508.0}]
    mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 510.0},
        contract_stop_map={"SPY": 510.0},
    )
    _assert_no_band(_ladder(html))


def test_prd223_no_band_on_invalid_stop_values() -> None:
    # Non-finite, non-positive, and non-coercible stops must not draw —
    # deleting any input guard makes one of these variants render a span.
    wz = [{"type": "PRIOR_LOW", "level": 508.0}]
    for bad_stop in (float("nan"), float("inf"), 0.0, -5.0, "not-a-price", True):
        mm = _mm_with_levels("SPY", grade="A+", watch_zones=wz)
        html = render_dashboard_html(
            _payload(), _run(), market_map=mm,
            contract_entry_map={"SPY": 510.0},
            contract_stop_map={"SPY": bad_stop},
        )
        _assert_no_band(_ladder(html))


def test_prd223_no_band_without_contract_entry() -> None:
    # A stop never draws against the current_price fallback anchor — the risk
    # span is the contract's entry->stop pair, not current-price->stop.
    s = _mm_symbol("SPY", grade="A+")
    s["current_price"] = 510.0
    s["watch_zones"] = [{"type": "PRIOR_LOW", "level": 508.0}]
    mm = _market_map({"SPY": s})
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_stop_map={"SPY": 505.0},
    )
    _assert_no_band(_ladder(html))


# ---------------------------------------------------------------------------
# PRD-226 — NOW anchor = current price; contract entry is a separate level
# ---------------------------------------------------------------------------

def test_prd226_now_anchor_is_current_price_not_contract_entry() -> None:
    s = _mm_symbol("SPY", grade="A+")
    s["current_price"] = 120.0
    s["watch_zones"] = [{"type": "SUPPORT", "level": 108.0}]
    mm = _market_map({"SPY": s})
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 110.0},
    )
    ladder = _ladder(html)
    assert _row(ladder, "NOW")[1] == "120.00"            # NOW is current price
    assert _row(ladder, "ENTRY")[1:3] == ("110.00", "-8.3%")
    # An unrecognised zone type keeps its structural (Tier 2) weight — the
    # exact-level reference never silently drops a fact.
    assert _row(ladder, "SUPPORT")[1:3] == ("108.00", "-10.0%")
    assert "lvl-t2" in _row(ladder, "SUPPORT")[3]


def test_prd226_no_entry_row_when_entry_equals_now() -> None:
    s = _mm_symbol("SPY", grade="A+")
    s["current_price"] = 100.0
    s["watch_zones"] = [{"type": "SUPPORT", "level": 99.0}]
    mm = _market_map({"SPY": s})
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 100.0},
    )
    ladder = _ladder(html)
    assert _row(ladder, "NOW")[1] == "100.00"
    assert "ENTRY" not in _names(ladder)
    assert "lvl-entry" not in ladder


def test_prd226_no_ladder_and_no_now_when_current_price_invalid() -> None:
    s = _mm_symbol("SPY", grade="A+")
    s["current_price"] = 0
    s["watch_zones"] = [{"type": "SUPPORT", "level": 108.0}]
    mm = _market_map({"SPY": s})
    html = render_dashboard_html(
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": 110.0},
    )
    assert 'class="lvl-ladder' not in html   # no ladder without a valid NOW
    assert 'class="setup-chart"' not in html  # and no chart (PRD-321 R3)
    assert ">110.00<" not in html             # entry never promoted to an anchor


def test_prd226_non_finite_current_price_suppresses_surface_not_render() -> None:
    for bad_price in (float("inf"), float("-inf"), float("nan")):
        s = _mm_symbol("SPY", grade="A+")
        s["current_price"] = bad_price
        s["watch_zones"] = [{"type": "SUPPORT", "level": 108.0}]
        mm = _market_map({"SPY": s})
        html = render_dashboard_html(   # must not raise
            _payload(), _run(), market_map=mm,
            contract_entry_map={"SPY": 110.0},
        )
        assert 'class="lvl-ladder' not in html
        assert 'class="setup-chart"' not in html


def test_prd226_non_finite_contract_entry_drops_entry_row_and_band() -> None:
    s = _mm_symbol("SPY", grade="A+")
    s["current_price"] = 120.0
    s["watch_zones"] = [{"type": "SUPPORT", "level": 108.0}]
    mm = _market_map({"SPY": s})
    html = render_dashboard_html(   # must not raise
        _payload(), _run(), market_map=mm,
        contract_entry_map={"SPY": float("inf")},
        contract_stop_map={"SPY": 105.0},
    )
    ladder = _ladder(html)
    assert _row(ladder, "NOW")[1] == "120.00"
    assert "ENTRY" not in _names(ladder)
    _assert_no_band(ladder)


# ---------------------------------------------------------------------------
# PRD-304 — operator lock neutralization, in the ladder's FALLBACK role
# (PRD-321 R3: all four preservation semantics bind the ladder in BOTH roles)
# ---------------------------------------------------------------------------

_LOCK_PERMISSION = "No new trades permitted — operator cannot monitor."


def _locked_run() -> dict:
    return _run(permission=_LOCK_PERMISSION)


def test_prd304_locked_fallback_ladder_neutralizes_wording_and_colour() -> None:
    # Mutation: drop the `operator_locked` branch in _render_level_ladder ->
    # ENTRY/STOP and the action accent classes reappear and this goes red.
    s = _mm_symbol("SPY", grade="A+")
    s["current_price"] = 508.0
    s["watch_zones"] = [{"type": "PRIOR_LOW", "level": 506.0}]
    mm = _market_map({"SPY": s})
    html = render_dashboard_html(
        _payload(), _locked_run(), market_map=mm,
        contract_entry_map={"SPY": 510.0},
        contract_stop_map={"SPY": 505.0},
    )
    ladder = _ladder(html)
    names = _names(ladder)
    assert "LEVEL" in names and "INVALIDATION" in names
    assert "ENTRY" not in names and "STOP" not in names
    assert "lvl-locked" in ladder
    assert "lvl-entry" not in ladder and "lvl-stop" not in ladder
    assert "lvl-neutral" in ladder
    # PRD-223 content survives the neutralization — the span is still marked,
    # in the neutral (non-action) colour class.
    assert 'class="lvl-riskband lvl-lockrisk"' in ladder
    assert "lvl-inrisk" not in ladder
    # PRD-221/222 facts survive the lock.
    assert _row(ladder, "LEVEL")[1:3] == ("510.00", "+0.4%")
    assert _row(ladder, "INVALIDATION")[1:3] == ("505.00", "-0.6%")
    assert _row(ladder, "PRIOR_LOW")[2] == "-0.4%"
