# North Star Implementation Program v0.1

**Initiative:** NORTH STAR
**Status:** RATIFIED — ratified and complete as of Dustin's merge of PR #187
(merge commit `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`, 2026-08-02); grants
no implementation permission. This line previously carried a pre-merge
draft/awaiting-ratification banner naming PR #187's then-pending merge; that
banner no longer applies now that the merge has occurred.
**Owner and final authority:** Dustin
**Companion:** `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` (the vision;
this document is the portfolio implementation program the ledger's §10 commissions)

This is a portfolio implementation program, not an implementation plan for every
feature. It maps every existing plan, finding, draft, and debt into the North
Star packets, names the one packet on the runway, and preserves everything else
without authorizing it. Every status below was verified against the live
repository at the baseline in §2; nothing here is asserted from chat history or
stale PR bodies. It allocates no PRD number and changes no lifecycle status.

## 1. Purpose and the four product questions

CuttingBoard is Dustin's personal trading decision-support cockpit. Every
workstream in this program serves at least one of:

1. What environment exists?
2. What matters today?
3. Is anything tradable?
4. What would invalidate or change the read?

> **State first. Trades second.**

Governance in this program is subordinate to product delivery: the only
governance activity on the runway is the already-ratified GOV-2 sequence that
any resumed implementation packet must clear. No new governance initiative is
opened here.

## 2. Verified repository baseline (2026-08-01)

**Post-merge note:** this baseline snapshot predates PR #187's own merge —
it records the repository state as observed while #187 was still open. PR
#187 has since merged as `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`. The
table below is preserved as a historical snapshot, not rewritten.

| Fact | Value | Source |
|---|---|---|
| `main` | `5fe8ad7216130d46d739510cc61257e6300080d9` (GOV-2 merge, PR #186) | `git rev-parse origin/main`, this session |
| Working branch | `docs/north-star-master-ledger`, started at `4b573efbb3059aaa6e1d01752e8512e48cb0c9f3` (= `main` + the ledger commit) | `git rev-parse`, this session |
| Open PRs | Three: **#184** (OPT-0 seam-trace packet, draft, head `24660ac`), **#185** (PRD-278 Stage 0, draft, head `ee2d12e`), and **#187** (this North Star ratification PR). The 2026-08-01 verification snapshot predated #187's opening; #184/#185 are held for Dustin per GOV-2 §12. **#187 has since merged as `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`; #184/#185 remain open per this row.** | GitHub API, this session; updated at the #187 correction pass |
| Registry validator | `tools/validate_prd_registry.py --skip-commit-resolvability` exit 0 at `4b573efb` | run this session |
| Test baseline | 3075 passed, 1 xfailed (CI truth on `main` at `4b0f3ba`) | `docs/PROJECT_STATE.md` |
| Active PRD (implementation) | None in progress | `docs/PROJECT_STATE.md`; registry |
| Registry IN PROGRESS rows | PRD-268 (scaffold, design fork unruled), PRD-271 (ORB scaffold, Gate A pending), PRD-274 (queued), PRD-275 (blocked by six DECISIONS 2026-07-26 constraints) | `docs/PRD_REGISTRY.md` |
| PRD numbering | `prd_index.json`: `latest_complete: 277`, `next_prd: 278`. **PRD-278 is already allocated on unmerged PR #185**; the first number free after #185 lands is 279. This program allocates nothing. | `docs/prd_index.json`; PR #185 |
| GOV-2 | RATIFIED (Dustin's merge of PR #186; DECISIONS 2026-08-01). Its §12 explicitly governs PRs #184/#185. | `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` |
| Finding D ruling | CANONICAL on `main` — PR #167 merged 2026-07-26 | DECISIONS 2026-07-24; PR #167 merge state |

PRs relevant to North Star, resolved:

- **#184 (open draft)** — OPT-0 smallest-contract-refusal seam trace. The
  upstream MATERIAL packet for CB-02. Findings artifacts committed under
  `audits/current-state-reconciliation-2026-07-30/`; all thirteen connector
  threads actioned/resolved. Outstanding per GOV-2 §12: independent
  exact-corrected-head confirmation.
- **#185 (open draft)** — PRD-278 Stage 0 (CB-02 refusal PRD + Gate A DECISIONS
  entry). Outstanding per GOV-2 §12: the final canonical nine-file ruling held
  consistently across its five files, then the fresh-context independent PRD
  review, then Dustin's Gate A.
- **#187 (merged as `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`)** — the NS-0B
  ratification vehicle carrying both North Star documents and the
  PROJECT_STATE pointer. This line originally described #187 as open; it has
  since merged.
- **#167 (merged)**, **#174 (merged)**, **#175 (merged)** — no longer blockers;
  see §3.

## 3. Source map

Every named North Star concern, its current authority, destination, and
disposition. "Authoritative" means the artifact still governs its subject at
the §2 baseline.

| Source (exact path or PR) | Current status | North Star destination | Authoritative? | Disposition |
|---|---|---|---|---|
| `docs/plans/decision-support-workplan-v0.1.md` | On `main`; GOV-0 COMPLETE; several rows stale (see below) | NS-0 / NS-1 / NS-5 / NS-6, sequencing law | YES for track gates; row states partially stale | RETAINED. Stale row: `D-RULE` (merged via #167 → COMPLETE). Clarified rows: `L0` (the new-PRD allocation freeze has ended — its named conditions resolved: PRD-271 document landed, 267/272/273 COMPLETE, validator green — but **L0 itself remains IN PROGRESS** until PRD-268's disposition and PRD-271's Gate A land), `OPT-0` (portfolio `PARKED / DUSTIN DECISION REQUIRED`; lifecycle `EVIDENCE BLOCKED` per the workplan — drafting PR #184's upstream packet is progress but does not satisfy OPT-0's governed exit, which still requires independent exact-corrected-head confirmation plus Dustin's approval of the carrier, the reason semantics, and the implementation seam) |
| `docs/plans/decision-support-expansion-doctrine-v0.1.md` | On `main`; binding | NS-5 (GEX gates), NS-6 (news gates), NS-1/ODATA (options contract), global invariants G1–G10 | YES | RETAINED. North Star packets NS-5/NS-6 restate its gates; the doctrine remains the boundary authority |
| `docs/plans/agent-work-charge-template-v0.1.md` | On `main`; binding | All packet execution | YES | RETAINED |
| `audits/current-state-reconciliation-2026-07-30/` (CHARTER, EVIDENCE_INDEX, FINDING_STATUS_MATRIX, RECONCILIATION_REPORT) | On `main` (PR #175); pin `9e6b772`; revised after a 12/12-correct connector review | NS-0A (delivered), debt ledger §5 (CB-01…CB-47) | YES as findings evidence; statuses are Dustin's to move | RETAINED. This IS the repository truth reset the ledger's NS-0A asked for |
| `audits/current-state-reconciliation-2026-07-30/STRATEGY_CANDIDATE_FIDELITY_DELTA_2026-07-31.md` | On `main` (`f6d508f`); pins verified by hash | NS-1A/NS-1B (delivered) | YES | RETAINED. Cuttingboard-side candidate-fidelity truth is settled: proxy posture defect only, no engine change, no doc drift. Residual is Strategy-repo decision D2 |
| `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md` (+ `verify-01`) | On `main`; SHA-pinned recon @ `771f730` | NS-2A/2B/2C/2E evidence base | YES as evidence; HYPOTHESIS-class consequences, no authority | RETAINED. Seeds the future NS-2 MATERIAL packet: producer/ownership map, positional-ORB runtime repro, two-axis lifecycle schema, Control Card row disposition |
| `audits/stage0-recon-2026-07-20/stage0-02-evaluation-v0.1.md` (+ `verify-02`) | On `main` | NS-8 evidence base | YES as evidence | RETAINED for NS-8 (cohort schema, `stay_flat_reason` audit gap, session-clustering absence) |
| `audits/stage0-recon-2026-07-20/stage0-03-scheduler-v0.1.md` (+ `verify-03`) | On `main` | NS-9 evidence base | YES as evidence | RETAINED for NS-9 (schedule owners, force/dedup semantics, verify-mode diagnostic baseline, "observed replacement" bar) |
| `audits/stage0-recon-2026-07-20/stage0-04-gex-v0.1.md` | On `main`; corrected verdict `NOT ATTEMPTED — EXTERNAL REACH DISABLED` | NS-5 | YES (repo-only claim: no GEX exists) | RETAINED. The original "NO VIABLE PROVIDER" verdict is superseded by the in-file re-disposition; GEX-0 has NOT been run |
| `audits/stage0-recon-2026-07-20/stage0-05-governance-debt-v0.1.md` (+ `verify-05`) | On `main` | Debt ledger | YES as evidence | RETAINED |
| PR #184 artifacts (`OPT_0_SMALLEST_CONTRACT_REFUSAL_SEAM_TRACE_2026-07-31.md`, addendum) | Open draft branch `worktree-opt-0-seam-trace` | NS-1E (CB-02) | YES as the upstream MATERIAL packet, pending exact-head confirmation | PARKED — DUSTIN DECISION REQUIRED (resume or leave parked). See §7 |
| PR #185 (`PRD-278.md`, Gate A ruling draft, registry/index edits) | Open draft branch `worktree-opt-1-prd` | NS-1E (CB-02) | Drafting only; no authority until reviewed + Gate A | PARKED — DUSTIN DECISION REQUIRED. See §7 |
| `docs/prd_history/PRD-271.md` | IN PROGRESS Stage-0 scaffold on `main`; **Gate A pending**; HIGH-RISK/EXECUTION | NS-2B (session-correct ORB) | YES — it owns the ORB defect (CB-07) | RETAINED, BLOCKED on Dustin's Gate A design ruling. NS-2B must ride this PRD, not duplicate it |
| `docs/prd_history/PRD-268.md` | IN PROGRESS scaffold; design fork unruled; HIGH-RISK | Debt ledger (drafted) | Scaffold only | REQUIRES DUSTIN RULING: approve / return to PROPOSED / deprecate (workplan L0 step 2, still open) |
| `docs/prd_history/PRD-274.md` | IN PROGRESS (queued); restores ruff resolved-rule coverage | Debt ledger (non-blocking) | YES | RETAINED, queued; not runway work |
| `docs/prd_history/PRD-275.md` | IN PROGRESS; blocked by six constraints (DECISIONS 2026-07-26) | Debt ledger (drafted/blocked) | YES | RETAINED, blocked; must not be implemented as sketched |
| `docs/prd_history/PRD-187.md` / `PRD-188.md` | 187 COMPLETE (dormant producer); 188 PROPOSED, gates unmet | MACRO-0 decision (workplan Wave 3) | YES | REQUIRES DUSTIN RULING: KEEP DORMANT / PROMOTE after splitting cadence / RETIRE. No fourth implicit state |
| `docs/prd_history/PRD-259.first-fire-consumers.proposal.md` | Findings E/F deferred, G parked, D ruled + tracked by CB-02; header disposition incomplete (DOC-0 still PROPOSED) | Debt ledger (parked); DOC-0 | Evidence yes; header stale by its own admission (doctrine G10 names it tracked debt) | RETAINED. DOC-0 header correction remains open, non-blocking |
| `docs/prd_history/PRD-209.md` | PROPOSED, shelved reopen-on-incident | Debt ledger (parked) | YES | RETAINED |
| Old options-data proposals (A1b / live economics, per workplan Wave 6) | Superseded as queue authority by the workplan | ODATA-0 (after CB-02) | Evidence only | RETAINED as evidence for the ODATA-0 recon; numbers not carried forward |
| TradingView/backtesting evidence (`dwats250/strategy` pins in the fidelity delta) | Hash-pinned at strategy `1aefaaa`; registered AS-IS run carries the floor-only posture defect | NS-1B residual; Dustin decision D2 | YES as pinned evidence | REQUIRES DUSTIN RULING (D2): Strategy-side dated correction; script identity gap preserved-open unless the operator-held script is committed |
| Market Map / decision-surface findings (stage0-01 Q10–Q12; `_render_candidate_card`) | Current surface is the candidate card; no Control Card contract exists | NS-2E | YES as evidence | RETAINED; row-disposition hypotheses feed the NS-2 packet |
| Fixed-SPY-observation work | **None exists in production.** No durable session-observation artifact; `watch.py` ORB positional defect reproduced twice | NS-2A | n/a | The slice is genuinely unbuilt; see §6 NEXT |
| Universe substrate (`config.TREND_STRUCTURE_SYMBOLS`, `market_map.PRIMARY_SYMBOLS`) | Two agreeing fixed six-symbol tuples | NS-4A seed | YES | RETAINED as the registry seed; NS-4A stays LATER |
| Registry-validator / closeout debt | Phantom-SHA class CLOSED WONTFIX-HISTORICAL (PRD-243); CI keeps `--skip-commit-resolvability` permanently; CB-12 residual bypasses PARTIAL, narrowed by PRD-276/277 | Debt ledger | YES | RETIRED as a work item (historical class); CB-12 residuals stay non-blocking debt |
| GOV-2 (`docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md`) | RATIFIED | Process spine of any implementation packet; MATERIAL intake test for every future NS packet | YES | BINDING. Not part of the product portfolio itself |

## 4. Dependency graph (NS-0 → NS-9)

```text
NS-0 (truth reset + ratification)          [DELIVERED; ratified via PR #187's merge as `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae` — this line previously read "ratification pending" before that merge]
  └─ everything below

NS-1E CB-02 refusal (PARKED / DUSTIN DECISION REQUIRED; PRs #184/#185,
  GOV-2 §12 sequence if resumed)
  ├─ unlocks ODATA-0 backlog recon (workplan: "after OPT-1")
  └─ unlocks PRES-0 Finding G promotion decision

PRD-271 Gate A (ORB session-provenance ruling)  [Dustin]
  └─ NS-2B session-correct ORB
       └─ NS-2A fixed SPY observation + NS-2C session VWAP
            ├─ needs: MATERIAL intake → upstream packet (seeded by stage0-01)
            ├─ NS-2D meaningful intraday event (LATER)
            └─ NS-2E Market Control Card
                 └─ NS-2F ranked control ladder (LATER)

NS-4A universe registry (LATER; seed exists in config)
  ├─ NS-4B heatmap → NS-4C leadership / NS-4D participation / NS-4E mirror
  ├─ NS-6 news registry (NEWS-0; doctrine gates NEWS-0→4)
  └─ NS-7 decoupling (needs benchmarks from the registry + NS-4B)

NS-2A observation artifact + NS-9C freshness vocabulary are shared substrate
  └─ NS-9 scheduling/freshness (evidence: stage0-03; debt anchors CB-18, CB-06)

NS-3 Opportunity Set Engine (LATER; needs qualification introspection —
  the parked near-miss-surface — plus stable NS-2 surfaces)

NS-8 prospective evaluation (LATER; needs NS-2/NS-3 surfaces plus the
  stage0-02 cohort decisions and CB-11 join key; CB-20…CB-25 cluster)

NS-5 GEX (EVIDENCE BLOCKED; GEX-0 requires a Dustin-commissioned
  network-enabled charge; doctrine gates GEX-0→3; air-gapped by G2)
```

No LATER packet inherits permission from this graph; it records only ordering.

## 5. Technical-debt ledger (NS-0C, delivered)

Statuses are recorded, not changed. Severity labels are the reconciliation's.

**Blocking CB-02 (if Dustin resumes it):** none in code. The blockers are the
GOV-2 §12 process steps in §7, all held for Dustin or requiring the
commissioned confirmation event. No repository defect blocks CB-02.

**Dustin-held safety ruling — gates any product expansion: CB-01.**
The hourly channel never evaluates the kill switch and publishes
`kill_switch: False` as a literal (confirmed Critical; no PRD carries it —
the planned number landed unrelated work; the reconciliation's commission
order puts it immediately after CB-02). Required before any implementation
packet begins, under either runway option: one explicit Dustin ruling —
**(A) promote CB-01 ahead of product expansion, or (B) defer it explicitly
with acknowledged risk.** Neither ruling is made here, and CB-01 does not
become `NOW` by this listing; Option B of the runway choice cannot silently
bypass it.

**Conditional packet dependency — blocks NS-2 only: CB-07.**
ORB computed from mid-session bars (`bars[:5]` after `tail(120)`); owned by
PRD-271 (HIGH-RISK, Gate A pending). It does not block CB-02 or North Star
ratification, but NS-2 cannot enter implementation until PRD-271's Gate A
resolves the shared ORB truth that the observation card and the execution
gate must both read.

**Open, non-blocking (named, with owner surface):**

- **CB-03 / CB-04 (High)** — policy size multiplier never resizes;
  trade brakes count recommendations as fills. Settled operator doctrine
  (2026-07-10) exists; recommended as a pair.
- **CB-05 / CB-06 (High)** — macro-pressure fails open; hourly job never goes
  red (readiness tests key presence, not status).
- **CB-08 (High)** — spread economics are a 30%-of-width estimate, never live
  chain pricing (residual of A1; ODATA territory, provider-dependent).
- **CB-10 (High)** — `docs/trade_qualification.md` states $150 where code uses
  $400; cheapest live-hazard removal, deliberately unfixed by the recon charter.
- **CB-11 (High)** — `system_candidate_id` join key never emitted; keystone of
  the NS-8 measurement loop.
- **CB-18 (High)** — freshness measures fetch time, not market time; NS-9
  anchor finding.
- **CB-12 (PARTIAL)** — validator-gate residual bypasses (casing,
  declared-CLASS trust, docless-COMPLETE, existence-not-content), narrowed by
  PRD-276/277; mitigated in practice by GOV-1 universal manual merge.
- **CB-12b (PARTIAL, Medium)** — manual-merge technical backstops, tracked
  separately from CB-12: the reconciliation's §12b live check found
  `enforce_admins` false, no required PR reviews, and checks `["test"]` only;
  CODEOWNERS and a CI changed-path check were never added. Severity
  reassessed down because GOV-1's universal manual merge plus the
  `gh pr merge` deny supersede the unbabysat-agent-merge premise. Source:
  `FINDING_STATUS_MATRIX.md` CB-12b row and RECONCILIATION_REPORT §12b.
- **CB-09, CB-16, CB-17, CB-19–CB-25 (Medium)** — including the six-row
  "records what it said, never what happened" cluster (CB-20–25) that NS-8
  will eventually own.
- **CB-26–CB-29 (Low)** — incl. CB-28 (PROJECT_STATE staleness shape persists:
  "Active PRD: none" vs four IN PROGRESS registry rows) and CB-29 (strategy-repo
  relationship pointer PARTIAL once the delta merged).
- **`runtime/` split mid-way** (PRD-173 skeleton only; re-evaluate by
  2026-08-15 per PROJECT_STATE).
- **Two unfiled MICROs** noted in PROJECT_STATE: `prd_close.sh` Next-step
  regex; `clean_generated_artifacts.sh` restores 4 of 8 dirtied files.
- **PRD-274** — ruff resolved-rule coverage (queued MICRO/INFRA).
- **DOC-0** — stale proposal headers (PRD-251 continuation proposal;
  PRD-259 proposal disposition summary); doctrine G10 names them tracked debt.

**UNKNOWN / UNADJUDICATED (neither blocking nor non-blocking — unverified):**

- **CB-30…CB-47** — eighteen historical findings whose current truth was
  never run to ground; the matrix marks CB-35 and CB-38 with plausible
  Critical/High consequences, and they lead any sweep. These rows never
  become `NOW` automatically; the triage sweep is a Dustin commission. If any
  row is confirmed a live safety blocker, the §10 adjacent-discovery stop
  condition escalates it immediately.

**Parked (reopen only under stated conditions):**

- PRD-187/188 macro-awareness track — **MACRO-0 decision required** (keep
  dormant / promote-after-cadence-split / retire).
- PRD-259 Findings E/F (PRES-0, consumer-contract pass) and G (small
  presentation correction, promotable after CB-02).
- PRD-209 (OHLCV bar-count floor) — shelved, reopen-on-incident.
- near-miss-surface; red-folder-entry-gate; section-registry-refactor;
  present-MANUAL_CHECK render visibility (all with stated reopen conditions in
  PROJECT_STATE).
- Old options-data proposals — ODATA-0 re-recon after CB-02; numbers not
  carried forward.
- PR #186-adjacent governance ideas; model/process optimization — parked; not
  product workstreams.
- `prd-second-model-commission` skill — QUEUED / OPERATOR COMMISSION
  REQUIRED: its queue dependency is cleared, but it remains inactive until
  Dustin explicitly commissions it; current repository sequencing places it
  after PRD-268 (source: stage0-05 governance-debt artifact Q24;
  PROJECT_STATE queue). Not promoted, no PRD allocated, not a new governance
  initiative.

**Drafted (exists, not authorized):**

- PRD-278 (PR #185) and the OPT-0 packet (PR #184) — the parked CB-02
  packet's documents (resume is Dustin's ruling).
- PRD-271 scaffold (Gate A pending), PRD-268 scaffold (fork unruled),
  PRD-275 (blocked by six constraints).

**FIXED / COMPLETE (verified at the reconciliation, discriminating tests read
by its lead):**

- **CB-13 — credit-spread max risk (was Critical): FIXED / COMPLETE.**
  `_max_loss_for_strategy` returns width-minus-credit; discriminating
  regression verified red-on-revert (correct test cited after the connector
  correction: `test_phase5.py:388-400`). Fixing CB-13 does NOT close
  still-open CB-08 — spread economics remain a 30%-of-width estimate,
  tracked above.
- **CB-14 — fabricated `pct_change = 0.0` (was High): FIXED / COMPLETE.**
  Now raises (PRD-262); two discriminating tests, one parametrised over the
  invalid values.
- **CB-15 — regime confidence inflation on dropout (was High): FIXED /
  COMPLETE.** Worst-case bounding over the fixed 8-vote denominator
  (PRD-263), named quorum-floor test plus exhaustive proof; disclosed limit:
  the 247-day replay contained zero partial-vote days, so synthetic tests
  remain the only dropout evidence.

**Retired / superseded:**

- D-RULE as a pending item (ruling merged via #167).
- Workplan L0's new-PRD allocation freeze only (its named conditions
  resolved; PRD-278's allocation on #185 is legitimate). L0 itself remains
  IN PROGRESS — see §3.
- Phantom-SHA debt class (WONTFIX-HISTORICAL, PRD-243).
- Continuation budget decouple (fixed by PRD-256 R3).
- stage0-04's original "NO VIABLE PROVIDER" GEX verdict (re-dispositioned in
  place: NOT ATTEMPTED, external reach disabled).
- The ledger draft's "historically PR #184/#185" framing — both PRs are live.

## 6. NOW / NEXT / LATER portfolio

**NOW (exactly one):**

- **NS-0B — North Star ratification** (this ledger + this program, PR #187):
  `NOW — COMPLETE UPON DUSTIN'S MERGE OF PR #187`. Dustin's merge is the
  ratifying and completing act; no post-merge transition commit is required
  (the GOV-0 merge-contingent convention). On merge, the NOW slot becomes
  intentionally vacant — no packet is promoted — until Dustin's A/B runway
  ruling. NS-0's truth-reset and debt-classification outcomes are already
  delivered (PR #175, the fidelity delta, this program).

**The immediate runway choice is Dustin's, and it is not made here:**

- **Option A — resume and finish CB-02** (NS-1E; PRs #184/#185), completing
  its GOV-2 §12 sequence, then begin fixed SPY observation.
- **Option B — leave CB-02 parked** and promote fixed SPY observation
  directly, after resolving its exact prerequisite (the PRD-271 Gate A ORB
  ruling). Option B also requires the explicit CB-01 safety ruling — it
  cannot silently bypass CB-01 (§5).

Until that ruling, CB-02 / NS-1E is `PARKED / DUSTIN DECISION REQUIRED` and
no implementation packet is on the runway.

**NEXT (approved follow-ons, not active; each needs its own GOV-2 intake,
packet where MATERIAL, PRD, review, and Gate A):**

1. **NS-2A/2B/2C — fixed SPY observation with session-correct ORB and session
   VWAP, with visible freshness.** The proposed first trader-facing product
   slice. Entry conditions: Dustin's A/B runway ruling above, **and** the
   PRD-271 Gate A design ruling (the ORB remedy — timestamp-based session
   selection vs widened window vs fail-loud — is a design choice the
   observation artifact and the execution gate must share; two independent ORB
   truths would be drift by construction). This slice is MATERIAL under GOV-2
   §1 (new persisted schema with multiple readers, crosses runtime +
   persistence + dashboard), so it begins with an upstream packet seeded by
   stage0-01, not with code.
2. **NS-2E — Market Control Card** (after NS-2A/B/C exist to feed it).

**LATER (preserved, not authorized):** NS-4A/4B (universe registry and basic
movement heatmap — the first named promotion candidates after NS-2E; registry
content is Dustin-authored, seed tuples exist, and promotion is Dustin's),
NS-2D, NS-2F, NS-3 (all packets), NS-4C/D/E, NS-5 (GEX-0→3; GEX-0→2 lifecycle
`EVIDENCE BLOCKED` per the workplan), NS-6 (NEWS-0→4; NEWS-0→3 lifecycle
`EVIDENCE BLOCKED` per the workplan), NS-7, NS-8, NS-9, ODATA-0/1+, PRES-0.
Portfolio rank and lifecycle condition are separate axes (ledger §3). Full
preservation in §12.

## 7. The runway candidate held for Dustin's ruling: NS-1E / CB-02

CB-02 is `PARKED / DUSTIN DECISION REQUIRED`. It becomes the NOW packet only
if Dustin explicitly resumes it (Option A in §6); nothing in this section is
that ruling. The facts below record where the parked work stands.

**Trader question served:** Q3 (is anything tradable?) and Q4 — a setup whose
smallest expressible contract exceeds the adjusted risk budget must refuse,
visibly, rather than silently emit a budget-breaching position. Refusal becomes
first-class evidence, which is the ledger's own product doctrine.

**State:** upstream MATERIAL packet drafted and connector-reviewed (PR #184,
head `24660ac`, thirteen threads actioned); PRD-278 + draft Gate A entry on PR
#185 (head `ee2d12e`). Both DRAFT, both parked by GOV-2 §12.

**Design (from the packet; final only at Gate A):** refuse at
`options.py::build_option_setups`, preserve the list return API via an optional
refusal out-parameter, token `SMALLEST_CONTRACT_EXCEEDS_BUDGET`, stage
`OPTIONS_SIZING`; full-truth surface across contract, dedicated audit carrier,
text report, notification, HTML, premarket, postmarket, CLI, dashboard;
postmarket aggregates agree with the new breakdown member; false generic
"no setups" wording suppressed when refusal is the cause.

**Exact remaining sequence if resumed (GOV-2 §12; order binding):**

1. Independent exact-corrected-head confirmation of PR #184's final head
   (commissioned per GOV-2 §2/§7 — **not performed by this planning session**).
2. Dustin approves OPT-0's **carrier**, **reason semantics**, and
   **implementation seam** — OPT-0's governed exit per the workplan. OPT-1 /
   PRD-278 cannot advance before this approval.
3. PR #185 carries the final canonical nine-file ruling consistently,
   including its `docs/DECISIONS.md` entry.
4. Fresh-context independent review of PRD-278 (reviewer is not the author or
   same-session implementer; verdict committed against the exact revision).
5. Dustin issues Gate A on the reviewed PRD — the first binding ceiling.
6. Implementation under the Gate A ceiling; implementation review; Dustin
   merges. Closeout rides the implementation PR (PRD-229).

Preparatory CB-02 review may continue, but CB-02 implementation and final
Gate A authorization cannot begin until Dustin dispositions PRD-268 and
closes the applicable L0 sequencing gate.

**Blockers, precisely:** steps 1–5 above, plus PRD-268's disposition and
closure of the applicable L0 sequencing gate — actual sequencing blockers to
final Gate A authorization and CB-02 implementation (preparatory review may
continue, as stated above). All are Dustin-held decisions or
Dustin-commissioned events. **Stale/apparent blockers, verified not blocking:**
the Finding D ruling (merged, #167); the workplan's L0 allocation freeze (its
conditions resolved — L0 itself remains IN PROGRESS, §3); PRD-274/275 (infra
debt); CB-01 (independent finding, not on this seam — though its own
Dustin-held safety ruling still gates implementation start; §5).

**Considerations for the A/B ruling (neither chosen here).** For Option A:
CB-02 is the furthest along under the ratified process (upstream packet
drafted and connector-hardened), it closes a Critical truth defect on the
sizing seam, its operator ruling is already canonical, and its ceiling is
bounded (nine production files, ~220 net LOC, two additive schema changes —
`ESTIMATED SURFACE — NOT YET APPROVED` until Gate A). For Option B: fixed SPY
observation is the faster trader-visible win, and CB-02's remaining steps are
all owner-held, so it parks without decaying. Either option's implementation
start additionally requires the CB-01 safety ruling (§5). Either way the
one-packet rule holds: whichever option Dustin rules, only that packet's
MATERIAL sequence is in flight.

## 8. Proposed acceptance contract for CB-02 (applies only if Dustin resumes it)

Proposed, for Gate A to fix; the checker returns exact SHA, per-requirement
PASS/FAIL, one blocking explanation per failure, ACCEPT or REJECT — and may not
add adjacent requirements at closeout.

1. When the smallest expressible contract's strategy max loss exceeds the
   applicable adjusted risk ceiling, no actionable setup or decision survives,
   on direct and continuation paths, debit and credit, correlation-adjusted
   included.
2. The refusal carries exact token `SMALLEST_CONTRACT_EXCEEDS_BUDGET` and
   stage `OPTIONS_SIZING`, stable at every consumer named in the packet
   (contract, audit carrier, text report, notification, HTML, premarket,
   postmarket, CLI, dashboard).
3. Postmarket aggregate counts agree with the new `rejection_breakdown`
   member; generic "no setups" / "no qualifying setups" wording is suppressed
   when sizing refusal is the actual cause.
4. Positive-sizing behavior and its dollar-risk arithmetic are unchanged
   (value-for-value); a mutation restoring the floor-one budget breach turns
   at least one test red (PRD-198 invariant 4).
5. No fractional contracts, no rounding up, no silent candidate drop, no
   budget change, no strategy-selection change, no live-chain work.
6. FILES stays within the Gate A ceiling; any increase is a stop-and-renew
   event (GOV-2 §5).

## 9. Explicit non-goals

- No prediction logic, ML, sentiment, or synthetic confidence (VISION non-goals;
  doctrine G1).
- No execution automation or broker integration.
- No backtest-optimization machinery (deflated Sharpe / PBO / walk-forward
  explicitly ruled out by the reconciliation).
- No GEX or news implementation of any kind before their doctrine gates pass;
  GEX stays air-gapped context-only (G2).
- No threshold tuning motivated by observed outcomes during any baseline
  window (NS-1D discipline).
- No proactive governance redesign, doctrine sweeps, or review archaeology for
  at least the next three product slices; no recursive review of this review.
- No new PRD numbers, statuses, or registry/index edits from this program.

## 10. Stop conditions

- **Boundary reset (GOV-2 §6):** a review that reveals a previously omitted
  consumer class returns the in-flight packet to DESIGN INCOMPLETE; stop
  incremental patching; Dustin chooses rebuild / narrow / park.
- **Materiality re-run (GOV-2 §1):** any material scope, schema, ceiling, or
  seam expansion mid-slice stops implementation until the packet sequence is
  re-cleared.
- **FILES breach:** a needed file outside the Gate A ceiling stops work before
  the edit (CLAUDE.md scope locking; GOV-2 §5 stop-and-renew).
- **Adjacent discovery:** new findings go to the §5 debt ledger, not the
  runway — unless they create false evidence, data corruption, unsafe
  execution, or irreversible repository damage, in which case stop and
  surface to Dustin.
- **Governance displacement:** if a week produces governance output without
  trader-facing progress while the runway is unblocked, stop and re-read the
  ledger's weekly product ledger discipline.

## 11. Dustin decisions required before implementation

Held decisions, stated once, none inferred or pre-empted:

1. **Ratify** the North Star ledger and this program (NS-0B); merge this
   branch when satisfied. **Done** — this item described the pre-merge
   state; Dustin has since ratified both documents via merge of PR #187
   (`fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`).
2. **The A/B runway ruling:** either **resume CB-02** (then: direct the GOV-2
   exact-head confirmation on PR #184; accept the #185 consistency
   correction; dispatch the fresh-context independent PRD-278 review; rule
   **Gate A** on PRD-278) — or **leave CB-02 parked** and promote fixed SPY
   observation directly, which requires the explicit CB-01 ruling below.
   Neither option is pre-selected by this program.
3. **PRD-271 Gate A** — choose the ORB remedy (prerequisite for the NS-2
   slice under either option; also resolves CB-07).
4. **PRD-268 disposition** — approve / return to PROPOSED / deprecate
   (closes workplan L0's last open step).
5. **MACRO-0** — KEEP DORMANT / PROMOTE after cadence split / RETIRE
   PRD-187/188.
6. **D2 (Strategy repo)** — dated correction of the AS-IS baseline records;
   decide whether a tier-complete frozen re-run is ever worth a session.
7. **CB-01 safety ruling** — required before any implementation packet begins
   under either runway option: promote CB-01 ahead of product expansion, or
   defer it explicitly with acknowledged risk (reconciliation's recommended
   order puts it directly after CB-02).
8. **Confirm the NEXT slice** — NS-2A/B/C fixed SPY observation as the first
   trader-facing product win, sequenced by the A/B ruling and entering
   through its own MATERIAL packet.
9. Non-blocking, whenever convenient: PRD-274 scheduling; PRD-275 constraint
   resolution; DOC-0 header pass; CB-10 doc correction; CB-30…47 triage-sweep
   commissioning.

## 12. "Not lost" appendix — every preserved future plan

Nothing below is authorized; everything below is deliberately preserved.

- **NS-2D** meaningful intraday event preservation; **NS-2F** ranked control
  ladder (support/pivot/resistance/structural failure, evidence-linked,
  non-predictive).
- **NS-3 Opportunity Set Engine** — taxonomy (Grade A / Near Qualification /
  Developing / Watch / Invalidated / Macro Conflict / Stay Flat); funnel
  visibility (Universe → Macro → Trend → Risk → Qualified → Grade A);
  evidence-based negative market statements ("no quality longs today");
  maturity/deterioration views; confidence decomposition. Depends on the
  parked near-miss-surface introspection.
- **NS-4** universe registry (symbols, aliases, themes, roles, horizons,
  benchmarks, questions; suggested groups Context / Energy / AI-Semis /
  Tradeable / Spec-Learning / Holdings); movement heatmap with visible
  freshness; leadership mode vs assigned benchmark; participation/breadth
  mode; external watchlist mirror. *Observe wide, trade narrow.*
- **NS-5 GEX** — GEX-0 bounded one-provider evidence pass (network charge,
  minimum honesty contract per doctrine §4.3); GEX-1 manual cached producer
  (flip, put wall, call wall, versioned, source/model/timestamps embedded);
  GEX-2 display-only consumer, baseline-identical when absent; GEX-3 cadence
  only after usefulness. *GEX is context, not a magic signal.*
- **NS-6 relationship-aware news** — NEWS-0 static Dustin-ratified registry;
  NEWS-1 manual producer (2–3 items, never over 5, deterministic, no
  sentiment); NEWS-2 KEEP/REVISE/RETIRE usefulness ruling; NEWS-3 display
  consumer; NEWS-4 cadence last. Relationship path GLOBAL STATE → THEME
  HEALTH → THEME LEADERS → WATCHLIST → SETUPS → TRADES.
- **NS-7 idiosyncratic decoupling** — contract (window, benchmark, threshold,
  freshness), heatmap label, news link without invented cause (AVGO/SOXX,
  OXY/energy, NVDA/QQQ examples).
- **NS-8 prospective decision evaluation** — cohort capture incl. STAY_FLAT,
  decision linkage, counterfactual observation of rejected/abstained cases,
  usefulness measures (comprehension time, outside-screen dependence,
  override quality, abstention value), review cadence with no baseline
  tuning. Builds on stage0-02's schema evidence, CB-11's join key, and the
  CB-20…25 cluster.
- **NS-9 scheduling/freshness** — run identity (nominal slot, trading date,
  idempotency key), execution observability, artifact freshness visible to
  every consumer, cadence promotion only after usefulness. Anchored by
  stage0-03, CB-18, CB-06. *The clock declares when. The pipeline decides how.*
- **NS-1D** prospective baseline freeze (observe outcomes without tuning).
- **ODATA-0/1+** — options-data backlog re-recon after CB-02; deterministic
  calendar expiry, absolute strikes, both-leg quotes, net debit/credit and
  live max loss, degraded-data behavior, display consumption — each a
  separate future unit, provider-dependent ones behind data-contract evidence.
- **PRES-0** — PRD-259 E/F consumer-contract pass; G as a small standalone
  correction after CB-02.
- **Parked with reopen conditions:** near-miss-surface; red-folder-entry-gate;
  section-registry-refactor; present-MANUAL_CHECK visibility; PRD-209.
- **Deliberately not built:** everything in the reconciliation's §11
  do-not-commission list (backtest machinery, CB-09 concurrency work, more
  deny-glob rounds, analytics over unsound evaluation output).

---

*Validation note: this program is documentation only. Green CI on its branch
proves the repository's existing checks still pass and that these documents
break no existing validation. CI does not semantically validate this portfolio
map — no CI check or test consumes these documents. The statuses here rest on
the session verification evidence cited in §2–§3 (GOV-2 §8). No new CI or
tests are added by this PR.*
