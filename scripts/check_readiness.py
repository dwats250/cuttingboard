#!/usr/bin/env python3
"""Validate scheduled dashboard artifacts before publishing them."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

JSON_REQUIRED_FIELDS = {
    Path("logs/latest_hourly_payload.json"): ("meta", "run_status", "schema_version", "sections"),
    Path("logs/latest_hourly_run.json"): ("status", "outcome"),
}
HTML_ARTIFACTS = (
    Path("ui/dashboard.html"),
    Path("ui/index.html"),
)
FORBIDDEN_HTML_PATTERNS = ("pytest-of-", "/tmp/pytest", "/tmp/")
REQUIRED_HTML_MARKERS = (
    'id="system-state"',
    'id="macro-tape"',
    'id="candidate-board"',
    "RUN SNAPSHOT",
)


def _load_json(path: Path, failures: list[str]) -> dict[str, Any] | None:
    full_path = ROOT / path
    if not full_path.exists():
        failures.append(f"{path}: missing required JSON artifact")
        return None
    try:
        data = json.loads(full_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return None
    if not isinstance(data, dict):
        failures.append(f"{path}: expected top-level JSON object")
        return None
    return data


def _validate_json_artifact(path: Path, required_fields: tuple[str, ...], failures: list[str]) -> None:
    data = _load_json(path, failures)
    if data is None:
        return
    for field in required_fields:
        if field not in data:
            failures.append(f"{path}: missing required field {field!r}")


def _read_html(path: Path, failures: list[str]) -> str | None:
    full_path = ROOT / path
    if not full_path.exists():
        failures.append(f"{path}: missing required HTML artifact")
        return None
    try:
        return full_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        failures.append(f"{path}: cannot read as UTF-8: {exc}")
        return None


def _validate_html_artifact(path: Path, failures: list[str]) -> None:
    html = _read_html(path, failures)
    if html is None:
        return
    for pattern in FORBIDDEN_HTML_PATTERNS:
        if pattern in html:
            failures.append(f"{path}: contains forbidden pattern {pattern!r}")
    for marker in REQUIRED_HTML_MARKERS:
        if marker not in html:
            failures.append(f"{path}: missing required marker {marker!r}")


def check_readiness() -> list[str]:
    failures: list[str] = []
    for path, required_fields in JSON_REQUIRED_FIELDS.items():
        _validate_json_artifact(path, required_fields, failures)
    for path in HTML_ARTIFACTS:
        _validate_html_artifact(path, failures)
    return failures


def main() -> int:
    failures = check_readiness()
    if failures:
        print("Readiness check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Readiness check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
