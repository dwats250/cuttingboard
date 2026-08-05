"""Transient SPY session observation carrier (PRD-288, NS-2A/NS-2C).

A read-only, non-persisted description of SPY's current session: session date,
freshness lifecycle, 09:30-anchored session VWAP + price-vs-VWAP relation, and
the current-session ORB projected VERBATIM from PRD-271's ``OrbObservation``.

Description, not prediction. This module touches no execution-adjacent surface:
it never recomputes an opening range, never mutates ``IntradayMetrics``, and
carries no durable/contract schema or cross-run persistence. The single reader
is the daily dashboard payload projection (``delivery/payload.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Optional

import pandas as pd

from cuttingboard.time_utils import convert_utc_to_et
from cuttingboard.watch import OrbObservation

# Observation/freshness states (distinct from the PRD-271 ORB axis).
PRE_OPEN = "PRE_OPEN"
OBSERVED = "OBSERVED"
STALE = "STALE"
UNAVAILABLE = "UNAVAILABLE"

# Freshness threshold: 2x the 60 s 1-minute-bar cadence plus one cadence of
# provider-lag margin. Deliberately NOT the 300 s quote-freshness / page-age
# constants (PRD-288 FRESHNESS SEMANTICS).
SPY_OBSERVATION_STALE_AFTER_SECONDS = 180

# Neutral price-vs-VWAP band (+/-10 bps), proposed for SPY intraday granularity;
# mirrors the sibling engine's ``_VWAP_BUFFER`` semantics, not silently inherited.
_VWAP_BAND = 0.001

# Observability floor: at least one regular-session bar to observe anything.
_MIN_OBSERVABLE_BARS = 1

_OBSERVED_SYMBOL = "SPY"
_TIMEZONE = "America/New_York"
_PRE_OPEN_CUTOFF_ET = time(9, 35)
_MARKET_OPEN_ET = time(9, 30)


@dataclass(frozen=True)
class SpyObservation:
    """Frozen, transient SPY session observation. Not persisted; not a schema."""

    observed_symbol: str
    intended_session_date: Optional[date]
    timezone: str
    observed_at_utc: Optional[datetime]
    state: str
    reason: Optional[str] = None
    session_vwap: Optional[float] = None
    current_price: Optional[float] = None
    price_vs_vwap: Optional[str] = None
    orb: Optional[OrbObservation] = None


def build_spy_observation(
    *,
    run_at_utc: datetime,
    session_frame: Optional[pd.DataFrame],
    orb: Optional[OrbObservation],
    halted: bool,
) -> SpyObservation:
    """Build the transient SPY observation for one daily run.

    Pure and side-effect-free. ``session_frame`` is the UTC-indexed SPY
    full-session frame (``None`` on fetch failure); ``orb`` is
    ``intraday_metrics["SPY"].orb`` projected verbatim (``None`` when absent).
    """
    if run_at_utc.tzinfo is None:
        run_at_utc = run_at_utc.replace(tzinfo=timezone.utc)
    intended_session_date = convert_utc_to_et(run_at_utc).date()
    now_et = convert_utc_to_et(run_at_utc)

    # 1. Halt: lifecycle truth, no fabricated value, ORB reports UNAVAILABLE.
    if halted:
        return _observation(intended_session_date, None, UNAVAILABLE,
                            reason="system_halted", orb=None)

    # 2. No frame / below the observability floor.
    if session_frame is None:
        return _observation(intended_session_date, None, UNAVAILABLE,
                            reason="intraday_fetch_failed", orb=orb)
    if len(session_frame) < _MIN_OBSERVABLE_BARS:
        return _observation(intended_session_date, None, UNAVAILABLE,
                            reason="insufficient_bars", orb=orb)

    observed_at_utc = session_frame.index[-1].to_pydatetime()
    trading_date = convert_utc_to_et(observed_at_utc).date()
    current_price = float(session_frame["Close"].iloc[-1])

    # 3. Frame is from a different session than intended.
    if trading_date != intended_session_date:
        if now_et.time() <= _PRE_OPEN_CUTOFF_ET:
            return _observation(intended_session_date, observed_at_utc, PRE_OPEN,
                                reason="pre_open_prior_session", orb=orb)
        return _observation(intended_session_date, observed_at_utc, STALE,
                            reason="session_mismatch", orb=orb)

    # 4. Frame is the intended session.
    if now_et.time() < _MARKET_OPEN_ET:
        return _observation(intended_session_date, observed_at_utc, PRE_OPEN,
                            reason="pre_open", orb=orb)
    age_seconds = (run_at_utc - observed_at_utc).total_seconds()
    if age_seconds > SPY_OBSERVATION_STALE_AFTER_SECONDS:
        return _observation(intended_session_date, observed_at_utc, STALE,
                            reason="observation_lag", orb=orb)

    # OBSERVED: emit VWAP (None on zero volume) and the price relation.
    session_vwap = _session_vwap(session_frame)
    price_vs_vwap = (
        "UNAVAILABLE" if session_vwap is None
        else _price_vs_vwap(current_price, session_vwap)
    )
    return _observation(
        intended_session_date, observed_at_utc, OBSERVED,
        session_vwap=session_vwap, current_price=current_price,
        price_vs_vwap=price_vs_vwap, orb=orb,
    )


def _observation(
    intended_session_date: Optional[date],
    observed_at_utc: Optional[datetime],
    state: str,
    *,
    reason: Optional[str] = None,
    session_vwap: Optional[float] = None,
    current_price: Optional[float] = None,
    price_vs_vwap: Optional[str] = None,
    orb: Optional[OrbObservation] = None,
) -> SpyObservation:
    return SpyObservation(
        observed_symbol=_OBSERVED_SYMBOL,
        intended_session_date=intended_session_date,
        timezone=_TIMEZONE,
        observed_at_utc=observed_at_utc,
        state=state,
        reason=reason,
        session_vwap=session_vwap,
        current_price=current_price,
        price_vs_vwap=price_vs_vwap,
        orb=orb,
    )


def _session_vwap(frame: pd.DataFrame) -> Optional[float]:
    """09:30-anchored cumulative typical-price VWAP: sum(TP*V)/sum(V).

    Zero-volume guard (fail-loud, PRD-198 #1): returns ``None`` when total
    session volume is 0 rather than seeding VWAP from the last close.
    """
    typical_price = (frame["High"] + frame["Low"] + frame["Close"]) / 3.0
    volume = frame["Volume"]
    total_volume = float(volume.sum())
    if total_volume == 0:
        return None
    return float((typical_price * volume).sum() / total_volume)


def _price_vs_vwap(current_price: float, session_vwap: float) -> str:
    if current_price > session_vwap * (1 + _VWAP_BAND):
        return "ABOVE"
    if current_price < session_vwap * (1 - _VWAP_BAND):
        return "BELOW"
    return "AT_LEVEL"
