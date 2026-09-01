"""PRD-324 (A1-C): pure consumer leaf for the intraday session chart.

Defensively admits the A1-P sidecar's 1-minute source bars for the primary symbol
and derives deterministic MEMBERSHIP-COMPLETE 09:30-anchored 5-minute candles.
Display-only. Import boundary (R12): stdlib + ``cuttingboard.time_utils`` ONLY --
never the renderer, decision code, ``cuttingboard.runtime``, or any network module.
The clock is injected (``now``); no I/O, and any admission failure returns ``None``
so the caller keeps its daily chart (R1/R2) -- the leaf never raises into the render
path. Each 1m ``ts`` is treated START-labeled and tz-aware UTC (R4); completeness
(R5) is membership-based, so it is robust to the label.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import date, datetime, time, timedelta
from typing import Any, NamedTuple, Optional

from cuttingboard import time_utils

_EASTERN = time_utils._EASTERN
_OPEN: time = time_utils._MARKET_OPEN_ET   # 09:30 ET
_CLOSE: time = time_utils._MARKET_CLOSE_ET  # 16:00 ET
_MAX_AGE = timedelta(minutes=90)           # R3 generated_at / through age bound (inclusive)
_MAX_FUTURE_SKEW = timedelta(minutes=5)    # R3 through future-skew tolerance (inclusive)
_BIN = 5                                   # R5 candle width (minutes)
_EXPECT_SOURCE = {"producer": "hourly", "provider": "yfinance", "interval": "1m"}
_EXPECT_COLUMNS = ["ts", "Open", "High", "Low", "Close", "Volume"]


class Candle(NamedTuple):
    """One completed 5m candle; ordered to feed ``setup_chart`` directly
    (``[0]`` label, ``[1..4]`` OHLC -- volume is not used by chart geometry)."""
    label: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class IntradaySession(NamedTuple):
    candles: list[Candle]
    session_date: str          # ET "YYYY-MM-DD"
    completed_through: str     # END / right edge of the last completed bin, ET "HH:MM" (R10)
    caption: str               # honest ET-session / completed-through caption (R10)


def derive_intraday_session(
    snapshot: Optional[Mapping[str, Any]],
    primary_symbol: Optional[str],
    now: datetime,
) -> Optional[IntradaySession]:
    """Completed 5m session for ``primary_symbol``, or ``None`` => keep the daily
    chart. Never raises (R1/R2)."""
    try:
        return _derive(snapshot, primary_symbol, now)
    except Exception:
        return None


def _derive(snapshot, primary_symbol, now):  # noqa: ANN001
    if not isinstance(snapshot, Mapping):
        return None
    # R2 top-level envelope: exact schema / source values / columns.
    sv = snapshot.get("schema_version")
    if type(sv) is not int or sv != 1:  # reject bool/float lookalikes (True==1, 1.0==1)
        return None
    source = snapshot.get("source")
    if not isinstance(source, Mapping) or source.get("adjusted") is not False:
        return None
    if any(source.get(k) != v for k, v in _EXPECT_SOURCE.items()):
        return None
    if snapshot.get("columns") != _EXPECT_COLUMNS:
        return None
    snap_primary = snapshot.get("primary_symbol")
    if not (snap_primary is None or isinstance(snap_primary, str)):
        return None
    # R7 producer / rendered-primary agreement.
    if not isinstance(primary_symbol, str) or not primary_symbol or snap_primary != primary_symbol:
        return None
    # R3 session / freshness, ET-normalized and DST-safe.
    now_et = _to_et(now)
    if now_et is None:
        return None
    session_date = _parse_date(snapshot.get("session_date"))
    if session_date is None or session_date != now_et.date():
        return None
    generated_at = _parse_dt(snapshot.get("generated_at"))
    if generated_at is None:
        return None
    if not timedelta(0) <= (now - generated_at) <= _MAX_AGE:  # reject future / stale
        return None
    symbols = snapshot.get("symbols")
    if not isinstance(symbols, Mapping):
        return None
    bars = _admit_symbol(symbols.get(primary_symbol), session_date)
    if bars is None:
        return None
    # R3 per-symbol `through`: age, future-skew, and ET session window.
    through = _parse_dt(symbols[primary_symbol].get("through"))
    if through is None or (now - through) > _MAX_AGE or through > now + _MAX_FUTURE_SKEW:
        return None
    through_et = _to_et(through)
    if through_et is None or not _in_session(through_et, session_date):
        return None
    # R4/R5 membership-complete 5m derivation.
    candles, completed_end = _derive_5m(bars, session_date)
    if not candles:
        return None
    return IntradaySession(candles, session_date.isoformat(), completed_end,
                           _caption(session_date, completed_end))


def _admit_symbol(entry, session_date):  # noqa: ANN001
    """R2 nested admission: ET-normalized validated bars, or ``None`` => omit the
    WHOLE symbol. Consumer-side defensive read of a possibly-corrupt file."""
    if not isinstance(entry, Mapping):
        return None
    bars, row_count, through = entry.get("bars"), entry.get("row_count"), entry.get("through")
    if not isinstance(bars, list) or not bars or not isinstance(through, str):
        return None
    if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count != len(bars):
        return None
    validated: list[tuple[datetime, float, float, float, float, int]] = []
    prev: Optional[datetime] = None
    for row in bars:
        if isinstance(row, (str, bytes)) or not isinstance(row, Sequence) or len(row) != 6:
            return None
        ts = _parse_dt(row[0])
        # R5: a 1m START bar is minute-aligned; rejecting sub-minute ts also bars two
        # observations from sharing one ET minute (a duplicate would be a non-ascending ts).
        if ts is None or ts.second or ts.microsecond or (prev is not None and ts <= prev):
            return None
        et = _to_et(ts)
        if et is None or et.date() != session_date:  # every bar's ET date == session_date
            return None
        o, h, low, c, v = _price(row[1]), _price(row[2]), _price(row[3]), _price(row[4]), _volume(row[5])
        if None in (o, h, low, c) or v is None or h < max(o, c) or low > min(o, c):
            return None
        validated.append((et, o, h, low, c, v))
        prev = ts
    if through != bars[-1][0]:  # `through` is the last bar's ts
        return None
    return validated


def _derive_5m(bars, session_date):  # noqa: ANN001
    """09:30-anchored half-open ``[09:30+5k, 09:30+5(k+1))`` bins; a bin is a
    COMPLETED candle only if all five START-labeled minutes are present (R5). No
    synthetic OHLC, no forward-fill, no partial bin."""
    anchor = datetime.combine(session_date, _OPEN, tzinfo=_EASTERN)
    grouped: dict[int, dict[int, tuple]] = {}
    for bar in bars:
        offset = (bar[0].hour * 60 + bar[0].minute) - (_OPEN.hour * 60 + _OPEN.minute)
        if offset >= 0:
            grouped.setdefault(offset // _BIN, {})[offset % _BIN] = bar
    candles: list[Candle] = []
    last_k = -1
    for k in sorted(grouped):
        members = grouped[k]
        if any(m not in members for m in range(_BIN)):  # missing interior minute -> drop
            continue
        candles.append(Candle(
            label=(anchor + timedelta(minutes=_BIN * k)).strftime("%H:%M"),
            open=members[0][1],
            high=max(m[2] for m in members.values()),
            low=min(m[3] for m in members.values()),
            close=members[_BIN - 1][4],
            volume=sum(m[5] for m in members.values()),
        ))
        last_k = k
    if last_k < 0:
        return [], ""
    return candles, (anchor + timedelta(minutes=_BIN * (last_k + 1))).strftime("%H:%M")


def _caption(session_date: date, completed_end: str) -> str:
    """R10: state the ET session_date and the completed-candles-THROUGH (the END /
    right edge of the last completed bin). Never states the raw source ``through``."""
    return f"{session_date.isoformat()} intraday 5m - completed through {completed_end} ET"


def _parse_dt(value: object) -> Optional[datetime]:
    """Tz-aware datetime, or ``None`` for a non-string, unparseable, or naive value."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _parse_date(value: object) -> Optional[date]:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _to_et(dt: Optional[datetime]) -> Optional[datetime]:
    if not isinstance(dt, datetime) or dt.tzinfo is None:
        return None
    return dt.astimezone(_EASTERN)


def _in_session(et_dt: datetime, session_date: date) -> bool:
    """True iff ``et_dt`` is on ``session_date`` within ``[09:30, 16:00)`` ET."""
    return et_dt.date() == session_date and _OPEN <= time(et_dt.hour, et_dt.minute) < _CLOSE


def _price(value: object) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    num = float(value)
    return num if math.isfinite(num) and num > 0 else None


def _volume(value: object) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
        return None
    return int(value) if value >= 0 else None
