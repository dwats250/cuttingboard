"""
Layer 5 — Macro Regime Engine.

Translates validated quotes into a regime state via an 8-input vote model.
No derived metrics are required — only pct_change and price from Layer 3.

Regime states:  RISK_ON | RISK_OFF | NEUTRAL | CHAOTIC
Postures:       AGGRESSIVE_LONG | CONTROLLED_LONG | NEUTRAL_PREMIUM
                DEFENSIVE_SHORT | STAY_FLAT

NEUTRAL replaces TRANSITION — allows selective trades (R:R ≥ 3:1, defined risk).
CHAOTIC and STAY_FLAT posture → NO TRADE.
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
NEUTRAL    = "NEUTRAL"
TRANSITION = "TRANSITION"   # legacy alias — compute_regime never returns this
CHAOTIC    = "CHAOTIC"
EXPANSION  = "EXPANSION"    # broad risk-on advance with breadth + leadership confirmation

AGGRESSIVE_LONG = "AGGRESSIVE_LONG"
CONTROLLED_LONG = "CONTROLLED_LONG"
NEUTRAL_PREMIUM = "NEUTRAL_PREMIUM"
DEFENSIVE_SHORT = "DEFENSIVE_SHORT"
STAY_FLAT       = "STAY_FLAT"
EXPANSION_LONG  = "EXPANSION_LONG"  # posture when EXPANSION regime is active

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

def detect_expansion_regime(valid_quotes: dict[str, NormalizedQuote]) -> bool:
    """Return True when broad risk-on expansion conditions are all met.

    All four conditions must hold simultaneously:
      1. Index alignment  — SPY and QQQ both positive
      2. VIX confirmation — VIX pct_change <= -1.0%
      3. Breadth          — >= 70% of tradable watchlist symbols advancing
      4. Leadership       — >= 2 of the leadership symbols up >= +1.5%
    """
    spy = valid_quotes.get("SPY")
    qqq = valid_quotes.get("QQQ")
    vix = valid_quotes.get("^VIX")

    # 1. Index alignment
    if spy is None or qqq is None:
        return False
    if spy.pct_change_decimal <= 0 or qqq.pct_change_decimal <= 0:
        return False

    # 2. VIX confirmation — falling volatility
    if vix is None or vix.pct_change_decimal > config.EXPANSION_VIX_PCT_THRESHOLD:
        return False

    # 3. Breadth — advancing over the CONFIGURED tradable universe (PRD-262):
    # a symbol that failed to report did not advance; dividing by survivors
    # would let dropouts raise the ratio and loosen the gate.
    advancing = sum(
        1 for s, q in valid_quotes.items()
        if s not in config.NON_TRADABLE_SYMBOLS and q.pct_change_decimal > 0
    )
    total = sum(1 for s in config.ALL_SYMBOLS if s not in config.NON_TRADABLE_SYMBOLS)
    if total == 0 or (advancing / total) < config.EXPANSION_MIN_BREADTH:
        return False

    # 4. Leadership — at least N symbols from the leadership list up >= +1.5%
    leading = sum(
        1 for s in config.EXPANSION_LEADERSHIP_SYMBOLS
        if s in valid_quotes and valid_quotes[s].pct_change_decimal >= config.EXPANSION_LEADERSHIP_MIN_PCT
    )
    return leading >= config.EXPANSION_LEADERSHIP_MIN_COUNT


def compute_regime(valid_quotes: dict[str, NormalizedQuote]) -> RegimeState:
    """Compute macro regime from validated quotes (Layer 3 output).

    EXPANSION is checked first. If all breadth + leadership conditions are met,
    EXPANSION is returned immediately without running the vote model.

    Every input that is absent from valid_quotes is skipped with a warning.
    Missing votes are scored against the survivors' leader (worst-case
    bounding, PRD-263): net is shrunk toward zero by one per missing vote and
    confidence is |bounded net| / 8, so absent data can only make the verdict
    more cautious, never more permissive.
    """
    vix = valid_quotes.get("^VIX")
    vix_level = vix.price              if vix else None
    vix_pct   = vix.pct_change_decimal if vix else None

    if detect_expansion_regime(valid_quotes):
        logger.info("Regime: EXPANSION | EXPANSION_LONG | breadth + leadership confirmed")
        return RegimeState(
            regime=EXPANSION,
            posture=EXPANSION_LONG,
            confidence=1.0,
            net_score=0,
            risk_on_votes=0,
            risk_off_votes=0,
            neutral_votes=0,
            total_votes=0,
            vote_breakdown={},
            vix_level=vix_level,
            vix_pct_change=vix_pct,
            computed_at_utc=datetime.now(timezone.utc),
        )

    spy = valid_quotes.get("SPY")
    qqq = valid_quotes.get("QQQ")
    iwm = valid_quotes.get("IWM")
    dxy = valid_quotes.get("DX-Y.NYB")
    tnx = valid_quotes.get("^TNX")
    btc = valid_quotes.get("BTC-USD")

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

    # PRD-263 worst-case bounding: each missing vote (only IWM / BTC-USD can
    # silently drop; the other six votes come from HALT_SYMBOLS) is scored as
    # if it voted against the survivors' leader, clamped at zero so bounding
    # never crosses sign. Confidence is over the structural 8-vote
    # denominator; on full coverage this equals |net| / total_votes.
    missing = len(raw_votes) - total_votes
    if net_score > 0:
        bounded_net = max(0, net_score - missing)
    else:
        bounded_net = min(0, net_score + missing)
    confidence = abs(bounded_net) / len(raw_votes)

    regime  = _classify_regime(bounded_net, confidence, vix_pct)
    posture = _determine_posture(regime, confidence, vix_level)

    logger.info(
        f"Regime: {regime} | {posture} | confidence={confidence:.2f} "
        f"| net={net_score:+d} (on={risk_on_votes} off={risk_off_votes} "
        f"neutral={neutral_votes}) | votes={total_votes}/{len(raw_votes)}"
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
    """Bridge from a flat ValidationResult list to a RegimeState."""
    valid_quotes = {
        r.symbol: r.quote
        for r in results
        if r.passed and r.quote is not None
    }
    return compute_regime(valid_quotes)


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
    return NEUTRAL


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

    if regime in (NEUTRAL, TRANSITION):
        if vix_level is not None and vix_level > 25:
            return STAY_FLAT        # elevated VIX in mixed regime → no trade
        if vix_level is not None and vix_level >= 18:
            return NEUTRAL_PREMIUM  # VIX 18–25 → selective defined-risk trades
        return STAY_FLAT            # VIX < 18 during mixed signals → complacency, no trade

    return STAY_FLAT
