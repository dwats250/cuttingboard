from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cuttingboard import config
from cuttingboard.contract import (
    _MACRO_DRIVER_SYMBOLS,
    assert_valid_contract,
    build_error_contract,
    build_pipeline_output_contract,
)
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.regime import AGGRESSIVE_LONG, RISK_ON, RegimeState

_NOW = datetime(2026, 4, 28, 14, 0, 0, tzinfo=timezone.utc)


def _quote(symbol: str, price: float, pct_change_decimal: float, units: str) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=price,
        pct_change_decimal=pct_change_decimal,
        volume=1_000_000.0,
        fetched_at_utc=_NOW,
        source="fixture",
        units=units,
        age_seconds=0.0,
    )


def _macro_quotes() -> dict[str, NormalizedQuote]:
    return {
        "^VIX": _quote("^VIX", 18.5, -0.02, "index_level"),
        "DX-Y.NYB": _quote("DX-Y.NYB", 104.0, 0.001, "index_level"),
        "^TNX": _quote("^TNX", 4.3, -0.003, "yield_pct"),
        "BTC-USD": _quote("BTC-USD", 65000.0, 0.015, "usd_price"),
    }


def _regime() -> RegimeState:
    return RegimeState(
        regime=RISK_ON,
        posture=AGGRESSIVE_LONG,
        confidence=0.75,
        net_score=4,
        risk_on_votes=5,
        risk_off_votes=1,
        neutral_votes=2,
        total_votes=8,
        vote_breakdown={},
        vix_level=16.0,
        vix_pct_change=-0.02,
        computed_at_utc=_NOW,
    )


class _PipelineResult:
    def __init__(self, normalized_quotes: dict[str, NormalizedQuote]):
        self.mode = "fixture"
        self.run_at_utc = _NOW
        self.date_str = "2026-04-28"
        self.regime = _regime()
        self.router_mode = "MIXED"
        self.qualification_summary = None
        self.watch_summary = None
        self.option_setups = []
        self.chain_results = {}
        self.validation_summary = None
        self.normalized_quotes = normalized_quotes
        self.raw_quotes = {}
        self.alert_sent = False
        self.report_path = "reports/2026-04-28.md"
        self.errors = []
        self.correlation = None


def _build_contract(normalized_quotes: dict[str, NormalizedQuote]) -> dict:
    return build_pipeline_output_contract(
        _PipelineResult(normalized_quotes),
        generated_at=_NOW,
        status="OK",
        artifacts={"log_path": "logs/latest_run.json"},
    )


def test_macro_drivers_present_with_exact_keys() -> None:
    contract = _build_contract(_macro_quotes())
    assert set(contract["macro_drivers"]) == {"volatility", "dollar", "rates", "bitcoin"}
    assert_valid_contract(contract)


def test_macro_drivers_symbols_match_mapping_and_config() -> None:
    contract = _build_contract(_macro_quotes())
    assert set(_MACRO_DRIVER_SYMBOLS.values()).issubset(set(config.MACRO_DRIVERS))
    for driver, symbol in _MACRO_DRIVER_SYMBOLS.items():
        block = contract["macro_drivers"].get(driver)
        if block is None:
            # PRD-122: optional drivers (e.g. "oil") may be absent when no quote
            # is supplied by the fixture; required drivers must still be present
            # and pass the symbol-identity check below.
            continue
        assert block["symbol"] == symbol


def test_macro_drivers_values_source_from_normalized_quotes() -> None:
    contract = _build_contract(_macro_quotes())
    macro = contract["macro_drivers"]
    assert macro["volatility"]["level"] == 18.5
    assert macro["volatility"]["change_pct"] == -2.0
    assert macro["dollar"]["level"] == 104.0
    assert macro["dollar"]["change_pct"] == 0.1
    assert macro["bitcoin"]["level"] == 65000.0
    assert macro["bitcoin"]["change_pct"] == 1.5


def test_rates_change_bps_uses_tnx_price_and_pct_change() -> None:
    contract = _build_contract(_macro_quotes())
    rates = contract["macro_drivers"]["rates"]
    assert rates["change_bps"] == pytest.approx(-1.29)


def test_missing_macro_symbol_raises_value_error() -> None:
    quotes = _macro_quotes()
    del quotes["BTC-USD"]
    with pytest.raises(ValueError, match="BTC-USD"):
        _build_contract(quotes)


def test_missing_macro_field_raises_value_error() -> None:
    quotes = _macro_quotes()
    quotes["^TNX"] = NormalizedQuote(
        symbol="^TNX",
        price=4.3,
        pct_change_decimal=None,
        volume=1_000_000.0,
        fetched_at_utc=_NOW,
        source="fixture",
        units="yield_pct",
        age_seconds=0.0,
    )
    with pytest.raises(ValueError, match="\\^TNX\\.pct_change_decimal"):
        _build_contract(quotes)


def test_error_contract_macro_drivers_empty_dict() -> None:
    contract = build_error_contract(generated_at=_NOW, artifacts={})
    assert contract["macro_drivers"] == {}
    assert_valid_contract(contract)


def test_no_data_mode_allows_empty_macro_drivers() -> None:
    contract = _build_contract({})
    assert contract["status"] == "OK"
    assert contract["macro_drivers"] == {}
    assert_valid_contract(contract)
