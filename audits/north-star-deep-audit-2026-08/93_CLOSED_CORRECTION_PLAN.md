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

### CP-002 — Open-PR baseline qualifier (surface expanded 2026-08-02, Codex connector finding)
- **Matrix rows:** TM-012 (MISMATCH).
- **Surface:** `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:33-46` (§2 baseline table) **plus every other merge-contingent in-body site referencing PR #187 as open or ratification as pending**, confirmed present at the pinned baseline via `git show fdeef90:...`: line 59 ("**#187 (open)** — this PR: the NS-0B ratification vehicle..."), line 102 ("`[substantially DELIVERED; ratification pending]`" in the §4 dependency graph), and line 444 ("**Ratify** the North Star ledger and this program (NS-0B); merge this branch when satisfied" in §11's held-decisions list). §6's NS-0B row (lines ~274-280, "NOW — COMPLETE UPON DUSTIN'S MERGE OF PR #187... the GOV-0 merge-contingent convention") is a different kind of text — it describes the ratification mechanism itself, which remains accurate regardless of merge timing — and is not part of this correction's surface. The PR-A author must grep the Program (and Ledger, if any parallel mentions exist there) for `#187` and "ratif" before landing this correction, since this list is what verification turned up, not a guaranteed-exhaustive enumeration.
- **Type:** doc fix (qualifier, not a rewrite of the snapshot).
- **Authority:** authoring agent drafts; Dustin merges.
- **Dependencies:** none. **Order:** 1 (rides PR-A).
- **Acceptance test:** every confirmed site above (and any other found by the required grep sweep) carries an explicit note that it predates PR #187's own merge and that PR #187 has since merged as `fdeef90`; PR #184/#185 entries unchanged; TM-011/TM-012 are fully closed with no remaining stale open/pending language for PR #187 itself.
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
- **Authority:** authoring agent drafts; Dustin merges **after** DR-003(ii) confirms the GOV-2-first ordering.
- **Dependencies:** DR-003(ii). **Order:** 2.
- **Acceptance test (corrected 2026-08-02, Codex connector finding — the "absent a recorded exception" carve-out is removed along with DR-003's option (ii-b); GOV-2 §2 provides no exception path):** the Program's NS-2 entry conditions state the GOV-2 §2 order — MATERIAL packet review and exact-head confirmation → design-direction ruling → PRD review → Gate A — with PRD-271's Gate A explicitly positioned per that order; no wording remains that permits Gate A before the packet review.
- **PR boundary:** PR-B. **Ruling prerequisite:** DR-003.

### CP-006 — PRD-228 thread-closure records on PR #187 (corrected three times 2026-08-02, Codex connector findings: the original 10+9 phase split was arithmetic error; comments 14/19 were misfiled with no fixing commit to cite; comments 7/12 were then found misfiled too — both are SUPPORTED-but-unresolved findings, not refuted ones, so a reply can cite the confirming evidence but cannot DISMISS the thread while DR-001/DR-003 remain open)
- **Matrix rows:** TM-081 (primary); closes the reply gap for TM-012, TM-013, TM-014, TM-018, TM-022, TM-025, TM-027, TM-029, TM-032, TM-040, TM-043, TM-046, TM-047, TM-055, TM-070, TM-078 threads.
- **Surface:** PR #187 review threads on GitHub (no repository file diff).
- **Type:** administrative cross-reference fix (in-thread replies per PRD-228).
- **Authority:** agent posts replies; Dustin's plan ratification is the authorizing act (these are exactly the missing administrative records his 2026-08-01/2026-08-02 rulings identified).
- **Three phases, 10+3+4 = 17 determined threads total (matches 9 SUPPORTED + 8 CONTRADICTED/CORRECTED):**
  1. **Dismiss-citing-existing-evidence, 10 comments (2, 4, 6, 8, 9, 14, 15, 19, 20, 21):** no dependency — each reply cites text already present at the pinned baseline showing the comment's concern is refuted or already addressed, so none needs a "fix" to have landed and none is waiting on a Dustin ruling. 4/8/20/21 cite Domain A's own evidence (Program:270-280; CLAUDE.md:290-305; Program:341-347/A-GOV-017; C-059's Program:226-231/stage0-05:78-96); 2/6/9/15 cite a sibling domain's own evidence (TM-032/Ledger; TM-046/Program:182-188; TM-029/Ledger; TM-047/Program:243-256); 14 and 19 cite Ledger:265/§3:74-80 and Ledger:87-90 respectively (both were SUPPORTED findings that Fable's own corrections — TM-013→MATCH, CP-003 withdrawn; TM-014 narrowed, PRD-268's row untouched — showed were already correct at baseline, so no fix exists because none was needed).
  2. **Cite-fixing-commit-SHA, 3 comments, split by which PR each actually needs (corrected 2026-08-02, Codex connector finding — the two PRs are independent corrections and were incorrectly joined):** comments 11 and 29 wait only on PR-A merging (CP-002, CP-004 respectively); comment 18 waits only on PR-B merging (CP-005). Neither sub-group waits on the other PR.
  3. **Ruling-gated, 4 comments (7, 12, 24, 26):** requires DR-001 (7), DR-003 (12), DR-005 (24), or DR-006 (26) to rule before this correction posts any reply for them. Unlike phase 1, comments 7 and 12 are **not** refuted — TM-040/TM-043 confirm their underlying facts (CB-01, CB-07) are real and open — but the comment's actual worry (is the current non-blocking/gating ordering acceptable) is exactly what DR-001/DR-003 decide.
- **Order:** phase 1 = 1 (parallel with PR-A); phase 2 = 3 for comments 11/29 (rides PR-A), 3 for comment 18 (rides PR-B) — these two sub-orders are independent, not sequential; phase 3 = after DR-001/DR-003/DR-005/DR-006 respectively.
- **Acceptance test (taxonomy corrected 2026-08-02, Codex connector finding — PRD-228's disposition set is closed to exactly ACTIONED / DISMISSED / BLOCKED-PARKED; "cite the ruling, not DISMISSED" was an unnamed fourth state):** each of the 13 phase-1/phase-2 threads carries an in-thread reply — phase 1 with a one-line dismissal reason citing the covering text (DISMISSED), phase 2 with a fixing commit SHA/PRD number (ACTIONED); none is closed by GitHub-resolve alone. The 4 phase-3 threads (7, 12, 24, 26) remain `BLOCKED/PARKED` — no reply is posted for any of them — until its ruling lands; the ruling then resolves the thread as `ACTIONED` (if it produces a governed follow-up commit/PRD to cite) or `DISMISSED` (if the ruling itself, cited by decision record, closes the concern with no further repository action) per whichever the ruling's content actually is — this correction cannot predetermine which, only that a reply is not owed before the ruling exists. The 12 remaining routed threads are *not* touched by this correction (they belong to CP-007).
- **PR boundary:** none (no diff). **Ruling prerequisite:** none for phase 1 or phase 2; phase 3 cannot proceed at all until its ruling lands.

### CP-007 — Bounded routed-queue adjudication packet (narrowed and grant-scope corrected 2026-08-02, Codex connector findings)
- **Matrix rows:** TM-080, TM-003 (UNKNOWN); confidence uplifts only for TM-022, TM-036, TM-037, TM-060.
- **Surface:** one new audit artifact under `audits/north-star-deep-audit-2026-08/` (e.g. `94_ROUTED_QUEUE_ADJUDICATION.md`), plus in-thread replies on the 12 remaining routed PR #187 threads (comments 1, 3, 5, 10, 13, 16, 17, 22, 23, 25, 27, 28 — comments 2, 6, 7, 9, 12, 15 were resolved directly in Phase 2 synthesis and removed from this packet's scope, see CP-006 phase 1).
- **Source authority (corrected 2026-08-02, Codex connector findings):** AMENDMENT-002/003/004's literal grants alone are **not sufficient** to adjudicate every remaining comment — several missing sources belong to a domain none of the three amendments touches (comment 3: C-owned `FINDING_STATUS_MATRIX.md`/Program §5; comments 13, 17, 23: B-owned `docs/PROJECT_STATE.md`; comment 25: D1-owned `stage0-01`; comment 27: B-owned Master Ledger §5). This packet's authority is therefore three-part: (i) the AMENDMENT-002/003/004 grants as written (comments 1, 10, 16, 22, and the workplan portions of 13, 27, 28 — seven comments total name the G-owned workplan as part of their missing source; corrected from six, comment 28 added); (ii) **evidence-reuse** of any domain's own already-accepted Phase 1 evidence for a comment whose missing source that domain already owns and cited (comments 3, 13, 17, 23, 25, 27's non-workplan portions); (iii) **one narrow direct-read authorization, TM-003 only:** the pinned baseline `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`, exact path `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`, sections §9 (non-goals) and §10 (stop conditions) — these are Domain A's own manifest-owned sections (Ledger sec 1,2,7,9,10; Program sec 1,9,10,11 | A) for which Phase 1 never dispatched an evidence row, so no prior read exists for (ii) to reuse; this authorization is scoped exactly to Program §§9-10 for TM-003's own check and creates no general source-expansion rule and no grant to any other row or domain. Comment 5's `README.md` component is owned by **no domain** in this audit and is reachable under none of (i)/(ii)/(iii) — it stays UNDETERMINED unless Dustin separately grants it or points to a source.
- **Type:** bounded evidence adjudication + administrative thread closure (no production code).
- **Authority:** Dustin authorizes via DR-007 (including the evidence-reuse and TM-003 direct-read authorizations above); fresh-context agent executes read-only against pinned baseline `fdeef90`; Dustin merges the artifact PR.
- **Dependencies:** DR-007. **Order:** 4.
- **Acceptance test:** every one of the 12 comments receives a recorded substantive determination (SUPPORTED / CONTRADICTED-CORRECTED / still-undeterminable-with-named-reason) and a PRD-228 workflow disposition — comment 5's `README.md` component may legitimately land as still-undeterminable if Dustin does not separately resolve it, which is a closed outcome, not a failed acceptance test; any newly SUPPORTED finding maps to a new bounded correction proposal for Dustin rather than being fixed silently; TM-003's §9/§10 check is recorded MATCH or MISMATCH using the direct read authorized in (iii) above; no source outside the DR-007 grants plus the evidence-reuse and TM-003 direct-read authorizations is read.
- **PR boundary:** PR-E. **Ruling prerequisite:** DR-007 (if Dustin grants selectively, the packet dispositions what its grants plus evidence-reuse reach and records the remainder as BLOCKED/PARKED-by-ruling — still a closed outcome).

### CP-008 — CB-29 status record
- **Matrix rows:** TM-050 (PARTIAL).
- **Surface:** per DR-008's choice — default: `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md` CB-29 row (lines 411-413 region), dated addendum only.
- **Type:** doc fix (registry-of-findings cross-reference), **or no repository change** under DR-008 option (c).
- **Authority:** authoring agent drafts; Dustin merges.
- **Dependencies:** DR-008. **Order:** 4 (any time after its ruling).
- **Acceptance test (corrected 2026-08-02, Codex connector findings):** under (a), a reader of the matrix's CB-29 row is pointed via dated addendum to Program:192-194's superseding PARTIAL status and the merged `f6d508f` delta; under (b), the row is updated in place to PARTIAL with the same pointer; under (c), Dustin has ruled the Program is the sole live-status source and the matrix stays untouched — no PR-C is opened, and CP-008 is satisfied by the ruling record alone. **The ruling record's location depends on timing:** if DR-008 is decided before PR #190's correction plan is ratified, the ruling is recorded in `92_DISPUTE_LOG.md` as originally stated. If DR-008 remains open at ratification, Charter §13 has already frozen `92_DISPUTE_LOG.md` as a historical, non-living record by the time the ruling lands — recording it there is not available. In that case the ruling is instead recorded in a new dated post-ratification decision record, following this audit's existing numbered-file convention (e.g. `95_POST_RATIFICATION_RULINGS.md`, committed via its own PR when the ruling actually lands, not created now), never by editing the frozen `92_DISPUTE_LOG.md`. Under any option and either timing, the missing canonical adoption record remains explicitly listed as CB-29's open residual, unchanged.
- **PR boundary:** PR-C under (a)/(b); none under (c). **Ruling prerequisite:** DR-008.

### CP-009 — Canonical entry-point pointer (discretionary)
- **Matrix rows:** TM-079 (PARTIAL).
- **Surface:** `CLAUDE.md` "Canonical sources" section (and/or `VISION.md` if Dustin prefers): add references to the two North Star documents.
- **Type:** doc fix — governance-adjacent file, so the PR opens as a **draft with the PRD-186 visible hold**, named as governance in its body.
- **Authority:** Dustin decides at review — accepting or declining both close TM-079 (decline = accepted state, PROJECT_STATE's existing pointer bullet deemed sufficient).
- **Dependencies:** none. **Order:** 5 (any time).
- **Acceptance test (corrected 2026-08-02, Codex connector finding — "the frozen matrix's amendment trail" named a mechanism Charter §13 does not define; §13 makes `90` immutable after ratification via a new dated amendment, not an open annotation surface):** either `CLAUDE.md`'s canonical-sources list references both North Star documents, or Dustin closes PR-D with a recorded decline — the closed/declined PR itself is the complete closure evidence for TM-079; no further matrix annotation is required or promised.
- **PR boundary:** PR-D. **Ruling prerequisite:** none formally (the draft-and-hold *is* the decision mechanism).

## Proposed PR sequence (smallest sensible set)

| PR | Contents | Gate |
|---|---|---|
| PR-A | CP-001, CP-002, CP-004 — doc-only North Star status/consistency corrections (CP-003 withdrawn 2026-08-02, moot) | none (Dustin's normal merge) |
| PR-B | CP-005 — NS-2 ordering text | DR-003 |
| PR-C | CP-008 — CB-29 record (conditional: opens only under DR-008 option (a)/(b); under (c) the ruling alone closes CP-008, no PR) | DR-008 |
| PR-D | CP-009 — entry-point pointer (draft + PRD-186 hold) | Dustin's accept/decline at review |
| PR-E | CP-007 — routed-queue adjudication artifact | DR-007 |

CP-006 is thread-administrative and carries no PR of its own (phase 1 immediately; phase 2 after PR-A/PR-B merge). Dependency ordering is exactly `91` §7; no correction depends on another correction except CP-006 phase 2 → {CP-001..CP-005 merged}. Scope is closed: any defect newly surfaced by CP-007 becomes a *proposal to Dustin*, not an automatic extension of this plan.
