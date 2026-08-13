"""PRD-293 (QW-5) mutation-discriminating tests for dev_bootstrap.

These tests use temporary repositories and stateful executable fakes. The fake
venv interpreter validates invocation isolation and invokes fake ruff/pytest
binaries. A separate hermetic harness executes the readiness probe extracted
verbatim from the production script under a real Python interpreter.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "dev_bootstrap.sh"
SETTINGS = REPO / ".claude" / "settings.json"
BEGIN = "# >>> dev_bootstrap (PRD-293) >>>"
END = "# <<< dev_bootstrap (PRD-293) <<<"

FAKE_RUFF = r"""#!/usr/bin/env bash
printf 'ruff %s\n' "$*" >>"$FAKE_CALLS"
echo 'ruff 0.15.22'
"""

FAKE_PYTEST = r"""#!/usr/bin/env bash
printf 'pytest %s\n' "$*" >>"$FAKE_CALLS"
echo 'pytest 9.0.0'
"""

FAKE_VENV_PY = r"""#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
args = sys.argv[1:]
calls = Path(os.environ["FAKE_CALLS"])
calls.parent.mkdir(parents=True, exist_ok=True)

def log(message):
    with calls.open("a") as f:
        f.write(message + "\n")

def isolated():
    if "-I" not in args:
        log("NO_I " + " ".join(args))
        return False
    return True

log("python " + " ".join(args) + " PYTHONPATH=" + os.environ.get("PYTHONPATH", "UNSET"))
if not isolated():
    sys.exit(91)

if "-c" in args:
    code = args[args.index("-c") + 1]
    if "sys.prefix" in code:
        sys.exit(0)
    sys.exit(0)

if "-m" in args and args[args.index("-m") + 1] == "pip":
    required = {"--isolated", "--no-cache-dir", "install"}
    if not required.issubset(args) or os.environ.get("PIP_CONFIG_FILE") != "/dev/null":
        log("BAD_PIP " + " ".join(args))
        sys.exit(92)
    log("pip")
    if (root / ".install_fail").exists():
        sys.exit(1)
    (root / ".ready").touch()
    sys.exit(0)

if "-m" in args and args[args.index("-m") + 1] == "pytest":
    log("pytest-I")
    sys.exit(1 if (root / ".pytest_bad").exists() else 0)

if "-" not in args:
    sys.exit(0)

sys.stdin.read()
log("probe")
if not (root / ".ready").exists():
    sys.exit(1)

for tool in ("ruff", "pytest"):
    result = subprocess.run(
        [str(root / ".venv" / "bin" / tool), "--version"],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        sys.exit(1)
result = subprocess.run(
    [str(root / ".venv" / "bin" / "python"), "-I", "-m", "pytest", "--version"],
    capture_output=True,
    text=True,
)
sys.exit(result.returncode)
"""

FAKE_BASE_PY = r"""#!/usr/bin/env python3
import os
import shutil
import sys
from pathlib import Path

args = sys.argv[1:]
calls = Path(os.environ["FAKE_CALLS"])

def log(message):
    with calls.open("a") as f:
        f.write(message + "\n")

if "-I" not in args:
    log("BASE_NO_I " + " ".join(args))
    sys.exit(95)
if "-c" in args:
    sys.exit(0)
if "-m" in args and args[args.index("-m") + 1] == "venv":
    target = Path(args[-1])
    target.joinpath("bin").mkdir(parents=True)
    for name, source in (
        ("python", os.environ["FAKE_VENV_PY_SRC"]),
        ("ruff", os.environ["FAKE_RUFF_SRC"]),
        ("pytest", os.environ["FAKE_PYTEST_SRC"]),
    ):
        destination = target / "bin" / name
        shutil.copyfile(source, destination)
        destination.chmod(0o755)
    log("venv")
    sys.exit(0)
sys.exit(0)
"""

PROBE_DRIVER = r"""
import importlib.metadata as md
import importlib.util as iu
import json
import os
import subprocess
import sys
import tomllib
import types
import urllib.parse

from packaging.requirements import Requirement

root, scenario = sys.argv[1], sys.argv[2]
venv = os.path.join(root, ".venv")
sys.prefix = "/usr" if scenario == "wrong_prefix" else venv
sys.base_prefix = venv if scenario == "wrong_prefix" else "/usr"
sys.executable = (
    "/usr/bin/other"
    if scenario == "wrong_identity"
    else os.path.join(venv, "bin", "python")
)
path = [os.path.join(venv, "lib", "python3.13", "site-packages")]
if scenario == "external_site":
    path.append("/opt/x/site-packages")
if scenario == "external_dist":
    path.append("/usr/lib/python3/dist-packages")
sys.path = path

package = "cuttingboard_evil" if scenario == "bad_origin" else "cuttingboard"
iu.find_spec = lambda name: types.SimpleNamespace(
    origin=os.path.join(root, package, "__init__.py"),
)

url = "file://" + root if scenario != "bad_url" else "file:///wrong"
editable = scenario != "non_editable"
md.distribution = lambda name: types.SimpleNamespace(
    read_text=lambda filename: (
        json.dumps({"url": url, "dir_info": {"editable": editable}})
        if filename == "direct_url.json"
        else None
    ),
)
md.version = lambda name: "0.0.1" if scenario == "bad_version" else "9.9.9"

def run(args, **kwargs):
    command = " ".join(map(str, args))
    output = "ruff 0.15.22" if "ruff" in command else "pytest 9.0.0"
    return types.SimpleNamespace(returncode=0, stdout=output, stderr="")

subprocess.run = run
probe = open(os.environ["PROBE_FILE"]).read()
sys.argv = ["probe", root]
exec(compile(probe, "<probe>", "exec"), {"__name__": "__main__"})
"""


def _write_executable(path: Path, content: str) -> None:
    # The fake python interpreters shadow `python3` on PATH; an `env python3`
    # shebang would recurse into the shadow (infinite exec loop). Pin them to the
    # real interpreter running this suite (CI-parity) so they execute as genuine
    # Python. Bash fakes (`env bash`) are untouched.
    marker = "#!/usr/bin/env python3"
    if content.startswith(marker):
        content = "#!" + sys.executable + content[len(marker):]
    path.write_text(content)
    path.chmod(0o755)


def _mkrepo(tmp_path: Path, *, with_venv: bool, ready: bool) -> Path:
    repo = tmp_path
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "scripts").mkdir()
    _write_executable(repo / "scripts" / "dev_bootstrap.sh", SCRIPT.read_text())
    (repo / "pyproject.toml").write_text(
        "[project]\nname='cuttingboard'\ndependencies=['example>=1']\n"
        "[project.optional-dependencies]\ndev=['dev-example>=1']\n"
    )
    (repo / "cuttingboard").mkdir()
    (repo / "cuttingboard" / "__init__.py").write_text("")

    _write_executable(repo / "fake_venv_python", FAKE_VENV_PY)
    _write_executable(repo / "fake_ruff", FAKE_RUFF)
    _write_executable(repo / "fake_pytest", FAKE_PYTEST)
    fakebin = repo / "fakebin"
    fakebin.mkdir()
    _write_executable(fakebin / "python3", FAKE_BASE_PY)
    _write_executable(fakebin / "python", FAKE_BASE_PY)

    if with_venv:
        bin_dir = repo / ".venv" / "bin"
        bin_dir.mkdir(parents=True)
        for name, source in (
            ("python", "fake_venv_python"),
            ("ruff", "fake_ruff"),
            ("pytest", "fake_pytest"),
        ):
            _write_executable(bin_dir / name, (repo / source).read_text())
    if ready:
        (repo / ".ready").touch()
    return repo


def _env(repo: Path, claude_env: Path | None = None) -> dict[str, str]:
    env = {
        "PATH": f"{repo / 'fakebin'}:{os.environ['PATH']}",
        "HOME": str(repo),
        "PYTHONPATH": "/caller/injection",
        "PYTHONHOME": "/caller/home",
        "FAKE_CALLS": str(repo / "calls.log"),
        "FAKE_VENV_PY_SRC": str(repo / "fake_venv_python"),
        "FAKE_RUFF_SRC": str(repo / "fake_ruff"),
        "FAKE_PYTEST_SRC": str(repo / "fake_pytest"),
    }
    if claude_env is not None:
        env["CLAUDE_ENV_FILE"] = str(claude_env)
    return env


def _run(
    repo: Path,
    *,
    claude_env: Path | None | object = ...,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    if claude_env is ...:
        claude_env = repo / "session.sh"
    if isinstance(claude_env, Path) and claude_env.parent.exists() and not claude_env.exists():
        claude_env.write_text("# user content\n")
    env = _env(repo, claude_env if isinstance(claude_env, Path) else None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(repo / "scripts" / "dev_bootstrap.sh")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _calls(repo: Path) -> str:
    path = repo / "calls.log"
    return path.read_text() if path.exists() else ""


def _session(repo: Path) -> str:
    path = repo / "session.sh"
    return path.read_text() if path.exists() else ""


def _owned_block(repo: Path) -> str:
    return (
        f"{BEGIN}\n"
        f"export VIRTUAL_ENV={repo / '.venv'!s}\n"
        f"export PATH={repo / '.venv' / 'bin'!s}:\"$PATH\"\n"
        f"{END}\n"
    )


def _read_probe() -> str:
    lines = SCRIPT.read_text().splitlines()
    start = next(index for index, line in enumerate(lines) if "<<'PY'" in line)
    end = next(
        index
        for index in range(start + 1, len(lines))
        if lines[index].strip() == "PY"
    )
    probe = "\n".join(lines[start + 1 : end]) + "\n"
    for guard in (
        "os.path.commonpath",
        "direct_url.json",
        '"dist-packages"',
        '"site-packages"',
        "Requirement(",
    ):
        assert guard in probe
    return probe


def _stage_probe_repo(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        "[project]\nname='cuttingboard'\ndependencies=['example>=1']\n"
        "[project.optional-dependencies]\ndev=['dev-example>=1']\n"
    )
    for package in ("cuttingboard", "cuttingboard_evil"):
        package_dir = root / package
        package_dir.mkdir()
        package_dir.joinpath("__init__.py").write_text("")
    (root / ".venv" / "bin").mkdir(parents=True)
    (root / ".venv" / "lib" / "python3.13" / "site-packages").mkdir(
        parents=True,
    )
    return root


def _run_probe(
    root: Path,
    scenario: str,
    probe: str,
) -> subprocess.CompletedProcess[str]:
    driver = root / "probe_driver.py"
    probe_file = root / "probe.py"
    driver.write_text(PROBE_DRIVER)
    probe_file.write_text(probe)
    env = os.environ.copy()
    env["PROBE_FILE"] = str(probe_file)
    return subprocess.run(
        [sys.executable, str(driver), str(root), scenario],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_script_stays_within_frozen_production_ceiling():
    production = [
        line
        for line in SCRIPT.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    # PRD-301 AMENDMENT 1 (owner amended Gate A 2026-08-12, event #7): the frozen ceiling is
    # raised to the ratified 260 to admit the exact-pathname link() acquisition, the
    # RECLAIM_LOCK-serialized reclaim, the PID-identity ownership proof, and the authoritative
    # post-move legacy-grave fail-loud. 260 is a CEILING not a target; >260 is a Section-8 RED
    # owner-stop, never a HELM renewal and never packed to evade.
    assert len(production) <= 260
    text = SCRIPT.read_text()
    assert "PIP_CONFIG_FILE=/dev/null" in text
    assert "--isolated install --no-cache-dir" in text
    assert 'mv -f "$tmp" "$CLAUDE_ENV_FILE"' in text
    assert '>>"$CLAUDE_ENV_FILE"' not in text
    # PRD-301 AMENDMENT 1: exact-pathname link() acquisition (not `ln`, which links inside a
    # directory); no GNU-only flags; RECLAIM_LOCK-serialized reclaim with a PID-identity,
    # existence-guarded EXIT release; authoritative post-move legacy-grave fail-loud; and the
    # superseded non-atomic `-ef` compare-then-unlink is gone.
    assert "mv -T" not in text and "ln -T" not in text
    assert 'link "$_lock_tmp" "$LOCKFILE"' in text
    assert 'RECLAIM_LOCK="$LOCKFILE.reclaim"' in text
    assert 'link "$_lock_tmp" "$RECLAIM_LOCK"' in text
    assert '[ -e "$RECLAIM_LOCK" ] && IFS= read -r _p <"$RECLAIM_LOCK"' in text
    assert 'rmdir "$grave" 2>/dev/null && return 0' in text
    assert "return 4" in text
    assert "-ef" not in text
    # PRD-301 (R5): the production lock-wait bound stays 60s (120 x 0.5s); tests override via
    # env, so pin the defaults in text lest a future edit silently change the production bound.
    assert "${DEV_BOOTSTRAP_LOCK_TRIES:-120}" in text
    assert "${DEV_BOOTSTRAP_LOCK_SLEEP:-0.5}" in text


def test_ready_path_is_isolated_version_true_and_binds(tmp_path):
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    result = _run(repo)
    assert result.returncode == 0, result.stderr
    calls = _calls(repo)
    assert "pip" not in calls
    assert "ruff --version" in calls
    assert "pytest --version" in calls and "pytest-I" in calls
    assert "NO_I" not in calls and "PYTHONPATH=UNSET" in calls
    assert _session(repo).count(BEGIN) == 1


def test_bootstrap_installs_once_with_isolated_pip(tmp_path):
    repo = _mkrepo(tmp_path, with_venv=False, ready=False)
    result = _run(repo)
    assert result.returncode == 0, result.stderr
    calls = _calls(repo)
    assert calls.count("pip\n") == 1
    assert "BAD_PIP" not in calls and "BASE_NO_I" not in calls
    assert _session(repo).count(BEGIN) == 1


def test_readiness_probe_rejects_each_semantic_fault(tmp_path):
    probe = _read_probe()
    accepted = _run_probe(_stage_probe_repo(tmp_path / "legitimate"), "legit", probe)
    assert accepted.returncode == 0, (accepted.stdout, accepted.stderr)

    for scenario in (
        "bad_origin",
        "external_site",
        "external_dist",
        "bad_version",
        "wrong_identity",
        "wrong_prefix",
        "non_editable",
        "bad_url",
    ):
        rejected = _run_probe(_stage_probe_repo(tmp_path / scenario), scenario, probe)
        assert rejected.returncode != 0, (
            scenario,
            rejected.stdout,
            rejected.stderr,
        )


def test_readiness_probe_harness_observes_boundary_guard_mutation(tmp_path):
    probe = _read_probe()
    assert "inside(spec.origin, package)" in probe
    mutated = probe.replace("inside(spec.origin, package)", "True", 1)
    result = _run_probe(
        _stage_probe_repo(tmp_path / "mutated"),
        "bad_origin",
        mutated,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)


def test_install_failure_removes_stale_positive_binding(tmp_path):
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    assert _run(repo).returncode == 0
    (repo / ".ready").unlink()
    (repo / ".install_fail").touch()
    result = _run(repo)
    assert result.returncode == 2
    assert BEGIN not in _session(repo)


# --- PRD-301: lock-carrier migration, reclamation, temp lifecycle -----------------------

_FAST_WAIT = {"DEV_BOOTSTRAP_LOCK_TRIES": "3", "DEV_BOOTSTRAP_LOCK_SLEEP": "0.02"}


def _dead_pid() -> int:
    """A pid that is certainly not live: spawn a trivial process and reap it."""
    proc = subprocess.Popen(["true"])
    proc.wait()
    return proc.pid


def test_dead_and_malformed_legacy_dir_locks_are_reclaimed(tmp_path):
    # Steady-state migration: a pre-upgrade DIRECTORY with a dead or malformed pid is
    # reclaimed automatically and the run proceeds.
    for kind, contents in (("dead", f"{_dead_pid()}\n"), ("malformed", "not-a-pid\n")):
        repo = _mkrepo(tmp_path / kind, with_venv=True, ready=True)
        lock = repo / ".dev_bootstrap.lock"
        lock.mkdir()
        (lock / "pid").write_text(contents)
        result = _run(repo)
        assert result.returncode == 0, (kind, result.stderr)
        assert not lock.exists(), kind
        assert _session(repo).count(BEGIN) == 1


def test_pid_less_legacy_dir_is_never_reclaimed_and_fails_loud(tmp_path):
    # Owner ruling #3: a pid-less legacy DIRECTORY is never automatically moved/removed;
    # after the bounded wait the run fails loud with a specific rmdir (never rm -rf) recovery.
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    lock.mkdir()
    result = _run(repo, extra_env=_FAST_WAIT)
    assert result.returncode == 2
    assert "legacy lock directory without pid" in result.stderr
    assert "rmdir" in result.stderr and "rm -rf" not in result.stderr
    assert lock.is_dir()  # never moved or removed automatically
    assert not (lock / "pid").exists()


def test_live_pid_legacy_dir_is_never_reclaimed(tmp_path):
    # A legacy DIRECTORY owned by a LIVE process is never reclaimed; a new-version process
    # never acquires the canonical lock while that live owner is recognized.
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    lock.mkdir()
    holder = subprocess.Popen(["sleep", "30"])
    try:
        (lock / "pid").write_text(f"{holder.pid}\n")
        result = _run(repo, extra_env=_FAST_WAIT)
        assert result.returncode == 2  # generic contention timeout, not the pid-less path
        assert "legacy lock directory without pid" not in result.stderr
        assert lock.is_dir() and (lock / "pid").read_text().strip() == str(holder.pid)
    finally:
        holder.terminate()
        holder.wait()


def test_pid_appearing_during_wait_changes_the_result(tmp_path):
    # Ruling #4: a pid appearing during the bounded wait changes the outcome. Start with a
    # pid-less legacy directory, then drop a DEAD pid into it while the run waits; the run
    # re-checks, reclaims the now-dead-pid directory, and proceeds instead of failing loud.
    import threading
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    lock.mkdir()
    dead = _dead_pid()

    def _drop_pid():
        time.sleep(0.05)
        (lock / "pid").write_text(f"{dead}\n")

    writer = threading.Thread(target=_drop_pid)
    writer.start()
    try:
        result = _run(repo, extra_env={"DEV_BOOTSTRAP_LOCK_TRIES": "80", "DEV_BOOTSTRAP_LOCK_SLEEP": "0.02"})
        assert result.returncode == 0, result.stderr
        assert "legacy lock directory without pid" not in result.stderr
        assert not lock.exists()
    finally:
        writer.join()


def test_file_lock_reclaims_dead_malformed_and_empty_pid(tmp_path):
    # Steady-state (post-migration) FILE lock: a dead, malformed, or empty pid is reclaimed.
    for kind, contents in (("dead", f"{_dead_pid()}\n"), ("malformed", "not-a-pid\n"), ("empty", "")):
        repo = _mkrepo(tmp_path / kind, with_venv=True, ready=True)
        lock = repo / ".dev_bootstrap.lock"
        lock.write_text(contents)  # a FILE, not a directory
        result = _run(repo, extra_env=_FAST_WAIT)
        assert result.returncode == 0, (kind, result.stderr)
        assert _session(repo).count(BEGIN) == 1


def test_dead_owner_acquisition_temp_is_swept_live_is_not(tmp_path):
    # Ruling #2/#4: a later run sweeps acquisition temps owned by DEAD pids and never a
    # live contender's temp; no permanently unowned artifact remains.
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    dead_temp = repo / f".dev_bootstrap.lock.new.{_dead_pid()}.aBcDeF"
    dead_temp.write_text("stale\n")
    holder = subprocess.Popen(["sleep", "30"])
    live_temp = repo / f".dev_bootstrap.lock.new.{holder.pid}.zZzZzZ"
    live_temp.write_text(f"{holder.pid}\n")
    try:
        result = _run(repo)
        assert result.returncode == 0, result.stderr
        assert not dead_temp.exists()  # dead-owner temp swept
        assert live_temp.exists()  # live contender's temp preserved
    finally:
        holder.terminate()
        holder.wait()
    live_temp.unlink(missing_ok=True)


def test_pid_zero_lock_is_reclaimed_not_treated_as_live(tmp_path):
    # `kill -0 0` probes the caller's process group and succeeds; a lock holding pid 0 must
    # be treated as malformed/dead and reclaimed, not mistaken for a live owner.
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    lock.write_text("0\n")
    result = _run(repo, extra_env=_FAST_WAIT)
    assert result.returncode == 0, result.stderr
    assert _session(repo).count(BEGIN) == 1


def test_sweep_parses_pid_by_literal_prefix_not_first_new_in_path(tmp_path):
    # The repo path itself contains ".new."; a live contender's temp must not be mis-parsed
    # (first ".new." in the parent path) and wrongly swept.
    repo = _mkrepo(tmp_path / "a.new.b", with_venv=True, ready=True)
    holder = subprocess.Popen(["sleep", "30"])
    live_temp = repo / f".dev_bootstrap.lock.new.{holder.pid}.zZzZzZ"
    live_temp.write_text(f"{holder.pid}\n")
    try:
        result = _run(repo)
        assert result.returncode == 0, result.stderr
        assert live_temp.exists()  # correct literal-prefix parse keeps the live temp
    finally:
        holder.terminate()
        holder.wait()
    live_temp.unlink(missing_ok=True)


def test_sigkill_holder_lock_is_reclaimed_on_next_run(tmp_path):
    # Post-acquisition SIGKILL leaves a file lock with a dead pid; the next run reclaims it.
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    lock.write_text(f"{_dead_pid()}\n")  # a holder acquired then was SIGKILLed
    stray_temp = repo / f".dev_bootstrap.lock.new.{_dead_pid()}.kkkkkk"
    stray_temp.write_text("orphan\n")
    result = _run(repo, extra_env=_FAST_WAIT)
    assert result.returncode == 0, result.stderr
    assert not lock.exists()  # dead-pid file lock reclaimed, then released by the new owner
    assert not stray_temp.exists()
    assert _session(repo).count(BEGIN) == 1


# Barrier shim for the exact-pathname `link` COMMAND (the ratified acquisition + reclaim
# primitive). Pauses the acquisition link (temp -> $LOCKFILE) or the RECLAIM_LOCK link
# (temp -> $LOCKFILE.reclaim) deterministically; all other link calls pass through.
FAKE_LINK = r"""#!/usr/bin/env bash
real_link=/usr/bin/link; [ -x "$real_link" ] || real_link=/bin/link
_pause() { touch "$LINK_BARRIER_DIR/reached"; while [ ! -e "$LINK_BARRIER_DIR/go" ]; do sleep 0.01; done; }
if [ -n "${LINK_BARRIER_DIR:-}" ] && [ -d "${LINK_BARRIER_DIR}" ]; then
  case "${1:-}::${2:-}" in
    *.dev_bootstrap.lock.new.*::*.dev_bootstrap.lock.reclaim)
      # reclaimer: acquire RECLAIM_LOCK FIRST, then pause while holding it
      if [ -n "${LINK_BARRIER_RECLAIM:-}" ]; then "$real_link" "$@"; rc=$?; _pause; exit "$rc"; fi
      ;;
    *.dev_bootstrap.lock.new.*::*.dev_bootstrap.lock)
      # pause BEFORE publishing so a test observes that no lock is visible yet
      [ -n "${LINK_BARRIER_ACQUIRE:-}" ] && _pause
      # publish FIRST, then pause, so a test observes the just-published lock already holds the pid
      if [ -n "${LINK_BARRIER_POST_ACQUIRE:-}" ]; then "$real_link" "$@"; rc=$?; _pause; exit "$rc"; fi
      ;;
  esac
fi
exec "$real_link" "$@"
"""


def _wait_for_barrier(proc, marker, *, timeout=30.0):
    # Wait until the shimmed child touches `marker`, OR the bootstrap process exits early. On
    # early exit, surface its stdout/stderr so a CI-only divergence is diagnosable rather than an
    # opaque "never reached". Generous timeout for loaded CI runners; local hits are sub-second.
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if marker.exists():
            return
        if proc.poll() is not None:
            out, err = proc.communicate()
            raise AssertionError(
                f"bootstrap exited (rc={proc.returncode}) before reaching barrier {marker}\n"
                f"--- stdout ---\n{out}\n--- stderr ---\n{err}"
            )
        time.sleep(0.02)
    raise AssertionError(f"barrier {marker} not reached within {timeout}s (bootstrap still running)")


def test_owner_paused_before_link_publishes_no_incomplete_lock_and_never_steals(tmp_path):
    # Atomic publication (FINAL RATIFIED DIRECTION item 1): an owner paused after its pid-temp is
    # written but before the exact-pathname `link` exposes no incomplete authoritative lock;
    # another process may acquire; the paused owner then waits and acquires cleanly (never
    # stealing). Deterministic via a `link` barrier.
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    (repo / "session.sh").write_text("# user content\n")
    lock = repo / ".dev_bootstrap.lock"
    barrier = repo / "barrier"
    barrier.mkdir()
    shimbin = repo / "shimbin"
    shimbin.mkdir()
    _write_executable(shimbin / "link", FAKE_LINK)

    env_a = _env(repo, repo / "session.sh")
    env_a["PATH"] = f"{shimbin}:{env_a['PATH']}"
    env_a["LINK_BARRIER_DIR"] = str(barrier)
    env_a["LINK_BARRIER_ACQUIRE"] = "1"
    proc_a = subprocess.Popen(
        ["bash", str(repo / "scripts" / "dev_bootstrap.sh")],
        cwd=repo, env=env_a, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        _wait_for_barrier(proc_a, barrier / "reached")
        # INVARIANT: no incomplete authoritative lock is visible while the owner is paused.
        assert not lock.exists()
        # Another process acquires cleanly while A is paused, and fully releases.
        result_b = _run(repo)
        assert result_b.returncode == 0, result_b.stderr
    finally:
        (barrier / "go").touch()
    out_a = proc_a.communicate(timeout=60)
    assert proc_a.returncode == 0, out_a  # A waited, then acquired cleanly -- never stole
    content = _session(repo)
    assert content.count(BEGIN) == 1 and content.count(END) == 1
    assert "# user content\n" in content


def test_serialized_reclaimer_never_unlinks_a_fresh_live_owner(tmp_path):
    # Ratified RECLAIM_LOCK serialization (FINAL RATIFIED DIRECTION item 2; supersedes the
    # pre-amendment `-ef` inode-capture test). A reclaimer removes $LOCKFILE only inside the
    # RECLAIM_LOCK critical section and only if the CURRENT lock pid is dead/absent. If a fresh
    # LIVE owner takes the canonical path while the reclaimer holds RECLAIM_LOCK, the reclaimer
    # reads the live pid and leaves the lock intact -- never steals. Deterministic via a
    # RECLAIM_LOCK `link` barrier.
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    reclaim = repo / ".dev_bootstrap.lock.reclaim"
    lock.write_text(f"{_dead_pid()}\n")  # a dead FILE lock present -> triggers reclaim
    barrier = repo / "barrier"
    barrier.mkdir()
    shimbin = repo / "shimbin"
    shimbin.mkdir()
    _write_executable(shimbin / "link", FAKE_LINK)

    env_c = _env(repo, repo / "session.sh")
    env_c["PATH"] = f"{shimbin}:{env_c['PATH']}"
    env_c["LINK_BARRIER_DIR"] = str(barrier)
    env_c["LINK_BARRIER_RECLAIM"] = "1"
    env_c.update(_FAST_WAIT)
    proc_c = subprocess.Popen(
        ["bash", str(repo / "scripts" / "dev_bootstrap.sh")],
        cwd=repo, env=env_c, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    new_owner = subprocess.Popen(["sleep", "30"])
    try:
        _wait_for_barrier(proc_c, barrier / "reached")
        assert reclaim.exists(), "reclaimer does not hold RECLAIM_LOCK at the barrier"
        # A NEW live owner takes the canonical path while the reclaimer is paused holding
        # RECLAIM_LOCK. The serialized critical section reads the CURRENT (now live) pid.
        lock.unlink()
        lock.write_text(f"{new_owner.pid}\n")
        (barrier / "go").touch()
        out_c = proc_c.communicate(timeout=60)
        # The live owner's lock is left intact; the reclaimer never unlinks a live owner.
        assert lock.exists() and lock.read_text().strip() == str(new_owner.pid), out_c
        # The reclaimer released RECLAIM_LOCK (no orphaned mutex from a clean exit).
        assert not reclaim.exists(), out_c
    finally:
        (barrier / "go").touch()
        new_owner.terminate()
        new_owner.wait()
        try:
            proc_c.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc_c.kill()


def test_concurrent_ready_starts_are_deterministically_serialized_under_stress(tmp_path):
    # Non-flaky guard: many rounds of concurrent ready starts must all exit 0 with exactly
    # one owned block. Reverting atomic publication (mkdir + later pid) reintroduces the
    # ownership-theft race and turns this red across rounds.
    for round_index in range(12):
        repo = _mkrepo(tmp_path / f"r{round_index}", with_venv=True, ready=True)
        (repo / "session.sh").write_text("# user content\n")
        env = _env(repo, repo / "session.sh")
        procs = [
            subprocess.Popen(
                ["bash", str(repo / "scripts" / "dev_bootstrap.sh")],
                cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            for _ in range(4)
        ]
        results = [p.communicate(timeout=60) for p in procs]
        assert all(p.returncode == 0 for p in procs), (round_index, results)
        content = _session(repo)
        assert content.count(BEGIN) == 1 and content.count(END) == 1


def test_concurrent_ready_starts_serialize_env_publication(tmp_path):
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    session = repo / "session.sh"
    session.write_text("# user content\n")
    env = _env(repo, session)
    processes = [
        subprocess.Popen(
            ["bash", str(repo / "scripts" / "dev_bootstrap.sh")],
            cwd=repo,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(4)
    ]
    results = [process.communicate(timeout=60) for process in processes]
    assert all(process.returncode == 0 for process in processes), results
    assert _calls(repo).count("pip\n") == 0
    content = _session(repo)
    assert content.count(BEGIN) == 1
    assert content.count(END) == 1
    assert "# user content\n" in content


def test_atomic_replacement_preserves_marker_collisions_and_unrelated_content(
    tmp_path,
):
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    session = repo / "session.sh"
    collision = f"{BEGIN}\nthis is user text\n{END}\n"
    session.write_text(
        "before\n"
        + collision
        + "between\n"
        + _owned_block(repo) * 2
        + "after\n"
    )
    result = _run(repo)
    assert result.returncode == 0, result.stderr
    content = session.read_text()
    assert collision in content
    assert "before\n" in content and "between\n" in content and "after\n" in content
    assert content.count(BEGIN) == 2
    assert content.count(END) == 2


def test_unwritable_env_publication_is_a_failure_not_false_success(tmp_path):
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    impossible = repo / "missing-parent" / "session.sh"
    result = _run(repo, claude_env=impossible)
    assert result.returncode == 2
    assert "CLAUDE_ENV_FILE publish" in result.stderr
    assert not impossible.exists()


def test_symlinked_venv_is_not_replaced(tmp_path):
    repo = _mkrepo(tmp_path, with_venv=False, ready=False)
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / "bin").mkdir(parents=True)
    _write_executable(elsewhere / "bin" / "python", FAKE_VENV_PY)
    (repo / ".venv").symlink_to(elsewhere)
    result = _run(repo)
    assert result.returncode == 2
    assert (repo / ".venv").is_symlink()


def test_human_run_does_not_mutate_an_env_file(tmp_path):
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    result = _run(repo, claude_env=None)
    assert result.returncode == 0
    assert ".venv/bin" in result.stdout
    assert not (repo / "session.sh").exists()


def test_settings_adds_only_required_sessionstart_hook():
    settings = json.loads(SETTINGS.read_text())
    session_start = settings["hooks"]["SessionStart"]
    assert len(session_start) == 1
    assert session_start[0]["matcher"] == "startup|resume|clear|fork"
    hook = session_start[0]["hooks"][0]
    assert hook["command"].endswith("bash scripts/dev_bootstrap.sh")
    assert hook["timeout"] == 300
    assert set(settings["hooks"]) == {
        "PreToolUse",
        "UserPromptSubmit",
        "SessionStart",
    }
    assert len(settings["hooks"]["PreToolUse"]) == 3
    assert "Bash(gh pr merge:*)" in settings["permissions"]["deny"]
    assert "Bash(gh pr ready*)" not in settings["permissions"]["deny"]


# --- PRD-301 AMENDMENT 1 (PATH-B) ratified-mechanism tests ---

# mv shim: inject a non-pid child into the legacy lock directory right before it is renamed to
# its .stale. grave -- models a false-acquisition child arriving AFTER the ls -A snapshot and
# BEFORE the move, so the authoritative post-move rmdir must fail loud. Other mv calls pass.
FAKE_MV_INJECT = r"""#!/usr/bin/env bash
real_mv=/usr/bin/mv; [ -x "$real_mv" ] || real_mv=/bin/mv
dst="${@: -1}"; src="${@: -2:1}"
case "$dst" in
  *.dev_bootstrap.lock.stale.*) [ -d "$src" ] && : >"$src/stray" ;;
esac
exec "$real_mv" "$@"
"""


def _shim_path(repo: Path, shimbin: Path, session: Path) -> dict[str, str]:
    base = _env(repo, session)
    return {"PATH": f"{shimbin}:{base['PATH']}"}


def test_post_move_retained_grave_fails_loud_and_does_no_bootstrap_work(tmp_path):
    # FINAL RATIFIED DIRECTION items 5 and 7: a non-pid child arriving after the ls -A snapshot
    # and before the mv is carried into the grave; the AUTHORITATIVE post-move rmdir fails, the
    # run fails loud (exit 2) naming the retained inspectable grave, never recommends rm -rf, and
    # does NO bootstrap work or env publication. Deterministic via an mv-injection shim.
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    lock.mkdir()  # legacy DIRECTORY carrier
    (lock / "pid").write_text(f"{_dead_pid()}\n")  # dead pid -> eligible for reclaim
    session = repo / "session.sh"
    session.write_text("# user content\n")
    shimbin = repo / "shimbin"
    shimbin.mkdir()
    _write_executable(shimbin / "mv", FAKE_MV_INJECT)
    result = _run(repo, extra_env={**_FAST_WAIT, **_shim_path(repo, shimbin, session)})
    assert result.returncode == 2, result
    assert "legacy grave retained" in result.stderr, result.stderr
    assert "never rm -rf" in result.stderr  # warns against, never recommends, rm -rf
    graves = list(repo.glob(".dev_bootstrap.lock.stale.*"))
    assert len(graves) == 1 and (graves[0] / "stray").exists(), (result, graves)
    # No bootstrap work / env publication after the retained-grave failure.
    assert "ready" not in result.stdout and "bootstrapped" not in result.stdout
    assert _session(repo) == "# user content\n"
    assert BEGIN not in _session(repo)


def test_clean_exit_emits_no_spurious_reclaim_lock_stderr(tmp_path):
    # FINAL RATIFIED DIRECTION item 8: a normal run never creates RECLAIM_LOCK, and the
    # existence-guarded EXIT read must NOT emit a spurious "No such file or directory".
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    result = _run(repo)
    assert result.returncode == 0, result.stderr
    assert "No such file or directory" not in result.stderr
    assert ".reclaim" not in result.stderr


def test_stale_foreign_reclaim_lock_fails_loud_and_is_never_removed(tmp_path):
    # FINAL RATIFIED DIRECTION items 3 and 4: a foreign RECLAIM_LOCK (another live pid) is NEVER
    # auto-stolen -- the run bounded-waits then fails loud with the manual `rm` instruction, and
    # the PID-identity EXIT trap leaves the foreign reclaim lock intact (removes only its own).
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    lock.write_text(f"{_dead_pid()}\n")  # dead file lock -> triggers reclaim attempts
    reclaim = repo / ".dev_bootstrap.lock.reclaim"
    foreign = subprocess.Popen(["sleep", "30"])  # a live foreign pid
    reclaim.write_text(f"{foreign.pid}\n")
    try:
        result = _run(repo, extra_env=_FAST_WAIT)
        assert result.returncode == 2, result
        assert "stale reclaim lock" in result.stderr, result.stderr
        assert "rm -f" in result.stderr and ".reclaim" in result.stderr
        assert "rm -rf" not in result.stderr
        assert reclaim.exists() and reclaim.read_text().strip() == str(foreign.pid), result
    finally:
        foreign.terminate()
        foreign.wait()


def test_terminated_reclaimer_does_not_orphan_its_reclaim_lock(tmp_path):
    # FINAL RATIFIED DIRECTION item 3: a reclaimer holding its OWN RECLAIM_LOCK that is TERM'd
    # does not orphan it -- the caught-signal / EXIT path removes its own reclaim lock.
    import signal

    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    reclaim = repo / ".dev_bootstrap.lock.reclaim"
    lock.write_text(f"{_dead_pid()}\n")
    barrier = repo / "barrier"
    barrier.mkdir()
    shimbin = repo / "shimbin"
    shimbin.mkdir()
    _write_executable(shimbin / "link", FAKE_LINK)
    base = _env(repo, repo / "session.sh")
    env = {
        **base,
        "PATH": f"{shimbin}:{base['PATH']}",
        "LINK_BARRIER_DIR": str(barrier),
        "LINK_BARRIER_RECLAIM": "1",
        **_FAST_WAIT,
    }
    proc = subprocess.Popen(
        ["bash", str(repo / "scripts" / "dev_bootstrap.sh")],
        cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        _wait_for_barrier(proc, barrier / "reached")
        assert reclaim.exists()  # it holds its own RECLAIM_LOCK
        proc.send_signal(signal.SIGTERM)
        (barrier / "go").touch()  # release the paused link child so the pending trap can run
        proc.wait(timeout=30)
        assert not reclaim.exists(), "TERM'd reclaimer orphaned its own RECLAIM_LOCK"
    finally:
        (barrier / "go").touch()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_live_legacy_dir_is_never_linked_into(tmp_path):
    # FINAL RATIFIED DIRECTION items 1 and 5: the exact-pathname `link` acquisition never links a
    # temp INSIDE a legacy directory (the pre-amendment `ln` bug). A live-pid legacy directory is
    # routed by [ -d ] and waited on; no `.new.*` child is ever created inside it.
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    lock.mkdir()
    live = subprocess.Popen(["sleep", "30"])
    (lock / "pid").write_text(f"{live.pid}\n")
    try:
        result = _run(repo, extra_env=_FAST_WAIT)
        assert result.returncode == 2, result  # live legacy owner -> contention fail, never steal
        children = [p.name for p in lock.iterdir()]
        assert children == ["pid"], children  # no acquisition temp linked inside the directory
        assert (lock / "pid").read_text().strip() == str(live.pid)  # live owner untouched
    finally:
        live.terminate()
        live.wait()


# link shim: create a directory at $LOCKFILE ONCE, immediately before the real acquisition link,
# to model a legacy directory appearing AFTER the [ -d ] test but at the instant of acquisition.
FAKE_LINK_DIR_INJECT = r"""#!/usr/bin/env bash
real_link=/usr/bin/link; [ -x "$real_link" ] || real_link=/bin/link
case "${1:-}::${2:-}" in
  *.dev_bootstrap.lock.new.*::*.dev_bootstrap.lock)
    if [ -n "${DIR_INJECT_DIR:-}" ] && [ ! -e "$DIR_INJECT_DIR/done" ]; then
      mkdir "$2" 2>/dev/null && touch "$DIR_INJECT_DIR/done"
    fi
    ;;
esac
exec "$real_link" "$@"
"""


def test_legacy_dir_appearing_at_acquisition_is_never_linked_into(tmp_path):
    # FINAL RATIFIED DIRECTION items 1 and 5 (kills the exact-path link mutation): if a legacy
    # directory appears at $LOCKFILE exactly when acquisition runs (after the [ -d ] test),
    # exact-pathname `link` FAILS EEXIST and links NO child inside it -- the pre-amendment `ln`
    # would link a temp INSIDE the directory (a false acquisition). The run then routes the
    # now-pid-less directory to the bounded-wait-then-fail-loud path.
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    marker = repo / "inject"
    marker.mkdir()
    shimbin = repo / "shimbin"
    shimbin.mkdir()
    _write_executable(shimbin / "link", FAKE_LINK_DIR_INJECT)
    base = _env(repo, repo / "session.sh")
    env = {**base, "PATH": f"{shimbin}:{base['PATH']}", "DIR_INJECT_DIR": str(marker), **_FAST_WAIT}
    result = subprocess.run(
        ["bash", str(repo / "scripts" / "dev_bootstrap.sh")],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert lock.is_dir(), result  # the injected directory is present at $LOCKFILE
    assert list(lock.iterdir()) == [], (result, [c.name for c in lock.iterdir()])  # no child linked in
    assert result.returncode == 2, result  # pid-less legacy directory -> bounded-wait then fail loud


def test_published_lock_already_contains_owner_pid(tmp_path):
    # FINAL RATIFIED DIRECTION item 1 (kills the pid-written-after-link mutation): the instant
    # $LOCKFILE becomes visible it ALREADY holds the owner pid -- the pid is written to the temp
    # BEFORE `link`, and `link` makes the lock a hardlink to that already-populated inode, so there
    # is no pid-less publication window. Deterministic via a post-acquisition link barrier that
    # pauses AFTER the real link. (The pre-link no-lock test alone green-passes a mutation that
    # writes the pid after the link.)
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    barrier = repo / "barrier"
    barrier.mkdir()
    shimbin = repo / "shimbin"
    shimbin.mkdir()
    _write_executable(shimbin / "link", FAKE_LINK)
    base = _env(repo, repo / "session.sh")
    env = {
        **base,
        "PATH": f"{shimbin}:{base['PATH']}",
        "LINK_BARRIER_DIR": str(barrier),
        "LINK_BARRIER_POST_ACQUIRE": "1",
        **_FAST_WAIT,
    }
    proc = subprocess.Popen(
        ["bash", str(repo / "scripts" / "dev_bootstrap.sh")],
        cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        _wait_for_barrier(proc, barrier / "reached")
        # The lock is now visible; it must ALREADY contain the owner pid (no pid-less window).
        assert lock.exists()
        assert lock.read_text().strip() == str(proc.pid), lock.read_text()
    finally:
        (barrier / "go").touch()
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_second_reclaimer_is_excluded_while_first_holds_reclaim_lock(tmp_path):
    # FINAL RATIFIED DIRECTION item 2 (kills the `link ... || :` serialization mutation): while a
    # reclaimer A holds RECLAIM_LOCK, a second REAL reclaimer B cannot enter the critical section --
    # B's RECLAIM_LOCK link fails EEXIST and B bails (return 1), so the dead primary lock is
    # untouched until A runs. A weakened `link ... || :` would let B proceed and evict the dead lock
    # while A is paused. Deterministic: A pauses AFTER a successful RECLAIM_LOCK link; B is a real
    # unshimmed bootstrap.
    repo = _mkrepo(tmp_path, with_venv=True, ready=True)
    lock = repo / ".dev_bootstrap.lock"
    reclaim = repo / ".dev_bootstrap.lock.reclaim"
    dead = _dead_pid()
    lock.write_text(f"{dead}\n")  # dead primary lock -> triggers reclaim
    barrier = repo / "barrier"
    barrier.mkdir()
    shimbin = repo / "shimbin"
    shimbin.mkdir()
    _write_executable(shimbin / "link", FAKE_LINK)
    base = _env(repo, repo / "session.sh")
    env_a = {
        **base,
        "PATH": f"{shimbin}:{base['PATH']}",
        "LINK_BARRIER_DIR": str(barrier),
        "LINK_BARRIER_RECLAIM": "1",
        **_FAST_WAIT,
    }
    proc_a = subprocess.Popen(
        ["bash", str(repo / "scripts" / "dev_bootstrap.sh")],
        cwd=repo, env=env_a, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        _wait_for_barrier(proc_a, barrier / "reached")
        assert reclaim.exists()  # A holds RECLAIM_LOCK
        # A second REAL (unshimmed) reclaimer B runs while A holds RECLAIM_LOCK; B must be excluded.
        result_b = _run(repo, extra_env=_FAST_WAIT)
        assert result_b.returncode == 2, result_b  # B bounded-waits then fails loud (stale reclaim lock)
        assert "stale reclaim lock" in result_b.stderr, result_b.stderr
        # B never entered the critical section: the dead primary lock is untouched.
        assert lock.exists() and lock.read_text().strip() == str(dead), (
            result_b, lock.read_text() if lock.exists() else "GONE",
        )
    finally:
        (barrier / "go").touch()
        try:
            proc_a.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc_a.kill()
