"""PRD-197 / PRD-207 — contract tests for the Codex cross-review GitHub Actions workflow.

Two layers:
  * Hermetic structure/security invariants parsed from
    `.github/workflows/codex-review.yml` (no network, no dispatch).
  * PRD-207 BEHAVIORAL tests (R3): the honor-resolution parser is EXTRACTED from
    the workflow itself and EXECUTED against REAL captured codex `--json` event
    streams (job 83746430244). These fail against any prose-string-presence
    implementation and against the pre-fix (final-message/rollout) workflow —
    PRD-198 #4: every guard ships a red test that fails when violated.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
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


def _run_blocks(job: dict) -> str:
    return "\n".join(s.get("run", "") for s in job["steps"])


# --- dispatch-only: the secret-exposure guard ------------------------------

def test_trigger_is_workflow_dispatch_only(wf):
    trig = _triggers(wf)
    assert "workflow_dispatch" in trig, "must be dispatchable"
    assert "pull_request" not in trig, "pull_request would expose the secret to forks"
    assert "pull_request_target" not in trig, "pull_request_target is equally unsafe"
    inputs = trig["workflow_dispatch"]["inputs"]
    for key in ("prd", "sha"):
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
    code = [ln for ln in raw.splitlines() if not ln.lstrip().startswith("#")]
    refs = [ln for ln in code if "secrets.OPENAI_API_KEY" in ln]
    assert len(refs) == 1, f"secrets.OPENAI_API_KEY should appear once, found: {refs}"
    assert "openai-api-key:" in refs[0], "the secret must be consumed only as the action input"
    for ln in code:
        s = ln.strip()
        assert not s.startswith("OPENAI_API_KEY:"), "secret must not be a job/step env var"
        assert not s.startswith("CODEX_API_KEY:"), "secret must not be a job/step env var"
    assert "echo $OPENAI_API_KEY" not in raw and "echo ${OPENAI_API_KEY" not in raw


def test_keyless_jobs_never_reference_the_secret(wf):
    # Only `review` holds the (proxied) key; resolve and land must never see it.
    for name in ("resolve", "land"):
        assert "OPENAI_API_KEY" not in yaml.safe_dump(wf["jobs"][name]), (
            f"{name} job must never reference the secret"
        )


# --- PRD-207: the gate must NOT run codex itself (secret-proxy NON-GOAL) ----

def test_resolve_does_not_invoke_codex_directly(wf):
    # The honor gate reads the GitHub job-log API — it must NOT run `codex exec`
    # in a run: step (that would consume OPENAI_API_KEY directly, breaking the
    # secret-proxy model). Only the openai/codex-action `uses:` step runs codex.
    resolve_runs = _run_blocks(wf["jobs"]["resolve"])
    assert "codex exec" not in resolve_runs, "resolve must not run codex directly (secret-proxy NON-GOAL)"
    assert "openai-api-key" not in resolve_runs


# --- three-job least-privilege split ---------------------------------------

def test_three_job_permission_split(wf):
    jobs = wf["jobs"]
    assert jobs["review"]["permissions"]["contents"] == "read", "key-holding job must be read-only"
    # resolve reads the completed review job log via the API → actions:read, no write.
    resolve_perms = jobs["resolve"]["permissions"]
    assert resolve_perms == {"actions": "read"}, "resolve job needs actions:read ONLY (reads job log)"
    # land pushes only the codex-review/* branch — contents:write, nothing more.
    land_perms = jobs["land"]["permissions"]
    assert land_perms["contents"] == "write", "land job pushes the codex-review/* branch"
    assert "pull-requests" not in land_perms, "land job must not hold pull-requests scope (no PR)"
    # Dependency chain: land → resolve → review.
    assert "resolve" in jobs["land"]["needs"], "land must depend on resolve"
    assert "review" in jobs["resolve"]["needs"], "resolve must depend on review"
    # top-level default is no permissions
    assert wf.get("permissions") == {}, "top-level permissions must default to none"


# --- gate integrity: branch-only landing, NEVER a protected-branch push -----

def test_land_branch_only_no_pr_no_protected_push(raw, wf):
    land = wf["jobs"]["land"]
    checkout = next(
        s for s in land["steps"] if str(s.get("uses", "")).startswith("actions/checkout")
    )
    assert checkout["with"]["ref"] == "${{ inputs.base }}", "artifact branch must be rooted at the base"
    run_blocks = _run_blocks(land)
    assert "codex-review/" in run_blocks, "artifact must land on a codex-review/* branch"
    assert "exit 1" in run_blocks, "must fail closed if the work branch is not under codex-review/"
    assert 'git push origin "HEAD:${work}"' in run_blocks, "push must target the codex-review/* work branch"
    assert "HEAD:${base}" not in run_blocks and "HEAD:main" not in run_blocks, (
        "must never push directly to the base / a protected branch"
    )
    assert "push origin main" not in run_blocks
    assert "gh pr create" not in raw, "land must not open a PR (human opens it at the seam)"
    assert "gh pr merge" not in raw and "--auto" not in raw, "land must not auto-merge"


# --- provenance: codex CLI version + resolved-model recorded ----------------

def test_provenance_recorded(wf):
    review_runs = _run_blocks(wf["jobs"]["review"])
    assert "codex --version" in review_runs, "must query the real Codex CLI version (review job)"
    resolve_runs = _run_blocks(wf["jobs"]["resolve"])
    assert "resolved-model=" in resolve_runs, "must record resolved-model in the artifact provenance"
    assert "requested=" in resolve_runs, "provenance must distinguish requested from resolved"


# --- PRD-207 R1/R2: resolution source is the completed job log, NEVER prose --

def test_resolution_reads_jobcodexlog_not_prose_or_rollout(wf):
    resolve = wf["jobs"]["resolve"]
    resolve_runs = _run_blocks(resolve)
    # R1 capture: reads the completed review job's log via the GitHub API.
    assert "actions/jobs/${job_id}/logs" in resolve_runs, (
        "resolution must read the completed review job's log via the GitHub API"
    )
    # R2: the prose step-output (`steps.codex.outputs.final-message`) is NEVER a
    # resolution source anywhere — that exact wiring was the incident's root
    # (PRD-198 #3). The final-message FILE may still be assembled into the body.
    full_dump = yaml.safe_dump(wf)
    assert "steps.codex.outputs.final-message" not in full_dump, (
        "the prose step-output must never be wired as a resolution source (PRD-198 #3)"
    )
    # The classification step resolves from the job log, not the prose output.
    classify_step = next(s for s in resolve["steps"] if "resolve_model.py" in s.get("run", ""))
    assert "final-message" not in yaml.safe_dump(classify_step.get("env", {})), (
        "the resolver step must not take the prose final-message as input"
    )
    # R2: the rollout/session-config fallback is DELETED as a resolution source.
    full = yaml.safe_dump(wf)
    assert "rollout-" not in full and "CODEX_HOME" not in full, (
        "the rollout/session-config fallback (requested-model proxy) must be removed"
    )


def test_failclosed_allowlist_indirection(raw, wf):
    resolve_runs = _run_blocks(wf["jobs"]["resolve"])
    assert "ALLOWED_CODEX_MODELS" in resolve_runs, "must check the resolved model against the allowlist"
    env = wf.get("env") or {}
    assert "ALLOWED_CODEX_MODELS" in env, "allowlist must be a human-configurable workflow env"
    assert env["ALLOWED_CODEX_MODELS"] in ("", None, "${{ vars.ALLOWED_CODEX_MODELS }}"), (
        "allowlist must stay fail-closed: empty, or sourced from the "
        "vars.ALLOWED_CODEX_MODELS repository variable; never a hardcoded model id"
    )


# --- R4: single model identity in the artifact body ------------------------

def test_r4_single_model_identity_in_body(wf):
    resolve_runs = _run_blocks(wf["jobs"]["resolve"])
    # The assemble step strips a leading prose `Model:` self-report so the body
    # cannot contradict the machine resolved-model provenance line.
    assert "/^Model:" in resolve_runs, (
        "assemble must strip a leading prose `Model:` self-report (single identity, R4)"
    )


# --- artifact identity: the gate artifact is what gets committed -----------

def test_artifact_is_the_gate_review_file(raw):
    assert "docs/prd_history/PRD-${PRD}.review.codex.md" in raw, (
        "the committed artifact must be the in-tree PRD-NNN.review.codex.md gate file"
    )


# ===========================================================================
# PRD-207 R3 — BEHAVIORAL: extract the workflow's resolver and run it against
# REAL captured codex --json streams. These fail against the pre-fix workflow
# (no resolver markers) and against any prose-grep implementation.
# ===========================================================================

def _extract_resolver(raw: str) -> str:
    lines = raw.splitlines()
    begins = [i for i, ln in enumerate(lines) if ln.strip().startswith("# === RESOLVER BEGIN")]
    ends = [i for i, ln in enumerate(lines) if ln.strip().startswith("# === RESOLVER END")]
    assert begins and ends, "codex-review.yml must embed an extractable RESOLVER block (PRD-207 R3)"
    return textwrap.dedent("\n".join(lines[begins[0]:ends[0] + 1]))


# Real captured event lines (job 83746430244), with the Actions log timestamp
# prefix the resolver must strip. These are the genuine codex --json shapes.
_TS = "2026-06-26T20:41:27.0881431Z"
_THREAD = _TS + ' {"type":"thread.started","thread_id":"019f05aa-7d14-79d0-a012-accfc4dfad9b"}'
_TURN_STARTED = _TS + ' {"type":"turn.started"}'
_ITEM_ERROR_FALLBACK = _TS + ' {"type":"item.completed","item":{"id":"item_0","type":"error",' \
    '"message":"Model metadata for `gpt-5-codex` not found. Defaulting to fallback metadata; ' \
    'this can degrade performance and cause issues."}}'
_ITEM_CMD = _TS + ' {"type":"item.completed","item":{"id":"item_1","type":"command_execution",' \
    '"command":"/bin/bash -lc ls","aggregated_output":"README.md"}}'
_ITEM_AGENT = _TS + ' {"type":"item.completed","item":{"id":"item_106","type":"agent_message",' \
    '"text":"Model: gpt-4.1\\n\\n**Verdict** APPROVE"}}'
_TURN_DONE = _TS + ' {"type":"turn.completed","usage":{"input_tokens":4779074,"output_tokens":27823}}'

# Captured WITH the model-metadata fallback (the incident: requested≠served).
FIX_FALLBACK = "\n".join([_THREAD, _TURN_STARTED, _ITEM_ERROR_FALLBACK, _ITEM_AGENT, _TURN_DONE]) + "\n"
# Captured WITHOUT any item.error, clean schema, turn completed (honored).
FIX_HONORED = "\n".join([_THREAD, _TURN_STARTED, _ITEM_CMD, _ITEM_AGENT, _TURN_DONE]) + "\n"
# Recognized events but the turn never completed (truncated/incomplete).
FIX_NO_COMPLETION = "\n".join([_THREAD, _TURN_STARTED, _ITEM_CMD, _ITEM_AGENT]) + "\n"
# A structured item.error whose message has been REWORDED (does not match the
# pinned fallback regex) — must STILL fail closed on item.type==error (STEP 1b).
_ITEM_ERROR_REWORDED = _TS + ' {"type":"item.completed","item":{"id":"item_0","type":"error",' \
    '"message":"Requested model unavailable; substituting a different model."}}'
FIX_REWORDED_ERROR = "\n".join([_THREAD, _TURN_STARTED, _ITEM_ERROR_REWORDED, _TURN_DONE]) + "\n"
# Not codex output at all (no recognizable events).
FIX_MALFORMED = "2026-06-26T20:41:00Z Setup job\n2026-06-26T20:41:01Z Run actions/checkout@v6\n"

_ALLOW = "gpt-5-codex gpt-5-codex-*"


@pytest.fixture(scope="module")
def resolver(raw: str, tmp_path_factory) -> Path:
    src = _extract_resolver(raw)
    compile(src, "resolver", "exec")  # must be valid python as embedded
    p = tmp_path_factory.mktemp("resolver") / "resolve_model.py"
    p.write_text(src, encoding="utf-8")
    return p


def _run_resolver(resolver: Path, tmp_path: Path, stream: str, requested: str, allow: str):
    log = tmp_path / "job.log"
    log.write_text(stream, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(resolver), str(log), requested, allow],
        capture_output=True, text=True,
    )


def test_prd207_fallback_present_fails_closed(resolver, tmp_path):
    r = _run_resolver(resolver, tmp_path, FIX_FALLBACK, "gpt-5-codex", _ALLOW)
    assert r.returncode != 0, "a captured stream WITH the model-metadata fallback must FAIL CLOSED"
    assert r.stdout.strip() == "", "no resolved-model may be emitted when the fallback fired"
    assert "FAIL-CLOSED" in r.stderr


def test_prd207_honored_allowlisted_passes(resolver, tmp_path):
    r = _run_resolver(resolver, tmp_path, FIX_HONORED, "gpt-5-codex", _ALLOW)
    assert r.returncode == 0, "an honored, allowlisted stream must PASS"
    assert r.stdout.strip() == "gpt-5-codex", "honored run resolves to the (served==requested) model"


def test_prd207_honored_off_allowlist_fails_closed(resolver, tmp_path):
    r = _run_resolver(resolver, tmp_path, FIX_HONORED, "gpt-4.1", _ALLOW)
    assert r.returncode != 0, "an honored but OFF-allowlist model must FAIL CLOSED"
    assert r.stdout.strip() == ""


def test_prd207_no_completion_fails_closed(resolver, tmp_path):
    r = _run_resolver(resolver, tmp_path, FIX_NO_COMPLETION, "gpt-5-codex", _ALLOW)
    assert r.returncode != 0, "a stream with no turn.completed must FAIL CLOSED (incomplete)"


def test_prd207_malformed_stream_fails_closed(resolver, tmp_path):
    r = _run_resolver(resolver, tmp_path, FIX_MALFORMED, "gpt-5-codex", _ALLOW)
    assert r.returncode != 0, "an unrecognized/non-codex stream must FAIL CLOSED, never silently pass"
    assert r.stdout.strip() == ""


def test_prd207_reworded_fallback_still_fails_closed(resolver, tmp_path):
    # STEP 1b hardening: a message-regex-only match would let a reworded fallback
    # pass as honored. ANY item.error must fail closed.
    r = _run_resolver(resolver, tmp_path, FIX_REWORDED_ERROR, "gpt-5-codex", _ALLOW)
    assert r.returncode != 0, "a reworded item.error must STILL fail closed (not regex-only)"
    assert r.stdout.strip() == ""


# ===========================================================================
# PRD-212 — CLI-identity pin. TRIPWIRE, NOT a behavioral proof.
#
# The unpinned `codex-version` let the action install a floating "current" CLI;
# the current CLI dropped `gpt-5-codex` metadata and fell back, so every dispatch
# fail-closed (no artifact). The fix pins the CLI to codex-cli 0.142.1 — the last
# version with LANDED PROOF of honoring the alias (PRD-210/PRD-208 certified
# artifacts).
#
# HONEST LABEL (PRD-198 #4, anti-hollow-gate): this is a PRESENCE/STRUCTURE check.
# It CANNOT prove 0.142.1 actually honors gpt-5-codex — that needs a live Codex
# dispatch (PRD-212 Phase-4 acceptance: resolved-model=gpt-5-codex HONORED, artifact
# lands). The BEHAVIORAL honor guard is test_prd207_fallback_present_fails_closed /
# test_prd207_honored_allowlisted_passes above (the workflow's own resolver run
# against the real captured fallback/honored streams). This tripwire only locks the
# proven-good version string: any change away from 0.142.1 goes RED and forces a
# fresh Phase-4 re-validation.
# ===========================================================================

def test_prd212_codex_version_pinned_tripwire(wf):
    review = wf["jobs"]["review"]
    codex_step = next(
        s for s in review["steps"]
        if isinstance(s.get("uses"), str) and s["uses"].startswith("openai/codex-action")
    )
    pinned = (codex_step.get("with") or {}).get("codex-version")
    assert pinned is not None, (
        "codex-version must be PINNED in the codex-action step — an unpinned/floating "
        "CLI is the PRD-212 drift (install a 'current' CLI that dropped gpt-5-codex)"
    )
    assert str(pinned).strip() == "0.142.1", (
        f"codex-version must pin the proven-good CLI 0.142.1 (got {pinned!r}); any other "
        "version requires a fresh Phase-4 live re-validation that it honors gpt-5-codex"
    )
