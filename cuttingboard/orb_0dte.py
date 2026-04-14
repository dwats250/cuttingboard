"""Deterministic intraday ORB 0DTE momentum engine.

Purpose:
- Evaluate one PT session of ORB 0DTE logic from normalized session candles and
  option snapshots.
- Produce a deterministic `SessionResult` that can be reviewed by higher-level
  read-only observation and replay layers.

Inputs:
- `SessionInput`
  - `session_date`: PT trading date used after timestamp normalization
  - `candles`: `{"SPY": Sequence[Candle], "QQQ": Sequence[Candle]}`
  - `option_snapshots`: per-symbol same-day option snapshots keyed by symbol
  - `scheduled_high_impact_day`: pre-session terminal skip flag
  - `normal_allocation`: baseline size; engine applies 0.50x internally

Outputs:
- `SessionResult`
  - `mode`: `ENABLED` or `DISABLED`
  - `bias`: `LONG`, `SHORT`, or `NONE`
  - `execution_ready`: deterministic readiness state
  - `kill_switch`: terminal post-entry exit state
  - `opening_range`, `entry`, `exits`, `fail_reason`, `events`
  - `qualification_audit`, `exit_audit`, `exit_cause`

Constraints:
- Deterministic session evaluator only.
- Expects caller-supplied candles and option snapshots for the target PT session.
- Does not own artifact writing, scheduling, or runtime orchestration.

What this module does not do:
- It does not fetch market data.
- It does not write files, publish reports, or emit operational artifacts.
- It does not place trades or alter the main runtime's qualification path.

Read-only status:
- Read-only with respect to the repository runtime. It computes a deterministic
  result from provided inputs and returns that result to callers.
- This module is read-only and does not execute trades.

Feature-flag usage:
- Runtime shadow mode calls this engine only through the read-only observation
  path: `execute_run(..., observe_orb_0dte=True, orb_session_input=...)` or
  CLI `--observe-orb-0dte --orb-session-file <path>`.

Deterministic assumptions:
- All timestamps are interpreted as 5-minute bar close timestamps.
- Raw timestamps may arrive in any timezone, but are normalized to PT once at
  the module boundary and evaluated only in PT thereafter.
- PT session date is authoritative after normalization; candles outside that
  date are invalid for the session.
- The cash session reference window is `06:30` through `13:00` PT.
- The opening-range trading period is `06:30` through `07:00` PT and is
  represented by the six close timestamps `06:35` through `07:00` PT.
- `OpeningRange.reference_price` is always the open of the first opening-range
  close bar, which is the deterministic session reference price for OR sizing.
- The trend-day gate direction is derived independently for SPY and QQQ; both
  must agree before the model is enabled.
- If multiple simultaneous valid entry candidates exist on the same evaluation
  close, candidate priority is deterministic: `SPY` before `QQQ`, then
  `breakout` before `retest`. The first candidate that passes option selection
  and premium validation is entered. Lower-priority candidates are recorded as
  non-entered and cannot fill because the engine permits only one open position.
- Post-entry management also evaluates on 5-minute closes only.
- When multiple kill conditions are true on the same management candle, exit
  priority is deterministic: `HEADLINE` before `OR_REENTRY`, then `STOP`, then
  `STALL`.
- This module is self-contained and depends only on the Python standard library.
The engine is intentionally stateful and terminal: once a session fail
condition or kill switch fires, the mode is disabled for the day.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Literal, Sequence
from zoneinfo import ZoneInfo


PT = ZoneInfo("America/Los_Angeles")
ORB_TITLE = "ORB 0DTE MOMENTUM MODE v1 (PT)"

CASH_SESSION_START_PT = time(6, 30)
CASH_SESSION_END_PT = time(13, 0)
PT_CASH_SESSION_WINDOW = (CASH_SESSION_START_PT, CASH_SESSION_END_PT)
OPENING_RANGE_PERIOD_PT = (time(6, 30), time(7, 0))
OPENING_RANGE_WINDOW_PT = (time(6, 35), time(7, 0))
ENTRY_WINDOW_MORNING_PT = (time(7, 5), time(7, 30))
ENTRY_WINDOW_POWER_HOUR_PT = (time(12, 0), time(12, 45))

TIMESTAMP_SEMANTICS = (
    "All candle and option timestamps are interpreted as 5-minute bar close "
    "timestamps after one-time normalization into PT."
)
OPENING_RANGE_TIMESTAMP_SEMANTICS = (
    "The 06:30-07:00 PT opening range is represented by the six close "
    "timestamps from 06:35 through 07:00 PT."
)
SESSION_REFERENCE_PRICE_SEMANTICS = (
    "The session reference price is the open of the first opening-range close "
    "bar at 06:35 PT after normalization."
)
SIMULTANEOUS_SIGNAL_POLICY = (
    "When simultaneous entry candidates exist on the same evaluation close, "
    "evaluate SPY before QQQ and breakout before retest; enter only the first "
    "candidate that passes option selection and premium validation."
)
SIMULTANEOUS_KILL_POLICY = (
    "When multiple kill conditions are true on the same management close, "
    "apply HEADLINE before OR_REENTRY, then STOP, then STALL."
)

MODE_ENABLED = "ENABLED"
MODE_DISABLED = "DISABLED"

BIAS_LONG = "LONG"
BIAS_SHORT = "SHORT"
BIAS_NONE = "NONE"

KILL_NONE = "NONE"
KILL_OR_REENTRY = "OR_REENTRY"
KILL_STALL = "STALL"
KILL_HEADLINE = "HEADLINE"
KILL_STOP = "STOP"

OPTION_CALL = "call"
OPTION_PUT = "put"

FAIL_SCHEDULED_HIGH_IMPACT_DAY = "SCHEDULED_HIGH_IMPACT_DAY"
FAIL_DATA_INVALID = "DATA_INVALID"
FAIL_OR_NOT_COMPUTABLE = "OR_NOT_COMPUTABLE"
FAIL_OR_TOO_NARROW = "OR_TOO_NARROW"
FAIL_DELTA_UNAVAILABLE = "DELTA_UNAVAILABLE"
FAIL_PREMIUM_EXPANDED = "PREMIUM_EXPANDED"

AUDIT_SESSION_SKIPPED = "SESSION_SKIPPED"
AUDIT_QUALIFICATION_FAILED = "QUALIFICATION_FAILED"
AUDIT_QUALIFICATION_REJECTED = "QUALIFICATION_REJECTED"
AUDIT_SIMULTANEOUS_SIGNAL = "SIMULTANEOUS_SIGNAL"
AUDIT_SIGNAL_SUPPRESSED = "SIGNAL_SUPPRESSED"
AUDIT_ENTERED = "ENTERED"
AUDIT_EXIT = "EXIT"

TREND_MIN_OR_PCT = 0.003
BREAK_MULTIPLIER = 1.2
ENTRY_DISTANCE_MULTIPLIER = 1.5
HEADLINE_MOVE_THRESHOLD = 0.0075
STOP_LOSS_PCT = 0.25
SCALE_OUT_PCT = 0.50
FINAL_TARGET_PCT = 1.00
PREMIUM_EXPANSION_LIMIT = 2.5

SYMBOLS = ("SPY", "QQQ")
SIMULTANEOUS_SIGNAL_SYMBOL_PRIORITY = ("SPY", "QQQ")
ENTRY_KIND_PRIORITY = ("breakout", "retest")

Direction = Literal["LONG", "SHORT"]
Mode = Literal["ENABLED", "DISABLED"]
KillSwitch = Literal["NONE", "OR_REENTRY", "STALL", "HEADLINE", "STOP"]
Bias = Literal["LONG", "SHORT", "NONE"]
OptionType = Literal["call", "put"]

__all__ = [
    "ORB_TITLE",
    "PT",
    "CASH_SESSION_START_PT",
    "CASH_SESSION_END_PT",
    "PT_CASH_SESSION_WINDOW",
    "OPENING_RANGE_PERIOD_PT",
    "OPENING_RANGE_WINDOW_PT",
    "ENTRY_WINDOW_MORNING_PT",
    "ENTRY_WINDOW_POWER_HOUR_PT",
    "TIMESTAMP_SEMANTICS",
    "OPENING_RANGE_TIMESTAMP_SEMANTICS",
    "SESSION_REFERENCE_PRICE_SEMANTICS",
    "SIMULTANEOUS_SIGNAL_POLICY",
    "SIMULTANEOUS_KILL_POLICY",
    "Candle",
    "OptionSnapshot",
    "OpeningRange",
    "EntryRecord",
    "ExitRecord",
    "SessionInput",
    "SessionResult",
    "evaluate_orb_0dte_session",
]


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    headline_shock: bool = False


@dataclass(frozen=True)
class OptionSnapshot:
    contract_id: str
    timestamp: datetime
    expiry: date
    option_type: OptionType
    strike: float
    delta: float
    premium: float
    session_open_premium: float
    underlying_symbol: str


@dataclass(frozen=True)
class OpeningRange:
    high: float
    low: float
    range_points: float
    range_percent: float
    reference_price: float


@dataclass(frozen=True)
class EntryRecord:
    symbol: str
    direction: Direction
    entry_time_pt: datetime
    entry_price: float
    entry_kind: Literal["breakout", "retest"]
    contract_id: str
    strike: float
    delta: float
    premium: float
    position_size: float


@dataclass(frozen=True)
class ExitRecord:
    symbol: str
    timestamp_pt: datetime
    reason: str
    premium: float
    fraction_closed: float


@dataclass(frozen=True)
class SessionInput:
    session_date: date
    candles: dict[str, Sequence[Candle]]
    option_snapshots: dict[str, Sequence[OptionSnapshot]]
    scheduled_high_impact_day: bool = False
    normal_allocation: float = 1.0


@dataclass(frozen=True)
class SessionResult:
    title: str
    mode: Mode
    bias: Bias
    execution_ready: bool
    kill_switch: KillSwitch
    opening_range: OpeningRange | None
    entry: EntryRecord | None
    exits: tuple[ExitRecord, ...]
    fail_reason: str | None
    qualification_audit: tuple[str, ...]
    exit_cause: str | None
    exit_audit: tuple[str, ...]
    events: tuple[str, ...]


@dataclass
class _ActivePosition:
    entry: EntryRecord
    contract_id: str
    entry_premium: float
    first_target_hit: bool = False
    awaiting_runner_confirmation: bool = False
    highest_high: float = float("-inf")
    lowest_low: float = float("inf")
    stall_count: int = 0
    remaining_fraction: float = 1.0


@dataclass(frozen=True)
class _EntryContext:
    symbol: str
    direction: Direction
    break_index: int
    evaluation_index: int
    entry_kind: Literal["breakout", "retest"]


def evaluate_orb_0dte_session(session: SessionInput) -> SessionResult:
    """Evaluate one PT session for the ORB 0DTE momentum model."""
    events: list[str] = []
    qualification_audit: list[str] = []
    exit_audit: list[str] = []

    if session.scheduled_high_impact_day:
        events.append("scheduled high-impact day: session skipped")
        qualification_audit.append(f"{AUDIT_SESSION_SKIPPED}:{FAIL_SCHEDULED_HIGH_IMPACT_DAY}")
        return SessionResult(
            title=ORB_TITLE,
            mode=MODE_DISABLED,
            bias=BIAS_NONE,
            execution_ready=False,
            kill_switch=KILL_NONE,
            opening_range=None,
            entry=None,
            exits=(),
            fail_reason=FAIL_SCHEDULED_HIGH_IMPACT_DAY,
            qualification_audit=tuple(qualification_audit),
            exit_cause=None,
            exit_audit=tuple(exit_audit),
            events=tuple(events),
        )

    normalized = {symbol: _normalize_candles(symbol, candles) for symbol, candles in session.candles.items()}
    validation_error = _validate_session_inputs(session.session_date, normalized)
    if validation_error is not None:
        events.append(validation_error)
        qualification_audit.append(f"{AUDIT_QUALIFICATION_FAILED}:{FAIL_DATA_INVALID}")
        return SessionResult(
            title=ORB_TITLE,
            mode=MODE_DISABLED,
            bias=BIAS_NONE,
            execution_ready=False,
            kill_switch=KILL_NONE,
            opening_range=None,
            entry=None,
            exits=(),
            fail_reason=FAIL_DATA_INVALID,
            qualification_audit=tuple(qualification_audit),
            exit_cause=None,
            exit_audit=tuple(exit_audit),
            events=tuple(events),
        )

    opening_range = _compute_opening_range(normalized["SPY"])
    if opening_range is None:
        events.append("opening range not computable by 07:00 PT")
        qualification_audit.append(f"{AUDIT_QUALIFICATION_FAILED}:{FAIL_OR_NOT_COMPUTABLE}")
        return SessionResult(
            title=ORB_TITLE,
            mode=MODE_DISABLED,
            bias=BIAS_NONE,
            execution_ready=False,
            kill_switch=KILL_NONE,
            opening_range=None,
            entry=None,
            exits=(),
            fail_reason=FAIL_OR_NOT_COMPUTABLE,
            qualification_audit=tuple(qualification_audit),
            exit_cause=None,
            exit_audit=tuple(exit_audit),
            events=tuple(events),
        )
    if opening_range.range_percent < TREND_MIN_OR_PCT:
        events.append(f"opening range too narrow: {opening_range.range_percent:.4%}")
        qualification_audit.append(f"{AUDIT_QUALIFICATION_FAILED}:{FAIL_OR_TOO_NARROW}")
        return SessionResult(
            title=ORB_TITLE,
            mode=MODE_DISABLED,
            bias=BIAS_NONE,
            execution_ready=False,
            kill_switch=KILL_NONE,
            opening_range=opening_range,
            entry=None,
            exits=(),
            fail_reason=FAIL_OR_TOO_NARROW,
            qualification_audit=tuple(qualification_audit),
            exit_cause=None,
            exit_audit=tuple(exit_audit),
            events=tuple(events),
        )

    option_book = {
        symbol: _index_option_snapshots(symbol, snapshots, session.session_date)
        for symbol, snapshots in session.option_snapshots.items()
    }
    timeline = [c.timestamp for c in normalized["SPY"] if _is_evaluation_time(c.timestamp.time())]

    mode: Mode = MODE_DISABLED
    bias: Bias = BIAS_NONE
    execution_ready = False
    kill_switch: KillSwitch = KILL_NONE
    fail_reason: str | None = None
    exit_cause: str | None = None
    entry_record: EntryRecord | None = None
    exits: list[ExitRecord] = []
    active_position: _ActivePosition | None = None
    terminal = False
    used_entry_times: set[datetime] = set()

    for timestamp in timeline:
        idx_spy = _index_for_timestamp(normalized["SPY"], timestamp)
        idx_qqq = _index_for_timestamp(normalized["QQQ"], timestamp)
        current_spy = normalized["SPY"][idx_spy]
        current_qqq = normalized["QQQ"][idx_qqq]

        if active_position is not None:
            kill_switch = _evaluate_open_position(
                active_position,
                current_spy if active_position.entry.symbol == "SPY" else current_qqq,
                option_book.get(active_position.entry.symbol, {}),
                opening_range,
                exits,
                exit_audit,
            )
            if kill_switch != KILL_NONE:
                mode = MODE_DISABLED
                execution_ready = False
                bias = BIAS_NONE
                terminal = True
                exit_cause = kill_switch
                events.append(f"kill switch fired: {kill_switch} at {timestamp.isoformat()}")
                break

            if active_position.remaining_fraction <= 0.0:
                active_position = None

        if terminal or active_position is not None:
            continue

        gate = _evaluate_trend_gate(normalized, opening_range, timestamp)
        if gate is None:
            mode = MODE_DISABLED
            bias = BIAS_NONE
            execution_ready = False
            continue

        mode = MODE_ENABLED
        bias = gate.direction

        entry_candidates = _find_entry_candidates(
            normalized,
            opening_range,
            timestamp,
            gate.direction,
            used_entry_times,
        )
        if not entry_candidates:
            execution_ready = False
            continue
        if len(entry_candidates) > 1:
            qualification_audit.append(f"{AUDIT_SIMULTANEOUS_SIGNAL}:{timestamp.isoformat()}")
            events.append(
                "simultaneous candidates at "
                f"{timestamp.isoformat()}: policy={SIMULTANEOUS_SIGNAL_POLICY}"
            )

        for candidate_idx, candidate in enumerate(entry_candidates):
            option = _select_option_candidate(
                symbol=candidate.symbol,
                direction=candidate.direction,
                spot_price=normalized[candidate.symbol][candidate.evaluation_index].close,
                entry_time=candidate_timestamp(normalized[candidate.symbol], candidate.evaluation_index),
                session_date=session.session_date,
                option_book=option_book.get(candidate.symbol, {}),
            )
            if option is None:
                if fail_reason is None:
                    fail_reason = FAIL_DELTA_UNAVAILABLE
                qualification_audit.append(
                    f"{AUDIT_QUALIFICATION_REJECTED}:{candidate.symbol}:"
                    f"{candidate.entry_kind}:{FAIL_DELTA_UNAVAILABLE}@{timestamp.isoformat()}"
                )
                events.append(f"{candidate.symbol}: no option candidate at {timestamp.isoformat()}")
                continue

            if option.premium > option.session_open_premium * PREMIUM_EXPANSION_LIMIT:
                if fail_reason is None:
                    fail_reason = FAIL_PREMIUM_EXPANDED
                qualification_audit.append(
                    f"{AUDIT_QUALIFICATION_REJECTED}:{candidate.symbol}:"
                    f"{candidate.entry_kind}:{FAIL_PREMIUM_EXPANDED}@{timestamp.isoformat()}"
                )
                events.append(f"{candidate.symbol}: premium expansion filter failed at {timestamp.isoformat()}")
                continue

            execution_ready = True
            entry_candle = normalized[candidate.symbol][candidate.evaluation_index]
            entry_record = EntryRecord(
                symbol=candidate.symbol,
                direction=candidate.direction,
                entry_time_pt=entry_candle.timestamp,
                entry_price=entry_candle.close,
                entry_kind=candidate.entry_kind,
                contract_id=option.contract_id,
                strike=option.strike,
                delta=option.delta,
                premium=option.premium,
                position_size=session.normal_allocation * 0.5,
            )
            active_position = _ActivePosition(
                entry=entry_record,
                contract_id=option.contract_id,
                entry_premium=option.premium,
                highest_high=entry_candle.high,
                lowest_low=entry_candle.low,
            )
            used_entry_times.add(entry_candle.timestamp)
            qualification_audit.append(
                f"{AUDIT_ENTERED}:{candidate.symbol}:{candidate.entry_kind}@{entry_record.entry_time_pt.isoformat()}"
            )
            for suppressed in entry_candidates[candidate_idx + 1 :]:
                qualification_audit.append(
                    f"{AUDIT_SIGNAL_SUPPRESSED}:{suppressed.symbol}:{suppressed.entry_kind}"
                    f"@{timestamp.isoformat()}"
                )
            events.append(
                f"entered {candidate.symbol} {candidate.direction} {entry_record.contract_id} "
                f"at {entry_record.entry_time_pt.isoformat()}"
            )
            break

    return SessionResult(
        title=ORB_TITLE,
        mode=mode,
        bias=bias,
        execution_ready=execution_ready,
        kill_switch=kill_switch,
        opening_range=opening_range,
        entry=entry_record,
        exits=tuple(exits),
        fail_reason=fail_reason,
        qualification_audit=tuple(qualification_audit),
        exit_cause=exit_cause or (exits[-1].reason if exits else None),
        exit_audit=tuple(exit_audit),
        events=tuple(events),
    )


def candidate_timestamp(candles: Sequence[Candle], index: int) -> datetime:
    return candles[index].timestamp


def _normalize_candles(symbol: str, candles: Sequence[Candle]) -> list[Candle]:
    normalized: list[Candle] = []
    for candle in sorted(candles, key=lambda item: item.timestamp):
        ts = candle.timestamp
        if ts.tzinfo is None:
            raise ValueError(f"{symbol}: candle timestamp is naive")
        normalized.append(
            Candle(
                timestamp=ts.astimezone(PT),
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
                headline_shock=candle.headline_shock,
            )
        )
    return normalized


def _validate_session_inputs(session_date: date, candles_by_symbol: dict[str, list[Candle]]) -> str | None:
    if tuple(sorted(candles_by_symbol)) != tuple(sorted(SYMBOLS)):
        return "missing required symbols"

    timestamp_sets: list[list[datetime]] = []
    for symbol in SYMBOLS:
        candles = candles_by_symbol.get(symbol, [])
        if not candles:
            return f"{symbol}: missing candles"
        timestamps = [c.timestamp for c in candles]
        if any(ts.date() != session_date for ts in timestamps):
            return f"{symbol}: candles not normalized to PT session date"
        for prev, cur in zip(timestamps, timestamps[1:]):
            if cur <= prev:
                return f"{symbol}: candle order invalid"
            if (cur - prev).total_seconds() != 300:
                return f"{symbol}: data gap or malformed 5-minute sequence"
        timestamp_sets.append(timestamps)

        for candle in candles:
            if candle.high < max(candle.open, candle.close):
                return f"{symbol}: malformed candle high"
            if candle.low > min(candle.open, candle.close):
                return f"{symbol}: malformed candle low"
            if candle.volume < 0:
                return f"{symbol}: malformed candle volume"

    if timestamp_sets[0] != timestamp_sets[1]:
        return "SPY/QQQ timestamps misaligned"

    return None


def _compute_opening_range(candles: Sequence[Candle]) -> OpeningRange | None:
    start, end = OPENING_RANGE_WINDOW_PT
    opening = [c for c in candles if start <= c.timestamp.time() <= end]
    if len(opening) != 6:
        return None
    high = max(c.high for c in opening)
    low = min(c.low for c in opening)
    range_points = high - low
    reference_price = opening[0].open
    if reference_price <= 0:
        return None
    return OpeningRange(
        high=high,
        low=low,
        range_points=range_points,
        range_percent=range_points / reference_price,
        reference_price=reference_price,
    )


def _is_evaluation_time(ts: time) -> bool:
    morning_start, morning_end = ENTRY_WINDOW_MORNING_PT
    power_start, power_end = ENTRY_WINDOW_POWER_HOUR_PT
    in_morning = morning_start <= ts <= morning_end
    in_power_hour = power_start <= ts <= power_end
    return in_morning or in_power_hour


def _index_for_timestamp(candles: Sequence[Candle], timestamp: datetime) -> int:
    for idx, candle in enumerate(candles):
        if candle.timestamp == timestamp:
            return idx
    raise ValueError(f"timestamp not found: {timestamp.isoformat()}")


def _evaluate_trend_gate(
    candles_by_symbol: dict[str, Sequence[Candle]],
    opening_range: OpeningRange,
    timestamp: datetime,
) -> _EntryContext | None:
    idx_spy = _index_for_timestamp(candles_by_symbol["SPY"], timestamp)
    idx_qqq = _index_for_timestamp(candles_by_symbol["QQQ"], timestamp)

    spy_direction = _trend_gate_direction(candles_by_symbol["SPY"], idx_spy, opening_range)
    qqq_direction = _trend_gate_direction(candles_by_symbol["QQQ"], idx_qqq, opening_range)

    if spy_direction is None or qqq_direction is None or spy_direction != qqq_direction:
        return None

    return _EntryContext(
        symbol="SPY",
        direction=spy_direction,
        break_index=idx_spy - 2,
        evaluation_index=idx_spy,
        entry_kind="breakout",
    )


def _trend_gate_direction(
    candles: Sequence[Candle],
    idx: int,
    opening_range: OpeningRange,
) -> Direction | None:
    if idx < 2:
        return None
    sequence = candles[idx - 2 : idx + 1]
    if all(c.close > opening_range.high for c in sequence):
        if _sequence_progresses(sequence, "LONG") and _no_reversal(sequence, "LONG"):
            return "LONG"
    if all(c.close < opening_range.low for c in sequence):
        if _sequence_progresses(sequence, "SHORT") and _no_reversal(sequence, "SHORT"):
            return "SHORT"
    return None


def _sequence_progresses(sequence: Sequence[Candle], direction: Direction) -> bool:
    if direction == "LONG":
        return sequence[1].high > sequence[0].high and sequence[2].high > sequence[1].high
    return sequence[1].low < sequence[0].low and sequence[2].low < sequence[1].low


def _no_reversal(sequence: Sequence[Candle], direction: Direction) -> bool:
    if direction == "LONG":
        return all(c.close >= c.open for c in sequence)
    return all(c.close <= c.open for c in sequence)


def _find_entry_candidates(
    candles_by_symbol: dict[str, Sequence[Candle]],
    opening_range: OpeningRange,
    timestamp: datetime,
    direction: Direction,
    used_entry_times: set[datetime],
) -> list[_EntryContext]:
    candidates: list[_EntryContext] = []
    for symbol in SIMULTANEOUS_SIGNAL_SYMBOL_PRIORITY:
        idx = _index_for_timestamp(candles_by_symbol[symbol], timestamp)
        if candles_by_symbol[symbol][idx].timestamp in used_entry_times:
            continue

        for entry_kind in ENTRY_KIND_PRIORITY:
            if entry_kind == "breakout":
                candidate = _breakout_entry_context(symbol, candles_by_symbol[symbol], idx, opening_range, direction)
            else:
                candidate = _retest_entry_context(symbol, candles_by_symbol[symbol], idx, opening_range, direction)
            if candidate is not None:
                candidates.append(candidate)
                break
    return candidates


def _breakout_entry_context(
    symbol: str,
    candles: Sequence[Candle],
    idx: int,
    opening_range: OpeningRange,
    direction: Direction,
) -> _EntryContext | None:
    if idx < 2:
        return None
    break_idx = idx - 2
    sequence = candles[break_idx : idx + 1]
    if not _entry_close_sequence_valid(sequence, direction):
        return None
    if not _break_candle_impulse_valid(candles, break_idx):
        return None
    if not _entry_outside_range(candles[idx], opening_range, direction):
        return None
    if not _entry_distance_valid(candles[idx], opening_range, direction):
        return None
    if candles[idx].timestamp.time() >= time(12, 0) and not _power_hour_recent_extension(candles, idx, direction):
        return None
    return _EntryContext(symbol=symbol, direction=direction, break_index=break_idx, evaluation_index=idx, entry_kind="breakout")


def _retest_entry_context(
    symbol: str,
    candles: Sequence[Candle],
    idx: int,
    opening_range: OpeningRange,
    direction: Direction,
) -> _EntryContext | None:
    if idx < 3:
        return None
    prior = candles[idx - 3 : idx]
    current = candles[idx]
    if not _entry_close_sequence_valid(prior, direction):
        return None
    if not _entry_outside_range(current, opening_range, direction):
        return None
    boundary = opening_range.high if direction == "LONG" else opening_range.low
    touched = current.low <= boundary if direction == "LONG" else current.high >= boundary
    if not touched:
        return None
    if not _close_in_extreme(current, direction):
        return None
    if not _entry_distance_valid(current, opening_range, direction):
        return None
    if current.timestamp.time() >= time(12, 0) and not _power_hour_recent_extension(candles, idx, direction):
        return None
    return _EntryContext(symbol=symbol, direction=direction, break_index=idx - 3, evaluation_index=idx, entry_kind="retest")


def _entry_close_sequence_valid(sequence: Sequence[Candle], direction: Direction) -> bool:
    return len(sequence) == 3 and all(_close_in_extreme(candle, direction) for candle in sequence)


def _close_in_extreme(candle: Candle, direction: Direction) -> bool:
    full_range = candle.high - candle.low
    if full_range <= 0:
        return False
    if direction == "LONG":
        return (candle.close - candle.low) / full_range >= 0.75
    return (candle.high - candle.close) / full_range >= 0.75


def _break_candle_impulse_valid(candles: Sequence[Candle], break_idx: int) -> bool:
    if break_idx < 5:
        return False
    break_candle = candles[break_idx]
    prior = candles[break_idx - 5 : break_idx]
    avg_volume = sum(c.volume for c in prior) / 5
    avg_range = sum(c.high - c.low for c in prior) / 5
    break_range = break_candle.high - break_candle.low
    if avg_volume <= 0 or avg_range <= 0:
        return False
    return (
        break_candle.volume >= avg_volume * BREAK_MULTIPLIER
        and break_range >= avg_range * BREAK_MULTIPLIER
    )


def _entry_outside_range(candle: Candle, opening_range: OpeningRange, direction: Direction) -> bool:
    if direction == "LONG":
        return candle.close > opening_range.high
    return candle.close < opening_range.low


def _entry_distance_valid(candle: Candle, opening_range: OpeningRange, direction: Direction) -> bool:
    if direction == "LONG":
        distance = candle.close - opening_range.high
    else:
        distance = opening_range.low - candle.close
    return distance <= opening_range.range_points * ENTRY_DISTANCE_MULTIPLIER


def _power_hour_recent_extension(candles: Sequence[Candle], idx: int, direction: Direction) -> bool:
    start = max(0, idx - 2)
    window = candles[start : idx + 1]
    if direction == "LONG":
        return any(window[pos].high > window[pos - 1].high for pos in range(1, len(window)))
    return any(window[pos].low < window[pos - 1].low for pos in range(1, len(window)))


def _index_option_snapshots(
    symbol: str,
    snapshots: Sequence[OptionSnapshot],
    session_date: date,
) -> dict[datetime, list[OptionSnapshot]]:
    indexed: dict[datetime, list[OptionSnapshot]] = {}
    for snapshot in snapshots:
        if snapshot.underlying_symbol != symbol:
            raise ValueError(f"{symbol}: option snapshot symbol mismatch")
        if snapshot.timestamp.tzinfo is None:
            raise ValueError(f"{symbol}: option snapshot timestamp is naive")
        ts = snapshot.timestamp.astimezone(PT)
        if ts.date() != session_date:
            continue
        if snapshot.expiry != session_date:
            continue
        indexed.setdefault(ts, []).append(
            OptionSnapshot(
                contract_id=snapshot.contract_id,
                timestamp=ts,
                expiry=snapshot.expiry,
                option_type=snapshot.option_type,
                strike=snapshot.strike,
                delta=snapshot.delta,
                premium=snapshot.premium,
                session_open_premium=snapshot.session_open_premium,
                underlying_symbol=snapshot.underlying_symbol,
            )
        )
    return indexed


def _select_option_candidate(
    symbol: str,
    direction: Direction,
    spot_price: float,
    entry_time: datetime,
    session_date: date,
    option_book: dict[datetime, list[OptionSnapshot]],
) -> OptionSnapshot | None:
    chain = option_book.get(entry_time, [])
    if not chain:
        return None
    option_type = OPTION_CALL if direction == "LONG" else OPTION_PUT
    eligible = [item for item in chain if item.expiry == session_date and item.option_type == option_type]
    if not eligible:
        return None

    exact = [item for item in eligible if 0.40 <= abs(item.delta) <= 0.60]
    if exact:
        return min(exact, key=lambda item: (abs(abs(item.delta) - 0.50), abs(item.strike - spot_price)))

    ordered = sorted(eligible, key=lambda item: item.strike)
    atm_index = min(range(len(ordered)), key=lambda idx: abs(ordered[idx].strike - spot_price))
    fallback = min(range(len(ordered)), key=lambda idx: abs(abs(ordered[idx].delta) - 0.50))
    if abs(fallback - atm_index) > 1:
        return None
    return ordered[fallback]


def _evaluate_open_position(
    position: _ActivePosition,
    candle: Candle,
    option_book: dict[datetime, list[OptionSnapshot]],
    opening_range: OpeningRange,
    exits: list[ExitRecord],
    exit_audit: list[str],
) -> KillSwitch:
    direction = position.entry.direction

    if _headline_kill(candle):
        premium = _premium_for_contract(option_book, candle.timestamp, position.contract_id)
        exits.append(_exit_record(position.entry.symbol, candle.timestamp, KILL_HEADLINE, premium, position.remaining_fraction))
        exit_audit.append(f"{AUDIT_EXIT}:{KILL_HEADLINE}@{candle.timestamp.isoformat()}")
        position.remaining_fraction = 0.0
        return KILL_HEADLINE

    if not _entry_outside_range(candle, opening_range, direction):
        premium = _premium_for_contract(option_book, candle.timestamp, position.contract_id)
        exits.append(_exit_record(position.entry.symbol, candle.timestamp, KILL_OR_REENTRY, premium, position.remaining_fraction))
        exit_audit.append(f"{AUDIT_EXIT}:{KILL_OR_REENTRY}@{candle.timestamp.isoformat()}")
        position.remaining_fraction = 0.0
        return KILL_OR_REENTRY

    premium = _premium_for_contract(option_book, candle.timestamp, position.contract_id)
    if premium is None:
        raise ValueError(f"missing option premium for {position.contract_id} at {candle.timestamp.isoformat()}")

    if premium <= position.entry_premium * (1.0 - STOP_LOSS_PCT):
        exits.append(_exit_record(position.entry.symbol, candle.timestamp, KILL_STOP, premium, position.remaining_fraction))
        exit_audit.append(f"{AUDIT_EXIT}:{KILL_STOP}@{candle.timestamp.isoformat()}")
        position.remaining_fraction = 0.0
        return KILL_STOP

    if direction == "LONG":
        extended = candle.high > position.highest_high
        position.highest_high = max(position.highest_high, candle.high)
    else:
        extended = candle.low < position.lowest_low
        position.lowest_low = min(position.lowest_low, candle.low)

    position.stall_count = 0 if extended else position.stall_count + 1
    if position.stall_count >= 3:
        exits.append(_exit_record(position.entry.symbol, candle.timestamp, KILL_STALL, premium, position.remaining_fraction))
        exit_audit.append(f"{AUDIT_EXIT}:{KILL_STALL}@{candle.timestamp.isoformat()}")
        position.remaining_fraction = 0.0
        return KILL_STALL

    if not position.first_target_hit and premium >= position.entry_premium * (1.0 + SCALE_OUT_PCT):
        position.first_target_hit = True
        position.awaiting_runner_confirmation = True
        position.remaining_fraction -= 0.5
        exits.append(_exit_record(position.entry.symbol, candle.timestamp, "TP1", premium, 0.5))
        exit_audit.append(f"{AUDIT_EXIT}:TP1@{candle.timestamp.isoformat()}")
        return KILL_NONE

    if position.awaiting_runner_confirmation:
        if extended:
            position.awaiting_runner_confirmation = False
        else:
            exits.append(_exit_record(position.entry.symbol, candle.timestamp, "RUNNER_FAIL", premium, position.remaining_fraction))
            exit_audit.append(f"{AUDIT_EXIT}:RUNNER_FAIL@{candle.timestamp.isoformat()}")
            position.remaining_fraction = 0.0
        return KILL_NONE

    if position.first_target_hit and premium >= position.entry_premium * (1.0 + FINAL_TARGET_PCT):
        exits.append(_exit_record(position.entry.symbol, candle.timestamp, "TP2", premium, position.remaining_fraction))
        exit_audit.append(f"{AUDIT_EXIT}:TP2@{candle.timestamp.isoformat()}")
        position.remaining_fraction = 0.0

    return KILL_NONE


def _headline_kill(candle: Candle) -> bool:
    if not candle.headline_shock or candle.open <= 0:
        return False
    return abs(candle.close - candle.open) / candle.open >= HEADLINE_MOVE_THRESHOLD


def _premium_for_contract(
    option_book: dict[datetime, list[OptionSnapshot]],
    timestamp: datetime,
    contract_id: str,
) -> float | None:
    for snapshot in option_book.get(timestamp, []):
        if snapshot.contract_id == contract_id:
            return snapshot.premium
    return None


def _exit_record(symbol: str, timestamp: datetime, reason: str, premium: float | None, fraction: float) -> ExitRecord:
    if premium is None:
        raise ValueError(f"missing premium for exit {reason} at {timestamp.isoformat()}")
    return ExitRecord(
        symbol=symbol,
        timestamp_pt=timestamp,
        reason=reason,
        premium=premium,
        fraction_closed=fraction,
    )
