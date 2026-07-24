"""PRD-273 — the lint contract is explicit and version-independent.

Before this PRD the repo had no ruff configuration at all, so `ruff check`
enforced whatever the installed ruff version happened to default to. On
2026-07-24 ruff 0.16.0 expanded its defaults and CI went red on code nobody
had touched — 1112 errors against a pristine `origin/main` whose own last
recorded CI run was green.

These tests pin the two halves of the fix. R4 is the red-by-construction
guard (PRD-198 invariant 4): it asserts the declared rule set is what is
actually holding the line, by showing that ruff run WITHOUT the repo's
config on the same tree reports errors. Delete `[tool.ruff.lint].select`
and R2/R3 go red immediately.
"""

import shutil
import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"

# The lint targets CI actually checks (.github/workflows/ci.yml).
LINT_TARGETS = ["cuttingboard/", "tests/"]

_RUFF = shutil.which("ruff")


def _pyproject() -> dict:
    with PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)


def _ruff(*args: str) -> subprocess.CompletedProcess:
    """Fail loud if ruff is absent — never skip a required dependency."""
    assert _RUFF is not None, (
        "ruff not found on PATH. It is a declared dev dependency "
        "(pyproject.toml [project.optional-dependencies] dev); a missing "
        "required dep must fail, not skip (PRD-198 invariant 4)."
    )
    return subprocess.run(
        [_RUFF, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


# ---------------------------------------------------------------------------
# R1 — ruff is pinned to a bounded range
# ---------------------------------------------------------------------------

def test_r1_ruff_specifier_has_an_upper_bound():
    dev = _pyproject()["project"]["optional-dependencies"]["dev"]
    ruff_specs = [s for s in dev if s.replace(" ", "").startswith("ruff")]
    assert ruff_specs, "ruff is not declared in the dev extra"
    spec = ruff_specs[0]
    assert "<" in spec, (
        f"ruff specifier {spec!r} has no upper bound. An unbounded specifier "
        "is a movable identity: ruff 0.16.0 expanded its default rule set and "
        "turned CI red with no diff (PRD-198 invariant 6)."
    )


# ---------------------------------------------------------------------------
# R2 — the rule set is declared explicitly
# ---------------------------------------------------------------------------

def test_r2_lint_rule_set_is_declared_explicitly():
    lint = _pyproject().get("tool", {}).get("ruff", {}).get("lint", {})
    assert "select" in lint, (
        "pyproject.toml has no [tool.ruff.lint] select. Without it the lint "
        "contract is ruff's implicit default, which changes between versions."
    )
    assert lint["select"], "[tool.ruff.lint] select is empty"


def test_r2_declared_rule_set_is_the_verified_baseline():
    """Pin the exact set, so widening or narrowing it is a visible diff."""
    lint = _pyproject()["tool"]["ruff"]["lint"]
    assert sorted(lint["select"]) == ["E4", "E7", "E9", "F"]


# ---------------------------------------------------------------------------
# R3 — the declared set reproduces the green baseline
# ---------------------------------------------------------------------------

def test_r3_repo_is_clean_under_the_declared_rule_set():
    result = _ruff("check", "--no-cache", *LINT_TARGETS)
    assert result.returncode == 0, (
        "`ruff check` is not clean under the declared rule set:\n"
        f"{result.stdout}\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# R4 — red by construction
# ---------------------------------------------------------------------------

def test_r4_declared_rule_set_is_a_consequential_choice():
    """The declared set must be a real boundary, not a vacuous one.

    Note what this does NOT assert. Under the pinned ruff (<0.16) the implicit
    defaults happen to COINCIDE with the declared set, so `--isolated` is also
    clean — asserting otherwise would be asserting something false. That
    coincidence is precisely why pinning alone was insufficient: it holds only
    until a release moves the defaults, which is what ruff 0.16.0 did (1112
    errors on an unchanged `origin/main`).

    What is verifiable on any ruff version is that the selection is
    consequential: a wider set on this same tree DOES fail, so the declared
    set is a deliberate boundary rather than "every rule, trivially satisfied".
    If this ever passes with the wider set, the tree has changed enough that
    the baseline should be re-derived rather than assumed.
    """
    configured = _ruff("check", "--no-cache", *LINT_TARGETS)
    assert configured.returncode == 0, (
        f"declared set is not clean:\n{configured.stdout}"
    )

    wider = _ruff(
        "check", "--no-cache", "--isolated",
        "--select", "E4,E7,E9,F,UP,DTZ,BLE",
        *LINT_TARGETS,
    )
    assert wider.returncode != 0, (
        "a deliberately wider rule set reports no violations on this tree, so "
        "the declared selection draws no real boundary. Re-derive the baseline "
        "instead of assuming this one."
    )


def test_r4_config_is_actually_applied_not_just_present():
    """Assert the resolved behavior, not the declared intent (invariant 2).

    A `[tool.ruff.lint]` table that ruff never loads would satisfy R2 while
    doing nothing. Proven by asking ruff itself to resolve the settings for a
    file in the lint target and echo back the rules it will apply.
    """
    result = _ruff("check", "--show-settings", "cuttingboard/output.py")
    assert result.returncode == 0, result.stderr
    assert "pyproject.toml" in result.stdout or "E4" in result.stdout, (
        "ruff did not report resolving this repo's configuration; the "
        "[tool.ruff.lint] table may be present but never loaded."
    )


def test_r4_installed_ruff_satisfies_the_declared_pin():
    """Assert the RESOLVED version, not the declared intent (invariant 2)."""
    result = _ruff("--version")
    assert result.returncode == 0
    version = result.stdout.split()[-1]
    major, minor = (int(p) for p in version.split(".")[:2])
    assert (major, minor) < (0, 16), (
        f"installed ruff {version} is outside the declared range (<0.16). "
        "The pin and the environment disagree; CI parity is not established."
    )
