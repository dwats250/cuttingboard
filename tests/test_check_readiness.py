"""Guardrail for the HTML-marker gate in scripts/check_readiness.py.

MICRO (PRD-219 downstream-consumer miss): PRD-219 (commit 7768bd4) renamed the
`RUN SNAPSHOT` freshness label to `UPDATED` in the renderer, but
check_readiness.py kept requiring the retired `RUN SNAPSHOT` marker. Nothing
forced the guard and the renderer to agree, so the hourly-alert readiness gate
failed silently until the stale marker was cut. This test is that missing
mechanism: it pins that EVERY marker in REQUIRED_HTML_MARKERS is actually
enforced (fails-when-absent), and that a complete artifact passes.

Fixtures are synthetic and owned here ON PURPOSE. Pointing the test at the real
ui/*.html would re-create the same silent coupling one level up: it would pass
on whatever the renderer happens to emit, which is exactly the gap that let the
drift land. The test controls its own HTML so a renderer change cannot mask a
broken gate.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import check_readiness as cr


def _synthetic_html(markers) -> str:
    """Minimal HTML carrying exactly `markers` and nothing forbidden."""
    body = "\n".join(
        f"<div {m}></div>" if m.startswith("id=") else f"<div>{m}</div>"
        for m in markers
    )
    return f"<html><body>\n{body}\n</body></html>"


def _write_dashboard(root: Path, html: str) -> Path:
    rel = Path("ui/dashboard.html")
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(html, encoding="utf-8")
    return rel


def test_passes_when_all_required_markers_present(tmp_path, monkeypatch):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    rel = _write_dashboard(tmp_path, _synthetic_html(cr.REQUIRED_HTML_MARKERS))

    failures: list[str] = []
    cr._validate_html_artifact(rel, failures)

    assert failures == []


@pytest.mark.parametrize("dropped", cr.REQUIRED_HTML_MARKERS)
def test_fails_when_a_required_marker_is_absent(tmp_path, monkeypatch, dropped):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    present = [m for m in cr.REQUIRED_HTML_MARKERS if m != dropped]
    rel = _write_dashboard(tmp_path, _synthetic_html(present))

    failures: list[str] = []
    cr._validate_html_artifact(rel, failures)

    assert any(
        dropped in f and "missing required marker" in f for f in failures
    ), f"gate did not flag missing marker {dropped!r}; failures={failures}"


# PRD-287: the hourly run artifact's HEALTH gate (not just key presence).
# check_readiness must reject an UNHEALTHY run — an in-run system failure and a
# data-integrity VALIDATION halt — while passing a healthy TRADE/NO_TRADE and a
# market-stress safety HALT, and must fail loud on malformed values. Fixtures are
# synthetic and owned here (same rationale as the HTML tests above).


def _write_run(root: Path, data) -> None:
    rel = cr.HOURLY_RUN_PATH
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(json.dumps(data), encoding="utf-8")


def _run_failures(root: Path) -> list[str]:
    failures: list[str] = []
    cr._validate_json_artifact(cr.HOURLY_RUN_PATH, cr.JSON_REQUIRED_FIELDS[cr.HOURLY_RUN_PATH], failures)
    return failures


_HEALTHY_TRADE = {"status": "SUCCESS", "outcome": "TRADE", "errors": [], "system_halted": False}
_HEALTHY_NO_TRADE = {"status": "SUCCESS", "outcome": "NO_TRADE", "errors": [], "system_halted": False}
_SAFETY_HALT = {"status": "FAIL", "outcome": "HALT", "errors": [], "system_halted": True}
_SYSTEM_FAILURE = {"status": "FAIL", "outcome": "HALT", "errors": ["data fetch failed"], "system_halted": True}
_VALIDATION_HALT = {"status": "SUCCESS", "outcome": "NO_TRADE", "errors": [], "system_halted": True}


@pytest.mark.parametrize(
    "artifact",
    [_HEALTHY_TRADE, _HEALTHY_NO_TRADE, _SAFETY_HALT],
    ids=["healthy_trade", "healthy_no_trade", "market_stress_safety_halt"],
)
def test_healthy_run_artifacts_pass(tmp_path, monkeypatch, artifact):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _write_run(tmp_path, artifact)
    assert _run_failures(tmp_path) == []


def test_in_run_system_failure_artifact_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _write_run(tmp_path, _SYSTEM_FAILURE)
    failures = _run_failures(tmp_path)
    assert any("in-run system failure" in f for f in failures), failures


def test_validation_halt_artifact_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _write_run(tmp_path, _VALIDATION_HALT)
    failures = _run_failures(tmp_path)
    assert any("data-integrity validation halt" in f for f in failures), failures


@pytest.mark.parametrize(
    "mutation, needle",
    [
        ({"status": "WAT"}, "status"),
        ({"outcome": "NOPE"}, "outcome"),
        ({"errors": {}}, "errors must be a list"),
        ({"system_halted": "yes"}, "system_halted must be a bool"),
    ],
    ids=["bad_status", "bad_outcome", "non_list_errors", "non_bool_system_halted"],
)
def test_malformed_run_artifact_fails_loud(tmp_path, monkeypatch, mutation, needle):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    artifact = {**_HEALTHY_NO_TRADE, **mutation}
    _write_run(tmp_path, artifact)
    failures = _run_failures(tmp_path)
    assert any(needle in f for f in failures), failures


@pytest.mark.parametrize("dropped", ("status", "outcome", "errors", "system_halted"))
def test_missing_required_health_field_fails(tmp_path, monkeypatch, dropped):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    artifact = {k: v for k, v in _HEALTHY_NO_TRADE.items() if k != dropped}
    _write_run(tmp_path, artifact)
    failures = _run_failures(tmp_path)
    assert any(dropped in f and "missing required field" in f for f in failures), failures
