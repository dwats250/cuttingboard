"""Canonical PT-hour slot + cross-run idempotency store for hourly alerts (PRD-141)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

_PT_TZ = ZoneInfo("America/Vancouver")

LAST_HOURLY_SLOT_PATH = "logs/last_hourly_slot.json"

_PREMARKET_MINUTES_UTC: frozenset[tuple[int, int]] = frozenset(
    {(12, 50), (13, 0), (13, 50)}
)

logger = logging.getLogger(__name__)


def canonical_slot_utc(now_utc: datetime) -> datetime:
    """Return the UTC datetime of the top of the PT hour containing now_utc.

    DST-correct year-round: floors in America/Vancouver, then converts back to UTC.
    """
    if now_utc.tzinfo is None:
        raise ValueError("canonical_slot_utc requires a tz-aware datetime")
    pt = now_utc.astimezone(_PT_TZ).replace(minute=0, second=0, microsecond=0)
    return pt.astimezone(timezone.utc)


def is_premarket_slot(now_utc: datetime, tolerance_minutes: int = 5) -> bool:
    """Return True iff now_utc is within ±tolerance of a declared premarket cron minute.

    Declared minutes (UTC): 12:50, 13:00, 13:50. Comparison ignores date/seconds.
    """
    if now_utc.tzinfo is None:
        raise ValueError("is_premarket_slot requires a tz-aware datetime")
    now = now_utc.astimezone(timezone.utc)
    now_minutes = now.hour * 60 + now.minute
    for hh, mm in _PREMARKET_MINUTES_UTC:
        target = hh * 60 + mm
        if abs(now_minutes - target) <= tolerance_minutes:
            return True
    return False


def load_last_slot(path: str = LAST_HOURLY_SLOT_PATH) -> Optional[dict]:
    """Return persisted slot dict, or None if missing/empty/malformed."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        raw = p.read_text(encoding="utf-8").strip()
        if not raw:
            return None
        data = json.loads(raw)
        if not isinstance(data, dict) or "slot_utc" not in data:
            logger.debug("last_hourly_slot.json malformed (missing slot_utc)")
            return None
        return data
    except (OSError, json.JSONDecodeError) as exc:
        logger.debug("load_last_slot failed: %s", exc)
        return None


def save_last_slot(slot_utc: datetime, path: str = LAST_HOURLY_SLOT_PATH) -> None:
    """Persist slot_utc to the store. Creates parent dir if missing."""
    if slot_utc.tzinfo is None:
        raise ValueError("save_last_slot requires a tz-aware datetime")
    slot = slot_utc.astimezone(timezone.utc)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slot_utc": slot.isoformat(),
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
