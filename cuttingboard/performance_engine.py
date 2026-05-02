"""
Performance evaluation layer — reads evaluation.jsonl and produces
a deterministic per-symbol summary of trade outcomes and edge metrics.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

RESULT_TARGET_HIT = "TARGET_HIT"
RESULT_STOP_HIT = "STOP_HIT"
RESULT_NO_HIT = "NO_HIT"
_VALID_RESULTS = frozenset({RESULT_TARGET_HIT, RESULT_STOP_HIT, RESULT_NO_HIT})

_REQUIRED_FIELDS = ("symbol", "direction", "evaluation")
_MIN_SAMPLE = 5


def run_performance_engine(
    evaluation_log_path: Path,
    output_path: Path,
) -> None:
    if not evaluation_log_path.exists():
        return

    records = _load_records(evaluation_log_path)
    buckets = _aggregate(records)
    summary = _build_summary(buckets)
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    logger.info("performance_summary written: %d buckets", len(buckets))


def _load_records(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open() as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("performance_engine: skipping malformed JSON at line %d", lineno)
                continue
            if _is_valid(record, lineno):
                records.append(record)
    return records


def _is_valid(record: dict[str, Any], lineno: int) -> bool:
    for field in _REQUIRED_FIELDS:
        if field not in record:
            logger.warning("performance_engine: skipping record at line %d — missing field %r", lineno, field)
            return False

    evaluation = record["evaluation"]
    if not isinstance(evaluation, dict):
        logger.warning("performance_engine: skipping record at line %d — evaluation is not a dict", lineno)
        return False

    result = evaluation.get("result")
    if result not in _VALID_RESULTS:
        logger.warning("performance_engine: skipping record at line %d — invalid result %r", lineno, result)
        return False

    if "R_multiple" not in evaluation:
        logger.warning("performance_engine: skipping record at line %d — missing R_multiple", lineno)
        return False

    r = evaluation["R_multiple"]
    if not isinstance(r, (int, float)):
        logger.warning("performance_engine: skipping record at line %d — R_multiple is not numeric", lineno)
        return False

    return True


def _aggregate(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    # Accumulate per-symbol lists for deterministic calculation
    raw: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"win_r": [], "loss_r": [], "flat_r": []}
    )

    for record in records:
        symbol = record["symbol"]
        result = record["evaluation"]["result"]
        r = float(record["evaluation"]["R_multiple"])

        if result == RESULT_TARGET_HIT:
            raw[symbol]["win_r"].append(r)
        elif result == RESULT_STOP_HIT:
            raw[symbol]["loss_r"].append(abs(r))
        else:
            raw[symbol]["flat_r"].append(r)

    buckets: dict[str, dict[str, Any]] = {}
    for symbol in sorted(raw.keys()):
        data = raw[symbol]
        wins = len(data["win_r"])
        losses = len(data["loss_r"])
        flats = len(data["flat_r"])
        total = wins + losses + flats

        if total < _MIN_SAMPLE:
            buckets[symbol] = {
                "total_trades": total,
                "wins": wins,
                "losses": losses,
                "flats": flats,
                "insufficient_data": True,
            }
            continue

        win_rate = wins / total
        avg_r_win = sum(data["win_r"]) / wins if wins else 0.0
        avg_r_loss = sum(data["loss_r"]) / losses if losses else 0.0
        expectancy = (win_rate * avg_r_win) - ((1 - win_rate) * avg_r_loss)

        buckets[symbol] = {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "flats": flats,
            "win_rate": round(win_rate, 4),
            "avg_r_win": round(avg_r_win, 4),
            "avg_r_loss": round(avg_r_loss, 4),
            "expectancy": round(expectancy, 4),
            "insufficient_data": False,
        }

    return buckets


def _build_summary(buckets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "buckets": buckets,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
