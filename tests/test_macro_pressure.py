from __future__ import annotations

import copy

import pytest

from cuttingboard.macro_pressure import build_macro_pressure


def _macro_drivers(
    *,
    volatility: float | None = None,
    dollar: float | None = None,
    rates: float | None = None,
    bitcoin: float | None = None,
    extra_top_level: dict | None = None,
    extra_fields: dict | None = None,
) -> dict:
    payload: dict = {}
    if volatility is not None:
        payload["volatility"] = {"change_pct": volatility}
    if dollar is not None:
        payload["dollar"] = {"change_pct": dollar}
    if rates is not None:
        payload["rates"] = {"change_bps": rates}
    if bitcoin is not None:
        payload["bitcoin"] = {"change_pct": bitcoin}
    if extra_fields:
        for key, value in extra_fields.items():
            payload.setdefault(key, {}).update(value)
    if extra_top_level:
        payload.update(extra_top_level)
    return payload


def test_empty_input_returns_all_unknown() -> None:
    assert build_macro_pressure({}, None) == {
        "volatility_pressure": "UNKNOWN",
        "dollar_pressure": "UNKNOWN",
        "rates_pressure": "UNKNOWN",
        "bitcoin_pressure": "UNKNOWN",
        "overall_pressure": "UNKNOWN",
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-0.01, "RISK_ON"),
        (0.01, "RISK_OFF"),
        (0.0, "NEUTRAL"),
        (-0.0099, "NEUTRAL"),
        (0.0099, "NEUTRAL"),
    ],
)
def test_volatility_thresholds(value: float, expected: str) -> None:
    result = build_macro_pressure(_macro_drivers(volatility=value))
    assert result["volatility_pressure"] == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-0.0025, "RISK_ON"),
        (0.0025, "RISK_OFF"),
        (0.0, "NEUTRAL"),
        (-0.0024, "NEUTRAL"),
        (0.0024, "NEUTRAL"),
    ],
)
def test_dollar_thresholds(value: float, expected: str) -> None:
    result = build_macro_pressure(_macro_drivers(dollar=value))
    assert result["dollar_pressure"] == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-3.0, "RISK_ON"),
        (3.0, "RISK_OFF"),
        (0.0, "NEUTRAL"),
        (-2.9, "NEUTRAL"),
        (2.9, "NEUTRAL"),
    ],
)
def test_rates_thresholds(value: float, expected: str) -> None:
    result = build_macro_pressure(_macro_drivers(rates=value))
    assert result["rates_pressure"] == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.01, "RISK_ON"),
        (-0.01, "RISK_OFF"),
        (0.0, "NEUTRAL"),
        (0.0099, "NEUTRAL"),
        (-0.0099, "NEUTRAL"),
    ],
)
def test_bitcoin_thresholds(value: float, expected: str) -> None:
    result = build_macro_pressure(_macro_drivers(bitcoin=value))
    assert result["bitcoin_pressure"] == expected


def test_overall_risk_on() -> None:
    result = build_macro_pressure(_macro_drivers(volatility=-0.01, bitcoin=0.01))
    assert result["overall_pressure"] == "RISK_ON"


def test_overall_risk_off() -> None:
    result = build_macro_pressure(_macro_drivers(volatility=0.01, dollar=0.0025))
    assert result["overall_pressure"] == "RISK_OFF"


def test_overall_mixed() -> None:
    result = build_macro_pressure(_macro_drivers(volatility=-0.01, dollar=0.0025))
    assert result["overall_pressure"] == "MIXED"


def test_overall_neutral() -> None:
    result = build_macro_pressure(_macro_drivers(volatility=0.0, dollar=0.0, rates=0.0, bitcoin=0.0))
    assert result["overall_pressure"] == "NEUTRAL"


def test_missing_component_returns_unknown_while_others_classify() -> None:
    result = build_macro_pressure(_macro_drivers(volatility=-0.01, dollar=0.0025))
    assert result["volatility_pressure"] == "RISK_ON"
    assert result["dollar_pressure"] == "RISK_OFF"
    assert result["rates_pressure"] == "UNKNOWN"
    assert result["bitcoin_pressure"] == "UNKNOWN"


def test_non_dict_macro_drivers_raises() -> None:
    with pytest.raises(ValueError, match="macro_drivers must be dict"):
        build_macro_pressure([])  # type: ignore[arg-type]


def test_non_dict_market_map_raises() -> None:
    with pytest.raises(ValueError, match="market_map must be dict or None"):
        build_macro_pressure({}, market_map=[])  # type: ignore[arg-type]


def test_non_dict_supported_driver_block_raises() -> None:
    with pytest.raises(ValueError, match="macro_drivers.volatility must be dict when present"):
        build_macro_pressure({"volatility": "bad"})


@pytest.mark.parametrize("value", ["0.01", True, False, float("nan"), float("inf"), -float("inf")])
def test_malformed_present_source_values_raise(value: object) -> None:
    with pytest.raises(ValueError):
        build_macro_pressure(_macro_drivers(volatility=0.0, extra_fields={"dollar": {"change_pct": value}}))


def test_returned_dict_has_exact_keys() -> None:
    result = build_macro_pressure({})
    assert set(result) == {
        "volatility_pressure",
        "dollar_pressure",
        "rates_pressure",
        "bitcoin_pressure",
        "overall_pressure",
    }


def test_macro_drivers_not_mutated() -> None:
    macro_drivers = _macro_drivers(volatility=-0.01, extra_fields={"volatility": {"symbol": "^VIX"}})
    before = copy.deepcopy(macro_drivers)
    build_macro_pressure(macro_drivers)
    assert macro_drivers == before


def test_market_map_not_mutated() -> None:
    macro_drivers = _macro_drivers(volatility=-0.01)
    market_map = {"symbols": {"SPY": {"current_price": 500.0}}}
    before = copy.deepcopy(market_map)
    build_macro_pressure(macro_drivers, market_map=market_map)
    assert market_map == before


def test_valid_market_map_does_not_change_output() -> None:
    macro_drivers = _macro_drivers(volatility=-0.01, dollar=0.0)
    result_none = build_macro_pressure(macro_drivers, market_map=None)
    result_map = build_macro_pressure(macro_drivers, market_map={"symbols": {}})
    assert result_none == result_map


def test_none_and_empty_market_map_are_identical() -> None:
    macro_drivers = _macro_drivers(volatility=-0.01, dollar=0.0)
    assert build_macro_pressure(macro_drivers, None) == build_macro_pressure(macro_drivers, {"symbols": {}})


def test_extra_macro_driver_keys_are_ignored() -> None:
    base = _macro_drivers(volatility=-0.01, bitcoin=0.01)
    with_extra = _macro_drivers(volatility=-0.01, bitcoin=0.01, extra_top_level={"credit": {"change_pct": 99.0}})
    assert build_macro_pressure(base) == build_macro_pressure(with_extra)


def test_extra_fields_inside_supported_blocks_are_ignored() -> None:
    base = _macro_drivers(volatility=-0.01, bitcoin=0.01)
    with_extra = _macro_drivers(
        volatility=-0.01,
        bitcoin=0.01,
        extra_fields={
            "volatility": {"level": 18.0, "symbol": "^VIX"},
            "bitcoin": {"level": 90000.0, "symbol": "BTC-USD"},
        },
    )
    assert build_macro_pressure(base) == build_macro_pressure(with_extra)
