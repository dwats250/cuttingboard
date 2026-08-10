"""PRD-295 - morning executor fail-loud failure notification (additive).

Proves the reused notification handler (format_failure_notification -> send_telegram)
emits only CURRENT workflow truth and never leaks a stale logs/latest_run.json, and
locks the .github/workflows/cuttingboard.yml wiring (Telegram env, terminal
if: failure() step, $GITHUB_ENV stage carrier, option-A import guard). No new
notification code is added; the failure step reuses the existing formatter/transport.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "cuttingboard.yml"

# Fields a stale prior observation would carry; none may appear in a failure alert.
STALE = ("2020-01-01", "BULLISH_TREND", "TOP_TRADE_VALIDATED")


def _workflow():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _notify_step(wf):
    steps = wf["jobs"]["pipeline"]["steps"]
    for step in steps:
        if step.get("name") == "Notify on failure":
            return step, steps
    raise AssertionError("Notify on failure step not found")


def _inline_python(run: str) -> str:
    match = re.search(r"<<'PY'\n(.*?)\n\s*PY", run, re.DOTALL)
    assert match, "PY heredoc not found in Notify-on-failure step"
    return match.group(1)


def _write_stale_latest_run(tmp_path: Path) -> None:
    (tmp_path / "logs").mkdir(exist_ok=True)
    (tmp_path / "logs" / "latest_run.json").write_text(json.dumps({
        "run_at_utc": "2020-01-01T00:00:00Z",
        "timestamp": "2020-01-01T00:00:00Z",
        "regime": "BULLISH_TREND",
        "status": "SUCCESS",
        "chain_validation": {"SPY": {"classification": "TOP_TRADE_VALIDATED"}},
    }))


# --- Behavioral: the SHIPPED inline handler emits only current truth (R2, R4, I1, I2) ---

def test_shipped_inline_handler_sends_only_current_truth(tmp_path, monkeypatch):
    from cuttingboard import output

    _write_stale_latest_run(tmp_path)
    monkeypatch.chdir(tmp_path)  # a stale latest_run.json is present in cwd
    monkeypatch.setenv("CB_JOB_MODE", "live")
    monkeypatch.setenv("CB_STAGE", "tests")
    monkeypatch.setenv("CB_RUN_URL", "http://example/run/1")

    sent: dict[str, str] = {}
    monkeypatch.setattr(
        output, "send_telegram",
        lambda title, body="", **kw: sent.update(title=title, body=body) or True,
    )

    code = _inline_python(_notify_step(_workflow())[0]["run"])
    exec(compile(code, "notify_inline.py", "exec"), {"__name__": "__notify__"})

    assert sent, "shipped inline handler did not invoke send_telegram"
    # Current workflow truth is present:
    assert "stage: tests" in sent["body"]
    assert "mode live" in sent["body"]
    assert str(datetime.now(timezone.utc).year) in sent["body"]  # formatter stamps current time
    # No stale observation field leaks into title or body:
    for field in (*STALE, "SUCCESS"):
        assert field not in sent["body"], f"stale field leaked into body: {field}"
        assert field not in sent["title"], f"stale field leaked into title: {field}"


def test_formatter_discards_supplied_date(tmp_path):
    from cuttingboard.notifications import format_failure_notification

    # date_str is discarded by the formatter; a stale date passed in must not surface.
    _, body = format_failure_notification("live", "2020-01-01", "morning pipeline failed at stage: tests")
    assert "2020-01-01" not in body
    assert str(datetime.now(timezone.utc).year) in body


# --- Structural / executable wiring (R1, R3, R6; VALIDATION) ---

def test_telegram_env_exposed_on_job():
    env = _workflow()["jobs"]["pipeline"]["env"]
    assert "TELEGRAM_BOT_TOKEN" in env
    assert "TELEGRAM_CHAT_ID" in env


def test_notify_step_is_terminal_and_failure_only():
    step, steps = _notify_step(_workflow())
    assert step["if"] == "failure()"                    # success never triggers the alert (R6)
    assert steps[-1]["name"] == "Notify on failure"     # terminal: catches any prior step's failure
    run = step["run"]
    assert "format_failure_notification" in run and "send_telegram" in run  # reuse (R4)
    assert "latest_run.json" not in run                 # never reads observation state (R2/I1)
    assert "except Exception" in run and "SystemExit(0)" in run  # option-A pre-install no-op (R4)


def test_stage_carrier_present_and_bounded_to_post_install():
    text = WORKFLOW.read_text(encoding="utf-8")
    for stage in ("lint", "tests", "engine_doctor", "execute", "verify", "render_commit", "push"):
        assert f'echo "CB_STAGE={stage}" >> "$GITHUB_ENV"' in text, f"missing CB_STAGE carrier: {stage}"
    # Pre-install / non-helper-available stages are not reportable (option-A boundary).
    assert "CB_STAGE=install" not in text
    assert "CB_STAGE=mode_resolution" not in text


def test_notify_inline_python_compiles():
    compile(_inline_python(_notify_step(_workflow())[0]["run"]), "notify_inline.py", "exec")
