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
from cuttingboard.watch import WatchSummary

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
    alert_sent: bool,
    report_path: str,
    router_mode: str = "",
    energy_score: float = 0.0,
    index_score: float = 0.0,
    watch_summary: Optional[WatchSummary] = None,
    suppressed_candidates: Optional[list] = None,
    intraday_state_context: Optional[dict[str, dict]] = None,
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
        router_mode=router_mode,
        energy_score=energy_score,
        index_score=index_score,
        validation_summary=validation_summary,
        qualification_summary=qualification_summary,
        watch_summary=watch_summary,
        option_setups=option_setups,
        suppressed_candidates=suppressed_candidates,
        intraday_state_context=intraday_state_context,
        halt_reason=halt_reason,
        alert_sent=alert_sent,
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
    alert_sent: bool,
    report_path: str,
    router_mode: str = "",
    energy_score: float = 0.0,
    index_score: float = 0.0,
    watch_summary: Optional[WatchSummary] = None,
    suppressed_candidates: Optional[list] = None,
    intraday_state_context: Optional[dict[str, dict]] = None,
) -> dict:
    qual = qualification_summary

    qualified_list = []
    watchlist_list = []
    near_a_plus_list = []
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
            meta = (intraday_state_context or {}).get(r.symbol)
            if meta is not None:
                entry["downside_permission"] = meta.get("downside_permission")
                entry["intraday_state"] = meta.get("intraday_state")
                entry["intraday_state_available"] = meta.get("intraday_state_available")
            qualified_list.append(entry)

        for r in qual.watchlist:
            entry = {
                "symbol": r.symbol,
                "reason": r.watchlist_reason,
            }
            meta = (intraday_state_context or {}).get(r.symbol)
            if meta is not None:
                entry["downside_permission"] = meta.get("downside_permission")
                entry["intraday_state"] = meta.get("intraday_state")
                entry["intraday_state_available"] = meta.get("intraday_state_available")
            near_a_plus_list.append(entry)

        excluded_dict = dict(qual.excluded)

    if watch_summary is not None:
        for item in watch_summary.watchlist:
            watchlist_list.append({
                "symbol": item.symbol,
                "score": item.score,
                "structure_note": item.structure_note,
                "missing_conditions": list(item.missing_conditions),
            })

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
        "router_mode":            router_mode,
        "energy_score":           round(energy_score, 2),
        "index_score":            round(index_score, 2),

        # Validation
        "symbols_validated":      validation_summary.symbols_validated,
        "symbols_total":          validation_summary.symbols_attempted,
        "symbols_failed":         validation_summary.symbols_failed,

        # Qualification
        "symbols_qualified":      qual.symbols_qualified if qual else 0,
        "symbols_near_a_plus":    qual.symbols_watchlist if qual else 0,
        "symbols_watchlist":      len(watch_summary.watchlist) if watch_summary else 0,
        "symbols_excluded":       qual.symbols_excluded if qual else 0,
        "regime_short_circuited": qual.regime_short_circuited if qual else None,
        "regime_failure_reason":  qual.regime_failure_reason if qual else None,

        # Trades
        "qualified_trades":       qualified_list,
        "watchlist":              watchlist_list,
        "near_a_plus":            near_a_plus_list,
        "excluded_symbols":       excluded_dict,
        "suppressed_candidates":  list(suppressed_candidates or []),

        # Run metadata
        "halt_reason":            halt_reason,
        "alert_sent":             alert_sent,
        "report_path":            report_path,
    }

    return record


# ---------------------------------------------------------------------------
# Notification audit
# ---------------------------------------------------------------------------

def write_notification_audit(
    *,
    transport: str,
    alert_title: str,
    attempted: bool,
    success: bool,
    http_status: Optional[int] = None,
    error: Optional[str] = None,
    reason: Optional[str] = None,
    message_preview: Optional[str] = None,
    retry_count: int = 0,
) -> dict:
    """Write one notification attempt record to audit.jsonl.

    Called unconditionally from send_telegram — every attempt (skip, success,
    HTTP failure, exception) produces exactly one record.

    Fields
    ------
    attempted   — False means the send was skipped before any HTTP call.
    success     — True only when HTTP 200 was received.
    http_status — Set when an HTTP response was received (success or failure).
    error       — Exception message or HTTP error body excerpt.
    reason      — Human-readable explanation for skip/failure.
    retry_count — Number of retries made (0 = first attempt succeeded/failed, 1 = one retry).
    """
    record: dict = {
        "event": "notification",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "transport": transport,
        "alert_title": alert_title,
        "attempted": attempted,
        "success": success,
        "http_status": http_status,
        "error": error,
        "reason": reason,
        "retry_count": retry_count,
        "message_preview": (message_preview[:120] if message_preview else None),
    }
    _append_record(record)
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
