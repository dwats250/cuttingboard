# Codex Event-1 review prompt -- Hourly admission / notification MATERIAL packet

```
GOV-2 sec2 step 3 dispatch prompt. Invocation: cbagent launch-codex (read-only sandbox, model_reasoning_effort=high), prompt file on stdin, artifact written from the job's result.md by the authoring session, 2026-09-17. Reviewed head named inside: 6505e2a3063217b0fc3084fe61f45119668a7c6b.
```

---

You are Sol, a commissioned fresh-context independent design reviewer (Adversary seat) for the Cuttingboard repository at the working directory you were launched in. Read-only. Do not edit files. Do not implement anything.

REVIEW TARGET
- Packet: audits/hourly-admission-notification-material-packet-2026-09/HOURLY_ADMISSION_NOTIFICATION_MATERIAL_PACKET_2026-09-17.md
- Frozen packet head: 6505e2a3063217b0fc3084fe61f45119668a7c6b (branch claude/hourly-admission-material-packet). HEAD is exactly one docs-only commit ahead of it that adds only this prompt file; verify `git rev-parse HEAD~1` equals the packet head and `git diff def0eb83..HEAD --stat` lists only the packet directory. If not, say so and stop.
- Base / main: def0eb83963bc02865ae46759f323ec47d1f89fe.
- Effort: HIGH. This is a MATERIAL, HIGH-RISK design packet review before any PRD or implementation exists. No implementation exists; do not ask for one.

CONTEXT YOU MUST READ FIRST
- CLAUDE.md, docs/contract/MODE_REVIEW.md, docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md sections 1, 2, 7.
- docs/prd_history/PRD-339.md and PRD-340.md (EffectivePermission Slice 1 / Slice 2; R3, R5, R7, Q4, D1-D3, the exclusive-writer rule and the channel enumeration in cuttingboard/authority_projection.py).
- cuttingboard/effective_permission.py (unavailable, _valid_canonical, admit_persisted, publication_admits, persist, _read_authority), cuttingboard/authority_projection.py (admit_projection, admit_ep, _cli).
- cuttingboard/runtime/__init__.py :540-972 (_execute_notify_run) and :1241-1257 (_load_accepted_authority); cuttingboard/alert_runner.py; cuttingboard/notifications/hourly_slot.py; cuttingboard/notifications/__init__.py :623 (format_failure_notification); cuttingboard/output.py send_notification / send_telegram.
- .github/workflows/hourly_alert.yml (all steps and their `if:` gates), tools/ci_push_artifacts.sh (authority_guard), tools/ci_restore_publish_state.sh, scripts/check_hourly_liveness.py.
- tests/test_hourly_alert.py :991-1110, tests/conftest.py :150-175, tests/test_effective_permission.py, tests/test_publish_authority_nonregression.py, tests/test_ci_artifact_hygiene.py.

ATTACK SURFACE (address each explicitly, with file:line evidence)
1. Incident account: verify every claim in packet section 1 against the repository and the publish branch history you can see (`git fetch origin publish` is allowed; GitHub API access may not be). Name any claim you cannot verify offline as UNVERIFIED rather than accepting it.
2. Ordering table: is every step and line range in section 2 current at the frozen head? Is anything between the ordinary send (:696-698) and the carrier block (:756-761) that the hoist in D2 would reorder with observable effect (contract/summary content, alert_sent, market map, audit rows)?
3. Canonical seam fidelity: does the D3 pre-flight call publication_admits and admit_persisted with inputs that are EXACTLY the publisher's (accepted = origin/publish tip carrier as restored; incoming = the envelope persist() will write; session = runner UTC date; now=None)? Identify any input where the runner and the publisher could disagree (restore timing, main-frozen copy, session date at a UTC day boundary, tz of run_at_utc). Is calling the underscore helper _read_authority from runtime an authority-authorship or exclusive-writer violation under PRD-339 R4/exclusive-writer AST guard, or a permitted read?
4. Authority duplication: does D3 duplicate R5 semantics in any way, or introduce a second authority implementation? Would a future change to publication_admits leave the pre-flight stale?
5. Refusal path: confirm that raising inside the try block reaches the except branch at :914 with the documented effects (one failure send, traceback.txt, error contract, FAIL summary, exit 1) and that NO ordinary send can precede it. Check whether any code between the hoisted block and :698 could itself raise after a partial write.
6. Ruling 1 (HALT context): is the HALT context available at the pre-flight point in a bounded form (which variable/line), and does prefixing it into a <=120-char reason honestly preserve "the existing bounded reason/context"? Is truncation a risk? Propose the exact source if the packet's description is too vague.
7. Ruling 2 (dedup): verify the claim that no cross-run state survives a refused publish and that last_hourly_slot.json is written only on alert_sent. Does alert_runner's same-slot dedup or window logic interact with the FAIL exit in any way that could suppress a legitimate later slot or re-admit the same slot unexpectedly?
8. Zero publication on refusal: walk every hourly_alert.yml step gate and confirm none can publish or advance the publish branch after a FAIL exit. Confirm "Upload failure artifacts" retains the diagnostic set. Confirm liveness can still go RED.
9. Restore-list change (D1): does restoring logs/latest_hourly_contract.json read-only in the hourly lane create any republish, ownership, or dirty-tree hazard (ci_push aborts on a dirty tree; the daily lane reverts this file at cuttingboard.yml:552)? Does the freshcheck (payload mtime) interact?
10. Test-ripple and vacuity: is the conftest autouse plan sound, or does it mask the very behavior under test in other files? For each test A-F and mutation M1-M4, would it actually be RED/GREEN as stated on the pre-packet runtime? Name any test that is vacuous or any FAIL line that is not observable.
11. Admissible-day regression: with the hoist in place, is there any admissible hourly run whose ordinary alert, contract, summary, save_last_slot, or published bytes would differ from today? Consider system_halted, operator_locked, STAY_FLAT, kill switch, and the qualify-only mode.
12. Scope and materiality: is HIGH-RISK / MATERIAL correct; are FILES complete (any test that pins the ordinary-send-before-contract ordering, the summary's alert_sent field, or the error-contract shape that the packet did not list)? Is anything in the packet an implementation instruction that belongs in the PRD instead?
13. Invariants: is any invariant in section 8 actually changed by D1-D6? Does D4's reuse of the generic exception branch change the market-stress HALT semantics on ADMISSIBLE days in any way?

OUTPUT FORMAT (markdown, plain ASCII only; no em-dashes, smart quotes, arrows, or emoji)
# Hourly admission / notification MATERIAL packet - Sol / Codex Event-1 review
- REVIEWED HEAD: <sha>
- VERDICT: ACCEPT | ACCEPT WITH CHANGES | REJECT
- REQUIRED CHANGES: numbered, each with file:line evidence and the smallest observable correction
- RECOMMENDED CHANGES: numbered
- ATTACK SURFACE DISPOSITIONS: one line per item 1-13 (CLEAN / FINDING n / UNVERIFIED)
- RATIONALE: short
Do not restate the packet. Do not propose a different mechanism unless a REQUIRED finding makes the ruled mechanism unsound; if so, say STOP and why.
