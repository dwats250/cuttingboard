# CuttingBoard North Star Master Ledger v0.1

**Initiative:** NORTH STAR  
**Status:** DRAFT FOR DUSTIN RATIFICATION  
**Owner and final authority:** Dustin  
**Purpose:** Preserve the full product vision, map all active/drafted/parked/debt work, and prevent governance from displacing trader-facing delivery.

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

## 4. Portfolio map

### NS-0 — Authority and truth reset

**Objective:** Establish one trustworthy map of the repository before new feature implementation.

| Packet | State | Outcome | Exit |
|---|---|---|---|
| NS-0A Repository truth reset | `NOW` | Inventory active, merged, drafted, blocked, parked, and stale work | Main SHA, open PRs, PRDs, packets, and debt agree |
| NS-0B Vision preservation | `NOW` | Ratified North Star and master ledger | Accessible from normal repository entry points |
| NS-0C Debt classification | `RECONCILE` | Label every debt blocking, non-blocking, parked, or retired | Nothing silently becomes the next task |

Boundary: read-only reconciliation plus product documentation. No production implementation.

### NS-1 — Candidate fidelity and backtesting repairs

**Objective:** Make intended engine behavior, direct-path behavior, and evidence artifacts agree before performance interpretation.

| Packet | State | Outcome | Exit |
|---|---|---|---|
| NS-1A SPY direct-path fidelity | `RECONCILE` | Verify candidates surface/reject for intended reasons | Complete counts, reasons, kill-switch effect, and seam conclusions |
| NS-1B Artifact/provenance repair | `RECONCILE` | Preserve exploratory lineage without confusing it with frozen studies | Canonical files, truthful names, manifests, and pre/post-patch provenance |
| NS-1C Engine seam corrections | `BLOCKED` | Fix only confirmed mismatches | Named mismatches fixed; unrelated thresholds unchanged |
| NS-1D Prospective baseline freeze | `NEXT` | Observe outcomes without tuning | Frozen rules and timestamped captures |

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
| NS-2B Session-correct ORB | `NEXT` | Use the intended market session, not a positional data tail | Correct morning through late session and half-days |
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
| GEX-0 Provider evidence pass | `DRAFTED / BLOCKED` | Test one provider against a bounded honesty contract |
| GEX-1 Manual cached producer | `LATER` | Versioned gamma flip, put wall, and call wall snapshot |
| GEX-2 Display-only consumer | `LATER` | Compact dashboard row with no qualification/sizing effect |
| GEX-3 Cadence decision | `LATER` | Premarket and bounded intraday refresh only after usefulness |

Required honesty: provider, model or provider-defined label, expiry scope, source/as-of time, observation time, spot basis, stale/unavailable state.

> **GEX is context, not a magic signal.**

### NS-6 — Relationship-aware news

**Objective:** Explain relevant movement through a static, human-approved relationship graph.

| Packet | State | Outcome |
|---|---|---|
| NEWS-0 Static relationship registry | `DRAFTED / BLOCKED` | Symbols, aliases, themes, benchmarks, related companies, approved sources |
| NEWS-1 Manual producer | `LATER` | Small deterministic artifact, normally 2–3 items and never over 5 |
| NEWS-2 Usefulness evaluation | `LATER` | Dustin chooses KEEP, one bounded REVISE, or RETIRE |
| NEWS-3 Display consumer | `LATER` | Display-only, baseline-neutral context |
| NEWS-4 Cadence | `LATER` | Scheduling only after demonstrated usefulness |

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

These entries preserve known work but require live-repository verification in NS-0A.

### Options/reconciliation chain

| Item | Working state | Truth check |
|---|---|---|
| OPT-0 / historically PR #184 | `RECONCILE` | Current state, exact head, findings artifact, resolved findings |
| OPT-1 / historically PR #185 | `RECONCILE` | Current state and whether the prior `docs/DECISIONS.md` blocker remains |
| PRD-271 lifecycle/document gap | `RECONCILE` | Gate A and landing status |
| PRD-267/272/273 closeout | `RECONCILE` | Registry, documents, provenance, project-state agreement |
| PRD-268 scaffold/design fork | `RECONCILE` | Approved, proposed, deprecated, or unresolved |
| Registry validator historical warnings | `PARKED / RECONCILE` | Confirm unchanged baseline and separate cleanup status |

### Candidate-fidelity evidence debt

| Item | State | Action |
|---|---|---|
| Export naming/content swaps | `RECONCILE` | Select canonical files |
| Partial-window or duplicate exports | `RECONCILE` | Preserve truthful canonical artifacts and explicit archive lineage |
| Run manifests | `RECONCILE` | Freeze script/version, data source, chart/session settings, capture time |
| Pre-patch/post-patch lineage | `RECONCILE` | Label exploratory versus authoritative |
| TradingView-to-engine mismatches | `RECONCILE` | Promote only confirmed defects |

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

## 6. Recommended order

### NOW

1. NS-0A — repository truth reset
2. NS-0B — ratify and land this ledger
3. NS-1A/B — candidate-fidelity truth and artifact preservation

### NEXT

4. NS-2A/B/C — fixed SPY observation, session ORB, session VWAP
5. NS-2E — Market Control Card
6. NS-4A/B — universe registry and basic movement heatmap

### LATER

7. Opportunity Set Engine
8. GEX evidence → producer → display
9. Relationship-aware news registry → producer → usefulness decision → display
10. Decoupling detection
11. Prospective decision evaluation
12. Scheduling/freshness promotion

Why:

- fidelity protects truth;
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
4. Confirm the first visible target: fixed SPY observation with session-correct ORB/VWAP and visible freshness.
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
