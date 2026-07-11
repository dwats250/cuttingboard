"""PRD-159: tests for scripts/prd_open.sh — the Stage-0 PRD scaffolder.

Each test builds a minimal docs/ fixture tree in a temp dir, runs the
script with cwd set to that tree, and asserts on the three Stage-0
artifacts (PRD-NNN.md, PRD_REGISTRY.md, prd_index.json).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "prd_open.sh"
VALIDATOR = REPO / "tools" / "validate_prd_registry.py"

REGISTRY_HEADER = (
    "| PRD | Commit(s) | Title | Status | File |\n"
    "|-----|-----------|-------|--------|------|\n"
)


def _make_tree(
    tmp_path: Path,
    extra_entries: list[dict] | None = None,
    audit_reports: bool = False,
) -> Path:
    """Create a validator-valid docs/ tree: complete PRDs 056-058, plus any
    extra entries. Returns the tree root (the dir to run the script from).

    When ``audit_reports`` is set, a trailing ``## Audit Reports`` table with a
    ``| PRD-016 |`` row is appended after the main table — reproducing the real
    registry shape that PRD-164 R1 fixes (the row must land in the MAIN table,
    not after the Audit Reports heading).
    """
    docs = tmp_path / "docs"
    (docs / "prd_history").mkdir(parents=True)

    base = [
        {"number": 56, "title": "Base 56", "status": "COMPLETE", "commit": "aaaaaaa"},
        {"number": 57, "title": "Base 57", "status": "COMPLETE", "commit": "bbbbbbb"},
        {"number": 58, "title": "Base 58", "status": "COMPLETE", "commit": "ccccccc"},
    ]
    entries = base + (extra_entries or [])
    entries.sort(key=lambda e: e["number"])

    index = {
        "tracking_start": 56,
        "latest_complete": 58,
        "next_prd": 59,
        "entries": entries,
    }
    (docs / "prd_index.json").write_text(json.dumps(index, indent=2) + "\n")

    rows = []
    for e in entries:
        commit_cell = e["commit"] if e["commit"] else "—"
        # File "—" skips the history-doc existence check in the validator.
        rows.append(
            f"| PRD-{e['number']:03d} | {commit_cell} | {e['title']} | {e['status']} | — |"
        )
    registry = "# PRD Registry\n\n" + REGISTRY_HEADER + "\n".join(rows) + "\n"
    if audit_reports:
        registry += (
            "\n## Audit Reports\n\n"
            "| PRD | File |\n"
            "|-----|------|\n"
            "| PRD-016 | [docs/prd_history/AUDIT_PRD016.md](prd_history/AUDIT_PRD016.md) |\n"
        )
    (docs / "PRD_REGISTRY.md").write_text(registry)
    return tmp_path


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _open_200(cwd: Path, *extra: str) -> subprocess.CompletedProcess:
    return _run(
        cwd, "--prd", "200", "--title", "Test PRD", "--lane", "MICRO",
        "--class", "GOVERNANCE", *extra,
    )


def _load_index(tree: Path) -> dict:
    return json.loads((tree / "docs" / "prd_index.json").read_text())


def test_scaffolds_prd_file(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _open_200(tree)
    assert res.returncode == 0, res.stderr
    prd = (tree / "docs" / "prd_history" / "PRD-200.md").read_text()
    # PRD-232: the scaffold must match docs/PRD_TEMPLATE.md, not a third
    # divergent skeleton — template header shape, section order, and the
    # A/M/D FILES format that the scope-lock-precommit skill parses
    # (PRD-254: protect_files.sh no longer parses FILES at all).
    assert prd.startswith("PRD-200 — Test PRD")
    assert "\nLANE\nMICRO\n" in prd
    assert "\nCLASS\nGOVERNANCE\n" in prd
    sections = ["GOAL", "SCOPE", "OUT OF SCOPE", "FILES", "REQUIREMENTS",
                "DATA FLOW", "FAIL CONDITIONS", "VALIDATION"]
    positions = [prd.find(f"\n{s}\n") for s in sections]
    assert all(p >= 0 for p in positions), f"missing sections: {[s for s, p in zip(sections, positions) if p < 0]}"
    assert positions == sorted(positions), "template section order violated"
    files_body = prd.split("\nFILES\n", 1)[1].split("\n\n", 1)[0]
    assert re.search(r"^[AMD] \S", files_body, flags=re.MULTILINE), (
        "FILES stub must use the template's A/M/D format"
    )
    assert "STATUS: IN PROGRESS" in prd


def test_inserts_registry_row(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _open_200(tree)
    assert res.returncode == 0, res.stderr
    registry = (tree / "docs" / "PRD_REGISTRY.md").read_text()
    assert (
        "| PRD-200 | — | Test PRD | IN PROGRESS | [PRD-200](prd_history/PRD-200.md) |"
        in registry
    )


def test_inserts_index_entry_unchanged_counters(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _open_200(tree)
    assert res.returncode == 0, res.stderr
    index = _load_index(tree)
    entry = next(e for e in index["entries"] if e["number"] == 200)
    assert entry == {
        "number": 200, "title": "Test PRD", "status": "IN PROGRESS", "commit": None,
    }
    # Opening a PRD must NOT advance completion counters.
    assert index["latest_complete"] == 58
    assert index["next_prd"] == 59


def test_index_stays_sorted_on_mid_insertion(tmp_path: Path) -> None:
    # A higher-numbered entry already exists; opening 200 must slot before it.
    tree = _make_tree(
        tmp_path,
        extra_entries=[
            {"number": 300, "title": "Future", "status": "IN PROGRESS", "commit": None}
        ],
    )
    res = _open_200(tree)
    assert res.returncode == 0, res.stderr
    numbers = [e["number"] for e in _load_index(tree)["entries"]]
    assert numbers == sorted(numbers)
    assert numbers.index(200) < numbers.index(300)


def test_title_with_regex_metacharacter_does_not_crash(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _run(
        tree, "--prd", "200", "--title", r"Fix \d bug", "--lane", "MICRO",
        "--class", "CONTRACT",
    )
    assert res.returncode == 0, res.stderr
    registry = (tree / "docs" / "PRD_REGISTRY.md").read_text()
    assert r"Fix \d bug" in registry
    entry = next(e for e in _load_index(tree)["entries"] if e["number"] == 200)
    assert entry["title"] == r"Fix \d bug"


def test_refuses_existing_prd_file(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    existing = tree / "docs" / "prd_history" / "PRD-200.md"
    existing.write_text("# PRD-200\noriginal content\n")
    registry_before = (tree / "docs" / "PRD_REGISTRY.md").read_text()
    res = _open_200(tree)
    assert res.returncode == 1
    # Existing PRD file is left untouched, registry unchanged.
    assert existing.read_text() == "# PRD-200\noriginal content\n"
    assert (tree / "docs" / "PRD_REGISTRY.md").read_text() == registry_before


def test_missing_required_arg_exits_2(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _run(tree, "--prd", "200", "--lane", "MICRO", "--class", "GOVERNANCE")
    assert res.returncode == 2


def test_resulting_tree_passes_validator(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    res = _open_200(tree)
    assert res.returncode == 0, res.stderr
    val = subprocess.run(
        [sys.executable, str(VALIDATOR), str(tree)],
        capture_output=True, text=True,
    )
    assert val.returncode == 0, val.stdout + val.stderr


def test_inserts_row_into_main_table_not_audit_reports(tmp_path: Path) -> None:
    # PRD-164 R1: with a trailing "## Audit Reports" table present, the new
    # IN PROGRESS row must land in the MAIN table (contiguous after PRD-058),
    # NOT after the Audit Reports heading. The pre-fix scan picked the last
    # "| PRD-016 |" row inside Audit Reports and inserted there.
    tree = _make_tree(tmp_path, audit_reports=True)
    res = _open_200(tree)
    assert res.returncode == 0, res.stderr
    registry = (tree / "docs" / "PRD_REGISTRY.md").read_text()

    row_idx = registry.index("| PRD-200 |")
    audit_idx = registry.index("## Audit Reports")
    main_last_idx = registry.index("| PRD-058 |")
    audit016_idx = registry.index("| PRD-016 |")

    # The new row is inside the main table: after PRD-058, before the heading.
    assert main_last_idx < row_idx < audit_idx, registry
    # And specifically not after the Audit Reports PRD-016 row.
    assert row_idx < audit016_idx, registry


def test_main_table_insertion_with_no_audit_table_unchanged(tmp_path: Path) -> None:
    # PRD-164 R1 regression guard: when there is NO Audit Reports table, the row
    # still appends after the last main-table row exactly as before.
    tree = _make_tree(tmp_path)
    res = _open_200(tree)
    assert res.returncode == 0, res.stderr
    registry = (tree / "docs" / "PRD_REGISTRY.md").read_text()
    assert (
        "| PRD-200 | — | Test PRD | IN PROGRESS | [PRD-200](prd_history/PRD-200.md) |"
        in registry
    )
    assert registry.index("| PRD-058 |") < registry.index("| PRD-200 |")


def test_commit_flag_creates_stage0_commit(tmp_path: Path) -> None:
    tree = _make_tree(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tree, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tree, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tree, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tree, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tree, check=True)
    res = _open_200(tree, "--commit")
    assert res.returncode == 0, res.stderr
    subject = subprocess.run(
        ["git", "log", "-1", "--format=%s"], cwd=tree, capture_output=True, text=True
    ).stdout.strip()
    assert subject == "PRD-200: stage 0"
