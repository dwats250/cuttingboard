from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from cuttingboard.chain_validation import ChainValidationResult, VALIDATED
from cuttingboard.options import OptionSetup
from cuttingboard.qualification import QualificationResult, TradeCandidate

ALLOW_TRADE = "ALLOW_TRADE"
BLOCK_TRADE = "BLOCK_TRADE"
VALID_DECISION_STATUSES = frozenset({ALLOW_TRADE, BLOCK_TRADE})
TRACE_STAGE_CHAIN_VALIDATION = "CHAIN_VALIDATION"
TRACE_SOURCE_CHAIN_VALIDATION = "chain_validation"
TRACE_REASON_ALLOW = "TOP_TRADE_VALIDATED"


def _default_decision_trace() -> dict[str, str]:
    return {
        "stage": TRACE_STAGE_CHAIN_VALIDATION,
        "source": TRACE_SOURCE_CHAIN_VALIDATION,
        "reason": TRACE_REASON_ALLOW,
    }


@dataclass(frozen=True)
class TradeDecision:
    ticker: str
    direction: str
    status: str
    entry: float
    stop: float
    target: float
    r_r: float
    contracts: int
    dollar_risk: float
    block_reason: Optional[str]
    decision_trace: dict[str, str] = field(default_factory=_default_decision_trace)

    def __post_init__(self) -> None:
        if self.status not in VALID_DECISION_STATUSES:
            raise ValueError(f"invalid trade decision status: {self.status!r}")

        numeric_fields = {
            "entry": self.entry,
            "stop": self.stop,
            "target": self.target,
            "r_r": self.r_r,
            "dollar_risk": self.dollar_risk,
        }
        for label, value in numeric_fields.items():
            if not math.isfinite(float(value)):
                raise ValueError(f"{label} must be finite")

        if not math.isfinite(float(self.contracts)):
            raise ValueError("contracts must be finite")
        if int(self.contracts) < 1:
            raise ValueError("contracts must be >= 1")

        if self.status == ALLOW_TRADE and self.block_reason is not None:
            raise ValueError("ALLOW_TRADE requires block_reason=None")
        if self.status == BLOCK_TRADE and not self.block_reason:
            raise ValueError("BLOCK_TRADE requires non-empty block_reason")

        trace_keys = {"stage", "source", "reason"}
        if set(self.decision_trace) != trace_keys:
            raise ValueError("decision_trace must contain exactly stage, source, reason")
        for key in ("stage", "source", "reason"):
            value = self.decision_trace.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"decision_trace.{key} must be non-empty string")


def create_trade_decision(
    candidate: TradeCandidate,
    result: QualificationResult,
    setup: OptionSetup,
    chain: ChainValidationResult,
) -> TradeDecision:
    risk = abs(candidate.entry_price - candidate.stop_price)
    reward = abs(candidate.target_price - candidate.entry_price)
    if risk <= 0:
        raise ValueError(f"{candidate.symbol}: entry and stop must define positive risk")

    status = ALLOW_TRADE if chain.classification == VALIDATED else BLOCK_TRADE
    if status == ALLOW_TRADE:
        decision_trace = {
            "stage": TRACE_STAGE_CHAIN_VALIDATION,
            "source": TRACE_SOURCE_CHAIN_VALIDATION,
            "reason": TRACE_REASON_ALLOW,
        }
    else:
        decision_trace = {
            "stage": TRACE_STAGE_CHAIN_VALIDATION,
            "source": TRACE_SOURCE_CHAIN_VALIDATION,
            "reason": chain.reason or chain.classification,
        }
    block_reason = None if status == ALLOW_TRADE else decision_trace["reason"]

    return TradeDecision(
        ticker=candidate.symbol,
        direction=result.direction,
        status=status,
        entry=float(candidate.entry_price),
        stop=float(candidate.stop_price),
        target=float(candidate.target_price),
        r_r=round(reward / risk, 2),
        contracts=int(setup.max_contracts),
        dollar_risk=float(setup.dollar_risk),
        block_reason=block_reason,
        decision_trace=decision_trace,
    )
