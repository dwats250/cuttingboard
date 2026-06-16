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


def test_min_fresh_bars_scales_with_window(monkeypatch):
    monkeypatch.setattr(config, "OHLCV_FETCH_MONTHS", 12)
    assert ingestion._ohlcv_min_fresh_bars() == 12 * 19
    monkeypatch.setattr(config, "OHLCV_FETCH_MONTHS", 6)
    assert ingestion._ohlcv_min_fresh_bars() == 6 * 19


def test_fresh_cache_rejects_short_frame_under_wide_window(monkeypatch):
    # 126 bars (~6-month fetch) is age-fresh but below the 12-month floor (228).
    monkeypatch.setattr(config, "OHLCV_FETCH_MONTHS", 12)
    assert ingestion._is_fresh_ohlcv_cache(_recent_daily(126)) is False


def test_fresh_cache_accepts_full_window_frame(monkeypatch):
    # ~252 bars (~12-month fetch), age-fresh, clears the 228 floor.
    monkeypatch.setattr(config, "OHLCV_FETCH_MONTHS", 12)
    assert ingestion._is_fresh_ohlcv_cache(_recent_daily(252)) is True


def test_window_bump_flips_a_126_bar_cache_from_fresh_to_stale(monkeypatch):
    # The same on-disk 126-bar frame: fresh under 6mo, stale under 12mo. This is
    # exactly the stale-by-shape transition the PRD-190 bump must trigger.
    frame = _recent_daily(126)
    monkeypatch.setattr(config, "OHLCV_FETCH_MONTHS", 6)
    assert ingestion._is_fresh_ohlcv_cache(frame) is True
    monkeypatch.setattr(config, "OHLCV_FETCH_MONTHS", 12)
    assert ingestion._is_fresh_ohlcv_cache(frame) is False


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
