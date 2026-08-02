# Authority & Dependency Map (Phase 2 synthesis — Fable)

## 1. Authoritative sources → dependent matrix claims

| Authority (owner domain) | Governs | Matrix rows depending on it |
|---|---|---|
| `docs/PRD_REGISTRY.md` + `docs/prd_index.json` (B) | Canonical PRD lifecycle values | TM-020, TM-021, TM-028, TM-035; qualifier correction CP-004 must defer to it |
| `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` (A) | MATERIAL intake, review order, exact-head confirmation | TM-016, TM-017, TM-018, TM-022, TM-078; CP-005's content |
| `CLAUDE.md` (A) | Landing/review/approval rules; PRD-228 taxonomy; CI-scope statement | TM-005, TM-007, TM-019, TM-025, TM-039, TM-081 |
| `VISION.md` (A) | Mission/non-goals | TM-001, TM-002 |
| Master Ledger / Program (planning docs; **no implementation authority** per TM-007) | Portfolio states, sequencing intent, debt reconciliation prose | TM-011–TM-014, TM-027–TM-037, TM-040–TM-055, TM-063, TM-070; all CP doc fixes land here except CP-008/CP-009 |
| `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md` + EVIDENCE_INDEX + RECONCILIATION_REPORT (C) | CB-01..47 finding truth | TM-040–TM-051; TM-050's divergence is the one place Program supersedes it (DR-008 decides recording mode) |
| `docs/plans/decision-support-workplan-v0.1.md` + expansion doctrine (G) | Expansion lifecycle states (OPT-0/OPT-1, GEX), vocabulary anchors | TM-071–TM-077; confidence ceiling on TM-022; seven TM-080 queue members name it as their missing source (corrected 2026-08-02, Codex connector finding — comment 28 was omitted; the full set is comments 1, 10, 13, 16, 22, 27, 28) |
| stage0 recon set: stage0-01/verify-01 (D1), stage0-02/03/verify (F), stage0-04 (G), stage0-05/verify-05 (A/C split) | As-built evidence bases | TM-056–TM-063, TM-066–TM-069, TM-024, TM-055 |
| `docs/prd_history/PRD-271.md` (E) | ORB defect ownership, Gate A scope | TM-021, TM-031, TM-058 |
| STRATEGY_CANDIDATE_FIDELITY_DELTA (E) | Proxy-count truth | TM-064, TM-065 |
| `docs/PROJECT_STATE.md` (B) | Current-state claims | TM-013 (CB-28), TM-079 |
| PR #187 GitHub metadata (A, snapshot-pinned) | The 29 threads | TM-080, TM-081 |

## 2. What can proceed WITHOUT Dustin (beyond his standard merge of each PR)

- **PR-A (CP-001…CP-004):** doc-only corrections whose content is fully adjudicated from evidence; no open ruling consumed. Dustin's act is the normal GOV-1 merge.
- **CP-006 phase 1:** in-thread replies for all 10 refuted threads, no dependency — comments 4, 8, 20, 21 (Domain A's own evidence: Program:270-280, CLAUDE.md:290-305, Program:341-347/A-GOV-017, C-059); comments 2, 6, 9, 15 (a sibling domain's own cited evidence: TM-032/TM-046/TM-029/TM-047); and comments 14, 19 (added 2026-08-02, Codex connector finding, reclassified CONTRADICTED/CORRECTED 2026-08-02 per a second Codex connector finding — both cite Ledger:265/§3:74-80 and Ledger:87-90 respectively, and Fable's own corrections showed each comment's underlying claim was false at baseline: PRD-268's row already read `IN PROGRESS / DECISION REQUIRED`, and the NS-0A exit already discloses CB-28) — this is exactly the missing administrative record Dustin's 2026-08-01 ruling identified. (Comments 7 and 12 are NOT in this phase — they are cross-domain-*confirmed*, not refuted, via TM-040/TM-043, and stay BLOCKED/PARKED pending DR-001/DR-003; see §7.)
- **CP-009 drafting** (PR-D opens as a draft with the PRD-186 visible hold; Dustin accepts or declines).

## 3. What CANNOT proceed without Dustin

| Item | Blocking decision | DR |
|---|---|---|
| Any runway promotion (NS-2 slice or CB-02 resume) | Option A/B runway ruling + explicit CB-01 deferral or scheduling | DR-001 |
| PRD-268 resolution / L0 closure | approve / return-to-PROPOSED / deprecate | DR-002 |
| NS-2B, any ORB remedy, CB-07 closure, CP-005 landing | PRD-271 Gate A + confirmation of GOV-2-first ordering | DR-003 |
| CB-02/OPT-0/OPT-1/ODATA chain | OPT-0 carrier/reason-semantics/seam approval + exact-head confirmation | DR-004 |
| Governance precedent for PR #187 | MATERIAL-intake classification of PR #187 itself | DR-005 |
| NS-9C-vs-NS-2 freshness sequencing | promote/split NS-9C vs compatibility-note default | DR-006 |
| CP-007 (routed-queue adjudication, narrowed to 11 comments 2026-08-02) and confidence uplifts for TM-022/TM-036/TM-037/TM-060/TM-003 | AMENDMENT-002/003/004 grant rulings + authorization of the bounded triage packet | DR-007 |
| CP-008 (CB-29 record) | frozen-snapshot-plus-addendum vs in-place matrix update | DR-008 |

## 4. Parked administration (holds that are NOT substantive blockers)

- All **29** PR #187 threads: BLOCKED/PARKED per Dustin's rulings — administrative record-keeping states only (settled rules 4–5), regardless of substantive determination. Corrected three times 2026-08-02 (Codex connector findings — stale pre-reconciliation counts; then comment 17 found misfiled UNDETERMINED though TM-011 already establishes its MISMATCH; then comments 14/19 found misfiled SUPPORTED though both were dismissed on existing, contradicting Ledger evidence): the final substantive split is **8 SUPPORTED, 10 CONTRADICTED/CORRECTED, 11 UNDETERMINED** (8+10+11=29). None of the three groups is a substantive blocker; see TM-081/CP-006 for the 18 determined threads' reply phasing and CP-007 for the 11 routed ones.
- **AMENDMENT-005** (Domain F): open PROPOSED, gates nothing (F's own text: "neither is needed for F's current scope"). Recommended disposition: defer/decline; carried inside DR-007's ruling for one-touch closure.
- Deferred owner decisions in §5 below — tracked debt, no pending question in this audit.

## 5. Dustin-held decisions that are deferred by design (tracked, not disputes)

1. Macro-awareness track: keep-dormant / promote / retire (TM-052, C-055).
2. Strategy-side fidelity disposition / corrected frozen run (TM-065, E-08/E-09).
3. Q27 model-role lane ratification when its trigger occurs; Q28 protocol creation if ever wanted (TM-024).
4. CB-16 sidecar-doctrine contradiction ruling (TM-048, C-017).
5. NS-3 / NS-4-residual / NS-6-path / NS-7 vocabulary ratification — owed at each track's future GOV-2 packet intake, per Domain G's methodology (TM-073–TM-076).

## 6. Genuine substantive implementation blockers (current product work)

Exactly four, all Dustin-held gates rather than unresolved facts: **CB-01** (open Critical safety bypass — gates runway, DR-001); **PRD-268/L0** (gates CB-02 chain, DR-002); **PRD-271 Gate A / CB-07** (gates NS-2, DR-003); **OPT-0 approvals** (gates CB-02/OPT-1/ODATA, DR-004).

## 7. Correction dependency ordering

```
PR-A (CP-001,002,004)          — no prerequisites (CP-003 withdrawn 2026-08-02, moot)
   └─ CP-006 phase 2, comments 11, 17, and 29 (cite PR-A's fixing SHAs)
DR-003 ── PR-B (CP-005)
   └─ CP-006 phase 2, comment 18 only (cites PR-B's fixing SHA)

(corrected twice 2026-08-02, Codex connector findings: the two PR-A/PR-B
edges above were previously joined at one node, implying all three phase-2
replies waited on both PRs; comment 18 depends only on PR-B, comments 11/29
depend only on PR-A — neither sub-group depends on the other PR; comment 17
was then added to the PR-A sub-group — TM-011 already establishes its
MISMATCH with a fix routed through CP-001/PR-A, so its reply rides the same
fixing SHA as 11/29)

DR-001 ── CP-006 phase 3 (comment 7 reply)
DR-003 ── CP-006 phase 3 (comment 12 reply)
DR-005 ── CP-006 phase 3 (comment 24 reply)
DR-006 ── CP-006 phase 3 (comment 26 reply)

DR-007 ── PR-E (CP-007: routed-queue adjudication artifact, 11 comments; may also close TM-003)
DR-008 ── PR-C (CP-008: CB-29 record)
(discretionary) PR-D (CP-009: entry-point pointer; PRD-186 draft+hold)
CP-006 phase 1 (10 refuted/cross-domain-refuted threads: 2,4,6,8,9,14,15,19,20,21) — independent, may run first, no ruling prerequisite
```
Corrected five times 2026-08-02 (Codex connector findings): CP-006 phase 2's original nine-comment framing was arithmetic error; comments 14/19 moved to phase 1 (dismissed on existing baseline evidence, no fixing commit exists; reclassified CONTRADICTED/CORRECTED, not SUPPORTED — their claims were false at baseline, not merely already satisfied); comments 7/12 then moved out of phase 1 into a four-comment phase 3 alongside 24/26 — DR-001 (7) and DR-003 (12) join DR-005/DR-006 as required rulings, since 7/12 are SUPPORTED-but-unresolved (the underlying fact is confirmed, but the ordering question the comment raises is exactly what those DRs decide) rather than refuted; comment 17 was then moved out of TM-080's UNDETERMINED queue into phase 2's PR-A sub-group — TM-011 already establishes its MISMATCH, so no ruling or new evidence was needed, only correct filing. No correction depends on any other correction except CP-006-phase-2 → {CP-001,002,004,005 merged}; phase 3 depends on rulings, not corrections. No cycle exists.
