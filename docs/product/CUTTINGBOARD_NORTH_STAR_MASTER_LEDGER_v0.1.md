# CuttingBoard North Star Master Ledger v0.1

**Initiative:** NORTH STAR  
**Status:** RATIFIED — ratified and complete as of Dustin's merge of PR #187
(merge commit `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`, 2026-08-02). This
line previously carried a pre-merge draft/awaiting-ratification banner
naming PR #187's then-pending merge; that banner no longer applies now that
the merge has occurred.  
**Owner and final authority:** Dustin  
**Purpose:** Preserve the full product vision, map all active/drafted/parked/debt work, and prevent governance from displacing trader-facing delivery.

**Companion:** `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` — the
repository-verified implementation program (§10's deliverable). Statuses below
were reconciled against live repository truth on 2026-08-01 at `main`
`5fe8ad7`; the program carries the full source map and evidence citations.

## 1. North Star

CuttingBoard is Dustin's personal trading decision-support cockpit.

It describes market state, organizes the opportunity landscape, explains why opportunities exist or fail, and helps Dustin decide whether to act or remain flat.

It does not predict, automate execution, or replace Dustin's judgment.

### Four permanent product questions

1. What environment exists?
2. What matters today?
3. Is anything tradable?
4. What would invalidate or change the read?

> **State first. Trades second.**

CuttingBoard must become:

- fresh enough to trust;
- compressed enough to use;
- observable enough to evaluate;
- truthful about qualification, rejection, uncertainty, and abstention;
- less mentally expensive than assembling context across scattered screens.

It must not become:

- a prediction engine;
- an automated execution system;
- an indicator collection;
- a generic headline firehose;
- a governance project with a trading product attached;
- a backtest-optimization machine.

## 2. Vision protection rules

1. Only one packet may be `NOW`.
2. Dustin alone promotes work from `NEXT` or `LATER`.
3. Acceptance requirements are fixed before implementation.
4. Adjacent discoveries are recorded as debt unless they create false evidence, data corruption, unsafe execution, or irreversible repository damage.
5. Each slice receives one design review, one implementation review, one correction pass, and one closed acceptance check.
6. No recursive governance repair.
7. Optional sidecars must leave baseline output unchanged when missing, stale, disabled, or invalid.
8. A planning entry grants no implementation permission.
9. Governance serves truth, safety, and delivery; it is not an independent product track.
10. Product progress is measured explicitly every week.

## 3. Status vocabulary

| State | Meaning |
|---|---|
| `NOW` | Single active product objective |
| `NEXT` | Approved follow-on, not active |
| `LATER` | Preserved vision, not authorized |
| `RECONCILE` | Current repository truth must be verified |
| `DRAFTED` | Proposal or scaffold exists |
| `BLOCKED` | Named dependency prevents progress |
| `PARKED` | Retained without consuming the workstream |
| `COMPLETE` | Acceptance satisfied and landed |
| `RETIRED` | Explicitly removed with rationale |

Two axes, defined once. **Portfolio rank** (`NOW` / `NEXT` / `LATER`) records
where work sits on the runway. **Lifecycle condition** (`DRAFTED`,
`EVIDENCE BLOCKED`, `DECISION REQUIRED`, `BLOCKED`, `PARKED`, and the other
promotion states owned by the governed workplans) records what currently
gates it. A packet may carry both, written `RANK / CONDITION`; rank never
overrides a lifecycle gate, the authoritative workplan remains the lifecycle
ledger for its tracks, and promotion on either axis is Dustin's alone.

## 4. Portfolio map

### NS-0 — Authority and truth reset

**Objective:** Establish one trustworthy map of the repository before new feature implementation.

| Packet | State | Outcome | Exit |
|---|---|---|---|
| NS-0A Repository truth reset | `COMPLETE` | Delivered by the 2026-07-30 reconciliation (PR #175), its 2026-07-31 fidelity delta, and the implementation program's verified baseline | Met at `main` `5fe8ad7`: SHA, open PRs (#184, #185, and this PR #187), PRDs, packets, and debt agree or are explicitly recorded as open debt (CB-28: the `PROJECT_STATE` "Active PRD: none" line vs four `IN PROGRESS` registry rows); validator exit 0 |
| NS-0B Vision preservation | `NOW — COMPLETE UPON DUSTIN'S MERGE OF PR #187` | This ledger + the implementation program (PR #187) — the current active documentation packet | Dustin's merge is the ratifying and completing act; no post-merge transition commit is required. On merge the `NOW` slot is intentionally vacant until Dustin's A/B runway ruling promotes a packet |
| NS-0C Debt classification | `COMPLETE` | Every known debt labeled blocking / non-blocking / parked / drafted / retired / UNKNOWN-unadjudicated (program §5) | Nothing silently becomes the next task |

Boundary: read-only reconciliation plus product documentation. No production implementation.

Scope note: `L0` remains the current packet inside the decision-support
workplan's own ledger; NS-0B is the current North Star portfolio ratification
packet. The two labels live in separate scoped ledgers and authorize no
concurrent implementation. After PR #187 merges, NS-0B completes and no North
Star implementation packet is promoted until Dustin rules.

### NS-1 — Candidate fidelity and backtesting repairs

**Objective:** Make intended engine behavior, direct-path behavior, and evidence artifacts agree before performance interpretation.

| Packet | State | Outcome | Exit |
|---|---|---|---|
| NS-1A SPY direct-path fidelity | `COMPLETE` | Delivered by the 2026-07-31 fidelity delta on `main`: counts recomputed, kill-switch effect verified, seam conclusion = proxy posture defect only, no engine change | Met; residual is the Strategy-repo D2 ruling (Dustin) |
| NS-1B Artifact/provenance repair | `COMPLETE` (Cuttingboard side) | Canonical files hash-pinned; exploratory vs frozen lineage separated; manifests verified | Strategy-side dated correction (D2) and the post-patch script identity gap remain Dustin's ruling |
| NS-1C Engine seam corrections | `BLOCKED` | Fix only confirmed mismatches — the fidelity delta confirmed **zero** Cuttingboard-side mismatches at this pin (the one rule mismatch is proxy-side) | Entry condition unmet; reopen only on a confirmed engine mismatch |
| NS-1D Prospective baseline freeze | `LATER` | Observe outcomes without tuning — preserved evaluation capability | Dustin-only promotion after the relevant decision surfaces and frozen baseline are ready; frozen rules and timestamped captures |
| NS-1E Smallest-contract refusal (CB-02 / PRD-278) | `PARKED / DUSTIN DECISION REQUIRED` | Refusal instead of a silent budget-breaching one-contract floor; rejection becomes first-class evidence. Becomes `NOW` only if Dustin explicitly resumes it | If resumed: GOV-2 §12 sequence on PRs #184/#185 — exact-head confirmation, PRD review, Dustin Gate A, implementation, Dustin merge |

Evidence to preserve:

- SPY daily stage counts and rejection decomposition;
- kill-switch removals;
- materially different export with only small result change;
- Opening Drive implementation identity and honest negative result;
- distinction between implementation fidelity and profitability.

### NS-2 — Fixed SPY observation and Market Control Card

**Objective:** Deliver the first visible post-governance product win.

| Packet | State | Outcome | Exit |
|---|---|---|---|
| NS-2A Fixed SPY observation | `NEXT` | Observe SPY on every relevant run, including `STAY_FLAT` and halted states | Independent of candidate availability |
| NS-2B Session-correct ORB | `NEXT` | Use the intended market session, not a positional data tail — rides PRD-271 (IN PROGRESS scaffold, HIGH-RISK, Gate A pending); never a duplicate ORB truth | Correct morning through late session and half-days |
| NS-2C Session VWAP | `NEXT` | Authoritative session-anchored typical-price VWAP | Source window, timestamp, and stale behavior explicit |
| NS-2D Meaningful intraday event | `LATER` | Preserve and expose the last meaningful transition | Rich state is not flattened or discarded |
| NS-2E Market Control Card | `NEXT` | Compact orientation replacing/refactoring generic Market Map | Answers state, location, event, transition, invalidation, permission, candidate implication |
| NS-2F Ranked control ladder | `LATER` | Support, pivot, resistance, structural failure | Evidence-linked, non-predictive |

### NS-3 — Opportunity Set Engine

**Objective:** Show the whole landscape, not only surviving trades.

| Packet | State | Outcome |
|---|---|---|
| NS-3A Opportunity taxonomy | `LATER` | Grade A, Near Qualification, Developing, Watch, Invalidated, Macro Conflict, Stay Flat |
| NS-3B Funnel visibility | `LATER` | Universe → Macro → Trend → Risk → Qualified → Grade A |
| NS-3C Negative market statements | `LATER` | “No quality longs,” “breakouts failing,” and similar evidence-based summaries |
| NS-3D Maturity/deterioration views | `LATER` | Emerging, improving, mature, deteriorating |
| NS-3E Confidence decomposition | `LATER` | Explain why confidence exists or is withheld |

### NS-4 — Universe registry and heatmap

**Objective:** Build the shared substrate for watchlists, news, GEX context, relative behavior, and visual compression.

| Packet | State | Outcome |
|---|---|---|
| NS-4A Universe registry | `LATER` | Human-authored symbols, aliases, themes, roles, horizons, benchmarks, questions |
| NS-4B Movement heatmap | `LATER` | Grouped raw movement with visible freshness |
| NS-4C Leadership mode | `LATER` | Relative performance versus assigned benchmark |
| NS-4D Participation mode | `LATER` | Breadth inside each group |
| NS-4E External watchlist mirror | `LATER` | One consistent universe across tools |

Suggested groups: Context, Energy, AI / Semis, Tradeable, Spec / Learning, Holdings.

> **Observe wide. Trade narrow.**

### NS-5 — Air-gapped GEX context

**Objective:** Add options-structure context without making GEX a signal or permission input.

| Packet | State | Outcome |
|---|---|---|
| GEX-0 Provider evidence pass | `LATER / EVIDENCE BLOCKED` | Test one provider against a bounded honesty contract — never attempted (the Stage-0 leg ran network-disabled); requires a Dustin-commissioned network charge |
| GEX-1 Manual cached producer | `LATER / EVIDENCE BLOCKED` | Versioned gamma flip, put wall, and call wall snapshot — lifecycle state per the workplan, gated on GEX-0 passing |
| GEX-2 Display-only consumer | `LATER / EVIDENCE BLOCKED` | Compact dashboard row with no qualification/sizing effect — lifecycle state per the workplan, gated on GEX-1 |
| GEX-3 Cadence decision | `LATER` | Premarket and bounded intraday refresh only after usefulness (no workplan lifecycle row; doctrine gate GEX-3 applies) |

Required honesty: provider, model or provider-defined label, expiry scope, source/as-of time, observation time, spot basis, stale/unavailable state.

> **GEX is context, not a magic signal.**

### NS-6 — Relationship-aware news

**Objective:** Explain relevant movement through a static, human-approved relationship graph.

| Packet | State | Outcome |
|---|---|---|
| NEWS-0 Static relationship registry | `LATER / EVIDENCE BLOCKED` | Symbols, aliases, themes, benchmarks, related companies, approved sources — nothing drafted yet; the workplan gates it and Dustin supplies/ratifies the universe |
| NEWS-1 Manual producer | `LATER / EVIDENCE BLOCKED` | Small deterministic artifact, normally 2–3 items and never over 5 — lifecycle state per the workplan, gated on NEWS-0 |
| NEWS-2 Usefulness evaluation | `LATER / EVIDENCE BLOCKED` | Dustin chooses KEEP, one bounded REVISE, or RETIRE — lifecycle state per the workplan, gated on NEWS-1 |
| NEWS-3 Display consumer | `LATER / EVIDENCE BLOCKED` | Display-only, baseline-neutral context — lifecycle state per the workplan, gated on NEWS-2 `KEEP` |
| NEWS-4 Cadence | `LATER` | Scheduling only after demonstrated usefulness (no workplan lifecycle row; doctrine gate NEWS-4 applies) |

Relationship path:

```text
GLOBAL STATE
    ↓
THEME HEALTH
    ↓
THEME LEADERS
    ↓
WATCHLIST
    ↓
SETUPS
    ↓
TRADES
```

### NS-7 — Idiosyncratic decoupling

**Objective:** Surface when a company diverges materially from its benchmark/theme and connect that divergence to context.

| Packet | State | Outcome |
|---|---|---|
| NS-7A Decoupling contract | `LATER` | Window, benchmark, threshold, freshness |
| NS-7B Heatmap label | `LATER` | Compact idiosyncratic/broad classification |
| NS-7C News link | `LATER` | Connect divergence to catalysts when present without inventing cause |

Examples: AVGO vs SOXX, OXY vs energy/crude, NVDA vs QQQ.

### NS-8 — Prospective decision evaluation

**Objective:** Evaluate whether CuttingBoard improves Dustin's decisions without pretending the system is a single backtestable strategy.

| Packet | State | Outcome |
|---|---|---|
| NS-8A Cohort capture | `LATER` | Qualified, near-miss, excluded-by-reason, and `STAY_FLAT` cohorts |
| NS-8B Decision linkage | `LATER` | What was shown, what Dustin did, whether behavior changed |
| NS-8C Counterfactual observation | `LATER` | Subsequent outcomes for rejected and abstained cases |
| NS-8D Usefulness measures | `LATER` | Comprehension time, outside-screen dependence, override quality, abstention value |
| NS-8E Review cadence | `LATER` | Human review after adequate sample; no threshold tuning during baseline |

```text
Macro State
→ Opportunity Set Engine
→ Qualification
→ Paper Trading Sandbox
→ Review
→ Statistics
```

### NS-9 — Scheduling and freshness

**Objective:** Make correct analysis operationally trustworthy.

| Packet | State | Outcome |
|---|---|---|
| NS-9A Run identity | `LATER` | Nominal slot, trading date, idempotency key |
| NS-9B Execution observability | `LATER` | Trigger, start, source times, completion/failure |
| NS-9C Artifact freshness | `LATER` | Current/stale/unavailable visible to every consumer |
| NS-9D Cadence promotion | `LATER` | Schedule producers only after usefulness |

> **The clock declares when. The pipeline decides how.**

## 5. Existing work, debt, and parked material

Verified against the live repository on 2026-08-01 (`main` `5fe8ad7`); full
citations in the implementation program's source map.

### Options/reconciliation chain

| Item | Working state | Verified truth |
|---|---|---|
| OPT-0 — PR #184 (open draft, head `24660ac`) | `PARKED / DUSTIN DECISION REQUIRED` (lifecycle: `EVIDENCE BLOCKED` per the workplan) | The upstream MATERIAL packet for NS-1E; findings artifacts committed, all 13 connector threads actioned — progress, but OPT-0's governed exit is unsatisfied: independent exact-corrected-head confirmation plus Dustin's approval of the carrier, reason semantics, and implementation seam all remain outstanding |
| OPT-1 — PR #185 (open draft, head `ee2d12e`) | `DRAFTED / BLOCKED` (lifecycle: `EVIDENCE BLOCKED` per the workplan, gated on OPT-0's exit) | PRD-278 Stage 0 + draft Gate A entry; the prior `DECISIONS.md` blocker is RESOLVED (Finding D ruling merged via PR #167, 2026-07-26); remaining: nine-file-ruling consistency, independent PRD review, Dustin Gate A |
| PRD-271 lifecycle/document gap | `BLOCKED` (this ledger's lifecycle-condition axis, §3) — a separate axis from, and not in conflict with, the registry's PRD-lifecycle value `IN PROGRESS` for PRD-271; see §3 above for the two-axis distinction | Document landed with its index entry via PR #173; Gate A (ORB remedy design ruling) pending with Dustin — also the NS-2B prerequisite |
| PRD-267/272/273 closeout | `COMPLETE` | Closed 2026-07-26 / 2026-07-31 (`724d84a`, `724d84a`, `4a1cb22`); registry, index, and validator agree (exit 0) |
| PRD-268 scaffold/design fork | `IN PROGRESS / DECISION REQUIRED` | Canonical lifecycle state unchanged (registry: IN PROGRESS), design fork unruled; Dustin chooses approve / return to PROPOSED / deprecate (one of L0's two open rulings — the other is PRD-271 Gate A) |
| Registry validator historical warnings | `RETIRED` | Phantom-SHA class closed WONTFIX-HISTORICAL (PRD-243); CI keeps `--skip-commit-resolvability` permanently; CB-12 residual bypasses remain non-blocking debt |

### Candidate-fidelity evidence debt

Resolved by the 2026-07-31 fidelity delta
(`audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md`,
on `main`), which hash-pinned every canonical artifact and recomputed every
headline count.

| Item | State | Verified truth |
|---|---|---|
| Export naming/content swaps | `COMPLETE` | Canonical files selected and SHA-256-pinned at the strategy pin |
| Partial-window or duplicate exports | `COMPLETE` | Pre-patch (`e28aa874`) vs post-patch (`2d375b4c`) exports separated with explicit lineage; corrected analogs 284 / 79 / 112 recomputed |
| Run manifests | `COMPLETE` | Frozen AS-IS manifest verified (script and export hashes recomputed, capture provenance recorded) |
| Pre-patch/post-patch lineage | `COMPLETE` | Exploratory vs authoritative labeled; the registered AS-IS run is floor-only-posture evidence, not a Cuttingboard-semantics description |
| TradingView-to-engine mismatches | `COMPLETE` | Exactly one confirmed rule mismatch, and it is proxy-side (missing 0.55 posture tier); zero Cuttingboard defects promoted. Residuals held for Dustin: D2 Strategy-side dated correction; the post-patch script identity gap stays preserved-open |

### Dormant and parked work

| Item | State | Disposition |
|---|---|---|
| PRD-187/188 macro-awareness track | `PARKED / DECISION REQUIRED` | KEEP DORMANT, PROMOTE after gates, or RETIRE |
| PRD-259 Findings E/F | `PARKED` | Presentation/consumer debt |
| PRD-259 Finding G | `PARKED` | Possible small presentation correction |
| Old options-data proposals | `PARKED` | Revisit after the current candidate/refusal path |
| PR #186 adjacent governance ideas | `PARKED` | Promote only from real product evidence |
| Model/process optimization | `PARKED` | Not a product workstream |

For at least the next three product slices:

- no proactive governance redesign;
- no doctrine consistency sweeps;
- no historical review archaeology;
- no process optimization unless the active product slice is truly blocked.

## 6. Recommended order (reconciled to repository truth, 2026-08-01)

NS-0A and NS-1A/B — the draft's original NOW — are already delivered on
`main`. The runway holds exactly one packet: this ratification branch.

### NOW

1. **NS-0B — North Star ratification** (this ledger + the implementation
   program, this branch). Held for Dustin's decision.

### DUSTIN'S IMMEDIATE RUNWAY CHOICE (neither option is chosen here)

- **A.** Resume and finish CB-02 (NS-1E; PRs #184/#185, parked under GOV-2
  §12), then begin fixed SPY observation.
- **B.** Leave CB-02 parked and promote fixed SPY observation directly,
  after resolving its exact prerequisite (the PRD-271 Gate A ORB ruling).
  Option B also requires the explicit CB-01 safety ruling (promote it ahead
  of product expansion, or defer it with acknowledged risk) — it cannot
  silently bypass CB-01 (program §5).

### NEXT

2. NS-2A/B/C — fixed SPY observation, session ORB, session VWAP, visible
   freshness: the proposed first trader-facing product slice. Prerequisite
   either way: the PRD-271 Gate A ruling (the ORB remedy the observation
   card and the execution gate must share). MATERIAL under GOV-2 — begins
   with its upstream packet, seeded by the stage0-01 decision-surface recon.
3. NS-2E — Market Control Card

### LATER

4. NS-4A/B — universe registry and basic movement heatmap (first named
   promotion candidates after NS-2E; promotion is Dustin's)
5. Opportunity Set Engine
6. GEX evidence → producer → display
7. Relationship-aware news registry → producer → usefulness decision → display
8. Decoupling detection
9. Prospective decision evaluation
10. Scheduling/freshness promotion

Why:

- fidelity protects truth — CB-02 is fidelity at the sizing seam (the
  refusal the operator already ruled for), which is the case for option A;
- SPY observation and the Control Card create immediate daily usefulness;
- the registry unlocks several later products cheaply;
- heatmap offers high information value at low cognitive cost;
- GEX remains bounded;
- news follows the registry because it is the deepest swamp;
- evaluation becomes meaningful after stable decision surfaces exist.

## 7. Standard North Star packet

```text
Packet ID:
Status:
Trader question served:
Operator outcome:
Why now:
Dependencies:
Explicit non-goals:
Expected files/areas:
Acceptance contract:
Baseline-neutral behavior:
Evidence produced:
Review scope:
Stop conditions:
Debt discovered:
Dustin decision required:
```

### Closed acceptance rule

A checker may return only:

- exact reviewed SHA;
- each named requirement as PASS/FAIL;
- one blocking explanation per failed requirement;
- ACCEPT or REJECT.

It may not add adjacent requirements during closeout.

## 8. Weekly product ledger

| Measure | Result |
|---|---|
| Trader-facing capability added | |
| Product question answered better | |
| Evidence captured | |
| Time-to-comprehension change | |
| External-screen dependence change | |
| Product hours | |
| Governance/review hours | |
| Debt parked instead of derailing delivery | |
| Next single product slice | |

A healthy week makes CuttingBoard more useful to Dustin. Governance output without trader-facing progress is an unhealthy product week.

## 9. Dustin ratification points

1. Name the initiative **NORTH STAR**.
2. Make this ledger the authoritative portfolio map.
3. Confirm the `NOW → NEXT → LATER` order.
4. Confirm the first trader-facing target: fixed SPY observation with session-correct ORB/VWAP and visible freshness — sequenced by the A/B runway choice (resume CB-02 first, or go straight to SPY observation).
5. Freeze proactive governance work for the next three product slices.
6. Keep GEX context-only and air-gapped.
7. Begin news with a Dustin-ratified relationship registry.
8. Evaluate a frozen engine prospectively rather than tuning it from outcomes.

## 10. Claude planning mission

After live repository truth is reconciled and Dustin ratifies the ledger, Claude should produce an implementation program—not implementation code—with:

1. exact mapping from current documents, PRDs, PRs, findings, and parked material into each North Star packet;
2. duplicates and superseded plans identified;
3. current technical-debt disposition;
4. dependency graph;
5. one bounded implementation plan for the active packet only;
6. explicit acceptance contract before code;
7. no new governance initiative;
8. no promotion of `NEXT` or `LATER` without Dustin's ruling.

The full cosmic vision remains visible while only one small, finishable product slice reaches the runway.

**Delivered:** `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`
(2026-08-01) — verified baseline, source map, dependency graph, debt ledger,
single-runway adjudication, acceptance contract, and the not-lost appendix.
It carried the same merge-contingent status as this ledger and was ratified
and completed upon Dustin's merge of PR #187 (merge commit
`fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`); it authorizes nothing beyond
that ratification.
