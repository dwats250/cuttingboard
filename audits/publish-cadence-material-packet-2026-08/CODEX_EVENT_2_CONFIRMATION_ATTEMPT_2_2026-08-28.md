# Codex Event-2 exact-corrected-head confirmation — ATTEMPT 2

```
GOV-2 sec7 artifact. Against head: 78c3627d52f208f5ac887f6d7f7b0f72051458f8
Invocation: codex exec -s read-only, captured verbatim from stdout 2026-08-28.
VERDICT: NOT CONFIRMED (single residual: Q4's stale "CF-only" wording vs the
corrected CF-primary ownership); F3/F5/F6/F10 PASS. The one-line repair is
applied in the next revision; ATTEMPT 3 follows.
```

---

Confirmed head SHA: 78c3627d52f208f5ac887f6d7f7b0f72051458f8

F3: PASS — Sec7 requires “at most one send” on the healthy path and assigns failure paths to bounded at-least-once regressions; remaining “exactly one send” occurrences only negate or describe the retired claim.

F5: PASS — Sec1.7 now states up to 48 yfinance logical operations + 1 Cboe invocation hourly and ≈525 yfinance logical operations + 9 Cboe invocations per PDT day; the old figure remains only quoted as removed in the repair record.

F6: PASS — The FILES cone includes `tests/test_hourly_slot.py:test_allowed_pt_slots_exact_set` at line 144, and sec7 mandates a workflow-shape assertion pinning the exact retimed cron set.

F9: FAIL — Sec3 labels 06:45 “CF-primary” and Q9(b) permits delayed-heartbeat delivery, but Q4 still says “06:45 is CF-only,” leaving the ownership disposition internally contradictory.

F10: PASS

VERDICT: NOT CONFIRMED (F9)

Independence/read-only attestation: Independently checked the exact corrected head and bounded residuals without writing to the repository; the worktree remained clean.
