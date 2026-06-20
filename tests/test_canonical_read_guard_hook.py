"""Tests for PRD-201: canonical_read_guard.sh non-blocking re-read reminder.

The hook warns (model-visible additionalContext) when the Read tool targets a
doc already injected into the system prompt at session start (repo-root
CLAUDE.md, auto-memory MEMORY.md), and is silent + non-blocking otherwise.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = REPO_ROOT / ".claude" / "hooks" / "canonical_read_guard.sh"


def _run_hook(file_path: str, project_dir: Path = REPO_ROOT) -> tuple[int, str]:
    """Invoke the hook with a synthetic PreToolUse(Read) payload."""
    payload = json.dumps({"tool_input": {"file_path": file_path}})
    result = subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload,
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir)},
    )
    return result.returncode, result.stdout


def _additional_context(stdout: str) -> str:
    """Parse the hook's JSON stdout and return additionalContext ('' if silent)."""
    if not stdout.strip():
        return ""
    parsed = json.loads(stdout)
    hso = parsed["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "allow", "guard must never block/deny"
    return hso.get("additionalContext", "")


def test_warns_on_repo_root_claude_md() -> None:
    rc, out = _run_hook(str(REPO_ROOT / "CLAUDE.md"))
    assert rc == 0
    assert _additional_context(out), "expected a reminder for repo-root CLAUDE.md"


def test_warns_on_auto_memory_md(tmp_path: Path) -> None:
    mem = tmp_path / ".claude" / "projects" / "proj" / "memory" / "MEMORY.md"
    mem.parent.mkdir(parents=True)
    mem.write_text("# mem\n", encoding="utf-8")
    rc, out = _run_hook(str(mem))
    assert rc == 0
    assert _additional_context(out), "expected a reminder for auto-memory MEMORY.md"


def test_silent_on_code_file() -> None:
    rc, out = _run_hook(str(REPO_ROOT / "tools" / "validate_prd_registry.py"))
    assert rc == 0
    assert out.strip() == "", "code-file Read must not warn"


def test_silent_on_other_doc() -> None:
    # PROJECT_STATE.md changes mid-session and is deliberately NOT guarded.
    rc, out = _run_hook(str(REPO_ROOT / "docs" / "PROJECT_STATE.md"))
    assert rc == 0
    assert out.strip() == "", "non-injected doc Read must not warn"


def test_silent_on_unrelated_memory_md(tmp_path: Path) -> None:
    # A MEMORY.md NOT under a .claude/.../memory path must not warn.
    other = tmp_path / "MEMORY.md"
    other.write_text("# unrelated\n", encoding="utf-8")
    rc, out = _run_hook(str(other))
    assert rc == 0
    assert out.strip() == ""


def test_silent_on_dot_claude_memory_without_projects(tmp_path: Path) -> None:
    # The real auto-memory lives under .claude/projects/<slug>/memory/; a
    # .claude/memory/MEMORY.md (no projects/) is not the injected file -> silent.
    mem = tmp_path / ".claude" / "memory" / "MEMORY.md"
    mem.parent.mkdir(parents=True)
    mem.write_text("# x\n", encoding="utf-8")
    rc, out = _run_hook(str(mem))
    assert rc == 0
    assert out.strip() == ""


def test_never_blocks_on_empty_or_missing_path() -> None:
    for rc, out in (_run_hook(""), ):
        assert rc == 0
        assert out.strip() == ""
