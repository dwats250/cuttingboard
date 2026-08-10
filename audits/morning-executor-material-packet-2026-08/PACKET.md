# MATERIAL PACKET - Morning Executor Truthfulness + Gate Swap

STATUS: DRAFT (pre-A0, pre-Stage-0). GOV-2 upstream material packet. Not binding; not authorization to implement. This document is the artifact that Codex packet review + exact-head confirmation + Dustin's design-direction ruling must clear before any Stage-0 PRD is opened.

CLASSIFICATION: MATERIAL under GOV-2 s1 (selects an implementation seam shared across all pipeline modes; changes a production execution/publish gate). CLASS: INFRA. Default tier T0 (CI gate feeds runtime execution). LANE: HIGH-RISK. `.github/workflows/**` is a protected, Bash-only-editable HIGH-RISK FILE.

TRACK: Own executor-hardening track, SEPARATE from the Cloudflare packet. CF-D4 retains the existing GitHub cron in slice 1; this defect and its fix exist regardless of Cloudflare, and Cloudflare later consumes the same "invocation authorizes an attempt" contract without co-design.

AUTHORITY MODEL: unchanged. GitHub remains executor/publisher/artifact authority. This packet touches no Cloudflare surface, no CF-E2, no CF-D1b, and no market/provider semantics.

## 0. Provenance

- Incident 2026-08-10: the nominal 06:00 PT live run started ~07:14 PT (scheduler drift; already mitigated for MODE by PRD-189 cron-string resolution) and FAILED before market execution because the unconditional repository-wide `pytest tests/ -q` gate (cuttingboard.yml:165) hit a flaky concurrency test (PRD-293 dev-bootstrap lock race), aborting the job -> latest_run.json stale, no publish, and the board gave no signal that today's slot missed. The hourly path (no test-suite gate) succeeded.
- Grounded recon (this session) + read-only GitHub API evidence confirm: the ci.yml `test` push-run for main HEAD `ddacbf0` was SUCCESS, while the same SHA's operational `pipeline` check shows `failure @ 2026-08-10T14:14Z` - i.e. main was CI-green; the pipeline's own re-run of the suite flaked. The full-suite morning gate is redundant re-validation of an already-validated revision, and its flakiness is the failure surface.
- Fable navigator pass (deep, read-only) recommended this two-PRD boundary and verified: the runtime token permission gap, that the CI proof relocates rather than eliminates the flake, that a latest_run.json SHA field is itself a MATERIAL schema change, and the frozen-board (PRD-250) constraint.

## 1. Problem (falsifiable)

A time-sensitive production morning observation is gated on the full repository test suite. Because the suite runs unconditionally before execution as a hard gate, ANY test failure (including an unrelated flaky test on a revision that already passed CI at merge) aborts the observation, leaves a stale prior success in latest_run.json, and produces no notification that the named slot missed. Quality control (the full suite) belongs at the merge gate (ci.yml, enforced by branch protection), not as a per-run runtime gate. FALSIFIER: if branch protection does NOT require ci.yml `test` SUCCESS before merge, main HEAD is not reliably CI-green and this framing fails (see Invalidators).

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

- This packet continues consuming the existing PRD-189 `scripts/resolve_run_mode.py` cron-string contract for mode identity. It does NOT introduce a fourth slot-time encoding, and it does NOT declare that module the permanent global clock source. Canonical clock consolidation (the three unsynchronized "13:00 UTC" encodings observed in evidence) belongs with the future Cloudflare explicit-slot work, not here.
- Because no slot-aware board logic is in scope (PRD 1 keeps the existing age-relative banner), the slot-time multiplicity RED is deferred by scope, not resolved here.
- The formal authorization to remove the full suite from morning runtime is a Gate-A ruling (Section 10), strongly implied by this direction but recorded as an explicit owner decision.

## 4. PRD 1 - Fail-loud additive truthfulness

PURPOSE: make "today's named morning slot did not produce a valid observation" observable, without promoting a failed attempt into valid market data, and without any gate/schema/permission change.

DESIGN:
- Add `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` to the cuttingboard.yml job `env:` (currently absent; hourly_alert.yml:40-42 already wires them).
- Add an `if: failure()` step that sends a Telegram failure alert naming the failed stage and the trading date. The message is built from workflow context ONLY (github.* + the failed step), never from latest_run.json. Minimum callable path: `cuttingboard.output.send_telegram(title, body)` (verified: no latest_run.json dependency) with a raw-stdlib `urllib` POST fallback for failures that precede dependency install.
- The existing client-side "BOARD N OLD" staleness banner (dashboard_renderer.py:244-290) remains the on-board stale signal; hourly re-render republishes it within the hour. No renderer change in PRD 1.

NON-GOALS (PRD 1): no gate change, no removal of the pytest/ruff steps, no permission expansion, no latest_run.json change, no attempt artifact, no slot-aware banner.

REALIZABILITY / RED TEST (open design point - see Section 10): a workflow if:failure notification is hard to red-test deterministically. Proposed: (a) a structural test asserting cuttingboard.yml wires an if:failure step that invokes the send path with TELEGRAM_* in env (pattern precedent: tests/test_resolve_run_mode.py asserts yaml wiring); plus (b) a unit test of the failure-message builder (reuse cuttingboard/notifications format_failure_notification). Owner/Codex to confirm this satisfies PRD-198 #4 or specify a stronger red test.

FILES (PRD 1):
- M `.github/workflows/cuttingboard.yml` (job env + if:failure step; Bash-only edit)
- M or A `tests/` (structural yaml assertion + message-builder unit test)
- (reuse) `cuttingboard/output.py` / `cuttingboard/notifications/__init__.py` - no change expected; reuse existing send + formatter
- Stage-0 bookkeeping (PRD doc, PRD_REGISTRY row, prd_index entry, PROJECT_STATE pointer)

LOC RANGE (PRD 1): ~10-25 net production/infra lines (workflow env + step; possibly a tiny message helper) + tests. Binding Gate-A ceiling set by Dustin at ruling.

## 5. PRD 2 - Atomic gate-swap unit (never split)

PURPOSE: stop gating the time-sensitive observation on the full suite; gate instead on (pre) the exact revision being CI-authoritative-green + runtime-ready, and (post) the produced artifact being healthy - preserving quality control at the merge gate.

ATOMIC UNIT (splitting creates an unguarded or double-gated interim; must land as one PRD):
1. Remove the pre-execution `pytest tests/ -q` (cuttingboard.yml:165) and `ruff` (:160) from the live/prefetch/sunday/verify execution path. The full suite + ruff remain in ci.yml (merge gate) unchanged.
2. Add the exact-SHA authoritative CI proof (Section 6) as a pre-execution gate.
3. Add `actions: read` to the cuttingboard.yml `permissions:` block (currently `contents: write` only); keep `contents: write`.
4. Add a deterministic runtime-readiness pre-gate (imports resolve, entrypoint + critical deps load, required config present, observation path invocable) - enumerated, seconds-fast, no concurrency/integration tests. Candidate: narrow/promote the existing engine_doctor.py (currently `|| true` non-blocking at :170) or a new scripts/check_runtime_readiness.py.
5. Add a morning post-execution artifact-health publish gate: extend scripts/check_readiness.py (PRD-287) to validate latest_run.json's health for the morning artifact set, invoked before Commit/Push. Hourly behavior stays bit-identical.
6. latest_run.json remains latest-executed-observation-only: a blocked/pending/drifted attempt that never executes MUST NOT write it (preserve the existing no-write-on-pre-execution-failure behavior); no schema change, no SHA field.

NON-GOALS (PRD 2): no staleness gate, no slot logic, no provenance schema field, no new artifact, no hourly-dedup reuse.

FILES (PRD 2):
- M `.github/workflows/cuttingboard.yml` (remove gate steps; add permission; add readiness pre-gate step; add CI-proof step; add post-execution artifact-health gate step; Bash-only edit)
- A `scripts/check_run_revision.py` (exact-SHA CI proof; typed states; fail-loud)
- A `scripts/check_runtime_readiness.py` (deterministic pre-gate) OR M/narrow `tools/engine_doctor.py`
- M `scripts/check_readiness.py` (parameterize for the morning artifact set; hourly path unchanged)
- A/M `tests/` (red tests: each typed revision state; each readiness check; morning check_readiness + a hourly-unchanged red test)
- Stage-0 bookkeeping (PRD doc, registry, index, PROJECT_STATE)

LOC RANGE (PRD 2): ~150-300 net production LOC (two new gate scripts + workflow rewiring + check_readiness extension), counting validation surface and typed-state guards as first-class per GOV-2 s5. State as a RANGE until Gate A; the binding ceiling is Dustin's Gate-A number set at the top of range + margin.

## 6. Exact-SHA authoritative CI proof contract (PRD 2)

MECHANISM (Actions API preferred, per evidence - avoids the polluted check-runs aggregate that mixes operational pipeline/alert/deploy checks, including today's own pipeline failure):
- Resolve the exact checked-out SHA: `git rev-parse HEAD` after `actions/checkout ref: main`.
- Query `GET /repos/{owner}/{repo}/actions/runs?head_sha={SHA}&event=push`, select the run with `path == .github/workflows/ci.yml`.
- Require `status == "completed"` AND `conclusion == "success"`.
- Read the CURRENT run object (reflects the latest attempt); never a cached prior success.

TYPED REVISION STATES (each maps to a named, notified, fail-loud outcome; none silently passes):
- CI_SUCCESS: exactly one selected ci.yml push run for the SHA is completed+success -> proceed to runtime-readiness + execution.
- CI_PENDING: the ci.yml push run exists but status != completed -> policy (Section 10; owner-chosen).
- CI_MISSING: no ci.yml push run found for the SHA (covers [skip ci], the ~2-3s pre-creation window, path/skip holes) -> named failure, skip.
- CI_FAILED: the ci.yml push run completed with conclusion != success -> named failure, skip.
- REVISION_DRIFT: the SHA proven at proof time != the SHA at execution time (re-check HEAD immediately before execution) -> named failure, skip.

INVARIANT: CI_SUCCESS authorizes an OBSERVATION ATTEMPT; it is NEVER evidence that an observation occurred or was valid. A post-execution conclusion flip is declared non-retroactive: the proof records what was authoritative at attempt time.

## 7. Consumer / seam analysis

- latest_run.json readers (verified): dashboard_renderer.py (UPDATED line / age banner), the in-workflow commit-message generator (cuttingboard.yml:279-307), cuttingboard/evaluation.py, and hourly_alert.yml (restores it read-only and reverts). Therefore: no schema change; a blocked attempt writes nothing; latest_run.json = latest executed observation only. This is why a SHA provenance field is OUT of scope (it would be a multi-reader persisted schema change = its own MATERIAL surface).
- check_readiness.py is shared code (hourly-owned today). The morning extension must be parameterized so hourly's artifact list + exit behavior stay bit-identical (red test required).
- Permission: `actions: read` added; `contents: write` preserved for the artifact commit/push; no over-grant.
- Signal-loss note: removing the morning suite ends the only SCHEDULED full-suite run on main (ci.yml fires only on PR/push). Merge authority is untouched, but daily test signal on quiet no-merge days disappears. Owner decision (Section 10): optionally add a separate scheduled full-suite drift run (non-blocking to the slot).

## 8. Semantic-failure hardening (PRD-198) applied

- Fail-loud, never silent-fallback: every non-CI_SUCCESS state is a named, notified failure; CI_MISSING never reads as pass.
- Assert the resolved, not the requested: prove the exact SHA's ci.yml push-run conclusion, not "main is green by construction."
- Authoritative source, not proxy: the ci.yml push run conclusion (the merge gate's own result), selected by event+path, not the aggregate check-runs list.
- Every guard ships a red test: each typed revision state, each readiness check, the morning artifact-health gate, and hourly-unchanged.
- Verify where truth is determined: the token capability (actions:read resolves the push run) is proven FROM a workflow run (Section 9 #1), not from local gh.
- Pin identities that matter: exact SHA + workflow path + event=push; re-check HEAD for REVISION_DRIFT.

## 9. Pre-Gate-A evidence requirements (must be satisfied before Gate A)

1. Prove FROM a real workflow run that `actions: read` lets GITHUB_TOKEN resolve the exact-SHA authoritative ci.yml push run (local gh success is insufficient).
2. Deliberately inspect rerun semantics: rerun a failed ci.yml run and confirm the current authoritative attempt cannot be confused with a superseded run (a prior success must not mask an active/failed rerun, and vice versa). (No rerun was observed in read-only sampling.)
3. Expand CI-latency sampling (read-only sampling to date: ~74-87s over n=3) enough to support the chosen CI_PENDING policy (esp. if a bounded-wait budget is selected).
4. Prove the runtime-readiness checks are enumerated, deterministic, and red-testable per check (PRD-198 #4) - no concurrency/integration/flaky checks.
5. Prove the morning check_readiness extension leaves hourly behavior bit-identical (red test on hourly's artifact list + exit codes).

## 10. Exact owner decisions still required

D1. Formal Gate-A authorization to remove pytest/ruff from morning runtime (the core ruling; strongly implied by Section 3 but must be explicit).
D2. Authorize the `actions: read` permission expansion in the T0 cuttingboard.yml.
D3. CI_PENDING policy: Option A (immediate named failure), B (short bounded wait ~<= observed p100 then decide), or C (hybrid); and the wait budget if B/C. Cross-cut: any wait must stay well under the slot's usefulness window.
D4. Whether to add a separate scheduled full-suite drift run to recover the lost daily test signal (Section 7), or accept its loss.
D5. Runtime-readiness pre-gate source: narrow/promote engine_doctor.py vs a new scripts/check_runtime_readiness.py; and confirm the exact check list.
D6. PRD 1 red-test strategy for the if:failure notification (structural yaml assertion + message-builder unit test, or a stronger mechanism).

## 11. Invalidators

- Branch protection does NOT require ci.yml `test` SUCCESS before merge -> the merge gate does not guarantee main HEAD green; removing the morning suite would weaken QC; packet must be re-scoped (Section 1 falsifier).
- Evidence #1 fails: actions:read does not let GITHUB_TOKEN resolve the exact-SHA push run from a workflow run -> the CI proof (PRD 2 core) is not implementable as designed -> STOP, redesign the proof.
- Evidence #2 shows a superseded success can mask an active/failed rerun with no reliable discriminator -> the "current authoritative attempt" definition is unsafe -> STOP.
- Evidence #4/#5 fail: readiness checks cannot be made deterministic/red-testable, or the check_readiness extension cannot leave hourly bit-identical -> PRD 2 reintroduces a flaky gate or breaks hourly -> re-scope.
- Any OUT-of-scope entry appears (staleness gate, slot canonicalization, 4th slot encoding, provenance schema field, hourly-dedup reuse, CF entanglement, PRD-293 fix) -> boundary breach; return to this packet.
- Dustin declines D1 -> whole packet invalid.

## 12. Codex/Sol packet-review checklist

Boundary and atomicity:
- [ ] Two PRDs correctly separated; PRD 1 is truly additive (no gate/schema/permission/artifact change); PRD 2 is one atomic unit (removal + proof + permission + readiness pre-gate + artifact-health gate), with no split that yields an unguarded or double-gated interim.
- [ ] No OUT-of-scope surface present (staleness gate, slot canonicalization, 4th slot-time encoding, latest_run.json schema/SHA field, new attempt artifact, hourly-dedup reuse, CF-E2/D1b, PRD-293).

Exact-SHA CI proof:
- [ ] Uses the Actions API (event=push + path=ci.yml + completed + conclusion=success), NOT the polluted check-runs aggregate.
- [ ] All five typed states handled; each non-SUCCESS is named + notified + fail-loud; CI_MISSING never reads as pass; REVISION_DRIFT re-checks HEAD at execution time; conclusion flips declared non-retroactive.
- [ ] Invariant preserved: CI success authorizes an attempt, never evidences an observation; latest_run.json = latest executed observation only (no write on blocked/pending/drifted attempt).

Permissions and seams:
- [ ] actions:read added; contents:write preserved; no over-grant.
- [ ] check_readiness morning extension leaves hourly bit-identical (red test present).
- [ ] Runtime-readiness pre-gate enumerated, deterministic, red-testable per check; not the full suite; no concurrency/integration tests.
- [ ] Signal-loss (no scheduled full-suite on quiet days) is acknowledged and D4 is decided.

Hardening and evidence:
- [ ] PRD-198 invariants applied (fail-loud, assert-resolved, authoritative-source, red-test-per-guard, verify-at-CI, pinned identities).
- [ ] Pre-Gate-A evidence #1-#5 listed and gate the ruling; #1 (token capability) proven from a workflow run, not local gh.
- [ ] FILES/LOC ceilings realistic; validation surface counted as first-class (GOV-2 s5); PRD 2 stated as a range until Gate A.
- [ ] PRD 1 red-test for the if:failure notification is real (not a can't-fail test).

## 13. Sequence after this packet

Codex packet review (read-only) -> one bounded correction -> independent exact-corrected-head confirmation -> Dustin design-direction ruling (deciding D1-D6) -> Stage-0 PRD 1 (fail-loud) -> its review + Gate A -> land -> Stage-0 PRD 2 (gate swap) with the five pre-Gate-A evidence items satisfied -> its review + Gate A -> land. No Stage-0 PRD is opened before this packet is review-clean and ruled.
