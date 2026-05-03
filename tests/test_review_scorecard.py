"""Tests for PRD-071: Trading Process Review Scorecard."""

from __future__ import annotations

import json
from pathlib import Path


from cuttingboard.review_scorecard import generate_scorecard


DATE = "2026-01-15"


def _write_journal(tmp_path: Path, records: list[dict]) -> Path:
    path = tmp_path / "manual_trades.jsonl"
    with open(path, "w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    return path


def _base_record(**overrides) -> dict:
    base = {
        "trade_date": DATE,
        "symbol": "SPY",
        "action": "ENTERED",
        "direction": "LONG",
        "instrument_type": "OPTION",
        "thesis_adherence": "FOLLOWED_THESIS",
        "intent": "PLANNED_TRADE",
        "mistake_labels": ["NONE"],
        "system_candidate_id": None,
        "notes": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# R8 — missing journal
# ---------------------------------------------------------------------------

def test_missing_journal_produces_insufficient_data(tmp_path):
    missing = tmp_path / "no_such_file.jsonl"
    sc = generate_scorecard(DATE, journal_path=missing, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "INSUFFICIENT_DATA"
    assert sc["total_records"] == 0
    assert "INSUFFICIENT_DATA" in sc["process_flags"]


def test_wrong_date_records_produce_insufficient_data(tmp_path):
    path = _write_journal(tmp_path, [_base_record(trade_date="2025-01-01")])
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "INSUFFICIENT_DATA"
    assert sc["total_records"] == 0


# ---------------------------------------------------------------------------
# Grade A
# ---------------------------------------------------------------------------

def test_clean_day_all_followed_thesis_no_mistakes_is_A(tmp_path):
    path = _write_journal(tmp_path, [_base_record()])
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "A"
    assert "CLEAN_PROCESS_DAY" in sc["process_flags"]


def test_no_entries_all_skipped_none_mistakes_is_A(tmp_path):
    records = [
        _base_record(action="SKIPPED"),
        _base_record(action="MISSED"),
    ]
    path = _write_journal(tmp_path, records)
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "A"
    assert sc["entered_count"] == 0
    assert "CLEAN_PROCESS_DAY" in sc["process_flags"]


# ---------------------------------------------------------------------------
# Grade B
# ---------------------------------------------------------------------------

def test_followed_thesis_with_non_critical_mistake_is_B(tmp_path):
    path = _write_journal(tmp_path, [_base_record(mistake_labels=["CHASED_ENTRY"])])
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "B"
    assert sc["mistake_counts"] == {"CHASED_ENTRY": 1}
    assert "CLEAN_PROCESS_DAY" not in sc["process_flags"]


# ---------------------------------------------------------------------------
# Grade C
# ---------------------------------------------------------------------------

def test_impulse_trade_with_no_F_or_D_is_C(tmp_path):
    path = _write_journal(tmp_path, [_base_record(intent="IMPULSE_TRADE")])
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "C"
    assert "IMPULSE_TRADE_PRESENT" in sc["process_flags"]
    assert sc["impulse_trade_count"] == 1


# ---------------------------------------------------------------------------
# Grade D
# ---------------------------------------------------------------------------

def test_entered_no_thesis_is_D(tmp_path):
    path = _write_journal(tmp_path, [_base_record(thesis_adherence="NO_THESIS")])
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "D"
    assert "NO_THESIS_ENTRY_PRESENT" in sc["process_flags"]


def test_entered_violated_thesis_is_D(tmp_path):
    path = _write_journal(tmp_path, [_base_record(thesis_adherence="VIOLATED_THESIS")])
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "D"
    assert "THESIS_VIOLATION_PRESENT" in sc["process_flags"]


# ---------------------------------------------------------------------------
# Grade F
# ---------------------------------------------------------------------------

def test_revenge_trade_label_is_F_even_if_thesis_followed(tmp_path):
    path = _write_journal(tmp_path, [_base_record(mistake_labels=["REVENGE_TRADE"])])
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "F"
    assert "REVENGE_TRADE_PRESENT" in sc["process_flags"]


def test_broke_rules_label_is_F(tmp_path):
    path = _write_journal(tmp_path, [_base_record(mistake_labels=["BROKE_RULES"])])
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "F"


# ---------------------------------------------------------------------------
# R7 — P/L field ignored
# ---------------------------------------------------------------------------

def test_pl_field_in_journal_is_ignored(tmp_path):
    record = _base_record()
    record["pnl"] = 1500.0
    record["realized_pl"] = -200.0
    path = _write_journal(tmp_path, [record])
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "A"
    assert "pnl" not in sc
    assert "realized_pl" not in sc


# ---------------------------------------------------------------------------
# R3 — flag invariants
# ---------------------------------------------------------------------------

def test_clean_process_day_absent_on_non_A_grade(tmp_path):
    path = _write_journal(tmp_path, [_base_record(mistake_labels=["CHASED_ENTRY"])])
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["overall_process_grade"] == "B"
    assert "CLEAN_PROCESS_DAY" not in sc["process_flags"]


def test_insufficient_data_flag_present_on_insufficient_data_grade(tmp_path):
    missing = tmp_path / "none.jsonl"
    sc = generate_scorecard(DATE, journal_path=missing, output_dir=tmp_path)
    assert "INSUFFICIENT_DATA" in sc["process_flags"]
    assert sc["overall_process_grade"] == "INSUFFICIENT_DATA"


# ---------------------------------------------------------------------------
# R1 — output file written
# ---------------------------------------------------------------------------

def test_output_file_written(tmp_path):
    path = _write_journal(tmp_path, [_base_record()])
    generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    expected = tmp_path / f"review_scorecard_{DATE}.json"
    assert expected.exists()
    with open(expected) as fh:
        data = json.load(fh)
    assert data["trade_date"] == DATE


# ---------------------------------------------------------------------------
# R6 — mistake_counts excludes NONE
# ---------------------------------------------------------------------------

def test_mistake_counts_excludes_none(tmp_path):
    path = _write_journal(tmp_path, [_base_record(mistake_labels=["NONE"])])
    sc = generate_scorecard(DATE, journal_path=path, output_dir=tmp_path)
    assert sc["mistake_counts"] == {}


# ---------------------------------------------------------------------------
# R9 — no import in runtime / contract / delivery
# ---------------------------------------------------------------------------

def test_review_scorecard_not_imported_by_runtime():
    import ast
    from pathlib import Path

    guarded = ["runtime.py", "contract.py"]
    for fname in guarded:
        fpath = Path("cuttingboard") / fname
        if not fpath.exists():
            continue
        tree = ast.parse(fpath.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in getattr(node, "names", [])]
                mod = getattr(node, "module", "") or ""
                assert "review_scorecard" not in mod, (
                    f"{fname} must not import review_scorecard"
                )
                assert not any("review_scorecard" in n for n in names), (
                    f"{fname} must not import review_scorecard"
                )
