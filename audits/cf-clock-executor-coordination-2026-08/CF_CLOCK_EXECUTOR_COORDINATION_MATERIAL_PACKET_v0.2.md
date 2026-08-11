# CF Clock / GitHub Executor — First-Success Coordination — MATERIAL PACKET (v0.2)

STATUS: PROVISIONAL — DESIGN COMPLETE (author-hardened §19; corrected against a
non-gating independent evidence review §20), PENDING INDEPENDENT CODEX PACKET
REVIEW (GOV-2 §2 step 3). This packet grants no downstream authority.

CORRECTION CYCLE (v0.1 → v0.2): a fresh-context independent EVIDENCE review
(`PACKET.review.evidence.md`, NON-GATING per GOV-2 §3; reviewed v0.1 @
`982615442e7e3ebcfb60b440feb04436a010ae13`) returned REQUIRED CHANGES. Three
consolidated corrections (C1 UTC window basis; C2 dedicated OPEN concurrency
group + PRD-194 correction; C3 CF-D4 owner-ruling conflict) plus one recommended
(C4 rerun-conclusion test) are folded in and dispositioned in §20. One element —
the CF-D4 heartbeat-retention conflict — is HELD FOR DUSTIN'S EXPLICIT RULING
(§16), not auto-resolved. This EVIDENCE review does not consume GOV-1's single
correction cycle for the eventual Codex gate, which reviews this corrected head. No Stage-0 PRD,
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
-> provisional material packet                       <- THIS DOCUMENT (v0.2)
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

**Terminology (pin — prevents conflation).** In this packet **"OPEN" denotes the
live morning-observation slot** (`mode==live`, the job the existing `0 13 * * 1-5`
≈ 06:00 PT cron performs), per the charter's `OPEN→live` mapping. It is NOT the
CF-D3 market-open (09:30 ET / 06:30 PT) "OPEN / OPEN+1" bar-dispatch cadence —
that belongs to the out-of-scope displacement slice (§0.1, §18). Everywhere
below, OPEN = the live morning observation.

**User-visible outcome (Dustin).** The morning board is published once per OPEN
slot, on time, whether Cloudflare fired the clock or the GitHub fallback did.
Under **provable** coordination (the first-success query returns a definite
answer), a duplicate clock tick, a late Cloudflare arrival, or a Cloudflare
outage produces neither a missing board nor a redundant second execution. Under
**unprovable** coordination — when the Actions-API evidence is transiently
unavailable (`PROOF_ERROR`) — the design deliberately prefers a *possible*
duplicate execution over a *possible* missed board (availability over
suppression, §6.2): it will re-run rather than risk dropping the only fallback.
A duplicate OPEN run re-publishes the same-slot board from slightly later data
and may re-emit the single success/HALT notification; that cost is accepted as
strictly less harmful than a missing board (§10 TRUTH owns this explicitly).
Nothing about market truth, board freshness, or validity is asserted by this
change beyond what the existing artifacts already prove (§11 TRUTH).

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
| 3 | Publish occurs **before** workflow success is finalized | GREEN (bounded — see note) | For an EXECUTING live run the render → `check_readiness --profile morning` → commit → push sequence runs as job steps; the job cannot conclude `success` until they complete, so an executing OPEN run that concludes success has necessarily published (PRD-298 DATA FLOW; `cuttingboard.yml` :386–442). **Bounding note (adversarial finding #7b):** this packet ALSO introduces a `SATISFIED` no-op success path (§7.4) that concludes success WITHOUT publishing (`PUBLISH_READY` stays false → commit/push skip). So post-change, "OPEN success" no longer implies "*this* run published" in general. The property coordination actually consumes is weaker and still true: **the FIRST qualifying OPEN success today published**, because a no-op success can only occur downstream of a prior `SATISFIED` verdict, which itself requires a prior real published success. Thus `∃ qualifying OPEN success today ⟺ the slot was really published today`. No non-coordination consumer reads "OPEN success ⇒ this run published"; the workflow's own publish is `PUBLISH_READY`-gated, not conclusion-gated |
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
`github.event.*` (contexts: `github`, `inputs`, `vars`), and the evaluated value
is returned as `display_title` on each run object from the list endpoint
(confirmed feasible, adversarial finding #1). For `workflow_dispatch`, the token
derives from the validated `slot` input. For the `schedule` OPEN fallback cron,
the token derives from a cron-string → slot map (`github.event.schedule`). A
chained-boolean expression covers both without shell, e.g.:

```yaml
run-name: >-
  ${{ github.event_name == 'workflow_dispatch' && inputs.slot && format('CB-SLOT:{0}', inputs.slot)
   || github.event.schedule == '<OPEN-fallback-cron>' && 'CB-SLOT:OPEN'
   || github.event.schedule == '50 12 * * 1-5' && 'CB-SLOT:PRE'
   || format('cuttingboard {0}', github.run_number) }}
```

The exact expression is finalized at the PRD/implementation stage; the DESIGN
commitment is: **every automatic PRE/OPEN run carries exactly one `CB-SLOT:`
token in `display_title`, and no other run does.** Two implementation-review
verification obligations (adversarial finding #1, cheap, non-blocking):
(i) confirm `inputs.slot` on a `schedule` event coerces falsey (guarded by the
explicit `event_name == 'workflow_dispatch'` test above); (ii) confirm the
non-slot crons (Sunday `30 23 * * 0`, and any run not matching a slot) evaluate
to a default that does NOT contain the substring `CB-SLOT:`, so clause-4
matching is safe.

### 5.2 Match predicate for "a satisfied OPEN slot"

A completed run **SATISFIES today's OPEN slot** iff ALL hold (every clause a
GitHub-native fact; `source` is never read here):

1. workflow path == `.github/workflows/cuttingboard.yml`;
2. `event` ∈ {`workflow_dispatch`, `schedule`};
3. `head_branch` == `main`;
4. `display_title` contains `CB-SLOT:OPEN`;
5. `created_at` (UTC) falls **within today's OPEN dispatch WINDOW, anchored in
   UTC** — not merely today's calendar date;
6. `status` == `completed`;
7. `conclusion` == `success`.

**Clause 5 is a WINDOW, and it is anchored in UTC (evidence review C1/D1 — this
supersedes v0.1's PT anchoring, which was a real winter defect).** Two reasons
the window must be a window, and must be UTC:

- *Why a window, not a bare date (v0.1 finding #5):* a bare same-date test would
  let ANY earlier successful `CB-SLOT:OPEN` run that day — an operator's off-hour
  `slot=OPEN` dispatch, or a mis-fired early trigger — permanently satisfy the
  slot and thereby SUPPRESS the real scheduled OPEN, producing the exact
  missing-board failure this design exists to prevent (the predicate is
  source-blind by §10, so a manual `slot=OPEN` run is otherwise indistinguishable
  from the automatic clock).
- *Why UTC, not PT (evidence review C1):* **both** clocks that produce candidate
  runs are UTC — GitHub Actions schedule crons are UTC, and Cloudflare Worker
  cron triggers are UTC-only (no timezone support). A PT-anchored window would
  track the trigger instants only in PDT: the existing live cron `0 13 * * 1-5`
  is labelled "06:00 PT / 13:00 UTC" (`cuttingboard.yml:8`), true in summer but
  05:00 PST in winter. A PT window like `[05:55, 06:20)` would EXCLUDE the real
  ~13:00/13:05 UTC runs every winter → `UNSATISFIED` for ~4–5 months/year →
  systematic double-execution. Anchoring the window in UTC to the actual trigger
  instants contains the real runs in BOTH DST regimes.

The window is a REVIEWED DESIGN parameter bracketing the actual UTC trigger
instants (~13:00 UTC CF + ~13:05 UTC fallback) with margin — candidate
**`[12:50, 13:25) UTC`** — exact bounds set at Stage-0 from CF-E1/E2 run-time
evidence; it is a constant in the helper (no persisted state, still
GitHub-native). **PT-date identity is preserved, not lost:** 12:50–13:25 UTC
maps to 04:50–05:25 (PST) or 05:50–06:25 (PDT) — early morning on the SAME
calendar date in both PT and UTC (the slot is far from any date boundary in
either zone), so the UTC window and the logical PT trading date coincide. The
weekday OPEN slot never lands on a DST-transition day (transitions occur Sunday;
OPEN is `1-5`), so there is no transition-day edge. Both the CF OPEN trigger and
the delayed GH fallback fall inside the window year-round; an off-window
operator/recovery run does not (and per charter, manual runs do not participate
in automatic coordination anyway). If Dustin instead wants a fixed *PT* board
time year-round, that is a larger design (a seasonal cron pair), called out here
and not chosen.

PRE and OPEN cannot collide (distinct tokens, clause 4). Previous-day and
off-window runs cannot qualify (clause 5). Manual ordinary dispatches
(`mode`-only, no `CB-SLOT:OPEN`) cannot qualify (clause 4); a manual *in-window*
`slot=OPEN` dispatch is definitionally an OPEN run and would qualify — that is
the intended, safe behavior (a real in-window published OPEN board IS the slot
satisfied), and it is pinned by test T20 (§11). Wrong-ref runs cannot qualify
(clause 3). A PRE run cannot satisfy OPEN (clause 4).

### 5.3 Date-boundary rule (the rerun / stale-success guard)

The UTC window membership (clause 5) is derived **at query time** from each
candidate run's **original creation instant** (`created_at`, UTC). This is what
makes clauses 5–7 immune to reruns:

- A re-run of a previous-day run keeps its original `created_at` → stays in its
  original UTC date/window → cannot satisfy today's slot (Phase-1 #6/#7).
- The OPEN window (~13:00 UTC) sits far from the UTC midnight boundary, so a
  `created=>=<utc-today-00:00Z>` server-side filter safely captures every
  candidate for today's OPEN slot; the UTC calendar date of the window equals
  the PT trading date for this slot (§5.2), so no PT candidate is dropped.

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
PT-date/window bucket + GitHub-native run fields are sufficient evidence. (If review
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

**OPEN CONCURRENCY GROUP — RECOMMENDATION: a dedicated group (evidence review
C2/D2; corrects v0.1's mischaracterization).** The existing group
`cuttingboard-pipeline` is STATIC and shared across all slots. GitHub allows only
ONE *pending* run per group: if CF-OPEN is still running at ~06:05 and the
fallback queues *pending* behind it, then any third same-group run queuing (a
manual dispatch in the gap; prefetch is done by ~05:58; Sunday is a weekend)
would **cancel the pending fallback** — and if CF-OPEN then fails, the fallback
that should have covered it is gone → missing board. A real availability hole.

**Give coordination-participating OPEN runs their own concurrency group** (keyed
on the trading date) so a pending OPEN fallback cannot be evicted by an unrelated
slot. **This does NOT reintroduce a publication race** — v0.1 wrongly claimed it
would. Verified: `hourly_alert.yml` runs under a DIFFERENT group (`hourly-alert`,
`:27`) and already publishes to the same `publish` branch CONCURRENTLY with
`cuttingboard-pipeline`; cross-workflow publish-race safety lives in
`tools/ci_push_artifacts.sh` (delta-append + bounded push-retry), NOT in the
shared concurrency group (`cuttingboard.yml:31–33` states exactly this). The only
cross-slot mutable seams in `cuttingboard.yml` are (i) the `publish` branch
(delta-append-safe, already exercised concurrently) and (ii) the OHLCV
`actions/cache`, whose sole writer is `prefetch` (`Save OHLCV cache` gated on
`job_mode=='prefetch'`; live/OPEN never saves it). A dedicated OPEN group touches
neither seam unsafely. Stage-0 records the one-line confirmation of these two
seams and corrects the PRD-194 characterization. (Option "keep the shared group
and accept the eviction hazard" is rejected: it leaves the missing-board hole the
whole design exists to prevent.)

### 7.5 Delayed OPEN fallback cron — REPLACES the existing 06:00 live cron

Two separable changes to the existing `0 13 * * 1-5` (13:00 UTC ≈ 06:00 PDT /
05:00 PST) live cron — the evidence review (C3) requires distinguishing them:

- **(a) CORRECTNESS REQUIREMENT (forced).** The existing live cron must NOT run
  un-gated alongside a CF dispatch: at the same instant it would run `live`
  unconditionally (no `CB-SLOT:OPEN` token, no §7.4 pre-check) *alongside* CF →
  guaranteed double execution. So the existing cron MUST be made
  coordination-participating — carry the `CB-SLOT:OPEN` token and run the §7.4
  first-success pre-check. This is non-negotiable and does not by itself change
  the cron's time or retire the heartbeat.
- **(b) RETIMING TO A DELAYED FALLBACK (elective — HELD for Dustin).** The
  charter frames GH as a "~5-min-delayed fallback" behind CF's punctual clock
  (justified because GitHub scheduled crons fire unreliably late, which is the
  actual case for CF punctuality). Implementing that means retiming the ~13:00
  UTC cron ~5 min later. **This conflicts with ratified CF-D4 — "Retain the
  existing GitHub cron heartbeats in slice 1" (`DECISIONS.md:73`)** — and is NOT
  inside §16's auto-ruling boundary. Reconciling the charter's delayed-fallback
  intent with CF-D4 is a GOV-2 §10 canonical-ruling-propagation act only Dustin
  can make (§16 item 4). Until he rules, the design lands change (a) only and
  keeps the heartbeat at its current time; (b) awaits his ruling.

Whichever timing Dustin rules, the OPEN cron carries `CB-SLOT:OPEN` via the
cron→slot map and runs the §7.4 first-success query, participating in the
identical symmetric rule (D3: expressed as a fixed-UTC cron, DST-drifting in PT
per the existing convention, not labelled PT-stable).

**Rollout / graceful-degradation consequence (flagged for Dustin).** The Worker
ships UNDEPLOYED (§9). Under change (a)-only (heartbeat kept at ~13:00 UTC,
token + pre-check added), the daily board time is UNCHANGED pre-deployment — the
existing cron still fires at its current instant and, with no prior CF success,
executes normally. The ≈5-min board-time shift arises ONLY if Dustin rules to
retime (b): then, before the Worker is deployed, the delayed cron is the sole
OPEN trigger and the board publishes ~5 min later; once CF is deployed, CF fires
punctually and the delayed cron is the fallback. That shift is within the
charter's evidence-supported ~5-min allowance but is a real behavioral change to
the board time — surfaced with the CF-D4 ruling (§16 item 4), not buried. The
PRD-158 pre-implementation grep sweep MUST enumerate every `resolve_run_mode` /
workflow test that asserts the current `0 13 * * 1-5 → live` mapping —
`tests/test_resolve_run_mode.py` exists and is in scope — and fold them into
FILES.

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
| CF OPEN already succeeded, then fallback's proof query transiently errors | `PROOF_ERROR` → execute → **possible duplicate publish** (accepted: availability over suppression, §6.2/§10) |
| Old successful run from previous PT date, or same-date but off-window | excluded by §5.2 clause 5 (window) / §5.3 |
| PRE run | not `CB-SLOT:OPEN` → ignored for OPEN |
| Manual ordinary run (`mode`-only, no `CB-SLOT:OPEN`) | ignored for automatic coordination (clause 4) |
| Manual in-window `slot=OPEN` dispatch | definitionally an OPEN run; qualifies if it succeeds+publishes in-window (intended; source-blind, §10) |
| Prior OPEN pending-behind a long CF-OPEN, evicted by a third same-group enqueue | availability hazard — §7.4 concurrency-group decision |
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
completed and (for an executing live OPEN) published, per existing artifact
truth. It does NOT promote dashboard freshness or market validity beyond what
the published artifacts already assert. Coordination reads run conclusion; it
never reads or asserts market/quote/displacement facts.

**Duplicate-publish cost (owned, adversarial finding #4/#7c).** Because the
fallback fails toward availability (§6.2), a `PROOF_ERROR` at the fallback's
pre-check when a prior CF OPEN already succeeded yields a SECOND live OPEN run
that re-renders and re-publishes today's board from ~5-min-later data and may
re-emit the single success/HALT notification. This is not free, and the packet
does not pretend it is. It is bounded and accepted: (i) the second board is the
SAME slot's board, monotonically written (`safe_write_latest` guards
`latest_run.json`; the published board is idempotent in identity, only fresher
in data); (ii) a duplicate operator notification is a strictly smaller harm than
a silently missing morning board; (iii) it occurs only under provable
API-evidence unavailability, not in the normal path. Whether the duplicate
success notification should additionally be de-duplicated is a candidate
follow-up, explicitly NOT bundled here (§18), and does not gate this slice.

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
| T10 | Successful OPEN run with previous-PT-date `created_at` | excluded → `UNSATISFIED` | move date to today (in-window) → `SATISFIED` (proves date bucketing) |
| T10b M | Successful `CB-SLOT:OPEN` run today but OFF-WINDOW (e.g. 05:00 PT) | excluded → `UNSATISFIED` (real OPEN not suppressed) | widen predicate to bare date → wrongly `SATISFIED` (proves §5.2 clause-5 window closes finding #5) |
| T11 | `CB-SLOT:PRE` success run only | ignored for OPEN → `UNSATISFIED` | change token to OPEN → `SATISFIED` |
| T12 | Manual run (no `CB-SLOT:` token) success | ignored → `UNSATISFIED` | add OPEN token → `SATISFIED` |
| T13 | Run on non-main `head_branch` | ignored → `UNSATISFIED` | set branch=main → `SATISFIED` |
| T14 | Wrong slot/mode dispatch (`OPEN`+`prefetch`) | resolver fails closed (non-zero, no execute) | align mode→live → resolves/executes |
| T15M | Re-run: previous-day run re-run today (original `created_at` yesterday) | still excluded (bucketed by original creation) | bucket by `run_started_at` instead → wrongly `SATISFIED` (proves the §5.3 field choice) |
| T16 | `source=cloudflare` on a manual run without OPEN token | ignored (source-blind predicate) → `UNSATISFIED` | — (documents spoof-inertness) |
| T17 | Valid HALT board still satisfying post-298 | `SATISFIED` for a valid market-stress HALT OPEN | — |
| T18 | Publish-failure run (live, `conclusion=failure`) | non-satisfying → `UNSATISFIED` | — |
| T19 | Current run excluded from its own scan | current `run_id` never self-satisfies | remove exclusion → false self-satisfy |
| T20 | Manual in-window `slot=OPEN` success (source-blind) | `SATISFIED` (intended: a real in-window OPEN publish IS the slot) | — (pins the §5.2 accepted behavior) |
| T21 | CF OPEN success present, fallback pre-check hits API error | `PROOF_ERROR` → executes (duplicate accepted); NEVER `SATISFIED`-suppressed on error | flip error→treated-as-satisfied → wrong suppression (proves fail-toward-availability) |
| T22 | No-op success run (SATISFIED path concluded success) exists alongside the real publish | `∃ qualifying OPEN success ⟺ real publish occurred` holds; no-op never the sole matcher | construct no-op-only-without-prior-publish (unreachable) → asserts invariant |
| T23 | Original publishing run re-run today and the re-run FAILS (latest-attempt `conclusion=failure`); a no-op success also present | suppression still SAFE — the published board persists on the `publish` branch; a failed re-run does not unpublish (evidence review C4, Target 6 edge) | remove the persistence argument / treat re-run-failure as unpublish → wrong; pins the one falsifiable case of the §3/Phase-1-#3 prose invariant |
| T24 (PST) | CF + fallback runs at ~13:00/13:05 UTC on a WINTER (PST) date | both fall inside the UTC window → deduped (proves UTC anchoring, C1) | use a PT-anchored `[05:55,06:20)` window → winter runs excluded → double-execute (reddens the v0.1 defect) |

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
- `M tests/test_resolve_run_mode.py` — slot/mode fail-closed cases; the file
  EXISTS (verified) and asserts the current cron→mode mapping, so it is in FILES
  and its `0 13 → live` assertions are updated by the PRD-158 sweep
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

**Review decisions (D1–D3 resolved by the evidence review C1–C2; D3/CF-D4 held
for Dustin — see §16 item 4):**

- **D1 — OPEN dispatch window bounds (§5.2 clause 5).** RESOLVED: anchor in
  **UTC**, candidate `[12:50, 13:25) UTC`, bracketing the ~13:00/13:05 UTC
  trigger instants; exact bounds set at Stage-0 from CF-E1/E2 run-time evidence.
  In-boundary (a helper constant); escalates to charter RETURN-7 only if evidence
  shows no window satisfies both containment and exclusion.
- **D2 — OPEN concurrency group (§7.4).** RESOLVED: a **dedicated** group for
  coordination-participating OPEN runs (keyed on the trading date). Verified not
  to reintroduce a publish race (PRD-194 publish-safety is in
  `ci_push_artifacts.sh`, not the shared group; the only cross-slot seams are the
  delta-append-safe `publish` branch and the prefetch-only OHLCV cache). Closes
  the pending-eviction/missing-board hazard.
- **D3 — fallback clock / DST (§7.5).** A single **fixed-UTC** fallback cron,
  paired with the D1 UTC window; documented as tracking a fixed UTC instant that
  drifts ±1h in PT across DST (the existing accepted convention,
  `cuttingboard.yml:8`) — NOT labelled "~06:05 PT" as if PT-stable. The exact
  fallback minute and the PRD-158 test-sweep set (`tests/test_resolve_run_mode.py`
  exists and MUST be in FILES) are Stage-0 items. **Whether the existing 06:00
  heartbeat is retimed at all is HELD for Dustin (CF-D4 conflict, §16 item 4).**

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
inside ALL of the following (verified true for v0.2):

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

### Items requiring Dustin's EXPLICIT ruling (NOT auto-effective)

The evidence review (§20, C3) identified one element outside the auto-ruling
boundary above:

- **Item 4 — CF-D4 heartbeat conflict (from §7.5).** Retiming the existing
  ~13:00 UTC live heartbeat into a ~5-min-delayed fallback conflicts with
  ratified **CF-D4 — "Retain the existing GitHub cron heartbeats in slice 1"**
  (`DECISIONS.md:73`). The auto-ruling list contains no authorization to modify
  CF-D4. This session's charter frames the delayed fallback as approved GREEN
  recon, so the charter and CF-D4 are in tension; reconciling them is a GOV-2 §10
  canonical-ruling-propagation act (mark CF-D4 SUPERSEDED and record one current
  ruling) that only Dustin can perform. **Options for his ruling:** (i) confirm
  the charter supersedes CF-D4 for this slice → retime to the delayed fallback,
  and mark CF-D4 SUPERSEDED in DECISIONS; or (ii) keep CF-D4 → land change (a)
  only (existing heartbeat kept at its current instant, made
  coordination-participating with token + pre-check), no retiming, CF and the
  heartbeat both nominally ~13:00 UTC and deduped via first-success +
  serialization + natural GitHub cron lateness. The correctness requirement
  (token + pre-check on the heartbeat) holds under BOTH options; only the timing
  differs. Implementation of the retiming is blocked until this ruling.

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

---

## 19. Author-side hardening pass (GOV-2 §3 evidence — NOT the independent gate)

Before hand-off, the authoring session ran one fresh-context adversarial pass
against v0.1 whose only charge was to falsify the design. Per GOV-2 §3 this
**contributes evidence and does NOT satisfy the independent-review
requirement** — it is author self-verification, not the GOV-2 §2/§7 Codex gate,
which remains PENDING (§17). It is recorded here for the independent reviewer's
provenance and to avoid re-litigating settled points.

Findings and dispositions (all folded into this revision):

| # | Finding | Severity | Disposition |
|---|---|---|---|
| 1 | `run-name` schedule-branch feasibility + two coercion checks | verify | HOLDS; expression + verification obligations added to §5.1 |
| 2 | `created_at` immutability across re-runs | confirm | HOLDS; §5.3 unchanged, its flagged obligation retained |
| 3 | Actions API filters/fields all exist; `?event=` single-valued | confirm | HOLDS; §5.2 already filters event client-side |
| 4 | §1 overclaimed "no duplicate" vs `PROOF_ERROR`→execute | correctness-of-spec | ACTIONED — §1 reworded; §10 owns the duplicate cost; §8/§11 rows added |
| 5 | Same-PT-*date* + source-blind suppresses the real OPEN (missing board) | **blocking defect** | ACTIONED — §5.2 clause 5 changed from date to **window**; T10b/T20 added |
| 6 | Pending-fallback eviction under shared static concurrency group | availability hazard | ACTIONED — §7.4 decision D2 recorded + §14; candidate fix stated |
| 7a | Existing 06:00 live cron not removed → double execution | **blocking defect** | ACTIONED — §7.5 now REPLACES the cron; rollout consequence + PRD-158 sweep noted |
| 7b | "success ⇒ published" invariant broken by the no-op path | consistency | ACTIONED — Phase-1 #3 bounded to the first qualifying success; T22 added |
| 7c | Duplicate publish/notification cost unowned | honesty | ACTIONED — §10 duplicate-publish paragraph |

Net effect: two blocking defects (#5, #7a) were caught and corrected at the
packet stage — the value of running the adversarial pass before hand-off. No
finding falsified a Phase-1 assumption or breached an owner pre-authorization
boundary; the design remains RED-free and in-bounds (§16). The two `blocking`
items were design-of-spec corrections, not a redesign, and introduce no new
persisted state, no credential-scope change, and no CF-D1b/CF-E2 coupling.

---

## 20. Evidence-review correction cycle (v0.1 → v0.2; NON-GATING)

A fresh-context independent EVIDENCE review of v0.1 @
`982615442e7e3ebcfb60b440feb04436a010ae13` returned REQUIRED CHANGES. Full record:
`PACKET.review.evidence.md` (this directory). Per GOV-2 §3 it is EVIDENCE, not
the independent-review gate — the GOV-2 §2/§7 Codex packet review (§17) remains
PENDING and reviews THIS corrected head. Corrections folded in:

| # | Finding (evidence review) | Disposition | Where |
|---|---|---|---|
| C1 | OPEN window PT-anchored but the CF + GH clocks are UTC → excludes real runs every PST winter → seasonal double-execution | ACTIONED — re-anchored the window to **UTC** `[12:50, 13:25)`; PT-date identity preserved; false "both fall inside" claim removed; T24 PST test added | §5.2, §5.3, §14-D1 |
| C2 | v0.1 wrongly claimed a dedicated OPEN concurrency group creates a publish race; PRD-194 mischaracterized | ACTIONED — recommend a **dedicated** OPEN group; corrected: publish-safety is in `ci_push_artifacts.sh`, not the shared group (`hourly-alert` already publishes concurrently); two cross-slot seams stated benign | §7.4, §14-D2 |
| C3 | §7.5 cron replacement conflicts with ratified **CF-D4** (retain heartbeats) and over-states "correctness fix" | ACTIONED + **HELD FOR DUSTIN** — split into forced correctness (token + pre-check) vs elective retiming; CF-D4 conflict raised as §16 item 4 for explicit owner ruling | §7.5, §14-D3, §16 item 4 |
| C4 | rerun-conclusion-mutation edge of the no-op invariant asserted "unreachable" rather than pinned | ACTIONED — T23 added, with the `publish`-branch-persistence safety argument | §11 T23 |

Independent re-verification by the author (Author disciplines / sub-agent sweep
re-verification): the C1 cron label (`cuttingboard.yml:8`), the C2 facts
(`hourly-alert` group, concurrent publish, `ci_push_artifacts.sh` delta-append,
prefetch-only cache save), and the C3 CF-D4 wording (`DECISIONS.md:73`) were each
re-checked directly, not taken on the reviewer's word. No correction breached an
owner pre-authorization or introduced persisted state / credential-scope change /
CF-D1b/CF-E2 coupling. The one non-mechanical item (CF-D4) is held for Dustin,
not resolved by the author.

---

END OF PACKET v0.2 — PROVISIONAL, author-hardened (§19) + evidence-review-
corrected (§20), PENDING INDEPENDENT CODEX PACKET REVIEW (§17). One element
(CF-D4, §16 item 4) is HELD FOR DUSTIN'S EXPLICIT RULING. No downstream authority
(Stage-0 PRD, Gate A, implementation) is granted by this document.
