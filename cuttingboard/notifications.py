"""
Notification formatters for scheduled notify-mode runs.

One formatter per mode. All return (title, body) for ntfy.
Shared by runtime.py — do not import from output.py here.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from cuttingboard.normalization import NormalizedQuote
from cuttingboard.qualification import QualificationSummary
from cuttingboard.regime import (
    RegimeState,
    AGGRESSIVE_LONG,
    CHAOTIC,
    CONTROLLED_LONG,
    DEFENSIVE_SHORT,
    NEUTRAL_PREMIUM,
    STAY_FLAT,
)
from cuttingboard.validation import ValidationSummary

# ---------------------------------------------------------------------------
# Notify mode constants
# ---------------------------------------------------------------------------

NOTIFY_PREMARKET = "premarket"
NOTIFY_ORB_TRAJECTORY = "orb_trajectory"
NOTIFY_POST_ORB = "post_orb"
NOTIFY_MIDMORNING = "midmorning"
NOTIFY_POWER_HOUR = "power_hour"

NOTIFY_MODES = frozenset(
    {NOTIFY_PREMARKET, NOTIFY_ORB_TRAJECTORY, NOTIFY_POST_ORB, NOTIFY_MIDMORNING, NOTIFY_POWER_HOUR}
)

_MODE_LABELS = {
    NOTIFY_PREMARKET: "PREMARKET",
    NOTIFY_ORB_TRAJECTORY: "EARLY SESSION",
    NOTIFY_POST_ORB: "POST-ORB",
    NOTIFY_MIDMORNING: "MIDDAY",
    NOTIFY_POWER_HOUR: "POWER HOUR",
}

_SUPPRESS_CONFIDENCE = 0.55

# PT = UTC-7 (PDT). Display only — no pytz dependency.
_PT_OFFSET = timedelta(hours=-7)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ntfy_title(notify_mode: str, date_str: str) -> str:
    label = _MODE_LABELS.get(notify_mode, notify_mode.upper())
    return f"CUTTINGBOARD - {label}"


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
) -> tuple[str, str]:
    """Return (title, body) for ntfy."""
    title = ntfy_title(notify_mode, date_str)
    del date_str, validation_summary, normalized_quotes
    body = _format_structured_notification(notify_mode, regime, qualification_summary)
    return title, body


def format_failure_notification(notify_mode: str, date_str: str, reason: str) -> tuple[str, str]:
    del date_str
    label = _MODE_LABELS.get(notify_mode, notify_mode.upper())
    title = f"CUTTINGBOARD - {label} FAILED"
    body = f"{label} - {_pt_timestamp()}\nFailure.\nReason: {reason}"
    return title, body


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _pt_timestamp(when_utc: Optional[datetime] = None) -> str:
    when_utc = when_utc or datetime.now(timezone.utc)
    pt = when_utc.astimezone(timezone(_PT_OFFSET))
    return pt.strftime("%H:%M PT")


def _body_session_line(notify_mode: str, regime: Optional[RegimeState]) -> str:
    label = _MODE_LABELS.get(notify_mode, notify_mode.upper())
    timestamp = regime.computed_at_utc if regime is not None else None
    return f"{label} - {_pt_timestamp(timestamp)}"


def _signed_int(value: int) -> str:
    return f"{value:+d}"


def _signed_pct(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"{value:+.1f}"


def _vix_level(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f}"


def _metrics_line(regime: Optional[RegimeState]) -> str:
    if regime is None:
        return "Conf N/A | Net N/A | VIX N/A (N/A)"
    delta = regime.vix_pct_change * 100 if regime.vix_pct_change is not None else None
    return (
        f"Conf {regime.confidence:.2f} | "
        f"Net {_signed_int(regime.net_score)} | "
        f"VIX {_vix_level(regime.vix_level)} ({_signed_pct(delta)})"
    )


def _regime_block(regime: Optional[RegimeState]) -> str:
    if regime is None:
        return "UNKNOWN / STAY_FLAT"
    return f"{regime.regime} / {regime.posture}"


def _focus_symbols(qualification_summary: Optional[QualificationSummary]) -> list[str]:
    if qualification_summary is None:
        return []
    return [result.symbol for result in qualification_summary.qualified_trades[:3]]


def _watch_symbols(qualification_summary: Optional[QualificationSummary]) -> list[str]:
    if qualification_summary is None:
        return []
    return [result.symbol for result in qualification_summary.watchlist[:2]]


def _summary_line(
    regime: Optional[RegimeState],
    qualification_summary: Optional[QualificationSummary],
) -> str:
    focus_count = 0 if qualification_summary is None else qualification_summary.symbols_qualified
    watch_count = 0 if qualification_summary is None else qualification_summary.symbols_watchlist

    if regime is None:
        return "No data. Stay flat."
    if regime.regime == CHAOTIC:
        return "Chaotic tape. No trade."
    if regime.posture == STAY_FLAT and focus_count == 0 and watch_count == 0:
        return "No edge. Stay flat."
    if regime.posture == STAY_FLAT and watch_count > 0:
        return "Chop. Reduce size."
    if focus_count > 0:
        if regime.posture in {AGGRESSIVE_LONG, CONTROLLED_LONG}:
            return "Continuations favored. Defined risk."
        if regime.posture == DEFENSIVE_SHORT:
            return "Risk-off pressure. Stay selective."
        if regime.posture == NEUTRAL_PREMIUM:
            return "Selective setups only. Defined risk."
    if watch_count > 0:
        if regime.posture in {AGGRESSIVE_LONG, CONTROLLED_LONG}:
            return "Expansion building. Watch breaks."
        return "Momentum building. Watch continuation."
    if regime.posture == DEFENSIVE_SHORT:
        return "Weak tape. Wait for confirmation."
    return "No edge. Stay flat."


def _format_structured_notification(
    notify_mode: str,
    regime: Optional[RegimeState],
    qualification_summary: Optional[QualificationSummary],
) -> str:
    lines = [
        _body_session_line(notify_mode, regime),
        _metrics_line(regime),
        "",
        _regime_block(regime),
    ]

    focus = _focus_symbols(qualification_summary)
    if focus:
        lines.extend(["", "Focus:", *focus])

    watch = _watch_symbols(qualification_summary)
    if watch:
        lines.extend(["", "Watch:", *watch])

    lines.extend(["", _summary_line(regime, qualification_summary)])
    return "\n".join(lines)
