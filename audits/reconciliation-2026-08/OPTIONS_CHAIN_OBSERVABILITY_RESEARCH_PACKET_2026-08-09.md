# OPTIONS CHAIN OBSERVABILITY — RESEARCH PACKET (2026-08-09)

RESEARCH ONLY. This packet allocates no PRD, opens no Stage-0, changes no
schema or contract, grants no implementation authority, changes no feature
priority, selects no provider, and does not alter the standing GEX state
(`EVIDENCE INCOMPLETE`, per the GEX-0 packet §1 — the packet verdict, not
the stale PROJECT_STATE framing). Merge of this file is held for Dustin
like every PR.

LABELS. Per the commissioning charge, every load-bearing claim is one of:
**FACT** (verified in-repo or from a real captured source), **INFERENCE**
(reasoned from facts, could be wrong), **DESIGN HYPOTHESIS** (a proposal
the owner may reject), **OWNER DECISION REQUIRED**. Provider-side claims
additionally carry the GEX-0 evidence fences: `search-derived — NOT
doctrine-grade evidence` (WebSearch result text; neither current provider
documentation read directly nor a real API response) and `MEMORY — NOT
EVIDENCE`. Nothing here advances the GEX-0 provider-evidence rows.

EXECUTION NOTE (honest provenance). Commissioned Codex seats route through
the asher remote-control bridge per Dustin's ruling this session. At
drafting time the bridge was not yet connected; sections that await the
Codex primary-doc confirmation pass are fenced `CODEX-CONFIRMATION
PENDING`. The adversarial pre-commit pass runs when the bridge is up.
House-style note: the charge mandates these 15 sections and the four
labels above; where this diverges from the 14-section planning template,
the charge governs (deliberate, not drift).

---

## 1. EXECUTIVE FINDING

**The useful primitive is NOT "an options chain." It is a small set of
deterministic OBSERVATIONS computed from the chain as raw input.**
(DESIGN HYPOTHESIS, but every line of evidence below points the same way.)

- The cognitive cost Dustin pays today is *reading and comparing chain
  rows himself*. Reproducing the chain in Cuttingboard would reproduce
  the cost. The compression that pays is: **one selected-contract
  observation, one expiry-level observation, one underlying-volatility
  observation, one market-quality observation** — each with typed
  unavailability — rendered at three altitudes (underlying → expiry →
  contract).
- **The repo is further from this than the commission assumed on the
  provider side, and closer than it assumed on the plumbing side.**
  (FACT, §3): there is no Polygon client, no IV, no Greeks, no realized
  vol anywhere in code — but the chain-fetch seam, quote-age concept,
  typed-unavailable patterns, snapshot-compare lifecycle, and
  notification dedupe machinery all exist and are directly reusable.
- **The first-slice OPTIONS OBSERVATION CARD hypothesis survives with
  three material amendments** (§11): bid/ask/spread/quote-age is
  entitlement-gated at the provider (search-derived), IV−RV must be
  horizon-disclosed or typed-unavailable (§5), and Greeks beyond delta
  are provider-model-derived and must carry provenance labels.
- **The two tracks (GEX, options observability) share more than raw
  data — they share the same unresolved evidence blocker.** (FACT, §10):
  GEX-0's verdict is fixed at `EVIDENCE INCOMPLETE` solely by egress
  denial; every provider-dependent claim in this packet is behind the
  same wall. One owner-granted evidence pass could serve both tracks'
  data-contract needs without coupling their authority.

## 2. USER PROBLEM

(FACT, from the commission.) Inspecting options today requires manual
cognition: reading raw chain rows, judging bid/ask quality, comparing
strikes and expirations, interpreting IV with no RV context, no data-
quality checks, no change detection. High mental dexterity for little
information gain.

**The VISION tension, argued rather than assumed.** VISION's "system
serves the trader" test says a feature that does not change a decision
should not exist, and warns against "intellectual comfort dressed as
progress." The sidecar doctrine's counter-rule says the human reader is
a valid consumer. The honest resolution for this surface (INFERENCE):
options-chain reading is cognition Dustin **already spends** at his
broker before acting. An observation surface that compresses an existing
manual act is not new information comfort — it is cost reduction on a
decision path already in use, exactly like the watchlist sidecar
precedent. The test each candidate observation must pass in §7 is
therefore: *does it replace a manual chain-reading step, or merely
decorate one?* Candidates that only decorate are marked DELIBERATELY
OMITTED in §9.

## 3. EXISTING REPO STATE

All FACT (session repo archaeology; exact cites retained; SCHEMA_MAP and
CALL_SITE_MAP contain zero options/volatility entries — a recon-map gap
to fix whenever a future slice lands, not before).

**What exists:**
- `cuttingboard/options.py` — strategy-label generator (spread type ×
  VIX band, relative strikes like `"ATM-5.00"`, hardcoded $5/$2.50
  strike distance, 0.30×width debit heuristic). Emits no market data.
- `cuttingboard/chain_validation.py` — the ONLY live chain fetcher:
  yfinance primary, yahooquery fallback. Reads bid/ask/OI/volume/strike
  for one ATM-ish contract per symbol; computes mid and spread_pct
  internally; classifies liquidity into a 5-value vocabulary. **Its
  computed bid/ask/mid never escape the module** — no consumer can see
  an actual quote today.
- `cuttingboard/flow.py` — the richest options schema in the repo
  (strike, type, premium, side, sweep, moneyness), fully implemented,
  fully tested, permanently `NO_DATA` (config ships no `data_path`).
- Volatility surface = a 4-label VIX band (`classify_iv_environment`)
  that **silently returns NORMAL_IV when VIX is None** — a fabricated
  default, explicitly NOT reusable for a display card — plus ATR14.
  yfinance's `impliedVolatility` chain column is deliberately unread.
- **No Polygon client exists.** `POLYGON_API_KEY` is exported in
  `cuttingboard.yml` and `hourly_alert.yml` and read by zero code
  (known finding F-22/CB-42). The prior Polygon integration was removed
  ("never used in production", DECISIONS heading 2026-06; a 109-exposure
  query-string key leak was remediated by rotation — any future auth
  MUST be header-based, never `?apiKey=`).
- **No realized-vol calculator, no Greeks, no IV, no GEX code, no
  rate limiter, no entitlement handling, no options artifact under
  `logs/`.**

**Reusable primitives a future slice would build on (FACT):**
- Quote-age: `NormalizedQuote.age_seconds` + three-tier freshness
  (300s/900s/clock-skew guard); per-surface staleness budget precedent
  (`spy_observation`: 180s, deliberately its own).
- Typed-unavailable: `spy_state.py` strict-XOR frozen dataclass with
  closed reason vocabulary (the strongest template); market-control-card
  per-cell XOR; trend_structure prioritized token propagation.
- Snapshot compare: `market_map_lifecycle.inject_lifecycle` (pure
  two-snapshot diff → NEW/UNCHANGED/UPGRADED/DOWNGRADED + removed) and
  notification state/dedupe/priority machinery.
- Fetch layer: retries/timeouts, trading-day-keyed parquet OHLCV cache,
  `block_live_data()` fence, per-source priority. **No rate limiting** —
  a gap any per-contract provider would expose immediately.
- Card idioms: `watchlist_sidecar` (pure, no-I/O, explicitly
  no-decision-surface) is the closest describe-don't-predict template;
  `_load_contract_entry_context` is the natural per-ticker join seam.

**Dangerous couplings a future slice must design around (FACT):**
- `_validated_chain_result()` fabricates a VALIDATED pass for missing
  chain data inside the decision chain — an observation surface must
  never inherit this default.
- `iv_environment` is a decision input (steers strategy selection), not
  an observation; a display card must compute its own typed-unavailable
  IV state, never call `classify_iv_environment`.
- "Spread" already means two things (`spread_width` = estimated debit;
  `spread_pct` = bid-ask). A quote-spread observation makes three —
  naming discipline required.
- Contract schema (`contract_types.py`) is guard-enforced with zero
  options fields; payload section keys are test-pinned; `option_setups_
  detail`/`chain_results_detail` payload sections are MISNAMED
  re-projections of trade candidates carrying no chain data.
- Banned-import walls: `reports/levels.py`, `market_map.py`,
  `reports/premarket.py` may not reach any fetcher.

## 4. PROVIDER / DATA REALITY

Scope fence (FACT): the standing Polygon boundary is governance about
the FUTURE provider; the incumbent runtime reality is yfinance/
yahooquery. The load-bearing repo finding is that mismatch — an unused
`POLYGON_API_KEY` in workflow config beside a yfinance fetcher — not
any branding question. Provider naming: rebrand Polygon→Massive
(announced Oct 2025; `api.polygon.io` remains valid, `api.massive.com`
parallel) is provider-context metadata only (search-derived;
CODEX-CONFIRMATION PENDING).

**Field classification.** Everything below is `search-derived — NOT
doctrine-grade evidence` unless marked otherwise; the entire table is
CODEX-CONFIRMATION PENDING and none of it advances GEX-0's 16 rows.

| Field | Classification (per charge vocabulary) | Notes |
|---|---|---|
| Underlying, expiration, strike, call/put | DIRECTLY PROVIDED | Contract metadata; reference + snapshot endpoints; index underlyings via `I:` prefix (SPX etc.), some indices paid-tier |
| Bid / ask / quote timestamps | DIRECTLY PROVIDED **and** ENTITLEMENT-DEPENDENT | Snapshot returns last_quote "only if your plan includes quotes"; lower options tiers reportedly exclude quotes/trades entirely |
| Last trade / trade timestamp | DIRECTLY PROVIDED and ENTITLEMENT-DEPENDENT | Same gating pattern |
| Day volume | DIRECTLY PROVIDED | Day aggregates in snapshot |
| Open interest | DIRECTLY PROVIDED, FRESHNESS-CONSTRAINED | "Quantity held at the end of the last trading day" — an EOD quantity, never intraday-fresh; exact publication time SEMANTICS UNCLEAR |
| Implied volatility | DIRECTLY PROVIDED, SEMANTICS UNCLEAR | Provider-computed (binomial model per search-derived docs); model inputs/rate assumptions undocumented at this evidence level; absent for some contracts (deep ITM noted) |
| Delta, gamma, theta, vega | DIRECTLY PROVIDED, SEMANTICS UNCLEAR | Provider-model-computed, not exchange-sourced — the GEX-0 packet's "derived-of-derived" concern (row 3) applies verbatim; may be absent per-contract |
| Midpoint, spread, spread% | DERIVABLE | From bid/ask when entitled; trivial arithmetic |
| Quote age | DERIVABLE | From quote timestamp vs observation time; needs timestamp-semantics confirmation (TZ, epoch units) |
| Moneyness, intrinsic, extrinsic | DERIVABLE | Needs fresh underlying spot + contract metadata (+ entitled quote for extrinsic); see §5 |
| Realized volatility (any window) | HISTORY REQUIRED — **computable today** | From underlying daily OHLCV; the repo already fetches/caches underlying history via yfinance (FACT). Does not require the options provider at all |
| IV history / IV rank / percentile | HISTORY REQUIRED, likely UNAVAILABLE as a service | No stored IV time series exists in-repo; constant-maturity IV history would have to be accumulated locally (≥ ~252 obs) or found as a provider product (unverified) |
| Real-time vs 15-min delayed status | ENTITLEMENT-DEPENDENT, UNVERIFIED | GEX-0 row 8's own fence stands: do not assume real-time |
| Rate limits per plan | SEMANTICS UNCLEAR | Historical in-repo fact: free tier was 5 req/min for the REMOVED equities integration (PRD-history doc; not current options truth) |
| Licensing: caching/persistence/public display | UNAVAILABLE at this evidence level | GEX-0 row 11 flagged this viability-critical for the public Pages dashboard; identical concern here |

**Consequences (INFERENCE):**
- A quality-honest card *requires* quotes; if the chosen plan tier
  excludes them, the MARKET block of the first slice is typed-
  unavailable by construction, not degraded silently. Plan choice is
  therefore a product decision, not an ops detail (→ §13, OBS-D3).
- OI is an EOD number: rendering it beside live-ish quotes without an
  as-of label would be a freshness lie. Every OI display carries its
  as-of date.
- The incumbent yfinance path already delivers bid/ask/OI/volume for
  one contract per symbol with no entitlement wall (FACT) — a
  first slice could be evidenced against the incumbent seam while the
  Polygon evidence pass waits (DESIGN HYPOTHESIS; owner's provider
  boundary governs, → OBS-D2).

## 5. VOLATILITY DEFINITIONS

Seat C. Definitions are FACT (standard, institutionally documented);
availability claims inherit §4's fences; display judgments are DESIGN
HYPOTHESIS. IMPLIED and REALIZED are kept conceptually separate
throughout; no composite volatility score exists or is proposed.

**Implied volatility (IV).** The volatility parameter that makes an
option-pricing model reproduce the observed option price. Inputs: option
price, spot, strike, DTE, rate/dividend assumptions, model (provider
uses a binomial model per §4). Forward-looking over the contract's
remaining life; quoted annualized. Failure modes: missing/crossed
quotes → no defensible IV; deep-ITM contracts may return none;
model/rate assumptions are the provider's, not observable. Typed-
unavailable: `IV_UNAVAILABLE(provider_absent | quote_quality |
stale_quote)`. Displayable without recommendation: yes — a number with
provenance ("provider-computed, binomial") and as-of time.

**Realized/historical volatility (RV).** Annualized standard deviation
of daily log returns of the UNDERLYING over a trailing window:
`RV_N = stdev(ln(P_t/P_{t-1}), N trading days) × √252`. Inputs: daily
closes (already cached in-repo). Window tradeoffs: RV10 reactive/noisy;
RV20 (~1 trading month) the conventional default; RV60 regime-scale.
Failure modes: splits/dividends (use adjusted closes), gaps, N too
small (`INSUFFICIENT_HISTORY` — the repo already has this token
pattern). Displayable: yes — pure description of the past.

**IV vs RV comparability (owner amendment 1 — the horizon problem).**
IV and RV are only comparable when three conventions are disclosed:
1. **Annualization**: both must be annualized on the same basis.
   Practitioner RV uses √252 (trading days); provider IV annualization
   convention is SEMANTICS UNCLEAR at this evidence level
   (CODEX-CONFIRMATION PENDING) — if the provider annualizes on
   calendar time, a constant ~√(365/252) ≈ 1.20 scaling ambiguity
   contaminates the difference.
2. **Direction of time**: IV is forward over the contract's remaining
   life; trailing RV is backward. `IV − RV` is therefore NEVER a
   like-for-like difference — it is a *descriptive juxtaposition* of a
   forward market parameter against recent history, and the label must
   say which history: **`IV − RV20` (or the chosen window), never a
   generic `IV − RV`.**
3. **Horizon match**: an expiry-specific IV (say 45 DTE) juxtaposed
   with RV20 mixes horizons. Options: (a) fixed disclosed window
   (simple, honest, slightly mismatched); (b) DTE-matched trailing
   window (RV over ≈ DTE trading days: `N ≈ DTE × 252/365`) — tighter
   semantics, more variants to validate, degenerate for short DTE
   (N < ~10 → INSUFFICIENT_HISTORY).
   **DESIGN HYPOTHESIS:** first slice uses fixed `RV20` with the
   window in the label and the contract's DTE displayed adjacent, so
   the mismatch is visible rather than hidden; DTE-matched RV is a
   later refinement if the owner wants it. If annualization basis
   cannot be confirmed, the difference renders as
   `COMPARABILITY_UNVERIFIED` (typed) rather than a bare number.
   A ratio IV/RV adds no descriptive information beyond the difference
   and invites "rich/cheap" reading — DELIBERATELY OMITTED.

**Term structure by expiration.** ATM-reference IV per expiry, listed
in expiry order. Deterministic and descriptive (which expiries price
more volatility). Requires an ATM-selection rule (nearest-to-spot
strike; ties → disclosed rule) — a definition choice, not a threshold.
Failure modes: sparse expiries, missing IV on the ATM contract
(propagate typed-unavailable per expiry, never interpolate).
Displayable: yes, as a list/strip — ordering words like
"backwardation" carry predictive flavor and are omitted; the numbers
speak.

**Skew/smile.** IV across strikes within one expiry. Descriptive but
the heaviest surface here: needs many strikes with quality IV, and
compressing it to one number (e.g. 25-delta risk reversal) imports
model-dependent conventions. DESIGN HYPOTHESIS: out of first slice;
neighboring-strike IV values (raw, unsummarized) cover the immediate
cognitive need.

**ATM-reference IV.** The IV of the nearest-to-spot strike (disclosed
rule) — the anchor for expiry cards and term structure. Fails typed
when spot is stale or the ATM contract's IV is absent.

**IV rank / percentile.** Defensible ONLY with ≥ ~1 year of
same-underlying, same-methodology IV history. No such history exists
in-repo (FACT) and no provider IV-history product is verified at this
evidence level. Until a local daily IV observation series accumulates
(a cheap byproduct of any daily options artifact), IV rank is
`INSUFFICIENT_HISTORY` by construction. DESIGN HYPOTHESIS: omit from
first slice; note that persisting daily IV observations starts the
clock.

**Descriptive price decomposition (owner amendment 2).**
- *Moneyness*: S−K (or %) with the convention disclosed. DERIVABLE;
  cheap; directly replaces a manual comparison step. Include.
- *Intrinsic value*: max(S−K, 0) calls / max(K−S, 0) puts. DERIVABLE
  from spot + strike; fails typed when spot stale/missing.
- *Extrinsic (time) value*: mid − intrinsic. Requires an entitled,
  fresh quote AND fresh spot; negative extrinsic is a data-quality
  signal (stale legs), not a trading observation — route it to §6.
- *Premium composition* (intrinsic/extrinsic split of the mid): the
  same two numbers rendered as a split; no separate machinery.
- *Put/call parity residual*: as a QUALITY-CHECK CONCEPT ONLY —
  C − P − (S − K) ignoring carry, materially nonzero → suspect quotes
  somewhere in the triple. Needs rate/dividend honesty to be exact;
  as an inexact residual it is a *coarse anomaly flag*, and any
  threshold on it is an owner/config decision. DESIGN HYPOTHESIS:
  defer; sparse-quote entitlement makes it moot if quotes are absent.
- **Excluded by charge and by VISION**: theoretical fair value,
  cheap/expensive labels, mispricing claims, expected returns,
  strategy valuation. The decomposition describes *what the premium
  is made of*, never *what it should be*.

## 6. DATA-QUALITY HAZARDS

Seat D. The taxonomy is FACT-shaped (deterministic, definitional);
which checks gate display is DESIGN HYPOTHESIS; every
threshold-shaped parameter is explicitly an owner/config decision — no
numeric thresholds are proposed anywhere in this section.

**The central distinction: OBSERVED ZERO ≠ UNAVAILABLE.** A bid of 0
with a live ask is a market fact (no buyer) — display it. A missing bid
field is an unknown — typed-unavailable. Volume 0 is a fact (nothing
traded); volume absent is unknown. OI 0 is a fact (no open contracts);
OI absent is unknown. The incumbent yfinance path returns NaN-ish
blanks that conflate these (INFERENCE from its DataFrame semantics —
the first slice must normalize at ingestion into an explicit
`value | OBSERVED_ZERO | UNAVAILABLE(reason)` cell, reusing the
market-control-card XOR-cell pattern.

**Quality states (each with its trigger and its typed token):**
- `STALE_QUOTE` — quote timestamp older than the surface's own
  staleness budget (per-surface budget precedent: `spy_observation`;
  the budget VALUE is an owner/config decision).
- `MISSING_BID` / `MISSING_ASK` / `MISSING_QUOTE` — field absent or
  entitlement-excluded; entitlement exclusion gets its own reason
  (`NOT_ENTITLED`) so the card never implies the market lacked a quote
  when the PLAN lacked it.
- `ZERO_BID` — observed fact; renders as 0 with a "no bid" annotation,
  and mid/spread computations from it are qualified (mid of 0×ask is
  not a price).
- `CROSSED_MARKET` (bid > ask) / `LOCKED_MARKET` (bid = ask) —
  deterministic booleans; crossed ⇒ derived mid/spread suppressed.
- `WIDE_SPREAD` — definitionally spread%; "wide" requires a threshold
  ⇒ display the spread% always, flag only if the owner configures a
  bound (the repo's existing `_SPREAD_PASS/WEAK` constants are
  DECISION-side thresholds and must not silently become display
  thresholds).
- `MISSING_UNDERLYING` / `STALE_UNDERLYING` — spot absent/stale voids
  moneyness, intrinsic, extrinsic, ATM selection: one upstream failure
  fans out; propagate with the trend_structure priority pattern.
- `ZERO_VOLUME` / `ZERO_OI` — observed facts, displayed as zeros with
  as-of labels (OI is EOD by nature, §4).
- `MISSING_IV` / `MISSING_GREEKS` — provider-absent (legitimately, per
  §4); reason distinguishes provider-absent from quote-quality-refused.
- `SPARSE_STRIKES` / `SPARSE_EXPIRIES` — coverage counts are facts;
  "sparse" is a threshold ⇒ display counts, no judgment.
- `ANOMALOUS_NEIGHBOR` — non-monotonic option prices across adjacent
  strikes (calls should be non-increasing in strike, puts
  non-decreasing) — a deterministic ordering check with no threshold;
  a violation is a quality flag on the DATA, phrased as such.
- `EXPIRY_EDGE` — DTE ≤ 0 or expiry-day contracts: settlement
  semantics differ, quotes decay to intrinsic; the card labels the
  state rather than interpreting it.

**Where typed-unavailable is REQUIRED (not optional):** IV (§5), the
IV−RV comparison (§5), extrinsic value (two freshness dependencies),
every entitlement-gated field, and everything downstream of underlying
spot. The `spy_state` strict-XOR dataclass is the template: a cell is
a value or a closed-vocabulary reason, never a default, never NaN,
never a fabricated NORMAL (the `classify_iv_environment` None→NORMAL_IV
behavior is the named in-repo anti-pattern this surface must not
repeat).

## 7. CANDIDATE OBSERVATIONS

Seat E/§2 test applied: each candidate names the manual act it
replaces. All DESIGN HYPOTHESIS.

| Observation | Replaces (manual act) | Inputs | Verdict |
|---|---|---|---|
| Selected-contract card: bid/ask/mid/spread%/quote-age | Reading raw rows + judging quote quality by eye | Entitled quote + clock | CORE |
| Liquidity pair: volume (today) + OI (as-of EOD date) | Scanning two columns and remembering which is stale | Snapshot | CORE |
| IV with provenance + `IV − RV20` (labeled, §5 discipline) | Interpreting a bare IV% with no context | Provider IV + repo OHLCV | CORE (typed-unavailable rich) |
| Moneyness + intrinsic/extrinsic split | Mental arithmetic per contract | Spot + strike + mid | CORE-ADJACENT (cheap, descriptive) |
| Delta (other Greeks secondary) | Reading the Greeks block | Provider Greeks | SECONDARY — provider-model provenance label mandatory |
| Expiry card: ATM-ref IV + strike/quote coverage counts + DTE | Comparing expirations by scrolling chains | Chain snapshot per expiry | CORE at expiry altitude |
| Term-structure strip (ATM IV by expiry, ordered) | Cross-expiry comparison | Multiple expiry cards | STRONG — derived free from expiry cards |
| Neighboring-strike strip (±N strikes: mid, IV, OI) | The strike-comparison scan | Chain slice | STRONG at contract altitude; N is config, not threshold |
| Quality state block (§6 states, one line) | The judgment "can I trust this row at all?" | All of the above | MANDATORY — the honesty surface |
| Volatility context card (underlying): RV10/20/60 + IV ref | "What regime is this underlying's vol in?" — currently answered nowhere | OHLCV (+ IV) | STRONG; RV side computable TODAY with zero provider dependency (FACT) |

DELIBERATELY OMITTED (fail the §2 test or the charge's boundaries):
full-chain reproduction, IV/RV ratio, IV rank (until history exists,
§5), skew summaries, composite quality "scores", any ranking of
contracts, anything labeled rich/cheap.

## 8. CANDIDATE CHANGE EVENTS / ALERTS

Seat F. Research candidates ONLY — none is an approved alert; no
numeric thresholds are assigned; "materially" is everywhere an
owner-configured bound. All DESIGN HYPOTHESIS. Repo machinery that
would carry them exists (FACT): snapshot-compare (`inject_lifecycle`
pattern), notification state/dedupe/priority, slot idempotency.

| Event | State required | False-positive hazards | Threshold problem | User-config preferable? | Interrupt-worthy? |
|---|---|---|---|---|---|
| Quote became stale | Last observation + staleness budget | Weekend/half-day calendars; provider hiccup vs market close | Budget value | Yes | No — badge on next view |
| Liquidity disappeared (bid vanished / spread blew out) | Previous quote snapshot | Auction opens/closes; single bad tick | "Blew out" bound | Yes | Only for a HELD contract |
| IV changed materially | Previous IV observation | Provider recompute artifacts; quote-quality flicker feeding model | Change bound | Yes | Rarely |
| IV−RV differential changed materially | IV + RV series | Two moving parts — RV window roll alone moves it; double-counting IV moves | Compound bound | Yes | Rarely |
| Skew changed | Two chain snapshots wide enough for skew | Sparse strikes make skew jumpy | Definition AND bound | Yes | No (and skew is out of first slice) |
| Term-structure ordering changed (adjacent-expiry IV inversion flip) | Prior term strip | ATM re-selection near strike boundaries flips the anchor, not the market | Ordering is binary — the honest kind — but anchor rule must be pinned first | Partly | Possibly — it is discrete and rare |
| Selected contract changed liquidity regime | Prior quality-state block | Regime = classification ⇒ inherits its thresholds | Inherited | Yes | For a held contract |
| User-defined condition crossed | The user's own predicate + prior state | User's problem, honestly | None — user owns it | **This is the cleanest alert of all** | User decides |

INFERENCE: the only structurally clean near-term alerts are the
*binary/discrete* ones (ordering flip, user-defined crossing) and
*held-contract* quality degradation. Continuous-magnitude alerts
("changed materially") all devolve to owner-tuned bounds and belong
behind user configuration if they exist at all. Change detection
without interruption (a "since yesterday" delta column on cards, via
the lifecycle-compare pattern) delivers most of the value with zero
alert ceremony — DESIGN HYPOTHESIS worth the owner's attention.

## 9. COMPRESSION / UX ALTERNATIVES

Seat E. All DESIGN HYPOTHESIS. Shapes compared against the three
mandated altitudes:

- **Compressed chain** (fewer columns, all rows): REJECTED — it is the
  brokerage chain with less ink; the reading cost survives.
- **Selected-contract card** (§7 CORE rows + quality block + neighbor
  strip): the contract-altitude winner. One contract is what Dustin is
  actually deciding about.
- **Expiry card** (ATM-ref IV, coverage counts, DTE, quality): the
  expiry-altitude winner; the term-structure strip falls out of a row
  of them.
- **Volatility context card** (underlying altitude: RV ladder + IV
  reference + `IV − RV20`): answers "what vol regime am I operating
  in" before any contract is chosen; its RV half needs no provider.
- **Neighboring-strike strip / term-structure strip**: context bands
  INSIDE the two cards above, not standalone surfaces.

**Classification (per charge):**
- ALWAYS VISIBLE: quality state; bid/ask/mid/spread% + quote age (or
  their typed-unavailable); DTE; moneyness; volume + OI with as-of.
- SECONDARY/EXPANDABLE: Greeks beyond delta; intrinsic/extrinsic
  split; neighbor strip; RV window ladder beyond the labeled default.
- ALERTABLE (candidates only, §8): quality degradation on a held
  contract; user-defined conditions; ordering flips.
- DELIBERATELY OMITTED: full chain; ratios/ranks/scores; skew
  summaries; anything predictive-flavored.

**Architectural answer (the commission's IMPORTANT QUESTION):** treat
the chain as RAW INPUT; the product surface is the three cards. The
chain itself is never rendered. This also matches the sidecar
doctrine mechanically: one producer, one versioned observation
artifact (future work), renderer as consumer, zero contract mutation.

## 10. GEX OVERLAP — SHARED DATA, SEPARATE AUTHORITY

FACT unless noted:
- Standing GEX state: `EVIDENCE INCOMPLETE` (GEX-0 packet §1). This
  packet cites the packet verdict and does not touch the four stale
  docs that contradict it (TD-1/QW-4, already dispositioned FIX NOW in
  the engineering-health packet).
- Both tracks read the same raw surface (an options chain snapshot
  with IV/Greeks/OI). Neither depends on the other: GEX aggregates
  gamma across the chain into levels; observability renders per-
  contract/per-expiry descriptions. No shared code exists yet; nothing
  here creates any.
- **They share the same evidence blocker.** GEX-0's verdict is fixed
  at INCOMPLETE solely by egress denial (all 16 rows `unavailable —
  egress blocked`); every provider-dependent row in §4 is behind the
  same wall. INFERENCE: one owner-commissioned provider-evidence pass
  (the GEX-D1 egress grant) would produce the captured real responses
  BOTH tracks need. That is evidence-sharing, not authority-sharing:
  GEX resumption still requires GEX-D1+GEX-D2; this track's future
  requires its own rulings (§13). Neither track's gate opens the
  other's.
- Greeks provenance cuts differently per track (INFERENCE): for GEX,
  model-derived gamma makes the headline number derived-of-derived
  (GEX-0 row 3, material to its doctrine). For observability, a
  provider-computed delta is displayable AS a labeled provider quantity
  — provenance honesty, not viability risk.
- ODATA seam (FACT): the workplan's options-data recon packet
  (ODATA-0, `EVIDENCE BLOCKED`) is gated on a predecessor already
  SUPERSEDED — an unresolved ledger seam. This packet is a NEW
  owner-commissioned research track, not ODATA-0; whether the two
  merge, and whether ODATA-0's gate is re-pointed, is OWNER DECISION
  REQUIRED (OBS-D1). Per doctrine §8, this packet stops at naming the
  seam rather than choosing an interpretation.

## 11. MINIMUM PLAUSIBLE FIRST SLICE

DESIGN HYPOTHESIS throughout; explicitly NOT authorized by this packet.

**The commissioned card hypothesis, falsification result:** SURVIVES
WITH AMENDMENTS. Field-by-field: CONTRACT block stands (metadata,
directly provided). MARKET block stands ONLY under a quotes-entitled
plan; otherwise typed `NOT_ENTITLED` (§4). LIQUIDITY stands with the
OI as-of-EOD label. VOLATILITY stands with the §5 label discipline
(`IV − RV20`, comparability-typed). SENSITIVITY: delta with provenance
label; other Greeks secondary. CONTEXT stands (neighbor strip, term
strip). QUALITY was the hypothesis's best idea and becomes mandatory.

**Smallest coherent slice** (INFERENCE from §7 verdicts): the
**underlying volatility-context card's RV half plus the quality
discipline**, because it is computable TODAY from cached OHLCV with
zero provider dependency, zero entitlement question, and zero GEX
adjacency — followed by the selected-contract card once provider
evidence lands. But slicing decisions belong to a PRD that does not
exist; this is a shape, not a plan.

**What any slice needs first (all owner-held):** provider-evidence
pass (or an explicit ruling to evidence against the incumbent yfinance
seam), plan/entitlement choice, and the §13 rulings. A producer slice
is expected MATERIAL (§14).

## 12. WHAT NOT TO BUILD

The charge's boundaries, made structural (all bind any future PRD):
no strategy engine, no composite scores, no contract ranking, no
buy/sell/signal output, no expected-return or fair-value estimates, no
rich/cheap/mispriced vocabulary, no alert thresholds baked into code
(owner/user configuration only), no full-chain rendering, no provider
abstraction/comparison layer (doctrine §4.2), no reuse of
`classify_iv_environment` for display, no inheritance of
`_validated_chain_result`'s fabricated pass, no third meaning of
"spread" without a naming ruling, no silent contract/payload
extension (sidecar artifact only), no IV rank until history exists, no
skew summaries in a first slice, and no touching the GEX verdict.

## 13. OPEN OWNER QUESTIONS

All OWNER DECISION REQUIRED; namespaced OBS-D:
- **OBS-D1 — Track identity.** Is options observability a new track
  beside the ODATA-0 ledger row, or does it absorb/re-point ODATA-0
  (whose predecessor gate is superseded)? The workplan is the only
  planning ledger; a row needs your ruling to exist.
- **OBS-D2 — Evidence base.** Commission a Polygon/Massive provider-
  evidence pass (shares the GEX-D1 egress-grant mechanics), or rule
  that a first slice may be evidenced against the incumbent
  yfinance/yahooquery seam it already uses? (Doctrine: provider-
  dependent work needs a data-contract evidence pass before a feature
  PRD.)
- **OBS-D3 — Entitlement posture.** Quotes are the card's spine and
  are plan-gated (search-derived). Which entitlement tier — if any —
  is acceptable? (This is a product decision: no quotes ⇒ no MARKET
  block.)
- **OBS-D4 — Does it earn the seat at all?** §2's argument (compresses
  an existing manual act) is ours; the "changes what I will actually
  do" test is yours alone. A NO retires this research cleanly.
- **OBS-D5 — Change-detection posture.** Cards-with-deltas only, or
  any alerts at all (and if so, user-configured only)? §8 recommends
  deltas-first.
- **OBS-D6 — Priority.** This packet changes no priority; Cloudflare-
  first and the standing lane order are untouched. Where, if anywhere,
  does this sit after the current arcs?

## 14. MATERIALITY / GOVERNANCE ASSESSMENT

- **This packet: NON-MATERIAL.** GOV-2 §1 walked: enumerates no
  complete consumer set (all repo claims are recon observations, not
  completeness claims); selects no implementation seam; sets no
  FILES/LOC ceiling; adds/renames no contract/audit/report/payload/
  persisted schema; changes no governance guardrail; resolves no
  Critical/High finding; crosses no pipeline layers. Precedent: GEX-0's
  identical self-classification. It follows the recon-artifact clause:
  the committed packet on this branch is the deliverable.
- **Any future producer slice: expect MATERIAL** (new versioned
  artifact contract, new external dependency + secret, future display
  consumer — the same triple that made the GEX producer slice
  expected-MATERIAL). Lane STANDARD minimum; MICRO ineligible.
- **Adjacent named debt, graduated not fixed here:** F-22/CB-42
  (unused POLYGON_API_KEY in workflows), F-10/CB-31 (`date.today()`
  DTE math in chain_validation), CB-47 (`_estimated_debit` arithmetic
  pass owed), the MANUAL_CHECK render gap (PARKED), TD-1/QW-4 (GEX
  docs drift, already FIX NOW), and the SCHEMA_MAP/CALL_SITE_MAP
  options silence. None is touched by this packet.
- **Closing challenge test (house convention): does anything here
  displace the standing lane order (Cloudflare → registry → GEX
  bundle)?** **NO.** Every §13 question can wait; the only
  time-coupled observation is that a GEX-D1 egress grant, if and when
  you make it, could cheaply serve OBS-D2 in the same pass.

## 15. RECOMMENDED NEXT STEP

One step, no priority change: **rule on OBS-D4 and OBS-D1** (does the
surface earn a seat; is it a new ledger row). If both answers are
yes-shaped, the natural sequel is a single provider-evidence
commission that serves GEX-D1 and OBS-D2 together — one egress grant,
one captured-response pass, two tracks' data contracts evidenced
without coupling their authority. Everything else in this packet
(definitions, taxonomy, card shapes, alert candidates) is durable
research that keeps: it waits without decaying.
