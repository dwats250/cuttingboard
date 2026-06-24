"""Canonical hourly alert entrypoint with slot-based idempotency (PRD-141)."""

from __future__ import annotations

import argparse
import logging
import os
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


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="cuttingboard.alert_runner")
    parser.add_argument(
        "--force-slot",
        action="store_true",
        help="Bypass cross-run slot idempotency (workflow_dispatch / operator override).",
    )
    return parser.parse_args(argv if argv is not None else [])


def main(argv: list[str] | None = None) -> int:
    """Run the hourly alert path and convert all runtime failures to exit 0."""
    args = _parse_args(argv)
    force_slot = args.force_slot or os.environ.get("CUTTINGBOARD_FORCE_SLOT") == "1"

    try:
        from cuttingboard.notifications import NOTIFY_HOURLY
        from cuttingboard.notifications.hourly_slot import (
            _PT_TZ,
            canonical_slot_utc,
            load_last_slot,
            routine_pt_slot,
        )
        from cuttingboard.output import write_notification_audit
        from cuttingboard.runtime import MODE_LIVE, _execute_notify_run

        now_utc = datetime.now(timezone.utc)

        if force_slot:
            slot_utc = canonical_slot_utc(now_utc)
        else:
            slot_utc = routine_pt_slot(now_utc)
            if slot_utc is None:
                now_pt = now_utc.astimezone(_PT_TZ)
                state_key = f"outside:{now_pt.strftime('%Y-%m-%dT%H:%M%z')}"
                write_notification_audit(
                    transport="telegram",
                    status="suppressed",
                    alert_title="hourly",
                    attempted=False,
                    success=False,
                    reason="outside_routine_window",
                    state_key=state_key,
                    notify_mode=NOTIFY_HOURLY,
                )
                logger.info(
                    "hourly alert suppressed: outside routine window now_pt=%s",
                    now_pt.isoformat(),
                )
                return 0
            last = load_last_slot()
            if last is not None and last.get("slot_utc") == slot_utc.isoformat():
                write_notification_audit(
                    transport="telegram",
                    status="suppressed",
                    alert_title="hourly",
                    attempted=False,
                    success=False,
                    reason="suppressed_same_slot",
                    state_key=slot_utc.isoformat(),
                    notify_mode=NOTIFY_HOURLY,
                )
                logger.info("hourly alert suppressed: same slot %s", slot_utc.isoformat())
                return 0

        _execute_notify_run(
            mode=MODE_LIVE,
            run_date=now_utc.date(),
            notify_mode=NOTIFY_HOURLY,
            slot_utc=slot_utc,
        )
    except Exception as exc:
        now_utc = datetime.now(timezone.utc)
        logger.exception("alert runner backstop caught exception")
        body = _backstop_body(exc, now_utc)
        try:
            # PRD-192: retained UNTAGGED by design (notify_mode defaults None).
            # This is the catastrophic runner-level backstop, distinct from a
            # normal hourly notify run; its audit reason "runner_level_exception"
            # already identifies it. NOTIFY_HOURLY is a lazy import inside the
            # try above, so it can be unbound here if the failure was that import
            # itself -- referencing it in the last-resort error path would risk a
            # NameError. The audit record stays self-describing via the reason.
            send_notification(
                "HALT - SYSTEM ERROR",
                body,
                notification_audit_reason="runner_level_exception",
            )
        except Exception as notify_exc:
            logger.exception("alert runner backstop notification failed: %s", notify_exc)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
