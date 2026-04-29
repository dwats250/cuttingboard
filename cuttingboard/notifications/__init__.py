"""
Notification formatters for scheduled notify-mode runs.

Public API is kept here for callers that import `cuttingboard.notifications`.
The alert renderer lives in formatter.py.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
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


def _hhmm(asof_utc: datetime) -> str:
    return asof_utc.astimezone(_ET_TZ).strftime("%H:%M")


def _compact_label(value: object) -> str:
    return str(value or "UNKNOWN").replace("_", " ").upper()


def _hourly_context_line(regime: Optional[RegimeState]) -> str:
    if regime is None:
        return "UNKNOWN | UNKNOWN | 0.00"
    return f"{_compact_label(regime.regime)} | {_compact_label(regime.posture)} | {regime.confidence:.2f}"


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
    **_: object,
) -> tuple[str, str]:
    """Return compact (title, body) for ntfy."""
    del date_str, normalized_quotes
    event = AlertEvent(
        alert_context=ALERT_CONTEXT_NOTIFY,
        notify_mode=notify_mode,
        outcome=outcome,
        asof_utc=(regime.computed_at_utc if regime is not None else datetime.now(timezone.utc)),
        regime=regime,
        validation_summary=validation_summary,
        qualification_summary=qualification_summary,
        watch_summary=watch_summary,
        halt_reason=halt_reason,
    )
    return format_ntfy_alert(event)


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
    return format_ntfy_alert(event)


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
) -> tuple[str, str]:
    del halt_reason
    hhmm = _hhmm(asof_utc)
    lines = [_hourly_context_line(regime)]
    parsed = tuple(
        parsed_line
        for line in candidate_lines
        if (parsed_line := _parse_candidate_line(line)) is not None
    )

    if regime is not None and regime.posture == STAY_FLAT:
        title = f"STAY FLAT {hhmm}"
        lines.extend(
            [
                "NO TRADE",
                _hourly_reason(
                    regime,
                    validation_summary,
                    qualification_summary,
                    has_candidates=False,
                ),
            ]
        )
        return title, "\n".join(lines)

    if parsed:
        first_symbol, first_direction, _ = parsed[0]
        title = f"{first_direction} {first_symbol} {hhmm}"
        lines.extend(
            f"- {symbol} {direction} RR {rr}"
            for symbol, direction, rr in parsed[:4]
        )
        return title, "\n".join(lines)

    title = f"ACTIVE - NO SETUP {hhmm}"
    has_candidates = bool(
        qualification_summary is not None
        and (qualification_summary.symbols_qualified or qualification_summary.symbols_watchlist)
    )
    lines.extend(
        [
            "WATCHLIST" if has_candidates else "NO TRADE",
            _hourly_reason(
                regime,
                validation_summary,
                qualification_summary,
                has_candidates=has_candidates,
            ),
        ]
    )
    return title, "\n".join(lines)


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
