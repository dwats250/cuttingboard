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

# Captured at import time, BEFORE the conftest autouse (function-scoped) replaces
# the module attribute with a no-op, so tests can drive the REAL A1-P card-fetch
# wrapper and prove what it forwards (R11).
_REAL_CARD_FETCH = runtime._fetch_intraday_card_bars


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


def _daily_history_frame() -> pd.DataFrame:
    """A deterministic, OFFLINE 6-month-style daily OHLCV frame (the shape
    `runtime.fetch_ohlcv` returns: [Open, High, Low, Close, Volume] indexed by
    date) for use as the daily-history seam stub. Fixed content and a fixed
    business-day index ending 2026-04-22 (<= the run's completed-session cutoff),
    so the derived price_bars / trend_structure snapshots are byte-identical on
    every call and across every scenario run -- removing the ONLY remaining live
    input (the pre-existing daily fetch that `_collect_trend_structure_history`
    falls back to) without weakening the compared surface."""
    index = pd.bdate_range(end="2026-04-22", periods=60)
    closes = [100.0 + 0.1 * i for i in range(len(index))]
    data = {
        "Open": [c - 0.05 for c in closes],
        "High": [c + 0.20 for c in closes],
        "Low": [c - 0.25 for c in closes],
        "Close": closes,
        "Volume": [1_000_000 + i for i in range(len(index))],
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


def test_seam_null_primary_targets_spy_only(monkeypatch, tmp_path):
    # R2: a null primary (no chartable primary) must acquire EXACTLY [SPY] --
    # never zero targets. A mutation making null-primary produce no targets reddens
    # here (the null-primary artifact test alone cannot catch it: the autouse
    # omission yields an empty symbols map either way).
    calls: list[str] = []
    monkeypatch.setattr(runtime, "select_primary_card_symbol", lambda *a, **k: None)
    monkeypatch.setattr(runtime, "_fetch_intraday_card_bars",
                        lambda symbol: calls.append(symbol) or None)
    _drive_halted_seam(monkeypatch, tmp_path)
    assert calls == ["SPY"]


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


def test_real_card_fetch_wrapper_forwards_budget_args(monkeypatch):
    # R11: prove the REAL _fetch_intraday_card_bars wrapper (not the fetcher
    # called directly) forwards exactly timeout_seconds=25 and retries=1 in a
    # single call. Drives the captured original so the autouse no-op does not mask
    # it; records the underlying runtime.fetch_intraday_session_bars call. A
    # mutation dropping/altering either argument, or making a second call, reddens.
    calls: list[tuple] = []
    monkeypatch.setattr(
        runtime, "fetch_intraday_session_bars",
        lambda symbol, **kwargs: calls.append((symbol, kwargs)) or None,
    )
    _REAL_CARD_FETCH("SPY")
    assert len(calls) == 1
    assert calls[0][0] == "SPY"
    assert calls[0][1] == {"timeout_seconds": 25, "retries": 1}


# --- R3 / R12: no network without opt-in ------------------------------------

def test_success_seam_makes_zero_live_card_fetch_under_autouse_default(monkeypatch, tmp_path):
    # R12: under the conftest autouse default (no opt-in), a representative seam
    # run performs ZERO intraday fetches OF ANY KIND. The daily SPY session fetch
    # lives in _run_pipeline (runtime:1310), NOT in this _execute_notify_run path,
    # so the ONLY fetch_intraday_session_bars caller reachable here is the card
    # path; assert the COMPLETE recorded list is empty (a parallel unguarded fetch,
    # with or without the timeout kwarg, reddens). Do NOT override the autouse --
    # removing it must turn this red too.
    logs_dir = _isolate_seam_paths(monkeypatch, tmp_path)
    recorded: list[dict] = []

    def _recorder(symbol, **kwargs):
        recorded.append({"symbol": symbol, **kwargs})
        return None

    monkeypatch.setattr(runtime, "fetch_intraday_session_bars", _recorder)
    _drive_halted_seam(monkeypatch, tmp_path)
    assert recorded == []  # no intraday fetch of any kind fired at the seam (R12)
    # And the artifact records card omission (empty symbols map).
    data = _read(logs_dir / "intraday_bars_snapshot.json")
    assert data["symbols"] == {}


# --- R10: no decision effect (full baseline-neutral surface) ----------------

_HOURLY_SIDECARS = (
    "trend_structure_snapshot.json",
    "price_bars_snapshot.json",
    "watchlist_snapshot.json",
    "latest_hourly_market_map.json",
)


def test_intraday_producer_is_baseline_neutral_across_full_hourly_surface(monkeypatch, tmp_path):
    # R10: a VALID A1-P acquisition must not alter ANY pre-existing hourly truth.
    # Run the full-success hourly seam twice under a fixed clock (deterministic) --
    # once with a valid producer acquisition, once with the producer disabled --
    # and compare the COMPLETE surface: status, the whole hourly summary and
    # contract, the notification count and content, and every pre-existing hourly
    # sidecar. Only the NEW intraday artifact is excluded. Any coupling that lets a
    # valid acquisition rewrite an outcome/HALT/notification/existing artifact
    # reddens.
    from tests.test_hourly_alert import _regime, _router_state, _validation

    # run_at_utc == _regime().computed_at_utc == 2026-04-23 14:30 UTC (fixed), so
    # the ET session date is 2026-04-23; build the valid frame on that session.
    valid_frame = _session_frame(date(2026, 4, 23))

    # Each scenario runs in its OWN fresh dir so both see previous_market_map=None
    # (the hourly market map carries lifecycle state across runs; a shared dir
    # would make the 2nd run's map legitimately differ). Embedded absolute paths
    # are normalized out before comparison so only substantive content is compared.
    def _run(subdir: str, card_fetch):
        run_dir = tmp_path / subdir
        run_dir.mkdir()
        logs_dir = run_dir / "logs"
        monkeypatch.chdir(run_dir)
        for name, rel in {
            "LOGS_DIR": logs_dir,
            "REPORTS_DIR": run_dir / "reports",
            "LATEST_HOURLY_RUN_PATH": logs_dir / "latest_hourly_run.json",
            "LATEST_HOURLY_CONTRACT_PATH": logs_dir / "latest_hourly_contract.json",
            "LATEST_HOURLY_PAYLOAD_PATH": logs_dir / "latest_hourly_payload.json",
            "HOURLY_REPORT_PATH": run_dir / "reports" / "hourly_report.html",
            "MARKET_MAP_PATH": logs_dir / "market_map.json",
            "LATEST_HOURLY_MARKET_MAP_PATH": logs_dir / "latest_hourly_market_map.json",
            "TREND_STRUCTURE_PATH": logs_dir / "trend_structure_snapshot.json",
            "PRICE_BARS_PATH": logs_dir / "price_bars_snapshot.json",
            "WATCHLIST_PATH": logs_dir / "watchlist_snapshot.json",
            "INTRADAY_BARS_PATH": logs_dir / "intraday_bars_snapshot.json",
        }.items():
            monkeypatch.setattr(runtime, name, rel)
        monkeypatch.setattr(runtime, "fetch_all", lambda: {})
        monkeypatch.setattr(runtime, "normalize_all", lambda raw: {})
        monkeypatch.setattr(runtime, "extract_fetch_failures", lambda raw: {})
        monkeypatch.setattr(runtime, "validate_quotes", lambda nq, *a, **k: _validation())
        monkeypatch.setattr(runtime, "compute_regime",
                            lambda *a, **k: _regime(posture="STAY_FLAT", regime="NEUTRAL"))
        monkeypatch.setattr(runtime, "compute_all_derived", lambda *a, **k: {})
        monkeypatch.setattr(runtime, "resolve_sector_router", lambda *a, **k: _router_state())
        monkeypatch.setattr(runtime, "_fetch_observe_only_quotes", lambda: {})
        # Hermeticity: the pre-existing daily-history seam (`fetch_ohlcv`, which
        # `_collect_trend_structure_history` falls back to for every
        # TREND_STRUCTURE_SYMBOL since `compute_all_derived` is stubbed empty) is
        # the last live input. yfinance returns slightly different adjusted floats
        # between the two sequential scenario runs, which propagate into
        # price_bars_snapshot.json and trend_structure_snapshot.json and break the
        # byte-identity assertion. Pin it to a deterministic offline frame so BOTH
        # runs consume byte-identical daily OHLCV; the A1-P intraday producer
        # (the only variable under test) is still the sole difference between runs.
        monkeypatch.setattr(runtime, "fetch_ohlcv", lambda symbol: _daily_history_frame())
        monkeypatch.setattr(runtime, "select_primary_card_symbol", lambda *a, **k: "SPY")
        captured: dict = {}
        notifs: list[tuple] = []
        monkeypatch.setattr(runtime, "_write_hourly_artifacts",
                            lambda summary, contract: captured.update(summary=summary, contract=contract))
        monkeypatch.setattr(runtime, "send_notification",
                            lambda title, body, **k: notifs.append((title, body)) or True)
        monkeypatch.setattr(runtime, "_fetch_intraday_card_bars", card_fetch)
        result = _execute_notify_run(
            mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY
        )
        blob = json.dumps(
            {
                "status": result["status"],
                "summary": captured.get("summary"),
                "contract": captured.get("contract"),
                "notifs": notifs,
                "sidecars": {
                    name: (logs_dir / name).read_text(encoding="utf-8") if (logs_dir / name).exists() else None
                    for name in _HOURLY_SIDECARS
                },
            },
            sort_keys=True, default=str,
        ).replace(str(run_dir), "<RUN>")
        return result["status"], len(notifs), blob

    status_on, n_on, blob_on = _run("on", lambda symbol: valid_frame)
    status_off, n_off, blob_off = _run("off", lambda symbol: None)

    assert status_on == status_off == runtime.SUMMARY_STATUS_SUCCESS
    assert n_on == n_off == 1  # exactly-once notification in both
    # The COMPLETE hourly surface (status, full summary, contract, notification
    # count+content, and every pre-existing hourly sidecar) is byte-identical
    # whether the A1-P producer acquired valid bars or was disabled -- only the
    # NEW intraday artifact (excluded) differs. Zero decision/notification effect.
    assert blob_on == blob_off
