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
- `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`

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
| E-05 | NS-2A will observe SPY on every relevant run, including `STAY_FLAT` and halted states, independently of candidate availability. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:122-130`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:294-307`; `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:80-99,101-110` | PARTIAL | Candidate-gated or skipped observation could leave the trader without fixed-market context precisely when no candidate exists. | MEDIUM | The phrase “every relevant run” is assumed to include all production decision modes but exclude fixture/Sunday paths where the cited stage evidence documents skips. | yes |
| E-06 | NS-2C is intended to provide an authoritative session-anchored VWAP with explicit source window, timestamp, and stale behavior. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:128-133`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:297-307`; `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:58-72,121-142,199-213` | MATCH | An unproven VWAP authority could expose stale or non-session values as market facts. | MEDIUM | “Authoritative” is treated as a future ownership requirement, not a claim that the current VWAP producer is authoritative. | yes |
| E-07 | The candidate-fidelity delta settled CuttingBoard-side truth as a proxy posture defect only, with no CuttingBoard engine change or documentation drift; PRD-271 was untouched. | FACT | `audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md:28-41,54-65,105-122`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:75-77,92`; `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:102-112,268-281` | MATCH | Misclassifying proxy evidence as an engine defect could authorize unnecessary CuttingBoard changes. | HIGH |  | no |
| E-08 | The fidelity delta’s corrected analog counts are 284 / 79 / 112, while the registered 602 / 170 / 239 counts must not be read as faithful CuttingBoard-semantics counts. | FACT | `audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md:107-145,181-201`; `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:268-281` | MATCH | Future packets could cite inflated proxy counts as if they were CuttingBoard candidate or trade outcomes. | HIGH |  | yes |
| E-09 | The frozen AS-IS proxy was executed, but its posture dimension is defective and faithful QUALIFIED/WATCHLIST/REJECT counts remain unresolved pending a corrected frozen run or Strategy-side disposition. | FACT | `audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md:114-123,181-200,216-240`; `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:275-281` | MATCH | Unqualified proxy outputs could be treated as production-semantics evidence. | HIGH |  | yes |
| E-10 | The current observation artifact is genuinely unbuilt: no durable session-observation record currently owns session date, ORB, full-session VWAP, and lifecycle together. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:93-95,110-115`; `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:58-63,121-142,199-213`; `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:115-126` | MATCH | Consumers may mistake transient or filtered values for durable session facts. | HIGH |  | no |
| E-11 | PRD-271’s North Star state is described as blocked pending Gate A, while the registry and PRD itself retain `IN PROGRESS`; these are not the same lifecycle value. | FACT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:257-265`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:76-85,157-162`; `docs/prd_history/PRD-271.md:1-4,59-65`; `docs/PRD_REGISTRY.md:291`; `docs/prd_index.json:1297-1300`; `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md:144-151` | PARTIAL | Ambiguous status wording can make a dependency block appear to be a lifecycle transition or imply that Gate A has already been resolved. | LOW | The ledger’s `BLOCKED` is assumed to describe implementation readiness rather than the authoritative PRD lifecycle. | yes |

## Non-match detail — E-05

- Exact source path+lines: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:122-130`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:294-307`; `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:101-110`.
- Governing authority: The North Star future-design statement is governed by Dustin; current producer behavior is evidenced by the pinned stage0-01 recon.
- Observed discrepancy: The North Star assertion uses universal “every relevant run,” while the cited evidence establishes production premarket/hourly placement but documents skips for fixture/Sunday modes and swallowed writer failures.
- Practical consequence: A future implementation could omit halted or otherwise non-candidate production paths while appearing consistent with the broad statement.
- False-authority risk: The future statement could be mistaken for an already-proven runtime contract.
- Safety relevance: Missing SPY observation can remove context needed for flat or halted decisions.
- Current-vs-future-facing effect: Future-facing design intent; no current implementation mismatch is claimed.
- Proposed disposition: Preserve the intent, but define the exact run-mode coverage and failure semantics at Gate A.
- Confidence: MEDIUM.
- Missing evidence: A complete run-mode matrix proving observation coverage for live, halted, `STAY_FLAT`, fixture, Sunday, and writer-failure paths.

## Non-match detail — E-11

- Exact source path+lines: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:257-265`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:76-85,157-162`; `docs/prd_history/PRD-271.md:1-4,59-65`; `docs/PRD_REGISTRY.md:291`; `docs/prd_index.json:1297-1300`.
- Governing authority: The PRD registry and PRD document govern lifecycle status; the North Star documents govern portfolio/dependency presentation.
- Observed discrepancy: The ledger labels the PRD-271 lifecycle/document gap `BLOCKED`, while the authoritative PRD and registry/index retain `IN PROGRESS`; the Program describes it as an IN PROGRESS scaffold blocked from implementation by Gate A.
- Practical consequence: Readers may interpret `BLOCKED` as a lifecycle status, causing incorrect queue, validator, or promotion decisions.
- False-authority risk: The ledger’s combined state can silently override the registry’s authoritative lifecycle vocabulary.
- Safety relevance: Gate A could be treated as complete or bypassed if status semantics are unclear around a high-risk execution seam.
- Current-vs-future-facing effect: Current documentation/status representation; implementation remains future-facing and unauthorized.
- Proposed disposition: Dustin should rule whether the ledger’s `BLOCKED` label is explicitly a dependency/readiness condition and ensure it is not presented as the PRD lifecycle value.
- Confidence: LOW.
- Missing evidence: A governing status-axis rule explicitly mapping the ledger’s `BLOCKED` state to the registry’s `IN PROGRESS` lifecycle while Gate A is pending.

No repository files were edited during this dispatch.
