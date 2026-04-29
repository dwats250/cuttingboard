"""Tests for the ReportPayload builder and validator (PRD-012)."""

from __future__ import annotations

import json

import pytest

from cuttingboard.delivery.payload import (
    PAYLOAD_SCHEMA_VERSION,
    assert_valid_payload,
    build_report_payload,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _minimal_contract(
    *,
    status: str = "OK",
    tradable: bool | None = True,
    market_regime: str | None = "RISK_ON",
    router_mode: str | None = "MIXED",
    qualified_count: int = 2,
    rejected_count: int = 1,
    continuation_audit_present: bool = False,
    continuation_accepted: int | None = None,
    continuation_rejected: int | None = None,
    trade_candidates: list | None = None,
    rejections: list | None = None,
    intraday_state: str | None = None,
    stay_flat_reason: str | None = None,
) -> dict:
    return {
        "schema_version": "v2",
        "generated_at": "2026-04-23T14:00:00Z",
        "session_date": "2026-04-23",
        "mode": "live",
        "status": status,
        "timezone": "America/New_York",
        "system_state": {
            "router_mode": router_mode,
            "market_regime": market_regime,
            "intraday_state": intraday_state,
            "time_gate_open": True,
            "tradable": tradable,
            "stay_flat_reason": stay_flat_reason,
        },
        "market_context": {
            "expansion_regime": None,
            "continuation_enabled": None,
            "imbalance_enabled": None,
            "stale_data_detected": False,
            "data_quality": "ok",
        },
        "trade_candidates": trade_candidates if trade_candidates is not None else [],
        "rejections": rejections if rejections is not None else [],
        "audit_summary": {
            "qualified_count": qualified_count,
            "rejected_count": rejected_count,
            "continuation_audit_present": continuation_audit_present,
            "continuation_accepted_count": continuation_accepted,
            "continuation_rejected_count": continuation_rejected,
            "error_count": 0,
        },
        "artifacts": {
            "report_path": "reports/2026-04-23.md",
            "log_path": "logs/latest_run.json",
            "notification_sent": False,
        },
        "correlation": None,
        "regime": None,
        "macro_drivers": {
            "volatility": {"symbol": "^VIX", "level": 18.5, "change_pct": -2.0},
            "dollar": {"symbol": "DX-Y.NYB", "level": 104.0, "change_pct": 0.1},
            "rates": {"symbol": "^TNX", "level": 4.3, "change_pct": -0.3, "change_bps": -1.29},
            "bitcoin": {"symbol": "BTC-USD", "level": 65000.0, "change_pct": 1.5},
        },
    }


def _trade_candidate(symbol: str = "SPY") -> dict:
    return {
        "symbol": symbol,
        "direction": "LONG",
        "entry_mode": "DIRECT",
        "strategy_tag": "BULL_CALL_SPREAD",
        "trigger": None,
        "entry": None,
        "stop": None,
        "target": None,
        "risk_reward": None,
        "timeframe": "7",
        "setup_quality": "VALIDATED",
        "notes": "OI=1200",
    }


def _rejection(symbol: str, stage: str = "QUALIFICATION", reason: str = "CHOP") -> dict:
    return {"symbol": symbol, "stage": stage, "reason": reason, "detail": None}


# ---------------------------------------------------------------------------
# A. Payload construction tests
# ---------------------------------------------------------------------------

class TestBuildReportPayload:
    def test_valid_contract_produces_valid_payload(self):
        contract = _minimal_contract()
        payload = build_report_payload(contract)
        assert_valid_payload(payload)

    def test_schema_version_is_correct(self):
        payload = build_report_payload(_minimal_contract())
        assert payload["schema_version"] == PAYLOAD_SCHEMA_VERSION

    def test_run_status_mapped(self):
        for status in ("OK", "STAY_FLAT", "ERROR"):
            payload = build_report_payload(_minimal_contract(status=status))
            assert payload["run_status"] == status

    def test_summary_fields_present(self):
        payload = build_report_payload(_minimal_contract(
            market_regime="RISK_ON", tradable=True, router_mode="ENERGY"
        ))
        assert payload["summary"]["market_regime"] == "RISK_ON"
        assert payload["summary"]["tradable"] is True
        assert payload["summary"]["router_mode"] == "ENERGY"

    def test_tradable_null_preserved(self):
        payload = build_report_payload(_minimal_contract(tradable=None))
        assert payload["summary"]["tradable"] is None

    def test_router_mode_null_preserved(self):
        payload = build_report_payload(_minimal_contract(router_mode=None))
        assert payload["summary"]["router_mode"] is None

    def test_market_regime_none_becomes_empty_string(self):
        payload = build_report_payload(_minimal_contract(market_regime=None))
        assert payload["summary"]["market_regime"] == ""

    def test_top_trades_populated(self):
        contract = _minimal_contract(trade_candidates=[_trade_candidate("SPY"), _trade_candidate("QQQ")])
        payload = build_report_payload(contract)
        assert len(payload["sections"]["top_trades"]) == 2
        assert payload["sections"]["top_trades"][0]["symbol"] == "SPY"

    def test_watchlist_filtered_from_rejections(self):
        rejections = [
            _rejection("NVDA", stage="WATCHLIST", reason="ONE_SOFT_MISS"),
            _rejection("TSLA", stage="QUALIFICATION"),
        ]
        payload = build_report_payload(_minimal_contract(rejections=rejections))
        assert len(payload["sections"]["watchlist"]) == 1
        assert payload["sections"]["watchlist"][0]["symbol"] == "NVDA"

    def test_rejected_excludes_watchlist(self):
        rejections = [
            _rejection("NVDA", stage="WATCHLIST", reason="ONE_SOFT_MISS"),
            _rejection("TSLA", stage="QUALIFICATION"),
        ]
        payload = build_report_payload(_minimal_contract(rejections=rejections))
        assert len(payload["sections"]["rejected"]) == 1
        assert payload["sections"]["rejected"][0]["symbol"] == "TSLA"

    def test_regime_rejection_in_rejected_not_watchlist(self):
        rejections = [_rejection("REGIME", stage="REGIME", reason="STAY_FLAT posture")]
        payload = build_report_payload(_minimal_contract(rejections=rejections))
        assert len(payload["sections"]["rejected"]) == 1
        assert len(payload["sections"]["watchlist"]) == 0

    def test_continuation_audit_null_when_absent(self):
        payload = build_report_payload(_minimal_contract(continuation_audit_present=False))
        assert payload["sections"]["continuation_audit"] is None

    def test_continuation_audit_populated_when_present(self):
        contract = _minimal_contract(
            continuation_audit_present=True,
            continuation_accepted=1,
            continuation_rejected=3,
        )
        payload = build_report_payload(contract)
        audit = payload["sections"]["continuation_audit"]
        assert audit is not None
        assert audit["accepted_count"] == 1
        assert audit["rejected_count"] == 3

    def test_option_setups_detail_built_from_trade_candidates(self):
        contract = _minimal_contract(trade_candidates=[_trade_candidate("SPY")])
        payload = build_report_payload(contract)
        detail = payload["sections"]["option_setups_detail"]
        assert len(detail) == 1
        assert detail[0]["symbol"] == "SPY"
        assert detail[0]["strategy_tag"] == "BULL_CALL_SPREAD"

    def test_chain_results_detail_built_from_trade_candidates(self):
        contract = _minimal_contract(trade_candidates=[_trade_candidate("SPY")])
        payload = build_report_payload(contract)
        detail = payload["sections"]["chain_results_detail"]
        assert len(detail) == 1
        assert detail[0]["symbol"] == "SPY"
        assert detail[0]["classification"] == "VALIDATED"

    def test_watch_summary_detail_from_intraday_state(self):
        payload = build_report_payload(_minimal_contract(intraday_state="PRE_MARKET"))
        assert payload["sections"]["watch_summary_detail"] == {"session": "PRE_MARKET"}

    def test_watch_summary_detail_null_when_no_intraday_state(self):
        payload = build_report_payload(_minimal_contract(intraday_state=None))
        assert payload["sections"]["watch_summary_detail"] is None

    def test_validation_halt_detail_from_stay_flat_reason(self):
        payload = build_report_payload(_minimal_contract(stay_flat_reason="VIX spike"))
        assert payload["sections"]["validation_halt_detail"] == {"reason": "VIX spike"}

    def test_validation_halt_detail_null_when_no_reason(self):
        payload = build_report_payload(_minimal_contract(stay_flat_reason=None))
        assert payload["sections"]["validation_halt_detail"] is None

    def test_symbols_scanned_from_counts(self):
        # No watchlist entries: qualified + rejected only
        payload = build_report_payload(_minimal_contract(qualified_count=3, rejected_count=5))
        assert payload["meta"]["symbols_scanned"] == 8

    def test_symbols_scanned_includes_watchlist(self):
        # qualified=1, rejected=1, one WATCHLIST rejection -> scanned=3, not 2
        rejections = [
            _rejection("NVDA", stage="WATCHLIST", reason="ONE_SOFT_MISS"),
        ]
        payload = build_report_payload(_minimal_contract(
            qualified_count=1,
            rejected_count=1,
            rejections=rejections,
        ))
        assert payload["meta"]["symbols_scanned"] == 3

    def test_symbols_scanned_watchlist_only(self):
        # All symbols went to watchlist: qualified=0, rejected=0, watchlist=2 -> scanned=2
        rejections = [
            _rejection("NVDA", stage="WATCHLIST", reason="ONE_SOFT_MISS"),
            _rejection("TSLA", stage="WATCHLIST", reason="ONE_SOFT_MISS"),
        ]
        payload = build_report_payload(_minimal_contract(
            qualified_count=0,
            rejected_count=0,
            rejections=rejections,
        ))
        assert payload["meta"]["symbols_scanned"] == 2

    def test_timestamp_from_generated_at(self):
        payload = build_report_payload(_minimal_contract())
        assert payload["meta"]["timestamp"] == "2026-04-23T14:00:00Z"

    def test_list_fields_default_to_empty(self):
        # contract with no trade_candidates or rejections
        payload = build_report_payload(_minimal_contract(trade_candidates=[], rejections=[]))
        assert payload["sections"]["top_trades"] == []
        assert payload["sections"]["watchlist"] == []
        assert payload["sections"]["rejected"] == []
        assert payload["sections"]["option_setups_detail"] == []
        assert payload["sections"]["chain_results_detail"] == []

    def test_deterministic_repeated_build(self):
        contract = _minimal_contract(
            trade_candidates=[_trade_candidate("SPY")],
            rejections=[_rejection("NVDA", stage="WATCHLIST")],
            intraday_state="PRE_MARKET",
        )
        p1 = build_report_payload(contract)
        p2 = build_report_payload(contract)
        assert p1 == p2

    def test_json_safe(self):
        payload = build_report_payload(_minimal_contract(
            trade_candidates=[_trade_candidate("SPY")],
        ))
        json.dumps(payload)  # must not raise


# ---------------------------------------------------------------------------
# B. Validator tests
# ---------------------------------------------------------------------------

class TestAssertValidPayload:
    def _base_payload(self) -> dict:
        return build_report_payload(_minimal_contract())

    def test_valid_payload_passes(self):
        assert_valid_payload(self._base_payload())

    def test_missing_top_level_key_raises(self):
        p = self._base_payload()
        del p["run_status"]
        with pytest.raises(ValueError, match="run_status"):
            assert_valid_payload(p)

    def test_invalid_schema_version_raises(self):
        p = self._base_payload()
        p["schema_version"] = "9.9"
        with pytest.raises(ValueError, match="schema_version"):
            assert_valid_payload(p)

    def test_invalid_run_status_raises(self):
        p = self._base_payload()
        p["run_status"] = "UNKNOWN"
        with pytest.raises(ValueError, match="run_status"):
            assert_valid_payload(p)

    def test_all_valid_run_statuses_pass(self):
        for status in ("OK", "STAY_FLAT", "ERROR"):
            p = self._base_payload()
            p["run_status"] = status
            if status == "ERROR":
                p["macro_drivers"] = {}
            assert_valid_payload(p)  # no exception

    def test_market_regime_must_be_str(self):
        p = self._base_payload()
        p["summary"]["market_regime"] = 42
        with pytest.raises(ValueError, match="market_regime"):
            assert_valid_payload(p)

    def test_tradable_null_is_valid(self):
        p = self._base_payload()
        p["summary"]["tradable"] = None
        assert_valid_payload(p)

    def test_tradable_bool_is_valid(self):
        for val in (True, False):
            p = self._base_payload()
            p["summary"]["tradable"] = val
            assert_valid_payload(p)

    def test_tradable_wrong_type_raises(self):
        p = self._base_payload()
        p["summary"]["tradable"] = "yes"
        with pytest.raises(ValueError, match="tradable"):
            assert_valid_payload(p)

    def test_router_mode_null_is_valid(self):
        p = self._base_payload()
        p["summary"]["router_mode"] = None
        assert_valid_payload(p)

    def test_router_mode_wrong_type_raises(self):
        p = self._base_payload()
        p["summary"]["router_mode"] = 99
        with pytest.raises(ValueError, match="router_mode"):
            assert_valid_payload(p)

    def test_list_field_must_be_list_not_null(self):
        for field in ("top_trades", "watchlist", "rejected", "option_setups_detail", "chain_results_detail"):
            p = self._base_payload()
            p["sections"][field] = None
            with pytest.raises(ValueError, match=field):
                assert_valid_payload(p)

    def test_continuation_audit_null_is_valid(self):
        p = self._base_payload()
        p["sections"]["continuation_audit"] = None
        assert_valid_payload(p)

    def test_continuation_audit_dict_is_valid(self):
        p = self._base_payload()
        p["sections"]["continuation_audit"] = {"accepted_count": 1, "rejected_count": 2}
        assert_valid_payload(p)

    def test_continuation_audit_wrong_type_raises(self):
        p = self._base_payload()
        p["sections"]["continuation_audit"] = [1, 2, 3]
        with pytest.raises(ValueError, match="continuation_audit"):
            assert_valid_payload(p)

    def test_missing_section_key_raises(self):
        p = self._base_payload()
        del p["sections"]["watch_summary_detail"]
        with pytest.raises(ValueError, match="watch_summary_detail"):
            assert_valid_payload(p)

    def test_timestamp_must_be_str(self):
        p = self._base_payload()
        p["meta"]["timestamp"] = 12345
        with pytest.raises(ValueError, match="timestamp"):
            assert_valid_payload(p)

    def test_symbols_scanned_must_be_int(self):
        p = self._base_payload()
        p["meta"]["symbols_scanned"] = "five"
        with pytest.raises(ValueError, match="symbols_scanned"):
            assert_valid_payload(p)

    def test_non_json_safe_raises(self):
        from datetime import datetime, timezone
        p = self._base_payload()
        # inject a datetime inside a dict field that passes structural checks
        p["sections"]["continuation_audit"] = {"accepted_count": datetime.now(timezone.utc)}
        with pytest.raises(ValueError, match="JSON-safe"):
            assert_valid_payload(p)
