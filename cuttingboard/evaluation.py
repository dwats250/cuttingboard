"""
Post-trade evaluation layer.

Reads the most recent same-day prior pipeline audit run, evaluates any
ALLOW_TRADE decisions against forward 1-minute bars, and appends one
deterministic result record per evaluated candidate.
"""

from __future__ import annotations

import json
import logging
import math
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd

from cuttingboard import config
from cuttingboard.audit import AUDIT_LOG_PATH
from cuttingboard.ingestion import fetch_intraday_bars

logger = logging.getLogger(__name__)

RESULT_TARGET_HIT = "TARGET_HIT"
RESULT_STOP_HIT = "STOP_HIT"
RESULT_NO_HIT = "NO_HIT"
VALID_RESULTS = frozenset({RESULT_TARGET_HIT, RESULT_STOP_HIT, RESULT_NO_HIT})
EVALUATION_LOG_PATH = "logs/evaluation.jsonl"
_REQUIRED_CANDIDATE_FIELDS = frozenset(
    {"symbol", "direction", "entry", "stop", "target"}
)


def run_post_trade_evaluation(
    *,
    current_run_at_utc: datetime,
    fetch_intraday_bars_fn: Callable[[str], Optional[pd.DataFrame]] = fetch_intraday_bars,
    audit_log_path: str = AUDIT_LOG_PATH,
    evaluation_log_path: str = EVALUATION_LOG_PATH,
    window_bars: int = config.EVALUATION_WINDOW_BARS,
) -> list[dict[str, Any]]:
    """Evaluate the most recent same-day prior run, then append results."""
    prior_record = load_most_recent_prior_run(
        current_run_at_utc=current_run_at_utc,
        audit_log_path=audit_log_path,
    )
    if prior_record is None:
        return []

    candidates = extract_allow_trade_candidates(prior_record)
    if not candidates:
        return []

    records = build_evaluation_records(
        prior_record=prior_record,
        evaluated_at_utc=current_run_at_utc,
        fetch_intraday_bars_fn=fetch_intraday_bars_fn,
        window_bars=window_bars,
    )
    if not records:
        return []

    try:
        append_evaluation_records(records, evaluation_log_path=evaluation_log_path)
    except OSError as exc:
        logger.error("Failed to append evaluation log %s: %s", evaluation_log_path, exc)

    return records


def load_most_recent_prior_run(
    *,
    current_run_at_utc: datetime,
    audit_log_path: str = AUDIT_LOG_PATH,
) -> Optional[dict[str, Any]]:
    """Return the most recent same-day prior pipeline run from audit.jsonl."""
    path = Path(audit_log_path)
    if not path.exists():
        return None

    latest: Optional[dict[str, Any]] = None
    latest_run_at: Optional[datetime] = None
    current_date = current_run_at_utc.date()

    with path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("event") is not None:
                continue
            run_at_raw = record.get("run_at_utc")
            if not isinstance(run_at_raw, str):
                raise KeyError("audit record missing required field: run_at_utc")
            run_at = _parse_utc_datetime(run_at_raw, field_name="run_at_utc")
            if run_at.date() != current_date or run_at >= current_run_at_utc:
                continue
            if latest_run_at is None or run_at > latest_run_at:
                latest = record
                latest_run_at = run_at

    return latest


def extract_allow_trade_candidates(prior_record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return persisted ALLOW_TRADE candidates from a prior audit record."""
    raw_candidates = prior_record.get("trade_decisions")
    if raw_candidates is None:
        raw_candidates = prior_record.get("qualified_trades")
    if raw_candidates is None:
        raise KeyError("audit record missing required field: trade_decisions")
    if not isinstance(raw_candidates, list):
        raise TypeError("trade_decisions must be a list")

    candidates: list[dict[str, Any]] = []
    for raw in raw_candidates:
        if not isinstance(raw, dict):
            raise TypeError("trade_decisions entries must be dicts")
        if raw.get("decision_status") == "ALLOW_TRADE":
            candidate = {
                "symbol": raw["symbol"],
                "direction": raw["direction"],
                "entry": float(raw["entry"]),
                "stop": float(raw["stop"]),
                "target": float(raw["target"]),
            }
            candidates.append(candidate)
    return candidates


def build_evaluation_records(
    *,
    prior_record: dict[str, Any],
    evaluated_at_utc: datetime,
    fetch_intraday_bars_fn: Callable[[str], Optional[pd.DataFrame]],
    window_bars: int = config.EVALUATION_WINDOW_BARS,
) -> list[dict[str, Any]]:
    """Build deterministic evaluation records for one prior run."""
    if window_bars < 1 or window_bars > 120:
        raise ValueError("EVALUATION_WINDOW_BARS must be between 1 and 120")
    if config.EVALUATION_TIMEFRAME != "1m":
        raise ValueError("EVALUATION_TIMEFRAME must match ingestion 1m bars")

    decision_run_raw = prior_record.get("run_at_utc")
    if not isinstance(decision_run_raw, str):
        raise KeyError("audit record missing required field: run_at_utc")
    anchor = _parse_utc_datetime(decision_run_raw, field_name="run_at_utc")

    records: list[dict[str, Any]] = []
    for candidate in extract_allow_trade_candidates(prior_record):
        bars = fetch_intraday_bars_fn(candidate["symbol"])
        evaluation = evaluate_trade_candidate(
            candidate=candidate,
            bars=bars,
            anchor=anchor,
            window_bars=window_bars,
        )
        record = {
            "evaluated_at_utc": evaluated_at_utc.isoformat(),
            "decision_run_at_utc": decision_run_raw,
            "symbol": candidate["symbol"],
            "direction": candidate["direction"],
            "entry": candidate["entry"],
            "stop": candidate["stop"],
            "target": candidate["target"],
            "evaluation": evaluation,
        }
        assert_evaluation_valid(record)
        records.append(record)

    return records


def evaluate_trade_candidate(
    *,
    candidate: dict[str, Any],
    bars: Optional[pd.DataFrame],
    anchor: datetime,
    window_bars: int,
) -> dict[str, Any]:
    """Evaluate one persisted candidate against forward intraday bars."""
    payload = deepcopy(candidate)
    _assert_candidate_shape(payload)

    entry = float(payload["entry"])
    stop = float(payload["stop"])
    target = float(payload["target"])
    direction = payload["direction"]
    risk = abs(entry - stop)
    if risk <= 0:
        raise ValueError(f"{payload['symbol']}: entry and stop must define positive risk")

    qualifying = _filter_forward_bars(bars=bars, anchor=anchor, window_bars=window_bars)
    if qualifying.empty:
        return {
            "result": RESULT_NO_HIT,
            "R_multiple": 0.0,
            "time_to_resolution": 0,
        }

    for idx, (_, bar) in enumerate(qualifying.iterrows(), start=1):
        high = float(bar["High"])
        low = float(bar["Low"])
        if direction == "LONG":
            if low <= stop:
                return _build_evaluation_result(RESULT_STOP_HIT, stop, entry, risk, direction, idx)
            if high >= target:
                return _build_evaluation_result(RESULT_TARGET_HIT, target, entry, risk, direction, idx)
        elif direction == "SHORT":
            if high >= stop:
                return _build_evaluation_result(RESULT_STOP_HIT, stop, entry, risk, direction, idx)
            if low <= target:
                return _build_evaluation_result(RESULT_TARGET_HIT, target, entry, risk, direction, idx)
        else:
            raise ValueError(f"invalid direction: {direction!r}")

    final_close = float(qualifying.iloc[-1]["Close"])
    return _build_evaluation_result(
        RESULT_NO_HIT,
        final_close,
        entry,
        risk,
        direction,
        window_bars,
    )


def assert_evaluation_valid(record: dict[str, Any]) -> None:
    """Validate one persisted evaluation record."""
    evaluation = record.get("evaluation")
    if not isinstance(evaluation, dict):
        raise TypeError("evaluation record missing evaluation payload")

    result = evaluation.get("result")
    if result not in VALID_RESULTS:
        raise ValueError(f"invalid evaluation result: {result!r}")

    r_multiple = evaluation.get("R_multiple")
    if not isinstance(r_multiple, (int, float)) or not math.isfinite(float(r_multiple)):
        raise ValueError("R_multiple must be a finite float")

    time_to_resolution = evaluation.get("time_to_resolution")
    if not isinstance(time_to_resolution, int) or time_to_resolution < 0:
        raise ValueError("time_to_resolution must be a non-negative int")


def append_evaluation_records(
    records: list[dict[str, Any]],
    *,
    evaluation_log_path: str = EVALUATION_LOG_PATH,
) -> None:
    """Append evaluation records to logs/evaluation.jsonl."""
    path = Path(evaluation_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=True) + "\n")


def _filter_forward_bars(
    *,
    bars: Optional[pd.DataFrame],
    anchor: datetime,
    window_bars: int,
) -> pd.DataFrame:
    if bars is None or bars.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    frame = bars.copy(deep=True)
    index = pd.to_datetime(frame.index)
    if index.tz is None:
        index = index.tz_localize("UTC")
    else:
        index = index.tz_convert("UTC")
    frame.index = index
    filtered = frame.loc[frame.index > anchor]
    return filtered.head(window_bars)


def _build_evaluation_result(
    result: str,
    exit_price: float,
    entry: float,
    risk: float,
    direction: str,
    time_to_resolution: int,
) -> dict[str, Any]:
    if direction == "LONG":
        r_multiple = (exit_price - entry) / risk
    elif direction == "SHORT":
        r_multiple = (entry - exit_price) / risk
    else:
        raise ValueError(f"invalid direction: {direction!r}")
    return {
        "result": result,
        "R_multiple": float(r_multiple),
        "time_to_resolution": int(time_to_resolution),
    }


def _assert_candidate_shape(candidate: dict[str, Any]) -> None:
    missing = sorted(_REQUIRED_CANDIDATE_FIELDS.difference(candidate))
    if missing:
        raise KeyError(f"trade_decision missing required fields: {', '.join(missing)}")


def _parse_utc_datetime(value: str, *, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone")
    return parsed
