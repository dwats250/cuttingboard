"""PRD-296 — single notification ownership.

Proves the runtime FAIL-owned sentinel and the workflow suppression it drives: the generic
PRD-295 terminal notifier fires for every outcome EXCEPT one the runtime already owns and
sent (a delivered notification on a PRE-verification FAIL attempt). A SUCCESS attempt - even
one execute_run later flips to FAIL via post-pipeline verification - never emits the token,
so its verification-failure alert is not suppressed (the crux the Stage-0 review pinned).
"""
from __future__ import annotations

import inspect
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import yaml

from cuttingboard import runtime
from cuttingboard.runtime import (
    FAIL_OWNED_SIGNAL,
    SUMMARY_STATUS_FAIL,
    SUMMARY_STATUS_SUCCESS,
    _emit_fail_owned_signal,
)

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "cuttingboard.yml"


def _workflow():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _step(name):
    for step in _workflow()["jobs"]["pipeline"]["steps"]:
        if step.get("name") == name:
            return step
    raise AssertionError(f"step not found: {name}")


def _contract(notification_sent):
    return {"artifacts": {"notification_sent": notification_sent}}


# --- Runtime predicate: the load-bearing (notification_sent AND status==FAIL) gate -----

def test_token_emitted_only_when_delivered_and_fail(capsys):
    _emit_fail_owned_signal(_contract(True), {"status": SUMMARY_STATUS_FAIL})
    assert FAIL_OWNED_SIGNAL in capsys.readouterr().out


def test_token_not_emitted_when_status_success(capsys):
    # Pre-verification SUCCESS: a delivered notification on a SUCCESS attempt (which
    # execute_run may later flip to FAIL via verification) must emit NO token, so the
    # terminal notifier stays free to fire on a verification failure. Drops-the-FAIL-gate mutation dies here.
    _emit_fail_owned_signal(_contract(True), {"status": SUMMARY_STATUS_SUCCESS})
    assert FAIL_OWNED_SIGNAL not in capsys.readouterr().out


def test_token_not_emitted_when_not_delivered(capsys):
    # Suppressed-repeat HALT and transport failure both leave notification_sent False/None.
    _emit_fail_owned_signal(_contract(False), {"status": SUMMARY_STATUS_FAIL})
    _emit_fail_owned_signal(_contract(None), {"status": SUMMARY_STATUS_FAIL})
    assert FAIL_OWNED_SIGNAL not in capsys.readouterr().out


def test_emit_uses_pre_verification_status_before_override():
    # Placement guard for the crux: execute_run must emit the signal from the
    # PRE-verification summary - the _emit_fail_owned_signal call must precede the
    # post-verification `pipeline.summary["status"] = ...` override. If moved after the
    # override, a SUCCESS attempt flipped to FAIL by verification would wrongly emit the
    # token and suppress its only failure alert.
    src = inspect.getsource(runtime.execute_run)
    assert "_emit_fail_owned_signal(" in src
    assert src.index("_emit_fail_owned_signal(") < src.index('pipeline.summary["status"] ='), (
        "the FAIL-owned signal must be emitted before the post-verification status override"
    )


def test_execute_run_success_pipeline_failing_verification_emits_no_token(monkeypatch, capsys):
    """Crux behavioral proof (PRD-296 VALIDATION / Stage-0 REQUIRED CHANGE #2): a delivered
    notification on a :1413-SUCCESS attempt whose post-pipeline verification FAILS must emit NO
    token, even though execute_run flips the final status to FAIL and cli would exit 1. The
    terminal notifier must stay free to fire (PRD-295 no-regression). Moving the emission after
    the :300-304 override makes this test fail (the token would be printed on the final FAIL)."""
    fake = SimpleNamespace(
        report_path="/does/not/matter.md",
        report="r",
        date_str="2026-04-12",
        run_at_utc=runtime.datetime(2026, 4, 12, 13, 0, tzinfo=runtime.timezone.utc),
        summary={"status": SUMMARY_STATUS_SUCCESS, "warnings": [], "errors": []},
        contract={"artifacts": {"notification_sent": True}},
        spy_observation=None,
        market_control_card=None,
        market_map={},
    )
    monkeypatch.setattr(runtime, "_run_pipeline", lambda **kw: fake)
    monkeypatch.setattr(runtime, "_write_summary_files", lambda *a, **k: (Path("s.json"), Path("l.json")))
    monkeypatch.setattr(runtime, "verify_run_summary", lambda *a, **k: {"pass": False, "warnings": [], "errors": ["verify failed"]})
    monkeypatch.setattr(runtime, "_write_markdown_report", lambda *a, **k: None)
    monkeypatch.setattr(runtime, "_rewrite_summary_file", lambda *a, **k: None)
    monkeypatch.setattr(runtime, "_write_contract_file", lambda *a, **k: None)
    monkeypatch.setattr(runtime, "_write_payload_artifacts", lambda *a, **k: None)
    monkeypatch.setattr(runtime, "_load_previous_market_map", lambda *a, **k: {})
    monkeypatch.setattr(runtime, "inject_lifecycle", lambda *a, **k: {})
    monkeypatch.setattr(runtime, "_write_market_map_file", lambda *a, **k: None)
    monkeypatch.setattr(runtime, "_write_macro_snapshot", lambda *a, **k: None)

    summary = runtime.execute_run(mode=runtime.MODE_LIVE, run_date=date.fromisoformat("2026-04-12"))

    assert summary["status"] == SUMMARY_STATUS_FAIL          # override flipped SUCCESS -> FAIL (cli would exit 1)
    assert FAIL_OWNED_SIGNAL not in capsys.readouterr().out  # but NO token: terminal stays free to fire


# --- Workflow wiring -------------------------------------------------------------------

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
