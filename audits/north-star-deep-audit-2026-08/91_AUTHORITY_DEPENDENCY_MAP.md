# Authority & Dependency Map (Phase 2 synthesis — Fable)

## 1. Authoritative sources → dependent matrix claims

| Authority (owner domain) | Governs | Matrix rows depending on it |
|---|---|---|
| `docs/PRD_REGISTRY.md` + `docs/prd_index.json` (B) | Canonical PRD lifecycle values | TM-020, TM-021, TM-028, TM-035; qualifier corrections CP-003/CP-004 must defer to it |
| `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` (A) | MATERIAL intake, review order, exact-head confirmation | TM-016, TM-017, TM-018, TM-022, TM-078; CP-005's content |
| `CLAUDE.md` (A) | Landing/review/approval rules; PRD-228 taxonomy; CI-scope statement | TM-005, TM-007, TM-019, TM-025, TM-039, TM-081 |
| `VISION.md` (A) | Mission/non-goals | TM-001, TM-002 |
| Master Ledger / Program (planning docs; **no implementation authority** per TM-007) | Portfolio states, sequencing intent, debt reconciliation prose | TM-011–TM-014, TM-027–TM-037, TM-040–TM-055, TM-063, TM-070; all CP doc fixes land here except CP-008/CP-009 |
| `audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md` + EVIDENCE_INDEX + RECONCILIATION_REPORT (C) | CB-01..47 finding truth | TM-040–TM-051; TM-050's divergence is the one place Program supersedes it (DR-008 decides recording mode) |
| `docs/plans/decision-support-workplan-v0.1.md` + expansion doctrine (G) | Expansion lifecycle states (OPT-0/OPT-1, GEX), vocabulary anchors | TM-071–TM-077; confidence ceiling on TM-022; six TM-080 queue members name it as their missing source |
| stage0 recon set: stage0-01/verify-01 (D1), stage0-02/03/verify (F), stage0-04 (G), stage0-05/verify-05 (A/C split) | As-built evidence bases | TM-056–TM-063, TM-066–TM-069, TM-024, TM-055 |
| `docs/prd_history/PRD-271.md` (E) | ORB defect ownership, Gate A scope | TM-021, TM-031, TM-058 |
| STRATEGY_CANDIDATE_FIDELITY_DELTA (E) | Proxy-count truth | TM-064, TM-065 |
| `docs/PROJECT_STATE.md` (B) | Current-state claims | TM-013 (CB-28), TM-079 |
| PR #187 GitHub metadata (A, snapshot-pinned) | The 29 threads | TM-080, TM-081 |

## 2. What can proceed WITHOUT Dustin (beyond his standard merge of each PR)

- **PR-A (CP-001…CP-004):** doc-only corrections whose content is fully adjudicated from evidence; no open ruling consumed. Dustin's act is the normal GOV-1 merge.
- **CP-006 phase 1:** in-thread replies for the four refuted threads (comments 4, 8, 20, 21), citing Program:270-280, CLAUDE.md:290-305, Program:341-347/A-GOV-017 evidence, and C-059's evidence respectively — this is exactly the missing administrative record Dustin's 2026-08-01 ruling identified.
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
| CP-007 (routed-queue adjudication) and confidence uplifts for TM-022/TM-036/TM-060/TM-003 | AMENDMENT-002/003/004 grant rulings + authorization of the bounded triage packet | DR-007 |
| CP-008 (CB-29 record) | frozen-snapshot-plus-addendum vs in-place matrix update | DR-008 |

## 4. Parked administration (holds that are NOT substantive blockers)

- All **29** PR #187 threads: BLOCKED/PARKED per Dustin's rulings — the 4 refuted and 18 undetermined holds are administrative record-keeping states only (settled rules 4–5). They block nothing in Phase 2/3.
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
PR-A (CP-001,002,003,004)      — no prerequisites
   └─ CP-006 phase 2 (SUPPORTED-thread replies cite PR-A/PR-B SHAs)
DR-003 ── PR-B (CP-005) ───────┘
DR-007 ── PR-E (CP-007: routed-queue adjudication artifact; may also close TM-003)
DR-008 ── PR-C (CP-008: CB-29 record)
(discretionary) PR-D (CP-009: entry-point pointer; PRD-186 draft+hold)
CP-006 phase 1 (4 refuted threads) — independent, may run first
```
No correction depends on any other correction except CP-006-phase-2 → {CP-001..005 merged}. No cycle exists.
