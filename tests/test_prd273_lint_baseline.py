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

import os
import re
import shutil
import subprocess
import tomllib
import uuid
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version

# Every source type ruff lints. Building `discovered` from *.py alone would
# make FLOOR 2 fail spuriously the first time a .pyi stub or .ipynb notebook
# lands under a target — ruff includes them, so the equality check would read
# a correctly-linted new file as missing coverage and block CI.
RUFF_SOURCE_GLOBS = ("*.py", "*.pyi", "*.ipynb")

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"

# The lint targets CI actually checks (.github/workflows/ci.yml).
LINT_TARGETS = ["cuttingboard/", "tests/"]

_RUFF = shutil.which("ruff")

# ---------------------------------------------------------------------------
# THE FLOOR (Dustin, 2026-07-24)
# ---------------------------------------------------------------------------
# Everything below the floor enumerates a bypass MECHANISM — `ignore`,
# `per-file-ignores`, `exclude`, an unbounded specifier. That approach
# produced five holes across three review rounds, because a config surface is
# open-ended: there is no finite list of ways to weaken a lint gate, so a
# guard built from such a list is provably incomplete.
#
# These two constants are the mechanism-INDEPENDENT floor. They assert the
# OUTCOME rather than the route to it:
#
#   BASELINE_RULES  - the effective rule set, exactly
#   (file coverage) - every .py file under the CI targets is actually linted
#
# Anything that empties the file list, disables rules, or suppresses per-file
# fails against the floor whether or not anyone predicted the mechanism.
# Same move as PRD-269's fail-loud parser floor.
#
# If ruff adds or removes a rule inside the pinned range, the floor goes RED
# and the baseline is re-derived deliberately. That is the intended behavior,
# not churn: a silently-changing baseline is the thing this PRD exists to stop.
BASELINE_RULES = frozenset({
    "E401", "E402", "E701", "E702", "E703", "E711", "E712", "E713", "E714",
    "E721", "E722", "E731", "E741", "E742", "E743", "E902",
    "F401", "F402", "F403", "F404", "F405", "F406", "F407",
    "F501", "F502", "F503", "F504", "F505", "F506", "F507", "F508", "F509",
    "F521", "F522", "F523", "F524", "F525", "F541",
    "F601", "F602", "F621", "F622", "F631", "F632", "F633", "F634",
    "F701", "F702", "F704", "F706", "F707", "F722",
    "F811", "F821", "F822", "F823", "F841", "F842", "F901",
})


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
# FLOOR — mechanism-independent. Read these two first; the rest are
# mechanism-specific tests kept because a named failure message is more
# useful than a generic one, not because the floor depends on them.
# ---------------------------------------------------------------------------

def _resolved_rule_codes() -> set[str]:
    result = _ruff("check", "--show-settings", "cuttingboard/output.py")
    assert result.returncode == 0, result.stderr
    block = re.search(
        r"^linter\.rules\.enabled = \[(.*?)^\]", result.stdout, re.S | re.M
    )
    assert block, "could not parse linter.rules.enabled"
    return set(re.findall(r"\(([A-Z]+[0-9]+)\)", block.group(1)))


def test_floor_effective_rule_set_equals_the_pinned_baseline():
    """FLOOR 1 — the effective rule set IS the baseline, exactly.

    Absolute, not relative: it does not derive the expectation from the same
    config it is checking, so narrowing `select` cannot move both sides
    together. Any mechanism that adds, removes, or disables a rule — `ignore`,
    `extend-select`, `extend-ignore`, a version bump that shifts defaults,
    or one nobody has thought of — lands here.
    """
    resolved = _resolved_rule_codes()
    assert resolved == set(BASELINE_RULES), (
        "effective rule set no longer equals the pinned baseline.\n"
        f"  missing (disabled): {sorted(set(BASELINE_RULES) - resolved)}\n"
        f"  extra   (added)   : {sorted(resolved - set(BASELINE_RULES))}\n"
        "Re-derive the baseline deliberately if this change is intended."
    )

    # `rules.enabled` is GLOBAL and does not reflect per-file suppression —
    # verified: a per-file ignore leaves the set above identical. So the
    # rule-dimension floor is only complete with this second half, asserting
    # ruff's resolved per-file table is empty. State-based, not
    # mechanism-based: both `per-file-ignores` and `extend-per-file-ignores`
    # resolve into this same key (both verified).
    result = _ruff("check", "--show-settings", "cuttingboard/output.py")
    match = re.search(r"^linter\.per_file_ignores = (.*)$", result.stdout, re.M)
    assert match, "could not find linter.per_file_ignores"
    assert match.group(1).strip() == "{}", (
        "the baseline holds globally but is suppressed for specific files, so "
        "the effective rule set is NOT the baseline everywhere.\n"
        f"  resolved per_file_ignores: {match.group(1).strip()}"
    )


def test_floor_every_target_file_is_actually_linted():
    """FLOOR 2 — the run lints every .py file under the CI targets.

    A run that lints zero files is a FAILURE, not a pass — ruff exits 0 on an
    empty file list. Asserting set equality against filesystem discovery (not
    merely non-empty) also catches partial erosion: excluding one directory,
    one file, or 90% of the tree fails identically. Mechanism-independent
    across `exclude`, `extend-exclude`, `force-exclude`, `include`,
    `respect-gitignore`, and anything future.
    """
    result = _ruff("check", "--show-files", *LINT_TARGETS)
    assert result.returncode == 0, result.stderr
    resolved = {Path(line) for line in result.stdout.splitlines() if line.strip()}

    discovered = {
        p.resolve()
        for target in LINT_TARGETS
        for glob in RUFF_SOURCE_GLOBS
        for p in (REPO_ROOT / target.rstrip("/")).rglob(glob)
        if "__pycache__" not in p.parts
    }

    assert resolved, (
        "ruff resolved ZERO files for the CI lint targets — the gate lints "
        "nothing while still exiting 0."
    )
    assert resolved == discovered, (
        "ruff's linted file set does not match the .py files present under "
        f"{LINT_TARGETS}.\n"
        f"  present but NOT linted: "
        f"{sorted(str(p.relative_to(REPO_ROOT)) for p in discovered - resolved)}\n"
        f"  linted but not present: "
        f"{sorted(str(p.relative_to(REPO_ROOT)) for p in resolved - discovered)}"
    )


    # Every linted file must resolve to THIS pyproject. Probing one file and
    # generalising is a proxy: a nested `tests/ruff.toml` re-scopes an entire
    # subtree while the probed file's settings are unchanged — verified.
    seen = set()
    for probe in ("cuttingboard/output.py", __file__):
        out = _ruff("check", "--show-settings", str(probe)).stdout
        m = re.search(r'^Settings path:\s*"(.+)"\s*$', out, re.M)
        assert m, f"ruff resolved no config for {probe}"
        seen.add(Path(m.group(1)))
    assert seen == {PYPROJECT}, (
        "linted files resolve to more than one ruff configuration; a nested "
        f"config re-scopes part of the tree.\n  resolved: {sorted(map(str, seen))}"
    )



# The ONLY ruff configuration keys this repo sanctions. An ALLOW-list, not a
# deny-list: a deny-list of bypass mechanisms is provably incomplete (eight
# holes across five rounds proved it empirically), whereas an allow-list is
# complete by construction — anything not named here fails, including options
# nobody has heard of.
SANCTIONED_RUFF_KEYS = frozenset({"lint.select"})


def _flatten(d: dict, prefix: str = "") -> set[str]:
    out: set[str] = set()
    for key, value in d.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            out |= _flatten(value, f"{path}.")
        else:
            out.add(path)
    return out


def test_floor_root_config_contains_only_sanctioned_keys():
    """FLOOR 3 — allow-list the root config's keys, don't deny-list bypasses.

    Round 4 and 5 each found a behavior-changing option the guards did not
    know to look for (`dummy-variable-rgx`, `pyflakes.allowed-unused-imports`).
    Enumerating them is unbounded — ruff has hundreds of settings and gains
    more each release. Inverting it is bounded: assert the config contains
    ONLY what we sanctioned, so any unlisted key fails whether or not anyone
    predicted it.
    """
    ruff_cfg = _pyproject().get("tool", {}).get("ruff", {})
    present = _flatten(ruff_cfg)
    unsanctioned = present - set(SANCTIONED_RUFF_KEYS)
    assert not unsanctioned, (
        "pyproject.toml's [tool.ruff] contains keys this PRD did not "
        "sanction. Any of them may change what the gate enforces.\n"
        f"  unsanctioned: {sorted(unsanctioned)}\n"
        f"  sanctioned  : {sorted(SANCTIONED_RUFF_KEYS)}\n"
        "If the addition is intended, add it here deliberately and re-derive "
        "the baseline."
    )
    assert present == set(SANCTIONED_RUFF_KEYS), (
        f"expected exactly {sorted(SANCTIONED_RUFF_KEYS)}, got {sorted(present)}"
    )


def test_floor_no_nested_ruff_config_anywhere():
    """FLOOR 4 — exactly one ruff configuration exists, repo-wide.

    Probing a couple of files' resolved settings and generalising is a sample;
    a nested config in any unprobed subtree slips through — verified twice,
    under `tests/` and under `cuttingboard/delivery/`, with every test green.
    Filesystem enumeration is EXHAUSTIVE where settings-probing is not: there
    is a finite, walkable set of places a ruff config can live.
    """
    nested = [
        p for name in ("ruff.toml", ".ruff.toml")
        for p in REPO_ROOT.rglob(name)
        if ".git" not in p.parts and "node_modules" not in p.parts
    ]
    assert not nested, (
        "nested ruff config file(s) found; they silently re-scope the "
        "baseline for their subtree.\n"
        f"  {[str(p.relative_to(REPO_ROOT)) for p in nested]}"
    )

    other_pyprojects = [
        p for p in REPO_ROOT.rglob("pyproject.toml")
        if p != PYPROJECT and ".git" not in p.parts
    ]
    for p in other_pyprojects:
        with p.open("rb") as fh:
            assert "ruff" not in tomllib.load(fh).get("tool", {}), (
                f"{p.relative_to(REPO_ROOT)} declares [tool.ruff]; only the "
                "root pyproject.toml may configure ruff."
            )


# The canary: real code that MUST be flagged. One violation per baseline
# family, chosen so each is reported by a different rule.
_CANARY = '''\
import json

lambda_assigned = lambda x: x


def _f():
    unused_local = 42
    return f"no placeholders"
'''
_CANARY_EXPECTED = {"F401", "E731", "F841", "F541"}


def test_floor_gate_actually_flags_known_bad_code():
    """FLOOR 0 — the strongest floor: stop inspecting config, feed it bad input.

    Every other guard here reads ruff's *configuration* and reasons about what
    it implies. That is a proxy, and it has now failed twice in ways no
    config-inspection could catch:
      - `dummy-variable-rgx = ".*"` leaves F841 in the enabled set while
        making it ignore every variable — behavior changed, codes identical.
      - a nested `tests/ruff.toml` re-scopes a whole subtree while the probed
        file's settings are unchanged.
    Freezing the full settings dump does not fix it either: the dump is not
    stable across the pinned range (0.15.8 vs 0.15.22 differ by 7 lines of
    newly-added options), so it would go red on benign patch bumps.

    So this asserts the OUTCOME with no reference to configuration at all: a
    file containing real violations, written INSIDE the lint targets so every
    scoping mechanism applies to it, must actually be flagged. Anything that
    disables a rule, guts its semantics, suppresses it per-file, re-scopes it
    via a nested config, or excludes the path makes the canary go silent —
    whether or not anyone predicted the mechanism.
    """
    # Unique name, and refuse to touch a path that already exists: a fixed
    # name would overwrite a developer's untracked file (or a concurrent run's
    # canary) and then delete it in the finally. A test must not destroy
    # working-tree state it did not create.
    canary = (
        REPO_ROOT / "tests" / f"_prd273_canary_{os.getpid()}_{uuid.uuid4().hex[:8]}.py"
    )
    assert not canary.exists(), f"canary path unexpectedly occupied: {canary}"
    try:
        canary.write_text(_CANARY)
        result = _ruff(
            "check", "--no-cache", "--output-format", "concise", str(canary)
        )
        reported = set(re.findall(r"\b([EFW]\d{3})\b", result.stdout))
        missing = _CANARY_EXPECTED - reported
        assert not missing, (
            "the lint gate did NOT flag known-bad code. These baseline rules "
            "are configured as enabled but are not actually enforced for this "
            f"path:\n  silent: {sorted(missing)}\n  reported: {sorted(reported)}\n"
            f"{result.stdout}"
        )
    finally:
        canary.unlink(missing_ok=True)


def test_floor_lint_targets_match_what_ci_actually_runs():
    """FLOOR 3 — the floor is measuring the command CI really uses.

    Both floors above are scoped to LINT_TARGETS. If `ci.yml` changed its
    ruff invocation, they would keep passing while guarding a command nobody
    runs — the floor measuring the wrong thing is the one way it fails
    silently, so it is pinned to the workflow's own text.
    """
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text()
    expected = "ruff check " + " ".join(LINT_TARGETS)

    # EXACT line match, not a substring. A substring check is evaded by
    # appending flags: `ruff check cuttingboard/ tests/ --ignore F401` still
    # contains the expected text while gutting the gate — verified, 17 tests
    # passed under it. CLI flags are the one config surface FLOOR 4's
    # filesystem walk cannot see, so the invocation itself must be pinned.
    ruff_lines = [
        line.split("run:", 1)[1].strip()
        for line in workflow.splitlines()
        if "run:" in line and "ruff" in line
    ]
    assert ruff_lines, "ci.yml has no ruff invocation"
    for line in ruff_lines:
        assert line == expected, (
            "ci.yml's ruff invocation is not exactly the pinned command. "
            "Extra flags (--ignore, --config, --isolated, --exclude) override "
            "the file-based configuration these floors verify.\n"
            f"  expected: {expected!r}\n  actual  : {line!r}"
        )


# ---------------------------------------------------------------------------
# R1 — ruff is pinned to a bounded range
# ---------------------------------------------------------------------------

def _ruff_specifier() -> str:
    dev = _pyproject()["project"]["optional-dependencies"]["dev"]
    specs = [s for s in dev if s.replace(" ", "").startswith("ruff")]
    assert specs, "ruff is not declared in the dev extra"
    return specs[0]


def test_r1_specifier_excludes_the_known_bad_versions():
    """Assert the ceiling actually EXCLUDES 0.16+, not merely that one exists.

    Checking only for the presence of a `<` is too weak: `ruff>=0.4.0,<1`
    contains one and still admits 0.16.0, the exact version this PRD exists
    to keep out. Parse the specifier and ask it directly.
    (Raised by chatgpt-codex-connector on PR #168; confirmed real.)
    """
    raw = _ruff_specifier().split(";")[0].removeprefix("ruff")
    spec = SpecifierSet(raw)

    # STRUCTURAL, not sampled. Testing a handful of versions is evaded by
    # `>=0.4,<0.17,!=0.16.0,!=0.16.1`, which excludes the samples and still
    # admits 0.16.2 — the same "checked the instances I thought of" error
    # this file has now made five times. Assert the CEILING instead: some
    # upper-bound clause must cut at or below 0.16, which excludes the whole
    # interval regardless of how many `!=` exceptions are bolted on.
    first_bad = Version("0.16.0")
    clauses = [(s.operator, Version(s.version)) for s in spec]
    uppers = [(op, v) for op, v in clauses if op in ("<", "<=")]
    assert uppers, (
        f"ruff specifier {raw!r} has no upper-bound clause at all; an "
        "unbounded specifier is a movable identity (PRD-198 invariant 6)."
    )
    # Operator-aware. Collapsing `<` and `<=` together is an off-by-one:
    # `<=0.16` admits 0.16.0 (packaging normalises 0.16 == 0.16.0), which is
    # the exact release that broke CI — and it passed the previous check.
    #   `<X`  excludes the whole 0.16 line iff X <= 0.16.0
    #   `<=X` excludes it iff X <  0.16.0
    excludes_line = any(
        (v <= first_bad) if op == "<" else (v < first_bad) for op, v in uppers
    )
    assert excludes_line, (
        f"ruff specifier {raw!r} does not exclude the whole 0.16 line: "
        f"ceiling {uppers}. 0.16.0 expanded ruff's default rule set and "
        "turned CI red with no diff."
    )
    # Belt and braces: assert the property directly too, so a mistake in the
    # structural reasoning above cannot let 0.16.0 back in on its own.
    assert str(first_bad) not in spec, (
        f"ruff specifier {raw!r} admits {first_bad}."
    )


def test_r1_specifier_still_admits_the_verified_versions():
    """The ceiling must not be so tight it excludes what CI actually installs."""
    spec = SpecifierSet(_ruff_specifier().split(";")[0].removeprefix("ruff"))
    for good in ("0.15.8", "0.15.22"):
        assert good in spec, (
            f"ruff specifier {_ruff_specifier()!r} excludes {good}, a version "
            "the baseline was verified against."
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


def _enabled_rules(*extra: str) -> set[str]:
    """The rules ruff RESOLVES for this repo, not the ones it was asked for.

    `select` is the request; this is the effect. Reading the effect is what
    makes the check immune to `ignore` / `per-file-ignores` quietly removing
    rules that `select` still lists.
    """
    result = _ruff("check", "--show-settings", *extra, "cuttingboard/output.py")
    assert result.returncode == 0, result.stderr
    block = re.search(
        r"^linter\.rules\.enabled = \[(.*?)^\]", result.stdout, re.S | re.M
    )
    assert block, "could not parse linter.rules.enabled from ruff --show-settings"
    return {
        line.strip().rstrip(",")
        for line in block.group(1).strip().splitlines()
        if line.strip()
    }


def test_r2_effective_rule_set_matches_the_declared_one():
    """Compare RESOLVED rules against the declared selection applied cleanly.

    Asserting only on the `select` list leaves a hole: adding
    `ignore = ["F401"]` or a `per-file-ignores` entry weakens the effective
    set while `select` still reads correctly, and — because the tree has no
    violations under the narrowed set — `ruff check` stays green too. Both
    guards would pass while the baseline silently eroded.

    So compare the repo's resolved rules against what the declared selection
    resolves to with no overrides. Any suppression makes the two differ.
    (Raised by chatgpt-codex-connector on PR #168; confirmed real — adding
    `ignore = ["F401"]` drops the resolved count from 59 to 58.)
    """
    declared = ",".join(_pyproject()["tool"]["ruff"]["lint"]["select"])
    repo_resolved = _enabled_rules()
    clean_resolved = _enabled_rules("--isolated", "--select", declared)

    assert repo_resolved == clean_resolved, (
        "the repo's effective rule set differs from its declared selection "
        "applied without overrides — something (ignore / per-file-ignores / "
        "extend-*) is suppressing rules that `select` still lists.\n"
        f"  suppressed: {sorted(clean_resolved - repo_resolved)}\n"
        f"  unexpected: {sorted(repo_resolved - clean_resolved)}"
    )
    assert repo_resolved, "resolved rule set is empty"


def test_r2_no_per_file_suppressions():
    """`rules.enabled` does NOT reflect per-file ignores — assert them separately.

    Correcting an overclaim I made when fixing the previous finding: I said
    comparing resolved rule sets "also catches extend-per-file-ignores". It
    does not. Per-file suppressions are reported under a different key and
    leave `linter.rules.enabled` untouched, so
    `per-file-ignores = {"cuttingboard/output.py" = ["F401"]}` disables F401
    for that file while every other guard here stays green — verified.
    (Raised by chatgpt-codex-connector on PR #168; confirmed real.)
    """
    result = _ruff("check", "--show-settings", "cuttingboard/output.py")
    assert result.returncode == 0, result.stderr

    match = re.search(r"^linter\.per_file_ignores = (.*)$", result.stdout, re.M)
    assert match, "could not find linter.per_file_ignores in ruff --show-settings"
    assert match.group(1).strip() == "{}", (
        "ruff resolved a non-empty linter.per_file_ignores. Per-file "
        "suppressions erode the declared baseline for the affected files "
        "without changing the enabled rule set, so they must be empty for "
        "the baseline claim to hold.\n"
        f"  resolved: {match.group(1).strip()}"
    )


# ---------------------------------------------------------------------------
# R3 — the declared set reproduces the green baseline
# ---------------------------------------------------------------------------

def test_r3_repo_is_clean_under_the_declared_rule_set():
    result = _ruff("check", "--no-cache", *LINT_TARGETS)
    assert result.returncode == 0, (
        "`ruff check` is not clean under the declared rule set:\n"
        f"{result.stdout}\n{result.stderr}"
    )


def test_r3_lint_actually_covers_both_targets():
    """A clean exit is not evidence of coverage — ruff exits 0 on zero files.

    `[tool.ruff] exclude = ["cuttingboard/**", "tests/**"]` makes
    `ruff check cuttingboard/ tests/` print "No Python files found", exit 0,
    and satisfy every other guard here — the lint gate silently disabled
    while CI stays green. Verified. So assert the resolved file set, not the
    exit code alone.
    (Raised by chatgpt-codex-connector on PR #168; confirmed real.)
    """
    result = _ruff("check", "--show-files", *LINT_TARGETS)
    assert result.returncode == 0, result.stderr
    files = [Path(line) for line in result.stdout.splitlines() if line.strip()]
    assert files, (
        "ruff resolved ZERO files for the CI lint targets — the gate checks "
        "nothing. Likely an `exclude` / `extend-exclude` covering "
        f"{LINT_TARGETS}."
    )

    pkg = REPO_ROOT / "cuttingboard"
    tst = REPO_ROOT / "tests"
    assert any(f.is_relative_to(pkg) for f in files), (
        "no files resolved under cuttingboard/ — that target is excluded"
    )
    assert any(f.is_relative_to(tst) for f in files), (
        "no files resolved under tests/ — that target is excluded"
    )
    # This test file itself must be covered; if it is not, the guard is
    # inspecting a lint run that would not even see its own assertions.
    assert Path(__file__).resolve() in files, (
        "this test file is not in ruff's resolved set for the CI targets"
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

    match = re.search(r'^Settings path:\s*"(.+)"\s*$', result.stdout, re.M)
    assert match, (
        "ruff reported no `Settings path`, meaning it resolved NO "
        "configuration file — the [tool.ruff.lint] table is not being loaded."
    )
    assert Path(match.group(1)) == PYPROJECT, (
        f"ruff loaded {match.group(1)!r}, not this repo's {PYPROJECT}."
    )


def test_r4_installed_ruff_satisfies_the_declared_pin():
    """Assert the RESOLVED version, not the declared intent (invariant 2)."""
    result = _ruff("--version")
    assert result.returncode == 0
    version = result.stdout.split()[-1]
    # Check membership in the WHOLE declared range, not just the ceiling: an
    # assertion named "satisfies the declared pin" that only tests the upper
    # bound would pass on a pre-0.4 ruff left on PATH by a stale environment.
    # (Raised by chatgpt-codex-connector on PR #168; correct.)
    spec = SpecifierSet(_ruff_specifier().split(";")[0].removeprefix("ruff"))
    assert version in spec, (
        f"installed ruff {version} does not satisfy the declared pin "
        f"{_ruff_specifier()!r}. The pin and the environment disagree; CI "
        "parity is not established (PRD-198 invariant 5)."
    )
