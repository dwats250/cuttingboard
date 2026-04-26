"""
Tests for PRD-023 — GLD–DXY Correlation Policy Layer.

Covers: ALIGNED, NEUTRAL (flat + missing + stale), CONFLICT, determinism (AC1–AC8).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cuttingboard import config
from cuttingboard.correlation import (
    ALIGNED,
    CONFLICT,
    NEUTRAL,
    CorrelationResult,
    _direction,
    compute_correlation,
)
from cuttingboard.normalization import NormalizedQuote

_NOW = datetime(2026, 4, 23, 14, 0, 0, tzinfo=timezone.utc)


def _quote(symbol: str, pct: float, age: float = 0.0) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=100.0,
        pct_change_decimal=pct,
        volume=1_000_000.0,
        fetched_at_utc=_NOW,
        source="yfinance",
        units="usd_price",
        age_seconds=age,
    )


def _quotes(gld_pct: float, dxy_pct: float) -> dict[str, NormalizedQuote]:
    return {
        "GLD":      _quote("GLD",      gld_pct),
        "DX-Y.NYB": _quote("DX-Y.NYB", dxy_pct),
    }


# ---------------------------------------------------------------------------
# Direction helper
# ---------------------------------------------------------------------------

class TestDirection:
    def test_positive_pct_returns_plus_one(self):
        assert _direction(_quote("GLD", 0.01)) == 1

    def test_negative_pct_returns_minus_one(self):
        assert _direction(_quote("GLD", -0.01)) == -1

    def test_zero_pct_returns_zero(self):
        assert _direction(_quote("GLD", 0.0)) == 0

    def test_none_returns_zero(self):
        assert _direction(None) == 0

    def test_stale_returns_zero(self):
        stale = _quote("GLD", 0.02, age=config.FRESHNESS_SECONDS + 1)
        assert _direction(stale) == 0

    def test_fresh_at_boundary_returns_direction(self):
        fresh = _quote("GLD", 0.02, age=config.FRESHNESS_SECONDS - 1)
        assert _direction(fresh) == 1


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

class TestAlignment:
    def test_gld_up_dxy_down_is_aligned(self):
        result = compute_correlation(_quotes(0.01, -0.005))
        assert result.state == ALIGNED

    def test_gld_down_dxy_up_is_aligned(self):
        result = compute_correlation(_quotes(-0.01, 0.005))
        assert result.state == ALIGNED

    def test_score_is_plus_one(self):
        result = compute_correlation(_quotes(0.01, -0.005))
        assert result.score == 1

    def test_risk_modifier_is_one(self):
        result = compute_correlation(_quotes(0.01, -0.005))
        assert result.risk_modifier == config.CORRELATION_RISK_MODIFIER_ALIGNED


class TestConflict:
    def test_both_up_is_conflict(self):
        result = compute_correlation(_quotes(0.01, 0.005))
        assert result.state == CONFLICT

    def test_both_down_is_conflict(self):
        result = compute_correlation(_quotes(-0.01, -0.005))
        assert result.state == CONFLICT

    def test_score_is_minus_one(self):
        result = compute_correlation(_quotes(0.01, 0.005))
        assert result.score == -1

    def test_risk_modifier_is_reduced(self):
        result = compute_correlation(_quotes(0.01, 0.005))
        assert result.risk_modifier == config.CORRELATION_RISK_MODIFIER_CONFLICT


class TestNeutral:
    def test_gld_flat_is_neutral(self):
        result = compute_correlation(_quotes(0.0, 0.01))
        assert result.state == NEUTRAL

    def test_dxy_flat_is_neutral(self):
        result = compute_correlation(_quotes(0.01, 0.0))
        assert result.state == NEUTRAL

    def test_both_flat_is_neutral(self):
        result = compute_correlation(_quotes(0.0, 0.0))
        assert result.state == NEUTRAL

    def test_missing_gld_is_neutral(self):
        quotes = {"DX-Y.NYB": _quote("DX-Y.NYB", 0.01)}
        result = compute_correlation(quotes)
        assert result.state == NEUTRAL

    def test_missing_dxy_is_neutral(self):
        quotes = {"GLD": _quote("GLD", 0.01)}
        result = compute_correlation(quotes)
        assert result.state == NEUTRAL

    def test_empty_quotes_is_neutral(self):
        result = compute_correlation({})
        assert result.state == NEUTRAL

    def test_stale_gld_is_neutral(self):
        quotes = {
            "GLD":      _quote("GLD", 0.01, age=config.FRESHNESS_SECONDS + 1),
            "DX-Y.NYB": _quote("DX-Y.NYB", -0.005),
        }
        result = compute_correlation(quotes)
        assert result.state == NEUTRAL

    def test_stale_dxy_is_neutral(self):
        quotes = {
            "GLD":      _quote("GLD", 0.01),
            "DX-Y.NYB": _quote("DX-Y.NYB", -0.005, age=config.FRESHNESS_SECONDS + 1),
        }
        result = compute_correlation(quotes)
        assert result.state == NEUTRAL

    def test_score_is_zero(self):
        result = compute_correlation(_quotes(0.0, 0.01))
        assert result.score == 0

    def test_risk_modifier_is_reduced(self):
        result = compute_correlation(_quotes(0.0, 0.01))
        assert result.risk_modifier == config.CORRELATION_RISK_MODIFIER_NEUTRAL


# ---------------------------------------------------------------------------
# AC1 — Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_input_same_output_aligned(self):
        q = _quotes(0.01, -0.005)
        assert compute_correlation(q) == compute_correlation(q)

    def test_same_input_same_output_conflict(self):
        q = _quotes(0.01, 0.005)
        assert compute_correlation(q) == compute_correlation(q)

    def test_same_input_same_output_neutral(self):
        q = _quotes(0.0, 0.01)
        assert compute_correlation(q) == compute_correlation(q)


# ---------------------------------------------------------------------------
# AC2 — Correct symbols
# ---------------------------------------------------------------------------

def test_uses_gld_as_gold_proxy():
    result = compute_correlation(_quotes(0.01, -0.005))
    assert result.gold_symbol == "GLD"


def test_uses_dxy_as_dollar_proxy():
    result = compute_correlation(_quotes(0.01, -0.005))
    assert result.dollar_symbol == "DX-Y.NYB"


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------

def test_result_is_frozen_dataclass():
    result = compute_correlation(_quotes(0.01, -0.005))
    with pytest.raises((AttributeError, TypeError)):
        result.state = "SOMETHING"  # type: ignore[misc]


def test_result_fields_present():
    result = compute_correlation(_quotes(0.01, -0.005))
    assert isinstance(result, CorrelationResult)
    assert result.gold_symbol is not None
    assert result.dollar_symbol is not None
    assert result.state in (ALIGNED, NEUTRAL, CONFLICT)
    assert result.score in (-1, 0, 1)
    assert isinstance(result.risk_modifier, float)


# ---------------------------------------------------------------------------
# CORRELATION_ENABLED = False
# ---------------------------------------------------------------------------

def test_disabled_returns_neutral_with_full_modifier(monkeypatch):
    monkeypatch.setattr(config, "CORRELATION_ENABLED", False)
    result = compute_correlation(_quotes(0.01, 0.005))  # would be CONFLICT if enabled
    assert result.state == NEUTRAL
    assert result.score == 0
    assert result.risk_modifier == 1.0
