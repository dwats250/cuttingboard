"""Tests for PRD-029: level awareness layer."""
from __future__ import annotations

import copy
import importlib
import pkgutil

import pytest

from cuttingboard.reports.levels import derive_key_levels
from cuttingboard.reports.premarket import _generate_scenarios, _generate_invalidation, build_premarket_report
from cuttingboard.reports.postmarket import build_postmarket_report

_LEVEL_KEYS = {"prior_high", "prior_low", "prior_close", "current_price", "gap_direction", "range_mid"}
_LEVEL_TOKENS = {"prior_high", "prior_low", "range_mid", "gap_direction"}
_VALID_GAP = {"UP", "DOWN", "FLAT"}
_VALID_EVR = {"MATCH", "PARTIAL", "MISS", "NO_EXPECTATION"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _contract(current_price: float | None = None) -> dict:
    artifacts: dict = {}
    if current_price is not None:
        artifacts["current_price"] = current_price
    return {
        "status": "SUCCESS",
        "system_state": {"market_regime": "NEUTRAL", "tradable": True},
        "market_context": {},
        "trade_candidates": [],
        "correlation": None,
        "artifacts": artifacts,
    }


def _run_record(
    *,
    run_at_utc: str = "2026-04-27T12:00:00+00:00",
    status: str = "SUCCESS",
    outcome: str = "TRADE",
    prior_high: float | None = None,
    prior_low: float | None = None,
    prior_close: float | None = None,
    posture: str = "AGGRESSIVE_LONG",
    regime: str = "RISK_ON",
) -> dict:
    record: dict = {
        "run_at_utc": run_at_utc,
        "outcome": outcome,
        "status": status,
        "posture": posture,
        "regime": regime,
    }
    if prior_high is not None:
        record["prior_high"] = prior_high
    if prior_low is not None:
        record["prior_low"] = prior_low
    if prior_close is not None:
        record["prior_close"] = prior_close
    return record


# ---------------------------------------------------------------------------
# R1 / R2 — output shape
# ---------------------------------------------------------------------------

class TestOutputShape:
    def test_exact_keys_empty_history(self):
        result = derive_key_levels(_contract(), [])
        assert set(result.keys()) == _LEVEL_KEYS

    def test_exact_keys_with_history(self):
        record = _run_record(prior_high=500.0, prior_low=490.0, prior_close=495.0)
        result = derive_key_levels(_contract(), [record])
        assert set(result.keys()) == _LEVEL_KEYS

    def test_gap_direction_valid_enum_or_null(self):
        result = derive_key_levels(_contract(), [])
        assert result["gap_direction"] is None or result["gap_direction"] in _VALID_GAP

    def test_all_null_on_empty_history_no_price(self):
        result = derive_key_levels(_contract(), [])
        assert result == {
            "prior_high": None,
            "prior_low": None,
            "prior_close": None,
            "current_price": None,
            "gap_direction": None,
            "range_mid": None,
        }


# ---------------------------------------------------------------------------
# R3 — prior values source
# ---------------------------------------------------------------------------

class TestPriorValuesSource:
    def test_null_when_empty_history(self):
        result = derive_key_levels(_contract(), [])
        assert result["prior_high"] is None
        assert result["prior_low"] is None
        assert result["prior_close"] is None

    def test_null_when_all_error_status(self):
        records = [
            _run_record(status="ERROR", prior_high=500.0, prior_low=490.0, prior_close=495.0),
            _run_record(status="ERROR", prior_high=510.0, prior_low=488.0, prior_close=505.0),
        ]
        result = derive_key_levels(_contract(), records)
        assert result["prior_high"] is None
        assert result["prior_low"] is None
        assert result["prior_close"] is None

    def test_uses_most_recent_valid_entry(self):
        records = [
            _run_record(run_at_utc="2026-04-25T12:00:00+00:00", prior_close=490.0),
            _run_record(run_at_utc="2026-04-27T12:00:00+00:00", prior_close=500.0),
            _run_record(run_at_utc="2026-04-26T12:00:00+00:00", prior_close=495.0),
        ]
        result = derive_key_levels(_contract(), records)
        assert result["prior_close"] == 500.0

    def test_skips_error_entries_uses_last_valid(self):
        records = [
            _run_record(run_at_utc="2026-04-26T12:00:00+00:00", prior_close=490.0),
            _run_record(run_at_utc="2026-04-27T12:00:00+00:00", status="ERROR", prior_close=999.0),
        ]
        result = derive_key_levels(_contract(), records)
        assert result["prior_close"] == 490.0

    def test_prior_values_absent_in_record_yield_null(self):
        record = _run_record()
        result = derive_key_levels(_contract(), [record])
        assert result["prior_high"] is None
        assert result["prior_low"] is None
        assert result["prior_close"] is None

    def test_prior_values_present_in_record(self):
        record = _run_record(prior_high=510.0, prior_low=488.0, prior_close=500.0)
        result = derive_key_levels(_contract(), [record])
        assert result["prior_high"] == 510.0
        assert result["prior_low"] == 488.0
        assert result["prior_close"] == 500.0


# ---------------------------------------------------------------------------
# R4 — current price source
# ---------------------------------------------------------------------------

class TestCurrentPriceSource:
    def test_null_when_no_artifact(self):
        result = derive_key_levels(_contract(), [])
        assert result["current_price"] is None

    def test_reads_from_artifacts(self):
        result = derive_key_levels(_contract(current_price=505.0), [])
        assert result["current_price"] == 505.0

    def test_no_external_imports_in_levels_module(self):
        import cuttingboard.reports.levels as mod
        source = open(mod.__file__).read()
        assert "import requests" not in source
        assert "import yfinance" not in source
        assert "import polygon" not in source
        assert "urllib" not in source


# ---------------------------------------------------------------------------
# R5 — gap direction classification
# ---------------------------------------------------------------------------

class TestGapDirection:
    def _levels(self, current: float, close: float) -> dict:
        record = _run_record(prior_close=close)
        return derive_key_levels(_contract(current_price=current), [record])

    def test_up_above_threshold(self):
        result = self._levels(current=501.0, close=500.0)
        assert result["gap_direction"] == "UP"

    def test_flat_at_exact_up_threshold(self):
        # current == prior_close * 1.001 exactly → FLAT (PRD uses strict >)
        close = 500.0
        current = close * 1.001
        result = self._levels(current=current, close=close)
        assert result["gap_direction"] == "FLAT"

    def test_flat_just_below_up_threshold(self):
        close = 500.0
        current = close * 1.001 - 0.001
        result = self._levels(current=current, close=close)
        assert result["gap_direction"] == "FLAT"

    def test_down_below_threshold(self):
        result = self._levels(current=499.0, close=500.0)
        assert result["gap_direction"] == "DOWN"

    def test_flat_at_exact_down_threshold(self):
        # current == prior_close * 0.999 exactly → FLAT (PRD uses strict <)
        close = 500.0
        current = close * 0.999
        result = self._levels(current=current, close=close)
        assert result["gap_direction"] == "FLAT"

    def test_flat_just_above_down_threshold(self):
        close = 500.0
        current = close * 0.999 + 0.001
        result = self._levels(current=current, close=close)
        assert result["gap_direction"] == "FLAT"

    def test_flat_no_movement(self):
        result = self._levels(current=500.0, close=500.0)
        assert result["gap_direction"] == "FLAT"

    def test_null_when_current_price_missing(self):
        record = _run_record(prior_close=500.0)
        result = derive_key_levels(_contract(), [record])
        assert result["gap_direction"] is None

    def test_null_when_prior_close_missing(self):
        result = derive_key_levels(_contract(current_price=500.0), [])
        assert result["gap_direction"] is None

    def test_null_when_both_missing(self):
        result = derive_key_levels(_contract(), [])
        assert result["gap_direction"] is None


# ---------------------------------------------------------------------------
# R6 — range midpoint
# ---------------------------------------------------------------------------

class TestRangeMid:
    def test_correct_value(self):
        record = _run_record(prior_high=510.0, prior_low=490.0)
        result = derive_key_levels(_contract(), [record])
        assert result["range_mid"] == 500.0

    def test_null_when_prior_high_missing(self):
        record = _run_record(prior_low=490.0)
        result = derive_key_levels(_contract(), [record])
        assert result["range_mid"] is None

    def test_null_when_prior_low_missing(self):
        record = _run_record(prior_high=510.0)
        result = derive_key_levels(_contract(), [record])
        assert result["range_mid"] is None

    def test_null_when_both_missing(self):
        result = derive_key_levels(_contract(), [])
        assert result["range_mid"] is None

    def test_exact_arithmetic(self):
        record = _run_record(prior_high=600.0, prior_low=400.0)
        result = derive_key_levels(_contract(), [record])
        assert result["range_mid"] == pytest.approx(500.0)


# ---------------------------------------------------------------------------
# R7 — premarket scenario level tokens
# ---------------------------------------------------------------------------

class TestScenarioLevelTokens:
    _REGIMES = ["RISK_ON", "RISK_OFF", "NEUTRAL", "CHAOTIC", "EXPANSION", None]

    def test_every_scenario_has_level_token(self):
        for regime in self._REGIMES:
            for s in _generate_scenarios(regime, None, {}):
                condition = s["condition"]
                has_token = any(token in condition for token in _LEVEL_TOKENS)
                assert has_token, f"Scenario '{s['id']}' condition missing level token: {condition!r}"

    def test_risk_on_scenarios_have_tokens(self):
        for s in _generate_scenarios("RISK_ON", None, {}):
            assert any(t in s["condition"] for t in _LEVEL_TOKENS)

    def test_risk_off_scenarios_have_tokens(self):
        for s in _generate_scenarios("RISK_OFF", None, {}):
            assert any(t in s["condition"] for t in _LEVEL_TOKENS)

    def test_neutral_scenarios_have_tokens(self):
        for s in _generate_scenarios("NEUTRAL", None, {}):
            assert any(t in s["condition"] for t in _LEVEL_TOKENS)

    def test_chaotic_scenarios_have_tokens(self):
        for s in _generate_scenarios("CHAOTIC", None, {}):
            assert any(t in s["condition"] for t in _LEVEL_TOKENS)

    def test_default_scenarios_have_tokens(self):
        for s in _generate_scenarios(None, None, {}):
            assert any(t in s["condition"] for t in _LEVEL_TOKENS)


# ---------------------------------------------------------------------------
# R8 — premarket invalidation level references
# ---------------------------------------------------------------------------

class TestInvalidationLevelReferences:
    _REGIMES = ["RISK_ON", "RISK_OFF", "NEUTRAL", "CHAOTIC", "EXPANSION", None]
    _INV_TOKENS = {"prior_high", "prior_low", "range_mid", "gap_direction", "prior_close"}

    def test_each_regime_invalidation_has_level_reference(self):
        for regime in self._REGIMES:
            scenarios = _generate_scenarios(regime, None, {})
            inv = _generate_invalidation(regime, None, scenarios)
            has_level = any(
                any(token in cond for token in self._INV_TOKENS)
                for cond in inv
            )
            assert has_level, f"Regime {regime!r} invalidation has no level-based condition"

    def test_default_invalidation_has_level_reference(self):
        scenarios = _generate_scenarios(None, None, {})
        inv = _generate_invalidation(None, None, scenarios)
        has_level = any(
            any(token in cond for token in self._INV_TOKENS)
            for cond in inv
        )
        assert has_level, "Default invalidation has no level-based condition"


# ---------------------------------------------------------------------------
# R9 — postmarket classification with levels
# ---------------------------------------------------------------------------

def _post_contract(market_regime: str = "RISK_ON", tradable: bool = True) -> dict:
    return {
        "status": "SUCCESS",
        "system_state": {"market_regime": market_regime, "tradable": tradable},
        "market_context": {},
        "trade_candidates": [],
        "rejections": [],
        "audit_summary": {"qualified_count": 0},
        "correlation": None,
    }


def _levels_dict(
    current_price: float | None = None,
    prior_high: float | None = None,
    prior_low: float | None = None,
    prior_close: float | None = None,
) -> dict:
    return {
        "prior_high": prior_high,
        "prior_low": prior_low,
        "prior_close": prior_close,
        "current_price": current_price,
        "gap_direction": None,
        "range_mid": None,
    }


class TestPostmarketClassification:
    def test_no_expectation_when_no_history(self):
        report = build_postmarket_report(_post_contract(), [], levels=_levels_dict())
        assert report["expectation_vs_reality"]["result"] == "NO_EXPECTATION"

    def test_miss_when_direction_misaligned(self):
        history = [_run_record(posture="AGGRESSIVE_LONG", regime="RISK_ON")]
        report = build_postmarket_report(
            _post_contract(market_regime="RISK_OFF", tradable=True),
            history,
            levels=_levels_dict(current_price=490.0, prior_high=500.0, prior_low=480.0),
        )
        assert report["expectation_vs_reality"]["result"] == "MISS"

    def test_match_long_above_prior_high(self):
        history = [_run_record(posture="AGGRESSIVE_LONG", regime="RISK_ON")]
        report = build_postmarket_report(
            _post_contract(market_regime="RISK_ON", tradable=True),
            history,
            levels=_levels_dict(current_price=505.0, prior_high=500.0, prior_low=480.0),
        )
        assert report["expectation_vs_reality"]["result"] == "MATCH"

    def test_partial_long_below_prior_high(self):
        history = [_run_record(posture="AGGRESSIVE_LONG", regime="RISK_ON")]
        report = build_postmarket_report(
            _post_contract(market_regime="RISK_ON", tradable=True),
            history,
            levels=_levels_dict(current_price=498.0, prior_high=500.0, prior_low=480.0),
        )
        assert report["expectation_vs_reality"]["result"] == "PARTIAL"

    def test_match_short_below_prior_low(self):
        history = [_run_record(posture="DEFENSIVE_SHORT", regime="RISK_OFF")]
        report = build_postmarket_report(
            _post_contract(market_regime="RISK_OFF", tradable=True),
            history,
            levels=_levels_dict(current_price=479.0, prior_high=500.0, prior_low=480.0),
        )
        assert report["expectation_vs_reality"]["result"] == "MATCH"

    def test_partial_short_above_prior_low(self):
        history = [_run_record(posture="DEFENSIVE_SHORT", regime="RISK_OFF")]
        report = build_postmarket_report(
            _post_contract(market_regime="RISK_OFF", tradable=True),
            history,
            levels=_levels_dict(current_price=485.0, prior_high=500.0, prior_low=480.0),
        )
        assert report["expectation_vs_reality"]["result"] == "PARTIAL"

    def test_partial_when_current_price_null(self):
        history = [_run_record(posture="AGGRESSIVE_LONG", regime="RISK_ON")]
        report = build_postmarket_report(
            _post_contract(market_regime="RISK_ON", tradable=True),
            history,
            levels=_levels_dict(current_price=None, prior_high=500.0),
        )
        assert report["expectation_vs_reality"]["result"] == "PARTIAL"

    def test_result_always_valid_enum(self):
        for posture, regime, cur, market in [
            ("AGGRESSIVE_LONG", "RISK_ON", 505.0, "RISK_ON"),
            ("AGGRESSIVE_LONG", "RISK_ON", 495.0, "RISK_ON"),
            ("DEFENSIVE_SHORT", "RISK_OFF", 479.0, "RISK_OFF"),
            ("STAY_FLAT", "NEUTRAL", None, "RISK_ON"),
        ]:
            history = [_run_record(posture=posture, regime=regime)]
            report = build_postmarket_report(
                _post_contract(market_regime=market, tradable=True),
                history,
                levels=_levels_dict(current_price=cur, prior_high=500.0, prior_low=480.0),
            )
            assert report["expectation_vs_reality"]["result"] in _VALID_EVR


# ---------------------------------------------------------------------------
# R10 — no intraday dependency
# ---------------------------------------------------------------------------

class TestNoIntradayDependency:
    def test_no_intraday_imports_in_levels(self):
        import cuttingboard.reports.levels as mod
        source = open(mod.__file__).read()
        for banned in ("intraday_state_engine", "watch.py", "ORB", "VWAP"):
            assert banned not in source


# ---------------------------------------------------------------------------
# R11 — determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_identical_inputs_yield_identical_output(self):
        record = _run_record(prior_high=510.0, prior_low=490.0, prior_close=500.0)
        c = _contract(current_price=502.0)
        r1 = derive_key_levels(c, [record])
        r2 = derive_key_levels(c, [record])
        assert r1 == r2

    def test_repeated_calls_stable(self):
        record = _run_record(prior_close=500.0)
        c = _contract(current_price=501.0)
        results = [derive_key_levels(c, [record]) for _ in range(5)]
        assert all(r == results[0] for r in results)


# ---------------------------------------------------------------------------
# R12 — no mutation
# ---------------------------------------------------------------------------

class TestNoMutation:
    def test_contract_not_mutated(self):
        record = _run_record(prior_close=500.0)
        c = _contract(current_price=501.0)
        original = copy.deepcopy(c)
        derive_key_levels(c, [record])
        assert c == original

    def test_run_history_not_mutated(self):
        record = _run_record(prior_high=510.0, prior_low=490.0, prior_close=500.0)
        history = [record]
        original = copy.deepcopy(history)
        derive_key_levels(_contract(), history)
        assert history == original


# ---------------------------------------------------------------------------
# Legacy postmarket compatibility (no levels param)
# ---------------------------------------------------------------------------

class TestLegacyPostmarketCompat:
    def test_no_levels_still_returns_valid_evr(self):
        history = [_run_record(posture="AGGRESSIVE_LONG", regime="RISK_ON")]
        report = build_postmarket_report(_post_contract(), history)
        assert report["expectation_vs_reality"]["result"] in _VALID_EVR

    def test_no_levels_no_expectation_on_empty_history(self):
        report = build_postmarket_report(_post_contract(), [])
        assert report["expectation_vs_reality"]["result"] == "NO_EXPECTATION"


# ---------------------------------------------------------------------------
# Premarket key_levels integration
# ---------------------------------------------------------------------------

class TestPremarketKeyLevels:
    def test_key_levels_populated_from_levels_dict(self):
        levels = {
            "prior_high": 510.0,
            "prior_low": 490.0,
            "prior_close": 500.0,
            "current_price": 502.0,
            "gap_direction": "FLAT",
            "range_mid": 500.0,
        }
        contract = {
            "status": "SUCCESS",
            "system_state": {"market_regime": "RISK_ON", "tradable": True},
            "market_context": {},
            "trade_candidates": [],
            "correlation": None,
        }
        report = build_premarket_report(contract, levels=levels)
        assert report["key_levels"]["prior_high"] == 510.0
        assert report["key_levels"]["prior_low"] == 490.0
        assert report["key_levels"]["gap_direction"] == "FLAT"

    def test_key_levels_null_without_levels(self):
        contract = {
            "status": "SUCCESS",
            "system_state": {"market_regime": "NEUTRAL", "tradable": True},
            "market_context": {},
            "trade_candidates": [],
            "correlation": None,
        }
        report = build_premarket_report(contract)
        assert report["key_levels"]["prior_high"] is None
        assert report["key_levels"]["gap_direction"] is None
