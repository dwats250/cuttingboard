"""
Notification formatters for scheduled notify-mode runs.

Public API is kept here for callers that import `cuttingboard.notifications`.
The alert renderer lives in formatter.py.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

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
    LOCAL_TZ,
    OUTCOME_TRADE,
    _ET_TZ,
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
_LIFECYCLE_HIGH_GRADES = frozenset({"A+", "A", "B"})


def _hhmm(asof_utc: datetime) -> str:
    return asof_utc.astimezone(_ET_TZ).strftime("%H:%M")


def _pt_clock(asof_utc: datetime) -> str:
    """PT 12-hour clock with leading zero stripped (e.g. "9:20 AM")."""
    return asof_utc.astimezone(LOCAL_TZ).strftime("%I:%M %p").lstrip("0")


def _compact_label(value: object) -> str:
    return str(value or "UNKNOWN").replace("_", " ").upper()


def _regime_line(regime: Optional[RegimeState]) -> str:
    if regime is None:
        return "Regime: unknown"
    return f"Regime: {_compact_label(regime.regime)}"


_MACRO_TAPE_SYMBOLS: tuple[tuple[str, str, str], ...] = (
    ("^VIX", "VIX", "level1"),
    ("DX-Y.NYB", "DXY", "level1"),
    ("^TNX", "10Y", "level2"),
    ("BTC-USD", "BTC", "btc"),
)

_TRADABLES_ORDER: tuple[str, ...] = ("SPY", "QQQ", "GLD", "SLV", "XLE", "GDX")


def _arrow(pct_decimal: Optional[float]) -> str:
    if pct_decimal is None:
        return "↑"
    return "↓" if pct_decimal < 0 else "↑"


def _fmt_level(price: float, fmt: str) -> str:
    if fmt == "level2":
        return f"{price:.2f}"
    if fmt == "btc":
        if price >= 1000:
            return f"{price / 1000:.1f}K"
        return f"{price:.0f}"
    return f"{price:.1f}"


def _macro_cell(label: str, symbol: str, level_fmt: str, quotes: dict) -> str:
    q = quotes.get(symbol) if quotes else None
    if q is None or q.price is None:
        return f"{label} n/a"
    level = _fmt_level(q.price, level_fmt)
    pct = q.pct_change_decimal
    if pct is None:
        return f"{label} {level}"
    arrow = _arrow(pct)
    abs_pct = abs(pct) * 100
    return f"{label} {level} {arrow}{abs_pct:.1f}%"


def _macro_tape_block(normalized_quotes: dict) -> list[str]:
    cells = [
        _macro_cell(label, symbol, level_fmt, normalized_quotes)
        for symbol, label, level_fmt in _MACRO_TAPE_SYMBOLS
    ]
    if all(cell.endswith(" n/a") for cell in cells):
        return []
    row1 = f"{cells[0]} | {cells[1]}"
    row2 = f"{cells[2]} | {cells[3]}"
    return ["Macro Tape:", row1, row2]


def _tradables_block(normalized_quotes: dict) -> list[str]:
    available: list[str] = []
    for symbol in _TRADABLES_ORDER:
        q = normalized_quotes.get(symbol) if normalized_quotes else None
        if q is None or q.price is None:
            continue
        available.append(f"{symbol} {q.price:.2f}")
    if not available:
        return []
    rows: list[str] = []
    for i in range(0, len(available), 2):
        pair = available[i : i + 2]
        rows.append(" | ".join(pair))
    return ["Tradables:", *rows]


def _confidence_line(regime: Optional[RegimeState]) -> str:
    if regime is None:
        return "Confidence: unknown"
    return f"Confidence: {regime.confidence:.2f}"


def _action_label(
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
    canonical_outcome: Optional[str] = None,
) -> str:
    if validation_summary.system_halted:
        return "HALT"
    qualified = (
        qualification_summary is not None
        and qualification_summary.symbols_qualified > 0
    )
    flat = regime is None or regime.posture == STAY_FLAT
    if qualified and not flat and canonical_outcome == OUTCOME_TRADE:
        return "TRADE"
    if qualified and not flat:
        return "MONITOR SETUP"
    if flat:
        return "STAY FLAT"
    return "MONITOR"


def _focus_tokens(
    qualification_summary: Optional[QualificationSummary],
    candidate_lines: tuple[str, ...],
) -> list[tuple[str, str]]:
    """Deterministic ordered focus tokens (SYMBOL, DIR), dedup-preserving order."""
    tokens: dict[tuple[str, str], None] = {}
    if qualification_summary is not None:
        for trade in qualification_summary.qualified_trades:
            if not is_tradable_symbol(trade.symbol):
                continue
            tokens[(trade.symbol.upper(), trade.direction.upper())] = None
            if len(tokens) >= 3:
                return list(tokens)
        for watch in qualification_summary.watchlist:
            if not is_tradable_symbol(watch.symbol):
                continue
            tokens[(watch.symbol.upper(), watch.direction.upper())] = None
            if len(tokens) >= 3:
                return list(tokens)
    for line in candidate_lines:
        parsed = _parse_candidate_line(line)
        if parsed is None:
            continue
        symbol, direction, _ = parsed
        tokens[(symbol, direction)] = None
        if len(tokens) >= 3:
            return list(tokens)
    return list(tokens)


def _focus_line(tokens: list[tuple[str, str]]) -> str:
    if not tokens:
        return "Focus: no active setup"
    rendered = ", ".join(f"{sym} {direction}" for sym, direction in tokens)
    return f"Focus: {rendered}"


def _blockers_line_opt(
    qualification_summary: Optional[QualificationSummary],
) -> Optional[str]:
    if qualification_summary is None:
        return None
    tags: dict[str, None] = {}
    for item in qualification_summary.watchlist:
        gates_failed = getattr(item, "gates_failed", ()) or ()
        for tag in gates_failed:
            text = _as_clean_string(tag)
            if text:
                tags[text] = None
    if not tags:
        return None
    return f"Blockers: {', '.join(tags)}"


def _pending_lines(
    focus_tokens_list: list[tuple[str, str]],
    candidate_lines: tuple[str, str],
) -> list[str]:
    """Render `Pending confirmation:` block only when focus symbols exist.

    Trigger conditions are attached to a concrete symbol via parsed candidate
    lines (structure tag from `SYMBOL | DIR | STRUCTURE | RR`). No generic
    regime-keyed boilerplate.
    """
    if not focus_tokens_list:
        return []
    focus_keys = {(sym, direction) for sym, direction in focus_tokens_list}
    entries: list[str] = []
    for line in candidate_lines:
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 4:
            continue
        symbol = parts[0].upper()
        direction = parts[1].upper()
        structure = _as_clean_string(parts[2])
        if not is_tradable_symbol(symbol):
            continue
        if (symbol, direction) not in focus_keys:
            continue
        if not structure:
            continue
        entries.append(f"{symbol}: {structure.lower()} confirmation")
        if len(entries) >= 3:
            break
    if not entries:
        return []
    return ["Pending confirmation:", *entries]


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
    canonical_outcome: Optional[str] = None,
    normalized_quotes: Optional[dict[str, NormalizedQuote]] = None,
) -> tuple[str, str]:
    del halt_reason
    pt = _pt_clock(asof_utc)
    parsed = tuple(
        parsed_line
        for line in candidate_lines
        if (parsed_line := _parse_candidate_line(line)) is not None
    )
    action = _action_label(
        regime, validation_summary, qualification_summary, canonical_outcome
    )

    if action == "TRADE" and parsed:
        first_symbol, first_direction, _ = parsed[0]
        title = f"{first_direction} {first_symbol} {pt}"
    elif action == "TRADE":
        title = f"TRADE {pt}"
    elif action == "HALT":
        title = f"HALT {pt}"
    elif action == "MONITOR SETUP":
        title = f"MONITOR SETUP {pt}"
    elif action == "MONITOR":
        title = f"MONITOR {pt}"
    else:
        title = f"STAY FLAT — {pt} PT"

    has_candidates = bool(
        qualification_summary is not None
        and (qualification_summary.symbols_qualified or qualification_summary.symbols_watchlist)
    )
    reason = _hourly_reason(
        regime,
        validation_summary,
        qualification_summary,
        has_candidates=has_candidates,
    )
    focus = _focus_tokens(qualification_summary, candidate_lines)
    quotes = normalized_quotes or {}

    lines: list[str] = [
        _regime_line(regime),
        _confidence_line(regime),
        f"Reason: {reason}",
    ]
    blockers = _blockers_line_opt(qualification_summary)
    if blockers is not None:
        lines.append(blockers)

    macro_block = _macro_tape_block(quotes)
    if macro_block:
        lines.append("")
        lines.extend(macro_block)

    tradables_block = _tradables_block(quotes)
    if tradables_block:
        lines.append("")
        lines.extend(tradables_block)

    lines.append("")
    lines.append(_focus_line(focus))

    pending = _pending_lines(focus, candidate_lines)
    if pending:
        lines.extend(["", *pending])

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
