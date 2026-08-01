# OPT-0 -- Smallest-Contract Refusal Seam Trace -- 2026-07-31

```
STATUS: READ-ONLY SEAM TRACE
AUTHORIZES NO IMPLEMENTATION
```

Append-only delta to the 2026-07-30 current-state reconciliation (PR #175,
extended by the PR #183 Strategy candidate-fidelity delta). The existing
artifacts in this directory are historical evidence and are not modified.
This file is the only addition.

Charge: the OPT-0 packet of `docs/plans/decision-support-workplan-v0.1.md`
(section 5, "OPT-0 -- Finding D seam trace"), executed under
`docs/plans/agent-work-charge-template-v0.1.md` non-deviation rules.

The operator ruling is NOT reopened here. Dustin ruled 2026-07-24
(`docs/DECISIONS.md:259-292` at the pin below): refuse the setup when the
smallest expressible contract exceeds the applicable adjusted risk budget.
Do not round up; do not permit the breach. This trace determines only the
seam, carrier, reason, downstream behavior, and initial FILES surface.

---

## 1. Reviewed-state header

| Field | Value |
|---|---|
| Repository | `dwats250/cuttingboard` |
| Inspection pin | `main` @ `f6d508f5784992f063d1b45526123031d8537b55` (= `origin/main` after `git pull --ff-only origin main`, "Already up to date"; working tree clean; zero open PRs at session start) |
| Final PR base | `f6d508f5784992f063d1b45526123031d8537b55` -- `origin/main` re-fetched immediately before commit and UNCHANGED from the inspection pin (`git rev-list f6d508f..origin/main` empty), so no intervening-change review was required |
| Branch | `worktree-opt-0-seam-trace` (dedicated worktree branched from `f6d508f`; only this file is added) |
| Working tree | Clean before this file; after, exactly one added file |
| Tool provenance | Local `git` (read-only: `pull --ff-only`, `rev-parse`, `log -S`, `status`, `diff`), `rg`/`grep`/`sed`, `gh` (PR-state reads), and in-process execution of production modules via `.venv/bin/python` (deterministic repro, section 3). Network: github.com only (`git`/`gh`). No market-data fetch, no TradingView, no live chain |
| Effective permission set | `.claude/settings.json` UNION `.claude/settings.local.json` both read per CLAUDE.md. Note: the local file allows `Bash(git checkout *)` and `Bash(git *)`, but the tracked deny list overrides (deny wins), so checkout/worktree/reset remain blocked via Bash; isolation used the harness worktree tool |
| Sub-agents | FOUR bounded read-only `Explore` sweeps: (1) sizing-path enumeration (callers of `build_option_setups`/`generate_candidates`, Gate 8 chain, continuation sizer, config/modifier provenance); (2) downstream-consumer enumeration (OptionSetup fields, absence handling, rejection carriers, renderers, notifiers); (3) test-surface enumeration (floor-binding tests, sizing tests, rejection-taxonomy tests); (4) historical PRD/decision trace (PRD-023/157/251/256, D-RULE, `size_rounds_to_zero`). Each returned paths, symbols, and commands only; none edited anything, decided anything, or assigned dispositions |
| Lead re-verification | The lead personally re-ran every decisive search and trace before use: the repo-wide `max(1,` sweep; the `size_rounds_to_zero` production sweep (zero hits); the `build_option_setups` call-site sweep (one production site); the `.max_contracts`/`.dollar_risk` consumer sweep; the rejections-stage inventory; `git log -S` for the floor's origin commit; and direct reads of `options.py:160-266,353-426`, `qualification.py:1-142,380-581,760-802`, `runtime/__init__.py:622-722,950-1035`, `contract.py:325-345`, `audit.py:123-136`, `output.py:315-370`, `trade_decision.py:55-70`, `trade_policy.py:25-40`, `correlation.py:1-90`, `config.py:60-80,260-285`. The deterministic repro (section 3) was authored and executed by the lead |

Line numbers below are pinned to `f6d508f` and re-resolved there; the
reconciliation baseline's `docs/DECISIONS.md:106-139` citation for the ruling
is stale at this pin (DECISIONS.md is newest-first and has grown); the ruling
now lives at `docs/DECISIONS.md:259-292`. Stale citation, correct content.

## 2. Executive conclusion

1. Seam: OPTIONS CONSTRUCTION -- `options.py::build_option_setups`, replacing
   the `max(1, ...)` floor at `options.py:233` with a refusal branch when
   `raw_adjusted < 1`. Truth is first fully known exactly there.
2. Carrier: a NEW minimal refusal record collected via a list-API-preserving
   `refusals` out-parameter (NOT a return-shape change -- corrected after
   connector review, section 22), threaded into contract `rejections[]`
   under a new stage token, the audit record, and the presentation surfaces.
3. Reason: new token `SMALLEST_CONTRACT_EXCEEDS_BUDGET`;
   `size_rounds_to_zero` is proven semantically distinct (section 11).
4. Surface (corrected, section 14): full truth is 6 production files and
   ~6 test files, ~90-140 net LOC -- the workplan's 4/3/100 ceiling and the
   pre-correction 5/3 estimate are both superseded by connector-verified
   consumers (postmarket aggregation, notification body, HTML adapter).
5. One Dustin ruling remains (section 17): the full-truth surface vs the
   smallest defensible reduced design. All else is settled here.

## 3. Current-defect reproduction

Deterministic, executed by the lead against production modules at the pin,
in-process (no monkeypatching of any constant; live config values). Method:
construct a `QualificationResult` shaped exactly as Gate 8 / the continuation
sizer emit it, call `build_option_setups` exactly as the sole production call
site does (`runtime/__init__.py:1018-1024`), read the emitted `OptionSetup`.
Script: `build_option_setups([qres], {sym: StructureResult(...)}, {}, None,
risk_modifier=<modifier>)` with live `config` values
(`ACCOUNT_EQUITY=15000.0`, `MAX_RISK_PCT_PER_TRADE=0.026667`, base budget
$400.005; modifiers ALIGNED 1.0 / NEUTRAL 0.7 / CONFLICT 0.4,
`CORRELATION_ENABLED=True`).

| # | Case | Strategy resolved | Risk/contract | Adjusted ceiling | Emitted | Breach |
|---|---|---|---|---|---|---|
| 1 | direct credit, index ETF (SPY, LONG, ELEVATED_IV), CONFLICT 0.4 | BULL_PUT_SPREAD, width 5.0, max loss 3.5/share | $350 | $160.00 | 1 contract, dollar_risk $350.00 | +$190.00, 2.1875x BREACH |
| 2 | direct credit, index ETF, NEUTRAL 0.7 | BULL_PUT_SPREAD | $350 | $280.00 | 1 contract, $350.00 | +$70.00, 1.2500x BREACH |
| 3 | direct credit, single name (SHORT, ELEVATED_IV), CONFLICT 0.4 | BEAR_CALL_SPREAD, width 2.5, max loss 1.75/share | $175 | $160.00 | 1 contract, $175.00 | +$15.00, 1.0937x BREACH |
| 4 | direct DEBIT, index ETF, CONFLICT 0.4 | BULL_CALL_SPREAD, max loss 1.5/share | $150 | $160.00 | 1 contract, $150.00 | within budget (0.9375x) |
| 5 | direct DEBIT, single name, CONFLICT 0.4 | BEAR_PUT_SPREAD, max loss 0.75/share | $75 | $160.00 | 2 contracts, $150.00 | within budget |
| 6 | CONTINUATION credit, index ETF (entry_mode=CONTINUATION), CONFLICT 0.4 | BULL_PUT_SPREAD | $350 | $160.00 | 1 contract, $350.00 | +$190.00, 2.1875x BREACH |
| 7 | positive control: debit single name, ALIGNED 1.0 | BULL_CALL_SPREAD | $75 | $400.00 | 5 contracts, $375.00 | within budget (unchanged) |
| 8 | positive control: credit single name, ALIGNED 1.0 (two-contract case; earlier mislabeled "boundary" -- corrected, section 22) | BULL_PUT_SPREAD | $175 | $400.00 | 2 contracts, $350.00 | within budget (unchanged) |
| 9 | ONE-CONTRACT BOUNDARY: credit index ETF, ALIGNED 1.0 (added at correction; executed at the pin) | BULL_PUT_SPREAD, width 5.0, max loss 3.5/share | $350 | $400.005 | 1 contract, $350.00 | within budget: `raw_adjusted = int(400.005 // 350) = 1`, `min(1, 1) = 1` |

What this proves and does not prove:

- CONFIRMED: the breach reproduces on the ordinary path with live constants,
  for direct credit (cases 1-3) and continuation credit (case 6), at both
  CONFLICT and NEUTRAL. `final_dollar_risk` truthfully reports the breaching
  amount; nothing anywhere states it exceeds the ceiling the system computed
  one line earlier. The floor silently nullifies the correlation modifier's
  entire risk reduction (PRD-198 invariant 1 violation, exactly as ruled).
- NARROWED (new precision beyond the CB-02 row): DEBIT strategies CANNOT
  breach at current constants. Worst debit risk/contract is $150 (ETF); the
  smallest reachable ceiling is $160 (CONFLICT 0.4). Cases 4-5 confirm. The
  debit refusal cases in the regression matrix (section 15) are therefore
  structurally covered by the shared code path but reachable only under
  synthetic constants (monkeypatched budget) -- the same technique the one
  existing floor-binding test already uses (`tests/test_phase5.py:482-500`,
  which pins the budget to $150 via monkeypatch).
- Continuation: case 6 exercises the IDENTICAL lines (`options.py:228-236`);
  since PRD-256 R3 there is no continuation branch in the sizing block
  (`options.py:222-227` comment; `entry_mode` does not alter sizing). A
  continuation credit accept under CONFLICT is precisely the "first-fire"
  combination Finding D named in 2026-07-14. Note: continuation has never
  fired in production (PRD-256 R1 replay: 3,984 symbol-days, zero
  acceptances; `docs/DECISIONS.md` 2026-07-13 entry), so continuation
  coverage is code-path truth, not observed-history truth.
- NEUTRAL reachability: per the corrected CB-02 row, NEUTRAL requires a
  genuinely flat GLD or DX-Y.NYB quote (DX-Y.NYB is a HALT symbol, so
  missing/stale halts before sizing). CONFLICT needs no degraded input and
  carries the finding. Not re-litigated here; consistent with
  `correlation.py:56-63` read directly.
- Not established: how often the floor has bound historically.
  `risk_modifier` is not persisted per candidate in `audit.jsonl` (baseline
  CB-02 row, "Missing proof"). This trace does not change that.

## 4. Complete path inventory

Every path reaching the floor at `options.py:233`, verified by the lead's
call-site sweep (`rg -n "build_option_setups\(" --type py -g '!tests/**'`:
exactly one production call site) and direct reads.

There is EXACTLY ONE floor site and EXACTLY ONE production entry into it:

`runtime/__init__.py:1018-1024` (inside `_run_pipeline`, def :861), guarded by
`if qualification_summary.qualified_trades:`, passing
`risk_modifier=policy_context.risk_modifier`.

Paths INTO that call, by the shape of the `QualificationResult` consumed:

| Path | Entry point | Strategy resolution | Sizing before options | Modifier/floor application | Output carrier | Downstream consumers |
|---|---|---|---|---|---|---|
| Direct (all four strategies) | `qualify_all` -> `qualify_candidate` (`qualification.py:223`) | `_select_strategy(result.direction, sr.iv_environment)` fresh at `options.py:183` | Gate 8 (`qualification.py:460-496`): `floor(EQUITY x PCT x regime_mult / (max_loss x 100))`; REFUSES (soft-fails GATE_MAX_RISK) when < 1 | `options.py:228-233`: `raw_adjusted = int(EQUITY x PCT x risk_modifier // risk_per_contract)`; `final = max(1, min(result.max_contracts, raw_adjusted))` | `OptionSetup(max_contracts, dollar_risk)` | chain_validation, trade_decision, contract, audit, output (section 9) |
| Direct, PULLBACK_IMBALANCE entry mode | same, plus candidate `replace()` at `options.py:186-205` | same | same Gate 8 | same block; entry/stop replacement does not touch sizing | same | same |
| Continuation (EXPANSION only, credit or debit resolution) | `qualify_all` EXPANSION block -> `_qualify_continuation_candidate` (`qualification.py:255`) | same fresh `_select_strategy` at `options.py:183` (continuation results carry no strategy; synthesized candidate has `max_loss=None`) | Continuation sizer (`qualification.py:767-785`): `floor(EQUITY x PCT / (max(0.50, atr14x0.05) x 100))`, NO regime multiplier (EXPANSION=1.0 by construction), NO correlation modifier; REFUSES (`STOP_TOO_TIGHT` continuation reject) when < 1 | same `options.py:228-233` block since PRD-256 R3 -- no entry_mode branch | same | same |
| Debit vs credit | not a separate path -- resolved per symbol inside the loop | `_max_loss_for_strategy` (`options.py:414-426`): credit = width - 30% credit proxy = 70% of width; debit = 30% of width | n/a | same block; only `risk_per_contract` differs | same | same |
| Correlation states | not a separate path -- a parameter | n/a | n/a | ALIGNED 1.0 / NEUTRAL 0.7 / CONFLICT 0.4 via `compute_correlation` -> `evaluate_policy` -> `policy_context.risk_modifier` | same | same |

Paths that do NOT reach the floor (verified):

- `_QUALIFY_ONLY_MODES` branch (`runtime/__init__.py:402-423`) and
  `_HOURLY_MODES` branch (:425-460): both run `generate_candidates` +
  qualification but never call `build_option_setups`. No OptionSetup, no
  floor, no correlation modifier applied on those paths.
- Skip branches inside `build_option_setups` itself: missing StructureResult
  (`options.py:178-180`) and missing sizing (`:212-214`) `continue` before
  the floor.
- The `risk_per_contract <= 0` else-branch (`options.py:234-235`) bypasses
  the floor and passes `result.max_contracts` through unchanged. Defensively
  dead for all four known strategies (both `_max_loss_for_strategy` returns
  are strictly positive for the fixed widths 5.0/2.50); noted in section 16.

Paths that can produce a raw or adjusted count below one:

- `raw_adjusted = 0` at `options.py:232` whenever
  `risk_per_contract > EQUITY x PCT x risk_modifier`. With live constants:
  credit ETF ($350) under NEUTRAL ($280) or CONFLICT ($160); credit single
  name ($175) under CONFLICT ($160). Debit: unreachable at current constants
  (section 3). This is the ONLY sub-one production site that does not refuse.
- Gate 8 `max_c < 1` (`qualification.py:481`) and continuation sizer
  `max_contracts < 1` (`qualification.py:784`): both already refuse; neither
  emits a zero. Qualified results therefore always carry
  `max_contracts >= 1` into options.

## 5. Risk-ceiling data flow

```
config.py:70-71   ACCOUNT_EQUITY = 15000.0, MAX_RISK_PCT_PER_TRADE = 0.026667
                  (authoritative source; validated at import,
                   _validate_sizing_config, config.py:83-102)
   |
   v
base budget       EQUITY x PCT ~= $400.005
   |
   +--> Gate 8 (qualification.py:464-467)
   |      effective_target = base x REGIME_RISK_MULTIPLIER[regime]
   |      sized against candidate.max_loss (strategy-aware since PRD-251,
   |      set at options.py:388 for direct candidates)
   |      -> max_c = floor(target / (max_loss x 100))
   |      -> REFUSES at max_c < 1 (soft GATE_MAX_RISK,
   |         qualification.py:480-487)
   |      -> QualificationResult.max_contracts (>= 1 when qualified)
   |
   +--> continuation sizer (qualification.py:767-785)
   |      continuation_budget = base (no multipliers)
   |      sized against the ATR debit proxy
   |      -> REFUSES at < 1 (STOP_TOO_TIGHT)
   |
   v
options.py:228    effective_risk = base x risk_modifier      <-- CORRELATION
                  (risk_modifier: config.py:274-276 constants ->
                   correlation.py:66-70 map -> trade_policy.py:35-38
                   passthrough -> runtime/__init__.py:954-955 ->
                   :1023 keyword argument. Single chain, no other source.)
options.py:229    effective_max_loss = _max_loss_for_strategy(strategy, width)
options.py:231    risk_per_contract = effective_max_loss x 100
options.py:232    raw_adjusted = int(effective_risk // risk_per_contract)
options.py:233    final_contracts = max(1, min(result.max_contracts,
                                               raw_adjusted))     <-- THE FLOOR
options.py:236    final_dollar_risk = final_contracts x risk_per_contract
   |
   v
OptionSetup.max_contracts / .dollar_risk
   |
   +--> trade_decision.py:178-179  (contracts, dollar_risk; validator
   |      REQUIRES contracts >= 1, trade_decision.py:66-67)
   +--> contract.py:363-368        (position_size, dollar_risk)
   +--> audit.py:133-134           (contracts, dollar_risk)
   +--> output.py:361-366          ("N contracts . max risk $R")
```

Two DIFFERENT adjusted budgets exist by design: Gate 8 applies the REGIME
multiplier only; options applies the CORRELATION modifier only. The emitted
quantity is `min` of the two counts -- floored at 1. The "applicable adjusted
risk ceiling" of the ruling is the options-layer one:
`ACCOUNT_EQUITY x MAX_RISK_PCT_PER_TRADE x risk_modifier` (the ruling names
this formula verbatim, `docs/DECISIONS.md:277-282`).

## 6. Candidate seams considered

1. Qualification (Gate 8, applying the correlation modifier there).
2. Options construction (`build_option_setups`) -- the floor's own site.
3. Strategy selection (`_select_strategy`).
4. Decision assembly (`_run_decision_gates` / `create_trade_decision`).
5. Execution-policy materialization (`apply_execution_policy_to_decisions`).
6. Chain validation.
7. Runtime post-hoc filter (drop breaching setups after construction).

## 7. Recommended seam

OPTIONS CONSTRUCTION: `options.py::build_option_setups`, the exact block
`options.py:228-236`. Replace the floor with a refusal branch: when
`risk_per_contract > 0` and `raw_adjusted < 1`, emit NO OptionSetup for the
symbol and emit an explicit refusal record instead (carrier: section 10).

Truth is FIRST and FULLY available exactly there, and nowhere earlier:

- The authoritative strategy is resolved fresh at `options.py:183`
  (`_select_strategy`); continuation results have no strategy before this
  point and their synthesized candidates carry `max_loss=None`
  (`qualification.py:278`).
- The strategy-aware per-contract charge is computed at `options.py:229-231`
  from `_max_loss_for_strategy` -- the single source of that truth since
  PRD-251/PRD-256 R3.
- The correlation modifier arrives as the `risk_modifier` argument -- its
  only production application site (`config -> correlation -> trade_policy
  -> runtime :954-955 -> :1023`; single chain, verified).
- The upstream regime-budget quantity (`result.max_contracts`) is present
  and already guaranteed >= 1.

Therefore the two facts the ruling turns on -- "quantity would be zero before
flooring" and "one contract exceeds the applicable adjusted ceiling" -- are
the SAME fact at this seam (`raw_adjusted == 0` with
`risk_per_contract > 0`), known at `options.py:232`, one line above the
defect. Refusing here is fail-loud at the point where truth is determined
(PRD-198 invariants 1 and 5), duplicates nothing, and automatically covers
direct, continuation, PULLBACK_IMBALANCE, debit, credit, and every
correlation state, because they all flow through this one block (section 4).

It also PRESERVES PRD-023 R2 ("risk_modifier MUST NOT alter qualification
gate outcomes"): qualification outcomes are untouched; the candidate still
qualifies; expression refuses. The ruling is implemented without amending
the correlation layer's advisory-only qualification contract.

## 8. Rejected alternatives

1. QUALIFICATION (apply the correlation modifier inside Gate 8, reuse its
   existing refusal). Rejected:
   - Violates PRD-023 R2 explicitly (`docs/prd_history/PRD-023.md:42-45`):
     "risk_modifier MUST NOT alter qualification gate outcomes." The D-RULE
     supersedes the floor, not this layering clause (section 12).
   - Cannot cover continuation: `_qualify_continuation_candidate` never runs
     Gate 8 and sizes off an ATR proxy with no resolved strategy; covering
     it would require duplicating `_select_strategy` +
     `_max_loss_for_strategy` truth into qualification (duplicated truth)
     or accepting divergent direct/continuation behavior.
   - Changes positive-sizing behavior: Gate 8's arithmetic feeds
     `max_contracts` for EVERY candidate; compounding regime and
     correlation multipliers there changes emitted quantities in currently
     in-budget cases -- forbidden by the preservation contract.
2. STRATEGY SELECTION (`_select_strategy`). Rejected: a pure direction x IV
   map with no economics -- no budget, no modifier, no width, no quantity.
   Refusal there is unimplementable without importing all of the sizing
   truth to it (wholesale duplication).
3. DECISION ASSEMBLY (block in `create_trade_decision` /
   `_run_decision_gates`). Rejected:
   - Truth arrives late: the breaching OptionSetup already exists and chain
     validation has already spent live-chain effort on it.
   - Duplicates truth: the decision layer has no `effective_risk`; it would
     recompute the budget arithmetic from constants -- a second site that
     can drift (PRD-198 invariant 3).
   - The setup survives: `output.py:317-324` renders setups by chain
     classification, not decision status (CB-04's corrected evidence:
     blocked candidates still render). A $350 position against a $160
     ceiling would still be displayed as a formed A+ trade and audited at
     `qualified_trades[].contracts=1, dollar_risk=350` -- the ruling says
     no such setup survives.
   - Note `trade_decision.py:66-67` REQUIRES `contracts >= 1`: there is no
     zero-contract decision representation; the carrier would have to be a
     block decision wrapping a breaching setup, which is the survival
     problem again.
4. EXECUTION-POLICY MATERIALIZATION. Rejected: that seam belongs to CB-03
   (`size_rounds_to_zero`, the policy multiplier that reduces an
   already-affordable position). Placing CB-02 there conflates two findings
   (prohibited by this charge and by the reconciliation charter), arrives
   even later than seam 3, and inherits all of seam 3's defects.
5. CHAIN VALIDATION. Rejected: its concern is liquidity evidence (OI,
   spread, bid/ask); it has no budget economics and its consumers treat its
   classifications as chain truth. A budget refusal there is a category
   error and a proxy (invariant 3).
6. RUNTIME POST-HOC FILTER (drop breaching setups after `build_option_setups`
   returns). Rejected: either silently drops the candidate (the forbidden
   outcome -- see section 9's absence behaviors) or must invent its own
   refusal carrier anyway, while splitting the refusal from the arithmetic
   that determined it (a proxy re-derivation of `raw_adjusted` outside the
   authoritative site).

Summary against the charge's criteria: seams 2-6 lack required economics or
duplicate truth; seams 3-5 let the breaching setup survive or misattribute
the refusal; seam 1 changes unrelated positive sizing and creates divergent
direct/continuation behavior; only options construction has all truth, no
duplication, no divergence, and no positive-sizing impact.

## 9. Downstream-consumer matrix

Verified by the consumer sweep and personally re-run
(`rg -n "\.max_contracts|\.dollar_risk" cuttingboard/ --type py`, plus direct
reads of every join). Production only.

| Consumer | Reads | Behavior today | Behavior on refusal (recommended design) |
|---|---|---|---|
| `chain_validation.py:144-165, 175-308` | iterates setups (`symbol`, `dte`, `strategy`) | validates each setup | refused symbol never reaches it (no wasted live-chain calls); no change |
| `trade_decision.py:147, 178-179` | `setup.max_contracts`, `setup.dollar_risk`; validator requires `contracts >= 1` (:66-67) | one decision per setup | no setup -> no decision; validator invariant preserved untouched |
| `runtime/__init__.py:646-670` | `setup_by_symbol` join; PRD-260 R5 raise for setup-without-candidate | decisions built FROM setups | unchanged; refusal reduces `setup_by_symbol` only |
| `runtime/__init__.py:706-714` | `decision_is_actionable` -> outcome TRADE/NO_TRADE | actionable decision => TRADE | a refused sole candidate correctly yields NO_TRADE with a stated reason |
| `contract.py:308, 325-345, 363-368` | `position_size`/`dollar_risk` from setup; raises on decision-without-setup (:329-331, unreachable by construction) | candidates built from decisions | unchanged for surviving candidates |
| `contract.py:382-413` `_build_rejections` | today: `qual.excluded` (stage QUALIFICATION), `qual.watchlist` (stage WATCHLIST), regime (stage REGIME) | three stages only | RECEIVES the refusal as a new stage entry (section 10) |
| `audit.py:125-134` | per qualified trade, `next(...)` join to setup | ABSENT SETUP -> silent `None` for strategy/structure/dte/contracts/dollar_risk | must carry the explicit refusal (reason token + economics), not a silent null row |
| `audit.py:169-187` | decision join | decisions always have setups | unchanged |
| `output.py:317-324, 341-386` | A+ TRADES = setups with VALIDATED chains; CHAIN UNVERIFIED = setups missing chain results | a qualified symbol with NO setup appears in NEITHER block -- invisible in the report body | one explicit refusal line required (section 17 carries the only open question: whether it rides OPT-1) |
| `output.py:435-461` | WATCHLIST / NEAR_A_PLUS / EXCLUDED blocks from qual summary | refusal is in none of them | unchanged (refusal is NOT a qualification exclusion) |
| `delivery/payload.py:50-51, 133-137` | splits contract `rejections[]` by `stage == WATCHLIST` vs rest | three stages | a new stage lands in the payload's `rejected` bucket automatically (additive-tolerant split) -- but presence in the payload is NOT user-visible HTML; see the next row |
| `delivery/html_renderer.py:15-23` -> `output.py::render_report_from_payload` (:509-575) | the HTML page body is `render_report_from_payload(payload)` | the adapter reconstructs a MINIMAL report: `qualification_summary=None, option_setups=[]`, and never reads `sections.rejected` -- a refusal present in the payload is DROPPED from the rendered HTML (CORRECTED after connector review; the pre-correction matrix implied payload presence sufficed) | full truth requires the adapter to render the refusal from `sections.rejected` (`output.py`, already in FILES) + `tests/test_delivery.py` |
| `delivery/dashboard_renderer.py` | NO reads of `max_contracts`/`dollar_risk`/`size_multiplier` (verified); candidate cards from market_map; `_load_contract_entry_context` reads entry/stop/status/block_reason only | -- | no change required |
| notification body (`output.py::build_notification_message` :1008-1016, `output.py::_alert_reason` :924-935) | with zero `trade_candidates`, the alert text is `_alert_reason`, whose fallback chain is `stay_flat_reason -> regime_failure_reason -> error_detail -> "no setups"` -- it NEVER reads `contract["rejections"]` | an all-candidates-refused run alerts a generic `Reason: no setups` with no trace of the refusal (CORRECTED after connector review; the pre-correction row claimed "no format change required" -- WITHDRAWN. `state.py:58-61`'s use of `rejections[0].reason` is dedup state only, not body text) | full truth requires `_alert_reason` (or the no-candidates branch) to surface the refusal (`output.py`, already in FILES) + the asserting notification tests (`tests/test_prd017_notification_stabilization.py`, `tests/test_prd267_alert_reason_coverage.py`; exact set locked by the OPT-1 Stage-0 grep sweep) |
| `reports/postmarket.py::build_postmarket_report` (:159-161, :212-220) | counts rejections by EXACT stage literals `REGIME` / `QUALIFICATION` / `WATCHLIST`; `rejection_breakdown` exposes only those three fixed keys; `trade_summary.rejected_count` = qualification_count only | an `OPTIONS_SIZING` rejection is invisible in the postmarket report (CORRECTED after connector review; the pre-correction row claimed the stage counts "pick the new stage up mechanically" -- WITHDRAWN, the aggregation is fixed-schema, and `tests/test_postmarket_report.py:90-92` pins the exact key set, a discriminating red on any new key) | full truth requires `reports/postmarket.py` + `tests/test_postmarket_report.py` in OPT-1 |
| `reports/premarket.py:343-352` | focus list from `trade_candidates[:5]` (no size, no rejections) | -- | no change |
| `contract.py:431` `rejected_count` | `len(qual.excluded)` only | already excludes watchlist/regime | unchanged by design (pre-existing narrowness, not widened here) |
| `tools/engine_doctor.py:88` | symbol existence of `OptionSetup`, `build_option_setups` | -- | unchanged (names retained) |
| `ui/app.js:130-137, 255` | `correlation.risk_modifier` display only | -- | no change |

Absence of an OptionSetup TODAY (the decisive finding for section 15): three
consumer behaviors coexist -- silent None in audit (`audit.py:125-134`),
invisibility in the report body (`output.py:317-324`), and a hard raise only
on the never-reachable decision-without-setup join (`contract.py:329-331`).
There is NO loud, visible representation of "qualified but not expressed."
Refusal-by-omission is therefore a silent drop. CONFIRMED.

## 10. Refusal-carrier analysis

Existing carriers traced (all consumers enumerated in section 9):

| Candidate carrier | Verdict | Why |
|---|---|---|
| `QualificationSummary.excluded` dict | REJECTED | Wrong layer truth: the candidate QUALIFIED. Writing it into `excluded` from the options layer (or runtime) rewrites layer-7's record with layer-9 information, leaves `symbols_qualified` counts inconsistent unless the frozen summary is rebuilt, and lands in the contract as stage QUALIFICATION -- a misattribution |
| `QualificationResult.watchlist` / `watchlist_reason` | REJECTED | Watchlist means "exactly one soft gate missed, re-checkable." This is a terminal expression refusal; also same wrong-layer problem |
| `CONTINUATION_REJECTION_REASONS` / `rejection_reason` | REJECTED | A closed 9-token taxonomy with an enforcement test asserting exact membership (`tests/test_continuation_audit.py:175-187`) and a validator raise on unknown tokens (`qualification.py:947-948`); continuation-only semantics; direct candidates never carry it |
| Execution-policy block (`BLOCK_TRADE` + `block_reason`) | REJECTED | Requires a `TradeDecision`, which requires a setup with `contracts >= 1` (`trade_decision.py:66-67`) -- the breaching setup would have to survive to be blocked. Also the CB-03 seam; conflation prohibited |
| `SuppressedCandidate` (`sector_router.py:18-22`) | REJECTED | Closest existing SHAPE (symbol + reason, serialized at `audit.py:235`), but its meaning is "suppressed by sector router" (currently a stub, always empty). Reuse would misattribute the source of the refusal |
| Contract `rejections[]` entry (`{symbol, stage, reason, detail}`) | PARTIAL -- reusable as the CONTRACT-side representation | The dict shape needs no schema change; a NEW stage token is required (existing stages REGIME/QUALIFICATION/WATCHLIST are all untruthful for this refusal). The payload's stage split is additive-tolerant. But `rejections[]` is built inside `contract.py` from the qualification summary -- something must CARRY the refusal from options to contract assembly |

Conclusion: NO existing carrier represents this refusal truthfully
end-to-end. The minimum new carrier is:

- a small frozen dataclass in `options.py` (e.g. symbol, strategy,
  risk_per_contract, adjusted ceiling, risk_modifier, stable reason token),
  collected via a NEW OPTIONAL `refusals` out-parameter on
  `build_option_setups` -- the LIST RETURN SHAPE IS PRESERVED. (CORRECTED
  after connector review: the pre-correction text said "returned ...
  alongside the setups", i.e. a tuple return -- WITHDRAWN. A tuple return
  breaks four test files outside any proposed ceiling. Caller proof, each
  read directly: `tests/test_continuation_audit.py:337-341` calls
  `build_option_setups` and consumes the result as a list;
  `tests/test_runtime_decision.py:164` and `:644`,
  `tests/test_evaluation.py:386`, and
  `tests/test_prd161_sizing_gate_fixture.py:210` monkeypatch it as
  `lambda *a, **k: [...]` -- kwarg-tolerant but returning a plain list that
  `_run_pipeline` would fail to unpack as a 2-tuple. With the out-parameter,
  every existing caller stays valid: direct callers omit the kwarg
  (default `None`), the runtime passes `refusals=<list>`, and the
  `*a, **k` stubs swallow the kwarg while their list return remains the
  sole return value the runtime reads);
- threaded by `runtime/__init__.py` into contract assembly and audit;
- represented in the contract as ONE new `rejections[]` stage token
  (proposed: `OPTIONS_SIZING`), NOT a new top-level contract field;
- represented in the audit record explicitly (not the silent-None join);
- represented at the presentation consumers (corrected scope, section 22):
  one report line in `render_report`, the `_alert_reason` /
  no-candidates notification branch, the `render_report_from_payload`
  HTML adapter (all three in `output.py`), and the postmarket
  `rejection_breakdown` (`reports/postmarket.py`) -- subject to the
  section 17 ruling on full vs reduced surface.

This is deliberately NOT a schema expansion: no new contract key, no new
enum surface beyond one stage token and one reason token, no new artifact
path. The exact dataclass name and threading mechanics are OPT-1 design
space within this envelope.

## 11. Refusal-reason analysis

Tokens considered:

| Token | Where it lives | Semantics | Verdict |
|---|---|---|---|
| `size_rounds_to_zero` | NOWHERE in code (verified: zero hits in `cuttingboard/`, `tests/`, `scripts/`, `tools/`, `ui/`); specified in `audits/BUILD_PLAN.md:21,86` (operator decision 2, 2026-07-10) | `floor(contracts x multiplier) = 0`: an execution-policy SIZE MULTIPLIER reduces an ALREADY-AFFORDABLE, already-qualified, already-expressed position to zero at decision materialization. Belongs to CB-03, which is not implemented either | REJECTED for reuse. Semantic equivalence FALSIFIED: CB-02's condition is that the smallest expressible contract was NEVER affordable under the correlation-adjusted budget -- no multiplier, no decision, no prior valid size involved. The workplan itself warns against this reuse (OPT-0 question 6), and doctrine 6.4 forbids reuse without proven equivalence |
| `STOP_TOO_TIGHT` (continuation) | `qualification.py:58-68` | continuation proxy sizing below one contract at the UNMODIFIED budget | REJECTED: closed taxonomy, continuation-only, and names a stop-geometry cause, not a budget-ceiling cause |
| Gate 8 prose ("1 contract at $X max loss = $Y -- exceeds budget") | `qualification.py:483-487` | regime-budget refusal at qualification | Not a token (free prose), wrong budget (regime, not correlation), wrong layer |
| `ONE_SOFT_MISS`, policy block reasons (`cooldown`, `loss_lockout`, ...) | `contract.py:407`, `execution_policy.py:22-32` | unrelated semantics | REJECTED |

RECOMMENDED: new token `SMALLEST_CONTRACT_EXCEEDS_BUDGET`.

- Plain-language meaning: "The smallest expressible position -- one contract
  of the selected spread -- carries a maximum loss larger than the
  correlation-adjusted per-trade risk budget. The setup is refused; no
  position size satisfies the budget."
- Display wording (report line, exact form an OPT-1 decision within this
  envelope): `REFUSED <SYM>: smallest contract $<risk_per_contract> exceeds
  adjusted budget $<ceiling> (<STATE> x<modifier>)`.
- Audit wording: the token plus the four numbers that prove it
  (risk_per_contract, ceiling, risk_modifier, strategy).
- Why it cannot be confused with policy-size materialization: it names the
  CONTRACT (the indivisible unit) exceeding the BUDGET -- a property of the
  instrument vs the ceiling, computable before any decision exists.
  `size_rounds_to_zero` names a MULTIPLIER zeroing a size -- a property of a
  policy acting on a valid position after expression. Different inputs,
  different layers, different remedies (refuse the setup vs block the
  decision). Token style (UPPERCASE) matches the repo's stable rejection
  tokens (`CONTINUATION_REJECTION_REASONS`, `ONE_SOFT_MISS`).

## 12. PRD-157 and later-ruling reconciliation

- ORIGIN CORRECTION (NARROWED vs the workplan's framing): the floor is NOT
  PRD-157's. `git log -S` pins `final_contracts = max(1, min(...))` and the
  "Never go below 1 contract (AC4: no removal)" comment to commit `314ca46`,
  PRD-023 (GLD-DXY correlation policy layer, 2026-04-26). "AC4" resolves to
  no acceptance criterion in any PRD-023 text -- the label is unbacked; the
  substantive rationale is PRD-023 R2's advisory-only contract
  (`PRD-023.md:19,42-45`): the modifier may shrink size but may not REMOVE a
  candidate qualification accepted.
- PRD-157 (2026-05-24) PRESERVED the floor while migrating the budget to
  equity-driven sizing (`PRD-157.md:84-85`, R5: "floor-of-one semantics
  preserved", with a FAIL line pinning it). Its equity-budget change is
  untouched by this refusal and remains valid.
- PRD-251 (2026-07-10) made the breach MATERIAL: credit max loss went from
  the 30% proxy to 70% of width ($350/contract on index ETFs), turning a
  latent floor into a live 2.19x breach. Its arithmetic is correct and
  preserved.
- PRD-252 (2026-07-11) raised the budget to ~$400. Preserved.
- PRD-256 R3 (2026-07-13) unified continuation into the same block,
  making the breach surface single-sited. Preserved.
- The 2026-07-24 ruling (D-RULE) SUPERSEDES EXACTLY: the `max(1, ...)`
  floor-of-one at expression -- PRD-023's "no removal" CONSEQUENCE at the
  sizing boundary, and PRD-157 R5's floor-preservation acceptance line.
  A setup whose smallest contract breaches the adjusted ceiling is now
  correctly refused (removed at EXPRESSION, not at qualification).
- What REMAINS VALID and is NOT superseded: PRD-023 R2's qualification
  clause (the modifier still must not alter qualification gate outcomes --
  the recommended seam preserves this exactly); the advisory
  `correlation` contract block and its display consumers; the modifier
  values; PRD-157's equity budget; PRD-251's max-loss arithmetic; PRD-256
  R3's unification; Gate 8's regime-budget refusal; the continuation
  sizer's refusal.
- Test documenting the superseded behavior: exactly ONE floor-binding test
  exists, `tests/test_phase5.py:482-500`
  (`test_credit_strategy_no_candidate_uses_strategy_aware_max_loss_prd256`),
  asserting `max_contracts == 1` and `dollar_risk == 350.0` where
  `raw_adjusted == 0`. Its PURPOSE is PRD-256's strategy-aware pricing, not
  the floor; under OPT-1 it is REWRITTEN to assert the refusal (the
  strategy-aware-pricing assertion moves onto the refusal record's
  economics), not deleted. Four floor-ADJACENT tests
  (`test_phase5.py:502,521,549,578,600,942` at `raw_adjusted >= 1`) assert
  in-budget behavior and must remain green unchanged. Per the PRD-158
  pre-implementation grep sweep, `tests/test_phase5.py` is the only
  asserting test file for the floor (lead re-ran the sweep).

## 13. Positive-behavior preservation contract

Exact invariants OPT-1 must hold (all evidenced by repro cases 4, 5, 7, 8
and the floor-adjacent tests):

1. For every result where `raw_adjusted >= 1`:
   `final_contracts = min(result.max_contracts, raw_adjusted)` and
   `final_dollar_risk = round(final_contracts x risk_per_contract, 2)`,
   value-for-value identical to today.
2. Quantity exactly 1 WITHIN budget (`raw_adjusted >= 1`, e.g. credit ETF at
   ALIGNED: $350 <= $400) emits exactly as today (repro case 8's shape).
3. Dollar-risk arithmetic, rounding, and field types unchanged for every
   emitted setup.
4. Strategy selection (`_select_strategy`), DTE selection, strike
   formatting, spread-width conventions: byte-identical behavior.
5. Chain validation inputs and classifications for surviving setups:
   unchanged.
6. Correlation computation, `PolicyContext`, and the advisory `correlation`
   contract block: unchanged.
7. Debit and credit ESTIMATES (`_estimated_debit`, `_max_loss_for_strategy`):
   unchanged.
8. Gate 8 and the continuation sizer: untouched files-wise where possible;
   behaviorally identical regardless.
9. The `result.max_contracts is None` and missing-StructureResult skip
   branches: unchanged (they are missing-data shapes, not refusals --
   section 16).
10. Qualification outcomes, watchlist membership, excluded dict, counts:
    unchanged (PRD-023 R2 preserved).

## 14. Initial FILES estimate

CORRECTED after connector review (section 22). The pre-correction estimate
(5 production / 3 tests) omitted three verified consumers and assumed a
return-shape change; both errors are withdrawn.

Production, FULL-TRUTH design (6):

| Path | Reason |
|---|---|
| `cuttingboard/options.py` | The refusal branch replacing the floor; the minimal refusal dataclass; the list-API-preserving `refusals` out-parameter (NOT a return-shape change) |
| `cuttingboard/runtime/__init__.py` | The single call site (:1018-1024): pass the refusals list, thread into contract assembly and audit inputs |
| `cuttingboard/contract.py` | `_build_rejections` gains the `OPTIONS_SIZING` stage entries from the threaded refusals |
| `cuttingboard/audit.py` | Explicit refusal representation on the audit record (replacing the silent-None join shape for refused symbols) |
| `cuttingboard/output.py` | THREE touch points, one file: the report-body refusal line (`render_report`); the notification body (`_alert_reason` / the no-candidates branch, :924-935 and :1008-1016); the HTML adapter (`render_report_from_payload` :509-575 rendering `sections.rejected`) |
| `cuttingboard/reports/postmarket.py` | `rejection_breakdown` / counts (:159-161, :212-220) gain the new stage so the postmarket report does not silently omit refusals |

Tests, FULL-TRUTH design (6 named; the OPT-1 Stage-0 PRD-158 grep sweep is
the final lock):

| Path | Assertion surface |
|---|---|
| `tests/test_phase5.py` | Rewrite the one floor-binding test (:482-500) to assert refusal + refusal-record economics; add direct/continuation, debit/credit, NEUTRAL/CONFLICT refusal cases; the repro-case-9 one-contract boundary; positive-preservation cases; report-line rendering |
| `tests/test_contract.py` | `rejections[]` carries the new stage + token; surviving candidates unchanged (the existing sizing-passthrough tests stay green) |
| `tests/test_audit.py` | Audit record carries the explicit refusal; no silent-None row for a refused symbol; existing sourcing test stays green |
| `tests/test_postmarket_report.py` | `rejection_breakdown` key-set test (:90-92) updated for the new stage; new count assertion |
| `tests/test_prd017_notification_stabilization.py` (+ `tests/test_prd267_alert_reason_coverage.py` if the `_alert_reason` fallback-chain edit moves its asserted strings) | All-refused run alerts the refusal, not generic `no setups` |
| `tests/test_delivery.py` | `render_report_from_payload` / `render_html` output contains the refusal when `sections.rejected` carries an `OPTIONS_SIZING` entry |

Documentation/contract files genuinely required (bookkeeping-class, outside
the production ceiling per the charge template's lifecycle rule):

| Path | Reason |
|---|---|
| `docs/prd_history/PRD-NNN.md` (OPT-1's own PRD, number assigned at Stage 0) | Required by process; no number allocated here |
| `docs/trade_qualification.md` | Documents sizing behavior that changes at the expression step (docs-match-code); exact edit scoped in OPT-1 |
| `docs/SCHEMA_MAP.md` / `docs/CALL_SITE_MAP.md` | Only if the recon maps index the changed symbols -- verify at OPT-1 Stage 0; not assumed |

Excluded (plausible but deliberately NOT required):

- `cuttingboard/qualification.py` -- untouched (seam choice preserves it).
- `cuttingboard/trade_decision.py`, `execution_policy.py`,
  `chain_validation.py`, `correlation.py`, `trade_policy.py`, `config.py` --
  no behavior change at those seams.
- `cuttingboard/delivery/payload.py` -- the stage split (:50-51) is
  additive-tolerant; no edit (the HTML gap is in the ADAPTER,
  `output.py::render_report_from_payload`, which IS in scope).
- `cuttingboard/delivery/html_renderer.py` -- delegates wholesale to
  `render_report_from_payload`; fixing the adapter fixes the page; no edit.
- `cuttingboard/delivery/dashboard_renderer.py`,
  `cuttingboard/notifications/formatter.py`,
  `cuttingboard/notifications/state.py` -- no size/rejection-body reads
  requiring change (state.py's dedup key tolerates the new reason string).
- `cuttingboard/reports/premarket.py` -- reads `trade_candidates` only.
- `cuttingboard/runtime/_types.py` -- only needed if the refusal list is
  added to `PipelineResult`; the minimal design threads it as locals within
  `_run_pipeline` -> `_build_and_finalize_contract` params. If typing forces
  it in, it is a FILES amendment at Stage 0, not a silent expansion.
- `tests/test_runtime_decision.py`, `tests/test_evaluation.py`,
  `tests/test_prd161_sizing_gate_fixture.py`,
  `tests/test_continuation_audit.py` -- kept OUT by the out-parameter
  carrier design (section 10 caller proof); a return-shape change would
  have pulled all four in. (CORRECTED: the pre-correction text excluded
  `tests/test_delivery.py` on a fixture argument -- WITHDRAWN; it is now a
  required test file for the HTML adapter.)

## 15. Required regression matrix

| # | Case | Expected |
|---|---|---|
| 1 | Direct debit below one (synthetic budget -- unreachable at live constants, section 3) | REFUSED: no setup, refusal record with token + economics |
| 2 | Direct credit below one (live constants, CONFLICT) | REFUSED; numbers of repro case 1 |
| 3 | Continuation debit below one (synthetic budget) | REFUSED via the same block |
| 4 | Continuation credit below one (live constants, CONFLICT; repro case 6) | REFUSED; identical to direct case 2 economics |
| 5 | Correlation NEUTRAL (0.7), credit ETF (repro case 2) | REFUSED at $280 ceiling |
| 6 | Correlation CONFLICT (0.4), credit single name (repro case 3) | REFUSED at $160 ceiling |
| 7 | Quantity exactly one and WITHIN budget (repro case 9: ALIGNED credit ETF, $350 risk/contract vs $400.005 ceiling, `raw_adjusted = 1`) -- CORRECTED, the pre-correction row cited the two-contract case 8 | EMITTED unchanged: exactly 1 contract, $350.00. Goes RED if the refusal condition is written `raw_adjusted <= 1` instead of `< 1` (off-by-one refuses an affordable one-contract position) |
| 8 | Quantity above one (repro cases 5, 7) | EMITTED unchanged, value-for-value |
| 9 | Missing/unavailable economics (`max_contracts is None`, missing StructureResult) | Existing skip behavior unchanged -- and NOT converted to the refusal token (distinctness test, section 16) |
| 10 | Positive-sizing arithmetic sweep (parametrized over strategies x modifiers with `raw_adjusted >= 1`) | Byte/value-identical to pre-change |
| 11 | Audit representation | Refused symbol: explicit token + economics on the audit record; NOT a silent-None qualified row |
| 12 | Presentation representation | Refused symbol visible on the report surface (or per the section 17 ruling); never in A+ TRADES / CHAIN UNVERIFIED |
| 13 | Contract representation | `rejections[]` entry with the new stage + token; payload split lands it in `rejected`; `assert_valid_contract` passes |
| 14 | Refusal reason stability | Exact token string pinned by test (the CB-03 lesson: an operator-approved reason that exists nowhere in code) |
| 15 | Outcome derivation | Sole candidate refused -> `NO_TRADE`, not `TRADE`; no actionable decision exists |
| 16 | ALIGNED (1.0) unchanged | Modifier 1.0 can only refuse what the base budget already could not afford; with `result.max_contracts >= 1` from Gate 8, ALIGNED never refuses when Gate 8 and options agree on max loss -- pinned as a test so the refusal cannot fire spuriously |
| 17 | Postmarket representation (added at correction) | `build_postmarket_report` on a refusal-run contract exposes the refusal in `rejection_breakdown`; the key-set pin (`tests/test_postmarket_report.py:90-92`) updated and green |
| 18 | Notification body (added at correction) | An all-candidates-refused run's alert body names the refusal, not generic `no setups`; dedup state unaffected |
| 19 | HTML delivery (added at correction) | `render_html` / `render_report_from_payload` output on a payload whose `sections.rejected` carries the `OPTIONS_SIZING` entry contains the refusal text |

## 16. Mutation-red design

Each mutation must turn at least one named test red:

1. RESTORE THE FLOOR: revert the refusal branch to
   `final_contracts = max(1, min(result.max_contracts, raw_adjusted))`.
   Red: matrix cases 1-6 (a setup is emitted where refusal is asserted;
   the rewritten `test_phase5.py` floor test fails on both the emitted
   setup and the missing refusal record).
2. BYPASS FOR ONE STRATEGY CLASS: reinstate an
   `entry_mode == ENTRY_MODE_CONTINUATION` exclusion (the exact pre-PRD-256
   shape) or a credit-only/debit-only guard around the refusal.
   Red: matrix cases 3-4 (continuation) or 1-2 (class asymmetry) -- the
   direct and continuation refusal tests assert through the same public
   call with only `entry_mode`/strategy varying.
3. DROP THE EXPLICIT REASON: emit the refusal record with `reason=None`,
   a different token, or free prose.
   Red: matrix case 14 (exact-token pin) and case 11 (audit wording).
4. SILENTLY OMIT THE CANDIDATE: refuse (no setup) but emit no refusal
   record (the `continue` shape of the existing skip branches).
   Red: matrix cases 11-13 -- audit, presentation, and contract assertions
   all require the affirmative record, not just absence of the setup.
5. WRONG-BUDGET REFUSAL: compute the ceiling without `risk_modifier` (or
   with the regime multiplier).
   Red: matrix cases 5-6 vs 16 -- NEUTRAL/CONFLICT refusal thresholds and
   the ALIGNED never-spuriously-refuses pin disagree with any other
   formula.
6. OFF-BY-ONE REFUSAL (added at correction): write the refusal condition
   as `raw_adjusted <= 1` instead of `< 1`.
   Red: matrix case 7 (repro case 9) -- the affordable one-contract
   ALIGNED credit-ETF position is wrongly refused.
7. SURFACE OMISSION (added at correction): render the refusal in the
   report but drop it from any one of postmarket / notification body /
   HTML adapter.
   Red: matrix cases 17-19 respectively -- each surface has its own
   discriminating assertion.

## 17. Dustin decisions

REWRITTEN at the connector correction cycle (section 22). The original
section posed report-line-vs-4-file-ceiling; Dustin approved the 5-file
design 2026-07-31 -- but that approval was given on incomplete evidence
(the pre-correction consumer matrix), so the surface question reopens
honestly rather than being inferred as approved at the larger size.

REQUIRES DUSTIN RULING -- full-truth surface vs reduced surface:

  (A) FULL-TRUTH DESIGN (RECOMMENDED): 6 production files (the approved
      five plus `reports/postmarket.py`), ~6 test files (the approved
      three plus `test_postmarket_report.py`, the asserting notification
      test(s), `test_delivery.py`), ~90-140 net LOC. Every existing
      consumer of rejections -- report body, notification body, HTML
      page, postmarket report, audit, contract -- states the refusal.
      This is what "explicit and stable at every existing
      presentation/audit consumer" actually costs.
  (B) SMALLEST DEFENSIBLE REDUCED DESIGN: the previously approved 5/3
      surface (report line only on the presentation side). Omits:
      postmarket `rejection_breakdown` (refusal invisible in the
      postmarket report), notification body (an all-refused run alerts
      generic "no setups"), HTML page (refusal absent from the delivered
      page). Temporarily truthful ONLY if those three omissions are
      recorded as named, dated presentation debt (the PRD-259 E/F/G
      precedent) with the audit record and contract `rejections[]` as
      the interim durable truth -- and honestly NOT compliant with a
      literal reading of "every existing presentation consumer".
This trace recommends (A) and proceeds on neither without the ruling.

## 18. Gate A recommendation for OPT-1

Exact ruling text Dustin can approve verbatim:

> OPT-1 Gate A -- APPROVED as follows.
> Seam: `cuttingboard/options.py::build_option_setups`. When
> `risk_per_contract > 0` and `int(effective_risk // risk_per_contract) < 1`,
> emit no OptionSetup and emit an explicit refusal record. The
> `max(1, ...)` floor is removed. The `min(result.max_contracts,
> raw_adjusted)` arithmetic for `raw_adjusted >= 1` is preserved
> value-for-value.
> Carrier: a minimal frozen refusal dataclass collected via an optional
> list-API-preserving `refusals` out-parameter on `build_option_setups`
> (return shape unchanged); threaded by `runtime/__init__.py` into
> (i) contract `rejections[]` as new stage `OPTIONS_SIZING`, (ii) the
> audit record, and (iii) the presentation surfaces per the section 17
> ruling: report line + notification body + HTML adapter (all in
> `output.py`) and postmarket `rejection_breakdown`
> (`reports/postmarket.py`). No new top-level contract field, no new
> artifact path, no schema expansion beyond the stage key.
> Reason: new stable token `SMALLEST_CONTRACT_EXCEEDS_BUDGET`, meaning "one
> contract of the selected spread has max loss exceeding
> ACCOUNT_EQUITY x MAX_RISK_PCT_PER_TRADE x risk_modifier." Reuse of
> `size_rounds_to_zero` is rejected on proven non-equivalence.
> FILES ceiling [option A, recommended]: production exactly {options.py,
> runtime/__init__.py, contract.py, audit.py, output.py,
> reports/postmarket.py}; tests exactly {test_phase5.py, test_contract.py,
> test_audit.py, test_postmarket_report.py,
> test_prd017_notification_stabilization.py (+
> test_prd267_alert_reason_coverage.py if its asserted strings move),
> test_delivery.py} with the final test set locked by the Stage-0 PRD-158
> grep sweep; lifecycle bookkeeping per process; <= 140 net production
> LOC; any further file is a stop-and-amend.
> Regression: the section 15 matrix in full, including the synthetic-budget
> debit cases, the ALIGNED no-spurious-refusal pin, the repro-case-9
> one-contract boundary, the postmarket/notification/HTML rows, and the
> exact-token pin.
> Mutation gate: the seven section 16 mutations verified red.
> Preservation: the section 13 invariants; Gate 8, the continuation sizer,
> qualification outcomes, and all estimate arithmetic untouched.
> Non-goals: no fractional contracts, no rounding up, no threshold or
> budget change, no CB-01/03/04 work, no live-chain economics, no
> provider work, no refactor beyond the named seam.
> Lane/class: HIGH-RISK / EXECUTION (PRD_PROCESS CLASS matrix; sizing is
> EXECUTION-class, T0). Stage-0 PRD first; one fresh-context review pinned
> to the final implementation SHA; second-model per the standing PRD-242
> disposition; draft PR; manual merge.

## 19. What Gate A approval would authorize

- Allocating the OPT-1 PRD number and landing its Stage-0 scaffold.
- Implementing exactly the seam, carrier, reason, FILES set, regression
  matrix, and mutation gate above.
- The PRD-158 pre-implementation grep sweep re-run at Stage 0 and the FILES
  lock derived from it.
- One draft PR, held for Dustin, with same-PR closeout per PRD-229.

## 20. What Gate A approval would not authorize

- Any change to budgets, modifiers, regime multipliers, or thresholds.
- Any qualification-layer change (Gate 8, continuation sizer, taxonomies).
- Any CB-03 work (`size_multiplier` materialization, `size_rounds_to_zero`),
  CB-01, CB-04, PRD-271, or any other finding -- no bundling.
- Any live-chain, provider, schema, dependency, workflow, or cadence work.
- Touching the `risk_per_contract <= 0` defensive branch
  (`options.py:234-235`): a distinct failed-computation shape, currently a
  silent passthrough, defensively dead for all four strategies. Recorded
  here as retained-with-reason; if Dustin wants it fail-loud, that is a
  separate micro-scope, not OPT-1 creep.
- Merging anything. Every PR stays draft and human-held.

Definitions the implementation must keep distinct (charge question 16):

- MISSING DATA: no StructureResult (`options.py:178-180`) or
  `max_contracts is None` (`:212-214`) -- existing skip branches, unchanged,
  never labeled with the refusal token.
- UNAVAILABLE DATA: stale/absent correlation inputs -> NEUTRAL state or
  upstream HALT (`correlation.py`, HALT_SYMBOLS) -- upstream of this seam.
- MALFORMED DATA: validation-layer and contract-validator concerns -- not
  this seam.
- FAILED COMPUTATION: `risk_per_contract <= 0` -- the defensive branch
  above; distinct from refusal.
- ECONOMICALLY VALID CALCULATION RESOLVING BELOW ONE CONTRACT: inputs
  present, arithmetic sound, result honest -- `raw_adjusted == 0` with
  `risk_per_contract > 0`. THE refusal case, and the only one that gets
  the new token.

## 21. Ceiling reality check -- and what was not checked

CORRECTED at the connector cycle (section 22). Ceiling (workplan OPT-1:
<= 4 production files, <= 3 test files, <= 100 net production LOC, no
dependency/workflow/schema/unrelated-refactor) versus the corrected
full-truth design:

- Production-file ceiling: NOT MET -- 6 files. Beyond the pre-correction
  five, `reports/postmarket.py` is forced by its fixed-stage aggregation
  (:159-161, :212-220); the notification-body and HTML-adapter gaps land
  inside `output.py` (already counted) but were unpriced pre-correction.
- Test-file ceiling: NOT MET -- ~6 files (adds
  `test_postmarket_report.py`, the asserting notification test(s),
  `test_delivery.py`); the Stage-0 PRD-158 grep sweep is the final lock.
- LOC ceiling: NOT reliably met -- corrected estimate ~90-140 net.
  Stated as an estimate, not a promise; breach is a stop condition.
- No-dependency/workflow/schema: MET (one stage token + one reason token,
  no schema key beyond the stage value).
- The pre-correction "5 production / 3 tests / ~60-100 LOC" figures, and
  Dustin's 2026-07-31 approval OF those figures, were based on the
  incomplete pre-correction consumer matrix. Neither is preserved here
  merely because it was approved; section 17 puts the corrected choice
  back to Dustin explicitly.

Not checked (explicitly out of this trace's evidence):

- Live-chain economics; every dollar figure is the estimate arithmetic
  (30%/70% of width) the repo itself documents as estimated.
- Historical frequency of the floor binding (audit does not persist
  `risk_modifier` per candidate; unchanged limitation from the baseline).
- The payload/dashboard handling of a new rejection stage was traced
  statically (additive-tolerant split at `payload.py:50-51`) but not
  executed with a synthetic contract; OPT-1's realizability check owns
  running it.
- The 18 UNKNOWN baseline rows (CB-30..47) and every other finding: not
  touched, per charter.
- Full test suite: not run for this docs-only artifact (no production or
  test file changes; CI on the PR is the deciding run for tree health).
- The hourly/qualify-only branches were verified not to reach
  `build_option_setups` by direct read (:402-460); their notification
  content was not otherwise audited.

## 22. What the connector review changed (correction cycle, 2026-07-31)

Five P2 inline threads on PR #184 (all from `chatgpt-codex-connector[bot]`
against the original head `4d51e84`). Every one was re-verified by the
lead directly against code before disposition; all five were CORRECT.
This is the one bounded correction cycle; corrections are recorded in
place above with explicit withdrawal notes, per the baseline convention.

| Thread (comment id) | Finding | Disposition | What changed |
|---|---|---|---|
| 3694043067 | A return-shape change to `build_option_setups` breaks four test files outside the 3-file ceiling | ACTIONED | Section 10 carrier rewritten to the list-API-preserving `refusals` out-parameter with a per-caller proof (stubs are `lambda *a, **k: [...]`; direct caller at `test_continuation_audit.py:337-341`); sections 2/14/18 updated |
| 3694043070 | Postmarket aggregation counts fixed stage literals; `OPTIONS_SIZING` would be silently omitted | ACTIONED | Verified `postmarket.py:159-161, 212-220` and the key-set pin `test_postmarket_report.py:90-92`; the pre-correction "picks the new stage up mechanically" claim WITHDRAWN; `reports/postmarket.py` + `test_postmarket_report.py` added to the full-truth surface (sections 9/14/15/18/21) |
| 3694043072 | Notification body falls back to generic `no setups`; `_alert_reason` never reads `rejections[]` | ACTIONED | Verified `output.py:924-935, 1008-1016`; the pre-correction "no format change required" claim WITHDRAWN; notification body added to the `output.py` scope with its asserting tests (sections 9/14/15/18) |
| 3694043073 | `render_report_from_payload` ignores `sections.rejected`, so the delivered HTML drops the refusal | ACTIONED | Verified `html_renderer.py:15-23` delegation and `output.py:509-575` (adapter renders with `qualification_summary=None, option_setups=[]`); adapter + `test_delivery.py` added to the full-truth surface (sections 9/14/15/18) |
| 3694043075 | The cited one-contract boundary fixture is a two-contract case | ACTIONED | Repro case 8 relabeled positive control; NEW case 9 executed at the pin (ALIGNED credit ETF: $350 risk/contract, $400.005 ceiling, `raw_adjusted = 1`, emits exactly 1 contract); matrix case 7 rewritten with the `<= 1` off-by-one red condition; mutation 6 added |

Net effect on the conclusion: seam, carrier dataclass, reason token, and
every rejected-alternative argument are unchanged. What changed is the
honest cost of full presentation truth (6 production / ~6 test files /
~90-140 LOC) and the carrier's compatibility mechanism (out-parameter,
not tuple return). The prior 5/3 approval is explicitly reopened in
section 17 rather than silently inherited.

---

Every load-bearing claim above carries its evidence inline. Dispositions
used: CONFIRMED (breach repro, single floor site, single call site,
consumer behaviors, token absence, origin commit, and all five connector
findings); NARROWED (debit unreachability at live constants; PRD-157 ->
PRD-023 origin correction); FALSIFIED (`size_rounds_to_zero` semantic
equivalence; the pre-correction postmarket/notification/HTML tolerance
claims, withdrawn in place); REQUIRES DUSTIN RULING (exactly one,
section 17). Nothing here is CONFIRMED on a prior artifact's authority
alone.
