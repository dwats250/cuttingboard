"""PRD-296 — single notification ownership (reworked for the moved emission).

The runtime FAIL-owned sentinel is now emitted INSIDE _run_pipeline, immediately after the
single notification send and BEFORE the fallible post-send work (audit / evaluation /
performance / trend sidecar / SPY card). That placement is the fix: if the send succeeded
and any later post-send step raises, _run_pipeline still propagates the exception, but the
token is already on stdout, so the workflow terminal notifier (gated on CB_NOTIFIED) does not
fire a DUPLICATE. A SUCCESS attempt that only fails post-pipeline verification never emits, so
its verification-failure alert stays free to fire. execute_run no longer emits.

This file owns:
  - the (delivered AND pre_verification_fail) predicate,
  - the behavioral regression that the token survives a post-send exception (the finding),
  - the crux that a successful NON-FAIL send emits nothing,
  - the not-owned cases (send failure / suppressed send),
  - the unchanged workflow wiring.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from cuttingboard import audit, runtime
from cuttingboard.runtime import (
    FAIL_OWNED_SIGNAL,
    SUMMARY_STATUS_FAIL,
    SUMMARY_STATUS_SUCCESS,
    _emit_fail_owned_signal,
)

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "cuttingboard.yml"

# 2026-04-13 is a Monday: MODE_LIVE stays live. execute_run takes `mode` directly and does
# not auto-switch, but a weekday date keeps the intent honest. 2026-04-26 is a Sunday.
_LIVE_DATE = date(2026, 4, 13)
_SUNDAY = date(2026, 4, 26)


def _workflow():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _step(name):
    for step in _workflow()["jobs"]["pipeline"]["steps"]:
        if step.get("name") == name:
            return step
    raise AssertionError(f"step not found: {name}")


# --- Artifact isolation + real send-path harness ---------------------------------------

def _isolate_artifacts(monkeypatch, tmp_path):
    logs_dir = tmp_path / "logs"
    reports_dir = tmp_path / "reports"
    monkeypatch.setattr(runtime, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(runtime, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(runtime, "LATEST_RUN_PATH", logs_dir / "latest_run.json")
    monkeypatch.setattr(runtime, "MARKET_MAP_PATH", logs_dir / "market_map.json")
    monkeypatch.setattr(runtime, "LATEST_CONTRACT_PATH", str(logs_dir / "latest_contract.json"))
    monkeypatch.setattr(runtime, "LAST_STATE_PATH", str(tmp_path / "last_state.json"))
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", str(logs_dir / "audit.jsonl"))
    # TREND_STRUCTURE_PATH is a module constant (not LOGS_DIR-derived); a full MODE_LIVE run
    # refreshes it, so redirect it too or the tests pollute the committed repo sidecar.
    monkeypatch.setattr(runtime, "TREND_STRUCTURE_PATH", tmp_path / "trend_structure_snapshot.json")
    # Payload artifacts fan out to the delivery transport; keep them off disk. Orthogonal
    # to the ownership signal under test.
    monkeypatch.setattr(runtime, "_write_payload_artifacts", lambda *a, **k: None)
    return logs_dir, reports_dir


def _halted_summary():
    """A minimal but valid validation HALT carrier (system_halted True) — the pre-verification
    FAIL that owns the notification. Empty valid_quotes mirrors an all-symbols-failed halt."""
    return runtime.ValidationSummary(
        system_halted=True,
        halt_reason="Failed: SPY quote unavailable",
        failed_halt_symbols=["SPY"],
        results={},
        valid_quotes={},
        invalid_symbols={"SPY": "symbol not fetched"},
        symbols_attempted=1,
        symbols_validated=0,
        symbols_failed=1,
        halt_cause=runtime.HaltCause.VALIDATION,
    )


def _arm_live_halt(monkeypatch, tmp_path, *, send_result=True, should_send_result=True):
    """Drive the REAL MODE_LIVE pipeline to a validation HALT that reaches the single
    notification send, without any live data. Input loading and validation are the only
    stubs; the send gate, contract build, the _emit_fail_owned_signal call, and all post-send
    work run for real, so this exercises the actual emission placement inside _run_pipeline."""
    _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_load_inputs", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(runtime, "validate_quotes", lambda *a, **k: _halted_summary())
    monkeypatch.setattr(runtime, "should_send", lambda *a, **k: should_send_result)
    monkeypatch.setattr(runtime, "send_notification", lambda *a, **k: send_result)
    monkeypatch.setattr(runtime, "save_last_state", lambda *a, **k: None)


# --- Runtime predicate: the load-bearing (delivered AND pre_verification_fail) gate -----

@pytest.mark.parametrize(
    ("delivered", "pre_verification_fail", "expected_token"),
    [
        (True, True, True),     # delivered notification on a pre-verification FAIL -> owns
        (True, False, False),   # delivered SUCCESS (verification may later flip) -> never owns
        (False, True, False),   # send failed on a FAIL -> not owned
        (False, False, False),  # nothing delivered, not a FAIL -> not owned
    ],
)
def test_emit_predicate_requires_both_conjuncts(capsys, delivered, pre_verification_fail, expected_token):
    # Both conjuncts are load-bearing: dropping either (delivered, or the FAIL gate) changes
    # exactly one of these rows, so a mutation to either half of the `and` dies here.
    _emit_fail_owned_signal(delivered, pre_verification_fail)
    assert (FAIL_OWNED_SIGNAL in capsys.readouterr().out) is expected_token


# --- Behavioral regression: ownership survives a post-send exception (the finding) ------

def test_owned_fail_token_survives_post_send_exception_in_pipeline(monkeypatch, tmp_path, capsys):
    """THE finding. A delivered HALT notification, then the FIRST post-send step
    (_load_run_history) raises. Because the emission now sits immediately after the send and
    before that fallible work, the token is already on stdout when the exception propagates
    out of _run_pipeline. Move the emission to after the post-send work and the raise pre-empts
    it -> the assertion below fails. This is a real run, not a source-order check."""
    _arm_live_halt(monkeypatch, tmp_path)

    def _raise(*_a, **_k):
        raise RuntimeError("post-send audit history read failed")

    monkeypatch.setattr(runtime, "_load_run_history", _raise)

    with pytest.raises(RuntimeError, match="post-send audit history read failed"):
        runtime._run_pipeline(mode=runtime.MODE_LIVE, run_date=_LIVE_DATE, fixture_file=None)

    assert FAIL_OWNED_SIGNAL in capsys.readouterr().out


def test_owned_fail_token_survives_into_execute_run_fail(monkeypatch, tmp_path, capsys):
    """The finding as the workflow sees it. Same post-send raise, driven through execute_run
    (what the CLI/workflow invokes): execute_run's handler turns the raise into a FAIL run, but
    the token was emitted before the raise, so ownership is on stdout and the workflow terminal
    notifier (CB_NOTIFIED) suppresses its duplicate. Under the OLD placement (emit after
    _run_pipeline returned) the raise skipped the emission and the terminal double-sent."""
    _arm_live_halt(monkeypatch, tmp_path)

    def _raise(*_a, **_k):
        raise RuntimeError("post-send audit history read failed")

    monkeypatch.setattr(runtime, "_load_run_history", _raise)

    summary = runtime.execute_run(mode=runtime.MODE_LIVE, run_date=_LIVE_DATE)

    assert summary["status"] == SUMMARY_STATUS_FAIL          # the run genuinely failed
    assert FAIL_OWNED_SIGNAL in capsys.readouterr().out      # ...but ownership survived the raise


# --- Crux: a successful NON-FAIL send owns nothing --------------------------------------

def test_successful_non_fail_send_emits_no_token(monkeypatch, tmp_path, capsys):
    """A SUCCESS attempt (system_halted False, no errors) that delivers its notification must
    emit NO token, so if execute_run later flips it to FAIL via verification, or a later
    workflow step fails, the terminal notifier stays free to fire (PRD-295 no-regression).
    Driven via MODE_SUNDAY, which delivers offline (monkeypatched) and is never system_halted."""
    _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "should_send", lambda *a, **k: True)
    monkeypatch.setattr(runtime, "send_notification", lambda *a, **k: True)
    monkeypatch.setattr(runtime, "save_last_state", lambda *a, **k: None)

    summary = runtime.execute_run(mode=runtime.MODE_SUNDAY, run_date=_SUNDAY)

    assert summary["status"] == SUMMARY_STATUS_SUCCESS       # delivered, non-FAIL
    assert FAIL_OWNED_SIGNAL not in capsys.readouterr().out  # ...so it owns nothing


# --- Not owned: send failure and suppressed send ----------------------------------------

def test_send_failure_emits_no_token(monkeypatch, tmp_path, capsys):
    """Transport failure on a HALT: send_notification returns False -> alert_sent False ->
    not owned. The runtime sent nothing, so the terminal notifier must fire."""
    _arm_live_halt(monkeypatch, tmp_path, send_result=False)

    summary = runtime.execute_run(mode=runtime.MODE_LIVE, run_date=_LIVE_DATE)

    assert summary["status"] == SUMMARY_STATUS_FAIL
    assert FAIL_OWNED_SIGNAL not in capsys.readouterr().out


def test_suppressed_send_emits_no_token(monkeypatch, tmp_path, capsys):
    """Suppressed repeat on a HALT: should_send False -> no send -> alert_sent False ->
    not owned. Nothing was delivered, so the terminal notifier must fire."""
    _arm_live_halt(monkeypatch, tmp_path, should_send_result=False)

    summary = runtime.execute_run(mode=runtime.MODE_LIVE, run_date=_LIVE_DATE)

    assert summary["status"] == SUMMARY_STATUS_FAIL
    assert FAIL_OWNED_SIGNAL not in capsys.readouterr().out


# --- Workflow wiring (unchanged runtime <-> workflow contract) --------------------------

def test_terminal_notifier_suppressed_only_when_owned():
    step = _step("Notify on failure")
    assert step["if"] == "failure() && env.CB_NOTIFIED != 'true'"   # fires unless owned
    assert _workflow()["jobs"]["pipeline"]["steps"][-1]["name"] == "Notify on failure"  # still terminal


def test_execute_steps_capture_rc_and_relay_token():
    for name in ("Run live pipeline", "Run Sunday regime report"):
        run = _step(name)["run"]
        assert FAIL_OWNED_SIGNAL in run                     # greps the exact token
        assert "CB_NOTIFIED=true" in run                    # relays via $GITHUB_ENV
        assert "rc=${PIPESTATUS[0]}" in run                 # captures the CLI exit code
        assert 'exit "$rc"' in run                          # preserves the CLI exit code
        # PUBLISH_READY still gated on success (rc==0), so publish semantics are unchanged:
        assert 'if [ "$rc" -eq 0 ]; then echo "PUBLISH_READY=true"' in run


def test_ownership_cannot_be_established_by_prefetch_or_verify():
    for name in ("Run prefetch", "Verify run"):
        run = _step(name).get("run", "")
        assert FAIL_OWNED_SIGNAL not in run
        assert "CB_NOTIFIED" not in run


def test_signal_token_is_the_shared_literal():
    assert FAIL_OWNED_SIGNAL == "::CB_NOTIFY_OWNED_FAIL::"
    assert FAIL_OWNED_SIGNAL in _step("Run live pipeline")["run"]
