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
