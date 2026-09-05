"""PRD-327 (D2) seam tests: R1, R2, R5-R9 over the VERDICT / MARKET STRUCTURE seam.

PRD-334 R11: the SHA / copy constants were regenerated after the whole-page
recomposition (the #tape-zone was deleted, its content consolidated into
#market-structure; the TAPE trend chips were removed; the verdict copy is now a
faithful translation). The 4th _BASE slot is the MARKET STRUCTURE region shape
(was #tape-zone); the chips_visible column and the chip-gate test (R4) are retired.
Any added, reordered or altered element still goes RED.
"""
from __future__ import annotations

import hashlib
import html as _html
import json
from html.parser import HTMLParser
from pathlib import Path

import pytest

from cuttingboard import config
from cuttingboard.delivery import dashboard_renderer as _dr
from cuttingboard.delivery.dashboard_renderer import render_dashboard_html
from tests.dash_helpers import _macro_drivers, _market_map, _mm_symbol, _payload, _run
from tests.preview_fixtures import SECTION_STATE_CASES, TREND_PARTIAL_COMPUTED_CASE

_SEAM = '<div class="block operator-zone" id="watching-zone">'
_DATA = Path(__file__).resolve().parent / "data"
_HERMETIC_MISSING = Path("/nonexistent/cuttingboard/preview_intraday_bars_snapshot.json")
_FIXTURES = {c.name: c for c in SECTION_STATE_CASES}
_FORBIDDEN = ("ALIGNED", "DIVERGING", "CONFLUENT", "systems agree", "supportive", "favorable", "favourable", "constructive", "mildly", "environment", "overall", "score")

# --- base constants (PRD-334 R11: regenerated after the whole-page recomposition;
# the seam marker id="watching-zone" is unchanged, but below-seam now covers
# MARKET STRUCTURE's descendants after WATCHING plus GEX and HISTORY) -----------
_GOLDEN_BELOW_SEAM = {
    "dashboard_pre_gex_golden.html": "cc459fc358f1f7433f0aa024bf231090be00cc0340279a4462d67b11b722cfd8",
    "dashboard_pre_a1c_chart_golden.html": "5e32399ffca3ce3935c7efa6b36b2e1b914cd7387b96f44a92f1052fce88d9a0",
}
# fixture -> (below-seam sha, #today-zone sha, #system-state shape sha, #market-structure shape sha)
# PRD-334 R11: the 4th slot is the MARKET STRUCTURE region shape (was #tape-zone,
# now deleted); the chips_visible column is retired (the TAPE trend chips were removed).
_BASE = {
    "coherence_mixed": ("83b14c7be6d3d061eb5d1f678a69ffcdba57d337554ca57a8dbf92ac4721aefa", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ea116ec497d4fe3818f9e952f952987e04d36c5c0c65f1c1ec471d95cab98fc9", "1bb56276f12d95b32d9d4ff9088d61efcad280e025a4d3fc9fb38d1eb4cc746a"),
    "sunday_premarket": ("71eb7820dcfa0b2138b6b61aa4f06c3a78ed0bb9cfba7fb14e94b5c651108161", "5941ce1a621774bef8dde02c39345956934d3c8eae8cb88b106ac7322bf20f66", "2a2a3502ba43b78b32d2a3c29976c4551667fac1f088bd4897fd70181298873f", "b9fff6df99f2832411fd7acf94f8089fd37d819ffc96d5ef146bfdd5317868e9"),
    "session_inactive": ("71eb7820dcfa0b2138b6b61aa4f06c3a78ed0bb9cfba7fb14e94b5c651108161", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "24b0d9b674f6aa92bc339f99bef2321eb595b03b841ee5b33ceea457d385e5f9"),
    "macro_tape_no_data": ("4138862aaa0bb9165bb7492cb318fb12b2445d46e238f9d6a198d4df3c679d50", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "ed4af1fbf0f15be2fdef1125523feac890ff998f4b927cba5a9f83a3e0a83ce5"),
    "red_folder_error": ("4138862aaa0bb9165bb7492cb318fb12b2445d46e238f9d6a198d4df3c679d50", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "e5c5da77562563628909f4577bc8607ce25c70fa0327ac0392c8d9b5c6575847"),
    "red_folder_expiring": ("4138862aaa0bb9165bb7492cb318fb12b2445d46e238f9d6a198d4df3c679d50", "7193f1c51ba67ad739c81595af452b9ce0252adf30d56aa9e923b92918c4a17a", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "e5c5da77562563628909f4577bc8607ce25c70fa0327ac0392c8d9b5c6575847"),
    "trend_awaiting_data": ("4138862aaa0bb9165bb7492cb318fb12b2445d46e238f9d6a198d4df3c679d50", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "fa7d8d2ca6e4ee785f1e158dfa7609dd7e1f190c150a360cea604651277134f0"),
    "trend_no_data": ("4138862aaa0bb9165bb7492cb318fb12b2445d46e238f9d6a198d4df3c679d50", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "e5c5da77562563628909f4577bc8607ce25c70fa0327ac0392c8d9b5c6575847"),
    "lineage_missing": ("cc459fc358f1f7433f0aa024bf231090be00cc0340279a4462d67b11b722cfd8", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "78b3bca20cbb53f5be20e53dbed076133d65f93709085fda25c932b3790cacb9", "1259d822a2d1d2f81b1993f13287e048e5533e9fd1bc0f076212b1ae5cb83a66"),
    "candidate_no_candidates": ("39613f7113a867d4ced0a55c4befdbaf0744dcd767a665c13ba552e0770d4cea", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "78b3bca20cbb53f5be20e53dbed076133d65f93709085fda25c932b3790cacb9", "cdeed514a063237d42eca68d69f0254dff8624a0066262b0e3993be6bdee9a59"),
    "healthy_baseline": ("db3fcf2a345016a199399fba8e9cb0c847fc26bd479497c0203ebe024aa1d2c3", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "e5c5da77562563628909f4577bc8607ce25c70fa0327ac0392c8d9b5c6575847"),
    "primary_chart_stay_flat": ("f989e1f21413fd4f624035fcb6efeab659b49a462affe29061485f73d7679cdc", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ce88cf68f914483308e472e5c4cb34b4238d3fc094a58be493800fa9f10f04af", "cf3047e84de94e5691797e955910d9ca72ac65d0272a7e9ab3830b3edc9f1bec"),
    "primary_chart_locked": ("c468ddf43aa602d187b015d5ea9a2ccc28b809a902055448decf1014ef82634d", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "0494c5bd3fb155b16ee9671081b1389892eb0c94b2c84f7ad1399d83d161b8ad", "cf3047e84de94e5691797e955910d9ca72ac65d0272a7e9ab3830b3edc9f1bec"),
    "primary_chart_permitted": ("7a7bda6b25af128de9c301a6d9327f94b0c4a22cd1b5109719c28e01de2add96", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "272a564bdce4954c38f4b7d00c4fbf55f228476c9c74c9ff3a76335ff5abbb6a", "cf3047e84de94e5691797e955910d9ca72ac65d0272a7e9ab3830b3edc9f1bec"),
    "market_map_stale_with_bars": ("45297d42d4e9e6ee2b925ea2717a1c2a826b836cd80d6c9c5d7405466fe5938d", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ce88cf68f914483308e472e5c4cb34b4238d3fc094a58be493800fa9f10f04af", "80d92052a141e55335ff36cb8086a050b9ec0ee676e503f0f61dbf1c956a11e1"),
    "primary_chart_c_grade": ("48b56e1dffe62034f49d1ad7573fcf86b16bda8e9ffead34cbad1e4072f15ae3", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "6894564b2b77672146384d0e09c40dc8a283e28fe8c6c0f1388a946af5e3b0f6", "2599249efaaff6e6320ede6876836f44c5efc2e06e66c7a34095c227ce4c496f"),
}
# PRD-334 R3: the verdict is now a faithful translation -- TRADE PERMITTED shows the
# regime verb; STAY FLAT / OBSERVE ONLY read "No new trades permitted"; HALT reads
# "System halted"; mixed reads "Inputs out of sync". The internal title token left
# the visible sentence (it survives only in data-raw-title).
_R1_AUTHORITY = {
    "stay_flat": {"decision": "STAY FLAT", "verdict": "No new trades permitted", "why": "WHY: no qualified setups",
            "kill": None, "permission": None, "regime": "Risk-on regime"},
    "locked": {"decision": "OBSERVE ONLY", "verdict": "No new trades permitted", "why": None,
            "kill": None, "permission": "No new trades permitted — operator cannot monitor.", "regime": "Risk-on regime"},
    "permitted": {"decision": "TRADE PERMITTED", "verdict": "Longs allowed", "why": None,
            "kill": None, "permission": None, "regime": "Risk-on regime"},
    "halt": {"decision": "HALT", "verdict": "System halted", "why": "WHY: operational halt",
            "kill": "Kill switch active", "permission": None, "regime": "Risk-on regime"},
    "mixed": {"decision": "STATE UNAVAILABLE", "verdict": "Inputs out of sync", "why": None,
            "kill": None, "permission": None, "regime": "Risk-on regime"},
}
_R2_UPDATED_LINE = '<div class="value" id="cb-updated" data-updated-utc="2026-04-28T12:00:00+00:00">Updated Apr 28 · 5:00 AM PT</div>'
_STALENESS_JS_SHA = "293812c1ded273bfd2133221939d6f4889f0af556bafd267429c00c0017d10cd"


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
    """Direct visible text of every element in the pre-WATCHING zones (PRD-334 R9:
    MARKET STRUCTURE replaced the deleted TAPE zone)."""
    return " ".join(t[3] for zone in ("system-state", "market-structure", "today-zone")
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
    # PRD-334 R9 order: VERDICT -> NEXT EVENT -> MARKET STRUCTURE -> WATCHING -> GEX -> HISTORY.
    ids = [html.find(f'id="{i}"') for i in ("system-state", "today-zone", "market-structure",
                                              "watching-zone", "gex-zone", "details-history")]
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


# --- R4: PRD-334 R5 removed the bland TAPE trend chips (replaced by the promoted
# #trend-structure table). The chip-gate truth table (test_r4_chip_gate_truth_table)
# and its helpers are deleted; the promoted table is asserted in test_r7 below.


# --- R5: TODAY byte-identical -------------------------------------------------
@pytest.mark.parametrize("name", sorted(_BASE))
def test_r5_today_zone_byte_identical(name) -> None:
    assert _sha(_block(_render(_FIXTURES[name]), "today-zone")) == _BASE[name][1]


# --- R6: unavailable / failure states stay named above the fold ---------------
# PRD-334 R9: above-fold unavailable states now come from VERDICT, NEXT EVENT and
# MARKET STRUCTURE (macro-tape "NO LIVE MACRO DATA", the promoted trend table's
# "no trend structure data"), never the deleted TAPE zone. Every unavailable state
# is still NAMED, never silent.
_R6_TABLE = {
    "coherence_mixed": ("Inputs are out of sync", "STATE UNAVAILABLE", "Event schedule unavailable"),
    "macro_tape_no_data": ("NO LIVE MACRO DATA", "no trend structure data", "Event schedule unavailable"),
    "trend_awaiting_data": ("no trend structure data", "Event schedule unavailable"),
    "primary_chart_locked": ("No new trades permitted — operator cannot monitor.", "Event schedule unavailable"),
    "session_inactive": ("SESSION INACTIVE", "Event schedule unavailable"),
    "red_folder_expiring": ("no trend structure data",),
}


@pytest.mark.parametrize("name", sorted(_R6_TABLE))
def test_r6_unavailable_states_named_above_the_fold(name) -> None:
    pre = _html.unescape(_pre_watching(_render(_FIXTURES[name])))
    for needle in _R6_TABLE[name]:
        assert needle in pre, needle


def test_r6_kill_switch_stays_in_the_decision_block() -> None:
    assert "Kill switch active" in _block(_helper_render("halt"), "system-state")


# --- R7: the promoted Trend Structure table is the single trend representation --
@pytest.mark.parametrize("name", sorted(_BASE))
def test_r7_promoted_trend_table_present(name) -> None:
    # PRD-334 R5: the TAPE trend chips are gone; the promoted #trend-structure
    # "curated watch set" table (in MARKET STRUCTURE) is the trend representation.
    html = _render(_FIXTURES[name])
    assert 'id="tape-zone"' not in html and 'class="tape-trend"' not in html
    deep = _block(html, "trend-structure")
    assert "curated watch set" in deep


# --- R8: exact region shape, no new visible text ------------------------------
@pytest.mark.parametrize("name", sorted(_BASE))
def test_r8_exact_region_shape(name) -> None:
    html = _render(_FIXTURES[name])
    ss = zone_tuples(html, "system-state")
    ms = zone_tuples(html, "market-structure")   # PRD-334 R9: replaced the deleted tape-zone
    exp_ss, exp_ms = _BASE[name][2], _BASE[name][3]
    assert _sha(json.dumps(ss)) == exp_ss, ss
    assert _sha(json.dumps(ms)) == exp_ms, ms
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
