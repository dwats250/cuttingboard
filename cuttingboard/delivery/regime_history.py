"""PRD-175 — Historical regime scoreboard aggregation sidecar.

Read-only. Folds the per-run pipeline records in ``logs/audit.jsonl`` into one
summary record per calendar date and writes the full, idempotent history to
``logs/regime_history.jsonl``. Each date's record carries the SPY next-session
percent change once the following trading day's close is available (so a call
made on day D gains its reference move on D+1's aggregation run).

Description, not prediction: it records what the regime engine said and what SPY
did next. It computes no hit-rate, accuracy, or grade.

Isolation (PRD-175 R5): reads only ``logs/audit.jsonl`` and the SPY OHLCV cache;
writes only ``logs/regime_history.jsonl``. It does not import or mutate runtime
decision state, the contract, or payloads.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from cuttingboard import config

AUDIT_LOG_PATH = "logs/audit.jsonl"
REGIME_HISTORY_PATH = "logs/regime_history.jsonl"

# Representative summary fields, drawn only from fields cuttingboard.audit
# actually writes to a pipeline record (PRD-175 R1).
_REGIME_FIELDS = ("regime", "posture", "confidence", "net_score", "vix_level")


def _load_pipeline_records(audit_path: str) -> list[dict]:
    """Return pipeline-shaped audit records: those with ``outcome`` + ``run_at_utc``
    + ``date`` and NO ``event`` key. Notification records (event=='notification')
    are excluded (PRD-175 R2)."""
    path = Path(audit_path)
    if not path.exists():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "event" in rec:
            continue
        if "outcome" in rec and "run_at_utc" in rec and "date" in rec:
            records.append(rec)
    return records


def _summarize_day(day_records: list[dict]) -> dict:
    """One summary per date. The representative call is the latest run of the
    day (max run_at_utc) -- the end-of-day state the scoreboard reports."""
    ordered = sorted(day_records, key=lambda r: r["run_at_utc"])
    last = ordered[-1]
    summary: dict = {"date": last["date"]}
    for field in _REGIME_FIELDS:
        summary[field] = last.get(field)
    summary["first_run_at_utc"] = ordered[0]["run_at_utc"]
    summary["last_run_at_utc"] = last["run_at_utc"]
    summary["run_count"] = len(ordered)
    return summary


def _load_spy_close_series(cache_path: Optional[str] = None) -> list[tuple[str, float]]:
    """SPY daily closes as a date-sorted list of (YYYY-MM-DD, close). Empty when
    the cache is missing or unreadable -- the change attaches on a later run."""
    import pandas as pd

    path = Path(cache_path) if cache_path else Path(config.OHLCV_CACHE_DIR) / "SPY_ohlcv.parquet"
    if not path.exists():
        return []
    try:
        df = pd.read_parquet(path)
    except Exception:
        return []
    if "Close" not in df.columns or df.empty:
        return []
    closes = [
        (pd.Timestamp(ts).strftime("%Y-%m-%d"), float(value))
        for ts, value in df["Close"].items()
    ]
    closes.sort(key=lambda kv: kv[0])
    return closes


def _next_session_change(spy_closes: list[tuple[str, float]], date_str: str) -> Optional[float]:
    """SPY percent change on the trading session AFTER ``date_str``: a call made
    on D is scored by D+1's close vs D's close. None when either close is absent."""
    dates = [d for d, _ in spy_closes]
    if date_str not in dates:
        return None
    idx = dates.index(date_str)
    if idx + 1 >= len(spy_closes):
        return None
    current = spy_closes[idx][1]
    following = spy_closes[idx + 1][1]
    if current == 0:
        return None
    return round(following / current - 1.0, 6)


def _write_history(history_path: str, summaries: list[dict]) -> None:
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        "".join(json.dumps(s, sort_keys=True) + "\n" for s in summaries),
        encoding="utf-8",
    )
    tmp.replace(path)


def aggregate(
    *,
    audit_path: str = AUDIT_LOG_PATH,
    history_path: str = REGIME_HISTORY_PATH,
    spy_closes: Optional[list[tuple[str, float]]] = None,
) -> list[dict]:
    """Rebuild logs/regime_history.jsonl from logs/audit.jsonl.

    Full rebuild is idempotent by construction: one record per date, sorted, with
    spy_close_change_pct recomputed each run (so a prior day gains its reference
    move once the next session's close exists). Always writes the file, even with
    zero pipeline records, so the workflow can stage it unconditionally.
    """
    if spy_closes is None:
        spy_closes = _load_spy_close_series()

    by_date: dict[str, list[dict]] = {}
    for rec in _load_pipeline_records(audit_path):
        by_date.setdefault(rec["date"], []).append(rec)

    summaries: list[dict] = []
    for date_str in sorted(by_date):
        summary = _summarize_day(by_date[date_str])
        summary["spy_close_change_pct"] = _next_session_change(spy_closes, date_str)
        summaries.append(summary)

    _write_history(history_path, summaries)
    return summaries


def main() -> int:
    summaries = aggregate()
    print(f"regime_history: {len(summaries)} dated record(s) -> {REGIME_HISTORY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
