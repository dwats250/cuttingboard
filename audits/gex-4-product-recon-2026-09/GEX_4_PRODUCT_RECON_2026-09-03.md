# GEX-4 PRODUCT RECON - structural profile / level map

Date: 2026-09-03. Mode: RECON (product design). Basis: Helm charge "GEX-4
PRODUCT RECON / STRUCTURAL PROFILE". Main at recon: a76e7a4 (HEAD == origin/main).
Recommendation: BUILD (revised toward a net + gross strike ladder, not the
net-only or call/put-split forms). No production code, no PRD allocated.

Non-authoritative: this artifact records findings and a recommendation. Every
product ruling below is Helm-held until Dustin accepts it.

Evidence files: `evidence/` (live-chain analysis text, selection-rule edge
cases, prototype HTML + generator, analysis script). The raw Cboe payload
(12.7 MB) was NOT committed (non-redistribution posture); it lives only in the
session scratchpad.

Data used: one live keyless GET of the existing endpoint at 2026-09-03
22:42:44 UTC (18:42 ET, post-close), fetched through the producer's own
`_http_get`, written to the scratchpad only. `logs/gex_snapshot.json` was not
touched. The committed-on-disk artifact from 2026-08-20 20:41 UTC (also
post-close) was used as a second sample. LIMITATION: no intraday sample was
obtainable this session; every 0DTE statement below is from post-close feeds.

--------------------------------------------------------------------------

## 1. CURRENT CAPABILITY

What exists (all CONFIRMED by reading current code on a76e7a4):

- Producer `tools/gex_snapshot.py` (PRD-306, patched by PRD-307): one GET,
  per-contract admissibility, `_gex()` per contract, per-strike call/put/net
  dicts, five derived outputs, atomic write of `logs/gex_snapshot.json`.
- Consumer `cuttingboard/delivery/gex_card.py` (PRD-309): identity + freshness
  + coherence gate, `GexCard` model, HTML fragment; suppresses to "" so the
  dashboard is byte-identical to `tests/data/dashboard_pre_gex_golden.html`.
- Cadence (PRD-310): `.github/workflows/hourly_alert.yml:203-207` runs the
  producer best-effort before Render; cron `10 14-21 * * 1-5` (07:10-13:10 PT)
  plus the 06:30/06:45 PT doubled slots. Artifact is run-local only: never
  restored, staged, or published (`git ls-files logs/ | grep gex` is empty).
  The rendered board goes to the `publish` branch. The daily `cuttingboard.yml`
  render never runs the producer, so the 06:00 PT publish drops the card until
  the next hourly refresh (accepted PRD-310 R3 semantics).
- Placement: the card is the FIRST child of `<details id="details-history">`
  (renderer `:3395-3407`), i.e. inside the operator-zone disclosure, not above
  the fold. Above the fold GEX is one tape row "GEX . CONTEXT ONLY".
- `market_state_panel.py` POSITIONING uses only `GexCard.net_usd`; the renderer
  does not import that module (see anomaly A3).

What it answers well:
- Sign and size of the whole-chain configured-assumption net (one number).
- Three single strikes (largest call-side, largest put-side, largest |net|)
  with distance from spot; 0DTE share of absolute GEX; as-of time.

What it does not answer:
- Where the paper sits relative to spot across strikes; whether the structure
  is one spike or a ridge; whether the three anchors are lone or part of a
  cluster; whether a large "wall" is one-sided or two-sided paper; anything
  about the 20-30 strikes around spot that a trader actually looks at.
- On the 2026-09-03 chain the card would read: Net +80.4B, Dominant 7800
  (+0.67%), Call wall 8000 (+3.26%), Put wall 8000 (+3.26%), 0DTE 2.5%.
  "Call wall = put wall = 8000" is unexplained by the card; see section 3.

## 2. DISCARDED INFORMATION (computed, then dropped at serialization)

In `_build_artifact` (`tools/gex_snapshot.py:315-323`), exactly these
intermediates exist and are discarded:

| intermediate | shape | survives? |
|---|---|---|
| `call_by_strike[K]` = sum over included calls at K of gamma*OI*100*spot^2*0.01 (>= 0) | dict strike -> float, 809 keys live | only argmax (call_wall) |
| `put_by_strike[K]` = -1 * same over puts (<= 0) | dict, 809 keys | only argmax |abs| (put_wall) |
| `net_by_strike[K]` = call + put | dict | only argmax |abs| (dominant) and the total |
| per-contract `abs(_gex)` inside `_zero_dte` | scalar accumulation only | share + per_root totals |

Not computed anywhere: per-expiry per-strike structure (only the 0DTE date
bucket is distinguished), any bin/window, any gross-by-strike (abs call + abs
put). The provider row also carries iv/delta/theo/volume etc.; none is used by
the producer and none may be persisted (PRD-306 R12).

Hypothesis in the charge ("producer computes call/put/net by strike and reduces
it to five outputs"): CONFIRMED exactly.

## 3. REAL-DATA FINDINGS (live chain, 2026-09-03 18:42 ET, spot 7747.71)

Facts (evidence/live_chain_analysis_2026-09-03.txt,
evidence/bins_topn_sidedness_2026-09-03.txt):

| quantity | value |
|---|---|
| contracts admitted | 28,492 / 28,492 |
| distinct strikes | 809 (200..20000); 669 with nonzero gross |
| chain net (configured sign) | +80.4B |
| chain gross (abs call + abs put) | 595.5B |
| chain |net| / gross | 0.135 |
| gross within +/-1% / 2% / 3% / 5% / 10% of spot | 33% / 48% / 56% / 80% / 94% |
| strike pitch within +/-3% | 5 points everywhere (93 strikes) |
| gross on 25-multiple strikes within +/-3% | 60%; the other 40% (134B) is spread over 74 five-point strikes, 1-5B each, almost none 0DTE |
| largest expiry by gross | 2026-09-18 monthly, 35.6% of chain gross |
| 0DTE (2026-09-03) contracts still in the post-close feed | 504, 14.8B gross, share 2.5% |

Observation F1 - cancellation is the dominant feature of this chain, and it is
concentrated at round strikes:

| strike | dist | call-side | put-side | net | gross | |net|/gross |
|---|---|---|---|---|---|---|
| 8000 | +3.26% | +38.06B | -32.94B | +5.12B | 71.0B | 0.07 |
| 7750 | +0.03% | +19.31B | -13.56B | +5.75B | 32.9B | 0.17 |
| 7700 | -0.62% | +13.32B | -14.23B | -0.92B | 27.6B | 0.03 |
| 7000 | -9.65% | +12.37B | -13.87B | -1.50B | 26.2B | 0.06 |
| 7600 | -1.91% | +8.74B | -10.68B | -1.93B | 19.4B | 0.10 |

Cause at 8000 (provider-observed rows): SPX 2026-09-18 8000 call OI 273,400
and put OI 263,216, both gamma 0.0007; the same near-equal call/put OI holds at
8000 across Oct, Dec and 2027 expiries. Near-equal call and put OI at a deep
strike across expiries is the footprint of box-spread / synthetic-forward
financing paper. Under the configured sign convention a same-strike call/put
pair nets to ~0 (which is also the true gamma of a box). So:

- The current "Call wall 8000 / Put wall 8000" is an OI-argmax captured by
  financing paper, not two directional walls. The card cannot show this.
- Net-only by strike hides the second largest bin next to spot (7700: gross
  39.5B in the 25-pt bin, net +0.03B) entirely.
- Gross-only would overstate box strikes as "concentration".
- Whether a cancelling strike is truly flat gamma (box/conversion) or is
  two large same-sign positions that the uniform convention happens to cancel
  (e.g. a straddle) is NOT determinable from OI. That is the honest statement
  the display must make, not resolve.

Observation F2 - the top-N-by-gross list is not spatially useful on its own:
N=16 covers 51% of gross and spans 7000..8000; N=32 reaches 6000 and still only
64%. Nearest-N is worse (N=32 = +/-1%, 34%). The structure lives in a window
around spot plus a few far outliers.

Observation F3 - 0DTE post-close: the feed at 18:42 ET still carried 504
contracts expiring 2026-09-03 (PM-settled SPXW, already expired), and their
Cboe-model gammas are degenerate (7750 call 0.0331 vs put 0.11). The Aug-20
artifact (16:41 ET) shows the same shape with 7.6%. PRD-306.md:274-275 expects
"outside market hours ... numerator legitimately 0"; on an expiry day after the
close that expectation is FALSIFIED by observation. The last hourly refresh at
13:10 PT (16:10 ET) is after the 16:00 ET expiry close; whether the feed has
dropped the expired contracts by 16:10 ET is UNKNOWN (not sampled). Not this
slice's scope; flagged in section 17.

Observation F4 - sidedness: whole chain 47% of gross above spot / 53% below;
within +/-5%, 52% above, and call-side is 58% of gross. Above spot the paper is
mostly call-side (|net|/gross 0.75-0.9); at and below spot it is two-sided
(|net|/gross 0.03-0.26). That asymmetry is the single most informative thing in
the chain and is invisible today.

## 4. PRODUCT VERDICT

The highest-value next GEX capability is a bounded SPX strike ladder around
spot showing, per 25-point strike bin, the configured-sign NET as a signed bar
over a neutral GROSS extent (call-side to the right, put-side to the left), with
the three existing anchors marked, a text line for material bins beyond the
window, and a numeric disclosure. Preserving the discarded per-strike structure
IS the highest-leverage move; the Helm hypothesis is CONFIRMED with three
revisions: (a) net + gross, not net-only and not a call/put split; (b) 25-point
bins in a fixed 31-bin window around the spot bin, not a distance-% or top-N
rule; (c) 0DTE stays a number, no per-strike 0DTE layer in v0.

## 5. RECOMMENDED V0

Visualization (winner of section 14): vertical strike ladder, highest strike on
top (same orientation as the D3 level ladder), one row per 25-point bin, 31
rows. Inline SVG, attribute-styled, server-rendered inside the existing
`#gex-context` fragment. No JS (renderer test pins exactly one `<script>`).

Row anatomy (left to right): strike label (100-multiples in ink, others muted)
| anchor marker column (C, P, D) | zero axis with put-side extent to the left
and call-side extent to the right in neutral gray, the net bar overlaid in blue
(positive) or red (negative) | net value in $B. Spot is a dashed line at its
exact position with the label "SPX <spot>". Native SVG `<title>` per bar gives
the hover tooltip without JS.

Default-visible (inside the existing details-history disclosure, as today):
- existing rows: Net, Dominant, Call wall, Put wall, 0DTE (unchanged)
- new row: Gross <chain gross $B>, "<n>% within window"
- the ladder
- one line: "beyond window: 7000 (-9.7%) gross 26.4B net -1.7B" or "beyond
  window: none >= 2% of chain gross"
- legend/footnote lines (exact copy in section 12)

Disclosure (`<details>` inside the fragment, house idiom, JS-free): "strike
bins by gross" table, top 8 bins in the window by gross, columns bin / dist /
call-side / put-side / net.

Mobile: viewBox 358 x 402, width 100%, max-width 520px (identical strategy to
the D4 chart). At 360px device width the rendered row pitch is ~11 px and the
label font ~9.6 px, above the 9 px floor measured for PRD-330. Nothing measures
the client. 31 rows x 12 units = 372 units of ladder; the whole card is ~600 px
tall on a phone, inside a disclosure that is closed by default.

Under-5-seconds read: spot line position; which side the blue/red mass is on;
where the wide gray bars are; whether a wide gray bar has a thin net bar.

## 6. QUANTITATIVE SEMANTICS

Per contract c (existing, unchanged): gex(c) = s(c) * gamma_c * OI_c * 100 *
spot^2 * 0.01, s = +1 for calls, -1 for puts. gamma_c is the provider's
model gamma (provider model output); OI_c is provider-observed; spot is
provider-observed `data.current_price`; 100 and 0.01 are configured; s is the
configured assumption.

Per strike K (existing intermediates, to be serialized):
- call_side(K) = sum of gex(c) over included calls at K, >= 0
- put_side(K)  = sum of gex(c) over included puts at K, <= 0 (signed, as the
  producer holds it)
- net(K) = call_side(K) + put_side(K)
- gross(K) = call_side(K) + |put_side(K)|  (Cuttingboard-derived arithmetic,
  no sign assumption)

Per bin b (consumer-derived): bin(K) = floor((K + 12.5) / 25) * 25; each of
call_side, put_side is summed over K in the bin; net and gross of the bin
follow from the sums. Chain totals: net_total = existing
`gex_total_1pct_usd`; gross_total = sum of gross(K) over all K.

Meaning: net(K) is the whole-expiry, whole-root gamma notional per 1% SPX move
that the configured convention attributes to strike K. gross(K) is the same
notional with the convention removed: how much OI-gamma is at K regardless of
who holds it. A bin with wide gross and thin net is "two-sided paper under the
convention"; the true sign there is unknown.

What they do NOT mean: measured dealer inventory; hedging pressure; price
levels that attract or repel; the sign of true aggregate gamma at a two-sided
bin; intraday 0DTE positioning (OI is prior-close; 0DTE opened today is
invisible and expires today); anything about SPY.

## 7. STRIKE-SELECTION RULE (deterministic)

Rule (class D hybrid, with binning): 
1. bin every strike with bin(K) = floor((K + 12.5)/25) * 25 (SPX strikes are
   on a 5-point grid, so no tie is possible; the floor form is deterministic
   for any input).
2. center = bin(spot). Window = the 31 bins center - 15*25 .. center + 15*25.
   Every window bin is drawn, including empty ones (an empty side is
   information).
3. Beyond-window bins with gross >= 2% of chain gross are listed as text in
   ascending strike order (strike, distance %, gross, net); never drawn on the
   axis, so one far outlier cannot compress the ladder.
4. Bar scale = 112 SVG units per max over window bins of max(call_side,
   |put_side|). Gross extents therefore always fit; the net bar is drawn on the
   same scale.
5. If window gross == 0 the ladder is omitted and only the beyond-window line
   is shown; if the whole `by_strike` block is absent or invalid the card
   renders exactly as it does today (no profile, no gross row).

Why: the live chain puts 80% of gross inside this window, at a 25-point
resolution that keeps all 5-point paper (40% of near gross) instead of
dropping it, at a row count that fits a phone; the fixed bin count keeps
layout stable across SPX levels; the outlier list keeps far structure honest
without distorting geometry. Rejected: A (distance %) = same window but row
count drifts with spot; B (top-N) loses contiguity, 51-64% coverage; C
(nearest-N) 17-40% coverage, never reaches 8000; E (25-multiple strikes only)
drops 40% of near gross.

Edge cases run on the live chain (evidence/selection_rule_edge_cases):
- one enormous far strike (7000 x5): window unchanged, in-window share 68%,
  outlier listed with gross 131B - honest and undistorted.
- no puts: ladder is all call-side; outlier list still works.
- very low total (/100): identical shape, values scale; bar scale is relative
  so the ladder still reads; the Gross row carries the small number.
- all exposure above spot: 16/31 bins nonzero, below-spot side empty; two
  outliers at +5.2%/+5.8% listed.
- all zero: window gross 0 -> ladder omitted; chain gross 0 also means the
  producer's dominant is `all_net_gamma_zero` so the whole card is already
  suppressed by PRD-309 Q6. The 2% threshold must be guarded against a zero
  denominator (0 >= 0 lists every bin) - a red test belongs here.
- tight near cluster only: 5/31 bins nonzero, 100% in window, no outliers.
- spot -6% (window re-centres): the old near-spot ridge becomes nine listed
  outliers; in-window share 34%. Acceptable and honest, but it shows the
  outlier line can grow; cap the listed outliers at 6 with "+N more".
- spot exactly on a bin boundary (7762.5): floor form picks 7775; deterministic.

What is omitted and how the UI says so: strikes outside the window below the
2% threshold (about 20% of gross today) are summarized only by the "n% within
window" figure on the Gross row. Bin resolution hides 5-point detail inside a
bin; the legend says "25-pt strike bins".

## 8. EXPIRATION / 0DTE DECISION

v0: one aggregate-all-expiry profile (identical to the producer's existing
aggregation), no expiration split, no 0DTE layer. The existing 0DTE share row
stays. Rationale: per-strike 0DTE gross in the post-close sample is 1.4B of
134B near gross (and degenerate after expiry); an intraday layer would need
the intraday sampling this session could not do, and a per-expiry per-strike
structure is new arithmetic and a much larger artifact. The all-expiry
aggregate is honest only with the existing caveat surfaced: AM-settled SPX and
PM-settled SPXW settlement timing is not modeled; expired same-day contracts
can remain in a post-close feed (F3). Deferred: 0DTE overlay, expiry facet,
excluding expired contracts after the close.

## 9. DATA CONTRACT

New top-level field, columnar (parallel arrays), so PRD-306 R12 stays green:
no forbidden raw-chain keys, no list-of-objects.

```
"by_strike": {
  "strike":            [200.0, 400.0, ..., 20000.0],   # ascending, unique
  "call_gex_1pct_usd": [0.0, ..., 38058745224.036],    # >= 0
  "put_gex_1pct_usd":  [0.0, ..., -32940752290.109]    # <= 0 (signed)
}
```

- one entry per strike in the producer's existing `strikes` set (every strike
  with at least one included contract; 809 today, ~30 KB at full precision).
  Emitting all strikes, not only nonzero ones, keeps the field the exact
  intermediate and lets tests reconcile: sum(call) + sum(put) ==
  `gex_total_1pct_usd`, argmax(call) == `call_wall.strike` (lowest-strike tie
  break), argmax |put| == `put_wall.strike`, argmax |call+put| ==
  `dominant_net_gamma.strike`. Float-sum order: the producer currently sums
  dict values in insertion order; the test should assert isclose, or the
  producer should compute the total from the sorted arrays so equality is
  exact (Codex question Q1).
- `provenance.derived` gains `"by_strike"` (test_r37 is exhaustive over
  top-level fields and must move).
- schema_version: stays 1, additive optional field. The consumer renders the
  profile iff the block is present and valid; otherwise the card is unchanged.
  Alternative: bump to 2 and gate on == 2. Because the artifact is run-local
  and producer + consumer deploy together from main there is no compatibility
  population either way; additive is the smaller cone and matches the
  planning recon's "changes are additive" rule. Helm decides (Codex Q9).
- Deterministic ordering: ascending strike; arrays are emitted from the sorted
  key list; `json.dumps(sort_keys=True)` already fixes key order.
- Size: ~30 KB (full precision) / ~19 KB (integer USD). The artifact is never
  committed or published, so size is a CI-runner concern only.
- Consumer validation (suppress the PROFILE only, not the card): dict; three
  lists of equal length >= 1; strikes finite, > 0, strictly ascending; calls
  finite >= 0; puts finite <= 0; bool-first rejection as everywhere.

## 10. CHANGE CONE (smallest exact)

- Producer `tools/gex_snapshot.py`: about 12 LOC in `_build_artifact` to emit
  the three arrays from the existing dicts and add the provenance entry. No
  new arithmetic.
- Consumer `cuttingboard/delivery/gex_card.py`: validation of `by_strike`,
  binning/window/outlier selection, ladder SVG builder, numeric-ladder
  `<details>`, Gross row, legend lines; `GexCard` gains an optional profile
  field. Estimated 130-170 LOC. All GEX arithmetic stays in this module
  (PRD-309 R20 keeps the renderer math-free).
- Renderer `dashboard_renderer.py`: NO change. The fragment is emitted as one
  string at `:3407`; SVG presentation attributes need no `_CSS` rule; the
  `<details>` idiom and `summary` styling are global already. Consequence:
  suppression stays byte-identical and BOTH goldens stay untouched. This is the
  cheapest possible cone and avoids the HIGH-RISK `*dashboard*.py` lane.
- Tests that must move: `test_r1_happy_path_full_schema_types` (new key),
  `test_r37_provenance_exhaustive_five_classes`; new producer tests:
  reconciliation invariants above, ascending/unique strikes, determinism
  unchanged, R12 still green with the columnar block, a red test that the
  block is the exact intermediate (a hand-built two-strike feed). New consumer
  tests: profile present/absent/invalid (card unchanged on invalid), bin
  arithmetic on a hand fixture, window centring incl. boundary spot, outlier
  listing incl. zero-denominator guard and the 6-cap, scale never clips, empty
  side rendered, forbidden-vocabulary list extended ("flip", "zero gamma",
  "long gamma", "short gamma", "support", "resistance", "magnet", "pin",
  "expected move", "target"), single-string fragment (R18 stripping still
  works), `<script` count unchanged. `test_gex_valid_card_rendered` fixture
  may gain the block. `test_gex_decision_outputs_unchanged` is unaffected if
  the fragment remains one `w()` call.
- Docs/authority actually required: a new PRD via the GOV-2 amended-authority
  path because PRD-306.md:75 ("No top_strikes; no full per-strike profile")
  is superseded in part, and PRD-309.md:214-216 cut the per-strike table from
  the card. `docs/SCHEMA_MAP.md` gex_snapshot rows and `docs/CALL_SITE_MAP.md`
  gex_card rows updated in the same PR. PRD-310 is untouched (its "no schema
  change" bound applied to that slice).

## 11. DEPENDENCIES

- new fetch: NO (same single GET; the arrays come from the same pass)
- new provider: NO
- new package: NO (stdlib only, both sides; no JS)

## 12. TRUTH BOUNDARIES

Exact labels allowed (proposed copy):
- column headers: "STRIKE", "put-side <", "> call-side", "NET $B"
- rows: "Gross <x>B", "<n>% within window"
- markers: "C", "P", "D" with legend "C / P / D = largest call-side, put-side,
  |net| strike" (the existing card rows keep their PRD-309 labels)
- spot: "SPX <spot>"
- legend line 1: "31 x 25-pt strike bins around SPX spot; all expirations;
  SPX+SPXW."
- legend line 2: "* net is signed under a configured positioning assumption
  (calls +1 / puts -1); positioning is not measured. gray = call-side +
  put-side gross, no sign assumption."
- outlier line: "beyond window: <strike> (<dist>) gross <x>B net <y>B" or
  "beyond window: none >= 2% of chain gross"
- disclosure: "strike bins by gross" with columns bin / dist / call-side /
  put-side / net
- tooltip: "<bin>: net <x>B (call-side <a>B, put-side <b>B)"
- provenance footer as today: "as of HH:MM ET . Cboe ~15m delayed source"

Claims forbidden anywhere in the fragment (extend the existing vocabulary
test): gamma flip, zero gamma, flip, long gamma, short gamma, dealer long /
dealer short, support, resistance, magnet, pin, pinning, expected move,
volatility suppression / expansion, acceleration, reversal, target, bullish,
bearish, "dealers are", "hedging pressure", "tracks spot", "at spot", max
pain, regime, and any SPY price. Also forbidden by design: drawing a line
where net changes sign (that is a gamma-flip claim by geometry), any
per-expiry claim, any relative "ago" freshness, any SPY axis.

Provenance classes kept distinct in copy: provider-observed (OI, spot,
timestamp), provider model output (gamma), Cuttingboard arithmetic (sums,
bins, gross), configured assumption (sign, multiplier, 1%), human
interpretation (none rendered).

## 13. PROVIDER-RIGHTS STATUS

UNCHANGED. Evidence: the accepted posture is "personal, non-redistributed,
context-only" (GEX_0_CBOE_PROVIDER_EVIDENCE_PACKET_2026-08-17.md:47,186,251);
the enforced prohibition is on persisting raw chain content and per-contract
rows (PRD-306 R12, `tests/test_gex_snapshot.py:564`), not on derived
per-strike figures, which the planning recon explicitly places inside the
artifact ("derived per-strike/aggregate GEX figures and provenance - never the
bulk raw chain", GEX_1_2_PLANNING_RECON_2026-08-20.md:220-224). The proposed
field is derived (gamma x OI x constants, not invertible to either factor),
columnar, and never committed or published; the board shows 31 bins. The
pre-existing, unadjudicated tension that the published board is
"display-to-others" is not changed by this slice; it was already accepted for
the GEX-2/3 card. No new terms review is triggered.

## 14. PROTOTYPE RESULT

Concepts (evidence/proto_abc_compare.html, evidence/proto_b_net_gross_ladder.html,
generator evidence/proto_generator.py; screenshots reviewed at 360 px frame):
- A: signed net ladder. Clean, 5-second read, but on the live chain 7700
  renders as +0.0 (nothing) and 8000 as a modest +6.6 with unexplained "C P"
  markers. It asserts "nothing at 7700", which the data does not support.
- B: net bar over gross extent (winner). 8000 becomes the obvious largest
  structure with a thin net; 7675/7700/7750 show as wide two-sided paper with
  small net; above spot the bars are nearly all net (one-sided call paper).
  The asymmetry in section 3 F4 is visible at a glance. Cost: net bars are
  scaled to the gross maximum, so they are about 40% shorter than in A;
  still legible (7800 net +15.1B is 45 units).
- C: horizontal columns (strike on x) plus ladder. 170 units tall, but at 31
  columns across 344 units each bar is ~10 px on a phone; per-bin reading and
  labels fail; gross and net columns compete. Rejected for phone density.
A call/put split (two bars per row) was not built: gross extent plus net
carries the same information with one fewer series and does not invite the
reader to read the call bar as "dealer long calls".

Palette: blue #3987e5 / red #e66767 diverging pair on the dashboard surface
#0d0d0d passes the validator (lightness band, normal-vision floor, contrast);
gray #4a4a4a is the neutral non-series extent (expected chroma-floor fail for
a neutral). Text stays in ink tokens, never series color.

## 15. CODEX HIGH PACKET

Frozen at `GEX_4_CODEX_HIGH_PACKET_2026-09-03.md` in this directory.

## 16. RECOMMENDATION

BUILD, as revised (net + gross ladder, 31 x 25-pt bins, outlier line, 0DTE as
a number, columnar additive field, zero renderer change).

Product test answers:
1. New question answerable: where is the paper relative to spot, is it
   one-sided or two-sided, and are the three anchors spikes or a ridge?
2. Immediately visible: spot position; side asymmetry; wide-gross bins; wide
   gross with thin net (two-sided under the convention).
3. Remaining ambiguity: true sign at two-sided bins; expiry mix inside a bin;
   5-point detail inside a bin; post-close expired 0DTE paper.
4. Most likely false reading: "blue above = resistance, red below = support"
   or "widest gray = strongest level".
5. Prevention: no level vocabulary anywhere; the legend names gross as
   "no sign assumption"; the footnote keeps "positioning is not measured";
   the C/P/D legend is literal; no sign-change line is drawn.
6. Worth the complexity: yes - producer +12 LOC, consumer ~150 LOC, no
   renderer or CSS change, no golden churn, no dependency.
7. Would Dustin keep looking after novelty: yes, conditionally. A strike
   ladder around spot is the one GEX artifact discretionary index traders
   consult daily; the current five-number card is not. The VISION line "if a
   feature does not change a decision it should not exist" is a pre-existing
   tension for all GEX context and is owner-ruled by doctrine 4.1 (context
   for human display). If Helm does not accept that ruling for this slice,
   the answer flips to DO NOT BUILD.

Smallest next-step authority plan:
1. Helm accepts or amends the product direction in this report (owner hold:
   design-direction ruling).
2. DESIGN session: draft PRD-3xx "GEX-4 strike ladder" via
   `prd-authoring-verified`; class MATERIAL under GOV-2 (schema field + new
   board surface; PRD-306 OUT-OF-SCOPE superseded in part); FILES =
   tools/gex_snapshot.py, cuttingboard/delivery/gex_card.py,
   tests/test_gex_snapshot.py, tests/test_gex_card.py, docs/SCHEMA_MAP.md,
   docs/CALL_SITE_MAP.md, registry/index. Codex HIGH falsification pass on
   the packet is Event 1; fresh-context review Event 2; Gate A.
3. IMPLEMENT session on Gate A; validate on a live intraday snapshot (the
   validate-then-fix rule), including one run at 09:40 PT to check the
   intraday 0DTE share and one at 13:10 PT for F3.

## 17. ANOMALIES / FUTURE (recorded, not acted on)

- A1 (finding, current card): the "Call wall" / "Put wall" argmax labels are
  captured by box-spread strikes (8000 on both samples). Candidate follow-up:
  relabel to "largest call-side strike" / "largest put-side strike" or gate
  the wall rows on |net|/gross. Owner call; outside this slice.
- A2 (finding, producer): PRD-306.md:274-275 expects a zero 0DTE numerator
  outside market hours; on expiry days the post-close feed still carries the
  expired contracts (504 rows, 2.5%, 18:42 ET; 522 rows, 7.6%, 16:41 ET on
  2026-08-20) with degenerate model gammas. Whether the 13:10 PT hourly run
  sees them is UNKNOWN. Candidate: exclude contracts whose expiry date ==
  observation date when feed time is after 16:00 ET (needs its own PRD; it
  changes the 0DTE semantics).
- A3 (stale map): `docs/CALL_SITE_MAP.md:68` says the renderer emits
  `market_state_panel.render_fragment`; `rg market_state_panel
  cuttingboard/delivery/dashboard_renderer.py` returns nothing. The panel is
  test-only today. Fix the map row in the next PR that touches it.
- A4 (stale snapshot): `ui/dashboard.html` on main predates PRD-318+ and has
  no GEX block; not a suppression signal. Regenerate only via the pipeline.
- FUTURE (not v0): 0DTE per-strike overlay from an intraday sample; expiry
  facet (monthly vs weekly); excluding expired same-day contracts post-close;
  SPY GEX as its own underlying (never a mapped SPX ladder); an above-the-fold
  one-line "gross within +/-2%" tape figure once the ladder proves useful.
