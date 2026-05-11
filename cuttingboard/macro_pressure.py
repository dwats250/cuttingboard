"""Deterministic macro-pressure snapshot builder."""

from __future__ import annotations

import math
from typing import Any

RISK_ON = "RISK_ON"
RISK_OFF = "RISK_OFF"
NEUTRAL = "NEUTRAL"
UNKNOWN = "UNKNOWN"
MIXED = "MIXED"

# PRD-122: `oil` is a visibility-only macro driver and is intentionally
# excluded from macro-pressure synthesis. It must NOT be added to
# _COMPONENT_KEYS or _COMPONENT_FIELDS — pressure semantics are part of
# the decision pipeline; oil contributes to the dashboard tape only.
_COMPONENT_KEYS = {
    "volatility_pressure": "volatility",
    "dollar_pressure": "dollar",
    "rates_pressure": "rates",
    "bitcoin_pressure": "bitcoin",
}

_COMPONENT_FIELDS = {
    "volatility": "change_pct",
    "dollar": "change_pct",
    "rates": "change_bps",
    "bitcoin": "change_pct",
}

_COMPONENT_ALLOWED = {RISK_ON, RISK_OFF, NEUTRAL, UNKNOWN}
_OVERALL_ALLOWED = {RISK_ON, RISK_OFF, MIXED, NEUTRAL, UNKNOWN}


def _validate_container(macro_drivers: dict, market_map: dict | None) -> None:
    if not isinstance(macro_drivers, dict):
        raise ValueError("macro_drivers must be dict")
    if market_map is not None and not isinstance(market_map, dict):
        raise ValueError("market_map must be dict or None")
    for driver in _COMPONENT_FIELDS:
        block = macro_drivers.get(driver)
        if block is not None and not isinstance(block, dict):
            raise ValueError(f"macro_drivers.{driver} must be dict when present")


def _validate_number(value: Any, path: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{path} must not be boolean")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{path} must be numeric")
    if not math.isfinite(value):
        raise ValueError(f"{path} must be finite")
    return float(value)


def _classify_driver(driver: str, block: dict[str, Any] | None) -> str:
    if block is None:
        return UNKNOWN

    field = _COMPONENT_FIELDS[driver]
    if field not in block or block[field] is None:
        return UNKNOWN

    value = _validate_number(block[field], f"macro_drivers.{driver}.{field}")
    if driver == "volatility":
        if value <= -0.01:
            return RISK_ON
        if value >= 0.01:
            return RISK_OFF
        return NEUTRAL
    if driver == "dollar":
        if value <= -0.0025:
            return RISK_ON
        if value >= 0.0025:
            return RISK_OFF
        return NEUTRAL
    if driver == "rates":
        if value <= -3.0:
            return RISK_ON
        if value >= 3.0:
            return RISK_OFF
        return NEUTRAL
    if driver == "bitcoin":
        if value >= 0.01:
            return RISK_ON
        if value <= -0.01:
            return RISK_OFF
        return NEUTRAL
    raise ValueError(f"Unsupported driver {driver!r}")


def _overall_pressure(components: list[str]) -> str:
    known = [component for component in components if component != UNKNOWN]
    if not known:
        return UNKNOWN

    risk_on_count = sum(component == RISK_ON for component in known)
    risk_off_count = sum(component == RISK_OFF for component in known)

    if risk_on_count >= 2 and risk_off_count == 0:
        return RISK_ON
    if risk_off_count >= 2 and risk_on_count == 0:
        return RISK_OFF
    if risk_on_count >= 1 and risk_off_count >= 1:
        return MIXED
    if all(component == NEUTRAL for component in known):
        return NEUTRAL
    return MIXED


def build_macro_pressure(
    macro_drivers: dict,
    market_map: dict | None = None,
) -> dict:
    _validate_container(macro_drivers, market_map)

    result = {
        component_key: _classify_driver(driver, macro_drivers.get(driver))
        for component_key, driver in _COMPONENT_KEYS.items()
    }
    for component_key in _COMPONENT_KEYS:
        if result[component_key] not in _COMPONENT_ALLOWED:
            raise ValueError(f"{component_key} produced invalid enum")

    result["overall_pressure"] = _overall_pressure(
        [
            result["volatility_pressure"],
            result["dollar_pressure"],
            result["rates_pressure"],
            result["bitcoin_pressure"],
        ]
    )
    if result["overall_pressure"] not in _OVERALL_ALLOWED:
        raise ValueError("overall_pressure produced invalid enum")
    return result
