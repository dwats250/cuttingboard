"""
Append-only manual trade journal writer.

Writes validated records to logs/manual_trades.jsonl.
This module must NOT be imported by any runtime, contract, or delivery module.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

JOURNAL_PATH = Path("logs/manual_trades.jsonl")

ALLOWED_ACTIONS = {"CONSIDERED", "ENTERED", "EXITED", "SKIPPED", "MISSED", "CANCELLED"}
ALLOWED_DIRECTIONS = {"LONG", "SHORT", "NEUTRAL", "UNKNOWN"}
ALLOWED_INSTRUMENT_TYPES = {"STOCK", "ETF", "OPTION", "OPTION_SPREAD", "CASH", "UNKNOWN"}
ALLOWED_THESIS_ADHERENCE = {"FOLLOWED_THESIS", "VIOLATED_THESIS", "NO_THESIS", "THESIS_UNKNOWN"}
ALLOWED_INTENTS = {
    "PLANNED_TRADE",
    "IMPULSE_TRADE",
    "HEDGE",
    "TEST_SIZE",
    "EXIT_MANAGEMENT",
    "REVIEW_ONLY",
    "UNKNOWN",
}
ALLOWED_MISTAKE_LABELS = {
    "CHASED_ENTRY",
    "OVERSIZED",
    "ENTERED_WITHOUT_THESIS",
    "IGNORED_INVALIDATION",
    "IGNORED_MACRO_CONFLICT",
    "ENTERED_LATE",
    "EXITED_EARLY",
    "HELD_TOO_LONG",
    "TOOK_LOW_QUALITY_SETUP",
    "REVENGE_TRADE",
    "OVERTRADED",
    "BROKE_RULES",
    "NONE",
}


@dataclass(frozen=True)
class TradeJournalRecord:
    trade_date: str
    symbol: str
    action: str
    direction: str
    instrument_type: str
    thesis_adherence: str
    intent: str
    mistake_labels: tuple[str, ...]
    system_candidate_id: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        _validate_record(self)


def _validate_record(r: TradeJournalRecord) -> None:
    for attr in (
        "trade_date",
        "symbol",
        "action",
        "direction",
        "instrument_type",
        "thesis_adherence",
        "intent",
    ):
        if not getattr(r, attr):
            raise ValueError(f"Missing required field: {attr}")

    if r.action not in ALLOWED_ACTIONS:
        raise ValueError(f"Invalid action: {r.action!r}. Allowed: {ALLOWED_ACTIONS}")
    if r.direction not in ALLOWED_DIRECTIONS:
        raise ValueError(f"Invalid direction: {r.direction!r}. Allowed: {ALLOWED_DIRECTIONS}")
    if r.instrument_type not in ALLOWED_INSTRUMENT_TYPES:
        raise ValueError(f"Invalid instrument_type: {r.instrument_type!r}. Allowed: {ALLOWED_INSTRUMENT_TYPES}")
    if r.thesis_adherence not in ALLOWED_THESIS_ADHERENCE:
        raise ValueError(f"Invalid thesis_adherence: {r.thesis_adherence!r}. Allowed: {ALLOWED_THESIS_ADHERENCE}")
    if r.intent not in ALLOWED_INTENTS:
        raise ValueError(f"Invalid intent: {r.intent!r}. Allowed: {ALLOWED_INTENTS}")

    labels = r.mistake_labels
    if not labels:
        raise ValueError("mistake_labels must not be empty. Use [\"NONE\"] if no mistake occurred.")
    invalid = set(labels) - ALLOWED_MISTAKE_LABELS
    if invalid:
        raise ValueError(f"Invalid mistake_labels: {invalid}. Allowed: {ALLOWED_MISTAKE_LABELS}")
    if "NONE" in labels and len(labels) > 1:
        raise ValueError("\"NONE\" must be the only element in mistake_labels when present.")


def append_record(record: TradeJournalRecord, path: Path = JOURNAL_PATH) -> None:
    """Validate and append one trade journal record to the JSONL file."""
    recorded_at = datetime.now(tz=timezone.utc).isoformat()
    payload = {
        "recorded_at_utc": recorded_at,
        "trade_date": record.trade_date,
        "symbol": record.symbol,
        "action": record.action,
        "direction": record.direction,
        "instrument_type": record.instrument_type,
        "thesis_adherence": record.thesis_adherence,
        "intent": record.intent,
        "mistake_labels": list(record.mistake_labels),
        "system_candidate_id": record.system_candidate_id,
        "notes": record.notes,
    }
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")
