"""Models for the deterministic trade policy layer."""

from dataclasses import dataclass
from typing import Literal

MacroTrend = Literal["up", "down", "flat"]
VixRegime = Literal["low", "expanding", "elevated"]
IndexStructure = Literal["trend", "range", "breakdown"]
MarketQuality = Literal["CLEAN", "MIXED", "CHAOTIC"]
TradeDirection = Literal["long", "short"]
TradeStructure = Literal["breakout", "pullback", "reversal"]
Posture = Literal["LONG_BIAS", "SHORT_BIAS", "NEUTRAL"]
TradeDecisionStatus = Literal["APPROVED", "REJECTED"]
SpreadType = Literal["call_debit", "put_debit", "call_credit", "put_credit"]
Duration = Literal["0DTE", "weekly", "30-45DTE"]


@dataclass(frozen=True)
class MacroState:
    dxy_trend: MacroTrend
    rates_direction: MacroTrend
    vix_regime: VixRegime
    oil_shock: bool
    index_structure: IndexStructure


@dataclass(frozen=True)
class TradeCandidate:
    ticker: str
    direction: TradeDirection
    entry_price: float
    stop_price: float
    target_price: float
    ema9: float
    ema21: float
    ema50: float
    atr14: float
    structure: TradeStructure


@dataclass(frozen=True)
class OptionsExpression:
    spread_type: SpreadType
    duration: Duration
    notes: str | None


@dataclass(frozen=True)
class TradeDecision:
    posture: Posture
    decision: TradeDecisionStatus
    reason: str | None
    options_plan: OptionsExpression | None
