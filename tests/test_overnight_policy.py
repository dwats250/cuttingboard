from __future__ import annotations

import copy
from datetime import datetime, timezone

import pytest

from cuttingboard.overnight_policy import apply_overnight_policy

EOD_AT = datetime(2026, 4, 30, 19, 45, tzinfo=timezone.utc)
NON_EOD_AT = datetime(2026, 4, 30, 18, 0, tzinfo=timezone.utc)


def _candidate(**overrides):
    candidate = {
        "symbol": "SPY",
        "direction": "LONG",
        "strategy_tag": "LONG_CALL",
        "entry": 100.0,
        "timeframe": "21",
        "decision_status": "ALLOW_TRADE",
        "block_reason": None,
        "decision_trace": {
            "stage": "CHAIN_VALIDATION",
            "source": "chain_validation",
            "reason": "TOP_TRADE_VALIDATED",
        },
        "policy_allowed": True,
        "policy_reason": "policy_allowed",
        "size_multiplier": 1.0,
    }
    candidate.update(overrides)
    return candidate


def _contract(candidate=None, *, market_regime="RISK_ON", continuation_enabled=True):
    return {
        "status": "OK",
        "outcome": "TRADE",
        "system_state": {"market_regime": market_regime},
        "market_context": {"continuation_enabled": continuation_enabled},
        "trade_candidates": [candidate or _candidate()],
    }


def _market_map(*, symbol="SPY", watch_zones=None):
    if watch_zones is None:
        watch_zones = [{"type": "VWAP", "level": 120.0, "context": "session vwap"}]
    return {"symbols": {symbol: {"watch_zones": watch_zones}}}


def _policy(contract):
    return contract["trade_candidates"][0]["overnight_policy"]


def test_outside_eod_window_returns_unchanged_contract_without_policy():
    contract = _contract()
    original = copy.deepcopy(contract)

    result = apply_overnight_policy(
        contract=contract,
        market_map=_market_map(),
        timestamp=NON_EOD_AT,
    )

    assert result == original
    assert result is contract
    assert "overnight_policy" not in result["trade_candidates"][0]


@pytest.mark.parametrize("timeframe", ["9", 9, "bad", None])
def test_dte_below_minimum_or_missing_fails_closed(timeframe):
    result = apply_overnight_policy(
        contract=_contract(_candidate(timeframe=timeframe)),
        market_map=_market_map(),
        timestamp=EOD_AT,
    )

    assert _policy(result) == {"decision": "FORCE_EXIT", "reason": "DTE_TOO_LOW"}


def test_dte_below_hard_exit_is_force_exit():
    result = apply_overnight_policy(
        contract=_contract(_candidate(timeframe="6")),
        market_map=_market_map(),
        timestamp=EOD_AT,
    )

    assert _policy(result) == {"decision": "FORCE_EXIT", "reason": "DTE_TOO_LOW"}


def test_near_key_level_fails_closed():
    result = apply_overnight_policy(
        contract=_contract(),
        market_map=_market_map(watch_zones=[{"type": "VWAP", "level": 100.5}]),
        timestamp=EOD_AT,
    )

    assert _policy(result) == {"decision": "FORCE_EXIT", "reason": "NEAR_KEY_LEVEL"}


def test_missing_or_non_numeric_entry_fails_closed():
    result = apply_overnight_policy(
        contract=_contract(_candidate(entry="bad")),
        market_map=_market_map(),
        timestamp=EOD_AT,
    )

    assert _policy(result) == {"decision": "FORCE_EXIT", "reason": "NEAR_KEY_LEVEL"}


def test_chaotic_regime_force_exits():
    result = apply_overnight_policy(
        contract=_contract(market_regime="CHAOTIC"),
        market_map=_market_map(),
        timestamp=EOD_AT,
    )

    assert _policy(result) == {"decision": "FORCE_EXIT", "reason": "REGIME_UNSTABLE"}


def test_missing_symbol_market_map_data_fails_closed():
    result = apply_overnight_policy(
        contract=_contract(),
        market_map=_market_map(symbol="QQQ"),
        timestamp=EOD_AT,
    )

    assert _policy(result) == {"decision": "FORCE_EXIT", "reason": "NEAR_KEY_LEVEL"}


def test_non_expansion_support_reduces_clean_candidate():
    result = apply_overnight_policy(
        contract=_contract(continuation_enabled=False),
        market_map=_market_map(),
        timestamp=EOD_AT,
    )

    assert _policy(result) == {"decision": "REDUCE_POSITION", "reason": "NO_EXPANSION_SUPPORT"}


def test_spread_candidate_increases_pass_severity_by_one_level():
    result = apply_overnight_policy(
        contract=_contract(_candidate(strategy_tag="BULL_CALL_SPREAD")),
        market_map=_market_map(),
        timestamp=EOD_AT,
    )

    assert _policy(result) == {"decision": "REDUCE_POSITION", "reason": "SPREAD_FRAGILITY"}


def test_spread_candidate_increases_reduce_severity_to_force_exit():
    result = apply_overnight_policy(
        contract=_contract(_candidate(strategy_tag="BULL_CALL_SPREAD"), continuation_enabled=False),
        market_map=_market_map(),
        timestamp=EOD_AT,
    )

    assert _policy(result) == {"decision": "FORCE_EXIT", "reason": "SPREAD_FRAGILITY"}


def test_spread_candidate_does_not_override_existing_force_exit_reason():
    result = apply_overnight_policy(
        contract=_contract(_candidate(strategy_tag="BULL_CALL_SPREAD", timeframe="6")),
        market_map=_market_map(),
        timestamp=EOD_AT,
    )

    assert _policy(result) == {"decision": "FORCE_EXIT", "reason": "DTE_TOO_LOW"}


def test_clean_non_spread_candidate_allows_hold():
    result = apply_overnight_policy(
        contract=_contract(),
        market_map=_market_map(),
        timestamp=EOD_AT,
    )

    assert _policy(result) == {"decision": "ALLOW_HOLD", "reason": "PASS_ALL"}


@pytest.mark.parametrize(
    "contract",
    [
        None,
        {},
        {"trade_candidates": []},
        {"trade_candidates": [], "system_state": {}},
    ],
)
def test_missing_required_top_level_inputs_raise_runtime_error(contract):
    market_map = _market_map() if contract is not None and "market_context" in contract else None

    with pytest.raises(RuntimeError):
        apply_overnight_policy(contract=contract, market_map=market_map, timestamp=EOD_AT)


def test_missing_required_market_map_raises_runtime_error():
    with pytest.raises(RuntimeError):
        apply_overnight_policy(contract=_contract(), market_map=None, timestamp=EOD_AT)


def test_repeated_runs_with_identical_inputs_are_deterministic():
    contract = _contract()
    market_map = _market_map()

    result_1 = apply_overnight_policy(
        contract=copy.deepcopy(contract),
        market_map=copy.deepcopy(market_map),
        timestamp=EOD_AT,
    )
    result_2 = apply_overnight_policy(
        contract=copy.deepcopy(contract),
        market_map=copy.deepcopy(market_map),
        timestamp=EOD_AT,
    )

    assert result_1 == result_2
