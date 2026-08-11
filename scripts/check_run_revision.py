#!/usr/bin/env python3
"""PRD-297: exact-SHA authoritative CI proof for the morning executor gate swap.

Proves that the EXACT checked-out revision's own ci.yml push run concluded
success before a morning observation is authorized, replacing the removed
full-suite/ruff runtime gate (quality control stays at the ci.yml merge gate).

Typed, fail-closed states; no unknown/error condition degrades to success.
CI_SUCCESS authorizes an observation ATTEMPT only -- it is never evidence that
an observation occurred or was valid (a post-execution CI flip is
non-retroactive). REVISION_DRIFT is enforced by the workflow (HEAD re-check
before execute) using the CI_PROOF_SHA this script prints.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

CI_WORKFLOW_PATH = os.environ.get("CB_CI_WORKFLOW_PATH", ".github/workflows/ci.yml")
WAIT_CEILING_S = int(os.environ.get("CB_CI_WAIT_CEILING_SECONDS", "120"))
POLL_INTERVAL_S = int(os.environ.get("CB_CI_POLL_INTERVAL_SECONDS", "10"))
API_VERSION = "2022-11-28"

CI_SUCCESS = "CI_SUCCESS"
CI_PENDING = "CI_PENDING"
CI_MISSING = "CI_MISSING"
CI_FAILED = "CI_FAILED"
CI_PROOF_ERROR = "CI_PROOF_ERROR"


class ProofError(Exception):
    """Any condition that prevents a deterministic proof -> CI_PROOF_ERROR (fail-closed)."""


def _resolve_sha(explicit: str | None) -> str:
    if explicit:
        sha = explicit.strip()
    else:
        try:
            sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            ).stdout.strip()
        except (subprocess.SubprocessError, OSError) as exc:
            raise ProofError(f"could not resolve HEAD: {exc}") from exc
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha.lower()):
        raise ProofError(f"HEAD is not a 40-hex SHA: {sha!r}")
    return sha.lower()


def _api_get(url: str, token: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "cuttingboard-ci-proof",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                raise ProofError(f"HTTP {resp.status} from {url}")
            body = resp.read()
    except urllib.error.HTTPError as exc:
        raise ProofError(f"HTTP error {exc.code} from {url}: {exc.reason}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ProofError(f"network error contacting {url}: {exc}") from exc
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ProofError(f"invalid JSON from {url}: {exc}") from exc
    if not isinstance(data, dict):
        raise ProofError(f"unexpected JSON shape from {url}: not an object")
    return data


def _collect_runs(repo: str, sha: str, token: str) -> list[dict]:
    workflow_file = CI_WORKFLOW_PATH.rsplit("/", 1)[-1]
    runs: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/runs"
            f"?head_sha={sha}&event=push&per_page=100&page={page}"
        )
        data = _api_get(url, token)
        batch = data.get("workflow_runs")
        if batch is None or not isinstance(batch, list):
            raise ProofError("missing/invalid 'workflow_runs' in API response")
        # A malformed record (null item, or non-comparable run_number/created_at
        # types) must surface as a typed CI_PROOF_ERROR, not an AttributeError/
        # TypeError traceback that escapes main() (R3/I2: every schema anomaly is
        # named and fail-closed).
        for item in batch:
            if not isinstance(item, dict):
                raise ProofError(f"malformed run record (not an object): {type(item).__name__}")
            run_number = item.get("run_number")
            if run_number is not None and not isinstance(run_number, int):
                raise ProofError(f"malformed run_number in run record: {run_number!r}")
            created_at = item.get("created_at")
            if created_at is not None and not isinstance(created_at, str):
                raise ProofError(f"malformed created_at in run record: {created_at!r}")
        runs.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        if page > 50:
            raise ProofError("pagination exceeded 50 pages (unexpected)")
    return runs


def _select(runs: list[dict], sha: str) -> dict | None:
    matches = [
        r
        for r in runs
        if r.get("event") == "push"
        and r.get("path") == CI_WORKFLOW_PATH
        and (r.get("head_sha") or "").lower() == sha
    ]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    # Deterministic current-authoritative selection: highest run_number, then
    # most-recent created_at. (Historically zero multi-run SHAs; defensive.)
    return sorted(matches, key=lambda r: (r.get("run_number", 0), r.get("created_at", "")))[-1]


def _classify(run: dict) -> str:
    if run.get("status") == "completed":
        return CI_SUCCESS if run.get("conclusion") == "success" else CI_FAILED
    return CI_PENDING


def prove(
    repo: str,
    token: str,
    explicit_sha: str | None = None,
    *,
    now=time.monotonic,
    sleep=time.sleep,
) -> tuple[str, str, int | None]:
    """Return (state, sha, run_number|None). Raises ProofError -> CI_PROOF_ERROR."""
    sha = _resolve_sha(explicit_sha)
    deadline = now() + WAIT_CEILING_S
    while True:
        run = _select(_collect_runs(repo, sha, token), sha)
        if run is None:
            return CI_MISSING, sha, None
        state = _classify(run)
        if state != CI_PENDING:
            return state, sha, run.get("run_number")
        remaining = deadline - now()
        if remaining <= 0:
            return CI_PENDING, sha, run.get("run_number")
        sleep(min(POLL_INTERVAL_S, remaining))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Exact-SHA authoritative CI proof (PRD-297).")
    parser.add_argument("--sha", default=os.environ.get("CB_EXPECTED_SHA"))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    if not args.repo:
        print(f"CI_PROOF_STATE={CI_PROOF_ERROR}")
        print("CI_PROOF_ERROR: GITHUB_REPOSITORY not set", file=sys.stderr)
        return 2
    if not token:
        print(f"CI_PROOF_STATE={CI_PROOF_ERROR}")
        print("CI_PROOF_ERROR: GITHUB_TOKEN/GH_TOKEN not set", file=sys.stderr)
        return 2

    try:
        state, sha, run_number = prove(args.repo, token, args.sha)
    except ProofError as exc:
        print(f"CI_PROOF_STATE={CI_PROOF_ERROR}")
        print(f"CI_PROOF_SHA={args.sha or ''}")
        print(f"CI_PROOF_ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"CI_PROOF_STATE={state}")
    print(f"CI_PROOF_SHA={sha}")
    if state == CI_SUCCESS:
        print(f"exact-SHA ci.yml push run {run_number} concluded success; authorizing attempt for {sha}")
        return 0
    msg = {
        CI_PENDING: f"ci.yml push run for {sha} still pending after {WAIT_CEILING_S}s budget",
        CI_MISSING: f"no ci.yml push run found for {sha} (revision is not CI-authoritative)",
        CI_FAILED: f"ci.yml push run {run_number} for {sha} concluded non-success",
    }.get(state, state)
    print(f"{state}: {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
