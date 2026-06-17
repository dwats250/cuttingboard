"""PRD-179 — preview fixture / all-section-state coverage tests.

R1 — every enumerated reachable section state has a catalog case.
R2 — the harness writes only to non-ui paths, and every case is structurally
     unpublishable to ui/ (the publish gate fails closed).
R4 — each case render contains its section-state marker.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cuttingboard.delivery.dashboard_renderer import (
    CoherentPublishError,
    _output_under_ui,
    render_dashboard_html,
    validate_coherent_publish,
)
from scripts.preview_fixtures import OUT_DIR, render_all
from tests.preview_fixtures import SECTION_STATE_CASES

# The reachable section states enumerated in docs/prd_history/PRD-179.md
# (REALIZABILITY). This set is the R1 contract: a reachable state without a
# case, or a case without a documented state, fails the suite.
_EXPECTED_CASE_NAMES = {
    "coherence_mixed",
    "sunday_premarket",
    "session_inactive",
    "macro_tape_no_data",
    "red_folder_error",
    "red_folder_empty",
    "red_folder_expiring",
    "trend_awaiting_data",
    "trend_no_data",
    "lineage_missing",
    "candidate_no_candidates",
    "healthy_baseline",
}

_CASE_IDS = [c.name for c in SECTION_STATE_CASES]


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
