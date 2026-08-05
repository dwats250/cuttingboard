# NS-2A / NS-2C — Fixed SPY Observation & Session VWAP — MATERIAL PACKET (v0.1)

STATUS: PROVISIONAL — NOT REVIEW-CLEAN. This is the upstream GOV-2 MATERIAL
packet for NS-2A (fixed SPY observation) and NS-2C (session VWAP). It carries no
implementation authority. Per GOV-2 §2 it must receive an independent Codex
packet review, one consolidated correction, and independent exact-corrected-head
confirmation before Dustin issues a design-direction ruling, a PRD is drafted
and independently reviewed, and Gate A is issued.

DERIVED AT: `main` @ `4902b1fd27df541ef432ac4511520919ff7045aa` (post-PR #209 /
PRD-271 merge). Working tree clean at derivation.

GOVERNING RULING: Dustin/ChatGPT design-direction ruling of 2026-08-05
(accepts the Stage-0 recommendation with binding scoping). This packet
implements that ruling verbatim; where the ruling is silent, VISION's
read-only-sidecars-by-default and cuts-before-additions principles govern.

CI CLAIM BOUNDARY (GOV-2 §8): This is a documentation-only packet. If CI runs
against the branch carrying it, green CI confirms only that this documentation
branch preserves the current green baseline. It does not execute or validate the
proposed runtime design, consumer inventory, VWAP formula, freshness rules, or
regression plan.

PROVISIONAL-CEILING LABELS (GOV-2 §5): every FILES and LOC figure below is
`ESTIMATED SURFACE — NOT YET APPROVED`. The first binding ceiling is Gate A on
the reviewed PRD.

CORRECTION LOG — Consolidated correction 1 (2026-08-05): applied one consolidated
correction addressing review findings F1–F5 (author self-verification pass; NOT
the GOV-2 §2 independent review). F1 lane classification resolved (§15); F2
regular-session VWAP window end bound pinned (§5, §6); F3 OBSERVED/`session_vwap`
contract contradiction eliminated (§4.1, §7.1, §7.2, §8); F4 timestamp authority
designated for the two-fetch case (§2.2, §4.1, §5); F5 one-ORB-truth and
halt-semantics proof obligations added (§13). No redesign, no scope expansion.
This corrected head is still NOT review-clean until the independent Codex packet
review and exact-corrected-head confirmation (GOV-2 §2, §7) complete.

CORRECTION LOG — Consolidated correction 2 (2026-08-05, Dustin-authorized): the
GOV-2 §2 step-4 consolidated correction responding to the independent Codex
packet review received on PR #210 at `16c2e40` (INITIAL PACKET REVIEW). Five
findings, all confirmed valid; Dustin ruled "correct + scope out hourly" (GOV-2
§6 "narrow its claim"). Applied: (Codex P1, carrier→payload) the transient
`SpyObservation` reaches the renderer via a new optional `build_report_payload`
parameter, NOT the contract — specified in §2.2/§4.2/§11; (Codex P1, hourly) the
outcome is narrowed to the daily `_run_pipeline`; the hourly publish path is
explicitly OUT OF SCOPE (card absent on hourly, §1/§2.2/§14), with hourly
coverage deferred to a follow-up; (Codex P2, zero-volume) the §4.1 value-emission
invariant is corrected so `price_vs_vwap` is a valid OBSERVED token ("UNAVAILABLE"
on zero volume) while `session_vwap` stays unset — no contradiction; (Codex P3,
status) §0's order table now reflects the true state. This consumes the single
GOV-2 §2 correction cycle for this packet. GOV-2 §6 first-boundary handling: this
is the first discovered omitted seam (hourly), resolved by narrowing the claim,
not by rebuild. Next step: independent Codex exact-corrected-head confirmation of
THIS head (GOV-2 §2 step 5, §7). Findings disposition for PR #210 threads: all
ACTIONED by this correction (cite this commit).

LOCAL CORRECTION 3 (2026-08-05, Dustin-authorized, GOV-2 §6 local fix — NOT a new
substantive cycle): the exact-corrected-head confirmation of `02202f7` confirmed
all four prior findings resolved and raised one NEW local P2 — the illustrative
`build_report_payload` signature dropped the existing `fixture_mode` parameter.
This is a local signature/wording accuracy fix, not a material boundary omission,
so it does not return the packet to DESIGN INCOMPLETE (GOV-2 §7). Corrected: the
signature now retains `fixture_mode` and adds `spy_observation` as a keyword-only
argument after it — `build_report_payload(contract, fixture_mode=False, *,
spy_observation=None)` (§2.2, §4.2, §11). No other change. A narrowly scoped
exact-head confirmation of the new head is then requested.

North Star lineage: NS-2A + NS-2C (ledger
`docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:132,134`), unblocked
by PRD-271 / NS-2B landing (PR #209). Evidence seed: `audits/stage0-recon-2026-07-20/`
(stage0-01 decision surface, verify-01). Materiality already ruled by the North
Star deep audit (TM-017).

---

## 0. Where this packet sits in the GOV-2 order

```
materiality check at intake ............................. DONE (MATERIAL; §15)
-> provisional material packet .......................... THIS DOCUMENT
-> independent Codex packet review ...................... RECEIVED (PR #210 @ 16c2e40; advisory — durable §17 record pending Dustin)
-> one consolidated author correction .................. DONE (correction 2, Dustin-authorized; THIS head — cycle consumed)
-> Codex exact-corrected-head confirmation ............. PENDING (of THIS corrected head; §17)
-> Dustin design-direction ruling on review-clean packet PENDING
-> PRD drafting ........................................ NOT STARTED (do not draft yet)
-> independent PRD review .............................. later
-> Dustin Gate A ...................................... later
-> implementation ..................................... later
```

No production implementation, PRD execution, branch-for-implementation, or
contract/persistence change may begin until the packet is review-clean, Dustin
has ruled, the PRD is drafted and independently reviewed, and Gate A is issued
(GOV-2 §4).

---

## 1. Product question and user-visible outcome

**Product question (the seam answers five things, all decision-support only):**

1. What session is being observed? (observed symbol = SPY; intended session date)
2. Is the observation current and usable? (freshness lifecycle state)
3. Where is SPY relative to the session VWAP? (session VWAP + price relation)
4. What current-session ORB is active? (projected PRD-271 ORB state + bounds)
5. What is unavailable, stale, forming, or invalid? (explicit reason token)

**User-visible outcome:** one compact SPY observation card on the daily
dashboard, present on **every relevant daily `_run_pipeline` run** — including
STAY_FLAT / NO_TRADE runs and daily halted runs — and therefore **independent of
candidate availability**. On a healthy run it shows SPY's session date,
observation timestamp, freshness, session VWAP and price-vs-VWAP relation, and
the current-session ORB state and bounds. When any input is missing, stale,
pre-open, or the run is halted, the card states that explicitly through lifecycle
truth rather than blanking or fabricating a value.

**SCOPE (Codex P1, Dustin ruling 2026-08-05 — narrowed):** this slice covers the
daily `_run_pipeline` path only. The **hourly publish path is explicitly OUT OF
SCOPE** — `_execute_notify_run` keeps `intraday_metrics = {}`
(`runtime/__init__.py:404`) and `_write_hourly_artifacts` renders from
`build_report_payload(contract)` (`:2112,:2122`) with no observation passed, so
the card is **absent** on the hourly-published `ui/dashboard.html` during market
hours. This is an accepted, honest v1 limitation (card appears on the daily
dashboard render, not the hourly republishes); extending the observation to the
hourly producer/carrier/artifact path is a deferred follow-up (§9, §14). The
earlier "every relevant run" wording is withdrawn.

**This is description, not prediction** (VISION). It computes no score, no
recommendation, no gate; it changes no execution decision (§10).

---

## 2. Exact producer → carrier → consumer seam

### 2.1 Current state (what exists at `4902b1f`)

- SPY ∈ `config.REQUIRED_SYMBOLS` (`cuttingboard/config.py:205`), so SPY is
  always in `validation_summary.valid_quotes` on any non-halt run.
- `runtime/__init__.py:1035` `compute_all_intraday_metrics(list(execution_quotes),
  asof=run_at_utc)` already produces `intraday_metrics["SPY"]`
  (`watch.IntradayMetrics`) on every non-halt live run (skipped on
  `MODE_FIXTURE`, `:1033`; skipped on both halt branches — `:996`, `:999` — where
  `intraday_metrics` keeps its default `{}` from `:979`).
- `IntradayMetrics` (`watch.py:94`) carries `orb: Optional[OrbObservation]`
  (`:112`) — session-true ORB provenance from PRD-271 — plus a rolling-tail
  `vwap` (`:100`, computed `:245-253`).
- **This observation is currently discarded for SPY**: SPY is never a trade
  *decision*, so `intraday_metrics["SPY"]` never reaches
  `_build_execution_policy_orb_states` (`runtime/__init__.py:1498`, keyed on
  decision tickers `:1504`) and is never surfaced anywhere SPY-specific.
- `OrbObservation` (`watch.py:77`, frozen, non-persisted): `state`,
  `trading_date`, `observed_at_utc`, `orb_high`, `orb_low`, `reason`. Produced by
  `_session_orb` (`watch.py:403`). ORB high/low populated **only** when
  `state == FORMED`.

### 2.2 Proposed seam (additive; nothing above is modified)

```
PRODUCER (new)                     CARRIER (new, transient)        CONSUMER (one card)
build_spy_observation(...)   -->   SpyObservation (frozen)   -->   payload.sections["spy_observation"]
  reads:                             fields: §4                       --> dashboard SPY card
   - intraday_metrics["SPY"].orb       (projects OrbObservation           (dashboard_renderer)
     (PROJECTED VERBATIM; §2.3)         verbatim; adds VWAP +
   - SPY full-session frame             freshness axis)
     (new opt-in fetch; §5)
   - run_at_utc (intended session)
   - halt flags (system_halted /
     kill-switch)
```

- **Producer:** new `cuttingboard/spy_observation.py::build_spy_observation(...)`
  — a dedicated module so watch.py's execution-adjacent surface is untouched and
  the non-effect boundary (§10) is structurally obvious.
- **Carrier:** new frozen `SpyObservation` (transient, non-persisted; mirrors
  `OrbObservation`'s discipline). Built in the **daily `_run_pipeline`** on BOTH
  its non-halt and halt branches (so the card is present on every daily run), and
  passed to the payload projection as an explicit argument (below). The hourly
  path does not build or pass it (§1 SCOPE).
- **Consumer / carrier→payload threading (Codex P1, resolved):**
  `delivery/payload.py::build_report_payload` currently takes a `PipelineContract`
  plus a `fixture_mode` flag (`payload.py:24`:
  `build_report_payload(contract, fixture_mode=False)`). Because §4.3 forbids
  putting the observation on the contract, the carrier reaches the projection via
  a **new keyword-only parameter added AFTER the existing ones (retaining
  `fixture_mode`)** — `build_report_payload(contract, fixture_mode=False, *,
  spy_observation: SpyObservation | None = None)`. Existing callers (which pass
  `fixture_mode=_fixture_mode`) are unaffected; the daily writer additionally
  passes the built observation;
  the hourly writer (`_write_hourly_artifacts`, `runtime/__init__.py:2122`) and
  any other caller pass nothing → `None` → no `spy_observation` section → card
  omitted (this is exactly the hourly scope-out, achieved by construction, not a
  special case). When present, `build_report_payload` projects
  `sections["spy_observation"]`; `delivery/dashboard_renderer.py` renders one
  card when the section exists and omits it when absent, reusing existing
  freshness/timestamp helpers and the VWAP-relation display map. The new
  parameter is additive and default-`None`, so no existing caller changes
  behavior.
- **Two SPY intraday fetches per run (acknowledged coupling, F4).** The projected
  `OrbObservation` is produced by the existing watch path
  (`compute_all_intraday_metrics → fetch_intraday_orb_bars`,
  `runtime/__init__.py:1035`), while the current price, session VWAP, and the
  headline observation timestamp come from the new SPY-only full-session fetch
  (§5). This is one additional SPY fetch per run (SPY only; ~391 bars). The two
  frames are captured at different instants, so their latest-bar timestamps can
  differ by the inter-fetch interval; the card's single authoritative
  `observed_at_utc` is defined in §4.1 to resolve this. No recomputation of the
  ORB occurs (§2.3).

### 2.3 The one-ORB-truth rule (binding)

The SPY observation **projects PRD-271's `OrbObservation` verbatim** — it holds
the existing `OrbObservation` object from `intraday_metrics["SPY"].orb` and reads
its `state`/`orb_high`/`orb_low`/`reason`. It never recomputes an opening range,
never calls `_session_orb` itself, and introduces no second ORB producer. If
`intraday_metrics["SPY"]` is absent (halt / fetch failure), the ORB portion of
the card reports UNAVAILABLE with the observation-level reason.

---

## 3. Recommended implementation design (single design, not alternatives)

A **transient, read-only SPY observation sidecar** that:

1. Builds a new frozen `SpyObservation` in a new `spy_observation.py`, from (a)
   the already-computed `intraday_metrics["SPY"].orb` projected verbatim, (b) a
   SPY-only bounded full-session intraday frame fetched through a new opt-in path
   for a truthful session VWAP, (c) `run_at_utc` for the intended session, and
   (d) halt flags.
2. Computes SPY session VWAP over the 09:30-ET-anchored full-session frame (§6),
   emitting it **only** in the OBSERVED state.
3. Derives an observation freshness lifecycle (PRE_OPEN / OBSERVED / STALE /
   UNAVAILABLE, §7-§8), separate from the ORB lifecycle.
4. Threads `SpyObservation` through the **daily** `_run_pipeline`
   (`runtime/__init__.py`) on its non-halt and halt branches, passes it as the
   new optional `build_report_payload` argument (daily writer only), and renders
   one dashboard card. The hourly path passes nothing (§1 SCOPE).
5. Touches **no** execution, candidate, short-permission, evaluation,
   `_watch_zones`, `IntradayMetrics.vwap`, or ORB-policy surface (§10).
6. Adds **no** durable/contract schema and **no** cross-run persistence (§4.3).

Rejected-elsewhere alternatives (recorded once, not offered as a menu): changing
`IntradayMetrics.vwap` to session-anchored (rejected — mutates the shared
execution-adjacent watch path, would alter `_watch_zones`/`near_vwap`/bias);
adding a required `PipelineContract` key (rejected — CONTRACT-class schema change
forcing HIGH-RISK, violates read-only-sidecar doctrine); persisting cumulative
PV/volume across runs (rejected by the ruling — no persistence authorized;
truthful session VWAP is achieved by bounded full-session retention within a
single run instead).

---

## 4. Sidecar contract

### 4.1 `SpyObservation` (new frozen dataclass, transient, non-persisted)

| Field | Type | Notes |
|---|---|---|
| `observed_symbol` | `str` | Constant `"SPY"`. |
| `intended_session_date` | `Optional[date]` | ET date of `run_at_utc` (the intended current session). |
| `timezone` | `str` | `"America/New_York"` (the canonical literal). |
| `observed_at_utc` | `Optional[datetime]` | UTC timestamp of the latest bar of the SPY **full-session fetch** (§5) — the single authoritative headline observation time; `None` when UNAVAILABLE. |
| `state` | `str` | Observation lifecycle: `PRE_OPEN` / `OBSERVED` / `STALE` / `UNAVAILABLE` (§7). |
| `reason` | `Optional[str]` | Reason token for any non-OBSERVED state (§7.2). |
| `session_vwap` | `Optional[float]` | Emitted **only** when `state == OBSERVED` **and** session volume > 0; else `None` (§4.1 invariant, §8). |
| `current_price` | `Optional[float]` | SPY last price; emitted **only** when `state == OBSERVED`. |
| `price_vs_vwap` | `Optional[str]` | `ABOVE` / `BELOW` / `AT_LEVEL` when VWAP is formed; `"UNAVAILABLE"` on a zero-volume OBSERVED run; `None` in any non-OBSERVED state. |
| `orb` | `Optional[OrbObservation]` | The PRD-271 carrier, projected verbatim (§2.3). |

Invariants (mirroring PRD-271's "high/low only when FORMED"):
- **Timestamp authority (F4):** `observed_at_utc` is the UTC timestamp of the
  latest bar of the new SPY-only **full-session fetch** (§5) — the single
  authoritative headline observation time, and the value the freshness state
  machine (§8) is computed against. The projected `OrbObservation` retains its
  own `observed_at_utc` on the nested `orb` for ORB provenance; it may differ by
  the inter-fetch interval and is never the card's headline timestamp.
- **Value emission (F3 + Codex P2, corrected):** `current_price` and
  `price_vs_vwap` are non-`None` **iff** `state == OBSERVED`. `session_vwap` is
  non-`None` **iff** `state == OBSERVED` **and** session volume > 0. On a
  zero-volume OBSERVED run, `session_vwap = None` while `price_vs_vwap =
  "UNAVAILABLE"` — `"UNAVAILABLE"` is a **valid OBSERVED relation token** meaning
  "cannot compare to VWAP", not a null; `current_price` remains present. The
  price observation is still current; only the VWAP comparison cannot be formed.
  (This removes the prior lumping of `price_vs_vwap` with `session_vwap`, which
  made the two contradict on zero volume.) No value is ever presented as current
  in any non-OBSERVED state (ruling §3).
- `orb_high`/`orb_low` are read only from `orb` and only when
  `orb.state == FORMED` (already guaranteed by `OrbObservation`).

### 4.2 Payload projection

`build_report_payload(contract, fixture_mode=False, *, spy_observation=None)` adds
`sections["spy_observation"]` = a plain dict mirror of the fields above
(dates/timestamps ISO-stringified) **only when the `spy_observation` argument is
provided** (daily path). When the argument is `None` (hourly path, §1 SCOPE, and
every pre-existing caller), no section is added and the renderer omits the card.
One reader: the dashboard renderer. No other consumer reads it.

### 4.3 Schema / persistence classification

- **No required `PipelineContract` top-level key** is added; the observation
  never enters `contract.py`'s `required_top` (`contract.py:601-606`) or
  `SYSTEM_STATE_ALLOWED_KEYS` (`:78-80`).
- **No new durable/decision-contract schema and no cross-run persistence.** The
  observation flows through the per-run render payload
  (`logs/latest_payload.json`), which is regenerated every run by the existing
  `transport.py` writer; it is a transient render feed, not a durable
  observation store. No observation state is carried from one run to the next.
- The single schema-surface touch is the additive payload section (one reader,
  one presentation path); `delivery/payload.py` is not a HIGH-RISK file and not
  the decision contract (bears on lane, §15).

---

## 5. SPY-only full-session-fetch boundary

**Why a new path:** a truthful full-session VWAP cannot be computed from the
existing retained frames. `fetch_intraday_bars` default returns
`tail(MAX_INTRADAY_RETURN_BARS=120)` (`ingestion.py:235-238`), and
`fetch_intraday_orb_bars` returns `_retain_session_frame` = `09:30-09:35 ET ∪
tail(120)` (`ingestion.py:179-191, 262-266`); `watch._bars_from_df` re-truncates
to `tail(120)`. On any session longer than ~120 minutes, mid-session bars are
dropped, so any VWAP over these frames is a rolling-window VWAP, not a
session-anchored one.

**Boundary (binding per ruling §2):**
- A **new opt-in full-session path** returns the **complete current
  regular-session** SPY frame for the intended session, UTC-indexed, no
  `tail(120)` truncation. **Session window (F2): 09:30–16:00 ET** — the regular
  session per `time_utils._MARKET_OPEN_ET`/`_MARKET_CLOSE_ET`
  (`time_utils.py:12-13`). This path **must set its own
  `between_time("09:30","16:00")` and must NOT inherit the default fetcher's
  `between_time("09:30","15:30")` bound (`ingestion.py:228`)**, which would
  silently drop 15:30–16:00 ET and make the "authoritative session VWAP"
  untruthful. Bounded to the single latest session date selected at
  `ingestion.py:231-232` (≈391 one-minute bars max for the full 09:30–16:00
  window; trivial memory for one symbol). The default fetcher's 15:30 bound is a
  pre-existing behavior of the contiguous-tail path and is **not changed** by
  this slice (adjacent, out of scope).
- **Ordinary `fetch_intraday_bars` behavior is unchanged** for short-permission
  state (`runtime/__init__.py:1436`), post-trade evaluation (`evaluation.py:160`),
  and every other contiguous-tail consumer. `fetch_intraday_orb_bars` (the watch
  ORB producer) is likewise unchanged.
- The full-session frame is consumed **only** by `build_spy_observation` for SPY
  and **must not leak** into `IntradayMetrics`, `_bars_from_df`, `_watch_zones`,
  or any existing consumer.
- **No persistence.** The frame lives for the single run; nothing is written to
  disk or carried across runs.

Implementation shape (recommended): a new keyword flag on `fetch_intraday_bars`
(e.g. `retain_full_session: bool = False`) or a thin wrapper
`fetch_intraday_session_bars(symbol)` mirroring the PRD-271 `retain_opening_range`
opt-in pattern, so the default contiguous behavior is preserved byte-for-byte and
proven so by test (§13).

---

## 6. VWAP formula and session anchor

- **Session anchor:** 09:30 ET of the intended current trading date.
- **Window (F2):** 09:30 ET (inclusive) through the latest observed bar, bounded
  by the 16:00 ET regular-session close; regular-session bars only, over the
  09:30–16:00 ET frame from the SPY-only full-session fetch (§5) — **not** the
  default fetcher's 09:30–15:30 frame.
- **Formula (cumulative typical-price VWAP):**
  `VWAP = Σ(TP_i · V_i) / Σ(V_i)`, where `TP_i = (High_i + Low_i + Close_i) / 3`.
  This reuses the typical-price accumulation pattern at `watch.py:249-253` but
  over the **full session frame** (09:30-anchored), not the rolling tail. It
  matches the session-date-masking discipline of `trend_structure._vwap`
  (`trend_structure.py:59-71`) while remaining intraday.
- **Zero-volume guard (fail-loud, PRD-198 #1):** if `Σ(V_i) == 0`, VWAP is
  **UNAVAILABLE** — the observation does not seed VWAP with the last close (which
  `watch.py:247` does for its rolling VWAP). This is a deliberate truthfulness
  improvement scoped to the new observation only; the existing watch VWAP is not
  changed.
- **Price relation:** `price_vs_vwap` compares `current_price` to `session_vwap`
  with a neutral band. Recommended band: reuse the sibling engine's
  `_VWAP_BUFFER = 0.001` (±10 bps) semantics (`intraday_state_engine.py:39,157-162`)
  → within ±0.1% ⇒ `AT_LEVEL`, above ⇒ `ABOVE`, below ⇒ `BELOW`. The band exists
  so a price sitting essentially on VWAP is not flapped ABOVE/BELOW by sub-tick
  noise. The buffer value is proposed, not inherited silently; packet review
  should confirm ±10 bps is appropriate for SPY intraday granularity.

---

## 7. Lifecycle and reason-token definitions

Two independent axes ride the card:

- **ORB axis** — reused **verbatim** from PRD-271, no new truth: states
  `PRE_OPEN / FORMING / FORMED / UNAVAILABLE / INVALID`; reasons `no_bars,
  unordered_bars, pre_open_prior_session, session_mismatch, mixed_session,
  formation_bars_absent, formation_incomplete, impossible_bounds`
  (`watch.py:41-45, 415-500`).
- **Observation/freshness axis** — new, minimal (below).

### 7.1 Observation states

| State | Meaning | VWAP/price emitted? |
|---|---|---|
| `PRE_OPEN` | Intended session has not opened, or latest frame is the prior session and the intended session's open window has not yet passed (benign). | No |
| `OBSERVED` | Current-session SPY data present and within the freshness threshold. | `current_price`: always. `price_vs_vwap`: always (a relation when volume > 0, else the token `"UNAVAILABLE"`). `session_vwap`: only when volume > 0, else `None` (§4.1, §8). |
| `STALE` | Data present but older than the freshness threshold, or a session mismatch after the session should be live. Fail-loud, never presented as current. | No |
| `UNAVAILABLE` | No usable SPY frame this run (fetch failed, insufficient bars, or run halted). | No |

### 7.2 Observation reason tokens

`system_halted` (run halted), `intraday_fetch_failed` (no frame returned),
`insufficient_bars` (frame too short to observe), `pre_open` (before 09:30 ET,
current session), `pre_open_prior_session` (prior-session frame before the
intended session's open window has passed), `session_mismatch` (prior-session
frame after the session should be live), `observation_lag` (current-session
frame older than the freshness threshold).

These reason tokens annotate **non-OBSERVED** states only. VWAP-unavailability
within an OBSERVED run (zero session volume) is NOT a state or reason change: it
is expressed through `session_vwap = None` and `price_vs_vwap = "UNAVAILABLE"`
per the §4.1 value-emission invariant (F3). There is no `no_volume` observation
reason token.

---

## 8. Freshness semantics

Inputs: `intended_session_date` (ET date of `run_at_utc`), `observed_at_utc`
(latest SPY bar), `trading_date` (ET date of the latest bar), `now` (`run_at_utc`),
bar count, halt flags.

**Transition rules (evaluated in order):**

1. Run halted (`validation_summary.system_halted` or kill-switch) →
   `UNAVAILABLE / system_halted` (no fetch attempted this slice; §9).
2. No frame or bar count below the observability floor →
   `UNAVAILABLE / intraday_fetch_failed | insufficient_bars`.
3. `trading_date != intended_session_date` (session mismatch):
   - `now` ET time ≤ 09:35 (intended session's open window not yet passed) →
     `PRE_OPEN / pre_open_prior_session` (the scheduled ~13:00 UTC pre-open run
     normally sees the prior session with `prepost=False`; this is benign and
     matches `_session_orb`'s `pre_open_prior_session` handling at
     `watch.py:436-442`).
   - else (session should be live) → `STALE / session_mismatch`.
4. `trading_date == intended_session_date`:
   - `now` ET time < 09:30 (market not open) → `PRE_OPEN / pre_open`.
   - `age = now − observed_at_utc`; `age ≤ SPY_OBSERVATION_STALE_AFTER_SECONDS`
     → `OBSERVED`; else → `STALE / observation_lag`.

**Session mismatch, before vs after open (ruling §4):** before the intended
session's 09:35 open window has passed, a prior-session frame is the benign
PRE_OPEN condition; after it, a prior-session frame is fail-loud STALE. This
mirrors the ORB axis exactly (PRE_OPEN vs INVALID/`session_mismatch`), so the two
axes never disagree about whether the session is live.

**Freshness threshold and rationale (ruling §4 — do not inherit blindly):**
1-minute bars arrive once per minute; a completed bar for minute *M* becomes
available shortly after *M+1*, plus provider (yfinance) lag. Expected age of the
latest bar at fetch time is therefore ~60-120 s under healthy conditions. A
threshold must exceed ~120 s to avoid false STALE, and be small enough to catch a
genuine multi-minute stall. **Proposed: `SPY_OBSERVATION_STALE_AFTER_SECONDS =
180` (3 min)** — 2× the 60 s bar cadence plus a one-cadence provider-lag margin.
This is deliberately **not** the 300 s quote-`FRESHNESS_SECONDS`
(`config.py:104`) nor the 300 s `DASHBOARD_STALE_AFTER_SECONDS`
(`dashboard_renderer.py:178`): those gate scalar-quote and page-age freshness,
not 1-minute intraday-bar cadence. The 300 s constants are recorded as the
conservative fallback if observed provider lag proves to exceed 180 s in live use;
the packet review should confirm the value against real yfinance 1-minute lag
before Gate A.

**Display vocabulary reuse:** the card reuses `_compute_timestamp_freshness`
(`dashboard_renderer.py:302`), `_freshness_label` (`:328-341`), and the
`ABOVE/BELOW/AT_LEVEL/UNAVAILABLE` display map (`:133-174`) for rendering — the
NEW element is only the threshold constant and the observation state machine, not
the render helpers.

**Zero-volume resolution (F3, resolved — no longer an open question):** a
zero-session-volume run where VWAP cannot be formed renders as `OBSERVED` (the
price observation is genuinely current) with `session_vwap = None` and
`price_vs_vwap = "UNAVAILABLE"`. It is not a distinct state and carries no
`no_volume` reason token; VWAP-unavailability is a value-emission fact under the
§4.1 invariant, not a lifecycle transition.

---

## 9. Halt behavior (ruling §3, binding)

- **Do not** lift SPY acquisition or computation above the halt branch
  (`runtime/__init__.py:996-1037`) in this slice. No live-fetch restructuring.
- On a halted run (data-integrity halt at `:996` or market-stress kill-switch at
  `:999`), `runtime/__init__.py` still builds and threads a `SpyObservation` with
  `state = UNAVAILABLE`, `reason = system_halted`, `session_vwap = None`,
  `current_price = None`, `orb` reporting UNAVAILABLE.
- The card is **present** on halted runs, showing lifecycle truth — no fabricated
  VWAP, no prior-run value, no stale current-session claim.
- Live SPY observation during market-stress halts (where SPY-vs-VWAP is arguably
  most decision-relevant) is **deferred** to a separate follow-up proposal after
  this slice ships and is observed in use.

---

## 10. Explicit non-effects on execution

The seam is read-only and additive. It provably does not affect:

- **Execution eligibility / trade decisions** — no change to
  `execution_policy.py`, `_run_decision_gates`, or the ORB gate
  (`_evaluate_orb_constraint`, `execution_policy.py:283-302`).
- **Candidate selection** — no change to qualification/options.
- **Short permission** — `_apply_intraday_short_permission`
  (`runtime/__init__.py:1399`) and `fetch_intraday_bars` default behavior
  unchanged.
- **Post-trade evaluation** — `evaluation.py:160` fetch path unchanged.
- **`_watch_zones`** — `market_map.py:310-339` unchanged; the new session VWAP is
  never written into market-map zones.
- **`IntradayMetrics.vwap`** — the shared rolling-tail VWAP (`watch.py:100,
  245-253`) is untouched; the session VWAP lives only on `SpyObservation`.
- **ORB policy** — `_build_execution_policy_orb_states`
  (`runtime/__init__.py:1498`) and `OrbPolicyState` (`execution_policy.py:57`)
  unchanged; there remains exactly one ORB truth (PRD-271's), projected verbatim.

**Proof obligation:** every existing ORB/VWAP/execution test must remain green
**unchanged** (§13 PRD-158 sweep). Their greenness is part of the non-effect
evidence.

---

## 11. Exact likely files (ESTIMATED SURFACE — NOT YET APPROVED)

Production:

| Op | File | Purpose |
|---|---|---|
| A | `cuttingboard/spy_observation.py` (new) | `SpyObservation` carrier + `build_spy_observation` + session-VWAP + freshness state machine |
| M | `cuttingboard/ingestion.py` | new opt-in bounded full-session SPY fetch path; default contiguous behavior preserved |
| M | `cuttingboard/runtime/__init__.py` | build & thread `SpyObservation` on the **daily** `_run_pipeline` non-halt AND halt branches, and pass it into the daily `build_report_payload` call. The hourly path (`_execute_notify_run`, `_write_hourly_artifacts`) is **NOT** modified — it keeps passing no observation (hourly scope-out, §1). |
| M | `cuttingboard/delivery/payload.py` | add a keyword-only `spy_observation` parameter to `build_report_payload` **after the existing `fixture_mode`** (retain `fixture_mode`); project `sections["spy_observation"]` only when it is provided |
| M | `cuttingboard/delivery/dashboard_renderer.py` | render one compact SPY card when the section is present; omit it when absent (hourly) |

Tests (edited/added):

| Op | File | Purpose |
|---|---|---|
| A | `tests/test_spy_observation.py` (new) | lifecycle, VWAP, freshness, fetch-boundary, halt — discriminating + mutation (T1–T10) |
| M | `tests/test_dashboard_renderer.py` | card render incl. UNAVAILABLE/halt/STALE/PRE_OPEN states, and card omission when no section |
| M | `tests/test_payload.py` | payload projection via the `spy_observation` parameter; hourly no-argument → no section (T12) |
| M | `tests/test_runtime_decision.py` | T11 halt-semantics-unchanged on the daily run (moved here from the must-stay-green set because T11 adds an assertion) |

Must remain GREEN, **unchanged** (non-effect proof; PRD-158 sweep of
`orb_high|orb_low|orb_inside_range|vwap|OrbObservation|orb_break` across
`tests/`): `tests/test_watch.py`, `tests/test_execution_policy.py`,
`tests/test_market_map.py`, `tests/test_intraday_state.py`,
`tests/test_dash_level_diagram.py`, `tests/test_gap_down_permission_integration.py`,
`tests/test_levels.py`, `tests/test_overnight_policy.py`,
`tests/test_prd017_notification_stabilization.py`,
`tests/test_trade_explanation.py`, `tests/test_trade_visibility.py`,
`tests/test_trend_structure.py`. (`tests/test_runtime_decision.py` is edited for
T11 and is listed above, not here.) (This change renames/deletes no field or token,
so the PRD-158 sweep adds none of these to FILES; they are listed as the
must-stay-green non-effect set.)

If review determines the full-session fetch boundary needs its own
ingestion-level regression (no `tests/test_ingestion.py` exists today), a new
`tests/test_ingestion.py` enters FILES via the amended estimate — flagged now so
it is not a reactive amendment.

---

## 12. Estimated production LOC ceiling

**ESTIMATED SURFACE — NOT YET APPROVED: ≤ 190 net production LOC** across the five
production files. Indicative split: `spy_observation.py` ~90; `ingestion.py`
full-session path ~25; `runtime/__init__.py` bridge (non-halt + halt) ~30;
`payload.py` projection ~15; `dashboard_renderer.py` card ~30. Test LOC is not
counted against this ceiling. A design that widens the fetch boundary, adds
persistence, or pushes into a contract key exceeds this estimate and is a
stop-and-amend event (§14).

---

## 13. Discriminating test plan

Each guard ships its red test (PRD-198 #4); T1/T2/T7 must reproduce where CI
determines truth (PRD-198 #5).

- **T1 — Healthy current session:** current-session SPY frame → `OBSERVED`;
  `session_vwap` equals the 09:30-anchored typical-price VWAP over the full
  session; `price_vs_vwap` correct vs the buffer; `orb` projected from FORMED.
- **T2 — Stale prior session (post-open):** prior-session frame, run past 09:35 →
  `STALE / session_mismatch`; `session_vwap`/`current_price`/`price_vs_vwap` all
  `None`; ORB never rendered as current.
- **T3 — Pre-open:** run before 09:30 (or prior-session frame ≤ 09:35) →
  `PRE_OPEN`; no invented VWAP/ORB; no error.
- **T4 — Fetch failure / insufficient bars:** `UNAVAILABLE` with reason; no
  fabricated value; VWAP not seeded from last close (PRD-198 #1).
- **T5 — NO_TRADE / STAY_FLAT run, no candidates:** card **present** and
  populated (the core NS-2A "independent of candidate availability" exit).
- **T6 — Halted run:** card present as `UNAVAILABLE / system_halted`; no VWAP; no
  stale/current claim (ruling §3).
- **T7 — Long full session (>120 bars):** session VWAP is truthful across the
  whole session (kills the rolling-tail limitation; passes only under the
  full-session fetch of §5).
- **T8 — Full-session fetch non-leak:** the new opt-in path returns the full
  session for SPY while `fetch_intraday_bars` default still returns the
  contiguous `tail(120)` for the short-gate/evaluation consumers (boundary of §5
  proven).
- **T9 — Zero-volume session:** `OBSERVED` with `session_vwap=None` and
  `price_vs_vwap="UNAVAILABLE"` per the §8 zero-volume resolution; no
  divide-by-zero, no fabricated VWAP.
- **T10 — one-ORB-truth (F5):** the card's ORB `state`/`orb_high`/`orb_low` are
  identical to `intraday_metrics["SPY"].orb`; `build_spy_observation` never calls
  `_session_orb` and never recomputes an opening range.
- **T11 — halt semantics unchanged (F5):** on a halted daily run the run
  `outcome`, `system_halted`, and `halt_reason` are identical to pre-change
  behavior; the added `SpyObservation` build is pure and side-effect-free (and
  yields `UNAVAILABLE / system_halted`, per T6).
- **T12 — hourly scope-out (Codex P1):** the hourly artifact path
  (`build_report_payload(contract)` with no `spy_observation` argument) produces a
  payload with **no** `spy_observation` section, and the renderer omits the card;
  the hourly path is proven unmodified. *(Mutation: pass an observation into the
  hourly writer → T12 RED, since the scope-out is violated.)*

**Mutation plan (PRD-198 #4):**
- Anchor the VWAP to the rolling tail instead of 09:30 → T1/T7 RED.
- Remove the session-mismatch STALE branch → T2 RED.
- Seed VWAP with last close on zero volume → T4/T9 RED.
- Drop the halt-path `SpyObservation` build → T6 RED.
- Skip the observation on no-candidate runs → T5 RED.
- Let the full-session frame flow into the default fetcher → T8 RED (a
  contiguous-consumer assertion breaks).
- Introduce any second/recomputed ORB in `build_spy_observation` (instead of
  projecting `intraday_metrics["SPY"].orb` verbatim) → T10 RED.
- Make the halt-path `SpyObservation` build alter `outcome`/halt state or raise →
  T11 RED.
- Pass an observation into the hourly writer / project a section on the hourly
  payload (violating the scope-out) → T12 RED.
A guard whose mutation leaves all tests green is not a guard and does not merge.

---

## 14. Stop-and-amend conditions

- Any move to a durable persisted observation store or a required
  `PipelineContract` top-level key → re-run GOV-2 classification; stop for
  amended authority (this would be ALT-B / CONTRACT-class).
- Any change to `IntradayMetrics.vwap`, `_watch_zones`, the ORB execution gate,
  short permission, or evaluation → forbidden in this slice (§10); stop.
- Any second ORB producer or recomputation of the opening range instead of
  projecting `OrbObservation` verbatim → forbidden (§2.3); stop.
- The full-session fetch changing what any contiguous-tail consumer sees
  (short gate `runtime/__init__.py:1436`, evaluation `evaluation.py:160`,
  watch producer) → stop; the fetch must stay strictly opt-in and SPY-only.
- Discovery that a truthful VWAP requires cross-run persistence after all → stop;
  surface to Dustin (no persistence is authorized).
- Needing to lift SPY acquisition above the halt branch to satisfy any card
  requirement → stop; that is the deferred follow-up (§9).
- Extending the SPY card to the **hourly** publish path (threading the
  observation through `_execute_notify_run` / `_write_hourly_artifacts` /
  `hourly_alert.yml`) → out of scope for this slice (§1 SCOPE); it is a separate
  follow-up proposal with its own producer/carrier/artifact inventory, FILES, and
  materiality re-run. Do not add it under this packet.
- FILES or LOC estimate needing to grow past §11/§12 → GOV-2 §5 stop-and-renew:
  amend the PRD, obtain fresh-context independent review of the exact amended
  revision, and Dustin's amended Gate A.

---

## 15. Materiality / lane classification

**MATERIAL** (GOV-2 §1), consistent with the North Star deep audit's TM-017.
Matching conditions: (i) it selects a carrier/seam feeding a presentation path
and crosses ≥2 of runtime / delivery / dashboard; (ii) it establishes a
production FILES/LOC estimate for a new observational surface; (iii) it adds a
payload schema surface with a reader. Therefore this upstream packet, its
independent Codex review, and the exact-corrected-head confirmation are required
before a design-direction ruling and downstream PRD.

**Governing CLASS: CONSUMER. Resulting LANE: HIGH-RISK (F1, resolved).** The
packet's user-visible deliverable is a dashboard card, and the design edits
`cuttingboard/delivery/dashboard_renderer.py` to render it. That file is a
**HIGH-RISK FILE for CLASS CONSUMER** (`docs/PRD_PROCESS.md:454`), touched as this
change's **payload** (the card render, PRD-276 payload-vs-pointer). Under the Lane
Downgrade Prohibition (PRD-121 R11, `docs/PRD_PROCESS.md:493-500`) that forces
`LANE: HIGH-RISK` regardless of diff size — the same determination Dustin applied
to the presentation-only renderer changes PRD-249 and PRD-250 (both
HIGH-RISK/CONSUMER because `dashboard_renderer.py` is a CONSUMER HIGH-RISK file).
MATERIAL already disqualifies MICRO (GOV-2 §1); the earlier STANDARD reading is
withdrawn.

The new `cuttingboard/spy_observation.py` module and the additive
`payload.sections["spy_observation"]` are sidecar-flavored, but CONSUMER is the
governing CLASS because the highest-risk payload surface is a CONSUMER HIGH-RISK
file and the deliverable is consumer-facing. The `runtime/__init__.py` threading
is additive and non-decision-bearing; note that the CLASS matrix's EXECUTION
HIGH-RISK entry names the legacy monolith `cuttingboard/runtime.py`, and whether
the `cuttingboard/runtime/__init__.py` package file inherits that status is an
acknowledged ambiguity (runtime-package debt) — it does not lower the lane, which
is already HIGH-RISK on the renderer trigger.

HIGH-RISK lane consequences the eventual PRD inherits: fresh-context-OR-
different-model review independence (`docs/PRD_PROCESS.md:491`) and the mandatory
Second-Model Disposition (a commissioned `PRD-NNN.review.<model>.md` artifact or
the verbatim `SECOND-MODEL:` line). MATERIAL classification adds no
Codex-commissioned events beyond the two GOV-2 §7 packet-cycle events; the
HIGH-RISK implementation-review disposition is a separate, lane-driven
requirement. A later design that instead added a contract-key or
execution-touching surface would remain HIGH-RISK and additionally trip the
CONTRACT/EXECUTION forbidden-surface rules — a stop-and-amend event (§14).

**GOV-0 / expansion-plan note:** this is a North Star NS-2 product slice, not a
GEX / news / options-data / macro-awareness expansion; the three
`docs/plans/*-v0.1.md` expansion files do not govern it. GOV-1's universal
manual-merge and one-fresh-context-review gate apply as to any PR.

---

## 16. Document-drift correction to carry (ruling §5)

`docs/PROJECT_STATE.md` (last updated #203, 2026-08-03) still lists PRD-271 as
`IN PROGRESS … held for Dustin's merge`; PRD-271 merged via PR #209 and this
packet is derived from that merged state. Per the ruling, this stale status is
recorded here as an **adjacent documentation correction to ride the eventual
governed PRD/implementation closeout** — not a separate cleanup initiative and
not fixed by this read-only packet.

---

## 17. Packet review records (GOV-2 §2, §7 — to be completed before review-clean)

### INITIAL PACKET REVIEW — PENDING
- Event type: `INITIAL PACKET REVIEW`
- Reviewer identity / capability role: _pending_
- Reviewed commit SHA / packet revision: _pending_
- Review date: _pending_
- Verdict: _pending_
- Findings and dispositions: _pending_
- Fresh-context / independence / run-isolation evidence: _pending_

### EXACT-CORRECTED-HEAD CONFIRMATION — PENDING
- Event type: `EXACT-CORRECTED-HEAD CONFIRMATION`
- Reviewer identity / capability role: _pending_
- Corrected head SHA: _pending_
- Prior finding identifiers + dispositions being confirmed: _pending_
- Review date: _pending_
- Verdict: _pending_
- Fresh-context / independence evidence: _pending_

A corrected head without independent SHA-pinned confirmation is not
review-clean (GOV-2 §2). A connector comment, resolved thread, external link, or
ephemeral transcript cannot substitute for either committed record.

---

END OF PACKET v0.1 — HELD FOR INDEPENDENT PACKET REVIEW AND DUSTIN/CHATGPT
DISPOSITION.
