"""PRD-321 R1/R6 — the pure setup-chart module.

`cuttingboard.delivery.setup_chart` renders daily candles plus a FIXED, CLOSED
tier map into a deterministic SVG string. It performs no I/O, reads no clock,
computes no level values, and never widens its price domain for Tier-3 context.
Every guard here ships a mutation-verified red test (see the per-test mutation
notes).
"""

from __future__ import annotations

import ast
import hashlib as _hashlib
import json as _json
import re
from pathlib import Path

import pytest

from cuttingboard.delivery import setup_chart
from cuttingboard.delivery.setup_chart import render_setup_chart_svg

REPO_ROOT = Path(__file__).resolve().parent.parent

# 12 completed daily sessions; values are the ONLY OHLC source in this module.
BARS: list[list] = [
    ["2026-08-10", 100.0, 102.0, 99.5, 101.5, 1_000],
    ["2026-08-11", 101.5, 103.0, 101.0, 102.8, 1_100],
    ["2026-08-12", 102.8, 103.5, 101.2, 101.4, 1_200],
    ["2026-08-13", 101.4, 102.2, 100.1, 100.4, 1_300],
    ["2026-08-14", 100.4, 101.0, 98.8, 99.2, 1_400],
    ["2026-08-17", 99.2, 100.6, 98.2, 100.3, 1_500],
    ["2026-08-18", 100.3, 104.0, 100.0, 103.7, 1_600],
    ["2026-08-19", 103.7, 104.5, 102.9, 103.1, 1_700],
    ["2026-08-20", 103.1, 103.4, 101.8, 102.0, 1_800],
    ["2026-08-21", 102.0, 102.6, 100.9, 101.1, 1_900],
    ["2026-08-24", 101.1, 102.4, 100.7, 102.2, 2_000],
    ["2026-08-25", 102.2, 103.9, 102.0, 103.4, 2_100],
]

ZONES = [
    {"type": "VWAP", "level": 102.5},
    {"type": "EMA9", "level": 102.0},
    {"type": "EMA21", "level": 101.2},
    {"type": "PRIOR_HIGH", "level": 103.9},
    {"type": "EMA50", "level": 100.6},
]
FIBS = {"retracements": {"0.382": 102.7, "0.5": 101.9, "0.618": 101.1}}

_WICK = re.compile(
    r'<line class="candle-wick" x1="(?P<cx>[\d.]+)" y1="(?P<y1>[\d.]+)" '
    r'x2="[\d.]+" y2="(?P<y2>[\d.]+)" stroke="(?P<colour>#[0-9a-f]{6})"'
)
_BODY = re.compile(r'<rect class="candle-body" [^/]*?fill="(?P<colour>#[0-9a-f]{6})"/>')
_TEXT = re.compile(r"<text[^>]*>(?P<text>[^<]*)</text>")
_LINE_CLASS = re.compile(
    r'<line class="(?P<cls>[^"]+)"[^/]*?stroke-width="(?P<sw>[\d.]+)"'
)


def _chart(**overrides) -> str:
    kwargs = dict(
        contract_entry=103.0,
        contract_stop=100.5,
        watch_zones=ZONES,
        fib_levels=FIBS,
    )
    kwargs.update(overrides)
    bars = kwargs.pop("bars", BARS)
    now_price = kwargs.pop("now_price", 102.4)
    return render_setup_chart_svg(bars, now_price, **kwargs)


# ---------------------------------------------------------------------------
# R1 — determinism
# ---------------------------------------------------------------------------

def test_two_identical_calls_are_byte_identical() -> None:
    # Mutation: seed any ordering with a set/dict iteration or a time value ->
    # the two renders diverge.
    assert _chart() == _chart()


def test_determinism_holds_across_reordered_equivalent_fib_input() -> None:
    # Fib retracements are emitted in a sorted order, so an input dict written
    # in a different key order renders the same bytes.
    reordered = {"retracements": {"0.618": 101.1, "0.382": 102.7, "0.5": 101.9}}
    assert _chart(fib_levels=reordered) == _chart()


# ---------------------------------------------------------------------------
# R1 — Tier 3 is context: it never widens the price domain
# ---------------------------------------------------------------------------

def test_distant_tier3_ema50_does_not_change_the_bar_region_scale() -> None:
    # R1 FAIL line. Mutation: append tier-3 levels to `domain` in
    # render_setup_chart_svg -> the candle geometry shifts and this goes red.
    baseline = _chart()
    far = [z for z in ZONES if z["type"] != "EMA50"] + [{"type": "EMA50", "level": 12.0}]
    widened = _chart(watch_zones=far)
    assert _WICK.findall(baseline) == _WICK.findall(widened)
    assert _BODY.findall(baseline) == _BODY.findall(widened)


def test_distant_tier3_fibs_do_not_change_the_bar_region_scale() -> None:
    baseline = _chart()
    far = {"retracements": {"0.382": 9.0, "0.5": 8.0, "0.618": 7.0}}
    assert _WICK.findall(_chart(fib_levels=far)) == _WICK.findall(baseline)


def test_tier3_outside_the_domain_is_not_drawn_at_all() -> None:
    far = [z for z in ZONES if z["type"] != "EMA50"] + [{"type": "EMA50", "level": 12.0}]
    svg = _chart(watch_zones=far)
    assert "EMA50" not in svg
    assert "12.0" not in svg


def test_tier2_levels_do_widen_the_domain() -> None:
    # Non-vacuity anchor for the Tier-3 test above: Tier 2 IS part of the scale,
    # so a distant Tier-2 level must change the candle geometry.
    stretched = ZONES + [{"type": "PRIOR_LOW", "level": 90.0}]
    assert _WICK.findall(_chart(watch_zones=stretched)) != _WICK.findall(_chart())


# ---------------------------------------------------------------------------
# R1/R2 — source-bar fidelity: candles come from the input, nothing else
# ---------------------------------------------------------------------------

def test_one_candle_per_input_bar_with_input_derived_direction() -> None:
    svg = _chart()
    wicks = _WICK.findall(svg)
    bodies = _BODY.findall(svg)
    assert len(wicks) == len(BARS) == len(bodies)
    expected = ["#4caf50" if bar[4] >= bar[1] else "#f44336" for bar in BARS]
    assert bodies == expected


def test_wick_extents_track_the_input_highs_and_lows_monotonically() -> None:
    # y grows downward, so a higher input high must map to a smaller y.
    svg = _chart()
    tops = [float(m[1]) for m in _WICK.findall(svg)]
    bottoms = [float(m[2]) for m in _WICK.findall(svg)]
    highs = [bar[2] for bar in BARS]
    lows = [bar[3] for bar in BARS]
    assert [i for i, _ in sorted(enumerate(tops), key=lambda kv: kv[1])] == \
           [i for i, _ in sorted(enumerate(highs), key=lambda kv: -kv[1])]
    assert [i for i, _ in sorted(enumerate(bottoms), key=lambda kv: -kv[1])] == \
           [i for i, _ in sorted(enumerate(lows), key=lambda kv: kv[1])]
    assert highs.index(max(highs)) == tops.index(min(tops))
    assert lows.index(min(lows)) == bottoms.index(max(bottoms))


def test_perturbing_one_input_bar_moves_only_that_candle() -> None:
    # Mutation-style: proves the candles are read from the bars, not synthesized.
    bumped = [list(b) for b in BARS]
    bumped[3][2] = 102.21  # nudge one high, inside the existing domain
    before = _WICK.findall(_chart())
    after = _WICK.findall(_chart(bars=bumped))
    differing = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert differing == [3]


def test_every_rendered_price_traces_to_an_input_value() -> None:
    # R1 FAIL line: no rendered price may be computed inside the module.
    svg = _chart()
    inputs = {102.4, 103.0, 100.5}
    inputs |= {z["level"] for z in ZONES}
    inputs |= {v for v in FIBS["retracements"].values()}
    for bar in BARS:
        inputs |= set(bar[1:5])
    allowed = {f"{v:,.2f}" for v in inputs} | {f"{v:,.1f}" for v in inputs}
    allowed |= set(FIBS["retracements"])  # the fib ratio labels are inputs too
    for text in _TEXT.findall(svg):
        # PRD-221/222 signed %-distances are facts derived from the NOW anchor,
        # not rendered prices; strip them before the trace check.
        prices_only = re.sub(r"[+-]\d+\.\d%", "", text)
        for token in re.findall(r"\d[\d,]*\.\d+", prices_only):
            assert token in allowed, f"{token!r} in {text!r} traces to no input"


def test_malformed_bar_rows_are_dropped_never_padded() -> None:
    # R2: OHLC is never synthesized. A short row, a non-numeric value and a
    # non-finite value are dropped; the remaining candles are unchanged.
    dirty = [BARS[0], ["2026-08-11", 1.0], BARS[1], ["x", 1, 2, "n/a", 4, 5],
             BARS[2], ["y", 1, float("inf"), 2, 3, 4]]
    svg = render_setup_chart_svg(dirty, 102.4)
    assert len(_WICK.findall(svg)) == 3


def test_bar_window_is_capped_at_the_most_recent_sessions() -> None:
    long_series = BARS * 5  # 60 rows
    svg = render_setup_chart_svg(long_series, 102.4)
    assert len(_WICK.findall(svg)) == setup_chart.MAX_BARS
    assert f">{setup_chart._day_label(long_series[-1][0])}<" in svg


def test_max_bars_none_renders_the_full_session() -> None:
    # PRD-324 (A1-C R8): max_bars=None disables the trailing cap so a full
    # current-session intraday series renders every candle (here 60 > MAX_BARS).
    long_series = BARS * 5  # 60 rows
    svg = render_setup_chart_svg(long_series, 102.4, max_bars=None)
    assert len(_WICK.findall(svg)) == len(long_series)


def test_max_bars_default_is_byte_identical_to_explicit_cap() -> None:
    # M16: the daily default must equal passing MAX_BARS explicitly; a changed
    # default (e.g. None) diverges here and at the :188 cap test above.
    long_series = BARS * 5
    assert (
        render_setup_chart_svg(long_series, 102.4)
        == render_setup_chart_svg(long_series, 102.4, max_bars=setup_chart.MAX_BARS)
    )


# ---------------------------------------------------------------------------
# R1 — nothing honest to draw => empty string (the caller falls back)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bars", [None, [], "not-bars", [["2026-08-10", 1, 2]]])
def test_no_usable_bars_returns_empty_string(bars) -> None:
    assert render_setup_chart_svg(bars, 102.4) == ""


@pytest.mark.parametrize(
    "price", [None, 0, -5.0, float("nan"), float("inf"), True, "n/a"]
)
def test_invalid_now_anchor_returns_empty_string(price) -> None:
    # PRD-226 carried into the chart: without a valid NOW anchor nothing draws.
    # Mutation: drop the `_fin` guard on now_price -> NaN/inf reach the y-scale
    # math and the render raises instead of returning "".
    assert render_setup_chart_svg(BARS, price) == ""


# ---------------------------------------------------------------------------
# R1/R6 — tier emphasis vs subdual
# ---------------------------------------------------------------------------

def test_tier_stroke_weights_descend_from_tier1_to_tier3() -> None:
    # R6 FAIL line (tier styling swapped). Mutation: give .lvl-t3 lines the
    # Tier-1 stroke width -> this goes red.
    svg = _chart()
    widths: dict[str, set[float]] = {}
    for cls, sw in _LINE_CLASS.findall(svg):
        for tier in ("lvl-t1", "lvl-t2", "lvl-t3"):
            if tier in cls:
                widths.setdefault(tier, set()).add(float(sw))
    assert widths["lvl-t3"] == {0.75}
    assert widths["lvl-t2"] == {1.0}
    assert min(widths["lvl-t1"]) >= 1.5
    assert min(widths["lvl-t1"]) > max(widths["lvl-t2"]) > max(widths["lvl-t3"])


def test_tier3_lines_are_dashed_context_and_tier3_labels_are_smallest() -> None:
    svg = _chart()
    for match in re.finditer(r'<line class="lvl-t3"[^/]*/>', svg):
        assert 'stroke-dasharray="2,4"' in match.group(0)
        assert 'stroke="#4a4a4a"' in match.group(0)
    sizes = {
        float(m.group("size")): m.group(0)
        for m in re.finditer(r'<text[^>]*font-size="(?P<size>[\d.]+)"[^>]*>[^<]*</text>', svg)
    }
    assert 7.5 in sizes  # tier-3 gutter labels
    assert min(sizes) == 7.5


def test_now_tag_is_boxed_and_tier1_words_are_bold() -> None:
    svg = _chart()
    assert '<rect class="now-tag"' in svg
    assert ">NOW 102.40<" in svg
    for word in ("ENTRY", "STOP"):
        assert re.search(rf'font-weight="bold"[^>]*>{word} [+-]\d', svg)


# ---------------------------------------------------------------------------
# R1/R3 — PRD-223 risk zone, PRD-304 lock neutralization
# ---------------------------------------------------------------------------

def test_risk_zone_shades_the_entry_to_stop_span() -> None:
    svg = _chart()
    rect = re.search(
        r'<rect class="risk-zone" x="0" y="(?P<y>[\d.]+)" width="\d+" '
        r'height="(?P<h>[\d.]+)" fill="#e05252" opacity="0.09"/>', svg
    )
    assert rect is not None
    entry_line = re.search(r'<line class="lvl-t1 lvl-entry" x1="0" y1="(?P<y>[\d.]+)"', svg)
    stop_line = re.search(r'<line class="lvl-t1 lvl-stop" x1="0" y1="(?P<y>[\d.]+)"', svg)
    assert entry_line is not None and stop_line is not None
    y_entry, y_stop = float(entry_line["y"]), float(stop_line["y"])
    assert float(rect["y"]) == min(y_entry, y_stop)
    assert float(rect["h"]) == pytest.approx(abs(y_entry - y_stop), abs=0.06)


@pytest.mark.parametrize(
    "bad_stop", [None, 0.0, -1.0, float("nan"), float("inf"), True, "n/a", 103.0]
)
def test_no_risk_zone_without_an_honest_contract_pair(bad_stop) -> None:
    # 103.0 == the entry: a zero-width span is not a risk zone.
    svg = _chart(contract_stop=bad_stop)
    assert "risk-zone" not in svg
    assert "lvl-stop" not in svg


def test_no_risk_zone_when_the_entry_is_missing() -> None:
    svg = _chart(contract_entry=None, contract_stop=100.5)
    assert "risk-zone" not in svg
    assert "lvl-stop" not in svg


def test_operator_lock_neutralizes_wording_and_every_action_colour() -> None:
    # R3 FAIL line. Mutation: drop the `operator_locked` branch -> ENTRY/STOP
    # and the amber/red action colours reappear.
    locked = _chart(operator_locked=True)
    assert "LEVEL " in locked and "INVALIDATION " in locked
    assert not re.search(r">ENTRY [+-]", locked)
    assert not re.search(r">STOP [+-]", locked)
    assert "#e0a552" not in locked
    assert "#e05252" not in locked
    assert "#6b7280" in locked
    # Non-vacuity: the unlocked render carries exactly what the lock removes.
    available = _chart()
    assert "#e0a552" in available and "#e05252" in available
    assert re.search(r">ENTRY [+-]", available)


# ---------------------------------------------------------------------------
# R1 — the tier map is FIXED and CLOSED
# ---------------------------------------------------------------------------

def test_tier_membership_is_the_fixed_closed_map() -> None:
    assert setup_chart.TIER2_TYPES == (
        "VWAP", "ORB_HIGH", "ORB_LOW", "PRIOR_HIGH", "PRIOR_LOW", "EMA9", "EMA21",
    )
    assert setup_chart.TIER3_TYPES == ("EMA50",)


def test_unknown_zone_types_are_not_inferred_into_a_tier() -> None:
    # Ruling Q4: no text-mining, no anchor inference. An unrecognised type is
    # simply not drawn on the chart (the compact ladder keeps the fact).
    svg = _chart(watch_zones=ZONES + [{"type": "SUPPORT_GUESS", "level": 101.7}])
    assert "SUPPORT_GUESS" not in svg
    assert "101.70" not in svg and "101.7 " not in svg


def test_orb_band_draws_only_when_both_edges_are_present() -> None:
    both = _chart(watch_zones=[{"type": "ORB_HIGH", "level": 103.2},
                               {"type": "ORB_LOW", "level": 101.4}])
    one = _chart(watch_zones=[{"type": "ORB_HIGH", "level": 103.2}])
    assert '<rect class="orb-band"' in both
    assert "orb-band" not in one


# ---------------------------------------------------------------------------
# R5 — responsive: viewBox scaling, no fixed pixel width
# ---------------------------------------------------------------------------

def test_svg_scales_by_viewbox_with_no_fixed_pixel_width() -> None:
    svg = _chart()
    assert svg.startswith(
        f'<svg viewBox="0 0 {setup_chart.CHART_WIDTH} {setup_chart.CHART_HEIGHT}" width="100%" '
    )
    assert 'height="844"' not in svg
    assert not re.search(r'<svg[^>]*width="\d+"', svg)


# ---------------------------------------------------------------------------
# R1/R3 — display-only import boundary
# ---------------------------------------------------------------------------

_FORBIDDEN_IMPORT_ROOTS = {
    "cuttingboard.runtime", "cuttingboard.market_map", "cuttingboard.trade_decision",
    "requests", "urllib", "urllib.request", "httpx", "yfinance", "socket",
    "time", "datetime", "random", "secrets",
}


def test_setup_chart_imports_no_decision_network_or_clock_module() -> None:
    # R1 FAIL line. Mutation: add `import datetime` (or a runtime import) to
    # setup_chart.py -> this goes red.
    tree = ast.parse((REPO_ROOT / "cuttingboard/delivery/setup_chart.py").read_text())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not imported & _FORBIDDEN_IMPORT_ROOTS, sorted(imported & _FORBIDDEN_IMPORT_ROOTS)
    assert not any(name.startswith("cuttingboard.") for name in imported), sorted(imported)


def test_only_the_delivery_layer_imports_setup_chart() -> None:
    # R3 FAIL line: `rg` finds no non-test, non-delivery module importing it.
    offenders: list[str] = []
    for root in ("cuttingboard", "tools", "scripts", "ui"):
        base = REPO_ROOT / root
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(REPO_ROOT)
            if rel.parts[:2] == ("cuttingboard", "delivery"):
                continue
            if "setup_chart" in path.read_text(encoding="utf-8"):
                offenders.append(str(rel))
    assert not offenders, f"setup_chart is display-only; found readers: {offenders}"


# ---------------------------------------------------------------------------
# PRD-330 R16 — frozen pre-D4 legacy byte oracle (S0; lands before any S1 change)
# ---------------------------------------------------------------------------
_LEGACY_ORACLE = REPO_ROOT / "tests" / "data" / "setup_chart_legacy_oracle.json"


def _oracle_render(case: dict) -> str:
    kw = dict(case["inputs"])
    return render_setup_chart_svg(kw.pop("bars"), kw.pop("now_price"), **kw)


def test_prd330_legacy_path_matches_frozen_oracle() -> None:
    # R11/R16: with no `layers` argument every representative render is byte-identical
    # to the sha256 frozen from the pre-PRD-330 module. Mutation: any byte of the
    # legacy paint list (order, attribute, rounding, leader threshold) fails this.
    oracle = _json.loads(_LEGACY_ORACLE.read_text())
    assert len(oracle["cases"]) >= 9
    for name, case in oracle["cases"].items():
        svg = _oracle_render(case)
        assert svg and len(svg) == case["length"], name
        assert _hashlib.sha256(svg.encode("utf-8")).hexdigest() == case["sha256"], name


def test_prd330_oracle_leader_threshold_is_a_real_boundary() -> None:
    # R16 non-vacuity: the two threshold cases sit at 4.0 (no leader) and 4.1 (leader)
    # units of displacement of the boxed ENTRY tag, straddling the legacy `> 4` rule.
    oracle = _json.loads(_LEGACY_ORACLE.read_text())
    for name, expect_leader in (("leader_threshold_exact_4_0", False), ("leader_threshold_just_over_4_1", True)):
        svg = _oracle_render(oracle["cases"][name])
        entry_y = re.search(r'class="lvl-t1 lvl-entry" x1="0" y1="([\d.]+)"', svg).group(1)
        assert (f'<line x1="280" y1="{entry_y}"' in svg) is expect_leader, name


# ---------------------------------------------------------------------------
# PRD-330 R7 / R10 / R12 — the five-segment compositor and the LEVELS layer
# ---------------------------------------------------------------------------
_ORB_ZONES = ZONES + [{"type": "ORB_HIGH", "level": 102.9}, {"type": "ORB_LOW", "level": 102.1},
                      {"type": "PRIOR_LOW", "level": 99.0}]
_SEG = re.compile(r'<g class="chart-layer" data-layer="([a-z]+)" data-part="([a-z]+)"( display="none")?>(.*?)</g>', re.S)
_ELEM = re.compile(r"<[^>]+?/>|<text[^>]*>[^<]*</text>")


def _layered(**kw) -> str:
    return _chart(contract_entry=None, contract_stop=None, watch_zones=_ORB_ZONES, layers=("levels",), **kw)


def _segments(svg: str) -> list[tuple[str, str, bool, str]]:
    return [(m.group(1), m.group(2), bool(m.group(3)), m.group(4)) for m in _SEG.finditer(svg)]


def _category(e: str) -> str:
    if e.startswith("<rect width="):
        return "bg"
    for key, cat in (("orb-band", "band"), ('class="lvl-t3"', "t3"), ('class="lvl-t2"', "t2"), ("candle", "candle"),
                     ("lvl-now", "now"), ("now-tag", "nowtag"), (">NOW ", "nowtag"), ("lvl-", "rail")):
        if key in e:
            return cat
    return "axis" if re.search(r">[A-Z][a-z]{2} \d{2}<", e) else "rail"


def _sequence(body: str) -> list[str]:
    out: list[str] = []
    for e in _ELEM.findall(body):
        c = _category(e)
        if not out or out[-1] != c:
            out.append(c)
    return out


def test_prd330_r7_five_segments_preserve_legacy_paint_order() -> None:
    # T1/T2: exact segment order and membership; category sequence equals the legacy render's;
    # level lines, band and candles byte-equal; VWAP line moves to base/price (D-2).
    svg, legacy = _layered(), _chart(contract_entry=None, contract_stop=None, watch_zones=_ORB_ZONES)
    segs = _segments(svg)
    assert [(s[0], s[1], s[2]) for s in segs] == [("base", "under", False), ("levels", "under", True),
                                                   ("base", "price", False), ("levels", "rail", True), ("base", "axis", False)]
    under, lv_under, price, lv_rail, axis = (s[3] for s in segs)
    assert under.startswith("<rect width=") and under.count("<") == 2 and "orb-band" in under
    assert price.startswith('<line class="lvl-t2"') and 'stroke="#29b6f6"' in price.split("/>", 1)[0]
    assert "candle-body" in price and "now-tag" in price and 'class="lvl-t3"' not in price
    assert lv_under.count('class="lvl-t3"') == 4 and lv_under.count('class="lvl-t2"') == 6 and "#29b6f6" not in lv_under
    assert axis.count("<text") == 2 and "</svg>" in svg[svg.index(axis) + len(axis):]
    legacy_elems = _ELEM.findall(legacy)
    for e in _ELEM.findall(lv_under) + _ELEM.findall(under) + _ELEM.findall(price):
        assert e in legacy_elems, e[:60]           # lines, band, candles, NOW: byte-equal to legacy
    assert _sequence(re.sub(r"</?g[^>]*>", "", svg[svg.index(">") + 1: svg.rindex("</svg>")])) == _sequence(
        legacy[legacy.index(">") + 1: legacy.rindex("</svg>")])
    with pytest.raises(ValueError):
        _chart(layers=("astro",))
    assert _chart() == _chart(layers=None)


def _rail_items(svg: str) -> tuple[list[float], list[tuple[str, float, float]], list[tuple[float, float]], str]:
    rail = _segments(svg)[3][3]
    ticks = [float(m) for m in re.findall(r'<line class="lvl-tick" x1="280" y1="([\d.]+)"', rail)]
    labels = [(t, float(y) - 10.5 * 0.35, 10.5) for y, t in
              re.findall(r'<text class="lvl-label" x="286" y="([\d.]+)" font-size="10.5" fill="#[0-9a-f]{3,6}">([^<]*)</text>', rail)]
    leaders = [(float(a), float(b)) for a, b in re.findall(r'<line class="lvl-leader" x1="283" y1="([\d.]+)" x2="285" y2="([\d.]+)"', rail)]
    return ticks, labels, leaders, rail


@pytest.mark.parametrize("name,zones,now,fibs", [
    ("live_like", _ORB_ZONES, 102.4, FIBS),
    ("symmetric_cluster", [{"type": t, "level": 102.4 + d} for t, d in
                           (("VWAP", -0.05), ("EMA9", 0.1), ("EMA21", -0.1), ("PRIOR_HIGH", 0.2), ("PRIOR_LOW", -0.2),
                            ("ORB_HIGH", 0.3), ("ORB_LOW", -0.3), ("EMA50", 0.4))], 102.4, FIBS),
    ("one_sided_below", [{"type": t, "level": 99.6 - i * 0.05} for i, t in
                         enumerate(("VWAP", "EMA9", "EMA21", "PRIOR_HIGH", "PRIOR_LOW", "ORB_HIGH", "ORB_LOW", "EMA50"))], 104.4, FIBS),
    ("forced_overflow_above", [{"type": t, "level": 104.45 + i * 0.05} for i, t in
                               enumerate(("VWAP", "EMA9", "EMA21", "PRIOR_HIGH", "PRIOR_LOW", "ORB_HIGH", "ORB_LOW", "EMA50"))], 104.4, FIBS),
    ("dense_sixteen_both_sides", [{"type": t, "level": 102.4 + d} for t, d in zip(("VWAP", "EMA9", "EMA21", "PRIOR_HIGH", "PRIOR_LOW", "ORB_HIGH", "ORB_LOW", "EMA50"), (0.02, 0.04, 0.06, 0.08, -0.02, -0.04, -0.06, -0.08))],
     102.4, {"retracements": {k: 102.2 + i * 0.05 for i, k in enumerate(("1.618", "1.272", "0.236", "0.382", "0.5", "0.618", "0.786", "1.0"))}}),
])
def test_prd330_r10_rail_invariants(name, zones, now, fibs) -> None:
    # T8: (a) no overlap, (b) clear of NOW, (c) side preserved, (d) in frame, (e) leader iff displaced > 2,
    # (f)+(g) a tick per level at legacy y, D-3 floor, 11-char cap; the overflow marker joins (a), (b), (d).
    svg = _chart(contract_entry=None, contract_stop=None, watch_zones=zones, fib_levels=fibs, now_price=now, layers=("levels",))
    legacy = _chart(contract_entry=None, contract_stop=None, watch_zones=zones, fib_levels=fibs, now_price=now)
    ticks, labels, leaders, rail = _rail_items(svg)
    now_y = float(re.search(r'class="lvl-t1 lvl-now" x1="0" y1="([\d.]+)"', svg).group(1))
    line_ys = sorted(float(y) for y in re.findall(r'<line class="lvl-t[23]" x1="0" y1="([\d.]+)"', legacy))
    assert sorted(ticks) == line_ys                                     # (f)+(g): one tick per level, legacy y
    assert sorted(float(y) for y in re.findall(r'<line class="lvl-t[23]" x1="0" y1="([\d.]+)"', svg)) == line_ys
    marker = re.findall(r'lvl-more" x="286" y="([\d.]+)" font-size="10.5" fill="#888">\+(\d+) in ladder</text>', rail)
    ys = sorted([y for _t, y, _f in labels] + [float(y) - 10.5 * 0.35 for y, _n in marker])   # marker included
    assert all(b - a >= 12 - 0.15 for a, b in zip(ys, ys[1:]))            # (a) (text y printed at 0.1)
    assert all(abs(y - now_y) >= 7 + 6 - 0.15 for y in ys)               # (b)
    assert all(len(t) <= 11 and re.search(r"\d+\.\d$", t) for t, _y, _f in labels)
    assert all(2 - 0.15 <= y - 6 and y + 6 <= 232 - 14 + 0.15 for y in ys)   # (d)
    assert all(any(abs(end - y) < 0.2 for _t, y, _f in labels) for _start, end in leaders)  # (e) leaders end at labels
    for tick_y, label_y in leaders:
        assert tick_y in ticks and abs(label_y - tick_y) > 2
        assert (tick_y <= now_y) == (label_y <= now_y)                  # (c) side preserved
    dropped = len(ticks) - len(labels)
    assert (dropped > 0) == bool(marker) and sum(int(n) for _y, n in marker) == dropped   # truthful +N
    assert (dropped >= 1) == name.startswith(("forced", "dense"))        # overflow path exercised iff forced
    assert "font-size=\"7.5\"" not in rail and 'font-size="8.5"' not in rail


def test_prd330_r12_probe_layer_two_positions_and_no_dead_ui(monkeypatch) -> None:
    # T6/T7: a synthetic layer renders independently in BOTH compositor positions; the
    # production map has one key; no astrology string anywhere; legacy path unaffected.
    from cuttingboard.delivery.setup_chart import LayerRenderResult
    def probe(ctx):
        return LayerRenderResult(('<rect class="probe-under" x="0" y="0" width="1" height="1"/>',),
                                 ('<text class="probe-rail" x="286" y="20">probe</text>',))
    legacy_before = _chart()
    monkeypatch.setitem(setup_chart._LAYER_RENDERERS, "probe", probe)
    svg = _chart(contract_entry=None, contract_stop=None, watch_zones=_ORB_ZONES, layers=("levels", "probe"))
    segs = [(s[0], s[1], s[2]) for s in _segments(svg)]
    assert segs == [("base", "under", False), ("levels", "under", True), ("probe", "under", True),
                    ("base", "price", False), ("levels", "rail", True), ("probe", "rail", True), ("base", "axis", False)]
    bodies = {(s[0], s[1]): s[3] for s in _segments(svg)}
    assert bodies[("probe", "under")] == probe(None).under_elements[0] and bodies[("probe", "rail")] == probe(None).rail_elements[0]
    assert "probe" not in bodies[("levels", "under")] and "probe" not in bodies[("levels", "rail")]
    assert _chart() == legacy_before                                    # candidate path byte-identical under the patch
    monkeypatch.undo()
    assert list(setup_chart._LAYER_RENDERERS) == ["levels"]
    source = (REPO_ROOT / "cuttingboard" / "delivery" / "setup_chart.py").read_text().lower()
    assert "astrolog" not in source and "probe" not in _layered()
