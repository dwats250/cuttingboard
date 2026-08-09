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
    assert len(production) <= 235
    text = SCRIPT.read_text()
    assert "PIP_CONFIG_FILE=/dev/null" in text
    assert "--isolated install --no-cache-dir" in text
    assert 'mv -f "$tmp" "$CLAUDE_ENV_FILE"' in text
    assert '>>"$CLAUDE_ENV_FILE"' not in text


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


def test_dead_malformed_and_orphaned_locks_are_reclaimed(tmp_path):
    for kind, contents in (
        ("dead", "99999999\n"),
        ("malformed", "not-a-pid\n"),
        ("orphan", None),
    ):
        repo = _mkrepo(tmp_path / kind, with_venv=True, ready=True)
        lock = repo / ".dev_bootstrap.lock"
        lock.mkdir()
        if contents is not None:
            (lock / "pid").write_text(contents)
        result = _run(repo)
        assert result.returncode == 0, (kind, result.stderr)
        assert not lock.exists(), kind


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
