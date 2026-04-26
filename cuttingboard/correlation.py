"""
GLD–DXY Correlation Policy Layer (PRD-023).

Computes a deterministic correlation state from existing normalized quote
direction. Output is purely advisory — it modulates risk sizing but does not
alter qualification, signal generation, or trade eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from cuttingboard import config

if TYPE_CHECKING:
    from cuttingboard.normalization import NormalizedQuote

ALIGNED  = "ALIGNED"
NEUTRAL  = "NEUTRAL"
CONFLICT = "CONFLICT"

_VALID_STATES = frozenset({ALIGNED, NEUTRAL, CONFLICT})


@dataclass(frozen=True)
class CorrelationResult:
    gold_symbol:   str
    dollar_symbol: str
    state:         str    # ALIGNED | NEUTRAL | CONFLICT
    score:         int    # +1 | 0 | -1
    risk_modifier: float


def compute_correlation(
    normalized_quotes: "dict[str, NormalizedQuote]",
) -> CorrelationResult:
    """Classify GLD–DXY correlation from current normalized quotes.

    Returns NEUTRAL whenever either symbol is flat, missing, or stale.
    Returns risk_modifier=1.0 when CORRELATION_ENABLED is False.
    """
    gold_sym = config.CORRELATION_GOLD_SYMBOL
    dxy_sym  = config.CORRELATION_DOLLAR_SYMBOL

    if not config.CORRELATION_ENABLED:
        return CorrelationResult(
            gold_symbol=gold_sym,
            dollar_symbol=dxy_sym,
            state=NEUTRAL,
            score=0,
            risk_modifier=1.0,
        )

    gld_dir = _direction(normalized_quotes.get(gold_sym))
    dxy_dir = _direction(normalized_quotes.get(dxy_sym))

    if gld_dir == 0 or dxy_dir == 0:
        state = NEUTRAL
    elif gld_dir == -dxy_dir:
        state = ALIGNED
    else:
        state = CONFLICT

    score = {ALIGNED: 1, NEUTRAL: 0, CONFLICT: -1}[state]
    modifier = {
        ALIGNED:  config.CORRELATION_RISK_MODIFIER_ALIGNED,
        NEUTRAL:  config.CORRELATION_RISK_MODIFIER_NEUTRAL,
        CONFLICT: config.CORRELATION_RISK_MODIFIER_CONFLICT,
    }[state]

    return CorrelationResult(
        gold_symbol=gold_sym,
        dollar_symbol=dxy_sym,
        state=state,
        score=score,
        risk_modifier=modifier,
    )


def _direction(quote: "NormalizedQuote | None") -> int:
    """Return +1, -1, or 0 from a normalized quote.

    Returns 0 (treated as NEUTRAL) when quote is None, stale, or flat.
    Direction is derived from pct_change_decimal, which is equivalent to
    comparing last_close vs previous_close.
    """
    if quote is None:
        return 0
    if quote.age_seconds > config.FRESHNESS_SECONDS:
        return 0
    pct = quote.pct_change_decimal
    if pct > 0:
        return 1
    if pct < 0:
        return -1
    return 0
