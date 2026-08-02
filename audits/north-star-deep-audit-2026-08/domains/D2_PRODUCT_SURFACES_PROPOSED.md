# Domain D2 — Product surfaces, proposed

## Header
- Baseline SHA: `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`
- Accepted scaffold seam SHA: `e0d481f4e3daeae9d8cba4a7aee7670d27b5a2b5`
- Authorized Phase 1 execution-contract SHA: `41bfcd6888b7c28da9c0478c9534bdb66a9a2600`
- Assigned domain: D2
- Dispatch parameters (verbatim from `01_SOURCE_AUTHORITY_MANIFEST.md`):

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

Files inspected:

- `audits/north-star-deep-audit-2026-08/00_AUDIT_CHARTER.md`
- `audits/north-star-deep-audit-2026-08/01_SOURCE_AUTHORITY_MANIFEST.md`
- `audits/north-star-deep-audit-2026-08/02_DOMAIN_COVERAGE_MATRIX.md`
- `CLAUDE.md` — pinned baseline read
- `docs/PRD_REGISTRY.md` — pinned baseline read
- `docs/prd_index.json` — pinned baseline read
- `docs/prd_history/PRD-271.md` — pinned baseline read
- `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` — pinned baseline read, NS-2 block only
- `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` — pinned baseline read, §§2, 3, 4, 6, 7

Files intentionally excluded: None. No source outside the dispatch parameters was required.  
Completion status: COMPLETE  
Attempt count: 1  
No-edits attestation: confirmed

## Evidence table

| ID | North Star assertion | assertion_type | evidence (path:lines, pinned) | result | risk | confidence | assumptions | Dustin ruling required? |
|---|---|---|---|---|---|---|---|---|
| D2-NS2-01 | NS-2 is intended to deliver the first visible post-governance product win. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:122-124`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:294-307` | MATCH | Misstating portfolio priority could promote the wrong product slice. | HIGH |  | no |
| D2-NS2-02 | NS-2A is a NEXT packet for fixed SPY observation on every relevant run, including `STAY_FLAT` and halted states, and is independent of candidate availability. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:126-129`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:77,94,294-307` | PARTIAL | Omission of non-candidate and halted-state observation requirements could produce incomplete observability. | MEDIUM | “Independent of candidate availability” is interpreted as independence from candidate output, not independence from the NS-2 dependency chain. | no |
| D2-NS2-03 | NS-2B is a NEXT packet for session-correct ORB, must use the intended market session rather than a positional data tail, rides PRD-271, and must not create a duplicate ORB truth. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:128-129`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:77,84,93-94,110-116`; `docs/prd_history/PRD-271.md:3-14,59-65` | MATCH | A divergent ORB implementation could cause observation and execution gates to disagree. | HIGH |  | yes |
| D2-NS2-04 | NS-2C is a NEXT packet for an authoritative session-anchored typical-price VWAP with explicit source window, timestamp, and stale behavior. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:128-130`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:77,110-116,297-306` | MATCH | Ambiguous VWAP provenance or freshness could make the observation card misleading. | MEDIUM |  | no |
| D2-NS2-05 | NS-2D is LATER and will preserve and expose the last meaningful intraday transition without flattening or discarding rich state. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:130-133`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:110-116,309-316` | MATCH | Loss of transition state would weaken later control-card interpretation. | MEDIUM |  | no |
| D2-NS2-06 | NS-2E is a NEXT Market Control Card, intended to replace or refactor the generic Market Map, answer the listed orientation questions, and occur after NS-2A/B/C exist to feed it. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:131-133`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:77,93,110-116,294-307` | MATCH | Building the card before its observation inputs exist could create an unsupported authority surface. | HIGH |  | no |
| D2-NS2-07 | NS-2F is LATER and represents a ranked, evidence-linked, non-predictive control ladder covering support, pivot, resistance, and structural failure. | FUTURE-DESIGN-INTENT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:131-133`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:110-116,309-316` | MATCH | A predictive or prematurely promoted ladder could introduce unsupported trading guidance. | MEDIUM |  | no |
| D2-NS2-08 | The NS-2A/B/C slice is not authorized for immediate implementation: it requires the A/B runway ruling, PRD-271 Gate A, MATERIAL intake, an upstream packet seeded by stage0-01, and must begin with the packet rather than code. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:9-14,77,84,99-116,136,294-306`; `CLAUDE.md:118-134,219-226,250-254`; `docs/prd_history/PRD-271.md:59-65` | MATCH | Treating planning text as implementation permission could bypass safety and design gates. | HIGH |  | yes |
| D2-NS2-09 | PRD-271 is the authoritative dependency for NS-2B and remains an IN PROGRESS, HIGH-RISK scaffold with Gate A pending; NS-2B must ride it rather than duplicate it. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:84,110-113`; `docs/prd_history/PRD-271.md:3-9,59-65`; `docs/PRD_REGISTRY.md:291`; `docs/prd_index.json:1297-1300` | MATCH | Incorrect lifecycle or ownership could authorize duplicate or conflicting ORB work. | HIGH |  | yes |
| D2-NS2-10 | The dependency sequence is NS-2B first, then NS-2A and NS-2C; NS-2E follows NS-2A/B/C; NS-2D and NS-2F remain later dependencies. | INTERPRETATION | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:99-116,123-127,294-316`; `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:126-133` | MATCH | Reordering could produce a control surface without stable observation inputs. | HIGH | “Independent of candidate availability” in NS-2A does not negate the separately stated ORB and observation dependency sequence. | no |
| D2-NS2-11 | The proposed NS-2 surfaces remain future-facing and unbuilt: no fixed-SPY observation artifact exists in production, and no Control Card contract exists. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:77,93-94,294-307`; `docs/prd_history/PRD-271.md:59-65` | MATCH | False claims of existing product capability could mislead downstream planning and review. | HIGH |  | no |

## Non-match detail blocks

None. No `MISMATCH` or `PARTIAL` row requires a non-match detail block beyond the documented D2-NS2-02 partial evidence limitation.

## PROPOSED AMENDMENT

None.

No repository files were edited during this dispatch.
