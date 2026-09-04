# GEX PROVIDER-RIGHTS RECONCILIATION (owner-decision support)

Date: 2026-09-03 (primary sources re-fetched 2026-09-03 22:50-23:20 UTC).
Mode: RECON / owner-decision support. Basis: Helm charge "GEX PROVIDER-RIGHTS
FINAL RECONCILIATION". Main: a76e7a4. GEX-4 review-clean package: PR #309 @
39931e5 (design GO per Helm; not reopened here).

Model note: this pass ran on Fable 5.1 (the charge named Opus 4.8; the
session model cannot be switched from inside the session).

This is evidence reconciliation for one owner ruling. It is not legal advice
and not advocacy. Standard applied: HTTP 200 is not permission; absence of a
prohibition is not permission; an inferred reading is not provider
authorization. Each use case gets exactly one of PERMITTED ON EVIDENCE / NOT
PERMITTED ON EVIDENCE / EVIDENCE INCOMPLETE.

Nothing was modified or disabled. No provider accounts were created. One
live GET of the existing endpoint was made earlier this session (the GEX-4
recon, 22:42 UTC) under the existing authorized path, plus a HEAD request
and one fetch of the public quote-table page for this pass; those
retrievals are themselves the conduct classified in A below and are
disclosed for owner awareness.

--------------------------------------------------------------------------

## 1. CURRENT AUTHORITY CONFLICT

Binding main says:
- GEX-0 `PROVIDER VIABLE` (scoped: personal / non-redistributed /
  context-only), `audits/gex-0-cboe-evidence-2026-08/...PACKET_2026-08-17.md`
  :47, :186, :251. Its terms leg rests on an owner ruling that "observed
  behavior + Cboe published site terms satisfy the s4.2 documentation leg";
  the same packet lists "a ToS/robots signal" as a STOP trigger (:303-306).
- GEX GO, `docs/DECISIONS.md:382-404` (2026-08-20), on that evidence.
- GEX-1/2/3 IMPLEMENTED/COMPLETE (`docs/plans/decision-support-workplan-v0.1.md:50-53`).
  GEX-3 is live: `.github/workflows/hourly_alert.yml:203-207` runs
  `tools/gex_snapshot.py` on every weekday hourly slot and the rendered card
  publishes to the public GitHub Pages board.

Unmerged, closed 2026-08-31 without any DECISIONS entry (verified: no
DECISIONS line mentions #262, #263, Massive, automated-use, or the
quote-table notice):
- PR #262 (head 30cc254, 2026-08-21): automated retrieval of the CDN
  delayed-quotes endpoint NOT PERMITTED on evidence; public re-display
  independently adverse; sanctioned Cboe path exists but unpriced/unsigned;
  verdict EVIDENCE INCOMPLETE for "Cboe as provider", NEGATIVE for the
  current endpoint.
- PR #263 (head f82e853, 2026-08-21): Massive individual tier: automated
  personal retrieval PERMITTED; derived GEX on the public board NOT
  PERMITTED; private derivation/display EVIDENCE INCOMPLETE pending one
  written clarification; PROVIDER NOT VIABLE for the public surface.

The conflict: main's GEX GO stands on a factual premise (no adverse ToS
signal) that #262 falsified on 2026-08-21 with first-hand primary evidence,
and GEX-0's own STOP trigger fired; no owner re-ruling was recorded, and
GEX-3 subsequently made the retrieval automated and the display public.
Section 2 shows the #262 evidence is current as of today.

## 2. CURRENT PRIMARY EVIDENCE (re-fetched this pass)

| # | Source (2026-09-03) | Status | Content |
|---|---|---|---|
| P1 | https://www.cboe.com/delayed_quotes/spx/quote_table (HTTP 200, 15.5 MB, fetched directly) | OBSERVED verbatim | "PLEASE NOTE: IT IS STRICTLY PROHIBITED TO DOWNLOAD DELAYED QUOTE TABLE DATA FROM THIS WEB SITE BY USING AUTO-EXTRACTION PROGRAMS/QUERIES AND/OR SOFTWARE. CBOE WILL BLOCK IP ADDRESSES OF ALL PARTIES WHO ATTEMPT TO DO SO. THIS DATA IS PROPERTY OF CBOE LIVEVOL OR ITS DATA PROVIDERS. DOWNLOADING THIS DATA IN ANY OTHER WAY THAN BY MANUAL TICKER SYMBOL ENTRY IS STRICTLY PROHIBITED." The page links only /terms, /use-of-content, /global-disclaimers, /privacy. |
| P2 | https://www.cboe.com/terms/ ("Last Updated: November 16, 2022") | REPORTED verbatim | s2: "You may view, print and download one copy of the Materials for your personal non-commercial use in connection with products and services offered by Cboe ..." and "You may not otherwise copy, reproduce, alter, store either in hard copy or in an electronic retrieval system, license, transmit, display, broadcast, create a derivative work from, use to verify or correct other data or information, publish, rent, sublicense, distribute, or otherwise use in whole or in part in any other manner the Materials without Cboe's prior written consent except to the extent that such use constitutes 'fair use' ..."; derivative work example "a financial product, service or index"; s4: "not intended for trading purposes". No explicit automated-access clause in /terms/ itself. |
| P3 | https://www.cboe.com/use-of-content/ | REPORTED verbatim | "In order to use any Cboe logo, data, photo/image or other content contained in Cboe websites (collectively 'Cboe Content'), you must receive approval in advance from Cboe." "You are not approved to use Cboe Content until a license agreement has been signed by both you and Cboe." Requests: permissions@cboe.com with intended use, screenshots/links of where it will be displayed, distribution plans (hits per month), duration; "typically ... within five business days". |
| P4 | robots.txt | OBSERVED | www.cboe.com: Disallow only /book/ and /*market_statistics/volume_reports/; cdn.cboe.com/robots.txt: HTTP 403. No permissive weight either way. |
| P5 | https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json (HEAD) | OBSERVED | HTTP/2 200, keyless, cloudfront/cloudflare, `cache-control: s-maxage=5`, last-modified advancing off-session. Technical accessibility only. |
| P6 | https://datashop.cboe.com/cboe-all-access-api | REPORTED | Free Trial: 500 points/day, $0/mo, 14-day, card authorization. Tier 3 $2,499/mo (1,250,000 pts), Tier 4 $4,599/mo (4,000,000 pts) reproduced; Tier 1/2 prices not rendered in today's fetch (#262 reported $599 / $799). Signup distinguishes "Individual ... if you will only be using the data for yourself" from "Firm". "If you intend to redistribute data to any external individuals or third parties, the All Access API redistribution license pricing will apply"; "The All Access API redistribution license covers non-SIP data ... permitting the retransmission of real-time, delayed, and historical non-SIP data into client-facing applications, websites, and/or data feeds." |
| P7 | https://www.cboe.com/global-disclaimers/ | REPORTED absence | No delayed-data, automation, or derived-data provisions. |
| P8 | Repo state on main | OBSERVED | Repository public; GitHub Pages enabled and public at https://dwats250.github.io/cuttingboard/ ; hourly_alert.yml:203-207 performs the automated GET; `logs/gex_snapshot.json` never committed; the rendered GEX card is in the published HTML. |

Not re-fetched this pass (used as #262/#263 REPORTED): the All Access API
endpoint documentation (`/allaccess/market/option-and-underlying-quotes`,
greeks incl. gamma, OI, delayed variant 8 points/request); Massive terms
(Individuals ToS 2025-07-18, Market Data ToS 2025-08-28). No general-web
research was performed; no additional providers were examined.

Provider terms change since 2026-08-21: NONE FOUND. /terms/ carries the same
2022-11-16 date and text; the quote-table notice is byte-for-byte the #262
capture; use-of-content is unchanged in substance.

## 3. USE-CASE MATRIX

| Use | Classification | Basis |
|---|---|---|
| A. Automated retrieval (hourly keyless GET of the CDN `_SPX.json` from GitHub Actions) | NOT PERMITTED ON EVIDENCE | P1 prohibits downloading delayed quote-table data "by using auto-extraction programs/queries and/or software" and any download "other than by manual ticker symbol entry", with an IP-blocking enforcement statement. The CDN JSON is the same delayed-quotes data (path vocabulary and payload; backend tie INFERRED, unchanged from #262). Whether P1's words "from this web site" reach the cdn.cboe.com host is UNRESOLVED; unresolved coverage cannot yield permission. P2 s2 permits only viewing/printing/downloading one copy for personal use; storing "in an electronic retrieval system" needs written consent. P3 requires a signed license for any use of Cboe data. No affirmative grant exists anywhere. P5's HTTP 200 carries no weight. |
| B. Local computation (derive modeled GEX from gamma, OI, strike, spot; no raw persistence) | EVIDENCE INCOMPLETE (and moot for the current source) | P2 s2 forbids creating "a derivative work from" the Materials without consent; the parenthetical example ("a financial product, service or index") does not obviously reach a private context analytic, and fair use is carved out, so the text does not resolve personal derivation either way. Standing alone: incomplete. In practice B cannot be cleaner than its input: under the current endpoint its input is A. |
| C. Current public display (GEX-2/3 card on the public Pages board) | NOT PERMITTED ON EVIDENCE | P2 s2: "display ... publish ... distribute" the Materials or a derivative work requires prior written consent; P3: a signed license precedes any use of Cboe data; P6 shows Cboe's own sanctioned product treats display to "external individuals or third parties" as redistribution requiring a redistribution license. Plus the input is A. |
| D. GEX-4 public display (per-strike modeled magnitudes, MODEL NET*, bins, anchors; no raw chain) | NOT PERMITTED ON EVIDENCE | Inherits A and C. GEX-4 changes degree (31 bins vs five numbers), not kind; nothing in GEX-4 improves or worsens the classification. |
| E. Private / operator-only variant (same computation, display only to Dustin, no redistribution) | NOT PERMITTED ON EVIDENCE for the current endpoint; EVIDENCE INCOMPLETE under a sanctioned source | Privacy resolves the display leg (P2 s2 one-copy personal use; nothing shown to third parties) but not the acquisition leg: A is prohibited conduct regardless of who sees the output. A manual, on-demand, single-copy personal use (typing the ticker on the Cboe page) is the only Cboe-permitted shape of E on this evidence, and it is not the scripted JSON fetch the tool performs. Under the sanctioned Cboe All Access API "Individual" internal-use path or Massive Individual tier, E becomes EVIDENCE INCOMPLETE pending the license text (Cboe) or one written clarification (Massive, per #263). |

Answers to the ten questions:
1. Automated retrieval through the current endpoint: NOT PERMITTED ON EVIDENCE.
2. Personal / non-commercial use does not change it: P1 is conduct-based
   (auto-extraction vs manual entry), not purpose-based; P2's personal grant
   is one copy for viewing.
3. Local derivation: EVIDENCE INCOMPLETE on the text; moot while the input
   is A.
4. Public display of derived analytics: NOT PERMITTED ON EVIDENCE (P2 s2
   display/publish/derivative-work consent; P3 signed license; P6
   redistribution framing).
5. Provider language that governs GEX-4: P2 s2 ("create a derivative work
   from", "display", "publish", "distribute", "store ... in an electronic
   retrieval system"), P1 (auto-extraction), P3 (signed license), P6
   (redistribution to third parties). Yes, materially.
6. No raw chain published: removes the most serious exposure (bulk
   redistribution of the Materials) but does not change any classification
   above; derived display and automated acquisition are governed
   independently.
7. Existing GEX-1/2/3: YES, implicated independently of GEX-4 (section 5).
8. Genuinely operator-private surface: resolves display, NOT acquisition;
   on current evidence it does not, by itself, make the current endpoint
   permitted (E).
9. Sanctioned Cboe path: exists (section 7); its permission specifics for
   this exact use are EVIDENCE INCOMPLETE without signup or written answer.
10. Exact unresolved facts: section 8.

## 4. PR #262 CLAIM-BY-CLAIM DISPOSITION

| #262 claim | Disposition today |
|---|---|
| Quote-table prohibition notice (verbatim S1) | CONFIRMED CURRENTLY (P1, first-hand, identical text) |
| /terms/ s2 one-copy personal use; consent for store/transmit/display/distribute/derivative; s4 not for trading | CONFIRMED CURRENTLY (P2; Last Updated 2022-11-16, unchanged) |
| Use of Content: approval in advance, signed license | CONFIRMED CURRENTLY (P3) |
| robots: www no rule on delayed_quotes/api; cdn 403 | CONFIRMED CURRENTLY (P4) |
| CDN endpoint undocumented as a public API / product | CONFIRMED (absence; not re-swept broadly this pass; no contrary evidence found) |
| CDN endpoint is the quote-table backend | NARROWED: still INFERRED (strong); not independently traced this pass |
| Whether the notice's letter reaches cdn.cboe.com | CONFIRMED UNRESOLVED (no Cboe text names the host); still cannot yield permission |
| Automated retrieval NOT PERMITTED | CONFIRMED CURRENTLY |
| Public re-display adverse under derivative-work / distribution language | CONFIRMED CURRENTLY (P2 s2, P3, P6) |
| GEX-0 owner-ruling premise superseded by the ToS signal | CONFIRMED (GEX-0 packet :303-306 names the trigger) |
| "No scheduled workflow on main invokes tools/gex_snapshot.py" | SUPERSEDED: PRD-310 merged; hourly_alert.yml:203-207 runs it hourly on weekdays; the card publishes to the public board |
| All Access API: free trial $0/500 pts per day; Tier 3 $2,499; Tier 4 $4,599; redistribution license text | CONFIRMED CURRENTLY (P6) |
| All Access API: Tier 1 $599, Tier 2 $799, delayed option-and-underlying-quotes endpoint with gamma/OI at 8 pts/request, CSMi index fee | NOT REPRODUCED this pass (not re-fetched; not contradicted) |
| Freshness/semantics findings (undocumented last_trade_time, off-session greek drift, three clocks) | Out of this charge's scope; not re-examined. Consistent with this session's own observation of degenerate post-close same-day gammas (GEX-4 recon F3). |
| Verdict: endpoint NEGATIVE; provider EVIDENCE INCOMPLETE | CONFIRMED CURRENTLY |

Net: every load-bearing #262 quotation is current; the only superseded
claim moved AGAINST the repo (exposure is now automated and public).

## 5. IMPACT ON EXISTING GEX-1/2/3

Independent of GEX-4, on the same evidence:
- GEX-1 producer (manual invocation): scripted JSON extraction, not manual
  ticker entry; NOT PERMITTED ON EVIDENCE as conduct, though each manual run
  is a bounded single act.
- GEX-3 hourly refresh (live on main, weekdays 07:10-13:10 PT plus the
  doubled morning slots): the exact conduct P1 prohibits, on a schedule,
  from GitHub-owned IP ranges, with an IP-blocking enforcement statement;
  NOT PERMITTED ON EVIDENCE.
- GEX-2 card on the public board: derived display without written consent
  (C); NOT PERMITTED ON EVIDENCE.
No change was made. Returned for Helm ruling (section 9 names the interim
choice).

## 6. IMPACT ON GEX-4

The GEX-4 design (PR #309) is provider-agnostic in its arithmetic (gamma x
OI x spot^2 per contract, per-strike magnitudes, bins, anchors) but not in
its producer contract: `tools/gex_snapshot.py` field names, admissibility
rules (Cboe integer-valued float OI, OCC symbol parsing), spot basis
(`data.current_price`), the R12 raw-key list, and the R6 settlement gate
(root + expiry + feed timestamp) are all Cboe-CDN-shaped. Under a sanctioned
Cboe API the shape is similar (same Hanweck greeks lineage, documented
snapshot semantics) but field names and timestamps differ; under Massive the
greeks omission semantics, OI definition, and I:SPX spot basis differ (#263
s8-s12). Consequence: the GEX-4 PRD cannot be drafted with a stable FILES
and data contract until the acquisition path and delivery surface are ruled.

## 7. SANCTIONED CBOE PATH

Cboe All Access API (P6; endpoint semantics per #262 s7, REPORTED):
- Free trial $0, 500 points/day, 14 days, card authorization. #262 reports
  the delayed option-and-underlying-quotes call at 8 points; one hourly
  weekday cadence (about 7 calls/day) would be ~56 points/day, inside the
  trial budget for its 14 days only.
- Paid: Tier 1 $599/mo (REPORTED by #262, not reproduced today); Tier 3
  $2,499/mo and Tier 4 $4,599/mo reproduced. Redistribution license
  (client-facing websites) $1,499-$5,999/mo per #262; today's page confirms
  redistribution pricing applies when data is shown to "external individuals
  or third parties".
- "Individual ... only be using the data for yourself" is a signup option
  (P6): a sanctioned internal-use personal path exists in product form. Its
  license text (derived analytics / non-display computation / self-display /
  display on a personal but public page) was NOT read and is EVIDENCE
  INCOMPLETE. SPX index value may need a CSMi add-on (#262, REPORTED).
Massive (PR #263, not re-fetched): Individual $29-78/mo; automated personal
retrieval PERMITTED; derived GEX on the public board NOT PERMITTED under
either reading of its Derived Works clause; private derivation/display
EVIDENCE INCOMPLETE pending one written clarification. It does not resolve
the public-board problem; it plausibly resolves a private one.

## 8. EXACT UNRESOLVED FACTS (written provider answer required, not inference)

U1. Cboe: is automated retrieval of
    `cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json` at a bounded
    hourly cadence, for one person's own derived context, permitted, and is
    display of derived (non-raw) GEX figures on a personal, publicly
    reachable dashboard permitted? The provider's own documented route is
    permissions@cboe.com (P3); it asks for exactly the facts Cuttingboard can
    state (use, screenshots/links, hits per month, duration).
U2. Cboe All Access API, Individual internal-use tier: does the license
    permit programmatic derived analytics and self-display, and does a
    personal public page count as redistribution? (Only answerable from the
    license text at signup or by sales.)
U3. Massive Individual: the #263 USE-B question (personal, non-redistributed
    derived analytic from greeks/OI/index value) - one written question.
Nothing else in the matrix turns on an unknown; A, C and D are resolved
NEGATIVE on current text.

## 9. OWNER OPTIONS (finite; only those the evidence supports)

1. WRITTEN CLARIFICATION REQUIRED (Cboe, U1). Cost $0; the provider's own
   process; typical five business days. Outcome resolves A-E for the current
   source in one answer. Interim sub-decision (owner-held): keep the GEX-3
   hourly step running, or pause it (a workflow change) until the answer.
2. LICENSE REQUIRED (Cboe All Access API, U2). Sanctioned automated
   acquisition from the same lineage; free trial then ~$599/mo (REPORTED)
   for private use; public display requires the redistribution tier
   ($1,499+/mo REPORTED), disproportionate for a personal board. Requires a
   new producer contract (new PRD), not GEX-4 as written.
3. PROVIDER CHANGE REQUIRED (Massive Individual, $29-78/mo) WITH a private
   delivery surface. A is permitted there; private E pends U3; public C/D are
   NOT PERMITTED. Requires re-scoping the delivery surface plus a new
   producer contract (new PRD).
4. STOP GEX. Supported as a choice; not required by the evidence given 1-3.
Not supported on current evidence: PUBLIC GO; PRIVATE-ONLY GO on the current
endpoint (E fails on acquisition).

## 10. RECOMMENDED OWNER RULING

Rule WRITTEN CLARIFICATION REQUIRED (option 1) now, and decide the interim
state of the GEX-3 hourly step explicitly rather than by default. Rationale:
it is free, it is the route Cboe itself publishes, it answers the exact
question with no inference, and it keeps GEX-4 intact if the answer is yes.
If the answer is no or absent after a bounded wait (suggest ten business
days), choose between option 3 with a private surface (cheapest, needs U3
and a surface change) and option 2 (same-lineage data, private only unless
the redistribution tier is bought). Recording this ruling in
`docs/DECISIONS.md` would also close the authority gap in section 1 (the
2026-08-21 packets were never adjudicated).

## 11. CAN THE GEX-4 PRD PROCEED?

HOLD. The design is GO and review-clean, but its producer data contract,
settlement gate, and delivery surface all depend on which acquisition path
and surface the owner rules. Drafting the PRD before U1 (or a licensing
choice) would fix FILES and a schema to a source whose automated use is NOT
PERMITTED ON EVIDENCE today.
