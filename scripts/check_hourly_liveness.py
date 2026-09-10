#!/usr/bin/env python3
"""Hourly delivery liveness probe (completion PR, 2026-09-09).

The GitHub schedule is no longer an execution fallback for the hourly alert:
the Cloudflare clock (workers/cuttingboard-clock) is the authoritative routine
clock and a scheduled GitHub arrival only PROBES whether delivery is alive.
This script is that probe. It reads the DELIVERY EVIDENCE the runtime persists
after a successful hourly send -- ``logs/last_hourly_slot.json`` on the
``publish`` branch -- directly from the fetched branch, and answers one
bounded question: has ANY canonical hourly slot been delivered today (PT)?

Verdicts (stdout line ``hourly-liveness: <STATE> ...``):

* ``NOT_DUE``  (exit 0) -- weekend, or a weekday before 08:00 PT. The
  threshold follows the 06:30 / 06:45 / 07:00 slots, the 07:25 end of the
  last 25-minute admission window, and 35 minutes of completion allowance.
  It asks for any same-day hourly delivery, never for the 08:00 slot itself.
* ``HEALTHY``  (exit 0) -- a well-formed, tz-aware, same-day, canonical-slot
  record with ``slot_utc <= saved_at_utc <= now``.
* ``RED``      (exit 1) -- due, and the evidence is missing (branch/path
  absent, fetch failure), malformed, naive, non-canonical, stale
  (previous day), or in the future.

Honesty limits (by design, not omission):

* Evidence is read from the exact fetched ``origin/<branch>:<path>`` blob,
  never through ``tools/ci_restore_publish_state.sh`` -- that helper keeps
  main's frozen copy when the publish path is absent, which would let a
  frozen record masquerade as live delivery.
* The probe can only alarm when GitHub actually delivers the scheduled
  arrival. A probe that never arrives raises nothing; this script does not
  and must not add another monitor to hide that.
* No holiday calendar: a weekday market holiday at/after 08:00 PT is RED
  (owner-accepted).
* Stdlib only. Canonical slot constants come from the stdlib-only leaf
  ``cuttingboard/notifications/hourly_slot.py`` loaded by path (no package
  import, no provider dependencies, no dependency install).
"""
from __future__ import annotations

import argparse
import json
import os
import runpy
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Callable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
_SLOT_LEAF = REPO_ROOT / "cuttingboard" / "notifications" / "hourly_slot.py"

NOT_DUE = "NOT_DUE"
HEALTHY = "HEALTHY"
RED = "RED"

DUE_THRESHOLD_PT = time(8, 0)
DEFAULT_PATH = "logs/last_hourly_slot.json"


def _load_slot_leaf() -> tuple[tuple[tuple[int, int], ...], object]:
    ns = runpy.run_path(str(_SLOT_LEAF), run_name="cuttingboard_hourly_slot_leaf")
    return tuple(ns["ALLOWED_PT_SLOTS"]), ns["_PT_TZ"]


ALLOWED_PT_SLOTS, PT_TZ = _load_slot_leaf()


class SourceError(RuntimeError):
    """The published evidence could not be read (branch/path absent, fetch failed)."""


@dataclass(frozen=True)
class Evidence:
    """What was actually read: the publish tip SHA and the raw blob text."""

    sha: str
    text: str


@dataclass(frozen=True)
class Verdict:
    state: str
    reason: str
    details: dict

    @property
    def exit_code(self) -> int:
        return 1 if self.state == RED else 0


# --------------------------------------------------------------------------
# Evidence extraction: exact fetched blob, never the restore helper.
# --------------------------------------------------------------------------

def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


def read_published_record(branch: str, path: str, repo_root: Path = REPO_ROOT) -> Evidence:
    """Fetch ``origin/<branch>`` and return the blob at ``path`` with the tip SHA.

    Raises SourceError on an absent/unreachable branch or an absent path. The
    caller decides what that means (RED when due); this never falls back to
    the working tree or to main.
    """
    fetched = _git(["fetch", "--no-tags", "origin", branch], repo_root)
    if fetched.returncode != 0:
        raise SourceError(f"fetch of origin/{branch} failed (absent or unreachable)")
    tip = _git(["rev-parse", "--verify", f"origin/{branch}"], repo_root)
    if tip.returncode != 0:
        raise SourceError(f"origin/{branch} has no resolvable tip after fetch")
    sha = tip.stdout.strip()
    blob = _git(["show", f"origin/{branch}:{path}"], repo_root)
    if blob.returncode != 0:
        raise SourceError(f"{path} absent on origin/{branch}@{sha[:8]}")
    return Evidence(sha=sha, text=blob.stdout)


# --------------------------------------------------------------------------
# Pure evaluation.
# --------------------------------------------------------------------------

def is_due(now_utc: datetime) -> tuple[bool, str]:
    """Weekday at/after 08:00 PT -> due. Pure; returns (due, reason)."""
    if now_utc.tzinfo is None:
        raise ValueError("is_due requires a tz-aware datetime")
    now_pt = now_utc.astimezone(PT_TZ)
    if now_pt.weekday() >= 5:
        return False, "weekend"
    if now_pt.time() < DUE_THRESHOLD_PT:
        return False, f"before {DUE_THRESHOLD_PT.strftime('%H:%M')} PT threshold"
    return True, "weekday at/after threshold"


def _parse_aware(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} missing or not a string")
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"{field} is not ISO-8601: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} is naive (no UTC offset): {value!r}")
    return parsed


def evaluate_record(now_utc: datetime, text: str) -> Verdict:
    """Validate one published record against ``now_utc``. Pure."""
    now_pt = now_utc.astimezone(PT_TZ)
    base = {"now_pt": now_pt.isoformat()}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return Verdict(RED, f"malformed JSON: {exc.msg}", base)
    if not isinstance(data, dict):
        return Verdict(RED, "malformed record: not a JSON object", base)
    try:
        slot = _parse_aware(data.get("slot_utc"), "slot_utc")
        saved = _parse_aware(data.get("saved_at_utc"), "saved_at_utc")
    except ValueError as exc:
        return Verdict(RED, f"malformed record: {exc}", base)
    details = {**base, "slot_utc": slot.isoformat(), "saved_at_utc": saved.isoformat()}

    slot_pt = slot.astimezone(PT_TZ)
    saved_pt = saved.astimezone(PT_TZ)
    today = now_pt.date()
    if slot_pt.date() > today or saved_pt.date() > today:
        return Verdict(RED, "future-dated record (slot or saved_at after today PT)", details)
    if slot_pt.date() < today or saved_pt.date() < today:
        return Verdict(
            RED,
            f"stale record: last delivery {slot_pt.date().isoformat()} PT, no hourly delivery today",
            details,
        )
    if (slot_pt.hour, slot_pt.minute) not in ALLOWED_PT_SLOTS or slot_pt.second or slot_pt.microsecond:
        return Verdict(RED, f"non-canonical slot {slot_pt.strftime('%H:%M:%S')} PT", details)
    if saved < slot:
        return Verdict(RED, "inconsistent record: saved_at_utc precedes slot_utc", details)
    if saved > now_utc:
        return Verdict(RED, "future record: saved_at_utc is after now", details)
    return Verdict(HEALTHY, f"hourly slot {slot_pt.strftime('%H:%M')} PT delivered today", details)


def evaluate(
    now_utc: datetime,
    load_evidence: Callable[[], Evidence],
) -> Verdict:
    """Due check first (no fetch when NOT_DUE), then evidence, then record."""
    due, why = is_due(now_utc)
    now_pt = now_utc.astimezone(PT_TZ).isoformat()
    if not due:
        return Verdict(NOT_DUE, why, {"now_pt": now_pt})
    try:
        evidence = load_evidence()
    except SourceError as exc:
        return Verdict(RED, f"no published evidence: {exc}", {"now_pt": now_pt})
    verdict = evaluate_record(now_utc, evidence.text)
    return Verdict(verdict.state, verdict.reason, {**verdict.details, "publish_sha": evidence.sha})


# --------------------------------------------------------------------------
# CLI.
# --------------------------------------------------------------------------

def _format(verdict: Verdict) -> str:
    kv = " ".join(f"{k}={v}" for k, v in verdict.details.items())
    return f"hourly-liveness: {verdict.state} reason=\"{verdict.reason}\" {kv}".rstrip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="check_hourly_liveness")
    parser.add_argument(
        "--branch",
        default=os.environ.get("PUBLISH_BRANCH", "publish"),
        help="publish branch on origin carrying delivery evidence (default: $PUBLISH_BRANCH or 'publish')",
    )
    parser.add_argument("--path", default=DEFAULT_PATH, help="evidence path on that branch")
    parser.add_argument(
        "--now",
        default=None,
        help="tz-aware ISO-8601 instant to evaluate at (tests/ops only; default: real UTC now)",
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.now is not None:
        try:
            now_utc = _parse_aware(args.now, "--now").astimezone(timezone.utc)
        except ValueError as exc:
            print(f"hourly-liveness: usage error: {exc}", file=sys.stderr)
            return 2
    else:
        now_utc = datetime.now(timezone.utc)
    repo_root = Path(args.repo_root)
    verdict = evaluate(now_utc, lambda: read_published_record(args.branch, args.path, repo_root))
    print(_format(verdict))
    if verdict.state == RED:
        print(
            "hourly-liveness: no same-day hourly delivery evidence on the publish branch; "
            "the Cloudflare clock (authoritative) or its dispatch credential needs owner attention.",
            file=sys.stderr,
        )
    return verdict.exit_code


if __name__ == "__main__":
    sys.exit(main())
