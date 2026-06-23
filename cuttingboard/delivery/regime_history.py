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
import logging
from pathlib import Path
from typing import Optional

from cuttingboard import config

logger = logging.getLogger(__name__)

AUDIT_LOG_PATH = "logs/audit.jsonl"
REGIME_HISTORY_PATH = "logs/regime_history.jsonl"

# PRD-204: a preserved (carried-forward) spy_close_change_pct carries this
# observable marker so a value that the current rebuild could not recompute
# cannot masquerade as freshly-computed. Always present on every record:
# True only when the value was preserved from the prior history because the
# SPY series could not resolve it this run; False when freshly computed or
# genuinely absent (never yet computed). Downstream staleness styling (the
# Lead-5 follow-up) reads this key; the renderer ignores it until then.
STALE_MARKER_KEY = "spy_close_change_pct_stale"

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


def _load_prior_history(history_path: str) -> dict[str, dict]:
    """Prior ``logs/regime_history.jsonl`` records keyed by date. Empty when the
    file is missing or unreadable. Used to preserve an already-computed
    spy_close_change_pct that the current rebuild cannot recompute (PRD-204)."""
    path = Path(history_path)
    if not path.exists():
        return {}
    prior: dict[str, dict] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            date = rec.get("date")
            if isinstance(date, str):
                prior[date] = rec
    except OSError:
        return {}
    return prior


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

    Idempotent and GAIN-ONLY by construction: one record per date, sorted. A
    date's spy_close_change_pct is recomputed each run so a prior day GAINS its
    reference move once the next session's close exists — and a value that the
    current run cannot recompute (the SPY series is absent/empty, or that date's
    next-session close is missing) is NEVER overwritten with null. Instead the
    already-computed value is PRESERVED from the prior history and flagged with
    ``spy_close_change_pct_stale = True`` (PRD-204). This is mode-agnostic: it
    holds for every caller and every absent-source path, not a calendar special
    case. The empty/partial-series case is logged loudly (R3), never a silent
    substitute. Always writes the file, even with zero pipeline records, so the
    workflow can stage it unconditionally.
    """
    if spy_closes is None:
        spy_closes = _load_spy_close_series()
    prior = _load_prior_history(history_path)

    by_date: dict[str, list[dict]] = {}
    for rec in _load_pipeline_records(audit_path):
        by_date.setdefault(rec["date"], []).append(rec)

    summaries: list[dict] = []
    preserved_dates: list[str] = []
    for date_str in sorted(by_date):
        summary = _summarize_day(by_date[date_str])
        computed = _next_session_change(spy_closes, date_str)
        if computed is not None:
            # Authoritative when computable: fresh value, not stale.
            summary["spy_close_change_pct"] = computed
            summary[STALE_MARKER_KEY] = False
        else:
            prior_value = prior.get(date_str, {}).get("spy_close_change_pct")
            if prior_value is not None:
                # PRD-204: do NOT wipe an already-computed return with null
                # because the source could not resolve it this run. Preserve
                # last-known-good and mark it stale.
                summary["spy_close_change_pct"] = prior_value
                summary[STALE_MARKER_KEY] = True
                preserved_dates.append(date_str)
            else:
                # Genuinely not yet computed (e.g. the next close does not exist
                # yet) — null is correct here, and it is not "stale".
                summary["spy_close_change_pct"] = None
                summary[STALE_MARKER_KEY] = False
        summaries.append(summary)

    null_count = sum(1 for s in summaries if s["spy_close_change_pct"] is None)

    if not spy_closes and summaries:
        # R3 (Codex P2): the SPY source itself did not resolve this run
        # (absent/empty/unreadable parquet), so NO date could compute a fresh
        # return. Log loudly whether or not anything was preservable — a bootstrap
        # publish branch, newly-added dates, or an all-null prior writes null(s)
        # here, and a degraded source must never be silent. This is the condition
        # R3 guards; gating the warning on preserved_dates left it unfulfilled.
        logger.warning(
            "regime_history: SPY close series is empty/absent this run — no "
            "next-session return could be computed for any of %d date(s). Preserved "
            "%d last-known-good value(s) (marked %s=True); wrote %d null(s) where no "
            "prior existed. A missing/unreadable SPY parquet is the usual cause (R3).",
            len(summaries),
            len(preserved_dates),
            STALE_MARKER_KEY,
            null_count,
        )
    elif preserved_dates:
        logger.warning(
            "regime_history: SPY series could not resolve %d date(s) this run "
            "(%s%s); preserved last-known-good spy_close_change_pct and marked "
            "%s=True. SPY close series had %d row(s).",
            len(preserved_dates),
            ", ".join(preserved_dates[:5]),
            "" if len(preserved_dates) <= 5 else ", …",
            STALE_MARKER_KEY,
            len(spy_closes),
        )

    _write_history(history_path, summaries)
    return summaries


def main() -> int:
    summaries = aggregate()
    preserved = sum(1 for s in summaries if s.get(STALE_MARKER_KEY))
    note = f"; {preserved} preserved stale return(s)" if preserved else ""
    print(
        f"regime_history: {len(summaries)} dated record(s) -> "
        f"{REGIME_HISTORY_PATH}{note}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
