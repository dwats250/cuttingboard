"""Tests for PRD-108: prd_eval.sh registry-gap exclusion of review/adjudication artifacts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = REPO_ROOT / ".claude" / "hooks" / "prd_eval.sh"


def _run_hook(workdir: Path, prompt: str) -> str:
    """Invoke prd_eval.sh in `workdir` with a synthetic UserPromptSubmit payload.

    Returns the additionalContext string emitted by the hook (or "").
    """
    payload = json.dumps({"prompt": prompt})
    result = subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload,
        cwd=str(workdir),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"hook exited {result.returncode}: stderr={result.stderr}"
    if not result.stdout.strip():
        return ""
    parsed = json.loads(result.stdout)
    return parsed["hookSpecificOutput"]["additionalContext"]


def _make_workspace(tmp_path: Path, prd_files: list[str], registry_rows: list[str]) -> Path:
    """Build a tmp repo layout with docs/PRD_REGISTRY.md and docs/prd_history/."""
    docs = tmp_path / "docs"
    history = docs / "prd_history"
    history.mkdir(parents=True)
    for name in prd_files:
        (history / name).write_text("# stub\n", encoding="utf-8")
    rows = "\n".join(f"| {r} |" for r in registry_rows)
    (docs / "PRD_REGISTRY.md").write_text(
        "# PRD Registry\n\n| PRD | Commit | Title | Status | File |\n|-----|--------|-------|--------|------|\n"
        + rows
        + "\n",
        encoding="utf-8",
    )
    return tmp_path


def test_review_artifact_does_not_trigger_gap(tmp_path: Path):
    """R1: PRD-999.review.claude.md with no registry row must NOT produce GAP output."""
    ws = _make_workspace(
        tmp_path,
        prd_files=["PRD-999.review.claude.md"],
        registry_rows=[],
    )
    ctx = _run_hook(ws, "PRD-999 status check")
    assert "REGISTRY GAP" not in ctx
    assert "PRD-999.review.claude.md" not in ctx


def test_adjudication_artifact_does_not_trigger_gap(tmp_path: Path):
    """R2: PRD-999.adjudication.md with no registry row must NOT produce GAP output."""
    ws = _make_workspace(
        tmp_path,
        prd_files=["PRD-999.adjudication.md"],
        registry_rows=[],
    )
    ctx = _run_hook(ws, "PRD-999 status check")
    assert "REGISTRY GAP" not in ctx
    assert "PRD-999.adjudication.md" not in ctx


def test_codex_prompt_artifact_does_not_trigger_gap(tmp_path: Path):
    """R2b: PRD-999.codex_prompt.md is a non-PRD sidecar; must NOT produce GAP output."""
    ws = _make_workspace(
        tmp_path,
        prd_files=["PRD-999.codex_prompt.md"],
        registry_rows=[],
    )
    ctx = _run_hook(ws, "PRD-999 status check")
    assert "REGISTRY GAP" not in ctx
    assert "PRD-999.codex_prompt.md" not in ctx


def test_real_unregistered_prd_does_trigger_gap(tmp_path: Path):
    """R3: a real PRD-NNN.md with no registry row MUST produce GAP output naming it."""
    ws = _make_workspace(
        tmp_path,
        prd_files=["PRD-999.md"],
        registry_rows=[],
    )
    ctx = _run_hook(ws, "PRD-999 status check")
    assert "REGISTRY GAP" in ctx
    assert "PRD-999.md" in ctx


def test_patch_variant_still_detected_when_unregistered(tmp_path: Path):
    """R4: PATCH/cleanup variants are still detected when unregistered."""
    ws = _make_workspace(
        tmp_path,
        prd_files=["PRD-999-PATCH.md"],
        registry_rows=[],
    )
    ctx = _run_hook(ws, "PRD-999 status check")
    assert "REGISTRY GAP" in ctx
    assert "PRD-999-PATCH.md" in ctx


def test_registered_prd_does_not_trigger_gap(tmp_path: Path):
    """A registered PRD must not be flagged."""
    ws = _make_workspace(
        tmp_path,
        prd_files=["PRD-999.md"],
        registry_rows=["PRD-999 | abc1234 | Title | COMPLETE | link"],
    )
    ctx = _run_hook(ws, "PRD-999 status check")
    assert "REGISTRY GAP" not in ctx


def test_mixed_review_and_real_prd(tmp_path: Path):
    """Review/adjudication/codex_prompt sidecars suppressed; real un-registered PRD still flagged."""
    ws = _make_workspace(
        tmp_path,
        prd_files=[
            "PRD-998.review.claude.md",
            "PRD-998.review.codex.md",
            "PRD-998.adjudication.md",
            "PRD-998.codex_prompt.md",
            "PRD-999.md",
        ],
        registry_rows=[],
    )
    ctx = _run_hook(ws, "PRD-999 status check")
    assert "REGISTRY GAP" in ctx
    assert "PRD-999.md" in ctx
    assert "PRD-998.review.claude.md" not in ctx
    assert "PRD-998.review.codex.md" not in ctx
    assert "PRD-998.adjudication.md" not in ctx
    assert "PRD-998.codex_prompt.md" not in ctx


def test_uses_tmp_directory_not_live_registry(tmp_path: Path):
    """Sanity: tmp registry isolation works (live registry not consulted)."""
    ws = _make_workspace(
        tmp_path,
        prd_files=["PRD-997.md"],
        registry_rows=[],
    )
    # The live registry contains PRD-104 / PRD-105 review files; this run must not see them.
    ctx = _run_hook(ws, "PRD-997 status check")
    assert "PRD-104" not in ctx
    assert "PRD-105" not in ctx
    assert "PRD-997.md" in ctx
