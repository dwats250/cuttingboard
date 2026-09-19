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

import json
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


def _resolved_rule_codes() -> set[str]:
    """Rule CODEs the pinned ruff RESOLVES, parsed from the
    ``linter.rules.enabled = [ ... ]`` block of ``ruff check --show-settings``;
    a missing/unterminated block fails loud (never a silent empty set)."""
    result = _ruff("check", "--show-settings", "cuttingboard/config.py")
    assert result.returncode == 0, f"--show-settings failed:\n{result.stdout}\n{result.stderr}"
    lines = result.stdout.splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().startswith("linter.rules.enabled = [")), None)
    assert start is not None, f"no 'linter.rules.enabled = [' block:\n{result.stdout}"
    end = next((j for j in range(start + 1, len(lines)) if lines[j].strip() == "]"), None)
    assert end is not None, "unterminated 'linter.rules.enabled' block in --show-settings"
    return set(re.findall(r"\(([A-Z]+[0-9]+)\)", "\n".join(lines[start : end + 1])))


def _declared_rule_codes() -> set[str]:
    """Expand ``[tool.ruff.lint].select`` against ruff's OWN catalogs (no
    hand-maintained code list): resolve each selector to its owning linter via
    ``ruff linter`` (code prefix = linter prefix + category prefix, so Pylint
    "PL"+"E" is "PLE" and never shadows pycodestyle "E", and FastAPI/FBT/FIX stay
    out of "F"), then take that linter's STABLE codes sharing the selector."""
    select = _load()["tool"]["ruff"]["lint"]["select"]
    rules_proc = _ruff("rule", "--all", "--output-format", "json")
    linters_proc = _ruff("linter", "--output-format", "json")
    assert rules_proc.returncode == 0, f"ruff rule catalog failed:\n{rules_proc.stderr}"
    assert linters_proc.returncode == 0, f"ruff linter catalog failed:\n{linters_proc.stderr}"
    rules = json.loads(rules_proc.stdout)

    prefix_to_linter: dict[str, str] = {}
    for entry in json.loads(linters_proc.stdout):
        base = entry.get("prefix") or ""
        if base:
            prefix_to_linter[base] = entry["name"]
        for category in entry.get("categories") or []:
            if category.get("prefix"):
                prefix_to_linter[base + category["prefix"]] = entry["name"]

    def _owner(selector: str) -> str:
        candidates = [p for p in prefix_to_linter if selector.startswith(p)]
        assert candidates, f"no ruff linter owns selector {selector!r}"
        return prefix_to_linter[max(candidates, key=len)]

    codes: set[str] = set()
    for selector in select:
        owner = _owner(selector)
        codes |= {
            rule["code"] for rule in rules
            if rule["linter"] == owner and rule["code"].startswith(selector)
            and isinstance(rule.get("status"), dict) and "Stable" in rule["status"]
        }
    return codes


def test_resolved_rule_set_equals_declared_expansion() -> None:
    """PRD-274 / PRD-198 invariant 2: the COMPLETE resolved rule set equals the
    COMPLETE declared-``select`` expansion — a missing or undeclared family turns
    this RED naming the symmetric difference; an empty side fails loud."""
    resolved = _resolved_rule_codes()
    declared = _declared_rule_codes()
    assert resolved, "RESOLVED rule set is empty — parse of ruff --show-settings failed"
    assert declared, "DECLARED rule set is empty — select expansion produced nothing"
    assert resolved == declared, (
        f"resolved != declared; declared missing from RESOLVED: {sorted(declared - resolved)}; "
        f"undeclared extras in RESOLVED: {sorted(resolved - declared)}"
    )
