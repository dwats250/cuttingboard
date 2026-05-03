"""Tests for PRD-072: macro_drivers snapshot write and fallback."""
from __future__ import annotations

import json
from pathlib import Path


from cuttingboard.delivery.dashboard_renderer import _load_macro_snapshot


# ---------------------------------------------------------------------------
# _load_macro_snapshot
# ---------------------------------------------------------------------------

def test_load_returns_empty_when_file_absent(tmp_path):
    result = _load_macro_snapshot(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_returns_empty_on_malformed_json(tmp_path):
    p = tmp_path / "snap.json"
    p.write_text("not json", encoding="utf-8")
    assert _load_macro_snapshot(p) == {}


def test_load_returns_empty_when_macro_drivers_key_missing(tmp_path):
    p = tmp_path / "snap.json"
    p.write_text(json.dumps({"generated_at": "2026-05-01T12:00:00Z"}), encoding="utf-8")
    assert _load_macro_snapshot(p) == {}


def test_load_returns_empty_when_macro_drivers_not_dict(tmp_path):
    p = tmp_path / "snap.json"
    p.write_text(json.dumps({"macro_drivers": "bad"}), encoding="utf-8")
    assert _load_macro_snapshot(p) == {}


def test_load_returns_macro_drivers_on_valid_file(tmp_path):
    drivers = {"vol": {"symbol": "^VIX", "level": 17.0, "change_pct": 2.1}}
    p = tmp_path / "snap.json"
    p.write_text(json.dumps({"macro_drivers": drivers, "generated_at": "2026-05-01T12:00:00Z"}), encoding="utf-8")
    assert _load_macro_snapshot(p) == drivers


def test_load_does_not_raise(tmp_path):
    # Absence and malformed both return {} — never raise
    assert _load_macro_snapshot(tmp_path / "missing.json") == {}


# ---------------------------------------------------------------------------
# _write_macro_snapshot (via runtime helper — tested via its observable output)
# ---------------------------------------------------------------------------

def test_write_macro_snapshot_writes_file(tmp_path, monkeypatch):
    from cuttingboard import runtime as rt
    monkeypatch.setattr(rt, "LOGS_DIR", tmp_path)

    contract = {
        "macro_drivers": {"volatility": {"symbol": "^VIX", "level": 17.5, "change_pct": 1.2}},
        "generated_at": "2026-05-01T13:00:00Z",
    }
    rt._write_macro_snapshot(contract)

    snap_path = tmp_path / "macro_drivers_snapshot.json"
    assert snap_path.exists()
    data = json.loads(snap_path.read_text(encoding="utf-8"))
    assert data["macro_drivers"] == contract["macro_drivers"]
    assert data["generated_at"] == "2026-05-01T13:00:00Z"


def test_write_macro_snapshot_skips_when_empty(tmp_path, monkeypatch):
    from cuttingboard import runtime as rt
    monkeypatch.setattr(rt, "LOGS_DIR", tmp_path)

    rt._write_macro_snapshot({"macro_drivers": {}, "generated_at": "2026-05-01T13:00:00Z"})

    assert not (tmp_path / "macro_drivers_snapshot.json").exists()


def test_write_macro_snapshot_skips_when_key_absent(tmp_path, monkeypatch):
    from cuttingboard import runtime as rt
    monkeypatch.setattr(rt, "LOGS_DIR", tmp_path)

    rt._write_macro_snapshot({"generated_at": "2026-05-01T13:00:00Z"})

    assert not (tmp_path / "macro_drivers_snapshot.json").exists()


def test_write_macro_snapshot_does_not_raise_on_write_failure(tmp_path, monkeypatch):
    from cuttingboard import runtime as rt
    # Point LOGS_DIR at a path that can't be written to
    monkeypatch.setattr(rt, "LOGS_DIR", Path("/nonexistent/path"))

    # Must not raise
    rt._write_macro_snapshot({"macro_drivers": {"vol": {}}, "generated_at": ""})


# ---------------------------------------------------------------------------
# Renderer fallback wiring — use same fixture shape as test_dashboard_renderer
# ---------------------------------------------------------------------------

def _payload(macro_drivers=None):
    return {
        "schema_version": "1.0",
        "run_status": "OK",
        "meta": {"timestamp": "2026-05-01T12:00:00Z", "symbols_scanned": 5},
        "macro_drivers": macro_drivers if macro_drivers is not None else {},
        "summary": {"market_regime": "RISK_ON", "tradable": True, "router_mode": "MIXED"},
        "sections": {
            "top_trades": [], "watchlist": [], "rejected": [],
            "option_setups_detail": [], "chain_results_detail": [],
            "continuation_audit": None, "watch_summary_detail": None,
            "validation_halt_detail": None, "trade_decision_detail": [],
        },
    }


def _run():
    return {
        "run_id": "live-20260501T120000Z", "status": "SUCCESS",
        "regime": "RISK_ON", "posture": "STAY_FLAT", "confidence": 0.25,
        "system_halted": False, "kill_switch": False, "errors": [],
        "data_status": "ok", "outcome": "NO_TRADE", "permission": None,
        "mode": "LIVE", "timestamp": "2026-05-01T12:00:00Z", "warnings": [],
    }


def test_renderer_uses_snapshot_when_payload_macro_drivers_empty(tmp_path):
    from cuttingboard.delivery.dashboard_renderer import render_dashboard_html

    drivers = {
        "volatility": {"symbol": "^VIX",     "level": 18.0, "change_pct":  3.0},
        "dollar":     {"symbol": "DX-Y.NYB", "level": 99.0, "change_pct":  0.1},
        "rates":      {"symbol": "^TNX",     "level":  4.5, "change_pct": -0.2, "change_bps": -0.9},
        "bitcoin":    {"symbol": "BTC-USD",  "level": 80000.0, "change_pct": 1.5},
    }
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps({"macro_drivers": drivers, "generated_at": "2026-05-01T12:00:00Z"}), encoding="utf-8")

    html = render_dashboard_html(_payload(macro_drivers={}), _run(), macro_snapshot_path=snap)
    assert "18.0" in html  # VIX level from snapshot


def test_renderer_does_not_use_snapshot_when_payload_has_data(tmp_path):
    from cuttingboard.delivery.dashboard_renderer import render_dashboard_html

    snapshot_drivers = {
        "volatility": {"symbol": "^VIX",     "level": 99.9, "change_pct":  0.0},
        "dollar":     {"symbol": "DX-Y.NYB", "level": 99.0, "change_pct":  0.0},
        "rates":      {"symbol": "^TNX",     "level":  4.5, "change_pct":  0.0, "change_bps": 0.0},
        "bitcoin":    {"symbol": "BTC-USD",  "level": 80000.0, "change_pct": 0.0},
    }
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps({"macro_drivers": snapshot_drivers}), encoding="utf-8")

    live_drivers = {
        "volatility": {"symbol": "^VIX",     "level": 17.5, "change_pct":  1.0},
        "dollar":     {"symbol": "DX-Y.NYB", "level": 98.0, "change_pct": -0.1},
        "rates":      {"symbol": "^TNX",     "level":  4.3, "change_pct": -0.5, "change_bps": -2.0},
        "bitcoin":    {"symbol": "BTC-USD",  "level": 78000.0, "change_pct": 0.5},
    }
    html = render_dashboard_html(_payload(macro_drivers=live_drivers), _run(), macro_snapshot_path=snap)
    assert "17.5" in html
    assert "99.9" not in html


def test_renderer_does_not_raise_when_snapshot_absent(tmp_path):
    from cuttingboard.delivery.dashboard_renderer import render_dashboard_html

    html = render_dashboard_html(
        _payload(macro_drivers={}), _run(),
        macro_snapshot_path=tmp_path / "missing.json",
    )
    assert html  # renders without error
