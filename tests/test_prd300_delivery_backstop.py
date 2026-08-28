"""PRD-300 — notification-delivery backstop for a transport-failed market-stress HALT.

A valid market-stress HALT concludes executor-SUCCESS (PRD-298, exit 0), so the workflow
failure() terminal notifier is unreachable. If its single owed Telegram send returns
FAILED_TRANSPORT, the HALT alert can reach ZERO recipients with a green job. This file owns:
  - the (system_halted AND MARKET_STRESS AND FAILED_TRANSPORT) emission predicate, each
    conjunct independently mutation-killed,
  - the fail-safe status read (a malformed/absent result never raises or emits),
  - the integration call site: the REAL execute_run/_run_pipeline emits the sentinel exactly
    when a market-stress HALT's real send yields FAILED_TRANSPORT, and execution_success is
    invariant to that,
  - the resend entrypoint's parity with the original successful-send path (identical owed
    message, footer, priority/state-key, one dispatch, audit, save_last_state), and its
    fail-open behavior on an invalid/absent contract,
  - the hourly path's structural non-reachability.
"""
from __future__ import annotations

import inspect
import json
from datetime import date

import pytest

from cuttingboard import audit, config, runtime
import cuttingboard.output as output
from cuttingboard.runtime import (
    DELIVERY_FAILED_SIGNAL,
    FAIL_OWNED_SIGNAL,
    SUMMARY_STATUS_FAIL,
    HaltCause,
    resend_owed_market_stress_halt_notification,
)

_LIVE_DATE = date(2026, 4, 13)   # Monday


# --- Harness ----------------------------------------------------------------------------

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
    monkeypatch.setattr(runtime, "TREND_STRUCTURE_PATH", tmp_path / "trend_structure_snapshot.json")
    monkeypatch.setattr(runtime, "PRICE_BARS_PATH", tmp_path / "price_bars_snapshot.json")
    monkeypatch.setattr(runtime, "_write_payload_artifacts", lambda *a, **k: None)
    # Reset the in-process notification result so a prior test's real send cannot leak a stale
    # FAILED_TRANSPORT status into a stubbed-send test via the module global.
    monkeypatch.setattr(output, "_last_notification_result", None)
    return logs_dir, reports_dir


def _healthy_summary():
    """A NON-halted validation carrier (system_halted False, errors implicit []). The valid
    market-stress halt is then reached via the kill-switch branch, which — unlike the
    validation-halt branch — never appends to errors, so errors stays [] (the exact state
    PRD-298 promotes to execution success)."""
    return runtime.ValidationSummary(
        system_halted=False,
        halt_reason=None,
        failed_halt_symbols=[],
        results={},
        valid_quotes={},
        invalid_symbols={},
        symbols_attempted=6,
        symbols_validated=6,
        symbols_failed=0,
    )


def _validation_halt_summary():
    """A real VALIDATION halt (system_halted True at the validation stage): the halt_reason is
    appended to errors, so this is an execution FAILURE (exit 1), already backstopped by the
    workflow failure() notifier."""
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
        halt_cause=HaltCause.VALIDATION,
    )


def _arm_live_market_stress(monkeypatch, tmp_path, *, post):
    """Drive the REAL MODE_LIVE pipeline to a VALID market-stress HALT (errors==[]) via the
    kill-switch branch, leaving the real notification send path intact (config present,
    requests.post controlled). Exercises the actual :981 send -> get_last_notification_result
    -> _emit_delivery_failed_signal wiring inside _run_pipeline."""
    logs_dir, _ = _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_load_inputs", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(runtime, "validate_quotes", lambda *a, **k: _healthy_summary())
    monkeypatch.setattr(runtime, "compute_regime", lambda *a, **k: None)
    monkeypatch.setattr(runtime, "_kill_switch", lambda *a, **k: True)   # market-stress trip
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(config, "TELEGRAM_CHAT_ID", "test-chat")
    monkeypatch.setattr(output.requests, "post", post)
    result = runtime.execute_run(
        mode=runtime.MODE_LIVE, run_date=_LIVE_DATE, fixture_file=None, notify_mode="premarket"
    )
    return result, logs_dir


def _arm_live_validation_halt(monkeypatch, tmp_path, *, post):
    """Drive the REAL MODE_LIVE pipeline to a VALIDATION halt with the real send path intact."""
    logs_dir, _ = _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_load_inputs", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(runtime, "validate_quotes", lambda *a, **k: _validation_halt_summary())
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(config, "TELEGRAM_CHAT_ID", "test-chat")
    monkeypatch.setattr(output.requests, "post", post)
    result = runtime.execute_run(
        mode=runtime.MODE_LIVE, run_date=_LIVE_DATE, fixture_file=None, notify_mode="premarket"
    )
    return result, logs_dir


def _post_conn_error(*_a, **_k):
    raise output.requests.exceptions.ConnectionError("transport down")


def _post_ok(*_a, **_k):
    class _Resp:
        status_code = 200
        text = "ok"
    return _Resp()


def _produce_market_stress_contract(monkeypatch, tmp_path):
    """Run a VALID market-stress HALT with the ORIGINAL send stubbed, so logs/latest_contract.json
    is written exactly as the runtime writes it — the artifact the resend reloads."""
    logs_dir, _ = _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_load_inputs", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(runtime, "validate_quotes", lambda *a, **k: _healthy_summary())
    monkeypatch.setattr(runtime, "compute_regime", lambda *a, **k: None)
    monkeypatch.setattr(runtime, "_kill_switch", lambda *a, **k: True)
    monkeypatch.setattr(runtime, "send_notification", lambda *a, **k: True)
    monkeypatch.setattr(runtime, "save_last_state", lambda *a, **k: None)
    result = runtime.execute_run(
        mode=runtime.MODE_LIVE, run_date=_LIVE_DATE, fixture_file=None, notify_mode="premarket"
    )
    assert result["status"] == SUMMARY_STATUS_FAIL
    assert result["errors"] == []
    assert result.execution_success is True
    # Restore the real send path so the resend under test dispatches for real; a test that
    # wants to instrument the resend send re-stubs runtime.send_notification after this call.
    monkeypatch.setattr(runtime, "send_notification", output.send_notification)
    return logs_dir


# --- Emission predicate: three individually load-bearing conjuncts (mutation matrix) ----

@pytest.mark.parametrize(
    ("system_halted", "halt_cause", "status", "expected"),
    [
        (True, HaltCause.MARKET_STRESS, "FAILED_TRANSPORT", True),    # the one case that resends
        (False, HaltCause.MARKET_STRESS, "FAILED_TRANSPORT", False),  # kills the system_halted conjunct
        (True, HaltCause.VALIDATION, "FAILED_TRANSPORT", False),      # kills the MARKET_STRESS conjunct (exit-1 path)
        (True, HaltCause.MARKET_STRESS, "SENT", False),              # kills the FAILED_TRANSPORT conjunct
        (True, HaltCause.MARKET_STRESS, "SKIPPED_NO_CONFIG", False),  # unconfigured -> no retry, no storm
        (True, HaltCause.MARKET_STRESS, "SUPPRESSED", False),
        (True, HaltCause.MARKET_STRESS, "NOT_REQUESTED", False),
    ],
)
def test_delivery_failed_predicate_matrix(capsys, system_halted, halt_cause, status, expected):
    runtime._emit_delivery_failed_signal(
        system_halted=system_halted, halt_cause=halt_cause, notification_status=status
    )
    assert (DELIVERY_FAILED_SIGNAL in capsys.readouterr().out) is expected


def test_delivery_failed_signal_literal_and_no_collision_with_owned():
    assert DELIVERY_FAILED_SIGNAL == "::CB_NOTIFY_DELIVERY_FAILED::"
    # Distinct from the FAIL-owned literal in BOTH directions: neither is a substring of the
    # other, so the workflow's two independent `grep -q` relays cannot cross-trigger.
    assert FAIL_OWNED_SIGNAL not in DELIVERY_FAILED_SIGNAL
    assert DELIVERY_FAILED_SIGNAL not in FAIL_OWNED_SIGNAL


# --- Fail-safe status read (PRD-300 R3) -------------------------------------------------

def test_safe_status_accessor_returns_sentinel_on_error(monkeypatch):
    def _boom():
        raise RuntimeError("bad result object")
    monkeypatch.setattr(runtime, "get_last_notification_result", _boom)
    assert runtime._safe_last_notification_status() == "NOT_REQUESTED"


def test_emit_does_not_raise_when_status_read_is_wrapped(capsys):
    # The emission helper must never raise even if handed a degenerate status.
    runtime._emit_delivery_failed_signal(system_halted=True, halt_cause=HaltCause.MARKET_STRESS, notification_status=None)
    assert DELIVERY_FAILED_SIGNAL not in capsys.readouterr().out


# --- Integration call site: the REAL execute_run/_run_pipeline path ----------------------

def test_market_stress_transport_failure_emits_at_call_site(monkeypatch, tmp_path, capsys):
    result, _ = _arm_live_market_stress(monkeypatch, tmp_path, post=_post_conn_error)
    out = capsys.readouterr().out
    assert DELIVERY_FAILED_SIGNAL in out                 # owed HALT alert failed transport -> resend requested
    assert result.execution_success is True              # PRD-298 unchanged: still an execution success
    assert result["status"] == SUMMARY_STATUS_FAIL       # domain truth preserved
    assert result["system_halted"] is True
    assert FAIL_OWNED_SIGNAL not in out                  # a market-stress HALT never owns FAIL (PRD-298)


def test_market_stress_transport_success_emits_no_sentinel(monkeypatch, tmp_path, capsys):
    result, _ = _arm_live_market_stress(monkeypatch, tmp_path, post=_post_ok)
    out = capsys.readouterr().out
    assert DELIVERY_FAILED_SIGNAL not in out             # SENT -> nothing to back up
    assert result.execution_success is True


def test_validation_halt_transport_failure_emits_no_sentinel(monkeypatch, tmp_path, capsys):
    result, _ = _arm_live_validation_halt(monkeypatch, tmp_path, post=_post_conn_error)
    out = capsys.readouterr().out
    assert DELIVERY_FAILED_SIGNAL not in out             # exit-1 path; already backstopped by failure()
    assert result.execution_success is False


def test_malformed_result_no_raise_no_emit_execution_success_unchanged(monkeypatch, tmp_path, capsys):
    logs_dir, _ = _isolate_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_load_inputs", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(runtime, "validate_quotes", lambda *a, **k: _healthy_summary())
    monkeypatch.setattr(runtime, "compute_regime", lambda *a, **k: None)
    monkeypatch.setattr(runtime, "_kill_switch", lambda *a, **k: True)
    monkeypatch.setattr(runtime, "send_notification", lambda *a, **k: False)   # transport failed
    monkeypatch.setattr(runtime, "save_last_state", lambda *a, **k: None)

    def _boom():
        raise RuntimeError("notification result inaccessible")
    monkeypatch.setattr(runtime, "get_last_notification_result", _boom)

    result = runtime.execute_run(
        mode=runtime.MODE_LIVE, run_date=_LIVE_DATE, fixture_file=None, notify_mode="premarket"
    )
    out = capsys.readouterr().out
    assert DELIVERY_FAILED_SIGNAL not in out             # fail-safe read -> NOT_REQUESTED -> no emit
    assert result.execution_success is True              # executor success invariant to result health
    assert result["status"] == SUMMARY_STATUS_FAIL


# --- Resend entrypoint parity with the original successful-send path (PRD-300 R6/R7) ----

def test_resend_reconstructs_identical_owed_message(monkeypatch, tmp_path):
    logs_dir = _produce_market_stress_contract(monkeypatch, tmp_path)
    contract = json.loads((logs_dir / "latest_contract.json").read_text(encoding="utf-8"))
    expected_title, expected_body = runtime.build_notification_message(contract)
    expected_priority = runtime.classify_notification_priority(contract).value
    expected_state_key = runtime.notification_state_key(contract)

    captured = {}
    def _capture(title, body, **kw):
        captured["title"], captured["body"], captured["kw"] = title, body, kw
        return True
    saved = []
    monkeypatch.setattr(runtime, "send_notification", _capture)
    monkeypatch.setattr(runtime, "save_last_state", lambda *a, **k: saved.append(a))

    ok = resend_owed_market_stress_halt_notification()

    assert ok is True
    assert captured["title"] == expected_title           # IDENTICAL owed message (pre-footer)
    assert captured["body"] == expected_body             # not a new meta-alert
    assert captured["kw"]["notification_priority"] == expected_priority
    assert captured["kw"]["notification_state_key"] == expected_state_key
    assert captured["kw"]["notify_mode"] == "premarket"
    assert saved and saved[0][0] == expected_state_key   # save_last_state(state_key, ...) on success


def test_resend_final_dispatch_carries_footer_one_send_and_audits(monkeypatch, tmp_path):
    logs_dir = _produce_market_stress_contract(monkeypatch, tmp_path)
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(config, "TELEGRAM_CHAT_ID", "test-chat")
    posts = []
    def _post(url, json=None, timeout=None):
        posts.append(json)
        class _Resp:
            status_code = 200
            text = "ok"
        return _Resp()
    monkeypatch.setattr(output.requests, "post", _post)

    ok = resend_owed_market_stress_halt_notification()

    assert ok is True
    assert len(posts) == 1                                # exactly one dispatch (send_telegram retry limit unchanged)
    assert output.DASHBOARD_URL in posts[0]["text"]       # final body carries the dashboard footer
    audit_lines = (logs_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert any('"event": "notification"' in line and '"success": true' in line for line in audit_lines)


def test_resend_persists_state_only_on_success(monkeypatch, tmp_path):
    _produce_market_stress_contract(monkeypatch, tmp_path)
    saved = []
    monkeypatch.setattr(runtime, "send_notification", lambda *a, **k: False)   # transport fails
    monkeypatch.setattr(runtime, "save_last_state", lambda *a, **k: saved.append(a))

    ok = resend_owed_market_stress_halt_notification()

    assert ok is False
    assert saved == []                                    # no dedup-state write on a failed resend


# --- Resend fail-open (PRD-300 R5) ------------------------------------------------------

def test_resend_fail_open_absent_contract(monkeypatch, tmp_path):
    _isolate_artifacts(monkeypatch, tmp_path)             # LATEST_CONTRACT_PATH points at a nonexistent file
    sent, saved = [], []
    monkeypatch.setattr(runtime, "send_notification", lambda *a, **k: sent.append(1) or True)
    monkeypatch.setattr(runtime, "save_last_state", lambda *a, **k: saved.append(1))

    assert resend_owed_market_stress_halt_notification() is False
    assert sent == [] and saved == []                     # no dispatch, no state write, no raise


def test_resend_fail_open_invalid_contract(monkeypatch, tmp_path):
    logs_dir, _ = _isolate_artifacts(monkeypatch, tmp_path)
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "latest_contract.json").write_text('{"not": "a valid finalized contract"}', encoding="utf-8")
    sent, saved = [], []
    monkeypatch.setattr(runtime, "send_notification", lambda *a, **k: sent.append(1) or True)
    monkeypatch.setattr(runtime, "save_last_state", lambda *a, **k: saved.append(1))

    # assert_valid_contract(finalized=True) rejects the malformed contract BEFORE reconstruction.
    assert resend_owed_market_stress_halt_notification() is False
    assert sent == [] and saved == []


# --- Hourly path structural non-reachability --------------------------------------------

def test_delivery_sentinel_only_reachable_from_daily_pipeline():
    # The emission lives in _run_pipeline (daily); the hourly path is a structurally separate
    # function that never calls it, so a market-stress-style hourly transport failure cannot
    # emit the daily backstop sentinel.
    assert "_emit_delivery_failed_signal" in inspect.getsource(runtime._run_pipeline)
    assert "_emit_delivery_failed_signal" not in inspect.getsource(runtime._execute_notify_run)
    assert DELIVERY_FAILED_SIGNAL not in inspect.getsource(runtime._execute_notify_run)
