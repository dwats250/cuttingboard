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
    INACTIVE_SESSION_TYPES,
    _UNAVAILABLE_WATCH,
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
    tape_block = tape[1].split('id="macro-pressure"', 1)[0]
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
    tape_block = tape[1].split('id="macro-pressure"', 1)[0]
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


def _artifact_diagnostics(html: str) -> str:
    return html.split('id="artifact-diagnostics"', 1)[1].split("</details>", 1)[0]


def _assert_lineage_state(html: str, state: str) -> None:
    diagnostics = _artifact_diagnostics(html)
    assert f"artifact_lineage_state={state}" in diagnostics
    assert len(re.findall(r"artifact_lineage_state=(COHERENT|MIXED|STALE|MISSING)", diagnostics)) == 1


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
    mm = _market_map({"SPY": _mm_symbol("SPY")})  # no current_price
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


def test_macro_pressure_collapsed_inside_macro_tape() -> None:
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()),
        _run(),
        market_map=_market_map({"SPY": _mm_symbol("SPY")}),
    )

    assert '<div class="block" id="macro-pressure">' not in html
    assert '<details id="macro-pressure">' in html
    assert "MACRO PRESSURE" in html

    tape_pos = html.index('id="macro-tape"')
    pressure_pos = html.index('id="macro-pressure"')
    board_pos = html.index('id="candidate-board"')
    assert tape_pos < pressure_pos < board_pos

    for label in ("Volatility", "Dollar", "Rates", "Bitcoin", "Overall"):
        assert label in html


def test_macro_pressure_no_data_guard_stays_inside_details(tmp_path: Path) -> None:
    html = render_dashboard_html(
        _payload(macro_drivers={}),
        _run(),
        market_map=_market_map(),
        macro_snapshot_path=tmp_path / "missing_macro_snapshot.json",
    )

    pressure = html.split('<details id="macro-pressure">', 1)[1].split("</details>", 1)[0]
    assert "MACRO PRESSURE UNAVAILABLE" in pressure
    assert "NO PRESSURE DATA" not in pressure


def test_macro_pressure_field_missing_guard_stays_inside_details(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cuttingboard.delivery.dashboard_renderer._build_pressure_snapshot",
        lambda _macro_drivers, _market_map: "FIELD_MISSING",
    )

    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()),
        _run(),
        market_map=_market_map(),
    )

    pressure = html.split('<details id="macro-pressure">', 1)[1].split("</details>", 1)[0]
    assert "MACRO PRESSURE UNAVAILABLE" in pressure
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
    assert "ACTION: ACTIVE" not in html


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
    assert "RUN SNAPSHOT" in html
    assert "ACTION: ACTIVE" in html


def test_artifact_diagnostics_show_sources_and_timestamps() -> None:
    html = render_dashboard_html(
        _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers()),
        _run_with_timestamp("2026-04-28T12:00:00Z"),
        market_map=_market_map(),
        contract_generated_at="2026-04-28T12:00:00Z",
        payload_source="logs/latest_hourly_payload.json",
        run_source="logs/latest_hourly_run.json",
        market_map_source="logs/market_map.json",
        contract_source="logs/latest_hourly_contract.json",
    )

    assert 'id="artifact-diagnostics"' in html
    assert "payload=logs/latest_hourly_payload.json @ 2026-04-28T12:00:00Z" in html
    assert "run=logs/latest_hourly_run.json @ 2026-04-28T12:00:00Z" in html
    assert "market_map=logs/market_map.json @" in html
    assert "contract=logs/latest_hourly_contract.json @ 2026-04-28T12:00:00Z" in html
    assert "payload_generation_id=test-gen-001" in html
    assert "run_generation_id=test-gen-001" in html
    assert "market_map_generation_id=test-gen-001" in html


def test_artifact_diagnostics_show_generation_ids_deterministically() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map()
    _set_generation_ids(payload, run, mm, "live-20260428T120000Z")

    html1 = render_dashboard_html(payload, run, market_map=mm)
    html2 = render_dashboard_html(payload, run, market_map=mm)

    assert html1 == html2
    assert "payload_generation_id=live-20260428T120000Z" in html1
    assert "run_generation_id=live-20260428T120000Z" in html1
    assert "market_map_generation_id=live-20260428T120000Z" in html1


def test_artifact_lineage_state_coherent() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map()
    _set_generation_ids(payload, run, mm, "live-20260428T120000Z")

    html = render_dashboard_html(payload, run, market_map=mm)

    _assert_lineage_state(html, "COHERENT")


def test_artifact_lineage_state_mixed() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map()
    payload["meta"]["generation_id"] = "gen-a"
    run["generation_id"] = "gen-b"
    mm["generation_id"] = "gen-a"

    html = render_dashboard_html(payload, run, market_map=mm)

    _assert_lineage_state(html, "MIXED")


def test_artifact_lineage_state_stale() -> None:
    payload = _payload(timestamp="2026-04-28T12:10:01Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:10:01Z")
    mm = _market_map()
    _set_generation_ids(payload, run, mm, "live-20260428T120000Z")
    mm["generated_at"] = "2026-04-28T12:00:00Z"

    html = render_dashboard_html(payload, run, market_map=mm)

    _assert_lineage_state(html, "STALE")


def test_artifact_lineage_state_missing_and_unavailable_generation_ids() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    # Strip helper-default generation_ids to exercise the "unavailable" path.
    payload["meta"].pop("generation_id", None)
    run.pop("generation_id", None)
    html = render_dashboard_html(payload, run, market_map=None)
    diagnostics = _artifact_diagnostics(html)

    _assert_lineage_state(html, "MISSING")
    assert "payload_generation_id=unavailable" in diagnostics
    assert "run_generation_id=unavailable" in diagnostics
    assert "market_map_generation_id=unavailable" in diagnostics


def test_artifact_lineage_state_uses_only_approved_classifications() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map()
    _set_generation_ids(payload, run, mm, "live-20260428T120000Z")

    diagnostics = _artifact_diagnostics(render_dashboard_html(payload, run, market_map=mm))

    states = re.findall(r"artifact_lineage_state=([A-Z_]+)", diagnostics)
    assert states == ["COHERENT"]
    assert set(states) <= {"COHERENT", "MIXED", "STALE", "MISSING"}


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


def test_candidate_level_diagram_suppresses_current_price_without_level_context() -> None:
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.34}})

    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    card = _candidate_card(html)

    assert "Level context unavailable" in card
    assert "Chart unavailable" not in card
    assert 'class="lvl-diagram"' not in card


def test_candidate_level_diagram_preserves_unavailable_without_valid_anchor() -> None:
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 0}})

    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    card = _candidate_card(html)

    assert "Chart unavailable" in card
    assert 'class="lvl-diagram"' not in card


def test_candidate_level_diagram_prefers_contract_entry_over_current_price() -> None:
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
    entry_line = re.search(r'<line x1="0" y1="(?P<y>\d+)" x2="160" y2="\d+" stroke="#f5c518"', card)

    assert entry_line is not None
    assert entry_line.group("y") == "70"


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


def test_failed_candidate_with_only_current_price_does_not_render_entry_only_diagram() -> None:
    mm = _market_map({"SPY": {**_mm_symbol("SPY", grade="D"), "current_price": 512.34}})

    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    card = _candidate_card(html)

    assert "Level context unavailable" in card
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
    history_block = html.split('id="run-history"', 1)[1]
    assert "NO_PREVIOUS_RUN" in delta_block
    assert "NO_HISTORY" in history_block
    # No crash — rendering completed; pressure block present
    assert 'id="macro-pressure"' in html


# PRD-089-PATCH tests

def _system_state_block(html: str) -> str:
    """Extract content of id="system-state" block."""
    return html.split('id="system-state"', 1)[1].split('<div class="block"', 1)[0]


def test_no_separate_dashboard_header_block() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'id="dashboard-header"' not in html


def test_system_state_contains_run_snapshot() -> None:
    html = render_dashboard_html(_payload(), _run())
    state = _system_state_block(html)
    assert "RUN SNAPSHOT" in state


def test_run_snapshot_stale_when_stale() -> None:
    old_ts = "2020-01-01T00:00:00Z"
    payload = _payload(timestamp=old_ts)
    run = _run_with_timestamp(old_ts)
    html = render_dashboard_html(payload, run)
    state = _system_state_block(html)
    assert "RUN SNAPSHOT - STALE" in state


def test_run_snapshot_current_when_fresh() -> None:
    from datetime import datetime, timezone
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = _payload(timestamp=now)
    run = _run_with_timestamp(now)
    html = render_dashboard_html(payload, run)
    state = _system_state_block(html)
    assert "RUN SNAPSHOT - CURRENT" in state


def test_run_snapshot_shows_pacific_timestamp() -> None:
    html = render_dashboard_html(
        _payload(timestamp="2026-05-05T20:29:00Z"),
        _run_with_timestamp("2026-05-05T20:29:00Z"),
    )
    state = _system_state_block(html)
    assert "PT" in state


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


def test_halted_state_permission_shows_halted() -> None:
    run = _run(system_halted=True)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "Permission" in state
    assert "HALTED" in state


def test_halted_state_raw_reason_shown_as_reason_not_permission() -> None:
    payload = _payload(validation_halt_detail={"reason": "STAY_FLAT regime"})
    run = _run(system_halted=True)
    html = render_dashboard_html(payload, run)
    state = _system_state_block(html)
    assert "Reason" in state
    assert "STAY_FLAT regime" in state
    perm_section = state.split("Permission", 1)[1].split("Halted", 1)[0]
    assert "STAY_FLAT regime" not in perm_section
    assert "HALTED" in perm_section


def test_non_halted_permission_preserved() -> None:
    run = _run(system_halted=False, permission=True)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "Permission" in state
    assert "True" in state


def test_normal_run_no_halted_or_kill_switch_in_system_state() -> None:
    run = _run(system_halted=False, kill_switch=False)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "Halted" not in state
    assert "Kill Switch" not in state


def test_halted_run_shows_halted_not_kill_switch() -> None:
    run = _run(system_halted=True, kill_switch=False)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "Halted" in state
    assert "Kill Switch" not in state


def test_kill_switch_run_shows_kill_switch() -> None:
    run = _run(system_halted=False, kill_switch=True)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "Kill Switch" in state


def test_regime_confidence_outcome_before_permission_in_system_state() -> None:
    html = render_dashboard_html(_payload(), _run())
    state = _system_state_block(html)
    regime_pos = state.find("Regime")
    outcome_pos = state.find("Outcome")
    permission_pos = state.find("Permission")
    assert regime_pos < permission_pos, "Regime must appear before Permission"
    assert outcome_pos < permission_pos, "Outcome must appear before Permission"


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


def test_d_grade_renders_inside_details_block() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="D")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    import re
    details = re.search(r'<details[^>]*id="tier-df"[^>]*>(.*?)</details>', html, re.DOTALL)
    assert details is not None, "tier-df <details> block not found"
    assert 'id="card-SPY"' in details.group(1), "D-grade card not inside tier-df <details>"


def test_f_grade_renders_inside_details_block() -> None:
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="F")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    import re
    details = re.search(r'<details[^>]*id="tier-df"[^>]*>(.*?)</details>', html, re.DOTALL)
    assert details is not None, "tier-df <details> block not found for F-grade"
    assert 'id="card-SPY"' in details.group(1), "F-grade card not inside tier-df <details>"


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
    assert card.count("WATCH") == 2
    assert "watch hold above support" in card
    assert "look for higher low" in card


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

def test_system_state_heading_prefixed_with_system_state() -> None:
    html = render_dashboard_html(_payload(), _run())
    state = _system_state_block(html)
    assert "SYSTEM STATE -" in state


def test_permission_none_shows_em_dash_not_no_qualified_setup() -> None:
    # PRD-120: Permission no longer renders as `&#8212;`; under default
    # _payload/_run (no market_map -> lineage MISSING) it renders UNKNOWN.
    run = _run(permission=None)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    perm_section = state.split("Permission", 1)[1].split("Reason", 1)[0]
    assert ">&#8212;<" not in perm_section
    assert "UNKNOWN" in perm_section
    assert "NO QUALIFIED SETUP" not in state


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


def test_permission_none_renders_em_dash() -> None:
    # PRD-120: replaces former `&#8212;` Permission fallback with a
    # deterministic UNKNOWN label under unhealthy lineage (default render
    # has no market_map -> lineage MISSING).
    run = _run(permission=None)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    perm_section = state.split("Permission", 1)[1].split("Reason", 1)[0]
    assert ">&#8212;<" not in perm_section
    assert "UNKNOWN" in perm_section
    assert "NONE" not in perm_section


def test_permission_none_does_not_mutate_run_dict() -> None:
    run = _run(permission=None)
    render_dashboard_html(_payload(), run)
    assert run["permission"] is None


def test_permission_none_shows_reason_line() -> None:
    run = _run(permission=None)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "Reason" in state
    assert "no qualified candidates" in state


def test_macro_pressure_missing_shows_unavailable() -> None:
    html = render_dashboard_html(
        _payload(macro_drivers={}),
        _run(),
        market_map=_market_map(),
        macro_snapshot_path=Path("/nonexistent/macro_snapshot.json"),
    )
    pressure = html.split('<details id="macro-pressure">', 1)[1].split("</details>", 1)[0]
    assert "MACRO PRESSURE UNAVAILABLE" in pressure
    assert "NO PRESSURE DATA" not in pressure


def test_macro_pressure_with_data_shows_affordance() -> None:
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()),
        _run(),
        market_map=_market_map({"SPY": _mm_symbol("SPY")}),
    )
    pressure = html.split('<details id="macro-pressure">', 1)[1].split("</details>", 1)[0]
    assert "▶" in pressure


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
        **_mm_symbol("SPY", grade="D"),
        "failure_reason": "structure broken",
        "reason_for_grade": "chop",
    }
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "FAILURE REASON" in card
    assert "structure broken" in card


def test_validation_requirements_from_explicit_field() -> None:
    """R6: validation_requirements field is rendered as VALIDATION rows."""
    entry = {
        **_mm_symbol("SPY", grade="C"),
        "validation_requirements": ["RR above minimum", "stop defined"],
    }
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "VALIDATION" in card
    assert "RR above minimum" in card
    assert "stop defined" in card


def test_validation_acceptance_used_when_no_validation_requirements() -> None:
    """R6: validation_acceptance used when validation_requirements is absent."""
    entry = {
        **_mm_symbol("SPY", grade="C"),
        "validation_acceptance": "needs consolidation",
    }
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "VALIDATION" in card
    assert "needs consolidation" in card


def test_validation_renderer_derived_from_reason_for_grade() -> None:
    """R6: Renderer derives VALIDATION from reason_for_grade when no explicit fields."""
    entry = {
        **_mm_symbol("SPY", grade="C"),
        "reason_for_grade": "too early in development",
    }
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "VALIDATION" in card
    assert "too early in development" in card


def test_validation_requirements_source_precedence() -> None:
    """R6: validation_requirements beats validation_acceptance when both present."""
    entry = {
        **_mm_symbol("SPY", grade="D"),
        "validation_requirements": "use validation_requirements",
        "validation_acceptance": "use validation_acceptance",
    }
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "use validation_requirements" in card
    assert "use validation_acceptance" not in card


def test_validation_acceptance_beats_renderer_derived() -> None:
    """R6: validation_acceptance beats renderer-derived (reason_for_grade) when present."""
    entry = {
        **_mm_symbol("SPY", grade="C"),
        "failure_reason": "explicit fail",
        "reason_for_grade": "renderer derived text",
        "validation_acceptance": "acceptance text",
    }
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "acceptance text" in card
    assert "renderer derived text" not in card


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
    entry = {**_mm_symbol("SPY", grade="F"), "reason_for_grade": None}
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    fallback = "No failure reason provided"
    assert fallback in card
    assert all(ord(c) < 128 for c in fallback)


def test_a_candidate_with_validation_requirements_renders_validation() -> None:
    """R6: A candidate with validation_requirements renders VALIDATION rows."""
    entry = {
        **_mm_symbol("SPY", grade="A"),
        "validation_requirements": ["hold above 510", "volume confirm"],
    }
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "VALIDATION" in card
    assert "hold above 510" in card
    assert "volume confirm" in card


def test_aplus_candidate_with_validation_acceptance_renders_validation() -> None:
    """R6: A+ candidate uses validation_acceptance when validation_requirements absent."""
    entry = {
        **_mm_symbol("SPY", grade="A+"),
        "validation_acceptance": "needs clean break above resistance",
    }
    mm = _market_map({"SPY": entry})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = _candidate_card(html)
    assert "VALIDATION" in card
    assert "needs clean break above resistance" in card


# ============================================================================
# PRD-112 — Trend Structure Dashboard Panel (R10 tests a-h)
# ============================================================================

from datetime import datetime as _dt112, timezone as _tz112
from cuttingboard.delivery import dashboard_renderer as _dr112

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
    assert "BULLISH" in section
    assert "SUPPORTIVE" in section


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
    assert section.count("MISSING") >= 6  # 6 placeholder Status cells
    assert "MISSING" in section.split("</h2>", 1)[0]  # header badge


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
    # All-MISSING placeholders for all 6
    assert section.count("MISSING") >= 6


# (e) Stale sidecar — frozen-clock test
def test_prd112_e_stale_sidecar_uses_frozen_clock_badge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed_now = _dt112(2026, 5, 10, 12, 0, 0, tzinfo=_tz112.utc)
    stale_iso = "2026-05-10T11:30:00+00:00"  # 1800s old, > 300s
    snap = _ts_healthy_snapshot(generated_at=stale_iso)

    class _FrozenDT(_dt112):  # type: ignore[misc]
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(_dr112, "datetime", _FrozenDT)
    html = render_dashboard_html(
        _payload(), _run(), market_map=_market_map(),
        trend_structure_snapshot=snap,
    )
    section = _ts_section(html)
    header = section.split("</h2>", 1)[0]
    assert "STALE" in header, header


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


# R6 — Diagnostics block remains visible with all four required entries under unhealthy lineage.
def test_prd116_r6_diagnostics_preserved_under_mixed() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp("2026-04-28T12:00:00Z")
    mm = _market_map({"SPY": _mm_symbol("SPY")})
    payload["meta"]["generation_id"] = "gen-A"
    run["generation_id"] = "gen-B"
    mm["generation_id"] = "gen-C"
    html = render_dashboard_html(payload, run, market_map=mm)
    diagnostics = _artifact_diagnostics(html)
    for entry in (
        "artifact_lineage_state=",
        "payload_generation_id=",
        "run_generation_id=",
        "market_map_generation_id=",
    ):
        assert entry in diagnostics


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

    _assert_lineage_state(html, "COHERENT")
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

    _assert_lineage_state(html, "MIXED")
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

    _assert_lineage_state(html, "COHERENT")
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

from cuttingboard.delivery.dashboard_renderer import (
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

from cuttingboard.delivery.dashboard_renderer import (
    INACTIVE_SESSION_MAX_AGE_HOURS,
    LIVE_SESSION_MAX_AGE_MINUTES,
)

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

from cuttingboard.delivery.dashboard_renderer import (
    _macro_tape_source_health,
    _market_map_source_health,
    _system_state_source_health,
    _trend_structure_source_health,
    _trend_symbols_usable,
)


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
def test_prd120_permission_monitor_only_active_no_trade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    html = _prd120_coherent_render(
        run_overrides={"permission": None, "outcome": "NO_TRADE", "system_halted": False},
    )
    perm = _prd120_perm_field(html)
    assert ">&#8212;<" not in perm
    assert "MONITOR_ONLY" in perm


# R14-2: HALTED precedence over MONITOR_ONLY/UNKNOWN.
def test_prd120_permission_halted_wins_over_monitor_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    html = _prd120_coherent_render(
        run_overrides={"permission": None, "outcome": "NO_TRADE", "system_halted": True},
    )
    perm = _prd120_perm_field(html)
    assert "HALTED" in perm
    assert "MONITOR_ONLY" not in perm


# R14-3: catch-all UNKNOWN when permission None, outcome="TRADE", not halted.
def test_prd120_permission_unknown_catchall_outcome_trade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    html = _prd120_coherent_render(
        run_overrides={"permission": None, "outcome": "TRADE", "system_halted": False},
    )
    perm = _prd120_perm_field(html)
    assert "UNKNOWN" in perm
    assert "MONITOR_ONLY" not in perm


# R14-4: Trend Structure SOURCE: MISSING when _ts_records is None.
def test_prd120_trend_structure_source_missing_under_coherent_lineage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    html = _prd120_coherent_render(trend_structure_snapshot=None)
    section = _ts_section(html)
    assert "SOURCE: MISSING" in section
    # R6: TREND SYMBOLS suppressed under MISSING.
    assert "TREND SYMBOLS:" not in section


# R14-5: Trend Structure SOURCE: STALE when generated_at is stale.
def test_prd120_trend_structure_source_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed_now = _dt112(2026, 5, 10, 12, 0, 0, tzinfo=_tz112.utc)
    stale_iso = "2026-05-10T11:30:00+00:00"  # > 300s old
    snap = _ts_healthy_snapshot(generated_at=stale_iso)

    class _FrozenDT(_dt112):  # type: ignore[misc]
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(_dr112, "datetime", _FrozenDT)
    _freeze_renderer_now(monkeypatch, fixed_now)
    html = _prd120_coherent_render(trend_structure_snapshot=snap)
    section = _ts_section(html)
    assert "SOURCE: STALE" in section
    assert f"TREND SYMBOLS: 6/{len(_TS_CURATED)}" in section


# R14-6: Trend Structure SOURCE: INVALID when generated_at is unparsable.
def test_prd120_trend_structure_source_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    snap = _ts_healthy_snapshot(generated_at="not-a-date")
    html = _prd120_coherent_render(trend_structure_snapshot=snap)
    section = _ts_section(html)
    assert "SOURCE: INVALID" in section
    # R6: TREND SYMBOLS suppressed under INVALID.
    assert "TREND SYMBOLS:" not in section


# R14-7: TREND SYMBOLS 0/6 + FALLBACK when snapshot exists but every
# symbol record is missing required fields.
def test_prd120_trend_structure_source_fallback_zero_usable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    snap = {
        "schema_version": 1,
        "generated_at": "2026-04-28T12:00:00+00:00",
        "symbols": {sym: {"symbol": sym} for sym in _TS_CURATED},
    }

    # Freeze renderer-side `datetime` so trend freshness reads FRESH.
    fixed_now = _dt112(2026, 4, 28, 12, 1, 0, tzinfo=_tz112.utc)

    class _FrozenDT(_dt112):  # type: ignore[misc]
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(_dr112, "datetime", _FrozenDT)

    html = _prd120_coherent_render(trend_structure_snapshot=snap)
    section = _ts_section(html)
    assert "SOURCE: FALLBACK" in section
    assert "TREND SYMBOLS: 0/6" in section


# R14-8: Macro Tape FALLBACK when any tape slot is `--` or `N/A`.
def test_prd120_macro_tape_source_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    # Default _payload() has no macro_drivers; pass _macro_drivers() so the
    # block does not short-circuit to MISSING. Market map has no symbols
    # for SPY/QQQ/IWM/GLD -> tradable slots render "N/A" -> FALLBACK.
    payload = _payload(macro_drivers=_macro_drivers())
    run = _run()
    mm = _market_map()  # empty symbols
    payload["meta"]["generation_id"] = "test-gen-001"
    run["generation_id"] = "test-gen-001"
    mm["generation_id"] = "test-gen-001"
    html = render_dashboard_html(payload, run, market_map=mm)
    tape = _macro_tape_block(html)
    assert "MACRO SOURCE: FALLBACK" in tape


# R14-9: Market Map OK with setups N matching rendered card count.
def test_prd120_market_map_source_ok_with_setup_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    mm = _market_map({
        "SPY": _mm_symbol("SPY", grade="A"),
        "QQQ": _mm_symbol("QQQ", grade="B"),
    })
    html = _prd120_coherent_render(market_map=mm)
    board = _candidate_board_only(html)
    assert "MARKET MAP SOURCE: OK - setups 2" in board


# R14-10: No stale precedent path emits OK.
def test_prd120_macro_tape_missing_does_not_emit_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    # No macro_drivers, no macro snapshot path -> MISSING.
    html = _prd120_coherent_render()
    tape = _macro_tape_block(html)
    # OK never emitted when underlying signal is MISSING.
    assert "MACRO SOURCE: OK" not in tape


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
    assert _trend_structure_source_health(
        artifact_lineage_state="COHERENT", inactive_session=False,
        snapshot={"symbols": {"SPY": rec}}, ts_generated_at_raw=fresh, usable_count=0,
    ) == "FALLBACK"
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
def test_prd120_trend_structure_inactive_session_label_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    payload = _payload()
    payload["meta"]["session_type"] = "SUNDAY_PREMARKET"
    payload["meta"]["generation_id"] = "test-gen-001"
    run = _run()
    run["generation_id"] = "test-gen-001"
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    mm["generation_id"] = "test-gen-001"
    html = render_dashboard_html(
        payload, run, market_map=mm, trend_structure_snapshot=None,
    )
    section = _ts_section(html)
    assert "SOURCE: INACTIVE_SESSION" in section
    assert INACTIVE_SESSION_LABEL in section
    assert "SOURCE: MISSING" not in section


# R14-15: MIXED lineage drives Trend Structure and Market Map blocks to MIXED.
def test_prd120_mixed_lineage_drives_trend_and_market_map_mixed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    payload = _payload(macro_drivers=_macro_drivers())
    run = _run()
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    payload["meta"]["generation_id"] = "gen-A"
    run["generation_id"] = "gen-B"  # mismatch -> MIXED lineage
    mm["generation_id"] = "gen-A"
    snap = _ts_healthy_snapshot()
    html = render_dashboard_html(
        payload, run, market_map=mm, trend_structure_snapshot=snap,
    )
    ts_section = _ts_section(html)
    board = _candidate_board_only(html)
    assert "SOURCE: MIXED" in ts_section
    assert "MARKET MAP SOURCE: MIXED" in board


# R14-16: no `>&#8212;<` inside Permission field for coherent active NO_TRADE.
def test_prd120_no_em_dash_in_permission_under_coherent_lineage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    html = _prd120_coherent_render(
        run_overrides={"permission": None, "outcome": "NO_TRADE"},
    )
    perm = _prd120_perm_field(html)
    assert ">&#8212;<" not in perm


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
    perm = _prd120_perm_field(html)
    assert "HALTED" in perm
    assert "MONITOR_ONLY" not in perm
    assert "UNKNOWN" not in perm


# R14-19: Non-ui render still emits source-health diagnostics.
def test_prd120_non_ui_render_emits_source_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    payload, run, market_map = _coherent_inputs()
    out = _non_ui_output_path(tmp_path)
    write_dashboard(
        payload, run,
        market_map=market_map,
        output_path=out,
        fixture_mode=False,
    )
    html = out.read_text(encoding="utf-8")
    assert "SOURCE:" in html
    assert "MACRO SOURCE:" in html
    assert "MARKET MAP SOURCE:" in html


# R14-20: malformed payload.meta.timestamp under coherent lineage renders
# System State SOURCE: INVALID (not STALE).
def test_prd120_system_state_invalid_when_timestamp_unparsable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    payload = _payload(timestamp="not-a-date")
    payload["meta"]["generation_id"] = "test-gen-001"
    run = _run()
    run["generation_id"] = "test-gen-001"
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    mm["generation_id"] = "test-gen-001"
    html = render_dashboard_html(payload, run, market_map=mm)
    state = _system_state_block(html)
    assert "SOURCE: INVALID" in state
    assert "SOURCE: STALE" not in state


# R14-21: permission=None under MIXED lineage -> UNKNOWN, not MONITOR_ONLY.
def test_prd120_permission_unknown_under_mixed_lineage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    payload = _payload()
    payload["meta"]["generation_id"] = "gen-A"
    run = _run(permission=None, outcome="NO_TRADE")
    run["generation_id"] = "gen-B"  # mixed lineage
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    mm["generation_id"] = "gen-A"
    html = render_dashboard_html(payload, run, market_map=mm)
    perm = _prd120_perm_field(html)
    assert "UNKNOWN" in perm
    assert "MONITOR_ONLY" not in perm


# R14-22: MIXED lineage with non-empty market_map.symbols -> setups 0.
def test_prd120_market_map_mixed_lineage_setups_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_renderer_now(monkeypatch)
    payload = _payload()
    payload["meta"]["generation_id"] = "gen-A"
    run = _run()
    run["generation_id"] = "gen-B"  # mixed lineage
    mm = _market_map({
        "SPY": _mm_symbol("SPY", grade="A"),
        "QQQ": _mm_symbol("QQQ", grade="B"),
    })
    mm["generation_id"] = "gen-A"
    html = render_dashboard_html(payload, run, market_map=mm)
    board = _candidate_board_only(html)
    assert "MARKET MAP SOURCE: MIXED - setups 0" in board


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

