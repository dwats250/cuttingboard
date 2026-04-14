# Cuttingboard

Cuttingboard is a deterministic trade qualification engine. It scans market conditions and surfaces only structurally valid trades under explicit rules. Selectivity is preferred over frequency, and remaining flat is a valid outcome.

## Project Identity

The system is built around a narrow operating standard:

- Deterministic rules over discretion
- No trade without clear structural alignment
- Outputs must be explainable through audit fields
- Structured artifacts come first, presentation comes second

The repository should reflect current truth directly. Logic should be inspectable, outputs should be reproducible, and every surfaced result should be understandable from the stored artifacts alone.

## Current Focus

Current work is centered on:

- Intraday 0DTE options
- SPY and QQQ
- ORB momentum-based qualification
- Shadow-mode observation only

## Current Module

### ORB 0DTE Shadow Observer

The ORB shadow module is the current operational subsystem in this repository.

- It is read-only.
- It runs automatically after the session close window in PT.
- It evaluates ORB trend-day conditions from collected session data.
- It produces durable daily artifacts for review.

What it produces:

- JSONL ledger
- Daily status record
- Compact observation output

What it does not do:

- It does not execute trades.
- It does not change runtime qualification behavior.
- It does not activate any live execution path.

## Outputs

### `data/orb_0dte_ledger.jsonl`

Append-only ORB shadow ledger. Each line is one PT session record containing the observed ORB result, the relevant audit fields, and the final modeled outcome.

### `data/orb_0dte_status/YYYY-MM-DD.json`

Compact daily operational status record. This file is intended to show whether shadow collection ran, whether the ledger write succeeded, and what final observation state was recorded for the session.

## Artifact Fields

Core ledger and status fields are intentionally compact:

- `MODE`: final ORB engine mode for the session, such as enabled or disabled.
- `BIAS`: directional bias selected by the ORB model, or `NONE`.
- `EXECUTION_READY`: whether the ORB model reached deterministic entry readiness. In shadow mode this is observational only.
- `qualification_audit`: compact explanation of how the session qualified, failed, or degraded.
- `exit_audit`: compact explanation of how the modeled management path unfolded.
- `exit_cause`: terminal session outcome such as `TP2`, `STOP`, `STALL`, `HEADLINE`, or `NONE`.
- `observation_status`: operational interpretation of the observed result, such as `OK`, `DATA_INVALID`, or a no-op state.

## Current Status

- ORB module: operational in shadow mode
- System phase: evidence gathering, pre-beta
- No execution logic active

## Usage

Public entrypoint:

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

Run targeted tests:

```bash
pytest -q tests/test_orb_0dte.py
pytest -q tests/test_orb_shadow_collection.py
```

## Workflow

- Branch naming: `feature/<clear-scope>`
- One feature per branch
- No mixed-scope development
- One milestone per commit
- No bundling unrelated changes
- Preferred workflow: `PRD -> Codex -> summary -> validation -> commit`

## Documentation Map

- `docs/system_map.md` — current architecture and flow boundaries
- `docs/roadmap.md` — production roadmap and phase definitions
- `docs/orb_shadow_artifacts.md` — ledger and status artifact semantics
- `docs/architecture.md` — deeper architecture notes
- `docs/trade_qualification.md` — qualification design notes
