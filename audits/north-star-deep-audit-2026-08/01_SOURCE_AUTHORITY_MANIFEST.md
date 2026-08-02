# North Star Deep Audit — Source Authority Manifest

**Baseline:** all reads in this audit are `git show
fdeef90b0a0e0747d1bbf92385d3750b4024f4ae:<path>`. No Luna, Fable, or Sol
invocation reads the live working tree (see Charter §2).

This manifest is the contract every Luna dispatch depends on. No domain
re-derives a source another domain owns (Global Constraint #5) — where two
domains touch the same source, exactly one is the owning domain here; all
others cite. Evidence `confidence` values follow Charter §7's committed
HIGH/MEDIUM/LOW definition — this manifest does not restate it.

**Excluded, not a source:** `.claude/settings.local.json` is untracked and
absent from baseline commit `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`
(confirmed via `git show fdeef90:.claude/settings.local.json`, which
errors — the path does not exist at that commit). Because every read in
this audit is pinned to that baseline, a file that never existed there
cannot be a mandatory owned source: no domain can satisfy Charter §11's
COMPLETE rule against a read that always fails. It is excluded from
baseline-owned evidence for that reason — not read, not captured from the
live working tree, not silently dropped. `.claude/settings.json` (which
does exist at baseline) remains owned by Domain A below.

## Owning / citing table

| Source | Owning domain | Cited by |
|---|---|---|
| `CLAUDE.md` (whole) | A | all |
| `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` | A | - |
| `docs/DECISIONS.md` (incl. the 2026-07-25 GOV-1 ruling, lines 212-271, and the GOV-0 references) | A | B |
| `docs/sidecar_doctrine.md`, `docs/architecture.md`, `docs/AGENT_WORKFLOW.md`, `docs/CLAUDE_HOOKS.md`, `docs/PRD_PROCESS.md` | A | - |
| `.claude/settings.json` (baseline-readable; `.claude/settings.local.json` explicitly excluded — see note above) | A | - |
| `docs/PRD_TEMPLATE.md`, `docs/PRD_REVIEW_TEMPLATE.md`, `VISION.md` | A | - |
| Master Ledger sec 1, 2, 7, 9, 10 | A | - |
| Program sec 1, 9, 10, 11 | A | - |
| `stage0-05-governance-debt-v0.1.md`, "## Governance" section only (Q27-28) | A | - |
| `docs/PROJECT_STATE.md` | B | C |
| `docs/PRD_REGISTRY.md`, `docs/prd_index.json` | B | all (PRD-number lookups only) |
| Master Ledger sec 3, 6, 8, and sec 4 EXCLUDING the NS-2 block (i.e. NS-0, NS-1, NS-3 through NS-9; lines 84-121 and 135-260) | B | D2 (cites for portfolio-state consistency checks against NS-2) |
| Program sec 2, 3, 4, 6, 7 (sec 2/3 baseline+source-map are this manifest's own basis; includes Program's NS-2-referencing rows — source map, dependency graph, NOW/NEXT/LATER sequencing — as portfolio/lifecycle facts, not product-design assertions) | B | all, D2 (dependency-chain cite for its NS-2 rows) |
| `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md` (all 47 CB definitions) | C | E, F |
| `audits/current-state-reconciliation-2026-07-30/EVIDENCE_INDEX.md`, `RECONCILIATION_REPORT.md` | C | - |
| Master Ledger sec 5 | C | - |
| Program sec 5, 8, 12 | C | - |
| `stage0-05-governance-debt-v0.1.md`, "## Existing debt and queue" section only (Q22-26) | C | - |
| `verify-05-governance-debt.md` (whole — its Q22-26 per-question disposition is the dominant content) | C | A (cites its Q27-28 per-question disposition sub-entries only) |
| `cuttingboard/delivery/dashboard_renderer.py`, `cuttingboard/market_map.py`, `cuttingboard/market_map_lifecycle.py` | D1 | - |
| `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md` | D1 | E |
| Master Ledger sec 4 NS-2 block ONLY (lines 122-134: NS-2A through NS-2F, "Fixed SPY observation and Market Control Card") | D2 | B (cites for portfolio-state consistency checks) |
| `docs/prd_history/PRD-271.md` | E | D2 (dependency-chain cite only) |
| `audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md` | E | - |
| `audits/stage0-recon-2026-07-20/stage0-02-evaluation-v0.1.md`, `stage0-03-scheduler-v0.1.md` (+ their verify-02/verify-03 companions) | F | - |
| `docs/plans/decision-support-expansion-doctrine-v0.1.md`, `docs/plans/decision-support-workplan-v0.1.md` | G | - |
| `audits/stage0-recon-2026-07-20/stage0-04-gex-v0.1.md` | G | - |
| PR #187 mechanical provenance (merge SHA, file list, body, connector threads) | scaffold (Charter §5) | A |

**Verification performed:** every file/section named above traces to
exactly one OWNED row; no source or explicit subsection is OWNED by two
domains; every "cited by" entry is carried into the citing domain's
concrete dispatch block below.

## Per-domain dispatch parameters

Each block below is the exact `{owned_sources}` / `{cited_sources}` /
`{excluded_items}` triple for that domain's Luna dispatch (execution plan
Task 1.2 template). Reconciled mechanically against the table above — every
row naming a domain as owner or citer appears in that domain's block.

### Domain A — Governance, authority, materiality
- OWNED: `CLAUDE.md`; `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md`;
  `docs/DECISIONS.md`; `docs/sidecar_doctrine.md`; `docs/architecture.md`;
  `docs/AGENT_WORKFLOW.md`; `docs/CLAUDE_HOOKS.md`; `docs/PRD_PROCESS.md`;
  `.claude/settings.json`; `docs/PRD_TEMPLATE.md`; `docs/PRD_REVIEW_TEMPLATE.md`;
  `VISION.md`; Master Ledger sec 1, 2, 7, 9, 10; Program sec 1, 9, 10, 11;
  `stage0-05-governance-debt-v0.1.md` "## Governance" section (Q27-28) only.
- CITED: `docs/PRD_REGISTRY.md` + `docs/prd_index.json` (owned by B, cited
  by all — PRD-number lookups only); Program sec 2, 3, 4, 6, 7 (owned by B,
  cited by all); `verify-05-governance-debt.md` (owned by C) — its Q27-28
  per-question disposition sub-entries only, not the whole file.
- EXCLUDED BY DEFAULT: `.claude/settings.local.json` — untracked, absent
  from baseline, not a valid pinned-commit read (see note above). No other
  exclusions — broadest domain by design.

### Domain B — Portfolio, lifecycle, PRD/current-state truth
- OWNED: `docs/PROJECT_STATE.md`; `docs/PRD_REGISTRY.md`; `docs/prd_index.json`;
  Master Ledger sec 3, 6, 8, and sec 4 excluding the NS-2 block (NS-0, NS-1,
  NS-3 through NS-9); Program sec 2, 3, 4, 6, 7.
- CITED: `CLAUDE.md` (owned by A, cited by all); `docs/DECISIONS.md` (owned
  by A — lifecycle rulings only, cite not re-derive); Master Ledger sec 4
  NS-2 block (owned by D2 — cite for portfolio-state consistency, e.g. is
  NS-2E's lifecycle tag consistent across both docs).
- EXCLUDED BY DEFAULT: full PRD-by-PRD re-audit of `docs/prd_history/` (417
  files) — cite only rows the Program/Ledger docs already reference.

### Domain C — Findings, parked debt, queues, completeness
- OWNED: `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md`;
  `EVIDENCE_INDEX.md`; `RECONCILIATION_REPORT.md`; Master Ledger sec 5;
  Program sec 5, 8, 12; `stage0-05-governance-debt-v0.1.md` "## Existing
  debt and queue" section (Q22-26) only; `verify-05-governance-debt.md`
  (whole file).
- CITED: `docs/PROJECT_STATE.md` (owned by B); `CLAUDE.md` (owned by A,
  cited by all); `docs/PRD_REGISTRY.md` + `docs/prd_index.json` (owned by
  B, cited by all — PRD-number lookups only); Program sec 2, 3, 4, 6, 7
  (owned by B, cited by all).
- EXCLUDED BY DEFAULT: "PRD-255 follow-ons" — dropped from scope (zero
  grounding found in either North Star anchor doc). If independently
  surfaced with a real connection, log as an amendment, don't chase it.

### Domain D1 — Product surfaces, as-built
- OWNED: `cuttingboard/delivery/dashboard_renderer.py`,
  `cuttingboard/market_map.py`, `cuttingboard/market_map_lifecycle.py`,
  `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md`.
- CITED: `CLAUDE.md` (owned by A, cited by all); `docs/PRD_REGISTRY.md` +
  `docs/prd_index.json` (owned by B, cited by all — PRD-number lookups
  only); Program sec 2, 3, 4, 6, 7 (owned by B, cited by all — specifically
  the candidate card / Market Map source-map row within sec 3).
- EXCLUDED BY DEFAULT: broader `cuttingboard/` traversal beyond the 3 named
  files — log as amendment if verifying "actual implementation seams"
  needs more.
- Methodology: fact-check against real code.

### Domain D2 — Product surfaces, proposed
- OWNED: Master Ledger sec 4 NS-2 block only (lines 122-134, NS-2A through
  NS-2F).
- CITED: `CLAUDE.md` (owned by A, cited by all); `docs/PRD_REGISTRY.md` +
  `docs/prd_index.json` (owned by B, cited by all — PRD-number lookups
  only); `docs/prd_history/PRD-271.md` (owned by E — dependency-chain
  only); Program sec 2, 3, 4, 6, 7 (owned by B, cited by all — specifically
  its NS-2 source-map/dependency-graph/sequencing rows, as the "stated
  dependency/unbuilt status" this domain's plan-consistency check verifies
  against).
- EXCLUDED BY DEFAULT: none beyond its methodology framing.
- Methodology: plan-consistency check only (does the North Star doc's own
  NS-2E description match its own stated dependency/unbuilt status) —
  never a fact-check, since nothing is built.

### Domain E — SPY observation, candidate fidelity, ORB
- OWNED: `docs/prd_history/PRD-271.md`,
  `STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md`.
- CITED: `CLAUDE.md` (owned by A, cited by all); `docs/PRD_REGISTRY.md` +
  `docs/prd_index.json` (owned by B, cited by all — PRD-number lookups
  only); `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md`
  (owned by D1); `FINDING_STATUS_MATRIX.md` CB-07 row (owned by C); Program
  sec 2, 3, 4, 6, 7 (owned by B, cited by all).
- EXCLUDED BY DEFAULT: general VWAP semantics (the 41-file scattered
  corpus, confirmed unrelated to the fidelity-delta doc). VWAP evidence
  directly tied to PRD-271/CB-07 may be cited; a general VWAP sweep may
  not — log as amendment if the ORB/fidelity evidence turns out to need it.

### Domain F — Data contracts, freshness, scheduling
- OWNED: `audits/stage0-recon-2026-07-20/stage0-02-evaluation-v0.1.md`,
  `stage0-03-scheduler-v0.1.md` (+ verify-02/verify-03 companions).
- CITED: `CLAUDE.md` (owned by A, cited by all); `docs/PRD_REGISTRY.md` +
  `docs/prd_index.json` (owned by B, cited by all — PRD-number lookups
  only); `FINDING_STATUS_MATRIX.md` (owned by C — CB-06/CB-18 rows);
  Master Ledger sec 4 NS-8A cohort-capture entry (owned by B, within the
  non-NS-2 block); Program sec 2, 3, 4, 6, 7 (owned by B, cited by all).
- EXCLUDED BY DEFAULT: an independent freshness/STAY_FLAT sweep across the
  full 79/70-file scattered corpus.
- Methodology: reconciliation against the already-cited stage0 recon (SHA
  `771f730`), not independent re-derivation.

### Domain G — Expansion vocabulary reconciliation
- OWNED: `docs/plans/decision-support-expansion-doctrine-v0.1.md`,
  `docs/plans/decision-support-workplan-v0.1.md`,
  `audits/stage0-recon-2026-07-20/stage0-04-gex-v0.1.md`.
- CITED: `CLAUDE.md` (owned by A, cited by all); `docs/PRD_REGISTRY.md` +
  `docs/prd_index.json` (owned by B, cited by all — PRD-number lookups
  only); Program sec 2, 3, 4, 6, 7 (owned by B, cited by all); Program sec
  12 "Not lost" appendix (owned by C — its GEX-1/GEX-2/GEX-3 rows, lines
  490-492); Master Ledger sec 4 NS-3 through NS-7 rows (owned by B, within
  the non-NS-2 block — Opportunity Set Engine=NS-3, universe
  registry/heatmap=NS-4, air-gapped GEX=NS-5, relationship-aware news=NS-6,
  idiosyncratic decoupling=NS-7 — cited as the terms being checked, not as
  a source of truth).
- EXCLUDED BY DEFAULT: none — surfacing the vocabulary gap is this
  domain's job, not something to avoid.
- Methodology: for each North-Star-only term, confirm/deny a doctrine
  anchor exists; where none exists, record `assertion_type:
  FUTURE-DESIGN-INTENT` or `OWNER-DECISION` with `Dustin ruling required?
  = yes` — not a MISMATCH.
