"""
Audit log — append-only JSONL.

Every pipeline run writes exactly one record to logs/audit.jsonl.
Records are never overwritten or deleted. sort_keys=True ensures
deterministic field ordering across runs.

Entry point: write_audit_record(...)
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from cuttingboard.options import OptionSetup
from cuttingboard.qualification import QualificationSummary
from cuttingboard.regime import RegimeState
from cuttingboard.validation import ValidationSummary

logger = logging.getLogger(__name__)

AUDIT_LOG_PATH = "logs/audit.jsonl"


def write_audit_record(
    run_at_utc: datetime,
    date_str: str,
    outcome: str,                                    # "TRADE" | "NO_TRADE" | "HALT"
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
    option_setups: list[OptionSetup],
    halt_reason: Optional[str],
    pushover_sent: bool,
    report_path: str,
) -> dict:
    """Build and append one audit record to logs/audit.jsonl.

    The record is serialized with sort_keys=True. The log file is opened
    in append mode — existing records are never modified. The directory
    is created if it does not exist.

    Returns the record dict (for testing and debugging).
    """
    record = _build_record(
        run_at_utc=run_at_utc,
        date_str=date_str,
        outcome=outcome,
        regime=regime,
        validation_summary=validation_summary,
        qualification_summary=qualification_summary,
        option_setups=option_setups,
        halt_reason=halt_reason,
        pushover_sent=pushover_sent,
        report_path=report_path,
    )

    _append_record(record)
    return record


# ---------------------------------------------------------------------------
# Record builder
# ---------------------------------------------------------------------------

def _build_record(
    run_at_utc: datetime,
    date_str: str,
    outcome: str,
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
    option_setups: list[OptionSetup],
    halt_reason: Optional[str],
    pushover_sent: bool,
    report_path: str,
) -> dict:
    qual = qualification_summary

    qualified_list = []
    watchlist_list = []
    excluded_dict: dict = {}

    if qual is not None:
        for r in qual.qualified_trades:
            setup = next((s for s in option_setups if s.symbol == r.symbol), None)
            entry: dict = {
                "symbol":     r.symbol,
                "direction":  r.direction,
                "strategy":   setup.strategy if setup else None,
                "structure":  setup.structure if setup else None,
                "dte":        setup.dte if setup else None,
                "contracts":  r.max_contracts,
                "dollar_risk": r.dollar_risk,
            }
            qualified_list.append(entry)

        for r in qual.watchlist:
            watchlist_list.append({
                "symbol": r.symbol,
                "reason": r.watchlist_reason,
            })

        excluded_dict = dict(qual.excluded)

    record: dict = {
        "run_at_utc":             run_at_utc.isoformat(),
        "date":                   date_str,
        "outcome":                outcome,

        # Regime
        "regime":                 regime.regime if regime else None,
        "posture":                regime.posture if regime else None,
        "confidence":             round(regime.confidence, 4) if regime else None,
        "net_score":              regime.net_score if regime else None,
        "vix_level":              regime.vix_level if regime else None,

        # Validation
        "symbols_validated":      validation_summary.symbols_validated,
        "symbols_total":          validation_summary.symbols_attempted,
        "symbols_failed":         validation_summary.symbols_failed,

        # Qualification
        "symbols_qualified":      qual.symbols_qualified if qual else 0,
        "symbols_watchlist":      qual.symbols_watchlist if qual else 0,
        "symbols_excluded":       qual.symbols_excluded if qual else 0,
        "regime_short_circuited": qual.regime_short_circuited if qual else None,
        "regime_failure_reason":  qual.regime_failure_reason if qual else None,

        # Trades
        "qualified_trades":       qualified_list,
        "watchlist":              watchlist_list,
        "excluded_symbols":       excluded_dict,

        # Run metadata
        "halt_reason":            halt_reason,
        "pushover_sent":          pushover_sent,
        "report_path":            report_path,
    }

    return record


# ---------------------------------------------------------------------------
# File writer
# ---------------------------------------------------------------------------

def _append_record(record: dict) -> None:
    """Serialize record to JSON and append to audit.jsonl."""
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)

    line = json.dumps(record, sort_keys=True, default=_json_default)

    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

    logger.info(f"Audit record written to {AUDIT_LOG_PATH}")


def _json_default(obj):
    """Fallback serializer for non-standard types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
