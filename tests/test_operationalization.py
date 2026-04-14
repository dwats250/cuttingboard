from __future__ import annotations

import json
import runpy
from datetime import date, timedelta
from pathlib import Path

import pytest

from cuttingboard import audit, runtime


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "2026-04-12.json"
REQUIRED_SUMMARY_FIELDS = {
    "run_id",
    "timestamp",
    "mode",
    "status",
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
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", str(logs_dir / "audit.jsonl"))
    return logs_dir, reports_dir


def _valid_summary(**overrides):
    summary = {
        "run_id": "fixture-2026-04-12",
        "timestamp": "2026-04-12T13:00:00Z",
        "mode": "FIXTURE",
        "status": "SUCCESS",
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


def test_main_module_dispatches_to_cli(monkeypatch):
    monkeypatch.setattr(runtime, "cli_main", lambda: 7)

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("cuttingboard", run_name="__main__")

    assert excinfo.value.code == 7


def test_cli_main_fixture_dispatches_to_fixture_path(monkeypatch):
    captured = {}

    def _fake_execute_run(mode, run_date, fixture_file=None, **kwargs):
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

    def _fake_execute_run(mode, run_date, fixture_file=None, **kwargs):
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

    latest_summary = json.loads(latest_path.read_text(encoding="utf-8"))
    timestamped_summary = json.loads(run_paths[0].read_text(encoding="utf-8"))

    assert REQUIRED_SUMMARY_FIELDS <= set(latest_summary)
    assert REQUIRED_SUMMARY_FIELDS <= set(timestamped_summary)
    assert latest_summary == timestamped_summary


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

    summary_2 = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )
    report_2 = (reports_dir / "2026-04-12.md").read_text(encoding="utf-8")

    scrubbed_1 = dict(summary_1)
    scrubbed_2 = dict(summary_2)
    for key in ("run_id", "timestamp"):
        scrubbed_1.pop(key, None)
        scrubbed_2.pop(key, None)

    assert scrubbed_1 == scrubbed_2
    assert report_1 == report_2
    assert report_1.startswith("Verification: PASS")
    assert "Verification: NOT RUN" not in report_1

    assert summary_1["timestamp"] == "2026-04-12T13:00:00Z"
    assert pipeline.summary["regime"] == pipeline.regime.regime
    assert pipeline.summary["posture"] == pipeline.regime.posture
    assert pipeline.summary["candidates_generated"] == pipeline.candidates_generated
    assert set(pipeline.summary["chain_validation"]) == set(pipeline.chain_results)

    assert logs_dir.joinpath("latest_run.json").exists()


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
    monkeypatch.setattr(runtime, "send_ntfy", lambda *_args, **_kwargs: pytest.fail("sunday fixture run sent ntfy"))

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
