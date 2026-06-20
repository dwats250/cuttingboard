"""Tests for scripts/prd_close.sh — the single-commit closeout helper.

Each test builds a minimal docs/ fixture tree (PRD doc + registry + PROJECT_STATE
+ prd_index) with an IN PROGRESS PRD-200, runs the script (no --commit, so it
only edits files), and asserts on the four closeout artifacts.

Covers PRD-164 R2 (registry row flipped in place), R3 (both status markers,
distinct forms), R5 (optional metacharacter-safe --next), and PRD-183 (the
"Current state / Recent ships" format: bulleted Active PRD reset, Test baseline
update in place, Recent ships row prepend, and zero WARN-skips).
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

# Mirrors the live PROJECT_STATE.md layout (PRD-183): top-level "Last updated",
# a "## Current state" bullet block (single-line Active PRD, a Proposed/next
# bullet, a "Test baseline:" bullet with the pytest cmd + commit ref), and a
# 3-column "## Recent ships" table.
PROJECT_STATE = """\
# Project state

**Last updated:** 2026-01-01 (commit abc0001)

## Current state

- **Active PRD:** PRD-200 (test PRD; LANE: STANDARD).
- **Proposed / next:** PRD-201 (later thing) — unstarted.
- **Test baseline:** 2400 passing, 1 xfailed (`python -m pytest tests -q` at `abc0001`).

**Next step:** finish PRD-200 implementation.

## Recent ships

| PRD | Title | Completed |
|-----|-------|-----------|
| PRD-199 | Prev | 2026-01-01 |
"""


def _make_tree(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    (docs / "prd_history").mkdir(parents=True)
    (docs / "prd_history" / "PRD-200.md").write_text(PRD_DOC)

    rows = [
        "| PRD-199 | abc0001 | Prev | COMPLETE | — |",
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
            {"number": 199, "title": "Prev", "status": "COMPLETE", "commit": "abc0001"},
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


# --- PRD-183: a complete closeout emits no WARN against the new format ----

def test_no_warn_skips_against_new_format(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _run(tree)
    assert res.returncode == 0, res.stderr
    assert "WARN:" not in res.stderr, res.stderr


# --- R2: registry row flipped in place -----------------------------------

def test_r2_registry_row_flipped_in_place(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _run(tree)
    assert res.returncode == 0, res.stderr
    reg = _registry(tree)
    assert "| PRD-200 | 1234abc | Test PRD | COMPLETE | [PRD-200](prd_history/PRD-200.md) |" in reg
    assert "PRD-200 | — | Test PRD | IN PROGRESS" not in reg
    assert reg.count("| PRD-200 |") == 1


# --- R3: both status markers, distinct completed forms --------------------

def test_r3_both_status_markers_flipped_distinct_forms(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    assert _run(tree).returncode == 0
    doc = _doc(tree)
    lines = doc.splitlines()
    assert "Status: COMPLETE" in lines
    assert "STATUS: COMPLETE @ 1234abc" in lines
    assert not [ln for ln in lines if re.match(r"^[Ss]tatus:", ln) and "IN PROGRESS" in ln]
    assert sum(1 for ln in lines if ln.startswith("STATUS: COMPLETE @")) == 1
    assert "Status: COMPLETE @" not in doc


# --- R4 (PRD-183): bulleted Active PRD reset; proposed note preserved -----

def test_r4_active_prd_reset_to_none_bulleted(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    assert _run(tree).returncode == 0
    state = _state(tree)
    assert re.search(r"^- \*\*Active PRD:\*\* none in progress\.\s*$", state, re.MULTILINE)
    # The just-closed PRD must not remain on the Active PRD line.
    assert not [ln for ln in state.splitlines()
                if ln.startswith("- **Active PRD:**") and "PRD-200" in ln]
    # The separate proposed-next bullet is untouched.
    assert "- **Proposed / next:** PRD-201" in state


# --- PRD-183: Test baseline updated in place, xfailed preserved -----------

def test_baseline_updated_in_place_xfailed_preserved(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _run(tree)
    assert res.returncode == 0, res.stderr
    assert "WARN: test baseline bullet not found" not in res.stderr
    state = _state(tree)
    # Whole bullet REBUILT (PRD-203): count -> 2401, commit -> 1234abc, "1 xfailed"
    # preserved, canonical "CI truth ... for `<hash>`" provenance.
    assert "- **Test baseline:** 2401 passing, 1 xfailed (CI truth on `main`; `test` job for `1234abc`)." in state
    assert "2400 passing" not in state
    assert "python -m pytest tests -q" not in state  # old prose rebuilt away
    assert "abc0001" not in state.splitlines()[2]  # Last updated line refreshed too


# --- PRD-183: soft-wrapped baseline bullet (commit ref on next line) ------

def test_baseline_wrapped_across_two_lines_is_updated(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    sp = tree / "docs" / "PROJECT_STATE.md"
    sp.write_text(sp.read_text().replace(
        "- **Test baseline:** 2400 passing, 1 xfailed (`python -m pytest tests -q` at `abc0001`).",
        "- **Test baseline:** 2400 passing, 1 xfailed (`python -m pytest tests -q` at\n  `abc0001`).",
    ))
    res = _run(tree)
    assert res.returncode == 0, res.stderr
    assert "WARN: test baseline bullet not found" not in res.stderr
    state = _state(tree)
    # Soft-wrapped bullet is matched whole and collapsed to the canonical line.
    assert "- **Test baseline:** 2401 passing, 1 xfailed (CI truth on `main`; `test` job for `1234abc`)." in state
    assert "2400 passing" not in state and "abc0001" not in state
    assert "python -m pytest tests -q" not in state


# --- PRD-183: Recent ships row prepended (3-column) -----------------------

def test_recent_ships_row_prepended(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    assert _run(tree).returncode == 0
    state = _state(tree)
    assert re.search(r"^\| PRD-200 \| Test PRD \| \d{4}-\d{2}-\d{2} \|$", state, re.MULTILINE)
    # Prepended above the prior row.
    pos_200 = state.index("| PRD-200 | Test PRD |")
    pos_199 = state.index("| PRD-199 | Prev |")
    assert pos_200 < pos_199


# --- R5: optional, metacharacter-safe --next -----------------------------

def test_r5_next_unchanged_when_omitted(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    assert _run(tree).returncode == 0
    state = _state(tree)
    assert "**Next step:** finish PRD-200 implementation." in state


def test_r5_next_set_when_supplied(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    assert _run(tree, "--next", "ship PRD-202").returncode == 0
    state = _state(tree)
    next_line = [ln for ln in state.splitlines() if ln.startswith("**Next step")]
    assert len(next_line) == 1
    assert "ship PRD-202" in next_line[0]


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
    assert index["latest_complete"] == 200
    assert index["next_prd"] == 201


# --- PRD-196 (a): fail-loud + atomic when a contracted bullet is absent ----

def test_missing_contracted_bullet_fails_loud_and_writes_nothing(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    sp = tree / "docs" / "PROJECT_STATE.md"
    # Drift the Active PRD bullet so its bold label can no longer be matched.
    sp.write_text(sp.read_text().replace("- **Active PRD:**", "- **Current PRD:**"))

    # Snapshot every closeout artifact before the run.
    before = {p: p.read_text() for p in (
        sp,
        tree / "docs" / "PRD_REGISTRY.md",
        tree / "docs" / "prd_history" / "PRD-200.md",
        tree / "docs" / "prd_index.json",
    )}

    res = _run(tree)
    assert res.returncode != 0, "missing contracted bullet must exit non-zero"
    assert "Active PRD" in res.stderr, res.stderr
    # Atomicity: a contracted-bullet failure leaves ALL four artifacts untouched.
    for p, original in before.items():
        assert p.read_text() == original, f"{p.name} was modified despite abort"


# --- PRD-196 (a): count still updates when the commit-ref prose drifts ------

def test_baseline_rebuilt_when_commit_ref_prose_drifts(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    sp = tree / "docs" / "PROJECT_STATE.md"
    # A drifted bullet ("on `main`", no "at `<hash>`"). PRD-203: the whole bullet
    # is rebuilt, so the count AND commit refresh and the old prose is gone.
    sp.write_text(sp.read_text().replace(
        "- **Test baseline:** 2400 passing, 1 xfailed (`python -m pytest tests -q` at `abc0001`).",
        "- **Test baseline:** 2400 passing, 1 xfailed (`python -m pytest tests -q` on `main`).",
    ))
    res = _run(tree)
    assert res.returncode == 0, res.stderr
    state = _state(tree)
    assert "- **Test baseline:** 2401 passing, 1 xfailed (CI truth on `main`; `test` job for `1234abc`)." in state
    assert "2400 passing" not in state
    assert "python -m pytest tests -q" not in state  # drifted prose rebuilt away


# --- PRD-203: stale multi-sentence provenance is fully rebuilt away --------

def test_baseline_rebuild_drops_stale_run_and_commit_provenance(tmp_path: Path) -> None:
    # The exact alignment-cadence-#4 drift: a multi-sentence "CI truth ... run <id>
    # for `<hash>`" bullet whose count had been bumped but provenance left stale.
    # The whole bullet must be rebuilt: new count + new commit, and the old run id,
    # old commit, and trailing sentences must NOT survive (PRD-198 invariant 4).
    tree = _make_tree(tmp_path)
    sp = tree / "docs" / "PROJECT_STATE.md"
    sp.write_text(sp.read_text().replace(
        "- **Test baseline:** 2400 passing, 1 xfailed (`python -m pytest tests -q` at `abc0001`).",
        "- **Test baseline:** 2400 passing, 1 xfailed (CI truth on `main` -- `test` job "
        "of run 27732171939 for `470aa2b`. In this sandbox the same suite reports 2390 "
        "passing because signing tests fail; the recorded baseline is the CI count.).",
    ))
    res = _run(tree)
    assert res.returncode == 0, res.stderr
    state = _state(tree)
    assert "- **Test baseline:** 2401 passing, 1 xfailed (CI truth on `main`; `test` job for `1234abc`)." in state
    for stale in ("470aa2b", "27732171939", "In this sandbox", "2400 passing", "2390"):
        assert stale not in state, f"stale token survived rebuild: {stale}"


# --- PRD-203: optional --ci-run is recorded; absent -> no run clause -------

def test_baseline_ci_run_recorded_when_supplied(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _run(tree, "--ci-run", "27865518359")
    assert res.returncode == 0, res.stderr
    assert ("- **Test baseline:** 2401 passing, 1 xfailed "
            "(CI truth on `main`; `test` job for `1234abc`, run 27865518359).") in _state(tree)


def test_baseline_no_run_clause_when_ci_run_omitted(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    assert _run(tree).returncode == 0
    baseline_line = next(ln for ln in _state(tree).splitlines() if "**Test baseline:**" in ln)
    assert ", run " not in baseline_line


def test_baseline_bullet_absent_fails_loud_and_writes_nothing(tmp_path: Path) -> None:
    # PRD-203 R3: a missing Test-baseline bullet aborts with no writes (atomicity).
    tree = _make_tree(tmp_path)
    sp = tree / "docs" / "PROJECT_STATE.md"
    sp.write_text(sp.read_text().replace("- **Test baseline:**", "- **Coverage note:**"))
    before = {p: p.read_text() for p in (
        sp,
        tree / "docs" / "PRD_REGISTRY.md",
        tree / "docs" / "prd_history" / "PRD-200.md",
        tree / "docs" / "prd_index.json",
    )}
    res = _run(tree)
    assert res.returncode != 0, "missing Test-baseline bullet must exit non-zero"
    assert "Test baseline" in res.stderr, res.stderr
    for p, original in before.items():
        assert p.read_text() == original, f"{p.name} modified despite abort"


# --- PRD-196 (b): baseline sourced from an injected CI summary -------------

def test_ci_summary_overrides_passed_in_tests(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    summary = tree / "ci_summary.txt"
    # A realistic pytest -q tail: the CI `test`-job count is the source of truth.
    summary.write_text("=== short test summary info ===\n2773 passed, 1 xfailed in 41.2s\n")
    # _run still passes --tests 2401 (the sandbox-local count); --ci-summary wins.
    res = _run(tree, "--ci-summary", str(summary))
    assert res.returncode == 0, res.stderr
    state = _state(tree)
    assert "2773 passing" in state, "baseline must come from the CI summary count"
    assert "2401 passing" not in state, "sandbox --tests count must not be recorded"


def test_ci_summary_thousands_separator_parsed(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    summary = tree / "ci_summary.txt"
    summary.write_text("12,773 passed, 1 xfailed in 99.9s\n")
    assert _run(tree, "--ci-summary", str(summary)).returncode == 0
    assert "12773 passing" in _state(tree)


def test_ci_summary_missing_file_fails_loud(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _run(tree, "--ci-summary", str(tree / "nope.txt"))
    assert res.returncode != 0
    assert "not found" in res.stderr


def test_ci_summary_unparseable_fails_loud(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    summary = tree / "ci_summary.txt"
    summary.write_text("the test job crashed before pytest produced a summary\n")
    res = _run(tree, "--ci-summary", str(summary))
    assert res.returncode != 0
    assert "no pytest pass count" in res.stderr


def test_tests_or_ci_summary_required(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = subprocess.run(
        [
            "bash", str(SCRIPT),
            "--prd", "200", "--hash", "1234abc", "--title", "Test PRD",
            "--added", "1", "--summary", "did the new thing",
        ],
        cwd=tree, capture_output=True, text=True,
    )
    assert res.returncode != 0
    assert "missing --tests or --ci-summary" in res.stderr
