# NS-2E — Market Control Card — MATERIAL PACKET (v0.3, FUNDAMENTAL REDESIGN)

STATUS: PROVISIONAL — REDESIGN RESET v0.3 — NOT REVIEW-CLEAN — NO IMPLEMENTATION
AUTHORITY. This packet carries no implementation authority; Gate A is neither
requested nor granted by it. Owner decisions D-1..D-5 and owner rulings R1..R3
(§16) are RECOMMENDED — PENDING EXPLICIT OWNER RATIFICATION before Gate A.

SUPERSESSION / RESET: This v0.3 packet SUPERSEDES both prior packets in full.
v0.1 (PR #222) and v0.2 (PR #225, reviewed head
`48eed6d70b2f16fecdd14221a711923ba48ab737`) — with all their corrections, reviews,
and findings — are preserved unmodified on their PRs as the historical review
trail; neither PR, branch, nor file is edited or re-adjudicated here, and nothing
NS-2E exists on `main` at derivation. This is a **fundamental redesign, not a
correction of v0.2**: it is one coherent specification that makes the card
truthful BY CONSTRUCTION, incorporating the closure of all five v0.2 findings from
inception. There is no amendment chain to read.

The single fresh independent Codex review of THIS packet is commissioned only after
Dustin authorizes its push/PR (§17). Until that review completes, this packet is
PROVISIONAL — NOT REVIEW-CLEAN, and no downstream Stage-0 PRD may be opened.

CHRONOLOGY / AUTHORITY (binding):
- v0.1 (PR #222) → terminal review exposed a missing F5 regression proof.
- v0.2 (PR #225, reviewed head `48eed6d`) → a fresh independent Codex review
  returned FIVE substantive findings (four P1, one P2, §"Findings closed"); the
  owner terminal rule fired → fundamental redesign, not a fourth correction.
- A bounded read-only architectural study (this session) verified the root cause
  and the recommended architecture (Option A) against current `main`; a bounded
  architecture review APPROVED Option A WITH CORRECTIONS and found the design
  READY TO COMMISSION. This packet is that commission.
- Gate A: not requested, not granted. The prior PRs' reviews satisfy no gate here.

DERIVED AT: `main` @ `26c2afea163599ebae3c646ef244a4ea91683f7f` (post GEX-0 docs
PRs #223/#224). Working tree clean at derivation. Every `file:line` anchor below
was re-verified against this SHA.

GOVERNING RULING: Dustin's redesign direction — "do not correct v0.2; author a
clean v0.3 that makes truthfulness a structural property of construction, close all
five findings, keep the slice small, and do not touch the two reviewed producers
unless proven impossible otherwise." Where the direction is silent, VISION's
read-only-sidecars-by-default and cuts-before-additions principles govern.

CI CLAIM BOUNDARY (GOV-2 §8): This is a documentation-only packet. If CI runs
against the branch carrying it, green CI confirms only that this documentation
branch preserves the current green baseline. It does not execute or validate the
proposed single-frame architecture, the isolation boundary, the typed carrier, or
the regression plan.

PROVISIONAL-CEILING LABELS (GOV-2 §5): every FILES and LOC figure below is
`ESTIMATED SURFACE — NOT YET APPROVED`. The first binding ceiling is Gate A on the
reviewed PRD.

## Findings closed — the five v0.2 findings, closed BY CONSTRUCTION

All five reduced to one failure mode: v0.2 asserted truthfulness with post-hoc
guards and prose instead of making it a structural property of construction. v0.3
designs each out.

| v0.2 finding | v0.3 closure | Mechanism (§) | Proven by (§13) |
|---|---|---|---|
| P1 frame-identity mismatch | BY CONSTRUCTION | §2.2, §6 — STATE and freshness are functions of the SAME `spy_session_frame` object; no second SPY fetch exists to diverge | M1, M2 |
| P1 false no-persistence boundary | BY CORRECTED CLASSIFICATION | §8 — four-category vocabulary; v0.2's absolute "durable artifacts byte-for-byte unchanged" explicitly retracted; verified against `assert_valid_payload` | M11 |
| P1 STATE isolation too narrow | BY CONSTRUCTION (scoped) | §5 — the STATE-acquisition seam (owned adapter + prev-close + engine call) is inside one typed guard in `spy_state.py`; the adapter has no existence outside it. Scoped to STATE acquisition; it does NOT enclose the separate, unmodified `build_spy_observation` (F1) | M3, M4, M5, M8 |
| P1 incomplete reason vocabulary | BY CONSTRUCTION | §7, §9 — top-down per-field taxonomy + closed frozenset the carrier validates; an unenumerated branch fails construction | M7, M10 |
| P2 unenforced XOR | BY CONSTRUCTION | §4.1 — `SpyStateOutcome.__post_init__` (TradeDecision idiom) | M9 |

---

## 0. Where this packet sits in the GOV-2 order

```
materiality check at intake ............................. DONE (MATERIAL; §15)
provisional material packet authored .................... DONE (this v0.3 doc)
independent packet review (GOV-2 §2 step 3) ............. PENDING (§17; single
                                                          review, only after Dustin
                                                          authorizes push/PR)
one consolidated correction (step 4) ................... PENDING (GOV-1: at most one)
exact-corrected-head confirmation (step 5) ............. PENDING
Dustin design-direction ruling (step 6) ................ PENDING
Stage-0 PRD drafting (step 7) .......................... PENDING (no PRD allocated)
independent PRD review (step 7) ........................ PENDING
Dustin Gate A (step 8) ................................. PENDING (not requested)
```

Relationship to v0.1/v0.2: v0.3 supersedes both; the PR #222 and PR #225 trails are
untouched; their review events satisfy no v0.3 gate. MICRO-ineligible (MATERIAL,
§15); rides STANDARD at minimum.

---

## 1. Product question and user-visible outcome

A compact, read-only SPY **Market Control Card** on the **daily** dashboard,
answering VISION's questions at a glance: where are we, what is the market's state,
what am I permitted to do, and what does that imply for today's candidates —
without prediction, inventing nothing.

- **Scope: the daily `_run_pipeline` only.** Hourly is OUT OF SCOPE from inception.
- **Seven fields, each value-or-explicit-UNAVAILABLE:** LOCATION, STATE, PERMISSION,
  EVENT, TRANSITION, INVALIDATION, CANDIDATE-IMPLICATION. Every field is a truthful
  value or a typed UNAVAILABLE carrying a reason token; the renderer invents
  nothing (§2.3, §7).

---

## 2. Exact producer → carrier → consumer seam

### 2.1 Current state (verified at `main` @ `26c2afe`)

The decisive current-state fact is a **frame split**:

- **FRAME A — the SpyObservation frame.** `spy_session_frame =
  fetch_intraday_session_bars("SPY")` (`runtime/__init__.py:1043`; declared `None`
  @ :981) → passed as `session_frame` to `build_spy_observation(...)` @
  `:1288-1293`. `fetch_intraday_session_bars` (`ingestion.py:281`,
  `retain_full_session=True`) returns the COMPLETE 09:30–16:00 ET session,
  UTC-indexed DataFrame, with NO `.tail` truncation (docstring: "must not inherit
  the default 15:30 bound"). `spy_session_frame` has exactly 3 references (:981,
  :1043, :1290) and never reaches `compute_intraday_state`.
- **FRAME B — the intraday short-gate frame.** In the short-permission gate,
  per-symbol: `intraday_df = fetch_intraday_bars(symbol)` (`:1454`) →
  `_intraday_state_bars_from_df(intraday_df)` (`:1459`, def `:1576-1591`, produces
  `list[Bar]`) → `compute_intraday_state(symbol, symbol_bars,
  previous_close=_reconstruct_previous_close(...))` (`:1466`). The default
  `fetch_intraday_bars` (`ingestion.py:195`) bounds to `between_time("09:30",
  "15:30")` then `.tail(MAX_INTRADAY_RETURN_BARS=120)`.
- **Freshness ownership:** `build_spy_observation` (`spy_observation.py:64-126`)
  decides `OBSERVED`/`STALE`/`PRE_OPEN`/`UNAVAILABLE` (constants `:25-28`, `state:
  str` `:56`, `reason: Optional[str]`) from `observed_at_utc =
  session_frame.index[-1]` vs `run_at_utc`, the 180 s threshold, session-date match,
  and ET session gates. **It is a `str` from module constants, NOT an enum.**
- **Engine:** `compute_intraday_state(symbol, bars, *, previous_close=None) ->
  Optional[IntraState]` (`intraday_state_engine.py:400-405`) consumes `list[Bar]`
  (frozen `:52-59`); returns `None` before 09:45 ET (`_NOISE_END`, check `:435-436`);
  raises `InsufficientDataError` (def `:91-92`, raised `:136` when <5 bars in the
  09:30–09:35 ORB window, `_ORB_START/_ORB_END` `:32-33`, `_compute_orb` `:128,135`);
  raises `ValueError` on empty/non-chronological bars.
- **`previous_close`:** `_reconstruct_previous_close(execution_quotes.get(symbol))`
  (`runtime/__init__.py:1594-1600`) — reconstructed from the NormalizedQuote, NOT
  from any intraday frame; returns `None` on absent quote or non-positive
  denominator. `compute_intraday_state` accepts `previous_close=None`.
- **Delivery:** `PipelineResult.spy_observation` (`runtime/_types.py:92`) →
  `_write_payload_artifacts` (`runtime/__init__.py:2282-2295`) →
  `build_report_payload(contract, fixture_mode=False, *, spy_observation=None)`
  (`delivery/payload.py:24-29`), projecting `sections["spy_observation"]` only when
  provided (`:140-141`, projector `:160-185`) → `deliver_json` →
  `logs/latest_payload.json` (`transport.py:16`), `deliver_html` →
  `reports/output/report.html` (`transport.py:15`); `dashboard_renderer` reads
  `logs/latest_payload.json` (`:54`) and renders `sections["spy_observation"]`
  (`:2538-2556`) into `reports/output/dashboard.html` (`:56`). The `report.html`
  path (`html_renderer.render_html` → `render_report_from_payload`) does NOT read
  `sections["spy_observation"]` today (grep-verified).
- **Schema tolerance:** `assert_valid_payload` (`payload.py:188`) raises only on
  MISSING keys among the 9 canonical `sections` (`_require_keys` computes `missing =
  keys - set(obj)`, `:257-260`); there is NO unexpected-key rejection on the
  top-level `sections` dict (strict-key rejection exists only for
  `trade_decision_detail` items). An additive `sections["market_control_card"]`
  therefore passes with no required-key change and no `PAYLOAD_SCHEMA_VERSION` bump.
- **Confirmed:** no `MarketControlCard`, `SpyStateOutcome`, or `spy_state.py` exists
  in production today.

**The v0.2 defect this makes structural:** the freshness verdict is a statement
about FRAME A; v0.2's STATE would have been computed from FRAME B — a frame the
verdict says nothing about. A "sessions match" guard cannot restore object identity
between two independently-fetched frames.

**Decisive corollary (ORB availability).** FRAME B's `.tail(120)` drops the
09:30–09:34 ORB bars once the session advances past ~11:35–12:00 ET, so
`_compute_orb` raises `InsufficientDataError` — STATE is structurally uncomputable
from FRAME B for exactly the end-of-day runs the daily card serves. FRAME A retains
the ORB window all session. **Deriving STATE from FRAME A is not merely cleaner
provenance; it is the only currently existing SPY frame from which a daily/EOD STATE
is reliably computable.**

### 2.2 Proposed seam — single authoritative frame (Option A; additive)

One path; no new SPY fetch:

1. On the **daily** `_run_pipeline`, after the existing `build_spy_observation`
   (`:1288`), the **same** `spy_session_frame` local (FRAME A) plus the SPY
   `previous_close` are passed to a new bounded producer
   `cuttingboard/spy_state.py`:
   `build_spy_state_outcome(session_frame, previous_close) -> SpyStateOutcome`.
2. `spy_state.py` OWNS a small FRAME A → `list[Bar]` adapter (it does not reach into
   the private `_intraday_state_bars_from_df`), invokes `compute_intraday_state`
   READ-ONLY, converts expected data-quality failures to typed unavailability (§5),
   and returns a frozen XOR carrier `SpyStateOutcome` (§4.1).
3. The card builder consumes `SpyObservation` (LOCATION, freshness), the
   `SpyStateOutcome` (STATE), `system_state.permission` (PERMISSION), and the
   candidate inputs (§9) to compose the seven-field `MarketControlCard`. Because
   STATE is derived from the SAME frame that produced the freshness verdict, STATE
   and freshness share one frame identity BY CONSTRUCTION — there is no cross-frame
   gate to get wrong.
4. The card rides a NEW optional `PipelineResult.market_control_card` field
   (`runtime/_types.py`, mirroring `spy_observation` @ `:92`), forwarded to the
   daily `build_report_payload` as a NEW keyword-only parameter after the existing
   ones, projected to `sections["market_control_card"]`, rendered read-only into
   `dashboard.html` iff present (§10).

### 2.3 Binding rule

Read-only presentation surface. The **builder is the SOLE producer** of every final
card value; the **renderer projects and never derives, defaults, or invents**. No
decision-contract key; no persistence beyond the presentation reality of §8.

---

## 3. Recommended implementation design (single design)

One build, once, on the daily path:

1. **Single-frame STATE acquisition (closes finding 1 + 3).** `spy_state.py`
   receives FRAME A (the exact `spy_session_frame` object) and the SPY
   `previous_close`; adapts FRAME A → `list[Bar]`; calls `compute_intraday_state`;
   all acquisition/adaptation/computation failures resolve inside this one seam to a
   typed `SpyStateOutcome` (§5). No second SPY fetch; no adapter statement outside
   the guard.
2. **Typed XOR carrier (closes finding 5).** `SpyStateOutcome` carries EITHER an
   `IntraState` value OR an explicit unavailable reason token — enforced at
   construction (§4.1).
3. **Freshness identity (closes finding 1).** STATE and the `SpyObservation`
   freshness verdict are functions of the same object; STATE surfaces on the card
   only under the same freshness the observation reports — a STALE observation can
   never render a STATE as fresh (§6). This is identity, not an equality check.
4. **Seven-field composition (closes finding 4).** Each field is value-or-explicit-
   UNAVAILABLE with a reason token drawn from a closed per-field vocabulary (§7, §9);
   owner-deferred fields render explicit deferred tokens, never silence.

D-1 dependency: the always-on SPY STATE acquisition is genuinely new; §16 D-1
recommends YES and the FRAME A design makes it actually computable EOD.

---

## 4. Sidecar contract

### 4.1 New dataclasses (transient — not a durable schema of their own)

- **`SpyStateOutcome`** (frozen; `cuttingboard/spy_state.py`): fields `state:
  Optional[IntraState]`, `unavailable_reason: Optional[str]`. Strict-XOR invariant
  enforced in `__post_init__` on the `TradeDecision.__post_init__` idiom
  (`trade_decision.py:45-88`) — it MUST reject: both populated; neither populated;
  `unavailable_reason` not in the closed
  `VALID_SPY_STATE_UNAVAILABLE_REASONS` frozenset (enumerated at packet authority in
  §7); `state` populated but not an `IntraState`. Pure validation (no derived-default backfill). The pre-09:45 engine
  `None` maps to a carrier with the pre-computation-window token — `state=None,
  reason=None` is constructor-rejected, which IS the P2 fix.
- **`MarketControlCard`** (frozen, transient — not a durable schema of its own; its
  projected dict mirror rides the payload additively, §8): seven fields, each a
  value-or-explicit-UNAVAILABLE cell (a small structured value carrying either a
  truthful value or a reason token). Sole producer: the card builder.

### 4.2 Payload projection

New keyword-only parameter after the existing ones:
`build_report_payload(contract, fixture_mode=False, *, spy_observation=None,
market_control_card=None)` — `fixture_mode` and `spy_observation` retained verbatim
(breaks no caller; the illustrative signature is pinned exactly to `payload.py:24-29`).
`sections["market_control_card"]` is a JSON-safe plain-dict mirror (like
`_project_spy_observation`), present iff the card is provided (daily path).

### 4.3 Schema / persistence classification

The `SpyStateOutcome` / `MarketControlCard` dataclasses are transient (in-memory, not
a durable schema of their own). NO decision-contract key, NO schema migration, NO
`PAYLOAD_SCHEMA_VERSION` bump, NO required-key change — verified:
`assert_valid_payload` accepts extra `sections` keys (§2.1). The card's projected
`sections["market_control_card"]` key DOES appear additively in the schema-governed
`latest_payload.json` artifact (cat-4); see §8 for that precise persistence boundary.

---

## 5. STATE acquisition and failure isolation (closes finding 3 — STATE isolation)

**Scope of the boundary (F1 correction).** The isolation boundary is the
`spy_state.py` STATE-ACQUISITION seam ONLY — the owned FRAME A → `list[Bar]` adapter
plus the `compute_intraday_state` call. It is not the runtime call site and not
pipeline-wide, and it explicitly does NOT enclose `build_spy_observation`, which is a
separate, unmodified upstream producer that reads FRAME A first
(`runtime/__init__.py:1288`, before the STATE seam) and owns its own defensive
handling (`session_frame is None`/`<1 bar` → `UNAVAILABLE`, `spy_observation.py`).
This section makes no claim about, and requires no change to, the observation
producer.

**Realizable inputs (F1 correction).** FRAME A's shape is guaranteed by the single
`fetch_intraday_session_bars("SPY")` contract, which selects the OHLCV columns
(`ingestion.py:231`) or returns `None`/empty on failure (`:258-271`). The input
states this seam must handle are therefore exactly: a well-formed session frame; or
`None`/empty. A present-but-malformed FRAME A (e.g. an otherwise-current frame
missing a column) is not producible by that fetch; the packet does NOT claim to
convert such a pathological frame into typed unavailability at the daily-run
altitude, because `build_spy_observation` would encounter it first and covering it
there would require modifying `spy_observation.py` (§14 hard stop #1). The caught set
below protects the acquisition seam against the malformations reachable at the
adapter/compute stage and against realistic `None`/empty inputs — not against a
frame shape the fetch contract cannot produce.

- **Acquisition:** adapt FRAME A → `list[Bar]` (owned adapter), then
  `compute_intraday_state("SPY", bars, previous_close=previous_close)`.
- **Resolve to typed UNAVAILABLE** (input-quality conditions — the provider's data,
  not our code):
  - frame `None`/empty (fetch already failed upstream) → producer-absent token;
  - adapter data-shape failures — `KeyError` (missing OHLCV column), `ValueError`
    (uncoercible value; note `pandas.errors.ParserError ⊂ ValueError`, so index-parse
    failures are covered), `TypeError` (non-numeric cell);
  - `InsufficientDataError` (<5 ORB bars);
  - engine `ValueError` (empty / non-chronological bars).
  - **Caught set, exactly:** `(KeyError, ValueError, TypeError,
    InsufficientDataError)`.
- **In-band, not via the exception path:** engine returns `None` before 09:45 ET →
  the `pre_computation_window` token.
- **Propagate (programmer errors — fail loud at run level):** everything else —
  `AttributeError`, `NameError`, `IndexError` from our own logic, etc. **No `except
  Exception`.** A propagated programmer error reaches `execute_run` (`:294`) → error
  contract → non-zero-visible failure, exactly as PRD-198 #1 demands.
- **`previous_close` graceful degradation:** an absent SPY NormalizedQuote yields
  `previous_close=None`, which `compute_intraday_state` accepts (weaker gap-typing);
  it does NOT make STATE unavailable and MUST NOT trigger a new fetch (hard-stop §14).

**Truthful novelty framing.** No production site catches `InsufficientDataError` by
name today; this typed guard on the new acquisition is genuinely new. The existing
short-gate call site (`runtime/__init__.py:1465-1471`) uses a generic `except
Exception` for its own gating purpose and is NOT modified or reused — that blanket
catch is the anti-pattern v0.3 corrects, not the idiom it copies.

**Doctrine reconciliation.** PRD-198 #1 ("Fail-loud, never silent-fallback... must
exit non-zero — never substitute-and-continue") forbids fabricating substitute
values and forbids silence; a typed UNAVAILABLE with a validated reason token,
rendered explicitly on a read-only sidecar, substitutes nothing and hides nothing.
Collapsing the entire daily run because the STATE-acquisition seam hit an
input-quality failure (insufficient/late bars, an adapter data-shape error on the
bars it adapts, or a compute error) would be failing loud at the WRONG altitude.
Programmer errors keep the exit-non-zero path untouched.

---

## 6. Frame identity and freshness (closes finding 1)

- **Identity, not equality.** STATE (`SpyStateOutcome`) and freshness
  (`SpyObservation`) are functions of the SAME `spy_session_frame` object within one
  run. There is no second fetch to diverge; the mismatch v0.2 could express is
  inexpressible here.
- **Freshness coherence.** The card composer surfaces STATE only under the freshness
  the observation reports: when `SpyObservation.state != OBSERVED`
  (`PRE_OPEN`/`STALE`/`UNAVAILABLE`), STATE is presented as UNAVAILABLE with the
  cascade token (§7), never as a fresh value — even though STATE was computed from
  the same (stale) frame. Because both derive from one frame, this is a coherence
  projection, not a cross-frame gate. Pinned by M13.
- No second freshness system is introduced; `SpyObservation` remains the sole
  freshness authority (`spy_observation.py`, unmodified).

---

## 7. Seven-field semantics and unavailability taxonomy (closes finding 4)

Reason tokens are **field-specific constants + a `VALID_*` frozenset** per producer
(the repo's strongest idiom: `execution_policy.py`, `invalidation.py`), NOT one
global enum. LOCATION surfaces `SpyObservation` directly and admits its raw `reason`
tokens; STATE and PERMISSION are downstream fields and admit shared observation
conditions ONLY through the deterministic normalization table below (never as raw
tokens). Reason classes: FIELD-SPECIFIC / SHARED / OWNER-DECISION-DEFERRED /
INPUT-UNAVAILABLE / PRODUCER-ABSENT.

| Field | Source | Legitimate unavailable branches | Class |
|---|---|---|---|
| LOCATION | `SpyObservation` (existing) | shared frame conditions; zero-volume→VWAP None (`price_vs_vwap="UNAVAILABLE"`) | SHARED; FIELD-SPECIFIC |
| STATE | `SpyStateOutcome` from FRAME A (§5, §6) | `observation_unavailable` (shared); `insufficient_bars`; `pre_computation_window`; `state_computation_error` (adapter data-shape or engine ValueError); `non_current_observation` (cascade) | SHARED; FIELD-SPECIFIC; INPUT-UNAVAILABLE |
| PERMISSION | `system_state.permission` (existing) | genuine shared observation failure → `observation_unavailable`; source absent → `permission_state_absent`; source present-but-indeterminate → `permission_uncomputable`. Non-current freshness (`PRE_OPEN`/`STALE`) does NOT make PERMISSION unavailable | SHARED; FIELD-SPECIFIC |
| EVENT | none | `no_truthful_producer` (declared defensive — no producer today) | PRODUCER-ABSENT |
| TRANSITION | per R1 (§16) | STATE-unavailable cascade; per-R1 shape (see §16) | FIELD-SPECIFIC; OWNER-DECISION-DEFERRED |
| INVALIDATION | bounded composition over `invalidation_guidance_map` | D-2 declined/pending token (R2); map empty `{}`; per-symbol absent; in-band UNKNOWN (`INSUFFICIENT_DETERMINISTIC_INPUTS`, projected verbatim) | OWNER-DECISION-DEFERRED; INPUT-UNAVAILABLE; PRODUCER-ABSENT |
| CANDIDATE-IMPLICATION | bounded/minimal from `visibility_map` + run `outcome` | D-3 declined/pending token (R2); `visibility_map` empty `{}`; uncomposable when inputs absent | OWNER-DECISION-DEFERRED; PRODUCER-ABSENT; FIELD-SPECIFIC |

EVENT / TRANSITION-without-truthful-producer are DECLARED DEFENSIVE (Author
discipline #3): explicit `UNAVAILABLE(reason="no_truthful_producer")`, no implied
active channel.

**Closed per-field reason vocabularies (F2 — enumerated at PACKET authority; NOT
deferred to the implementing PRD).** Each field's unavailable-reason token set is
fixed here as a closed frozenset; the carrier/composer rejects any token outside its
field's set. Tokens are field-specific `snake_case` constants (the
`execution_policy.py` / `invalidation.py` idiom). Shared observation conditions reach
LOCATION as raw `SpyObservation.reason` tokens and reach STATE/PERMISSION only via
the deterministic normalization table that follows the frozensets.

- `VALID_SPY_STATE_UNAVAILABLE_REASONS = frozenset({"insufficient_bars",
  "pre_computation_window", "state_computation_error", "non_current_observation",
  "observation_unavailable"})` — respectively: engine `InsufficientDataError`
  (<5 ORB bars); engine `None` before 09:45 ET (in-band); adapter data-shape
  (`KeyError`/`ValueError`/`TypeError`) or engine `ValueError` at the acquisition
  seam; cascade when `SpyObservation.state` is `PRE_OPEN`/`STALE`; shared, when
  `SpyObservation` is `UNAVAILABLE` (halt / `None`-frame / fetch-failed).
- `VALID_LOCATION_UNAVAILABLE_REASONS` — PROJECTED from the existing `SpyObservation`
  vocabulary, not a new set: `{"system_halted", "intraday_fetch_failed",
  "insufficient_bars", "pre_open_prior_session", "session_mismatch", "pre_open",
  "observation_lag"}` (`spy_observation.py`), plus the field-specific
  `"vwap_unavailable"` for the zero-volume `price_vs_vwap="UNAVAILABLE"` case.
- `VALID_PERMISSION_UNAVAILABLE_REASONS = frozenset({"observation_unavailable",
  "permission_state_absent", "permission_uncomputable"})` — respectively: genuine
  shared observation failure (observation `UNAVAILABLE`, e.g. halt / fetch-failed);
  `system_state.permission` source absent; source present but indeterminate.
  Non-current freshness (`PRE_OPEN`/`STALE`) does NOT enter this set (normalization
  table below).
- `VALID_EVENT_UNAVAILABLE_REASONS = frozenset({"no_truthful_producer"})` — declared
  defensive; no producer today.
- `VALID_TRANSITION_UNAVAILABLE_REASONS = frozenset({"transition_state_unavailable",
  "transition_deferred", "no_truthful_producer"})` — cascade when STATE unavailable;
  owner-deferred if R1 (§16) is declined; defensive if no same-run producer is
  ratified.
- `VALID_INVALIDATION_UNAVAILABLE_REASONS = frozenset({"invalidation_deferred_d2",
  "invalidation_inputs_absent", "invalidation_indeterminate"})` — owner-deferred
  (R2); `invalidation_guidance_map` empty / per-symbol absent; in-band UNKNOWN
  (upstream `INSUFFICIENT_DETERMINISTIC_INPUTS`).
- `VALID_CANDIDATE_IMPLICATION_UNAVAILABLE_REASONS =
  frozenset({"candidate_implication_deferred_d3", "candidate_inputs_absent",
  "candidate_implication_uncomposable"})` — owner-deferred (R2); `visibility_map`
  empty / no candidates; uncomposable when the decision inputs are absent.

**Shared-observation reason normalization (normative; the implementing PRD has ZERO
discretion here).** LOCATION is the one field that surfaces `SpyObservation`
directly, so it admits the raw `SpyObservation.reason` tokens verbatim — that is
intentional and internally consistent (LOCATION *is* the observation projection).
STATE and PERMISSION do NOT admit raw observation tokens; they normalize
deterministically per the table below, keyed on `SpyObservation.state` (the closed
four-constant axis, which fully partitions the reason space). Every normalized output
is a member of that field's `VALID_*` frozenset, so no documented shared branch can
produce a token its carrier rejects.

| `SpyObservation.state` | member `SpyObservation.reason`(s) | → STATE token | → PERMISSION token |
|---|---|---|---|
| `OBSERVED` | — (observation current) | STATE computed; else acquisition-seam token (`insufficient_bars` / `pre_computation_window` / `state_computation_error`) | PERMISSION from `system_state.permission`; else `permission_state_absent` (source absent) or `permission_uncomputable` (source indeterminate) |
| `PRE_OPEN` | `pre_open`, `pre_open_prior_session` | `non_current_observation` | — (unaffected: `system_state.permission` is independent of SPY freshness and remains valued) |
| `STALE` | `session_mismatch`, `observation_lag` | `non_current_observation` | — (unaffected, as above) |
| `UNAVAILABLE` | `system_halted`, `intraday_fetch_failed`, `insufficient_bars` | `observation_unavailable` | `observation_unavailable` |

Normative rules: (1) STATE normalizes non-current freshness (`PRE_OPEN`/`STALE`) to
`non_current_observation` and genuine observation failure (`UNAVAILABLE`) to
`observation_unavailable` — the distinction the existing STATE vocabulary already
supports; STATE never emits a raw observation token. (2) PERMISSION is produced
independently by `system_state.permission`; its only shared-observation coupling is
genuine unavailability (`UNAVAILABLE` → `observation_unavailable`); non-current
freshness does not make PERMISSION unavailable. (3) No new tokens are introduced —
the enumerated vocabulary already expresses every required distinction. Pinned by
M13.

Every branch in the table above maps to exactly one token in its field's frozenset;
the sets are closed at THIS packet's authority (not deferred), so an unenumerated
branch fails construction rather than rendering silence. The implementing PRD binds
these sets as written and may only narrow them under a recorded owner ruling (e.g.
the R1 TRANSITION shape).

---

## 8. Persistence vocabulary (closes finding 2)

Output classification (verified `transport.py:15-16`, `dashboard_renderer.py:54-56`,
`runtime/__init__.py:2282-2295`):

1. **PRESENTATION** — `logs/latest_payload.json`, `reports/output/report.html`,
   `reports/output/dashboard.html`, `reports/{date}.md`.
2. **DURABLE OBSERVATION/CACHE** — `logs/market_map.json`,
   `logs/macro_drivers_snapshot.json`, `logs/trend_structure_snapshot.json`,
   `logs/performance_summary.json`, OHLCV cache.
3. **DECISION/AUDIT** — `logs/latest_contract.json` (PRD-011), `logs/audit.jsonl`,
   `logs/evaluation.jsonl`.
4. **SCHEMA-GOVERNED** — `logs/latest_payload.json`, `logs/market_map.json`,
   `logs/latest_contract.json`.

**Truthful boundary for the Market Control Card:**
- TRUE and intended: the card appears in existing PRESENTATION outputs (cat 1) — a
  new optional `sections["market_control_card"]` key in `latest_payload.json` and a
  rendered block in `dashboard.html` (and in `report.html` only per R3, §10).
- TRUE (F3 — precise): `logs/latest_payload.json` is a SCHEMA-GOVERNED (cat-4) — and
  simultaneously PRESENTATION (cat-1) — artifact, and it CHANGES ADDITIVELY: the
  optional `sections["market_control_card"]` key is written into it. That change is
  additive only — its required-key contract and `PAYLOAD_SCHEMA_VERSION` remain
  unchanged (verified: `assert_valid_payload` accepts extra `sections` keys, §2.1;
  accepting extra keys governs compatibility, it does not make the persistence
  disappear). The OTHER cat-4 artifacts (`market_map.json`, `latest_contract.json`)
  are untouched. All DECISION/AUDIT (cat-3) artifacts — `latest_contract.json`,
  `audit.jsonl`, `evaluation.jsonl` — are untouched. NO new cat-2 writes; NO new
  durable persistence SURFACE is introduced. **No blanket "category 4 is untouched"
  claim is made** — that would be false, since the payload artifact is cat-4 and
  changes additively.
- **EXPLICIT RETRACTION:** v0.2's absolute claim "durable artifacts byte-for-byte
  unchanged" (v0.2 §13 T10) is FALSE (the card, by design, changes cat-1 presentation
  files) and is retired. It must not be restated in any absolute form in any
  authority record.

---

## 9. Candidate inputs — CANDIDATE-IMPLICATION / INVALIDATION (F2 lineage, R2)

- **Builder receives candidate inputs as parameters:** `visibility_map`
  (`runtime/__init__.py:1140`), the run-level `outcome`, and
  `invalidation_guidance_map` (both from `_run_decision_gates`, `:1105-1123`).
  Verified: today none reach any card builder. `outcome` is a NON-optional `str`
  (`OUTCOME_TRADE`/`OUTCOME_NO_TRADE`/`OUTCOME_HALT`) — never modeled `Optional`;
  `visibility_map`/`invalidation_guidance_map` use empty `{}` = absent (never `None`
  at the `PipelineResult` boundary).
- **Renderer never derives** either field; the builder is sole producer.
- **CANDIDATE-IMPLICATION** — bounded/minimal rollup over actual candidate
  visibility/outcome (e.g. any candidate ACTIVE/NEAR_MISS/BLOCKED + run outcome);
  absence yields a truthful minimal value, not an invented one; D-3 declined/pending
  → explicit `candidate_implication_deferred_d3` token (R2), never silence.
- **INVALIDATION** — bounded composition over the existing `invalidation_guidance_map`
  only (no new computation, no predictive judgment); D-2 declined/pending → explicit
  `invalidation_deferred_d2` token (R2), never silence.

---

## 10. Presentation surface (R3)

Per R3 (§16, recommended): the card renders in **`logs/latest_payload.json`
(mirror) + `reports/output/dashboard.html` only** — NOT `report.html`. Verified:
`html_renderer` (report.html) does not read `sections["spy_observation"]` today, so
adding the card there would require teaching `render_report_from_payload` — extra
surface for no product need. The card's home is the dashboard, matching the existing
SPY-observation card footprint. If Dustin ratifies report.html inclusion, that is a
bounded addition recorded before Gate A.

---

## 11. Exact likely files (ESTIMATED SURFACE — NOT YET APPROVED)

Option A. Production files:

| Op | File | Purpose |
|---|---|---|
| A | `cuttingboard/spy_state.py` (new) | `SpyStateOutcome` + `VALID_SPY_STATE_UNAVAILABLE_REASONS`; owned FRAME A→`list[Bar]` adapter; `build_spy_state_outcome`; the isolation boundary (§5) |
| A/M | card builder — new `cuttingboard/market_control_card.py` (or a bounded builder within the seam) | `MarketControlCard` + seven-field composition (§7, §9), sole producer |
| M | `cuttingboard/runtime/__init__.py` | call `build_spy_state_outcome` with the existing `spy_session_frame` + SPY `previous_close`; build the card; set `PipelineResult.market_control_card`; forward to the daily `build_report_payload`; hourly untouched |
| M | `cuttingboard/runtime/_types.py` | one optional `market_control_card` field on `PipelineResult` (mirrors `spy_observation` `:92`) |
| M | `cuttingboard/delivery/payload.py` | keyword-only `market_control_card` param + `sections["market_control_card"]` projection |
| M | `cuttingboard/delivery/dashboard_renderer.py` | one card block, present iff section present (precedent `:2538-2556`) |

**Deliberately NOT in FILES (design claims the reviewer should attack):**
`cuttingboard/spy_observation.py` and `cuttingboard/intraday_state_engine.py` remain
READ-ONLY imports. Touching either is a §14 stop-and-amend event.

Test files: new `tests/test_spy_state.py` (+ `tests/test_market_control_card.py` if
the builder is a separate module); bounded edits to `tests/test_runtime_decision.py`,
`tests/test_payload.py`, `tests/test_dashboard_renderer.py`. PRD-158 sweep: this
change deletes/renames no rendered token; sweep over `market_control_card`,
`SpyStateOutcome`, and the reason tokens adds no further asserting test files.

---

## 12. Estimated production LOC ceiling (ESTIMATED SURFACE — NOT YET APPROVED)

Governing metric: net production LOC via `git diff --numstat` across the authorized
production files; test LOC uncounted.

- **~+150–230 net production LOC; provisional ceiling ≤300.** The STATE spine
  (`spy_state.py` + carrier + isolation) is ~130–190; the bounded seven-field
  composer + payload/renderer plumbing adds the remainder. Non-binding; first binding
  ceiling is Gate A.
- **Stop-and-amend tripwire:** any production file beyond the §11 set, any change to
  the two excluded producers, any persistence/schema/decision-contract touch, or any
  second SPY fetch → §14.

---

## 13. Discriminating test / mutation matrix (M-suffix = reddening mutation required)

| # | Case | Asserted | Mut? |
|---|---|---|---|
| M1 | Same-frame identity | STATE derived from the exact object passed to `build_spy_observation`; discriminating fixture where full-session vs tail-120 frame yield different STATE (ORB present only in full session) | **YES** — reintroducing a separate fetch/frame reddens |
| M2 | Single fetch | fetch counter: exactly one `fetch_intraday_session_bars("SPY")` feeds both observation and STATE | **YES** |
| M3 | Fetch None/empty FRAME A (the realistic failure the fetch contract can produce) | observation UNAVAILABLE (its own guard) AND carrier unavailable (producer-absent); daily run NOT ERROR | |
| M4 | Adapter data-shape failure at the STATE seam — call `build_spy_state_outcome` with a malformed bar input (missing OHLCV column) | typed UNAVAILABLE from that call (unit-level, at the `spy_state.py` seam) — proves the adapter/compute guard catches it | **YES** — narrowing the guard to compute-only reddens |
| M5 | Adapter ValueError at the STATE seam (uncoercible/unparseable value) | typed UNAVAILABLE from `build_spy_state_outcome` | |
| M6 | InsufficientDataError (<5 ORB bars) | typed UNAVAILABLE, field-specific token | |
| M7 | Pre-09:45 engine None | typed UNAVAILABLE, `pre_computation_window` — distinct from error tokens | |
| M8 | Injected AttributeError in the engine call | PROPAGATES to run level (error contract) — proves no blanket catch | **YES** |
| M9 | XOR both / neither populated | `SpyStateOutcome.__post_init__` raises both ways | **YES** |
| M10 | Unknown reason token | constructor raises | **YES** |
| M11 | Persistence truth | card present in redirected `latest_payload.json` + rendered `dashboard.html`; redirected `audit.jsonl` and `latest_contract.json` byte-unchanged (conftest `_isolate_real_log_paths`) | |
| M12 | Additive-only e2e | `_run_pipeline(mode=MODE_FIXTURE)`: outcome/halt/decision fields pinned unchanged while card section present | |
| M13 | Freshness coherence + shared-reason normalization | `STALE`/`PRE_OPEN` observation → STATE = `non_current_observation` (never fresh) AND PERMISSION unaffected (still valued); observation `UNAVAILABLE` (halt) → STATE and PERMISSION = `observation_unavailable`. Pins the §7 normalization table into STATE/PERMISSION | **YES** |
| M14 | Halt path | `halted=True` → observation + carrier unavailable; no fetch, no engine call attempted | |

Reuse `_utc_frame` (test_spy_observation.py:27-33) for DataFrame fixtures and the ET
`_bar/_orb_bars/_noise_bars` builders (test_intraday_state.py) for Bar fixtures.
Payload gate via `assert_valid_payload` with/without the section; dashboard via
targeted substring presence/absence — NO golden-file byte-diff. Mutation plan: a
guard whose mutation leaves all tests green is not a guard and does not merge.

---

## 14. Stop-and-amend conditions (hard stops — return to Dustin, re-run GOV-2 §1)

1. Any change to `intraday_state_engine.py` or `spy_observation.py` beyond read-only
   import.
2. Any required-key addition to `assert_valid_payload` or any `PAYLOAD_SCHEMA_VERSION`
   bump.
3. Any SPY fetch beyond the existing single `fetch_intraday_session_bars("SPY")`.
4. Any NEW durable persistence SURFACE for the card; any write to a cat-2
   (observation/cache) or cat-3 (decision/audit) artifact; or any change to a cat-4
   artifact's `PAYLOAD_SCHEMA_VERSION` or required-key contract. (The additive
   optional `sections["market_control_card"]` key in the existing cat-4/cat-1
   `latest_payload.json` is the intended, allowed behavior — §8 — not a stop
   condition.)
5. The hourly path consuming `sections["market_control_card"]`.
6. TRANSITION (R1) requiring persisted prior-run state — a new persistence category.
7. Any decision-contract change.
8. Any Market Map removal/refactor in this slice (D-4 SPLIT).
9. Exceeding the §11 Option-A file surface, or the §12 ceiling, without a fresh
   GOV-2 §1 classification.
10. Renderer-side derivation of any card value; or EVENT/TRANSITION gaining a
    "producer" without a truthful source.

---

## 15. Materiality / lane classification

**MATERIAL** under GOV-2 §1: new cross-layer seam (runtime → transient carrier →
payload → renderer), new module `spy_state.py`, new `SpyStateOutcome` /
`MarketControlCard` dataclasses. Fits the existing NS-2E MATERIAL classification; no
new materiality trigger beyond what v0.1/v0.2 carried (Option A adds no new consumer,
no schema-version/required-key change, and no new persistence surface — the card
rides the existing payload additively, §8). Lane: STANDARD minimum (MICRO-ineligible). After the
packet is review-clean and Dustin issues a design-direction ruling, a fresh PRD →
independent PRD review → Gate A sequence is required before implementation.

---

## 16. Owner decisions and rulings (RECOMMENDED — PENDING OWNER RATIFICATION)

Nothing here is ratified. The design encodes these as working assumptions so the
spec is coherent; each is held for Dustin's explicit ratification before Gate A.

**D-1 always-on SPY STATE — recommend YES (strengthened).** FRAME A makes daily/EOD
STATE actually computable (FRAME B could not, §2.1 corollary). If declined: STATE
joins EVENT as explicit UNAVAILABLE and §5 is moot.

**D-2 bounded INVALIDATION — recommend INCLUDE (refined).** Composition-only over
`invalidation_guidance_map`; declined/pending renders an explicit token (R2), never
silence.

**D-3 minimal CANDIDATE-IMPLICATION — recommend INCLUDE (refined).** Truthful by
construction from real candidate inputs; declined/pending renders an explicit token
(R2).

**D-4 Market Map retirement — recommend SPLIT.** No Market Map coupling or removal in
this slice.

**D-5 proceed on committed in-tree authority — recommend PROCEED**, conditioned on
this packet's corrected §8 persistence wording replacing the false v0.2 absolute
claim (satisfied here).

**R1 TRANSITION — recommend the smallest truthful SAME-RUN definition.** Sourced from
fields the engine already computes on FRAME A (`IntraState.orb_break_direction`,
`reclaimed_orb`, `failed_reclaim`, `holding_bars`, `phase`) — an intra-session
transition (e.g. "ORB broken long, holding" / "failed reclaim"), composed by the
builder, cascading to explicit UNAVAILABLE when STATE is unavailable. This needs NO
prior-run state. A run-over-run TRANSITION would require persisted prior-run state →
hard stop §14.6. If no same-run definition is product-meaningful, fall back to
explicit OWNER-DECISION-DEFERRED unavailability (never silence).

**R2 D-2/D-3 declined/pending shape — recommend explicit compact tokens.** INVALIDATION
→ `invalidation_deferred_d2`; CANDIDATE-IMPLICATION → `candidate_implication_deferred_d3`;
rendered as "UNAVAILABLE — deferred pending owner ruling"; field-specific,
provenance-honest, never silent omission.

**R3 report.html — recommend dashboard.html + latest_payload.json ONLY, not
report.html** (§10). Smallest useful presentation set.

---

## 17. Packet review records (GOV-2 §2, §7 — PENDING)

NO REVIEW OF THIS v0.3 PACKET HAS OCCURRED. The single fresh independent Codex
packet review is commissioned ONLY AFTER Dustin authorizes the push/PR carrying it —
not requested, scheduled, or implied by this document's existence. The v0.1/v0.2
review records remain on the superseded PR #222/#225 trails and satisfy no gate for
v0.3. Until the record below is populated, this packet is PROVISIONAL — NOT
REVIEW-CLEAN, and no downstream PRD may be opened on it.

### INITIAL PACKET REVIEW — PENDING

| Field | Value |
|---|---|
| Event type | `INITIAL PACKET REVIEW` (v0.3, GOV-2 §2 auto-commissioned) |
| Reviewer identity / capability role | PENDING — independent Codex packet review, fresh context, read-only |
| Reviewed commit SHA / packet revision | PENDING — pinned to the exact reviewed commit at review time |
| Review date | PENDING |
| Verdict | PENDING |
| Findings and dispositions | PENDING — at most one consolidated correction cycle (GOV-1) |
| Fresh-context / independence / run-isolation evidence | PENDING — recorded at review time |

**Terminal rule (binding).** This redesign gets ONE fresh independent review after
Dustin authorizes the push/PR. If that review finds another structural or boundary
omission, work STOPS and returns to Dustin for a more fundamental owner redesign — it
does NOT begin another iterative correction chain.

---

END OF PACKET v0.3 — PROVISIONAL — REDESIGN RESET — NOT REVIEW-CLEAN — NO
IMPLEMENTATION AUTHORITY. v0.3 supersedes v0.1 (PR #222) and v0.2 (PR #225), both
preserved untouched, and closes all five v0.2 findings by construction. Gate A is
neither requested nor granted. D-1..D-5 and R1..R3 are recommended, pending owner
ratification.
