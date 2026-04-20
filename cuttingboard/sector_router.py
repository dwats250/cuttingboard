"""Minimal compatibility layer for runtime sector routing imports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from cuttingboard.qualification import QualificationSummary


@dataclass(frozen=True)
class SectorRouterState:
    mode: str
    energy_score: float
    index_score: float
    computed_at_utc: datetime
    session_date: str


@dataclass(frozen=True)
class SuppressedCandidate:
    symbol: str
    reason: str
    sector: Optional[str] = None


def resolve_sector_router(
    quotes: dict,
    derived: dict,
    computed_at_utc: datetime,
    *,
    state_path: Optional[str] = None,
) -> SectorRouterState:
    del quotes, derived, state_path
    return SectorRouterState(
        mode="MIXED",
        energy_score=0.0,
        index_score=0.0,
        computed_at_utc=computed_at_utc,
        session_date=computed_at_utc.date().isoformat(),
    )


def apply_sector_router(
    qualification_summary: QualificationSummary,
    router_state: SectorRouterState,
    asof: datetime,
) -> tuple[QualificationSummary, list[SuppressedCandidate]]:
    del router_state, asof
    return qualification_summary, []
