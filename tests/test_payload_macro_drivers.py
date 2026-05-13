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


# ---------------------------------------------------------------------------
# PRD-122-PATCH: private-validator regression coverage.
# These exercise cuttingboard.delivery.payload._require_macro_drivers directly,
# isolating the payload-layer validator from the public assert_valid_payload
# entry exercised above. Catches duplicate-validator drift between this module
# and cuttingboard.contract._OPTIONAL_MACRO_DRIVERS.
# ---------------------------------------------------------------------------

from cuttingboard.delivery.payload import _require_macro_drivers  # noqa: E402


def _oil_block() -> dict:
    return {"symbol": "CL=F", "level": 78.5, "change_pct": -0.8}


def test_require_macro_drivers_required_four_pass() -> None:
    _require_macro_drivers(_macro_drivers())  # must not raise


def test_require_macro_drivers_required_four_plus_oil_pass() -> None:
    drivers = _macro_drivers()
    drivers["oil"] = _oil_block()
    _require_macro_drivers(drivers)  # must not raise


def test_require_macro_drivers_missing_required_raises() -> None:
    drivers = _macro_drivers()
    del drivers["bitcoin"]
    with pytest.raises(ValueError, match="missing required driver keys"):
        _require_macro_drivers(drivers)


def test_require_macro_drivers_unknown_extra_driver_raises() -> None:
    drivers = _macro_drivers()
    drivers["platinum"] = {"symbol": "PL=F", "level": 950.0, "change_pct": 0.5}
    with pytest.raises(ValueError, match="unexpected driver keys"):
        _require_macro_drivers(drivers)


def test_require_macro_drivers_invalid_oil_field_shape_raises() -> None:
    drivers = _macro_drivers()
    # Missing `change_pct` — oil block has incomplete field set.
    drivers["oil"] = {"symbol": "CL=F", "level": 78.5}
    with pytest.raises(ValueError, match="macro_drivers.oil has unexpected keys"):
        _require_macro_drivers(drivers)


def _gold_block() -> dict:
    return {"symbol": "GC=F", "level": 3200.0, "change_pct": 0.4}


def _silver_block() -> dict:
    return {"symbol": "SI=F", "level": 39.5, "change_pct": -0.7}


def test_require_macro_drivers_required_four_plus_gold_pass() -> None:
    drivers = _macro_drivers()
    drivers["gold"] = _gold_block()
    _require_macro_drivers(drivers)  # must not raise


def test_require_macro_drivers_required_four_plus_silver_pass() -> None:
    drivers = _macro_drivers()
    drivers["silver"] = _silver_block()
    _require_macro_drivers(drivers)  # must not raise


def test_require_macro_drivers_required_four_plus_gold_and_silver_pass() -> None:
    drivers = _macro_drivers()
    drivers["gold"] = _gold_block()
    drivers["silver"] = _silver_block()
    _require_macro_drivers(drivers)  # must not raise


def test_require_macro_drivers_required_four_plus_oil_gold_silver_pass() -> None:
    drivers = _macro_drivers()
    drivers["oil"] = _oil_block()
    drivers["gold"] = _gold_block()
    drivers["silver"] = _silver_block()
    _require_macro_drivers(drivers)  # must not raise


def test_require_macro_drivers_invalid_gold_field_shape_raises() -> None:
    drivers = _macro_drivers()
    drivers["gold"] = {"symbol": "GC=F", "level": 3200.0}
    with pytest.raises(ValueError, match="macro_drivers.gold has unexpected keys"):
        _require_macro_drivers(drivers)


def test_require_macro_drivers_invalid_silver_field_shape_raises() -> None:
    drivers = _macro_drivers()
    drivers["silver"] = {"symbol": "SI=F", "level": 39.5}
    with pytest.raises(ValueError, match="macro_drivers.silver has unexpected keys"):
        _require_macro_drivers(drivers)
