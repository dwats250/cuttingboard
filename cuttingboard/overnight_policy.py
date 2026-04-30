"""Deterministic EOD overnight exit guidance layer."""

from __future__ import annotations

import copy
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from cuttingboard import config, time_utils

ALLOW_HOLD = "ALLOW_HOLD"
REDUCE_POSITION = "REDUCE_POSITION"
FORCE_EXIT = "FORCE_EXIT"
VALID_DECISIONS = frozenset({ALLOW_HOLD, REDUCE_POSITION, FORCE_EXIT})

REASON_DTE_TOO_LOW = "DTE_TOO_LOW"
REASON_NEAR_KEY_LEVEL = "NEAR_KEY_LEVEL"
REASON_REGIME_UNSTABLE = "REGIME_UNSTABLE"
REASON_NO_EXPANSION_SUPPORT = "NO_EXPANSION_SUPPORT"
REASON_SPREAD_FRAGILITY = "SPREAD_FRAGILITY"
REASON_PASS_ALL = "PASS_ALL"
VALID_REASONS = frozenset(
    {
        REASON_DTE_TOO_LOW,
        REASON_NEAR_KEY_LEVEL,
        REASON_REGIME_UNSTABLE,
        REASON_NO_EXPANSION_SUPPORT,
        REASON_SPREAD_FRAGILITY,
        REASON_PASS_ALL,
    }
)

KEY_LEVEL_TYPES = frozenset(
    {
        "VWAP",
        "ORB_HIGH",
        "ORB_LOW",
        "PRIOR_HIGH",
        "PRIOR_LOW",
        "EMA9",
        "EMA21",
        "EMA50",
    }
)

_SEVERITY = {
    ALLOW_HOLD: 0,
    REDUCE_POSITION: 1,
    FORCE_EXIT: 2,
}
_DECISION_BY_SEVERITY = {value: key for key, value in _SEVERITY.items()}


def apply_overnight_policy(
    *,
    contract: dict[str, Any] | None,
    market_map: dict[str, Any] | None,
    timestamp: datetime,
) -> dict[str, Any] | None:
    """Return contract annotated with EOD overnight policy, or unchanged outside EOD."""
    if not _is_eod_window(timestamp):
        return contract

    _validate_required_inputs(contract, market_map)
    assert contract is not None
    assert market_map is not None

    annotated = copy.deepcopy(contract)
    candidates = annotated["trade_candidates"]
    regime = annotated["system_state"].get("market_regime")
    continuation_enabled = annotated["market_context"].get("continuation_enabled")

    for candidate in candidates:
        candidate["overnight_policy"] = _evaluate_candidate(
            candidate=candidate,
            market_map=market_map,
            market_regime=regime,
            continuation_enabled=continuation_enabled,
        )

    return annotated


def _is_eod_window(timestamp: datetime) -> bool:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    now_et = time_utils.convert_utc_to_et(timestamp)
    close_dt = now_et.replace(
        hour=config.OVERNIGHT_POLICY_MARKET_CLOSE_ET.hour,
        minute=config.OVERNIGHT_POLICY_MARKET_CLOSE_ET.minute,
        second=0,
        microsecond=0,
    )
    start_dt = close_dt - timedelta(minutes=config.OVERNIGHT_POLICY_EOD_WINDOW_MINUTES)
    return start_dt <= now_et < close_dt


def _validate_required_inputs(contract: dict[str, Any] | None, market_map: dict[str, Any] | None) -> None:
    if contract is None or not isinstance(contract, dict):
        raise RuntimeError("Missing required overnight policy input: contract")
    for key in ("trade_candidates", "system_state", "market_context"):
        if key not in contract:
            raise RuntimeError(f"Missing required overnight policy input: contract[{key!r}]")
    if not isinstance(contract["trade_candidates"], list):
        raise RuntimeError("Missing required overnight policy input: contract['trade_candidates']")
    if not isinstance(contract["system_state"], dict):
        raise RuntimeError("Missing required overnight policy input: contract['system_state']")
    if not isinstance(contract["market_context"], dict):
        raise RuntimeError("Missing required overnight policy input: contract['market_context']")
    if market_map is None or not isinstance(market_map, dict):
        raise RuntimeError("Missing required overnight policy input: market_map")


def _evaluate_candidate(
    *,
    candidate: dict[str, Any],
    market_map: dict[str, Any],
    market_regime: Any,
    continuation_enabled: Any,
) -> dict[str, str]:
    dte = _parse_dte(candidate.get("timeframe"))

    if dte is not None and dte < config.OVERNIGHT_POLICY_HARD_EXIT_DTE:
        decision = FORCE_EXIT
        reason = REASON_DTE_TOO_LOW
    elif market_regime == "CHAOTIC":
        decision = FORCE_EXIT
        reason = REASON_REGIME_UNSTABLE
    elif _near_key_level(candidate, market_map):
        decision = FORCE_EXIT
        reason = REASON_NEAR_KEY_LEVEL
    elif dte is None or dte < config.OVERNIGHT_POLICY_MIN_HOLD_DTE:
        decision = FORCE_EXIT
        reason = REASON_DTE_TOO_LOW
    elif continuation_enabled is not True:
        decision = REDUCE_POSITION
        reason = REASON_NO_EXPANSION_SUPPORT
    else:
        decision = ALLOW_HOLD
        reason = REASON_PASS_ALL

    if _is_spread(candidate) and decision != FORCE_EXIT:
        decision = _increase_severity(decision)
        reason = REASON_SPREAD_FRAGILITY

    return {"decision": decision, "reason": reason}


def _parse_dte(value: Any) -> float | None:
    if value is None:
        return None
    try:
        dte = float(value)
    except (TypeError, ValueError):
        return None
    return dte if math.isfinite(dte) else None


def _near_key_level(candidate: dict[str, Any], market_map: dict[str, Any]) -> bool:
    entry = _parse_finite_positive_float(candidate.get("entry"))
    if entry is None:
        return True

    symbol = candidate.get("symbol")
    symbols = market_map.get("symbols")
    if not isinstance(symbols, dict) or not symbol or symbol not in symbols:
        return True

    symbol_record = symbols.get(symbol)
    if not isinstance(symbol_record, dict):
        return True
    watch_zones = symbol_record.get("watch_zones")
    if watch_zones is None or not isinstance(watch_zones, list):
        return True

    for zone in watch_zones:
        if not isinstance(zone, dict):
            continue
        if zone.get("type") not in KEY_LEVEL_TYPES:
            continue
        level = _parse_finite_positive_float(zone.get("level"))
        if level is None:
            continue
        distance_pct = abs(level - entry) / entry
        if distance_pct <= config.OVERNIGHT_POLICY_KEY_LEVEL_PROXIMITY_PCT:
            return True
    return False


def _parse_finite_positive_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0:
        return None
    return number


def _is_spread(candidate: dict[str, Any]) -> bool:
    return "SPREAD" in str(candidate.get("strategy_tag") or "").upper()


def _increase_severity(decision: str) -> str:
    severity = min(_SEVERITY[decision] + 1, _SEVERITY[FORCE_EXIT])
    return _DECISION_BY_SEVERITY[severity]
