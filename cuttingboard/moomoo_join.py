"""Join Moomoo NormalizedTrade rows against ``logs/audit.jsonl``.

Read-only: never mutates the audit log, the trade list, or any pipeline
state. For each input trade with a Cuttingboard-universe underlier,
attaches every same-day audit record that mentions the underlier in any
candidate-or-rejection field, plus deterministic blind-spot tags drawn
from a closed set.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from cuttingboard import config
from cuttingboard.audit import AUDIT_LOG_PATH
from cuttingboard.moomoo_parser import (
    CLASS_EQUITY,
    NormalizedTrade,
    OPTION_PUT,
    SIDE_SELL,
)


__all__ = [
    "EnrichedTrade",
    "enrich",
    "BLIND_GAP_DOWN_SHORT_SUPPRESSED",
    "BLIND_NOTIFY_MODE_ONLY",
    "BLIND_EXPANSION_DATA_INCOMPLETE_AMBIGUOUS",
    "BLIND_NO_AUDIT_FOR_DATE",
    "BLIND_UNDERLIER_NOT_IN_AUDIT_UNIVERSE",
]


BLIND_GAP_DOWN_SHORT_SUPPRESSED = "gap_down_short_suppressed"
BLIND_NOTIFY_MODE_ONLY = "notify_mode_only"
BLIND_EXPANSION_DATA_INCOMPLETE_AMBIGUOUS = "expansion_data_incomplete_ambiguous"
BLIND_NO_AUDIT_FOR_DATE = "no_audit_for_date"
BLIND_UNDERLIER_NOT_IN_AUDIT_UNIVERSE = "underlier_not_in_audit_universe"


def cuttingboard_universe() -> frozenset[str]:
    """Universe used for the ``in_universe`` flag per PRD-153 R2."""
    return frozenset(config.INDICES + config.COMMODITIES + config.HIGH_BETA)


@dataclass(frozen=True)
class EnrichedTrade:
    trade: NormalizedTrade
    in_universe: bool
    audit_records: list[dict]
    blind_spots: list[str]


# ---------------------------------------------------------------------------
# Audit log loading
# ---------------------------------------------------------------------------

def _is_pipeline_record(rec: dict) -> bool:
    """A pipeline run record carries ``run_at_utc`` and ``outcome``.

    Notification-event records (``audit.py:write_notification_audit``)
    omit ``outcome`` and carry ``event == "notification"`` instead.
    """
    return "run_at_utc" in rec and "outcome" in rec


def _parse_run_at(rec: dict) -> Optional[datetime]:
    raw = rec.get("run_at_utc")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def load_audit_records(audit_log_path: str) -> list[dict]:
    """Load pipeline run records from a JSONL audit file.

    Notification-event records are filtered out. Malformed JSON lines are
    silently skipped (the audit log is append-only and read-only here).
    Sparse-by-design per docs/audit_doctrine.md: ~1 record per trading
    day; intraday trades have no same-day pipeline record by design.
    """
    path = Path(audit_log_path)
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict) and _is_pipeline_record(rec):
                out.append(rec)
    return out


# ---------------------------------------------------------------------------
# Per-record symbol scans
# ---------------------------------------------------------------------------

def _entries_for(rec: dict, key: str) -> list[dict]:
    val = rec.get(key)
    return [e for e in val if isinstance(e, dict)] if isinstance(val, list) else []


def _record_mentions_underlier(rec: dict, underlier: str) -> bool:
    """True iff the record mentions ``underlier`` in any candidate-or-rejection field.

    Fields scanned per PRD-153 R2: ``qualified_trades``, ``excluded_symbols``,
    ``near_a_plus``, ``watchlist``.
    """
    for key in ("qualified_trades", "near_a_plus", "watchlist"):
        for entry in _entries_for(rec, key):
            if entry.get("symbol") == underlier:
                return True
    excluded = rec.get("excluded_symbols")
    if isinstance(excluded, dict) and underlier in excluded:
        return True
    return False


def _record_date(rec: dict) -> Optional[str]:
    dt = _parse_run_at(rec)
    if dt is None:
        return None
    return dt.date().isoformat()


# ---------------------------------------------------------------------------
# Blind-spot evaluation
# ---------------------------------------------------------------------------

def _has_intraday_context_for(records: list[dict], underlier: str) -> bool:
    """Any joined record carrying intraday context on the underlier's entry."""
    for rec in records:
        for key in ("qualified_trades", "near_a_plus"):
            for entry in _entries_for(rec, key):
                if entry.get("symbol") != underlier:
                    continue
                if entry.get("intraday_state_available") is not None:
                    return True
    return False


def _is_expansion_data_incomplete(records: list[dict], underlier: str) -> bool:
    for rec in records:
        if rec.get("regime") != "EXPANSION":
            continue
        excluded = rec.get("excluded_symbols")
        if isinstance(excluded, dict) and excluded.get(underlier) == "DATA_INCOMPLETE":
            return True
    return False


def _is_short_trade(trade: NormalizedTrade) -> bool:
    if trade.option is not None and trade.option.right == OPTION_PUT:
        return True
    if trade.instrument_class == CLASS_EQUITY and trade.side == SIDE_SELL:
        return True
    return False


def _evaluate_blind_spots(
    *,
    trade: NormalizedTrade,
    underlier: Optional[str],
    matching_records: list[dict],
    date_records: list[dict],
) -> list[str]:
    flags: list[str] = []
    if underlier is None:
        return flags

    if not matching_records:
        if not date_records:
            flags.append(BLIND_NO_AUDIT_FOR_DATE)
        else:
            flags.append(BLIND_UNDERLIER_NOT_IN_AUDIT_UNIVERSE)
            if _is_short_trade(trade):
                flags.append(BLIND_GAP_DOWN_SHORT_SUPPRESSED)
    else:
        if not _has_intraday_context_for(matching_records, underlier):
            flags.append(BLIND_NOTIFY_MODE_ONLY)
        if _is_expansion_data_incomplete(matching_records, underlier):
            flags.append(BLIND_EXPANSION_DATA_INCOMPLETE_AMBIGUOUS)

    return flags


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def enrich(
    trades: list[NormalizedTrade],
    audit_log_path: str = AUDIT_LOG_PATH,
) -> list[EnrichedTrade]:
    """Attach same-day audit context and blind-spot flags to each trade."""
    records = load_audit_records(audit_log_path)
    # Bucket records by date string for cheap lookup.
    by_date: dict[str, list[dict]] = {}
    for rec in records:
        d = _record_date(rec)
        if d is None:
            continue
        by_date.setdefault(d, []).append(rec)
    for bucket in by_date.values():
        bucket.sort(key=lambda r: r.get("run_at_utc") or "")

    universe = cuttingboard_universe()
    enriched: list[EnrichedTrade] = []
    for trade in trades:
        underlier = trade.underlier
        date_str = trade.date.isoformat()
        date_records = by_date.get(date_str, [])
        matching: list[dict] = []
        if underlier:
            matching = [r for r in date_records if _record_mentions_underlier(r, underlier)]

        in_universe = bool(underlier and underlier in universe)
        blind_spots = _evaluate_blind_spots(
            trade=trade,
            underlier=underlier,
            matching_records=matching,
            date_records=date_records,
        )

        enriched.append(
            EnrichedTrade(
                trade=trade,
                in_universe=in_universe,
                audit_records=matching,
                blind_spots=blind_spots,
            )
        )

    return enriched
