"""PRD-197 — contract tests for the Codex cross-review GitHub Actions workflow.

These are hermetic: they parse `.github/workflows/codex-review.yml` and assert the
security/structure invariants the PRD's FAIL-lines require. No network, no dispatch.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml  # hard dep (PyYAML in the dev extra) — must not silently skip in CI

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "codex-review.yml"


@pytest.fixture(scope="module")
def raw() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def wf(raw: str) -> dict:
    return yaml.safe_load(raw)


def _triggers(wf: dict) -> dict:
    # PyYAML parses the bare key `on:` as the boolean True (YAML 1.1), so accept both.
    if "on" in wf:
        return wf["on"]
    if True in wf:
        return wf[True]
    raise AssertionError("workflow has no `on:` trigger block")


# --- dispatch-only: the secret-exposure guard ------------------------------

def test_trigger_is_workflow_dispatch_only(wf):
    trig = _triggers(wf)
    assert "workflow_dispatch" in trig, "must be dispatchable"
    assert "pull_request" not in trig, "pull_request would expose the secret to forks"
    assert "pull_request_target" not in trig, "pull_request_target is equally unsafe"
    # dispatch carries the target identifiers
    inputs = trig["workflow_dispatch"]["inputs"]
    for key in ("prd", "sha", "branch"):
        assert key in inputs, f"dispatch must take `{key}` as input"


# --- read-only execution ---------------------------------------------------

def test_read_only_sandbox_and_no_workspace_write(raw, wf):
    review = wf["jobs"]["review"]
    codex_step = next(
        s for s in review["steps"] if str(s.get("uses", "")).startswith("openai/codex-action")
    )
    assert codex_step["with"]["sandbox"] == "read-only"
    assert "workspace-write" not in raw, "workspace-write must appear nowhere in the workflow"


# --- secret hygiene: proxied only, never env, never echoed -----------------

def test_secret_only_as_action_input(raw):
    # Ignore comment lines (security commentary legitimately names the token).
    code = [ln for ln in raw.splitlines() if not ln.lstrip().startswith("#")]
    # The secret interpolation appears exactly once — as the action input it proxies.
    refs = [ln for ln in code if "secrets.OPENAI_API_KEY" in ln]
    assert len(refs) == 1, f"secrets.OPENAI_API_KEY should appear once, found: {refs}"
    assert "openai-api-key:" in refs[0], "the secret must be consumed only as the action input"
    # Never declared as a job/step env var, never echoed.
    for ln in code:
        s = ln.strip()
        assert not s.startswith("OPENAI_API_KEY:"), "secret must not be a job/step env var"
        assert not s.startswith("CODEX_API_KEY:"), "secret must not be a job/step env var"
    assert "echo $OPENAI_API_KEY" not in raw and "echo ${OPENAI_API_KEY" not in raw


def test_commit_job_never_references_the_secret(raw, wf):
    # Re-serialize just the commit job and assert the secret is absent from it.
    commit = wf["jobs"]["commit"]
    assert "OPENAI_API_KEY" not in yaml.safe_dump(commit)


# --- two-job least-privilege split -----------------------------------------

def test_two_job_permission_split(wf):
    jobs = wf["jobs"]
    assert jobs["review"]["permissions"]["contents"] == "read", "key-holding job must be read-only"
    assert jobs["commit"]["permissions"]["contents"] == "write", "commit job writes the artifact"
    assert "review" in jobs["commit"]["needs"] or jobs["commit"]["needs"] == "review"
    # top-level default is no permissions
    assert wf.get("permissions") == {}, "top-level permissions must default to none"


# --- gate integrity: refuse to commit a review for a superseded SHA --------

def test_commit_job_guards_against_stale_sha(wf):
    commit = wf["jobs"]["commit"]
    run_blocks = "\n".join(s.get("run", "") for s in commit["steps"])
    assert "rev-parse HEAD" in run_blocks, "commit job must read the current HEAD"
    # the guard compares HEAD to the reviewed SHA input before writing/pushing
    assert "SHA" in run_blocks and "exit 1" in run_blocks, (
        "commit job must fail if the branch tip no longer equals the reviewed SHA"
    )


# --- provenance: real Codex model/version recorded -------------------------

def test_provenance_recorded(raw, wf):
    review = wf["jobs"]["review"]
    run_blocks = "\n".join(s.get("run", "") for s in review["steps"])
    assert "codex --version" in run_blocks, "must query the real Codex CLI version"
    assert "model=" in run_blocks, "must record the model id in the artifact provenance"


# --- artifact identity: the gate artifact is what gets committed -----------

def test_artifact_is_the_gate_review_file(raw):
    assert "docs/prd_history/PRD-${PRD}.review.codex.md" in raw, (
        "the committed artifact must be the in-tree PRD-NNN.review.codex.md gate file"
    )
