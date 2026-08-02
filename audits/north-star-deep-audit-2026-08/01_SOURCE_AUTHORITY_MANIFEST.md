# North Star Deep Audit — Source Authority Manifest

**Baseline:** all reads in this audit are `git show
fdeef90b0a0e0747d1bbf92385d3750b4024f4ae:<path>`. No Luna, Fable, or Sol
invocation reads the live working tree (see Charter §2).

This manifest is the contract every Luna dispatch depends on. No domain
re-derives a source another domain owns (Global Constraint #5) — where two
domains touch the same source, exactly one is the owning domain here; all
others cite it.

## Owning / citing table

| Source | Owning domain | Cited by |
|---|---|---|
| `CLAUDE.md` (whole) | A | all |
| `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` | A | - |
| `docs/DECISIONS.md` (incl. the 2026-07-25 GOV-1 ruling, lines 212-271, and the GOV-0 references) | A | B |
| `docs/sidecar_doctrine.md`, `docs/architecture.md`, `docs/AGENT_WORKFLOW.md`, `docs/CLAUDE_HOOKS.md`, `docs/PRD_PROCESS.md` | A | - |
| `.claude/settings.json` + `.claude/settings.local.json` (union of both) | A | - |
| `docs/PRD_TEMPLATE.md`, `docs/PRD_REVIEW_TEMPLATE.md`, `VISION.md` | A | - |
| Master Ledger sec 1, 2, 7, 9, 10 | A | - |
| Program sec 1, 9, 10, 11 | A | - |
| `docs/PROJECT_STATE.md` | B | C |
| `docs/PRD_REGISTRY.md`, `docs/prd_index.json` | B | all (PRD-number lookups only) |
| Master Ledger sec 3, 4, 6, 8 | B | - |
| Program sec 2, 3, 4, 6, 7 (sec 2/3 baseline+source-map are this manifest's own basis) | B | all |
| `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md` (all 47 CB definitions) | C | E, F |
| `audits/current-state-reconciliation-2026-07-30/EVIDENCE_INDEX.md`, `RECONCILIATION_REPORT.md` | C | - |
| Master Ledger sec 5 | C | - |
| Program sec 5, 8, 12 | C | - |
| `cuttingboard/delivery/dashboard_renderer.py`, `cuttingboard/market_map.py`, `cuttingboard/market_map_lifecycle.py` | D1 | - |
| `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md` | D1 | E |
| North Star NS-2E / Market Control Card sections (Ledger sec 4, Program NS-2A/B/C/E rows) | D2 | - |
| `docs/prd_history/PRD-271.md` | E | D2 (dependency-chain cite only) |
| `audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md` | E | - |
| `audits/stage0-recon-2026-07-20/stage0-02-evaluation-v0.1.md`, `stage0-03-scheduler-v0.1.md` (+ their verify-02/verify-03 companions) | F | - |
| `docs/plans/decision-support-expansion-doctrine-v0.1.md`, `docs/plans/decision-support-workplan-v0.1.md` | G | - |
| PR #187 mechanical provenance (merge SHA, file list, body, connector threads) | scaffold (Charter §5) | A, H-folded |

**Verification performed:** every file/section named above traces to a row
in this table; no source appears as OWNED in two rows.

## Per-domain dispatch parameters

Each block below is the exact `{owned_sources}` / `{cited_sources}` /
`{excluded_items}` triple for that domain's Luna dispatch (execution plan
Task 1.2 template).

### Domain A — Governance, authority, materiality
- OWNED: every "A"-owned row above.
- CITED: none required beyond its own owned set.
- EXCLUDED BY DEFAULT: none — broadest domain by design.

### Domain B — Portfolio, lifecycle, PRD/current-state truth
- OWNED: every "B"-owned row above.
- CITED: `docs/DECISIONS.md` (lifecycle rulings only, cite not re-derive).
- EXCLUDED BY DEFAULT: full PRD-by-PRD re-audit of `docs/prd_history/` (417
  files) — cite only rows the Program/Ledger docs already reference.

### Domain C — Findings, parked debt, queues, completeness
- OWNED: every "C"-owned row above.
- CITED: none beyond its own owned set.
- EXCLUDED BY DEFAULT: "PRD-255 follow-ons" — dropped from scope (zero
  grounding found in either North Star anchor doc). If independently
  surfaced with a real connection, log as an amendment, don't chase it.

### Domain D1 — Product surfaces, as-built
- OWNED: `cuttingboard/delivery/dashboard_renderer.py`,
  `cuttingboard/market_map.py`, `cuttingboard/market_map_lifecycle.py`,
  `stage0-01-decision-surface-v0.1.md`.
- CITED: Program sec 3 row for candidate card / Market Map.
- EXCLUDED BY DEFAULT: broader `cuttingboard/` traversal beyond the 3 named
  files — log as amendment if verifying "actual implementation seams"
  needs more.
- Methodology: fact-check against real code.

### Domain D2 — Product surfaces, proposed
- OWNED: North Star NS-2E / Market Control Card sections.
- CITED: `docs/prd_history/PRD-271.md` (dependency-chain only).
- EXCLUDED BY DEFAULT: none beyond its methodology framing.
- Methodology: plan-consistency check only (does the North Star doc's own
  NS-2E description match its own stated dependency/unbuilt status) —
  never a fact-check, since nothing is built.

### Domain E — SPY observation, candidate fidelity, ORB
- OWNED: `docs/prd_history/PRD-271.md`,
  `STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md`.
- CITED: `stage0-01-decision-surface-v0.1.md` (from D1); CB-07 row in
  `FINDING_STATUS_MATRIX.md` (from C).
- EXCLUDED BY DEFAULT: general VWAP semantics (the 41-file scattered
  corpus, confirmed unrelated to the fidelity-delta doc). VWAP evidence
  directly tied to PRD-271/CB-07 may be cited; a general VWAP sweep may
  not — log as amendment if the ORB/fidelity evidence turns out to need it.

### Domain F — Data contracts, freshness, scheduling
- OWNED: `stage0-02-evaluation-v0.1.md`, `stage0-03-scheduler-v0.1.md` (+
  verify companions).
- CITED: Program sec 5 rows for CB-06/CB-18; Master Ledger NS-8A
  cohort-capture entry.
- EXCLUDED BY DEFAULT: an independent freshness/STAY_FLAT sweep across the
  full 79/70-file scattered corpus.
- Methodology: reconciliation against the already-cited stage0 recon (SHA
  `771f730`), not independent re-derivation.

### Domain G — Expansion vocabulary reconciliation
- OWNED: `decision-support-expansion-doctrine-v0.1.md`,
  `decision-support-workplan-v0.1.md`.
- CITED: North Star docs' expansion-vocabulary mentions (Opportunity Set
  Engine, idiosyncratic decoupling, relationship-aware news, universe
  registry, heatmap) — cited as the terms being checked, not as a source
  of truth.
- EXCLUDED BY DEFAULT: none — surfacing the vocabulary gap is this
  domain's job, not something to avoid.
- Methodology: for each North-Star-only term, confirm/deny a doctrine
  anchor exists; where none exists, record `assertion_type:
  FUTURE-DESIGN-INTENT` or `OWNER-DECISION` with `Dustin ruling required?
  = yes` — not a MISMATCH.
