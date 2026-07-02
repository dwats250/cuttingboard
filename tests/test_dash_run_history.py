"""Tests for PRD-055 — dashboard renderer: Run history/snapshot section and run delta."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cuttingboard.delivery.dashboard_renderer import (
    _resolve_previous_run,
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

    # PRD-158 § 4.2 translation 13: regime transition to NEUTRAL has no
    # "Permission flipped to …" phrase and is suppressed.
    assert "Permission flipped to" not in delta
    assert "Regime:" not in delta
    assert "Posture: Stay Flat -&gt; Controlled Long" in delta
    assert "System Halted: YES -&gt; NO" in delta


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
# PRD-042 run history — CUT by PRD-177 R1 (debugging surface of no trader value)
# ---------------------------------------------------------------------------

def test_run_history_section_cut() -> None:
    # PRD-177 R1: the run-history section is gone regardless of history_runs.
    html = render_dashboard_html(_payload(), _run(), history_runs=[_run()])
    assert 'id="run-history"' not in html
    assert "NO_HISTORY" not in html


def test_run_history_argument_still_accepted_and_deterministic() -> None:
    # history_runs remains a tolerated argument (loaded by main()); it renders
    # nothing now, but passing it must not crash and stays deterministic.
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

def test_run_health_fields() -> None:
    # PRD-219: halt shows in the distilled verdict; the operational error is the
    # context reason (no raw "YES" halted-bool field).
    html = render_dashboard_html(_payload(), _run(system_halted=True, kill_switch=False, errors=["err_unique"]))
    health = html.split('id="system-state"', 1)[1]
    assert "SYSTEM HALT" in health
    assert "err_unique"  in health


def test_run_health_no_error_when_empty() -> None:
    html = render_dashboard_html(_payload(), _run(errors=[]))
    health = html.split('id="system-state"', 1)[1]
    assert ">Error<" not in health


def test_run_delta_no_previous_run_shows_no_previous_run() -> None:
    """When previous_run is None, Changes Since Last Run shows NO_PREVIOUS_RUN not SOURCE_MISSING."""
    html = render_dashboard_html(_payload(), _run(), previous_run=None)
    # PRD-177 R1/R2: run-history is cut; the run-delta block now ends at the
    # scoreboard section that follows it.
    delta = html.split('id="run-delta"', 1)[1].split('id="scoreboard"', 1)[0]
    assert "NO_PREVIOUS_RUN" in delta
    assert "SOURCE_MISSING" not in delta
