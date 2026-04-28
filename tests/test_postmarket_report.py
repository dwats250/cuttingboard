"""Tests for PRD-027: build_postmarket_report."""
import copy

import pytest

from cuttingboard.reports.postmarket import build_postmarket_report

_SCHEMA_KEYS = {
    "system_outcome",
    "expectation_vs_reality",
    "trade_summary",
    "rejection_breakdown",
    "regime_validation",
    "deterministic_observations",
}
_SYSTEM_OUTCOME_KEYS = {"market_regime", "tradable", "stay_flat_reason", "status"}
_EVR_KEYS = {"result", "notes"}
_TRADE_SUMMARY_KEYS = {"qualified_count", "watchlist_count", "rejected_count"}
_REJECTION_BREAKDOWN_KEYS = {"regime", "qualification", "watchlist"}
_REGIME_VALIDATION_KEYS = {"persisted", "flipped"}
_VALID_EVR_RESULTS = {"MATCH", "PARTIAL", "MISS", "NO_EXPECTATION"}


def _make_contract(
    market_regime: str | None = "NEUTRAL",
    tradable: bool = True,
    stay_flat_reason: str | None = None,
    status: str = "SUCCESS",
    qualified_count: int = 0,
    continuation_rejected_count: int | None = None,
    continuation_enabled: bool | None = None,
    rejections: list | None = None,
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
        "trade_candidates": [],
        "rejections": rejections or [],
        "audit_summary": {
            "qualified_count": qualified_count,
            "continuation_rejected_count": continuation_rejected_count,
        },
        "correlation": correlation,
    }


def _run_record(regime: str, posture: str = "AGGRESSIVE_LONG") -> dict:
    return {
        "run_at_utc": "2026-04-27T12:00:00+00:00",
        "outcome": "TRADE",
        "regime": regime,
        "posture": posture,
    }


class TestSchemaExact:
    def test_top_level_keys(self):
        report = build_postmarket_report(_make_contract(), [])
        assert set(report.keys()) == _SCHEMA_KEYS

    def test_system_outcome_keys(self):
        report = build_postmarket_report(_make_contract(), [])
        assert set(report["system_outcome"].keys()) == _SYSTEM_OUTCOME_KEYS

    def test_evr_keys(self):
        report = build_postmarket_report(_make_contract(), [])
        assert set(report["expectation_vs_reality"].keys()) == _EVR_KEYS

    def test_trade_summary_keys(self):
        report = build_postmarket_report(_make_contract(), [])
        assert set(report["trade_summary"].keys()) == _TRADE_SUMMARY_KEYS

    def test_rejection_breakdown_keys(self):
        report = build_postmarket_report(_make_contract(), [])
        assert set(report["rejection_breakdown"].keys()) == _REJECTION_BREAKDOWN_KEYS

    def test_regime_validation_keys(self):
        report = build_postmarket_report(_make_contract(), [])
        assert set(report["regime_validation"].keys()) == _REGIME_VALIDATION_KEYS

    def test_no_execution_fields(self):
        report = build_postmarket_report(_make_contract(), [])
        text = str(report)
        for f in ("entry", "stop", "target"):
            assert f not in text.lower().replace("system_outcome", "").replace("stay_flat_reason", "")


class TestExpectationVsReality:
    def test_no_history_gives_no_expectation(self):
        report = build_postmarket_report(_make_contract(), [])
        assert report["expectation_vs_reality"]["result"] == "NO_EXPECTATION"

    def test_result_always_set(self):
        for history in [[], [_run_record("NEUTRAL")], [_run_record("RISK_ON")]]:
            report = build_postmarket_report(_make_contract(market_regime="NEUTRAL", tradable=False), history)
            assert report["expectation_vs_reality"]["result"] in _VALID_EVR_RESULTS

    def test_match_same_regime_same_tradable(self):
        history = [_run_record("NEUTRAL", posture="STAY_FLAT")]
        report = build_postmarket_report(_make_contract(market_regime="NEUTRAL", tradable=False), history)
        assert report["expectation_vs_reality"]["result"] == "MATCH"

    def test_partial_same_regime_different_tradable(self):
        history = [_run_record("NEUTRAL", posture="AGGRESSIVE_LONG")]
        report = build_postmarket_report(_make_contract(market_regime="NEUTRAL", tradable=False), history)
        assert report["expectation_vs_reality"]["result"] == "PARTIAL"

    def test_miss_different_regime(self):
        history = [_run_record("RISK_ON")]
        report = build_postmarket_report(_make_contract(market_regime="NEUTRAL"), history)
        assert report["expectation_vs_reality"]["result"] == "MISS"

    def test_notes_non_empty(self):
        report = build_postmarket_report(_make_contract(), [_run_record("NEUTRAL")])
        assert report["expectation_vs_reality"]["notes"]


class TestRejectionBreakdown:
    def test_counts_by_stage(self):
        rejections = [
            {"stage": "REGIME", "reason": "STAY_FLAT"},
            {"stage": "QUALIFICATION", "reason": "hard gate"},
            {"stage": "QUALIFICATION", "reason": "hard gate 2"},
            {"stage": "WATCHLIST", "reason": "soft miss"},
        ]
        report = build_postmarket_report(_make_contract(rejections=rejections), [])
        assert report["rejection_breakdown"]["regime"] == 1
        assert report["rejection_breakdown"]["qualification"] == 2
        assert report["rejection_breakdown"]["watchlist"] == 1

    def test_empty_rejections_all_zero(self):
        report = build_postmarket_report(_make_contract(rejections=[]), [])
        assert report["rejection_breakdown"] == {"regime": 0, "qualification": 0, "watchlist": 0}

    def test_trade_summary_matches_rejections(self):
        rejections = [
            {"stage": "QUALIFICATION", "reason": "hard gate"},
            {"stage": "WATCHLIST", "reason": "soft miss"},
            {"stage": "WATCHLIST", "reason": "soft miss 2"},
        ]
        report = build_postmarket_report(
            _make_contract(rejections=rejections, qualified_count=2), []
        )
        assert report["trade_summary"]["qualified_count"] == 2
        assert report["trade_summary"]["rejected_count"] == 1
        assert report["trade_summary"]["watchlist_count"] == 2


class TestRegimeValidation:
    def test_empty_history_both_false(self):
        report = build_postmarket_report(_make_contract(market_regime="NEUTRAL"), [])
        assert report["regime_validation"] == {"persisted": False, "flipped": False}

    def test_persisted_when_all_same(self):
        history = [_run_record("NEUTRAL"), _run_record("NEUTRAL")]
        report = build_postmarket_report(_make_contract(market_regime="NEUTRAL"), history)
        assert report["regime_validation"]["persisted"] is True
        assert report["regime_validation"]["flipped"] is False

    def test_flipped_when_any_different(self):
        history = [_run_record("NEUTRAL"), _run_record("RISK_ON")]
        report = build_postmarket_report(_make_contract(market_regime="NEUTRAL"), history)
        assert report["regime_validation"]["flipped"] is True
        assert report["regime_validation"]["persisted"] is False


class TestDeterministicObservations:
    def test_returns_list(self):
        report = build_postmarket_report(_make_contract(), [])
        assert isinstance(report["deterministic_observations"], list)

    def test_qualified_count_zero_observation(self):
        report = build_postmarket_report(_make_contract(qualified_count=0), [])
        obs = report["deterministic_observations"]
        assert any("No trade candidates qualified" in o for o in obs)

    def test_qualified_count_nonzero_observation(self):
        report = build_postmarket_report(_make_contract(qualified_count=3), [])
        obs = report["deterministic_observations"]
        assert any("3 candidate(s) qualified" in o for o in obs)

    def test_continuation_disabled_observation(self):
        report = build_postmarket_report(_make_contract(continuation_enabled=False), [])
        obs = report["deterministic_observations"]
        assert any("Continuation disabled" in o for o in obs)

    def test_continuation_enabled_observation(self):
        report = build_postmarket_report(_make_contract(continuation_enabled=True), [])
        obs = report["deterministic_observations"]
        assert any("Continuation enabled" in o for o in obs)

    def test_correlation_observation_when_present(self):
        corr = {"state": "ALIGNED", "risk_modifier": 0.5}
        report = build_postmarket_report(_make_contract(correlation=corr), [])
        obs = report["deterministic_observations"]
        assert any("ALIGNED" in o for o in obs)

    def test_stay_flat_observation_when_not_tradable(self):
        report = build_postmarket_report(
            _make_contract(tradable=False, stay_flat_reason="STAY_FLAT posture"), []
        )
        obs = report["deterministic_observations"]
        assert any("STAY_FLAT posture" in o for o in obs)

    def test_notification_records_excluded_from_history(self):
        notification_record = {
            "event": "notification",
            "transport": "telegram",
            "alert_title": "NO TRADE",
        }
        report = build_postmarket_report(_make_contract(), [notification_record])
        assert report["expectation_vs_reality"]["result"] == "NO_EXPECTATION"


class TestImmutability:
    def test_contract_not_modified(self):
        contract = _make_contract()
        original = copy.deepcopy(contract)
        build_postmarket_report(contract, [])
        assert contract == original

    def test_run_history_not_modified(self):
        history = [_run_record("NEUTRAL")]
        original = copy.deepcopy(history)
        build_postmarket_report(_make_contract(), history)
        assert history == original


class TestDeterminism:
    def test_identical_inputs_produce_identical_output(self):
        contract = _make_contract(market_regime="RISK_ON")
        history = [_run_record("NEUTRAL")]
        r1 = build_postmarket_report(contract, history)
        r2 = build_postmarket_report(contract, history)
        assert r1 == r2
