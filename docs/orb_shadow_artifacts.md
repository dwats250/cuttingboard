# ORB Shadow Artifacts

## Purpose

This document defines the durable artifacts emitted by the ORB shadow system and the meaning of the key fields. The goal is to keep artifact interpretation unambiguous.

## Artifact Locations

- Ledger: `data/orb_0dte_ledger.jsonl`
- Daily operational status: `data/orb_0dte_status/YYYY-MM-DD.json`
- Human-readable report block: `reports/YYYY-MM-DD.md`

## Ledger Format

The ledger is append-only JSONL. Each line is one PT session record.

Typical fields:

- `session_date`
- `timezone`
- `MODE`
- `BIAS`
- `EXECUTION_READY`
- `qualification_audit`
- `exit_audit`
- `exit_cause`
- `selected_symbol`
- `selected_contract_summary`
- `OR_high`
- `OR_low`
- `OR_range`
- `OR_range_percent`
- `fail_reason`
- `observation_status`

## Daily Status File Format

The daily status file is a compact JSON object intended for operational health reporting.

Required fields:

- `session_date`
- `orb_shadow_enabled`
- `run_attempted`
- `ledger_write_success`
- `observation_status`
- `selected_symbol`
- `exit_cause`

Purpose:

- Confirm whether ORB shadow collection ran for the PT session
- Confirm whether the ledger write succeeded
- Surface the compact final observation state without reading the full ledger

## Field Meanings

### `MODE`

The ORB engine state for the session result.

- `ENABLED`: the model reached an enabled state for the session.
- `DISABLED`: the model remained disabled or degraded out.

### `BIAS`

The directional orientation determined by the ORB model.

- `LONG`
- `SHORT`
- `NONE`

### `EXECUTION_READY`

Boolean readiness state from the ORB engine. It reflects whether the model reached deterministic readiness for entry under its own rules. In shadow mode this is observational only.

### `qualification_audit`

A compact list of qualification or degradation events that explain why the session qualified, failed, or degraded. This is the first place to inspect when `observation_status` is not `OK`.

### `exit_audit`

A compact list of post-entry management events. It explains what happened after entry logic became active inside the ORB model.

### `exit_cause`

The terminal exit reason from the ORB session result.

Examples:

- `TP2`
- `HEADLINE`
- `STOP`
- `STALL`
- `NONE`

### `observation_status`

Operational interpretation of the ORB shadow record.

Examples:

- `OK`: session was observed successfully
- `DATA_INVALID`: session input was missing or invalid
- `INTERNAL_ERROR`: unexpected failure while building the observation
- `NOOP_DISABLED`: ORB shadow collection was disabled
- `NOOP_UNSUPPORTED_MODE`: runtime mode was not eligible
- `NOOP_WAITING_FOR_WINDOW`: live runtime was before the post-session collection window

This is the primary compact field for determining whether a session was healthy, degraded, or intentionally skipped.

## Operational Interpretation

### Healthy session

- `orb_shadow_enabled = true`
- `run_attempted = true`
- `ledger_write_success = true`
- `observation_status = OK` or another explicit terminal state

### No-op session

- `orb_shadow_enabled = false` or collection was not yet eligible
- `run_attempted = false`
- `ledger_write_success = false`
- `observation_status` explains why collection did not run

### Failure session

- `run_attempted = true`
- `ledger_write_success = true` if a degraded record was still persisted
- `observation_status = DATA_INVALID` or `INTERNAL_ERROR`

The design goal is compact but explicit status, not silent failure.
