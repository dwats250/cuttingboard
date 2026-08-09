# CuttingBoard — Sol Campaign Delta Review (2026-08-09)

Campaign-level architecture / orchestration review of the current execution
campaign, over the master parallel implementation plan and current state.
Explicit owner (Dustin) commission. NOT a routine implementation review, NOT a
substitute for Opus 4.8 as HELM, NOT a Gate A; authorizes no merge or
implementation. Preserved because it carries substantive new findings (merge-
train head change, dynamic PRD numbering, a twice-recurring friction).

## SOL MODEL VERIFICATION
- Model: **gpt-5.6-sol** (self-reported "I am GPT-5.6 Sol"; CLI selected via
  `-m gpt-5.6-sol` — the CLI default is `gpt-5.6-terra`, so Sol was chosen
  explicitly).
- Reasoning effort: **xhigh** (Max, per owner).
- Mode: sandboxed **read-only** (`codex exec -s read-only`); Sol made no edits,
  commits, branch/PR changes.
- Command: `codex exec -s read-only -m gpt-5.6-sol -c model_reasoning_effort=xhigh - < <prompt>`
- Evidence Sol read: all nine reconciliation artifacts @
  `origin/claude/cuttingboard-reconciliation-notes-op3p8w`; Registry packet +
  review @ `origin/docs/registry-material-packet-2026-08@84ff230`; PRD-290 +
  history @ `origin/governance/f1-estimation-rule-graduation@ed43243`; #232 @
  `a1b434e`; CF-E2 @ `c3a1777`; and canonical PROJECT_STATE / DECISIONS /
  PRD_PROCESS / VISION / doctrine / workplan on `main@7d0805e`.

## VERDICT
**MASTER PLAN VALID WITH DELTAS.** The execution DAG, authority boundaries,
scope walls, and lane independence still hold; no material contradiction
requires rewriting the plan. Cloudflare-first remains correct for the FEATURE
implementation priority (it carries the only near-term external timing/trigger
unknowns and completes the shipped Market Control Card's post-open value;
Registry's procedural lead stays parallelizable, not a reason to displace CF).

## DELTAS (since the master plan)
- F1/P-4 complete through PRD-290 closeout, zero production LOC, awaiting #233
  owner merge. The master's fixed "CF PRD-290" reference is obsolete — future
  Stage-0 numbers must be allocated DYNAMICALLY (never preassign 291/292).
- Alignment check #6 complete + PASS, awaiting #232 owner merge.
- Registry advanced packet-ready -> GOV-2 review-clean; REG-D2 settled. Only
  owner design direction + REG-D1/D3–D7 remain before Stage 0. (An older
  "awaits Codex review" banner in the packet body is superseded by its adjacent
  confirmation artifact.)
- Cloudflare rulings + CF-E2 authorization done; CF-E2 staged for Aug 10; CF-E1
  still needs Dustin's Worker deploy + PAT.
- GEX blocker narrowed from egress to CREDENTIAL availability (reachability
  proven; a keyless run would improperly consume the second-INCOMPLETE).
- No newly earned abstraction (the mutation runner was already "earned now"
  when the master was written; no Morning Brief copy #3, second provenance
  carrier, second scheduled consumer, or Registry consumer has shipped since).

## SERIALIZATION MAP
- `docs/PROJECT_STATE.md`: #233 and #232 both touch it, but a three-way merge
  preview is clean (edits in separate hunks). Merge serially anyway.
- PR numbering / lifecycle files: PRD-290 is consumed. CF and Registry Stage-0
  drafting must serialize allocation against then-current `prd_index.json`;
  never preassign 291/292.
- QW-4: start from post-#232 (preferably post-#233) `main` — it also edits
  `PROJECT_STATE.md`.
- CF future surfaces (order unchanged): QW-1 before CF touches
  `resolve_run_mode.py`; QW-2 before CF owns `payload.py`; QW-3 before or folded
  into CF's `cuttingboard.yml`.
- Registry packet, CF-E2 harness, GEX evidence paths: disjoint from #232/#233
  and each other.
- **Recommended merge-train head:** #233 -> reconcile/revalidate #232 -> #232
  -> QW-4 -> QW-1 -> QW-2 -> QW-3 folded into CF. This changes the train's HEAD
  (#233-first minimizes disturbance to its SHA-pinned governance chain), not the
  feature-lane order; either order is textually mergeable.

## AUTONOMY MAP
- **Codex now:** CF-E2 timed captures; QW-1/QW-2/QW-4; mechanical post-merge
  diff/validator checks; CF-E1 after deployment/PAT; GEX-0 after a key exists;
  later Registry R1 only after its own Gate A.
- **Opus HELM:** maintain the DAG + file ownership; compile the CF MATERIAL
  packet from completed evidence/rulings; author Stage-0 PRDs; prevent
  concurrent number/lifecycle-file ownership.
- **Fable:** GEX terminal-verdict framing; any unresolved CF/Registry semantic
  ambiguity; the now-triggered recurring harness-friction classification.
- **Owner-only:** every merge and Gate A; Registry design/content rulings;
  CF-D1b; Worker deploy/PAT; Polygon key; conditional GEX go.
- (Q6) Codex is underused if QW-1/QW-2 stay merely queued or if Opus performs
  CF-E2/CF-E1/GEX capture or mechanical reconciliation itself.
- (Q7) No heavy-model overuse so far; do not spend Opus/Fable on capture
  execution, exact-path checks, validators, or quick-win implementation.
- (Q8) One owner wait is semantically mechanical: toggling #232/#233 draft ->
  ready is assigned to agent-managed post-review readiness by the owner-closeout
  convention, but `gh pr ready` is harness-denied. It could safely be delegated
  after an intentional permission/process correction; do NOT bypass the present
  denial.
- (Q10) **YES — friction tripped twice:** `gh pr ready` denial recurred on two
  completed drafts, and branch-command denial / plumbing workarounds recurred
  across multiple branches. Trips the master's twice-rule; escalate ONCE to
  Fable for classification. Does NOT transfer merge authority.
- (Q11) No newly earned abstraction.

## NEXT ACTION QUEUE (after #233 and #232 are owner-resolved)
1. Re-anchor on new `main`; verify PRD-290 COMPLETE, `latest_complete: 290`,
   `next_prd: 291`, and Alignment #6's pointer.
2. Dispatch QW-4, QW-1, QW-2 as three isolated Codex goals — never an omnibus
   branch.
3. Run CF-E2 premarket capture Mon Aug 10 ~06:00 PT.
4. Run CF-E2 open capture ~06:32 PT; preserve both evidence files.
5. As each quick win goes green/review-ready, owner-merge QW-4 -> QW-1 -> QW-2;
   keep QW-3 reserved for the CF workflow change.
6. Dustin deploys the Worker + issues the PAT; Codex immediately runs CF-E1
   through the zero-side-effect verification path.
7. Present the review-clean Registry choices; Dustin issues design direction +
   REG-D1/D3–D7; then draft the Registry Stage-0 PRD using the currently free
   number, obtain independent review, stop for its separate Gate A.
8. Once CF-E1 + both CF-E2 captures + CF-D1b are complete: draft the CF MATERIAL
   packet -> Codex review/confirmation -> owner design ruling -> dynamically
   numbered Stage-0 PRD -> independent review -> stop for CF Gate A.
9. If Dustin supplies the Polygon key, Codex runs exactly one GEX-0 continuation
   against the fixed checklist; Fable/design-class frames the terminal verdict;
   stop for Dustin's conditional go. No GEX-1.

## STOP CONDITIONS
No new stop condition. The missing Polygon key instantiates the existing
second-INCOMPLETE discipline; the repeated `gh pr ready` denial is a Fable
escalation trigger, not a product-lane stop.

---
This artifact authorizes nothing. It is a read-only campaign review; every
merge, Gate A, and owner ruling remains Dustin's act.
