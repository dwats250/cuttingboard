"""PRD-083: focused tests for dashboard data freshness and source visibility."""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import pytest

from cuttingboard.delivery.dashboard_renderer import (
    DASHBOARD_STALE_AFTER_SECONDS,
    _UNAVAILABLE_WATCH,
    render_dashboard_html,
)
from tests.dash_helpers import _macro_drivers, _market_map, _mm_symbol, _payload, _run

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
    assert "payload_generation_id=unavailable" in html
    assert "run_generation_id=unavailable" in html
    assert "market_map_generation_id=unavailable" in html


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
    run = _run(permission=None)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "&#8212;" in state
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
    run = _run(permission=None)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "&#8212;" in state
    perm_section = state.split("Permission", 1)[1]
    assert "NONE" not in perm_section.split("Reason", 1)[0]


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
