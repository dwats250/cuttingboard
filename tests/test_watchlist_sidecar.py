"""Tests for the watchlist snapshot sidecar (NS-4A v2 measurement projection).

Pins the derived projections (22 measurement, 11 personal, benchmark map) and the
schema_version-3 carrier: exact 22-row population in registry order, UCO/TSLA
absent, minimal five-key rows, honest nulls (never coerced to 0.0), byte
determinism, and tz-awareness.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cuttingboard.normalization import NormalizedQuote
from cuttingboard.watchlist_sidecar import (
    BENCHMARK_BY_SYMBOL,
    MARKET_STRUCTURE_ROWS,
    MARKET_STRUCTURE_SYMBOLS,
    PERSONAL_SYMBOLS,
    build_watchlist_snapshot,
)

_MARKET_STRUCTURE_22 = (
    "SPY", "QQQ",
    "XLK", "XLF", "XLE", "XLI", "XLY", "XLP", "XLV", "XLU", "XLB", "XLRE", "XLC",
    "GLD", "SLV", "GDX",
    "AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOG",
)
_PERSONAL_11 = (
    "SPY", "QQQ", "XLE", "GLD", "SLV", "GDX", "NVDA", "META", "AMZN", "GOOG", "UCO",
)


def _quote(symbol: str, price: float, pct: float = 0.0) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol, price=price, pct_change_decimal=pct, volume=None,
        fetched_at_utc=datetime(2026, 5, 10, 14, 0, tzinfo=timezone.utc),
        source="test", units="usd_price", age_seconds=0.0,
    )


def _full_quotes() -> dict[str, NormalizedQuote]:
    return {sym: _quote(sym, 100.0 + i) for i, sym in enumerate(MARKET_STRUCTURE_SYMBOLS)}


def _generated_at() -> datetime:
    return datetime(2026, 5, 10, 14, 0, tzinfo=timezone.utc)


# --- Projections ------------------------------------------------------------
def test_market_structure_symbols_exact_22() -> None:
    assert MARKET_STRUCTURE_SYMBOLS == _MARKET_STRUCTURE_22


def test_personal_symbols_exact_11() -> None:
    assert PERSONAL_SYMBOLS == _PERSONAL_11


def test_market_structure_rows_shape_and_order() -> None:
    assert len(MARKET_STRUCTURE_ROWS) == 22
    assert [sym for sym, *_ in MARKET_STRUCTURE_ROWS] == list(_MARKET_STRUCTURE_22)
    assert [idx for *_, idx in MARKET_STRUCTURE_ROWS] == list(range(22))
    for sym, group, idx in MARKET_STRUCTURE_ROWS:
        assert isinstance(group, str) and group
        assert isinstance(idx, int) and not isinstance(idx, bool)


def test_benchmark_map_has_22_keys_over_measurement() -> None:
    assert set(BENCHMARK_BY_SYMBOL) == set(_MARKET_STRUCTURE_22)
    assert BENCHMARK_BY_SYMBOL["SPY"] is None
    assert BENCHMARK_BY_SYMBOL["QQQ"] == "SPY"
    assert BENCHMARK_BY_SYMBOL["GLD"] is None
    assert BENCHMARK_BY_SYMBOL["SLV"] == "GLD"
    assert BENCHMARK_BY_SYMBOL["AAPL"] == "QQQ"


def test_uco_and_tsla_absent_from_measurement() -> None:
    assert "UCO" not in MARKET_STRUCTURE_SYMBOLS
    assert "TSLA" not in MARKET_STRUCTURE_SYMBOLS


# --- v3 carrier envelope ----------------------------------------------------
def test_top_level_schema_keys() -> None:
    snap = build_watchlist_snapshot(_full_quotes(), _generated_at())
    assert set(snap) == {"schema_version", "source", "generated_at", "symbols"}
    assert snap["schema_version"] == 3
    assert snap["source"] == "watchlist"


def test_per_symbol_record_has_exactly_five_keys() -> None:
    snap = build_watchlist_snapshot(_full_quotes(), _generated_at())
    expected_keys = {"symbol", "primary_group", "registry_index", "current_price", "daily_change_pct"}
    for record in snap["symbols"].values():
        assert set(record) == expected_keys


def test_no_legacy_row_keys() -> None:  # M7-adjacent: no metadata leakage
    snap = build_watchlist_snapshot(_full_quotes(), _generated_at())
    for record in snap["symbols"].values():
        for forbidden in ("sector_theme", "watch_reason", "roles", "benchmark_symbol",
                          "rationale", "personal", "market_structure", "trade_eligible"):
            assert forbidden not in record, forbidden


def test_symbols_exactly_22_in_registry_order() -> None:
    snap = build_watchlist_snapshot(_full_quotes(), _generated_at())
    assert list(snap["symbols"]) == list(_MARKET_STRUCTURE_22)


def test_uco_and_tsla_never_serialized() -> None:  # M7 / M8
    snap = build_watchlist_snapshot({}, _generated_at())  # all n/a, full population
    assert "UCO" not in snap["symbols"]
    assert "TSLA" not in snap["symbols"]
    assert set(snap["symbols"]) == set(_MARKET_STRUCTURE_22)


def test_registry_index_and_primary_group_populated() -> None:
    snap = build_watchlist_snapshot(_full_quotes(), _generated_at())
    for sym, group, idx in MARKET_STRUCTURE_ROWS:
        assert snap["symbols"][sym]["primary_group"] == group
        assert snap["symbols"][sym]["registry_index"] == idx


def test_current_price_passthrough() -> None:
    quotes = _full_quotes()
    snap = build_watchlist_snapshot(quotes, _generated_at())
    for symbol, record in snap["symbols"].items():
        assert record["current_price"] == quotes[symbol].price


def test_daily_change_pct_scale() -> None:
    snap = build_watchlist_snapshot({"SPY": _quote("SPY", 500.0, 0.052)}, _generated_at())
    assert snap["symbols"]["SPY"]["daily_change_pct"] == 5.2  # decimal*100, 1 dp


def test_missing_quote_yields_null_price_and_pct_never_zero() -> None:  # M5
    snap = build_watchlist_snapshot({"SPY": _quote("SPY", 500.0, 0.01)}, _generated_at())
    assert snap["symbols"]["SPY"]["current_price"] == 500.0
    for symbol in set(_MARKET_STRUCTURE_22) - {"SPY"}:
        assert snap["symbols"][symbol]["current_price"] is None
        assert snap["symbols"][symbol]["daily_change_pct"] is None  # NEVER 0.0


def test_all_missing_yields_all_nulls() -> None:  # M5
    snap = build_watchlist_snapshot({}, _generated_at())
    for rec in snap["symbols"].values():
        assert rec["current_price"] is None
        assert rec["daily_change_pct"] is None


def test_unrequested_quote_symbols_ignored() -> None:
    quotes = _full_quotes()
    quotes["AMD"] = _quote("AMD", 999.0)
    quotes["UCO"] = _quote("UCO", 40.0)   # personal-only must never appear
    quotes["TSLA"] = _quote("TSLA", 200.0)
    snap = build_watchlist_snapshot(quotes, _generated_at())
    assert "AMD" not in snap["symbols"]
    assert "UCO" not in snap["symbols"]
    assert "TSLA" not in snap["symbols"]


def test_determinism_byte_identical() -> None:
    quotes = _full_quotes()
    gen = _generated_at()
    a = json.dumps(build_watchlist_snapshot(quotes, gen), sort_keys=True)
    b = json.dumps(build_watchlist_snapshot(quotes, gen), sort_keys=True)
    assert a == b


def test_naive_datetime_raises() -> None:
    naive = datetime(2026, 5, 10, 14, 0)
    with pytest.raises(ValueError):
        build_watchlist_snapshot(_full_quotes(), naive)


def test_generated_at_none_yields_null() -> None:
    snap = build_watchlist_snapshot(_full_quotes(), None)
    assert snap["generated_at"] is None


def test_generated_at_isoformat_with_tz() -> None:
    snap = build_watchlist_snapshot(_full_quotes(), _generated_at())
    assert snap["generated_at"] == "2026-05-10T14:00:00+00:00"


# --- Source hygiene ---------------------------------------------------------
def test_no_forbidden_wall_clock_substrings_in_source() -> None:
    src = Path(__file__).resolve().parent.parent / "cuttingboard" / "watchlist_sidecar.py"
    text = src.read_text(encoding="utf-8")
    for forbidden in ("datetime.now", "time.time", "time.monotonic"):
        assert forbidden not in text, f"{forbidden} present in watchlist_sidecar.py"


def test_no_trend_structure_coupling_in_source() -> None:
    src = Path(__file__).resolve().parent.parent / "cuttingboard" / "watchlist_sidecar.py"
    text = src.read_text(encoding="utf-8")
    for forbidden in ("trend_structure", "TREND_STRUCTURE"):
        assert forbidden not in text, f"{forbidden} present in watchlist_sidecar.py"


def test_no_io_imports_in_source() -> None:
    src = Path(__file__).resolve().parent.parent / "cuttingboard" / "watchlist_sidecar.py"
    text = src.read_text(encoding="utf-8")
    for forbidden in ("import requests", "import urllib", "import httpx",
                      "from cuttingboard.transport", "from cuttingboard.delivery"):
        assert forbidden not in text, f"{forbidden} present in watchlist_sidecar.py"


def test_legacy_symbols_removed_from_module() -> None:
    src = Path(__file__).resolve().parent.parent / "cuttingboard" / "watchlist_sidecar.py"
    text = src.read_text(encoding="utf-8")
    for forbidden in ("WATCHLIST_SYMBOLS", "_PRIMARY_GROUP_TO_THEME", "build_watchlist_symbols"):
        assert forbidden not in text, f"{forbidden} still present in watchlist_sidecar.py"


# --- HALT-guard placement (unchanged contract) ------------------------------
def test_runtime_call_site_has_explicit_halt_guard() -> None:
    src = Path(__file__).resolve().parent.parent / "cuttingboard" / "runtime" / "__init__.py"
    lines = src.read_text(encoding="utf-8").splitlines()

    trend_close_idx = next(
        i for i, ln in enumerate(lines)
        if ln.strip() == ")" and any(
            "_write_trend_structure_snapshot(" in lines[k] for k in range(max(0, i - 6), i)
        )
    )
    guard_idx = next(
        i for i in range(trend_close_idx + 1, len(lines))
        if lines[i].strip() and not lines[i].lstrip().startswith("#")
    )
    assert lines[guard_idx].strip() == "if not validation_summary.system_halted:", (
        f"line after trend_structure call must be the explicit HALT guard, "
        f"got: {lines[guard_idx]!r}"
    )
    watch_idx = next(
        i for i in range(guard_idx + 1, len(lines))
        if "_write_watchlist_snapshot(" in lines[i]
    )
    guard_indent = len(lines[guard_idx]) - len(lines[guard_idx].lstrip())
    watch_indent = len(lines[watch_idx]) - len(lines[watch_idx].lstrip())
    assert watch_indent > guard_indent


def test_runtime_write_helper_writes_atomically(tmp_path, monkeypatch) -> None:
    from cuttingboard import runtime

    monkeypatch.setattr(runtime, "LOGS_DIR", tmp_path)
    monkeypatch.setattr(runtime, "WATCHLIST_PATH", tmp_path / "watchlist_snapshot.json")

    runtime._write_watchlist_snapshot(normalized_quotes=_full_quotes(), generated_at=_generated_at())
    artifact = tmp_path / "watchlist_snapshot.json"
    assert artifact.exists()
    assert not (tmp_path / "watchlist_snapshot.json.tmp").exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["schema_version"] == 3
    assert set(data["symbols"]) == set(_MARKET_STRUCTURE_22)
