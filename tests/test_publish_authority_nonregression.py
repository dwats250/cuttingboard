"""PRD-339 Slice 1 (R5): publication non-regression. Unit tests on
``publication_admits`` (lexicographic authority_version gate, Q4 recovery M5c,
equal-version GOVERNED-identity M5b + finding 2) + a bounded OFFLINE replay of
ci_push_artifacts.sh against a temp bare remote across ALL routes (bootstrap,
daily overlay, hourly overlay, retry) and BOTH carriers, with CROSSED-ORDER
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
    return {
        "verdict": av.get("verdict", "NO_TRADE"),
        "restriction_rank": av["rank"], "decision_uid": av.get("uid", "LIVE-1"),
        "session_date": av["date"], "run_uid": av.get("run_uid", "r1"),
        "authority_version": [av["date"], av["seq"], av["rank"]],
        "valid_until": av.get("valid_until", "2026-04-13T08:00:00+00:00"),
        "recovery_basis": av.get("recovery_basis"),
        "permission_line": av.get("permission_line", "x"), "decision_seq": av["seq"],
    }


# --- unit: publication_admits (R5 a-d) ---------------------------------------

def test_bootstrap_admits_when_no_accepted() -> None:
    assert ep.publication_admits(None, _env(date=SD, seq=1, rank=1)) is True


def test_malformed_incoming_refused() -> None:
    assert ep.publication_admits(_env(date=SD, seq=1, rank=1), None) is False
    assert ep.publication_admits(_env(date=SD, seq=1, rank=1), {"x": 1}) is False


def test_older_session_and_older_decision_refused() -> None:
    acc = _env(date=SD, seq=2, rank=0)
    assert ep.publication_admits(acc, _env(date="2026-04-11", seq=9, rank=0)) is False
    assert ep.publication_admits(acc, _env(date=SD, seq=1, rank=0)) is False


def test_intra_decision_downgrade_refused() -> None:
    acc = _env(date=SD, seq=1, rank=2)
    assert ep.publication_admits(acc, _env(date=SD, seq=1, rank=1, uid="LIVE-1")) is False


def test_equal_version_governed_identical_is_noop_admit() -> None:  # R5(d)
    e = _env(date=SD, seq=1, rank=1, uid="LIVE-1")
    replay = dict(e, run_uid="a-different-run")  # only run_uid differs -> still a no-op
    assert ep.publication_admits(e, replay) is True


def test_equal_version_any_governed_field_change_refused() -> None:  # M5b / finding 2
    acc = _env(date=SD, seq=1, rank=1, uid="LIVE-1")
    for field, value in (
        ("decision_uid", "LIVE-DIFFERENT"),
        ("verdict", "PERMITTED"),
        ("permission_line", "TAMPERED"),
        ("valid_until", "2099-01-01T00:00:00+00:00"),
        ("recovery_basis", {"reason": "REDECISION"}),
    ):
        inc = dict(acc)
        inc[field] = value
        assert ep.publication_admits(acc, inc) is False, f"equal-version differing {field} admitted"


def test_recovery_gated_downgrade_admitted() -> None:  # M5c
    acc = _env(date=SD, seq=1, rank=2)
    inc = _env(date=SD, seq=2, rank=0, uid="LIVE-2", verdict="PERMITTED",
               recovery_basis={"superseded_authority_version": [SD, 1, 2],
                               "superseding_decision_uid": "LIVE-2", "reason": "REDECISION"})
    assert ep.publication_admits(acc, inc) is True


def test_recovery_refused_without_matching_superseding_uid() -> None:  # finding 6
    acc = _env(date=SD, seq=1, rank=2)
    inc = _env(date=SD, seq=2, rank=0, uid="LIVE-2", verdict="PERMITTED",
               recovery_basis={"superseded_authority_version": [SD, 1, 2],
                               "superseding_decision_uid": "SOMEONE_ELSE", "reason": "REDECISION"})
    assert ep.publication_admits(acc, inc) is False


def test_non_recovery_downgrade_refused() -> None:  # M5c converse
    acc = _env(date=SD, seq=1, rank=2)
    inc = _env(date=SD, seq=2, rank=0, uid="LIVE-2", recovery_basis=None)
    assert ep.publication_admits(acc, inc) is False


# --- bounded offline shell replay -------------------------------------------

def _git(cwd, *args, check=True):
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} -> {r.returncode}\n{r.stderr}")
    return r


def _carrier(generated_at, envelope):
    return json.dumps({"generated_at": generated_at, "effective_permission": envelope},
                      indent=2, sort_keys=True) + "\n"


def _init_work(tmp_path, carrier_path, tip_carrier=None):
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
    (work / carrier_path).write_text(
        _carrier("2050-01-01T00:00:00+00:00", _env(date=SD, seq=1, rank=1)), encoding="utf-8")
    _git(work, "add", "-A")
    _git(work, "commit", "-qm", "base")
    _git(work, "branch", "-M", "main")
    _git(work, "push", "-q", "origin", "main")
    if tip_carrier is not None:
        (work / carrier_path).write_text(tip_carrier, encoding="utf-8")
        _git(work, "add", "-A")
        _git(work, "commit", "-qm", "publish tip")
        _git(work, "push", "-q", "origin", "HEAD:refs/heads/publish")
        _git(work, "reset", "-q", "--hard", "HEAD~1")
    return work, remote


def _run_publish(work, remote, pre_sha, post_sha, base_sha):
    env = dict(os.environ, PRE_SHA=pre_sha, POST_SHA=post_sha,
               CB_PUBLISH_BASE_SHA=base_sha, PUBLISH_BRANCH="publish",
               CB_PUBLISH_MAX_ATTEMPTS="1")
    return subprocess.run(["bash", str(SCRIPT)], cwd=str(work), env=env,
                          capture_output=True, text=True)


def _make_post(work, carrier_path, contents):
    (work / carrier_path).write_text(contents, encoding="utf-8")
    with (work / "logs" / "audit.jsonl").open("a", encoding="utf-8") as fh:
        fh.write('{"row":2}\n')
    _git(work, "add", "-A")
    _git(work, "commit", "-qm", "run")
    return _git(work, "rev-parse", "HEAD").stdout.strip()


def _tip(remote):
    return _git(remote, "rev-parse", "--verify", "--quiet",
                "refs/heads/publish", check=False).stdout.strip()


DAILY = "logs/latest_contract.json"
HOURLY = "logs/latest_hourly_contract.json"


def test_shell_bootstrap_admits_valid(tmp_path):
    work, remote = _init_work(tmp_path, DAILY, tip_carrier=None)
    pre = _git(work, "rev-parse", "HEAD").stdout.strip()
    post = _make_post(work, DAILY, _carrier("2050-01-02T00:00:00+00:00", _env(date=SD, seq=1, rank=1)))
    r = _run_publish(work, remote, pre, post, "")
    assert r.returncode == 0, r.stderr
    assert _tip(remote), "publish branch not bootstrapped"


def test_shell_bootstrap_refuses_malformed_carrier(tmp_path):
    # A bootstrap bundle whose authority carrier lacks the canonical field -> refused.
    work, remote = _init_work(tmp_path, DAILY, tip_carrier=None)
    pre = _git(work, "rev-parse", "HEAD").stdout.strip()
    post = _make_post(work, DAILY, json.dumps({"generated_at": "2050-01-02T00:00:00+00:00"}) + "\n")
    r = _run_publish(work, remote, pre, post, "")
    assert r.returncode != 0, f"bootstrap admitted a malformed carrier\n{r.stdout}"
    assert not _tip(remote), "publish branch created from a malformed bootstrap bundle"


def _overlay_refuses_behind(tmp_path, carrier):
    tip = _carrier("2000-01-01T00:00:00+00:00", _env(date=SD, seq=2, rank=0, uid="LIVE-2"))
    work, remote = _init_work(tmp_path, carrier, tip_carrier=tip)
    base = _tip(remote)
    pre = _git(work, "rev-parse", "HEAD").stdout.strip()
    post = _make_post(work, carrier, _carrier("2099-01-01T00:00:00+00:00", _env(date=SD, seq=1, rank=1)))
    r = _run_publish(work, remote, pre, post, base)
    assert r.returncode != 0, f"expected refuse for {carrier}\n{r.stdout}\n{r.stderr}"
    assert _tip(remote) == base, f"tip advanced on a refused behind {carrier}"


def _overlay_admits_ahead(tmp_path, carrier):
    tip = _carrier("2099-01-01T00:00:00+00:00", _env(date=SD, seq=1, rank=1))
    work, remote = _init_work(tmp_path, carrier, tip_carrier=tip)
    base = _tip(remote)
    pre = _git(work, "rev-parse", "HEAD").stdout.strip()
    post = _make_post(work, carrier, _carrier("2000-01-01T00:00:00+00:00",
                                              _env(date=SD, seq=2, rank=1, uid="LIVE-2")))
    r = _run_publish(work, remote, pre, post, base)
    assert r.returncode == 0, f"expected admit for {carrier}\n{r.stdout}\n{r.stderr}"
    assert _tip(remote) != base, f"tip did not advance on an admitted {carrier}"


def test_shell_daily_overlay_refuses_behind(tmp_path):
    _overlay_refuses_behind(tmp_path, DAILY)


def test_shell_daily_overlay_admits_ahead(tmp_path):
    _overlay_admits_ahead(tmp_path, DAILY)


def test_shell_hourly_overlay_refuses_behind(tmp_path):
    _overlay_refuses_behind(tmp_path, HOURLY)


def test_shell_hourly_overlay_admits_ahead(tmp_path):
    _overlay_admits_ahead(tmp_path, HOURLY)


def test_guard_runs_on_every_route_bootstrap_overlay_retry() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    # bootstrap route calls the guard before the direct push
    boot = text.split("attempting bootstrap", 1)[1].split("attempt_publish()", 1)[0]
    assert "authority_guard" in boot, "bootstrap route not guarded (R5)"
    # overlay + retry: the guard is inside attempt_publish, which the loop re-invokes
    body = text.split("attempt_publish()", 1)[1].split("\nfor attempt in", 1)[0]
    assert "authority_guard" in body, "overlay/retry route not guarded (R5)"
    assert 'AUTH_CARRIERS=("logs/latest_contract.json" "logs/latest_hourly_contract.json")' in text
