"""Frozen data models for the PRD 5 Output Standard Layer."""

from dataclasses import dataclass
from typing import Literal

ReasonCode = Literal[
    "INVALID_INPUT",
    "MACRO_CONFLICT",
    "MARKET_CHAOTIC",
    "NEUTRAL_POSTURE",
    "NO_STRUCTURE",
    "RR_INVALID",
    "VOL_MISMATCH",
]


@dataclass(frozen=True)
class TradeOutput:
    ticker: str
    direction: str
    structure: str
    entry: float
    stop: float
    target: float
    rr: float
    spread_type: str
    duration: str


@dataclass(frozen=True)
class RejectedTrade:
    ticker: str
    reason: ReasonCode
    direction: str
    structure: str


@dataclass(frozen=True)
class SummaryStats:
    total_candidates: int
    approved_count: int
    rejected_count: int
    rejection_breakdown: dict[ReasonCode, int]


@dataclass(frozen=True)
class SystemReport:
    timestamp: str
    posture: str
    market_quality: str
    top_trades: list[TradeOutput]
    watchlist: list[TradeOutput]
    rejected: list[RejectedTrade]
    summary: SummaryStats
