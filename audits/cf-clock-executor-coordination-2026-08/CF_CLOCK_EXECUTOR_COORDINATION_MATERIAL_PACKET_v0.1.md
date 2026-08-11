# CF Clock / GitHub Executor — First-Success Coordination — MATERIAL PACKET (v0.1)

STATUS: PROVISIONAL — DESIGN COMPLETE, PENDING INDEPENDENT CODEX PACKET REVIEW
(GOV-2 §2 step 3). This packet grants no downstream authority. No Stage-0 PRD,
Gate A, or implementation may begin until the review sequence in §17 is clean
and Dustin has issued the design-direction ruling (§16 records the standing
owner pre-authorizations that make that ruling automatic *iff* this design
stays inside their boundary; the pre-authorizations do not waive the
independent review gate).

Authoring session: `claude/cf-gh-executor-coordination-6ak3ka` (branch carries
packet drafting only; GOV-2 §4 — the branch's existence creates no
implementation authority).

Reviewed repository baseline: `main` @ `b1309861` (this branch's HEAD equals
`origin/main` at drafting; the packet describes proposed surface, it does not
implement it).

---

## 0. Where this packet sits in the GOV-2 order

```
materiality check at intake                         <- §15 (MATERIAL: crosses
                                                       runtime-exit / workflow /
                                                       notification / delivery;
                                                       adds a coordination seam)
-> provisional material packet                       <- THIS DOCUMENT (v0.1)
-> Codex packet review                               <- PENDING (§17; instrument
                                                       not present in the current
                                                       cloud session)
-> one consolidated correction                       <- pending
-> Codex confirmation of exact corrected head        <- pending
-> Dustin design-direction ruling                    <- automatic iff in-bounds
                                                       (§16 pre-authorizations)
-> PRD drafting (Stage-0)                             <- pending
-> independent PRD review                             <- pending
-> Dustin Gate A                                      <- automatic iff Stage-0
                                                       stays inside this packet
-> implementation                                     <- pending
-> required implementation review                     <- pending
-> Dustin merge                                       <- pending
```

CI-claim boundary (GOV-2 §8): CI on the branch carrying this packet confirms
only that the documentation branch preserves the current green baseline. It
does not execute or validate the proposed runtime design, the coordination
helper, the workflow integration, or the regression plan.

### 0.1 Scope split from the 2026-08-09 CF-D bundle (why this packet is narrower)

`docs/DECISIONS.md` (2026-08-09, "CF-D owner-ruling bundle") sequenced a
broader morning-brief slice whose MATERIAL packet was gated on CF-E1 + CF-E2
evidence and the CF-D1b displacement ruling. This packet is the deliberately
**narrower clock/executor-COORDINATION-only** slice authorized by the resume
charter. It carves CF-E2 and CF-D1b explicitly OUT OF SCOPE (§18) and does not
depend on them:

- CF-E2 / CF-D1b concern **what the published board displays** about premarket
  quote displacement (a rendering/banner question).
- This packet concerns **when and how an OPEN attempt is dispatched and
  deduplicated** (a transport/coordination question).

The coordination mechanism reads GitHub run-conclusion evidence only. It never
reads quote semantics, first-bar latency, or displacement. There is therefore
no evidence dependency on CF-E2/CF-D1b. If review finds a hidden dependency,
that is a §14 stop-and-amend event.

---

## 1. Product question and user-visible outcome

**Question.** For a single logical OPEN slot on a given PT trading date, run the
live morning observation **exactly once successfully**, using Cloudflare as the
preferred punctual clock and a delayed GitHub cron as a coordinated fallback —
without any repo-persisted coordination state, and without a second successful
OPEN board being published for the same slot.

**User-visible outcome (Dustin).** The morning board is published once per OPEN
slot, on time, whether Cloudflare fired the clock or the GitHub fallback did. A
duplicate clock tick, a late Cloudflare arrival, or a Cloudflare outage never
produces either a missing board or a redundant second execution. Nothing about
market truth, board freshness, or validity is asserted by this change beyond
what the existing artifacts already prove (§11 TRUTH).

---

## 2. Authority model (RATIFIED direction — §16)

| Component | Role | May do | May NOT do |
|---|---|---|---|
| Cloudflare Worker | Preferred authoritative **clock** | Authorize an attempt by POSTing `workflow_dispatch` to `main` with minimum `mode`/`slot`/`source` metadata; log accepted-vs-rejected dispatch | Observe, validate, render, publish, interpret `latest_run`, hold dedup state, or assert success |
| GitHub Actions pipeline | **Executor / observation / validation / rendering / publication / observation truth** | Everything downstream of dispatch; own the run conclusion; own the first-success proof; own publication | — |

Cloudflare dispatch accepted ≠ observation succeeded ≠ publish succeeded ≠
dashboard current. Dispatch is an *attempt authorization*, nothing more. This
inequality is the load-bearing premise of the whole design and is preserved
end-to-end.

---

## 3. Post-PRD-298 assumption revalidation (Phase 1 — RED clearance)

PRD-298 (COMPLETE @ #245) is the stated prerequisite. Each Phase-1 assumption
is verified against the merged code and workflow. **All GREEN; no RED.**

| # | Assumption | Verdict | Evidence |
|---|---|---|---|
| 1 | `conclusion=success` now covers TRADE, NO_TRADE, and valid MARKET_STRESS HALT | GREEN | PRD-298 R1: `execution_success = verification.pass AND (status==SUCCESS OR (system_halted AND halt_cause==MARKET_STRESS AND not errors))`; `cuttingboard/runtime/__init__.py` cli_main drives exit code from this signal; valid halt → exit 0 |
| 2 | Genuine crash / VALIDATION failure / publish failure remain `conclusion=failure` | GREEN | PRD-298 R1/R5/I3: VALIDATION halt, crash, `errors!=[]` → exit 1, no publish. Publish steps are `if: success() && PUBLISH_READY=='true'` with `set -euo pipefail`; a failed `check_readiness`/`git push` aborts the step → job failure (`cuttingboard.yml` "Commit artifacts" :387–417, "Push" :438) |
| 3 | Publish occurs **before** workflow success is finalized | GREEN | The render → `check_readiness --profile morning` → commit → push sequence runs as job steps; the job cannot conclude `success` until they complete. A run that concludes success on the OPEN slot has necessarily published (PRD-298 DATA FLOW; `cuttingboard.yml` :386–442). "Run success" therefore implies "board published" — the exact property coordination consumes |
| 4 | GitHub run metadata identifies workflow identity, event type, run conclusion, ref/head branch, and logical slot identity | GREEN (slot identity requires §5 carrier, unbuilt but mechanically addable inside the transport boundary) | Actions API run objects expose `path`/`workflow_id`, `event`, `status`+`conclusion`, `head_branch`, and `name`/`display_title`. Slot identity is carried in `display_title` per §5 |
| 5 | Delayed fallback can query prior qualifying runs deterministically | GREEN | `GET /repos/{repo}/actions/workflows/cuttingboard.yml/runs?branch=main&status=completed&created=>=<utc-today>`; identical transport already in production (`scripts/check_run_revision.py` :84–116) |
| 6 | rerun / `run_attempt` cannot let a stale SUCCESS satisfy a new logical slot | GREEN (with §5.3 bucketing rule) | Date bucketing uses the run's **original creation** timestamp, not the latest attempt's `run_started_at`; a re-run keeps its original date bucket. Manual reruns are additionally excluded from automatic coordination (§6). See §5.3 for the exact field-selection rule and its author-verification obligation |
| 7 | Old successful OPEN from a previous PT date cannot be mistaken for today's | GREEN | Same mechanism: `PT-date(created_at) == today_PT` is part of the match predicate (§5.3); plus `created=>=<utc-today>` server-side bound |
| 8 | Malformed Actions API records fail safely | GREEN | `check_run_revision._collect_runs` already models this: typed `ProofError` on any non-object / wrong-typed field. The coordination helper mirrors it, but its safe direction is **AVAILABILITY** (execute), not deny — see §7.3 |

No Phase-1 assumption is false. No condition requires changing domain truth,
`latest_run` semantics, contract schema, hourly semantics, or the workflow's
existing rc==0 publish gate.

---

## 4. Current state verified at `main` (what exists / what is unbuilt)

Verified surface (recon re-run at drafting):

- `.github/workflows/cuttingboard.yml`: `schedule` crons `50 12 * * 1-5`
  (prefetch 05:50 PT), `0 13 * * 1-5` (live 06:00 PT), `30 23 * * 0` (Sunday);
  `workflow_dispatch` input **`mode`** only (`live|sunday|verify|prefetch`);
  `concurrency: cuttingboard-pipeline, cancel-in-progress: false`;
  `permissions: contents: write, actions: read`. **No `run-name`, no
  `display_title`, no PRE/OPEN inputs.**
- `scripts/resolve_run_mode.py`: pure cron-string → mode lookup; dispatch
  returns the raw `mode` input. **No PRE/OPEN slot vocabulary.**
- `scripts/check_run_revision.py` (PRD-297): the reuse template — stdlib
  `urllib`, `github.token`, `actions/workflows/{file}/runs`, typed fail-closed
  states, malformed-record guards, deterministic selection.
- `logs/latest_run.json`: observation state, monotonic-guarded writer
  (`safe_write_latest`, keyed on `run_at_utc`). **Unchanged by this packet.**

Unbuilt coordination surface (this packet's proposed work): slot inputs, the
`display_title` slot carrier, the OPEN first-success helper, the pre-execution
suppression step, the delayed OPEN cron, and the undeployed Worker.

---

## 5. Slot identity (Phase 2 — frozen, GitHub-native, no persisted state)

### 5.1 Carrier

The logical slot is encoded in the run's **`display_title`** (surfaced via
`run-name:` at workflow top level), from validated invocation inputs. A single
machine-queryable token:

```
CB-SLOT:OPEN     (live morning observation slot)
CB-SLOT:PRE      (prefetch warm-up slot)
```

`run-name` is evaluated at run start and may reference `inputs.*` and
`github.event.*`. For `workflow_dispatch`, the token derives from the validated
`slot` input. For the `schedule` OPEN fallback cron, the token derives from a
cron-string → slot map (`github.event.schedule`). The exact `run-name`
expression is an implementation detail reviewable at the PRD/implementation
stage; the DESIGN commitment is: **every automatic PRE/OPEN run carries exactly
one `CB-SLOT:` token in `display_title`, and no other run does.**

### 5.2 Match predicate for "a satisfied OPEN slot"

A completed run **SATISFIES today's OPEN slot** iff ALL hold (every clause a
GitHub-native fact; `source` is never read here):

1. workflow path == `.github/workflows/cuttingboard.yml`;
2. `event` ∈ {`workflow_dispatch`, `schedule`};
3. `head_branch` == `main`;
4. `display_title` contains `CB-SLOT:OPEN`;
5. `PT-date(created_at)` == the target PT date (today, at query time);
6. `status` == `completed`;
7. `conclusion` == `success`.

PRE and OPEN cannot collide (distinct tokens, clause 4). Historical/previous-day
runs cannot qualify (clause 5). Manual ordinary dispatches (`mode`-only, no
`CB-SLOT:OPEN`) cannot qualify (clause 4). Wrong-ref runs cannot qualify
(clause 3). A PRE run cannot satisfy OPEN (clause 4).

### 5.3 Date-boundary rule (the rerun / stale-success guard)

The PT date is derived **at query time** from each candidate run's **original
creation instant**, converted to `America/Los_Angeles`. This is what makes
clauses 5–7 immune to reruns:

- A re-run of a previous-day run keeps its original creation instant → stays in
  its original PT-date bucket → cannot satisfy today's slot (Phase-1 #6/#7).
- The OPEN window (~06:30 PT ≈ 13:30 UTC) sits far from the UTC midnight
  boundary, so a `created=>=<utc-today-00:00Z>` server-side filter safely
  captures every candidate for today's PT OPEN slot without a same-day
  UTC/PT split.

**Author-verification obligation (carried into implementation review):** confirm
the exact Actions-API field whose value is immutable across re-runs and use it
for bucketing. `created_at` is the run-record creation time and is the intended
field; `run_started_at` reflects the latest attempt and MUST NOT be used for
date bucketing. If review determines `created_at` is not attempt-stable in
practice, the mechanical correction inside the transport boundary is to read
the first attempt's start via the run-attempts endpoint, or (for the
`workflow_dispatch` path only) to additionally stamp the PT date into
`display_title` at dispatch. Either correction stays inside §5's carrier and
introduces no persisted state. This is flagged, not deferred.

### 5.4 No `invocation_id`

No `invocation_id` or synthetic correlation id is introduced. The slot token +
PT-date bucket + GitHub-native run fields are sufficient evidence. (If review
falsifies this — §14 stop-and-amend — the smallest alternative is stamping the
PT date into `display_title` on the dispatch path, still no persisted state.)

---

## 6. Coordination mechanism (Phase 3 — typed helper, fail-toward-availability)

New helper `scripts/check_open_slot_satisfied.py`, a close sibling of
`check_run_revision.py`, reusing its transport, headers, pagination bound, and
malformed-record guards. It answers exactly one question: **"Has today's logical
automatic OPEN slot already been satisfied by a prior qualifying run?"**

### 6.1 Typed result vocabulary

```
SATISFIED      — a prior run meets the §5.2 predicate for today's OPEN slot.
UNSATISFIED    — the query succeeded and NO prior run meets the predicate.
PROOF_ERROR    — the query could not deterministically prove satisfaction
                 (network error, HTTP error, malformed record, missing token,
                 missing repo/token env). UNKNOWN collapses into PROOF_ERROR.
```

The current run itself is excluded from the scan (a run cannot satisfy its own
slot) — matched by run id, available to the step via `github.run_id`.

### 6.2 Fail direction (the crux, and its contrast with `check_run_revision`)

| Helper | Gates | Safe direction on uncertainty | Rationale |
|---|---|---|---|
| `check_run_revision` (PRD-297) | ATTEMPT AUTHORIZATION | fail **CLOSED** (deny) | An unproven authorization must not authorize |
| `check_open_slot_satisfied` (this packet) | SUPPRESSION of the only fallback | fail **toward AVAILABILITY** (execute) | An unproven suppression must not suppress the only fallback |

Both obey PRD-198 #1 (fail-loud, never silent-fallback) and #3 (authoritative
source, not proxy). The safe direction differs because the consequence of being
wrong differs: for an authorization gate, the danger is a false GO; for a
dedup-suppressor, the danger is a false STOP that drops the only remaining
fallback and produces a **missing** board. Therefore:

- `SATISFIED` → the automatic OPEN fallback **no-ops successfully** before any
  market execution.
- `UNSATISFIED` → **execute**.
- `PROOF_ERROR` → **execute**, and log the proof failure explicitly with the
  typed evidence. The helper NEVER prints or implies `UNSATISFIED` as a fact
  when it could not prove satisfaction; `PROOF_ERROR` is a distinct state and
  is logged as such. The only fallback is never silently suppressed on
  uncertain evidence.

### 6.3 Output contract

Stdout key/value lines mirroring `check_run_revision` (`CB_OPEN_SLOT_STATE=...`,
`CB_OPEN_SLOT_EVIDENCE=...`), and a process exit code the workflow step maps to
execute-vs-no-op. `SATISFIED` and `PROOF_ERROR`/`UNSATISFIED` are distinguished
by the printed state, never by exit code alone, so the degraded path is legible
in the run log.

---

## 7. Workflow integration (Phase 4)

Additions to `.github/workflows/cuttingboard.yml` (M), minimal:

### 7.1 Inputs

Add `workflow_dispatch` inputs alongside the existing `mode`:

- `slot` (choice: `OPEN`, `PRE`; the CF Worker sets it);
- `source` (string; provenance only — see §10 SECURITY).

`mode` is **reused**, not replaced. The Worker passes `mode` + `slot` + `source`.

### 7.2 Slot/mode consistency (fail closed)

`slot`↔`mode` consistency is validated (extending `scripts/resolve_run_mode.py`
or a dedicated validation step): `OPEN` requires `mode==live`; `PRE` requires
`mode==prefetch`. A mismatch **fails closed** (non-zero, no execution) — a
malformed dispatch never runs the wrong slot. No new refresh mode is introduced;
`OPEN→live`, `PRE→prefetch` reuse existing modes.

### 7.3 `run-name` / slot carrier

Add a dynamic `run-name:` emitting the `CB-SLOT:<slot>` token per §5.1.

### 7.4 Pre-execution first-success query (OPEN only)

Before the live execute step, on an **automatic OPEN** invocation, run
`check_open_slot_satisfied.py` using the ambient `github.token` (the workflow
already holds `actions: read` — **no new credential**):

- `SATISFIED` → no-op successfully **before** market execution (skip the live
  pipeline; the run concludes success as a legitimate coordinated no-op).
- `UNSATISFIED` → execute.
- `PROOF_ERROR` → execute, with the degraded-coordination evidence logged.

Concurrency (`cuttingboard-pipeline`, `cancel-in-progress: false`) serializes an
overlapping CF-OPEN and GH-fallback so the later one re-checks *after* the prior
completes — serialization orders them; the first-success query dedupes them
(concurrency alone does not dedupe — preserved recon).

### 7.5 Delayed OPEN fallback cron

Add a `schedule` cron for the GH OPEN fallback, delayed ~5 minutes from the
preferred CF OPEN trigger (supported by observed run-time evidence; §14 lists
the falsifier). It carries `CB-SLOT:OPEN` via the cron→slot map and runs the
same §7.4 first-success query, so it participates in the identical symmetric
rule.

### 7.6 Manual dispatch / PRE

- **Manual dispatch** does not participate in automatic OPEN suppression by
  default: an ordinary operator run uses `mode` without `slot=OPEN`, so it does
  not carry `CB-SLOT:OPEN` and is neither a suppressor nor suppressed. Because
  the predicate never reads `source`, a manual run cannot impersonate Cloudflare
  authority via `source` text — there is nothing to impersonate (§10).
- **PRE** gets a slot token and slot/mode fail-closed validation for identity
  and safety, but **no first-success suppression** — this slice stays focused on
  OPEN (per charter). PRE requires no shared idempotency semantics (§14 lists
  the falsifier that would return this to Dustin).

---

## 8. Coordinated fallback behavior (symmetric first-success — specification)

For a logical OPEN slot/date, the FIRST completed successful qualifying
automatic OPEN execution satisfies the slot. A successful qualifying OPEN
includes TRADE, NO_TRADE, and a valid market-stress HALT (PRD-298). A failed
run does not satisfy.

| Scenario | Result |
|---|---|
| CF OPEN succeeds → later GH OPEN fallback | fallback query `SATISFIED` → no-op |
| CF OPEN valid HALT succeeds → later GH fallback | HALT is success (PRD-298) → `SATISFIED` → no-op |
| CF OPEN fails | no successful OPEN today → fallback `UNSATISFIED` → executes |
| CF dispatch accepted, GitHub execution later fails | no successful OPEN → fallback executes |
| CF never fires | no OPEN run → fallback executes |
| Duplicate CF dispatch | first successful qualifying OPEN wins; later duplicate → `SATISFIED` → no-op |
| GH fallback succeeds first → later CF OPEN | later CF run's own pre-check `SATISFIED` → no-op |
| Prior OPEN still running when fallback arrives | concurrency serializes; fallback re-checks after prior completes; prior success → no-op; prior failure → execute |
| Malformed Actions API record | `PROOF_ERROR` → execute + logged degraded evidence |
| Actions API outage | `PROOF_ERROR` → execute |
| Old successful run from previous PT date | excluded by §5.3 date bucket |
| PRE run | not `CB-SLOT:OPEN` → ignored for OPEN |
| Manual run | not `CB-SLOT:OPEN` → ignored for automatic coordination |
| Wrong ref | `head_branch != main` → ignored |
| Wrong slot/mode | fail-closed at §7.2, no execution |
| Publish failure on an otherwise-live run | job `conclusion=failure` → non-satisfying (§11 TRUTH) |

Every CF and GH-fallback OPEN run runs its own pre-check, so the rule is
symmetric regardless of which clock arrives first.

---

## 9. Worker (Phase 5 — minimum, in-repo, UNDEPLOYED)

An in-repo, undeployed Cloudflare Worker under `workers/cuttingboard-clock/`.
Responsibilities strictly limited to:

- on a scheduled event, resolve PRE vs OPEN;
- `POST .../actions/workflows/cuttingboard.yml/dispatches` with `ref=main` and
  minimum `{mode, slot, source}`;
- log accepted-vs-rejected dispatch (HTTP status);
- never claim observation/publish success.

Explicitly NOT in the Worker: market logic, board-freshness logic, `latest_run`
interpretation, any dedup database, Cloudflare KV / Durable Objects. The
credential is a fine-grained GitHub token, **Actions: write only**, stored as a
Worker secret — never written to the repo. Actual Worker deployment and the
real PAT provisioning are an owner-held external seam (§14 item 10), out of this
implementation's reach; the repo carries only the undeployed source +
configuration example + a README documenting the deploy/secret steps Dustin
performs out-of-band.

Note for review: the Worker introduces a JS/TS surface into a Python repo. This
is called out as a review/consideration point (tooling, test strategy for an
undeployed Worker), not hidden.

---

## 10. STATE, TRUTH, SECURITY

**STATE (no new persisted coordination state).** No attempt registry, no
dispatch-state file, no idempotency store, no KV/DO. `logs/latest_run.json`
semantics are unchanged (still observation state, monotonic-guarded). All
coordination evidence is read live from the GitHub Actions API at query time.

**TRUTH.** Run success is execution-control evidence only. It means the executor
completed and (for a live OPEN) published, per existing artifact truth. It does
NOT promote dashboard freshness or market validity beyond what the published
artifacts already assert. Coordination reads run conclusion; it never reads or
asserts market/quote/displacement facts.

**SECURITY / AUTHORITY.** The Worker credential is Actions-write only
(dispatch). The in-workflow coordination query uses the ambient `github.token`
with the pre-existing `actions: read` permission — no scope widening. `source`
is descriptive provenance, never an authentication or security fact, and is
**never read by the §5.2 predicate**. Because the predicate is source-blind,
spoofing `source` (e.g. a manual dispatch claiming `source=cloudflare`) changes
nothing: satisfaction depends only on slot token + branch + event + PT-date +
completed + success. There is no authority semantics attached to `source`, so
none can be forged.

---

## 11. Falsification / discriminating test matrix (Phase 6)

Behavioral tests (fixture-injected API payloads; no live network). `M` = a
reddening mutation must be shown to flip the test. Target file
`tests/test_open_slot_coordination.py` (new).

| # | Scenario | Asserted behavior | Mutation (M) |
|---|---|---|---|
| T1 | CF OPEN success in payload | `SATISFIED` → no-op | drop success run → executes |
| T2 | CF OPEN valid market-stress HALT success | `SATISFIED` (HALT is success) | flip halt run conclusion→failure → executes |
| T3 | CF OPEN failure only | `UNSATISFIED` → executes | — |
| T4 | Dispatch-accepted but run conclusion=failure | `UNSATISFIED` → executes | mark run success → no-op (proves conclusion is read) |
| T5 | Empty run list (CF never fired) | `UNSATISFIED` → executes | — |
| T6 | Two successful OPEN runs (duplicate CF) | `SATISFIED`; helper stable/deterministic | — |
| T7 | GH-fallback success present, evaluated by a later CF run | `SATISFIED` → no-op | — |
| T8M | Malformed run record (non-object / wrong-typed field) | `PROOF_ERROR` → executes; never `UNSATISFIED` | make record well-formed-but-nonmatching → `UNSATISFIED` (proves PROOF_ERROR ≠ UNSATISFIED) |
| T9M | API HTTP/URL error | `PROOF_ERROR` → executes | — |
| T10 | Successful OPEN run with previous-PT-date `created_at` | excluded → `UNSATISFIED` | move date to today → `SATISFIED` (proves date bucketing) |
| T11 | `CB-SLOT:PRE` success run only | ignored for OPEN → `UNSATISFIED` | change token to OPEN → `SATISFIED` |
| T12 | Manual run (no `CB-SLOT:` token) success | ignored → `UNSATISFIED` | add OPEN token → `SATISFIED` |
| T13 | Run on non-main `head_branch` | ignored → `UNSATISFIED` | set branch=main → `SATISFIED` |
| T14 | Wrong slot/mode dispatch (`OPEN`+`prefetch`) | resolver fails closed (non-zero, no execute) | align mode→live → resolves/executes |
| T15M | Re-run: previous-day run re-run today (original `created_at` yesterday) | still excluded (bucketed by original creation) | bucket by `run_started_at` instead → wrongly `SATISFIED` (proves the §5.3 field choice) |
| T16 | `source=cloudflare` on a manual run without OPEN token | ignored (source-blind predicate) → `UNSATISFIED` | — (documents spoof-inertness) |
| T17 | Valid HALT board still satisfying post-298 | `SATISFIED` for a valid market-stress HALT OPEN | — |
| T18 | Publish-failure run (live, `conclusion=failure`) | non-satisfying → `UNSATISFIED` | — |
| T19 | Current run excluded from its own scan | current `run_id` never self-satisfies | remove exclusion → false self-satisfy |

Verification runway (at implementation): focused tests green locally, then the
full suite reproduced on CI (PRD-198 #5, environment parity);
`python tools/validate_prd_registry.py --skip-commit-resolvability` exit 0.

---

## 12. Exact likely files (ESTIMATED SURFACE — NOT YET APPROVED)

Binding only at Gate A on the reviewed Stage-0 PRD (GOV-2 §5). Estimate:

- `A scripts/check_open_slot_satisfied.py` — the typed first-success helper
- `A tests/test_open_slot_coordination.py` — the §11 matrix
- `M .github/workflows/cuttingboard.yml` — slot/source inputs, `run-name`
  carrier, OPEN pre-execution query step, delayed OPEN cron
- `M scripts/resolve_run_mode.py` — slot↔mode consistency / cron→slot map
- `M tests/test_resolve_run_mode.py` — slot/mode fail-closed cases (if the file
  exists; else folded into the coordination test — confirmed at Stage-0 via the
  PRD-158 grep sweep)
- `A workers/cuttingboard-clock/` — undeployed Worker source, config example,
  README (no secret values)

PRD-158 pre-implementation grep sweep is REQUIRED at Stage-0 for any rendered
token/contract key touched (none expected — coordination adds no contract
field), and to enumerate every `resolve_run_mode` test asserting the current
dispatch behavior.

---

## 13. Estimated production LOC ceiling (ESTIMATED SURFACE — NOT YET APPROVED)

≤ ~220 net non-test production LOC (helper ~110, workflow YAML additions ~40,
resolver additions ~20, Worker ~50), red tests excluded. Provisional estimate,
not a constraint; the binding ceiling is Gate A on the reviewed PRD.

---

## 14. Stop-and-amend conditions (hard stops — return to Dustin; re-run GOV-2 §1)

Return RED / stop if any becomes true (these mirror the charter's RETURN list):

1. GitHub-native run evidence cannot safely prove OPEN-slot satisfaction
   post-298 (any Phase-1 assumption falsified and not mechanically correctable
   inside the transport boundary).
2. Slot identity requires persisted state or a broader schema (i.e. §5's
   `display_title` carrier + `created_at` bucket proves insufficient).
3. Coordination would require suppressing the fallback on uncertain evidence
   (i.e. `PROOF_ERROR` cannot safely map to execute).
4. Credential scope must widen beyond Actions-write.
5. Manual/auth provenance creates unresolved authority semantics (i.e. `source`
   cannot remain source-blind in the predicate).
6. PRE unexpectedly requires shared idempotency semantics.
7. Fallback timing requires a genuine owner product tradeoff (the ~5-minute
   delay is falsified by new run-time evidence).
8. `latest_run` or observation semantics must change.
9. CF-D1b / CF-E2 becomes coupled to coordination.
10. Actual external Worker/PAT deployment is the remaining seam (owner-held).
11. Final implementation is merge-ready (return to hand off).

The §5.3 `created_at`-vs-`run_started_at` verification is a bounded correction
inside the transport boundary (not a stop) unless it proves `created_at` is not
attempt-stable AND no in-boundary correction exists — then it escalates to
item 2.

---

## 15. Materiality / lane classification (GOV-2 §1)

**MATERIAL.** Matches: selects an implementation seam touching runtime-exit
consumption + workflow + notification-adjacent control; crosses two or more of
runtime, delivery, and workflow/coordination; establishes a production
FILES/LOC ceiling. Therefore ineligible for `LANE: MICRO`.

**Lane: STANDARD at minimum.** HIGH-RISK only if PRD-121 R11's own triggers fire
independently at Stage-0 (the workflow touches the live publish path and
execution-control semantics, which the drafter should weigh — a HIGH-RISK
classification would be defensible and is left to the Stage-0 PRD + independent
review, not asserted here). MATERIAL classification itself adds no
Codex-commissioned events beyond GOV-2 §7's two (packet review; exact-head
confirmation).

---

## 16. Owner rulings recorded (standing pre-authorizations from the resume charter)

The design-direction ruling is **automatically effective** iff this design stays
inside ALL of the following (verified true for v0.1):

- Cloudflare remains clock only — §2 ✓
- GitHub remains executor only — §2 ✓
- PRE→prefetch / OPEN→live — §7.2 ✓
- no persisted coordination state — §10 ✓
- GitHub-native first-success proof is sufficient — §5–§6 ✓
- credential remains Actions-write only — §9, §10 ✓
- manual `source` text is not treated as authentication — §10 ✓
- `latest_run` semantics unchanged — §10 ✓
- CF-D1b / CF-E2 remain excluded — §0.1, §18 ✓
- no new canonical multi-producer scheduling schema is introduced — §5.4, §10 ✓

Gate A is automatically effective iff the Stage-0 PRD stays inside this reviewed
packet.

**These pre-authorizations do not waive the independent review gate** (GOV-2 §2
step 3 / §7). The design-direction ruling being automatic removes Dustin's
manual ruling from the critical path; it does not remove the Codex packet
review, which is a capability/instrument gate, not an owner decision.

---

## 17. Packet review records (GOV-2 §2, §7) — PENDING (NOT satisfied)

This packet is PROVISIONAL. The two GOV-2 auto-commissioned Codex events have
NOT occurred. No verdict is fabricated. The required durable-record fields
(GOV-2 §2) are scaffolded here and MUST be filled by the actual independent
reviewer against the exact reviewed SHA before any downstream authority opens.

### INITIAL PACKET REVIEW — PENDING

| Field | Value |
|---|---|
| Event type | `INITIAL PACKET REVIEW` (GOV-2 §2 auto-commissioned) |
| Reviewer identity / capability role | PENDING (independent Codex, fresh context) |
| Reviewed commit SHA / revision | PENDING (this packet's committed SHA) |
| Review date | PENDING |
| Verdict | PENDING |
| Findings + dispositions | PENDING |
| Fresh-context / independence evidence | PENDING |

### EXACT-CORRECTED-HEAD CONFIRMATION — PENDING

| Field | Value |
|---|---|
| Event type | `EXACT-CORRECTED-HEAD CONFIRMATION` |
| Corrected SHA | PENDING |
| Prior finding ids + dispositions confirmed | PENDING |
| Reviewer / independence evidence | PENDING |

**Instrument note.** GOV-2 §2/§7 require an independent **Codex** review for
both events; `docs/DECISIONS.md` (2026-08-09) states CF execution "moves to the
Codex harness." The Codex instrument is not present in the current cloud
session, and GOV-2 §3 forbids a subagent spawned by the authoring session from
satisfying independent review. The packet therefore stops, correctly, at
PROVISIONAL — this is the standing blocker, held for Dustin to run/commission
the Codex packet review (or direct otherwise).

---

## 18. Out of scope (explicit)

- CF-D1b (premarket-displacement banner ruling)
- CF-E2 (premarket quote-semantics / first-bar-latency evidence capture)
- Notification-delivery-reliability follow-up (PRD-298 KNOWN LIMITATION;
  connector P1 #302)
- PRD-293 (dev-bootstrap; no coupling)
- Any general scheduler framework / canonical multi-producer scheduling schema
- Any change to `logs/latest_run.json`, the contract schema, the hourly path,
  or the domain-truth semantics settled by PRD-298
- CF-E2/CF-D1b coupling of any kind (a discovered coupling is a §14 stop)

---

END OF PACKET v0.1 — PROVISIONAL, PENDING INDEPENDENT CODEX PACKET REVIEW.
No downstream authority (Stage-0 PRD, Gate A, implementation) is granted by this
document.
