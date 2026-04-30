from __future__ import annotations

import json
import runpy
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from cuttingboard import audit, runtime
from cuttingboard.notifications import NOTIFY_HOURLY


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "2026-04-12.json"
REQUIRED_SUMMARY_FIELDS = {
    "run_id",
    "timestamp",
    "run_at_utc",
    "mode",
    "status",
    "outcome",
    "regime",
    "posture",
    "confidence",
    "net_score",
    "permission",
    "kill_switch",
    "min_rr_applied",
    "data_status",
    "fallback_used",
    "system_halted",
    "halt_reason",
    "candidates_generated",
    "candidates_qualified",
    "candidates_watchlist",
    "chain_validation",
    "warnings",
    "errors",
}


def _isolate_artifacts(monkeypatch, tmp_path):
    logs_dir = tmp_path / "logs"
    reports_dir = tmp_path / "reports"
    monkeypatch.setattr(runtime, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(runtime, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(runtime, "LATEST_RUN_PATH", logs_dir / "latest_run.json")
    monkeypatch.setattr(runtime, "MARKET_MAP_PATH", logs_dir / "market_map.json")
    monkeypatch.setattr(runtime, "LATEST_CONTRACT_PATH", str(logs_dir / "latest_contract.json"))
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", str(logs_dir / "audit.jsonl"))
    return logs_dir, reports_dir


def _valid_summary(**overrides):
    summary = {
        "run_id": "fixture-2026-04-12",
        "timestamp": "2026-04-12T13:00:00Z",
        "run_at_utc": "2026-04-12T13:00:00Z",
        "mode": "FIXTURE",
        "status": "SUCCESS",
        "outcome": "TRADE",
        "regime": "RISK_ON",
        "posture": "AGGRESSIVE_LONG",
        "confidence": 0.875,
        "net_score": 7,
        "permission": "Long bias — trend continuation allowed.",
        "kill_switch": False,
        "min_rr_applied": 2.0,
        "data_status": "ok",
        "fallback_used": False,
        "system_halted": False,
        "halt_reason": None,
        "candidates_generated": 3,
        "candidates_qualified": 1,
        "candidates_watchlist": 1,
        "chain_validation": {
            "SPY": {
                "classification": "TOP_TRADE_VALIDATED",
                "reason": None,
            }
        },
        "warnings": [],
        "errors": [],
    }
    summary.update(overrides)
    return summary


def _write_summary(path: Path, summary: dict) -> None:
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _valid_contract(**overrides):
    contract = {
        "generated_at": "2026-04-12T13:00:00Z",
        "outcome": "NO_TRADE",
        "status": "STAY_FLAT",
        "system_state": {"tradable": False, "market_regime": "RISK_OFF"},
        "trade_candidates": [],
    }
    contract.update(overrides)
    return contract


def test_main_module_dispatches_to_cli(monkeypatch):
    monkeypatch.setattr(runtime, "cli_main", lambda: 7)

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("cuttingboard", run_name="__main__")

    assert excinfo.value.code == 7


def test_cli_main_fixture_dispatches_to_fixture_path(monkeypatch):
    captured = {}

    def _fake_execute_run(mode, run_date, fixture_file=None, notify_mode=None):
        captured["mode"] = mode
        captured["run_date"] = run_date
        captured["fixture_file"] = fixture_file
        return {"status": "SUCCESS"}

    monkeypatch.setattr(runtime, "execute_run", _fake_execute_run)

    rc = runtime.cli_main(
        ["--mode", "fixture", "--fixture-file", str(FIXTURE_PATH), "--date", "2026-04-12"]
    )

    assert rc == 0
    assert captured == {
        "mode": runtime.MODE_FIXTURE,
        "run_date": date.fromisoformat("2026-04-12"),
        "fixture_file": FIXTURE_PATH,
    }


def test_cli_main_verify_dispatches_to_verify_path(monkeypatch):
    captured = {}

    def _fake_verify(path):
        captured["path"] = path
        return {"pass": True, "warnings": [], "errors": []}

    monkeypatch.setattr(runtime, "verify_run_summary", _fake_verify)

    rc = runtime.cli_main(["--mode", "verify", "--file", "/tmp/run.json"])

    assert rc == 0
    assert captured == {"path": "/tmp/run.json"}


def test_cli_main_verify_defaults_to_latest_run(monkeypatch, tmp_path):
    summary_path = tmp_path / "latest_run.json"
    monkeypatch.setattr(runtime, "LATEST_RUN_PATH", summary_path)

    captured = {}

    def _fake_verify(path):
        captured["path"] = path
        return {"pass": True, "warnings": [], "errors": []}

    monkeypatch.setattr(runtime, "verify_run_summary", _fake_verify)

    rc = runtime.cli_main(["--mode", "verify"])

    assert rc == 0
    assert captured == {"path": str(summary_path)}


def test_cli_main_invalid_mode_fails_cleanly():
    with pytest.raises(SystemExit) as excinfo:
        runtime.cli_main(["--mode", "bogus"])

    assert excinfo.value.code != 0


def test_cli_main_auto_switches_live_to_sunday(monkeypatch):
    captured = {}

    def _fake_execute_run(mode, run_date, fixture_file=None, notify_mode=None):
        captured["mode"] = mode
        captured["run_date"] = run_date
        captured["fixture_file"] = fixture_file
        return {"status": "SUCCESS"}

    monkeypatch.setattr(runtime, "execute_run", _fake_execute_run)

    rc = runtime.cli_main(["--mode", "live", "--date", "2026-04-12"])

    assert rc == 0
    assert captured == {
        "mode": runtime.MODE_SUNDAY,
        "run_date": date.fromisoformat("2026-04-12"),
        "fixture_file": None,
    }


def test_fixture_run_writes_expected_artifacts_and_required_fields(monkeypatch, tmp_path):
    logs_dir, reports_dir = _isolate_artifacts(monkeypatch, tmp_path)

    summary = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )

    latest_path = logs_dir / "latest_run.json"
    run_paths = sorted(logs_dir.glob("run_*.json"))
    report_path = reports_dir / "2026-04-12.md"

    assert summary["status"] == "SUCCESS"
    assert latest_path.exists()
    assert len(run_paths) == 1
    assert report_path.exists()
    assert (logs_dir / "audit.jsonl").exists()
    assert (logs_dir / "latest_contract.json").exists()
    assert (logs_dir / "market_map.json").exists()

    latest_summary = json.loads(latest_path.read_text(encoding="utf-8"))
    timestamped_summary = json.loads(run_paths[0].read_text(encoding="utf-8"))
    latest_contract = json.loads((logs_dir / "latest_contract.json").read_text(encoding="utf-8"))
    market_map = json.loads((logs_dir / "market_map.json").read_text(encoding="utf-8"))

    assert REQUIRED_SUMMARY_FIELDS <= set(latest_summary)
    assert REQUIRED_SUMMARY_FIELDS <= set(timestamped_summary)
    assert latest_summary == timestamped_summary
    assert latest_contract["outcome"] in {"TRADE", "NO_TRADE", "HALT"}
    assert latest_contract["outcome"] == latest_summary["outcome"]
    assert market_map["schema_version"] == "market_map.v1"
    assert market_map["primary_symbols"] == ["SPY", "QQQ", "GDX", "GLD", "SLV", "XLE"]
    assert set(market_map["symbols"]) == {"SPY", "QQQ", "GDX", "GLD", "SLV", "XLE"}


def test_notify_mode_execute_run_writes_canonical_artifacts(monkeypatch, tmp_path):
    logs_dir, reports_dir = _isolate_artifacts(monkeypatch, tmp_path)

    summary = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
        notify_mode=NOTIFY_HOURLY,
    )

    latest_path = logs_dir / "latest_run.json"
    contract_path = logs_dir / "latest_contract.json"
    report_path = reports_dir / "2026-04-12.md"

    assert summary["status"] == "SUCCESS"
    assert latest_path.exists()
    assert contract_path.exists()
    assert report_path.exists()

    latest_summary = json.loads(latest_path.read_text(encoding="utf-8"))
    latest_contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert REQUIRED_SUMMARY_FIELDS <= set(latest_summary)
    assert latest_contract["outcome"] in {"TRADE", "NO_TRADE", "HALT"}
    assert latest_contract["outcome"] == latest_summary["outcome"]


def test_fixture_mode_does_not_invoke_fetch_all(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "fetch_all", lambda: pytest.fail("fixture mode called fetch_all"))

    summary = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )

    assert summary["status"] == "SUCCESS"


def test_fixture_run_is_deterministic_and_matches_pipeline(monkeypatch, tmp_path):
    logs_dir, reports_dir = _isolate_artifacts(monkeypatch, tmp_path)

    pipeline = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )

    summary_1 = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )
    report_1 = (reports_dir / "2026-04-12.md").read_text(encoding="utf-8")
    market_map_1 = json.loads((logs_dir / "market_map.json").read_text(encoding="utf-8"))

    summary_2 = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )
    report_2 = (reports_dir / "2026-04-12.md").read_text(encoding="utf-8")
    market_map_2 = json.loads((logs_dir / "market_map.json").read_text(encoding="utf-8"))

    scrubbed_1 = dict(summary_1)
    scrubbed_2 = dict(summary_2)
    for key in ("run_id", "timestamp"):
        scrubbed_1.pop(key, None)
        scrubbed_2.pop(key, None)

    assert scrubbed_1 == scrubbed_2
    assert report_1 == report_2
    assert market_map_1 == market_map_2
    assert report_1.startswith("Verification: PASS")
    assert "Verification: NOT RUN" not in report_1

    assert summary_1["timestamp"] == "2026-04-12T13:00:00Z"
    assert pipeline.summary["regime"] == pipeline.regime.regime
    assert pipeline.summary["posture"] == pipeline.regime.posture
    assert pipeline.summary["candidates_generated"] == pipeline.candidates_generated
    assert set(pipeline.summary["chain_validation"]) == set(pipeline.chain_results)

    assert logs_dir.joinpath("latest_run.json").exists()


def test_execute_run_writes_latest_summary_on_controlled_failure(monkeypatch, tmp_path):
    logs_dir, reports_dir = _isolate_artifacts(monkeypatch, tmp_path)

    fake_pipeline = SimpleNamespace(
        report_path=str(reports_dir / "2026-04-12.md"),
        report="pipeline report",
        date_str="2026-04-12",
        run_at_utc=runtime.datetime(2026, 4, 12, 13, 0, tzinfo=runtime.timezone.utc),
        summary=_valid_summary(),
    )

    def _fake_run_pipeline(*_args, **_kwargs):
        reports_dir.mkdir(parents=True, exist_ok=True)
        Path(fake_pipeline.report_path).write_text(fake_pipeline.report, encoding="utf-8")
        raise AssertionError(
            "trade-only formatter invoked for NO_TRADE run"
        )

    monkeypatch.setattr(runtime, "_run_pipeline", _fake_run_pipeline)

    summary = runtime.execute_run(
        mode=runtime.MODE_LIVE,
        run_date=date.fromisoformat("2026-04-12"),
    )

    latest_path = logs_dir / "latest_run.json"
    timestamped_runs = sorted(logs_dir.glob("run_*.json"))
    report_path = reports_dir / "2026-04-12.md"

    assert summary["status"] == "FAIL"
    assert latest_path.exists()
    assert len(timestamped_runs) == 1
    assert report_path.exists()

    latest_summary = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest_summary["status"] == "FAIL"
    assert latest_summary["system_halted"] is True
    assert any("trade-only formatter invoked" in error for error in latest_summary["errors"])

    report_text = report_path.read_text(encoding="utf-8")
    assert report_text.startswith("Verification: FAIL")


def test_safe_write_creates_file_when_missing(tmp_path):
    path = tmp_path / "latest_run.json"
    summary = _valid_summary()

    runtime.safe_write_latest(path, summary, "run_at_utc")

    assert json.loads(path.read_text(encoding="utf-8")) == summary


def test_safe_write_overwrites_when_newer(tmp_path):
    path = tmp_path / "latest_run.json"
    older = _valid_summary(run_at_utc="2026-04-12T12:00:00Z", timestamp="2026-04-12T12:00:00Z")
    newer = _valid_summary(run_at_utc="2026-04-12T13:00:00Z", timestamp="2026-04-12T13:00:00Z")
    _write_summary(path, older)

    runtime.safe_write_latest(path, newer, "run_at_utc")

    assert json.loads(path.read_text(encoding="utf-8")) == newer


def test_safe_write_rejects_older(tmp_path):
    path = tmp_path / "latest_run.json"
    newer = _valid_summary(run_at_utc="2026-04-12T13:00:00Z", timestamp="2026-04-12T13:00:00Z")
    older = _valid_summary(run_at_utc="2026-04-12T12:00:00Z", timestamp="2026-04-12T12:00:00Z")
    _write_summary(path, newer)

    runtime.safe_write_latest(path, older, "run_at_utc")

    assert json.loads(path.read_text(encoding="utf-8")) == newer


def test_safe_write_rejects_equal_timestamp(tmp_path):
    path = tmp_path / "latest_run.json"
    existing = _valid_summary()
    replacement = _valid_summary(status="FAIL", system_halted=True, halt_reason="should not overwrite")
    _write_summary(path, existing)

    runtime.safe_write_latest(path, replacement, "run_at_utc")

    assert json.loads(path.read_text(encoding="utf-8")) == existing


def test_safe_write_overwrites_legacy_artifact_without_timestamp(tmp_path):
    path = tmp_path / "latest_run.json"
    legacy = _valid_summary()
    legacy.pop("run_at_utc")
    replacement = _valid_summary(run_at_utc="2026-04-12T14:00:00Z", timestamp="2026-04-12T14:00:00Z")
    _write_summary(path, legacy)

    runtime.safe_write_latest(path, replacement, "run_at_utc")

    assert json.loads(path.read_text(encoding="utf-8")) == replacement


def test_missing_new_timestamp_raises_and_legacy_existing_overwrites(tmp_path):
    path = tmp_path / "latest_run.json"

    with pytest.raises(RuntimeError, match="Missing required timestamp field in new data: run_at_utc"):
        runtime.safe_write_latest(path, {"status": "SUCCESS"}, "run_at_utc")

    _write_summary(path, {"status": "SUCCESS"})
    runtime.safe_write_latest(path, _valid_summary(), "run_at_utc")
    assert REQUIRED_SUMMARY_FIELDS <= set(json.loads(path.read_text(encoding="utf-8")))


def test_safe_write_overwrites_legacy_contract_artifact_without_timestamp(tmp_path):
    path = tmp_path / "latest_contract.json"
    legacy = _valid_contract()
    legacy.pop("generated_at")
    replacement = _valid_contract(generated_at="2026-04-12T14:00:00Z", outcome="TRADE")
    _write_summary(path, legacy)

    runtime.safe_write_latest(path, replacement, "generated_at")

    assert json.loads(path.read_text(encoding="utf-8")) == replacement


def test_execute_run_overwrites_legacy_latest_summary(monkeypatch, tmp_path):
    logs_dir, reports_dir = _isolate_artifacts(monkeypatch, tmp_path)
    legacy_summary = _valid_summary()
    legacy_summary.pop("run_at_utc")
    logs_dir.mkdir(parents=True, exist_ok=True)
    _write_summary(logs_dir / "latest_run.json", legacy_summary)

    summary = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )

    latest_path = logs_dir / "latest_run.json"
    assert summary["status"] == "SUCCESS"
    assert json.loads(latest_path.read_text(encoding="utf-8"))["run_at_utc"] == "2026-04-12T13:00:00Z"
    assert (reports_dir / "2026-04-12.md").exists()


def test_latest_run_integrity_under_simulated_race(monkeypatch, tmp_path):
    logs_dir, _ = _isolate_artifacts(monkeypatch, tmp_path)
    older_at = runtime.datetime(2026, 4, 12, 12, 0, tzinfo=runtime.timezone.utc)
    newer_at = runtime.datetime(2026, 4, 12, 13, 0, tzinfo=runtime.timezone.utc)
    older = _valid_summary(run_id="older", timestamp="2026-04-12T12:00:00Z", run_at_utc="2026-04-12T12:00:00Z")
    newer = _valid_summary(run_id="newer", timestamp="2026-04-12T13:00:00Z", run_at_utc="2026-04-12T13:00:00Z")

    runtime._write_summary_files(newer, newer_at)
    runtime._write_summary_files(older, older_at)

    latest_summary = json.loads((logs_dir / "latest_run.json").read_text(encoding="utf-8"))
    older_timestamped = json.loads((logs_dir / "run_2026-04-12_120000.json").read_text(encoding="utf-8"))
    newer_timestamped = json.loads((logs_dir / "run_2026-04-12_130000.json").read_text(encoding="utf-8"))

    assert older_timestamped["run_id"] == "older"
    assert newer_timestamped["run_id"] == "newer"
    assert latest_summary["run_id"] == "newer"
    assert latest_summary == newer_timestamped


def test_latest_contract_integrity_under_simulated_race(monkeypatch, tmp_path):
    logs_dir, _ = _isolate_artifacts(monkeypatch, tmp_path)
    newer = _valid_contract(generated_at="2026-04-12T13:00:00Z", outcome="NO_TRADE")
    older = _valid_contract(generated_at="2026-04-12T12:00:00Z", outcome="HALT")

    runtime._write_contract_file(newer)
    runtime._write_contract_file(older)

    latest_contract = json.loads((logs_dir / "latest_contract.json").read_text(encoding="utf-8"))
    assert latest_contract == newer


def test_fixture_invalid_json_fails_immediately(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)
    broken_path = tmp_path / "broken_fixture.json"
    broken_path.write_text('{"SPY": {"symbol": "SPY"}', encoding="utf-8")

    summary = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=broken_path,
    )

    assert summary["status"] == "FAIL"
    assert any("invalid fixture JSON" in error for error in summary["errors"])


def test_fixture_schema_mismatch_identifies_symbol(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)
    mismatch_path = tmp_path / "bad_fixture.json"
    mismatch_path.write_text(
        json.dumps(
            {
                "SPY": {
                    "symbol": "SPY",
                    "price": 500.0,
                    "pct_change_decimal": 0.01,
                    "volume": 1000,
                    "fetched_at_utc": "2026-04-12T13:00:00Z",
                    "source": "fixture",
                    "units": "usd_price",
                    "unexpected": "boom",
                }
            }
        ),
        encoding="utf-8",
    )

    summary = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=mismatch_path,
    )

    assert summary["status"] == "FAIL"
    assert any("fixture[SPY] schema mismatch" in error for error in summary["errors"])


def test_sunday_mode_fixture_run_is_end_to_end_and_offline(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "fetch_all", lambda: pytest.fail("sunday fixture run called fetch_all"))
    monkeypatch.setattr(runtime, "send_notification", lambda *_args, **_kwargs: pytest.fail("sunday fixture run sent notification"))

    summary = runtime.execute_run(
        mode=runtime.MODE_SUNDAY,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )

    report = (tmp_path / "reports" / "2026-04-12.md").read_text(encoding="utf-8")

    assert summary["status"] == "SUCCESS"
    assert summary["mode"] == "SUNDAY"
    assert summary["candidates_generated"] == 0
    assert summary["candidates_qualified"] == 0
    assert report.startswith("Verification: PASS")
    assert "CUTTINGBOARD" in report


def test_verify_accepts_valid_summary(tmp_path):
    summary_path = tmp_path / "latest_run.json"
    _write_summary(summary_path, _valid_summary())

    result = runtime.verify_run_summary(str(summary_path))

    assert result == {"pass": True, "warnings": [], "errors": []}


def test_verify_accepts_stale_data_status(tmp_path):
    summary_path = tmp_path / "latest_run.json"
    _write_summary(summary_path, _valid_summary(data_status="stale"))

    result = runtime.verify_run_summary(str(summary_path))

    assert result["pass"] is True


def test_verify_rejects_missing_file(tmp_path):
    result = runtime.verify_run_summary(str(tmp_path / "missing.json"))

    assert result["pass"] is False
    assert any("file not found" in error for error in result["errors"])


def test_verify_rejects_malformed_json(tmp_path):
    broken_path = tmp_path / "broken.json"
    broken_path.write_text('{"status":"SUCCESS"', encoding="utf-8")

    result = runtime.verify_run_summary(str(broken_path))

    assert result["pass"] is False
    assert any("invalid JSON" in error for error in result["errors"])


@pytest.mark.parametrize(
    ("label", "mutate", "expected_error"),
    [
        ("missing required field", lambda s: s.pop("permission"), "missing required fields"),
        ("invalid mode", lambda s: s.__setitem__("mode", "BROKEN"), "invalid mode"),
        ("invalid status", lambda s: s.__setitem__("status", "BROKEN"), "invalid status"),
        ("invalid outcome", lambda s: s.__setitem__("outcome", "BROKEN"), "invalid outcome"),
        ("trade outcome contradiction", lambda s: s.update(outcome="TRADE", candidates_qualified=0), "TRADE outcome requires qualified candidates"),
        ("no trade outcome contradiction", lambda s: s.update(outcome="NO_TRADE", candidates_qualified=1), "NO_TRADE outcome cannot qualify trades"),
        ("invalid regime", lambda s: s.__setitem__("regime", "BROKEN"), "invalid regime"),
        ("invalid posture", lambda s: s.__setitem__("posture", "BROKEN"), "invalid posture"),
        ("confidence out of range", lambda s: s.__setitem__("confidence", 1.5), "confidence out of range"),
        ("net_score out of range", lambda s: s.__setitem__("net_score", 9), "net_score out of range"),
        ("invalid data_status", lambda s: s.__setitem__("data_status", "broken"), "invalid data_status"),
        ("timestamp invalid format", lambda s: s.__setitem__("timestamp", "2026-04-12"), "invalid timestamp"),
        ("kill_switch contradiction", lambda s: s.update(kill_switch=True, candidates_qualified=1), "kill_switch runs must not qualify trades"),
        ("chaotic contradiction", lambda s: s.update(regime="CHAOTIC", posture="STAY_FLAT", candidates_qualified=1), "CHAOTIC runs must not qualify trades"),
        ("stay flat contradiction", lambda s: s.update(posture="STAY_FLAT", candidates_qualified=1), "STAY_FLAT runs must not qualify trades"),
        ("neutral rr contradiction", lambda s: s.update(regime="NEUTRAL", posture="NEUTRAL_PREMIUM", min_rr_applied=2.0), "NEUTRAL runs must apply min_rr_applied == 3.0"),
        ("system halted contradiction", lambda s: s.update(system_halted=True, status="SUCCESS"), "system_halted runs must have status FAIL"),
        ("null non nullable", lambda s: s.__setitem__("permission", None), "permission must not be null"),
    ],
)
def test_verify_rejects_invalid_summaries(tmp_path, label, mutate, expected_error):
    summary = _valid_summary()
    mutate(summary)
    summary_path = tmp_path / f"{label.replace(' ', '_')}.json"
    _write_summary(summary_path, summary)

    result = runtime.verify_run_summary(str(summary_path))

    assert result["pass"] is False
    assert any(expected_error in error for error in result["errors"])


def test_failure_summary_no_longer_triggers_spurious_neutral_min_rr_error(tmp_path):
    summary_path = tmp_path / "failure.json"
    failure_summary = runtime._failure_summary(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        errors=["boom"],
        report_path=None,
    )
    _write_summary(summary_path, failure_summary)

    result = runtime.verify_run_summary(str(summary_path))

    assert result["pass"] is True
    assert not any("min_rr" in error for error in result["errors"])


def test_failure_summary_status_mismatch_reports_only_expected_error(tmp_path):
    summary_path = tmp_path / "failure_status.json"
    failure_summary = runtime._failure_summary(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        errors=["boom"],
        report_path=None,
    )
    failure_summary["status"] = "SUCCESS"
    _write_summary(summary_path, failure_summary)

    result = runtime.verify_run_summary(str(summary_path))

    assert result["pass"] is False
    assert result["errors"] == ["system_halted runs must have status FAIL"]


def test_verify_live_timestamp_too_old_fails(tmp_path):
    summary_path = tmp_path / "live.json"
    old_timestamp = (runtime.datetime.now(runtime.timezone.utc) - timedelta(hours=7)).isoformat().replace("+00:00", "Z")
    _write_summary(summary_path, _valid_summary(mode="LIVE", timestamp=old_timestamp))

    result = runtime.verify_run_summary(str(summary_path))

    assert result["pass"] is False
    assert any("timestamp older than 6 hours" in error for error in result["errors"])
