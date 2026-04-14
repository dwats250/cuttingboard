"""Shared compact output formatting for notifications and report summaries."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from cuttingboard.qualification import QualificationSummary
from cuttingboard.regime import RegimeState
from cuttingboard.validation import ValidationSummary


SYSTEM_NAME = "CUTTINGBOARD"
OUTCOME_TRADE = "TRADE"
OUTCOME_NO_TRADE = "NO_TRADE"
OUTCOME_HALT = "HALT"


def build_output_summary(
    *,
    date_str: str,
    outcome: str,
    regime: Optional[RegimeState] = None,
    validation_summary: Optional[ValidationSummary] = None,
    qualification_summary: Optional[QualificationSummary] = None,
    report_path: Optional[str] = None,
    halt_reason: Optional[str] = None,
) -> dict[str, Any]:
    qual = qualification_summary
    validated = validation_summary.symbols_validated if validation_summary else None
    total = validation_summary.symbols_attempted if validation_summary else None
    qualified_symbols = [trade.symbol for trade in (qual.qualified_trades if qual else [])]

    return {
        "date": date_str,
        "outcome": outcome,
        "regime": regime.regime if regime else None,
        "posture": regime.posture if regime else None,
        "confidence": regime.confidence if regime else None,
        "net_score": regime.net_score if regime else None,
        "symbols_validated": validated,
        "symbols_total": total,
        "qualified_count": qual.symbols_qualified if qual else len(qualified_symbols),
        "vix_level": regime.vix_level if regime else None,
        "report_path": report_path,
        "regime_failure_reason": qual.regime_failure_reason if qual else None,
        "regime_short_circuited": qual.regime_short_circuited if qual else False,
        "halt_reason": halt_reason,
        "qualified_symbols": qualified_symbols,
    }


def format_ntfy_message(summary: Mapping[str, Any]) -> str:
    outcome = str(summary.get("outcome") or "").upper()
    lines = [_title_line(summary), format_status_line(summary)]

    if outcome == OUTCOME_TRADE:
        count_line = format_trade_counts_line(summary)
        if count_line:
            lines.append(count_line)
        top_line = summarize_top_symbols(summary)
        if top_line:
            lines.append(top_line)
    else:
        reason_line = format_reason_line(summary)
        if reason_line:
            lines.append(reason_line)
        count_line = format_validation_line(summary)
        if count_line:
            lines.append(count_line)

    report_line = format_report_line(summary)
    if report_line:
        lines.append(report_line)

    return "\n".join(line for line in lines if line)


def format_report_summary_lines(summary: Mapping[str, Any]) -> list[str]:
    lines = [format_status_line(summary)]
    outcome = str(summary.get("outcome") or "").upper()
    if outcome == OUTCOME_TRADE:
        count_line = format_trade_counts_line(summary)
    else:
        count_line = format_validation_line(summary)
    if count_line:
        lines.append(count_line)
    return [line for line in lines if line]


def format_trade_notification(summary: Mapping[str, Any]) -> str:
    return format_ntfy_message({**dict(summary), "outcome": OUTCOME_TRADE})


def format_no_trade_notification(summary: Mapping[str, Any]) -> str:
    return format_ntfy_message({**dict(summary), "outcome": OUTCOME_NO_TRADE})


def summarize_top_symbols(summary: Mapping[str, Any], limit: int = 3) -> str:
    raw_symbols = summary.get("qualified_symbols") or []
    symbols = [str(symbol) for symbol in raw_symbols if symbol][:limit]
    if not symbols:
        return ""
    return f"Top: {', '.join(symbols)}"


def summarize_reason(summary: Mapping[str, Any]) -> str:
    regime_reason = summary.get("regime_failure_reason")
    if summary.get("regime_short_circuited") and regime_reason:
        reason = str(regime_reason)
        if "posture" in reason.lower() or "short-circuit" in reason.lower():
            return "regime short-circuited"
        return _clean_reason(reason)

    for raw_reason in (summary.get("halt_reason"), regime_reason):
        cleaned = _clean_reason(raw_reason)
        if cleaned:
            return cleaned
    return ""


def format_status_line(summary: Mapping[str, Any]) -> str:
    pieces = [_display_outcome(summary.get("outcome"))]
    for key in ("regime", "posture"):
        value = summary.get(key)
        if value:
            pieces.append(str(value))

    confidence = summary.get("confidence")
    if confidence is not None:
        pieces.append(f"conf {_format_confidence(confidence)}")

    net_score = summary.get("net_score")
    if net_score is not None:
        pieces.append(f"net {_format_net_score(net_score)}")

    return " | ".join(piece for piece in pieces if piece)


def format_trade_counts_line(summary: Mapping[str, Any]) -> str:
    qualified = summary.get("qualified_count")
    denominator = summary.get("symbols_validated")
    if denominator is None:
        denominator = summary.get("symbols_total")

    pieces = []
    if qualified is not None or denominator is not None:
        qualified_value = int(qualified or 0)
        if denominator is None:
            pieces.append(f"Qualified {qualified_value}")
        else:
            pieces.append(f"Qualified {qualified_value}/{int(denominator)}")

    vix_segment = _format_vix_segment(summary.get("vix_level"))
    if vix_segment:
        pieces.append(vix_segment)
    return " | ".join(pieces)


def format_validation_line(summary: Mapping[str, Any]) -> str:
    validated = summary.get("symbols_validated")
    total = summary.get("symbols_total")
    pieces = []

    if validated is not None or total is not None:
        if validated is None and total is not None:
            validated = total
        if total is None and validated is not None:
            total = validated
        pieces.append(f"Validated {int(validated)}/{int(total)}")

    vix_segment = _format_vix_segment(summary.get("vix_level"))
    if vix_segment:
        pieces.append(vix_segment)
    return " | ".join(pieces)


def format_reason_line(summary: Mapping[str, Any]) -> str:
    reason = summarize_reason(summary)
    if not reason:
        return ""
    return f"Reason: {reason}"


def format_report_line(summary: Mapping[str, Any]) -> str:
    report_path = summary.get("report_path")
    if not report_path:
        return ""
    return f"Report: {report_path}"


def _title_line(summary: Mapping[str, Any]) -> str:
    date_str = summary.get("date") or "unknown-date"
    return f"{SYSTEM_NAME} {date_str}"


def _display_outcome(outcome: Any) -> str:
    value = str(outcome or OUTCOME_NO_TRADE).upper().replace("_", " ")
    return value


def _format_confidence(value: Any) -> str:
    return f"{float(value):.2f}"


def _format_net_score(value: Any) -> str:
    return f"{int(value):+d}"


def _format_vix_segment(value: Any) -> str:
    if value is None:
        return ""
    return f"VIX {float(value):.1f}"


def _clean_reason(reason: Any) -> str:
    if reason is None:
        return ""
    cleaned = " ".join(str(reason).split())
    if not cleaned:
        return ""
    if cleaned.startswith("{") or cleaned.startswith("["):
        return "details in report"
    if len(cleaned) > 80:
        cleaned = cleaned[:77].rstrip() + "..."
    return cleaned
