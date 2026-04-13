"""
Layer 8 — Options Expression Engine.

Maps each qualified trade setup to a specific options spread strategy using
the structure / regime / IV environment matrix. Strike selection is always
relative — never absolute prices.

Entry point: generate_candidates() → TradeCandidate objects for qualify_all()
             build_option_setups()  → OptionSetup objects for output layer

Spread width conventions
------------------------
TradeCandidate.spread_width   = estimated net DEBIT per share (×100 → risk/contract)
OptionSetup.strike_distance   = distance between strikes in underlying price points

Max strike distances: $5.00 for index ETFs (SPY/QQQ/IWM), $2.50 for all others.
Estimated debit = 30% of strike distance (ATM vertical spread approximation).

DTE selection (driven by structure, fine-tuned by |momentum_5d|)
-----------------------------------------------------------------
  BREAKOUT / REVERSAL  → 7 DTE  (fast-move plays)
  PULLBACK             → 14 DTE
  TREND                → 21 DTE
  Strong momentum (|mom| ≥ 0.03) compresses to one tier shorter.

Exit rule: close at +50% of max profit OR full debit loss — every trade.
"""

import logging
import math
from dataclasses import dataclass
from typing import Optional

from cuttingboard import config
from cuttingboard.derived import DerivedMetrics
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.qualification import TradeCandidate, QualificationResult, direction_for_regime
from cuttingboard.regime import RegimeState, NEUTRAL
from cuttingboard.structure import (
    StructureResult,
    TREND, PULLBACK, BREAKOUT, REVERSAL, CHOP,
    LOW_IV, NORMAL_IV, ELEVATED_IV, HIGH_IV,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Strategy labels
# ---------------------------------------------------------------------------

BULL_CALL_SPREAD = "BULL_CALL_SPREAD"
BULL_PUT_SPREAD  = "BULL_PUT_SPREAD"
BEAR_PUT_SPREAD  = "BEAR_PUT_SPREAD"
BEAR_CALL_SPREAD = "BEAR_CALL_SPREAD"

# ---------------------------------------------------------------------------
# Spread constraints
# ---------------------------------------------------------------------------

_INDEX_ETFS          = {"SPY", "QQQ", "IWM"}
_MAX_STRIKE_DIST_ETF  = 5.0     # max strike distance for index ETFs
_MAX_STRIKE_DIST_STK  = 2.50    # max strike distance for individual names
_DEBIT_PCT_OF_WIDTH   = 0.30    # estimated debit = 30% of strike distance
_EXIT_PROFIT_TARGET   = 0.50    # close at 50% of max profit
_EXIT_LOSS            = "full_debit"

# DTE tiers
_DTE_FAST   = 7
_DTE_SHORT  = 14
_DTE_MEDIUM = 21
_DTE_LONG   = 30

_STRONG_MOMENTUM_THRESHOLD = 0.03   # |momentum_5d| above this → compress DTE


# ---------------------------------------------------------------------------
# OptionSetup dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OptionSetup:
    """Fully expressed options trade — ready for output and audit.

    strike_distance is the spread width in underlying price points.
    spread_width    is the estimated net debit per share (for sizing, same
                    value that flows through TradeCandidate → qualification).
    """
    symbol:             str
    strategy:           str           # BULL_CALL_SPREAD | BULL_PUT_SPREAD | etc.
    direction:          str           # LONG | SHORT
    structure:          str           # TREND | PULLBACK | BREAKOUT | REVERSAL
    iv_environment:     str           # LOW_IV | NORMAL_IV | ELEVATED_IV | HIGH_IV
    long_strike:        str           # relative label, e.g. "1_ITM"
    short_strike:       str           # relative label, e.g. "ATM"
    strike_distance:    float         # strike width in underlying $ points
    spread_width:       float         # estimated net debit per share
    dte:                int           # target days to expiry
    max_contracts:      int           # from qualification
    dollar_risk:        float         # from qualification
    exit_profit_pct:    float         # 0.50 = +50% of max profit
    exit_loss:          str           # "full_debit"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_candidates(
    structure_results: dict[str, StructureResult],
    derived_metrics: dict[str, DerivedMetrics],
    valid_quotes: dict[str, NormalizedQuote],
    regime: RegimeState,
) -> dict[str, TradeCandidate]:
    """Generate TradeCandidate objects for every non-CHOP symbol.

    Candidates are built from price + ATR14 for stop/target. Spread width
    is set to the estimated net debit (not strike distance). The qualification
    layer screens these candidates through all 9 gates.

    Returns an empty dict when direction_for_regime is None (no candidates
    for NEUTRAL_PREMIUM / TRANSITION regimes where direction is ambiguous).
    """
    direction = direction_for_regime(regime)
    if direction is None:
        reason = (
            "net_score=0 in NEUTRAL regime — no tiebreaker direction"
            if regime.regime == NEUTRAL
            else "no directional bias"
        )
        logger.info(f"generate_candidates: {reason} — returning empty candidate set")
        return {}

    candidates: dict[str, TradeCandidate] = {}

    for symbol, sr in structure_results.items():
        if sr.structure == CHOP:
            continue

        quote = valid_quotes.get(symbol)
        if quote is None:
            continue

        dm = derived_metrics.get(symbol)
        candidate = _build_candidate(symbol, direction, quote, dm)
        if candidate is not None:
            candidates[symbol] = candidate
            logger.debug(
                f"Candidate {symbol}: {direction} entry={candidate.entry_price:.2f} "
                f"stop={candidate.stop_price:.2f} target={candidate.target_price:.2f} "
                f"spread_width={candidate.spread_width:.2f}"
            )

    return candidates


def build_option_setups(
    qualified_trades: list[QualificationResult],
    structure_results: dict[str, StructureResult],
    derived_metrics: dict[str, DerivedMetrics],
) -> list["OptionSetup"]:
    """Map each qualified trade to a fully expressed OptionSetup.

    Uses the structure/IV matrix to select strategy type, then computes
    DTE from structure + momentum and formats relative strike labels.
    """
    setups: list[OptionSetup] = []

    for result in qualified_trades:
        symbol = result.symbol
        sr = structure_results.get(symbol)
        if sr is None:
            logger.warning(f"build_option_setups: no StructureResult for {symbol} — skipped")
            continue

        dm = derived_metrics.get(symbol)
        strategy = _select_strategy(result.direction, sr.iv_environment)
        dte = _select_dte(sr.structure, dm)
        strike_distance = (
            _MAX_STRIKE_DIST_ETF if symbol in _INDEX_ETFS else _MAX_STRIKE_DIST_STK
        )
        spread_width = _estimated_debit(strike_distance)
        long_strike, short_strike = _format_strikes(strategy, strike_distance)

        if result.max_contracts is None or result.dollar_risk is None:
            logger.warning(f"build_option_setups: {symbol} missing sizing — skipped")
            continue

        setup = OptionSetup(
            symbol=symbol,
            strategy=strategy,
            direction=result.direction,
            structure=sr.structure,
            iv_environment=sr.iv_environment,
            long_strike=long_strike,
            short_strike=short_strike,
            strike_distance=strike_distance,
            spread_width=spread_width,
            dte=dte,
            max_contracts=result.max_contracts,
            dollar_risk=result.dollar_risk,
            exit_profit_pct=_EXIT_PROFIT_TARGET,
            exit_loss=_EXIT_LOSS,
        )
        setups.append(setup)
        logger.info(
            f"OPTION_SETUP {symbol}: {strategy}  {long_strike}/{short_strike}  "
            f"{dte} DTE  {result.max_contracts}c  ${result.dollar_risk:.0f}"
        )

    return setups


# ---------------------------------------------------------------------------
# Strategy selection matrix
# ---------------------------------------------------------------------------

def _select_strategy(direction: str, iv_environment: str) -> str:
    """Select spread strategy from direction × IV environment.

    Debit spreads are preferred in low/normal IV (cheaper to buy).
    Credit spreads are preferred in elevated/high IV (collect more premium).

    LONG  + LOW_IV / NORMAL_IV   → BULL_CALL_SPREAD  (debit)
    LONG  + ELEVATED_IV / HIGH_IV → BULL_PUT_SPREAD  (credit)
    SHORT + LOW_IV / NORMAL_IV   → BEAR_PUT_SPREAD   (debit)
    SHORT + ELEVATED_IV / HIGH_IV → BEAR_CALL_SPREAD (credit)
    """
    high_iv = iv_environment in (ELEVATED_IV, HIGH_IV)

    if direction == "LONG":
        return BULL_PUT_SPREAD if high_iv else BULL_CALL_SPREAD
    else:
        return BEAR_CALL_SPREAD if high_iv else BEAR_PUT_SPREAD


# ---------------------------------------------------------------------------
# DTE selection
# ---------------------------------------------------------------------------

def _select_dte(structure: str, dm: Optional[DerivedMetrics]) -> int:
    """Select target DTE from structure type and momentum strength.

    Base DTE by structure:
      BREAKOUT / REVERSAL → 7   (fast-move, time-compressed)
      PULLBACK            → 14  (expecting bounce within 2 weeks)
      TREND               → 21  (sustained move, give room)

    Strong momentum (|momentum_5d| ≥ 0.03) compresses one tier.
    """
    momentum = (
        abs(dm.momentum_5d)
        if dm is not None and dm.momentum_5d is not None
        else 0.0
    )
    strong = momentum >= _STRONG_MOMENTUM_THRESHOLD

    if structure in (BREAKOUT, REVERSAL):
        return _DTE_FAST  # already minimum — momentum doesn't compress further

    if structure == PULLBACK:
        return _DTE_FAST if strong else _DTE_SHORT

    if structure == TREND:
        return _DTE_SHORT if strong else _DTE_MEDIUM

    # Fallback (should not reach here — CHOP excluded by caller)
    return _DTE_MEDIUM


# ---------------------------------------------------------------------------
# Strike formatting
# ---------------------------------------------------------------------------

def _format_strikes(strategy: str, strike_distance: float) -> tuple[str, str]:
    """Return (long_strike_label, short_strike_label) for the spread.

    Labels are relative — never absolute prices.

    BULL_CALL_SPREAD : buy 1_ITM call  /  sell ATM call       (debit)
    BULL_PUT_SPREAD  : buy ATM-{w} put /  sell ATM put         (credit)
    BEAR_PUT_SPREAD  : buy 1_ITM put   /  sell ATM put         (debit)
    BEAR_CALL_SPREAD : buy ATM+{w} call / sell ATM call        (credit)
    """
    w = f"{strike_distance:.2f}"

    if strategy == BULL_CALL_SPREAD:
        return "1_ITM", "ATM"
    if strategy == BULL_PUT_SPREAD:
        return f"ATM-{w}", "ATM"
    if strategy == BEAR_PUT_SPREAD:
        return "1_ITM", "ATM"
    if strategy == BEAR_CALL_SPREAD:
        return "ATM", f"ATM+{w}"

    return "ATM", "ATM"   # unreachable


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_candidate(
    symbol: str,
    direction: str,
    quote: NormalizedQuote,
    dm: Optional[DerivedMetrics],
) -> Optional[TradeCandidate]:
    """Build a TradeCandidate from current price and ATR-based stop/target.

    Stop:   1 × ATR14 away from entry (2% fallback if no ATR)
    Target: 2 × stop_distance from entry (ensures RR ≥ 2.0)
    Spread: estimated debit for a max-width spread on this symbol
    """
    entry = quote.price

    if dm is not None and dm.atr14 is not None and dm.atr14 > 0:
        risk_distance = dm.atr14
    else:
        risk_distance = entry * 0.02   # 2% default

    if direction == "LONG":
        stop   = entry - risk_distance
        target = entry + 2.0 * risk_distance
    else:
        stop   = entry + risk_distance
        target = entry - 2.0 * risk_distance

    # Validate stop is sensible (must be > 0)
    if stop <= 0:
        logger.warning(f"{symbol}: computed stop {stop:.4f} ≤ 0 — candidate skipped")
        return None

    strike_distance = _MAX_STRIKE_DIST_ETF if symbol in _INDEX_ETFS else _MAX_STRIKE_DIST_STK
    spread_width = _estimated_debit(strike_distance)

    return TradeCandidate(
        symbol=symbol,
        direction=direction,
        entry_price=entry,
        stop_price=stop,
        target_price=target,
        spread_width=spread_width,
        has_earnings_soon=None,   # unknown — fail-open per PRD
    )


def _estimated_debit(strike_distance: float) -> float:
    """Estimate net debit as 30% of strike distance.

    This is the value passed into TradeCandidate.spread_width and used
    by gate 8 to compute max_contracts and dollar_risk.

    ETF  ($5.00 strike dist): debit ≈ $1.50  → 1 contract  → $150 risk
    Stock ($2.50 strike dist): debit ≈ $0.75  → 2 contracts → $150 risk
    """
    return round(strike_distance * _DEBIT_PCT_OF_WIDTH, 4)
