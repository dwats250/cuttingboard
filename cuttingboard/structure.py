"""
Layer 6 — Structure Engine.

Classifies per-ticker market structure using EMA alignment, price position,
momentum, and volume from Layer 4 (DerivedMetrics). Requires no regime input.

IV environment is classified from VIX level (Layer 3 / RegimeState.vix_level).

CHOP is automatic disqualification — logged at INFO level, never promoted to output.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from cuttingboard import config
from cuttingboard.derived import DerivedMetrics
from cuttingboard.normalization import NormalizedQuote

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Structure labels
# ---------------------------------------------------------------------------

TREND    = "TREND"
PULLBACK = "PULLBACK"
BREAKOUT = "BREAKOUT"
REVERSAL = "REVERSAL"
CHOP     = "CHOP"

# IV environment labels
LOW_IV      = "LOW_IV"       # VIX < 15
NORMAL_IV   = "NORMAL_IV"    # VIX 15–20
ELEVATED_IV = "ELEVATED_IV"  # VIX 20–28
HIGH_IV     = "HIGH_IV"      # VIX > 28

# Classification thresholds — structure-layer specific, not in config
_BREAKOUT_MOMENTUM_MIN = 0.02    # 5d momentum must exceed this
_BREAKOUT_VOLUME_MIN   = 1.3     # volume_ratio must exceed this (strict >)
_REVERSAL_SPREAD_MAX   = 0.002   # |ema_spread_pct| below → crossover zone
_REVERSAL_MOMENTUM_MIN = 0.003   # abs(momentum) above → directional shift
_TREND_MOMENTUM_MIN    = 0.005   # momentum to confirm active trend


@dataclass(frozen=True)
class StructureResult:
    symbol: str
    structure: str              # TREND | PULLBACK | BREAKOUT | REVERSAL | CHOP
    iv_environment: str         # LOW_IV | NORMAL_IV | ELEVATED_IV | HIGH_IV
    is_tradeable: bool          # False when structure == CHOP
    disqualification_reason: Optional[str]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_all_structure(
    valid_quotes: dict[str, NormalizedQuote],
    derived_metrics: dict[str, DerivedMetrics],
    vix_level: Optional[float] = None,
) -> dict[str, StructureResult]:
    """Classify structure for every symbol in valid_quotes.

    Symbols absent from derived_metrics or with insufficient_history are CHOP.
    CHOP symbols are logged and never promoted to qualification output.
    """
    iv_env = classify_iv_environment(vix_level)
    results: dict[str, StructureResult] = {}

    for symbol, quote in valid_quotes.items():
        dm = derived_metrics.get(symbol)
        result = classify_structure(symbol, quote, dm, iv_env)
        results[symbol] = result

        if not result.is_tradeable:
            logger.info(
                f"CHOP {symbol}: {result.disqualification_reason or 'CHOP structure'}"
            )
        else:
            logger.debug(
                f"STRUCTURE {symbol}: {result.structure}  IV: {result.iv_environment}"
            )

    return results


def classify_structure(
    symbol: str,
    quote: NormalizedQuote,
    dm: Optional[DerivedMetrics],
    iv_environment: Optional[str] = None,
    vix_level: Optional[float] = None,
) -> StructureResult:
    """Classify structure for a single symbol.

    iv_environment takes precedence over vix_level if both are provided.
    """
    if iv_environment is None:
        iv_environment = classify_iv_environment(vix_level)

    structure = _determine_structure(quote.price, dm)
    is_tradeable = structure != CHOP

    disq_reason: Optional[str] = None
    if not is_tradeable:
        if dm is None:
            disq_reason = "no derived metrics available"
        elif not dm.sufficient_history:
            disq_reason = "insufficient OHLCV history"
        elif not dm.ema_aligned_bull and not dm.ema_aligned_bear:
            disq_reason = "EMA not aligned, momentum flat"
        else:
            disq_reason = "price outside tradeable EMA zone"

    return StructureResult(
        symbol=symbol,
        structure=structure,
        iv_environment=iv_environment,
        is_tradeable=is_tradeable,
        disqualification_reason=disq_reason,
    )


def classify_iv_environment(vix_level: Optional[float]) -> str:
    """Map VIX level to IV environment label.

    Returns NORMAL_IV when VIX is unavailable (conservative default).
    """
    if vix_level is None:
        return NORMAL_IV
    if vix_level < config.VIX_LOW:        # < 15
        return LOW_IV
    if vix_level < config.VIX_ELEVATED:   # 15–20
        return NORMAL_IV
    if vix_level <= config.VIX_HIGH:      # 20–28
        return ELEVATED_IV
    return HIGH_IV                         # > 28


# ---------------------------------------------------------------------------
# Core classification logic
# ---------------------------------------------------------------------------

def _determine_structure(price: float, dm: Optional[DerivedMetrics]) -> str:
    """Classify structure from price and derived metrics.

    Classification priority (highest specificity first):
      1. CHOP (no history or no EMA data)
      2. BREAKOUT (strong momentum + volume, before EMA alignment)
      3. REVERSAL (EMA crossover zone — tight spread + momentum)
      4. TREND / PULLBACK (EMA-alignment based)
      5. CHOP (fallthrough — aligned but price outside tradeable zone,
               or not aligned without breakout/reversal conditions)
    """
    if dm is None or not dm.sufficient_history:
        return CHOP

    ema9  = dm.ema9
    ema21 = dm.ema21
    ema50 = dm.ema50

    if ema9 is None or ema21 is None or ema50 is None:
        return CHOP

    momentum  = dm.momentum_5d  if dm.momentum_5d  is not None else 0.0
    vol_ratio = dm.volume_ratio if dm.volume_ratio is not None else 0.0
    spread    = abs(dm.ema_spread_pct) if dm.ema_spread_pct is not None else 0.0

    # --- BREAKOUT ---
    # Strong directional momentum with volume confirmation.
    # Intentionally checked before EMA alignment — a breakout can precede
    # alignment as EMAs catch up to the new price level.
    if (momentum >  _BREAKOUT_MOMENTUM_MIN
            and vol_ratio > _BREAKOUT_VOLUME_MIN
            and price > ema9):
        return BREAKOUT
    if (momentum < -_BREAKOUT_MOMENTUM_MIN
            and vol_ratio > _BREAKOUT_VOLUME_MIN
            and price < ema9):
        return BREAKOUT

    # --- REVERSAL ---
    # Approximates "EMA crossover within last 3 bars": EMAs are in a
    # crossover zone (very tight spread) with directional momentum.
    # Does not require alignment — applies in both aligned and crossing states.
    if spread < _REVERSAL_SPREAD_MAX and abs(momentum) > _REVERSAL_MOMENTUM_MIN:
        return REVERSAL

    # --- TREND / PULLBACK (alignment-based) ---
    if dm.ema_aligned_bull:
        if price >= ema9:
            # Price at or above the fast EMA — trend fully intact
            return TREND
        if price >= ema21:
            # Price pulled back below EMA9 but holding EMA21 support
            return PULLBACK
        # Price below EMA21 while bull-aligned: structure has degraded
        return CHOP

    if dm.ema_aligned_bear:
        if price <= ema9:
            # Price at or below the fast EMA — downtrend fully intact
            return TREND
        if price <= ema21:
            # Bounced above EMA9 but holding below EMA21 resistance
            return PULLBACK
        # Price above EMA21 while bear-aligned: downtrend structure degraded
        return CHOP

    # Not aligned, not BREAKOUT, not REVERSAL → CHOP
    return CHOP
