"""Read-only graded market map sidecar.

This module consumes already-computed runtime objects. It does not fetch data,
write artifacts, or alter execution decisions.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Mapping

from cuttingboard.derived import DerivedMetrics
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.regime import EXPANSION, NEUTRAL, RISK_OFF, RISK_ON, RegimeState
from cuttingboard.structure import BREAKOUT, CHOP, PULLBACK, REVERSAL, TREND, StructureResult
from cuttingboard.watch import IntradayMetrics, WatchSummary

SCHEMA_VERSION = "market_map.v1"
PRIMARY_SYMBOLS = ("SPY", "QQQ", "GDX", "GLD", "SLV", "XLE")

GRADE_A_PLUS = "A+"
GRADE_A = "A"
GRADE_B = "B"
GRADE_C = "C"
GRADE_D = "D"
GRADE_F = "F"
VALID_GRADES = frozenset({GRADE_A_PLUS, GRADE_A, GRADE_B, GRADE_C, GRADE_D, GRADE_F})

BIAS_BULLISH = "BULLISH"
BIAS_BEARISH = "BEARISH"
BIAS_NEUTRAL = "NEUTRAL"
BIAS_MIXED = "MIXED"
VALID_BIASES = frozenset({BIAS_BULLISH, BIAS_BEARISH, BIAS_NEUTRAL, BIAS_MIXED})

STRUCTURE_TRENDING_UP = "TRENDING_UP"
STRUCTURE_TRENDING_DOWN = "TRENDING_DOWN"
STRUCTURE_PULLBACK = "PULLBACK"
STRUCTURE_BREAKOUT = "BREAKOUT"
STRUCTURE_BREAKDOWN = "BREAKDOWN"
STRUCTURE_RANGE = "RANGE"
STRUCTURE_CHOPPY = "CHOPPY"
STRUCTURE_UNKNOWN = "UNKNOWN"
VALID_STRUCTURES = frozenset(
    {
        STRUCTURE_TRENDING_UP,
        STRUCTURE_TRENDING_DOWN,
        STRUCTURE_PULLBACK,
        STRUCTURE_BREAKOUT,
        STRUCTURE_BREAKDOWN,
        STRUCTURE_RANGE,
        STRUCTURE_CHOPPY,
        STRUCTURE_UNKNOWN,
    }
)

SETUP_ACTIONABLE = "ACTIONABLE"
SETUP_STRONG_WATCH = "STRONG_WATCH"
SETUP_DEVELOPING = "DEVELOPING"
SETUP_EXTENDED = "EXTENDED"
SETUP_CHOPPY = "CHOPPY"
SETUP_LOW_QUALITY = "LOW_QUALITY"
SETUP_DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
VALID_SETUP_STATES = frozenset(
    {
        SETUP_ACTIONABLE,
        SETUP_STRONG_WATCH,
        SETUP_DEVELOPING,
        SETUP_EXTENDED,
        SETUP_CHOPPY,
        SETUP_LOW_QUALITY,
        SETUP_DATA_UNAVAILABLE,
    }
)

CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW = "LOW"
VALID_CONFIDENCE = frozenset({CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW})

TRADE_DIRECTION_LONG = "LONG"
TRADE_DIRECTION_SHORT = "SHORT"
TRADE_DIRECTION_NEUTRAL = "NEUTRAL"
VALID_TRADE_DIRECTIONS = frozenset(
    {TRADE_DIRECTION_LONG, TRADE_DIRECTION_SHORT, TRADE_DIRECTION_NEUTRAL}
)

TRADE_TYPE_CALL_SPREAD = "call_spread"
TRADE_TYPE_PUT_SPREAD = "put_spread"
TRADE_TYPE_NONE = "none"
VALID_TRADE_TYPES = frozenset({TRADE_TYPE_CALL_SPREAD, TRADE_TYPE_PUT_SPREAD, TRADE_TYPE_NONE})

IF_NOW_TAKE = "TAKE"
IF_NOW_WAIT = "WAIT"
VALID_IF_NOW = frozenset({IF_NOW_TAKE, IF_NOW_WAIT})

UNAVAILABLE_WHAT_TO_LOOK_FOR = "Market data unavailable for this run; review during live market session."
UNAVAILABLE_INVALIDATION = "No trade structure available until price, structure, and level data are present."
UNAVAILABLE_REASON = "Market data unavailable for this run."

ASSET_GROUPS = {
    "SPY": "INDEX",
    "QQQ": "INDEX",
    "GDX": "METALS",
    "GLD": "METALS",
    "SLV": "METALS",
    "XLE": "ENERGY",
}

ENERGY_CONTEXT_SYMBOL = "USO"
FIB_WINDOW_BARS = 20
EXTENSION_ATR_MULTIPLIER = 1.5
PROXIMITY_THRESHOLD_PCT = 0.01


def build_market_map(
    *,
    generated_at: datetime,
    session_date: str,
    mode: str,
    run_at_utc: datetime,
    normalized_quotes: Mapping[str, NormalizedQuote],
    derived_metrics: Mapping[str, DerivedMetrics],
    structure_results: Mapping[str, StructureResult],
    intraday_metrics: Mapping[str, IntradayMetrics],
    regime: RegimeState | None,
    watch_summary: WatchSummary | None = None,
    bar_windows: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    symbols = {
        symbol: _build_symbol_record(
            symbol=symbol,
            quote=normalized_quotes.get(symbol),
            derived=derived_metrics.get(symbol),
            structure_result=structure_results.get(symbol),
            intraday=intraday_metrics.get(symbol),
            regime=regime,
            watch_summary=watch_summary,
            bars=(bar_windows or {}).get(symbol),
        )
        for symbol in PRIMARY_SYMBOLS
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _iso(generated_at),
        "session_date": session_date,
        "source": {
            "mode": mode,
            "run_at_utc": _iso(run_at_utc),
        },
        "primary_symbols": list(PRIMARY_SYMBOLS),
        "symbols": symbols,
        "context": _build_context(normalized_quotes, derived_metrics, structure_results),
        "data_quality": _build_data_quality(symbols),
    }


def _build_symbol_record(
    *,
    symbol: str,
    quote: NormalizedQuote | None,
    derived: DerivedMetrics | None,
    structure_result: StructureResult | None,
    intraday: IntradayMetrics | None,
    regime: RegimeState | None,
    watch_summary: WatchSummary | None,
    bars: Any,
) -> dict[str, Any]:
    missing = _missing_inputs(quote, derived, structure_result, intraday)
    price = _optional_float(getattr(quote, "price", None)) if quote is not None else None
    bias = _bias(quote, derived, regime)
    structure = _structure(structure_result, derived, bias)
    watch_zones = _watch_zones(price, derived, intraday)
    fib_levels = _fib_levels(bars)
    extended = _is_extended(price, derived)
    near_key_level = _near_key_level(price, watch_zones)
    regime_aligned = _regime_aligned(bias, regime)
    strong_structure = structure in {
        STRUCTURE_TRENDING_UP,
        STRUCTURE_TRENDING_DOWN,
        STRUCTURE_BREAKOUT,
        STRUCTURE_BREAKDOWN,
    }
    on_watch = _watch_contains(symbol, watch_summary)

    if quote is None or not _derived_sufficient(derived) or structure_result is None:
        grade = GRADE_F
        setup_state = SETUP_DATA_UNAVAILABLE
    elif structure == STRUCTURE_CHOPPY:
        grade = GRADE_F
        setup_state = SETUP_CHOPPY
    elif extended:
        grade = GRADE_D
        setup_state = SETUP_EXTENDED
    elif regime_aligned and strong_structure and near_key_level:
        grade = GRADE_A_PLUS
        setup_state = SETUP_ACTIONABLE
    elif regime_aligned and (strong_structure or on_watch):
        grade = GRADE_A
        setup_state = SETUP_STRONG_WATCH
    elif structure in {STRUCTURE_PULLBACK, STRUCTURE_BREAKOUT, STRUCTURE_BREAKDOWN} or on_watch:
        grade = GRADE_B
        setup_state = SETUP_DEVELOPING
    elif structure in {STRUCTURE_RANGE, STRUCTURE_UNKNOWN}:
        grade = GRADE_C
        setup_state = SETUP_LOW_QUALITY
    else:
        grade = GRADE_D
        setup_state = SETUP_LOW_QUALITY

    record = {
        "symbol": symbol,
        "asset_group": ASSET_GROUPS[symbol],
        "grade": grade,
        "bias": bias,
        "structure": structure,
        "setup_state": setup_state,
        "confidence": _confidence(grade, regime, structure),
        "watch_zones": watch_zones,
        "fib_levels": fib_levels,
        "what_to_look_for": _what_to_look_for(grade, bias, setup_state, watch_zones, missing),
        "invalidation": _invalidation(bias, watch_zones, missing),
        "preferred_trade_structure": _preferred_trade_structure(grade, bias, setup_state),
        "reason_for_grade": _reason_for_grade(
            grade=grade,
            bias=bias,
            structure=structure,
            regime_aligned=regime_aligned,
            near_key_level=near_key_level,
            extended=extended,
            missing=missing,
        ),
    }
    record["trade_framing"] = _trade_framing(
        grade=grade,
        bias=bias,
        structure=structure,
        setup_state=setup_state,
        watch_zones=watch_zones,
        asset_group=record["asset_group"],
    )
    return record


def _missing_inputs(
    quote: NormalizedQuote | None,
    derived: DerivedMetrics | None,
    structure_result: StructureResult | None,
    intraday: IntradayMetrics | None,
) -> list[str]:
    missing: list[str] = []
    if quote is None:
        missing.append("missing_quote")
    if derived is None or not _derived_sufficient(derived):
        missing.append("missing_derived_metrics")
    if structure_result is None:
        missing.append("missing_structure")
    if intraday is None:
        missing.append("missing_intraday_metrics")
    return missing


def _bias(
    quote: NormalizedQuote | None,
    derived: DerivedMetrics | None,
    regime: RegimeState | None,
) -> str:
    if derived is not None and _derived_sufficient(derived):
        if bool(getattr(derived, "ema_aligned_bull", False)):
            return BIAS_BULLISH
        if bool(getattr(derived, "ema_aligned_bear", False)):
            return BIAS_BEARISH

    if quote is not None:
        pct_change = float(getattr(quote, "pct_change_decimal", 0.0))
        if pct_change > 0.003:
            return BIAS_BULLISH
        if pct_change < -0.003:
            return BIAS_BEARISH

    if regime is not None and regime.regime == NEUTRAL:
        return BIAS_NEUTRAL
    return BIAS_MIXED


def _structure(
    structure_result: StructureResult | None,
    derived: DerivedMetrics | None,
    bias: str,
) -> str:
    if structure_result is None:
        return STRUCTURE_UNKNOWN
    if structure_result.structure == CHOP:
        return STRUCTURE_CHOPPY
    if structure_result.structure == TREND:
        if derived is not None and bool(getattr(derived, "ema_aligned_bear", False)):
            return STRUCTURE_TRENDING_DOWN
        return STRUCTURE_TRENDING_UP
    if structure_result.structure == PULLBACK:
        return STRUCTURE_PULLBACK
    if structure_result.structure == BREAKOUT:
        return STRUCTURE_BREAKDOWN if bias == BIAS_BEARISH else STRUCTURE_BREAKOUT
    if structure_result.structure == REVERSAL:
        return STRUCTURE_RANGE
    return STRUCTURE_UNKNOWN


def _watch_zones(
    price: float | None,
    derived: DerivedMetrics | None,
    intraday: IntradayMetrics | None,
) -> list[dict[str, Any]]:
    if price is None or price <= 0:
        return []

    zones: list[dict[str, Any]] = []
    if intraday is not None:
        zones.extend(
            [
                _zone("VWAP", intraday.vwap, price, "session vwap"),
                _zone("ORB_HIGH", intraday.orb_high, price, "opening range high"),
                _zone("ORB_LOW", intraday.orb_low, price, "opening range low"),
                _zone("PRIOR_HIGH", intraday.pdh, price, "prior session high"),
                _zone("PRIOR_LOW", intraday.pdl, price, "prior session low"),
            ]
        )
    if derived is not None:
        zones.extend(
            [
                _zone("EMA9", _optional_float(getattr(derived, "ema9", None)), price, "fast trend reference"),
                _zone("EMA21", _optional_float(getattr(derived, "ema21", None)), price, "primary trend reference"),
                _zone("EMA50", _optional_float(getattr(derived, "ema50", None)), price, "trend base reference"),
            ]
        )

    zones = [zone for zone in zones if zone is not None]
    zones.sort(key=lambda zone: (abs(float(zone["level"]) - price) / price, zone["type"]))
    return zones


def _zone(zone_type: str, level: float | None, price: float, context: str) -> dict[str, Any] | None:
    if level is None:
        return None
    numeric = float(level)
    if not math.isfinite(numeric):
        return None
    distance_pct = abs(numeric - price) / price if price > 0 else 1.0
    if distance_pct > 0.05:
        return None
    return {
        "type": zone_type,
        "level": round(numeric, 4),
        "context": context,
    }


def _fib_levels(bars: Any) -> dict[str, Any] | None:
    if bars is None:
        return None
    try:
        frame = bars.tail(FIB_WINDOW_BARS)
        if len(frame) < 2:
            return None
        high = float(frame["High"].astype(float).max())
        low = float(frame["Low"].astype(float).min())
    except Exception:
        return None

    if not math.isfinite(high) or not math.isfinite(low) or high <= low:
        return None

    span = high - low
    return {
        "source": f"last_{FIB_WINDOW_BARS}_bars_high_low",
        "swing_high": round(high, 4),
        "swing_low": round(low, 4),
        "retracements": {
            "0.382": round(high - span * 0.382, 4),
            "0.5": round(high - span * 0.5, 4),
            "0.618": round(high - span * 0.618, 4),
        },
    }


def _is_extended(price: float | None, derived: DerivedMetrics | None) -> bool:
    if price is None or derived is None:
        return False
    ema21 = _optional_float(getattr(derived, "ema21", None))
    atr14 = _optional_float(getattr(derived, "atr14", None))
    if ema21 is None or atr14 is None or atr14 <= 0:
        return False
    return abs(price - ema21) / atr14 > EXTENSION_ATR_MULTIPLIER


def _near_key_level(price: float | None, watch_zones: list[dict[str, Any]]) -> bool:
    if price is None or price <= 0:
        return False
    return any(abs(float(zone["level"]) - price) / price <= PROXIMITY_THRESHOLD_PCT for zone in watch_zones)


def _regime_aligned(bias: str, regime: RegimeState | None) -> bool:
    if regime is None:
        return False
    if bias == BIAS_BULLISH:
        return regime.regime in {RISK_ON, EXPANSION} or regime.net_score > 0
    if bias == BIAS_BEARISH:
        return regime.regime == RISK_OFF or regime.net_score < 0
    if bias == BIAS_NEUTRAL:
        return regime.regime == NEUTRAL
    return False


def _watch_contains(symbol: str, watch_summary: WatchSummary | None) -> bool:
    if watch_summary is None:
        return False
    return any(item.symbol == symbol for item in watch_summary.watchlist)


def _confidence(grade: str, regime: RegimeState | None, structure: str) -> str:
    regime_conf = regime.confidence if regime is not None else 0.0
    if grade in {GRADE_D, GRADE_F}:
        return CONFIDENCE_LOW
    if grade in {GRADE_A_PLUS, GRADE_A} and regime_conf >= 0.5 and structure not in {STRUCTURE_UNKNOWN, STRUCTURE_CHOPPY}:
        return CONFIDENCE_HIGH
    if grade in {GRADE_B, GRADE_C} or regime_conf >= 0.35:
        return CONFIDENCE_MEDIUM
    return CONFIDENCE_LOW


def _what_to_look_for(
    grade: str,
    bias: str,
    setup_state: str,
    watch_zones: list[dict[str, Any]],
    missing: list[str],
) -> list[str]:
    if missing and grade == GRADE_F:
        return [UNAVAILABLE_WHAT_TO_LOOK_FOR]

    nearest = watch_zones[0]["type"] if watch_zones else "defined reference level"
    if setup_state == SETUP_EXTENDED:
        return [f"look for reset toward {nearest}", "watch for cleaner compression"]
    if bias == BIAS_BULLISH:
        return [f"watch hold above {nearest}", "look for higher low with expanding volume"]
    if bias == BIAS_BEARISH:
        return [f"watch rejection near {nearest}", "look for lower high with expanding volume"]
    return [f"watch reaction around {nearest}", "look for clearer directional structure"]


def _invalidation(
    bias: str,
    watch_zones: list[dict[str, Any]],
    missing: list[str],
) -> list[str]:
    if missing and not watch_zones:
        return [UNAVAILABLE_INVALIDATION]
    nearest = watch_zones[0]["type"] if watch_zones else "reference level"
    if bias == BIAS_BULLISH:
        return [f"loses {nearest} with weak recovery", "momentum fades below primary trend reference"]
    if bias == BIAS_BEARISH:
        return [f"reclaims {nearest} with follow-through", "momentum improves above primary trend reference"]
    return [f"range fails to define around {nearest}", "mixed structure persists"]


def _preferred_trade_structure(grade: str, bias: str, setup_state: str) -> str | None:
    if grade == GRADE_F or setup_state in {SETUP_DATA_UNAVAILABLE, SETUP_CHOPPY}:
        return None
    if setup_state == SETUP_EXTENDED:
        return "pullback reset watch"
    if bias == BIAS_BULLISH:
        return "bullish defined-risk continuation"
    if bias == BIAS_BEARISH:
        return "bearish defined-risk continuation"
    return "range-resolution watch"


def _trade_framing(
    *,
    grade: str,
    bias: str,
    structure: str,
    setup_state: str,
    watch_zones: list[dict[str, Any]],
    asset_group: str,
) -> dict[str, str]:
    nearest = watch_zones[0]["type"] if watch_zones else "defined reference level"
    directional_grade = grade in {GRADE_A_PLUS, GRADE_A, GRADE_B}
    actionable_now = grade == GRADE_A_PLUS and setup_state == SETUP_ACTIONABLE

    if directional_grade and bias == BIAS_BULLISH:
        return {
            "direction": TRADE_DIRECTION_LONG,
            "trade_type": TRADE_TYPE_CALL_SPREAD,
            "setup": f"{asset_group.lower()} bullish {structure.lower()}",
            "entry": f"hold above {nearest} with constructive follow-through",
            "if_now": IF_NOW_TAKE if actionable_now else IF_NOW_WAIT,
            "upgrade": "improves on clean hold near key level with expanding participation",
            "downgrade": f"wait if price loses {nearest} or structure turns choppy",
        }

    if directional_grade and bias == BIAS_BEARISH:
        return {
            "direction": TRADE_DIRECTION_SHORT,
            "trade_type": TRADE_TYPE_PUT_SPREAD,
            "setup": f"{asset_group.lower()} bearish {structure.lower()}",
            "entry": f"rejects near {nearest} with downside follow-through",
            "if_now": IF_NOW_TAKE if actionable_now else IF_NOW_WAIT,
            "upgrade": "improves on clean rejection near key level with expanding participation",
            "downgrade": f"wait if price reclaims {nearest} or structure turns choppy",
        }

    if setup_state == SETUP_DATA_UNAVAILABLE:
        return {
            "direction": TRADE_DIRECTION_NEUTRAL,
            "trade_type": TRADE_TYPE_NONE,
            "setup": "market data unavailable for this run",
            "entry": "wait for price, structure, and level data to populate",
            "if_now": IF_NOW_WAIT,
            "upgrade": "reassess when market data is available",
            "downgrade": "remains unavailable while primary market data is absent",
        }

    if setup_state == SETUP_EXTENDED:
        setup = f"{asset_group.lower()} extended {bias.lower()} structure"
        entry = f"wait for reset toward {nearest} before defining risk"
    elif setup_state == SETUP_CHOPPY:
        setup = f"{asset_group.lower()} choppy structure"
        entry = f"wait for cleaner structure around {nearest}"
    else:
        setup = f"{asset_group.lower()} low-quality {structure.lower()}"
        entry = f"wait for clearer reaction around {nearest}"

    return {
        "direction": TRADE_DIRECTION_NEUTRAL,
        "trade_type": TRADE_TYPE_NONE,
        "setup": setup,
        "entry": entry,
        "if_now": IF_NOW_WAIT,
        "upgrade": "improves with cleaner directional structure near a key level",
        "downgrade": "weakens if structure stays mixed or moves away from reference levels",
    }


def _reason_for_grade(
    *,
    grade: str,
    bias: str,
    structure: str,
    regime_aligned: bool,
    near_key_level: bool,
    extended: bool,
    missing: list[str],
) -> str:
    if missing and grade == GRADE_F:
        return UNAVAILABLE_REASON
    if structure == STRUCTURE_CHOPPY:
        return f"{grade}: structurally invalid - choppy market structure"
    if extended:
        return f"{grade}: {bias.lower()} structure is extended from trend reference"
    parts = [f"{grade}: {bias.lower()} {structure.lower()}"]
    parts.append("regime aligned" if regime_aligned else "regime mixed")
    parts.append("near key level" if near_key_level else "away from key level")
    return ", ".join(parts)


def _build_context(
    normalized_quotes: Mapping[str, NormalizedQuote],
    derived_metrics: Mapping[str, DerivedMetrics],
    structure_results: Mapping[str, StructureResult],
) -> dict[str, Any]:
    quote = normalized_quotes.get(ENERGY_CONTEXT_SYMBOL)
    if quote is None:
        return {"energy": None}
    derived = derived_metrics.get(ENERGY_CONTEXT_SYMBOL)
    structure = structure_results.get(ENERGY_CONTEXT_SYMBOL)
    return {
        "energy": {
            "symbol": ENERGY_CONTEXT_SYMBOL,
            "asset_group": "ENERGY_CONTEXT",
            "price": float(getattr(quote, "price", 0.0)),
            "pct_change_decimal": float(getattr(quote, "pct_change_decimal", 0.0)),
            "structure": _structure(structure, derived, _bias(quote, derived, None)),
        }
    }


def _build_data_quality(symbols: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    unavailable = [
        symbol
        for symbol, record in symbols.items()
        if record["grade"] == GRADE_F or record["setup_state"] == SETUP_DATA_UNAVAILABLE
    ]
    fib_deferred = [
        symbol
        for symbol, record in symbols.items()
        if record["fib_levels"] is None
    ]
    return {
        "unavailable_symbols": unavailable,
        "fib_deferred_symbols": fib_deferred,
    }


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _derived_sufficient(derived: Any) -> bool:
    return bool(getattr(derived, "sufficient_history", False))


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
