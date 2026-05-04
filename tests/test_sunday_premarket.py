"""Tests for PRD-077 — Sunday Futures Pre-Report."""

from datetime import date, datetime, timezone, timedelta


from cuttingboard.runtime import MODE_LIVE, MODE_SUNDAY, _resolve_effective_mode
from cuttingboard.delivery.payload import build_report_payload
from cuttingboard.delivery.dashboard_renderer import render_dashboard_html


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SUNDAY = date(2025, 1, 5)  # known Sunday
_MONDAY = date(2025, 1, 6)

_ET_OFFSET = timedelta(hours=-5)  # EST (close enough for unit purposes)

def _et(hour: int, minute: int) -> datetime:
    """Return a timezone-aware datetime in ET at the given hour/minute."""
    return datetime(2025, 1, 5, hour, minute, tzinfo=timezone(timedelta(hours=-5)))


def _minimal_contract(session_type: str | None = None) -> dict:
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
        "macro_drivers": {},
    }


def _minimal_run() -> dict:
    return {
        "run_id": "sunday-test",
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
# R1 — Time gate
# ---------------------------------------------------------------------------

class TestTimeGate:
    def test_sunday_at_1530_et_resolves_to_sunday_mode(self):
        result = _resolve_effective_mode(MODE_LIVE, _SUNDAY, _et(15, 30))
        assert result == MODE_SUNDAY

    def test_sunday_after_1530_et_resolves_to_sunday_mode(self):
        result = _resolve_effective_mode(MODE_LIVE, _SUNDAY, _et(16, 0))
        assert result == MODE_SUNDAY

    def test_sunday_before_1530_et_resolves_to_live_mode(self):
        result = _resolve_effective_mode(MODE_LIVE, _SUNDAY, _et(14, 59))
        assert result == MODE_LIVE

    def test_sunday_at_1529_et_resolves_to_live_mode(self):
        result = _resolve_effective_mode(MODE_LIVE, _SUNDAY, _et(15, 29))
        assert result == MODE_LIVE

    def test_weekday_not_promoted(self):
        result = _resolve_effective_mode(MODE_LIVE, _MONDAY, _et(16, 0))
        assert result == MODE_LIVE

    def test_no_now_et_defaults_to_sunday_mode(self):
        # Backward compat: no time info → Sunday mode preserved
        result = _resolve_effective_mode(MODE_LIVE, _SUNDAY)
        assert result == MODE_SUNDAY


# ---------------------------------------------------------------------------
# R4 — Payload propagation
# ---------------------------------------------------------------------------

class TestPayloadPropagation:
    def test_session_type_present_in_meta(self):
        contract = _minimal_contract(session_type="SUNDAY_PREMARKET")
        payload = build_report_payload(contract)
        assert payload["meta"]["session_type"] == "SUNDAY_PREMARKET"

    def test_session_type_absent_on_weekday(self):
        contract = _minimal_contract(session_type=None)
        payload = build_report_payload(contract)
        assert "session_type" not in payload["meta"]


# ---------------------------------------------------------------------------
# R5 — Dashboard banner
# ---------------------------------------------------------------------------

class TestDashboardBanner:
    def _make_payload(self, session_type: str | None) -> dict:
        contract = _minimal_contract(session_type=session_type)
        return build_report_payload(contract)

    def test_banner_present_on_sunday_premarket(self):
        payload = self._make_payload("SUNDAY_PREMARKET")
        html = render_dashboard_html(payload, _minimal_run())
        assert "SUNDAY PRE-MARKET CONTEXT" in html

    def test_banner_absent_on_weekday(self):
        payload = self._make_payload(None)
        html = render_dashboard_html(payload, _minimal_run())
        assert "SUNDAY PRE-MARKET CONTEXT" not in html
