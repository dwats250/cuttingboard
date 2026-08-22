# CuttingBoard Existing-Work and Future-Scaffold Workplan v0.1

Status: APPROVED FOR MANUAL MERGE — EFFECTIVE WHEN MERGED

Companion authority:
`docs/plans/decision-support-expansion-doctrine-v0.1.md`

Baseline inspected: `main` at
`724d84af58bd0a021bb989cd2637832e2639e8a3` on 2026-07-25.

This is the single planning ledger for GEX, personalized news, future
options-data work, and the existing reconciliation that must precede them. It
assigns work-packet labels, not PRD numbers. PRD numbers are allocated only at
Stage 0 under `docs/PRD_PROCESS.md`.

## 1. Sequencing law

Work proceeds in this order:

1. Land the durable planning authority.
2. Reconcile current lifecycle and operator decisions.
3. Correct already-constructed truth and safety defects.
4. Decide the fate of dormant constructed work.
5. Scaffold future observational tracks.
6. Build producers before consumers.
7. Consider cadence only after usefulness is proven.

Later waves may be researched while earlier implementation waits, but no later
wave may be promoted to implementation in a way that bypasses an earlier gate.

No new numbered feature PRD is allocated while the PRD-271 document gap and
the PRD-267/272/273 lifecycle closeouts remain unresolved.

## 2. Work ledger

| Packet | State | Concern | Mutation permission | Exit |
|---|---|---|---|---|
| GOV-0 | COMPLETE | Land doctrine, workplan, and charge template | Docs-only governance PR | True when its held PR merges |
| L0 | COMPLETE (2026-08-05) | Reconcile PRD-267/268/271/272/273 lifecycle truth | Bookkeeping only after rulings | Met: PRD-267/271/272/273 all COMPLETE with real merged provenance; PRD-268 returned to PROPOSED and PARKED on Dustin's 2026-08-05 ruling (its last open disposition); `tools/validate_prd_registry.py --skip-commit-resolvability` exits 0 |
| D-RULE | COMPLETE | Make Finding D refusal ruling canonical | PR #167 only | Met: the ruling is on `main` (`docs/DECISIONS.md`, 2026-07-24 "Finding D RULED"), merged via PR #167 on 2026-07-26 |
| OPT-0 | SUPERSEDED (2026-08-05) | Trace Finding D implementation seam | Read-only findings artifact | Superseded by PRD-283. Its two evidence artifacts are durably in-tree under `audits/current-state-reconciliation-2026-07-30/` (imported out of order under a historical banner); PR #184 is closed as superseded, not merged. See `docs/DECISIONS.md` 2026-08-05 "TRUTH-SYNC" |
| OPT-1 | SUPERSEDED (2026-08-05) | Implement smallest-contract refusal after OPT-0 | Future HIGH-RISK PRD | Superseded by PRD-283, which restarted this line under its own number and merged to `main` as `f806f5b` on 2026-08-03 (HIGH-RISK/EXECUTION; validated at the exact merged head by `docs/prd_history/PRD-283.review.claude.md`). PR #185 (the abandoned OPT-1/PRD-278 draft) carries no authority. See `docs/DECISIONS.md` 2026-08-05 "TRUTH-SYNC" |
| DOC-0 | COMPLETE (2026-08-05) | Correct stale proposal headers | Docs-only bounded change | Met: the PRD-251 continuation-path and PRD-259 first-fire-consumers proposal headers now state their current disposition on the first screen |
| MACRO-0 | KEEP DORMANT (2026-08-05, ruled: Dustin) | Keep, promote, or retire PRD-187/188 track | Read-only decision packet | Met by explicit ruling: PRD-187 stays a manual/evaluation-only producer, PRD-188 stays PROPOSED and unpromoted, the read-only decision packet is not run. Re-evaluate only if Dustin reopens the track |
| PRES-0 | DEFERRED | PRD-259 Findings E/F/G | No current build | Separately promoted |
| NEWS-0 | EVIDENCE BLOCKED | Static news registry and schema after L0 | Future planning/PRD | Approved static contract |
| NEWS-1 | EVIDENCE BLOCKED | Manual news producer after NEWS-0 | Future SIDECAR PRD | Useful artifact |
| NEWS-2 | EVIDENCE BLOCKED | News usefulness evaluation after NEWS-1 | Evaluation only | KEEP/REVISE/RETIRE |
| NEWS-3 | EVIDENCE BLOCKED | Display consumer after NEWS-2 | Future CONSUMER PRD | Baseline-neutral display |
| GEX-0 | `PROVIDER VIABLE` (Cboe delayed_quotes, 2026-08-17; scoped: personal/non-redistributed/context-only, ~15-min delayed) | One-provider live evidence pass after L0 | Network research only | Verdict speaks only to the one provider examined. Fresh 2026-08-17 pass reached `cdn.cboe.com/api/global/delayed_quotes/options/{SPY,_SPX}.json` keyless, HTTP 200: SPY 14,546 contracts; _SPX 30,558 (SPX AM-settled + SPXW PM-settled). All 13 doctrine §4.3 legs established live, including per-strike `open_interest` + `gamma` + `iv` + quotes + spot; feed ships no vendor flip/put-wall/call-wall. Packet: `audits/gex-0-cboe-evidence-2026-08/GEX_0_CBOE_PROVIDER_EVIDENCE_PACKET_2026-08-17.md`. GEX-1 remains gated behind a separate PRD + Gate A. Prior 2026-08-06 Polygon pass is unchanged (`EVIDENCE INCOMPLETE` for Polygon: free tier gates the options snapshot where OI/greeks live) |
| GEX-1 | IMPLEMENTED (PRD-306; Gate A granted 2026-08-20 on reviewed head `47f3129`, authority package merged `a3f01a9`. Producer `tools/gex_snapshot.py` performs one keyless GET against Cboe `_SPX` and writes observe-only `logs/gex_snapshot.json` over the SPX+SPXW universe under the full R1-R37 contract; stdlib-only, isolated from `cuttingboard/`. Context-only; baseline-neutral; no decision authority. SPY still deferred pending usefulness evidence, not invalidated) | Manual cached GEX producer after GEX-0 | PRD-306 (SIDECAR) | Honest artifact |
| GEX-2 | IMPLEMENTED (PRD-309; Gate A granted 2026-08-21 on reviewed revision `097faa9`. Display-only, baseline-neutral GEX context card `cuttingboard/delivery/gex_card.py`, loaded and emitted by `dashboard_renderer.py`; reads `logs/gex_snapshot.json` for display only under the R1-R20 contract; suppresses to a byte-identical baseline dashboard on absent/stale/invalid; no decision authority; no producer/cadence/schema change. Public-board visibility is capability-now/public-later (deferred GEX-3). Held for Dustin's merge) | Display-only consumer after GEX-1 | PRD-309 (HIGH-RISK/CONSUMER) | Baseline-neutral display |
| ODATA-0 | EVIDENCE BLOCKED | Refresh future options-data proposals after OPT-1 | Read-only recon | Ranked, current backlog |
| ODATA-1+ | EVIDENCE BLOCKED | Data-independent/provider-dependent builds after ODATA-0 | Separate future PRDs | Per-PRD gates |

`GOV-0: COMPLETE` is merge-contingent: the held governance PR's manual merge
makes that state true and makes `L0` the current packet. No post-merge state
transition commit is required.

## 3. Wave 0 — durable planning authority

### GOV-0 — Land the planning package

Goal: make this direction visible from normal repository entry points so a
future agent cannot mistake an absent plan for permission to improvise.

Exact intended repository changes:

- Add `docs/plans/decision-support-expansion-doctrine-v0.1.md`.
- Add `docs/plans/decision-support-workplan-v0.1.md`.
- Add `docs/plans/agent-work-charge-template-v0.1.md`.
- Add the three files under `CLAUDE.md` canonical sources.
- Add a binding `CLAUDE.md` carve-out: every PR governed by these plans is
  manual-merge-only and must never be queued for auto-merge.
- Add one short pointer in `docs/PROJECT_STATE.md` naming the current workplan
  packet.
- Add a dated `docs/DECISIONS.md` entry recording Dustin's ratification and
  that these tracks have planning authority but no implementation permission.

Constraints:

- Docs only.
- No PRD number inferred.
- No production, test, dependency, workflow, registry, or index changes.
- No feature is marked `READY FOR PRD` merely because the plan lands.
- Manual-merge-only because this adds governance guardrails.

Validation:

- All three paths resolve from `CLAUDE.md`.
- `PROJECT_STATE.md` names exactly one current packet.
- The decision entry points to exact file paths and version.
- Repository documentation links are valid.

Exit: merged manually and visible on `main`.

## 4. Wave 1 — current lifecycle and rulings

### D-RULE — Land PR #167 safely

Known state: PR #167 contains Dustin's ruling that a smallest expressible
contract exceeding the adjusted risk budget must be refused. It is docs-only,
manual-merge-only, and based on an older `main`.

Required pass:

1. Bring the PR branch current with `main` without force-push or rewrite.
2. Confirm its diff remains exactly the intended `docs/DECISIONS.md` entry.
3. Confirm it does not claim implementation.
4. Run applicable documentation/registry validation.
5. Hold for Dustin's manual merge.

Exit: the ruling exists on `main`. Until then, agents may cite it as Dustin's
decision but must label it unmerged.

### L0 — Reconcile lifecycle truth

Known current truth:

- PRD-267 implementation merged via PR #166 but remains IN PROGRESS.
- PRD-272 documentation sweep merged via PR #166 but remains IN PROGRESS.
- PRD-273 implementation merged via PR #169 but remains IN PROGRESS.
- PRD-271 is allocated on an unmerged branch and is held for Gate A.
- PRD-268 is an IN PROGRESS scaffold with an unruled design fork.
- `PROJECT_STATE.md` still describes PR #166 as in flight.
- `prd_index.json` remains `latest_complete: 270`, `next_prd: 271`.

Required order:

1. Resolve PRD-271 Gate A. Produce a complete, truthful scaffold before
   landing its document. Do not merge TODO scope as if it were approved.
2. Disposition PRD-268 explicitly:
   - approve it for implementation;
   - return it to PROPOSED if implementation has not begun; or
   - deprecate it with a dated reason.
3. Land the PRD-271 document in sequence.
4. Perform residual closeout bookkeeping for merged PRD-267, PRD-272, and
   PRD-273 using their real merged PR provenance.
5. Refresh `PROJECT_STATE.md` so no merged PR is described as active.
6. Set `latest_complete` and `next_prd` only to values justified by the
   resulting contiguous record.
7. Run the authoritative registry validator and full documentation checks.

Forbidden:

- Inventing a PRD-271 implementation to close the numbering gap.
- Marking PRD-268 COMPLETE without implementation.
- Giving PRD-267/272/273 fabricated SHAs.
- Allocating a new feature PRD before the sequence is coherent.

Exit:

- Registry, index, PRD documents, and `PROJECT_STATE.md` agree.
- No allocated-but-unlanded gap blocks future work.
- The first free PRD number is derived by tooling, not stated from memory.

## 5. Wave 2 — existing options and document truth

### OPT-0 — Finding D seam trace

Class: read-only architecture and consumer recon.

The operator decision is not reopened: refuse the setup rather than round up
past the adjusted risk ceiling.

Questions:

1. Enumerate every path to `options.py`'s final `max(1, ...)`.
2. Identify which paths can produce a raw adjusted contract count of zero.
3. Trace all consumers of `OptionSetup.max_contracts`, `dollar_risk`, and the
   absence of an `OptionSetup`.
4. Determine whether the correct refusal occurs in options construction,
   qualification, decision assembly, or policy materialization.
5. Identify an existing non-actionable carrier, if one exists.
6. Determine the exact refusal reason needed. Do not assume
   `size_rounds_to_zero`; that token currently describes policy-multiplier
   materialization and may not truthfully describe a smallest-contract budget
   failure.
7. Reconcile PRD-157's intentional floor-one behavior with the later
   risk-ceiling ruling and identify what is superseded.
8. Enumerate direct, continuation, debit, credit, and correlation-adjusted
   cases.
9. Produce the initial `FILES` estimate and every asserting test surface.
10. State how positive-sizing behavior remains byte-for-byte or
   value-for-value unchanged.

Deliverable:

- One versioned findings artifact.
- Every load-bearing claim labeled `CONFIRMED`, `FALSIFIED`, `NARROWED`, or
  `NOT REPRODUCED`.
- One recommended implementation seam and one rejected-alternatives section.
- No code, PRD number, registry edit, or implementation permission.

Exit: Dustin approves the carrier, reason semantics, and implementation seam.

### OPT-1 — Implement the refusal

Expected lane/class: HIGH-RISK / EXECUTION + PATCH. Final classification comes
from `docs/PRD_PROCESS.md`.

Initial ceiling, subject to OPT-0:

- At most four production files.
- At most three test files.
- At most 100 net production LOC.
- No dependency, workflow, schema, or unrelated refactor.

Required behavior:

- If one contract exceeds the applicable adjusted risk ceiling, no actionable
  setup or decision survives.
- The refusal is explicit and stable at every existing presentation/audit
  consumer.
- Direct and continuation paths agree.
- Debit and credit paths are covered.
- Correlation penalties are covered.
- Positive quantities and their current dollar-risk arithmetic remain
  unchanged.
- A mutation restoring the floor-one budget breach turns at least one test
  red.

Forbidden:

- Fractional contracts.
- Rounding up.
- Silently dropping the candidate.
- Reusing a reason token without proving semantic equivalence.
- Changing the configured budget.
- Altering strategy selection or estimated economics.
- Live-chain work.

Landing:

- Stage-0 PRD before implementation.
- Exact FILES lock.
- One fresh-context review pinned to the final implementation SHA.
- Commissioned second-model review only if Dustin requests it; otherwise use
  the repository's exact waiver rule.
- Draft/manual merge; no agent merge.

### DOC-0 — Correct proposal truth

Small docs-only correction after D-RULE and the L0 truth pass.

Scope:

- Update the top of
  `docs/prd_history/PRD-251.continuation-path.proposal.md` to state that
  PRD-256 R3 fulfilled/superseded the proposal and that no Gate A remains.
- Update the top disposition summary of
  `docs/prd_history/PRD-259.first-fire-consumers.proposal.md` so D, E, F, and
  G are all represented:
  - D: ruled refuse; implementation tracked by OPT-0/OPT-1.
  - E/F: open, non-blocking, deferred.
  - G: open, non-blocking, presentation follow-up.

Constraints:

- Header/status truth only.
- Preserve historical analysis.
- Do not rewrite the original evidence.
- No production or test changes.

Exit: a reader can learn every proposal's current disposition from its first
screen.

### PRES-0 — Deferred presentation debt

Finding G may be promoted as a small standalone consumer correction after
OPT-1 if recon confirms it affects one presentation seam.

Findings E and F remain deferred until a consumer pass identifies whether they
share one coherent presentation contract. They are not to be swept into
OPT-1.

No implementation is authorized by this ledger entry.

## 6. Wave 3 — constructed macro-awareness decision

### MACRO-0 — Keep, promote, or retire

Read-only packet:

1. Verify PRD-187 producer, workflow trigger, artifact paths, tests, and
   current model/source realizability.
2. Verify the evaluation corpus labeling state.
3. Confirm whether any valid evaluation result exists.
4. Confirm PRD-188's gate remains unmet or identify exact evidence satisfying
   it.
5. Estimate ongoing maintenance cost and the human question the artifact
   answers.

Dustin chooses exactly one:

- `KEEP DORMANT`: retain manual/evaluation-only producer and set a dated
  re-evaluation point.
- `PROMOTE THE PRD-188 CONSUMER AFTER SPLITTING OUT CADENCE`: first amend the
  existing proposal so consumer construction remains in PRD-188 and scheduled
  activation becomes a separately ruled future packet; then require every
  written PRD-188 consumer gate to pass before implementation.
- `RETIRE`: remove dormant surfaces under a separate subtraction PRD.

Forbidden:

- Calling the collector a news feed.
- Weakening its structural-shock-only contract.
- Adding cron or dashboard consumption before the decision.

## 7. Wave 4 — personalized-news scaffold

### NEWS-0 — Static registry and artifact contract

Begins only after L0 is complete.

Deliverables:

- Versioned static universe/source/theme registry.
- Versioned proposed artifact schema.
- Exact source allowlist.
- Exact item cap and deterministic relevance/dedup/freshness rules.
- Example valid, empty, stale, and partial-source artifacts.
- No network collector.

Required registry categories:

- tradeable symbols;
- context-only symbols;
- themes;
- approved sources; and
- enabled/disabled state with a human-editable reason.

The exact universe content is supplied or ratified by Dustin. An agent may not
infer additional symbols or sources.

### NEWS-1 — Manual producer

One SIDECAR PRD:

- reads only the approved registry and sources;
- writes one new versioned artifact;
- normally emits two to three items, never more than five;
- labels source and publication time;
- makes unavailable/partial-source state explicit;
- contains no prediction or sentiment fields; and
- has no pipeline, renderer, notification, or cron edits.

### NEWS-2 — Usefulness evaluation

Dustin inspects representative artifacts and chooses:

- `KEEP`;
- `REVISE` with one bounded correction; or
- `RETIRE`.

No automatic promotion follows a passing technical test.

### NEWS-3 — Consumer

Separate CONSUMER PRD after `KEEP`:

- display-only;
- no standing firehose;
- missing/stale/invalid artifact leaves baseline output unchanged;
- renderer performs no new analytics; and
- no notification or cadence.

## 8. Wave 5 — GEX evidence and scaffold

### GEX-0 — One-provider live evidence

Network-enabled, read-only, one provider.

The artifact must answer every minimum-honesty field from the doctrine with
current primary evidence and a real response. It ends in exactly one verdict
(amended 2026-08-05 per doctrine §4.3; each speaks only to the one provider
examined in this bounded pass, never to the existence of a viable provider):

- `PROVIDER VIABLE`;
- `PROVIDER NOT VIABLE`; or
- `EVIDENCE INCOMPLETE`.

`PROVIDER NOT VIABLE` or `EVIDENCE INCOMPLETE` ends the track until Dustin
explicitly commissions a fresh pass.

No second provider, code, abstraction, schema implementation, or PRD number is
authorized automatically.

### GEX-1 — Manual cached producer

Only after a pass and Dustin's explicit go:

- primary universe only;
- manual/lazy/cached;
- source/model/timestamp/coverage embedded;
- explicit stale/unavailable;
- versioned additive artifact;
- no consumer, cron, notifications, or decision imports.

### GEX-2 — Display consumer

Only after Dustin inspects useful GEX-1 artifacts:

- display/audit only;
- no permission or sizing effect;
- no renderer computation;
- missing/stale/invalid yields baseline-identical output.

Delivered by PRD-309 (HIGH-RISK/CONSUMER): a pure `cuttingboard/delivery/gex_card.py`
plus a load-and-emit seam in `dashboard_renderer.py`. All four constraints hold —
display-only; no permission/sizing/decision effect (R17-R20); all GEX arithmetic in
`gex_card.py`, none in the renderer (R20, so "no renderer computation" is satisfied
and the Q2 distance geometry is presentation-layer only); and absent/stale/invalid
yields output byte-identical to an independent pre-GEX golden (R1). Public-board
visibility remains the deferred, optional GEX-3 (invoke the producer in CI).

## 9. Wave 6 — future options-data refresh

### ODATA-0 — Reconcile the old backlog

Run after OPT-1.

Re-read current:

- `cuttingboard/options.py`;
- `cuttingboard/chain_validation.py`;
- contract and audit consumers;
- current tests and maps;
- historical A1b/live-economics proposals; and
- any absolute-strike or expiry placeholders.

Classify each candidate:

- already constructed;
- still valid and data-independent;
- provider-dependent;
- superseded;
- rejected; or
- requires Dustin's ruling.

Do not carry old tentative PRD numbers forward.

### ODATA-1+ — Separate construction units

Possible units are not approved by this list. If recon retains them, separate:

1. deterministic calendar-expiry representation;
2. absolute strike resolution;
3. both-leg live quote resolution;
4. net debit/credit and live max-loss calculation;
5. degraded-data behavior; and
6. display/audit consumption.

Provider-dependent units require their own data-contract evidence. No unit may
bundle broker integration or execution automation.

## 10. Parallelism

Safe concurrent work:

- GOV-0 drafting and read-only L0 evidence collection.
- OPT-0 read-only trace after D-RULE content is known.
- MACRO-0 read-only audit.
- NEWS-0 registry-question preparation without assigning symbols.
- GEX-0 provider-pass charge preparation without conducting the pass.

Unsafe concurrent work:

- Any implementation while its Gate A is open.
- Multiple agents editing lifecycle files.
- OPT-1 concurrent with another options sizing change.
- NEWS or GEX consumer work before producer evaluation.
- Any two branches allocating the same next PRD number.

One owner at a time controls:

- `docs/PRD_REGISTRY.md`;
- `docs/prd_index.json`;
- `docs/PROJECT_STATE.md`;
- `docs/DECISIONS.md`; and
- active PRD numbering.

## 11. Model allocation

Use a higher-reasoning model for:

- lifecycle/doctrine conflict resolution;
- OPT-0/OPT-1;
- provider contract evaluation;
- final PRD authoring for HIGH-RISK work; and
- final drift review.

Use a lighter model for:

- mechanical header corrections;
- exact-path inventories;
- registry validation;
- deterministic link checks; and
- implementation only when the approved PRD leaves no semantic choice.

No model reviews its own work as the independent reviewer.

## 12. Completion definition

This workplan is complete only when:

- every constructed item is COMPLETE, SUPERSEDED, RETIRED, or carries a dated
  reevaluation state;
- no proposal header contradicts current truth;
- GEX and NEWS each have an explicit stop-or-promotion record;
- provider-dependent options work has evidence before implementation;
- every landed producer has a named consumer or an approved observational
  purpose;
- `PROJECT_STATE.md` points to the current packet; and
- a fresh-context agent can determine the whole queue from canonical
  repository files without reconstructing it from chat or audits.
