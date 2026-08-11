"""PRD-297: behavior tests for the exact-SHA authoritative CI proof.

Proves the typed-state selector is TOTAL and FAIL-CLOSED: every input maps to a
named state, no unknown/error condition degrades to exit 0, a pull_request or
non-ci.yml run cannot authorize, and the multiple-run tie-break resolves to the
current authoritative run. The Actions API is mocked; no network.
"""
from __future__ import annotations

import pytest

from scripts import check_run_revision as cr

SHA = "a" * 40
REPO = "owner/repo"
TOKEN = "t0ken"


def _run(status, conclusion, *, event="push", path=".github/workflows/ci.yml", head_sha=SHA, run_number=1, created_at="2026-08-11T00:00:00Z"):
    return {
        "status": status,
        "conclusion": conclusion,
        "event": event,
        "path": path,
        "head_sha": head_sha,
        "run_number": run_number,
        "created_at": created_at,
    }


def _patch_collect(monkeypatch, batches):
    """batches: a list produced on successive _collect_runs calls (or a single list)."""
    if isinstance(batches, list) and (not batches or isinstance(batches[0], dict)):
        seq = [batches]
    else:
        seq = list(batches)
    calls = {"i": 0}

    def fake_collect(repo, sha, token):
        idx = min(calls["i"], len(seq) - 1)
        calls["i"] += 1
        return seq[idx]

    monkeypatch.setattr(cr, "_collect_runs", fake_collect)


# --- typed states -----------------------------------------------------------

def test_success_authorizes(monkeypatch):
    _patch_collect(monkeypatch, [_run("completed", "success")])
    state, sha, num = cr.prove(REPO, TOKEN, SHA, now=lambda: 0.0, sleep=lambda s: None)
    assert state == cr.CI_SUCCESS and sha == SHA


def test_missing_is_named_failure(monkeypatch):
    _patch_collect(monkeypatch, [])
    state, _, _ = cr.prove(REPO, TOKEN, SHA, now=lambda: 0.0, sleep=lambda s: None)
    assert state == cr.CI_MISSING


@pytest.mark.parametrize("conclusion", ["failure", "cancelled", "timed_out", "startup_failure", None])
def test_completed_non_success_is_failed(monkeypatch, conclusion):
    _patch_collect(monkeypatch, [_run("completed", conclusion)])
    state, _, _ = cr.prove(REPO, TOKEN, SHA, now=lambda: 0.0, sleep=lambda s: None)
    assert state == cr.CI_FAILED


def test_pending_then_success_within_budget(monkeypatch):
    _patch_collect(monkeypatch, [[_run("queued", None)], [_run("completed", "success")]])
    state, _, _ = cr.prove(REPO, TOKEN, SHA, now=lambda: 0.0, sleep=lambda s: None)
    assert state == cr.CI_SUCCESS


def test_pending_beyond_ceiling_is_named_failure(monkeypatch):
    monkeypatch.setattr(cr, "WAIT_CEILING_S", 0)
    _patch_collect(monkeypatch, [_run("in_progress", None)])
    state, _, _ = cr.prove(REPO, TOKEN, SHA, now=lambda: 0.0, sleep=lambda s: None)
    assert state == cr.CI_PENDING


def test_proof_error_propagates(monkeypatch):
    def boom(repo, sha, token):
        raise cr.ProofError("HTTP 403 rate limit")

    monkeypatch.setattr(cr, "_collect_runs", boom)
    with pytest.raises(cr.ProofError):
        cr.prove(REPO, TOKEN, SHA, now=lambda: 0.0, sleep=lambda s: None)


# --- selector: wrong workflow/event cannot authorize ------------------------

def test_pull_request_run_cannot_authorize(monkeypatch):
    _patch_collect(monkeypatch, [_run("completed", "success", event="pull_request")])
    state, _, _ = cr.prove(REPO, TOKEN, SHA, now=lambda: 0.0, sleep=lambda s: None)
    assert state == cr.CI_MISSING


def test_non_ci_workflow_run_cannot_authorize(monkeypatch):
    _patch_collect(monkeypatch, [_run("completed", "success", path=".github/workflows/drift_full_suite.yml")])
    state, _, _ = cr.prove(REPO, TOKEN, SHA, now=lambda: 0.0, sleep=lambda s: None)
    assert state == cr.CI_MISSING


def test_mismatched_head_sha_cannot_authorize(monkeypatch):
    _patch_collect(monkeypatch, [_run("completed", "success", head_sha="b" * 40)])
    state, _, _ = cr.prove(REPO, TOKEN, SHA, now=lambda: 0.0, sleep=lambda s: None)
    assert state == cr.CI_MISSING


# --- multiple-run tie-break selects the current authoritative run -----------

def test_multiple_runs_select_highest_run_number_success():
    runs = [_run("completed", "failure", run_number=1), _run("completed", "success", run_number=2)]
    assert cr._classify(cr._select(runs, SHA)) == cr.CI_SUCCESS


def test_multiple_runs_select_highest_run_number_failure():
    # A superseded success cannot mask the current authoritative failure.
    runs = [_run("completed", "success", run_number=1), _run("completed", "failure", run_number=2)]
    assert cr._classify(cr._select(runs, SHA)) == cr.CI_FAILED


# --- SHA resolution ---------------------------------------------------------

def test_bad_sha_is_proof_error():
    with pytest.raises(cr.ProofError):
        cr._resolve_sha("not-a-sha")


# --- pagination (full follow) -----------------------------------------------

def test_collect_runs_follows_pagination(monkeypatch):
    page1 = {"workflow_runs": [_run("completed", "success", run_number=n) for n in range(100)]}
    page2 = {"workflow_runs": [_run("completed", "success", run_number=100)]}
    seen = {"pages": []}

    def fake_api_get(url, token):
        import urllib.parse

        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        page = int(query["page"][0])
        seen["pages"].append(page)
        return page1 if page == 1 else page2

    monkeypatch.setattr(cr, "_api_get", fake_api_get)
    runs = cr._collect_runs(REPO, SHA, TOKEN)
    assert len(runs) == 101 and seen["pages"] == [1, 2]


def test_api_get_http_error_is_proof_error(monkeypatch):
    import urllib.error

    def boom(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 403, "rate limited", {}, None)

    monkeypatch.setattr(cr.urllib.request, "urlopen", boom)
    with pytest.raises(cr.ProofError):
        cr._api_get("https://api.github.com/x?page=1", TOKEN)


# --- main() exit codes: only CI_SUCCESS exits 0 -----------------------------

def test_main_success_exit_zero(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.setenv("GITHUB_TOKEN", TOKEN)
    monkeypatch.setattr(cr, "prove", lambda *a, **k: (cr.CI_SUCCESS, SHA, 7))
    assert cr.main([]) == 0


@pytest.mark.parametrize("state", [cr.CI_MISSING, cr.CI_FAILED, cr.CI_PENDING])
def test_main_named_failures_exit_nonzero(monkeypatch, state):
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.setenv("GITHUB_TOKEN", TOKEN)
    monkeypatch.setattr(cr, "prove", lambda *a, **k: (state, SHA, 7))
    assert cr.main([]) != 0


def test_main_proof_error_exit_nonzero(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.setenv("GITHUB_TOKEN", TOKEN)

    def boom(*a, **k):
        raise cr.ProofError("network down")

    monkeypatch.setattr(cr, "prove", boom)
    assert cr.main([]) != 0
    assert "CI_PROOF_STATE=CI_PROOF_ERROR" in capsys.readouterr().out


def test_main_missing_token_is_proof_error(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert cr.main([]) != 0
