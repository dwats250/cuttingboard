"""Functional tests for tools/prune_run_history.sh (PRD-195).

Each test builds a REAL git repo standing in for a publish worktree, seeds it
with timestamped logs/run_<ts>.json files (+ non-run logs/ files), runs the
prune against it, and asserts on what remains on disk and what is staged for
deletion. Commits set commit.gpgsign=false so the suite is hermetic regardless
of the host's commit-signing wrapper.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "prune_run_history.sh"

# Ascending in time -> ascending lexicographically (the property the prune relies on).
RUN_TS = [
    "2026-04-01_010101",
    "2026-04-15_090000",
    "2026-05-01_120000",
    "2026-05-02_120000",
    "2026-05-10_235959",
    "2026-05-20_000000",
    "2026-06-01_120000",
    "2026-06-10_080808",
]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )


def _seed(tmp_path: Path, run_ts: list[str], extras: tuple[str, ...] = ()) -> Path:
    repo = tmp_path / "wt"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    logs = repo / "logs"
    logs.mkdir()
    for ts in run_ts:
        (logs / f"run_{ts}.json").write_text("{}\n")
    for name in extras:
        (logs / name).write_text("{}\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed")
    return repo


def _prune(repo: Path, *extra: str, retain_env: str | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if retain_env is not None:
        env["CB_RUN_HISTORY_RETAIN"] = retain_env
    else:
        env.pop("CB_RUN_HISTORY_RETAIN", None)
    return subprocess.run(
        ["bash", str(SCRIPT), str(repo), *extra],
        capture_output=True, text=True, env=env,
    )


def _present_runs(repo: Path) -> list[str]:
    return sorted(p.name for p in (repo / "logs").glob("run_*.json"))


def _staged_deletions(repo: Path) -> list[str]:
    out = _git(repo, "diff", "--cached", "--name-status").stdout
    return sorted(line.split("\t", 1)[1] for line in out.splitlines()
                  if line.startswith("D\t"))


# --- core: prune the oldest beyond retain, keep the newest ----------------

def test_prunes_oldest_beyond_retain(tmp_path: Path) -> None:
    repo = _seed(tmp_path, RUN_TS)  # 8 files
    res = _prune(repo, "5")
    assert res.returncode == 0, res.stderr
    kept = _present_runs(repo)
    assert kept == [f"run_{ts}.json" for ts in RUN_TS[-5:]], kept
    # The 3 oldest are removed from disk AND staged as deletions for the commit.
    dropped = [f"logs/run_{ts}.json" for ts in RUN_TS[:3]]
    assert _staged_deletions(repo) == sorted(dropped)


def test_keeps_exactly_retain_count(tmp_path: Path) -> None:
    repo = _seed(tmp_path, RUN_TS)
    _prune(repo, "3")
    assert len(_present_runs(repo)) == 3
    assert _present_runs(repo) == [f"run_{ts}.json" for ts in RUN_TS[-3:]]


# --- no-op paths ----------------------------------------------------------

def test_noop_when_equal_to_retain(tmp_path: Path) -> None:
    repo = _seed(tmp_path, RUN_TS[:5])
    res = _prune(repo, "5")
    assert res.returncode == 0
    assert "nothing to prune" in res.stdout
    assert len(_present_runs(repo)) == 5
    assert _staged_deletions(repo) == []


def test_noop_when_below_retain(tmp_path: Path) -> None:
    repo = _seed(tmp_path, RUN_TS[:4])
    res = _prune(repo, "5")
    assert res.returncode == 0
    assert len(_present_runs(repo)) == 4


def test_noop_when_no_run_files(tmp_path: Path) -> None:
    repo = _seed(tmp_path, [], extras=("audit.jsonl",))
    res = _prune(repo, "5")
    assert res.returncode == 0
    assert "nothing to prune" in res.stdout
    assert _staged_deletions(repo) == []


# --- scope: only run_*.json is touched ------------------------------------

def test_non_run_logs_are_never_pruned(tmp_path: Path) -> None:
    extras = ("audit.jsonl", "latest_run.json", "regime_history.json",
              "macro_awareness_state.json")
    repo = _seed(tmp_path, RUN_TS, extras=extras)
    _prune(repo, "2")
    survivors = sorted(p.name for p in (repo / "logs").glob("*"))
    for name in extras:
        assert name in survivors, f"{name} must survive the prune"
    assert len([s for s in survivors if s.startswith("run_")]) == 2


# --- retain hardening -----------------------------------------------------

def test_non_numeric_retain_falls_back_to_default(tmp_path: Path) -> None:
    repo = _seed(tmp_path, RUN_TS)  # 8 < default 50 -> no-op
    res = _prune(repo, "not-a-number")
    assert res.returncode == 0
    assert "nothing to prune" in res.stdout
    assert len(_present_runs(repo)) == 8


def test_zero_retain_is_floored_to_one(tmp_path: Path) -> None:
    repo = _seed(tmp_path, RUN_TS)
    _prune(repo, "0")
    # Floored at 1 — never wipes the whole history; keeps the single newest.
    assert _present_runs(repo) == [f"run_{RUN_TS[-1]}.json"]


def test_env_var_override(tmp_path: Path) -> None:
    repo = _seed(tmp_path, RUN_TS)
    _prune(repo, retain_env="2")  # no positional arg -> env governs
    assert len(_present_runs(repo)) == 2
    assert _present_runs(repo) == [f"run_{ts}.json" for ts in RUN_TS[-2:]]


def test_positional_arg_beats_env(tmp_path: Path) -> None:
    repo = _seed(tmp_path, RUN_TS)
    _prune(repo, "3", retain_env="6")  # arg 3 wins over env 6
    assert len(_present_runs(repo)) == 3


# --- defensive ------------------------------------------------------------

def test_missing_worktree_arg_fails(tmp_path: Path) -> None:
    res = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True)
    assert res.returncode != 0
