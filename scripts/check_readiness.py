#!/usr/bin/env python3
"""Validate scheduled dashboard artifacts before publishing them."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# PRD-287: canonical health vocabularies from their source of truth (public
# package surfaces), never duplicated literals. The hourly workflow runs
# `pip install -e .` before this script, so the import resolves.
from cuttingboard.output import OUTCOME_HALT, OUTCOME_NO_TRADE, OUTCOME_TRADE
from cuttingboard.runtime import SUMMARY_STATUS_FAIL, SUMMARY_STATUS_SUCCESS


ROOT = Path(__file__).resolve().parents[1]

# PRD-287: the authoritative hourly run-health artifact.
HOURLY_RUN_PATH = Path("logs/latest_hourly_run.json")

_VALID_RUN_STATUS = frozenset({SUMMARY_STATUS_SUCCESS, SUMMARY_STATUS_FAIL})
_VALID_RUN_OUTCOME = frozenset({OUTCOME_TRADE, OUTCOME_NO_TRADE, OUTCOME_HALT})

JSON_REQUIRED_FIELDS = {
    Path("logs/latest_hourly_payload.json"): ("meta", "run_status", "schema_version", "sections"),
    # PRD-287: `errors` and `system_halted` are already emitted by
    # _build_hourly_run_summary; requiring them lets readiness judge run HEALTH,
    # not merely key presence.
    HOURLY_RUN_PATH: ("status", "outcome", "errors", "system_halted"),
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
)

# PRD-297: the morning executor's run-health artifact carries the same
# status/outcome/errors/system_halted schema and vocabulary as the hourly run
# artifact, so the morning profile reuses the identical run-health checks. The
# HTML artifacts + markers are shared (one renderer produces both boards).
MORNING_RUN_PATH = Path("logs/latest_run.json")
_MORNING_JSON_REQUIRED_FIELDS = {
    MORNING_RUN_PATH: ("status", "outcome", "errors", "system_halted"),
}
# Default run-health trigger set = today's hourly behavior (the flagless path).
_DEFAULT_RUN_HEALTH_PATHS = frozenset({HOURLY_RUN_PATH})


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


def _validate_hourly_run_health(path: Path, data: dict[str, Any], failures: list[str]) -> None:
    """PRD-287: judge the hourly run artifact's HEALTH, not just key presence.

    Rejects an in-run system failure (status=FAIL + non-empty errors) and a
    data-integrity VALIDATION halt (system_halted=True + status=SUCCESS); passes
    healthy TRADE/NO_TRADE and the market-stress safety HALT (status=FAIL,
    errors=[], system_halted=True); fails loud on malformed values. Caller
    guarantees the four required fields are present.
    """
    status, outcome = data.get("status"), data.get("outcome")
    errors, system_halted = data.get("errors"), data.get("system_halted")

    if status not in _VALID_RUN_STATUS:
        failures.append(f"{path}: status {status!r} not one of {sorted(_VALID_RUN_STATUS)}")
    if outcome not in _VALID_RUN_OUTCOME:
        failures.append(f"{path}: outcome {outcome!r} not one of {sorted(_VALID_RUN_OUTCOME)}")
    if not isinstance(errors, list):
        failures.append(f"{path}: errors must be a list, got {type(errors).__name__}")
    if not isinstance(system_halted, bool):
        failures.append(f"{path}: system_halted must be a bool, got {type(system_halted).__name__}")

    if isinstance(errors, list) and status == SUMMARY_STATUS_FAIL and errors:
        failures.append(f"{path}: unhealthy run — status=FAIL with errors {errors!r} (in-run system failure)")
    if isinstance(system_halted, bool) and system_halted and status == SUMMARY_STATUS_SUCCESS:
        failures.append(f"{path}: unhealthy run — system_halted=True with status=SUCCESS (data-integrity validation halt)")


def _validate_json_artifact(
    path: Path,
    required_fields: tuple[str, ...],
    failures: list[str],
    run_health_paths: frozenset[Path] = _DEFAULT_RUN_HEALTH_PATHS,
) -> None:
    data = _load_json(path, failures)
    if data is None:
        return
    missing = [field for field in required_fields if field not in data]
    for field in missing:
        failures.append(f"{path}: missing required field {field!r}")
    # PRD-287: judge run HEALTH only when every required field is present, so a
    # missing-key failure is not double-reported as a malformed-value failure.
    # PRD-297: the run-health trigger is a caller-supplied set (default = the
    # hourly artifact) so the morning profile applies the identical checks to
    # logs/latest_run.json.
    if path in run_health_paths and not missing:
        _validate_hourly_run_health(path, data, failures)


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


def check_readiness(
    json_required: dict[Path, tuple[str, ...]] = JSON_REQUIRED_FIELDS,
    html_artifacts: tuple[Path, ...] = HTML_ARTIFACTS,
    run_health_paths: frozenset[Path] = _DEFAULT_RUN_HEALTH_PATHS,
) -> list[str]:
    failures: list[str] = []
    for path, required_fields in json_required.items():
        _validate_json_artifact(path, required_fields, failures, run_health_paths)
    for path in html_artifacts:
        _validate_html_artifact(path, failures)
    return failures


# PRD-297: profiles select the artifact set. The default (flagless) invocation
# is the hourly profile - identical to pre-PRD-297 behavior byte-for-byte.
_PROFILES: dict[str, dict] = {
    "hourly": {},
    "morning": {
        "json_required": _MORNING_JSON_REQUIRED_FIELDS,
        "html_artifacts": HTML_ARTIFACTS,
        "run_health_paths": frozenset({MORNING_RUN_PATH}),
    },
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate scheduled dashboard artifacts before publishing them."
    )
    parser.add_argument(
        "--profile",
        choices=tuple(_PROFILES),
        default="hourly",
        help="artifact set to validate (default: hourly - the flagless behavior)",
    )
    args = parser.parse_args(argv)
    failures = check_readiness(**_PROFILES[args.profile])
    if failures:
        print("Readiness check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Readiness check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
