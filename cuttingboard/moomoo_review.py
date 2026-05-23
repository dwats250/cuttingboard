"""``python -m cuttingboard.moomoo_review`` — Moomoo statement consumer CLI.

Read-only and descriptive-only. Joins Moomoo client-statement trades to
``logs/audit.jsonl`` and emits two output channels:

* ``logs/moomoo_review.jsonl`` — append-only, one record per trade.
* ``reports/moomoo/<YYYY-MM>.md`` — rendered per-statement view, overwritten.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from cuttingboard.audit import AUDIT_LOG_PATH
from cuttingboard.moomoo_join import EnrichedTrade, enrich
from cuttingboard.moomoo_parser import (
    NormalizedTrade,
    extract_period_from_pdf,
    parse_statement,
)


__all__ = ["main", "process_statement"]


JSONL_OUTPUT_PATH = "logs/moomoo_review.jsonl"
REPORT_DIR = "reports/moomoo"


def _collect_pdfs(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(p for p in target.iterdir() if p.suffix.lower() == ".pdf")
    return []


def _trade_to_jsonl_record(
    enriched: EnrichedTrade,
    *,
    statement_path: Path,
    processed_at_utc: str,
) -> dict:
    return {
        "trade": enriched.trade.to_dict(),
        "in_universe": enriched.in_universe,
        "blind_spots": list(enriched.blind_spots),
        "audit_records": list(enriched.audit_records),
        "statement_path": str(statement_path),
        "processed_at_utc": processed_at_utc,
    }


def _append_jsonl(path: Path, records: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")


def _format_trade_line(t: NormalizedTrade) -> str:
    bits = [t.side, t.instrument_class]
    if t.underlier:
        bits.append(t.underlier)
    if t.option:
        bits.append(f"{t.option.right} {t.option.strike} {t.option.expiry.isoformat()} x{t.option.contracts}")
    bits.append(f"qty={t.quantity:g}")
    if t.price is not None:
        bits.append(f"price={t.price:g}")
    bits.append(f"amount={t.amount:.2f}")
    if t.next_period:
        bits.append("[next_period]")
    return " ".join(bits)


def _render_markdown(
    period_ending: date,
    enriched_trades: list[EnrichedTrade],
    statement_path: Path,
) -> str:
    lines: list[str] = []
    lines.append(f"# Moomoo Statement Review — {period_ending.isoformat()}")
    lines.append("")
    lines.append(f"Source: `{statement_path}`")
    lines.append("")
    lines.append(f"Trades parsed: **{len(enriched_trades)}**")
    lines.append("")

    by_date: dict[str, list[EnrichedTrade]] = {}
    for et in enriched_trades:
        by_date.setdefault(et.trade.date.isoformat(), []).append(et)

    for d in sorted(by_date):
        lines.append(f"## {d}")
        lines.append("")
        for et in by_date[d]:
            lines.append(f"- {_format_trade_line(et.trade)}")
            lines.append(f"    - account: `{et.trade.account}`")
            lines.append(f"    - in_universe: `{et.in_universe}`")
            if et.blind_spots:
                lines.append(f"    - blind_spots: {', '.join(f'`{b}`' for b in et.blind_spots)}")
            lines.append(f"    - audit_records: {len(et.audit_records)}")
        lines.append("")

    return "\n".join(lines)


def _write_markdown(period_ending: date, body: str) -> Path:
    out_dir = Path(REPORT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{period_ending.strftime('%Y-%m')}.md"
    out_path.write_text(body, encoding="utf-8")
    return out_path


def process_statement(
    pdf_path: Path,
    *,
    audit_log_path: str = AUDIT_LOG_PATH,
    jsonl_path: Path = Path(JSONL_OUTPUT_PATH),
    processed_at_utc: Optional[str] = None,
) -> tuple[int, Optional[Path]]:
    """Process one PDF. Returns (trade_count, markdown_path_or_None)."""
    trades = parse_statement(pdf_path)
    period = extract_period_from_pdf(pdf_path)
    if period is None:
        raise ValueError(f"could not extract Period Ending from {pdf_path}")

    enriched_trades = enrich(trades, audit_log_path=audit_log_path)

    processed_at_utc = processed_at_utc or datetime.now(timezone.utc).isoformat()
    records = [
        _trade_to_jsonl_record(et, statement_path=pdf_path, processed_at_utc=processed_at_utc)
        for et in enriched_trades
    ]
    _append_jsonl(jsonl_path, records)

    body = _render_markdown(period, enriched_trades, pdf_path)
    md_path = _write_markdown(period, body)
    return len(enriched_trades), md_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cuttingboard.moomoo_review",
        description="Join Moomoo client-statement PDFs to logs/audit.jsonl (read-only).",
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to a single .pdf file, or a directory of .pdf files (non-recursive).",
    )
    parser.add_argument(
        "--audit-log",
        default=AUDIT_LOG_PATH,
        help=f"Path to audit JSONL (default: {AUDIT_LOG_PATH}).",
    )
    parser.add_argument(
        "--jsonl-output",
        type=Path,
        default=Path(JSONL_OUTPUT_PATH),
        help=f"Path to append per-trade JSONL output (default: {JSONL_OUTPUT_PATH}).",
    )
    args = parser.parse_args(argv)

    pdfs = _collect_pdfs(args.path)
    if not pdfs:
        print(f"moomoo_review: no .pdf files found at {args.path}", file=sys.stderr)
        return 1

    processed_ok = 0
    for pdf in pdfs:
        try:
            count, md_path = process_statement(
                pdf,
                audit_log_path=args.audit_log,
                jsonl_path=args.jsonl_output,
            )
        except Exception as exc:  # parse-level failures must not abort the batch
            print(f"moomoo_review: failed to process {pdf}: {exc}", file=sys.stderr)
            continue
        processed_ok += 1
        print(f"moomoo_review: {pdf} -> {count} trades, report {md_path}")

    if processed_ok == 0:
        print("moomoo_review: every PDF failed to parse", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
