"""PRD-190 R5: OHLCV cache must be shape-aware, not only age-aware.

A fresh-but-short cached frame (fetched under a narrower OHLCV_FETCH_MONTHS) must
be treated as stale so a window bump (6 -> 12 months) actually takes effect on
the first post-bump run instead of serving a ~126-bar frame that can never
satisfy SMA-200.
"""

from __future__ import annotations

import pandas as pd
import pytest

from cuttingboard import config, ingestion


def _recent_daily(n_bars: int) -> pd.DataFrame:
    """Daily OHLCV frame whose last bar is ~now (age-fresh), n_bars deep."""
    last = pd.Timestamp.now(tz="UTC")
    idx = pd.date_range(end=last, periods=n_bars, freq="D")
    closes = [100.0] * n_bars
    return pd.DataFrame(
        {
            "Open": closes,
            "High": [c * 1.01 for c in closes],
            "Low": [c * 0.99 for c in closes],
            "Close": closes,
            "Volume": [1_000_000.0] * n_bars,
        },
        index=idx,
    )


def test_min_fresh_bars_is_the_sma200_consumer_window():
    # The floor is the longest consumer window (SMA-200), NOT the fetch target.
    assert ingestion._ohlcv_min_fresh_bars() == 200


def test_min_fresh_bars_is_config_independent(monkeypatch):
    # Tied to the analytic requirement, not OHLCV_FETCH_MONTHS — so a slightly
    # short (holiday-dense) full-window fetch can never spin a re-fetch loop.
    monkeypatch.setattr(config, "OHLCV_FETCH_MONTHS", 6)
    assert ingestion._ohlcv_min_fresh_bars() == 200
    monkeypatch.setattr(config, "OHLCV_FETCH_MONTHS", 24)
    assert ingestion._ohlcv_min_fresh_bars() == 200


def test_fresh_cache_rejects_pre_bump_short_frame():
    # 126 bars (~6-month fetch) is age-fresh but below the 200-bar SMA-200 floor.
    assert ingestion._is_fresh_ohlcv_cache(_recent_daily(126)) is False


def test_fresh_cache_accepts_full_window_frame():
    # ~252 bars (~12-month fetch), age-fresh, clears the 200 floor.
    assert ingestion._is_fresh_ohlcv_cache(_recent_daily(252)) is True


def test_holiday_shortened_full_window_frame_is_fresh_no_refetch_loop():
    # The anti-loop guarantee: a 12-month fetch trimmed by a holiday-dense year
    # (~248 bars) still clears the 200-bar consumer floor, so it is NOT marked
    # stale — there is no fetch -> short -> stale -> fetch loop. Boundary: 200
    # bars exactly is fresh (sma_200 needs len >= 200), 199 is stale.
    assert ingestion._is_fresh_ohlcv_cache(_recent_daily(248)) is True
    assert ingestion._is_fresh_ohlcv_cache(_recent_daily(200)) is True
    assert ingestion._is_fresh_ohlcv_cache(_recent_daily(199)) is False


def test_fetch_ohlcv_refetches_when_cached_frame_is_short(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "OHLCV_FETCH_MONTHS", 12)
    cache_path = tmp_path / "SPY_ohlcv.parquet"
    _recent_daily(126).to_parquet(cache_path)
    monkeypatch.setattr(ingestion, "_ohlcv_cache_path", lambda _s: cache_path)

    full = _recent_daily(252)
    calls = {"n": 0}

    def _fake_fetch(_symbol):
        calls["n"] += 1
        return full

    monkeypatch.setattr(ingestion, "_fetch_ohlcv_from_yfinance", _fake_fetch)

    out = ingestion.fetch_ohlcv("SPY")
    assert calls["n"] == 1                 # the short cache forced a live refresh
    assert out is not None and len(out) == 252


def test_fetch_ohlcv_serves_full_cache_without_refetch(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "OHLCV_FETCH_MONTHS", 12)
    cache_path = tmp_path / "SPY_ohlcv.parquet"
    _recent_daily(252).to_parquet(cache_path)
    monkeypatch.setattr(ingestion, "_ohlcv_cache_path", lambda _s: cache_path)

    def _must_not_fetch(_symbol):
        raise AssertionError("live fetch attempted despite a full fresh cache")

    monkeypatch.setattr(ingestion, "_fetch_ohlcv_from_yfinance", _must_not_fetch)

    out = ingestion.fetch_ohlcv("SPY")
    assert out is not None and len(out) == 252
