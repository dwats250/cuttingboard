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
from dataclasses import dataclass, replace
from typing import Optional

from cuttingboard import config
from cuttingboard.derived import DerivedMetrics
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.qualification import (
    ENTRY_MODE_PULLBACK_IMBALANCE,
    ENTRY_MODE_CONTINUATION,
    TradeCandidate,
    QualificationResult,
    direction_for_regime,
)
from cuttingboard.regime import RegimeState, NEUTRAL
from cuttingboard.structure import (
    StructureResult,
    TREND, PULLBACK, BREAKOUT, REVERSAL, CHOP,
    ELEVATED_IV, HIGH_IV,
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
    layer screens these candidates through all 11 gates.

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
        candidate = _build_candidate(symbol, direction, quote, dm, sr.iv_environment)
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
    candidates: Optional[dict[str, TradeCandidate]] = None,
    *,
    risk_modifier: float = 1.0,
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
        candidate = (candidates or {}).get(symbol)
        if (
            result.entry_mode == ENTRY_MODE_PULLBACK_IMBALANCE
            and result.imbalance_zone is not None
            and candidate is not None
        ):
            midpoint = (
                result.imbalance_zone.upper_bound + result.imbalance_zone.lower_bound
            ) / 2.0
            stop_price = (
                result.imbalance_zone.lower_bound
                if result.direction == "LONG"
                else result.imbalance_zone.upper_bound
            )
            candidate = replace(candidate, entry_price=midpoint, stop_price=stop_price)
            logger.info(
                "build_option_setups: %s using imbalance pullback entry=%.2f stop=%.2f",
                symbol,
                candidate.entry_price,
                candidate.stop_price,
            )
        strike_distance = (
            _MAX_STRIKE_DIST_ETF if symbol in _INDEX_ETFS else _MAX_STRIKE_DIST_STK
        )
        spread_width = candidate.spread_width if candidate is not None else _estimated_debit(strike_distance)
        long_strike, short_strike = _format_strikes(strategy, strike_distance)

        if result.max_contracts is None or result.dollar_risk is None:
            logger.warning(f"build_option_setups: {symbol} missing sizing — skipped")
            continue

        # Apply correlation risk_modifier: reduce effective risk budget and
        # recompute max contracts. Never go below 1 contract (AC4: no removal).
        # PRD-157: equity-driven sizing. effective_risk = account equity ×
        # per-trade risk pct × correlation modifier. (Note: risk_modifier here
        # is the correlation modifier, distinct from qualification.py's
        # risk_multiplier which is regime-based.)
        effective_risk = (
            config.ACCOUNT_EQUITY * config.MAX_RISK_PCT_PER_TRADE * risk_modifier
        )
        # PRD-251: size off the strategy-aware max loss when this result came
        # from the standard Gate-8 path AND its TradeCandidate resolved one.
        # Continuation-path results (entry_mode == ENTRY_MODE_CONTINUATION)
        # NEVER use a candidate's max_loss, even when `candidates` happens to
        # hold a direct TradeCandidate for the same symbol -- EXPANSION regime
        # runs generate_candidates() (direction_for_regime(EXPANSION)="LONG")
        # AND the continuation qualifier side by side, so a symbol that fails
        # direct qualification but passes continuation qualification can have
        # a direct candidate sitting in the dict that has nothing to do with
        # the continuation result being rendered here. Using it would re-price
        # a path R4 declares untouched off the wrong candidate's economics --
        # exactly the R3 divergence this PRD exists to remove, in the one path
        # it must not touch. Fall back to spread_width unchanged (pre-PRD
        # behavior, verbatim) for continuation results and for any result with
        # no resolved candidate.
        effective_max_loss = (
            candidate.max_loss
            if (
                candidate is not None
                and candidate.max_loss is not None
                and result.entry_mode != ENTRY_MODE_CONTINUATION
            )
            else spread_width
        )
        risk_per_contract = effective_max_loss * 100
        if risk_per_contract > 0:
            raw_adjusted = int(effective_risk // risk_per_contract)
            final_contracts = max(1, min(result.max_contracts, raw_adjusted))
        else:
            final_contracts = result.max_contracts
        final_dollar_risk = round(float(final_contracts) * risk_per_contract, 2)

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
            max_contracts=final_contracts,
            dollar_risk=final_dollar_risk,
            exit_profit_pct=_EXIT_PROFIT_TARGET,
            exit_loss=_EXIT_LOSS,
        )
        setups.append(setup)
        logger.info(
            f"OPTION_SETUP {symbol}: {strategy}  {long_strike}/{short_strike}  "
            f"{dte} DTE  {result.max_contracts}c  ${result.dollar_risk:.0f}  "
            f"mode={result.entry_mode}"
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
    iv_environment: str,
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
    strategy = _select_strategy(direction, iv_environment)
    max_loss = _max_loss_for_strategy(strategy, strike_distance)

    return TradeCandidate(
        symbol=symbol,
        direction=direction,
        entry_price=entry,
        stop_price=stop,
        target_price=target,
        spread_width=spread_width,
        has_earnings_soon=None,   # unknown — fail-open per PRD
        max_loss=max_loss,
    )


def _estimated_debit(strike_distance: float) -> float:
    """Estimate net debit as 30% of strike distance.

    This is the value passed into TradeCandidate.spread_width, unchanged
    in meaning by PRD-251 (still "estimated net debit per share").

    ETF  ($5.00 strike dist): debit ≈ $1.50  → 1 contract  → $150 risk
    Stock ($2.50 strike dist): debit ≈ $0.75  → 2 contracts → $150 risk
    """
    return round(strike_distance * _DEBIT_PCT_OF_WIDTH, 4)


def _max_loss_for_strategy(strategy: str, strike_distance: float) -> float:
    """Strategy-aware max loss per share, used by Gate 8 and the final resize.

    PRD-251: for credit strategies (BULL_PUT_SPREAD, BEAR_CALL_SPREAD) the
    estimated credit collected (30% of width, the same proxy as
    _estimated_debit) is NOT the max loss — the max loss is width minus
    that credit, i.e. 70% of width. Debit strategies (BULL_CALL_SPREAD,
    BEAR_PUT_SPREAD) are unaffected: max loss IS the debit paid.
    """
    debit_proxy = _estimated_debit(strike_distance)
    if strategy in (BULL_PUT_SPREAD, BEAR_CALL_SPREAD):
        return round(strike_distance - debit_proxy, 4)
    return debit_proxy
