"""Read-only ORB 0DTE observation helpers.

Purpose:
- Evaluate `cuttingboard.orb_0dte` from one supplied session input.
- Convert the resulting `SessionResult` into compact observation and report
  surfaces suitable for shadow review.

Inputs:
- `build_orb_observation(session)` accepts one ORB `SessionInput`.
- `format_orb_observation_lines(observation)` accepts the observation mapping
  produced by `build_orb_observation()`.
- `format_orb_shadow_health_lines(status)` accepts the compact operational
  status mapping emitted by the ORB shadow collector.

Outputs:
- Observation mapping with `MODE`, `BIAS`, `EXECUTION_READY`,
  `qualification_audit`, `exit_audit`, `exit_cause`, `selected_symbol`, and
  `selected_contract_summary`, plus opening-range metrics for audit or ledger
  use.
- PT-consistent report lines suitable for markdown or debug surfaces.

Constraints:
- Observation and formatting only.
- Expects a valid caller-supplied ORB session input or observation payload.
- Does not own scheduling, persistence, or runtime control.

What this module does not do:
- It does not fetch session data.
- It does not write ledger files or status records.
- It does not change qualification, execution, or option-selection flow.

Read-only status:
- Fully read-only. It derives display and observation payloads from supplied
  data and returns them to callers.
- This module is read-only and does not execute trades.

Feature-flag usage:
- Used only when runtime shadow mode is explicitly enabled with
  `observe_orb_0dte=True` or CLI flag `--observe-orb-0dte` together with an
  ORB session fixture file.

This module keeps ORB replay and report-surface logic isolated from the main
runtime.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from cuttingboard.orb_0dte import SessionInput, evaluate_orb_0dte_session


_AUDIT_PREVIEW_ITEMS = 3
_DISPLAY_MAX_LEN = 96


def build_orb_observation(session: SessionInput) -> dict[str, Any]:
    result = evaluate_orb_0dte_session(session)
    selected_contract_summary = None
    if result.entry is not None:
        selected_contract_summary = (
            f"{result.entry.contract_id} | strike={result.entry.strike:.2f} | "
            f"delta={result.entry.delta:.2f} | premium={result.entry.premium:.2f}"
        )
    opening_range = result.opening_range

    return {
        "MODE": result.mode,
        "BIAS": result.bias,
        "EXECUTION_READY": result.execution_ready,
        "qualification_audit": list(result.qualification_audit),
        "exit_audit": list(result.exit_audit),
        "exit_cause": result.exit_cause,
        "selected_symbol": result.entry.symbol if result.entry is not None else None,
        "selected_contract_summary": selected_contract_summary,
        "OR_high": opening_range.high if opening_range is not None else None,
        "OR_low": opening_range.low if opening_range is not None else None,
        "OR_range": opening_range.range_points if opening_range is not None else None,
        "OR_range_percent": opening_range.range_percent if opening_range is not None else None,
        "fail_reason": result.fail_reason,
    }


def format_orb_observation_lines(observation: Mapping[str, object]) -> list[str]:
    qualification = _bounded_display_text(_compact_audit_preview(observation["qualification_audit"]))
    exit_value = _format_exit_line(observation)
    return [
        "  ORB 0DTE OBSERVATION",
        "  " + "─" * 50,
        f"  MODE              {observation['MODE']}",
        f"  BIAS              {observation['BIAS']}",
        f"  EXECUTION_READY   {observation['EXECUTION_READY']}",
        f"  SYMBOL            {observation['selected_symbol'] or 'NONE'}",
        "  CONTRACT          "
        f"{_bounded_display_text(str(observation['selected_contract_summary'] or 'NONE'))}",
        f"  QUALIFICATION     {qualification}",
        f"  EXIT              {exit_value}",
        "",
    ]


def format_orb_shadow_health_lines(status: Mapping[str, object]) -> list[str]:
    return [
        "  ORB SHADOW HEALTH",
        "  " + "─" * 50,
        f"  session_date        {_display_status_value(status.get('session_date'))}",
        f"  orb_shadow_enabled  {_display_status_value(status.get('orb_shadow_enabled'))}",
        f"  run_attempted       {_display_status_value(status.get('run_attempted'))}",
        f"  ledger_write_success {_display_status_value(status.get('ledger_write_success'))}",
        f"  observation_status  {_display_status_value(status.get('observation_status'))}",
        f"  selected_symbol     {_display_status_value(status.get('selected_symbol'))}",
        f"  exit_cause          {_display_status_value(status.get('exit_cause'))}",
        "",
    ]


def _compact_audit_preview(values: object) -> str:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return "[]"
    items = [str(item) for item in values]
    if not items:
        return "[]"
    preview = items[:_AUDIT_PREVIEW_ITEMS]
    if len(items) > _AUDIT_PREVIEW_ITEMS:
        preview.append(f"+{len(items) - _AUDIT_PREVIEW_ITEMS} more")
    return ", ".join(preview)


def _bounded_display_text(value: str) -> str:
    if len(value) <= _DISPLAY_MAX_LEN:
        return value
    return value[: _DISPLAY_MAX_LEN - 3] + "..."


def _format_exit_line(observation: Mapping[str, object]) -> str:
    cause = str(observation.get("exit_cause") or "NONE")
    audit = _compact_audit_preview(observation.get("exit_audit"))
    if audit == "[]":
        return cause
    return _bounded_display_text(f"{cause} | {audit}")


def _display_status_value(value: object) -> str:
    if value is None:
        return "NONE"
    return _bounded_display_text(str(value))
