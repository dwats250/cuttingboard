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

**Correction (2026-08-03) — one consolidated pass per GOV-2 §7, addressing the
independent Codex review of commit `73f0f14e7afbc4a7297bec1609b2e3481a9e1397`:**
four findings, all accepted as factually correct on re-verification against `main`
at the same head. (1, P1) The recommended design threaded `kill_switch`/
`system_halted` but left the hourly success path reporting `status: SUCCESS` /
`outcome: NO_TRADE` — corrected in §7/§8 to carry terminal HALT semantics through
both `_build_hourly_run_summary` and `_build_hourly_contract`. (2, P2) §15 Q1
previously presented a failure-path `False` option as contract-compliant when the
packet's own text already showed it was not — corrected to state plainly that only
`True` is compliant given the current Boolean schema. (3, P2) §3 claimed every
intraday trip reaches candidate generation, ignoring that the existing CHAOTIC/
STAY_FLAT posture gate already suppresses the VIX-%-change leg — corrected to name
the two discriminating bypass cases and require a non-CHAOTIC fixture in the test
plan. (4, P1) The recommended guard still let `compute_all_derived`,
`resolve_sector_router`, and `_load_flow()` run after a detected trip, risking the
known HALT being overwritten by a generic failure summary if one of those raised —
corrected to an early exit immediately on trip, before any of that downstream work.

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

**Terminal HALT carriers are also hardcoded, not just `kill_switch` (added
2026-08-03, Codex finding 1):**
- `_execute_notify_run:527-528` — the success call site passes
  `status=SUMMARY_STATUS_SUCCESS, outcome=OUTCOME_NO_TRADE` to
  `_build_hourly_run_summary` unconditionally; neither is derived from
  `validation_summary.system_halted` or any kill-switch evaluation.
- `_build_hourly_contract:1862-1866` — `contract_status = derive_run_status(
  OUTCOME_NO_TRADE, regime, bool(validation_summary.system_halted) if
  validation_summary is not None else False)` passes the literal `OUTCOME_NO_TRADE`
  as its outcome argument regardless of `system_halted`.
- `_build_hourly_contract:1898` — `contract["outcome"] = OUTCOME_NO_TRADE` is a
  second, separate hardcode of the same literal on the same function.
- By contrast, the daily path's own convention for a kill-switch trip is
  `status=SUMMARY_STATUS_FAIL` (`_build_run_summary:1279`,
  `SUMMARY_STATUS_FAIL if validation_summary.system_halted or errors else
  SUMMARY_STATUS_SUCCESS`) and `outcome=OUTCOME_HALT` (`_run_pipeline:952`, set
  before `_build_run_summary` is called). Threading `kill_switch`/`system_halted`
  alone, without also correcting these two outcome/status literals, would leave a
  tripped hourly run self-reporting `SUCCESS`/`NO_TRADE` next to `kill_switch:
  true` — an internally inconsistent artifact, not the daily path's terminal HALT
  shape.

**CHAOTIC/STAY_FLAT already suppresses one of the three kill-switch legs (added
2026-08-03, Codex finding 4):**
- `regime._classify_regime` (`regime.py:299-306`): `if vix_pct is not None and
  vix_pct > config.VIX_CHAOTIC_SPIKE: return CHAOTIC`, where
  `config.VIX_CHAOTIC_SPIKE = 0.15` (`config.py:113`) — the exact same threshold
  and strict-`>` comparison as `_kill_switch`'s VIX-%-change leg
  (`KILL_SWITCH_VIX_PCT_CHANGE = 0.15`).
- `regime._determine_posture` (`regime.py:319-326`): `if regime == CHAOTIC or
  confidence < config.MIN_REGIME_CONFIDENCE: return STAY_FLAT`.
- The existing hourly guard at `:426` (`elif notify_mode in _HOURLY_MODES and
  regime.posture != "STAY_FLAT":`) therefore already blocks candidate generation
  whenever the VIX-%-change leg alone trips — independently of this remediation,
  and today, before any fix lands.
- **The `kill_switch: false` misreport (§1, §3) is unaffected by this and persists
  regardless of which leg trips** — CHAOTIC/STAY_FLAT suppresses candidate
  generation for that one leg, but `_build_hourly_run_summary` still hardcodes the
  field to `False` on every hourly run, CHAOTIC or not. Only the "candidates
  presented as tradable during a halt-equivalent condition" half of CB-01's
  consequence is narrower than a blanket claim; the "falsely reports clear" half is
  not narrowed at all.

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

**Corrected 2026-08-03 (Codex finding 4):** an earlier version of this section
claimed every intraday kill-switch condition still reaches candidate generation.
That is not precisely true for one of the three legs — see §2's CHAOTIC/STAY_FLAT
note. CB-01's Critical classification in `FINDING_STATUS_MATRIX.md` is unaffected
by this correction; it stands on the discriminating cases below and on the
misreport, which is unconditional.

The two demonstrated cases where the hourly channel still generates, qualifies,
and presents candidates during a condition that would HALT the daily pipeline —
because CHAOTIC/STAY_FLAT does not fire and the existing `:426` guard does not
block them — are:
- **sustained VIX level above 35**, without an accompanying single-interval VIX
  spike above 15% (so `_classify_regime` does not return CHAOTIC); or
- **an absolute SPY move above 3%**, independent of VIX entirely.

On either of those two conditions today:
- The hourly channel still runs fetch → regime → candidate → qualify.
- It still sends a Telegram alert with qualified candidate R:R lines.
- Its own published `latest_hourly_run.json` summary states `"kill_switch": false`,
  affirmatively certifying the safety indicator as clear on the very run where it
  is not.
- Any consumer of that summary (dashboard render, downstream tooling) inherits the
  false certification, not just a missing one.

**The misreport itself is unconditional and broader than the two cases above:**
`_build_hourly_run_summary` hardcodes `kill_switch: false` on every hourly run,
including a CHAOTIC-driven trip where candidate generation is already (separately)
suppressed. A dashboard or downstream reader consulting `kill_switch` alone cannot
distinguish "verified clear" from "never evaluated" on any hourly run today.

`VISION.md:30-34` treats extreme market stress as a hard invalidation. It is
currently enforced on one of the two live channels only.

## 4. Bounded design options

### Option A — Evaluate before any downstream work, carry terminal HALT through every hourly output

**Corrected 2026-08-03 (Codex findings 1 and 4).** Evaluate
`_kill_switch(regime, normalized_quotes)` once regime is available in the hourly
branch of `_execute_notify_run`, immediately and before any further downstream
work — not only before candidate generation/qualification, but before
`compute_all_derived`, `resolve_sector_router`, and `_load_flow()` as well. On a
trip, escalate exactly as the daily path does (mark the validation state halted
with `KILL_SWITCH_HALT_REASON` / `HaltCause.MARKET_STRESS`), take the early-exit
branch (no downstream computation, no candidate generation), and carry that
terminal HALT state through every hourly output that currently hardcodes a
clear/success literal: `_build_hourly_run_summary`'s `kill_switch`, `status`, and
`outcome` fields, and `_build_hourly_contract`'s `outcome` field (both of its
current hardcode sites).

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

**Option A satisfies the full contract, corrected shape.** Evaluating before any
downstream work and early-exiting on a trip, before qualification runs, satisfies
items 1–3 directly (nothing to qualify or present once gated, and nothing that
could raise and swallow the trip runs either — Codex finding 4); reuses
`_kill_switch`/`KILL_SWITCH_HALT_REASON`/`HaltCause.MARKET_STRESS` verbatim, so item
7 holds; threading the trip signal through existing function signatures adds no
schema (item 8); touches no dashboard, notification formatter, or unrelated module
(item 9); and the clear-state branch (posture-gated candidate generation) is
untouched when the switch is not tripped, so item 4 holds. Item 5 (failure
handling) is resolved by §7 step 6's unconditional `kill_switch=True` on the
failure path, not left as an open design choice — see §15 Q1.

**Option C** — not evaluated; no evidence forces a smaller boundary than A/B, and
A already meets the contract at the smallest observed control-flow cost (one
evaluation call, reused escalation pattern, threaded parameters, no new file).

## 7. Recommended design (Option A, corrected 2026-08-03)

Reuse the daily path's own pattern in full — its early exit and its terminal HALT
output shape, not only its evaluator and escalation dataclass:

1. In `_execute_notify_run`, immediately after `regime = compute_regime(...)`
   (`:392`) and still inside `if not validation_summary.system_halted:`, evaluate
   the kill switch only for the hourly mode:
   `hourly_kill_switch = notify_mode in _HOURLY_MODES and _kill_switch(regime,
   normalized_quotes)`, initialized `False` before the `try` block so it is always
   defined at both summary/contract call sites.
2. **Early exit, before any downstream work (Codex finding 4, P1).** Restructure so
   that on a trip, none of `compute_all_derived`, `resolve_sector_router`, or
   `_load_flow()` (currently unconditional at `:393-401`) run, and neither
   candidate-generation branch (`_QUALIFY_ONLY_MODES` at `:403-424` or
   `_HOURLY_MODES` at `:426-462`) runs. Concretely: those calls move into an
   `else:` keyed on `hourly_kill_switch`, mirroring the daily path's own early exit
   on a trip (`_run_pipeline:937-953`, which skips its entire qualification `else:`
   block on the same condition). This is what prevents a downstream helper
   (`_load_flow()` was Codex's example) from raising and having the exception
   handler overwrite an already-known trip with the separately-ruled failure-path
   value — once tripped, nothing that could raise runs before the halt is
   recorded.
3. On trip, escalate `validation_summary` the same way the daily path does —
   `dataclasses.replace(validation_summary, system_halted=True,
   halt_reason=KILL_SWITCH_HALT_REASON, halt_cause=HaltCause.MARKET_STRESS)` — so
   fields that already derive from `validation_summary.system_halted` /
   `halt_reason` in `_build_hourly_run_summary` (permission text, `system_halted`,
   `halt_reason`) update themselves with no additional field-by-field change.
4. **Terminal HALT carriers (Codex finding 1, P1).** Correct the two hardcoded
   outcome/status literals identified in §2, so a tripped run cannot self-report
   success or NO_TRADE next to `kill_switch: true`:
   - `_build_hourly_run_summary`'s call site (`:512-532`) passes
     `status=SUMMARY_STATUS_FAIL if hourly_kill_switch else SUMMARY_STATUS_SUCCESS`
     and `outcome=OUTCOME_HALT if hourly_kill_switch else OUTCOME_NO_TRADE`,
     replacing the current unconditional `status=SUMMARY_STATUS_SUCCESS,
     outcome=OUTCOME_NO_TRADE` (`:527-528`).
   - `_build_hourly_contract` gains the same trip signal as a new parameter and
     uses it at both of its current hardcode sites: the `derive_run_status(
     OUTCOME_NO_TRADE, regime, ...)` call (`:1862-1866`) and the
     `contract["outcome"] = OUTCOME_NO_TRADE` assignment (`:1898`) both become
     `OUTCOME_HALT if hourly_kill_switch else OUTCOME_NO_TRADE`.
5. Add a `kill_switch: bool` parameter to `_build_hourly_run_summary` and replace
   the hardcoded `"kill_switch": False,` literal (`:1975`) with that parameter. Pass
   `kill_switch=hourly_kill_switch` at the success call site.
6. **Failure-path Boolean (Codex finding 3, P2).** At the failure/exception call
   site (`:598-617`), pass `kill_switch=True` unconditionally, regardless of
   whatever `hourly_kill_switch` held before the exception. The current schema is
   a plain Boolean with no "unknown" state; `False` on a run that never completed
   evaluation is indistinguishable from an evaluated clear result and therefore
   never satisfies contract item 5. `True` (assume tripped, fail-safe) is the only
   value consistent with the safety contract at this schema. This packet does not
   introduce a tri-state or additional field (contract item 8; §10 non-goals) — a
   schema change, if ever wanted, is a separate authorization.

This is the pattern already ruled sound for the daily path (PRD-180), corrected to
match its early-exit and terminal-HALT output shape exactly — nothing new is
designed.

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

**After** (Option A, corrected 2026-08-03):

```
fetch/normalize/validate quotes
if not validation_summary.system_halted:
    regime = compute_regime(...)
    hourly_kill_switch = (notify_mode in _HOURLY_MODES) and _kill_switch(regime, normalized_quotes)
    if hourly_kill_switch:
        validation_summary = replace(validation_summary, system_halted=True,
                                      halt_reason=KILL_SWITCH_HALT_REASON,
                                      halt_cause=HaltCause.MARKET_STRESS)
        # EARLY EXIT -- nothing below runs: no derived/router_state/flow_snapshot,
        # no _QUALIFY_ONLY_MODES or _HOURLY_MODES candidate branch, nothing that
        # could raise and overwrite the already-known trip.
    else:
        derived, router_state computed                          # unchanged
        flow_snapshot = _load_flow()
        if notify_mode in _QUALIFY_ONLY_MODES:
            generate_candidates -> qualify_all -> candidate_lines   # unchanged
        elif notify_mode in _HOURLY_MODES and regime.posture != STAY_FLAT:
            generate_candidates -> qualify_all -> candidate_lines   # unchanged
format_hourly_notification(...)   # halt_reason reflects the trip automatically
send_notification(...)
build_hourly_contract(..., kill_switch=hourly_kill_switch)   # outcome=HALT on trip, both hardcode sites
_build_hourly_run_summary(
    ..., kill_switch=hourly_kill_switch,
    status=FAIL if hourly_kill_switch else SUCCESS,
    outcome=HALT if hourly_kill_switch else NO_TRADE,
)
write hourly artifacts
```

Exception path: `hourly_kill_switch` is defined (default `False`) before the `try`
block, but the failure-path `_build_hourly_run_summary` call passes
`kill_switch=True` unconditionally (finding 3) — independent of whatever
`hourly_kill_switch` held when the exception was raised. A failed run never
asserts clear.

## 9. Exact proposed file boundary

```
ESTIMATED SURFACE — NOT YET APPROVED
```

- `M  cuttingboard/runtime/__init__.py` — the changes in §7/§8, all within this one
  file: one evaluation call, one conditional escalation reusing existing
  constants/dataclasses, an early-exit restructure of the existing
  `if not validation_summary.system_halted:` block, one new `kill_switch`
  parameter on `_build_hourly_run_summary` plus its `status`/`outcome` call-site
  arguments, and one new trip-signal parameter on `_build_hourly_contract` used at
  its two existing `OUTCOME_NO_TRADE` hardcode sites. **Widened 2026-08-03**
  (Codex finding 1) from the original single-parameter estimate to include
  `_build_hourly_contract`'s outcome carriers — still the same one file, no new
  file added.
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
- `contract.py` has no `kill_switch` handling and is not touched. The hourly
  contract builder (`_build_hourly_contract`, `:1847-1901`, in
  `runtime/__init__.py`) does need its own explicit change — see §7 step 4 and the
  widened §9 bullet above — because its `outcome` field is independently hardcoded
  at two sites and does not update automatically from the `validation_summary`
  escalation alone.
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

- **Downstream rendering of the corrected values is unverified.** This packet does
  not inspect the dashboard renderer or notification formatter (explicit non-goal);
  if either currently assumes `kill_switch` is always `false`, or `outcome` is
  always `NO_TRADE`, on the hourly surface, a previously-dormant rendering path
  could activate for the first time now that a tripped run can report `status:
  FAIL` / `outcome: HALT`. Recommend the eventual PRD's downstream-consumer audit
  (per `CLAUDE.md` Author disciplines) explicitly check `ui/` and `notifications/`
  renderers before Gate A, even though this packet does not touch them.
- **Resolved 2026-08-03 (was: `derived`/`router_state`/`structure` continuing to
  compute after a trip).** The corrected design (§7 step 2) now early-exits before
  any of that computation, matching the daily path's own shape. No longer a risk;
  removed as an open question (former §15 Q2).
- **`_build_hourly_contract`'s widened parameter surface (§9) is a slightly larger
  touch than the original single-parameter estimate**, though still confined to
  the same one file. Recommend the fresh-context independent PRD reviewer (GOV-2
  §2 step 7) re-check that this is in fact the minimal set of carriers once an
  implementation PRD is drafted, rather than assuming this packet's enumeration is
  exhaustive.

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

1. **Trip halts and reports true — non-CHAOTIC fixture (corrected 2026-08-03,
   Codex finding 4).** Monkeypatch `compute_regime`/quotes to produce ONE of the
   two discriminating bypass conditions named in §3 — sustained VIX level above 35
   with `vix_pct_change` at or below `0.15` (so `_classify_regime` does NOT return
   CHAOTIC and the pre-existing `:426` STAY_FLAT gate does NOT independently
   suppress candidates), or an absolute SPY move above 3% with VIX otherwise quiet
   — applied through `_execute_notify_run(notify_mode=NOTIFY_HOURLY)`. A CHAOTIC-
   triggering fixture (VIX-%-change alone) must NOT be used here, since it would
   pass even without this fix, proving the pre-existing posture gate instead of
   the new kill-switch gate. Assert `latest_hourly_run.json` has `kill_switch:
   true`, `system_halted: true`, `halt_reason` equal to `KILL_SWITCH_HALT_REASON`,
   `status: SUMMARY_STATUS_FAIL`, `outcome: OUTCOME_HALT`, `candidates_qualified ==
   0`, and `candidate_lines == []`; assert `latest_hourly_contract.json`'s
   `outcome` is also `OUTCOME_HALT`. Red against current code on every one of
   those assertions.
2. **Trip suppresses candidate generation, not just the reported field.** Same
   fixture as (1); assert `generate_candidates`/`qualify_all` were not invoked (spy
   or monkeypatch to raise if called) — this is the test that specifically
   discriminates Option A from Option B (§6): reverting only the summary literal
   while leaving qualification ungated must fail this assertion.
3. **No downstream work after a detected trip (added 2026-08-03, Codex finding
   4).** Same fixture as (1); monkeypatch `_load_flow` (and/or
   `compute_all_derived`, `resolve_sector_router`) to raise if called. Assert
   `_execute_notify_run` still returns `{"status": SUMMARY_STATUS_SUCCESS,
   "suppressed": False}` (a detected trip is a successful run, not an exception)
   and that `latest_hourly_run.json` still carries the true trip state from (1) —
   proving the early exit actually happens before any helper that could raise, not
   only that skipping candidate generation happens to avoid today's specific
   raise sites.
4. **Clear state unchanged.** Existing tests that already exercise a non-tripped
   hourly run with qualified candidates (e.g.
   `test_hourly_candidate_line_uses_promoted_geometry_prd260_r7`) must continue to
   pass unmodified — cited as regression evidence for contract item 4, not
   rewritten.
5. **Direct summary-builder unit test.** Mirror
   `test_notification_sent_derived_strictly_from_status`'s pattern of calling
   `_build_hourly_run_summary` directly with `kill_switch=True` and
   `kill_switch=False` (and, per §7 step 4, `status`/`outcome` covarying with the
   same trip flag); assert every field passes through verbatim. Proves the
   parameter threading independent of the control-flow gating.
6. **Failure path always reports true (corrected 2026-08-03, Codex finding 3).**
   Extend `test_hourly_sends_exactly_once_on_exception` /
   `test_hourly_writes_traceback_on_exception`'s fixture to assert
   `kill_switch: true` on the failure summary unconditionally — not a
   placeholder pending a ruling; §7 step 6 fixes this value directly, since
   `False` is never contract-compliant for an incomplete evaluation.
7. **Daily unchanged (regression only, no new test).** Existing
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
- `latest_hourly_run.json`'s `kill_switch`, `status`, and `outcome` fields, and
  `latest_hourly_contract.json`'s `outcome` field, are all derived from the same
  trip evaluation, not literal, at both call sites of `_build_hourly_run_summary`
  and at `_build_hourly_contract` — a tripped run cannot report `SUCCESS`,
  `NO_TRADE`, or `kill_switch: false` on any of the four fields (added 2026-08-03,
  Codex finding 1).
- A detected trip is provably reached before `compute_all_derived`,
  `resolve_sector_router`, and `_load_flow()` run — §13 test 3 must demonstrate
  this by making each raise and confirming the trip state still surfaces correctly
  (added 2026-08-03, Codex finding 4).
- The hourly failure-path summary reports `kill_switch: true` unconditionally;
  `False` on an incomplete evaluation is never acceptable at the current schema
  (added 2026-08-03, Codex finding 3).
- §13 test 1 uses a non-CHAOTIC fixture (sustained VIX > 35 without a
  matching %-change spike, or `|SPY %change| > 3%`) so the discriminating
  assertion exercises the new kill-switch gate, not the pre-existing CHAOTIC/
  STAY_FLAT posture gate (added 2026-08-03, Codex finding 4).
- No file outside §9's two-file boundary is modified.
- Full existing suite remains green, including every test named in §13 items 4 and
  7 as unmodified regression evidence.

## 15. Open questions requiring Dustin's design-direction ruling

**Q1 — Failure-path `kill_switch` value: confirm, or authorize a schema change
(revised 2026-08-03, Codex finding 3).** The prior revision of this question
presented `True` and `False` as two contract-compliant candidates. On correction,
only `True` is contract-compliant: `False` on a run that never completed
evaluation is indistinguishable in the JSON from an evaluated clear result and
therefore always violates contract item 5 ("does not falsely assert a clear
state") — it is not a live design choice at the current Boolean schema. §7 step 6
already fixes the failure-path value to `True` unconditionally as this packet's
recommended design, not as one of two open options. What remains for Dustin's
ruling is narrower: (a) **ratify `True`** as designed — `system_halted`/`status:
FAIL`/`outcome: HALT` already correctly signal "no trades" on this path regardless
of the `kill_switch` literal, so this is a labeling choice, not a
candidate-suppression one (contract item 3 is already satisfied on the failure
path independent of this answer, since `qualification_summary=None` there in all
cases); or (b) **authorize a tri-state or additional field** (e.g.
`kill_switch_evaluated: bool` alongside `kill_switch: bool`) if a bare "assume
tripped" reading is judged too likely to mislead a dashboard viewer into believing
market stress was actually observed. Option (b) is a schema change and is out of
this packet's non-goals (§10) if chosen — it would need its own amended-boundary
treatment, not silent inclusion here. Recommendation: (a); introduce a second field
only if Dustin judges the mislabeling risk in §11 material enough to accept the
larger surface.

**Q2 — Boundary observation on `_QUALIFY_ONLY_MODES`.** §2's boundary observation
(the same pre-branch gate also precedes `post_orb`/`power_hour`/`market_close`) is
not sized, rated, or acted on by this packet. Does Dustin want a separate
materiality check opened for that surface, independent of and not blocking CB-01?
Recommendation: defer; CB-01's own DR-001 sequencing constraint (must merge before
CB-02 Gate A) already sets urgency on the narrower fix, and expanding this packet's
claim would itself trigger GOV-2's boundary-reset rule (§6) for scope not yet
verified.

**Resolved 2026-08-03 — former Q2 (`derived`/`router_state`/`structure`
computation on a trip).** Codex finding 4 elevated this from an acceptable
asymmetry to a correctness requirement: without an early exit, a downstream raise
during a genuine trip could route to the failure path and lose the already-known
HALT determination. §7 step 2 now adopts the daily path's full early-exit shape
directly; this is no longer an open question.

---

_Packet author: Claude Code, fresh-context recon session, 2026-08-03. Reviewed
against `main` @ `e6a5ce69e8fba18c3e5147bc5ceac3aebddc13c3`. This packet is
provisional per GOV-2 §2 until independent Codex review, one consolidated
correction if required, and independent exact-corrected-head confirmation have
landed. It authorizes no implementation, no PRD drafting, and no design-direction
ruling._
