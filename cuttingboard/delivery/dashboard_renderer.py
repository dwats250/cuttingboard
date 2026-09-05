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
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from cuttingboard import config
from cuttingboard.contract_types import PipelineContract
from cuttingboard.delivery.dashboard_integrator import (
    RULE2_LONG_VERDICT,
    RULE2_SHORT_VERDICT,
    RULE3_MIXED_VERDICT,
    dashboard_integrator,
)
from cuttingboard.delivery import gex_card
from cuttingboard.delivery import intraday_bars
from cuttingboard.delivery import movement_card
from cuttingboard.delivery import setup_chart
from cuttingboard.delivery.primary_selection import select_primary_card_symbol
from cuttingboard.delivery.macro_tape_layout import (
    MACRO_BIAS_CONTRA_CYCLICAL,
    MACRO_BIAS_DRIVERS,
    MACRO_ROW_1,
    MACRO_ROW_2,
    TRADABLES_ROW,
)
from cuttingboard.macro_pressure import build_macro_pressure
from cuttingboard.trade_decision import ALLOW_TRADE
from cuttingboard.chain_validation import MANUAL_CHECK

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
_GEX_SNAPSHOT_PATH = Path("logs/gex_snapshot.json")  # PRD-309: display-only GEX card sidecar
_MOVEMENT_SNAPSHOT_PATH = Path("logs/watchlist_snapshot.json")  # PRD-311: MARKET MOVEMENT card sidecar
# PRD-321 R2: read-only consumer of the PRD-320 price-bars sidecar (the writer
# owns `runtime.PRICE_BARS_PATH`; the renderer never imports runtime).
_PRICE_BARS_SNAPSHOT_PATH = Path("logs/price_bars_snapshot.json")
_INTRADAY_BARS_SNAPSHOT_PATH = Path("logs/intraday_bars_snapshot.json")  # PRD-324: A1-P intraday sidecar (consumer)
_PRICE_BARS_MAX_AGE_DAYS = 5

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

# PRD-288: SPY session-observation price-vs-VWAP display tokens.
_SPY_PRICE_VS_VWAP_DISPLAY: dict[str, str] = {
    "ABOVE": "ABOVE VWAP",
    "BELOW": "BELOW VWAP",
    "AT_LEVEL": "AT VWAP",
    "UNAVAILABLE": "VWAP UNAVAILABLE",
}

_SPY_STATE_DISPLAY: dict[str, str] = {
    "OBSERVED": "Session data observed",
    "PRE_OPEN": "Pre-open",
    "STALE": "Session data stale",
    "UNAVAILABLE": "Session data unavailable",
}

_SPY_REASON_DISPLAY: dict[str, str] = {
    "system_halted": "system halted",
    "intraday_fetch_failed": "intraday data fetch failed",
    "insufficient_bars": "not enough session bars",
    "pre_open_prior_session": "prior-session reference",
    "session_mismatch": "session date mismatch",
    "pre_open": "awaiting today's session",
    "observation_lag": "session observation delayed",
    "vwap_unavailable": "VWAP unavailable",
}

_ORB_STATE_DISPLAY: dict[str, str] = {
    "PRE_OPEN": "Pre-open",
    "FORMING": "Opening range forming",
    "FORMED": "Opening range formed",
    "UNAVAILABLE": "Opening range unavailable",
    "INVALID": "Opening range invalid",
}

_MCC_VALUE_DISPLAY: dict[str, str] = {
    "EXPANSION_CONFIRMED": "Expansion confirmed",
    "FAILED_EXPANSION": "Expansion failed",
    "RANGE": "Range",
    "NO_BREAK": "No ORB break",
    "ORB_BREAK_HOLDING_LONG": "Long ORB break holding",
    "ORB_BREAK_HOLDING_SHORT": "Short ORB break holding",
    "ORB_RECLAIMED": "ORB reclaimed",
    "FAILED_RECLAIM": "Reclaim failed",
    "NOT_TRIGGERED": "Not triggered",
    "WARNING": "Warning",
    "TRIGGERED": "Triggered",
    "NO_ACTIVE_CANDIDATES": "No active candidates",
    "ACTIONABLE_CANDIDATES": "Actionable candidates present",
    "CANDIDATES_PRESENT_NONE_ACTIONABLE": "Candidates present; none actionable",
    "NO_CANDIDATES": "No candidates qualified this run",
}

_MCC_REASON_DISPLAY: dict[str, str] = {
    "insufficient_bars": "not enough session bars",
    "pre_computation_window": "awaiting the 09:45 ET state window",
    "state_computation_error": "state calculation unavailable",
    "non_current_observation": "session observation is not current",
    "observation_unavailable": "session observation unavailable",
    "event_schedule_unavailable": "event schedule unavailable",
    "transition_state_unavailable": "transition state unavailable",
    "transition_deferred": "transition check deferred",
    "invalidation_deferred_d2": "invalidation check deferred",
    "invalidation_inputs_absent": "invalidation inputs unavailable",
    "invalidation_indeterminate": "invalidation unavailable",
    "candidate_implication_deferred_d3": "candidate qualification deferred",
    "candidate_inputs_absent": "candidate inputs unavailable",
}


def _spy_orb_summary(orb: dict | None) -> str:
    """Render the PRD-271 ORB projection in closed operator language."""
    if not orb:
        return "Opening range unavailable"
    raw_state = str(orb.get("state") or "UNAVAILABLE")
    state = _ORB_STATE_DISPLAY.get(raw_state, "Opening range unavailable")
    high, low = orb.get("orb_high"), orb.get("orb_low")
    if orb.get("state") == "FORMED" and isinstance(high, (int, float)) and isinstance(low, (int, float)):
        state = f"{state} [{low:.2f}, {high:.2f}]"
    return f'<span data-raw-state="{_esc(raw_state)}">{_esc(state)}</span>'


def _mcc_cell_display(cell: dict) -> str:
    """Project a PRD-289 value/reason through a closed display translation."""
    if cell.get("value") is not None:
        raw = str(cell["value"])
        shown = _MCC_VALUE_DISPLAY.get(raw, raw)
        return f'<span data-raw-value="{_esc(raw)}">{_esc(shown)}</span>'
    raw = str(cell.get("unavailable_reason"))
    shown = _MCC_REASON_DISPLAY.get(raw, "unavailable")
    return f'<span data-raw-reason="{_esc(raw)}">Unavailable — {_esc(shown)}</span>'


def _mcc_event_display(cell: dict) -> str:
    if cell.get("unavailable_reason") is not None:
        raw = str(cell["unavailable_reason"])
        shown = _MCC_REASON_DISPLAY.get(raw, "event schedule unavailable")
        return f'<span data-raw-reason="{_esc(raw)}">Unavailable — {_esc(shown)}</span>'
    suffix = " · schedule expiring" if cell.get("expiring") else ""
    if cell.get("value") is not None:
        raw = str(cell["value"])
        shown = "No scheduled events in the next 48 hours" if raw == "no_scheduled_events" else raw
        return f'<span data-raw-value="{_esc(raw)}">{_esc(shown + suffix)}</span>'
    return _esc("; ".join(
        f'{e["date"]} {e["time_et"]} ET — {e["type"]}: {e["name"]}' for e in cell["events"]
    )) + suffix


def _mcc_location_display(cell: dict) -> str:
    raw_state = str(cell["state"])
    text = _SPY_STATE_DISPLAY.get(raw_state, "Session data unavailable")
    if cell.get("reason"):
        text += f' — {_SPY_REASON_DISPLAY.get(str(cell["reason"]), "unavailable")}'
    if cell.get("price_vs_vwap"):
        relation = {
            "ABOVE": "above VWAP",
            "BELOW": "below VWAP",
            "AT_LEVEL": "at VWAP",
        }.get(str(cell["price_vs_vwap"]), "VWAP relation unavailable")
        text += f" ({relation})"
    return f'<span data-raw-state="{_esc(raw_state)}">{_esc(text)}</span>'


def _operator_timestamp(value: object) -> str:
    """Concise Pacific display clock; carrier value remains in data attributes."""
    if isinstance(value, datetime):
        parsed = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    else:
        parsed = _parse_utc_timestamp(value)
    if parsed is None:
        return "Update time unavailable"
    return parsed.astimezone(_PT).strftime("%b %-d · %-I:%M %p PT")


def _operator_clock(value: object) -> str:
    """PRD-330 D-8: time-only Pacific clock for same-session facts."""
    parsed = value if isinstance(value, datetime) else _parse_utc_timestamp(value)
    if parsed is None:
        return "time unavailable"
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).astimezone(_PT).strftime("%-I:%M %p PT")


def _fmt_or_verbatim(fn: object, raw: object) -> str:
    """PRD-330 R2/R4: format an existing field, or render it verbatim (escaped); never invent."""
    try:
        return fn()  # type: ignore[operator]
    except (ValueError, TypeError):
        return _esc(raw if raw is not None else "")


def _mon_d(iso: object) -> str:
    return _fmt_or_verbatim(lambda: date.fromisoformat(str(iso)[:10]).strftime("%b %-d"), iso)


# PRD-330 R8/R12: the closed layer -> (control id, label) map; one entry, so one control.
_LAYER_CONTROLS: dict[str, tuple[str, str]] = {"levels": ("spy-levels", "LEVELS")}
_SPY_REL_WORD = {"ABOVE": "above", "BELOW": "below", "AT_LEVEL": "at"}
_WATCHLIST_CUTOFF_REASON = "entry blocked after 3:30 PM ET"


def _spy_session_lines(spy_obs: dict) -> tuple[str, str]:
    """PRD-330 R2 (D-1, D-8): line 1 (session clock; time-only iff same session) and line 2 (ORB)."""
    state, reason = str(spy_obs.get("state") or "UNAVAILABLE"), spy_obs.get("reason")
    obs_at, intended = spy_obs.get("observed_at_utc"), spy_obs.get("intended_session_date")
    when = _mon_d(intended) if intended else "unknown session"
    price, vwap, rel = spy_obs.get("current_price"), spy_obs.get("session_vwap"), spy_obs.get("price_vs_vwap")
    withheld = " · no current price/VWAP read"
    if state == "OBSERVED" and isinstance(price, (int, float)) and not isinstance(price, bool):
        vwap_txt = (f"{_SPY_REL_WORD.get(str(rel), 'at')} session VWAP {vwap:.2f}"
                    if isinstance(vwap, (int, float)) and not isinstance(vwap, bool) else "· session VWAP unavailable")
        line1 = f"SPY {price:.2f} {vwap_txt} · read {_operator_clock(obs_at)}"
    elif state == "PRE_OPEN" and reason == "pre_open_prior_session":
        line1 = f"Pre-open for {when} · prior session read {_operator_timestamp(obs_at)}"
    elif state == "PRE_OPEN":
        line1 = f"Pre-open · awaiting today's session · last {_operator_clock(obs_at)}"
    elif state == "STALE" and reason == "session_mismatch":
        line1 = f"Session read is from another session · intended {when} · last {_operator_timestamp(obs_at)}{withheld}"
    elif state == "STALE":
        line1 = f"Session read not current · last {_operator_clock(obs_at)}{withheld}"
    else:
        line1 = f"No session read for {when} · {_SPY_REASON_DISPLAY.get(str(reason), 'reason not recognised')}"
    orb = spy_obs.get("orb") if isinstance(spy_obs.get("orb"), dict) else None
    hi, lo = (orb or {}).get("orb_high"), (orb or {}).get("orb_low")
    if orb and orb.get("state") == "FORMED" and isinstance(hi, (int, float)) and isinstance(lo, (int, float)):
        line2 = f"ORB {lo:.2f}-{hi:.2f}"
    elif orb and orb.get("state") == "PRE_OPEN":
        line2 = "Opening range pre-open"
    else:
        line2 = _spy_orb_summary(orb)
    return line1, line2


def _spy_clock_line(mm_clock_label: str, intended: object, caption: str) -> str:
    """PRD-330 R2 line 3: map clock (time-only iff same Pacific day as the session) + bars `as_of`."""
    parsed = _parse_utc_timestamp(mm_clock_label)
    same_day = parsed is not None and bool(intended) and parsed.astimezone(_PT).date().isoformat() == str(intended)[:10]
    clock = _operator_clock(parsed) if same_day else _operator_timestamp(parsed if parsed else mm_clock_label)
    as_of = caption.split("bars through ", 1)[1][:10] if "bars through " in caption else ""
    return f"Market-map levels {clock} · daily bars through {_mon_d(as_of) if as_of else 'unknown date'}"


def _next_event_line(red_folder: object) -> str:
    """PRD-330 R4: the named next event from the existing red-folder view (window stays loader-owned)."""
    if not (isinstance(red_folder, dict) and red_folder.get("ok", True)):
        return "Event schedule unavailable"
    events = [e for e in (red_folder.get("events") or []) if isinstance(e, dict)]
    text = "No scheduled events in the next 48 hours"
    if events:
        ev = events[0]
        when = _fmt_or_verbatim(lambda: date.fromisoformat(str(ev.get("date"))[:10]).strftime("%a %b %-d"), ev.get("date"))
        at = _fmt_or_verbatim(lambda: datetime.strptime(str(ev.get("time_et")), "%H:%M").strftime("%-I:%M %p"), ev.get("time_et"))
        text = f"{ev.get('type') or ev.get('name') or 'event'} · {when} · {at} ET" + (
            f" · +{len(events) - 1} more in DETAILS" if len(events) > 1 else "")
    return text + (" · schedule expiring" if red_folder.get("expiring") else "")


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

# PRD-250: client-side page-age banner threshold. During an ACTIVE session a
# refresh is due roughly hourly (one slot + routine lag + render); past this the
# published board may no longer describe today's tape, so a sizing decision
# should not rest on it. Derived from the decision, not from false-positive
# avoidance (see docs/prd_history/PRD-250.proposal.md §4). The freshness verdict
# is computed in-browser against the viewer's clock — never baked here — so a
# frozen board cannot freeze its own "fresh" label.
BOARD_STALE_AFTER_SECONDS = 90 * 60  # 90 min

# PRD-250: inline client-side staleness script. Reads the machine-readable
# UPDATED timestamp emitted on #cb-updated, compares it to the viewer's clock at
# VIEW time, and paints a page-age notice into #staleness-banner. Re-runs on each
# <meta http-equiv="refresh"> reload. Server bakes NO verdict; the browser is the
# only component that keeps running when the pipeline stops. `data-session-inactive`
# is the server-supplied "was a refresh due" signal (payload.meta.session_type via
# inactive_session) — no market calendar is reimplemented here. Informs the age
# condition only; it never instructs an action.
_STALENESS_BANNER_JS = """
(function () {
  function fmtAge(sec) {
    var m = Math.floor(sec / 60);
    if (m < 60) return m + "m";
    var h = Math.floor(m / 60);
    if (h < 24) return h + "h";
    return Math.floor(h / 24) + "d";
  }
  function run() {
    var banner = document.getElementById("staleness-banner");
    if (!banner) return;
    var el = document.getElementById("cb-updated");
    var iso = el ? el.getAttribute("data-updated-utc") : "";
    var updated = iso ? new Date(iso) : null;
    if (!updated || isNaN(updated.getTime())) {
      banner.textContent = "LAST UPDATE: UNAVAILABLE";
      banner.style.color = "#888";
      banner.hidden = false;
      return;
    }
    var ageSec = (Date.now() - updated.getTime()) / 1000;
    var staleAfter = parseInt(banner.getAttribute("data-board-stale-after-s"), 10);
    if (!(staleAfter > 0)) staleAfter = 5400;
    var inactive = banner.getAttribute("data-session-inactive") === "true";
    if (inactive) {
      banner.textContent = "MARKET CLOSED \\u00b7 LAST UPDATE " + fmtAge(ageSec) + " AGO";
      banner.style.color = "#888";
      banner.hidden = false;
      return;
    }
    if (ageSec > staleAfter) {
      banner.textContent = "BOARD " + fmtAge(ageSec) + " OLD";
      banner.style.color = "#ff9800";
      banner.style.borderColor = "#ff9800";
      banner.hidden = false;
    } else {
      banner.hidden = true;
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();
"""

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
_LOCKED_INTEGRATOR_VERDICTS: dict[str, str] = {
    RULE2_LONG_VERDICT: "No high-grade setups observed for the current regime.",
    RULE2_SHORT_VERDICT: "No high-grade setups observed for the current regime.",
    RULE3_MIXED_VERDICT: "Mixed regime, macro, and symbol observations.",
}
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
    "body{background:#0d0d0d;color:#e0e0e0;font-family:ui-monospace,'SF Mono',Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace;font-size:13px;padding:1rem}"
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
    ".sys-permission{color:#aaa;font-size:0.78rem;line-height:1.35;margin-top:4px}"
    ".sys-context.halted{color:#f44336}"
    # PRD-281: WHY line -- the already-authoritative reason, promoted out of
    # sys-context into its own line under the verdict. Bolder than
    # sys-context (it is the headline answer to "why"), plainer than the
    # decision-state/verdict colour classes (it never overrides HALT red).
    ".sys-why{color:#ccc;font-size:0.85rem;font-weight:bold;margin-top:4px}"
    # PRD-279: Decision State Header -- prominent HALT/STAY FLAT/TRADE
    # PERMITTED label above the existing sys-verdict line. Reuses the
    # sys-up/sys-down/sys-flat/sys-halt colour classes for consistency.
    ".decision-state{font-weight:bold;font-size:1.4rem;letter-spacing:0.02em}"
    ".decision-state.sys-up{color:#4caf50}"
    ".decision-state.sys-down{color:#f44336}"
    ".decision-state.sys-flat{color:#ff9800}"
    ".decision-state.sys-halt{color:#f44336}"
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
    # PRD-249: one-line identity header replaces the 8-line stacked SYMBOL/GRADE/
    # BIAS/STRUCTURE block.
    ".card-header{font-weight:bold;margin-bottom:6px}"
    # Change #4: IF NOW / IN / OUT couplets in one aligned-column grid; the
    # lifecycle line spans both tracks so the labels stay aligned.
    ".card-brief{gap:3px .75rem;align-items:baseline}"
    ".card-brief .value,.card-brief .value-key{margin-top:0}"
    ".card-brief .lifecycle-detail{grid-column:1/-1;margin:2px 0}"
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
    ".tier-header{font-size:.72rem;font-weight:normal;color:#888;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;opacity:1}"
    ".candidate-state{font-weight:bold;margin-bottom:4px}"
    ".candidate-risk{color:#ff9800}"
    ".candidate-state.manual-check{border-left:3px solid #ff9800;padding:4px 8px}"
    ".manual-check-flag{display:inline-block;border:1px solid currentColor;border-radius:3px;padding:0 5px;margin-right:6px;font-size:.7rem;letter-spacing:.06em;color:#ff9800}"
    ".tape-slot.up{color:#4caf50}"
    ".tape-slot.down{color:#f44336}"
    ".tape-slot.flat{color:#888}"
    ".tape-slot.na{color:#444;opacity:0.7}"
    ".macro-bias.long{color:#4caf50}"
    ".macro-bias.short{color:#f44336}"
    ".macro-bias.mixed{color:#ff9800}"
    # Change #3: TAPE bias-token colour -- reuses the palette, adds no weight or
    # margin (unlike .macro-bias), so only the direction token gets the accent.
    ".tape-bias.long{color:#4caf50}.tape-bias.short{color:#f44336}.tape-bias.mixed{color:#ff9800}"
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
    ".lvl-unavail{color:#555;font-size:0.75rem;font-style:italic;margin-top:6px}"
    # PRD-321: the setup chart is the primary spatial representation. viewBox
    # scaling only — width:100% inside the card, capped so a desktop card shows
    # the SAME svg wider rather than a second chart system.
    ".setup-chart{margin-top:8px;padding-top:6px;border-top:1px solid #1a1a1a}"
    ".setup-chart svg{display:block;width:100%;height:auto;max-width:520px}"
    ".chart-caption{color:#666;font-size:0.68rem;margin-top:2px}"
    ".chart-detail{margin-top:8px}"
    ".chart-detail>summary{cursor:pointer;color:#777;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em}"
    # PRD-321 R4: compact tiered ladder — the chart's subordinate exact-level
    # reference and the no-bars fallback. Tier 1 strongest, Tier 2 clear,
    # Tier 3 faint; the tier weights are the assertion surface.
    ".lvl-ladder{margin-top:6px;padding-top:5px;border-top:1px solid #1a1a1a;"
    "max-width:520px;font-family:ui-monospace,'SF Mono',Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace;font-size:0.72rem;line-height:1.5}"
    ".lvl-row{display:grid;grid-template-columns:minmax(6ch,auto) 1fr auto;"
    "column-gap:8px;white-space:nowrap}"
    ".lvl-px{text-align:right}"
    ".lvl-pct{text-align:right;min-width:6ch}"
    ".lvl-t1{color:#ddd;font-weight:700;opacity:1}"
    ".lvl-t2{color:#3a7a8a;font-weight:400;opacity:0.9}"
    ".lvl-t3{color:#555;font-weight:400;opacity:0.65}"
    ".lvl-now{color:#f5c518}"
    ".lvl-entry{color:#e0a552}"
    ".lvl-stop{color:#e05252}"
    ".lvl-vwap{color:#29b6f6}"
    ".lvl-neutral{color:#6b7280}"
    ".lvl-riskband{padding-left:5px;margin:1px 0}"
    ".lvl-inrisk{border-left:2px solid #e05252;background:rgba(224,82,82,.06)}"
    ".lvl-lockrisk{border-left:2px solid #6b7280;background:rgba(107,114,128,.06)}"
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
    # PRD-265 R5: coverage-bounded day marker on the scoreboard row.
    ".scoreboard-coverage{color:#ff9800;font-weight:600}"
    # PRD-318: answer-first zones. Existing subsystem blocks remain intact in
    # the DOM, but their supporting-evidence copies lose peer-card weight under
    # DETAILS / HISTORY.
    ".operator-zone{background:#101010}"
    ".operator-zone>h2{color:#aaa}"
    ".zone-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 14px}"
    ".zone-item{min-width:0}"
    ".zone-value{font-size:.82rem;line-height:1.35;margin-top:2px}"
    ".zone-note{color:#777;font-size:.7rem;line-height:1.3;margin-top:2px}"
    # PRD-322: TAPE operator-context bands. Both strips are COLUMN GRIDS (the
    # PRD-321 `.lvl-row` pattern) so every driver and every symbol lines up on
    # the same vertical edges; `auto-fit` drops a column rather than
    # overflowing, and `.tape-slot`'s nowrap keeps each cell on one line.
    ".tape-band-cap{color:#777;font-size:.64rem;text-transform:uppercase;letter-spacing:.1em}"
    ".tape-drivers{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));"
    "gap:2px 12px;margin-top:6px;color:#aaa;font-size:.75rem}"
    ".tape-driver{display:grid;grid-template-columns:3ch 1ch auto;column-gap:4px}"
    ".tape-trend{display:grid;grid-template-columns:repeat(auto-fit,minmax(154px,1fr));"
    "gap:1px 12px;margin-top:5px;font-size:.72rem}"
    ".tape-trend-row{display:grid;grid-template-columns:4ch 4ch 4ch 5ch 2ch;column-gap:5px}"
    ".tape-foot{margin-top:2px;opacity:.72}"
    ".tape-band+.tape-band,.tape-band+.tape-foot{margin-top:6px}"
    "#verdict-zone{border-color:#3a3a3a}"
    "#verdict-zone #system-state.block{border:0;margin:0;padding:0}"
    "#system-state>h2{margin-bottom:.3rem}"
    # Change #1: demote the freshness timestamp below state/why/context so
    # metadata no longer outranks meaning under the page anchor.
    "#system-state #cb-updated{color:#666;font-size:.72rem;margin-top:6px}"
    "#staleness-banner{border:1px solid currentColor;border-radius:3px;padding:5px 8px;margin-bottom:8px;font-size:.72rem;letter-spacing:.04em}"
    ".verdict-warning{border-left:3px solid #ff9800;color:#ff9800;padding:6px 8px;margin-bottom:8px}"
    "#watching-zone .operator-subsection{padding-top:10px;margin-top:10px;border-top:1px solid #222}"
    "#watching-zone .operator-subsection:first-of-type{padding-top:0;margin-top:0;border-top:0}"
    "#watching-zone .block{border:0;border-radius:0;margin-bottom:0;padding-left:0;padding-right:0}"
    "#watching-zone h3,#details-history h3{font-size:.75rem;color:#888;text-transform:uppercase;letter-spacing:.06em;margin-bottom:7px}"
    ".candidate-observation{opacity:.82}"
    ".candidate-observation .value-actionable{color:inherit}"
    ".level-detail{margin-top:6px}"
    ".level-detail>summary{cursor:pointer;color:#777;font-size:.7rem;text-transform:uppercase}"
    "#details-history>summary{cursor:pointer;list-style:none;color:#aaa;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em}"
    "#details-history>summary::-webkit-details-marker{display:none}"
    "#details-history>.details-body{margin-top:10px}"
    "#details-history .block{border:0;border-radius:0;border-top:1px solid #222;margin:0;padding:12px 0}"
    "#details-history .block:first-child{border-top:0}"
    "#details-history .block h2{margin-bottom:7px}"
    ".spy-session-group{border-top:1px solid #222;padding-top:12px}"
    ".spy-session-group>.block:first-of-type{border-top:0}"
    # PRD-330 (D4): SPY SESSION section + header lines; native LEVELS control (hidden focusable checkbox, 44 px label); NEXT EVENT strip; WATCHING line.
    "#spy-session{border:1px solid #2a2a2a;border-radius:4px;background:#101010;padding:1rem;margin-bottom:1rem}#spy-session>h3{font-size:.8rem;color:#aaa;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.75rem;font-weight:normal}#spy-observation{border:0;border-radius:0;padding:0;margin:0}#spy-session .spy-chart{margin-top:6px}"
    ".spy-read{font-size:.82rem;line-height:1.35}.spy-clock{color:#777;font-size:.7rem;line-height:1.3;margin-top:4px}.chart-controls{display:flex;justify-content:flex-end;margin-top:8px}"
    ".chart-toggle{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0}"
    ".chart-toggle-label{display:inline-flex;align-items:center;min-height:44px;cursor:pointer;color:#777;border:1px solid #2a2a2a;border-radius:3px;padding:0 10px;font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;user-select:none}.chart-toggle-label::before{content:'\\25A1  ';color:#555}"
    ".chart-toggle:checked~.chart-controls .chart-toggle-label{color:#e0e0e0;border-color:#3a7a8a;background:#132a30}.chart-toggle:checked~.chart-controls .chart-toggle-label::before{content:'\\25A0  ';color:#29b6f6}.chart-toggle:focus-visible~.chart-controls .chart-toggle-label{outline:1px solid #29b6f6}"
    "#spy-levels:checked~.spy-chart .chart-layer[data-layer=\"levels\"]{display:inline}"
    "#today-zone h2{display:inline;margin:0 10px 0 0}#today-zone .event-line{display:inline;font-size:.85rem;font-weight:bold;color:#e0e0e0}.screen-line{color:#777;font-size:.7rem;line-height:1.3;margin:-2px 0 8px 0}.scope-note{text-transform:none;letter-spacing:0;color:#666;font-weight:normal}"
    # PRD-215: "actionable now" accent (cyan #29b6f6 — the level/VWAP colour) on
    # the falsifiable trade fields, plus the collapsed REASON/PLAY/WATCH detail.
    ".value-actionable{color:#29b6f6}"
    ".card-detail summary{cursor:pointer;list-style:none;color:#888;font-size:0.72rem;"
    "text-transform:uppercase;letter-spacing:.05em;margin-top:4px}"
    ".card-detail summary::-webkit-details-marker{display:none}"
    # PRD-218: alignment-coloured price (bullish green / bearish red).
    ".ts-px-up{color:#4caf50}"
    ".ts-px-down{color:#f44336}"
    # PRD-332 (D5) main-section rules: C WATCHING setup-workspace + A-upper
    # refinements. Placed in the main-rules section (before any @media block) so
    # the 44px tab target is not scoped into a phone block (PRD-330 R8). No
    # existing rule string is edited (R5). Responsive additions are appended in
    # @media blocks at the very end of _CSS.
    ".setup-workspace{min-width:0}"
    ".setup-select{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0}"
    ".setup-tabs{display:flex;flex-wrap:nowrap;overflow-x:auto;border-bottom:1px solid #2a2a2a;margin-bottom:10px;min-width:0}"
    ".setup-tab{flex:0 0 auto;min-height:44px;display:inline-flex;align-items:center;gap:6px;padding:0 12px;cursor:pointer;color:#888;background:transparent;border-bottom:2px solid transparent;border-left:0;white-space:nowrap;font-size:.75rem;letter-spacing:.04em;user-select:none}"
    ".setup-tab-sym{font-weight:bold}"
    ".setup-tab-grade{color:#aaa}"
    ".setup-tab-lc{display:inline-block;padding:0 .35rem;border-radius:3px;font-size:.68rem}"
    ".setup-tab-check{border:1px solid currentColor;border-radius:3px;padding:0 4px;font-size:.62rem;letter-spacing:.06em;color:#ff9800}"
    ".setup-panels{min-width:0}"
    ".setup-panel{min-width:0}"
    # PRD-332 (D5) / PR #319 salvage: 44px touch targets on the WATCHING and
    # DETAILS/HISTORY disclosures (main-section, so not scoped into a phone block).
    "#watching-zone summary,#details-history>summary{min-height:44px;display:flex;align-items:center}"
    "#verdict-zone{border-left:3px solid #3a3a3a}"
    "#verdict-zone:has(.decision-state.sys-up){border-left-color:#4caf50}"
    "#verdict-zone:has(.decision-state.sys-down),#verdict-zone:has(.decision-state.sys-halt){border-left-color:#f44336}"
    "#verdict-zone:has(.decision-state.sys-flat){border-left-color:#ff9800}"
    "#today-zone{border-left:3px solid #ff9800}"
    ".lvl-ladder,.tape-drivers,.tape-trend,.history-table{font-variant-numeric:tabular-nums}"
    # Change #5: desktop-width trend-table readability. Scoped >=641px so the
    # <=640px flex-card reflow below stays byte-identical. white-space:normal
    # needs !important to beat each td's inline "white-space:nowrap".
    "@media(min-width:641px){"
    ".ts-table td{border-top:1px solid #1a1a1a}"
    ".ts-table tbody tr:first-child td{border-top:0}"
    ".ts-table td:first-child{font-weight:bold}"
    ".ts-table td.ts-intraday{color:#888;white-space:normal!important;max-width:22ch}"
    ".ts-table td[data-label='Price'],.ts-table td[data-label='RVOL']{text-align:right}"
    "}"
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
    # PRD-318: phone-first compaction at the existing 430px boundary.
    "@media(max-width:430px){"
    "body{padding:8px}"
    ".operator-zone{padding:10px;margin-bottom:8px}"
    ".operator-zone>h2{margin-bottom:7px}"
    ".zone-grid{gap:6px 10px}"
    ".zone-value{font-size:.78rem}"
    ".decision-state{font-size:1.25rem}"
    ".sys-verdict{font-size:.82rem}"
    ".sys-why{font-size:.78rem;margin-top:3px}"
    ".sys-context{font-size:.74rem}"
    "#system-state .sep{margin:5px 0}"
    "#watching-zone .operator-subsection{padding-top:8px;margin-top:8px}"
    "#opportunity-survival .kv-grid{grid-template-columns:auto minmax(2.5ch,1fr) auto minmax(2.5ch,1fr)}"
    "#opportunity-survival .kv-grid>*:nth-child(10){grid-column:2/-1}"
    "#candidate-board .candidate-scope{padding:5px 7px;margin-bottom:6px;font-size:.68rem;line-height:1.25}"
    "#candidate-board:not(:has(.candidate-card)) .unavailable{font-size:.72rem}"
    "#details-history .block{padding:10px 0}"
    "}"
    # PRD-330: phone parity in a SEPARATE media block; the PRD-318/327 block above stays byte-identical.
    "@media(max-width:430px){#spy-session{padding:10px;margin-bottom:8px}#spy-session>h3{margin-bottom:7px}#today-zone{padding:8px 10px}}"
    # PRD-332 (D5) tail: desktop + phone media additions for the C WATCHING setup
    # workspace and A-upper refinements. The main-section D5 rules are inserted in
    # the main-rules section above (before the phone blocks) so no 44px touch
    # target lands inside a phone @media block (PRD-330 R8). Append-only; no
    # existing rule string is edited (R5).
    "@media(min-width:641px){"
    ".wrap{max-width:760px}"
    ".tape-drivers{grid-template-columns:repeat(auto-fit,minmax(9ch,1fr))}"
    ".setup-workspace{display:grid;grid-template-columns:minmax(9ch,13ch) minmax(0,1fr);column-gap:14px;align-items:start}"
    ".setup-workspace>.setup-tabs{grid-column:1;flex-direction:column;flex-wrap:nowrap;overflow-x:visible;border-bottom:0;border-right:1px solid #222;margin-bottom:0}"
    ".setup-workspace>.setup-panels{grid-column:2;min-width:0}"
    ".setup-tab{border-bottom:0;border-left:3px solid transparent;justify-content:space-between}"
    "}"
    "@media(max-width:430px){"
    ".setup-tabs{margin-bottom:8px}"
    ".setup-tab{padding:0 10px;font-size:.72rem}"
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


def _load_price_bars_snapshot(path: Path) -> dict | None:
    """PRD-321 R2: read the PRD-320 price-bars sidecar; never raise.

    Missing, unreadable, non-JSON, or structurally wrong => None, and every
    candidate degrades to the compact ladder. Nothing outside the chart region
    changes: this loader is the only place the artifact is touched.
    """
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("symbols"), dict):
        return None
    return data


def _load_intraday_bars_snapshot(path: Path) -> dict | None:
    """PRD-324 (A1-C) R1: read the A1-P intraday 1m sidecar; never raise.

    Missing, unreadable, non-UTF-8, corrupt JSON, or a non-object top level =>
    None, and the primary card keeps its existing daily chart. Deeper defensive
    admission of the persisted content lives in
    ``intraday_bars.derive_intraday_session`` (R2); this loader only reads.
    """
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _price_bars_caption(snapshot: dict, as_of: str) -> str:
    """PRD-321 R2: the honesty caption — the bars' `as_of` plus the sidecar's
    own source provenance (`source.provider` / `source.interval`)."""
    caption = f"bars through {as_of}"
    source = snapshot.get("source")
    if isinstance(source, dict):
        provenance = " ".join(
            part for part in (
                str(source.get("provider") or "").strip(),
                str(source.get("interval") or "").strip(),
            ) if part
        )
        if provenance:
            caption = f"{caption} · {provenance}"
    return caption


def _price_bars_by_symbol(
    snapshot: dict | None, now: datetime
) -> dict[str, tuple[list, str]]:
    """PRD-321 R2: `{symbol: (completed bars, caption)}` for the symbols that
    clear the age guard.

    The guard is UTC calendar-day arithmetic: a symbol is bars-absent when
    (UTC date of `now`) minus (its `as_of` date) exceeds 5 days. A symbol whose
    entry is malformed, whose `as_of` is unparseable, or whose bar list is
    empty is simply absent — OHLC is never synthesized or padded.
    """
    usable: dict[str, tuple[list, str]] = {}
    if not isinstance(snapshot, dict):
        return usable
    symbols = snapshot.get("symbols")
    if not isinstance(symbols, dict):
        return usable
    now_date = now.astimezone(timezone.utc).date()
    for symbol, record in symbols.items():
        if not isinstance(record, dict):
            continue
        bars = record.get("bars")
        as_of = record.get("as_of")
        if not isinstance(bars, list) or not bars or not isinstance(as_of, str):
            continue
        try:
            as_of_date = date.fromisoformat(as_of[:10])
        except ValueError:
            continue
        if (now_date - as_of_date).days > _PRICE_BARS_MAX_AGE_DAYS:
            continue
        usable[str(symbol)] = (bars, _price_bars_caption(snapshot, as_of[:10]))
    return usable


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


def _coverage_bounded(row: dict) -> bool:
    """PRD-265 four-state coverage predicate: coverage_bounded(row) :=
    "total_votes" in row and 0 < row["total_votes"] < 8.

    absent (key not in row) = LEGACY (a regime_history row from before this
    field existed) -- never marked BOUNDED. total_votes == 0 (EXPANSION) and
    == 8 (FULL) are likewise never marked. Only 0 < total_votes < 8 renders
    the BOUNDED marker. A present-but-None value is treated the same as
    absent, never crashing the comparison below.
    """
    if "total_votes" not in row:
        return False
    total_votes = row["total_votes"]
    if total_votes is None:
        return False
    return 0 < total_votes < 8


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
) -> list[tuple[str, str]]:
    # PRD-312: the Macro-Tape tradables daily-change arrow (formerly the SIGN of
    # the trend-structure record `daily_change_pct`) is retired here — it
    # duplicated the Market Movement card's signed value. Only the macro-driver
    # arrows remain; the tradables row keeps its label + price (no arrow).
    slots: list[tuple[str, str]] = []

    for row in (MACRO_ROW_1, MACRO_ROW_2):
        for slot in row.slots:
            block = macro_drivers.get(slot.payload_key) if macro_drivers else None
            change_pct = block.get("change_pct") if isinstance(block, dict) else None
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


# PRD-322: TAPE operator-context vocabularies. Closed display maps only — the
# bands project values already bound in the render body and compute no new
# fact. `overall_pressure` is deliberately absent: TAPE shows the per-driver
# component states, never the aggregate.
_TAPE_PRESSURE_DISPLAY: dict[str, str] = {
    "RISK_ON": "risk-on", "RISK_OFF": "risk-off",
    "NEUTRAL": "neutral", "UNKNOWN": "n/a",
}
_TAPE_PRESSURE_COMPONENTS: tuple[tuple[str, str], ...] = (
    ("volatility_pressure", "VIX"), ("dollar_pressure", "DXY"),
    ("rates_pressure", "10Y"), ("bitcoin_pressure", "BTC"),
)
# The vs-VWAP glyph set is NEW to PRD-322 and closed: a glyph renders only for
# a computed comparison token, never for DATA_UNAVAILABLE / NOT_COMPUTED.
_TAPE_VWAP_GLYPH: dict[str, str] = {"ABOVE": "V↑", "BELOW": "V↓", "AT_LEVEL": "V="}
# A trend row "counts" only when its alignment is an actual comparison outcome.
_TAPE_COMPUTED_ALIGNMENTS: frozenset[str] = frozenset({"BULLISH", "BEARISH", "MIXED"})
_TAPE_ALIGN_CSS: dict[str, str] = {"BULLISH": "up", "BEARISH": "down", "MIXED": "flat"}
_TAPE_TREND_HEALTH_TEXT: dict[str, str] = {
    "MARKET_CLOSED": "Market closed — awaiting intraday data",
    "AWAITING_DATA": "Market closed — awaiting intraday data",
    "STALE": "Trend stale",
}
_TAPE_TREND_HEALTH_FALLBACK = "Trend data unavailable"
_TAPE_TREND_ABSENT = "Trend unavailable"
_TAPE_PRESSURE_ABSENT = "Pressure unavailable"
_TAPE_MACRO_ABSENT = "Macro unavailable"
# The 9 arrow composites are all shaped "<a> 50 <b> 200"; splitting on the
# window boundary yields the two aligned grid cells without inventing a token.
_TAPE_COMPOSITE_SPLIT = " 50 "


def _tape_trend_summary(ts_records: dict | None, ts_health: str) -> tuple[str, str]:
    """PRD-322 R1: health-aware TAPE trend summary -> (text, derivation token).

    Unavailability is never rendered as bearishness: only rows whose
    `trend_alignment` is a computed comparison enter the denominator. All six
    computed reproduces the pre-PRD-322 string byte-for-byte; every degraded
    branch derives from `_trend_structure_source_health`, not from a count.
    """
    rows = list((ts_records or {}).values())
    if not rows:
        return _TAPE_TREND_ABSENT, "trend-health"
    computed = [
        rec for rec in rows
        if isinstance(rec, dict)
        and str(rec.get("trend_alignment", "")) in _TAPE_COMPUTED_ALIGNMENTS
    ]
    bullish = sum(1 for rec in computed if rec.get("trend_alignment") == "BULLISH")
    if len(computed) == len(rows):
        return f"{bullish} of {len(rows)} bullish", "bullish-row-count"
    if computed:
        return (
            f"{bullish} of {len(computed)} bullish · {len(rows) - len(computed)} n/a",
            "trend-health",
        )
    return _TAPE_TREND_HEALTH_TEXT.get(ts_health, _TAPE_TREND_HEALTH_FALLBACK), "trend-health"


def _build_trend_chips(
    ts_records: dict | None,
) -> list[tuple[str, str, str, str, str, str]]:
    """PRD-322 R4: one aligned TAPE row per curated symbol, in
    `config.TREND_STRUCTURE_SYMBOLS` order.

    Returns (symbol, alignment, sma_50, sma_200, vwap, css_class). Every token
    comes verbatim from an existing translator (`_TS_ALIGN_ABBR`,
    `_trend_structure_composite_display`) or the closed `_TAPE_VWAP_GLYPH` map.
    A row whose alignment is not computed renders symbol + dash only — never a
    partial arrow. Enumeration only: no breadth metric, ratio, or score.
    """
    records = ts_records or {}
    rows: list[tuple[str, str, str, str, str, str]] = []
    for symbol in config.TREND_STRUCTURE_SYMBOLS:
        record = records.get(symbol)
        alignment = str(record.get("trend_alignment", "")) if isinstance(record, dict) else ""
        if alignment not in _TAPE_COMPUTED_ALIGNMENTS:
            rows.append((symbol, _DASH, "", "", "", "na"))
            continue
        composite = _trend_structure_composite_display(record)
        head, _sep, tail = composite.partition(_TAPE_COMPOSITE_SPLIT)
        sma_50, sma_200 = (f"{head} 50", tail) if tail else (composite, "")
        rows.append((
            symbol,
            _TS_ALIGN_ABBR[alignment],
            sma_50,
            sma_200,
            _TAPE_VWAP_GLYPH.get(str(record.get("price_vs_vwap", "")), ""),
            _TAPE_ALIGN_CSS[alignment],
        ))
    return rows


def _pressure_note(pressure: dict | None) -> str:
    """PRD-322 R2: per-driver macro-pressure states through a closed four-state
    display map. The aggregate `overall_pressure` is never read."""
    if not isinstance(pressure, dict):
        return _TAPE_PRESSURE_ABSENT
    return "pressure: " + " · ".join(
        f"{label} {_TAPE_PRESSURE_DISPLAY.get(str(pressure.get(key)), 'n/a')}"
        for key, label in _TAPE_PRESSURE_COMPONENTS
    )


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
    *,
    operator_locked: bool = False,
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
    if operator_locked:
        monday_watch = f"Current regime reference: {posture}"
    elif posture in ("RISK_ON", "AGGRESSIVE_LONG", "CONTROLLED_LONG"):
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


def _render_level_ladder(
    w: object,
    now_price: float | None,
    contract_entry: float | None,
    fib_levels: dict | None,
    watch_zones: list | None,
    contract_stop: float | None = None,
    *,
    operator_locked: bool = False,
) -> None:
    """PRD-321 R4: the compact tiered level ladder — the setup chart's
    subordinate exact-level reference, and the honest fallback when no
    completed bars are available.

    This REPLACES the pre-PRD-321 full-size `_render_level_diagram` SVG
    (owner ruling Q3: the chart is the spatial representation, the ladder is
    the compact exact-level reference; no chart + old-ladder duplication).
    It shares the chart's tier hierarchy — Tier 1 strongest, Tier 2 clear,
    Tier 3 faint — and carries the same facts the old ladder carried:

    * PRD-216: every level label carries its dollar value.
    * PRD-221/PRD-222: NOW is the anchor (the live current price) and every
      other level carries its signed % distance from it.
    * PRD-223: the contract entry->stop span is the risk zone, rendered here
      as a bordered row group spanning exactly those levels.
    * PRD-226: NOW is `now_price`, never the contract entry; without a valid
      current price nothing is drawn (the caller gates; this is the
      belt-and-suspenders guard).
    * PRD-304: under operator lock the wording neutralizes (ENTRY -> LEVEL,
      STOP -> INVALIDATION) and no action colour class is emitted.

    Tier assignment mirrors `setup_chart`: EMA50 and fib retracements are
    Tier 3 context; the named intraday/trend structure levels are Tier 2.
    An unrecognised watch-zone type keeps its pre-PRD-321 structural weight
    (Tier 2) so the exact-level reference never silently drops a fact.
    """
    if now_price is None or not math.isfinite(now_price) or now_price <= 0:
        w('  <div class="lvl-unavail">Chart unavailable — no price data</div>')
        return
    anchor = float(now_price)

    entry_price: float | None = None
    if (
        contract_entry is not None
        and not isinstance(contract_entry, bool)
        and math.isfinite(contract_entry)
        and contract_entry > 0
    ):
        entry_price = float(contract_entry)

    # PRD-223/PRD-226: the risk band draws only from an honest contract pair —
    # a finite positive stop distinct from its own entry, never against NOW.
    stop_price: float | None = None
    if entry_price is not None and contract_stop is not None and not isinstance(contract_stop, bool):
        try:
            stop_candidate = float(contract_stop)
        except (TypeError, ValueError):
            stop_candidate = None
        if (
            stop_candidate is not None
            and math.isfinite(stop_candidate)
            and stop_candidate > 0
            and stop_candidate != entry_price
        ):
            stop_price = stop_candidate

    def _pct(level: float) -> str:
        return f" {((level - anchor) / anchor * 100.0):+.1f}%"

    # (price, tier, name, extra-class, pct-suffix)
    rows: list[tuple[float, str, str, str, str]] = []
    rows.append((anchor, "lvl-t1", "NOW", " lvl-now", ""))
    if entry_price is not None and abs(entry_price - anchor) >= 0.005:
        rows.append((
            entry_price, "lvl-t1",
            "LEVEL" if operator_locked else "ENTRY",
            " lvl-neutral" if operator_locked else " lvl-entry",
            _pct(entry_price),
        ))
    if stop_price is not None:
        rows.append((
            stop_price, "lvl-t1",
            "INVALIDATION" if operator_locked else "STOP",
            " lvl-neutral" if operator_locked else " lvl-stop",
            _pct(stop_price),
        ))

    for zone in (watch_zones or []):
        if not isinstance(zone, dict):
            continue
        level = zone.get("level")
        ztype = str(zone.get("type") or "")
        if level is None or isinstance(level, bool):
            continue
        try:
            level_f = float(level)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(level_f):
            continue
        tier = "lvl-t3" if ztype in setup_chart.TIER3_TYPES else "lvl-t2"
        extra = " lvl-vwap" if ztype == "VWAP" else ""
        rows.append((level_f, tier, _esc(ztype[:10]), extra, _pct(level_f)))

    if fib_levels and isinstance(fib_levels, dict):
        for label, value in (fib_levels.get("retracements") or {}).items():
            if value is None or isinstance(value, bool):
                continue
            try:
                level_f = float(value)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(level_f):
                continue
            rows.append((level_f, "lvl-t3", _esc(str(label)[:5]), "", _pct(level_f)))

    # Deterministic top-down order: highest price first, insertion order on ties.
    order = sorted(range(len(rows)), key=lambda i: (-rows[i][0], i))

    band: tuple[float, float] | None = None
    if entry_price is not None and stop_price is not None:
        band = (min(entry_price, stop_price), max(entry_price, stop_price))
    band_class = "lvl-lockrisk" if operator_locked else "lvl-inrisk"

    w(f'  <div class="lvl-ladder{" lvl-locked" if operator_locked else ""}">')
    in_band = False
    for idx in order:
        price, tier, name, extra, pct_text = rows[idx]
        if band is not None:
            inside = band[0] <= price <= band[1]
            if inside and not in_band:
                w(f'    <div class="lvl-riskband {band_class}">')
                in_band = True
            elif not inside and in_band:
                w("    </div>")
                in_band = False
        w(
            f'    <div class="lvl-row {tier}{extra}">'
            f'<span class="lvl-name">{name}</span>'
            f'<span class="lvl-px">{price:,.2f}</span>'
            f'<span class="lvl-pct">{pct_text.strip()}</span></div>'
        )
    if in_band:
        w("    </div>")
    w("  </div>")


def _render_setup_chart_block(
    w: object, svg: str, caption: str, *, disclosed: bool, open_when_disclosed: bool = False
) -> None:
    """PRD-321 R3 (ruling Q2): one full-width chart for the highest-priority
    visible setup; every other candidate's chart sits behind a NEW native
    `<details>` wrapper. That wrapper is orthogonal to the not-permitted
    `level-detail` wrapper — both apply per their own rules. PRD-329 R1: inside
    a CLOSED low tier the wrapper carries `open` (one tier tap reveals it)."""
    if disclosed:
        w(f'  <details{" open" if open_when_disclosed else ""} class="chart-detail"><summary>CHART ▶</summary>')
    w(f'  <div class="setup-chart">{svg}</div>')
    w(f'  <div class="chart-caption">{_esc(caption)}</div>')
    if disclosed:
        w("  </details>")


def _render_candidate_card(
    w: object, sym: str, entry: dict, contract_entry: float | None = None,
    contract_stop: float | None = None, operator_locked: bool = False,
    decision_permitted: bool = False,
    bars: list | None = None, bars_caption: str = "",
    chart_slot_available: bool = False,
    intraday_session: "intraday_bars.IntradaySession | None" = None,
    tier_closed: bool = False,
) -> bool:
    """Render one candidate card. Returns True when this card took the single
    full-width chart slot (PRD-321 R3 / ruling Q2).

    PRD-324 (A1-C): when this card holds the chart slot and an admitted
    ``intraday_session`` is supplied, its full-session 5m chart REPLACES the daily
    chart in that one slot (R9); every non-admitted state keeps the daily chart
    byte-identically (R11)."""
    # PRD-304 R7: under lock the card keeps every analytical observation (symbol,
    # grade letter, bias, structure, price/level context, invalidation content,
    # reasoning, watch) but omits the action directives IF NOW and PLAY and drops
    # the actionability accent class from the IN/OUT levels (neutral styling).
    grade = entry.get("grade") or ""
    css_class = _GRADE_CSS.get(grade, "unknown")
    _val_cls = "value-key" if operator_locked else "value-key value-actionable"
    # PRD-304 R7 (Sol finding 3): under lock the action-oriented IN →/OUT →
    # labels read as neutral observational labels (the level VALUES are
    # analytical and preserved).
    _in_label = "LEVEL" if operator_locked else "IN →"
    _out_label = "INVALIDATION" if operator_locked else "OUT →"
    is_high = grade in _HIGH_GRADES

    lifecycle: dict | None = entry.get("lifecycle")
    lc_tr = lifecycle.get("grade_transition") if lifecycle else None
    badge_css = _LIFECYCLE_BADGE_CSS.get(lc_tr) if lc_tr else None
    badge_html = f'<span class="lifecycle-badge {badge_css}">{_esc(lc_tr)}</span>' if badge_css else ""

    _observation_class = "" if decision_permitted else " candidate-observation"
    w(f'<div class="candidate-card grade-{css_class}{_observation_class}" id="card-{_esc(sym)}">')

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
        w(f'  <div class="label">SCREENING NOTE</div><div class="value">{_fail_text}</div>')
    else:
        # PRD-249: collapse the 8-line stacked identity block (SYMBOL/GRADE/BIAS/
        # STRUCTURE label-over-value pairs) into one header line:
        #   SYMBOL · GRADE · [STATE ·] BIAS STRUCTURE
        # GRADE is the letter grade (the tier header already carries the action
        # word); STATE is setup_state and now lives ONLY here — the standalone
        # STATE line below is removed, not the datum. The lifecycle badge rides
        # the header (previously on the GRADE value).
        setup_state = entry.get("setup_state")
        header_bits = [_esc(entry.get("symbol")), _esc(grade)]
        if setup_state and setup_state != "DATA_UNAVAILABLE":
            header_bits.append(_esc(setup_state))
        bias_structure = " ".join(
            p for p in (_esc(entry.get("bias")), _esc(entry.get("structure"))) if p
        )
        if bias_structure:
            header_bits.append(bias_structure)
        header = " · ".join(b for b in header_bits if b)
        w(f'  <div class="card-header">{header}{badge_html}</div>')

    if is_high:
        tf: dict = entry.get("trade_framing") or {}

        # PRD-249: the verdict is the card's headline answer — render it first,
        # immediately under the header, not buried below the identity/lifecycle.
        if_now = tf.get("if_now")
        # Change #4: IF NOW / IN / OUT couplets share ONE kv-grid so their labels
        # form one aligned column; the lifecycle line spans both columns so the
        # couplet labels stay aligned across it (no couplet reorder).
        w('  <div class="kv-grid card-brief">')
        if if_now is not None and not operator_locked:  # PRD-304 R7: action directive omitted under lock
            w(f'  <div class="label">IF NOW</div><div class="value">{_esc(if_now)}</div>')

        # PRD-249: render the lifecycle line only on a REAL transition. A no-op
        # (grade AND setup_state both unchanged, e.g. "B → B | DEVELOPING →
        # DEVELOPING") is noise and is suppressed; the badge already suppresses
        # UNCHANGED via _LIFECYCLE_BADGE_CSS.
        if lifecycle:
            prev_g = lifecycle.get("previous_grade")
            cur_g = lifecycle.get("current_grade")
            prev_s = lifecycle.get("previous_setup_state")
            cur_s = lifecycle.get("current_setup_state")
            if prev_g != cur_g or prev_s != cur_s:
                pg = _esc(prev_g) or _DASH
                cg = _esc(cur_g) or _DASH
                ps = _esc(prev_s) or _DASH
                cs = _esc(cur_s) or _DASH
                w(f'  <div class="lifecycle-detail">LIFECYCLE: {pg} → {cg} | {ps} → {cs}</div>')

        # PRD-165 R1 / PRD-215 / PRD-249: the falsifiable in/out couplet is the
        # visual focus — bold (.value-key) + cyan actionable accent
        # (.value-actionable). PRD-249 relabels ENTRY→"IN →" and
        # INVALIDATION→"OUT →" (one couplet) and drops the standalone RISK line.
        entry_val = tf.get("entry")
        if entry_val is not None:
            w(f'  <div class="label">{_in_label}</div><div class="{_val_cls}">{_esc(entry_val)}</div>')

        # PRD-249 review advisory: trade_framing.downgrade restated the
        # invalidation's PRICE clause but carried one extra clause the couplet
        # does not express — the structural-invalidation path (the part after
        # " or ", e.g. "structure turns choppy"). Fold ONLY that non-redundant
        # clause into OUT so dropping the RISK line loses no data. This is a
        # presentation-only compose: read both existing fields (invalidation and
        # downgrade), join for display, verbatim — derive nothing, add no wording.
        invalidation = entry.get("invalidation")
        if invalidation and len(invalidation) > 0 and invalidation[0] is not None:
            out_text = _esc(invalidation[0])
            downgrade = tf.get("downgrade")
            if downgrade and " or " in downgrade:
                structural = downgrade.split(" or ", 1)[1].strip()
                if structural and structural not in invalidation[0]:
                    out_text = f"{out_text}, or {_esc(structural)}"
            w(f'  <div class="label">{_out_label}</div><div class="{_val_cls}">{out_text}</div>')
        w('  </div>')

        # PRD-215/PRD-249: REASON/PLAY/WATCH are supporting context — tuck them
        # behind a default-collapsed disclosure so the accented couplet stays the
        # focal point. WATCH is now ONE semicolon-joined line under one label
        # instead of one label per what_to_look_for item.
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
            if pts is not None and not operator_locked:  # PRD-304 R7: PLAY directive omitted under lock
                w(f'  <div class="label">PLAY</div><div class="value">{_esc(pts)}</div>')
            if _watch_items:
                _watch_joined = "; ".join(_esc(item) for item in _watch_items)
                w(f'  <div class="label">WATCH</div><div class="value">{_watch_joined}</div>')
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
    took_chart_slot = False
    if now_valid and has_level_context:
        # PRD-223: the risk band needs the contract pair — a stop only draws
        # against its own entry, never against the NOW/current-price anchor.
        # This gate also carries contract staleness: a stale contract nulls
        # the entry map, so its stop can never pair up and draw.
        band_stop = contract_stop if entry_valid else None
        # PRD-324 (A1-C R8/R9): when this card holds the chart slot and an admitted
        # intraday 5m session exists, its full-session chart (`max_bars=None`)
        # REPLACES the daily chart in this one slot. Every non-admitted state -- no
        # session, or an empty intraday SVG -- falls through to the untouched daily
        # branch below byte-identically (R11).
        # PRD-326 R3: the single canonical primary-slot chart is observational and
        # renders undisclosed in every decision state, so on a non-permitted
        # render it takes the existing lock presentation (LEVEL / INVALIDATION,
        # grey). Chart-only: every other card has `chart_slot_available=False`,
        # so this equals `operator_locked` there; the ladder and every directive
        # stay keyed on `operator_locked` alone (R2).
        chart_neutral = operator_locked or (chart_slot_available and not decision_permitted)
        chart_svg = ""
        chart_caption = bars_caption
        if chart_slot_available and intraday_session is not None:
            chart_svg = setup_chart.render_setup_chart_svg(
                intraday_session.candles,
                now_price,
                contract_entry=contract_entry if entry_valid else None,
                contract_stop=band_stop,
                watch_zones=watch_zones,
                fib_levels=fib_levels,
                operator_locked=chart_neutral,
                max_bars=None,
            )
            if chart_svg:
                chart_caption = intraday_session.caption
        # PRD-321 R1/R2: the daily chart draws only from completed bars that passed
        # the loader's age guard; an empty SVG means "nothing honest to draw" and
        # the card degrades to the compact ladder alone (R4).
        if not chart_svg:
            chart_svg = setup_chart.render_setup_chart_svg(
                bars,
                now_price,
                contract_entry=contract_entry if entry_valid else None,
                contract_stop=band_stop,
                watch_zones=watch_zones,
                fib_levels=fib_levels,
                operator_locked=chart_neutral,
            ) if bars else ""
        if chart_svg:
            took_chart_slot = bool(chart_slot_available)
        # PRD-326 R1 (PRD-321 R3 / PRD-318 R4 superseded in part): the primary-slot
        # chart is emitted BEFORE the decision-state-keyed `level-detail` wrapper,
        # undisclosed in every decision state; every other card's chart stays
        # inside that wrapper behind `chart-detail` (R2). No placeholder (R4).
        if took_chart_slot:
            _render_setup_chart_block(
                w, chart_svg, chart_caption, disclosed=not took_chart_slot
            )
        # PRD-329 R1 (S1-Q1): inside a CLOSED low tier both nested disclosures
        # carry `open`, so the operator's single tier tap shows card + LEVEL MAP +
        # CHART; open tiers and A+/A/B cards keep today's closed wrappers (R2).
        if not decision_permitted:
            w(f'  <details{" open" if tier_closed else ""} class="level-detail"><summary>LEVEL MAP ▶</summary>')
        if chart_svg and not took_chart_slot:
            _render_setup_chart_block(
                w, chart_svg, chart_caption, disclosed=not took_chart_slot,
                open_when_disclosed=tier_closed,
            )
        # PRD-321 R4: the compact ladder is the chart's subordinate exact-level
        # reference (rendered directly below it) AND the full fallback when no
        # bars are available. Both roles carry every authority semantic.
        _render_level_ladder(
            w,
            now_price,
            contract_entry if entry_valid else None,
            fib_levels,
            watch_zones,
            contract_stop=band_stop,
            operator_locked=operator_locked,
        )
        if not decision_permitted:
            w("  </details>")

    w("</div>")
    return took_chart_slot


def _render_spy_session(
    w: object, spy_obs: dict, spy_bars: tuple | None, spy_record: object,
    mm_health: str, unhealthy_lineage: bool, mm_clock_label: str,
) -> None:
    """PRD-329 S2 (R4-R8): the `#spy-observation` subtree — the PRD-288 rows
    (bytes unchanged), then a NEUTRAL SPY daily-bar chart and a NEUTRAL level
    ladder from the SPY market-map record. A pure function of these
    observational inputs: no decision, permission, ranking or contract state
    is read (R7). Resolution ladder (R5): map unhealthy -> one line; no SPY
    record -> one line; invalid price -> the ladder's no-price line; no bars ->
    the no-bars line plus the ladder; else chart + caption + ladder. Three
    clocks stay named: OBSERVED AT (session), bars `as_of` (daily), NOW (map)."""
    _line1, _line2 = _spy_session_lines(spy_obs)
    _raw_reason = spy_obs.get("reason")
    w('<div class="block" id="spy-observation">')
    w(f'  <div class="spy-read" data-raw-state="{_esc(str(spy_obs.get("state") or "UNAVAILABLE"))}"'
      f' data-observed-at-utc="{_esc(str(spy_obs.get("observed_at_utc") or ""))}"'
      f' data-session-date="{_esc(str(spy_obs.get("intended_session_date") or ""))}"'
      + (f' data-raw-reason="{_esc(str(_raw_reason))}"' if _raw_reason else "") + f'>{_esc(_line1)}</div>')
    w(f'  <div class="spy-read">{_line2}</div>')
    if mm_health != "OK" or unhealthy_lineage:
        w(f'  <div class="lvl-unavail">Chart and levels unavailable — market map {_esc(mm_health)}</div>')
    elif not isinstance(spy_record, dict):
        w('  <div class="lvl-unavail">Chart and levels unavailable — market map no SPY record</div>')
    else:
        now_price = spy_record.get("current_price")
        zones, fibs = spy_record.get("watch_zones"), spy_record.get("fib_levels")
        price_valid = (isinstance(now_price, (int, float)) and not isinstance(now_price, bool)
                       and math.isfinite(now_price) and now_price > 0)
        if price_valid:
            bars, caption = spy_bars if spy_bars else (None, "")
            svg = setup_chart.render_setup_chart_svg(
                bars, now_price, contract_entry=None, contract_stop=None,
                watch_zones=zones, fib_levels=fibs, operator_locked=False, layers=("levels",),
            ) if bars else ""
            if svg:
                w(f'  <div class="spy-clock">{_esc(_spy_clock_line(mm_clock_label, spy_obs.get("intended_session_date"), caption))}</div>')
                _cid, _clabel = _LAYER_CONTROLS["levels"]
                w(f'  <input type="checkbox" id="{_cid}" class="chart-toggle">')
                w(f'  <div class="chart-controls"><label for="{_cid}" class="chart-toggle-label">{_clabel}</label></div>')
                w(f'  <div class="spy-chart">{svg}</div>')
            else:
                w('  <div class="lvl-unavail">Chart unavailable — no bars for SPY</div>')
        _render_level_ladder(w, now_price if price_valid else None, None, fibs, zones, None,
                             operator_locked=False)
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
    gex_snapshot: dict | None = None,
    movement_snapshot: dict | None = None,
    price_bars_snapshot: dict | None = None,
    now: datetime | None = None,
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
    # PRD-304 R7: the operator lock is visible in the existing permission field.
    # Under lock the dashboard keeps all analytical observations but replaces
    # every permission/action vocabulary token (see the OPERATOR LOCK marker,
    # A+ — OBSERVATION ONLY, SETUPS FOUND, and the suppressed IF NOW/PLAY/accents
    # below). A system halt keeps its own permission string, so this is False then.
    operator_locked = permission == config.OPERATOR_LOCK_PERMISSION
    title = "MIXED_ARTIFACTS" if artifact_mixed else _decision_title(outcome, bool(system_halted), status)

    # R1 — tape slots
    tape_slots = _build_tape_slots(macro_drivers)
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
    _verdict_lines: list[str] = []
    _tape_lines: list[str] = []
    _spy_lines: list[str] = []
    _today_lines: list[str] = []
    _watching_lines: list[str] = []
    _details_lines: list[str] = []
    _active_lines = lines

    def w(line: str) -> None:
        _active_lines.append(line)

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

    # --- VERDICT: the sole top-level permission/decision surface. ---
    _active_lines = _verdict_lines
    w('<div class="block operator-zone" id="verdict-zone">')
    if artifact_mixed:
        w('<div class="verdict-warning" id="artifact-coherence" data-raw-state="MIXED_ARTIFACTS">')
        w('  <div class="value-key">Inputs are out of sync</div>')
        w('  <div class="value">Dashboard inputs are from different artifact generations.</div>')
        if generation_ids_mixed:
            w(
                '  <div class="zone-note">'
                f"payload={_esc(payload_generation_id or 'unavailable')} "
                f"run={_esc(run_generation_id or 'unavailable')} "
                f"market_map={_esc(market_map_generation_id or 'unavailable')}"
                "</div>"
            )
        w("</div>")

    # PRD-250 freshness remains client-clocked and safety-visible, but is now a
    # compact treatment inside the authoritative card instead of a peer card.
    w(f'<div class="block" id="staleness-banner" hidden'
      f' style="text-align:center;font-weight:bold"'
      f' data-session-inactive="{"true" if inactive_session else "false"}"'
      f' data-board-stale-after-s="{BOARD_STALE_AFTER_SECONDS}"></div>')
    w(f'<script>{_STALENESS_BANNER_JS}</script>')
    w('<div class="block operator-subsection" id="system-state">')
    w('  <h2>VERDICT</h2>')

    # PRD-312's five independent facts are redistributed without changing their
    # sources: environment+permission here, positioning+participation in TAPE,
    # and event risk in TODAY. No peer MARKET STATE card remains.
    _ms_gex_card = (
        gex_card.build_gex_card(gex_snapshot, now=now if now is not None else _utcnow())
        if gex_snapshot is not None else None
    )
    _ms_movement_card = (
        movement_card.build_movement_card(movement_snapshot)
        if movement_snapshot is not None else None
    )
    # --- existing SYSTEM STATE authority, now presented as VERDICT ---
    regime_permission_text = _regime_to_permission_verb(market_regime)
    # PRD-219: distilled system-state — a plain-English verdict (posture verb +
    # decision title, coloured by regime), one context line (regime + the
    # trader-facing reason), and one absolute timestamp. Replaces the
    # REGIME/OUTCOME/PERMISSION grep and the three relative freshness lines. The
    # decision title stays inside the verdict, so the decision-title contract is
    # unchanged. Halt is unmistakable (red verdict, title carries SYSTEM HALT).
    # PRD-280: derive the halt color from the already-authoritative `title`
    # in addition to `system_halted` (not `system_halted` alone) --
    # _decision_title also returns SYSTEM HALT for status=FAIL/ERROR, which
    # system_halted-only coloring missed. `bool(system_halted)` is ORed in,
    # not replaced: when artifact_mixed=True, `title` is overridden to
    # "MIXED_ARTIFACTS" (Codex correction) even if the underlying run is
    # genuinely halted, so title alone would silently lose the halt color
    # for that overlap. Wrapped like PRD-279's R2: an unexpected comparison
    # error must not crash the render -- fall back to the neutral class.
    try:
        _verdict_cls = "sys-halt" if (bool(system_halted) or title == "SYSTEM HALT") else _SYS_VERDICT_CLS.get(
            str(market_regime), "sys-flat"
        )
    except Exception:
        _verdict_cls = "sys-flat"
    # PRD-279: Decision State Header -- a prominent three-word label derived
    # from the same `title` already computed above (_decision_title), never
    # independently recomputed. Falls back to STATE UNAVAILABLE rather than
    # ever propagating, and never infers TRADE PERMITTED from the absence
    # of HALT (it requires _decision_title's own "TRADE SETUP ACTIVE").
    try:
        if title == "MIXED_ARTIFACTS":
            # PRD-279 (Codex correction): a lineage mismatch is a data-
            # integrity error, not a coherent STAY FLAT decision -- never
            # present a confident-looking state over untrustworthy data.
            _decision_state, _decision_state_cls = "STATE UNAVAILABLE", "sys-flat"
        elif title == "SYSTEM HALT":
            _decision_state, _decision_state_cls = "HALT", _verdict_cls
        elif title == "TRADE SETUP ACTIVE":
            _decision_state, _decision_state_cls = "TRADE PERMITTED", _verdict_cls
        else:
            _decision_state, _decision_state_cls = "STAY FLAT", _verdict_cls
    except Exception:
        _decision_state, _decision_state_cls = "STATE UNAVAILABLE", "sys-flat"
    # PRD-304 R7: under the operator lock, the decision-state and the permission
    # verb both carry the lock marker instead of any trade-permission vocabulary.
    if operator_locked:
        _decision_state = "OBSERVE ONLY"
    try:
        _title_display = "INPUTS OUT OF SYNC" if title == "MIXED_ARTIFACTS" else title
    except Exception:
        _title_display = "STATE UNAVAILABLE"
    _verb_text = "Operator locked: cannot monitor" if operator_locked else regime_permission_text
    w(f'  <div class="decision-state {_decision_state_cls}">{_esc(_decision_state)}</div>')
    w(f'  <div class="sys-verdict {_verdict_cls}" data-raw-title="{_esc(title)}">'
      f'{_esc(_verb_text)} · {_esc(_title_display)}</div>')
    # Context line: regime in plain words. PRD-281: the trader-facing reason
    # ("why") moved to its own dedicated .sys-why line below.
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
    # PRD-283 (CB-02): count options-sizing refusals from the payload so the WHY
    # line names them instead of "no qualified setups" or "gated" — a refused
    # setup qualified (so it may be high-grade in the market map) but was refused
    # because its smallest contract exceeds the budget. Without this the WHY line
    # contradicts the Opportunity Survival Summary, which already counts it.
    _sizing_refusal_n = 0
    _why_sections = payload.get("sections") or {}
    _why_rejected = _why_sections.get("rejected")
    if isinstance(_why_rejected, list):
        _sizing_refusal_n = sum(
            1 for _r in _why_rejected
            if isinstance(_r, dict) and _r.get("stage") == "OPTIONS_SIZING"
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
        # PRD-283: an options-sizing refusal is the precise cause and takes
        # precedence — a refused setup may still be high-grade, so "gated" and
        # "no qualified setups" would both be wrong here.
        if _sizing_refusal_n > 0:
            _ctx_reason = (
                f"{_sizing_refusal_n} setup{'s' if _sizing_refusal_n != 1 else ''} "
                f"refused: contract exceeds risk budget"
            )
        elif _hg_count > 0:
            _ctx_reason = f"{_hg_count} setup{'s' if _hg_count != 1 else ''} gated"
        elif alert_candidates:
            _ctx_reason = "candidates gated"
        else:
            _ctx_reason = "no qualified setups"
    else:
        _ctx_reason = None
    # R2/PRD-281 R4: never surface raw engine internals (regime=…,
    # confidence=…) or a literal None/NULL sentinel. Each pattern is
    # stripped independently of the other -- a bare "confidence=0.25" with
    # no "(regime=" wrapper, or vice versa, must not survive either -- and a
    # reason that collapses to nothing (or IS the sentinel, before or after
    # stripping -- e.g. "None (regime=RISK_OFF, confidence=0.25)" strips down
    # to bare "None") is treated as no reason, not rendered as an empty/raw
    # WHY line. The sentinel check runs both before AND after stripping.
    if _ctx_reason:
        _reason_str = str(_ctx_reason).strip()
        if _reason_str not in ("None", "NULL"):
            _reason_str = re.sub(r"\s*\(?\s*regime=.*", "", _reason_str)
            _reason_str = re.sub(r"\s*\(?\s*confidence=.*", "", _reason_str)
            _reason_str = _reason_str.strip()
        _ctx_reason = None if _reason_str in ("None", "NULL", "") else _reason_str
    # PRD-281: the reason renders exactly once, in the dedicated WHY line
    # below -- never appended to the regime context line (superseding, for
    # this one display, PRD-219's "folds into the context line" choice).
    # Shown only for HALT / STAY FLAT with a computable reason; TRADE
    # PERMITTED needs no reason, and STATE UNAVAILABLE (including mixed
    # artifacts) must never pair a confident-looking reason with an
    # untrustworthy or unresolved decision state.
    if _ctx_reason and _decision_state in ("HALT", "STAY FLAT"):
        w(f'  <div class="sys-why">WHY: {_esc(str(_ctx_reason))}</div>')
    _ctx = _esc(_regime_plain) + " regime"
    _ctx_cls = " halted" if bool(system_halted) else ""
    w(f'  <div class="sys-context{_ctx_cls}">{_ctx}</div>')
    if bool(kill_switch):
        w('  <div class="sys-context halted">Kill switch active</div>')
    if isinstance(permission, str) and permission.strip():
        w(f'  <div class="sys-permission">{_esc(permission)}</div>')
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
    # PRD-250: machine-readable UTC form of the same timestamp the display uses,
    # for the client-side staleness banner. Mirrors the display fallback
    # (pipeline run first, then payload). Emitted into HTML output ONLY — no
    # contract/payload write; both operands are already-parsed datetimes in hand.
    _updated_dt = _pipeline_run_ts or payload_timestamp
    _updated_iso = _updated_dt.isoformat() if _updated_dt is not None else ""
    _updated_display = _operator_timestamp(
        _pipeline_run_ts or payload_timestamp_value or timestamp or ""
    )
    w(f'  <div class="value" id="cb-updated" data-updated-utc="{_esc(_updated_iso)}">'
      f'Updated {_esc(_updated_display)}</div>')
    w("</div>")  # #system-state
    w("</div>")  # #verdict-zone

    # --- TAPE: display-only adjacency over values already loaded above. ---
    _active_lines = _tape_lines
    # PRD-322: two labeled bands (MACRO, TREND) over the same render-body
    # values, then a subordinate footer carrying the positioning/participation
    # availability rows. Every token is a projection of an already-loaded fact.
    w('<div class="block operator-zone" id="tape-zone">')
    w('  <h2>TAPE <span class="label">context only</span></h2>')
    w('  <div class="tape-band">')
    w('    <div class="tape-band-cap">MACRO</div>')
    _total_votes = long_votes + short_votes
    _votes_suffix = f" · {long_votes} on / {short_votes} off" if _total_votes else ""
    # PRD-322 R2: MISSING means the driver payload is empty or unavailable, so
    # the zero-vote tie below would fabricate "MACRO BIAS: MIXED". FALLBACK
    # must NOT trip this gate — it also fires on missing tradables under a
    # genuine, fully-voted macro bias.
    if _tape_health == "MISSING":
        _macro_html = _esc(_TAPE_MACRO_ABSENT)
    else:
        # Change #3: colour ONLY the direction token (LONG/SHORT/MIXED) via
        # .tape-bias (existing palette; NOT .macro-bias, which adds weight and
        # margin). The "MACRO BIAS:" label and the vote suffix stay muted.
        _bias_prefix, _bias_sep, _bias_token = macro_bias.partition(": ")
        if _bias_sep:
            _macro_html = (
                f'{_esc(_bias_prefix)}: '
                f'<span class="tape-bias {_esc(macro_bias_css.split()[-1])}">'
                f'{_esc(_bias_token)}</span>{_esc(_votes_suffix)}'
            )
        else:
            _macro_html = _esc(macro_bias) + _esc(_votes_suffix)
    if not integrator_suppress["macro_bias"]:
        w(f'    <div class="zone-value">{_macro_html}</div>')
    _tape_values = dict(tape_value_slots)
    _tape_arrows = dict(tape_slots)
    # PRD-322 R3: all seven macro drivers, data-driven from the shared layout
    # rows. Deliberately NOT `macro-tape-slot` / `macro-tape-value` /
    # `data-symbol` — those are regex-harvested and order-pinned in DETAILS.
    # Codex F3: the strip normalizes the DETAILS-side "N/A" absent-metal
    # placeholder to the strip's uniform "--"; the shared projection is untouched.
    _strip_values = {k: ("--" if v == "N/A" else v) for k, v in _tape_values.items()}
    _driver_cells = [
        f'<div class="tape-driver tape-slot '
        f'{_ARROW_CSS.get(_tape_arrows.get(slot.label, _DASH), "na")}">'
        f'<span>{_esc(slot.display)}</span>'
        f'<span>{_esc(_tape_arrows.get(slot.label, _DASH))}</span>'
        f'<span>{_esc(_strip_values.get(slot.label, _DASH))}</span></div>'
        for _row in (MACRO_ROW_2, MACRO_ROW_1)
        for slot in _row.slots
    ]
    w('    <div class="tape-drivers">' + "".join(_driver_cells) + "</div>")
    w(f'    <div class="zone-note">{_esc(_pressure_note(pressure))}</div>')
    w('  </div>')
    w('  <div class="tape-band">')
    w('    <div class="tape-band-cap">TREND</div>')
    _trend_summary, _trend_derivation = _tape_trend_summary(_ts_records, _ts_health)
    _trend_rows = _build_trend_chips(_ts_records)
    w(f'    <div class="zone-value" data-derivation="{_esc(_trend_derivation)}">'
      f'{_esc(_trend_summary)}</div>')
    _trend_cells = [
        f'<div class="tape-trend-row tape-slot {_cls}">'
        f'<span>{_esc(_sym)}</span><span>{_esc(_align)}</span>'
        f'<span>{_esc(_c50)}</span><span>{_esc(_c200)}</span>'
        f'<span>{_esc(_vwap)}</span></div>'
        for _sym, _align, _c50, _c200, _vwap, _cls in _trend_rows
    ]
    # PRD-327 D2-Q2 (Helm ruling 2026-09-01): the six placeholder chips leave
    # the fold only when zero rows are computed under healthy lineage in an
    # active session -- exactly the branch where the unchanged DETAILS
    # #trend-structure table enumerates the curated symbols. Any computed
    # row, unhealthy lineage or inactive session keeps all six chips (PRD-322 R4).
    _chips_visible = (
        any(_cls in _TAPE_ALIGN_CSS.values() for *_row, _cls in _trend_rows)
        or unhealthy_lineage
        or inactive_session
    )
    if _chips_visible:
        w('    <div class="tape-trend">' + "".join(_trend_cells) + "</div>")
    w('  </div>')
    # PRD-322 R5: absence is stated, never silent. Both rows keep one shape
    # across present/absent so the GEX decision-invariance regex strips exactly
    # one row from each document.
    w('  <div class="zone-grid tape-foot">')
    if _ms_gex_card is not None:
        _gex_b = _ms_gex_card.net_usd / 1e9
        _gex_net = f"{'-' if _gex_b < 0 else '+'}${abs(_gex_b):.1f}B net"
        w('    <div class="zone-item"><div class="label">GEX · CONTEXT ONLY</div>'
          f'<div class="zone-value">{_esc(_gex_net)}</div>'
          f'<div class="zone-note">as of {_esc(_ms_gex_card.as_of_et)} ET · Cboe ~15m delayed · positioning not measured</div></div>')
    else:
        w('    <div class="zone-item"><div class="label">GEX · CONTEXT ONLY</div>'
          '<div class="zone-value">unavailable</div></div>')
    if _ms_movement_card is not None:
        _movement_chips = [
            chip for _group, _chips in _ms_movement_card.groups for chip in _chips
        ]
        _movement_usable = sum(1 for _chip in _movement_chips if not _chip.endswith(" n/a"))
        w('    <div class="zone-item"><div class="label">PARTICIPATION</div>'
          f'<div class="zone-value">{_movement_usable}/{len(_movement_chips)} captured</div>'
          f'<div class="zone-note">captured {_esc(_ms_movement_card.captured_et)} ET</div></div>')
    else:
        w('    <div class="zone-item"><div class="label">PARTICIPATION</div>'
          '<div class="zone-value">not captured</div></div>')
    w('  </div>')
    w("</div>")

    # --- SPY SESSION (PRD-330 S1): observational orientation between TAPE and NEXT EVENT. ---
    _spy_obs = (payload.get("sections") or {}).get("spy_observation")
    _now_effective = now if now is not None else _utcnow()
    _price_bars = _price_bars_by_symbol(price_bars_snapshot, _now_effective)
    if _spy_obs:
        _active_lines = _spy_lines
        _spy_symbols = (market_map or {}).get("symbols")
        w('<section class="spy-session-group" id="spy-session">')
        w('  <h3>SPY SESSION</h3>')
        _render_spy_session(
            w, _spy_obs, _price_bars.get("SPY"),
            _spy_symbols.get("SPY") if isinstance(_spy_symbols, dict) else None,
            _mm_health, unhealthy_lineage,
            _timestamp_label(market_map_timestamp_value, market_map_timestamp),
        )
        w("</section>")

    # --- NEXT EVENT (PRD-330 S3): the named next event, honest empty states, Sunday. ---
    _active_lines = _today_lines
    w('<div class="block operator-zone" id="today-zone">')
    w('  <h2>NEXT EVENT</h2>')
    w(f'  <div class="event-line">{_esc(_next_event_line(red_folder))}</div>')
    if sunday_coherent:
        w('  <div class="zone-item" id="premarket-banner"><div class="label">SESSION</div>'
          '<div class="zone-value">SUNDAY PRE-MARKET CONTEXT · no cash session</div></div>')
    w("</div>")

    # --- WATCHING: Opportunity -> Candidate -> alert continuity. ---
    _active_lines = _watching_lines
    w('<div class="block operator-zone" id="watching-zone">')
    w('  <h2>WATCHING</h2>')

    # --- opportunity-survival (PRD-282) ---
    # Trader-facing survival funnel: how many symbols were surfaced, how many
    # survived to qualified, how many were watchlisted, how many rejected --
    # plus the single most common terminal rejection reason. Every value is read
    # from data already present in the payload at the renderer; no new schema,
    # contract, or taxonomy (GOV-2 NOT MATERIAL).
    #
    # Fail closed (PRD-282 correction F2): render only over a coherent lineage,
    # a real integer scan (bool is an int subclass -- exclude it), and
    # well-formed survival inputs. The render path does not re-run
    # assert_valid_payload, so a corrupted/partial payload can reach here;
    # malformed shapes suppress the whole block rather than crash, count a
    # string's length, accept True as 1, or show misleading partial counts.
    _os_meta = payload.get("meta") or {}
    _os_surfaced = _os_meta.get("symbols_scanned")
    _os_sections = payload.get("sections") or {}
    _os_rejected_all = _os_sections.get("rejected")
    _os_watchlist = _os_sections.get("watchlist")
    _os_valid = (
        not unhealthy_lineage
        and isinstance(_os_surfaced, int)
        and not isinstance(_os_surfaced, bool)
        and _os_surfaced > 0
        and isinstance(_os_rejected_all, list)
        and isinstance(_os_watchlist, list)
        and all(isinstance(_r, dict) for _r in _os_rejected_all)
    )
    if _os_valid:
        # PRD-260 R4 (correction F1): a CONTINUATION-promoted symbol keeps its
        # DIRECT rejection on the audit trail (reason rewritten to include
        # "promoted via CONTINUATION", cuttingboard/qualification.py) AND counts
        # as qualified -- so it appears in BOTH excluded and qualified, double-
        # counting it in symbols_scanned and seeding a non-terminal rejection
        # record. "promoted via CONTINUATION" is the pipeline's own authoritative
        # marker: use it to drop these audit records from REJECTED and the
        # primary reason, and to remove the double-count from SURFACED, so each
        # symbol is represented exactly once (the promoted one as qualified).
        _os_rejected = [
            _r for _r in _os_rejected_all
            if "promoted via CONTINUATION" not in str(_r.get("reason") or "")
        ]
        _os_promoted_n = len(_os_rejected_all) - len(_os_rejected)
        _os_surfaced_n = _os_surfaced - _os_promoted_n
        _os_rejected_n = len(_os_rejected)
        _os_watchlist_n = len(_os_watchlist)
        # QUALIFIED is the derived remainder. With the promotion double-count
        # removed and the scan>0 gate excluding the REGIME short-circuit (the
        # only other non-QUALIFICATION rejection path, which forces
        # symbols_scanned == 0), this equals the upstream qualified_count
        # exactly -- the inverse of symbols_scanned's own definition, not a
        # divergent proxy (PRD-198 invariant 3). The clamp guards an already-
        # excluded state.
        _os_qualified_n = max(0, _os_surfaced_n - _os_rejected_n - _os_watchlist_n)
        # Primary rejection reason: the mode of the pipeline's own terminal
        # `reason` strings (not a new taxonomy), with engine internals stripped
        # by the same policy as the system-state WHY line above
        # (regime=/confidence= suffixes and None/NULL sentinels) so no raw
        # internal leaks, then HTML-escaped at render. Deterministic tie-break:
        # highest count, then lexicographically smallest reason.
        _os_primary = None
        if _os_rejected_n > 0:
            _os_tally: dict[str, int] = {}
            for _r in _os_rejected:
                _reason = _r.get("reason")
                if not _reason:
                    continue
                _clean = str(_reason).strip()
                _clean = re.sub(r"\s*\(?\s*regime=.*", "", _clean)
                _clean = re.sub(r"\s*\(?\s*confidence=.*", "", _clean)
                _clean = _clean.strip()
                if _clean and _clean not in ("None", "NULL"):
                    _os_tally[_clean] = _os_tally.get(_clean, 0) + 1
            if _os_tally:
                _os_primary = sorted(
                    _os_tally.items(), key=lambda kv: (-kv[1], kv[0])
                )[0][0]
        # PRD-330 R5 (D-7): one line; counts unchanged; zero qualified omitted; closed reason policy.
        _os_all_cutoff = _os_watchlist_n > 0 and all(
            isinstance(_w, dict) and str(_w.get("reason") or "") == _WATCHLIST_CUTOFF_REASON for _w in _os_watchlist)
        _os_parts = [f"{_os_surfaced_n} screened",
                     f"{_os_watchlist_n} held by the 3:30 PM cutoff" if _os_all_cutoff else f"{_os_watchlist_n} on watch"]
        if _os_qualified_n > 0:
            _os_parts.append(f"{_os_qualified_n} {'setups found' if operator_locked else 'qualified'}")
        _os_parts.append(f"{_os_rejected_n} rejected")
        if _os_primary is not None:
            _os_parts.append(f"top reason {_esc(_os_primary)} ({_os_tally[_os_primary]})")
        w(f'  <p class="screen-line">{" · ".join(_os_parts)}</p>')

    # --- alert-watchlist (PRD-332 D5: relocated ABOVE the candidate board so
    # MANUAL CHECK is never hidden by setup selection; the block's inner markup
    # is byte-identical to PRD-331 -- only its position moves). ---
    _manual_check_syms: set[str] = set()
    if alert_candidates:
        w('<div class="block operator-subsection" id="alert-watchlist">')
        w('  <h3>ALERT WATCHLIST</h3>')
        w('  <div class="label">Candidates gated by execution policy</div>')
        for cand in alert_candidates:
            sym = _esc(str(cand.get("symbol") or "").upper())
            direction = _esc(str(cand.get("direction") or "").upper())
            block_reason = _esc(str(cand.get("block_reason") or "").upper())
            _tail = f'{sym} {direction}' + (f' — {block_reason}' if block_reason else '') + '</div>'
            # PRD-331: presentation-only manual-action flag, keyed on the contract's
            # verbatim chain classification (setup_quality). No value is derived, no
            # row is reordered; every non-manual row is byte-identical to before.
            if cand.get("setup_quality") == MANUAL_CHECK:
                _manual_check_syms.add(str(cand.get("symbol") or "").upper())
                w('  <div class="candidate-state manual-check" data-raw-state="NEEDS_MANUAL_CHECK">'
                  '<span class="manual-check-flag">MANUAL CHECK</span> ' + _tail)
            else:
                w('  <div class="candidate-state">' + _tail)
        w("</div>")

    # --- candidate-board ---
    # PRD-321 R2/R3: resolve the age-guarded bars once per render, and keep the
    # single full-width chart slot for the highest-priority visible setup —
    # every later candidate's chart goes behind its own disclosure (ruling Q2).
    # PRD-324 (A1-C R6): the single chart slot is awarded ONCE, by the shared leaf,
    # over the byte-identical runtime inputs the inline `_chart_slot_open` latch
    # consumed (post-fixture-replacement `market_map`, `_price_bars`,
    # `integrator_skips`). The card whose symbol equals this result takes the slot;
    # the deleted latch is replaced by an equality check at the call site (R6).
    _primary_card_symbol = select_primary_card_symbol(
        market_map, _price_bars, integrator_skips
    )
    # PRD-324 (A1-C R1/R2/R3): load the A1-P intraday sidecar and derive the
    # admitted completed-5m session for the primary; None => the daily chart stays.
    _intraday_session = intraday_bars.derive_intraday_session(
        _load_intraday_bars_snapshot(_INTRADAY_BARS_SNAPSHOT_PATH),
        _primary_card_symbol,
        _now_effective,
    )
    w(f'<div class="block operator-subsection{disabled_class}" id="candidate-board">')
    if fixture_mode:
        w('  <h3>SETUP SCREENING &#8212; <span style="color:#ff9800">DEMO MODE &#8212; FIXTURE DATA</span></h3>')
    else:
        w('  <h3>SETUPS <span class="scope-note">· screening grades, not permission</span></h3>')
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
            _display_verdict = (
                _LOCKED_INTEGRATOR_VERDICTS.get(_verdict, _verdict)
                if operator_locked
                else _verdict
            )
            w(f'  <div class="idle-summary">{_esc(_display_verdict)}</div>')
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
                w('  <div class="unavailable" data-raw-state="NO_CANDIDATES">'
                  'Map empty — no symbols graded this run</div>')
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
                    # PRD-304 R7 (Sol finding 3): the low-grade idle summary reads
                    # as a neutral observation under lock — no action vocabulary.
                    _idle_head = "NO HIGH-GRADE SETUPS OBSERVED" if operator_locked else "NO ACTIONABLE SETUPS"
                    w('  <div class="idle-summary">'
                      f'<div>{_idle_head}</div>'
                      '<div>Market is not offering structure</div>'
                      '</div>')
                # PRD-158 § 4.3 Rule 4: empty tiers (post-Rule-1 filter) are
                # suppressed by the existing `if not tier_syms: continue` below.
                # PRD-332 (D5): with >=2 high-grade cards, present them as a native
                # radio-group setup workspace (no JS). Low tiers stay below, and the
                # single/zero high-grade case renders byte-identically to before.
                # Presentation only: sorted order, grades, tier headers/labels,
                # cards, and the chart slot are all unchanged (`_emit_card` makes the
                # same `_render_candidate_card` call the pre-D5 loop made).
                _hg_syms = [s for s in sorted_syms if symbols[s].get("grade", "") in _HIGH_GRADES]

                def _emit_card(sym: str, *, tier_closed: bool) -> None:
                    _sym_bars, _sym_caption = _price_bars.get(sym, (None, ""))
                    _render_candidate_card(
                        w, sym, symbols[sym],
                        contract_entry=(contract_entry_map or {}).get(sym),
                        contract_stop=(contract_stop_map or {}).get(sym),
                        operator_locked=operator_locked,
                        decision_permitted=_decision_state == "TRADE PERMITTED",
                        bars=_sym_bars,
                        bars_caption=_sym_caption,
                        chart_slot_available=(sym == _primary_card_symbol),
                        intraday_session=_intraday_session,
                        tier_closed=tier_closed,
                    )

                def _tier_label_for(tier_id: str, tier_label: str) -> str:
                    # PRD-304 R7: under lock the A+ tier reads OBSERVATION ONLY,
                    # never ACTIONABLE; the grade letter itself is analytical and
                    # preserved. _TIER_DEFS is shared, so substitute locally.
                    return (
                        "A+ — OBSERVATION ONLY"
                        if operator_locked and tier_id == "aplus"
                        else tier_label
                    )

                _use_workspace = len(_hg_syms) >= 2
                if _use_workspace:
                    # PRD-332 R1: default selection = the canonical primary when it
                    # is a high-grade workspace symbol, else the first workspace
                    # symbol (RC-1: a low-tier primary keeps its own chart slot below
                    # and is not a workspace tab). Selection is presentation only.
                    _default_setup = (
                        _primary_card_symbol
                        if _primary_card_symbol in _hg_syms
                        else _hg_syms[0]
                    )
                    w('<div class="setup-workspace" id="setup-workspace">')
                    # PRD-332 R2/R4/R7: native per-symbol visibility, no JS. Every
                    # rule is keyed on a `#setup-` radio, so the static _CSS never
                    # hides a panel -> a selector failure shows more, never less.
                    _rules: list[str] = []
                    for s in _hg_syms:
                        _sid = f"setup-{_esc(s)}"
                        _dq = _esc(s)
                        _rules.append(f'#{_sid}:checked~.setup-panels .setup-panel:not([data-setup="{_dq}"]){{display:none}}')
                        _rules.append(f'#{_sid}:checked~.setup-panels .tier-group:not(:has(.setup-panel[data-setup="{_dq}"])){{display:none}}')
                        _rail = {"A+": "#4caf50", "A": "#8bc34a", "B": "#ff9800"}.get(symbols[s].get("grade", ""), "#29b6f6")
                        _rules.append(f'#{_sid}:checked~.setup-tabs label[for="{_sid}"]{{color:#e0e0e0;background:#0d0d0d;border-bottom-color:{_rail};border-left-color:{_rail}}}')
                        _rules.append(f'#{_sid}:focus-visible~.setup-tabs label[for="{_sid}"]{{outline:1px solid #29b6f6;outline-offset:-2px}}')
                    w(f'  <style>{"".join(_rules)}</style>')
                    for s in _hg_syms:
                        _sid = f"setup-{_esc(s)}"
                        _chk = " checked" if s == _default_setup else ""
                        w(f'  <input type="radio" name="setup-select" id="{_sid}" class="setup-select"{_chk}>')
                    w('  <div class="setup-tabs" role="group" aria-label="Setups">')
                    for s in _hg_syms:
                        _g = symbols[s].get("grade", "")
                        _gcss = _GRADE_CSS.get(_g, "unknown")
                        _lc = symbols[s].get("lifecycle") or {}
                        _lc_tr = _lc.get("grade_transition")
                        _badge = _LIFECYCLE_BADGE_CSS.get(_lc_tr) if _lc_tr else None
                        _lc_html = f'<span class="setup-tab-lc {_badge}">{_esc(_lc_tr)}</span>' if _badge else ""
                        # PRD-332 R3: mirror MANUAL CHECK onto the tab as the token
                        # "CHECK" (never the literal "MANUAL CHECK", which stays
                        # exclusive to #alert-watchlist) when this workspace symbol is
                        # also a NEEDS_MANUAL_CHECK alert candidate.
                        _chk_html = '<span class="setup-tab-check">CHECK</span>' if s.upper() in _manual_check_syms else ""
                        w(f'    <label class="setup-tab grade-{_gcss}" for="setup-{_esc(s)}">'
                          f'<span class="setup-tab-sym">{_esc(s)}</span>'
                          f'<span class="setup-tab-grade">{_esc(_g)}</span>{_lc_html}{_chk_html}</label>')
                    w('  </div>')
                    w('  <div class="setup-panels">')
                    for tier_id, tier_label, tier_grades in _TIER_DEFS:
                        if tier_grades.isdisjoint(_HIGH_GRADES):
                            continue
                        tier_syms = [s for s in sorted_syms if symbols[s].get("grade", "") in tier_grades]
                        if not tier_syms:
                            continue
                        w(f'  <div class="tier-group" id="tier-{tier_id}">')
                        w(f'    <div class="tier-header">{_esc(_tier_label_for(tier_id, tier_label))} ({len(tier_syms)})</div>')
                        for sym in tier_syms:
                            w(f'    <div class="setup-panel" data-setup="{_esc(sym)}">')
                            _emit_card(sym, tier_closed=False)
                            w('    </div>')
                        w('  </div>')
                    w('  </div>')
                    w('</div>')

                for tier_id, tier_label, tier_grades in _TIER_DEFS:
                    is_low_tier = tier_grades.isdisjoint(_HIGH_GRADES)
                    if _use_workspace and not is_low_tier:
                        continue  # high tiers already rendered in the workspace
                    tier_syms = [s for s in sorted_syms if symbols[s].get("grade", "") in tier_grades]
                    if not tier_syms:
                        continue
                    _tier_label = _tier_label_for(tier_id, tier_label)
                    if is_low_tier:
                        # PRD-326 D1-Q1 (Option A): the low tier holding the canonical primary opens.
                        _open = " open" if _primary_card_symbol in tier_syms else ""
                        w(f'  <details{_open} class="tier-group" id="tier-{tier_id}">')
                        w(f'    <summary class="tier-header">{_esc(_tier_label)} ({len(tier_syms)})</summary>')
                    else:
                        w(f'  <div class="tier-group" id="tier-{tier_id}">')
                        w(f'    <div class="tier-header">{_esc(_tier_label)} ({len(tier_syms)})</div>')
                    for sym in tier_syms:
                        _emit_card(sym, tier_closed=(is_low_tier and not _open))
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

    w("</div>")  # #watching-zone

    # --- DETAILS / HISTORY: full evidence remains present, default collapsed. ---
    _active_lines = _details_lines
    w('<details class="block operator-zone" id="details-history">')
    w('  <summary>DETAILS / HISTORY ▶</summary>')
    w('  <div class="details-body">')

    # --- gex-context (PRD-309: display-only, baseline-neutral GEX card; emitted
    #     iff a fresh in-domain artifact is present, else true omission -> the
    #     document stays byte-identical to the pre-GEX baseline) ---
    if gex_snapshot is not None:
        gex_fragment = gex_card.render_fragment(
            gex_snapshot, now=now if now is not None else _utcnow()
        )
        if gex_fragment:
            w(gex_fragment)

    # --- market-movement (PRD-311: display-only 12/12 movement card; emitted iff
    #     a valid schema_version-2 artifact is present, else true omission -> the
    #     document stays byte-identical to the pre-card baseline). movement_card
    #     owns all validation/grouping/ordering; the renderer only loads + emits. ---
    if movement_snapshot is not None:
        movement_fragment = movement_card.render_fragment(movement_snapshot)
        if movement_fragment:
            w(movement_fragment)

    # --- SPY SESSION (DETAILS): PRD-329 R9 — the observation now renders
    #     first-class above; the group wrapper survives only for MCC-only renders
    #     (today's bytes); with an observation present MARKET CONTROL stands alone.
    _mcc = (payload.get("sections") or {}).get("market_control_card")
    if _mcc and not _spy_obs:
        w('<section class="spy-session-group" id="spy-session-details">')
        w('  <h3>SPY SESSION</h3>')

    # --- market-control-card (PRD-289: seven-field daily card; present iff the
    #     payload carries the section; projection-only — no renderer derivation) ---
    if _mcc:
        _cand = _mcc["candidate_implication"]
        _cand_display = _mcc_cell_display(_cand)
        if _cand.get("counts") is not None:
            _c = _cand["counts"]
            _cand_display += _esc(
                f' (ACTIVE {_c["ACTIVE"]} / NEAR_MISS {_c["NEAR_MISS"]} / BLOCKED {_c["BLOCKED"]})'
            )
        w('<div class="block" id="market-control-card">')
        w('  <h2>MARKET CONTROL</h2>')
        w('  <div class="kv-grid">')
        w(f'    <div class="label">LOCATION</div><div class="value">{_mcc_location_display(_mcc["location"])}</div>')
        w(f'    <div class="label">STATE</div><div class="value">{_mcc_cell_display(_mcc["state"])}</div>')
        w(f'    <div class="label">EVENT</div><div class="value">{_mcc_event_display(_mcc["event"])}</div>')
        w(f'    <div class="label">TRANSITION</div><div class="value">{_mcc_cell_display(_mcc["transition"])}</div>')
        w(f'    <div class="label">INVALIDATION</div><div class="value">{_mcc_cell_display(_mcc["invalidation"])}</div>')
        w(f'    <div class="label">CANDIDATE-IMPLICATION</div><div class="value">{_cand_display}</div>')
        w('  </div>')
        w("</div>")

    if _mcc and not _spy_obs:
        w("</section>")

    # --- sunday-macro-context (PRD-116: only under coherent Sunday lineage) ---
    if sunday_coherent:
        ctx = _build_sunday_context(
            macro_drivers,
            market_regime,
            market_map,
            operator_locked=operator_locked,
        )
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
        _monday_label = "Monday Context" if operator_locked else "Monday Watch"
        w(f'  <div class="field" style="margin-top:8px"><div class="label">{_monday_label}</div>'
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

    # Tradables grid (PRD-312: label + price, 2 per row). The monochrome
    # daily-change arrow was retired here — it duplicated the Market Movement
    # card's signed value. The price (current_price) is independently fresh from
    # market_map; the tradables row keeps its label + price with no arrow.
    w('  <div class="macro-tradables-grid">')
    for slot in TRADABLES_ROW.slots:
        val = tape_value_map.get(slot.label, "N/A")
        w(
            f'    <span class="tradable-cell">'
            f'<span class="macro-tape-label">{_esc(slot.label)}</span>'
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
    # PRD-313: suppress the standalone block only for a RESOLVED view dict that
    # is healthy, has zero events, and is not expiring -- the redundant empty
    # state MARKET STATE EVENT RISK already carries. A None/omitted view is NOT
    # a resolved view and keeps its existing empty-state render (never silent).
    _rf_suppress = (
        isinstance(red_folder, dict)
        and red_folder.get("ok", True)
        and not (red_folder.get("events") or [])
        and not red_folder.get("expiring")
    )
    if not _rf_suppress:
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
                # reflow can render the header inline. PRD-218 + Change #5: the
                # Price cell (index 1) AND the Alignment cell (index 3) carry the
                # alignment colour class. PRD-220: the Intraday cell (index 7)
                # gets a class so it wraps to its own line.
                _classes = []
                if _i in (1, 3) and _px_cls:
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

    # --- run-delta ---
    w('<div class="block" id="run-delta">')
    w("  <h2>Changes Since Last Run</h2>")
    if previous_run is None:
        w('  <div class="value">NO_PREVIOUS_RUN</div>')
    else:
        any_emitted = False
        # PRD-158 § 4.2 translation 13: regime transitions render as
        # "Permission flipped to …" or are suppressed entirely.
        previous_regime = _req(previous_run, "regime")
        current_regime = _req(run, "regime")
        if operator_locked:
            if previous_regime != current_regime:
                w(
                    f'  <div class="value">Regime: {_esc(previous_regime)} '
                    f'-&gt; {_esc(current_regime)}</div>'
                )
                any_emitted = True
            delta_fields = (
                ("System Halted", _bool_str(_req(run, "system_halted")),
                                  _bool_str(_req(previous_run, "system_halted"))),
            )
        else:
            regime_flip = _regime_flip_phrase(previous_regime, current_regime)
            if regime_flip is not None:
                w(f'  <div class="value">{_esc(regime_flip)}</div>')
                any_emitted = True
            delta_fields = (
                ("Posture",
                 _POSTURE_LABELS.get(str(_req(run, "posture")), str(_req(run, "posture"))),
                 _POSTURE_LABELS.get(
                     str(_req(previous_run, "posture")),
                     str(_req(previous_run, "posture")),
                 )),
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
            # PRD-265 R5: mark coverage-bounded days; legacy/EXPANSION/FULL render
            # unchanged (no marker).
            _sb_bounded_html = (
                '<span class="scoreboard-coverage">BOUNDED</span>'
                if _coverage_bounded(_row) else ""
            )
            w(
                f'  <div class="scoreboard-row">'
                f'<span class="scoreboard-date">{_sb_date}</span>'
                f'<span class="scoreboard-regime">{_sb_regime}</span>'
                f'<span class="scoreboard-posture">{_esc(_sb_posture)}</span>'
                f'<span class="scoreboard-spy">SPY next {_esc(_sb_spy_txt)}</span>'
                f'{_sb_bounded_html}'
                f"</div>"
            )
    else:
        w('  <div class="value">No regime history yet.</div>')
    w("</div>")

    w("  </div>")  # .details-body
    w("</details>")

    # Assemble the five operator-question zones in source order. Each buffer was
    # rendered from the same in-memory facts as the prior subsystem blocks.
    _active_lines = lines
    lines.extend(_verdict_lines)
    lines.extend(_tape_lines)
    lines.extend(_spy_lines)
    lines.extend(_today_lines)
    lines.extend(_watching_lines)
    lines.extend(_details_lines)

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
    gex_snapshot: dict | None = None,
    movement_snapshot: dict | None = None,
    price_bars_snapshot: dict | None = None,
    now: datetime | None = None,
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
        gex_snapshot=gex_snapshot,
        movement_snapshot=movement_snapshot,
        price_bars_snapshot=price_bars_snapshot,
        now=now,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def _load_contract_entry_context(
    logs_dir: Path,
) -> tuple[dict[str, float], dict[str, float], list[dict], object | None, Path]:
    """Load latest_hourly_contract entry/stop prices, alert_candidates, and generated_at timestamp."""
    path = logs_dir / _HOURLY_CONTRACT_PATH.name
    # The persisted hourly contract IS a PipelineContract (PRD-237/J1); this
    # is the renderer's only direct contract read — everything else consumes
    # the (untyped) payload.
    contract: PipelineContract | None = _load_json_optional(path)
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
    # PRD-309: display-only GEX card sidecar; absent/malformed => None => card suppressed.
    gex_snapshot = gex_card.load_gex_snapshot(logs_dir / _GEX_SNAPSHOT_PATH.name)
    # PRD-311: MARKET MOVEMENT card sidecar; absent/malformed/invalid => None => card suppressed.
    movement_snapshot = movement_card.load_watchlist_snapshot(logs_dir / _MOVEMENT_SNAPSHOT_PATH.name)
    # PRD-321 R2: display-only price-bars sidecar; absent/malformed => None =>
    # every candidate degrades to the compact ladder, nothing else changes.
    price_bars_snapshot = _load_price_bars_snapshot(logs_dir / _PRICE_BARS_SNAPSHOT_PATH.name)
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
        gex_snapshot=gex_snapshot,
        movement_snapshot=movement_snapshot,
        price_bars_snapshot=price_bars_snapshot,
        now=_utcnow(),
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
