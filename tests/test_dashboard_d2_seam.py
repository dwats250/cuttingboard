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
    "dashboard_pre_gex_golden.html": "53026f083109a78f32a439b42b810a85585ab690f586fea9d06aa4c27f9f763e",
    "dashboard_pre_a1c_chart_golden.html": "54d53ce031928de69de026c46bb1ec29723cc86c5d5326cbd19d3cb72eaeba8b",
}
# fixture -> (below-seam sha, #today-zone sha, #system-state shape sha, #market-structure shape sha)
# PRD-334 R11: the 4th slot is the MARKET STRUCTURE region shape (was #tape-zone,
# now deleted); the chips_visible column is retired (the TAPE trend chips were removed).
_BASE = {
    "coherence_mixed": ("9e18cc4bfe495873be435af23cddfab0938633a8386f2200e2b4642ae013bfe4", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ea116ec497d4fe3818f9e952f952987e04d36c5c0c65f1c1ec471d95cab98fc9", "d34745b9fa0906fa7677e04a120c932dd3bb9485fdfa77617cacca3541bea4b3"),
    "sunday_premarket": ("b9811ab5a305f9b5945a594f0e28cfc5a94537fb770958292bf21fcd5aef301c", "5941ce1a621774bef8dde02c39345956934d3c8eae8cb88b106ac7322bf20f66", "2a2a3502ba43b78b32d2a3c29976c4551667fac1f088bd4897fd70181298873f", "127eeb7785b9283ba848b521c29312d17ab879c3afbee1b9f932a36b61845ffe"),
    "session_inactive": ("b9811ab5a305f9b5945a594f0e28cfc5a94537fb770958292bf21fcd5aef301c", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "0e8d117b1124494089098a0771287432494ddf9f1a283675396addaece6e2179"),
    "macro_tape_no_data": ("c273f3f2959f3e8bce8f7506a240370762fdeeacf9d7ba4e16c2afe6bf4b5e09", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "782013c69dc9ec1f9e283202ae0ecb312414468fdd67fe73be90ea5444ef441a"),
    "red_folder_error": ("c273f3f2959f3e8bce8f7506a240370762fdeeacf9d7ba4e16c2afe6bf4b5e09", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "f6cfd0f0c217a34f9104f494efc5dcfb8fec831b7575f4116b9bcf0889afeed4"),
    "red_folder_expiring": ("c273f3f2959f3e8bce8f7506a240370762fdeeacf9d7ba4e16c2afe6bf4b5e09", "7193f1c51ba67ad739c81595af452b9ce0252adf30d56aa9e923b92918c4a17a", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "f6cfd0f0c217a34f9104f494efc5dcfb8fec831b7575f4116b9bcf0889afeed4"),
    "trend_awaiting_data": ("c273f3f2959f3e8bce8f7506a240370762fdeeacf9d7ba4e16c2afe6bf4b5e09", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "b77e2d8b228a12f80bd27690f0d1dab3a0e0dad37c97a41c3d1c9c1901795d82"),
    "trend_no_data": ("c273f3f2959f3e8bce8f7506a240370762fdeeacf9d7ba4e16c2afe6bf4b5e09", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "f6cfd0f0c217a34f9104f494efc5dcfb8fec831b7575f4116b9bcf0889afeed4"),
    "lineage_missing": ("53026f083109a78f32a439b42b810a85585ab690f586fea9d06aa4c27f9f763e", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "78b3bca20cbb53f5be20e53dbed076133d65f93709085fda25c932b3790cacb9", "b162fffa5afe418f5ff22ee3b09a79350d8b7ec443a0ea00de71ab65d07977b8"),
    "candidate_no_candidates": ("426d46b3b58ba7f8c473311e32b433d04186f82550bf0cfc610d966b0f9d735a", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "78b3bca20cbb53f5be20e53dbed076133d65f93709085fda25c932b3790cacb9", "a87e8387a082440fb38e3e48166f4d41a7934fe91327ebe82aa73313978e16b6"),
    "healthy_baseline": ("68effde0fc0082a85e74a3b93e0e6f1413b431428e30575d42700151f0f3e7b3", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "b3a935c38b351c414d9f28636de961b4abfa81859312394d341c5fa50331c0d0", "f6cfd0f0c217a34f9104f494efc5dcfb8fec831b7575f4116b9bcf0889afeed4"),
    "primary_chart_stay_flat": ("9e5916bf4327e6977fca1eeb61741f91aec7bf5476992867b73841a00e75e8a9", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ce88cf68f914483308e472e5c4cb34b4238d3fc094a58be493800fa9f10f04af", "dbd29cd394d05bd34daab48d209214d10df4303e0a68f5bcbe79f092027204ca"),
    "primary_chart_locked": ("18ce16a9f9fadada6e083fbd0524512faa1b7b0d0bb422ba97fb6c312fc1e975", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "0494c5bd3fb155b16ee9671081b1389892eb0c94b2c84f7ad1399d83d161b8ad", "dbd29cd394d05bd34daab48d209214d10df4303e0a68f5bcbe79f092027204ca"),
    "primary_chart_permitted": ("db7f4f1bf92b48cdd00afcd662faa4c76a18f7042cf02999f0d9938bcc91fc94", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "272a564bdce4954c38f4b7d00c4fbf55f228476c9c74c9ff3a76335ff5abbb6a", "dbd29cd394d05bd34daab48d209214d10df4303e0a68f5bcbe79f092027204ca"),
    "market_map_stale_with_bars": ("bd1acc319221e42d906ed53117769353673bb8b01218a7a3887d1acc632e7821", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "ce88cf68f914483308e472e5c4cb34b4238d3fc094a58be493800fa9f10f04af", "197b49e0bcaa2e2da511905267ca5ccc6cc91d9cdb1cdd63b3466132653feded"),
    "primary_chart_c_grade": ("0c9ebcf8a8ab9755e77aa8631ab9b143a296df08482ef0726b65bb12e8320d83", "d3c7a817cd633556c57fb2a55899c1e44392858fd0377bfa1f6a9e3668ef1a65", "6894564b2b77672146384d0e09c40dc8a283e28fe8c6c0f1388a946af5e3b0f6", "ecae7d18937a9d72cbba2f253d33f85961708806ead37bcc13c941513f778b60"),
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
