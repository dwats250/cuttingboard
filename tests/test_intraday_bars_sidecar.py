"""PRD-323 (A1-P) — intraday 1-minute source-bar producer.

Covers the validator/writer (R4/R5/R6), the seam wiring (R2), the single
isolation boundary (R7), the best-effort acquisition budget (R11), no-network-
without-opt-in (R3/R12), and no decision effect (R10). All network is stubbed;
no test performs a live fetch.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

import cuttingboard.runtime as runtime
from cuttingboard.notifications import NOTIFY_HOURLY
from cuttingboard.runtime import MODE_LIVE, _execute_notify_run

_ET = ZoneInfo("America/New_York")


# --- fixtures / helpers -----------------------------------------------------

@pytest.fixture
def artifact(monkeypatch, tmp_path) -> Path:
    """Redirect the intraday sidecar (and LOGS_DIR) to tmp, mirroring the
    price-bars sidecar's `isolated` fixture. Returns the artifact path."""
    logs_dir = tmp_path / "logs"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(runtime, "INTRADAY_BARS_PATH", logs_dir / "intraday_bars_snapshot.json")
    return logs_dir / "intraday_bars_snapshot.json"


def _session_frame(session_date: date, n: int = 3) -> pd.DataFrame:
    """A well-formed current-session 1m frame: UTC-indexed, strictly ascending,
    coherent OHLCV, all bars on `session_date` (ET)."""
    base = datetime(session_date.year, session_date.month, session_date.day, 10, 0, tzinfo=_ET)
    index = pd.DatetimeIndex([(base + timedelta(minutes=i)).astimezone(timezone.utc) for i in range(n)])
    data = {
        "Open": [100.0 + i for i in range(n)],
        "High": [101.0 + i for i in range(n)],
        "Low": [99.0 + i for i in range(n)],
        "Close": [100.5 + i for i in range(n)],
        "Volume": [1000 + i for i in range(n)],
    }
    return pd.DataFrame(data, index=index)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _isolate_seam_paths(monkeypatch, tmp_path):
    """Redirect every path the hourly seam writes, plus the intraday sidecar."""
    logs_dir = tmp_path / "logs"
    monkeypatch.chdir(tmp_path)
    for name, rel in {
        "LOGS_DIR": logs_dir,
        "REPORTS_DIR": tmp_path / "reports",
        "LATEST_HOURLY_RUN_PATH": logs_dir / "latest_hourly_run.json",
        "LATEST_HOURLY_CONTRACT_PATH": logs_dir / "latest_hourly_contract.json",
        "LATEST_HOURLY_PAYLOAD_PATH": logs_dir / "latest_hourly_payload.json",
        "HOURLY_REPORT_PATH": tmp_path / "reports" / "hourly_report.html",
        "MARKET_MAP_PATH": logs_dir / "market_map.json",
        "LATEST_HOURLY_MARKET_MAP_PATH": logs_dir / "latest_hourly_market_map.json",
        "TREND_STRUCTURE_PATH": logs_dir / "trend_structure_snapshot.json",
        "PRICE_BARS_PATH": logs_dir / "price_bars_snapshot.json",
        "WATCHLIST_PATH": logs_dir / "watchlist_snapshot.json",
        "INTRADAY_BARS_PATH": logs_dir / "intraday_bars_snapshot.json",
    }.items():
        monkeypatch.setattr(runtime, name, rel)
    return logs_dir


def _drive_halted_seam(monkeypatch, tmp_path):
    """Drive the real hourly seam down the lightest path (HALT) that still
    reaches the A1-P producer block. Isolates EVERY seam-written path to tmp
    (and chdir, so a failure-path traceback.txt lands in tmp too). Returns the
    run result dict and the send_notification mock."""
    _isolate_seam_paths(monkeypatch, tmp_path)
    validation = MagicMock(spec=runtime.ValidationSummary)
    validation.system_halted = True
    validation.halt_reason = "test halt"
    validation.valid_quotes = {}
    validation.symbols_validated = 0
    validation.symbols_attempted = 0
    with (
        patch("cuttingboard.runtime.fetch_all", return_value={}),
        patch("cuttingboard.runtime.normalize_all", return_value={}),
        patch("cuttingboard.runtime.extract_fetch_failures", return_value={}),
        patch("cuttingboard.runtime.validate_quotes", return_value=validation),
        patch("cuttingboard.runtime.send_notification", return_value=True) as send,
    ):
        result = _execute_notify_run(
            mode=MODE_LIVE, run_date=date(2026, 5, 12), notify_mode=NOTIFY_HOURLY
        )
    return result, send


# --- R6 / R4 / R5: writer + validator (direct, deterministic) ---------------

def test_schema_shape_is_exactly_the_versioned_contract(artifact):
    session = date(2026, 5, 12)
    runtime._write_intraday_bars_snapshot(
        frames_by_symbol={"AAPL": _session_frame(session), "SPY": _session_frame(session)},
        primary_symbol="AAPL",
        generated_at=datetime(2026, 5, 12, 18, 0, tzinfo=timezone.utc),
        session_date=session,
    )
    data = _read(artifact)
    assert set(data) == {
        "schema_version", "generated_at", "session_date",
        "primary_symbol", "source", "columns", "symbols",
    }
    assert data["schema_version"] == 1 and isinstance(data["schema_version"], int)
    assert data["session_date"] == "2026-05-12"
    assert data["primary_symbol"] == "AAPL"
    assert data["source"] == {
        "producer": "hourly", "provider": "yfinance", "interval": "1m", "adjusted": False,
    }
    assert data["columns"] == ["ts", "Open", "High", "Low", "Close", "Volume"]
    assert set(data["symbols"]) == {"AAPL", "SPY"}


def test_generated_at_is_timezone_aware_utc_and_not_future(artifact):
    session = date(2026, 5, 12)
    runtime._write_intraday_bars_snapshot(
        frames_by_symbol={"SPY": _session_frame(session)},
        primary_symbol=None,
        generated_at=datetime(2026, 5, 12, 18, 0, tzinfo=timezone.utc),
        session_date=session,
    )
    data = _read(artifact)
    parsed = datetime.fromisoformat(data["generated_at"])
    assert parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)
    assert data["primary_symbol"] is None  # R6: field present even when null


def test_through_equals_last_ts_and_row_count_matches(artifact):
    session = date(2026, 5, 12)
    runtime._write_intraday_bars_snapshot(
        frames_by_symbol={"SPY": _session_frame(session, n=4)},
        primary_symbol="SPY",
        generated_at=datetime(2026, 5, 12, 18, 0, tzinfo=timezone.utc),
        session_date=session,
    )
    entry = _read(artifact)["symbols"]["SPY"]
    assert entry["row_count"] == len(entry["bars"]) == 4
    assert entry["through"] == entry["bars"][-1][0]
    # Each row is [ts, O, H, L, C, V] with a tz-aware ts.
    assert all(len(row) == 6 for row in entry["bars"])
    assert datetime.fromisoformat(entry["bars"][0][0]).tzinfo is not None


@pytest.mark.parametrize("mutate", [
    "naive_index", "wrong_columns", "nonascending", "incoherent_ohlcv",
    "nonfinite", "nonpositive_price", "negative_volume",
])
def test_malformed_frame_omits_whole_symbol(artifact, mutate):
    session = date(2026, 5, 12)
    good = _session_frame(session)
    bad = _session_frame(session).copy()
    if mutate == "naive_index":
        bad.index = pd.DatetimeIndex([ts.replace(tzinfo=None) for ts in bad.index])
    elif mutate == "wrong_columns":
        bad = bad.rename(columns={"Close": "Adj"})
    elif mutate == "nonascending":
        bad = bad.iloc[::-1]
    elif mutate == "incoherent_ohlcv":
        bad.iloc[1, bad.columns.get_loc("High")] = 0.01  # High < max(Open, Close)
    elif mutate == "nonfinite":
        bad.iloc[1, bad.columns.get_loc("Close")] = float("inf")
    elif mutate == "nonpositive_price":
        bad.iloc[1, bad.columns.get_loc("Low")] = 0.0
    elif mutate == "negative_volume":
        bad.iloc[1, bad.columns.get_loc("Volume")] = -5
    runtime._write_intraday_bars_snapshot(
        frames_by_symbol={"GOOD": good, "BAD": bad},
        primary_symbol="GOOD",
        generated_at=datetime(2026, 5, 12, 18, 0, tzinfo=timezone.utc),
        session_date=session,
    )
    symbols = _read(artifact)["symbols"]
    assert "GOOD" in symbols  # the well-formed symbol is written
    assert "BAD" not in symbols  # any defect omits the WHOLE symbol (R4)


def test_prior_session_frame_is_omitted(artifact):
    session = date(2026, 5, 12)
    prior = _session_frame(date(2026, 5, 11))  # a different ET session
    runtime._write_intraday_bars_snapshot(
        frames_by_symbol={"SPY": _session_frame(session), "STALE": prior},
        primary_symbol="SPY",
        generated_at=datetime(2026, 5, 12, 18, 0, tzinfo=timezone.utc),
        session_date=session,  # R5: current session computed independently of the frame
    )
    symbols = _read(artifact)["symbols"]
    assert "SPY" in symbols and "STALE" not in symbols


def test_empty_frame_and_none_omit_symbol(artifact):
    session = date(2026, 5, 12)
    runtime._write_intraday_bars_snapshot(
        frames_by_symbol={"A": None, "B": pd.DataFrame(), "SPY": _session_frame(session)},
        primary_symbol="SPY",
        generated_at=datetime(2026, 5, 12, 18, 0, tzinfo=timezone.utc),
        session_date=session,
    )
    assert set(_read(artifact)["symbols"]) == {"SPY"}


# --- R2: seam selection + bounded acquisition -------------------------------

def test_seam_fetches_exactly_primary_and_spy_deduped(monkeypatch, tmp_path):
    calls: list[str] = []
    monkeypatch.setattr(runtime, "select_primary_card_symbol", lambda *a, **k: "AAPL")
    monkeypatch.setattr(runtime, "_fetch_intraday_card_bars",
                        lambda symbol: calls.append(symbol) or None)
    _drive_halted_seam(monkeypatch, tmp_path)
    assert calls == ["AAPL", "SPY"]  # exactly [primary, SPY], primary first


def test_seam_dedupes_when_primary_is_spy(monkeypatch, tmp_path):
    calls: list[str] = []
    monkeypatch.setattr(runtime, "select_primary_card_symbol", lambda *a, **k: "SPY")
    monkeypatch.setattr(runtime, "_fetch_intraday_card_bars",
                        lambda symbol: calls.append(symbol) or None)
    _drive_halted_seam(monkeypatch, tmp_path)
    assert calls == ["SPY"]  # deduped to a single acquisition


def test_seam_records_primary_and_writes_only_targets(monkeypatch, tmp_path):
    logs_dir = _isolate_seam_paths(monkeypatch, tmp_path)
    session = runtime.time_utils.convert_utc_to_et(datetime.now(timezone.utc)).date()
    monkeypatch.setattr(runtime, "select_primary_card_symbol", lambda *a, **k: "AAPL")
    monkeypatch.setattr(runtime, "_fetch_intraday_card_bars",
                        lambda symbol: _session_frame(session))
    _drive_halted_seam(monkeypatch, tmp_path)
    data = _read(logs_dir / "intraday_bars_snapshot.json")
    assert data["primary_symbol"] == "AAPL"
    assert set(data["symbols"]) == {"AAPL", "SPY"}


# --- R7: one isolation boundary, exactly-once notification ------------------

def test_fetch_raise_is_isolated_single_notification(monkeypatch, tmp_path):
    def _boom(symbol):
        raise RuntimeError("intraday fetch blew up")
    monkeypatch.setattr(runtime, "_fetch_intraday_card_bars", _boom)
    result, send = _drive_halted_seam(monkeypatch, tmp_path)
    assert result["status"] == runtime.SUMMARY_STATUS_SUCCESS  # no failure path
    assert send.call_count == 1  # exactly one notification, not the failure one


def test_writer_raise_is_isolated_single_notification(monkeypatch, tmp_path):
    def _boom(**kwargs):
        raise RuntimeError("serialize blew up")
    monkeypatch.setattr(runtime, "_write_intraday_bars_snapshot", _boom)
    result, send = _drive_halted_seam(monkeypatch, tmp_path)
    assert result["status"] == runtime.SUMMARY_STATUS_SUCCESS
    assert send.call_count == 1


# --- R11: best-effort acquisition budget ------------------------------------

def test_over_budget_block_logs_breach_without_raising(monkeypatch, tmp_path, caplog):
    # Each monotonic() call advances 100s. The block's start/elapsed calls are
    # consecutive (the stubbed fetch calls no monotonic), so the measured elapsed
    # is a deterministic 100s > 60s regardless of any prior calls in the seam.
    import itertools
    counter = itertools.count(0, 100)
    monkeypatch.setattr(runtime.time, "monotonic", lambda: float(next(counter)))
    monkeypatch.setattr(runtime, "select_primary_card_symbol", lambda *a, **k: "AAPL")
    monkeypatch.setattr(runtime, "_fetch_intraday_card_bars", lambda symbol: None)
    with caplog.at_level(logging.WARNING):
        result, send = _drive_halted_seam(monkeypatch, tmp_path)
    assert result["status"] == runtime.SUMMARY_STATUS_SUCCESS  # no raise into notification
    assert send.call_count == 1  # decision/notification unchanged
    assert any("budget breach" in rec.getMessage() for rec in caplog.records)


def test_card_fetch_is_single_attempt_timeout_25_no_retry():
    # R11: the A1-P card path passes timeout_seconds=25 to yf.download and makes
    # ONE attempt (retries=1, no backoff). The existing default caller passes no
    # override, so its call is byte-for-byte unchanged (no timeout kwarg).
    from cuttingboard import ingestion

    card_calls: list[dict] = []

    def _fake_download(symbol, **kwargs):
        card_calls.append(kwargs)
        # Return a minimal yfinance-shaped frame the fetcher can post-process.
        idx = pd.DatetimeIndex([datetime(2026, 5, 12, 14, 30, tzinfo=timezone.utc)])
        return pd.DataFrame(
            {"Open": [100.0], "High": [101.0], "Low": [99.0], "Close": [100.5], "Volume": [1000]},
            index=idx,
        )

    with (
        patch.object(ingestion, "_is_live_data_blocked", return_value=False),
        patch.object(ingestion.yf, "download", side_effect=_fake_download),
    ):
        # A1-P path (what _fetch_intraday_card_bars passes): one attempt,
        # timeout=25. Call the fetcher directly so the conftest autouse (which
        # no-ops the wrapper) does not mask the real ingestion behavior.
        ingestion.fetch_intraday_session_bars("SPY", timeout_seconds=25, retries=1)
        assert len(card_calls) == 1
        assert card_calls[0].get("timeout") == 25

        # Existing default caller: no timeout override in the yf.download call.
        card_calls.clear()
        ingestion.fetch_intraday_session_bars("SPY")
        assert card_calls and all("timeout" not in kw for kw in card_calls)


def test_default_intraday_caller_retry_behavior_unchanged():
    # An existing default caller retries config.FETCH_RETRIES times on failure;
    # the A1-P override (retries=1) does NOT change that default.
    from cuttingboard import ingestion, config
    attempts = {"n": 0}

    def _always_fail(symbol, **kwargs):
        attempts["n"] += 1
        raise ValueError("boom")

    with (
        patch.object(ingestion, "_is_live_data_blocked", return_value=False),
        patch.object(ingestion.yf, "download", side_effect=_always_fail),
        patch.object(ingestion.time, "sleep", lambda _s: None),
    ):
        ingestion.fetch_intraday_session_bars("SPY")  # no override => default retries
    assert attempts["n"] == config.FETCH_RETRIES


# --- R3 / R12: no network without opt-in ------------------------------------

def test_success_seam_makes_zero_live_card_fetch_under_autouse_default(monkeypatch, tmp_path):
    # R12: under the conftest autouse default (no opt-in), a representative seam
    # run performs ZERO live card fetches. Record at the DEEPER fetcher and filter
    # by the card signature (timeout_seconds=25) so the daily :1250 SPY fetch (no
    # override) is not miscounted. Do NOT override the autouse — removing the
    # autouse must turn this red.
    logs_dir = _isolate_seam_paths(monkeypatch, tmp_path)
    recorded: list[dict] = []

    def _recorder(symbol, **kwargs):
        recorded.append({"symbol": symbol, **kwargs})
        return None

    monkeypatch.setattr(runtime, "fetch_intraday_session_bars", _recorder)
    _drive_halted_seam(monkeypatch, tmp_path)
    card_calls = [c for c in recorded if c.get("timeout_seconds") == 25]
    assert card_calls == []  # the card fetch never fired (R12)
    # And the artifact records card omission (empty symbols map).
    data = _read(logs_dir / "intraday_bars_snapshot.json")
    assert data["symbols"] == {}


# --- R10: no decision effect ------------------------------------------------

def test_intraday_outcome_does_not_change_decision_output(monkeypatch, tmp_path):
    session = runtime.time_utils.convert_utc_to_et(datetime.now(timezone.utc)).date()

    def _run(card_fetch):
        _isolate_seam_paths(monkeypatch, tmp_path)
        monkeypatch.setattr(runtime, "select_primary_card_symbol", lambda *a, **k: "AAPL")
        monkeypatch.setattr(runtime, "_fetch_intraday_card_bars", card_fetch)
        titles: list[tuple] = []
        orig = runtime.format_failure_notification
        with (
            patch("cuttingboard.runtime.fetch_all", return_value={}),
            patch("cuttingboard.runtime.normalize_all", return_value={}),
            patch("cuttingboard.runtime.extract_fetch_failures", return_value={}),
            patch("cuttingboard.runtime.validate_quotes", return_value=_halted()),
            patch("cuttingboard.runtime.send_notification",
                  side_effect=lambda title, body, **k: titles.append((title, body)) or True),
        ):
            assert orig is runtime.format_failure_notification  # sanity: not the failure path
            result = _execute_notify_run(
                mode=MODE_LIVE, run_date=date(2026, 5, 12), notify_mode=NOTIFY_HOURLY
            )
        return result["status"], titles

    def _boom(symbol):
        raise RuntimeError("intraday down")

    status_ok, titles_ok = _run(lambda symbol: _session_frame(session))
    status_fail, titles_fail = _run(_boom)
    # The decision status and the (single) notification are identical whether the
    # intraday producer succeeds or fails: it has zero decision/notification effect.
    assert status_ok == status_fail == runtime.SUMMARY_STATUS_SUCCESS
    assert len(titles_ok) == len(titles_fail) == 1
    assert titles_ok == titles_fail


def _halted():
    validation = MagicMock(spec=runtime.ValidationSummary)
    validation.system_halted = True
    validation.halt_reason = "test halt"
    validation.valid_quotes = {}
    validation.symbols_validated = 0
    validation.symbols_attempted = 0
    return validation
