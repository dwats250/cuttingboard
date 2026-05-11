"""
Shared pytest fixtures for the cuttingboard test suite.
"""

import pytest


@pytest.fixture(autouse=True)
def _reset_telegram_rate_limiter(monkeypatch):
    """Reset the Telegram send-rate state and suppress sleeps between tests.

    Without this, the 1.1s rate-limit enforcement in send_telegram causes
    successive tests to sleep, adding > 1s latency per test in a session.
    Tests that specifically verify sleep behavior override time.sleep via
    their own monkeypatch call (the last setattr wins).
    """
    import cuttingboard.output as _out
    monkeypatch.setattr(_out, "_LAST_SEND_TS", 0.0)
    monkeypatch.setattr("cuttingboard.output.time.sleep", lambda _: None)


@pytest.fixture(autouse=True)
def _isolate_real_log_paths(monkeypatch, tmp_path):
    """Redirect default-path writes that would otherwise mutate the tracked
    files `logs/audit.jsonl` and `logs/latest_payload.json`.

    Two redirects, two mechanisms:

    1. `cuttingboard.audit.AUDIT_LOG_PATH` is read at call time, so a
       plain `monkeypatch.setattr` on the module constant suffices.
    2. `cuttingboard.delivery.transport.deliver_json` /
       `deliver_html` use `_DEFAULT_JSON_PATH` / `_DEFAULT_HTML_PATH` as
       default argument values — those defaults are frozen at function
       definition time, so a module-constant patch is INSUFFICIENT.
       Instead we wrap the functions to substitute the tmp path when
       the caller passes no `output_path`.

    The redirect target is `tmp_path / "logs"` so that chdir-isolating
    tests reading a relative `logs/audit.jsonl` still resolve to the
    same file. The directory is created lazily by the writers (both
    `cuttingboard.audit.append_audit` and `cuttingboard.delivery.
    transport._write_file` call `mkdir(exist_ok=True)`), so this
    fixture does NOT pre-create the directory — pre-creating would
    collide with tests that build their own `tmp_path / "logs"`
    without `exist_ok=True`.

    Tests that monkeypatch these constants or functions themselves
    remain unaffected — pytest's last-setattr-wins semantics let
    specific tests override the autouse redirect.

    Without this fixture, ~134 notifier tests and several pipeline
    tests mutate the real tracked files on every pytest run, leaving
    them perpetually dirty in `git status` (the files are force-added
    by the hourly CI workflow, so they cannot simply be gitignored).
    """
    import cuttingboard.audit as _audit
    import cuttingboard.delivery.transport as _transport
    # Target paths under `tmp_path/logs/` so tests that chdir into
    # tmp_path and read a relative "logs/audit.jsonl" still resolve to
    # the same file. Parent dirs are created lazily by the audit writer
    # (os.makedirs exist_ok=True) and the transport writer
    # (path.parent.mkdir parents=True exist_ok=True), so we do NOT
    # pre-create — that would collide with tests that mkdir
    # `tmp_path/logs/` themselves without exist_ok=True.
    logs_dir = tmp_path / "logs"
    monkeypatch.setattr(_audit, "AUDIT_LOG_PATH", str(logs_dir / "audit.jsonl"))

    _orig_deliver_json = _transport.deliver_json
    _orig_deliver_html = _transport.deliver_html
    _safe_json_path = str(logs_dir / "latest_payload.json")
    _safe_html_path = str(tmp_path / "reports" / "output" / "report.html")

    def _safe_deliver_json(payload, output_path=None):
        if output_path is None:
            output_path = _safe_json_path
        return _orig_deliver_json(payload, output_path=output_path)

    def _safe_deliver_html(payload, output_path=None):
        if output_path is None:
            output_path = _safe_html_path
        return _orig_deliver_html(payload, output_path=output_path)

    monkeypatch.setattr(_transport, "deliver_json", _safe_deliver_json)
    monkeypatch.setattr(_transport, "deliver_html", _safe_deliver_html)
