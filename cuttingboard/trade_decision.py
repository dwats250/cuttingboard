from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from cuttingboard.chain_validation import ChainValidationResult, VALIDATED
from cuttingboard.options import OptionSetup
from cuttingboard.qualification import QualificationResult, TradeCandidate

ALLOW_TRADE = "ALLOW_TRADE"
BLOCK_TRADE = "BLOCK_TRADE"
VALID_DECISION_STATUSES = frozenset({ALLOW_TRADE, BLOCK_TRADE})


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
    block_reason = None if status == ALLOW_TRADE else (chain.reason or chain.classification)

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
    )
