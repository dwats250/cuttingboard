"""Tests for PRD-055 — dashboard renderer: Core rendering, blocks, section order, auto-refresh, run delta, empty candidates."""

from __future__ import annotations

import copy

from cuttingboard.delivery.dashboard_renderer import (
    _DASHBOARD_REFRESH_SECONDS,
    render_dashboard_html,
)

from tests.dash_helpers import _macro_drivers, _market_map, _mm_symbol, _payload, _run, _trade, _trade_decision


# ---------------------------------------------------------------------------
# PRD-315 depth-aware top-level extraction (test-local; replaces Candidate-
# relative substring sentinels so the Opportunity->Candidate continuity move
# cannot silently weaken order coverage).
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
# Field mapping
# ---------------------------------------------------------------------------

def test_field_mapping_exact() -> None:
    p = _payload(
        market_regime="CHAOTIC",
        tradable=False,
        timestamp="2026-01-15T09:30:00Z",
        validation_halt_detail={"reason": "VIX_SPIKE_HALT"},
    )
    r = _run(
        status="HALT",
        posture="STAY_FLAT",
        confidence=0.625,
        system_halted=True,
        kill_switch=False,
        errors=["quota_exceeded_unique"],
        data_status="stale",
    )
    html = render_dashboard_html(p, r)

    # PRD-158 § 4.2: timestamp now renders as relative freshness; raw
    # CHAOTIC regime translates to "Stand down"; confidence is suppressed.
    assert "HALT" in html
    assert "Stand down" in html
    assert "STAY_FLAT" in html
    # PRD-219: distilled system-state — on a halt the operational error is the
    # context reason; the raw "YES" halted-bool field is gone.
    assert "quota_exceeded_unique" in html  # errors[0] surfaced as halt context
    assert ">YES<" not in html


def test_no_unapproved_fields() -> None:
    html = render_dashboard_html(_payload(), _run()).lower()
    for field in (
        "net_score",
        "router_mode",
        "run_id",
        "candidates_generated",
        "energy_score",
        "index_score",
        "schema_version",
        "symbols_scanned",
        "watchlist",
        "rejected",
    ):
        assert field not in html, f"Unapproved field rendered: {field}"


def test_deterministic_output() -> None:
    p = _payload()
    r = _run()
    assert render_dashboard_html(p, r) == render_dashboard_html(p, r)


def test_no_mutation() -> None:
    p = _payload(top_trades=[_trade("NVDA")])
    r = _run(errors=["some_error"])
    p_before = copy.deepcopy(p)
    r_before = copy.deepcopy(r)
    render_dashboard_html(p, r)
    assert p == p_before
    assert r == r_before


# ---------------------------------------------------------------------------
# R9 — removed block IDs absent
# ---------------------------------------------------------------------------

def test_removed_block_ids_absent() -> None:
    html = render_dashboard_html(
        _payload(top_trades=[_trade()], trade_decision_detail=[_trade_decision()]),
        _run(),
    )
    assert 'id="decision-summary"'  not in html
    assert 'id="primary-setup"'     not in html
    assert 'id="secondary-setups"'  not in html
    assert 'id="trade-decisions"'   not in html
    # PRD-177 R1: the two debugging sections are cut.
    assert 'id="run-history"'         not in html
    assert 'id="artifact-diagnostics"' not in html


def test_preserved_block_ids_present() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run(), history_runs=[_run()])
    assert 'id="system-state"'     in html
    assert 'id="run-delta"'        in html
    # PRD-177 R1: run-history is cut; the calibration surface is now the scoreboard.
    assert 'id="run-history"'      not in html
    assert 'id="scoreboard"'       in html


# ---------------------------------------------------------------------------
# PRD-055 PATCH — auto-refresh meta
# ---------------------------------------------------------------------------

def test_auto_refresh_meta_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'http-equiv="refresh"' in html
    assert 'content="30"' in html


def test_dashboard_refresh_constant_value() -> None:
    assert _DASHBOARD_REFRESH_SECONDS == 30


# ---------------------------------------------------------------------------
# PRD-041 — run delta (present/absent with previous_run)
# ---------------------------------------------------------------------------

def test_run_delta_present_with_previous_run() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run(posture="STAY_FLAT"))
    assert 'id="run-delta"' in html


def test_run_delta_source_missing_without_previous_run() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=None)
    assert 'id="run-delta"' in html
    assert "NO_PREVIOUS_RUN" in html.split('id="run-delta"', 1)[1]


# ---------------------------------------------------------------------------
# PRD-073 — R5: Section order
# ---------------------------------------------------------------------------

def test_section_order_system_state_before_candidates() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert html.index('id="system-state"') < html.index('id="candidate-board"')


def test_section_order_system_state_before_run_delta() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run())
    assert html.index('id="system-state"') < html.index('id="run-delta"')


def test_section_order_full_r5_sequence() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="B")})
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), previous_run=_run(), market_map=mm)
    ids = _top_ids(html)
    # PRD-315: Candidate is lifted ahead of the detailed Context chain, so the
    # full-board order is System (-> Opportunity when valid) -> Candidate ->
    # Macro -> ... -> Run Delta. macro-pressure stays inline inside macro-tape.
    assert ids.index("system-state") < ids.index("candidate-board")
    assert ids.index("candidate-board") < ids.index("macro-tape") < ids.index("run-delta")
    if "opportunity-survival" in ids:
        assert ids.index("system-state") < ids.index("opportunity-survival") < ids.index("candidate-board")
    macro = _top_block(html, "macro-tape")
    assert 'class="macro-pressure-line' in macro


# PRD-177 R2: four-questions section order
def test_section_order_four_questions_sequence() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="B")})
    # PRD-313: a healthy-empty view suppresses the standalone block, so the order
    # check uses a populated (preserved) view to assert red-folder's position.
    rf = {"ok": True, "error": None,
          "events": [{"date": "2026-06-11", "time_et": "08:30", "type": "CPI", "name": "CPI (May)"}],
          "expiring": False}
    hist = [{"date": "2026-06-09", "regime": "RISK_ON", "posture": "CONTROLLED_LONG",
             "spy_close_change_pct": 0.01}]
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()), _run(),
        previous_run=_run(), market_map=mm, regime_history=hist, red_folder=rf,
    )
    # PRD-315: Candidate now leads the detailed Context chain (System ->
    # Candidate -> Macro -> Red Folder -> Trend), so it precedes macro-tape.
    order = [
        "system-state", "candidate-board", "macro-tape", "red-folder",
        "trend-structure", "run-delta", "scoreboard",
    ]
    ids = _top_ids(html)
    positions = [ids.index(section) for section in order]
    assert positions == sorted(positions)


# ---------------------------------------------------------------------------
# PRD-073 — R6: Section labels
# ---------------------------------------------------------------------------

def test_run_delta_section_label_changes_since_last_run() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run())
    delta = html.split('id="run-delta"', 1)[1]
    assert "Changes Since Last Run" in delta


def test_run_delta_section_label_old_delta_absent() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run())
    delta = html.split('id="run-delta"', 1)[1]
    assert "<h2>Delta</h2>" not in delta


# ---------------------------------------------------------------------------
# PRD-073 — R8: Empty candidate state
# ---------------------------------------------------------------------------

def test_empty_candidates_message() -> None:
    mm = _market_map({})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "NO_CANDIDATES" in html


def test_empty_candidates_no_error() -> None:
    mm = _market_map({})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="candidate-board"' in html
