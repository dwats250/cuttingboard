from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from cuttingboard import audit, config, orb_shadow, runtime
from tests.test_orb_observational_replay import FIXTURE_PATH, _clean_trend_session


def _isolate_artifacts(monkeypatch, tmp_path):
    logs_dir = tmp_path / "logs"
    reports_dir = tmp_path / "reports"
    data_dir = tmp_path / "data"
    monkeypatch.setattr(runtime, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(runtime, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(runtime, "LATEST_RUN_PATH", logs_dir / "latest_run.json")
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", str(logs_dir / "audit.jsonl"))
    monkeypatch.setattr(orb_shadow, "ORB_SHADOW_LEDGER_PATH", data_dir / "orb_0dte_ledger.jsonl")
    monkeypatch.setattr(orb_shadow, "ORB_SHADOW_SESSION_INPUT_DIR", data_dir / "orb_0dte_sessions")
    monkeypatch.setattr(orb_shadow, "ORB_SHADOW_STATUS_DIR", data_dir / "orb_0dte_status")
    monkeypatch.setattr(runtime, "ORB_SHADOW_STATUS_DIR", data_dir / "orb_0dte_status")
    return logs_dir, reports_dir, data_dir


def _ledger_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_orb_shadow_successful_end_of_session_write(monkeypatch, tmp_path):
    _, reports_dir, data_dir = _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(config, "ORB_SHADOW_ENABLED", True)
    monkeypatch.setattr(orb_shadow, "collect_orb_shadow_session_input", lambda run_date: _clean_trend_session())

    summary = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )

    ledger_records = _ledger_records(data_dir / "orb_0dte_ledger.jsonl")
    daily_status = json.loads((data_dir / "orb_0dte_status" / "2026-04-12.json").read_text(encoding="utf-8"))
    report = (reports_dir / "2026-04-12.md").read_text(encoding="utf-8")
    orb_lines = [
        line
        for line in report.splitlines()
        if "ORB 0DTE OBSERVATION" in line
        or "ORB SHADOW HEALTH" in line
        or "MODE" in line
        or "BIAS" in line
        or "EXECUTION_READY" in line
        or "SYMBOL" in line
        or "CONTRACT" in line
        or "QUALIFICATION" in line
        or "EXIT" in line
        or "session_date" in line
        or "orb_shadow_enabled" in line
        or "run_attempted" in line
        or "ledger_write_success" in line
        or "observation_status" in line
        or "selected_symbol" in line
        or "exit_cause" in line
    ]

    assert len(ledger_records) == 1
    assert ledger_records[0]["session_date"] == "2026-04-12"
    assert ledger_records[0]["timezone"] == "PT"
    assert ledger_records[0]["observation_status"] == "OK"
    assert ledger_records[0]["selected_symbol"] == "SPY"
    assert ledger_records[0]["selected_contract_summary"].startswith("SPY-CLEAN-C")
    assert summary["orb_0dte_observation"] == ledger_records[0]
    assert summary["orb_shadow_operational_status"] == daily_status
    assert daily_status == {
        "session_date": "2026-04-12",
        "orb_shadow_enabled": True,
        "run_attempted": True,
        "ledger_write_success": True,
        "observation_status": "OK",
        "selected_symbol": "SPY",
        "exit_cause": "TP2",
    }
    assert "ORB 0DTE OBSERVATION" in report
    assert "ORB SHADOW HEALTH" in report
    assert all(len(line) <= 160 for line in orb_lines)


def test_orb_shadow_ledger_is_append_only_per_session(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(config, "ORB_SHADOW_ENABLED", True)
    monkeypatch.setattr(orb_shadow, "collect_orb_shadow_session_input", lambda run_date: _clean_trend_session())

    runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )
    runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )

    ledger_records = _ledger_records(orb_shadow.ORB_SHADOW_LEDGER_PATH)
    assert len(ledger_records) == 1
    assert ledger_records[0]["session_date"] == "2026-04-12"


def test_orb_shadow_is_noop_when_disabled(monkeypatch, tmp_path):
    _, reports_dir, data_dir = _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(config, "ORB_SHADOW_ENABLED", False)

    def _unexpected_collection(run_date):
        raise AssertionError("shadow collector should not run when disabled")

    monkeypatch.setattr(orb_shadow, "collect_orb_shadow_session_input", _unexpected_collection)

    baseline = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )
    report = (reports_dir / "2026-04-12.md").read_text(encoding="utf-8")
    daily_status = json.loads((data_dir / "orb_0dte_status" / "2026-04-12.json").read_text(encoding="utf-8"))

    assert not (data_dir / "orb_0dte_ledger.jsonl").exists()
    assert "orb_0dte_observation" not in baseline
    assert baseline["orb_shadow_operational_status"] == daily_status
    assert daily_status == {
        "session_date": "2026-04-12",
        "orb_shadow_enabled": False,
        "run_attempted": False,
        "ledger_write_success": False,
        "observation_status": "NOOP_DISABLED",
        "selected_symbol": None,
        "exit_cause": None,
    }
    assert "ORB 0DTE OBSERVATION" not in report
    assert "ORB SHADOW HEALTH" in report
    assert "observation_status  NOOP_DISABLED" in report


def test_orb_shadow_missing_data_degrades_to_data_invalid_record(monkeypatch, tmp_path):
    _, reports_dir, data_dir = _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(config, "ORB_SHADOW_ENABLED", True)
    monkeypatch.setattr(orb_shadow, "collect_orb_shadow_session_input", lambda run_date: None)

    summary = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )

    ledger_records = _ledger_records(data_dir / "orb_0dte_ledger.jsonl")
    daily_status = json.loads((data_dir / "orb_0dte_status" / "2026-04-12.json").read_text(encoding="utf-8"))
    report = (reports_dir / "2026-04-12.md").read_text(encoding="utf-8")

    assert len(ledger_records) == 1
    assert ledger_records[0]["observation_status"] == "DATA_INVALID"
    assert ledger_records[0]["qualification_audit"] == ["DATA_INVALID:SESSION_INPUT_UNAVAILABLE"]
    assert ledger_records[0]["selected_symbol"] is None
    assert summary["orb_0dte_observation"]["observation_status"] == "DATA_INVALID"
    assert summary["orb_shadow_operational_status"] == daily_status
    assert daily_status["ledger_write_success"] is True
    assert daily_status["observation_status"] == "DATA_INVALID"
    assert "QUALIFICATION     DATA_INVALID:SESSION_INPUT_UNAVAILABLE" in report
    assert "observation_status  DATA_INVALID" in report


def test_runtime_behavior_is_unchanged_when_shadow_disabled(monkeypatch, tmp_path):
    _, reports_dir, _ = _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(config, "ORB_SHADOW_ENABLED", False)

    baseline = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )
    baseline_report = (reports_dir / "2026-04-12.md").read_text(encoding="utf-8")

    disabled = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )
    disabled_report = (reports_dir / "2026-04-12.md").read_text(encoding="utf-8")

    baseline_scrubbed = dict(baseline)
    disabled_scrubbed = dict(disabled)
    for key in ("run_id", "timestamp"):
        baseline_scrubbed.pop(key, None)
        disabled_scrubbed.pop(key, None)
    baseline_scrubbed.pop("orb_shadow_operational_status", None)
    disabled_scrubbed.pop("orb_shadow_operational_status", None)

    assert baseline_scrubbed == disabled_scrubbed
    assert "ORB SHADOW HEALTH" in baseline_report
    assert baseline_report == disabled_report
