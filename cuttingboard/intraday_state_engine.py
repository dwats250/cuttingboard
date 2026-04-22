"""
Intraday State Engine — ORB classification, Phase 1.

Public API: compute_intraday_state(symbol, bars) -> IntraState | None
All other functions are internal.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from cuttingboard.confirmation import (
    DIRECTION_DOWN,
    DIRECTION_UP,
    STATE_BREAK_ONLY,
    STATE_FAILURE_CONFIRMED,
    STATE_HOLD_CONFIRMED,
    LevelConfirmation,
    evaluate_level_confirmation,
)

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")

# ---------------------------------------------------------------------------
# Time boundaries (ET wall-clock)
# ---------------------------------------------------------------------------
_ORB_START   = time(9, 30)
_ORB_END     = time(9, 35)
_NOISE_END   = time(9, 45)
_PRIMARY_END = time(10, 30)
_MIDDAY_END  = time(13, 30)

# ---------------------------------------------------------------------------
_VWAP_BUFFER     = 0.001   # ±10 bps
_VOLUME_BUFFER   = 0.10    # ±10%
_HOLD_BARS_MIN   = 3
_GAP_THRESHOLD   = 0.0025
_ACCEPTANCE_CLOSES_MIN = 2
_EXPECTED_BAR_INTERVAL = timedelta(minutes=1)
_BAR_INTERVAL_TOLERANCE = timedelta(minutes=1)


# ---------------------------------------------------------------------------
# Data contract
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Bar:
    timestamp: datetime   # timezone-aware, US/Eastern
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class IntraState:
    symbol:              str
    timestamp:           str          # ISO 8601

    orb_high:            float
    orb_low:             float
    current_price:       float

    orb_break_direction: Optional[str]   # "LONG" | "SHORT" | None
    holding_bars:        int
    reclaimed_orb:       bool
    permission_state:    str          # confirmation layer internal state
    trades_allowed:      bool
    gap_type:            str          # "DOWN" | "UP" | "FLAT"
    phase:               str          # "OPEN" | "EARLY" | "POST_OPEN"
    failed_reclaim:      bool
    acceptance_below_level: bool
    consecutive_closes_below_level: int

    vwap:                float
    vwap_position:       str          # "ABOVE" | "BELOW" | "NEUTRAL"
    volume_trend:        str          # "EXPANDING" | "FLAT" | "DECLINING"

    state:               str          # "EXPANSION_CONFIRMED" | "FAILED_EXPANSION" | "RANGE"
    confidence:          float
    time_window:         str          # "PRIMARY" | "MIDDAY" | "SECONDARY"


class InsufficientDataError(Exception):
    """Fewer than 5 bars exist in the ORB window."""


@dataclass(frozen=True)
class SessionContext:
    open_price: float
    prev_close: Optional[float]
    gap_type: str


@dataclass(frozen=True)
class DownsidePermissionState:
    phase: str
    or_low_broken: bool
    failed_reclaim: bool
    acceptance_below_level: bool


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_et(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        raise ValueError(f"Naive timestamp not allowed: {ts}")
    return ts.astimezone(ET)


def _et_time(ts: datetime) -> time:
    return _to_et(ts).time()


def _orb_bars(bars: list[Bar]) -> list[Bar]:
    """Return bars whose timestamp falls within 09:30–09:35 ET (inclusive)."""
    return [
        b for b in bars
        if _ORB_START <= _et_time(b.timestamp) <= _ORB_END
    ]


def _compute_orb(bars: list[Bar]) -> tuple[float, float, float]:
    """Return (orb_high, orb_low, orb_volume_avg)."""
    orb = _orb_bars(bars)
    if len(orb) < 5:
        raise InsufficientDataError(
            f"ORB window requires 5 bars; got {len(orb)}"
        )
    orb_high = max(b.high for b in orb)
    orb_low  = min(b.low  for b in orb)
    orb_vol_avg = sum(b.volume for b in orb) / len(orb)
    return orb_high, orb_low, orb_vol_avg


def _compute_vwap(bars: list[Bar]) -> float:
    """Rolling session VWAP from first bar through last bar."""
    cum_pv = 0.0
    cum_v  = 0
    for b in bars:
        cum_pv += b.close * b.volume
        cum_v  += b.volume
    if cum_v == 0:
        return bars[-1].close
    return cum_pv / cum_v


def _vwap_position(close: float, vwap: float) -> str:
    if close > vwap * (1 + _VWAP_BUFFER):
        return "ABOVE"
    if close < vwap * (1 - _VWAP_BUFFER):
        return "BELOW"
    return "NEUTRAL"


def _volume_trend(current_volume: int, orb_vol_avg: float) -> str:
    if current_volume > orb_vol_avg * (1 + _VOLUME_BUFFER):
        return "EXPANDING"
    if current_volume < orb_vol_avg * (1 - _VOLUME_BUFFER):
        return "DECLINING"
    return "FLAT"


def _time_window(ts: datetime) -> str:
    t = _et_time(ts)
    if t <= _PRIMARY_END:
        return "PRIMARY"
    if t <= _MIDDAY_END:
        return "MIDDAY"
    return "SECONDARY"


def classify_gap(open_price: float, prev_close: Optional[float], threshold: float = _GAP_THRESHOLD) -> str:
    if prev_close is None or prev_close <= 0:
        return "FLAT"

    gap_pct = (open_price - prev_close) / prev_close
    if gap_pct <= -threshold:
        return "DOWN"
    if gap_pct >= threshold:
        return "UP"
    return "FLAT"


def classify_phase(minutes_since_open: float) -> str:
    if minutes_since_open < 5:
        return "OPEN"
    if minutes_since_open < 30:
        return "EARLY"
    return "POST_OPEN"


def detect_failed_reclaim(high: float, close: float, level: float) -> bool:
    reclaim_attempt = high >= level
    return reclaim_attempt and close < level


def count_consecutive_closes_below_level(closes: list[float], level: float) -> int:
    n = _ACCEPTANCE_CLOSES_MIN
    if len(closes) < n:
        return 0
    count = 0
    for close in reversed(closes):
        if close < level:
            count += 1
        else:
            break
    return count


def _acceptance_closes(bars: list[Bar]) -> list[float]:
    """Extract closes for acceptance check; return [] if trailing bars are non-contiguous."""
    n = _ACCEPTANCE_CLOSES_MIN
    if len(bars) < n:
        return [b.close for b in bars]
    trailing = bars[-n:]
    max_delta = _EXPECTED_BAR_INTERVAL + _BAR_INTERVAL_TOLERANCE
    for i in range(n - 1):
        if trailing[i + 1].timestamp - trailing[i].timestamp > max_delta:
            return []
    return [b.close for b in bars]


def detect_acceptance_below_level(
    closes: list[float],
    level: float,
    consecutive_closes_required: int = _ACCEPTANCE_CLOSES_MIN,
) -> tuple[bool, int]:
    count = count_consecutive_closes_below_level(closes, level)
    return count >= consecutive_closes_required, count


def downside_short_permission(context: SessionContext, intraday_state: DownsidePermissionState) -> bool:
    if context.gap_type != "DOWN":
        return True

    if intraday_state.phase == "OPEN":
        return False

    if intraday_state.or_low_broken and not (
        intraday_state.failed_reclaim or intraday_state.acceptance_below_level
    ):
        return False

    if intraday_state.failed_reclaim:
        return True

    if intraday_state.acceptance_below_level:
        return True

    return False


def _evaluate_break_state(
    bars: list[Bar],
    orb_high: float,
    orb_low: float,
) -> tuple[Optional[str], int, bool, str, bool, LevelConfirmation]:
    """
    Evaluate OR high / OR low through the confirmation layer.

    OR high only tracks upside breaks; OR low only tracks downside breaks. Each
    level is evaluated independently, then collapsed into the legacy ORB view
    expected by the intraday state engine.
    """
    post_orb = [b for b in bars if _et_time(b.timestamp) > _ORB_END]
    if not post_orb:
        empty = LevelConfirmation(
            level_name="OR_LOW",
            level_price=orb_low,
            state="IDLE",
            output="SYSTEM_DEFAULT",
            direction=None,
            break_candle_index=None,
            evaluation_candles=0,
            holding_closes=0,
            reclaim_active=False,
            reclaim_candle_index=None,
            current_candle_index=None,
        )
        return None, 0, False, "IDLE", False, empty

    closes = [b.close for b in post_orb]
    long_level = evaluate_level_confirmation(
        "OR_HIGH",
        orb_high,
        closes,
        allowed_directions={DIRECTION_UP},
    )
    short_level = evaluate_level_confirmation(
        "OR_LOW",
        orb_low,
        closes,
        allowed_directions={DIRECTION_DOWN},
    )

    selected = _select_orb_level(long_level, short_level)
    if selected is None:
        return None, 0, False, "IDLE", False, short_level

    direction = "LONG" if selected.direction == DIRECTION_UP else "SHORT"
    reclaimed = selected.reclaim_active or selected.state == STATE_FAILURE_CONFIRMED
    return direction, selected.holding_closes, reclaimed, selected.state, selected.trades_allowed, short_level


def _select_orb_level(
    long_level: LevelConfirmation,
    short_level: LevelConfirmation,
) -> Optional[LevelConfirmation]:
    candidates = [
        level
        for level in (long_level, short_level)
        if level.state != "IDLE"
    ]
    if not candidates:
        return None

    def _sort_key(level: LevelConfirmation) -> tuple[int, int, int]:
        state_rank = {
            STATE_HOLD_CONFIRMED: 4,
            STATE_FAILURE_CONFIRMED: 3,
            STATE_BREAK_ONLY: 2,
        }.get(level.state, 1)
        break_index = -1 if level.break_candle_index is None else level.break_candle_index
        current_index = -1 if level.current_candle_index is None else level.current_candle_index
        return (state_rank, break_index, current_index)

    return max(candidates, key=_sort_key)


def _compute_confidence(
    break_direction: Optional[str],
    vwap_pos: str,
    volume_trend: str,
    holding_bars: int,
    reclaimed: bool,
    state: str,
    time_window: str,
    bars_since_reclaim: int,
) -> float:
    score = 0.0

    if break_direction is not None:
        score += 0.30

    aligned = (
        (break_direction == "LONG"  and vwap_pos == "ABOVE") or
        (break_direction == "SHORT" and vwap_pos == "BELOW")
    )
    if aligned:
        score += 0.30

    if volume_trend == "EXPANDING":
        score += 0.20

    if holding_bars >= _HOLD_BARS_MIN:
        score += 0.20

    # Time window penalties
    if time_window == "MIDDAY":
        score -= 0.15
    elif time_window == "SECONDARY":
        score -= 0.10

    # State-specific adjustments
    if state == "FAILED_EXPANSION":
        # Freeze at reclaim value then decay 0.10/bar inside ORB
        score = max(0.10, score - 0.10 * bars_since_reclaim)
    elif state == "RANGE":
        score = min(0.40, score)

    return max(0.0, min(1.0, score))


def _count_bars_since_reclaim(bars: list[Bar], orb_high: float, orb_low: float) -> int:
    """Count consecutive bars (from the end) where close is inside ORB."""
    post_orb = [b for b in bars if _et_time(b.timestamp) > _ORB_END]
    count = 0
    for b in reversed(post_orb):
        if orb_low <= b.close <= orb_high:
            count += 1
        else:
            break
    return count


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_intraday_state(
    symbol: str,
    bars: list[Bar],
    *,
    previous_close: Optional[float] = None,
) -> Optional[IntraState]:
    """
    Classify intraday ORB state for a single symbol.

    Args:
        symbol: Ticker string (e.g., "SPY")
        bars:   Ordered list of Bar objects from 09:30 ET onward

    Returns:
        IntraState, or None if current time is before 09:45 ET

    Raises:
        InsufficientDataError: fewer than 5 bars in the ORB window
        ValueError:            bars not in chronological order or empty
    """
    if not bars:
        raise ValueError("bars list is empty")

    # Validate chronological order
    for i in range(1, len(bars)):
        if bars[i].timestamp <= bars[i - 1].timestamp:
            raise ValueError(
                f"Bars not in chronological order at index {i}: "
                f"{bars[i-1].timestamp} >= {bars[i].timestamp}"
            )

    current_bar = bars[-1]
    current_et_time = _et_time(current_bar.timestamp)

    # Before noise exclusion window ends → return None
    if current_et_time < _NOISE_END:
        return None

    orb_high, orb_low, orb_vol_avg = _compute_orb(bars)
    session_context = SessionContext(
        open_price=bars[0].open,
        prev_close=previous_close,
        gap_type=classify_gap(bars[0].open, previous_close),
    )
    market_open_dt = _to_et(current_bar.timestamp).replace(
        hour=_ORB_START.hour,
        minute=_ORB_START.minute,
        second=0,
        microsecond=0,
    )
    minutes_since_open = (_to_et(current_bar.timestamp) - market_open_dt).total_seconds() / 60.0
    phase = classify_phase(minutes_since_open)

    vwap = _compute_vwap(bars)
    vwap_pos = _vwap_position(current_bar.close, vwap)
    vol_trend = _volume_trend(current_bar.volume, orb_vol_avg)
    window = _time_window(current_bar.timestamp)

    break_direction, holding_bars, reclaimed, permission_state, trades_allowed, short_level = _evaluate_break_state(
        bars, orb_high, orb_low
    )
    post_orb = [b for b in bars if _et_time(b.timestamp) > _ORB_END]
    failed_reclaim = any(detect_failed_reclaim(b.high, b.close, orb_low) for b in post_orb)
    acceptance_below_level, consecutive_closes_below_level = detect_acceptance_below_level(
        _acceptance_closes(post_orb), orb_low
    )
    downside_permission = downside_short_permission(
        session_context,
        DownsidePermissionState(
            phase=phase,
            or_low_broken=short_level.break_candle_index is not None,
            failed_reclaim=failed_reclaim,
            acceptance_below_level=acceptance_below_level,
        ),
    )
    if break_direction == "SHORT":
        trades_allowed = trades_allowed and downside_permission

    # Determine state
    if break_direction is None:
        state = "RANGE"
    elif permission_state == STATE_FAILURE_CONFIRMED:
        state = "FAILED_EXPANSION"
    else:
        aligned = (
            (break_direction == "LONG"  and vwap_pos == "ABOVE") or
            (break_direction == "SHORT" and vwap_pos == "BELOW")
        )
        if permission_state == STATE_HOLD_CONFIRMED and holding_bars >= _HOLD_BARS_MIN and aligned:
            state = "EXPANSION_CONFIRMED"
        else:
            # Not yet confirmed — treat as RANGE for output
            state = "RANGE"

    bars_since_reclaim = _count_bars_since_reclaim(bars, orb_high, orb_low) if reclaimed else 0

    confidence = _compute_confidence(
        break_direction=break_direction,
        vwap_pos=vwap_pos,
        volume_trend=vol_trend,
        holding_bars=holding_bars,
        reclaimed=reclaimed,
        state=state,
        time_window=window,
        bars_since_reclaim=bars_since_reclaim,
    )

    logger.debug(
        f"{symbol} {current_et_time.strftime('%H:%M')} "
        f"state={state} conf={confidence:.2f} window={window}"
    )

    return IntraState(
        symbol=symbol,
        timestamp=current_bar.timestamp.isoformat(),
        orb_high=orb_high,
        orb_low=orb_low,
        current_price=current_bar.close,
        orb_break_direction=break_direction,
        holding_bars=holding_bars,
        reclaimed_orb=reclaimed,
        permission_state=permission_state,
        trades_allowed=trades_allowed,
        gap_type=session_context.gap_type,
        phase=phase,
        failed_reclaim=failed_reclaim,
        acceptance_below_level=acceptance_below_level,
        consecutive_closes_below_level=consecutive_closes_below_level,
        vwap=vwap,
        vwap_position=vwap_pos,
        volume_trend=vol_trend,
        state=state,
        confidence=confidence,
        time_window=window,
    )


# ---------------------------------------------------------------------------
# CLI output formatter
# ---------------------------------------------------------------------------

def format_intraday_state(s: IntraState) -> str:
    et_ts = datetime.fromisoformat(s.timestamp).astimezone(ET)
    time_str = et_ts.strftime("%H:%M ET")

    lines = [
        f"{s.symbol}  [{time_str}]  {s.time_window} WINDOW",
        "─" * 38,
        f"ORB        : {s.orb_low:.2f} – {s.orb_high:.2f}",
    ]

    if s.orb_break_direction and s.permission_state == STATE_FAILURE_CONFIRMED:
        arrow = "↑" if s.orb_break_direction == "LONG" else "↓"
        lines.append(f"BREAK      : {arrow} {s.orb_break_direction} → FAILURE CONFIRMED")
    elif s.orb_break_direction and not s.reclaimed_orb:
        arrow = "↑" if s.orb_break_direction == "LONG" else "↓"
        lines.append(f"BREAK      : {arrow} {s.orb_break_direction}  (held {s.holding_bars} bars)")
    elif s.orb_break_direction and s.reclaimed_orb:
        arrow = "↑" if s.orb_break_direction == "LONG" else "↓"
        lines.append(f"BREAK      : {arrow} {s.orb_break_direction} → RECLAIMED")
    else:
        lines.append("BREAK      : none")

    lines.append(f"VWAP       : {s.vwap_position}  ({s.current_price:.2f} vs {s.vwap:.2f})")
    lines.append(f"VOLUME     : {s.volume_trend}")
    lines.append("")
    lines.append(f"→ STATE      : {s.state}")
    lines.append(f"→ CONFIDENCE : {s.confidence:.2f}")

    return "\n".join(lines)
