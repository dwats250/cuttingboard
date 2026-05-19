"""PRD-141: alert_runner cross-run slot dedup, force flag, premarket exemption."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from cuttingboard import alert_runner
from cuttingboard.notifications.hourly_slot import (
    LAST_HOURLY_SLOT_PATH,
    canonical_slot_utc,
    save_last_slot,
)


def _audit_path(tmp: Path) -> Path:
    return tmp / "logs" / "audit.jsonl"


def _notification_rows(tmp: Path) -> list[dict]:
    p = _audit_path(tmp)
    if not p.exists():
        return []
    return [
        json.loads(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("event") == "notification"
    ]


@pytest.fixture
def intraday_now():
    """Tuesday 2026-05-19 20:15Z = 1:15 PM PDT (intraday, non-premarket)."""
    return datetime(2026, 5, 19, 20, 15, 0, tzinfo=timezone.utc)


@pytest.fixture
def premarket_now():
    """2026-05-19 13:00Z = declared premarket cron minute."""
    return datetime(2026, 5, 19, 13, 0, 0, tzinfo=timezone.utc)


def _stub_execute(*, mode, run_date, notify_mode, slot_utc=None, **kwargs):
    """Stand in for _execute_notify_run: simulate a successful send and persist the slot."""
    if slot_utc is not None:
        save_last_slot(slot_utc)
    from cuttingboard.output import write_notification_audit
    write_notification_audit(
        transport="telegram",
        status="success",
        alert_title="hourly",
        attempted=True,
        success=True,
        state_key=slot_utc.isoformat() if slot_utc is not None else None,
    )
    return {"status": "SUCCESS", "suppressed": False}


def _stub_execute_failed_send(*, mode, run_date, notify_mode, slot_utc=None, **kwargs):
    """Simulate a failed send: audit row written, slot NOT persisted."""
    from cuttingboard.output import write_notification_audit
    write_notification_audit(
        transport="telegram",
        status="failed",
        alert_title="hourly",
        attempted=True,
        success=False,
        state_key=slot_utc.isoformat() if slot_utc is not None else None,
    )
    return {"status": "FAILED", "suppressed": False}


def test_same_slot_second_call_is_suppressed(tmp_path, monkeypatch, intraday_now):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()

    with (
        patch("cuttingboard.alert_runner.datetime") as mock_dt,
        patch("cuttingboard.runtime._execute_notify_run", _stub_execute),
    ):
        mock_dt.now.return_value = intraday_now
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
        assert alert_runner.main([]) == 0
        assert alert_runner.main([]) == 0

    rows = _notification_rows(tmp_path)
    statuses = [r["status"] for r in rows]
    assert statuses.count("success") == 1
    assert statuses.count("suppressed") == 1
    suppressed = next(r for r in rows if r["status"] == "suppressed")
    assert suppressed["reason"] == "suppressed_same_slot"
    assert suppressed["attempted"] is False
    assert suppressed["success"] is False


def test_force_slot_flag_bypasses_gate(tmp_path, monkeypatch, intraday_now):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()

    with (
        patch("cuttingboard.alert_runner.datetime") as mock_dt,
        patch("cuttingboard.runtime._execute_notify_run", _stub_execute),
    ):
        mock_dt.now.return_value = intraday_now
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
        assert alert_runner.main([]) == 0
        assert alert_runner.main(["--force-slot"]) == 0

    rows = _notification_rows(tmp_path)
    assert [r["status"] for r in rows].count("success") == 2
    assert not any(r["status"] == "suppressed" for r in rows)


def test_force_slot_env_var_bypasses_gate(tmp_path, monkeypatch, intraday_now):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    monkeypatch.setenv("CUTTINGBOARD_FORCE_SLOT", "1")

    with (
        patch("cuttingboard.alert_runner.datetime") as mock_dt,
        patch("cuttingboard.runtime._execute_notify_run", _stub_execute),
    ):
        mock_dt.now.return_value = intraday_now
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
        assert alert_runner.main([]) == 0
        assert alert_runner.main([]) == 0

    rows = _notification_rows(tmp_path)
    assert [r["status"] for r in rows].count("success") == 2


def test_failed_send_does_not_persist_slot(tmp_path, monkeypatch, intraday_now):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()

    slot_path = tmp_path / LAST_HOURLY_SLOT_PATH

    with (
        patch("cuttingboard.alert_runner.datetime") as mock_dt,
        patch("cuttingboard.runtime._execute_notify_run", _stub_execute_failed_send),
    ):
        mock_dt.now.return_value = intraday_now
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
        assert alert_runner.main([]) == 0

    assert not slot_path.exists()

    # Second invocation in same slot: store empty → re-attempts (now succeeds)
    with (
        patch("cuttingboard.alert_runner.datetime") as mock_dt,
        patch("cuttingboard.runtime._execute_notify_run", _stub_execute),
    ):
        mock_dt.now.return_value = intraday_now
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
        assert alert_runner.main([]) == 0

    rows = _notification_rows(tmp_path)
    statuses = [r["status"] for r in rows]
    assert statuses.count("failed") == 1
    assert statuses.count("success") == 1
    assert "suppressed" not in statuses


def test_premarket_invocation_bypasses_gate_then_intraday_also_sends(
    tmp_path, monkeypatch, premarket_now
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()

    intraday_next_hour = datetime(2026, 5, 19, 14, 0, 0, tzinfo=timezone.utc)

    with (
        patch("cuttingboard.alert_runner.datetime") as mock_dt,
        patch("cuttingboard.runtime._execute_notify_run", _stub_execute),
    ):
        mock_dt.now.return_value = premarket_now
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
        assert alert_runner.main([]) == 0

    with (
        patch("cuttingboard.alert_runner.datetime") as mock_dt,
        patch("cuttingboard.runtime._execute_notify_run", _stub_execute),
    ):
        mock_dt.now.return_value = intraday_next_hour
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
        assert alert_runner.main([]) == 0

    rows = _notification_rows(tmp_path)
    assert [r["status"] for r in rows].count("success") == 2


def test_persisted_slot_matches_canonical_slot(tmp_path, monkeypatch, intraday_now):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()

    with (
        patch("cuttingboard.alert_runner.datetime") as mock_dt,
        patch("cuttingboard.runtime._execute_notify_run", _stub_execute),
    ):
        mock_dt.now.return_value = intraday_now
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
        alert_runner.main([])

    slot_path = tmp_path / LAST_HOURLY_SLOT_PATH
    data = json.loads(slot_path.read_text(encoding="utf-8"))
    expected = canonical_slot_utc(intraday_now)
    assert data["slot_utc"] == expected.isoformat()
