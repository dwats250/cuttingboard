"""PRD-293 (QW-5): mutation-discriminating tests for the dev-bootstrap script and
the SessionStart settings addition. Fully isolated -- temp repos + fake
executables, NO network, no real venv/pip. The fake `.venv/bin/python`
dispatches on argv to simulate readiness / identity / install so the script's
ORCHESTRATION (readiness gate, lock serialization, install-once, transactional
CLAUDE_ENV_FILE binding, fail-loud) is exercised without real interpreters."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "dev_bootstrap.sh"
SETTINGS = REPO / ".claude" / "settings.json"

# Fake `.venv/bin/python`: derives repo root from its own path; dispatches on argv.
FAKE_VENV_PY = r"""#!/usr/bin/env bash
R="$(cd "$(dirname "$0")/../.." && pwd)"
printf 'PYTHONPATH=[%s]\n' "${PYTHONPATH-UNSET}" >> "$R/env.log"
case "$*" in
  *tomllib*|*direct_url*|*cuttingboard*) [ -f "$R/.ready" ] && exit 0 || exit 1 ;;
  *sys.prefix*) [ -f "$R/.broken" ] && exit 1 || exit 0 ;;
  *"-m pip"*install*) echo pip >> "$R/calls.log"; [ -f "$R/.install_fail" ] && exit 1; touch "$R/.ready"; exit 0 ;;
  *"-m pytest"*) exit 0 ;;
esac
exit 0
"""
# Fake base `python3`/`python` (on PATH): version/venv ok; `-m venv` builds a fake venv.
FAKE_BASE_PY = r"""#!/usr/bin/env bash
case "$*" in
  *"import sys; sys.exit(0 if sys.version_info"*) exit 0 ;;
  *"import venv"*) exit 0 ;;
  *"-m venv"*) v="${@: -1}"; mkdir -p "$v/bin"; cp "$FAKE_VENV_PY_SRC" "$v/bin/python"; chmod +x "$v/bin/python"; echo venv >> "$FAKE_CALLS"; exit 0 ;;
esac
exit 0
"""


def _mkrepo(tmp: Path, *, with_venv: bool, ready: bool) -> Path:
    r = tmp
    (r / "scripts").mkdir(parents=True)
    (r / "scripts" / "dev_bootstrap.sh").write_text(SCRIPT.read_text())
    os.chmod(r / "scripts" / "dev_bootstrap.sh", 0o755)
    (r / "pyproject.toml").write_text('[project]\nname="cuttingboard"\n')
    (r / "cuttingboard").mkdir()
    (r / "cuttingboard" / "__init__.py").write_text("")
    fv = r / "fake_venv_python"
    fv.write_text(FAKE_VENV_PY)
    os.chmod(fv, 0o755)
    fb = r / "fakebin"
    fb.mkdir()
    (fb / "python3").write_text(FAKE_BASE_PY)
    (fb / "python").write_text(FAKE_BASE_PY)
    for n in ("python3", "python"):
        os.chmod(fb / n, 0o755)
    if with_venv:
        (r / ".venv" / "bin").mkdir(parents=True)
        (r / ".venv" / "bin" / "python").write_text(FAKE_VENV_PY)
        os.chmod(r / ".venv" / "bin" / "python", 0o755)
    if ready:
        (r / ".ready").touch()
    return r


def _run(r: Path, *, claude_env=True, extra_env=None):
    env = {
        "PATH": f"{r/'fakebin'}:{os.environ['PATH']}",
        "FAKE_VENV_PY_SRC": str(r / "fake_venv_python"),
        "FAKE_CALLS": str(r / "calls.log"),
        "HOME": str(r),
        "PYTHONPATH": "/junk/should/be/unset",
        "PYTHONHOME": "/junk",
    }
    if claude_env:
        env["CLAUDE_ENV_FILE"] = str(r / "session.sh")
        (r / "session.sh").write_text("# pre-existing\n")
    if extra_env:
        env.update(extra_env)
    p = subprocess.run(["bash", str(r / "scripts" / "dev_bootstrap.sh")],
                       capture_output=True, text=True, env=env, cwd=str(r), timeout=60)
    calls = (r / "calls.log").read_text() if (r / "calls.log").exists() else ""
    sess = (r / "session.sh").read_text() if (r / "session.sh").exists() else ""
    return p.returncode, p.stdout, p.stderr, calls, sess


def test_ready_is_noop_and_binds(tmp_path):
    r = _mkrepo(tmp_path, with_venv=True, ready=True)
    rc, out, err, calls, sess = _run(r)
    assert rc == 0, err
    assert "pip" not in calls, "ready env must not invoke pip"
    assert sess.count(">>> dev_bootstrap") == 1 and "export VIRTUAL_ENV=" in sess


def test_not_ready_installs_once_and_binds(tmp_path):
    r = _mkrepo(tmp_path, with_venv=False, ready=False)
    rc, out, err, calls, sess = _run(r)
    assert rc == 0, err
    assert calls.count("pip") == 1, "exactly one install"
    assert sess.count(">>> dev_bootstrap") == 1


def test_install_failure_exits_2_and_no_binding(tmp_path):
    r = _mkrepo(tmp_path, with_venv=False, ready=False)
    (r / ".install_fail").touch()
    rc, out, err, calls, sess = _run(r)
    assert rc == 2 and "FAIL" in err
    assert ">>> dev_bootstrap" not in sess, "no success binding on failure"


def test_env_binding_idempotent_no_duplicates(tmp_path):
    r = _mkrepo(tmp_path, with_venv=True, ready=True)
    _run(r)
    _, _, _, _, sess = _run(r)
    assert sess.count(">>> dev_bootstrap") == 1, "no duplicate blocks across runs"


def test_success_then_failure_removes_stale_binding(tmp_path):
    r = _mkrepo(tmp_path, with_venv=True, ready=True)
    _, _, _, _, sess1 = _run(r)
    assert ">>> dev_bootstrap" in sess1
    # now make the next run fail its post-install probe: not ready + install "succeeds"
    (r / ".ready").unlink()
    (r / ".install_fail").touch()
    rc, out, err, calls, sess2 = _run(r)
    assert rc == 2
    assert ">>> dev_bootstrap" not in sess2, "stale success binding must be removed on later failure"


def test_concurrent_starts_single_install(tmp_path):
    r = _mkrepo(tmp_path, with_venv=False, ready=False)
    env = {
        "PATH": f"{r/'fakebin'}:{os.environ['PATH']}",
        "FAKE_VENV_PY_SRC": str(r / "fake_venv_python"),
        "FAKE_CALLS": str(r / "calls.log"),
        "HOME": str(r), "CLAUDE_ENV_FILE": str(r / "session.sh"),
    }
    (r / "session.sh").write_text("")
    procs = [subprocess.Popen(["bash", str(r / "scripts" / "dev_bootstrap.sh")],
             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, cwd=str(r)) for _ in range(3)]
    for p in procs:
        p.wait(timeout=60)
    calls = (r / "calls.log").read_text() if (r / "calls.log").exists() else ""
    assert calls.count("pip") == 1, f"lock must serialize to one install, got {calls.count('pip')}"


def test_broken_symlinked_venv_fails_without_delete(tmp_path):
    r = _mkrepo(tmp_path, with_venv=False, ready=False)
    other = tmp_path / "elsewhere"
    (other / "bin").mkdir(parents=True)
    (other / "bin" / "python").write_text(FAKE_VENV_PY)
    os.chmod(other / "bin" / "python", 0o755)
    (r / ".venv").symlink_to(other)  # .venv is a symlink -> invalid
    rc, out, err, calls, sess = _run(r)
    assert rc == 2 and "FAIL" in err
    assert (r / ".venv").is_symlink(), "must not delete the venv"


def test_pollution_vars_unset_for_invocations(tmp_path):
    r = _mkrepo(tmp_path, with_venv=True, ready=True)
    _run(r)  # env passes PYTHONPATH=/junk; script must unset it
    envlog = (r / "env.log").read_text() if (r / "env.log").exists() else ""
    assert "PYTHONPATH=[UNSET]" in envlog or "PYTHONPATH=[]" in envlog, envlog


def test_human_run_prints_activation_no_binding(tmp_path):
    r = _mkrepo(tmp_path, with_venv=True, ready=True)
    rc, out, err, calls, sess = _run(r, claude_env=False)
    assert rc == 0
    assert ".venv/bin" in out


def test_settings_only_sessionstart_added():
    """Invariant 18: the shipped settings.json adds only hooks.SessionStart;
    permissions and existing hooks match a durable pinned baseline."""
    s = json.loads(SETTINGS.read_text())
    assert "SessionStart" in s["hooks"]
    ss = s["hooks"]["SessionStart"][0]
    assert ss["matcher"] == "startup|resume|clear|fork"
    assert ss["hooks"][0]["command"].endswith("bash scripts/dev_bootstrap.sh")
    assert ss["hooks"][0]["timeout"] == 300
    # pinned baseline invariants (durable, not origin/main):
    assert "Bash(gh pr merge:*)" in s["permissions"]["deny"]
    assert "Bash(gh pr ready*)" not in s["permissions"]["deny"]  # removed by PRD-291
    assert set(s["hooks"]) == {"PreToolUse", "UserPromptSubmit", "SessionStart"}
    assert len(s["hooks"]["PreToolUse"]) == 3
    # SessionStart is additive: dropping it leaves only the two prior hook events
    base = dict(s["hooks"])
    base.pop("SessionStart")
    assert set(base) == {"PreToolUse", "UserPromptSubmit"}
