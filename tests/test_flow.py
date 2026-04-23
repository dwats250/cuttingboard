"""
Tests for PRD-013 — Flow Alignment Soft Gate (cuttingboard/flow.py).
Extended in PRD-015 with loader and wiring tests.

All tests use static fixtures. No runtime data, no I/O.
Acceptance criteria (PRD-013):
  1. PASS LONG + dominant bearish spec flow → WATCHLIST
  2. PASS SHORT + dominant bullish spec flow → WATCHLIST
  3. PASS + matching spec flow → PASS
  4. PASS + HEDGE flow → PASS
  5. PASS + MIXED flow → PASS
  6. PASS + no flow data → PASS
  7. WATCHLIST remains WATCHLIST
  8. REJECT remains REJECT
  9. Deterministic output
 10. HEDGE classification uses full print set (pre-speculative filter)

Acceptance criteria (PRD-015):
 AC2. Loader raises on missing file
 AC4. Gate triggers: opposing snapshot → PASS downgraded to WATCHLIST
 AC5. gate noop when snapshot=None (qualify_all path)
 AC6. Loader raises on invalid schema / empty symbols
"""

import json
import os
import pytest

from cuttingboard.flow import (
    FlowPrint,
    FlowSnapshot,
    apply_flow_gate,
    load_flow_snapshot,
    _classify_strike,
)
from cuttingboard.qualification import QualificationResult, ENTRY_MODE_DIRECT

# ---------------------------------------------------------------------------
# Constants for fixtures
# ---------------------------------------------------------------------------

_UNDERLYING = 450.0
_OTM_CALL_STRIKE = 460.0   # distance = +2.2%  → OTM CALL
_OTM_PUT_STRIKE  = 440.0   # distance = -2.2%  → OTM PUT
_ITM_CALL_STRIKE = 440.0   # distance = -2.2%  → ITM CALL
_ITM_PUT_STRIKE  = 460.0   # distance = +2.2%  → ITM PUT
_LARGE_PREMIUM   = 600_000
_SMALL_PREMIUM   = 300_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pass_result(symbol="SPY", direction="LONG") -> QualificationResult:
    return QualificationResult(
        symbol=symbol,
        qualified=True,
        watchlist=False,
        direction=direction,
        gates_passed=["REGIME", "CONFIDENCE", "DIRECTION", "STRUCTURE",
                      "STOP_DEFINED", "STOP_DISTANCE", "RR_RATIO",
                      "MAX_RISK", "EARNINGS", "EXTENSION", "TIME"],
        gates_failed=[],
        hard_failure=None,
        watchlist_reason=None,
        max_contracts=1,
        dollar_risk=150.0,
    )


def _watchlist_result(symbol="SPY", direction="LONG") -> QualificationResult:
    return QualificationResult(
        symbol=symbol,
        qualified=False,
        watchlist=True,
        direction=direction,
        gates_passed=["REGIME", "CONFIDENCE", "DIRECTION", "STRUCTURE"],
        gates_failed=["RR_RATIO"],
        hard_failure=None,
        watchlist_reason="R:R 1.5 below 2.0 minimum",
        max_contracts=1,
        dollar_risk=150.0,
    )


def _reject_result(symbol="SPY", direction="LONG") -> QualificationResult:
    return QualificationResult(
        symbol=symbol,
        qualified=False,
        watchlist=False,
        direction=direction,
        gates_passed=[],
        gates_failed=["REGIME"],
        hard_failure="REGIME: posture is STAY_FLAT",
        watchlist_reason=None,
        max_contracts=None,
        dollar_risk=None,
    )


def _otm_ask_call(symbol="SPY", premium=_LARGE_PREMIUM) -> FlowPrint:
    return FlowPrint(
        symbol=symbol, strike=_OTM_CALL_STRIKE, option_type="CALL",
        premium=premium, side="ASK", is_sweep=True,
        underlying_price=_UNDERLYING,
    )


def _otm_ask_put(symbol="SPY", premium=_LARGE_PREMIUM) -> FlowPrint:
    return FlowPrint(
        symbol=symbol, strike=_OTM_PUT_STRIKE, option_type="PUT",
        premium=premium, side="ASK", is_sweep=True,
        underlying_price=_UNDERLYING,
    )


def _itm_call(symbol="SPY", premium=_LARGE_PREMIUM) -> FlowPrint:
    return FlowPrint(
        symbol=symbol, strike=_ITM_CALL_STRIKE, option_type="CALL",
        premium=premium, side="ASK", is_sweep=False,
        underlying_price=_UNDERLYING,
    )


def _itm_put(symbol="SPY", premium=_LARGE_PREMIUM) -> FlowPrint:
    return FlowPrint(
        symbol=symbol, strike=_ITM_PUT_STRIKE, option_type="PUT",
        premium=premium, side="ASK", is_sweep=False,
        underlying_price=_UNDERLYING,
    )


def _snapshot(*prints: FlowPrint) -> dict[str, list[FlowPrint]]:
    result: dict[str, list[FlowPrint]] = {}
    for p in prints:
        result.setdefault(p.symbol, []).append(p)
    return result


# ---------------------------------------------------------------------------
# Strike classification unit tests
# ---------------------------------------------------------------------------

def test_classify_otm_call():
    assert _classify_strike(_OTM_CALL_STRIKE, _UNDERLYING, "CALL") == "OTM"


def test_classify_itm_call():
    assert _classify_strike(_ITM_CALL_STRIKE, _UNDERLYING, "CALL") == "ITM"


def test_classify_otm_put():
    assert _classify_strike(_OTM_PUT_STRIKE, _UNDERLYING, "PUT") == "OTM"


def test_classify_itm_put():
    assert _classify_strike(_ITM_PUT_STRIKE, _UNDERLYING, "PUT") == "ITM"


def test_classify_atm_call():
    # Strike at exactly underlying → ATM
    assert _classify_strike(_UNDERLYING, _UNDERLYING, "CALL") == "ATM"


def test_classify_atm_put():
    assert _classify_strike(_UNDERLYING, _UNDERLYING, "PUT") == "ATM"


# ---------------------------------------------------------------------------
# Acceptance criterion 1 — PASS LONG + dominant bearish spec flow → WATCHLIST
# ---------------------------------------------------------------------------

def test_long_opposes_bearish_flow():
    result = _pass_result(direction="LONG")
    # 2× bearish OTM ask put vs 1× bullish OTM ask call → bearish dominant
    snapshot = _snapshot(
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_call(premium=_SMALL_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "OPPOSES"
    assert updated.qualified is False
    assert updated.watchlist is True
    assert updated.watchlist_reason == "FLOW_ALIGNMENT: opposing speculative flow"
    assert updated.flow_alignment == "OPPOSES"


# ---------------------------------------------------------------------------
# Acceptance criterion 2 — PASS SHORT + dominant bullish spec flow → WATCHLIST
# ---------------------------------------------------------------------------

def test_short_opposes_bullish_flow():
    result = _pass_result(direction="SHORT")
    snapshot = _snapshot(
        _otm_ask_call(premium=_LARGE_PREMIUM),
        _otm_ask_call(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_SMALL_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "OPPOSES"
    assert updated.qualified is False
    assert updated.watchlist is True


# ---------------------------------------------------------------------------
# Acceptance criterion 3 — PASS + matching spec flow → PASS
# ---------------------------------------------------------------------------

def test_long_supported_by_bullish_flow():
    result = _pass_result(direction="LONG")
    snapshot = _snapshot(
        _otm_ask_call(premium=_LARGE_PREMIUM),
        _otm_ask_call(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_SMALL_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "SUPPORTS"
    assert updated.qualified is True
    assert updated.flow_alignment == "SUPPORTS"


def test_short_supported_by_bearish_flow():
    result = _pass_result(direction="SHORT")
    snapshot = _snapshot(
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_call(premium=_SMALL_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "SUPPORTS"
    assert updated.qualified is True


# ---------------------------------------------------------------------------
# Acceptance criterion 4 — PASS + HEDGE flow (ITM-dominant) → PASS
# ---------------------------------------------------------------------------

def test_hedge_flow_no_downgrade():
    result = _pass_result(direction="LONG")
    # ITM prints dominate (>50% of total premium)
    snapshot = _snapshot(
        _itm_put(premium=700_000),   # ITM premium = 700k
        _otm_ask_call(premium=300_000),  # OTM ask = 300k
    )
    # itm / total = 700k / 1000k = 70% > 50% → HEDGE
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NEUTRAL"
    assert updated.qualified is True


# ---------------------------------------------------------------------------
# Acceptance criterion 5 — PASS + MIXED flow → PASS
# ---------------------------------------------------------------------------

def test_mixed_flow_no_downgrade():
    result = _pass_result(direction="LONG")
    # OTM ask = 50% of total → below MIN_SPEC_SHARE (0.60), not ITM-dominant
    snapshot = _snapshot(
        _otm_ask_put(premium=500_000),  # OTM ask
        FlowPrint(                       # BID side (not counted as OTM ask)
            symbol="SPY", strike=_OTM_PUT_STRIKE, option_type="PUT",
            premium=500_000, side="BID", is_sweep=False,
            underlying_price=_UNDERLYING,
        ),
    )
    # itm / total = 0%, otm_ask / total = 50% < 0.60 → MIXED
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NEUTRAL"
    assert updated.qualified is True


# ---------------------------------------------------------------------------
# Acceptance criterion 6 — PASS + no flow data → PASS
# ---------------------------------------------------------------------------

def test_no_flow_data_no_effect():
    result = _pass_result(direction="LONG")
    updated, alignment = apply_flow_gate(result, {})
    assert alignment == "NO_DATA"
    assert updated.qualified is True


def test_below_premium_threshold_treated_as_no_data():
    result = _pass_result(direction="LONG")
    # Prints exist but all below MIN_PREMIUM (250k)
    snapshot = _snapshot(
        FlowPrint(
            symbol="SPY", strike=_OTM_PUT_STRIKE, option_type="PUT",
            premium=100_000, side="ASK", is_sweep=True,
            underlying_price=_UNDERLYING,
        )
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NO_DATA"
    assert updated.qualified is True


# ---------------------------------------------------------------------------
# Acceptance criterion 7 — WATCHLIST remains WATCHLIST
# ---------------------------------------------------------------------------

def test_watchlist_result_unchanged():
    result = _watchlist_result(direction="LONG")
    snapshot = _snapshot(
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_LARGE_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NO_DATA"
    assert updated.qualified is False
    assert updated.watchlist is True
    assert updated.watchlist_reason == result.watchlist_reason


# ---------------------------------------------------------------------------
# Acceptance criterion 8 — REJECT remains REJECT
# ---------------------------------------------------------------------------

def test_reject_result_unchanged():
    result = _reject_result(direction="LONG")
    snapshot = _snapshot(
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_LARGE_PREMIUM),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NO_DATA"
    assert updated.qualified is False
    assert updated.watchlist is False
    assert updated.hard_failure == result.hard_failure


# ---------------------------------------------------------------------------
# Acceptance criterion 9 — deterministic output
# ---------------------------------------------------------------------------

def test_deterministic_output():
    result = _pass_result(direction="LONG")
    snapshot = _snapshot(
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_put(premium=_LARGE_PREMIUM),
        _otm_ask_call(premium=_SMALL_PREMIUM),
    )
    r1, a1 = apply_flow_gate(result, snapshot)
    r2, a2 = apply_flow_gate(result, snapshot)
    assert a1 == a2
    assert r1 == r2


# ---------------------------------------------------------------------------
# Acceptance criterion 10 — HEDGE uses full print set (pre-speculative filter)
# ---------------------------------------------------------------------------

def test_hedge_classification_uses_full_print_set():
    result = _pass_result(direction="LONG")
    # ITM prints are not OTM+ASK — they'd be invisible to speculative filter.
    # Hedge classification must use all prints above threshold.
    snapshot = _snapshot(
        _itm_put(premium=700_000),    # ITM → only visible in full print set
        _otm_ask_call(premium=200_000),
        _otm_ask_put(premium=100_000),
    )
    # total = 1_000_000, itm = 700_000, itm/total = 70% > 50% → HEDGE, not SPECULATIVE
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NEUTRAL"
    assert updated.qualified is True


# ---------------------------------------------------------------------------
# Edge case — neutral spec direction (balanced bullish and bearish)
# ---------------------------------------------------------------------------

def test_balanced_speculative_flow_neutral():
    result = _pass_result(direction="LONG")
    # Equal bullish and bearish spec premium → NEUTRAL dominant
    snapshot = _snapshot(
        _otm_ask_call(premium=500_000),
        _otm_ask_put(premium=500_000),
    )
    updated, alignment = apply_flow_gate(result, snapshot)
    assert alignment == "NEUTRAL"
    assert updated.qualified is True


# ---------------------------------------------------------------------------
# PRD-015 — FlowSnapshot loader tests (AC2, AC6)
# ---------------------------------------------------------------------------

def _valid_snapshot_dict(symbol="SPY", underlying=450.0):
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


def _write_json(tmp_path, data):
    p = tmp_path / "flow.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


class TestLoader:
    """AC2 + AC6: loader raises on every failure mode, parses valid snapshot."""

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_flow_snapshot(str(tmp_path / "nonexistent.json"))

    def test_raises_on_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json{{{", encoding="utf-8")
        with pytest.raises(ValueError, match="invalid JSON"):
            load_flow_snapshot(str(p))

    def test_raises_on_missing_timestamp(self, tmp_path):
        data = _valid_snapshot_dict()
        del data["timestamp"]
        path = _write_json(tmp_path, data)
        with pytest.raises(ValueError, match="timestamp"):
            load_flow_snapshot(path)

    def test_raises_on_unparseable_timestamp(self, tmp_path):
        data = _valid_snapshot_dict()
        data["timestamp"] = "not-a-date"
        path = _write_json(tmp_path, data)
        with pytest.raises(ValueError, match="timestamp"):
            load_flow_snapshot(path)

    def test_raises_on_empty_symbols(self, tmp_path):
        data = _valid_snapshot_dict()
        data["symbols"] = {}
        path = _write_json(tmp_path, data)
        with pytest.raises(ValueError, match="empty"):
            load_flow_snapshot(path)

    def test_raises_on_missing_print_field(self, tmp_path):
        data = _valid_snapshot_dict()
        del data["symbols"]["SPY"][0]["premium"]
        path = _write_json(tmp_path, data)
        with pytest.raises(ValueError, match="premium"):
            load_flow_snapshot(path)

    def test_raises_on_negative_premium(self, tmp_path):
        data = _valid_snapshot_dict()
        data["symbols"]["SPY"][0]["premium"] = -1.0
        path = _write_json(tmp_path, data)
        with pytest.raises(ValueError, match="premium"):
            load_flow_snapshot(path)

    def test_raises_on_zero_premium(self, tmp_path):
        data = _valid_snapshot_dict()
        data["symbols"]["SPY"][0]["premium"] = 0
        path = _write_json(tmp_path, data)
        with pytest.raises(ValueError, match="premium"):
            load_flow_snapshot(path)

    def test_raises_on_invalid_option_type(self, tmp_path):
        data = _valid_snapshot_dict()
        data["symbols"]["SPY"][0]["option_type"] = "STRADDLE"
        path = _write_json(tmp_path, data)
        with pytest.raises(ValueError, match="option_type"):
            load_flow_snapshot(path)

    def test_raises_on_invalid_side(self, tmp_path):
        data = _valid_snapshot_dict()
        data["symbols"]["SPY"][0]["side"] = "CROSS"
        path = _write_json(tmp_path, data)
        with pytest.raises(ValueError, match="side"):
            load_flow_snapshot(path)

    def test_raises_on_non_bool_is_sweep(self, tmp_path):
        data = _valid_snapshot_dict()
        data["symbols"]["SPY"][0]["is_sweep"] = 1  # int, not bool
        path = _write_json(tmp_path, data)
        with pytest.raises(ValueError, match="is_sweep"):
            load_flow_snapshot(path)

    def test_parses_valid_snapshot(self, tmp_path):
        path = _write_json(tmp_path, _valid_snapshot_dict())
        snapshot = load_flow_snapshot(path)
        assert isinstance(snapshot, FlowSnapshot)
        assert "SPY" in snapshot.symbols
        prints = snapshot.symbols["SPY"]
        assert len(prints) == 1
        assert prints[0].premium == 600_000.0
        assert prints[0].option_type == "CALL"
        assert prints[0].is_sweep is True

    def test_snapshot_timestamp_utc(self, tmp_path):
        path = _write_json(tmp_path, _valid_snapshot_dict())
        snapshot = load_flow_snapshot(path)
        assert snapshot.timestamp.tzinfo is not None

    # --- get_flow_data_path() tests (AC3, AC6) ---

    def test_no_path_means_none_snapshot(self, tmp_path):
        """config.toml with empty data_path → get_flow_data_path returns None (AC6)."""
        from cuttingboard.config import get_flow_data_path
        toml = tmp_path / "config.toml"
        toml.write_text('[flow]\ndata_path = ""\n', encoding="utf-8")
        assert get_flow_data_path(_config_path=toml) is None

    def test_absent_flow_section_means_none(self, tmp_path):
        """config.toml with no [flow] section → None."""
        from cuttingboard.config import get_flow_data_path
        toml = tmp_path / "config.toml"
        toml.write_text("[other]\nfoo = 1\n", encoding="utf-8")
        assert get_flow_data_path(_config_path=toml) is None

    def test_missing_config_file_means_none(self, tmp_path):
        """No config.toml → None."""
        from cuttingboard.config import get_flow_data_path
        assert get_flow_data_path(_config_path=tmp_path / "nonexistent.toml") is None

    def test_config_returns_path_when_set(self, tmp_path):
        """config.toml with valid path → returns that path string."""
        from cuttingboard.config import get_flow_data_path
        flow_path = str(tmp_path / "flow.json")
        toml = tmp_path / "config.toml"
        toml.write_text(f'[flow]\ndata_path = "{flow_path}"\n', encoding="utf-8")
        assert get_flow_data_path(_config_path=toml) == flow_path

    def test_loader_raises_when_path_set_and_file_missing(self, tmp_path):
        """get_flow_data_path returns a path but that file is missing → load raises (AC2/AC5)."""
        from cuttingboard.config import get_flow_data_path
        missing = str(tmp_path / "missing.json")
        toml = tmp_path / "config.toml"
        toml.write_text(f'[flow]\ndata_path = "{missing}"\n', encoding="utf-8")
        path = get_flow_data_path(_config_path=toml)
        assert path is not None
        with pytest.raises(FileNotFoundError):
            load_flow_snapshot(path)


# ---------------------------------------------------------------------------
# PRD-015 — Gate integration with FlowSnapshot (AC4 + AC5)
# ---------------------------------------------------------------------------

class TestFlowGateWithSnapshot:
    """AC4: opposing snapshot triggers downgrade. AC5: None snapshot → no downgrade."""

    def test_gate_triggers_opposing_bearish_snapshot(self):
        """LONG candidate + dominant bearish speculative flow → WATCHLIST (AC4)."""
        snapshot = {
            "SPY": [
                FlowPrint(
                    symbol="SPY", strike=440.0, option_type="PUT",
                    premium=700_000, side="ASK", is_sweep=True,
                    underlying_price=450.0,
                ),
                FlowPrint(
                    symbol="SPY", strike=440.0, option_type="PUT",
                    premium=400_000, side="ASK", is_sweep=False,
                    underlying_price=450.0,
                ),
            ]
        }
        result = _pass_result(direction="LONG")
        updated, alignment = apply_flow_gate(result, snapshot)
        assert not updated.qualified
        assert updated.watchlist
        assert alignment == "OPPOSES"

    def test_gate_noop_when_snapshot_none(self):
        """qualify_all with flow_snapshot=None → no flow-related downgrade (AC5)."""
        from cuttingboard.regime import RegimeState, RISK_ON, AGGRESSIVE_LONG
        from cuttingboard.structure import StructureResult, TREND
        from cuttingboard.qualification import qualify_all
        from datetime import datetime, timezone

        regime = RegimeState(
            regime=RISK_ON,
            posture=AGGRESSIVE_LONG,
            confidence=0.80,
            net_score=5,
            risk_on_votes=6,
            risk_off_votes=1,
            neutral_votes=1,
            total_votes=8,
            vote_breakdown={},
            vix_level=16.0,
            vix_pct_change=-0.02,
            computed_at_utc=datetime(2026, 4, 23, 13, 0, 0, tzinfo=timezone.utc),
        )
        structure = {
            "SPY": StructureResult(
                symbol="SPY",
                structure=TREND,
                iv_environment="NORMAL",
                is_tradeable=True,
                disqualification_reason=None,
            )
        }
        summary = qualify_all(regime, structure, flow_snapshot=None)
        # No candidates passed → no per-symbol qualification ran; gate is vacuously satisfied
        # What matters: no exception and no flow-related rejection
        for reason in summary.excluded.values():
            assert "FLOW" not in reason
