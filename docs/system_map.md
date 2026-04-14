# System Map

## Purpose

This document is the high-level map of Cuttingboard as it exists in the current pre-beta state. It is intended to make module boundaries, artifact flow, and read-only versus active behavior explicit without requiring code inspection first.

## Architecture Summary

Cuttingboard currently contains two adjacent systems:

- Core engine under development: the future primary runtime path that ingests market data, validates it, classifies structure, qualifies setups, and emits reports and summaries.
- Read-only ORB shadow system: the current ORB 0DTE observational layer that runs alongside the runtime but does not alter trading logic.

## High-Level Flow

```text
python -m cuttingboard
  -> runtime.py
  -> ingestion / normalization / validation
  -> derived / regime / structure / qualification / options
  -> output report + run summary + audit
  -> ORB shadow collection
     -> orb_shadow.py
     -> orb_observation.py
     -> data/orb_0dte_ledger.jsonl
     -> data/orb_0dte_status/YYYY-MM-DD.json
     -> reports/YYYY-MM-DD.md
```

## ORB Shadow Data Flow

```text
runtime.py
  -> collect_orb_shadow_operational_status(...)
  -> orb_shadow.py loads session input
  -> orb_observation.py builds observation payload
  -> orb_shadow.py appends ledger record
  -> orb_shadow.py writes compact daily status
  -> runtime summary includes compact status
  -> report renders ORB observation and ORB shadow health blocks
```

Required path:

- `runtime -> ORB shadow -> ledger -> report`

That path is additive only. It does not feed back into the core qualification path.

## Module Boundaries

### Core engine modules

- `cuttingboard/runtime.py`
  - Public orchestration layer
  - Writes run summaries and markdown reports
- `cuttingboard/ingestion.py`
  - Live and fixture data ingestion
- `cuttingboard/normalization.py`
  - Quote normalization and timestamp normalization
- `cuttingboard/validation.py`
  - Data-quality gates and halt behavior
- `cuttingboard/derived.py`
  - Derived technical metrics
- `cuttingboard/regime.py`
  - Regime and posture determination
- `cuttingboard/structure.py`
  - Structure classification
- `cuttingboard/qualification.py`
  - Main qualification gating
- `cuttingboard/options.py`
  - Options expression mapping
- `cuttingboard/output/*`
  - Report and notification surfaces
- `cuttingboard/audit.py`
  - Append-only audit log

### Observational modules

- `cuttingboard/orb_0dte.py`
  - Deterministic ORB engine
  - Computes session result only
- `cuttingboard/orb_observation.py`
  - Converts ORB session result into observation and display payloads
- `cuttingboard/orb_replay.py`
  - Loads ORB fixture files and runs replay review
- `cuttingboard/orb_shadow.py`
  - Coordinates post-session shadow collection and observational artifacts

## Read-Only vs Active

### Core engine path

- Regime and posture
- Qualification outcomes
- Options expression mapping
- Runtime summary generation
- Audit logging
- External alerting

### Observational path

- ORB replay
- ORB observation formatting
- ORB shadow ledger generation
- ORB daily status generation

Read-only here means the subsystem may write observational artifacts, but it must not change the active trade decision path.

## Artifact Map

### Main runtime artifacts

- `reports/YYYY-MM-DD.md`
- `logs/run_YYYY-MM-DD_HHMMSS.json`
- `logs/latest_run.json`
- `logs/audit.jsonl`

### ORB shadow artifacts

- `data/orb_0dte_ledger.jsonl`
- `data/orb_0dte_status/YYYY-MM-DD.json`

## Stability Labels

- Stable:
  - Runtime artifact flow
  - Report and summary generation
  - Audit output
- Experimental:
  - ORB 0DTE shadow observer
  - ORB replay review flow
  - ORB operational health reporting

## Design Rule

The ORB shadow system is intentionally isolated. It may observe, record, and summarize. It may not alter trade qualification, execution behavior, or the core ORB rule set during this documentation phase.
