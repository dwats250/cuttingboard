"""PRD-164: tests for scripts/prd_close.sh — the single-commit closeout helper.

Each test builds a minimal docs/ fixture tree (PRD doc + registry + PROJECT_STATE
+ prd_index) with an IN PROGRESS PRD-200, runs the script (no --commit, so it
only edits files), and asserts on the four closeout artifacts. Covers PRD-164
R2 (registry row flipped in place), R3 (both status markers, distinct forms),
R4 (Active PRD reset), R5 (optional metacharacter-safe --next).
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "prd_close.sh"

REGISTRY_HEADER = (
    "| PRD | Commit(s) | Title | Status | File |\n"
    "|-----|-----------|-------|--------|------|\n"
)

PRD_DOC = """\
# PRD-200: Test PRD

Lane: STANDARD / INFRA
Status: IN PROGRESS
Author: T
Filed: 2026-01-01

## GOAL

Do the thing.

STATUS: IN PROGRESS
"""

PROJECT_STATE = """\
# PROJECT_STATE.md

## Current State

**Last updated:** 2026-01-01
**Last completed PRD:** PRD-199 - Prev (commit zzzzzzz)
**Test baseline:** 2400 passing, 1 xfailed.
- **2400 passing** (as of 2026-01-01; PRD-199 added 5 tests)
**Last work completed:** 2026-01-01 — PRD-199: did the prior thing.

**Active PRD:** PRD-200. Running completion log that should be reset.

**Next step (some label):** finish PRD-200 implementation.

## Recent PRD history

| PRD | Title | Status | Completed |
|-----|-------|--------|-----------|
| PRD-199 | Prev | COMPLETE | 2026-01-01 |
"""


def _make_tree(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    (docs / "prd_history").mkdir(parents=True)
    (docs / "prd_history" / "PRD-200.md").write_text(PRD_DOC)

    rows = [
        "| PRD-199 | zzzzzzz | Prev | COMPLETE | — |",
        "| PRD-200 | — | Test PRD | IN PROGRESS | [PRD-200](prd_history/PRD-200.md) |",
    ]
    (docs / "PRD_REGISTRY.md").write_text(
        "# PRD Registry\n\n" + REGISTRY_HEADER + "\n".join(rows) + "\n"
    )
    (docs / "PROJECT_STATE.md").write_text(PROJECT_STATE)

    index = {
        "tracking_start": 56,
        "latest_complete": 199,
        "next_prd": 200,
        "entries": [
            {"number": 199, "title": "Prev", "status": "COMPLETE", "commit": "zzzzzzz"},
            {"number": 200, "title": "Test PRD", "status": "IN PROGRESS", "commit": None},
        ],
    }
    (docs / "prd_index.json").write_text(json.dumps(index, indent=2) + "\n")
    return tmp_path


def _run(cwd: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "bash", str(SCRIPT),
            "--prd", "200", "--hash", "1234abc", "--title", "Test PRD",
            "--tests", "2401", "--added", "1", "--summary", "did the new thing",
            *extra,
        ],
        cwd=cwd, capture_output=True, text=True,
    )


def _registry(tree: Path) -> str:
    return (tree / "docs" / "PRD_REGISTRY.md").read_text()


def _doc(tree: Path) -> str:
    return (tree / "docs" / "prd_history" / "PRD-200.md").read_text()


def _state(tree: Path) -> str:
    return (tree / "docs" / "PROJECT_STATE.md").read_text()


# --- R2: registry row flipped in place -----------------------------------

def test_r2_registry_row_flipped_in_place(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _run(tree)
    assert res.returncode == 0, res.stderr
    reg = _registry(tree)
    assert "| PRD-200 | 1234abc | Test PRD | COMPLETE | [PRD-200](prd_history/PRD-200.md) |" in reg
    # No IN PROGRESS remains for PRD-200, and exactly one PRD-200 row exists.
    assert "PRD-200 | — | Test PRD | IN PROGRESS" not in reg
    assert reg.count("| PRD-200 |") == 1


# --- R3: both status markers, distinct completed forms --------------------

def test_r3_both_status_markers_flipped_distinct_forms(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    assert _run(tree).returncode == 0
    doc = _doc(tree)
    lines = doc.splitlines()
    # Header is exactly "Status: COMPLETE" (no hash).
    assert "Status: COMPLETE" in lines
    # Trailing marker is exactly "STATUS: COMPLETE @ <hash>".
    assert "STATUS: COMPLETE @ 1234abc" in lines
    # No status-anchored line still says IN PROGRESS.
    assert not [ln for ln in lines if re.match(r"^[Ss]tatus:", ln) and "IN PROGRESS" in ln]
    # Exactly one trailing all-caps marker.
    assert sum(1 for ln in lines if ln.startswith("STATUS: COMPLETE @")) == 1
    # Header not corrupted into the trailing form.
    assert "Status: COMPLETE @" not in doc


# --- R4: Active PRD reset -------------------------------------------------

def test_r4_active_prd_reset_to_none(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    assert _run(tree).returncode == 0
    state = _state(tree)
    assert re.search(r"^\*\*Active PRD:\*\* none\s*$", state, re.MULTILINE)
    assert "**Active PRD:** PRD-200" not in state


# --- R5: optional, metacharacter-safe --next -----------------------------

def test_r5_next_unchanged_when_omitted(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    assert _run(tree).returncode == 0
    state = _state(tree)
    assert "**Next step (some label):** finish PRD-200 implementation." in state


def test_r5_next_set_when_supplied(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    assert _run(tree, "--next", "ship PRD-201").returncode == 0
    state = _state(tree)
    next_line = [ln for ln in state.splitlines() if ln.startswith("**Next step")]
    assert len(next_line) == 1
    assert "ship PRD-201" in next_line[0]


def test_r5_next_metacharacter_safe(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _run(tree, "--next", r"do thing matching PRD-\d+ pattern")
    assert res.returncode == 0, res.stderr
    state = _state(tree)
    assert r"do thing matching PRD-\d+ pattern" in state


# --- index + cross-artifact agreement ------------------------------------

def test_index_entry_completed(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    assert _run(tree).returncode == 0
    index = json.loads((tree / "docs" / "prd_index.json").read_text())
    entry = next(e for e in index["entries"] if e["number"] == 200)
    assert entry["status"] == "COMPLETE"
    assert entry["commit"] == "1234abc"


# --- PRD-172: baseline bullet in the "N passing, M xfailed" form updates ---

def test_baseline_bullet_with_xfailed_suffix_is_updated(tmp_path: Path) -> None:
    # The default fixture bullet is already normalized ("- **2400 passing**");
    # rewrite it to the real-world "- **2400 passing, 1 xfailed**" form, which
    # the pre-PRD-172 regex (passing\*\*) failed to match.
    tree = _make_tree(tmp_path)
    state_path = tree / "docs" / "PROJECT_STATE.md"
    state_path.write_text(
        state_path.read_text().replace(
            "- **2400 passing** (as of 2026-01-01; PRD-199 added 5 tests)",
            "- **2400 passing, 1 xfailed** (as of 2026-01-01; PRD-199 added 5 tests)",
        )
    )
    res = _run(tree)
    assert res.returncode == 0, res.stderr
    assert "WARN: test baseline bullet not found" not in res.stderr
    state = _state(tree)
    # --tests 2401 from _run(); bullet normalized to the new count, suffix gone.
    # (Scope the negative check to the bullet form — the separate inline
    # "**Test baseline:** 2400 passing, 1 xfailed." line is intentionally
    # left untouched by the script.)
    assert "- **2401 passing** (as of" in state
    assert "- **2400 passing, 1 xfailed**" not in state
