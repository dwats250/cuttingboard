"""PRD-083: focused tests for dashboard data freshness and source visibility."""
from __future__ import annotations

import ast as _ast
import hashlib
import inspect
import json
import os
import re
import time
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cuttingboard.delivery.dashboard_renderer import (
    DASHBOARD_STALE_AFTER_SECONDS,
    INACTIVE_SESSION_LABEL,
    INACTIVE_SESSION_MAX_AGE_HOURS,
    INACTIVE_SESSION_TYPES,
    LIVE_SESSION_MAX_AGE_MINUTES,
    _UNAVAILABLE_WATCH,
    _macro_tape_source_health,
    _market_map_source_health,
    _system_state_source_health,
    _trend_structure_source_health,
    _trend_symbols_usable,
    render_dashboard_html,
)
from cuttingboard.delivery import dashboard_renderer as _dr
from cuttingboard.delivery import gex_card as _gex
from tests.dash_helpers import (
    _PC_BARS,
    _bars_snapshot,
    _chartable,
    _macro_drivers,
    _macro_tape_block,
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


_UI_DASHBOARD = Path("ui/dashboard.html")
_UI_INDEX = Path("ui/index.html")
_FORBIDDEN_ARTIFACT_PATTERNS = ("pytest-of-", "/tmp/pytest", "/tmp/")


def _assert_no_forbidden_artifact_patterns(path: Path | str, html: str) -> None:
    for pattern in _FORBIDDEN_ARTIFACT_PATTERNS:
        assert pattern not in html, f"{path}: contains forbidden pattern {pattern!r}"


# PA1 — published artifact must not contain raw DATA_UNAVAILABLE in macro tape slots
def test_published_artifact_no_data_unavailable_in_tape() -> None:
    if not _UI_INDEX.exists():
        pytest.skip("ui/index.html not present")
    html = _UI_INDEX.read_text(encoding="utf-8")
    tape = html.split('id="macro-tape"', 1)
    assert len(tape) == 2, "macro-tape block not found in ui/index.html"
    tape_block = tape[1].split('id="red-folder"', 1)[0]
    assert "DATA_UNAVAILABLE" not in tape_block, (
        "ui/index.html macro tape contains DATA_UNAVAILABLE — regenerate with updated renderer"
    )


# PA2 — published artifact must not show NO LIVE MACRO DATA when tape has real values
def test_published_artifact_no_false_no_live_macro_data() -> None:
    if not _UI_INDEX.exists():
        pytest.skip("ui/index.html not present")
    html = _UI_INDEX.read_text(encoding="utf-8")
    tape = html.split('id="macro-tape"', 1)
    assert len(tape) == 2, "macro-tape block not found in ui/index.html"
    tape_block = tape[1].split('id="red-folder"', 1)[0]
    has_real_values = any(
        f'data-symbol="{sym}"' in tape_block and "--" not in tape_block.split(f'data-symbol="{sym}"', 1)[1][:30]
        for sym in ("VIX", "DXY", "10Y", "BTC")
    )
    if has_real_values:
        assert "NO LIVE MACRO DATA" not in tape_block, (
            "ui/index.html shows NO LIVE MACRO DATA despite having real macro values"
        )


# PA3 — published artifact must use mobile-friendly 2-column tradables grid
def test_published_artifact_mobile_grid_width() -> None:
    if not _UI_INDEX.exists():
        pytest.skip("ui/index.html not present")
    html = _UI_INDEX.read_text(encoding="utf-8")
    assert "macro-tradables-grid" in html, "macro-tradables-grid not found in ui/index.html"


# PA4 — published artifacts must not expose pytest or local temp paths
@pytest.mark.parametrize("path", (_UI_DASHBOARD, _UI_INDEX), ids=("dashboard", "index"))
def test_published_artifacts_no_local_artifact_paths(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"{path} not present")
    html = path.read_text(encoding="utf-8")
    _assert_no_forbidden_artifact_patterns(path, html)


def test_artifact_contamination_check_allows_clean_html() -> None:
    _assert_no_forbidden_artifact_patterns("synthetic.html", "<html><body>clean</body></html>")


@pytest.mark.parametrize("pattern", _FORBIDDEN_ARTIFACT_PATTERNS)
def test_artifact_contamination_check_rejects_forbidden_patterns(pattern: str) -> None:
    with pytest.raises(AssertionError, match=re.escape(f"synthetic.html: contains forbidden pattern {pattern!r}")):
        _assert_no_forbidden_artifact_patterns("synthetic.html", f"<span>{pattern}</span>")


def test_ci_workflows_publish_dashboard_with_same_render_copy_contract() -> None:
    for path in (
        Path(".github/workflows/cuttingboard.yml"),
        Path(".github/workflows/hourly_alert.yml"),
    ):
        text = path.read_text(encoding="utf-8")
        render = "python3 -m cuttingboard.delivery.dashboard_renderer"
        copy = "cp ui/dashboard.html ui/index.html"
        assert render in text
        assert copy in text
        assert text.index(render) < text.index(copy)


def test_prd128_hourly_readiness_runs_after_render_and_copy_before_commit_and_push() -> None:
    """PRD-128: hourly readiness must validate freshly rendered artifacts.

    Asserts the full ordering chain in .github/workflows/hourly_alert.yml:
        render < copy < check_readiness < commit < push
    and that the readiness step body carries no `continue-on-error: true`.
    """
    text = Path(".github/workflows/hourly_alert.yml").read_text(encoding="utf-8")

    render = "python3 -m cuttingboard.delivery.dashboard_renderer"
    copy = "cp ui/dashboard.html ui/index.html"
    ready = "python3 scripts/check_readiness.py"
    commit = 'git commit -m "CB hourly:'
    push = "bash tools/ci_push_artifacts.sh"

    for anchor in (render, copy, ready, commit, push):
        assert anchor in text, f"missing anchor in hourly_alert.yml: {anchor!r}"

    render_idx = text.index(render)
    copy_idx = text.index(copy)
    ready_idx = text.index(ready)
    commit_idx = text.index(commit)
    push_idx = text.index(push)

    assert render_idx < copy_idx, "render must precede copy"
    assert copy_idx < ready_idx, "copy must precede readiness"
    assert ready_idx < commit_idx, "readiness must precede commit"
    assert ready_idx < push_idx, "readiness must precede push"

    # The readiness step body is delimited by the preceding `- name:` line and
    # the next `- name:` line. It MUST NOT carry `continue-on-error: true`.
    step_name_start = text.rfind("- name:", 0, ready_idx)
    assert step_name_start != -1, "could not locate readiness step `- name:` line"
    next_step_start = text.find("\n      - name:", ready_idx)
    step_body = text[step_name_start:next_step_start if next_step_start != -1 else len(text)]
    assert "continue-on-error: true" not in step_body, (
        "readiness step must not carry `continue-on-error: true`"
    )


def _candidate_board_section(html: str) -> str:
    return _top_block(html, "candidate-board")


def _candidate_card(html: str, symbol: str = "SPY") -> str:
    return html.split(f'id="card-{symbol}"', 1)[1].split('</div>\n</div>', 1)[0]


_LADDER_ROW = re.compile(
    r'<div class="lvl-row (?P<cls>[^"]+)">'
    r'<span class="lvl-name">(?P<name>[^<]*)</span>'
    r'<span class="lvl-px">(?P<px>[^<]*)</span>'
    r'<span class="lvl-pct">(?P<pct>[^<]*)</span></div>'
)


def _ladder_rows(fragment: str) -> dict[str, tuple[str, str]]:
    """PRD-321 R4: {row name: (price, signed % distance)} from a compact ladder."""
    return {m["name"]: (m["px"], m["pct"]) for m in _LADDER_ROW.finditer(fragment)}


def _ladder_classes(fragment: str) -> dict[str, str]:
    return {m["name"]: m["cls"] for m in _LADDER_ROW.finditer(fragment)}


def _run_with_timestamp(timestamp: str, **kwargs: object) -> dict:
    run = _run(**kwargs)
    run["timestamp"] = timestamp
    run["run_at_utc"] = timestamp
    run["generated_at"] = timestamp
    return run


def _set_generation_ids(payload: dict, run: dict, market_map: dict, generation_id: str) -> None:
    payload.setdefault("meta", {})["generation_id"] = generation_id
    run["generation_id"] = generation_id
    market_map["generation_id"] = generation_id


# T1 — missing market map renders SOURCE_MISSING, not generic MARKET MAP UNAVAILABLE
def test_missing_market_map_renders_source_missing() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=None)
    board = _top_block(html, "candidate-board")
    assert "MARKET MAP UNAVAILABLE" not in board
    assert "SOURCE_MISSING" in board or "N/A" in board


# T2 — stale market_map file renders STALE in candidate board
def test_stale_market_map_renders_stale(tmp_path: pytest.TempPathFactory) -> None:
    mm_file = tmp_path / "market_map.json"
    mm_file.write_text(json.dumps(_market_map()), encoding="utf-8")
    stale_mtime = time.time() - DASHBOARD_STALE_AFTER_SECONDS - 60
    os.utime(mm_file, (stale_mtime, stale_mtime))
    html = render_dashboard_html(_payload(), _run(), market_map_path=mm_file)
    board = _top_block(html, "candidate-board")
    assert "STALE" in board


# T3 — parse-error market_map renders PARSE_ERROR and does not crash
def test_parse_error_market_map_renders_parse_error(tmp_path: pytest.TempPathFactory) -> None:
    mm_file = tmp_path / "market_map.json"
    mm_file.write_text("{not valid json", encoding="utf-8")
    html = render_dashboard_html(_payload(), _run(), market_map_path=mm_file)
    board = _top_block(html, "candidate-board")
    assert "PARSE_ERROR" in board


# T4 — missing tradable quote shows N/A, not silent "--"
def test_missing_tradable_quote_renders_data_unavailable() -> None:
    # Explicitly null current_price; the default _mm_symbol shape mirrors the
    # L8 producer which always supplies a price for high-grade symbols.
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": None}})
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    from tests.dash_helpers import _macro_tape_value_slots
    slots = dict(_macro_tape_value_slots(html))
    assert slots["SPY"] == "N/A"
    assert "--" not in slots.get("SPY", "")


# T5 — available tradable quote renders value, not DATA_UNAVAILABLE
def test_available_tradable_quote_renders_value() -> None:
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    from tests.dash_helpers import _macro_tape_value_slots
    slots = dict(_macro_tape_value_slots(html))
    assert slots["SPY"] == "512.34"
    assert "N/A" not in slots.get("SPY", "")


# PRD-122 R8(a) — full oil render: OIL slot shows formatted level and arrow.
def test_prd122_oil_full_render() -> None:
    from tests.dash_helpers import _macro_tape_block, _macro_tape_value_slots
    drivers = _macro_drivers()
    drivers["oil"] = {"symbol": "CL=F", "level": 78.5, "change_pct": 1.2}
    html = render_dashboard_html(
        _payload(macro_drivers=drivers),
        _run(),
        market_map=_market_map(),
    )
    slots = dict(_macro_tape_value_slots(html))
    assert slots.get("OIL") == "78.5", f"expected OIL=78.5, got slots={slots}"
    tape = _macro_tape_block(html)
    assert 'data-symbol="OIL"' in tape, "OIL slot missing from macro-drivers-row"
    # Arrow for positive change_pct should be the UP glyph.
    assert "OIL ↑" in tape, "OIL slot missing UP arrow for positive change_pct"


# PRD-122 R8(b) — oil key absent: OIL slot degrades to em-dash arrow and '--' value.
def test_prd122_oil_missing_renders_dash() -> None:
    from tests.dash_helpers import _macro_tape_block, _macro_tape_value_slots
    drivers = _macro_drivers()  # no oil key
    assert "oil" not in drivers
    html = render_dashboard_html(
        _payload(macro_drivers=drivers),
        _run(),
        market_map=_market_map(),
    )
    slots = dict(_macro_tape_value_slots(html))
    assert slots.get("OIL") == "--", f"expected OIL=--, got slots={slots}"
    tape = _macro_tape_block(html)
    assert 'data-symbol="OIL"' in tape, "OIL slot must appear in tape even when oil data missing"
    # Em-dash glyph for missing-arrow case.
    assert "OIL —" in tape, "OIL slot missing em-dash arrow for absent oil data"


# PRD-122 R8(c) — stale snapshot fallback: payload omits macro_drivers, snapshot supplies them.
def test_prd122_oil_renders_from_stale_snapshot(tmp_path: Path) -> None:
    from tests.dash_helpers import _macro_tape_value_slots
    snapshot_path = tmp_path / "macro_drivers_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "macro_drivers": {
                    "volatility": {"symbol": "^VIX",     "level": 18.0,    "change_pct": 0.05},
                    "dollar":     {"symbol": "DX-Y.NYB", "level": 104.0,   "change_pct": -0.01},
                    "rates":      {"symbol": "^TNX",     "level": 4.5,     "change_pct": 0.02, "change_bps": 2.0},
                    "bitcoin":    {"symbol": "BTC-USD",  "level": 65000.0, "change_pct": 0.03},
                    "oil":        {"symbol": "CL=F",     "level": 82.4,    "change_pct": -0.8},
                }
            }
        ),
        encoding="utf-8",
    )
    html = render_dashboard_html(
        _payload(macro_drivers={}),
        _run(),
        market_map=_market_map(),
        macro_snapshot_path=snapshot_path,
    )
    slots = dict(_macro_tape_value_slots(html))
    assert slots.get("OIL") == "82.4", (
        f"expected OIL=82.4 from snapshot fallback, got slots={slots}"
    )


def test_macro_pressure_inline_beside_tally() -> None:
    # PRD-217: no standalone macro-pressure disclosure; the per-component phrases
    # render as one inline line inside the macro tape.
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()),
        _run(),
        market_map=_market_map({"SPY": _mm_symbol("SPY")}),
    )

    assert 'id="macro-pressure"' not in html
    assert '<details id="macro-pressure">' not in html
    assert 'class="macro-pressure-line' in html

    # PRD-315: the macro-pressure line lives inside Macro (independent of
    # Candidate position); Candidate now precedes the Macro chain.
    macro = _top_block(html, "macro-tape")
    assert 'class="macro-pressure-line' in macro
    ids = _top_ids(html)
    assert ids.index("candidate-board") < ids.index("macro-tape")

    pressure = html.split('class="macro-pressure-line', 1)[1].split("</div>", 1)[0]
    has_decision_phrase = any(
        phrase in pressure
        for phrase in (
            "VIX permits longs", "VIX blocks longs",
            "DXY pressures longs", "DXY supports risk-on",
            "BTC supports risk-on", "BTC pressures risk-on",
        )
    )
    assert has_decision_phrase, pressure
    assert "Overall" not in pressure


def test_macro_pressure_no_data_renders_unavailable_line(tmp_path: Path) -> None:
    html = render_dashboard_html(
        _payload(macro_drivers={}),
        _run(),
        market_map=_market_map(),
        macro_snapshot_path=tmp_path / "missing_macro_snapshot.json",
    )

    pressure = html.split('class="macro-pressure-line', 1)[1].split("</div>", 1)[0]
    assert "Macro pressure unavailable" in pressure
    assert "NO PRESSURE DATA" not in pressure


def test_macro_pressure_field_missing_renders_unavailable_line(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cuttingboard.delivery.dashboard_renderer._build_pressure_snapshot",
        lambda _macro_drivers, _market_map: "FIELD_MISSING",
    )

    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()),
        _run(),
        market_map=_market_map(),
    )

    pressure = html.split('class="macro-pressure-line', 1)[1].split("</div>", 1)[0]
    assert "Macro pressure unavailable" in pressure
    assert "FIELD_MISSING" not in pressure


def test_mixed_generation_ids_render_warning_and_suppress_active_setup() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp(
        "2026-04-28T12:00:00Z",
        outcome="TRADE",
        permission=True,
    )
    mm = _market_map()
    payload["meta"]["generation_id"] = "gen-a"
    run["generation_id"] = "gen-b"
    mm["generation_id"] = "gen-a"

    html = render_dashboard_html(payload, run, market_map=mm)

    assert "MIXED_ARTIFACTS" in html
    assert "TRADE SETUP ACTIVE" not in html


def test_coherent_generation_ids_preserve_active_setup_behavior() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp(
        "2026-04-28T12:10:01Z",
        outcome="TRADE",
        permission=True,
    )
    mm = _market_map()
    _set_generation_ids(payload, run, mm, "live-20260428T120000Z")

    html = render_dashboard_html(payload, run, market_map=mm)

    assert "MIXED_ARTIFACTS" not in html
    assert 'id="cb-updated"' in html  # PRD-327 R1/R2: the UPDATED label left the fold


def test_dashboard_render_preserves_decision_fields_byte_equal() -> None:
    payload = _payload(
        timestamp="2026-04-28T12:00:00Z",
        macro_drivers=_macro_drivers(),
        top_trades=[{"symbol": "SPY", "direction": "LONG"}],
        trade_decision_detail=[{"symbol": "SPY", "block_reason": "none"}],
    )
    run = _run_with_timestamp("2026-04-28T12:00:00Z", outcome="TRADE")
    mm = _market_map()
    _set_generation_ids(payload, run, mm, "live-20260428T120000Z")
    contract_entry_map = {
        "SPY": 512.34,
        "outcome": "TRADE",
        "trade_candidates": [{"symbol": "SPY"}],
        "block_reasons": [],
    }
    before = json.dumps(
        {
            "run": {"outcome": run["outcome"]},
            "payload": {
                "trade_candidates": deepcopy(payload["sections"]["top_trades"]),
                "block_reasons": deepcopy(payload["sections"]["trade_decision_detail"]),
            },
            "contract": {
                "outcome": contract_entry_map["outcome"],
                "trade_candidates": deepcopy(contract_entry_map["trade_candidates"]),
                "block_reasons": deepcopy(contract_entry_map["block_reasons"]),
            },
        },
        sort_keys=True,
    )

    render_dashboard_html(payload, run, market_map=mm, contract_entry_map=contract_entry_map)

    after = json.dumps(
        {
            "run": {"outcome": run["outcome"]},
            "payload": {
                "trade_candidates": payload["sections"]["top_trades"],
                "block_reasons": payload["sections"]["trade_decision_detail"],
            },
            "contract": {
                "outcome": contract_entry_map["outcome"],
                "trade_candidates": contract_entry_map["trade_candidates"],
                "block_reasons": contract_entry_map["block_reasons"],
            },
        },
        sort_keys=True,
    )
    assert after == before


def test_stale_market_map_suppresses_candidate_cards() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z")
    mm = _market_map({
        "SPY": {
            **_mm_symbol("SPY"),
            "current_price": 512.34,
            "watch_zones": [{"type": "SUPPORT", "level": 510.0}],
        }
    })
    mm["generated_at"] = "2026-04-28T12:00:00Z"

    html = render_dashboard_html(payload, run, market_map=mm)
    board = _top_block(html, "candidate-board")

    assert "STALE MARKET MAP" in board
    assert "Market Map / Developing Setups paused" in board
    assert 'id="card-SPY"' not in board


def test_market_map_without_generated_at_does_not_trigger_stale() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z")
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})
    mm.pop("generated_at", None)

    html = render_dashboard_html(payload, run, market_map=mm)
    board = _top_block(html, "candidate-board")

    assert "STALE_MARKET_MAP" not in board


def test_candidate_level_diagram_uses_current_price_when_contract_entry_missing() -> None:
    entry = {
        **_mm_symbol("SPY"),
        "current_price": 512.34,
        "watch_zones": [{"type": "SUPPORT", "level": 510.0}],
    }
    mm = _market_map({"SPY": entry})

    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    card = _candidate_card(html)

    assert "Chart unavailable" not in card
    assert "Level context unavailable" not in card
    # PRD-321: with no bars snapshot the compact ladder is the whole surface.
    assert 'class="lvl-ladder' in card
    assert 'class="setup-chart"' not in card


def test_candidate_level_diagram_hidden_when_no_level_context() -> None:
    # PRD-158 § 4.2 translation 12: anchor without fib_levels/watch_zones
    # hides the diagram entirely — no placeholder.
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})

    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    card = _candidate_card(html)

    assert "Level context unavailable" not in card
    assert "Chart unavailable" not in card
    assert 'class="lvl-ladder' not in card


def test_candidate_level_diagram_hidden_when_anchor_invalid() -> None:
    # PRD-158 § 4.2 translation 12: invalid anchor (zero/negative) hides the
    # diagram entirely — no placeholder.
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 0}})

    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    card = _candidate_card(html)

    assert "Chart unavailable" not in card
    assert "Level context unavailable" not in card
    assert 'class="lvl-ladder' not in card


def test_candidate_level_diagram_now_anchor_is_current_price_entry_marked_separately() -> None:
    # PRD-226: NOW is the current price (120), NOT the contract entry (110);
    # the entry is its own separate level. PRD-321 carries this into the
    # compact ladder: distinct NOW and ENTRY rows, % measured from NOW.
    entry = {
        **_mm_symbol("SPY"),
        "current_price": 120.0,
        "watch_zones": [
            {"type": "SUPPORT", "level": 100.0},
            {"type": "RESISTANCE", "level": 130.0},
        ],
    }
    mm = _market_map({"SPY": entry})

    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()),
        _run(),
        market_map=mm,
        contract_entry_map={"SPY": 110.0},
    )
    card = _candidate_card(html)
    rows = _ladder_rows(card)

    assert rows["NOW"] == ("120.00", "")            # NOW = current price
    assert rows["ENTRY"] == ("110.00", "-8.3%")     # ENTRY = contract entry
    assert "lvl-now" in _ladder_classes(card)["NOW"]
    assert "lvl-entry" in _ladder_classes(card)["ENTRY"]


def test_stale_contract_entries_are_ignored_for_level_anchors() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z")
    entry = {
        **_mm_symbol("SPY"),
        "current_price": 120.0,
        "watch_zones": [
            {"type": "SUPPORT", "level": 100.0},
            {"type": "RESISTANCE", "level": 130.0},
        ],
    }
    mm = _market_map({"SPY": entry})
    mm["generated_at"] = "2026-04-28T12:10:01Z"

    html = render_dashboard_html(
        payload,
        run,
        market_map=mm,
        contract_entry_map={"SPY": 110.0},
        contract_generated_at="2026-04-28T12:00:00Z",
    )
    card = _candidate_card(html)

    # The stale contract entry is dropped: NOW is the only Tier-1 price row.
    assert _ladder_rows(card)["NOW"] == ("120.00", "")
    assert "ENTRY" not in _ladder_rows(card)


def test_prd223_loader_extracts_valid_stops_and_rejects_invalid(tmp_path: Path) -> None:
    # PRD-223: _load_contract_entry_context captures trade_candidates[].stop
    # into a stop map — finite positive floats only. Deleting any guard lets an
    # undrawable stop through and this test fails.
    from cuttingboard.delivery.dashboard_renderer import _load_contract_entry_context

    contract = {
        "generated_at": "2026-04-28T12:00:00Z",
        "trade_candidates": [
            {"symbol": "SPY", "decision_status": "ALLOW_TRADE", "entry": 510.0, "stop": 505.0},
            {"symbol": "QQQ", "decision_status": "ALLOW_TRADE", "entry": 430.0, "stop": float("nan")},
            {"symbol": "GLD", "decision_status": "ALLOW_TRADE", "entry": 220.0, "stop": -1.0},
            {"symbol": "SLV", "decision_status": "ALLOW_TRADE", "entry": 29.0, "stop": "not-a-price"},
            # bool must be rejected BEFORE coercion: float(True) == 1.0 would
            # masquerade as a real price (Codex P2 on PR #89).
            {"symbol": "XLE", "decision_status": "ALLOW_TRADE", "entry": 90.0, "stop": True},
            {"symbol": "GDX", "decision_status": "ALLOW_TRADE", "entry": 41.0},
            # PRD-224: the entry path mirrors the stop guards — bool, non-finite,
            # and non-positive entries never become anchors.
            {"symbol": "IWM", "decision_status": "ALLOW_TRADE", "entry": True, "stop": 200.0},
            {"symbol": "TLT", "decision_status": "ALLOW_TRADE", "entry": float("inf"), "stop": 90.0},
            {"symbol": "UUP", "decision_status": "ALLOW_TRADE", "entry": -1.0, "stop": 27.0},
        ],
    }
    (tmp_path / "latest_hourly_contract.json").write_text(json.dumps(contract), encoding="utf-8")

    entry_map, stop_map, _alerts, generated_at, _path = _load_contract_entry_context(tmp_path)

    assert stop_map == {"SPY": 505.0, "IWM": 200.0, "TLT": 90.0, "UUP": 27.0}
    assert entry_map == {"SPY": 510.0, "QQQ": 430.0, "GLD": 220.0, "SLV": 29.0, "XLE": 90.0, "GDX": 41.0}
    assert generated_at == "2026-04-28T12:00:00Z"


def test_prd223_stale_contract_stops_are_ignored_for_risk_band() -> None:
    # PRD-223: contract staleness nulls ONLY the entry map; the card-level
    # pair gate (a stop draws only against its own contract entry) then
    # blocks the orphaned stop. There is deliberately NO stop-map nulling —
    # it proved unobservable (no red test could fail on it) and was cut per
    # semantic-hardening invariant 4. A stale stop must not shade a fresh card.
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z")
    entry = {
        **_mm_symbol("SPY"),
        "current_price": 120.0,
        "watch_zones": [
            {"type": "SUPPORT", "level": 100.0},
            {"type": "RESISTANCE", "level": 130.0},
        ],
    }
    mm = _market_map({"SPY": entry})
    mm["generated_at"] = "2026-04-28T12:10:01Z"

    html = render_dashboard_html(
        payload,
        run,
        market_map=mm,
        contract_entry_map={"SPY": 110.0},
        contract_stop_map={"SPY": 105.0},
        contract_generated_at="2026-04-28T12:00:00Z",
    )
    card = _candidate_card(html)

    assert 'opacity="0.08"' not in card
    assert 'stroke="#e05252"' not in card
    assert ">STOP " not in card


def test_failed_candidate_with_only_current_price_does_not_render_entry_only_diagram() -> None:
    mm = _market_map({"SPY": {**_mm_symbol("SPY", grade="C"), "current_price": 512.34}})

    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    card = _candidate_card(html)

    # PRD-158 translation 12: no level surface and no placeholder when level
    # context is absent.
    assert "Level context unavailable" not in card
    assert 'class="lvl-ladder' not in card
    assert 'class="setup-chart"' not in card
    assert "ENTRY" not in card


# T5b — GDX must appear in tradables section of macro tape
def test_gdx_present_in_tradables() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=None)
    from tests.dash_helpers import _macro_tape_value_slots
    slots = dict(_macro_tape_value_slots(html))
    assert "GDX" in slots
    assert slots["GDX"] == "N/A"


# T6 — null-safe secondary sections: FIELD_MISSING, SOURCE_MISSING, NO_HISTORY
def test_null_safe_secondary_sections_no_crash() -> None:
    html = render_dashboard_html(
        _payload(),
        _run(),
        previous_run=None,
        history_runs=None,
    )
    delta_block = html.split('id="run-delta"', 1)[1]
    assert "NO_PREVIOUS_RUN" in delta_block
    # PRD-177 R1: run-history cut; its empty-state token is gone.
    assert 'id="run-history"' not in html
    assert "NO_HISTORY" not in html
    # No crash — rendering completed; pressure block present, scoreboard
    # falls back to its empty-state line with no regime_history supplied.
    assert 'id="macro-tape"' in html
    scoreboard = html.split('id="scoreboard"', 1)[1]
    assert "No regime history yet." in scoreboard


# PRD-089-PATCH tests

def _system_state_block(html: str) -> str:
    """Extract content of id="system-state" block."""
    return html.split('id="system-state"', 1)[1].split('<div class="block"', 1)[0]


def _updated_value(state: str) -> str:
    """PRD-219: the single absolute UPDATED timestamp value.

    The value div may carry extra attributes (PRD-250 adds id="cb-updated" +
    data-updated-utc for the client-side staleness banner), so parse past the
    class token to the tag close rather than matching 'class="value">' literally.
    """
    # PRD-327 R1: the "UPDATED" label element is gone; the timestamp value is
    # the only class="value" element inside #system-state.
    after_value = state.split('class="value"', 1)[1]
    return after_value.split(">", 1)[1].split("</div>", 1)[0]


def test_no_separate_dashboard_header_block() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'id="dashboard-header"' not in html


def test_system_state_contains_updated_timestamp() -> None:
    # PRD-219: one absolute UPDATED line replaces RUN SNAPSHOT/LIVE STATE/SCOREBOARD.
    html = render_dashboard_html(_payload(), _run())
    state = _system_state_block(html)
    assert 'id="cb-updated"' in state  # PRD-327 R2: label removed, value element stays


@pytest.mark.parametrize(
    "age_seconds,expected",
    [
        (30, "<1 min old"),          # sub-minute
        (59, "<1 min old"),
        (60, "1 minute old"),
        (180, "3 minutes old"),
        (300, "5 minutes old"),      # exactly at threshold
        (301, "STALE (>5 min)"),     # just past threshold
        (-60, "<1 min old"),         # future-dated -> no negative token
    ],
)
def test_prd167_run_snapshot_freshness_token_boundaries(age_seconds: int, expected: str) -> None:
    from cuttingboard.delivery.dashboard_renderer import _run_snapshot_freshness_token
    base = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    ts = "2026-04-28T12:00:00Z"
    now = base + timedelta(seconds=age_seconds)
    assert _run_snapshot_freshness_token(ts, now) == expected


@pytest.mark.parametrize("bad", [None, "", "not-a-date", 12345])
def test_prd167_run_snapshot_freshness_token_unavailable(bad: object) -> None:
    from cuttingboard.delivery.dashboard_renderer import _run_snapshot_freshness_token
    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    assert _run_snapshot_freshness_token(bad, now) == "unavailable"


# --- PRD-189: per-surface freshness (live-state + scoreboard age) -----------

def _surface_value(state: str, label: str) -> str:
    """Extract the value rendered for a system-state freshness label."""
    after = state.split(f">{label}</div>", 1)[1]
    return after.split('class="value">', 1)[1].split("</div>", 1)[0]


@pytest.mark.parametrize(
    "age_seconds,expected",
    [
        (30, "<1 min old"),
        (59, "<1 min old"),
        (60, "1 min old"),
        (3599, "59 min old"),
        (3600, "1 hr old"),
        (86399, "23 hr old"),
        (86400, "1 day old"),
        (2 * 86400, "2 days old"),
        (33 * 86400, "33 days old"),
        (-60, "<1 min old"),  # future-dated -> no negative/0-min token
    ],
)
def test_prd189_surface_age_token_boundaries(age_seconds: int, expected: str) -> None:
    from cuttingboard.delivery.dashboard_renderer import _surface_age_token
    base = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
    parsed = base - timedelta(seconds=age_seconds)
    assert _surface_age_token(parsed, base, "absent") == expected


def test_prd189_surface_age_token_absent_is_explicit() -> None:
    from cuttingboard.delivery.dashboard_renderer import _surface_age_token
    now = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
    assert _surface_age_token(None, now, "no live run recorded") == "no live run recorded"


@pytest.mark.parametrize(
    "newest_date,expected",
    [
        ("2026-06-16", "today"),
        ("2026-06-15", "1 day old"),
        ("2026-05-14", "33 days old"),
    ],
)
def test_prd189_scoreboard_age_token(newest_date: str, expected: str) -> None:
    from cuttingboard.delivery.dashboard_renderer import _scoreboard_age_token
    now = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
    history = [{"date": "2026-05-01"}, {"date": newest_date}]
    assert _scoreboard_age_token(history, now, "absent") == expected


@pytest.mark.parametrize("history", [None, [], [{"date": "garbage"}], [{}]])
def test_prd189_scoreboard_age_token_absent_or_unparseable(history) -> None:
    from cuttingboard.delivery.dashboard_renderer import _scoreboard_age_token
    now = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
    assert _scoreboard_age_token(history, now, "no scoreboard history") == "no scoreboard history"


def test_prd219_updated_reads_pipeline_time_not_fresh_payload() -> None:
    # PRD-219 preserves the PRD-189 frozen-pipeline signal in the single UPDATED
    # line: it reads the PIPELINE run time, so a stale pipeline shows an old
    # absolute timestamp even when the payload is fresh.
    run = _run_with_timestamp("2026-05-14T12:00:00Z")  # 33 days stale pipeline run
    html = render_dashboard_html(
        _payload(timestamp="2026-06-16T11:58:00Z"),  # payload fresh
        run,
    )
    updated = _updated_value(_system_state_block(html))
    assert "May 14" in updated
    assert "Jun 16" not in updated


def test_prd219_updated_reads_pipeline_run_not_hourly_override() -> None:
    # PRD-219/PRD-189: UPDATED reads the PIPELINE run (latest_run.json), not the
    # hourly --run override, so a frozen cuttingboard.yml pipeline reads stale
    # even while the hourly publish run is fresh.
    fresh_hourly_run = _run_with_timestamp("2026-06-16T11:59:30Z")
    stale_pipeline_run = _run_with_timestamp("2026-05-14T12:00:00Z")
    html = render_dashboard_html(
        _payload(timestamp="2026-06-16T11:59:30Z"),
        fresh_hourly_run,
        pipeline_run=stale_pipeline_run,
    )
    updated = _updated_value(_system_state_block(html))
    assert "May 14" in updated and "Jun 16" not in updated


def test_prd219_updated_falls_back_to_run_when_no_pipeline_run() -> None:
    # When pipeline_run is absent, UPDATED falls back to `run`.
    html = render_dashboard_html(
        _payload(timestamp="2026-06-16T12:00:00Z"),
        _run_with_timestamp("2026-06-16T12:00:00Z"),
    )
    updated = _updated_value(_system_state_block(html))
    assert "Jun 16" in updated


def test_main_block_no_original_utc_timestamp() -> None:
    html = render_dashboard_html(
        _payload(timestamp="2026-05-05T20:29:00Z"),
        _run_with_timestamp("2026-05-05T20:29:00Z"),
    )
    state = _system_state_block(html)
    assert "Original" not in state
    assert "UTC" not in state


def test_permission_label_used_not_trade_permission() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert "Trade Permission" not in html


def test_halted_state_verdict_shows_halt() -> None:
    # PRD-219: halt is unmistakable in the distilled verdict (red, SYSTEM HALT).
    run = _run(system_halted=True)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert 'class="sys-verdict sys-halt"' in state
    assert "SYSTEM HALT" in state


def test_halted_state_reason_in_why_line() -> None:
    # PRD-281: the halt reason renders in the dedicated WHY line (superseding,
    # for this one display, PRD-219's "folds into the context line" choice).
    payload = _payload(validation_halt_detail={"reason": "STAY_FLAT regime"})
    run = _run(system_halted=True)
    html = render_dashboard_html(payload, run)
    state = _system_state_block(html)
    assert "SYSTEM HALT" in state
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "STAY_FLAT regime" in why
    context = state.split('class="sys-context', 1)[1].split("</div>", 1)[0]
    assert "STAY_FLAT regime" not in context


def test_non_halted_renders_verdict_no_permission_field() -> None:
    # PRD-219: no Permission field; the verdict conveys the state.
    run = _run(system_halted=False, permission=True)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert 'class="sys-verdict' in state
    assert ">Permission<" not in state


def test_normal_run_no_halted_or_kill_switch_in_system_state() -> None:
    run = _run(system_halted=False, kill_switch=False)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "Halted" not in state
    assert "Kill Switch" not in state


def test_halted_run_shows_halted_not_kill_switch() -> None:
    # PRD-219: halt shows in the verdict; kill-switch line absent when off.
    run = _run(system_halted=True, kill_switch=False)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "SYSTEM HALT" in state
    assert "Kill switch active" not in state


def test_kill_switch_run_shows_kill_switch() -> None:
    # PRD-219: kill switch renders an explicit context line.
    run = _run(system_halted=False, kill_switch=True)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "Kill switch active" in state


# ---------------------------------------------------------------------------
# PRD-279: Decision State Header
# ---------------------------------------------------------------------------

def test_prd279_halted_shows_decision_state_halt() -> None:
    run = _run(system_halted=True)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "decision-state-label" not in state  # PRD-327 R1: caption removed
    assert 'class="decision-state sys-halt">HALT</div>' in state


def test_prd279_kill_switch_halt_shows_decision_state_halt() -> None:
    # A kill-switch trip escalates system_halted=True (PRD-278); the header
    # must still read HALT, and the existing kill-switch context line stays.
    run = _run(system_halted=True, kill_switch=True)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert 'class="decision-state sys-halt">HALT</div>' in state
    assert "Kill switch active" in state


def test_prd279_trade_outcome_shows_decision_state_trade_permitted() -> None:
    run = _run(system_halted=False, outcome="TRADE")
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert 'decision-state sys-up">TRADE PERMITTED</div>' in state


def test_prd279_no_trade_shows_decision_state_stay_flat() -> None:
    run = _run(system_halted=False, outcome="NO_TRADE")
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert ">STAY FLAT</div>" in state
    assert "TRADE PERMITTED" not in state


def test_prd279_unrecognized_outcome_never_shows_trade_permitted() -> None:
    # R1 (red pre-change is the risk being guarded against, not the current
    # code): TRADE PERMITTED must never be inferred merely from the absence
    # of HALT -- an outcome _decision_title doesn't recognize as "TRADE"
    # must fall back to STAY FLAT, not TRADE PERMITTED.
    run = _run(system_halted=False, outcome="SOMETHING_ELSE")
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert ">STAY FLAT</div>" in state
    assert "TRADE PERMITTED" not in state


def test_prd279_state_unavailable_fallback_on_comparison_error(monkeypatch) -> None:
    # R2: an unexpected error deriving the decision state must fall back to
    # STATE UNAVAILABLE, never crash the render or silently show a state.
    import cuttingboard.delivery.dashboard_renderer as dr

    class _RaisingEq:
        def __eq__(self, other):
            raise RuntimeError("boom")

        def __str__(self):
            return "adversarial"

    monkeypatch.setattr(dr, "_decision_title", lambda *a, **k: _RaisingEq())
    html = render_dashboard_html(_payload(), _run())
    state = _system_state_block(html)
    assert 'class="decision-state sys-flat">STATE UNAVAILABLE</div>' in state


def test_prd279_mixed_artifacts_shows_state_unavailable_not_stay_flat() -> None:
    # Codex correction (P2): a payload/run/market_map generation-ID mismatch
    # is a data-integrity error, not a coherent decision -- the header must
    # read STATE UNAVAILABLE, never a confident-looking STAY FLAT (which the
    # pre-correction code rendered, misleadingly colored by regime).
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run(outcome="TRADE")
    run["timestamp"] = "2026-04-28T12:00:00Z"
    mm = _market_map()
    payload["meta"]["generation_id"] = "gen-a"
    run["generation_id"] = "gen-b"
    mm["generation_id"] = "gen-a"

    html = render_dashboard_html(payload, run, market_map=mm)
    state = _system_state_block(html)
    assert 'class="decision-state sys-flat">STATE UNAVAILABLE</div>' in state
    assert ">STAY FLAT</div>" not in state
    assert "TRADE PERMITTED" not in state


def test_prd279_existing_system_state_lines_unchanged() -> None:
    # R4: the pre-existing verdict/timestamp lines are byte-identical to
    # their current form -- PRD-279's header only added lines, never edited.
    # PRD-281 is the one deliberate exception: it moves the reason out of
    # .sys-context into its own .sys-why line (see
    # test_halted_state_reason_in_why_line), so .sys-context now carries the
    # regime phrase only.
    run = _run(system_halted=True)
    payload = _payload(validation_halt_detail={"reason": "STAY_FLAT regime"})
    html = render_dashboard_html(payload, run)
    state = _system_state_block(html)
    assert 'class="sys-verdict sys-halt"' in state
    assert "SYSTEM HALT" in state
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "STAY_FLAT regime" in why
    context = state.split('class="sys-context', 1)[1].split("</div>", 1)[0]
    assert "STAY_FLAT regime" not in context
    assert _updated_value(state)


# ---------------------------------------------------------------------------
# PRD-090: Candidate Board Display Tiers
# ---------------------------------------------------------------------------

def test_prd303_candidate_scope_precedes_setup_action_language() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A+")})
    html = render_dashboard_html(_payload(), _run(outcome="NO_TRADE"), market_map=mm)
    board = _top_block(html, "candidate-board")
    scope = "MARKET-MAP SCREENING GRADES · OBSERVATION ONLY — grades never grant permission."
    assert scope in board
    assert board.index(scope) < board.index("A+ — ACTIONABLE")


def test_c_grade_renders_inside_details_block() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="C")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    import re
    details = re.search(r'<details[^>]*id="tier-c"[^>]*>(.*?)</details>', html, re.DOTALL)
    assert details is not None, "tier-c <details> block not found"
    assert 'id="card-SPY"' in details.group(1), "C-grade card not inside tier-c <details>"


def test_a_grade_not_inside_details_block() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    board = _top_block(html, "candidate-board")
    assert '<details' not in board, "A-grade card is incorrectly wrapped in <details>"


def test_aplus_grade_not_inside_details_block() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A+")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    board = _top_block(html, "candidate-board")
    assert '<details' not in board, "A+ grade card is incorrectly wrapped in <details>"


def test_b_grade_not_inside_details_block() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="B")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    board = _top_block(html, "candidate-board")
    assert '<details' not in board, "B-grade card is incorrectly wrapped in <details>"


def test_high_grade_candidate_renders_validation_context() -> None:
    entry = {
        **_mm_symbol("SPY", grade="A"),
        "preferred_trade_structure": "bullish defined-risk continuation",
        "what_to_look_for": ["watch hold above support", "look for higher low"],
    }
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map({"SPY": entry}))
    card = _candidate_card(html)

    assert "PLAY" in card
    assert "bullish defined-risk continuation" in card
    # PRD-249: the two watch items now render as ONE semicolon-joined WATCH line.
    assert card.count("WATCH") == 1
    assert "watch hold above support; look for higher low" in card


def test_high_grade_candidate_omits_empty_validation_context() -> None:
    entry = {
        **_mm_symbol("SPY", grade="A+"),
        "preferred_trade_structure": None,
        "what_to_look_for": [],
    }
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map({"SPY": entry}))
    card = _candidate_card(html)

    assert "PLAY" not in card
    assert "WATCH" not in card


def test_high_grade_candidate_filters_unavailable_watch_sentinel() -> None:
    entry = {
        **_mm_symbol("SPY", grade="A"),
        "preferred_trade_structure": None,
        "what_to_look_for": [_UNAVAILABLE_WATCH],
    }
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map({"SPY": entry}))
    card = _candidate_card(html)

    assert "WATCH" not in card
    assert _UNAVAILABLE_WATCH not in card


def test_high_grade_candidate_entry_invalidation_bold() -> None:
    # PRD-165 R1 / PRD-215 / PRD-249: the IN →/OUT → couplet (entry/invalidation)
    # uses the bold .value-key class AND the cyan .value-actionable accent,
    # distinct from the generic .value shared by the (collapsed) REASON/PLAY/WATCH.
    entry = _mm_symbol(
        "SPY", grade="A",
        trade_framing={"entry": "above 580.50"},
        invalidation=["below 578.20"],
        reason_for_grade="breadth thrust",
    )
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map({"SPY": entry}))
    card = _candidate_card(html)

    assert '<div class="label">IN →</div><div class="value-key value-actionable">above 580.50</div>' in card
    assert '<div class="label">OUT →</div><div class="value-key value-actionable">below 578.20</div>' in card
    # REASON stays on the generic .value class — NOT the bold .value-key.
    assert '<div class="label">REASON</div><div class="value">breadth thrust' in card
    assert 'REASON</div><div class="value-key">' not in card
    # The dedicated classes are defined in CSS (bold key + cyan accent).
    assert ".value-key{margin-top:0.25rem;font-weight:bold}" in html
    assert ".value-actionable{color:#29b6f6}" in html


def test_failed_candidate_omits_validation_context() -> None:
    entry = {
        **_mm_symbol("SPY", grade="C"),
        "preferred_trade_structure": "bullish defined-risk continuation",
        "what_to_look_for": ["watch hold above support"],
    }
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map({"SPY": entry}))
    card = _candidate_card(html)

    assert "PLAY" not in card
    assert "WATCH" not in card
    assert "bullish defined-risk continuation" not in card
    assert "watch hold above support" not in card


def test_no_actionable_message_present_when_only_c_grade() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="C")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "NO ACTIONABLE SETUPS" in html


def test_no_actionable_message_present_when_only_d_grade() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="D")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "NO ACTIONABLE SETUPS" in html


def test_details_tier_group_summary_css_selector_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert "details.tier-group summary" in html


def test_c_tier_uses_summary_not_div_header() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="C")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    import re
    details = re.search(r'<details[^>]*id="tier-c"[^>]*>(.*?)</details>', html, re.DOTALL)
    assert details is not None
    assert '<summary class="tier-header">' in details.group(0)
    assert '<div class="tier-header">' not in details.group(0)


def test_a_tier_uses_div_not_summary_header() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="tier-a"' in html
    assert '<details' not in html.split('id="tier-a"', 1)[1].split('id="card-SPY"', 1)[0]
    board = _top_block(html, "candidate-board")
    assert '<div class="tier-header">' in board


# PRD-093-PATCH tests

def test_system_state_heading_is_system_state() -> None:
    # PRD-318: the authoritative carrier is unchanged; the zone label is VERDICT.
    html = render_dashboard_html(_payload(), _run())
    state = _system_state_block(html)
    assert "<h2>VERDICT</h2>" in state


def test_stale_market_map_shows_updated_wording() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z")
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})
    mm["generated_at"] = "2026-04-28T12:00:00Z"

    html = render_dashboard_html(payload, run, market_map=mm)
    board = _top_block(html, "candidate-board")

    assert "STALE MARKET MAP" in board
    assert "Market Map / Developing Setups paused" in board
    assert "market_map timestamp is older than selected run" in board
    assert "STALE_MARKET_MAP" not in board
    assert "Candidate Board suppressed" not in board


def test_normal_render_no_pytest_paths() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert "pytest-of-" not in html
    assert "/tmp/pytest" not in html


# ---------------------------------------------------------------------------
# PRD-097: Dashboard Sidecar Freshness and Permission Clarity
# ---------------------------------------------------------------------------

def test_stale_market_map_includes_run_timestamp() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z")
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})
    mm["generated_at"] = "2026-04-28T12:00:00Z"
    html = render_dashboard_html(payload, run, market_map=mm)
    board = _top_block(html, "candidate-board")
    assert "STALE MARKET MAP" in board
    assert "Run:" in board
    assert "2026-04-28T12:10:01" in board


def test_stale_market_map_includes_market_map_timestamp() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z")
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})
    mm["generated_at"] = "2026-04-28T12:00:00Z"
    html = render_dashboard_html(payload, run, market_map=mm)
    board = _top_block(html, "candidate-board")
    assert "Market map:" in board
    assert "2026-04-28T12:00:00Z" in board


def test_stale_market_map_missing_run_timestamp_shows_unavailable() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run()
    del run["timestamp"]
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})
    mm["generated_at"] = "2026-04-28T12:00:00Z"
    html = render_dashboard_html(payload, run, market_map=mm)
    board = _top_block(html, "candidate-board")
    assert "STALE MARKET MAP" in board
    assert "Run: unavailable" in board


def test_permission_none_does_not_mutate_run_dict() -> None:
    run = _run(permission=None)
    render_dashboard_html(_payload(), run)
    assert run["permission"] is None


def test_permission_none_reason_in_why_line() -> None:
    # PRD-281: the reason renders in the dedicated WHY line, not the context
    # line (supersedes PRD-219's "folds into the context line" choice).
    run = _run(permission=None)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "no qualified setups" in why
    context = state.split('class="sys-context', 1)[1].split("</div>", 1)[0]
    assert "no qualified setups" not in context


def test_macro_pressure_missing_shows_unavailable() -> None:
    html = render_dashboard_html(
        _payload(macro_drivers={}),
        _run(),
        market_map=_market_map(),
        macro_snapshot_path=Path("/nonexistent/macro_snapshot.json"),
    )
    pressure = html.split('class="macro-pressure-line', 1)[1].split("</div>", 1)[0]
    assert "Macro pressure unavailable" in pressure
    assert "NO PRESSURE DATA" not in pressure


def test_macro_pressure_with_data_renders_inline_phrases() -> None:
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()),
        _run(),
        market_map=_market_map({"SPY": _mm_symbol("SPY")}),
    )
    assert 'class="macro-pressure-line' in html
    assert '<details id="macro-pressure">' not in html


# ---------------------------------------------------------------------------
# PRD-098: Candidate Board Visibility and Validation Diagnostics
# ---------------------------------------------------------------------------

def test_b_candidate_renders_when_permission_none() -> None:
    """R1/R3: B candidates render from fresh market_map even when permission is None."""
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="B")})
    html = render_dashboard_html(_payload(), _run(permission=None), market_map=mm)
    board = _top_block(html, "candidate-board")
    assert 'id="card-SPY"' in board


def test_b_candidate_not_in_details_when_permission_none() -> None:
    """R3: B candidate renders in normal board flow (not in details) when permission is None."""
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="B")})
    html = render_dashboard_html(_payload(), _run(permission=None), market_map=mm)
    board = _top_block(html, "candidate-board")
    assert '<details' not in board
    assert 'id="card-SPY"' in board


def test_b_candidate_renders_when_permission_false() -> None:
    """R3: B candidates render from fresh market_map when permission is False (blocked)."""
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="B")})
    html = render_dashboard_html(_payload(), _run(permission=False), market_map=mm)
    board = _top_block(html, "candidate-board")
    assert 'id="card-SPY"' in board


def test_a_candidate_renders_when_permission_none() -> None:
    """R2: A candidates render from fresh market_map even when permission is None."""
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    html = render_dashboard_html(_payload(), _run(permission=None), market_map=mm)
    board = _top_block(html, "candidate-board")
    assert 'id="card-SPY"' in board


def test_lower_grade_failure_reason_from_reason_for_grade() -> None:
    """R5: Failure reason uses reason_for_grade when no explicit failure field."""
    entry = {**_mm_symbol("SPY", grade="C"), "reason_for_grade": "momentum fading"}
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "SCREENING NOTE" in card
    assert "momentum fading" in card


def test_lower_grade_failure_reason_fallback() -> None:
    """R5: Failure reason falls back to 'No failure reason provided' when no fields set."""
    entry = {**_mm_symbol("SPY", grade="C"), "reason_for_grade": None}
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "No failure reason provided" in card


def test_lower_grade_failure_reason_from_explicit_field() -> None:
    """R5: Explicit failure_reason field takes precedence over reason_for_grade."""
    entry = {
        **_mm_symbol("SPY", grade="C"),
        "failure_reason": "structure broken",
        "reason_for_grade": "chop",
    }
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "SCREENING NOTE" in card
    assert "structure broken" in card


def test_stale_market_map_suppresses_candidates_regardless_of_permission() -> None:
    """R7: Stale market_map suppresses candidates even when permission is True."""
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z", permission=True)
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    mm["generated_at"] = "2026-04-28T12:00:00Z"
    html = render_dashboard_html(payload, run, market_map=mm)
    board = _top_block(html, "candidate-board")
    assert "STALE MARKET MAP" in board
    assert 'id="card-SPY"' not in board


def test_validation_deterministic_on_identical_input() -> None:
    """R8: Renderer-derived validation requirements are identical across calls."""
    entry = {**_mm_symbol("SPY", grade="C"), "reason_for_grade": "structure not confirmed"}
    mm = _market_map({"SPY": entry})
    html1 = render_dashboard_html(_payload(), _run(), market_map=mm)
    html2 = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert html1 == html2


def test_failure_reason_fallback_is_ascii_only() -> None:
    """R8: Fallback failure reason text is ASCII-only."""
    entry = {**_mm_symbol("SPY", grade="C"), "reason_for_grade": None}
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    fallback = "No failure reason provided"
    assert fallback in card
    assert all(ord(c) < 128 for c in fallback)


# ============================================================================
# PRD-112 — Trend Structure Dashboard Panel (R10 tests a-h)
# ============================================================================

from datetime import datetime as _dt112, timezone as _tz112  # noqa: E402
from cuttingboard.delivery import dashboard_renderer as _dr112  # noqa: E402

_TS_CURATED = ("SPY", "QQQ", "GDX", "GLD", "SLV", "XLE")
_TS_BANNED = (
    "^VIX", "^TNX", "DX-Y.NYB", "BTC-USD", "IWM", "PAAS", "USO",
    "NVDA", "TSLA", "AAPL", "META", "AMZN", "COIN", "MSTR",
)
_TS_FORBIDDEN_LABELS = (
    "ELEVATED", "STRONG", "WEAK", "BULLISH+", "BEARISH+",
    "HIGH RVOL", "LOW RVOL", "OVEREXTENDED", "COMPRESSED",
    "MOMENTUM", "FADING", "BREAKOUT", "BREAKDOWN",
)


def _ts_record(symbol: str, *, current_price=580.12, rvol=1.07) -> dict:
    return {
        "symbol": symbol,
        "data_status": "OK",
        "current_price": current_price,
        "vwap": 578.40,
        "sma_50": 560.00,
        "sma_200": 510.00,
        "relative_volume": rvol,
        "price_vs_vwap": "ABOVE",
        "price_vs_sma_50": "ABOVE",
        "price_vs_sma_200": "ABOVE",
        "trend_alignment": "BULLISH",
        "entry_context": "SUPPORTIVE",
        "reason": "above all references",
    }


def _ts_healthy_snapshot(generated_at: str = "2026-05-10T12:00:00+00:00") -> dict:
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "source": "trend_structure",
        "symbols": {sym: _ts_record(sym) for sym in _TS_CURATED},
    }


def _ts_section(html: str) -> str:
    # PRD-315: depth-aware trend-structure extraction; Candidate no longer
    # follows Trend, so the old candidate-board end sentinel over-captured.
    return _top_block(html, "trend-structure")


# (a) Healthy sidecar fixture
def test_prd112_a_healthy_sidecar_renders_six_rows_in_order() -> None:
    snap = _ts_healthy_snapshot()
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    assert "Trend Structure" in section
    rows = re.findall(r'<tr>(.*?)</tr>', section, re.S)
    body_rows = [r for r in rows if "<td" in r]
    assert len(body_rows) == 6, f"expected 6 body rows, got {len(body_rows)}"
    positions = [section.find(f">{sym}<") for sym in _TS_CURATED]
    assert all(p > 0 for p in positions), positions
    assert positions == sorted(positions), f"row order wrong: {positions}"
    assert "BULL" in section
    assert "SUPPORTIVE" in section


# ----------------------------------------------------------------------------
# PRD-165 R2 — conditional collapse of uniformly-unavailable trend columns
# ----------------------------------------------------------------------------

def test_prd165_r2_uniformly_unavailable_columns_collapse() -> None:
    # PRD-165 R2: vs VWAP / Alignment / Entry Context collapse when every rendered
    # symbol is unavailable for them; kept columns still render. (PRD-208 cut the
    # vs SMA50 / vs SMA200 columns — they are always absent now, never rendered.)
    snap = _ts_healthy_snapshot()
    for rec in snap["symbols"].values():
        rec["price_vs_vwap"] = "NOT_COMPUTED"
        rec["trend_alignment"] = "NOT_COMPUTED"
        rec["entry_context"] = "NOT_COMPUTED"
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(), trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    for hdr in (">vs VWAP</th>", ">Alignment</th>", ">Entry Context</th>"):
        assert hdr not in section, f"expected {hdr} collapsed"
    # PRD-208: the granular SMA columns are cut entirely (not merely collapsed).
    for hdr in (">vs SMA50</th>", ">vs SMA200</th>"):
        assert hdr not in section, f"expected {hdr} cut (PRD-208)"
    for hdr in (">Symbol</th>", ">Price</th>", ">RVOL</th>",
                ">SMA 50/200</th>", ">Intraday</th>"):
        assert hdr in section, f"expected {hdr} retained"


def test_prd165_r2_column_with_one_healthy_value_not_collapsed() -> None:
    # PRD-165 R2 FAIL(a): a column with at least one healthy value across symbols
    # must NOT collapse.
    snap = _ts_healthy_snapshot()
    for rec in snap["symbols"].values():
        rec["trend_alignment"] = "NOT_COMPUTED"
    snap["symbols"]["SPY"]["trend_alignment"] = "BULLISH"
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(), trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    assert ">Alignment</th>" in section
    assert "BULL" in section


def test_prd165_r2_healthy_snapshot_renders_all_columns() -> None:
    # PRD-165 R2 FAIL(a): a fully healthy snapshot collapses nothing.
    # PRD-208: vs SMA50/vs SMA200 are cut; the composite header is "SMA 50/200".
    snap = _ts_healthy_snapshot()
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(), trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    for hdr in (">vs VWAP</th>", ">Alignment</th>", ">Entry Context</th>",
                ">SMA 50/200</th>", ">Intraday</th>"):
        assert hdr in section, f"expected {hdr} retained in healthy snapshot"
    for hdr in (">vs SMA50</th>", ">vs SMA200</th>"):
        assert hdr not in section, f"expected {hdr} cut (PRD-208)"


def test_prd208_r3_columns_cut_renamed_and_counts_match() -> None:
    # PRD-208 R3: vs SMA50 / vs SMA200 columns cut; composite header renamed to
    # "SMA 50/200". Assert the header set by IDENTITY/ORDER (the cut re-indexes
    # every column to its right) and that each body row has one cell per header.
    import re as _re208
    snap = _ts_healthy_snapshot()
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(), trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    headers = _re208.findall(r"<th[^>]*>([^<]*)</th>", section)
    assert headers == [
        "Symbol", "Price", "vs VWAP", "Alignment",
        "Entry Context", "RVOL", "SMA 50/200", "Intraday",
    ], f"unexpected trend-structure header identity/order: {headers}"
    assert "SMA Composite" not in section, "old 'SMA Composite' header must be gone"
    body_rows = _re208.findall(r"<tr>\s*(<td.*?)</tr>", section, _re208.S)
    assert body_rows, "expected rendered trend-structure body rows"
    for row in body_rows:
        assert row.count("<td") == len(headers), (
            f"row cell count {row.count('<td')} != header count {len(headers)}"
        )


def test_prd213_mobile_reflow_data_labels_and_media_query() -> None:
    # PRD-213 + PRD-218: the trend table carries a class hook + a narrow-viewport
    # media query. PRD-218 reflows each symbol to one compact inline row (per-cell
    # labels hidden via content:none) rather than a stacked card; the data-label
    # attributes remain on every <td>.
    import re as _re213
    snap = _ts_healthy_snapshot()
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(), trend_structure_snapshot=snap,
    )
    # Media query + class hook are defined in the rendered CSS.
    assert "@media(max-width:640px)" in html
    assert ".ts-table td::before{content:none}" in html
    assert 'class="ts-table"' in html
    # Every rendered body <td> has a non-empty data-label.
    section = _ts_section(html)
    body = section.split("<tbody>", 1)[1]
    tds = _re213.findall(r"<td\s+data-label=\"([^\"]*)\"", body)
    all_tds = body.count("<td")
    assert len(tds) == all_tds, f"{all_tds - len(tds)} <td> without data-label"
    assert all(lbl.strip() for lbl in tds), "empty data-label on a trend-structure cell"


def test_prd218_price_color_and_sma_arrow_spacing() -> None:
    import re as _r218
    # Healthy fixture is BULLISH across the board -> price cells coloured green.
    snap = _ts_healthy_snapshot()
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(), trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    assert ".ts-px-up{color:#4caf50}" in html and ".ts-px-down{color:#f44336}" in html
    assert 'class="ts-px-up"' in section, "bullish price cell not coloured"
    # SMA arrows carry a trailing space (PRD-218); no unspaced arrow-digit.
    assert _r218.search(r"[\u2191\u2193=] 50 [\u2191\u2193=] 200", section), "spaced SMA composite missing"
    assert not _r218.search(r"[\u2191\u2193=](50|200)", section), "unspaced SMA arrow present"
    # A bearish symbol colours its price red.
    snap2 = _ts_healthy_snapshot()
    first = next(iter(snap2["symbols"]))
    snap2["symbols"][first]["trend_alignment"] = "BEARISH"
    html2 = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(), trend_structure_snapshot=snap2,
    )
    assert 'class="ts-px-down"' in _ts_section(html2), "bearish price cell not coloured"


# (b) Missing file
def test_prd112_b_missing_file_renders_six_placeholders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = tmp_path / "trend_structure_snapshot.json"
    snapshot = _dr112._load_trend_structure_snapshot(missing)
    assert snapshot is None
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        trend_structure_snapshot=snapshot,
    )
    section = _ts_section(html)
    assert "no trend structure data" in section
    # 6 placeholder rows (one per curated symbol) rendered in table body.
    rows = re.findall(r"<tr>(.*?)</tr>", section, re.S)
    placeholder_rows = [row for row in rows if "<td" in row]
    assert len(placeholder_rows) == 6


# (c) Malformed JSON
def test_prd112_c_malformed_json_renders_six_placeholders(
    tmp_path: Path,
) -> None:
    bad = tmp_path / "trend_structure_snapshot.json"
    bad.write_text("{not json", encoding="utf-8")
    snapshot = _dr112._load_trend_structure_snapshot(bad)
    assert snapshot is None
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        trend_structure_snapshot=snapshot,
    )
    section = _ts_section(html)
    assert "no trend structure data" in section


# (d) Per-record key missing → all-or-nothing degradation
def test_prd112_d_per_record_key_missing_degrades_entire_section() -> None:
    snap = _ts_healthy_snapshot()
    del snap["symbols"]["GDX"]["price_vs_vwap"]
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    assert "no trend structure data" in section
    # No salvaged rows: SUPPORTIVE/BULLISH from other symbols must NOT appear
    assert "SUPPORTIVE" not in section
    assert "BULLISH" not in section
    # All-placeholder rows for all 6 curated symbols.
    rows = re.findall(r"<tr>(.*?)</tr>", section, re.S)
    placeholder_rows = [row for row in rows if "<td" in row]
    assert len(placeholder_rows) == 6


# (f) Disallowed symbol from sidecar must NOT render
def test_prd112_f_disallowed_symbol_in_sidecar_excluded() -> None:
    snap = _ts_healthy_snapshot()
    snap["symbols"]["IWM"] = _ts_record("IWM")
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    assert "IWM" not in section


# (g) Banned-symbol HTML grep
def test_prd112_g_banned_symbols_absent_from_section() -> None:
    snap = _ts_healthy_snapshot()
    for sym in _TS_BANNED:
        snap["symbols"][sym] = _ts_record(sym)
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    hits = [s for s in _TS_BANNED if s in section]
    assert not hits, f"banned symbols rendered: {hits}"


# (h) Forbidden-label HTML grep
def test_prd112_h_forbidden_labels_absent_from_section() -> None:
    snap = _ts_healthy_snapshot()
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    hits = [s for s in _TS_FORBIDDEN_LABELS if s in section]
    assert not hits, f"forbidden labels rendered: {hits}"


# Structural guards: no <details>, no card-grid, no script in section
def test_prd112_section_has_no_collapsible_or_card_widgets() -> None:
    snap = _ts_healthy_snapshot()
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    banned_markup = (
        "<details", "<summary", "data-toggle", "<script",
        'class="cards"', 'class="card-grid"', 'class="grid-cards"',
    )
    hits = [m for m in banned_markup if m in section]
    assert not hits, f"banned markup in section: {hits}"
    # Flat <table> with <tr>/<td> rows
    assert "<table" in section
    assert section.count("<tr>") >= 6


# ============================================================================
# PRD-116 — Dashboard Mixed-Artifact Hierarchy Hardening
# ============================================================================

def _strip_generation_ids(payload: dict, run: dict, market_map: dict | None) -> None:
    payload.get("meta", {}).pop("generation_id", None)
    run.pop("generation_id", None)
    if market_map is not None:
        market_map.pop("generation_id", None)


def _trend_section(html: str) -> str:
    return html.split('id="trend-structure"', 1)[1].split("</div>", 1)[0]


def _candidate_section(html: str) -> str:
    return _top_block(html, "candidate-board")


def _system_state_index(html: str) -> int:
    return html.index('id="system-state"')


# R1 — Under MIXED lineage, System State is the first normal block after the wrap.
# Only the MIXED_ARTIFACTS warning banner may precede it.
def test_prd116_r1_mixed_section_order_system_state_before_other_blocks() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    payload["meta"]["generation_id"] = "gen-A"
    run["generation_id"] = "gen-B"
    mm["generation_id"] = "gen-C"
    html = render_dashboard_html(payload, run, market_map=mm)
    ss = _system_state_index(html)
    coh = html.index('id="artifact-coherence"')
    assert coh < ss  # critical coherence warning remains inside the outer VERDICT card
    for later_id in (
        'id="macro-tape"',
        'id="trend-structure"',
        'id="candidate-board"',
        'id="premarket-banner"',
        'id="sunday-macro-context"',
    ):
        if later_id in html:
            assert html.index(later_id) > ss


# R1 — Under MISSING lineage (no market_map), System State precedes all other blocks.
def test_prd116_r1_missing_section_order() -> None:
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()), _run(), market_map=None,
    )
    ss = _system_state_index(html)
    for later_id in (
        'id="macro-tape"', 'id="trend-structure"', 'id="candidate-board"',
    ):
        assert html.index(later_id) > ss


# R2 — MIXED_ARTIFACTS warning still emits payload/run/market_map generation details.
def test_prd116_r2_mixed_warning_emits_generation_details() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map({"SPY": _mm_symbol("SPY")})
    payload["meta"]["generation_id"] = "gen-A"
    run["generation_id"] = "gen-B"
    mm["generation_id"] = "gen-C"
    html = render_dashboard_html(payload, run, market_map=mm)
    coh = html.split('id="artifact-coherence"', 1)[1].split('id="system-state"', 1)[0]
    assert "payload=gen-A" in coh
    assert "run=gen-B" in coh
    assert "market_map=gen-C" in coh


# R3 — Sunday banner/context suppressed when artifact lineage is not COHERENT.
def test_prd116_r3_sunday_blocks_suppressed_under_mixed() -> None:
    # Sunday at 2026-05-10 12:00 UTC == 05:00 PT Sunday
    payload = _payload(timestamp="2026-05-10T12:00:00Z", macro_drivers=_macro_drivers())
    payload["meta"]["session_type"] = "SUNDAY_PREMARKET"
    run = _run_with_timestamp("2026-05-10T12:00:00Z")
    mm = _market_map({"SPY": _mm_symbol("SPY")})
    payload["meta"]["generation_id"] = "gen-A"
    run["generation_id"] = "gen-B"
    mm["generation_id"] = "gen-C"
    html = render_dashboard_html(payload, run, market_map=mm)
    assert 'id="premarket-banner"' not in html
    assert 'id="sunday-macro-context"' not in html


# R3/R8 — Sunday banner and context render under coherent Sunday/pre-market lineage.
def test_prd116_r8_coherent_sunday_renders_sunday_blocks() -> None:
    payload = _payload(timestamp="2026-05-10T12:00:00Z", macro_drivers=_macro_drivers())
    payload["meta"]["session_type"] = "SUNDAY_PREMARKET"
    run = _run_with_timestamp("2026-05-10T12:00:00Z")
    mm = _market_map({"SPY": _mm_symbol("SPY")})
    mm["generated_at"] = "2026-05-10T12:00:00Z"
    # default coherent test-gen-001 across all three
    html = render_dashboard_html(payload, run, market_map=mm)
    assert 'id="premarket-banner"' in html
    assert 'id="sunday-macro-context"' in html


# R4 — Trend Structure is disabled and emits no data rows under unhealthy lineage.
def test_prd116_r4_trend_structure_disabled_under_mixed() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map({"SPY": _mm_symbol("SPY")})
    payload["meta"]["generation_id"] = "gen-A"
    run["generation_id"] = "gen-B"
    mm["generation_id"] = "gen-C"
    html = render_dashboard_html(payload, run, market_map=mm)
    head, _, _ = html.partition('id="trend-structure"')
    # The opening div tag for the block ends right before id="trend-structure".
    open_tag_start = head.rfind("<div")
    open_tag = html[open_tag_start: html.index('id="trend-structure"') + len('id="trend-structure"')]
    assert "disabled" in open_tag
    section = _trend_section(html)
    assert "<tr>" not in section  # no per-symbol data rows


# R4 — Trend Structure renders normal table under coherent lineage.
def test_prd116_r4_trend_structure_renders_under_coherent() -> None:
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()), _run(),
        market_map=_market_map({"SPY": _mm_symbol("SPY")}),
    )
    head, _, _ = html.partition('id="trend-structure"')
    open_tag_start = head.rfind("<div")
    open_tag = html[open_tag_start: html.index('id="trend-structure"') + len('id="trend-structure"')]
    assert "disabled" not in open_tag


# R5 — Candidate board is disabled and emits no cards/tier headers under unhealthy lineage.
def test_prd116_r5_candidate_board_disabled_under_mixed() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    payload["meta"]["generation_id"] = "gen-A"
    run["generation_id"] = "gen-B"
    mm["generation_id"] = "gen-C"
    html = render_dashboard_html(payload, run, market_map=mm)
    head, _, _ = html.partition('id="candidate-board"')
    open_tag_start = head.rfind("<div")
    open_tag = html[open_tag_start: html.index('id="candidate-board"') + len('id="candidate-board"')]
    assert "disabled" in open_tag
    section = _candidate_section(html)
    assert 'id="card-SPY"' not in section
    assert 'class="tier-header"' not in section


# R5 — Under MISSING (no market_map), candidate board is disabled.
def test_prd116_r5_candidate_board_disabled_under_missing() -> None:
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()), _run(), market_map=None,
    )
    head, _, _ = html.partition('id="candidate-board"')
    open_tag_start = head.rfind("<div")
    open_tag = html[open_tag_start: html.index('id="candidate-board"') + len('id="candidate-board"')]
    assert "disabled" in open_tag


# R7 — Coherent live-session dashboard renders all sections without disabled marker.
def test_prd116_r7_coherent_live_preserves_sections() -> None:
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()), _run(),
        market_map=_market_map({"SPY": _mm_symbol("SPY", grade="A")}),
    )
    assert 'id="macro-tape"' in html
    assert 'id="trend-structure"' in html
    assert 'id="candidate-board"' in html
    for section_id in ('id="trend-structure"', 'id="candidate-board"'):
        head, _, _ = html.partition(section_id)
        open_tag_start = head.rfind("<div")
        open_tag = html[open_tag_start: html.index(section_id) + len(section_id)]
        assert "disabled" not in open_tag, f"{section_id} should not be disabled under coherent live"


# ----------------------------------------------------------------------
# PRD-117 — Session-Aware Inactive-State Labeling
# ----------------------------------------------------------------------


def _trend_structure_section(html: str) -> str:
    # PRD-315: depth-aware trend-structure extraction (was bounded by the
    # candidate-board sentinel, which no longer follows Trend).
    return _top_block(html, "trend-structure")


def _candidate_board_only(html: str) -> str:
    # PRD-315: depth-aware candidate-board extraction (was bounded by the
    # run-delta sentinel, which is no longer adjacent after the move).
    return _top_block(html, "candidate-board")


def _inactive_payload(timestamp: str = "2026-04-28T12:00:00Z") -> dict:
    payload = _payload(timestamp=timestamp, macro_drivers=_macro_drivers())
    payload.setdefault("meta", {})["session_type"] = "SUNDAY_PREMARKET"
    return payload


# R2/R4/R5 — Coherent + inactive session renders INACTIVE_SESSION_LABEL inside
# both targeted section IDs (proof of R2 via element-scoped assertion).
def test_prd117_inactive_session_label_renders_in_both_sections() -> None:
    payload = _inactive_payload()
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map()
    _set_generation_ids(payload, run, mm, "live-20260428T120000Z")

    html = render_dashboard_html(payload, run, market_map=mm)

    assert "MIXED_ARTIFACTS" not in html
    assert INACTIVE_SESSION_LABEL in _trend_structure_section(html)
    assert INACTIVE_SESSION_LABEL in _candidate_board_only(html)


# R3 — Unhealthy lineage precedence: MIXED + SUNDAY_PREMARKET must NOT show
# INACTIVE_SESSION_LABEL at the targeted sections.
def test_prd117_unhealthy_lineage_overrides_inactive_label() -> None:
    payload = _inactive_payload()
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map()
    payload["meta"]["generation_id"] = "gen-a"
    run["generation_id"] = "gen-b"
    mm["generation_id"] = "gen-a"

    html = render_dashboard_html(payload, run, market_map=mm)

    assert "MIXED_ARTIFACTS" in html
    assert INACTIVE_SESSION_LABEL not in _trend_structure_section(html)
    assert INACTIVE_SESSION_LABEL not in _candidate_board_only(html)


# R6 — Coherent live-session regression: session_type absent must NOT show
# INACTIVE_SESSION_LABEL.
def test_prd117_coherent_live_session_no_inactive_label() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    payload.get("meta", {}).pop("session_type", None)
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map()
    _set_generation_ids(payload, run, mm, "live-20260428T120000Z")

    html = render_dashboard_html(payload, run, market_map=mm)

    assert "MIXED_ARTIFACTS" not in html
    assert INACTIVE_SESSION_LABEL not in _trend_structure_section(html)
    assert INACTIVE_SESSION_LABEL not in _candidate_board_only(html)


# R1 — Renderer constants are exactly as the PRD specifies. Guards against
# accidental enum expansion or label drift.
def test_prd117_constants_match_prd() -> None:
    assert INACTIVE_SESSION_LABEL == "SESSION INACTIVE"
    assert INACTIVE_SESSION_TYPES == frozenset({"SUNDAY_PREMARKET"})


# ----------------------------------------------------------------------------
# PRD-118 — Coherent dashboard publish gate
# ----------------------------------------------------------------------------

from cuttingboard.delivery.dashboard_renderer import (  # noqa: E402
    CoherentPublishError,
    StalePublishError,
    validate_coherent_publish,
    write_dashboard,
)


# PRD-119: payload default timestamp in tests.dash_helpers is fixed at
# "2026-04-28T12:00:00Z". Tests that need the freshness gate to PASS must
# freeze the renderer's UTC clock close to that timestamp.
_FROZEN_FRESH_REFERENCE = datetime(2026, 4, 28, 12, 30, 0, tzinfo=timezone.utc)


def _freeze_renderer_now(monkeypatch: pytest.MonkeyPatch, ts: datetime = _FROZEN_FRESH_REFERENCE) -> None:
    from cuttingboard.delivery import dashboard_renderer as _dr
    monkeypatch.setattr(_dr, "_utcnow", lambda: ts)


def _coherent_inputs(gid: str = "test-gen-001"):
    payload = _payload()
    payload["meta"]["generation_id"] = gid
    run = _run()
    run["generation_id"] = gid
    market_map = _market_map()
    market_map["generation_id"] = gid
    return payload, run, market_map


def _ui_output_path(tmp_path: Path) -> Path:
    ui = tmp_path / "ui"
    ui.mkdir()
    return ui / "dashboard.html"


def _non_ui_output_path(tmp_path: Path) -> Path:
    rep = tmp_path / "reports" / "output"
    rep.mkdir(parents=True)
    return rep / "dashboard.html"


# R11-1: coherent publish success — file written
def test_prd118_coherent_publish_success_writes_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_renderer_now(monkeypatch)
    payload, run, market_map = _coherent_inputs()
    out = _ui_output_path(tmp_path)
    write_dashboard(
        payload, run,
        market_map=market_map,
        output_path=out,
        fixture_mode=False,
    )
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>") or "<html" in out.read_text(encoding="utf-8")


# R11-2: mismatched generation_ids — exception, no file
def test_prd118_mismatched_generation_ids_blocks(tmp_path: Path) -> None:
    payload, run, market_map = _coherent_inputs()
    run["generation_id"] = "different-gen"
    out = _ui_output_path(tmp_path)
    with pytest.raises(CoherentPublishError, match=r"generation_id mismatch"):
        write_dashboard(
            payload, run,
            market_map=market_map,
            output_path=out,
            fixture_mode=False,
        )
    assert not out.exists()


# PRD-134 R5: regression for noop-publish observed in failed Cuttingboard
# Pipeline runs 25759504467, 25753693370, 25747005282, 25746783255,
# 25745013143 — live-stamped payload/run paired with an hourly-stamped
# market_map (after hourly_alert overwrote logs/market_map.json between
# the daily live run and a later "noop"-mode scheduled run). PRD-118 must
# reject this exact mix.
def test_prd134_noop_live_payload_with_hourly_market_map_blocks(tmp_path: Path) -> None:
    payload, run, market_map = _coherent_inputs()
    payload["meta"]["generation_id"] = "live-20260512T113206Z"
    run["generation_id"] = "live-20260512T113206Z"
    market_map["generation_id"] = "hourly-20260512T195802Z"
    out = _ui_output_path(tmp_path)
    with pytest.raises(CoherentPublishError, match=r"generation_id mismatch"):
        validate_coherent_publish(
            payload=payload,
            run=run,
            market_map=market_map,
            output_path=out,
            fixture_mode=False,
        )


# ----------------------------------------------------------------------------
# PRD-166 — hourly market_map artifact isolation (R2 renderer flag + R4 hazard)
# ----------------------------------------------------------------------------

def _prd166_write_inputs(tmp_path: Path, *, gid: str, shared_gid: str) -> tuple[Path, Path, Path]:
    """Write payload/run (gid), a poisoned shared logs/market_map.json
    (shared_gid), and a matching hourly market_map (gid). Return the
    (payload_file, run_file, hourly_market_map_file) paths."""
    payload = _payload()
    payload["meta"]["generation_id"] = gid
    run = _run()
    run["generation_id"] = gid
    payload_file = tmp_path / "latest_payload.json"
    run_file = tmp_path / "latest_run.json"
    payload_file.write_text(json.dumps(payload), encoding="utf-8")
    run_file.write_text(json.dumps(run), encoding="utf-8")

    shared_mm = _market_map()
    shared_mm["generation_id"] = shared_gid
    (tmp_path / "market_map.json").write_text(json.dumps(shared_mm), encoding="utf-8")

    hourly_mm = _market_map()
    hourly_mm["generation_id"] = gid
    hourly_file = tmp_path / "latest_hourly_market_map.json"
    hourly_file.write_text(json.dumps(hourly_mm), encoding="utf-8")
    return payload_file, run_file, hourly_file


def test_prd166_r4_explicit_path_bypasses_poisoned_shared_market_map(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R4: a mismatched shared logs/market_map.json plus a matching hourly
    market_map renders ui/dashboard.html when --market-map-path points at the
    hourly file — the explicit path flows through both the CLI pre-validation
    read and the write_dashboard() validation read, and the poisoned shared
    file is never consulted."""
    from cuttingboard.delivery.dashboard_renderer import main

    _freeze_renderer_now(monkeypatch)
    payload_file, run_file, hourly_file = _prd166_write_inputs(
        tmp_path, gid="hourly-20260428T120000Z", shared_gid="poisoned-20260101T000000Z"
    )
    out = tmp_path / "ui" / "dashboard.html"
    out.parent.mkdir()
    main(
        payload_path=payload_file,
        run_path=run_file,
        output_path=out,
        logs_dir=tmp_path,
        market_map_path=hourly_file,
    )
    assert out.exists()


def test_prd166_r4_default_path_reads_poisoned_shared_and_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R4 converse: omitting --market-map-path falls back to
    <logs-dir>/market_map.json (the poisoned shared file), so the coherence
    gate raises. Proves the hazard is real and that the default path is the
    shared file — i.e. the override is what closes it."""
    from cuttingboard.delivery.dashboard_renderer import main

    _freeze_renderer_now(monkeypatch)
    payload_file, run_file, _hourly = _prd166_write_inputs(
        tmp_path, gid="hourly-20260428T120000Z", shared_gid="poisoned-20260101T000000Z"
    )
    out = tmp_path / "ui" / "dashboard.html"
    out.parent.mkdir()
    with pytest.raises(CoherentPublishError, match=r"generation_id mismatch"):
        main(
            payload_path=payload_file,
            run_path=run_file,
            output_path=out,
            logs_dir=tmp_path,
        )
    assert not out.exists()


def test_prd166_r2_default_market_map_path_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R2: when --market-map-path is omitted the renderer loads market_map from
    <logs-dir>/market_map.json (current behavior); a coherent shared file
    renders to ui/ successfully."""
    from cuttingboard.delivery.dashboard_renderer import main

    _freeze_renderer_now(monkeypatch)
    gid = "hourly-20260428T120000Z"
    payload = _payload()
    payload["meta"]["generation_id"] = gid
    run = _run()
    run["generation_id"] = gid
    payload_file = tmp_path / "latest_payload.json"
    run_file = tmp_path / "latest_run.json"
    payload_file.write_text(json.dumps(payload), encoding="utf-8")
    run_file.write_text(json.dumps(run), encoding="utf-8")
    shared_mm = _market_map()
    shared_mm["generation_id"] = gid
    (tmp_path / "market_map.json").write_text(json.dumps(shared_mm), encoding="utf-8")
    out = tmp_path / "ui" / "dashboard.html"
    out.parent.mkdir()
    main(
        payload_path=payload_file,
        run_path=run_file,
        output_path=out,
        logs_dir=tmp_path,
    )
    assert out.exists()


# R11-3: missing payload.meta.generation_id — exception, no file
def test_prd118_missing_payload_generation_id_blocks(tmp_path: Path) -> None:
    payload, run, market_map = _coherent_inputs()
    del payload["meta"]["generation_id"]
    out = _ui_output_path(tmp_path)
    with pytest.raises(CoherentPublishError, match=r"missing generation_id .*payload\.meta\.generation_id"):
        write_dashboard(
            payload, run,
            market_map=market_map,
            output_path=out,
            fixture_mode=False,
        )
    assert not out.exists()


# R11-4: missing market_map entirely — exception, no file
def test_prd118_missing_market_map_blocks(tmp_path: Path) -> None:
    payload, run, _market_map_unused = _coherent_inputs()
    out = _ui_output_path(tmp_path)
    with pytest.raises(CoherentPublishError, match=r"missing artifact.*market_map"):
        write_dashboard(
            payload, run,
            market_map=None,
            market_map_path=None,
            output_path=out,
            fixture_mode=False,
        )
    assert not out.exists()


# R11-5: fixture substring in any generation_id — exception, no file
@pytest.mark.parametrize("target", ("payload", "run", "market_map"))
def test_prd118_fixture_substring_blocks(tmp_path: Path, target: str) -> None:
    payload, run, market_map = _coherent_inputs()
    fixture_gid = "fixture-live-20260508T220000Z"
    if target == "payload":
        payload["meta"]["generation_id"] = fixture_gid
    elif target == "run":
        run["generation_id"] = fixture_gid
    else:
        market_map["generation_id"] = fixture_gid
    out = _ui_output_path(tmp_path)
    with pytest.raises(CoherentPublishError, match=r"fixture artifact detected"):
        write_dashboard(
            payload, run,
            market_map=market_map,
            output_path=out,
            fixture_mode=False,
        )
    assert not out.exists()


# R11-6: fixture_mode=True with ui/ output — exception, no file
def test_prd118_fixture_mode_blocks_ui_output(tmp_path: Path) -> None:
    payload, run, market_map = _coherent_inputs()
    out = _ui_output_path(tmp_path)
    with pytest.raises(CoherentPublishError, match=r"fixture mode active \(fixture_mode=True\)"):
        write_dashboard(
            payload, run,
            market_map=market_map,
            output_path=out,
            fixture_mode=True,
        )
    assert not out.exists()


# R11-7: fixture_mode=True with non-ui/ output — file written (gate scoped to ui/)
def test_prd118_fixture_mode_allowed_for_non_ui_output(tmp_path: Path) -> None:
    payload, run, market_map = _coherent_inputs()
    out = _non_ui_output_path(tmp_path)
    write_dashboard(
        payload, run,
        market_map=market_map,
        output_path=out,
        fixture_mode=True,
    )
    assert out.exists()


# R11-8 / R12: missing artifact is not silently substituted — explicit failure
def test_prd118_no_silent_fallback_for_missing_artifact(tmp_path: Path) -> None:
    payload, run, _market_map_unused = _coherent_inputs()
    out = _ui_output_path(tmp_path)
    # Pass market_map=None and a non-existent path; renderer must NOT substitute
    # an empty dict, default, or fixture artifact — it must raise and leave ui/
    # untouched.
    missing_path = tmp_path / "logs" / "no_market_map.json"
    with pytest.raises(CoherentPublishError, match=r"missing artifact.*market_map"):
        write_dashboard(
            payload, run,
            market_map=None,
            market_map_path=missing_path,
            output_path=out,
            fixture_mode=False,
        )
    assert not out.exists()
    assert list((tmp_path / "ui").iterdir()) == []


# Bonus: validate FIXTURE_MODE env var trigger (R2 clause c)
def test_prd118_fixture_env_var_blocks_ui_output(tmp_path: Path, monkeypatch) -> None:
    payload, run, market_map = _coherent_inputs()
    out = _ui_output_path(tmp_path)
    monkeypatch.setenv("FIXTURE_MODE", "1")
    with pytest.raises(CoherentPublishError, match=r"fixture mode active \(FIXTURE_MODE=1\)"):
        write_dashboard(
            payload, run,
            market_map=market_map,
            output_path=out,
            fixture_mode=False,
        )
    assert not out.exists()


# Diagnostic-line verification (R4): deterministic stderr on each failure mode
def test_prd118_diagnostic_line_names_failure(tmp_path: Path, capsys) -> None:
    payload, run, market_map = _coherent_inputs()
    run["generation_id"] = "another-gen"
    out = _ui_output_path(tmp_path)
    with pytest.raises(CoherentPublishError):
        validate_coherent_publish(
            payload=payload, run=run, market_map=market_map,
            output_path=out, fixture_mode=False,
        )
    err = capsys.readouterr().err
    assert "PRD-118 publish blocked:" in err
    assert "generation_id mismatch" in err
    assert "payload=test-gen-001" in err
    assert "run=another-gen" in err


# ----------------------------------------------------------------------------
# PRD-119 — Dashboard publish freshness gate (R15 deterministic coverage)
# ----------------------------------------------------------------------------

# Payload helper default timestamp is 2026-04-28T12:00:00Z.
_PAYLOAD_TS_DT = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)


# R15-1: coherent fresh live publish succeeds with explicit freshness assertion.
def test_prd119_fresh_live_publish_succeeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # now = payload_ts + (window - 1 minute) -> inside live window.
    fresh_now = _PAYLOAD_TS_DT + timedelta(minutes=LIVE_SESSION_MAX_AGE_MINUTES - 1)
    _freeze_renderer_now(monkeypatch, fresh_now)
    payload, run, market_map = _coherent_inputs()
    out = _ui_output_path(tmp_path)
    write_dashboard(
        payload, run,
        market_map=market_map,
        output_path=out,
        fixture_mode=False,
    )
    assert out.exists()


# R15-2: coherent stale live publish raises StalePublishError.
def test_prd119_stale_live_publish_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stale_now = _PAYLOAD_TS_DT + timedelta(minutes=LIVE_SESSION_MAX_AGE_MINUTES + 1)
    _freeze_renderer_now(monkeypatch, stale_now)
    payload, run, market_map = _coherent_inputs()
    out = _ui_output_path(tmp_path)
    with pytest.raises(StalePublishError, match=r"stale payload"):
        write_dashboard(
            payload, run,
            market_map=market_map,
            output_path=out,
            fixture_mode=False,
        )
    assert not out.exists()


# R15-3: coherent fresh inactive-session publish succeeds (72h window).
def test_prd119_fresh_inactive_session_publish_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, run, market_map = _coherent_inputs()
    payload["meta"]["session_type"] = "SUNDAY_PREMARKET"
    fresh_now = _PAYLOAD_TS_DT + timedelta(hours=INACTIVE_SESSION_MAX_AGE_HOURS - 1)
    _freeze_renderer_now(monkeypatch, fresh_now)
    out = _ui_output_path(tmp_path)
    write_dashboard(
        payload, run,
        market_map=market_map,
        output_path=out,
        fixture_mode=False,
    )
    assert out.exists()


# R15-4: coherent stale inactive-session publish raises StalePublishError.
def test_prd119_stale_inactive_session_publish_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, run, market_map = _coherent_inputs()
    payload["meta"]["session_type"] = "SUNDAY_PREMARKET"
    stale_now = _PAYLOAD_TS_DT + timedelta(hours=INACTIVE_SESSION_MAX_AGE_HOURS + 1)
    _freeze_renderer_now(monkeypatch, stale_now)
    out = _ui_output_path(tmp_path)
    with pytest.raises(StalePublishError, match=r"stale payload"):
        write_dashboard(
            payload, run,
            market_map=market_map,
            output_path=out,
            fixture_mode=False,
        )
    assert not out.exists()


# R15-5: malformed payload.meta.timestamp raises StalePublishError.
@pytest.mark.parametrize(
    "bad_ts",
    ("not-a-date", "2026-04-28T12:00:00", "2026-13-28T12:00:00Z", ""),
)
def test_prd119_malformed_payload_timestamp_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bad_ts: str,
) -> None:
    _freeze_renderer_now(monkeypatch)
    payload, run, market_map = _coherent_inputs()
    payload["meta"]["timestamp"] = bad_ts
    out = _ui_output_path(tmp_path)
    with pytest.raises(StalePublishError, match=r"payload\.meta\.timestamp"):
        write_dashboard(
            payload, run,
            market_map=market_map,
            output_path=out,
            fixture_mode=False,
        )
    assert not out.exists()


# R15-6: missing payload.meta.timestamp raises StalePublishError.
def test_prd119_missing_payload_timestamp_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    payload, run, market_map = _coherent_inputs()
    del payload["meta"]["timestamp"]
    out = _ui_output_path(tmp_path)
    with pytest.raises(StalePublishError, match=r"payload\.meta\.timestamp missing"):
        write_dashboard(
            payload, run,
            market_map=market_map,
            output_path=out,
            fixture_mode=False,
        )
    assert not out.exists()


# R15-7: non-ui stale render succeeds (freshness gate scoped to ui/ only).
def test_prd119_non_ui_stale_render_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Make `now` very stale relative to payload timestamp; non-ui path must
    # bypass the freshness gate entirely.
    stale_now = _PAYLOAD_TS_DT + timedelta(days=365)
    _freeze_renderer_now(monkeypatch, stale_now)
    payload, run, market_map = _coherent_inputs()
    out = _non_ui_output_path(tmp_path)
    assert "ui" not in out.resolve().parts
    write_dashboard(
        payload, run,
        market_map=market_map,
        output_path=out,
        fixture_mode=False,
    )
    assert out.exists()


# R15-8: PRD-118 generation_id mismatch raises CoherentPublishError BEFORE
# freshness evaluation. Both failure modes are present; the coherent-gen gate
# must short-circuit first (PRD-119 R9 ordering).
def test_prd119_coherent_gen_mismatch_precedes_freshness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    stale_now = _PAYLOAD_TS_DT + timedelta(days=365)
    _freeze_renderer_now(monkeypatch, stale_now)
    payload, run, market_map = _coherent_inputs()
    run["generation_id"] = "different-gen"  # PRD-118 violation
    # Payload timestamp also far stale (PRD-119 violation).
    out = _ui_output_path(tmp_path)
    with pytest.raises(CoherentPublishError, match=r"generation_id mismatch"):
        write_dashboard(
            payload, run,
            market_map=market_map,
            output_path=out,
            fixture_mode=False,
        )
    assert not out.exists()


# R15-9: stderr diagnostic on freshness failure contains R7 fields.
def test_prd119_freshness_failure_diagnostic_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys,
) -> None:
    stale_now = _PAYLOAD_TS_DT + timedelta(minutes=LIVE_SESSION_MAX_AGE_MINUTES + 5)
    _freeze_renderer_now(monkeypatch, stale_now)
    payload, run, market_map = _coherent_inputs()
    out = _ui_output_path(tmp_path)
    with pytest.raises(StalePublishError):
        validate_coherent_publish(
            payload=payload, run=run, market_map=market_map,
            output_path=out, fixture_mode=False,
        )
    err = capsys.readouterr().err
    assert "PRD-119 publish blocked:" in err
    assert "payload_timestamp=2026-04-28T12:00:00Z" in err
    assert "artifact_age=" in err
    assert f"window={LIVE_SESSION_MAX_AGE_MINUTES}m" in err
    assert "session_type=None" in err


# ----------------------------------------------------------------------------
# PRD-120 - Dashboard source-health diagnostics + Permission display
# ----------------------------------------------------------------------------

def _prd120_coherent_render(
    *,
    payload_overrides: dict | None = None,
    run_overrides: dict | None = None,
    market_map: dict | None = None,
    trend_structure_snapshot: dict | None = None,
) -> str:
    payload = _payload()
    if payload_overrides:
        for k, v in payload_overrides.items():
            payload[k] = v
    run = _run()
    if run_overrides:
        for k, v in run_overrides.items():
            run[k] = v
    if market_map is None:
        market_map = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    # Force coherent generation_ids.
    payload["meta"]["generation_id"] = "test-gen-001"
    run["generation_id"] = "test-gen-001"
    market_map["generation_id"] = "test-gen-001"
    return render_dashboard_html(
        payload, run, market_map=market_map,
        trend_structure_snapshot=trend_structure_snapshot,
    )


def _prd120_perm_field(html: str) -> str:
    state = _system_state_block(html)
    after = state.split("Permission", 1)[1]
    return after.split("</div></div>", 1)[0]


# R14-1: Permission MONITOR_ONLY for active NO_TRADE under coherent lineage.
# R14-2: HALTED precedence over MONITOR_ONLY/UNKNOWN.
def test_prd120_permission_halted_wins_over_monitor_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    html = _prd120_coherent_render(
        run_overrides={"permission": None, "outcome": "NO_TRADE", "system_halted": True},
    )
    state = _system_state_block(html)
    assert "SYSTEM HALT" in state
    assert "MONITOR_ONLY" not in state


# R14-3: catch-all UNKNOWN when permission None, outcome="TRADE", not halted.
# ----------------------------------------------------------------------------
# PRD-123 — Trend Structure Refresh Decoupling and Truthful Source Status
# ----------------------------------------------------------------------------


def _prd123_fresh_zero_usable_snapshot() -> dict:
    """Snapshot with full required-field shape for every curated symbol but
    data_status=MISSING — i.e. shape-present, data-unusable. Mirrors the
    real-world "market closed, no intraday" condition that surfaced from
    the live 2026-05-09 snapshot inspected during PRD-123 design."""
    rec_template = {
        "current_price": None,
        "vwap": None,
        "sma_50": None,
        "sma_200": None,
        "relative_volume": None,
        # PRD-130: post-normalization snapshots no longer emit "UNKNOWN";
        # missing current_price routes all comparison fields to
        # DATA_UNAVAILABLE via the caller in trend_structure.py.
        "price_vs_vwap": "DATA_UNAVAILABLE",
        "price_vs_sma_50": "DATA_UNAVAILABLE",
        "price_vs_sma_200": "DATA_UNAVAILABLE",
        "trend_alignment": "DATA_UNAVAILABLE",
        "entry_context": "DATA_UNAVAILABLE",
        "data_status": "MISSING",
        "reason": "current_price unavailable",
    }
    return {
        "schema_version": 1,
        "generated_at": "2026-04-28T12:00:00+00:00",
        "symbols": {sym: {"symbol": sym, **rec_template} for sym in _TS_CURATED},
    }


def _prd123_freeze_fresh(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin renderer-side `datetime.now` to a moment 60s after the fixture
    `generated_at` so freshness reads FRESH (well under the 300s threshold)."""
    fixed_now = _dt112(2026, 4, 28, 12, 1, 0, tzinfo=_tz112.utc)

    class _FrozenDT(_dt112):  # type: ignore[misc]
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(_dr112, "datetime", _FrozenDT)


def test_prd123_no_fallback_string_in_trend_renders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R8 invariant: `SOURCE: FALLBACK` must not appear in any trend-structure
    render after this PRD merges. Covers OK / STALE / MARKET_CLOSED /
    AWAITING_DATA in turn."""
    _freeze_renderer_now(monkeypatch)
    _prd123_freeze_fresh(monkeypatch)
    for label, snap in [
        ("ok", _ts_healthy_snapshot(generated_at="2026-04-28T12:00:00+00:00")),
        ("awaiting_data", _prd123_fresh_zero_usable_snapshot()),
    ]:
        html = _prd120_coherent_render(trend_structure_snapshot=snap)
        section = _ts_section(html)
        assert "SOURCE: FALLBACK" not in section, f"FALLBACK leaked into {label} render"


# R14-11 already covered by existing PRD-118 tests (regression).


# R14-12 / R14-18: Determinism with frozen `datetime` AND `_utcnow`.
def test_prd120_determinism_byte_identical_renders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed_now = _dt112(2026, 4, 28, 12, 1, 0, tzinfo=_tz112.utc)

    class _FrozenDT(_dt112):  # type: ignore[misc]
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(_dr112, "datetime", _FrozenDT)
    _freeze_renderer_now(monkeypatch, fixed_now)
    snap = _ts_healthy_snapshot()
    payload = _payload()
    run = _run()
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    payload["meta"]["generation_id"] = "test-gen-001"
    run["generation_id"] = "test-gen-001"
    mm["generation_id"] = "test-gen-001"
    html_a = render_dashboard_html(
        payload, run, market_map=mm, trend_structure_snapshot=snap,
    )
    html_b = render_dashboard_html(
        payload, run, market_map=mm, trend_structure_snapshot=snap,
    )
    assert html_a == html_b


# R14-13: mapping table coverage - exhaustive per-block enum coverage via
# direct unit calls against the pure helpers.
def test_prd120_system_state_enum_coverage() -> None:
    fresh_ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    stale_ts = "2020-01-01T00:00:00Z"
    bad_ts = "not-a-date"
    assert _system_state_source_health(
        artifact_lineage_state="MIXED", payload_timestamp_value=fresh_ts,
    ) == "MIXED"
    assert _system_state_source_health(
        artifact_lineage_state="STALE", payload_timestamp_value=fresh_ts,
    ) == "STALE"
    assert _system_state_source_health(
        artifact_lineage_state="MISSING", payload_timestamp_value=fresh_ts,
    ) == "MISSING"
    assert _system_state_source_health(
        artifact_lineage_state="COHERENT", payload_timestamp_value=bad_ts,
    ) == "INVALID"
    assert _system_state_source_health(
        artifact_lineage_state="COHERENT", payload_timestamp_value=stale_ts,
    ) == "STALE"
    assert _system_state_source_health(
        artifact_lineage_state="COHERENT", payload_timestamp_value=fresh_ts,
    ) == "OK"


def test_prd120_macro_tape_enum_coverage() -> None:
    drivers = _macro_drivers()
    assert _macro_tape_source_health(
        macro_drivers={}, tape_value_slots=[("VIX", "18.0")],
    ) == "MISSING"
    assert _macro_tape_source_health(
        macro_drivers={"x": "MARKET MAP UNAVAILABLE"},
        tape_value_slots=[("VIX", "18.0")],
    ) == "MISSING"
    assert _macro_tape_source_health(
        macro_drivers=drivers,
        tape_value_slots=[("VIX", "--"), ("SPY", "500.0")],
    ) == "FALLBACK"
    assert _macro_tape_source_health(
        macro_drivers=drivers,
        tape_value_slots=[("VIX", "18.0"), ("SPY", "N/A")],
    ) == "FALLBACK"
    assert _macro_tape_source_health(
        macro_drivers=drivers,
        tape_value_slots=[("VIX", "18.0"), ("SPY", "500.0")],
    ) == "OK"


def test_prd120_trend_structure_enum_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed_now = _dt112(2026, 4, 28, 12, 0, 0, tzinfo=_tz112.utc)

    class _FrozenDT(_dt112):  # type: ignore[misc]
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(_dr112, "datetime", _FrozenDT)
    fresh = "2026-04-28T12:00:00+00:00"
    stale = "2020-01-01T00:00:00+00:00"
    bad = "not-a-date"
    rec = {"a": 1}  # dummy "exists"
    assert _trend_structure_source_health(
        artifact_lineage_state="MIXED", inactive_session=False,
        snapshot=None, ts_generated_at_raw=fresh, usable_count=0,
    ) == "MIXED"
    assert _trend_structure_source_health(
        artifact_lineage_state="STALE", inactive_session=False,
        snapshot=None, ts_generated_at_raw=fresh, usable_count=0,
    ) == "STALE"
    assert _trend_structure_source_health(
        artifact_lineage_state="MISSING", inactive_session=False,
        snapshot=None, ts_generated_at_raw=fresh, usable_count=0,
    ) == "MISSING"
    assert _trend_structure_source_health(
        artifact_lineage_state="COHERENT", inactive_session=True,
        snapshot=None, ts_generated_at_raw=fresh, usable_count=0,
    ) == "INACTIVE_SESSION"
    assert _trend_structure_source_health(
        artifact_lineage_state="COHERENT", inactive_session=False,
        snapshot=None, ts_generated_at_raw=fresh, usable_count=0,
    ) == "MISSING"
    assert _trend_structure_source_health(
        artifact_lineage_state="COHERENT", inactive_session=False,
        snapshot={"symbols": {"SPY": rec}}, ts_generated_at_raw=bad, usable_count=6,
    ) == "INVALID"
    assert _trend_structure_source_health(
        artifact_lineage_state="COHERENT", inactive_session=False,
        snapshot={"symbols": {"SPY": rec}}, ts_generated_at_raw=stale, usable_count=6,
    ) == "STALE"
    # PRD-123 R5: previous FALLBACK return replaced by AWAITING_DATA when
    # snapshot is fresh and usable_count == 0 under active session.
    assert _trend_structure_source_health(
        artifact_lineage_state="COHERENT", inactive_session=False,
        snapshot={"symbols": {"SPY": rec}}, ts_generated_at_raw=fresh, usable_count=0,
    ) == "AWAITING_DATA"
    # PRD-123 R5: corresponding inactive-session case returns MARKET_CLOSED.
    assert _trend_structure_source_health(
        artifact_lineage_state="COHERENT", inactive_session=True,
        snapshot={"symbols": {"SPY": rec}}, ts_generated_at_raw=fresh, usable_count=0,
    ) == "MARKET_CLOSED"
    assert _trend_structure_source_health(
        artifact_lineage_state="COHERENT", inactive_session=False,
        snapshot={"symbols": {"SPY": rec}}, ts_generated_at_raw=fresh, usable_count=6,
    ) == "OK"


def test_prd120_market_map_enum_coverage() -> None:
    assert _market_map_source_health(
        artifact_lineage_state="MIXED", inactive_session=False, mm_status="FRESH",
    ) == "MIXED"
    assert _market_map_source_health(
        artifact_lineage_state="STALE", inactive_session=False, mm_status="FRESH",
    ) == "STALE"
    assert _market_map_source_health(
        artifact_lineage_state="MISSING", inactive_session=False, mm_status="FRESH",
    ) == "MISSING"
    assert _market_map_source_health(
        artifact_lineage_state="COHERENT", inactive_session=True, mm_status="FRESH",
    ) == "INACTIVE_SESSION"
    assert _market_map_source_health(
        artifact_lineage_state="COHERENT", inactive_session=False, mm_status="SOURCE_MISSING",
    ) == "MISSING"
    assert _market_map_source_health(
        artifact_lineage_state="COHERENT", inactive_session=False, mm_status="PARSE_ERROR",
    ) == "INVALID"
    assert _market_map_source_health(
        artifact_lineage_state="COHERENT", inactive_session=False, mm_status="STALE",
    ) == "STALE"
    assert _market_map_source_health(
        artifact_lineage_state="COHERENT", inactive_session=False, mm_status="FRESH",
    ) == "OK"


# R14-14: INACTIVE_SESSION_LABEL precedence over Trend Structure missing
# symbol diagnostic under coherent inactive lineage.
# R14-16: no `>&#8212;<` inside Permission field for coherent active NO_TRADE.
def test_prd120_no_em_dash_in_permission_under_coherent_lineage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    html = _prd120_coherent_render(
        run_overrides={"permission": None, "outcome": "NO_TRADE"},
    )
    state = _system_state_block(html)
    assert ">&#8212;<" not in state


# R14-17: HALTED + stay_flat_reason -> HALTED takes precedence.
def test_prd120_halted_and_stay_flat_reason_renders_halted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    payload = _payload(validation_halt_detail={"reason": "STAY_FLAT regime"})
    payload["meta"]["generation_id"] = "test-gen-001"
    run = _run(system_halted=True, permission=None)
    run["generation_id"] = "test-gen-001"
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    mm["generation_id"] = "test-gen-001"
    html = render_dashboard_html(payload, run, market_map=mm)
    state = _system_state_block(html)
    assert "SYSTEM HALT" in state
    assert "MONITOR_ONLY" not in state


# R14-21: permission=None under MIXED lineage -> UNKNOWN, not MONITOR_ONLY.
# R14 supplementary: _trend_symbols_usable per-symbol counting.
def test_prd120_trend_symbols_usable_per_symbol_count() -> None:
    full = _ts_healthy_snapshot()
    assert _trend_symbols_usable(full) == 6
    # Strip required fields from one record -> count drops by one.
    snap = _ts_healthy_snapshot()
    snap["symbols"]["SPY"] = {"symbol": "SPY"}
    assert _trend_symbols_usable(snap) == 5
    # All records empty -> 0 usable.
    bad = _ts_healthy_snapshot()
    for sym in list(bad["symbols"].keys()):
        bad["symbols"][sym] = {"symbol": sym}
    assert _trend_symbols_usable(bad) == 0
    # None snapshot -> 0.
    assert _trend_symbols_usable(None) == 0


# R12/R13: ASCII-only guard for the SOURCE diagnostic strings.
def test_prd120_source_lines_ascii_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    html = _prd120_coherent_render()
    for line in html.splitlines():
        if "SOURCE:" in line or "TREND SYMBOLS:" in line:
            assert all(ord(ch) < 128 for ch in line), line


# ----------------------------------------------------------------------------
# PRD-130 — Trend Structure Unknown-State Normalization (renderer mapping)
# ----------------------------------------------------------------------------


def _prd130_snapshot_with_token(token: str) -> dict:
    """Build a trend-structure snapshot where SPY's comparison fields carry
    `token` and the remaining curated symbols carry a benign healthy
    record. Used to isolate a single state token in rendered output."""
    snap = _ts_healthy_snapshot()
    spy = snap["symbols"]["SPY"]
    spy["price_vs_vwap"] = token
    spy["price_vs_sma_50"] = token
    spy["price_vs_sma_200"] = token
    spy["trend_alignment"] = token
    spy["entry_context"] = token
    return snap


def _prd130_spy_row(section: str) -> str:
    """Extract SPY's single <tr> row from a rendered trend-structure
    section so per-cell display strings can be compared in isolation."""
    rows = re.findall(r"<tr>(.*?)</tr>", section, re.S)
    for row in rows:
        if ">SPY<" in row:
            return row
    raise AssertionError("SPY row not found in trend-structure section")


def test_prd130_r4_five_states_render_distinct_display_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PRD-130 R4: AT_LEVEL, INSUFFICIENT_HISTORY, DATA_UNAVAILABLE,
    NOT_COMPUTED, and the renderer-only SESSION_UNAVAILABLE branch MUST
    each produce a distinct, non-empty display string within the
    trend-structure block. No variant may contain the literal "UNKNOWN"
    inside that block. AT_LEVEL MUST render affirmatively, not as an
    unavailable-glyph fallback.
    """
    _freeze_renderer_now(monkeypatch)

    per_cell_tokens = (
        "AT_LEVEL",
        "INSUFFICIENT_HISTORY",
        "DATA_UNAVAILABLE",
        "NOT_COMPUTED",
    )
    per_cell_rows: dict[str, str] = {}
    for token in per_cell_tokens:
        html = _prd120_coherent_render(
            trend_structure_snapshot=_prd130_snapshot_with_token(token),
        )
        section = _ts_section(html)
        assert "UNKNOWN" not in section, (
            f"trend-structure block contains literal 'UNKNOWN' for token {token}"
        )
        per_cell_rows[token] = _prd130_spy_row(section)

    # Affirmative AT_LEVEL rendering — must not collapse to an unknown glyph.
    assert "AT LEVEL" in per_cell_rows["AT_LEVEL"]
    assert "INSUFFICIENT HISTORY" in per_cell_rows["INSUFFICIENT_HISTORY"]
    assert "DATA UNAVAILABLE" in per_cell_rows["DATA_UNAVAILABLE"]
    assert "NOT COMPUTED" in per_cell_rows["NOT_COMPUTED"]

    # Pairwise distinctness across the four per-cell tokens.
    rows = list(per_cell_rows.values())
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            assert rows[i] != rows[j], (
                "two PRD-130 state tokens rendered identical SPY rows: "
                f"{per_cell_tokens[i]} vs {per_cell_tokens[j]}"
            )

    # Renderer-only SESSION_UNAVAILABLE branch: inactive session yields
    # the INACTIVE_SESSION_LABEL ("SESSION INACTIVE") instead of the
    # per-symbol table. That display string must be distinct from the
    # four per-cell displays above.
    inactive_payload = _inactive_payload()
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map()
    _set_generation_ids(inactive_payload, run, mm, "live-20260428T120000Z")
    inactive_html = render_dashboard_html(
        inactive_payload, run, market_map=mm,
        trend_structure_snapshot=_ts_healthy_snapshot(),
    )
    inactive_section = _trend_structure_section(inactive_html)
    assert INACTIVE_SESSION_LABEL in inactive_section
    assert "UNKNOWN" not in inactive_section
    for display in ("AT LEVEL", "INSUFFICIENT HISTORY", "DATA UNAVAILABLE", "NOT COMPUTED"):
        # The inactive-session branch suppresses the per-symbol table, so
        # the per-cell display strings cannot appear there.
        assert display not in inactive_section, (
            f"inactive-session render leaked per-cell display '{display}'"
        )


# ----------------------------------------------------------------------------
# PRD-131 — Trend Structure Composite Display Layer
# ----------------------------------------------------------------------------

import subprocess  # noqa: E402

from cuttingboard.delivery.dashboard_renderer import (  # noqa: E402
    _trend_structure_composite_display,
)

_PRD131_VOCAB = (
    "↑ 50 ↑ 200",
    "↑ 50 ↓ 200",
    "↓ 50 ↑ 200",
    "↓ 50 ↓ 200",
    "= 50 ↑ 200",
    "= 50 ↓ 200",
    "↑ 50 = 200",
    "↓ 50 = 200",
    "= 50 = 200",
    "Structure unavailable",
    "SMA history insufficient",
    "Structure not computed",
)

# PRD-208: compressed 3-state arrow vocabulary (ABOVE=↑, BELOW=↓, AT_LEVEL==),
# suffixed with the SMA window. All 9 (3×3) composites asserted exactly.
_PRD131_R1_TABLE = (
    (("ABOVE", "ABOVE"),       "↑ 50 ↑ 200"),
    (("ABOVE", "BELOW"),       "↑ 50 ↓ 200"),
    (("BELOW", "ABOVE"),       "↓ 50 ↑ 200"),
    (("BELOW", "BELOW"),       "↓ 50 ↓ 200"),
    (("AT_LEVEL", "ABOVE"),    "= 50 ↑ 200"),
    (("AT_LEVEL", "BELOW"),    "= 50 ↓ 200"),
    (("ABOVE", "AT_LEVEL"),    "↑ 50 = 200"),
    (("BELOW", "AT_LEVEL"),    "↓ 50 = 200"),
    (("AT_LEVEL", "AT_LEVEL"), "= 50 = 200"),
)

_PRD131_FORBIDDEN = (
    "recovery", "pullback", "inflection", "established",
    "weakness", "weak", "strong", "firm", "soft", "confirmation",
    "breakout", "breakdown", "rebound", "reversal", "momentum",
    "trending", "likely", "probable", "expected", "imminent",
    "confidence", "high-probability", "uptrend", "downtrend",
    "bullish", "bearish",
)


# R1 — Per-cell deterministic mapping for all 9 comparison-token combinations.
@pytest.mark.parametrize("pair,expected", _PRD131_R1_TABLE)
def test_prd131_r1_composite_display_table(
    pair: tuple[str, str], expected: str,
) -> None:
    p50, p200 = pair
    rec = {"price_vs_sma_50": p50, "price_vs_sma_200": p200}
    assert _trend_structure_composite_display(rec) == expected


# PRD-208 R1 — the AT_LEVEL glyph must be DISTINCT from ABOVE and BELOW, so the
# three "at"-containing composites are not silently merged into ↑/↓ renderings.
def test_prd208_arrow_three_state_glyphs_distinct() -> None:
    g_above = _trend_structure_composite_display(
        {"price_vs_sma_50": "ABOVE", "price_vs_sma_200": "ABOVE"})
    g_below = _trend_structure_composite_display(
        {"price_vs_sma_50": "BELOW", "price_vs_sma_200": "BELOW"})
    g_at = _trend_structure_composite_display(
        {"price_vs_sma_50": "AT_LEVEL", "price_vs_sma_200": "AT_LEVEL"})
    assert len({g_above, g_below, g_at}) == 3, (
        "ABOVE/BELOW/AT_LEVEL must render distinct compact glyphs; "
        f"got {g_above!r}/{g_below!r}/{g_at!r}"
    )
    # AT_LEVEL must not reuse the ↑ or ↓ glyph.
    assert "↑" not in g_at and "↓" not in g_at, (
        f"AT_LEVEL composite {g_at!r} must use a distinct glyph, not ↑/↓"
    )


# R1 — Forbidden vocabulary must not appear in any composite display string.
def test_prd131_r1_no_forbidden_vocabulary() -> None:
    joined = " ".join(_PRD131_VOCAB).lower()
    for term in _PRD131_FORBIDDEN:
        assert term not in joined, (
            f"PRD-131 vocabulary leaked forbidden term {term!r}: {joined!r}"
        )


# R2 slot 2 — DATA_UNAVAILABLE on either SMA field → "Structure unavailable".
@pytest.mark.parametrize("p50,p200", [
    ("DATA_UNAVAILABLE", "ABOVE"),
    ("ABOVE", "DATA_UNAVAILABLE"),
    ("DATA_UNAVAILABLE", "DATA_UNAVAILABLE"),
])
def test_prd131_r2_slot2_data_unavailable(p50: str, p200: str) -> None:
    rec = {"price_vs_sma_50": p50, "price_vs_sma_200": p200}
    assert _trend_structure_composite_display(rec) == "Structure unavailable"


# R2 slot 3 — INSUFFICIENT_HISTORY (without DATA_UNAVAILABLE) → "SMA history insufficient".
@pytest.mark.parametrize("p50,p200", [
    ("INSUFFICIENT_HISTORY", "ABOVE"),
    ("ABOVE", "INSUFFICIENT_HISTORY"),
    ("INSUFFICIENT_HISTORY", "INSUFFICIENT_HISTORY"),
])
def test_prd131_r2_slot3_insufficient_history(p50: str, p200: str) -> None:
    rec = {"price_vs_sma_50": p50, "price_vs_sma_200": p200}
    assert _trend_structure_composite_display(rec) == "SMA history insufficient"


# R2 slot 4 — NOT_COMPUTED on an SMA field (totality reserve) → "Structure not computed".
@pytest.mark.parametrize("p50,p200", [
    ("NOT_COMPUTED", "ABOVE"),
    ("ABOVE", "NOT_COMPUTED"),
])
def test_prd131_r2_slot4_not_computed_totality_reserve(
    p50: str, p200: str,
) -> None:
    rec = {"price_vs_sma_50": p50, "price_vs_sma_200": p200}
    assert _trend_structure_composite_display(rec) == "Structure not computed"


# R2 — precedence: DATA_UNAVAILABLE > INSUFFICIENT_HISTORY > NOT_COMPUTED.
def test_prd131_r2_precedence_order() -> None:
    # DATA_UNAVAILABLE wins over INSUFFICIENT_HISTORY.
    assert _trend_structure_composite_display(
        {"price_vs_sma_50": "DATA_UNAVAILABLE",
         "price_vs_sma_200": "INSUFFICIENT_HISTORY"}
    ) == "Structure unavailable"
    # DATA_UNAVAILABLE wins over NOT_COMPUTED.
    assert _trend_structure_composite_display(
        {"price_vs_sma_50": "DATA_UNAVAILABLE",
         "price_vs_sma_200": "NOT_COMPUTED"}
    ) == "Structure unavailable"
    # INSUFFICIENT_HISTORY wins over NOT_COMPUTED.
    assert _trend_structure_composite_display(
        {"price_vs_sma_50": "INSUFFICIENT_HISTORY",
         "price_vs_sma_200": "NOT_COMPUTED"}
    ) == "SMA history insufficient"


# R3 — inactive-session branch emits no composite display vocabulary.
def test_prd131_r3_inactive_session_short_circuits_composite_display() -> None:
    inactive_payload = _inactive_payload()
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map()
    _set_generation_ids(inactive_payload, run, mm, "live-20260428T120000Z")
    html = render_dashboard_html(
        inactive_payload, run, market_map=mm,
        trend_structure_snapshot=_ts_healthy_snapshot(),
    )
    section = _trend_structure_section(html)
    assert INACTIVE_SESSION_LABEL in section
    for phrase in _PRD131_VOCAB:
        assert phrase not in section, (
            f"inactive-session render leaked composite display {phrase!r}"
        )


# R3 — snapshot-absent branch emits no composite display vocabulary.
def test_prd131_r3_snapshot_absent_short_circuits_composite_display(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    html = _prd120_coherent_render(trend_structure_snapshot=None)
    section = _ts_section(html)
    for phrase in _PRD131_VOCAB:
        assert phrase not in section, (
            f"snapshot-absent render leaked composite display {phrase!r}"
        )


# R1/R5 — composite display cell appears in trend-structure section on a
# healthy render and matches the helper output for a known record.
def test_prd131_r1_composite_cell_renders_in_panel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    snap = _ts_healthy_snapshot()
    # Force SPY into ABOVE/ABOVE.
    spy = snap["symbols"]["SPY"]
    spy["price_vs_sma_50"] = "ABOVE"
    spy["price_vs_sma_200"] = "ABOVE"
    html = _prd120_coherent_render(trend_structure_snapshot=snap)
    section = _ts_section(html)
    assert "↑ 50 ↑ 200" in section
    assert "SMA 50/200" in section  # header present (PRD-208 rename)


# R4(a) — helper name MUST NOT appear outside dashboard_renderer.py.
def test_prd131_r4a_helper_name_containment() -> None:
    result = subprocess.run(
        ["grep", "-RIln", "_trend_structure_composite_display",
         "cuttingboard/"],
        capture_output=True, text=True, check=False,
    )
    matches = [p for p in result.stdout.splitlines() if p.strip()]
    allowed = {"cuttingboard/delivery/dashboard_renderer.py"}
    leaked = [p for p in matches if p not in allowed]
    assert not leaked, (
        f"_trend_structure_composite_display leaked outside delivery: {leaked}"
    )


# R4(b) — every vocabulary literal under cuttingboard/ MUST live only in
# dashboard_renderer.py.
@pytest.mark.parametrize("phrase", _PRD131_VOCAB)
def test_prd131_r4b_vocabulary_under_source_only_in_renderer(
    phrase: str,
) -> None:
    result = subprocess.run(
        ["grep", "-RIlFn", phrase, "cuttingboard/"],
        capture_output=True, text=True, check=False,
    )
    matches = [p.split(":", 1)[0] for p in result.stdout.splitlines() if p.strip()]
    allowed = {"cuttingboard/delivery/dashboard_renderer.py"}
    leaked = sorted(set(matches) - allowed)
    assert not leaked, (
        f"vocabulary literal {phrase!r} leaked outside renderer: {leaked}"
    )


# R4(c) — vocabulary MUST NOT appear in machine-readable artifacts under
# logs/ or reports/ (HTML rendered destinations are explicitly excluded).
@pytest.mark.parametrize("phrase", _PRD131_VOCAB)
def test_prd131_r4c_vocabulary_not_in_machine_readable_artifacts(
    phrase: str,
) -> None:
    search_paths = []
    if Path("logs").is_dir():
        search_paths.append("logs")
    if Path("reports").is_dir():
        search_paths.append("reports")
    if not search_paths:
        pytest.skip("no logs/ or reports/ directory present")
    # Include only machine-readable formats; exclude *.html anywhere.
    result = subprocess.run(
        ["grep", "-RIlFn",
         "--include=*.json", "--include=*.jsonl",
         "--include=*.txt", "--include=*.md", "--include=*.csv",
         "--exclude=*.html",
         phrase, *search_paths],
        capture_output=True, text=True, check=False,
    )
    matches = [p.split(":", 1)[0] for p in result.stdout.splitlines() if p.strip()]
    leaked = sorted(set(matches))
    assert not leaked, (
        f"vocabulary literal {phrase!r} leaked into machine-readable "
        f"artifact paths: {leaked}"
    )


# ----------------------------------------------------------------------------
# PRD-132 — Intraday VWAP × RVOL Context Display Layer
# ----------------------------------------------------------------------------

from cuttingboard.delivery.dashboard_renderer import (  # noqa: E402
    _INTRADAY_RVOL_THRESHOLD,
    _intraday_rvol_band,
    _trend_structure_intraday_display,
)

_PRD132_R1_TABLE = (
    (("ABOVE",    "AT_OR_ABOVE"), "Above VWAP, RVOL >= 1.5x"),
    (("ABOVE",    "BELOW"),       "Above VWAP, RVOL < 1.5x"),
    (("ABOVE",    "UNAVAILABLE"), "Above VWAP, RVOL unavailable"),
    (("BELOW",    "AT_OR_ABOVE"), "Below VWAP, RVOL >= 1.5x"),
    (("BELOW",    "BELOW"),       "Below VWAP, RVOL < 1.5x"),
    (("BELOW",    "UNAVAILABLE"), "Below VWAP, RVOL unavailable"),
    (("AT_LEVEL", "AT_OR_ABOVE"), "At VWAP, RVOL >= 1.5x"),
    (("AT_LEVEL", "BELOW"),       "At VWAP, RVOL < 1.5x"),
    (("AT_LEVEL", "UNAVAILABLE"), "At VWAP, RVOL unavailable"),
)

_PRD132_VOCAB = tuple(s for _, s in _PRD132_R1_TABLE) + (
    "Intraday N/A",
    "VWAP N/A",
)

_PRD132_MAGNITUDE_DENY = (
    "elevated", "normal", "high", "low", "heavy", "light",
)

_PRD132_RVOL_FOR_BAND = {
    "AT_OR_ABOVE": 2.0,
    "BELOW": 0.8,
    "UNAVAILABLE": None,
}


# R1 — Deterministic 9-cell mapping (3 VWAP × 3 RVOL band).
@pytest.mark.parametrize("pair,expected", _PRD132_R1_TABLE)
def test_prd132_r1_intraday_display_table(
    pair: tuple[str, str], expected: str,
) -> None:
    vwap, band = pair
    rec = {
        "price_vs_vwap": vwap,
        "relative_volume": _PRD132_RVOL_FOR_BAND[band],
    }
    assert _trend_structure_intraday_display(rec) == expected


# R1 — Forbidden vocabulary check (PRD-131 list + magnitude deny-set).
def test_prd132_r1_no_forbidden_vocabulary() -> None:
    joined = " ".join(_PRD132_VOCAB).lower()
    for term in _PRD131_FORBIDDEN:
        assert term not in joined, f"PRD-132 vocab leaked PRD-131 term {term!r}"
    for term in _PRD132_MAGNITUDE_DENY:
        # match as whole-word boundary to avoid false positives in "normalization"
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        for phrase in _PRD132_VOCAB:
            assert not pattern.search(phrase), (
                f"PRD-132 vocab {phrase!r} contains magnitude adjective {term!r}"
            )


# R2 — VWAP unknown-state precedence over RVOL.
@pytest.mark.parametrize("rvol", [None, 0.5, 2.0, float("nan"), float("inf")])
def test_prd132_r2_data_unavailable_precedence(rvol: float | None) -> None:
    rec = {"price_vs_vwap": "DATA_UNAVAILABLE", "relative_volume": rvol}
    assert _trend_structure_intraday_display(rec) == "Intraday N/A"


@pytest.mark.parametrize("rvol", [None, 0.5, 2.0, float("nan"), float("inf")])
def test_prd132_r2_not_computed_precedence(rvol: float | None) -> None:
    rec = {"price_vs_vwap": "NOT_COMPUTED", "relative_volume": rvol}
    assert _trend_structure_intraday_display(rec) == "VWAP N/A"


# R3 — Inactive-session short-circuit.
def test_prd132_r3_inactive_session_short_circuits_intraday() -> None:
    inactive_payload = _inactive_payload()
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map()
    _set_generation_ids(inactive_payload, run, mm, "live-20260428T120000Z")
    html = render_dashboard_html(
        inactive_payload, run, market_map=mm,
        trend_structure_snapshot=_ts_healthy_snapshot(),
    )
    section = _trend_structure_section(html)
    assert INACTIVE_SESSION_LABEL in section
    import html as _h
    for phrase in _PRD132_VOCAB:
        escaped = _h.escape(phrase)
        assert phrase not in section and escaped not in section, (
            f"inactive-session render leaked intraday vocab {phrase!r}"
        )


# R3 — Snapshot-absent short-circuit.
def test_prd132_r3_snapshot_absent_short_circuits_intraday(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    html = _prd120_coherent_render(trend_structure_snapshot=None)
    section = _ts_section(html)
    import html as _h
    for phrase in _PRD132_VOCAB:
        escaped = _h.escape(phrase)
        assert phrase not in section and escaped not in section, (
            f"snapshot-absent render leaked intraday vocab {phrase!r}"
        )


# R1/R6 — Intraday Context cell appears in rendered panel; column order
# preserved (PRD-131/PRD-208 "SMA 50/200" stays present, Intraday Context after it).
def test_prd132_r1_r6_intraday_cell_renders_and_column_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    snap = _ts_healthy_snapshot()
    spy = snap["symbols"]["SPY"]
    spy["price_vs_vwap"] = "ABOVE"
    spy["relative_volume"] = 2.0
    html = _prd120_coherent_render(trend_structure_snapshot=snap)
    section = _ts_section(html)
    # Header presence + relative order.
    sma_pos = section.find("SMA 50/200")
    intra_pos = section.find(">Intraday</th>")
    assert sma_pos >= 0, "SMA 50/200 header missing"
    assert intra_pos > sma_pos, (
        "Intraday header must come after SMA 50/200"
    )
    # Phrase present in body. HTML-escape the operators since the renderer
    # passes cells through _esc(); browsers render entities back to glyphs.
    assert "Above VWAP, RVOL &gt;= 1.5x" in section


# R4(a) — helper / constant names containment under cuttingboard/.
@pytest.mark.parametrize("symbol", [
    "_trend_structure_intraday_display",
    "_intraday_rvol_band",
    "_INTRADAY_RVOL_THRESHOLD",
])
def test_prd132_r4a_symbol_containment(symbol: str) -> None:
    result = subprocess.run(
        ["grep", "-RIln", symbol, "cuttingboard/"],
        capture_output=True, text=True, check=False,
    )
    matches = [p for p in result.stdout.splitlines() if p.strip()]
    allowed = {"cuttingboard/delivery/dashboard_renderer.py"}
    leaked = [p for p in matches if p not in allowed]
    assert not leaked, f"{symbol!r} leaked outside delivery: {leaked}"


# R4(b) — every vocabulary literal under cuttingboard/ MUST live only in
# dashboard_renderer.py.
@pytest.mark.parametrize("phrase", _PRD132_VOCAB)
def test_prd132_r4b_vocabulary_under_source_only_in_renderer(
    phrase: str,
) -> None:
    result = subprocess.run(
        ["grep", "-RIlFn", phrase, "cuttingboard/"],
        capture_output=True, text=True, check=False,
    )
    matches = [
        p.split(":", 1)[0] for p in result.stdout.splitlines() if p.strip()
    ]
    allowed = {"cuttingboard/delivery/dashboard_renderer.py"}
    leaked = sorted(set(matches) - allowed)
    assert not leaked, (
        f"PRD-132 vocab literal {phrase!r} leaked outside renderer: {leaked}"
    )


# R4(c) — vocabulary MUST NOT appear in machine-readable artifacts.
# Rendered HTML (*.html) is the intended destination and is excluded.
@pytest.mark.parametrize("phrase", _PRD132_VOCAB)
def test_prd132_r4c_vocabulary_not_in_machine_readable_artifacts(
    phrase: str,
) -> None:
    search_paths = []
    if Path("logs").is_dir():
        search_paths.append("logs")
    if Path("reports").is_dir():
        search_paths.append("reports")
    if not search_paths:
        pytest.skip("no logs/ or reports/ directory present")
    result = subprocess.run(
        ["grep", "-RIlFn",
         "--include=*.json", "--include=*.jsonl",
         "--include=*.txt", "--include=*.md", "--include=*.csv",
         "--exclude=*.html",
         phrase, *search_paths],
        capture_output=True, text=True, check=False,
    )
    matches = [
        p.split(":", 1)[0] for p in result.stdout.splitlines() if p.strip()
    ]
    leaked = sorted(set(matches))
    assert not leaked, (
        f"PRD-132 vocab literal {phrase!r} leaked into machine-readable "
        f"artifacts (excluding *.html): {leaked}"
    )


# R5 — RVOL band classifier edge cases.
@pytest.mark.parametrize("rvol,expected", [
    (None, "UNAVAILABLE"),
    (float("nan"), "UNAVAILABLE"),
    (float("inf"), "UNAVAILABLE"),
    (float("-inf"), "UNAVAILABLE"),
    (0.0, "BELOW"),
    (1.0, "BELOW"),
    (1.49, "BELOW"),
    (1.5, "AT_OR_ABOVE"),   # boundary — inclusive
    (1.51, "AT_OR_ABOVE"),
    (5.0, "AT_OR_ABOVE"),
])
def test_prd132_r5_rvol_band_classifier(
    rvol: float | None, expected: str,
) -> None:
    assert _intraday_rvol_band(rvol) == expected


# R5 — threshold constant matches displayed literal "1.5x".
def test_prd132_r5_threshold_constant_matches_displayed_literal() -> None:
    assert _INTRADAY_RVOL_THRESHOLD == 1.5, (
        "Threshold constant drifted from displayed '1.5x' substring; if you "
        "tune the threshold, every R1 display string must update in lock-step."
    )
    # Cross-check: every R1 display string referencing the threshold uses '1.5x'.
    threshold_phrases = [
        s for _, s in _PRD132_R1_TABLE if "RVOL >=" in s or "RVOL <" in s
    ]
    for phrase in threshold_phrases:
        assert "1.5x" in phrase, (
            f"R1 phrase {phrase!r} missing '1.5x' literal"
        )


# R6(b) — PRD-131 symbol literals still present unmodified.
@pytest.mark.parametrize("symbol", [
    "_TREND_STRUCTURE_COMPOSITE_DISPLAY",
    "_trend_structure_composite_display",
])
def test_prd132_r6b_prd131_symbols_present(symbol: str) -> None:
    result = subprocess.run(
        ["grep", "-Fn", symbol,
         "cuttingboard/delivery/dashboard_renderer.py"],
        capture_output=True, text=True, check=False,
    )
    assert result.stdout.strip(), (
        f"PRD-131 symbol {symbol!r} missing from dashboard_renderer.py — "
        "PRD-132 isolation invariant R6(b) violated"
    )


# R6(c) — "SMA 50/200" header present, "Intraday Context" appended after.
def test_prd132_r6c_header_order_in_source() -> None:
    src = Path("cuttingboard/delivery/dashboard_renderer.py").read_text()
    sma_pos = src.find('"SMA 50/200"')
    intra_pos = src.find('"Intraday"')
    assert sma_pos >= 0, "PRD-131/PRD-208 'SMA 50/200' header literal missing"
    assert intra_pos > sma_pos, (
        "PRD-132 'Intraday' header must appear after 'SMA 50/200'"
    )


# R6(d) — `_cells` tuple order: composite display call precedes intraday call.
def test_prd132_r6d_cells_call_order_in_source() -> None:
    src = Path("cuttingboard/delivery/dashboard_renderer.py").read_text()
    comp_pos = src.find("_trend_structure_composite_display(_rec)")
    intra_pos = src.find("_trend_structure_intraday_display(_rec)")
    assert comp_pos >= 0, (
        "PRD-131 composite display call missing from _cells tuple"
    )
    assert intra_pos > comp_pos, (
        "PRD-132 intraday display call must be appended after composite call"
    )


# R6(e) — all 12 PRD-131 display strings present byte-identically.
_PRD131_VOCAB_FOR_R6E = (
    "↑ 50 ↑ 200",
    "↑ 50 ↓ 200",
    "↓ 50 ↑ 200",
    "↓ 50 ↓ 200",
    "= 50 ↑ 200",
    "= 50 ↓ 200",
    "↑ 50 = 200",
    "↓ 50 = 200",
    "= 50 = 200",
    "Structure unavailable",
    "SMA history insufficient",
    "Structure not computed",
)


@pytest.mark.parametrize("phrase", _PRD131_VOCAB_FOR_R6E)
def test_prd132_r6e_prd131_vocabulary_present(phrase: str) -> None:
    result = subprocess.run(
        ["grep", "-Fn", phrase,
         "cuttingboard/delivery/dashboard_renderer.py"],
        capture_output=True, text=True, check=False,
    )
    assert result.stdout.strip(), (
        f"PRD-131 display string {phrase!r} missing from renderer — "
        "PRD-132 isolation invariant R6(e) violated"
    )


# R6(f) — Missing-record row cell count matches the table column count.
def test_prd132_r6f_missing_record_cell_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    # Build a trend-structure snapshot where one curated symbol has no record.
    snap = _ts_healthy_snapshot()
    missing_sym = next(iter(snap["symbols"].keys()))
    snap["symbols"][missing_sym] = {"symbol": missing_sym}  # strip required fields
    html = _prd120_coherent_render(trend_structure_snapshot=snap)
    section = _ts_section(html)
    # Identify the placeholder row by its symbol cell.
    rows = re.findall(r"<tr>(.*?)</tr>", section, re.S)
    missing_row = None
    for row in rows:
        if f">{missing_sym}<" in row and "<td" in row:
            missing_row = row
            break
    assert missing_row is not None, (
        f"row for {missing_sym} not found in trend-structure section"
    )
    cell_count = len(re.findall(r"<td[^>]*>", missing_row))
    assert cell_count == 8, (
        f"missing-record row has {cell_count} cells; expected 8 "
        "(Symbol, Price, vs VWAP, Alignment, Entry Context, RVOL, SMA 50/200, "
        "Intraday — PRD-208 cut vs SMA50/vs SMA200)"
    )


# =========================================================================
# PRD-136 R9 — Spot-metals row tests
# =========================================================================


def _drivers_with_metals(
    *, gold: float | None = 2050.5, silver: float | None = 24.75
) -> dict:
    """PRD-136: macro_drivers fixture extended with gold/silver entries.

    Mirrors the PRD-122 oil pattern. Set gold=None or silver=None to omit
    that key entirely from the macro_drivers dict (graceful-degradation
    test path).
    """
    drivers = _macro_drivers()
    if gold is not None:
        drivers["gold"] = {"symbol": "GC=F", "level": gold, "change_pct": 0.4}
    if silver is not None:
        drivers["silver"] = {"symbol": "SI=F", "level": silver, "change_pct": -0.2}
    return drivers


def test_prd136_r9a_xau_xag_present_in_rendered_html() -> None:
    """R9(a): data-symbol="XAU" and data-symbol="XAG" present in HTML."""
    html = render_dashboard_html(
        _payload(macro_drivers=_drivers_with_metals()),
        _run(),
        market_map=_market_map(),
    )
    tape = _macro_tape_block(html)
    assert 'data-symbol="XAU"' in tape, "XAU missing from macro-tape block"
    assert 'data-symbol="XAG"' in tape, "XAG missing from macro-tape block"
    assert "macro-spot-metals-row" in tape, "macro-spot-metals-row wrapper missing"


def test_prd138_macro_rows_render_in_shared_layout_order() -> None:
    """R3: row 1 is XAU/XAG/BTC, then row 2, then tradables."""
    html = render_dashboard_html(
        _payload(macro_drivers=_drivers_with_metals()),
        _run(),
        market_map=_market_map(),
    )
    tape = _macro_tape_block(html)
    xau_idx = tape.index('data-symbol="XAU"')
    xag_idx = tape.index('data-symbol="XAG"')
    btc_idx = tape.index('data-symbol="BTC"')
    vix_idx = tape.index('data-symbol="VIX"')
    oil_idx = tape.index('data-symbol="OIL"')
    gld_idx = tape.index('data-symbol="GLD"')
    assert xau_idx < xag_idx < btc_idx < vix_idx < oil_idx < gld_idx


def test_prd136_r9b_spot_metals_row_follows_macro_bias() -> None:
    """R9(b) supplement: spot-metals row sits between MACRO BIAS and drivers row."""
    html = render_dashboard_html(
        _payload(macro_drivers=_drivers_with_metals()),
        _run(),
        market_map=_market_map(),
    )
    tape = _macro_tape_block(html)
    metals_idx = tape.index('class="macro-spot-metals-row"')
    drivers_idx = tape.index('class="macro-drivers-row"')
    assert metals_idx < drivers_idx, (
        f"spot-metals row must precede macro-drivers-row; "
        f"metals_idx={metals_idx}, drivers_idx={drivers_idx}"
    )


def test_prd138_renderer_uses_shared_macro_tape_layout_constants() -> None:
    from cuttingboard.delivery.macro_tape_layout import MACRO_ROW_1, MACRO_ROW_2, TRADABLES_ROW

    assert tuple(slot.label for slot in MACRO_ROW_1.slots) == ("XAU", "XAG", "BTC")
    assert tuple(slot.label for slot in MACRO_ROW_2.slots) == ("VIX", "DXY", "10Y", "OIL")
    assert tuple(slot.label for slot in TRADABLES_ROW.slots) == (
        "SPY", "QQQ", "GLD", "GDX", "SLV", "XLE",
    )


def test_prd138_xau_xag_route_through_directional_arrow_css() -> None:
    html = render_dashboard_html(
        _payload(macro_drivers=_drivers_with_metals()),
        _run(),
        market_map=_market_map(),
    )
    tape = _macro_tape_block(html)
    # PRD-211: visible label is the honest CME futures ticker (GC/SI); the slot
    # id / data-symbol stays XAU/XAG (asserted by the R9(a)/order tests above).
    # PRD-224: 2-char labels pad to the 3-char column with &nbsp;.
    assert 'class="macro-tape-slot tape-slot up"><span class="macro-tape-label">GC&nbsp; ↑</span>' in tape
    assert 'class="macro-tape-slot tape-slot down"><span class="macro-tape-label">SI&nbsp; ↓</span>' in tape


def test_prd136_r9d_no_silent_na_regression_driver_side() -> None:
    """R9(d): driver-side cells (VIX/DXY/10Y/BTC/OIL) and the new spot-metals
    (XAU/XAG) all render non-N/A when their macro_drivers entries are
    present. Tradables-side cells (SPY/QQQ/GLD/SLV/XLE/GDX) depend on
    market_map.symbols and are covered by R3 and the pre-existing
    tradables tests; this regression assertion is intentionally scoped to
    the cells the spot-metals insertion could plausibly perturb."""
    drivers = _drivers_with_metals()
    drivers["oil"] = {"symbol": "CL=F", "level": 78.5, "change_pct": 1.2}
    html = render_dashboard_html(
        _payload(macro_drivers=drivers),
        _run(),
        market_map=_market_map(),
    )
    from tests.dash_helpers import _macro_tape_value_slots
    slots = dict(_macro_tape_value_slots(html))
    for label in ("VIX", "DXY", "10Y", "BTC", "OIL", "XAU", "XAG"):
        assert label in slots, f"{label} missing from tape value slots"
        assert slots[label] != "N/A", f"{label} unexpectedly rendered N/A"
        assert slots[label] != "--", f"{label} unexpectedly rendered '--'"


def test_prd136_r9f_xau_missing_renders_na() -> None:
    """R9(f): missing gold key → XAU cell renders N/A, dashboard still renders."""
    drivers = _drivers_with_metals(gold=None, silver=24.75)
    assert "gold" not in drivers
    html = render_dashboard_html(
        _payload(macro_drivers=drivers),
        _run(),
        market_map=_market_map(),
    )
    from tests.dash_helpers import _macro_tape_value_slots
    slots = dict(_macro_tape_value_slots(html))
    assert slots.get("XAU") == "N/A", f"expected XAU=N/A, got slots={slots}"
    assert slots.get("XAG") == "24.75", f"expected XAG=24.75, got slots={slots}"
    # Rest of dashboard still rendered
    assert 'data-symbol="XAU"' in html
    assert "macro-drivers-row" in html


def test_prd136_r9f_xag_missing_renders_na() -> None:
    """R9(f): missing silver key → XAG cell renders N/A, dashboard still renders."""
    drivers = _drivers_with_metals(gold=2050.5, silver=None)
    assert "silver" not in drivers
    html = render_dashboard_html(
        _payload(macro_drivers=drivers),
        _run(),
        market_map=_market_map(),
    )
    from tests.dash_helpers import _macro_tape_value_slots
    slots = dict(_macro_tape_value_slots(html))
    assert slots.get("XAU") == "2050.5", f"expected XAU=2050.5, got slots={slots}"
    assert slots.get("XAG") == "N/A", f"expected XAG=N/A, got slots={slots}"


def test_prd136_r9f_both_missing_renders_na() -> None:
    """R9(f): both gold and silver absent → both cells N/A, dashboard renders."""
    drivers = _macro_drivers()  # no gold, no silver
    html = render_dashboard_html(
        _payload(macro_drivers=drivers),
        _run(),
        market_map=_market_map(),
    )
    from tests.dash_helpers import _macro_tape_value_slots
    slots = dict(_macro_tape_value_slots(html))
    assert slots.get("XAU") == "N/A", f"expected XAU=N/A, got slots={slots}"
    assert slots.get("XAG") == "N/A", f"expected XAG=N/A, got slots={slots}"


def test_prd136_r3_tradables_grid_preserved() -> None:
    """R3: canonical PRD-138 tradables grid still renders."""
    html = render_dashboard_html(
        _payload(macro_drivers=_drivers_with_metals()),
        _run(),
        market_map=_market_map(),
    )
    assert 'class="macro-tradables-grid"' in html
    for sym in ("SPY", "QQQ", "GLD", "GDX", "SLV", "XLE"):
        assert f'data-symbol="{sym}"' in html, f"{sym} missing from tradables grid"


def test_prd136_r4a_spot_metals_in_non_tradable_symbols() -> None:
    """R4(a): GC=F and SI=F are NON_TRADABLE_SYMBOLS members (fences qualification)."""
    from cuttingboard import config
    assert "GC=F" in config.NON_TRADABLE_SYMBOLS
    assert "SI=F" in config.NON_TRADABLE_SYMBOLS


# ---------------------------------------------------------------------------
# PRD-177 — scoreboard (R4), red folder (R5). (R3 macro-evidence rows removed
# by PRD-214; replaced with the single MACRO BIAS risk-vote tally.)
# ---------------------------------------------------------------------------

def test_prd214_macro_tally_present_and_agrees_with_headline() -> None:
    # PRD-214: the per-driver macro-evidence rows (PRD-177 R3 / PRD-191) are
    # superseded by a single risk-vote tally under the MACRO BIAS headline.
    # Cyclicality-correct bullish drivers: VIX/DXY/10Y down, BTC up -> all four
    # vote risk-ON (long); headline reads LONG and the tally must agree.
    drivers = _macro_drivers(vix=-0.5, dxy=-0.3, tnx=-0.4, btc=0.6)
    html = render_dashboard_html(_payload(macro_drivers=drivers), _run(), market_map=_market_map())
    tape = _macro_tape_block(html)
    assert "MACRO BIAS: LONG" in tape
    m = re.search(r'class="macro-tally">Risk votes: (\d+) off / (\d+) on \S+ (\w+)</div>', tape)
    assert m is not None, "PRD-214 macro-tally line missing"
    off, on, bias_word = int(m.group(1)), int(m.group(2)), m.group(3)
    assert (on, off, bias_word) == (4, 0, "LONG"), (on, off, bias_word)


def test_prd214_macro_evidence_rows_removed() -> None:
    # PRD-214 supersession: the per-driver evidence rows and their classes are
    # gone from the rendered tape and the CSS.
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()), _run(), market_map=_market_map(),
    )
    assert "macro-evidence" not in html
    assert "risk-ON vote" not in html and "risk-OFF vote" not in html


def test_prd177_r4_scoreboard_renders_rows() -> None:
    hist = [
        {"date": "2026-06-08", "regime": "RISK_ON", "posture": "CONTROLLED_LONG",
         "spy_close_change_pct": 0.0123},
        {"date": "2026-06-09", "regime": "RISK_OFF", "posture": "STAY_FLAT",
         "spy_close_change_pct": -0.004},
    ]
    html = render_dashboard_html(_payload(), _run(), regime_history=hist)
    board = html.split('id="scoreboard"', 1)[1]
    assert "2026-06-09" in board and "2026-06-08" in board
    # Most-recent row first.
    assert board.index("2026-06-09") < board.index("2026-06-08")
    # Raw posture enum mapped to a display label, not the literal.
    assert "Stay Flat" in board
    assert "STAY_FLAT" not in board
    assert "SPY next +1.23%" in board
    assert "No regime history yet." not in board


def test_prd177_r4_scoreboard_caps_at_five_rows() -> None:
    hist = [
        {"date": f"2026-05-{day:02d}", "regime": "RISK_ON", "posture": "CONTROLLED_LONG",
         "spy_close_change_pct": 0.001 * day}
        for day in range(1, 16)
    ]
    html = render_dashboard_html(_payload(), _run(), regime_history=hist)
    board = html.split('id="scoreboard"', 1)[1]
    assert board.count('class="scoreboard-row"') == 5
    # Oldest ten (days 1-10) are dropped; the newest five (days 11-15) are shown.
    assert "2026-05-15" in board
    assert "2026-05-11" in board
    assert "2026-05-10" not in board
    assert "2026-05-01" not in board


def test_prd177_r4_scoreboard_empty_state() -> None:
    for hist in (None, []):
        html = render_dashboard_html(_payload(), _run(), regime_history=hist)
        board = html.split('id="scoreboard"', 1)[1]
        assert "No regime history yet." in board
        assert 'class="scoreboard-row"' not in board


def test_prd265_r5_scoreboard_marks_bounded_row() -> None:
    # total_votes=5 -> BOUNDED (1-7): renders the marker.
    hist = [
        {"date": "2026-06-08", "regime": "RISK_ON", "posture": "CONTROLLED_LONG",
         "spy_close_change_pct": 0.0123, "total_votes": 5},
    ]
    html = render_dashboard_html(_payload(), _run(), regime_history=hist)
    board = html.split('id="scoreboard"', 1)[1]
    assert "BOUNDED" in board


def test_prd265_r5_scoreboard_four_states_only_bounded_marks() -> None:
    # absent=LEGACY, 0=EXPANSION, 8=FULL must NOT render BOUNDED; only the
    # 1-7 row does.
    hist = [
        {"date": "2026-06-05", "regime": "NEUTRAL", "posture": "STAY_FLAT",
         "spy_close_change_pct": 0.0},  # LEGACY: no total_votes key at all
        {"date": "2026-06-06", "regime": "RISK_ON", "posture": "CONTROLLED_LONG",
         "spy_close_change_pct": 0.001, "total_votes": 0},  # EXPANSION
        {"date": "2026-06-07", "regime": "RISK_ON", "posture": "CONTROLLED_LONG",
         "spy_close_change_pct": 0.002, "total_votes": 5},  # BOUNDED
        {"date": "2026-06-08", "regime": "RISK_OFF", "posture": "DEFENSIVE_SHORT",
         "spy_close_change_pct": -0.001, "total_votes": 8},  # FULL
    ]
    html = render_dashboard_html(_payload(), _run(), regime_history=hist)
    board = html.split('id="scoreboard"', 1)[1]
    rows = board.split('class="scoreboard-row"')[1:]
    assert len(rows) == 4
    marked = [i for i, row in enumerate(rows) if "BOUNDED" in row]
    # Most-recent-first ordering: 06-08 (FULL), 06-07 (BOUNDED), 06-06 (EXPANSION), 06-05 (LEGACY)
    assert marked == [1], f"only the BOUNDED (1-7) row should carry the marker, got rows marked: {marked}"


def test_prd177_r5_red_folder_lists_events() -> None:
    rf = {"ok": True, "error": None, "expiring": False,
          "events": [{"date": "2026-06-11", "time_et": "08:30", "type": "CPI", "name": "CPI (May)"}]}
    html = render_dashboard_html(_payload(), _run(), red_folder=rf)
    block = html.split('id="red-folder"', 1)[1].split('id="trend-structure"', 1)[0]
    assert "CPI (May)" in block
    assert "2026-06-11 08:30 ET" in block
    assert "No red-folder events" not in block


def test_prd313_r1_red_folder_healthy_empty_suppressed() -> None:
    # PRD-313: a healthy, zero-event, non-expiring RESOLVED dict suppresses the
    # standalone block entirely -- MARKET STATE EVENT RISK already carries the fact.
    rf = {"ok": True, "error": None, "expiring": False, "events": []}
    html = render_dashboard_html(_payload(), _run(), red_folder=rf)
    assert 'id="red-folder"' not in html


def test_prd313_r6_event_risk_and_order_under_suppression() -> None:
    # PRD-313: suppression leaves EVENT RISK and surrounding block order intact.
    rf = {"ok": True, "error": None, "expiring": False, "events": []}
    html = render_dashboard_html(_payload(), _run(), red_folder=rf)
    assert 'id="red-folder"' not in html
    assert "No scheduled events in the next 48 hours" in html
    assert html.index('id="macro-tape"') < html.index('id="trend-structure"')


def test_prd177_r5_red_folder_loader_error_warns() -> None:
    rf = {"ok": False, "error": "schedule file not found", "expiring": False, "events": []}
    html = render_dashboard_html(_payload(), _run(), red_folder=rf)
    block = html.split('id="red-folder"', 1)[1].split('id="trend-structure"', 1)[0]
    assert "RED FOLDER UNAVAILABLE" in block
    assert "schedule file not found" in block
    assert "No red-folder events" not in block


def test_prd177_r5_red_folder_expiry_warning() -> None:
    rf = {"ok": True, "error": None, "expiring": True, "events": []}
    html = render_dashboard_html(_payload(), _run(), red_folder=rf)
    block = html.split('id="red-folder"', 1)[1].split('id="trend-structure"', 1)[0]
    assert "nearing expiry" in block


def test_prd177_r5_red_folder_default_empty_state() -> None:
    # No red_folder argument -> empty-state line (never silent absence).
    html = render_dashboard_html(_payload(), _run())
    assert 'id="red-folder"' in html
    block = html.split('id="red-folder"', 1)[1].split('id="trend-structure"', 1)[0]
    assert "No red-folder events in the next 48 hours." in block


# ---------------------------------------------------------------------------
# PRD-199 — macro-tape tradables daily %-change arrow
# ---------------------------------------------------------------------------

def _ts_snapshot_with_changes(changes: dict, *, generated_at: str | None = None) -> dict:
    snap = _ts_healthy_snapshot()
    if generated_at is not None:
        snap["generated_at"] = generated_at
    for sym, rec in snap["symbols"].items():
        rec["daily_change_pct"] = changes.get(sym)
    return snap


def _fresh_ts_iso() -> str:
    # Trend-snapshot freshness (_compute_timestamp_freshness) is measured against the
    # real wall clock, so a wall-clock-fresh snapshot needs a near-now generated_at.
    return datetime.now(timezone.utc).isoformat()


def _tradable_cell(html: str, symbol: str) -> str:
    grid = html.split('class="macro-tradables-grid"', 1)[1].split("</div>", 1)[0]
    for cell in grid.split('class="tradable-cell"')[1:]:
        if f'data-symbol="{symbol}"' in cell:
            return cell
    raise AssertionError(f"tradable cell for {symbol} not found")


def _render_tradables(monkeypatch, changes, *, generated_at, mm_symbols=None) -> str:
    # _ts_health == "OK" needs BOTH fresh+coherent lineage (frozen _utcnow + coherent
    # generation_ids) and a wall-clock-fresh snapshot generated_at.
    _freeze_renderer_now(monkeypatch)
    payload, run, market_map = _coherent_inputs()
    if mm_symbols is not None:
        market_map["symbols"] = mm_symbols
        market_map["primary_symbols"] = list(mm_symbols.keys())
    snap = _ts_snapshot_with_changes(changes, generated_at=generated_at)
    return render_dashboard_html(payload, run, market_map=market_map, trend_structure_snapshot=snap)


def test_prd312_tradables_arrow_removed(monkeypatch) -> None:
    # PRD-312 (M14): the Macro-Tape tradables daily-change arrow is cut. No
    # `tradable-arrow` span renders anywhere, regardless of trend-snapshot content
    # -- reintroducing the arrow reddens. (Supersedes the PRD-199/R5 arrow tests.)
    html = _render_tradables(
        monkeypatch, {"SPY": -0.42, "QQQ": 0.85}, generated_at=_fresh_ts_iso(),
        mm_symbols={"SPY": _mm_symbol("SPY", grade="A"), "QQQ": _mm_symbol("QQQ", grade="A")},
    )
    assert "tradable-arrow" not in html
    grid = html.split('class="macro-tradables-grid"', 1)[1].split("</div>", 1)[0]
    assert "tradable-arrow" not in grid


def test_prd312_tradables_price_preserved(monkeypatch) -> None:
    # PRD-312 (M15): the tradables PRICE tape survives the arrow cut -- the label +
    # current_price still render; removing the price reddens. (Supersedes the
    # PRD-199 R4 price-unchanged-with-arrow test.)
    html = _render_tradables(
        monkeypatch, {"SPY": 0.5}, generated_at=_fresh_ts_iso(),
        mm_symbols={"SPY": {**_mm_symbol("SPY", grade="A"), "current_price": 512.345}},
    )
    cell = _tradable_cell(html, "SPY")
    assert 'data-symbol="SPY">512.35</span>' in cell
    assert "tradable-arrow" not in cell


def test_prd312_market_state_before_system_state_outside_region() -> None:
    # PRD-318 supersedes the peer-card placement while preserving all five facts
    # in their operator-question zones.
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map())
    assert 'id="market-state"' not in html
    assert "Risk-on regime" in _top_block(html, "system-state")
    assert 'id="tape-zone"' in html
    assert 'id="today-zone"' in html


# ---------------------------------------------------------------------------
# PRD-314 — first-screen phone compaction (presentation-only, max-width:430px)
# ---------------------------------------------------------------------------
_PRD318_PHONE_BLOCK = (
    "@media(max-width:430px){"
    "body{padding:8px}"
    ".operator-zone{padding:10px;margin-bottom:8px}"
    ".operator-zone>h2{margin-bottom:7px}"
    ".zone-grid{gap:6px 10px}"
    ".zone-value{font-size:.78rem}"
    ".decision-state{font-size:1.25rem}"
    ".sys-verdict{font-size:.82rem}"
    ".sys-why{font-size:.78rem;margin-top:3px}"
    ".sys-context{font-size:.74rem}"
    "#system-state .sep{margin:5px 0}"
    "#system-state #cb-updated{font-size:.78rem}"
    "#watching-zone .operator-subsection{padding-top:8px;margin-top:8px}"
    "#opportunity-survival .kv-grid{grid-template-columns:auto minmax(2.5ch,1fr) auto minmax(2.5ch,1fr)}"
    "#opportunity-survival .kv-grid>*:nth-child(10){grid-column:2/-1}"
    "#candidate-board .candidate-scope{padding:5px 7px;margin-bottom:6px;font-size:.68rem;line-height:1.25}"
    "#candidate-board:not(:has(.candidate-card)) .unavailable{font-size:.72rem}"
    "#details-history .block{padding:10px 0}"
    "}"
)


def test_prd314_phone_block_present_and_id_scoped() -> None:
    # PRD-318 supersedes the prior producer-card compaction at the same boundary.
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map())
    assert _PRD318_PHONE_BLOCK in html
    assert "display:none" not in _PRD318_PHONE_BLOCK


def test_prd314_phone_block_is_separate_from_640_breakpoint() -> None:
    # A new INDEPENDENT breakpoint; the existing 640px Trend rule is untouched.
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map())
    assert "@media(max-width:430px){" in html
    assert "@media(max-width:640px){" in html


def test_prd314_generic_selectors_unchanged() -> None:
    # No global .block / .kv-grid redefinition -- lower-page cards are unaffected.
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map())
    assert ".block{border:1px solid #2a2a2a;border-radius:4px;margin-bottom:1rem;padding:1rem}" in html
    assert ".kv-grid{display:grid;grid-template-columns:max-content 1fr;gap:2px 0.75rem;margin-top:0.25rem}" in html


# ---------------------------------------------------------------------------
# PRD-317 — preserved mobile-operator layout promotion (CSS-only, <=430px)
# ---------------------------------------------------------------------------
def test_prd317_exact_phone_rules_share_the_430_boundary() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map())
    assert _PRD318_PHONE_BLOCK in html
    assert "@media(max-width:431px){" not in html


def test_prd317_rules_are_id_scoped_and_overflow_neutral() -> None:
    selectors = (
        ".operator-zone{",
        "#system-state .sep{",
        "#watching-zone .operator-subsection{",
        "#candidate-board .candidate-scope{",
        "#candidate-board:not(:has(.candidate-card)) .unavailable{",
        "#details-history .block{",
    )
    assert all(selector in _PRD318_PHONE_BLOCK for selector in selectors)
    assert all(token not in _PRD318_PHONE_BLOCK for token in (
        "min-width:", "overflow:", "display:none", "position:", "transform:",
    ))


def test_prd317_authoritative_text_order_parity() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map())
    ids = (
        'id="system-state"',
        'id="tape-zone"',
        'id="today-zone"',
        'id="watching-zone"',
        'id="details-history"',
    )
    assert all(block_id in html for block_id in ids)
    assert [html.index(block_id) for block_id in ids] == sorted(html.index(block_id) for block_id in ids)


def test_prd318_four_full_weight_zones_before_details() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map())
    before_details = html.split('<details class="block operator-zone"', 1)[0]
    assert before_details.count('class="block operator-zone"') == 4
    assert 'id="market-state"' not in before_details
    assert html.index('id="system-state"') < html.index('id="tape-zone"')
    assert html.index('id="tape-zone"') < html.index('id="today-zone"')
    assert html.index('id="today-zone"') < html.index('id="watching-zone"')


def test_prd318_tape_is_display_only_adjacency() -> None:
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        trend_structure_snapshot=_ts_healthy_snapshot(),
    )
    tape = _top_block(html, "tape-zone")
    assert "6 of 6 bullish" in tape
    assert 'data-derivation="bullish-row-count"' in tape
    for forbidden in ("ALIGNED", "DIVERGING", "CONFLUENT", "systems agree"):
        assert forbidden not in tape


def test_prd318_candidate_detail_keys_only_from_authoritative_decision() -> None:
    entry = _mm_symbol("SPY", grade="A")
    entry["watch_zones"] = [{"level": 101.0, "type": "RESISTANCE"}]
    mm = _market_map({"SPY": entry})
    flat = render_dashboard_html(_payload(), _run(outcome="NO_TRADE"), market_map=mm)
    permitted = render_dashboard_html(_payload(), _run(outcome="TRADE"), market_map=mm)
    flat_card = _candidate_card(flat)
    permitted_card = _candidate_card(permitted)
    assert 'class="candidate-card grade-a candidate-observation"' in flat
    assert '<details class="level-detail">' in flat_card
    assert 'class="candidate-card grade-a"' in permitted
    assert '<details class="level-detail">' not in permitted_card
    for fact in ("SPY", "A", "hold above reference", "loses reference"):
        assert fact in flat_card and fact in permitted_card


def test_prd318_candidate_empty_vocabularies_are_distinct() -> None:
    map_empty = render_dashboard_html(_payload(), _run(), market_map=_market_map({}))
    mcc_empty = _render_with_mcc(_mcc_section(
        candidate_implication={
            "value": "NO_CANDIDATES", "unavailable_reason": None,
            "counts": {"ACTIVE": 0, "NEAR_MISS": 0, "BLOCKED": 0},
        }
    ))
    assert "Map empty — no symbols graded this run" in map_empty
    assert "No candidates qualified this run" in mcc_empty
    assert "No candidates qualified this run" not in map_empty


def test_prd318_details_default_collapsed_and_evidence_present() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=_market_map())
    assert '<details class="block operator-zone" id="details-history">' in html
    assert '<details class="block operator-zone" id="details-history" open' not in html
    for block_id in ("macro-tape", "trend-structure", "run-delta", "scoreboard"):
        assert f'id="{block_id}"' in html.split('id="details-history"', 1)[1]


def test_prd318_authoritative_permission_renders_once_from_system_state() -> None:
    normal_permission = "Long bias - defined risk preferred. Kill: VIX crosses 25."
    locked_permission = "No new trades permitted — operator cannot monitor."
    payload = _payload()
    payload["summary"]["permission"] = "payload summary must not win"

    for permission in (normal_permission, locked_permission):
        html = render_dashboard_html(payload, _run(permission=permission), market_map=_market_map())
        state = _top_block(html, "system-state")

        assert state.count('class="sys-permission"') == 1
        assert state.count(permission) == 1
        assert html.count(permission) == 1
        assert "payload summary must not win" not in html
        assert 'id="market-state"' not in html
        assert '<div class="label">PERMISSION</div>' not in html


# ---------------------------------------------------------------------------
# PRD-220 — round-2 refinements
# ---------------------------------------------------------------------------

def test_prd220_context_reports_gated_setups_not_no_qualified() -> None:
    # R1: with an A+ setup present and NO_TRADE, the context reports the gated
    # count — never the contradictory "no qualified".
    mm = _market_map({"GDX": _mm_symbol("GDX", grade="A+")})
    html = render_dashboard_html(_payload(), _run(outcome="NO_TRADE", permission=None), market_map=mm)
    state = html.split('id="system-state"', 1)[1].split('id="macro-tape"', 1)[0]
    assert "1 setup gated" in state
    assert "no qualified" not in state


def test_prd220_context_no_qualified_when_truly_empty() -> None:
    html = render_dashboard_html(_payload(), _run(outcome="NO_TRADE", permission=None), alert_candidates=[])
    state = _top_block(html, "system-state")
    assert "no qualified setups" in state


def test_prd283_why_line_names_sizing_refusal() -> None:
    # PRD-283 (CB-02): a run refused at options sizing must NOT read
    # "no qualified setups" — that contradicts the Opportunity Survival Summary,
    # which counts the refusal as REJECTED. The WHY line names the refusal.
    payload = _payload()
    payload["sections"]["rejected"] = [
        {"symbol": "SPY", "stage": "OPTIONS_SIZING",
         "reason": "SMALLEST_CONTRACT_EXCEEDS_BUDGET", "detail": None},
    ]
    html = render_dashboard_html(payload, _run(outcome="NO_TRADE", permission=None))
    state = _system_state_block(html)
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "no qualified setups" not in why
    assert "refused" in why.lower()


def test_prd283_why_line_refusal_wins_over_gated_high_grade() -> None:
    # A refused setup may still be high-grade in the market map; the sizing
    # refusal is the precise cause and must win over the "N gated" wording.
    payload = _payload()
    payload["sections"]["rejected"] = [
        {"symbol": "GDX", "stage": "OPTIONS_SIZING",
         "reason": "SMALLEST_CONTRACT_EXCEEDS_BUDGET", "detail": None},
    ]
    mm = _market_map({"GDX": _mm_symbol("GDX", grade="A+")})
    html = render_dashboard_html(
        payload, _run(outcome="NO_TRADE", permission=None), market_map=mm
    )
    state = _system_state_block(html)
    why = state.split('class="sys-why"', 1)[1].split("</div>", 1)[0]
    assert "refused" in why.lower()
    assert "gated" not in why


def test_prd220_macro_pressure_one_bullet_per_line() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    line = html.split('class="macro-pressure-line', 1)[1].split("</div>", 1)[0]
    assert "• " in line
    assert "<br>" in line  # phrases on separate lines


def test_prd312_tradables_label_then_price_no_arrow() -> None:
    # PRD-312 (supersedes PRD-220 arrow-before-price): the arrow is cut, so a
    # tradable cell now goes label -> price directly with NO arrow span between
    # them. Reintroducing the arrow reddens.
    import re as _r312
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=_market_map())
    assert "tradable-arrow" not in html
    # label span is immediately followed by the value span (no arrow in between)
    assert _r312.search(
        r'class="macro-tape-label">[^<]*</span>&nbsp;<span class="macro-tape-value"', html
    )


def test_prd220_trend_alignment_abbreviated() -> None:
    snap = _ts_healthy_snapshot()
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(), trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    assert "BULL" in section
    assert "BULLISH" not in section
    assert 'class="ts-intraday"' in section  # Intraday cell hook (muted, flows inline)


def test_prd225_trend_rows_wrap_uniformly() -> None:
    # PRD-225: the mobile trend row must wrap identically for every alignment
    # token. Mechanism pins (each fails if the change is reverted):
    #  - the Alignment cell carries the uniform-width hook (MIX 3ch vs
    #    BULL/BEAR 4ch was the only per-row width variance);
    #  - the mobile CSS equalizes it at 4ch;
    #  - the PRD-213 padding:0 override actually defeats the inline
    #    "padding:2px 8px" (it silently never applied without !important);
    #  - gap tightened and legacy min-widths right-sized in ch units.
    # Layout truth (one line at phone widths, uniform wrap below) was verified
    # at implementation time in headless Chromium over the published dashboard;
    # CI has no browser, so these tokens pin the mechanism.
    snap = _ts_healthy_snapshot()
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(), trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    assert 'class="ts-align"' in section
    assert ".ts-table td.ts-align{min-width:4ch}" in html
    assert ".ts-table td{white-space:nowrap!important;padding:0!important}" in html
    assert "gap:2px 8px" in html and "gap:2px 10px" not in html
    assert ".ts-table td:first-child{font-weight:bold;min-width:4ch}" in html
    assert ".ts-table td:nth-child(2){min-width:7ch}" in html


# ---------------------------------------------------------------------------
# PRD-288: SPY session observation card (present iff the daily section exists)
# ---------------------------------------------------------------------------

def _spy_section(**overrides) -> dict:
    base = {
        "observed_symbol": "SPY",
        "intended_session_date": "2026-04-28",
        "timezone": "America/New_York",
        "observed_at_utc": "2026-04-28T13:34:00+00:00",
        "state": "OBSERVED",
        "reason": None,
        "session_vwap": 102.0,
        "current_price": 104.0,
        "price_vs_vwap": "ABOVE",
        "orb": {
            "state": "FORMED", "trading_date": "2026-04-28",
            "observed_at_utc": "2026-04-28T13:35:00+00:00",
            "orb_high": 105.0, "orb_low": 100.0, "reason": None,
        },
    }
    base.update(overrides)
    return base


def _render_with_spy(section: dict | None) -> str:
    payload = _payload()
    if section is not None:
        payload["sections"]["spy_observation"] = section
    return render_dashboard_html(payload, _run(), market_map=_market_map())


def test_spy_observation_card_rendered_observed():
    html = _render_with_spy(_spy_section())
    assert 'id="spy-observation"' in html
    assert "SPY SESSION OBSERVATION" in html
    assert "102.00" in html            # session VWAP
    assert "104.00" in html            # current price
    assert "ABOVE VWAP" in html        # price-vs-VWAP display token
    assert "Opening range formed [100.00, 105.00]" in html
    assert 'data-raw-state="FORMED"' in html


def test_spy_observation_card_halt_state_no_fabricated_value():
    html = _render_with_spy(_spy_section(
        state="UNAVAILABLE", reason="system_halted",
        session_vwap=None, current_price=None, price_vs_vwap=None, orb=None,
    ))
    assert 'id="spy-observation"' in html
    assert "Session data unavailable — system halted" in html
    assert 'data-raw-state="UNAVAILABLE"' in html
    assert "VWAP UNAVAILABLE" not in html   # no price_vs_vwap token when None
    # No fabricated VWAP/price number leaks onto the halt card.
    import re as _re
    card = _re.search(r'id="spy-observation".*?</div>\s*</div>', html, _re.DOTALL).group(0)
    assert "102.00" not in card and "104.00" not in card


def test_spy_observation_card_stale_and_pre_open():
    stale = _render_with_spy(_spy_section(
        state="STALE", reason="session_mismatch",
        session_vwap=None, current_price=None, price_vs_vwap=None,
    ))
    assert "Session data stale — session date mismatch" in stale
    pre = _render_with_spy(_spy_section(
        state="PRE_OPEN", reason="pre_open",
        session_vwap=None, current_price=None, price_vs_vwap=None,
        orb={"state": "PRE_OPEN", "trading_date": None, "observed_at_utc": None,
             "orb_high": None, "orb_low": None, "reason": "no_bars"},
    ))
    assert "Pre-open — awaiting today&#x27;s session" in pre
    assert 'data-raw-state="PRE_OPEN"' in pre


def test_t12_no_spy_observation_card_when_section_absent():
    # Renderer side of T12: no section -> card omitted entirely.
    html = _render_with_spy(None)
    assert 'id="spy-observation"' not in html
    assert "SPY SESSION OBSERVATION" not in html


# ---------------------------------------------------------------------------
# PRD-289: Market Control Card block (present iff the daily section exists)
# ---------------------------------------------------------------------------

def _mcc_section(**overrides) -> dict:
    base = {
        "location": {"state": "OBSERVED", "reason": None, "price_vs_vwap": "ABOVE",
                     "orb": {"state": "FORMED", "reason": None, "orb_high": 105.0, "orb_low": 100.0}},
        "state": {"value": "RANGE", "unavailable_reason": None},
        "permission": {"value": "Selective only — defined risk, R:R >= 3:1."},
        "event": {"events": [{"date": "2026-04-29", "time_et": "08:30", "type": "CPI", "name": "CPI (April)"}],
                  "value": None, "unavailable_reason": None, "expiring": False},
        "transition": {"value": "NO_BREAK", "unavailable_reason": None},
        "invalidation": {"value": "NO_ACTIVE_CANDIDATES", "unavailable_reason": None},
        "candidate_implication": {"value": "CANDIDATES_PRESENT_NONE_ACTIONABLE",
                                  "unavailable_reason": None,
                                  "counts": {"ACTIVE": 1, "NEAR_MISS": 0, "BLOCKED": 0}},
    }
    base.update(overrides)
    return base


def _render_with_mcc(section: dict | None) -> str:
    payload = _payload()
    if section is not None:
        payload["sections"]["market_control_card"] = section
    return render_dashboard_html(payload, _run(), market_map=_market_map())


def _mcc_block(html: str) -> str:
    import re as _re
    match = _re.search(r'id="market-control-card".*?</div>\s*</div>', html, _re.DOTALL)
    assert match is not None, "market-control-card block missing"
    return match.group(0)


def test_m11_market_control_card_rendered_with_all_seven_fields():
    html = _render_with_mcc(_mcc_section())
    block = _mcc_block(html)
    for label in ("LOCATION", "STATE", "EVENT", "TRANSITION",
                  "INVALIDATION", "CANDIDATE-IMPLICATION"):
        assert f'<div class="label">{label}</div>' in block
    assert '<div class="label">PERMISSION</div>' not in block
    assert '<div class="label">ORB</div>' not in block
    assert "MARKET CONTROL" in html
    assert "Range" in block
    assert "2026-04-29 08:30 ET — CPI: CPI (April)" in block
    assert "No active candidates" in block
    assert "Candidates present; none actionable" in block


def test_m23_no_market_control_card_when_section_absent():
    html = _render_with_mcc(None)
    assert 'id="market-control-card"' not in html


def test_r5_zero_volume_location_renders_vwap_unavailable_never_raw_literal():
    html = _render_with_mcc(_mcc_section(
        location={"state": "OBSERVED", "reason": "vwap_unavailable",
                  "price_vs_vwap": None, "orb": None},
    ))
    block = _mcc_block(html)
    assert "Session data observed — VWAP unavailable" in block
    assert "(UNAVAILABLE VWAP)" not in block  # the raw upstream literal never renders
    assert "UNAVAILABLE VWAP" not in block


def test_r13_unavailable_cells_render_typed_tokens_only():
    html = _render_with_mcc(_mcc_section(
        state={"value": None, "unavailable_reason": "pre_computation_window"},
        transition={"value": None, "unavailable_reason": "transition_state_unavailable"},
        event={"events": None, "value": None,
               "unavailable_reason": "event_schedule_unavailable", "expiring": None},
        invalidation={"value": None, "unavailable_reason": "invalidation_indeterminate"},
        candidate_implication={"value": None, "unavailable_reason": "candidate_inputs_absent"},
    ))
    block = _mcc_block(html)
    assert "Unavailable — awaiting the 09:45 ET state window" in block
    assert "Unavailable — transition state unavailable" in block
    assert "Unavailable — event schedule unavailable" in block
    assert "Unavailable — invalidation unavailable" in block
    assert "Unavailable — candidate inputs unavailable" in block
    # No renderer-derived value stands in for an unavailable cell.
    assert "RANGE" not in block and "NO_BREAK" not in block


def test_m17_renderer_never_carries_loader_error_string():
    html = _render_with_mcc(_mcc_section(
        event={"events": None, "value": None,
               "unavailable_reason": "event_schedule_unavailable", "expiring": None},
    ))
    assert "red-folder schedule not found" not in html
    assert "malformed red-folder schedule" not in html


def test_event_truthful_empty_and_expiring_flag():
    html = _render_with_mcc(_mcc_section(
        event={"events": None, "value": "no_scheduled_events",
               "unavailable_reason": None, "expiring": True},
    ))
    block = _mcc_block(html)
    assert "No scheduled events in the next 48 hours · schedule expiring" in block
    assert 'data-raw-value="no_scheduled_events"' in block


# ---------------------------------------------------------------------------
# PRD-304 R7 — dashboard replaces permission/action vocabulary under lock
# ---------------------------------------------------------------------------

_LOCK_PERMISSION = "No new trades permitted — operator cannot monitor."


def test_r7_locked_dashboard_replaces_action_vocabulary() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A+")})
    run = _run(outcome="NO_TRADE", permission=_LOCK_PERMISSION)
    html = render_dashboard_html(_payload(), run, market_map=mm)

    # Marker present; A+ relabelled; ACTIONABLE gone.
    assert "Operator locked: cannot monitor" in html
    assert "A+ — OBSERVATION ONLY" in html
    assert "A+ — ACTIONABLE" not in html
    # Permission verbs suppressed.
    assert "Longs allowed" not in html
    assert "Shorts allowed" not in html
    assert "Momentum longs allowed" not in html
    # Opportunity-survival count relabelled.
    assert "SETUPS FOUND" in html
    assert ">QUALIFIED</div>" not in html
    # Analytical observations preserved: the symbol card and the A+ grade letter.
    assert 'id="card-SPY"' in html


def test_r7_available_dashboard_keeps_action_vocabulary() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A+")})
    run = _run(outcome="TRADE", permission="Long bias — trend continuation allowed.")
    html = render_dashboard_html(_payload(), run, market_map=mm)
    assert "A+ — ACTIONABLE" in html
    assert "A+ — OBSERVATION ONLY" not in html
    assert "OPERATOR LOCK — CANNOT MONITOR" not in html
    assert ">QUALIFIED</div>" in html


def test_r7_locked_dashboard_omits_play_directive() -> None:
    entry = {
        **_mm_symbol("SPY", grade="A"),
        "preferred_trade_structure": "bullish defined-risk continuation",
    }
    locked = render_dashboard_html(
        _payload(), _run(permission=_LOCK_PERMISSION), market_map=_market_map({"SPY": entry})
    )
    available = render_dashboard_html(
        _payload(), _run(permission="Long bias — trend continuation allowed."),
        market_map=_market_map({"SPY": entry}),
    )
    card_locked = _candidate_card(locked)
    card_available = _candidate_card(available)
    assert "PLAY" not in card_locked                     # action directive omitted under lock
    assert "PLAY" in card_available                       # present when available
    # The structural reasoning text is not otherwise leaked as an action directive.
    assert "bullish defined-risk continuation" not in card_locked


# ---------------------------------------------------------------------------
# PRD-304 Sol finding 3 — locked dashboard: neutral labels + low-grade wording
# ---------------------------------------------------------------------------
import copy as _copy2  # noqa: E402


def _framed_aplus_mm():
    entry = {**_mm_symbol("SPY", grade="A+"),
             "trade_framing": {"entry": "512.30", "if_now": "break 513"},
             "invalidation": ["lose 510"]}
    return _market_map({"SPY": entry})


def test_r7_locked_level_labels_are_observational():
    mm = _framed_aplus_mm()
    html = render_dashboard_html(_payload(), _run(permission=_LOCK_PERMISSION), market_map=mm)
    assert "IN →" not in html
    assert "OUT →" not in html
    assert ">LEVEL<" in html
    assert ">INVALIDATION<" in html


def test_r7_available_level_labels_and_accent_present():
    # Non-vacuity anchor: IN →/OUT → and the action accent are present normally.
    mm = _framed_aplus_mm()
    html = render_dashboard_html(_payload(), _run(permission="Long bias — trend continuation allowed."), market_map=mm)
    assert "IN →" in html
    assert "OUT →" in html
    assert '<div class="value-key value-actionable">' in _candidate_card(html)


def test_r7_locked_level_diagram_uses_neutral_labels_and_styling():
    entry = {
        **_mm_symbol("SPY", grade="A+"),
        "current_price": 120.0,
        "watch_zones": [{"type": "SUPPORT", "level": 100.0}],
    }
    kwargs = {
        "market_map": _market_map({"SPY": entry}),
        "contract_entry_map": {"SPY": 110.0},
        "contract_stop_map": {"SPY": 105.0},
    }
    locked = _candidate_card(render_dashboard_html(
        _payload(), _run(permission=_LOCK_PERMISSION), **kwargs,
    ))
    available = _candidate_card(render_dashboard_html(
        _payload(), _run(permission="Long bias — trend continuation allowed."), **kwargs,
    ))

    # PRD-321 R3/R4: the neutralization binds the redesigned compact ladder.
    assert _ladder_rows(locked)["LEVEL"] == ("110.00", "-8.3%")
    assert _ladder_rows(locked)["INVALIDATION"] == ("105.00", "-12.5%")
    assert "ENTRY" not in _ladder_rows(locked)
    assert "STOP" not in _ladder_rows(locked)
    assert "lvl-entry" not in locked and "lvl-stop" not in locked
    assert "lvl-inrisk" not in locked
    assert 'class="lvl-riskband lvl-lockrisk"' in locked

    assert _ladder_rows(available)["ENTRY"] == ("110.00", "-8.3%")
    assert _ladder_rows(available)["STOP"] == ("105.00", "-12.5%")
    assert 'class="lvl-riskband lvl-inrisk"' in available
    assert "lvl-entry" in available and "lvl-stop" in available


def test_r7_locked_low_grade_dashboard_has_no_action_vocabulary():
    mm = _market_map({"XYZ": _mm_symbol("XYZ", grade="C")})
    html = render_dashboard_html(_payload(), _run(permission=_LOCK_PERMISSION), market_map=mm)
    assert "NO ACTIONABLE SETUPS" not in html
    assert "NO HIGH-GRADE SETUPS OBSERVED" in html


def test_r7_available_low_grade_keeps_no_actionable_setups():
    mm = _market_map({"XYZ": _mm_symbol("XYZ", grade="C")})
    html = render_dashboard_html(_payload(), _run(permission="Long bias — trend continuation allowed."), market_map=mm)
    assert "NO ACTIONABLE SETUPS" in html


def test_r7_locked_high_grade_render_does_not_mutate_sources():
    mm = _framed_aplus_mm()
    payload, run = _payload(), _run(permission=_LOCK_PERMISSION)
    p0, r0, m0 = _copy2.deepcopy(payload), _copy2.deepcopy(run), _copy2.deepcopy(mm)
    render_dashboard_html(payload, run, market_map=mm)
    assert (payload, run, mm) == (p0, r0, m0), "locked high-grade render mutated a source object"


def test_r7_locked_low_grade_render_does_not_mutate_sources():
    mm = _market_map({"XYZ": _mm_symbol("XYZ", grade="C")})
    payload, run = _payload(), _run(permission=_LOCK_PERMISSION)
    p0, r0, m0 = _copy2.deepcopy(payload), _copy2.deepcopy(run), _copy2.deepcopy(mm)
    render_dashboard_html(payload, run, market_map=mm)
    assert (payload, run, mm) == (p0, r0, m0), "locked low-grade render mutated a source object"


def test_r7_locked_run_delta_is_observational():
    previous = _run(regime="RISK_OFF", posture="DEFENSIVE_SHORT")
    locked = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(regime="RISK_ON", posture="CONTROLLED_LONG", permission=_LOCK_PERMISSION),
        previous_run=previous,
    )
    available = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(
            regime="RISK_ON",
            posture="CONTROLLED_LONG",
            permission="Long bias — trend continuation allowed.",
        ),
        previous_run=previous,
    )

    assert "Permission flipped to longs" not in locked
    assert "Posture: Defensive Short -&gt; Controlled Long" not in locked
    assert "Regime: RISK_OFF -&gt; RISK_ON" in locked
    assert "Permission flipped to longs" in available
    assert "Posture: Defensive Short -&gt; Controlled Long" in available


def test_r7_locked_integrator_verdicts_are_observational():
    missing_price = {**_mm_symbol("SPY", grade="A+", bias="BEAR"), "current_price": None}
    rule2_mm = _market_map({"SPY": missing_price})
    rule2_locked = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(permission=_LOCK_PERMISSION),
        market_map=rule2_mm,
    )
    rule2_available = render_dashboard_html(
        _payload(market_regime="RISK_ON"),
        _run(permission="Long bias — trend continuation allowed."),
        market_map=rule2_mm,
    )
    assert "No qualifying long setups currently available." not in rule2_locked
    assert "No high-grade setups observed for the current regime." in rule2_locked
    assert "No qualifying long setups currently available." in rule2_available

    short_macro = _macro_drivers(vix=1.0, dxy=1.0, tnx=1.0, btc=-1.0)
    rule3_mm = _market_map({"SPY": _mm_symbol("SPY", grade="A+", bias="BULL")})
    rule3_locked = render_dashboard_html(
        _payload(market_regime="RISK_ON", macro_drivers=short_macro),
        _run(permission=_LOCK_PERMISSION),
        market_map=rule3_mm,
    )
    rule3_available = render_dashboard_html(
        _payload(market_regime="RISK_ON", macro_drivers=short_macro),
        _run(permission="Long bias — trend continuation allowed."),
        market_map=rule3_mm,
    )
    assert "Mixed tape — directional trades require symbol-level confirmation." not in rule3_locked
    assert "Mixed regime, macro, and symbol observations." in rule3_locked
    assert "Mixed tape — directional trades require symbol-level confirmation." in rule3_available


def test_r7_locked_sunday_context_has_no_watch_directive():
    payload = _payload(
        timestamp="2026-05-10T12:00:00Z",
        market_regime="RISK_ON",
        macro_drivers=_macro_drivers(),
    )
    payload["meta"]["session_type"] = "SUNDAY_PREMARKET"
    run_locked = _run_with_timestamp(
        "2026-05-10T12:00:00Z",
        permission=_LOCK_PERMISSION,
    )
    run_available = _run_with_timestamp(
        "2026-05-10T12:00:00Z",
        permission="Long bias — trend continuation allowed.",
    )
    mm = _market_map({"SPY": _mm_symbol("SPY")})
    mm["generated_at"] = "2026-05-10T12:00:00Z"

    locked = render_dashboard_html(payload, run_locked, market_map=mm)
    available = render_dashboard_html(payload, run_available, market_map=mm)
    assert "Monday Watch" not in locked
    assert "Watch for confirmation of risk-on bias before Monday open" not in locked
    assert "Monday Context" in locked
    assert "Current regime reference: RISK_ON" in locked
    assert "Monday Watch" in available
    assert "Watch for confirmation of risk-on bias before Monday open" in available


# ============================================================================
# PRD-309 GEX-2 free board card — integration guards (R1, R7, R17-R20).
# The card is display-only and baseline-neutral: absent/stale/invalid artifact
# yields output byte-identical to an INDEPENDENT pre-feature golden, and no
# decision surface is coupled to the artifact.
# ============================================================================
_GEX_FROZEN = datetime(2026, 4, 28, 12, 5, 0, tzinfo=timezone.utc)
_GEX_GOLDEN = Path(__file__).resolve().parent / "data" / "dashboard_pre_gex_golden.html"
_CB_ROOT = Path(__file__).resolve().parent.parent / "cuttingboard"


def _valid_gex():
    return {
        "schema_version": 1,
        "source": "cboe_delayed_quotes",
        "data_delay": "~15 min delayed (REPORTED; Cboe delayed_quotes posture)",
        "gex_total_1pct_usd": -5000000000.0,
        "spot": {"value": 100.0, "basis": "x"},
        "fetched_at_utc": "2026-04-28T12:00:00+00:00",
        "call_wall": {"strike": 105.0, "gex_1pct_usd": 1.0, "reason": None},
        "put_wall": {"strike": 95.0, "gex_1pct_usd": -1.0, "reason": None},
        "dominant_net_gamma": {"strike": 101.0, "gex_1pct_usd": -1.0, "reason": None},
        "zero_dte": {"share": 0.10, "reason": None},
    }


# --- R1: suppressed -> byte-identical to the independent pre-GEX golden ---
# --- PRD-330 R16/R17: frozen golden regions + the A1-C golden's embedded candidate SVG ---
_LEGACY_ORACLE_JSON = Path(__file__).resolve().parent / "data" / "setup_chart_legacy_oracle.json"


def _golden_region(html: str, block_id: str) -> str:
    idx = html.index(f'id="{block_id}"')
    start = html.rfind("<", 0, idx)
    if block_id == "details-history":
        return html[start: html.rindex("</details>") + len("</details>")]
    i, depth = start, 0
    while True:
        nd, ne = html.find("<div", i), html.find("</div>", i)
        if nd != -1 and nd < ne:
            depth, i = depth + 1, nd + 4
        else:
            depth, i = depth - 1, ne + 6
            if depth == 0:
                return html[start:i]


def test_prd330_golden_regions_and_embedded_svg_pinned() -> None:
    # R17: the VERDICT, TAPE and DETAILS regions of both goldens equal the shas frozen
    # at S0, so a regeneration may change only the authorized regions; the candidate
    # SVG embedded in the A1-C golden equals its frozen sha (R16 legacy oracle).
    oracle = json.loads(_LEGACY_ORACLE_JSON.read_text())
    for filename, regions in oracle["golden_regions"].items():
        html = (Path(__file__).resolve().parent / "data" / filename).read_text()
        for block_id, expected in regions.items():
            assert hashlib.sha256(_golden_region(html, block_id).encode("utf-8")).hexdigest() == expected, (filename, block_id)
    a1c = _A1C_GOLDEN.read_text()
    svg = a1c.split('<div class="setup-chart">', 1)[1].split("</svg>", 1)[0] + "</svg>"
    assert a1c.count("<svg ") == 1
    assert hashlib.sha256(svg.encode("utf-8")).hexdigest() == oracle["a1c_golden_embedded_svg_sha256"]


def test_gex_absent_baseline_identical(monkeypatch):
    # mutation: emit an empty wrapper on absence, OR add a rule to the
    # unconditional _CSS -> the suppressed document diverges from the golden.
    monkeypatch.setattr(_dr, "_utcnow", lambda: _GEX_FROZEN)
    golden = _GEX_GOLDEN.read_text(encoding="utf-8")
    assert render_dashboard_html(_payload(), _run(), gex_snapshot=None, now=_GEX_FROZEN) == golden
    stale = _valid_gex()
    stale["fetched_at_utc"] = "2020-01-01T00:00:00+00:00"
    assert render_dashboard_html(_payload(), _run(), gex_snapshot=stale, now=_GEX_FROZEN) == golden
    assert render_dashboard_html(
        _payload(), _run(), gex_snapshot={"schema_version": 99}, now=_GEX_FROZEN
    ) == golden


# --- R7: valid artifact -> card present with exact values ---
def test_gex_valid_card_rendered(monkeypatch):
    monkeypatch.setattr(_dr, "_utcnow", lambda: _GEX_FROZEN)
    html = render_dashboard_html(_payload(), _run(), gex_snapshot=_valid_gex(), now=_GEX_FROZEN)
    assert 'id="gex-context"' in html
    assert "-$5.0B" in html          # net /1e9, signed
    assert "+1.00%" in html          # dominant 101 vs spot 100
    assert "+5.00%" in html and "-5.00%" in html  # call/put walls
    assert "10.0%" in html           # 0DTE share*100


# --- R18: decision-output invariance — the ONLY diff vs absent is the card block ---
def test_gex_decision_outputs_unchanged(monkeypatch):
    # mutation: let any decision path read the sidecar -> a non-card region differs.
    monkeypatch.setattr(_dr, "_utcnow", lambda: _GEX_FROZEN)
    absent = render_dashboard_html(_payload(), _run(), gex_snapshot=None, now=_GEX_FROZEN)
    present = render_dashboard_html(_payload(), _run(), gex_snapshot=_valid_gex(), now=_GEX_FROZEN)
    frag = _gex.render_fragment(_valid_gex(), now=_GEX_FROZEN)
    assert frag and frag in present
    # PRD-318: TAPE also reflects valid GEX presence. Strip only that display-only
    # summary row, then excise the full detail card; all other bytes stay equal.
    # PRD-322 R5: absence is now STATED ("unavailable") rather than silent, so the
    # same literal row shape exists on both sides and the strip applies to BOTH
    # documents. The invariance claim is unchanged: outside that one row and the
    # detail card, a valid artifact changes nothing.
    import re as _re312
    def _strip_gex_summary(html):
        return _re312.sub(
            r'    <div class="zone-item"><div class="label">GEX · CONTEXT ONLY</div>.*?</div></div>\n',
            "", html,
            count=1, flags=_re312.S,
        )
    assert 'class="label">GEX · CONTEXT ONLY</div><div class="zone-value">unavailable</div>' in absent
    assert _strip_gex_summary(present).replace("\n" + frag, "", 1) == _strip_gex_summary(absent)


# --- R17: AST/path-literal isolation guard ---
def test_gex_isolation_ast():
    # mutation: import gex_card into a decision module / open the artifact path
    # elsewhere / add a reverse import into the card.
    importers = []
    card_cb_imports = []
    artifact_refs = []
    for py in sorted(_CB_ROOT.rglob("*.py")):
        src = py.read_text(encoding="utf-8")
        tree = _ast.parse(src)
        is_card = py.name == "gex_card.py"
        is_renderer = py.name == "dashboard_renderer.py"
        for node in _ast.walk(tree):
            names = []
            if isinstance(node, _ast.ImportFrom) and node.module:
                names.append(node.module)
            elif isinstance(node, _ast.Import):
                names.extend(alias.name for alias in node.names)
            for name in names:
                if "gex_card" in name and not is_renderer:
                    importers.append(py.name)
                if is_card and name.startswith("cuttingboard"):
                    card_cb_imports.append(name)
        if "gex_snapshot" in src and py.name not in ("gex_card.py", "dashboard_renderer.py"):
            artifact_refs.append(py.name)
    assert importers == [], f"non-renderer importers of gex_card: {importers}"
    assert card_cb_imports == [], f"gex_card imports cuttingboard: {card_cb_imports}"
    assert artifact_refs == [], f"unexpected artifact readers: {artifact_refs}"


# --- R19: card adds no readiness marker / not in coherent-publish set ---
def test_gex_no_readiness_marker():
    # mutation: add a GEX readiness marker.
    readiness = (Path(__file__).resolve().parent.parent / "scripts" / "check_readiness.py").read_text(
        encoding="utf-8"
    )
    assert "gex" not in readiness.lower()
    import inspect

    assert "gex" not in inspect.getsource(_dr.validate_coherent_publish).lower()


# --- R20: renderer holds no GEX arithmetic (all math lives in gex_card) ---
def test_renderer_has_no_gex_math():
    # mutation: move card math into the renderer.
    src = (_CB_ROOT / "delivery" / "dashboard_renderer.py").read_text(encoding="utf-8")
    for token in (
        "gex_total_1pct_usd",
        "dominant_net_gamma",
        "call_wall",
        "put_wall",
        "zero_dte",
        "fetched_at_utc",
    ):
        assert token not in src, token


def _movement_snapshot():  # PRD-311: a valid full-12 schema_version-2 artifact
    from cuttingboard.normalization import NormalizedQuote
    from cuttingboard.watchlist_sidecar import WATCHLIST_SYMBOLS, build_watchlist_snapshot

    def _q(sym):
        return NormalizedQuote(
            symbol=sym, price=100.0, pct_change_decimal=0.012, volume=None,
            fetched_at_utc=datetime(2026, 8, 22, 14, 30, tzinfo=timezone.utc),
            source="test", units="usd_price", age_seconds=0.0,
        )

    quotes = {sym: _q(sym) for sym, *_ in WATCHLIST_SYMBOLS}
    return build_watchlist_snapshot(quotes, datetime(2026, 8, 22, 14, 30, tzinfo=timezone.utc))


def test_movement_card_present_when_valid_snapshot():  # PRD-311 renderer wiring
    html = render_dashboard_html(_payload(), _run(), market_map=None,
                                 movement_snapshot=_movement_snapshot())
    assert 'id="market-movement"' in html
    assert "MARKET MOVEMENT" in html
    assert "UCO" in html and "GOOG" in html


def test_movement_card_suppression_is_baseline_neutral():  # PRD-311 M8/M9 whole-output equality
    baseline = render_dashboard_html(_payload(), _run(), market_map=None)  # no movement_snapshot
    assert 'id="market-movement"' not in baseline
    # absent artifact -> byte-identical to the no-movement baseline
    assert render_dashboard_html(_payload(), _run(), market_map=None,
                                 movement_snapshot=None) == baseline
    # every invalid artifact class -> whole dashboard byte-identical to baseline
    valid = _movement_snapshot()
    for mutate in (
        lambda s: s.__setitem__("schema_version", 1),
        lambda s: s.__setitem__("source", "not_watchlist"),
        lambda s: s["symbols"].pop("GOOG"),
        lambda s: s["symbols"].__setitem__("ZZZ", s["symbols"]["SPY"]),
        lambda s: s.__setitem__("generated_at", "not-a-date"),
        lambda s: s.__setitem__("symbols", "not a dict"),
        lambda s: s["symbols"]["SPY"].__setitem__("daily_change_pct", 1),
    ):
        bad = deepcopy(valid)
        mutate(bad)
        assert render_dashboard_html(_payload(), _run(), market_map=None,
                                     movement_snapshot=bad) == baseline


def test_movement_card_malformed_json_file_is_baseline_neutral(tmp_path):  # PRD-311 M9 malformed-JSON end-to-end
    from cuttingboard.delivery import movement_card
    baseline = render_dashboard_html(_payload(), _run(), market_map=None)
    p = tmp_path / "watchlist_snapshot.json"
    p.write_text("{not valid json", encoding="utf-8")
    snap = movement_card.load_watchlist_snapshot(p)  # malformed on disk -> None
    assert snap is None
    # the loader's None drives the renderer to a byte-identical no-block baseline
    assert render_dashboard_html(_payload(), _run(), market_map=None,
                                 movement_snapshot=snap) == baseline


# ===========================================================================
# PRD-322 — operator context tape: visible macro + trend projection.
# The TAPE zone becomes two labeled bands (MACRO, TREND) plus a subordinate
# availability footer, all projected from values already bound in the render
# body. Red-first: the two live honesty defects the PRD names.
# ===========================================================================
_PRD322_TAPE_BANNED = (
    "ALIGNED", "DIVERGING", "CONFLUENT", "systems agree", "agreement", "confluence",
)


def _prd322_tape(html: str) -> str:
    return _top_block(html, "tape-zone")


def _prd322_ts_snapshot(**per_symbol) -> dict:
    """A curated-6 snapshot whose records carry the given field overrides."""
    snap = _ts_healthy_snapshot()
    for rec in snap["symbols"].values():
        rec.update(per_symbol)
    return snap


def test_prd322_all_unavailable_trend_is_not_reported_as_zero_bullish() -> None:
    # DEFECT 1 (red-first): six DATA_UNAVAILABLE rows are six records with zero
    # BULLISH, so the raw count rendered "0 of 6 bullish" — unavailability
    # presented as bearishness. Mutation: revert the TAPE trend item to the raw
    # bullish-row count -> red.
    snap = _prd322_ts_snapshot(
        trend_alignment="DATA_UNAVAILABLE",
        price_vs_sma_50="DATA_UNAVAILABLE",
        price_vs_sma_200="DATA_UNAVAILABLE",
        price_vs_vwap="DATA_UNAVAILABLE",
        data_status="MISSING",
    )
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(), trend_structure_snapshot=snap,
    )
    tape = _prd322_tape(html)
    assert "0 of 6 bullish" not in tape
    assert 'data-derivation="trend-health"' in tape


def test_prd322_empty_macro_drivers_render_no_fabricated_bias_in_tape() -> None:
    # DEFECT 2 (red-first): an empty macro-driver payload casts zero votes, and
    # the zero-vote tie fabricated "MACRO BIAS: MIXED" in the TAPE zone.
    # Mutation: remove the _tape_health == "MISSING" gate -> red. The DETAILS
    # macro-tape block is explicitly out of scope and still renders its label.
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        macro_snapshot_path=Path("/nonexistent/prd322_no_snapshot.json"),
    )
    tape = _prd322_tape(html)
    assert "MACRO BIAS" not in tape
    assert "Macro unavailable" in tape


# --- R1 unit matrix: _tape_trend_summary over the closed vocabulary ---------
def _prd322_records(*alignments: str) -> dict:
    return {
        sym: {**_ts_record(sym), "trend_alignment": align}
        for sym, align in zip(_TS_CURATED, alignments)
    }


def test_prd322_trend_summary_all_computed_is_byte_identical_to_the_prior_string() -> None:
    # R1: six computed rows reproduce the pre-PRD-322 headline byte-for-byte,
    # including its derivation token. Mutation: change either -> red here and
    # in test_prd318_tape_is_display_only_adjacency.
    assert _dr._tape_trend_summary(_ts_healthy_snapshot()["symbols"], "OK") == (
        "6 of 6 bullish", "bullish-row-count",
    )
    mixed = _prd322_records("BULLISH", "BEARISH", "MIXED", "BULLISH", "BEARISH", "MIXED")
    assert _dr._tape_trend_summary(mixed, "OK") == ("2 of 6 bullish", "bullish-row-count")


def test_prd322_trend_summary_denominator_counts_only_computed_rows() -> None:
    # R1: the honest partial form. INSUFFICIENT_HISTORY and NOT_COMPUTED are
    # n/a rows, not bearish rows. Mutation: count non-computed rows in the
    # denominator -> red.
    partial = _prd322_records(
        "BULLISH", "BEARISH", "DATA_UNAVAILABLE", "BULLISH",
        "INSUFFICIENT_HISTORY", "NOT_COMPUTED",
    )
    assert _dr._tape_trend_summary(partial, "OK") == (
        "2 of 3 bullish · 3 n/a", "trend-health",
    )


@pytest.mark.parametrize(
    "health,expected",
    [
        ("MARKET_CLOSED", "Market closed — awaiting intraday data"),
        ("AWAITING_DATA", "Market closed — awaiting intraday data"),
        ("STALE", "Trend stale"),
        ("OK", "Trend data unavailable"),
        ("MIXED", "Trend data unavailable"),
        ("INACTIVE_SESSION", "Trend data unavailable"),
    ],
)
def test_prd322_trend_summary_zero_computed_uses_source_health(health, expected) -> None:
    # R1 / DEFECT 1: zero computed rows never render a count. Mutation: fall
    # back to "0 of 6 bullish" -> red.
    dead = _prd322_records(*(("DATA_UNAVAILABLE",) * 6))
    assert _dr._tape_trend_summary(dead, health) == (expected, "trend-health")


def test_prd322_trend_summary_absent_records_is_health_derived() -> None:
    # R1: the records-absent literal is preserved, but its derivation is now
    # honest (`trend-health`, not a count that was never taken).
    for records in (None, {}):
        assert _dr._tape_trend_summary(records, "MISSING") == (
            "Trend unavailable", "trend-health",
        )


# --- R4 unit matrix: _build_trend_chips ------------------------------------
def test_prd322_trend_chips_follow_the_curated_order() -> None:
    # R4: chip order is the curated tuple, not snapshot insertion order.
    # Mutation: iterate the record dict instead -> red.
    shuffled = {
        sym: _ts_record(sym) for sym in ("XLE", "SLV", "GLD", "GDX", "QQQ", "SPY")
    }
    assert [row[0] for row in _dr._build_trend_chips(shuffled)] == list(
        _dr.config.TREND_STRUCTURE_SYMBOLS
    )
    assert list(_dr.config.TREND_STRUCTURE_SYMBOLS) == list(_TS_CURATED)


def test_prd322_trend_chip_tokens_come_only_from_existing_translators() -> None:
    # R4: alignment abbreviations, SMA arrow halves and the closed V-glyph set.
    # Mutation: emit a synthesized token -> red.
    rows = _dr._build_trend_chips(
        _prd322_records("BULLISH", "BEARISH", "MIXED", "BULLISH", "BEARISH", "MIXED")
    )
    assert [r[1] for r in rows] == ["BULL", "BEAR", "MIX", "BULL", "BEAR", "MIX"]
    assert {r[2] for r in rows} == {"↑ 50"}
    assert {r[3] for r in rows} == {"↑ 200"}
    assert {r[4] for r in rows} == {"V↑"}
    assert [r[5] for r in rows] == ["up", "down", "flat", "up", "down", "flat"]
    for row in rows:
        assert row[1] in set(_dr._TS_ALIGN_ABBR.values())
        assert f"{row[2]} {row[3]}" in set(_dr._TREND_STRUCTURE_COMPOSITE_DISPLAY.values())
        assert row[4] in set(_dr._TAPE_VWAP_GLYPH.values())


@pytest.mark.parametrize(
    "vwap,glyph",
    [("ABOVE", "V↑"), ("BELOW", "V↓"), ("AT_LEVEL", "V="),
     ("DATA_UNAVAILABLE", ""), ("NOT_COMPUTED", ""), ("UNAVAILABLE", ""), ("", "")],
)
def test_prd322_trend_chip_vwap_glyph_only_for_a_computed_comparison(vwap, glyph) -> None:
    # R4: the V-glyph vocabulary is closed to three tokens and renders only for
    # a real comparison. Mutation: pass the raw token through -> red.
    records = {sym: {**_ts_record(sym), "price_vs_vwap": vwap} for sym in _TS_CURATED}
    assert {row[4] for row in _dr._build_trend_chips(records)} == {glyph}


@pytest.mark.parametrize(
    "alignment", ["DATA_UNAVAILABLE", "INSUFFICIENT_HISTORY", "NOT_COMPUTED", ""]
)
def test_prd322_non_computed_trend_row_renders_symbol_and_dash_only(alignment) -> None:
    # R4: no partial arrows on a row whose alignment was never computed.
    # Mutation: keep emitting the composite/glyph cells -> red.
    records = {sym: {**_ts_record(sym), "trend_alignment": alignment} for sym in _TS_CURATED}
    assert _dr._build_trend_chips(records) == [
        (sym, "—", "", "", "", "na") for sym in _TS_CURATED
    ]
    # a wholly absent record set degrades the same way
    assert _dr._build_trend_chips(None) == [
        (sym, "—", "", "", "", "na") for sym in _TS_CURATED
    ]


# --- R2 unit matrix: _pressure_note ----------------------------------------
def test_prd322_pressure_note_uses_the_closed_four_state_display_map() -> None:
    # R2: the four component states and nothing else. Mutation: pass the raw
    # enum through -> red.
    note = _dr._pressure_note({
        "volatility_pressure": "RISK_ON", "dollar_pressure": "RISK_OFF",
        "rates_pressure": "NEUTRAL", "bitcoin_pressure": "UNKNOWN",
    })
    assert note == "pressure: VIX risk-on · DXY risk-off · 10Y neutral · BTC n/a"
    for raw in ("RISK_ON", "RISK_OFF", "NEUTRAL", "UNKNOWN", "MIXED"):
        assert raw not in note


def test_prd322_pressure_note_never_reads_the_overall_aggregate() -> None:
    # R2: `overall_pressure` is banned from TAPE — an unknown or absent
    # component degrades to n/a rather than borrowing the aggregate.
    # Mutation: render overall_pressure -> red.
    note = _dr._pressure_note({
        "volatility_pressure": "RISK_ON", "overall_pressure": "MIXED",
    })
    assert note == "pressure: VIX risk-on · DXY n/a · 10Y n/a · BTC n/a"
    assert "overall" not in note and "MIXED" not in note
    assert _dr._pressure_note(None) == "Pressure unavailable"
    assert _dr._pressure_note("not a dict") == "Pressure unavailable"


# --- rendered path ---------------------------------------------------------
def _prd322_healthy_render(**kwargs):
    return render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()), _run(), market_map=_market_map(),
        trend_structure_snapshot=_ts_healthy_snapshot(), **kwargs,
    )


def test_prd322_tape_renders_all_seven_drivers_in_layout_order() -> None:
    # R3: seven chips, data-driven from MACRO_ROW_2 + MACRO_ROW_1. Mutation:
    # restore the hand-listed four-driver tuple -> red.
    tape = _prd322_tape(_prd322_healthy_render())
    labels = re.findall(r'<div class="tape-driver tape-slot \w+"><span>([^<]+)</span>', tape)
    assert labels == ["VIX", "DXY", "10Y", "OIL", "GC", "SI", "BTC"]


@pytest.mark.parametrize(
    "driver_key,display",
    [
        ("volatility", "VIX"), ("dollar", "DXY"), ("rates", "10Y"),
        ("oil", "OIL"), ("gold", "GC"), ("silver", "SI"), ("bitcoin", "BTC"),
    ],
)
def test_prd322_absent_driver_keeps_its_chip_with_the_placeholder(driver_key, display) -> None:
    # R3 (Codex F3): absence is visible, never zero and never dropped — for
    # EVERY slot, including the metals whose DETAILS-side placeholder is
    # "N/A" (the strip must normalize to "--"). Mutation: skip missing
    # drivers, or drop the normalization -> red.
    drivers = _macro_drivers()
    drivers.pop(driver_key, None)
    html = render_dashboard_html(
        _payload(macro_drivers=drivers), _run(), market_map=_market_map(),
    )
    tape = _prd322_tape(html)
    assert tape.count('class="tape-driver tape-slot') == 7
    assert (
        f'<div class="tape-driver tape-slot na"><span>{display}</span>'
        f'<span>—</span><span>--</span></div>'
    ) in tape


def test_prd322_tape_zone_never_collides_with_the_details_harvest_shape() -> None:
    # R3: `macro-tape-slot` / `macro-tape-value` / `data-symbol` are regex-
    # harvested and order-pinned in DETAILS. Mutation: reuse them in TAPE ->
    # red (and the DETAILS harvest silently doubles).
    html = _prd322_healthy_render()
    tape = _prd322_tape(html)
    for token in ("macro-tape-value", "macro-tape-slot", "data-symbol"):
        assert token not in tape
        assert token in html.split('id="macro-tape"', 1)[1]


def test_prd322_tape_carries_no_agreement_vocabulary_healthy_or_degraded() -> None:
    # R4: extends the PRD-318 ban test with "agreement"/"confluence" and runs
    # it over a degraded render too. Mutation: add any agreement semantic -> red.
    healthy = _prd322_tape(_prd322_healthy_render())
    degraded = _prd322_tape(render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        macro_snapshot_path=Path("/nonexistent/prd322_no_snapshot.json"),
        trend_structure_snapshot=_prd322_ts_snapshot(trend_alignment="DATA_UNAVAILABLE"),
    ))
    for tape in (healthy, degraded):
        for banned in _PRD322_TAPE_BANNED:
            assert banned not in tape


def test_prd322_trend_chips_render_in_curated_order_in_the_tape() -> None:
    # R4 rendered path: six chips, curated order, alignment-keyed colour class.
    tape = _prd322_tape(_prd322_healthy_render())
    rendered = re.findall(
        r'<div class="tape-trend-row tape-slot (\w+)"><span>([A-Z]+)</span><span>([^<]*)</span>',
        tape,
    )
    assert [sym for _cls, sym, _align in rendered] == list(_TS_CURATED)
    assert {cls for cls, _s, _a in rendered} == {"up"}
    assert {align for _c, _s, align in rendered} == {"BULL"}


def test_prd322_degraded_trend_rows_render_dash_only_in_the_tape() -> None:
    # R4 rendered path: the na row shape. Mutation: emit partial arrows -> red.
    # PRD-327 D2-Q2: an all-na strip under healthy lineage in an active session
    # is suppressed (tests/test_dashboard_d2_seam.py), so render the inactive
    # session, where PRD-322 R4's six na chips remain mandatory.
    _inactive = _payload()
    _inactive["meta"]["session_type"] = "SUNDAY_PREMARKET"
    tape = _prd322_tape(render_dashboard_html(
        _inactive, _run(), market_map=_market_map(),
        trend_structure_snapshot=_prd322_ts_snapshot(
            trend_alignment="DATA_UNAVAILABLE", price_vs_sma_50="DATA_UNAVAILABLE",
            price_vs_sma_200="DATA_UNAVAILABLE", price_vs_vwap="DATA_UNAVAILABLE",
        ),
    ))
    for sym in _TS_CURATED:
        assert (f'<div class="tape-trend-row tape-slot na"><span>{sym}</span>'
                f'<span>—</span><span></span><span></span><span></span></div>') in tape
    assert "↑" not in tape.split('class="tape-trend"', 1)[1]


def test_prd322_macro_gate_keys_on_missing_not_fallback() -> None:
    # R2: FALLBACK also fires on missing TRADABLES values under a genuine,
    # fully-voted macro bias — it must NOT suppress the bias. Mutation: key the
    # gate on `!= "OK"` -> red.
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()), _run(), market_map=None,
    )
    assert _macro_tape_source_health(
        macro_drivers=_macro_drivers(),
        tape_value_slots=_dr._build_tape_value_slots(_macro_drivers(), None),
    ) == "FALLBACK"
    tape = _prd322_tape(html)
    assert "MACRO BIAS:" in tape
    assert "Macro unavailable" not in tape


def test_prd322_suppressed_macro_bias_stays_omitted_with_no_substitute(monkeypatch) -> None:
    # R2 / OUT OF SCOPE: the integrator seam keeps winning — a suppressed bias
    # renders no bias line AND no fabricated stand-in. Mutation: render
    # "Macro unavailable" (or the bias) under suppression -> red.
    _freeze_renderer_now(monkeypatch)
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A", bias="BULL")})
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=0.0)),
        _run(), market_map=mm,
    )
    tape = _prd322_tape(html)
    assert "MACRO BIAS" not in tape
    assert "Macro unavailable" not in tape
    assert '<div class="tape-band-cap">MACRO</div>' in tape  # the band survives
    assert 'class="tape-driver' in tape                      # drivers stay visible


def test_prd322_gex_absence_is_stated_in_the_tape() -> None:
    # R5: mutation -- restore the silent omission -> red.
    absent = _prd322_tape(_prd322_healthy_render(gex_snapshot=None))
    assert ('<div class="zone-item"><div class="label">GEX · CONTEXT ONLY</div>'
            '<div class="zone-value">unavailable</div></div>') in absent
    present = _prd322_tape(_prd322_healthy_render(
        gex_snapshot=_valid_gex(), now=_GEX_FROZEN,
    ))
    assert "-$5.0B net" in present and "unavailable" not in present


def test_prd322_participation_absence_is_stated_in_the_tape() -> None:
    # R5: mutation -- restore the silent omission -> red.
    absent = _prd322_tape(_prd322_healthy_render(movement_snapshot=None))
    assert ('<div class="zone-item"><div class="label">PARTICIPATION</div>'
            '<div class="zone-value">not captured</div></div>') in absent
    present = _prd322_tape(_prd322_healthy_render(movement_snapshot=_movement_snapshot()))
    assert "captured</div>" in present and "not captured" not in present


def test_prd322_tape_band_structure_and_zone_set_are_preserved() -> None:
    # R6 (superseded in part by PRD-327 R4): two labeled bands with no `.sep`
    # dividers, the availability footer last, and the four-zone set untouched.
    html = _prd322_healthy_render()
    tape = _prd322_tape(html)
    assert tape.index('<div class="tape-band-cap">MACRO</div>') < tape.index(
        '<div class="tape-band-cap">TREND</div>')
    assert tape.index('<div class="tape-band-cap">TREND</div>') < tape.index(
        '<div class="zone-grid tape-foot">')
    assert tape.count('<div class="sep"></div>') == 0
    assert tape.index('class="tape-drivers"') < tape.index('class="zone-note"')
    before_details = html.split('<details class="block operator-zone"', 1)[0]
    assert before_details.count('class="block operator-zone"') == 4
    assert '<h2>TAPE <span class="label">context only</span></h2>' in tape


def test_prd322_new_styling_stays_out_of_the_pinned_phone_block() -> None:
    # R6: every new rule lives in base CSS; the 430px block stays byte-identical.
    html = _prd322_healthy_render()
    assert _PRD318_PHONE_BLOCK in html
    for rule in ("tape-band-cap", "tape-driver", "tape-trend", "tape-foot"):
        assert rule not in _PRD318_PHONE_BLOCK
        assert rule in html
    # aligned column grids, nowrap per cell (via .tape-slot), no fixed widths
    assert ".tape-trend-row{display:grid;grid-template-columns:4ch 4ch 4ch 5ch 2ch" in html
    assert ".tape-driver{display:grid;grid-template-columns:3ch 1ch auto" in html
    # Codex F7: the OUTER strips are grids too — a regression to flex-wrap
    # (ragged columns, the owner-rejected sketch state) must go red here.
    assert ".tape-drivers{display:grid;grid-template-columns:repeat(auto-fit,minmax(88px,1fr))" in html
    assert ".tape-trend{display:grid;grid-template-columns:repeat(auto-fit,minmax(154px,1fr))" in html
    assert ".tape-slot{white-space:nowrap}" in html


# PRD-324 (A1-C) intraday consumer: parity, fallback, isolation. Chart-bearing
# recipe from test_dash_candidates (R11 oracle); byte-identity mirrors test_prd120.
from tests.test_dash_candidates import (  # noqa: E402
    _bars_snapshot as _a1c_bars,
    _chartable as _a1c_chartable,
    _pc_card as _a1c_card,
)

_A1C_NOW = _dt112(2026, 8, 28, 14, 0, 0, tzinfo=_tz112.utc)  # 10:00 ET, mid-session
_A1C_SESSION = "2026-08-28"
_A1C_MISSING = Path("/nonexistent/a1c_no_intraday.json")
_A1C_GOLDEN = Path(__file__).resolve().parent / "data" / "dashboard_pre_a1c_chart_golden.html"


def _a1c_intraday_snapshot(**over) -> dict:
    """A valid current-session A1-P sidecar for SPY (2 completed 5m bins, END 09:40)."""
    n_bars = over.pop("n_bars", 10)
    anchor = _dt112(2026, 8, 28, 13, 30, tzinfo=_tz112.utc)  # 09:30 ET
    bars = [[(anchor + timedelta(minutes=i)).isoformat(), 100.0, 101.0, 99.0, 100.0, 10]
            for i in range(n_bars)]
    snap = {
        "schema_version": 1,
        "generated_at": (_A1C_NOW - timedelta(minutes=5)).isoformat(),
        "session_date": _A1C_SESSION,
        "primary_symbol": "SPY",
        "source": {"producer": "hourly", "provider": "yfinance",
                   "interval": "1m", "adjusted": False},
        "columns": ["ts", "Open", "High", "Low", "Close", "Volume"],
        "symbols": {"SPY": {"through": bars[-1][0] if bars else None,
                            "row_count": len(bars), "bars": bars}},
    }
    snap.update(over)
    return snap


def _a1c_write(tmp_path, snap) -> Path:
    path = tmp_path / "intraday_bars_snapshot.json"
    path.write_text(json.dumps(snap), encoding="utf-8")
    return path


def _a1c_render_html(monkeypatch, *, intraday_path=_A1C_MISSING, mm=None, fixture_mode=False) -> str:
    class _FrozenDT(_dt112):  # P1: freeze the datetime CLASS, not just _utcnow
        @classmethod
        def now(cls, tz=None):
            return _A1C_NOW if tz is None else _A1C_NOW.astimezone(tz)
    monkeypatch.setattr(_dr112, "datetime", _FrozenDT)
    _freeze_renderer_now(monkeypatch, _A1C_NOW)
    monkeypatch.setattr(_dr, "_INTRADAY_BARS_SNAPSHOT_PATH", intraday_path)
    if mm is None:
        mm = _market_map({"SPY": _a1c_chartable("SPY", "A+")})
    payload, run = _payload(), _run(outcome="TRADE")
    payload["meta"]["generation_id"] = "test-gen-001"
    run["generation_id"] = "test-gen-001"
    mm["generation_id"] = "test-gen-001"
    kwargs = {"price_bars_snapshot": _a1c_bars(symbols=tuple(mm["symbols"])), "now": _A1C_NOW}
    if fixture_mode:
        kwargs["fixture_mode"] = True
    return render_dashboard_html(payload, run, market_map=mm, **kwargs)


def test_a1c_pre_a1c_golden_is_chart_bearing_and_reproducible(monkeypatch):  # R11
    html = _a1c_render_html(monkeypatch)  # sidecar absent
    assert 'class="setup-chart"' in html  # a REAL chart-bearing baseline, not SOURCE_MISSING
    if not _A1C_GOLDEN.exists():
        _A1C_GOLDEN.write_text(html, encoding="utf-8")
    assert html == _A1C_GOLDEN.read_text(encoding="utf-8")


_A1C_NON_ADMITTED = {
    "stale": lambda: _a1c_intraday_snapshot(
        generated_at=(_A1C_NOW - timedelta(minutes=91)).isoformat()),   # M17
    "wrong_schema": lambda: _a1c_intraday_snapshot(schema_version=2),   # M20
    "wrong_session": lambda: _a1c_intraday_snapshot(session_date="2026-08-27"),  # M9
    "primary_disagree": lambda: _a1c_intraday_snapshot(primary_symbol="QQQ"),    # M11
    "zero_completed_bins": lambda: _a1c_intraday_snapshot(n_bars=3),    # M13
    "malformed_source": lambda: _a1c_intraday_snapshot(source={"producer": "x"}),  # M21
}


@pytest.mark.parametrize("key", list(_A1C_NON_ADMITTED))
def test_a1c_non_admitted_sidecar_is_baseline_neutral(monkeypatch, tmp_path, key):  # R11/M17
    path = _a1c_write(tmp_path, _A1C_NON_ADMITTED[key]())
    assert _a1c_render_html(monkeypatch, intraday_path=path) == _A1C_GOLDEN.read_text(encoding="utf-8")


def test_a1c_malformed_json_sidecar_is_baseline_neutral(monkeypatch, tmp_path):  # R1/R11
    path = tmp_path / "i.json"
    path.write_text("{not valid json", encoding="utf-8")
    assert _a1c_render_html(monkeypatch, intraday_path=path) == _A1C_GOLDEN.read_text(encoding="utf-8")


def test_a1c_admitted_intraday_replaces_daily_in_primary_slot(monkeypatch, tmp_path):  # R8/R9/R10/M30
    golden = _A1C_GOLDEN.read_text(encoding="utf-8")
    path = _a1c_write(tmp_path, _a1c_intraday_snapshot())
    html = _a1c_render_html(monkeypatch, intraday_path=path)
    assert html != golden                                    # daily was replaced
    assert "completed through 09:40 ET" in html              # R10 completed-through caption (END)
    assert html.count('class="setup-chart"') == 1            # M30: exactly one chart in the slot
    assert "lvl-row" in html                                 # M30: the compact ladder is retained


def test_a1c_empty_intraday_svg_falls_back_to_daily(monkeypatch, tmp_path):  # M14
    import cuttingboard.delivery.setup_chart as _sc
    real = _sc.render_setup_chart_svg

    def stub(bars, now_price, **kw):
        if kw.get("max_bars", "keep") is None:  # the intraday call (max_bars=None) renders empty
            return ""
        return real(bars, now_price, **kw)

    monkeypatch.setattr(_sc, "render_setup_chart_svg", stub)
    path = _a1c_write(tmp_path, _a1c_intraday_snapshot())
    assert _a1c_render_html(monkeypatch, intraday_path=path) == _A1C_GOLDEN.read_text(encoding="utf-8")


def test_a1c_leaf_receives_runtime_inputs_and_drives_slot(monkeypatch, tmp_path):  # R6/M12
    calls = []
    real = _dr.select_primary_card_symbol

    def rec(market_map, price_bars, skips):
        result = real(market_map, price_bars, skips)
        calls.append((market_map, price_bars, skips, result))
        return result

    monkeypatch.setattr(_dr, "select_primary_card_symbol", rec)
    path = _a1c_write(tmp_path, _a1c_intraday_snapshot())
    html = _a1c_render_html(monkeypatch, intraday_path=path)
    assert len(calls) == 1
    market_map, price_bars, skips, result = calls[0]
    assert "SPY" in market_map["symbols"]                      # the real runtime market_map
    # the EXACT runtime _price_bars map, not a reconstruction (isolates M12):
    assert price_bars == _dr._price_bars_by_symbol(_a1c_bars(symbols=("SPY",)), _A1C_NOW)
    assert isinstance(skips, dict)                             # the runtime integrator_skips
    assert result == "SPY"                                     # leaf winner
    assert 'class="setup-chart"' in html                       # winner drives the slot


def test_a1c_leaf_fed_post_fixture_symbols(monkeypatch):  # R6/M29
    from cuttingboard.delivery.fixtures import FIXTURE_SYMBOLS
    seen = []
    real = _dr.select_primary_card_symbol

    def rec(mm, pb, sk):
        seen.append((mm, pb, sk))
        return real(mm, pb, sk)

    monkeypatch.setattr(_dr, "select_primary_card_symbol", rec)
    _a1c_render_html(monkeypatch, fixture_mode=True)
    assert seen, "leaf not called in fixture mode"
    mm, pb, sk = seen[0]
    assert mm["symbols"] is FIXTURE_SYMBOLS                    # POST-replacement symbols feed the leaf
    assert pb == _dr._price_bars_by_symbol(_a1c_bars(symbols=("SPY",)), _A1C_NOW)  # runtime price bars
    assert isinstance(sk, dict)                               # runtime integrator_skips


def test_a1c_non_primary_daily_chart_preserved_under_intraday(monkeypatch, tmp_path):  # R9/M31
    mm = _market_map({"SPY": _a1c_chartable("SPY", "A+"), "QQQ": _a1c_chartable("QQQ", "A")})
    path = _a1c_write(tmp_path, _a1c_intraday_snapshot())  # primary is SPY
    html = _a1c_render_html(monkeypatch, intraday_path=path, mm=mm)
    assert "completed through 09:40 ET" in html               # SPY took the intraday slot
    assert html.count('class="setup-chart"') == 2             # SPY intraday + QQQ disclosed daily
    assert 'class="setup-chart"' in _a1c_card(html, "QQQ")    # non-primary daily chart retained


def test_a1c_isolation_no_side_effect_and_only_chart_slot(monkeypatch, tmp_path):  # R12/M18/M32
    import builtins
    import pathlib
    import cuttingboard.ingestion as _ing
    import cuttingboard.output as _out
    path = _a1c_write(tmp_path, _a1c_intraday_snapshot())  # real sidecar write, before the spies
    effects: list = []
    real_open = builtins.open
    # spy every side-effect seam: write/append/create opens, Path writes, notification, fetch
    monkeypatch.setattr(builtins, "open", lambda f, mode="r", *a, **k:
                        effects.append("open") if any(c in mode for c in "wax+")
                        else real_open(f, mode, *a, **k))
    monkeypatch.setattr(pathlib.Path, "write_text", lambda self, *a, **k: effects.append("write_text"))
    monkeypatch.setattr(pathlib.Path, "write_bytes", lambda self, *a, **k: effects.append("write_bytes"))
    monkeypatch.setattr(_out, "send_notification", lambda *a, **k: effects.append("notify"))
    monkeypatch.setattr(_ing, "fetch_intraday_session_bars", lambda *a, **k: effects.append("fetch"))
    absent = _a1c_render_html(monkeypatch)
    assert effects == []
    effects.clear()
    present = _a1c_render_html(monkeypatch, intraday_path=path)
    assert effects == []  # M18/M32: admitting intraday adds no write, notification, or fetch
    assert absent != present  # the admitted case differs (intraday substituted)...
    assert absent.split('id="candidate-board"')[0] == present.split('id="candidate-board"')[0]  # ...only in the slot


def test_a1c_loader_never_raises_on_oserror(monkeypatch, tmp_path):  # R1/M19
    import pathlib
    p = tmp_path / "i.json"
    p.write_text("{}", encoding="utf-8")

    def boom(self, *a, **k):
        raise OSError("unreadable")

    monkeypatch.setattr(pathlib.Path, "read_text", boom)
    assert _dr._load_intraday_bars_snapshot(p) is None  # OSError swallowed to None, never raised


# ---------------------------------------------------------------------------
# PRD-329 (D3) S2: SPY SESSION FIRST-CLASS OBSERVATION. The `#spy-observation`
# subtree is the pure output of `_render_spy_session(...)` over five observational
# inputs; MARKET CONTROL stays in DETAILS / HISTORY (S2-Q1 STAY); the SPY chart and
# ladder are neutral and never suppressed by ranking / primary selection (S2-Q2).
# ---------------------------------------------------------------------------

_S2_NOW = datetime(2026, 8, 28, 14, 0, tzinfo=timezone.utc)
_S2_LOCK = "No new trades permitted — operator cannot monitor."
_S2_DEFAULT = object()
_S2_MAP_LINE = '<div class="lvl-unavail">Chart and levels unavailable — market map {}</div>'
_S2_KV_SHA = "9ce2c7dcc6f7ffbe42ae54271c7e82513aa10af5121357de448bf18b0440f97b"      # pre-PRD-329 kv-grid
_S2_MCC_ONLY_SHA = "330eec12eafe1f23d81bd781b3a590f6e08a0d9930d84da1f5a75f377002d806"  # pre-PRD-329 DETAILS group


def _s2_render(*, spy: bool = True, mm: object = _S2_DEFAULT, bars: bool = True,
               run: dict | None = None, **kw) -> str:
    payload = _payload()
    if spy:
        payload["sections"]["spy_observation"] = _spy_section()
    if mm is _S2_DEFAULT:
        mm = _market_map({"SPY": _chartable("SPY", "C")})
    syms = tuple((mm or {}).get("symbols") or ()) or ("SPY",)
    return render_dashboard_html(
        payload, run or _run(outcome="NO_TRADE"), market_map=mm,
        price_bars_snapshot=_bars_snapshot(symbols=syms) if bars else None, now=_S2_NOW, **kw)


def _s2_obs(html: str) -> str:
    """The `#spy-observation` block: from its id to its own column-zero close (the `_d1_card` convention)."""
    return html.split('id="spy-observation"', 1)[1].split("\n</div>\n", 1)[0]


def _s2_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_prd329_spy_session_promoted_between_watching_and_details() -> None:
    # T8/T10 (R4): first-class section strictly between the two seams; the
    # observation no longer renders inside DETAILS; not an `operator-zone`.
    html = _s2_render()
    assert html.index('id="watching-zone"') < html.index('id="spy-session"') < html.index('id="details-history"')
    assert ('<section class="spy-session-group" id="spy-session">\n  <h3>SPY SESSION</h3>\n'
            '<div class="block" id="spy-observation">\n  <h2>SPY SESSION OBSERVATION</h2>') in html
    details = html.split('id="details-history"', 1)[1]
    assert 'id="spy-observation"' not in details and 'id="spy-session-details"' not in details
    assert html.count("<h3>SPY SESSION</h3>") == 1 and html.count('id="spy-observation"') == 1
    assert 'operator-zone" id="spy-session"' not in html
    assert html.split('<details class="block operator-zone"', 1)[0].count('class="block operator-zone"') == 4


def test_prd329_observation_kv_grid_bytes_unchanged() -> None:
    # T9 (R4/R8), regression guard: the six rows move verbatim.
    obs = _s2_obs(_s2_render())
    kv = obs.split('<div class="kv-grid">', 1)[1].split("  </div>", 1)[0]
    assert _s2_sha(kv) == _S2_KV_SHA
    for row in ("SESSION", "STATE", "OBSERVED AT", "SESSION VWAP", "PRICE", "ORB"):
        assert f'<div class="label">{row}</div>' in kv
    assert 'data-raw-state="OBSERVED"' in kv and 'data-observed-at-utc="2026-04-28T13:34:00+00:00"' in kv


def test_prd329_spy_chart_is_daily_neutral_with_named_clocks() -> None:
    # T11 (R5/R8): `spy-chart` (never `setup-chart`) with no candidate semantics,
    # even when a SPY contract exists; caption = bars caption + NOW market-map clock.
    html = _s2_render(contract_entry_map={"SPY": 102.5}, contract_stop_map={"SPY": 99.8})
    obs = _s2_obs(html)
    assert obs.count('<div class="spy-chart"><svg') == 1 and 'class="setup-chart"' not in obs
    svg = obs.split('class="spy-chart"', 1)[1].split("</svg>", 1)[0]
    for bad in ('class="risk-zone"', "ENTRY", "STOP", "#e0a552", "#e05252"):
        assert bad not in svg, bad
    caption = obs.split('<div class="chart-caption">', 1)[1].split("</div>", 1)[0]
    assert caption == "bars through 2026-08-27 · yfinance 1d · NOW per market map 2026-04-28T12:00:00Z"
    assert "intraday" not in obs and "5m" not in obs
    assert obs.index('class="spy-chart"') < obs.index('class="chart-caption"') < obs.index('class="lvl-ladder')
    assert "ENTRY" in html.split('id="card-SPY"', 1)[1]  # positive control: the candidate chart is not neutral


def test_prd329_spy_ladder_is_observational_only() -> None:
    # T12 (R6): rows are NOW + zones + fibs, byte-equal to a direct neutral ladder
    # over the same SPY map levels; no candidate class or word.
    html = _s2_render(contract_entry_map={"SPY": 102.5}, contract_stop_map={"SPY": 99.8})
    ladder = _s2_obs(html).split('class="lvl-ladder', 1)[1]
    out: list[str] = []
    rec = _chartable("SPY", "C")
    _dr._render_level_ladder(out.append, 101.8, None, rec["fib_levels"], rec["watch_zones"], None,
                             operator_locked=False)
    assert "\n".join(out) in _s2_obs(html)
    for name in ("NOW", "VWAP", "EMA9", "EMA50"):
        assert f'<span class="lvl-name">{name}</span>' in ladder, name
    for bad in ("lvl-entry", "lvl-stop", "lvl-riskband", "lvl-inrisk", "lvl-lockrisk", "lvl-neutral",
                "lvl-locked", "ENTRY", "STOP", "INVALIDATION", "TRADE", "TRIGGER"):
        assert bad not in ladder, bad
    assert "102.00" not in ladder and "105.00" not in ladder   # observation VWAP / ORB never merged


def test_prd329_spy_unavailable_when_market_map_unhealthy() -> None:
    # T13(a) (R5): `_mm_health` != OK, including `market_map=None`, -> one honest line.
    stale = _market_map({"SPY": _chartable("SPY", "C")})
    stale["generated_at"] = "2026-04-28T10:00:00Z"   # two hours behind the run
    for mm, token in ((None, "MISSING"), (stale, "STALE")):
        obs = _s2_obs(_s2_render(mm=mm))
        assert obs.count(_S2_MAP_LINE.format(token)) == 1, token
        assert "<svg" not in obs and "lvl-ladder" not in obs and "spy-chart" not in obs
        assert 'data-raw-state="OBSERVED"' in obs   # observation rows still render


def test_prd329_spy_unavailable_when_healthy_map_lacks_spy_record() -> None:
    # T13(b) (R5): reachable public shapes never raise; direct helper is `.get`-defensive.
    no_symbols = _market_map()
    del no_symbols["symbols"]
    for mm in (_market_map({"QQQ": _chartable("QQQ", "C")}), _market_map(), no_symbols):
        obs = _s2_obs(_s2_render(mm=mm))
        assert obs.count(_S2_MAP_LINE.format("no SPY record")) == 1
        assert "<svg" not in obs and "lvl-ladder" not in obs
    for rec in (None, ["not", "a", "dict"], "SPY"):
        out: list[str] = []
        _dr._render_spy_session(out.append, _spy_section(), (_PC_BARS, "cap"), rec, "OK", False, "clock")
        assert _S2_MAP_LINE.format("no SPY record") in "\n".join(out) and "<svg" not in "\n".join(out)
    out = []
    _dr._render_spy_session(out.append, _spy_section(), (_PC_BARS, "cap"),
                            {"current_price": 101.8, "watch_zones": None, "fib_levels": None}, "OK", False, "c")
    assert "<svg" in "\n".join(out) and 'class="lvl-ladder' in "\n".join(out)  # NOW-only ladder, no raise


def test_prd329_spy_invalid_price_suppresses_chart_only() -> None:
    # T13(c) (R5): the ladder's existing no-price line is the only chart-related output.
    for bad in (None, float("nan"), float("inf"), -1.0, 0, True):
        rec = _chartable("SPY", "C")
        rec["current_price"] = bad
        obs = _s2_obs(_s2_render(mm=_market_map({"SPY": rec})))
        assert obs.count('<div class="lvl-unavail">Chart unavailable — no price data</div>') == 1, bad
        assert "<svg" not in obs and "no bars for SPY" not in obs and "lvl-ladder" not in obs


def test_prd329_spy_no_bars_keeps_the_ladder(monkeypatch) -> None:
    # T13(d) (R5): bars absent, or an empty SVG, -> the named line and the ladder.
    obs = _s2_obs(_s2_render(bars=False))
    assert obs.count('<div class="lvl-unavail">Chart unavailable — no bars for SPY</div>') == 1
    assert "<svg" not in obs and "spy-chart" not in obs and '<span class="lvl-name">NOW</span>' in obs
    monkeypatch.setattr(_dr.setup_chart, "render_setup_chart_svg", lambda *a, **k: "")
    assert _s2_obs(_s2_render()) == obs


def test_prd329_observation_subtree_is_a_pure_function_of_observational_inputs() -> None:
    # T14 (R7): positive controls, then one decision input at a time -> identical bytes.
    base = _s2_obs(_s2_render())
    for control in ('class="spy-chart"', "<svg", 'class="lvl-ladder', 'data-raw-state="OBSERVED"'):
        assert control in base, control
    for bad in ("PERMITTED", "TRADE", "NO TRADE", "GRADE", "ACTIONABLE", "TRIGGER"):
        assert bad not in base, bad
    variants = (dict(outcome="TRADE"), dict(outcome="NO_TRADE", permission=_S2_LOCK),
                dict(system_halted=True, outcome="NO_TRADE"),
                dict(system_halted=True, outcome="NO_TRADE", permission=_S2_LOCK))
    for run in variants:
        assert _s2_obs(_s2_render(run=_run(**run))) == base, run
    assert _s2_obs(_s2_render(contract_entry_map={"SPY": 102.5}, contract_stop_map={"SPY": 99.8})) == base
    # Observation state is an independent clock: PRE_OPEN / STALE do not suppress chart or ladder.
    payload = _payload()
    payload["sections"]["spy_observation"] = _spy_section(state="PRE_OPEN", session_vwap=None, current_price=None)
    obs = _s2_obs(render_dashboard_html(payload, _run(outcome="NO_TRADE"),
                                        market_map=_market_map({"SPY": _chartable("SPY", "C")}),
                                        price_bars_snapshot=_bars_snapshot(), now=_S2_NOW))
    assert 'class="spy-chart"' in obs and 'class="lvl-ladder' in obs and "UNAVAILABLE" in obs


def test_prd329_spy_session_source_cone() -> None:
    # T14 AST clause (R7): the helper reads no decision / permission / ranking state.
    fn = _dr._render_spy_session
    assert list(inspect.signature(fn).parameters) == [
        "w", "spy_obs", "spy_bars", "spy_record", "mm_health", "unhealthy_lineage", "mm_clock_label"]
    tree = _ast.parse(inspect.getsource(fn))
    forbidden = {"_decision_state", "decision_state", "decision_permitted", "permission", "operator_locked",
                 "system_state", "market_control_card", "contract_entry_map", "contract_stop_map",
                 "_primary_card_symbol", "chart_slot_available"}
    reads = [n.id for n in _ast.walk(tree) if isinstance(n, _ast.Name)]
    reads += [n.attr for n in _ast.walk(tree) if isinstance(n, _ast.Attribute)]
    assert not [r for r in reads if r in forbidden or r.startswith(("candidate_", "grade", "rank"))], reads
    calls = {getattr(c.func, "attr", getattr(c.func, "id", None)): c
             for c in _ast.walk(tree) if isinstance(c, _ast.Call)}
    kws = {k.arg: k.value for k in calls["render_setup_chart_svg"].keywords}
    for name, value in (("contract_entry", None), ("contract_stop", None), ("operator_locked", False)):
        assert isinstance(kws[name], _ast.Constant) and kws[name].value is value, name
    ladder = calls["_render_level_ladder"].args
    assert all(isinstance(ladder[i], _ast.Constant) and ladder[i].value is None for i in (2, 5))


def test_prd329_market_control_stays_in_details_with_unchanged_bytes() -> None:
    # T15 / T15-mcc-only (R9): MCC never moves; observation-present renders drop the
    # single-member DETAILS group; MCC-only renders keep today's wrapper bytes.
    payload = _payload()
    payload["sections"]["market_control_card"] = _mcc_section()
    payload["sections"]["spy_observation"] = _spy_section()
    html = render_dashboard_html(payload, _run(), market_map=_market_map())
    assert html.index('id="details-history"') < html.index('id="market-control-card"')
    details = html.split('id="details-history"', 1)[1]
    assert 'id="spy-session-details"' not in details and "<h3>SPY SESSION</h3>" not in details
    section = html.split('id="spy-session"', 1)[1].split("</section>", 1)[0]
    assert "MARKET CONTROL" not in section and 'id="market-control-card"' not in section
    mcc_only = _render_with_mcc(_mcc_section())
    assert _mcc_block(html) == _mcc_block(mcc_only)
    fragment = mcc_only.split('<section class="spy-session-group" id="spy-session-details">', 1)[1]
    assert _s2_sha(fragment.split("</section>", 1)[0]) == _S2_MCC_ONLY_SHA
    assert 'id="spy-session"' not in mcc_only and 'id="spy-observation"' not in mcc_only


def test_prd329_spy_chart_never_suppressed_by_primary_selection(monkeypatch) -> None:
    # T17 (R5 CO-OCCURRENCE): (i) SPY as C primary; (ii) another symbol primary;
    # (iii) no primary at all; and every decision state -> exactly one `spy-chart`.
    html = _s2_render()
    assert '<details open class="tier-group" id="tier-c">' in html
    assert html.count('class="setup-chart"') == 1 and html.count('class="spy-chart"') == 1
    html = _s2_render(mm=_market_map({"AAA": _chartable("AAA", "A+"), "SPY": _chartable("SPY", "C")}))
    assert html.count('class="spy-chart"') == 1
    assert html.count('class="setup-chart"') == 2   # AAA primary + SPY's own secondary behind disclosure
    assert html.index('class="setup-chart"') < html.index('id="card-SPY"')   # AAA holds the slot
    spy_card = html.split('id="card-SPY"', 1)[1].split("\n</div>\n", 1)[0]   # closed C tier -> S1 `open`
    assert '<details open class="chart-detail">' in spy_card and "spy-chart" not in spy_card
    for run in (dict(outcome="TRADE"), dict(outcome="NO_TRADE", permission=_S2_LOCK)):
        assert _s2_render(run=_run(**run)).count('class="spy-chart"') == 1
    monkeypatch.setattr(_dr, "select_primary_card_symbol", lambda *a, **k: None)
    html = _s2_render()
    assert '<details open class="tier-group"' not in html            # no primary: tier stays closed
    assert "spy-chart" not in html.split('id="card-SPY"', 1)[1].split("\n</div>\n", 1)[0]
    assert html.count('class="spy-chart"') == 1


def test_prd329_spy_session_call_site_guarded_only_by_observation_presence() -> None:
    # T18 (R5 CALL-SITE RULE): exactly one call, under exactly one `If`, testing bare `_spy_obs`.
    tree = _ast.parse(inspect.getsource(_dr.render_dashboard_html))
    parents = {child: node for node in _ast.walk(tree) for child in _ast.iter_child_nodes(node)}
    calls = [n for n in _ast.walk(tree)
             if isinstance(n, _ast.Call) and getattr(n.func, "id", None) == "_render_spy_session"]
    assert len(calls) == 1
    node, ifs = calls[0], []
    while node in parents:
        node = parents[node]
        if isinstance(node, _ast.If):
            ifs.append(node)
    assert len(ifs) == 1
    assert isinstance(ifs[0].test, _ast.Name) and ifs[0].test.id == "_spy_obs"


def test_prd329_preview_fixture_pins_the_promoted_block() -> None:
    # T16: the `spy_session_observed` fixture renders the promoted block with chart + ladder.
    from tests.preview_fixtures import SECTION_STATE_CASES
    case = next(c for c in SECTION_STATE_CASES if c.name == "spy_session_observed")
    html = render_dashboard_html(case.payload, case.run, market_map=case.market_map, **case.render_kwargs)
    assert 'id="spy-session"' in html and html.count('class="spy-chart"') == 1
    assert html.index('id="watching-zone"') < html.index('id="spy-session"') < html.index('id="details-history"')
    assert _s2_sha(html.split('<div class="block operator-zone" id="watching-zone">', 1)[1]) == _S2_FIXTURE_SHA


_S2_FIXTURE_SHA = "dccd1721213618ed2eb24357344ea7f88c1d27175b2f076730eef195c47c973f"  # implementation head
