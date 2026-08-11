"""PRD-297 (D4): prove the DRIFT full-suite observation is structurally non-authoritative.

It must be impossible for the drift workflow to gate the morning slot, publish or
mutate a market artifact, satisfy the exact-SHA CI proof, or set PUBLISH_READY.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from scripts import check_run_revision as cr

ROOT = Path(__file__).resolve().parents[1]
DRIFT = ROOT / ".github/workflows/drift_full_suite.yml"
DRIFT_PATH = ".github/workflows/drift_full_suite.yml"
SHA = "a" * 40


def _doc() -> dict:
    return yaml.safe_load(DRIFT.read_text(encoding="utf-8"))


def _text() -> str:
    return DRIFT.read_text(encoding="utf-8")


def _noncomment_text() -> str:
    """The workflow with comment lines stripped (comments may name what is EXCLUDED)."""
    return "\n".join(line for line in _text().splitlines() if not line.strip().startswith("#"))


def test_permissions_are_read_only():
    perms = _doc().get("permissions")
    assert perms == {"contents": "read"}, f"drift workflow must be contents:read only, got {perms}"


def test_no_publish_push_or_market_mutation():
    text = _noncomment_text()
    for forbidden in (
        "PUBLISH_READY",
        "ci_push_artifacts",
        "git push",
        "send_telegram",
        "publish",
        "secrets.",
        "dashboard_renderer",
        "regime_history",
    ):
        assert forbidden not in text, f"drift workflow must not reference {forbidden!r}"


def test_it_actually_runs_the_suite():
    # The drift observation must exist (it is the point of D4).
    assert "pytest tests/ -q" in _text()


def test_triggers_are_schedule_and_dispatch_only():
    on = _doc().get(True) or _doc().get("on")  # PyYAML may parse `on:` as boolean True
    assert "schedule" in on and "workflow_dispatch" in on
    # No push/pull_request trigger that could masquerade as a CI event.
    assert "push" not in on and "pull_request" not in on


def test_ci_proof_selector_can_never_select_the_drift_workflow():
    # check_run_revision filters to path == .github/workflows/ci.yml, so a run of
    # the drift workflow (even a hypothetical push/success) is not selectable.
    assert cr.CI_WORKFLOW_PATH != DRIFT_PATH
    drift_run = {
        "status": "completed",
        "conclusion": "success",
        "event": "push",
        "path": DRIFT_PATH,
        "head_sha": SHA,
        "run_number": 1,
        "created_at": "2026-08-11T00:00:00Z",
    }
    assert cr._select([drift_run], SHA) is None
