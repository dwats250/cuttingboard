"""
Layer 5 — Macro Regime Engine.

Translates validated quotes into a regime state via an 8-input vote model.
No derived metrics are required — only pct_change and price from Layer 3.

Regime states:  RISK_ON | RISK_OFF | TRANSITION | CHAOTIC
Postures:       AGGRESSIVE_LONG | CONTROLLED_LONG | NEUTRAL_PREMIUM
                DEFENSIVE_SHORT | STAY_FLAT

STAY_FLAT and CHAOTIC → NO TRADE.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from cuttingboard import config
from cuttingboard.normalization import NormalizedQuote

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Labels — use these constants, never bare strings
# ---------------------------------------------------------------------------

RISK_ON    = "RISK_ON"
RISK_OFF   = "RISK_OFF"
TRANSITION = "TRANSITION"
CHAOTIC    = "CHAOTIC"

AGGRESSIVE_LONG = "AGGRESSIVE_LONG"
CONTROLLED_LONG = "CONTROLLED_LONG"
NEUTRAL_PREMIUM = "NEUTRAL_PREMIUM"
DEFENSIVE_SHORT = "DEFENSIVE_SHORT"
STAY_FLAT       = "STAY_FLAT"

_VOTE_RISK_ON  = "RISK_ON"
_VOTE_RISK_OFF = "RISK_OFF"
_VOTE_NEUTRAL  = "NEUTRAL"

# Keys used in vote_breakdown — order matches PRD table
_VOTE_KEYS = [
    "SPY pct_change",
    "QQQ pct_change",
    "IWM pct_change",
    "VIX level",
    "VIX pct_change",
    "DXY pct_change",
    "TNX pct_change",
    "BTC pct_change",
]


# ---------------------------------------------------------------------------
# RegimeState
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegimeState:
    regime:         str               # RISK_ON | RISK_OFF | TRANSITION | CHAOTIC
    posture:        str               # AGGRESSIVE_LONG | … | STAY_FLAT
    confidence:     float             # abs(net_score) / total_votes
    net_score:      int               # risk_on_votes − risk_off_votes
    risk_on_votes:  int
    risk_off_votes: int
    neutral_votes:  int
    total_votes:    int               # votes cast (skipped symbols excluded)
    vote_breakdown: dict[str, str]    # key → RISK_ON | RISK_OFF | NEUTRAL
    vix_level:      Optional[float]
    vix_pct_change: Optional[float]
    computed_at_utc: datetime


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_regime(valid_quotes: dict[str, NormalizedQuote]) -> RegimeState:
    """Compute macro regime from validated quotes (Layer 3 output).

    Every input that is absent from valid_quotes is skipped with a warning.
    The confidence formula uses only the votes that were actually cast, so a
    missing optional symbol (e.g. IWM) degrades gracefully without halting.
    """
    spy = valid_quotes.get("SPY")
    qqq = valid_quotes.get("QQQ")
    iwm = valid_quotes.get("IWM")
    vix = valid_quotes.get("^VIX")
    dxy = valid_quotes.get("DX-Y.NYB")
    tnx = valid_quotes.get("^TNX")
    btc = valid_quotes.get("BTC-USD")

    vix_level = vix.price               if vix else None
    vix_pct   = vix.pct_change_decimal  if vix else None

    # 8 votes in PRD order
    raw_votes: list[tuple[str, Optional[str]]] = [
        ("SPY pct_change", _vote_pct_up(spy,  risk_on_gt=0.003,   risk_off_lt=-0.003)),
        ("QQQ pct_change", _vote_pct_up(qqq,  risk_on_gt=0.003,   risk_off_lt=-0.003)),
        ("IWM pct_change", _vote_pct_up(iwm,  risk_on_gt=0.004,   risk_off_lt=-0.004)),
        ("VIX level",      _vote_lvl_low(vix, risk_on_lt=18,       risk_off_gt=25)),
        ("VIX pct_change", _vote_pct_low(vix, risk_on_lt=-0.03,   risk_off_gt=0.05)),
        ("DXY pct_change", _vote_pct_low(dxy, risk_on_lt=-0.002,  risk_off_gt=0.003)),
        ("TNX pct_change", _vote_pct_low(tnx, risk_on_lt=-0.005,  risk_off_gt=0.008)),
        ("BTC pct_change", _vote_pct_up(btc,  risk_on_gt=0.015,   risk_off_lt=-0.020)),
    ]

    vote_breakdown: dict[str, str] = {}
    risk_on_votes = risk_off_votes = neutral_votes = 0

    for key, vote in raw_votes:
        if vote is None:
            logger.warning(f"Regime: '{key}' skipped — symbol not in valid_quotes")
            continue
        vote_breakdown[key] = vote
        if vote == _VOTE_RISK_ON:
            risk_on_votes += 1
        elif vote == _VOTE_RISK_OFF:
            risk_off_votes += 1
        else:
            neutral_votes += 1

    total_votes = risk_on_votes + risk_off_votes + neutral_votes
    net_score   = risk_on_votes - risk_off_votes
    confidence  = abs(net_score) / total_votes if total_votes > 0 else 0.0

    regime  = _classify_regime(net_score, confidence, vix_pct)
    posture = _determine_posture(regime, confidence, vix_level)

    logger.info(
        f"Regime: {regime} | {posture} | confidence={confidence:.2f} "
        f"| net={net_score:+d} (on={risk_on_votes} off={risk_off_votes} neutral={neutral_votes})"
    )

    return RegimeState(
        regime=regime,
        posture=posture,
        confidence=confidence,
        net_score=net_score,
        risk_on_votes=risk_on_votes,
        risk_off_votes=risk_off_votes,
        neutral_votes=neutral_votes,
        total_votes=total_votes,
        vote_breakdown=vote_breakdown,
        vix_level=vix_level,
        vix_pct_change=vix_pct,
        computed_at_utc=datetime.now(timezone.utc),
    )


def from_validation_results(results: list) -> RegimeState:
    """Bridge from validate_all() flat ValidationResult list."""
    valid_quotes = {
        r.symbol: r.quote
        for r in results
        if r.passed and r.quote is not None
    }
    return compute_regime(valid_quotes)


def from_validation_summary(summary) -> RegimeState:
    """Bridge from ValidationSummary (validate_quotes() output)."""
    return compute_regime(summary.valid_quotes)


def print_regime_report(state: RegimeState) -> None:
    """Print full regime state and vote breakdown to terminal."""
    vix_str = f"{state.vix_level:.1f}" if state.vix_level is not None else "N/A"
    vix_pct_str = (
        f"{state.vix_pct_change:+.1%}" if state.vix_pct_change is not None else "N/A"
    )

    print(f"\n{'─' * 52}")
    print(f"  REGIME: {state.regime:<12}  POSTURE: {state.posture}")
    print(f"  Confidence: {state.confidence:.2f}  |  Net score: {state.net_score:+d}")
    print(f"  Votes: {state.risk_on_votes} risk-on  "
          f"{state.risk_off_votes} risk-off  "
          f"{state.neutral_votes} neutral  "
          f"({state.total_votes} cast)")
    print(f"  VIX: {vix_str} ({vix_pct_str})")
    print(f"{'─' * 52}")
    print("  VOTE BREAKDOWN")
    for key in _VOTE_KEYS:
        if key in state.vote_breakdown:
            vote = state.vote_breakdown[key]
            marker = "▲" if vote == _VOTE_RISK_ON else ("▼" if vote == _VOTE_RISK_OFF else "─")
            print(f"    {marker} {key:<20}  {vote}")
        else:
            print(f"    ? {key:<20}  (skipped — symbol unavailable)")
    print(f"{'─' * 52}\n")


# ---------------------------------------------------------------------------
# Vote helpers
# ---------------------------------------------------------------------------

def _vote_pct_up(
    quote: Optional[NormalizedQuote],
    risk_on_gt: float,
    risk_off_lt: float,
) -> Optional[str]:
    """Higher pct_change = risk-on. Used for: SPY, QQQ, IWM, BTC."""
    if quote is None:
        return None
    p = quote.pct_change_decimal
    if p > risk_on_gt:
        return _VOTE_RISK_ON
    if p < risk_off_lt:
        return _VOTE_RISK_OFF
    return _VOTE_NEUTRAL


def _vote_pct_low(
    quote: Optional[NormalizedQuote],
    risk_on_lt: float,
    risk_off_gt: float,
) -> Optional[str]:
    """Lower pct_change = risk-on. Used for: VIX change, DXY, TNX."""
    if quote is None:
        return None
    p = quote.pct_change_decimal
    if p < risk_on_lt:
        return _VOTE_RISK_ON
    if p > risk_off_gt:
        return _VOTE_RISK_OFF
    return _VOTE_NEUTRAL


def _vote_lvl_low(
    quote: Optional[NormalizedQuote],
    risk_on_lt: float,
    risk_off_gt: float,
) -> Optional[str]:
    """Lower price level = risk-on. Used for: VIX level."""
    if quote is None:
        return None
    lvl = quote.price
    if lvl < risk_on_lt:
        return _VOTE_RISK_ON
    if lvl > risk_off_gt:
        return _VOTE_RISK_OFF
    return _VOTE_NEUTRAL


# ---------------------------------------------------------------------------
# Classification and posture
# ---------------------------------------------------------------------------

def _classify_regime(
    net_score: int,
    confidence: float,
    vix_pct: Optional[float],
) -> str:
    # CHAOTIC override: single-interval VIX spike > 15%
    if vix_pct is not None and vix_pct > config.VIX_CHAOTIC_SPIKE:
        return CHAOTIC

    if net_score >= 4 and confidence >= 0.60:
        return RISK_ON
    if net_score >= 2:
        return RISK_ON
    if net_score <= -4 and confidence >= 0.60:
        return RISK_OFF
    if net_score <= -2:
        return RISK_OFF
    return TRANSITION


def _determine_posture(
    regime: str,
    confidence: float,
    vix_level: Optional[float],
) -> str:
    # Global floor: confidence below minimum → always STAY_FLAT
    if regime == CHAOTIC or confidence < config.MIN_REGIME_CONFIDENCE:
        return STAY_FLAT

    if regime == RISK_ON:
        if confidence >= 0.75:
            return AGGRESSIVE_LONG
        if confidence >= 0.55:
            return CONTROLLED_LONG
        return STAY_FLAT  # 0.50 ≤ confidence < 0.55

    if regime == RISK_OFF:
        if confidence >= 0.55:
            return DEFENSIVE_SHORT
        return STAY_FLAT  # 0.50 ≤ confidence < 0.55

    if regime == TRANSITION:
        if vix_level is not None and vix_level > 25:
            return STAY_FLAT         # PRD: TRANSITION with VIX > 25 → STAY_FLAT
        if vix_level is not None and vix_level >= 18:
            return NEUTRAL_PREMIUM   # PRD: TRANSITION with VIX 18–25 → NEUTRAL_PREMIUM
        return STAY_FLAT             # VIX < 18 or unknown during TRANSITION

    return STAY_FLAT
