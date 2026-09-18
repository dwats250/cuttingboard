# Codex Event-2 ATTEMPT 3 exact-corrected-head confirmation prompt -- Hourly admission / notification MATERIAL packet

```
GOV-2 sec7 step 3 dispatch prompt, ATTEMPT 3 (after the wording repair recorded in packet section 13). Invocation: cbagent launch-codex (read-only sandbox, model_reasoning_effort=high), 2026-09-17. Corrected packet head named inside: bb3e7affc9bc3eedc0bca9712019ee1026f58015. HEAD is exactly one docs-only commit ahead that adds only this prompt file.
```

---

You are Sol, a commissioned fresh-context independent reviewer (Adversary seat) for the Cuttingboard repository at the working directory you were launched in. Read-only. Do not edit files. Do not implement anything. You have NO memory of the Event-1 pass; read its committed record.

CONFIRMATION TARGET
- Packet: audits/hourly-admission-notification-material-packet-2026-09/HOURLY_ADMISSION_NOTIFICATION_MATERIAL_PACKET_2026-09-17.md
- Event-1 record: audits/hourly-admission-notification-material-packet-2026-09/CODEX_EVENT_1_REVIEW_2026-09-17.md. Event-2 ATTEMPT 1 record: CODEX_EVENT_2_CONFIRMATION_ATTEMPT_1_2026-09-17.md. Event-2 ATTEMPT 2 record (NOT CONFIRMED: only the EXPIRY-BOUNDARY reachability wording and the 06:30 PT slot range): CODEX_EVENT_2_CONFIRMATION_ATTEMPT_2_2026-09-17.md, same directory. Read all three.
- Corrected packet head: bb3e7affc9bc3eedc0bca9712019ee1026f58015 (branch claude/hourly-admission-material-packet). Verify `git rev-parse HEAD~1` equals it and `git diff def0eb83..HEAD --stat` lists only the packet directory. If not, say so and stop.
- Base / main: def0eb83963bc02865ae46759f323ec47d1f89fe.
- Effort: HIGH. This is the ONE exact-corrected-head confirmation of GOV-2 sec7. If you find a NEW material boundary omission the packet reopens as DESIGN INCOMPLETE; say so explicitly.

TASK
1. For the Event-2 attempt-2 residual (EXPIRY-BOUNDARY reachability: session-equality check at effective_permission.py:224-225 precedes expiry; canonical slots hourly_slot.py:27-42 start 06:30 PT; test H must be characterized as synthetic) and, briefly, for each Event-1 REQUIRED 1-5 and RECOMMENDED 1-4, state whether the corrected packet ACTIONS it correctly and completely, with the packet section and the repository file:line you checked. Use exactly one of: CONFIRMED / NOT CONFIRMED (with the smallest residual) / SUPERSEDED (explain).
2. Re-verify the correction itself against the code, not the packet's description:
   a. D3 session parity: with `CB_WORKFLOW_SESSION` frozen by the workflow before "Run hourly alert" and consumed by both the runner pre-flight and tools/ci_push_artifacts.sh:40, is there ANY remaining input on which runner admission and publisher admission can disagree (accepted tip, incoming envelope, session, now)? Is the `or date_str` fallback safe (only reachable when no workflow session is set)?
   b. D2 as repaired: the persisted carrier block (:755-764) and the artifact clock (:715) are NOT moved; the pre-flight is a separate read-only copy of the carrier computed before the send. Confirm the persisted envelope, contract, summary and generation identifiers are byte-identical to today on every path, and that the EXPIRY-BOUNDARY residual in D5 is bounded exactly as stated (valid_until always 08:00Z, effective_permission.py:83-88; canonical slots 06:00-13:00 PT, hourly_slot.py:32; only a manual --force-slot run at 07:59:5xZ can straddle it). Confirm test H and M6/M7 are discriminating as rewritten.
   c. D4 HALT context: confirm `validation_summary.halt_reason` is set and readable at the pre-flight point on every kill-switch path (runtime :593-599 and :689), that the composed reason fits the 120-char truncation at :924 with the constant at :3087, and that no other bounded HALT context the ordinary alert carries is lost.
   d. Test D as rewritten: confirm tests/test_hourly_slot_idempotency.py's harness can drive two same-slot arrivals through alert_runner with the carrier inadmissible, and that the assertions (no last_hourly_slot.json after the first; second arrival reaches _execute_notify_run; two failure sends; zero ordinary) are observable and RED/GREEN as stated.
   e. Test G and M5/M6: are they discriminating on the pre-packet runtime?
   f. FILES completeness after the correction (the added workflow step, tests/test_hourly_slot_idempotency.py, the named fixture scope).
3. Any NEW finding not covered by Event-1, with file:line evidence. Do not re-litigate Event-1 findings that are CONFIRMED.

OUTPUT FORMAT (markdown, plain ASCII only; no em-dashes, smart quotes, arrows, or emoji)
# Hourly admission / notification MATERIAL packet - Sol / Codex Event-2 confirmation, ATTEMPT 3
- CONFIRMED HEAD: <sha of HEAD~1>
- VERDICT: CONFIRMED-CLEAN | NOT CONFIRMED | DESIGN INCOMPLETE
- EVENT-1 DISPOSITIONS: REQ-1..5, REC-1..4, one line each
- RE-VERIFICATION 2a-2f: one short paragraph each with file:line
- NEW FINDINGS: numbered or "none"
- RATIONALE: short
