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
    "dashboard_pre_gex_golden.html": "d974a89ef8c36901caeb465ab8000bfd9aad4acc7225af784eb67a38a19f992f",
    "dashboard_pre_a1c_chart_golden.html": "c67a18de7638745b118e6c8414af2683aafbde2b0bdd46cd1751018e38334cb5",
}
# fixture -> (below-seam sha, #today-zone sha, #system-state shape sha, #market-structure shape sha)
# PRD-334 R11: the 4th slot is the MARKET STRUCTURE region shape (was #tape-zone,
# now deleted); the chips_visible column is retired (the TAPE trend chips were removed).
_BASE = {
    "candidate_no_candidates": ("a83214e514f55b75eba8f3f8280da6aa66c5d9399bfea9b90f98e56d03b52978", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "2d7f850dd2b5044c15a577b9bd28bd35ba45c3e248e3021f3f441d52cc75ecf5", "4e6aef8ffac4dee352264e9b9bed03202e8606dd82eb56e5ed560c009c1d6c25"),
    "coherence_mixed": ("c9d35d80a14197282480e00503bdf0d4969ae742f9d50a38a655182cb79f0908", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ea116ec497d4fe3818f9e952f952987e04d36c5c0c65f1c1ec471d95cab98fc9", "e4b73cbf6e0726883960d2631f32d4a3bf561b0981f67f74aad7b50b8cf59932"),
    "healthy_baseline": ("1f5e28a6ab2e043e6400f3fddc9366f8def4ecde84ded86842900583b82b5498", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "2ba331f020aacb2ab5819b9842d29b0804478d3f4332820d7aae1fdd6e9b96db", "f403c437524bc787e4a8fc368928b8cd9ba1889ac843a4b74751185479d72e42"),
    "lineage_missing": ("d974a89ef8c36901caeb465ab8000bfd9aad4acc7225af784eb67a38a19f992f", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "2d7f850dd2b5044c15a577b9bd28bd35ba45c3e248e3021f3f441d52cc75ecf5", "4b6f47e328110d82f216d7673c179cc4c346115cf235459d925f8953ef3d77a5"),
    "macro_tape_no_data": ("4a2eefc61d1b86fed621e93e288fb3d367297bbb9f62ded0d9951d40418fda68", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "2ba331f020aacb2ab5819b9842d29b0804478d3f4332820d7aae1fdd6e9b96db", "b2e2f391e9714008ca17c389e951e5152472f4a7b633dd9687a8e10c318ee10b"),
    "market_map_stale_with_bars": ("07c6dc0e9f86a42f8457ba7a73b7003db9c73ec86969dad692412748c2a4d36d", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "39a200802a473f73235b22d0a662285ea5aa4388475cb09f775fc183dc09882a", "e76a61e759216f6a93df45f79c346908d9891f72e5b078261d7396c872d9856c"),
    "primary_chart_c_grade": ("575c04b388e2e2792fc24ad4e8f799d4a0c75b7a35870c0661d9527ca84ed972", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "aa5398f2e7378c3460d772c159e48f488569e093453ecf69aa89a3a77a5d6054", "a87253c520ea85b6448916304fe8897ad7bae1abdcb7a84c1480a9a54b5cd8da"),
    "primary_chart_locked": ("fa604afe3a7485d1309c03c445ef68211167584a3872593c2722c5d36e01114f", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "f44c626b83638c700db4e3fac21a9a2e657214bcbfc49ec88253751a56f54e4c", "a1b01427ea1713f05b703d115c36e5f38bd26dfcdc06f659ce2abbf050eb53fc"),
    "primary_chart_permitted": ("a9f11c297a7793767983bfc465128d0e803b519b14fa894e6d2db510e6270f69", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "0aca9da205ed7b45dc3168b1457c702b7a36498cf806bb7f82119a5a2e187c62", "a1b01427ea1713f05b703d115c36e5f38bd26dfcdc06f659ce2abbf050eb53fc"),
    "primary_chart_stay_flat": ("c55ea490dfdd2cc34123b13c44d2647c31ae0415045baa7c1b5be4b0bc80b1d2", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "39a200802a473f73235b22d0a662285ea5aa4388475cb09f775fc183dc09882a", "a1b01427ea1713f05b703d115c36e5f38bd26dfcdc06f659ce2abbf050eb53fc"),
    "red_folder_error": ("4a2eefc61d1b86fed621e93e288fb3d367297bbb9f62ded0d9951d40418fda68", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "2ba331f020aacb2ab5819b9842d29b0804478d3f4332820d7aae1fdd6e9b96db", "f403c437524bc787e4a8fc368928b8cd9ba1889ac843a4b74751185479d72e42"),
    "red_folder_expiring": ("4a2eefc61d1b86fed621e93e288fb3d367297bbb9f62ded0d9951d40418fda68", "7193f1c51ba67ad739c81595af452b9ce0252adf30d56aa9e923b92918c4a17a", "2ba331f020aacb2ab5819b9842d29b0804478d3f4332820d7aae1fdd6e9b96db", "f403c437524bc787e4a8fc368928b8cd9ba1889ac843a4b74751185479d72e42"),
    "session_inactive": ("a85e6f01f23659227d20ef79182aebb3ce5bd15781cb52e2dd7ad2169d5b0331", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "2ba331f020aacb2ab5819b9842d29b0804478d3f4332820d7aae1fdd6e9b96db", "b55f6c58a2f920619bb9a1a4062987791af6f3c497367a0e051846049c9e2966"),
    "sunday_premarket": ("a85e6f01f23659227d20ef79182aebb3ce5bd15781cb52e2dd7ad2169d5b0331", "5941ce1a621774bef8dde02c39345956934d3c8eae8cb88b106ac7322bf20f66", "990ad97c790939e7547a1572b4e63b8bc261f7fd2d72d199effcae78d2c26f5c", "3e9d6863dd9f113ae66cf8340bc48011d268b406a2f723ae3bb89f26a5f223d7"),
    "trend_awaiting_data": ("4a2eefc61d1b86fed621e93e288fb3d367297bbb9f62ded0d9951d40418fda68", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "2ba331f020aacb2ab5819b9842d29b0804478d3f4332820d7aae1fdd6e9b96db", "622653ee6cb26a044cb87f27c54b80893103418c9c11eb8848c017fad948e795"),
    "trend_no_data": ("4a2eefc61d1b86fed621e93e288fb3d367297bbb9f62ded0d9951d40418fda68", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "2ba331f020aacb2ab5819b9842d29b0804478d3f4332820d7aae1fdd6e9b96db", "f403c437524bc787e4a8fc368928b8cd9ba1889ac843a4b74751185479d72e42"),
}
# PRD-334 R3: the verdict is now a faithful translation -- TRADE PERMITTED shows the
# regime verb; STAY FLAT / OBSERVE ONLY read "No new trades permitted"; HALT reads
# "System halted"; mixed reads "Inputs out of sync". The internal title token left
# the visible sentence (it survives only in data-raw-title).
_R1_AUTHORITY = {
    "stay_flat": {"decision": "STAY FLAT", "verdict": "", "why": "WHY: no qualified setups",
            "kill": None, "permission": None, "regime": "Risk-on regime"},
    "locked": {"decision": "OBSERVE ONLY", "verdict": "", "why": None,
            "kill": None, "permission": "No new trades permitted — operator cannot monitor.", "regime": "Risk-on regime"},
    "permitted": {"decision": "TRADE PERMITTED", "verdict": "", "why": None,
            "kill": None, "permission": None, "regime": "Risk-on regime"},
    "halt": {"decision": "HALT", "verdict": "", "why": "WHY: operational halt",
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
    _verdict_frag = _first(state, '<div class="sys-verdict ')
    got = {
        "decision": _first(state, '<div class="decision-state ').split(">", 1)[1],
        # PRD-335 R5: the sys-verdict div is omitted for STAY FLAT / OBSERVE ONLY /
        # HALT / generic-unavailable, so the verdict slot is "".
        "verdict": _verdict_frag.split(">", 1)[1] if _verdict_frag else "",
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
