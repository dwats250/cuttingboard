"""PRD-339 Slice 1 (R5): publication non-regression. Unit tests on
``publication_admits`` (lexicographic authority_version gate, Q4 recovery M5c,
equal-version identity M5b) + a bounded OFFLINE replay of ci_push_artifacts.sh
against a temp bare remote (bootstrap/overlay/retry routes) with CROSSED-ORDER
fixtures whose generated_at + commit order disagree with authority_version,
proving the guard orders by authority_version, never a timestamp (M5)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from cuttingboard import effective_permission as ep

SD = "2026-04-12"
SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "ci_push_artifacts.sh"


def _env(**av):
    """A canonical envelope with the given authority_version fields."""
    return {
        "verdict": av.get("verdict", "NO_TRADE"),
        "restriction_rank": av["rank"], "decision_uid": av.get("uid", "LIVE-1"),
        "session_date": av["date"], "run_uid": av.get("run_uid", "r1"),
        "authority_version": [av["date"], av["seq"], av["rank"]],
        "valid_until": None, "recovery_basis": av.get("recovery_basis"),
        "permission_line": "x", "decision_seq": av["seq"],
    }


# --- unit: publication_admits (R5 a-d) ---------------------------------------

def test_bootstrap_admits_when_no_accepted() -> None:
    assert ep.publication_admits(None, _env(date=SD, seq=1, rank=1)) is True


def test_malformed_incoming_refused() -> None:
    assert ep.publication_admits(_env(date=SD, seq=1, rank=1), None) is False
    assert ep.publication_admits(_env(date=SD, seq=1, rank=1), {"x": 1}) is False


def test_older_session_and_older_decision_refused() -> None:
    acc = _env(date=SD, seq=2, rank=0)
    assert ep.publication_admits(acc, _env(date="2026-04-11", seq=9, rank=0)) is False  # older session
    assert ep.publication_admits(acc, _env(date=SD, seq=1, rank=0)) is False            # older decision


def test_intra_decision_downgrade_refused() -> None:
    acc = _env(date=SD, seq=1, rank=2)
    assert ep.publication_admits(acc, _env(date=SD, seq=1, rank=1, uid="LIVE-1")) is False


def test_equal_version_same_decision_is_noop_admit() -> None:  # R5(d)
    e = _env(date=SD, seq=1, rank=1, uid="LIVE-1")
    assert ep.publication_admits(e, dict(e)) is True


def test_equal_version_differing_decision_refused() -> None:  # M5b
    acc = _env(date=SD, seq=1, rank=1, uid="LIVE-1")
    inc = _env(date=SD, seq=1, rank=1, uid="LIVE-DIFFERENT")
    assert ep.publication_admits(acc, inc) is False


def test_recovery_gated_downgrade_admitted() -> None:  # M5c
    acc = _env(date=SD, seq=1, rank=2)
    inc = _env(date=SD, seq=2, rank=0, uid="LIVE-2",
               recovery_basis={"superseded_authority_version": [SD, 1, 2],
                               "superseding_decision_uid": "LIVE-2", "reason": "REDECISION"})
    assert ep.publication_admits(acc, inc) is True


def test_non_recovery_downgrade_refused() -> None:  # M5c converse
    acc = _env(date=SD, seq=1, rank=2)
    inc = _env(date=SD, seq=2, rank=0, uid="LIVE-2", recovery_basis=None)
    assert ep.publication_admits(acc, inc) is False


def test_higher_decision_same_or_higher_rank_admitted() -> None:
    acc = _env(date=SD, seq=1, rank=0)
    assert ep.publication_admits(acc, _env(date=SD, seq=2, rank=1, uid="LIVE-2")) is True


# --- bounded offline shell replay -------------------------------------------

def _git(cwd, *args, check=True):
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} -> {r.returncode}\n{r.stderr}")
    return r


def _carrier(generated_at, envelope):
    return json.dumps({"generated_at": generated_at, "effective_permission": envelope},
                      indent=2, sort_keys=True) + "\n"


def _init_work(tmp_path, tip_carrier=None):
    """Bare origin + a work repo on main. If tip_carrier is given, seed a publish
    branch carrying it. Returns (work, remote)."""
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", "-q", str(remote))
    work = tmp_path / "work"
    work.mkdir()
    _git(work, "init", "-q")
    _git(work, "config", "user.email", "t@t")
    _git(work, "config", "user.name", "t")
    _git(work, "remote", "add", "origin", str(remote))
    (work / "logs").mkdir()
    (work / "logs" / "audit.jsonl").write_text('{"row":1}\n', encoding="utf-8")
    (work / "logs" / "latest_contract.json").write_text(
        _carrier("2050-01-01T00:00:00+00:00", _env(date=SD, seq=1, rank=1)), encoding="utf-8")
    _git(work, "add", "-A")
    _git(work, "commit", "-qm", "base")
    _git(work, "branch", "-M", "main")
    _git(work, "push", "-q", "origin", "main")
    if tip_carrier is not None:
        (work / "logs" / "latest_contract.json").write_text(tip_carrier, encoding="utf-8")
        _git(work, "add", "-A")
        _git(work, "commit", "-qm", "publish tip")
        _git(work, "push", "-q", "origin", "HEAD:refs/heads/publish")
        _git(work, "reset", "-q", "--hard", "HEAD~1")  # work returns to base for the run
    return work, remote


def _run_publish(work, remote, pre_sha, post_sha, base_sha):
    env = dict(os.environ, PRE_SHA=pre_sha, POST_SHA=post_sha,
               CB_PUBLISH_BASE_SHA=base_sha, PUBLISH_BRANCH="publish",
               CB_PUBLISH_MAX_ATTEMPTS="1")
    return subprocess.run(["bash", str(SCRIPT)], cwd=str(work), env=env,
                          capture_output=True, text=True)


def _make_post(work, carrier):
    (work / "logs" / "latest_contract.json").write_text(carrier, encoding="utf-8")
    with (work / "logs" / "audit.jsonl").open("a", encoding="utf-8") as fh:
        fh.write('{"row":2}\n')
    _git(work, "add", "-A")
    _git(work, "commit", "-qm", "run")
    return _git(work, "rev-parse", "HEAD").stdout.strip()


def _tip_sha(remote):
    return _git(remote, "rev-parse", "refs/heads/publish", check=False).stdout.strip()


def test_shell_bootstrap_creates_publish(tmp_path):
    # Route 1 (bootstrap): publish absent -> seeded from the run; guard exempt.
    work, remote = _init_work(tmp_path, tip_carrier=None)
    pre = _git(work, "rev-parse", "HEAD").stdout.strip()
    post = _make_post(work, _carrier("2050-01-02T00:00:00+00:00", _env(date=SD, seq=1, rank=1)))
    r = _run_publish(work, remote, pre, post, "")
    assert r.returncode == 0, r.stderr
    assert _tip_sha(remote), "publish branch not bootstrapped"


def test_shell_overlay_refuses_behind_authority_despite_newer_timestamp(tmp_path):
    # Route 2 (overlay), M5 crossed-order: tip authority AHEAD (seq2) with an OLD
    # timestamp; incoming BEHIND (seq1) with a NEWER timestamp + newer commit.
    # The guard orders by authority_version -> REFUSE; a timestamp/commit mutant admits.
    tip = _carrier("2000-01-01T00:00:00+00:00", _env(date=SD, seq=2, rank=0, uid="LIVE-2"))
    work, remote = _init_work(tmp_path, tip_carrier=tip)
    base = _tip_sha(remote)
    pre = _git(work, "rev-parse", "HEAD").stdout.strip()
    post = _make_post(work, _carrier("2099-01-01T00:00:00+00:00", _env(date=SD, seq=1, rank=1)))
    r = _run_publish(work, remote, pre, post, base)
    assert r.returncode != 0, f"expected refuse, got 0\n{r.stdout}\n{r.stderr}"
    assert _tip_sha(remote) == base, "publish tip advanced on a refused (behind) bundle"


def test_shell_overlay_admits_ahead_authority_despite_older_timestamp(tmp_path):
    # Route 2 (overlay), M5 converse: tip authority BEHIND (seq1) with a NEW
    # timestamp; incoming AHEAD (seq2) with an OLDER timestamp. The guard admits;
    # a timestamp mutant would refuse.
    tip = _carrier("2099-01-01T00:00:00+00:00", _env(date=SD, seq=1, rank=1))
    work, remote = _init_work(tmp_path, tip_carrier=tip)
    base = _tip_sha(remote)
    pre = _git(work, "rev-parse", "HEAD").stdout.strip()
    post = _make_post(work, _carrier("2000-01-01T00:00:00+00:00",
                                     _env(date=SD, seq=2, rank=1, uid="LIVE-2")))
    r = _run_publish(work, remote, pre, post, base)
    assert r.returncode == 0, f"expected admit, got {r.returncode}\n{r.stdout}\n{r.stderr}"
    assert _tip_sha(remote) != base, "publish tip did not advance on an admitted bundle"


def test_guard_runs_inside_attempt_publish_for_every_retry() -> None:
    # Route 3 (retry): the loop re-invokes attempt_publish, so the guard (inside it)
    # runs on every retry. Assert the guard is inside the retried function.
    text = SCRIPT.read_text(encoding="utf-8")
    body = text.split("attempt_publish()", 1)[1].split("\nfor attempt in", 1)[0]
    assert "publication-admits" in body, "R5 guard is not inside attempt_publish (retry route)"
