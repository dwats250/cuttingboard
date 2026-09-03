"""tools/review_prep.py: deterministic review evidence, facts only."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import review_prep  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit(repo: Path, msg: str) -> str:
    _git(repo, "add", "-A")
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-q",
            "-m",
            msg,
        ],
        check=True,
    )
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture()
def repo(tmp_path: Path) -> tuple[Path, str, str]:
    r = tmp_path
    _git(r, "init", "-q")
    (r / "cuttingboard").mkdir()
    (r / "tests" / "data").mkdir(parents=True)
    (r / "docs").mkdir()
    (r / "cuttingboard" / "mod.py").write_text(
        "def keep():\n    return 1\n\n\ndef gone():\n    return 2\n\n\ndef tweak(x):\n    return x\n",
        encoding="utf-8",
    )
    (r / "tests" / "test_mod.py").write_text(
        "from cuttingboard.mod import keep\n\n\ndef test_keep():\n    assert keep() == 1\n",
        encoding="utf-8",
    )
    (r / "tests" / "data" / "mod_golden.txt").write_text("golden\n", encoding="utf-8")
    (r / "docs" / "NOTES.md").write_text("# notes\n", encoding="utf-8")
    base = _commit(r, "base")
    (r / "cuttingboard" / "mod.py").write_text(
        "def keep():\n    return 1\n\n\ndef tweak(x):\n    return x + 1\n\n\nclass Fresh:\n    def run(self):\n        return 0\n",
        encoding="utf-8",
    )
    (r / "tests" / "test_mod.py").write_text(
        "from cuttingboard.mod import keep, Fresh\n\n\ndef test_keep():\n    assert keep() == 1\n\n\ndef test_fresh():\n    assert Fresh().run() == 0\n",
        encoding="utf-8",
    )
    (r / "tests" / "data" / "mod_golden.txt").write_text(
        "golden v2\n", encoding="utf-8"
    )
    (r / "docs" / "NOTES.md").write_text(
        "# notes\nPRD-330 R7 supersedes PRD-102 R5 per DECISIONS and Gate A.  \nSUPERSEDED IN PART by PRD-330.\n",
        encoding="utf-8",
    )
    (r / ".github").mkdir()
    (r / ".github" / "wf.yml").write_text("on: push\n", encoding="utf-8")
    head = _commit(r, "head")
    return r, base, head


def test_classify_five_classes() -> None:
    assert review_prep.classify("cuttingboard/delivery/setup_chart.py") == "production"
    assert review_prep.classify("tests/test_setup_chart.py") == "test"
    assert (
        review_prep.classify("tests/data/setup_chart_legacy_oracle.json")
        == "fixture/golden"
    )
    assert review_prep.classify("docs/prd_history/PRD-330.md") == "docs/governance"
    assert (
        review_prep.classify(".github/workflows/hourly_alert.yml")
        == "workflow/infrastructure"
    )
    assert review_prep.classify("tools/review_prep.py") == "workflow/infrastructure"
    assert review_prep.classify("ui/dashboard.html") == "fixture/golden"
    assert review_prep.classify("LICENSE") == "other"


def test_report_facts(repo: tuple[Path, str, str]) -> None:
    r, base, head = repo
    out = review_prep.build_report(r, "HEAD~1", "HEAD", [], with_diff=False)
    assert f"- base: `{base}`" in out and f"- head: `{head}`" in out
    # inventory + class
    assert "| production | `cuttingboard/mod.py` | M |" in out
    assert "| fixture/golden | `tests/data/mod_golden.txt` | M |" in out
    assert "| workflow/infrastructure | `.github/wf.yml` | A |" in out
    # blob identity: added file has no base blob
    assert "| ABSENT |" in out
    # symbols
    assert "- added: `Fresh (L9)`, `Fresh.run (L10)`" in out
    assert "- removed: `gone (base L5)`" in out
    assert "- modified: `tweak (L5)`" in out
    # test references: module + whole-word symbol
    assert "- module references: `tests/test_mod.py`" in out
    assert "- `Fresh`: `tests/test_mod.py`" in out
    assert "- `tweak`: NOT FOUND" in out
    # authority + supersession
    assert (
        "`docs/NOTES.md`: DECISIONS x1, Gate A x1, PRD-102 R5 x1, PRD-330 x1, PRD-330 R7 x1"
        in out
    )
    assert "SUPERSEDED IN PART by PRD-330." in out
    # git diff --check catches the trailing whitespace in NOTES.md
    assert "- exit code: 2 (whitespace issues)" in out
    assert "docs/NOTES.md:2: trailing whitespace" in out


def test_report_is_deterministic_and_pointer_only(repo: tuple[Path, str, str]) -> None:
    r, _, _ = repo
    a = review_prep.build_report(r, "HEAD~1", "HEAD", [], with_diff=False)
    b = review_prep.build_report(r, "HEAD~1", "HEAD", [], with_diff=False)
    assert a == b
    assert "```diff" not in a and "- `@@ " in a
    with_diff = review_prep.build_report(r, "HEAD~1", "HEAD", [], with_diff=True)
    assert "```diff" in with_diff and "+    return x + 1" in with_diff


def test_path_filter_and_cli(repo: tuple[Path, str, str]) -> None:
    r, _, _ = repo
    out = review_prep.build_report(r, "HEAD~1", "HEAD", ["docs/"], with_diff=False)
    assert "`docs/NOTES.md`" in out and "cuttingboard/mod.py" not in out
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "review_prep.py"),
            "--repo",
            str(r),
            "--base",
            "HEAD~1",
            "--head",
            "HEAD",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0 and proc.stdout.startswith("# REVIEW PREP EVIDENCE")
    bad = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "review_prep.py"),
            "--repo",
            str(r),
            "--base",
            "nope",
            "--head",
            "HEAD",
        ],
        capture_output=True,
        text=True,
    )
    assert bad.returncode != 0
