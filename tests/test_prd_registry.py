from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
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
            # PRD-269: carries a bare-STATUS/COMPLETE header so the default
            # fixture stays clean under _validate_doc_status_word_agreement.
            # Numbers whose registry row isn't COMPLETE (e.g. PRD-061,
            # default IN PROGRESS) are skipped by that check regardless of
            # doc content, so a uniform COMPLETE header here is safe.
            (history / f"PRD-{number:03d}.md").write_text(
                f"PRD-{number:03d} test fixture\n\nSTATUS\nCOMPLETE\n",
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

    assert any("Invalid commit: PRD-060 commit is neither a hex SHA nor a PR reference (#NNN)" in error for error in _errors(root))


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


# ---------------------------------------------------------------------------
# PRD-164 R6: commit-hash drift detection
# ---------------------------------------------------------------------------

def _init_git_repo(root: Path) -> str:
    """Init a git repo at `root` with one commit; return its short hash."""
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    (root / "seed.txt").write_text("seed\n")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True
    ).stdout.strip()


def _rows(commit: str, file_cell: str = "x") -> dict[int, dict[str, str | None]]:
    return {56: {"number": 56, "status": "COMPLETE", "commit": commit, "file": file_cell}}


def test_r6_commit_tokens_splits_multi_hash() -> None:
    assert validate_prd_registry._commit_tokens("a1b2c3d, e4f5a6b") == ["a1b2c3d", "e4f5a6b"]
    assert validate_prd_registry._commit_tokens(None) == []
    assert validate_prd_registry._commit_tokens("—") == ["—"]  # caller strips dashes upstream


def test_r6_unresolvable_commit_flagged_in_git_tree(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    errors: list[str] = []
    validate_prd_registry._validate_commit_resolvable(tmp_path, _rows("deadbee"), errors)
    assert any("Unresolvable commit: PRD-056 hash deadbee" in e for e in errors)


def test_r6_real_commit_passes_in_git_tree(tmp_path: Path) -> None:
    real = _init_git_repo(tmp_path)
    errors: list[str] = []
    validate_prd_registry._validate_commit_resolvable(tmp_path, _rows(real), errors)
    assert errors == []


def test_r6_multi_hash_each_checked(tmp_path: Path) -> None:
    real = _init_git_repo(tmp_path)
    errors: list[str] = []
    validate_prd_registry._validate_commit_resolvable(
        tmp_path, _rows(f"{real}, deadbee"), errors
    )
    assert any("deadbee" in e for e in errors)
    assert not any(real in e for e in errors)


def test_r6_non_hex_token_skipped(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    errors: list[str] = []
    validate_prd_registry._validate_commit_resolvable(
        tmp_path, _rows("feature/ui-decision-layer"), errors
    )
    assert errors == []


def test_r6_non_git_tree_skips_resolvability(tmp_path: Path) -> None:
    # No .git -> synthetic hashes must not be flagged.
    errors: list[str] = []
    validate_prd_registry._validate_commit_resolvable(tmp_path, _rows("deadbee"), errors)
    assert errors == []


def test_r6_doc_status_hash_mismatch_flagged(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text(
        "# PRD-056\n\nStatus: COMPLETE\n\nSTATUS: COMPLETE @ deadbee\n"
    )
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](prd_history/PRD-056.md)"), errors
    )
    assert any("Doc/registry hash mismatch: PRD-056" in e for e in errors)


def test_r6_doc_status_membership_passes_multi_hash(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text(
        "# PRD-056\n\nSTATUS: COMPLETE @ e4f5a6b\n"
    )
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_agreement(
        tmp_path, _rows("a1b2c3d, e4f5a6b", file_cell="[PRD-056](x)"), errors
    )
    assert errors == []


def test_r6_doc_check_skipped_when_file_dash(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text(
        "STATUS: COMPLETE @ deadbee\n"
    )
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_agreement(
        tmp_path, _rows("e7365c6", file_cell="—"), errors
    )
    assert errors == []


def test_r6_doc_without_status_line_skipped(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text("PRD-056 fixture, no status line\n")
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](x)"), errors
    )
    assert errors == []


# ---------------------------------------------------------------------------
# PRD-269: doc-status blind spot. _validate_doc_status_agreement above only
# fires on the "STATUS: COMPLETE @ <hash>" convention, so a doc still
# reading IN PROGRESS/PROPOSED against a COMPLETE registry row produced no
# signal there. _extract_doc_status_words / _validate_doc_status_word_agreement
# read the doc's status word directly, independent of hash format and
# header convention, and treat an unrecognized-or-absent status line as a
# FAILURE rather than a skip.
# ---------------------------------------------------------------------------

def test_269_bold_convention_recognized() -> None:
    words = validate_prd_registry._extract_doc_status_words("# Title\n\n**Status:** COMPLETE\n")
    assert words == {"COMPLETE"}


def test_269_plain_colon_convention_recognized() -> None:
    words = validate_prd_registry._extract_doc_status_words("# Title\n\nSTATUS: COMPLETE\n")
    assert words == {"COMPLETE"}


def test_269_bare_next_line_convention_recognized() -> None:
    words = validate_prd_registry._extract_doc_status_words("PRD-107 — Title\n\nSTATUS\nCOMPLETE\n\nGOAL\n")
    assert words == {"COMPLETE"}


def test_269_escaped_asterisk_convention_recognized() -> None:
    words = validate_prd_registry._extract_doc_status_words(
        "# Title\n\n\\*\\*Status:\\*\\* COMPLETE\n**Commit:** --\n"
    )
    assert words == {"COMPLETE"}


def test_269_heading_convention_recognized() -> None:
    words = validate_prd_registry._extract_doc_status_words("# Title\n\n## STATUS\nCOMPLETE\n\n## CLASS\n")
    assert words == {"COMPLETE"}


def test_269_bullet_convention_recognized() -> None:
    words = validate_prd_registry._extract_doc_status_words(
        "# Title\n\n- **LANE:** STANDARD\n- **STATUS:** COMPLETE\n"
    )
    assert words == {"COMPLETE"}


def test_269_in_progress_word_extracted() -> None:
    words = validate_prd_registry._extract_doc_status_words("# Title\n\n**Status:** IN PROGRESS\n")
    assert words == {"IN PROGRESS"}


def test_269_proposed_word_extracted() -> None:
    words = validate_prd_registry._extract_doc_status_words("# Title\n\nSTATUS\nPROPOSED\n")
    assert words == {"PROPOSED"}


def test_269_no_status_line_returns_empty_set() -> None:
    words = validate_prd_registry._extract_doc_status_words("# Title\n\n## GOAL\n\nSome body text.\n")
    assert words == set()


def test_269_unrecognized_seventh_format_returns_empty_set() -> None:
    # A deliberately invented format none of the six known conventions
    # cover, proving the parser doesn't accidentally match arbitrary prose.
    words = validate_prd_registry._extract_doc_status_words("# Title\n\nCurrent State: Done\n")
    assert words == set()


def test_269_agreement_passes(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text("# Title\n\n**Status:** COMPLETE\n")
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](x)"), errors
    )
    assert errors == []


def test_269_disagreement_flagged_in_progress(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text("# Title\n\n**Status:** IN PROGRESS\n")
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](x)"), errors
    )
    assert any("Doc status disagreement: PRD-056" in e and "IN PROGRESS" in e for e in errors)


def test_269_disagreement_flagged_proposed(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text("# Title\n\nSTATUS\nPROPOSED\n")
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](x)"), errors
    )
    assert any("Doc status disagreement: PRD-056" in e and "PROPOSED" in e for e in errors)


def test_269_unreadable_when_no_status_line(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text("# Title\n\n## GOAL\n\nBody text only.\n")
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](x)"), errors
    )
    assert any("Doc status unreadable: PRD-056" in e for e in errors)


def test_269_unreadable_when_unrecognized_format(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text("# Title\n\nCurrent State: Done\n")
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](x)"), errors
    )
    assert any("Doc status unreadable: PRD-056" in e for e in errors)


def test_269_skipped_when_file_dash(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text("# Title\n\n**Status:** IN PROGRESS\n")
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(
        tmp_path, _rows("e7365c6", file_cell="—"), errors
    )
    assert errors == []


def test_269_skipped_when_doc_missing(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](x)"), errors
    )
    assert errors == []


def test_269_skipped_when_not_complete(tmp_path: Path) -> None:
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text("# Title\n\nno status line at all\n")
    rows = {56: {"number": 56, "status": "IN PROGRESS", "commit": None, "file": "[PRD-056](x)"}}
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(tmp_path, rows, errors)
    assert errors == []


def test_269_existing_hash_check_independent_of_new_check(tmp_path: Path) -> None:
    # R4: the trailing hash-agreement check and the new status-word check
    # fire independently off the same doc/registry pair, neither masking
    # the other.
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text(
        "# Title\n\n**Status:** COMPLETE\n\nSTATUS: COMPLETE @ deadbee\n"
    )
    rows = _rows("e7365c6", file_cell="[PRD-056](x)")
    hash_errors: list[str] = []
    validate_prd_registry._validate_doc_status_agreement(tmp_path, rows, hash_errors)
    assert any("Doc/registry hash mismatch: PRD-056" in e for e in hash_errors)

    word_errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(tmp_path, rows, word_errors)
    assert word_errors == []


def test_269_group_a_stale_header_correct_trailer_flagged(tmp_path: Path) -> None:
    # Group A (found by a full-registry sweep, 8 real instances: PRD-140,
    # 144-148, 154, 155): the header a human reads first still says
    # PROPOSED/IN PROGRESS, but a correctly-formatted trailing
    # "STATUS: COMPLETE @ <hash>" line already exists. A lenient
    # "COMPLETE anywhere" check passes this silently; the strict
    # words == {"COMPLETE"} floor must not.
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text(
        "# Title\n\nSTATUS\nPROPOSED\n\nGOAL\n...\n\nSTATUS: COMPLETE @ e7365c6\n"
    )
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](x)"), errors
    )
    assert any(
        "Doc status disagreement: PRD-056" in e and "COMPLETE" in e and "PROPOSED" in e
        for e in errors
    )


def test_269_group_b_correct_header_stale_trailer_flagged(tmp_path: Path) -> None:
    # Group B (2 real instances: PRD-189, 194): the inverse of Group A —
    # header correctly says COMPLETE, but a leftover trailing
    # "STATUS: IN PROGRESS" line was never updated at closeout.
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text(
        "# Title\n\n**Status:** COMPLETE\n\nGOAL\n...\n\nSTATUS: IN PROGRESS\n"
    )
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](x)"), errors
    )
    assert any(
        "Doc status disagreement: PRD-056" in e and "COMPLETE" in e and "IN PROGRESS" in e
        for e in errors
    )


def test_269_completed_typo_not_extracted_as_complete() -> None:
    # Review catch: a bare `startswith` prefix check accepted "COMPLETED" as
    # "COMPLETE" ("COMPLETED".startswith("COMPLETE")), silently treating a
    # malformed status word as valid agreement -- the third partial-match
    # hole found in this same check (after "COMPLETE anywhere" and the
    # hash-format-only regex). Requires a token boundary after the
    # candidate: the matched word must be the whole value or followed by a
    # non-alphanumeric character.
    words = validate_prd_registry._extract_doc_status_words("# Title\n\n**Status:** COMPLETED\n")
    assert words == set()


def test_269_incomplete_not_extracted_as_complete() -> None:
    # A second near-miss, lexically related but not a prefix match in
    # either direction -- pins that status matching is whole-token, not
    # substring/fuzzy.
    words = validate_prd_registry._extract_doc_status_words("# Title\n\n**Status:** INCOMPLETE\n")
    assert words == set()


def test_269_completed_typo_registry_complete_flagged(tmp_path: Path) -> None:
    # A doc whose ONLY status line is a malformed near-miss is flagged as
    # a disagreement (something was declared, just wrong), not as
    # "unreadable" (nothing found) — round 2's malformed-line tracking
    # distinguishes the two rather than treating both as absence.
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text("# Title\n\n**Status:** COMPLETED\n")
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](x)"), errors
    )
    assert any(
        "Doc status disagreement: PRD-056" in e and "COMPLETED" in e for e in errors
    )


def test_269_hyphenated_near_miss_not_extracted(tmp_path: Path) -> None:
    # Round-1's boundary fix allowed any non-alphanumeric follower, which
    # still let "COMPLETE-ish" pass ("-" satisfies that check). Round 2
    # requires whitespace or end-of-string specifically.
    words = validate_prd_registry._extract_doc_status_words("# Title\n\n**Status:** COMPLETE-ish\n")
    assert words == set()


def test_269_valid_line_plus_malformed_line_flagged(tmp_path: Path) -> None:
    # Round-2 catch: a doc with one VALID "Status: COMPLETE" line and a
    # SEPARATE malformed line ("STATUS: COMPLETED @ abc") must not pass
    # just because one line happens to be valid — the malformed line is
    # evidence of a problem, not silently dropped.
    (tmp_path / "docs" / "prd_history").mkdir(parents=True)
    (tmp_path / "docs" / "prd_history" / "PRD-056.md").write_text(
        "# Title\n\n**Status:** COMPLETE\n\nGOAL\n...\n\nSTATUS: COMPLETED @ abc\n"
    )
    errors: list[str] = []
    validate_prd_registry._validate_doc_status_word_agreement(
        tmp_path, _rows("e7365c6", file_cell="[PRD-056](x)"), errors
    )
    assert any(
        "Doc status disagreement: PRD-056" in e and "COMPLETE" in e and "COMPLETED" in e
        for e in errors
    )


def test_269_lowercase_status_prose_not_treated_as_declaration() -> None:
    # Malformed-line tracking (round 2) initially matched ANY line
    # starting with "status" case-insensitively, which caught ordinary
    # body prose ("- status: one of VALID, INCOMPLETE, ...", describing an
    # unrelated code enum) as a false "malformed declaration" -- found by
    # running the tightened check against the full live registry before
    # shipping it (16 false positives). Every real convention capitalizes
    # the label ("Status"/"STATUS"); plain lowercase "status" must be
    # ignored entirely, not flagged.
    words, malformed = validate_prd_registry._scan_doc_status_lines(
        "# Title\n\n**Status:** COMPLETE\n\n"
        "- status: one of VALID, INCOMPLETE, CONFLICTED, UNKNOWN\n"
        "- status = BLOCK_TRADE\n"
    )
    assert words == {"COMPLETE"}
    assert malformed == []


def test_269_status_as_a_noun_not_treated_as_declaration() -> None:
    # A second false-positive shape from the same live-registry run: a
    # capitalized "Status" used as an ordinary noun ("Status column:
    # PARTIAL · Tier header: ...", describing a dashboard column) rather
    # than a declaration. Every real convention has the label immediately
    # followed by nothing or ":" -- never a space then another word.
    words, malformed = validate_prd_registry._scan_doc_status_lines(
        "# Title\n\n**Status:** COMPLETE\n\n"
        "Status column: PARTIAL · Tier header: D/F — FAILING · Card VALIDATION ·\n"
    )
    assert words == {"COMPLETE"}
    assert malformed == []


# ---------------------------------------------------------------------------
# PRD-200: --skip-commit-resolvability is a NARROW, CI-scoped opt-out.
# In a clean CI checkout the synthetic/historical COMPLETE hashes do not
# resolve; the flag must skip ONLY that git check, never a consistency check.
# ---------------------------------------------------------------------------

def test_skip_commit_resolvability_flag_skips_only_git_check(tmp_path: Path) -> None:
    # A git tree whose registry COMPLETE rows carry synthetic (unresolvable) hashes.
    root = _write_fixture(tmp_path)
    _init_git_repo(root)

    full = validate_prd_registry.validate_repository(root)
    assert any("Unresolvable commit" in e for e in full)

    skipped = validate_prd_registry.validate_repository(
        root, skip_commit_resolvability=True
    )
    assert not any("Unresolvable commit" in e for e in skipped)
    # The fixture is otherwise consistent: skipping resolvability leaves no errors.
    assert skipped == []


def test_skip_commit_resolvability_still_catches_consistency_drift(tmp_path: Path) -> None:
    # PRD-056 title diverges between index and registry; the flag must NOT hide it.
    index = copy.deepcopy(VALID_INDEX)
    index["entries"][0]["title"] = "DRIFTED INDEX TITLE"
    root = _write_fixture(tmp_path, index=index)
    _init_git_repo(root)

    errors = validate_prd_registry.validate_repository(
        root, skip_commit_resolvability=True
    )
    assert any("Registry mismatch: PRD-056 title differs" in e for e in errors)


def test_main_skip_commit_resolvability_flag(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path)
    _init_git_repo(root)
    # Without the flag the historical hashes are unresolvable -> exit 1.
    assert validate_prd_registry.main([str(root)]) == 1
    # With the flag the consistency-clean fixture passes -> exit 0.
    assert validate_prd_registry.main([str(root), "--skip-commit-resolvability"]) == 0


# ---------------------------------------------------------------------------
# PRD-229 R3: same-PR closeout — COMPLETE commit cells may record a PR
# reference (#NNN) because the squash SHA does not exist until merge.
# ---------------------------------------------------------------------------

def _fixture_with_prd060_commit(tmp_path: Path, commit: str) -> Path:
    index = copy.deepcopy(VALID_INDEX)
    index["entries"][4]["commit"] = commit
    rows = [
        row.replace("| 0ed003b |", f"| {commit} |") if "PRD-060" in row else row
        for row in MAIN_REGISTRY_ROWS
    ]
    return _write_fixture(tmp_path, index=index, rows=rows)


def test_complete_prd_with_pr_reference_commit_passes(tmp_path: Path) -> None:
    root = _fixture_with_prd060_commit(tmp_path, "#98")

    assert _errors(root) == []


def test_complete_prd_with_mixed_hex_and_pr_reference_passes(tmp_path: Path) -> None:
    root = _fixture_with_prd060_commit(tmp_path, "0ed003b, #98")

    assert _errors(root) == []


def test_complete_prd_with_malformed_pr_reference_fails(tmp_path: Path) -> None:
    root = _fixture_with_prd060_commit(tmp_path, "#abc")

    assert any("Invalid commit: PRD-060" in error for error in _errors(root))


def test_r6_pr_reference_token_skipped_by_resolvability(tmp_path: Path) -> None:
    # A PR reference is not a git object; resolvability must never flag it.
    _init_git_repo(tmp_path)
    errors: list[str] = []
    validate_prd_registry._validate_commit_resolvable(tmp_path, _rows("#98"), errors)
    assert errors == []


# ---------------------------------------------------------------------------
# PRD-242 second-model disposition (write-the-sentence)
# ---------------------------------------------------------------------------

SENTENCE = validate_prd_registry.SECOND_MODEL_SENTENCE


def _hr_rows(number: int) -> dict[int, dict[str, str | None]]:
    return {
        number: {
            "number": number,
            "status": "COMPLETE",
            "commit": "#114",
            "file": f"[PRD-{number:03d}](prd_history/PRD-{number:03d}.md)",
        }
    }


def _write_prd_doc(tmp_path: Path, number: int, body: str) -> Path:
    history = tmp_path / "docs" / "prd_history"
    history.mkdir(parents=True, exist_ok=True)
    doc = history / f"PRD-{number:03d}.md"
    doc.write_text(body, encoding="utf-8")
    return doc


def test_242_high_risk_without_artifact_or_sentence_fails(tmp_path: Path) -> None:
    # RED case: the guard must fail when violated (PRD-198 invariant 4).
    _write_prd_doc(tmp_path, 243, "PRD-243 — x\n\nLANE\nHIGH-RISK\n\nGOAL\nx\n")
    errors: list[str] = []
    validate_prd_registry._validate_second_model_disposition(tmp_path, _hr_rows(243), errors)
    assert any("Second-model disposition missing: PRD-243" in e for e in errors)


def test_242_claude_review_artifact_alone_does_not_satisfy(tmp_path: Path) -> None:
    # The Claude review is the FIRST leg; it must never count as the second model.
    _write_prd_doc(tmp_path, 243, "PRD-243 — x\n\nLANE\nHIGH-RISK\n")
    (tmp_path / "docs" / "prd_history" / "PRD-243.review.claude.md").write_text(
        "VERDICT: ACCEPT\n", encoding="utf-8"
    )
    errors: list[str] = []
    validate_prd_registry._validate_second_model_disposition(tmp_path, _hr_rows(243), errors)
    assert any("Second-model disposition missing: PRD-243" in e for e in errors)


def test_242_sentence_in_prd_doc_satisfies(tmp_path: Path) -> None:
    _write_prd_doc(
        tmp_path,
        243,
        f"PRD-243 — x\n\nLANE\nHIGH-RISK\n\nSECOND-MODEL: {SENTENCE}.\n",
    )
    errors: list[str] = []
    validate_prd_registry._validate_second_model_disposition(tmp_path, _hr_rows(243), errors)
    assert errors == []


def test_242_second_model_artifact_satisfies(tmp_path: Path) -> None:
    _write_prd_doc(tmp_path, 243, "PRD-243 — x\n\nLANE\nHIGH-RISK\n")
    (tmp_path / "docs" / "prd_history" / "PRD-243.review.gpt5.md").write_text(
        "Mechanism: commissioned second-model review\n", encoding="utf-8"
    )
    errors: list[str] = []
    validate_prd_registry._validate_second_model_disposition(tmp_path, _hr_rows(243), errors)
    assert errors == []


def test_242_inline_lane_form_detected(tmp_path: Path) -> None:
    # "LANE: HIGH-RISK" single-line form must also trip the check.
    _write_prd_doc(tmp_path, 243, "PRD-243 — x\n\nLANE: HIGH-RISK\n")
    errors: list[str] = []
    validate_prd_registry._validate_second_model_disposition(tmp_path, _hr_rows(243), errors)
    assert any("Second-model disposition missing: PRD-243" in e for e in errors)


def test_242_pre_cutoff_high_risk_exempt(tmp_path: Path) -> None:
    # Historical rows (< 242) are exempt; they are not rewritten.
    _write_prd_doc(tmp_path, 240, "PRD-240 — x\n\nLANE\nHIGH-RISK\n")
    errors: list[str] = []
    validate_prd_registry._validate_second_model_disposition(tmp_path, _hr_rows(240), errors)
    assert errors == []


def test_242_standard_lane_exempt(tmp_path: Path) -> None:
    _write_prd_doc(tmp_path, 243, "PRD-243 — x\n\nLANE\nSTANDARD\n")
    errors: list[str] = []
    validate_prd_registry._validate_second_model_disposition(tmp_path, _hr_rows(243), errors)
    assert errors == []


def test_242_non_complete_high_risk_not_checked(tmp_path: Path) -> None:
    _write_prd_doc(tmp_path, 243, "PRD-243 — x\n\nLANE\nHIGH-RISK\n")
    rows = _hr_rows(243)
    rows[243]["status"] = "IN PROGRESS"
    rows[243]["commit"] = None
    errors: list[str] = []
    validate_prd_registry._validate_second_model_disposition(tmp_path, rows, errors)
    assert errors == []


def test_242_misnamed_claude_variant_does_not_satisfy(tmp_path: Path) -> None:
    # Review RECOMMENDED EDIT 1: any claude-* model token is the first leg,
    # never the second model — claude-fresh/claude2 must not satisfy R2.
    _write_prd_doc(tmp_path, 243, "PRD-243 — x\n\nLANE\nHIGH-RISK\n")
    (tmp_path / "docs" / "prd_history" / "PRD-243.review.claude-fresh.md").write_text(
        "VERDICT: ACCEPT\n", encoding="utf-8"
    )
    errors: list[str] = []
    validate_prd_registry._validate_second_model_disposition(tmp_path, _hr_rows(243), errors)
    assert any("Second-model disposition missing: PRD-243" in e for e in errors)
