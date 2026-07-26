"""PRD-273 — lint-baseline guards.

The lint contract used to be "whatever the installed ruff defaults to":
pyproject.toml declared ``ruff>=0.4.0`` (unpinned) with no ruff config at all,
so ruff 0.16.0's broadened default rule set turned CI red on untouched code.
PRD-273 pins ruff to an exact version and declares the historical selection
explicitly. These tests hold that repair in place.

Discriminating, not exhaustive. They prove: exactly one exact ruff pin, the
exact historical select set, that ruff resolves the ROOT pyproject config, and
that ``ruff check cuttingboard/ tests/`` (the CI command) still passes. They do
NOT sweep ruff versions, firewall nested configs, or assert an unconfigured run
fails — under the pinned ruff the defaults happen to coincide with the declared
set (which is exactly why the pin, not the coincidence, is load-bearing).
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
EXPECTED_SELECT = ["E4", "E7", "E9", "F"]
EXPECTED_PIN = "ruff==0.15.22"

# Isolate the requirement name from a PEP 508 dependency string: the name ends
# at the first version operator, marker, extras bracket, or whitespace.
_NAME_END = "=<>!~; ["


def _load() -> dict:
    with PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)


def _req_name(spec: str) -> str:
    name = spec.strip()
    for i, ch in enumerate(name):
        if ch in _NAME_END:
            return name[:i].lower()
    return name.lower()


def _ruff(*args: str) -> subprocess.CompletedProcess:
    # Drive ruff via the current interpreter so the test uses the same installed
    # ruff the pin selects, not whatever a bare `ruff` on PATH happens to be.
    return subprocess.run(
        [sys.executable, "-m", "ruff", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_exactly_one_exact_ruff_pin() -> None:
    """Exactly one ruff dependency, and it is an exact `==` pin."""
    data = _load()
    project = data["project"]
    specs = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        specs.extend(group)

    ruff_specs = [s for s in specs if _req_name(s) == "ruff"]
    assert len(ruff_specs) == 1, f"expected exactly one ruff dependency, got {ruff_specs}"

    spec = ruff_specs[0].strip()
    assert spec == EXPECTED_PIN, f"ruff dep must be an exact pin {EXPECTED_PIN!r}, got {spec!r}"
    assert "==" in spec and ">=" not in spec, f"ruff dep must be pinned with ==, got {spec!r}"


def test_lint_select_is_historical_set() -> None:
    """The declared lint selection equals the historical default, exactly."""
    data = _load()
    lint = data.get("tool", {}).get("ruff", {}).get("lint", {})
    assert "select" in lint, "pyproject.toml is missing [tool.ruff.lint].select"
    assert lint["select"] == EXPECTED_SELECT, (
        f"lint.select must be {EXPECTED_SELECT}, got {lint['select']}"
    )


def test_ruff_resolves_root_config() -> None:
    """Ruff's reported ``Settings path`` is exactly the ROOT pyproject.toml.

    ``--show-settings`` prints a ``Settings path:`` header naming the config
    file ruff actually loaded. Parsing that field — rather than inspecting any
    selected-rule value — proves the pinned ruff resolved the repository-root
    ``pyproject.toml`` where PRD-273's pin and select live.
    """
    result = _ruff("check", "--show-settings", "cuttingboard/config.py")
    assert result.returncode == 0, f"--show-settings failed:\n{result.stdout}\n{result.stderr}"

    settings_path: str | None = None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Settings path:"):
            match = re.fullmatch(r'Settings path:\s*"(.+)"', stripped)
            assert match, f"malformed 'Settings path:' line: {stripped!r}"
            settings_path = match.group(1)
            break
    assert settings_path is not None, (
        f"ruff --show-settings emitted no 'Settings path:' field:\n{result.stdout}"
    )

    resolved = Path(settings_path).resolve()
    assert resolved == REPO_ROOT / "pyproject.toml", (
        f"ruff resolved config {resolved}, expected root {REPO_ROOT / 'pyproject.toml'}"
    )


def test_ruff_check_passes() -> None:
    """`ruff check cuttingboard/ tests/` — the CI command — passes clean."""
    result = _ruff("check", "cuttingboard/", "tests/")
    assert result.returncode == 0, (
        f"ruff check failed:\n{result.stdout}\n{result.stderr}"
    )
