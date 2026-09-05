"""PRD-332 (D5) — WATCHING setup-workspace: native radio-group selector + the
#alert-watchlist relocation above #candidate-board.

These are the RED guards for the D5 implementation. Each asserts the NEW
presentation-only behavior and fails on pre-implementation HEAD. The selector
changes presentation ONLY: grades, ordering, tiers, MANUAL_CHECK semantics,
primary-symbol selection, and the chart slot are unchanged (verified here by
counting the single setup-chart and by checking the default = primary).
"""

from __future__ import annotations

from datetime import datetime, timezone
import re

from cuttingboard.delivery.dashboard_renderer import render_dashboard_html
from cuttingboard.delivery import primary_selection

from tests.dash_helpers import (
    _bars_snapshot,
    _chartable,
    _market_map,
    _mm_symbol,
    _payload,
    _run,
)
from tests.test_dash_candidates import _top_ids

_NOW = datetime(2026, 8, 28, 14, 0, tzinfo=timezone.utc)

_MANUAL = "NEEDS_MANUAL_CHECK"


# --- fixtures ---------------------------------------------------------------

def _two_high_grade_html(**kwargs) -> str:
    """>=2 high-grade cards (non-chart) -> the workspace renders."""
    mm = _market_map({"AAA": _mm_symbol("AAA", "A+"), "BBB": _mm_symbol("BBB", "A")})
    return render_dashboard_html(_payload(), _run(outcome="TRADE"), market_map=mm, now=_NOW, **kwargs)


def _two_high_grade_chart_html(**kwargs) -> str:
    """>=2 high-grade chart-bearing cards; canonical primary = AAA (A+)."""
    mm = _market_map({"AAA": _chartable("AAA", "A+"), "BBB": _chartable("BBB", "A")})
    return render_dashboard_html(
        _payload(), _run(outcome="TRADE"), market_map=mm,
        price_bars_snapshot=_bars_snapshot(symbols=("AAA", "BBB")), now=_NOW, **kwargs,
    )


def _one_high_grade_html() -> str:
    mm = _market_map({"AAA": _mm_symbol("AAA", "A+")})
    return render_dashboard_html(_payload(), _run(outcome="TRADE"), market_map=mm, now=_NOW)


def _low_tier_primary_html() -> str:
    """>=2 high-grade cards (non-chart) + a chart-bearing C-grade card that becomes
    the canonical primary (RC-1/RC-3): primary sits OUTSIDE the workspace."""
    mm = _market_map({
        "AAA": _mm_symbol("AAA", "A+"),
        "BBB": _mm_symbol("BBB", "A"),
        "CCC": _chartable("CCC", "C"),
    })
    return render_dashboard_html(
        _payload(), _run(outcome="TRADE"), market_map=mm,
        price_bars_snapshot=_bars_snapshot(symbols=("CCC",)), now=_NOW,
    )


def _radio_ids(html: str) -> list[str]:
    return re.findall(r'<input type="radio" name="setup-select" id="(setup-[^"]+)"', html)


# --- S1: workspace activation gate -----------------------------------------

def test_workspace_renders_with_two_high_grade_cards() -> None:
    assert 'id="setup-workspace"' in _two_high_grade_html()


def test_no_workspace_with_single_high_grade_card() -> None:
    assert 'id="setup-workspace"' not in _one_high_grade_html()


def test_no_workspace_with_no_high_grade_cards() -> None:
    mm = _market_map({"DDD": _mm_symbol("DDD", "D"), "FFF": _mm_symbol("FFF", "F")})
    html = render_dashboard_html(_payload(), _run(outcome="TRADE"), market_map=mm, now=_NOW)
    assert 'id="setup-workspace"' not in html


# --- S2: one radio/label/panel per workspace symbol; exactly one checked ----

def test_one_radio_label_panel_per_symbol_and_exactly_one_checked() -> None:
    html = _two_high_grade_html()
    radios = _radio_ids(html)
    assert radios == ["setup-AAA", "setup-BBB"]
    assert html.count('class="setup-tab ') == 2
    assert html.count('class="setup-panel"') == 2
    assert len(re.findall(r'<input type="radio" name="setup-select"[^>]* checked>', html)) == 1


# --- S3: default-checked = canonical primary (chart-slot unchanged) ----------

def test_default_checked_is_canonical_primary_when_in_workspace() -> None:
    html = _two_high_grade_chart_html()
    mm = _market_map({"AAA": _chartable("AAA", "A+"), "BBB": _chartable("BBB", "A")})
    primary = primary_selection.select_primary_card_symbol(
        mm, {s: (_bars_snapshot(symbols=(s,))["symbols"][s]["bars"], "") for s in ("AAA", "BBB")}, {}
    )
    # primary resolves to AAA (A+ over A); the AAA radio is the checked one.
    assert re.search(r'id="setup-AAA" class="setup-select" checked>', html)
    assert 'id="setup-BBB" class="setup-select" checked' not in html
    assert primary == "AAA"


def test_low_tier_primary_default_is_first_workspace_symbol() -> None:
    # RC-1/RC-3: primary is the C-grade card (outside the workspace); the default
    # tab is the first workspace symbol, and no inline chart lives in the workspace.
    html = _low_tier_primary_html()
    assert re.search(r'id="setup-AAA" class="setup-select" checked>', html)
    workspace = html.split('id="setup-workspace"', 1)[1].split('id="alert-watchlist"', 1)[0]
    assert 'class="setup-chart"' not in workspace


# --- S4: tab order = sorted order; tier headers preserved -------------------

def test_tab_order_matches_grade_order_and_tier_headers_preserved() -> None:
    html = _two_high_grade_html()
    assert _radio_ids(html) == ["setup-AAA", "setup-BBB"]
    assert html.index('for="setup-AAA"') < html.index('for="setup-BBB"')
    assert 'id="tier-aplus"' in html and 'id="tier-a"' in html
    assert "A+ — ACTIONABLE (1)" in html and "A — HIGH QUALITY (1)" in html


# --- S5: alert-watchlist above candidate-board; CHECK token mirror ----------

def test_alert_watchlist_before_candidate_board() -> None:
    cand = {"symbol": "NVDA", "direction": "LONG",
            "block_reason": "CHAIN DATA UNAVAILABLE", "setup_quality": _MANUAL}
    ids = _top_ids(_two_high_grade_html(alert_candidates=[cand]))
    assert ids.index("alert-watchlist") < ids.index("candidate-board")
    assert ids.index("candidate-board") == ids.index("alert-watchlist") + 1


def test_manual_check_tab_token_when_workspace_symbol_is_alert_candidate() -> None:
    cand = {"symbol": "AAA", "direction": "LONG",
            "block_reason": "CHAIN DATA UNAVAILABLE", "setup_quality": _MANUAL}
    html = _two_high_grade_html(alert_candidates=[cand])
    aaa_tab = html.split('for="setup-AAA"', 1)[1].split("</label>", 1)[0]
    bbb_tab = html.split('for="setup-BBB"', 1)[1].split("</label>", 1)[0]
    assert '<span class="setup-tab-check">CHECK</span>' in aaa_tab
    assert "CHECK" not in bbb_tab
    # the literal MANUAL CHECK is NOT duplicated onto tabs (PRD-331 preserved)
    assert "MANUAL CHECK" not in html.split('id="candidate-board"', 1)[1]


# --- S6: no JavaScript ------------------------------------------------------

def test_no_javascript_added() -> None:
    html = _two_high_grade_html()
    assert html.count("<script") == 1  # pre-existing staleness banner only
    assert "onclick" not in html and "onchange" not in html
    assert 'role="tab"' not in html and 'role="tablist"' not in html


# --- S7: fail-open — only inline per-symbol rules hide panels ----------------

def test_static_css_never_hides_a_panel_and_inline_rules_are_setup_scoped() -> None:
    html = _two_high_grade_html()
    head_css = html.split("<style>", 1)[1].split("</style>", 1)[0]
    assert "setup-panel" not in head_css or "display:none" not in head_css
    assert ".tier-group{display:none" not in head_css
    # inline workspace style: every visibility rule is keyed on a #setup- radio
    inline = html.split('id="setup-workspace"', 1)[1].split("<style>", 1)[1].split("</style>", 1)[0]
    for rule in re.findall(r'([^{}]+)\{[^{}]*display:none[^{}]*\}', inline):
        assert rule.strip().startswith("#setup-"), rule


# --- S8: chart slot unchanged (primary inline + others disclosed) -----------

def test_setup_chart_count_unchanged_by_workspace() -> None:
    # PRD-321: the primary takes the inline chart; every other chartable card
    # keeps its own CHART > disclosure. Both AAA (primary, inline) and BBB
    # (disclosed) render a setup-chart -> 2. The workspace must not change this.
    html = _two_high_grade_chart_html()
    assert html.count('class="setup-chart"') == 2
    # exactly one INLINE chart (not inside a chart-detail disclosure) = the primary
    disclosed = html.count('class="chart-detail"')
    assert html.count('class="setup-chart"') - disclosed == 1
