"""CLI smoke tests for ``cuttingboard.moomoo_review``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cuttingboard.moomoo_review import main


FIXTURE = Path(__file__).parent / "fixtures" / "moomoo" / "synthetic_statement.pdf"


@pytest.fixture
def chdir_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_cli_single_file_smoke(chdir_tmp, tmp_path):
    audit_path = tmp_path / "audit.jsonl"
    audit_path.write_text("", encoding="utf-8")

    rc = main([str(FIXTURE), "--audit-log", str(audit_path)])
    assert rc == 0

    jsonl_path = tmp_path / "logs" / "moomoo_review.jsonl"
    assert jsonl_path.exists()
    lines = [ln for ln in jsonl_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 9  # matches parser fixture count

    for ln in lines:
        rec = json.loads(ln)
        assert set(rec.keys()) == {
            "trade", "in_universe", "blind_spots", "audit_records",
            "statement_path", "processed_at_utc",
        }
        assert isinstance(rec["trade"], dict)
        assert isinstance(rec["in_universe"], bool)
        assert isinstance(rec["blind_spots"], list)
        assert isinstance(rec["audit_records"], list)

    md_path = tmp_path / "reports" / "moomoo" / "2026-02.md"
    assert md_path.exists()
    body = md_path.read_text(encoding="utf-8")
    assert "Moomoo Statement Review" in body
    assert "2026-02-28" in body


def test_cli_directory_input(chdir_tmp, tmp_path):
    """Directory input processes every *.pdf file (non-recursive)."""
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    # Symlink works on linux; fall back to copy if not.
    try:
        (pdf_dir / "synthetic.pdf").symlink_to(FIXTURE)
    except OSError:
        (pdf_dir / "synthetic.pdf").write_bytes(FIXTURE.read_bytes())

    rc = main([str(pdf_dir)])
    assert rc == 0
    jsonl_path = tmp_path / "logs" / "moomoo_review.jsonl"
    assert jsonl_path.exists()
    assert len(jsonl_path.read_text(encoding="utf-8").splitlines()) == 9


def test_cli_missing_path_exits_1(chdir_tmp, tmp_path):
    rc = main([str(tmp_path / "does_not_exist.pdf")])
    assert rc == 1


def test_cli_empty_directory_exits_1(chdir_tmp, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    rc = main([str(empty)])
    assert rc == 1


def test_cli_jsonl_is_append_only(chdir_tmp, tmp_path):
    """Repeated invocations append to logs/moomoo_review.jsonl."""
    audit_path = tmp_path / "audit.jsonl"
    audit_path.write_text("", encoding="utf-8")
    assert main([str(FIXTURE), "--audit-log", str(audit_path)]) == 0
    assert main([str(FIXTURE), "--audit-log", str(audit_path)]) == 0
    jsonl_path = tmp_path / "logs" / "moomoo_review.jsonl"
    assert len(jsonl_path.read_text(encoding="utf-8").splitlines()) == 18


def test_cli_markdown_is_overwritten(chdir_tmp, tmp_path):
    """Repeated invocations overwrite (not append) the Markdown report."""
    audit_path = tmp_path / "audit.jsonl"
    audit_path.write_text("", encoding="utf-8")
    main([str(FIXTURE), "--audit-log", str(audit_path)])
    md_path = tmp_path / "reports" / "moomoo" / "2026-02.md"
    size1 = md_path.stat().st_size
    main([str(FIXTURE), "--audit-log", str(audit_path)])
    size2 = md_path.stat().st_size
    assert size1 == size2
