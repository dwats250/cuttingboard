# NS-4B — GOV-2 Event-1 INITIAL PACKET REVIEW (12/12 boundary, v0.4) — durable record

**Event type:** `INITIAL PACKET REVIEW` (fresh, on the owner-expanded 12/12
boundary; owner-commissioned 2026-08-22).
**Reviewer:** independent Codex (`codex-cli 0.147.0`, `gpt-5.6-sol`), fresh
context, read-only (`codex exec -s read-only`, high effort).
**Reviewed SHA / packet revision:** `5d51f94414515139ad2ae110f6d60d49490d97b1`
— packet v0.4. Code baseline `main` @ `80ac6eb`.
**Review date:** 2026-08-22.
**Run-isolation:** separate Codex session; sandbox read-only; no repo write;
transcribed by Claude Code from captured stdout.

## Verdict: FINDINGS — 3 BOUNDARY (F1,F2,F4), 2 P1 (F3,F6), 2 P2 (F5,F7). E7 (G1 fix) CONFIRMED.

The two central claims of the 12/12 boundary reset are REFUTED (F1, F2). The
safe design requires a runtime observe-only admission cut, which re-expands the
MATERIAL boundary — this returns to Dustin (GOV-2 §1) rather than a mechanical
consolidated correction.

### Findings

- **[F1] BOUNDARY — no-decision-authority proof refuted.** `NON_TRADABLE_SYMBOLS`
  fences breadth and FINAL actionability, but NOT the
  derived->structure->candidate->qualification pipeline. Fetched UCO/GOOG enter
  every stage and can change hourly action/reason via unfiltered qualification
  counts. Evidence: `runtime/__init__.py:588-641`; `derived.py:47-59`;
  `structure.py:59-75`; `qualification.py:191-232`;
  `notifications/__init__.py:135-151,246-261,565-574`. **Author-confirmed:**
  `qualification.py:191` iterates `structure_results.items()` with NO is_tradable
  filter; `symbols_qualified` drives the qualified/outcome decision
  (`notifications:143-150`); and `docs/universe_taxonomy.md` states `ALL_SYMBOLS`
  consumers include "derived metrics, regime inputs, qualification fan-out." So
  the config-membership seam does NOT isolate observe-only symbols. Falsifies
  E2/E9, §4.2 R8.
- **[F2] BOUNDARY — "validation failure -> n/a" is false.** Validation-invalid
  quotes are removed from `valid_quotes` but REMAIN in `normalized_quotes`, which
  the sidecar receives; the builder treats them as present and renders their
  movement, not `n/a`. Only a fetch/normalization failure (absent from
  `normalized_quotes`) yields `n/a`. Evidence: `validation.py:93-102`;
  `runtime/__init__.py:549-552,778-786`; `watchlist_sidecar.py:61-76`. Falsifies
  E3/E6, R1', carried F3, M15.
- **[F3] P1 — cited standing guard is not killable.** If UCO/GOOG go into
  `ALL_SYMBOLS` but NOT `NON_TRADABLE_SYMBOLS`, denominator becomes 18, yet
  `test_expansion_regime.py:200-230` stays green (11/18 still blocks, 14/18 still
  passes); the tests comment about 16 but never assert the cardinality. Need an
  explicit `len(ALL_SYMBOLS \ NON_TRADABLE_SYMBOLS) == 16` mutation guard.
  Falsifies E1/E6, §4.2 standing-guard claim, §10 M17.
- **[F4] BOUNDARY — PRICE_BOUNDS/source-priority omission violates the canonical
  universe taxonomy.** `docs/universe_taxonomy.md` (a governance doc, previously
  unconsulted) requires that adding an `ALL_SYMBOLS` symbol update source
  priority and validation bounds; the "macro-driver precedent" for omission is
  wrong (every macro driver has an explicit source-priority entry). Evidence:
  `config.py:258-265,275-284,290-313`; `validation.py:203-217`;
  `docs/universe_taxonomy.md:3-25`. (Note: the taxonomy doc is itself stale — 4
  macro drivers vs 7 in code — a pre-existing drift.) Falsifies E4/E8, §4.3, §8.
- **[F5] P2 — PRD-158 inventory incomplete.** Six more files assert the changed
  universe constants and are neither scoped nor named verified-unaffected:
  `test_contract_macro_drivers.py:94-96`, `test_prd161_sizing_gate_fixture.py:244-248`,
  `test_prd162_reconciliation.py:124-141`, `test_runtime_decision.py:246-252`,
  `test_trade_decision.py:242-259`, `test_trend_structure.py:429-438`. Falsifies
  E5/E6, §8.
- **[F6] P1 — v2 acceptance lacks full-12 identity/completeness.** Validates
  source/version/per-row types but not the exact symbol set/count, key-to-row
  identity, or unique `registry_index`; an empty/partial well-typed v2 artifact
  could pass and silently omit UCO/GOOG (violates R1'). Need exact full-12
  acceptance + missing/extra/mismatched/duplicate-index mutations. Falsifies E6,
  carried F2/F4/F5.
- **[F7] P2 — "never tradable" unreconciled with the owner-ratified registry.**
  `universe_registry.py` has UCO/GOOG `trade_eligible=True` and
  `test_universe_registry.py:80-83` requires all twelve flags true; neither
  surface is in FILES. Needs an explicit ruling distinguishing inert registry
  eligibility from runtime tradability, or a registry/test update. Falsifies E8.

### Per-target
E1=[F3] (seam yields is_tradable/is_actionable False + denom 16, but the guard
does not hold) · E2=[F1] · E3=[F2] (yfinance/default-source/non-HALT confirmed;
validation-failure != n/a) · E4=[F4] · E5=[F5] · E6=[F2,F3,F5,F6] ·
**E7=CONFIRMED (G1 fix good — future case removed, no clock)** · E8=[F1,F4,F5,F7]
· E9=[F1] (MATERIAL/HIGH-RISK ok; R8 proof refuted).

### Recommended (non-blocking)
M11 cross-reference `§12 #6` should be `§12 #7`.

## Governance consequence

F1 refutes the no-decision-authority proof and F2 refutes the transient-failure
contract. Achieving true observe-only 12/12 (fetched + rendered, but excluded
from qualification/regime, with a truthful n/a) requires a RUNTIME observe-only
admission cut / dedicated fetch path — a materially larger boundary than v0.4's
config-membership seam. Under GOV-2 §1 (boundary expansion) and the owner's own
direction ("choose a narrower fetch-only seam"; "return that expanded runtime
boundary for owner review"), this returns to Dustin for a design-direction
ruling BEFORE the single consolidated correction is spent. Packet status:
DESIGN INCOMPLETE — held for Dustin.
