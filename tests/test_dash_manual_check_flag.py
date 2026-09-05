"""PRD-331: MANUAL CHECK flag on the ALERT WATCHLIST row (presentation-only).

An alert candidate whose contract classification is NEEDS_MANUAL_CHECK renders a
labelled, color-independent "MANUAL CHECK" flag as the first token of its
#alert-watchlist row inside WATCHING; every other row stays byte-identical.

The flag is keyed on the verbatim contract field ``setup_quality`` (written at
cuttingboard/contract.py:352 as ``chain.classification``); the constant
NEEDS_MANUAL_CHECK is cuttingboard.chain_validation.MANUAL_CHECK.

Discriminators used deliberately: the class attribute ``class="candidate-state
manual-check"`` (a SPACE; the CSS selector uses a dot ``.candidate-state.manual
-check``) and the visible label ``MANUAL CHECK`` (a SPACE; the CSS class is the
hyphenated ``manual-check-flag``). Neither HTML-only form appears in ``_CSS``, so
they cleanly prove presence/absence of the rendered flag independent of the
always-present stylesheet.
"""

from __future__ import annotations

import copy

import cuttingboard.delivery.dashboard_renderer as _dr
from cuttingboard.delivery.dashboard_renderer import render_dashboard_html
from tests.dash_helpers import _payload, _run, _trade_decision
from tests.test_dash_candidates import _top_block, _top_ids

# The real MANUAL_CHECK candidate shape (^TNX + chain reason) is the live shape
# from logs/run_2026-05-07_052221.json; hourly contracts are latest-only so no
# archived contract can be loaded directly (PRD-331 VALIDATION note).
_MANUAL_REASON = "chain data unavailable from all sources"
# Expected rendered form (symbol/direction/reason are uppercased and the em dash
# separator is emitted exactly as the existing row does at dashboard_renderer.py).
_MANUAL_ROW = (
    '<div class="candidate-state manual-check" data-raw-state="NEEDS_MANUAL_CHECK">'
    '<span class="manual-check-flag">MANUAL CHECK</span> '
    "^TNX LONG — CHAIN DATA UNAVAILABLE FROM ALL SOURCES</div>"
)


def _manual(sym: str = "^TNX", direction: str = "LONG", reason: str | None = _MANUAL_REASON) -> dict:
    c = _trade_decision(
        sym, direction, decision_status="BLOCK_TRADE", block_reason=reason,
        trace_reason=(reason or "NEEDS_MANUAL_CHECK"),
    )
    c["setup_quality"] = "NEEDS_MANUAL_CHECK"  # verbatim contract field (contract.py:352)
    c["notes"] = reason
    return c


def _non_manual(sym: str = "META", setup_quality: str | None = None) -> dict:
    c = _trade_decision(sym, "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION")
    if setup_quality is not None:
        c["setup_quality"] = setup_quality
    return c


def _css_rule(selector: str) -> str:
    css = _dr._CSS
    i = css.find(selector)
    assert i != -1, f"{selector!r} not found in _CSS"
    return css[i:css.find("}", i) + 1]


# --- R1 -------------------------------------------------------------------
def test_manual_check_row_carries_label_and_raw_state() -> None:
    html = render_dashboard_html(_payload(), _run(), alert_candidates=[_manual()])
    block = _top_block(html, "alert-watchlist")
    assert _MANUAL_ROW in block


# --- R2 (mutation guard; green before and after) --------------------------
def test_non_manual_rows_byte_identical_and_label_absent() -> None:
    cands = [
        _non_manual("META"),                                       # no setup_quality key
        _non_manual("META", setup_quality="DISQUALIFIED_OPTIONS_INVALID"),
        _non_manual("META", setup_quality="TOP_TRADE_VALIDATED"),
    ]
    html = render_dashboard_html(_payload(), _run(), alert_candidates=cands)
    block = _top_block(html, "alert-watchlist")
    assert block.count('<div class="candidate-state">META LONG — LATE_SESSION</div>') == 3
    # HTML-only discriminators: absent when no manual candidate (CSS uses a dot
    # and the hyphenated class, so neither of these substrings is in _CSS).
    assert 'class="candidate-state manual-check"' not in html
    assert "MANUAL CHECK" not in html


# --- R2 (single surface, once per candidate, order preserved) -------------
def test_manual_check_flag_rendered_once_per_candidate_and_only_in_alert_watchlist() -> None:
    cands = [_manual("^TNX"), _non_manual("META"), _manual("XLE", "SHORT")]
    html = render_dashboard_html(_payload(), _run(), alert_candidates=cands)
    block = _top_block(html, "alert-watchlist")
    # Exactly two labels, and every occurrence lies inside #alert-watchlist.
    assert html.count("MANUAL CHECK") == 2
    assert block.count("MANUAL CHECK") == 2
    # Input order preserved: ^TNX, META, XLE.
    assert block.index("^TNX") < block.index("META") < block.index("XLE")


# --- R3 (keyed on classification, not reason text) ------------------------
def test_manual_check_flag_keyed_on_setup_quality_not_reason_text() -> None:
    # (a) chain-flavoured reason text but NOT the NEEDS_MANUAL_CHECK class -> no flag.
    a = _non_manual("META")
    a["block_reason"] = _MANUAL_REASON
    html_a = render_dashboard_html(_payload(), _run(), alert_candidates=[a])
    assert 'class="candidate-state manual-check"' not in html_a
    assert "MANUAL CHECK" not in html_a
    # (b) NEEDS_MANUAL_CHECK with a None block reason -> flag, and NO trailing separator.
    html_b = render_dashboard_html(_payload(), _run(), alert_candidates=[_manual("SPY", "LONG", reason=None)])
    block_b = _top_block(html_b, "alert-watchlist")
    assert '<span class="manual-check-flag">MANUAL CHECK</span> SPY LONG</div>' in block_b


# --- R4 (legible without color) -------------------------------------------
def test_manual_check_flag_legible_without_color() -> None:
    html = render_dashboard_html(_payload(), _run(), alert_candidates=[_manual()])
    block = _top_block(html, "alert-watchlist")
    start = block.index('<div class="candidate-state manual-check"')
    row = block[start:block.index("</div>", start) + 6]
    import re
    visible = re.sub(r"<[^>]+>", "", row)
    assert visible.startswith("MANUAL CHECK ")
    assert visible.index("MANUAL CHECK") < visible.index("^TNX")  # position cue precedes ticker
    # Color-independent cues live in CSS structure, not hue alone.
    flag_rule = _css_rule(".manual-check-flag{")
    assert "border:1px solid currentColor" in flag_rule
    assert "content:" not in flag_rule  # label is real HTML body text, not CSS-generated
    assert "border-left:3px solid" in _css_rule(".candidate-state.manual-check{")
    # The label text is in the HTML body, not only in the stylesheet.
    assert "MANUAL CHECK" in block


# --- R4 (CSS outside the protected phone block) ---------------------------
def test_manual_check_css_outside_protected_phone_block() -> None:
    non_phone, _, phone = _dr._CSS.partition("@media(max-width:430px){")
    assert phone, "phone media block not found in _CSS"
    assert ".manual-check-flag{" in non_phone
    assert ".candidate-state.manual-check{" in non_phone
    assert "manual-check" not in phone


# --- R4 (presentation-only: no input mutation, no new top-level block) -----
def test_manual_check_render_does_not_mutate_inputs() -> None:
    cands = [_manual(), _non_manual("META")]
    snapshot = copy.deepcopy(cands)
    html = render_dashboard_html(_payload(), _run(), alert_candidates=cands)
    assert cands == snapshot  # inputs untouched
    ids = _top_ids(html)
    # No new top-level block; alert-watchlist stays immediately before candidate-board (PRD-332 D5).
    assert "alert-watchlist" in ids
    assert ids.index("candidate-board") == ids.index("alert-watchlist") + 1


# --- R4 (mobile layout tokens: the row wraps, never overflows) ------------
def test_manual_check_flag_mobile_layout_tokens() -> None:
    # CI has no browser (see the 390px CDP proof in PRD-331 VALIDATION); pin the
    # mechanism instead: the flag is inline-block with no width/nowrap pins, so a
    # long reason wraps at 390px rather than forcing horizontal overflow.
    rule = _css_rule(".manual-check-flag{")
    assert "display:inline-block" in rule
    assert "white-space:nowrap" not in rule
    assert "min-width" not in rule
    assert "width:" not in rule
    # The row div carries no inline style attribute.
    html = render_dashboard_html(_payload(), _run(), alert_candidates=[_manual()])
    block = _top_block(html, "alert-watchlist")
    start = block.index('<div class="candidate-state manual-check"')
    row = block[start:block.index(">", start) + 1]
    assert "style=" not in row
