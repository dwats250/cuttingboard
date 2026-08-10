# MATERIAL PACKET - Morning Executor Truthfulness + Gate Swap

REVISION: 2 (one bounded correction applied to the five REQUIRED findings in PACKET.review.sol.md @ de3cc6e; scope unchanged). This corrected head is subject to Sol exact-corrected-head confirmation before Dustin's design-direction ruling.

STATUS: DRAFT (pre-A0, pre-Stage-0). GOV-2 upstream material packet. Not binding; not authorization to implement. This document is the artifact that Codex packet review + exact-head confirmation + Dustin's design-direction ruling must clear before any Stage-0 PRD is opened.

CLASSIFICATION: MATERIAL under GOV-2 s1 (selects an implementation seam shared across all pipeline modes; changes a production execution/publish gate). CLASS: INFRA. Default tier T0 (CI gate feeds runtime execution). LANE: HIGH-RISK. `.github/workflows/**` is a protected, Bash-only-editable HIGH-RISK FILE.

TRACK: Own executor-hardening track, SEPARATE from the Cloudflare packet. CF-D4 retains the existing GitHub cron in slice 1; this defect and its fix exist regardless of Cloudflare, and Cloudflare later consumes the same "invocation authorizes an attempt" contract without co-design.

AUTHORITY MODEL: unchanged. GitHub remains executor/publisher/artifact authority. This packet touches no Cloudflare surface, no CF-E2, no CF-D1b, and no market/provider semantics.

GOV-2 ORDERING (binding): owner design-direction ruling (D1-D6) -> PRD 2 Stage-0 drafting -> independent PRD review -> Gate A -> implementation. Nothing in this packet is Gate A or implementation authorization; D1/D2 below are design directions for what a future reviewed PRD may PROPOSE.

## 0. Provenance

- Incident 2026-08-10: the nominal 06:00 PT live run started ~07:14 PT (scheduler drift; already mitigated for MODE by PRD-189 cron-string resolution) and FAILED before market execution because the unconditional repository-wide `pytest tests/ -q` gate (cuttingboard.yml:165) hit a flaky concurrency test (PRD-293 dev-bootstrap lock race), aborting the job -> latest_run.json stale, no publish, and the board gave no signal that today's slot missed. The hourly path (no test-suite gate) succeeded.
- Read-only GitHub API evidence (this session) confirms: the ci.yml `test` push-run for main HEAD `ddacbf0` was SUCCESS, while the same SHA's operational `pipeline` check shows `failure @ 2026-08-10T14:14Z`. Main was CI-green; the pipeline's own re-run of the suite flaked. The full-suite morning gate is redundant re-validation of an already-validated revision, and its flakiness is the failure surface.
- Fable navigator pass + Sol packet review (PACKET.review.sol.md) shaped this two-PRD boundary and this corrected revision.

## 1. Problem (falsifiable)

A time-sensitive production morning observation is gated on the full repository test suite. Because the suite runs unconditionally before execution as a hard gate, ANY test failure (including an unrelated flaky test on a revision that already passed CI at merge) aborts the observation, leaves a stale prior success in latest_run.json, and produces no notification that the named slot missed. Quality control (the full suite) belongs at the merge gate (ci.yml), not as a per-run runtime gate.

PRE-RULING EXTERNAL PREMISE (must be verified current before Dustin's D1 ruling; not provable from repo contents): main branch protection actually requires the ci.yml `test` check to conclude SUCCESS before a merge to `main`. If that protection is not in force, main HEAD is not reliably CI-green and PRD 2's "CI-authoritative-green revision" premise fails; this premise is an out-of-tree fact Dustin confirms at ruling time, NOT a repo falsifier.

## 2. Boundary and non-goals (FROZEN)

IN scope (two PRDs, one packet):
- PRD 1: fail-loud additive truthfulness. Add a Telegram failure notification to the morning pipeline. No gate changes, no CI permission expansion, no latest_run.json schema change, no attempt artifact, no slot-aware board logic. The existing client-side "BOARD N OLD" banner remains the stale-board signal.
- PRD 2: one atomic gate-swap unit. Remove operational pytest/ruff from the live path; add exact-SHA authoritative CI proof; add the required `actions: read` permission; add a deterministic runtime-readiness pre-gate; add a morning post-execution artifact-health gate; preserve latest_run.json as latest-executed-observation-only.

OUT of scope (any entry invalidates the packet boundary):
- No wall-clock staleness gate.
- No morning-slot canonicalization; no fourth slot-time encoding.
- No reuse of the hourly dedup state.
- No latest_run.json schema change; no provenance SHA field; no new attempt artifact.
- No CF-E2 / CF-D1b inference; no Cloudflare build; no repository_dispatch/idempotency/slot inputs.
- No PRD-293 dev-bootstrap fix hitchhiker.
- No market/provider semantics.

## 3. Owner design direction (recorded, Dustin 2026-08-10)

- This packet continues consuming the existing PRD-189 `scripts/resolve_run_mode.py` cron-string contract for mode identity. It does NOT introduce a fourth slot-time encoding, and it does NOT declare that module the permanent global clock source. Canonical clock consolidation belongs with the future Cloudflare explicit-slot work.
- Because no slot-aware board logic is in scope, the slot-time multiplicity finding is deferred by scope, not resolved here.
- Removing the full suite from morning runtime, and adding `actions: read`, are DESIGN DIRECTIONS for what PRD 2 may PROPOSE (D1, D2). They are NOT Gate A and NOT implementation authorization; actual authorization is reserved for the reviewed PRD 2 Gate A per the GOV-2 ordering above.

## 4. PRD 1 - Fail-loud additive truthfulness

PURPOSE: make "today's named morning slot did not produce a valid observation" observable, without promoting a failed attempt into valid market data, and without any gate/schema/permission change.

DESIGN:
- Add `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` to the cuttingboard.yml job `env:` (currently absent; hourly_alert.yml:40-42 already wires them).
- Add an `if: failure()` terminal step that sends a Telegram failure alert whose content is derived ONLY from workflow context, NEVER from latest_run.json (which may be a stale prior observation).
- Minimum truthful failure contract - carriers, all from workflow context:
  - intended run mode: `github.event.inputs.mode` for a dispatch, else the resolved mode if the mode-resolution step ran; else "unknown mode".
  - failed stage / failure class: the failing step or a coarse failure class if deterministically known from the workflow; do NOT fabricate a specific stage if it is not available.
  - date/time: from workflow context (`date -u` / GitHub run metadata), NOT from any observation artifact.
  - NOTE: `cuttingboard/notifications/__init__.py` `format_failure_notification` DISCARDS its `date_str` argument (verified :586-607); it may be reused only for message shape, and the date/stage carriers above must be supplied explicitly and threaded, or the message must state only what is truthfully available. Do not claim the existing formatter supplies stage/date.
- Send path: `cuttingboard.output.send_telegram(title, body)` (verified: no latest_run.json dependency) once the package is importable; a raw-stdlib `urllib` POST to `sendMessage` fallback for a failure that precedes dependency install (if Slice 1 claims that coverage).
- The existing client-side "BOARD N OLD" banner (dashboard_renderer.py:244-290) remains the on-board stale signal; hourly re-render republishes within the hour. No renderer change in PRD 1.

NON-GOALS (PRD 1): no gate change, no removal of the pytest/ruff steps, no permission expansion, no latest_run.json change, no attempt artifact, no slot-aware banner.

RED TEST (REQUIRED; structural YAML assertion alone is insufficient): an executable test of the ACTUAL invoked notification handler that proves, with a stale latest_run.json present and the live pipeline never executed, the notification reports only current workflow failure truth (mode/stage/date from context) and never the stale observation's data; the Telegram call is isolated/mocked. If Slice 1 claims pre-install coverage, also test the pre-install stdlib fallback path. A structural yaml assertion (that the if:failure step is wired with TELEGRAM_* in env) is retained as a complement, not the proof.

FILES (PRD 1):
- M `.github/workflows/cuttingboard.yml` (job env + if:failure step; Bash-only edit)
- A/M `tests/` (executable handler test + pre-install fallback test + structural yaml assertion)
- possibly A/M `cuttingboard/notifications/` (a small failure-message helper that accepts explicit mode/stage/date, if reuse of the existing formatter is insufficient)
- Stage-0 bookkeeping (PRD doc, PRD_REGISTRY row, prd_index entry, PROJECT_STATE pointer)

## 5. PRD 2 - Atomic gate-swap unit (never split into separate PRDs)

PURPOSE: stop gating the time-sensitive observation on the full suite; gate instead on (pre) the exact revision being CI-authoritative-green + runtime-ready, and (post) the freshly-produced artifact being healthy - preserving quality control at the merge gate.

ATOMIC UNIT (splitting into separate PRDs creates an unguarded or double-gated interim; must land as one PRD):
1. Remove the pre-execution `pytest tests/ -q` (cuttingboard.yml:165) and `ruff` (:160) from the execution path. The full suite + ruff remain in ci.yml (merge gate) unchanged.
2. Add the exact-SHA authoritative CI proof (Section 6) as a pre-execution gate.
3. Add `actions: read` to the cuttingboard.yml `permissions:` block (currently `contents: write` only); keep `contents: write`. No other permission.
4. Add a deterministic runtime-readiness pre-gate (imports resolve, entrypoint + critical deps load, required config present, observation path invocable) - enumerated, seconds-fast, no concurrency/integration tests, one red mutation per check.
5. Add a morning post-execution artifact-health publish gate with correct ordering (see EXECUTION ORDERING below).
6. latest_run.json remains latest-executed-observation-only: a blocked/pending/drifted/proof-error attempt that never executes MUST NOT write it (preserve the existing write-only-after-execution behavior; the writer is runtime/__init__.py:1948, reached only after pipeline execution); no schema change, no SHA field.

EXECUTION ORDERING (corrected): the current `Commit artifacts` step (cuttingboard.yml:309-339) RENDERS the board (`python3 -m cuttingboard.delivery.dashboard_renderer`) and stages logs/HTML INSIDE the commit step; a health gate placed before it would validate STALE checked-in HTML. PRD 2 must enforce: execute observation -> generate/render/stage the CURRENT morning artifacts -> VALIDATE the exact current artifact set -> commit -> push. PRD 2 may need to MECHANICALLY SPLIT the current render-and-commit step so validation runs after render and before commit/push. Enumerate the morning artifact set to validate (PRD 2 fixes the exact list and red-tests it): at minimum logs/latest_run.json run-health (status/outcome/errors/system_halted) and the freshly-rendered ui/dashboard.html + ui/index.html (required markers present; forbidden `pytest-of-`/`/tmp/` patterns absent), mirroring check_readiness's existing model adapted to the morning artifacts. Do NOT change hourly's artifact set or exit semantics.

NON-GOALS (PRD 2): no staleness gate, no slot logic, no provenance schema field, no new artifact, no hourly-dedup reuse.

FILES (PRD 2):
- M `.github/workflows/cuttingboard.yml` (remove gate steps; add permission; add readiness pre-gate + CI-proof pre-gate steps; split render/commit; add post-render artifact-health gate; Bash-only edit)
- A `scripts/check_run_revision.py` (exact-SHA CI proof; deterministic selection; typed states incl. CI_PROOF_ERROR; fail-closed)
- A `scripts/check_runtime_readiness.py` (deterministic pre-gate) OR M/narrow `tools/engine_doctor.py` (see D5)
- M `scripts/check_readiness.py` (parameterize for the morning artifact set; hourly path unchanged; regression test proving hourly bit-identical)
- A/M `tests/` (red tests: each typed revision state incl. CI_PROOF_ERROR + selection/pagination/multiple-run cases; each readiness check; morning check_readiness + hourly-unchanged red test)
- Stage-0 bookkeeping

## 6. Exact-SHA authoritative CI proof contract (PRD 2)

DETERMINISTIC LOOKUP (must fully resolve to a single authoritative run BEFORE any typed state is assigned):
1. Resolve the exact checked-out SHA: `git rev-parse HEAD` after `actions/checkout ref: main`.
2. Query the Actions runs endpoint scoped by `head_sha={SHA}` and `event=push`, with COMPLETE pagination handling (follow every page; do not truncate).
3. Filter the collected runs to `path == .github/workflows/ci.yml`.
4. Deterministic cardinality handling: zero matching runs -> CI_MISSING; exactly one -> that run; multiple -> select the current run deterministically (highest run_number / most recent created_at; define and red-test the tie-break), then use its current attempt.
5. Current-run/current-attempt selection: read the selected run object's CURRENT `status` + `conclusion` (these reflect the latest attempt; a rerun updates them). Never a cached prior success.
6. status/conclusion interpretation -> typed state below.
7. Any HTTP / auth / rate-limit / schema / parse failure at any step -> CI_PROOF_ERROR (fail-closed). No API/read failure may degrade to CI_SUCCESS.

TYPED REVISION STATES (each maps to a named, notified, fail-loud outcome; none silently passes):
- CI_SUCCESS: the uniquely selected ci.yml push run is status=completed AND conclusion=success -> proceed to runtime-readiness + execution.
- CI_PENDING: selected run exists but status != completed -> policy (D3).
- CI_MISSING: no ci.yml push run found for the SHA (covers [skip ci], the ~2-3s pre-creation window, path/skip holes) -> named failure, skip.
- CI_FAILED: selected run completed with conclusion != success -> named failure, skip.
- REVISION_DRIFT: the SHA proven at proof time != the SHA at execution time (re-check HEAD immediately before execution) -> named failure, skip.
- CI_PROOF_ERROR: the lookup could not be completed deterministically (API/auth/rate-limit/schema/parse/ambiguity) -> named failure, skip; fail-closed.

INVARIANT: CI_SUCCESS authorizes an OBSERVATION ATTEMPT; it is NEVER evidence that an observation occurred or was valid. A post-execution conclusion flip is non-retroactive: the proof records what was authoritative at attempt time.

## 7. Consumer / seam analysis (reader inventory refreshed)

SEARCH METHOD (recorded): `rg -n "latest_run\.json|LATEST_RUN_PATH" cuttingboard/ scripts/ tools/ .github/`; `rg -n "verify_run_summary" cuttingboard/ scripts/`; plus direct inspection of cuttingboard/evaluation.py.

WRITER (single): `cuttingboard/runtime/__init__.py:1948` `safe_write_latest(LATEST_RUN_PATH, ...)` (LATEST_RUN_PATH defined at runtime/_constants.py:46), reached only after pipeline execution.

READERS (verified):
- `cuttingboard/delivery/dashboard_renderer.py:55, 3283-3290` - LIVE STATE / UPDATED (pipeline_run).
- `.github/workflows/cuttingboard.yml:289` - the in-workflow commit-message generator reads logs/latest_run.json.
- `cuttingboard/runtime/__init__.py:207, 273` (via `verify_run_summary`, def at :1645) - the `--mode verify` verification path.
- `.github/workflows/hourly_alert.yml:87` (restore read-only via tools/ci_restore_publish_state.sh) and `:157` (`git checkout HEAD -- logs/latest_run.json` reverts it) - hourly treats it as pipeline-owned, restores read-only, and never republishes it.

CORRECTION: `cuttingboard/evaluation.py` is NOT a latest_run.json reader; it reads `audit.jsonl` ("most recent same-day prior pipeline run from audit.jsonl", evaluation.py:79). The prior packet enumeration was wrong and is replaced.

CONCLUSION (unchanged): latest_run.json remains latest-executed-observation state only; no schema change; no SHA/provenance field; a blocked/pending/drifted/proof-error attempt writes nothing (the writer runs only after execution). A SHA field would be a multi-reader persisted-schema change (its own MATERIAL surface) and is out of scope.

OTHER SEAMS:
- check_readiness.py is shared code (hourly-owned today). The morning extension must be parameterized so hourly's artifact list + exit behavior stay bit-identical (regression test required).
- Permission: `actions: read` added; `contents: write` preserved; no over-grant. `checks: read` is unnecessary because the proof uses the Actions API, not the check-runs aggregate.
- Signal-loss note: removing the morning suite ends the only SCHEDULED full-suite run on main (ci.yml fires only on PR/push). Merge authority is untouched; daily DRIFT observation on quiet no-merge days disappears (D4).

## 8. Semantic-failure hardening (PRD-198) applied

- Fail-loud, never silent-fallback: every non-CI_SUCCESS state (incl. CI_PROOF_ERROR) is a named, notified failure; CI_MISSING/CI_PROOF_ERROR never read as pass.
- Assert the resolved, not the requested: prove the exact SHA's uniquely-selected ci.yml push-run conclusion, not "main is green by construction."
- Authoritative source, not proxy: the ci.yml push run conclusion (the merge gate's own result), selected by head_sha+event+path, not the aggregate check-runs list.
- Every guard ships a red test: each typed state incl. CI_PROOF_ERROR and the selection/pagination/cardinality cases; each readiness check; the morning artifact-health gate; hourly-unchanged; the fail-loud handler.
- Verify where truth is determined: the token capability (actions:read resolves the push run) is proven FROM a workflow run (Section 9), not from local gh.
- Pin identities that matter: exact SHA + workflow path + event=push; deterministic current-attempt; re-check HEAD for REVISION_DRIFT.

## 9. Pre-Gate-A evidence requirements (must be satisfied before PRD 2 Gate A)

1. Prove FROM a real workflow run that `actions: read` lets GITHUB_TOKEN resolve the exact-SHA authoritative ci.yml push run (local gh success is insufficient).
2. Deterministically inspect rerun / current-attempt semantics AND multiple-matching-run / pagination behavior: confirm the selection resolves to the current authoritative attempt and that a superseded run cannot mask an active/failed one, and vice versa.
3. Expand CI-latency sampling (read-only sampling to date: ~74-87s over n=3) enough to support the chosen CI_PENDING policy (esp. a bounded-wait budget).
4. Prove the runtime-readiness checks are enumerated, deterministic, and red-testable per check (PRD-198 #4) - no concurrency/integration/flaky checks.
5. Prove the morning check_readiness extension leaves hourly behavior bit-identical (regression test on hourly's artifact list + exit codes).
6. Prove deterministic handling of API/HTTP/auth/rate-limit/schema/parse failure (CI_PROOF_ERROR fail-closed) and of zero/one/multiple matching runs.

## 10. Owner design directions still required (D1-D6; directions, not Gate A)

D1. Whether PRD 2 MAY PROPOSE removing operational pytest/ruff from morning runtime (design direction; actual authorization reserved for the reviewed PRD 2 Gate A). Requires the Section 1 branch-protection external premise verified current.
D2. Whether PRD 2 MAY PROPOSE adding `actions: read` while retaining `contents: write` (design direction; authorization at PRD 2 Gate A).
D3. CI_PENDING policy: immediate named failure / short bounded wait (~<= observed p100) / hybrid; and the wait budget if applicable. Any wait must stay well under the slot's usefulness window.
D4. Whether to recover quiet-main DRIFT observation with a separate scheduled, non-blocking full-suite run (see recommendation), or accept its loss.
D5. Runtime-readiness pre-gate source: dedicated `scripts/check_runtime_readiness.py` vs narrowing `tools/engine_doctor.py`; and the exact closed check list.
D6. The executable failure-notification red-test mechanism and the exact stage/date carrier contract (per Section 4).

## 11. FILES / LOC ceilings - ESTIMATED SURFACE - NOT YET APPROVED

Provisional per GOV-2 s5 (validation + proof-support code counted first-class; binding Gate-A number set by Dustin at PRD Gate A, top of range + margin):
- PRD 1: ESTIMATED SURFACE - NOT YET APPROVED. ~25-50 net infra/production lines, accounting for the failure-stage/mode/date provenance threading, the pre-install fallback path, a possible small failure-message helper, and the executable red tests - materially above the prior 10-25 estimate.
- PRD 2: ESTIMATED SURFACE - NOT YET APPROVED. ~200-400 net production LOC, accounting for the full Actions API selection + pagination + error/cardinality handling (check_run_revision), the runtime-readiness checker, permission plumbing, the render/commit workflow-step split + post-render validation, the check_readiness morning extension, and red tests per typed state and per readiness check - above the prior 150-300 estimate. If D4 selects a drift run, add its separate (non-blocking) workflow surface.

## 12. Invalidators

- The Section 1 branch-protection external premise is NOT in force -> the merge gate does not guarantee main HEAD green; removing the morning suite would weaken QC -> re-scope.
- Evidence #1 fails: actions:read does not let GITHUB_TOKEN resolve the exact-SHA push run from a workflow run -> the CI proof (PRD 2 core) is not implementable as designed -> STOP, redesign the proof.
- Evidence #2/#6 shows the selection cannot deterministically resolve the current authoritative attempt across reruns / multiple runs / pagination, or API failure cannot be made fail-closed -> STOP.
- Evidence #4/#5 fail: readiness checks cannot be made deterministic/red-testable, or the check_readiness extension cannot leave hourly bit-identical -> PRD 2 reintroduces flakiness or breaks hourly -> re-scope.
- Any OUT-of-scope entry appears (staleness gate, slot canonicalization, 4th slot encoding, latest_run.json schema/SHA field, new attempt artifact, hourly-dedup reuse, CF entanglement, PRD-293 fix) -> boundary breach.
- Dustin declines D1 -> whole packet invalid.

## 13. Non-blocking recommendations (recorded, NOT REQUIRED)

- D5: prefer a dedicated `scripts/check_runtime_readiness.py` over narrowing `tools/engine_doctor.py` (a broad ~652-line diagnostic that can run pytest and reads `.env`; narrowing risks preserving mutable diagnostic authority inside a production gate).
- D4: if a scheduled full-suite drift run is chosen, classify it as DRIFT OBSERVATION only - never slot-gating, never eligible as `event=push` CI_SUCCESS evidence.

## 14. Sequence after this packet

Sol exact-corrected-head confirmation against the five prior findings -> Dustin's D1-D6 design-direction ruling -> Stage-0 PRD 1 (fail-loud) -> its independent review + Gate A -> land -> Stage-0 PRD 2 (gate swap) with the six pre-Gate-A evidence items satisfied -> its independent review + Gate A -> land. No Stage-0 PRD is opened before this packet is confirmation-clean and ruled.
