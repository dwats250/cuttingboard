"""PRD-176 — Red-folder economic calendar loader.

Deterministic fixtures only. Timezone-correctness is the hard criterion, so the
window-math cases are table-driven across ET event times vs UTC run timestamps,
UTC day boundaries, PT trading-window edges, and DST.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cuttingboard import red_folder
from cuttingboard.red_folder import load_schedule


def _write_schedule(path: Path, events: list[dict], *, year: int = 2026) -> None:
    path.write_text(json.dumps({
        "year": year,
        "source_note": "test fixture",
        "events": events,
    }), encoding="utf-8")


def _ev(date: str, time_et: str = "08:30", type_: str = "CPI", name: str = "CPI") -> dict:
    return {"date": date, "time_et": time_et, "type": type_, "name": name}


def _utc(y, mo, d, h, mi) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=timezone.utc)


# --- R1 — window filtering (table-driven, ET math) ----------------------

@pytest.mark.parametrize("now_utc, expect_dates", [
    # CPI event 2026-06-10 08:30 ET (= 12:30 UTC, EDT/UTC-4).
    # Run at 06:00 PT = 13:00 UTC on 06-10: event already passed today -> NOT in
    # the forward window. (window is [now, now+48h])
    (_utc(2026, 6, 10, 13, 0), []),
    # Run the evening before (2026-06-09 23:00 UTC = 19:00 ET 06-09): event next
    # morning is inside 48h.
    (_utc(2026, 6, 9, 23, 0), ["2026-06-10"]),
    # Run 2026-06-08 10:00 UTC: the event (06-10 12:30 UTC) is 50.5h out, past
    # the 48h horizon -> excluded at the upper boundary.
    (_utc(2026, 6, 8, 10, 0), []),
    # Run 2026-06-08 13:00 UTC (09:00 ET): 06-10 08:30 ET is within 48h.
    (_utc(2026, 6, 8, 13, 0), ["2026-06-10"]),
])
def test_prd176_events_in_window_table(tmp_path, now_utc, expect_dates) -> None:
    path = tmp_path / "rf.json"
    _write_schedule(path, [_ev("2026-06-10")])
    result = load_schedule(str(path))
    assert result.ok, result.error
    got = [e.date for e in result.events_in_window(now_utc, lookahead_hours=48)]
    assert got == expect_dates, f"now={now_utc.isoformat()} expected {expect_dates}, got {got}"


def test_prd176_window_is_et_anchored_across_utc_day_boundary(tmp_path) -> None:
    """A run at 2026-06-09T03:30Z is 2026-06-08 23:30 ET (previous ET day). An
    event on 2026-06-10 08:30 ET is ~32.x ET-hours later -> inside the 48h window,
    proving the math is ET-anchored, not UTC-date-anchored."""
    path = tmp_path / "rf.json"
    _write_schedule(path, [_ev("2026-06-10")])
    result = load_schedule(str(path))
    got = [e.date for e in result.events_in_window(_utc(2026, 6, 9, 3, 30), lookahead_hours=48)]
    assert got == ["2026-06-10"]


def test_prd176_dst_awareness_summer_vs_winter_offset(tmp_path) -> None:
    """Same 14:00 ET wall time resolves to 18:00 UTC in June (EDT, UTC-4) and
    19:00 UTC in December (EST, UTC-5). ZoneInfo must apply the right offset."""
    path = tmp_path / "rf.json"
    _write_schedule(path, [
        _ev("2026-06-17", "14:00", "FOMC", "FOMC"),
        _ev("2026-12-09", "14:00", "FOMC", "FOMC"),
    ])
    result = load_schedule(str(path))
    by_date = {e.date: e for e in result.events}
    jun = by_date["2026-06-17"].et_datetime().astimezone(timezone.utc)
    dec = by_date["2026-12-09"].et_datetime().astimezone(timezone.utc)
    assert (jun.hour, dec.hour) == (18, 19), "EDT->18:00Z, EST->19:00Z"


# --- R2 — loud failure on missing / malformed / invalid -----------------

def test_prd176_missing_file_is_loud_error(tmp_path) -> None:
    result = load_schedule(str(tmp_path / "does_not_exist.json"))
    assert result.ok is False
    assert result.error and "not found" in result.error.lower()
    assert result.events == ()


def test_prd176_malformed_json_is_loud_error(tmp_path) -> None:
    path = tmp_path / "rf.json"
    path.write_text("{ this is not valid json ", encoding="utf-8")
    result = load_schedule(str(path))
    assert result.ok is False
    assert result.error
    assert result.events == ()


def test_prd176_invalid_entry_missing_key_is_loud_error(tmp_path) -> None:
    path = tmp_path / "rf.json"
    # missing "time_et"
    path.write_text(json.dumps({"year": 2026, "source_note": "x",
                                "events": [{"date": "2026-06-10", "type": "CPI", "name": "CPI"}]}),
                    encoding="utf-8")
    result = load_schedule(str(path))
    assert result.ok is False, "an event missing a required key must not load as valid"
    assert result.error
    assert result.events == ()


def test_prd176_invalid_entry_unparseable_date_is_loud_error(tmp_path) -> None:
    path = tmp_path / "rf.json"
    _write_schedule(path, [_ev("2026-13-99", "08:30")])
    result = load_schedule(str(path))
    assert result.ok is False, "an unparseable date must not load as valid"
    assert result.error
    assert result.events == ()


# --- R3 — expiry signal -------------------------------------------------

def test_prd176_expiry_fires_within_30_days_of_last_entry(tmp_path) -> None:
    path = tmp_path / "rf.json"
    _write_schedule(path, [_ev("2026-06-10"), _ev("2026-12-15", "08:30", "PPI", "PPI")])
    result = load_schedule(str(path))
    # 20 days before the last entry -> expiring.
    assert result.is_expiring(_utc(2026, 11, 25, 13, 0), within_days=30) is True
    # Far before the last entry -> not expiring.
    assert result.is_expiring(_utc(2026, 6, 10, 13, 0), within_days=30) is False


# --- empty state (valid file, zero events) ------------------------------

def test_prd176_empty_schedule_is_ok_not_error(tmp_path) -> None:
    path = tmp_path / "rf.json"
    _write_schedule(path, [])
    result = load_schedule(str(path))
    assert result.ok is True, "an empty-but-valid file is the empty state, not an error"
    assert result.error is None
    assert result.events == ()
    assert result.events_in_window(_utc(2026, 6, 10, 13, 0)) == []
    assert result.is_expiring(_utc(2026, 6, 10, 13, 0)) is False


# --- the committed production data file must parse -----------------------

def test_prd176_real_data_file_loads_clean() -> None:
    """The hand-entered data/red_folder_2026.json must load without error and
    expose at least the verified FOMC + CPI + NFP entries."""
    result = load_schedule()  # default path -> data/red_folder_2026.json
    assert result.ok, result.error
    assert len(result.events) >= 6, "expected at least the verified FOMC/CPI/NFP entries"
    types = {e.type for e in result.events}
    assert {"FOMC", "CPI", "NFP"}.issubset(types)


def test_prd176_module_is_pure_no_decision_imports() -> None:
    import inspect
    src = inspect.getsource(red_folder)
    for forbidden in ("runtime", "contract", "payload", "qualification"):
        assert f"from cuttingboard.{forbidden}" not in src and f"import {forbidden}" not in src, (
            f"red_folder must stay pure; no coupling to cuttingboard.{forbidden}"
        )
