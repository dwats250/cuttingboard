#!/usr/bin/env python3
"""Macro-Awareness producer (PRD-187) - isolated, observe-only sidecar.

Once-per-dispatch, pull a fixed allowlist of central-bank official feeds, ask an
Anthropic model to CLASSIFY + SELECT (at most one item, assign an event_type from
a fixed enum - it authors no narrative), then write a controlled, semantic-safe
snapshot describing an unscheduled STRUCTURAL regime shock, QUIET by default.

Doctrine (PRD-187):
- R1 Isolation: NO import from cuttingboard/. anthropic/feedparser/requests are
  lazy-imported inside functions so the offline test suite needs none installed.
- R3 Schema: the text fields (source_name/url/published_at/source_excerpt) come
  from the feed entry verbatim; the model only returns {shock_present,
  selected_index, event_type}. No bias/confidence/forecast/posture/transmission.
- R4 Fail-closed: ambiguity -> QUIET; any fetch/parse/validation/credential
  failure preserves the prior snapshot byte-identical and exits non-zero; snapshot
  and novelty state publish as one coherent generation or neither.
- R5 Novelty: identity = (event_type, source_entity, normalized_event_date);
  suppressed for 5 trading days unless event_type changes.
- R6 Source authority: source_url domain MUST be in the allowlist.

This module MUST NOT import anything from cuttingboard/ (R1).
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Frozen contract constants (PRD-187 R3/R5/R6)
# ---------------------------------------------------------------------------

SCHEMA_VERSION = 1
SNAPSHOT_PATH = Path("logs/macro_awareness_snapshot.json")
STATE_PATH = Path("logs/macro_awareness_state.json")

DEFAULT_MODEL = "claude-opus-4-8"
RECENCY_HOURS = 36
EXCERPT_MAX = 280
NOVELTY_TTL_TRADING_DAYS = 5

# Fixed structural event-type enum. The model selects one of these; it does not
# invent labels. These are regime-level classes only (R5 materiality).
EVENT_TYPES = (
    "POLICY_REGIME_SHIFT",
    "SOVEREIGN_CREDIT_RUPTURE",
    "FX_PEG_BREAK",
    "GEOPOLITICAL_CROSS_ASSET_SHOCK",
)


@dataclass(frozen=True)
class FeedSource:
    name: str
    entity: str
    feed_url: str
    domain: str


# v1 allowlist: central-bank official channels only. Wires are NOT auto-authoritative
# and are intentionally excluded; adding any requires a follow-up PRD.
FEED_SOURCES = (
    FeedSource("Federal Reserve", "Fed",
               "https://www.federalreserve.gov/feeds/press_all.xml", "federalreserve.gov"),
    FeedSource("European Central Bank", "ECB",
               "https://www.ecb.europa.eu/rss/press.html", "ecb.europa.eu"),
    FeedSource("Bank of Japan", "BoJ",
               "https://www.boj.or.jp/en/rss/whatsnew.xml", "boj.or.jp"),
    FeedSource("Bank of England", "BoE",
               "https://www.bankofengland.co.uk/boeapps/rss/feeds.aspx?feed=News", "bankofengland.co.uk"),
    FeedSource("People's Bank of China", "PBoC",
               "http://www.pbc.gov.cn/en/3688110/3688172/index.rss", "pbc.gov.cn"),
)

ALLOWLIST_DOMAINS = frozenset(s.domain for s in FEED_SOURCES)
ALLOWLIST_NAMES = frozenset(s.name for s in FEED_SOURCES)

_TOP_KEYS = frozenset({"schema_version", "generated_at", "status", "shock"})
_SHOCK_KEYS = frozenset(
    {"event_type", "source_name", "source_url", "published_at", "source_excerpt", "detected_at"}
)

# Belt-and-suspenders: forbidden notions that must never appear at any nesting
# level (the schema only allows the keys above; this catches drift).
_FORBIDDEN_KEYS = frozenset({
    "macro_bias", "bias", "confidence_score", "confidence", "forecast", "projection",
    "posture", "direction", "recommended_direction", "recommendation", "sentiment",
    "transmission", "observed_transmission", "label", "evidence",
})


# ---------------------------------------------------------------------------
# Small pure helpers
# ---------------------------------------------------------------------------

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_iso(value: object) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt


def _domain_of(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def _domain_in_allowlist(url: str) -> bool:
    dom = _domain_of(url)
    return any(dom == d or dom.endswith("." + d) for d in ALLOWLIST_DOMAINS)


def add_trading_days(start: datetime, n: int) -> datetime:
    """Advance n weekdays from start (skips Sat/Sun). Holidays are not modelled
    (documented approximation for the 5-trading-day novelty TTL)."""
    cur = start
    added = 0
    while added < n:
        cur = cur + timedelta(days=1)
        if cur.weekday() < 5:  # Mon-Fri
            added += 1
    return cur


def _log(reason: str) -> None:
    """Emit an explicit, single-line reason to stderr (no silent fallback, R4)."""
    print(json.dumps({"macro_awareness": reason}), file=sys.stderr)


# ---------------------------------------------------------------------------
# Schema validation (PRD-187 R3) - shared by tool, workflow gate, and tests
# ---------------------------------------------------------------------------

def _scan_forbidden(obj: object, errors: list[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _FORBIDDEN_KEYS:
                errors.append(f"forbidden field present: {k}")
            _scan_forbidden(v, errors)
    elif isinstance(obj, list):
        for item in obj:
            _scan_forbidden(item, errors)


def validate_snapshot(snap: object) -> list[str]:
    """Return a list of R3 contract violations; empty list == valid."""
    errors: list[str] = []
    if not isinstance(snap, dict):
        return ["snapshot is not an object"]

    if set(snap.keys()) != set(_TOP_KEYS):
        errors.append(f"top-level keys {sorted(snap.keys())} != {sorted(_TOP_KEYS)}")

    if snap.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version mismatch")
    if _parse_iso(snap.get("generated_at")) is None:
        errors.append("generated_at missing/naive/unparseable")

    status = snap.get("status")
    if status not in ("QUIET", "SHOCK"):
        errors.append(f"invalid status: {status!r}")

    shock = snap.get("shock")
    if status == "QUIET" and shock is not None:
        errors.append("status QUIET requires shock=null")
    if status == "SHOCK":
        if not isinstance(shock, dict):
            errors.append("status SHOCK requires a shock object")
        else:
            if set(shock.keys()) != set(_SHOCK_KEYS):
                errors.append(f"shock keys {sorted(shock.keys())} != {sorted(_SHOCK_KEYS)}")
            if shock.get("event_type") not in EVENT_TYPES:
                errors.append("event_type not in enum")
            url = shock.get("source_url")
            if not isinstance(url, str) or not _domain_in_allowlist(url):
                errors.append("source_url domain not in allowlist")
            if shock.get("source_name") not in ALLOWLIST_NAMES:
                errors.append("source_name not in allowlist")
            if _parse_iso(shock.get("published_at")) is None:
                errors.append("published_at missing/naive/unparseable")
            if _parse_iso(shock.get("detected_at")) is None:
                errors.append("detected_at missing/naive/unparseable")
            excerpt = shock.get("source_excerpt")
            if not isinstance(excerpt, str) or not excerpt:
                errors.append("source_excerpt missing/empty")
            elif len(excerpt) > EXCERPT_MAX:
                errors.append("source_excerpt exceeds length cap")
            elif html.escape(html.unescape(excerpt)) != excerpt:
                errors.append("source_excerpt is not HTML-escaped")

    _scan_forbidden(snap, errors)
    return errors


# ---------------------------------------------------------------------------
# Feed fetch (lazy imports; injectable for tests)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Entry:
    source_name: str
    entity: str
    domain: str
    title: str
    summary: str
    link: str
    published_at: str  # ISO-8601 UTC with tz


def fetch_entries(now: datetime, *, timeout: float = 10.0, retries: int = 3) -> list[Entry]:
    """Fetch + parse the FEED_SOURCES allowlist into recent Entry rows.

    Lazy-imports requests + feedparser so the offline test suite (which injects a
    fetch function) never needs them installed (R1/R7)."""
    import time

    import feedparser  # lazy (not in base test env)
    import requests  # lazy

    cutoff = now - timedelta(hours=RECENCY_HOURS)
    entries: list[Entry] = []
    any_ok = False

    for src in FEED_SOURCES:
        body: Optional[bytes] = None
        for attempt in range(retries):
            try:
                resp = requests.get(src.feed_url, timeout=timeout)
                if resp.status_code == 200:
                    body = resp.content
                    break
            except requests.RequestException:
                pass
            time.sleep(2 ** attempt)
        if body is None:
            _log(f"feed unreachable: {src.entity}")
            continue
        any_ok = True
        parsed = feedparser.parse(body)
        for item in parsed.entries:
            pub = item.get("published_parsed") or item.get("updated_parsed")
            if pub is None:
                continue
            published = datetime(*pub[:6], tzinfo=timezone.utc)
            if published < cutoff:
                continue
            entries.append(Entry(
                source_name=src.name,
                entity=src.entity,
                domain=src.domain,
                title=str(item.get("title", "")).strip(),
                summary=str(item.get("summary", "")).strip(),
                link=str(item.get("link", "")).strip(),
                published_at=_iso(published),
            ))

    if not any_ok:
        raise RuntimeError("all feeds unreachable")
    return entries


# ---------------------------------------------------------------------------
# Classification (lazy import anthropic; injectable for tests)
# ---------------------------------------------------------------------------

_CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "shock_present": {"type": "boolean"},
        "selected_index": {"type": ["integer", "null"]},
        "event_type": {"type": ["string", "null"], "enum": list(EVENT_TYPES) + [None]},
    },
    "required": ["shock_present", "selected_index", "event_type"],
    "additionalProperties": False,
}

_CLASSIFY_SYSTEM = (
    "You are a classifier, not a writer. From the numbered central-bank feed items, "
    "decide whether ANY describes an UNSCHEDULED, STRUCTURAL regime shock - a "
    "policy-regime change (e.g. exiting ZIRP/YCC), a sovereign/credit rupture, an FX "
    "peg break, or a major geopolitical shock with cross-asset transmission. Routine "
    "scheduled releases, speeches, minutes, and ordinary news are NOT shocks. Default "
    "to shock_present=false when uncertain. If and only if there is a clear structural "
    "shock, set shock_present=true, selected_index to the single most material item's "
    "number, and event_type to the matching enum value. Do not write any prose; only "
    "return the structured fields."
)


def classify(entries: list[Entry], *, model: str = DEFAULT_MODEL) -> dict:
    """Ask the model to classify + select. Returns {shock_present, selected_index,
    event_type}. Lazy-imports anthropic. Raises on malformed output (caller treats
    as fail-closed)."""
    import anthropic  # lazy (not in base test env)

    if not entries:
        return {"shock_present": False, "selected_index": None, "event_type": None}

    listing = "\n".join(
        f"[{i}] ({e.entity}) {e.title} | {e.summary[:300]}" for i, e in enumerate(entries)
    )
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    resp = client.messages.create(
        model=model,
        max_tokens=512,
        system=_CLASSIFY_SYSTEM,
        messages=[{"role": "user", "content": f"Feed items:\n{listing}"}],
        output_config={"format": {"type": "json_schema", "schema": _CLASSIFY_SCHEMA}},
    )
    text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), "")
    return json.loads(text)  # JSONDecodeError -> caller fail-closes


# ---------------------------------------------------------------------------
# Snapshot construction + novelty (pure; directly unit-tested)
# ---------------------------------------------------------------------------

def _quiet(now: datetime) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _iso(now),
        "status": "QUIET",
        "shock": None,
    }


def build_snapshot(entries: list[Entry], classification: dict, now: datetime) -> dict:
    """Turn a classification + the selected feed entry into a snapshot (pre-novelty).

    The text fields are taken verbatim from the feed entry; the model contributed
    only event_type + selection. Fail-closed to QUIET on any inconsistency."""
    if not classification.get("shock_present"):
        return _quiet(now)
    idx = classification.get("selected_index")
    event_type = classification.get("event_type")
    if not isinstance(idx, int) or not (0 <= idx < len(entries)):
        _log("classification selected_index out of range -> QUIET")
        return _quiet(now)
    if event_type not in EVENT_TYPES:
        _log("classification event_type not in enum -> QUIET")
        return _quiet(now)
    entry = entries[idx]
    if not _domain_in_allowlist(entry.link):
        _log(f"selected entry domain not in allowlist -> QUIET ({entry.link})")
        return _quiet(now)

    excerpt_raw = entry.title if not entry.summary else f"{entry.title} - {entry.summary}"
    excerpt = html.escape(excerpt_raw)[:EXCERPT_MAX]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _iso(now),
        "status": "SHOCK",
        "shock": {
            "event_type": event_type,
            "source_name": entry.source_name,
            "source_url": entry.link,
            "published_at": entry.published_at,
            "source_excerpt": excerpt,
            "detected_at": _iso(now),
        },
    }


def _identity(entity: str, event_type: str, event_date: str) -> str:
    return f"{entity}|{event_type}|{event_date}"


def apply_novelty(snapshot: dict, state: dict, now: datetime) -> tuple[dict, dict]:
    """Suppress a SHOCK whose identity was seen within the TTL (unless event_type
    changed). Returns (snapshot, new_state). Pure given `now`."""
    new_state = {"version": 1, "seen": []}
    # prune expired
    for rec in state.get("seen", []) if isinstance(state, dict) else []:
        first = _parse_iso(rec.get("first_detected"))
        if first is None:
            continue
        if now <= add_trading_days(first, NOVELTY_TTL_TRADING_DAYS):
            new_state["seen"].append(rec)

    if snapshot.get("status") != "SHOCK":
        return snapshot, new_state

    shock = snapshot["shock"]
    entity = shock["source_name"]
    event_type = shock["event_type"]
    event_date = (shock.get("published_at") or "")[:10]
    key = _identity(entity, event_type, event_date)

    for rec in new_state["seen"]:
        if rec.get("entity") == entity and rec.get("event_date") == event_date:
            if rec.get("event_type") == event_type:
                _log(f"novelty suppression (seen within TTL): {key}")
                return _quiet(now), new_state
            # event_type changed -> material update; refresh the record
            rec["event_type"] = event_type
            rec["first_detected"] = _iso(now)
            return snapshot, new_state

    new_state["seen"].append({
        "entity": entity,
        "event_type": event_type,
        "event_date": event_date,
        "first_detected": _iso(now),
    })
    return snapshot, new_state


# ---------------------------------------------------------------------------
# Atomic coherent write (R4: both-or-neither)
# ---------------------------------------------------------------------------

def _write_atomic(snapshot: dict, state: dict, snapshot_path: Path, state_path: Path) -> None:
    """Publish snapshot + state as one generation, both-or-neither (R4).

    os.replace is atomic per file, so the only failure window is between the two
    replaces. We capture the prior snapshot and, if the state replace fails after
    the snapshot replace, roll the snapshot back to its prior generation - so a
    partial write never leaves snapshot and state out of sync."""
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    prior_snapshot = snapshot_path.read_bytes() if snapshot_path.exists() else None
    snap_tmp = snapshot_path.with_suffix(".json.tmp")
    state_tmp = state_path.with_suffix(".json.tmp")
    snap_tmp.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    state_tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Both staged; now publish as one generation.
    snap_tmp.replace(snapshot_path)
    try:
        state_tmp.replace(state_path)
    except Exception:
        # Roll the snapshot back so snapshot/state never diverge (R4).
        if prior_snapshot is not None:
            snapshot_path.write_bytes(prior_snapshot)
        else:
            snapshot_path.unlink(missing_ok=True)
        state_tmp.unlink(missing_ok=True)
        raise


def _load_state(state_path: Path) -> dict:
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "seen": []}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run(
    *,
    now: Optional[datetime] = None,
    snapshot_path: Path = SNAPSHOT_PATH,
    state_path: Path = STATE_PATH,
    model: str = DEFAULT_MODEL,
    fetch_fn: Callable[[datetime], list[Entry]] = None,  # type: ignore[assignment]
    classify_fn: Callable[[list[Entry]], dict] = None,  # type: ignore[assignment]
) -> int:
    """Produce one snapshot. Returns 0 on a successful (QUIET or SHOCK) generation,
    1 on a hard failure (prior artifacts left byte-identical)."""
    now = now or _now_utc()
    fetch_fn = fetch_fn or (lambda n: fetch_entries(n))
    classify_fn = classify_fn or (lambda e: classify(e, model=model))

    if not os.environ.get("ANTHROPIC_API_KEY"):
        _log("ANTHROPIC_API_KEY unset -> no network call, prior snapshot preserved")
        return 1

    try:
        entries = fetch_fn(now)
        classification = classify_fn(entries)
        snapshot = build_snapshot(entries, classification, now)
        state = _load_state(state_path)
        snapshot, new_state = apply_novelty(snapshot, state, now)
    except Exception as exc:  # fail-closed: never fabricate, preserve prior
        _log(f"producer failure ({type(exc).__name__}) -> prior snapshot preserved")
        return 1

    errors = validate_snapshot(snapshot)
    if errors:
        _log(f"self-validation failed -> prior snapshot preserved: {errors}")
        return 1

    try:
        _write_atomic(snapshot, new_state, snapshot_path, state_path)
    except Exception as exc:  # fail-closed: prior generation left intact
        _log(f"atomic write failed -> prior generation preserved: {exc}")
        return 1
    _log(f"published status={snapshot['status']}")
    return 0


def _validate_only(path: str) -> int:
    """Pre-commit gate (R7): re-validate an on-disk snapshot against the full R3
    contract. Exit 0 if valid, 1 otherwise."""
    try:
        snap = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _log(f"validate-only: unreadable snapshot: {exc}")
        return 1
    errors = validate_snapshot(snap)
    if errors:
        _log(f"validate-only: invalid snapshot: {errors}")
        return 1
    _log("validate-only: snapshot valid")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Macro-Awareness producer (PRD-187)")
    parser.add_argument("--snapshot-path", default=str(SNAPSHOT_PATH))
    parser.add_argument("--state-path", default=str(STATE_PATH))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--validate-only", metavar="PATH", default=None,
                        help="Re-validate an on-disk snapshot and exit (workflow gate).")
    args = parser.parse_args(argv)

    if args.validate_only is not None:
        return _validate_only(args.validate_only)

    return run(
        snapshot_path=Path(args.snapshot_path),
        state_path=Path(args.state_path),
        model=args.model,
    )


if __name__ == "__main__":
    raise SystemExit(main())
