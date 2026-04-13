"""Pure rule helpers for the deterministic trade policy layer."""

from numbers import Real

from cuttingboard.policy.models import (
    MacroState,
    MarketQuality,
    Posture,
    TradeCandidate,
)

VALID_DXY_TRENDS = {"up", "down", "flat"}
VALID_RATES_DIRECTIONS = {"up", "down", "flat"}
VALID_VIX_REGIMES = {"low", "expanding", "elevated"}
VALID_INDEX_STRUCTURES = {"trend", "range", "breakdown"}
VALID_MARKET_QUALITIES = {"CLEAN", "MIXED", "CHAOTIC"}
VALID_DIRECTIONS = {"long", "short"}
VALID_TRADE_STRUCTURES = {"breakout", "pullback", "reversal"}


def validate_macro_state(macro: MacroState) -> None:
    if not isinstance(macro, MacroState):
        raise ValueError("macro must be a MacroState")
    _require_enum("dxy_trend", macro.dxy_trend, VALID_DXY_TRENDS)
    _require_enum("rates_direction", macro.rates_direction, VALID_RATES_DIRECTIONS)
    _require_enum("vix_regime", macro.vix_regime, VALID_VIX_REGIMES)
    _require_bool("oil_shock", macro.oil_shock)
    _require_enum("index_structure", macro.index_structure, VALID_INDEX_STRUCTURES)


def validate_market_quality(quality: MarketQuality) -> None:
    _require_enum("quality", quality, VALID_MARKET_QUALITIES)


def validate_candidate(candidate: TradeCandidate) -> None:
    if not isinstance(candidate, TradeCandidate):
        raise ValueError("candidate must be a TradeCandidate")
    if not candidate.ticker or not isinstance(candidate.ticker, str):
        raise ValueError("candidate.ticker is required")
    _require_enum("candidate.direction", candidate.direction, VALID_DIRECTIONS)
    _require_positive_number("candidate.entry_price", candidate.entry_price)
    _require_positive_number("candidate.stop_price", candidate.stop_price)
    _require_positive_number("candidate.target_price", candidate.target_price)
    _require_positive_number("candidate.ema9", candidate.ema9)
    _require_positive_number("candidate.ema21", candidate.ema21)
    _require_positive_number("candidate.ema50", candidate.ema50)
    _require_positive_number("candidate.atr14", candidate.atr14)
    _require_enum("candidate.structure", candidate.structure, VALID_TRADE_STRUCTURES)


def determine_posture(macro: MacroState) -> Posture:
    if macro.oil_shock:
        return "SHORT_BIAS"
    if macro.vix_regime == "expanding":
        return "NEUTRAL"
    if macro.dxy_trend == "up" and macro.rates_direction == "up":
        return "SHORT_BIAS"
    if macro.dxy_trend == "down" and macro.rates_direction == "down":
        return "LONG_BIAS"
    return "NEUTRAL"


def check_market_gate(quality: MarketQuality) -> str | None:
    if quality == "CHAOTIC":
        return "MARKET_CHAOTIC"
    return None


def validate_price_relationships(candidate: TradeCandidate) -> str | None:
    if candidate.direction == "long":
        if candidate.stop_price >= candidate.entry_price:
            return "RR_INVALID"
        if candidate.target_price <= candidate.entry_price:
            return "RR_INVALID"
        return None

    if candidate.stop_price <= candidate.entry_price:
        return "RR_INVALID"
    if candidate.target_price >= candidate.entry_price:
        return "RR_INVALID"
    return None


def compute_stop_distance(candidate: TradeCandidate) -> float:
    if candidate.direction == "long":
        return candidate.entry_price - candidate.stop_price
    return candidate.stop_price - candidate.entry_price


def compute_reward(candidate: TradeCandidate) -> float:
    if candidate.direction == "long":
        return candidate.target_price - candidate.entry_price
    return candidate.entry_price - candidate.target_price


def compute_rr(candidate: TradeCandidate) -> float:
    stop_distance = compute_stop_distance(candidate)
    if stop_distance <= 0:
        return 0.0
    return compute_reward(candidate) / stop_distance


def direction_matches_posture(posture: Posture, direction: str) -> bool:
    if posture == "LONG_BIAS":
        return direction == "long"
    if posture == "SHORT_BIAS":
        return direction == "short"
    return False


def is_mean_reversion_exception(posture: Posture, candidate: TradeCandidate) -> bool:
    if posture == "NEUTRAL":
        return False
    if direction_matches_posture(posture, candidate.direction):
        return False
    if candidate.structure != "reversal":
        return False
    if candidate.entry_price <= candidate.ema50:
        return False
    return compute_rr(candidate) >= 3.0


def structure_is_valid(candidate: TradeCandidate) -> bool:
    if candidate.structure == "breakout":
        return (
            candidate.entry_price > candidate.ema9
            and candidate.ema9 > candidate.ema21 > candidate.ema50
        )
    if candidate.structure == "pullback":
        return (
            candidate.entry_price >= candidate.ema21
            and candidate.ema21 > candidate.ema50
        )
    if candidate.structure == "reversal":
        return candidate.entry_price > candidate.ema50
    return False


def risk_reward_is_valid(candidate: TradeCandidate, *, require_high_rr: bool) -> bool:
    stop_distance = compute_stop_distance(candidate)
    rr = compute_rr(candidate)
    if stop_distance < 0.01 * candidate.entry_price:
        return False
    if stop_distance < 0.5 * candidate.atr14:
        return False
    if rr < 2.0:
        return False
    if require_high_rr and rr < 3.0:
        return False
    return True


def debit_spreads_only(vix_regime: str) -> bool:
    return vix_regime in {"low", "expanding"}


def _require_enum(name: str, value: str | None, allowed: set[str]) -> None:
    if value is None:
        raise ValueError(f"{name} is required")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}")


def _require_bool(name: str, value: object) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a bool")


def _require_positive_number(name: str, value: object) -> None:
    if value is None:
        raise ValueError(f"{name} is required")
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be numeric")
    if value <= 0:
        raise ValueError(f"{name} must be > 0")
