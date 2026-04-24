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
