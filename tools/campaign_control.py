"""Campaign control plane -- PRD-302 Slice-A bootstrap tool.

Slice A is a bounded, non-authoritative owner-decision coordination bootstrap.
This tool turns ONE fixed synthetic normalized event into ONE schema-valid,
explicitly non-authoritative proposed charge rendered inside a fixed
NOT-AUTHORITY wrapper. It has NO network access, reads only the files it is
given, and emits only generic fail-closed diagnostics that never echo event or
model content.

CLASS CONTRACT (PRD-302): the normalized-event and charge shapes are internal
job-boundary contracts. `.github/campaign/charge.schema.json` is kept in
lockstep with the validators here by the drift-guard tests
(tests/test_campaign_control.py). Standard library only.

See docs/prd_history/PRD-302.md (R1-R21) and the review-clean MATERIAL packet
audits/campaign-control-plane-material-packet-2026-08/PACKET.md.
"""
from __future__ import annotations

import argparse
import dataclasses
import glob
import html
import json
import os
import sys
from dataclasses import fields as dataclasses_fields  # noqa: F401 (public re-export)
from pathlib import Path
from typing import Any
import re

# --- identities / closed vocabulary (must equal charge.schema.json) ----------
SCHEMA_EVENT = "cuttingboard-campaign-event/v1"
SCHEMA_CHARGE = "cuttingboard-owner-charge/v1"
KIND = "OWNER_DECISION"

TRIGGERS = frozenset({
    "AUTHORITY_CONFLICT", "REVIEW_SPLIT", "FILES_LOC", "MATERIALITY",
    "PORTABILITY", "NEW_CONSUMER", "OTHER_BOUNDARY",
})
BOUNDARIES = frozenset({
    "SEMANTICS", "GOVERNANCE", "FILES_LOC", "TRUST", "PLATFORM",
    "CONSUMER", "EVIDENCE",
})
CONFIDENCE = frozenset({"HIGH", "MEDIUM", "LOW"})
OPTION_IDS = ("A", "B", "C")

EVENT_KEYS = frozenset({
    "schema", "source_comment_id", "campaign", "event_id", "kind",
    "pr_number", "head_sha", "trigger", "authority_boundary", "summary",
    "options", "recommended_option",
})
OPTION_KEYS = frozenset({"id", "label", "effect"})
CHARGE_KEYS = frozenset({
    "schema", "event_id", "head_sha", "recommended_option", "confidence",
    "rationale", "charge_markdown",
})

RE_CAMPAIGN = re.compile(r"^PRD-[0-9]{3}$")
RE_EVENT_ID = re.compile(r"^PRD-[0-9]{3}-E[0-9]{2}$")
RE_SHA = re.compile(r"^[0-9a-f]{40}$")

MAX_EVENT_BYTES = 8192
MAX_SUMMARY = 1200
MAX_LABEL = 80
MAX_EFFECT = 600
MAX_RATIONALE_CHARS = 2000
MAX_CHARGE_CHARS = 6000

FAIL_PREFIX = "campaign-control: FAIL"
DISCLOSURE = "requested model; served identity unverified"

# Enumerated runner-owned credential targets the R7 probe checks (relative to
# the resolved runner root), plus a glob for temp credentials.
CREDENTIAL_BASENAMES = (".credentials", ".credentials_migrated", ".runner")
REQUIRED_CREDENTIAL = ".credentials"


class CampaignError(Exception):
    """Stable code + safe message; NEVER embeds event/model/secret content."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _require(cond: bool, code: str, message: str) -> None:
    if not cond:
        raise CampaignError(code, message)


def _no_controls(text: str) -> bool:
    """True iff text has no ASCII control chars other than newline."""
    return all(ch == "\n" or ord(ch) >= 0x20 for ch in text)


def _exact_keys(obj: dict[str, Any], allowed: frozenset[str], code: str) -> None:
    _require(isinstance(obj, dict) and set(obj) == allowed, code,
             "object has unexpected or missing keys")


def _int_not_bool(value: Any, code: str) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool), code,
             "expected a non-boolean integer")
    return value


# --- data contracts ----------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class DecisionOption:
    id: str
    label: str
    effect: str


@dataclasses.dataclass(frozen=True)
class NormalizedEvent:
    schema: str
    source_comment_id: int
    campaign: str
    event_id: str
    kind: str
    pr_number: int
    head_sha: str
    trigger: str
    authority_boundary: str
    summary: str
    options: tuple[DecisionOption, ...]
    recommended_option: str


@dataclasses.dataclass(frozen=True)
class Charge:
    schema: str
    event_id: str
    head_sha: str
    recommended_option: str
    confidence: str
    rationale: str
    charge_markdown: str


@dataclasses.dataclass(frozen=True)
class CredentialObservation:
    """A gathered fact about one runner-owned credential target. Carries NO
    credential content -- only path, existence, owner uid, and readability by
    the Codex uid."""
    path: str
    exists: bool
    owner_uid: int | None
    readable_by_codex: bool


# --- event parsing -----------------------------------------------------------
def parse_event(obj: dict[str, Any]) -> NormalizedEvent:
    _exact_keys(obj, EVENT_KEYS, "event-keys")
    _require(obj["schema"] == SCHEMA_EVENT, "event-schema", "bad event schema")
    src = _int_not_bool(obj["source_comment_id"], "event-src")
    _require(src >= 0, "event-src", "bad source_comment_id")
    campaign = obj["campaign"]
    _require(isinstance(campaign, str) and bool(RE_CAMPAIGN.match(campaign)),
             "event-campaign", "bad campaign id")
    event_id = obj["event_id"]
    _require(isinstance(event_id, str) and bool(RE_EVENT_ID.match(event_id))
             and event_id.startswith(campaign + "-E"),
             "event-id", "bad event id")
    _require(obj["kind"] == KIND, "event-kind", "bad kind")
    pr = _int_not_bool(obj["pr_number"], "event-pr")
    _require(pr > 0, "event-pr", "bad pr_number")
    sha = obj["head_sha"]
    _require(isinstance(sha, str) and bool(RE_SHA.match(sha)),
             "event-sha", "bad head_sha")
    _require(obj["trigger"] in TRIGGERS, "event-trigger", "bad trigger")
    _require(obj["authority_boundary"] in BOUNDARIES, "event-boundary",
             "bad authority_boundary")
    summary = obj["summary"]
    _require(isinstance(summary, str) and 1 <= len(summary) <= MAX_SUMMARY
             and _no_controls(summary), "event-summary", "bad summary")
    options = _parse_options(obj["options"])
    rec = obj["recommended_option"]
    _require(rec in {o.id for o in options}, "event-rec", "bad recommendation")
    return NormalizedEvent(
        schema=SCHEMA_EVENT, source_comment_id=src, campaign=campaign,
        event_id=event_id, kind=KIND, pr_number=pr, head_sha=sha,
        trigger=obj["trigger"], authority_boundary=obj["authority_boundary"],
        summary=summary, options=options, recommended_option=rec)


def _parse_options(raw: Any) -> tuple[DecisionOption, ...]:
    _require(isinstance(raw, list) and 2 <= len(raw) <= 3, "opt-count",
             "options must be a list of 2-3")
    seen: set[str] = set()
    out: list[DecisionOption] = []
    for item in raw:
        _exact_keys(item, OPTION_KEYS, "opt-keys")
        oid = item["id"]
        _require(oid in OPTION_IDS and oid not in seen, "opt-id",
                 "bad or duplicate option id")
        seen.add(oid)
        label = item["label"]
        _require(isinstance(label, str) and 1 <= len(label) <= MAX_LABEL
                 and _no_controls(label), "opt-label", "bad label")
        effect = item["effect"]
        _require(isinstance(effect, str) and 1 <= len(effect) <= MAX_EFFECT
                 and _no_controls(effect), "opt-effect", "bad effect")
        out.append(DecisionOption(id=oid, label=label, effect=effect))
    return tuple(out)


# --- charge parsing ----------------------------------------------------------
def parse_charge(obj: dict[str, Any]) -> Charge:
    _exact_keys(obj, CHARGE_KEYS, "charge-keys")
    _require(obj["schema"] == SCHEMA_CHARGE, "charge-schema", "bad charge schema")
    eid = obj["event_id"]
    _require(isinstance(eid, str) and bool(RE_EVENT_ID.match(eid)),
             "charge-eid", "bad event id")
    sha = obj["head_sha"]
    _require(isinstance(sha, str) and bool(RE_SHA.match(sha)),
             "charge-sha", "bad head_sha")
    _require(obj["recommended_option"] in OPTION_IDS, "charge-rec",
             "bad recommendation")
    _require(obj["confidence"] in CONFIDENCE, "charge-conf", "bad confidence")
    rationale = obj["rationale"]
    _require(isinstance(rationale, str)
             and 1 <= len(rationale) <= MAX_RATIONALE_CHARS
             and _no_controls(rationale), "charge-rationale", "bad rationale")
    md = obj["charge_markdown"]
    _require(isinstance(md, str) and 1 <= len(md) <= MAX_CHARGE_CHARS,
             "charge-md", "bad charge_markdown")
    return Charge(schema=SCHEMA_CHARGE, event_id=eid, head_sha=sha,
                  recommended_option=obj["recommended_option"],
                  confidence=obj["confidence"], rationale=rationale,
                  charge_markdown=md)


# --- rendering ---------------------------------------------------------------
def neutralize(text: str) -> str:
    """HTML-escape and neutralize @-mentions. Model text is untrusted-shaped."""
    return html.escape(text, quote=True).replace("@", "&#64;")


def render_charge(event: NormalizedEvent, charge: Charge) -> str:
    _require(charge.event_id == event.event_id, "match-eid", "event id mismatch")
    _require(charge.head_sha == event.head_sha, "match-sha", "head sha mismatch")
    _require(charge.recommended_option == event.recommended_option,
             "match-rec", "recommendation mismatch")
    return (
        f"<!-- cuttingboard-campaign-charge:v1 event_id={event.event_id} "
        f"head_sha={event.head_sha} -->\n\n"
        "## PROPOSED OWNER CHARGE -- NOT AUTHORITY\n\n"
        "This is a read-only Codex proposal for Dustin to accept, edit, or "
        "reject. It does not approve, resume, modify, dispatch, or merge "
        "anything.\n\n"
        f"_Model provenance: {DISCLOSURE}._\n\n"
        f"<pre>{neutralize(charge.rationale)}</pre>\n\n"
        f"<pre>{neutralize(charge.charge_markdown)}</pre>\n")


# --- synthetic event ---------------------------------------------------------
def make_dry_run_event(head_sha: str) -> NormalizedEvent:
    _require(isinstance(head_sha, str) and bool(RE_SHA.match(head_sha)),
             "dry-sha", "bad --head-sha")
    return NormalizedEvent(
        schema=SCHEMA_EVENT, source_comment_id=0, campaign="PRD-302",
        event_id="PRD-302-E01", kind=KIND, pr_number=1, head_sha=head_sha,
        trigger="OTHER_BOUNDARY", authority_boundary="EVIDENCE",
        summary="Slice-A synthetic dry-run event (fixed, non-adversarial).",
        options=(DecisionOption("A", "Hold", "Keep the current boundary."),
                 DecisionOption("B", "Amend", "Renew only the boundary.")),
        recommended_option="B")


def event_to_dict(event: NormalizedEvent) -> dict[str, Any]:
    return dataclasses.asdict(event)


# --- R7 credential-isolation probe: fail-closed decision logic ---------------
def evaluate_isolation(runner_uid: int, codex_uid: int, runner_root: str,
                       observations: list[CredentialObservation]) -> None:
    """Raise CampaignError unless credential isolation is AFFIRMATIVELY proven:
    the Codex uid differs from the runner uid, the runner root resolved, the
    required `.credentials` target exists and is runner-owned, and NO enumerated
    runner-owned credential is readable by the Codex uid. Absent/ambiguous/
    mis-owned targets are NOT proof of denial -> fail closed. Never inspects
    credential contents."""
    _require(codex_uid != runner_uid, "probe-same-uid",
             "codex uid equals runner uid")
    _require(bool(runner_root), "probe-root", "runner root not resolved")
    required = [o for o in observations
                if o.path.endswith("/" + REQUIRED_CREDENTIAL)
                or os.path.basename(o.path) == REQUIRED_CREDENTIAL]
    _require(len(required) == 1, "probe-missing-target",
             "required .credentials observation absent or ambiguous")
    cred = required[0]
    _require(cred.exists, "probe-absent", "required .credentials absent")
    _require(cred.owner_uid == runner_uid, "probe-owner",
             "required .credentials not runner-owned")
    for obs in observations:
        _require(not obs.readable_by_codex, "probe-readable",
                 "a runner-owned credential is readable by the codex uid")


def _gather_observations(runner_root: str) -> list[CredentialObservation]:
    paths = [os.path.join(runner_root, b) for b in CREDENTIAL_BASENAMES]
    runner_temp = os.environ.get("RUNNER_TEMP", "")
    if runner_temp:
        paths.extend(sorted(glob.glob(os.path.join(runner_temp, "*.credentials"))))
    obs: list[CredentialObservation] = []
    for p in paths:
        exists = os.path.exists(p)
        owner = os.stat(p).st_uid if exists else None
        readable = os.access(p, os.R_OK) if exists else False
        obs.append(CredentialObservation(path=p, exists=exists,
                                         owner_uid=owner,
                                         readable_by_codex=readable))
    return obs


# --- IO ----------------------------------------------------------------------
def load_event_bytes(raw: bytes) -> NormalizedEvent:
    _require(len(raw) <= MAX_EVENT_BYTES, "event-size", "event too large")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise CampaignError("event-utf8", "event is not valid utf-8")
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        raise CampaignError("event-json", "event is not valid json")
    return parse_event(obj)


def load_json(path: Path, code: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError:
        raise CampaignError(code, "input unreadable")
    _require(len(raw) <= MAX_EVENT_BYTES, code, "input too large")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise CampaignError(code, "input not valid json")
    _require(isinstance(obj, dict), code, "input is not an object")
    return obj


def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


# --- CLI ---------------------------------------------------------------------
def cmd_make_dry_run_event(args: argparse.Namespace) -> int:
    event = make_dry_run_event(args.head_sha)
    atomic_write(Path(args.event_output),
                 json.dumps(event_to_dict(event), indent=2) + "\n")
    return 0


def cmd_validate_charge(args: argparse.Namespace) -> int:
    event = parse_event(load_json(Path(args.event), "event-load"))
    charge = parse_charge(load_json(Path(args.charge), "charge-load"))
    atomic_write(Path(args.comment_output), render_charge(event, charge))
    return 0


def cmd_probe_isolation(args: argparse.Namespace) -> int:
    observations = _gather_observations(args.runner_root)
    evaluate_isolation(runner_uid=args.runner_uid, codex_uid=os.getuid(),
                       runner_root=args.runner_root, observations=observations)
    # identities + per-target booleans ONLY; never credential contents.
    print(f"isolation-probe: codex_uid={os.getuid()} runner_uid={args.runner_uid}")
    for obs in observations:
        print(f"isolation-probe: {obs.path} exists={obs.exists} "
              f"owner_uid={obs.owner_uid} readable_by_codex={obs.readable_by_codex}")
    print("isolation-probe: PASS (runner-owned credentials not readable by codex uid)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="campaign_control")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("make-dry-run-event")
    p1.add_argument("--head-sha", required=True)
    p1.add_argument("--event-output", required=True)
    p1.set_defaults(func=cmd_make_dry_run_event)

    p2 = sub.add_parser("validate-charge")
    p2.add_argument("--event", required=True)
    p2.add_argument("--charge", required=True)
    p2.add_argument("--comment-output", required=True)
    p2.set_defaults(func=cmd_validate_charge)

    p3 = sub.add_parser("probe-isolation")
    p3.add_argument("--runner-uid", required=True, type=int)
    p3.add_argument("--runner-root", required=True)
    p3.set_defaults(func=cmd_probe_isolation)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except CampaignError as exc:
        print(f"{FAIL_PREFIX} [{exc.code}] {exc.message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
