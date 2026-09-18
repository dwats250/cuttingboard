# Hourly authority-admission / notification truth -- MATERIAL design packet

```
STATUS: PROVISIONAL MATERIAL PACKET -- 2026-09-17 -- DESIGN ONLY
CLASS: HIGH-RISK. MATERIALITY: MATERIAL (owner ruling 3, recorded below).
AUTHORIZES NO IMPLEMENTATION, NO PRD, NO GATE A, NO MERGE.
GOV-2 PACKET-REVIEW CYCLE: EVENT 1 (Sol/Codex, fresh context) PENDING.
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
- Fifteen hourly `workflow_dispatch` runs (13:30Z .. 20:01Z; first is
  34975381741): every step through "Commit hourly artifacts" SUCCEEDED,
  including the ordinary Telegram send; "Push hourly artifacts" FAILED with
  `artifact publish: authority non-regression REFUSED (R5) on
  logs/latest_hourly_contract.json` then `hard error on attempt 1 - aborting`.
  Log excerpt (run 34975381741):
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
  2026-09-15. Pages served the 09-14 board all day.
- Six `schedule` (liveness) arrivals on 09-15 concluded `failure` (RED),
  correctly. No hourly failure Telegram exists in `hourly_alert.yml`, so the
  operator received fifteen normal-looking alerts and no failure notice.
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
| 3 | Alert formatted from `operator_locked` + qualification. The hourly Telegram body does NOT read the EffectivePermission projection (output.py:346 `project()` is the daily `build_notification_message` path). | runtime :690-694 |
| 4 | ORDINARY TELEGRAM SEND when `mode == MODE_LIVE`; `alert_sent` captured. | runtime :696-698 |
| 5 | Hourly contract + summary built with `alert_sent` baked in. | runtime :702-748 |
| 6 | EffectivePermission carrier: `_load_accepted_authority(run_date, run_at_utc)` reads latest_run.json then latest_contract.json through `admit_persisted` (:1241-1257); `carry_forward(...)` if admitted else `ep_authority.unavailable(...)`; `persist()` onto contract + summary; `_write_hourly_artifacts`. | runtime :756-764 |
| 7 | Market map; `save_last_slot(slot_utc)` ONLY IF `alert_sent`; sidecars; return `{"status": SUCCESS}`. | runtime :798-802, :912 |
| 8 | Workflow: freshcheck (payload mtime) -> aggregate -> render -> `check_readiness.py` -> commit (explicit allowlist incl. latest_hourly_contract.json). All `if: success()`. | hourly_alert.yml:174-271 |
| 9 | Push: `tools/ci_push_artifacts.sh::authority_guard` runs (a) `effective_permission.py publication-admits <origin/publish tip carrier> <incoming>` (R5) and (b) `authority_projection.py admit <incoming> <runner UTC date>` (Slice-2 read boundary; `now=None`). Refusal = exit 1 = job RED, no publish. | ci_push_artifacts.sh:70-110 |
| 10 | `pages.yml` deploys `origin/publish` on `workflow_run` completion (branch simply did not move). | pages.yml |
| 11 | Liveness probe reads `origin/publish:logs/last_hourly_slot.json`. | scripts/check_hourly_liveness.py |

The exception branch (:914-970) already: formats
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

D2. Hoist the carrier. In `_execute_notify_run`, the block now at :756-761
(`_acc` / `_hourly_ep`) moves to immediately BEFORE the ordinary send (:696).
`run_at_utc` is computed there with the identical expression from :703
(`regime.computed_at_utc if regime is not None else datetime.now(timezone.utc)`)
and reused unchanged downstream; the later block at :756-761 is deleted, the
`persist()` calls at :762-763 stay where they are.

D3. In-process canonical pre-flight. Immediately after `_hourly_ep` exists,
and only when `mode == MODE_LIVE and notify_mode in _HOURLY_MODES`:

```
accepted = ep_authority._read_authority(str(LATEST_HOURLY_CONTRACT_PATH))
incoming = _hourly_ep.to_envelope()
admissible = (
    ep_authority.publication_admits(accepted, incoming)
    and ep_authority.admit_persisted(
        incoming, current_session_date=date_str, now=None) is not None
)
if not admissible:
    raise HourlyPublicationInadmissible(<message per D4>)
```

`now=None` mirrors the Slice-2 CLI exactly. `date_str` is
`run_date.isoformat()`, the same `now(UTC).date()` the runner-side
`PUBLISH_SESSION` uses. The pre-flight is the publisher's two calls with the
same inputs (accepted = restored publish tip, incoming = the envelope that
will be persisted). It authors nothing.

D4. Refusal enters the EXISTING failure branch. `HourlyPublicationInadmissible`
is a small module-level `Exception` subclass in `runtime/__init__.py`. Its
message is <= 120 chars because `format_failure_notification` truncates the
reason (:929 `str(exc)[:120]`) and must state that the hourly board update
was REFUSED / NOT PUBLISHED (R5). Per Ruling 1, when `hourly_kill_switch` is
true the message is prefixed with the bounded market-stress HALT context
already available at that point (the kill-switch reason line the ordinary
HALT alert would have carried), so the single failure notification preserves
the HALT observation. The except branch then (unchanged): one failure send,
`traceback.txt`, error contract with `OUTCOME_HALT`, FAIL summary via
`_write_hourly_artifacts`, return FAIL. `alert_runner` exits 1; every later
workflow step is `if: success()` so publish count is 0; "Upload failure
artifacts" (`if: failure()`) retains `latest_hourly_*.json` and
`traceback.txt`; `save_last_slot` never runs, so liveness can still go RED.

D5. Publisher untouched. `tools/ci_push_artifacts.sh` remains the
publication authority. Residual: the publish tip can move between restore and
push; the publisher then refuses and the job is RED without a Telegram (the
existing accepted-residual class; a daily-parity hourly failure notifier is a
separate candidate from the 2026-09-17 audit and is OUT OF SCOPE here).

D6. Unchanged for admissible runs: alert wording, send count (one), contract
and summary content, `save_last_slot`, sidecars, publish, Pages. A
market-stress HALT hourly on an admissible day is unaffected (`carry_forward`
raises rank; R5 admits a rank raise).

## 7. FILES (ESTIMATED SURFACE -- NOT YET APPROVED; Gate A sets the ceiling)

Production:
- `cuttingboard/runtime/__init__.py` (hoist ~8 lines; pre-flight ~15 lines;
  exception class ~3 lines; HALT-context prefix ~3 lines)
- `.github/workflows/hourly_alert.yml` (1 token in the restore list)

Tests:
- `tests/test_hourly_alert.py` (tests A-E below)
- `tests/conftest.py` (autouse admitted-carrier seeding, see sec 9)
- `tests/test_ci_artifact_hygiene.py` (pin the restore-list token)

Reference only, unchanged: `tools/ci_push_artifacts.sh`,
`cuttingboard/effective_permission.py`, `cuttingboard/authority_projection.py`,
`cuttingboard/alert_runner.py`, `.github/workflows/cuttingboard.yml`.

ESTIMATED PROD LOC: 25-40 (runtime) + 1 (workflow).
ESTIMATED TEST LOC: 180-260.

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

Test-ripple (the real cost): ~46 `_execute_notify_run` call sites across 14
test files (24 in `tests/test_hourly_alert.py`) run with NO accepted carrier;
today their EP is UNAVAILABLE and they expect the ordinary send. Under D3 they
would all flip to the failure path. Mitigation: a `tests/conftest.py` autouse
fixture (same pattern as the existing `_fetch_intraday_card_bars` autouse at
:160-172) monkeypatches `cuttingboard.runtime._load_accepted_authority` to
return a same-day admitted EP, with no accepted-tip file present (bootstrap
admits). Tests B and D override it to `None`.

- A. `test_hourly_admissible_carrier_sends_ordinary_once`: admitted accepted
  carrier -> exactly one send, ordinary title, status SUCCESS,
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
- D. `test_hourly_refused_slot_redispatch_bounded` (Ruling 2): run the same
  refused slot twice -> two failure sends total, zero ordinary; second run is
  not `suppressed_same_slot` (documents bounded per-dispatch behavior).
- E. Existing `test_hourly_sends_exactly_once_system_halted` and
  `_stay_flat` stay green under the autouse fixture (admissible HALT/flat).
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

## 10. NOTIFICATION OWNERSHIP

- Within a run: one send on every path -- ordinary (:698) XOR failure (:929).
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

Revert the runtime hunk (send returns to the :696 order, pre-flight and
exception class removed) and the one-token workflow change; delete the
conftest fixture and the new tests. No persisted schema or authority change
to unwind.

## 12. EVIDENCE INDEX

- Incident: GitHub runs 34972228502 (OPEN), 34975381741 and the fourteen
  later hourly dispatches on 2026-09-15; `origin/publish` history around
  47fff037 / bcced276.
- Ordering and seam: `cuttingboard/runtime/__init__.py` :540-972,
  :1241-1257; `cuttingboard/effective_permission.py` :91-98, :189-238,
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

- EVENT 1 review: `CODEX_EVENT_1_REVIEW_2026-09-17.md` (pending).
- Consolidated correction: pending.
- EVENT 2 exact-corrected-head confirmation: pending.
- Helm design-direction ruling from the review-clean packet: pending.
