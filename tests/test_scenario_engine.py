"""Tests for PRD-030: scenario engine hardening."""
import inspect

import pytest

from cuttingboard.reports import premarket as _pm_module
from cuttingboard.reports.premarket import (
    _generate_invalidation,
    _generate_scenarios,
    build_premarket_report,
)

_ALL_REGIMES = ["RISK_ON", "RISK_OFF", "NEUTRAL", "CHAOTIC", "EXPANSION", None]
_ALL_GAPS = ["UP", "DOWN", "FLAT", None]
_LEVEL_TOKENS = {"prior_high", "prior_low", "range_mid", "gap_direction"}
_INV_TOKENS = {"prior_high", "prior_low", "range_mid", "gap_direction", "prior_close"}
_SCENARIO_KEYS = {"id", "condition", "expected_behavior", "preferred_direction"}
_VALID_DIRECTIONS = {"LONG", "SHORT", "NEUTRAL"}

_SAMPLE_LEVELS = {
    "prior_high": 452.0,
    "prior_low": 445.0,
    "prior_close": 448.0,
    "current_price": 450.0,
    "gap_direction": "FLAT",
    "range_mid": 448.5,
}


def _has_level_token(text: str, tokens: set[str] = _LEVEL_TOKENS) -> bool:
    return any(t in text for t in tokens)


def _make_contract(market_regime: str | None = "NEUTRAL", tradable: bool = True) -> dict:
    return {
        "status": "OK",
        "system_state": {"market_regime": market_regime, "tradable": tradable},
        "market_context": {},
        "trade_candidates": [],
    }


# ── R1: Scenario shape ───────────────────────────────────────────────────────


class TestScenarioShape:
    @pytest.mark.parametrize("regime", _ALL_REGIMES)
    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_required_keys_exact(self, regime, gap):
        for s in _generate_scenarios(regime, gap, _SAMPLE_LEVELS):
            assert set(s.keys()) == _SCENARIO_KEYS

    @pytest.mark.parametrize("regime", _ALL_REGIMES)
    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_preferred_direction_enum(self, regime, gap):
        for s in _generate_scenarios(regime, gap, _SAMPLE_LEVELS):
            assert s["preferred_direction"] in _VALID_DIRECTIONS

    @pytest.mark.parametrize("regime", _ALL_REGIMES)
    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_id_and_condition_are_nonempty_strings(self, regime, gap):
        for s in _generate_scenarios(regime, gap, _SAMPLE_LEVELS):
            assert isinstance(s["id"], str) and s["id"]
            assert isinstance(s["condition"], str) and s["condition"]


# ── R2: Determinism ──────────────────────────────────────────────────────────


class TestDeterminism:
    @pytest.mark.parametrize("regime,gap", [
        ("RISK_ON", "UP"), ("RISK_ON", None),
        ("RISK_OFF", "DOWN"), ("RISK_OFF", None),
        ("NEUTRAL", None), ("NEUTRAL", "UP"),
        ("CHAOTIC", None), ("EXPANSION", "UP"), ("EXPANSION", None),
        (None, None),
    ])
    def test_identical_inputs_produce_identical_scenarios(self, regime, gap):
        assert _generate_scenarios(regime, gap, _SAMPLE_LEVELS) == \
               _generate_scenarios(regime, gap, _SAMPLE_LEVELS)

    @pytest.mark.parametrize("regime", _ALL_REGIMES)
    def test_identical_inputs_produce_identical_invalidation(self, regime):
        scenarios = _generate_scenarios(regime, None, _SAMPLE_LEVELS)
        assert _generate_invalidation(regime, None, scenarios) == \
               _generate_invalidation(regime, None, scenarios)


# ── R3: Scenario count ───────────────────────────────────────────────────────


class TestScenarioCount:
    @pytest.mark.parametrize("regime,gap", [
        ("RISK_ON", "UP"), ("RISK_ON", "DOWN"), ("RISK_ON", "FLAT"),
        ("RISK_OFF", "UP"), ("RISK_OFF", "DOWN"), ("RISK_OFF", "FLAT"),
        ("EXPANSION", "UP"), ("EXPANSION", "DOWN"), ("EXPANSION", "FLAT"),
        ("CHAOTIC", None), ("CHAOTIC", "UP"),
        (None, None), (None, "DOWN"),
    ])
    def test_two_scenarios(self, regime, gap):
        assert len(_generate_scenarios(regime, gap, _SAMPLE_LEVELS)) == 2

    @pytest.mark.parametrize("regime", ["RISK_ON", "RISK_OFF", "NEUTRAL", "EXPANSION"])
    def test_three_scenarios_for_null_gap(self, regime):
        assert len(_generate_scenarios(regime, None, _SAMPLE_LEVELS)) == 3

    @pytest.mark.parametrize("regime", _ALL_REGIMES)
    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_count_within_bounds(self, regime, gap):
        n = len(_generate_scenarios(regime, gap, _SAMPLE_LEVELS))
        assert 2 <= n <= 3


# ── R4: Level token enforcement ──────────────────────────────────────────────


class TestLevelTokens:
    @pytest.mark.parametrize("regime", _ALL_REGIMES)
    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_every_condition_has_level_token(self, regime, gap):
        for s in _generate_scenarios(regime, gap, _SAMPLE_LEVELS):
            assert _has_level_token(s["condition"]), (
                f"Missing level token: regime={regime} gap={gap} "
                f"condition={s['condition']!r}"
            )


# ── R5: Regime alignment ─────────────────────────────────────────────────────


class TestRegimeAlignment:
    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_risk_on_has_long_no_short(self, gap):
        dirs = [s["preferred_direction"] for s in _generate_scenarios("RISK_ON", gap, _SAMPLE_LEVELS)]
        assert "LONG" in dirs
        assert "SHORT" not in dirs

    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_expansion_has_long_no_short(self, gap):
        dirs = [s["preferred_direction"] for s in _generate_scenarios("EXPANSION", gap, _SAMPLE_LEVELS)]
        assert "LONG" in dirs
        assert "SHORT" not in dirs

    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_risk_off_has_short_no_long(self, gap):
        dirs = [s["preferred_direction"] for s in _generate_scenarios("RISK_OFF", gap, _SAMPLE_LEVELS)]
        assert "SHORT" in dirs
        assert "LONG" not in dirs

    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_neutral_has_at_least_one_neutral(self, gap):
        dirs = [s["preferred_direction"] for s in _generate_scenarios("NEUTRAL", gap, _SAMPLE_LEVELS)]
        assert "NEUTRAL" in dirs

    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_chaotic_all_neutral(self, gap):
        for s in _generate_scenarios("CHAOTIC", gap, _SAMPLE_LEVELS):
            assert s["preferred_direction"] == "NEUTRAL"

    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_unknown_regime_all_neutral(self, gap):
        for s in _generate_scenarios(None, gap, _SAMPLE_LEVELS):
            assert s["preferred_direction"] == "NEUTRAL"


# ── R6: Gap-direction sub-branching ─────────────────────────────────────────


class TestGapDirectionSubBranching:
    def _conditions(self, regime, gap):
        return " ".join(s["condition"] for s in _generate_scenarios(regime, gap, _SAMPLE_LEVELS))

    def test_risk_on_up_references_prior_high(self):
        assert "prior_high" in self._conditions("RISK_ON", "UP")

    def test_expansion_up_references_prior_high(self):
        assert "prior_high" in self._conditions("EXPANSION", "UP")

    def test_risk_on_down_references_range_mid_or_prior_low(self):
        c = self._conditions("RISK_ON", "DOWN")
        assert "range_mid" in c or "prior_low" in c

    def test_expansion_down_references_range_mid_or_prior_low(self):
        c = self._conditions("EXPANSION", "DOWN")
        assert "range_mid" in c or "prior_low" in c

    def test_risk_off_down_references_prior_low(self):
        assert "prior_low" in self._conditions("RISK_OFF", "DOWN")

    def test_risk_off_up_references_range_mid_or_prior_high(self):
        c = self._conditions("RISK_OFF", "UP")
        assert "range_mid" in c or "prior_high" in c

    def test_neutral_any_gap_references_range_mid_or_both_bounds(self):
        for gap in _ALL_GAPS:
            c = self._conditions("NEUTRAL", gap)
            assert "range_mid" in c or ("prior_high" in c and "prior_low" in c), \
                f"NEUTRAL gap={gap!r} missing range_mid or both bounds"

    def test_chaotic_references_gap_direction_token(self):
        assert "gap_direction" in self._conditions("CHAOTIC", None)

    def test_unknown_regime_references_gap_direction_or_levels(self):
        c = self._conditions(None, None)
        assert _has_level_token(c)


# ── R7: Invalidation derivation ──────────────────────────────────────────────


class TestInvalidation:
    @pytest.mark.parametrize("regime", _ALL_REGIMES)
    def test_minimum_two_conditions(self, regime):
        scenarios = _generate_scenarios(regime, None, _SAMPLE_LEVELS)
        inv = _generate_invalidation(regime, None, scenarios)
        assert len(inv) >= 2

    @pytest.mark.parametrize("regime", _ALL_REGIMES)
    def test_all_conditions_have_level_tokens(self, regime):
        scenarios = _generate_scenarios(regime, None, _SAMPLE_LEVELS)
        for cond in _generate_invalidation(regime, None, scenarios):
            assert _has_level_token(cond, _INV_TOKENS), \
                f"No level token in invalidation: regime={regime} cond={cond!r}"

    def test_risk_on_invalidation_references_prior_high(self):
        scenarios = _generate_scenarios("RISK_ON", None, _SAMPLE_LEVELS)
        inv = _generate_invalidation("RISK_ON", None, scenarios)
        assert any("prior_high" in c for c in inv)

    def test_expansion_invalidation_references_prior_high(self):
        scenarios = _generate_scenarios("EXPANSION", None, _SAMPLE_LEVELS)
        inv = _generate_invalidation("EXPANSION", None, scenarios)
        assert any("prior_high" in c for c in inv)

    def test_risk_off_invalidation_references_prior_low(self):
        scenarios = _generate_scenarios("RISK_OFF", None, _SAMPLE_LEVELS)
        inv = _generate_invalidation("RISK_OFF", None, scenarios)
        assert any("prior_low" in c for c in inv)


# ── R8: Scenario uniqueness ──────────────────────────────────────────────────


class TestScenarioUniqueness:
    @pytest.mark.parametrize("regime", _ALL_REGIMES)
    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_no_duplicate_condition_direction_pairs(self, regime, gap):
        scenarios = _generate_scenarios(regime, gap, _SAMPLE_LEVELS)
        pairs = [(s["condition"], s["preferred_direction"]) for s in scenarios]
        assert len(pairs) == len(set(pairs))


# ── R9: Backward compatibility ───────────────────────────────────────────────


class TestBackwardCompatibility:
    @pytest.mark.parametrize("regime", ["RISK_ON", "RISK_OFF", "NEUTRAL", "CHAOTIC", None])
    def test_levels_none_does_not_raise(self, regime):
        report = build_premarket_report(_make_contract(regime), levels=None)
        assert "scenarios" in report

    def test_top_level_keys_unchanged(self):
        expected = {"system_state", "macro_context", "key_levels", "scenarios", "focus_list", "invalidation"}
        assert set(build_premarket_report(_make_contract()).keys()) == expected

    def test_key_levels_keys_unchanged(self):
        expected = {"prior_high", "prior_low", "overnight_high", "overnight_low", "gap_direction"}
        report = build_premarket_report(_make_contract())
        assert set(report["key_levels"].keys()) == expected

    def test_key_levels_null_when_no_levels(self):
        report = build_premarket_report(_make_contract())
        for v in report["key_levels"].values():
            assert v is None

    def test_key_levels_populated_when_levels_provided(self):
        levels = {**_SAMPLE_LEVELS, "gap_direction": "UP"}
        report = build_premarket_report(_make_contract("RISK_ON"), levels=levels)
        assert report["key_levels"]["prior_high"] == 452.0
        assert report["key_levels"]["gap_direction"] == "UP"

    @pytest.mark.parametrize("regime", ["RISK_ON", "RISK_OFF", "NEUTRAL"])
    def test_three_scenarios_for_known_regime_without_levels(self, regime):
        report = build_premarket_report(_make_contract(regime))
        assert len(report["scenarios"]) == 3

    def test_two_scenarios_for_chaotic_without_levels(self):
        assert len(build_premarket_report(_make_contract("CHAOTIC"))["scenarios"]) == 2

    def test_two_scenarios_for_unknown_regime_without_levels(self):
        assert len(build_premarket_report(_make_contract(None))["scenarios"]) == 2


# ── R10: EXPANSION coverage ───────────────────────────────────────────────────


class TestExpansionCoverage:
    def test_expansion_distinct_ids_from_unknown(self):
        exp_ids = {s["id"] for s in _generate_scenarios("EXPANSION", None, _SAMPLE_LEVELS)}
        unk_ids = {s["id"] for s in _generate_scenarios(None, None, _SAMPLE_LEVELS)}
        assert not exp_ids & unk_ids

    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_expansion_all_long(self, gap):
        for s in _generate_scenarios("EXPANSION", gap, _SAMPLE_LEVELS):
            assert s["preferred_direction"] == "LONG"

    @pytest.mark.parametrize("gap", _ALL_GAPS)
    def test_expansion_references_prior_high(self, gap):
        conditions = " ".join(s["condition"] for s in _generate_scenarios("EXPANSION", gap, _SAMPLE_LEVELS))
        assert "prior_high" in conditions


# ── R11: No external data dependencies ───────────────────────────────────────


class TestNoExternalDependencies:
    _BANNED = ["requests", "yfinance", "polygon", "urllib", "open(", "fetch("]

    def test_generate_scenarios_no_banned_calls(self):
        source = inspect.getsource(_pm_module._generate_scenarios)
        for term in self._BANNED:
            assert term not in source, f"Banned term {term!r} in _generate_scenarios"

    def test_generate_invalidation_no_banned_calls(self):
        source = inspect.getsource(_pm_module._generate_invalidation)
        for term in self._BANNED:
            assert term not in source, f"Banned term {term!r} in _generate_invalidation"

    def test_sub_builders_no_banned_calls(self):
        builders = [
            _pm_module._scenarios_risk_on,
            _pm_module._scenarios_expansion,
            _pm_module._scenarios_risk_off,
            _pm_module._scenarios_neutral,
            _pm_module._scenarios_chaotic,
            _pm_module._scenarios_unknown,
            _pm_module._generate_invalidation,
        ]
        for fn in builders:
            source = inspect.getsource(fn)
            for term in self._BANNED:
                assert term not in source, f"Banned term {term!r} in {fn.__name__}"
