"""Tests for PRD-055 — dashboard renderer: Run history/snapshot section and run delta."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cuttingboard.delivery.dashboard_renderer import (
    HISTORY_LIMIT,
    _resolve_previous_run,
    main,
    render_dashboard_html,
)

from tests.dash_helpers import _payload, _run


# ---------------------------------------------------------------------------
# PRD-041 — run delta (preserved)
# ---------------------------------------------------------------------------

def test_run_delta_detects_changes() -> None:
    current  = _run(regime="NEUTRAL",  posture="CONTROLLED_LONG", confidence=0.75, system_halted=False)
    previous = _run(regime="RISK_OFF", posture="STAY_FLAT",        confidence=0.25, system_halted=True)
    html     = render_dashboard_html(_payload(), current, previous_run=previous)
    delta    = html.split('id="run-delta"', 1)[1]
    delta    = delta.split('id="system-state"', 1)[0]

    assert "Regime: RISK_OFF -&gt; NEUTRAL"              in delta
    assert "Posture: Stay Flat -&gt; Controlled Long"   in delta
    assert "Confidence: 0.25 -&gt; 0.75"               in delta
    assert "System Halted: YES -&gt; NO"               in delta


def test_run_delta_ignores_unchanged_fields() -> None:
    html  = render_dashboard_html(_payload(), _run(), previous_run=_run())
    delta = html.split('id="run-delta"', 1)[1]
    delta = delta.split('id="system-state"', 1)[0]

    assert "No changes since last run" in delta
    assert "Regime:"         not in delta
    assert "Posture:"        not in delta
    assert "Confidence:"     not in delta
    assert "System Halted:"  not in delta


def test_run_delta_correct_previous_selection_by_timestamp(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    oldest          = _run(status="OLD",  confidence=0.1)
    oldest["timestamp"] = "2026-04-28T10:00:00Z"
    newest          = _run(status="NEW",  confidence=0.2)
    newest["timestamp"] = "2026-04-28T12:00:00Z"
    previous        = _run(status="PREV", confidence=0.3)
    previous["timestamp"] = "2026-04-28T11:00:00Z"

    (logs_dir / "run_oldest.json").write_text(json.dumps(oldest),   encoding="utf-8")
    (logs_dir / "run_newest.json").write_text(json.dumps(newest),   encoding="utf-8")
    (logs_dir / "run_previous.json").write_text(json.dumps(previous), encoding="utf-8")

    assert _resolve_previous_run(logs_dir) == previous


def test_run_delta_no_unapproved_fields() -> None:
    previous = _run(status="HALT", kill_switch=True, data_status="stale")
    html     = render_dashboard_html(_payload(), _run(), previous_run=previous)
    delta    = html.split('id="run-delta"', 1)[1]
    delta    = delta.split('id="system-state"', 1)[0]

    for field in ("Status:", "Kill Switch:", "Data Status:", "Outcome:", "Run Id:"):
        assert field not in delta


def test_render_function_does_not_discover_files(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cuttingboard.delivery.dashboard_renderer._resolve_previous_run",
        lambda logs_dir: (_ for _ in ()).throw(AssertionError("unexpected discovery")),
    )
    html = render_dashboard_html(_payload(), _run(), previous_run=_run())
    assert 'id="run-delta"' in html


def test_run_delta_deterministic_output() -> None:
    payload  = _payload()
    current  = _run(regime="NEUTRAL", posture="STAY_FLAT", confidence=0.0)
    previous = _run(regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.75)
    assert render_dashboard_html(payload, current, previous_run=previous) == render_dashboard_html(
        payload, current, previous_run=previous
    )


# ---------------------------------------------------------------------------
# PRD-042 — run history (preserved)
# ---------------------------------------------------------------------------

def test_run_history_present() -> None:
    html = render_dashboard_html(_payload(), _run(), history_runs=[_run()])
    assert 'id="run-history"' in html


def test_run_history_limit_enforced(tmp_path: Path) -> None:
    logs_dir     = tmp_path / "logs"
    logs_dir.mkdir()
    payload_file = tmp_path / "latest_payload.json"
    run_file     = tmp_path / "latest_run.json"
    out_file     = tmp_path / "dashboard.html"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    run_file.write_text(json.dumps(_run()), encoding="utf-8")

    for i in range(HISTORY_LIMIT + 2):
        history_run = _run(regime=f"RISK_{i}", posture=f"POSTURE_{i}", confidence=float(i))
        history_run["timestamp"] = f"2026-04-28T12:{i:02d}:00Z"
        (logs_dir / f"run_{i}.json").write_text(json.dumps(history_run), encoding="utf-8")

    main(payload_path=payload_file, run_path=run_file, output_path=out_file, logs_dir=logs_dir)
    history = out_file.read_text(encoding="utf-8").split('id="run-history"', 1)[1]
    import re as _re
    data_cells = _re.findall(r'class="history-cell"', history)
    assert len(data_cells) // 4 == HISTORY_LIMIT


def test_run_history_sorted_descending(tmp_path: Path) -> None:
    logs_dir     = tmp_path / "logs"
    logs_dir.mkdir()
    payload_file = tmp_path / "latest_payload.json"
    run_file     = tmp_path / "latest_run.json"
    out_file     = tmp_path / "dashboard.html"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    run_file.write_text(json.dumps(_run()), encoding="utf-8")

    older                  = _run(regime="OLDER")
    older["timestamp"]  = "2026-04-28T10:00:00Z"
    newest                 = _run(regime="NEWEST")
    newest["timestamp"] = "2026-04-28T12:00:00Z"
    middle                 = _run(regime="MIDDLE")
    middle["timestamp"] = "2026-04-28T11:00:00Z"

    (logs_dir / "run_older.json").write_text(json.dumps(older),   encoding="utf-8")
    (logs_dir / "run_newest.json").write_text(json.dumps(newest), encoding="utf-8")
    (logs_dir / "run_middle.json").write_text(json.dumps(middle), encoding="utf-8")

    main(payload_path=payload_file, run_path=run_file, output_path=out_file, logs_dir=logs_dir)
    history = out_file.read_text(encoding="utf-8").split('id="run-history"', 1)[1]
    assert history.index("NEWEST") < history.index("MIDDLE") < history.index("OLDER")


def test_run_history_field_mapping_exact() -> None:
    history_run = _run(regime="RISK_OFF", posture="STAY_FLAT", confidence=0.25)
    history_run["timestamp"] = "2026-04-28T12:50:00Z"
    html    = render_dashboard_html(_payload(), _run(), history_runs=[history_run])
    history = html.split('id="run-history"', 1)[1]
    assert "12:50" in history
    assert "RISK_OFF" in history
    assert "Stay Flat" in history
    assert "0.25" in history


def test_run_history_timestamp_format() -> None:
    history_run = _run()
    history_run["timestamp"] = "2026-04-28T09:30:45Z"
    html    = render_dashboard_html(_payload(), _run(), history_runs=[history_run])
    history = html.split('id="run-history"', 1)[1]
    assert "09:30" in history
    assert "2026-04-28T09:30:45Z" not in history


def test_run_history_no_extra_fields() -> None:
    history_run = _run(status="FAIL", system_halted=True, kill_switch=True, data_status="stale")
    html    = render_dashboard_html(_payload(), _run(), history_runs=[history_run])
    history = html.split('id="run-history"', 1)[1].lower()
    for field in ("status", "system_halted", "kill_switch", "data_status", "outcome", "run_id"):
        assert field not in history


def test_run_history_deterministic_output() -> None:
    payload      = _payload()
    run          = _run()
    history_runs = [
        _run(regime="RISK_OFF", posture="STAY_FLAT",        confidence=0.25),
        _run(regime="NEUTRAL",  posture="CONTROLLED_LONG",  confidence=0.75),
    ]
    history_runs[0]["timestamp"] = "2026-04-28T12:50:00Z"
    history_runs[1]["timestamp"] = "2026-04-28T11:45:00Z"
    assert render_dashboard_html(payload, run, history_runs=history_runs) == render_dashboard_html(
        payload, run, history_runs=history_runs
    )


# ---------------------------------------------------------------------------
# Run health (preserved)
# ---------------------------------------------------------------------------

def test_run_health_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    state = html.split('id="system-state"', 1)[1]
    assert 'class="action-line"' in state
    assert "SYSTEM ACTIVE"       in state


def test_run_health_fields() -> None:
    html = render_dashboard_html(_payload(), _run(system_halted=True, kill_switch=False, errors=["err_unique"]))
    health = html.split('id="system-state"', 1)[1]
    assert "YES"        in health   # system_halted
    assert "err_unique" in health


def test_run_health_no_error_when_empty() -> None:
    html = render_dashboard_html(_payload(), _run(errors=[]))
    health = html.split('id="system-state"', 1)[1]
    assert ">Error<" not in health


def test_run_delta_no_previous_run_shows_no_previous_run() -> None:
    """When previous_run is None, Changes Since Last Run shows NO_PREVIOUS_RUN not SOURCE_MISSING."""
    html = render_dashboard_html(_payload(), _run(), previous_run=None)
    delta = html.split('id="run-delta"', 1)[1].split('id="run-history"', 1)[0]
    assert "NO_PREVIOUS_RUN" in delta
    assert "SOURCE_MISSING" not in delta
