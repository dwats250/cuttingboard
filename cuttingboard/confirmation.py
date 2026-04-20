"""Minimal, contract-compatible confirmation primitives for the intraday engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

DIRECTION_UP = "UP"
DIRECTION_DOWN = "DOWN"

STATE_IDLE = "IDLE"
STATE_BREAK_ONLY = "BREAK_ONLY"
STATE_HOLD_CONFIRMED = "HOLD_CONFIRMED"
STATE_FAILURE_CONFIRMED = "FAILURE_CONFIRMED"

_HOLD_CLOSES_REQUIRED = 3


@dataclass(slots=True)
class LevelConfirmation:
    level_name: str = ""
    level_price: float = 0.0
    state: str = STATE_IDLE
    direction: Optional[str] = None
    break_candle_index: Optional[int] = None
    current_candle_index: Optional[int] = None
    holding_closes: int = 0
    reclaim_active: bool = False
    trades_allowed: bool = False
    output: str = "SYSTEM_DEFAULT"
    evaluation_candles: int = 0
    reclaim_candle_index: Optional[int] = None


def _normalize_allowed_directions(allowed_directions: Optional[Iterable[str]]) -> tuple[str, ...]:
    if allowed_directions is None:
        return (DIRECTION_UP, DIRECTION_DOWN)
    return tuple(allowed_directions)


def _crosses_level(close: float, level_price: float, direction: str) -> bool:
    if direction == DIRECTION_UP:
        return close > level_price
    if direction == DIRECTION_DOWN:
        return close < level_price
    return False


def _reclaims_level(close: float, level_price: float, direction: str) -> bool:
    if direction == DIRECTION_UP:
        return close <= level_price
    if direction == DIRECTION_DOWN:
        return close >= level_price
    return False


def _build_confirmation(
    *,
    level_name: str,
    level_price: float,
    closes: list[float],
    direction: str,
) -> LevelConfirmation:
    break_index: Optional[int] = None
    current_index = len(closes) - 1 if closes else None
    holding_closes = 0
    reclaim_candle_index: Optional[int] = None
    state = STATE_IDLE

    for idx, close in enumerate(closes):
        if break_index is None:
            if _crosses_level(close, level_price, direction):
                break_index = idx
                holding_closes = 1
                state = STATE_BREAK_ONLY
            continue

        if _crosses_level(close, level_price, direction):
            holding_closes += 1
            if holding_closes >= _HOLD_CLOSES_REQUIRED:
                state = STATE_HOLD_CONFIRMED
            continue

        if _reclaims_level(close, level_price, direction):
            reclaim_candle_index = idx
            state = STATE_FAILURE_CONFIRMED
            break

    reclaim_active = state == STATE_FAILURE_CONFIRMED
    trades_allowed = state in {STATE_HOLD_CONFIRMED, STATE_FAILURE_CONFIRMED}
    return LevelConfirmation(
        level_name=level_name,
        level_price=level_price,
        state=state,
        direction=direction if break_index is not None else None,
        break_candle_index=break_index,
        current_candle_index=current_index,
        holding_closes=holding_closes,
        reclaim_active=reclaim_active,
        trades_allowed=trades_allowed,
        evaluation_candles=len(closes),
        reclaim_candle_index=reclaim_candle_index,
    )


def evaluate_level_confirmation(
    level_name: str,
    level_price: float,
    closes: Iterable[float],
    *,
    allowed_directions: Optional[Iterable[str]] = None,
) -> LevelConfirmation:
    """Evaluate a single level using minimal deterministic break/hold/reclaim logic."""
    close_list = list(closes)
    directions = _normalize_allowed_directions(allowed_directions)
    candidates = [
        _build_confirmation(
            level_name=level_name,
            level_price=level_price,
            closes=close_list,
            direction=direction,
        )
        for direction in directions
    ]
    active = [candidate for candidate in candidates if candidate.state != STATE_IDLE]
    if not active:
        return LevelConfirmation(
            level_name=level_name,
            level_price=level_price,
            current_candle_index=len(close_list) - 1 if close_list else None,
            evaluation_candles=len(close_list),
        )

    state_rank = {
        STATE_HOLD_CONFIRMED: 3,
        STATE_FAILURE_CONFIRMED: 2,
        STATE_BREAK_ONLY: 1,
    }
    return max(
        active,
        key=lambda candidate: (
            state_rank[candidate.state],
            -1 if candidate.break_candle_index is None else candidate.break_candle_index,
            -1 if candidate.current_candle_index is None else candidate.current_candle_index,
        ),
    )
