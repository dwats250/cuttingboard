# Codex Event-2 exact-corrected-head confirmation — ATTEMPT 1

```
GOV-2 sec7 artifact. Confirmed head: 64676f5acc37d7570ad9f727292b452d62a21326
Invocation: codex exec -s read-only, captured verbatim from stdout 2026-08-28.
VERDICT: NOT CONFIRMED (residuals F1, F3, F6, F7; F8 new-material-class PASS).
A bounded confirmation repair is applied in the next revision; ATTEMPT 2 follows,
per the GEX-2 packet-cycle precedent (audits/gex-2-free-board-card-2026-08/).
```

---

- Confirmed head SHA: `64676f5acc37d7570ad9f727292b452d62a21326`
- F1: FAIL — restore lists correctly omit `trend_structure_snapshot.json` and sec5 now covers `.github/` and `tests/`, but the overwrite rule is not generation-monotonic: legal partial snapshots directly contradict the claim that same-session runs are identical, so an older run can overwrite a newer complete snapshot with omitted symbols.
- F2: PASS — sec3 now filters against `most_recent_completed_session_date(generated_at)`; the authority exists at `cuttingboard/time_utils.py:37` and governs cache freshness through `cuttingboard/ingestion.py:147-167`.
- F3: FAIL — provenance, columns, and partial-snapshot policy are specified, but the claimed one-session freshness bound is false: a caught writer failure leaves the tracked fallback available indefinitely, and the reader has no age rejection, so a freshly rendered page can chart arbitrarily stale bars.
- F4: PASS — sec3 requires one bound `history_by_symbol` collection per seam, and sec2 correctly qualifies hourly fib availability as path/state dependent.
- F5: PASS — sec4 preserves PRD-226 suppression when `current_price` is invalid, matching the caller gate at `dashboard_renderer.py:2141-2164`; it does not claim the internal sentinel is reachable.
- F6: FAIL — `tests/test_ci_artifact_hygiene.py` is now in the PRD-P cone, but a module-level `PRICE_BARS_PATH = LOGS_DIR / ...` is fixed at import time and will not follow later `LOGS_DIR` monkeypatches; the two full-live harnesses must explicitly redirect `PRICE_BARS_PATH`, as they already do for `TREND_STRUCTURE_PATH`.
- F7: FAIL — the committed generator reads gitignored local parquet files through a hard-coded repository path; recorded hashes without committed input fixtures or committed viewport screenshots/measurements do not make the evidence independently reproducible from a fresh checkout.
- F8 new-material-class check: PASS — the correction introduces no new material carrier, consumer, workflow, or production-layer class beyond those already present in Event-1’s reviewed design.
- VERDICT: NOT CONFIRMED (F1, F3, F6, F7)
- Independence/read-only attestation: I independently reviewed the pinned corrected head, did not author or modify any repository content, performed no commits, and confirmed the worktree was clean before and after review.
