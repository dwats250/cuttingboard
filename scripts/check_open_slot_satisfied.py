#!/usr/bin/env python3
"""PRD-299: GitHub-native first-success proof for the automatic OPEN slot.

Answers exactly one question: has today's logical automatic OPEN slot already
been satisfied by a prior qualifying run? Typed states:

    SATISFIED    -- a prior qualifying run proves today's OPEN slot is done.
    UNSATISFIED  -- the query succeeded and NO prior run qualifies.
    PROOF_ERROR  -- satisfaction could not be deterministically proven
                    (network/HTTP error, malformed record, missing env).

POLARITY (the crux vs. scripts/check_run_revision.py). check_run_revision gates
ATTEMPT AUTHORIZATION and fails CLOSED (an unproven authorization must not
authorize). THIS proof gates SUPPRESSION of the only automatic fallback and
therefore fails toward AVAILABILITY: on PROOF_ERROR the caller EXECUTES rather
than suppress the only fallback. Both obey PRD-198 #1 (fail-loud, never silent
substitution); the safe direction differs because the cost of a wrong answer
differs -- a false GO vs a false STOP that drops the only fallback -> missing
board. This script therefore NEVER exits non-zero for a computed state and NEVER
prints UNSATISFIED/SATISFIED when it could not prove the answer; PROOF_ERROR is a
distinct printed state the workflow maps to "execute, degraded".

Slot identity is GitHub-native only (PRD-299 R4/R5; packet
audits/cf-clock-executor-coordination-2026-08 v0.4): workflow path, event,
head_branch, the `CB-SLOT:OPEN` display_title token, created_at, status,
conclusion, and run id. No persisted coordination state.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, time, timezone
from pathlib import Path

# Reuse the repository's canonical DST-aware market-time boundary (PRD-299 R5).
# time_utils' contract: "All market time decisions must go through these
# functions." Ensure the repo root is importable when run as a bare script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cuttingboard.time_utils import _MARKET_OPEN_ET, convert_utc_to_et  # noqa: E402

WORKFLOW_FILE = os.environ.get("CB_COORD_WORKFLOW_FILE", "cuttingboard.yml")
WORKFLOW_PATH = f".github/workflows/{WORKFLOW_FILE}"
OPEN_TOKEN = "CB-SLOT:OPEN"
# workflow_dispatch lower bound, tied to the CF OPEN trigger (~13:00 UTC, a fixed
# UTC cron); rejects off-hour-early manual dispatches. UTC-anchored because the
# CF/GH clocks are UTC (packet C1). The upper bound is the ET market-open
# boundary (R5), applied only to workflow_dispatch.
DISPATCH_LOWER_UTC = time(12, 55)
API_VERSION = "2022-11-28"

SATISFIED = "SATISFIED"
UNSATISFIED = "UNSATISFIED"
PROOF_ERROR = "PROOF_ERROR"


class ProofError(Exception):
    """Any condition preventing a deterministic proof -> PROOF_ERROR (fail toward availability)."""


def _api_get(url: str, token: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "cuttingboard-open-slot-proof",
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


def _parse_created_at(value: object) -> datetime:
    """Parse a run's `created_at` (ISO-8601 Z) to an aware UTC datetime.

    A malformed/missing value is a schema anomaly -> ProofError (fail-loud),
    never a silently-dropped record that could hide a real success.
    """
    if not isinstance(value, str):
        raise ProofError(f"malformed created_at (not a string): {value!r}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProofError(f"unparseable created_at {value!r}: {exc}") from exc
    if parsed.tzinfo is None:
        raise ProofError(f"naive created_at {value!r} (no timezone)")
    return parsed.astimezone(timezone.utc)


def _collect_runs(repo: str, token: str, since: date) -> list[dict]:
    """Completed cuttingboard runs on main created on/after `since` (UTC date).

    Every record is validated at collection: a malformed run record raises a
    typed ProofError rather than escaping as an AttributeError/TypeError. Event
    is NOT filtered server-side (the API accepts one event value only); the
    small same-day result set is filtered client-side in _is_qualifying_open.
    """
    runs: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/runs"
            f"?branch=main&status=completed&created=%3E%3D{since.isoformat()}"
            f"&per_page=100&page={page}"
        )
        data = _api_get(url, token)
        batch = data.get("workflow_runs")
        if batch is None or not isinstance(batch, list):
            raise ProofError("missing/invalid 'workflow_runs' in API response")
        for item in batch:
            if not isinstance(item, dict):
                raise ProofError(f"malformed run record (not an object): {type(item).__name__}")
        runs.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        if page > 50:
            raise ProofError("pagination exceeded 50 pages (unexpected)")
    return runs


def _is_qualifying_open(run: dict, today_utc: date, current_run_id: object) -> bool:
    """True iff `run` proves today's OPEN slot is satisfied (PRD-299 R4/R5).

    Requires: this workflow; event in {schedule, workflow_dispatch}; head_branch
    main; the CB-SLOT:OPEN token; completed; conclusion=success; not the current
    run; today's trading date; and the event-aware R5 eligibility bound.
    """
    if run.get("path") != WORKFLOW_PATH:
        return False
    event = run.get("event")
    if event not in ("schedule", "workflow_dispatch"):
        return False
    if (run.get("head_branch") or "") != "main":
        return False
    title = run.get("display_title") or run.get("name") or ""
    if not isinstance(title, str) or OPEN_TOKEN not in title:
        return False
    if run.get("status") != "completed":
        return False
    if run.get("conclusion") != "success":
        return False
    if current_run_id is not None and str(run.get("id")) == str(current_run_id):
        return False  # a run never satisfies its own slot
    created = _parse_created_at(run.get("created_at"))
    if created.date() != today_utc:
        return False  # trading-date bucket (UTC date == PT/ET date for this ~13:00-UTC slot)
    if event == "schedule":
        # The sole CB-SLOT:OPEN schedule run is the automatic fallback; a schedule
        # event can never be manual, so ANY lateness within the trading date
        # satisfies (PRD-299 R5 / Sol S1 fix -- no guessed lateness ceiling).
        return True
    # workflow_dispatch (CF automatic OR manual): premarket only.
    if created.time() < DISPATCH_LOWER_UTC:
        return False
    return convert_utc_to_et(created).time() < _MARKET_OPEN_ET


def evaluate_runs(runs: list[dict], now_utc: datetime, current_run_id: object) -> str:
    """Pure evaluation over already-fetched run records -> SATISFIED/UNSATISFIED.

    Raises ProofError for a malformed record (the caller maps it to PROOF_ERROR).
    Injectable for tests (fixture payloads, no live network).
    """
    today = now_utc.astimezone(timezone.utc).date()
    for run in runs:
        if not isinstance(run, dict):
            raise ProofError(f"malformed run record (not an object): {type(run).__name__}")
        if _is_qualifying_open(run, today, current_run_id):
            return SATISFIED
    return UNSATISFIED


def prove(repo: str, token: str, current_run_id: object, *, now_utc: datetime | None = None) -> str:
    now = now_utc or datetime.now(timezone.utc)
    runs = _collect_runs(repo, token, now.astimezone(timezone.utc).date())
    return evaluate_runs(runs, now, current_run_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GitHub-native OPEN first-success proof (PRD-299).")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID"))
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    evidence = ""
    if not args.repo:
        state, evidence = PROOF_ERROR, "GITHUB_REPOSITORY not set"
    elif not token:
        state, evidence = PROOF_ERROR, "GITHUB_TOKEN/GH_TOKEN not set"
    else:
        try:
            state = prove(args.repo, token, args.run_id)
        except ProofError as exc:
            state, evidence = PROOF_ERROR, str(exc)

    # The printed state is the authoritative signal (packet 6.3: distinguished by
    # printed state, never by exit code alone). Emit for both humans and the
    # workflow step output. Exit 0 ALWAYS: a non-zero exit under `set -e` would
    # abort the step and suppress the fallback -- the opposite of fail-toward-
    # availability. The workflow executes unless state == SATISFIED.
    print(f"CB_OPEN_SLOT_STATE={state}")
    if evidence:
        print(f"CB_OPEN_SLOT_EVIDENCE={evidence}", file=sys.stderr)
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        try:
            with open(gh_out, "a", encoding="utf-8") as fh:
                fh.write(f"state={state}\n")
        except OSError as exc:
            print(f"CB_OPEN_SLOT_EVIDENCE=could not write GITHUB_OUTPUT: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
