"""Tests for the delivery layer: adapter, html renderer, transport (PRD-012)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cuttingboard.delivery.payload import build_report_payload
from cuttingboard.delivery.html_renderer import render_html
from cuttingboard.delivery.transport import (
    deliver,
    deliver_cli,
    deliver_html,
    deliver_json,
)
from cuttingboard.output import render_report_from_payload


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _contract(
    *,
    status: str = "OK",
    tradable: bool | None = True,
    market_regime: str = "RISK_ON",
    stay_flat_reason: str | None = None,
) -> dict:
    return {
        "schema_version": "v1",
        "generated_at": "2026-04-23T14:00:00Z",
        "session_date": "2026-04-23",
        "mode": "live",
        "status": status,
        "timezone": "America/New_York",
        "system_state": {
            "router_mode": "MIXED",
            "market_regime": market_regime,
            "intraday_state": "PRE_MARKET",
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
        "trade_candidates": [],
        "rejections": [],
        "audit_summary": {
            "qualified_count": 2,
            "rejected_count": 1,
            "continuation_audit_present": False,
            "continuation_accepted_count": None,
            "continuation_rejected_count": None,
            "error_count": 0,
        },
        "artifacts": {
            "report_path": "reports/2026-04-23.md",
            "log_path": "logs/latest_run.json",
            "notification_sent": False,
        },
    }


def _error_contract() -> dict:
    return {
        "schema_version": "v1",
        "generated_at": "2026-04-23T14:00:00Z",
        "session_date": None,
        "mode": None,
        "status": "ERROR",
        "timezone": "America/New_York",
        "system_state": {
            "router_mode": None,
            "market_regime": None,
            "intraday_state": None,
            "time_gate_open": None,
            "tradable": False,
            "stay_flat_reason": "Pipeline exception: connection refused",
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
            "error_count": 1,
        },
        "artifacts": {
            "report_path": None,
            "log_path": None,
            "notification_sent": None,
        },
    }


def _payload(contract: dict | None = None) -> dict:
    return build_report_payload(contract or _contract())


# ---------------------------------------------------------------------------
# A. render_report_from_payload adapter
# ---------------------------------------------------------------------------

class TestRenderReportFromPayload:
    def test_returns_string(self):
        result = render_report_from_payload(_payload())
        assert isinstance(result, str)
        assert len(result) > 0

    def test_ok_status_renders_without_halt(self):
        result = render_report_from_payload(_payload(_contract(status="OK")))
        assert "SYSTEM HALT" not in result

    def test_stay_flat_renders_no_trade(self):
        result = render_report_from_payload(
            _payload(_contract(status="STAY_FLAT", stay_flat_reason="STAY_FLAT posture"))
        )
        assert "NO TRADE" in result or "STAY_FLAT" in result

    def test_error_status_renders_halt(self):
        result = render_report_from_payload(_payload(_error_contract()))
        assert "HALT" in result

    def test_deterministic_for_same_payload(self):
        p = _payload()
        r1 = render_report_from_payload(p)
        r2 = render_report_from_payload(p)
        assert r1 == r2

    def test_invalid_payload_raises(self):
        bad = _payload()
        bad["run_status"] = "BOGUS"
        with pytest.raises(ValueError):
            render_report_from_payload(bad)

    def test_does_not_import_pipeline_result(self):
        import cuttingboard.output as mod
        import inspect
        source = inspect.getsource(mod.render_report_from_payload)
        assert "PipelineResult" not in source

    def test_does_not_import_regime_state_directly(self):
        import cuttingboard.output as mod
        import inspect
        source = inspect.getsource(mod.render_report_from_payload)
        assert "RegimeState" not in source

    # --- adapter degradation documentation (audit fix A) ---

    def test_adapter_does_not_render_summary_block(self):
        # The SUMMARY block in render_report is gated on regime != None.
        # The adapter passes regime=None, so "Market state:" never appears.
        result = render_report_from_payload(_payload(_contract(market_regime="RISK_ON")))
        assert "Market state:" not in result

    def test_adapter_does_not_render_vix_header(self):
        # VIX header is also gated on regime != None.
        result = render_report_from_payload(_payload(_contract()))
        assert "VIX:" not in result

    def test_adapter_renders_date(self):
        # Date border is always rendered regardless of regime.
        result = render_report_from_payload(_payload(_contract()))
        assert "2026-04-23" in result

    # --- timestamp determinism / failure (audit fix C) ---

    def test_empty_timestamp_raises_value_error(self):
        p = _payload()
        p["meta"]["timestamp"] = ""
        with pytest.raises(ValueError, match="unparseable timestamp"):
            render_report_from_payload(p)

    def test_malformed_timestamp_raises_value_error(self):
        p = _payload()
        p["meta"]["timestamp"] = "not-a-date"
        with pytest.raises(ValueError, match="unparseable timestamp"):
            render_report_from_payload(p)

    def test_valid_timestamp_is_deterministic(self):
        # Same payload called twice must produce identical output (no datetime.now fallback).
        p = _payload()
        assert render_report_from_payload(p) == render_report_from_payload(p)


# ---------------------------------------------------------------------------
# B. html_renderer
# ---------------------------------------------------------------------------

class TestRenderHtml:
    def test_returns_string(self):
        result = render_html(_payload())
        assert isinstance(result, str)

    def test_contains_doctype(self):
        assert "<!DOCTYPE html>" in render_html(_payload())

    def test_contains_generated_at(self):
        result = render_html(_payload())
        assert "2026-04-23T14:00:00Z" in result

    def test_deterministic(self):
        p = _payload()
        assert render_html(p) == render_html(p)

    def test_same_payload_same_html(self):
        contract = _contract(market_regime="RISK_OFF")
        p = build_report_payload(contract)
        h1 = render_html(p)
        h2 = render_html(p)
        assert h1 == h2

    def test_error_contract_renders_valid_html(self):
        p = _payload(_error_contract())
        result = render_html(p)
        assert "<html" in result
        assert "HALT" in result

    def test_invalid_payload_raises(self):
        bad = _payload()
        bad["run_status"] = "BAD"
        with pytest.raises(ValueError):
            render_html(bad)


# ---------------------------------------------------------------------------
# C. Transport: file writers
# ---------------------------------------------------------------------------

class TestDeliverJson:
    def test_writes_file(self, tmp_path):
        p = _payload()
        out = str(tmp_path / "payload.json")
        deliver_json(p, output_path=out)
        assert Path(out).exists()

    def test_content_is_valid_json(self, tmp_path):
        p = _payload()
        out = str(tmp_path / "payload.json")
        deliver_json(p, output_path=out)
        loaded = json.loads(Path(out).read_text(encoding="utf-8"))
        assert loaded["run_status"] == "OK"

    def test_creates_parent_dirs(self, tmp_path):
        p = _payload()
        out = str(tmp_path / "nested" / "deep" / "payload.json")
        deliver_json(p, output_path=out)
        assert Path(out).exists()

    def test_invalid_payload_raises(self, tmp_path):
        bad = _payload()
        bad["run_status"] = "NOPE"
        with pytest.raises(ValueError):
            deliver_json(bad, output_path=str(tmp_path / "out.json"))


class TestDeliverHtml:
    def test_writes_file(self, tmp_path):
        p = _payload()
        out = str(tmp_path / "report.html")
        deliver_html(p, output_path=out)
        assert Path(out).exists()

    def test_content_contains_html(self, tmp_path):
        p = _payload()
        out = str(tmp_path / "report.html")
        deliver_html(p, output_path=out)
        content = Path(out).read_text(encoding="utf-8")
        assert "<html" in content

    def test_creates_parent_dirs(self, tmp_path):
        p = _payload()
        out = str(tmp_path / "sub" / "report.html")
        deliver_html(p, output_path=out)
        assert Path(out).exists()

    def test_invalid_payload_raises(self, tmp_path):
        bad = _payload()
        bad["run_status"] = "NOPE"
        with pytest.raises(ValueError):
            deliver_html(bad, output_path=str(tmp_path / "r.html"))


class TestDeliverCli:
    def test_prints_status(self, capsys):
        deliver_cli(_payload(_contract(status="OK")))
        captured = capsys.readouterr()
        assert "STATUS:" in captured.out
        assert "OK" in captured.out

    def test_prints_market_regime(self, capsys):
        deliver_cli(_payload(_contract(market_regime="RISK_ON")))
        captured = capsys.readouterr()
        assert "RISK_ON" in captured.out

    def test_prints_symbols_scanned(self, capsys):
        deliver_cli(_payload())
        captured = capsys.readouterr()
        assert "SYMBOLS_SCANNED" in captured.out

    def test_prints_counts(self, capsys):
        deliver_cli(_payload())
        captured = capsys.readouterr()
        assert "TOP_TRADES" in captured.out
        assert "WATCHLIST" in captured.out
        assert "REJECTED" in captured.out

    def test_deterministic_output(self, capsys):
        p = _payload()
        deliver_cli(p)
        out1 = capsys.readouterr().out
        deliver_cli(p)
        out2 = capsys.readouterr().out
        assert out1 == out2

    def test_invalid_payload_raises(self):
        bad = _payload()
        bad["run_status"] = "NOPE"
        with pytest.raises(ValueError):
            deliver_cli(bad)


class TestDeliver:
    def test_html_mode(self, tmp_path):
        p = _payload()
        # Patch default path to tmp_path
        from cuttingboard.delivery import transport as t
        original = t._DEFAULT_HTML_PATH
        t._DEFAULT_HTML_PATH = str(tmp_path / "report.html")
        try:
            deliver(p, mode="html")
            assert (tmp_path / "report.html").exists()
        finally:
            t._DEFAULT_HTML_PATH = original

    def test_json_mode(self, tmp_path):
        p = _payload()
        from cuttingboard.delivery import transport as t
        original = t._DEFAULT_JSON_PATH
        t._DEFAULT_JSON_PATH = str(tmp_path / "payload.json")
        try:
            deliver(p, mode="json")
            assert (tmp_path / "payload.json").exists()
        finally:
            t._DEFAULT_JSON_PATH = original

    def test_cli_mode(self, capsys):
        deliver(_payload(), mode="cli")
        assert "STATUS:" in capsys.readouterr().out

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown delivery mode"):
            deliver(_payload(), mode="ftp")


# ---------------------------------------------------------------------------
# D. Error contract path
# ---------------------------------------------------------------------------

class TestErrorContractPath:
    def test_error_contract_builds_valid_payload(self):
        payload = build_report_payload(_error_contract())
        from cuttingboard.delivery.payload import assert_valid_payload
        assert_valid_payload(payload)

    def test_error_payload_run_status_is_error(self):
        payload = build_report_payload(_error_contract())
        assert payload["run_status"] == "ERROR"

    def test_error_payload_renders_html(self):
        payload = build_report_payload(_error_contract())
        html = render_html(payload)
        assert "<html" in html

    def test_error_payload_serializes_to_json(self, tmp_path):
        payload = build_report_payload(_error_contract())
        out = str(tmp_path / "error_payload.json")
        deliver_json(payload, output_path=out)
        loaded = json.loads(Path(out).read_text())
        assert loaded["run_status"] == "ERROR"

    def test_error_payload_adapter_renders(self):
        payload = build_report_payload(_error_contract())
        result = render_report_from_payload(payload)
        assert isinstance(result, str)
        assert "HALT" in result


# ---------------------------------------------------------------------------
# E. Compatibility: existing render_report interface untouched
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# F. Roundtrip safety (audit fix D)
# ---------------------------------------------------------------------------

class TestJsonRoundtrip:
    def test_deliver_json_roundtrip(self, tmp_path):
        from cuttingboard.delivery.payload import assert_valid_payload
        p = _payload()
        out = str(tmp_path / "payload.json")
        deliver_json(p, output_path=out)
        import json as _json
        loaded = _json.loads(Path(out).read_text(encoding="utf-8"))
        assert_valid_payload(loaded)

    def test_roundtrip_preserves_run_status(self, tmp_path):
        import json as _json
        for status in ("OK", "STAY_FLAT", "ERROR"):
            if status == "ERROR":
                p = _payload(_error_contract())
            else:
                c = _contract(status=status)
                p = _payload(c)
            out = str(tmp_path / f"p_{status}.json")
            deliver_json(p, output_path=out)
            loaded = _json.loads(Path(out).read_text(encoding="utf-8"))
            assert loaded["run_status"] == status

    def test_roundtrip_preserves_tradable_null(self, tmp_path):
        import json as _json
        p = _payload(_contract(tradable=None))
        out = str(tmp_path / "payload_null.json")
        deliver_json(p, output_path=out)
        loaded = _json.loads(Path(out).read_text(encoding="utf-8"))
        assert loaded["summary"]["tradable"] is None


# ---------------------------------------------------------------------------
# E. Compatibility: existing render_report interface untouched
# ---------------------------------------------------------------------------

class TestExistingRenderReportUnchanged:
    def test_existing_signature_still_works(self):
        from datetime import datetime, timezone
        from cuttingboard.output import OUTCOME_NO_TRADE, render_report
        from cuttingboard.regime import RegimeState, RISK_ON, CONTROLLED_LONG
        from cuttingboard.validation import ValidationSummary

        regime = RegimeState(
            regime=RISK_ON,
            posture=CONTROLLED_LONG,
            confidence=0.75,
            net_score=3,
            risk_on_votes=5,
            risk_off_votes=2,
            neutral_votes=1,
            total_votes=8,
            vote_breakdown={},
            vix_level=18.0,
            vix_pct_change=-0.02,
            computed_at_utc=datetime(2026, 4, 23, 14, 0, tzinfo=timezone.utc),
        )
        val = ValidationSummary(
            system_halted=False,
            halt_reason=None,
            failed_halt_symbols=[],
            results={},
            valid_quotes={},
            invalid_symbols={},
            symbols_attempted=5,
            symbols_validated=5,
            symbols_failed=0,
        )
        report = render_report(
            date_str="2026-04-23",
            run_at_utc=datetime(2026, 4, 23, 14, 0, tzinfo=timezone.utc),
            regime=regime,
            validation_summary=val,
            qualification_summary=None,
            option_setups=[],
            outcome=OUTCOME_NO_TRADE,
        )
        assert isinstance(report, str)
        assert "2026-04-23" in report
