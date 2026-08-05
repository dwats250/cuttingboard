# NS-2A / NS-2C — Fixed SPY Observation & Session VWAP — MATERIAL PACKET (v0.1)

STATUS: REVIEW-CLEAN — RESTORED after correction 4 re-confirmation (2026-08-05);
durable in `main` on the merge of PR #215. This is the upstream GOV-2 MATERIAL
packet for NS-2A (fixed SPY observation) and NS-2C (session VWAP). It still
carries no implementation authority.

The packet was REVIEW-CLEAN via PR #212 (merge `3061ca53493649e7e4940c43f78016ba5f1d492c`);
a connector finding on downstream Stage-0 PRD-288 (PR #214, **P1**) then revealed a
MATERIAL BOUNDARY OMISSION — the v0.1 seam never specified the intra-runtime
carrier from `_run_pipeline` to the daily `build_report_payload` call (which runs
AFTER the pipeline returns, in `_write_payload_artifacts(pipeline.contract)`, with
only `contract` in scope; `PipelineResult` (`runtime/_types.py`) had no
observation field; a contract key is forbidden §4.3; ORB recompute is forbidden
§2.3). Per GOV-2 §6/§7 that briefly returned the packet to DESIGN INCOMPLETE. It
is corrected by **correction 4** (the observation rides a new optional
`PipelineResult.spy_observation` field in `cuttingboard/runtime/_types.py` — a 6th
production file; §2.1/§2.2/§11/§12/§14), on Dustin's 2026-08-05 "fix the packet
first (GOV-2)" ruling. The independent exact-corrected-head RE-CONFIRMATION of the
corrected design head `2e9d6a422f940d07516f5ff011005689a048a881` returned **CLEAN**
(Codex "Didn't find any major issues"; §17), which RESTORES REVIEW-CLEAN. This
durable status/record edit is committed on top of that re-confirmed design head
(record-only — no design changed after the re-confirmed head) and takes effect in
`main` on the merge of PR #215.

The prior GOV-2 §2/§7 review cycle also stands, recorded in §17: an independent
Codex packet review (of `16c2e40`), one consolidated author correction
(correction 2 → `02202f7`), then independent exact-corrected-head confirmation —
a bounded GOV-2 §6 local fix (correction 3 → `1308871`) followed by Codex's clean
confirmation of `130887125bcac8952ea812d6e2dbcbd319515dcb`. Both cycles stand;
correction 4 was a newly-discovered material boundary, now re-confirmed clean.

CHRONOLOGY / AUTHORITY (binding — the two merges are distinct):
- PR #210 / merge `70700f7e4c2ee1d4ca40db5768c6c09a7f73e1a2` carried the
  packet-review evidence (the connector review events) and Dustin's ACCEPTED
  design direction, BUT the committed packet at that merge remained PROVISIONAL:
  its header read `STATUS: PROVISIONAL — NOT REVIEW-CLEAN` and its §17 was
  PENDING. PR #210 is therefore NOT the merged review-clean artifact.
- PR #212 / merge `3061ca53493649e7e4940c43f78016ba5f1d492c` committed the
  durable packet-local §17 record and changed the repository artifact to
  REVIEW-CLEAN. The durable GOV-2 §2/§7 gate is satisfied by the packet as
  committed through PR #212 — NOT by PR #210 alone. A downstream PRD's GOV-2
  "review-clean packet" prerequisite is satisfied by the packet at/after the
  PR #212 merge.
The design-direction RULING (the decision Dustin issued on the confirmed-clean
review, tied to PR #210) is DISTINCT from the durable CLOSEOUT (the committed
review-clean record, PR #212). This later corrective edit fixes only that
chronology/authority framing; it makes no new design decision.

NEXT PHASE (blocked pending re-confirmation): Stage-0 PRD drafting has BEGUN —
PRD-288 (PR #214) — but Dustin's Gate A on that PRD is BLOCKED until this amended
packet is re-confirmed REVIEW-CLEAN (§17). No implementation, PRD execution, or
contract/persistence change is authorized by this packet. Scope is unchanged from
the reviewed design: the daily `_run_pipeline` only; the hourly publish path
remains OUT OF SCOPE and deferred (§1 SCOPE, §9, §14). The PR #212 closeout and
the PR #213 chronology edit modified no design element; **correction 4 (this
amendment) DOES amend design** — it adds the intra-runtime carrier seam
(§2.1/§2.2) and a 6th production file `runtime/_types.py` (§11/§12/§14) — which is
exactly why it reopens the packet to DESIGN INCOMPLETE and requires an independent
exact-corrected-head re-confirmation before REVIEW-CLEAN is restored.

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

CORRECTION 4 (2026-08-05, Dustin-authorized "fix the packet first (GOV-2)" ruling
— a NEWLY DISCOVERED MATERIAL BOUNDARY OMISSION, GOV-2 §6/§7): the connector's
review of the downstream Stage-0 PRD-288 (PR #214) raised a P1 — the v0.1 seam
specified the `build_report_payload` parameter but never the INTRA-RUNTIME carrier
that moves the `SpyObservation` from `_run_pipeline` (where the ORB is built) to
the daily `build_report_payload` call (which runs after the pipeline returns, in
`_write_payload_artifacts(pipeline.contract)`, with only `contract` in scope).
Because `PipelineResult` (`runtime/_types.py`) had no observation field, a
contract key is forbidden (§4.3), and ORB recompute is forbidden (§2.3), the
5-file ceiling was not realizable. Corrected: the observation rides a NEW optional
`PipelineResult.spy_observation` field in `cuttingboard/runtime/_types.py` (a 6th
production file), threaded `_run_pipeline` → `execute_run` →
`_write_payload_artifacts` → `build_report_payload` (§2.1, §2.2, §11, §12, §14).
This is a MATERIAL boundary (a new production carrier surface), so — unlike
correction 3 — it returned the packet to DESIGN INCOMPLETE and required an
independent exact-corrected-head RE-CONFIRMATION of this amended head before
REVIEW-CLEAN could be restored and before Gate A on PRD-288 (§17; that
re-confirmation is now CLEAN). Every design
invariant is preserved (transient, no contract key, no persistence, one ORB
truth, additive param, hourly untouched); the only surface change is +1 carrier
file and +~5 LOC. Disposition for the PR #214 thread: ACTIONED by this amendment
(cite this commit); the PRD-288 FILES ceiling is realigned to 6 after this packet
is re-confirmed. Re-confirmation: the independent Codex exact-corrected-head
re-confirmation of the amended head `2e9d6a4` returned CLEAN ("Didn't find any
major issues"; §17), which RESTORES REVIEW-CLEAN (GOV-2 §7). Remaining downstream
step: realign PRD-288 (PR #214) FILES to the 6-file / ≤195-LOC ceiling once this
packet merges.

North Star lineage: NS-2A + NS-2C (ledger
`docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:132,134`), unblocked
by PRD-271 / NS-2B landing (PR #209). Evidence seed: `audits/stage0-recon-2026-07-20/`
(stage0-01 decision surface, verify-01). Materiality already ruled by the North
Star deep audit (TM-017).

---

## 0. Where this packet sits in the GOV-2 order

```
materiality check at intake ............................. DONE (MATERIAL; §15)
-> provisional material packet .......................... DONE (THIS DOCUMENT; landed via PR #210 @ 70700f7 in PROVISIONAL form)
-> independent Codex packet review ...................... DONE (event; PR #210 @ 16c2e40, 2026-08-05; findings dispositioned; §17)
-> one consolidated author correction .................. DONE (event; correction 2 @ 02202f7; single GOV-2 §2 cycle consumed)
-> Codex exact-corrected-head confirmation ............. DONE (event; bounded §6 local fix @ 1308871; Codex clean confirmation of 130887125bca; §17)
-> Dustin design-direction ruling ..................... DONE (ACCEPTED on the confirmed-clean review; tied to the PR #210 merge; daily-only, hourly deferred)
-> PR #210 merged (packet landed PROVISIONAL) ......... DONE (merge 70700f7; §17 PENDING in that tree — NOT the review-clean artifact)
-> packet REVIEW-CLEAN (PR #212) ...................... WAS DONE, then SUSPENDED by the material boundary below
-> material boundary omission found (downstream) ...... DONE (connector P1 on PRD-288 PR #214, 2026-08-05: intra-runtime carrier seam)
-> correction 4 (add PipelineResult carrier; 6th file) DONE (this amendment; §2.1/§2.2/§11/§12/§14; GOV-2 §6/§7 → DESIGN INCOMPLETE)
-> independent exact-corrected-head RE-CONFIRMATION ... DONE — CLEAN (Codex on 2e9d6a4; §17)
-> packet REVIEW-CLEAN RESTORED ....................... DONE on the branch; durable in main on the merge of PR #215
-> Stage-0 PRD drafting ............................... BEGUN (PRD-288, PR #214) — FILES realign to 6 once PR #215 merges
-> independent PRD review .............................. later
-> Dustin Gate A (on PRD-288) ......................... after PR #215 merges + PRD-288 FILES realign + independent PRD review
-> implementation ..................................... later
```

The packet was REVIEW-CLEAN via PR #212 (merge `3061ca5`), and Dustin's
design-direction ruling (ACCEPTED) — issued on the confirmed-clean review, tied to
the PR #210 merge — still stands. REVIEW-CLEAN was briefly SUSPENDED when
correction 4 (this amendment) added the intra-runtime carrier seam and a 6th
production file to close a material boundary omission the connector found on
downstream PRD-288 (PR #214). Per GOV-2 §6/§7 the packet was DESIGN INCOMPLETE
until an independent exact-corrected-head re-confirmation of the amended head
completed — which it now has, **CLEAN** on `2e9d6a4` (§17), so **REVIEW-CLEAN is
RESTORED** (durable in `main` on the merge of PR #215). Even so, no production
implementation, PRD execution, branch-for-implementation, or contract/persistence
change may begin; Gate A on PRD-288 follows only after PR #215 merges, PRD-288's
FILES are realigned to the 6-file / ≤195-LOC ceiling, and the independent PRD
review completes (GOV-2 §4).

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
- **Daily payload build path (current state — the seam v0.1 omitted).** The daily
  payload is written AFTER `_run_pipeline` returns: `execute_run`
  (`runtime/__init__.py:287`) calls `_write_payload_artifacts(pipeline.contract)`
  (`:2264`), which calls `build_report_payload(contract, ...)` (`:2271`).
  `_run_pipeline` returns `PipelineResult` (`cuttingboard/runtime/_types.py:55`),
  which carries `contract` and the decision surfaces but NO intraday-observation
  field. So the transient `intraday_metrics["SPY"].orb`, built inside
  `_run_pipeline` (`:1035`), is not reachable at the daily `build_report_payload`
  call site. (See §2.2 correction 4 for the added carrier.)

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
- **Intra-runtime carrier (PR #214 P1 — correction 4).** The parameter above says
  HOW `build_report_payload` receives the observation; this bullet says HOW the
  observation reaches that call, which the v0.1 packet left unspecified. The daily
  payload is built AFTER `_run_pipeline` returns (§2.1): `execute_run`
  (`runtime/__init__.py:287`) → `_write_payload_artifacts(pipeline.contract)`
  (`:2264`) → `build_report_payload` (`:2271`); the return carrier `PipelineResult`
  (`cuttingboard/runtime/_types.py:55`) has NO observation field, §4.3 forbids a
  contract key, and §2.3 forbids recomputing the ORB in `execute_run`. Therefore
  the transient `SpyObservation` is carried on a NEW optional field
  **`PipelineResult.spy_observation`** (`cuttingboard/runtime/_types.py` — a 6th
  production file, see §11/§14): `_run_pipeline` sets it on both the non-halt and
  daily-halt returns; `execute_run` forwards `pipeline.spy_observation` into
  `_write_payload_artifacts`, which forwards it into `build_report_payload`. The
  field is optional and defaults to `None`, so every non-daily caller (hourly
  writer, error path) is unchanged. This preserves every invariant (transient, no
  contract key, no persistence, one ORB truth, additive param, hourly untouched);
  it adds exactly one carrier file. Added by correction 4 under GOV-2 §6/§7.
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

Production (SIX files after correction 4 — the added carrier file is `runtime/_types.py`):

| Op | File | Purpose |
|---|---|---|
| A | `cuttingboard/spy_observation.py` (new) | `SpyObservation` carrier + `build_spy_observation` + session-VWAP + freshness state machine |
| M | `cuttingboard/ingestion.py` | new opt-in bounded full-session SPY fetch path; default contiguous behavior preserved |
| M | `cuttingboard/runtime/__init__.py` | build & thread `SpyObservation` on the **daily** `_run_pipeline` non-halt AND halt branches; set it on the returned `PipelineResult`; `execute_run` forwards `pipeline.spy_observation` into `_write_payload_artifacts` → the daily `build_report_payload` call. The hourly path (`_execute_notify_run`, `_write_hourly_artifacts`) is **NOT** modified — it keeps passing no observation (hourly scope-out, §1). |
| M | `cuttingboard/runtime/_types.py` | **(correction 4, PR #214 P1)** add ONE optional field `spy_observation: SpyObservation \| None = None` to the frozen `PipelineResult` dataclass — the intra-runtime carrier from `_run_pipeline` to the daily payload writer (§2.1/§2.2). Additive, defaults to `None`; no existing field or reader changes. |
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

**ESTIMATED SURFACE — NOT YET APPROVED: ≤ 195 net production LOC** across the six
production files (raised from ≤190/five by correction 4 for the carrier field).
Indicative split: `spy_observation.py` ~90; `ingestion.py` full-session path ~25;
`runtime/__init__.py` bridge (non-halt + halt + `PipelineResult` set/forward) ~32;
`runtime/_types.py` carrier field ~3; `payload.py` projection ~15;
`dashboard_renderer.py` card ~30. Test LOC is not counted against this ceiling. A
design that widens the fetch boundary, adds persistence, pushes into a contract
key, or requires a SEVENTH production file exceeds this estimate and is a
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
- A SEVENTH production file, or FILES / LOC growth past the §11/§12 six-file /
  ≤195-LOC ceiling → GOV-2 §5 stop-and-renew: amend the PRD, obtain fresh-context
  independent review of the exact amended revision, and Dustin's amended Gate A.
  (The 6th file `runtime/_types.py`, the intra-runtime carrier, is authorized by
  correction 4 under Dustin's 2026-08-05 "fix the packet first (GOV-2)" ruling —
  it is no longer a stop-and-amend trigger; a 7th file is.)

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

## 17. Packet review records (GOV-2 §2, §7 — prior cycle COMPLETE; RE-CONFIRMATION PENDING after correction 4)

### INITIAL PACKET REVIEW — COMPLETE
- Event type: `INITIAL PACKET REVIEW`
- Reviewer identity / capability role: independent Codex packet review by
  `chatgpt-codex-connector[bot]` (GitHub review 4860908412 on PR #210), the
  GOV-2 §2 auto-commissioned MATERIAL packet-review event.
- Reviewed commit SHA / packet revision:
  `16c2e403782bf7780cbd9aa91f53829979321b8e` (v0.1 + consolidated correction 1,
  findings F1–F5 applied).
- Review date: 2026-08-05T04:11:18Z.
- Verdict: findings raised (COMMENTED) — four findings, all confirmed valid:
  P1 (cover hourly dashboard publishes), P1 (define a carrier into the payload
  projection), P2 (resolve the zero-volume value invariant), P3 (mark the
  correction step consistently).
- Findings and dispositions: Dustin ruled "correct + scope out hourly" (GOV-2 §6
  "narrow its claim"); all four ACTIONED in consolidated correction 2 @
  `02202f7` (PR #210 issue comment 5187622641) — hourly publish path scoped OUT
  (§1 SCOPE/§2.2/§14; test T12); carrier threaded via
  `build_report_payload(contract, fixture_mode=False, *, spy_observation=None)`,
  not on the contract (§2.2/§4.2/§11); zero-volume invariant corrected so
  `price_vs_vwap="UNAVAILABLE"` is a valid OBSERVED token while `session_vwap`
  stays `None` (§4.1/§7.1/§8/T9); §0 order table corrected. This consumed the
  single GOV-2 §2 correction cycle.
- Fresh-context / independence / run-isolation evidence: independent connector
  review, not the packet-authoring session; SHA-pinned to `16c2e40`; read-only
  (documentation-only packet, no code to execute — GOV-2 §8 CI-claim boundary).
  Advisory per PRD-228; this committed §17 record is the durable GOV-2 §2 record,
  populated at Dustin's direction, not by the author certifying the gate.

### EXACT-CORRECTED-HEAD CONFIRMATION — COMPLETE
- Event type: `EXACT-CORRECTED-HEAD CONFIRMATION`
- Reviewer identity / capability role: independent Codex confirmation by
  `chatgpt-codex-connector[bot]` (PR #210).
- Corrected head SHA: `130887125bcac8952ea812d6e2dbcbd319515dcb` (final reviewed
  head). Intermediate confirmation of head
  `02202f76197d21586380612f0c8346d1f85bc491` (GitHub review 4861190633,
  2026-08-05T05:11:15Z) confirmed all four prior findings resolved and raised one
  NEW local P2 — `fixture_mode` dropped from the illustrative
  `build_report_payload` signature. That was a bounded GOV-2 §6 local
  signature/wording fix (LOCAL CORRECTION 3), NOT a material boundary omission,
  so the packet did not return to DESIGN INCOMPLETE (GOV-2 §7); `fixture_mode`
  was retained @ `1308871` (§2.2/§4.2/§11).
- Prior finding identifiers + dispositions being confirmed: initial-review P1
  (hourly), P1 (carrier→payload), P2 (zero-volume), P3 (status) — all confirmed
  resolved; plus the local P2 (fixture_mode) confirmed resolved at the final head.
- Review date: 2026-08-05T05:20:29Z (final confirmation of `1308871`).
- Verdict: CLEAN — Codex "Didn't find any major issues" on the exact final head
  `130887125b` (PR #210 issue comment 5187870539). Final CI green on the merged
  state (`main` @ `70700f7`, `test` job run 30977948437: 3224 passed, 1 xfailed).
- Fresh-context / independence evidence: independent connector confirmation,
  SHA-pinned to `1308871`, distinct from the packet-authoring session; scope was
  confirming the prior findings resolved, not a fresh broad review (GOV-2 §7).

### DESIGN-DIRECTION RULING, PR #210 MERGE, AND DURABLE REVIEW-CLEAN RECORD
- Dustin ACCEPTED the design direction (2026-08-05) after Codex's clean
  confirmation of the final head: the Stage-0 recommendation with binding scoping
  — daily `_run_pipeline` only; the hourly publish path deferred (§1 SCOPE, §9,
  §14). Recorded in the GOVERNING RULING header and §0. The ruling is a decision
  tied to PR #210; it is DISTINCT from the durable review-clean closeout below.
- PR #210 merge (GOV-1): merge commit
  `70700f7e4c2ee1d4ca40db5768c6c09a7f73e1a2`, 2026-08-05T05:23:14Z. IMPORTANT:
  that merge landed THIS packet in its PROVISIONAL form — its header read
  `STATUS: PROVISIONAL — NOT REVIEW-CLEAN` and §17 was PENDING. The
  review-clean-in-fact condition (Codex's clean confirmation) preceded the merge,
  but the durable packet-local record did not, and PR #210 is NOT the merged
  review-clean artifact.
- DURABLE REVIEW-CLEAN RECORD: this §17 record and the REVIEW-CLEAN status were
  committed to `main` via PR #212, merge
  `3061ca53493649e7e4940c43f78016ba5f1d492c` (2026-08-05). That is the commit
  that made the packet REVIEW-CLEAN in repository history. A downstream PRD's
  GOV-2 "review-clean packet" prerequisite is satisfied by the packet as
  committed through PR #212 — NOT by PR #210 alone. (This chronology framing was
  corrected in a small follow-up doc edit after PR #212 merged, resolving Codex's
  PR #212 P2; the review evidence, findings, corrections, scope, and design are
  unchanged.)
- NEXT PHASE: Stage-0 PRD drafting has begun (PRD-288, PR #214); Gate A is BLOCKED
  pending the correction-4 re-confirmation below.

### CORRECTION 4 — MATERIAL BOUNDARY OMISSION (found downstream) — ACTIONED
- Event type: `MATERIAL BOUNDARY OMISSION + CORRECTION` (GOV-2 §6/§7).
- Source: independent Codex review of downstream Stage-0 PRD-288 (PR #214),
  finding **P1** ("Add the missing transient carrier seam to FILES"),
  2026-08-05.
- Finding (valid): the v0.1 seam never specified the intra-runtime carrier from
  `_run_pipeline` to the daily `build_report_payload` call
  (`_write_payload_artifacts(pipeline.contract)`), and `PipelineResult`
  (`runtime/_types.py`) had no observation field — so the 5-file ceiling was not
  realizable without a contract key (forbidden §4.3) or an ORB recompute
  (forbidden §2.3).
- Disposition: Dustin ruled "fix the packet first (GOV-2)" (2026-08-05).
  Correction 4 adds the optional `PipelineResult.spy_observation` field in
  `cuttingboard/runtime/_types.py` (6th production file) as the carrier, threaded
  `_run_pipeline` → `execute_run` → `_write_payload_artifacts` →
  `build_report_payload` (§2.1/§2.2/§11/§12/§14). All design invariants preserved.
- GOV-2 classification: MATERIAL boundary → the packet returned to DESIGN
  INCOMPLETE; REVIEW-CLEAN suspended until re-confirmation (now CLEAN, below).

### EXACT-CORRECTED-HEAD RE-CONFIRMATION (of correction 4) — COMPLETE (CLEAN)
- Event type: `EXACT-CORRECTED-HEAD CONFIRMATION` (GOV-2 §7).
- Reviewer identity / capability role: independent Codex confirmation
  (`chatgpt-codex-connector[bot]`), requested on the correction-4 amendment
  PR #215.
- Corrected (design) head SHA: `2e9d6a422f940d07516f5ff011005689a048a881` — the
  head carrying correction 4's design (§2.1/§2.2/§11/§12/§14). This §17 record +
  the REVIEW-CLEAN restoration are committed on top of that head (record-only, no
  design change after the re-confirmed head), durable in `main` on the merge of
  PR #215.
- Scope: confirmed ONLY that correction 4's carrier seam resolves the PR #214 P1
  and introduces no new material boundary — not a fresh broad review.
- Review date: 2026-08-05.
- Verdict: **CLEAN** — Codex "Didn't find any major issues" on `2e9d6a422f`.
- Fresh-context / independence evidence: independent connector confirmation,
  SHA-pinned to `2e9d6a4`, distinct from the amendment-authoring session.
- Effect: RESTORES REVIEW-CLEAN. Gate A on PRD-288 is unblocked only after PR #215
  merges AND PRD-288's FILES are realigned to 6 files / ≤195 LOC AND the
  independent PRD review completes.

A corrected head without independent SHA-pinned confirmation is not
review-clean (GOV-2 §2). This §17 block is the durable, packet-local, SHA-pinned
GOV-2 §2/§7 record; the advisory connector threads on PR #210/#214/#215 do not by
themselves satisfy the gate — the committed records here do. Both cycles (the
PR #212 cycle and correction 4's re-confirmation) stand.

---

END OF PACKET v0.1 — REVIEW-CLEAN (RESTORED after correction 4 re-confirmation,
2026-08-05; durable in `main` on the merge of PR #215). The packet was
REVIEW-CLEAN via PR #212 (merge `3061ca5`), and Dustin's ACCEPTED design-direction
ruling still stands; correction 4 (this amendment) added the intra-runtime carrier
seam + a 6th production file (`runtime/_types.py`) to close a material boundary
omission the connector found on downstream PRD-288 (PR #214 P1), on Dustin's "fix
the packet first (GOV-2)" ruling. Per GOV-2 §6/§7 that briefly returned the packet
to DESIGN INCOMPLETE; the independent exact-corrected-head RE-CONFIRMATION of the
amended head `2e9d6a4` returned CLEAN (§17), restoring REVIEW-CLEAN. PR #210
remains the provisional-merge + ruling; the durable review-clean record is the
PR #212 cycle plus correction 4's re-confirmation. Gate A on PRD-288 follows PR
#215's merge, the PRD-288 FILES realign (5→6), and the independent PRD review.
