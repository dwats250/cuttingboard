"""
Notification formatters for scheduled notify-mode runs.

Public API is kept here for callers that import `cuttingboard.notifications`.
The alert renderer lives in formatter.py.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from cuttingboard.normalization import NormalizedQuote
from cuttingboard.qualification import QualificationSummary
from cuttingboard.regime import CHAOTIC, RegimeState, STAY_FLAT
from cuttingboard.validation import ValidationSummary
from cuttingboard.watch import WatchSummary

from .formatter import (
    ALERT_CONTEXT_INTRADAY,
    ALERT_CONTEXT_NOTIFY,
    ALERT_CONTEXT_RUN,
    AlertEvent,
    format_ntfy_alert,
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
    }
)

_SUPPRESS_CONFIDENCE = 0.55


def ntfy_title(notify_mode: str, date_str: str) -> str:
    del date_str
    event = AlertEvent(
        alert_context=ALERT_CONTEXT_NOTIFY,
        notify_mode=notify_mode,
        outcome="NO_TRADE",
        asof_utc=datetime.now(timezone.utc),
    )
    title, _ = format_ntfy_alert(event)
    return title


def should_suppress(
    notify_mode: str,
    regime: Optional[RegimeState],
    qualification_summary: Optional[QualificationSummary],
) -> bool:
    """Return True if the notification should be suppressed.

    Only applies to midmorning and power_hour.
    CHAOTIC is always suppressed — run_intraday.py handles crisis alerts.
    Suppress when posture is STAY_FLAT, confidence is low, and no watchlist.
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


def format_failure_notification(notify_mode: str, date_str: str, reason: str) -> tuple[str, str]:
    del date_str
    event = AlertEvent(
        alert_context=ALERT_CONTEXT_NOTIFY,
        notify_mode=notify_mode,
        outcome="NO_TRADE",
        asof_utc=datetime.now(timezone.utc),
        failure_reason=reason,
    )
    return format_ntfy_alert(event)
