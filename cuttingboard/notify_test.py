"""
Smoke test: send a timestamped test message via Telegram and write notification audit.

Usage:
    python3 -m cuttingboard.notify_test

Loads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from .env / environment.
Prints SUCCESS or FAILURE and exits with code 0 (success) or 1 (failure).
The notification audit entry is written to logs/audit.jsonl regardless of outcome.
"""

import sys
from datetime import datetime, timezone

from cuttingboard import config  # noqa: F401 — loads .env on import
from cuttingboard.output import send_telegram


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    title = "notify_test"
    body = f"Smoke test OK — {ts}"

    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID
    token_display = f"...{token[-6:]}" if token and len(token) > 6 else "(not set)"
    chat_display = chat_id or "(not set)"

    print(f"token : {token_display}")
    print(f"chat  : {chat_display}")
    print(f"title : {title!r}")
    print(f"body  : {body!r}")
    print()

    ok = send_telegram(title, body)
    if ok:
        print("SUCCESS — check Telegram and logs/audit.jsonl")
    else:
        print("FAILURE — check logs/audit.jsonl for error detail")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
