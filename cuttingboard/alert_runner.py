"""Canonical hourly alert entrypoint with a runner-level notification backstop."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from cuttingboard.output import send_notification

logger = logging.getLogger(__name__)


def _ascii_safe(text: str) -> str:
    return text.encode("ascii", errors="replace").decode("ascii")


def _backstop_body(exc: BaseException, now_utc: datetime) -> str:
    return _ascii_safe(
        "\n".join(
            [
                f"error_type: {type(exc).__name__}",
                f"error_message: {str(exc)[:200]}",
                f"timestamp: {now_utc.isoformat()}",
            ]
        )
    )


def main() -> int:
    """Run the hourly alert path and convert all runtime failures to exit 0."""
    try:
        from cuttingboard.notifications import NOTIFY_HOURLY
        from cuttingboard.runtime import MODE_LIVE, _execute_notify_run

        run_date = datetime.now(timezone.utc).date()
        _execute_notify_run(mode=MODE_LIVE, run_date=run_date, notify_mode=NOTIFY_HOURLY)
    except Exception as exc:
        now_utc = datetime.now(timezone.utc)
        logger.exception("alert runner backstop caught exception")
        body = _backstop_body(exc, now_utc)
        try:
            send_notification(
                "HALT - SYSTEM ERROR",
                body,
                notification_audit_reason="runner_level_exception",
            )
        except Exception as notify_exc:
            logger.exception("alert runner backstop notification failed: %s", notify_exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
