from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "tools" / "validate_prd_registry.py"
spec = importlib.util.spec_from_file_location("validate_prd_registry", VALIDATOR_PATH)
validate_prd_registry = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validate_prd_registry)


VALID_INDEX = {
    "tracking_start": 56,
    "latest_complete": 60,
    "next_prd": 61,
    "entries": [
        {
            "number": 56,
            "title": "Candidate lifecycle tracking — deterministic grade/setup_state transition metadata in market_map",
            "status": "COMPLETE",
            "commit": "e7365c6",
        },
        {
            "number": 57,
            "title": "Lifecycle visibility on Signal Forge dashboard — badge, detail row, removed symbols section",
            "status": "COMPLETE",
            "commit": "e7365c6",
        },
        {
            "number": 58,
            "title": "Overnight Exit Guidance Layer",
            "status": "COMPLETE",
            "commit": "8f942c7",
        },
        {
            "number": 59,
            "title": "Macro Tape value row hardening",
            "status": "COMPLETE",
            "commit": "64d6aac",
        },
        {
            "number": 60,
            "title": "Deterministic macro pressure snapshot",
            "status": "COMPLETE",
            "commit": "0ed003b",
        },
        {
            "number": 61,
            "title": "PRD Registry Numbering Guard",
            "status": "IN PROGRESS",
            "commit": None,
        },
    ],
}


MAIN_REGISTRY_ROWS = [
    "| Init | d84cd027 | Bootstrap — initial PRD committed | COMPLETE | — |",
    "| PRD-001 | d37e72f | Historical row | COMPLETE | [PRD-001](prd_history/PRD-001.md) |",
    "| PRD-003.2 | 7838f461 | Decimal patch row | PATCH | [PRD-003.2](prd_history/PRD-003.2.md) |",
    "| PRD-012A | 0d6b0215 | Letter suffix row | COMPLETE | [PRD-012A](prd_history/PRD-012A.md) |",
    "| PRD-053 PATCH | — | Patch suffix row | READY | [PRD-053-PATCH](prd_history/PRD-053-PATCH.md) |",
    "| PRD-056 | e7365c6 | Candidate lifecycle tracking — deterministic grade/setup_state transition metadata in market_map | COMPLETE | [PRD-056](prd_history/PRD-056.md) |",
    "| PRD-057 | e7365c6 | Lifecycle visibility on Signal Forge dashboard — badge, detail row, removed symbols section | COMPLETE | [PRD-057](prd_history/PRD-057.md) |",
    "| PRD-058 | 8f942c7 | Overnight Exit Guidance Layer | COMPLETE | [PRD-058](prd_history/PRD-058.md) |",
    "| PRD-059 | 64d6aac | Macro Tape value row hardening | COMPLETE | [PRD-059](prd_history/PRD-059.md) |",
    "| PRD-060 | 0ed003b | Deterministic macro pressure snapshot | COMPLETE | [PRD-060](prd_history/PRD-060.md) |",
    "| PRD-061 | — | PRD Registry Numbering Guard | IN PROGRESS | [PRD-061](prd_history/PRD-061.md) |",
]


def _registry_text(rows: list[str]) -> str:
    return "\n".join(
        [
            "# PRD Registry",
            "",
            "| PRD | Commit(s) | Title | Status | File |",
            "|-----|-----------|-------|--------|------|",
            *rows,
            "",
            "## Audit Reports",
            "",
            "| PRD | File |",
            "|-----|------|",
            "| PRD-999 | [ignored audit row](prd_history/AUDIT.md) |",
            "",
        ]
    )


def _write_fixture(
    tmp_path: Path,
    *,
    index: dict | None = None,
    rows: list[str] | None = None,
    omit_history: set[int] | None = None,
) -> Path:
    root = tmp_path
    docs = root / "docs"
    history = docs / "prd_history"
    history.mkdir(parents=True)

    data = copy.deepcopy(VALID_INDEX if index is None else index)
    (docs / "prd_index.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    (docs / "PRD_REGISTRY.md").write_text(
        _registry_text(MAIN_REGISTRY_ROWS if rows is None else rows),
        encoding="utf-8",
    )

    missing = omit_history or set()
    for number in range(56, 62):
        if number not in missing:
            (history / f"PRD-{number:03d}.md").write_text(
                f"PRD-{number:03d} test fixture\n",
                encoding="utf-8",
            )

    return root


def _errors(root: Path) -> list[str]:
    return validate_prd_registry.validate_repository(root)


def test_valid_current_registry_index_state_passes(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path)

    assert _errors(root) == []


def test_duplicate_prd_number_fails(tmp_path: Path) -> None:
    index = copy.deepcopy(VALID_INDEX)
    index["entries"].append(copy.deepcopy(index["entries"][4]))
    root = _write_fixture(tmp_path, index=index)

    assert any("Duplicate PRD number: PRD-060 appears more than once" in error for error in _errors(root))


def test_missing_prd_number_fails(tmp_path: Path) -> None:
    index = copy.deepcopy(VALID_INDEX)
    index["entries"] = [entry for entry in index["entries"] if entry["number"] != 59]
    root = _write_fixture(tmp_path, index=index)

    assert any("Missing PRD number: PRD-059 is missing" in error for error in _errors(root))


def test_complete_prd_without_commit_fails(tmp_path: Path) -> None:
    index = copy.deepcopy(VALID_INDEX)
    index["entries"][4]["commit"] = ""
    root = _write_fixture(tmp_path, index=index)

    assert any("Missing commit: PRD-060 is COMPLETE but commit is empty" in error for error in _errors(root))


def test_complete_prd_with_non_hex_commit_fails(tmp_path: Path) -> None:
    index = copy.deepcopy(VALID_INDEX)
    index["entries"][4]["commit"] = "feature/macro-pressure"
    root = _write_fixture(tmp_path, index=index)

    assert any("Invalid commit: PRD-060 commit contains non-hex text" in error for error in _errors(root))


def test_invalid_status_enum_fails(tmp_path: Path) -> None:
    index = copy.deepcopy(VALID_INDEX)
    index["entries"][5]["status"] = "IN_PROGRESS"
    root = _write_fixture(tmp_path, index=index)

    assert any("Invalid status: PRD-061 has status IN_PROGRESS" in error for error in _errors(root))


def test_latest_complete_mismatch_fails(tmp_path: Path) -> None:
    index = copy.deepcopy(VALID_INDEX)
    index["latest_complete"] = 59
    root = _write_fixture(tmp_path, index=index)

    assert any("Bad latest_complete" in error and "expected 60" in error for error in _errors(root))


def test_next_prd_mismatch_fails(tmp_path: Path) -> None:
    index = copy.deepcopy(VALID_INDEX)
    index["next_prd"] = 62
    root = _write_fixture(tmp_path, index=index)

    assert any("Bad next_prd: next_prd is 62 but expected 61" in error for error in _errors(root))


def test_next_prd_may_exist_as_proposed_or_in_progress(tmp_path: Path) -> None:
    for status in ("PROPOSED", "IN PROGRESS"):
        index = copy.deepcopy(VALID_INDEX)
        index["entries"][5]["status"] = status
        rows = [row.replace("IN PROGRESS", status) if "PRD-061" in row else row for row in MAIN_REGISTRY_ROWS]
        root = _write_fixture(tmp_path / status.replace(" ", "_"), index=index, rows=rows)

        assert _errors(root) == []


def test_missing_history_doc_fails_for_tracked_entry(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path, omit_history={58})

    assert any("Missing history doc: docs/prd_history/PRD-058.md not found" in error for error in _errors(root))


def test_registry_index_mismatch_fails(tmp_path: Path) -> None:
    rows = [
        row.replace("Deterministic macro pressure snapshot", "Changed title")
        if "PRD-060" in row
        else row
        for row in MAIN_REGISTRY_ROWS
    ]
    root = _write_fixture(tmp_path, rows=rows)

    assert any("Registry mismatch: PRD-060 title differs" in error for error in _errors(root))


def test_registry_normal_integer_row_missing_from_index_fails(tmp_path: Path) -> None:
    rows = [
        *MAIN_REGISTRY_ROWS,
        "| PRD-062 | — | Future row | PROPOSED | [PRD-062](prd_history/PRD-062.md) |",
    ]
    root = _write_fixture(tmp_path, rows=rows)

    assert any("Registry entry PRD-062 is missing from docs/prd_index.json" in error for error in _errors(root))


def test_parser_ignores_special_and_historical_rows(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path)

    assert _errors(root) == []


def test_validator_does_not_mutate_files(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path)
    watched = [
        root / "docs" / "prd_index.json",
        root / "docs" / "PRD_REGISTRY.md",
        *(root / "docs" / "prd_history").glob("PRD-*.md"),
    ]
    before = {path: path.read_text(encoding="utf-8") for path in watched}

    assert _errors(root) == []

    after = {path: path.read_text(encoding="utf-8") for path in watched}
    assert after == before


def test_prd_061_is_next_when_prd_060_is_latest_complete(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path)
    assert _errors(root) == []

    data = json.loads((root / "docs" / "prd_index.json").read_text(encoding="utf-8"))
    assert data["latest_complete"] == 60
    assert data["next_prd"] == 61


def test_main_exits_nonzero_on_invalid_state(tmp_path: Path, capsys) -> None:
    index = copy.deepcopy(VALID_INDEX)
    index["next_prd"] = 62
    root = _write_fixture(tmp_path, index=index)

    assert validate_prd_registry.main([str(root)]) == 1
    captured = capsys.readouterr()
    assert "Bad next_prd: next_prd is 62 but expected 61" in captured.err
