"""Tests for PRD-107 trend structure snapshot builder."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pandas as pd
import pytest

from cuttingboard.normalization import NormalizedQuote
from cuttingboard.trend_structure import (
    SCHEMA_VERSION,
    SOURCE,
    build_trend_structure_snapshot,
)


def _quote(symbol: str, price: float) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=price,
        pct_change_decimal=0.0,
        volume=1_000_000.0,
        fetched_at_utc=datetime(2026, 5, 9, 14, 0, tzinfo=timezone.utc),
        source="yfinance",
        units="usd_price",
        age_seconds=10.0,
    )


def _daily_history(closes: list[float], volumes: list[float] | None = None) -> pd.DataFrame:
    n = len(closes)
    if volumes is None:
        volumes = [1_000_000.0] * n
    idx = pd.date_range(end="2026-05-08", periods=n, freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "Open": closes,
            "High": [c * 1.01 for c in closes],
            "Low": [c * 0.99 for c in closes],
            "Close": closes,
            "Volume": volumes,
        },
        index=idx,
    )


def _intraday_session(prices: list[float], volumes: list[float] | None = None) -> pd.DataFrame:
    n = len(prices)
    if volumes is None:
        volumes = [10_000.0] * n
    base = pd.Timestamp("2026-05-09 13:30", tz="UTC")
    idx = pd.DatetimeIndex([base + timedelta(minutes=i) for i in range(n)])
    return pd.DataFrame(
        {
            "Open": prices,
            "High": [p * 1.001 for p in prices],
            "Low": [p * 0.999 for p in prices],
            "Close": prices,
            "Volume": volumes,
        },
        index=idx,
    )


def test_schema_and_top_level_keys():
    out = build_trend_structure_snapshot({}, {}, [])
    assert out["schema_version"] == SCHEMA_VERSION
    assert out["source"] == SOURCE
    assert out["generated_at"] is None
    assert out["symbols"] == {}


def test_generated_at_iso_utc():
    ts = datetime(2026, 5, 9, 14, 0, tzinfo=timezone.utc)
    out = build_trend_structure_snapshot({}, {}, [], generated_at=ts)
    assert out["generated_at"] == ts.isoformat()


def test_generated_at_naive_rejected():
    with pytest.raises(ValueError):
        build_trend_structure_snapshot(
            {}, {}, [], generated_at=datetime(2026, 5, 9, 14, 0)
        )


def test_emits_one_record_per_symbol():
    out = build_trend_structure_snapshot({}, {}, ["SPY", "QQQ", "AAPL"])
    assert set(out["symbols"].keys()) == {"SPY", "QQQ", "AAPL"}


def test_missing_quote_yields_missing_record():
    out = build_trend_structure_snapshot({}, {}, ["SPY"])
    rec = out["symbols"]["SPY"]
    assert rec["data_status"] == "MISSING"
    assert rec["current_price"] is None
    assert rec["price_vs_vwap"] == "UNKNOWN"
    assert rec["price_vs_sma_50"] == "UNKNOWN"
    assert rec["price_vs_sma_200"] == "UNKNOWN"
    assert rec["trend_alignment"] == "UNKNOWN"
    assert rec["entry_context"] == "UNKNOWN"
    assert rec["reason"] == "current_price unavailable"


def test_missing_history_does_not_raise():
    quotes = {"SPY": _quote("SPY", 500.0)}
    out = build_trend_structure_snapshot(quotes, {}, ["SPY"])
    rec = out["symbols"]["SPY"]
    assert rec["current_price"] == 500.0
    assert rec["vwap"] is None
    assert rec["sma_50"] is None
    assert rec["sma_200"] is None
    assert rec["relative_volume"] is None
    assert rec["price_vs_vwap"] == "UNKNOWN"
    assert rec["price_vs_sma_50"] == "UNKNOWN"
    assert rec["price_vs_sma_200"] == "UNKNOWN"
    assert rec["trend_alignment"] == "UNKNOWN"
    assert rec["entry_context"] == "UNKNOWN"
    assert rec["data_status"] == "PARTIAL"


def test_bullish_aligned_fixture():
    closes = [100.0] * 200
    quotes = {"SPY": _quote("SPY", 150.0)}
    history = {"SPY": _daily_history(closes)}
    out = build_trend_structure_snapshot(quotes, history, ["SPY"])
    rec = out["symbols"]["SPY"]
    assert rec["sma_50"] == 100.0
    assert rec["sma_200"] == 100.0
    assert rec["price_vs_sma_50"] == "ABOVE"
    assert rec["price_vs_sma_200"] == "ABOVE"
    assert rec["trend_alignment"] == "BULLISH"


def test_bearish_aligned_fixture():
    closes = [100.0] * 200
    quotes = {"SPY": _quote("SPY", 80.0)}
    history = {"SPY": _daily_history(closes)}
    out = build_trend_structure_snapshot(quotes, history, ["SPY"])
    rec = out["symbols"]["SPY"]
    assert rec["price_vs_sma_50"] == "BELOW"
    assert rec["price_vs_sma_200"] == "BELOW"
    assert rec["trend_alignment"] == "BEARISH"


def test_mixed_alignment_fixture():
    # sma_50 = 300 (price below); sma_200 = 150 (price above) -> MIXED
    closes = [100.0] * 150 + [300.0] * 50
    quotes = {"SPY": _quote("SPY", 200.0)}
    history = {"SPY": _daily_history(closes)}
    out = build_trend_structure_snapshot(quotes, history, ["SPY"])
    rec = out["symbols"]["SPY"]
    assert rec["sma_50"] == 300.0
    assert rec["sma_200"] == 150.0
    assert rec["price_vs_sma_50"] == "BELOW"
    assert rec["price_vs_sma_200"] == "ABOVE"
    assert rec["trend_alignment"] == "MIXED"


def test_supportive_entry_context():
    daily_closes = [100.0] * 200
    intraday = _intraday_session([140.0, 141.0, 142.0, 143.0])
    full_history = pd.concat([_daily_history(daily_closes), intraday])
    quotes = {"SPY": _quote("SPY", 145.0)}
    out = build_trend_structure_snapshot(
        quotes, {"SPY": full_history}, ["SPY"]
    )
    rec = out["symbols"]["SPY"]
    assert rec["trend_alignment"] == "BULLISH"
    assert rec["price_vs_vwap"] == "ABOVE"
    assert rec["entry_context"] == "SUPPORTIVE"


def test_avoid_entry_context():
    daily_closes = [100.0] * 200
    intraday = _intraday_session([60.0, 59.0, 58.0, 57.0])
    full_history = pd.concat([_daily_history(daily_closes), intraday])
    quotes = {"SPY": _quote("SPY", 55.0)}
    out = build_trend_structure_snapshot(
        quotes, {"SPY": full_history}, ["SPY"]
    )
    rec = out["symbols"]["SPY"]
    assert rec["trend_alignment"] == "BEARISH"
    assert rec["price_vs_vwap"] == "BELOW"
    assert rec["entry_context"] == "AVOID"


def test_neutral_entry_context_when_mixed_signals():
    daily_closes = [100.0] * 200
    intraday = _intraday_session([130.0, 131.0, 132.0, 133.0])
    full_history = pd.concat([_daily_history(daily_closes), intraday])
    # bullish alignment but price below VWAP -> NEUTRAL
    quotes = {"SPY": _quote("SPY", 120.0)}
    out = build_trend_structure_snapshot(
        quotes, {"SPY": full_history}, ["SPY"]
    )
    rec = out["symbols"]["SPY"]
    assert rec["trend_alignment"] == "BULLISH"
    assert rec["price_vs_vwap"] == "BELOW"
    assert rec["entry_context"] == "NEUTRAL"


def test_data_status_ok_requires_all_three_refs():
    daily_closes = [100.0] * 200
    intraday = _intraday_session([105.0, 106.0])
    full_history = pd.concat([_daily_history(daily_closes), intraday])
    quotes = {"SPY": _quote("SPY", 110.0)}
    out = build_trend_structure_snapshot(
        quotes, {"SPY": full_history}, ["SPY"]
    )
    rec = out["symbols"]["SPY"]
    assert rec["data_status"] == "OK"


def test_data_status_partial_when_no_intraday():
    closes = [100.0] * 200
    quotes = {"SPY": _quote("SPY", 110.0)}
    history = {"SPY": _daily_history(closes)}
    out = build_trend_structure_snapshot(quotes, history, ["SPY"])
    rec = out["symbols"]["SPY"]
    assert rec["sma_50"] is not None
    assert rec["sma_200"] is not None
    assert rec["vwap"] is None
    assert rec["data_status"] == "PARTIAL"


def test_short_history_yields_null_smas_no_raise():
    closes = [100.0] * 30
    quotes = {"SPY": _quote("SPY", 110.0)}
    history = {"SPY": _daily_history(closes)}
    out = build_trend_structure_snapshot(quotes, history, ["SPY"])
    rec = out["symbols"]["SPY"]
    assert rec["sma_50"] is None
    assert rec["sma_200"] is None
    assert rec["data_status"] == "PARTIAL"


def test_no_at_enum_value():
    # exact equality must produce UNKNOWN, not "AT"
    closes = [100.0] * 200
    quotes = {"SPY": _quote("SPY", 100.0)}
    history = {"SPY": _daily_history(closes)}
    out = build_trend_structure_snapshot(quotes, history, ["SPY"])
    rec = out["symbols"]["SPY"]
    assert rec["price_vs_sma_50"] == "UNKNOWN"
    assert rec["price_vs_sma_200"] == "UNKNOWN"


def test_relative_volume_computed():
    closes = [100.0] * 30
    volumes = [1_000_000.0] * 29 + [3_000_000.0]
    quotes = {"SPY": _quote("SPY", 110.0)}
    history = {"SPY": _daily_history(closes, volumes)}
    out = build_trend_structure_snapshot(quotes, history, ["SPY"])
    assert out["symbols"]["SPY"]["relative_volume"] == pytest.approx(3.0)


def test_record_has_required_keys():
    quotes = {"SPY": _quote("SPY", 100.0)}
    out = build_trend_structure_snapshot(quotes, {}, ["SPY"])
    rec = out["symbols"]["SPY"]
    required = {
        "symbol", "data_status", "current_price", "vwap",
        "sma_50", "sma_200", "relative_volume",
        "price_vs_vwap", "price_vs_sma_50", "price_vs_sma_200",
        "trend_alignment", "entry_context", "reason",
    }
    assert required <= set(rec.keys())


def test_deterministic_output_same_inputs():
    closes = [100.0] * 200
    quotes = {"SPY": _quote("SPY", 110.0)}
    history = {"SPY": _daily_history(closes)}
    a = build_trend_structure_snapshot(quotes, history, ["SPY"])
    b = build_trend_structure_snapshot(quotes, history, ["SPY"])
    assert a == b


# ---------------------------------------------------------------------------
# PRD-110: curated trend-structure universe
# ---------------------------------------------------------------------------

_PRD110_EXPECTED = ("SPY", "QQQ", "GDX", "GLD", "SLV", "XLE")
_PRD110_BANNED = frozenset({
    "^VIX", "^TNX", "DX-Y.NYB", "BTC-USD",
    "IWM", "PAAS", "USO",
    "NVDA", "TSLA", "AAPL", "META", "AMZN", "COIN", "MSTR",
})


def test_prd110_constant_is_tuple_with_fixed_order():
    from cuttingboard import config

    assert isinstance(config.TREND_STRUCTURE_SYMBOLS, tuple)
    assert config.TREND_STRUCTURE_SYMBOLS == _PRD110_EXPECTED


def test_prd110_constant_subset_of_all_symbols():
    from cuttingboard import config

    assert set(config.TREND_STRUCTURE_SYMBOLS).issubset(set(config.ALL_SYMBOLS))


def test_prd110_constant_disjoint_from_non_tradables():
    from cuttingboard import config

    assert set(config.TREND_STRUCTURE_SYMBOLS).isdisjoint(config.NON_TRADABLE_SYMBOLS)
    assert set(config.TREND_STRUCTURE_SYMBOLS).isdisjoint(_PRD110_BANNED)


def test_prd110_runtime_helper_passes_curated_list(monkeypatch, tmp_path):
    """R2 + R5: writer passes list(config.TREND_STRUCTURE_SYMBOLS) as symbols=
    and the artifact symbol set equals the curated universe.

    Isolated fixture: monkeypatched LOGS_DIR/TREND_STRUCTURE_PATH and a builder
    spy. No live data, no network, no wall-clock dependency.
    """
    from cuttingboard import config, runtime

    captured: dict = {}

    def _spy(*, normalized_quotes, history_by_symbol, symbols, generated_at):
        captured["symbols"] = symbols
        captured["generated_at"] = generated_at
        return {
            "schema_version": 1,
            "generated_at": generated_at.isoformat(),
            "source": "trend_structure",
            "symbols": {s: {"symbol": s} for s in symbols},
        }

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    artifact = logs_dir / "trend_structure_snapshot.json"

    monkeypatch.setattr(runtime, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(runtime, "TREND_STRUCTURE_PATH", artifact)
    monkeypatch.setattr(runtime, "build_trend_structure_snapshot", _spy)

    runtime._write_trend_structure_snapshot(
        normalized_quotes={},
        history_by_symbol={},
        generated_at=datetime(2026, 5, 10, 14, 0, tzinfo=timezone.utc),
    )

    # R2: exact list passed to builder.
    assert captured["symbols"] == list(config.TREND_STRUCTURE_SYMBOLS)
    assert captured["symbols"] == list(_PRD110_EXPECTED)
    assert isinstance(captured["symbols"], list)

    # R5: artifact symbol-key set equals curated universe.
    import json
    data = json.loads(artifact.read_text())
    assert set(data["symbols"]) == set(_PRD110_EXPECTED)

    # R6: banned symbols absent.
    assert _PRD110_BANNED.isdisjoint(set(data["symbols"]))


def test_prd110_runtime_helper_does_not_use_tradable_symbols(monkeypatch, tmp_path):
    """R2 negative: _write_trend_structure_snapshot must NOT route through
    _tradable_symbols(). If it does, this test fails by surfacing the wider
    universe (which includes IWM, PAAS, USO, NVDA, ...).
    """
    from cuttingboard import runtime

    captured: dict = {}

    def _spy(*, normalized_quotes, history_by_symbol, symbols, generated_at):
        captured["symbols"] = list(symbols)
        return {
            "schema_version": 1,
            "generated_at": generated_at.isoformat(),
            "source": "trend_structure",
            "symbols": {},
        }

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    monkeypatch.setattr(runtime, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(runtime, "TREND_STRUCTURE_PATH", logs_dir / "trend_structure_snapshot.json")
    monkeypatch.setattr(runtime, "build_trend_structure_snapshot", _spy)

    runtime._write_trend_structure_snapshot(
        normalized_quotes={},
        history_by_symbol={},
        generated_at=datetime(2026, 5, 10, 14, 0, tzinfo=timezone.utc),
    )

    # The wider tradable universe contains symbols outside the curated 6.
    # If the helper regressed to _tradable_symbols(), these would appear.
    wider_only = {"IWM", "PAAS", "USO", "NVDA", "TSLA", "AAPL", "META", "AMZN", "COIN", "MSTR"}
    assert wider_only.isdisjoint(set(captured["symbols"]))


def test_prd110_no_leakage_into_decision_modules():
    """R7: trend_structure tokens must not appear in
    contract / delivery / notifications / qualification / regime / output / ui."""
    import re
    from pathlib import Path

    targets = [
        Path("cuttingboard/contract.py"),
        Path("cuttingboard/qualification.py"),
        Path("cuttingboard/regime.py"),
        Path("cuttingboard/output.py"),
    ]
    for d in (Path("cuttingboard/delivery"), Path("cuttingboard/notifications"), Path("ui")):
        if d.exists():
            targets.extend(
                p for p in d.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts
            )

    # PRD-112: dashboard_renderer.py is the authorized read-only consumer of
    # logs/trend_structure_snapshot.json. Decision-module leakage coverage is
    # preserved (contract/qualification/regime/output, notifications, ui/,
    # and all other delivery files remain checked).
    _PRD112_AUTHORIZED_CONSUMERS = {
        Path("cuttingboard/delivery/dashboard_renderer.py").resolve(),
    }

    pattern = re.compile(r"TREND_STRUCTURE_SYMBOLS|trend_structure_snapshot|trend_structure")
    offenders: list[str] = []
    for path in targets:
        if not path.exists() or not path.is_file():
            continue
        if path.resolve() in _PRD112_AUTHORIZED_CONSUMERS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if pattern.search(text):
            offenders.append(str(path))
    assert offenders == [], f"trend_structure leakage into decision modules: {offenders}"
