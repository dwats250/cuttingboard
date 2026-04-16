"""
Deterministic intraday WATCH layer.

WATCH is a structural awareness layer that runs independently of A+
qualification. It never weakens existing trade qualification gates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from statistics import mean
from typing import Callable, Optional
from zoneinfo import ZoneInfo

import pandas as pd

from cuttingboard.derived import DerivedMetrics
from cuttingboard.ingestion import fetch_intraday_bars, fetch_ohlcv
from cuttingboard.regime import CHAOTIC, NEUTRAL, RISK_OFF, RISK_ON, RegimeState
from cuttingboard.structure import BREAKOUT, CHOP, PULLBACK, StructureResult, TREND

logger = logging.getLogger(__name__)

EASTERN_TZ = ZoneInfo("America/New_York")

N_RANGE = 5
N_PRIOR = 20
MAX_INTRADAY_BARS = 120
WATCH_SCORE_MIN = 60.0
WATCH_OUTPUT_MAX = 10

MORNING = "MORNING"
MIDDAY = "MIDDAY"
POWER_HOUR = "POWER_HOUR"

STRUCTURE_SCORES = {
    BREAKOUT: 40.0,
    TREND: 30.0,
    PULLBACK: 20.0,
    CHOP: 15.0,
}

SESSION_THRESHOLDS = {
    MORNING: 3,
    MIDDAY: 3,
    POWER_HOUR: 2,
}


@dataclass(frozen=True)
class IntradayBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class IntradayMetrics:
    symbol: str
    bars: list[IntradayBar]
    orb_high: float
    orb_low: float
    vwap: float
    pdh: float
    pdl: float
    range_last_n: float
    avg_range_prior: float
    compression_ratio: float
    volume_ratio: float
    consecutive_expansion_count: int
    higher_lows: bool
    lower_highs: bool
    first_expansion: bool
    wide_range_dominance: bool


@dataclass(frozen=True)
class WatchItem:
    symbol: str
    score: float
    structure: str
    structure_note: str
    missing_conditions: list[str]
    total_signals: int
    level: str
    bias: str


@dataclass(frozen=True)
class WatchSummary:
    session: Optional[str]
    threshold: Optional[int]
    watchlist: list[WatchItem]
    ignored_symbols: list[str]
    execution_posture: str


def get_session_phase(ts: datetime) -> Optional[str]:
    """Return session phase from a timestamp, or None outside the watch window."""
    et = ts.astimezone(EASTERN_TZ)
    clock = et.time()
    if time(9, 30) <= clock < time(10, 30):
        return MORNING
    if time(10, 30) <= clock < time(14, 0):
        return MIDDAY
    if time(14, 0) <= clock <= time(15, 30):
        return POWER_HOUR
    return None


def compute_all_intraday_metrics(
    symbols: list[str],
    *,
    intraday_fetcher: Callable[[str], Optional[pd.DataFrame]] = fetch_intraday_bars,
    daily_fetcher: Callable[[str], Optional[pd.DataFrame]] = fetch_ohlcv,
) -> tuple[dict[str, IntradayMetrics], list[str]]:
    """Compute intraday metrics for all symbols, ignoring per-symbol failures."""
    results: dict[str, IntradayMetrics] = {}
    ignored: list[str] = []

    for symbol in symbols:
        metrics = compute_intraday_metrics(
            symbol,
            intraday_fetcher=intraday_fetcher,
            daily_fetcher=daily_fetcher,
        )
        if metrics is None:
            ignored.append(symbol)
        else:
            results[symbol] = metrics
    return results, ignored


def compute_intraday_metrics(
    symbol: str,
    *,
    intraday_fetcher: Callable[[str], Optional[pd.DataFrame]] = fetch_intraday_bars,
    daily_fetcher: Callable[[str], Optional[pd.DataFrame]] = fetch_ohlcv,
) -> Optional[IntradayMetrics]:
    """Build IntradayMetrics from intraday and daily data for one symbol."""
    intraday_df = intraday_fetcher(symbol)
    if intraday_df is None or intraday_df.empty:
        logger.info("WATCH ignore %s: intraday fetch unavailable", symbol)
        return None

    daily_df = daily_fetcher(symbol)
    if daily_df is None or daily_df.empty:
        logger.info("WATCH ignore %s: daily OHLCV unavailable", symbol)
        return None

    bars = _bars_from_df(intraday_df)
    if len(bars) < (N_RANGE + N_PRIOR):
        logger.info("WATCH ignore %s: only %d intraday bars available", symbol, len(bars))
        return None

    pdh = float(daily_df["High"].astype(float).iloc[-1])
    pdl = float(daily_df["Low"].astype(float).iloc[-1])

    orb_slice = bars[:N_RANGE]
    orb_high = max(bar.high for bar in orb_slice)
    orb_low = min(bar.low for bar in orb_slice)

    range_last_n = max(bar.high for bar in bars[-N_RANGE:]) - min(bar.low for bar in bars[-N_RANGE:])
    prior_ranges = [(bar.high - bar.low) for bar in bars[-(N_RANGE + N_PRIOR):-N_RANGE]]
    avg_range_prior = mean(prior_ranges)
    if avg_range_prior <= 0:
        logger.info("WATCH ignore %s: avg_range_prior <= 0", symbol)
        return None

    compression_ratio = range_last_n / avg_range_prior

    trailing_volumes = [bar.volume for bar in bars[-N_PRIOR:]]
    avg_volume = mean(trailing_volumes)
    if avg_volume <= 0:
        logger.info("WATCH ignore %s: avg intraday volume <= 0", symbol)
        return None
    volume_ratio = bars[-1].volume / avg_volume

    ranges = [(bar.high - bar.low) for bar in bars]
    consecutive_expansion_count = 0
    for bar_range in reversed(ranges):
        if bar_range > avg_range_prior:
            consecutive_expansion_count += 1
        else:
            break

    highs = [bar.high for bar in bars[-N_RANGE:]]
    lows = [bar.low for bar in bars[-N_RANGE:]]
    higher_lows = all(curr > prev for prev, curr in zip(lows, lows[1:]))
    lower_highs = all(curr < prev for prev, curr in zip(highs, highs[1:]))

    current_range = ranges[-1]
    previous_range = ranges[-2]
    first_expansion = current_range > avg_range_prior and previous_range <= avg_range_prior
    wide_range_dominance = sum(1 for bar_range in ranges[-N_RANGE:] if bar_range > 1.5 * avg_range_prior) >= 3

    cumulative_pv = 0.0
    cumulative_volume = 0.0
    vwap = bars[-1].close
    for bar in bars:
        typical_price = (bar.high + bar.low + bar.close) / 3.0
        cumulative_pv += typical_price * bar.volume
        cumulative_volume += bar.volume
        if cumulative_volume > 0:
            vwap = cumulative_pv / cumulative_volume

    return IntradayMetrics(
        symbol=symbol,
        bars=bars,
        orb_high=orb_high,
        orb_low=orb_low,
        vwap=vwap,
        pdh=pdh,
        pdl=pdl,
        range_last_n=range_last_n,
        avg_range_prior=avg_range_prior,
        compression_ratio=compression_ratio,
        volume_ratio=volume_ratio,
        consecutive_expansion_count=consecutive_expansion_count,
        higher_lows=higher_lows,
        lower_highs=lower_highs,
        first_expansion=first_expansion,
        wide_range_dominance=wide_range_dominance,
    )


def classify_watchlist(
    structure_results: dict[str, StructureResult],
    derived_metrics: dict[str, DerivedMetrics],
    intraday_metrics: dict[str, IntradayMetrics],
    regime: RegimeState,
    *,
    asof: Optional[datetime] = None,
    ignored_symbols: Optional[list[str]] = None,
) -> WatchSummary:
    """Build the deterministic WATCHLIST for the current session."""
    asof = asof or datetime.now(timezone.utc)
    session = get_session_phase(asof)
    threshold = SESSION_THRESHOLDS.get(session) if session else None
    watch_items: list[WatchItem] = []

    if threshold is not None:
        for symbol, im in intraday_metrics.items():
            sr = structure_results.get(symbol)
            dm = derived_metrics.get(symbol)
            if sr is None or dm is None:
                continue

            item = _classify_symbol(symbol, sr, dm, im, threshold)
            if item is not None:
                watch_items.append(item)

    watch_items.sort(key=lambda item: (-item.score, item.symbol))
    watch_items = watch_items[:WATCH_OUTPUT_MAX]

    return WatchSummary(
        session=session,
        threshold=threshold,
        watchlist=watch_items,
        ignored_symbols=sorted(ignored_symbols or []),
        execution_posture=_execution_posture(regime),
    )


def _classify_symbol(
    symbol: str,
    structure_result: StructureResult,
    derived: DerivedMetrics,
    intraday: IntradayMetrics,
    threshold: int,
) -> Optional[WatchItem]:
    price = intraday.bars[-1].close
    if price <= 0:
        return None

    if structure_result.structure == CHOP and intraday.compression_ratio >= 0.7:
        return None

    if intraday.consecutive_expansion_count >= 4:
        return None

    if intraday.wide_range_dominance:
        return None

    near_ema9 = derived.ema9 is not None and _distance_pct(price, derived.ema9) < 0.005
    near_ema21 = derived.ema21 is not None and _distance_pct(price, derived.ema21) < 0.01
    pattern_signal = intraday.higher_lows or intraday.lower_highs
    near_orb = min(_distance_pct(price, intraday.orb_high), _distance_pct(price, intraday.orb_low)) < 0.005
    near_vwap = _distance_pct(price, intraday.vwap) < 0.005
    near_pdh_pdl = min(_distance_pct(price, intraday.pdh), _distance_pct(price, intraday.pdl)) < 0.005
    volume_signal = intraday.volume_ratio > 1.2
    compression_signal = intraday.compression_ratio < 0.7
    first_expansion = intraday.first_expansion

    total_signals = sum(
        (
            near_ema9,
            near_ema21,
            pattern_signal,
            near_orb,
            near_vwap,
            near_pdh_pdl,
            volume_signal,
            compression_signal,
            first_expansion,
        )
    )

    if total_signals < threshold:
        return None

    score = (
        _structure_score(structure_result.structure)
        + _compression_score(intraday.compression_ratio)
        + _proximity_score(price, intraday)
        + _momentum_score(intraday.volume_ratio, intraday.first_expansion)
    )
    score = round(score, 1)

    if score < WATCH_SCORE_MIN:
        return None

    level = _nearest_level(price, intraday)
    bias = _infer_bias(price, derived, intraday)
    structure_note = f"{structure_result.structure} near {level} with {_compression_state(intraday)}"

    missing_conditions: list[str] = []
    if not near_orb:
        missing_conditions.append("move to ORB level")
    if not _breakout_confirmed(price, intraday):
        missing_conditions.append("break above ORB high" if bias == "LONG" else "break below ORB low")
    if not intraday.higher_lows:
        missing_conditions.append("form higher low")
    if intraday.volume_ratio <= 1.2:
        missing_conditions.append("volume expansion")
    if intraday.compression_ratio >= 0.7:
        missing_conditions.append("tighten range")

    return WatchItem(
        symbol=symbol,
        score=score,
        structure=structure_result.structure,
        structure_note=structure_note,
        missing_conditions=missing_conditions,
        total_signals=total_signals,
        level=level,
        bias=bias,
    )


def _bars_from_df(df: pd.DataFrame) -> list[IntradayBar]:
    frame = df.tail(MAX_INTRADAY_BARS).copy()
    frame.index = pd.to_datetime(frame.index, utc=True)
    bars: list[IntradayBar] = []
    for ts, row in frame.iterrows():
        bars.append(
            IntradayBar(
                timestamp=ts.to_pydatetime(),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
            )
        )
    return bars


def _distance_pct(price: float, level: float) -> float:
    if price <= 0:
        return 1.0
    return abs(price - level) / price


def _structure_score(structure: str) -> float:
    return STRUCTURE_SCORES.get(structure, 0.0)


def _compression_score(compression_ratio: float) -> float:
    return max(0.0, min(20.0, 20.0 * (1.0 - compression_ratio)))


def _proximity_score(price: float, intraday: IntradayMetrics) -> float:
    distance_pct = min(
        _distance_pct(price, intraday.orb_high),
        _distance_pct(price, intraday.orb_low),
        _distance_pct(price, intraday.vwap),
        _distance_pct(price, intraday.pdh),
        _distance_pct(price, intraday.pdl),
    )
    return max(0.0, min(20.0, 20.0 * (1.0 - (distance_pct / 0.01))))


def _momentum_score(volume_ratio: float, first_expansion: bool) -> float:
    if volume_ratio > 1.5:
        score = 20.0
    elif volume_ratio > 1.2:
        score = 15.0
    else:
        score = 5.0
    if first_expansion:
        score += 5.0
    return min(20.0, score)


def _nearest_level(price: float, intraday: IntradayMetrics) -> str:
    distances = {
        "ORB": min(_distance_pct(price, intraday.orb_high), _distance_pct(price, intraday.orb_low)),
        "VWAP": _distance_pct(price, intraday.vwap),
        "PDH": _distance_pct(price, intraday.pdh),
        "PDL": _distance_pct(price, intraday.pdl),
    }
    return min(distances.items(), key=lambda item: (item[1], item[0]))[0]


def _compression_state(intraday: IntradayMetrics) -> str:
    if intraday.first_expansion:
        return "early expansion"
    if intraday.compression_ratio < 0.7:
        return "tight range"
    return "building compression"


def _breakout_confirmed(price: float, intraday: IntradayMetrics) -> bool:
    return price > intraday.orb_high or price < intraday.orb_low


def _infer_bias(price: float, derived: DerivedMetrics, intraday: IntradayMetrics) -> str:
    if intraday.lower_highs and not intraday.higher_lows:
        return "SHORT"
    if intraday.higher_lows and not intraday.lower_highs:
        return "LONG"
    if derived.ema_aligned_bear:
        return "SHORT"
    if derived.ema_aligned_bull:
        return "LONG"
    return "LONG" if _distance_pct(price, intraday.orb_high) <= _distance_pct(price, intraday.orb_low) else "SHORT"


def regime_bias(regime: Optional[RegimeState]) -> str:
    if regime is None:
        return "N/A"
    if regime.regime == RISK_ON:
        return "LONG"
    if regime.regime == RISK_OFF:
        return "SHORT"
    if regime.regime == NEUTRAL:
        if regime.net_score > 0:
            return "LONG"
        if regime.net_score < 0:
            return "SHORT"
        return "BALANCED"
    if regime.regime == CHAOTIC:
        return "NO TRADE"
    return "N/A"


def _execution_posture(regime: Optional[RegimeState]) -> str:
    if regime is None:
        return "No Trade"
    if regime.regime == CHAOTIC or regime.posture == "STAY_FLAT":
        return "No Trade"
    return "A+ Only"
