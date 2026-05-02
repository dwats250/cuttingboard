"""PRD-069: Entry Quality and Chase Filter.

Classifies entry quality for each ALLOW_TRADE candidate and blocks trades
where the entry is deterministically identified as extended, stale, chased,
or missing a valid entry condition.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from cuttingboard.qualification import QualificationResult, TradeCandidate
from cuttingboard.structure import StructureResult
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE, TradeDecision

ENTRY_QUALITY_CLEAN = "CLEAN"
ENTRY_QUALITY_EXTENDED = "EXTENDED"
ENTRY_QUALITY_STALE = "STALE"
ENTRY_QUALITY_CHASE_RISK = "CHASE_RISK"
ENTRY_QUALITY_MISSING_ENTRY = "MISSING_ENTRY"
ENTRY_QUALITY_UNKNOWN = "UNKNOWN"

VALID_STATUSES = frozenset(
    {
        ENTRY_QUALITY_CLEAN,
        ENTRY_QUALITY_EXTENDED,
        ENTRY_QUALITY_STALE,
        ENTRY_QUALITY_CHASE_RISK,
        ENTRY_QUALITY_MISSING_ENTRY,
        ENTRY_QUALITY_UNKNOWN,
    }
)

ACTION_ALLOW = "ALLOW"
ACTION_WAIT = "WAIT"
ACTION_AVOID = "AVOID"
ACTION_UNKNOWN = "UNKNOWN"

VALID_ACTIONS = frozenset({ACTION_ALLOW, ACTION_WAIT, ACTION_AVOID, ACTION_UNKNOWN})

BLOCKING_STATUSES = frozenset(
    {
        ENTRY_QUALITY_EXTENDED,
        ENTRY_QUALITY_STALE,
        ENTRY_QUALITY_CHASE_RISK,
        ENTRY_QUALITY_MISSING_ENTRY,
    }
)

_BLOCK_REASON = "ENTRY_QUALITY_BLOCK"
_BLOCK_TRACE = {
    "stage": "ENTRY_QUALITY_GATE",
    "source": "entry_quality",
    "reason": _BLOCK_REASON,
}


def _classify(
    symbol: str,
    qual: Optional[QualificationResult],
    structure: Optional[StructureResult],
    thesis: Optional[dict],
    decision: TradeDecision,
) -> dict:
    """Return an entry_quality dict for one symbol using only deterministic inputs."""
    has_entry_mode = qual is not None and bool(getattr(qual, "entry_mode", None))
    has_structure = structure is not None and bool(getattr(structure, "structure", None))
    has_thesis = thesis is not None
    thesis_status = thesis.get("status") if has_thesis else None
    confirmation = thesis.get("confirmation") if has_thesis else None
    invalidation = thesis.get("invalidation") if has_thesis else None
    has_confirmation = confirmation not in (None, "UNKNOWN")
    has_invalidation = invalidation is not None

    has_any_input = has_entry_mode or has_structure or has_confirmation or has_invalidation

    if not has_any_input:
        return {
            "status": ENTRY_QUALITY_MISSING_ENTRY,
            "action": ACTION_AVOID,
            "reason": "MISSING_ENTRY_CONDITION",
            "blocking": True,
            "source": "entry_quality_gate",
        }

    # STALE: qualification explicitly marks setup as no longer fresh
    if qual is not None and getattr(qual, "rejection_reason", None):
        return {
            "status": ENTRY_QUALITY_STALE,
            "action": ACTION_WAIT,
            "reason": f"STALE:{qual.rejection_reason}",
            "blocking": True,
            "source": "qualification.rejection_reason",
        }

    # CHASE_RISK: thesis is actively conflicted with an invalidation signal present
    if thesis_status == "CONFLICTED" and has_invalidation:
        return {
            "status": ENTRY_QUALITY_CHASE_RISK,
            "action": ACTION_AVOID,
            "reason": f"CHASE_RISK:thesis_conflicted|invalidation={invalidation}",
            "blocking": True,
            "source": "thesis_map.status+invalidation",
        }

    # EXTENDED: entry mode and structure present but thesis confirmation is absent
    if has_entry_mode and has_structure and has_thesis and confirmation == "UNKNOWN":
        return {
            "status": ENTRY_QUALITY_EXTENDED,
            "action": ACTION_WAIT,
            "reason": f"EXTENDED:no_confirmation|structure={structure.structure}",
            "blocking": True,
            "source": "execution_structure.structure+thesis_map.confirmation",
        }

    # CLEAN: entry mode present with a valid confirmation signal
    if has_entry_mode and has_confirmation:
        return {
            "status": ENTRY_QUALITY_CLEAN,
            "action": ACTION_ALLOW,
            "reason": None,
            "blocking": False,
            "source": "entry_quality_gate",
        }

    # UNKNOWN: inputs exist but no deterministic classification is possible
    return {
        "status": ENTRY_QUALITY_UNKNOWN,
        "action": ACTION_UNKNOWN,
        "reason": "INSUFFICIENT_DETERMINISTIC_INPUTS",
        "blocking": False,
        "source": "entry_quality_gate",
    }


def apply_entry_quality_gate(
    trade_decisions: list[TradeDecision],
    candidates: dict[str, TradeCandidate],
    qualified_by_symbol: dict[str, QualificationResult],
    execution_structure: dict[str, StructureResult],
    thesis_map: dict[str, dict],
) -> tuple[list[TradeDecision], dict[str, dict]]:
    """Classify entry quality and block ALLOW_TRADE decisions with blocking statuses.

    Returns (decisions, entry_quality_map). Runs after apply_thesis_gate.
    Does not modify decisions already BLOCK_TRADE.
    """
    entry_quality_map: dict[str, dict] = {}
    result: list[TradeDecision] = []

    for decision in trade_decisions:
        symbol = decision.ticker
        qual = qualified_by_symbol.get(symbol)
        structure = execution_structure.get(symbol)
        thesis = thesis_map.get(symbol)

        eq = _classify(symbol, qual, structure, thesis, decision)
        entry_quality_map[symbol] = eq

        if decision.status == ALLOW_TRADE and eq["blocking"]:
            decision = dataclasses.replace(
                decision,
                status=BLOCK_TRADE,
                block_reason=_BLOCK_REASON,
                decision_trace=dict(_BLOCK_TRACE),
                policy_allowed=False,
                policy_reason="entry_quality_gate_blocked",
            )

        result.append(decision)

    return result, entry_quality_map
