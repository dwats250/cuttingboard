"""PRD-233: assert_valid_contract runs at pipeline finalization.

Two surfaces, red-first:

1. Unit — the validator's system_state key whitelist (7 builder keys + 4
   declared runtime injections) and the `finalized=True` mode that makes
   runtime's post-build mutations part of the declared schema.
2. Pipeline — a corrupted contract raises inside _run_pipeline BEFORE any
   artifact write (no audit record appended); execute_run's existing
   handler is what turns that into a fail-loud ERROR contract.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from cuttingboard import runtime
from cuttingboard.chain_validation import ChainValidationResult, MANUAL_CHECK
from cuttingboard.contract import assert_valid_contract, build_error_contract
from cuttingboard.trade_decision import ALLOW_TRADE

from tests.test_contract import (
    _NOW,
    _FakePipelineResult,
    _build,
    _chain_result,
    _option_setup,
    _qual_summary,
    _regime,
    _trade_decision,
)
from tests.test_runtime_decision import _setup_runtime_mocks


def _valid_contract() -> dict:
    pr = _FakePipelineResult(
        regime=_regime(),
        qualification_summary=_qual_summary(qualified=1),
        option_setups=[_option_setup()],
        chain_results={"SPY": _chain_result()},
        trade_decisions=[_trade_decision()],
    )
    return _build(pr)


def _finalize(contract: dict) -> dict:
    """Apply the same post-build mutations _run_pipeline performs."""
    contract["outcome"] = "TRADE"
    contract["system_state"]["outcome"] = "TRADE"
    contract["system_state"]["permission"] = "New trades permitted."
    contract["system_state"]["reason"] = contract["system_state"].get("stay_flat_reason")
    contract["artifacts"]["notification_sent"] = False
    return contract


# ---------------------------------------------------------------------------
# R1 — system_state key whitelist
# ---------------------------------------------------------------------------

def test_undeclared_system_state_key_fails_default_mode():
    contract = _valid_contract()
    contract["system_state"]["wibble"] = True

    with pytest.raises(AssertionError, match="wibble"):
        assert_valid_contract(contract)


def test_undeclared_system_state_key_fails_on_error_contract():
    # The whitelist must run before the STATUS_ERROR early return.
    contract = build_error_contract(
        generated_at=_NOW,
        generation_id="error-test",
        artifacts={},
        error_detail="boom",
    )
    contract["system_state"]["wibble"] = True

    with pytest.raises(AssertionError, match="wibble"):
        assert_valid_contract(contract)


def test_error_contract_without_extras_still_valid():
    contract = build_error_contract(
        generated_at=_NOW,
        generation_id="error-test",
        artifacts={},
        error_detail="boom",
    )
    assert_valid_contract(contract)  # must not raise


# ---------------------------------------------------------------------------
# R2 — finalized mode
# ---------------------------------------------------------------------------

def test_finalized_contract_passes():
    contract = _finalize(_valid_contract())
    assert_valid_contract(contract, finalized=True)  # must not raise


def test_finalized_sunday_session_type_is_declared():
    contract = _finalize(_valid_contract())
    contract["system_state"]["session_type"] = "SUNDAY_PREMARKET"
    assert_valid_contract(contract, finalized=True)  # must not raise


def test_finalized_missing_permission_fails():
    contract = _finalize(_valid_contract())
    del contract["system_state"]["permission"]

    with pytest.raises(AssertionError, match="permission"):
        assert_valid_contract(contract, finalized=True)


def test_finalized_missing_top_level_outcome_fails():
    contract = _finalize(_valid_contract())
    del contract["outcome"]

    with pytest.raises(AssertionError, match="outcome"):
        assert_valid_contract(contract, finalized=True)


def test_finalized_missing_notification_sent_fails():
    contract = _finalize(_valid_contract())
    del contract["artifacts"]["notification_sent"]

    with pytest.raises(AssertionError, match="notification_sent"):
        assert_valid_contract(contract, finalized=True)


def test_builder_contract_passes_default_mode():
    # Un-finalized builder output (no runtime injections) must stay valid
    # under the default mode — existing builder tests keep their meaning.
    assert_valid_contract(_valid_contract())  # must not raise


# ---------------------------------------------------------------------------
# R3 — live in _run_pipeline, before artifact writes
# ---------------------------------------------------------------------------

def _run_mocked_pipeline(monkeypatch, tmp_path):
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {
        "SPY": ChainValidationResult(
            symbol="SPY",
            classification=MANUAL_CHECK,
            reason="fixture mode skips live chain validation",
            spread_pct=None,
            open_interest=None,
            volume=None,
            expiry_used=None,
            data_source=None,
        )
    })
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *args, **kwargs: runtime.TradeDecision(
        ticker="SPY",
        direction="LONG",
        status=ALLOW_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=None,
    ))
    return runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )


def test_pipeline_rejects_undeclared_system_state_key(monkeypatch, tmp_path):
    def _corrupting_overnight_policy(*, contract, market_map, timestamp):
        contract["system_state"]["smuggled_key"] = "oops"
        return contract

    monkeypatch.setattr(runtime, "apply_overnight_policy", _corrupting_overnight_policy)

    with pytest.raises(AssertionError, match="smuggled_key"):
        _run_mocked_pipeline(monkeypatch, tmp_path)

    # Fail-loud BEFORE artifact writes: no audit record was appended.
    audit_path = tmp_path / "logs" / "audit.jsonl"
    assert not audit_path.exists(), "audit record written despite corrupt contract"


def test_pipeline_validates_clean_contract(monkeypatch, tmp_path):
    # Guard against a can't-fail test: the same harness with no corruption
    # completes, proving the corruption (not the mocks) is what raises above.
    result = _run_mocked_pipeline(monkeypatch, tmp_path)
    assert result.outcome == runtime.OUTCOME_TRADE
