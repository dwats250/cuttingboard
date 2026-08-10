REVIEWED COMMIT: de3cc6ef7991dcb6ac307d09f91b665deb58b433
REVIEWED ARTIFACT: audits/morning-executor-material-packet-2026-08/PACKET.md
REVIEWER: gpt-5.6-sol, reasoning=max, read-only, GOV-2 upstream material-packet review
PRIMARY QUESTION: No. The core boundary is sound, but authority ordering, CI-run selection, failure notification, consumer inventory, and artifact-gate ordering require one bounded packet correction before Dustin can rule.

VERDICT: REQUIRED CHANGES

REQUIRED CHANGES: One consolidated bounded correction only is permitted; it must address all items below.

1. Sections 3, 10, and 13 - D1 is incorrectly called "Formal Gate-A authorization" before PRD 2 exists or has independent review. D2 similarly reads as advance implementation authorization. GOV-2 section 2 orders design-direction ruling, PRD drafting, independent PRD review, and only then Gate A. Recast D1 and D2 as non-binding directions for what PRD 2 may propose; reserve implementation authorization for the later reviewed PRD 2 Gate A. Make current branch-protection proof a pre-ruling premise rather than an unproven falsifier.

2. Sections 6, 9, and 11 - The Actions-API authority rule is not total. "Select the run" does not define pagination, multiple matching run objects, HTTP/auth/schema failures, or how ambiguity fails closed. The five revision states begin only after a unique run has been selected. Define deterministic current-run/current-attempt selection, require complete result handling, and add named non-success proof outcomes or an explicit proof-error class. Extend evidence and invalidators to cover multiple objects and pagination, not only reruns of one object.

3. Sections 4 and 10 - The failure-notification seam is not realizable as specified. `format_failure_notification` discards `date_str` at cuttingboard/notifications/__init__.py:586-607, and the packet names no reliable workflow-context carrier for the failed step. Either narrow the claim to an honestly available workflow/mode failure or specify explicit stage/date inputs. Require an executable test of the exact invoked handler or extracted helper with a stale latest_run.json present and the pre-install fallback exercised; the structural YAML assertion remains useful but is insufficient alone.

4. Section 7 - The claimed verified reader set is factually wrong and incomplete. cuttingboard/evaluation.py:37-49 reads audit.jsonl, not latest_run.json. Actual omitted readers include `verify_run_summary` through cuttingboard/runtime/__init__.py:206-213, 273, 1645-1684 and direct validation-shell reads. Perform the one GOV-2 consumer-inventory refresh and replace the false enumeration. This does not overturn the no-schema-change direction, but the packet cannot remain review-clean with a false completeness claim.

5. Sections 5, 7, and 11 - Pin the current-generation ordering for the morning artifact gate. The current morning workflow renders and stages UI inside `Commit artifacts` at cuttingboard.yml:309-339; a separate gate placed before that step could validate stale checked-in HTML. Specify the exact morning artifact set and require generation/render, readiness validation, commit, then push. Re-estimate both FILES and LOC afterward, use GOV-2's `ESTIMATED SURFACE - NOT YET APPROVED` label, and allow realistic margin: PRD 1's 10-25 lines do not safely cover stage provenance plus an early-failure fallback, while PRD 2's 300-line top is tight once total API handling and workflow splitting are counted.

RECOMMENDATIONS (non-blocking):

1. For D5, prefer a dedicated scripts/check_runtime_readiness.py. tools/engine_doctor.py is a broad 652-line diagnostic that scans dependency cycles, imports a large catalog, checks baseline files including `.env`, and can run pytest. Narrowing it risks preserving unrelated, mutable diagnostic authority inside a production gate.

2. The quiet-main drift gap is meaningful because ci.yml runs only on pull_request/push while pyproject.toml:6-20 leaves most runtime and test dependencies lower-bound-only and the runner is `ubuntu-latest`. If D4 selects recovery, make it a separate non-blocking DRIFT OBSERVATION run and keep it excluded from the event=push CI authority proof.

FINDINGS (per verification item 1-12):

1. BOUNDARY: PASS. Sections 2 and 5 define one executor-hardening track separate from Cloudflare, PRD 1 as additive fail-loud only, and PRD 2 as the atomic removal/proof/permission/runtime-readiness/post-health unit. Sections 2, 3, 5, and 11 expressly exclude wall-clock staleness, slot canonicalization, a fourth slot encoding, latest_run.json schema or SHA changes, attempt artifacts, hourly dedup reuse, Cloudflare surfaces, and PRD-293.

2. ORDERING: PASS. No safe PRD-2-first ordering exists under this boundary. ci.yml:6-22 can have a red or pending push run for main; PRD 2 would then block before the live step at cuttingboard.yml:231-240. The current morning job has no Telegram credentials at cuttingboard.yml:46-56, so landing PRD 2 first would introduce additional silent pre-execution blocks unless it absorbed PRD 1 and violated the frozen separation. Fail-loud-first is necessary.

3. EXACT-SHA CI AUTHORITY: REQUIRED CHANGE. Exact HEAD, event=push, ci.yml path, completed status, success conclusion, missing/pending/failed handling, HEAD recheck, and non-retroactivity are correctly stated. Exact SHA prevents older-SHA success, and ci.yml contains no runtime/API dependency, so there is no CI-runtime circle. However, multiple matching run objects, pagination, and API/proof failures have no total state. CI_SUCCESS/PENDING/MISSING/FAILED/REVISION_DRIFT cover revision outcomes only after unambiguous selection. The packet correctly prohibits treating CI_SUCCESS as evidence that an observation occurred.

4. PERMISSIONS: PASS. cuttingboard.yml:38-39 currently grants only `contents: write`; the packet explicitly adds `actions: read` and preserves `contents: write`. The selected Actions workflow-runs API requires Actions read authority. `checks: read` is unnecessary because the packet rejects the check-runs aggregate. No additional permission is justified.

5. OBSERVATION TRUTH: CONTRACT PASS, INVENTORY FAIL. The proposed CI and readiness gates occur before `python -m cuttingboard`; the current writer is reached only after pipeline execution at runtime/__init__.py:265-288 or its entered-pipeline failure path at 300-334. Thus CI_PENDING/MISSING/FAILED/REVISION_DRIFT and other pre-execution blocks need not write latest_run.json. dashboard_renderer.py:3281-3290, cuttingboard.yml:278-307, and hourly_alert.yml:71-87, 151-157 are real readers/restorers. evaluation.py is not. No discovered consumer makes latest-executed-observation-only false.

6. PRD 1 FAIL-LOUD: REQUIRED CHANGE. An `if: failure()` terminal handler using workflow context can report a failed job even when the live pipeline never ran and a stale latest_run.json exists, and the packet explicitly bans deriving the reason from that file. The proposed builder currently drops the supplied date, and failed-step provenance is undefined. Structural YAML plus a formatter unit test cannot prove the actual early-failure command runs or avoids stale data. A bounded executable handler test is required; a full hosted-Actions end-to-end test is not.

7. PRD 2 RUNTIME READINESS: DEDICATED SCRIPT IS SAFER. engine_doctor.py:79-111, 142-159, 224-272, and 575-648 mixes runtime prerequisites with repository-wide import catalogs, dependency-cycle analysis, baseline files, reporting, and optional pytest. A dedicated checker can expose a closed, deterministic, seconds-fast set of runtime prerequisites with one red mutation per check and no partial-suite behavior. D5 remains Dustin's decision, including the exact check list.

8. POST-EXECUTION READINESS: PARTIAL. scripts/check_readiness.py:20-41, 125-142 can be parameterized while retaining its current no-argument hourly behavior. The packet repeatedly requires a regression test for the hourly artifact list and exit codes, satisfying the hourly-preservation obligation. It does not yet secure current-generation morning ordering because rendering presently occurs inside the commit step; that seam requires correction.

9. DAILY TEST SIGNAL: MEANINGFUL DRIFT GAP, NOT MERGE AUTHORITY. Removing the scheduled morning suite eliminates observation of dependency, runner-image, and environment drift on quiet-main days. A separate scheduled full-suite run can recover that signal, but its result must remain DRIFT OBSERVATION only: it neither authorizes merges nor qualifies as event=push CI_SUCCESS and must never gate a morning slot. D4 remains an owner cost/noise decision.

10. PRE-GATE-A EVIDENCE: PASS WITH THE CI-SELECTOR CORRECTION. Sections 9 and 11 correctly retain workflow-token Actions-API capability, rerun/current-attempt semantics, expanded CI-latency sampling, per-check deterministic runtime-readiness red evidence, and unchanged hourly readiness behavior as blockers before PRD 2 Gate A. Local `gh` evidence is expressly rejected. Rerun evidence must be widened to multiple-run and pagination behavior. Live branch protection is external to the tree and must also be current before D1.

11. CEILINGS: REQUIRED CHANGE. GOV-2 section 5 and PRD_PROCESS.md:666-680 require validation and proof-support code to be estimated as first-class surface and prescribe the provisional estimate label. The current ranges omit realistic pressure from failed-stage provenance, fallback execution, total API error/cardinality handling, and current-generation render/gate splitting. The conditional D4 file surface is also absent if Dustin selects it.

12. OWNER DECISIONS: D1-D6 remain the minimum set. Technical evidence and packet corrections do not create a seventh owner decision. D1 and D2 must be expressed as design directions, not premature Gate A or implementation authority.

OWNER DECISIONS STILL REQUIRED:

1. D1: Whether PRD 2 may propose removing operational pytest/ruff from morning runtime, with actual authorization reserved for reviewed PRD 2 Gate A.

2. D2: Whether PRD 2 may propose adding `actions: read` while retaining `contents: write`, again subject to reviewed PRD 2 Gate A.

3. D3: CI_PENDING policy - immediate named failure, bounded wait, or hybrid - and the exact wait budget if applicable.

4. D4: Whether to recover quiet-main drift observation with a separate scheduled, non-blocking full-suite run.

5. D5: Dedicated runtime-readiness checker versus a narrowed engine doctor, plus the exact closed check list.

6. D6: The executable failure-notification red-test mechanism and the exact stage/date contract.

CLOSING: One consolidated bounded correction cycle must repair the authority wording, CI selector, fail-loud seam, reader inventory, artifact-gate ordering, and provisional ceilings. The exact corrected head then requires GOV-2 confirmation before Dustin's D1-D6 design-direction ruling or Stage-0 PRD 1 drafting authority; neither PRD is authorized or implemented by this review.
