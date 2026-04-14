"""Automatic ORB 0DTE shadow collection.

Purpose:
- Run the ORB engine once per session in read-only shadow mode.
- Persist one append-only JSONL ledger record per PT session.
- Persist one compact daily operational status record per PT session.
- Degrade missing or malformed inputs into auditable records without affecting
  the main runtime.

Inputs:
- `maybe_collect_orb_shadow()` accepts runtime mode, PT session date, runtime
  timestamp, and an optional explicit ORB `SessionInput`.
- `collect_orb_shadow_operational_status()` accepts the same inputs and returns
  both the observation payload and the compact operational status payload.
- When no explicit session is provided, this module looks for a serialized ORB
  session fixture at `data/orb_0dte_sessions/YYYY-MM-DD.json`.

Outputs:
- Observation mapping suitable for the existing debug or report surface and run
  summary.
- Durable append-only JSONL ledger at `data/orb_0dte_ledger.jsonl`.
- Compact daily status JSON at `data/orb_0dte_status/YYYY-MM-DD.json`.

Constraints:
- Observational artifact collection only.
- Eligible only in supported runtime modes and only after the PT post-session window for live runs.
- Must not feed back into core qualification or execution behavior.

What this module does not do:
- It does not modify ORB rules.
- It does not place trades or alter the main execution path.
- It does not promote ORB observations into the qualification layer.

Read-only status:
- Read-only with respect to trading behavior. It may write observational
  artifacts, but it does not change macro, qualification, or execution logic.
- This module is read-only and does not execute trades.

Deterministic assumptions:
- PT is the only exposed timezone in ledger output.
- Automatic collection is eligible only on Monday-Friday sessions.
- Live-mode collection runs only after `13:00 PT`.
- Duplicate session writes are suppressed by session date so the ledger grows
  by at most one record per PT session.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from cuttingboard import config
from cuttingboard.orb_0dte import CASH_SESSION_END_PT, PT, SessionInput
from cuttingboard.orb_observation import build_orb_observation
from cuttingboard.orb_replay import load_orb_session_fixture


ORB_SHADOW_LEDGER_PATH = Path("data/orb_0dte_ledger.jsonl")
ORB_SHADOW_SESSION_INPUT_DIR = Path("data/orb_0dte_sessions")
ORB_SHADOW_STATUS_DIR = Path("data/orb_0dte_status")

OBSERVATION_OK = "OK"
OBSERVATION_DATA_INVALID = "DATA_INVALID"
OBSERVATION_SESSION_INVALID = "SESSION_INVALID"
OBSERVATION_INTERNAL_ERROR = "INTERNAL_ERROR"
OBSERVATION_NOOP_DISABLED = "NOOP_DISABLED"
OBSERVATION_NOOP_UNSUPPORTED_MODE = "NOOP_UNSUPPORTED_MODE"
OBSERVATION_NOOP_WAITING_FOR_WINDOW = "NOOP_WAITING_FOR_WINDOW"

_SHADOW_REQUIRED_SYMBOLS = ("SPY", "QQQ")
_PT_LABEL = "PT"


def maybe_collect_orb_shadow(
    *,
    mode: str,
    run_date: date,
    run_at_utc: datetime,
    explicit_session_input: SessionInput | None = None,
) -> dict[str, Any] | None:
    observation, _ = collect_orb_shadow_operational_status(
        mode=mode,
        run_date=run_date,
        run_at_utc=run_at_utc,
        explicit_session_input=explicit_session_input,
    )
    return observation


def collect_orb_shadow_operational_status(
    *,
    mode: str,
    run_date: date,
    run_at_utc: datetime,
    explicit_session_input: SessionInput | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if not config.ORB_SHADOW_ENABLED:
        return None, _build_health_status(
            session_date=run_date.isoformat(),
            orb_shadow_enabled=False,
            run_attempted=False,
            ledger_write_success=False,
            observation_status=OBSERVATION_NOOP_DISABLED,
            selected_symbol=None,
            exit_cause=None,
        )
    if mode not in {"live", "fixture"}:
        return None, _build_health_status(
            session_date=run_date.isoformat(),
            orb_shadow_enabled=True,
            run_attempted=False,
            ledger_write_success=False,
            observation_status=OBSERVATION_NOOP_UNSUPPORTED_MODE,
            selected_symbol=None,
            exit_cause=None,
        )
    if mode == "live" and not _is_live_collection_window(run_date, run_at_utc):
        return None, _build_health_status(
            session_date=run_date.isoformat(),
            orb_shadow_enabled=True,
            run_attempted=False,
            ledger_write_success=False,
            observation_status=OBSERVATION_NOOP_WAITING_FOR_WINDOW,
            selected_symbol=None,
            exit_cause=None,
        )

    existing_record = _load_ledger_session(run_date, ORB_SHADOW_LEDGER_PATH)
    if existing_record is not None:
        return existing_record, _status_from_observation(
            existing_record,
            orb_shadow_enabled=True,
            run_attempted=True,
            ledger_write_success=True,
        )

    observation = _build_shadow_observation(
        run_date=run_date,
        session_input=explicit_session_input or collect_orb_shadow_session_input(run_date),
    )
    append_orb_shadow_ledger_record(ORB_SHADOW_LEDGER_PATH, observation)
    return observation, _status_from_observation(
        observation,
        orb_shadow_enabled=True,
        run_attempted=True,
        ledger_write_success=True,
    )


def collect_orb_shadow_session_input(run_date: date) -> SessionInput | None:
    path = ORB_SHADOW_SESSION_INPUT_DIR / f"{run_date.isoformat()}.json"
    if not path.exists():
        return None
    return load_orb_session_fixture(str(path))


def append_orb_shadow_ledger_record(path: Path, record: dict[str, Any]) -> None:
    payload = (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)


def write_orb_shadow_status_record(path: Path, status: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_shadow_observation(
    *,
    run_date: date,
    session_input: SessionInput | None,
) -> dict[str, Any]:
    if session_input is None:
        return _failure_observation(
            run_date=run_date,
            status=OBSERVATION_DATA_INVALID,
            audit_reason="DATA_INVALID:SESSION_INPUT_UNAVAILABLE",
        )
    invalid_reason = _validate_session_input(session_input)
    if invalid_reason is not None:
        return _failure_observation(
            run_date=run_date,
            status=OBSERVATION_DATA_INVALID,
            audit_reason=invalid_reason,
        )

    try:
        observation = build_orb_observation(session_input)
    except ValueError as exc:
        return _failure_observation(
            run_date=run_date,
            status=OBSERVATION_DATA_INVALID,
            audit_reason=f"DATA_INVALID:{exc}",
        )
    except Exception as exc:
        return _failure_observation(
            run_date=run_date,
            status=OBSERVATION_INTERNAL_ERROR,
            audit_reason=f"INTERNAL_ERROR:{exc}",
        )

    if observation.get("fail_reason") == "DATA_INVALID":
        observation_status = OBSERVATION_DATA_INVALID
    else:
        observation_status = OBSERVATION_OK

    return {
        "session_date": run_date.isoformat(),
        "timezone": _PT_LABEL,
        **observation,
        "observation_status": observation_status,
    }


def _failure_observation(
    *,
    run_date: date,
    status: str,
    audit_reason: str,
) -> dict[str, Any]:
    return {
        "session_date": run_date.isoformat(),
        "timezone": _PT_LABEL,
        "MODE": "DISABLED",
        "BIAS": "NONE",
        "EXECUTION_READY": False,
        "qualification_audit": [audit_reason],
        "exit_audit": [],
        "exit_cause": None,
        "selected_symbol": None,
        "selected_contract_summary": None,
        "OR_high": None,
        "OR_low": None,
        "OR_range": None,
        "OR_range_percent": None,
        "fail_reason": audit_reason.split(":", 1)[-1],
        "observation_status": status,
    }


def _build_health_status(
    *,
    session_date: str,
    orb_shadow_enabled: bool,
    run_attempted: bool,
    ledger_write_success: bool,
    observation_status: str,
    selected_symbol: str | None,
    exit_cause: str | None,
) -> dict[str, Any]:
    return {
        "session_date": session_date,
        "orb_shadow_enabled": orb_shadow_enabled,
        "run_attempted": run_attempted,
        "ledger_write_success": ledger_write_success,
        "observation_status": observation_status,
        "selected_symbol": selected_symbol,
        "exit_cause": exit_cause,
    }


def _status_from_observation(
    observation: dict[str, Any],
    *,
    orb_shadow_enabled: bool,
    run_attempted: bool,
    ledger_write_success: bool,
) -> dict[str, Any]:
    return _build_health_status(
        session_date=str(observation.get("session_date")),
        orb_shadow_enabled=orb_shadow_enabled,
        run_attempted=run_attempted,
        ledger_write_success=ledger_write_success,
        observation_status=str(observation.get("observation_status") or OBSERVATION_INTERNAL_ERROR),
        selected_symbol=_optional_string(observation.get("selected_symbol")),
        exit_cause=_optional_string(observation.get("exit_cause")),
    )


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _validate_session_input(session_input: SessionInput) -> str | None:
    for symbol in _SHADOW_REQUIRED_SYMBOLS:
        candles = session_input.candles.get(symbol)
        if not candles:
            return f"DATA_INVALID:{symbol}_CANDLES_MISSING"
        snapshots = session_input.option_snapshots.get(symbol)
        if snapshots is None:
            return f"DATA_INVALID:{symbol}_OPTION_SNAPSHOTS_MISSING"
    return None


def _is_live_collection_window(run_date: date, run_at_utc: datetime) -> bool:
    if run_date.weekday() >= 5:
        return False
    return run_at_utc.astimezone(PT).time() >= CASH_SESSION_END_PT


def _ledger_has_session(run_date: date, path: Path) -> bool:
    return _load_ledger_session(run_date, path) is not None


def _load_ledger_session(run_date: date, path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    session_date = run_date.isoformat()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("session_date") == session_date:
                return payload
    return None
