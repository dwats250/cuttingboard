# Codex Event-2 exact-corrected-head confirmation — ATTEMPT 3

```
GOV-2 sec7 artifact. Against head: 3a0171bcfd68a9f3266e35639a07e8ed7b1b6b2f
Invocation: codex exec -s read-only, captured verbatim from stdout 2026-08-28.
VERDICT: NOT CONFIRMED (single residual: sec10's "06:45 exists only when CF
dispatches it" vs CF-primary ownership); F11 PASS. Repaired next revision;
ATTEMPT 4 follows.
```

---

Confirmed head SHA: 3a0171bcfd68a9f3266e35639a07e8ed7b1b6b2f

F9: FAIL — Sec3/Q4/Q9 consistently establish CF-primary ownership with possible delayed-heartbeat delivery, but sec10 still claims “06:45 exists only when CF dispatches it” outside the repair-record quotations.

F11: PASS — The Q4 repair introduces no new boundary; it only aligns Q4 with the already-dispositioned Q9(b) delayed-heartbeat corner.

VERDICT: NOT CONFIRMED (F9)

Independence/read-only attestation: Independently checked the exact corrected head and bounded residual without writing to the repository; the worktree remained clean.
