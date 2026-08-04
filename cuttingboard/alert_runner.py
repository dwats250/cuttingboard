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
    """Run the hourly alert path; the exit code reports the run's health (PRD-287).

    Exit 0 only on a healthy completion (``_execute_notify_run`` returned
    ``SUMMARY_STATUS_SUCCESS`` — TRADE, NO_TRADE, or market-stress safety HALT) or
    a suppressed slot; an in-run system failure and a runner-level exception both
    exit 1 (the latter after the unchanged notification/diagnostic backstop).
    """
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
        from cuttingboard.runtime import (
            MODE_LIVE,
            SUMMARY_STATUS_SUCCESS,
            _execute_notify_run,
        )

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

        result = _execute_notify_run(
            mode=MODE_LIVE,
            run_date=now_utc.date(),
            notify_mode=NOTIFY_HOURLY,
            slot_utc=slot_utc,
        )
        # PRD-287: exit 0 only on a healthy completion; a non-SUCCESS return
        # (in-run system failure) exits non-zero so the job fails and does not
        # publish. A market-stress safety HALT returns SUCCESS and stays 0.
        return 0 if result.get("status") == SUMMARY_STATUS_SUCCESS else 1
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
        # PRD-287: runner-level exception is a system failure -- exit non-zero
        # AFTER the notification/diagnostic attempt above (unchanged).
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
