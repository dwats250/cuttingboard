"""Pipeline result dataclasses for the runtime package (PRD-173, L0 leaf).

Extracted verbatim from the former ``cuttingboard/runtime.py`` and
re-exported by ``cuttingboard.runtime`` (``__init__``). L0 leaf: imports
only stdlib and non-runtime ``cuttingboard.*`` field types, never
``cuttingboard.runtime``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from cuttingboard.chain_validation import ChainValidationResult
from cuttingboard.correlation import CorrelationResult
from cuttingboard.ingestion import RawQuote
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.options import OptionSetup
from cuttingboard.qualification import QualificationSummary
from cuttingboard.regime import RegimeState
from cuttingboard.sector_router import SuppressedCandidate
from cuttingboard.trade_decision import TradeDecision
from cuttingboard.validation import ValidationSummary
from cuttingboard.watch import WatchSummary


@dataclass
class _PartialPipelineResult:
    """Lightweight view passed to the contract builder before PipelineResult is frozen."""
    mode: str
    generation_id: str
    run_at_utc: datetime
    date_str: str
    raw_quotes: dict
    normalized_quotes: dict
    validation_summary: Any
    regime: Any
    router_mode: str
    qualification_summary: Any
    watch_summary: Any
    option_setups: list
    chain_results: dict
    alert_sent: bool
    report_path: str
    errors: list
    correlation: Optional[CorrelationResult] = None
    trade_decisions: list[TradeDecision] = field(default_factory=list)
    thesis_map: Optional[dict] = None
    invalidation_guidance_map: Optional[dict] = None
    entry_quality_map: Optional[dict] = None


@dataclass(frozen=True)
class PipelineResult:
    mode: str
    generation_id: str
    run_at_utc: datetime
    date_str: str
    raw_quotes: dict[str, RawQuote]
    normalized_quotes: dict[str, NormalizedQuote]
    validation_summary: ValidationSummary
    regime: Optional[RegimeState]
    router_mode: str
    energy_score: float
    index_score: float
    qualification_summary: Optional[QualificationSummary]
    watch_summary: Optional[WatchSummary]
    candidates_generated: int
    option_setups: list[OptionSetup]
    trade_decisions: list[TradeDecision]
    suppressed_candidates: list[SuppressedCandidate]
    chain_results: dict[str, ChainValidationResult]
    outcome: str
    alert_sent: bool
    report: str
    report_path: str
    audit_record: dict[str, Any]
    warnings: list[str]
    errors: list[str]
    summary: dict[str, Any]
    contract: dict[str, Any]
    correlation: Optional[CorrelationResult] = None
    premarket_report: dict[str, Any] = field(default_factory=dict)
    postmarket_report: dict[str, Any] = field(default_factory=dict)
    market_map: dict[str, Any] = field(default_factory=dict)
    visibility_map: dict[str, dict] = field(default_factory=dict)
    explanation_map: dict[str, dict] = field(default_factory=dict)


__all__ = ["_PartialPipelineResult", "PipelineResult"]
