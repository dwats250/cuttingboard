# Cuttingboard

Cuttingboard is a deterministic trade qualification engine. Its purpose is to scan market conditions and surface only structurally valid trades under explicit rules, with selectivity favored over activity.

## Project Overview

The repository currently has two tracks:

- Core engine under development: the future primary path that ingests data, validates it, classifies structure, qualifies setups, maps options expressions, and emits reports and summaries.
- ORB 0DTE Shadow Observer: the current deterministic read-only observational layer that runs after the PT cash session and persists daily artifacts for review.

`python -m cuttingboard` is the public entrypoint for `live`, `fixture`, `sunday`, and `verify` modes.

## System Philosophy

- Selectivity over frequency
- Deterministic rules over discretion
- Flat is a valid position
- No trade unless conditions are clearly favorable

## Current Focus

- Intraday 0DTE options
- SPY and QQQ
- ORB momentum-based qualification

## Future Direction

The longer-term direction is broader instrument coverage under the same qualification discipline:

- metals
- macro-driven trades
- liquid options strategies

Expansion does not change the operating principle: no trade should be surfaced unless it passes clear deterministic qualification logic.

## Current Modules

- Core engine modules
  - `runtime.py`
  - `ingestion.py`
  - `normalization.py`
  - `validation.py`
  - `derived.py`
  - `regime.py`
  - `structure.py`
  - `qualification.py`
  - `options.py`
  - `output/*`
  - `audit.py`
- ORB 0DTE Shadow Observer
  - `orb_0dte.py`
  - `orb_observation.py`
  - `orb_replay.py`
  - `orb_shadow.py`

## Status

- ORB module: observational and pre-beta
- Core engine: under development

## High-Level Pipeline

```text
L1  Ingestion       -> RawQuote per symbol
L2  Normalization   -> NormalizedQuote
L3  Validation      -> ValidationSummary
L4  Derived         -> EMA, ATR, momentum, volume metrics
L5  Regime          -> market state and posture
L6  Structure       -> symbol structure + IV environment
L7  Qualification   -> qualified / watchlist / reject
L8  Options         -> options expression mapping
L9  Output          -> terminal, markdown, ntfy
L10 Audit           -> append-only audit log
ORB Shadow          -> read-only ORB observation + ledger + daily status
```

## ORB Shadow Mode

The ORB shadow system is a read-only observer. It evaluates an ORB 0DTE session, records what the model would have selected, and writes durable artifacts for operational review.

What it does:

- Runs after the PT session window when shadow collection is eligible.
- Builds an ORB observation payload from session candles and option snapshots.
- Writes one append-only ledger record per PT session.
- Writes one compact daily operational status record per PT session.
- Surfaces compact status in the markdown report and JSON summary.

What it does not do:

- It does not place trades.
- It does not alter qualification or option-selection behavior in the main runtime.
- It does not change execution logic.

When it runs:

- Automatic shadow collection is gated by `config.ORB_SHADOW_ENABLED`.
- Live-mode collection is eligible only after `13:00 PT`.
- Fixture-mode collection can be exercised deterministically in tests.

Where outputs are written:

- Ledger: `data/orb_0dte_ledger.jsonl`
- Daily status: `data/orb_0dte_status/YYYY-MM-DD.json`
- Human-readable report block: `reports/YYYY-MM-DD.md`

## ORB Shadow Artifacts

Ledger records are JSONL objects containing ORB observation fields, including:

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
- `observation_status`

Daily status files are compact JSON objects containing:

- `session_date`
- `orb_shadow_enabled`
- `run_attempted`
- `ledger_write_success`
- `observation_status`
- `selected_symbol`
- `exit_cause`

Meaning of core fields:

- `MODE`: whether the ORB engine ended in an enabled or disabled state for that session.
- `BIAS`: directional bias produced by the ORB model, or `NONE`.
- `EXECUTION_READY`: whether the ORB model reached deterministic readiness for entry.
- `qualification_audit`: compact audit trail for why the model qualified, degraded, or failed.
- `exit_audit`: compact audit trail for how management and exits unfolded.
- `exit_cause`: terminal exit reason such as `TP2`, `HEADLINE`, `STOP`, or `NONE`.
- `observation_status`: operational interpretation of the record, such as `OK`, `DATA_INVALID`, or a no-op status.

## Setup

```bash
pip install -e .
cp .env.example .env
```

Populate `.env` with the required external configuration such as `POLYGON_API_KEY`, `NTFY_TOPIC`, and `NTFY_URL` if those integrations are used.

## Usage

Run the main system:

```bash
python -m cuttingboard
python -m cuttingboard --mode fixture --fixture-file tests/fixtures/2026-04-12.json
python -m cuttingboard --mode verify
```

Enable ORB shadow collection:

```python
# cuttingboard/config.py
ORB_SHADOW_ENABLED = True
```

Run tests:

```bash
python3 -m pytest tests/test_orb_shadow_collection.py -q
python3 -m pytest tests/test_orb_observational_replay.py -q
python3 -m pytest tests/test_operationalization.py -q
```

No full test suite is required for documentation-only changes. If code behavior is touched, rerun only the targeted tests that cover that area.

## Branch and Workflow Rules

- Branch naming: `feature/<clear-scope>`
- One feature per branch
- No mixed-scope development
- One milestone per commit
- No bundling unrelated changes
- Preferred workflow: `PRD -> Codex -> summary -> validation -> commit`

The intent is low ambiguity. Each branch should carry one scoped change set, and each commit should mark a meaningful checkpoint that can be reviewed independently.

## Docs

- `docs/system_map.md` — high-level architecture, module boundaries, read-only vs active paths
- `docs/roadmap_beta.md` — ORB shadow beta phase definition and exit criteria
- `docs/orb_shadow_artifacts.md` — ledger and status file semantics
- `docs/architecture.md` — full layer diagram and data contracts
- `docs/regime_model.md` — vote thresholds and posture rules
- `docs/trade_qualification.md` — qualification gates
- `docs/options_framework.md` — options expression mapping
- `docs/runbook.md` — operational procedures
- `docs/data_sources.md` — data source and fallback details
