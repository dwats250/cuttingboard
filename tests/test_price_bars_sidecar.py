"""PRD-320 — price-bars sidecar producer.

Guards the display-only `logs/price_bars_snapshot.json` writer: schema shape,
completed-session filtering (filter FIRST, window SECOND), the 40-bar cap,
per-symbol omission, catch-and-log failure semantics, atomic tmp-replace,
idempotence, `as_of` truth, once-per-seam binding of the collected frames, and
the display-only boundary. Every fixture is synthetic; no network, no cache
read, no wall-clock dependency.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import cuttingboard.runtime as runtime

REPO_ROOT = Path(__file__).resolve().parents[1]

# 2026-05-11 is a Monday; most_recent_completed_session_date(2026-05-12T14:00Z)
# is therefore 2026-05-11 and a row dated 2026-05-12 is the CURRENT session.
GENERATED_AT = datetime(2026, 5, 12, 14, 0, tzinfo=timezone.utc)
COMPLETED_CUTOFF = date(2026, 5, 11)


def _frame(dates: list[str], *, columns: tuple[str, ...] = ("Open", "High", "Low", "Close", "Volume")):
    """A synthetic OHLCV frame shaped exactly like a fetch_ohlcv/parquet frame:
    columns Open/High/Low/Close/Volume over a DatetimeIndex."""
    index = pd.DatetimeIndex(pd.to_datetime(dates), name="Date")
    data = {}
    for offset, column in enumerate(columns):
        base = 1000 if column == "Volume" else 100.0 + offset
        data[column] = [base + i for i in range(len(dates))]
    return pd.DataFrame(data, index=index)


def _sessions(count: int, *, end: date = COMPLETED_CUTOFF) -> list[str]:
    """`count` consecutive calendar days ending at `end` (weekend dates are fine
    as fixture input — the writer filters on the cutoff, not on weekday)."""
    days = pd.date_range(end=pd.Timestamp(end), periods=count, freq="D")
    return [d.date().isoformat() for d in days]


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    logs_dir = tmp_path / "logs"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(runtime, "PRICE_BARS_PATH", logs_dir / "price_bars_snapshot.json")
    return logs_dir / "price_bars_snapshot.json"


def _write(history, *, generated_at=GENERATED_AT, producer="hourly") -> None:
    runtime._write_price_bars_snapshot(
        history_by_symbol=history, generated_at=generated_at, producer=producer
    )


def _read(artifact: Path) -> dict:
    return json.loads(artifact.read_text(encoding="utf-8"))


# --- R2: schema shape --------------------------------------------------------


def test_schema_shape_is_exactly_the_packet_contract(isolated):
    _write({"SPY": _frame(_sessions(3))}, producer="daily")
    data = _read(isolated)

    assert set(data) == {"schema_version", "generated_at", "source", "columns", "symbols"}
    assert data["schema_version"] == 1
    assert data["generated_at"] == GENERATED_AT.isoformat()
    assert data["source"] == {
        "producer": "daily",
        "provider": "yfinance",
        "interval": "1d",
        "adjusted": True,
    }
    assert data["columns"] == ["date", "open", "high", "low", "close", "volume"]
    assert set(data["symbols"]["SPY"]) == {"as_of", "bars"}

    row = data["symbols"]["SPY"]["bars"][0]
    assert len(row) == 6
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[0])
    assert all(isinstance(v, float) for v in row[1:5])
    assert isinstance(row[5], int) and not isinstance(row[5], bool)


def test_producer_hourly_is_recorded_verbatim(isolated):
    _write({"SPY": _frame(_sessions(2))}, producer="hourly")
    assert _read(isolated)["source"]["producer"] == "hourly"


# --- R2: completed-session filtering (the red test) --------------------------


def test_current_session_row_never_survives_into_bars(isolated):
    """R2 FAIL line: a fixture frame containing a current-session row (dated
    AFTER most_recent_completed_session_date(generated_at)) must not appear."""
    dates = _sessions(5) + ["2026-05-12", "2026-05-13"]
    _write({"SPY": _frame(dates)})

    bars = _read(isolated)["symbols"]["SPY"]["bars"]
    written = [row[0] for row in bars]
    assert "2026-05-12" not in written
    assert "2026-05-13" not in written
    assert max(written) == COMPLETED_CUTOFF.isoformat()


def test_filter_runs_before_the_forty_bar_window(isolated):
    """Ordering guard: with >40 rows whose LAST rows are current-session, the
    window must slide BACK to end at the last completed session — not return the
    trailing 40 raw rows minus the excluded ones from a pre-sliced tail."""
    dates = _sessions(60) + ["2026-05-12", "2026-05-13", "2026-05-14"]
    _write({"SPY": _frame(dates)})

    bars = _read(isolated)["symbols"]["SPY"]["bars"]
    assert len(bars) == 40
    assert bars[-1][0] == COMPLETED_CUTOFF.isoformat()
    # The window's first bar is the 40th completed session counting back.
    assert bars[0][0] == _sessions(60)[-40]


def test_forty_bar_cap(isolated):
    _write({"SPY": _frame(_sessions(120))})
    assert len(_read(isolated)["symbols"]["SPY"]["bars"]) == 40


def test_short_frame_writes_every_completed_bar(isolated):
    _write({"SPY": _frame(_sessions(7))})
    assert len(_read(isolated)["symbols"]["SPY"]["bars"]) == 7


# --- R3: per-symbol validation and omission ----------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(None, id="absent_frame"),
        pytest.param(pd.DataFrame(), id="empty_frame"),
        pytest.param(_frame(_sessions(3), columns=("Open", "High", "Low", "Close")), id="no_volume"),
        pytest.param(_frame(_sessions(3), columns=("Close", "Volume")), id="missing_ohl"),
        pytest.param(_frame(["2026-05-12", "2026-05-13"]), id="zero_completed_rows"),
    ],
)
def test_bad_symbol_is_omitted_while_valid_siblings_serialize(isolated, bad):
    """R3: a symbol whose frame is absent, malformed, or yields zero completed
    rows is OMITTED entirely — never a partial entry — and the partial snapshot
    is legal: valid siblings still serialize."""
    _write({"SPY": _frame(_sessions(5)), "BAD": bad, "QQQ": _frame(_sessions(4))})

    data = _read(isolated)
    assert set(data["symbols"]) == {"SPY", "QQQ"}
    assert len(data["symbols"]["SPY"]["bars"]) == 5
    assert len(data["symbols"]["QQQ"]["bars"]) == 4


def test_nan_in_a_completed_row_omits_the_whole_symbol(isolated):
    df = _frame(_sessions(5))
    df.iloc[2, df.columns.get_loc("High")] = float("nan")
    _write({"SPY": df, "QQQ": _frame(_sessions(3))})

    assert set(_read(isolated)["symbols"]) == {"QQQ"}


def test_all_symbols_bad_still_writes_a_valid_empty_snapshot(isolated):
    _write({"SPY": None, "QQQ": pd.DataFrame()})
    data = _read(isolated)
    assert data["symbols"] == {}
    assert data["schema_version"] == 1


# --- R3: catch-and-log failure semantics (the writer-raise red test) ----------


def test_writer_exception_is_caught_and_logged_never_raised(isolated, monkeypatch, caplog):
    """R3 FAIL line: a writer-level exception must not escape to the seam (the
    run continues). PRD-278 R8 catch-and-log."""
    def _boom(*args, **kwargs):
        raise RuntimeError("session-date resolution blew up")

    monkeypatch.setattr(runtime.time_utils, "most_recent_completed_session_date", _boom)

    with caplog.at_level("ERROR"):
        _write({"SPY": _frame(_sessions(3))})  # must return normally

    assert not isolated.exists()
    assert any("price_bars_snapshot" in r.message for r in caplog.records)


def test_missing_logs_dir_is_created_not_raised(isolated):
    assert not isolated.parent.exists()
    _write({"SPY": _frame(_sessions(3))})
    assert isolated.exists()


# --- R3: atomicity -----------------------------------------------------------


def test_write_is_atomic_tmp_then_replace(isolated, monkeypatch):
    """R3 FAIL line: no non-atomic write path. A replace() failure must leave the
    PREVIOUS artifact byte-untouched (a half-written target is impossible), and a
    successful write leaves no tmp residue."""
    _write({"SPY": _frame(_sessions(5))})
    before = isolated.read_bytes()
    assert not list(isolated.parent.glob("*.tmp")), "tmp residue after a clean write"

    real_replace = Path.replace

    def _failing_replace(self, target):
        if str(target).endswith("price_bars_snapshot.json"):
            raise OSError("replace failed")
        return real_replace(self, target)

    monkeypatch.setattr(Path, "replace", _failing_replace)
    _write({"SPY": _frame(_sessions(9))})

    assert isolated.read_bytes() == before, "target mutated by a failed replace"


# --- R4: idempotence and as_of truth -----------------------------------------


def test_two_invocations_are_byte_identical_under_symbols(isolated):
    history = {"SPY": _frame(_sessions(50)), "QQQ": _frame(_sessions(12))}
    _write(history)
    first = json.dumps(_read(isolated)["symbols"], sort_keys=True)
    _write(history)
    second = json.dumps(_read(isolated)["symbols"], sort_keys=True)
    assert first == second


def test_as_of_equals_the_last_written_bar_date(isolated):
    _write({"SPY": _frame(_sessions(50) + ["2026-05-12"]), "QQQ": _frame(_sessions(3))})
    for record in _read(isolated)["symbols"].values():
        assert record["as_of"] == record["bars"][-1][0]
    assert _read(isolated)["symbols"]["SPY"]["as_of"] == COMPLETED_CUTOFF.isoformat()


# --- R2: the frames are bound ONCE per seam ----------------------------------


def test_hourly_seam_collects_history_once_and_threads_it_to_both_writers(tmp_path, monkeypatch):
    """R2 FAIL line: either seam calling _collect_trend_structure_history more
    than once per run. Drives the real hourly seam and asserts one call plus the
    SAME object reaching both sidecar writers."""
    from datetime import date as _date

    from cuttingboard.runtime import MODE_LIVE, _execute_notify_run
    from cuttingboard.notifications import NOTIFY_HOURLY

    monkeypatch.chdir(tmp_path)
    logs_dir = tmp_path / "logs"
    monkeypatch.setattr(runtime, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(runtime, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_RUN_PATH", logs_dir / "latest_hourly_run.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_CONTRACT_PATH", logs_dir / "latest_hourly_contract.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_PAYLOAD_PATH", logs_dir / "latest_hourly_payload.json")
    monkeypatch.setattr(runtime, "HOURLY_REPORT_PATH", tmp_path / "reports" / "hourly_report.html")
    monkeypatch.setattr(runtime, "MARKET_MAP_PATH", logs_dir / "market_map.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_MARKET_MAP_PATH", logs_dir / "latest_hourly_market_map.json")
    monkeypatch.setattr(runtime, "TREND_STRUCTURE_PATH", logs_dir / "trend_structure_snapshot.json")
    monkeypatch.setattr(runtime, "PRICE_BARS_PATH", logs_dir / "price_bars_snapshot.json")

    collected = {"SPY": _frame(_sessions(5))}
    calls: list[int] = []
    seen: list[object] = []

    def _counting_collect(candidate_ohlcv):
        calls.append(1)
        return collected

    def _capture_trend(*, normalized_quotes, history_by_symbol, generated_at):
        seen.append(history_by_symbol)

    real_bars = runtime._write_price_bars_snapshot

    def _capture_bars(*, history_by_symbol, generated_at, producer):
        seen.append(history_by_symbol)
        assert producer == "hourly"
        return real_bars(
            history_by_symbol=history_by_symbol, generated_at=generated_at, producer=producer
        )

    monkeypatch.setattr(runtime, "_collect_trend_structure_history", _counting_collect)
    monkeypatch.setattr(runtime, "_write_trend_structure_snapshot", _capture_trend)
    monkeypatch.setattr(runtime, "_write_price_bars_snapshot", _capture_bars)

    # A HALTed validation is the lightest path that still reaches the sidecar
    # seam (the trend/bars writers run outside the not-halted branch).
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
        patch("cuttingboard.runtime.send_notification", return_value=True),
    ):
        _execute_notify_run(
            mode=MODE_LIVE, run_date=_date(2026, 5, 12), notify_mode=NOTIFY_HOURLY
        )

    assert len(calls) == 1, f"_collect_trend_structure_history called {len(calls)} times"
    assert len(seen) == 2, "both sidecar writers must receive the bound frames"
    assert seen[0] is seen[1] is collected, "the two writers got different objects"
    assert (logs_dir / "price_bars_snapshot.json").exists()


def test_daily_seam_binds_history_once(monkeypatch):
    """R2 FAIL line, daily half. The full daily pipeline is far heavier than the
    hourly seam, so the binding is pinned structurally: the MODE_LIVE block that
    feeds the trend refresh and the bars writer calls the collector exactly once
    and passes a LOCAL to both."""
    import inspect

    source = inspect.getsource(runtime._run_pipeline)
    assert source.count("_collect_trend_structure_history(") == 1, (
        "the daily seam must bind _collect_trend_structure_history exactly once"
    )
    assert "history_by_symbol=trend_history" in source
    assert re.search(
        r"_write_price_bars_snapshot\(\s*history_by_symbol=trend_history,", source
    ), "the daily bars writer must receive the SAME bound local"


def test_writer_call_graph_contains_no_fetch(isolated):
    """R2 FAIL line: no yfinance/network symbol in the writer's call graph. The
    writer serializes frames HANDED to it — it never reaches for data itself."""
    import inspect

    source = inspect.getsource(runtime._write_price_bars_snapshot) + inspect.getsource(
        runtime._price_bars_rows
    )
    # `"yfinance"` appears only as the provenance LITERAL in source.provider;
    # the banned tokens below are call-shaped, so that literal is not one.
    for token in ("fetch_ohlcv", "fetch_all", "yf.", "requests", "urlopen", "download("):
        assert token not in source, f"the price-bars writer must not reference {token}"

    # And behaviorally: a run with fetch_ohlcv booby-trapped still writes.
    with patch("cuttingboard.runtime.fetch_ohlcv", side_effect=AssertionError("no fetch")):
        _write({"SPY": _frame(_sessions(3))})
    assert _read(isolated)["symbols"]["SPY"]["bars"]


# --- R6: display-only boundary ----------------------------------------------


def test_no_module_outside_the_writer_references_the_sidecar():
    """R6 FAIL line: `rg -l "price_bars_snapshot|PRICE_BARS_PATH"` over
    cuttingboard/ tools/ scripts/ ui/ returns only the two writer-side files."""
    pattern = re.compile(r"price_bars_snapshot|PRICE_BARS_PATH")
    allowed = {
        Path("cuttingboard/runtime/_constants.py"),
        Path("cuttingboard/runtime/__init__.py"),
    }
    offenders: list[str] = []
    for root in ("cuttingboard", "tools", "scripts", "ui"):
        base = REPO_ROOT / root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            rel = path.relative_to(REPO_ROOT)
            if rel in allowed:
                continue
            if pattern.search(text):
                offenders.append(str(rel))
    assert not offenders, (
        f"PRD-320 R6: the price-bars sidecar has no reader until PRD-321; found {offenders}"
    )
