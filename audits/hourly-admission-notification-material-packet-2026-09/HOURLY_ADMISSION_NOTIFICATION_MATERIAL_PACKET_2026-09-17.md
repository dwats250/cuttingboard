# Hourly authority-admission / notification truth -- MATERIAL design packet

```
STATUS: CORRECTED MATERIAL PACKET -- 2026-09-17 -- DESIGN ONLY
CLASS: HIGH-RISK. MATERIALITY: MATERIAL (owner ruling 3, recorded below).
AUTHORIZES NO IMPLEMENTATION, NO PRD, NO GATE A, NO MERGE.
GOV-2 PACKET-REVIEW CYCLE: EVENT 1 (Sol/Codex, fresh context, HIGH) at
  packet head 6505e2a3: ACCEPT WITH CHANGES (5 REQUIRED, 4 RECOMMENDED) --
  CODEX_EVENT_1_REVIEW_2026-09-17.md. All 5 REQUIRED verified by the author
  against the head and ACTIONED in this ONE consolidated correction; the 4
  RECOMMENDED also ACTIONED. EVENT 2 exact-corrected-head confirmation PENDING.
BASE: main def0eb83963bc02865ae46759f323ec47d1f89fe (merge of PR #337).
PROVENANCE: promoted from the owner-charged read-only design recon of
2026-09-17 ("HOURLY AUTHORITY-ADMISSION / NOTIFICATION TRUTH", MODE:
DESIGN / RECON FIRST) and the owner rulings that answered it. No
reconnaissance is restarted and no mechanism is redesigned here.
Ceilings below are ESTIMATES carried into the downstream PRD (GOV-2 sec5).
```

> Sequence (owner charge, GOV-2 sec2/sec7): this packet -> Event-1
> independent Codex/Sol review -> one consolidated correction if required
> -> Event-2 exact-corrected-head confirmation -> return for the owner
> design-direction ruling -> bounded implementation PRD -> fresh-context
> independent PRD review -> explicit Gate A -> only then implement.

## 1. INCIDENT EVIDENCE (2026-09-15)

Read from `gh run list/view`, the GitHub job-log API, and `origin/publish`.

- PR #335 merged at 04:03Z. CI on `main` @ 306ea153 FAILED (paired-run
  `slot_utc` flake; fixed by PR #337 @ dbb900a9, merged 2026-09-16 02:38Z).
- Pipeline run 34972228502 (CB-SLOT:OPEN, 13:00Z): step "Exact-SHA CI proof"
  FAILED; "Notify on failure" ran. Correct fail-closed. No 2026-09-15 daily
  carrier ever reached `publish`.
- Nine hourly `workflow_dispatch` runs on 2026-09-15 (13:30Z .. 20:01Z; from
  34975381741 through 35017065416) plus six `schedule` liveness runs; all
  fifteen concluded `failure` (GitHub run metadata). For the dispatch runs the
  step conclusions show every step through "Commit hourly artifacts"
  SUCCEEDED, including the ordinary Telegram send, and "Push hourly
  artifacts" FAILED. The full job log was read for ONE run (34975381741);
  it shows `artifact publish: authority non-regression REFUSED (R5) on
  logs/latest_hourly_contract.json` then `hard error on attempt 1 - aborting`.
  UNVERIFIED (not read): the per-run Telegram delivery lines and refusal text
  of the other eight dispatch runs; they are inferred from identical step
  conclusions. Log excerpt (run 34975381741):
  ```
  13:30:32Z INFO  hourly alert admitted: slot_utc=2026-09-15T13:30:00+00:00
  13:31:54Z INFO  Telegram delivered: 'OBSERVE ONLY -- OPERATOR LOCK' (214 bytes)
  13:32:02Z INFO  hourly alert completed: status=SUCCESS ... exit=0
  artifact publish: 63 file(s) -> publish
  artifact publish: authority non-regression REFUSED (R5) on logs/latest_hourly_contract.json
  artifact publish: hard error on attempt 1 - aborting
  ```
- `git log origin/publish --since=2026-09-12` shows commits on 09-14 (last
  47fff037 20:01Z) and next on 09-16 (bcced276 13:03Z); ZERO commits dated
  2026-09-15. INFERRED (not separately observed): Pages therefore served
  the 09-14 board all day, since pages.yml deploys only `origin/publish`.
- Six `schedule` (liveness) arrivals on 09-15 concluded `failure` (RED),
  correctly. No hourly failure Telegram exists in `hourly_alert.yml`, so the
  operator received up to nine normal-looking alerts (one verified by log)
  and no failure notice.
- Published carriers: `origin/publish@47fff037:logs/latest_run.json` and
  `logs/latest_hourly_contract.json` both carry
  `authority_version ["2026-09-14",1,1]`, `session_date 2026-09-14`,
  `valid_until 2026-09-15T08:00:00+00:00`.
- Falsifier: if `origin/publish` held any 2026-09-15 commit, or if the
  hourly job logs showed the send AFTER the push step, this account is wrong.
  Neither is the case.

## 2. CURRENT ORDERING (verified at def0eb83)

Hourly lane, `cuttingboard/runtime/__init__.py::_execute_notify_run` (:540)
and `.github/workflows/hourly_alert.yml`:

| # | Step | Location |
|---|------|----------|
| 0 | Publish-state restore: audit, last_hourly_slot, latest_hourly_market_map, latest_run (read-only, daily-owned), macro snapshot, regime_history, run_*. `logs/latest_hourly_contract.json` (the publish ACCEPTED tip R5 compares against) is NOT restored. | hourly_alert.yml:127 |
| 1 | alert_runner admits the slot (window + same-slot dedup from restored last_hourly_slot.json) and calls `_execute_notify_run`. | alert_runner.py:150-210 |
| 2 | Observation / qualification: fetch_all -> validate -> regime -> derived -> structure -> candidates -> SHORT gate -> ohlcv -> qualify. | runtime :563-690 |
| 3 | Alert formatted from `operator_locked` + qualification. The hourly Telegram body does NOT read the EffectivePermission projection (output.py:346 `project()` is the daily `build_notification_message` path). | runtime :690-707 |
| 4 | ORDINARY TELEGRAM SEND when `mode == MODE_LIVE`; `alert_sent` captured. Nothing between alert formatting and this send writes, mutates the summary, builds a market map, or appends an audit row. | runtime :708-712 |
| 5 | `run_at_utc` derived (`regime.computed_at_utc` else `datetime.now`), then hourly contract + summary built with `alert_sent` baked in. | runtime :715, :714-753 |
| 6 | EffectivePermission carrier: `_load_accepted_authority(run_date, run_at_utc)` reads latest_run.json then latest_contract.json through `admit_persisted` (:1241-1257); `carry_forward(...)` if admitted else `ep_authority.unavailable(...)`; `persist()` onto contract + summary; `_write_hourly_artifacts`. | runtime :754-764 |
| 7 | Market map; `save_last_slot(slot_utc)` ONLY IF `alert_sent`; sidecars; return `{"status": SUCCESS}`. | runtime :798-802, :917 |
| 8 | Workflow: freshcheck (payload mtime) -> aggregate -> render -> `check_readiness.py` -> commit (explicit allowlist incl. latest_hourly_contract.json). All `if: success()`. | hourly_alert.yml:174-271 |
| 9 | Push: `tools/ci_push_artifacts.sh::authority_guard` runs (a) `effective_permission.py publication-admits <origin/publish tip carrier> <incoming>` (R5) and (b) `authority_projection.py admit <incoming> <runner UTC date>` (Slice-2 read boundary; `now=None`). Refusal = exit 1 = job RED, no publish. | ci_push_artifacts.sh:70-110 |
| 10 | `pages.yml` deploys `origin/publish` on `workflow_run` completion (branch simply did not move). | pages.yml |
| 11 | Liveness probe reads `origin/publish:logs/last_hourly_slot.json`. | scripts/check_hourly_liveness.py |

The exception branch (:919-972) already: formats
`format_failure_notification(NOTIFY_HOURLY, date_str, reason)`, sends exactly
one failure Telegram, writes `traceback.txt`, builds an error contract
(`OUTCOME_HALT`) and a FAIL summary via `_write_hourly_artifacts`, returns
`{"status": FAIL}`; alert_runner then exits 1 (:207-211).

## 3. CANONICAL ADMISSION SEAM

Two pure, read-only functions in `cuttingboard/effective_permission.py` are
already the sole authority on every publication route:

- `publication_admits(accepted_envelope, incoming_envelope)` (:282-317), R5
  non-regression. A non-canonical incoming is refused; the UNAVAILABLE sentinel
  (`decision_uid ""`, `decision_seq 0`, `valid_until None`; :91-98) always fails
  `_valid_canonical` (:189-215), so an unavailable carrier is NEVER admissible.
- `admit_persisted(envelope, current_session_date=, now=None)` (:218-238),
  which `authority_projection.admit_projection` (:112-125) routes through for the
  Slice-2 CLI (:267-271, `now=None`).

Inputs the runner holds or can hold read-only at step 6: the incoming
envelope is `_hourly_ep.to_envelope()` (exactly what `persist()` writes,
:318-322); the accepted envelope is the publish tip's
`latest_hourly_contract.json` canonical field, readable through the existing
`effective_permission._read_authority(path)` (:333-341) once the workflow
restores that file read-only.

The carrier depends only on restored files, `run_date`, `run_at_utc`, and the
halted/locked flags. None of those depend on the send. The run therefore knows
publication will be refused BEFORE any user-facing delivery, with no
side effect until `persist()`/write.

## 4. WHY SEPTEMBER 15 ESCAPED

- `_load_accepted_authority(session 2026-09-15)` -> `admit_persisted` refused
  the restored 09-14 envelope as prior-session (:230) -> `_acc None` ->
  `_hourly_ep = unavailable("2026-09-15")`.
- The ordinary Telegram had already been sent at step 4, two steps earlier,
  with wording derived from `operator_locked`, not from the carrier.
- The publisher's `publication_admits(accepted 09-14 tip, incoming UNAVAILABLE)`
  -> `_valid_canonical` false -> REFUSED (R5) -> hard error.
- `save_last_slot` ran (alert_sent true) but could not be published, so
  liveness went RED correctly.

Root cause in one line: the ordinary send precedes the carrier computation,
and admissibility is tested only in the publisher.

## 5. OWNER RULINGS RECORDED (Dustin / HELM, 2026-09-17; verbatim)

### Ruling 1 -- MARKET-STRESS HALT DURING ADMISSION REFUSAL (APPROVED RULE)

If the hourly run contains a valid market-stress HALT but its authority
carrier is inadmissible for publication:

- DO NOT send the ordinary hourly/HALT success notification.
- Send exactly one operational-failure notification.
- The failure notification MUST preserve the fact that a market-stress HALT
  was observed and include its existing bounded reason/context.
- It MUST also state that the hourly board update was refused / not
  published.
- The HALT observation does not make the inadmissible carrier authoritative
  and does not bypass EffectivePermission or R5.

Goal: safety information remains visible without falsely representing
successful publication.

### Ruling 2 -- REFUSED-SLOT FAILURE DEDUP (APPROVED RULE)

One failure notification per refused workflow dispatch is acceptable.

Within one dispatch/run: exactly one failure notification attempt; zero
ordinary hourly notifications.

Across separate dispatches: no new cross-run dedup requirement; do not invent
a new persistence/state channel solely for suppression; publication remains
the existing durable cross-run state boundary. A repeated legitimate dispatch
may therefore produce another failure notification.

### Ruling 3 -- CLASSIFICATION / REVIEWER

CLASS: HIGH-RISK. MATERIALITY: MATERIAL. Reason: the implementation changes
ordering at the canonical authority-admission/user-notification boundary and
selects a seam shared across publication authority and user-facing delivery.
Small LOC does not make this local.

Builder after Gate A: fresh-context Claude Code implementation session,
Builder role only. Independent/adversarial review: fresh-context Codex/Sol;
reviewer must not be the implementation author/session; exact-head evidence
required.

### Ruling 4 -- DESIGN DIRECTION (APPROVED FOR MATERIAL-PACKET FORMATION)

Use the existing canonical pure functions `publication_admits` and
`admit_persisted`. Do not create or duplicate authority logic. The intended
smallest mechanism is:

- restore the existing hourly-owned carrier needed for admission
- move/compute the EffectivePermission carrier before ordinary Telegram
  delivery
- perform the canonical read-only admission checks in-process
- on refusal, enter the existing failure path before ordinary notification
- reuse that branch for one failure Telegram, traceback/diagnostics, error
  contract and failing exit
- preserve R5 as the publication authority
- preserve zero publication on refusal
- preserve liveness RED capability

No change to: EffectivePermission resolution semantics; authority-version
ordering; recovery/carry semantics; operator availability; qualification;
trade decisions; market-stress HALT semantics; Cloudflare/GitHub scheduling
ownership; publish-branch ownership.

### Ruling 5 -- GOVERNANCE STATE

IMPLEMENTATION IS NOT YET AUTHORIZED. This packet exists to capture incident
evidence, canonical seam, the rulings above, FILES/LOC estimates, invariants,
test/mutation proof, and rollback, then follow the MATERIAL sequence.

## 6. DESIGN (the smallest correct mechanism, per Ruling 4)

D1. Workflow restore (one token). `hourly_alert.yml:127` restore list gains
`logs/latest_hourly_contract.json`. The hourly lane OWNS and regenerates this
file and already force-adds it at :249, so restoring it is read-then-overwrite,
never a republish of another producer's copy. Without it the in-runner
accepted envelope is main's frozen copy and the pre-flight would be weaker
than the publisher on the "behind tip" branch.

D2. Hoist the carrier, not the artifact clock. In `_execute_notify_run`, the
block now at :755-761 (`_acc` / `_hourly_ep`) moves to immediately BEFORE the
ordinary send (:711). The loader's staleness clock at that point is a
dedicated `_preflight_now = datetime.now(timezone.utc)`; the artifact
`run_at_utc` at :715 STAYS where it is (after the send) so that on runs where
`regime is None` (validation-halted / system-halted) the generation
identifiers, contract and summary timestamps, and published bytes are derived
exactly as today. `carry_forward` and `unavailable` read no clock, so the
carried envelope is identical whichever `now` the loader used (the loader's
`now` only affects the stale check by seconds). The later block at :755-761
is deleted; the `persist()` calls at :762-763 stay where they are.

D3. In-process canonical pre-flight with ONE frozen workflow session.
Immediately after `_hourly_ep` exists, and only when
`mode == MODE_LIVE and notify_mode in _HOURLY_MODES`:

```
admit_session = os.environ.get("CB_WORKFLOW_SESSION") or date_str
accepted = ep_authority._read_authority(str(LATEST_HOURLY_CONTRACT_PATH))
incoming = _hourly_ep.to_envelope()
admissible = (
    ep_authority.publication_admits(accepted, incoming)
    and ep_authority.admit_persisted(
        incoming, current_session_date=admit_session, now=None) is not None
)
if not admissible:
    raise HourlyPublicationInadmissible(<message per D4>)
```

Session parity (Event-1 REQUIRED 2): the publisher computes
`PUBLISH_SESSION="${CB_WORKFLOW_SESSION:-$(date -u +%F)}"`
(ci_push_artifacts.sh:40) at push time, while `run_date` is captured earlier
by alert_runner (:198-202). Across a 00:00 UTC boundary the two could differ,
so the pre-flight could admit and the publisher refuse. The workflow therefore
FREEZES the session once, before the runner starts, and both consumers read
it: `hourly_alert.yml` sets job-level `CB_WORKFLOW_SESSION: $(date -u +%F)`
in a step before "Run hourly alert" (exported via `$GITHUB_ENV`) and the
existing publisher override consumes it unchanged. `alert_runner` is NOT
modified; `run_date` still drives the carrier's session_date, so a genuine
boundary crossing yields the same refusal in runner and publisher (the
carrier's session_date != the frozen session) rather than a disagreement.
The `or date_str` fallback exists only for direct in-process callers (tests)
where no workflow session is set. `now=None` mirrors the Slice-2 CLI exactly.
The pre-flight is the publisher's two calls with the same inputs (accepted =
restored publish tip, incoming = the envelope that will be persisted, session
= the frozen workflow session). It authors nothing; `_read_authority` is a
read, not authorship (PRD-339 exclusive-writer restricts `persist` /
`persist_copy`).

D4. Refusal enters the EXISTING failure branch. `HourlyPublicationInadmissible`
is a small module-level `Exception` subclass in `runtime/__init__.py`. Its
message is composed to fit the existing 120-char truncation
(`format_failure_notification(notify_mode, date_str, str(exc)[:120])` at
:924) and must state that the hourly board update was REFUSED / NOT
PUBLISHED (R5). Per Ruling 1, when `hourly_kill_switch` is true the message
is prefixed with the EXACT bounded HALT source available at the seam:
`validation_summary.halt_reason`, which the kill-switch trip sets to
`KILL_SWITCH_HALT_REASON` at :593-599 (constant at :3087:
"Market-stress kill switch tripped; new positions halted.", 55 chars). The
composed reason is
`"<halt_reason> | Hourly board update REFUSED, not published (R5)"`
(<= 120 chars including the prefix; no alert title and no reconstructed
context is used). The except branch then (unchanged): one failure send,
`traceback.txt`, error contract with `OUTCOME_HALT`, FAIL summary via
`_write_hourly_artifacts`, return FAIL. `alert_runner` exits 1; every later
workflow step is `if: success()` so publish count is 0; "Upload failure
artifacts" (`if: failure()`) retains `latest_hourly_*.json` and
`traceback.txt`; `save_last_slot` never runs, so liveness can still go RED.

D5. Publisher untouched. `tools/ci_push_artifacts.sh` remains the
publication authority. Two residual classes, recorded separately:
- ACCEPTED-TIP RACE (retained): the publish tip can move between restore and
  push; the publisher then refuses and the job is RED without a Telegram (the
  existing accepted-residual class; a daily-parity hourly failure notifier is
  a separate candidate from the 2026-09-17 audit and is OUT OF SCOPE here).
- UTC-SESSION DRIFT (closed by D3): deterministic input drift between runner
  and publisher session dates is not a residual; it is closed by the frozen
  `CB_WORKFLOW_SESSION` and pinned by test G.

D6. Unchanged for admissible runs: alert wording, send count (one),
`save_last_slot`, sidecars, publish, Pages. Contract and summary content are
unchanged because the artifact clock `run_at_utc` is not hoisted (D2); the
hoisted loader uses its own `_preflight_now`, and the carried envelope does
not depend on it. A market-stress HALT hourly on an admissible day is
unaffected (`carry_forward` raises rank; R5 admits a rank raise).

## 7. FILES (ESTIMATED SURFACE -- NOT YET APPROVED; Gate A sets the ceiling)

Production:
- `cuttingboard/runtime/__init__.py` (hoist ~8 lines; pre-flight ~17 lines
  incl. the session read; exception class ~3 lines; HALT-context compose
  ~3 lines)
- `.github/workflows/hourly_alert.yml` (1 token in the restore list; ~3
  lines freezing `CB_WORKFLOW_SESSION` before "Run hourly alert")

Tests:
- `tests/test_hourly_alert.py` (tests A, B, B2, C, E, G below)
- `tests/test_hourly_slot_idempotency.py` (test D via the alert_runner
  slot harness)
- `tests/conftest.py` (named admitted-authority fixture, see sec 9)
- `tests/test_ci_artifact_hygiene.py` (pin the restore-list token and the
  frozen-session step)

Reference only, unchanged: `tools/ci_push_artifacts.sh` (already honors
`CB_WORKFLOW_SESSION`), `cuttingboard/effective_permission.py`,
`cuttingboard/authority_projection.py`, `cuttingboard/alert_runner.py`,
`.github/workflows/cuttingboard.yml`.

ESTIMATED PROD LOC: 30-45 (runtime) + 4 (workflow).
ESTIMATED TEST LOC: 220-300.

## 8. INVARIANTS (may not change)

- EffectivePermission resolver semantics, `carry_forward`, `unavailable`,
  `authority_version` ordering, R5 `publication_admits`, `admit_persisted`
  fail-closed behavior: not edited, only called.
- The publisher guard stays the authority; the runner pre-flight is a
  pre-image of it, never a replacement.
- Zero publication on refusal (workflow gating unchanged).
- Liveness semantics unchanged (`last_hourly_slot.json` written only on a
  delivered ordinary alert).
- Operator availability, qualification, trade decisions, market-stress HALT
  semantics on admissible days, Cloudflare/GitHub ownership, publish-branch
  ownership, Pages workflow, Telegram transport configuration: untouched.
- Daily path: out of scope; its failure-notification semantics unchanged.
- Notification ownership: exactly one send per run on every path (ordinary
  XOR failure).

## 9. TEST / MUTATION PROOF

Test-ripple (the real cost): 47 `_execute_notify_run(` call sites across 9
test files (24 in `tests/test_hourly_alert.py`; 14 files mention the symbol
but only 9 contain call sites) run with NO accepted carrier; today their EP
is UNAVAILABLE and they expect the ordinary send. Under D3 they would all
flip to the failure path. Mitigation: a NAMED fixture
`admitted_hourly_authority` in `tests/conftest.py` that monkeypatches
`cuttingboard.runtime._load_accepted_authority` to return a same-day admitted
EP, applied `autouse` ONLY within the hourly-path test modules that need it
(via a module-level `pytestmark` / per-module conftest), never suite-wide, so
the real restore/read boundary stays exercised elsewhere. Tests B, B2, C, D,
G override it to `None` or leave it unapplied.

- A. `test_hourly_admissible_carrier_sends_ordinary_once`: admitted accepted
  carrier AND a realistic accepted-tip `logs/latest_hourly_contract.json`
  seeded (so the pre-flight compares against a restored tip, not only the
  bootstrap branch) -> exactly one send, ordinary title, status SUCCESS,
  `last_hourly_slot.json` written, persisted envelope accepted by
  `publication_admits(accepted_tip, envelope)`.
- B. `test_hourly_inadmissible_carrier_blocks_ordinary_send`: accepted
  authority None -> `mock_send.call_count == 1`; the single title is the
  failure title (contains "HOURLY" and "REFUSED"/"NOT PUBLISHED"); no call
  carries the ordinary title; status FAIL; `traceback.txt` exists;
  `last_hourly_slot.json` absent; `latest_hourly_run.json` status FAIL.
- B2. `test_hourly_inadmissible_carrier_halt_context_preserved` (Ruling 1):
  `hourly_kill_switch` true + accepted None -> one failure send whose body
  contains the HALT observation context AND the refusal statement; no
  ordinary HALT alert.
- C. `test_hourly_refusal_notice_transport_failure_still_fails`: send patched
  to return False (and separately to raise) -> status FAIL, artifacts written,
  exactly one send attempt.
- D. `test_refused_slot_redispatch_reaches_runner_and_sends_one_failure`
  (Ruling 2), in `tests/test_hourly_slot_idempotency.py` using its existing
  alert_runner harness (`intraday_now`, `--routine-slot`): two same-slot
  arrivals through `alert_runner.main` with the carrier inadmissible ->
  the first leaves NO `last_hourly_slot.json`; the second arrival is NOT
  returned by the `suppressed_same_slot` path (alert_runner.py:172-191) and
  reaches `_execute_notify_run`; two failure sends total, zero ordinary.
  (A direct double call of `_execute_notify_run` would not exercise the
  dedup boundary and is not the test.)
- E. Existing `test_hourly_sends_exactly_once_system_halted` and
  `_stay_flat` stay green under the named fixture (admissible HALT/flat).
- G. `test_hourly_preflight_uses_frozen_workflow_session` (UTC boundary):
  carrier session_date = run_date D, `CB_WORKFLOW_SESSION` = D+1 -> the
  pre-flight refuses (one failure send, zero ordinary), matching what the
  publisher would do with the same frozen session. RED on a pre-flight that
  derives its session from `run_date` alone.
- F. No daily test touched; `tests/test_prd300_delivery_backstop.py` and the
  cuttingboard.yml notifier tests unchanged.
- Hygiene: `hourly_alert.yml` restore list contains
  `logs/latest_hourly_contract.json`.

Mutation proofs (must be RED):
- M1: move the ordinary send back above the carrier/pre-flight block -> test B
  sees two sends (ordinary + failure) -> RED.
- M2: delete the pre-flight raise -> test B sees one ORDINARY send -> RED on
  the title assertion.
- M3: drop the HALT-context prefix -> test B2 RED.
- M4: remove the restore-list token -> hygiene test RED.
- M5: replace `admit_session` with `date_str` -> test G RED.
- M6: hoist `run_at_utc` above the send -> an admissible system-halted run's
  summary/contract timestamp equality assertion (added to test E) RED.

## 10. NOTIFICATION OWNERSHIP

- Within a run: one send on every path -- ordinary (:711) XOR failure (:928).
  Pinned today by `test_hourly_sends_exactly_once_{stay_flat,system_halted,
  on_exception}`; the refusal path rides the on_exception branch.
- Workflow layer: `hourly_alert.yml` has no failure notifier, so no
  double-send from the workflow is possible. The daily FAIL_OWNED /
  DELIVERY_FAILED sentinels (:266-317) are not on this path.
- Across dispatches of the same refused slot: bounded to one failure
  notification per dispatch (Ruling 2). `last_hourly_slot.json` is written
  only on `alert_sent` and cannot be published on refusal; no new state
  channel is introduced.
- Telegram failure while notifying the refusal: `send_notification` returns
  False (or raises, caught at :931-933); status FAIL regardless; workflow RED;
  artifacts uploaded; `output.py` keeps its single bounded 429/5xx retry.

## 11. ROLLBACK

Revert the runtime hunk (send returns to the :711 order, pre-flight and
exception class removed) and the workflow changes (restore token, frozen
session step); delete the conftest fixture and the new tests. No persisted
schema or authority change to unwind.

## 12. EVIDENCE INDEX

- Incident: GitHub runs 34972228502 (OPEN), 34975381741 and the eight
  later hourly dispatches on 2026-09-15 (through 35017065416), six schedule
  runs; `origin/publish` history around 47fff037 / bcced276.
- Ordering and seam: `cuttingboard/runtime/__init__.py` :540-972 (send :711,
  clock :715, carrier :755-764, except :919-972, halt_reason :593-599,
  KILL_SWITCH_HALT_REASON :3087), :1241-1257; `cuttingboard/effective_permission.py` :91-98, :189-238,
  :282-341; `cuttingboard/authority_projection.py` :112-142, :267-271;
  `tools/ci_push_artifacts.sh` :30-110; `.github/workflows/hourly_alert.yml`
  :96-277; `cuttingboard/alert_runner.py` :150-211;
  `cuttingboard/notifications/hourly_slot.py` :151-165;
  `cuttingboard/notifications/__init__.py` :623.
- Test surface: `tests/test_hourly_alert.py` :991-1110 (exactly-once trio);
  `tests/conftest.py` :160-172; `tests/test_effective_permission.py`;
  `tests/test_publish_authority_nonregression.py`.
- Sibling audit (context only, not authority): the 2026-09-17 backend
  maintenance audit (owner-held, not committed).

## 13. GOV-2 CYCLE RECORD

- EVENT 1 review (Sol, job codex-20260918T010936Z-0bd0, at packet head
  6505e2a3): ACCEPT WITH CHANGES -- `CODEX_EVENT_1_REVIEW_2026-09-17.md`.
- Author verification before correcting: REQ-1 nine dispatch + six schedule
  runs CONFIRMED via `gh run list`; REQ-2 `PUBLISH_SESSION` derivation
  CONFIRMED at ci_push_artifacts.sh:40 and run_date at alert_runner.py:198-202;
  REQ-3 `run_at_utc` after the send CONFIRMED at :715; REQ-4 halt_reason at
  :597 and constant at :3087 CONFIRMED; REQ-5 suppression lives in
  alert_runner CONFIRMED (:172-191); test-call count 47 in 9 files CONFIRMED.
- Consolidated correction (this revision): REQ-1 ACTIONED (sec 1 counts and
  UNVERIFIED/INFERRED labels); REQ-2 ACTIONED (D3 frozen `CB_WORKFLOW_SESSION`,
  test G, M5, FILES); REQ-3 ACTIONED (D2 keeps the artifact clock; D6 narrowed;
  M6); REQ-4 ACTIONED (D4 exact `validation_summary.halt_reason` source and
  composed reason); REQ-5 ACTIONED (test D through the alert_runner slot
  harness; FILES). REC-1 ACTIONED (citations refreshed); REC-2 ACTIONED
  (named module-scoped fixture; count corrected); REC-3 ACTIONED (test A
  seeds an accepted tip); REC-4 ACTIONED (D5 two residual classes).
- EVENT 2 exact-corrected-head confirmation: pending.
- Helm design-direction ruling from the review-clean packet: pending.
