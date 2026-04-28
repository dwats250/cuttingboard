"""Tests for PRD-027: build_premarket_report."""
import copy

import pytest

from cuttingboard.reports.premarket import build_premarket_report

_SCHEMA_KEYS = {
    "system_state",
    "macro_context",
    "key_levels",
    "scenarios",
    "focus_list",
    "invalidation",
}
_SYSTEM_STATE_KEYS = {"market_regime", "tradable", "stay_flat_reason", "status"}
_MACRO_CONTEXT_KEYS = {
    "volatility_state",
    "correlation_state",
    "correlation_risk_modifier",
    "expansion_enabled",
}
_KEY_LEVELS_KEYS = {"prior_high", "prior_low", "overnight_high", "overnight_low", "gap_direction"}
_SCENARIO_KEYS = {"id", "condition", "expected_behavior", "preferred_direction"}


def _make_contract(
    market_regime: str | None = "NEUTRAL",
    tradable: bool = True,
    stay_flat_reason: str | None = None,
    status: str = "SUCCESS",
    trade_candidates: list | None = None,
    continuation_enabled: bool | None = None,
    correlation: dict | None = None,
) -> dict:
    return {
        "status": status,
        "system_state": {
            "market_regime": market_regime,
            "tradable": tradable,
            "stay_flat_reason": stay_flat_reason,
        },
        "market_context": {
            "continuation_enabled": continuation_enabled,
        },
        "trade_candidates": trade_candidates or [],
        "correlation": correlation,
    }


class TestSchemaExact:
    def test_top_level_keys(self):
        report = build_premarket_report(_make_contract())
        assert set(report.keys()) == _SCHEMA_KEYS

    def test_system_state_keys(self):
        report = build_premarket_report(_make_contract())
        assert set(report["system_state"].keys()) == _SYSTEM_STATE_KEYS

    def test_macro_context_keys(self):
        report = build_premarket_report(_make_contract())
        assert set(report["macro_context"].keys()) == _MACRO_CONTEXT_KEYS

    def test_key_levels_keys(self):
        report = build_premarket_report(_make_contract())
        assert set(report["key_levels"].keys()) == _KEY_LEVELS_KEYS

    def test_scenario_keys(self):
        report = build_premarket_report(_make_contract())
        for s in report["scenarios"]:
            assert set(s.keys()) == _SCENARIO_KEYS

    def test_focus_list_keys(self):
        candidates = [{"symbol": "NVDA", "direction": "LONG", "strategy_tag": "BULL_CALL", "entry_mode": None}]
        report = build_premarket_report(_make_contract(trade_candidates=candidates))
        for item in report["focus_list"]:
            assert set(item.keys()) == {"symbol", "bias", "condition"}

    def test_no_execution_fields(self):
        report = build_premarket_report(_make_contract())
        text = str(report)
        for field in ("entry", "stop", "target"):
            assert field not in text.lower().replace("system_state", "").replace("stay_flat_reason", "")


class TestScenarioCount:
    @pytest.mark.parametrize("regime", ["RISK_ON", "RISK_OFF", "NEUTRAL"])
    def test_three_scenarios_for_known_regime(self, regime):
        report = build_premarket_report(_make_contract(market_regime=regime))
        assert len(report["scenarios"]) == 3

    def test_two_scenarios_for_chaotic(self):
        report = build_premarket_report(_make_contract(market_regime="CHAOTIC"))
        assert len(report["scenarios"]) == 2

    def test_two_scenarios_for_unknown_regime(self):
        report = build_premarket_report(_make_contract(market_regime=None))
        assert len(report["scenarios"]) == 2

    @pytest.mark.parametrize("regime", ["RISK_ON", "RISK_OFF", "NEUTRAL", "CHAOTIC", None])
    def test_minimum_two_scenarios_always(self, regime):
        report = build_premarket_report(_make_contract(market_regime=regime))
        assert len(report["scenarios"]) >= 2


class TestInvalidation:
    def test_not_tradable_with_reason_prepends_reason(self):
        report = build_premarket_report(
            _make_contract(tradable=False, stay_flat_reason="STAY_FLAT posture")
        )
        assert len(report["invalidation"]) >= 1
        assert "STAY_FLAT posture" in report["invalidation"][0]

    def test_not_tradable_without_reason_has_fallback(self):
        report = build_premarket_report(_make_contract(tradable=False, stay_flat_reason=None))
        assert len(report["invalidation"]) >= 1
        assert "Tradable == False" in report["invalidation"][0]

    def test_tradable_true_no_stay_flat_prefix(self):
        report = build_premarket_report(_make_contract(tradable=True))
        for item in report["invalidation"]:
            assert "Tradable == False" not in item
            assert "System stay-flat:" not in item


class TestMacroContext:
    @pytest.mark.parametrize("regime,expected", [
        ("CHAOTIC", "ELEVATED"),
        ("RISK_OFF", "CAUTIONARY"),
        ("NEUTRAL", "NEUTRAL"),
        ("RISK_ON", "SUBDUED"),
        (None, None),
    ])
    def test_volatility_state_derivation(self, regime, expected):
        report = build_premarket_report(_make_contract(market_regime=regime))
        assert report["macro_context"]["volatility_state"] == expected

    def test_correlation_fields_when_present(self):
        corr = {"state": "ALIGNED", "risk_modifier": 0.8}
        report = build_premarket_report(_make_contract(correlation=corr))
        assert report["macro_context"]["correlation_state"] == "ALIGNED"
        assert report["macro_context"]["correlation_risk_modifier"] == 0.8

    def test_correlation_fields_null_when_absent(self):
        report = build_premarket_report(_make_contract(correlation=None))
        assert report["macro_context"]["correlation_state"] is None
        assert report["macro_context"]["correlation_risk_modifier"] is None

    def test_expansion_enabled_from_continuation(self):
        report = build_premarket_report(_make_contract(continuation_enabled=True))
        assert report["macro_context"]["expansion_enabled"] is True


class TestKeyLevels:
    def test_all_key_levels_are_null(self):
        report = build_premarket_report(_make_contract())
        for v in report["key_levels"].values():
            assert v is None


class TestFocusList:
    def test_max_five_candidates(self):
        candidates = [
            {"symbol": f"SYM{i}", "direction": "LONG", "strategy_tag": "BULL_CALL", "entry_mode": None}
            for i in range(8)
        ]
        report = build_premarket_report(_make_contract(trade_candidates=candidates))
        assert len(report["focus_list"]) == 5

    def test_empty_when_no_candidates(self):
        report = build_premarket_report(_make_contract(trade_candidates=[]))
        assert report["focus_list"] == []

    def test_symbol_and_bias_populated(self):
        candidates = [{"symbol": "NVDA", "direction": "LONG", "strategy_tag": "BULL_CALL", "entry_mode": None}]
        report = build_premarket_report(_make_contract(trade_candidates=candidates))
        assert report["focus_list"][0]["symbol"] == "NVDA"
        assert report["focus_list"][0]["bias"] == "LONG"


class TestImmutability:
    def test_contract_not_modified(self):
        contract = _make_contract()
        original = copy.deepcopy(contract)
        build_premarket_report(contract)
        assert contract == original


class TestDeterminism:
    def test_identical_inputs_produce_identical_output(self):
        contract = _make_contract(market_regime="RISK_ON", tradable=True)
        r1 = build_premarket_report(contract)
        r2 = build_premarket_report(contract)
        assert r1 == r2
