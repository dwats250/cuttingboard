"""Output package exposing both the legacy engine and PRD 5 report layer."""

from cuttingboard.output.formatter import format_system_report
from cuttingboard.output.legacy import (
    OUTCOME_HALT,
    OUTCOME_NO_TRADE,
    OUTCOME_TRADE,
    render_report,
    run_pipeline,
    send_ntfy,
    write_markdown,
    write_terminal,
)
from cuttingboard.output.models import RejectedTrade, SummaryStats, SystemReport, TradeOutput
from cuttingboard.output.report import generate_report

__all__ = [
    "OUTCOME_HALT",
    "OUTCOME_NO_TRADE",
    "OUTCOME_TRADE",
    "RejectedTrade",
    "SummaryStats",
    "SystemReport",
    "TradeOutput",
    "format_system_report",
    "generate_report",
    "render_report",
    "run_pipeline",
    "send_ntfy",
    "write_markdown",
    "write_terminal",
]
