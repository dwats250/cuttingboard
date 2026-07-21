"""PRD-083: focused tests for dashboard data freshness and source visibility."""
from __future__ import annotations

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
from tests.dash_helpers import (
    _macro_drivers,
    _macro_tape_block,
    _market_map,
    _mm_symbol,
    _payload,
    _run,
)

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
    return html.split('id="candidate-board"', 1)[1].split('</div>\n\n', 1)[0]


def _candidate_card(html: str, symbol: str = "SPY") -> str:
    return html.split(f'id="card-{symbol}"', 1)[1].split('</div>\n</div>', 1)[0]


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
    board = html.split('id="candidate-board"', 1)[1]
    assert "MARKET MAP UNAVAILABLE" not in board
    assert "SOURCE_MISSING" in board or "N/A" in board


# T2 — stale market_map file renders STALE in candidate board
def test_stale_market_map_renders_stale(tmp_path: pytest.TempPathFactory) -> None:
    mm_file = tmp_path / "market_map.json"
    mm_file.write_text(json.dumps(_market_map()), encoding="utf-8")
    stale_mtime = time.time() - DASHBOARD_STALE_AFTER_SECONDS - 60
    os.utime(mm_file, (stale_mtime, stale_mtime))
    html = render_dashboard_html(_payload(), _run(), market_map_path=mm_file)
    board = html.split('id="candidate-board"', 1)[1]
    assert "STALE" in board


# T3 — parse-error market_map renders PARSE_ERROR and does not crash
def test_parse_error_market_map_renders_parse_error(tmp_path: pytest.TempPathFactory) -> None:
    mm_file = tmp_path / "market_map.json"
    mm_file.write_text("{not valid json", encoding="utf-8")
    html = render_dashboard_html(_payload(), _run(), market_map_path=mm_file)
    board = html.split('id="candidate-board"', 1)[1]
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

    tape_pos = html.index('id="macro-tape"')
    line_pos = html.index('class="macro-pressure-line')
    board_pos = html.index('id="candidate-board"')
    assert tape_pos < line_pos < board_pos

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
    assert ">UPDATED</div>" in html


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
    board = html.split('id="candidate-board"', 1)[1]

    assert "STALE MARKET MAP" in board
    assert "Market Map / Developing Setups paused" in board
    assert 'id="card-SPY"' not in board


def test_market_map_without_generated_at_does_not_trigger_stale() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z")
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})
    mm.pop("generated_at", None)

    html = render_dashboard_html(payload, run, market_map=mm)
    board = html.split('id="candidate-board"', 1)[1]

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
    assert 'class="lvl-diagram"' in card


def test_candidate_level_diagram_hidden_when_no_level_context() -> None:
    # PRD-158 § 4.2 translation 12: anchor without fib_levels/watch_zones
    # hides the diagram entirely — no placeholder.
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})

    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    card = _candidate_card(html)

    assert "Level context unavailable" not in card
    assert "Chart unavailable" not in card
    assert 'class="lvl-diagram"' not in card


def test_candidate_level_diagram_hidden_when_anchor_invalid() -> None:
    # PRD-158 § 4.2 translation 12: invalid anchor (zero/negative) hides the
    # diagram entirely — no placeholder.
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 0}})

    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    card = _candidate_card(html)

    assert "Chart unavailable" not in card
    assert "Level context unavailable" not in card
    assert 'class="lvl-diagram"' not in card


def test_candidate_level_diagram_now_anchor_is_current_price_entry_marked_separately() -> None:
    # PRD-226: the yellow NOW line is the current price (120), NOT the contract
    # entry (110). The entry gets its own amber ENTRY line. Pre-PRD-226 the
    # yellow anchor sat on the contract entry (y=70); now it sits on current
    # price (y=40) and the amber ENTRY line sits on the entry (y=70).
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
    now_line = re.search(r'<line x1="0" y1="(?P<y>\d+)" x2="160" y2="\d+" stroke="#f5c518"', card)
    entry_line = re.search(r'<line x1="0" y1="(?P<y>\d+)" x2="160" y2="\d+" stroke="#e0a552"', card)

    assert now_line is not None and now_line.group("y") == "40"    # NOW = current price
    assert entry_line is not None and entry_line.group("y") == "70"  # ENTRY = contract entry
    assert ">NOW 120.00</text>" in card
    assert ">ENTRY 110.00 -8.3%</text>" in card


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
    entry_line = re.search(r'<line x1="0" y1="(?P<y>\d+)" x2="160" y2="\d+" stroke="#f5c518"', card)

    assert entry_line is not None
    assert entry_line.group("y") == "40"


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

    # PRD-158 translation 12: no diagram and no placeholder when level
    # context is absent.
    assert "Level context unavailable" not in card
    assert 'class="lvl-diagram"' not in card
    assert ">ENTRY</text>" not in card


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
    after = state.split(">UPDATED</div>", 1)[1]
    after_value = after.split('class="value"', 1)[1]
    return after_value.split(">", 1)[1].split("</div>", 1)[0]


def test_no_separate_dashboard_header_block() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'id="dashboard-header"' not in html


def test_system_state_contains_updated_timestamp() -> None:
    # PRD-219: one absolute UPDATED line replaces RUN SNAPSHOT/LIVE STATE/SCOREBOARD.
    html = render_dashboard_html(_payload(), _run())
    state = _system_state_block(html)
    assert ">UPDATED</div>" in state


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
    assert "2026-05-14" in updated
    assert "2026-06-16" not in updated


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
    assert "2026-05-14" in updated and "2026-06-16" not in updated


def test_prd219_updated_falls_back_to_run_when_no_pipeline_run() -> None:
    # When pipeline_run is absent, UPDATED falls back to `run`.
    html = render_dashboard_html(
        _payload(timestamp="2026-06-16T12:00:00Z"),
        _run_with_timestamp("2026-06-16T12:00:00Z"),
    )
    updated = _updated_value(_system_state_block(html))
    assert "2026-06-16" in updated


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


def test_halted_state_reason_in_context_line() -> None:
    # PRD-219: the halt reason folds into the context line under the verdict.
    payload = _payload(validation_halt_detail={"reason": "STAY_FLAT regime"})
    run = _run(system_halted=True)
    html = render_dashboard_html(payload, run)
    state = _system_state_block(html)
    assert "SYSTEM HALT" in state
    context = state.split('class="sys-context', 1)[1].split("</div>", 1)[0]
    assert "STAY_FLAT regime" in context


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
# PRD-090: Candidate Board Display Tiers
# ---------------------------------------------------------------------------

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
    board = html.split('id="candidate-board"', 1)[1].split('id="run-delta"', 1)[0]
    assert '<details' not in board, "A-grade card is incorrectly wrapped in <details>"


def test_aplus_grade_not_inside_details_block() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A+")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    board = html.split('id="candidate-board"', 1)[1].split('id="run-delta"', 1)[0]
    assert '<details' not in board, "A+ grade card is incorrectly wrapped in <details>"


def test_b_grade_not_inside_details_block() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="B")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    board = html.split('id="candidate-board"', 1)[1].split('id="run-delta"', 1)[0]
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
    board = html.split('id="candidate-board"', 1)[1].split('id="run-delta"', 1)[0]
    assert '<div class="tier-header">' in board


# PRD-093-PATCH tests

def test_system_state_heading_is_system_state() -> None:
    # PRD-219: the decision title moved into the verdict; the h2 is just the label.
    html = render_dashboard_html(_payload(), _run())
    state = _system_state_block(html)
    assert "<h2>SYSTEM STATE</h2>" in state


def test_stale_market_map_shows_updated_wording() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z")
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})
    mm["generated_at"] = "2026-04-28T12:00:00Z"

    html = render_dashboard_html(payload, run, market_map=mm)
    board = html.split('id="candidate-board"', 1)[1]

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
    board = html.split('id="candidate-board"', 1)[1]
    assert "STALE MARKET MAP" in board
    assert "Run:" in board
    assert "2026-04-28T12:10:01" in board


def test_stale_market_map_includes_market_map_timestamp() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z")
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})
    mm["generated_at"] = "2026-04-28T12:00:00Z"
    html = render_dashboard_html(payload, run, market_map=mm)
    board = html.split('id="candidate-board"', 1)[1]
    assert "Market map:" in board
    assert "2026-04-28T12:00:00Z" in board


def test_stale_market_map_missing_run_timestamp_shows_unavailable() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run()
    del run["timestamp"]
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})
    mm["generated_at"] = "2026-04-28T12:00:00Z"
    html = render_dashboard_html(payload, run, market_map=mm)
    board = html.split('id="candidate-board"', 1)[1]
    assert "STALE MARKET MAP" in board
    assert "Run: unavailable" in board


def test_permission_none_does_not_mutate_run_dict() -> None:
    run = _run(permission=None)
    render_dashboard_html(_payload(), run)
    assert run["permission"] is None


def test_permission_none_reason_in_context_line() -> None:
    # PRD-219: the reason folds into the context line (no separate Reason field).
    run = _run(permission=None)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    context = state.split('class="sys-context', 1)[1].split("</div>", 1)[0]
    assert "no qualified setups" in context


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
    board = html.split('id="candidate-board"', 1)[1].split('id="run-delta"', 1)[0]
    assert 'id="card-SPY"' in board


def test_b_candidate_not_in_details_when_permission_none() -> None:
    """R3: B candidate renders in normal board flow (not in details) when permission is None."""
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="B")})
    html = render_dashboard_html(_payload(), _run(permission=None), market_map=mm)
    board = html.split('id="candidate-board"', 1)[1].split('id="run-delta"', 1)[0]
    assert '<details' not in board
    assert 'id="card-SPY"' in board


def test_b_candidate_renders_when_permission_false() -> None:
    """R3: B candidates render from fresh market_map when permission is False (blocked)."""
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="B")})
    html = render_dashboard_html(_payload(), _run(permission=False), market_map=mm)
    board = html.split('id="candidate-board"', 1)[1].split('id="run-delta"', 1)[0]
    assert 'id="card-SPY"' in board


def test_a_candidate_renders_when_permission_none() -> None:
    """R2: A candidates render from fresh market_map even when permission is None."""
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    html = render_dashboard_html(_payload(), _run(permission=None), market_map=mm)
    board = html.split('id="candidate-board"', 1)[1].split('id="run-delta"', 1)[0]
    assert 'id="card-SPY"' in board


def test_lower_grade_failure_reason_from_reason_for_grade() -> None:
    """R5: Failure reason uses reason_for_grade when no explicit failure field."""
    entry = {**_mm_symbol("SPY", grade="C"), "reason_for_grade": "momentum fading"}
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "FAILURE REASON" in card
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
    assert "FAILURE REASON" in card
    assert "structure broken" in card


def test_stale_market_map_suppresses_candidates_regardless_of_permission() -> None:
    """R7: Stale market_map suppresses candidates even when permission is True."""
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z", permission=True)
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    mm["generated_at"] = "2026-04-28T12:00:00Z"
    html = render_dashboard_html(payload, run, market_map=mm)
    board = html.split('id="candidate-board"', 1)[1]
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
    start = html.find('id="trend-structure"')
    assert start >= 0, "trend-structure section not rendered"
    end = html.find('id="candidate-board"', start)
    return html[start:end if end >= 0 else len(html)]


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
    return html.split('id="candidate-board"', 1)[1].split("</div>\n\n", 1)[0]


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
    assert coh < ss
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
    # PRD-120: trend-structure block now contains multiple inner <div>s;
    # extract by next-section sentinel rather than first </div>.
    start = html.index('id="trend-structure"')
    end = html.find('id="candidate-board"', start)
    return html[start:end] if end >= 0 else html[start:]


def _candidate_board_only(html: str) -> str:
    # PRD-120: candidate-board contains multiple inner <div>s after the
    # MARKET MAP SOURCE line; extract by next-section sentinel.
    start = html.index('id="candidate-board"')
    end = html.find('id="run-delta"', start)
    return html[start:end] if end >= 0 else html[start:]


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


def test_prd177_r5_red_folder_empty_state() -> None:
    rf = {"ok": True, "error": None, "expiring": False, "events": []}
    html = render_dashboard_html(_payload(), _run(), red_folder=rf)
    block = html.split('id="red-folder"', 1)[1].split('id="trend-structure"', 1)[0]
    assert "No red-folder events in the next 48 hours." in block


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


def test_prd199_r2_tradable_arrow_follows_pct_not_direction(monkeypatch) -> None:
    # Red test: SPY trade_framing.direction = LONG (high-grade BULL) but
    # daily_change_pct < 0 -> arrow must be DOWN (driven by %-change sign, not direction).
    html = _render_tradables(
        monkeypatch, {"SPY": -0.42}, generated_at=_fresh_ts_iso(),
        mm_symbols={"SPY": _mm_symbol("SPY", grade="A", bias="BULL")},
    )
    cell = _tradable_cell(html, "SPY")
    assert '<span class="tradable-arrow">↓</span>' in cell
    assert '<span class="tradable-arrow">↑</span>' not in cell


def test_prd199_r3_tradable_arrow_renders_for_nonzero_change(monkeypatch) -> None:
    html = _render_tradables(
        monkeypatch, {"QQQ": 0.85}, generated_at=_fresh_ts_iso(),
        mm_symbols={"QQQ": _mm_symbol("QQQ", grade="A", bias="BULL")},
    )
    assert '<span class="tradable-arrow">↑</span>' in _tradable_cell(html, "QQQ")


def test_prd199_r3_tradable_arrow_dash_when_change_missing(monkeypatch) -> None:
    # Fresh+healthy snapshot but daily_change_pct absent -> dash sentinel (missing-field path).
    html = _render_tradables(
        monkeypatch, {}, generated_at=_fresh_ts_iso(),
        mm_symbols={"SPY": _mm_symbol("SPY", grade="A")},
    )
    assert '<span class="tradable-arrow">—</span>' in _tradable_cell(html, "SPY")


def test_prd199_arrow_is_monochrome_no_color_class(monkeypatch) -> None:
    # Approval edit: the tradable arrow carries no _ARROW_CSS color class; color
    # stays reserved for the macro-driver rows (tape-slot up/down).
    html = _render_tradables(
        monkeypatch, {"SPY": -0.42, "QQQ": 0.85}, generated_at=_fresh_ts_iso(),
        mm_symbols={"SPY": _mm_symbol("SPY", grade="A")},
    )
    grid = html.split('class="macro-tradables-grid"', 1)[1].split("</div>", 1)[0]
    assert "tradable-arrow" in grid
    assert "tape-slot up" not in grid
    assert "tape-slot down" not in grid


def test_prd199_r4_tradable_price_unchanged_with_arrow(monkeypatch) -> None:
    from tests.dash_helpers import _macro_tape_value_slots
    html = _render_tradables(
        monkeypatch, {"SPY": 0.5}, generated_at=_fresh_ts_iso(),
        mm_symbols={"SPY": {**_mm_symbol("SPY", grade="A"), "current_price": 512.345}},
    )
    assert dict(_macro_tape_value_slots(html))["SPY"] == "512.35"


def test_prd199_r5_tradable_arrow_dashes_when_trend_snapshot_stale(monkeypatch) -> None:
    # PRD-199 R5 (freshness gate): lineage fresh+coherent but the trend snapshot is
    # wall-clock STALE -> _ts_health == STALE -> the tradables ARROW degrades to the dash
    # sentinel, while the price (independently fresh from market_map) is retained.
    html = _render_tradables(
        monkeypatch, {"SPY": -0.42}, generated_at="2020-01-01T00:00:00+00:00",
        mm_symbols={"SPY": _mm_symbol("SPY", grade="A")},
    )
    cell = _tradable_cell(html, "SPY")
    assert '<span class="tradable-arrow">—</span>' in cell       # arrow degraded to dash
    assert '<span class="tradable-arrow">↓</span>' not in cell    # not the stale directional arrow
    assert 'data-symbol="SPY">100.00</span>' in cell             # price retained (market_map fresh)


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
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "no qualified setups" in state


def test_prd220_macro_pressure_one_bullet_per_line() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    line = html.split('class="macro-pressure-line', 1)[1].split("</div>", 1)[0]
    assert "• " in line
    assert "<br>" in line  # phrases on separate lines


def test_prd220_tradables_arrow_before_price() -> None:
    import re as _r220
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=_market_map())
    # arrow span precedes the value span within a tradable cell
    assert _r220.search(
        r'class="tradable-arrow">[^<]*</span>&nbsp;<span class="macro-tape-value"', html
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
