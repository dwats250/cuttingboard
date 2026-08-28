# Codex Event-2 exact-corrected-head confirmation — ATTEMPT 1

```
GOV-2 sec7 artifact. Against head: 7a2acb9b6f7deec3edfa1e446e31f2f536fbc2b6
Invocation: codex exec -s read-only, captured verbatim from stdout 2026-08-28.
VERDICT: NOT CONFIRMED (F3 sec7 contradiction, F5 sec1 residual arithmetic,
F6 missing tests/test_hourly_slot.py, F9 winter-ownership/failure-coverage/
06:45-contention dispositions). F1/F2/F4/F7/F8 PASS. Bounded repair applied
in the next revision; ATTEMPT 2 follows, per the GEX-2 precedent.
```

---

- Confirmed head SHA: `7a2acb9b6f7deec3edfa1e446e31f2f536fbc2b6`
- F1: PASS — `(6,0)` is retired, 06:30 heartbeats move to `40 13`/`40 14`, and sec5 enumerates daily/hourly notification state, runtime send/persist, both CI transport scripts, all three Pages writers, and `ui/` last-writer semantics.
- F2: PASS — sec3 defines explicit `kind` + `slot` dispatch inputs and `--routine-slot`; wall-clock inference remains on GitHub heartbeat arrivals, with the known identity-shift residual submitted in Q9.
- F3: FAIL — sec2/sec3 correctly state at-least-once behavior and sec7/Q10 cover failure residuals, but sec7 still demands “CF dispatch + cron arrival same slot -> exactly one send,” directly contradicting the claimed removal of that guarantee.
- F4: PASS — sec4 makes `event.scheduledTime` authoritative, specifies a static `(cron, offset) -> slot/NO-OP` table, disambiguates `14:00Z`, and requests the extension ruling in Q8.
- F5: FAIL — sec6 has the corrected `48 yfinance + 1 Cboe` logical-operation ceiling and approximately-zero slot-swap delta, but sec1 still retains the erroneous “≈49 requests” and “~534 yfinance + 9 Cboe” accounting.
- F6: FAIL — the requested runtime/CI/Node/idempotency surfaces and widened falsifier are present, but the FILES cone omits `tests/test_hourly_slot.py`, whose `test_allowed_pt_slots_exact_set` must change when `(6,0)` is removed and `(6,45)` added; no existing or mandated test pins the exact retimed cron set.
- F7: PASS — Q7–Q11 are present and material, and Q5 explicitly reclassifies any separated cache work as non-MICRO.
- F8: PASS — sec1 uses “repository-recorded as undeployed,” states that no CF-E1 completion evidence exists, and disclaims live Cloudflare-account verification.
- F9 new-material-class check: FAIL — the fixed `13:05Z` daily fallback precedes the proposed 06:00 PT Worker dispatch in winter (05:05 PST versus 06:00 PST) and a successful scheduled run qualifies for first-success suppression, so it can suppress the supposedly primary 06:00 Worker run; retiring `(6,0)` also removes the independent 06:00 failure-coverage path, while a sufficiently delayed 06:40 heartbeat can infer `(6,45)` even after a successful CF 06:30 run and contend with the claimed CF-only 06:45 owner. These ownership/availability consequences and exact-cron regression requirements are not dispositioned.
- VERDICT: NOT CONFIRMED (F3, F5, F6, F9)
- Independence/read-only attestation: I did not author or modify the packet, made no repository changes, created no review artifact, and performed no implementation. The checkout remained clean at the exact corrected head before and after review. GitNexus was indexed against stale temporary sibling checkouts, so I did not refresh it or treat its graph output as evidence.
