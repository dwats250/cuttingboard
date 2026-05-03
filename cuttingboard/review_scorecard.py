"""
Trading process review scorecard generator.

Reads logs/manual_trades.jsonl (PRD-070) and produces a daily process-quality
scorecard. Does NOT affect runtime trade decisions.
Must NOT be imported by runtime.py, contract.py, or any delivery module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

JOURNAL_PATH = Path("logs/manual_trades.jsonl")
SCORECARD_DIR = Path("logs")

_CRITICAL_MISTAKES = {"REVENGE_TRADE", "BROKE_RULES"}
_BAD_THESIS = {"NO_THESIS", "VIOLATED_THESIS"}

_VALID_FLAGS = {
    "NO_TRADES_RECORDED",
    "IMPULSE_TRADE_PRESENT",
    "THESIS_VIOLATION_PRESENT",
    "NO_THESIS_ENTRY_PRESENT",
    "REVENGE_TRADE_PRESENT",
    "OVERTRADING_PRESENT",
    "CLEAN_PROCESS_DAY",
    "INSUFFICIENT_DATA",
}


def generate_scorecard(
    trade_date: str,
    journal_path: Path = JOURNAL_PATH,
    output_dir: Path = SCORECARD_DIR,
) -> dict[str, Any]:
    """Generate and write the process scorecard for trade_date (YYYY-MM-DD)."""
    records = _load_records(journal_path, trade_date)

    if not records:
        scorecard = _insufficient_data_scorecard(trade_date)
    else:
        scorecard = _compute_scorecard(trade_date, records)

    _write(scorecard, trade_date, output_dir)
    return scorecard


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------

def _load_records(path: Path, trade_date: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("trade_date") == trade_date:
                records.append(row)
    return records


def _insufficient_data_scorecard(trade_date: str) -> dict[str, Any]:
    return {
        "trade_date": trade_date,
        "total_records": 0,
        "entered_count": 0,
        "skipped_count": 0,
        "missed_count": 0,
        "exited_count": 0,
        "planned_trade_count": 0,
        "impulse_trade_count": 0,
        "thesis_followed_count": 0,
        "thesis_violated_count": 0,
        "no_thesis_count": 0,
        "mistake_counts": {},
        "process_flags": ["INSUFFICIENT_DATA"],
        "overall_process_grade": "INSUFFICIENT_DATA",
    }


def _compute_scorecard(trade_date: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    entered = [r for r in records if r.get("action") == "ENTERED"]
    skipped = [r for r in records if r.get("action") == "SKIPPED"]
    missed  = [r for r in records if r.get("action") == "MISSED"]
    exited  = [r for r in records if r.get("action") == "EXITED"]

    planned_count = sum(1 for r in records if r.get("intent") == "PLANNED_TRADE")
    impulse_count = sum(1 for r in records if r.get("intent") == "IMPULSE_TRADE")

    thesis_followed = sum(1 for r in records if r.get("thesis_adherence") == "FOLLOWED_THESIS")
    thesis_violated = sum(1 for r in records if r.get("thesis_adherence") == "VIOLATED_THESIS")
    no_thesis       = sum(1 for r in records if r.get("thesis_adherence") == "NO_THESIS")

    mistake_counts: dict[str, int] = {}
    for r in records:
        for label in r.get("mistake_labels", []):
            if label != "NONE":
                mistake_counts[label] = mistake_counts.get(label, 0) + 1

    grade = _grade(records, entered, impulse_count, mistake_counts)
    flags = _flags(records, entered, impulse_count, mistake_counts, grade)

    return {
        "trade_date": trade_date,
        "total_records": len(records),
        "entered_count": len(entered),
        "skipped_count": len(skipped),
        "missed_count": len(missed),
        "exited_count": len(exited),
        "planned_trade_count": planned_count,
        "impulse_trade_count": impulse_count,
        "thesis_followed_count": thesis_followed,
        "thesis_violated_count": thesis_violated,
        "no_thesis_count": no_thesis,
        "mistake_counts": mistake_counts,
        "process_flags": flags,
        "overall_process_grade": grade,
    }


def _grade(
    records: list[dict[str, Any]],
    entered: list[dict[str, Any]],
    impulse_count: int,
    mistake_counts: dict[str, int],
) -> str:
    # R5: priority-ordered grading
    all_labels = {label for r in records for label in r.get("mistake_labels", [])}

    if _CRITICAL_MISTAKES & all_labels:
        return "F"

    if any(r.get("thesis_adherence") in _BAD_THESIS for r in entered):
        return "D"

    if impulse_count > 0:
        return "C"

    all_entered_followed = all(
        r.get("thesis_adherence") == "FOLLOWED_THESIS" for r in entered
    ) if entered else True

    all_mistakes_none = not mistake_counts  # empty dict means only NONE labels

    if all_entered_followed and not all_mistakes_none:
        return "B"

    if all_entered_followed and all_mistakes_none:
        return "A"

    # fallback — no entered records + all NONE mistakes → A
    if not entered:
        all_none = all(
            r.get("mistake_labels") == ["NONE"] for r in records
        )
        if all_none:
            return "A"

    return "B"


def _flags(
    records: list[dict[str, Any]],
    entered: list[dict[str, Any]],
    impulse_count: int,
    mistake_counts: dict[str, int],
    grade: str,
) -> list[str]:
    flags: list[str] = []

    if not records:
        flags.append("NO_TRADES_RECORDED")

    if impulse_count > 0:
        flags.append("IMPULSE_TRADE_PRESENT")

    if any(r.get("thesis_adherence") == "VIOLATED_THESIS" for r in entered):
        flags.append("THESIS_VIOLATION_PRESENT")

    if any(r.get("thesis_adherence") == "NO_THESIS" for r in entered):
        flags.append("NO_THESIS_ENTRY_PRESENT")

    all_labels = {label for r in records for label in r.get("mistake_labels", [])}
    if "REVENGE_TRADE" in all_labels:
        flags.append("REVENGE_TRADE_PRESENT")
    if "OVERTRADED" in mistake_counts:
        flags.append("OVERTRADING_PRESENT")

    if grade == "A":
        flags.append("CLEAN_PROCESS_DAY")

    if grade == "INSUFFICIENT_DATA":
        flags.append("INSUFFICIENT_DATA")

    return flags


def _write(scorecard: dict[str, Any], trade_date: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"review_scorecard_{trade_date}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(scorecard, fh, indent=2)
