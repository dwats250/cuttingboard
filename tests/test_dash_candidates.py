"""Tests for PRD-055 — dashboard renderer: Candidate board, tiers, cards, setup_state, candidate_risk, grade_order, lifecycle badges/detail, removed symbols."""

from __future__ import annotations

from cuttingboard.delivery.dashboard_renderer import (
    _GRADE_ORDER,
    render_dashboard_html,
)

import pytest

from tests.dash_helpers import (
    _PC_BARS,
    _bars_snapshot,
    _chartable,
    _intraday_snapshot,
    _market_map,
    _mm_symbol,
    _payload,
    _run,
)


# ---------------------------------------------------------------------------
# PRD-315 depth-aware top-level extraction (test-local; replaces Candidate-
# relative substring sentinels invalidated by the Opportunity->Candidate move).
# ---------------------------------------------------------------------------

def _top_ids(html: str) -> list[str]:
    """Ordered top-level `.block` ids via depth-aware sibling scan."""
    ids: list[str] = []
    i = 0
    while True:
        j = html.find('class="block', i)
        if j == -1:
            break
        k = html.find('id="', j)
        e = html.find('"', k + 4)
        ids.append(html[k + 4:e])
        i = e
    return ids


def _top_block(html: str, block_id: str) -> str:
    """Exact `<div ... id="{block_id}"> ... </div>` fragment (matches nested divs)."""
    marker = f'id="{block_id}"'
    idx = html.find(marker)
    assert idx != -1, f"{block_id} not rendered"
    start = html.rfind("<div", 0, idx)
    i, depth = start, 0
    while i < len(html):
        nd = html.find("<div", i)
        nc = html.find("</div>", i)
        if nc == -1:
            break
        if nd != -1 and nd < nc:
            depth += 1
            i = nd + 4
        else:
            depth -= 1
            i = nc + 6
            if depth == 0:
                return html[start:i]
    return html[start:]


# ---------------------------------------------------------------------------
# R3 — Candidate Visibility Board
# ---------------------------------------------------------------------------

def test_candidate_board_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'id="candidate-board"' in html


def test_candidate_board_market_map_absent() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=None)
    assert 'id="candidate-board"' in html
    assert "SOURCE_MISSING" in html


def test_candidate_board_empty_symbols() -> None:
    mm   = _market_map({})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="candidate-board"' in html
    assert "Map empty — no symbols graded this run" in html
    assert ">NO_CANDIDATES<" not in html


def test_candidate_board_sort_order() -> None:
    syms = {
        "XLE": _mm_symbol("XLE", grade="C"),
        "GLD": _mm_symbol("GLD", grade="A"),
        "SPY": _mm_symbol("SPY", grade="A+"),
        "SLV": _mm_symbol("SLV", grade="B"),
        "QQQ": _mm_symbol("QQQ", grade="A"),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    # A+(SPY) < A(GLD) < A(QQQ) < B(SLV) < C(XLE) — GLD before QQQ alphabetically
    assert html.index('id="card-SPY"') < html.index('id="card-GLD"')
    assert html.index('id="card-GLD"') < html.index('id="card-QQQ"')
    assert html.index('id="card-QQQ"') < html.index('id="card-SLV"')
    assert html.index('id="card-SLV"') < html.index('id="card-XLE"')


def test_candidate_board_all_symbols_rendered() -> None:
    syms = {s: _mm_symbol(s, grade="B") for s in ("SPY", "QQQ", "GLD")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    for sym in ("SPY", "QQQ", "GLD"):
        assert f'id="card-{sym}"' in html


# ---------------------------------------------------------------------------
# R3.1 — Tier Grouping
# ---------------------------------------------------------------------------

def test_tier_grouping_order() -> None:
    syms = {
        "QQQ": _mm_symbol("QQQ", grade="A+"),
        "SPY": _mm_symbol("SPY", grade="B"),
        "GLD": _mm_symbol("GLD", grade="C"),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert html.index('id="tier-aplus"') < html.index('id="tier-b"') < html.index('id="tier-c"')


def test_tier_empty_group_absent() -> None:
    syms = {"SPY": _mm_symbol("SPY", grade="A+")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="tier-aplus"' in html
    assert 'id="tier-a"'     not in html
    assert 'id="tier-b"'     not in html
    assert 'id="tier-c"'     not in html


def test_tier_header_labels() -> None:
    syms = {
        "SPY": _mm_symbol("SPY", grade="A+"),
        "QQQ": _mm_symbol("QQQ", grade="A"),
        "GLD": _mm_symbol("GLD", grade="B"),
        "SLV": _mm_symbol("SLV", grade="C"),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "A+ — ACTIONABLE"  in html
    assert "A — HIGH QUALITY" in html
    assert "B — DEVELOPING"   in html
    assert "C — EARLY"        in html


# ---------------------------------------------------------------------------
# R4 — Candidate Card Fields
# ---------------------------------------------------------------------------

def test_card_always_rendered_fields() -> None:
    syms = {"SPY": _mm_symbol("SPY", grade="C", bias="BEAR", structure="DOWNTREND")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = html.split('id="card-SPY"', 1)[1]
    assert "SPY"       in card
    assert "C"         in card
    assert "BEAR"      in card
    assert "DOWNTREND" in card


def test_card_grade_css_class() -> None:
    for grade, css in (("A+", "grade-aplus"), ("A", "grade-a"), ("B", "grade-b"),
                       ("C", "grade-c"), ("D", "grade-d"), ("F", "grade-f")):
        syms = {"SPY": _mm_symbol("SPY", grade=grade)}
        mm   = _market_map(syms)
        html = render_dashboard_html(_payload(), _run(), market_map=mm)
        assert css in html, f"CSS class {css} not found for grade {grade}"


def test_card_id_present() -> None:
    syms = {"NVDA": _mm_symbol("NVDA", grade="A")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="card-NVDA"' in html


def test_low_grade_card_fields_excluded() -> None:
    syms = {
        "GLD": _mm_symbol(
            "GLD",
            grade="C",
            setup_state="RANGE_BOUND",
            trade_framing={
                "direction": "NEUTRAL",
                "if_now": "WAIT_UNIQUE",
                "entry": "above 220_UNIQUE",
                "downgrade": "break below 210_UNIQUE",
            },
            invalidation=["below 200_UNIQUE"],
            reason_for_grade="low quality setup_UNIQUE",
        ),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = html.split('id="card-GLD"', 1)[1]
    # Execution/trade-framing fields stay suppressed on low-grade cards
    assert "WAIT_UNIQUE"            not in card
    assert "above 220_UNIQUE"       not in card
    assert "below 200_UNIQUE"       not in card
    assert "break below 210_UNIQUE" not in card
    # PRD-098 R5/R6: reason_for_grade is now rendered as diagnostic/validation
    # inside collapsed diagnostics — suppressing it would violate R6
    assert "low quality setup_UNIQUE" in card


def test_high_grade_card_shows_optional_fields() -> None:
    syms = {
        "SPY": _mm_symbol(
            "SPY",
            grade="A+",
            setup_state="BREAKOUT",
            trade_framing={"direction": "LONG", "if_now": "BUY_UNIQUE", "entry": "above 510_UNIQUE"},
            invalidation=["below 490_UNIQUE"],
            reason_for_grade="strong trend_UNIQUE",
        ),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "BUY_UNIQUE"          in html
    assert "above 510_UNIQUE"    in html
    assert "below 490_UNIQUE"    in html
    assert "strong trend_UNIQUE" in html


# ---------------------------------------------------------------------------
# R4.1 — PRD-249: single-line header, verdict-first order, cut STATE/RISK lines
# ---------------------------------------------------------------------------

def _card(html: str, sym: str) -> str:
    """This card's HTML, bounded at the next candidate card so 'not in' holds."""
    after = html.split(f'id="card-{sym}"', 1)[1]
    return after.split('class="candidate-card', 1)[0]


def test_header_single_line_composition() -> None:
    # R1: SYMBOL · GRADE · STATE · BIAS STRUCTURE on one header line.
    syms = {"SPY": _mm_symbol("SPY", grade="A+", bias="BULL", structure="UPTREND",
                              setup_state="BREAKOUT")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = _card(html, "SPY")
    assert 'class="card-header"' in card
    assert "SPY · A+ · BREAKOUT · BULL UPTREND" in card


def test_header_replaces_stacked_identity_block() -> None:
    # R1: the old stacked GRADE/BIAS/STRUCTURE label pairs are gone on a
    # high-grade card.
    syms = {"SPY": _mm_symbol("SPY", grade="A+")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = _card(html, "SPY")
    assert '<div class="label">GRADE</div>'     not in card
    assert '<div class="label">BIAS</div>'      not in card
    assert '<div class="label">STRUCTURE</div>' not in card


def test_header_omits_setup_state_when_data_unavailable() -> None:
    # R1: a DATA_UNAVAILABLE setup_state is not surfaced in the header.
    syms = {"SPY": _mm_symbol("SPY", grade="A", setup_state="DATA_UNAVAILABLE")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = _card(html, "SPY")
    assert "DATA_UNAVAILABLE" not in card


def test_verdict_first_before_couplet() -> None:
    # R2: the IF NOW verdict renders before the IN → couplet.
    syms = {"SPY": _mm_symbol("SPY", grade="A+", setup_state="BREAKOUT",
                              trade_framing={"direction": "LONG",
                                             "if_now": "WAIT",
                                             "entry": "hold above reference"})}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = _card(html, "SPY")
    assert card.index("IF NOW") < card.index("IN →")


def test_in_out_couplet_labels_and_accent() -> None:
    # R4: entry/invalidation render as the IN →/OUT → couplet, both keeping the
    # cyan actionable accent, in that order. PRD-249 review advisory: OUT folds
    # downgrade's non-redundant structural clause (the part after " or ").
    syms = {"SPY": _mm_symbol("SPY", grade="A",
                              trade_framing={"direction": "LONG",
                                             "entry": "above 510_UNIQUE",
                                             "downgrade": "wait if price loses 510_UNIQUE or structure turns choppy"},
                              invalidation=["below 490_UNIQUE"])}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = _card(html, "SPY")
    assert ('<div class="label">IN →</div>'
            '<div class="value-key value-actionable">above 510_UNIQUE</div>') in card
    assert ('<div class="label">OUT →</div>'
            '<div class="value-key value-actionable">below 490_UNIQUE, or structure turns choppy</div>') in card
    assert card.index("IN →") < card.index("OUT →")


def test_out_line_folds_downgrade_structural_clause() -> None:
    # PRD-249 review advisory: downgrade carries a structural-invalidation clause
    # ("structure turns choppy") distinct from the price-reclaim condition. It is
    # folded into OUT so dropping the standalone RISK line loses NO data. Asserted
    # on the RENDERED OUT value so a future refactor can't silently drop it.
    syms = {"SPY": _mm_symbol(
        "SPY", grade="A", bias="BEAR",
        trade_framing={"direction": "SHORT",
                       "entry": "rejects near PRIOR_HIGH with downside follow-through",
                       "downgrade": "wait if price reclaims PRIOR_HIGH or structure turns choppy"},
        invalidation=["reclaims PRIOR_HIGH with follow-through"])}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = _card(html, "SPY")
    out_value = card.split(
        '<div class="label">OUT →</div><div class="value-key value-actionable">', 1
    )[1].split('</div>', 1)[0]
    # both invalidation paths are on the single OUT line
    assert "reclaims PRIOR_HIGH with follow-through" in out_value
    assert "structure turns choppy" in out_value
    # ...but the redundant price-clause of downgrade is NOT reintroduced, and no
    # standalone RISK line comes back.
    assert "wait if price reclaims" not in out_value
    assert 'class="candidate-risk"' not in card


def test_risk_line_removed() -> None:
    # R4: the standalone RISK line (trade_framing.downgrade) is gone.
    syms = {"SPY": _mm_symbol("SPY", grade="A",
                              trade_framing={"direction": "LONG",
                                             "entry": "hold above reference",
                                             "downgrade": "break below 500_UNIQUE"})}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = _card(html, "SPY")
    assert 'class="candidate-risk"' not in card
    assert "RISK:"                  not in card
    assert "break below 500_UNIQUE" not in card


def test_standalone_state_line_removed_but_state_retained() -> None:
    # R4: the standalone STATE line is gone; setup_state lives in the header.
    syms = {"SPY": _mm_symbol("SPY", grade="A+", setup_state="BREAKOUT")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = _card(html, "SPY")
    assert 'class="candidate-state"' not in card
    assert "STATE: BREAKOUT"         not in card
    assert "BREAKOUT"                in card  # retained in the header


def test_watch_single_joined_line() -> None:
    # R5: multiple what_to_look_for items render as ONE semicolon-joined WATCH
    # line under a single label, not one label per item.
    sym = _mm_symbol("SPY", grade="A")
    sym["what_to_look_for"] = ["watch A_UNIQUE", "watch B_UNIQUE"]
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map({"SPY": sym}))
    card = _card(html, "SPY")
    assert card.count('<div class="label">WATCH</div>') == 1
    assert "watch A_UNIQUE; watch B_UNIQUE" in card


def test_risk_and_state_absent_on_low_grade() -> None:
    # Low-grade cards never carried the RISK/STATE lines; still absent.
    syms = {"GLD": _mm_symbol("GLD", grade="D",
                              trade_framing={"direction": "SHORT",
                                             "downgrade": "break above 200"})}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    assert 'class="candidate-risk"'  not in html
    assert 'class="candidate-state"' not in html


# ---------------------------------------------------------------------------
# R6 — _GRADE_ORDER constant
# ---------------------------------------------------------------------------

def test_grade_order_constant_correct() -> None:
    assert _GRADE_ORDER["A+"] == 0
    assert _GRADE_ORDER["A"]  == 1
    assert _GRADE_ORDER["B"]  == 2
    assert _GRADE_ORDER["C"]  == 3
    assert _GRADE_ORDER["D"]  == 4
    assert _GRADE_ORDER["F"]  == 5


def test_sort_deterministic() -> None:
    syms = {s: _mm_symbol(s, grade="B") for s in ("ZZZ", "AAA", "MMM")}
    mm   = _market_map(syms)
    html1 = render_dashboard_html(_payload(), _run(), market_map=mm)
    html2 = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert html1 == html2
    # alphabetical within same grade: AAA < MMM < ZZZ
    assert html1.index('id="card-AAA"') < html1.index('id="card-MMM"') < html1.index('id="card-ZZZ"')


# ---------------------------------------------------------------------------
# R7 — market_map optional
# ---------------------------------------------------------------------------

def test_render_accepts_market_map_none() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=None)
    assert "SOURCE_MISSING" in html


def test_render_accepts_market_map_dict() -> None:
    mm   = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="card-SPY"' in html


# ---------------------------------------------------------------------------
# PRD-055 PATCH — candidate idle summary
# ---------------------------------------------------------------------------

def test_candidate_idle_summary_when_no_actionable() -> None:
    syms = {"GLD": _mm_symbol("GLD", grade="C"), "SLV": _mm_symbol("SLV", grade="D")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "NO ACTIONABLE SETUPS" in html
    assert "Market is not offering structure" in html


def test_candidate_idle_summary_absent_when_actionable() -> None:
    syms = {"SPY": _mm_symbol("SPY", grade="A+")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "NO ACTIONABLE SETUPS" not in html


def test_candidate_idle_summary_absent_when_no_symbols() -> None:
    mm   = _market_map({})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "NO ACTIONABLE SETUPS" not in html


def test_candidate_idle_summary_absent_when_map_none() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=None)
    assert "NO ACTIONABLE SETUPS" not in html


# ---------------------------------------------------------------------------
# PRD-168 — suppress the RULE2 idle verdict above populated high-grade cards
# ---------------------------------------------------------------------------

def test_prd168_rule2_verdict_suppressed_above_high_grade_card() -> None:
    # regime permits longs (RISK_ON); the only high-grade card is a SHORT setup,
    # so the integrator emits "No qualifying long setups" AND a high-grade card
    # renders. PRD-168 D1: suppress the RULE2 verdict when a high-grade card shows.
    from cuttingboard.delivery.dashboard_integrator import RULE2_LONG_VERDICT
    syms = {"SPY": _mm_symbol("SPY", grade="A", bias="BEAR")}
    mm = _market_map(syms)
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run(), market_map=mm)
    assert 'id="card-SPY"' in html
    assert RULE2_LONG_VERDICT not in html


def test_prd168_rule2_verdict_present_when_no_high_grade_card() -> None:
    # No high-grade card (only C grade reaches the board); the RULE2 idle verdict
    # must still render — the gate only fires when a high-grade card is present.
    from cuttingboard.delivery.dashboard_integrator import RULE2_LONG_VERDICT
    syms = {"GLD": _mm_symbol("GLD", grade="C", bias="BEAR")}
    mm = _market_map(syms)
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run(), market_map=mm)
    assert RULE2_LONG_VERDICT in html


def test_prd168_gate_targets_only_rule2_verdicts() -> None:
    # D2: the suppression set is exactly the two RULE2 idle verdicts; RULE3_MIXED
    # (a real conflict signal) is never in the gated set. Guards against a future
    # edit widening the gate. RULE3 render behavior itself is covered by
    # tests/test_dash_macro.py.
    import inspect

    from cuttingboard.delivery import dashboard_renderer as _dr
    from cuttingboard.delivery.dashboard_integrator import RULE3_MIXED_VERDICT
    src = inspect.getsource(_dr.render_dashboard_html)
    assert "_PRD168_GATED_VERDICTS" in src
    assert RULE3_MIXED_VERDICT not in _dr._PRD168_GATED_VERDICTS
    assert _dr.RULE2_LONG_VERDICT in _dr._PRD168_GATED_VERDICTS
    assert _dr.RULE2_SHORT_VERDICT in _dr._PRD168_GATED_VERDICTS


# ---------------------------------------------------------------------------
# PRD-055 PATCH — tier counts
# ---------------------------------------------------------------------------

def test_tier_count_in_header() -> None:
    syms = {
        "SPY": _mm_symbol("SPY", grade="A+"),
        "QQQ": _mm_symbol("QQQ", grade="A+"),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "A+ — ACTIONABLE (2)" in html


def test_tier_count_single() -> None:
    syms = {"GLD": _mm_symbol("GLD", grade="B")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "B — DEVELOPING (1)" in html


# ---------------------------------------------------------------------------
# PRD-057 — Lifecycle badge and detail helpers (local)
# ---------------------------------------------------------------------------

def _lifecycle(
    grade_transition: str = "UPGRADED",
    previous_grade: str | None = "B",
    current_grade: str = "A",
    previous_setup_state: str | None = "DEVELOPING",
    current_setup_state: str | None = "ACTIONABLE",
) -> dict:
    return {
        "previous_grade":          previous_grade,
        "current_grade":           current_grade,
        "grade_transition":        grade_transition,
        "previous_setup_state":    previous_setup_state,
        "current_setup_state":     current_setup_state,
        "setup_state_transition":  "CHANGED",
        "is_new":                  grade_transition == "NEW",
        "is_removed":              False,
    }


def _sym_with_lc(
    symbol: str,
    grade: str,
    grade_transition: str = "UPGRADED",
    previous_grade: str | None = "B",
    setup_state: str | None = "ACTIONABLE",
    previous_setup_state: str | None = "DEVELOPING",
) -> dict:
    sym = _mm_symbol(symbol, grade=grade, setup_state=setup_state)
    sym["lifecycle"] = _lifecycle(
        grade_transition=grade_transition,
        previous_grade=previous_grade,
        current_grade=grade,
        previous_setup_state=previous_setup_state,
        current_setup_state=setup_state,
    )
    return sym


# ---------------------------------------------------------------------------
# PRD-057 — R1: Lifecycle badge
# ---------------------------------------------------------------------------

def test_lifecycle_badge_upgraded() -> None:
    syms = {"SPY": _sym_with_lc("SPY", grade="A", grade_transition="UPGRADED")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = html.split('id="card-SPY"', 1)[1]
    assert 'class="lifecycle-badge lifecycle-upgraded"' in card
    assert "UPGRADED" in card


def test_lifecycle_badge_downgraded() -> None:
    syms = {"SPY": _sym_with_lc("SPY", grade="C", grade_transition="DOWNGRADED", previous_grade="A")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = html.split('id="card-SPY"', 1)[1]
    assert 'class="lifecycle-badge lifecycle-downgraded"' in card


def test_lifecycle_badge_new() -> None:
    syms = {"SPY": _sym_with_lc("SPY", grade="B", grade_transition="NEW", previous_grade=None)}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = html.split('id="card-SPY"', 1)[1]
    assert 'class="lifecycle-badge lifecycle-new"' in card


def test_lifecycle_badge_unknown() -> None:
    syms = {"SPY": _sym_with_lc("SPY", grade="B", grade_transition="UNKNOWN")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = html.split('id="card-SPY"', 1)[1]
    assert 'class="lifecycle-badge lifecycle-unknown"' in card


def test_lifecycle_badge_unchanged_suppressed() -> None:
    syms = {"SPY": _sym_with_lc("SPY", grade="B", grade_transition="UNCHANGED")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = html.split('id="card-SPY"', 1)[1]
    assert "lifecycle-badge" not in card


def test_lifecycle_badge_absent_when_no_lifecycle() -> None:
    syms = {"SPY": _mm_symbol("SPY", grade="A")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = html.split('id="card-SPY"', 1)[1]
    assert "lifecycle-badge" not in card


# ---------------------------------------------------------------------------
# PRD-057 — R3: Lifecycle detail row
# ---------------------------------------------------------------------------

def test_lifecycle_detail_rendered_for_a_grade() -> None:
    syms = {"SPY": _sym_with_lc("SPY", grade="A", grade_transition="UPGRADED")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = html.split('id="card-SPY"', 1)[1]
    assert 'class="lifecycle-detail"' in card
    assert "LIFECYCLE:" in card


def test_lifecycle_detail_rendered_for_b_grade() -> None:
    syms = {"GLD": _sym_with_lc("GLD", grade="B", grade_transition="UNCHANGED")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = html.split('id="card-GLD"', 1)[1]
    assert 'class="lifecycle-detail"' in card


def test_lifecycle_detail_not_rendered_when_absent() -> None:
    syms = {"SPY": _mm_symbol("SPY", grade="A+")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    assert 'class="lifecycle-detail"' not in html


def test_lifecycle_detail_null_prev_renders_dash() -> None:
    sym = _mm_symbol("SPY", grade="A")
    sym["lifecycle"] = _lifecycle(
        grade_transition="NEW",
        previous_grade=None,
        previous_setup_state=None,
        current_grade="A",
        current_setup_state="ACTIONABLE",
    )
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map({"SPY": sym}))
    card = html.split('id="card-SPY"', 1)[1]
    assert "LIFECYCLE: — →" in card


def test_lifecycle_detail_after_verdict() -> None:
    # PRD-249: a real lifecycle transition renders after the IF NOW verdict
    # (the standalone STATE line it used to precede is gone).
    syms = {"SPY": _sym_with_lc("SPY", grade="A+", grade_transition="UPGRADED", setup_state="ACTIONABLE")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = html.split('id="card-SPY"', 1)[1]
    assert card.index("IF NOW") < card.index('class="lifecycle-detail"')


def test_lifecycle_detail_suppressed_on_noop_transition() -> None:
    # PRD-249 R3: a no-op transition (grade AND setup_state both unchanged, e.g.
    # "B → B | DEVELOPING → DEVELOPING") is not rendered.
    syms = {"SPY": _sym_with_lc("SPY", grade="B", grade_transition="UNCHANGED",
                                previous_grade="B", setup_state="DEVELOPING",
                                previous_setup_state="DEVELOPING")}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = html.split('id="card-SPY"', 1)[1]
    assert 'class="lifecycle-detail"' not in card


# ---------------------------------------------------------------------------
# PRD-057 — R4: Removed symbols section
# ---------------------------------------------------------------------------

def test_removed_symbols_section_rendered() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    mm["removed_symbols"] = [{"symbol": "GLD", "previous_grade": "B", "grade_transition": "REMOVED", "is_removed": True}]
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'class="removed-symbols"' in html
    assert "GLD" in html
    assert "removed (prev: B)" in html


def test_removed_symbols_section_absent_when_empty() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    mm["removed_symbols"] = []
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'class="removed-symbols"' not in html


def test_removed_symbols_section_absent_when_key_missing() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'class="removed-symbols"' not in html


def test_removed_symbols_not_in_tier_group() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    mm["removed_symbols"] = [{"symbol": "GLD", "previous_grade": "B", "grade_transition": "REMOVED", "is_removed": True}]
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="card-GLD"' not in html


def test_removed_symbols_values_escaped() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    mm["removed_symbols"] = [{"symbol": "<XSS>", "previous_grade": "<b>", "grade_transition": "REMOVED", "is_removed": True}]
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "<XSS>" not in html
    assert "&lt;XSS&gt;" in html


# ---------------------------------------------------------------------------
# R2 / R3 / R4 — Alert Watchlist Section
# ---------------------------------------------------------------------------

def test_alert_watchlist_absent_when_no_candidates() -> None:
    """No alert-watchlist section when alert_candidates is not provided."""
    html = render_dashboard_html(_payload(), _run())
    assert 'id="alert-watchlist"' not in html


def test_alert_watchlist_absent_when_empty_candidates() -> None:
    """No alert-watchlist section when alert_candidates is an empty list."""
    html = render_dashboard_html(_payload(), _run(), alert_candidates=[])
    assert 'id="alert-watchlist"' not in html


def test_alert_watchlist_present_when_candidates() -> None:
    """Alert Watchlist section present when alert_candidates provided."""
    from tests.dash_helpers import _trade_decision
    gated = [_trade_decision("META", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION")]
    html = render_dashboard_html(_payload(), _run(), alert_candidates=gated)
    assert 'id="alert-watchlist"' in html


def test_alert_watchlist_shows_symbol_and_direction() -> None:
    """Alert Watchlist section shows symbol and direction for each candidate."""
    from tests.dash_helpers import _trade_decision
    gated = [
        _trade_decision("META", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION"),
        _trade_decision("XLE", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION"),
    ]
    html = render_dashboard_html(_payload(), _run(), alert_candidates=gated)
    block = _top_block(html, "alert-watchlist")
    assert "META" in block
    assert "LONG" in block
    assert "XLE" in block


def test_candidate_board_positioned_before_alert_watchlist() -> None:
    """PRD-315: candidate-board immediately precedes alert-watchlist in DOM.

    Supersedes the historical Alert-before-Candidate pin (packet section 5):
    Candidate is lifted above Alert and is its immediate top-level predecessor.
    Reverting Candidate to its old seam breaks the adjacency assertion below.
    """
    from tests.dash_helpers import _trade_decision
    gated = [_trade_decision("NVDA", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION")]
    html = render_dashboard_html(_payload(), _run(), alert_candidates=gated)
    ids = _top_ids(html)
    assert ids.index("candidate-board") < ids.index("alert-watchlist")
    assert ids.index("alert-watchlist") == ids.index("candidate-board") + 1


# ---------------------------------------------------------------------------
# R5 — Candidate Board Rename
# ---------------------------------------------------------------------------

def test_candidate_board_renamed_to_market_map() -> None:
    """PRD-330 R6 (supersedes PRD-102 R5): the board heading is SETUPS with the permission clause."""
    html = render_dashboard_html(_payload(), _run())
    assert '<h3>SETUPS <span class="scope-note">· screening grades, not permission</span></h3>' in html
    assert "Market Map / Developing Setups · screening" not in html
    # Old label must not appear in the board section heading
    board = html.split('id="candidate-board"', 1)[1].split('</div>', 1)[0]
    assert "Candidate Board" not in board


# ---------------------------------------------------------------------------
# PRD-321 — setup chart consumer: bars loading, age guard, disclosure ordering,
# and the authority semantics carried into the chart AND the compact ladder.
# ---------------------------------------------------------------------------

import json  # noqa: E402
import re  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402

from cuttingboard.delivery import dashboard_renderer as _dr  # noqa: E402

_NOW = datetime(2026, 8, 28, 14, 0, tzinfo=timezone.utc)

_LADDER_ROW = re.compile(
    r'<div class="lvl-row (?P<cls>[^"]+)">'
    r'<span class="lvl-name">(?P<name>[^<]*)</span>'
    r'<span class="lvl-px">(?P<px>[^<]*)</span>'
    r'<span class="lvl-pct">(?P<pct>[^<]*)</span></div>'
)


def _render(mm: dict, snapshot: dict | None = None, **kwargs) -> str:
    kwargs.setdefault("now", _NOW)
    return render_dashboard_html(
        _payload(), kwargs.pop("run", _run(outcome="TRADE")),
        market_map=mm, price_bars_snapshot=snapshot, **kwargs,
    )


def _pc_card(html: str, sym: str = "SPY") -> str:
    return html.split(f'id="card-{sym}"', 1)[1].split("</div>\n</div>", 1)[0]


def _ladder_rows(fragment: str) -> dict[str, tuple[str, str]]:
    return {m["name"]: (m["px"], m["pct"]) for m in _LADDER_ROW.finditer(fragment)}


def _charts_by_details_depth(html: str) -> list[int]:
    """Depth of every `.setup-chart` relative to enclosing `<details>` elements."""
    depths: list[int] = []
    depth = 0
    for token in re.finditer(r"<details\b|</details>|<div class=\"setup-chart\"", html):
        text = token.group(0)
        if text.startswith("<details"):
            depth += 1
        elif text == "</details>":
            depth -= 1
        else:
            depths.append(depth)
    return depths


# --- R2: loading, provenance caption, and the 5-calendar-day UTC age guard ---

def test_prd321_chart_renders_from_the_snapshot_with_an_as_of_caption() -> None:
    html = _render(_market_map({"SPY": _chartable()}), _bars_snapshot())
    card = _pc_card(html)
    assert 'class="setup-chart"' in card
    assert "bars through 2026-08-27 · yfinance 1d" in card
    # Source-bar fidelity: one candle per snapshot bar, direction from the input.
    assert card.count('class="candle-body"') == len(_PC_BARS)
    assert card.count('class="candle-wick"') == len(_PC_BARS)


def test_prd321_age_guard_admits_exactly_five_calendar_days() -> None:
    # R2 FAIL line, boundary. Mutation: change `> 5` to `>= 5` -> the 5-day
    # case loses its chart; change it to `> 6` -> the 6-day case renders one.
    for delta, expect_chart in ((5, True), (6, False)):
        as_of = (_NOW.date() - timedelta(days=delta)).isoformat()
        html = _render(_market_map({"SPY": _chartable()}), _bars_snapshot(as_of=as_of))
        card = _pc_card(html)
        assert ('class="setup-chart"' in card) is expect_chart, (delta, expect_chart)
        assert (f"bars through {as_of}" in card) is expect_chart
        # Either way the compact ladder is present with its exact levels.
        assert 'class="lvl-ladder' in card


def test_prd321_age_guard_uses_utc_calendar_days_not_elapsed_hours() -> None:
    # 5 days + 23h of wall-clock elapsed time is still 5 CALENDAR days.
    as_of = "2026-08-23"
    late = datetime(2026, 8, 28, 23, 30, tzinfo=timezone.utc)
    html = _render(_market_map({"SPY": _chartable()}), _bars_snapshot(as_of=as_of), now=late)
    assert 'class="setup-chart"' in _pc_card(html)


def test_prd321_now_falls_back_to_utcnow_when_the_caller_passes_none(monkeypatch) -> None:
    monkeypatch.setattr(_dr, "_utcnow", lambda: _NOW)
    html = render_dashboard_html(
        _payload(), _run(outcome="TRADE"), market_map=_market_map({"SPY": _chartable()}),
        price_bars_snapshot=_bars_snapshot(),
    )
    assert 'class="setup-chart"' in _pc_card(html)


@pytest.mark.parametrize("snapshot", [
    None,
    {},
    {"symbols": None},
    {"symbols": {"SPY": {"as_of": "2026-08-27"}}},          # no bars
    {"symbols": {"SPY": {"as_of": "not-a-date", "bars": _PC_BARS}}},
    {"symbols": {"SPY": {"as_of": "2026-08-27", "bars": []}}},
    {"symbols": {"QQQ": {"as_of": "2026-08-27", "bars": _PC_BARS}}},  # other symbol
])
def test_prd321_unusable_snapshot_changes_nothing_outside_the_chart_region(snapshot) -> None:
    # R2 FAIL line: a missing/corrupt snapshot must not raise and must not alter
    # any non-chart output. The baseline is the same render with no snapshot.
    mm = _market_map({"SPY": _chartable()})
    baseline = _render(mm, None)
    degraded = _render(mm, snapshot)
    assert degraded == baseline
    assert 'class="setup-chart"' not in degraded
    assert "bars through" not in degraded
    assert 'class="lvl-ladder' in degraded


def test_prd321_loader_never_raises_on_a_broken_artifact(tmp_path) -> None:
    # R2: the reader degrades on missing / non-JSON / wrong-shape files.
    missing = tmp_path / "absent.json"
    assert _dr._load_price_bars_snapshot(missing) is None
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert _dr._load_price_bars_snapshot(broken) is None
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"symbols": []}), encoding="utf-8")
    assert _dr._load_price_bars_snapshot(wrong) is None
    good = tmp_path / "good.json"
    good.write_text(json.dumps(_bars_snapshot()), encoding="utf-8")
    assert _dr._load_price_bars_snapshot(good)["symbols"]["SPY"]["bars"] == _PC_BARS


# --- R3: one full chart, everything else behind disclosure -------------------

def test_prd321_only_the_top_setup_gets_a_chart_outside_disclosure() -> None:
    # R3 FAIL line (depth-aware). Mutation: pass `chart_slot_available=True` for
    # every card -> three undisclosed charts and this goes red.
    syms = ("AAA", "BBB", "CCC")
    mm = _market_map({s: _chartable(s) for s in syms})
    html = _render(mm, _bars_snapshot(symbols=syms))
    depths = _charts_by_details_depth(html)
    assert len(depths) == 3
    assert depths.count(0) == 1                 # exactly one full-width chart
    assert sorted(depths)[1:] == [1, 1]         # the rest behind disclosure
    # The undisclosed chart belongs to the highest-priority visible setup.
    assert 'class="setup-chart"' in _pc_card(html, "AAA")
    assert '<details class="chart-detail">' in _pc_card(html, "BBB")
    assert '<details class="chart-detail">' in _pc_card(html, "CCC")
    assert '<details class="chart-detail">' not in _pc_card(html, "AAA")


def test_prd321_no_chart_sits_outside_disclosure_when_not_permitted() -> None:
    # R3 FAIL clause as SUPERSEDED IN PART by PRD-326 A1: under a non-permitted
    # render the single canonical primary-slot chart sits outside disclosure
    # (depth 0, observational); every other chart stays behind the orthogonal
    # `level-detail` wrapper AND its own `chart-detail` (depth 2).
    syms = ("AAA", "BBB")
    mm = _market_map({s: _chartable(s) for s in syms})
    html = _render(mm, _bars_snapshot(symbols=syms), run=_run(outcome="NO_TRADE"))
    assert _charts_by_details_depth(html) == [0, 2]
    assert '<details class="level-detail">' in _pc_card(html, "AAA")
    assert '<details class="chart-detail">' in _pc_card(html, "BBB")
    assert 'class="candidate-card grade-aplus candidate-observation"' in html


def test_prd321_permitted_render_drops_the_level_detail_wrapper_only() -> None:
    mm = _market_map({"SPY": _chartable()})
    permitted = _pc_card(_render(mm, _bars_snapshot(), run=_run(outcome="TRADE")))
    assert '<details class="level-detail">' not in permitted
    assert 'class="setup-chart"' in permitted
    assert 'class="lvl-ladder' in permitted


def test_prd321_chart_and_ladder_render_together_never_the_old_ladder() -> None:
    # R4 FAIL line: chart + compact ladder, and no pre-PRD-321 markup anywhere.
    card = _pc_card(_render(_market_map({"SPY": _chartable()}), _bars_snapshot()))
    assert card.index('class="setup-chart"') < card.index('class="lvl-ladder')
    assert "lvl-diagram" not in card
    assert 'x2="160"' not in card


# --- R3: authority semantics on the chart AND the compact ladder -------------

_LOCK_PERMISSION = "No new trades permitted — operator cannot monitor."


def test_prd321_locked_render_neutralizes_the_chart_and_the_ladder() -> None:
    # R3 FAIL line. Mutation: stop threading `operator_locked` into either the
    # chart call or the ladder call -> action wording/colours reappear.
    mm = _market_map({"SPY": _chartable()})
    card = _pc_card(_render(
        mm, _bars_snapshot(),
        run=_run(outcome="NO_TRADE", permission=_LOCK_PERMISSION),
        contract_entry_map={"SPY": 102.5}, contract_stop_map={"SPY": 99.8},
    ))
    assert 'class="setup-chart"' in card
    chart = card.split('class="setup-chart"', 1)[1].split("</svg>", 1)[0]
    assert "LEVEL" in chart and "INVALIDATION" in chart
    assert not re.search(r">ENTRY [+-]", chart) and not re.search(r">STOP [+-]", chart)
    assert "#e0a552" not in chart and "#e05252" not in chart
    assert "#6b7280" in chart
    rows = _ladder_rows(card)
    assert rows["LEVEL"] == ("102.50", "+0.7%")
    assert rows["INVALIDATION"] == ("99.80", "-2.0%")
    assert "ENTRY" not in rows and "STOP" not in rows
    assert 'class="lvl-riskband lvl-lockrisk"' in card


def test_prd321_permitted_render_keeps_the_action_palette() -> None:
    # Non-vacuity anchor for the lock test above.
    mm = _market_map({"SPY": _chartable()})
    card = _pc_card(_render(
        mm, _bars_snapshot(), run=_run(outcome="TRADE"),
        contract_entry_map={"SPY": 102.5}, contract_stop_map={"SPY": 99.8},
    ))
    chart = card.split('class="setup-chart"', 1)[1].split("</svg>", 1)[0]
    assert re.search(r">ENTRY [+-]", chart) and re.search(r">STOP [+-]", chart)
    assert "#e0a552" in chart and "#e05252" in chart
    rows = _ladder_rows(card)
    assert rows["ENTRY"] == ("102.50", "+0.7%") and rows["STOP"] == ("99.80", "-2.0%")
    assert 'class="lvl-riskband lvl-inrisk"' in card


def test_prd321_halted_run_still_neutralizes_the_chart() -> None:
    mm = _market_map({"SPY": _chartable()})
    card = _pc_card(_render(
        mm, _bars_snapshot(),
        run=_run(system_halted=True, permission=_LOCK_PERMISSION, outcome="NO_TRADE"),
        contract_entry_map={"SPY": 102.5}, contract_stop_map={"SPY": 99.8},
    ))
    chart = card.split('class="setup-chart"', 1)[1].split("</svg>", 1)[0]
    assert "#e0a552" not in chart and "#e05252" not in chart


@pytest.mark.parametrize("bad_price", [0, -1.0, float("nan"), float("inf")])
def test_prd321_invalid_current_price_renders_no_chart_and_no_ladder(bad_price) -> None:
    # R3 FAIL line (PRD-226): an invalid anchor suppresses BOTH surfaces even
    # when usable bars exist for the symbol.
    entry = _chartable()
    entry["current_price"] = bad_price
    html = _render(_market_map({"SPY": entry}), _bars_snapshot())   # must not raise
    assert 'class="setup-chart"' not in html
    assert 'class="lvl-ladder' not in html
    assert "bars through" not in html
    # PRD-158 translation 12 / PRD-226: suppressed outright, not replaced by a
    # placeholder. Mutation: drop `now_valid` from the caller gate -> the
    # ladder's belt-and-suspenders guard emits "Chart unavailable" and this
    # goes red.
    assert "Chart unavailable" not in html
    assert 'class="lvl-unavail"' not in html
    assert 'id="card-SPY"' in html


def test_prd321_no_bars_fallback_keeps_the_pct_and_entry_stop_facts() -> None:
    # R4 FAIL line: the fallback ladder loses no PRD-221/222/223 fact.
    mm = _market_map({"SPY": _chartable()})
    card = _pc_card(_render(
        mm, None, contract_entry_map={"SPY": 102.5}, contract_stop_map={"SPY": 99.8},
    ))
    assert 'class="setup-chart"' not in card
    rows = _ladder_rows(card)
    assert rows["NOW"] == ("101.80", "")
    assert rows["ENTRY"] == ("102.50", "+0.7%")
    assert rows["STOP"] == ("99.80", "-2.0%")
    assert rows["VWAP"] == ("101.50", "-0.3%")
    assert rows["0.5"] == ("100.70", "-1.1%")
    assert 'class="lvl-riskband lvl-inrisk"' in card


def test_prd321_low_grade_cards_also_degrade_to_the_compact_ladder() -> None:
    entry = _chartable("XYZ", grade="C")
    html = _render(_market_map({"XYZ": entry}), None)
    card = _pc_card(html, "XYZ")
    assert 'class="lvl-ladder' in card
    assert 'class="setup-chart"' not in card


# --- PRD-326 (D1): PRIMARY CHART VISIBILITY IS OBSERVATIONAL AND DOES NOT GRANT
# OR IMPLY TRADE PERMISSION. The "pre-D1 oracle" (R7) renders the same inputs with
# `select_primary_card_symbol` returning None: no card takes the chart slot, so every
# non-primary card and fallback surface keeps its pre-D1 bytes by construction.

_D1_CONTRACTS = {"contract_entry_map": {"AAA": 102.5, "BBB": 102.5},
                 "contract_stop_map": {"AAA": 99.8, "BBB": 99.8}}
_D1_HALT_UNLOCKED = dict(system_halted=True, outcome="NO_TRADE")  # non-lock permission
_D1_ZONES = ("verdict-zone", "staleness-banner", "system-state", "tape-zone", "today-zone")
_D1_DIRECTIVE = re.compile(
    r'<div class="label">(?:IF NOW|PLAY|IN →|OUT →|LEVEL|INVALIDATION)</div>'
    r'<div class="[^"]*">[^<]*</div>'
)


def _d1_map() -> dict:
    return _market_map({"AAA": _chartable("AAA", "A+"), "BBB": _chartable("BBB", "A")})


def _d1_render(run: dict, mm: dict | None = None, *, bars: bool = True, **kwargs) -> str:
    mm = mm if mm is not None else _d1_map()
    snap = _bars_snapshot(symbols=tuple(mm["symbols"])) if bars else None
    return _render(mm, snap, run=run, **kwargs)


def _d1_oracle(run: dict, mm: dict | None = None, **kwargs) -> str:
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(_dr, "select_primary_card_symbol", lambda *a, **k: None)
        return _d1_render(run, mm, **kwargs)


def _d1_card(html: str, sym: str) -> str:
    """Exactly one card: from its id to the card's own column-zero close tag."""
    return html.split(f'id="card-{sym}"', 1)[1].split("\n</div>\n", 1)[0]


def _d1_chart(card: str) -> str:
    return card.split('class="setup-chart"', 1)[1].split("</svg>", 1)[0]


def _assert_neutral(chart: str) -> None:
    assert "LEVEL" in chart and "INVALIDATION" in chart
    assert not re.search(r">ENTRY ", chart) and not re.search(r">STOP ", chart)
    assert "#e0a552" not in chart and "#e05252" not in chart
    assert "#6b7280" in chart


# --- R1: undisclosed primary chart in every decision state -------------------

def test_prd326_primary_chart_undisclosed_when_not_permitted() -> None:
    # R1 FAIL line. M1 (wrapper opened above the chart), M3 (`disclosed=True`)
    # and M8 (secondary disclosure keyed on permission) all go red here.
    html = _d1_render(_run(outcome="NO_TRADE"))
    assert 'decision-state sys-up">STAY FLAT<' in html
    card = _d1_card(html, "AAA")
    assert 'class="setup-chart"' in card
    assert "<details" not in card.split('class="setup-chart"', 1)[0]
    assert _charts_by_details_depth(html) == [0, 2]
    assert '<details class="chart-detail">' not in card


def test_prd326_primary_chart_precedes_level_detail() -> None:
    # R1/R2: chart block, THEN the LEVEL MAP wrapper, THEN the ladder inside it
    # (M2 emits the chart after the ladder inside the wrapper -> red).
    card = _d1_card(_d1_render(_run(outcome="NO_TRADE")), "AAA")
    i_chart = card.index('class="setup-chart"')
    i_caption = card.index('class="chart-caption"')
    i_wrap = card.index('<details class="level-detail"><summary>LEVEL MAP ▶</summary>')
    i_ladder = card.index('class="lvl-ladder')
    assert i_chart < i_caption < i_wrap < i_ladder
    assert "</details>" not in card[i_chart:i_wrap]
    assert card.rstrip().endswith("</details>")   # the ladder closes inside the wrapper


def test_prd326_lock_render_primary_chart_undisclosed() -> None:
    html = _d1_render(_run(outcome="NO_TRADE", permission=_LOCK_PERMISSION))
    assert ">OBSERVE ONLY<" in html
    card = _d1_card(html, "AAA")
    assert "<details" not in card.split('class="setup-chart"', 1)[0]
    assert '<details class="level-detail">' in card
    assert _charts_by_details_depth(html) == [0, 2]


def test_prd326_c_grade_primary_tier_opens() -> None:
    # D1-Q1 = OPTION A: the low tier holding the canonical primary defaults OPEN;
    # its secondary keeps `chart-detail` closed; a C tier without the primary
    # keeps today's collapsed wrapper (M15 drops the attribute -> red).
    mm = _market_map({"CCC": _chartable("CCC", "C"), "DDD": _chartable("DDD", "C")})
    html = _d1_render(_run(outcome="NO_TRADE"), mm)
    assert '<details open class="tier-group" id="tier-c">' in html
    card = _d1_card(html, "CCC")
    assert 'class="setup-chart"' in card
    assert "<details" not in card.split('class="setup-chart"', 1)[0]
    assert _charts_by_details_depth(html) == [1, 3]      # open tier; then tier+level+chart
    assert '<details class="chart-detail">' in _d1_card(html, "DDD")
    assert "<details open" not in _d1_card(html, "DDD")
    mixed = _market_map({"AAA": _chartable("AAA", "A+"), "CCC": _chartable("CCC", "C")})
    html2 = _d1_render(_run(outcome="NO_TRADE"), mixed)
    assert '<details class="tier-group" id="tier-c">' in html2
    assert '<details open class="tier-group"' not in html2  # PRD-329 T7: nested `open` is now S1's


# --- R2/R3: everything else keeps today's bytes; the exposed chart is neutral --

def test_prd326_secondary_and_ladder_byte_identical_when_not_permitted() -> None:
    # M7 (ladder keyed on chart_neutral) and M10 (predicate without the
    # chart_slot_available conjunct) both change bytes the oracle pins.
    run = _run(outcome="NO_TRADE")
    html, oracle = _d1_render(run, **_D1_CONTRACTS), _d1_oracle(run, **_D1_CONTRACTS)
    assert 'class="setup-chart"' in _d1_card(html, "AAA")
    assert '<details class="chart-detail">' in _d1_card(oracle, "AAA")  # oracle: no slot holder
    assert _d1_card(html, "BBB") == _d1_card(oracle, "BBB")
    assert "#e0a552" in _d1_chart(_d1_card(html, "BBB"))            # secondary keeps its palette
    def ladder(h: str) -> str:
        return _d1_card(h, "AAA").split('class="lvl-ladder', 1)[1]
    assert ladder(html) == ladder(oracle)
    assert "ENTRY" in _ladder_rows(_d1_card(html, "AAA"))            # ladder keyed on lock alone


def test_prd326_non_permitted_primary_chart_is_neutral() -> None:
    # R3 (M4): NO_TRADE, unlocked, contract prices present -> the newly exposed
    # primary chart carries the PRD-304/321 lock presentation, nothing else.
    card = _d1_card(_d1_render(_run(outcome="NO_TRADE"), **_D1_CONTRACTS), "AAA")
    _assert_neutral(_d1_chart(card))


def test_prd326_non_permitted_intraday_primary_chart_is_neutral(monkeypatch, tmp_path) -> None:
    # R3 (M5): the admitted intraday session takes the slot and is neutral too.
    path = tmp_path / "intraday_bars_snapshot.json"
    path.write_text(json.dumps(_intraday_snapshot(_NOW, primary="AAA")), encoding="utf-8")
    monkeypatch.setattr(_dr, "_INTRADAY_BARS_SNAPSHOT_PATH", path)
    card = _d1_card(_d1_render(_run(outcome="NO_TRADE"), **_D1_CONTRACTS), "AAA")
    assert "completed through 09:40 ET" in card
    _assert_neutral(_d1_chart(card))


def test_prd326_unlocked_halt_primary_chart_is_neutral() -> None:
    # R3 (M11): system_halted with a NON-lock permission is not permitted, so the
    # exposed chart is neutral while the unlocked directives stay (F4 not masked).
    html = _d1_render(_run(**_D1_HALT_UNLOCKED), **_D1_CONTRACTS)
    assert 'decision-state sys-halt">HALT<' in html
    assert ">OBSERVE ONLY<" not in html
    card = _d1_card(html, "AAA")
    assert "<details" not in card.split('class="setup-chart"', 1)[0]
    _assert_neutral(_d1_chart(card))
    assert '<div class="label">IF NOW</div>' in card


def test_prd326_directives_stay_keyed_on_lock() -> None:
    # R2/R3 (M6): IF NOW, PLAY, the IN/OUT couplet and its actionable accent are
    # keyed on the operator lock alone, even while the exposed chart is neutral.
    mm = _d1_map()
    mm["symbols"]["AAA"]["preferred_trade_structure"] = "BULL_CALL_SPREAD"
    run = _run(outcome="NO_TRADE")
    card = _d1_card(_d1_render(run, mm, **_D1_CONTRACTS), "AAA")
    oracle = _d1_card(_d1_oracle(run, mm, **_D1_CONTRACTS), "AAA")
    assert '<div class="label">IF NOW</div>' in card
    assert '<div class="label">PLAY</div>' in card
    assert '<div class="label">IN →</div>' in card and '<div class="label">OUT →</div>' in card
    assert "value-actionable" in card
    assert _D1_DIRECTIVE.findall(card) == _D1_DIRECTIVE.findall(oracle)
    assert "#e0a552" not in _d1_chart(card)


# --- R4: no primary / stale board -> unchanged, no placeholder ----------------

def test_prd326_no_primary_renders_no_placeholder(monkeypatch) -> None:
    run = _run(outcome="NO_TRADE")
    html = _d1_render(run, bars=False, **_D1_CONTRACTS)
    assert 'class="setup-chart"' not in html and "bars through" not in html
    assert 'class="lvl-ladder' in _d1_card(html, "AAA")             # fallback ladder
    assert 'class="lvl-riskband lvl-lockrisk"' not in html                # no lock palette
    # M9: force the slot open with nothing honest to draw -> still no placeholder.
    monkeypatch.setattr(_dr, "select_primary_card_symbol", lambda *a, **k: "AAA")
    assert _d1_render(run, bars=False, **_D1_CONTRACTS) == html


def test_prd326_stale_map_with_bars_renders_no_chart() -> None:
    mm = _d1_map()
    mm["generated_at"] = "2026-04-28T11:00:00Z"   # an hour behind the run: STALE
    run = _run(outcome="NO_TRADE")
    with_bars = _d1_render(run, mm, **_D1_CONTRACTS)
    assert "STALE MARKET MAP" in with_bars
    assert 'class="setup-chart"' not in with_bars and 'id="card-AAA"' not in with_bars
    assert with_bars == _d1_render(run, mm, bars=False, **_D1_CONTRACTS)


# --- R5: verdict, permission, and staleness authority are chart-invariant -----

@pytest.mark.parametrize("run", [
    _run(outcome="NO_TRADE"),
    _run(outcome="NO_TRADE", permission=_LOCK_PERMISSION),
    _run(outcome="TRADE"),
    _run(**_D1_HALT_UNLOCKED),
], ids=["stay_flat", "locked", "permitted", "halt_unlocked"])
def test_prd326_verdict_zones_are_chart_invariant(run) -> None:
    # M12 (caption text appended into #system-state) goes red here.
    with_bars = _d1_render(run, **_D1_CONTRACTS)
    without = _d1_render(run, bars=False, **_D1_CONTRACTS)
    assert 'class="setup-chart"' in with_bars and 'class="setup-chart"' not in without
    for zone in _D1_ZONES:
        assert _top_block(with_bars, zone) == _top_block(without, zone), zone
    for pattern in (
        r'<div class="idle-summary candidate-scope">[^<]*</div>',
        r'<(?:div|summary) class="tier-header">[^<]*</(?:div|summary)>',
        r'<div class="candidate-card [^"]*" id="card-[A-Z]+">',
        r'<div class="decision-state [^"]*">[^<]*</div>',
    ):
        assert re.findall(pattern, with_bars) == re.findall(pattern, without), pattern


# --- PRD-329 (D3) S1: CLOSED-C-TIER ONE-CLICK EVIDENCE. Inside a `tier-group`
# `<details>` emitted WITHOUT `open`, `level-detail` and `chart-detail` carry
# `open`, so one tier tap exposes card + LEVEL MAP + CHART; every A+/A/B card and
# every card inside an OPEN C tier keeps today's bytes (R1/R2); no JS (R3).

_S1_LOCK_HALT = dict(system_halted=True, outcome="NO_TRADE", permission=_LOCK_PERMISSION)
_S1_STATES = {"stay_flat": dict(outcome="NO_TRADE"),
              "locked": dict(outcome="NO_TRADE", permission=_LOCK_PERMISSION),
              "halt_unlocked": _D1_HALT_UNLOCKED, "halt_locked": _S1_LOCK_HALT}
_S1_LEVEL_OPEN = '<details open class="level-detail"><summary>LEVEL MAP ▶</summary>'
_S1_CHART_OPEN = '<details open class="chart-detail"><summary>CHART ▶</summary>'


def _s1_mixed() -> dict:  # AAA (A+) is the canonical primary, so tier-c is CLOSED
    return _market_map({"AAA": _chartable("AAA", "A+"), "CCC": _chartable("CCC", "C")})


@pytest.mark.parametrize("state", sorted(_S1_STATES))
def test_prd329_closed_c_tier_evidence_opens_with_the_tier(state) -> None:
    # T1 (R1): non-permitted states keep the `level-detail` wrapper; both nested
    # wrappers carry `open` while the tier itself stays closed on load.
    html = _d1_render(_run(**_S1_STATES[state]), _s1_mixed())
    assert '<details class="tier-group" id="tier-c">' in html
    card = _d1_card(html, "CCC")
    assert _S1_LEVEL_OPEN in card and _S1_CHART_OPEN in card
    assert '<details class="level-detail">' not in card
    assert '<details class="chart-detail">' not in card
    assert _charts_by_details_depth(html) == [0, 3]      # primary undisclosed; tier+level+chart
    assert "<details open" not in _d1_card(html, "AAA")  # R2: A+ card untouched


def test_prd329_closed_c_tier_permitted_chart_opens_without_level_wrapper() -> None:
    # T2 (R1): TRADE PERMITTED emits no `level-detail`; `chart-detail` alone carries `open`.
    html = _d1_render(_run(outcome="TRADE"), _s1_mixed())
    assert ">TRADE PERMITTED<" in html
    assert '<details class="tier-group" id="tier-c">' in html
    card = _d1_card(html, "CCC")
    assert "level-detail" not in card and _S1_CHART_OPEN in card
    assert _charts_by_details_depth(html) == [0, 2]


def test_prd329_open_tiers_and_high_grades_keep_closed_wrappers() -> None:
    # T3-T6 (R2/R3), regression guards: open C tier siblings, A/B cards and
    # `card-detail` never carry `open`; exactly the one pre-existing `<script`.
    mm = _market_map({"CCC": _chartable("CCC", "C"), "DDD": _chartable("DDD", "C")})
    html = _d1_render(_run(outcome="NO_TRADE"), mm)
    assert '<details open class="tier-group" id="tier-c">' in html
    assert "<details open" not in _d1_card(html, "DDD")
    for state in _S1_STATES.values():
        html = _d1_render(_run(**state), _market_map(
            {"AAA": _chartable("AAA", "A+"), "BBB": _chartable("BBB", "B")}))
        assert '<details open class="tier-group"' not in html  # no low tier at all
        assert "<details open" not in html
        assert html.count("<script") == 1
    assert '<details open class="card-detail">' not in _d1_render(_run(outcome="NO_TRADE"), _s1_mixed())
