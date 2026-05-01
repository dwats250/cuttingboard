"""
Notification formatters for scheduled notify-mode runs.

Public API is kept here for callers that import `cuttingboard.notifications`.
The alert renderer lives in formatter.py.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from cuttingboard.normalization import NormalizedQuote
from cuttingboard.qualification import QualificationSummary
from cuttingboard.regime import CHAOTIC, RegimeState, STAY_FLAT
from cuttingboard.universe import is_tradable_symbol
from cuttingboard.validation import ValidationSummary
from cuttingboard.watch import WatchSummary

from .formatter import (
    ALERT_CONTEXT_INTRADAY,
    ALERT_CONTEXT_NOTIFY,
    ALERT_CONTEXT_RUN,
    AlertEvent,
    format_ntfy_alert,
    NOTIFY_HOURLY,
)

# ---------------------------------------------------------------------------
# Notify mode constants
# ---------------------------------------------------------------------------

NOTIFY_PREMARKET = "premarket"
NOTIFY_ORB_TRAJECTORY = "orb_trajectory"
NOTIFY_POST_ORB = "post_orb"
NOTIFY_MIDMORNING = "midmorning"
NOTIFY_POWER_HOUR = "power_hour"
NOTIFY_MARKET_CLOSE = "market_close"

NOTIFY_MODES = frozenset(
    {
        NOTIFY_PREMARKET,
        NOTIFY_ORB_TRAJECTORY,
        NOTIFY_POST_ORB,
        NOTIFY_MIDMORNING,
        NOTIFY_POWER_HOUR,
        NOTIFY_MARKET_CLOSE,
        NOTIFY_HOURLY,
    }
)

_SUPPRESS_CONFIDENCE = 0.55
_ET_TZ = ZoneInfo("America/New_York")
_LIFECYCLE_HIGH_GRADES = frozenset({"A+", "A", "B"})


def _hhmm(asof_utc: datetime) -> str:
    return asof_utc.astimezone(_ET_TZ).strftime("%H:%M")


def _compact_label(value: object) -> str:
    return str(value or "UNKNOWN").replace("_", " ").upper()


def _hourly_context_line(regime: Optional[RegimeState]) -> str:
    if regime is None:
        return "UNKNOWN | UNKNOWN | 0.00"
    return f"{_compact_label(regime.regime)} | {_compact_label(regime.posture)} | {regime.confidence:.2f}"


def _hourly_regime_label(regime: Optional[RegimeState]) -> str:
    return _compact_label(regime.regime if regime is not None else None)


def _trigger_conditions(regime_label: str) -> tuple[str, str]:
    if regime_label == "RISK OFF":
        return ("breakdown below support", "failed reclaim at breakdown level")
    if regime_label in {"RISK ON", "EXPANSION"}:
        return ("breakout above resistance", "continuation hold above trigger")
    if regime_label == "NEUTRAL":
        return ("range break", "expansion confirmation")
    return ("range break", "confirmed direction")


def _append_trigger_block(lines: list[str], regime_label: str) -> None:
    lines.extend(["", "TRIGGERS:"])
    lines.extend(f"- {condition}" for condition in _trigger_conditions(regime_label))


def _hourly_reason(
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
    *,
    has_candidates: bool,
) -> str:
    if validation_summary.system_halted:
        return str(validation_summary.halt_reason or "system halted")[:80]
    if has_candidates:
        return "candidates gated"
    if qualification_summary is not None and qualification_summary.regime_failure_reason:
        return str(qualification_summary.regime_failure_reason)[:80]
    if regime is not None and regime.posture == STAY_FLAT:
        return "stay flat posture"
    return "no setups"


def _watch_lines_from_qualification(qualification_summary: Optional[QualificationSummary]) -> tuple[str, ...]:
    if qualification_summary is None:
        return ()
    lines = []
    ranked = sorted(
        qualification_summary.watchlist,
        key=lambda item: (item.symbol, item.direction),
    )
    for item in ranked:
        if not is_tradable_symbol(item.symbol):
            continue
        line = f"- {item.symbol.upper()} {item.direction.upper()}"
        reason = _as_clean_string(getattr(item, "watchlist_reason", None))
        if reason:
            line = f"{line}: {reason[:60]}"
        lines.append(line)
        if len(lines) >= 2:
            break
    return tuple(lines)


def _parse_candidate_line(line: str) -> Optional[tuple[str, str, str]]:
    parts = [part.strip() for part in line.split("|")]
    if len(parts) < 4:
        return None
    symbol = parts[0].upper()
    direction = parts[1].upper()
    rr = parts[-1].replace(":1", "").strip()
    if not is_tradable_symbol(symbol):
        return None
    try:
        rr_text = f"{float(rr):.1f}"
    except ValueError:
        return None
    return symbol, direction, rr_text


def _as_clean_string(value: object) -> Optional[str]:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned.encode("ascii", errors="replace").decode("ascii")


def _lifecycle_reason(entry: dict[str, Any]) -> Optional[str]:
    trade_framing = entry.get("trade_framing")
    downgrade = trade_framing.get("downgrade") if isinstance(trade_framing, dict) else None
    for value in (downgrade, entry.get("setup_state"), entry.get("reason_for_grade")):
        if reason := _as_clean_string(value):
            return reason
    return None


def _current_lifecycle_line(symbol: object, entry: object, hhmm: str) -> Optional[tuple[str, str]]:
    if not isinstance(symbol, str) or not isinstance(entry, dict):
        return None
    lifecycle = entry.get("lifecycle")
    if not isinstance(lifecycle, dict):
        return None

    transition = _as_clean_string(lifecycle.get("grade_transition"))
    current_grade = _as_clean_string(entry.get("grade"))
    previous_grade = _as_clean_string(lifecycle.get("previous_grade"))
    if transition is None or current_grade is None:
        return None

    should_alert = (
        transition == "UPGRADED"
        or (transition == "NEW" and current_grade in _LIFECYCLE_HIGH_GRADES)
        or (transition == "DOWNGRADED" and previous_grade in _LIFECYCLE_HIGH_GRADES)
    )
    if not should_alert:
        return None

    symbol_text = symbol.strip().upper()
    if not symbol_text:
        return None
    direction = _as_clean_string(entry.get("direction"))
    prefix = f"{hhmm} {symbol_text}"
    if direction:
        prefix = f"{prefix} {direction.upper()}"

    if transition == "UPGRADED":
        line = f"{prefix} - UPGRADED TO {current_grade}"
    elif transition == "DOWNGRADED":
        line = f"{prefix} - DOWNGRADED TO {current_grade}"
    else:
        line = f"{prefix} - NEW ({current_grade})"
    return line, f"{symbol_text}|{transition}|{previous_grade or ''}|{current_grade}"


def _removed_lifecycle_line(entry: object, hhmm: str) -> Optional[tuple[str, str]]:
    if not isinstance(entry, dict):
        return None
    symbol = _as_clean_string(entry.get("symbol"))
    previous_grade = _as_clean_string(entry.get("previous_grade"))
    transition = _as_clean_string(entry.get("grade_transition"))
    if (
        symbol is None
        or previous_grade not in _LIFECYCLE_HIGH_GRADES
        or transition != "REMOVED"
    ):
        return None
    symbol_text = symbol.upper()
    return (
        f"{hhmm} {symbol_text} - REMOVED (prev: {previous_grade})",
        f"{symbol_text}|REMOVED|{previous_grade}|",
    )


def _lifecycle_alert_lines(market_map: Optional[dict[str, Any]], asof_utc: datetime) -> tuple[str, ...]:
    if not isinstance(market_map, dict):
        return ()

    hhmm = _hhmm(asof_utc)
    lines: list[str] = []
    seen: set[str] = set()
    symbols = market_map.get("symbols")
    if isinstance(symbols, dict):
        for symbol, entry in symbols.items():
            parsed = _current_lifecycle_line(symbol, entry, hhmm)
            if parsed is None:
                continue
            line, key = parsed
            if key in seen:
                continue
            seen.add(key)
            lines.append(line)
            if isinstance(entry, dict) and (reason := _lifecycle_reason(entry)):
                lines.append(reason)

    removed_symbols = market_map.get("removed_symbols")
    if isinstance(removed_symbols, list):
        for entry in removed_symbols:
            parsed = _removed_lifecycle_line(entry, hhmm)
            if parsed is None:
                continue
            line, key = parsed
            if key in seen:
                continue
            seen.add(key)
            lines.append(line)

    return tuple(lines)


def _append_lifecycle_alerts(body: str, market_map: Optional[dict[str, Any]], asof_utc: datetime) -> str:
    lines = _lifecycle_alert_lines(market_map, asof_utc)
    if not lines:
        return body
    return "\n".join([body, "", *lines])


def should_suppress(
    notify_mode: str,
    regime: Optional[RegimeState],
    qualification_summary: Optional[QualificationSummary],
) -> bool:
    """Return True if the notification should be suppressed.

    Only applies to midmorning and power_hour.
    CHAOTIC is always suppressed — the hourly workflow handles crisis-level alerts.
    Suppress when posture is STAY_FLAT, confidence is low, and no watchlist.

    NOTE: This function is currently NOT called from _execute_notify_run() or any
    live send path. Suppression does not happen at runtime. If wired in, callers
    must write a notification audit record with reason="suppressed" so skips are
    visible in logs/audit.jsonl.
    """
    if notify_mode not in {NOTIFY_MIDMORNING, NOTIFY_POWER_HOUR}:
        return False
    if regime is None:
        return True
    if regime.regime == CHAOTIC:
        return True
    flat = regime.posture == STAY_FLAT
    low_conf = regime.confidence < _SUPPRESS_CONFIDENCE
    no_watches = qualification_summary is None or (
        qualification_summary.symbols_watchlist == 0
        and qualification_summary.symbols_qualified == 0
    )
    return flat and low_conf and no_watches


def format_notification(
    notify_mode: str,
    date_str: str,
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
    normalized_quotes: dict[str, NormalizedQuote],
    watch_summary: Optional[WatchSummary] = None,
    outcome: str = "NO_TRADE",
    halt_reason: Optional[str] = None,
    market_map: Optional[dict[str, Any]] = None,
    **_: object,
) -> tuple[str, str]:
    """Return compact (title, body) for ntfy."""
    del date_str, normalized_quotes
    asof_utc = regime.computed_at_utc if regime is not None else datetime.now(timezone.utc)
    event = AlertEvent(
        alert_context=ALERT_CONTEXT_NOTIFY,
        notify_mode=notify_mode,
        outcome=outcome,
        asof_utc=asof_utc,
        regime=regime,
        validation_summary=validation_summary,
        qualification_summary=qualification_summary,
        watch_summary=watch_summary,
        halt_reason=halt_reason,
    )
    title, body = format_ntfy_alert(event)
    return title, _append_lifecycle_alerts(body, market_map, asof_utc)


def format_run_alert(
    *,
    outcome: str,
    run_at_utc: datetime,
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
    watch_summary: Optional[WatchSummary],
    halt_reason: Optional[str] = None,
    notify_mode: Optional[str] = None,
    market_map: Optional[dict[str, Any]] = None,
    **_: object,
) -> tuple[str, str]:
    """Format the default live/sunday ntfy alert from pipeline state."""
    event = AlertEvent(
        alert_context=ALERT_CONTEXT_RUN,
        notify_mode=notify_mode,
        outcome=outcome,
        asof_utc=run_at_utc,
        regime=regime,
        validation_summary=validation_summary,
        qualification_summary=qualification_summary,
        watch_summary=watch_summary,
        halt_reason=halt_reason,
    )
    title, body = format_ntfy_alert(event)
    return title, _append_lifecycle_alerts(body, market_map, run_at_utc)


def format_intraday_alert(
    *,
    alert_type: str,
    asof_utc: datetime,
    regime: Optional[RegimeState],
) -> tuple[str, str]:
    """Format an intraday trigger using the shared ntfy formatter."""
    event = AlertEvent(
        alert_context=ALERT_CONTEXT_INTRADAY,
        notify_mode=None,
        outcome="NO_TRADE",
        asof_utc=asof_utc,
        regime=regime,
        intraday_alert_type=alert_type,
    )
    return format_ntfy_alert(event)


def format_hourly_notification(
    *,
    asof_utc: datetime,
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
    candidate_lines: tuple[str, ...] = (),
    halt_reason: Optional[str] = None,
    market_map: Optional[dict[str, Any]] = None,
) -> tuple[str, str]:
    del halt_reason
    hhmm = _hhmm(asof_utc)
    regime_label = _hourly_regime_label(regime)
    lines = [_hourly_context_line(regime)]
    parsed = tuple(
        parsed_line
        for line in candidate_lines
        if (parsed_line := _parse_candidate_line(line)) is not None
    )

    if regime is not None and regime.posture == STAY_FLAT:
        title = f"STAY FLAT {hhmm}"
        reason = _hourly_reason(
            regime,
            validation_summary,
            qualification_summary,
            has_candidates=False,
        )
        lines.extend(
            [
                "No trade.",
                f"Reason: {reason}",
            ]
        )
        _append_trigger_block(lines, regime_label)
        body = "\n".join(lines)
        return title, _append_lifecycle_alerts(body, market_map, asof_utc)

    if parsed:
        first_symbol, first_direction, _ = parsed[0]
        title = f"{first_direction} {first_symbol} {hhmm}"
        lines.extend(
            f"- {symbol} {direction} RR {rr}"
            for symbol, direction, rr in parsed[:4]
        )
        body = "\n".join(lines)
        return title, _append_lifecycle_alerts(body, market_map, asof_utc)

    has_candidates = bool(
        qualification_summary is not None
        and (qualification_summary.symbols_qualified or qualification_summary.symbols_watchlist)
    )
    title = f"WATCHLIST {hhmm}" if has_candidates else f"ACTIVE - NO SETUP {hhmm}"
    reason = _hourly_reason(
        regime,
        validation_summary,
        qualification_summary,
        has_candidates=has_candidates,
    )
    lines.extend(
        [
            "WATCHLIST" if has_candidates else "No trade.",
            f"Reason: {reason}",
        ]
    )
    if has_candidates:
        watch_lines = _watch_lines_from_qualification(qualification_summary)
        if watch_lines:
            lines.extend(["", "WATCH:", *watch_lines])
    _append_trigger_block(lines, regime_label)
    body = "\n".join(lines)
    return title, _append_lifecycle_alerts(body, market_map, asof_utc)


def format_failure_notification(notify_mode: str, date_str: str, reason: str) -> tuple[str, str]:
    del date_str
    label = {
        NOTIFY_PREMARKET: "PREMARKET",
        NOTIFY_ORB_TRAJECTORY: "EARLY SESSION",
        NOTIFY_POST_ORB: "POST-ORB",
        NOTIFY_MIDMORNING: "MIDDAY",
        NOTIFY_POWER_HOUR: "POWER HOUR",
        NOTIFY_MARKET_CLOSE: "MARKET CLOSE",
        NOTIFY_HOURLY: "HOURLY",
    }.get(notify_mode, str(notify_mode).upper())
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_reason = str(reason)[:200].encode("ascii", errors="replace").decode("ascii")
    title = f"{label} ERROR"
    body = "\n".join(
        [
            f"timestamp: {timestamp}",
            "",
            "Failure",
            safe_reason,
        ]
    )
    return title, body
