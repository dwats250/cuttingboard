"""PRD-319 R5: season gate for the dual-seasonal OPEN fallback crons."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_open_fallback_window.py"
_spec = importlib.util.spec_from_file_location("check_open_fallback_window", _SCRIPT)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

PDT_CRON = "20 13 * * 1-5"
PST_CRON = "20 14 * * 1-5"


@pytest.mark.parametrize(
    "cron, now_utc, expected",
    [
        # In-season, on time (06:20 PT)
        (PDT_CRON, datetime(2026, 5, 19, 13, 20, tzinfo=timezone.utc), gate.IN_SEASON),
        (PST_CRON, datetime(2026, 1, 12, 14, 20, tzinfo=timezone.utc), gate.IN_SEASON),
        # In-season, DELIVERED LATE (the observed 45-55 min GitHub latency):
        # the season gate must still execute the fallback — R5 FAIL line.
        (PDT_CRON, datetime(2026, 5, 19, 14, 15, tzinfo=timezone.utc), gate.IN_SEASON),
        (PST_CRON, datetime(2026, 1, 12, 15, 30, tzinfo=timezone.utc), gate.IN_SEASON),
        # Off-season twins ALWAYS no-op, regardless of delivery time.
        (PDT_CRON, datetime(2026, 1, 12, 13, 20, tzinfo=timezone.utc), gate.OFF_SEASON_NOOP),
        (PDT_CRON, datetime(2026, 1, 12, 15, 0, tzinfo=timezone.utc), gate.OFF_SEASON_NOOP),
        (PST_CRON, datetime(2026, 5, 19, 14, 20, tzinfo=timezone.utc), gate.OFF_SEASON_NOOP),
        (PST_CRON, datetime(2026, 5, 19, 16, 0, tzinfo=timezone.utc), gate.OFF_SEASON_NOOP),
    ],
)
def test_season_verdicts(cron, now_utc, expected):
    assert gate.check(cron, now_utc) == expected


def test_unknown_cron_fails_closed():
    with pytest.raises(gate.UnknownCronError):
        gate.check("5 13 * * 1-5", datetime(2026, 5, 19, 13, 20, tzinfo=timezone.utc))
    with pytest.raises(gate.UnknownCronError):
        gate.check("", datetime(2026, 5, 19, 13, 20, tzinfo=timezone.utc))


def test_naive_datetime_rejected():
    with pytest.raises(ValueError):
        gate.check(PDT_CRON, datetime(2026, 5, 19, 13, 20))


def test_main_red_unknown_cron_exits_nonzero():
    """PRD-198 invariant 4: the fail-closed guard ships a red test — an unknown
    cron must exit NON-ZERO, never print a verdict."""
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        env={"CB_EVENT_SCHEDULE": "not-a-cron", "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 2
    assert "FAIL-CLOSED" in proc.stderr
    assert proc.stdout.strip() == ""


def test_main_prints_verdict_for_known_cron():
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        env={"CB_EVENT_SCHEDULE": PDT_CRON, "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() in (gate.IN_SEASON, gate.OFF_SEASON_NOOP)
