"""
Layer 7 — Trade Qualification.

All 9 gates must pass for a trade to qualify. No partial credit. No exceptions.

Gates 1–4 are HARD stops: failure → REJECT with no watchlist eligibility.
Gates 5–9 are SOFT stops: exactly one miss → WATCHLIST with reason stated.
                           Two or more misses → REJECT.

Earnings gate (9) is fail-open: None = unknown → gate passes.

Entry point: qualify_all(regime, structure_results, candidates, derived_metrics)
Short-circuit: STAY_FLAT / CHAOTIC posture halts before any per-symbol work.
"""

import logging
import math
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional

import pandas as pd

from cuttingboard import config, time_utils
from cuttingboard.derived import DerivedMetrics
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.regime import (
    RegimeState,
    RISK_ON, RISK_OFF, TRANSITION, CHAOTIC, NEUTRAL, EXPANSION,
    STAY_FLAT,
)
from cuttingboard.structure import StructureResult, CHOP, TREND

logger = logging.getLogger(__name__)

ENTRY_MODE_DIRECT = "DIRECT"
ENTRY_MODE_PULLBACK_IMBALANCE = "PULLBACK_IMBALANCE"
ENTRY_MODE_CONTINUATION = "CONTINUATION"

# Gate name constants — used in gates_passed / gates_failed lists
GATE_REGIME      = "REGIME"
GATE_CONFIDENCE  = "CONFIDENCE"
GATE_DIRECTION   = "DIRECTION"
GATE_STRUCTURE   = "STRUCTURE"
GATE_STOP_DEF    = "STOP_DEFINED"
GATE_STOP_DIST   = "STOP_DISTANCE"
GATE_RR          = "RR_RATIO"
GATE_MAX_RISK    = "MAX_RISK"
GATE_EARNINGS    = "EARNINGS"
GATE_EXTENSION   = "EXTENSION"
GATE_TIME        = "TIME"

HARD_GATES = {GATE_REGIME, GATE_CONFIDENCE, GATE_DIRECTION, GATE_STRUCTURE}
SOFT_GATES = {GATE_STOP_DEF, GATE_STOP_DIST, GATE_RR, GATE_MAX_RISK, GATE_EARNINGS,
              GATE_EXTENSION, GATE_TIME}

CONTINUATION_REJECTION_REASONS = (
    "DATA_INCOMPLETE",
    "VIX_BLOCKED",
    "NO_BREAKOUT",
    "NO_HOLD_CONFIRMATION",
    "INSUFFICIENT_MOMENTUM",
    "EXTENDED_FROM_MEAN",
    "STOP_TOO_TIGHT",
    "RR_BELOW_THRESHOLD",
    "TIME_BLOCKED",
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TradeCandidate:
    """Trade parameters needed to run all 9 qualification gates.

    Supplied by the options layer (Phase 5). For Phase 4 testing, pass
    candidates=None to qualify_all — gates 1–4 still execute.
    """
    symbol: str
    direction: str              # "LONG" | "SHORT"
    entry_price: float
    stop_price: float
    target_price: float
    spread_width: float         # spread width in dollars (for sizing)
    has_earnings_soon: Optional[bool] = None  # None = unknown → fail-open


@dataclass(frozen=True)
class QualificationResult:
    symbol: str
    qualified: bool
    watchlist: bool             # exactly one soft gate missed
    direction: str
    gates_passed: list[str]
    gates_failed: list[str]
    hard_failure: Optional[str]      # set when any hard gate (1–4) fails
    watchlist_reason: Optional[str]  # the one missed soft gate description
    max_contracts: Optional[int]     # floor(150 / spread_width×100)
    dollar_risk: Optional[float]     # max_contracts × spread_width × 100
    entry_mode: str = ENTRY_MODE_DIRECT
    imbalance_zone: Optional["FVGZone"] = None
    rejection_reason: Optional[str] = None


@dataclass(frozen=True)
class FVGZone:
    upper_bound: float
    lower_bound: float


@dataclass(frozen=True)
class QualificationSummary:
    regime_passed: bool
    regime_short_circuited: bool     # True when gates 1–2 halt before per-symbol
    regime_failure_reason: Optional[str]
    qualified_trades: list[QualificationResult]
    watchlist: list[QualificationResult]
    excluded: dict[str, str]         # symbol → reason (CHOP, direction, etc.)
    symbols_evaluated: int
    symbols_qualified: int
    symbols_watchlist: int
    symbols_excluded: int
    continuation_audit: Optional[dict[str, int]] = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def qualify_all(
    regime: RegimeState,
    structure_results: dict[str, StructureResult],
    candidates: Optional[dict[str, "TradeCandidate"]] = None,
    derived_metrics: Optional[dict[str, DerivedMetrics]] = None,
    ohlcv: Optional[dict[str, pd.DataFrame]] = None,
    now_et: Optional[datetime] = None,
) -> QualificationSummary:
    """Run all qualification gates for all symbols.

    Regime gates (1–2) are checked first. On failure the function returns
    immediately — no per-symbol work runs. This is the STAY_FLAT short-circuit.

    When candidates is None (Phase 4), gates 5–9 are skipped. CHOP symbols
    are still detected and logged (gate 4).
    """
    # --- Gates 1–2: Regime check (system-level, before any per-symbol work) ---
    regime_fail = _check_regime_gates(regime)
    if regime_fail:
        logger.info(f"Qualification short-circuited — {regime_fail}")
        return QualificationSummary(
            regime_passed=False,
            regime_short_circuited=True,
            regime_failure_reason=regime_fail,
            qualified_trades=[],
            watchlist=[],
            excluded={},
            symbols_evaluated=0,
            symbols_qualified=0,
            symbols_watchlist=0,
            symbols_excluded=0,
            continuation_audit=None,
        )

    # --- Per-symbol evaluation ---
    excluded: dict[str, str] = {}
    qualified: list[QualificationResult] = []
    watchlist_trades: list[QualificationResult] = []
    expected_direction = direction_for_regime(regime)
    continuation_rejections: list[QualificationResult] = []

    for symbol, sr in structure_results.items():
        # Gate 4: CHOP — hard stop, no watchlist
        if sr.structure == CHOP:
            excluded[symbol] = "CHOP"
            logger.info(f"REJECTED {symbol}: CHOP — never qualifies")
            continue

        # Gate 3: direction alignment — check without a candidate
        if expected_direction is not None and candidates is not None:
            candidate = candidates.get(symbol)
            if candidate is None:
                # Structure is fine but no trade parameters provided for this symbol
                continue
            if candidate.direction != expected_direction:
                excluded[symbol] = (
                    f"direction mismatch: {candidate.direction} "
                    f"vs regime {expected_direction}"
                )
                logger.info(f"REJECTED {symbol}: direction mismatch")
                continue

            dm = (derived_metrics or {}).get(symbol)
            result = qualify_candidate(candidate, regime, sr, dm, now_et)
            result = _resolve_entry_mode(result, candidate, regime, dm, (ohlcv or {}).get(symbol))

            if result.qualified:
                qualified.append(result)
                logger.info(
                    f"QUALIFIED {symbol}: {result.direction} | "
                    f"{sr.structure} | mode={result.entry_mode} | "
                    f"contracts={result.max_contracts} risk=${result.dollar_risk:.0f}"
                )
            elif result.watchlist:
                watchlist_trades.append(result)
                logger.info(
                    f"WATCHLIST {symbol}: missing — {result.watchlist_reason}"
                )
            else:
                excluded[symbol] = result.hard_failure or "failed qualification"
                logger.info(f"REJECTED {symbol}: {excluded[symbol]}")

    # --- Continuation path (EXPANSION regime only) ---
    if regime.regime == EXPANSION:
        qualified_syms = {r.symbol for r in qualified}
        watchlist_syms = {r.symbol for r in watchlist_trades}

        for symbol, sr in structure_results.items():
            if symbol in qualified_syms or symbol in watchlist_syms:
                continue
            if sr.structure == CHOP:
                continue
            dm = (derived_metrics or {}).get(symbol)
            df = (ohlcv or {}).get(symbol)
            cont = _qualify_continuation_candidate(symbol, df, sr, regime, dm, now_et)
            if cont.qualified:
                qualified.append(cont)
                qualified_syms.add(symbol)
                logger.info(
                    f"EXPANSION QUALIFIED {symbol}: CONTINUATION | "
                    f"contracts={cont.max_contracts} risk=${cont.dollar_risk:.0f}"
                )
            elif cont.watchlist:
                watchlist_trades.append(cont)
                watchlist_syms.add(symbol)
                logger.info(f"EXPANSION WATCHLIST {symbol}: {cont.watchlist_reason}")
            else:
                continuation_rejections.append(cont)
                logger.info(
                    "EXPANSION REJECTED %s: CONTINUATION | %s",
                    symbol,
                    cont.rejection_reason or "UNKNOWN",
                )

    continuation_audit = _build_continuation_audit(
        regime,
        qualified,
        watchlist_trades,
        continuation_rejections,
    )

    return QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=qualified,
        watchlist=watchlist_trades,
        excluded=excluded,
        symbols_evaluated=len(structure_results),
        symbols_qualified=len(qualified),
        symbols_watchlist=len(watchlist_trades),
        symbols_excluded=len(excluded),
        continuation_audit=continuation_audit,
    )


def qualify_candidate(
    candidate: TradeCandidate,
    regime: RegimeState,
    structure: StructureResult,
    dm: Optional[DerivedMetrics] = None,
    now_et: Optional[datetime] = None,
) -> QualificationResult:
    """Run all 9 gates for a single trade candidate.

    Returns a QualificationResult indicating qualified / watchlist / rejected.
    Gates 1–4 short-circuit on first failure (no watchlist).
    """
    gates_passed: list[str] = []
    soft_failures: list[tuple[str, str]] = []  # (gate_name, reason)

    # -----------------------------------------------------------------------
    # Hard gates 1–4
    # -----------------------------------------------------------------------

    # Gate 1: Regime posture — STAY_FLAT and CHAOTIC are no-trade states
    if regime.posture == STAY_FLAT:
        return _hard_reject(
            candidate,
            GATE_REGIME,
            f"posture is STAY_FLAT (regime={regime.regime})",
            gates_passed,
        )
    gates_passed.append(GATE_REGIME)

    # Gate 2: Confidence
    if regime.confidence < config.MIN_REGIME_CONFIDENCE:
        return _hard_reject(
            candidate,
            GATE_CONFIDENCE,
            f"confidence {regime.confidence:.2f} < {config.MIN_REGIME_CONFIDENCE} minimum",
            gates_passed,
        )
    gates_passed.append(GATE_CONFIDENCE)

    # Gate 3: Direction matches regime
    expected = direction_for_regime(regime)
    if expected is not None and candidate.direction != expected:
        return _hard_reject(
            candidate,
            GATE_DIRECTION,
            f"{candidate.direction} direction incompatible with {regime.regime} regime",
            gates_passed,
        )
    gates_passed.append(GATE_DIRECTION)

    # Gate 4: Structure not CHOP
    if structure.structure == CHOP:
        return _hard_reject(
            candidate,
            GATE_STRUCTURE,
            "CHOP structure — automatic disqualification",
            gates_passed,
        )
    gates_passed.append(GATE_STRUCTURE)

    # -----------------------------------------------------------------------
    # Soft gates 5–9
    # -----------------------------------------------------------------------

    risk   = abs(candidate.entry_price - candidate.stop_price)
    reward = abs(candidate.target_price - candidate.entry_price)

    # Gate 5: Stop defined (stop_price > 0 and distance > 0)
    if candidate.stop_price <= 0 or risk == 0:
        soft_failures.append((GATE_STOP_DEF, "stop price not defined or equals entry"))
    else:
        gates_passed.append(GATE_STOP_DEF)

    # Gate 6: Stop distance ≥ 1% of price AND ≥ 0.5 × ATR14
    if risk > 0 and candidate.entry_price > 0:
        stop_pct = risk / candidate.entry_price
        atr_half = (dm.atr14 * 0.5) if (dm is not None and dm.atr14 is not None) else None

        if stop_pct < 0.01:
            soft_failures.append((
                GATE_STOP_DIST,
                f"stop distance {stop_pct:.1%} below 1.0% minimum",
            ))
        elif atr_half is not None and risk < atr_half:
            soft_failures.append((
                GATE_STOP_DIST,
                f"stop distance {risk:.2f} below 0.5× ATR14 ({atr_half:.2f})",
            ))
        else:
            gates_passed.append(GATE_STOP_DIST)
    else:
        soft_failures.append((GATE_STOP_DIST, "entry or stop undefined — cannot compute"))

    # Gate 7: R:R minimum — stricter in NEUTRAL, relaxed in EXPANSION
    if regime.regime == NEUTRAL:
        min_rr = config.NEUTRAL_RR_RATIO
    elif regime.regime == EXPANSION:
        min_rr = config.EXPANSION_RR_RATIO
    else:
        min_rr = config.MIN_RR_RATIO
    if risk > 0:
        rr = reward / risk
        if rr < min_rr:
            soft_failures.append((
                GATE_RR,
                f"R:R {rr:.2f} below {min_rr:.1f} minimum"
                + (" (NEUTRAL stricter gate)" if regime.regime == NEUTRAL else ""),
            ))
        else:
            gates_passed.append(GATE_RR)
    else:
        soft_failures.append((GATE_RR, "risk is zero — cannot compute R:R"))

    # Gate 8: Fits within risk budget — scaled by regime multiplier
    risk_multiplier = config.REGIME_RISK_MULTIPLIER.get(regime.regime, 1.0)
    effective_target = config.TARGET_DOLLAR_RISK * risk_multiplier
    spread_cost = candidate.spread_width * 100  # 1 contract = 100 multiplier
    max_contracts: Optional[int] = None
    dollar_risk: Optional[float] = None

    if spread_cost > 0 and effective_target > 0:
        max_c = math.floor(effective_target / spread_cost)
        if max_c < 1:
            soft_failures.append((
                GATE_MAX_RISK,
                f"1 contract at ${candidate.spread_width:.2f} "
                f"width = ${spread_cost:.0f} — exceeds budget "
                f"(${effective_target:.0f} after {regime.regime} multiplier)",
            ))
        else:
            dr = max_c * spread_cost
            max_contracts = max_c
            dollar_risk = dr
            gates_passed.append(GATE_MAX_RISK)
    elif spread_cost > 0 and effective_target == 0:
        soft_failures.append((GATE_MAX_RISK, f"zero risk budget for {regime.regime} regime"))
    else:
        soft_failures.append((GATE_MAX_RISK, "spread width undefined"))

    # Gate 9: No earnings within 5 calendar days (fail-open when unknown)
    if candidate.has_earnings_soon is True:
        soft_failures.append((GATE_EARNINGS, "earnings within 5 calendar days"))
    else:
        # None = unknown → pass (fail-open per PRD)
        gates_passed.append(GATE_EARNINGS)

    # Gate 10: Not extended — price within EXTENSION_ATR_MULTIPLIER × ATR14 of EMA21
    if dm is not None and dm.ema21 is not None and dm.atr14 is not None and dm.atr14 > 0:
        extension = abs(candidate.entry_price - dm.ema21) / dm.atr14
        if extension > config.EXTENSION_ATR_MULTIPLIER:
            soft_failures.append((
                GATE_EXTENSION,
                f"price {extension:.1f}× ATR from EMA21 "
                f"(max {config.EXTENSION_ATR_MULTIPLIER}×) — entry extended",
            ))
        else:
            gates_passed.append(GATE_EXTENSION)
    else:
        gates_passed.append(GATE_EXTENSION)  # fail-open when metrics unavailable

    # Gate 11: Not late session — no new entries after 3:30 PM ET
    if _is_late_session(now_et):
        soft_failures.append((GATE_TIME, "entry blocked after 3:30 PM ET"))
    else:
        gates_passed.append(GATE_TIME)

    # -----------------------------------------------------------------------
    # Outcome
    # -----------------------------------------------------------------------

    gate_names_failed = [g for g, _ in soft_failures]

    if not soft_failures:
        return QualificationResult(
            symbol=candidate.symbol,
            qualified=True,
            watchlist=False,
            direction=candidate.direction,
            gates_passed=gates_passed,
            gates_failed=gate_names_failed,
            hard_failure=None,
            watchlist_reason=None,
            max_contracts=max_contracts,
            dollar_risk=dollar_risk,
        )

    if len(soft_failures) == 1:
        _, reason = soft_failures[0]
        return QualificationResult(
            symbol=candidate.symbol,
            qualified=False,
            watchlist=True,
            direction=candidate.direction,
            gates_passed=gates_passed,
            gates_failed=gate_names_failed,
            hard_failure=None,
            watchlist_reason=reason,
            max_contracts=max_contracts,
            dollar_risk=dollar_risk,
        )

    # Two or more soft gate failures → REJECT
    reasons = "; ".join(r for _, r in soft_failures)
    return QualificationResult(
        symbol=candidate.symbol,
        qualified=False,
        watchlist=False,
        direction=candidate.direction,
        gates_passed=gates_passed,
        gates_failed=gate_names_failed,
        hard_failure=f"{len(soft_failures)} soft gates failed: {reasons}",
        watchlist_reason=None,
        max_contracts=max_contracts,
        dollar_risk=dollar_risk,
    )


def detect_fvg(
    df: pd.DataFrame,
    direction: str,
    atr14: Optional[float],
) -> Optional[FVGZone]:
    """Return the most recent valid, non-invalidated FVG within the lookback window."""
    if atr14 is None or atr14 <= 0:
        return None
    if direction not in {"LONG", "SHORT"}:
        return None
    if len(df) < 3:
        return None

    window = df.iloc[-(config.FVG_LOOKBACK_CANDLES + 2):]
    if len(window) < 3:
        return None

    for i in range(len(window) - 1, 1, -1):
        candle1 = window.iloc[i - 2]
        candle2 = window.iloc[i - 1]
        candle3 = window.iloc[i]

        if direction == "LONG":
            has_gap = float(candle1["High"]) < float(candle3["Low"])
            lower_bound = float(candle1["High"])
            upper_bound = float(candle3["Low"])
        else:
            has_gap = float(candle1["Low"]) > float(candle3["High"])
            upper_bound = float(candle1["Low"])
            lower_bound = float(candle3["High"])

        if not has_gap:
            continue
        if not _is_displacement_candle(candle2, direction, atr14):
            continue

        gap_size = upper_bound - lower_bound
        if gap_size < (config.FVG_GAP_K * atr14):
            continue

        closes_after = window.iloc[i + 1:]["Close"].astype(float)
        if direction == "LONG" and (closes_after < lower_bound).any():
            continue
        if direction == "SHORT" and (closes_after > upper_bound).any():
            continue

        return FVGZone(upper_bound=upper_bound, lower_bound=lower_bound)

    return None


def direction_for_regime(regime: RegimeState) -> Optional[str]:
    """Return expected trade direction for the current regime.

    NEUTRAL: net_score breaks the tie (+1 → LONG, -1 → SHORT, 0 → None).
    EXPANSION: always LONG (momentum/continuation bias).
    CHAOTIC and TRANSITION (legacy): no directional bias.
    """
    if regime.regime == RISK_ON:
        return "LONG"
    if regime.regime == RISK_OFF:
        return "SHORT"
    if regime.regime == EXPANSION:
        return "LONG"
    if regime.regime == NEUTRAL:
        if regime.net_score > 0:
            return "LONG"
        if regime.net_score < 0:
            return "SHORT"
        return None  # net_score == 0 → truly ambiguous → no trade
    return None  # CHAOTIC, TRANSITION


def print_qualification_summary(
    summary: QualificationSummary,
    regime: RegimeState,
) -> None:
    """Print qualification summary to terminal."""
    print(f"\n{'─' * 52}")
    print(f"  QUALIFICATION SUMMARY")
    print(f"  Regime: {regime.regime} / {regime.posture}  conf={regime.confidence:.2f}")
    if summary.regime_short_circuited:
        print(f"  ⚠  SHORT-CIRCUITED: {summary.regime_failure_reason}")
        print(f"  Symbols evaluated: 0  (regime gate blocked per-symbol work)")
    else:
        print(f"  Symbols evaluated:  {summary.symbols_evaluated}")
        print(f"  Qualified trades:   {summary.symbols_qualified}")
        print(f"  Watchlist:          {summary.symbols_watchlist}")
        print(f"  Excluded:           {summary.symbols_excluded}")

    if summary.qualified_trades:
        print(f"\n  QUALIFIED:")
        for r in summary.qualified_trades:
            print(
                f"    ✓ {r.symbol:<8} {r.direction:<5} "
                f"contracts={r.max_contracts}  risk=${r.dollar_risk:.0f}"
            )

    if summary.watchlist:
        print(f"\n  WATCHLIST:")
        for r in summary.watchlist:
            print(f"    ~ {r.symbol:<8} missing: {r.watchlist_reason}")

    if summary.excluded and not summary.regime_short_circuited:
        print(f"\n  EXCLUDED:")
        for sym, reason in sorted(summary.excluded.items()):
            print(f"    ✗ {sym:<8} {reason}")

    print(f"{'─' * 52}\n")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def detect_continuation_breakout(
    df: pd.DataFrame,
) -> Optional[float]:
    """Return breakout level when current close clears the recent high."""
    n = config.CONTINUATION_BREAKOUT_BARS
    hold_candles = max(1, config.CONTINUATION_HOLD_CANDLES)
    if len(df) < n + 1 + hold_candles:
        return None

    lookback = df.iloc[-(n + 1):-1]
    breakout_level = float(lookback["High"].max())
    current_close = float(df.iloc[-1]["Close"])

    if current_close <= breakout_level:
        return None

    return breakout_level


def _qualify_continuation_candidate(
    symbol: str,
    df: Optional[pd.DataFrame],
    sr: StructureResult,
    regime: RegimeState,
    dm: Optional[DerivedMetrics],
    now_et: Optional[datetime] = None,
) -> "QualificationResult":
    """Build and qualify a continuation candidate for EXPANSION regime."""
    if df is None or dm is None or dm.atr14 is None or dm.atr14 <= 0:
        return _continuation_reject(symbol, "DATA_INCOMPLETE")

    entry_price = float(df.iloc[-1]["Close"])
    gates_passed: list[str] = []

    if (
        regime.vix_pct_change is not None
        and regime.vix_pct_change > config.CONTINUATION_VIX_SPIKE_BLOCK
    ):
        return _continuation_reject(symbol, "VIX_BLOCKED", gates_passed)
    gates_passed.append("VIX")

    breakout_level = detect_continuation_breakout(df)
    if breakout_level is None:
        return _continuation_reject(symbol, "NO_BREAKOUT", gates_passed)
    gates_passed.append("BREAKOUT")

    hold_candles = max(1, config.CONTINUATION_HOLD_CANDLES)
    hold_close = float(df.iloc[-(hold_candles + 1)]["Close"])
    if hold_close <= breakout_level:
        return _continuation_reject(symbol, "NO_HOLD_CONFIRMATION", gates_passed)
    gates_passed.append("HOLD")

    candle_range = float(df.iloc[-1]["High"]) - float(df.iloc[-1]["Low"])
    if candle_range < config.CONTINUATION_MOMENTUM_K * dm.atr14:
        return _continuation_reject(symbol, "INSUFFICIENT_MOMENTUM", gates_passed)
    gates_passed.append("MOMENTUM")

    if dm.ema21 is not None:
        extension = abs(entry_price - dm.ema21) / dm.atr14
        if extension > config.CONTINUATION_MAX_EXTENSION_ATR:
            return _continuation_reject(symbol, "EXTENDED_FROM_MEAN", gates_passed)
    gates_passed.append("EXTENSION")

    stop_price = breakout_level
    risk = entry_price - stop_price
    min_risk = entry_price * 0.01
    if stop_price <= 0 or stop_price >= entry_price or risk < min_risk:
        return _continuation_reject(symbol, "STOP_TOO_TIGHT", gates_passed)
    gates_passed.append("STOP")

    reward = dm.atr14 * (
        (config.CONTINUATION_BREAKOUT_BARS + max(1, config.CONTINUATION_HOLD_CANDLES))
        / 2.0
    )
    rr = reward / risk
    if rr < config.EXPANSION_RR_RATIO:
        return _continuation_reject(symbol, "RR_BELOW_THRESHOLD", gates_passed)
    gates_passed.append("RR")

    if _is_late_session(now_et):
        return _continuation_reject(symbol, "TIME_BLOCKED", gates_passed)
    gates_passed.append("TIME")

    target_price = entry_price + reward

    spread_width = max(0.50, dm.atr14 * 0.05)
    spread_cost = spread_width * 100
    max_contracts = math.floor(config.TARGET_DOLLAR_RISK / spread_cost) if spread_cost > 0 else None
    dollar_risk = (max_contracts * spread_cost) if max_contracts and max_contracts > 0 else None

    if max_contracts is None or max_contracts < 1 or dollar_risk is None:
        return _continuation_reject(symbol, "STOP_TOO_TIGHT", gates_passed)

    return QualificationResult(
        symbol=symbol,
        qualified=True,
        watchlist=False,
        direction="LONG",
        gates_passed=gates_passed,
        gates_failed=[],
        hard_failure=None,
        watchlist_reason=None,
        max_contracts=max_contracts,
        dollar_risk=dollar_risk,
        entry_mode=ENTRY_MODE_CONTINUATION,
        rejection_reason=None,
    )


def _check_regime_gates(regime: RegimeState) -> Optional[str]:
    """Return failure reason if gates 1–2 fail, else None."""
    if regime.posture == STAY_FLAT:
        return f"STAY_FLAT posture (regime={regime.regime}, confidence={regime.confidence:.2f})"
    if regime.confidence < config.MIN_REGIME_CONFIDENCE:
        return (
            f"confidence {regime.confidence:.2f} < "
            f"{config.MIN_REGIME_CONFIDENCE} minimum"
        )
    return None


def _resolve_entry_mode(
    result: QualificationResult,
    candidate: TradeCandidate,
    regime: RegimeState,
    dm: Optional[DerivedMetrics],
    df: Optional[pd.DataFrame],
) -> QualificationResult:
    if not result.qualified:
        return result
    if result.direction not in {"LONG", "SHORT"}:
        return result
    if df is None or dm is None or dm.atr14 is None or dm.atr14 <= 0:
        return result

    zone = detect_fvg(df, result.direction, dm.atr14)
    if zone is None:
        return result

    midpoint = (zone.upper_bound + zone.lower_bound) / 2.0
    current_close = float(df.iloc[-1]["Close"])
    distance = abs(current_close - midpoint)
    if distance > (config.FVG_PROXIMITY_K * dm.atr14):
        return result

    stop_price = zone.lower_bound if result.direction == "LONG" else zone.upper_bound
    risk = abs(midpoint - stop_price)
    reward = abs(candidate.target_price - midpoint)
    imbalance_rr = (reward / risk) if risk > 0 else 0.0
    min_rr = config.NEUTRAL_RR_RATIO if regime.regime == NEUTRAL else config.MIN_RR_RATIO
    if imbalance_rr < min_rr:
        return result

    return replace(
        result,
        entry_mode=ENTRY_MODE_PULLBACK_IMBALANCE,
        imbalance_zone=zone,
    )


def _is_displacement_candle(
    candle: pd.Series,
    direction: str,
    atr14: float,
) -> bool:
    open_price = float(candle["Open"])
    high_price = float(candle["High"])
    low_price = float(candle["Low"])
    close_price = float(candle["Close"])

    if high_price == low_price:
        return False

    range_size = high_price - low_price
    close_location = (close_price - low_price) / range_size

    if direction == "LONG":
        body = close_price - open_price
        return (
            close_price > open_price
            and body >= (config.FVG_DISPLACEMENT_K * atr14)
            and close_location >= 0.75
        )

    body = open_price - close_price
    return (
        open_price > close_price
        and body >= (config.FVG_DISPLACEMENT_K * atr14)
        and close_location <= 0.25
    )


def _hard_reject(
    candidate: TradeCandidate,
    failed_gate: str,
    reason: str,
    gates_passed: list[str],
) -> QualificationResult:
    return QualificationResult(
        symbol=candidate.symbol,
        qualified=False,
        watchlist=False,
        direction=candidate.direction,
        gates_passed=list(gates_passed),
        gates_failed=[failed_gate],
        hard_failure=f"{failed_gate}: {reason}",
        watchlist_reason=None,
        max_contracts=None,
        dollar_risk=None,
    )


def _continuation_reject(
    symbol: str,
    rejection_reason: str,
    gates_passed: Optional[list[str]] = None,
) -> QualificationResult:
    if rejection_reason not in CONTINUATION_REJECTION_REASONS:
        raise ValueError(f"invalid continuation rejection reason: {rejection_reason}")
    return QualificationResult(
        symbol=symbol,
        qualified=False,
        watchlist=False,
        direction="LONG",
        gates_passed=list(gates_passed or []),
        gates_failed=[rejection_reason],
        hard_failure=rejection_reason,
        watchlist_reason=None,
        max_contracts=None,
        dollar_risk=None,
        entry_mode=ENTRY_MODE_CONTINUATION,
        rejection_reason=rejection_reason,
    )


def _build_continuation_audit(
    regime: RegimeState,
    qualified: list[QualificationResult],
    watchlist_trades: list[QualificationResult],
    rejected: list[QualificationResult],
) -> Optional[dict[str, int]]:
    if regime.regime != EXPANSION:
        return None

    accepted = sum(
        1
        for result in [*qualified, *watchlist_trades]
        if result.entry_mode == ENTRY_MODE_CONTINUATION and (result.qualified or result.watchlist)
    )
    audit = {
        "total_candidates": accepted + len(rejected),
        "accepted": accepted,
    }
    for reason in CONTINUATION_REJECTION_REASONS:
        audit[reason] = sum(1 for result in rejected if result.rejection_reason == reason)
    return audit


def _is_late_session(now_et: datetime | None = None) -> bool:
    """True if ET time is at or after ENTRY_CUTOFF_ET (3:30 PM ET).

    Accepts an optional now_et for deterministic testing. Falls back to the
    real wall-clock. Fails open (returns False) on any error.
    """
    try:
        if now_et is None:
            now_et = time_utils.get_now_et()
        return time_utils.is_after_entry_cutoff(now_et, config.ENTRY_CUTOFF_ET)
    except Exception:
        return False  # fail-open
