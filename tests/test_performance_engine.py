"""Tests for cuttingboard/performance_engine.py"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cuttingboard.performance_engine import run_performance_engine


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")


def _make_record(symbol: str, result: str, r_multiple: float, direction: str = "LONG") -> dict:
    return {
        "symbol": symbol,
        "direction": direction,
        "entry": 100.0,
        "stop": 97.0,
        "target": 106.0,
        "decision_run_at_utc": "2026-04-28T13:00:00+00:00",
        "evaluated_at_utc": "2026-04-28T19:45:00+00:00",
        "evaluation": {
            "result": result,
            "R_multiple": r_multiple,
            "time_to_resolution": 30,
        },
    }


# ---------------------------------------------------------------------------
# Missing file — silent skip
# ---------------------------------------------------------------------------

def test_missing_file_is_silent(tmp_path: Path) -> None:
    out = tmp_path / "summary.json"
    run_performance_engine(tmp_path / "evaluation.jsonl", out)
    assert not out.exists()


# ---------------------------------------------------------------------------
# Insufficient data (< 5 records)
# ---------------------------------------------------------------------------

def test_insufficient_data_flag(tmp_path: Path) -> None:
    records = [
        _make_record("SPY", "TARGET_HIT", 1.5),
        _make_record("SPY", "STOP_HIT", -0.8),
        _make_record("SPY", "NO_HIT", 0.0),
    ]
    ev = tmp_path / "evaluation.jsonl"
    _write_jsonl(ev, records)
    out = tmp_path / "summary.json"
    run_performance_engine(ev, out)

    summary = json.loads(out.read_text())
    bucket = summary["buckets"]["SPY"]
    assert bucket["insufficient_data"] is True
    assert bucket["total_trades"] == 3
    assert "win_rate" not in bucket
    assert "expectancy" not in bucket


# ---------------------------------------------------------------------------
# Full metrics with >= 5 records
# ---------------------------------------------------------------------------

def test_full_metrics_five_records(tmp_path: Path) -> None:
    records = [
        _make_record("SPY", "TARGET_HIT", 2.0),
        _make_record("SPY", "TARGET_HIT", 1.5),
        _make_record("SPY", "STOP_HIT", -1.0),
        _make_record("SPY", "STOP_HIT", -0.8),
        _make_record("SPY", "NO_HIT", 0.0),
    ]
    ev = tmp_path / "evaluation.jsonl"
    _write_jsonl(ev, records)
    out = tmp_path / "summary.json"
    run_performance_engine(ev, out)

    summary = json.loads(out.read_text())
    bucket = summary["buckets"]["SPY"]
    assert bucket["insufficient_data"] is False
    assert bucket["total_trades"] == 5
    assert bucket["wins"] == 2
    assert bucket["losses"] == 2
    assert bucket["flats"] == 1
    assert bucket["win_rate"] == pytest.approx(0.4, abs=1e-4)
    assert bucket["avg_r_win"] == pytest.approx(1.75, abs=1e-4)
    assert bucket["avg_r_loss"] == pytest.approx(0.9, abs=1e-4)
    expected = (0.4 * 1.75) - (0.6 * 0.9)
    assert bucket["expectancy"] == pytest.approx(expected, abs=1e-4)


# ---------------------------------------------------------------------------
# avg_r_loss uses |R_multiple|, not signed value
# ---------------------------------------------------------------------------

def test_avg_r_loss_uses_absolute_value(tmp_path: Path) -> None:
    records = [
        _make_record("QQQ", "TARGET_HIT", 2.0),
        _make_record("QQQ", "TARGET_HIT", 2.0),
        _make_record("QQQ", "TARGET_HIT", 2.0),
        _make_record("QQQ", "STOP_HIT", -1.5),  # negative in file
        _make_record("QQQ", "STOP_HIT", -1.5),
    ]
    ev = tmp_path / "evaluation.jsonl"
    _write_jsonl(ev, records)
    out = tmp_path / "summary.json"
    run_performance_engine(ev, out)

    bucket = json.loads(out.read_text())["buckets"]["QQQ"]
    assert bucket["avg_r_loss"] == pytest.approx(1.5, abs=1e-4)
    # expectancy should be positive given win-heavy sample
    assert bucket["expectancy"] > 0


# ---------------------------------------------------------------------------
# Multi-symbol bucketing
# ---------------------------------------------------------------------------

def test_multi_symbol_separate_buckets(tmp_path: Path) -> None:
    spy = [_make_record("SPY", "TARGET_HIT", 1.0) for _ in range(5)]
    qqq = [_make_record("QQQ", "STOP_HIT", -1.0) for _ in range(5)]
    ev = tmp_path / "evaluation.jsonl"
    _write_jsonl(ev, spy + qqq)
    out = tmp_path / "summary.json"
    run_performance_engine(ev, out)

    buckets = json.loads(out.read_text())["buckets"]
    assert "SPY" in buckets
    assert "QQQ" in buckets
    assert buckets["SPY"]["wins"] == 5
    assert buckets["QQQ"]["losses"] == 5


# ---------------------------------------------------------------------------
# Determinism — identical input → identical output metrics
# ---------------------------------------------------------------------------

def test_deterministic_output(tmp_path: Path) -> None:
    records = [
        _make_record("SPY", "TARGET_HIT", 1.8),
        _make_record("SPY", "STOP_HIT", -0.9),
        _make_record("SPY", "TARGET_HIT", 2.1),
        _make_record("SPY", "NO_HIT", 0.0),
        _make_record("SPY", "STOP_HIT", -1.1),
    ]
    ev = tmp_path / "evaluation.jsonl"
    _write_jsonl(ev, records)

    out1 = tmp_path / "summary1.json"
    out2 = tmp_path / "summary2.json"
    run_performance_engine(ev, out1)
    run_performance_engine(ev, out2)

    s1 = json.loads(out1.read_text())
    s2 = json.loads(out2.read_text())
    assert s1["buckets"] == s2["buckets"]


# ---------------------------------------------------------------------------
# Invalid / malformed records are skipped without crash
# ---------------------------------------------------------------------------

def test_missing_evaluation_field_skipped(tmp_path: Path) -> None:
    good = [_make_record("SPY", "TARGET_HIT", 1.5) for _ in range(5)]
    bad = {"symbol": "SPY", "direction": "LONG"}  # no evaluation key
    ev = tmp_path / "evaluation.jsonl"
    _write_jsonl(ev, good + [bad])
    out = tmp_path / "summary.json"
    run_performance_engine(ev, out)

    bucket = json.loads(out.read_text())["buckets"]["SPY"]
    assert bucket["total_trades"] == 5


def test_invalid_result_value_skipped(tmp_path: Path) -> None:
    good = [_make_record("SPY", "TARGET_HIT", 1.5) for _ in range(5)]
    bad = _make_record("SPY", "UNKNOWN_RESULT", 0.0)
    ev = tmp_path / "evaluation.jsonl"
    _write_jsonl(ev, good + [bad])
    out = tmp_path / "summary.json"
    run_performance_engine(ev, out)

    bucket = json.loads(out.read_text())["buckets"]["SPY"]
    assert bucket["total_trades"] == 5


def test_malformed_json_line_skipped(tmp_path: Path) -> None:
    ev = tmp_path / "evaluation.jsonl"
    lines = [json.dumps(_make_record("SPY", "TARGET_HIT", 1.0)) for _ in range(5)]
    lines.insert(2, "NOT_VALID_JSON{{{")
    ev.write_text("\n".join(lines) + "\n")
    out = tmp_path / "summary.json"
    run_performance_engine(ev, out)

    bucket = json.loads(out.read_text())["buckets"]["SPY"]
    assert bucket["total_trades"] == 5


# ---------------------------------------------------------------------------
# Edge: all FLAT records → insufficient or valid but 0.0 expectancy
# ---------------------------------------------------------------------------

def test_all_flat_records(tmp_path: Path) -> None:
    records = [_make_record("IWM", "NO_HIT", 0.0) for _ in range(5)]
    ev = tmp_path / "evaluation.jsonl"
    _write_jsonl(ev, records)
    out = tmp_path / "summary.json"
    run_performance_engine(ev, out)

    bucket = json.loads(out.read_text())["buckets"]["IWM"]
    assert bucket["insufficient_data"] is False
    assert bucket["win_rate"] == pytest.approx(0.0)
    assert bucket["expectancy"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Output includes generated_at
# ---------------------------------------------------------------------------

def test_output_has_generated_at(tmp_path: Path) -> None:
    records = [_make_record("SPY", "TARGET_HIT", 1.0) for _ in range(5)]
    ev = tmp_path / "evaluation.jsonl"
    _write_jsonl(ev, records)
    out = tmp_path / "summary.json"
    run_performance_engine(ev, out)

    summary = json.loads(out.read_text())
    assert "generated_at" in summary
    assert summary["generated_at"]  # non-empty
