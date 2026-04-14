# System Map

## Purpose

This document defines the current high-level architecture of Cuttingboard as a deterministic trade qualification engine. It separates the future engine layer from the current observational ORB layer and makes the artifact flow explicit.

## Architecture

Cuttingboard currently has three layers:

1. Engine layer
   Future trade qualification logic and orchestration.
2. Observation layer
   Current ORB 0DTE shadow observer.
3. Output layer
   Durable artifacts and compact report surfaces.

## Layer Definitions

### Engine Layer

This is the future active qualification path.

- Runtime orchestration
- Data ingestion and normalization
- Validation
- Structure and qualification logic
- Audit generation

This layer is where future active trade qualification logic belongs.

### Observation Layer

This is the current operational layer.

- `cuttingboard/orb_0dte.py`
- `cuttingboard/orb_observation.py`
- `cuttingboard/orb_replay.py`
- `cuttingboard/orb_shadow.py`

The ORB layer is observational only. It evaluates session conditions, records outcomes, and writes artifacts. It does not execute trades.

### Output Layer

This layer persists and renders the current observable outputs.

- `data/orb_0dte_ledger.jsonl`
- `data/orb_0dte_status/YYYY-MM-DD.json`
- Report blocks in `reports/YYYY-MM-DD.md`

## Current Flow

```text
runtime -> orb_shadow -> ledger + status -> report
```

Expanded path:

```text
python -m cuttingboard
  -> runtime.py
  -> orb_shadow.py
  -> orb_observation.py
  -> data/orb_0dte_ledger.jsonl
  -> data/orb_0dte_status/YYYY-MM-DD.json
  -> reports/YYYY-MM-DD.md
```

This flow is additive and read-only from the perspective of trade behavior.

## Read-Only vs Active

### Read-only components

- `orb_0dte.py`
- `orb_observation.py`
- `orb_replay.py`
- `orb_shadow.py`
- ORB ledger writes
- ORB daily status writes
- ORB report blocks

These components may write observational artifacts, but they do not activate execution behavior.

### Active components

There is no active ORB execution path.

The future engine layer is where active qualification logic will live, but that is not the current operational state represented by this repository.

## Module Boundaries

### Runtime boundary

`cuttingboard/runtime.py` is the public orchestrator. It can invoke the ORB shadow observer and surface the resulting status, but the shadow path must remain isolated from live trade behavior.

### ORB shadow boundary

`cuttingboard/orb_shadow.py` coordinates collection timing, artifact writes, and compact operational status.

### Observation formatting boundary

`cuttingboard/orb_observation.py` converts ORB results into durable observation fields and compact report-ready structures.

### Replay boundary

`cuttingboard/orb_replay.py` supports deterministic review from fixtures. It is an observational tool, not an execution path.

## Design Rule

The ORB shadow module may observe, summarize, and persist. It may not alter qualification rules, execution behavior, or system trading decisions.
