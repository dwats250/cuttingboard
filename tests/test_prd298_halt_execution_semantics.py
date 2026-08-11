"""PRD-298: a valid market-stress HALT is an EXECUTION success (daily path).

Behavioral + mutation tests for the execution/domain split: the process exit code
follows an execution-success signal, NOT the domain status, so a valid market-stress
kill-switch HALT exits 0 (and publishes) while a VALIDATION halt / crash / degraded
halt stays exit 1. The persisted domain status is never flipped.
"""
from __future__ import annotations

import json
from datetime import date

from cuttingboard import runtime
from cuttingboard.runtime import RunResult, _is_execution_success
from cuttingboard.validation import HaltCause
from tests.test_operationalization import FIXTURE_PATH, _isolate_artifacts
from tests.test_notification_ownership import _isolate_artifacts as _isolate_live_artifacts

SUCCESS = runtime.SUMMARY_STATUS_SUCCESS
FAIL = runtime.SUMMARY_STATUS_FAIL


# --- the execution-success predicate: core red + mutation tests ---------------

def test_normal_success_is_execution_success():
    assert _is_execution_success(
        verification_pass=True, status=SUCCESS, system_halted=False, halt_cause=None, errors=[]
    ) is True


def test_market_stress_halt_is_execution_success():
    # Domain status FAIL, but a valid observation -> execution success.
    assert _is_execution_success(
        verification_pass=True, status=FAIL, system_halted=True,
        halt_cause=HaltCause.MARKET_STRESS, errors=[],
    ) is True


def test_market_stress_halt_with_errors_is_failure():
    # RC1: the `not errors` guard. A degraded market-stress-labelled run stays failure.
    # (Mutation: dropping `not errors` from the predicate flips this to True.)
    assert _is_execution_success(
        verification_pass=True, status=FAIL, system_halted=True,
        halt_cause=HaltCause.MARKET_STRESS, errors=["boom"],
    ) is False


def test_validation_halt_is_failure():
    # A real VALIDATION halt carries errors (halt_reason appended); this fails via the
    # `not errors` clause. The MARKET_STRESS guard is isolated separately below.
    assert _is_execution_success(
        verification_pass=True, status=FAIL, system_halted=True,
        halt_cause=HaltCause.VALIDATION, errors=["missing HALT symbol"],
    ) is False


def test_non_market_stress_halt_with_no_errors_is_failure():
    # Isolates the MARKET_STRESS guard (PRD-198 #4): a system_halted run with NO errors
    # but a non-MARKET_STRESS cause must NOT be promoted. (Mutation: dropping the
    # `halt_cause == MARKET_STRESS` clause flips this to True -> the guard is red-tested
    # independently of the `not errors` clause.)
    assert _is_execution_success(
        verification_pass=True, status=FAIL, system_halted=True,
        halt_cause=HaltCause.VALIDATION, errors=[],
    ) is False


def test_market_stress_halt_with_failed_verification_is_failure():
    assert _is_execution_success(
        verification_pass=False, status=FAIL, system_halted=True,
        halt_cause=HaltCause.MARKET_STRESS, errors=[],
    ) is False


def test_plain_fail_is_failure():
    assert _is_execution_success(
        verification_pass=True, status=FAIL, system_halted=False, halt_cause=None, errors=[]
    ) is False


# --- RunResult carrier semantics ---------------------------------------------

def test_runresult_behaves_as_dict_and_carries_signal():
    r = RunResult({"status": FAIL, "system_halted": True}, execution_success=True)
    assert r["status"] == FAIL
    assert r == {"status": FAIL, "system_halted": True}  # dict equality ignores subclass + attribute
    assert r.execution_success is True


def test_runresult_attribute_is_not_serialized():
    # R2/R3: no new persisted artifact field.
    r = RunResult({"status": FAIL}, execution_success=True)
    assert "execution_success" not in json.loads(json.dumps(r))


# --- cli_main exit-code mapping: R1 / R3 fail-closed --------------------------

def _cli_fixture(monkeypatch, result):
    monkeypatch.setattr(runtime, "execute_run", lambda **kw: result)
    return runtime.cli_main(
        ["--mode", "fixture", "--fixture-file", str(FIXTURE_PATH), "--date", "2026-04-12"]
    )


def test_cli_main_exit_zero_on_execution_success(monkeypatch):
    assert _cli_fixture(monkeypatch, RunResult({"status": FAIL}, execution_success=True)) == 0


def test_cli_main_exit_one_on_execution_failure(monkeypatch):
    assert _cli_fixture(monkeypatch, RunResult({"status": SUCCESS}, execution_success=False)) == 1


def test_cli_main_fail_closed_on_absent_signal(monkeypatch):
    # R3: a bare dict (no execution_success attribute) fail-closes to rc=1 even with status SUCCESS.
    assert _cli_fixture(monkeypatch, {"status": SUCCESS}) == 1


# --- integration: a real market-stress HALT through execute_run --------------

def test_execute_run_market_stress_halt_is_execution_success_and_domain_preserved(monkeypatch, tmp_path):
    logs_dir, _reports_dir = _isolate_artifacts(monkeypatch, tmp_path)
    # Force the kill-switch branch on the normal fixture -> a valid MARKET_STRESS halt.
    monkeypatch.setattr(runtime, "_kill_switch", lambda *a, **k: True)

    result = runtime.execute_run(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=FIXTURE_PATH,
    )

    # Execution success (drives exit 0 / publish) ...
    assert isinstance(result, RunResult)
    assert result.execution_success is True
    # ... while the DOMAIN summary stays truthfully HALTed.
    assert result["status"] == FAIL
    assert result["system_halted"] is True
    assert result["outcome"] == "HALT"
    assert result["errors"] == []

    # The persisted artifact carries no execution_success field and stays FAIL.
    latest = json.loads((logs_dir / "latest_run.json").read_text(encoding="utf-8"))
    assert "execution_success" not in latest
    assert latest["status"] == FAIL
    assert latest["system_halted"] is True
    assert latest["outcome"] == "HALT"


# --- R6: the daily path owns exactly one HALT notification --------------------

def _halt_summary(halt_cause):
    return runtime.ValidationSummary(
        system_halted=True,
        halt_reason=runtime.KILL_SWITCH_HALT_REASON,
        failed_halt_symbols=[],
        results={},
        valid_quotes={},
        invalid_symbols={},
        symbols_attempted=6,
        symbols_validated=6,
        symbols_failed=0,
        halt_cause=halt_cause,
    )


def _drive_live_halt_and_count_sends(monkeypatch, tmp_path, halt_cause, *, should_send_result):
    """Drive the REAL MODE_LIVE pipeline to a halt with the given halt_cause and count sends.
    Mirrors the proven _arm_live_halt harness: input load + validation are the only stubs;
    the notify gate (force-send OR should_send) runs for real."""
    _isolate_live_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_load_inputs", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(runtime, "validate_quotes", lambda *a, **k: _halt_summary(halt_cause))
    monkeypatch.setattr(runtime, "should_send", lambda *a, **k: should_send_result)
    sends: list[int] = []
    monkeypatch.setattr(runtime, "send_notification", lambda *a, **k: (sends.append(1), True)[1])
    monkeypatch.setattr(runtime, "save_last_state", lambda *a, **k: None)
    runtime.execute_run(
        mode=runtime.MODE_LIVE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=None,
        notify_mode="premarket",
    )
    return sends


def test_market_stress_halt_sends_one_notification_even_when_dedup_would_suppress(monkeypatch, tmp_path):
    # R6: a market-stress HALT owns its single notification; a suppressing should_send is bypassed.
    sends = _drive_live_halt_and_count_sends(
        monkeypatch, tmp_path, HaltCause.MARKET_STRESS, should_send_result=False
    )
    assert len(sends) == 1


def test_market_stress_halt_sends_exactly_one_not_two_when_should_send_true(monkeypatch, tmp_path):
    # Single call site -> never a double, even when should_send also returns True.
    sends = _drive_live_halt_and_count_sends(
        monkeypatch, tmp_path, HaltCause.MARKET_STRESS, should_send_result=True
    )
    assert len(sends) == 1


def test_validation_halt_still_obeys_dedup_suppression(monkeypatch, tmp_path):
    # Control: the force-send is MARKET_STRESS-specific; a VALIDATION halt still suppresses.
    sends = _drive_live_halt_and_count_sends(
        monkeypatch, tmp_path, HaltCause.VALIDATION, should_send_result=False
    )
    assert len(sends) == 0
