from __future__ import annotations

import copy

import pytest

from cuttingboard.delivery.payload import assert_valid_payload, build_report_payload


def _macro_drivers() -> dict:
    return {
        "volatility": {
            "symbol": "^VIX",
            "level": 18.5,
            "change_pct": -2.0,
        },
        "dollar": {
            "symbol": "DX-Y.NYB",
            "level": 104.0,
            "change_pct": 0.1,
        },
        "rates": {
            "symbol": "^TNX",
            "level": 4.3,
            "change_pct": -0.3,
            "change_bps": -1.29,
        },
        "bitcoin": {
            "symbol": "BTC-USD",
            "level": 65000.0,
            "change_pct": 1.5,
        },
    }


def _contract() -> dict:
    return {
        "schema_version": "v2",
        "generated_at": "2026-04-28T14:00:00Z",
        "session_date": "2026-04-28",
        "mode": "live",
        "status": "OK",
        "timezone": "America/New_York",
        "system_state": {
            "router_mode": "MIXED",
            "market_regime": "RISK_ON",
            "intraday_state": None,
            "time_gate_open": True,
            "tradable": True,
            "stay_flat_reason": None,
        },
        "market_context": {
            "expansion_regime": None,
            "continuation_enabled": None,
            "imbalance_enabled": None,
            "stale_data_detected": False,
            "data_quality": "ok",
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
            "report_path": "reports/2026-04-28.md",
            "log_path": "logs/latest_run.json",
            "notification_sent": False,
        },
        "correlation": None,
        "regime": None,
        "macro_drivers": _macro_drivers(),
    }


def test_payload_macro_drivers_pass_through_exactly() -> None:
    contract = _contract()
    payload = build_report_payload(contract)
    assert payload["macro_drivers"] == contract["macro_drivers"]
    assert_valid_payload(payload)


def test_payload_macro_drivers_no_mutation() -> None:
    contract = _contract()
    original = copy.deepcopy(contract["macro_drivers"])
    payload = build_report_payload(contract)
    assert contract["macro_drivers"] == original
    assert payload["macro_drivers"] == original


def test_payload_validator_rejects_missing_macro_driver_key() -> None:
    payload = build_report_payload(_contract())
    del payload["macro_drivers"]["bitcoin"]
    with pytest.raises(ValueError, match="macro_drivers"):
        assert_valid_payload(payload)


def test_payload_validator_rejects_extra_macro_driver_key() -> None:
    payload = build_report_payload(_contract())
    payload["macro_drivers"]["extra_driver"] = {"symbol": "XYZ", "level": 70.0, "change_pct": 1.0}
    with pytest.raises(ValueError, match="macro_drivers"):
        assert_valid_payload(payload)


def test_payload_validator_rejects_non_finite_macro_value() -> None:
    payload = build_report_payload(_contract())
    payload["macro_drivers"]["rates"]["change_bps"] = float("inf")
    with pytest.raises(ValueError, match="finite float"):
        assert_valid_payload(payload)


def test_error_payload_allows_empty_macro_drivers() -> None:
    contract = _contract()
    contract["status"] = "ERROR"
    contract["macro_drivers"] = {}
    payload = build_report_payload(contract)
    assert payload["macro_drivers"] == {}
    assert_valid_payload(payload)


def test_no_data_payload_passes_through_empty_macro_drivers() -> None:
    contract = _contract()
    contract["macro_drivers"] = {}
    payload = build_report_payload(contract)
    assert payload["macro_drivers"] == {}
    assert_valid_payload(payload)
