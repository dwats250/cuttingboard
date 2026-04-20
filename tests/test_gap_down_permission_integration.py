"""
Integration tests for gap-down short permission gate.

Prevents regression of the A-1 wiring bug: ensures that the intraday
permission gate is correctly wired into _apply_intraday_short_permission
for all observable failure modes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pandas as pd
import pytz
import pytest

from cuttingboard.normalization import NormalizedQuote
from cuttingboard.qualification import TradeCandidate
from cuttingboard.runtime import _apply_intraday_short_permission

ET = pytz.timezone("US/Eastern")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _et_ts(hour: int, minute: int) -> datetime:
    return ET.localize(datetime(2026, 4, 18, hour, minute, 0))


def _make_bar_df(rows: list[tuple]) -> pd.DataFrame:
    """rows: (hour, minute, open, high, low, close, volume)"""
    index, opens, highs, lows, closes, volumes = [], [], [], [], [], []
    for h, m, o, hi, lo, c, v in rows:
        index.append(_et_ts(h, m))
        opens.append(o)
        highs.append(hi)
        lows.append(lo)
        closes.append(c)
        volumes.append(v)
    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": volumes},
        index=index,
    )


# ORB_HIGH=455.0, ORB_LOW=453.0
_ORB_ROWS = [
    (9, 30, 455.0, 455.0, 453.0, 454.0, 2_000_000),
    (9, 31, 454.0, 454.5, 453.0, 453.5, 2_000_000),
    (9, 32, 453.5, 454.0, 453.0, 453.5, 2_000_000),
    (9, 33, 453.5, 454.0, 453.0, 453.0, 2_000_000),
    (9, 34, 453.0, 453.5, 453.0, 453.0, 2_000_000),
]

# 09:36–09:44: post-ORB, close=453.5 (inside ORB range, above ORB_LOW)
_NOISE_ROWS = [
    (9, m, 453.2, 453.5, 453.0, 453.5, 1_000_000)
    for m in range(36, 45)
]

# prev_close ≈ 460.0 → gap_pct ≈ -1.1% → gap_type="DOWN"
_GAP_DOWN_QUOTE = NormalizedQuote(
    symbol="TSLA",
    price=453.0,
    pct_change_decimal=-0.01522,
    volume=30_000_000.0,
    fetched_at_utc=datetime(2026, 4, 18, 14, 0, 0, tzinfo=timezone.utc),
    source="yfinance",
    units="USD",
    age_seconds=60.0,
)

_SHORT_CANDIDATE = TradeCandidate(
    symbol="TSLA",
    direction="SHORT",
    entry_price=452.8,
    stop_price=455.5,
    target_price=445.0,
    spread_width=3.0,
)


# ---------------------------------------------------------------------------
# CASE 1 — Gap-down, no permission
# ---------------------------------------------------------------------------

def test_case1_gap_down_no_permission_blocks_short():
    """1 close below ORB_LOW → acceptance=0 → SHORT suppressed."""
    rows = _ORB_ROWS + _NOISE_ROWS + [
        (9, 45, 452.9, 452.9, 452.5, 452.8, 2_500_000),
    ]
    df = _make_bar_df(rows)

    with patch("cuttingboard.runtime.fetch_intraday_bars", return_value=df):
        filtered, context = _apply_intraday_short_permission(
            {"TSLA": _SHORT_CANDIDATE}, {"TSLA": _GAP_DOWN_QUOTE}
        )

    assert "TSLA" not in filtered
    assert context["TSLA"]["intraday_state_available"] is True
    assert context["TSLA"]["downside_permission"] is False


# ---------------------------------------------------------------------------
# CASE 2 — Gap-down, permission granted
# ---------------------------------------------------------------------------

def test_case2_gap_down_acceptance_allows_short():
    """2 contiguous closes below ORB_LOW → acceptance confirmed → SHORT allowed."""
    rows = _ORB_ROWS + _NOISE_ROWS + [
        (9, 45, 452.9, 452.9, 452.5, 452.8, 2_500_000),
        (9, 46, 452.9, 452.9, 452.5, 452.8, 2_500_000),
    ]
    df = _make_bar_df(rows)

    with patch("cuttingboard.runtime.fetch_intraday_bars", return_value=df):
        filtered, context = _apply_intraday_short_permission(
            {"TSLA": _SHORT_CANDIDATE}, {"TSLA": _GAP_DOWN_QUOTE}
        )

    assert "TSLA" in filtered
    assert context["TSLA"]["intraday_state_available"] is True
    assert context["TSLA"]["downside_permission"] is True


# ---------------------------------------------------------------------------
# CASE 3 — Intraday state unavailable (fail-open)
# ---------------------------------------------------------------------------

def test_case3_state_unavailable_fails_open():
    """When compute_intraday_state raises, SHORT is kept (fail-open)."""
    rows = _ORB_ROWS + _NOISE_ROWS + [
        (9, 45, 452.9, 452.9, 452.5, 452.8, 2_500_000),
    ]
    df = _make_bar_df(rows)

    with patch("cuttingboard.runtime.fetch_intraday_bars", return_value=df), \
         patch("cuttingboard.runtime.compute_intraday_state",
               side_effect=Exception("simulated failure")):
        filtered, context = _apply_intraday_short_permission(
            {"TSLA": _SHORT_CANDIDATE}, {"TSLA": _GAP_DOWN_QUOTE}
        )

    assert "TSLA" in filtered
    assert context["TSLA"]["intraday_state_available"] is False
    assert "downside_permission" not in context["TSLA"]


# ---------------------------------------------------------------------------
# CASE 4 — Sparse bars (non-contiguous)
# ---------------------------------------------------------------------------

def test_case4_sparse_bars_blocks_short():
    """3-minute gap between last 2 bars → contiguity violated → acceptance=0 → SHORT blocked."""
    rows = _ORB_ROWS + _NOISE_ROWS + [
        (9, 45, 452.9, 452.9, 452.5, 452.8, 2_500_000),
        (9, 48, 452.9, 452.9, 452.5, 452.8, 2_500_000),  # 3-min gap > 2-min tolerance
    ]
    df = _make_bar_df(rows)

    with patch("cuttingboard.runtime.fetch_intraday_bars", return_value=df):
        filtered, context = _apply_intraday_short_permission(
            {"TSLA": _SHORT_CANDIDATE}, {"TSLA": _GAP_DOWN_QUOTE}
        )

    assert "TSLA" not in filtered
    assert context["TSLA"]["intraday_state_available"] is True
    assert context["TSLA"]["downside_permission"] is False
