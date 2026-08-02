# Domain F — Data contracts, freshness, scheduling

## Header
- Baseline SHA: `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`
- Accepted scaffold seam SHA: `e0d481f4e3daeae9d8cba4a7aee7670d27b5a2b5`
- Authorized Phase 1 execution-contract SHA: `41bfcd6888b7c28da9c0478c9534bdb66a9a2600`
- Assigned domain: F
- Dispatch parameters (verbatim from `01_SOURCE_AUTHORITY_MANIFEST.md`):

- OWNED: `audits/stage0-recon-2026-07-20/stage0-02-evaluation-v0.1.md`,
  `audits/stage0-recon-2026-07-20/stage0-03-scheduler-v0.1.md` (+
  `audits/stage0-recon-2026-07-20/verify-02-evaluation.md`/`audits/stage0-recon-2026-07-20/verify-03-scheduler.md` companions, same
  directory).
- CITED: `CLAUDE.md` (owned by A, cited by all); `docs/PRD_REGISTRY.md` +
  `docs/prd_index.json` (owned by B, cited by all — PRD-number lookups
  only); `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md` (owned by C — CB-06/CB-18 rows);
  Master Ledger sec 4 NS-8A cohort-capture entry (owned by B, within the
  non-NS-2 block); Program sec 2, 3, 4, 6, 7 (owned by B, cited by all).
- EXCLUDED BY DEFAULT: an independent freshness/STAY_FLAT sweep across the
  full 79/70-file scattered corpus.
- Methodology: reconciliation against the already-cited stage0 recon (SHA
  `771f730`), not independent re-derivation.

Files inspected:

- `audits/north-star-deep-audit-2026-08/00_AUDIT_CHARTER.md`
- `audits/north-star-deep-audit-2026-08/01_SOURCE_AUTHORITY_MANIFEST.md`
- `audits/north-star-deep-audit-2026-08/02_DOMAIN_COVERAGE_MATRIX.md`
- `audits/north-star-deep-audit-2026-08/03_AMENDMENTS_LOG.md`
- `CLAUDE.md`
- `docs/PRD_REGISTRY.md`
- `docs/prd_index.json`
- `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md`
- `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`
- `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`
- `audits/stage0-recon-2026-07-20/stage0-02-evaluation-v0.1.md`
- `audits/stage0-recon-2026-07-20/stage0-03-scheduler-v0.1.md`
- `audits/stage0-recon-2026-07-20/verify-02-evaluation.md`
- `audits/stage0-recon-2026-07-20/verify-03-scheduler.md`

Files intentionally excluded:

- Full 79/70-file scattered freshness/STAY_FLAT corpus — explicitly excluded by dispatch; no independent sweep performed.
- `audits/north-star-deep-audit-2026-08/domains/PR187_EVIDENCE_SNAPSHOT_2026-08-02.md` — Domain A-only PR #187 connector evidence; not applicable to Domain F.
- `docs/prd_history/` beyond PRD-number lookups — excluded by the manifest; no full PRD re-audit performed.

Completion status: COMPLETE — every OWNED source and required CITED source was inspected with no blocking gap.  
Attempt count: 1  
No-edits attestation: confirmed

## Evidence

| ID | North Star assertion | assertion_type | evidence (path:lines, pinned) | result | risk | confidence | assumptions | Dustin ruling required? |
|---|---|---|---|---|---|---|---|---|
| F-01 | Stage0-02 is retained as the NS-8 evidence base for cohort schema, the `stay_flat_reason` audit gap, and absence of session clustering. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:77-79,506-507`; `audits/stage0-recon-2026-07-20/stage0-02-evaluation-v0.1.md:36-80`; `audits/stage0-recon-2026-07-20/verify-02-evaluation.md:16-83` — all pinned via `git show fdeef90:<path>` | MATCH | Incorrectly discarding this evidence could cause NS-8 to be designed without the known cohort and aggregation limitations. | HIGH |  | no |
| F-02 | Stage0-03 is retained as the NS-9 evidence base for schedule ownership, force/deduplication semantics, verify-mode diagnostics, and the observed-replacement bar. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:77-80`; `audits/stage0-recon-2026-07-20/stage0-03-scheduler-v0.1.md:33-91`; `audits/stage0-recon-2026-07-20/verify-03-scheduler.md:16-102` — pinned | MATCH | Scheduling changes could rely on incomplete ownership or treat green workflow status as operational proof. | HIGH |  | no |
| F-03 | NS-8A is intended to capture qualified, near-miss, excluded-by-reason, and `STAY_FLAT` cohorts. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:218-228`; `audits/stage0-recon-2026-07-20/stage0-02-evaluation-v0.1.md:38-56`; `verify-02-evaluation.md:16-39` — pinned | MATCH | A future evaluator that records only `ALLOW_TRADE` would omit decision-relevant cohorts. | HIGH |  | yes |
| F-04 | The current evaluator selects only `ALLOW_TRADE` decisions and does not represent qualification-watchlist or excluded cohorts. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:78`; `stage0-02-evaluation-v0.1.md:38-46`; `verify-02-evaluation.md:16-35` — pinned | MATCH | NS-8 outcome analysis would be biased toward trades and lose abstentions or exclusions. | HIGH |  | no |
| F-05 | The bare `watchlist` label is ambiguous because qualification watchlist data and intraday `WatchSummary.watchlist` are persisted under distinct meanings. | FACT | `stage0-02-evaluation-v0.1.md:48-56`; `verify-02-evaluation.md:27-39` — pinned | MATCH | A cohort contract using the unqualified label could attribute outcomes to the wrong population. | HIGH |  | no |
| F-06 | The finalized `system_state.stay_flat_reason` reaches contract and payload artifacts but is absent from the append-only audit/evaluation record. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:78`; `stage0-02-evaluation-v0.1.md:58-68`; `verify-02-evaluation.md:41-67` — pinned | MATCH | Evaluation history cannot explain non-halt `STAY_FLAT` or Sunday outcomes. | HIGH |  | no |
| F-07 | Current performance aggregation is per-symbol and per-record, with a minimum sample of five records, not session-clustered. | FACT | `stage0-02-evaluation-v0.1.md:70-80`; `verify-02-evaluation.md:69-83` — pinned | MATCH | Multiple candidates from one decision run may be counted as independent observations. | HIGH |  | no |
| F-08 | NS-9A–NS-9D are intended to provide run identity, execution observability, visible artifact freshness, and cadence promotion only after usefulness. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:239-250`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:508-511`; `stage0-03-scheduler-v0.1.md:45-91`; `verify-03-scheduler.md:68-102` — pinned | MATCH | Missing any of these fields could make stale or duplicate outputs appear trustworthy. | HIGH |  | yes |
| F-09 | The hourly runner can remain green for broken-but-non-throwing runs, and readiness checks key presence rather than status values; CB-06 remains open and High. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:164-178`; `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md:118-128` — pinned | MATCH | A stale or ERROR artifact may be treated as healthy and published. | HIGH |  | no |
| F-10 | Freshness currently measures fetch time rather than market time; CB-18 remains open and High and anchors NS-9. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:164-178`; `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md:355-361` — pinned | MATCH | Delayed, prior-close, weekend, or holiday data may be certified as current. | HIGH |  | no |
| F-11 | NS-8 and NS-9 are preserved as LATER work and are not authorized implementation packets. | FUTURE-DESIGN-INTENT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:294-316,471-511`; `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:218-250` — pinned | MATCH | Treating preserved work as authorized could bypass portfolio and review gates. | HIGH |  | yes |
| F-12 | The scheduling/freshness work is ordered after the NS-2 observation substrate, with NS-2A observation artifacts and NS-9C freshness vocabulary identified as shared substrate. | FUTURE-DESIGN-INTENT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:99-124`; `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:122-134,239-250` — pinned | MATCH | Implementing NS-2A's freshness handling without eventual reconciliation to NS-9C's formal vocabulary could create incompatible freshness semantics once NS-9C lands. | HIGH | Corrected 2026-08-02 per adjudicated Stage 0 finding: the dependency graph's own arrow convention (confirmed elsewhere in the same graph, e.g. `PRD-271 Gate A └─ NS-2B └─ NS-2A/NS-2C`, prerequisite-above / dependent-below) reads "NS-2A observation artifact + NS-9C freshness vocabulary are shared substrate └─ NS-9 scheduling/freshness" as NS-2A and NS-9C being co-prerequisites feeding NS-9 as the dependent — not NS-2A depending on NS-9C. NS-9C is itself a sub-packet of NS-9 (Master Ledger NS-9 table: "NS-9C Artifact freshness"), not an external thing NS-2A must consume first. No blocking sequencing conflict is established by this text; the earlier PARTIAL result and "circular dependency" framing misread the arrow direction. A non-blocking design note remains: NS-2A's initial freshness handling should stay compatible with NS-9C's later formal vocabulary, so an interim local contract may need reconciling once NS-9C lands — this is a coherence note, not a blocker, and requires no Dustin ruling. | no |

## Non-match detail blocks

## PROPOSED AMENDMENT

- discovered by: Program §12 NS-8 references CB-11 and CB-20…CB-25; description: those join-key and decision-history findings are outside Domain F’s named cited sources; proposed scope change: add the relevant matrix rows if F is required to verify the complete NS-8 dependency chain; blocking: no.

- discovered by: Program §4 dependency graph; description: NS-9C is described as sharing substrate with the NS-2A observation artifact owned outside Domain F; proposed scope change: add the relevant NS-2A artifact source only if a cross-domain substrate audit is required; blocking: no.

No repository files were edited during this dispatch.
