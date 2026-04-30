from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from cuttingboard.derived import DerivedMetrics
from cuttingboard import runtime
from cuttingboard.market_map import (
    PRIMARY_SYMBOLS,
    VALID_BIASES,
    VALID_CONFIDENCE,
    VALID_GRADES,
    VALID_SETUP_STATES,
    VALID_STRUCTURES,
    build_market_map,
)
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.regime import AGGRESSIVE_LONG, RegimeState, RISK_ON
from cuttingboard.structure import NORMAL_IV, TREND, StructureResult
from cuttingboard.watch import IntradayBar, IntradayMetrics


RUN_AT = datetime(2026, 4, 12, 13, 0, tzinfo=timezone.utc)
SYMBOL_FIELDS = {
    "symbol",
    "asset_group",
    "grade",
    "bias",
    "structure",
    "setup_state",
    "confidence",
    "watch_zones",
    "fib_levels",
    "what_to_look_for",
    "invalidation",
    "preferred_trade_structure",
    "reason_for_grade",
}


def _quote(symbol: str, price: float = 100.0, pct: float = 0.01) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=price,
        pct_change_decimal=pct,
        volume=1_000_000.0,
        fetched_at_utc=RUN_AT,
        source="fixture",
        units="usd_price",
        age_seconds=0.0,
    )


def _derived(symbol: str, *, extended: bool = False) -> DerivedMetrics:
    ema21 = 96.0 if extended else 99.5
    return DerivedMetrics(
        symbol=symbol,
        ema9=100.2,
        ema21=ema21,
        ema50=98.0,
        ema_aligned_bull=True,
        ema_aligned_bear=False,
        ema_spread_pct=0.007,
        atr14=1.0,
        atr_pct=0.01,
        momentum_5d=0.02,
        volume_ratio=1.4,
        computed_at_utc=RUN_AT,
        sufficient_history=True,
    )


def _structure(symbol: str) -> StructureResult:
    return StructureResult(
        symbol=symbol,
        structure=TREND,
        iv_environment=NORMAL_IV,
        is_tradeable=True,
        disqualification_reason=None,
    )


def _intraday(symbol: str) -> IntradayMetrics:
    bars = [
        IntradayBar(
            timestamp=RUN_AT,
            open=99.8,
            high=100.4,
            low=99.4,
            close=100.0,
            volume=100_000.0,
        )
    ]
    return IntradayMetrics(
        symbol=symbol,
        bars=bars,
        orb_high=100.5,
        orb_low=99.4,
        vwap=100.1,
        pdh=101.0,
        pdl=98.5,
        range_last_n=1.0,
        avg_range_prior=1.0,
        compression_ratio=0.5,
        volume_ratio=1.4,
        consecutive_expansion_count=1,
        higher_lows=True,
        lower_highs=False,
        first_expansion=False,
        wide_range_dominance=False,
    )


def _regime() -> RegimeState:
    return RegimeState(
        regime=RISK_ON,
        posture=AGGRESSIVE_LONG,
        confidence=0.75,
        net_score=5,
        risk_on_votes=5,
        risk_off_votes=0,
        neutral_votes=3,
        total_votes=8,
        vote_breakdown={},
        vix_level=17.0,
        vix_pct_change=-0.02,
        computed_at_utc=RUN_AT,
    )


def _bars() -> pd.DataFrame:
    idx = pd.date_range("2026-03-01", periods=20, freq="1D")
    return pd.DataFrame(
        {
            "Open": [100.0 + i for i in range(20)],
            "High": [101.0 + i for i in range(20)],
            "Low": [99.0 + i for i in range(20)],
            "Close": [100.5 + i for i in range(20)],
            "Volume": [1_000_000.0 for _ in range(20)],
        },
        index=idx,
    )


def _full_inputs():
    quotes = {symbol: _quote(symbol) for symbol in PRIMARY_SYMBOLS}
    derived = {symbol: _derived(symbol) for symbol in PRIMARY_SYMBOLS}
    structure = {symbol: _structure(symbol) for symbol in PRIMARY_SYMBOLS}
    intraday = {symbol: _intraday(symbol) for symbol in PRIMARY_SYMBOLS}
    return quotes, derived, structure, intraday


def _build(**overrides):
    quotes, derived, structure, intraday = _full_inputs()
    args = {
        "generated_at": RUN_AT,
        "session_date": "2026-04-12",
        "mode": "fixture",
        "run_at_utc": RUN_AT,
        "normalized_quotes": quotes,
        "derived_metrics": derived,
        "structure_results": structure,
        "intraday_metrics": intraday,
        "regime": _regime(),
        "watch_summary": None,
        "bar_windows": {},
    }
    args.update(overrides)
    return build_market_map(**args)


def test_schema_exact_match():
    result = _build()

    assert set(result) == {
        "schema_version",
        "generated_at",
        "session_date",
        "source",
        "primary_symbols",
        "symbols",
        "context",
        "data_quality",
    }
    assert result["schema_version"] == "market_map.v1"
    assert result["primary_symbols"] == list(PRIMARY_SYMBOLS)
    assert set(result["symbols"]) == set(PRIMARY_SYMBOLS)
    for symbol in PRIMARY_SYMBOLS:
        assert set(result["symbols"][symbol]) == SYMBOL_FIELDS


def test_grade_structure_setup_state_and_confidence_enums():
    result = _build()

    for record in result["symbols"].values():
        assert record["grade"] in VALID_GRADES
        assert record["bias"] in VALID_BIASES
        assert record["structure"] in VALID_STRUCTURES
        assert record["setup_state"] in VALID_SETUP_STATES
        assert record["confidence"] in VALID_CONFIDENCE


def test_a_plus_requires_alignment_structure_proximity_and_not_extended():
    result = _build()
    assert result["symbols"]["SPY"]["grade"] == "A+"

    quotes, derived, structure, intraday = _full_inputs()
    derived["SPY"] = _derived("SPY", extended=True)
    result = _build(
        normalized_quotes=quotes,
        derived_metrics=derived,
        structure_results=structure,
        intraday_metrics=intraday,
    )

    assert result["symbols"]["SPY"]["grade"] != "A+"
    assert result["symbols"]["SPY"]["setup_state"] == "EXTENDED"


def test_valid_fixture_inputs_produce_useful_visibility():
    result = _build(bar_windows={"SPY": _bars()})
    record = result["symbols"]["SPY"]

    assert record["grade"] != "F"
    assert record["watch_zones"]
    assert record["fib_levels"] is not None
    assert record["reason_for_grade"] != ""


def test_watch_zones_shape_validation():
    result = _build()
    zones = result["symbols"]["SPY"]["watch_zones"]

    assert zones
    for zone in zones:
        assert set(zone) == {"type", "level", "context"}
        assert isinstance(zone["type"], str)
        assert isinstance(zone["level"], float)
        assert isinstance(zone["context"], str)


def test_fib_calculation_from_fixed_window():
    result = _build(bar_windows={"SPY": _bars()})
    fib = result["symbols"]["SPY"]["fib_levels"]

    assert fib == {
        "source": "last_20_bars_high_low",
        "swing_high": 120.0,
        "swing_low": 99.0,
        "retracements": {
            "0.382": 111.978,
            "0.5": 109.5,
            "0.618": 107.022,
        },
    }


def test_missing_data_returns_deferred_record_not_crash():
    result = build_market_map(
        generated_at=RUN_AT,
        session_date="2026-04-12",
        mode="sunday",
        run_at_utc=RUN_AT,
        normalized_quotes={},
        derived_metrics={},
        structure_results={},
        intraday_metrics={},
        regime=None,
    )

    assert set(result["symbols"]) == set(PRIMARY_SYMBOLS)
    for record in result["symbols"].values():
        assert record["grade"] == "F"
        assert record["setup_state"] == "DATA_UNAVAILABLE"
        assert record["watch_zones"] == []
        assert record["fib_levels"] is None
        assert record["what_to_look_for"] == [
            "Market data unavailable for this run; review during live market session."
        ]
        assert record["invalidation"] == [
            "No trade structure available until price, structure, and level data are present."
        ]
        assert record["reason_for_grade"] == "Market data unavailable for this run."
        user_guidance = " ".join(
            record["what_to_look_for"] + record["invalidation"] + [record["reason_for_grade"]]
        )
        assert "missing_" not in user_guidance


def test_malformed_derived_input_degrades_to_unavailable():
    quotes, _derived_map, structure, intraday = _full_inputs()

    result = _build(
        normalized_quotes=quotes,
        derived_metrics={"SPY": object()},
        structure_results=structure,
        intraday_metrics=intraday,
    )
    record = result["symbols"]["SPY"]

    assert record["grade"] == "F"
    assert record["setup_state"] == "DATA_UNAVAILABLE"
    assert record["reason_for_grade"] == "Market data unavailable for this run."
    user_guidance = " ".join(
        record["what_to_look_for"] + record["invalidation"] + [record["reason_for_grade"]]
    )
    assert "missing_derived_metrics" not in user_guidance


def test_builder_does_not_mutate_inputs():
    quotes, derived, structure, intraday = _full_inputs()
    before = copy.deepcopy((quotes, derived, structure, intraday))

    _build(
        normalized_quotes=quotes,
        derived_metrics=derived,
        structure_results=structure,
        intraday_metrics=intraday,
    )

    assert (quotes, derived, structure, intraday) == before


def test_uso_context_only_when_present():
    quotes, derived, structure, intraday = _full_inputs()
    quotes["USO"] = _quote("USO", price=75.0, pct=0.02)
    derived["USO"] = _derived("USO")
    structure["USO"] = _structure("USO")

    result = _build(
        normalized_quotes=quotes,
        derived_metrics=derived,
        structure_results=structure,
        intraday_metrics=intraday,
    )

    assert "USO" not in result["symbols"]
    assert result["context"]["energy"]["symbol"] == "USO"
    assert result["context"]["energy"]["asset_group"] == "ENERGY_CONTEXT"


def test_market_map_module_has_no_fetch_imports():
    source = Path("cuttingboard/market_map.py").read_text(encoding="utf-8")

    for forbidden in (
        "fetch_all",
        "fetch_quote",
        "fetch_ohlcv",
        "fetch_intraday_bars",
        "requests",
        "yfinance",
        "polygon",
        "urllib",
    ):
        assert forbidden not in source


def test_market_map_output_is_deterministic_except_allowed_timestamps():
    first = _build()
    second = _build()

    first["generated_at"] = "<timestamp>"
    second["generated_at"] = "<timestamp>"
    first["source"]["run_at_utc"] = "<timestamp>"
    second["source"]["run_at_utc"] = "<timestamp>"

    assert first == second


def test_runtime_filters_already_available_bar_windows_to_primary_symbols():
    bars = _bars()

    result = runtime._market_map_bar_windows({"SPY": bars, "USO": bars, "AAPL": bars})

    assert result == {"SPY": bars}
