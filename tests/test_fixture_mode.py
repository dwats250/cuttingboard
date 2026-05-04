"""Tests for PRD-078 — Dashboard Demo Candidate Fixture Mode."""

import pytest

from cuttingboard.delivery.fixtures import FIXTURE_SYMBOLS
from cuttingboard.delivery.payload import build_report_payload
from cuttingboard.delivery.dashboard_renderer import render_dashboard_html


# ---------------------------------------------------------------------------
# Minimal contract helper (reused from test_sunday_premarket structure)
# ---------------------------------------------------------------------------

def _minimal_contract() -> dict:
    return {
        "schema_version": "v2",
        "generated_at": "2025-01-06T16:00:00Z",
        "session_date": "2025-01-06",
        "mode": "live",
        "status": "STAY_FLAT",
        "timezone": "America/New_York",
        "system_state": {
            "router_mode": "MIXED",
            "market_regime": "NEUTRAL",
            "intraday_state": None,
            "time_gate_open": True,
            "tradable": False,
            "stay_flat_reason": None,
        },
        "market_context": {
            "expansion_regime": None,
            "continuation_enabled": None,
            "imbalance_enabled": None,
            "stale_data_detected": None,
            "data_quality": None,
        },
        "trade_candidates": [],
        "rejections": [],
        "audit_summary": {
            "qualified_count": 0,
            "rejected_count": 0,
            "continuation_audit_present": False,
            "continuation_accepted_count": None,
            "continuation_rejected_count": None,
            "error_count": 0,
        },
        "artifacts": {
            "report_path": None,
            "log_path": None,
            "notification_sent": None,
        },
        "correlation": None,
        "regime": None,
        "macro_drivers": {},
    }


def _minimal_run() -> dict:
    return {
        "run_id": "fixture-test",
        "timestamp": "2025-01-06T16:00:00Z",
        "run_at_utc": "2025-01-06T16:00:00Z",
        "mode": "LIVE",
        "outcome": "NO_TRADE",
        "status": "SUCCESS",
        "regime": "NEUTRAL",
        "posture": "STAY_FLAT",
        "confidence": 0.0,
        "net_score": 0,
        "router_mode": "MIXED",
        "energy_score": 0.0,
        "index_score": 0.0,
        "permission": "No new trades permitted.",
        "kill_switch": False,
        "min_rr_applied": 3.0,
        "data_status": "ok",
        "fallback_used": False,
        "system_halted": False,
        "halt_reason": None,
        "candidates_generated": 0,
        "candidates_qualified": 0,
        "candidates_watchlist": 0,
        "chain_validation": {},
        "warnings": [],
        "errors": [],
    }


# ---------------------------------------------------------------------------
# R3 — Fixture data schema
# ---------------------------------------------------------------------------

class TestFixtureData:
    def test_fixture_symbols_has_three_entries(self):
        assert len(FIXTURE_SYMBOLS) == 3

    def test_grades_cover_aplus_a_b(self):
        grades = {v["grade"] for v in FIXTURE_SYMBOLS.values()}
        assert grades == {"A+", "A", "B"}

    def test_all_entries_have_required_keys(self):
        required = {"symbol", "grade", "bias", "structure", "setup_state",
                    "trade_framing", "invalidation", "reason_for_grade"}
        for sym, entry in FIXTURE_SYMBOLS.items():
            missing = required - set(entry)
            assert not missing, f"{sym} missing keys: {missing}"

    def test_trade_framing_has_required_keys(self):
        for sym, entry in FIXTURE_SYMBOLS.items():
            tf = entry["trade_framing"]
            assert "entry" in tf, f"{sym} missing trade_framing.entry"
            assert "if_now" in tf, f"{sym} missing trade_framing.if_now"
            assert "downgrade" in tf, f"{sym} missing trade_framing.downgrade"

    def test_invalidation_is_list(self):
        for sym, entry in FIXTURE_SYMBOLS.items():
            assert isinstance(entry["invalidation"], list), f"{sym} invalidation must be list"

    def test_deterministic_across_calls(self):
        from cuttingboard.delivery.fixtures import FIXTURE_SYMBOLS as FS2
        assert FIXTURE_SYMBOLS is FS2


# ---------------------------------------------------------------------------
# R2 — Payload flag
# ---------------------------------------------------------------------------

class TestPayloadFlag:
    def test_fixture_mode_true_sets_meta_flag(self):
        contract = _minimal_contract()
        payload = build_report_payload(contract, fixture_mode=True)
        assert payload["meta"]["fixture_mode"] is True

    def test_fixture_mode_false_omits_meta_flag(self):
        contract = _minimal_contract()
        payload = build_report_payload(contract, fixture_mode=False)
        assert "fixture_mode" not in payload["meta"]

    def test_contract_unchanged_by_fixture_mode(self):
        import copy
        contract = _minimal_contract()
        original = copy.deepcopy(contract)
        build_report_payload(contract, fixture_mode=True)
        assert contract == original


# ---------------------------------------------------------------------------
# R4 — Renderer substitution and banner
# ---------------------------------------------------------------------------

class TestRendererFixtureMode:
    def test_demo_banner_present_when_fixture_mode(self):
        payload = build_report_payload(_minimal_contract(), fixture_mode=True)
        html = render_dashboard_html(payload, _minimal_run(), fixture_mode=True)
        assert "DEMO MODE" in html

    def test_demo_banner_absent_when_not_fixture_mode(self):
        payload = build_report_payload(_minimal_contract())
        html = render_dashboard_html(payload, _minimal_run(), fixture_mode=False)
        assert "DEMO MODE" not in html

    def test_fixture_symbols_rendered_when_fixture_mode(self):
        payload = build_report_payload(_minimal_contract(), fixture_mode=True)
        html = render_dashboard_html(payload, _minimal_run(), fixture_mode=True)
        assert "SPY" in html
        assert "QQQ" in html
        assert "GDX" in html

    def test_market_map_not_mutated_by_renderer(self):
        import copy
        payload = build_report_payload(_minimal_contract(), fixture_mode=True)
        market_map = {"symbols": {"AAPL": {"grade": "C", "symbol": "AAPL"}}}
        original = copy.deepcopy(market_map)
        render_dashboard_html(payload, _minimal_run(), market_map=market_map, fixture_mode=True)
        assert market_map == original
