# Domain G — Expansion vocabulary reconciliation

## Header
- Baseline SHA: `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`
- Accepted scaffold seam SHA: `e0d481f4e3daeae9d8cba4a7aee7670d27b5a2b5`
- Authorized Phase 1 execution-contract SHA: `41bfcd6888b7c28da9c0478c9534bdb66a9a2600`
- Assigned domain: G
- Dispatch parameters (verbatim from `01_SOURCE_AUTHORITY_MANIFEST.md`):

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

- Files inspected:
  - `audits/north-star-deep-audit-2026-08/00_AUDIT_CHARTER.md`
  - `audits/north-star-deep-audit-2026-08/01_SOURCE_AUTHORITY_MANIFEST.md`
  - `audits/north-star-deep-audit-2026-08/02_DOMAIN_COVERAGE_MATRIX.md`
  - `CLAUDE.md`
  - `docs/PRD_REGISTRY.md`
  - `docs/prd_index.json`
  - `docs/plans/decision-support-expansion-doctrine-v0.1.md`
  - `docs/plans/decision-support-workplan-v0.1.md`
  - `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`
  - `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`
  - `audits/stage0-recon-2026-07-20/stage0-04-gex-v0.1.md`
- Files intentionally excluded: None — the manifest specifies no Domain G exclusions.
- Completion status: COMPLETE — every owned source and required cited source was inspected with no blocking gap.
- Attempt count: 1
- No-edits attestation: confirmed

## Evidence

| ID | North Star assertion | assertion_type | evidence (path:lines, pinned) | result | risk | confidence | assumptions | Dustin ruling required? |
|---|---|---|---|---|---|---|---|---|
| G-001 | NS-3 defines an Opportunity Set Engine with opportunity taxonomy, funnel visibility, negative market statements, maturity/deterioration views, and confidence decomposition. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:135-145`; doctrine boundary at `docs/plans/decision-support-expansion-doctrine-v0.1.md:40-43,49-53` | UNKNOWN | An unsupported vocabulary item could later be mistaken for an approved product contract or analytical permission. | MEDIUM | Corrected 2026-08-02 per Fable's adjudication (Finding 5): removed `Program:478-483` (§12 NS-3 entry, Domain C's territory, outside G's narrow §12 GEX-only 490-492 grant). Master Ledger:135-145 (G-cited, term being checked) plus the doctrine citation already fully support this result. | yes |
| G-002 | NS-4 defines a shared universe registry and heatmap substrate containing symbols, aliases, themes, roles, horizons, benchmarks, questions, movement, leadership, participation, and an external watchlist mirror. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:147-161`; doctrine news-scope anchor at `docs/plans/decision-support-expansion-doctrine-v0.1.md:284-302`; workplan registry anchor at `docs/plans/decision-support-workplan-v0.1.md:310-334` | PARTIAL | The doctrine anchors a bounded universe/theme registry, but not the broader shared heatmap, leadership, participation, or watchlist-substrate vocabulary. | MEDIUM | Corrected 2026-08-02 per Fable's adjudication (Finding 5): removed `Program:484-488` (§12 NS-4 entry, outside G's narrow §12 GEX-only 490-492 grant) from the row and its detail block. Master Ledger:147-161 plus the doctrine/workplan citations already fully support this result. | yes |
| G-003 | NS-5 is an air-gapped GEX expansion: GEX-0 provider evidence, GEX-1 cached producer, GEX-2 display-only consumer, and optional GEX-3 cadence, with no signal, qualification, sizing, or permission effect. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:163-176`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:132-133,490-492`; `docs/plans/decision-support-expansion-doctrine-v0.1.md:215-271`; `docs/plans/decision-support-workplan-v0.1.md:368-401` | MATCH | If the air-gap is lost, observational context could alter trade permission or risk decisions without authorization. | HIGH | Corrected 2026-08-02 per Fable's adjudication (Finding 5): narrowed `Program:489-493` to `490-492` — G's exact §12 grant is the GEX-1/GEX-2/GEX-3 rows at lines 490-492 only; 489 and 493 exceeded it. Result unaffected. | yes |
| G-004 | No committed GEX provider, contract, or consumer exists at the pinned baseline, and GEX-0 has not been run because external reach was disabled. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:80`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:132-133`; `audits/stage0-recon-2026-07-20/stage0-04-gex-v0.1.md:47-56,64-69` | MATCH | Treating GEX as implemented or provider-validated could authorize unsupported downstream work. | HIGH |  | no |
| G-005 | NS-6 defines relationship-aware news through a static Dustin-ratified registry, deterministic manual producer, bounded item count, usefulness ruling, display consumer, and last-stage cadence. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:178-204`; `docs/plans/decision-support-expansion-doctrine-v0.1.md:273-318`; `docs/plans/decision-support-workplan-v0.1.md:310-366` | MATCH | An unbounded news feed or premature cadence could create nondeterministic, misleading, or pipeline-coupled output. | HIGH | Corrected 2026-08-02 per Fable's adjudication (Finding 5): removed `Program:178-204` (§5, Domain C's territory, and content-irrelevant — those lines are CB debt rows, not NS-6 content) and `Program:494-498` (§12 NS-6 entry, outside G's narrow grant). Master Ledger:178-204 (G-cited) plus the doctrine/workplan citations already fully support this result. | yes |
| G-006 | NS-6's relationship path is `GLOBAL STATE → THEME HEALTH → THEME LEADERS → WATCHLIST → SETUPS → TRADES`. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:190-204`; doctrine boundary at `docs/plans/decision-support-expansion-doctrine-v0.1.md:273-302` | UNKNOWN | The path could be mistaken for an approved causal or decision pipeline despite lacking a doctrine anchor. | MEDIUM | Corrected 2026-08-02 per Fable's adjudication (Finding 5): removed `Program:494-498` (§12 NS-6 entry, outside G's narrow §12 GEX-only 490-492 grant). Master Ledger:190-204 plus the doctrine citation already fully support this result. | yes |
| G-007 | NS-7 defines idiosyncratic decoupling using a window, benchmark, threshold, freshness, heatmap label, and news link without invented cause. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:206-216`; doctrine boundary at `docs/plans/decision-support-expansion-doctrine-v0.1.md:49-53,284-302` | UNKNOWN | An unanchored decoupling score or causal label could become unsupported analytical or trading guidance. | MEDIUM | Corrected 2026-08-02 per Fable's adjudication (Finding 5): removed `Program:499-501` (§12 NS-7 entry, outside G's narrow §12 GEX-only 490-492 grant). Master Ledger:206-216 plus the doctrine citation already fully support this result. | yes |
| G-008 | Personalized news is distinct from the existing PRD-187 macro-awareness producer and PRD-188 gated consumer; the macro-awareness track may not be renamed or repurposed as personalized news. | FACT | `docs/plans/decision-support-expansion-doctrine-v0.1.md:165-177`; `docs/plans/decision-support-workplan-v0.1.md:279-308`; `docs/PRD_REGISTRY.md:207-208`; `docs/prd_index.json:793-803`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:88` | MATCH | Conflating the tracks could bypass the separate news registry and promotion gates. | HIGH | Corrected 2026-08-02 per Fable's adjudication (Finding 5): removed `,414-415` from the Program citation (§9, Domain A's territory). G's own doctrine (165-177) and workplan (279-308) citations already state the no-rename/no-repurpose rule directly; the remaining `Program:88` (§3, G-cited) is unaffected. | no |

## Non-match detail

### G-002 — PARTIAL

- Exact source path+lines: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:147-161`; `docs/plans/decision-support-expansion-doctrine-v0.1.md:284-302`; `docs/plans/decision-support-workplan-v0.1.md:310-334`
- Governing authority: `docs/plans/decision-support-expansion-doctrine-v0.1.md:15-26,284-318`
- Observed discrepancy: The doctrine anchors a bounded personal universe, context symbols, themes, deterministic source/symbol/theme/freshness/deduplication rules, and a human-approved registry. It does not define the full NS-4 shared substrate vocabulary: movement heatmap, leadership mode, participation mode, external watchlist mirror, roles, horizons, benchmarks, or questions.
- Practical consequence: NS-4's unanchored components remain future design intent and cannot be treated as an existing contract.
- False-authority risk: A future implementation could infer that the doctrine already authorizes a shared registry, heatmap, benchmark-relative analysis, or watchlist synchronization.
- Safety relevance: Indirect; the main risk is unsupported analytical context becoming coupled to decision or trade outputs.
- Current-vs-future-facing effect: No current implementation claim is established; the discrepancy affects future design only.
- Proposed disposition: Retain as `PARTIAL` with `assertion_type: FUTURE-DESIGN-INTENT` and require owner review before treating the missing vocabulary as a doctrine-backed contract.
- Confidence: MEDIUM
- Missing evidence: A doctrine or owner-ratified contract defining the full NS-4 registry and heatmap substrate.

## PROPOSED AMENDMENT

None.

No repository files were edited during this dispatch.
