"""
Premarket runner — Layers 1–9 full pipeline.

Scheduled entry point: 13:00 UTC Monday–Friday (06:00 PT).
  python -m cuttingboard.run_premarket

Calls run_pipeline() then writes .cb_commit_msg in the repo root so the
GitHub Actions commit step can use it directly with `git commit -F`.

Commit message format:
  CB report: YYYY-MM-DD | {REGIME} | {n} trades [{TICKER, ...}]

Examples:
  CB report: 2026-04-11 | TRANSITION | 0 trades []
  CB report: 2026-04-14 | RISK_ON | 3 trades [SPY, QQQ, NVDA]
"""

import json
import logging
import sys

from cuttingboard.output import run_pipeline

logger = logging.getLogger(__name__)

_COMMIT_MSG_PATH = ".cb_commit_msg"
_AUDIT_LOG_PATH  = "logs/audit.jsonl"


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    exit_code = run_pipeline()
    _write_commit_msg()
    sys.exit(exit_code)


def _write_commit_msg() -> None:
    """Build commit message from last audit record and write to .cb_commit_msg."""
    try:
        with open(_AUDIT_LOG_PATH, "r", encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh if ln.strip()]

        if not lines:
            logger.warning("audit.jsonl is empty — using fallback commit message")
            _write_fallback()
            return

        record = json.loads(lines[-1])

        date    = record.get("date", "unknown")
        regime  = record.get("regime") or "UNKNOWN"
        trades  = record.get("qualified_trades") or []
        n       = len(trades)
        tickers = ", ".join(t["symbol"] for t in trades if "symbol" in t)
        msg = f"CB report: {date} | {regime} | {n} trades [{tickers}]"

        with open(_COMMIT_MSG_PATH, "w", encoding="utf-8") as fh:
            fh.write(msg + "\n")

        logger.info(f"Commit message written: {msg}")

    except FileNotFoundError:
        logger.warning(f"{_AUDIT_LOG_PATH} not found — using fallback commit message")
        _write_fallback()
    except Exception as exc:
        logger.warning(f"Could not write {_COMMIT_MSG_PATH}: {exc}")
        _write_fallback()


def _write_fallback() -> None:
    from datetime import date as _date
    today = _date.today().isoformat()
    with open(_COMMIT_MSG_PATH, "w", encoding="utf-8") as fh:
        fh.write(f"CB run: {today}\n")


if __name__ == "__main__":
    main()
