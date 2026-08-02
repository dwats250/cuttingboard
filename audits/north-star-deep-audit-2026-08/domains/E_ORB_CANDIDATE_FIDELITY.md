# Domain E — SPY observation, candidate fidelity, ORB

## Header
- Baseline SHA: `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`
- Accepted scaffold seam SHA: `e0d481f4e3daeae9d8cba4a7aee7670d27b5a2b5`
- Authorized Phase 1 execution-contract SHA: `41bfcd6888b7c28da9c0478c9534bdb66a9a2600`
- Assigned domain: E
- Dispatch parameters (verbatim from `01_SOURCE_AUTHORITY_MANIFEST.md`):

- OWNED: `docs/prd_history/PRD-271.md`,
  `audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md`.
- CITED: `CLAUDE.md` (owned by A, cited by all); `docs/PRD_REGISTRY.md` +
  `docs/prd_index.json` (owned by B, cited by all — PRD-number lookups
  only); `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md`
  and `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md`
  (owned by D1); `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md` CB-07 row (owned by C); Program
  sec 2, 3, 4, 6, 7 (owned by B, cited by all).
- EXCLUDED BY DEFAULT: general VWAP semantics (the 41-file scattered
  corpus, confirmed unrelated to the fidelity-delta doc). VWAP evidence
  directly tied to PRD-271/CB-07 may be cited; a general VWAP sweep may
  not — log as amendment if the ORB/fidelity evidence turns out to need it.


Files inspected:

- `audits/north-star-deep-audit-2026-08/00_AUDIT_CHARTER.md`
- `audits/north-star-deep-audit-2026-08/01_SOURCE_AUTHORITY_MANIFEST.md`
- `audits/north-star-deep-audit-2026-08/02_DOMAIN_COVERAGE_MATRIX.md`
- `docs/prd_history/PRD-271.md`
- `audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md`
- `CLAUDE.md`
- `docs/PRD_REGISTRY.md`
- `docs/prd_index.json`
- `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md`
- `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md`
- `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md`
- `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`
- `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` — read during
  attempt 1, but not in Domain E's OWNED or CITED dispatch set (see the
  Stage 0 review remediation note below the evidence table). Kept in this
  list because it accurately records what was read; no evidence-table row
  now cites it.

Files intentionally excluded:

- General VWAP corpus — excluded by dispatch; only PRD-271/CB-07-tied VWAP evidence was considered.
- Unnamed `cuttingboard/` implementation files — outside the dispatch scope.

Completion status: COMPLETE — every owned source and required cited source was inspected with no blocking gap.

Attempt count: 1

No-edits attestation: confirmed

## Evidence

| ID | North Star assertion | assertion_type | evidence (path:lines, pinned) | result | risk | confidence | assumptions | Dustin ruling required? |
|---|---|---|---|---|---|---|---|---|
| E-01 | NS-2B is the session-correct ORB packet and must ride PRD-271 rather than create a second ORB truth. | FUTURE-DESIGN-INTENT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:294-307`; `docs/prd_history/PRD-271.md:59-65`; `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:121-153` | MATCH | A duplicate ORB producer could create conflicting execution and observation decisions. | HIGH |  | yes |
| E-02 | PRD-271 is an IN PROGRESS, HIGH-RISK, execution-class Stage-0 scaffold with Gate A pending and no fix authorized. | FACT | `docs/prd_history/PRD-271.md:1-9,54-65,104`; `docs/PRD_REGISTRY.md:288-295`; `docs/prd_index.json:1297-1300`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:84-85,297-305` | MATCH | Treating the scaffold as implementation authorization could permit an unruled high-risk change. | HIGH |  | no |
| E-03 | The ORB defect is caused by upstream `tail(120)`, a second `tail(120)`, and positional `bars[:5]`, producing a mid-session rather than opening-session range. | FACT | `docs/prd_history/PRD-271.md:11-34`; `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:121-129,146-153`; `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:16-49`; `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md:138-153` | MATCH | Incorrect ORB values can contaminate trader-facing state and execution gating. | HIGH |  | no |
| E-04 | The ORB is not display-only; it feeds the live `orb_inside_range` BLOCK_TRADE gate and can both block valid trades and permit trades that should block. | FACT | `docs/prd_history/PRD-271.md:47-52`; `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md:145-149`; `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:146-153` | MATCH | A false ORB can alter terminal trade permission. | HIGH |  | no |
| E-07 | The candidate-fidelity delta settled CuttingBoard-side truth as a proxy posture defect only, with no CuttingBoard engine change or documentation drift; PRD-271 was untouched. | FACT | `audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md:28-41,54-65,105-122`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:75-77,92` | MATCH | Misclassifying proxy evidence as an engine defect could authorize unnecessary CuttingBoard changes. | HIGH |  | no |
| E-08 | The fidelity delta’s corrected analog counts are 284 / 79 / 112, while the registered 602 / 170 / 239 counts must not be read as faithful CuttingBoard-semantics counts. | FACT | `audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md:107-145,181-201` | MATCH | Future packets could cite inflated proxy counts as if they were CuttingBoard candidate or trade outcomes. | HIGH |  | yes |
| E-09 | The frozen AS-IS proxy was executed, but its posture dimension is defective and faithful QUALIFIED/WATCHLIST/REJECT counts remain unresolved pending a corrected frozen run or Strategy-side disposition. | FACT | `audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md:114-123,181-200,216-240` | MATCH | Unqualified proxy outputs could be treated as production-semantics evidence. | HIGH |  | yes |
| E-10 | The current observation artifact is genuinely unbuilt: no durable session-observation record currently owns session date, ORB, full-session VWAP, and lifecycle together. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:93-95,110-115`; `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:58-63,121-142,199-213`; `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:115-126` | MATCH | Consumers may mistake transient or filtered values for durable session facts. | HIGH |  | no |

**Rows removed during Stage 0 review remediation (2026-08-02):** E-05 (NS-2A
fixed-SPY-observation future intent), E-06 (NS-2C VWAP future intent), and
E-11 (PRD-271 lifecycle `BLOCKED` vs `IN PROGRESS` label discrepancy) cited
`docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`, which is not
in Domain E's OWNED or CITED dispatch set (Master Ledger sec 4's NS-2 block
is owned by D2; the remainder, including the PRD-271 lifecycle row at
lines 257-265, is owned by B). E-05 and E-06 duplicated D2's own
already-covered findings D2-NS2-02 and D2-NS2-04 exactly (same assertions,
overlapping Ledger line ranges) — routed to D2, not re-derived here.
E-11's underlying Ledger range (257-265, encompassing 263-265) is the same
evidence B-016 already cites for PRD-271's lifecycle status; routed to B
rather than duplicated. No unauthorized evidence was added to compensate —
these three rows are removed, not replaced with unsupported certainty.

No repository files were edited during this dispatch.
