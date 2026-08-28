"""Canonical PT-hour slot + cross-run idempotency store for hourly alerts (PRD-141).

PRD-149 adds ``ALLOWED_PT_SLOTS`` and ``routine_pt_slot`` to anchor routine
hourly alerts to a fixed PT slot set (6:00 AM – 1:00 PM PT) regardless of
GitHub Actions cron drift.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

_PT_TZ = ZoneInfo("America/Vancouver")

LAST_HOURLY_SLOT_PATH = "logs/last_hourly_slot.json"

_PREMARKET_MINUTES_UTC: frozenset[tuple[int, int]] = frozenset(
    {(12, 50), (13, 0), (13, 50)}
)

# PRD-149: allowed routine PT slots, interpreted in America/Vancouver
# (identical offsets to the ruling's America/Los_Angeles year-round).
# PRD-319: (6,0) retired — the daily pipeline exclusively owns the 06:00 PT
# board and alert, so a routine hourly send there would duplicate it with no
# cross-path dedup. (6,45) added — the ruled post-open snapshot (CF-D3
# "OPEN+1"). The 15-minute spacing next to (6,30) sits inside max_lag, which
# is why routine dispatches carry EXPLICIT slot identity (explicit_pt_slot).
ALLOWED_PT_SLOTS: tuple[tuple[int, int], ...] = (
    (6, 30),
    (6, 45),
    (7, 0),
    (8, 0),
    (9, 0),
    (10, 0),
    (11, 0),
    (12, 0),
    (13, 0),
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


def routine_pt_slot(
    now_utc: datetime, max_lag_minutes: int = 25
) -> Optional[datetime]:
    """Resolve ``now_utc`` to the largest allowed PT slot within ``max_lag_minutes``.

    Returns a tz-aware UTC datetime corresponding to the PT slot, or ``None`` if
    ``now_utc`` is outside the allowed window or its lag from every allowed slot
    exceeds ``max_lag_minutes``.
    """
    if now_utc.tzinfo is None:
        raise ValueError("routine_pt_slot requires a tz-aware datetime")
    now_pt = now_utc.astimezone(_PT_TZ)
    best_slot_pt: Optional[datetime] = None
    best_lag = timedelta(minutes=max_lag_minutes)
    for hour, minute in ALLOWED_PT_SLOTS:
        slot_pt = now_pt.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if slot_pt > now_pt:
            continue
        lag = now_pt - slot_pt
        if lag <= best_lag:
            best_slot_pt = slot_pt
            best_lag = lag
    if best_slot_pt is None:
        return None
    return best_slot_pt.astimezone(timezone.utc)


def explicit_pt_slot(
    now_utc: datetime, slot_label: str, max_lag_minutes: int = 25
) -> Optional[datetime]:
    """Resolve an EXPLICITLY NAMED PT slot ("HH:MM"), never inferring another.

    PRD-319 R2: a routine dispatch (Cloudflare, or a GitHub heartbeat whose
    cron maps to a fixed intended slot) names its slot; the name is honoured
    or the arrival no-ops — identity never shifts under start-time delay the
    way ``routine_pt_slot`` inference can. Returns the canonical UTC slot iff
    the label parses as HH:MM, is a member of ``ALLOWED_PT_SLOTS``, is not in
    the future, and lags ``now_utc`` by at most ``max_lag_minutes``; else
    ``None`` (callers audit ``outside_routine_window`` and exit 0).
    """
    if now_utc.tzinfo is None:
        raise ValueError("explicit_pt_slot requires a tz-aware datetime")
    try:
        hh_s, mm_s = slot_label.strip().split(":")
        hour, minute = int(hh_s), int(mm_s)
    except (AttributeError, ValueError):
        return None
    if (hour, minute) not in ALLOWED_PT_SLOTS:
        return None
    now_pt = now_utc.astimezone(_PT_TZ)
    slot_pt = now_pt.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if slot_pt > now_pt:
        return None
    if now_pt - slot_pt > timedelta(minutes=max_lag_minutes):
        return None
    return slot_pt.astimezone(timezone.utc)


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
