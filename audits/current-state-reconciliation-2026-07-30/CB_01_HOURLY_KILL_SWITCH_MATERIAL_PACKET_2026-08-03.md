# CB-01 — Hourly Kill-Switch Bypass: GOV-2 MATERIAL Remediation Packet

```
STATUS: PROVISIONAL MATERIAL PACKET
AUTHORIZES NO IMPLEMENTATION
```

**Governing order:** `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` §§1–4, §7.
**Materiality trigger:** GOV-2 §1 — "it resolves a Critical or High finding." CB-01 is
recorded `OPEN` / **Critical** in
`audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md`.
**Upstream authority:** DR-001 ruling, Dustin, 2026-08-03 —
`audits/north-star-deep-audit-2026-08/95_POST_RATIFICATION_RULINGS.md` lines 17–104.
**Sequencing constraint (DR-001):** this fix must merge before CB-02 reaches
implementation Gate A.
**Charge boundary:** this packet answers exactly one question (below). It does not
open a Stage-0 PRD, does not allocate PRD-278, does not update the PRD registry,
does not implement code, and does not make Dustin's design-direction ruling.
**Formatting precedent:** `OPT_0_SMALLEST_CONTRACT_REFUSAL_SEAM_TRACE_2026-07-31.md`
(branch `origin/worktree-opt-0-seam-trace`; not yet review-clean) — used for section
shape only, not as ruled authority.

---

## 1. Problem statement

**Packet question:** What is the smallest safe correction that prevents the hourly
alert path from bypassing and falsely reporting the existing kill-switch state?

The daily pipeline evaluates the existing market-stress kill switch and, on a trip,
escalates the run to a full halt before any candidate is qualified or presented. The
hourly alert path runs the same fetch → regime → candidate → qualify sequence but
never evaluates the kill switch, and its published summary hardcodes
`"kill_switch": False` regardless of actual market conditions. During a VIX/SPY
stress condition that would halt the daily pipeline, the hourly channel keeps
qualifying and presenting candidates as tradable, and its own published summary
affirmatively (and falsely) reports the safety indicator as clear.

## 2. Current behavior — exact code references (verified against `main` @
`e6a5ce69e8fba18c3e5147bc5ceac3aebddc13c3`, `cuttingboard/runtime/__init__.py`)

**The evaluator (reused, not touched):**
- `_kill_switch(regime, normalized_quotes)` — defined `:2194-2203`. Pure predicate:
  VIX level > 35, or VIX % change > 0.15, or `|SPY % change|` > 0.03.

**Daily path (in scope for reuse of its pattern; the daily path's own code is
untouched by this remediation):**
- `_run_pipeline`, `:937` — `elif _kill_switch(regime, normalized_quotes):` — on
  trip, escalates by rebuilding `validation_summary` via `dataclasses.replace(...,
  system_halted=True, halt_reason=KILL_SWITCH_HALT_REASON,
  halt_cause=HaltCause.MARKET_STRESS)` (`:946-951`), setting `outcome = OUTCOME_HALT`
  (`:952`), and skipping the entire qualification/candidate/decision block (the
  `else:` at `:953` that would otherwise run correlation → derived → structure →
  candidates → qualify).
- `_build_run_summary`, `:1256-1259` — independently re-evaluates
  `_kill_switch(regime, normalized_quotes)` and reports the real value; when tripped,
  additionally zeroes `validated_count`.

**Hourly path (the defect):**
- `_execute_notify_run`, `:356-619` — the "lightweight path for non-premarket notify
  modes," used by `NOTIFY_HOURLY` (`_HOURLY_MODES`, `runtime/_constants.py:35`) among
  others.
  - `:391` — `if not validation_summary.system_halted:` is the ONLY gate before
    candidate generation. `system_halted` here reflects data-validation failures
    only (missing/invalid quotes); it has no relationship to `_kill_switch`.
  - `:392` — `regime = compute_regime(...)` is computed, but `_kill_switch` is never
    called anywhere in this function.
  - `:426-462` — `elif notify_mode in _HOURLY_MODES and regime.posture !=
    "STAY_FLAT":` generates candidates (`generate_candidates`), qualifies them
    (`qualify_all`), and builds `candidate_lines` for the Telegram alert — all
    unconditional on any market-stress evaluation.
  - `:497-568` — when `notify_mode in _HOURLY_MODES`, the contract and summary are
    built and hourly-specific artifacts (report, contract, market map, watchlist,
    trend snapshot) are written from that same ungated candidate state.
- `_build_hourly_run_summary`, defined `:1903-1993` — the hourly summary builder.
  - `:1975` — `"kill_switch": False,` is a hardcoded literal. It is not derived from
    `regime`, `normalized_quotes`, or any evaluation. This single function backs
    BOTH call sites below, so both inherit the same falsification.
  - Success call site: `_execute_notify_run:512-532`, inside the `try` block, after
    candidate generation/qualification has already run ungated.
  - Failure call site: `_execute_notify_run:598-617`, inside the `except Exception`
    handler. Here `regime=None`, `validation_summary=None`,
    `normalized_quotes={}` are passed (`:603-604, 616`) — the function never had
    the information to evaluate the kill switch even if asked, yet still asserts
    `False` (clear) rather than leaving the state honestly unknown.
- A third hardcode exists at `_failure_summary:2366` (defined `:2335`), but its only
  call site is `execute_run`'s daily exception handler (`:296`) — **out of scope**,
  per DR-001 ("existing daily behavior remains unchanged") and per the Confirmed
  Problem's own framing (this packet addresses the hourly path only).

**Boundary observation, not investigated further (explicitly out of scope, no
adjacent-defect search performed):** the same `if not validation_summary.system_halted:`
gate at `:391` also precedes `_QUALIFY_ONLY_MODES` (`post_orb`, `power_hour`,
`market_close`; `:403-424`), which share the ungated candidate-generation shape.
Those modes do not call `_build_hourly_run_summary` and are not part of CB-01's
recorded claim in `FINDING_STATUS_MATRIX.md`, which names only the hourly channel.
Noted here only because it was visible in the code already read for this packet's
required scope, per the "read only the minimum relevant" charge boundary; not
characterized, sized, or rated, and not a design input below. If Dustin wants it
assessed, that is a separate materiality check, not part of this packet's question.

## 3. Safety consequence

On an intraday VIX/SPY stress condition that would HALT the daily pipeline:
- The hourly channel still runs fetch → regime → candidate → qualify.
- It still sends a Telegram alert with qualified candidate R:R lines.
- Its own published `latest_hourly_run.json` summary states `"kill_switch": false`,
  affirmatively certifying the safety indicator as clear on the very run where it
  is not.
- Any consumer of that summary (dashboard render, downstream tooling) inherits the
  false certification, not just a missing one.

`VISION.md:30-34` treats extreme market stress as a hard invalidation. It is
currently enforced on one of the two live channels only.

## 4. Bounded design options

### Option A — Evaluate before qualification, carry the result through the summary

Evaluate `_kill_switch(regime, normalized_quotes)` once regime is available in the
hourly branch of `_execute_notify_run`, before candidate generation/qualification
runs. On a trip, escalate exactly as the daily path does (mark the validation state
halted with `KILL_SWITCH_HALT_REASON` / `HaltCause.MARKET_STRESS`) and skip
candidate generation for that run. Thread the evaluated boolean into
`_build_hourly_run_summary` in place of the hardcoded literal, for both call sites.

### Option B — Evaluate only during hourly summary construction

Leave candidate generation/qualification in `_execute_notify_run` untouched; call
`_kill_switch` only inside `_build_hourly_run_summary` (or immediately before it) to
compute the reported field, without gating anything upstream.

### Option C — Smaller alternative

Not reached. No direct code evidence found in `runtime/__init__.py` shows that
Option A cannot preserve the established safety contract (§5) at the file boundary
already required by Options A/B. Option C is therefore not evaluated further.

## 5. Required safety contract (from the charge; restated for evaluation)

1. Hourly evaluates the same existing kill-switch semantics as daily.
2. A triggered state cannot be reported as clear.
3. A triggered state cannot produce or present candidates as tradable when the
   daily contract would halt.
4. Clear-state hourly behavior unchanged.
5. Hourly failure handling does not falsely assert a clear state.
6. Daily behavior unchanged.
7. No new kill-switch model.
8. No persisted schema introduced.
9. No dashboard/notification/unrelated runtime redesign.
10. Smallest proven file boundary.

## 6. Why rejected options fail the contract

**Option B fails contract items 2 and 3.** Reporting the correct boolean while
candidate generation and qualification remain ungated changes only what the summary
*says*, not what the system *does*. A tripped condition would still generate,
qualify, and send Telegram candidate lines with R:R math — the hourly channel would
now honestly report "kill switch: true" in the same JSON file that lists tradable
candidates it should not have produced. The charge is explicit that this shape is
rejected: "Reject any option that merely changes the reported Boolean while still
allowing halted candidates to be presented as tradable." Option B is exactly that
shape.

**Option A satisfies the full contract.** Gating candidate generation on the same
evaluator the daily path already uses, before qualification runs, satisfies items
1–3 directly (nothing to qualify or present once gated); reuses
`_kill_switch`/`KILL_SWITCH_HALT_REASON`/`HaltCause.MARKET_STRESS` verbatim, so item
7 holds; threading a boolean through an existing function signature adds no schema
(item 8); touches no dashboard, notification formatter, or unrelated module (item
9); and the clear-state branch (posture-gated candidate generation) is untouched
when the switch is not tripped, so item 4 holds. Item 5 (failure handling) is not
automatically resolved by Option A's control-flow change alone — see §12 open
questions.

**Option C** — not evaluated; no evidence forces a smaller boundary than A/B, and
A already meets the contract at the smallest observed control-flow cost (one
evaluation call, reused escalation pattern, one threaded parameter).

## 7. Recommended design (Option A)

Reuse the daily path's own pattern, scoped to the hourly branch only:

1. In `_execute_notify_run`, after `regime = compute_regime(...)` (`:392`) and while
   still inside `if not validation_summary.system_halted:`, evaluate the kill switch
   only for the hourly mode:
   `hourly_kill_switch = notify_mode in _HOURLY_MODES and _kill_switch(regime,
   normalized_quotes)`, initialized `False` before the `try` block so it is always
   defined at both summary call sites.
2. On trip, escalate `validation_summary` the same way the daily path does —
   `dataclasses.replace(validation_summary, system_halted=True,
   halt_reason=KILL_SWITCH_HALT_REASON, halt_cause=HaltCause.MARKET_STRESS)` — so
   downstream fields that already derive from `validation_summary.system_halted` /
   `halt_reason` in `_build_hourly_run_summary` (permission text `:1976-1980`,
   `system_halted` `:1982`, `halt_reason` `:1983`) update themselves with no
   additional field-by-field change.
3. Add `and not hourly_kill_switch` to the existing `elif notify_mode in
   _HOURLY_MODES and regime.posture != "STAY_FLAT":` guard (`:426`) so candidate
   generation/qualification is skipped on a trip — mirroring the daily path's skip
   of its qualification block on halt.
4. Add a `kill_switch: bool` parameter to `_build_hourly_run_summary` and replace
   the hardcoded `"kill_switch": False,` literal (`:1975`) with that parameter. Pass
   `kill_switch=hourly_kill_switch` at the success call site (`:512-532`).
5. At the failure/exception call site (`:598-617`), pass an explicit value rather
   than reusing whatever `hourly_kill_switch` held before the exception — see §12
   Q1 for the exact value, which is a Dustin decision, not one this packet makes.

This is the pattern already ruled sound for the daily path (PRD-180); nothing new is
designed, only the same evaluator and escalation reused at a second call site that
was missing it.

## 8. Before/after control flow

**Before** (`_execute_notify_run`, `NOTIFY_HOURLY`):

```
fetch/normalize/validate quotes
if not validation_summary.system_halted:
    regime = compute_regime(...)
    derived, router_state computed
    if notify_mode in _HOURLY_MODES and regime.posture != STAY_FLAT:
        generate_candidates -> qualify_all -> candidate_lines   # UNGATED
format_hourly_notification(...)
send_notification(...)
build_hourly_contract(...)
_build_hourly_run_summary(...)  # kill_switch hardcoded False
write hourly artifacts
```

**After** (Option A):

```
fetch/normalize/validate quotes
if not validation_summary.system_halted:
    regime = compute_regime(...)
    hourly_kill_switch = (notify_mode in _HOURLY_MODES) and _kill_switch(regime, normalized_quotes)
    if hourly_kill_switch:
        validation_summary = replace(validation_summary, system_halted=True,
                                      halt_reason=KILL_SWITCH_HALT_REASON,
                                      halt_cause=HaltCause.MARKET_STRESS)
    derived, router_state computed                              # unchanged
    if notify_mode in _HOURLY_MODES and not hourly_kill_switch and regime.posture != STAY_FLAT:
        generate_candidates -> qualify_all -> candidate_lines   # GATED
format_hourly_notification(...)   # halt_reason now reflects the trip automatically
send_notification(...)
build_hourly_contract(...)
_build_hourly_run_summary(..., kill_switch=hourly_kill_switch)   # real value
write hourly artifacts
```

Exception path: `hourly_kill_switch` is defined (default `False`) before the `try`
block; the failure-path `_build_hourly_run_summary` call passes an explicit,
Dustin-ruled value rather than an uninitialized or stale one (§12 Q1).

## 9. Exact proposed file boundary

```
ESTIMATED SURFACE — NOT YET APPROVED
```

- `M  cuttingboard/runtime/__init__.py` — the changes in §7/§8: one evaluation call,
  one conditional escalation reusing existing constants/dataclasses, one guard
  clause edit, one new parameter on `_build_hourly_run_summary`, two call-site
  argument additions.
- `M  tests/test_hourly_alert.py` — the smallest existing test file that already
  exercises `_execute_notify_run` for `NOTIFY_HOURLY` (`test_hourly_run_writes_
  hourly_specific_artifacts`, `test_hourly_sends_exactly_once_system_halted`,
  `test_hourly_writes_traceback_on_exception`, `test_notification_sent_derived_
  strictly_from_status` calling `_build_hourly_run_summary` directly) — the natural
  home for the new discriminating tests (§13).

No other file is touched by direct call-chain dependency:
- `verify_run_summary` (`runtime/__init__.py:1499-1597`) is CLI-mode-gated to
  `live`/`sunday` daily verification only (`docs/audit/gate_recon_2026-06-12.md`
  line 602: "verify_run_summary only after live/sunday; intraday modes never
  verify"); it is not a consumer of the hourly summary and needs no change.
- `contract.py` has no `kill_switch` handling; the hourly contract
  (`_build_hourly_contract`, `:1847-1901`) already derives its `contract_status`
  from `validation_summary.system_halted` via `derive_run_status`, which the
  escalation in §7 step 2 already updates for free.
- No dashboard, notification-formatter, or persistence-schema file is touched
  (contract item 9).

## 10. Explicit non-goals

- No change to the daily pipeline (`_run_pipeline`, `_build_run_summary`,
  `execute_run`, `_failure_summary`).
- No change to `_QUALIFY_ONLY_MODES` (`post_orb`, `power_hour`, `market_close`) —
  the §2 boundary observation is not acted on here.
- No new kill-switch thresholds, evaluator, or model — `_kill_switch` and its
  constants are reused verbatim.
- No new persisted field beyond correcting the existing `kill_switch` value that
  `latest_hourly_run.json` already carries.
- No dashboard rendering change, notification formatter change, or Telegram
  message-shape change.
- No PRD drafting, no Stage-0 scaffold, no registry update, no implementation.
  This packet is documentation only.

## 11. Risks

- **Failure-path semantics (see §12 Q1) is a genuine judgment call, not a
  mechanical default.** Whatever this packet's author sets without a ruling would
  be exactly the kind of unruled design decision GOV-2 exists to catch — flagged
  as an open question rather than decided here.
- **Downstream rendering of the corrected value is unverified.** This packet does
  not inspect the dashboard renderer or notification formatter (explicit non-goal);
  if either currently assumes `kill_switch` is always `false` on the hourly
  surface, a previously-dormant rendering path could activate for the first time.
  Recommend the eventual PRD's downstream-consumer audit (per `CLAUDE.md` Author
  disciplines) explicitly check `ui/` and `notifications/` renderers before Gate A,
  even though this packet does not touch them.
- **`derived`/`router_state`/`structure` continue to compute even when the switch
  trips**, since the recommended design only gates candidate generation, not the
  whole `if not validation_summary.system_halted:` block (unlike the daily path,
  which skips everything past the trip). This is deliberate — minimal-diff, and
  those values are not presented as tradable — but it means the hourly and daily
  paths are not byte-for-byte identical in what they skip on a trip, only in what
  they report and what they qualify.

## 12. Rollback approach

The change is a pure control-flow addition plus one new function parameter with a
default derivable from existing state — no schema migration, no data backfill, no
config flag. Rollback is a plain revert of the single commit/PR touching
`cuttingboard/runtime/__init__.py` and `tests/test_hourly_alert.py`; no downstream
artifact format changes survive a revert, since `kill_switch` is an existing field
whose value changes, not a new field.

## 13. Focused test plan (home: `tests/test_hourly_alert.py`)

Discriminating additions (each must fail if the corresponding fix line is reverted
to the current hardcoded/ungated behavior — mutation-red per `CLAUDE.md`
semantic-failure hardening invariant 4):

1. **Trip halts and reports true.** Monkeypatch `compute_regime`/quotes to produce a
   VIX/SPY reading that trips `_kill_switch` (mirror the fixture shape already used
   in `tests/test_runtime_decision.py::test_kill_switch_threshold_boundaries` /
   `test_kill_switch_predicate_strict_greater_than`, applied through
   `_execute_notify_run(notify_mode=NOTIFY_HOURLY)`). Assert
   `latest_hourly_run.json` has `kill_switch: true`, `system_halted: true`,
   `halt_reason` equal to `KILL_SWITCH_HALT_REASON`, `candidates_qualified == 0`,
   and `candidate_lines == []`. Red against current code: the field is hardcoded
   `False` and candidates are ungated.
2. **Trip suppresses candidate generation, not just the reported field.** Same
   fixture as (1); assert `generate_candidates`/`qualify_all` were not invoked (spy
   or monkeypatch to raise if called) — this is the test that specifically
   discriminates Option A from Option B (§6): reverting only the summary literal
   while leaving qualification ungated must fail this assertion.
3. **Clear state unchanged.** Existing tests that already exercise a non-tripped
   hourly run with qualified candidates (e.g.
   `test_hourly_candidate_line_uses_promoted_geometry_prd260_r7`) must continue to
   pass unmodified — cited as regression evidence for contract item 4, not
   rewritten.
4. **Direct summary-builder unit test.** Mirror
   `test_notification_sent_derived_strictly_from_status`'s pattern of calling
   `_build_hourly_run_summary` directly with `kill_switch=True` and
   `kill_switch=False`; assert the field passes through verbatim in both
   directions. Proves the parameter threading independent of the control-flow
   gating.
5. **Failure path.** Extend `test_hourly_sends_exactly_once_on_exception` /
   `test_hourly_writes_traceback_on_exception`'s fixture to assert the ruled value
   from §12 Q1 on the failure summary's `kill_switch` field — written once Dustin's
   ruling fixes the expected value.
6. **Daily unchanged (regression only, no new test).** Existing
   `tests/test_runtime_decision.py::test_kill_switch_trip_forces_full_halt_escalation`,
   `test_kill_switch_trip_skips_pipeline`,
   `test_validation_halt_unchanged_when_kill_switch_not_tripped`, and
   `test_kill_switch_audit_record_carries_halt` continue to pass unmodified —
   evidence for contract item 6.

## 14. Acceptance contract

The implementation is acceptable only if, on the exact file boundary in §9:

- Every item in §5's ten-point safety contract holds, verified by the tests in
  §13.
- `_kill_switch`, `KILL_SWITCH_HALT_REASON`, and `HaltCause.MARKET_STRESS` are the
  only kill-switch-related symbols referenced; no new evaluator or threshold is
  added.
- `latest_hourly_run.json`'s `kill_switch` field is derived, not literal, at both
  call sites of `_build_hourly_run_summary`.
- No file outside §9's two-file boundary is modified.
- Full existing suite remains green, including every test named in §13 items 3 and
  6 as unmodified regression evidence.

## 15. Open questions requiring Dustin's design-direction ruling

**Q1 — Failure-path `kill_switch` value.** When `_execute_notify_run` raises before
or during kill-switch evaluation (`regime`/`normalized_quotes` unavailable), what
should the failure-path `_build_hourly_run_summary` call report for `kill_switch`?
Two candidates, both contract-compliant on item 5 ("does not falsely assert a clear
state") but with different implications:
  - **(a) Report `True`** — fail-safe: treat "unknown" as "assume tripped," matching
    the RECOMMENDATION BOUNDARY's stated preference for fail-safe behavior and
    PRD-198 invariant 1 (fail-loud, never silent-fallback). Risk: a viewer reading
    `kill_switch: true` literally may infer market stress was actually detected,
    when the true condition is "run failed before evaluation was possible." Note
    that `system_halted`/`status: FAIL`/`outcome: HALT` already correctly signal
    "no trades" on this path regardless of the `kill_switch` literal — this is a
    labeling question, not a candidate-suppression question (contract item 3 is
    already satisfied on the failure path independent of Q1's answer, since
    `qualification_summary=None` there in all cases).
  - **(b) Leave `False`, matching the daily `_failure_summary`'s explicitly
    out-of-scope precedent** — consistent with "existing daily behavior remains
    unchanged" read as a stylistic precedent for failure summaries generally, but
    arguably still "falsely asserts a clear state" per contract item 5's literal
    text, since it is indistinguishable in the JSON from a genuinely evaluated
    clear reading.
  This packet does not choose between (a) and (b); it is Dustin's design-direction
  ruling to make. Recommendation, per the RECOMMENDATION BOUNDARY's own stated
  preference for fail-safe behavior: (a).

**Q2 — `derived`/`router_state`/`structure` computation on a trip.** §11 already
flags that the recommended design continues computing these on a hourly trip
(unlike the daily path, which skips them entirely). Is this asymmetry acceptable,
or should the hourly trip mirror the daily path's full early-exit for tighter
parity at the cost of a larger diff? Recommendation: acceptable as designed — these
values are not presented as tradable and are already defaulted to empty structures
elsewhere in the same function; forcing full parity would grow the diff without a
corresponding safety gain.

**Q3 — Boundary observation on `_QUALIFY_ONLY_MODES`.** §2's boundary observation
(the same pre-branch gate also precedes `post_orb`/`power_hour`/`market_close`) is
not sized, rated, or acted on by this packet. Does Dustin want a separate
materiality check opened for that surface, independent of and not blocking CB-01?
Recommendation: defer; CB-01's own DR-001 sequencing constraint (must merge before
CB-02 Gate A) already sets urgency on the narrower fix, and expanding this packet's
claim would itself trigger GOV-2's boundary-reset rule (§6) for scope not yet
verified.

---

_Packet author: Claude Code, fresh-context recon session, 2026-08-03. Reviewed
against `main` @ `e6a5ce69e8fba18c3e5147bc5ceac3aebddc13c3`. This packet is
provisional per GOV-2 §2 until independent Codex review, one consolidated
correction if required, and independent exact-corrected-head confirmation have
landed. It authorizes no implementation, no PRD drafting, and no design-direction
ruling._
