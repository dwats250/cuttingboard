# MATERIAL PACKET - Valid HALT Execution Semantics (daily path)

REVISION: 2 (one bounded correction applied to the two REQUIRED CHANGES in PACKET.review.claude.md @ de794ee: RC1 the `not errors` guard is now explicit in the D-CORE execution-success predicate + owed a red test; RC2 the execution-success return carrier is specified across every return path incl. the exception path, fail-closed on absent, no persisted field. Non-blocking: postmarket path corrected to cuttingboard/reports/postmarket.py; EVR halt-prior MISS-path test noted. Scope unchanged. Subject to exact-head confirmation before the conditional design-direction ruling and Stage-0.

STATUS: DRAFT (pre-A0, pre-Stage-0). GOV-2 upstream material packet, drafted by the Claude/Opus HELM under the owner's 2026-08-11 explicit carve-out override (harness reassignment for this slice) and the subsequent "Option B / valid-HALT execution semantics" routing ruling. Not binding; not authorization to implement.

CLASSIFICATION: MATERIAL under GOV-2 s1 (changes the production execution/publish gate semantics: which observation outcomes conclude the GitHub executor successfully and publish). CLASS: INFRA + EXECUTION. LANE: HIGH-RISK (touches cuttingboard/runtime execution/exit semantics and the publish gate; runtime is acknowledged debt handled with care).

TRACK: PREREQUISITE to the Cloudflare clock/executor campaign. That campaign's GitHub-native first-success coordination requires `conclusion=success` to mean "the OPEN observation executed and satisfied the slot." Today a valid market-stress HALT is a valid observation that concludes the executor FAILURE (exit 1, no publish), so `conclusion=success` under-counts satisfied slots and cannot be coordinated on. This packet closes that gap; the Cloudflare campaign resumes from the first-success coordination point after this merges.

AUTHORITY MODEL: unchanged. GitHub remains executor/publisher/artifact authority. This packet touches no Cloudflare surface, no dispatch contract, no CF-D1b/CF-E2, and no market/provider semantics.

## 0. Owner ruling / provenance

- Owner routing ruling (2026-08-11): "Option B. A valid market-stress / kill-switch HALT is: domain outcome HALT/system_halted; execution outcome SUCCESSFUL VALID OBSERVATION. It must remain truthfully HALTed in domain artifacts; produce the halted observation; pass appropriate artifact validation; publish the halted board; own its single HALT notification; conclude the GitHub executor successfully; satisfy the OPEN slot. A genuine crash / unusable data / readiness failure / artifact-validation failure / publish failure remains executor FAILURE. Do NOT simply change summary.status from FAIL to SUCCESS."
- Owner return-gate (answered YES, so proceed): the repo CAN distinguish a valid market-stress halt from an invalid/degraded halt at the exit/publish decision point (see s3).
- Arc: surfaced while designing the Cloudflare first-success coordination (a valid HALT concludes `failure`, indistinguishable from a crash via GitHub-native run evidence). Owner ruled the fix is the execution/domain split, executed as this prerequisite slice.

## 1. Problem (falsifiable)

A valid market-stress kill-switch HALT is a correct, intended live observation: the pipeline fetched and validated quotes, computed the regime, and the kill switch correctly decided to halt new positions. Yet it concludes the GitHub executor as FAILURE and does not publish:
- `cli_main` (runtime/__init__.py:237) returns `0 if status==SUCCESS else 1`.
- A halt is `status=FAIL` by construction: `_build_run_summary:1436` sets `status=FAIL if system_halted or errors`, and the verify invariant :1757-1758 enforces "system_halted runs must have status FAIL." So a halt exits 1.
- The workflow live step sets `PUBLISH_READY=true` only if `rc==0` (cuttingboard.yml:298); Commit/Push are gated on it (:387,:438). So a valid halt: no publish, conclusion=failure.

Consequences: (a) the halted board is never published - the dashboard shows the prior (stale) observation with the client-side BOARD-N-OLD banner instead of today's real "market halted" observation; (b) `conclusion=failure` makes a valid observation indistinguishable from a crash to any GitHub-native consumer (blocking the Cloudflare first-success coordination); (c) a dedup-suppressed repeat halt today relies on the PRD-295 `if:failure()` step to alert, which sends a misleading "pipeline FAILED" message for a valid halt.

The DAILY path conflates two orthogonal truths in one field: the DOMAIN outcome (HALT / system_halted - market truth) and the EXECUTION outcome (did the observation run correctly). They must be decoupled.

PROVEN PRECEDENT: the HOURLY path already implements this decoupling. `alert_runner.py` / `_execute_notify_run` returns execution `status=SUCCESS` on any non-exception completion INCLUDING a market-stress halt (runtime/__init__.py:645), while the persisted artifact keeps `status=FAIL`/`system_halted=True`/`outcome=HALT` (:583-584); `alert_runner.py:116` exits `0 if status==SUCCESS else 1`; its docstring (:45-46) states the intent verbatim: "Exit 0 only on a healthy completion ... TRADE, NO_TRADE, or market-stress safety HALT." This slice brings the daily `cli_main`/`execute_run` path to the same parity.

## 2. The distinction is real and typed (return-gate cleared)

The repo distinguishes a valid market-stress halt from an invalid/degraded halt on multiple independent axes:
- `HaltCause` enum (validation.py:37-44): exactly `VALIDATION` (data/validation halt) and `MARKET_STRESS` (kill-switch halt), PRD-180. `halt_cause` is a field on the in-memory `ValidationSummary` (validation.py:60); today an "in-memory render-time discriminator only," JSON-safe if surfaced.
- Valid market-stress halt (runtime/__init__.py:437-445 hourly, :1022-1037 daily): `halt_cause=MARKET_STRESS`, `errors==[]`, `outcome=HALT`, `system_halted=True`, `kill_switch=True`. Kill switch trips only on successfully-validated data (regime computed at :1016-1017 before the kill-switch elif at :1022).
- Invalid/degraded (data-integrity) halt (:1019-1021): `halt_cause=VALIDATION`, `errors` NON-empty (halt_reason appended).
- Crash (execute_run exception :315-349): `_failure_summary` with `errors` NON-empty, `kill_switch=False`, NO `halt_cause`.
- NO MASQUERADE PATH: `errors==[] AND halt_cause==MARKET_STRESS` is reachable only on a genuine kill-switch trip on validated data. A crash after a valid halt board is produced is caught by :315 and REPLACED with `_failure_summary` (errors non-empty), degrading correctly to FAILURE. At the decision point (execute_run success return :313-314), `pipeline.validation_summary.halt_cause` is reachable via the frozen PipelineResult.

## 3. Design (FROZEN intent; minimum split)

D-CORE. Introduce an EXECUTION-SUCCESS signal, distinct from the persisted DOMAIN `status`, that drives the exit code (and therefore PUBLISH_READY / job conclusion). Execution succeeds iff the observation ran and produced its intended result:
- `execution_success = verification.pass AND (summary.status == SUCCESS OR (system_halted AND halt_cause == MARKET_STRESS AND not errors))`.
- The `not errors` clause is REQUIRED, not incidental (RC1). It encodes the market-stress-vs-degraded invariant EXPLICITLY at the highest-consequence decision, rather than relying on the un-encoded runtime :1019/:1022 mutual exclusion; `verify_run_summary` does not gate on `errors` (its `pass` is over its own invariant list, :1668-1800). A constructed summary with `system_halted AND halt_cause==MARKET_STRESS AND errors!=[]` (a degraded market-stress halt, e.g. verification appended an error at execute_run:296) MUST exit 1; this ships a red test.
- RETURN CARRIER (RC2): `execute_run` computes `execution_success` and conveys it to `cli_main` via an EXPLICIT signal set on EVERY return path, never by mutating/persisting the summary dict. Concretely: (i) the success return (:313) carries the computed predicate; (ii) the exception return (:315-349, which builds a DISTINCT `_failure_summary` that has no such signal) carries `execution_success=False`; (iii) `cli_main` treats an absent/unknown signal as FAILURE (fail-closed). Because `execute_run` returns the same mutable `pipeline.summary` it already persisted at :302-303, the signal must NOT be a key added to that dict (it would either persist or be added post-persistence and be fragile) - it is a separate return value / typed result. `cli_main` returns `0 if execution_success else 1` (replacing the `status==SUCCESS` test). The persisted summary dict is unchanged; no new artifact field.
- The persisted DOMAIN `status` stays FAIL for a halt (unchanged). Do NOT flip status - it is rejected by verify (:1757) and morning readiness (check_readiness.py:96), and would corrupt domain truth. system_halted / outcome=HALT / errors / kill_switch are all preserved verbatim.

D-PUBLISH. A valid market-stress halt now exits 0 -> the EXISTING workflow sets PUBLISH_READY=true -> renders the halt board (renderer emits all three required markers unconditionally: dashboard_renderer.py:2317/2652/2922) -> `check_readiness --profile morning` PASSES it (market-stress halt is the documented healthy case: status=FAIL, errors=[], system_halted=True; check_readiness.py:78-79,96-97) -> commit + push the halt board. NO workflow file change is required (the gate already keys on rc==0). A VALIDATION halt (errors non-empty) still exits 1 (execution FAILURE) and is additionally rejected by morning readiness :94-95 - double-safe.

D-NOTIFY. The runtime already sends exactly one halt notification during `_run_pipeline` (:912, gated on mode in {LIVE,SUNDAY} and should_send), independent of exit code. Under exit 0 the PRD-295 `if:failure()` step never fires, so the runtime's own send is the single notification - exactly-one is preserved for the normal (send-succeeds) case. ONE hazard to close: a market-stress halt is LOW priority (STAY_FLAT, not tradable), so `should_send` can dedup-SUPPRESS a repeat halt whose coarse state-key equals the last published key (last_notification_state.json now persists a halt key because the halt publishes). Today that suppressed case is (mis)covered by the failure backstop; under exit 0 it would yield ZERO. To satisfy "own its single HALT notification," the DAILY (LIVE/SUNDAY) path must always send its single halt notification for a market-stress halt (bypass the state-key dedup for that outcome). This is a daily-path-scoped change; the HOURLY path and `classify_notification_priority` semantics are NOT altered.

D-CONSUMERS. Publishing a halt board first-commits the halt audit/scoreboard rows (today discarded with the runner). Verified benign: evaluation.jsonl/performance never mis-score a halt (a halt writes zero evaluation records; performance_engine drops non-{TARGET_HIT,STOP_HIT,NO_HIT}); regime_history folds a well-formed halt row (regime populated for a market-stress halt; no accuracy scoring). ONE behavioral consequence to make explicit + test: postmarket EVR (reads audit.jsonl as run_history) will see the published halt as a "prior run" for the NEXT run's expectation-vs-reality. A halt is STAY_FLAT (no trade expectation), so EVR against a halt prior is benign; the slice will assert this (or exclude MARKET_STRESS-halt priors from EVR if the assertion fails) - decided at Stage-0 by the behavioral test, not by convenience.

## 4. Boundary and non-goals (FROZEN)

IN scope:
- Decouple execution-success from domain status on the DAILY path (execute_run/cli_main); a valid market-stress halt -> exit 0 -> publishes the halt board -> conclusion=success -> satisfies OPEN.
- Guarantee exactly-one HALT notification on the daily path (always-send the market-stress halt notification).
- Keep VALIDATION halts, crashes, unusable-data, readiness/artifact-validation/publish failures as execution FAILURE (exit 1, no publish).
- Behavioral test coverage for each outcome class and each consumer touched by the first-time halt publish.

OUT of scope (any entry invalidates the boundary):
- No change to domain truth: status stays FAIL for a halt; system_halted / outcome=HALT / errors / kill_switch unchanged; no flip of status to SUCCESS.
- No latest_run.json / contract schema change (no new persisted field; halt_cause need not be surfaced - execution-success is computed in-memory and conveyed via the daily return contract).
- No change to the HOURLY path (alert_runner / _execute_notify_run) or to shared `classify_notification_priority` semantics.
- No Cloudflare surface, no dispatch contract, no slot/source metadata, no CF-D1b/CF-E2.
- No change to the notification message content/formatter beyond ensuring the halt's single send fires.
- No new authority model, no new persisted attempt/idempotency state.
- No workflow (.github/workflows/**) change if avoidable (the rc==0 gate already suffices); if a marginal change is unavoidable it stays Bash-only and inside the reviewed FILES.

## 5. Consumer / seam analysis

- Exit-code / publish gate: cli_main:237 (change), execute_run:297-301 (execution-success computed here), workflow rc==0->PUBLISH_READY (cuttingboard.yml:298; unchanged).
- verify_run_summary (:1668, invariant :1757): PASSES a valid halt board today (FAIL+HALT+system_halted+zero-qualified are invariant-consistent); NOT a blocker; unchanged.
- check_readiness --profile morning (check_readiness.py:73-97): PASSES a market-stress halt, FAILS a VALIDATION halt; unchanged (relies on errors==[]).
- Notification: runtime send at :912; PRD-296 sentinel :258-267/:1240 becomes moot under success (harmless); daily always-send-on-market-stress-halt added.
- Publish consumers (now receive a halt row): regime_history.py:51-85 (folds halt row, no scoring); audit.py:219-227 (well-formed); evaluation.py:53-54,114-137 + performance_engine.py:68-71 (halt writes zero eval records -> never mis-scored); cuttingboard/reports/postmarket.py:5-6,64-120 (EVR is DISPLAY-ONLY; it sees the STAY_FLAT halt as a "prior run" for the next run's expectation-vs-reality. Benign: a halt prior can only produce a directional-run "MISS"-style label, never a truth corruption. Stage-0 ships a behavioral test covering the halt-prior -> directional-next-run MISS path; exclude MARKET_STRESS-halt priors from EVR only if that test shows a real defect).
- Renderer: dashboard_renderer.py halt handling (:1491-1493 SYSTEM HALT title, markers :2317/2652/2922); validate_coherent_publish (:557-633) age-based, passes a fresh halt payload.

## 6. Semantic-failure hardening (PRD-198) applied

- Fail-loud, never silent-fallback: a VALIDATION halt / crash / unusable-data condition stays execution FAILURE (exit 1) and remains fail-loud; only a genuine market-stress halt is promoted to execution success.
- Assert the resolved, not the requested: execution-success is computed from the resolved kill-switch discriminator (halt_cause==MARKET_STRESS AND errors==[]), not from a mode/intent.
- Authoritative source, not proxy: the discriminator is the typed HaltCause + the errors list, the same source check_readiness's health logic uses; no proxy.
- Every guard ships a red test: each outcome class (TRADE/NO_TRADE exit 0; market-stress HALT exit 0 + publishes; VALIDATION halt exit 1 no publish; crash exit 1; dedup-suppressed repeat halt still sends exactly one) gets a behavioral red test; a mutation that would let a VALIDATION halt or crash exit 0 must go red.
- Verify where truth is determined: full suite green locally then reproduced on CI; the exit-code/publish behavior is asserted at the cli_main/execute_run boundary, not only in the workflow YAML.
- Pin identities that matter: HaltCause.MARKET_STRESS is the pinned discriminator; the market-stress halt_reason literal is KILL_SWITCH_HALT_REASON (runtime:2379).

## 7. Falsification (attacks -> handling)

- TRADE/NO_TRADE -> exit 0, publishes (unchanged).
- Valid market-stress HALT -> exit 0, publishes halt board, conclusion=success, satisfies OPEN, one halt notification.
- VALIDATION/data-integrity halt -> exit 1, no publish, conclusion=failure (errors non-empty; also fails readiness :94).
- Crash before/at observation -> _failure_summary (errors non-empty, no MARKET_STRESS) -> exit 1, no publish.
- Crash AFTER a valid halt board is produced -> caught by execute_run :315, replaced with _failure_summary -> exit 1 (correct degrade).
- Kill switch trips on UNVALIDATED data -> impossible: validation halts first (mutual exclusion :1019/:1022; regime not computed on a validation halt).
- Repeat identical market-stress halt (same coarse key) -> daily always-send guarantees one notification (no ZERO); no failure-backstop reliance.
- Market moved but still halt -> still a market-stress halt -> exit 0, publishes fresh halt board, one notification.
- Readiness fails on the freshly-rendered halt board -> publish blocked (execution treated as failed by the artifact gate) - a market-stress halt passes readiness by construction, so this only blocks a malformed render (correct).
- Publish (git push) fails -> PRD-297 fail-loud path unchanged; execution FAILURE surfaced.
- Hourly halt -> untouched (separate path; already exits 0 on a market-stress halt).
- Postmarket EVR sees a halt prior -> benign (STAY_FLAT, no trade expectation); asserted at Stage-0.

## 8. FILES / LOC ceiling - ESTIMATED SURFACE - NOT YET APPROVED

Provisional per GOV-2 s5 (binding Gate-A number set by Dustin at PRD Gate A). Likely surfaces:
- M cuttingboard/runtime/__init__.py (execute_run execution-success determination; cli_main exit-code mapping; daily always-send-on-market-stress-halt).
- Possibly M cuttingboard/output.py or cuttingboard/notifications/* (only if the daily always-send is cleanest there rather than in the runtime notify block).
- Possibly M cuttingboard/reports/postmarket.py (only if the EVR halt-prior behavioral test requires excluding MARKET_STRESS-halt priors).
- M tests/ (behavioral: exit-code per outcome class, publish-on-halt, exactly-one halt notification incl. the repeat-suppressed case, verify/readiness on halt, consumer coverage). The PRD-158 grep sweep (halt/exit assertions across ~8 decisive test files incl. test_operationalization.py, test_notification_ownership.py, test_check_readiness*.py, test_contract.py, test_dash_*.py) is completed at Stage-0 and every asserting file added to FILES.
- NO .github/workflows/** change expected (rc==0 gate suffices).
Estimated ~80-160 net non-test production LOC. Red tests excluded from the count.

## 9. Invalidators / STOP (return to owner)

- A valid market-stress halt cannot be distinguished from an invalid/degraded halt at the decision point -> CLEARED (s2), but if implementation surfaces a real masquerade path, STOP.
- The fix requires changing market/domain truth (status/system_halted/outcome) rather than execution truth -> STOP.
- latest_run.json / contract schema must materially change -> STOP.
- Notification ownership cannot be made exactly-one without touching hourly or shared priority semantics -> STOP (current design keeps it daily-scoped; if that proves impossible, return).
- Hourly semantics must change -> STOP.
- A new authority/schema seam appears -> STOP.
- Publishing a halt board mis-scores or corrupts a downstream consumer that cannot be made correct additively -> STOP.

## 10. Sequence after this packet

Independent adversarial packet review -> one bounded correction + exact-head confirmation -> conditional owner design-direction ruling (pre-authorized if the frozen invariants hold) -> Stage-0 PRD-298 (feature branch, references this packet SHA) -> independent PRD review -> conditional Gate A -> implementation -> behavioral tests -> implementation review -> HIGH-RISK disposition -> closeout -> final CI -> merge-ready. Then the Cloudflare clock/executor campaign resumes from the first-success coordination point.
