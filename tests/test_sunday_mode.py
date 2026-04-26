"""
PRD-019: Sunday mode isolation and non-live data execution.

AC1: sunday mode is resolved from 'live' on a Sunday run date
AC2: no live data calls occur in sunday mode
AC3: pipeline completes successfully with no live data
AC4: contract.tradable == False
AC5: exactly one notification is sent
AC6: run_status != ERROR
AC7: block_live_data guard raises if fetch_all is called
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from cuttingboard import audit, runtime
from cuttingboard.contract import STATUS_ERROR
from cuttingboard.ingestion import block_live_data, fetch_all


# Sunday date for tests: 2026-04-26 is a Sunday
_SUNDAY = date(2026, 4, 26)
_WEEKDAY = date(2026, 4, 25)  # Saturday → stays live (not auto-sunday)


def _isolate_artifacts(monkeypatch, tmp_path):
    logs_dir = tmp_path / "logs"
    reports_dir = tmp_path / "reports"
    monkeypatch.setattr(runtime, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(runtime, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(runtime, "LATEST_RUN_PATH", logs_dir / "latest_run.json")
    monkeypatch.setattr(runtime, "LAST_STATE_PATH", str(tmp_path / "last_state.json"))
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", str(logs_dir / "audit.jsonl"))
    return logs_dir, reports_dir


def _suppress_notification(monkeypatch):
    """Suppress notification delivery; return a call-count list."""
    calls = []

    def _mock_send(message, notification_priority=None, notification_state_key=None):
        calls.append(message)
        return True

    monkeypatch.setattr(runtime, "send_notification", _mock_send)
    monkeypatch.setattr(runtime, "should_send", lambda *_: True)
    monkeypatch.setattr(runtime, "save_last_state", lambda *_: None)
    return calls


# ---------------------------------------------------------------------------
# AC1: cron → mode mapping
# ---------------------------------------------------------------------------

def test_sunday_mode_resolved_from_live_on_sunday():
    result = runtime._resolve_effective_mode("live", _SUNDAY)
    assert result == runtime.MODE_SUNDAY


def test_live_mode_not_overridden_on_weekday():
    result = runtime._resolve_effective_mode("live", _WEEKDAY)
    assert result == runtime.MODE_LIVE


def test_sunday_mode_explicit_is_not_overridden():
    result = runtime._resolve_effective_mode("sunday", _WEEKDAY)
    assert result == runtime.MODE_SUNDAY


# ---------------------------------------------------------------------------
# AC2: no live data calls in sunday mode
# ---------------------------------------------------------------------------

def test_sunday_mode_does_not_call_fetch_all(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)
    _suppress_notification(monkeypatch)

    monkeypatch.setattr(
        runtime,
        "fetch_all",
        lambda: pytest.fail("sunday mode must not call fetch_all"),
    )

    summary = runtime.execute_run(
        mode=runtime.MODE_SUNDAY,
        run_date=_SUNDAY,
    )

    assert summary["status"] == runtime.SUMMARY_STATUS_SUCCESS


# ---------------------------------------------------------------------------
# AC3: pipeline completes with no live data
# ---------------------------------------------------------------------------

def test_sunday_pipeline_completes_with_no_data(monkeypatch, tmp_path):
    logs_dir, reports_dir = _isolate_artifacts(monkeypatch, tmp_path)
    _suppress_notification(monkeypatch)

    summary = runtime.execute_run(
        mode=runtime.MODE_SUNDAY,
        run_date=_SUNDAY,
    )

    assert summary["status"] == runtime.SUMMARY_STATUS_SUCCESS
    assert summary["mode"] == runtime.SUMMARY_MODE_SUNDAY
    assert (logs_dir / "latest_run.json").exists()
    assert (reports_dir / f"{_SUNDAY.isoformat()}.md").exists()


# ---------------------------------------------------------------------------
# AC4: contract.tradable == False
# ---------------------------------------------------------------------------

def test_sunday_contract_tradable_false(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)
    _suppress_notification(monkeypatch)

    pipeline = runtime._run_pipeline(
        mode=runtime.MODE_SUNDAY,
        run_date=_SUNDAY,
        fixture_file=None,
    )

    assert pipeline.contract["system_state"]["tradable"] is False


# ---------------------------------------------------------------------------
# AC5: exactly one notification is sent
# ---------------------------------------------------------------------------

def test_sunday_notification_sent_exactly_once(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)
    send_calls = _suppress_notification(monkeypatch)

    runtime.execute_run(
        mode=runtime.MODE_SUNDAY,
        run_date=_SUNDAY,
    )

    assert len(send_calls) == 1


# ---------------------------------------------------------------------------
# AC6: run_status != ERROR
# ---------------------------------------------------------------------------

def test_sunday_run_status_not_error(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)
    _suppress_notification(monkeypatch)

    pipeline = runtime._run_pipeline(
        mode=runtime.MODE_SUNDAY,
        run_date=_SUNDAY,
        fixture_file=None,
    )

    assert pipeline.contract["status"] != STATUS_ERROR


def test_sunday_contract_status_is_stay_flat_or_ok(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)
    _suppress_notification(monkeypatch)

    pipeline = runtime._run_pipeline(
        mode=runtime.MODE_SUNDAY,
        run_date=_SUNDAY,
        fixture_file=None,
    )

    assert pipeline.contract["status"] in {"STAY_FLAT", "OK"}


# ---------------------------------------------------------------------------
# AC7: block_live_data guard raises on live fetch attempt
# ---------------------------------------------------------------------------

def test_live_data_guard_raises_if_fetch_all_called():
    with block_live_data():
        with pytest.raises(RuntimeError, match="LIVE_DATA_FORBIDDEN_IN_SUNDAY_MODE"):
            fetch_all()


def test_live_data_guard_raises_for_intraday_bars():
    from cuttingboard.ingestion import fetch_intraday_bars
    with block_live_data():
        with pytest.raises(RuntimeError, match="LIVE_DATA_FORBIDDEN_IN_SUNDAY_MODE"):
            fetch_intraday_bars("SPY")


def test_live_data_guard_does_not_affect_other_threads():
    """Guard is thread-local: activating in one thread doesn't block another."""
    import threading

    errors = []

    def _try_call_without_guard():
        # This thread has no block_live_data active, so calling fetch_all
        # must not raise the guard error (it may raise for other reasons).
        try:
            # We just verify the guard check itself doesn't interfere
            from cuttingboard.ingestion import _is_live_data_blocked
            if _is_live_data_blocked():
                errors.append("guard leaked into other thread")
        except Exception as exc:
            errors.append(str(exc))

    with block_live_data():
        t = threading.Thread(target=_try_call_without_guard)
        t.start()
        t.join()

    assert not errors


def test_live_data_guard_released_after_context_exits():
    from cuttingboard.ingestion import _is_live_data_blocked
    with block_live_data():
        assert _is_live_data_blocked()
    assert not _is_live_data_blocked()
