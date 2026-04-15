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
    NEUTRAL,
    NEUTRAL_PREMIUM,
    RISK_OFF,
    RISK_ON,
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
    NOTIFY_PREMARKET:      "PREMARKET",
    NOTIFY_ORB_TRAJECTORY: "EARLY SESSION",
    NOTIFY_POST_ORB:       "POST-ORB",
    NOTIFY_MIDMORNING:     "MID-SESSION",
    NOTIFY_POWER_HOUR:     "POWER HOUR",
}

_FALLBACK_WATCHLIST = ["SPY", "QQQ", "NVDA", "MU"]

_SUPPRESS_CONFIDENCE = 0.55
_SEND_CONFIDENCE = 0.60

# PT = UTC-7 (PDT). Display only — no pytz dependency.
_PT_OFFSET = timedelta(hours=-7)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ntfy_title(notify_mode: str, date_str: str) -> str:
    label = _MODE_LABELS.get(notify_mode, notify_mode.upper())
    return f"CUTTINGBOARD · {label}"


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

    if notify_mode == NOTIFY_PREMARKET:
        body = _fmt_premarket(regime, validation_summary, qualification_summary)
    elif notify_mode == NOTIFY_ORB_TRAJECTORY:
        body = _fmt_orb_trajectory(regime, validation_summary, normalized_quotes)
    elif notify_mode == NOTIFY_POST_ORB:
        body = _fmt_post_orb(regime, validation_summary, qualification_summary)
    elif notify_mode == NOTIFY_MIDMORNING:
        body = _fmt_midmorning(regime, validation_summary, qualification_summary)
    elif notify_mode == NOTIFY_POWER_HOUR:
        body = _fmt_power_hour(regime, validation_summary, qualification_summary)
    else:
        body = _fmt_premarket(regime, validation_summary, qualification_summary)

    return title, body


def format_failure_notification(notify_mode: str, date_str: str, reason: str) -> tuple[str, str]:
    label = _MODE_LABELS.get(notify_mode, notify_mode.upper())
    title = f"CUTTINGBOARD · {label} FAILED"
    body = f"CUTTINGBOARD · {_pt_now()}\n{label} SCAN FAILED\nReason: {reason}"
    return title, body


# ---------------------------------------------------------------------------
# Regime interpretation
# ---------------------------------------------------------------------------

def interpret_regime(regime: Optional[RegimeState]) -> str:
    """Deterministic one-line market read from regime state."""
    if regime is None:
        return "No regime data available"
    r, p = regime.regime, regime.posture
    vix = regime.vix_level

    if r == CHAOTIC:
        return "Tape in distress — no trade conditions"
    if p == AGGRESSIVE_LONG:
        return "Directional pressure building — risk-on tone"
    if p == CONTROLLED_LONG:
        return "Bullish bias confirmed — defined risk preferred"
    if p == DEFENSIVE_SHORT:
        return "Risk-off pressure — breakdown trades in play"
    if p == NEUTRAL_PREMIUM:
        return "Mixed signals — selective defined-risk only"
    # STAY_FLAT — differentiate by regime context
    if r == RISK_ON:
        return "Mild bullish lean — not confirmed"
    if r == RISK_OFF:
        return "Soft risk-off — watch for follow-through"
    if r == NEUTRAL:
        if vix is not None and vix > 25:
            return "Elevated VIX in mixed tape — stay flat"
        if vix is not None and vix >= 18:
            return "Mixed signals — selective defined-risk only"
    return "Mixed signals — no directional control"


def _what_would_change(regime: Optional[RegimeState]) -> list[str]:
    if regime is None:
        return ["Regime data required to assess"]
    table: dict[str, list[str]] = {
        STAY_FLAT: [
            "Clean ORB break + hold with volume",
            "EMA9 above EMA21 with momentum confirmation",
            "Net regime score >= +4",
        ],
        AGGRESSIVE_LONG: [
            "VIX spike > 15% or SPY reversal > 1.5%",
            "Net score drops below +3",
        ],
        CONTROLLED_LONG: [
            "EMA9 crosses below EMA21",
            "VIX rises above 25",
        ],
        DEFENSIVE_SHORT: [
            "VIX falls below 20 and net score improves above -2",
        ],
        NEUTRAL_PREMIUM: [
            "VIX moves outside 18-25 band",
            "Net score shifts beyond +/-3",
        ],
    }
    return table.get(regime.posture, ["Net score shift >= 3 in either direction"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _pt_now() -> str:
    pt = datetime.now(timezone.utc).astimezone(timezone(_PT_OFFSET))
    return pt.strftime("%Y-%m-%d %H:%M PT")


def _header_lines(regime: Optional[RegimeState]) -> list[str]:
    lines = [f"CUTTINGBOARD · {_pt_now()}"]
    if regime is not None:
        sign = "+" if regime.net_score >= 0 else ""
        lines.append(f"REGIME: {regime.regime}")
        lines.append(f"POSTURE: {regime.posture}")
        lines.append(f"CONFIDENCE: {regime.confidence:.2f}")
        lines.append(f"NET: {sign}{regime.net_score}")
    return lines


def _data_footer(
    validation_summary: ValidationSummary,
    regime: Optional[RegimeState],
) -> list[str]:
    vix_level = (
        f"{regime.vix_level:.1f}"
        if regime is not None and regime.vix_level is not None
        else "N/A"
    )
    vix_pct = (
        f" ({regime.vix_pct_change:+.1%})"
        if regime is not None and regime.vix_pct_change is not None
        else ""
    )
    return [
        "",
        f"VIX {vix_level}{vix_pct}",
        f"DATA  {validation_summary.symbols_validated}/{validation_summary.symbols_attempted} validated",
    ]


def _watchlist_symbols(qualification_summary: Optional[QualificationSummary]) -> list[str]:
    """Return watchlist symbols from qualification, or fallback list."""
    if qualification_summary is None:
        return _FALLBACK_WATCHLIST
    symbols = [r.symbol for r in qualification_summary.watchlist]
    if not symbols:
        symbols = [r.symbol for r in qualification_summary.qualified_trades]
    return symbols or _FALLBACK_WATCHLIST


def _trade_status_line(
    regime: Optional[RegimeState],
    qualification_summary: Optional[QualificationSummary],
) -> str:
    if regime is None or regime.regime == CHAOTIC:
        return "NO TRADE — chaotic conditions"
    if regime.posture == STAY_FLAT:
        return "STAY FLAT — edge not present"
    if qualification_summary is not None and qualification_summary.symbols_qualified > 0:
        return f"ACTIVE — {qualification_summary.symbols_qualified} setup(s) qualify"
    if qualification_summary is not None and qualification_summary.symbols_watchlist > 0:
        return "WATCH ONLY — structure forming, not qualified"
    return "NO TRADE — no qualifying setups"


def _session_label(pct: float) -> str:
    if pct > 0.015:
        return "extending"
    if pct > 0.005:
        return "holding"
    if pct > -0.005:
        return "mixed"
    if pct > -0.015:
        return "fading"
    return "failing"


# ---------------------------------------------------------------------------
# Mode formatters
# ---------------------------------------------------------------------------

def _fmt_premarket(
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
) -> str:
    lines = _header_lines(regime)
    lines.append("")

    lines.append("MARKET READ")
    lines.append(interpret_regime(regime))
    lines.append("")

    lines.append("TRADE STATUS")
    lines.append(_trade_status_line(regime, qualification_summary))
    lines.append("")

    lines.append("WATCHLIST")
    for sym in _watchlist_symbols(qualification_summary)[:4]:
        lines.append(f"  {sym}")
    lines.append("")

    lines.append("WHAT WOULD CHANGE THIS")
    for cond in _what_would_change(regime):
        lines.append(f"  {cond}")

    lines.extend(_data_footer(validation_summary, regime))
    return "\n".join(lines)


def _fmt_orb_trajectory(
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    normalized_quotes: dict[str, NormalizedQuote],
) -> str:
    lines = _header_lines(regime)
    lines.append("")

    lines.append("EARLY SESSION READ")
    for sym in ("SPY", "QQQ", "NVDA"):
        quote = normalized_quotes.get(sym)
        if quote is not None:
            pct = quote.pct_change_decimal
            sign = "+" if pct >= 0 else ""
            lines.append(f"  {sym:<6}  {sign}{pct:.1%} from open   {_session_label(pct)}")
    lines.append("")

    lines.append("READ")
    lines.append(interpret_regime(regime))

    lines.extend(_data_footer(validation_summary, regime))
    return "\n".join(lines)


def _fmt_post_orb(
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
) -> str:
    lines = _header_lines(regime)
    lines.append("")

    lines.append("MARKET READ")
    lines.append(interpret_regime(regime))
    lines.append("")

    watchlist = _watchlist_symbols(qualification_summary)
    if qualification_summary is not None or watchlist != _FALLBACK_WATCHLIST:
        lines.append("BEST STRUCTURES")
        for sym in watchlist[:3]:
            lines.append(f"  {sym}")
        lines.append("")

    lines.append("TRADE STATUS")
    if regime is not None and regime.posture == STAY_FLAT:
        lines.append("No clean follow-through — do not force it")
    elif qualification_summary is not None and qualification_summary.symbols_qualified > 0:
        lines.append(f"{qualification_summary.symbols_qualified} setup(s) worth active attention")
    elif qualification_summary is not None and qualification_summary.symbols_watchlist > 0:
        lines.append("Structure forming — remain selective")
    else:
        lines.append("Still mostly chop — remain selective")

    lines.extend(_data_footer(validation_summary, regime))
    return "\n".join(lines)


def _fmt_midmorning(
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
) -> str:
    lines = _header_lines(regime)
    lines.append("")

    lines.append("SYNOPSIS")
    lines.append(_midmorning_synopsis(regime, qualification_summary))
    lines.append("")

    if qualification_summary is not None:
        watchlist = _watchlist_symbols(qualification_summary)
        if watchlist and watchlist != _FALLBACK_WATCHLIST:
            lines.append("ACTIVE WATCHES")
            for sym in watchlist[:3]:
                lines.append(f"  {sym}")
            lines.append("")

    lines.append("STATUS")
    if regime is not None and regime.posture != STAY_FLAT and regime.confidence >= _SEND_CONFIDENCE:
        lines.append("Morning thesis intact — stay selective")
    elif regime is not None and regime.confidence < _SUPPRESS_CONFIDENCE:
        lines.append("No meaningful continuation — attention should drop")
    else:
        lines.append("Stay selective — no forced entries")

    lines.extend(_data_footer(validation_summary, regime))
    return "\n".join(lines)


def _midmorning_synopsis(
    regime: Optional[RegimeState],
    qs: Optional[QualificationSummary],
) -> str:
    if regime is None:
        return "Data unavailable"
    if regime.regime == CHAOTIC:
        return "Tape in distress — no trade conditions"
    if regime.posture == STAY_FLAT and regime.confidence < _SUPPRESS_CONFIDENCE:
        return "No meaningful continuation — chop increasing"
    if regime.confidence >= _SEND_CONFIDENCE and qs and qs.symbols_watchlist > 0:
        return "Morning trend intact — leadership still narrow"
    if regime.confidence >= _SEND_CONFIDENCE:
        return "Directional bias holding — watch for confirmation"
    return "Early strength fading — chop increasing"


def _fmt_power_hour(
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
) -> str:
    lines = _header_lines(regime)
    lines.append("")

    lines.append("MARKET READ")
    lines.append(interpret_regime(regime))
    lines.append("")

    if qualification_summary is not None:
        watchlist = _watchlist_symbols(qualification_summary)
        if watchlist and watchlist != _FALLBACK_WATCHLIST:
            lines.append("BEST LATE SETUPS")
            for sym in watchlist[:3]:
                lines.append(f"  {sym}")
            lines.append("")

    lines.append("STATUS")
    has_watches = qualification_summary is not None and (
        qualification_summary.symbols_watchlist > 0
        or qualification_summary.symbols_qualified > 0
    )
    if regime is not None and regime.confidence >= _SEND_CONFIDENCE and has_watches:
        lines.append("Active attention warranted — entries only if confirmed")
    elif regime is not None and regime.posture == STAY_FLAT:
        lines.append("Broad tape weak — no reason to re-engage")
    else:
        lines.append("Stay selective — last hour, discipline required")

    lines.extend(_data_footer(validation_summary, regime))
    return "\n".join(lines)
