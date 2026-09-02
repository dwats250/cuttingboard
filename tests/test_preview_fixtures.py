"""PRD-179 — preview fixture / all-section-state coverage tests.

R1 — every enumerated reachable section state has a catalog case.
R2 — the harness writes only to non-ui paths, and every case is structurally
     unpublishable to ui/ (the publish gate fails closed).
R4 — each case render contains its section-state marker.
PRD-326 R8 — five primary-chart matrix cases; the harness and this module are
     hermetic against a live `logs/intraday_bars_snapshot.json`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cuttingboard.delivery import dashboard_renderer as _dr
from cuttingboard.delivery.dashboard_renderer import (
    CoherentPublishError,
    _output_under_ui,
    render_dashboard_html,
    validate_coherent_publish,
)
from scripts.preview_fixtures import OUT_DIR, render_all
from tests.dash_helpers import _intraday_snapshot
from tests.preview_fixtures import _D1_NOW, SECTION_STATE_CASES

# The reachable section states enumerated in docs/prd_history/PRD-179.md
# (REALIZABILITY). This set is the R1 contract: a reachable state without a
# case, or a case without a documented state, fails the suite.
_EXPECTED_CASE_NAMES = {
    "coherence_mixed",
    "sunday_premarket",
    "session_inactive",
    "macro_tape_no_data",
    "red_folder_error",
    "red_folder_expiring",
    "trend_awaiting_data",
    "trend_no_data",
    "lineage_missing",
    "candidate_no_candidates",
    "healthy_baseline",
    # PRD-326 (D1) primary-chart matrix (REALIZABILITY extended by PRD-326 R8)
    "primary_chart_stay_flat",
    "primary_chart_locked",
    "primary_chart_permitted",
    "market_map_stale_with_bars",
    "primary_chart_c_grade",
    # PRD-329 (D3) S2: promoted SPY SESSION observation with neutral chart + ladder
    "spy_session_observed",
}
_D1_CHART_CASES = ("primary_chart_stay_flat", "primary_chart_locked",
                   "primary_chart_permitted", "primary_chart_c_grade")
_D1_NO_CHART_CASES = ("healthy_baseline", "candidate_no_candidates",
                      "market_map_stale_with_bars", "coherence_mixed")
_HERMETIC_MISSING = Path("/nonexistent/cuttingboard/preview_intraday_bars_snapshot.json")

_CASE_IDS = [c.name for c in SECTION_STATE_CASES]


@pytest.fixture(autouse=True)
def _hermetic_intraday_sidecar(monkeypatch):
    # PRD-326 R8: never let a real/live A1-P sidecar reach a fixture render.
    monkeypatch.setattr(_dr, "_INTRADAY_BARS_SNAPSHOT_PATH", _HERMETIC_MISSING)


def _case(name: str):
    return next(c for c in SECTION_STATE_CASES if c.name == name)


def _render(case) -> str:
    return render_dashboard_html(
        case.payload,
        case.run,
        market_map=case.market_map,
        fixture_mode=case.fixture_mode,
        **case.render_kwargs,
    )


# --- R1: coverage ----------------------------------------------------------

def test_catalog_covers_every_reachable_state():
    assert {c.name for c in SECTION_STATE_CASES} == _EXPECTED_CASE_NAMES


def test_case_names_unique():
    assert len(_CASE_IDS) == len(set(_CASE_IDS))


# --- R4: each case renders its section-state marker ------------------------

@pytest.mark.parametrize("case", SECTION_STATE_CASES, ids=_CASE_IDS)
def test_case_render_contains_marker(case):
    html = _render(case)
    assert case.marker in html, f"{case.name}: marker {case.marker!r} absent"
    for extra in case.extra_markers:
        assert extra in html, f"{case.name}: extra marker {extra!r} absent"


def test_trend_awaiting_case_is_time_independent():
    # Regression guard (PR #20 Codex review): the AWAITING_DATA fixture must not
    # carry a wall-clock `generated_at`, or a render >300s after import flips the
    # snapshot to STALE and the marker disappears. Omitting generated_at skips the
    # freshness gate entirely.
    case = next(c for c in SECTION_STATE_CASES if c.name == "trend_awaiting_data")
    snap = case.render_kwargs["trend_structure_snapshot"]
    assert "generated_at" not in snap


def test_healthy_baseline_has_no_demo_banner():
    case = next(c for c in SECTION_STATE_CASES if c.name == "healthy_baseline")
    html = _render(case)
    assert "DEMO MODE" not in html


# --- R2: non-ui only / structurally unpublishable --------------------------

def test_harness_output_dir_is_non_ui():
    assert not _output_under_ui(OUT_DIR / "fixture_x.html")


@pytest.mark.parametrize("case", SECTION_STATE_CASES, ids=_CASE_IDS)
def test_case_blocked_from_ui_publish(case):
    # Every case carries a "fixture" generation_id (or a missing artifact), so
    # the PRD-118 coherent-publish gate must fail closed for a ui/ output path.
    with pytest.raises(CoherentPublishError):
        validate_coherent_publish(
            payload=case.payload,
            run=case.run,
            market_map=case.market_map,
            output_path=Path("ui/dashboard.html"),
            fixture_mode=case.fixture_mode,
        )


# --- harness end-to-end (R2 path + R4) -------------------------------------

def test_harness_renders_all_to_non_ui(tmp_path):
    written = render_all(out_dir=tmp_path)
    assert len(written) == len(SECTION_STATE_CASES)
    for path in written:
        assert path.exists()
        assert not _output_under_ui(path)
        assert path.read_text(encoding="utf-8").lstrip().startswith("<!doctype html>")


def test_harness_refuses_ui_out_dir(tmp_path):
    # render_all writes HTML directly, bypassing validate_coherent_publish, so it
    # must structurally refuse a ui/ out_dir or fixture HTML could reach the publish
    # tree (PR #20 review). The guard reuses the publish path's _output_under_ui
    # helper and must reject before creating the directory.
    ui_dir = tmp_path / "ui"
    with pytest.raises(SystemExit):
        render_all(out_dir=ui_dir)
    assert not ui_dir.exists()


def test_harness_refuses_symlink_into_ui(tmp_path):
    # The per-file guard must resolve symlinks: a planted fixture_*.html symlink
    # into ui/ would otherwise let write_text follow it into the publish tree even
    # though out_dir itself resolves outside ui/ (PR #20 review).
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    target = tmp_path / "ui" / "dashboard.html"
    target.parent.mkdir()
    target.write_text("PUBLISH", encoding="utf-8")
    link = out_dir / f"fixture_{SECTION_STATE_CASES[0].name}.html"
    link.symlink_to(target)
    with pytest.raises(SystemExit):
        render_all(out_dir=out_dir)
    assert target.read_text(encoding="utf-8") == "PUBLISH"  # publish tree untouched


# --- PRD-326 R8: primary-chart matrix and sidecar hermeticity ---------------

@pytest.mark.parametrize("name", _D1_CHART_CASES)
def test_prd326_chart_case_renders_an_undisclosed_primary_chart(name):
    html = _render(_case(name))
    assert "<details" not in html.split('id="card-SPY"', 1)[1].split('class="setup-chart"', 1)[0]
    assert "bars through 2026-08-27" in html                      # the daily caption


@pytest.mark.parametrize("name", _D1_NO_CHART_CASES)
def test_prd326_no_primary_cases_render_no_chart(name):
    html = _render(_case(name))
    assert 'class="setup-chart"' not in html and 'class="chart-caption"' not in html


def test_prd326_harness_is_hermetic_against_a_live_intraday_sidecar(monkeypatch, tmp_path):
    # M14: a planted, age-admitted sidecar whose primary_symbol equals the chart
    # case's primary must NOT reach `render_all`; the case keeps its daily caption.
    planted = tmp_path / "intraday_bars_snapshot.json"
    planted.write_text(json.dumps(_intraday_snapshot(_D1_NOW, primary="SPY")), encoding="utf-8")
    monkeypatch.setattr(_dr, "_INTRADAY_BARS_SNAPSHOT_PATH", planted)
    render_all(out_dir=tmp_path / "out")
    html = (tmp_path / "out" / "fixture_primary_chart_stay_flat.html").read_text(encoding="utf-8")
    assert "bars through 2026-08-27" in html and "completed through" not in html
    assert _dr._INTRADAY_BARS_SNAPSHOT_PATH == planted            # restored after rendering
