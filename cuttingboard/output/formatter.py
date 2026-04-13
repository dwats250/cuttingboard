"""CLI formatter for SystemReport."""

from cuttingboard.output.models import SystemReport


def format_system_report(report: SystemReport) -> str:
    lines = [
        "=== CUTTINGBOARD REPORT ===",
        f"Timestamp: {report.timestamp}",
        f"Posture: {report.posture}",
        f"Market: {report.market_quality}",
        "",
        "TOP TRADES",
    ]

    if report.top_trades:
        for index, trade in enumerate(report.top_trades, start=1):
            lines.append(
                f"{index}. {trade.ticker} | {trade.structure} | RR {trade.rr:.2f} | "
                f"{trade.spread_type} ({trade.duration})"
            )

    lines.extend(["", "WATCHLIST"])
    if report.watchlist:
        for trade in report.watchlist:
            lines.append(f"- {trade.ticker} | {trade.structure} | RR {trade.rr:.2f}")

    lines.extend(["", "REJECTED (SUMMARY)"])
    for reason, count in report.summary.rejection_breakdown.items():
        lines.append(f"{reason}: {count}")

    return "\n".join(lines)
