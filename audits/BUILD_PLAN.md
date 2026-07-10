# Build Plan — Reconciled Findings → PRD Sequence

**Date:** 2026-07-10
**Source of truth:** `audits/RECONCILED_FINDINGS.md` (tiers and severities settled; not re-litigated here).
**Evidence trail:** `audits/CODEX_REVIEW.md`, `audits/FABLE_REVIEW.md`, `audits/FINDINGS.md`.
**Operator decisions taken as given:**
- **Build order: SURFACE-FIRST.** A1 → F-02 → F-01, then the rest of Tier 2, then Tiers 3+. Fence (F-04/F-05) early but not first (operator reviews every merge; delegation risk not yet live).
- **A3 doctrine: ACTUAL-TRADES-ONLY, minimal fix.** Current counting of surfaced ALLOW_TRADE recommendations as trades is a wiring bug. Fix = brakes go dormant absent a validated trade source. No journal integration built now; documented as a future option.

**PRD numbers below are tentative** (next free number is 251; actual numbers assigned by `scripts/prd_open.sh` at Stage 0). Every FILES list here is the plan-level estimate; each PRD's authoritative FILES lands at authoring via `prd-authoring-verified` **plus the PRD-158 grep sweep** — several of these changes touch tokens (`dollar_risk`, `spread_width`, `kill_switch`, `pct_change`) asserted across 20+ test files, so expect FILES to grow with asserting-test entries at authoring time.

**Lane note:** A1a, F-02, F-01, A2, A3 all change the live decision path. Expect HIGH-RISK lane per the PRD_PROCESS matrix, which means each carries the PRD-242 second-model disposition (artifact or the exact waiver sentence) at close. F-04/F-05 are governance guardrails → MANUAL-MERGE-ONLY regardless of lane.

---

## Operator decisions recorded 2026-07-10 (plan is approved and decision-complete)

The four decisions flagged for sign-off at plan presentation are settled. This section is the record; the per-PRD text below has been updated to match.

1. **A1 split into A1a (risk arithmetic) / A1b (chain both-leg pricing): APPROVED as planned.** Two PRDs, A1a first, seam left for A1b's live economics.
2. **A2 zero-contract case: APPROVED — explicit `size_rounds_to_zero` policy block** when `floor(contracts × multiplier) = 0`. Do NOT round up to 1.
3. **A3: APPROVED — fully dormant, including the same-run in-run counter** (not just cross-run history). Brakes stay wired but starved; journal integration remains documented-future, not built.
4. **A1a's credit-spread budget consequence: ACCEPTED, handled by a SEPARATE config change** — raise the risk budget cap from $150 to $400 (a one-line constant change, its own change/PRD, NOT bundled into A1a's arithmetic fix). Rationale: this widens the qualifying window for high-IV credit spreads now that their true ~2.3x max loss is shown; the operator holds the real position-size limit personally and will stay well below the cap. It is a preference knob, not a correctness fix — single-concern, separate from A1a. It slots immediately after A1a in the sequence (numbering assigned at `prd_open` like the rest).

Not ruled on (stays a recommendation, decided when reached): the Tier-4 quorum-floor pull-forward.

---

## Wave 1 — the money numbers (operator-set head of sequence)

### PRD-251 (A1a) — Credit-spread max risk: strategy-aware max-loss arithmetic — Tier 0, CRITICAL
**Single concern:** the risk number on the decision surface is wrong ~2.3x for credit spreads.

**Specific change:**
- `options.py`: spread economics become strategy-aware. Today one proxy (`spread_width` = 30% of strike distance, documented as "estimated net DEBIT") is used for all four strategies. For credit strategies (BULL_PUT_SPREAD, BEAR_CALL_SPREAD): estimated credit = 30% of width (same proxy), **max loss/share = width − estimated credit** (i.e., 70% of width). For debit strategies max loss = the debit (unchanged). Carry an explicit per-share `max_loss` through TradeCandidate/OptionSetup rather than overloading `spread_width` — leave a seam so PRD-256 (A1b) can later substitute live chain economics for the 30% proxy.
- `qualification.py:425-441` (Gate 8): `spread_cost` sizes off max-loss, not the debit proxy; `dollar_risk` = contracts × max-loss × 100.
- `output.py:345-350` needs no logic change (renders `setup.dollar_risk`), but its rendered string is an asserting surface — sweep tests.

**FILES (estimate):** `cuttingboard/options.py`, `cuttingboard/qualification.py`, `tests/test_qualification.py`, `tests/test_account_equity_sizing.py`, `tests/test_prd161_sizing_gate_fixture.py`, plus every test the PRD-158 sweep finds asserting `spread_width`/`dollar_risk` values (~20 files match the token; the sweep decides which actually assert credit-path arithmetic).

**Test that proves it (red before / green after):** a $5-wide BULL_PUT_SPREAD candidate: per-contract risk asserts **$350, not $150**; under the default $150 effective budget Gate 8 yields **0 contracts (GATE_MAX_RISK soft-fail)**, where pre-fix it yielded 1 contract at "$150 max risk". Debit-spread control case asserts unchanged sizing.

**Behavioral consequence to state in the PRD (not a side effect — the point):** credit spreads are selected exactly in ELEVATED/HIGH IV, and at true max-loss many will stop fitting the current risk budget. Fewer/no credit-spread ALLOWs at current `ACCOUNT_EQUITY × MAX_RISK_PCT` is the *correct* behavior; the prior allows were understated risk. Downstream-consumer audit: evaluation records, dashboard candidate board, notification lines all shift. **Settled 2026-07-10 (decision 4):** the consequence is accepted and offset by a separate one-line config change raising the risk budget cap $150 → $400 — its own PRD, immediately after A1a, never bundled into the arithmetic fix.

**Stage 0 update (2026-07-10):** opened as PRD-251, confirming the tentative number above. `tests/test_phase5.py` (options.py's own credit-strategy test file) was added to FILES during the sweep — not in the original estimate, but it directly exercises `_select_strategy`/`build_option_setups` on the credit strategies this PRD touches. **The EXPANSION-regime continuation path (`_qualify_continuation_candidate`, `qualification.py:630-730`) was proposed for fold-in at Gate A, then descoped once Stage 0 code inspection showed it estimates its debit proxy through an independent ATR-based formula with no width term — a materially different fix, not the same width-minus-credit correction.** PRD-251 ships Gate 8 only. The continuation-path fix is tracked as a fast-follow, not floating: `docs/prd_history/PRD-251.continuation-path.proposal.md` (needs its own Gate A before build; see `docs/DECISIONS.md` 2026-07-10). Slot it after PRD-251 once numbered, timing TBD relative to PRD-256 (A1b).

### PRD-252 (F-02) — Missing/NaN pct_change fails loud — Tier 1, HIGH (root cause)
**Single concern:** a fabricated zero silently disarms every percentage-based stress guard (kill-switch pct legs, CHAOTIC override, regime vote coloring).

**Specific change:**
- `ingestion.py:303-312`: missing/invalid `previous_close` **raises** inside `_yfinance_quote_raw` — the existing retry wrapper then emits `fetch_succeeded=False` with a `failure_reason`, instead of a valid-looking quote with `pct_change=0.0` at DEBUG.
- `normalization.py:96-109` (the twin): NaN `pct_change_raw` becomes a normalization failure (quote dropped, ERROR-logged) instead of `0.0`.
- Resulting semantics, deliberately: a halt symbol (SPY, ^VIX, DX-Y.NYB, ^TNX, QQQ) with missing prev-close → validation **halt** (fail-loud, correct); an optional symbol (IWM, BTC-USD) → visible dropout in the validation summary.

**FILES (estimate):** `cuttingboard/ingestion.py`, `cuttingboard/normalization.py`, `tests/test_phase1.py` (+ whichever ingestion/normalization tests the sweep finds asserting the 0.0 fallback).

**Test that proves it:** (1) quote with `previous_close=None` → `fetch_succeeded=False`, no fabricated 0.0; (2) NaN pct → no NormalizedQuote emitted; (3) integration-level red test: SPY prev-close missing → `system_halted=True`, and specifically NOT a calm-looking kill-switch/regime evaluation.

**Noted, deliberately not scoped here:** `_kill_switch` itself defaults missing SPY/VIX inputs to 0.0 (`runtime/__init__.py:2166-2169`) — currently shielded because those are halt symbols and the call sites are halt-guarded. Record as an observation in the PRD; widening scope to it would violate the one-concern rule.

### PRD-253 (F-01) — Hourly path evaluates the kill switch; no more hardcoded `False` — Tier 2, CRITICAL
**Single concern:** one of two live channels never checks market stress and affirmatively reports `kill_switch: False`.

**Specific change:**
- `runtime/__init__.py` `_execute_notify_run`: after `compute_regime`, evaluate `_kill_switch(regime, valid_quotes)`. When tripped: suppress the candidate branch (no `candidate_lines`; same "no new entries" semantics as the daily HALT), and thread the real value through.
- Replace the literal `"kill_switch": False` at `runtime/__init__.py:1946` (`_build_hourly_run_summary`) with the evaluated value; hourly contract gets the same treatment if it carries the field.
- `notifications/formatter.py`: hourly alert renders the halt state (kill-switch-tripped language) instead of candidate lines.
- **Carry the CHAOTIC-mirror nuance into the PRD text** (per reconcile): the vix_pct>0.15 leg is already mirrored via CHAOTIC→STAY_FLAT (`regime.py:290`, disarmable by F-02 — hence PRD-252 lands first); the net-new protection is the VIX>35 sustained leg and the |SPY|>3% leg, plus truthful reporting on all three.
- Explicitly minimal: this **inserts** the check into the hourly sequence; it does not de-triplicate the pipeline (F-11 stays acknowledged debt, Tier 6).

**FILES (estimate):** `cuttingboard/runtime/__init__.py`, `cuttingboard/notifications/formatter.py`, `tests/test_hourly_alert.py`, `tests/test_notifications.py`, plus sweep results for `kill_switch` assertions (dashboard tests read the field via `_req`).

**Test that proves it:** hourly run with VIX=40 without a >15% spike (CHAOTIC does NOT fire) → no candidate lines, summary `kill_switch: true`, alert body carries halt language. Second case: SPY −4%. Mutation check: removing the hourly `_kill_switch` call turns both red.

**Sequencing constraint (from reconcile, operator-confirmed):** F-02 before F-01 — otherwise the new hourly check can be silently disarmed on day one by the fabricated zero, and F-01's stress tests would be written against fabricable inputs.

---

## Wave 2 — complete Tier 0

### PRD-254 (A2) — Policy size multiplier materializes into contracts/dollar_risk — Tier 0, HIGH
**Single concern:** `size_multiplier` is computed but never resizes anything; trader-facing surfaces render pre-policy size.

**Specific change:**
- One materialization step after execution policy: final `position_size` / `dollar_risk` derived from the **correlation-adjusted** setup × `size_multiplier` (Codex confirmed contract sizing currently predates both correlation and policy). Single function, consumed by both `contract.py` (`position_size`, `dollar_risk`) and `output.py:345-350` (report line) so the two surfaces cannot disagree.
- **Rounding rule (settled 2026-07-10, decision 2):** `contracts_eff = floor(contracts × multiplier)`; when that is 0 (e.g., 1 contract × 0.5), the decision downgrades to a policy block with the explicit reason `size_rounds_to_zero`. Never round up to 1 (that would un-apply the cut); never fabricate fractional risk.

**FILES (estimate):** `cuttingboard/execution_policy.py` (or a small materialization helper), `cuttingboard/contract.py`, `cuttingboard/output.py`, `cuttingboard/runtime/__init__.py` (wiring), `tests/test_execution_policy.py`, `tests/test_contract.py`, `tests/test_contract_finalization.py`, `tests/test_prd162_reconciliation.py` + sweep.

**Test that proves it:** setup 2 contracts / $300 risk, policy multiplier 0.5 → report prints "1 contract — max risk $150"; contract exports `position_size: 1`, `dollar_risk: 150.0`, `size_multiplier: 0.5`. Never again the Codex-demonstrated inconsistent triple `{0.5, 2, 300}`. Plus the floor-to-zero case per the rounding decision.

**Ordering constraint:** after PRD-251 (A1a) — A1a changes the dollar_risk base the multiplier applies to; landing A2 first would mean writing its fixtures against the understated risk base and rewriting them a week later.

### PRD-255 (A3, minimal) — Trade brakes count only confirmable actual trades (dormant until a validated source exists) — Tier 0, HIGH
**Doctrine (operator-set):** actual-trades-only. Counting surfaced ALLOW_TRADE recommendations as trades is a wiring bug. **No journal integration now.**

**Specific change:**
- `execution_policy.py` `load_execution_session_state`: stop deriving `prior_trade_count` / `last_trade_at_utc` from ALLOW_TRADE audit records (`:94-103`) and stop deriving `consecutive_losses` from hypothetical evaluation records (`_load_consecutive_losses`). Absent a validated trade source, the function returns dormant state (0 / 0 / None). Keep `ExecutionSessionState` and the gate checks (`session_trade_limit`, `loss_lockout`, `cooldown` at `:224-229`) intact — the brakes stay wired, starved of phantom input, ready for a future validated source.
- **In-run counting (settled 2026-07-10, decision 3):** `apply_execution_policy_to_decisions:150-152` also advances `trade_count`/`last_trade_at` per same-run ALLOW — same-run recommendations are not fills either. Fully dormant: the in-run counter stops advancing the trade brakes too, not just the cross-run history.
- `evaluation.jsonl` **keeps being written** — it serves the VISION trap-loop (awareness); only execution_policy stops consuming it as loss evidence.
- Realizability discipline (author discipline 3): `POLICY_SESSION_TRADE_LIMIT` / `POLICY_LOSS_LOCKOUT` / `POLICY_COOLDOWN` become currently-unrealizable output channels — declare them defensive-against-future-routing in the PRD and in `docs/PROJECT_STATE.md`; one `docs/DECISIONS.md` entry records the actual-trades-only ruling and the deferred journal-integration option (`manual_journal.py` as the natural future source — documented, not built).

**FILES (estimate):** `cuttingboard/execution_policy.py`, `cuttingboard/runtime/__init__.py` (call-site args if simplified), `tests/test_execution_policy.py`, `tests/test_trade_policy.py`, `docs/PROJECT_STATE.md`, `docs/DECISIONS.md` + sweep for tests asserting cooldown/lockout/limit firing from audit/evaluation fixtures.

**Test that proves it:** audit log with 2 prior same-day ALLOW_TRADE records + evaluation log with 2 hypothetical STOP_HITs → session state is dormant; a fresh ALLOW candidate is NOT blocked by session_trade_limit / loss_lockout / cooldown (each of Codex's three worked examples becomes a red test of the old behavior). Companion test pins the seam: with test-injected non-dormant state (2 losses), the lockout still fires — proving the brakes work and are merely starved, not deleted.

### PRD-256 (A1b) — Chain validation resolves and prices both spread legs — Tier 0 (second leg of A1)
**Single concern:** chain validation prices one near-ATM contract by OI (`chain_validation.py:222-244`); it never resolves the proposed strikes, prices both legs, or computes net credit/debit — so live spread economics are never established (Codex: "the system never establishes that the live credit is actually $1.50").

**Specific change:** resolve the setup's two strikes from its relative labels, price both legs from the chain, compute net credit/debit and live spread max loss; feed the live max-loss back through the A1a seam (superseding the 30% proxy when chain data is good); degraded chain (either leg missing/unpriceable) → `MANUAL_CHECK`, never a silent single-leg pass.

**FILES (estimate):** `cuttingboard/chain_validation.py`, `cuttingboard/options.py` (strike-label→strike resolution helper), `tests/test_chain_validation.py`, `tests/test_output_chain_fail_open.py` + sweep.

**Test that proves it:** fixture chain, $5-wide credit spread, live credit $1.50 → validation carries max loss $350; one leg missing → MANUAL_CHECK.

**Sequencing note:** the biggest and slowest of the Tier-0 fixes (network/data-layer). It trails A1a deliberately — A1a fixes the money number on estimated economics immediately; A1b upgrades estimate→live. May slide after Wave 3/4 without re-opening risk already fixed by A1a; the honest label until then is "estimated".

---

## Wave 3 — the fence (early, not first; both MANUAL-MERGE-ONLY per PRD-186)

### PRD-257 (F-04) — HIGH-RISK gate verifies reality, not labels
`tools/validate_prd_registry.py`: robust/case-insensitive LANE detection; docless COMPLETE row fails instead of `continue`; artifact leg validates content — non-empty, SHA-pinned to the reviewed commit, and the waiver matched as the exact documented sentence, not an inner substring. **A red test per bypass** (all four verified bypasses become negative tests), per hardening invariant 4.
**FILES:** `tools/validate_prd_registry.py`, `tests/test_prd_registry.py`.

### PRD-258 (F-05) — Technical backstops for MANUAL-MERGE-ONLY
CODEOWNERS covering `CLAUDE.md`, `.claude/skills/`, `tools/validate_prd_registry.py`, workflows; a CI changed-path check that fails (or labels un-auto-mergeable) any PR touching governance files; `protect_files.sh` protected-set additions (`CLAUDE.md`, `.claude/skills/`). The GitHub settings leg (required approvals, admin enforcement — Codex confirmed currently off) is an **operator manual action documented in the PRD**, not code.
**FILES:** `.github/CODEOWNERS` (new), `.github/workflows/ci.yml`, `.claude/hooks/protect_files.sh`, `tests/` (hook/path-check tests), `docs/CLAUDE_HOOKS.md`.

Both PRDs change the guardrails that constrain the agent opening them: opened and **HELD for Dustin's merge**, no auto-merge queued.

---

## Wave 4 — rest of Tier 2

### PRD-259 (F-08) — Hourly channel cannot be broken-but-green
`alert_runner.py` stops converting all runtime failures to exit 0 (keep the Telegram backstop, but the job goes red); `hourly_alert.yml` missing/stale-payload path exits 1 (the `dashboard_preview.yml:47-64` inversion already in the repo is the template); `scripts/check_readiness.py` asserts **status semantics** (`run_status`/`status` values), not key presence — a fresh ERROR/HALT artifact must not satisfy readiness-to-publish-as-healthy. Red tests: ERROR-status payload fails readiness; missing payload fails the job (2026-07-07 incident class becomes a regression test).
**FILES:** `cuttingboard/alert_runner.py`, `.github/workflows/hourly_alert.yml`, `scripts/check_readiness.py`, `tests/test_prd050_alert_runner.py`, `tests/test_check_readiness.py`.
**Ordering constraint:** after PRD-253 (F-01) — F-01 changes the hourly summary shape (`kill_switch` becomes real) that readiness assertions are written against.

### PRD-260 (F-07) — Macro-pressure failure fails loud
`runtime/__init__.py:1355-1362` `_compute_overall_pressure`: exception no longer degrades to `"UNKNOWN"` (which `execution_policy._apply_macro_pressure:240` treats as full-allow-at-full-size) — a computation failure raises and the run fails loud. `UNKNOWN` remains legal only as a genuinely computed value; the PRD distinguishes computed-UNKNOWN from failed-to-compute. Red test: injected exception in pressure computation → run fails, no full-size allow emitted.
**FILES:** `cuttingboard/runtime/__init__.py`, `tests/test_macro_pressure.py`, `tests/test_runtime_decision.py`.
(The F-15 doctrine contradiction this sits inside stays Tier 6 — needs a doctrine ruling, not code.)

---

## Wave 5 — Tier 3 + Tier 4 (sequence-level; PRDs authored when reached)

- **C1 — market-time freshness.** Freshness compares against exchange timestamp, not `fetched_at_utc=now()`. Surface flag: invalidates F-23c's comment claim and changes weekend/holiday behavior; coordinate with F-19's clock nuances.
- **F-06 — atomic writes, corrected scope.** Temp+rename for `latest_run.json` / `latest_contract.json` / `market_map.json` / payload+HTML; fix `_rewrite_summary_file`'s guard bypass; in-process locking for shared JSONL appends. Per reconcile: the cross-workflow-concurrency portion and the impossible line cite are **dropped** — do not build for separate-runner concurrency.
- **F-03 — replayability.** Raw-input snapshot per run (design PRD first: what to archive, where, retention). Forensic capability, no live-decision urgency — last in Tier 3.
- **Tier 4 — regime quorum floor.** Minimum-coverage floor before emitting confidence/posture (bounded: worst case 8→6 votes moves posture one tier). **Recommendation: pull this forward to ride immediately after Wave 1** — see interaction flag #2; it is small (regime.py + tests) and F-02 makes it more relevant, not less. Red test straight from the FABLE addendum arithmetic: 4 RISK_ON + 2 NEUTRAL at 6 votes must not out-permit the same evidence at 8 votes.

## Wave 6 — Tiers 6–7 (held mediums / lows)
Worked when reached, batched per MICRO/cosmetic rules where eligible. Two need **doctrine rulings before any code**: F-09 (wire earnings data or retire Gate 9 — product decision) and F-15 (sidecar doctrine self-contradiction — the ruling feeds how F-07's fix is worded). F-21 is a docs-fix per reclassification (correct `architecture.md`/`artifact_flow_map.md` to describe the stub). Codex-miss items (DST daily schedule, cross-process Telegram dedup, ORB bar-count CANNOT-DETERMINE) ride this wave; ORB needs a captured yfinance frame first. The owed arithmetic pass (`_estimated_debit` soundness beyond max-loss, ATR/EMA, R:R, sizing end-to-end) is scheduled as a read-only audit charge, not a PRD, after Wave 2 — A1a/A1b/A2 change the surfaces it would measure, so running it earlier would audit numbers about to change.

---

## Sequence (one line)

**A1a → budget-cap config change ($150→$400, own PRD, decision 4) → F-02 → F-01 → [Tier-4 quorum floor, recommended pull-forward] → A2 → A3 → F-04 + F-05 (fence, manual merges) → F-08 → F-07 → A1b → C1 → F-06 → F-03 → Tier 6/7 batches.** (Numbers assigned at `prd_open`.)

Hard ordering constraints (the rest is preference):
1. **F-02 before F-01** — reconcile-mandated; the hourly kill-switch check must not be born disarmable by the fabricated zero.
2. **A1a before A2** — A2's materialized dollar_risk is computed from the base A1a corrects.
3. **F-01 before F-08** — readiness/red-test assertions are written against the post-F-01 hourly summary shape.
4. **A1a before the remaining-arithmetic audit pass** (and before A1b, which fills A1a's live-economics seam).

## Cross-cutting interaction flags (fixing X changes the surface Y is measured against)

1. **A1a → A2, evaluation, dashboards, sizing tests.** Corrected max-loss shrinks credit-spread sizing (often to 0 contracts at the current budget) exactly in ELEVATED/HIGH IV. A2's fixtures, evaluation-record expectations, and candidate-board rendering all shift. Also the deliberate reason A2 waits for A1a.
2. **F-02 → Tier 4.** F-02 converts fabricated-calm votes into dropouts — and dropout is precisely what the missing quorum floor mishandles (dilution becomes concentration; confidence inflates). Bounded to IWM/BTC-USD, but F-02 makes the Tier-4 exposure *more* likely to occur in practice. Hence the pull-forward recommendation.
3. **F-02 → F-01/kill-switch/CHAOTIC tests.** Post-F-02, stress-scenario tests can no longer construct fabricated-zero quotes; F-01's tests must inject real stressed data. Another reason F-02 lands before F-01's test suite is written.
4. **F-01 → F-08 and the hourly dashboard contract.** `kill_switch` in the hourly summary becomes a real value the renderer (`_req`) and readiness checks read; F-08's semantics assertions are defined against the new shape.
5. **A3 → A2 test fixtures.** A2's policy tests should be written against dormant session state from the start (A3's target semantics) so A3 doesn't churn them; the two PRDs stay independent but their test authors share this convention.
6. **A1b → A1a.** A1b replaces A1a's estimated economics with live chain economics through the seam A1a leaves; the "max risk" figure changes provenance (estimate → live) without changing meaning.
7. **F-04/F-05 → the process that lands everything above.** Once the fence PRDs merge, subsequent PRDs' closeout mechanics face the hardened validator (real artifact-content checks). Any close between now and then is on the honor system — acceptable per operator decision (every merge reviewed), which is exactly why the fence rides early-not-first.

## Status

Plan presented 2026-07-10 and **approved the same day — the four flagged decisions are recorded above and reflected in place**. The plan is decision-complete except the Tier-4 pull-forward recommendation (decided when reached). Implementation begins with PRD authoring at Stage 0 (`prd_open.sh`) per the sequence; nothing is opened as of this commit.
