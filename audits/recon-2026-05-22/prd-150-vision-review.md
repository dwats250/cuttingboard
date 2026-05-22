# PRD-150 Vision Review — Five-Tier Symbol Classification System

**Date:** 2026-05-22
**Reviewer:** Claude Code (this session). Holding the review; not delegating to Codex.
**Standard:** `VISION.md` only. Not prior PRDs. Not general "good architecture."

---

## 1. Summary

**Verdict: REVISE — and the revision honestly collapses toward KILL.**

The PRD survived four Codex passes (REJECT → REJECT → REJECT → ACCEPT WITH CHANGES) and landed on a coherent design. But over the course of those four passes, the realizable output set of its main visibility channel shrank from "five tiers, every evaluated symbol" to **one tier in practice** — PRIME-eligible candidates demoted to QUALIFIED by concentration cap or flow-gate. Under current `qualify_all`, DEVELOPING / WATCHLIST / REJECT tiers all route through the pre-existing `qual.excluded` and `qual.watchlist` channels and are dedupe-guarded out of the new CLASSIFICATION emission. The PRD is now mostly infrastructure (2 new modules, contract value-space expansion, new sidecar artifact, notification path split, postmarket counter rewrite) in service of surfacing one previously-untracked emission case. Against `VISION.md`'s "cuts before additions" and the behavioral-test rubric ("does this change what Dustin actually does?"), the cost is hard to justify. Recommend rewriting it as a 30-LOC patch on the existing rejection or watchlist channels — or dropping it.

---

## 2. What PRD-150 proposes

Mechanically:

- **Deletes the regime-level STAY_FLAT short-circuit** in [qualification.py:151–166](../../cuttingboard/qualification.py#L151), so `qualify_all` runs the per-symbol loop on every posture. After R1, `regime_short_circuited` is always False and `regime_failure_reason` is always None. Five existing reader branches (contract.py:212, contract.py:352, output.py:290, audit.py:218, qualification.py:580/602) become permanently dead by design — kept in place for shape stability.
- **Adds two new modules**: `cuttingboard/classification.py` (~110 LOC; `ClassificationTier` StrEnum with PRIME/QUALIFIED/WATCHLIST/DEVELOPING/REJECT, `classify_symbol`, `apply_concentration_caps`, `apply_flow_gate_demotion`) and `cuttingboard/daily_classification_sidecar.py` (~60 LOC; writes `reports/daily_classification.md`).
- **Expands the contract value-space**: `_VALID_STATUSES` grows from 3 to 4 by adding `STATUS_NO_TRADE = "NO_TRADE"`. `derive_run_status` gets a new return path for zero-PRIME-after-gating, non-CHAOTIC, no-error.
- **Extends `_build_rejections`** with a new `stage = "CLASSIFICATION"` plus tier-specific `reason` literals (`NON_PRIME_QUALIFIED` / `NON_PRIME_WATCHLIST` / `NON_PRIME_DEVELOPING` / `NON_PRIME_REJECT`), guarded by a dedupe rule: emit only if the symbol is NOT already in `qual.excluded` or `qual.watchlist`.
- **Splits the notification path**: the existing aggregate Telegram call at [runtime.py:575](../../cuttingboard/runtime.py#L575) becomes PRIME-content-gated and is suppressed when zero PRIME; a second `send_notification` call is appended for the QUALIFIED-tier summary, suppressed when zero QUALIFIED.
- **Updates `reports/postmarket.py`** with a fourth counter (`classification_count`) and changes `trade_summary.rejected_count` semantics from "qualification-only" to "total non-PRIME across all stages."
- **Stated problem**: "the binary STAY_FLAT short-circuit collapses every symbol's evaluation into a single posture-level decision, destroying per-symbol visibility on days when the regime is mildly defensive." Five-tier classification restores graduated visibility through a sidecar and rejection-channel audit trail.

Budget: 250 production LOC / 400 test LOC. LANE: HIGH-RISK.

---

## 3. What already exists

The user's prompt referenced `CORE/CONDITIONAL/SIGNAL/MACRO/EXCLUDED tiers already in universe.py`. **Those literal tier names do not exist anywhere in the codebase.** Grep across `cuttingboard/` returns zero matches for `CORE_TIER`, `CONDITIONAL_TIER`, `SIGNAL_TIER`, `CORE_SYMBOLS`, `CONDITIONAL_SYMBOLS`, etc. [universe.py](../../cuttingboard/universe.py) is 33 lines — a compatibility shim around `is_tradable_symbol` and `filter_execution_*` stubs.

What does exist:

**Symbol-universe *categories*** in [config.py:147–156](../../cuttingboard/config.py#L147):

```
MACRO_DRIVERS = ["^VIX", "DX-Y.NYB", "^TNX", "BTC-USD", "CL=F", "GC=F", "SI=F"]
NON_TRADABLE_SYMBOLS = frozenset(MACRO_DRIVERS)
INDICES       = ["SPY", "QQQ", "IWM"]
COMMODITIES   = ["GLD", "SLV", "GDX", "PAAS", "USO", "XLE"]
HIGH_BETA     = ["NVDA", "TSLA", "AAPL", "META", "AMZN", "COIN", "MSTR"]
ALL_SYMBOLS   = MACRO_DRIVERS + INDICES + COMMODITIES + HIGH_BETA
REQUIRED_SYMBOLS = ["^VIX", "DX-Y.NYB", "^TNX", "BTC-USD", "SPY", "QQQ"]
TREND_STRUCTURE_SYMBOLS = ("SPY", "QQQ", "GDX", "GLD", "SLV", "XLE")
HALT_SYMBOLS = ["^VIX", "DX-Y.NYB", "^TNX", "SPY", "QQQ"]
EXPANSION_LEADERSHIP_SYMBOLS = ["NVDA", "COIN", "MSTR", "SMCI", "TSLA"]
```

Categories are **inputs to behavior** (which symbols to fetch, which to halt on, which to trend-track) — not classification *outcomes*.

**Evaluation-outcome tiers** that DO exist today, in [qualification.py:170–214](../../cuttingboard/qualification.py#L170):

- `qualified` — passes all hard gates, passes all soft gates (becomes `qualified_trades` on the summary)
- `watchlist_trades` — passes all hard gates, exactly one soft-miss (becomes `qual.watchlist`)
- `excluded` — CHOP, direction mismatch, hard-fail, OR ≥2 soft misses (becomes `qual.excluded`)

These three outcome buckets are already surfaced in `_build_rejections` at [contract.py:346–376](../../cuttingboard/contract.py#L346) under three stages: `REGIME` (when short-circuit fires), `QUALIFICATION` (everything in `qual.excluded`), `WATCHLIST` (everything in `qual.watchlist`). PRD-150 adds a 4th stage `CLASSIFICATION`.

**Is PRD-150 building something that already exists in a different form?** Partially yes. The system already has three outcome buckets; PRD-150 formalizes them into a five-member enum, adds a "DEVELOPING" tier conceptually, and adds a "QUALIFIED-via-demotion" tier (PRIME-eligible candidates demoted by post-R5 caps or flow-gate). The five-tier enum is a refinement, not a green-field abstraction. Critically (and per Codex Pass 4 RE4-1), the new CLASSIFICATION emission channel only realistically catches the "QUALIFIED-via-demotion" case. DEVELOPING is unreachable under current `qualify_all` because anything with a hard-gate failure is already in `excluded` and gets dedupe-guarded out of CLASSIFICATION.

---

## 4. VISION.md alignment check

For each `VISION.md` principle (lines 50–57):

| Principle | Classification | Notes |
|---|---|---|
| **PRD before build for anything non-trivial** | ALIGNED | PRD-150 exists; HIGH-RISK lane declared; four-pass cross-review. Process discipline is solid. |
| **Read-only sidecars by default** | ALIGNED | The new sidecar (`daily_classification_sidecar.py`) is explicitly forbidden from importing pipeline-decision modules; writes only under `reports/`. Codex Pass 1 confirmed sidecar doctrine compliance. |
| **Description, not prediction** | ALIGNED | No forecasting. Tier assignment is deterministic from gate-pass arithmetic + posture. Classification *describes* what happened to each candidate in qualification; it does not predict future behavior. |
| **Cuts before additions** | **VIOLATION** | This is the central tension. PRD-150 adds 2 new modules (~170 LOC), expands the contract value-space, adds a new sidecar artifact, splits the notification path into two calls, and modifies postmarket counters. The justifying value (per Codex Pass 4 RE4-1) is *one* new emission case: PRIME→QUALIFIED demotions via concentration cap or flow-gate. Five-of-five tier members exist in the enum but only one tier is realizably reachable through the new CLASSIFICATION channel under current `qualify_all`. The other four are tracked by existing channels and dedupe-suppressed from CLASSIFICATION. PRD-150 is mostly scaffolding for a narrow new emission. See `VISION.md:53` — "before adding a feature, the system should justify the features it already has." |
| **System serves the trader, not the other way around** | TENSION | If Dustin uses the sidecar to make decisions, ALIGNED. If the sidecar exists but isn't consulted, the principle is violated — the system is producing a feature Dustin doesn't act on. Not assessable without observing usage. Discussed further in §7. |
| **System must match its documentation** | NEUTRAL | The PRD updates relevant docs (`docs/artifact_flow_map.md` row required by R4). No documentation drift introduced; existing docs are unchanged or augmented. |

Against `VISION.md` non-goals (lines 11–18):

- Not an automated execution engine — ALIGNED (no execution surface change).
- Not a backtesting framework — ALIGNED.
- Not a machine learning system — ALIGNED.
- Not a multi-agent orchestration platform — ALIGNED.
- Not a generalized financial operating system — TENSION-leaning-NEUTRAL. Adding a five-tier taxonomy for symbols is the kind of "generalized framework" abstraction that risks expanding scope. Currently bounded — but the enum is shaped for extension.
- Not a high-frequency signal factory — ALIGNED.
- Not a regulated infrastructure project requiring aircraft-grade process — TENSION. Four review passes, dead-branch enumeration of five reader sites, HIGH-RISK lane process, 400-LOC test ceiling at the limit — for a change whose actual user-facing delta is a new markdown sidecar and a split notification. The process weight is plausibly out of proportion to the value being delivered. `VISION.md:19` — "The system is built by one person, for one person's trading, on a part-time schedule. Scope decisions reflect that reality."

---

## 5. Engagement with prior REJECTions

Two-of-four REJECTions is a stronger signal than the final ACCEPT WITH CHANGES suggests. Each pass surfaced a *fresh* blocking issue the author didn't anticipate:

| Pass | Headline blocker | Resolution | VISION.md weight |
|---|---|---|---|
| 1 | R6 vocabulary drift ("TRADES list" not in contract surface) | Author picked Option (b): keep all symbols in `trade_candidates[]`, force non-PRIME to BLOCK_TRADE with new `block_reason`. **Resolved in pass 2 — but Option (b) was itself unviable (see pass 2)**. The author was working from a mental model of the contract that didn't match the code. | Aligned with `VISION.md:57`: "When code and documented intent diverge, one of them is wrong." The PRD's intent didn't match the code; the PRD got corrected. Good. |
| 2 | `derive_run_status` return alphabet was wrong; `block_reason == decision_trace["reason"]` invariant violated; runtime cite at 828–850 wrong (no per-PRIME loop there) | Author switched strategies entirely: non-PRIME goes to `rejections[]` not `trade_candidates[]`; `STATUS_NO_TRADE` is added explicitly to the value space; notification is content-gated at the existing aggregate call. **Resolved in pass 3**. | Three repo-anchored facts the PRD asserted without verifying. This pattern — claiming things about the code that aren't true — is exactly the "silent drift" failure mode VISION.md:69–71 warns about, in the small. |
| 3 | Postmarket consumer not updated; rejection duplication across stages unaddressed | Author added `cuttingboard/reports/postmarket.py` to FILES, added classification_count counter, chose Option (a) dedupe via existing-rejection guard. **Resolved in pass 4**. | Each consumer audit miss reveals "hidden coupling" — the governance principle `VISION.md:50` is built on the inverse. |
| 4 | DEVELOPING-tier CLASSIFICATION emission is unrealizable; CHANGE SURFACE narrative inverted from realizable set | **Pass 4's "ACCEPT WITH CHANGES" required only text-and-fixture revision, not architectural change.** Author was directed to rewrite the dedupe fixture and tighten the CHANGE SURFACE language. This is the smallest of the four passes' blockers — but its substance is large: the PRD's main visibility delivery turns out to be one tier wide. | This is the key insight for the vision review. The PRD's stated value ("five-tier classification restores graduated visibility") is much smaller in practice than the writeup implies. |

**Does VISION.md share the objections?** Codex's objections were all repo-anchored (factual claims vs. actual code). VISION.md is principle-anchored. They don't conflict — VISION.md tightens the standard further by asking whether the resulting design is justified by the four questions and by behavioral change. Codex didn't ask that; that's this review's job.

**The four-pass arc itself is a signal.** Cumulatively: vocabulary drift, three unverified repo claims, two unaudited downstream consumers, and a narrative-vs-realizable-set mismatch. The author of the PRD has been working from a model that's adjacent to the code but not the code. That's exactly the drift VISION.md was written to prevent.

---

## 6. The four-questions test

`VISION.md:5` — Cuttingboard answers: *what environment, what matters today, is it tradable, what invalidates*.

Does PRD-150 make the system better at any of these?

- **What environment?** No. Regime computation is OUT OF SCOPE; STAY_FLAT short-circuit removal doesn't change regime determination, only what happens after. Same answer pre- and post-PRD-150.
- **What matters today?** Marginally. The new sidecar lists per-symbol tiers — a viewer of the sidecar can see "these 3 symbols had clean hard gates but were demoted by flow opposition" in one place rather than reconstructing it from `rejections` + `qual.watchlist`. But the underlying facts are already accessible via existing artifacts. The sidecar is a reorganization, not new information.
- **Is it tradable?** No. The PRIME path remains the sole gateway to actual trade emission ([PRD-150 lines 19–20](../../docs/prd_history/PRD-150.md#L19)). Tradability decisions are unchanged; only their visibility is reorganized.
- **What invalidates?** No. Invalidation logic (PRD-068, `cuttingboard/invalidation.py`) is untouched.

PRD-150 adds infrastructure that *organizes* answers to "what matters today" but doesn't *improve* any of the four answers. That's a thin justification under `VISION.md:5`.

---

## 7. The behavioral test (VISION.md's trap warning)

`VISION.md:69–71` is explicit: *"Every proposed feature should be evaluated against: does this change what I'll actually do, or does it just help me feel more informed about what I might do? The latter is intellectual comfort dressed as progress."*

PRD-150 outputs:

1. **A new sidecar artifact** `reports/daily_classification.md` — markdown for human reading. Has no consumer in the pipeline.
2. **New `CLASSIFICATION`-stage rows in `rejections[]`** — visible in the contract artifact for audit / dashboard / report consumers.
3. **A split notification** — same recipients, same Telegram channel, body now lists PRIME-only + a QUALIFIED summary tail.
4. **A new `STATUS_NO_TRADE`** distinct from `STATUS_STAY_FLAT` — distinguishes "posture allowed trading but zero PRIME after gating" from "posture forbade trading."

For each output, ask: does this change what Dustin does?

- Output 1: Sidecar is observational. Only useful if Dustin reads it and acts on the reading. Currently no observed evidence Dustin is reading the existing equivalent surfaces (`qual.watchlist` etc.) and acting differently.
- Output 2: `rejections[]` consumers are postmarket reports and (potentially) future dashboards. Same observational concern.
- Output 3: Telegram body change. If the previous aggregate body listed all-three-buckets and Dustin acted on some non-PRIME entries, PRIME-only gating now hides them — that's a behavioral change (toward narrower action). If Dustin only ever acted on the PRIME entries anyway, it's cosmetic.
- Output 4: `STATUS_NO_TRADE` vs `STATUS_STAY_FLAT` — semantic precision in the contract. Useful to a reader of the artifact; behaviorally inert to Dustin unless he reads contract artifacts directly.

**On balance: PRD-150 is mostly "help him feel more informed."** The PRIME notification gating is the one substantive behavior nudge — and it could be implemented as a ~10-line change to the existing notification call without any of the surrounding infrastructure.

This is the strongest single VISION.md signal in this review. `VISION.md:71` calls out "intellectual comfort dressed as progress" by name.

---

## 8. Cost analysis

**Production surface:**

- New module `cuttingboard/classification.py` (~110 LOC)
- New module `cuttingboard/daily_classification_sidecar.py` (~60 LOC)
- Modified `cuttingboard/qualification.py` (~30 LOC: delete short-circuit, add `classification` field)
- Modified `cuttingboard/runtime.py` (~20 LOC: classify/cap/demote/sidecar wiring + notification gate)
- Modified `cuttingboard/notifications/__init__.py` (~20 LOC: QUALIFIED summary formatter)
- Modified `cuttingboard/contract.py` (~10 LOC: STATUS_NO_TRADE, derive_run_status path, _build_rejections extension)
- Modified `cuttingboard/reports/postmarket.py` (~5–10 LOC: classification_count + rejected_count rollup)
- Total: ~255–265 LOC (claimed budget 250 — already over before LOC discipline).

**Test surface:** 400 LOC ceiling exactly hit (Codex Pass 4 confirmed). No buffer.

**Conceptual surface:**

- One new public enum (`ClassificationTier`) with 5 members
- One new dataclass (`ClassificationRecord`)
- One new status literal (`STATUS_NO_TRADE`) in contract value-space
- One new `rejections[]` stage (`CLASSIFICATION`)
- Four new `reason` literals (`NON_PRIME_*` family) — three of which are unrealizable under current routing
- One new `demotion_reason` value space (4 values)
- New semantic for `trade_summary.rejected_count` (qualification-only → all-stages-non-PRIME)
- One new sidecar artifact path (`reports/daily_classification.md`)
- Five existing reader branches go permanently dead by design (with the PRD enforcing they stay in place for shape stability — an explicit zombie-code tradeoff)

**Maintenance burden:**

- Every future `qualify_all` change must consider whether it affects tier assignment realizability (the DEVELOPING-tier-is-unreachable issue is a maintenance signal — future contributors must keep the realizable set in mind to avoid the same kind of fixture-vs-code drift the PRD itself had).
- Every future `rejections[]` consumer must handle the four-stage shape (or get dedupe-guarded out and miss the new emission).
- Every future contract status enum reader must handle the four-value space.
- The semantic shift in `rejected_count` will surprise any consumer (downstream dashboards, reports) inheriting the field across the PRD-150 boundary.

**Versus the delivered value:** One new emission case (post-R5 PRIME→QUALIFIED demotion via cap or flow-gate) becomes auditable through a structured channel rather than being silent. That's the entire user-facing delta of PRD-150's CLASSIFICATION channel under current routing.

Cost-benefit per `VISION.md:53`: the ratio is unfavorable.

---

## 9. Verdict and recommendation

**REVISE — and the honest revision collapses toward KILL.**

The full-scope PRD-150 fails the "cuts before additions" test and the behavioral test. Four pages of infrastructure to make one new emission case observable does not match `VISION.md:53`'s standard.

### If REVISE: what survives

The narrowest defensible version of PRD-150's intent is:

- Keep the post-R5 demotion semantics (concentration cap + flow-gate-opposed) — these are real decision-affecting events worth surfacing.
- Add ONE new rejection row per demotion to the existing `rejections[]` channel with `stage = "DEMOTION"` (or fold into existing QUALIFICATION stage with a richer `reason` string).
- Skip: the `ClassificationTier` enum (the system doesn't need five tier names; the three existing buckets plus "demoted" are enough), `classify_symbol` (not adding tier-classification logic the system doesn't act on), `apply_concentration_caps` and `apply_flow_gate_demotion` as pure-functional post-steps (these can be inline at the demotion site), the new `STATUS_NO_TRADE` (zero PRIME with posture allowing is rare enough that `STATUS_OK` plus an empty `trade_candidates` already conveys it), the daily classification sidecar (the markdown sidecar has no consumer; it's the "help him feel more informed" trap directly), the notification path split (or keep this one piece — PRIME-only gating is the one substantive behavior change).

Scope of the surviving PRD: ~30 production LOC, ~50 test LOC, no new modules, no contract value-space change, no new sidecar, no postmarket counter refactor, no dead-branch retirements, STANDARD lane.

### If KILL: what's salvageable

Some elements of PRD-150 deserve to be captured as governance artifacts even if the PRD itself is dropped:

- **The dead-branch enumeration discipline.** PRD-150's CHANGE SURFACE listing of five reader sites that go permanently dead by design (with explicit "retained in place for shape stability" framing) is a good template for future R1-style retirements. Capture as a section in `docs/PRD_PROCESS.md` or a note in `docs/DECISIONS.md`.
- **The `block_reason == decision_trace["reason"]` invariant.** Surfaced in Codex Pass 2 RE2-2; this is a contract-validator landmine future PRDs must respect. Worth one line in `docs/architecture.md`.
- **The downstream-consumer audit pattern.** Codex's pass-3 catch of the postmarket counter drift is a generalizable habit (any new rejection stage must audit `reports/postmarket.py`). Capture as a PRD-author checklist.
- **The realizability check (Pass 4 RE4-1).** A PRD that claims to emit on N tiers must verify each tier is reachable under current routing. Capture as a `prd-authoring-verified` skill addition or a PRD template checklist item.

None of these need PRD-150 to land to be useful. They can be captured in DECISIONS.md or as small PR(D)s of their own.

### If KEEP: required edits before implementation

I don't recommend KEEP, but if Dustin overrides:

- Address Codex Pass 4 RE4-1 (rewrite the dedupe validation fixture, tighten the CHANGE SURFACE narrative to the realizable set).
- Acknowledge in the PRD itself (not just in the review) that DEVELOPING / WATCHLIST / REJECT tier emissions are forward-compatibility defenses, not currently-active code paths. The PRD reads as though five tiers are real; only one is.
- Tighten the LOC budgets: 250 production is already tight per Codex Pass 4's tally; raise to 280 with a written justification, or carve out the postmarket update into a follow-up.

---

## 10. Honest limits

- **I could not observe whether Dustin uses the existing observability surfaces** (`qual.watchlist`, `rejections[]`, the postmarket report). The behavioral test in §7 leans on the assumption that existing surfaces are under-used; if Dustin actively reads `rejections[]` daily and would read `reports/daily_classification.md` the same way, the behavioral case for the sidecar strengthens. This is a usage-pattern question only Dustin can answer.
- **A reviewer with deeper familiarity with the post-R5 demotion semantics** might argue that PRIME→QUALIFIED demotions are decision-affecting enough to warrant the dedicated infrastructure. I judged it as one tier of observable delta against five tiers of declared scope — but the value of *that* one tier could be higher than my §6/§7 analysis weights it.
- **The "feel more informed vs. change what you do" test is intrinsically subjective.** I made the call based on the artifact shapes (markdown sidecar, structured rejection rows) producing observational outputs — but observational data can change behavior if a trader is disciplined about consulting it. I'm trusting `VISION.md:69–71`'s own framing that this is a real concern Dustin shares.
- **I did not run a determinism audit of `classify_symbol`'s decision tree against the actual gate counts.** Codex Pass 4 verified the tree against the gate routing and found DEVELOPING unreachable; I trusted that finding without independently re-deriving it from `qualification.py` line by line.
- **The user's prompt mentioned `CORE/CONDITIONAL/SIGNAL/MACRO/EXCLUDED` tiers in universe.py.** Those literal tier names do not exist in the codebase. I assumed the user was loosely referring to the symbol-category structure (`MACRO_DRIVERS`, `INDICES`, `COMMODITIES`, `HIGH_BETA`) that does exist. If the user meant a different tier system that I missed, my §3 finding is incomplete.
- **I am not the project lead in the sense `VISION.md:62` describes** (Claude in chat). I'm Claude Code, the implementation agent. VISION.md positions architectural review with Dustin and the chat-Claude. This review is one input among several Dustin can weigh; the decision is his.
- **The recommendation "REVISE collapsing toward KILL" is intentionally weighted.** Two prior REJECTions plus a final ACCEPT-with-narrative-defect is a real signal, but it would be intellectually dishonest to dismiss the considerable work the PRD has already absorbed. If Dustin sees value I'm missing — particularly behavioral value from the PRIME notification gating piece — the right move may be to extract that piece and ship it, even if everything else gets dropped.
