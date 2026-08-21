# GEX Cboe Automated-Use and Freshness Evidence Packet

DATE: 2026-08-21
AUTHOR SEAT: Fable / Navigator (commissioned provider-evidence pass)
STATUS: EVIDENCE ONLY. No implementation, no PRD, no Gate A, no merge.

## 1. Repo / base / head

- Repository: dwats250/cuttingboard
- Canonical main at pass start: e89eebb64997e8857827a9f294d228538b30bdce
  (verified equal to origin/main at session start)
- Evidence branch: worktree-gex-cboe-evidence-gate (this packet is its only
  substantive change)
- Frozen GEX-2 design packet: PR #261, head
  acced04248ee91bd473ced58a3d23980a35f7db4 (r3). NOT modified by this pass.

## 2. Purpose and boundary

Owner-commissioned bounded evidence gate, inserted before any GEX-1b work,
answering two load-bearing provider questions about the CURRENT Cboe source
used by `tools/gex_snapshot.py`:

- A. Is automated retrieval of the delayed-quotes CDN JSON endpoint permitted
  for the intended automated published-board GEX product (GEX-3 would fetch
  from GitHub Actions)?
- B. What do the response timestamps actually mean, and is option-model
  (Greek) freshness knowable from this feed?

Out of scope by charge: correcting PR #261, implementing anything, drafting
PRDs, researching any non-Cboe provider. Frozen product decisions honored:
D-0 (doctrine split), D-1 (presentation distance math), D-2
(feed_timestamp_utc is not a freshness clock), GEX is context only, GEX-1b
if viable is CLASS SIDECAR / LANE STANDARD / MATERIAL YES (GOV-2 T4).

## 3. Prior r3 Codex finding summary

Fresh Codex Event-1 on r3 head acced042 returned DESIGN INCOMPLETE, NEW
MATERIAL BOUNDARY FOUND: YES, 6 required findings (verdict transmitted in the
owner charge; the full findings artifact is not in-tree). The two load-bearing
gaps this pass was commissioned to evidence:

1. `data.last_trade_time` semantics were asserted, not established: no
   documented meaning, no documented timezone, no established link between an
   SPX index timestamp and option-model gamma freshness.
2. Automated access was assumed: Cboe's delayed-quotes pages prohibit
   automated extraction of delayed quote-table data, and reachability of the
   CDN endpoint is not permission.

Relevant r3 packet claims now testable against evidence: that
`data.last_trade_time` "is fresh during RTH and freezes overnight/weekend/
holiday", sits "~15 minutes behind" edge regeneration, and can be renamed
`underlying_last_trade_utc` with semantics "delayed market-observation time".

## 4. Authoritative source inventory

All accessed 2026-08-21. A = authoritative Cboe property.

| # | Source | Type |
|---|--------|------|
| S1 | https://www.cboe.com/delayed_quotes/spx/quote_table (full HTML fetched directly, 16.4 MB; prohibition notice captured verbatim first-hand) | A |
| S2 | https://www.cboe.com/terms/ ("Terms and Conditions for Use of Cboe Websites") | A |
| S3 | https://www.cboe.com/use-of-content/ ("Use of Cboe Content") | A |
| S4 | https://www.cboe.com/robots.txt and https://cdn.cboe.com/robots.txt | A |
| S5 | https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json (two bounded live fetches; see section 14) | A (undocumented endpoint) |
| S6 | https://datashop.cboe.com/cboe-all-access-api (All Access API product page, tiers/pricing) | A |
| S7 | https://api.livevol.com/v1/docs/Help and endpoint doc GET /allaccess/market/option-and-underlying-quotes | A |
| S8 | https://datashop.cboe.com/option-eod-summary ; https://datashop.cboe.com/option-quote-intervals ; https://datashop.cboe.com/end-of-day-theoretical-values ; https://datashop.cboe.com/documentation | A |
| S9 | https://www.cboe.com/us/indices/accessing-index-data ; https://datashop.cboe.com/csmi-fee-increase-effective-112021 | A |
| S10 | In-repo prior evidence: audits/gex-0-cboe-evidence-2026-08/ (2026-08-17 packet) | repo |
| S11 | Community usage (OpenBB discussions, GitHub GEX scripts) | non-authoritative; used only to establish that community use exists, never for permission or semantics |

Search-engine caches of rendered dashboard pages were used for one item only
(the dashboard's "ET (Delayed)" timestamp label) and are marked second-hand
where cited.

## 5. Automated-access evidence

REPORTED (S1, captured verbatim first-hand from the SPX quote_table page
HTML, 2026-08-21):

> "PLEASE NOTE: IT IS STRICTLY PROHIBITED TO DOWNLOAD DELAYED QUOTE TABLE
> DATA FROM THIS WEB SITE BY USING AUTO-EXTRACTION PROGRAMS/QUERIES AND/OR
> SOFTWARE. CBOE WILL BLOCK IP ADDRESSES OF ALL PARTIES WHO ATTEMPT TO DO
> SO. THIS DATA IS PROPERTY OF CBOE LIVEVOL OR ITS DATA PROVIDERS.
> DOWNLOADING THIS DATA IN ANY OTHER WAY THAN BY MANUAL TICKER SYMBOL ENTRY
> IS STRICTLY PROHIBITED."

REPORTED (S2, /terms/ Section 2): use is limited to "view, print and
download one copy of the Materials for your personal non-commercial use";
otherwise copying, storing "in an electronic retrieval system", transmitting,
displaying, broadcasting, distributing or otherwise using the Materials
requires "Cboe's prior written consent"; creating "a derivative work (for
example, a financial product, service or index)" from the Materials is
prohibited. Section 4: Materials are "for general informational and
educational purposes only and are not intended for trading purposes."

REPORTED (S3, Use of Cboe Content): "In order to use any Cboe Content, you
must receive approval in advance from Cboe." "You are not approved to use
Cboe Content until a license agreement has been signed by both you and Cboe."

OBSERVED (S4): www.cboe.com/robots.txt disallows only /book/ and
/*market_statistics/volume_reports/ (no rule on /delayed_quotes/ or /api/);
cdn.cboe.com/robots.txt returns HTTP 403 AccessDenied (no robots file
served). Per the charge standard, absence of a robots rule is NOT permission
and is given no permissive weight.

REPORTED (absence, S1-S9 sweep): no Cboe page grants permission for
automated retrieval of delayed-quotes data outside licensed products.

## 6. Exact endpoint status

Endpoint: https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json
(the exact URL in `tools/gex_snapshot.py:42`).

- REPORTED (absence): no Cboe page documents this endpoint as a public API,
  supported feed, or licensed product. Targeted searches surface only the
  cboe.com delayed-quotes dashboard (its consumer) and community scrapers.
- INFERRED (strong): it is the undocumented backend of the
  www.cboe.com/delayed_quotes dashboard. Basis: identical path vocabulary
  ("delayed_quotes"), identical data shape to the quote table, and the data
  ownership statement on the quote-table page ("THIS DATA IS PROPERTY OF
  CBOE LIVEVOL"). The page HTML itself constructs API calls in bundled
  scripts; the literal URL was not located in static HTML, so the
  backend tie is INFERRED, not OBSERVED.
- Whether the S1 prohibition's words "FROM THIS WEB SITE" reach the
  cdn.cboe.com host as a matter of letter is UNRESOLVED (no Cboe text names
  the CDN host). Per the charge standard, unresolved coverage reads as NOT
  PERMITTED, not as permitted. The prohibition unambiguously covers the DATA
  (delayed quote table data) and the CONDUCT (download by auto-extraction
  programs/queries/software; only manual ticker symbol entry permitted).
- OBSERVED: no authentication, HTTP 200, `cache-control: s-maxage=5`,
  served via CloudFront/Cloudflare. Given no permissive weight.

Endpoint-specific permission finding: automated retrieval of this endpoint
is NOT PERMITTED on the evidence. A scheduled GitHub Actions fetch is
squarely the described prohibited conduct (scripted auto-extraction, not
manual ticker entry) applied to the same delayed quote-table data, with an
express enforcement threat (IP blocking). No affirmative grant exists
anywhere, and the sitewide terms require written consent / a signed license
for uses beyond personal one-copy viewing.

Note on GEX-0 (S10): the GEX-0 packet's terms leg rested on an owner ruling
that "observed behavior + Cboe published site terms" satisfied the
documentation leg, with a stated posture of personal, non-redistributed,
context-only use. That ruling predates the surfacing of the quote-table
prohibition notice. GEX-0 itself listed "a ToS/robots signal" as a
re-review trigger; the S1 notice is exactly such a signal, so the factual
premise of that ruling is superseded by this packet. GEX-0's technical
observations (field schema, ET-naive per-row last_trade_time, UTC top-level
timestamp) remain valid and are reused below.

## 7. Official programmatic Cboe alternatives

REPORTED (S6, S7) - Cboe All Access API (LiveVol Web API), the closest
sanctioned equivalent:

- Endpoint GET /allaccess/market/option-and-underlying-quotes, documented as
  "a synchronized snapshot of current options and underlying quotes";
  documented response fields include delta, gamma, vega, theta, rho, iv,
  mid_iv, open interest, and underlying/implied-underlying quotes; Greeks
  "powered by Cboe Hanweck". Parameters: root, option_type, date,
  min/max_expiry, min/max_strike, symbol.
- Live / delayed / historical variants (delayed URL path /v1/delayed/...).
  Point-priced per request (option-and-underlying-quotes: live 4 pts,
  delayed 8 pts, historical 3 pts).
- Auth: OAuth 2.0 client-credentials over HTTPS REST; sandbox exists.
- Pricing (publicly listed): free trial 500 pts/day ($0, card
  authorization); Tier 1 $599/mo (150k pts); Tier 2 $799/mo; Tier 3
  $2,499/mo; Tier 4 $4,599/mo. Redistribution-licensed variants $1,499 to
  $5,999/mo: "The All Access API redistribution license covers non-SIP data
  available through the API, permitting the retransmission of real-time,
  delayed, and historical non-SIP data into client-facing applications,
  websites, and/or data feeds."
- True SPX index values require a CSMi subscription (REPORTED 2021 per-user
  fee: delayed $1.22/mo; current fee NOT PUBLICLY STATED). Implied
  underlying prices are included without it.

REPORTED (S8) - DataShop file products (batch alternative): Option EOD
Summary (EOD + 15:45 ET snapshot; optional Calcs add-on with IV and Greeks
including gamma; OI included; SFTP delivery; quote-based pricing); Option
Quote Intervals (1-min or N-min snapshots, "Intraday files are delayed by 15
minutes after each snapshot is recorded", optional Greeks/IV/OI; index
underlying values gated on a Cboe Global Indices license, "$1k+/month");
End-of-Day Theoretical Values (4 PM ET theoretical values and Greeks for SPX
et al.; use-case pricing).

Fit assessment (INFERRED): the All Access API delayed
option-and-underlying-quotes endpoint is a same-provider, sanctioned,
documented replacement for the CDN endpoint's role (chain + gamma + OI +
underlying), at Tier 1 cost or possibly within the free trial for a
low-frequency job, subject to the unknowns in section 19 (per-request chain
caps, delayed-variant timestamp semantics, base-tier display rights for a
public board, SPXW root handling, current CSMi fee). No account was created
and nothing was purchased in this pass.

## 8. data.last_trade_time evidence

- FIELD EXISTENCE - OBSERVED: present in both live fetches of
  options/_SPX.json (section 14), in the sibling quotes/_SPX.json, and in
  the 2026-08-17 GEX-0 samples. Present at two levels with distinct
  meanings: top-level `data.last_trade_time` (the underlying/index) and
  per-option-row `last_trade_time` (per-contract; null on never-traded
  rows: 7,316 of 30,842 rows null in fetch 1).
- FORMAT - OBSERVED: "YYYY-MM-DDTHH:MM:SS", ISO-8601-shaped, naive (no
  timezone suffix), second resolution. Distinct from the top-level
  `timestamp` format "YYYY-MM-DD HH:MM:SS" (space separator).
- DOCUMENTATION - REPORTED (absence): NO official Cboe definition found for
  this field at either level, in any Cboe property searched.
- SEMANTICS (index level) - INFERRED (strong, three independent supports,
  but inference nonetheless): it is the time of the last disseminated SPX
  index value, in US Eastern wall-clock. Supports: (a) observed value
  2026-08-20T16:14:59 is one second before 4:15 PM ET, the end of SPX index
  dissemination; (b) it froze at that value across both overnight fetches
  while the top-level timestamp advanced; (c) `data.volume` is 0 and
  `security_type` is "index" - SPX is a calculated cash index, so a literal
  trade reading is untenable. It is NOT a trade timestamp; no authoritative
  evidence supports "trade" semantics for the index level.
- PROVENANCE: everything above the DOCUMENTATION line is OBSERVED; the
  meaning is INFERRED; nothing about this field is REPORTED, because Cboe
  documents nothing about it.

## 9. Timezone evidence

- Top-level `timestamp`: OBSERVED UTC - "2026-08-21 07:07:07" against HTTP
  `Date: 07:08:01 GMT` and `Last-Modified: 07:07:09 GMT` (fetch 1); same
  pattern in fetch 2 and in GEX-0.
- `data.last_trade_time` and per-row `last_trade_time`: NOT documented
  anywhere. INFERRED US Eastern from: (a) 16:14:59 alignment with the 4:15
  PM ET dissemination end; (b) GEX-0's SPY per-row check (last_trade_time
  14:27:08 read as ET at 18:43 UTC = ~16 min lag, consistent with a
  15-minute delayed feed; any other timezone reading produces nonsense
  lags); (c) the dashboard consumer labels its timestamp "ET (Delayed)"
  (search-cache render, second-hand). Formal timezone documentation:
  ABSENT.
- Consequence: the response mixes a UTC heartbeat with naive-ET market
  fields, and neither is labeled. Any consumer conversion to UTC encodes an
  undocumented inference.

## 10. SPX / index semantic evidence

OBSERVED (fetch 1): `data.symbol` "^SPX", `security_type` "index",
`exchange_id` 5, `volume` 0, bid/ask populated with size 1,
`current_price` 7641.1602 equal to `prev_day_close` off-session, `seqno`
44305785112 frozen across both fetches. REPORTED (absence): none of these
index-level fields are defined in any Cboe document found. INFERRED: quote
and trade shaped fields are repurposed for a calculated index; index-level
bid/ask are synthetic; `current_price` off-session shows the prior close.
The r3 name candidate `underlying_last_trade_utc` is doubly unsupported:
"trade" (no trades exist for the cash index) and "utc" (source value is
naive, inferred ET).

## 11. Option-model gamma freshness evidence

- REPORTED (absence): no Cboe documentation exists for when or how the CDN
  feed's per-row gamma/iv/theo/delta are computed, on what inputs, or on
  what cadence. NO field in the response is documented to timestamp the
  model values.
- REPORTED (nearest lineage, applicability INFERRED): LiveVol All Access
  docs define theo as "Theoretical price at the computed theoretical implied
  volatility" and iv as computed "utilizing the volatility surface"
  (Hanweck); DataShop snapshot products state Greeks are computed per
  snapshot, in ET, delivered on a 15-minute delay. Cboe nowhere states the
  CDN feed shares this pipeline.
- OBSERVED (decisive, this pass): between the two overnight fetches (07:08Z
  and 07:11Z, 3 AM ET) the SAME option row (SPX260821C07640000) changed
  gamma 0.0129 -> 0.0126 and theo 19.393 -> 20.3062 while every market
  input was frozen: index `last_trade_time`, `current_price`, `seqno`, and
  the row's own last-trade fields all identical. The model layer is being
  recomputed off-session on undocumented inputs and an undocumented clock.
- Consequence: option-model values in this feed cannot be attributed to
  session end, to `data.last_trade_time`, or to any observable moment.
  **Option-model Greek observation age is not separately established** -
  and the off-session drift observation makes it strictly worse than
  "unknown but frozen": the values move while the market does not.
- OBSERVED (supporting, GEX-0 + fetch 1): rows with stale or null
  last-trade times still carry populated model fields; an expiring-today
  row carried iv 0.0 with nonzero gamma. Model presence never implies
  market freshness.

## 12. Response snapshot semantics

The response is NOT a synchronized snapshot. It carries three distinct
clocks, none documented:

1. Top-level `timestamp` (UTC): edge regeneration heartbeat. OBSERVED
   advancing every ~1 minute even at 3 AM ET, tracking `Last-Modified`
   within seconds. Confirms owner decision D-2: this is not a freshness
   clock (a 3 AM regeneration carried prior-day market data).
2. Market-input fields (naive ET, inferred): index `last_trade_time`,
   `current_price`, `seqno`, per-row trade fields. OBSERVED frozen
   off-session at prior-session values.
3. Model fields (gamma/iv/theo/delta): no clock at all. OBSERVED drifting
   off-session while clocks 1 advances and 2 is frozen.

Same-response co-delivery therefore proves nothing about co-observation:
each fetch is a fresh envelope around a frozen market layer and a drifting
model layer.

## 13. Observed vs reported vs inferred table

| Claim | Status |
|-------|--------|
| Endpoint returns HTTP 200, no auth, ~13.7 MB, 30,842 option rows | OBSERVED (2026-08-21) |
| Top-level `timestamp` is UTC and tracks Last-Modified (regeneration) | OBSERVED |
| Regeneration continues off-session (~1 min cadence at 3 AM ET) | OBSERVED (two fetches, one night) |
| `data.last_trade_time` exists, ISO naive, second resolution | OBSERVED |
| `data.last_trade_time` froze at 2026-08-20T16:14:59 overnight | OBSERVED (one night, two fetches) |
| `data.last_trade_time` means last disseminated SPX index value | INFERRED |
| `data.last_trade_time` timezone is US Eastern | INFERRED (three supports; undocumented) |
| Quote-table prohibition text (auto-extraction banned, manual entry only, IP blocking, Livevol property) | REPORTED (verbatim, first-hand capture) |
| Site terms: one-copy personal non-commercial; written consent otherwise; no derivative financial products | REPORTED |
| Use of Content requires a signed license agreement | REPORTED |
| CDN endpoint is the dashboard backend | INFERRED (strong) |
| CDN endpoint documented as public API | REPORTED ABSENT (no such documentation exists) |
| Prohibition's letter names the CDN host | UNRESOLVED (no text found either way) |
| Greeks/theo recomputed off-session with frozen market inputs | OBSERVED (decisive pair of fetches) |
| Any timestamp covers the model values | REPORTED ABSENT / contradicted by observation |
| Feed is ~15 minutes delayed | REPORTED for Cboe delayed products generally; INFERRED for this endpoint (GEX-0 SPY lag consistent once); NOT licensed as a precise per-fetch claim |
| Freezes on weekends/holidays | UNPROVEN (no weekend/holiday observation exists) |
| RTH advancement sequence of `data.last_trade_time` | UNPROVEN (both fetches this pass were off-session; GEX-0 observed freshness once during RTH) |
| All Access API delayed endpoint carries gamma/OI/IV/underlying, $599+/mo, redistribution tier exists | REPORTED |

## 14. Bounded live observations

Two read-only GETs of options/_SPX.json, ~4.5 minutes apart, overnight
(off-session), 2026-08-21. No polling loop, no raw-chain persistence (raw
bodies held in session scratchpad only, not committed), no redistribution.
One additional GET of quotes/_SPX.json by a research subagent. robots.txt
GETs on both hosts.

| Field | Fetch 1 (07:08:01Z) | Fetch 2 (07:11:32Z) |
|-------|---------------------|---------------------|
| HTTP Last-Modified | 07:07:09 GMT | 07:11:09 GMT |
| top-level `timestamp` | 2026-08-21 07:07:07 | 2026-08-21 07:11:06 |
| `data.last_trade_time` | 2026-08-20T16:14:59 | 2026-08-20T16:14:59 (frozen) |
| `data.current_price` | 7641.1602 | 7641.1602 (frozen) |
| `data.seqno` | 44305785112 | 44305785112 (frozen) |
| row SPX260821C07640000 gamma | 0.0129 | 0.0126 (moved) |
| row SPX260821C07640000 theo | 19.393 | 20.3062 (moved) |
| row last_trade_time | 2026-08-20T16:14:27 | 2026-08-20T16:14:27 (frozen) |

Row-population facts (fetch 1): 30,842 rows; 10,226 with volume > 0, all
dated 2026-08-20; 7,316 rows null last_trade_time; remainder spread over
prior sessions back weeks. These are single-night observations and are
labeled as such everywhere in this packet.

## 15. Off-session evidence limits

- PROVEN (bounded): overnight freeze of market-input fields across one
  4.5-minute pair on one night; regeneration heartbeat continues
  off-session; model fields drift off-session.
- SUPPORTED BY ONE OBSERVATION: after-hours freeze also seen once in GEX-0
  (2026-08-17); ~16-minute SPY lag once (GEX-0).
- UNPROVEN: weekend behavior, holiday behavior, the RTH advancement
  sequence, lag stability, and any model-Greek synchronization.
- Necessity analysis: a consumer that fails closed when the market
  observation evidence is too old does NOT need weekend/holiday behavior
  catalogued - staleness handling subsumes it. But that design still
  presumes the observation field's meaning and timezone, which are
  inference-only on this feed. Fail-closed engineering cannot manufacture
  documented semantics.

## 16. Strongest truthful display language

Given the evidence, the strongest claims this feed can truthfully support:

- The r3-style claim "GEX structure as of HH:MM, ~15m delayed" is NOT
  licensed: it asserts a model-value age no evidence establishes.
- Charge example A ("Fresh request to a delayed Cboe options source") is
  truthful but nearly information-free (it describes the fetch, not the
  data).
- The strongest supportable form is charge example B/C combined, with the
  inference flagged:
  "Cboe delayed feed. Index observation 16:14 ET (undocumented field,
  timezone inferred). Option-model value age unknown."
- Even that sentence rests on INFERRED semantics for its only number. No
  display language derived from this endpoint can meet a
  documented-semantics bar, because Cboe documents none of the fields.

## 17. Minimum possible schema consequence

RECOMMENDATION: NONE. No schema field is proposed from this pass.

Rationale (charge section 9 bar): provider semantics are insufficient - the
candidate field is undocumented, its timezone and meaning are inference-only,
its "trade" name is factually wrong for a cash index, and the acquisition
channel itself is not permitted for the automated use the field would serve.
Defining `underlying_last_trade_utc` (or any renaming of it) would encode
three unlicensed claims (trade, UTC, observation semantics) into a contract.
If a licensed Cboe channel is later adopted, its documented timestamp fields
(e.g. the All Access API's documented snapshot semantics) define the schema;
naming would follow source truth (an index observation time, not a trade
time).

## 18. Automation viability

Automated (scheduled, scripted) retrieval of
cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json for the intended
GEX product: NOT PERMITTED on the evidence.

- The conduct (auto-extraction of delayed quote-table data; anything other
  than manual ticker entry) is expressly prohibited on the data's own
  display pages, with an IP-blocking enforcement statement.
- The sitewide terms permit only one-copy personal non-commercial viewing
  and prohibit derivative financial products without written consent; the
  Use of Content page requires a signed license.
- No affirmative permission for the CDN endpoint exists anywhere in Cboe's
  public materials; the only unresolved question (whether the prohibition's
  letter reaches the CDN host) cannot produce permission, only a difference
  between "expressly prohibited" and "unpermitted".
- Additionally adverse for GEX-3 specifically: publishing GEX derived from
  this data to a public dashboard sits against the derivative-work and
  redistribution language independently of the automation question.

Current repo exposure: no scheduled workflow on main invokes
`tools/gex_snapshot.py` or touches cdn.cboe.com; existing use is manual and
test-fixture based. This packet takes no action on the existing tool (out
of charge scope) but records that even manual scripted fetches sit
uncomfortably against the manual-ticker-entry-only language; owner
awareness item.

## 19. Unresolved unknowns

1. Whether the quote-table prohibition's letter formally reaches the
   cdn.cboe.com host (no Cboe text names it; resolvable only by Cboe).
2. cdn.cboe.com/robots.txt contents (403; likely absent).
3. All Access API specifics load-bearing for a sanctioned migration:
   full-chain SPX+SPXW retrieval mechanics and per-request caps/points,
   delayed-variant timestamp semantics, base-tier (non-redistribution)
   display rights for a public personal dashboard, SPXW root handling,
   current CSMi index-value fee. Resolvable only via signup/sales contact
   (not authorized this pass).
4. Weekend/holiday/RTH advancement behavior of `data.last_trade_time`
   (unproven; moot for the current endpoint given section 18, relevant only
   if an owner ever authorizes a manual-use design).
5. The CDN feed's model-recompute cadence and inputs (undocumented;
   evidenced only as "moves off-session").

## 20. Verdict

Scope: "Cboe as the provider for the intended automated published-board GEX
context."

VERDICT: EVIDENCE INCOMPLETE

Decomposition:

- The CURRENT access method (CDN delayed-quotes endpoint, automated) is
  resolved NEGATIVE: not permitted (section 18). If the provider question
  were confined to this endpoint, the verdict would be PROVIDER NOT VIABLE.
- The provider question as charged is wider: Cboe offers a sanctioned,
  documented, same-lineage programmatic channel (All Access API delayed;
  section 7) that plausibly supports the product - including a documented
  "synchronized snapshot" semantics claim the free feed lacks - but its
  load-bearing permission and semantic specifics (section 19 item 3) cannot
  be closed without signup/spend decisions that are Dustin's alone.
- The semantic leg on the current endpoint is also insufficient standing
  alone: no documented field meanings, inferred timezone, and
  observationally unknowable Greek age (section 11).

Per the charge's verdict standard: PROVIDER VIABLE fails (permission for
the intended access method is not establishable); PROVIDER NOT VIABLE would
overclaim (a sanctioned Cboe path exists and is unpriced-but-plausible for
this product); a load-bearing permission/semantics set remains unknown on
the sanctioned path. EVIDENCE INCOMPLETE. Returned to Dustin / HELM per
charge section 11; no second-provider research performed.

## 21. Downstream consequences

- GEX-1b (producer evidence field): EVIDENCE BLOCKED. The candidate field's
  semantics are undocumented and the automated acquisition it would serve
  is not permitted from the current endpoint. No schema field is proposed
  (section 17). Any GEX-1b revival follows a provider decision, not more
  numeric thresholds.
- GEX-2 (PR #261, frozen r3): remains DESIGN INCOMPLETE, untouched. This
  packet supersedes the factual basis of its provider-freshness premises:
  "freezes overnight/weekend/holiday" is part-proven/part-unproven (section
  15), "~15 minutes behind" is not licensed as a precise claim (section
  13), `underlying_last_trade_utc` naming is unsupported (section 10), and
  the semantics-VERIFIED wording for last-trade fields overstated what
  documentation exists. Any packet rewrite awaits Dustin's
  boundary/provider ruling on this packet's verdict.
- GEX-3 (automated publish): EVIDENCE BLOCKED with the current source -
  automation is not permitted, and public re-display is independently
  adverse under the terms. The only Cboe-sanctioned path evidenced is a
  licensed API product (owner decision: cost tier, redistribution vs
  base-tier display rights, CSMi add-on), or file-based DataShop delivery
  for an EOD-shaped product.
- Existing `tools/gex_snapshot.py`: no scheduled exposure today; flagged
  for owner awareness (section 18), no action taken.

## Charge compliance

NO IMPLEMENTATION / NO PRD / NO GATE A / NO MERGE. PR #261 untouched. No
second provider researched. No accounts created, nothing purchased. Two
bounded live fetches, raw bodies not committed. This packet is the pass's
only substantive artifact.
