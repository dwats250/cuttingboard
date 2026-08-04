from datetime import date, datetime, timezone

import pandas as pd
import pytest

from cuttingboard.derived import DerivedMetrics
from cuttingboard.ingestion import MAX_INTRADAY_RETURN_BARS, _retain_session_frame
from cuttingboard.regime import AGGRESSIVE_LONG, RegimeState, RISK_ON
from cuttingboard.structure import NORMAL_IV, StructureResult, TREND
from cuttingboard.watch import (
    EASTERN_TZ,
    MORNING,
    ORB_FORMED,
    ORB_FORMING,
    ORB_INVALID,
    ORB_PRE_OPEN,
    ORB_UNAVAILABLE,
    POWER_HOUR,
    WatchItem,
    _session_orb,
    classify_watchlist,
    compute_intraday_metrics,
    get_session_phase,
)


def _utc_open(trading_day: str = "2026-04-15") -> pd.Timestamp:
    """09:30 ET as a UTC timestamp for an EDT trading day (13:30 UTC)."""
    return pd.Timestamp(f"{trading_day} 09:30:00", tz=EASTERN_TZ).tz_convert("UTC")


def _session_df(
    *,
    trading_day: str = "2026-04-15",
    n_post: int = 355,
    formation_high: float = 110.0,
    formation_low: float = 100.0,
    post_high: float = 777.0,
    post_low: float = 776.0,
    formation_bars: int = 6,
) -> pd.DataFrame:
    """Build a UTC-indexed single-session 1-minute frame.

    The 09:30-09:35 ET formation window carries ``formation_high``/``low``; every
    later bar carries the (deliberately different) ``post_high``/``low`` so a
    positional slice of the tail would produce the wrong ORB. Default size
    (6 + 355 = 361) is a full regular session.
    """
    start = _utc_open(trading_day)
    total = formation_bars + n_post
    idx = pd.date_range(start, periods=total, freq="1min")
    rows = []
    for i in range(total):
        hi, lo = (formation_high, formation_low) if i < formation_bars else (post_high, post_low)
        rows.append({"Open": lo, "High": hi, "Low": lo, "Close": (hi + lo) / 2, "Volume": 100.0})
    return pd.DataFrame(rows, index=idx)


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
    # PRD-271 / CB-07: ORB is the 09:30-09:35 ET formation window (13:30-13:35
    # UTC = the first 6 bars of this EDT fixture), selected by timestamp — not a
    # positional slice.
    assert metrics.orb is not None
    assert metrics.orb.state == ORB_FORMED
    assert metrics.orb.trading_date == date(2026, 4, 15)
    assert metrics.orb_high == pytest.approx(100.20)
    assert metrics.orb_low == 100.0
    assert metrics.orb.orb_high == pytest.approx(100.20)
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


def _bar(hi: float, lo: float, vol: float = 100.0) -> dict:
    return {"Open": lo, "High": hi, "Low": lo, "Close": (hi + lo) / 2, "Volume": vol}


def test_full_session_orb_uses_open_not_positional_tail():
    # 361-bar full session: opening range high=110, mid/late bars high=777. A
    # positional bars[:5] over the tail window would return 777; the
    # session-scoped producer must return the true 09:30-09:35 open (110).
    df = _session_df()
    metrics = compute_intraday_metrics(
        "SPY",
        intraday_fetcher=lambda symbol: df,
        daily_fetcher=lambda symbol: _daily_frame(),
        asof=datetime(2026, 4, 15, 15, 0, tzinfo=timezone.utc),
    )
    assert metrics is not None
    assert metrics.orb is not None
    assert metrics.orb.state == ORB_FORMED
    assert metrics.orb_high == pytest.approx(110.0)
    assert metrics.orb_low == pytest.approx(100.0)
    assert metrics.orb_high != pytest.approx(777.0)


def test_retention_preserves_opening_range_bars():
    # Eastern-time single-session frame longer than the rolling window: the
    # plain tail would evict the 09:30 open, retention must keep it.
    start_et = pd.Timestamp("2026-04-15 09:30:00", tz=EASTERN_TZ)
    idx = pd.date_range(start_et, periods=200, freq="1min")
    frame = pd.DataFrame([_bar(101.0, 100.0) for _ in range(200)], index=idx)

    retained = _retain_session_frame(frame)
    open_utc = start_et.tz_convert("UTC")
    # The opening bar survives retention...
    assert open_utc in retained.index
    # ...even though the ordinary tail(120) would have dropped it.
    assert start_et not in frame.tail(MAX_INTRADAY_RETURN_BARS).index
    # All six 09:30-09:35 ET formation bars are retained.
    window_utc = pd.date_range(open_utc, periods=6, freq="1min")
    assert all(ts in retained.index for ts in window_utc)


def test_missing_formation_bars_report_unavailable_not_fabricated():
    # A frame with no 09:30-09:35 bars (e.g. tail-only, no retention) must
    # report UNAVAILABLE and fabricate no high/low.
    start = pd.Timestamp("2026-04-15 09:40:00", tz=EASTERN_TZ).tz_convert("UTC")
    idx = pd.date_range(start, periods=130, freq="1min")
    df = pd.DataFrame([_bar(101.0, 100.0) for _ in range(130)], index=idx)

    orb = _session_orb(df, asof=datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc))
    assert orb.state == ORB_UNAVAILABLE
    assert orb.orb_high is None and orb.orb_low is None


def test_current_session_formed_accepted():
    df = _session_df(n_post=60)
    orb = _session_orb(df, asof=datetime(2026, 4, 15, 14, 0, tzinfo=timezone.utc))
    assert orb.state == ORB_FORMED
    assert orb.trading_date == date(2026, 4, 15)
    assert orb.orb_high == pytest.approx(110.0)
    assert orb.observed_at_utc is not None


def test_prior_session_orb_is_invalid_session_mismatch():
    # A fully-formed prior-session frame consumed as if it were today's session
    # must fail provenance (INVALID), not leak a stale ORB.
    df = _session_df(trading_day="2026-04-14", n_post=60)
    metrics = compute_intraday_metrics(
        "SPY",
        intraday_fetcher=lambda symbol: df,
        daily_fetcher=lambda symbol: _daily_frame(),
        asof=datetime(2026, 4, 15, 14, 0, tzinfo=timezone.utc),
    )
    assert metrics is not None
    assert metrics.orb is not None
    assert metrics.orb.state == ORB_INVALID
    assert metrics.orb.reason == "session_mismatch"
    assert metrics.orb_high is None and metrics.orb_low is None


def test_malformed_bounds_are_invalid():
    df = _session_df(formation_high=100.0, formation_low=110.0, n_post=20)
    orb = _session_orb(df, asof=None)
    assert orb.state == ORB_INVALID
    assert orb.reason == "impossible_bounds"
    assert orb.orb_high is None


def test_mixed_session_formation_bars_are_invalid():
    d1 = pd.date_range(pd.Timestamp("2026-04-14 09:30:00", tz=EASTERN_TZ), periods=3, freq="1min")
    d2 = pd.date_range(pd.Timestamp("2026-04-15 09:30:00", tz=EASTERN_TZ), periods=6, freq="1min")
    idx = d1.append(d2).tz_convert("UTC")
    df = pd.DataFrame([_bar(110.0, 100.0) for _ in range(9)], index=idx)
    orb = _session_orb(df, asof=None)
    assert orb.state == ORB_INVALID
    assert orb.reason == "mixed_session"


def test_unordered_bars_are_invalid():
    df = _session_df(n_post=20).iloc[::-1]
    orb = _session_orb(df, asof=None)
    assert orb.state == ORB_INVALID
    assert orb.reason == "unordered_bars"


def test_pre_open_abstains_without_failure():
    start = pd.Timestamp("2026-04-15 09:25:00", tz=EASTERN_TZ).tz_convert("UTC")
    idx = pd.date_range(start, periods=4, freq="1min")
    df = pd.DataFrame([_bar(101.0, 100.0) for _ in range(4)], index=idx)
    orb = _session_orb(df, asof=datetime(2026, 4, 15, 13, 28, tzinfo=timezone.utc))
    assert orb.state == ORB_PRE_OPEN
    assert orb.orb_high is None


def test_forming_abstains_while_window_incomplete():
    start = _utc_open()
    idx = pd.date_range(start, periods=3, freq="1min")
    df = pd.DataFrame([_bar(110.0, 100.0) for _ in range(3)], index=idx)
    orb = _session_orb(df, asof=None)
    assert orb.state == ORB_FORMING
    assert orb.orb_high is None


def test_internal_watch_signals_none_safe_when_orb_absent():
    # UNAVAILABLE metrics must not crash the internal ORB-dependent signals and
    # must not surface ORB as the nearest level (no stale leak into scoring).
    from cuttingboard.watch import (
        _breakout_confirmed,
        _infer_bias,
        _nearest_level,
        _proximity_score,
    )

    start = pd.Timestamp("2026-04-15 09:40:00", tz=EASTERN_TZ).tz_convert("UTC")
    idx = pd.date_range(start, periods=150, freq="1min")
    df = pd.DataFrame([_bar(100.10 + i * 0.001, 100.0 + i * 0.001) for i in range(150)], index=idx)
    metrics = compute_intraday_metrics(
        "SPY",
        intraday_fetcher=lambda symbol: df,
        daily_fetcher=lambda symbol: _daily_frame(),
        asof=datetime(2026, 4, 15, 13, 30, tzinfo=timezone.utc),
    )
    assert metrics is not None
    assert metrics.orb.state == ORB_UNAVAILABLE
    assert metrics.orb_high is None

    price = metrics.bars[-1].close
    assert _breakout_confirmed(price, metrics) is False
    assert _nearest_level(price, metrics) != "ORB"
    # These must simply not raise when the ORB is absent.
    _proximity_score(price, metrics)
    _infer_bias(price, _derived(), metrics)
