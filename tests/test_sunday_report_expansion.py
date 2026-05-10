"""Tests for PRD-080 — Sunday Report Expansion Layer."""

import pytest

from cuttingboard.delivery.payload import build_report_payload
from cuttingboard.delivery.dashboard_renderer import (
    render_dashboard_html,
    _build_sunday_context,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MACRO_DRIVERS = {
    "volatility": {"symbol": "^VIX", "level": 20.0, "change_pct": 2.0},
    "dollar":     {"symbol": "DX-Y.NYB", "level": 104.0, "change_pct": 0.5},
    "rates":      {"symbol": "^TNX", "level": 4.5, "change_pct": 0.9, "change_bps": 4.0},
    "bitcoin":    {"symbol": "BTC-USD", "level": 70000.0, "change_pct": 2.0},
}

_MARKET_MAP_WITH_METALS = {
    "generation_id": "sun-001",
    "generated_at": "2025-01-05T20:00:00Z",
    "symbols": {
        "GLD": {"grade": "A", "change_pct": 0.8},
        "SLV": {"grade": "B", "change_pct": 0.5},
        "GDX": {"grade": "C", "change_pct": -0.2},
    },
}


def _coherent(payload: dict, run: dict, mm: dict | None) -> tuple[dict, dict, dict | None]:
    """Inject coherent generation_ids so PRD-116 Sunday gate sees COHERENT lineage."""
    payload.setdefault("meta", {})["generation_id"] = "sun-001"
    run["generation_id"] = "sun-001"
    if isinstance(mm, dict):
        mm.setdefault("generation_id", "sun-001")
        mm.setdefault("generated_at", "2025-01-05T20:00:00Z")
    return payload, run, mm


def _minimal_contract(session_type: str | None = None, macro_drivers: dict | None = None) -> dict:
    ss: dict = {
        "router_mode": "MIXED",
        "market_regime": "NEUTRAL",
        "intraday_state": None,
        "time_gate_open": True,
        "tradable": False,
        "stay_flat_reason": None,
    }
    if session_type is not None:
        ss["session_type"] = session_type
    return {
        "schema_version": "v2",
        "generated_at": "2025-01-05T20:00:00Z",
        "session_date": "2025-01-05",
        "mode": "sunday",
        "status": "STAY_FLAT",
        "timezone": "America/New_York",
        "system_state": ss,
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
        "macro_drivers": macro_drivers if macro_drivers is not None else {},
    }


def _minimal_run() -> dict:
    return {
        "run_id": "sunday-test",
        "generation_id": "sun-001",
        "timestamp": "2025-01-05T20:00:00Z",
        "run_at_utc": "2025-01-05T20:00:00Z",
        "mode": "SUNDAY",
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
# R1 — Sunday context block presence
# ---------------------------------------------------------------------------

class TestSundayContextBlockPresence:
    def test_sunday_context_block_present_in_sunday_premarket(self):
        contract = _minimal_contract(session_type="SUNDAY_PREMARKET", macro_drivers=_MACRO_DRIVERS)
        payload = build_report_payload(contract)
        payload, run, mm = _coherent(payload, _minimal_run(), dict(_MARKET_MAP_WITH_METALS))
        html = render_dashboard_html(payload, run, market_map=mm)
        assert "sunday-macro-context" in html
        assert "Sunday Macro Context" in html

    def test_sunday_context_block_absent_on_weekday(self):
        contract = _minimal_contract(session_type=None, macro_drivers=_MACRO_DRIVERS)
        payload = build_report_payload(contract)
        payload, run, mm = _coherent(payload, _minimal_run(), dict(_MARKET_MAP_WITH_METALS))
        html = render_dashboard_html(payload, run, market_map=mm)
        assert "sunday-macro-context" not in html
        assert "Sunday Macro Context" not in html

    def test_sunday_context_block_absent_on_other_session_type(self):
        contract = _minimal_contract(session_type="LIVE", macro_drivers=_MACRO_DRIVERS)
        payload = build_report_payload(contract)
        html = render_dashboard_html(payload, _minimal_run())
        assert "sunday-macro-context" not in html


# ---------------------------------------------------------------------------
# R3 — Context fields rendered
# ---------------------------------------------------------------------------

class TestSundayContextFields:
    def _html(self, macro_drivers=None, market_map=None) -> str:
        contract = _minimal_contract(
            session_type="SUNDAY_PREMARKET",
            macro_drivers=macro_drivers if macro_drivers is not None else _MACRO_DRIVERS,
        )
        payload = build_report_payload(contract)
        mm = dict(market_map) if isinstance(market_map, dict) else market_map
        payload, run, mm = _coherent(payload, _minimal_run(), mm)
        return render_dashboard_html(payload, run, market_map=mm)

    def test_headline_rendered(self):
        html = self._html(market_map=_MARKET_MAP_WITH_METALS)
        assert "Sunday Macro Context" in html
        assert "No Cash Session" in html

    def test_posture_rendered(self):
        html = self._html(market_map=_MARKET_MAP_WITH_METALS)
        assert "Posture" in html

    def test_dollar_context_rendered(self):
        html = self._html(market_map=_MARKET_MAP_WITH_METALS)
        assert "Dollar" in html

    def test_rates_context_rendered(self):
        html = self._html(market_map=_MARKET_MAP_WITH_METALS)
        assert "Rates" in html

    def test_volatility_context_rendered(self):
        html = self._html(market_map=_MARKET_MAP_WITH_METALS)
        assert "Volatility" in html

    def test_metals_context_rendered(self):
        html = self._html(market_map=_MARKET_MAP_WITH_METALS)
        assert "Metals" in html
        assert "GLD" in html

    def test_risk_sentiment_rendered(self):
        html = self._html(market_map=_MARKET_MAP_WITH_METALS)
        assert "Risk Sentiment" in html

    def test_monday_watch_rendered(self):
        html = self._html(market_map=_MARKET_MAP_WITH_METALS)
        assert "Monday Watch" in html


# ---------------------------------------------------------------------------
# R5 — Missing metals symbols do not crash
# ---------------------------------------------------------------------------

class TestMissingMetals:
    def test_missing_market_map_does_not_crash(self):
        # PRD-116 R3: market_map=None → lineage MISSING → Sunday context suppressed.
        # Test now asserts graceful suppression (no crash, no Sunday block).
        contract = _minimal_contract(session_type="SUNDAY_PREMARKET", macro_drivers=_MACRO_DRIVERS)
        payload = build_report_payload(contract)
        payload["meta"]["generation_id"] = "sun-001"
        html = render_dashboard_html(payload, _minimal_run(), market_map=None)
        assert "Sunday Macro Context" not in html

    def test_empty_symbols_does_not_crash(self):
        contract = _minimal_contract(session_type="SUNDAY_PREMARKET", macro_drivers=_MACRO_DRIVERS)
        payload = build_report_payload(contract)
        payload, run, mm = _coherent(payload, _minimal_run(), {"symbols": {}})
        html = render_dashboard_html(payload, run, market_map=mm)
        assert "Sunday Macro Context" in html

    def test_partial_metals_does_not_crash(self):
        contract = _minimal_contract(session_type="SUNDAY_PREMARKET", macro_drivers=_MACRO_DRIVERS)
        payload = build_report_payload(contract)
        payload, run, mm = _coherent(
            payload, _minimal_run(),
            {"symbols": {"GLD": {"grade": "A", "change_pct": 0.5}}},
        )
        html = render_dashboard_html(payload, run, market_map=mm)
        assert "Sunday Macro Context" in html
        assert "GLD" in html

    def test_build_sunday_context_missing_all_metals(self):
        ctx = _build_sunday_context(_MACRO_DRIVERS, "NEUTRAL", {"symbols": {}})
        assert "unavailable" in ctx["metals_context"]

    def test_build_sunday_context_none_market_map(self):
        ctx = _build_sunday_context(_MACRO_DRIVERS, "NEUTRAL", None)
        assert "unavailable" in ctx["metals_context"]


# ---------------------------------------------------------------------------
# R6 — monday_watch must not contain ALLOW_TRADE or TRADE ACTIVE
# ---------------------------------------------------------------------------

class TestMondayWatchLanguage:
    _POSTURES = [
        "RISK_ON", "RISK_OFF", "NEUTRAL", "CHAOTIC",
        "AGGRESSIVE_LONG", "CONTROLLED_LONG", "DEFENSIVE_SHORT",
        "STAY_FLAT", "UNKNOWN",
    ]

    @pytest.mark.parametrize("posture", _POSTURES)
    def test_monday_watch_no_allow_trade(self, posture):
        ctx = _build_sunday_context(_MACRO_DRIVERS, posture, _MARKET_MAP_WITH_METALS)
        assert "ALLOW_TRADE" not in ctx["monday_watch"]

    @pytest.mark.parametrize("posture", _POSTURES)
    def test_monday_watch_no_trade_active(self, posture):
        ctx = _build_sunday_context(_MACRO_DRIVERS, posture, _MARKET_MAP_WITH_METALS)
        assert "TRADE ACTIVE" not in ctx["monday_watch"]


# ---------------------------------------------------------------------------
# R4 — Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_identical_inputs_produce_identical_context(self):
        ctx1 = _build_sunday_context(_MACRO_DRIVERS, "NEUTRAL", _MARKET_MAP_WITH_METALS)
        ctx2 = _build_sunday_context(_MACRO_DRIVERS, "NEUTRAL", _MARKET_MAP_WITH_METALS)
        assert ctx1 == ctx2

    def test_identical_inputs_produce_identical_html(self):
        contract = _minimal_contract(session_type="SUNDAY_PREMARKET", macro_drivers=_MACRO_DRIVERS)
        payload = build_report_payload(contract)
        html1 = render_dashboard_html(payload, _minimal_run(), market_map=_MARKET_MAP_WITH_METALS)
        html2 = render_dashboard_html(payload, _minimal_run(), market_map=_MARKET_MAP_WITH_METALS)
        assert html1 == html2


# ---------------------------------------------------------------------------
# R7 — Contract isolation: build_report_payload unchanged
# ---------------------------------------------------------------------------

class TestContractIsolation:
    def test_payload_schema_unchanged(self):
        from cuttingboard.delivery.payload import assert_valid_payload
        contract = _minimal_contract(session_type="SUNDAY_PREMARKET", macro_drivers=_MACRO_DRIVERS)
        build_report_payload(contract)
        # assert_valid_payload must not raise — schema is unchanged
        # macro_drivers is empty in minimal contract for this call
        contract2 = _minimal_contract(session_type="SUNDAY_PREMARKET")
        payload2 = build_report_payload(contract2)
        assert_valid_payload(payload2)

    def test_sunday_context_not_in_payload_sections(self):
        contract = _minimal_contract(session_type="SUNDAY_PREMARKET", macro_drivers=_MACRO_DRIVERS)
        payload = build_report_payload(contract)
        assert "sunday_context" not in payload["sections"]
