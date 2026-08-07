# NS-2E — Market Control Card — MATERIAL PACKET (v0.4, REPLACEMENT)

STATUS: REVIEW-CLEAN / MERGED (PR #227, merge commit
`53e76d56350c3d0a6a60cb0e4f80235e28f2f774`, reviewed head
`b78e77c1bdabb433565af2928bbf03c33a67395c`) — NO IMPLEMENTATION AUTHORITY.
This packet carries no implementation authority; Gate A is neither requested
nor granted. Option A and all ratified owner rulings are unchanged. The owner
rulings in §16 marked RATIFIED were ratified by Dustin on 2026-08-07 in the
authorization commissioning this packet; the remainder stay RECOMMENDED —
PENDING RATIFICATION.

## Supersession and termination statement (binding context)

**PR #226 (v0.3) was TERMINATED, not corrected further, because vocabulary
closure had not been exhaustively reconciled before the seven-field composer
vocabulary was specified.** Three successive review events each surfaced one more
closed-vocabulary/raw-token mismatch (shared observation reasons; then the
INVALIDATION `INSUFFICIENT_DETERMINISTIC_INPUTS` projection), which is evidence
of a missing upstream step, not of a correctable defect. The owner terminal
condition fired and the correction chain stopped.

**v0.4 REPLACES PR #226 and does not continue its correction chain.** PR #222
(v0.1), PR #225 (v0.2), and PR #226 (v0.3) are preserved untouched as the
historical review trail; none is edited or re-adjudicated here, and their review
events satisfy no v0.4 gate. Nothing NS-2E exists on `main` at derivation.

**Normative design input.** This packet is authored from the bounded read-only
Producer→Field Vocabulary Reconciliation (2026-08-07, commissioned by Dustin
after the PR #226 terminal stop; incorporated in full in §2 and §7 below — the
reachability tables ARE that reconciliation). Every `file:line` anchor was
verified against `main` @ `26c2afea163599ebae3c646ef244a4ea91683f7f`.

CHRONOLOGY / AUTHORITY (binding):
- v0.1 (PR #222) → terminal review exposed a missing F5 regression proof.
- v0.2 (PR #225, reviewed head `48eed6d`) → five substantive findings; owner
  terminal rule fired → fundamental redesign.
- v0.3 (PR #226, final head `a122a1c`) → Option A architecture survived three
  review events; each event found one more vocabulary-closure defect; final
  exact-head confirmation raised the INVALIDATION raw-token P1 → owner terminal
  condition fired → BLOCKED, frozen as historical evidence.
- 2026-08-07: bounded read-only producer→field vocabulary reconciliation
  performed against `main` @ `26c2afe` and the exact PR #226 packet; verdict
  OPTION A UNAFFECTED; recommendation AUTHOR REPLACEMENT MATERIAL PACKET.
- 2026-08-07: Dustin authorized this v0.4 replacement packet and ratified the
  §16 rulings marked RATIFIED.
- Gate A: not requested, not granted.

DERIVED AT: `main` @ `26c2afea163599ebae3c646ef244a4ea91683f7f` (post GEX-0 docs
PRs #223/#224). Working tree clean at derivation.

GOVERNING DIRECTION: preserve Option A unchanged — single authoritative FRAME A,
no second SPY fetch, `spy_state.py` bounded STATE seam, `SpyStateOutcome` XOR
carrier, same ORB rationale, same failure boundary, same persistence
classification, no changes to `spy_observation.py` or `intraday_state_engine.py`
— and replace the seven-field vocabulary layer with the reconciled,
code-demonstrated contract in §7.

CI CLAIM BOUNDARY (GOV-2 §8): documentation-only packet. Green CI on the branch
carrying it confirms only that the branch preserves the current green baseline;
it does not execute or validate the proposed design.

PROVISIONAL-CEILING LABELS (GOV-2 §5): every FILES and LOC figure below is
`ESTIMATED SURFACE — NOT YET APPROVED`. The first binding ceiling is Gate A on
the reviewed PRD.

---

## 0. Where this packet sits in the GOV-2 order

```
materiality check at intake ............................. DONE (MATERIAL; §15)
producer→field vocabulary reconciliation ................ DONE (2026-08-07; §2, §7)
provisional material packet authored .................... DONE (this v0.4 doc)
independent packet review (GOV-2 §2 step 3) ............. DONE (2026-08-07,
                                                          PR #227 @ b95cccc,
                                                          4 findings F1-F4; §18)
one consolidated correction (step 4) ................... DONE (this revision —
                                                          the single GOV-1 cycle,
                                                          authorized 2026-08-07)
exact-corrected-head confirmation (step 5) ............. DONE (2026-08-07:
                                                          4b8c7d0 confirmed, one
                                                          P2 → owner-authorized
                                                          micro-correction; final
                                                          narrow confirmation on
                                                          b78e77c CLEAN; packet
                                                          merged @ 53e76d5, §18)
Dustin design-direction ruling (step 6) ................ DONE (2026-08-07:
                                                          PROCEED with Option A;
                                                          recorded in
                                                          docs/DECISIONS.md,
                                                          "2026-08-07 — NS-2E
                                                          design-direction
                                                          ruling"; D-1 YES,
                                                          D-4 SPLIT, D-5
                                                          PROCEED, R3
                                                          dashboard+payload only)
Stage-0 PRD drafting (step 7) .......................... IN PROGRESS (PRD-289
                                                          allocated)
independent PRD review (step 7) ........................ PENDING
Dustin Gate A (step 8) ................................. PENDING (not requested)
```

MICRO-ineligible (MATERIAL, §15); rides STANDARD at minimum.

---

## 1. Product question and user-visible outcome

A compact, read-only SPY **Market Control Card** on the **daily** dashboard,
answering VISION's questions at a glance: where are we, what is the market's
state, what am I permitted to do, and what does that imply for today's
candidates — without prediction, inventing nothing.

- **Scope: the daily `_run_pipeline` only, and NOT `MODE_SUNDAY` (ruled F1,
  2026-08-07).** Hourly is OUT OF SCOPE from inception. **The card is not
  produced and not rendered for `MODE_SUNDAY` runs**: Sunday skips the entire
  candidate/gate block (`runtime/__init__.py:1021-1123`) while the defaults
  (`outcome=NO_TRADE`, empty maps, `:983-989`) still hold, so a Sunday card
  could only misreport skipped gates as truthful emptiness. ELIGIBLE runs —
  the only runs on which the composer executes — are daily `_run_pipeline`
  executions in `MODE_LIVE` or `MODE_FIXTURE` (halted eligible runs included).
  There is no Sunday-specific unavailable token; the card is simply absent
  (payload section omitted, renderer block absent), pinned by M23.
- **Seven fields, each value-or-explicit-UNAVAILABLE:** LOCATION, STATE,
  PERMISSION, EVENT, TRANSITION, INVALIDATION, CANDIDATE-IMPLICATION. Every
  field is a truthful value or a typed UNAVAILABLE carrying a reason token from
  a closed per-field vocabulary (§7); the renderer invents nothing (§2.3).

---

## 2. Producer graph and current state (verified at `main` @ `26c2afe`)

### 2.1 Producer graph — which producers feed which fields

```
fetch_intraday_session_bars("SPY")  [FRAME A]  (runtime/__init__.py:1043;
    declared None @ :981; stays None on halt/kill-switch/Sunday/fixture paths)
 ├─► build_spy_observation (spy_observation.py:64) ─────────► LOCATION
 │        (direct projection, incl. the verbatim PRD-271 ORB sub-object)
 │        └─ freshness axis SpyObservation.state ───────────► STATE cascade
 └─► [proposed spy_state.py seam] compute_intraday_state ───► STATE

compute_regime → RegimeState.posture ─┐
validation_summary.system_halted ─────┴─► _PERMISSION_LINES
    (runtime/_constants.py:81-87) → system_state.permission
    (runtime/__init__.py:855-860) ──────────────────────────► PERMISSION

red_folder.load_schedule() (red_folder.py:91; PRD-176) ─────► EVENT
    (exists TODAY, consumed renderer-side only:
     dashboard_renderer.py:3193-3211, :3258; v0.4 routes the
     same pure read into the card builder, keyed on run_at_utc)

IntraState same-run fields (intraday_state_engine.py:63-88:
    orb_break_direction, holding_bars, reclaimed_orb,
    failed_reclaim, phase, permission_state ∈ {IDLE, BREAK_ONLY,
    HOLD_CONFIRMED, FAILURE_CONFIRMED} (confirmation.py:11-14)) ─► TRANSITION

apply_thesis_gate (trade_thesis.py:134)
  → apply_invalidation_gate (invalidation.py:129)
  → invalidation_guidance_map (single production caller
    runtime/__init__.py:753) ──────────────────────────────► INVALIDATION

build_visibility_map (trade_visibility.py:31; call site :1140)
  + run outcome (TRADE/NO_TRADE/HALT; output.py:232-234,
    derivation runtime/__init__.py:766-774, halt :1000/:1016) ─► CANDIDATE-IMPLICATION
```

**Run-class defaults that ARE producers** (`runtime/__init__.py:981-989`): on
halt, kill-switch halt, Sunday, and fixture paths, `spy_session_frame=None`,
`thesis_map={}`, `invalidation_guidance_map={}`, `trade_decisions=[]` (→
`visibility_map={}`), `overall_pressure="UNKNOWN"`. `build_spy_observation` runs
on BOTH halt and non-halt branches (:1284-1293).

### 2.2 The frame split (unchanged from v0.3; re-verified)

- **FRAME A** — `spy_session_frame = fetch_intraday_session_bars("SPY")`
  (`runtime/__init__.py:1043`; `ingestion.py:281`, `retain_full_session=True`):
  the COMPLETE 09:30–16:00 ET session, UTC-indexed, NO `.tail` truncation.
  Exactly 3 references (:981, :1043, :1290); never reaches
  `compute_intraday_state`.
- **FRAME B** — the intraday short-gate frame: `fetch_intraday_bars(symbol)`
  (`:1454`) → `_intraday_state_bars_from_df` (`:1459`, def `:1576-1591`) →
  `compute_intraday_state(...)` (`:1466`). Default fetch bounds to
  `between_time("09:30", "15:30")` then `.tail(120)` (`ingestion.py:195`), so
  FRAME B drops the 09:30–09:35 ORB bars late in the session —
  `_compute_orb` raises `InsufficientDataError`
  (`intraday_state_engine.py:132-137`). **FRAME A is the only existing SPY frame
  from which a daily/EOD STATE is reliably computable.** The short-gate call
  site's blanket `except Exception` (`:1468`) is the anti-pattern the §5 seam
  corrects, not the idiom it copies; that site is NOT modified or reused.
- **Freshness ownership:** `build_spy_observation` (`spy_observation.py:64-126`)
  decides `OBSERVED`/`STALE`/`PRE_OPEN`/`UNAVAILABLE` (constants `:25-28`) from
  the 180 s threshold (`:33`), session-date match, and ET session gates. A `str`
  from module constants, NOT an enum.
- **Delivery:** `PipelineResult.spy_observation` (`runtime/_types.py:92`) →
  `build_report_payload(contract, fixture_mode=False, *, spy_observation=None)`
  (`payload.py:24-29`) → `sections["spy_observation"]` iff provided
  (`:140-141`, projector `:160-185`) → `logs/latest_payload.json` /
  `dashboard.html`. `assert_valid_payload` (`payload.py:188`) rejects only
  MISSING canonical section keys — an additive `sections["market_control_card"]`
  passes with no required-key change and no `PAYLOAD_SCHEMA_VERSION` bump.
- Confirmed: no `MarketControlCard`, `SpyStateOutcome`, or `spy_state.py` exists
  in production today.

### 2.3 Binding rule

Read-only presentation surface. The **builder is the SOLE producer** of every
final card value; the **renderer projects and never derives, defaults, or
invents**. No decision-contract key; no persistence beyond §8. All card-side
time logic is keyed on `run_at_utc` — never wall-clock `now()` — so the card is
deterministic for a given run. **The composer contract is defined over ELIGIBLE
runs only (§1): daily `MODE_LIVE`/`MODE_FIXTURE` executions. On `MODE_SUNDAY`
the composer is not invoked and the card does not exist** — every §7 mapping
presupposes an eligible run.

---

## 3. Recommended implementation design (Option A, preserved; EVENT routed)

One build, once, on the eligible daily path (`MODE_LIVE` / `MODE_FIXTURE`;
never `MODE_SUNDAY`, §1):

1. **Single-frame STATE acquisition.** `spy_state.py` receives FRAME A (the
   exact `spy_session_frame` object) and the SPY `previous_close`
   (`_reconstruct_previous_close`, `runtime/__init__.py:1594-1600` — `None` on
   absent quote or non-positive denominator, accepted by the engine); adapts
   FRAME A → `list[Bar]` (owned adapter); calls `compute_intraday_state`
   READ-ONLY; all acquisition failures resolve inside the one seam to a typed
   `SpyStateOutcome` (§5). No second SPY fetch.
2. **Typed XOR carrier.** `SpyStateOutcome` carries EITHER an `IntraState` value
   OR an unavailable reason token from the closed §7 STATE set — enforced in
   `__post_init__` (TradeDecision idiom, `trade_decision.py:45-88`).
3. **Freshness identity.** STATE and the `SpyObservation` freshness verdict are
   functions of the SAME frame object; STATE surfaces only under the freshness
   the observation reports (§6). Identity, not equality-checking.
4. **EVENT routing (RATIFIED 2026-08-07).** The card builder calls the existing
   pure loader `red_folder.load_schedule()` (`red_folder.py:91`, PRD-176,
   read-only import, UNMODIFIED) and resolves
   `events_in_window(run_at_utc, 48)` / `is_expiring(run_at_utc)`
   (`red_folder.py:52-66`) against the RUN time — deterministic, unlike the
   renderer's existing panel which resolves against render-time `now()`
   (`dashboard_renderer.py:3193-3211`). The two surfaces may legitimately
   differ when render time ≠ run time; each is truthful about its own instant.
   No new event persistence; the loader reads the existing static
   `data/red_folder_2026.json` (`red_folder.py:24`).
5. **Seven-field composition.** Each field is value-or-explicit-UNAVAILABLE with
   tokens drawn from the closed per-field vocabularies of §7, composed by the
   builder from: `SpyObservation` (LOCATION, freshness axis), `SpyStateOutcome`
   (STATE, TRANSITION), `system_state.permission` (PERMISSION), the resolved
   red-folder view (EVENT), `invalidation_guidance_map` + `outcome`
   (INVALIDATION), and `visibility_map` + `outcome` (CANDIDATE-IMPLICATION).

---

## 4. Sidecar contract

### 4.1 New dataclasses (transient — not a durable schema of their own)

- **`SpyStateOutcome`** (frozen; `cuttingboard/spy_state.py`): fields `state:
  Optional[IntraState]`, `unavailable_reason: Optional[str]`. Strict-XOR
  invariant enforced in `__post_init__`: rejects both populated; neither
  populated; `unavailable_reason` not in `VALID_SPY_STATE_UNAVAILABLE_REASONS`;
  `state` populated but not an `IntraState`. Pure validation, no
  derived-default backfill. The pre-09:45 engine `None` maps to the
  `pre_computation_window` token — `state=None, reason=None` is
  constructor-rejected.
- **`MarketControlCard`** (frozen, transient; projected dict mirror rides the
  payload additively, §8): seven fields, each a value-or-explicit-UNAVAILABLE
  cell. The composer validates every unavailable token against its field's
  frozenset and every value against its field's closed value set at
  construction; an unenumerated branch fails construction rather than
  rendering silence.

### 4.2 Payload projection

New keyword-only parameter after the existing ones:
`build_report_payload(contract, fixture_mode=False, *, spy_observation=None,
market_control_card=None)` — existing parameters retained verbatim (signature
pinned to `payload.py:24-29`). `sections["market_control_card"]` is a JSON-safe
plain-dict mirror, present iff the card is provided (daily path).

### 4.3 Schema / persistence classification

Transient dataclasses; NO decision-contract key, NO schema migration, NO
`PAYLOAD_SCHEMA_VERSION` bump, NO required-key change (verified:
`assert_valid_payload` accepts extra `sections` keys, §2.2). The projected
`sections["market_control_card"]` key appears additively in the schema-governed
`latest_payload.json` (cat-4/cat-1); §8 states that boundary precisely.

---

## 5. STATE acquisition and failure isolation (unchanged from v0.3)

**Scope.** The isolation boundary is the `spy_state.py` STATE-ACQUISITION seam
ONLY — the owned FRAME A → `list[Bar]` adapter plus the
`compute_intraday_state` call. It does NOT enclose `build_spy_observation`
(separate, unmodified producer that reads FRAME A first, `:1288`, and owns its
own defensive handling).

**Realizable inputs.** FRAME A's shape is guaranteed by the single
`fetch_intraday_session_bars("SPY")` contract (selects OHLCV columns,
`ingestion.py:231`; returns `None`/empty on failure, `:258-271`). Input states
this seam handles: well-formed frame, or `None`/empty. A present-but-malformed
frame is not producible by that fetch and is not claimed covered.

- **Resolve to typed UNAVAILABLE** (input-quality, per §7 STATE table):
  frame `None`/empty; adapter `KeyError`/`ValueError`/`TypeError`;
  `InsufficientDataError` (<5 ORB bars, engine `:132-137`); engine `ValueError`
  (empty / non-chronological / naive-timestamp bars, `:420-429`, `:114-117`).
  **Caught set, exactly:** `(KeyError, ValueError, TypeError,
  InsufficientDataError)`.
- **In-band, not via the exception path:** engine returns `None` before
  09:45 ET (`:435-436`) → `pre_computation_window`.
- **Propagate (programmer errors — fail loud at run level):** everything else.
  **No `except Exception`.** A propagated programmer error reaches
  `execute_run` → error contract → non-zero-visible failure (PRD-198 #1).
- **`previous_close` graceful degradation:** `None` is accepted by the engine
  (weaker gap-typing); it never makes STATE unavailable and MUST NOT trigger a
  new fetch.

**Doctrine reconciliation** (PRD-198 #1): a typed UNAVAILABLE with a validated
reason token on a read-only sidecar substitutes nothing and hides nothing;
collapsing the daily run for an input-quality failure at this seam would fail
loud at the wrong altitude. Programmer errors keep the exit-non-zero path.

---

## 6. Frame identity and freshness (unchanged from v0.3)

- **Identity, not equality.** STATE and freshness are functions of the SAME
  `spy_session_frame` object within one run; no second fetch exists to diverge.
- **Freshness coherence.** When `SpyObservation.state != OBSERVED`, STATE is
  presented as UNAVAILABLE with the §7 cascade token, never as a fresh value.
  Pinned by M13.
- `SpyObservation` remains the sole freshness authority (unmodified).
- **PERMISSION is explicitly OUTSIDE this coherence rule** (RATIFIED): it is
  produced independently of the SPY observation and remains valued under every
  observation state, including halt (§7).

---

## 7. Seven-field vocabulary — reachability tables, closed sets, closure proof

This section IS the 2026-08-07 producer→field reconciliation, encoded at packet
authority. Reason tokens are field-specific constants + a `VALID_*` frozenset
per field (the `execution_policy.py` / `invalidation.py` idiom), NOT one global
enum. LOCATION alone projects raw upstream tokens (it IS the observation
projection); every other field normalizes deterministically. The implementing
PRD has ZERO discretion anywhere in this section.

**Branch classes** used in every table below:
- **REACHABLE** — a current production path produces it.
- **DEFENSIVE-ONLY** — declared guard with no current input path
  (Author discipline #3); retained explicitly, never claimed active.
- **OWNER-DEFERRED** — exists only under a (declined/reversed) owner ruling;
  dormant after the 2026-08-07 ratifications.
- **UNREACHABLE / IMPOSSIBLE** — no producer branch can reach it; REMOVED from
  the vocabulary (listed for the record with the removal reason).

### 7.1 LOCATION — direct projection of `SpyObservation`

| Upstream outcome (spy_observation.py) | Class | Field result | Exact token/value |
|---|---|---|---|
| `halted=True` (`:83-85`) | REACHABLE | UNAVAILABLE | `system_halted` |
| `session_frame is None` (`:89-90`) | REACHABLE | UNAVAILABLE | `intraday_fetch_failed` (also fires when no fetch was attempted — fixture/Sunday; §17 A-1, out of scope) |
| frame < 1 bar (`:91-93`) | REACHABLE | UNAVAILABLE | `insufficient_bars` (empty-frame meaning; distinct from STATE's ORB-window token of the same name — see closure note) |
| other-session frame, now ≤09:35 ET (`:100-103`) | REACHABLE | PRE_OPEN | `pre_open_prior_session` |
| other-session frame, now >09:35 ET (`:104-105`) | REACHABLE | STALE | `session_mismatch` |
| same-session, now <09:30 ET (`:108-110`) | REACHABLE | PRE_OPEN | `pre_open` |
| same-session, age >180 s (`:111-114`) | REACHABLE | STALE | `observation_lag` |
| OBSERVED, volume >0 (`:116-126`) | REACHABLE | value | `price_vs_vwap ∈ {ABOVE, BELOW, AT_LEVEL}` + vwap + price; `reason=None` |
| OBSERVED, zero session volume (`:117-121`, `:154-165`) | REACHABLE (rare) | value with VWAP unavailable | field-specific `vwap_unavailable` (upstream literal: `price_vs_vwap="UNAVAILABLE"`) |
| ORB sub-object (`watch.py:407-505`), projected VERBATIM | REACHABLE | sub-axis | states `{PRE_OPEN, FORMING, FORMED, UNAVAILABLE, INVALID}`; reasons `{no_bars, unordered_bars, pre_open_prior_session, session_mismatch, mixed_session, formation_bars_absent, formation_incomplete, impossible_bounds}`; `reason=None` legal for PRE_OPEN/FORMING/FORMED; `orb=None` when SPY metrics absent |

```
VALID_LOCATION_STATES = frozenset({"OBSERVED", "PRE_OPEN", "STALE",
                                   "UNAVAILABLE"})
VALID_LOCATION_PRICE_VS_VWAP = frozenset({"ABOVE", "BELOW", "AT_LEVEL"})
    # valued (OBSERVED, volume > 0) observations only; the zero-volume case
    # normalizes to the reason token "vwap_unavailable" below, and the raw
    # upstream literal price_vs_vwap="UNAVAILABLE" never renders as a value.
VALID_LOCATION_REASONS = frozenset({
    "system_halted", "intraday_fetch_failed", "insufficient_bars",
    "pre_open_prior_session", "session_mismatch", "pre_open",
    "observation_lag", "vwap_unavailable",
})
    # renamed from v0.4-initial VALID_LOCATION_UNAVAILABLE_REASONS (F2):
    # pre_open / pre_open_prior_session / session_mismatch / observation_lag
    # accompany the PRE_OPEN and STALE states, which are non-current but NOT
    # UNAVAILABLE — the old name mislabeled them.
VALID_LOCATION_ORB_STATES  = frozenset({"PRE_OPEN", "FORMING", "FORMED",
                                        "UNAVAILABLE", "INVALID"})
VALID_LOCATION_ORB_REASONS = frozenset({"no_bars", "unordered_bars",
    "pre_open_prior_session", "session_mismatch", "mixed_session",
    "formation_bars_absent", "formation_incomplete", "impossible_bounds"})
```

Composer validation for LOCATION (zero discretion, per §4.1): `state` must be a
member of `VALID_LOCATION_STATES`; `reason` must be `None` (legal exactly for
`OBSERVED`) or a member of `VALID_LOCATION_REASONS` keyed by state per the table
above; a valued observation's `price_vs_vwap` must be a member of
`VALID_LOCATION_PRICE_VS_VWAP` or normalize to `vwap_unavailable`; the ORB
sub-object validates against the two ORB sets (its `reason=None` is legal for
`PRE_OPEN`/`FORMING`/`FORMED`).

Closure: the observation's four-state axis IS the closed value contract and
fully partitions its reason space; all seven raw reasons + the field-specific
`vwap_unavailable` are enumerated; the ORB sub-axis (previously unenumerated —
a v0.3 gap) is closed at packet authority. `insufficient_bars` appears in both
LOCATION and STATE sets with different meanings (empty frame vs <5 ORB bars);
the sets are per-field namespaces and never mix, and the collision is called
out here so no reviewer reads them as one condition.

### 7.2 STATE — `SpyStateOutcome` from FRAME A

| Upstream outcome | Class | Field result | Exact token/value |
|---|---|---|---|
| engine returns `IntraState` (`intraday_state_engine.py:512-534`) | REACHABLE | value | `state ∈ {EXPANSION_CONFIRMED, FAILED_EXPANSION, RANGE}` (`:479-492`) |
| observation `PRE_OPEN` / `STALE` | REACHABLE | UNAVAILABLE (cascade) | `non_current_observation` |
| observation `UNAVAILABLE` (halt / `None`/empty frame) | REACHABLE | UNAVAILABLE | `observation_unavailable` — frame-`None`/empty and observation-UNAVAILABLE are the SAME world (`spy_observation.py:89-93`); one token, deliberately |
| engine `None` — run between 09:30 and 09:45 ET with an OBSERVED frame (`:435-436`) | REACHABLE | UNAVAILABLE | `pre_computation_window` (in-band) |
| `InsufficientDataError` — ≥09:45 with <5 ORB bars (`:132-137`) | REACHABLE (provider data gap) | UNAVAILABLE | `insufficient_bars` |
| adapter `KeyError`/`ValueError`/`TypeError`; engine `ValueError` (`:420-429`) | DEFENSIVE-ONLY (fetch contract precludes a malformed present frame; §5) | UNAVAILABLE | `state_computation_error` |
| any other exception (`AttributeError`, …) | REACHABLE (programmer defect) | PROPAGATE — fail loud | — |
| `previous_close=None` (`runtime/__init__.py:1594-1600`) | REACHABLE | value (weaker gap-typing) | never unavailability |

```
VALID_SPY_STATE_UNAVAILABLE_REASONS = frozenset({
    "insufficient_bars", "pre_computation_window", "state_computation_error",
    "non_current_observation", "observation_unavailable",
})
VALID_SPY_STATE_VALUES = frozenset({"EXPANSION_CONFIRMED", "FAILED_EXPANSION",
                                    "RANGE"})
```

Shared-observation normalization (STATE only — PERMISSION removed from this
table by ratified ruling):

| `SpyObservation.state` | member reasons | → STATE token |
|---|---|---|
| `OBSERVED` | — | STATE computed; else the acquisition-seam token (`insufficient_bars` / `pre_computation_window` / `state_computation_error`) |
| `PRE_OPEN` | `pre_open`, `pre_open_prior_session` | `non_current_observation` |
| `STALE` | `session_mismatch`, `observation_lag` | `non_current_observation` |
| `UNAVAILABLE` | `system_halted`, `intraday_fetch_failed`, `insufficient_bars` | `observation_unavailable` |

Closure: unchanged from v0.3 and re-demonstrated against code — every branch of
the four-state axis and every seam outcome maps to exactly one member; STATE
never emits a raw observation token.

### 7.3 PERMISSION — direct projection of `system_state.permission` (RATIFIED)

**`system_state.permission` is a TOTAL producer.** It is injected at contract
finalization (`runtime/__init__.py:855-860`) as
`_PERMISSION_LINES.get(posture, "No new trades permitted.")` with a halt
override; `_summary_regime_fields(None)` → `("NEUTRAL", "STAY_FLAT", 0.0, 0)`
(`:2350-2353`); `assert_valid_contract(finalized=True)` requires the key
(`contract.py:627`). It is already rendered today via `payload.summary.permission`
(`payload.py:47-49`, `:151-153`). It does not read the SPY observation anywhere.

| Upstream outcome | Class | Field result | Exact value |
|---|---|---|---|
| posture ∈ the 6 `VALID_POSTURES` (`runtime/_constants.py:61-68`) | REACHABLE | value | the 6 literal `_PERMISSION_LINES` strings (`:81-87`) |
| `regime is None` | REACHABLE | value | `"No new trades permitted."` (STAY_FLAT) |
| posture ∉ map | UNREACHABLE in practice (posture produced only from the validated set); `.get` default exists | value | `"No new trades permitted."` (byte-identical to STAY_FLAT — §17 A-3, out of scope) |
| halt (incl. kill-switch escalation) | REACHABLE | value | `"No trades permitted. System halted."` |
| source absent / indeterminate | **UNREACHABLE / IMPOSSIBLE** | — | — |

```
VALID_PERMISSION_VALUES = frozenset({
    "Long bias — trend continuation allowed.",
    "Long bias — defined risk preferred.",
    "Short bias — breakdown trades allowed.",
    "Selective only — defined risk, R:R >= 3:1.",
    "No new trades permitted.",
    "EXPANSION — momentum allowed. Continuation entries. R:R >= 1.5.",
    "No trades permitted. System halted.",
})
VALID_PERMISSION_UNAVAILABLE_REASONS = frozenset()   # EMPTY — total producer
```

**Removed as UNREACHABLE / IMPOSSIBLE (ratified):** `permission_state_absent`,
`permission_uncomputable`, and the entire SPY-observation coupling
(`observation_unavailable`) that v0.3 carried. On halt the producer emits a
truthful VALUED line; v0.3's normalization row would have discarded it and
manufactured unavailability. PERMISSION has no unavailable branch, and the card
projects the line verbatim.

Closure: seven literal strings enumerate the producer's entire range (the
STAY_FLAT line and the `.get` default are the same string); the unavailable set
is empty because no unavailable branch exists.

### 7.4 EVENT — routed from `red_folder.load_schedule()` (RATIFIED)

Producer: `red_folder.py` (PRD-176) — pure, read-only loader of the static
`data/red_folder_2026.json` schedule of macro-risk events (CPI/PPI/NFP/FOMC).
`RedFolderResult` (`:45-66`): `ok`, `events`, `error`, `last_event_date`;
`events_in_window(now_utc, lookahead_hours=48)`; `is_expiring(now_utc)`. The
card builder resolves against `run_at_utc` (§3.4). v0.3's claim that EVENT had
"no truthful producer today" was factually false — this producer is live on the
dashboard now, renderer-side (`dashboard_renderer.py:2719-2739`, `:3193-3211`).

| Upstream outcome | Class | Field result | Exact token/value |
|---|---|---|---|
| `ok=True`, ≥1 event in the 48 h window | REACHABLE | value | the event list, each `{date, time_et, type, name}` projected verbatim |
| `ok=True`, zero events in window | REACHABLE | truthful value — NOT unavailable | `no_scheduled_events` |
| `ok=False` (missing / malformed / invalid / expired-format file, `:69-70`) | REACHABLE | UNAVAILABLE | `event_schedule_unavailable` — the free-form loader `error` string is NOT projected into the card (open text cannot enter a closed vocabulary; log-only) |
| `is_expiring(run_at_utc)=True` | REACHABLE | boolean modifier | `expiring: true` — a flag on the field, never a token |
| producer absent | **UNREACHABLE / IMPOSSIBLE** after routing | — | v0.3's `no_truthful_producer` token is removed |

```
VALID_EVENT_UNAVAILABLE_REASONS = frozenset({"event_schedule_unavailable"})
# Values: the projected event list, or the literal value "no_scheduled_events".
# "expiring" is a boolean modifier, not a vocabulary member.
```

Distinction demonstrated in code: "no event" vs "unavailable" are distinct
(`ok` flag); "empty event set" ≡ "no events in window" (a single condition, one
token); "producer absent" was an altitude statement about routing, retired by
this ratified routing. No new event persistence exists or is introduced.

### 7.5 TRANSITION — bounded SAME-RUN definition (RATIFIED)

Sourced exclusively from fields the engine already computes on FRAME A
(`intraday_state_engine.py:63-88`): `orb_break_direction ∈ {"LONG", "SHORT",
None}`, `holding_bars: int`, `reclaimed_orb: bool`, `failed_reclaim: bool`,
`permission_state ∈ {IDLE, BREAK_ONLY, HOLD_CONFIRMED, FAILURE_CONFIRMED}`
(`confirmation.py:11-14`), `phase ∈ {OPEN, EARLY, POST_OPEN}`. **No prior-run
persistence is required or permitted** (hard stop §14.6). The renderer-side
previous-run mechanism (`dashboard_renderer.py:3237`) is renderer-altitude and
is NOT used — §2.3 forbids renderer derivation.

Deterministic value derivation (precedence order, first match wins):

| Precedence | Condition on valued `IntraState` | Class | Exact value |
|---|---|---|---|
| 1 | `permission_state == FAILURE_CONFIRMED` | REACHABLE | `FAILED_EXPANSION` |
| 2 | `failed_reclaim == True` | REACHABLE | `FAILED_RECLAIM` |
| 3 | `reclaimed_orb == True` | REACHABLE | `ORB_RECLAIMED` |
| 4 | `orb_break_direction == "LONG"` | REACHABLE | `ORB_BREAK_HOLDING_LONG` |
| 5 | `orb_break_direction == "SHORT"` | REACHABLE | `ORB_BREAK_HOLDING_SHORT` |
| 6 | no break (`orb_break_direction is None`) | REACHABLE | `NO_BREAK` |
| — | STATE unavailable (any §7.2 token) | REACHABLE | UNAVAILABLE: `transition_state_unavailable` (cascade) |
| — | same-run ruling reversed by a later owner ruling | OWNER-DEFERRED (dormant) | UNAVAILABLE: `transition_deferred` |

```
VALID_TRANSITION_VALUES = frozenset({"NO_BREAK", "ORB_BREAK_HOLDING_LONG",
    "ORB_BREAK_HOLDING_SHORT", "ORB_RECLAIMED", "FAILED_RECLAIM",
    "FAILED_EXPANSION"})
VALID_TRANSITION_UNAVAILABLE_REASONS = frozenset({
    "transition_state_unavailable", "transition_deferred",
})
```

**Removed as duplicate-meaning (ratified):** v0.3's `no_truthful_producer` — a
truthful same-run producer exists, and the token duplicated
`transition_deferred`. Closure: every valued `IntraState` matches exactly one
precedence row (row 6 is the total fallback for `None` direction); every
unavailable STATE cascades to exactly one token.

### 7.6 INVALIDATION — bounded rollup over `invalidation_guidance_map` (RATIFIED)

Producer semantics, traced exactly (`invalidation.py`): statuses
`{NOT_TRIGGERED, WARNING, TRIGGERED, UNKNOWN}` (`:15-20`), actions (`:23-29`);
guidance reasons are an OPEN axis — two branches emit unbounded f-string
interpolations (`:87`, `:104`) and two emit the literal
`"INSUFFICIENT_DETERMINISTIC_INPUTS"` (`:59-66`, `:119-126`). The map gains
entries ONLY for decisions still `ALLOW_TRADE` at the gate (`:147-154`);
single production caller `runtime/__init__.py:753`, immediately after
`apply_thesis_gate` (`:746-752`).

**Reachability proof (the decisive v0.4 correction).** The thesis gate writes a
thesis for every ALLOW decision and blocks every `INCOMPLETE`/`CONFLICTED` one
(`trade_thesis.py:151-192`); `build_thesis` classifies exactly the
`_MACRO_CONFLICTED` pairs (`:28-29`, `:113-115`) that the invalidation gate's
pressure check tests (`invalidation.py:93-107`); surviving theses have
`status ∈ {VALID, UNKNOWN}` and `block_reason=None` (`:110-121`). Therefore at
the invalidation gate: `thesis is None` is impossible; TRIGGERED is impossible;
both WARNING branches are impossible; the status-fallback requires a status
outside the closed `_VALID_STATUSES` frozenset (`trade_thesis.py:26`) —
impossible. **Every production map entry is
`NOT_TRIGGERED / HOLD_OK / reason=None`.** The gate's non-trivial surface is
dead under current routing (§17 A-2, out of scope for NS-2E).

| Upstream outcome | Class | Field result | Exact token/value |
|---|---|---|---|
| map has entries, all `NOT_TRIGGERED` | REACHABLE (the only populated case today) | value | `NOT_TRIGGERED` |
| an entry with `WARNING` | DEFENSIVE-ONLY (dead under current routing) | value | `WARNING` |
| an entry with `TRIGGERED` | DEFENSIVE-ONLY (dead; a TRIGGERED guidance is written to the map before the block conversion, `invalidation.py:154-169`) | value | `TRIGGERED` |
| an entry with `UNKNOWN` (upstream reason `INSUFFICIENT_DETERMINISTIC_INPUTS`) | DEFENSIVE-ONLY (dead) | UNAVAILABLE | `invalidation_indeterminate` — the upstream status is NORMALIZED; the raw reason string is NEVER projected (RATIFIED; the open reason axis cannot enter a closed vocabulary) |
| map `{}`, outcome ≠ `HALT` (eligible run, §1) | REACHABLE | truthful value — NOT unavailable | `NO_ACTIVE_CANDIDATES` (on an eligible non-halt run the gate chain executed — vacuously when zero setups exist, `runtime/__init__.py:1105-1123`, `:701-705` — and no candidate was in scope; `MODE_SUNDAY`, where the chain is skipped wholesale, produces no card at all, §1/F1) |
| map `{}`, outcome = `HALT` | REACHABLE | UNAVAILABLE | `invalidation_inputs_absent` (gates never ran; `runtime/__init__.py:983-989`) |
| per-symbol absent (symbol without an ALLOW decision) | REACHABLE | excluded from the run-level rollup | — (the contract already renders per-symbol `None`, `contract.py:374`; not a card token) |
| D-2 declined by a later owner ruling | OWNER-DEFERRED (dormant) | UNAVAILABLE | `invalidation_deferred_d2` |

```
VALID_INVALIDATION_VALUES = frozenset({"NOT_TRIGGERED", "WARNING", "TRIGGERED",
                                       "NO_ACTIVE_CANDIDATES"})
# WARNING / TRIGGERED are DEFENSIVE-ONLY, declared, never claimed active.
VALID_INVALIDATION_UNAVAILABLE_REASONS = frozenset({
    "invalidation_deferred_d2", "invalidation_inputs_absent",
    "invalidation_indeterminate",
})
```

**Mixed-status aggregate precedence (F4, ruled 2026-08-07 — the implementing
PRD has ZERO discretion).** For a non-empty map, the single field result derives
from the highest-severity entry status under the strict order:

```
TRIGGERED > WARNING > UNKNOWN (→ invalidation_indeterminate) > NOT_TRIGGERED
```

i.e. any `TRIGGERED` entry → value `TRIGGERED`; else any `WARNING` → `WARNING`;
else any `UNKNOWN` → UNAVAILABLE `invalidation_indeterminate`; else →
`NOT_TRIGGERED`. Mixed maps are DEFENSIVE-ONLY like their member branches
(current routing produces uniform `NOT_TRIGGERED`), but the rule is total over
every combination of the 4-member status axis. Pinned by M24.

Closure: the producer's closed axis is the 4-member STATUS set; each member maps
to exactly one card value/token, and the F4 precedence makes the rollup total
and deterministic over every multi-entry combination; the two `{}` worlds are
split deterministically by `outcome` on eligible runs (RATIFIED — non-halt
empty is a truthful empty, halt empty is absent inputs; `MODE_SUNDAY` produces
no card, §1); no raw reason string can reach the card.

### 7.7 CANDIDATE-IMPLICATION — rollup over `visibility_map` + `outcome` (RATIFIED)

Producers: `build_visibility_map(trade_decisions, market_map)`
(`trade_visibility.py:31-70`; statuses `{ACTIVE, NEAR_MISS, BLOCKED}` `:17-19`;
one entry per TradeDecision; call site `runtime/__init__.py:1140`, common path
incl. halt) and the run `outcome` (`TRADE`/`NO_TRADE`/`HALT`,
`output.py:232-234`; derivation `:766-774`, halt `:1000`/`:1016`). Both inputs
are TOTAL at the boundary: `PipelineResult.outcome` is a non-optional `str`
(`runtime/_types.py:75`) and `visibility_map` a defaulted dict (`:88`).

| Upstream outcome | Class | Field result | Exact token/value |
|---|---|---|---|
| `outcome=TRADE` (≥1 actionable decision) | REACHABLE | value | `ACTIONABLE_CANDIDATES` (+ ACTIVE/NEAR_MISS/BLOCKED counts) |
| `outcome=NO_TRADE`, map non-empty | REACHABLE | value | `CANDIDATES_PRESENT_NONE_ACTIONABLE` (+ ACTIVE/NEAR_MISS/BLOCKED counts) — truthful cover-all (F3, ruled 2026-08-07): candidates exist and none is actionable, whether BLOCKED, NEAR_MISS, or ACTIVE-but-non-actionable (a policy-allowed NON_TRADABLE symbol is `ACTIVE` in the map yet excluded from actionability, `trade_visibility.py:47-52`, `runtime/__init__.py:766-774`); the retired label `CANDIDATES_BLOCKED_OR_NEAR_MISS` was false for the reachable ACTIVE-only map |
| `outcome=NO_TRADE`, map `{}` (eligible run, §1) | REACHABLE | truthful value — NOT unavailable | `NO_CANDIDATES` (`MODE_SUNDAY` produces no card at all, §1/F1) |
| `outcome=HALT` (map always `{}` — gates skipped) | REACHABLE | UNAVAILABLE | `candidate_inputs_absent` |
| inputs absent/`None` at the boundary | **UNREACHABLE / IMPOSSIBLE** | — | v0.3's `candidate_implication_uncomposable` is removed (RATIFIED) — it contradicted v0.3's own §9 verification that these inputs are never absent |
| per-symbol absent (no decision for a symbol) | REACHABLE | excluded from rollup | — (distinct from the empty map; not a card token) |
| D-3 declined by a later owner ruling | OWNER-DEFERRED (dormant) | UNAVAILABLE | `candidate_implication_deferred_d3` |

```
VALID_CANDIDATE_IMPLICATION_VALUES = frozenset({"ACTIONABLE_CANDIDATES",
    "CANDIDATES_PRESENT_NONE_ACTIONABLE", "NO_CANDIDATES"})
VALID_CANDIDATE_IMPLICATION_UNAVAILABLE_REASONS = frozenset({
    "candidate_implication_deferred_d3", "candidate_inputs_absent",
})
```

Closure: over eligible runs (§1), `(outcome, map-emptiness)` has six
combinations; `TRADE` with an empty map is impossible (an actionable decision
implies a map entry), `HALT` with a non-empty map is impossible (gates skipped
⇒ no decisions); the four possible combinations map to exactly one value/token
each, and `CANDIDATES_PRESENT_NONE_ACTIONABLE` is truthful over every
non-actionable status mix including the ACTIVE-only map (F3).

### 7.8 Closure demonstration — summary

All §7 mappings are defined over ELIGIBLE runs (§1); `MODE_SUNDAY` produces no
card and therefore consumes no vocabulary (F1). For each field: every REACHABLE
branch in §7.1–§7.7 maps to exactly one member of that field's value set or
unavailable frozenset (LOCATION's value contract closed per F2; the
CANDIDATE-IMPLICATION non-actionable value truthful per F3; the INVALIDATION
mixed-map rollup total per F4); every DEFENSIVE-ONLY and OWNER-DEFERRED member
is explicitly declared as such; every UNREACHABLE token from v0.3 is removed,
not silently kept (`permission_state_absent`,
`permission_uncomputable`, PERMISSION `observation_unavailable`,
`candidate_implication_uncomposable`, TRANSITION `no_truthful_producer`,
EVENT `no_truthful_producer`). No raw upstream reason string enters any closed
set except LOCATION's deliberate raw projection. The carrier/composer rejects
any token outside its field's set at construction, so an unenumerated branch
fails construction rather than rendering silence.

---

## 8. Persistence vocabulary (unchanged from v0.3; EVENT read noted)

Output classification (verified `transport.py:15-16`,
`dashboard_renderer.py:54-56`, `runtime/__init__.py:2282-2295`):

1. **PRESENTATION** — `logs/latest_payload.json`, `reports/output/report.html`,
   `reports/output/dashboard.html`, `reports/{date}.md`.
2. **DURABLE OBSERVATION/CACHE** — `logs/market_map.json`,
   `logs/macro_drivers_snapshot.json`, `logs/trend_structure_snapshot.json`,
   `logs/performance_summary.json`, OHLCV cache.
3. **DECISION/AUDIT** — `logs/latest_contract.json`, `logs/audit.jsonl`,
   `logs/evaluation.jsonl`.
4. **SCHEMA-GOVERNED** — `logs/latest_payload.json`, `logs/market_map.json`,
   `logs/latest_contract.json`.

**Truthful boundary:** the card appears in cat-1 presentation outputs — the
additive optional `sections["market_control_card"]` key in the cat-4/cat-1
`latest_payload.json` (required-key contract and `PAYLOAD_SCHEMA_VERSION`
unchanged) and a rendered `dashboard.html` block. The other cat-4 artifacts and
all cat-3 artifacts are untouched. NO new cat-2 writes; NO new durable
persistence SURFACE. **EVENT adds a READ only:** the existing static
`data/red_folder_2026.json` via the existing pure loader — no event
persistence, no schedule write, no new file. v0.2's retracted absolute claim
("durable artifacts byte-for-byte unchanged") stays retracted and is not
restated.

---

## 9. Candidate inputs (verified)

- Builder receives as parameters: `visibility_map` (`:1140`), the run-level
  `outcome`, and `invalidation_guidance_map` (from `_run_decision_gates`,
  `:1105-1123`; defaults `:983-989` on skipped-gate paths). Today none reach
  any card builder. `outcome` is a NON-optional `str`;
  `visibility_map`/`invalidation_guidance_map` use empty `{}` = absent (never
  `None` at the boundary — `_PartialPipelineResult`'s `Optional` defaults,
  `runtime/_types.py:50-52`, are always overridden by the production call,
  `:842-845`).
- Renderer never derives either field; the builder is sole producer.

---

## 10. Presentation surface

The card renders in **`logs/latest_payload.json` (mirror) +
`reports/output/dashboard.html` only** — NOT `report.html` (verified:
`html_renderer` does not read `sections["spy_observation"]` today; adding the
card there is extra surface for no product need). R3 carried forward as
recommended (§16). The existing renderer-side red-folder panel
(`dashboard_renderer.py:2719-2739`) is untouched; the card's EVENT field is the
run-time-keyed view (§3.4).

---

## 11. Exact likely files (ESTIMATED SURFACE — NOT YET APPROVED)

| Op | File | Purpose |
|---|---|---|
| A | `cuttingboard/spy_state.py` (new) | `SpyStateOutcome` + `VALID_SPY_STATE_UNAVAILABLE_REASONS`; owned FRAME A→`list[Bar]` adapter; `build_spy_state_outcome`; the §5 isolation boundary |
| A | `cuttingboard/market_control_card.py` (new) | `MarketControlCard`, the six other `VALID_*` sets, the seven-field composer (sole producer), the red-folder run-time resolution (§3.4) |
| M | `cuttingboard/runtime/__init__.py` | call `build_spy_state_outcome` with the existing `spy_session_frame` + SPY `previous_close`; build the card on ELIGIBLE runs only (`MODE_LIVE`/`MODE_FIXTURE`, §1 — never `MODE_SUNDAY`); set `PipelineResult.market_control_card`; forward to the daily `build_report_payload`; hourly untouched |
| M | `cuttingboard/runtime/_types.py` | one optional `market_control_card` field on `PipelineResult` (mirrors `spy_observation` @ `:92`) |
| M | `cuttingboard/delivery/payload.py` | keyword-only `market_control_card` param + `sections["market_control_card"]` projection |
| M | `cuttingboard/delivery/dashboard_renderer.py` | one card block, present iff section present (precedent `:2538-2556`) |

**Deliberately NOT in FILES:** `cuttingboard/spy_observation.py`,
`cuttingboard/intraday_state_engine.py`, and `cuttingboard/red_folder.py` are
READ-ONLY imports. Touching any of the three is a §14 stop-and-amend event.

Test files: new `tests/test_spy_state.py`, `tests/test_market_control_card.py`;
bounded edits to `tests/test_runtime_decision.py`, `tests/test_payload.py`,
`tests/test_dashboard_renderer.py`. PRD-158 sweep: this change deletes/renames
no rendered token; a sweep over `market_control_card`, `SpyStateOutcome`, and
the §7 tokens adds no further asserting test files.

---

## 12. Estimated production LOC ceiling (ESTIMATED SURFACE — NOT YET APPROVED)

Governing metric: net production LOC via `git diff --numstat` across the
authorized production files; test LOC uncounted.

- **~+170–260 net production LOC; provisional ceiling ≤300.** The STATE spine
  (`spy_state.py` + carrier + isolation) is ~130–190 (unchanged from v0.3); the
  seven-field composer + EVENT resolution + payload/renderer plumbing adds the
  remainder. Non-binding; first binding ceiling is Gate A.
- **Stop-and-amend tripwire:** any production file beyond §11, any change to the
  three excluded producers, any persistence/schema/decision-contract touch, or
  any second SPY fetch → §14.

---

## 13. Discriminating test / mutation matrix (M-suffix = reddening mutation required)

M1–M12 and M14 carry over from v0.3 unchanged; M13 is REVISED; M15–M22 are new
and pin the corrected producer semantics.

| # | Case | Asserted | Mut? |
|---|---|---|---|
| M1 | Same-frame identity | STATE derived from the exact object passed to `build_spy_observation`; discriminating fixture where full-session vs tail-120 frame yield different STATE | **YES** |
| M2 | Single fetch | exactly one `fetch_intraday_session_bars("SPY")` feeds both observation and STATE | **YES** |
| M3 | Fetch `None`/empty FRAME A | observation UNAVAILABLE AND carrier `observation_unavailable`; daily run NOT ERROR | |
| M4 | Adapter data-shape failure at the seam (missing OHLCV column) | typed UNAVAILABLE `state_computation_error` (unit-level) | **YES** |
| M5 | Adapter ValueError at the seam | typed UNAVAILABLE | |
| M6 | `InsufficientDataError` (<5 ORB bars) | typed UNAVAILABLE `insufficient_bars` | |
| M7 | Pre-09:45 engine `None` | `pre_computation_window` — distinct from error tokens | |
| M8 | Injected `AttributeError` in the engine call | PROPAGATES to run level — no blanket catch | **YES** |
| M9 | XOR both / neither populated | `SpyStateOutcome.__post_init__` raises both ways | **YES** |
| M10 | Unknown reason token (any field's carrier/composer cell) | constructor raises | **YES** |
| M11 | Persistence truth | card present in redirected `latest_payload.json` + rendered `dashboard.html`; redirected `audit.jsonl` and `latest_contract.json` byte-unchanged | |
| M12 | Additive-only e2e | `_run_pipeline(mode=MODE_FIXTURE)`: outcome/halt/decision fields pinned unchanged while card section present | |
| M13 | Freshness coherence (REVISED) | `STALE`/`PRE_OPEN` observation → STATE `non_current_observation`; observation `UNAVAILABLE` (halt) → STATE `observation_unavailable`; **PERMISSION remains VALUED in every one of those cases, including the halt line verbatim** | **YES** — re-adding the v0.3 PERMISSION coupling (normalizing PERMISSION to unavailable on any observation state) reddens |
| M14 | Halt path | `halted=True` → observation + carrier unavailable; no fetch, no engine call attempted | |
| M15 | EVENT valued | schedule fixture with events inside `run_at_utc`+48 h → valued event list; window math keyed on `run_at_utc`, not wall-clock | **YES** — switching the builder to `datetime.now()` reddens (fixture pins a run time where they differ) |
| M16 | EVENT truthful empty | `ok=True`, empty window → value `no_scheduled_events`, NOT an unavailable token | |
| M17 | EVENT unavailable | missing/malformed schedule file → `event_schedule_unavailable`; the loader's free-form `error` string does NOT appear anywhere in the card cell | **YES** — projecting the raw error string reddens |
| M18 | PERMISSION total projection | halt fixture → card PERMISSION is the literal halt line; non-halt fixture → the exact posture line; no unavailable branch exists in the composer | **YES** — mapping halt to an unavailable token reddens |
| M19 | INVALIDATION empty-map split | non-halt `{}` → value `NO_ACTIVE_CANDIDATES`; halt `{}` → `invalidation_inputs_absent` | **YES** — merging the two worlds reddens |
| M20 | CANDIDATE-IMPLICATION split | non-halt `{}` → `NO_CANDIDATES`; halt → `candidate_inputs_absent`; NO_TRADE + non-empty map → `CANDIDATES_PRESENT_NONE_ACTIONABLE`, including a discriminating ACTIVE-only fixture (policy-allowed NON_TRADABLE symbol) proving the value is truthful when nothing is blocked or near-miss (F3) | **YES** |
| M21 | INVALIDATION normalization | constructed guidance entry with `status=UNKNOWN`, `reason="INSUFFICIENT_DETERMINISTIC_INPUTS"` → card shows `invalidation_indeterminate`; the raw upstream string appears nowhere in the card | **YES** — projecting the raw token reddens (the exact PR #226 terminal defect, pinned forever) |
| M22 | TRANSITION derivation + cascade | precedence pinned (`FAILURE_CONFIRMED` > `failed_reclaim` > `reclaimed_orb` > break-direction > `NO_BREAK`) with one fixture per row; STATE-unavailable → `transition_state_unavailable` | **YES** — reordering precedence reddens |
| M23 | Sunday absence (F1) | `_run_pipeline(mode=MODE_SUNDAY)`: `PipelineResult.market_control_card is None`, `sections["market_control_card"]` absent from the payload, and no card block in the rendered dashboard | **YES** — producing the card on Sunday reddens |
| M24 | INVALIDATION mixed-status precedence (F4; fixture matrix completed per the owner-authorized P2 micro-correction, 2026-08-07) | constructed non-empty maps: {TRIGGERED, WARNING} → `TRIGGERED`; {TRIGGERED, UNKNOWN} → `TRIGGERED`; {WARNING, UNKNOWN} → `WARNING`; {WARNING, NOT_TRIGGERED} → `WARNING`; {UNKNOWN, NOT_TRIGGERED} → `invalidation_indeterminate`; uniform NOT_TRIGGERED → `NOT_TRIGGERED`. The matrix pairs every adjacent and skip-level status, so it is discriminating for the complete stated total order — e.g. a wrong `TRIGGERED > UNKNOWN > WARNING > NOT_TRIGGERED` ordering fails the {WARNING, UNKNOWN} fixture | **YES** — reordering the severity precedence reddens |

Reuse `_utc_frame` (`test_spy_observation.py:27-33`) for DataFrame fixtures and
the ET `_bar/_orb_bars/_noise_bars` builders (`test_intraday_state.py`) for Bar
fixtures; red-folder fixtures via a temp schedule path (the loader takes an
explicit `path`). Payload gate via `assert_valid_payload` with/without the
section; dashboard via targeted substring presence/absence — NO golden-file
byte-diff. A guard whose mutation leaves all tests green is not a guard and
does not merge.

---

## 14. Stop-and-amend conditions (hard stops — return to Dustin, re-run GOV-2 §1)

1. Any change to `intraday_state_engine.py`, `spy_observation.py`, or
   `red_folder.py` beyond read-only import.
2. Any required-key addition to `assert_valid_payload` or any
   `PAYLOAD_SCHEMA_VERSION` bump.
3. Any SPY fetch beyond the existing single `fetch_intraday_session_bars("SPY")`.
4. Any NEW durable persistence SURFACE for the card or the event read; any write
   to a cat-2 or cat-3 artifact; any change to a cat-4 artifact's
   `PAYLOAD_SCHEMA_VERSION` or required-key contract. (The additive optional
   `sections["market_control_card"]` key is the intended behavior, §8.)
5. The hourly path consuming `sections["market_control_card"]`.
6. TRANSITION requiring persisted prior-run state.
7. Any decision-contract change.
8. Any Market Map removal/refactor in this slice.
9. Exceeding the §11 file surface or the §12 ceiling without a fresh GOV-2 §1
   classification.
10. Renderer-side derivation of any card value.
11. Any wall-clock (`datetime.now()`) dependence inside the builder — all card
    time logic is keyed on `run_at_utc` (§2.3, §3.4).
12. Any raw upstream free-form string (invalidation reasons, red-folder `error`)
    entering a card cell — open axes never enter closed vocabularies (§7.6,
    §7.4).

---

## 15. Materiality / lane classification

**MATERIAL** under GOV-2 §1: new cross-layer seam (runtime → transient carrier →
payload → renderer), new modules `spy_state.py` / `market_control_card.py`, new
dataclasses. The ratified EVENT routing adds a read-only consumer of an
existing pure loader and static file — no new materiality trigger (no new
consumer OF the card, no schema-version/required-key change, no new persistence
surface). Lane: STANDARD minimum (MICRO-ineligible). After this packet is
review-clean and Dustin issues a design-direction ruling, a fresh PRD →
independent PRD review → Gate A sequence is required before implementation.

---

## 16. Owner rulings

### RATIFIED (Dustin, 2026-08-07, in the v0.4 authorization — binding on this packet)

- **EVENT** — route the existing red-folder schedule result into the card
  builder as a read-only input; distinguish valued events /
  `no_scheduled_events` (truthful value) / `event_schedule_unavailable`
  (load failure); `expiring` remains a boolean modifier; no new event
  persistence. (§7.4, §3.4)
- **INVALIDATION** — non-halt empty map = truthful `NO_ACTIVE_CANDIDATES`; halt
  empty map = `invalidation_inputs_absent`; producer `STATUS_UNKNOWN`
  normalizes to `invalidation_indeterminate`; the open/free-form upstream
  reason strings are never projected into the closed card vocabulary. (§7.6)
- **CANDIDATE-IMPLICATION** — non-halt empty map = truthful `NO_CANDIDATES`;
  halt empty map = `candidate_inputs_absent`;
  `candidate_implication_uncomposable` removed as unreachable. (§7.7)
- **PERMISSION** — direct projection of `system_state.permission`; a total
  producer with no unavailable branch; `permission_state_absent`,
  `permission_uncomputable`, and the SPY-observation coupling removed. (§7.3)
- **TRANSITION** — the bounded same-run definition with values `NO_BREAK`,
  `ORB_BREAK_HOLDING_LONG`, `ORB_BREAK_HOLDING_SHORT`, `ORB_RECLAIMED`,
  `FAILED_RECLAIM`, `FAILED_EXPANSION`; unavailable tokens exactly
  `transition_state_unavailable`, `transition_deferred`; no prior-run
  persistence. (§7.5)
- **LOCATION** — retain the direct `SpyObservation` projection and explicitly
  enumerate the ORB sub-axis states/reasons. (§7.1)
- **STATE** — retain the already-validated closed vocabulary unchanged:
  `insufficient_bars`, `pre_computation_window`, `state_computation_error`,
  `non_current_observation`, `observation_unavailable`. (§7.2)

### RATIFIED (Dustin, 2026-08-07, authorizing the single GOV-1 consolidated correction — findings F1–F4 of the initial packet review, §18)

- **F1 — Sunday exclusion:** the card is not produced/rendered for
  `MODE_SUNDAY` runs; no Sunday-specific unavailable token; the truthful-empty
  mappings apply only to eligible non-Sunday daily runs where the
  candidate/gate path is actually in scope. (§1, §2.3, §7.6, §7.7; M23)
- **F2 — LOCATION closure:** `VALID_LOCATION_STATES` and
  `VALID_LOCATION_PRICE_VS_VWAP` added; the reason vocabulary renamed to
  `VALID_LOCATION_REASONS` (PRE_OPEN/STALE reasons are non-current, not
  "unavailable"); ORB sub-axis retained explicitly. (§7.1)
- **F3 — candidate-implication label:** `CANDIDATES_BLOCKED_OR_NEAR_MISS`
  replaced by the truthful cover-all `CANDIDATES_PRESENT_NONE_ACTIONABLE`,
  correct for ACTIVE-only/non-tradable maps as well as blocked/near-miss.
  (§7.7; M20)
- **F4 — INVALIDATION mixed-status precedence:**
  `TRIGGERED > WARNING > invalidation_indeterminate > NOT_TRIGGERED`, total
  over the defensive mixed-map combinations. (§7.6; M24)

### CARRIED FORWARD — RECOMMENDED, PENDING RATIFICATION (before Gate A)

- **D-1 always-on SPY STATE — recommend YES** (implicitly reaffirmed by the
  directive to preserve Option A; formally pending with Gate A).
- **D-4 Market Map retirement — recommend SPLIT.** No Market Map coupling or
  removal in this slice (restated as a hard boundary in the v0.4 authorization).
- **D-5 proceed on committed in-tree authority — recommend PROCEED.**
- **R3 presentation surface — recommend `dashboard.html` +
  `latest_payload.json` ONLY, not `report.html`** (§10).

The dormant OWNER-DEFERRED tokens (`invalidation_deferred_d2`,
`candidate_implication_deferred_d3`, `transition_deferred`) remain in their
frozensets solely for a future owner ruling that reverses the corresponding
ratified inclusion; they have no reachable branch while the 2026-08-07
ratifications stand and are classified accordingly in §7.

---

## 17. Out-of-scope observations — existing-code ambiguities (NOT NS-2E fixes)

Recorded here so the packet review does not rediscover them as NS-2E defects.
None blocks the card; none is patched in this slice; each is candidate MICRO /
follow-up material outside NS-2E.

- **A-1** `spy_observation.py`'s `intraday_fetch_failed` reason also fires when
  no fetch was attempted (fixture and Sunday runs leave `spy_session_frame=None`
  by construction, `runtime/__init__.py:981-1043`) — an untruthful reason label
  on those run classes. The card projects it verbatim (LOCATION is a raw
  projection); relabeling is a `spy_observation.py` change and therefore out of
  scope (§14.1).
- **A-2** The invalidation gate (PRD-068) is structurally a no-op under current
  routing: the thesis gate (PRD-067) pre-empts every TRIGGERED/WARNING/UNKNOWN
  branch (§7.6 proof). Its non-trivial surface is dead code. The card treats
  those branches as DEFENSIVE-ONLY; whether to retire or rewire the gate is a
  separate product decision.
- **A-3** `_PERMISSION_LINES.get(posture, "No new trades permitted.")` — the
  `.get` default is byte-identical to the STAY_FLAT line, so an out-of-set
  posture would silently read as STAY_FLAT. Unreachable in practice; a
  fail-loud default is a separate hardening candidate.
- **A-4** `system_state.intraday_state` (`contract.py:253-260`) carries the
  WATCH SESSION label, not ORB state — a naming collision adjacent to the
  card's STATE field. Documentation/rename is out of scope.

---

## 18. Packet review records (GOV-2 §2, §7 — COMPLETE; merged @ `53e76d5`)

The v0.1/v0.2/v0.3 review records remain on their PR trails (#222, #225, #226)
and satisfy no gate for v0.4. All v0.4 review events below are COMPLETE; the
packet is REVIEW-CLEAN and MERGED (PR #227 @ `53e76d5`). Downstream authority
still requires, in order: Dustin's design-direction ruling, a Stage-0 PRD, the
independent PRD review, and Gate A — none of which this packet grants.

### INITIAL PACKET REVIEW — COMPLETE (2026-08-07)

| Field | Value |
|---|---|
| Event type | `INITIAL PACKET REVIEW` (v0.4, GOV-2 §2 auto-commissioned) |
| Reviewer identity / capability role | independent Codex packet review (`chatgpt-codex-connector`, Codex cloud), fresh context, read-only (no repo write access) |
| Reviewed commit SHA / packet revision | `b95cccc87a70c2c26cdd8c0fa98b64b40502cd60` (PR #227 initial head) |
| Review date | 2026-08-07 |
| Verdict | 4 findings: 3 P1 + 1 P2 (no architectural finding; Option A undisputed) |
| Findings and dispositions | F1 Sunday skipped-gates vs truthful-empty (P1) → Sunday exclusion ruled, §1/M23. F2 LOCATION value vocabulary not closed (P1) → `VALID_LOCATION_STATES` / `VALID_LOCATION_PRICE_VS_VWAP` added, reason set renamed, §7.1. F3 `CANDIDATES_BLOCKED_OR_NEAR_MISS` false for ACTIVE-only map (P1) → replaced by `CANDIDATES_PRESENT_NONE_ACTIONABLE`, §7.7/M20. F4 mixed-status rollup precedence undefined (P2) → severity precedence pinned, §7.6/M24. All four dispositioned in the single GOV-1 consolidated correction (this revision), authorized by Dustin 2026-08-07 (§16). |
| Fresh-context / independence / run-isolation evidence | Codex cloud connector review, triggered by PR commission comment; reviewer had no authoring-session context and no write access; findings posted as PR review threads on PR #227 |

### EXACT-CORRECTED-HEAD CONFIRMATION — COMPLETE (2026-08-07)

| Field | Value |
|---|---|
| Event type | `EXACT-CORRECTED-HEAD CONFIRMATION` (GOV-2 §2 step 5) |
| Scope | disposition of exactly F1–F4 at the corrected head, plus detection of any new blocking inconsistency — a confirmation, not a fresh-scope review |
| Reviewed commit SHA | `4b8c7d0a965363ca442fc43b3a47f388581c7adf` |
| Verdict | F1–F4 dispositions confirmed (none re-raised); ZERO new P1 / boundary findings; ONE new P2 (M24 fixture matrix not discriminating for the stated total order — `{WARNING, UNKNOWN}` / `{TRIGGERED, UNKNOWN}` pairings absent) |
| Disposition | Owner ruled the permanent-stop rule NOT triggered (P2, not P1/boundary) and authorized a P2-ONLY micro-correction strictly limited to completing the M24 fixture matrix (this revision). Precedence semantics, vocabularies, reachability claims, and all contracts unchanged. |
| Fresh-context / independence / run-isolation evidence | Codex cloud connector review (`chatgpt-codex-connector`), commissioned by owner PR comment on PR #227 (2026-08-07 19:11Z-commission pattern; confirmation commission at 21:0xZ). Run-isolation: the reviewer executes in OpenAI's vendor-hosted Codex cloud runtime, instantiated per event, whose only inputs are the committed repository state at the pinned SHA and the PR surface — it shares no memory, context window, or session state with the Claude authoring session (different vendor, different runtime, no cross-session persistence). Read-only: no repo write access; finding delivered as PR review thread `discussion_r3738800831` (2026-08-07 21:13Z). |

### NARROW EXACT-HEAD CONFIRMATION OF THE P2 MICRO-CORRECTION — COMPLETE (2026-08-07)

| Field | Value |
|---|---|
| Event type | narrow exact-head confirmation (owner-commissioned, 2026-08-07) |
| Scope | ONLY: does M24 now discriminate the complete stated precedence, and does any new substantive P1/boundary inconsistency exist at the micro-corrected head |
| Reviewer identity / capability role | independent Codex review (`chatgpt-codex-connector`, Codex cloud), fresh context, read-only |
| Reviewed commit SHA | `b78e77c1bdabb433565af2928bbf03c33a67395c` |
| Verdict | **CLEAN — no issues found.** M24 discrimination unchallenged; zero new substantive P1/boundary inconsistencies; permanent-stop rule not triggered |
| Prior findings confirmed | the single P2 of the `4b8c7d0` confirmation (M24 fixture-matrix discrimination, thread `discussion_r3738800831`) — ACTIONED at this head; no other findings were open |
| Fresh-context / independence / run-isolation evidence | Codex cloud connector review (`chatgpt-codex-connector`), commissioned by owner PR comment on PR #227 (2026-08-07 22:19Z). Run-isolation: the reviewer executes in OpenAI's vendor-hosted Codex cloud runtime, instantiated per event, whose only inputs are the committed repository state at `b78e77c` and the PR surface — it shares no memory, context window, or session state with the Claude authoring session (different vendor, different runtime, no cross-session persistence). Read-only: no repo write access; verdict delivered as the PR comment "Didn't find any major issues. Reviewed commit: `b78e77c1bd`" (2026-08-07 22:35Z). |

### MERGE RECORD (2026-08-07)

PR #227 merged by Dustin (GOV-1 manual merge) at merge commit
`53e76d56350c3d0a6a60cb0e4f80235e28f2f774`, reviewed head
`b78e77c1bdabb433565af2928bbf03c33a67395c`. The v0.4 MATERIAL packet is
REVIEW-CLEAN / MERGED. Option A and all §16 ratified owner rulings are
unchanged by the merge.

**Terminal rule (binding, per Dustin 2026-08-07).** The permanent-stop rule is
unchanged: any NEW substantive P1 or boundary omission at any confirmation head
stops v0.4 permanently and returns it to the owner — no further correction
cycle exists. The P2 micro-correction above did not trigger it and does not
reset it.

---

END OF PACKET v0.4 — REVIEW-CLEAN / MERGED (PR #227 @ `53e76d5`, reviewed head
`b78e77c`) — NO IMPLEMENTATION AUTHORITY. v0.4 replaces PR #226 (v0.3), which
was terminated because vocabulary closure had not been exhaustively reconciled
before the composer vocabulary was specified; v0.1 (PR #222), v0.2 (PR #225),
and v0.3 (PR #226) are preserved untouched as the historical review trail.
Option A is preserved unchanged; the seven-field vocabulary layer is the
reconciled, code-demonstrated contract of §7. Gate A is neither requested nor
granted; the next governed step is Dustin's design-direction ruling.
