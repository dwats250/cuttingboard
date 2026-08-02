# Closed Correction Plan (Phase 2 synthesis — Fable)

**Closure statement.** Every non-accepted matrix state has exactly one disposition. The 3 MISMATCH rows map to CP-001, CP-002, CP-005. The 10 PARTIAL rows: TM-013→CP-003, TM-014→CP-004, TM-050→CP-008, TM-079→CP-009; TM-036, TM-037, TM-060, TM-070, TM-078 are **resolved by ruling only** (DR-007, DR-004, DR-007, DR-006, DR-005 respectively — no repository defect to correct; each is either an accepted confidence ceiling or a held owner decision); TM-075 is **no correction needed** — deferred by Domain G's own methodology to NS-4's future GOV-2 intake. The 5 UNKNOWN rows: TM-003 and TM-080→CP-007; TM-073, TM-074, TM-076 are **no correction needed** — deferred to their tracks' future packet intakes, same basis as TM-075. There is no open-ended "investigate further" bucket: the only investigation item (CP-007) is a single bounded packet whose scope is the 18 named comments plus the two named Program sections, gated explicitly on DR-007. This plan describes future bounded PRs; it implements nothing now.

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

### CP-003 — NS-0A exit qualifier / CB-28 consistency
- **Matrix rows:** TM-013 (PARTIAL).
- **Surface:** `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` NS-0A row (sec 4, within lines 84-100); `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` NS-0A/source-map wording as needed; optionally `docs/PROJECT_STATE.md:28` ("Active PRD: none in progress" → qualified wording).
- **Type:** doc fix / cross-reference fix.
- **Authority:** authoring agent drafts; Dustin merges. Content: qualify NS-0A's exit as "complete except the CB-28 active-PRD-wording disagreement, tracked open" (the treatment C-029 and B-005's corrected detail block already agree on) — not a resolution of CB-28 itself.
- **Dependencies:** none. **Order:** 1 (rides PR-A).
- **Acceptance test:** NS-0A's exit text and the CB-28 debt record no longer contradict (the exit names CB-28 as its open residual); if PROJECT_STATE.md:28 is touched, it reads as a scoped statement consistent with four IN PROGRESS registry rows.
- **PR boundary:** PR-A. **Ruling prerequisite:** none (CB-28 stays open Low debt; no new ruling consumed).

### CP-004 — Lifecycle-axis qualifiers and legend
- **Matrix rows:** TM-014 (PARTIAL).
- **Surface:** `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` sec 5 rows for PRD-271 (line 263 region) and PRD-268 (line 265 region), plus a one-line axis legend in sec 5's preamble.
- **Type:** doc fix.
- **Authority:** authoring agent drafts; Dustin merges. Content: PRD-271 → "IN PROGRESS (registry lifecycle) / BLOCKED = Gate A pending, dependency condition not a lifecycle value"; PRD-268 → "IN PROGRESS / DECISION REQUIRED"; legend states rank, lifecycle, and dependency-condition are separate axes (harmonizes with B-003/C-049/C-051/C-053 and answers comments 14/29 exactly).
- **Dependencies:** none. **Order:** 1 (rides PR-A).
- **Acceptance test:** grep of the Ledger finds no unqualified `BLOCKED`/`PARKED` for PRD-271/PRD-268; registry values remain untouched and authoritative; Program's "changes no lifecycle status" promise is textually consistent with every Ledger row it companions.
- **PR boundary:** PR-A. **Ruling prerequisite:** none.

### CP-005 — NS-2 entry-condition ordering aligned to GOV-2
- **Matrix rows:** TM-018 (MISMATCH).
- **Surface:** `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:110-116` and `:297-307` (NS-2 entry conditions).
- **Type:** doc fix (sequencing text).
- **Authority:** authoring agent drafts; Dustin merges **after** DR-003(ii) confirms the GOV-2-first ordering (or records a documented exception, in which case CP-005 instead encodes that exception).
- **Dependencies:** DR-003(ii). **Order:** 2.
- **Acceptance test:** the Program's NS-2 entry conditions state the GOV-2 §2 order — MATERIAL packet review and exact-head confirmation → design-direction ruling → PRD review → Gate A — with PRD-271's Gate A explicitly positioned per the ruling; no wording remains that permits Gate A before the packet review absent a recorded exception.
- **PR boundary:** PR-B. **Ruling prerequisite:** DR-003.

### CP-006 — PRD-228 thread-closure records on PR #187
- **Matrix rows:** TM-081 (primary); closes the reply gap for TM-012, TM-013, TM-014, TM-018, TM-022, TM-025, TM-027, TM-055, TM-070, TM-078 threads.
- **Surface:** PR #187 review threads on GitHub (no repository file diff).
- **Type:** administrative cross-reference fix (in-thread replies per PRD-228).
- **Authority:** agent posts replies; Dustin's plan ratification is the authorizing act (these are exactly the missing administrative records his 2026-08-01/2026-08-02 rulings identified).
- **Dependencies:** phase 1 (comments 4, 8, 20, 21): none — replies cite the already-present refuting text (Program:270-280; CLAUDE.md:290-305; Program:341-347; C-059's Program:226-231/stage0-05:78-96 evidence). Phase 2 (comments 11, 14, 19, 29 and — after PR-B — 18; 24 and 26 after DR-005/DR-006 rule): requires PR-A/PR-B merged so replies cite fixing commit SHAs.
- **Order:** phase 1 = 1 (parallel with PR-A); phase 2 = 3.
- **Acceptance test:** each of the 11 determined threads carries an in-thread reply with either a fixing commit SHA/PRD number (ACTIONED) or a one-line dismissal reason citing the covering text (DISMISSED); none is closed by GitHub-resolve alone; the 18 routed threads are *not* touched by this correction (they belong to CP-007).
- **PR boundary:** none (no diff). **Ruling prerequisite:** none for phases as scoped (comment-24/26 replies wait for DR-005/DR-006 outcomes).

### CP-007 — Bounded routed-queue adjudication packet
- **Matrix rows:** TM-080, TM-003 (UNKNOWN); confidence uplifts only for TM-022, TM-036, TM-060.
- **Surface:** one new audit artifact under `audits/north-star-deep-audit-2026-08/` (e.g. `94_ROUTED_QUEUE_ADJUDICATION.md`), plus in-thread replies on the 18 routed PR #187 threads; sources read strictly per the DR-007 grants (each comment's missing source is already named in its A-PR187 row; TM-003's scope is Program §9/§10, already A-owned).
- **Type:** bounded evidence adjudication + administrative thread closure (no production code).
- **Authority:** Dustin authorizes via DR-007; fresh-context agent executes read-only against pinned baseline `fdeef90`; Dustin merges the artifact PR.
- **Dependencies:** DR-007. **Order:** 4.
- **Acceptance test:** every one of the 18 comments receives a recorded substantive determination (SUPPORTED / CONTRADICTED-CORRECTED / still-undeterminable-with-named-reason) and a PRD-228 workflow disposition; any newly SUPPORTED finding maps to a new bounded correction proposal for Dustin rather than being fixed silently; TM-003's §9/§10 check is recorded MATCH or MISMATCH; no source outside the DR-007 grants is read.
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
| PR-A | CP-001, CP-002, CP-003, CP-004 — doc-only North Star status/consistency corrections | none (Dustin's normal merge) |
| PR-B | CP-005 — NS-2 ordering text | DR-003 |
| PR-C | CP-008 — CB-29 record | DR-008 |
| PR-D | CP-009 — entry-point pointer (draft + PRD-186 hold) | Dustin's accept/decline at review |
| PR-E | CP-007 — routed-queue adjudication artifact | DR-007 |

CP-006 is thread-administrative and carries no PR of its own (phase 1 immediately; phase 2 after PR-A/PR-B merge). Dependency ordering is exactly `91` §7; no correction depends on another correction except CP-006 phase 2 → {CP-001..CP-005 merged}. Scope is closed: any defect newly surfaced by CP-007 becomes a *proposal to Dustin*, not an automatic extension of this plan.
