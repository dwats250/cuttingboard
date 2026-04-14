from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from cuttingboard import audit, runtime
from cuttingboard.orb_replay import run_orb_observational_replay
from tests.test_orb_0dte import (
    _build_series,
    _long_morning_overrides,
    _option,
    _session,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "2026-04-12.json"


def _isolate_artifacts(monkeypatch, tmp_path):
    logs_dir = tmp_path / "logs"
    reports_dir = tmp_path / "reports"
    monkeypatch.setattr(runtime, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(runtime, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(runtime, "LATEST_RUN_PATH", logs_dir / "latest_run.json")
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", str(logs_dir / "audit.jsonl"))
    return logs_dir, reports_dir


def _clean_trend_session():
    spy = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"high": 102.55, "low": 102.10, "close": 102.50, "volume": 150},
            (7, 25): {"high": 102.95, "low": 102.45, "close": 102.90, "volume": 150},
            (7, 30): {"high": 103.20, "low": 102.80, "close": 103.10, "volume": 140},
        },
        end=(7, 30),
    )
    qqq = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"high": 102.60, "low": 102.05, "close": 102.52, "volume": 150},
            (7, 25): {"high": 103.00, "low": 102.48, "close": 102.94, "volume": 150},
            (7, 30): {"high": 103.25, "low": 102.82, "close": 103.14, "volume": 140},
        },
        end=(7, 30),
    )
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-CLEAN-C", option_type="call", strike=102.0, delta=0.50, premium=1.00, open_premium=0.80),
        _option(7, 20, symbol="SPY", contract_id="SPY-CLEAN-C", option_type="call", strike=102.0, delta=0.55, premium=1.55, open_premium=0.80),
        _option(7, 25, symbol="SPY", contract_id="SPY-CLEAN-C", option_type="call", strike=102.0, delta=0.60, premium=2.05, open_premium=0.80),
        _option(7, 30, symbol="SPY", contract_id="SPY-CLEAN-C", option_type="call", strike=102.0, delta=0.62, premium=2.12, open_premium=0.80),
    ]
    return _session(spy, qqq, spy_options, [])


def _chop_session():
    overrides = {
        (6, 35): {"open": 100.00, "high": 100.20, "low": 99.70, "close": 100.10, "volume": 100},
        (6, 40): {"high": 100.25, "low": 99.80, "close": 99.95, "volume": 100},
        (6, 45): {"high": 100.30, "low": 99.85, "close": 100.15, "volume": 100},
        (6, 50): {"high": 100.25, "low": 99.80, "close": 100.00, "volume": 100},
        (6, 55): {"high": 100.30, "low": 99.82, "close": 100.12, "volume": 100},
        (7, 0): {"high": 100.28, "low": 99.84, "close": 100.05, "volume": 100},
    }
    spy = _build_series(overrides, end=(12, 45))
    qqq = _build_series(overrides, end=(12, 45))
    return _session(spy, qqq, [], [])


def _scheduled_skip_session():
    spy = _build_series(_long_morning_overrides(), end=(7, 15))
    qqq = _build_series(_long_morning_overrides(), end=(7, 15))
    return _session(spy, qqq, [], [], scheduled=True)


def _headline_shock_session():
    spy = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"open": 102.20, "high": 103.20, "low": 102.15, "close": 103.05, "volume": 300, "headline": True},
        },
        end=(7, 20),
    )
    qqq = _build_series(
        {
            **_long_morning_overrides(),
            (7, 20): {"open": 102.18, "high": 103.10, "low": 102.10, "close": 102.98, "volume": 300, "headline": True},
        },
        end=(7, 20),
    )
    spy_options = [
        _option(7, 15, symbol="SPY", contract_id="SPY-HEADLINE-C", option_type="call", strike=102.0, delta=0.50, premium=1.00, open_premium=0.80),
        _option(7, 20, symbol="SPY", contract_id="SPY-HEADLINE-C", option_type="call", strike=102.0, delta=0.60, premium=1.20, open_premium=0.80),
    ]
    return _session(spy, qqq, spy_options, [])


def _power_hour_session():
    long_noon = {
        (12, 0): {"high": 101.55, "low": 100.95, "close": 101.50, "volume": 230},
        (12, 5): {"high": 101.90, "low": 101.35, "close": 101.85, "volume": 180},
        (12, 10): {"high": 102.20, "low": 101.70, "close": 102.15, "volume": 170},
    }
    base = {
        (6, 35): {"open": 100.00, "high": 100.25, "low": 99.85, "close": 100.10, "volume": 100},
        (6, 40): {"high": 100.35, "low": 100.00, "close": 100.30, "volume": 100},
        (6, 45): {"high": 100.55, "low": 100.20, "close": 100.50, "volume": 100},
        (6, 50): {"high": 100.75, "low": 100.40, "close": 100.70, "volume": 100},
        (6, 55): {"high": 100.95, "low": 100.60, "close": 100.80, "volume": 100},
        (7, 0): {"high": 101.10, "low": 100.70, "close": 101.00, "volume": 100},
    }
    spy = _build_series({**base, **long_noon}, end=(12, 10))
    qqq = _build_series({**base, **long_noon}, end=(12, 10))
    spy_options = [
        _option(12, 10, symbol="SPY", contract_id="SPY-NOON-C", option_type="call", strike=102.0, delta=0.49, premium=1.10, open_premium=0.70),
    ]
    return _session(spy, qqq, spy_options, [])


def _curated_sessions():
    return {
        "clean_trend": _clean_trend_session(),
        "chop": _chop_session(),
        "scheduled_event_skip": _scheduled_skip_session(),
        "headline_shock": _headline_shock_session(),
        "power_hour_continuation": _power_hour_session(),
    }


def test_orb_observation_path_is_inert_when_disabled(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)
    orb_session = _clean_trend_session()

    baseline = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )
    baseline_report = (tmp_path / "reports" / "2026-04-12.md").read_text(encoding="utf-8")

    disabled = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
        observe_orb_0dte=False,
        orb_session_input=orb_session,
    )
    disabled_report = (tmp_path / "reports" / "2026-04-12.md").read_text(encoding="utf-8")

    baseline_scrubbed = dict(baseline)
    disabled_scrubbed = dict(disabled)
    for key in ("run_id", "timestamp"):
        baseline_scrubbed.pop(key, None)
        disabled_scrubbed.pop(key, None)

    assert baseline_scrubbed == disabled_scrubbed
    assert disabled_report == baseline_report
    assert "orb_0dte_observation" not in disabled
    assert "ORB 0DTE OBSERVATION" not in disabled_report


def test_cli_shadow_mode_dispatches_explicit_orb_session(monkeypatch):
    captured = {}
    orb_session = _clean_trend_session()

    monkeypatch.setattr(runtime, "load_orb_session_fixture", lambda path: orb_session)

    def _fake_execute_run(mode, run_date, fixture_file=None, *, observe_orb_0dte=False, orb_session_input=None):
        captured["mode"] = mode
        captured["run_date"] = run_date
        captured["fixture_file"] = fixture_file
        captured["observe_orb_0dte"] = observe_orb_0dte
        captured["orb_session_input"] = orb_session_input
        return {"status": "SUCCESS"}

    monkeypatch.setattr(runtime, "execute_run", _fake_execute_run)

    rc = runtime.cli_main(
        [
            "--mode", "fixture",
            "--fixture-file", str(FIXTURE_PATH),
            "--date", "2026-04-12",
            "--observe-orb-0dte",
            "--orb-session-file", "/tmp/orb-session.json",
        ]
    )

    assert rc == 0
    assert captured == {
        "mode": runtime.MODE_FIXTURE,
        "run_date": date.fromisoformat("2026-04-12"),
        "fixture_file": FIXTURE_PATH,
        "observe_orb_0dte": True,
        "orb_session_input": orb_session,
    }


def test_orb_replay_runner_reviews_curated_sessions_and_keeps_outputs_compact(monkeypatch, tmp_path):
    logs_dir, reports_dir = _isolate_artifacts(monkeypatch, tmp_path)
    sessions = _curated_sessions()

    replay = run_orb_observational_replay(sessions)

    assert set(replay) == {
        "clean_trend",
        "chop",
        "scheduled_event_skip",
        "headline_shock",
        "power_hour_continuation",
    }

    assert replay["clean_trend"].observation["MODE"] == "ENABLED"
    assert replay["clean_trend"].observation["BIAS"] == "LONG"
    assert replay["clean_trend"].observation["selected_symbol"] == "SPY"
    assert replay["clean_trend"].observation["exit_cause"] == "TP2"

    assert replay["chop"].observation["MODE"] == "DISABLED"
    assert replay["chop"].observation["BIAS"] == "NONE"
    assert replay["chop"].observation["EXECUTION_READY"] is False
    assert replay["chop"].observation["selected_symbol"] is None
    assert replay["chop"].observation["qualification_audit"] == []

    assert replay["scheduled_event_skip"].observation["MODE"] == "DISABLED"
    assert replay["scheduled_event_skip"].observation["qualification_audit"] == ["SESSION_SKIPPED:SCHEDULED_HIGH_IMPACT_DAY"]

    assert replay["headline_shock"].observation["MODE"] == "DISABLED"
    assert replay["headline_shock"].observation["exit_cause"] == "HEADLINE"
    assert any(item.startswith("EXIT:HEADLINE@") for item in replay["headline_shock"].observation["exit_audit"])

    assert replay["power_hour_continuation"].observation["MODE"] == "ENABLED"
    assert replay["power_hour_continuation"].observation["EXECUTION_READY"] is True
    assert replay["power_hour_continuation"].observation["exit_cause"] is None
    assert replay["power_hour_continuation"].observation["selected_contract_summary"].startswith("SPY-NOON-C")

    for output in replay.values():
        assert "ORB 0DTE OBSERVATION" in output.report_block
        assert len(output.report_block.splitlines()) <= 10
        assert all(len(line) <= 160 for line in output.report_block.splitlines())

    runtime_summary = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
        observe_orb_0dte=True,
        orb_session_input=sessions["headline_shock"],
    )

    observation = runtime_summary["orb_0dte_observation"]
    report = (reports_dir / "2026-04-12.md").read_text(encoding="utf-8")
    latest_summary = json.loads((logs_dir / "latest_run.json").read_text(encoding="utf-8"))

    assert observation == latest_summary["orb_0dte_observation"]
    assert observation["MODE"] == "DISABLED"
    assert observation["BIAS"] == "NONE"
    assert observation["EXECUTION_READY"] is False
    assert observation["selected_symbol"] == "SPY"
    assert observation["exit_cause"] == "HEADLINE"
    assert observation["selected_contract_summary"].startswith("SPY-HEADLINE-C | strike=102.00")
    assert "ORB 0DTE OBSERVATION" in report
    assert "QUALIFICATION" in report
    assert "ENTERED:SPY:breakout@" in report
    assert "EXIT              HEADLINE | EXIT:HEADLINE@" in report
    assert len(observation["qualification_audit"]) <= 3
    assert len(observation["exit_audit"]) <= 2
