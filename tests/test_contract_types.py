"""PRD-237: the TypedDict schema is LOAD-BEARING, not documentation.

The repo runs no static type checker, so these sync guards are what makes
type/code drift fail the suite: every guard compares a TypedDict's
__required_keys__/__optional_keys__ against what the producers actually
write (or against the PRD-233 whitelist the validator enforces).

Mutation-verified per PRD-198 invariant 4: removing any key from a
TypedDict, adding an undeclared producer key, or editing
SYSTEM_STATE_ALLOWED_KEYS makes the matching guard fail (demonstrated at
implementation; each assertion is a strict set equality, so it cannot
rot to always-green).
"""

from __future__ import annotations

from cuttingboard.contract import SYSTEM_STATE_ALLOWED_KEYS, build_error_contract
from cuttingboard.contract_types import (
    ContractCandidate,
    DecisionTrace,
    OvernightPolicyDecision,
    PipelineContract,
    SystemState,
)

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


def _built_contract() -> dict:
    pr = _FakePipelineResult(
        regime=_regime(),
        qualification_summary=_qual_summary(qualified=1),
        option_setups=[_option_setup()],
        chain_results={"SPY": _chain_result()},
        trade_decisions=[_trade_decision()],
    )
    return _build(pr)


# ---------------------------------------------------------------------------
# Guard (a): SystemState <-> the PRD-233 enforced whitelist
# ---------------------------------------------------------------------------

def test_system_state_type_matches_enforced_whitelist():
    assert set(SystemState.__annotations__) == set(SYSTEM_STATE_ALLOWED_KEYS), (
        "SystemState and SYSTEM_STATE_ALLOWED_KEYS drifted — declare new keys "
        "in BOTH cuttingboard/contract_types.py and cuttingboard/contract.py"
    )


def test_system_state_required_keys_match_builder():
    contract = _built_contract()
    built_keys = set(contract["system_state"])

    # Builder writes the required set plus confidence (optional because the
    # error contract omits it); runtime injections are the other optionals.
    assert built_keys == set(SystemState.__required_keys__) | {"confidence"}
    assert set(SystemState.__optional_keys__) == {
        "confidence", "outcome", "permission", "reason", "session_type",
    }


# ---------------------------------------------------------------------------
# Guard (b): PipelineContract <-> build_pipeline_output_contract
# ---------------------------------------------------------------------------

def test_top_level_keys_match_builder():
    contract = _built_contract()

    assert set(contract) == set(PipelineContract.__required_keys__), (
        "build_pipeline_output_contract and PipelineContract drifted"
    )
    assert set(PipelineContract.__optional_keys__) == {"outcome"}, (
        "top-level optionals must stay exactly the runtime-injected outcome"
    )


# ---------------------------------------------------------------------------
# Guard (c): ContractCandidate <-> _build_trade_candidates
# ---------------------------------------------------------------------------

def test_candidate_keys_match_builder():
    contract = _built_contract()
    candidate = contract["trade_candidates"][0]

    assert set(candidate) == set(ContractCandidate.__required_keys__), (
        "_build_trade_candidates and ContractCandidate drifted"
    )
    assert set(ContractCandidate.__optional_keys__) == {"overnight_policy"}
    assert set(candidate["decision_trace"]) == set(DecisionTrace.__annotations__)
    assert set(OvernightPolicyDecision.__annotations__) == {"decision", "reason"}


# ---------------------------------------------------------------------------
# Guard (d): the error contract stays inside the declared shape
# ---------------------------------------------------------------------------

def test_error_contract_system_state_is_declared_subset():
    err = build_error_contract(
        generated_at=_NOW,
        generation_id="error-test",
        artifacts={},
        error_detail="boom",
    )

    # Error block = exactly the required keys (no confidence, no injections).
    assert set(err["system_state"]) == set(SystemState.__required_keys__)
    # Error top level = the full builder shape (outcome injected later by
    # execute_run's handler, hence not present here).
    assert set(err) == set(PipelineContract.__required_keys__)
