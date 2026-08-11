"""PRD-297: the morning profile of check_readiness, and the hourly-unchanged regression.

Proves (1) `--profile morning` validates logs/latest_run.json run-health plus the
freshly-rendered dashboard/index markers and fails per class, and (2) the flagless
(hourly) invocation is bit-identical to pre-PRD-297 behavior.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts import check_readiness as cr

HEALTHY_RUN = {"status": "SUCCESS", "outcome": "NO_TRADE", "errors": [], "system_halted": False}
HOURLY_PAYLOAD = {"meta": {}, "run_status": "ok", "schema_version": 1, "sections": []}


def _healthy_html() -> str:
    return "<html>" + "".join(f"<div {m}></div>" for m in cr.REQUIRED_HTML_MARKERS) + "</html>"


def _write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _morning_fixtures(root: Path, *, run=HEALTHY_RUN, html=None) -> None:
    _write(root, "logs/latest_run.json", json.dumps(run))
    html = _healthy_html() if html is None else html
    _write(root, "ui/dashboard.html", html)
    _write(root, "ui/index.html", html)


def _hourly_fixtures(root: Path, *, run=HEALTHY_RUN) -> None:
    _write(root, "logs/latest_hourly_payload.json", json.dumps(HOURLY_PAYLOAD))
    _write(root, "logs/latest_hourly_run.json", json.dumps(run))
    _write(root, "ui/dashboard.html", _healthy_html())
    _write(root, "ui/index.html", _healthy_html())


# --- morning profile: pass + per-class failures -----------------------------

def test_morning_healthy_passes(monkeypatch, tmp_path):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _morning_fixtures(tmp_path)
    assert cr.main(["--profile", "morning"]) == 0


def test_morning_missing_run_artifact_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _morning_fixtures(tmp_path)
    (tmp_path / "logs/latest_run.json").unlink()
    assert cr.main(["--profile", "morning"]) == 1


def test_morning_fail_status_with_errors_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _morning_fixtures(tmp_path, run={"status": "FAIL", "outcome": "NO_TRADE", "errors": ["boom"], "system_halted": False})
    assert cr.main(["--profile", "morning"]) == 1


def test_morning_system_halted_with_success_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _morning_fixtures(tmp_path, run={"status": "SUCCESS", "outcome": "NO_TRADE", "errors": [], "system_halted": True})
    assert cr.main(["--profile", "morning"]) == 1


def test_morning_missing_html_marker_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _morning_fixtures(tmp_path, html="<html>no markers here</html>")
    assert cr.main(["--profile", "morning"]) == 1


def test_morning_forbidden_pattern_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    bad = _healthy_html().replace("</html>", "/tmp/pytest-of-runner</html>")
    _morning_fixtures(tmp_path, html=bad)
    assert cr.main(["--profile", "morning"]) == 1


def test_morning_market_stress_halt_passes(monkeypatch, tmp_path):
    # status=FAIL, errors=[], system_halted=True is the healthy market-stress HALT.
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _morning_fixtures(tmp_path, run={"status": "FAIL", "outcome": "HALT", "errors": [], "system_halted": True})
    assert cr.main(["--profile", "morning"]) == 0


# --- hourly (flagless) bit-identical regression -----------------------------

def test_flagless_defaults_to_hourly_artifact_set():
    # The default (no-arg) contract must be the frozen hourly set.
    assert set(cr.JSON_REQUIRED_FIELDS) == {
        Path("logs/latest_hourly_payload.json"),
        cr.HOURLY_RUN_PATH,
    }
    assert cr._DEFAULT_RUN_HEALTH_PATHS == frozenset({cr.HOURLY_RUN_PATH})
    assert cr.HTML_ARTIFACTS == (Path("ui/dashboard.html"), Path("ui/index.html"))


def test_flagless_hourly_healthy_passes(monkeypatch, tmp_path):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _hourly_fixtures(tmp_path)
    assert cr.main([]) == 0


def test_flagless_hourly_unhealthy_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _hourly_fixtures(tmp_path, run={"status": "FAIL", "outcome": "NO_TRADE", "errors": ["x"], "system_halted": False})
    assert cr.main([]) == 1


def test_flagless_does_not_require_morning_artifact(monkeypatch, tmp_path):
    # A morning run artifact is irrelevant to the hourly (flagless) profile.
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _hourly_fixtures(tmp_path)
    # no logs/latest_run.json present
    assert cr.main([]) == 0


def test_morning_profile_ignores_hourly_artifacts(monkeypatch, tmp_path):
    # The morning profile must not require the hourly payload/run artifacts.
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _morning_fixtures(tmp_path)
    # no hourly artifacts present
    assert cr.main(["--profile", "morning"]) == 0
