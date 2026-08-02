# Domain A — Governance, authority, materiality

## Header
- Baseline SHA: `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`
- Accepted scaffold seam SHA: `e0d481f4e3daeae9d8cba4a7aee7670d27b5a2b5`
- Authorized Phase 1 execution-contract SHA: `41bfcd6888b7c28da9c0478c9534bdb66a9a2600`
- Assigned domain: A
- Dispatch parameters (verbatim from `01_SOURCE_AUTHORITY_MANIFEST.md`):

- OWNED: `CLAUDE.md`; `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md`;
  `docs/DECISIONS.md`; `docs/sidecar_doctrine.md`; `docs/architecture.md`;
  `docs/AGENT_WORKFLOW.md`; `docs/CLAUDE_HOOKS.md`; `docs/PRD_PROCESS.md`;
  `.claude/settings.json`; `docs/PRD_TEMPLATE.md`; `docs/PRD_REVIEW_TEMPLATE.md`;
  `docs/plans/agent-work-charge-template-v0.1.md`; `VISION.md`;
  `audits/current-state-reconciliation-2026-07-30/CHARTER.md`; Master
  Ledger sec 1, 2, 7, 9, 10; Program sec 1, 9, 10, 11;
  `audits/stage0-recon-2026-07-20/stage0-05-governance-debt-v0.1.md`
  "## Governance" section (Q27-28) only; **PR #187 provenance and
  connector-thread evidence** — merge SHA/file list/body are fixed since
  the PR is closed/merged (`git show`-verifiable as repository facts per
  Charter §4-§5); the 28 inline review comments, their reply threads, any
  cited fixing SHA/PRD, and any explicit dismissal reason are read live at
  dispatch time via `gh api repos/dwats250/cuttingboard/pulls/187/comments`
  and `gh api repos/dwats250/cuttingboard/issues/187/comments` (0 found at
  scaffold time) — this is GitHub-hosted PR metadata, not a repository
  path, so it is not `git show`-pinned; if a new reply appears on PR #187
  after Domain A's dispatch captures its evidence snapshot, that is newer
  material routed to the Amendments Log per Charter §2, never silently
  substituted in. GitHub's `isResolved`/`isOutdated` fields are read as
  workflow metadata only, never as a PRD-228 disposition by themselves
  (Charter §5).
- CITED: `docs/PRD_REGISTRY.md` + `docs/prd_index.json` (owned by B, cited
  by all — PRD-number lookups only); Program sec 2, 3, 4, 6, 7 (owned by B,
  cited by all); `audits/stage0-recon-2026-07-20/verify-05-governance-debt.md`
  (owned by C) — its Q27-28 per-question disposition sub-entries only, not
  the whole file.
- EXCLUDED BY DEFAULT: `.claude/settings.local.json` — untracked, absent
  from baseline, not a valid pinned-commit read (see note above). No other
  exclusions — broadest domain by design.
- **PR #187 evidence pin:** the dispatch parameters above (verbatim from
  the manifest) describe "the 28 inline review comments" — that phrasing
  reflects Phase 0's capture point. The immutable capture this dispatch
  actually used is `domains/PR187_EVIDENCE_SNAPSHOT_2026-08-02.md`,
  captured `2026-08-02T04:12:33Z`. It records 29 comments: a 29th (id
  `3696977973`) was posted at `2026-08-02T00:08:09Z`, 37 seconds after PR
  #187's merge and after Phase 0's capture — not a Phase 0 undercount, a
  later addition. This snapshot's 29-comment count is what feeds the
  evidence table below, not the manifest's "28" phrasing.

Files inspected:

- `audits/north-star-deep-audit-2026-08/00_AUDIT_CHARTER.md`
- `audits/north-star-deep-audit-2026-08/01_SOURCE_AUTHORITY_MANIFEST.md`
- `audits/north-star-deep-audit-2026-08/domains/PR187_EVIDENCE_SNAPSHOT_2026-08-02.md`
- `CLAUDE.md`
- `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md`
- `docs/DECISIONS.md`
- `docs/sidecar_doctrine.md`
- `docs/architecture.md`
- `docs/AGENT_WORKFLOW.md`
- `docs/CLAUDE_HOOKS.md`
- `docs/PRD_PROCESS.md`
- `.claude/settings.json`
- `docs/PRD_TEMPLATE.md`
- `docs/PRD_REVIEW_TEMPLATE.md`
- `docs/plans/agent-work-charge-template-v0.1.md`
- `VISION.md`
- `audits/current-state-reconciliation-2026-07-30/CHARTER.md`
- `audits/stage0-recon-2026-07-20/stage0-05-governance-debt-v0.1.md`
- `docs/PRD_REGISTRY.md`
- `docs/prd_index.json`
- `audits/stage0-recon-2026-07-20/verify-05-governance-debt.md`
- `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`
- `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`

Files intentionally excluded:

- `.claude/settings.local.json` — untracked and absent from the pinned baseline; not valid pinned-commit evidence.

Completion status: COMPLETE — every OWNED source inspected, every CITED source consulted, every EXCLUDED-BY-DEFAULT item documented, evidence table fully populated for in-scope assertions with no blank rows; out-of-scope dependencies correctly routed to the unchanged PROPOSED AMENDMENT section, which does not block completion under this definition (Charter §11; retry 2 of 2 per Global Constraint #6, re-assessed against attempt 1's unchanged evidence — see Coverage Matrix).  
Attempt count: 2  
No-edits attestation: confirmed

## Evidence table

| ID | North Star assertion | assertion_type | evidence (path:lines, pinned) | result | risk | confidence | assumptions | Dustin ruling required? |
|---|---|---|---|---|---|---|---|---|
| A-GOV-001 | CuttingBoard is a personal trading decision-support cockpit serving four permanent product questions. | FACT | `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:15-28`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:18-26`; `VISION.md:3-28` | MATCH | Product scope could drift toward prediction or execution. | HIGH |  | no |
| A-GOV-002 | The product must not become a prediction engine, automated execution system, indicator collection, headline firehose, governance project, or backtest-optimization machine. | FACT | Master Ledger:38-45; `VISION.md:36-47`; `CLAUDE.md:44-49` | MATCH | Violating these boundaries creates unsafe or misleading product behavior. | HIGH |  | no |
| A-GOV-003 | Only one packet may be `NOW`, and Dustin alone promotes `NEXT` or `LATER`. | OWNER-DECISION | Master Ledger:49-50; Master Ledger:74-80; `CLAUDE.md:9-20`; `docs/DECISIONS.md:49-52` | MATCH | Multiple active packets can create unauthorized implementation. | HIGH |  | no |
| A-GOV-004 | Acceptance requirements are fixed before implementation and closeout may return only the reviewed SHA, requirement PASS/FAIL results, blocking explanations, and ACCEPT/REJECT. | FUTURE-DESIGN-INTENT | Master Ledger:51-53,372-381; `docs/PRD_TEMPLATE.md:17-24`; `docs/PRD_REVIEW_TEMPLATE.md:29-75`; `docs/PRD_PROCESS.md:119-126` | MATCH | Requirements can expand during closeout and invalidate review scope. | HIGH |  | no |
| A-GOV-005 | A planning entry grants no implementation permission. | FACT | Master Ledger:56; Program:9-14; `CLAUDE.md:118-134`; `docs/AGENT_WORKFLOW.md:160-165` | MATCH | Planning text could be mistaken for authority to edit production. | HIGH |  | no |
| A-GOV-006 | Optional or observational sidecars must preserve baseline output when absent, stale, disabled, or invalid and must not mutate pipeline-owned decision artifacts. | FACT | Master Ledger:55; `VISION.md:49-62`; `docs/sidecar_doctrine.md:43-63,83-96`; `docs/architecture.md:1-40` | MATCH | Sidecar influence could silently change qualification, sizing, or execution decisions. | HIGH |  | no |
| A-GOV-007 | Governance serves truth, safety, and delivery and is not an independent product track; proactive governance work is frozen for the next three product slices. | OWNER-DECISION | Master Ledger:57,405; Program:28-31; `VISION.md:67-75`; `audits/current-state-reconciliation-2026-07-30/CHARTER.md:24-37` | MATCH | Governance activity could displace trader-facing delivery. | MEDIUM |  | yes |
| A-GOV-008 | The standard packet requires a bounded scope, dependencies, acceptance contract, evidence, review scope, stop conditions, debt, and Dustin decision field. | FUTURE-DESIGN-INTENT | Master Ledger:352-370; `docs/plans/agent-work-charge-template-v0.1.md:15-36,120-136` | MATCH | Missing fields weaken authority and closeout traceability. | HIGH |  | no |
| A-GOV-009 | The ratification ledger and program were draft-until-merge artifacts that became ratified and complete upon PR #187 merge. | FACT | Master Ledger:3-11,425-429; Program:3-14; Charter:4-5,20-24 | MISMATCH | The pinned baseline is already the merge commit, while the documents retain pre-merge status language. | HIGH |  | no |
| A-GOV-010 | The Program's baseline records three open PRs including PR #187. | FACT | Program:33-46; Charter:4-5; Charter:§4-5; snapshot header | MISMATCH | Readers may rely on stale open-PR state when determining authority and blockers. | HIGH |  | no |
| A-GOV-011 | NS-0A's repository-truth reset is complete and the PRD, packet, and debt inventories agree or are explicitly recorded as open debt. | FACT | Master Ledger:90-97; Program:99-108,190-231; `docs/PRD_REGISTRY.md:288-297`; `docs/prd_index.json:3-5,1315-1336` | PARTIAL | The Program itself records a canonical disagreement between `Active PRD: none` and four `IN PROGRESS` registry rows. | HIGH |  | no |
| A-GOV-012 | The Program changes no lifecycle status. | FACT | Program:9-14; Program:64-97; `docs/PRD_REGISTRY.md:288-295` | PARTIAL | The companion ledger labels PRD-271 `BLOCKED`, while the cited registry records it as `IN PROGRESS`; lifecycle and blocking condition are not consistently separated. | HIGH |  | no |
| A-GOV-013 | GOV-2 is ratified and binding, and material work must pass packet review, Dustin's design-direction ruling, independent PRD review, Gate A, implementation review, and Dustin's merge. | FACT | Program:28-31,45; GOV-2:1-16,31-41,65-110,139-172; `docs/DECISIONS.md:19-52`; `CLAUDE.md:118-134` | MATCH | Skipping the sequence can grant downstream implementation authority prematurely. | HIGH |  | no |
| A-GOV-014 | The NS-2 slice is MATERIAL and must begin with an upstream material packet before code. | FUTURE-DESIGN-INTENT | Program:294-307; GOV-2:18-41,65-84; `CLAUDE.md:118-134` | MATCH | A persisted multi-reader boundary could be implemented without review-clean authority. | HIGH |  | no |
| A-GOV-015 | A material packet's connector comments cannot substitute for independent review or exact-head confirmation. | FACT | `CLAUDE.md:189-205`; GOV-2:65-110,228-252; snapshot reminder | MATCH | Workflow metadata or bot comments could be mistaken for substantive disposition. | HIGH |  | no |
| A-GOV-016 | PRD-268 remains `IN PROGRESS` and requires a Dustin disposition; PRD-271 remains `IN PROGRESS` with Gate A pending. | FACT | Master Ledger:263-265; Program:84-85; `docs/PRD_REGISTRY.md:288-295`; `verify-05-governance-debt.md:116-138` | MATCH | Agents could drop active reconciliations or treat unruled design forks as complete. | HIGH |  | yes |
| A-GOV-017 | OPT-0 remains evidence-blocked pending exact-head confirmation and Dustin's approval of carrier, reason semantics, and implementation seam. | FACT | Master Ledger:261-262; Program:72,82,341-347; GOV-2:178-201 | MATCH | CB-02 could advance while its upstream authority remains incomplete. | MEDIUM | The governing workplan is referenced by the North Star documents but was not dispatched as a source. | yes |
| A-GOV-018 | The Program preserves the queued `prd-second-model-commission` item and says activation requires an operator commission. | FACT | Program:226-231; stage0-05:78-96; `verify-05-governance-debt.md:77-92` | MATCH | Queued governance capability could be mistaken for a standing review gate. | HIGH |  | yes |
| A-GOV-019 | The reconciliation charter is read-only, authorizes no implementation, and treats recommendations as proposals. | FACT | Reconciliation Charter:1-6,17-37,167-193,207-215; Program:72,97 | MATCH | Evidence artifacts could be mistaken for implementation or governance authority. | HIGH |  | no |
| A-GOV-020 | Q27's model-role lane remains provisional until its trigger is met; Q28 has no single five-track operator-side reconciliation protocol. | FACT | stage0-05 Governance:129-151; `verify-05-governance.md:116-138`; `docs/PRD_PROCESS.md:176-220`; `CLAUDE.md:247-264` | MATCH | An unratified lane or nonexistent protocol could be treated as binding process. | HIGH |  | yes |
| A-GOV-021 | The Program's validation note correctly limits green CI to existing checks and explicitly says CI does not semantically validate the portfolio map. | FACT | Program:527-532; `CLAUDE.md:290-305`; `docs/plans/agent-work-charge-template-v0.1.md:137-148` | MATCH | CI could be falsely presented as proof of portfolio truth. | HIGH |  | no |
| A-GOV-022 | The Program's source map identifies authoritative artifacts and preserves no implementation authority in planning material. | INTERPRETATION | Program:64-97; `audits/current-state-reconciliation-2026-07-30/CHARTER.md:48-65`; `CLAUDE.md:290-305` | MATCH | Evidence and plans could silently become implementation authority. | MEDIUM |  | no |
| A-GOV-023 | The Master Ledger's ratification points reserve initiative naming, portfolio authority, sequencing, safety ordering, GEX/news boundaries, and prospective evaluation for Dustin. | OWNER-DECISION | Master Ledger:399-408; `docs/DECISIONS.md:19-52`; `VISION.md:49-65` | MATCH | Agent-authored interpretation could preempt owner decisions. | HIGH |  | yes |
| A-GOV-024 | The Claude planning mission produces a program, not implementation code; it maps work, identifies duplicates and debt, builds dependencies, bounds one active plan, and does not promote `NEXT` or `LATER` without Dustin. | FUTURE-DESIGN-INTENT | Master Ledger:410-429; Program:9-14 | MATCH | A planning deliverable could be mistaken for authorization or implementation. | HIGH |  | no |
| A-PR187-001 | PR #187 comment 1 has disposition `ACTIONED`, `DISMISSED`, or `BLOCKED/PARKED`. | FACT | Snapshot: comment 1, disposition reminder | UNKNOWN | An unresolved substantive lifecycle finding may be lost or improperly advanced. | LOW |  | yes |
| A-PR187-002 | PR #187 comment 2 has a supported disposition. | FACT | Snapshot: comment 2, disposition reminder | UNKNOWN | Portfolio authorization could remain ambiguous. | LOW |  | yes |
| A-PR187-003 | PR #187 comment 3 has a supported disposition. | FACT | Snapshot: comment 3, disposition reminder | UNKNOWN | Potential safety-relevant debt classification may be mishandled. | LOW |  | yes |
| A-PR187-004 | PR #187 comment 4 has a supported disposition. | FACT | Snapshot: comment 4, disposition reminder | UNKNOWN | The post-merge NOW transition may remain unclear. | LOW |  | yes |
| A-PR187-005 | PR #187 comment 5 has a supported disposition. | FACT | Snapshot: comment 5, disposition reminder | UNKNOWN | Fresh agents may miss the authoritative portfolio. | LOW |  | yes |
| A-PR187-006 | PR #187 comment 6 has a supported disposition. | FACT | Snapshot: comment 6, disposition reminder | UNKNOWN | Distinct debt status could be lost. | LOW |  | yes |
| A-PR187-007 | PR #187 comment 7 has a supported disposition. | FACT | Snapshot: comment 7, disposition reminder | UNKNOWN | A critical safety bypass could be treated as non-blocking. | LOW |  | yes |
| A-PR187-008 | PR #187 comment 8 has a supported disposition. | FACT | Snapshot: comment 8, disposition reminder | UNKNOWN | CI could be misrepresented as semantic validation. | LOW |  | yes |
| A-PR187-009 | PR #187 comment 9 has a supported disposition. | FACT | Snapshot: comment 9, disposition reminder | UNKNOWN | NS-1D promotion eligibility could remain ambiguous. | LOW |  | yes |
| A-PR187-010 | PR #187 comment 10 has a supported disposition. | FACT | Snapshot: comment 10, disposition reminder | UNKNOWN | GEX evidence gates could be bypassed. | LOW |  | yes |
| A-PR187-011 | PR #187 comment 11 has a supported disposition. | FACT | Snapshot: comment 11, disposition reminder | UNKNOWN | The baseline open-PR inventory could remain inaccurate. | LOW |  | yes |
| A-PR187-012 | PR #187 comment 12 has a supported disposition. | FACT | Snapshot: comment 12, disposition reminder | UNKNOWN | The ORB dependency could be treated as skippable. | LOW |  | yes |
| A-PR187-013 | PR #187 comment 13 has a supported disposition. | FACT | Snapshot: comment 13, disposition reminder | UNKNOWN | Two competing current packets could be presented. | LOW |  | yes |
| A-PR187-014 | PR #187 comment 14 has a supported disposition. | FACT | Snapshot: comment 14, disposition reminder | UNKNOWN | PRD-268 could disappear from active reconciliation. | LOW |  | yes |
| A-PR187-015 | PR #187 comment 15 has a supported disposition. | FACT | Snapshot: comment 15, disposition reminder | UNKNOWN | Fixed findings could be silently omitted. | LOW |  | yes |
| A-PR187-016 | PR #187 comment 16 has a supported disposition. | FACT | Snapshot: comment 16, disposition reminder | UNKNOWN | CB-02 could bypass an upstream lifecycle gate. | LOW |  | yes |
| A-PR187-017 | PR #187 comment 17 has a supported disposition. | FACT | Snapshot: comment 17, disposition reminder | UNKNOWN | File-level status could conflict with post-merge authority. | LOW |  | yes |
| A-PR187-018 | PR #187 comment 18 has a supported disposition. | FACT | Snapshot: comment 18, disposition reminder | UNKNOWN | Gate A could precede required material review. | LOW |  | yes |
| A-PR187-019 | PR #187 comment 19 has a supported disposition. | FACT | Snapshot: comment 19, disposition reminder | UNKNOWN | NS-0A could be closed despite unresolved inventory disagreement. | LOW |  | yes |
| A-PR187-020 | PR #187 comment 20 has a supported disposition. | FACT | Snapshot: comment 20, disposition reminder | UNKNOWN | OPT-0 approval could be treated as complete. | LOW |  | yes |
| A-PR187-021 | PR #187 comment 21 has a supported disposition. | FACT | Snapshot: comment 21, disposition reminder | UNKNOWN | Queued second-model work could disappear from the authoritative map. | LOW |  | yes |
| A-PR187-022 | PR #187 comment 22 has a supported disposition. | FACT | Snapshot: comment 22, disposition reminder | UNKNOWN | OPT-1 could advance before its evidence gate. | LOW |  | yes |
| A-PR187-023 | PR #187 comment 23 has a supported disposition. | FACT | Snapshot: comment 23, disposition reminder | UNKNOWN | Existing queued debt could be lost. | LOW |  | yes |
| A-PR187-024 | PR #187 comment 24 has a supported disposition. | FACT | Snapshot: comment 24, disposition reminder | UNKNOWN | A governance guardrail could become authoritative without GOV-2 clearance. | LOW |  | yes |
| A-PR187-025 | PR #187 comment 25 has a supported disposition. | FACT | Snapshot: comment 25, disposition reminder | UNKNOWN | The NS-2E packet could target the wrong surface. | LOW |  | yes |
| A-PR187-026 | PR #187 comment 26 has a supported disposition. | FACT | Snapshot: comment 26, disposition reminder | UNKNOWN | Freshness consumers could invent incompatible local contracts. | LOW |  | yes |
| A-PR187-027 | PR #187 comment 27 has a supported disposition. | FACT | Snapshot: comment 27, disposition reminder | UNKNOWN | OPT-1 could advance while OPT-0 remains evidence-blocked. | LOW |  | yes |
| A-PR187-028 | PR #187 comment 28 has a supported disposition. | FACT | Snapshot: comment 28, disposition reminder | UNKNOWN | Gate A could be sought before PRD-268/L0 clearance. | LOW |  | yes |
| A-PR187-029 | PR #187 comment 29 has a supported disposition. | FACT | Snapshot: comment 29, disposition reminder | UNKNOWN | PRD-271 could be dropped from active lifecycle reconciliation. | LOW |  | yes |

## Non-match detail blocks

### A-GOV-009

- Exact source path and lines: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:4,428-429`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:4`; Charter:4-5.
- Governing authority: Audit Charter §§2, 4, and 5; pinned baseline SHA.
- Observed discrepancy: The pinned baseline is PR #187's merge commit, but both documents retain `DRAFT UNTIL MERGE` and “ratified upon merge” language.
- Practical consequence: Readers cannot determine whether the documents are already authoritative.
- False-authority risk: The stale draft status may cause agents to ignore the ratified portfolio; the merge-contingent language may also falsely imply a future transition.
- Safety relevance: Indirect governance and implementation-authority risk.
- Current-vs-future-facing effect: Current-state mismatch; intended future transition is not encoded consistently.
- Proposed disposition: Dustin should ratify the post-merge status wording.
- Confidence: HIGH.
- Missing evidence: None.

### A-GOV-010

- Exact source path and lines: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:37-46`; Charter:4-5.
- Governing authority: Audit Charter §4 PR provenance and §5 mechanical attestation.
- Observed discrepancy: Program §2 describes PR #187 as open, while the pinned baseline is the merged PR #187 commit.
- Practical consequence: The baseline inventory is stale and can misstate which review or merge gates remain.
- False-authority risk: Agents may treat a merged ratification vehicle as still awaiting merge or overlook the actual post-merge state.
- Safety relevance: Governance-authority risk.
- Current-vs-future-facing effect: Current-state mismatch.
- Proposed disposition: Replace the pre-merge PR inventory with a clearly dated merged-baseline statement.
- Confidence: HIGH.
- Missing evidence: None.

### A-GOV-011

- Exact source path and lines: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:90-97`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:190-208`; `docs/PRD_REGISTRY.md:288-295`.
- Governing authority: `docs/PRD_REGISTRY.md` for PRD lifecycle; `docs/PROJECT_STATE.md` is cited by the Program but is owned by Domain B.
- Observed discrepancy: The NS-0A completion claim acknowledges the `Active PRD: none` versus four `IN PROGRESS` rows disagreement rather than resolving it.
- Practical consequence: The claimed truth reset is not fully reconciled.
- False-authority risk: The `COMPLETE` label could be read as authority that the inventory is reconciled.
- Safety relevance: Indirect; unresolved lifecycle truth can permit unsafe sequencing.
- Current-vs-future-facing effect: Current reconciliation remains partial.
- Proposed disposition: Preserve NS-0A as partial or explicitly classify the disagreement as an accepted owner decision.
- Confidence: HIGH.
- Missing evidence: Domain B's `docs/PROJECT_STATE.md` is cited but not owned by Domain A.

### A-GOV-012

- Exact source path and lines: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:263`; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:9-14`; `docs/PRD_REGISTRY.md:291`.
- Governing authority: `docs/PRD_REGISTRY.md` for canonical PRD lifecycle; `CLAUDE.md` and GOV-2 for authority sequencing.
- Observed discrepancy: The ledger labels PRD-271 `BLOCKED`, while the registry records `IN PROGRESS`; the Program separately says lifecycle statuses are unchanged.
- Practical consequence: Readers may drop PRD-271 from active reconciliation or confuse lifecycle condition with dependency state.
- False-authority risk: The portfolio document could silently override the canonical registry.
- Safety relevance: PRD-271 Gate A controls the ORB boundary for the future NS-2 slice.
- Current-vs-future-facing effect: Current lifecycle representation is inconsistent; future sequencing is affected.
- Proposed disposition: Express the condition as `IN PROGRESS / BLOCKED` while retaining registry authority.
- Confidence: HIGH.
- Missing evidence: None.

### A-GOV-017

- Exact source path and lines: Master Ledger:261-262; Program:72,341-347.
- Governing authority: The Program identifies the workplan as authoritative for lifecycle gates, but that workplan is outside the dispatched source set.
- Observed discrepancy: The North Star assertion depends on an undispatched workplan for the exact OPT-0 exit.
- Practical consequence: Domain A cannot independently verify the governing lifecycle claim under the dispatch contract.
- False-authority risk: A stale or misread workplan condition could be treated as current authority.
- Safety relevance: CB-02 concerns a risk-budget refusal and implementation authorization.
- Current-vs-future-facing effect: Evidence gap affecting future implementation sequencing.
- Proposed disposition: Add the workplan to the Domain A cited-source scope through an amendment.
- Confidence: MEDIUM.
- Missing evidence: `docs/plans/decision-support-workplan-v0.1.md`.

## PROPOSED AMENDMENT

- discovered by: Domain A / A-GOV-017 and related lifecycle assertions / description: North Star documents rely on `docs/plans/decision-support-workplan-v0.1.md` and expansion-doctrine material for governing lifecycle and evidence-blocked states / proposed scope change: add the referenced workplan and doctrine sections to Domain A's cited-source dispatch / blocking: yes.

No repository files were edited during this dispatch.
