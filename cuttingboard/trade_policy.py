"""
Trade Policy Layer (PRD-023).

Translates a CorrelationResult into a PolicyContext that downstream
sizing can consume. This is the only layer allowed to apply correlation
output to trade behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass

from cuttingboard.correlation import CorrelationResult, ALIGNED, NEUTRAL, CONFLICT


@dataclass(frozen=True)
class PolicyContext:
    risk_modifier: float
    policy_note:   str


_NOTES = {
    ALIGNED:  "correlation_aligned",
    NEUTRAL:  "correlation_neutral",
    CONFLICT: "correlation_conflict",
}


def evaluate_policy(correlation: CorrelationResult) -> PolicyContext:
    """Return a PolicyContext from a CorrelationResult.

    risk_modifier is passed directly into options sizing.
    policy_note is informational only — never drives gate logic.
    """
    return PolicyContext(
        risk_modifier=correlation.risk_modifier,
        policy_note=_NOTES[correlation.state],
    )
