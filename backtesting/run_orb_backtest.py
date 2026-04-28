"""Command-line runner for the deterministic ORB reference backtest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from algos.orb_reference import run_backtest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic SSRN ORB reference backtest on CSV data."
    )
    parser.add_argument("--spy", type=Path, help="Path to SPY 1-minute OHLCV CSV")
    parser.add_argument("--qqq", type=Path, help="Path to QQQ 1-minute OHLCV CSV")
    parser.add_argument("--out", type=Path, help="Optional output JSON path")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON instead of compact JSON",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a compact performance summary after the trade JSON",
    )
    args = parser.parse_args()

    data = {}
    if args.spy:
        data["SPY"] = pd.read_csv(args.spy)
    if args.qqq:
        data["QQQ"] = pd.read_csv(args.qqq)

    if not data:
        parser.error("provide at least one of --spy or --qqq")

    trades = run_backtest(data)
    summary = _summarize(data, trades)
    payload = json.dumps(
        trades,
        indent=2 if args.pretty else None,
        sort_keys=True,
        separators=None if args.pretty else (",", ":"),
    )

    if args.out:
        args.out.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    if args.summary:
        print(json.dumps(summary, indent=2, sort_keys=True))

    return 0


def _summarize(data: dict[str, pd.DataFrame], trades: list[dict]) -> dict:
    symbol_days = 0
    rows = 0
    date_ranges = {}

    for symbol, frame in data.items():
        normalized_timestamps = pd.to_datetime(frame["timestamp"], errors="raise")
        dates = sorted(pd.Series(normalized_timestamps).dt.date.unique())
        rows += len(frame)
        symbol_days += len(dates)
        date_ranges[symbol] = {
            "first_date": dates[0].isoformat() if dates else None,
            "last_date": dates[-1].isoformat() if dates else None,
            "trading_days": len(dates),
            "rows": len(frame),
        }

    r_values = [float(trade["R_multiple"]) for trade in trades]
    wins = [r for r in r_values if r > 0]
    losses = [r for r in r_values if r < 0]

    return {
        "rows": rows,
        "symbol_days": symbol_days,
        "trades": len(trades),
        "trade_rate_per_symbol_day": (len(trades) / symbol_days) if symbol_days else 0.0,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": (len(wins) / len(trades)) if trades else 0.0,
        "total_R": sum(r_values),
        "average_R": (sum(r_values) / len(r_values)) if r_values else 0.0,
        "by_symbol": date_ranges,
    }


if __name__ == "__main__":
    raise SystemExit(main())
