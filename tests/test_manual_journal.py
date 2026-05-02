"""Tests for manual_journal.py — PRD-070."""

import json
from pathlib import Path

import pytest

from cuttingboard.manual_journal import TradeJournalRecord, append_record


def _valid_record(**overrides) -> TradeJournalRecord:
    defaults = dict(
        trade_date="2026-05-01",
        symbol="SPY",
        action="ENTERED",
        direction="LONG",
        instrument_type="OPTION",
        thesis_adherence="FOLLOWED_THESIS",
        intent="PLANNED_TRADE",
        mistake_labels=("NONE",),
        system_candidate_id=None,
        notes=None,
    )
    defaults.update(overrides)
    return TradeJournalRecord(**defaults)


class TestValidRecords:
    def test_entered_option_writes_jsonl(self, tmp_path):
        path = tmp_path / "manual_trades.jsonl"
        record = _valid_record()
        append_record(record, path=path)
        lines = path.read_text().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["symbol"] == "SPY"
        assert data["action"] == "ENTERED"
        assert data["mistake_labels"] == ["NONE"]
        assert data["system_candidate_id"] is None
        assert "recorded_at_utc" in data

    def test_skipped_trade_writes_jsonl(self, tmp_path):
        path = tmp_path / "manual_trades.jsonl"
        record = _valid_record(action="SKIPPED", intent="REVIEW_ONLY")
        append_record(record, path=path)
        data = json.loads(path.read_text().splitlines()[0])
        assert data["action"] == "SKIPPED"

    def test_multiple_mistake_labels(self, tmp_path):
        path = tmp_path / "manual_trades.jsonl"
        record = _valid_record(mistake_labels=("CHASED_ENTRY", "OVERSIZED"))
        append_record(record, path=path)
        data = json.loads(path.read_text().splitlines()[0])
        assert set(data["mistake_labels"]) == {"CHASED_ENTRY", "OVERSIZED"}

    def test_null_system_candidate_id_accepted(self, tmp_path):
        path = tmp_path / "manual_trades.jsonl"
        record = _valid_record(system_candidate_id=None)
        append_record(record, path=path)
        data = json.loads(path.read_text().splitlines()[0])
        assert data["system_candidate_id"] is None

    def test_with_system_candidate_id(self, tmp_path):
        path = tmp_path / "manual_trades.jsonl"
        record = _valid_record(system_candidate_id="SPY-LONG-20260501")
        append_record(record, path=path)
        data = json.loads(path.read_text().splitlines()[0])
        assert data["system_candidate_id"] == "SPY-LONG-20260501"

    def test_append_multiple_records(self, tmp_path):
        path = tmp_path / "manual_trades.jsonl"
        append_record(_valid_record(symbol="SPY"), path=path)
        append_record(_valid_record(symbol="QQQ", action="SKIPPED"), path=path)
        lines = path.read_text().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[1])["symbol"] == "QQQ"

    def test_none_alone_is_accepted(self):
        record = _valid_record(mistake_labels=("NONE",))
        assert record.mistake_labels == ("NONE",)


class TestValidationErrors:
    def test_missing_required_field_raises(self):
        with pytest.raises((ValueError, TypeError)):
            TradeJournalRecord(
                trade_date="2026-05-01",
                symbol="",
                action="ENTERED",
                direction="LONG",
                instrument_type="OPTION",
                thesis_adherence="FOLLOWED_THESIS",
                intent="PLANNED_TRADE",
                mistake_labels=("NONE",),
            )

    def test_invalid_action_raises(self):
        with pytest.raises(ValueError, match="Invalid action"):
            _valid_record(action="BUY")

    def test_invalid_direction_raises(self):
        with pytest.raises(ValueError, match="Invalid direction"):
            _valid_record(direction="UP")

    def test_invalid_instrument_type_raises(self):
        with pytest.raises(ValueError, match="Invalid instrument_type"):
            _valid_record(instrument_type="FUTURES")

    def test_invalid_thesis_adherence_raises(self):
        with pytest.raises(ValueError, match="Invalid thesis_adherence"):
            _valid_record(thesis_adherence="MAYBE")

    def test_invalid_intent_raises(self):
        with pytest.raises(ValueError, match="Invalid intent"):
            _valid_record(intent="GAMBLING")

    def test_invalid_mistake_label_raises(self):
        with pytest.raises(ValueError, match="Invalid mistake_labels"):
            _valid_record(mistake_labels=("FOMO",))

    def test_empty_mistake_labels_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            _valid_record(mistake_labels=())

    def test_none_with_other_label_raises(self):
        with pytest.raises(ValueError, match='"NONE" must be the only element'):
            _valid_record(mistake_labels=("NONE", "CHASED_ENTRY"))


class TestRuntimeIsolation:
    def test_manual_journal_not_imported_by_runtime(self):
        import importlib
        import cuttingboard.runtime as rt
        source = Path(rt.__file__).read_text()
        assert "manual_journal" not in source

    def test_manual_journal_not_imported_by_contract(self):
        import cuttingboard.contract as ct
        source = Path(ct.__file__).read_text()
        assert "manual_journal" not in source
