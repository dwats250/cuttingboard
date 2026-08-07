# NS-2E — Market Control Card — MATERIAL PACKET (v0.2, REDESIGN RESET)

STATUS: PROVISIONAL — REDESIGN RESET — NOT REVIEW-CLEAN — NO IMPLEMENTATION
AUTHORITY. This packet carries no implementation authority; Gate A is neither
requested nor granted by it. Owner decisions D-1..D-5 (§10) remain UNRESOLVED.

SUPERSESSION / RESET: This v0.2 packet SUPERSEDES the v0.1 packet in full. v0.1,
its three corrections, and its terminal exact-head review are preserved unmodified
on PR #222 as the superseded forensic/review trail; that trail is not edited,
restated, or re-adjudicated here, and nothing NS-2E exists on `main` at derivation
(verified: no NS-2E artifact under `audits/` at `main` HEAD). This is a **redesign
reset, NOT correction #4** — one coherent specification that incorporates the
validated v0.1 design decisions AND all five review findings (F1–F5) from
inception. There is no amendment chain to read; the document is complete as
written. The single fresh independent review of THIS packet is commissioned only
after Dustin authorizes its push/PR (§17); until that review completes, this packet
is PROVISIONAL — NOT REVIEW-CLEAN, and no downstream Stage-0 PRD may be opened.

CHRONOLOGY / AUTHORITY (binding):
- v0.1 (PR #222) accumulated three corrections and a terminal exact-head Codex
  confirmation whose final finding — F5, a missing regression proof of the F4
  freshness gate — plus the accumulated amendment weight led Dustin to order a
  redesign reset rather than a fourth correction on that trail.
- The validated design decisions carried forward (daily-only; transient
  non-persisted `MarketControlCard`; read-only presentation surface; no
  decision-contract key; seven fields each value-or-explicit-UNAVAILABLE;
  renderer invents nothing; LOCATION/PERMISSION reuse existing producers;
  EVENT/TRANSITION explicit UNAVAILABLE; INVALIDATION bounded composition;
  CANDIDATE-IMPLICATION bounded/minimal from real candidate inputs; Market Map
  retirement split to a separate later slice; hourly out of scope) were confirmed
  by the v0.1 fresh-context review cycle and are restated here as first-class
  design, not inherited corrections.
- Gate A: not requested, not granted. The v0.1 review events on PR #222 satisfy no
  gate for v0.2.

DERIVED AT: `main` @ `daa7065d4fb5ee5a4a051de05bd1d18cae375afc` (post-PR #221
merge; == origin/main at derivation). Working tree clean at derivation. Every
`file:line` anchor below was re-verified against this SHA.

GOVERNING RULING: Dustin's redesign-reset direction (2026-08-07) — "do not make
correction #4 on PR #222; author a clean v0.2 that consolidates the validated
design plus F1–F5 from inception." This is an authoring instruction, NOT a
design-direction acceptance ruling — no such ruling exists for v0.2 yet; it comes
only after the §17 review. Where the direction is silent, VISION's
read-only-sidecars-by-default and cuts-before-additions principles govern.

CI CLAIM BOUNDARY (GOV-2 §8): This is a documentation-only packet. If CI runs
against the branch carrying it, green CI confirms only that this documentation
branch preserves the current green baseline. It does not execute or validate the
proposed runtime design, the always-on state acquisition, the isolation guard, the
freshness gate, the consumer inventory, or the regression plan.

PROVISIONAL-CEILING LABELS (GOV-2 §5): every FILES and LOC figure below is
`ESTIMATED SURFACE — NOT YET APPROVED`. The first binding ceiling is Gate A on the
reviewed PRD.

F1–F5 INCORPORATION MAP: the five findings below are not corrections applied to
this document; they are constraints the design was rebuilt around. Each is bound in
a normative design section (or, for F5, the test plan) and proven by named tests in
§13.

| Finding | Incorporated as designed-from-inception in | Proven by (§13) |
|---|---|---|
| F1 — STATE computation isolation      | §5 (normative), §3, §4.1 | T2, T3 |
| F2 — candidate inputs to the builder  | §8 (normative), §4.1, §2.2 | T4 |
| F3 — typed `StateOutcome`             | §7 (normative), §4.1 | T1, T2 |
| F4 — freshness / session gate         | §6 (normative), §3 | T6–T8 |
| F5 — regression proof of F4           | §13 (binding paragraph) | T6–T9 |

---

## 0. Where this packet sits in the GOV-2 order

```
materiality check at intake ............................. DONE (MATERIAL; §15)
provisional material packet authored .................... DONE (this v0.2 doc)
independent packet review (GOV-2 §2 step 3) ............. PENDING (§17; single
                                                          review, commissioned only
                                                          after Dustin authorizes
                                                          push/PR)
one consolidated correction (step 4) ................... PENDING (GOV-1: at most one)
exact-corrected-head confirmation (step 5) ............. PENDING
Dustin design-direction ruling (step 6) ................ PENDING
Stage-0 PRD drafting (step 7) .......................... PENDING (no PRD allocated)
independent PRD review (step 7) ........................ PENDING
Dustin Gate A (step 8) ................................. PENDING (not requested)
```

Relationship to v0.1 / PR #222 (stated once): v0.2 supersedes v0.1; the v0.1 trail
on PR #222 is untouched; the v0.1 review events do NOT satisfy any v0.2 gate. This
packet re-enters the GOV-2 order at step 2 (a freshly authored provisional packet)
and must clear its own step-3 review before any downstream authority exists.

MICRO ineligibility: this is MATERIAL work (§15); GOV-2 §1 makes a MATERIAL slice
ineligible for `LANE: MICRO` — the required order includes a PRD, its independent
review, and an explicit Gate A, none of which MICRO contains. It rides STANDARD at
minimum.

---

## 1. Product question and user-visible outcome

The Market Control Card is a compact, read-only orientation surface on the **daily**
dashboard answering, at a glance, the trader-facing questions VISION frames:
*where are we, what is the market's state, what am I permitted to do, and what does
that imply for today's candidates* — without prediction and without inventing any
value.

- **Scope: the daily `_run_pipeline` only.** The hourly publish path is OUT OF
  SCOPE from inception (not a scope-out correction): the card is built once on the
  daily path, and the hourly path adds no card section (the renderer omits the card
  when the section is absent, §2.2).
- **Seven fields, each value-or-explicit-UNAVAILABLE.** The card never shows a
  blank and never invents: every field is either a truthful value from an existing
  producer / bounded composition, or a typed `UNAVAILABLE` carrying a reason token.
  This value-or-explicit-UNAVAILABLE discipline is the card's identity and the
  binding constraint the renderer and builder are held to (§2.3, §7).

The seven fields: **LOCATION**, **STATE**, **EVENT**, **TRANSITION**,
**PERMISSION**, **INVALIDATION**, **CANDIDATE-IMPLICATION** (semantics in §7).

---

## 2. Exact producer → carrier → consumer seam

### 2.1 Current state (verified at `main` @ `daa7065`)

- **`SpyObservation`** — frozen dataclass, `cuttingboard/spy_observation.py:48-61`.
  Its `state` field is `state: str` (`:56`), populated from four MODULE-LEVEL
  STRING CONSTANTS (`spy_observation.py:24-28`): `PRE_OPEN`, `OBSERVED`, `STALE`,
  `UNAVAILABLE`. **It is a `str` fed by these constants, NOT an `Enum`/`Literal`
  type** — comparisons are against the imported constants. Built once on the daily
  path at `runtime/__init__.py:1288` via `build_spy_observation(...)` (pure,
  side-effect-free); carried transiently on `PipelineResult.spy_observation`
  (`runtime/_types.py:92`, the PRD-288 additive carrier that defaults to `None` and
  is never serialized to a durable/decision contract).
- **`compute_intraday_state(symbol, bars, *, previous_close=None) -> Optional[IntraState]`**
  — `cuttingboard/intraday_state_engine.py:400-405`. Returns `None` when the last
  bar's ET wall-clock time is before 09:45 (`_NOISE_END`, `:435-436`). RAISES
  `InsufficientDataError` (defined `intraday_state_engine.py:91-92`; raised in
  `_compute_orb` at `:136` when fewer than 5 ORB-window bars exist) and `ValueError`
  on empty / non-chronological bars.
- **Freshness gap (the exact gap F4 closes).** `compute_intraday_state` reads only
  the last bar's wall-clock ET *time-of-day* (`current_bar = bars[-1]`;
  `current_et_time = _et_time(current_bar.timestamp)`; `intraday_state_engine.py:431-436`)
  and never compares the bar's *date* or session against the intended run session.
  A prior-session post-09:45 frame therefore computes a confident, stale
  `IntraState`.
- **Sole existing `compute_intraday_state` call site:** `runtime/__init__.py:1466`,
  inside the short-permission gate loop, wrapped in a **generic `except Exception`
  that logs-and-skips** (`:1465-1471`) for that gate's own purpose. There is **no
  production site that catches `InsufficientDataError` by name** (grep-verified).
- **Candidate inputs.** `_run_decision_gates(...)` (called `runtime/__init__.py:1112`,
  unpacked `:1105-1123`) returns the run-level `outcome` and the
  `invalidation_guidance_map`; `visibility_map = build_visibility_map(trade_decisions,
  market_map)` at `runtime/__init__.py:1140` classifies each decision. Neither the
  `visibility_map`, the run `outcome`, nor the `invalidation_guidance_map`
  currently reaches any card builder.
- **Payload / renderer precedent.** `build_report_payload(contract,
  fixture_mode=False, *, spy_observation=None)` (`delivery/payload.py:24-29`)
  projects `sections["spy_observation"] = _project_spy_observation(spy_observation)`
  (`:141`, helper at `:160`) only when the observation is provided (daily path);
  the SPY session card is rendered defensively at
  `dashboard_renderer.py:2538-2557` (reads `payload["sections"]["spy_observation"]`,
  guards on truthiness, emits a `<div class="block">` with `<h2>` + kv-grid rows;
  omitted when absent).
- **Confirmed:** no `MarketControlCard` type, builder, payload section, or renderer
  exists in production today (grep-verified across `.py`).

### 2.2 Proposed seam (additive; nothing above is modified)

One path, mirroring the `SpyObservation` carrier precedent exactly:

1. On the **daily** `_run_pipeline`, after the decision gates (`:1112`) and the
   existing `build_spy_observation` (`:1288`), perform the new **always-on** SPY
   state acquisition (§5) and build the card **once** via
   `build_market_control_card(...)`, passing: (a) the already-built
   `SpyObservation`; (b) the typed `StateOutcome` from the guarded always-on call
   (F1/F3); (c) the candidate inputs — `visibility_map`, run `outcome`, and (for
   INVALIDATION) `invalidation_guidance_map` (F2).
2. Carry the card transiently on a NEW optional field
   `PipelineResult.market_control_card` (`runtime/_types.py`), mirroring
   `spy_observation` at `_types.py:92` — additive, defaults to `None`, never
   serialized to a durable/decision contract.
3. Forward it to the **daily** `build_report_payload` call as a NEW keyword-only
   parameter placed AFTER the existing ones — i.e.
   `build_report_payload(contract, fixture_mode=False, *, spy_observation=None,
   market_control_card=None)` — retaining `fixture_mode` and `spy_observation`
   verbatim (breaks no existing caller).
4. Project to `sections["market_control_card"]` (a JSON-safe plain-dict mirror,
   like `_project_spy_observation`) only when provided.
5. Render one `<div class="block">` card iff `sections["market_control_card"]` is
   present (precedent `:2538-2557`); the hourly path passes nothing and the card is
   omitted — the hourly path is otherwise unmodified.

### 2.3 Binding rule (read-only, builder-is-sole-producer)

- The card is a **read-only presentation surface**. The **builder is the SOLE
  producer** of every final card value.
- The **renderer projects and never derives, defaults, or invents** a value: a
  field absent from `sections["market_control_card"]` never appears in the HTML.
- **No decision-contract key**, no `market_map.json` change, no audit/report/payload
  schema change, no persistence. The card rides the transient carrier only.

---

## 3. Recommended implementation design (single design, not alternatives)

One build, executed once on the daily path, with F1/F3/F4/F2 as load-bearing
structure in order:

1. **Always-on state acquisition + isolation guard (F1).** A new daily call to
   `compute_intraday_state` for SPY, wrapped in a typed guard (§5) that catches
   `InsufficientDataError` and bounded computation/data failures and NEVER
   propagates — a provider gap or engine error yields a typed unavailable outcome,
   not a failed daily pipeline.
2. **Typed `StateOutcome` (F3).** The guarded acquisition produces a
   `StateOutcome` carrying EITHER the available `IntraState` value OR an explicit
   unavailable reason token — never both, never neither. `Optional[IntraState]`
   alone is insufficient because it cannot distinguish "insufficient bars" from a
   normal pre-computation `None` (§7).
3. **Freshness / session gate (F4).** A computed `IntraState` may surface as the
   card's STATE ONLY when `spy_observation.state == OBSERVED`. `PRE_OPEN` / `STALE`
   / `UNAVAILABLE` map to `STATE = UNAVAILABLE(reason="non_current_observation")`
   even when the engine returned a value (§6). The gate reuses the existing
   `SpyObservation` freshness authority; no second freshness system is introduced.
4. **Seven-field composition.** LOCATION and PERMISSION from existing producers;
   EVENT and TRANSITION explicit `UNAVAILABLE(reason="no_truthful_producer")`
   (declared defensive — no truthful producer exists today); INVALIDATION bounded
   composition over existing guidance (D-2); CANDIDATE-IMPLICATION bounded/minimal
   from the passed-in candidate inputs (F2; D-3).

**D-1 dependency, stated plainly.** The always-on SPY state call is genuinely NEW —
the only existing `compute_intraday_state` call sits inside the short-permission
gate (`:1466`). Whether to add it always-on is an UNRESOLVED owner decision (§10,
D-1); this design recommends it but does not assume ratification. If D-1 is
declined, STATE joins EVENT/TRANSITION as explicit UNAVAILABLE and §5's guard is
moot.

---

## 4. Sidecar contract

### 4.1 New dataclasses (transient, non-persisted)

- **`MarketControlCard`** — a new frozen dataclass, transient, non-persisted, built
  once on the daily path. Seven fields, each a value-or-explicit-UNAVAILABLE cell
  (a small structured value carrying either a truthful value or a reason token).
- **`StateOutcome`** — a new frozen dataclass expressing exactly one of: an
  available `IntraState` value, OR an explicit unavailable reason token. Invariant:
  exactly one populated — never both, never neither (F3).
- **Builder signature (illustrative, to be pinned by the PRD against the then-current
  SHA):**
  `build_market_control_card(*, spy_observation, state_outcome, visibility_map,
  run_outcome, invalidation_guidance_map, ...) -> MarketControlCard`. Passing the
  candidate inputs into the signature is F2 made structural — the builder, not the
  renderer, is the sole producer of CANDIDATE-IMPLICATION and INVALIDATION.
- **Closed reason-token set** (the only UNAVAILABLE reasons the card may emit):
  - `insufficient_bars` — the always-on engine call raised `InsufficientDataError`
    (F1).
  - `state_computation_error` — a bounded computation/data failure at the state
    seam (F1).
  - `non_current_observation` — the `SpyObservation` is non-current
    (`PRE_OPEN`/`STALE`/`UNAVAILABLE`) so a computed state is suppressed (F4).
  - `pre_computation_window` — the engine returned `None` because the last bar is
    before 09:45 ET (a normal not-yet-computable window; distinct from an error and
    from `non_current_observation`).
  - `no_truthful_producer` — EVENT / TRANSITION have no truthful producer today
    (declared defensive).

### 4.2 Payload projection

- A NEW keyword-only parameter on `build_report_payload`, placed AFTER the existing
  parameters: `build_report_payload(contract, fixture_mode=False, *,
  spy_observation=None, market_control_card=None)`. `fixture_mode` and
  `spy_observation` are retained verbatim; no existing caller breaks (the illustrative
  signature is pinned exactly against `payload.py:24-29` — an inaccurate illustrative
  signature is exactly the class of local finding to avoid).
- `sections["market_control_card"]` is a JSON-safe plain-dict mirror, present iff the
  card is provided (daily path); absent otherwise (hourly and every pre-existing
  path).

### 4.3 Schema / persistence classification

Transient and non-persisted. NO decision-contract key, NO schema migration, NO
`market_map.json` change, NO durable artifact change. The payload validator
tolerates extra sections, so no schema bump is required. Negative proof: §13 T10.

---

## 5. Always-on STATE acquisition and failure isolation (F1 — normative home)

- **The new call.** A new always-on daily call to `compute_intraday_state` for SPY.
  Its outcomes are exhaustively: (a) a real `IntraState`; (b) `None` (last bar
  before 09:45 ET, `_NOISE_END`, `:435-436`); (c) a raise — `InsufficientDataError`
  (`:91-92`, `:136`) or a bounded data/computation failure.
- **The typed guard (F1).** The acquisition is wrapped in a typed guard that
  catches `InsufficientDataError` and bounded computation/data failures at the new
  call seam and maps them to `StateOutcome.unavailable(reason="insufficient_bars")`
  or `reason="state_computation_error"` — NEVER propagating, so a missing provider
  bar or engine error cannot fail the daily pipeline. `None` maps to
  `reason="pre_computation_window"`. This is PRD-198 #1 (fail-loud) realized *on the
  card* while the pipeline is *isolated* from the failure.
- **Truthful novelty framing (do not misstate).** No production site catches
  `InsufficientDataError` by name today; F1's typed guard on the new always-on call
  is therefore genuinely new, and no existing catch path is reused. The sole
  existing `compute_intraday_state` call site (`runtime/__init__.py:1465-1471`,
  short-permission gate) handles failures with a generic `except Exception`
  log-and-skip for its own gating purpose and is NOT modified by this design.
- **Non-effect.** The new call must not perturb the existing short-gate call, its
  context dict, or any execution decision (proven §13 T3/T10; §9).

Recommended placement of the guard: in the builder (or a thin runtime bridge
immediately feeding it), so the builder remains the sole producer of the final
STATE cell. The packet recommends the builder.

---

## 6. Current-observation freshness / session gate (F4 — normative home)

- **The gap, cited exactly.** `compute_intraday_state` validates only the last
  bar's wall-clock ET time-of-day (`intraday_state_engine.py:431-436`), never its
  date or session — a prior-session frame at a valid time of day yields a confident,
  stale `IntraState`.
- **The gate.** A computed `IntraState` may surface as the card's STATE ONLY when
  `spy_observation.state == OBSERVED` (string comparison against the imported
  `OBSERVED` constant, `spy_observation.py:26`). Mapping:

  | `SpyObservation.state` | card STATE |
  |---|---|
  | `OBSERVED` + computed `IntraState` | the computed state value |
  | `OBSERVED` + engine `None` (pre-09:45) | `UNAVAILABLE(reason="pre_computation_window")` |
  | `PRE_OPEN` | `UNAVAILABLE(reason="non_current_observation")` — even if a value was computed |
  | `STALE` | `UNAVAILABLE(reason="non_current_observation")` — even if a value was computed |
  | `UNAVAILABLE` | `UNAVAILABLE(reason="non_current_observation")` — even if a value was computed |

- **Authority reuse (binding).** The gate reuses the already-built `SpyObservation`
  freshness authority; the design FORBIDS a second freshness computation (PRD-198
  #3: authoritative source, not proxy). Introducing any second freshness mechanism
  is a §14 stop-and-amend event.
- **The 09:35–09:45 boundary case, named honestly.** `SpyObservation` can be
  `OBSERVED` from 09:35 (`_PRE_OPEN_CUTOFF_ET`) while the engine returns `None`
  until 09:45. That outcome is `UNAVAILABLE(reason="pre_computation_window")` — a
  distinct reason token, NOT `non_current_observation` and NOT an error. Conflating
  it with `non_current_observation` would corrupt the meaning of the F5 matrix
  (§13).

---

## 7. Typed StateOutcome and the seven-field semantics (F3 — normative home)

**Why `Optional[IntraState]` is insufficient.** A bare `Optional[IntraState]`
conflates "no state" with "why there is no state": the builder cannot distinguish
an `InsufficientDataError` from a normal pre-09:45 `None`, and so cannot emit the
correct reason token. The `StateOutcome` type carries the reason explicitly; the
builder remains the sole producer of the final card values (F3).

**Seven-field table:**

| Field | Source | Rule |
|---|---|---|
| **LOCATION** | existing producer (`SpyObservation`) | reuse; value-or-UNAVAILABLE |
| **STATE** | new always-on engine call → `StateOutcome` (§5) → freshness gate (§6) | value only when `OBSERVED`; else typed UNAVAILABLE |
| **EVENT** | none | `UNAVAILABLE(reason="no_truthful_producer")` — declared defensive |
| **TRANSITION** | none | `UNAVAILABLE(reason="no_truthful_producer")` — declared defensive |
| **PERMISSION** | existing producer (`system_state.permission`) | reuse; value-or-UNAVAILABLE |
| **INVALIDATION** | bounded composition over `invalidation_guidance_map` | composes existing guidance only; computes nothing new (D-2) |
| **CANDIDATE-IMPLICATION** | bounded/minimal from `visibility_map` + run `outcome` (F2) | builder-produced; renderer never derives (D-3) |

**EVENT / TRANSITION are declared defensive** (Author discipline #3, realizability):
they have no truthful producer under current routing and emit
`UNAVAILABLE(reason="no_truthful_producer")` by design. The packet does not claim
an active channel and does not promise a future producer beyond declaring these
fields defensive-against-future-routing. Relabeling the presentation lifecycle as
market state is explicitly forbidden.

---

## 8. Candidate inputs and CANDIDATE-IMPLICATION / INVALIDATION composition (F2 — normative home)

- **The builder receives the candidate inputs as parameters** — `visibility_map`
  (`runtime/__init__.py:1140`), the run `outcome`, and `invalidation_guidance_map`
  (both from `_run_decision_gates`, `:1105-1123`). Verified: today none of these
  reach any card builder; F2 threads them at build time.
- **The renderer NEVER derives** CANDIDATE-IMPLICATION or INVALIDATION from other
  payload sections; the builder produces both.
- **CANDIDATE-IMPLICATION — bounded/minimal.** A minimal rollup over the actual
  candidate visibility/outcome inputs (e.g. whether any candidate is ACTIVE /
  NEAR_MISS / BLOCKED and the run-level outcome). Absence of candidates yields a
  truthful minimal value (e.g. "no actionable candidates"), NOT an invented one.
- **INVALIDATION — bounded composition only.** Composes the existing
  `invalidation_guidance_map` into a compact statement; it computes no new
  invalidation logic and makes no predictive judgment. Anything requiring a new
  source or a predictive judgment is a §14 stop-and-amend event.

---

## 9. Explicit non-effects on execution and halt behavior

The card build is pure and side-effect-free. Unchanged by this design: the run
`outcome`, halt semantics, the short-permission gate and its context dict, the
hourly path, the decision contract, `market_map.json`, all durable artifacts, and
persistence. On a halted run the card renders with truthful UNAVAILABLE cells (it
fabricates no value), consistent with the existing `SpyObservation` halt behavior.
Each non-effect maps to a §13 test (T10) or the must-stay-green set (§11).

---

## 10. Open owner decisions (D-1..D-5 — UNRESOLVED, held for Dustin)

These recommendations are the author's, presented for the design-direction ruling
that follows the §17 review. **Nothing in this packet treats any of D-1..D-5 as
decided.** The §11/§12 FILES/LOC estimate assumes the recommended shape and says so.

- **D-1 — always-on SPY STATE computation on the daily path.**
  Recommendation: **YES.** Rationale: the card's STATE field is empty without it;
  the isolation guard (§5) caps the blast radius; the freshness gate (§6) keeps it
  truthful. If declined: STATE joins EVENT/TRANSITION as explicit UNAVAILABLE and
  §5's guard is moot. **Status: UNRESOLVED — held for Dustin.**
- **D-2 — bounded INVALIDATION in v1.**
  Recommendation: **INCLUDE.** Rationale: composition-only over existing
  `invalidation_guidance_map`; no new computation. If declined: the field ships
  explicit UNAVAILABLE. **Status: UNRESOLVED — held for Dustin.**
- **D-3 — minimal CANDIDATE-IMPLICATION rollup.**
  Recommendation: **INCLUDE.** Rationale: F2 makes it truthful by construction from
  real candidate inputs. If declined: the field ships explicit UNAVAILABLE and the
  F2 parameters drop from the builder signature. **Status: UNRESOLVED — held for
  Dustin.**
- **D-4 — Market Map retirement.**
  Recommendation: **SPLIT** into a separate later subtractive slice. Rationale: the
  generic per-symbol Market Map board has live consumers (`trade_visibility`,
  `overnight_policy`, `macro_pressure`), so retiring it is a dead-branch-enumeration
  exercise of its own; building the additive card in v1 and retiring the board later
  honors cuts-before-additions by sequencing, not by coupling. This packet builds
  the card additively and changes nothing about the Market Map. **Status:
  UNRESOLVED — held for Dustin.**
- **D-5 — proceed on committed in-tree authority.**
  Recommendation: **PROCEED.** Rationale: the load-bearing rulings are durable in
  `docs/DECISIONS.md`; no off-tree plan is required to author or review this packet.
  **Status: UNRESOLVED — held for Dustin.**

---

## 11. Exact likely files (ESTIMATED SURFACE — NOT YET APPROVED)

**9 files (5 production + 4 test).** F1–F5 add LOC and test surface, not files.

**Production:**

| Op | File | Purpose |
|---|---|---|
| A | `cuttingboard/market_control_card.py` (new) | `MarketControlCard` + `StateOutcome` frozen dataclasses; `build_market_control_card(...)` — F1 typed guard, F3 typed outcome, F4 freshness gate, F2 candidate composition, seven-field derivation |
| M | `cuttingboard/runtime/__init__.py` | always-on daily SPY state acquisition; build the card after the decision gates and the existing `build_spy_observation` (`:1288`); set it on `PipelineResult`; forward to the daily `build_report_payload` call; hourly path untouched |
| M | `cuttingboard/runtime/_types.py` | one optional `market_control_card` field on `PipelineResult` (mirrors `spy_observation`, `:92`) |
| M | `cuttingboard/delivery/payload.py` | keyword-only `market_control_card` parameter + `sections["market_control_card"]` projection |
| M | `cuttingboard/delivery/dashboard_renderer.py` | one card block, present iff section present (precedent `:2538-2557`) |

**Deliberately NOT in FILES (a design claim the reviewer should attack):**
`cuttingboard/intraday_state_engine.py` and `cuttingboard/spy_observation.py`. The
design catches at the NEW call seam and reuses the existing freshness authority
UNMODIFIED; touching either is a §14 stop-and-amend event.

**Test:**

| Op | File | Purpose |
|---|---|---|
| A | `tests/test_market_control_card.py` (new) | builder unit tests T1–T9, including the F5 freshness matrix (T6–T8) and the F5 mutation obligation (T9) |
| M | `tests/test_runtime_decision.py` | daily-path end-to-end wiring + non-effects (T3 isolation, T10 no-contract-change) |
| M | `tests/test_payload.py` | `sections["market_control_card"]` projection; hourly-absent |
| M | `tests/test_dashboard_renderer.py` | card block render + omission + renderer-invents-nothing (T5) |

**PRD-158 grep sweep note.** This change deletes, renames, or translates no
rendered field / contract key / enum value; the sweep over the affected tokens
(`market_control_card`, `MarketControlCard`, the reason tokens) returns no existing
asserting tests, so the sweep adds no further test files. The sweep was run over
those tokens at derivation.

**Must-stay-green (unchanged) set:** the decision contract and its tests, the
short-permission gate, `market_map.json` and its tests, the hourly path, all
persistence/audit/report schema tests.

---

## 12. Estimated production LOC ceiling (ESTIMATED SURFACE — NOT YET APPROVED)

Governing metric: net production LOC via `git diff --numstat` across the authorized
production files; test LOC is not counted against this ceiling.

- **Revised estimate: ~+230–320 net production LOC; provisional ceiling ≤340.**
  Revised UP from v0.1's ~+180–250 because F1–F5 add real production surface:
  - F3 `StateOutcome` type + threading: ~+20–30
  - F1 typed guard + reason-token mapping: ~+10–15
  - F4 freshness gate + mapping: ~+10–15
  - F2 candidate-input threading through builder/runtime/signatures: ~+10–15
  - F5 adds only test LOC (uncounted under the governing metric).
- **Indicative split:** `market_control_card.py` ~130–170; `runtime/__init__.py`
  ~40–55; `_types.py` ~3; `payload.py` ~15–20; `dashboard_renderer.py` ~30–40.
- **Precedent, cited honestly:** the sibling NS-2A/NS-2C packet's ≤195 estimate
  proved insufficient and was amended to ≤325 mid-flight; v0.2 prices the known
  surface up front rather than underbidding.

Non-binding. The first binding ceiling is Gate A on the reviewed PRD.
**Stop-and-amend tripwire:** a sixth production file, any persistence, or any
decision-contract key returns the packet to §14 (stop, amend, re-review).

---

## 13. Discriminating test plan (F5 bound HERE)

Tests T1–T10 map 1:1 to the required inventory (smallest set that proves the
properties; not inflated):

- **T1 — normal.** `OBSERVED` + a computable `IntraState` → the card's STATE cell
  carries the value (proves the F3 value side).
- **T2 — insufficient bars.** Engine raises `InsufficientDataError` →
  `UNAVAILABLE(reason="insufficient_bars")` (F1 + F3 reason side).
- **T3 — computation/data error isolation.** A bounded failure at the state seam →
  typed `UNAVAILABLE(reason="state_computation_error")` AND the daily pipeline
  completes (does not raise) (F1 isolation).
- **T4 — candidate implication from real inputs.** CANDIDATE-IMPLICATION is built
  from the actually-passed `visibility_map` / run `outcome`; changing those inputs
  changes the field (F2).
- **T5 — renderer invents nothing.** A card value absent from
  `sections["market_control_card"]` never appears in the rendered HTML; the card
  block is omitted entirely when the section is absent.
- **F5 freshness matrix (T6–T8), one parameterized case per non-current state — a
  computable `IntraState` exists in every case:**
  - **T6 — `STALE` + computable `IntraState`** → STATE = `UNAVAILABLE(reason="non_current_observation")`.
  - **T7 — `PRE_OPEN` + computable `IntraState`** → STATE = `UNAVAILABLE(reason="non_current_observation")`.
  - **T8 — `UNAVAILABLE` observation + computable `IntraState`** → STATE = `UNAVAILABLE(reason="non_current_observation")`.
- **T9 — mutation obligation for the F4 gate.** Removing or bypassing the §6 gate —
  forwarding the computed `IntraState` regardless of `SpyObservation.state`, or
  widening the accepted set beyond `OBSERVED` — MUST turn at least one of T6–T8 RED.
- **T10 — no persistence/schema/decision-contract output changes.** The decision
  contract, `market_map.json`, and durable artifacts are byte-for-byte unchanged by
  the presence of the card (non-effect proof).

**F5 — Regression proof of the freshness gate (binding on the implementing PRD's
test plan).** The §6 freshness gate must be *proven*, not merely exercised. The test
plan MUST include at least one test in which (a) the intraday inputs are sufficient
for `compute_intraday_state` to return a real `IntraState` — a computable STATE
genuinely exists; AND (b) the already-built `SpyObservation.state` is non-current
(`STALE`, `PRE_OPEN`, or `UNAVAILABLE`); AND (c) the final card's STATE field is
asserted to be `UNAVAILABLE` with reason `non_current_observation` — never the
computed value. A parameterized matrix covering all three non-current states is the
required form (T6–T8). A case in which the `IntraState` is itself unavailable —
insufficient bars, an engine `None`, or a raised error — does NOT satisfy this
requirement, because it cannot distinguish the freshness gate from the availability
path. Mutation obligation (PRD-198 #4): removing or bypassing the §6 gate —
forwarding the computed `IntraState` regardless of `SpyObservation.state`, or
widening the accepted set beyond `OBSERVED` — MUST turn at least one of T6–T8 RED
(T9). An implementation in which the gate can be deleted while the suite stays green
does not satisfy this packet and does not merge.

**Mutation plan (each guard → which test reddens):**

| Guard mutated | Test that reddens |
|---|---|
| Drop the F1 catch (let the engine raise propagate) | T2, T3 |
| Return bare `Optional[IntraState]` (drop the reason) | T2 |
| Remove/bypass the F4 freshness gate (or widen beyond `OBSERVED`) | T6, T7, or T8 (T9) |
| Let the renderer derive CANDIDATE-IMPLICATION | T4, T5 |
| Serialize the card into a durable/contract surface | T10 |

A guard whose mutation leaves all tests green is not a guard and does not merge.

---

## 14. Stop-and-amend conditions

Stop, re-run GOV-2 §1 classification, and amend the packet/PRD (with fresh review
of the amended revision per GOV-2 §5/§6) if implementation needs ANY of:

- a decision-contract key or any persisted/schema surface;
- to rename or remove an existing rendered token;
- to touch the hourly path;
- a second freshness mechanism (beyond reusing `SpyObservation` authority);
- EVENT or TRANSITION to gain a "producer" without a truthful source;
- a sixth production file beyond the §11 set, or exceeding the §12 ceiling;
- renderer-side derivation of any card value;
- a new source or predictive judgment for INVALIDATION / CANDIDATE-IMPLICATION.

---

## 15. Materiality / lane classification

**MATERIAL** under GOV-2 §1: this selects an implementation seam / carrier shared
across pipeline layers (runtime → transient carrier → payload → renderer), adds a
new dataclass/presentation surface with more than one path, and crosses runtime,
delivery, and dashboard. Therefore it clears an upstream packet before any
downstream PRD.

Lane: **STANDARD at minimum** (MICRO-ineligible, §0). HIGH-RISK only if R11's own
triggers fire; this additive, transient, read-only sidecar does not, on its face,
meet those triggers — the design touches no persistence, no decision contract, and
no execution path — so STANDARD is the expected lane. Dustin may classify
otherwise.

---

## 16. Document-drift correction (if any)

None required at derivation. The `docs/SCHEMA_MAP.md` / `docs/CALL_SITE_MAP.md`
entries for the new `MarketControlCard` / `StateOutcome` types and the new call
sites are created by the implementing PRD (not by this read-only packet). Any
update to the NS-2E status line in `docs/PROJECT_STATE.md` (from `NEXT` toward
"packet authored — awaiting review") rides that later governed closeout, not this
packet.

---

## 17. Packet review records (GOV-2 §2, §7 — PENDING)

NO REVIEW OF THIS v0.2 PACKET HAS OCCURRED. Per the terminal rule closing the v0.1
cycle, the single fresh independent Codex packet review of this packet is
commissioned ONLY AFTER Dustin authorizes the push/PR carrying it — it is not
requested, scheduled, or implied by this document's existence. The v0.1 review
records remain on the superseded PR #222 trail and do NOT satisfy any gate for
v0.2. Until the record below is populated, this packet is PROVISIONAL — NOT
REVIEW-CLEAN, and no downstream PRD may be opened on it.

### INITIAL PACKET REVIEW — PENDING

| Field | Value |
|---|---|
| Event type | `INITIAL PACKET REVIEW` (v0.2, GOV-2 §2 auto-commissioned) |
| Reviewer identity / capability role | PENDING — independent Codex packet review, fresh context, read-only |
| Reviewed commit SHA / packet revision | PENDING — pinned to the exact reviewed commit at review time |
| Review date | PENDING |
| Verdict | PENDING |
| Findings and dispositions | PENDING — at most one consolidated correction cycle (GOV-1) |
| Fresh-context / independence / run-isolation evidence | PENDING — recorded at review time |

A corrected head without independent SHA-pinned confirmation is not review-clean
(GOV-2 §2). When populated, this §17 block becomes the durable, packet-local,
SHA-pinned GOV-2 §2/§7 record; advisory connector threads do not by themselves
satisfy the gate.

**Terminal rule (binding on this redesign).** This redesign gets ONE fresh
independent review after Dustin authorizes the push/PR. If that review finds another
structural or boundary omission, work STOPS and returns to Dustin for a more
fundamental owner redesign — it does NOT begin another iterative correction chain.

---

END OF PACKET v0.2 — PROVISIONAL — REDESIGN RESET — NOT REVIEW-CLEAN — NO
IMPLEMENTATION AUTHORITY. v0.2 supersedes v0.1 (preserved untouched on PR #222) and
incorporates F1–F5 from inception. Gate A is neither requested nor granted. Owner
decisions D-1..D-5 remain UNRESOLVED, held for Dustin.
