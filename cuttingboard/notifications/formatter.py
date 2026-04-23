from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from cuttingboard.qualification import QualificationResult, QualificationSummary
from cuttingboard.regime import (
    AGGRESSIVE_LONG,
    CHAOTIC,
    CONTROLLED_LONG,
    DEFENSIVE_SHORT,
    NEUTRAL,
    NEUTRAL_PREMIUM,
    RISK_OFF,
    RISK_ON,
    RegimeState,
    STAY_FLAT,
)
from cuttingboard.validation import ValidationSummary
from cuttingboard.watch import WatchItem, WatchSummary, regime_bias

LOCAL_TZ = ZoneInfo("America/Vancouver")
_ET_TZ = ZoneInfo("America/New_York")

NOTIFY_PREMARKET = "premarket"
NOTIFY_ORB_TRAJECTORY = "orb_trajectory"
NOTIFY_POST_ORB = "post_orb"
NOTIFY_MIDMORNING = "midmorning"
NOTIFY_POWER_HOUR = "power_hour"
NOTIFY_HOURLY = "hourly"

OUTCOME_TRADE = "TRADE"
OUTCOME_NO_TRADE = "NO_TRADE"
OUTCOME_HALT = "HALT"

ALERT_CONTEXT_NOTIFY = "notify"
ALERT_CONTEXT_RUN = "run"
ALERT_CONTEXT_INTRADAY = "intraday"


@dataclass(frozen=True)
class AlertEvent:
    alert_context: str
    notify_mode: Optional[str]
    outcome: str
    asof_utc: datetime
    regime: Optional[RegimeState] = None
    validation_summary: Optional[ValidationSummary] = None
    qualification_summary: Optional[QualificationSummary] = None
    watch_summary: Optional[WatchSummary] = None
    halt_reason: Optional[str] = None
    failure_reason: Optional[str] = None
    intraday_alert_type: Optional[str] = None
    candidate_lines: tuple[str, ...] = ()


def format_ntfy_alert(event: AlertEvent) -> tuple[str, str]:
    if event.failure_reason:
        return _format_failure(event)
    if event.intraday_alert_type:
        return _format_intraday(event)
    if event.outcome == OUTCOME_HALT or event.halt_reason:
        return _format_halt(event)
    if event.notify_mode == NOTIFY_HOURLY:
        return _format_hourly(event)
    if event.alert_context == ALERT_CONTEXT_RUN:
        return _format_run_summary(event)
    if event.notify_mode == NOTIFY_PREMARKET:
        return _format_premarket(event)
    if _qualified_focus(event):
        return _format_setup_ready(event)
    if _forming_focus(event):
        return _format_setup_forming(event)
    if event.notify_mode in {NOTIFY_MIDMORNING, NOTIFY_POWER_HOUR, NOTIFY_ORB_TRAJECTORY}:
        return _format_session_check(event)
    if _focus_candidates(event):
        return _format_watchlist_update(event)
    return _format_no_trade(event)


def _format_hourly(event: AlertEvent) -> tuple[str, str]:
    regime = event.regime
    posture = regime.posture if regime is not None else STAY_FLAT
    tradable = posture != STAY_FLAT

    qual = event.qualification_summary
    candidate_count = qual.symbols_qualified if (qual is not None and tradable) else 0

    ts = event.asof_utc.astimezone(_ET_TZ).strftime("%H:%M ET")
    regime_str = regime.regime if regime is not None else "UNKNOWN"
    confidence_str = f"{regime.confidence:.2f}" if regime is not None else "0.00"

    lines = [
        ts,
        "",
        f"Regime: {regime_str}",
        f"Posture: {posture}",
        f"Confidence: {confidence_str}",
        f"Tradable: {'Yes' if tradable else 'No'}",
        f"Setups: {candidate_count}",
    ]

    if candidate_count > 0 and event.candidate_lines:
        lines.append("")
        lines.extend(event.candidate_lines)
        first = qual.qualified_trades[0]
        title = f"{first.symbol} {first.direction} READY"
    elif candidate_count == 0 and tradable:
        lines.extend(["", "No A+ setups"])
        title = "NO SETUP"
    else:
        lines.extend(["", "STAY_FLAT — no entries"])
        title = "STAY FLAT"

    return title, "\n".join(lines)


def _format_run_summary(event: AlertEvent) -> tuple[str, str]:
    # End-of-run alerts are contract-driven: TRADE alerts require a qualified
    # trade, and every non-trade outcome renders the generic no-trade summary.
    if event.outcome == OUTCOME_TRADE:
        return _format_setup_ready(event)
    return _format_no_trade(event)


def _format_intraday(event: AlertEvent) -> tuple[str, str]:
    alert_type = event.intraday_alert_type
    posture = _session_posture(event)
    vix_line = _vix_line(event.regime)

    if alert_type == "CHAOTIC":
        lines = [
            _time_line(event.asof_utc),
            "",
            "Chaotic market",
            "Volatility regime unstable",
            "",
            "Posture",
            "Stay flat",
        ]
        if vix_line:
            lines.extend(["", "Volatility", vix_line])
        return "CHAOTIC ALERT", "\n".join(lines)

    if alert_type == "REGIME_SHIFT":
        shifted_line = "Risk improving" if event.regime and event.regime.regime == RISK_ON else "Risk deteriorating"
        lines = [
            _time_line(event.asof_utc),
            "",
            "Regime changed",
            shifted_line,
            "",
            "Posture",
            posture,
        ]
        if vix_line:
            lines.extend(["", "Volatility", vix_line])
        return "REGIME SHIFT", "\n".join(lines)

    lines = [
        _time_line(event.asof_utc),
        "",
        "Volatility jumped fast",
        "Review market tone",
        "",
        "Posture",
        posture,
    ]
    if vix_line:
        lines.extend(["", "Volatility", vix_line])
    return "VIX SPIKE", "\n".join(lines)


def _format_failure(event: AlertEvent) -> tuple[str, str]:
    label = _mode_label(event.notify_mode)
    title = f"{label} FAILED"
    body = "\n".join([
        _time_line(event.asof_utc),
        "",
        "Failure",
        _clean_reason(event.failure_reason or "unknown error"),
    ])
    return title, body


def _format_halt(event: AlertEvent) -> tuple[str, str]:
    lines = [
        _time_line(event.asof_utc),
        "",
        "Macro data invalid",
    ]
    if event.halt_reason:
        lines.append(_clean_reason(event.halt_reason))
    return "SYSTEM HALT", "\n".join(lines)


def _format_premarket(event: AlertEvent) -> tuple[str, str]:
    if _focus_candidates(event):
        return _format_watchlist_update(event)
    return _format_no_trade(event)


def _format_no_trade(event: AlertEvent) -> tuple[str, str]:
    lines = [_time_line(event.asof_utc), ""]
    lines.extend(_no_trade_context(event))
    return "NO TRADE", "\n".join(lines)


def _format_watchlist_update(event: AlertEvent) -> tuple[str, str]:
    lines = [_time_line(event.asof_utc), "", "Top Focus"]
    lines.extend(_focus_candidates(event)[:3])
    bias_line = _display_bias(event.regime)
    if bias_line:
        lines.extend(["", "Bias", bias_line])
    return "WATCHLIST UPDATE", "\n".join(lines)


def _format_setup_ready(event: AlertEvent) -> tuple[str, str]:
    trade = _qualified_focus(event)
    assert trade is not None
    direction = trade.direction.upper()
    title = f"{trade.symbol} {direction} READY"
    lines = [
        _time_line(event.asof_utc),
        "",
        _setup_ready_line(direction),
        _direction_context(direction, event.regime),
        "Defined risk",
        "",
        "Trigger",
        trade.symbol,
    ]
    invalidation = _invalidation_line(event, trade.symbol, direction)
    if invalidation:
        lines.extend(["", "Invalidation", invalidation])
    return title, "\n".join(lines)


def _format_setup_forming(event: AlertEvent) -> tuple[str, str]:
    symbol, direction, reason = _forming_focus(event)
    assert symbol is not None and direction is not None and reason is not None
    title = f"{symbol} {direction} FORMING"
    lines = [
        _time_line(event.asof_utc),
        "",
        reason,
        _direction_context(direction, event.regime),
        _forming_context_line(direction, event.regime),
        "",
        "Watch",
        symbol,
    ]
    invalidation = _invalidation_line(event, symbol, direction)
    if invalidation:
        lines.extend(["", "Invalidation", invalidation])
    return title, "\n".join(lines)


def _format_session_check(event: AlertEvent) -> tuple[str, str]:
    title = _session_check_title(event.notify_mode)
    lines = [_time_line(event.asof_utc), ""]
    lines.extend(_session_context(event))
    leaders = _focus_candidates(event)[:2]
    if leaders:
        lines.extend(["", "Leaders", *leaders])
    lines.extend(["", "Posture", _session_posture(event)])
    return title, "\n".join(lines)


def _no_trade_context(event: AlertEvent) -> list[str]:
    regime = event.regime
    lines: list[str] = []
    lines.append(_no_trade_state_line(regime))

    session_line = _session_line(event)
    if session_line:
        lines.append(session_line)

    vix_line = _vix_line(regime)
    if vix_line and event.notify_mode in {None, NOTIFY_PREMARKET, NOTIFY_ORB_TRAJECTORY, NOTIFY_MIDMORNING, NOTIFY_POWER_HOUR}:
        lines.append(vix_line)

    bias_line = _display_bias(regime)
    if bias_line:
        lines.append(bias_line)

    validation = event.validation_summary
    if validation is not None and event.notify_mode == NOTIFY_PREMARKET and validation.symbols_attempted:
        lines.append(f"{validation.symbols_validated}/{validation.symbols_attempted} validated")

    return lines[:5]


def _session_context(event: AlertEvent) -> list[str]:
    regime = event.regime
    lines = []
    if regime is None:
        return ["No market read", "Stay selective"]
    if regime.regime == CHAOTIC:
        return ["Chaotic market", "No expansion"]
    if regime.posture == STAY_FLAT:
        lines.append("Market steady")
        lines.append("No clean expansion")
    elif regime.regime == RISK_OFF:
        lines.append("Pressure remains")
        lines.append("Short setups favored")
    else:
        lines.append("Trend intact")
        lines.append("Selective continuation")
    return lines


def _session_posture(event: AlertEvent) -> str:
    regime = event.regime
    if regime is None or regime.regime == CHAOTIC or regime.posture == STAY_FLAT:
        return "Stay flat"
    if regime.posture == NEUTRAL_PREMIUM:
        return "Stay selective"
    if regime.posture == DEFENSIVE_SHORT:
        return "Lean short"
    return "Lean long"


def _focus_candidates(event: AlertEvent) -> list[str]:
    lines: list[str] = []
    qual = event.qualification_summary
    if qual is not None:
        for trade in qual.qualified_trades[:3]:
            lines.append(f"{trade.symbol} - ready")
        for watch in qual.watchlist[:3 - len(lines)]:
            lines.append(f"{watch.symbol} - {_watch_reason(watch)}")
    watch_summary = event.watch_summary
    if watch_summary is not None and len(lines) < 3:
        for item in watch_summary.watchlist:
            line = f"{item.symbol} - {_watch_item_phrase(item)}"
            if line not in lines:
                lines.append(line)
            if len(lines) == 3:
                break
    return lines


def _qualified_focus(event: AlertEvent) -> Optional[QualificationResult]:
    qual = event.qualification_summary
    if qual is None or not qual.qualified_trades:
        return None
    return qual.qualified_trades[0]


def _forming_focus(event: AlertEvent) -> tuple[Optional[str], Optional[str], Optional[str]]:
    qual = event.qualification_summary
    if qual is not None and qual.watchlist:
        watch = qual.watchlist[0]
        return watch.symbol, watch.direction.upper(), _watch_reason(watch).capitalize()

    watch_summary = event.watch_summary
    if watch_summary is not None and watch_summary.watchlist:
        item = watch_summary.watchlist[0]
        return item.symbol, item.bias.upper(), _watch_item_phrase(item).capitalize()

    return None, None, None


def _mode_label(notify_mode: Optional[str]) -> str:
    return {
        NOTIFY_PREMARKET: "PREMARKET",
        NOTIFY_ORB_TRAJECTORY: "EARLY SESSION",
        NOTIFY_POST_ORB: "POST-ORB",
        NOTIFY_MIDMORNING: "MIDDAY",
        NOTIFY_POWER_HOUR: "POWER HOUR",
        NOTIFY_HOURLY: "HOURLY",
        None: "ALERT",
    }.get(notify_mode, str(notify_mode).upper())


def _session_check_title(notify_mode: Optional[str]) -> str:
    return {
        NOTIFY_MIDMORNING: "MIDDAY CHECK",
        NOTIFY_POWER_HOUR: "POWER HOUR CHECK",
        NOTIFY_ORB_TRAJECTORY: "EARLY SESSION CHECK",
    }.get(notify_mode, "CHECK")


def _time_line(asof_utc: datetime) -> str:
    local = asof_utc.astimezone(LOCAL_TZ)
    return local.strftime("%I:%M %p").lstrip("0")


def _display_bias(regime: Optional[RegimeState]) -> Optional[str]:
    if regime is None:
        return None
    bias = regime_bias(regime)
    if bias == "LONG":
        return "Leaning long"
    if bias == "SHORT":
        return "Leaning short"
    if bias == "BALANCED":
        return "Balanced bias"
    if bias == "NO TRADE":
        return "Stay flat"
    return None


def _session_line(event: AlertEvent) -> Optional[str]:
    if event.notify_mode == NOTIFY_PREMARKET:
        return "Off session"
    watch_summary = event.watch_summary
    if watch_summary is None or watch_summary.session is None:
        return None
    return {
        "MORNING": "Morning session",
        "MIDDAY": "Midday session",
        "POWER_HOUR": "Power hour",
    }.get(watch_summary.session, watch_summary.session.replace("_", " ").title())


def _vix_line(regime: Optional[RegimeState]) -> Optional[str]:
    if regime is None or regime.vix_level is None:
        return None
    change = regime.vix_pct_change * 100 if regime.vix_pct_change is not None else 0.0
    return f"VIX {regime.vix_level:.1f} ({change:+.1f}%)"


def _no_trade_state_line(regime: Optional[RegimeState]) -> str:
    if regime is None:
        return "No market read - stay flat"
    if regime.regime == CHAOTIC:
        return "Chaotic market - stay flat"
    if regime.regime == NEUTRAL:
        return "Neutral market - stay flat"
    if regime.posture == STAY_FLAT and regime.regime == RISK_ON:
        return "Risk-on tape - stay flat"
    if regime.posture == STAY_FLAT and regime.regime == RISK_OFF:
        return "Risk-off tape - stay flat"
    if regime.posture == STAY_FLAT:
        return "No edge - stay flat"
    return "Stay selective"


def _watch_reason(watch: QualificationResult) -> str:
    reason = _clean_reason(watch.watchlist_reason or "setup forming")
    if len(reason) > 30:
        return "setup forming"
    return reason


def _watch_item_phrase(item: WatchItem) -> str:
    structure = item.structure.lower().replace("_", " ")
    if item.bias.upper() == "SHORT":
        return f"{structure} building"
    return f"{structure} building"


def _clean_reason(reason: str) -> str:
    cleaned = " ".join((reason or "").replace("_", " ").replace("=", " ").split())
    replacements = {
        "off session": "Off session",
        "stay flat": "Stay flat",
        "balanced": "Balanced bias",
    }
    lower = cleaned.lower()
    for src, dst in replacements.items():
        if lower == src:
            return dst
    return cleaned


def _setup_ready_line(direction: str) -> str:
    return "Long setup ready" if direction == "LONG" else "Short setup ready"


def _direction_context(direction: str, regime: Optional[RegimeState]) -> str:
    if direction == "SHORT":
        return "Short bias"
    if regime is not None and regime.posture == NEUTRAL_PREMIUM:
        return "Selective long bias"
    return "Long bias"


def _forming_context_line(direction: str, regime: Optional[RegimeState]) -> str:
    if direction == "SHORT":
        return "Trend pressure intact"
    if regime is not None and regime.posture in {AGGRESSIVE_LONG, CONTROLLED_LONG, NEUTRAL_PREMIUM}:
        return "Trend intact"
    return "Bias forming"


def _invalidation_line(event: AlertEvent, symbol: str, direction: str) -> Optional[str]:
    watch_summary = event.watch_summary
    if watch_summary is None:
        return None
    item = next((entry for entry in watch_summary.watchlist if entry.symbol == symbol), None)
    if item is None:
        return None
    if item.level == "VWAP":
        return "Lose VWAP" if direction == "LONG" else "Reclaim VWAP"
    if item.level == "ORB":
        return "Back inside ORB" if direction == "LONG" else "Back inside ORB"
    return f"Lose {item.level}" if direction == "LONG" else f"Reclaim {item.level}"
