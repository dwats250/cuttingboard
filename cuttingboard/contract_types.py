"""PRD-237 (master-plan J1): the pipeline output contract's shape, as types.

This is a LEAF module — it imports nothing from the package, so
`contract.py`, `delivery/payload.py`, and every downstream consumer can
import it without cycles.

These TypedDicts are the single schema artifact for the contract dict,
its `system_state` block, and `trade_candidates` items. They were derived
from the producers (code is truth), not from prose:

- top level:      contract.build_pipeline_output_contract / build_error_contract
- system_state:   contract._build_system_state + the runtime injections in
                  runtime._build_and_finalize_contract (PRD-233's
                  SYSTEM_STATE_ALLOWED_KEYS is the enforced whitelist)
- candidates:     contract._build_trade_candidates + overnight_policy.
                  apply_overnight_policy (EOD window only)

The repo runs no static type checker, so these types are made
LOAD-BEARING by tests/test_contract_types.py: the sync guards fail the
suite if a producer key and a TypedDict key ever drift apart. Keep
`NotRequired` placement in lockstep with reality:

- ``outcome`` (top level) and system_state ``outcome`` / ``permission`` /
  ``reason`` are injected by the runtime at finalization — absent in raw
  builder output and in error contracts. ``assert_valid_contract(...,
  finalized=True)`` is the runtime enforcement of the stronger
  at-persist invariant.
- system_state ``session_type`` is Sunday-only; ``confidence`` is built
  for normal contracts but absent from error contracts.
- candidate ``overnight_policy`` exists only when apply_overnight_policy
  ran inside the EOD window.
"""

# NOTE: no `from __future__ import annotations` here — PEP 563 string
# annotations prevent TypedDict from classifying NotRequired keys into
# __optional_keys__ on Python 3.11, which the sync guards depend on.
from typing import Any, NotRequired, Optional, TypedDict


class SystemState(TypedDict):
    """`contract["system_state"]` — built keys + declared runtime injections."""

    router_mode: Optional[str]
    market_regime: Optional[str]
    intraday_state: Optional[str]
    time_gate_open: Optional[bool]
    tradable: bool
    stay_flat_reason: Optional[str]
    # Built for normal contracts; ABSENT from build_error_contract's block.
    confidence: NotRequired[Optional[float]]
    # Runtime injections (runtime._build_and_finalize_contract; hourly path
    # injects outcome only). Required at finalization, never at build.
    outcome: NotRequired[str]
    permission: NotRequired[str]
    reason: NotRequired[Optional[str]]
    # Sunday path only (MODE_SUNDAY).
    session_type: NotRequired[str]


class DecisionTrace(TypedDict):
    """`trade_candidates[i]["decision_trace"]` — all three non-empty strings."""

    stage: str
    source: str
    reason: str


class OvernightPolicyDecision(TypedDict):
    """`trade_candidates[i]["overnight_policy"]` (EOD window only)."""

    decision: str
    reason: str


class ContractCandidate(TypedDict):
    """`contract["trade_candidates"][i]` as _build_trade_candidates writes it."""

    symbol: str
    direction: Optional[str]
    entry_mode: Optional[str]
    strategy_tag: Optional[str]
    # Always None today — no producer sets it; retained for shape stability.
    trigger: Optional[str]
    entry: float
    stop: float
    target: float
    risk_reward: float
    timeframe: Optional[str]
    setup_quality: Optional[str]
    notes: Optional[str]
    decision_status: str
    block_reason: Optional[str]
    decision_trace: DecisionTrace
    policy_allowed: bool
    policy_reason: str
    size_multiplier: float
    position_size: Optional[int]
    dollar_risk: Optional[float]
    estimated_debit: float
    visibility_status: Optional[str]
    visibility_reason: Optional[str]
    enable_conditions: list[str]
    explanation: dict[str, Any]
    thesis: Optional[dict[str, Any]]
    invalidation_guidance: Optional[dict[str, Any]]
    entry_quality: Optional[dict[str, Any]]
    # Attached by overnight_policy.apply_overnight_policy in the EOD window.
    overnight_policy: NotRequired[OvernightPolicyDecision]


class PipelineContract(TypedDict):
    """The canonical pipeline output contract (schema_version v2)."""

    schema_version: str
    generation_id: Optional[str]
    generated_at: str
    session_date: Optional[str]
    mode: Optional[str]
    status: str
    timezone: str
    system_state: SystemState
    market_context: dict[str, Any]
    trade_candidates: list[ContractCandidate]
    rejections: list[dict[str, Any]]
    audit_summary: dict[str, Any]
    artifacts: dict[str, Any]
    correlation: Optional[dict[str, Any]]
    regime: Optional[dict[str, Any]]
    macro_drivers: dict[str, Any]
    # Runtime-injected at finalization (and on the hourly/error paths);
    # absent in raw builder output.
    outcome: NotRequired[str]
