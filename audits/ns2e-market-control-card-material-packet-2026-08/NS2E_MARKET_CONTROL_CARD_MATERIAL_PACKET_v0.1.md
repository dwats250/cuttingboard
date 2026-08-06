# NS-2E — Market Control Card — MATERIAL PACKET (v0.1)

STATUS: **PROVISIONAL — NOT REVIEW-CLEAN (owner-authorized exceptional correction 2
applied; final exact-head confirmation pending).** This is the upstream GOV-2
MATERIAL packet for NS-2E (Market Control Card). It carries **no implementation
authority**. The GOV-2 §2 step-5 exact-corrected-head confirmation of `f0a55a3`
surfaced a new valid P2 (the STATE unavailable-reason did not reach the builder),
tied to the STATE input-carrier consolidated correction 1 introduced — which
reopened the packet as DESIGN INCOMPLETE (GOV-2 §6/§7). **Dustin then authorized
one exceptional, narrowly bounded correction beyond the single GOV-1 cycle**,
scoped exactly to that defect. **Consolidated correction 2** (below) applies it:
a typed `StateOutcome` now carries the guarded computation's state-or-reason into
`build_market_control_card`, so the builder still produces every final card value
(§2.3) and the exception→reason mapping stays in the guard, never the renderer.
No contract, FILES estimate, product scope, or D-1…D-5 changed. The corrected head
now requires **one final independent Codex exact-head confirmation**; if that
review finds any additional boundary omission, the packet stops and returns to
Dustin — no further correction loop without his ruling. Downstream authority (PRD,
Gate A) remains prohibited until the packet is review-clean.

GOV-2 §2 order: independent Codex packet review (step 3, DONE), consolidated
correction (step 4, DONE), independent exact-corrected-head confirmation (step 5,
DONE — found one P2), **owner-authorized exceptional correction 2 (applied)**,
final exact-head confirmation (**pending**), Dustin's design-direction ruling
(step 6), a drafted+independently-reviewed PRD (step 7), and Dustin's Gate A
(step 8).

CORRECTION LOG — Consolidated correction 1 (GOV-2 §2 step 4). The independent
Codex packet review of `0a8f57ebf2` (GOV-2 §2 step 3) returned two P2 findings,
both confirmed valid against current `main`; this single consolidated correction
ACTIONS both (GOV-1's one correction cycle):
- **F1 (Codex, packet L226) — guard the always-on STATE computation.**
  `compute_intraday_state` can *raise* `InsufficientDataError`
  (`intraday_state_engine.py:130-138`), not only return `None`; a bare always-on
  call could fail the daily pipeline. §3 now makes the `try/except` isolation
  (mirroring the existing `runtime/__init__.py:1465-1471` guard) a binding part of
  the D-1 design, mapping a raise to `STATE = UNAVAILABLE(insufficient_bars)`; §4
  field 1 updated to match.
- **F2 (Codex, packet L180) — pass candidate outcomes to the builder.** The base
  `build_market_control_card` inputs omitted a candidate source, so D-3's rollup
  would have been un-derivable without the renderer inventing it (forbidden §2.3).
  §4 field 7 and §5 now make the candidate data (`visibility_map`
  `runtime/__init__.py:1140` and/or `trade_decisions`) an explicit conditional
  builder input riding the same transient carrier, adopted only if D-3 includes
  the rollup.
This consumed the single GOV-1 correction cycle.

**F2 durable disposition: ACTIONED and CONFIRMED RESOLVED.** The candidate-input
finding was actioned in correction 1 (§4 field 7, §5) and the GOV-2 step-5
exact-corrected-head confirmation of `f0a55a3` verified it resolved (no re-raise).
It is closed on the merits; the F2 connector thread needs no further design change.

CORRECTION LOG — Consolidated correction 2 (OWNER-AUTHORIZED EXCEPTIONAL, beyond
the single GOV-1 cycle). The GOV-2 step-5 exact-corrected-head confirmation of
`f0a55a3` confirmed F2 resolved but surfaced one NEW valid P2 — the STATE
unavailable-reason did not reach the builder (the §5 input list carried only the
guarded call's `IntraState | None`, and the guard sets `None` on catch, so
`insufficient_bars` was indistinguishable from a natural pre-open `None`, while
§2.3 requires the builder to produce every card value). Per GOV-2 §6/§7 the packet
reopened as DESIGN INCOMPLETE and the author did not self-patch. **Dustin then
authorized one exceptional, narrowly bounded correction** scoped exactly to this
defect. Applied:
- **F3 (Codex step-5, packet L359) — carry the STATE failure reason into the
  builder.** A typed `StateOutcome` (§5) now carries **either** the computed
  `IntraState` **or** a typed `unavailable_reason` (`pre_open` /
  `insufficient_bars` / `not_computed`) from the §3 guard into
  `build_market_control_card`. The exception→reason mapping stays in the guard
  (runtime), never the renderer (§2.3 preserved: the builder produces the final
  STATE value/reason from the typed input). §3, §4 field 1, and §5 updated.
Scope discipline (per the owner authorization): this correction adds **no** file
(the `StateOutcome` type lives in the already-listed `market_control_card.py`; the
guard in the already-listed `runtime/__init__.py`), **no** contract key, **no**
new card field, and changes **no** FILES/LOC estimate, product scope, or D-1…D-5.
Next: **one final** independent Codex exact-head confirmation of the corrected
head. If it finds any additional boundary omission, the packet stops and returns
to Dustin — no further correction loop without his ruling (GOV-2 §7). No
implementation authority is created by this correction.

DERIVED AT: `main` @ `daa7065d4fb5ee5a4a051de05bd1d18cae375afc` (== `origin/main`;
the merge of PR #221, Owner-Merge / Agent-Managed-Closeout Convention). Working
tree clean at derivation. Branch carrying this packet:
`claude/ns-2e-market-control-card-jz6xxr`.

GOVERNING AUTHORITY (this packet invents no product direction; it composes what
these already establish):
- `docs/governance/PRODUCT_DELIVERY_OPERATING_RULE_2026-08-06.md` — Product-
  priority rule (ratified on PR #220): active lane 1 is **NS-2E Market Control
  Card**.
- `docs/DECISIONS.md` 2026-08-05 (nine TRUTH-SYNC rulings), ruling #1 —
  BALANCED route; product NEXT is NS-2E.
- `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:136` — NS-2E is
  `NEXT`; outcome "Compact orientation replacing/refactoring generic Market
  Map"; "Answers state, location, event, transition, invalidation, permission,
  candidate implication."
- `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:325-327` — "NS-2E —
  Market Control Card — now the live NEXT packet, with NS-2A/B/C existing to
  feed it. Still MATERIAL: it begins with its own upstream packet, not with
  code."
- `VISION.md:14-34,49-62` — the four questions and the Operating principles
  (description-not-prediction; read-only-sidecars-by-default; cuts-before-
  additions; the-system-serves-the-trader; docs-match-code).
- Evidence seed: `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md`
  (Control Card §, Q10–Q12) — HYPOTHESIS-class, pinned at `771f730`; **its line
  numbers and "unavailable in v1" list are re-verified against current `main` in
  §2 below, because NS-2A/2B/2C shipped after that pin.**

PROVENANCE NOTE (source pointer, resolved — for Dustin): the charge that
commissioned this packet cites "Prompt J2" in
`audits/compression-runway-2026-08-05/COMPRESSION_RUNWAY_PLAN_2026-08-05.md`.
That file was **never committed to the repository** (`git log --all --
audits/compression-runway-2026-08-05/*` is empty; the only commit referencing
the string is `8ba61f2`, the DECISIONS.md entry that cites the plan as an
off-tree planning packet). Consistent with the PRD-230 rule
(`CLAUDE.md` § Anti-patterns) that off-tree session scratch is discarded once
its durable rulings land in `docs/DECISIONS.md`. The J2 prompt's substance is
fully restated in the charge and its authority is the in-tree governing set
above, so this packet was produced within existing authority. If Dustin instead
wants the J2 plan restored before this packet is reviewed, this is a stop point.

CI CLAIM BOUNDARY (GOV-2 §8): This is a documentation-only packet. If CI runs
against the branch carrying it, green CI confirms only that this documentation
branch preserves the current green baseline. It does not execute or validate the
proposed runtime design, consumer inventory, contract, or regression plan.

PROVISIONAL-CEILING LABELS (GOV-2 §5): every FILES and LOC figure below is
`ESTIMATED SURFACE — NOT YET APPROVED`. The first binding ceiling is Gate A on
the reviewed PRD.

---

## 0. Where this packet sits in the GOV-2 order

Materiality (GOV-2 §1): **MATERIAL.** It selects an implementation seam shared
across pipeline layers (runtime → payload → renderer); it adds a new presented
surface with more than one reader; it crosses runtime, delivery/payload, and
dashboard. It is therefore ineligible for `LANE: MICRO`; the downstream PRD
rides STANDARD at minimum (§14).

Required order and current position:

| Step | GOV-2 §2 | State |
|---|---|---|
| 1 | Author investigates and self-verifies | DONE (this packet; §16 records the author self-verification) |
| 2 | Author produces provisional packet | DONE (this document) |
| 3 | Independent Codex review of packet + surface | **DONE** — reviewed `0a8f57ebf2`; two P2 findings, both valid (§16) |
| 4 | One consolidated author correction | **DONE** — correction 1 (top of packet); F1+F2 ACTIONED |
| 5 | Independent exact-corrected-head confirmation | **DONE** — reviewed `f0a55a3`; F2 confirmed resolved, one NEW valid P2 (F3: STATE reason does not reach the builder, §16) |
| 5b | **Owner-authorized exceptional correction 2** | **DONE** — Dustin authorized one bounded correction beyond the GOV-1 cycle; F3 ACTIONED via the typed `StateOutcome` (correction log + §3/§4.1/§5) |
| 5c | Final independent exact-head confirmation | **PENDING** — one final Codex confirmation of the corrected head; stop-and-return-to-Dustin if any additional omission |
| 6 | Dustin design-direction ruling | not started — **owner hold** (after review-clean) |
| 7 | PRD drafted + fresh-context independent review | not started |
| 8 | Dustin Gate A | not started — **owner hold** |

No PRD number is allocated by this packet (GOV-2 §2: the PRD is step 7, after
Dustin's ruling). No `prd_history/` file, no registry row, no `prd_index.json`
entry is created.

---

## 1. Product question and user-visible outcome

**Question the card answers (once, for SPY, on the daily dashboard):** where are
we, and what does it mean for whether I act? It is a compact, read-only
*orientation* surface — description, not prediction — answering the seven
ledger fields, which map onto VISION's four questions:

- STATE, LOCATION → Q1 "What environment are we in?"
- EVENT, TRANSITION → the meaningful-change axis feeding Q1/Q2
- INVALIDATION → Q4 "What would invalidate this?" (extreme stress = hard
  invalidation, `VISION.md:30-34`)
- PERMISSION, CANDIDATE IMPLICATION → Q3 "Is this actually tradable?"

**User-visible outcome:** one new block on the **daily** dashboard (a sibling of
the existing `spy-observation` block), rendered read-only. Every field either
carries a value traceable to an existing upstream producer, or is shown
explicitly UNAVAILABLE with a reason token. The card never asserts a value the
system has not computed.

**Scope boundary (binding for v1):**
- DAILY `_run_pipeline` only. The hourly publish path is OUT OF SCOPE (the hourly
  runtime builds a market map with empty intraday metrics — `runtime/__init__.py`
  hourly branch — and carries no SPY session observation; §9). This mirrors the
  NS-2A/2C daily-only boundary.
- The card is **additive**. It retires nothing in this slice. Whether it
  ultimately *replaces/refactors* the generic per-symbol Market Map board is a
  separate, larger slice — see §9 (SPLIT recommendation).

---

## 2. Exact producer → carrier → consumer seam

### 2.1 Current state (what exists at `daa7065d4`)

Re-verified against current `main` (the stage0-01 seed was pinned at `771f730`;
NS-2A/2B/2C have since shipped, so several "unavailable in v1" statements from
that seed are now partially satisfied — noted inline).

**The current "Market Map decision surface" is the per-symbol candidate card, not
a Control Card.** `_render_candidate_card` at
`cuttingboard/delivery/dashboard_renderer.py:1826-1991` renders, per graded
symbol: header (grade/setup_state/bias/structure, `1856-1874`), `IF NOW`
(`1876-1883`), the market-map `LIFECYCLE` line (`1885-1899`), `IN →`
(`1901-1907`), `OUT →` (`1909-1924`), and the `REASON`/`PLAY`/`WATCH` detail
(`1926-1945`). It is invoked from the candidate board ("Market Map / Developing
Setups") at `2866-2978` (card call `2959-2964`). This is per-*candidate*, not
per-*session*.

**A SPY session card already exists** (PRD-288 seed): the `spy-observation` block
at `dashboard_renderer.py:2538-2569`, gated on `payload["sections"]
["spy_observation"]`. It renders SESSION, STATE (a *freshness* state, not
market-state), OBSERVED AT, SESSION VWAP, PRICE (+`price_vs_vwap`), ORB — each
with an explicit UNAVAILABLE fallback (never fabricated). This is the Control
Card's seed and the exact render pattern it extends.

Producers of the seven fields at current `main`:

| Field | Producer at `main` | Persisted? |
|---|---|---|
| STATE | `IntraState.state` (`intraday_state_engine.py:86`; values `RANGE`/`FAILED_EXPANSION`/`EXPANSION_CONFIRMED`, `:479-492`). Built via `compute_intraday_state` — **single production call site** `runtime/__init__.py:1466**, inside the SHORT-permission gate `_apply_intraday_short_permission`. Returns `None` before 09:45 ET / <5 ORB bars (`:435-436`, `:91-92`). | Transient object. Only the `.state` string leaks to the durable audit record for **candidate** symbols (`audit.py:167,179`). Not computed for SPY unless SPY is itself a SHORT candidate. |
| LOCATION | `SpyObservation` (`spy_observation.py:48-61`): `session_vwap`, `current_price`, `price_vs_vwap` (`ABOVE`/`BELOW`/`AT_LEVEL`/`UNAVAILABLE`), `orb` (PRD-271 `OrbObservation`, projected verbatim). Built **unconditionally** each daily run at `runtime/__init__.py:1288`. | Transient; projected only into the render payload (`sections["spy_observation"]`), never the decision contract. |
| EVENT | none. `market_map_lifecycle.inject_lifecycle` (`market_map_lifecycle.py:39-99`) transitions **presentation** grade/setup only. | n/a |
| TRANSITION | none genuine. Same presentation lifecycle; no cross-run `IntraState` is loaded or diffed — market state is recomputed fresh and discarded each run. | n/a |
| INVALIDATION | no discrete value. Raw materials exist: ORB levels + VWAP (LOCATION), and the extreme-stress kill-switch (`_kill_switch`, thresholds `runtime/__init__.py:2319-2321`; terminal HALT per `docs/system_logic_map.md` / `VISION.md:30-34`). `invalidation.py` is per-*candidate* trade-thesis invalidation (PRD-068), not a market-read. | n/a |
| PERMISSION | `system_state.permission` (durable; `runtime/__init__.py:860`), plus the separate `downside_permission` axis (`:1477`) and per-candidate `TradeDecision.policy_allowed` (`trade_decision.py:41`; `execution_policy.py:188-229`). | `system_state.permission` is in the durable contract. |
| CANDIDATE IMPLICATION | per-candidate only: `policy_allowed` (`trade_decision.py:41`) and `visibility_map` (`trade_visibility.build_visibility_map`, `trade_visibility.py:31-53`). No card-level rollup statement. | Per-candidate durable in contract/audit. |

**The reusable carrier seam** (PRD-288 pattern — the card reuses it exactly):
`PipelineResult.spy_observation` (`runtime/_types.py:90-92`, an
`Optional[SpyObservation]` "transient intra-runtime carrier … never serialized
to a durable/decision contract") → assigned in `_run_pipeline` (`:1329`) →
handed as a **separate kwarg** (not via the contract dict) to
`_write_payload_artifacts(pipeline.contract, spy_observation=...)` (`:288`,
signature `:2282`, forward `:2289`) → `build_report_payload(..., spy_observation=
None)` (`delivery/payload.py:24-28`) → projected to `sections["spy_observation"]`
whenever the kwarg is non-`None` (`payload.py:140-141`, `_project_spy_observation`
`:160-185`) → rendered read-only (`dashboard_renderer.py:2538-2569`).
**Daily-only-ness is enforced by the runtime writer, not `payload.py`:** the daily
`_write_payload_artifacts` (`:288`) passes the kwarg; the hourly
`_write_hourly_artifacts` (`runtime/__init__.py:2140`) does not — so no
`spy_observation` section appears on the hourly payload. The card mirrors this
exactly.

### 2.2 Proposed seam (additive; nothing above is modified)

Introduce one transient carrier that rides the identical seam:

```
_run_pipeline (daily)
  build_market_control_card(spy_observation, intra_state?, permission, halted, kill_switch_state)   # NEW, pure
  → PipelineResult.market_control_card: Optional[MarketControlCard]                                   # NEW field on _types.py
  → _write_payload_artifacts(contract, spy_observation=..., market_control_card=...)                  # NEW kwarg, threaded
  → build_report_payload(contract, *, spy_observation=None, market_control_card=None)                 # NEW kwarg
  → sections["market_control_card"] = _project_market_control_card(...)                               # NEW projection (daily only)
  → dashboard_renderer: render read-only block, present iff the section is present                    # NEW render block
```

No decision contract key is added (§5). No existing producer, contract, or
artifact schema is modified. The card **composes** existing transient producers;
its only genuinely-new derivations are enumerated in §6.

### 2.3 The renderer-invents-nothing rule (binding)

Every value on the card is produced by `build_market_control_card()` (a pure
composition helper) or by a named upstream producer it reads. The renderer only
formats strings and chooses present/absent; it computes no decision-bearing
value. Where no producer exists for a field (EVENT, TRANSITION in v1), the field
is emitted as an explicit `UNAVAILABLE` token with a reason, never inferred,
back-filled, or relabeled from an adjacent value. In particular, the presentation
grade/setup lifecycle **must not** be relabeled as a market-state TRANSITION
(stage0-01 Q11, binding), and the SPY *freshness* state (PRE_OPEN/OBSERVED/STALE)
**must not** be conflated with the market STATE axis (they are two distinct
fields on the card).

---

## 3. Recommended implementation design (single design, not alternatives)

A new module `cuttingboard/market_control_card.py` mirroring
`spy_observation.py`: a frozen, transient, non-persisted `MarketControlCard`
dataclass and a pure `build_market_control_card(...)` that assembles the seven
fields from already-computed inputs passed in by `_run_pipeline` (it fetches
nothing and mutates nothing). The card is built once on the daily path, rides the
`PipelineResult` → payload-kwarg → `sections[...]` seam, and renders as a
read-only dashboard block. The design **reuses** the `SpyObservation` already
built at `runtime/__init__.py:1288` for LOCATION rather than recomputing VWAP/ORB
(one-truth rule: no second VWAP/ORB authority).

The single genuinely-new **always-on** derivation the design recommends is a
SPY market-STATE call (§6, field 1): today `compute_intraday_state` runs only
when SPY is a SHORT candidate, so STATE would almost always be UNAVAILABLE and
the card would fail "the-system-serves-the-trader." The SPY session bars are
already in hand each daily run (`_market_map_bar_windows` primary set includes
SPY; the SpyObservation session frame exists), and `compute_intraday_state` is
side-effect-free, so one additional always-on call
`compute_intraday_state("SPY", spy_bars)` is additive.

**Binding guard requirement (do not implement the call bare).**
`compute_intraday_state` does not merely return `None`; it can **raise**
`InsufficientDataError` — `_compute_orb` (`intraday_state_engine.py:130-138`)
raises when the 09:30–09:35 ET window holds fewer than five bars, a reachable
state for a post-09:45 SPY frame with sparse/late provider bars. The existing
production call site already isolates this in `try/except Exception`
(`runtime/__init__.py:1465-1471`, setting `intra_state = None` on failure). The
card's always-on call **must** reuse that isolation so a missing provider bar can
never **fail the daily pipeline** (violating §8 and the fail-loud-in-the-right-
place principle — the read-only card must not be the thing that halts the run).

**The guard produces a typed STATE outcome, not a bare `IntraState | None`
(correction 2, owner-authorized — resolves the step-5 P2).** A bare `None` on
catch cannot distinguish an `InsufficientDataError` (which must surface as
`insufficient_bars`) from a natural pre-open/not-computed `None`. So the guarded
computation in `_run_pipeline` yields a small typed `StateOutcome` (§5) carrying
**exactly one of**: the computed `IntraState`, or an explicit typed
`unavailable_reason` token (`pre_open` / `insufficient_bars` / `not_computed`).
The guard sets the reason from the two disjoint failure modes — a caught
`InsufficientDataError` → `insufficient_bars`; a `None` return → the engine's
documented pre-09:45 / no-state reason — and passes the `StateOutcome` into
`build_market_control_card`. The builder then produces the final STATE card value
(the `IntraState.state` string, or `UNAVAILABLE` plus `state_reason`) from that
typed input — so **the builder still produces every final card value (§2.3), and
the exception→reason mapping stays in the guard, never in the renderer.** The
guarded computation and the `StateOutcome` type both live in the already-listed
FILES (`runtime/__init__.py`, `cuttingboard/market_control_card.py`); this adds
no file, no contract key, and no card field.

**Whether v1 includes this always-on STATE call, or instead ships STATE as
"available-only-when-SPY-is-a-short-candidate / else UNAVAILABLE," is an
unresolved owner decision (§15, D-1). Either way the guard above applies wherever
the call is made.**

---

## 4. The seven-field contract (smallest truthful v1)

Each field is `value | UNAVAILABLE(reason)`. "Source" is the producer;
"Derivation" is what `build_market_control_card` does.

1. **STATE** — market-state classification. Source: the typed `StateOutcome` (§5)
   from the §3-guarded SPY call — carrying either the computed `IntraState` or a
   typed `unavailable_reason`. Derivation: the builder emits `IntraState.state`
   (`RANGE`/`FAILED_EXPANSION`/`EXPANSION_CONFIRMED`) when the outcome carries a
   state, else `UNAVAILABLE` with the carried `state_reason` (`pre_open` /
   `insufficient_bars` / `not_computed`). The exception→reason mapping happens in
   the §3 guard (a raised `InsufficientDataError` → `insufficient_bars`, never
   propagates); the builder produces the final STATE value from the typed input,
   so `insufficient_bars` is distinguishable from a natural pre-open `None`.
   Depends on D-1 (§15).
2. **LOCATION** — price vs session anchors. Source: the existing `SpyObservation`
   (`session_vwap`, `price_vs_vwap`, `orb`, `current_price`). Derivation:
   pass-through/compose from the already-built `SpyObservation`; inherits its
   UNAVAILABLE/STALE semantics verbatim. **EXISTS — no new derivation.**
3. **EVENT** — last meaningful intraday transition. Source: none (NS-2D `LATER`).
   Derivation: `UNAVAILABLE(reason="deferred_ns2d")`. Not derived in v1.
4. **TRANSITION** — genuine market-session transition. Source: none (would need
   cross-run `IntraState` persistence = a durable schema change, out of a
   read-only sidecar's scope). Derivation: `UNAVAILABLE(reason=
   "no_session_transition_source")`. Not derived in v1. Must not be sourced from
   presentation lifecycle (§2.3).
5. **INVALIDATION** — what voids the current read. Source: the extreme-stress
   kill-switch/terminal-HALT state (authoritative; `VISION.md:30-34`,
   `docs/system_logic_map.md`) **plus** the session-anchor reference levels
   already in LOCATION (ORB high/low, VWAP). Derivation (bounded, descriptive):
   report the hard-invalidation state (HALT active/inactive) and name the
   reference levels whose loss/break changes the read — **without** asserting a
   directional thesis (directional/ranked invalidation is NS-2F `LATER`).
   Anchor-level clauses are UNAVAILABLE when their source is UNAVAILABLE. **NEW
   derivation — bounded; owner decision D-2 (§15) on whether v1 includes it or
   defers.**
6. **PERMISSION** — trading posture, a separate axis from STATE. Source:
   `system_state.permission` (`runtime/__init__.py:860`). Derivation:
   pass-through of the existing global posture. **EXISTS — no new derivation.**
   Presented on its own axis (stage0-01 Q11, binding).
7. **CANDIDATE IMPLICATION** — what this means for candidates. Source: existing
   `visibility_map` (built at `runtime/__init__.py:1140`) and/or `trade_decisions`
   / candidate outcomes. Derivation (minimal): a descriptive count/presence
   statement (e.g. "N actionable candidate(s)" / "none"), derived from existing
   per-candidate data; UNAVAILABLE when candidate data absent. A richer
   negative-statement rollup ("no quality longs") is NS-3C `LATER`.
   **Realizability (binding, per Codex F2): if D-3 adopts this rollup, the
   selected candidate data (`visibility_map` and/or `trade_decisions`) MUST be
   passed into `build_market_control_card` as an explicit input — it is not in the
   base signature below. The renderer may not derive it (§2.3); a builder with no
   candidate input would force this field to be fabricated or always UNAVAILABLE.
   If D-3 defers, the field is `UNAVAILABLE(reason="deferred_ns3")` and no
   candidate input is threaded.** **PARTIAL — minimal rollup is new; owner
   decision D-3 (§15) on scope.**

---

## 5. Sidecar contract (`MarketControlCard`)

New frozen dataclasses in `cuttingboard/market_control_card.py`, transient and
non-persisted (mirrors `SpyObservation`). The `StateOutcome` type (correction 2)
is the typed carrier that lets the §3 guard convey *why* STATE is unavailable
without moving the mapping into the renderer:

```
@dataclass(frozen=True)
class StateOutcome:
    # Typed result of the §3-guarded always-on SPY IntraState call.
    # Exactly one side is populated; produced in _run_pipeline, consumed by the builder.
    state: IntraState | None = None            # the computed state, when available
    unavailable_reason: str | None = None      # "pre_open" | "insufficient_bars" | "not_computed"

@dataclass(frozen=True)
class MarketControlCard:
    observed_symbol: str            # "SPY"
    intended_session_date: date | None
    observed_at_utc: datetime | None
    # seven fields, each value-or-UNAVAILABLE:
    state: str                      # market-state token or "UNAVAILABLE"
    state_reason: str | None
    location: <compose from SpyObservation: vwap, price_vs_vwap, orb summary>
    event: str                      # "UNAVAILABLE"
    event_reason: str | None        # "deferred_ns2d"
    transition: str                 # "UNAVAILABLE"
    transition_reason: str | None   # "no_session_transition_source"
    invalidation: <hard-halt state + reference levels> | "UNAVAILABLE"
    permission: str                 # existing system_state.permission posture
    candidate_implication: str | "UNAVAILABLE"
```

(Exact field shape is design-level; the reviewed PRD fixes it.)

**Builder inputs (binding).** `build_market_control_card` is pure and reads only
what `_run_pipeline` passes it: the already-built `SpyObservation` (LOCATION), the
typed **`StateOutcome`** from the §3-guarded call (STATE — carries the computed
`IntraState` **or** the typed `unavailable_reason`, so the builder emits the right
STATE value/reason itself), `system_state.permission` (PERMISSION), the halt flag,
and the kill-switch state (INVALIDATION). **If D-3
adopts the candidate rollup (§4 field 7, Codex F2), the selected candidate data
— `visibility_map` (`runtime/__init__.py:1140`) and/or `trade_decisions` — is an
additional explicit builder input and rides the same transient carrier; it is NOT
sourced by the renderer.** No builder input is fetched or mutated by the card.

**Schema / persistence classification (binding):** NOT a schema. NOT persisted.
NOT a decision-contract key. It is a transient render sidecar projected only into
`sections["market_control_card"]` of `latest_payload.json` (a render artifact),
exactly like `spy_observation`. It does not touch `contract.json`,
`market_map.json`, the audit record, or any cross-run state. This satisfies
VISION read-only-sidecars-by-default and keeps the decision contract frozen.

---

## 6. Values already existing vs new derivation

| Field | Verdict | If new, what exactly |
|---|---|---|
| STATE | EXISTS (conditional) | Optionally one always-on `compute_intraday_state("SPY", spy_bars)` call so STATE is present most sessions (D-1), guarded and carried into the builder via the typed `StateOutcome` (§3, §5). Engine unchanged. |
| LOCATION | EXISTS | none — reuse `SpyObservation`. |
| EVENT | NEW | none in v1 — emit UNAVAILABLE (deferred NS-2D). |
| TRANSITION | NEW | none in v1 — emit UNAVAILABLE (no source; forbidden to source from presentation lifecycle). |
| INVALIDATION | NEW (bounded) | a pure composition over existing kill-switch state + existing anchor levels; no new inputs fetched (D-2). |
| PERMISSION | EXISTS | none — reuse `system_state.permission`. |
| CANDIDATE IMPLICATION | PARTIAL | a minimal descriptive rollup over existing candidate/visibility data (D-3). |

Net: **four of seven fields need no new derivation** (LOCATION, PERMISSION, and
the two explicit-UNAVAILABLE deferrals EVENT/TRANSITION). STATE needs at most one
always-on call to an existing pure engine. INVALIDATION and CANDIDATE
IMPLICATION are bounded compositions over existing values. No new data source, no
new fetch, no schema change.

---

## 7. Lifecycle, reason tokens, and UNAVAILABLE semantics

The card inherits the daily run's freshness truth from `SpyObservation`
(PRE_OPEN/OBSERVED/STALE/UNAVAILABLE and its reason tokens,
`spy_observation.py:25-28,84-114`). On a system HALT the card is present and
truthful: LOCATION/STATE report UNAVAILABLE (`system_halted`), INVALIDATION
reports the hard-invalidation HALT as active. Field-level reason tokens
introduced by the card are limited to `deferred_ns2d` (EVENT),
`no_session_transition_source` (TRANSITION), and STATE's pass-through reasons.
No new global lifecycle vocabulary is created.

---

## 8. Explicit non-effects on execution (read-only)

The card reads `IntraState`, `SpyObservation`, `system_state.permission`, and
kill-switch state; it **mutates none of them** and feeds nothing back into
routing, qualification, sizing, gating, or the contract. Removing the card from
the build would change no decision, no audit record, and no contract byte — only
the rendered daily dashboard. If the always-on STATE call (D-1) is adopted, it is
an additional read-only invocation of a pure engine; it does not enter the
short-permission gate and cannot change candidate filtering.

---

## 9. Market Map retirement — SPLIT (recommended); this slice is additive

The ledger outcome says "replacing/refactoring generic Market Map." This packet
recommends the retirement be **split out of the v1 card slice**, for concrete,
enumerated reasons:

Retiring/refactoring the generic per-symbol Market Map board
(`dashboard_renderer.py:1826-1991` card + `2866-2978` board) is a **subtractive**
change that orphans multiple **live** consumers, each of which must be
re-homed or deleted with its own dead-branch enumeration:
- `trade_visibility.build_visibility_map` reads `market_map["symbols"][sym]
  ["grade"]` — `trade_visibility.py:40-53`.
- `overnight_policy._near_key_level` reads `["watch_zones"]` —
  `overnight_policy.py:167-178`.
- `macro_pressure.build_macro_pressure(macro_drivers, market_map)` —
  `macro_pressure.py:112-116`.
- Renderer secondary market_map readers: `_build_tape_value_slots`
  (`1249-1265`), `_build_pressure_snapshot` (`1473-1477`), `_build_integrator_
  input` (`1399-1413`), `_build_sunday_context` (`1501-1527`), high-grade count
  (`2334-2340`).
- `inject_lifecycle` producer (`market_map_lifecycle.py:39`) and its writers
  (`runtime/__init__.py:289-291` daily, `571-601` hourly), plus the
  `LATEST_HOURLY_MARKET_MAP_PATH` artifact contract (`_constants.py:55`; CI-
  guarded by `tests/test_ci_artifact_hygiene.py:164-166,274`).

Per VISION cuts-before-additions, a cut must justify itself; the honest sequence
is to ship the additive Control Card first, let it earn its keep, **then** open a
separate MATERIAL packet for the Market Map retirement with a full dead-branch
enumeration. Trying to retire in the same slice would multiply the FILES ceiling
and the risk without a truthful need. **Recommendation: additive card now;
retirement is a distinct later slice. Owner decision D-4 (§15).**

**Related live drift found (not fixed here):** the notification lifecycle
renderer (`notifications/__init__.py:288-395`) is already a **dead branch** in
production — the runtime callers `format_hourly_notification`
(`runtime/__init__.py:502-510`) and `format_notification` (`:512-523`) pass no
`market_map=`, so lifecycle alerts always receive `None` and emit nothing; only
tests exercise that code. This is pre-existing and out of scope for the card; it
belongs to the eventual Market Map retirement slice (wire it or delete it).
Recorded so the retirement packet inherits it, not silently carried.

---

## 10. Exact likely FILES (ESTIMATED SURFACE — NOT YET APPROVED)

Production (5):
1. `cuttingboard/market_control_card.py` — NEW. `MarketControlCard` +
   `build_market_control_card()`.
2. `cuttingboard/runtime/_types.py` — add `market_control_card:
   Optional[MarketControlCard] = None` to `PipelineResult` (mirror `:90-92`).
3. `cuttingboard/runtime/__init__.py` — build the card in `_run_pipeline`
   (near `:1288`), assign to the result (near `:1329`), thread the kwarg through
   the daily `_write_payload_artifacts` (`:288`, `:2282`, `:2289`); if D-1
   adopted, one always-on `compute_intraday_state("SPY", …)` call. The **second**
   production `build_report_payload` caller is the hourly `_write_hourly_artifacts`
   (`:2140`); it is left untouched, so the new keyword-only default-`None` kwarg
   provably breaks no caller and the card stays daily-only.
4. `cuttingboard/delivery/payload.py` — add the kwarg to `build_report_payload`
   and `_project_market_control_card` projection (mirror `:140-141,160-185`).
5. `cuttingboard/delivery/dashboard_renderer.py` — the read-only render block
   (mirror the SPY block `:2538-2569`).

Tests (4–5) — the PRD-158 grep sweep of `tests/` for the tokens this design
touches (the existing SPY-card, candidate-card, and lifecycle assertions are the
compatibility baseline that must stay green):
6. `tests/test_market_control_card.py` — NEW. Builder/composition units;
   present/absent and UNAVAILABLE-not-fabricated per field.
7. `tests/test_payload.py` — projection mirror + daily-only presence.
8. `tests/test_dashboard_renderer.py` — render block present/absent; halt truth;
   UNAVAILABLE rendering; **regression guard that the existing `spy-observation`
   block (`:2538-2569`) and candidate board are unchanged.**
9. `tests/test_runtime_decision.py` — carrier threading through
   `PipelineResult`/`_write_payload_artifacts`; present on daily, absent
   otherwise.
- Possibly `tests/test_spy_observation.py` only if the compose reuses its
  fixtures.

Compatibility baseline (must stay green, not edited unless a token they assert is
deliberately changed — none is planned): `tests/test_dash_candidates.py`
(candidate card IN→/OUT→/IF NOW/LIFECYCLE), `tests/test_market_map_lifecycle.py`,
`tests/test_market_map.py`, `tests/test_notifications.py`,
`tests/test_ci_artifact_hygiene.py`. **The card adds a surface; it renames/removes
no existing rendered token, so no existing assertion should require editing. If
implementation finds otherwise, that is a scope-expansion stop-and-amend event
(§13).**

Docs candidate to resolve at PRD-stage FILES sweep: a new presented dashboard
surface plausibly warrants a one-line entry in a dashboard-surface doc
(`docs/system_logic_map.md` or equivalent) under VISION docs-match-code. Carried
here as a note for the PRD's PRD-158 grep sweep, not counted in the estimate.

ESTIMATE: ~9 files (5 production + 4 test). This is provisional (GOV-2 §5).

---

## 11. Estimated production LOC ceiling (ESTIMATED SURFACE — NOT YET APPROVED)

- `market_control_card.py`: ~120–160 (cf. `spy_observation.py` = 174).
- `_types.py`: +2.
- `runtime/__init__.py`: +8–15 (build + thread; +~5 if D-1 always-on STATE).
- `payload.py`: +20–30 (projection).
- `dashboard_renderer.py`: +30–45 (render block).

Estimated production net: **~+180–250 LOC**, additive. Tests: ~+150–250 LOC.
Provisional; the binding ceiling is Gate A on the reviewed PRD.

---

## 12. Discriminating test plan (present/absent + mutation)

**Present/absent compatibility:**
- PRESENT: on a daily OBSERVED run the card block renders with LOCATION +
  PERMISSION populated, STATE populated (per D-1), and EVENT/TRANSITION shown
  UNAVAILABLE with their reason tokens.
- ABSENT: when the payload carries no `market_control_card` section, the block is
  omitted entirely — mirroring the SPY block's section-gated omission
  (`dashboard_renderer.py:2540`). A **named** test asserts the hourly writer
  (`_write_hourly_artifacts`, `runtime/__init__.py:2140`) emits no
  `market_control_card` section (daily-only-ness is a runtime-writer property,
  not a `payload.py` property).
- HALT: the block is present and truthful — STATE/LOCATION UNAVAILABLE
  (`system_halted`), INVALIDATION reports HALT active, no fabricated numbers.
- CONTRACT UNCHANGED: a test asserts `contract.json` / `market_map.json` bytes
  are unaffected by the card (read-only sidecar).
- EXISTING SURFACES UNCHANGED: a test asserts the `spy-observation` block and the
  candidate board render identically with and without the card.

**Mutation plan (each guard ships a red test — PRD-198 #4):**
1. Drop `market_control_card` from `PipelineResult` / stop threading the kwarg →
   the PRESENT render test goes red (carrier proven load-bearing).
2. Emit a fabricated STATE/LOCATION value when the producer is UNAVAILABLE → the
   "UNAVAILABLE-not-fabricated" test goes red (renderer-invents-nothing, §2.3).
3. Source TRANSITION from the presentation grade/setup lifecycle → the
   "no market-state relabel" test goes red (stage0-01 Q11).
4. Conflate the SPY freshness state with the market STATE field → a
   two-distinct-fields test goes red.
5. Omit the extreme-stress HALT from INVALIDATION (if D-2 adopted) → the
   hard-invalidation test goes red.
6. Render the card on the hourly path → the daily-only presence test goes red.

Each mutation must turn ≥1 **named** test red; a guard that no mutation can break
is banned (PRD-198 #4).

---

## 13. Stop-and-amend conditions

Stop, re-run GOV-2 §1 materiality, and amend the packet/PRD (with fresh
independent review and, after Gate A, an amended Gate A per GOV-2 §5) if
implementation discovers any of:
- a decision-contract key, `market_map.json`, or audit-record change is needed
  (would break the read-only-sidecar classification, §5);
- an existing rendered token must be renamed/removed (would pull compatibility
  test files into FILES beyond the additive baseline, §10);
- STATE cannot be produced for SPY without entering or altering the
  short-permission gate (would cross into execution behavior, §8);
- INVALIDATION or CANDIDATE IMPLICATION cannot be produced without a new data
  source or a directional/predictive judgment (would violate description-not-
  prediction; defer the field to UNAVAILABLE instead);
- the hourly path is pulled in (explicitly OUT OF SCOPE, §1/§9);
- a previously-omitted consumer class surfaces (GOV-2 §6 boundary-reset).

---

## 14. Materiality / lane classification

MATERIAL (GOV-2 §1): shared runtime→payload→renderer seam; new presented surface
with more than one reader; crosses runtime/delivery/dashboard. Therefore **MICRO-
ineligible**. The downstream PRD rides **STANDARD** (a new read-only observational
surface, additive, no execution/contract change). It is **not** HIGH-RISK on its
face: it changes no execution gate, no contract, no persisted schema — the R11
(PRD-121) downgrade-prohibition triggers do not fire on a read-only sidecar. If
D-1's always-on STATE call, on review, is judged to touch execution-adjacent
behavior, re-run classification (§13). Final lane is set on the drafted PRD at
review; this packet does not fix it (GOV-2: lane is a PRD-stage property).

---

## 15. Unresolved owner decisions (for Dustin's design-direction ruling)

- **D-1 (STATE availability).** Adopt the single always-on
  `compute_intraday_state("SPY", spy_bars)` call so STATE is present most
  sessions? Or ship STATE as available-only-when-SPY-is-a-short-candidate, else
  UNAVAILABLE? Recommendation: **adopt the always-on call** (else the field is
  near-always empty and fails serves-the-trader); it is a read-only call to a
  pure engine.
- **D-2 (INVALIDATION scope for v1).** Include the bounded descriptive
  INVALIDATION (hard-HALT state + reference anchor levels, no directional
  thesis)? Or defer INVALIDATION entirely to NS-2F and show UNAVAILABLE?
  Recommendation: **include the bounded form** — it directly serves VISION Q4 and
  uses only existing values.
- **D-3 (CANDIDATE IMPLICATION scope).** Minimal presence/count rollup from
  existing candidate data, or defer to NS-3 and show UNAVAILABLE?
  Recommendation: **minimal rollup** (cheap, truthful, from existing data);
  negative-statement richness stays NS-3C.
- **D-4 (Market Map retirement split).** Confirm the retirement/refactor of the
  generic per-symbol Market Map board is a **separate later slice**, with the card
  additive in v1? Recommendation: **yes, split** (§9).
- **D-5 (provenance).** Proceed on in-tree authority (the J2 plan is off-tree and
  its rulings are durable in DECISIONS.md), or restore the compression-runway
  plan file before review? Recommendation: **proceed**; the plan was session
  scratch per PRD-230.

---

## 16. Packet review records (GOV-2 §2, §7)

### INITIAL PACKET REVIEW (GOV-2 §2 step 3) — **DONE**

- Event type: `INITIAL PACKET REVIEW`.
- Reviewer identity / role: `chatgpt-codex-connector[bot]` (Codex), the
  fresh-context second-model reviewer, auto-triggered on the PR being marked
  ready for review. Independent of the authoring session.
- Reviewed commit: `0a8f57ebf2977e78e32375c648e0dff86013828` (the packet head at
  review time).
- Review date: 2026-08-06. Delivered as PR #222 review comments.
- Verdict: two P2 findings, no P1/blocker; both confirmed valid against current
  `main` by the author.
- Findings and dispositions (both **ACTIONED** by consolidated correction 1 —
  see the CORRECTION LOG at the top of this packet):
  - **F1** (packet L226) guard the always-on STATE computation against
    `InsufficientDataError` → ACTIONED (§3, §4 field 1).
  - **F2** (packet L180) pass candidate outcomes to the builder for D-3 →
    ACTIONED (§4 field 7, §5).

Dustin commissioned this review by marking PR #222 ready for review (the connector
auto-triggers on that event); it was not self-run by the author (Codex is not
installed in the packet-authoring environment).

### EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 §2 step 5) — **DONE — NOT CLEAN**

- Event type: `EXACT-CORRECTED-HEAD CONFIRMATION`.
- Reviewer identity / role: `chatgpt-codex-connector[bot]` (Codex), fresh-context
  second-model reviewer; re-triggered by Dustin's `@codex review` comment on
  PR #222. Independent of the authoring session.
- Reviewed commit: `f0a55a3d0094b7a66c762e93656cfb1244e04e0e` (the corrected head).
- Review date: 2026-08-06.
- Prior findings confirmed resolved: **F2** (candidate-outcome builder input) —
  resolved at this head, no re-raise.
- **NEW finding (P2), packet L359 — STATE failure reason does not reach the
  builder.** The consolidated-correction-1 STATE guard maps a caught
  `InsufficientDataError` to `UNAVAILABLE(insufficient_bars)`, but §5's binding
  builder-input list passes only the guarded call's `IntraState | None` result.
  The existing guard pattern (`runtime/__init__.py:1465-1471`) sets
  `intra_state = None` on catch, so the builder receives bare `None` and **cannot
  distinguish** `insufficient_bars` (caught raise) from a natural
  `pre_open`/`not_computed` `None` — yet §2.3 requires the builder (not the
  runtime, not the renderer) to produce every card value. Doing the reason-mapping
  outside the builder conflicts with §2.3. Confirmed valid by the author against
  `intraday_state_engine.py:130-138` and `runtime/__init__.py:1465-1471`.
- **GOV-2 §6/§7 consequence at the time:** the packet reopened as DESIGN
  INCOMPLETE; the omission was in the STATE input-carrier that correction 1 itself
  introduced, so the author did not self-certify its own boundary and did not
  self-apply a second correction. The decision went to Dustin.
- **Resolution — Dustin authorized one exceptional bounded correction.** Scoped
  exactly to this defect. F3 is **ACTIONED** by consolidated correction 2 (the
  typed `StateOutcome` — §3, §4 field 1, §5; correction log at the top). The
  connector thread's disposition is therefore ACTIONED (fix in the corrected head
  below); it remains unresolved on GitHub only pending the final exact-head
  confirmation.

### FINAL EXACT-HEAD CONFIRMATION (owner-authorized correction 2) — **PENDING**

The exceptional-correction head requires one final independent Codex confirmation
that F3 is resolved and no additional boundary omission exists. Dustin re-triggers
it (`@codex review`). Per his authorization and GOV-2 §7, if that review finds any
additional boundary omission the packet **stops and returns to Dustin** — no
further correction loop without his ruling. Until it returns clean, the packet
remains PROVISIONAL — NOT REVIEW-CLEAN and confers no downstream authority.

### AUTHOR SELF-VERIFICATION (GOV-2 §3 — NOT independent review)

Recorded for transparency; explicitly does **not** satisfy the independent-review
requirement (GOV-2 §3: a subagent spawned by the author cannot satisfy it).
- Prerequisites re-verified at `main` @ `daa7065d4` (== origin/main); working
  tree clean.
- Two fresh-context sub-agent seam traces (renderer/consumer; producer/state),
  both re-verified against current `main`; the load-bearing anchors
  (candidate-card block, SPY card block, carrier seam, single STATE call site,
  notification dead branch) were re-run by the authoring agent directly.
- One fresh-context sub-agent review of this packet (did not author it),
  instructed to falsify every load-bearing citation and design claim against
  current `main`. **VERDICT: ACCEPT — no required corrections.** It independently
  re-derived the renderer blocks, the full carrier seam, the single
  `compute_intraday_state` production call site (`:1466`, via grep), the
  notification dead branch, the engine state values, and all three §9 live
  Market Map consumers; all resolved at `daa7065d4`. It confirmed FILES
  completeness (the payload validation layer tolerates extra sections — no schema
  bump; the new keyword-only default-`None` kwarg breaks no existing
  `build_report_payload` caller). Three non-blocking RECOMMENDED refinements were
  folded into this revision: (i) daily-only projection attributed to the runtime
  writer, not `payload.py` (§2.1, §12); (ii) the second emitter
  `_write_hourly_artifacts` (`:2140`) named as provably unaffected (§10); (iii) a
  docs-match-code dashboard-surface doc entry carried to the PRD FILES sweep
  (§10). This is author-side self-verification only; per GOV-2 §3 it does **not**
  satisfy the independent-review requirement — that is the Codex INITIAL PACKET
  REVIEW above (now DONE; its two P2 findings ACTIONED in correction 1), which the
  exact-corrected-head confirmation must still clean-confirm.

---

*End of packet v0.1. No implementation authority. No PRD number allocated. Held
for Dustin's decision.*
