# Closed Correction Plan (Phase 2 synthesis — Fable)

**Closure statement (updated 2026-08-02, Codex connector findings applied).** Every non-accepted matrix state has exactly one disposition. TM-013 reclassified PARTIAL→MATCH — CP-003 **withdrawn as moot** (the Ledger's own NS-0A exit text already discloses CB-28; no repository correction needed), ID preserved below for audit-trail continuity only. The 3 MISMATCH rows map to CP-001, CP-002, CP-005. The 9 remaining PARTIAL rows: TM-014→CP-004 (narrowed to PRD-271 only), TM-050→CP-008, TM-079→CP-009; TM-036, TM-037, TM-060, TM-070, TM-078 are **resolved by ruling only** (DR-007, DR-004+DR-007, DR-007, DR-006, DR-005 respectively — no repository defect to correct; each is either an accepted confidence ceiling or a held owner decision); TM-075 is **no correction needed** — deferred by Domain G's own methodology to NS-4's future GOV-2 intake. The 5 UNKNOWN rows: TM-003 and TM-080→CP-007 (narrowed to 12 comments); TM-073, TM-074, TM-076 are **no correction needed** — deferred to their tracks' future packet intakes, same basis as TM-075. There is no open-ended "investigate further" bucket: the only investigation item (CP-007) is a single bounded packet whose scope is the 12 named comments plus the two named Program sections, gated explicitly on DR-007. This plan describes future bounded PRs; it implements nothing now.

## Corrections

### CP-001 — Post-merge status banners
- **Matrix rows:** TM-011 (MISMATCH).
- **Surface:** `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` (preamble, lines 1-12 region, and the closing status text near lines 425-429); `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (preamble, lines 1-15 region).
- **Type:** doc fix.
- **Authority:** authoring agent drafts; Dustin merges (GOV-1). Content per A-GOV-009's proposed disposition ("ratified as of merge `fdeef90`, 2026-08-02"); no lifecycle or portfolio content touched.
- **Dependencies:** none. **Order:** 1.
- **Acceptance test:** neither document contains "DRAFT UNTIL MERGE" or awaiting-ratification language; each preamble states ratified status naming merge commit `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`.
- **PR boundary:** PR-A. **Ruling prerequisite:** none.

### CP-002 — Open-PR baseline qualifier
- **Matrix rows:** TM-012 (MISMATCH).
- **Surface:** `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:33-46` (§2 baseline table).
- **Type:** doc fix (qualifier, not a rewrite of the snapshot).
- **Authority:** authoring agent drafts; Dustin merges.
- **Dependencies:** none. **Order:** 1 (rides PR-A).
- **Acceptance test:** the §2 table carries an explicit note that its open-PR snapshot predates PR #187's own merge and that PR #187 has since merged as `fdeef90`; PR #184/#185 entries unchanged.
- **PR boundary:** PR-A. **Ruling prerequisite:** none.

### CP-003 — WITHDRAWN 2026-08-02 (Codex connector finding, verified)
- **Matrix rows:** TM-013 (reclassified PARTIAL→MATCH).
- **Reason:** `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:87-90` (NS-0A exit, verified via `git show fdeef90:...`) already reads "...agree or are explicitly recorded as open debt (CB-28: the `PROJECT_STATE` 'Active PRD: none' line vs four `IN PROGRESS` registry rows)" — the exit already names and qualifies CB-28 inline. The originally proposed correction was moot; no repository defect exists at this row. CB-28 itself remains valid open Low debt, tracked unchanged in Domain C's own record (C-029) — this withdrawal does not touch or resolve CB-28.
- **ID preserved, not reused,** for audit-trail continuity with the original synthesis and the connector review thread that identified the error.

### CP-004 — PRD-271 lifecycle-vocabulary clarifying note (narrowed 2026-08-02, Codex connector finding)
- **Matrix rows:** TM-014 (PARTIAL).
- **Surface:** `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` sec 5 PRD-271 row only (line 263 region).
- **Type:** doc fix.
- **Authority:** authoring agent drafts; Dustin merges. Content: add an inline note to PRD-271's row distinguishing the Ledger's own lifecycle-condition value `BLOCKED` (Gate A pending; §3's local vocabulary) from the registry's separate PRD-lifecycle field (`IN PROGRESS`), so the two are not read as conflicting values on one axis (answers comment 29 exactly; matches A-GOV-012's own HIGH-risk flag).
- **Scope correction:** PRD-268's row (`IN PROGRESS / DECISION REQUIRED`) is **not touched** — verified already correct at the pinned baseline; the original claim that it read `PARKED` was false, as was the claim that no axis legend exists (one is already present at Ledger §3 lines 74-80). Both claims are removed from TM-014 and this correction; no legend addition is needed.
- **Dependencies:** none. **Order:** 1 (rides PR-A).
- **Acceptance test:** PRD-271's Ledger row carries the clarifying note; PRD-268's row and Ledger §3 are unchanged; registry values remain untouched and authoritative.
- **PR boundary:** PR-A. **Ruling prerequisite:** none.

### CP-005 — NS-2 entry-condition ordering aligned to GOV-2
- **Matrix rows:** TM-018 (MISMATCH).
- **Surface:** `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:110-116` and `:297-307` (NS-2 entry conditions).
- **Type:** doc fix (sequencing text).
- **Authority:** authoring agent drafts; Dustin merges **after** DR-003(ii) confirms the GOV-2-first ordering (or records a documented exception, in which case CP-005 instead encodes that exception).
- **Dependencies:** DR-003(ii). **Order:** 2.
- **Acceptance test:** the Program's NS-2 entry conditions state the GOV-2 §2 order — MATERIAL packet review and exact-head confirmation → design-direction ruling → PRD review → Gate A — with PRD-271's Gate A explicitly positioned per the ruling; no wording remains that permits Gate A before the packet review absent a recorded exception.
- **PR boundary:** PR-B. **Ruling prerequisite:** DR-003.

### CP-006 — PRD-228 thread-closure records on PR #187 (expanded 2026-08-02, Codex connector finding)
- **Matrix rows:** TM-081 (primary); closes the reply gap for TM-012, TM-014, TM-018, TM-022, TM-025, TM-027, TM-029, TM-032, TM-040, TM-043, TM-046, TM-047, TM-055, TM-070, TM-078 threads.
- **Surface:** PR #187 review threads on GitHub (no repository file diff).
- **Type:** administrative cross-reference fix (in-thread replies per PRD-228).
- **Authority:** agent posts replies; Dustin's plan ratification is the authorizing act (these are exactly the missing administrative records his 2026-08-01/2026-08-02 rulings identified).
- **Dependencies:** phase 1, 10 comments (2, 4, 6, 7, 8, 9, 12, 15, 20, 21): none — each reply cites already-present evidence, either Domain-A-owned text (4, 8, 20, 21) or a sibling domain's own cited evidence within this matrix (2→TM-032/Ledger; 6→TM-046/Program:182-188; 7→TM-040/FINDING_STATUS_MATRIX; 9→TM-029/Ledger; 12→TM-043/Program; 15→TM-047/Program:243-256). Phase 2, 9 comments (11, 14, 18, 19, 29 need only PR-A/PR-B merged for a fixing-commit-SHA reply; 24 additionally needs DR-005 to rule; 26 additionally needs DR-006 to rule).
- **Order:** phase 1 = 1 (parallel with PR-A); phase 2 = 3 (comments 11/14/18/19/29), or after DR-005/DR-006 respectively (comments 24/26).
- **Acceptance test:** each of the 19 determined threads (10 phase-1 + 9 phase-2) carries an in-thread reply with either a fixing commit SHA/PRD number (ACTIONED) or a one-line dismissal reason citing the covering text (DISMISSED); none is closed by GitHub-resolve alone; the 12 remaining routed threads are *not* touched by this correction (they belong to CP-007).
- **PR boundary:** none (no diff). **Ruling prerequisite:** none for phase 1 or for comments 11/14/18/19/29 in phase 2; comments 24/26 wait for DR-005/DR-006 respectively.

### CP-007 — Bounded routed-queue adjudication packet (narrowed 2026-08-02, Codex connector finding)
- **Matrix rows:** TM-080, TM-003 (UNKNOWN); confidence uplifts only for TM-022, TM-036, TM-037, TM-060.
- **Surface:** one new audit artifact under `audits/north-star-deep-audit-2026-08/` (e.g. `94_ROUTED_QUEUE_ADJUDICATION.md`), plus in-thread replies on the 12 remaining routed PR #187 threads (comments 1, 3, 5, 10, 13, 16, 17, 22, 23, 25, 27, 28 — comments 2, 6, 7, 9, 12, 15 were resolved directly in Phase 2 synthesis and removed from this packet's scope, see CP-006 phase 1); sources read strictly per the DR-007 grants (each comment's missing source is already named in its A-PR187 row; TM-003's scope is Program §9/§10, already A-owned).
- **Type:** bounded evidence adjudication + administrative thread closure (no production code).
- **Authority:** Dustin authorizes via DR-007; fresh-context agent executes read-only against pinned baseline `fdeef90`; Dustin merges the artifact PR.
- **Dependencies:** DR-007. **Order:** 4.
- **Acceptance test:** every one of the 12 comments receives a recorded substantive determination (SUPPORTED / CONTRADICTED-CORRECTED / still-undeterminable-with-named-reason) and a PRD-228 workflow disposition; any newly SUPPORTED finding maps to a new bounded correction proposal for Dustin rather than being fixed silently; TM-003's §9/§10 check is recorded MATCH or MISMATCH; no source outside the DR-007 grants is read.
- **PR boundary:** PR-E. **Ruling prerequisite:** DR-007 (if Dustin grants selectively, the packet dispositions what its grants reach and records the remainder as BLOCKED/PARKED-by-ruling — still a closed outcome).

### CP-008 — CB-29 status record
- **Matrix rows:** TM-050 (PARTIAL).
- **Surface:** per DR-008's choice — default: `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md` CB-29 row (lines 411-413 region), dated addendum only.
- **Type:** doc fix (registry-of-findings cross-reference).
- **Authority:** authoring agent drafts; Dustin merges.
- **Dependencies:** DR-008. **Order:** 4 (any time after its ruling).
- **Acceptance test:** a reader of the matrix's CB-29 row is pointed, via dated addendum (or the in-place update if Dustin so rules), to Program:192-194's superseding PARTIAL status and the merged `f6d508f` delta; the missing canonical adoption record remains explicitly listed as CB-29's open residual, unchanged.
- **PR boundary:** PR-C. **Ruling prerequisite:** DR-008.

### CP-009 — Canonical entry-point pointer (discretionary)
- **Matrix rows:** TM-079 (PARTIAL).
- **Surface:** `CLAUDE.md` "Canonical sources" section (and/or `VISION.md` if Dustin prefers): add references to the two North Star documents.
- **Type:** doc fix — governance-adjacent file, so the PR opens as a **draft with the PRD-186 visible hold**, named as governance in its body.
- **Authority:** Dustin decides at review — accepting or declining both close TM-079 (decline = accepted state, PROJECT_STATE's existing pointer bullet deemed sufficient).
- **Dependencies:** none. **Order:** 5 (any time).
- **Acceptance test:** either `CLAUDE.md`'s canonical-sources list references both North Star documents, or the PR is closed by Dustin with a recorded decline and TM-079's disposition is annotated accepted-as-is in the frozen matrix's amendment trail.
- **PR boundary:** PR-D. **Ruling prerequisite:** none formally (the draft-and-hold *is* the decision mechanism).

## Proposed PR sequence (smallest sensible set)

| PR | Contents | Gate |
|---|---|---|
| PR-A | CP-001, CP-002, CP-004 — doc-only North Star status/consistency corrections (CP-003 withdrawn 2026-08-02, moot) | none (Dustin's normal merge) |
| PR-B | CP-005 — NS-2 ordering text | DR-003 |
| PR-C | CP-008 — CB-29 record | DR-008 |
| PR-D | CP-009 — entry-point pointer (draft + PRD-186 hold) | Dustin's accept/decline at review |
| PR-E | CP-007 — routed-queue adjudication artifact | DR-007 |

CP-006 is thread-administrative and carries no PR of its own (phase 1 immediately; phase 2 after PR-A/PR-B merge). Dependency ordering is exactly `91` §7; no correction depends on another correction except CP-006 phase 2 → {CP-001..CP-005 merged}. Scope is closed: any defect newly surfaced by CP-007 becomes a *proposal to Dustin*, not an automatic extension of this plan.
