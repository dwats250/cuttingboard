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
    render_dashboard_html,
)
from tests.dash_helpers import _macro_drivers, _market_map, _mm_symbol, _payload, _run

_UI_INDEX = Path("ui/index.html")


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


def test_mixed_payload_run_renders_warning_and_suppresses_active_setup() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp(
        "2026-04-28T12:10:01Z",
        outcome="TRADE",
        permission=True,
    )

    html = render_dashboard_html(payload, run, market_map=_market_map())

    assert "MIXED_ARTIFACTS" in html
    assert "TRADE SETUP ACTIVE" not in html
    assert "ACTION: ACTIVE" not in html


def test_coherent_payload_run_preserves_active_setup_behavior() -> None:
    payload = _payload(timestamp="2026-04-28T12:00:00Z", macro_drivers=_macro_drivers())
    run = _run_with_timestamp(
        "2026-04-28T12:00:00Z",
        outcome="TRADE",
        permission=True,
    )

    html = render_dashboard_html(payload, run, market_map=_market_map())

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

    assert "STALE_MARKET_MAP" in board
    assert "Candidate Board suppressed" in board
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
    assert "SOURCE_MISSING" in delta_block
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


def test_halted_and_kill_switch_visible_in_system_state() -> None:
    run = _run(system_halted=True, kill_switch=False)
    html = render_dashboard_html(_payload(), run)
    state = _system_state_block(html)
    assert "Halted" in state
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
