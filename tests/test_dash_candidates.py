"""Tests for PRD-055 — dashboard renderer: Candidate board, tiers, cards, setup_state, candidate_risk, grade_order, lifecycle badges/detail, removed symbols."""

from __future__ import annotations

from cuttingboard.delivery.dashboard_renderer import (
    _GRADE_ORDER,
    render_dashboard_html,
)

from tests.dash_helpers import _market_map, _mm_symbol, _payload, _run


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
    assert "NO_CANDIDATES" in html


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
    # cyan actionable accent, in that order.
    syms = {"SPY": _mm_symbol("SPY", grade="A",
                              trade_framing={"direction": "LONG",
                                             "entry": "above 510_UNIQUE"},
                              invalidation=["below 490_UNIQUE"])}
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map(syms))
    card = _card(html, "SPY")
    assert ('<div class="label">IN →</div>'
            '<div class="value-key value-actionable">above 510_UNIQUE</div>') in card
    assert ('<div class="label">OUT →</div>'
            '<div class="value-key value-actionable">below 490_UNIQUE</div>') in card
    assert card.index("IN →") < card.index("OUT →")


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
    block = html.split('id="alert-watchlist"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "META" in block
    assert "LONG" in block
    assert "XLE" in block


def test_alert_watchlist_positioned_before_candidate_board() -> None:
    """alert-watchlist section appears before candidate-board in DOM."""
    from tests.dash_helpers import _trade_decision
    gated = [_trade_decision("NVDA", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION")]
    html = render_dashboard_html(_payload(), _run(), alert_candidates=gated)
    assert html.index('id="alert-watchlist"') < html.index('id="candidate-board"')


# ---------------------------------------------------------------------------
# R5 — Candidate Board Rename
# ---------------------------------------------------------------------------

def test_candidate_board_renamed_to_market_map() -> None:
    """Candidate Board heading is renamed to Market Map / Developing Setups."""
    html = render_dashboard_html(_payload(), _run())
    assert "Market Map / Developing Setups" in html
    # Old label must not appear in the board section heading
    board = html.split('id="candidate-board"', 1)[1].split('</div>', 1)[0]
    assert "Candidate Board" not in board
