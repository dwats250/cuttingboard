# GEX-1 MATERIAL Packet — Event 2 Exact-Corrected-Head Confirmation (durable record)

- **Event:** EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 §7)
- **Reviewer:** Codex, fresh-context independent reviewer
- **Confirmed corrected-head SHA:** `33f753fae0c6e3884367cc31c129eefa9cb7f4ee`
- **Verdict:** CONFIRMED
- **Date:** 2026-08-20
- **Context:** fresh-context, read-only (`codex exec -s read-only`), independent — a confirmation against the Event-1 findings list, not a fresh-scope review

This is the durable ATTEMPT-2 confirmation record. Codex Event-2 ATTEMPT 1
(against the Event-1 corrected head `4dd0a0b`) returned NOT CONFIRMED on three
non-material confirmation defects (F4, F6, R4) — recorded in
`GEX_1_EVENT_2_CONFIRMATION_ATTEMPT_1_2026-08-20.md`. Dustin/HELM authorized
one bounded confirmation repair for those three defects only; the repair
landed at `33f753f`, and this ATTEMPT-2 confirmation against that exact head
returned CONFIRMED with every check PASS. The packet is now review-clean under
GOV-2. It still carries NO implementation authority: Dustin's design-direction
ruling, then the Stage-0 PRD, fresh-context PRD review, and Gate A remain
ahead.

---

## Verbatim Codex stdout (ATTEMPT 2 — CONFIRMED)

```
CONFIRMED COMMIT: 33f753fae0c6e3884367cc31c129eefa9cb7f4ee
CONFIRMATION: CONFIRMED

F1: PASS — Packet §§0 and 5 record the consumer-enumeration leg as firing, name Dustin/manual local inspection as the human consumer, distinguish machine readers as none, and forbid `Consumers: (none)`.
F2: PASS — Packet §§1 and 3 state PR #256 is MERGED via `ed87913`; the only historical open/ready wording appears explicitly identified as the stale claim that was corrected.
F3: PASS — Packet §4 D6 freezes top-level and per-contract admissibility, bool-first and finite checks, six exclusion reason keys, deterministic counting, and fail-loud top-level behavior.
F4: PASS — Packet §4 D4a/D5/D6 and R23 use naive `YYYY-MM-DD HH:MM:SS` interpreted as UTC, normalize `feed_timestamp_utc` to tz-aware ISO-8601, fail loud on malformed input, and cross the UTC/ET date boundary; no `2026-08-18T01:00Z` form survives.
F5: PASS — Packet §4 D4a/D5 freezes always-present unavailable objects with `reason` tokens, unified `gex_1pct_usd`, and the complete `zero_dte` shape.
F6: PASS — Packet §4 D5 defines exhaustive CONFIGURED/OBSERVED/REPORTED/DERIVED/INFERRED provenance, places coverage under DERIVED, and identifies `fetched_at_utc` as locally observed.
F7: PASS — Packet §6 R7/R12/R14/R17/R19/R23 and R24–R37 contain the required discriminating fixtures, exhaustive guard, actual timestamp shape, and mutation-red rows.
R1: PASS — Event-1 charge line 40 and packet §§0/5 use `rg -ni 'gex|gamma' cuttingboard/`.
R2: PASS — Packet §4 D5 gives `roots` its own schema row.
R3: PASS — Packet §11 uses `python3 tools/validate_prd_registry.py --skip-commit-resolvability`.
R4: PASS — Packet uses `dominant_net_gamma` throughout the active design; §12 and the correction record mark historical `dominant_gamma` mentions as superseded.
ancestry: PASS — `git merge-base --is-ancestor ed87913 HEAD` exited 0, and the GEX-0 Cboe evidence packet is present in-tree at HEAD.
no-new-boundary: PASS — Packet §§2–5, §7–§9 retain `_SPX` only, one fetch, standalone stdlib-only `tools/gex_snapshot.py`, `logs/gex_snapshot.json`, and no workflow/cadence, machine consumer, payload/contract/dashboard path, second provider, or SPY; `top_strikes` removal and validation additions introduce no new consumer, seam, schema surface beyond the sidecar artifact, dependency, or authority claim.
cone/ceiling: PASS — Packet §7 retains one production file, one test file, and mandated documentation/bookkeeping rows; §8 retains a bottom-up ≈380 LOC estimate plus ≈20 margin for a ≤400 production-LOC ceiling and does not widen the file cone.

NOTES: Exact-corrected-head confirmation only; no fresh-scope findings.
```
