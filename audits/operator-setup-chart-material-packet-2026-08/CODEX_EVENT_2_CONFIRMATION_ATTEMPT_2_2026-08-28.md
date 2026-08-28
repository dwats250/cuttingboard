# Codex Event-2 exact-corrected-head confirmation — ATTEMPT 2

```
GOV-2 sec7 artifact. Against head: f1abe012912a6b176874faa7985cbd52fc848484
Invocation: codex exec -s read-only, captured verbatim from stdout 2026-08-28.
VERDICT: NOT CONFIRMED (F1 wording, F3 internal contradiction, F7 fixture
untracked via global *.json gitignore); F6 PASS, F8 PASS. Bounded repair
applied in the next revision; ATTEMPT 3 follows.
```

---

Confirmed head SHA: f1abe012912a6b176874faa7985cbd52fc848484

F1: FAIL — Per-symbol idempotence is now distinguished from whole-snapshot idempotence, but “at most one publish cycle” is not guaranteed: the packet only self-heals on the next successful per-symbol run, so repeated omission can persist across multiple publish cycles.

F3: FAIL — Sec3 defines the five-calendar-day `as_of` guard, but sec4 still says there is “NO separate chart-staleness threshold” and bars are at most one session behind; sec10 likewise claims staleness is bounded to “yesterday,” leaving the packet internally contradictory.

F6: PASS — Sec7 places both `tests/test_notification_ownership.py` and `tests/test_prd300_delivery_backstop.py` in the PRD-P cone and explicitly requires each harness to redirect the import-time-bound `PRICE_BARS_PATH`.

F7: FAIL — The three viewport screenshots are committed and the local ignored fixture reproduces the HTML byte-identically, but `EVIDENCE_BARS_FIXTURE_2026-08-28.json` is ignored by `*.json` and absent from HEAD, so reproduction from a fresh checkout fails.

F8: PASS

VERDICT: NOT CONFIRMED (F1, F3, F7)

Independence/read-only attestation: I independently reviewed the exact corrected head, made no repository writes or commits, generated only a temporary `/tmp` artifact for comparison, and confirmed the tracked worktree remained clean.
