# GEX MASSIVE/POLYGON PROVIDER EVIDENCE PACKET -- 2026-08-21

DATE: 2026-08-21
AUTHOR SEAT: Fable / independent provider/data-contract investigator
  (owner-commissioned second-provider evidence pass)
STATUS: EVIDENCE ONLY. No implementation, no PRD, no Gate A, no merge.
SCOPE: Massive.com (formerly Polygon.io) as provider for Cuttingboard's
  intended personal GEX context product, including the intended delivery
  surface. Exactly one provider family examined. No provider #3.

All quotes ASCII-normalized (em-dashes to "--", smart quotes to straight
quotes). Evidence classes used throughout: OBSERVED (this pass saw it
directly: live API response, gh/git output, or a page the author fetched
first-hand), REPORTED (provider-published text: docs, KB, legal, blog,
pricing), DERIVED (arithmetic composed from OBSERVED/REPORTED inputs),
INFERRED (reasoned interpretation, not proven). Delegated research-agent
findings were accepted only where the decisive quote or response was
re-verified first-hand by the author (CLAUDE.md author discipline 4).

---

## 1. Repo, base, and commissioning state

- Repo: github.com/dwats250/cuttingboard (PUBLIC -- OBSERVED,
  `gh repo view`: {"isPrivate":false,"visibility":"PUBLIC"}).
- main at evidence time: e89eebb64997e8857827a9f294d228538b30bdce
  (== origin/main, confirmed at session start).
- Cboe evidence baseline: PR #262 (draft, branch
  worktree-gex-cboe-evidence-gate, head 30cc2540ed88f1f5818e6eb18b8dc6d8a2d8ca4a),
  verdict EVIDENCE INCOMPLETE overall with the free/undocumented Cboe CDN
  delayed-quotes endpoint resolved NEGATIVE for automated use.
- Prior Polygon baseline: GEX-0 packet
  audits/gex-0-polygon-provider-evidence-2026-08/ (PRs #223/#224/#236),
  verdict EVIDENCE INCOMPLETE (egress blocked in the 2026-08-06 pass; a
  2026-08-09 addendum records a real HTTP 401 proving reachability; "the
  next step needs a real free-tier Polygon credential" --
  docs/DECISIONS.md 2026-08-09 addendum).
- Commissioning: owner (Dustin) charge of 2026-08-21 explicitly authorizes
  this fresh bounded Massive/Polygon pass. This satisfies workplan Wave-5
  "ends the track until Dustin explicitly commissions a fresh pass"
  (docs/plans/decision-support-workplan-v0.1.md) -- the commission is this
  charge. The charge forbids: rescuing the Cboe CDN endpoint, researching
  any further provider, implementation, PRD drafting, Gate A, provider
  abstraction, purchases/upgrades, and touching PRs #261/#262.

## 2. Purpose and boundary

Answer, with evidence: can Massive supply the minimum honest inputs for the
frozen GEX product (GEX = gamma x open_interest x 100 x spot^2 x 0.01;
outputs gex_total_1pct_usd, call_wall, put_wall, dominant_net_gamma,
zero_dte; population SPX+SPXW, all expirations -- tools/gex_snapshot.py,
PRD-306/PRD-307), and do Massive's usage terms permit Cuttingboard's
contemplated uses, including the delivery surface? Product calculations
remain frozen; a provider migration MAY imply a new provider schema, but no
schema is proposed here.

## 3. What this pass resolves from the prior Polygon record

The GEX-0 Polygon packet left 16 of 16 provider-side items unresolved, with
a captured sample response named as the load-bearing gap. This pass, run
with the real credential now present on the host (.env POLYGON_API_KEY,
dated 2026-08-14, git-ignored):

- RESOLVED live: identity/rebrand, key validity, auth mechanics, reference
  chain coverage (SPX/SPXW), free-tier entitlement boundary, EOD aggregate
  class, rate-limit tier, hostname continuity.
- RESOLVED from provider-published documents (REPORTED): snapshot field
  semantics, greeks methodology and omission conditions, OI definition,
  pagination, pricing, and the full licensing text.
- STILL OPEN (named precisely in section 21): a live chain-snapshot sample,
  greek freshness mechanics on delayed plans, and the underlying-value
  entitlement interplay -- all gated behind a paid plan this charge forbids
  purchasing.

## 4. Provider identity: Polygon.io is Massive.com

- REPORTED (https://massive.com/blog/polygon-is-now-massive, dated
  2025-10-30): "We have just renamed Polygon.io to Massive.com, effective
  today (October 30, 2025) at 4 PM ET." "While the brand has changed, your
  APIs, accounts, and data quality continue to work exactly as they do
  today." "Existing API keys remain valid." "API endpoints at
  api.polygon.io continue to work for an extended period."
- OBSERVED: https://polygon.io/docs returns 301 to https://massive.com/docs;
  polygon.io legal URLs 301 to massive.com equivalents.
- OBSERVED (live, this pass): the same host credential returned HTTP 200 on
  BOTH https://api.polygon.io/v1/marketstatus/now and
  https://api.massive.com/v1/marketstatus/now (t1/t7, section 6).
- OBSERVED (live): the entitlement error body itself points at the new
  brand: "Please upgrade your plan at https://massive.com/pricing" (t4).

Conclusion: one provider family, pure rebrand, key and hostname continuity
confirmed live. Current canonical docs base: https://massive.com/docs.

## 5. Authoritative source inventory

Provider-published (authority class A -- the provider's own current word):

| Source | URL | Dated |
|---|---|---|
| Rebrand announcement | massive.com/blog/polygon-is-now-massive | 2025-10-30 |
| Options pricing | massive.com/pricing?product=options and /options | current |
| Indices pricing | massive.com/pricing?product=indices and /indices | current |
| Business options | massive.com/business-options | current |
| Chain snapshot docs | massive.com/docs/rest/options/snapshots/option-chain-snapshot(.md) | current |
| Per-contract snapshot docs | .../option-contract-snapshot(.md) | current |
| Reference contracts docs | massive.com/docs/rest/options/contracts/all-contracts.md | current |
| Market status docs | massive.com/docs/rest/options/market-operations/market-status.md | current |
| Indices snapshot docs | massive.com/docs/rest/indices/snapshots/indices-snapshot.md | current |
| Greeks methodology blog | massive.com/blog/greeks-and-implied-volatility | 2022-03-22 |
| Pagination blog | massive.com/blog/api-pagination-patterns | undated |
| Market Data Terms of Service | massive.com/legal/market-data-terms-of-service | 2025-08-28 |
| Individuals Terms of Service | massive.com/legal/individuals-terms-of-service | 2025-07-18 |
| Businesses Terms of Service | massive.com/legal/businesses-terms-of-service | 2025-09-02 |
| Legal index | massive.com/legal/terms | undated |
| KB: redistribution | massive.com/knowledge-base/article/how-can-i-redistribute-massives-market-data | undated |
| KB: subscriptions per asset class | .../what-are-the-different-massive-subscriptions-i-can-use | undated |
| KB: index-option greeks (I:SPX example) | .../does-massive-support-greeks-for-index-option-contracts | undated |
| KB: request limits | .../what-is-the-request-limit-for-massives-restful-apis | undated |
| KB: options data source (OPRA) | .../where-does-massives-options-data-come-from | undated |
| Professional status | massive.com/blog/understanding-professional-status | 2020-05-08 |

Every licensing clause quoted in sections 14-16 and both decisive docs
claims (greeks omission, I:SPX example) were re-fetched first-hand by the
author on 2026-08-21, not accepted from delegated summaries alone.

## 6. Credential handling and live entitlement evidence

Secret handling (binding on this pass): the credential was never printed,
echoed, logged, committed, or placed in a URL. Every live call used header
auth (`Authorization: Bearer`). Historical context that motivates this:
gitleaks (2026-05-22) found 109 historical exposures of POLYGON_API_KEY via
`?apiKey=` query-string URLs logged into committed logs; remediated by
out-of-band key rotation (docs/DECISIONS.md 2026-05-22 area;
audits/cleanup-2026-05-22/). The current key (32 chars, .env, git-ignored
at .gitignore:2) is presumed the rotated replacement. `next_url` values
were checked for an embedded apiKey before any display: none present
(OBSERVED, consistent with the pagination blog: "we will exclude the API
key from the values in next/previous_url" -- REPORTED).

Live call ledger (all 2026-08-21 ~08:00-08:15 UTC, pre-market;
market status at the time: "extended-hours", earlyHours=true):

| # | Endpoint (auth header omitted) | HTTP | Finding |
|---|---|---|---|
| t1 | api.polygon.io/v1/marketstatus/now | 200 | market=extended-hours; serverTime=2026-08-21T04:02:45-04:00; indicesGroups.s_and_p=open |
| t2 | /v3/reference/options/contracts?underlying_ticker=I:SPX&limit=2 | 200 | status OK, count 0 -- I:SPX is NOT the reference-endpoint underlying syntax |
| t3 | /v3/reference/options/contracts?underlying_ticker=SPX&expiration_date=2026-08-21&limit=1000 (+2 next_url pages) | 200 | 2,180 contracts expiring 2026-08-21: root SPX 1,180 + root SPXW 1,000; european; shares_per_contract 100; next_url carries no apiKey |
| t4 | /v3/snapshot/options/SPX?limit=5 | 403 | {"status":"NOT_AUTHORIZED","error":"You are not entitled to this data. Please upgrade your plan at https://massive.com/pricing"} |
| t5 | /v2/aggs/ticker/I:SPX/prev | 403 | NOT_AUTHORIZED (same body) -- NO Indices entitlement on this key |
| t6 | /v2/aggs/ticker/O:SPX260821C00200000/prev | 200 | EOD bar returned (c=7522.39, t=1787169600000 = 2026-08-20 20:00 UTC close) -- free tier includes EOD option aggregates |
| t7 | api.massive.com/v1/marketstatus/now | 200 | same key valid on the new hostname |

Entitlement classification (OBSERVED): the host credential is an Options
Basic-class (free) key -- reference endpoints and EOD option aggregates
entitled; chain/contract snapshots NOT entitled; Indices NOT entitled at
any level. This matches the published Options Basic row exactly ($0/mo,
5 calls/min, EOD, no snapshots/greeks/OI). Consequence: the decisive
product surface (the chain snapshot carrying greeks/OI/underlying) could
not be sampled live on this credential; its semantics below are REPORTED
(provider-published) rather than OBSERVED, exactly as flagged per charge
section 5 ("If current key is only Basic/free and snapshot is unavailable,
record that cleanly").

Minimal redacted live sample excerpts (charge section 14; no full chain, no
raw persistence beyond these excerpts):

- t3 sample contract (reference row): {"ticker":"O:SPX260821C00200000",
  "contract_type":"call","strike_price":200,
  "expiration_date":"2026-08-21","exercise_style":"european",
  "shares_per_contract":100}
- t6 EOD aggregate: {"T":"O:SPX260821C00200000","v":6,"vw":7520.2,
  "o":7518.01,"c":7522.39,"h":7522.39,"l":7518.01,"t":1787169600000,"n":2}
  (deep-ITM close consistent with SPX ~7722 -- DERIVED, diagnostic only)
- t4 error body, verbatim: {"status":"NOT_AUTHORIZED","error":"You are not
  entitled to this data. Please upgrade your plan at
  https://massive.com/pricing"}

## 7. Option-chain snapshot endpoint semantics (REPORTED, docs re-verified)

Endpoint: GET /v3/snapshot/options/{underlyingAsset}
(docs: option-chain-snapshot.md; per-contract variant exists).

- Purpose: "consolidates key metrics for each contract, including pricing
  details, greeks (delta, gamma, theta, vega), implied volatility, quotes,
  trades, and open interest."
- Per-contract fields: details (ticker, contract_type, strike_price,
  expiration_date, exercise_style, shares_per_contract), day (OHLCV,
  last_updated), greeks (delta/gamma/theta/vega -- optional),
  implied_volatility (optional), open_interest (optional), last_quote
  ("only returned if your current plan includes quotes"), last_trade
  ("only returned if your current plan includes trades"), underlying_asset,
  break_even_price, fmv ("only available on Business plans").
- Pagination: "Limit the number of results returned, default is 10 and max
  is 250." next_url: "If present, this value can be used to fetch the next
  page of data." Cursor-based; API key intentionally excluded from
  next_url.
- Filters: strike_price(.gte/.gt/.lte/.lt), expiration_date(same ranges),
  contract_type, order/sort.
- No market_status field on the chain snapshot itself; market state comes
  from GET /v1/marketstatus/now (OBSERVED live: market, earlyHours,
  afterHours, exchanges, indicesGroups.s_and_p, serverTime RFC3339). The
  separate unified snapshot (/v3/snapshot) does carry per-result
  market_status (open/closed/early_trading/late_trading) but is capped at
  250 explicit tickers per call and is not the chain surface.
- Failure/absence behavior: optional fields are omitted, not nulled;
  entitlement failures are loud (HTTP 403 NOT_AUTHORIZED -- OBSERVED);
  auth failures 401 (matches the 2026-08-09 recorded 401). This satisfies
  fail-loud composition: a consumer can distinguish "field absent" from
  "request failed".

## 8. SPX / SPXW identity semantics

- Reference endpoint (/v3/reference/options/contracts): underlying_ticker
  is bare "SPX". OBSERVED live: I:SPX returns zero rows (t2); SPX returns
  the chain (t3). Contract tickers are OCC-style O:SPX... / O:SPXW...;
  strike_price is numeric (no /1000 digit parsing needed); expiration_date
  ISO; contract_type call/put; exercise_style european; expired contracts
  excluded by default (expired: "Default is false").
- Chain snapshot: underlyingAsset is prefixed "I:SPX". REPORTED (official
  KB example URL: https://api.massive.com/v3/snapshot/options/I:SPX). Not
  live-verifiable at current entitlement (t4 was 403 before symbol
  resolution could be observed).
- Both roots under one underlying: OBSERVED live at the reference surface
  (t3: SPX and SPXW rows under underlying_ticker=SPX); REPORTED at the
  snapshot surface (the official KB I:SPX example response contains
  details.ticker "O:SPXW230712C04500000" -- an SPXW weekly under the I:SPX
  chain). AM-settled SPX monthlies and PM-settled SPXW weeklies/dailies
  coexist: OBSERVED for today's third-Friday overlap (1,180 SPX + 1,000
  SPXW contracts expiring 2026-08-21).
- Population magnitude: the Cboe _SPX chain ran 30,282 contracts in
  PRD-307's live probe (repo record). The Massive universe is the same OCC
  listed universe; full-chain size of the same order is DERIVED, not
  independently counted this pass.

## 9. Greeks semantics and omission accounting

- Who computes: Massive, not the exchange. REPORTED (methodology blog):
  "our new Options Snapshot API, which calculates Greeks and implied
  volatility on demand"; "We chose the binomial options pricing model";
  inputs: time to maturity, spot price, strike price, volatility (solved as
  IV), dividend yield, risk-free interest rate; IV solved from the QUOTE
  MIDPOINT ("Implied volatility calculations are often done using the
  midpoint between the bid and ask"). Author re-verified all four quotes
  first-hand.
- Omission conditions: REPORTED (docs, both snapshot pages): "There are
  certain circumstances where greeks will not be returned, such as options
  contracts that are deep in the money." Mechanism (blog): 10-15% of
  contracts historically violated no-arbitrage bounds (deep-ITM midpoints
  below intrinsic), making the model unsolvable -- those contracts carry no
  greeks/IV.
- Structural suitability for GEX aggregation (charge section 4 CRITICAL):
  INFERRED (strong, mechanism-backed): omissions concentrate in deep-ITM
  contracts, whose TRUE gamma is near zero, so honest exclusion biases
  total GEX only marginally; near-the-money contracts (which drive walls,
  dominant strike, and 0DTE share) have tight two-sided quotes and are the
  least likely to fail the no-arbitrage solve. The landed producer already
  implements exactly the right treatment: rows lacking gamma/OI are
  EXCLUDED AND TALLIED per exclusion key with a coverage block
  (tools/gex_snapshot.py EXCLUSION_KEYS, PRD-306 R-contract) -- missing
  gamma is never treated as zero. UNPROVEN live: the actual omission rate
  by moneyness band on a current chain (requires snapshot entitlement);
  named as bounded-probe item P2 in section 21.
- "Real-time Greeks and IV" on 15-minute-delayed plans (pricing-page
  bullet on Starter/Developer): NO official page explains the mechanics
  (what quote/spot clock feeds the on-demand computation on a delayed
  plan). Docs NOT-FOUND after targeted search. The honest reading is
  UNRESOLVED between (a) greeks computed at request time FROM 15-min
  delayed quotes ("real-time computation, delayed inputs") and (b) greeks
  from real-time quotes delivered even to delayed subscribers. INFERRED
  (weak) toward (a) given the input-gating pattern on quotes; the greek
  CLOCK is therefore not establishable from documents alone -- but unlike
  the Cboe feed, Massive attaches per-field timestamps (section 12), so an
  entitled probe CAN measure it (probe item P3).

## 10. Open-interest semantics

- Definition: REPORTED (docs, re-verified): open_interest = "The quantity
  of this contract held at the end of the last trading day." Plan bullet:
  "Daily open interest" on all paid tiers.
- Cadence: daily, prior-trading-day close. This preserves the existing
  product caveat verbatim: OI is not intraday.
- Missing behavior: optional field; absent rather than null/zero. The
  producer's exclusion accounting (invalid_open_interest /
  missing_fields tallies) composes honestly.
- Numeric representation: documented "number"; doc examples are
  integer-valued (4501). Whether the JSON wire value arrives as int or
  integer-valued float is unverified live at the snapshot surface; the
  PRD-307 admissibility rule (accept integer-valued floats, normalize to
  int) already generalizes to either representation.
- Source: options data "directly from the Options Price Reporting
  Authority (OPRA)" (KB, REPORTED). Index-option OI difference: none
  documented (NOT-FOUND).

## 11. Underlying spot basis

- The frozen formula needs SPX spot (spot^2 term). Under Cboe this came
  in-band (data.current_price).
- Under Massive: the chain snapshot embeds an underlying_asset block; for
  index underlyings the official KB example shows {"last_updated":
  1680814651655000000, "value": 4483.78, "ticker": "I:SPX", "timeframe":
  "REAL-TIME"} -- an index VALUE with its own timestamp and timeframe
  label (REPORTED, re-verified first-hand).
- Entitlement interplay (load-bearing, UNRESOLVED): the docs describe
  underlying_asset with stock wording: "The market data returned depends
  on your current stocks plan." The per-asset-class subscription model
  (KB: "Each asset class has its own subscription") implies the Indices
  analogue governs index values, and this key's I:SPX 403 (t5) confirms
  index data is a separate entitlement -- but NO official statement says
  whether an Options-only plan surfaces underlying_asset.value inside the
  option snapshot for I:SPX, omits it, or serves it delayed. EVIDENCE
  INCOMPLETE; decides $29/mo vs $78/mo (section 13); probe item P4.
- Honest fallbacks if value is absent under Options-only: Indices Starter
  ($49/mo, 15-min delayed I:SPX) is the sanctioned in-provider basis. A
  derived spot (e.g. deep-ITM parity implied) would violate
  authoritative-source-not-proxy and is NOT proposed.

## 12. Timestamp / freshness semantics

This is where Massive structurally differs from the Cboe CDN feed whose
clock ambiguity produced the PR #262 negative freshness finding (greeks
moved while every market input sat frozen, with no per-field clocks).

- Per-field clocks: day.last_updated, last_quote.last_updated,
  last_trade.sip_timestamp, underlying_asset.last_updated,
  fmv_last_updated -- 19-digit nanosecond epochs in every documented
  example; the unit is stated explicitly for fmv_last_updated ("the
  nanosecond timestamp of the last FMV calculation") and on the sibling
  indices snapshot page ("The nanosecond timestamp of when this
  information was updated"); child descriptions on the chain page itself
  are thin (REPORTED with that caveat).
- Per-field timeframe labels: enum DELAYED / REAL-TIME (documented on the
  indices snapshot page; appears on last_quote/last_trade/underlying_asset
  in options examples). No "15_MIN_DELAYED" literal exists.
- Whole-response clock: NONE. Top-level fields are status, request_id,
  results, next_url only. There is no snapshot-generation timestamp; a
  chain page is not documented as an atomic moment. Fields ARE allowed to
  be on different clocks -- each self-labeled.
- Server clock: GET /v1/marketstatus/now returns serverTime (RFC3339)
  plus market/session flags (OBSERVED live) -- a genuine provider-side
  "now" to anchor freshness deltas against, which the Cboe feed never had.
- Greek-calculation timestamp: NONE documented. Greeks carry no
  last_updated of their own; their clock is the unresolved item from
  section 9 (probe item P3 can bound it empirically: fetch twice inside a
  quiet window and watch greeks vs quote timestamps, this time WITH
  per-field clocks available).
- Consequence for the product: honest per-field freshness disclosure is
  POSSIBLE under Massive (fetched_at from producer, per-field provider
  timestamps, serverTime anchor, timeframe labels) -- a strict upgrade over
  the single ambiguous Cboe top-level timestamp. The existing
  feed_timestamp_utc contract (naive-UTC string) would NOT carry over; a
  Massive schema would record nanosecond epochs per field. No schema is
  proposed here.

## 13. Rate limits, request economics, minimum plan and cost

Published plan rows (REPORTED, cross-verified on two official pages):

| Plan | Price | Calls | Data | Snapshot/Greeks/OI |
|---|---|---|---|---|
| Options Basic | $0/mo | 5/min | End-of-day | none |
| Options Starter | $29/mo | Unlimited | 15-min delayed | Snapshots + "Real-time Greeks and IV" + daily OI |
| Options Developer | $79/mo | Unlimited | 15-min delayed | same + 4yr history |
| Options Advanced | $199/mo | Unlimited | Real-time | same; "Non-pros only" |
| Indices Basic | $0/mo | 5/min | End-of-day | limited tickers |
| Indices Starter | $49/mo | Unlimited | 15-min delayed | all index tickers, snapshot |
| Indices Advanced | $99/mo | Unlimited | Real-time | all index tickers |
| Options Business | $1,999/mo | Unlimited | Real-time + FMV | "Business use" label |

"Unlimited" carries a KB soft ceiling: "stay under 100 requests per
second" (REPORTED). Free-tier limit OBSERVED indirectly (documented 5/min;
this pass stayed under it deliberately; no 429 was provoked).

Cadence math (DERIVED):
- Board cadence today: ~10 renders per trading day (1 pipeline OPEN
  publish + up to 9 hourly_alert re-renders; .github/workflows/*.yml).
  The charge's working figure of 7-8 eligible hourly runs is the same
  order; both are used below as the range 8-10.
- Full-chain snapshot at max limit 250: ceil(~30,282 / 250) = ~122
  pages/run (chain size DERIVED from the Cboe-observed universe).
- Requests/day: ~122 x (8..10) = ~976..1,220 chain calls/day, plus 1
  marketstatus call/run. Trivially inside "unlimited"; far under 100/s at
  any sane pacing.
- Options Basic cannot serve the product at all: no snapshot entitlement
  (OBSERVED 403), EOD-only data, and 5/min would need ~25 minutes per
  full-chain run even if entitled.
- 0DTE-only diagnostics: today's expiration alone was 2,180 contracts
  (OBSERVED) = 9 pages with expiration_date filtering, if ever needed.

Minimum technically sufficient plan (DERIVED from the above):
- Options Starter, $29/mo -- IF the option snapshot surfaces
  underlying_asset.value for I:SPX under Options-only entitlement.
- Options Starter + Indices Starter, $29 + $49 = $78/mo -- if it does not.
- Free tier: NOT sufficient (fails snapshot, greeks, OI, cadence).
- No purchase or upgrade was made in this pass (charge sections 5/9).

## 14. Licensing document map -- which terms govern

For an individual subscriber the governing stack is (all OBSERVED
first-hand by the author, 2026-08-21):

1. Massive for Individuals Terms of Service (2025-07-18) -- the Services
   (API) grant: "solely for your own personal, non-commercial, and
   non-business purposes." Preamble: "If you are using the Services for
   business or commercial purposes, you may not use any of the Services
   labeled for individual or personal use."
2. Market Data Terms of Service (2025-08-28) -- the data license itself:
   - Section 1 grant: "a nonexclusive, nontransferable, non-sublicensable,
     revocable, limited license to use Market Data exclusively for your
     personal, non-business, and non-commercial purposes. For the
     avoidance of doubt, you may not use the Market Data for any business
     or commercial purpose, and you may not use the Market Data to build
     an application intended for use by end users other than you."
   - Section 2: "The Market Data may not be copied, reproduced,
     republished, uploaded, posted, publicly displayed, encoded,
     translated, transmitted, or distributed in any way (including
     'mirroring') to any other computer, server, website, or other medium
     for publication or distribution or for any business or commercial
     enterprise, without Massive's express prior written consent." And:
     "Unless otherwise stated in a subsequent agreement with us or a Third
     Party Provider, any and all Market Data is strictly for display use
     only."
   - Section 5 (preamble: "Absent prior express written consent from
     Massive or to the extent permitted by an agreement with a Third Party
     Provider, you may not:"):
     (c) "Redistribute, display, disseminate, duplicate, license,
     sublicense, publish, broadcast, transmit, distribute, redistribute,
     perform, display, sell, resell, rebrand, or otherwise transfer the
     Market Data -- or any data, charts, analytics, research, or other
     works based on, referring to, or derived from the Market Data
     ('Derived Works') -- to any third party or use the Market Data for
     business or commercial purposes;"
     (d) "Use Market Data for non-display use or to create derivative
     works (including, without limitation, any index, indicative value,
     net asset value, investment product, financial contract, (including,
     without limitation, contracts for difference or spread betting),
     settlement value or investment strategy) based on the Market Data
     unless you are licensed to do so;"
     ("non-display use" is nowhere defined in the document.)
   - Section 3: Non-Professional = "any natural person who receives
     market data solely for their own personal, non-business use and who
     is not a Professional." Plus a retroactive-billing clause: if Massive
     or its providers later determine (from "companies websites, email
     address and domain, LinkedIn, regulatory or company registries,
     payment method, or other available information") that a subscriber is
     Professional, the rate difference applies "retroactively from the
     date you initiated your subscription" and may be auto-charged.
   - Section 8: on termination/suspension "you agree to cease all use of
     the Market Data and delete all Market Data in your possession."
3. OPRA Non-Professional Subscriber Agreement (Schedule 1) -- triggered
   ONLY for real-time recipients: Section 4.1: "To the extent you are a
   recipient of real-time options Market Data provided by OPRA, you hereby
   enter into the 'OPRA Non-Professional Subscriber Agreement'..." On a
   15-minute-delayed plan (Starter/Developer) the OPRA schedule is NOT
   triggered; Massive's own Sections 1-8 govern in full. Delayed data does
   NOT escape the vendor restrictions. (If real-time were ever bought, the
   OPRA addendum confines use to "your personal investment activities" --
   which affirmatively frames personal investment use of options data.)
4. Business alternative: Massive for Businesses Terms of Service
   (2025-09-02): Information grant "solely for its use in websites or
   software applications owned or licensed by Customer"; distribution
   permitted to "Customer, its Authorized Users, or its Edge Users"
   ("individuals or entities that are users of Customer's products and
   services"); 6.1(j) still restricts productized derivative works
   ("index, indicative value, net asset value, investment product,
   financial contract, ... settlement value or investment strategy")
   "unless licensed to do so." KB: "Any user who wishes to redistribute
   Massive's market data must sign up for one of our business products."

Dustin's classification basis: solo discretionary trader, own account, no
regulatory registrations of record -- fits Non-Professional as defined
(subject to Dustin's own confirmation; the packet does not classify him,
it records the definition and the retroactive-billing enforcement risk).

## 15. Contemplated uses A-G: verdicts with authoritative basis

| Use | Verdict | Basis (short) |
|---|---|---|
| A. Automated API retrieval by software, for Dustin personally | PERMITTED | Individuals ToS s.2 grants Services/API use for personal purposes; API calls are the sold metered unit ("Unlimited API Calls" on individual tiers); no automation prohibition exists anywhere in the stack (direct contrast with Cboe's anti-automation clause); requires the Non-Professional representation |
| B. Computing GEX (gamma+OI+spot) for Dustin's own trading context | EVIDENCE INCOMPLETE | Genuine textual tension, section 16; one written provider clarification is the smallest resolver |
| C. Persisting the raw option chain | NOT PURSUED (and stays product-forbidden) | Not needed; PRD-306 R12 already bans raw-chain keys in the artifact; MDT s.2 copy/republication language plus s.8 delete-on-termination make raw persistence adverse; note s.2's prohibition is textually publication-directed ("for publication or distribution or for any business or commercial enterprise"), so transient private processing inherent to API use is not the target |
| D. Persisting a compact derived GEX artifact PRIVATELY | EVIDENCE INCOMPLETE (inherits B) | The persistence element itself transfers nothing to a third party; the creation question is B's; caveat: the current artifact embeds spot.value -- one raw Market Data element -- so the artifact must stay genuinely private (see section 17 on what "private" can mean in this repo) |
| E. Displaying derived GEX to Dustin on a PRIVATE authenticated surface | EVIDENCE INCOMPLETE (inherits B) | Display-to-self is the affirmatively granted use ("strictly for display use only" cuts FOR private display); the composite rests on B's computation question |
| F. Displaying derived GEX on the CURRENT public GitHub Pages dashboard | NOT PERMITTED | MDT s.5(c) verbatim covers "analytics ... derived from the Market Data ('Derived Works')" transferred/displayed "to any third party"; s.2 bans posting/public display on any website for publication; s.1 bans applications "intended for use by end users other than you"; KB requires business products for redistribution. The Pages site is public (OBSERVED: pages API public:true) and the repo is PUBLIC. Attribution changes nothing (no attribution carve-out exists in any document). Obscurity/unlisted URL changes nothing (still publicly accessible; the repo itself is public). Holds under BOTH readings of the section-16 tension |
| G. Redistributing raw market data | NOT PERMITTED (and not intended) | MDT s.2, s.5(c); KB redistribution article |

## 16. Derived Works -- the load-bearing analysis for personal GEX (USE B)

The question: does computing GEX from gamma+OI+spot, for Dustin alone, fall
inside the individual license or inside a restricted category?

Text pulling AGAINST (restrictive reading):
- MDT s.2: "any and all Market Data is strictly for display use only."
  Computing with the data (gamma as an input to an aggregation) is not
  "display use" of that datum under a strict reading.
- MDT s.5(d): no "non-display use or ... create derivative works ...
  unless you are licensed to do so" -- and "non-display use" is undefined.
  Under the broadest reading, any programmatic computation is non-display
  use requiring a further license.

Text pulling FOR (harmonized reading):
- MDT s.5(c) defines Derived Works -- expressly including "analytics" --
  and restricts TRANSFERRING them "to any third party" or business use. A
  transfer-only restriction on Derived Works presupposes that CREATING a
  Derived Work for personal use is contemplated and not itself the
  violation; otherwise 5(c)'s careful transfer language would be largely
  redundant of 5(d).
- MDT s.5(d)'s enumeration is uniformly productized-derivative shaped
  (index, indicative value, NAV, investment product, financial contract,
  CFDs/spread betting, settlement value, investment strategy) -- classic
  exchange derived-data licensing boilerplate aimed at tradable products
  and settlement uses, not at a subscriber's private analytics. Read
  maximally it would also prohibit any subscriber from forming "an
  investment strategy" by looking at the data -- an absurd result that
  suggests the productized reading is the operative one.
- The Individuals grant (s.1/s.2) licenses personal use of an API whose
  individual tiers sell greeks, IV, and snapshots -- data whose ONLY
  personal utility is computational/analytic.
- The OPRA addendum (when triggered) affirmatively licenses use "solely in
  connection with your personal investment activities."
- Provider marketing addressed to individual tiers: "What will you
  build?", "Trading tools, research agents, dashboards", "the same
  institutional-level data access to both companies and individuals
  alike" (REPORTED; marketing cannot amend terms, but it evidences the
  provider's own understanding of licensed personal use).

Finding: the documents genuinely conflict at the level of personal derived
computation. Neither "it's personal, so fine" nor "the text says
non-display, so forbidden" is honest. Per the charge's standard, USE B is
EVIDENCE INCOMPLETE. The smallest remaining evidence step is one written
question to Massive (support@ or sales@): "Under the Individual plans, may
a Non-Professional subscriber programmatically compute a private,
non-redistributed analytic (specifically: a gamma-exposure aggregate from
greeks, open interest, and the index value) solely for their own personal
trading context, with no display or transfer to any third party?" A
written yes resolves B, D, and E simultaneously. A written no resolves the
provider NEGATIVE for the product in any form at individual pricing.

What does NOT depend on this tension: USE F's NOT PERMITTED (public
transfer/display is prohibited under either reading), and USE A's
PERMITTED (retrieval under the Services grant).

## 17. Public board vs private board (delivery-surface finding)

Evidence about the current surface (all OBSERVED):
- The repo is PUBLIC; the GitHub Pages site
  (https://dwats250.github.io/cuttingboard/) is public:true; Pages serves
  the publish branch of the SAME public repo; generated artifacts
  (logs/latest_*.json, ui/dashboard.html) are committed at PUBLIC
  visibility. logs/gex_snapshot.json is the sole exception: NOT committed
  anywhere (PRD-306/307 design).

MAJOR PRODUCT/INFRA FINDING: under Massive individual licensing, derived
GEX metrics may NOT appear on the current public GitHub Pages dashboard
(USE F NOT PERMITTED), while a strictly private personal variant is
plausibly permitted pending the single USE B clarification. If GEX is to
exist under Massive at individual pricing, the GEX card must live on a
surface only Dustin can read, while the rest of Cuttingboard stays public.

What "private" can honestly mean with EXISTING repo capabilities (no
architecture is proposed or implemented here):
- PRIVATE TODAY: the operator-local path. tools/gex_snapshot.py already
  writes an uncommitted local artifact, and the doctrine's GEX-2 gate
  already begins with "Dustin inspects useful GEX-1 artifacts" -- i.e. the
  producer-and-local-inspection loop that exists on main is ALREADY the
  private surface. Local rendering/reading of logs/gex_snapshot.json on
  Dustin's machine transfers nothing to any third party.
- NOT PRIVATE (despite intuition): committing even a compact derived
  artifact to this repo (public), the publish branch (public), or CI
  workflow artifacts (downloadable by any logged-in GitHub user on a
  public repo). None of these can carry Massive-derived data.
- NEW INFRA (owner decision, out of scope to design): a private repo
  split, an authenticated page, or any operator-only remote surface.

## 18. Business-tier sanity check (only if Individual blocks GEX)

If public display of the derived GEX card is a hard product requirement,
the minimum sanctioned Massive path is a Business Options subscription:
$1,999/mo (REPORTED, verified current), whose grant covers use "in
websites or software applications owned or licensed by Customer" with
availability to Edge Users, and whose KB names business products as the
redistribution route. Residual caveat: Businesses ToS 6.1(j) still
restricts productized derivative works "unless licensed to do so"; a
public derived-GEX display would sit in the Edge-User display frame, but a
written confirmation would be prudent before ever relying on it. Economic
finding (DERIVED): $1,999/mo is ~69x Options Starter and is not
commensurate with a personal context board; it is recorded for
completeness, not recommended.

## 19. Strongest truthful GEX disclosure under Massive (if ever displayed)

"GEX computed from Massive (formerly Polygon.io) option-chain snapshot of
SPX+SPXW (underlying I:SPX). Greeks are Massive-model-computed (binomial,
quote-midpoint inputs) on ~15-minute-delayed quotes [Starter tier];
greek-calculation clock provider-undocumented. Open interest is as of the
prior trading-day close (not intraday). Spot basis: I:SPX index value,
~15-minute delayed, per-field provider timestamp recorded. Contracts
without provider greeks or OI are excluded and tallied (deep-ITM greeks
are systematically omitted by the provider). Fields carry independent
provider clocks; no single snapshot moment exists. Fetched at
<fetched_at_utc>; provider serverTime <serverTime>. Private, personal,
non-redistributed use only."

Every clause above is traceable to a section of this packet; nothing in it
overstates coherence the provider does not document.

## 20. Claim-status table

| # | Claim | Class |
|---|---|---|
| 1 | Polygon.io == Massive.com; keys and api.polygon.io continue; api.massive.com canonical | OBSERVED (live t1/t7 + 301s) + REPORTED (blog) |
| 2 | Host credential authenticates; Options Basic-class; no Indices entitlement | OBSERVED |
| 3 | Chain snapshot 403-gated on free tier; exact error body captured | OBSERVED |
| 4 | Reference underlying syntax SPX; chain syntax I:SPX | OBSERVED (reference, live) / REPORTED (chain, official KB example) |
| 5 | SPX+SPXW coexist under one underlying; 2,180 contracts expire 2026-08-21 | OBSERVED (reference) / REPORTED (snapshot example) |
| 6 | Full SPX chain ~30k contracts; ~122 snapshot pages/run; ~1.0-1.2k calls/day at board cadence | DERIVED |
| 7 | Snapshot fields incl. greeks/IV/OI/underlying_asset; limit max 250; plan-gated last_quote/last_trade; fmv Business-only | REPORTED (docs, re-verified) |
| 8 | Greeks Massive-computed, binomial, midpoint inputs; omitted on no-arb violation (deep ITM) | REPORTED (docs + methodology blog, re-verified) |
| 9 | Greek omissions concentrate where true gamma ~ 0; exclusion accounting suffices | INFERRED (strong; live moneyness-band rate unproven) |
| 10 | "Real-time Greeks" on delayed plans: input clock | UNRESOLVED (no official mechanics; INFERRED weak toward delayed-input computation) |
| 11 | OI = prior-trading-day close; daily cadence; optional field | REPORTED (docs, re-verified) |
| 12 | Index underlying carries value + ns timestamp + timeframe in snapshot | REPORTED (official KB example, re-verified) |
| 13 | Whether Options-only entitles underlying I:SPX value in-band | EVIDENCE INCOMPLETE |
| 14 | Per-field ns clocks + DELAYED/REAL-TIME labels; no whole-response clock; serverTime exists | REPORTED (docs) + OBSERVED (serverTime live) |
| 15 | Pricing rows (Basic $0 / Starter $29 / Developer $79 / Advanced $199 / Indices $0-$49-$99 / Business $1,999) | REPORTED (two official pages each, cross-checked) |
| 16 | Free tier 5/min; paid unlimited with 100/s soft ceiling | REPORTED + OBSERVED (free-tier class behavior) |
| 17 | MDT s.1/s.2/s.5(c)/s.5(d)/s.3/s.4.1/s.8 verbatim as quoted | OBSERVED (author fetched the documents first-hand) |
| 18 | OPRA schedule triggers only for real-time recipients; delayed governed by Massive's own terms | OBSERVED (document text) |
| 19 | Repo PUBLIC; Pages public; publish branch public; logs/ artifacts public; gex artifact uncommitted | OBSERVED |
| 20 | USE F prohibited; USE A permitted; USE B/D/E unresolved by documents | See sections 15-16 (document-grounded) |

## 21. Unresolved unknowns and smallest remaining evidence steps

U1 (technical, decisive): no live chain-snapshot sample exists on the
current credential. Doctrine 4.2 requires "current provider documentation
and a real response"; the real responses obtained (reference, aggregates,
market status) do not cover the decisive surface.
U2 (technical): greek-clock mechanics on delayed plans (section 9).
U3 (technical): underlying I:SPX value entitlement under Options-only
(section 11); decides $29 vs $78/mo.
U4 (technical): greek/OI omission rate by moneyness band on a real chain.
U5 (rights, decisive for any private variant): USE B personal derived
computation (section 16).
U6 (rights, minor): whether Business 6.1(j) would need a further letter
for public derived display (moot unless $1,999/mo is ever on the table).

Smallest remaining evidence steps (both owner-gated; NEITHER performed in
this pass):
- P1: one month of Options Starter ($29) + a bounded ~10-call probe closes
  U1-U4 in a single session (chain page sample incl. greeks/OI/underlying
  block; two spaced fetches for clock observation; moneyness-band omission
  counts; underlying-value presence). Add Indices Starter ($49) only if
  the probe shows the value absent.
- P2: one written clarification to Massive resolves U5 (text proposed in
  section 16).

## 22. Verdict

TECHNICAL VERDICT: EVIDENCE INCOMPLETE. On provider-published documents,
Massive is technically strong for the frozen GEX product -- consolidated
chain snapshot with greeks/IV/OI, SPX+SPXW under I:SPX, per-field
nanosecond clocks with delay labels, a server clock, documented greeks
methodology and omission semantics compatible with the producer's existing
exclusion accounting, unlimited-call pricing at $29-78/mo, and loud
entitlement failures. But the decisive surface has not returned a real
response on the available credential (U1), and U2-U4 are open. Doctrine
4.3's sample-response leg is unmet live; a $29 bounded probe closes it.

USAGE-RIGHTS VERDICT: split, and the split is the finding.
- USE A (automated personal retrieval): PERMITTED.
- USE F (derived GEX on the current public GitHub Pages board):
  NOT PERMITTED under Individual terms -- by explicit, current,
  first-hand-verified contract text, under either available reading of
  the derived-works tension, with no attribution or obscurity cure.
- USE B/D/E (the private personal variant): EVIDENCE INCOMPLETE --
  resolvable by one written provider clarification.

FINAL PROVIDER VERDICT (scoped per the charge to "Massive/Polygon as
provider for Cuttingboard's intended personal GEX context product,
including the intended delivery surface" -- and the actual current
delivery surface is the public GitHub Pages board):

PROVIDER NOT VIABLE

-- for the product as currently surfaced. The block is a licensing-surface
block, not a data-quality block: the only sanctioned routes to a PUBLIC
derived-GEX display are a $1,999/mo Business subscription (economically
disproportionate) or express written consent. Stated precisely, as the
charge requires: a private-personal GEX variant under Massive at $29-78/mo
remains plausibly permitted and technically promising, pending exactly two
bounded owner-gated steps (P1 probe, P2 written clarification); if the
owner re-scopes the GEX delivery surface to private/operator-local, this
verdict does not carry over to that re-scoped product, and a short
follow-up evidence note on P1+P2 would complete the picture.

## 23. Consequences for the current GEX product and downstream gates

- Combined provider state after PR #262 + this packet: NEITHER free path
  is clean for the intended public product. Cboe CDN: automated retrieval
  itself prohibited (terms), public re-display adverse, clock semantics
  unknowable. Massive individual: automated personal retrieval cleanly
  permitted, clock semantics honest, but public display of derived GEX
  prohibited. The two failures are of different kinds: Cboe fails at
  INGEST; Massive fails at the current PUBLIC DISPLAY surface.
- The frozen GEX calculations (PRD-306) survive unchanged under a Massive
  migration; the provider-facing half of the producer would need a new
  schema (I:SPX chain, per-field ns timestamps, greeks-omission exclusion
  tallies, snapshot pagination) -- NOT designed here, and gated behind
  owner decisions below.
- GEX-1 as landed (Cboe-based, manual, uncommitted artifact) is untouched
  by this pass. GEX-2 (PR #261) and the Cboe packet (PR #262) are
  untouched.
- Owner decisions now on the table (exactly these, per charge section 19):
  D-M1: Re-scope the GEX delivery surface to private/operator-local (the
        existing local-artifact loop), or keep the public-board
        requirement (which forecloses Massive at individual pricing).
  D-M2: Authorize $29 (one month, Options Starter) for bounded probe P1;
        +$49 Indices Starter only if the probe shows it necessary.
  D-M3: Authorize sending Massive the written USE-B clarification (P2).
  D-M4: If neither re-scope nor Business pricing is acceptable, the GEX
        track ends per doctrine 4.3 until a fresh owner commission.

## 24. Charge compliance

NO IMPLEMENTATION / NO PRD / NO GATE A / NO MERGE. One evidence packet,
one branch, one draft PR. PRs #261 and #262 untouched. No second provider
researched (charge section 16 honored). No account created, upgraded, or
purchased; no plan changed. Seven bounded live API calls plus three
reference-pagination continuations, all header-authenticated; the
credential was never echoed, logged, committed, or URL-embedded; no raw
chain was persisted (the only live payloads retained are the redacted
excerpts in section 6). The Cboe CDN endpoint was not re-tested or
"rescued". Verdict vocabulary per doctrine 4.3. Evidence classes per
charge section 7. This packet is the deliverable authorized by the
recon-artifact clause; its branch-to-main merge is held for Dustin.

-- END OF PACKET --
