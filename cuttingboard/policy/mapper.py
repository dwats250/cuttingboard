"""Options mapping for approved trade policy decisions."""

from cuttingboard.policy.models import OptionsExpression, Posture, TradeCandidate, VixRegime
from cuttingboard.policy.rules import debit_spreads_only


def map_options_expression(
    posture: Posture,
    candidate: TradeCandidate,
    vix_regime: VixRegime,
) -> OptionsExpression:
    if posture == "NEUTRAL":
        raise ValueError("NEUTRAL posture cannot be mapped to options")

    spread_type = _spread_type_for(posture, candidate.structure)
    if debit_spreads_only(vix_regime) and spread_type.endswith("credit"):
        raise ValueError(f"spread_type {spread_type} is not allowed in {vix_regime}")

    return OptionsExpression(
        spread_type=spread_type,
        duration="weekly",
        notes=None,
    )


def _spread_type_for(posture: Posture, structure: str) -> str:
    if posture == "LONG_BIAS":
        return "call_debit"
    if posture == "SHORT_BIAS":
        return "put_debit"
    raise ValueError(f"unsupported posture {posture!r} for structure {structure!r}")
