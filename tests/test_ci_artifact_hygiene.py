"""PRD-129 — CI artifact hygiene regression tests.

These tests guard the interaction between two prior PRDs:

* PRD-020 — Engine health check step writes ``engine_doctor.json`` and
  ``engine_doctor.txt`` to the repo root for artifact upload.
* PRD-100-PATCH — ``tools/ci_push_artifacts.sh`` aborts the push step if
  ``git status --short`` is non-empty before rebasing onto ``origin/main``.

If either filename is not gitignored, the workflow's Engine health check
step leaves the working tree dirty by the push guard's definition and the
pipeline's final Push step fails. This test enforces both the
pattern-coverage assertion (``git check-ignore``) and the push-guard
predicate (``git status --short`` is empty) so the regression cannot
silently return.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_ARTIFACT_FILENAMES = ("engine_doctor.json", "engine_doctor.txt")
HOURLY_REQUIRED_STAGED_ARTIFACTS = (
    "logs/audit.jsonl",
    "logs/market_map.json",
    "logs/macro_drivers_snapshot.json",
    "logs/trend_structure_snapshot.json",
    "logs/latest_run.json",
    "logs/latest_contract.json",
    "logs/latest_payload.json",
    "logs/latest_hourly_run.json",
    "logs/latest_hourly_contract.json",
    "logs/latest_hourly_payload.json",
    "ui/contract.json",
    "ui/dashboard.html",
    "ui/index.html",
)


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("filename", CI_ARTIFACT_FILENAMES)
def test_engine_doctor_artifact_is_gitignored(filename: str) -> None:
    """R1 / R3(a) — pattern-coverage assertion.

    ``git check-ignore`` MUST exit 0 for each filename CI writes to the
    repo root during the Engine health check step.
    """

    result = _run(["git", "check-ignore", "-q", filename], REPO_ROOT)
    assert result.returncode == 0, (
        f"{filename!r} is not gitignored; the Engine health check step "
        f"(PRD-020) would leave it as an untracked file and trip the "
        f"push-guard dirty-tree check in tools/ci_push_artifacts.sh "
        f"(PRD-100-PATCH). check-ignore exit={result.returncode}, "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}."
    )


def test_engine_doctor_artifacts_leave_porcelain_clean() -> None:
    """R2 / R3(b) — push-guard predicate assertion.

    Creating both engine doctor outputs at the exact repo-root paths CI
    uses MUST NOT add lines to ``git status --short`` for those paths.
    This is the predicate ``tools/ci_push_artifacts.sh`` evaluates
    immediately before ``git rebase origin/main``; any non-empty output
    aborts the push step.

    The test path-scopes the ``git status`` invocation so unrelated
    in-progress work in the developer's tree cannot mask the assertion.
    It only writes the artifacts when they are absent and removes only
    the files it created.
    """

    created: list[Path] = []
    try:
        for filename in CI_ARTIFACT_FILENAMES:
            path = REPO_ROOT / filename
            if path.exists():
                continue
            path.write_text("PRD-129 test fixture; safe to delete.\n")
            created.append(path)

        result = _run(
            ["git", "status", "--short", "--", *CI_ARTIFACT_FILENAMES],
            REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"git status failed: {result.stderr!r}"
        )
        assert result.stdout == "", (
            "git status --short produced non-empty output for engine "
            "doctor artifacts at the repo root. "
            "tools/ci_push_artifacts.sh treats any non-empty status as "
            "a dirty tree and aborts the push step. Offending output:\n"
            f"{result.stdout}"
        )
    finally:
        for path in created:
            path.unlink(missing_ok=True)


def test_hourly_workflow_stages_all_mutated_artifacts_before_push() -> None:
    """Hourly artifacts written before the push guard must be staged.

    ``tools/ci_push_artifacts.sh`` intentionally fails on any dirty tree
    before rebase. Keep this list aligned with files the hourly run mutates
    and expects to publish before invoking the push helper.
    """

    workflow = REPO_ROOT / ".github" / "workflows" / "hourly_alert.yml"
    text = workflow.read_text(encoding="utf-8")

    commit_step = text[text.index("- name: Commit hourly artifacts"):]
    push_idx = commit_step.index("- name: Push hourly artifacts")
    commit_step = commit_step[:push_idx]

    for artifact in HOURLY_REQUIRED_STAGED_ARTIFACTS:
        assert artifact in commit_step, (
            f"{artifact} is not staged by the hourly Commit hourly artifacts "
            "step before tools/ci_push_artifacts.sh runs. Any mutated but "
            "unstaged artifact leaves the tree dirty and correctly trips "
            "the push guard."
        )
