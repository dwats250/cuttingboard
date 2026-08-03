# CB-01 kill-switch remediation — upstream GOV-2 MATERIAL packet

STATUS: PROVISIONAL — independent Codex packet review (GOV-2 §2 step 3)
complete against commit `6994d146958c9bfd8bfe1dd02b14f4a200b68589`; one
consolidated correction applied (step 4, below). Awaiting independent
exact-corrected-head confirmation (GOV-2 §2 step 5) against this corrected
commit. Not review-clean until that confirmation lands. Grants no
implementation authority (GOV-2 §4).

Author: Claude Code, self-verified per GOV-2 §3 (code-path reads, call-site
greps, existing-test inventory below, and the baseline test run recorded in
§10). This packet is NOT independent review.

**Correction pass (2026-08-03), addressing the independent Codex packet
review of commit `6994d146958c9bfd8bfe1dd02b14f4a200b68589`:** seven
findings, all confirmed against current code and applied in one consolidated
pass — see §2 (propagation gap), §4/§5 (hourly-only guard; status/outcome/
return propagation, scoped to the kill-switch halt cause only), §7
(provisional-ceiling label; PRD-278 naming conflict), §9 (atomic rollback),
§10 (corrected formatter test citation; baseline test run). No finding
required expanding this packet's file boundary or reopening design options
A/B/C.

MATERIAL trigger: GOV-2 §1 — "it resolves a Critical or High finding." CB-01
is recorded at Critical severity in
`audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md`.

Runway authority: `audits/north-star-deep-audit-2026-08/95_POST_RATIFICATION_RULINGS.md`
DR-001 (Dustin, 2026-08-03) — CB-01 must merge before CB-02 reaches
implementation Gate A; deferral is not authorized.

---

## 1. Problem statement

The packet answers exactly one question: **what is the smallest safe
correction that prevents the hourly alert path from bypassing and falsely
reporting the existing kill-switch state?**

The hourly notification path (`_execute_notify_run`) generates, qualifies,
and publishes trade candidates to Telegram without ever evaluating market-
stress conditions, and its published run summary hardcodes
`"kill_switch": False` regardless of actual market state. The daily path
(`_run_pipeline`) already evaluates the same conditions and halts before
generating any candidates when they trip.

## 2. Current behavior — exact code references

All references are against `cuttingboard/runtime/__init__.py` at `main`
`e6a5ce69e8fba18c3e5147bc5ceac3aebddc13c3` (merge of PR #192).

**The evaluator (unchanged, reused as-is):**
```
2185  KILL_SWITCH_VIX_LEVEL = 35
2186  KILL_SWITCH_VIX_PCT_CHANGE = 0.15
2187  KILL_SWITCH_SPY_PCT_CHANGE = 0.03
2191  KILL_SWITCH_HALT_REASON = "Market-stress kill switch tripped; new positions halted."
2194  def _kill_switch(regime, normalized_quotes) -> bool: ...
```
`_kill_switch` has exactly two call sites in the whole file, both inside
`_run_pipeline` (the **daily** path):

- `:937` — `elif _kill_switch(regime, normalized_quotes):` — a trip
  rebuilds `validation_summary` with `system_halted=True`,
  `halt_reason=KILL_SWITCH_HALT_REASON`, `halt_cause=HaltCause.MARKET_STRESS`
  (`:946-951`, via `dataclasses.replace`, already imported `:21`), then
  `outcome = OUTCOME_HALT` (`:952`). The subsequent `else:` branch (`:953`
  on) — correlation, structure, candidate generation, qualification — is
  skipped entirely on a trip, exactly as it is for a validation halt.
- `:1256` — `kill_switch = _kill_switch(regime, normalized_quotes)` inside
  `_build_run_summary`, the daily summary writer — reports the real
  evaluated value and zeroes `validated_count` when true (`:1258-1259`).

**The hourly path (`_execute_notify_run`, `:356-619`):**
- `:370-374` — fetches and validates quotes; `validation_summary` reflects
  only data-quality halts (missing/stale/invalid quotes), never market
  stress.
- `:391-462` — `if not validation_summary.system_halted:` computes `regime`
  (`:392`, unconditionally whenever not already validation-halted, same
  pattern as the daily path's `:931-932`), then branches into
  `_QUALIFY_ONLY_MODES` (`:403`) or `_HOURLY_MODES` (`:426`,
  `elif notify_mode in _HOURLY_MODES and regime.posture != "STAY_FLAT":`)
  to generate candidates, run `qualify_all`, and build `candidate_lines`
  (`:431-462`). **No `_kill_switch` call anywhere in this block or this
  function.** A VIX/SPY stress condition that would trip the daily halt at
  `:937` has no effect here — candidates are generated and qualified
  exactly as in a calm market.
- `:464-476` — `format_hourly_notification(...)` builds `alert_title`/
  `alert_body` from `candidate_lines`/`qualification_summary` computed
  above, **before** the summary is built.
- `:512-532` — success path calls `_build_hourly_run_summary(...)` with the
  real `regime`/`normalized_quotes`.
- `:598-617` — failure path (exception handler) calls the same
  `_build_hourly_run_summary(...)` with `regime=None`,
  `normalized_quotes={}`, `validation_summary=None`, `status=SUMMARY_STATUS_FAIL`.
- `:1903-1990` — `_build_hourly_run_summary` (shared by both call sites
  above): `"kill_switch": False` is a **hardcoded literal at `:1975`**, used
  for both the success and the failure summary. `:1982-1983` show this
  function already has a working sentinel for "this is the failure-path
  call" — `bool(validation_summary.system_halted) if validation_summary is
  not None else True` — used for `system_halted`/`halt_reason` but not
  reused for `kill_switch`.

**Halt propagation is incomplete downstream of `validation_summary` today.**
Three sites do not derive from `validation_summary.system_halted` and would
not reflect a kill-switch escalation if only `validation_summary` were
mutated:
- `_build_hourly_run_summary`'s **call site** (`:527-528`) passes
  `status=SUMMARY_STATUS_SUCCESS, outcome=OUTCOME_NO_TRADE` as literal
  kwargs, not derived from `validation_summary`.
- `_build_hourly_contract` hardcodes `contract["outcome"] = OUTCOME_NO_TRADE`
  unconditionally at `:1898`, after `contract_status` (which does read
  `validation_summary.system_halted`, `:1862-1866`) is already computed.
- `_execute_notify_run`'s success-path return (`:569`) is the unconditional
  literal `{"status": SUMMARY_STATUS_SUCCESS, "suppressed": False}`.

This is a **pre-existing gap**, not one this packet's design introduces: an
hourly run that hits an in-band *validation* halt (e.g. a stale/missing
quote, `halt_cause=HaltCause.VALIDATION`) already reaches these same three
sites today and already reports `status: SUCCESS`/`outcome: NO_TRADE` despite
`system_halted: True`. §5 addresses this precisely for the kill-switch case
without touching that separate, out-of-scope validation-halt behavior — see
the open question in §11.

**A separate function, `_failure_summary`** (`:2335`, literal at `:2366`)
also hardcodes `kill_switch: False`, but its only call site (`:296`) is the
**daily** `execute_run`'s exception handler. Per Dustin's ruling ("existing
daily behavior remains unchanged"), this function is explicitly out of
scope — noted here only because `FINDING_STATUS_MATRIX.md`'s CB-01 evidence
field names it alongside the hourly literal; it is a daily-path write site,
not an hourly one.

## 3. Safety consequence

On a genuine market-stress spike (VIX > 35, VIX up > 15%, or SPY moving
> 3%) that passes data validation: the daily pipeline halts and emits no
candidates. The hourly pipeline, running the same underlying market data,
continues to generate, qualify, and Telegram-alert candidates with
entry/stop/target (R:R) lines, and its published JSON summary affirmatively
states `"kill_switch": false`. `VISION.md:30-34` names extreme stress "a
hard invalidation"; it is enforced on only one of the two live channels.

## 4. Design options

### Option A — Evaluate the kill switch before hourly candidate
qualification and use the result in the hourly summary

Mirror the daily path's existing `if system_halted: ... elif
_kill_switch(...): escalate ... else: generate/qualify` shape (`:934-953`)
inside `_execute_notify_run`, immediately after `regime` is computed
(`:392`) and before the `_QUALIFY_ONLY_MODES`/`_HOURLY_MODES` branches
(`:403`, `:426`):

```
if not validation_summary.system_halted:
    regime = compute_regime(validation_summary.valid_quotes)
    if notify_mode in _HOURLY_MODES and _kill_switch(regime, normalized_quotes):
        validation_summary = replace(
            validation_summary,
            system_halted=True,
            halt_reason=KILL_SWITCH_HALT_REASON,
            halt_cause=HaltCause.MARKET_STRESS,
        )
    else:
        derived = compute_all_derived(...)
        router_state = resolve_sector_router(...)
        flow_snapshot = _load_flow()
        if notify_mode in _QUALIFY_ONLY_MODES:
            ...                      # unchanged
        elif notify_mode in _HOURLY_MODES and regime.posture != "STAY_FLAT":
            ...                      # unchanged
```

Everything inside the new `else:` is the existing code, re-indented one
level — no logic inside it changes. `KILL_SWITCH_HALT_REASON`, `HaltCause`,
and `replace` are already imported in this file (`:21`, `:119`) for the
daily path; no new imports.

**Corrected (2026-08-03):** the check is now `notify_mode in _HOURLY_MODES
and _kill_switch(...)`, not a bare `_kill_switch(...)`. Independent Codex
review confirmed the original form would also fire inside
`_QUALIFY_ONLY_MODES = {post_orb, power_hour, market_close}`
(`cuttingboard/runtime/_constants.py:34-35`) — three non-hourly notify
modes this packet's stated question does not cover and whose acceptance
tests (§10) never exercise. The corrected form only ever changes hourly
behavior, matching the packet's scope exactly.

Downstream effects, all via already-existing machinery unless noted
otherwise:
- `format_hourly_notification` (called `:468-476`, via `_action_label`,
  `cuttingboard/notifications/__init__.py:134-153`) already returns action
  `"HALT"` — and therefore title `f"HALT {pt}"` (`notifications/__init__.py
  :534-535`) — whenever `validation_summary.system_halted` is `True`,
  regardless of cause. **Corrected (2026-08-03):** the packet originally
  cited `test_format_hourly_system_halt_routes_to_halt_format`
  (`tests/test_hourly_alert.py:283-294`) and the title `"SYSTEM HALT"` as
  proof; independent Codex review found both wrong — that test calls
  `format_telegram_alert` with a hand-built `AlertEvent`, a different
  function `_execute_notify_run` never calls. The correct existing proof is
  `test_prd133_action_label_branches_via_title`
  (`tests/test_hourly_alert.py:583-604`, HALT case at `:596-603`), which
  calls `format_hourly_notification` directly — the function
  `_execute_notify_run` actually calls — with
  `validation_summary=_validation(halted=True)` and asserts
  `title.startswith("HALT ")`. A kill-switch escalation reaches this same,
  correctly-cited branch with no formatter change.
- `_build_hourly_contract`'s `contract_status` (`:1862-1866`) already reads
  `validation_summary.system_halted` — a kill-switch escalation
  automatically flips contract status with no contract-builder change. Its
  separate `contract["outcome"]` field does **not** (see the new bullet
  below).
- `_build_hourly_run_summary`'s `"candidates_qualified"` (`:1984`) already
  defaults to `0` when `qualification_summary is None` — since the
  qualification block is skipped on a trip, this is correct with no change.
- `_build_hourly_run_summary`'s `"kill_switch"` literal (`:1975`) becomes
  `_kill_switch(regime, normalized_quotes) if validation_summary is not
  None else None` — reusing the exact `validation_summary is not None`
  sentinel this same function already uses one line above (`:1982-1983`)
  to distinguish the success call site from the failure call site. On
  success, `regime` and `normalized_quotes` are always populated by this
  point (computed at `:392`/`:372` whether or not the switch tripped), so
  the evaluation is always meaningful. On failure, `regime is None` and
  `normalized_quotes == {}`, so no evaluation is attempted.
- **New (2026-08-03), not via existing machinery — independent Codex review
  finding:** `_build_hourly_run_summary`'s call-site kwargs (`:527-528`),
  `_build_hourly_contract`'s `contract["outcome"]` line (`:1898`), and
  `_execute_notify_run`'s success-path return (`:569`) are each
  unconditional literals today (§2) and do **not** derive from
  `validation_summary`. Left unchanged, a kill-switch trip would mutate
  `validation_summary.system_halted` (correctly flipping the formatter
  title and `contract_status`) while these three sites kept publishing
  `status: SUCCESS` / `outcome: NO_TRADE` — a self-contradictory summary
  that would fail `verify_run_summary`'s HALT invariants and misreport the
  run as successful. All three must become conditional on
  `validation_summary.halt_cause == HaltCause.MARKET_STRESS` specifically
  (not on `system_halted` generally, to avoid also changing today's
  separate, out-of-scope validation-halt reporting — see §11):
  `status=SUMMARY_STATUS_FAIL if validation_summary.halt_cause ==
  HaltCause.MARKET_STRESS else SUMMARY_STATUS_SUCCESS` (mirroring the
  daily `_build_run_summary`'s own internal derivation shape, `:1279`),
  `outcome=OUTCOME_HALT if validation_summary.halt_cause ==
  HaltCause.MARKET_STRESS else OUTCOME_NO_TRADE`, and the equivalent
  substitution at `:1898` and `:569`.

**Satisfies the rejection rule** ("reject any option that merely changes
the reported Boolean while still allowing halted candidates to be presented
as tradable") because the escalation happens *before* `candidate_lines` and
`alert_body` are built (`:431-476`), not after: a trip changes what is
generated and sent, not only what is reported.

### Option B — Evaluate only during hourly summary construction

Leave `_execute_notify_run`'s control flow untouched; change only
`_build_hourly_run_summary`'s `:1975` literal to
`_kill_switch(regime, normalized_quotes)`.

**Rejected by the task's own rule.** `alert_title`/`alert_body` are built at
`:468-476`, and `candidate_lines`/`qualification_summary` are populated at
`:431-462` — all strictly *before* `_build_hourly_run_summary` runs
(`:512`/`:598`). A market-stress trip under Option B would still generate,
qualify, and Telegram-alert candidates exactly as today; only the JSON
summary's Boolean would flip. The result is self-contradictory
(`"kill_switch": true` published alongside a Telegram alert presenting
those same candidates as monitor-setup opportunities) and leaves the actual
"user-visible consequence" named in `FINDING_STATUS_MATRIX.md` — the
Telegram alert itself — completely unfixed. This is exactly the pattern the
task instructed to reject.

### Option C — Smaller option

Not proposed. No direct code evidence found that Option A cannot preserve
the safety contract at the stated file boundary — Option A's every
downstream effect (formatter, contract, summary) is satisfied by
already-existing conditional logic keyed on `validation_summary.system_halted`
or `validation_summary is not None`, with no new consumer-facing behavior
invented. A narrower option is not apparent.

## 5. Recommended design

**Option A**, as specified in §4, confined to `cuttingboard/runtime/__init__.py`:
1. `_execute_notify_run`: insert the kill-switch check and halt-escalation
   between regime computation (`:392`) and the existing candidate-generation
   branches (`:403`+), guarded by `notify_mode in _HOURLY_MODES` so
   `_QUALIFY_ONLY_MODES` is never affected, reusing `_kill_switch`,
   `KILL_SWITCH_HALT_REASON`, `HaltCause.MARKET_STRESS`, and
   `dataclasses.replace` — all already used for the identical purpose in
   the daily path (`:934-953`). No new kill-switch model, threshold, or
   halt cause.
2. `_build_hourly_run_summary`: replace the `:1975` literal with
   `_kill_switch(regime, normalized_quotes) if validation_summary is not
   None else None`, reusing this function's own existing
   `validation_summary is not None` sentinel (`:1982-1983`).
3. `_build_hourly_run_summary`'s call-site `status`/`outcome` kwargs
   (`:527-528`), `_build_hourly_contract`'s `contract["outcome"]` line
   (`:1898`), and `_execute_notify_run`'s success-path return (`:569`):
   each becomes conditional on `validation_summary.halt_cause ==
   HaltCause.MARKET_STRESS`, per §4's new bullet — the propagation fix an
   independent Codex review of this packet's first revision identified as
   missing. Scoped to the kill-switch halt cause specifically, not to
   `system_halted` generally, so today's separate validation-halt
   reporting is untouched (§11).

## 6. Data / control flow — before and after

**Before:** `fetch → normalize → validate → (if not validation-halted)
regime → derived/router → [QUALIFY_ONLY | HOURLY: generate → qualify →
candidate_lines] → format alert (candidates visible regardless of market
stress) → build contract → build summary (kill_switch: False, always)`.

**After:** `fetch → normalize → validate → (if not validation-halted) regime
→ kill-switch check → [tripped: escalate validation_summary to halted, skip
straight to alert/contract/summary construction, exactly as an existing
validation halt does today] → [not tripped: derived/router → generate →
qualify → candidate_lines, unchanged] → format alert (title `"HALT {pt}"` on a
trip, via the existing formatter branch — `test_prd133_action_label_
branches_via_title`; unchanged candidate presentation otherwise) → build
contract (`contract_status` already halt-aware; `contract["outcome"]` now
also conditional on the kill-switch halt cause, §5 step 3) → build summary
(`kill_switch`: real evaluated value on success paths, `None` on the
already-existing failure-path sentinel; `status`/`outcome` now also
conditional on the kill-switch halt cause) → `_execute_notify_run` returns
`status: FAIL` on a kill-switch trip instead of the previous unconditional
`SUCCESS`.

No new branch, consumer, or persisted field is added; an existing branch
(the validation-halt path) gains a second way to be entered, one
already-computed value (`_kill_switch`'s result) is read where a literal
was previously written, and three already-existing status/outcome fields
that today silently ignore `system_halted` become conditional on the new
kill-switch-specific halt cause.

## 7. Proposed file boundary

`ESTIMATED SURFACE — NOT YET APPROVED` (GOV-2 §5 — this is a pre-review
estimate, not a constraint; the first binding ceiling is set at Gate A on
the reviewed PRD).

- `M cuttingboard/runtime/__init__.py` — the changes in §5.
- `A` or `M` one focused test file covering the hourly path — either a new,
  **unnumbered** test file, or an addition to the existing
  `tests/test_hourly_alert.py` / `tests/test_runtime_decision.py` (the
  latter already contains the daily kill-switch test suite, `:438-663`, as
  a direct structural precedent for the hourly-path equivalents). The
  exact file is an authoring-time decision once a PRD is drafted, not
  fixed by this packet.
  **Corrected (2026-08-03):** the packet's first revision suggested a
  `test_prd278_...`-style filename. Independent Codex review found
  `docs/prd_history/PRD-277.md:153-160` (Amendment 2, "RE-SCHEDULED AS
  PRD-278") already records a different, durable scope reservation against
  PRD-278 — a numbered Phase-1 pointer-diff-verification contract step, not
  CB-01. `docs/prd_index.json`'s `next_prd: 278` is a mechanical "next
  available" counter only; it does not adjudicate this conflicting textual
  reservation. Reusing PRD-278 for CB-01 would create conflicting
  downstream authority records. This packet does not resolve which PRD
  number CB-01 ultimately gets (that is a registry-allocation decision
  outside a MATERIAL packet's scope) — it only removes the specific,
  premature "278" reference from its own test-naming suggestion.

No other file. `cuttingboard/delivery/dashboard_renderer.py` was read
(read-only, for the consumer-compatibility check in §9) but is not
proposed for change — it already keys its "halted" styling
(`:2297`, `if bool(system_halted)`) independently of the `kill_switch`
field, and only additionally renders a "Kill switch active" sub-banner
(`:2299`, `if bool(kill_switch):`) when `kill_switch` is truthy. No direct
call-chain dependency requires touching it.

## 8. Explicit non-goals

- No change to `_failure_summary` (`:2335`/`:2366`) or the daily
  `execute_run` exception path — daily behavior is unchanged per Dustin's
  ruling.
- No change to `_run_pipeline`, `_build_run_summary`, or any other daily
  call site.
- No new kill-switch thresholds, carriers, or evaluator — `_kill_switch`,
  `KILL_SWITCH_VIX_LEVEL`/`_PCT_CHANGE`/`_SPY_PCT_CHANGE`, and
  `KILL_SWITCH_HALT_REASON` are reused verbatim.
- No new persisted field. `"kill_switch"` already exists in the hourly
  summary schema; only its computed value changes, plus (§9) a possible
  narrowing from always-`bool` to `bool | null` on the failure path only —
  flagged as an open question, not decided here.
- No dashboard, notification-formatter, or contract-builder code change.
- No CB-02 scope, packet, or sequencing decision — CB-02 is referenced only
  for the single fact that CB-01 must merge before its Gate A (DR-001).
- No PRD allocation, PRD drafting, or implementation. This packet is
  design-only.

## 9. Risks and rollback

**Risk — failure-path `kill_switch` value (open question, see §11).**
Setting it to `None` on the existing failure-path sentinel is semantically
more honest ("unevaluated," not "confirmed clear") but widens the field's
JSON type from `bool` to `bool | null`. Consumer check:
`dashboard_renderer.py:875-881`'s `_req` only validates key *presence*, not
type or non-null — a `None` value would not raise, and `bool(None) is
False` at `:2299`, so the dashboard's "Kill switch active" sub-banner would
not additionally render on a failed hourly run either way. The dashboard's
primary "halted" styling (`:2297`) reads `system_halted` independently and
already correctly renders on the failure path (`_build_hourly_run_summary`
`:1982`, `True` when `validation_summary is None`), so a failed run is
never visually presented as clear regardless of which value is chosen here.
`tests/test_operationalization.py:645` asserts a *contradiction* rule
("kill_switch runs must not qualify trades") that is orthogonal to this
choice. No consumer found that requires `kill_switch` to be non-null.

**Risk — the hourly halt path's data-status/error text.** Escalating via
`replace(validation_summary, system_halted=True, halt_reason=
KILL_SWITCH_HALT_REASON, halt_cause=HaltCause.MARKET_STRESS)` overwrites any
prior `halt_reason` a not-yet-validation-halted `validation_summary` might
carry. Verified not applicable: the escalation in §5 is reached only inside
`if not validation_summary.system_halted:`, i.e. only when
`validation_summary.halt_reason` is already unset — no existing reason is
discarded.

**Rollback — corrected (2026-08-03):** the changes in §5 are confined to
`cuttingboard/runtime/__init__.py` but are **not** independently safe to
partially revert, per independent Codex review. Reverting only the
control-flow change (step 1) while keeping the summary-field change (step
2) recreates rejected Option B: `kill_switch` would report the real value
while stressed candidates are still generated and Telegram-alerted.
Reverting only the summary-field change (step 2) while keeping the
control-flow change (step 1) restores candidate suppression but resumes
publishing a hardcoded `kill_switch: false` alongside the now-correctly
halted contract/summary — reopening exactly half of CB-01's Critical
defect either way. Reverting steps 1-2 while keeping step 3 (propagation)
is inert but harmless; reverting step 3 alone while keeping 1-2 reopens the
self-contradictory-summary defect §4/§5 describe. **The eventual
implementation PRD must land steps 1-3 as one deploy unit and specify that
an incident rollback reverts the entire commit, never a subset.** A revert
of the full unit restores exactly today's behavior with no residual state,
migration, or persisted artifact to unwind.

## 10. Test and acceptance contract

**Baseline (2026-08-03), no code changed — GOV-2 §3 self-verification:**
```
python3 -m pytest tests/test_runtime_decision.py tests/test_hourly_alert.py tests/test_dashboard_renderer.py -q
```
→ `426 passed in 71.43s`, 0 failed, against `main`
`e6a5ce69e8fba18c3e5147bc5ceac3aebddc13c3`. This establishes the clean
baseline the eventual implementation must not regress and confirms every
existing test cited below currently passes as described.

Existing precedent: `tests/test_runtime_decision.py:438-663` is the daily
kill-switch test suite (threshold boundaries, halt escalation, audit-record
carry-through) built directly against `_kill_switch`/`_run_pipeline`. The
hourly equivalents should mirror its structure against `_execute_notify_run`
/ `_build_hourly_run_summary`.
`test_prd133_action_label_branches_via_title`
(`tests/test_hourly_alert.py:583-604`, HALT case `:596-603`) — **corrected
citation, 2026-08-03** — is the existing proof that the formatter path
Option A relies on (`format_hourly_notification`, not `format_telegram_alert`)
already works.

A PRD drafted from this packet must require, at minimum:
1. Hourly success summaries report the real evaluated kill-switch state
   (mirrors `tests/test_runtime_decision.py:479-483`'s daily threshold-
   boundary pattern, retargeted at the hourly path).
2. A triggered kill switch cannot be represented as `false`/clear in the
   hourly summary, and the hourly alert does not present candidates as
   tradable in that state (assert on both the summary JSON and
   `candidate_lines`/`alert_title`/`alert_body`, per §4's rejection rule).
3. **(Added 2026-08-03.)** A triggered kill switch produces a
   self-consistent halted summary and contract, not merely a flipped
   Boolean: `summary["status"] == SUMMARY_STATUS_FAIL`,
   `summary["outcome"] == OUTCOME_HALT`, `contract["outcome"] ==
   OUTCOME_HALT`, and `_execute_notify_run`'s return value has
   `status == SUMMARY_STATUS_FAIL` (§4/§5's propagation fix). Assert
   `verify_run_summary` (or its hourly equivalent, if any) accepts the
   result without a HALT-invariant violation.
4. Hourly failure summaries do not hardcode or imply a clear state (assert
   whichever value Dustin's ruling selects in §11).
5. Non-hourly notify modes (`post_orb`, `power_hour`, `market_close`) are
   unaffected by a market-stress condition — assert `_QUALIFY_ONLY_MODES`
   candidate generation still runs under conditions that would trip the
   kill switch, proving the `notify_mode in _HOURLY_MODES` guard (§4/§5)
   is actually enforced, not merely stated.
6. Existing daily-path tests (`tests/test_runtime_decision.py`) are
   unchanged and still pass.
7. Mutation-verified red test: revert only the `_execute_notify_run`
   control-flow change (keep the summary-field change) and confirm a
   kill-switch-tripped hourly run still generates/qualifies candidates —
   proving requirement 2 above is actually enforced by the control-flow
   change, not merely by the reporting change (PRD-198 invariant 4).
8. Full `pytest tests/ -q` green, including `tests/test_hourly_alert.py`
   and `tests/test_dashboard_renderer.py` (consumer regression check for
   `kill_switch`/`system_halted` rendering).

## 11. Open questions requiring Dustin's design-direction ruling

1. **Failure-path `kill_switch` value:** `None`/null (semantically honest,
   narrows nothing a known consumer depends on per §9, but widens the JSON
   type) or keep it `False` (matches today's hourly behavior and the
   unchanged daily `_failure_summary` precedent; relies entirely on
   `system_halted: True` + `status: FAIL` to prevent a "clear" reading,
   which §9 shows already holds for every checked consumer)?
2. **Test file placement:** new dedicated test file, or extend
   `tests/test_hourly_alert.py` / `tests/test_runtime_decision.py`
   (§7) — no functional difference, author's choice unless Dustin has a
   preference.
3. **Confirm Option A is the design-direction ruling** (§4/§5), i.e. that
   evaluating and escalating inside `_execute_notify_run`'s control flow —
   not merely the summary field — is authorized, since this is the step
   GOV-2 §2 step 6 reserves to Dustin and this packet cannot itself
   authorize.
4. **(Added 2026-08-03.)** §2/§5 surfaced that hourly runs halted by a
   plain **validation** failure (`halt_cause=HaltCause.VALIDATION` —
   missing/stale quotes, not market stress) already publish `status:
   SUCCESS` / `outcome: NO_TRADE` today, despite `system_halted: True` —
   the same class of propagation gap CB-01 has for the kill-switch case,
   but pre-existing and outside CB-01's Critical finding. §5's fix is
   scoped to `halt_cause == HaltCause.MARKET_STRESS` specifically so it
   does not silently also change that separate behavior. Does Dustin want
   this pre-existing validation-halt gap logged as its own (non-Critical)
   finding for separate triage, or left as an undocumented observation?
   This packet takes no position and proposes no fix for it.
5. **(Added 2026-08-03.)** PRD-278 is informally reserved for different,
   already-recorded work (`docs/prd_history/PRD-277.md:153-160`). This
   packet's own earlier revision incorrectly assumed it was free for CB-01
   (repeated in PR #192's report). No action needed from this packet's
   design-direction ruling, but whoever allocates CB-01's eventual PRD
   number should not default to PRD-278 without first resolving that
   reservation.

Independent Codex packet review (GOV-2 §2 step 3) is the next required
step before any of the above may be ruled on.
