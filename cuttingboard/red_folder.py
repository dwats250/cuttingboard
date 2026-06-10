"""PRD-176 — Red-folder economic calendar loader.

Pure and read-only. Loads the static ``data/red_folder_2026.json`` schedule of
scheduled macro-risk events (CPI/PPI/NFP/FOMC), validates it, and exposes exactly
what a renderer (PRD-177) needs as returned data: events inside a lookahead
window, the empty state, a loud error state for a missing/malformed/invalid file,
and a schedule-expiry signal. It renders nothing and gates nothing.

Timezone convention: events are wall-clock Eastern Time; the loader resolves each
to a tz-aware instant via ZoneInfo("America/New_York") (DST-correct), and window
membership is an absolute-instant comparison against the caller's UTC run time.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

_ET = ZoneInfo("America/New_York")
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEDULE_PATH = str(_PROJECT_ROOT / "data" / "red_folder_2026.json")
_REQUIRED_KEYS = ("date", "time_et", "type", "name")


@dataclass(frozen=True)
class RedFolderEvent:
    date: str
    time_et: str
    type: str
    name: str
    source: Optional[str] = None
    verified: bool = True

    def et_datetime(self) -> datetime:
        """Wall-clock ET instant for this event. Raises ValueError on a bad
        date/time, which the loader turns into a loud error result."""
        year, month, day = (int(part) for part in self.date.split("-"))
        hour, minute = (int(part) for part in self.time_et.split(":"))
        return datetime(year, month, day, hour, minute, tzinfo=_ET)


@dataclass(frozen=True)
class RedFolderResult:
    ok: bool
    events: tuple[RedFolderEvent, ...] = ()
    error: Optional[str] = None
    last_event_date: Optional[str] = None

    def events_in_window(self, now_utc: datetime, lookahead_hours: int = 48) -> list[RedFolderEvent]:
        """Events whose ET instant falls in [now_utc, now_utc + lookahead]."""
        if not self.ok:
            return []
        window_end = now_utc + timedelta(hours=lookahead_hours)
        return [e for e in self.events if now_utc <= e.et_datetime() <= window_end]

    def is_expiring(self, now_utc: datetime, within_days: int = 30) -> bool:
        """True once the run date is within ``within_days`` of the last entry (or
        past it) -- the anti-rot signal that the schedule file needs refreshing."""
        if not self.ok or self.last_event_date is None:
            return False
        last = datetime.strptime(self.last_event_date, "%Y-%m-%d").date()
        now_et_date = now_utc.astimezone(_ET).date()
        return (last - now_et_date).days <= within_days


def _error(message: str) -> RedFolderResult:
    return RedFolderResult(ok=False, events=(), error=message, last_event_date=None)


def _parse_event(raw: object) -> RedFolderEvent:
    if not isinstance(raw, dict):
        raise ValueError(f"event is not an object: {raw!r}")
    for key in _REQUIRED_KEYS:
        if key not in raw:
            raise ValueError(f"event missing required key {key!r}: {raw!r}")
    event = RedFolderEvent(
        date=str(raw["date"]),
        time_et=str(raw["time_et"]),
        type=str(raw["type"]),
        name=str(raw["name"]),
        source=raw.get("source"),
        verified=bool(raw.get("verified", True)),
    )
    event.et_datetime()  # validate the instant is constructible; loud on failure
    return event


def load_schedule(path: Optional[str] = None) -> RedFolderResult:
    """Load and validate the red-folder schedule.

    A missing file, malformed JSON, a missing ``events`` list, or any invalid
    event yields a loud error result (ok=False, error set, no events). It never
    raises and never returns a silently-empty success. A valid file with zero
    events is the empty state (ok=True, no events).
    """
    target = Path(path) if path else Path(DEFAULT_SCHEDULE_PATH)
    if not target.exists():
        return _error(f"red-folder schedule not found: {target}")
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return _error(f"malformed red-folder schedule {target}: {exc}")
    if not isinstance(raw, dict) or not isinstance(raw.get("events"), list):
        return _error(f"red-folder schedule {target} is missing an 'events' list")
    try:
        events = tuple(sorted(
            (_parse_event(item) for item in raw["events"]),
            key=lambda e: e.et_datetime(),
        ))
    except ValueError as exc:
        return _error(f"invalid red-folder event in {target}: {exc}")
    last_event_date = max((e.date for e in events), default=None)
    return RedFolderResult(ok=True, events=events, error=None, last_event_date=last_event_date)
