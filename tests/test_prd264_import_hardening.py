"""
PRD-264: pytest import hardening.

R1 - every pytest session prints the resolved package path.
R2 - a PYTHONPATH swap under the bare pytest binary resolves the swapped
     package, not the repo's own (red against current main by construction:
     the tests/__init__.py rootdir insertion shadows the swap today).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_RESOLVED_RE = re.compile(r"^cuttingboard resolved: (.+)$", re.MULTILINE)

# R2 is specifically about the bare `pytest` binary, not `python3 -m pytest`.
# `-m` invocation puts sys.path[0] = '' (cwd) ahead of PYTHONPATH -- a
# separate, already-documented, not-fixable-via-config limitation (this
# PRD's own SCOPE section), not what R2 tests.
_PYTEST_BIN = shutil.which("pytest")
assert _PYTEST_BIN is not None, "bare `pytest` binary not found on PATH"


def _run_pytest(*, cwd: Path, extra_env: dict[str, str] | None = None) -> str:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        [_PYTEST_BIN, "tests/test_regime.py", "-q"],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.stdout + result.stderr


def test_r1_conftest_prints_resolved_package_path():
    output = _run_pytest(cwd=REPO_ROOT)
    match = _RESOLVED_RE.search(output)
    assert match is not None, (
        "expected a 'cuttingboard resolved: <path>' line in pytest output, "
        f"got:\n{output}"
    )


def test_r2_pythonpath_swap_resolves_swapped_package(tmp_path):
    snapshot_dir = tmp_path / "prd264_probe"
    snapshot_dir.mkdir()
    archive = subprocess.run(
        ["git", "archive", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["tar", "-x", "-C", str(snapshot_dir)],
        input=archive.stdout,
        check=True,
    )

    output = _run_pytest(
        cwd=REPO_ROOT,
        extra_env={"PYTHONPATH": str(snapshot_dir)},
    )
    match = _RESOLVED_RE.search(output)
    assert match is not None, (
        f"expected a 'cuttingboard resolved: <path>' line, got:\n{output}"
    )
    resolved_path = Path(match.group(1)).resolve()
    snapshot_real = snapshot_dir.resolve()
    assert snapshot_real in resolved_path.parents or resolved_path == snapshot_real, (
        f"expected resolved package under snapshot {snapshot_real}, "
        f"got {resolved_path} (repo root is {REPO_ROOT})"
    )

    shutil.rmtree(snapshot_dir, ignore_errors=True)
