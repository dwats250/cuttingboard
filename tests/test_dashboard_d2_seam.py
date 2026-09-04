"""PRD-327 (D2) seam tests: R1, R2, R4-R9 over the VERDICT / TAPE emitters.

Constants were captured from the pre-implementation render at main ``a28e568``
(renderer bytes identical to the design baseline ``f555b48``). Below-seam and
TODAY hashes are raw base values; the R8 shape hashes are the base ordered
tuple lists with exactly the R8 removals applied (``.decision-state-label``,
``.sep``, the ``UPDATED`` label; the two TAPE ``.sep`` dividers; and, only when
``chips_visible`` is false, the ``.tape-trend`` wrapper with its six rows and
their cell spans). Any added, reordered or altered element goes RED.
"""
from __future__ import annotations

import hashlib
import html as _html
import json
from dataclasses import replace
from html.parser import HTMLParser
from pathlib import Path

import pytest

from cuttingboard import config
from cuttingboard.delivery import dashboard_renderer as _dr
from cuttingboard.delivery.dashboard_renderer import render_dashboard_html
from tests.dash_helpers import _macro_drivers, _market_map, _mm_symbol, _payload, _run
from tests.preview_fixtures import (
    SECTION_STATE_CASES,
    TREND_PARTIAL_COMPUTED_CASE,
    trend_structure_snapshot,
)

_SEAM = '<div class="block operator-zone" id="watching-zone">'
_DATA = Path(__file__).resolve().parent / "data"
_HERMETIC_MISSING = Path("/nonexistent/cuttingboard/preview_intraday_bars_snapshot.json")
_FIXTURES = {c.name: c for c in SECTION_STATE_CASES}
_CHIP_ROW = '<div class="tape-trend-row tape-slot '
_FORBIDDEN = ("ALIGNED", "DIVERGING", "CONFLUENT", "systems agree", "supportive", "favorable", "favourable", "constructive", "mildly", "environment", "overall", "score")

# --- base constants (see module docstring) ----------------------------------
_GOLDEN_BELOW_SEAM = {
    "dashboard_pre_gex_golden.html": "a7c47ca6c9461c6d33ec9e57496ba2ebf7e18adf438381ebebf10002cb60a294",
    "dashboard_pre_a1c_chart_golden.html": "f3ae5dac3e266b35f8cfa0984f2e35639e871be32a964a6fc5cb68952def0838",
}
# fixture -> (below-seam sha, #today-zone sha, #system-state shape sha, #tape-zone shape sha, chips_visible)
_BASE = {
    "coherence_mixed": ("2002dc68741278307786b550147c1e0107e2127ce8a0be32ddc2578aa79163a6", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "fc805de92df537814271ccb1a926f350ba1a9cd8ff53111e3ee4f53a2bdb885f", "f0a4d63a2524f78130c35a4e12c8a5fabbf392255e9d68be423f407585b5777b", True),
    "sunday_premarket": ("c5cae46a42f115d4e3c868d2a425da5d3e928194d67505278c50c8700136821a", "5941ce1a621774bef8dde02c39345956934d3c8eae8cb88b106ac7322bf20f66", "5b076058bf7ed302f6cb3d51d7eba4fb994df1b9cde7421cfd81ca4bdd0b16f9", "f0a4d63a2524f78130c35a4e12c8a5fabbf392255e9d68be423f407585b5777b", True),
    "session_inactive": ("b440494edb0546980c7b6880f8a1e8871bdf71a706eb4d49e9844c460a21cb89", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ff2d341419759e9d0b17871d3bd7f9ba3dfe42f529cdc6d76445a6cd5f6b27c6", "f0a4d63a2524f78130c35a4e12c8a5fabbf392255e9d68be423f407585b5777b", True),
    "macro_tape_no_data": ("01857236e904d4e388ff4dfd25cd62e77188ae1347bdf8babd6ae84acce698b2", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ff2d341419759e9d0b17871d3bd7f9ba3dfe42f529cdc6d76445a6cd5f6b27c6", "412ec82805afdab3c4bffe0cf3379c08c3a2882dc4f9d9a7888d15a7d777306a", False),
    "red_folder_error": ("f0d3db9d799b42a0a4b861673947e24aef7bc8ce04afbd9853998547ae770716", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ff2d341419759e9d0b17871d3bd7f9ba3dfe42f529cdc6d76445a6cd5f6b27c6", "c69b20f6f3b1d95e9288931cc005a0219d1a977c1a616a4b41015909f69ceb6d", False),
    "red_folder_expiring": ("75299dc8477df7575726c2802fd2362ea5230398f5581484705e1e9f0c7de053", "7193f1c51ba67ad739c81595af452b9ce0252adf30d56aa9e923b92918c4a17a", "ff2d341419759e9d0b17871d3bd7f9ba3dfe42f529cdc6d76445a6cd5f6b27c6", "c69b20f6f3b1d95e9288931cc005a0219d1a977c1a616a4b41015909f69ceb6d", False),
    "trend_awaiting_data": ("cbadc5771ba8df38a065b059f8bd421d33c53e207c1022d85c6102cdb087a487", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ff2d341419759e9d0b17871d3bd7f9ba3dfe42f529cdc6d76445a6cd5f6b27c6", "c69b20f6f3b1d95e9288931cc005a0219d1a977c1a616a4b41015909f69ceb6d", False),
    "trend_no_data": ("f7e81d41c0c75616e86056675b093949d831b69ed6db93a48a84b77c5272929a", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ff2d341419759e9d0b17871d3bd7f9ba3dfe42f529cdc6d76445a6cd5f6b27c6", "c69b20f6f3b1d95e9288931cc005a0219d1a977c1a616a4b41015909f69ceb6d", False),
    "lineage_missing": ("141120c43d65abcad07536653b99093e65b42e1e6ecf5bd35f0f083e17dd3445", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ac75c2ee6451560bebb0d902e48c19c8e3b435a48f0067f5662e1957d5e55b9a", "f0a4d63a2524f78130c35a4e12c8a5fabbf392255e9d68be423f407585b5777b", True),
    "candidate_no_candidates": ("2cdeae717797db506ad1320d2df4c885eb7e042da9558a29cf2a1c3757479980", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ac75c2ee6451560bebb0d902e48c19c8e3b435a48f0067f5662e1957d5e55b9a", "c69b20f6f3b1d95e9288931cc005a0219d1a977c1a616a4b41015909f69ceb6d", False),
    "healthy_baseline": ("51656f4556944f71c9a938e5e08f82374f287757f49be1ca14003872d309c379", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ff2d341419759e9d0b17871d3bd7f9ba3dfe42f529cdc6d76445a6cd5f6b27c6", "c69b20f6f3b1d95e9288931cc005a0219d1a977c1a616a4b41015909f69ceb6d", False),
    "primary_chart_stay_flat": ("64f9b9770ced65e1b788c84c1c57c6a185312ed9a2b16bc388b0033b03ab52fb", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "752057e4b3a798459bf5ff560231f0fbe391a5d0644eb270ba9a0b414cb1273f", "c69b20f6f3b1d95e9288931cc005a0219d1a977c1a616a4b41015909f69ceb6d", False),
    "primary_chart_locked": ("a433f33bee641107e80757606e4ca72e498aef57270b4bcaedb9efb986392333", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "e5f021067242fcf703545706745af21a908ef9c4c700fcb3b7f1bb46519003f5", "c69b20f6f3b1d95e9288931cc005a0219d1a977c1a616a4b41015909f69ceb6d", False),
    "primary_chart_permitted": ("47e75c5feb400b9790e9979d5bc7a03ab646cfa238374d4b8ed5a59cf0499c95", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b0820f37f0aa6f0cf6894e2c28872624aa4cfd5b9f5ed305f905575a4c8639d5", "c69b20f6f3b1d95e9288931cc005a0219d1a977c1a616a4b41015909f69ceb6d", False),
    "market_map_stale_with_bars": ("d79fa1d96f7b6c3cbec7d211e004e1d79a6fc40de59e3f471b27d0f461f65a52", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "752057e4b3a798459bf5ff560231f0fbe391a5d0644eb270ba9a0b414cb1273f", "f0a4d63a2524f78130c35a4e12c8a5fabbf392255e9d68be423f407585b5777b", True),
    "primary_chart_c_grade": ("c895f9e31ebbdbad02e6934abb517260fc2823c26b3b4f1dbe840f400ddd3ae7", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "608ca086de81d2e082e8453d48ca74b10abfa5795568730d1b3f6eb726a9300a", "c69b20f6f3b1d95e9288931cc005a0219d1a977c1a616a4b41015909f69ceb6d", False),
}
_R1_AUTHORITY = {
    "stay_flat": {"decision": "STAY FLAT", "verdict": "Longs allowed · NO TRADE", "why": "WHY: no qualified setups",
            "kill": None, "permission": None, "regime": "Risk-on regime"},
    "locked": {"decision": "OBSERVE ONLY", "verdict": "Operator locked: cannot monitor · NO TRADE", "why": None,
            "kill": None, "permission": "No new trades permitted — operator cannot monitor.", "regime": "Risk-on regime"},
    "permitted": {"decision": "TRADE PERMITTED", "verdict": "Longs allowed · TRADE SETUP ACTIVE", "why": None,
            "kill": None, "permission": None, "regime": "Risk-on regime"},
    "halt": {"decision": "HALT", "verdict": "Longs allowed · SYSTEM HALT", "why": "WHY: operational halt",
            "kill": "Kill switch active", "permission": None, "regime": "Risk-on regime"},
    "mixed": {"decision": "STATE UNAVAILABLE", "verdict": "Longs allowed · INPUTS OUT OF SYNC", "why": None,
            "kill": None, "permission": None, "regime": "Risk-on regime"},
}
_R2_UPDATED_LINE = '<div class="value" id="cb-updated" data-updated-utc="2026-04-28T12:00:00+00:00">Updated Apr 28 · 5:00 AM PT</div>'
_STALENESS_JS_SHA = "90ca619252eb0a303222902941851743b37e1c28f9b19efc2b34db8ed40d7689"


@pytest.fixture(autouse=True)
def _hermetic_intraday_sidecar(monkeypatch):
    monkeypatch.setattr(_dr, "_INTRADAY_BARS_SNAPSHOT_PATH", _HERMETIC_MISSING)


def _sha(text: str | bytes) -> str:
    return hashlib.sha256(text if isinstance(text, bytes) else text.encode("utf-8")).hexdigest()


def _render(case) -> str:
    return render_dashboard_html(case.payload, case.run, market_map=case.market_map,
                                 fixture_mode=case.fixture_mode, **case.render_kwargs)


def _block(html: str, block_id: str) -> str:
    """Exact `<div ... id="{block_id}"> ... </div>` fragment (nesting-aware)."""
    idx = html.find(f'id="{block_id}"')
    assert idx != -1, f"{block_id} not rendered"
    start = html.rfind("<div", 0, idx)
    i, depth = start, 0
    while True:
        nd, ne = html.find("<div", i), html.find("</div>", i)
        if nd != -1 and nd < ne:
            depth, i = depth + 1, nd + 4
        else:
            depth, i = depth - 1, ne + 6
            if depth == 0:
                return html[start:i]


def _pre_watching(html: str) -> str:
    return html.split(_SEAM, 1)[0]


def _visible_text_above_fold(html: str) -> str:
    """Direct visible text of every element in the three pre-WATCHING zones."""
    return " ".join(t[3] for zone in ("system-state", "tape-zone", "today-zone")
                    for t in zone_tuples(html, zone) if t[3])


_HELPER_RUNS = {"stay_flat": {"outcome": "NO_TRADE"}, "permitted": {"outcome": "TRADE", "permission": True},
                "locked": {"outcome": "NO_TRADE", "permission": config.OPERATOR_LOCK_PERMISSION},
                "halt": {"system_halted": True, "kill_switch": True}}


def _helper_render(name: str) -> str:
    p, r = _payload(macro_drivers=_macro_drivers()), _run(**_HELPER_RUNS.get(name, {}))
    if name != "mixed":
        return render_dashboard_html(p, r)
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    p["meta"]["generation_id"], r["generation_id"], mm["generation_id"] = "mixed-p", "mixed-r", "mixed-mm"
    return render_dashboard_html(p, r, market_map=mm)


# --- ordered (tag, class, id, direct visible text) walk of one zone ----------


class _ZoneWalk(HTMLParser):
    def __init__(self, zone_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self._zone_id, self._stack, self._root_depth, self.done = zone_id, [], None, False
        self.entries: list[list] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.done:
            return
        if self._root_depth is None and a.get("id") == self._zone_id:
            self._root_depth = len(self._stack)
        entry = [tag, a.get("class", ""), a.get("id", ""), []]
        if self._root_depth is not None:
            self.entries.append(entry)
        self._stack.append(entry)

    def handle_endtag(self, tag):
        if self.done:
            return
        while self._stack:
            if self._stack.pop()[0] == tag:
                break
        if self._root_depth is not None and len(self._stack) == self._root_depth:
            self.done = True

    def handle_data(self, data):
        if self._root_depth is not None and not self.done and self._stack:
            self._stack[-1][3].append(data)


def zone_tuples(html: str, zone_id: str) -> list[tuple[str, str, str, str]]:
    walker = _ZoneWalk(zone_id)
    walker.feed(html)
    assert walker.done, f"zone {zone_id!r} not found or unterminated"
    return [(t, c, i, "".join(parts).strip()) for t, c, i, parts in walker.entries]


def _first(fragment: str, opener: str) -> str | None:
    if opener not in fragment:
        return None
    return fragment.split(opener, 1)[1].split("</div>", 1)[0]


# --- R1: decision state first, undivided; authority strings byte-identical ---
@pytest.mark.parametrize("name", sorted(_R1_AUTHORITY))
def test_r1_decision_block_is_first_undivided_and_byte_identical(name) -> None:
    html = _helper_render(name)
    ids = [html.find(f'id="{i}"') for i in ("system-state", "tape-zone", "today-zone",
                                              "watching-zone", "details-history")]
    assert all(i != -1 for i in ids) and ids == sorted(ids)
    state = _block(html, "system-state")
    assert "decision-state-label" not in html
    assert ">UPDATED</div>" not in html
    assert 'class="sep"' not in state
    pre = _pre_watching(html)
    assert pre.count('class="decision-state ') == 1
    assert pre.count('class="sys-permission"') <= 1
    if name == "mixed":  # R6: the coherence warning stays ahead of the decision block
        assert html.find('id="artifact-coherence"') < html.find('id="system-state"')
    got = {
        "decision": _first(state, '<div class="decision-state ').split(">", 1)[1],
        "verdict": _first(state, "<div class=\"sys-verdict ").split(">", 1)[1],
        "why": _first(state, '<div class="sys-why">'),
        "kill": _first(state, '<div class="sys-context halted">Kill') and "Kill switch active",
        "permission": _first(state, '<div class="sys-permission">'),
        "regime": _first(state, '<div class="sys-context">') or _first(state, '<div class="sys-context halted">'),
    }
    assert got == _R1_AUTHORITY[name]


# --- R2: the freshness element is byte-identical and follows the regime line -
def test_r2_updated_line_byte_identical_after_regime_line() -> None:
    state = _block(_helper_render("stay_flat"), "system-state")
    assert _R2_UPDATED_LINE in state
    assert state.index('<div class="sys-context">') < state.index(_R2_UPDATED_LINE)
    assert _sha(_dr._STALENESS_BANNER_JS) == _STALENESS_JS_SHA


# --- R4: the narrowed D2-Q2 chip gate, exact truth table -----------------------
_CHIP_TABLE = [  # (case, chips expected)
    # zero computed + healthy lineage + active session -> suppressed
    ("healthy_baseline", False), ("trend_no_data", False), ("trend_awaiting_data", False),
    ("primary_chart_stay_flat", False), ("primary_chart_locked", False), ("primary_chart_permitted", False),
    # any computed row (five na chips included) / unhealthy lineage / inactive session -> all six chips
    ("trend_partial_computed", True), ("six_computed", True), ("coherence_mixed", True), ("lineage_missing", True),
    ("market_map_stale_with_bars", True), ("session_inactive", True), ("sunday_premarket", True),
]


def _table_case(name):
    if name == "trend_partial_computed":
        return TREND_PARTIAL_COMPUTED_CASE
    if name == "six_computed":
        return replace(_FIXTURES["healthy_baseline"], name=name, render_kwargs={
            "trend_structure_snapshot": trend_structure_snapshot(config.TREND_STRUCTURE_SYMBOLS)})
    return _FIXTURES[name]


@pytest.mark.parametrize("name,chips", _CHIP_TABLE)
def test_r4_chip_gate_truth_table(name, chips) -> None:
    html = _render(_table_case(name))
    tape = _block(html, "tape-zone")
    assert 'class="sep"' not in tape
    assert tape.count('<div class="tape-band">') == 2 and 'data-derivation="' in tape
    rows = [seg.split('"', 1)[0] for seg in tape.split(_CHIP_ROW)[1:]]
    if chips:
        assert 'class="tape-trend"' in tape and len(rows) == 6
        syms = [seg.split("</span>", 1)[0] for seg in tape.split(_CHIP_ROW)[1:]]
        assert [s.split("<span>", 1)[1] for s in syms] == list(config.TREND_STRUCTURE_SYMBOLS)
    else:
        assert "tape-trend" not in tape and rows == []
    if name == "trend_partial_computed":  # filtering only the na rows must go RED
        assert rows.count("na") == 5 and rows.count("up") == 1
    if name == "six_computed":
        assert set(rows) == {"up"}


# --- R5: TODAY byte-identical -------------------------------------------------
@pytest.mark.parametrize("name", sorted(_BASE))
def test_r5_today_zone_byte_identical(name) -> None:
    assert _sha(_block(_render(_FIXTURES[name]), "today-zone")) == _BASE[name][1]


# --- R6: unavailable / failure states stay named above the fold ---------------
_COMMON = ("Trend unavailable", '<div class="zone-value">unavailable</div>', "not captured")
_R6_TABLE = {
    "coherence_mixed": _COMMON + ("Inputs are out of sync", "STATE UNAVAILABLE", "Event schedule unavailable"),
    "macro_tape_no_data": _COMMON + ("Macro unavailable", "Pressure unavailable", "Event schedule unavailable"),
    "trend_awaiting_data": _COMMON + ("Event schedule unavailable",),
    "primary_chart_locked": _COMMON + ("No new trades permitted — operator cannot monitor.",
                                       "Event schedule unavailable"),
    "session_inactive": _COMMON + ("Event schedule unavailable",),
    "red_folder_expiring": _COMMON,
}


@pytest.mark.parametrize("name", sorted(_R6_TABLE))
def test_r6_unavailable_states_named_above_the_fold(name) -> None:
    pre = _html.unescape(_pre_watching(_render(_FIXTURES[name])))
    for needle in _R6_TABLE[name]:
        assert needle in pre, needle


def test_r6_kill_switch_stays_in_the_decision_block() -> None:
    assert "Kill switch active" in _block(_helper_render("halt"), "system-state")


# --- R7: chips leave the fold only where DETAILS enumerates the symbols -------
@pytest.mark.parametrize("name", sorted(_BASE))
def test_r7_suppressed_chips_imply_the_deep_six_symbol_table(name) -> None:
    html = _render(_FIXTURES[name])
    deep = _block(html, "trend-structure")
    chips = "tape-trend" in _block(html, "tape-zone")
    assert chips == _BASE[name][4]
    if not chips:
        assert 'class="ts-table"' in deep
        assert all(f">{sym}<" in deep for sym in config.TREND_STRUCTURE_SYMBOLS)
    else:
        assert 'class="ts-table"' not in deep


# --- R8: exact shape, no new visible text -------------------------------------
@pytest.mark.parametrize("name", sorted(_BASE))
def test_r8_exact_shape_equals_base_minus_listed_removals(name) -> None:
    html = _render(_FIXTURES[name])
    ss, tz = zone_tuples(html, "system-state"), zone_tuples(html, "tape-zone")
    exp_ss, exp_tz = _BASE[name][2], _BASE[name][3]
    assert _sha(json.dumps(ss)) == exp_ss, ss
    assert _sha(json.dumps(tz)) == exp_tz, tz
    text = _visible_text_above_fold(html)
    assert not any(tok in text for tok in _FORBIDDEN), text


def test_r8_partial_case_adds_no_forbidden_text() -> None:
    html = _render(TREND_PARTIAL_COMPUTED_CASE)
    text = _visible_text_above_fold(html)
    assert not any(tok in text for tok in _FORBIDDEN), text
    pre = _pre_watching(html)
    assert "decision-state-label" not in pre and ">UPDATED</div>" not in pre


# --- R9: below-seam byte invariance -------------------------------------------
@pytest.mark.parametrize("filename", sorted(_GOLDEN_BELOW_SEAM))
def test_r9_golden_below_seam_hash(filename) -> None:
    raw = (_DATA / filename).read_bytes()
    assert _sha(raw.split(_SEAM.encode(), 1)[1]) == _GOLDEN_BELOW_SEAM[filename]


@pytest.mark.parametrize("name", sorted(_BASE))
def test_r9_fixture_below_seam_hash(name) -> None:
    html = _render(_FIXTURES[name])
    assert _sha(html.split(_SEAM, 1)[1]) == _BASE[name][0]


# --- CSS cone: the three non-phone edits, phone block untouched ---------------
def test_css_edits_confined_to_the_non_phone_region() -> None:
    non_phone, _sep, phone = _dr._CSS.partition("@media(max-width:430px){")
    assert ".decision-state-label{" not in _dr._CSS
    assert "#system-state>h2{margin-bottom:.3rem}" in non_phone
    assert ".tape-band+.tape-band,.tape-band+.tape-foot{margin-top:6px}" in non_phone
    assert "tape-band+" not in phone and "#system-state .sep{margin:5px 0}" in phone
