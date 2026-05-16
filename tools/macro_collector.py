#!/usr/bin/env python3
"""Upstream macro collector sidecar (PRD-139).

Pulls a fixed RSS allowlist, summarizes via Anthropic structured-JSON output,
and atomically writes a typed snapshot to logs/macro_regime_snapshot.json.

Sidecar-only. No cuttingboard imports. No runtime consumers.
Run: python3 tools/macro_collector.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

FEEDS: tuple[str, ...] = (
    "https://www.federalreserve.gov/feeds/press_all.xml",
    "https://home.treasury.gov/system/files/126/ofac_press_releases.xml",
    "https://www.bls.gov/feed/bls_latest.rss",
)
SNAPSHOT_PATH: Path = Path("logs/macro_regime_snapshot.json")
TMP_PATH: Path = Path("logs/macro_regime_snapshot.json.tmp")
MODEL_ID: str = "claude-sonnet-4-6"
FEED_TIMEOUT_S: int = 10
BACKOFF_SCHEDULE_S: tuple[int, ...] = (1, 2, 4)
ALLOWED_BIAS: frozenset[str] = frozenset({"RISK_ON", "RISK_OFF", "NEUTRAL", "CHAOTIC"})
EXPECTED_KEYS: frozenset[str] = frozenset(
    {"macro_bias", "confidence_score", "fundamental_driver", "timestamp"}
)


def _err(msg: str) -> None:
    sys.stderr.write(json.dumps({"error": msg}) + "\n")


def _cleanup_tmp() -> None:
    try:
        TMP_PATH.unlink()
    except FileNotFoundError:
        pass


def fetch_feed(url: str) -> str:
    last_exc: Exception | None = None
    for delay in BACKOFF_SCHEDULE_S:
        try:
            with urllib.request.urlopen(url, timeout=FEED_TIMEOUT_S) as resp:
                status = getattr(resp, "status", 200)
                if status != 200:
                    raise urllib.error.HTTPError(url, status, "non-200", resp.headers, None)
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:
            last_exc = exc
            time.sleep(delay)
    raise RuntimeError(f"feed failed after retries: {url}: {last_exc}")


def fetch_all_feeds() -> str:
    return "\n\n".join(fetch_feed(url) for url in FEEDS)


def call_anthropic(text: str) -> dict[str, Any]:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=MODEL_ID,
        max_tokens=512,
        system=(
            "Return ONE flat JSON object with keys: "
            "macro_bias (RISK_ON|RISK_OFF|NEUTRAL|CHAOTIC), "
            "confidence_score (float 0..1), "
            "fundamental_driver (<=280 chars), "
            "timestamp (UTC ISO-8601 with Z or +00:00). "
            "JSON only, no prose, no fences."
        ),
        messages=[{"role": "user", "content": text[:200_000]}],
    )
    raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned non-JSON: {exc}") from exc


def validate_snapshot(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, dict) or set(obj.keys()) != set(EXPECTED_KEYS):
        raise ValueError(f"key set mismatch: {sorted(obj) if isinstance(obj, dict) else type(obj)}")
    if obj["macro_bias"] not in ALLOWED_BIAS:
        raise ValueError(f"macro_bias invalid: {obj['macro_bias']!r}")
    score = obj["confidence_score"]
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0.0 <= float(score) <= 1.0:
        raise ValueError(f"confidence_score out of range: {score!r}")
    drv = obj["fundamental_driver"]
    if not isinstance(drv, str) or not drv or len(drv) > 280:
        raise ValueError("fundamental_driver invalid")
    ts = obj["timestamp"]
    if not isinstance(ts, str) or not (ts.endswith("Z") or ts.endswith("+00:00")):
        raise ValueError(f"timestamp lacks tz suffix: {ts!r}")
    try:
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"timestamp not ISO-8601: {ts!r}") from exc
    return obj


def write_atomic(snapshot: dict[str, Any]) -> None:
    TMP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TMP_PATH.open("w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2, sort_keys=True)
    os.replace(TMP_PATH, SNAPSHOT_PATH)


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        _err("ANTHROPIC_API_KEY unset")
        return 1
    try:
        text = fetch_all_feeds()
    except Exception as exc:
        _err(f"feed deprivation: {exc}")
        _cleanup_tmp()
        return 1
    try:
        snapshot = validate_snapshot(call_anthropic(text))
    except ValueError as exc:
        _err(f"LLM schema mismatch: {exc}")
        _cleanup_tmp()
        return 1
    write_atomic(snapshot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
