#!/usr/bin/env python3
"""Validate tracked PRD registry/index consistency."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


TRACKING_START = 56
ALLOWED_STATUSES = {"PROPOSED", "IN PROGRESS", "COMPLETE", "PATCH", "DEPRECATED"}
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,40}(,\s*[0-9a-fA-F]{7,40})*$")
REGISTRY_ROW_RE = re.compile(r"^\|\s*PRD-(\d{3})\s*\|")
MAIN_TABLE_HEADER = "| PRD | Commit(s) | Title | Status | File |"


def _display_prd(number: int) -> str:
    return f"PRD-{number:03d}"


def _normalize_registry_commit(value: str) -> str | None:
    stripped = value.strip()
    if stripped in {"", "-", "—"}:
        return None
    return stripped


def _load_index(root: Path, errors: list[str]) -> dict[str, Any] | None:
    path = root / "docs" / "prd_index.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append("Missing docs/prd_index.json")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in docs/prd_index.json: {exc}")
        return None

    if not isinstance(data, dict):
        errors.append("docs/prd_index.json must contain a JSON object")
        return None
    return data


def _validate_index_schema(data: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    if data.get("tracking_start") != TRACKING_START:
        errors.append(f"Bad tracking_start: {data.get('tracking_start')} but expected {TRACKING_START}")

    for key in ("latest_complete", "next_prd"):
        if not isinstance(data.get(key), int):
            errors.append(f"{key} must be an integer")

    entries = data.get("entries")
    if not isinstance(entries, list):
        errors.append("entries must be a list")
        return []

    valid_entries: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entries[{index}] must be an object")
            continue

        number = entry.get("number")
        title = entry.get("title")
        status = entry.get("status")
        commit = entry.get("commit")

        if not isinstance(number, int):
            errors.append(f"entries[{index}].number must be an integer")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{_display_prd(number) if isinstance(number, int) else f'entries[{index}]'} title must be non-empty")
        if status not in ALLOWED_STATUSES:
            errors.append(f"Invalid status: {_display_prd(number) if isinstance(number, int) else f'entries[{index}]'} has status {status} instead of one of {sorted(ALLOWED_STATUSES)}")
        if commit is not None and not isinstance(commit, str):
            errors.append(f"{_display_prd(number) if isinstance(number, int) else f'entries[{index}]'} commit must be a string or null")

        if isinstance(number, int) and isinstance(title, str) and isinstance(status, str):
            valid_entries.append(entry)

    return valid_entries


def _validate_index_rules(data: dict[str, Any], entries: list[dict[str, Any]], errors: list[str]) -> None:
    numbers = [entry["number"] for entry in entries if isinstance(entry.get("number"), int)]
    if numbers != sorted(numbers):
        errors.append("entries must be sorted by number ascending")

    seen: set[int] = set()
    for number in numbers:
        if number in seen:
            errors.append(f"Duplicate PRD number: {_display_prd(number)} appears more than once")
        seen.add(number)

    complete_numbers = [entry["number"] for entry in entries if entry.get("status") == "COMPLETE"]
    if complete_numbers:
        expected_latest = max(complete_numbers)
        if data.get("latest_complete") != expected_latest:
            errors.append(
                f"Bad latest_complete: latest_complete is {data.get('latest_complete')} but expected {expected_latest}"
            )
    elif data.get("latest_complete") is not None:
        errors.append("Bad latest_complete: no COMPLETE entries exist")

    latest_complete = data.get("latest_complete")
    if isinstance(latest_complete, int):
        expected_next = latest_complete + 1
        if data.get("next_prd") != expected_next:
            errors.append(f"Bad next_prd: next_prd is {data.get('next_prd')} but expected {expected_next}")

        for number in range(TRACKING_START, latest_complete + 1):
            if number not in seen:
                errors.append(f"Missing PRD number: {_display_prd(number)} is missing from docs/prd_index.json")

    for entry in entries:
        number = entry["number"]
        commit = entry.get("commit")
        if entry.get("status") == "COMPLETE":
            if not isinstance(commit, str) or not commit.strip():
                errors.append(f"Missing commit: {_display_prd(number)} is COMPLETE but commit is empty")
            elif not COMMIT_RE.fullmatch(commit.strip()):
                errors.append(f"Invalid commit: {_display_prd(number)} commit contains non-hex text")
        elif commit is not None and isinstance(commit, str) and commit.strip() and not COMMIT_RE.fullmatch(commit.strip()):
            errors.append(f"Invalid commit: {_display_prd(number)} commit contains non-hex text")


def _parse_registry(root: Path, errors: list[str]) -> dict[int, dict[str, str | None]]:
    path = root / "docs" / "PRD_REGISTRY.md"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append("Missing docs/PRD_REGISTRY.md")
        return {}

    in_main_table = False
    rows: dict[int, dict[str, str | None]] = {}
    for line in lines:
        if not in_main_table:
            if line.strip() == MAIN_TABLE_HEADER:
                in_main_table = True
            continue

        if not line.startswith("|"):
            break
        if line.startswith("|-----"):
            continue

        match = REGISTRY_ROW_RE.match(line)
        if not match:
            continue

        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue

        number = int(match.group(1))
        if number in rows:
            errors.append(f"Duplicate registry row: {_display_prd(number)} appears more than once")
            continue

        rows[number] = {
            "number": number,
            "commit": _normalize_registry_commit(cells[1]),
            "title": cells[2],
            "status": cells[3],
        }

    return rows


def _validate_history_docs(root: Path, entries: list[dict[str, Any]], errors: list[str]) -> None:
    for entry in entries:
        number = entry["number"]
        if number < TRACKING_START:
            continue
        history_path = root / "docs" / "prd_history" / f"PRD-{number:03d}.md"
        if not history_path.exists():
            errors.append(f"Missing history doc: docs/prd_history/PRD-{number:03d}.md not found")


def _validate_registry_agreement(
    registry_rows: dict[int, dict[str, str | None]],
    entries: list[dict[str, Any]],
    errors: list[str],
) -> None:
    index_by_number = {entry["number"]: entry for entry in entries if entry["number"] >= TRACKING_START}

    for number in sorted(registry_rows):
        if number < TRACKING_START:
            continue
        if number not in index_by_number:
            errors.append(f"Registry entry {_display_prd(number)} is missing from docs/prd_index.json")

    for number, entry in sorted(index_by_number.items()):
        registry_entry = registry_rows.get(number)
        if registry_entry is None:
            errors.append(f"Index entry {_display_prd(number)} is missing from docs/PRD_REGISTRY.md")
            continue

        for field in ("title", "status", "commit"):
            if registry_entry[field] != entry.get(field):
                errors.append(
                    f"Registry mismatch: {_display_prd(number)} {field} differs between docs/PRD_REGISTRY.md and docs/prd_index.json"
                )


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    data = _load_index(root, errors)
    if data is None:
        return errors

    entries = _validate_index_schema(data, errors)
    _validate_index_rules(data, entries, errors)
    registry_rows = _parse_registry(root, errors)
    _validate_history_docs(root, entries, errors)
    _validate_registry_agreement(registry_rows, entries, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]).resolve() if args else Path.cwd()
    errors = validate_repository(root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("PRD registry validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
