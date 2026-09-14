"""PRD-339 Slice 1 (R5): publication non-regression. Unit tests on
``publication_admits`` + a bounded OFFLINE replay of ci_push_artifacts.sh (temp
bare remote) across all routes (bootstrap/daily/hourly overlay/retry) and both
carriers, with crossed-order fixtures proving ordering by authority_version (M5)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from cuttingboard import effective_permission as ep

SD = "2026-04-12"
SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "ci_push_artifacts.sh"


_VERDICT_BY_RANK = {0: "PERMITTED", 1: "NO_TRADE", 2: "HALT", 3: "UNAVAILABLE"}


def _env(**av):
    return {
        "verdict": av.get("verdict", _VERDICT_BY_RANK[av["rank"]]),  # cross-field consistent
        "restriction_rank": av["rank"], "decision_uid": av.get("uid", "LIVE-1"),
        "session_date": av["date"], "run_uid": av.get("run_uid", "r1"),
        "authority_version": [av["date"], av["seq"], av["rank"]],
        "valid_until": av.get("valid_until", "2026-04-13T08:00:00+00:00"),
        "recovery_basis": av.get("recovery_basis"),
        "permission_line": av.get("permission_line", "x"), "decision_seq": av["seq"],
    }


def _tomorrow():
    from datetime import datetime, timezone, timedelta
    return (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()


# --- unit: publication_admits (R5 a-d) ---------------------------------------

def test_bootstrap_admits_valid_when_no_accepted() -> None:
    assert ep.publication_admits(None, _env(date=SD, seq=1, rank=1)) is True


def test_bootstrap_refuses_malformed_incoming() -> None:  # D2
    assert ep.publication_admits(None, {"garbage": 1}) is False
    assert ep.publication_admits(None, None) is False


def test_full_key_but_structurally_invalid_refused_both_routes() -> None:  # D2
    # full key set but structurally invalid -> refused on BOTH bootstrap and overlay.
    acc = _env(date=SD, seq=1, rank=1)
    for bad in (
        _env(date=SD, seq=1, rank=1, verdict="GO"),                 # unknown verdict
        {**_env(date=SD, seq=1, rank=1), "restriction_rank": 2},    # rank/verdict mismatch
        _env(date=SD, seq=1, rank=1, uid=""),                       # blank identity
        {**_env(date=SD, seq=1, rank=1), "extra": 1},               # extra field
        {**_env(date=SD, seq=1, rank=1), "valid_until": None},      # null expiry
    ):
        assert ep.publication_admits(None, bad) is False, "bootstrap admitted invalid"
        assert ep.publication_admits(acc, bad) is False, "overlay admitted invalid"


def test_refuses_future_session_on_both_routes() -> None:  # D2 (no today+1 grace)
    fut = _env(date=_tomorrow(), seq=1, rank=1)
    assert ep.publication_admits(None, fut) is False                       # bootstrap
    assert ep.publication_admits(_env(date=SD, seq=1, rank=1), fut) is False  # overlay


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


def test_equal_version_requires_full_identity() -> None:  # R5(d)/D1
    e = _env(date=SD, seq=1, rank=1, uid="LIVE-1")
    assert ep.publication_admits(e, dict(e)) is True                     # byte-identical -> no-op
    assert ep.publication_admits(e, dict(e, run_uid="OTHER")) is False   # D1: differing run_uid refused
    assert ep.publication_admits(e, {**e, "extra": 1}) is False          # extra field refused


def test_equal_version_any_field_change_refused() -> None:  # M5b / D1
    acc = _env(date=SD, seq=1, rank=1, uid="LIVE-1")
    for field, value in (
        ("decision_uid", "LIVE-DIFFERENT"),
        ("verdict", "PERMITTED"),
        ("permission_line", "TAMPERED"),
        ("valid_until", "2050-01-01T00:00:00+00:00"),
        ("recovery_basis", {"reason": "REDECISION"}),
        ("run_uid", "OTHER"),  # D1: run_uid is now governed
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
    # A real published carrier (a pipeline contract) carries a TOP-LEVEL session_date
    # (contract.py:140, a required contract field). PRD-340 F5: the Slice-2 read
    # boundary validates the EP against THIS trusted carrier session, not the EP
    # envelope's own claimed session, so the fixture mirrors a genuine carrier.
    return json.dumps({"generated_at": generated_at,
                       "session_date": envelope.get("session_date"),
                       "effective_permission": envelope},
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


def _run_publish(work, remote, pre_sha, post_sha, base_sha, session=SD):
    # PRD-340 publish-admit fix: the publish seam validates each carrier's EP against
    # an INDEPENDENT runner session (CB_WORKFLOW_SESSION, else the runner-clock date),
    # never the carrier's own session_date. The offline replay injects that session
    # explicitly (defaulting to SD, the fixtures' session) so the seam does NOT read
    # the carrier for its expected session -- exactly the production independence.
    env = dict(os.environ, PRE_SHA=pre_sha, POST_SHA=post_sha,
               CB_PUBLISH_BASE_SHA=base_sha, PUBLISH_BRANCH="publish",
               CB_PUBLISH_MAX_ATTEMPTS="1", CB_WORKFLOW_SESSION=session)
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


# --- PRD-340 publish-admit commissioning fix (owner session-ruling 2026-09-13) ------

def test_publish_admit_uses_independent_session_not_the_carrier() -> None:
    # WIRING: the publish seam computes an INDEPENDENT session (the runner-clock UTC
    # date, overridable via CB_WORKFLOW_SESSION) and passes it explicitly to the admit
    # validator -- it does NOT let the validator source the expected session from the
    # carrier being validated. A regression dropping the explicit argument (reverting
    # to the carrier-derived fallback) reddens.
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'PUBLISH_SESSION="${CB_WORKFLOW_SESSION:-$(date -u +%F)}"' in text, (
        "publish seam must compute an independent session from the runner clock")
    assert 'admit "$inc" "$PUBLISH_SESSION"' in text, (
        "publish admit must receive the independent session as an explicit argv")


def _selfcert_carrier(outer_session, ep_session):
    # A carrier whose OUTER top-level session_date can differ from its EP session, so a
    # carrier-derived (self-certifying) validator and an independent-session validator
    # diverge. R5-ahead (seq=2) so publication_admits admits; the ONLY thing that can
    # refuse is the independent-session check.
    env = _env(date=ep_session, seq=2, rank=1, uid="LIVE-2", run_uid="r2")
    return json.dumps({"generated_at": "2099-01-01T00:00:00+00:00",
                       "session_date": outer_session,
                       "effective_permission": env},
                      indent=2, sort_keys=True) + "\n"


def test_shell_publish_cannot_self_certify_via_carrier_session_field(tmp_path):
    # PROOF E (shell, self-certification -- THE core owner ruling): a SELF-CONSISTENT
    # carrier (outer session_date == EP session == SD) that is R5-ahead of the tip must
    # STILL be REFUSED when the INDEPENDENT runner session differs from the carrier's
    # session (the run is a day later than the carrier claims). The tip must not
    # advance. A mutant reverting admit to carrier.get("session_date") would match the
    # outer field and PUBLISH this stale authority -> RED.
    tip = _carrier("2000-01-01T00:00:00+00:00", _env(date=SD, seq=1, rank=1))
    work, remote = _init_work(tmp_path, DAILY, tip_carrier=tip)
    base = _tip(remote)
    pre = _git(work, "rev-parse", "HEAD").stdout.strip()
    post = _make_post(work, DAILY, _selfcert_carrier(outer_session=SD, ep_session=SD))
    r = _run_publish(work, remote, pre, post, base, session="2026-04-13")  # independent != SD
    assert r.returncode != 0, f"publish self-certified a stale carrier\n{r.stdout}\n{r.stderr}"
    assert _tip(remote) == base, "tip advanced on a self-certifying carrier"


def test_shell_publish_admits_when_independent_session_matches(tmp_path):
    # CONTROL for PROOF E: the SAME R5-ahead carrier admits when the independent runner
    # session MATCHES the carrier's EP session -- proving the refusal above is the
    # independent-session check, not an unrelated regression. Non-regression (R5) is
    # additive: the ahead carrier already passes publication_admits.
    tip = _carrier("2000-01-01T00:00:00+00:00", _env(date=SD, seq=1, rank=1))
    work, remote = _init_work(tmp_path, DAILY, tip_carrier=tip)
    base = _tip(remote)
    pre = _git(work, "rev-parse", "HEAD").stdout.strip()
    post = _make_post(work, DAILY, _selfcert_carrier(outer_session=SD, ep_session=SD))
    r = _run_publish(work, remote, pre, post, base, session=SD)  # independent == EP session
    assert r.returncode == 0, f"expected admit under matching independent session\n{r.stderr}"
    assert _tip(remote) != base, "tip did not advance under a matching independent session"
