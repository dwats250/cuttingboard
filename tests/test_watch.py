from datetime import datetime, timezone

import pandas as pd
import pytest

from cuttingboard.derived import DerivedMetrics
from cuttingboard.regime import AGGRESSIVE_LONG, RegimeState, RISK_ON
from cuttingboard.structure import NORMAL_IV, StructureResult, TREND
from cuttingboard.watch import (
    MORNING,
    POWER_HOUR,
    WatchItem,
    classify_watchlist,
    compute_intraday_metrics,
    get_session_phase,
)


def _intraday_frame() -> pd.DataFrame:
    idx = pd.date_range("2026-04-15 13:30:00+00:00", periods=25, freq="1min")
    rows = []
    for i in range(20):
        rows.append(
            {
                "Open": 100.0 + i * 0.02,
                "High": 100.1 + i * 0.02,
                "Low": 100.0 + i * 0.02,
                "Close": 100.08 + i * 0.02,
                "Volume": 100.0,
            }
        )

    tail = [
        {"Open": 100.48, "High": 100.50, "Low": 100.47, "Close": 100.49, "Volume": 100.0},
        {"Open": 100.49, "High": 100.51, "Low": 100.48, "Close": 100.50, "Volume": 100.0},
        {"Open": 100.50, "High": 100.52, "Low": 100.49, "Close": 100.51, "Volume": 100.0},
        {"Open": 100.51, "High": 100.53, "Low": 100.50, "Close": 100.52, "Volume": 100.0},
        {"Open": 100.52, "High": 100.54, "Low": 100.51, "Close": 100.53, "Volume": 220.0},
    ]
    rows.extend(tail)
    return pd.DataFrame(rows, index=idx)


def _daily_frame() -> pd.DataFrame:
    idx = pd.date_range("2026-04-14", periods=30, freq="1D")
    rows = [{"Open": 99.0, "High": 101.0, "Low": 98.0, "Close": 100.0, "Volume": 1000.0} for _ in idx]
    return pd.DataFrame(rows, index=idx)


def _derived() -> DerivedMetrics:
    now = datetime.now(timezone.utc)
    return DerivedMetrics(
        symbol="NVDA",
        ema9=100.50,
        ema21=100.20,
        ema50=99.50,
        ema_aligned_bull=True,
        ema_aligned_bear=False,
        ema_spread_pct=0.003,
        atr14=1.2,
        atr_pct=0.012,
        momentum_5d=0.03,
        volume_ratio=1.4,
        computed_at_utc=now,
        sufficient_history=True,
    )


def _structure() -> StructureResult:
    return StructureResult(
        symbol="NVDA",
        structure=TREND,
        iv_environment=NORMAL_IV,
        is_tradeable=True,
        disqualification_reason=None,
    )


def _regime() -> RegimeState:
    now = datetime(2026, 4, 15, 14, 15, tzinfo=timezone.utc)
    return RegimeState(
        regime=RISK_ON,
        posture=AGGRESSIVE_LONG,
        confidence=0.75,
        net_score=5,
        risk_on_votes=5,
        risk_off_votes=0,
        neutral_votes=3,
        total_votes=8,
        vote_breakdown={},
        vix_level=17.5,
        vix_pct_change=-0.02,
        computed_at_utc=now,
    )


def test_get_session_phase_boundaries():
    assert get_session_phase(datetime(2026, 4, 15, 13, 30, tzinfo=timezone.utc)) == MORNING
    assert get_session_phase(datetime(2026, 4, 15, 18, 30, tzinfo=timezone.utc)) == POWER_HOUR
    assert get_session_phase(datetime(2026, 4, 15, 21, 31, tzinfo=timezone.utc)) is None


def test_compute_intraday_metrics_deterministic_fields():
    metrics = compute_intraday_metrics(
        "NVDA",
        intraday_fetcher=lambda symbol: _intraday_frame(),
        daily_fetcher=lambda symbol: _daily_frame(),
    )

    assert metrics is not None
    assert len(metrics.bars) == 25
    assert metrics.orb_high == pytest.approx(100.18)
    assert metrics.orb_low == 100.0
    assert round(metrics.range_last_n, 2) == 0.07
    assert round(metrics.avg_range_prior, 2) == 0.10
    assert round(metrics.compression_ratio, 2) == 0.70
    assert round(metrics.volume_ratio, 2) == 2.08
    assert metrics.higher_lows is True
    assert metrics.lower_highs is False
    assert metrics.first_expansion is False


def test_classify_watchlist_ignores_failed_symbol_and_surfaces_watch():
    metrics = compute_intraday_metrics(
        "NVDA",
        intraday_fetcher=lambda symbol: _intraday_frame(),
        daily_fetcher=lambda symbol: _daily_frame(),
    )
    assert metrics is not None

    summary = classify_watchlist(
        {"NVDA": _structure()},
        {"NVDA": _derived()},
        {"NVDA": metrics},
        _regime(),
        asof=datetime(2026, 4, 15, 14, 15, tzinfo=timezone.utc),
        ignored_symbols=["AAPL"],
    )

    assert summary.session == MORNING
    assert summary.ignored_symbols == ["AAPL"]
    assert len(summary.watchlist) == 1
    item = summary.watchlist[0]
    assert isinstance(item, WatchItem)
    assert item.symbol == "NVDA"
    assert item.score >= 60
    assert "tighten range" in item.missing_conditions
    assert item.structure_note == "TREND near VWAP with building compression"
