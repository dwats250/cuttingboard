"""
PRD-015.1 — Runtime wiring tests for flow snapshot ingestion.

Verifies _load_flow() behavior:
  - returns None when config has no path
  - loads and returns snapshot.symbols when path is set
  - propagates loader exception (no masking)

These tests target cuttingboard.runtime._load_flow directly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import cuttingboard.config as config_mod
from cuttingboard.flow import FlowPrint
from cuttingboard.runtime import _load_flow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_flow_json(symbol: str = "SPY", underlying: float = 450.0) -> dict:
    return {
        "timestamp": "2026-04-23T13:00:00Z",
        "symbols": {
            symbol: [
                {
                    "symbol": symbol,
                    "strike": 460.0,
                    "option_type": "CALL",
                    "premium": 600_000.0,
                    "side": "ASK",
                    "is_sweep": True,
                    "underlying_price": underlying,
                }
            ]
        },
    }


def _write_flow_file(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "flow.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _write_config_toml(tmp_path: Path, data_path: str) -> Path:
    toml = tmp_path / "config.toml"
    toml.write_text(f'[flow]\ndata_path = "{data_path}"\n', encoding="utf-8")
    return toml


# ---------------------------------------------------------------------------
# test_runtime_passes_none_when_config_null
# ---------------------------------------------------------------------------

def test_runtime_passes_none_when_config_null(monkeypatch):
    """When get_flow_data_path() returns None, _load_flow() returns None."""
    monkeypatch.setattr(config_mod, "get_flow_data_path", lambda **_: None)
    result = _load_flow()
    assert result is None


# ---------------------------------------------------------------------------
# test_runtime_passes_snapshot_when_config_set
# ---------------------------------------------------------------------------

def test_runtime_passes_snapshot_when_config_set(tmp_path, monkeypatch):
    """When get_flow_data_path() returns a valid path, _load_flow() returns symbols dict."""
    flow_file = _write_flow_file(tmp_path, _valid_flow_json())
    monkeypatch.setattr(config_mod, "get_flow_data_path", lambda **_: str(flow_file))

    result = _load_flow()

    assert isinstance(result, dict)
    assert "SPY" in result
    assert isinstance(result["SPY"], list)
    assert isinstance(result["SPY"][0], FlowPrint)


# ---------------------------------------------------------------------------
# test_runtime_propagates_loader_exception
# ---------------------------------------------------------------------------

def test_runtime_propagates_loader_exception(tmp_path, monkeypatch):
    """When get_flow_data_path() returns a nonexistent path, _load_flow() raises."""
    missing = str(tmp_path / "nonexistent.json")
    monkeypatch.setattr(config_mod, "get_flow_data_path", lambda **_: missing)

    with pytest.raises(FileNotFoundError):
        _load_flow()


def test_runtime_propagates_invalid_schema_exception(tmp_path, monkeypatch):
    """When flow file has invalid schema, _load_flow() raises ValueError."""
    bad_data = {"timestamp": "2026-04-23T13:00:00Z", "symbols": {}}  # empty symbols
    flow_file = _write_flow_file(tmp_path, bad_data)
    monkeypatch.setattr(config_mod, "get_flow_data_path", lambda **_: str(flow_file))

    with pytest.raises(ValueError, match="empty"):
        _load_flow()


# ---------------------------------------------------------------------------
# AC7 — qualify_all wiring (integration smoke)
# ---------------------------------------------------------------------------

def test_qualify_all_receives_none_when_no_path(monkeypatch):
    """qualify_all called with flow_snapshot=None when config has no path."""
    from cuttingboard.qualification import qualify_all
    from cuttingboard.regime import RegimeState, RISK_ON, AGGRESSIVE_LONG
    from cuttingboard.structure import StructureResult, TREND
    from datetime import datetime, timezone

    monkeypatch.setattr(config_mod, "get_flow_data_path", lambda **_: None)

    regime = RegimeState(
        regime=RISK_ON, posture=AGGRESSIVE_LONG, confidence=0.80,
        net_score=5, risk_on_votes=6, risk_off_votes=1, neutral_votes=1,
        total_votes=8, vote_breakdown={}, vix_level=16.0, vix_pct_change=-0.02,
        computed_at_utc=datetime(2026, 4, 23, 13, 0, 0, tzinfo=timezone.utc),
    )
    structure = {
        "SPY": StructureResult(
            symbol="SPY", structure=TREND, iv_environment="NORMAL",
            is_tradeable=True, disqualification_reason=None,
        )
    }

    flow_snapshot = _load_flow()
    assert flow_snapshot is None

    summary = qualify_all(regime, structure, flow_snapshot=flow_snapshot)
    for reason in summary.excluded.values():
        assert "FLOW" not in reason
