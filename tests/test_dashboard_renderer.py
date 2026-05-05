"""PRD-083: focused tests for dashboard data freshness and source visibility."""
from __future__ import annotations

import json
import os
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


# PA3 — published artifact must use mobile-friendly grid (minmax ≤ 100px)
def test_published_artifact_mobile_grid_width() -> None:
    if not _UI_INDEX.exists():
        pytest.skip("ui/index.html not present")
    html = _UI_INDEX.read_text(encoding="utf-8")
    import re
    m = re.search(r"macro-tape-grid\{[^}]*minmax\((\d+)px", html)
    assert m is not None, "macro-tape-grid minmax not found in ui/index.html"
    assert int(m.group(1)) <= 100, (
        f"macro-tape-grid minmax is {m.group(1)}px — must be ≤100px for mobile"
    )


def _candidate_board_section(html: str) -> str:
    return html.split('id="candidate-board"', 1)[1].split('</div>\n\n', 1)[0]


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
