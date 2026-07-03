"""
Signal Forge dashboard renderer (PRD-055).

Reads logs/latest_payload.json, logs/latest_run.json, and
(optionally) logs/market_map.json.
Writes reports/output/dashboard.html.

No computation, inference, or engine logic permitted.
"""

from __future__ import annotations

import html as _html
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from cuttingboard import config
from cuttingboard.delivery.dashboard_integrator import (
    RULE2_LONG_VERDICT,
    RULE2_SHORT_VERDICT,
    dashboard_integrator,
)
from cuttingboard.delivery.macro_tape_layout import (
    MACRO_BIAS_CONTRA_CYCLICAL,
    MACRO_BIAS_DRIVERS,
    MACRO_ROW_1,
    MACRO_ROW_2,
    TRADABLES_ROW,
)
from cuttingboard.macro_pressure import build_macro_pressure
from cuttingboard.trade_decision import ALLOW_TRADE

# Dashboard sidecar dependencies (PRD-097 audit):
#   logs/latest_payload.json        — primary payload (overridden by --payload in hourly workflow)
#   logs/latest_run.json            — run metadata (overridden by --run in hourly workflow)
#   logs/latest_hourly_contract.json — contract entry prices via _load_contract_entry_context
#   logs/market_map.json            — symbol-level market context, loaded from logs_dir/market_map.json
#                                     (PRD-166: overridden by --market-map-path; the hourly workflow
#                                      passes logs/latest_hourly_market_map.json for lineage isolation)
#   logs/macro_drivers_snapshot.json — macro driver fallback when payload has no macro_drivers
#   logs/run_*.json                 — history runs, globbed from logs_dir
#
# Publish note: the hourly workflow renders dashboard HTML in CI with fresh market_map.json
# present locally. The published artifact is the rendered HTML. No sidecar publish change needed.

_PAYLOAD_PATH = Path("logs/latest_payload.json")
_RUN_PATH = Path("logs/latest_run.json")
_OUTPUT_PATH = Path("reports/output/dashboard.html")
_MACRO_SNAPSHOT_PATH = Path("logs/macro_drivers_snapshot.json")
_HOURLY_CONTRACT_PATH = Path("logs/latest_hourly_contract.json")
_TREND_STRUCTURE_PATH = Path("logs/trend_structure_snapshot.json")

# PRD-112: per-record fields the renderer requires for a non-degraded
# trend-structure section. Missing or wrong-typed for any curated symbol →
# whole section degrades to MISSING (R5 all-or-nothing rule).
_TREND_STRUCTURE_REQUIRED_FIELDS: tuple[str, ...] = (
    "symbol", "current_price", "vwap", "sma_50", "sma_200",
    "relative_volume", "price_vs_vwap", "price_vs_sma_50",
    "price_vs_sma_200", "trend_alignment", "entry_context", "data_status",
)

# PRD-130: deterministic unknown-state tokens emitted by
# cuttingboard.trend_structure are mapped here to compact operator-readable
# display text. AT_LEVEL renders as an affirmative neutral-comparison
# string (successful comparison, not an unavailable state). The
# renderer-only SESSION_UNAVAILABLE branch is handled by the existing
# INACTIVE_SESSION_LABEL / market-closed paths below, distinct from these
# per-cell tokens.
_TREND_STRUCTURE_STATE_DISPLAY: dict[str, str] = {
    "AT_LEVEL": "AT LEVEL",
    "INSUFFICIENT_HISTORY": "INSUFFICIENT HISTORY",
    "DATA_UNAVAILABLE": "DATA UNAVAILABLE",
    "NOT_COMPUTED": "NOT COMPUTED",
}


def _ts_display(token: str) -> str:
    return _TREND_STRUCTURE_STATE_DISPLAY.get(token, token)


# PRD-131 / PRD-208: deterministic composite display layer flattening the two SMA
# comparison tokens (price_vs_sma_50, price_vs_sma_200) into one short compact cell.
# Pure function of the input record. No VWAP, no narrative, no trajectory, no
# forecast vocabulary. Closed vocabulary. PRD-208 compresses the prose to a 3-state
# arrow scheme for cognitive compression: ABOVE=↑, BELOW=↓, AT_LEVEL== (a DISTINCT
# glyph per state), each suffixed with its SMA window. All 9 (3×3) combinations map.
_TREND_STRUCTURE_COMPOSITE_DISPLAY: dict[tuple[str, str], str] = {
    ("ABOVE", "ABOVE"):       "↑ 50 ↑ 200",
    ("ABOVE", "BELOW"):       "↑ 50 ↓ 200",
    ("BELOW", "ABOVE"):       "↓ 50 ↑ 200",
    ("BELOW", "BELOW"):       "↓ 50 ↓ 200",
    ("AT_LEVEL", "ABOVE"):    "= 50 ↑ 200",
    ("AT_LEVEL", "BELOW"):    "= 50 ↓ 200",
    ("ABOVE", "AT_LEVEL"):    "↑ 50 = 200",
    ("BELOW", "AT_LEVEL"):    "↓ 50 = 200",
    ("AT_LEVEL", "AT_LEVEL"): "= 50 = 200",
}

_TREND_STRUCTURE_COMPOSITE_UNAVAILABLE = "Structure unavailable"
_TREND_STRUCTURE_COMPOSITE_INSUFFICIENT = "SMA history insufficient"
_TREND_STRUCTURE_COMPOSITE_NOT_COMPUTED = "Structure not computed"


def _trend_structure_composite_display(record: dict) -> str:
    p50 = str(record.get("price_vs_sma_50", ""))
    p200 = str(record.get("price_vs_sma_200", ""))
    pair = (p50, p200)
    if "DATA_UNAVAILABLE" in pair:
        return _TREND_STRUCTURE_COMPOSITE_UNAVAILABLE
    if "INSUFFICIENT_HISTORY" in pair:
        return _TREND_STRUCTURE_COMPOSITE_INSUFFICIENT
    if "NOT_COMPUTED" in pair:
        return _TREND_STRUCTURE_COMPOSITE_NOT_COMPUTED
    return _TREND_STRUCTURE_COMPOSITE_DISPLAY[pair]


# PRD-132: deterministic Intraday Context display layer flattening the
# VWAP comparison token and the relative_volume float into one short
# positional phrase. Pure function of the input record. Strictly
# threshold-position vocabulary (no magnitude adjectives, no quality
# language). VWAP unknown-state precedence over RVOL.
_INTRADAY_RVOL_THRESHOLD: float = 1.5

_TREND_STRUCTURE_INTRADAY_DISPLAY: dict[tuple[str, str], str] = {
    ("ABOVE",    "AT_OR_ABOVE"): "Above VWAP, RVOL >= 1.5x",
    ("ABOVE",    "BELOW"):       "Above VWAP, RVOL < 1.5x",
    ("ABOVE",    "UNAVAILABLE"): "Above VWAP, RVOL unavailable",
    ("BELOW",    "AT_OR_ABOVE"): "Below VWAP, RVOL >= 1.5x",
    ("BELOW",    "BELOW"):       "Below VWAP, RVOL < 1.5x",
    ("BELOW",    "UNAVAILABLE"): "Below VWAP, RVOL unavailable",
    ("AT_LEVEL", "AT_OR_ABOVE"): "At VWAP, RVOL >= 1.5x",
    ("AT_LEVEL", "BELOW"):       "At VWAP, RVOL < 1.5x",
    ("AT_LEVEL", "UNAVAILABLE"): "At VWAP, RVOL unavailable",
}

_INTRADAY_VWAP_DATA_UNAVAILABLE = "Intraday N/A"
_INTRADAY_VWAP_NOT_COMPUTED = "VWAP N/A"


def _intraday_rvol_band(rvol: float | None) -> str:
    if rvol is None:
        return "UNAVAILABLE"
    try:
        f = float(rvol)
    except (TypeError, ValueError):
        return "UNAVAILABLE"
    if not math.isfinite(f):
        return "UNAVAILABLE"
    if f >= _INTRADAY_RVOL_THRESHOLD:
        return "AT_OR_ABOVE"
    return "BELOW"


def _trend_structure_intraday_display(record: dict) -> str:
    vwap_token = str(record.get("price_vs_vwap", ""))
    if vwap_token == "NOT_COMPUTED":
        return _INTRADAY_VWAP_NOT_COMPUTED
    # Any vwap token outside the {ABOVE, BELOW, AT_LEVEL} comparison set
    # (DATA_UNAVAILABLE today, plus any non-comparison sentinel a future
    # emitter or synthetic stress test might inject into the field) routes
    # through the data-unavailable branch — keeps the helper total over
    # arbitrary input strings while preserving the closed R1/R2 vocabulary.
    if vwap_token not in ("ABOVE", "BELOW", "AT_LEVEL"):
        return _INTRADAY_VWAP_DATA_UNAVAILABLE
    band = _intraday_rvol_band(record.get("relative_volume"))
    return _TREND_STRUCTURE_INTRADAY_DISPLAY[(vwap_token, band)]
HISTORY_LIMIT = 5
SCOREBOARD_LIMIT = 5  # render at most the 5 most-recent regime-history rows (was 10, PRD-177 R4)
_DASHBOARD_REFRESH_SECONDS = 30
DASHBOARD_STALE_AFTER_SECONDS = 300

_GRADE_ORDER: dict[str, int] = {"A+": 0, "A": 1, "B": 2, "C": 3, "D": 4, "F": 5}

_GRADE_CSS: dict[str, str] = {
    "A+": "aplus",
    "A": "a",
    "B": "b",
    "C": "c",
    "D": "d",
    "F": "f",
}

_HIGH_GRADES = frozenset({"A+", "A", "B"})
# PRD-168 D1/D2: the RULE2 "no qualifying setups" idle verdicts are suppressed
# when a high-grade card renders below them (UX preference). RULE3_MIXED is a
# real conflict signal and is deliberately NOT in this set.
_PRD168_GATED_VERDICTS = frozenset({RULE2_LONG_VERDICT, RULE2_SHORT_VERDICT})
_UNAVAILABLE_WATCH = "Market data unavailable for this run; review during live market session."

# PRD-117: enumerated session_type values that map to an inactive-session
# presentation label. Renderer-local only; runtime/contract are unchanged.
INACTIVE_SESSION_TYPES: frozenset[str] = frozenset({"SUNDAY_PREMARKET"})
INACTIVE_SESSION_LABEL: str = "SESSION INACTIVE"

_LIFECYCLE_BADGE_CSS: dict[str, str] = {
    "NEW":        "lifecycle-new",
    "UPGRADED":   "lifecycle-upgraded",
    "DOWNGRADED": "lifecycle-downgraded",
    "UNKNOWN":    "lifecycle-unknown",
}

_PT = ZoneInfo("America/Los_Angeles")


def format_dashboard_timestamp(value: str) -> tuple[str, str]:
    """Return (pacific_line, original_line) for display only. Input is never mutated.

    pacific_line: "YYYY-MM-DD HH:MM:SS PT" or "" on parse failure.
    original_line: readable original, e.g. "YYYY-MM-DD HH:MM:SS UTC".
    """
    raw = str(value) if value else ""
    cleaned = raw.replace("T", " ").rstrip("Z").strip()
    if raw.endswith("Z"):
        cleaned = cleaned + " UTC"
    try:
        if raw.endswith("Z"):
            dt_utc = datetime.fromisoformat(raw[:-1] + "+00:00")
        else:
            dt_utc = datetime.fromisoformat(raw)
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        dt_pt = dt_utc.astimezone(_PT)
        pacific_line = dt_pt.strftime("%Y-%m-%d %H:%M:%S") + " PT"
        return pacific_line, cleaned
    except Exception:
        return "", cleaned


def _compute_timestamp_freshness(value: str) -> str:
    """Return FRESH, STALE, or PARSE_ERROR based on age of a timestamp string."""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        age = (datetime.now(tz=timezone.utc) - dt).total_seconds()
        return "STALE" if age > DASHBOARD_STALE_AFTER_SECONDS else "FRESH"
    except (ValueError, TypeError):
        return "PARSE_ERROR"


def _parse_utc_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _run_snapshot_freshness_token(value: object, now: datetime) -> str:
    """PRD-167: relative-freshness token for the RUN SNAPSHOT field.

    future-dated or age < 60s -> "<1 min old"; 60s <= age <= 300s ->
    "N minute(s) old" (floored); age > 300s -> "STALE (>5 min)"; an
    absent/None/empty/unparseable source -> "unavailable". `now` is passed in
    (from `_utcnow()`) so the token is deterministic under a frozen clock.
    """
    parsed = _parse_utc_timestamp(value)
    if parsed is None:
        return "unavailable"
    age_seconds = (now - parsed).total_seconds()
    if age_seconds < 60:  # includes future-dated (negative age)
        return "<1 min old"
    if age_seconds <= DASHBOARD_STALE_AFTER_SECONDS:
        minutes = int(age_seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} old"
    return "STALE (>5 min)"


def _surface_age_token(parsed: datetime | None, now: datetime, absent_label: str) -> str:
    """PRD-189: coarse relative-age token for a pipeline-state surface (the live
    run, the scoreboard). Unlike the RUN SNAPSHOT token this expresses long ages
    in hours/days, so a frozen pipeline reads loudly stale instead of saturating
    at "STALE (>5 min)". ``parsed`` None -- an absent or unparseable source --
    renders ``absent_label``, never a misleading "0 min"/"<1 min" reading."""
    if parsed is None:
        return absent_label
    age = (now - parsed).total_seconds()
    if age < 60:  # includes future-dated (negative age)
        return "<1 min old"
    if age < 3600:
        minutes = int(age // 60)
        return f"{minutes} min old"
    if age < 86400:
        hours = int(age // 3600)
        return f"{hours} hr old"
    days = int(age // 86400)
    return f"{days} day{'s' if days != 1 else ''} old"


def _scoreboard_age_token(
    regime_history: list[dict] | None, now: datetime, absent_label: str
) -> str:
    """PRD-189: day-granular age of the newest logs/regime_history.jsonl record
    (the scoreboard's last dated row), computed from the rows the renderer
    already holds. Empty/absent history or an unparseable date renders
    ``absent_label``."""
    if not regime_history:
        return absent_label
    newest = None
    for row in regime_history:
        if not isinstance(row, dict):
            continue
        try:
            parsed = datetime.strptime(str(row.get("date")), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        if newest is None or parsed > newest:
            newest = parsed
    if newest is None:
        return absent_label
    days = (now.astimezone(timezone.utc).date() - newest).days
    if days <= 0:
        return "today"
    return f"{days} day{'s' if days != 1 else ''} old"


def _first_timestamp(obj: dict | None, paths: tuple[tuple[str, ...], ...]) -> tuple[object, datetime | None]:
    if not isinstance(obj, dict):
        return None, None
    for path in paths:
        current: object = obj
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        parsed = _parse_utc_timestamp(current)
        if parsed is not None:
            return current, parsed
    return None, None


def _timestamp_label(value: object, parsed: datetime | None) -> str:
    if parsed is None:
        return "unavailable"
    return str(value)


def _timestamp_older_than_baseline(value: datetime | None, baseline: datetime | None) -> bool:
    if value is None or baseline is None:
        return False
    return (baseline - value).total_seconds() > DASHBOARD_STALE_AFTER_SECONDS


class CoherentPublishError(RuntimeError):
    """PRD-118: raised when dashboard publish to `ui/` would emit an incoherent artifact set."""


class StalePublishError(RuntimeError):
    """PRD-119: raised when dashboard publish to `ui/` would emit stale artifacts."""


# PRD-119: freshness windows applied to ui/ publish.
LIVE_SESSION_MAX_AGE_MINUTES: int = 180
INACTIVE_SESSION_MAX_AGE_HOURS: int = 72


def _utcnow() -> datetime:
    """PRD-119: single indirection so tests can freeze the freshness reference time."""
    return datetime.now(timezone.utc)


def _parse_payload_timestamp(raw: object) -> datetime:
    """PRD-119 R5: strict ISO-8601 UTC parser; requires trailing 'Z'."""
    if not isinstance(raw, str) or not raw.strip():
        raise StalePublishError(
            f"payload.meta.timestamp missing or non-string: {raw!r}"
        )
    s = raw.strip()
    if not s.endswith("Z"):
        raise StalePublishError(
            f"payload.meta.timestamp not Zulu-formatted: {raw!r}"
        )
    try:
        parsed = datetime.fromisoformat(s[:-1] + "+00:00")
    except ValueError as exc:
        raise StalePublishError(
            f"payload.meta.timestamp unparseable: {raw!r} ({exc})"
        ) from None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(None):
        raise StalePublishError(
            f"payload.meta.timestamp not UTC: {raw!r}"
        )
    return parsed.astimezone(timezone.utc)


def _allowed_freshness_window(session_type: object) -> tuple[int, str]:
    """PRD-119: (max_age_seconds, label) keyed off payload.meta.session_type."""
    if isinstance(session_type, str) and session_type in INACTIVE_SESSION_TYPES:
        return INACTIVE_SESSION_MAX_AGE_HOURS * 3600, f"{INACTIVE_SESSION_MAX_AGE_HOURS}h"
    return LIVE_SESSION_MAX_AGE_MINUTES * 60, f"{LIVE_SESSION_MAX_AGE_MINUTES}m"


def _output_under_ui(output_path: Path) -> bool:
    """PRD-118: gate applies only when output_path resolves under the repo's `ui/` directory."""
    try:
        resolved = output_path.resolve()
    except Exception:
        resolved = output_path
    return "ui" in resolved.parts


def _coherent_generation_ids(
    payload: dict | None,
    run: dict | None,
    market_map: dict | None,
) -> tuple[str | None, str | None, str | None]:
    """Extract generation_ids from the exact paths defined by PRD-118 TERMINOLOGY.

    payload_generation_id := payload["meta"]["generation_id"]
    run_generation_id     := run["generation_id"]
    market_map_generation_id := market_map["generation_id"]

    Returns (payload_gid, run_gid, market_map_gid). Each entry is the stripped string
    if present and non-empty; otherwise None. No fallback paths, no fuzzy matching.
    """
    def _pick(obj: dict | None, *keys: str) -> str | None:
        cur: object = obj
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        if not isinstance(cur, str):
            return None
        s = cur.strip()
        return s or None

    return (
        _pick(payload, "meta", "generation_id"),
        _pick(run, "generation_id"),
        _pick(market_map, "generation_id"),
    )


def validate_coherent_publish(
    *,
    payload: dict | None,
    run: dict | None,
    market_map: dict | None,
    output_path: Path,
    fixture_mode: bool,
) -> None:
    """PRD-118 gate. No-op when output_path is not under `ui/`.

    Order of checks (each fails closed with deterministic stderr diagnostic):
      1. presence of payload/run/market_map dicts
      2. presence of payload.meta.generation_id, run.generation_id, market_map.generation_id
      3. fixture_mode kwarg OR FIXTURE_MODE=1 env var
      4. "fixture" substring in any generation_id
      5. exact string equality of all three generation_ids
    """
    if not _output_under_ui(output_path):
        return

    def _fail(msg: str) -> None:
        print(f"PRD-118 publish blocked: {msg}", file=sys.stderr)
        raise CoherentPublishError(msg)

    missing = []
    if not isinstance(payload, dict):
        missing.append("payload")
    if not isinstance(run, dict):
        missing.append("run")
    if not isinstance(market_map, dict):
        missing.append("market_map")
    if missing:
        _fail(f"missing artifact(s): {', '.join(missing)}")

    p_gid, r_gid, m_gid = _coherent_generation_ids(payload, run, market_map)

    missing_ids: list[str] = []
    if p_gid is None:
        missing_ids.append("payload.meta.generation_id")
    if r_gid is None:
        missing_ids.append("run.generation_id")
    if m_gid is None:
        missing_ids.append("market_map.generation_id")
    if missing_ids:
        _fail(f"missing generation_id at: {', '.join(missing_ids)}")

    if fixture_mode:
        _fail("fixture mode active (fixture_mode=True) for ui/ output")
    if os.environ.get("FIXTURE_MODE", "0") == "1":
        _fail("fixture mode active (FIXTURE_MODE=1) for ui/ output")

    fixture_hits: list[str] = []
    if "fixture" in p_gid:
        fixture_hits.append(f"payload={p_gid}")
    if "fixture" in r_gid:
        fixture_hits.append(f"run={r_gid}")
    if "fixture" in m_gid:
        fixture_hits.append(f"market_map={m_gid}")
    if fixture_hits:
        _fail(f"fixture artifact detected: {'; '.join(fixture_hits)}")

    if not (p_gid == r_gid == m_gid):
        _fail(
            f"generation_id mismatch: payload={p_gid} run={r_gid} market_map={m_gid}"
        )

    # PRD-119 R1/R6/R14: freshness gate executes only after PRD-118 coherent
    # checks succeed, reads `now` exactly once per invocation, and runs before
    # any output bytes are written.
    meta = payload.get("meta") or {}
    session_type = meta.get("session_type")
    session_label = session_type if isinstance(session_type, str) else "None"
    raw_ts = meta.get("timestamp")

    def _stale_fail(msg: str) -> None:
        print(f"PRD-119 publish blocked: {msg}", file=sys.stderr)
        raise StalePublishError(msg)

    try:
        parsed_ts = _parse_payload_timestamp(raw_ts)
    except StalePublishError as exc:
        # R5/R7: emit deterministic diagnostic for malformed timestamp.
        print(
            "PRD-119 publish blocked: "
            f"payload_timestamp={raw_ts!r} artifact_age=unavailable "
            f"window=unavailable session_type={session_label} ({exc})",
            file=sys.stderr,
        )
        raise

    now_utc = _utcnow()
    age_seconds = int((now_utc - parsed_ts).total_seconds())
    max_age_seconds, window_label = _allowed_freshness_window(session_type)

    if age_seconds > max_age_seconds:
        _stale_fail(
            f"stale payload: payload_timestamp={raw_ts} "
            f"artifact_age={age_seconds}s window={window_label} "
            f"session_type={session_label}"
        )


def _artifact_generation_id(obj: dict | None, paths: tuple[tuple[str, ...], ...]) -> str | None:
    if not isinstance(obj, dict):
        return None
    for path in paths:
        current: object = obj
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        if isinstance(current, str) and current:
            return current
    return None


def _generation_ids_mixed(*generation_ids: str | None) -> bool:
    present = [gid for gid in generation_ids if gid]
    return len(present) > 1 and len(set(present)) > 1


def _artifact_lineage_state(
    *,
    payload_available: bool,
    run_available: bool,
    market_map_available: bool,
    payload_generation_id: str | None,
    run_generation_id: str | None,
    market_map_generation_id: str | None,
    market_map_stale_for_run: bool,
) -> str:
    generation_ids = (
        payload_generation_id,
        run_generation_id,
        market_map_generation_id,
    )
    if (
        not payload_available
        or not run_available
        or not market_map_available
        or any(gid is None for gid in generation_ids)
    ):
        return "MISSING"
    if _generation_ids_mixed(*generation_ids):
        return "MIXED"
    if market_map_stale_for_run:
        return "STALE"
    return "COHERENT"


def _resolve_market_map(path: Path) -> tuple[str, dict | None]:
    """Load market_map from path and return (status, data).

    status: SOURCE_MISSING | PARSE_ERROR | STALE | FRESH
    data: loaded dict, or None on error/missing
    """
    if not path.exists():
        return "SOURCE_MISSING", None
    try:
        mtime_age = time.time() - os.path.getmtime(path)
    except OSError:
        return "SOURCE_MISSING", None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "PARSE_ERROR", None
    if mtime_age > DASHBOARD_STALE_AFTER_SECONDS:
        return "STALE", data
    return "FRESH", data


def _is_sunday_pt(value: str) -> bool:
    """Return True only if value parses to a Sunday in America/Los_Angeles. Fails closed."""
    try:
        raw = str(value) if value else ""
        if raw.endswith("Z"):
            dt_utc = datetime.fromisoformat(raw[:-1] + "+00:00")
        else:
            dt_utc = datetime.fromisoformat(raw)
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        return dt_utc.astimezone(_PT).weekday() == 6  # 6 = Sunday
    except Exception:
        return False


_TIER_DEFS = [
    ("aplus", "A+ — ACTIONABLE", frozenset({"A+"})),
    ("a",     "A — HIGH QUALITY", frozenset({"A"})),
    ("b",     "B — DEVELOPING",   frozenset({"B"})),
    ("c",     "C — EARLY",        frozenset({"C"})),
]

_CSS = (
    "*{box-sizing:border-box;margin:0;padding:0}"
    "body{background:#0d0d0d;color:#e0e0e0;font-family:monospace;padding:1rem}"
    ".wrap{max-width:640px;margin:0 auto}"
    ".block{border:1px solid #2a2a2a;border-radius:4px;margin-bottom:1rem;padding:1rem}"
    ".label{color:#888;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em}"
    ".value{margin-top:0.25rem}"
    ".value-key{margin-top:0.25rem;font-weight:bold}"
    ".row{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:0.5rem}"
    ".field{flex:1;min-width:120px}"
    ".badge{display:inline-block;padding:0.2rem 0.5rem;border-radius:3px;font-size:0.8rem}"
    ".RISK_ON{background:#1a3a1a;color:#4caf50}"
    ".RISK_OFF{background:#3a1a1a;color:#f44336}"
    ".NEUTRAL{background:#2a2a1a;color:#ff9800}"
    ".CHAOTIC{background:#3a1a3a;color:#e040fb}"
    ".STAY_FLAT{background:#1a1a2a;color:#90caf9}"
    ".AGGRESSIVE_LONG,.CONTROLLED_LONG{background:#1a3a1a;color:#4caf50}"
    ".DEFENSIVE_SHORT{background:#3a1a1a;color:#f44336}"
    ".NEUTRAL_PREMIUM{background:#2a2a1a;color:#ff9800}"
    ".halted{color:#f44336;font-weight:bold}"
    ".warn{color:#ff9800}"
    # PRD-219: distilled system-state verdict + context.
    ".sys-verdict{font-weight:bold;font-size:0.95rem;letter-spacing:0.02em}"
    ".sys-verdict.sys-up{color:#4caf50}"
    ".sys-verdict.sys-down{color:#f44336}"
    ".sys-verdict.sys-flat{color:#ff9800}"
    ".sys-verdict.sys-halt{color:#f44336}"
    ".sys-context{color:#888;font-size:0.8rem;margin-top:2px}"
    ".sys-context.halted{color:#f44336}"
    "h2{font-size:0.8rem;color:#888;text-transform:uppercase;"
    "letter-spacing:0.08em;margin-bottom:0.75rem}"
    ".sep{border-top:1px solid #1a1a1a;margin:0.5rem 0}"
    ".tape-slot{white-space:nowrap}"
    ".macro-tape-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));"
    "gap:6px 12px;margin-top:6px;overflow-x:hidden}"
    ".macro-drivers-row,.macro-spot-metals-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px 16px;margin-top:6px;overflow-x:hidden}"
    ".macro-tradables-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;"
    "margin-top:6px;overflow-x:hidden}"
    ".tradable-cell{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
    ".macro-tape-slot{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}"
    ".macro-tape-label{margin-right:0.25rem}"
    ".macro-tape-value{opacity:0.85}"
    ".candidate-card{border-left:3px solid #2a2a2a;padding:0.75rem;margin-bottom:0.5rem}"
    ".grade-aplus{border-left-color:#4caf50}"
    ".grade-a{border-left-color:#8bc34a}"
    ".grade-b{border-left-color:#ff9800}"
    ".grade-c{border-left-color:#607d8b;opacity:0.8}"
    ".grade-d{border-left-color:#f44336;opacity:0.7}"
    ".grade-f{border-left-color:#424242;opacity:0.5}"
    ".unavailable{color:#888}"
    ".macro-bias{margin-top:6px;font-weight:bold}"
    ".action-line{font-weight:bold;margin-bottom:8px;padding:8px 10px;"
    "border-left:3px solid #4a6fa5;background:#111827;font-size:0.9rem;"
    "letter-spacing:0.03em}"
    ".tier-group{margin-bottom:16px}"
    ".tier-header{font-weight:bold;margin-bottom:6px;opacity:0.9}"
    ".candidate-state{font-weight:bold;margin-bottom:4px}"
    ".candidate-risk{color:#ff9800}"
    ".tape-slot.up{color:#4caf50}"
    ".tape-slot.down{color:#f44336}"
    ".tape-slot.flat{color:#888}"
    ".tape-slot.na{color:#444;opacity:0.7}"
    ".macro-bias.long{color:#4caf50}"
    ".macro-bias.short{color:#f44336}"
    ".macro-bias.mixed{color:#ff9800}"
    ".tape-no-data{color:#888;font-style:italic;margin-top:4px;font-size:0.8rem}"
    ".idle-summary{color:#888;margin-bottom:12px;padding:8px;"
    "border-left:3px solid #2a2a2a}"
    ".lifecycle-badge{display:inline-block;padding:0.15rem 0.4rem;"
    "border-radius:3px;font-size:0.75rem;margin-left:0.5rem}"
    ".lifecycle-new{background:#0d2a3a;color:#29b6f6}"
    ".lifecycle-upgraded{background:#1a3a1a;color:#4caf50}"
    ".lifecycle-downgraded{background:#3a1a1a;color:#f44336}"
    ".lifecycle-unknown{background:#222;color:#555}"
    ".lifecycle-detail{color:#888;font-size:0.8rem;margin-bottom:4px}"
    ".removed-symbols{margin-top:12px}"
    ".removed-row{color:#888;font-size:0.8rem;padding:2px 0}"
    ".MIXED{background:#2a1a3a;color:#ba68c8}"
    ".UNKNOWN{background:#1a1a1a;color:#555}"
    # PRD-217: pressure phrases fold into one wrapping line beside the tally.
    ".macro-pressure-line{color:#aaa;font-size:0.72rem;margin-top:3px}"
    ".macro-pressure-line.pressure-na{color:#888;font-style:italic}"
    ".kv-grid{display:grid;grid-template-columns:max-content 1fr;gap:2px 0.75rem;margin-top:0.25rem}"
    ".history-table{display:grid;grid-template-columns:5ch max-content max-content max-content;"
    "column-gap:0.75rem;row-gap:2px;margin-top:4px;align-items:baseline}"
    ".history-cell{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:0.8rem}"
    ".lvl-diagram{margin-top:8px;padding-top:6px;border-top:1px solid #1a1a1a}"
    ".lvl-unavail{color:#555;font-size:0.75rem;font-style:italic;margin-top:6px}"
    ".artifact-warning{border-color:#ff9800;color:#ff9800}"
    ".artifact-diagnostics{color:#888;font-size:0.72rem;line-height:1.45}"
    ".artifact-diagnostics span{display:block}"
    "#artifact-diagnostics summary,#run-history summary,details.tier-group summary{cursor:pointer;list-style:none}"
    "#artifact-diagnostics summary::-webkit-details-marker,#run-history summary::-webkit-details-marker{display:none}"
    "#artifact-diagnostics summary{color:#555;font-size:0.72rem}"
    "#run-history summary{color:#aaa;font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em}"
    ".failed-card-fields{display:grid;grid-template-columns:1fr 1fr;gap:6px 8px;margin-top:4px}"
    ".failed-card-fields .label{font-size:0.7rem}"
    ".failed-card-fields .value{margin-top:1px}"
    ".macro-tally{color:#aaa;font-size:0.78rem;margin-top:2px}"
    "#red-folder .red-folder-event{font-size:0.78rem;margin-top:4px}"
    ".red-folder-when{color:#ddd}"
    ".red-folder-type{color:#888}"
    ".red-folder-expiry{color:#ff9800;font-size:0.72rem;margin-top:6px}"
    "#scoreboard .scoreboard-row{font-size:0.74rem;color:#bbb;display:flex;flex-wrap:wrap;gap:10px;margin-top:3px}"
    ".scoreboard-date{color:#ddd;min-width:80px}"
    ".scoreboard-spy{color:#888}"
    # PRD-215: "actionable now" accent (cyan #29b6f6 — the level/VWAP colour) on
    # the falsifiable trade fields, plus the collapsed REASON/PLAY/WATCH detail.
    ".value-actionable{color:#29b6f6}"
    ".card-detail summary{cursor:pointer;list-style:none;color:#888;font-size:0.72rem;"
    "text-transform:uppercase;letter-spacing:.05em;margin-top:4px}"
    ".card-detail summary::-webkit-details-marker{display:none}"
    # PRD-218: alignment-coloured price (bullish green / bearish red).
    ".ts-px-up{color:#4caf50}"
    ".ts-px-down{color:#f44336}"
    # PRD-213/PRD-218: below the mobile breakpoint each symbol reflows to one
    # compact inline row (per-cell labels hidden) rather than a tall stacked card.
    "@media(max-width:640px){"
    ".ts-table thead{position:absolute;left:-9999px}"
    ".ts-table,.ts-table tbody{display:block;width:100%}"
    ".ts-table tr{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 8px;"
    "border:1px solid #2a2a2a;border-radius:4px;margin-bottom:5px;padding:5px 8px}"
    # PRD-225: padding needs !important too — each td carries inline
    # "padding:2px 8px", which silently defeated the PRD-213 padding:0 half of
    # this rule (16px dead padding per cell, ~96px per row on a phone). The
    # flex gap, not padding, is the mobile cell separator.
    ".ts-table td{white-space:nowrap!important;padding:0!important}"
    ".ts-table td::before{content:none}"
    # PRD-225: min-widths right-sized in ch (text-width) units — the em values
    # carried ~34px/row of dead width that pushed the Intraday cell off-line.
    # Cross-card column alignment is preserved: 4ch covers every symbol, 7ch
    # every price in the traded universe.
    ".ts-table td:first-child{font-weight:bold;min-width:4ch}"
    ".ts-table td:nth-child(2){min-width:7ch}"          # price column aligns
    ".ts-table td.ts-intraday{color:#888}"  # muted; flows inline now that BULL/BEAR/MIX reclaimed the room
    # PRD-225: the Alignment token is the row's only variable-width cell
    # (MIX 3ch vs BULL/BEAR 4ch); equalize it so every row wraps identically.
    ".ts-table td.ts-align{min-width:4ch}"
    "}"
)

_UP   = "↑"
_DOWN = "↓"
_FLAT = "→"
_DASH = "—"

_ARROW_CSS: dict[str, str] = {_UP: "up", _DOWN: "down", _FLAT: "flat", _DASH: "na"}


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"Required file missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {path}: {exc}") from exc


def _load_json_optional(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {path}: {exc}") from exc


def _req(obj: dict, *keys: str) -> object:
    current = obj
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            raise RuntimeError(f"Required field missing: {'.'.join(keys)}")
        current = current[key]
    return current


def _load_trend_structure_snapshot(path: Path) -> dict | None:
    """PRD-112 R1/R5: read the sidecar; never raise. Return dict on success,
    None on missing/malformed/IO-error. Caller renders the all-MISSING state
    on None per R5's all-or-nothing rule."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _trend_symbols_usable(snapshot: dict | None) -> int:
    """PRD-120 / PRD-123: per-symbol *usable data* count.

    Returns the number of TREND_STRUCTURE_SYMBOLS whose record in
    `snapshot["symbols"]` (a) contains every field in
    `_TREND_STRUCTURE_REQUIRED_FIELDS` AND (b) carries
    `data_status != "MISSING"`. Shape-present-but-data-MISSING rows
    do NOT count — usable means usable data, not shape presence.
    """
    if not isinstance(snapshot, dict):
        return 0
    symbols = snapshot.get("symbols")
    if not isinstance(symbols, dict):
        return 0
    count = 0
    for sym in config.TREND_STRUCTURE_SYMBOLS:
        rec = symbols.get(sym)
        if not isinstance(rec, dict):
            continue
        if not all(field in rec for field in _TREND_STRUCTURE_REQUIRED_FIELDS):
            continue
        if rec.get("data_status") == "MISSING":
            continue
        count += 1
    return count


def _system_state_source_health(
    *,
    artifact_lineage_state: str,
    payload_timestamp_value: object,
) -> str:
    """PRD-120 SOURCE-HEALTH MAPPING for System State. First match wins."""
    if artifact_lineage_state == "MIXED":
        return "MIXED"
    if artifact_lineage_state in ("STALE", "MISSING"):
        return artifact_lineage_state
    freshness = _compute_timestamp_freshness(str(payload_timestamp_value))
    if freshness == "PARSE_ERROR":
        return "INVALID"
    if freshness == "STALE":
        return "STALE"
    if freshness == "FRESH" and artifact_lineage_state == "COHERENT":
        return "OK"
    return "UNKNOWN"


def _macro_tape_source_health(
    *,
    macro_drivers: dict,
    tape_value_slots: list[tuple[str, str]],
) -> str:
    """PRD-120 SOURCE-HEALTH MAPPING for Macro Tape. First match wins."""
    if (not macro_drivers) or all(
        str(v) == "MARKET MAP UNAVAILABLE" for v in macro_drivers.values()
    ):
        return "MISSING"
    for _label, value in tape_value_slots:
        if value in ("--", "N/A"):
            return "FALLBACK"
    return "OK"


def _trend_structure_source_health(
    *,
    artifact_lineage_state: str,
    inactive_session: bool,
    snapshot: dict | None,
    ts_generated_at_raw: object,
    usable_count: int,
) -> str:
    """PRD-120 / PRD-123 SOURCE-HEALTH MAPPING for Trend Structure.

    Precedence (first match wins):
      1. lineage MIXED            → MIXED
      2. lineage STALE            → STALE
      3. lineage MISSING          → MISSING
      4. snapshot not a dict      → MISSING
      5. freshness PARSE_ERROR    → INVALID
      6. freshness STALE          → STALE
      7. usable_count == 0        → MARKET_CLOSED if inactive_session else AWAITING_DATA  (PRD-123)
      8. inactive_session         → INACTIVE_SESSION  (rare: inactive with usable rows)
      9. otherwise                → OK

    PRD-123 R5: the `usable_count == 0` branch must precede the
    `inactive_session` branch so MARKET_CLOSED is reachable. The previous
    PRD-120 `FALLBACK` return is removed from this function entirely.
    """
    if artifact_lineage_state == "MIXED":
        return "MIXED"
    if artifact_lineage_state in ("STALE", "MISSING"):
        return artifact_lineage_state
    if not isinstance(snapshot, dict):
        # PRD-123: no snapshot file at all. Preserve PRD-117 coherence:
        # under inactive_session, return INACTIVE_SESSION so the panel
        # body's "SESSION INACTIVE" label is not contradicted by
        # "SOURCE: MISSING". Under active session, report MISSING
        # truthfully so the operator sees the writer regression.
        return "INACTIVE_SESSION" if inactive_session else "MISSING"
    if isinstance(ts_generated_at_raw, str) and ts_generated_at_raw:
        freshness = _compute_timestamp_freshness(ts_generated_at_raw)
        if freshness == "PARSE_ERROR":
            return "INVALID"
        if freshness == "STALE":
            return "STALE"
    if usable_count == 0:
        # PRD-123: snapshot exists and is fresh but no symbol carries
        # usable data — typically markets closed or intraday not yet
        # streaming. This branch must precede the bare INACTIVE_SESSION
        # below so MARKET_CLOSED is reachable.
        return "MARKET_CLOSED" if inactive_session else "AWAITING_DATA"
    if inactive_session:
        return "INACTIVE_SESSION"  # rare: inactive with usable rows
    return "OK"


def _market_map_source_health(
    *,
    artifact_lineage_state: str,
    inactive_session: bool,
    mm_status: str,
) -> str:
    """PRD-120 SOURCE-HEALTH MAPPING for Market Map. First match wins."""
    if artifact_lineage_state == "MIXED":
        return "MIXED"
    if artifact_lineage_state == "STALE":
        return "STALE"
    if artifact_lineage_state == "MISSING":
        return "MISSING"
    if inactive_session:
        return "INACTIVE_SESSION"
    if mm_status == "SOURCE_MISSING":
        return "MISSING"
    if mm_status == "PARSE_ERROR":
        return "INVALID"
    if mm_status == "STALE":
        return "STALE"
    return "OK"


_MARKET_MAP_RENDERED_GRADES: frozenset[str] = frozenset({"A+", "A", "B", "C", "D", "F"})


def _market_map_rendered_setup_count(market_map: dict | None) -> int:
    """PRD-120 R7: count of candidate cards the renderer will emit under OK lineage."""
    if not isinstance(market_map, dict):
        return 0
    symbols = market_map.get("symbols")
    if not isinstance(symbols, dict):
        return 0
    return sum(
        1 for entry in symbols.values()
        if isinstance(entry, dict)
        and (entry.get("grade") or "") in _MARKET_MAP_RENDERED_GRADES
    )


def _trend_structure_records(snapshot: dict | None) -> dict[str, dict] | None:
    """Validate per-record shape for the curated 6 symbols. Returns the
    per-symbol record dict on success, or None when any required field is
    missing or wrong-typed for any curated symbol (R5 all-or-nothing)."""
    if snapshot is None:
        return None
    symbols = snapshot.get("symbols")
    if not isinstance(symbols, dict):
        return None
    out: dict[str, dict] = {}
    for sym in config.TREND_STRUCTURE_SYMBOLS:
        rec = symbols.get(sym)
        if not isinstance(rec, dict):
            return None
        for field in _TREND_STRUCTURE_REQUIRED_FIELDS:
            if field not in rec:
                return None
        out[sym] = rec
    return out


def _format_trend_number(value: object) -> str:
    """Display formatting only — no comparisons, no derived labels."""
    if value is None or isinstance(value, bool):
        return _DASH
    try:
        f = float(value)
    except (TypeError, ValueError):
        return _DASH
    if math.isnan(f) or math.isinf(f):
        return _DASH
    return f"{f:.2f}"


def _load_macro_snapshot(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        drivers = data.get("macro_drivers")
        return drivers if isinstance(drivers, dict) else {}
    except Exception:
        return {}


def _esc(value: object) -> str:
    if value is None:
        return ""
    return _html.escape(str(value))


def _bool_str(value: object) -> str:
    if value is True:
        return "YES"
    if value is False:
        return "NO"
    return ""


def _pct_arrow(change_pct: float) -> str:
    if change_pct > 0:
        return _UP
    if change_pct < 0:
        return _DOWN
    return _FLAT


def _fmt_pct_signed(fraction: object) -> str:
    """Format a fractional change (0.02 -> '+2.00%') with explicit sign for the
    scoreboard. Returns 'n/a' for non-finite / non-numeric input."""
    if not _is_finite_number(fraction):
        return "n/a"
    return f"{float(fraction) * 100:+.2f}%"


def _direction_arrow(direction: str) -> str:
    if direction == "LONG":
        return _UP
    if direction == "SHORT":
        return _DOWN
    return _FLAT


def _is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _build_tape_slots(
    macro_drivers: dict,
    trend_records: dict[str, dict] | None,
) -> list[tuple[str, str]]:
    slots: list[tuple[str, str]] = []

    for row in (MACRO_ROW_1, MACRO_ROW_2):
        for slot in row.slots:
            block = macro_drivers.get(slot.payload_key) if macro_drivers else None
            change_pct = block.get("change_pct") if isinstance(block, dict) else None
            if _is_finite_number(change_pct):
                slots.append((slot.label, _pct_arrow(float(change_pct))))
            else:
                slots.append((slot.label, _DASH))

    # PRD-199: the tradables arrow is the SIGN of the symbol's daily %-change
    # (trend-structure record daily_change_pct), via the same _pct_arrow path as
    # the macro-driver rows. Replaces the dead trade_framing.direction branch,
    # whose arrow was computed but never rendered.
    records = trend_records or {}
    for slot in TRADABLES_ROW.slots:
        rec = records.get(slot.quote_symbol)
        change_pct = rec.get("daily_change_pct") if isinstance(rec, dict) else None
        if _is_finite_number(change_pct):
            slots.append((slot.label, _pct_arrow(float(change_pct))))
        else:
            slots.append((slot.label, _DASH))

    return slots


def _format_tape_value(symbol: str, value: object) -> str:
    if not _is_finite_number(value):
        return "--"

    numeric = float(value)
    if symbol == "VIX":
        return f"{numeric:.1f}"
    if symbol == "DXY":
        return f"{numeric:.1f}"
    if symbol == "10Y":
        return f"{numeric:.2f}"
    if symbol == "BTC":
        if abs(numeric) >= 10000:
            return f"{numeric / 1000:.1f}K"
        return f"{numeric:.0f}"
    if symbol == "OIL":
        return f"{numeric:.1f}"
    if symbol == "XAU":
        return f"{numeric:.1f}"
    if symbol == "XAG":
        return f"{numeric:.2f}"
    return f"{numeric:.2f}"


def _build_tape_value_slots(
    macro_drivers: dict,
    market_map: dict | None,
) -> list[tuple[str, str]]:
    slots: list[tuple[str, str]] = []

    for row in (MACRO_ROW_1, MACRO_ROW_2):
        for slot in row.slots:
            block = macro_drivers.get(slot.payload_key) if macro_drivers else None
            value = block.get("level") if isinstance(block, dict) else None
            fallback = "N/A" if row is MACRO_ROW_1 and slot.label != "BTC" else "--"
            if _is_finite_number(value):
                slots.append((slot.label, _format_tape_value(slot.label, value)))
            else:
                slots.append((slot.label, fallback))

    symbols: dict = (market_map or {}).get("symbols") or {}
    for slot in TRADABLES_ROW.slots:
        entry = symbols.get(slot.quote_symbol)
        value = entry.get("current_price") if isinstance(entry, dict) else None
        if _is_finite_number(value):
            slots.append((slot.label, _format_tape_value(slot.label, value)))
        else:
            slots.append((slot.label, "N/A"))

    return slots


_PRESSURE_COMPONENT_LABELS = [
    ("volatility_pressure", "Volatility"),
    ("dollar_pressure",     "Dollar"),
    ("bitcoin_pressure",    "Bitcoin"),
]


# PRD-158 § 4.2 translation tables. Each maps an existing payload value
# to decision-language output. Returning None means cut from render.

def _regime_to_permission_verb(regime: object) -> str:
    """Translation 1: regime → trader-facing permission."""
    if regime == "RISK_ON":
        return "Longs allowed"
    if regime == "RISK_OFF":
        return "Shorts allowed"
    if regime == "EXPANSION":
        # PRD-163: EXPANSION is a long-momentum regime (posture EXPANSION_LONG,
        # Permission "momentum allowed. Continuation entries."). Without this
        # branch it fell through to "Stand down", contradicting the Permission
        # field. Distinct from RISK_ON's "Longs allowed" to preserve that
        # EXPANSION is a breadth/leadership-confirmed advance.
        return "Momentum longs allowed"
    return "Stand down"


# PRD-219: system-state distillation — regime → verdict colour + plain-English name.
_SYS_VERDICT_CLS: dict[str, str] = {
    "RISK_ON": "sys-up", "EXPANSION": "sys-up",
    "RISK_OFF": "sys-down", "NEUTRAL": "sys-flat",
}
_SYS_REGIME_PLAIN: dict[str, str] = {
    "RISK_ON": "Risk-on", "RISK_OFF": "Risk-off",
    "NEUTRAL": "Neutral", "EXPANSION": "Expansion",
}

# PRD-220: abbreviate the trend-structure alignment token so a symbol's row fits
# on one compact mobile line (BULLISH→BULL etc.). Display-only; the raw
# trend_alignment still drives the price colour class.
_TS_ALIGN_ABBR: dict[str, str] = {"BULLISH": "BULL", "BEARISH": "BEAR", "MIXED": "MIX"}


_PRESSURE_DECISION_PHRASES: dict[str, dict[str, str]] = {
    "volatility_pressure": {
        "RISK_ON":  "VIX permits longs",
        "RISK_OFF": "VIX blocks longs",
    },
    "dollar_pressure": {
        "RISK_OFF": "DXY pressures longs",
        "RISK_ON":  "DXY supports risk-on",
    },
    "bitcoin_pressure": {
        "RISK_ON":  "BTC supports risk-on",
        "RISK_OFF": "BTC pressures risk-on",
    },
}


def _pressure_decision_phrase(component_key: str, pressure_value: object) -> str | None:
    """Translations 4-6: per-component pressure → decision phrase, or None to cut."""
    table = _PRESSURE_DECISION_PHRASES.get(component_key)
    if table is None:
        return None
    return table.get(str(pressure_value))


def _grade_to_action(grade: object) -> str | None:
    """Translation 11: card grade → action verb, or None to cut."""
    if grade in ("A+", "A"):
        return "Tradeable"
    if grade == "B":
        return "Developing"
    return None


def _regime_flip_phrase(previous_regime: object, current_regime: object) -> str | None:
    """Translation 13: regime transition → 'Permission flipped to …' or None."""
    if previous_regime == current_regime:
        return None
    if current_regime == "RISK_ON":
        return "Permission flipped to longs"
    if current_regime == "RISK_OFF":
        return "Permission flipped to shorts"
    return None


# PRD-158 § 4.3: build the dashboard_integrator input from existing
# render-time state. No new computation — only field selection.

def _regime_to_permission_key(regime: object) -> str:
    if regime == "RISK_ON":
        return "longs"
    if regime == "RISK_OFF":
        return "shorts"
    return "stand_down"


def _macro_bias_direction_key(long_votes: int, short_votes: int) -> str:
    """Map the macro_bias vote tally to the integrator's direction key.

    PRD-160 unwound the PRD-158 § 4.2 workaround. The renderer's macro_bias
    tally now applies per-driver cyclicality (contra-cyclical VIX/DXY/10Y
    invert; pro-cyclical BTC keeps sign), so the votes passed here already
    carry the same semantics as the visible "MACRO BIAS: …" label and the
    Macro Pressure sub-signals. The integrator therefore receives a single,
    correct source of truth: Rule 3 fires only on genuine regime/macro/setup
    divergence, no longer on the old arrow-count vs. semantic-pressure
    mismatch that PRD-158 deliberately mirrored to keep the two surfaces in
    sync."""
    if long_votes > short_votes:
        return "long"
    if short_votes > long_votes:
        return "short"
    return "mixed"


_BIAS_TO_SETUP_DIRECTION: dict[str, str] = {
    "BULL": "long", "BULLISH": "long", "LONG": "long",
    "BEAR": "short", "BEARISH": "short", "SHORT": "short",
}


def _setup_direction_from_entry(entry: dict) -> str | None:
    """Derive long/short from an existing market_map symbol entry."""
    tf = entry.get("trade_framing") or {}
    direction = tf.get("direction") or entry.get("bias")
    if isinstance(direction, str):
        return _BIAS_TO_SETUP_DIRECTION.get(direction.upper())
    return None


def _build_integrator_input(
    market_regime: object,
    long_votes: int,
    short_votes: int,
    market_map: dict | None,
) -> dict:
    """Construct dashboard_integrator input from existing render-time values.

    Only high-grade symbols (A+/A/B) are fed to the integrator — these are
    the symbols the dashboard claims as tradable setups. Lower grades
    (C/D/F) are observational and already carry FAILURE REASON in the
    rendered card; Rule 1's required-data check is not meant for them.
    """
    symbols_payload: dict[str, dict] = {}
    mm_symbols = (market_map or {}).get("symbols") or {}
    for sym, entry in mm_symbols.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("grade") not in _HIGH_GRADES:
            continue
        invalidation = entry.get("invalidation")
        invalidation_value = (
            invalidation[0] if isinstance(invalidation, list) and invalidation else None
        )
        tf = entry.get("trade_framing") or {}
        trigger_value = tf.get("entry") or tf.get("if_now")
        symbols_payload[sym] = {
            "current_price": entry.get("current_price"),
            "setup_direction": _setup_direction_from_entry(entry),
            "setup_type": entry.get("setup_state") or entry.get("structure"),
            "trigger": trigger_value,
            "invalidation": invalidation_value,
            "grade": entry.get("grade"),
        }

    tiers: list[tuple[str, str, list[str]]] = []
    for tier_id, tier_label, tier_grades in _TIER_DEFS:
        if tier_grades.isdisjoint(_HIGH_GRADES):
            continue
        tier_syms = [
            sym for sym in symbols_payload
            if mm_symbols[sym].get("grade") in tier_grades
        ]
        if tier_syms:
            tiers.append((tier_id, tier_label, tier_syms))

    return {
        "regime_permission": _regime_to_permission_key(market_regime),
        "macro_bias_direction": _macro_bias_direction_key(long_votes, short_votes),
        "symbols": symbols_payload,
        "tiers": tiers,
    }

_POSTURE_LABELS: dict[str, str] = {
    "AGGRESSIVE_LONG": "Aggressive Long",
    "CONTROLLED_LONG": "Controlled Long",
    "EXPANSION_LONG":  "Expansion Long",
    "NEUTRAL_PREMIUM": "Neutral Premium",
    "DEFENSIVE_SHORT": "Defensive Short",
    "STAY_FLAT":       "Stay Flat",
    "CHAOTIC":         "Chaotic",
}


def _decision_title(outcome: object, system_halted: bool, status: object) -> str:
    if str(status) in {"FAIL", "ERROR"} or system_halted:
        return "SYSTEM HALT"
    if outcome == "TRADE":
        return "TRADE SETUP ACTIVE"
    if outcome == "NO_TRADE":
        return "NO TRADE"
    return "MONITOR"


def _build_pressure_snapshot(macro_drivers: dict, market_map: dict | None) -> dict | None:
    if (not macro_drivers) or all(str(v) == "MARKET MAP UNAVAILABLE" for v in macro_drivers.values()):
        return None
    try:
        return build_macro_pressure(macro_drivers, market_map)
    except Exception:
        return None


def _pct_label(change_pct: float | None, high_label: str, low_label: str) -> str:
    if change_pct is None:
        return "unavailable"
    if change_pct > 0.3:
        return high_label
    if change_pct < -0.3:
        return low_label
    return "flat"


def _metal_label(sym: str, entry: dict | None) -> str:
    if entry is None:
        return f"{sym}: unavailable"
    grade = entry.get("grade") or ""
    change_pct = entry.get("change_pct")
    direction = "up" if (change_pct or 0) > 0 else "down" if (change_pct or 0) < 0 else "flat"
    return f"{sym}: {grade} ({direction})" if grade else f"{sym}: {direction}"


def _build_sunday_context(
    macro_drivers: dict,
    market_regime: str | None,
    market_map: dict | None,
) -> dict:
    drivers = macro_drivers or {}
    dollar_pct = (drivers.get("dollar") or {}).get("change_pct")
    rates_pct = (drivers.get("rates") or {}).get("change_pct")
    vix_level = (drivers.get("volatility") or {}).get("level")
    vix_pct = (drivers.get("volatility") or {}).get("change_pct")
    btc_pct = (drivers.get("bitcoin") or {}).get("change_pct")

    dollar_context = _pct_label(dollar_pct, "dollar strengthening", "dollar weakening")
    rates_context = _pct_label(rates_pct, "rates rising", "rates falling")

    if vix_level is None:
        volatility_context = "volatility unavailable"
    elif vix_level > 25:
        volatility_context = f"elevated volatility (VIX {vix_level:.1f})"
    elif vix_level < 18:
        volatility_context = f"low volatility (VIX {vix_level:.1f})"
    else:
        volatility_context = f"moderate volatility (VIX {vix_level:.1f})"
    if vix_pct is not None and vix_pct > 15:
        volatility_context += " — chaotic spike"

    symbols: dict = (market_map or {}).get("symbols") or {}
    metals_parts = [_metal_label(sym, symbols.get(sym)) for sym in ("GLD", "SLV", "GDX")]
    metals_context = " | ".join(metals_parts)

    risk_context = _pct_label(btc_pct, "risk appetite present", "risk-off signal")

    posture = market_regime or "UNKNOWN"
    if posture in ("RISK_ON", "AGGRESSIVE_LONG", "CONTROLLED_LONG"):
        monday_watch = "Watch for confirmation of risk-on bias before Monday open"
    elif posture in ("RISK_OFF", "DEFENSIVE_SHORT"):
        monday_watch = "Monitor risk pressure — watch for rejection at resistance"
    elif posture == "CHAOTIC":
        monday_watch = "No trade decision before cash session — chaotic conditions"
    else:
        monday_watch = "Watch for confirmation before Monday cash session"

    return {
        "session_type": "SUNDAY_PREMARKET",
        "headline": "Sunday Macro Context — No Cash Session",
        "macro_posture": posture,
        "dollar_context": dollar_context,
        "rates_context": rates_context,
        "volatility_context": volatility_context,
        "metals_context": metals_context,
        "risk_context": risk_context,
        "monday_watch": monday_watch,
    }


def _resolve_previous_run(logs_dir: Path) -> dict | None:
    run_files = sorted(logs_dir.glob("run_*.json"))
    if len(run_files) < 2:
        return None
    runs = [_load_json(path) for path in run_files]
    runs.sort(key=lambda run: str(_req(run, "timestamp")), reverse=True)
    return runs[1]


def _render_level_diagram(
    w: object,
    now_price: float | None,
    contract_entry: float | None,
    fib_levels: dict | None,
    watch_zones: list | None,
    contract_stop: float | None = None,
) -> None:
    """Render a deterministic SVG level diagram for a candidate card (PRD-074).

    PRD-216: each level label carries its dollar value. PRD-221/PRD-222: the
    anchor is labelled NOW and every other level carries its signed % distance
    from that anchor. PRD-223: a numeric stop shades the entry→stop span as a
    soft risk zone with a dashed STOP edge — zone shading, not a crisp hairline,
    because the invalidation the engine describes is a zone, not a tick.

    PRD-226: NOW is the *live current price* (``now_price``) — the 0% reference
    and the yellow focal line. The contract's planned entry (``contract_entry``,
    from ``trade_candidates[].entry``) is a SEPARATE level: it is the risk-band
    top edge and, when it differs from NOW beyond display resolution, its own
    amber ENTRY marker. It is never relabelled NOW. The current price is the
    required anchor: absent it, the diagram is suppressed (the caller gates on a
    valid current price) — the entry is never promoted to a NOW label.
    """
    # PRD-226: everything scales around and reports % distance from the 0%
    # reference — the live current price. The caller only reaches here with a
    # valid current price; the guard is belt-and-suspenders. A non-finite anchor
    # (inf/NaN) must fail here too: the y-scale math would otherwise produce NaN
    # and round() would raise, aborting the whole render.
    if now_price is None or not math.isfinite(now_price) or now_price <= 0:
        w('  <div class="lvl-unavail">Chart unavailable — no price data</div>')
        return
    anchor_base = now_price

    # PRD-223: the risk zone draws only from an honest numeric pair — a
    # finite positive stop distinct from the anchor. Anything else renders
    # exactly the pre-PRD-223 diagram.
    # PRD-226: the band draws entry→stop, so a stop needs a valid contract entry
    # to pair against — never against the NOW/current-price anchor.
    stop_price: float | None = None
    if (
        contract_entry is not None
        and contract_entry > 0
        and contract_stop is not None
        and not isinstance(contract_stop, bool)
    ):
        try:
            stop_candidate = float(contract_stop)
        except (TypeError, ValueError):
            stop_candidate = None
        if (
            stop_candidate is not None
            and math.isfinite(stop_candidate)
            and stop_candidate > 0
            and stop_candidate != contract_entry
        ):
            stop_price = stop_candidate

    vwap_level: float | None = None
    zone_lines: list[tuple[float, str]] = []
    for zone in (watch_zones or []):
        lv = zone.get("level")
        zt = zone.get("type", "")
        if lv is None:
            continue
        try:
            lv_f = float(lv)
        except (TypeError, ValueError):
            continue
        if zt == "VWAP":
            if lv_f > 0:
                vwap_level = lv_f
        else:
            zone_lines.append((lv_f, zt))

    fib_items: list[tuple[float, str]] = []
    if fib_levels and isinstance(fib_levels, dict):
        retracements = fib_levels.get("retracements") or {}
        for label, val in retracements.items():
            if val is None:
                continue
            try:
                fib_items.append((float(val), str(label)))
            except (TypeError, ValueError):
                pass

    all_prices = [anchor_base]
    if contract_entry is not None and contract_entry != anchor_base:
        all_prices.append(contract_entry)
    if stop_price is not None:
        all_prices.append(stop_price)
    if vwap_level is not None:
        all_prices.append(vwap_level)
    for lv_f, _ in zone_lines:
        all_prices.append(lv_f)
    for lv_f, _ in fib_items:
        all_prices.append(lv_f)

    p_min = min(all_prices)
    p_max = max(all_prices)
    p_span = p_max - p_min

    if p_span < 0.01:
        p_min = anchor_base * 0.995
        p_max = anchor_base * 1.005
        p_span = p_max - p_min
    else:
        pad = p_span * 0.12
        p_min -= pad
        p_max += pad
        p_span = p_max - p_min

    SVG_H = 110
    LINE_W = 160
    LABEL_X = LINE_W + 4
    SVG_W = 280

    def _to_y(price: float) -> int:
        return round(SVG_H * (1.0 - (price - p_min) / p_span))

    def _pct(level: float) -> str:
        # PRD-226: signed % distance from the 0% reference — the live current
        # price (`anchor_base` is `now_price`, guaranteed valid past the guard).
        return f" {((level - anchor_base) / anchor_base * 100.0):+.1f}%"

    w('  <div class="lvl-diagram">')
    w(
        f'    <svg width="{SVG_W}" height="{SVG_H}" '
        f'xmlns="http://www.w3.org/2000/svg" style="display:block;overflow:visible">'
    )
    w(f'    <rect width="{LINE_W}" height="{SVG_H}" fill="#0a0a0a"/>')

    # PRD-223/PRD-226: risk zone — the contract entry→stop span (its top edge is
    # the entry, not the NOW anchor), shaded behind every level line so the
    # levels stay legible on top of it.
    if stop_price is not None:
        band_top = min(_to_y(contract_entry), _to_y(stop_price))
        band_h = abs(_to_y(contract_entry) - _to_y(stop_price))
        w(
            f'    <rect x="0" y="{band_top}" width="{LINE_W}" height="{band_h}" '
            f'fill="#e05252" opacity="0.08"/>'
        )

    # Draw every level LINE at its true price-mapped y, and collect the label
    # for a second pass. Lines are never moved (the ENTRY line y is a pinned
    # contract for downstream tests); only the text labels are decluttered so
    # that clustered levels — which is exactly when they matter — stay legible
    # instead of overprinting into an unreadable stack.
    labels: list[tuple[int, str, str]] = []  # (true_y, text, fill)

    for lv_f, label in sorted(fib_items, key=lambda x: x[0], reverse=True):
        y = _to_y(lv_f)
        w(
            f'    <line x1="0" y1="{y}" x2="{LINE_W}" y2="{y}" '
            f'stroke="#3a3a3a" stroke-width="1" stroke-dasharray="3,3"/>'
        )
        # PRD-216: annotate with the dollar level (facts, not forecasts).
        # PRD-221: + signed % distance from price NOW.
        labels.append((y, f"{_esc(label[:5])} {lv_f:,.2f}{_pct(lv_f)}", "#555"))

    for lv_f, zt in sorted(zone_lines, key=lambda x: x[0], reverse=True):
        y = _to_y(lv_f)
        w(
            f'    <line x1="0" y1="{y}" x2="{LINE_W}" y2="{y}" '
            f'stroke="#1a4a5a" stroke-width="1"/>'
        )
        labels.append((y, f"{_esc(zt[:10])} {lv_f:,.2f}{_pct(lv_f)}", "#3a7a8a"))

    if vwap_level is not None:
        y = _to_y(vwap_level)
        w(
            f'    <line x1="0" y1="{y}" x2="{LINE_W}" y2="{y}" '
            f'stroke="#29b6f6" stroke-width="1.5" stroke-dasharray="4,2"/>'
        )
        labels.append((y, f"VWAP {vwap_level:,.2f}{_pct(vwap_level)}", "#29b6f6"))

    # PRD-223: dashed STOP edge on the risk zone's far side. Dashed, not
    # solid — the stop is where the thesis is wrong, rendered as a zone edge
    # per the DECISIONS 2026-07-02 second-order caution.
    if stop_price is not None:
        y = _to_y(stop_price)
        w(
            f'    <line x1="0" y1="{y}" x2="{LINE_W}" y2="{y}" '
            f'stroke="#e05252" stroke-width="1.5" stroke-dasharray="5,3"/>'
        )
        labels.append((y, f"STOP {stop_price:,.2f}{_pct(stop_price)}", "#e05252"))

    # PRD-226: NOW is the live current price — the 0% reference — drawn as the
    # yellow focal line (no % suffix). The contract entry is never relabelled NOW.
    y = _to_y(now_price)
    w(
        f'    <line x1="0" y1="{y}" x2="{LINE_W}" y2="{y}" '
        f'stroke="#f5c518" stroke-width="2"/>'
    )
    w(f'    <circle cx="3" cy="{y}" r="3" fill="#f5c518"/>')
    labels.append((y, f"NOW {now_price:,.2f}", "#f5c518"))

    # PRD-226: the contract's planned entry is a SEPARATE amber level carrying
    # its signed % distance from NOW — the risk-band top edge made explicit. It
    # is drawn when it differs from NOW beyond display resolution (< 0.005 rounds
    # to the same 2dp price, so the two lines would overprint an identical
    # label); when it equals NOW they coincide and only NOW shows.
    if (
        contract_entry is not None
        and contract_entry > 0
        and abs(contract_entry - now_price) >= 0.005
    ):
        y = _to_y(contract_entry)
        w(
            f'    <line x1="0" y1="{y}" x2="{LINE_W}" y2="{y}" '
            f'stroke="#e0a552" stroke-width="1.5"/>'
        )
        labels.append((y, f"ENTRY {contract_entry:,.2f}{_pct(contract_entry)}", "#e0a552"))

    # Label-declutter pass. Spread baselines so no two labels sit closer than
    # LABEL_MIN_GAP px; a thin leader connects any label pushed off its line.
    # Deterministic: stable sort by (true_y, insertion index).
    LABEL_MIN_GAP = 11
    BASE_OFF = 4          # baseline offset that centers text on its line
    TOP_CLAMP = 9         # keep the topmost label inside the canvas
    order = sorted(range(len(labels)), key=lambda i: (labels[i][0], i))
    # When more labels are present than fit at LABEL_MIN_GAP within the canvas
    # (SVG_H - TOP_CLAMP), shrink the gap so they still fit instead of spilling
    # off the top/bottom edge. n-1 gaps must span at most (SVG_H - TOP_CLAMP).
    n = len(order)
    gap = LABEL_MIN_GAP
    if n > 1:
        gap = min(float(LABEL_MIN_GAP), (SVG_H - TOP_CLAMP) / (n - 1))
    pos: dict[int, float] = {}
    prev: float | None = None
    for idx in order:
        base = labels[idx][0] + BASE_OFF
        p = max(base, TOP_CLAMP) if prev is None else max(base, prev + gap)
        pos[idx] = p
        prev = p
    # If the stack overran the bottom edge, compress upward from the last label.
    # With the fitted gap above, this can never push the top label past TOP_CLAMP
    # (SVG_H - (n-1)*gap >= TOP_CLAMP), so every label stays on-canvas.
    if order and pos[order[-1]] > SVG_H:
        cap = float(SVG_H)
        for idx in reversed(order):
            pos[idx] = min(pos[idx], cap)
            cap = pos[idx] - gap

    for idx, (true_y, text, fill) in enumerate(labels):
        by = round(pos[idx])
        if abs(by - (true_y + BASE_OFF)) > 3:
            w(
                f'    <line x1="{LINE_W}" y1="{true_y}" '
                f'x2="{LABEL_X - 1}" y2="{by - 3}" '
                f'stroke="#444" stroke-width="0.75"/>'
            )
        w(
            f'    <text x="{LABEL_X}" y="{by}" font-size="9" '
            f'fill="{fill}" font-family="monospace">{text}</text>'
        )

    w('    </svg>')
    w('  </div>')


def _render_candidate_card(
    w: object, sym: str, entry: dict, contract_entry: float | None = None,
    contract_stop: float | None = None,
) -> None:
    grade = entry.get("grade") or ""
    css_class = _GRADE_CSS.get(grade, "unknown")
    is_high = grade in _HIGH_GRADES

    lifecycle: dict | None = entry.get("lifecycle")
    lc_tr = lifecycle.get("grade_transition") if lifecycle else None
    badge_css = _LIFECYCLE_BADGE_CSS.get(lc_tr) if lc_tr else None
    badge_html = f'<span class="lifecycle-badge {badge_css}">{_esc(lc_tr)}</span>' if badge_css else ""

    w(f'<div class="candidate-card grade-{css_class}" id="card-{_esc(sym)}">')

    grade_action = _grade_to_action(grade)
    if not is_high:
        # PRD-158 § 4.2 translation 11: low-grade GRADE label suppressed —
        # FAILURE REASON below carries the trader action.
        w('  <div class="failed-card-fields">')
        w(f'    <div><div class="label">SYMBOL</div><div class="value">{_esc(entry.get("symbol"))}{badge_html}</div></div>')
        w(f'    <div><div class="label">BIAS</div><div class="value">{_esc(entry.get("bias"))}</div></div>')
        w(f'    <div><div class="label">STRUCTURE</div><div class="value">{_esc(entry.get("structure"))}</div></div>')
        w('  </div>')
        _fail = (
            entry.get("failure_reason")
            or entry.get("block_reason")
            or entry.get("reason_for_grade")
        )
        _fail_text = _esc(_fail) if _fail else "No failure reason provided"
        w(f'  <div class="label">FAILURE REASON</div><div class="value">{_fail_text}</div>')
    else:
        w(f'  <div class="label">SYMBOL</div><div class="value">{_esc(entry.get("symbol"))}</div>')
        if grade_action is not None:
            w(f'  <div class="label">GRADE</div>'
              f'<div class="value">{_esc(grade_action)}{badge_html}</div>')
        w(f'  <div class="label">BIAS</div><div class="value">{_esc(entry.get("bias"))}</div>')
        w(f'  <div class="label">STRUCTURE</div><div class="value">{_esc(entry.get("structure"))}</div>')

    if is_high:
        if lifecycle:
            pg = _esc(lifecycle.get("previous_grade")) or _DASH
            cg = _esc(lifecycle.get("current_grade")) or _DASH
            ps = _esc(lifecycle.get("previous_setup_state")) or _DASH
            cs = _esc(lifecycle.get("current_setup_state")) or _DASH
            w(f'  <div class="lifecycle-detail">LIFECYCLE: {pg} → {cg} | {ps} → {cs}</div>')

        setup_state = entry.get("setup_state")
        if setup_state and setup_state != "DATA_UNAVAILABLE":
            w(f'  <div class="candidate-state">STATE: {_esc(setup_state)}</div>')

        tf: dict = entry.get("trade_framing") or {}

        if_now = tf.get("if_now")
        if if_now is not None:
            w(f'  <div class="label">IF NOW</div><div class="value">{_esc(if_now)}</div>')

        # PRD-165 R1 / PRD-215: ENTRY/INVALIDATION are the falsifiable, actionable
        # fields; render them bold (.value-key) AND in the cyan "actionable" accent
        # (.value-actionable) so they are the visual focus of the card.
        entry_val = tf.get("entry")
        if entry_val is not None:
            w(f'  <div class="label">ENTRY</div><div class="value-key value-actionable">{_esc(entry_val)}</div>')

        invalidation = entry.get("invalidation")
        if invalidation and len(invalidation) > 0 and invalidation[0] is not None:
            w(f'  <div class="label">INVALIDATION</div><div class="value-key value-actionable">{_esc(invalidation[0])}</div>')

        downgrade = tf.get("downgrade")
        if downgrade is not None:
            w(f'  <div class="candidate-risk">RISK: {_esc(downgrade)}</div>')

        # PRD-215: REASON/PLAY/WATCH are supporting context — tuck them behind a
        # default-collapsed disclosure so the accented ENTRY/INVALIDATION stay the
        # focal point. Rendered only when at least one of the three has content.
        reason = entry.get("reason_for_grade")
        pts = entry.get("preferred_trade_structure")
        _watch_items = [
            item for item in (entry.get("what_to_look_for") or [])
            if item and item != _UNAVAILABLE_WATCH
        ]
        if reason is not None or pts is not None or _watch_items:
            w('  <details class="card-detail"><summary>DETAIL ▶</summary>')
            if reason is not None:
                w(f'  <div class="label">REASON</div><div class="value">{_esc(reason)}</div>')
            if pts is not None:
                w(f'  <div class="label">PLAY</div><div class="value">{_esc(pts)}</div>')
            for item in _watch_items:
                w(f'  <div class="label">WATCH</div><div class="value">{_esc(item)}</div>')
            w('  </details>')

    # PRD-158 § 4.2 translation 12: render the level diagram only when both
    # an anchor and level context exist. No placeholder for partial data.
    # PRD-226: the NOW anchor / 0% reference is the live current price; the
    # contract's planned entry is passed separately (risk-band edge + ENTRY
    # marker), never as the NOW anchor. The diagram renders only against a valid
    # current price — an absent/invalid one suppresses it (the entry is never an
    # anchor).
    now_price = entry.get("current_price")
    fib_levels = entry.get("fib_levels")
    watch_zones = entry.get("watch_zones")
    has_level_context = bool(fib_levels) or bool(watch_zones)

    def _valid_price(v: object) -> bool:
        # PRD-226: a drawable price must be a finite positive number. inf/NaN are
        # floats > 0 (inf) or pass isinstance (NaN) but crash the y-scale math —
        # exclude them so a malformed price suppresses the diagram, not the render.
        return (
            isinstance(v, (int, float))
            and not isinstance(v, bool)
            and math.isfinite(v)
            and v > 0
        )

    now_valid = _valid_price(now_price)
    entry_valid = _valid_price(contract_entry)
    # PRD-226: the current price is the required NOW anchor — the diagram renders
    # only against it (every rendered high-grade card carries current_price; the
    # integrator's Rule 1 collapses a card that lacks it). The contract entry is
    # never an anchor.
    if now_valid and has_level_context:
        # PRD-223: the risk band needs the contract pair — a stop only draws
        # against its own entry, never against the NOW/current-price anchor.
        # This gate also carries contract staleness: a stale contract nulls
        # the entry map, so its stop can never pair up and draw.
        band_stop = contract_stop if entry_valid else None
        _render_level_diagram(
            w,
            now_price,
            contract_entry if entry_valid else None,
            fib_levels,
            watch_zones,
            contract_stop=band_stop,
        )

    w("</div>")


def render_dashboard_html(
    payload: dict,
    run: dict,
    *,
    previous_run: dict | None = None,
    history_runs: list[dict] | None = None,
    market_map: dict | None = None,
    market_map_path: Path | None = None,
    macro_snapshot_path: Path | None = None,
    contract_entry_map: dict | None = None,
    contract_stop_map: dict | None = None,
    alert_candidates: list[dict] | None = None,
    contract_generated_at: object | None = None,
    payload_source: str | Path = _PAYLOAD_PATH,
    run_source: str | Path = _RUN_PATH,
    market_map_source: str | Path | None = None,
    contract_source: str | Path = _HOURLY_CONTRACT_PATH,
    trend_structure_snapshot: dict | None = None,
    regime_history: list[dict] | None = None,
    red_folder: dict | None = None,
    pipeline_run: dict | None = None,
    fixture_mode: bool = False,
) -> str:
    """Return deterministic Signal Forge dashboard HTML.

    No payload or run mutation. No engine calls.
    """
    # Resolve market_map from path if not provided directly; compute status for candidate board.
    if market_map is not None:
        _mm_status = "FRESH"
    elif market_map_path is not None:
        _mm_status, market_map = _resolve_market_map(market_map_path)
    else:
        _mm_status = "SOURCE_MISSING"

    resolved_market_map_source = market_map_source
    if resolved_market_map_source is None:
        if market_map_path is not None:
            resolved_market_map_source = market_map_path
        elif market_map is not None:
            resolved_market_map_source = "provided"
        else:
            resolved_market_map_source = "none"

    timestamp     = _req(payload, "meta", "timestamp")
    status        = _req(run, "status")
    market_regime = _req(payload, "summary", "market_regime")

    payload_timestamp_value, payload_timestamp = _first_timestamp(
        payload,
        (("meta", "timestamp"), ("timestamp",), ("generated_at",)),
    )
    run_timestamp_value, run_timestamp = _first_timestamp(
        run,
        (("run_at_utc",), ("timestamp",), ("generated_at",)),
    )
    market_map_timestamp_value, market_map_timestamp = _first_timestamp(
        market_map,
        (("generated_at",),),
    )
    contract_timestamp = _parse_utc_timestamp(contract_generated_at)
    payload_generation_id = _artifact_generation_id(payload, (("meta", "generation_id"), ("generation_id",)))
    run_generation_id = _artifact_generation_id(run, (("generation_id",), ("meta", "generation_id")))
    market_map_generation_id = _artifact_generation_id(market_map, (("generation_id",),))
    generation_ids_mixed = _generation_ids_mixed(
        payload_generation_id,
        run_generation_id,
        market_map_generation_id,
    )

    artifact_mixed = generation_ids_mixed
    baseline_timestamp: datetime | None = None
    if not artifact_mixed:
        present_timestamps = [ts for ts in (payload_timestamp, run_timestamp) if ts is not None]
        if present_timestamps:
            baseline_timestamp = max(present_timestamps)
    market_map_stale_for_run = (
        not artifact_mixed
        and _timestamp_older_than_baseline(market_map_timestamp, baseline_timestamp)
    )
    contract_stale_for_run = (
        not artifact_mixed
        and _timestamp_older_than_baseline(contract_timestamp, baseline_timestamp)
    )
    artifact_lineage_state = _artifact_lineage_state(
        payload_available=isinstance(payload, dict),
        run_available=isinstance(run, dict),
        market_map_available=isinstance(market_map, dict),
        payload_generation_id=payload_generation_id,
        run_generation_id=run_generation_id,
        market_map_generation_id=market_map_generation_id,
        market_map_stale_for_run=market_map_stale_for_run,
    )
    # PRD-116: unhealthy lineage gates section ordering and disabled-state rendering.
    unhealthy_lineage = artifact_lineage_state in ("MIXED", "STALE", "MISSING")
    disabled_class = " disabled" if unhealthy_lineage else ""
    if contract_stale_for_run:
        contract_entry_map = None

    validation_halt_detail = _req(payload, "sections", "validation_halt_detail")
    stay_flat_reason = (
        validation_halt_detail["reason"]
        if isinstance(validation_halt_detail, dict)
        else None
    )

    macro_drivers: dict = payload.get("macro_drivers") or {}
    if (not macro_drivers) or all(str(v) == "MARKET MAP UNAVAILABLE" for v in macro_drivers.values()):
        _snap = macro_snapshot_path if macro_snapshot_path is not None else _MACRO_SNAPSHOT_PATH
        macro_drivers = _load_macro_snapshot(_snap)

    system_halted = _req(run, "system_halted")
    kill_switch   = _req(run, "kill_switch")
    errors        = _req(run, "errors")
    first_error   = errors[0] if errors else None

    outcome    = run.get("outcome")
    permission = run.get("permission")
    if permission is None:
        permission = payload.get("summary", {}).get("permission")
    title = "MIXED_ARTIFACTS" if artifact_mixed else _decision_title(outcome, bool(system_halted), status)

    # R1 — tape slots
    tape_slots = _build_tape_slots(macro_drivers, _trend_structure_records(trend_structure_snapshot))
    tape_value_slots = _build_tape_value_slots(macro_drivers, market_map)
    pressure = _build_pressure_snapshot(macro_drivers, market_map)

    # R1.1 — macro bias from legacy driver inputs only, with per-driver
    # cyclicality semantics (PRD-160). Contra-cyclical drivers (VIX/DXY/10Y)
    # invert: a falling reading is risk-ON (long), a rising one risk-OFF
    # (short). Pro-cyclical drivers (BTC) keep their sign. OIL and spot metals
    # are visibility-only and do not contribute. The vote counts (not raw
    # arrow counts) are what flow to the integrator, so its directional view
    # matches the visible label — see _macro_bias_direction_key.
    _arrow_by_label = dict(tape_slots)
    long_votes = 0
    short_votes = 0
    for row in (MACRO_ROW_1, MACRO_ROW_2):
        for slot in row.slots:
            if slot.payload_key not in MACRO_BIAS_DRIVERS:
                continue
            arrow = _arrow_by_label.get(slot.label, _DASH)
            if arrow not in (_UP, _DOWN):
                continue  # flat / missing drivers cast no vote
            risk_on = arrow == _UP
            if slot.payload_key in MACRO_BIAS_CONTRA_CYCLICAL:
                risk_on = not risk_on
            if risk_on:
                long_votes += 1
            else:
                short_votes += 1
    if long_votes > short_votes:
        macro_bias = f"MACRO BIAS: LONG {_UP}"
        macro_bias_css = "macro-bias long"
    elif short_votes > long_votes:
        macro_bias = f"MACRO BIAS: SHORT {_DOWN}"
        macro_bias_css = "macro-bias short"
    else:
        macro_bias = "MACRO BIAS: MIXED"
        macro_bias_css = "macro-bias mixed"

    # PRD-158 § 4.3: renderer-bound translation pass. The integrator collapses
    # contradictory raw state into trader-facing verdicts/skips and emits
    # suppression flags for raw Outcome / Permission / Macro Bias labels.
    # Skip the integrator entirely when there is no market_map data — the
    # existing renderer already emits "N/A" / "SOURCE_MISSING" / "STALE" in
    # that case; emitting an availability verdict on top adds no value.
    _mm_symbols_for_integrator = (market_map or {}).get("symbols") or {}
    if _mm_symbols_for_integrator:
        integrator_result = dashboard_integrator(
            _build_integrator_input(market_regime, long_votes, short_votes, market_map)
        )
    else:
        integrator_result = {
            "symbol_skips": {},
            "screen_verdicts": [],
            "rendered_tiers": [],
            "suppress": {"permission": False, "outcome": False, "macro_bias": False},
        }
    integrator_suppress = integrator_result["suppress"]
    integrator_verdicts: list[str] = integrator_result["screen_verdicts"]
    integrator_skips: dict[str, str] = integrator_result["symbol_skips"]

    lines: list[str] = []

    def w(line: str) -> None:
        lines.append(line)

    session_type = (payload.get("meta") or {}).get("session_type")
    # PRD-116: Sunday context must only render under coherent Sunday/pre-market lineage.
    sunday_coherent = (
        artifact_lineage_state == "COHERENT"
        and session_type == "SUNDAY_PREMARKET"
        and _is_sunday_pt(str(timestamp))
    )
    # PRD-117: inactive-session presentation flag. Active only under coherent
    # lineage; unhealthy lineage retains PRD-116 precedence at the section level.
    inactive_session = (
        artifact_lineage_state == "COHERENT"
        and session_type in INACTIVE_SESSION_TYPES
    )

    w("<!doctype html>")
    w('<html lang="en">')
    w("<head>")
    w('  <meta charset="UTF-8">')
    w('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    w(f'  <meta http-equiv="refresh" content="{_DASHBOARD_REFRESH_SECONDS}">')
    w("  <title>Signal Forge</title>")
    w(f"  <style>{_CSS}</style>")
    w("</head>")
    w("<body>")
    w('<div class="wrap">')

    if artifact_mixed:
        w('<div class="block artifact-warning" id="artifact-coherence">')
        w("  <h2>MIXED_ARTIFACTS</h2>")
        w("  <div class=\"value\">Dashboard inputs are from different artifact generations.</div>")
        if generation_ids_mixed:
            w(
                "  <div class=\"value\">"
                f"payload={_esc(payload_generation_id or 'unavailable')} "
                f"run={_esc(run_generation_id or 'unavailable')} "
                f"market_map={_esc(market_map_generation_id or 'unavailable')}"
                "</div>"
            )
        w("</div>")

    if sunday_coherent:
        w('<div class="block" id="premarket-banner" style="border-color:#29b6f6;color:#29b6f6;text-align:center">')
        w('  <h2>SUNDAY PRE-MARKET CONTEXT &#8212; NO CASH SESSION</h2>')
        w("</div>")

    if fixture_mode:
        from cuttingboard.delivery.fixtures import FIXTURE_SYMBOLS
        market_map = dict(market_map) if market_map is not None else {}
        market_map = {**market_map, "symbols": FIXTURE_SYMBOLS}
        _mm_status = "FRESH"

    # --- PRD-120: block source-health derivation ---
    # Pure functions of upstream state (lineage, freshness, mm_status,
    # tape value slots, trend snapshot). Computed once before any block
    # emits SOURCE diagnostics so each block reads byte-stable values.
    _ts_records = _trend_structure_records(trend_structure_snapshot)
    _ts_generated_at_raw = (
        trend_structure_snapshot.get("generated_at")
        if isinstance(trend_structure_snapshot, dict)
        else None
    )
    _ts_usable = _trend_symbols_usable(trend_structure_snapshot)
    _sys_health = _system_state_source_health(
        artifact_lineage_state=artifact_lineage_state,
        payload_timestamp_value=timestamp,
    )
    _tape_health = _macro_tape_source_health(
        macro_drivers=macro_drivers,
        tape_value_slots=tape_value_slots,
    )
    _ts_health = _trend_structure_source_health(
        artifact_lineage_state=artifact_lineage_state,
        inactive_session=inactive_session,
        snapshot=trend_structure_snapshot,
        ts_generated_at_raw=_ts_generated_at_raw,
        usable_count=_ts_usable,
    )
    _mm_health = _market_map_source_health(
        artifact_lineage_state=artifact_lineage_state,
        inactive_session=inactive_session,
        mm_status=_mm_status,
    )
    _mm_setup_count = (
        _market_map_rendered_setup_count(market_map) if _mm_health == "OK" else 0
    )

    # --- system-state ---
    regime_permission_text = _regime_to_permission_verb(market_regime)
    # PRD-219: distilled system-state — a plain-English verdict (posture verb +
    # decision title, coloured by regime), one context line (regime + the
    # trader-facing reason), and one absolute timestamp. Replaces the
    # REGIME/OUTCOME/PERMISSION grep and the three relative freshness lines. The
    # decision title stays inside the verdict, so the decision-title contract is
    # unchanged. Halt is unmistakable (red verdict, title carries SYSTEM HALT).
    w('<div class="block" id="system-state">')
    w('  <h2>SYSTEM STATE</h2>')
    _verdict_cls = "sys-halt" if bool(system_halted) else _SYS_VERDICT_CLS.get(
        str(market_regime), "sys-flat"
    )
    w(f'  <div class="sys-verdict {_verdict_cls}">'
      f'{_esc(regime_permission_text)} · {_esc(title)}</div>')
    # Context line: regime in plain words + the trader-facing reason (why).
    _regime_plain = _SYS_REGIME_PLAIN.get(
        str(market_regime), str(market_regime).replace("_", " ").title()
    )
    # PRD-220: count the high-grade setups actually present in the market map so
    # the context never contradicts it (an A+ ACTIONABLE card with a "no qualified
    # candidates" verdict was the reported contradiction).
    _hg_count = 0
    if isinstance(market_map, dict):
        _hg_count = sum(
            1 for _sym, _e in (market_map.get("symbols") or {}).items()
            if isinstance(_e, dict) and _e.get("grade", "") in _HIGH_GRADES
        )
    if bool(system_halted):
        # On a halt the operational error is the most actionable context;
        # fall back to the posture reason, then a generic label.
        _ctx_reason: object = first_error or stay_flat_reason or "operational halt"
    elif first_error:
        _ctx_reason = first_error
    elif outcome in (None, "STAY_FLAT", "NO_TRADE"):
        # No trade taken. If the map holds actionable setups, say they're gated
        # (regime/posture standing down) rather than falsely claiming none exist.
        if _hg_count > 0:
            _ctx_reason = f"{_hg_count} setup{'s' if _hg_count != 1 else ''} gated"
        elif alert_candidates:
            _ctx_reason = "candidates gated"
        else:
            _ctx_reason = "no qualified setups"
    else:
        _ctx_reason = None
    # R2: never surface the raw engine internals (regime=…, confidence=…).
    if _ctx_reason and "confidence=" in str(_ctx_reason):
        _ctx_reason = str(_ctx_reason).split(" (regime=")[0].strip()
    _ctx = _esc(_regime_plain) + " regime"
    if _ctx_reason:
        _ctx += " · " + _esc(str(_ctx_reason))
    _ctx_cls = " halted" if bool(system_halted) else ""
    w(f'  <div class="sys-context{_ctx_cls}">{_ctx}</div>')
    if bool(kill_switch):
        w('  <div class="sys-context halted">Kill switch active</div>')
    w('  <div class="sep"></div>')
    # PRD-219: one absolute Pacific timestamp replaces the three relative
    # RUN SNAPSHOT / LIVE STATE / SCOREBOARD freshness lines. It reads the
    # PIPELINE run timestamp (PRD-189 source), not the payload's — so a frozen
    # pipeline still shows an old UPDATED time even when the hourly quote path
    # keeps the payload fresh. Falls back to the payload timestamp when no
    # pipeline run is present.
    _pipeline_run = pipeline_run if pipeline_run is not None else run
    _, _pipeline_run_ts = _first_timestamp(
        _pipeline_run, (("run_at_utc",), ("timestamp",), ("generated_at",))
    )
    _updated_pt, _ = format_dashboard_timestamp(
        str(_pipeline_run_ts or payload_timestamp_value or timestamp or "")
    )
    w('  <div class="label">UPDATED</div>')
    w(f'  <div class="value">{_esc(_updated_pt) if _updated_pt else "unknown"}</div>')
    w("</div>")

    # --- alert-watchlist ---
    if alert_candidates:
        w('<div class="block" id="alert-watchlist">')
        w('  <h2>Alert Watchlist</h2>')
        w('  <div class="label">Candidates gated by execution policy</div>')
        for cand in alert_candidates:
            sym = _esc(str(cand.get("symbol") or "").upper())
            direction = _esc(str(cand.get("direction") or "").upper())
            block_reason = _esc(str(cand.get("block_reason") or "").upper())
            w(f'  <div class="candidate-state">{sym} {direction}'
              + (f' — {block_reason}' if block_reason else '')
              + '</div>')
        w("</div>")

    # --- sunday-macro-context (PRD-116: only under coherent Sunday lineage) ---
    if sunday_coherent:
        ctx = _build_sunday_context(macro_drivers, market_regime, market_map)
        w('<div class="block" id="sunday-macro-context" style="border-color:#29b6f6">')
        w(f'  <h2>{_esc(ctx["headline"])}</h2>')
        w('  <div class="row">')
        w(f'    <div class="field"><div class="label">Posture</div>'
          f'<div class="value">{_esc(ctx["macro_posture"])}</div></div>')
        w(f'    <div class="field"><div class="label">Dollar</div>'
          f'<div class="value">{_esc(ctx["dollar_context"])}</div></div>')
        w(f'    <div class="field"><div class="label">Rates</div>'
          f'<div class="value">{_esc(ctx["rates_context"])}</div></div>')
        w('  </div>')
        w('  <div class="row">')
        w(f'    <div class="field"><div class="label">Volatility</div>'
          f'<div class="value">{_esc(ctx["volatility_context"])}</div></div>')
        w(f'    <div class="field"><div class="label">Risk Sentiment</div>'
          f'<div class="value">{_esc(ctx["risk_context"])}</div></div>')
        w('  </div>')
        w(f'  <div class="field"><div class="label">Metals</div>'
          f'<div class="value">{_esc(ctx["metals_context"])}</div></div>')
        w(f'  <div class="field" style="margin-top:8px"><div class="label">Monday Watch</div>'
          f'<div class="value">{_esc(ctx["monday_watch"])}</div></div>')
        w("</div>")

    # --- macro-tape ---
    w('<div class="block" id="macro-tape">')
    w("  <h2>Macro Tape</h2>")
    if (not macro_drivers) or all(str(v) == "MARKET MAP UNAVAILABLE" for v in macro_drivers.values()):
        w('  <div class="tape-no-data">NO LIVE MACRO DATA</div>')
    tape_value_map = dict(tape_value_slots)

    # Suppress the raw MACRO BIAS label when the integrator detects a genuine
    # regime/macro/setup directional conflict (Rule 3); it emits "Mixed tape —
    # …" in the candidate-board verdict line instead. Post-PRD-160 the macro
    # bias fed to the integrator is the cyclicality-correct one, so this fires
    # only on real divergence.
    if not integrator_suppress["macro_bias"]:
        w(f'  <div class="{_esc(macro_bias_css)}">{_esc(macro_bias)}</div>')
        # PRD-214: single risk-vote tally replaces the per-driver evidence rows.
        # long_votes/short_votes are the cyclicality-aware counts (risk-ON =
        # long, risk-OFF = short) computed above; the tally's bias word is
        # derived from the same counts so it always agrees with the headline.
        _total_votes = long_votes + short_votes
        if _total_votes:
            _tally_bias = (
                "LONG" if long_votes > short_votes
                else "SHORT" if short_votes > long_votes
                else "MIXED"
            )
            w(
                f'  <div class="macro-tally">Risk votes: {short_votes} off / '
                f'{long_votes} on {_FLAT} {_tally_bias}</div>'
            )

    # PRD-217: fold the per-component pressure phrases into one wrapping line
    # beside the tally (replaces the removed MACRO PRESSURE disclosure).
    _pressure_available = (
        bool(macro_drivers)
        and not all(str(v) == "MARKET MAP UNAVAILABLE" for v in macro_drivers.values())
        and isinstance(pressure, dict)
    )
    if _pressure_available:
        _pressure_phrases = [
            _pressure_decision_phrase(_pk, pressure.get(_pk))
            for _pk, _ in _PRESSURE_COMPONENT_LABELS
        ]
        _pressure_phrases = [_p for _p in _pressure_phrases if _p]
        if _pressure_phrases:
            # PRD-220: one bullet per phrase on its own line (was a single
            # middot-joined line).
            w(
                '  <div class="macro-pressure-line">'
                + "<br>".join("• " + _esc(_p) for _p in _pressure_phrases)
                + "</div>"
            )
    else:
        w('  <div class="macro-pressure-line pressure-na">Macro pressure unavailable</div>')

    _tape_arrow_map = dict(tape_slots)

    def _tape_label_padded(display: str) -> str:
        # PRD-224: pad 2-char labels (GC/SI, PRD-211) to the 3-char column with
        # &nbsp; so the arrow glyphs align. Plain spaces cannot do this — HTML
        # collapses consecutive regular spaces even under white-space:nowrap.
        # Applied after _esc; the notification path pads via f"{display:<3}".
        return _esc(display) + "&nbsp;" * max(0, 3 - len(display))

    row_1_html = [
        f'<span class="macro-tape-slot tape-slot {_ARROW_CSS.get(_tape_arrow_map.get(slot.label, _DASH), "na")}">'
        f'<span class="macro-tape-label">{_tape_label_padded(slot.display)} {_esc(_tape_arrow_map.get(slot.label, _DASH))}</span>'
        f'<span class="macro-tape-value" data-symbol="{_esc(slot.label)}">'
        f'{_esc(tape_value_map.get(slot.label, ""))}</span>'
        f'</span>'
        for slot in MACRO_ROW_1.slots
    ]
    w('  <div class="macro-spot-metals-row">' + "".join(row_1_html) + "</div>")

    row_2_html = [
        f'<span class="macro-tape-slot tape-slot {_ARROW_CSS.get(_tape_arrow_map.get(slot.label, _DASH), "na")}">'
        f'<span class="macro-tape-label">{_tape_label_padded(slot.display)} {_esc(_tape_arrow_map.get(slot.label, _DASH))}</span>'
        f'<span class="macro-tape-value" data-symbol="{_esc(slot.label)}">'
        f'{_esc(tape_value_map.get(slot.label, ""))}</span>'
        f'</span>'
        for slot in MACRO_ROW_2.slots
    ]
    w('  <div class="macro-drivers-row">' + "".join(row_2_html) + "</div>")

    # PRD-214: the per-driver macro-evidence rows (PRD-177/PRD-191) are
    # superseded by the one-line risk-vote tally rendered under the MACRO BIAS
    # headline above. The cyclicality-aware vote logic they surfaced is retained
    # in the headline tally computation; only the redundant per-driver
    # presentation is removed.

    # Divider
    w('  <div class="sep"></div>')

    # Tradables grid (PRD-199: monochrome daily %-change arrow + price, 2 per row).
    # The arrow span carries NO _ARROW_CSS color class — color stays reserved
    # for the macro-driver rows. PRD-199 freshness gate: the arrow reads the
    # trend-structure snapshot, so it degrades to the dash sentinel unless that
    # snapshot is health-usable for the current run (_ts_health == "OK" — the same
    # gate the trend section uses). The price (current_price) is independently fresh
    # from market_map and is NOT gated: degradation is fresh price + dash arrow.
    _ts_arrow_ok = _ts_health == "OK"
    w('  <div class="macro-tradables-grid">')
    for slot in TRADABLES_ROW.slots:
        val = tape_value_map.get(slot.label, "N/A")
        arrow = _tape_arrow_map.get(slot.label, _DASH) if _ts_arrow_ok else _DASH
        w(
            f'    <span class="tradable-cell">'
            f'<span class="macro-tape-label">{_esc(slot.label)}</span>'
            f'&nbsp;<span class="tradable-arrow">{_esc(arrow)}</span>'
            f'&nbsp;<span class="macro-tape-value" data-symbol="{_esc(slot.label)}">{_esc(val)}</span>'
            f'</span>'
        )
    w('  </div>')

    # PRD-217: the standalone MACRO PRESSURE disclosure is removed; its
    # per-component phrases now render inline beside the tally above.
    w("</div>")

    # --- red-folder (PRD-176 loader / PRD-177 render): Q2 "what matters today".
    # Presentation only: the caller resolves the loader window (events,
    # expiring, error) and passes a plain view dict; the renderer computes no
    # dates and casts no votes here.
    w('<div class="block" id="red-folder">')
    w("  <h2>Red Folder</h2>")
    if red_folder is not None and not red_folder.get("ok", True):
        _rf_error = red_folder.get("error") or "schedule unavailable"
        w(f'  <div class="value">RED FOLDER UNAVAILABLE: {_esc(str(_rf_error))}</div>')
    else:
        _rf_events = (red_folder or {}).get("events") or []
        if _rf_events:
            for _ev in _rf_events:
                _ev_date = _esc(str(_ev.get("date", "")))
                _ev_time = _esc(str(_ev.get("time_et", "")))
                _ev_name = _esc(str(_ev.get("name", "")))
                _ev_type = _esc(str(_ev.get("type", "")))
                w(
                    f'  <div class="red-folder-event">'
                    f'<span class="red-folder-when">{_ev_date} {_ev_time} ET</span> '
                    f'<span class="red-folder-name">{_ev_name}</span>'
                    f'<span class="red-folder-type"> ({_ev_type})</span>'
                    f"</div>"
                )
        else:
            w('  <div class="value">No red-folder events in the next 48 hours.</div>')
        if (red_folder or {}).get("expiring"):
            w('  <div class="red-folder-expiry">Red-folder schedule nearing expiry -- refresh the calendar.</div>')
    w("</div>")

    # --- trend-structure (PRD-112) ---
    w(f'<div class="block{disabled_class}" id="trend-structure">')
    w('  <h2>Trend Structure</h2>')
    # PRD-123 R6: human-readable degraded-state label and last-snapshot
    # line for the two new "no live data" states. STALE retains its
    # existing rendering — the two are visually and semantically distinct.
    if _ts_health in ("MARKET_CLOSED", "AWAITING_DATA"):
        w('  <div class="label">MARKET CLOSED &#8212; AWAITING INTRADAY DATA</div>')
        if isinstance(_ts_generated_at_raw, str) and _ts_generated_at_raw:
            w(f'  <div class="label">Last snapshot: {_esc(_ts_generated_at_raw)}</div>')
    if unhealthy_lineage:
        # PRD-116 R4: disabled state under unhealthy lineage; no per-symbol data rows.
        w(
            '  <div class="tape-no-data">UNAVAILABLE '
            f'artifact_lineage_state={_esc(artifact_lineage_state)}</div>'
        )
    elif inactive_session:
        # PRD-117 R4: coherent inactive session — render presentation label only.
        w(f'  <div class="tape-no-data">{_esc(INACTIVE_SESSION_LABEL)}</div>')
    else:
        if _ts_records is None:
            w('  <div class="tape-no-data">no trend structure data</div>')
        w(
            '  <table class="ts-table" style="width:100%;border-collapse:collapse;'
            'font-size:0.78rem;display:block;overflow-x:auto">'
        )
        _ts_headers = (
            "Symbol", "Price", "vs VWAP", "Alignment",
            "Entry Context", "RVOL", "SMA 50/200", "Intraday",
        )
        # PRD-165 R2 / PRD-208: collapse a granular column when it is uniformly
        # unavailable. Indices into _ts_headers. PRD-208 cut the redundant
        # "vs SMA50"/"vs SMA200" columns (the "SMA 50/200" arrow composite now
        # carries that position), re-indexing the collapsible set to vs VWAP (2),
        # Alignment (3), Entry Context (4). The composite reserve columns
        # ("SMA 50/200", Intraday) are never collapsed.
        _ts_collapsible_cols = (2, 3, 4)
        _ts_unavailable_cells = {
            "NOT COMPUTED", "INSUFFICIENT HISTORY", "DATA UNAVAILABLE", _DASH,
        }

        _records_for_render = _ts_records or {}
        # PRD-218: each row carries a price-colour class keyed to trend_alignment
        # (bullish green / bearish red) applied to the Price cell.
        _ts_rows: list[tuple[tuple[str, ...], str]] = []
        for _sym in config.TREND_STRUCTURE_SYMBOLS:
            _rec = _records_for_render.get(_sym)
            if _rec is None:
                _cells = (
                    _sym, _DASH, _DASH, _DASH,
                    _DASH, _DASH, _DASH, _DASH,
                )
                _px_cls = ""
            else:
                # PRD-208: "vs SMA50"/"vs SMA200" columns cut; the "SMA 50/200"
                # arrow composite below carries the price-vs-SMA position.
                _cells = (
                    str(_rec.get("symbol", _sym)),
                    _format_trend_number(_rec.get("current_price")),
                    _ts_display(str(_rec.get("price_vs_vwap", ""))),
                    _TS_ALIGN_ABBR.get(
                        str(_rec.get("trend_alignment", "")),
                        _ts_display(str(_rec.get("trend_alignment", ""))),
                    ),
                    _ts_display(str(_rec.get("entry_context", ""))),
                    _format_trend_number(_rec.get("relative_volume")),
                    _trend_structure_composite_display(_rec),
                    _trend_structure_intraday_display(_rec),
                )
                _align = str(_rec.get("trend_alignment", "")).upper()
                _px_cls = (
                    "ts-px-up" if _align == "BULLISH"
                    else "ts-px-down" if _align == "BEARISH"
                    else ""
                )
            _ts_rows.append((_cells, _px_cls))

        # PRD-165 R2: collapse only in the healthy-records path. When
        # `_ts_records` is None the PRD-112 all-or-nothing gate has already
        # degraded the whole section to placeholders — leave that untouched so
        # collapse never salvages a partial row.
        _ts_collapsed: set[int] = set()
        if _ts_records:
            for _ci in _ts_collapsible_cols:
                if all(_row[0][_ci] in _ts_unavailable_cells for _row in _ts_rows):
                    _ts_collapsed.add(_ci)

        w('    <thead><tr style="text-align:left;color:#888">')
        for _i, _hdr in enumerate(_ts_headers):
            if _i in _ts_collapsed:
                continue
            w(f'      <th style="padding:2px 8px">{_esc(_hdr)}</th>')
        w('    </tr></thead>')
        w('    <tbody>')
        for _cells, _px_cls in _ts_rows:
            w('      <tr>')
            for _i, _cell in enumerate(_cells):
                if _i in _ts_collapsed:
                    continue
                # PRD-213: data-label mirrors the column header so the mobile
                # reflow can render the header inline. PRD-218: the Price cell
                # (index 1) carries the alignment colour class. PRD-220: the
                # Intraday cell (index 7) gets a class so it wraps to its own line.
                _classes = []
                if _i == 1 and _px_cls:
                    _classes.append(_px_cls)
                # PRD-225: uniform-width hook — BULL/BEAR/MIX all occupy 4ch so
                # row width (and therefore wrap behavior) is token-independent.
                if _i == 3:
                    _classes.append("ts-align")
                if _i == 7:
                    _classes.append("ts-intraday")
                _cls = f' class="{" ".join(_classes)}"' if _classes else ""
                w(
                    f'        <td data-label="{_esc(_ts_headers[_i])}"{_cls} '
                    'style="padding:2px 8px;white-space:nowrap">'
                    f'{_esc(_cell)}</td>'
                )
            w('      </tr>')
        w('    </tbody>')
        w('  </table>')
    w("</div>")

    # --- candidate-board ---
    w(f'<div class="block{disabled_class}" id="candidate-board">')
    if fixture_mode:
        w('  <h2>Market Map / Developing Setups &#8212; <span style="color:#ff9800">DEMO MODE &#8212; FIXTURE DATA</span></h2>')
    else:
        w("  <h2>Market Map / Developing Setups</h2>")
    # PRD-158 § 4.3: integrator screen verdicts (Rules 2/3) render here as
    # decision-language banner lines. Suppressed under unhealthy lineage so
    # operators see the lineage diagnostic first.
    # PRD-168 D1: when a high-grade card renders below, suppress the RULE2
    # "no qualifying setups" idle verdicts (UX preference). RULE3 conflict
    # signals are not gated (D2). The predicate mirrors the healthy-path card
    # render conditions: not unhealthy, market_map present/usable, not inactive,
    # and at least one non-skipped high-grade symbol.
    _prd168_high_grade_card = (
        not unhealthy_lineage
        and _mm_status not in ("SOURCE_MISSING", "PARSE_ERROR")
        and not inactive_session
        and isinstance(market_map, dict)
        and any(
            entry.get("grade", "") in _HIGH_GRADES
            for sym, entry in ((market_map.get("symbols") or {}).items())
            if sym not in integrator_skips and isinstance(entry, dict)
        )
    )
    if not unhealthy_lineage:
        for _verdict in integrator_verdicts:
            if _prd168_high_grade_card and _verdict in _PRD168_GATED_VERDICTS:
                continue
            w(f'  <div class="idle-summary">{_esc(_verdict)}</div>')
    if unhealthy_lineage:
        # PRD-116 R5: suppress candidate cards and tier headers under unhealthy lineage.
        # Preserve legacy diagnostic text (SOURCE_MISSING / PARSE_ERROR / STALE MARKET MAP)
        # inside the disabled branch so operators retain the file-level reason.
        if artifact_lineage_state == "STALE":
            _run_ts_label = _timestamp_label(run_timestamp_value, run_timestamp)
            _mm_ts_label  = _timestamp_label(market_map_timestamp_value, market_map_timestamp)
            w('  <div class="unavailable">STALE MARKET MAP</div>')
            w('  <div class="idle-summary">'
              '<div>Market Map / Developing Setups paused because market_map timestamp is older than selected run.</div>'
              f'<div>Run: {_esc(_run_ts_label)}</div>'
              f'<div>Market map: {_esc(_mm_ts_label)}</div>'
              '</div>')
        elif _mm_status in ("SOURCE_MISSING", "PARSE_ERROR"):
            w(f'  <div class="unavailable">{_esc(_mm_status)}</div>')
        else:
            w(
                '  <div class="unavailable">UNAVAILABLE '
                f'artifact_lineage_state={_esc(artifact_lineage_state)}</div>'
            )
    elif _mm_status in ("SOURCE_MISSING", "PARSE_ERROR"):
        w(f'  <div class="unavailable">{_esc(_mm_status)}</div>')
    elif inactive_session:
        # PRD-117 R5: coherent inactive session — render presentation label only.
        w(f'  <div class="unavailable">{_esc(INACTIVE_SESSION_LABEL)}</div>')
    else:
        if _mm_status == "STALE":
            w('  <div class="unavailable">STALE</div>')
        if market_map is None:
            w('  <div class="unavailable">N/A</div>')
        else:
            symbols: dict = market_map.get("symbols") or {}
            if not symbols:
                w('  <div class="unavailable">NO_CANDIDATES</div>')
            else:
                # PRD-158 § 4.3 Rule 1: emit one skip line per symbol the
                # integrator flagged for missing required market data; those
                # symbols are then filtered out of tier rendering.
                for skip_sym, skip_line in integrator_skips.items():
                    w(f'  <div class="idle-summary">{_esc(skip_line)}</div>')
                sorted_syms = sorted(
                    [s for s in symbols.keys() if s not in integrator_skips],
                    key=lambda sym: (_GRADE_ORDER.get(symbols[sym].get("grade", ""), 6), sym),
                )
                has_actionable = any(symbols[s].get("grade", "") in _HIGH_GRADES for s in sorted_syms)
                if sorted_syms and not has_actionable:
                    w('  <div class="idle-summary">'
                      '<div>NO ACTIONABLE SETUPS</div>'
                      '<div>Market is not offering structure</div>'
                      '</div>')
                # PRD-158 § 4.3 Rule 4: empty tiers (post-Rule-1 filter) are
                # suppressed by the existing `if not tier_syms: continue` below.
                for tier_id, tier_label, tier_grades in _TIER_DEFS:
                    tier_syms = [s for s in sorted_syms if symbols[s].get("grade", "") in tier_grades]
                    if not tier_syms:
                        continue
                    is_low_tier = tier_grades.isdisjoint(_HIGH_GRADES)
                    if is_low_tier:
                        w(f'  <details class="tier-group" id="tier-{tier_id}">')
                        w(f'    <summary class="tier-header">{_esc(tier_label)} ({len(tier_syms)})</summary>')
                    else:
                        w(f'  <div class="tier-group" id="tier-{tier_id}">')
                        w(f'    <div class="tier-header">{_esc(tier_label)} ({len(tier_syms)})</div>')
                    for sym in tier_syms:
                        _render_candidate_card(
                            w, sym, symbols[sym],
                            contract_entry=(contract_entry_map or {}).get(sym),
                            contract_stop=(contract_stop_map or {}).get(sym),
                        )
                    if is_low_tier:
                        w("  </details>")
                    else:
                        w("  </div>")
            removed_syms: list = market_map.get("removed_symbols") or []
            if removed_syms:
                w('  <div class="removed-symbols">')
                w('    <div class="tier-header">REMOVED</div>')
                for removed_entry in removed_syms:
                    rsym  = _esc(removed_entry.get("symbol"))
                    rprev = _esc(removed_entry.get("previous_grade")) or _DASH
                    w(f'    <div class="removed-row">{rsym} — removed (prev: {rprev})</div>')
                w("  </div>")
    w("</div>")

    # --- run-delta ---
    w('<div class="block" id="run-delta">')
    w("  <h2>Changes Since Last Run</h2>")
    if previous_run is None:
        w('  <div class="value">NO_PREVIOUS_RUN</div>')
    else:
        any_emitted = False
        # PRD-158 § 4.2 translation 13: regime transitions render as
        # "Permission flipped to …" or are suppressed entirely.
        regime_flip = _regime_flip_phrase(
            _req(previous_run, "regime"),
            _req(run, "regime"),
        )
        if regime_flip is not None:
            w(f'  <div class="value">{_esc(regime_flip)}</div>')
            any_emitted = True
        delta_fields = (
            ("Posture",
             _POSTURE_LABELS.get(str(_req(run, "posture")),        str(_req(run, "posture"))),
             _POSTURE_LABELS.get(str(_req(previous_run, "posture")), str(_req(previous_run, "posture")))),
            ("System Halted", _bool_str(_req(run, "system_halted")),
                              _bool_str(_req(previous_run, "system_halted"))),
        )
        for label, current_value, previous_value in delta_fields:
            if current_value != previous_value:
                w(
                    f'  <div class="value">{_esc(label)}: '
                    f'{_esc(previous_value)} -&gt; {_esc(current_value)}</div>'
                )
                any_emitted = True
        if not any_emitted:
            w('  <div class="value">No changes since last run</div>')
    w("</div>")

    # --- scoreboard (PRD-175 aggregation / PRD-177 render): Q4 calibration.
    # Reads the finalized logs/regime_history.jsonl rows (already aggregated by
    # the PRD-175 sidecar); the renderer only formats up to the 10 most-recent
    # dated rows. Empty/absent history renders a single empty-state line, never
    # a dead table.
    w('<div class="block" id="scoreboard">')
    w("  <h2>Scoreboard</h2>")
    if regime_history:
        _board_rows = list(regime_history)[-SCOREBOARD_LIMIT:][::-1]
        for _row in _board_rows:
            _sb_date = _esc(str(_row.get("date", "")))
            _sb_regime = _esc(str(_row.get("regime", "")))
            _sb_posture = _POSTURE_LABELS.get(
                str(_row.get("posture")), str(_row.get("posture", ""))
            )
            _sb_spy = _row.get("spy_close_change_pct")
            _sb_spy_txt = _fmt_pct_signed(_sb_spy) if _sb_spy is not None else "n/a"
            w(
                f'  <div class="scoreboard-row">'
                f'<span class="scoreboard-date">{_sb_date}</span>'
                f'<span class="scoreboard-regime">{_sb_regime}</span>'
                f'<span class="scoreboard-posture">{_esc(_sb_posture)}</span>'
                f'<span class="scoreboard-spy">SPY next {_esc(_sb_spy_txt)}</span>'
                f"</div>"
            )
    else:
        w('  <div class="value">No regime history yet.</div>')
    w("</div>")

    w("</div>")  # .wrap
    w("</div>")
    w("</body>")
    w("</html>")

    return "\n".join(lines)


def write_dashboard(
    payload: dict,
    run: dict,
    previous_run: dict | None = None,
    history_runs: list[dict] | None = None,
    market_map: dict | None = None,
    output_path: Path = _OUTPUT_PATH,
    macro_snapshot_path: Path | None = None,
    market_map_path: Path | None = None,
    contract_entry_map: dict | None = None,
    contract_stop_map: dict | None = None,
    alert_candidates: list[dict] | None = None,
    contract_generated_at: object | None = None,
    payload_source: str | Path = _PAYLOAD_PATH,
    run_source: str | Path = _RUN_PATH,
    market_map_source: str | Path | None = None,
    contract_source: str | Path = _HOURLY_CONTRACT_PATH,
    trend_structure_snapshot: dict | None = None,
    regime_history: list[dict] | None = None,
    red_folder: dict | None = None,
    pipeline_run: dict | None = None,
    fixture_mode: bool = False,
) -> None:
    # PRD-118 R1/R2/R3/R10: validate coherent artifact set before any byte is written
    # to output_path. No-op when output_path is not under `ui/`.
    market_map_for_validation: dict | None = market_map
    if market_map_for_validation is None and market_map_path is not None and market_map_path.exists():
        try:
            market_map_for_validation = json.loads(market_map_path.read_text(encoding="utf-8"))
        except Exception:
            market_map_for_validation = None
    validate_coherent_publish(
        payload=payload,
        run=run,
        market_map=market_map_for_validation,
        output_path=output_path,
        fixture_mode=fixture_mode,
    )

    html = render_dashboard_html(
        payload,
        run,
        previous_run=previous_run,
        history_runs=history_runs,
        market_map=market_map,
        market_map_path=market_map_path,
        macro_snapshot_path=macro_snapshot_path,
        contract_entry_map=contract_entry_map,
        contract_stop_map=contract_stop_map,
        alert_candidates=alert_candidates,
        contract_generated_at=contract_generated_at,
        payload_source=payload_source,
        run_source=run_source,
        market_map_source=market_map_source,
        contract_source=contract_source,
        trend_structure_snapshot=trend_structure_snapshot,
        regime_history=regime_history,
        red_folder=red_folder,
        pipeline_run=pipeline_run,
        fixture_mode=fixture_mode,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def _load_contract_entry_context(
    logs_dir: Path,
) -> tuple[dict[str, float], dict[str, float], list[dict], object | None, Path]:
    """Load latest_hourly_contract entry/stop prices, alert_candidates, and generated_at timestamp."""
    path = logs_dir / _HOURLY_CONTRACT_PATH.name
    contract = _load_json_optional(path)
    if not contract:
        return {}, {}, [], None, path
    entry_map: dict[str, float] = {}
    stop_map: dict[str, float] = {}
    alert_candidates: list[dict] = []
    for cand in (contract.get("trade_candidates") or []):
        sym = cand.get("symbol")
        # PRD-224: the entry path carries the same guards as the PRD-223 stop
        # path below — bool rejected BEFORE coercion (float(True) is 1.0, a
        # masquerading anchor), then finite and positive. Unreachable from
        # valid contracts (finite-float-asserted for ALLOW_TRADE); symmetry
        # defense for malformed artifacts.
        val = cand.get("entry")
        if sym and val is not None and not isinstance(val, bool):
            try:
                entry_f = float(val)
            except (TypeError, ValueError):
                entry_f = None
            if entry_f is not None and math.isfinite(entry_f) and entry_f > 0:
                entry_map[sym] = entry_f
        # PRD-223: the numeric stop feeds the level ladder's risk band; only a
        # finite positive price is drawable. Booleans are rejected BEFORE
        # coercion — float(True) is 1.0, which would masquerade as a real
        # price past every downstream guard.
        stop_val = cand.get("stop")
        if sym and stop_val is not None and not isinstance(stop_val, bool):
            try:
                stop_f = float(stop_val)
            except (TypeError, ValueError):
                stop_f = None
            if stop_f is not None and math.isfinite(stop_f) and stop_f > 0:
                stop_map[sym] = stop_f
        if cand.get("decision_status") != ALLOW_TRADE:
            alert_candidates.append(cand)
    return entry_map, stop_map, alert_candidates, contract.get("generated_at"), path


def _load_regime_history(history_path: Path) -> list[dict]:
    """Load logs/regime_history.jsonl (one JSON object per line) for the
    scoreboard. Returns an empty list when the file is missing or unreadable --
    the section renders its empty-state line. Read-only; never writes."""
    if not history_path.exists():
        return []
    rows: list[dict] = []
    try:
        for line in history_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                rows.append(record)
    except OSError:
        return []
    rows.sort(key=lambda r: str(r.get("date", "")))
    return rows


def _resolve_red_folder_view(now_utc: datetime) -> dict:
    """Resolve the PRD-176 red-folder loader into a plain view dict for the
    renderer: loader error, events inside the 48h window, and the expiry flag.
    The renderer stays date-free; all window math happens here."""
    from cuttingboard import red_folder

    result = red_folder.load_schedule()
    if not result.ok:
        return {"ok": False, "error": result.error, "events": [], "expiring": False}
    events = [
        {"date": e.date, "time_et": e.time_et, "type": e.type, "name": e.name}
        for e in result.events_in_window(now_utc)
    ]
    return {
        "ok": True,
        "error": None,
        "events": events,
        "expiring": result.is_expiring(now_utc),
    }


def main(
    payload_path: Path = _PAYLOAD_PATH,
    run_path: Path = _RUN_PATH,
    output_path: Path = _OUTPUT_PATH,
    logs_dir: Path = Path("logs"),
    macro_snapshot_path: Path | None = None,
    market_map_path: Path | None = None,
    fixture_mode: bool = False,
) -> None:
    import os
    _fixture_mode = fixture_mode or os.environ.get("FIXTURE_MODE", "0") == "1"

    payload    = _load_json(payload_path)
    run        = _load_json(run_path)
    # PRD-189: LIVE STATE must reflect the PIPELINE run (latest_run.json) even
    # when --run overrides `run` with latest_hourly_run.json on the hourly
    # publish path; load it explicitly (optional — absent => "no live run
    # recorded"). When --run is the default this is the same file as `run`.
    # Assumption: the pipeline run lives in --logs-dir (latest_run.json's basename
    # under logs_dir), so a --logs-dir override moves this read with it; pass a
    # logs-dir that contains latest_run.json if you also override --run.
    pipeline_run = _load_json_optional(logs_dir / _RUN_PATH.name)

    previous_run = _resolve_previous_run(logs_dir)
    history_run_files = sorted(logs_dir.glob("run_*.json"))
    history_runs = [_load_json(path) for path in history_run_files]
    history_runs.sort(
        key=lambda history_run: str(_req(history_run, "timestamp")),
        reverse=True,
    )
    history_runs = history_runs[:HISTORY_LIMIT]

    contract_entry_map_raw, contract_stop_map_raw, alert_candidates_raw, contract_generated_at, contract_source = _load_contract_entry_context(logs_dir)
    contract_entry_map = contract_entry_map_raw or None
    contract_stop_map = contract_stop_map_raw or None
    # PRD-166 R2: an explicit --market-map-path overrides the default; when
    # omitted the default is <logs-dir>/market_map.json (current behavior).
    market_map_path = market_map_path if market_map_path is not None else logs_dir / "market_map.json"
    trend_structure_snapshot = _load_trend_structure_snapshot(
        logs_dir / _TREND_STRUCTURE_PATH.name
    )
    # PRD-177: Q4 scoreboard + Q2 red-folder sidecars. Both degrade to their
    # empty-state forms when the artifact is absent and never block publish.
    regime_history = _load_regime_history(logs_dir / "regime_history.jsonl")
    red_folder_view = _resolve_red_folder_view(datetime.now(timezone.utc))

    # PRD-118 R10: validate at the CLI entrypoint before write_dashboard runs.
    # write_dashboard re-validates; main() validation produces an earlier, clean exit.
    _main_market_map: dict | None = None
    if market_map_path.exists():
        try:
            _main_market_map = json.loads(market_map_path.read_text(encoding="utf-8"))
        except Exception:
            _main_market_map = None
    validate_coherent_publish(
        payload=payload,
        run=run,
        market_map=_main_market_map,
        output_path=output_path,
        fixture_mode=_fixture_mode,
    )

    write_dashboard(
        payload, run, previous_run, history_runs, output_path=output_path,
        market_map_path=market_map_path,
        macro_snapshot_path=macro_snapshot_path,
        contract_entry_map=contract_entry_map,
        contract_stop_map=contract_stop_map,
        alert_candidates=alert_candidates_raw or None,
        contract_generated_at=contract_generated_at,
        payload_source=payload_path,
        run_source=run_path,
        market_map_source=market_map_path,
        contract_source=contract_source,
        trend_structure_snapshot=trend_structure_snapshot,
        regime_history=regime_history,
        red_folder=red_folder_view,
        pipeline_run=pipeline_run,
        fixture_mode=_fixture_mode,
    )
    print(f"Dashboard written: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Render Signal Forge dashboard")
    parser.add_argument("--output",         type=Path, default=_OUTPUT_PATH)
    parser.add_argument("--payload",         type=Path, default=_PAYLOAD_PATH)
    parser.add_argument("--run",             type=Path, default=_RUN_PATH)
    parser.add_argument("--logs-dir",        type=Path, default=Path("logs"))
    parser.add_argument("--macro-snapshot",  type=Path, default=None)
    parser.add_argument("--market-map-path", type=Path, default=None)
    args = parser.parse_args()
    main(
        payload_path=args.payload,
        run_path=args.run,
        output_path=args.output,
        logs_dir=args.logs_dir,
        macro_snapshot_path=args.macro_snapshot,
        market_map_path=args.market_map_path,
    )
