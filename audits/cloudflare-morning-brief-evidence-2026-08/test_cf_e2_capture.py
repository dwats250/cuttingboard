"""Behavior tests for the bounded CF-E2 evidence harness."""
from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest


HARNESS_PATH = Path(__file__).with_name("cf_e2_capture.py")
SPEC = importlib.util.spec_from_file_location("cf_e2_capture", HARNESS_PATH)
assert SPEC is not None and SPEC.loader is not None
cf_e2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cf_e2)


@pytest.mark.parametrize(
    ("slot", "now_utc"),
    [
        ("premarket", datetime(2026, 8, 9, 13, 0, tzinfo=timezone.utc)),
        ("open", datetime(2026, 8, 9, 13, 32, tzinfo=timezone.utc)),
        ("premarket", datetime(2026, 8, 10, 13, 32, tzinfo=timezone.utc)),
        ("open", datetime(2026, 8, 10, 13, 0, tzinfo=timezone.utc)),
    ],
)
def test_explicit_slot_cannot_bypass_authorized_window(monkeypatch, tmp_path, slot, now_utc):
    monkeypatch.setattr(cf_e2, "OUT_DIR", tmp_path)
    monkeypatch.setattr(cf_e2, "_now_utc", lambda: now_utc)

    with pytest.raises(SystemExit) as exc:
        cf_e2.main(["--slot", slot])

    assert exc.value.code == 3
    assert list(tmp_path.iterdir()) == []


def test_unparseable_open_bar_is_invalid_not_present():
    now = datetime(2026, 8, 10, 13, 32, tzinfo=timezone.utc)
    frame = pd.DataFrame(
        {"Open": ["not-a-number"], "Close": [101.0]},
        index=[pd.Timestamp("2026-08-10T09:30:00-04:00")],
    )

    record = cf_e2._build_open_record(frame, now)
    outcome = record["bars"]["bar_0930_OPEN"]

    assert outcome["outcome"] == "UNPARSEABLE"
    assert record["status"] == "INVALID"
    assert record["diagnostic"]["bar_0930_present"] is False
    assert "not-a-number" in outcome["raw"]


def test_duplicate_open_rows_cannot_hide_an_unparseable_row():
    now = datetime(2026, 8, 10, 13, 32, tzinfo=timezone.utc)
    timestamp = pd.Timestamp("2026-08-10T09:30:00-04:00")
    frame = pd.DataFrame(
        {"Open": ["bad", 100.0], "Close": [101.0, 101.0]},
        index=[timestamp, timestamp],
    )

    record = cf_e2._build_open_record(frame, now)

    assert record["bars"]["bar_0930_OPEN"]["outcome"] == "UNPARSEABLE"
    assert record["status"] == "INVALID"


@pytest.mark.parametrize(
    ("hhmm", "bar_key"),
    [
        ("09:30", "bar_0930_OPEN"),
        ("09:31", "bar_0931_OPEN_PLUS_1"),
    ],
)
def test_timezone_naive_open_timestamp_is_unparseable(hhmm, bar_key):
    now = datetime(2026, 8, 10, 13, 32, tzinfo=timezone.utc)
    raw_timestamp = pd.Timestamp(f"2026-08-10 {hhmm}:00")
    frame = pd.DataFrame(
        {"Open": [100.0], "Close": [101.0]},
        index=[raw_timestamp],
    )

    record = cf_e2._build_open_record(frame, now)
    outcome = record["bars"][bar_key]

    assert outcome["outcome"] == "UNPARSEABLE"
    assert outcome["reason"] == "timezone_unverified"
    assert outcome["raw_timestamp"] == repr(raw_timestamp)
    assert record["status"] == "INVALID"
    assert record["diagnostic"][f"bar_{hhmm.replace(':', '')}_present"] is False


def test_timezone_aware_utc_open_timestamps_normalize_to_et_and_are_present():
    now = datetime(2026, 8, 10, 13, 32, tzinfo=timezone.utc)
    raw_0930 = pd.Timestamp("2026-08-10T13:30:00+00:00")
    raw_0931 = pd.Timestamp("2026-08-10T13:31:00+00:00")
    frame = pd.DataFrame(
        {"Open": [100.0, 101.0], "Close": [100.5, 101.5]},
        index=[raw_0930, raw_0931],
    )

    record = cf_e2._build_open_record(frame, now)

    assert record["status"] == "OK"
    assert record["bars"]["bar_0930_OPEN"] == {
        "outcome": "PRESENT",
        "raw_timestamp": repr(raw_0930),
        "time_et": "2026-08-10T09:30:00-04:00",
        "open": 100.0,
        "close": 100.5,
    }
    assert record["bars"]["bar_0931_OPEN_PLUS_1"] == {
        "outcome": "PRESENT",
        "raw_timestamp": repr(raw_0931),
        "time_et": "2026-08-10T09:31:00-04:00",
        "open": 101.0,
        "close": 101.5,
    }


def test_mixed_naive_and_aware_duplicate_retains_timezone_reason_and_raw_values():
    now = datetime(2026, 8, 10, 13, 32, tzinfo=timezone.utc)
    naive = pd.Timestamp("2026-08-10 09:30:00")
    aware = pd.Timestamp("2026-08-10T13:30:00+00:00")
    frame = pd.DataFrame(
        {"Open": [100.0, 100.0], "Close": [101.0, 101.0]},
        index=[naive, aware],
    )

    record = cf_e2._build_open_record(frame, now)
    outcome = record["bars"]["bar_0930_OPEN"]

    assert outcome["outcome"] == "UNPARSEABLE"
    assert outcome["reason"] == "timezone_unverified"
    assert repr(naive) in outcome["raw_timestamps"]
    assert repr(aware) in outcome["raw_timestamps"]
    assert record["status"] == "INVALID"


def test_price_difference_without_provider_session_semantics_is_inconclusive():
    now = datetime(2026, 8, 10, 13, 0, tzinfo=timezone.utc)

    record = cf_e2._build_premarket_record(
        fast_info={"last_price": 101.0, "previous_close": 100.0},
        quote_info={},
        now=now,
    )

    assert record["raw_observations"]["fast_info"]["last_price"] == 101.0
    assert record["raw_observations"]["fast_info"]["previous_close"] == 100.0
    assert record["status"] == "INCONCLUSIVE"
    assert record["diagnostic"]["classification"] == "INCONCLUSIVE"


def test_provider_label_without_timestamp_is_inconclusive():
    now = datetime(2026, 8, 10, 13, 0, tzinfo=timezone.utc)

    record = cf_e2._build_premarket_record(
        fast_info={"last_price": 101.0, "previous_close": 100.0},
        quote_info={"marketState": "PRE", "preMarketPrice": 101.0},
        now=now,
    )

    assert record["status"] == "INCONCLUSIVE"
    assert record["diagnostic"]["classification"] == "INCONCLUSIVE"
    assert "preMarketTime" in record["diagnostic"]["reason"]


def test_provider_labeled_dated_premarket_observation_is_classifiable():
    now = datetime(2026, 8, 10, 13, 0, tzinfo=timezone.utc)
    observed = datetime(2026, 8, 10, 12, 59, tzinfo=timezone.utc)

    record = cf_e2._build_premarket_record(
        fast_info={"last_price": 101.0, "previous_close": 100.0},
        quote_info={
            "marketState": "PRE",
            "preMarketPrice": 101.25,
            "preMarketTime": int(observed.timestamp()),
            "regularMarketPrice": 100.0,
            "regularMarketTime": int(datetime(2026, 8, 7, 20, 0, tzinfo=timezone.utc).timestamp()),
        },
        now=now,
    )

    assert record["status"] == "OK"
    assert record["diagnostic"]["classification"] == "PROVIDER_IDENTIFIED_PREMARKET"
    assert record["premarket_observation"]["price"] == 101.25
    assert record["premarket_observation"]["observed_utc"] == observed.isoformat()


def test_quote_info_can_support_classification_when_fast_info_is_unavailable():
    now = datetime(2026, 8, 10, 13, 0, tzinfo=timezone.utc)
    observed = datetime(2026, 8, 10, 12, 59, tzinfo=timezone.utc)

    record = cf_e2._build_premarket_record(
        fast_info={},
        fast_info_error="fast_info request failed",
        quote_info={
            "marketState": "PRE",
            "preMarketPrice": 101.25,
            "preMarketTime": int(observed.timestamp()),
            "previousClose": 100.0,
        },
        now=now,
    )

    assert record["status"] == "OK"
    assert record["raw_observations"]["fast_info_error"] == "fast_info request failed"


def test_capture_completing_outside_window_writes_nothing(monkeypatch, tmp_path):
    times = iter(
        [
            datetime(2026, 8, 10, 13, 32, tzinfo=timezone.utc),  # 06:32 PT: authorized
            datetime(2026, 8, 10, 13, 46, tzinfo=timezone.utc),  # 06:46 PT: too late
        ]
    )

    class FakeYFinance:
        @staticmethod
        def download(*args, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(cf_e2, "OUT_DIR", tmp_path)
    monkeypatch.setattr(cf_e2, "_now_utc", lambda: next(times))
    monkeypatch.setattr(cf_e2, "_import_yf", lambda _slot: FakeYFinance)

    with pytest.raises(SystemExit) as exc:
        cf_e2.main(["--slot", "open"])

    assert exc.value.code == 3
    assert list(tmp_path.iterdir()) == []
