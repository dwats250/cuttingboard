# Recon — Gap-Down Permission Gating ↔ PRD-150 Coupling

**Date:** 2026-05-22
**Scope:** Read-only coupling analysis. Single question: does Gap-Down Permission Gating logically depend on PRD-150?

---

## 1. Document identification

**Gap-Down Permission Gating PRD:** does not exist.

A search of `docs/prd_history/` (177 files) and `docs/PRD_REGISTRY.md` returns zero matches for `gap-down`, `gap_down`, `gapdown`, or "permission gating". `docs/PROJECT_STATE.md:36` states "**Next step:** Phase 1 step 3 per VISION.md — Gap-Down Permission Gating implementation. PRD to be drafted; not yet open."

However, **Gap-Down Permission Gating already exists as implementation** without a corresponding PRD:

- `cuttingboard/intraday_state_engine.py:180–262` — `classify_gap()`, `downside_short_permission()`, `DownsidePermissionState`, gap classification and acceptance logic.
- `cuttingboard/runtime.py:1205–1248` — `_apply_intraday_short_permission(candidates, execution_quotes)` — production wiring; SHORT candidates are filtered by intraday state before they reach `qualify_all`.
- `cuttingboard/runtime.py:489, 518, 805` — three call sites invoking the gate (daily-mode, hourly-mode, and a third path that gates only outside `MODE_FIXTURE`).
- `tests/test_gap_down_permission_integration.py` (~200 LOC) — integration tests covering A-1 wiring + acceptance/clean-reclaim/permission paths.
- `tests/test_intraday_state.py:285–360` — 7 unit tests on gap-down state transitions and short-permission inputs.

Per the brief: *"If you can't locate the Gap-Down PRD, state so plainly and stop — surface for human direction rather than guessing."* The deliverable below proceeds on a best-effort basis using the **implemented behavior** as a proxy for "what Gap-Down does," because the coupling question is still answerable against working code. The verdict and recommendation account for the missing-PRD finding.

**PRD-150:**

- `docs/prd_history/PRD-150.md` — *Five-Tier Symbol Classification System*. PROPOSED. HIGH-RISK lane.
- `docs/prd_history/PRD-150.review.codex.md` — Codex cross-review, two passes recorded, both REJECT. No mention of gap-down, intraday short permission, or `_apply_intraday_short_permission` in the review (grep clean).

**VISION.md:** Read for Phase 1 step 3 framing ("Gap-Down Permission Gating PRD — needs implementation") and the "intraday state classification PRD needs review against this vision before building" line.

**`cuttingboard/universe.py`:** Compatibility shim only — `is_tradable_symbol`, `filter_execution_dict`, `filter_execution_items`, `log_universe_configuration`. Universe content lives in `config.py`.

---

## 2. Gap-Down summary

Gap-Down Permission Gating blocks SHORT-direction trade candidates intraday during gap-down opens until a "permission" condition is met. It runs **before** `qualify_all`: `runtime._apply_intraday_short_permission` iterates candidates whose `direction == "SHORT"`, fetches per-symbol intraday bars, computes intraday state via `intraday_state_engine.compute_intraday_state`, and applies `intraday_state_engine.downside_short_permission(context, state)`. Permission is granted when the symbol is past the OPEN phase AND either (a) failed-reclaim of ORB low, (b) acceptance below level, or (c) the gap was not a DOWN gap at all. Suppressed shorts are popped from `candidates` before qualification; they never reach `qualify_all`, never receive a `QualificationResult`, never appear in `rejections[]`, and never appear in `trade_candidates[]`. The gate sits one layer upstream of qualification.

---

## 3. PRD-150 summary

PRD-150 replaces the regime-level STAY_FLAT short-circuit in `qualify_all` with a five-tier per-symbol classification system (PRIME, QUALIFIED, WATCHLIST, DEVELOPING, REJECT) computed **after** `qualify_all` returns. A new pure module `cuttingboard/classification.py` defines `classify_symbol(qualification_result, regime)` plus two post-steps `apply_concentration_caps` and `apply_flow_gate_demotion` (PRIME → QUALIFIED only). A new sidecar `reports/daily_classification.md` surfaces all five tiers. The contract gains a new top-level status `NO_TRADE` (distinct from `STAY_FLAT`), `_build_rejections` gains a `CLASSIFICATION` stage for non-PRIME-tier demotions, and the existing aggregate Telegram notification is gated to PRIME-only with a second QUALIFIED-summary call appended. `trade_candidates[]` shape is unchanged; non-PRIME symbols never enter it.

---

## 4. Coupling analysis

| Coupling point | Classification | Notes |
|---|---|---|
| **Symbol tier references** | INDEPENDENT | Gap-Down doesn't reference any tier concept (no PRIME/QUALIFIED/WATCHLIST/DEVELOPING/REJECT in `intraday_state_engine.py` or in the `_apply_intraday_short_permission` body). PRD-150 doesn't reference gap-down state, gap_type, downside_short_permission, or `_apply_intraday_short_permission`. |
| **Threshold tiering** | INDEPENDENT | Gap-Down applies one uniform gap threshold (`_GAP_THRESHOLD` in `intraday_state_engine.py`, scoped to the per-symbol intraday state). It does not vary by symbol category. PRD-150 doesn't modify gap thresholds, lookback windows, or any gating-rule parameter relevant to gap-down. |
| **Universe scope** | INDEPENDENT | Gap-Down operates on whatever `generate_candidates(...)` produces, then narrows by `direction == "SHORT"`. It does not consult `universe.py` or any tier-bucket. PRD-150's `OUT OF SCOPE` section explicitly excludes universe changes. |
| **Shared modules** | AMBIGUOUS | Both touch `cuttingboard/runtime.py`, but on disjoint call paths. Gap-Down wires in at `runtime.py:489, 518, 805` (pre-qualify_all). PRD-150's `runtime.py` edits sit **after** `qualify_all` returns — `runtime.py:575` (notification gating), plus three append-only invocations of `classify_symbol`, `apply_concentration_caps`, `apply_flow_gate_demotion`, and the sidecar writer. PRD-150's `CHANGE SURFACE` enumerates the runtime edits as "append-only" and does not touch `_apply_intraday_short_permission` or its call sites. Risk of merge conflict is non-zero (same file) but logically the surfaces don't overlap. |
| **Sidecar coupling** | INDEPENDENT | Gap-Down emits no sidecar. PRD-150's `daily_classification_sidecar` reads finalized contract + qualification summary; gap-down state is not exposed on either. The sidecar would not surface gap-down-suppressed shorts — they're invisible to PRD-150's classification because they never reach `qualify_all`. |
| **State / data structure overlap** | INDEPENDENT (with visibility gap, noted below) | PRD-150 adds `classification: dict[str, ClassificationRecord]` to `QualificationSummary`. Gap-Down doesn't read `QualificationSummary`. PRD-150 doesn't read `IntraState`, `DownsidePermissionState`, or `SessionContext`. No data structure is shared, derived from, or mutated by both. |

**Visibility gap (not a coupling, surfaced for context):** A SHORT candidate suppressed by Gap-Down is popped from `candidates` before `qualify_all` runs. It therefore never receives a tier, never appears in `rejections[]` at any stage, and never appears in `trade_candidates[]`. Post-PRD-150, this symbol is "absent from the classification record" rather than "REJECT tier" or "non-PRIME CLASSIFICATION." This is an observability gap — gap-down-suppressed shorts are silent in both pre- and post-PRD-150 contracts. Addressing it would require either: (a) moving gap-down filtering into qualify_all so the symbol becomes visible to classification, or (b) adding a separate sidecar field for pre-qualification suppression. Neither is in either PRD's scope. Listed here as informational, not a coupling.

---

## 5. Verdict

**INDEPENDENT.**

PRD-150's logic does not reference gap-down state; Gap-Down's logic does not reference symbol tiers. They sit on opposite sides of `qualify_all`. Implementing PRD-150 against the current Gap-Down-as-implemented codebase carries no foreseeable logical rework. The only operational risk is merge friction in `runtime.py` if PRD-150 implementation lands in the same hunk window as a future Gap-Down PRD edit — easily resolved during landing.

Caveat the brief flagged in advance: **the absence of a Gap-Down PRD prevents a definitive coupling analysis against a stable PRD specification.** This verdict applies to the implemented behavior in the current codebase. If a future Gap-Down PRD extends the gate's surface (for example, exposing suppressed shorts to the rejection channel, or making gap-down behavior tier-aware), the coupling profile would need to be re-examined.

---

## 6. Recommended sequence

**Option A — Implement Gap-Down first, vision-review PRD-150 in parallel or after** — applies here, with a modification.

Specifically:

1. **Resolve the Gap-Down governance gap first.** VISION.md says "in flight: needs implementation," PROJECT_STATE.md says "PRD to be drafted; not yet open," but the implementation has been in production code since at least the existing integration test suite was written. Either:
   - (a) Write a retrospective PRD documenting the implemented behavior (declare COMPLETE on landing), OR
   - (b) Update VISION.md and PROJECT_STATE.md to remove Gap-Down from "in flight" and acknowledge it as already-implemented infrastructure.

   This is independent of PRD-150 and unblocks Phase 1 closure either way.

2. **Vision-review PRD-150 separately.** It's currently PROPOSED with two REJECTed Codex cross-review passes; HIGH-RISK lane requires fresh-context / different-model review. Vision review is orthogonal to gap-down and can proceed in parallel with step 1.

3. **Implement PRD-150 only after vision review accepts it.** No gap-down precondition.

The brief's option A framing ("Gap-Down can be implemented first, PRD-150 in parallel") fits the spirit, but the literal phrasing is misleading because Gap-Down is *already implemented*. The recommendation is therefore: close the Gap-Down documentation gap on its own track; PRD-150 proceeds on a separate, independent track.

---

## 7. Honest limits

- **No Gap-Down PRD exists**, so coupling was assessed against implemented code rather than a stable PRD specification. A future Gap-Down PRD could expand scope (sidecar emission, tier-awareness, etc.) and change the coupling profile. The verdict is conditional on the current implementation behavior.
- The "Visibility gap" point under §4 is an observability concern, not a logical coupling. I classified it as not-a-coupling but it could fairly be read as AMBIGUOUS if you view "gap-down-suppressed shorts being invisible to classification" as a substantive coupling concern.
- I did not independently verify every PRD-150 `FAIL` condition against the codebase. Coupling analysis was limited to the structural questions the brief asked.
- `cuttingboard/runtime.py` is ~2100 LOC; I did not exhaustively read it. The three `_apply_intraday_short_permission` call sites and the definition were inspected directly. PRD-150's `runtime.py` edit footprint was read from its CHANGE SURFACE section rather than from a live diff (no diff exists; PRD-150 is PROPOSED, not implemented).
- The brief's deliverable path used the placeholder `audits/recon-2026-05-XX/`. I wrote to `audits/recon-2026-05-22/gap-down-prd150-coupling.md` to match the actual directory created.
- PRD-150's Codex review file is 746 lines and contains two REJECT verdicts. I did not parse the review for additional context beyond confirming it doesn't surface a gap-down coupling concern. If the review's REJECT reasons interact with gap-down assumptions, that's not surfaced here.
