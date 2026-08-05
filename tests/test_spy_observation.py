"""PRD-288 — transient SPY session observation (NS-2A/NS-2C).

Discriminating tests T1-T10 (T5/T11 are the runtime end-to-end tests in
test_runtime_decision.py; T12 is the payload/renderer scope-out). Each guard
ships its reddening test per the MUTATION PLAN.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from cuttingboard import ingestion
from cuttingboard.spy_observation import (
    OBSERVED,
    PRE_OPEN,
    STALE,
    UNAVAILABLE,
    SpyObservation,
    build_spy_observation,
)
from cuttingboard.watch import OrbObservation


def _utc_frame(start_utc: str, highs, lows, closes, vols) -> pd.DataFrame:
    """UTC-indexed 1-minute OHLCV frame (the shape the full-session fetch returns)."""
    idx = pd.date_range(start_utc, periods=len(closes), freq="1min", tz="UTC")
    return pd.DataFrame(
        {"Open": closes, "High": highs, "Low": lows, "Close": closes, "Volume": vols},
        index=idx,
    )


def _formed_orb() -> OrbObservation:
    return OrbObservation(state="FORMED", orb_high=105.0, orb_low=100.0)


# --- T1: healthy current session -> OBSERVED, 09:30-anchored typical-price VWAP ---
def test_t1_healthy_session_observed():
    # 5 bars 09:30-09:34 ET (13:30-13:34 UTC, EDT) on 2026-04-28.
    frame = _utc_frame(
        "2026-04-28 13:30",
        highs=[101, 102, 103, 104, 105.0],
        lows=[99, 100, 101, 102, 103.0],
        closes=[100, 101, 102, 103, 104.0],
        vols=[1000] * 5,
    )
    run_at = datetime(2026, 4, 28, 13, 34, 30, tzinfo=timezone.utc)  # 30 s after last bar
    orb = _formed_orb()
    obs = build_spy_observation(run_at_utc=run_at, session_frame=frame, orb=orb, halted=False)

    assert obs.state == OBSERVED
    assert obs.observed_symbol == "SPY"
    # equal volume -> VWAP is the mean typical price; TP per bar == its close here.
    assert obs.session_vwap == pytest.approx(102.0)
    assert obs.current_price == 104.0
    assert obs.price_vs_vwap == "ABOVE"
    assert obs.observed_at_utc == frame.index[-1].to_pydatetime()
    assert obs.orb is orb  # verbatim projection


# --- T2: stale prior session, post-open -> STALE / session_mismatch, no live values ---
def test_t2_stale_prior_session():
    frame = _utc_frame(
        "2026-04-27 13:30",  # prior session (04-27)
        highs=[101.0], lows=[99.0], closes=[100.0], vols=[1000],
    )
    run_at = datetime(2026, 4, 28, 14, 0, tzinfo=timezone.utc)  # 10:00 ET, session should be live
    obs = build_spy_observation(run_at_utc=run_at, session_frame=frame, orb=_formed_orb(), halted=False)

    assert obs.state == STALE
    assert obs.reason == "session_mismatch"
    assert obs.session_vwap is None
    assert obs.current_price is None
    assert obs.price_vs_vwap is None


# --- T3: pre-open (both variants) -> PRE_OPEN, no invented value, no error ---
def test_t3_pre_open_prior_session():
    frame = _utc_frame("2026-04-27 13:30", highs=[101.0], lows=[99.0], closes=[100.0], vols=[1000])
    run_at = datetime(2026, 4, 28, 13, 20, tzinfo=timezone.utc)  # 09:20 ET <= 09:35
    obs = build_spy_observation(run_at_utc=run_at, session_frame=frame, orb=_formed_orb(), halted=False)
    assert obs.state == PRE_OPEN
    assert obs.reason == "pre_open_prior_session"
    assert obs.session_vwap is None and obs.current_price is None


def test_t3_pre_open_same_session_before_open():
    frame = _utc_frame("2026-04-28 13:30", highs=[101.0], lows=[99.0], closes=[100.0], vols=[1000])
    run_at = datetime(2026, 4, 28, 13, 25, tzinfo=timezone.utc)  # 09:25 ET < 09:30
    obs = build_spy_observation(run_at_utc=run_at, session_frame=frame, orb=_formed_orb(), halted=False)
    assert obs.state == PRE_OPEN
    assert obs.reason == "pre_open"


# --- T4: fetch failure / insufficient bars -> UNAVAILABLE, no fabricated value ---
def test_t4_fetch_failure_none_frame():
    run_at = datetime(2026, 4, 28, 14, 0, tzinfo=timezone.utc)
    obs = build_spy_observation(run_at_utc=run_at, session_frame=None, orb=None, halted=False)
    assert obs.state == UNAVAILABLE
    assert obs.reason == "intraday_fetch_failed"
    assert obs.session_vwap is None and obs.current_price is None and obs.observed_at_utc is None


def test_t4_insufficient_bars_empty_frame():
    run_at = datetime(2026, 4, 28, 14, 0, tzinfo=timezone.utc)
    empty = _utc_frame("2026-04-28 13:30", highs=[], lows=[], closes=[], vols=[])
    obs = build_spy_observation(run_at_utc=run_at, session_frame=empty, orb=None, halted=False)
    assert obs.state == UNAVAILABLE
    assert obs.reason == "insufficient_bars"


# --- T6 (unit): halted run -> UNAVAILABLE / system_halted, no value, ORB UNAVAILABLE ---
def test_t6_halt_unit():
    run_at = datetime(2026, 4, 28, 14, 0, tzinfo=timezone.utc)
    frame = _utc_frame("2026-04-28 13:30", highs=[101.0], lows=[99.0], closes=[100.0], vols=[1000])
    obs = build_spy_observation(run_at_utc=run_at, session_frame=frame, orb=_formed_orb(), halted=True)
    assert obs.state == UNAVAILABLE
    assert obs.reason == "system_halted"
    assert obs.session_vwap is None and obs.current_price is None
    assert obs.orb is None  # ORB reports UNAVAILABLE on a halt


# --- T7: long session (>120 bars) -> VWAP truthful across the WHOLE session ---
def test_t7_full_session_vwap_beats_rolling_tail():
    # 30 low-price bars then 120 high-price bars; the full-session VWAP (82.0)
    # differs from the last-120 rolling-tail VWAP (100.0), so a rolling-tail
    # anchoring mutation reddens this test.
    highs = [10.0] * 30 + [100.0] * 120
    lows = [10.0] * 30 + [100.0] * 120
    closes = [10.0] * 30 + [100.0] * 120
    vols = [1000] * 150
    frame = _utc_frame("2026-04-28 13:30", highs=highs, lows=lows, closes=closes, vols=vols)
    last_bar = frame.index[-1].to_pydatetime()
    run_at = last_bar.replace(second=30)
    obs = build_spy_observation(run_at_utc=run_at, session_frame=frame, orb=_formed_orb(), halted=False)
    assert obs.state == OBSERVED
    assert obs.session_vwap == pytest.approx((30 * 10.0 + 120 * 100.0) / 150)  # 82.0
    assert obs.session_vwap != pytest.approx(100.0)


# --- T8: full-session fetch boundary + non-leak (opt-in path vs default tail) ---
def test_t8_full_session_fetch_boundary_and_non_leak(monkeypatch):
    # One session 09:30-16:00 ET == 13:30-20:00 UTC (EDT). Naive UTC index.
    idx = pd.date_range("2026-04-28 13:30", "2026-04-28 20:00", freq="1min")
    df = pd.DataFrame(
        {
            "Open": range(len(idx)),
            "High": range(len(idx)),
            "Low": range(len(idx)),
            "Close": range(len(idx)),
            "Volume": [100] * len(idx),
        },
        index=idx,
    )
    monkeypatch.setattr(ingestion.yf, "download", lambda *a, **k: df.copy())

    session = ingestion.fetch_intraday_session_bars("SPY")
    default = ingestion.fetch_intraday_bars("SPY")

    # Default path: contiguous last-120, clipped to the 15:30 ET bound.
    assert len(default) == 120
    default_et = default.index.tz_convert("America/New_York")
    assert default_et[-1].strftime("%H:%M") == "15:30"

    # Full-session path: complete 09:30-16:00 ET session, no tail truncation.
    assert len(session) > 120
    session_et = session.index.tz_convert("America/New_York")
    assert session_et[0].strftime("%H:%M") == "09:30"
    assert session_et[-1].strftime("%H:%M") == "16:00"  # 15:30-16:00 retained (would be dropped by the default bound)


# --- T9: zero-volume session -> OBSERVED, session_vwap None, price_vs_vwap UNAVAILABLE ---
def test_t9_zero_volume_session():
    frame = _utc_frame(
        "2026-04-28 13:30",
        highs=[101, 102, 103.0], lows=[99, 100, 101.0], closes=[100, 101, 102.0],
        vols=[0, 0, 0],
    )
    run_at = datetime(2026, 4, 28, 13, 33, tzinfo=timezone.utc)
    obs = build_spy_observation(run_at_utc=run_at, session_frame=frame, orb=_formed_orb(), halted=False)
    assert obs.state == OBSERVED
    assert obs.session_vwap is None  # not seeded from the last close
    assert obs.price_vs_vwap == "UNAVAILABLE"
    assert obs.current_price == 102.0  # current price still present


# --- T10: one ORB truth -> the projected ORB is the SAME object, never recomputed ---
def test_t10_one_orb_truth_verbatim_projection():
    frame = _utc_frame("2026-04-28 13:30", highs=[101.0], lows=[99.0], closes=[100.0], vols=[1000])
    run_at = datetime(2026, 4, 28, 13, 30, 30, tzinfo=timezone.utc)
    orb = _formed_orb()
    obs = build_spy_observation(run_at_utc=run_at, session_frame=frame, orb=orb, halted=False)
    assert obs.orb is orb
    assert obs.orb.orb_high == 105.0 and obs.orb.orb_low == 100.0


# --- Value-emission invariant: current_price/price_vs_vwap non-None IFF OBSERVED ---
def test_value_emission_invariant_non_observed_states_null():
    run_at = datetime(2026, 4, 28, 14, 0, tzinfo=timezone.utc)
    for obs in (
        build_spy_observation(run_at_utc=run_at, session_frame=None, orb=None, halted=False),
        build_spy_observation(
            run_at_utc=run_at,
            session_frame=_utc_frame("2026-04-27 13:30", highs=[101.0], lows=[99.0], closes=[100.0], vols=[1000]),
            orb=None, halted=False,
        ),
    ):
        if obs.state != OBSERVED:
            assert obs.current_price is None
            assert obs.price_vs_vwap is None
            assert obs.session_vwap is None


def test_spy_observation_is_frozen():
    obs = build_spy_observation(
        run_at_utc=datetime(2026, 4, 28, 14, 0, tzinfo=timezone.utc),
        session_frame=None, orb=None, halted=True,
    )
    assert isinstance(obs, SpyObservation)
    with pytest.raises(Exception):
        obs.state = "MUTATED"  # frozen dataclass
