# GEX-4 PRODUCT RECON - SPX strike ladder (current candidate design, post-Event-1)

Date: 2026-09-03. Basis: Helm charge "GEX-4 PRODUCT RECON / STRUCTURAL
PROFILE", then Helm charge "GEX-4 MATERIAL CORRECTION AFTER EVENT 1". Main at
recon: a76e7a4. Recon head: e259964 (Event-1 review input, frozen). This file
is the ONE consolidated correction after Event 1 and is now the current
candidate design. It carries no implementation authority: no PRD, no Gate A.

Non-authoritative: every product ruling below is Helm-held until Dustin
accepts it. Provider-rights tension remains an explicit Helm hold before Gate
A / public surfacing and is not reopened here.

--------------------------------------------------------------------------

## 0. CORRECTION CYCLE (Event 1 -> this head)

Event-1 record: `GEX_4_EVENT_1_CODEX_REVIEW_2026-09-03.md` (Codex HIGH, fresh
context, reviewed head e259964; APPROVE WITH REQUIRED EDITS, R1-R8 required,
none blocking, 5 recommended). Helm adjudication: R1-R5, R7, R8 ACCEPT; R6
ACCEPT WITH NARROW IMPLEMENTATION BOUNDARY; no waiver.

| finding | where resolved in this document |
|---|---|
| R1 strategy-identity overclaim | 3 (Observation F1 rewritten), 17 A1; every box / financing / footprint / paired-position phrase removed from the current design |
| R2 model-bounded net / magnitude language | 6 (quantities), 12 (vocabulary); "cancellation", "offset", "two-sided position", unqualified Net/Gross removed |
| R3 directional color and loaded labels | 5 (one non-directional net treatment), 12 (labels), 14 (corrected prototype) |
| R4 exact bin contract, raw-strike anchors, 7750/8000 defect | 7 (integer mills, half-open interval), 12 (C/P/D legend), 3 (widest bin stated correctly) |
| R5 window honesty | 7 (in/out percentages, N of M shown, recentering statement) |
| R6 profile-only settlement validity | 8 (fail-closed rule, typed carrier shape, core card untouched) |
| R7 expiry / root disclosure | 12 (visible adjacent copy) |
| R8 canonical carrier, exact reconciliation, compatibility | 9 (carrier: positive call and put modeled magnitudes, model net = call - put, pinned fsum expression), 10 (tests), schema v1 kept |
| accessibility recommendation | 5 (full-bin textual table, no hover reliance) |
| live-validation recommendation | 16 (recorded; not all pre-build blockers) |
| strike-mills recommendation | 7 (adopted) |
| keep all admitted strikes | 9 (adopted) |
| window recentering statement | 7, 12 (adopted) |

Event-2 attempt 1 (`GEX_4_EVENT_2_CONFIRMATION_ATTEMPT_1_2026-09-03.md`,
head d852682): NOT CONFIRMED on two confirmation defects; Helm authorized ONE
bounded repair limited to them: (A) exact visible vocabulary (CALL MODELED
MAGNITUDE, PUT MODELED MAGNITUDE, MODEL NET*, CALL+PUT MODELED MAGNITUDE;
LARGEST CALL-CONTRACT MAGNITUDE STRIKE, LARGEST PUT-CONTRACT MAGNITUDE STRIKE,
LARGEST RAW-STRIKE |MODEL NET|), applied throughout this document, section 12
and the current prototype; (B) the carrier stores POSITIVE call and put
modeled magnitudes (`call_modeled_magnitude_1pct_usd`,
`put_modeled_magnitude_1pct_usd`), model net = call - put, one pinned fsum
expression (section 9). R1, R4, R5, R6, R7, schema v1, window, outlier rule,
accessibility and suppression architecture are unchanged in substance.

Historical artifacts: `GEX_4_CODEX_HIGH_PACKET_2026-09-03.md` is the frozen
Event-1 review input and is NOT updated (it still contains the superseded
red/blue design, the superseded labels, the "box-spread" wording in section 6,
and the 7750 "widest bin" defect in Q8). `evidence/proto_abc_compare.html`,
`evidence/proto_b_net_gross_ladder.html` and `evidence/proto_generator.py` are
HISTORICAL / SUPERSEDED BY EVENT-1 CORRECTION (see `evidence/README.md`); the
corrected prototype is `evidence/proto_corrected_ladder.html` (generator
`evidence/proto_generator_corrected.py`). `evidence/live_chain_analysis_*.txt`
and `evidence/bins_topn_sidedness_*.txt` are raw analysis printouts whose
column headers use the pre-correction words "call", "put", "net", "abs",
"gross"; they are arithmetic only and are read under section 6 definitions.

--------------------------------------------------------------------------

Evidence basis: one live keyless GET of the existing endpoint at 2026-09-03
22:42:44 UTC (18:42 ET, post-close), fetched through the producer's own
`_http_get`, written to the scratchpad only; `logs/gex_snapshot.json` untouched;
the raw payload (12.7 MB) was NOT committed. Second sample: the on-disk
artifact from 2026-08-20 20:41 UTC (also post-close). LIMITATION: no intraday
sample was obtainable; every same-day-expiry statement is from post-close feeds.

## 1. CURRENT CAPABILITY

CONFIRMED by reading a76e7a4:
- Producer `tools/gex_snapshot.py` (PRD-306/307): one GET, per-contract
  admissibility, `_gex()` per contract, per-strike call/put/net dicts, five
  derived outputs, atomic write of `logs/gex_snapshot.json`.
- Consumer `cuttingboard/delivery/gex_card.py` (PRD-309): identity, freshness
  (24 h on `fetched_at_utc`) and coherence gate; `GexCard`; HTML fragment;
  suppresses to "" so the dashboard stays byte-identical to the golden.
- Cadence (PRD-310): `.github/workflows/hourly_alert.yml:203-207`, cron
  `10 14-21 * * 1-5` (07:10-13:10 PT) plus the 06:30/06:45 PT doubled slots;
  artifact run-local only, never restored/staged/published; board goes to the
  `publish` branch; the daily `cuttingboard.yml` render never runs the
  producer, so the 06:00 PT publish drops the card until the next hourly run.
- Placement: first child of `<details id="details-history">` (renderer
  `:3395-3407`). Above the fold GEX is one tape row "GEX . CONTEXT ONLY".
- `market_state_panel.py` uses only `GexCard.net_usd` and is not imported by
  the renderer (anomaly A3).

Answers well: sign and size of the whole-chain model net; three single
strikes with distance from spot; 0DTE share; as-of time. Does not answer:
where the modeled magnitude sits relative to spot across strikes; whether it
is a spike or a ridge; whether the three anchors are lone or clustered;
whether a large anchor strike is one-sided or near-balanced. On the
2026-09-03 chain the card reads: Net +80.4B, Dominant 7800 (+0.67%), Call wall
8000 (+3.26%), Put wall 8000 (+3.26%), 0DTE 2.5%. The identical 8000 anchors
are unexplained by the card.

## 2. DISCARDED INFORMATION

At `tools/gex_snapshot.py:315-323` the producer holds, then discards:

| intermediate | shape | survives? |
|---|---|---|
| `call_by_strike[K]` = sum over included calls at K of gamma*OI*100*spot^2*0.01 (>= 0) | dict, 809 keys live | argmax only |
| `put_by_strike[K]` = -1 * same over puts (<= 0) | dict, 809 keys | argmax of magnitude only |
| `net_by_strike[K]` = call + put | dict | argmax of magnitude, and the total |

Nothing per-expiry per-strike is computed. Helm hypothesis CONFIRMED exactly.

## 3. REAL-DATA FINDINGS (live chain, 2026-09-03 18:42 ET, spot 7747.71)

Quantities below use section 6 definitions: CALL MODELED MAGNITUDE = call modeled
magnitude, PUT MODELED MAGNITUDE = put modeled magnitude (shown as a positive number), CALL+PUT MODELED MAGNITUDE =
call+put modeled magnitude, MODEL NET* = call modeled magnitude - put modeled magnitude under the
configured convention.

| quantity | value |
|---|---|
| contracts admitted | 28,492 / 28,492 |
| distinct strikes | 809 (200..20000); 669 with nonzero magnitude |
| chain MODEL NET* | +80.4B |
| chain CALL+PUT MODELED MAGNITUDE | 595.5B |
| chain |model net| / mag | 0.135 |
| CALL+PUT MODELED MAGNITUDE within +/-1% / 2% / 3% / 5% / 10% of spot | 33% / 48% / 56% / 80% / 94% |
| strike pitch within +/-3% | 5 points everywhere (93 strikes) |
| CALL+PUT MODELED MAGNITUDE on 25-multiple strikes within +/-3% | 60%; the other 40% (134B) is spread over 74 five-point strikes, 1-5B each, almost none same-day |
| largest expiry by CALL+PUT MODELED MAGNITUDE | 2026-09-18 monthly, 35.6% of chain CALL+PUT MODELED MAGNITUDE |
| same-day (2026-09-03) contracts still in the post-close feed | 504, 14.8B CALL+PUT MODELED MAGNITUDE, share 2.5% |

Observation F1 (R1-corrected). Near-balanced call and put modeled magnitude
at the same strike is the dominant feature of this chain, and it sits on
round strikes:

| strike | dist | CALL MODELED MAGNITUDE | PUT MODELED MAGNITUDE | MODEL NET* | CALL+PUT MODELED MAGNITUDE | |model net| / magnitude |
|---|---|---|---|---|---|---|
| 8000 | +3.26% | 38.06B | 32.94B | +5.12B | 71.0B | 0.07 |
| 7750 | +0.03% | 19.31B | 13.56B | +5.75B | 32.9B | 0.17 |
| 7700 | -0.62% | 13.32B | 14.23B | -0.92B | 27.6B | 0.03 |
| 7000 | -9.65% | 12.37B | 13.87B | -1.50B | 26.2B | 0.06 |
| 7600 | -1.91% | 8.74B | 10.68B | -1.93B | 19.4B | 0.10 |

What the provider rows establish at 8000: SPX 2026-09-18 8000 call OI
273,400 and put OI 263,216, each with provider-model gamma 0.0007, and
similarly near-balanced call/put OI at 8000 across Oct-2026, Dec-2026 and
Dec-2027 expiries. The strongest justified description is: a large,
near-balanced call-contract and put-contract modeled magnitude at the same
strike across several expirations. Aggregate OI carries no trade pairing,
opening/closing direction, account identity, participant side, or any other
strike leg; identical call/put gamma at one strike and expiry is provider
model behavior. The structure is consistent with multiple strategies; none is
identified, and the design does not depend on knowing one.

Consequences for the display:
- The existing 8000 anchors are argmaxes of call magnitude and put magnitude
  that happen to coincide because both magnitudes are large there. The card
  cannot show that they are near-balanced.
- A model-net-only profile would render the 7700 bin (CALL+PUT MODELED MAGNITUDE 39.5B, MODEL NET*
  +0.03B) as nothing, which asserts more than the data supports.
- A magnitude-only profile would rank 8000 far above every other strike
  without showing that its model net is small.
- Whether near-balanced call and put magnitude at a strike corresponds to
  flat true gamma, or to two large positions that the uniform convention
  happens to bring near zero, is NOT determinable from OI. The display states
  the arithmetic and stops.

Observation F2. Top-N by magnitude is not spatially useful alone: N=16 covers
51% of CALL+PUT MODELED MAGNITUDE spanning 7000..8000; N=32 reaches 6000 and only 64%. Nearest-N is
worse (N=32 = +/-1%, 34%).

Observation F3 (R6 input). The post-close feed still carried 504 contracts
expiring 2026-09-03 (PM-settled SPXW, expired at feed time) with degenerate
model gammas (7750 call 0.0331 vs put 0.11). The Aug-20 artifact (16:41 ET)
shows the same shape at 7.6%. PRD-306.md:274-275 expects "outside market
hours ... numerator legitimately 0"; on an expiry day after the close that is
FALSIFIED by observation. Whether the 13:10 PT (16:10 ET) hourly run sees
those rows is UNKNOWN (not sampled).

Observation F4. Within +/-5%, 52% of CALL+PUT MODELED MAGNITUDE is above spot and CALL MODELED MAGNITUDE is 58% of
CALL+PUT MODELED MAGNITUDE. Above spot |model net| / magnitude is 0.75-0.9 (mostly call magnitude); at and
below spot it is 0.03-0.26 (near-balanced). That asymmetry is invisible today.

Bin fact for R4: in the 31-bin table (section 14 / historical packet) the
widest bin by CALL+PUT MODELED MAGNITUDE is 8000 (72.57B); the widest bin at spot is 7750 (47.53B).
The historical packet's Q8 wording ("widest bin (7750)") was wrong and is
left uncorrected there as the frozen Event-1 input.

## 4. PRODUCT VERDICT

Preserving the discarded per-strike structure is the highest-leverage move.
The candidate is a bounded SPX strike ladder around the spot bin, one row per
25-point bin, showing the call and put modeled magnitudes as a neutral
extent with the configured-convention model net overlaid in one
non-directional treatment, the three existing raw-strike anchors marked, an
explicit in-window / outside-window magnitude disclosure, a bounded outside-bin
list with counts, all expirations combined, 0DTE kept as a number, no SPY
coordinate mapping, no permission or trade coupling.

## 5. RECOMMENDED V0 (corrected)

Visualization: vertical strike ladder, highest strike on top (same
orientation as the D3 level ladder), 31 rows, one per 25-point bin. Inline
attribute-styled SVG inside the existing `#gex-context` fragment. No JS (the
renderer test pins exactly one `<script>`).

Row anatomy, left to right: bin label (100-multiples in ink, others muted) |
raw-strike anchor marker column (C, P, D) | zero axis; PUT MODELED MAGNITUDE extent to the
left and CALL MODELED MAGNITUDE extent to the right in one neutral gray; MODEL NET* bar
overlaid in ONE non-directional color (dashboard ink #e0e0e0), drawn to the
left of zero when negative and to the right when positive | MODEL NET* value
with explicit sign. Spot: dashed line at its exact position, label "SPX CASH
SPOT <value>". Column headings "PUT MODELED MAGNITUDE <" and "> CALL MODELED MAGNITUDE" in neutral muted
text. No red, no blue, no status colors anywhere in the block.

Default-visible (inside the existing details-history disclosure as today):
- existing rows, semantics unchanged, labels relabeled per section 12
- new row: "CALL+PUT MODELED MAGNITUDE <x>B"
- window line: "WINDOW SHOWS 80% OF CHAIN CALL+PUT MODELED MAGNITUDE . 20% OUTSIDE"
- the ladder
- outside-bins line with counts (section 7)
- adjacent qualifier lines (section 12)
- provenance footer as today

Accessible textual content (Event-1 recommendation, adopted): a `<details>`
"ALL 31 BINS + OUTSIDE BINS" plain-HTML table with one row per window bin
(bin, interval, CALL MODELED MAGNITUDE, PUT MODELED MAGNITUDE, MODEL NET*) plus one row per listed
outside bin. It is the phone-inspectable form; SVG `<title>` remains only as
a desktop convenience and is not relied on. Each SVG row group also carries an
`aria-label` with the same four values.

Mobile: viewBox 358 x 402, width 100%, max-width 520px (D4 strategy). At
360px device width the row pitch is ~11 px and labels ~9.6 px, above the 9 px
floor measured for PRD-330. Nothing measures the client.

Under-5-seconds read: where spot sits; which side carries more magnitude;
where the wide neutral extents are; whether a wide extent has a thin model-net
bar (near-balanced call and put magnitude under the convention).

## 6. QUANTITATIVE SEMANTICS (R2)

Per contract c (existing, unchanged): gex(c) = s(c) * gamma_c * OI_c * 100 *
spot^2 * 0.01, s = +1 call, -1 put. gamma_c: provider model output. OI_c,
spot, timestamp: provider-observed. 100, 0.01: configured. s: configured
assumption (INFERRED class).

Per strike K (existing intermediates, serialized by the canonical carrier):
- CALL MODELED MAGNITUDE(K) = sum of gex(c) over included calls at K, >= 0
- PUT MODELED MAGNITUDE(K)  = |sum of gex(c) over included puts at K|, >= 0 (the carrier
  stores this positive magnitude; the producer's signed put contribution is
  -PUT MODELED MAGNITUDE(K))
- MODEL NET*(K) = CALL MODELED MAGNITUDE(K) - PUT MODELED MAGNITUDE(K) (equal to the producer's
  net_by_strike[K] under the existing call-positive / put-negative arithmetic)
- CALL+PUT MODELED MAGNITUDE(K) = CALL MODELED MAGNITUDE(K) + PUT MODELED MAGNITUDE(K)

Per bin b (consumer-derived, section 7): each of CALL MODELED MAGNITUDE and PUT MODELED MAGNITUDE summed
over K in the bin; MODEL NET* and CALL+PUT MODELED MAGNITUDE of the bin follow from the sums. Chain
totals: MODEL NET* total = existing `gex_total_1pct_usd`; chain CALL+PUT MODELED MAGNITUDE = sum over
K of CALL MODELED MAGNITUDE + PUT MODELED MAGNITUDE.

Meaning: CALL MODELED MAGNITUDE and PUT MODELED MAGNITUDE are the provider-model gamma notionals per 1%
SPX move carried by call contracts and by put contracts at a strike, across
all expirations and both roots. MODEL NET* applies the configured call-plus /
put-minus convention to them. CALL+PUT MODELED MAGNITUDE is the same arithmetic with
the sign assignment removed.

A thin MODEL NET* bar over a wide CALL+PUT MODELED MAGNITUDE extent means only: the aggregated call
and put modeled magnitudes inside this bin are near-balanced under the
configured arithmetic. It does not claim economic offset, participant
cancellation, dealer exposure, or a true-gamma sign.

Not meant, ever: measured dealer or participant inventory; hedging pressure;
price attraction or repulsion; the true sign of gamma at a near-balanced bin;
intraday same-day positioning (OI is prior-close); anything about SPY.

## 7. STRIKE-SELECTION RULE (R4, R5)

Bin contract (integer strike mills, from the OCC strike digits):
- strike_mills = the admitted OCC 8-digit strike field as an int (K * 1000).
- bin_mills(K) = ((strike_mills + 12500) // 25000) * 25000
- Equivalent interval: [b - 12.5, b + 12.5); an exact upper half-boundary
  (K = b + 12.5) belongs to the HIGHER bin. No float arithmetic in binning.
  The producer parser admits three-decimal strikes, so ties are possible in
  principle and are resolved by this rule.
- Every admitted raw strike is preserved in the carrier (section 9); binning
  is consumer-side presentation arithmetic and is lossy by design: within-bin
  location is discarded, and a bin's MODEL NET* can near-balance from
  opposing contributions at DIFFERENT strikes (raw 7700 is -0.92B; the 7700
  bin is +0.03B). Copy states this (section 12).

Window: center = bin(spot_mills) where spot_mills = round(spot * 1000);
window = the 31 bins center - 15*25 .. center + 15*25 in strike units. Every
window bin is drawn, including empty ones. The window recenters in 25-point
steps as SPX crosses a half-bin boundary; copy states this so edge bins
appearing or disappearing between hourly runs is not read as a structural
change.

Coverage disclosure (both directions, with the denominator named):
"WINDOW SHOWS <in>% OF CHAIN CALL+PUT MODELED MAGNITUDE . <out>% OUTSIDE", in + out
= 100 (rounded consistently; if rounding breaks the sum, show one decimal).

Outside bins: every bin outside the window with CALL+PUT MODELED MAGNITUDE >= 2% of chain CALL+PUT MODELED MAGNITUDE
qualifies; the list is ascending by strike; at most 6 rows are shown; when
capped the line reads "<N> OF <M> OUTSIDE BINS >= 2% OF CHAIN CALL+PUT MODELED MAGNITUDE SHOWN . <K>
MORE". When none qualify: "OUTSIDE BINS >= 2% OF CHAIN CALL+PUT MODELED MAGNITUDE: NONE". Each row:
bin, distance %, CALL+PUT MODELED MAGNITUDE, MODEL NET*. The full accessible table (section 5) lists
ALL qualifying outside bins, uncapped. Zero-denominator guard: when chain CALL+PUT MODELED MAGNITUDE
== 0 no bin qualifies (a red test covers 0 >= 0).

Scale: bar scale = 112 SVG units per max over window bins of max(CALL MODELED MAGNITUDE,
PUT MODELED MAGNITUDE); extents always fit; the MODEL NET* bar uses the same scale.

Raw-strike anchors (R4): C, P, D are the existing producer anchors
(call_wall.strike, put_wall.strike, dominant_net_gamma.strike). They are
placed in their containing bin and do NOT identify the bin-level maximum;
the legend and the accessible table row say so and print the raw strike.

Suppression: if window CALL+PUT MODELED MAGNITUDE == 0 the ladder is omitted and only the coverage
and outside lines are shown; if the carrier is absent, unavailable, or
malformed the card renders exactly as today (section 9).

Why this rule: 80% of chain CALL+PUT MODELED MAGNITUDE is inside the window on the live chain; 25-pt
resolution keeps all 5-point rows (40% of near CALL+PUT MODELED MAGNITUDE) instead of dropping them;
the fixed bin count keeps layout stable; the outside list with counts keeps
far structure honest without distorting geometry. Rejected: distance-%
window (row count drifts with spot), top-N (51-64% coverage, no contiguity),
nearest-N (17-40%, never reaches 8000), 25-multiple strikes only (drops 40%
of near CALL+PUT MODELED MAGNITUDE).

Edge cases run on the live chain (`evidence/selection_rule_edge_cases_*`):
far outlier x5 (window unchanged, in-window 68%, outlier listed at 131B); no
puts; /100; all magnitude above spot (16/31 bins nonzero, two outside bins
listed); all zero (ladder omitted; chain CALL+PUT MODELED MAGNITUDE 0 also means dominant is
`all_net_gamma_zero` so PRD-309 Q6 already suppresses the card); tight near
cluster (5/31 bins, 100% in window); spot -6% (nine qualifying outside bins,
in-window 34%: the line reads "6 OF 9 ... 3 MORE" and the table lists all
nine); spot on a bin boundary (higher bin, deterministic).

## 8. EXPIRATION / SAME-DAY VALIDITY (R6, R7)

v0 aggregation: one all-expiry, both-root profile, identical to the
producer's existing aggregation. No expiry split, no 0DTE layer; the existing
0DTE share row stays. Visible copy states: "ALL EXPIRATIONS COMBINED, EXPIRY
MIX HIDDEN. SPX+SPXW COMBINED, AM/PM SETTLEMENT NOT MODELED."

Profile-only settlement validity (Helm R6 boundary; the existing core card,
total, anchors and 0DTE semantics are NOT changed by GEX-4):

The producer already has root, expiry, and the provider observation date
(feed timestamp in America/New_York, `.date()`) before aggregation. For the
profile carrier, evaluated per observation, in this order:
1. If any admitted row has root SPX and expiry == observation date, the
   profile is UNAVAILABLE for that observation; reason token
   `same_day_spx_rows_present`. (Deliberately conservative: AM settlement
   timing is not modeled, so same-day AM-settled rows cannot be established as
   unsettled at any time of day.)
2. Else, if the provider observation time is >= 16:00:00 America/New_York
   and any admitted row has root SPXW and expiry == observation date, the
   profile is UNAVAILABLE; reason token `post_close_same_day_spxw_rows_present`.
3. Otherwise the profile carrier is emitted with reason null.

The gate is fail-closed (unavailable when the condition cannot be evaluated is
impossible by construction: root, expiry and observation time are already
required for admissibility and for `zero_dte`). No settlement precision is
claimed beyond "same-day rows present" and "at or after 16:00 ET". The
observed 2026-09-03 18:42 ET feed and the 2026-08-20 16:41 ET artifact both
fall under rule 2 and would carry no profile; a monthly-expiration day falls
under rule 1 all day.

Deferred: 0DTE overlay (needs intraday sampling), expiry facet, any producer
change to the core 0DTE numerator (its own PRD).

## 9. DATA CONTRACT (R8, schema)

Canonical carrier (producer-internal, always built): the sorted union of
admitted strikes, ascending by strike_mills, with CALL MODELED MAGNITUDE and
PUT MODELED MAGNITUDE (both >= 0; the put magnitude is the absolute value of
the producer's existing signed put contribution) for every strike, absent
sides filled with 0.0, all admitted strikes kept including zero-magnitude rows
(809 on the live chain). The core `gex_total_1pct_usd` is computed from this
carrier by ONE pinned expression, in ascending raw-strike order:

```
gex_total_1pct_usd = math.fsum(
    v for c, p in zip(call_modeled_magnitude, put_modeled_magnitude)
      for v in (c, -p)
)
```
i.e. the flattened operand sequence c(K1), -p(K1), c(K2), -p(K2), ... . The
producer calculation, the serialized-carrier validation, and the post-JSON
round-trip validation use this same operand order and the same `math.fsum`
semantics (exactly rounded; the current dict-insertion-order `sum()` is
replaced by it).
call_wall / put_wall / dominant_net_gamma are selected from the same carrier
with the existing lowest-strike tie rule (values unchanged; the per-strike
floats are the same objects).

Serialized field, additive, schema_version stays 1:

```
"by_strike": {
  "reason": null,                                   # or an unavailable token (section 8)
  "strike":                            [200.0, ..., 20000.0],           # float, strictly ascending, = strike_mills / 1000
  "call_modeled_magnitude_1pct_usd":   [0.0, ..., 38058745224.036],     # float >= 0
  "put_modeled_magnitude_1pct_usd":    [0.0, ..., 32940752290.109]      # float >= 0 (positive magnitude)
}
```
Field names are binding: the positive put field is NOT named
`put_gex_1pct_usd`; no signed-negative put value is serialized in the carrier.
Model net per strike is derived, never stored:
`model_net(K) = call_modeled_magnitude(K) - put_modeled_magnitude(K)`.
`strike` is emitted as the producer's own `int(digits) / 1000` float (identical
expression to the anchors' strikes); the consumer derives
`strike_mills = int(round(strike * 1000))` for binning and rejects the carrier
if `strike_mills / 1000 != strike`.
When unavailable: `"by_strike": {"reason": "<token>"}` with no arrays
(typed-unavailable, same construction style as the wall objects). Columnar,
so PRD-306 R12 stays green (no raw-chain keys, no list of objects).
`provenance.derived` gains `"by_strike"`. Ordering: ascending strike_mills;
`json.dumps(sort_keys=True)` fixes key order. Size ~35 KB, run-local only.

Exact reconciliation invariants (consumer and tests, after JSON round trip;
Python float repr round-trips exactly):
- `math.fsum(v for c, p in zip(call, put) for v in (c, -p)) ==
  gex_total_1pct_usd` (exact equality; the pinned expression above)
- CALL anchor: argmax(call_modeled_magnitude) with lowest-strike tie ==
  call_wall.strike when call_wall is available; max == 0.0 when
  call_wall.reason == no_nonzero_call_gex; call_wall.gex_1pct_usd == call[i]
- PUT anchor: argmax(put_modeled_magnitude) likewise against put_wall;
  put_wall.gex_1pct_usd == -put[i]
- DOMINANT anchor: argmax(abs(call[i] - put[i])) likewise against
  dominant_net_gamma; dominant_net_gamma.gex_1pct_usd == call[i] - put[i]
- strike strictly ascending floats > 0; strike_mills round trip exact
- lengths equal and >= 1; every value finite, non-bool; call >= 0; put >= 0

Compatibility (schema_version stays 1 unless correction work proves a wire
failure; none found):
- carrier ABSENT (old producer): existing card renders, profile absent
- carrier present with a non-null reason and no arrays: profile absent,
  card unchanged
- carrier MALFORMED without contradicting the core (bad types, lengths,
  ordering, reason/arrays mismatch): profile suppressed, card unchanged
- carrier present and domain-valid but contradicting the core total or any
  anchor: WHOLE CARD suppressed (artifact internally incoherent)
- new producer -> old consumer: the extra key is ignored (current consumer
  reads only its required keys)
`docs/SCHEMA_MAP.md` gex_snapshot section must define `by_strike` as an
optional v1 extension for consumers, always emitted by the new producer
(available or typed-unavailable).

## 10. CHANGE CONE (smallest exact)

- Producer `tools/gex_snapshot.py`: build the canonical sorted carrier from
  the existing dicts (put side negated to a positive magnitude); compute the
  total with the pinned flattened `math.fsum` expression over it; select the
  three anchors from it (same tie rule; DOMINANT from call - put); evaluate the profile validity gate;
  emit `by_strike`; add the provenance entry. About 35-45 LOC. Core
  semantics unchanged (values identical except possible last-ulp differences
  in the total from exact summation).
- Consumer `cuttingboard/delivery/gex_card.py`: carrier validation and
  reconciliation; mills binning; window and outside selection; ladder SVG
  (single neutral net color); accessible full table; coverage line; label
  relabel of the core rows (text only); qualifier lines. About 160-200 LOC.
  All GEX arithmetic stays here (PRD-309 R20).
- Renderer / CSS: NO change; the fragment is one string at `:3407`; SVG uses
  presentation attributes; `<details>` idiom is global. Suppression stays
  byte-identical; both goldens untouched.
- Tests that move: producer R1 schema (new key), R37 provenance, R13
  determinism (regenerate expected bytes if the fsum total differs in the
  last ulp), R2 hand-computed total (exact against fsum); new producer tests:
  carrier is the exact intermediate (hand-built feed; put magnitude equals
  the negated signed put sum), all admitted strikes kept, strictly ascending,
  exact reconciliation after round trip with the pinned fsum expression, R12
  still green, validity gate rules 1/2/3 each with a red mutation, typed
  unavailable shape. New consumer tests: absent / unavailable / malformed /
  contradicting carriers (profile-only vs whole-card suppression), mills bin
  boundaries incl. an exact half boundary and a three-decimal strike, window
  centering incl. boundary spot, coverage arithmetic sums to 100, outside
  list cap with counts and zero-denominator guard, scale never clips, empty
  side rendered, accessible table complete (31 + outside), no red/blue or
  status color in the fragment, forbidden vocabulary extended, fragment still
  one string (R18), `<script` count unchanged, relabeled core rows.
- Docs/authority actually required: a new PRD via the GOV-2 amended-authority
  path (PRD-306.md:75 "no full per-strike profile" and PRD-309.md:214-216
  per-strike-table cut superseded in part); `docs/SCHEMA_MAP.md` gex_snapshot
  rows; `docs/CALL_SITE_MAP.md` gex_card rows. PRD-310 untouched.

## 11. DEPENDENCIES: new fetch NO; new provider NO; new package NO.

## 12. TRUTH BOUNDARIES - final visible vocabulary (R2, R3, R4, R5, R7)

Core rows (semantics unchanged, labels relabeled, text-only):
- "MODEL NET*" (was Net)
- "LARGEST RAW-STRIKE |MODEL NET|" (was Dominant)
- "LARGEST CALL-CONTRACT MAGNITUDE STRIKE" (was Call wall)
- "LARGEST PUT-CONTRACT MAGNITUDE STRIKE" (was Put wall)
- "0DTE" (unchanged)

Profile block:
- new row: "CALL+PUT MODELED MAGNITUDE <x>B"
- coverage: "WINDOW SHOWS <in>% OF CHAIN CALL+PUT MODELED MAGNITUDE . <out>% OUTSIDE"
- ladder headers: "STRIKE" | "PUT MODELED MAGNITUDE <" | "> CALL MODELED
  MAGNITUDE" | "MODEL NET* $B"
- spot label: "SPX CASH SPOT <value>"
- markers: "C", "P", "D"
- marker legend: "C / P / D = RAW-STRIKE ANCHORS (LARGEST CALL-CONTRACT
  MAGNITUDE STRIKE, LARGEST PUT-CONTRACT MAGNITUDE STRIKE, LARGEST RAW-STRIKE
  |MODEL NET|) SHOWN IN THEIR 25-PT BIN; NOT THE BIN MAXIMUM."
- bin legend: "31 x 25-PT BINS [B-12.5, B+12.5) AROUND THE SPX CASH SPOT BIN;
  RECENTERS IN 25-PT STEPS. BIN MODEL NET CAN NEAR-BALANCE ACROSS DIFFERENT
  STRIKES."
- expiry/root: "ALL EXPIRATIONS COMBINED, EXPIRY MIX HIDDEN. SPX+SPXW
  COMBINED, AM/PM SETTLEMENT NOT MODELED."
- adjacent sign qualifier: "* MODEL NET = CALL MODELED MAGNITUDE - PUT MODELED
  MAGNITUDE. CONFIGURED CALL-PLUS / PUT-MINUS CONVENTION; PARTICIPANT AND
  DEALER POSITIONING ARE NOT MEASURED. CALL+PUT MODELED MAGNITUDE = CALL
  MODELED MAGNITUDE + PUT MODELED MAGNITUDE, NO SIGN ASSIGNMENT."
- outside line: "OUTSIDE BINS >= 2% OF CHAIN CALL+PUT MODELED MAGNITUDE: <bin> (<dist>) CALL+PUT MODELED MAGNITUDE <x>B NET
  <y>B" / "<N> OF <M> OUTSIDE BINS >= 2% OF CHAIN CALL+PUT MODELED MAGNITUDE SHOWN . <K> MORE" /
  "OUTSIDE BINS >= 2% OF CHAIN CALL+PUT MODELED MAGNITUDE: NONE"
- accessible table: "ALL 31 BINS + OUTSIDE BINS" with columns BIN | INTERVAL
  | CALL MODELED MAGNITUDE | PUT MODELED MAGNITUDE | MODEL NET*
- footer as today: "as of HH:MM ET . Cboe ~15m delayed source"

Color: one neutral gray extent, one non-directional ink-colored net bar, muted
headings, no red/blue, no status colors. Sign is carried by side of zero and
the printed +/- value.

Forbidden anywhere in the fragment (extend the vocabulary test): gamma flip,
zero gamma, flip, long gamma, short gamma, dealer long / short, "dealers are",
hedging pressure, support, resistance, magnet, pin, pinning, expected move,
volatility suppression / expansion, acceleration, reversal, target, bullish,
bearish, tracks spot, at spot, max pain, regime, wall, dominant (as a label),
gross, cancellation, offset, box, spread, financing, footprint, paired,
"two-sided", any SPY price, any drawn line where model net changes sign, any
per-expiry claim, relative "ago" freshness.

Provenance classes kept distinct: provider-observed (OI, spot, timestamp);
provider model output (gamma); Cuttingboard arithmetic (sums, bins, CALL+PUT MODELED MAGNITUDE,
coverage); configured assumption (sign, multiplier, 1%, bin size, window,
2% threshold); human interpretation (none rendered).

## 13. PROVIDER-RIGHTS STATUS

Not reopened. The accepted posture (personal, non-redistributed,
context-only) and the enforced raw-chain / per-contract-row prohibition
(PRD-306 R12) are unchanged by a derived, columnar, run-local carrier; the
board shows 31 bins plus a bounded list. The known authority/evidence tension
(binding main GEX GO vs the unmerged PR #262 evidence) is an explicit Helm
hold before Gate A / public surfacing and is outside this correction.

## 14. PROTOTYPE RESULT (corrected)

Historical concepts A (net-only ladder), B (net over magnitude ladder, red /
blue), C (columns) are SUPERSEDED BY EVENT-1 CORRECTION and kept only as
evidence of the form decision: the ladder form won because a net-only ladder
renders the 7700 bin as nothing and the column form is unreadable at 31
columns on a phone.

Current prototype: `evidence/proto_corrected_ladder.html` (generator
`evidence/proto_generator_corrected.py`), rendered from the same live chain:
single neutral extent, single ink net bar, neutral headings, section 12
labels, coverage line in both directions, outside line with counts, C/P/D
legend, expiry/root line, adjacent qualifier, and the full 31-bin accessible
table in a closed `<details>`. Screenshot reviewed at a 360 px frame: the
sign remains readable from side-of-zero plus the printed value; the 8000 row
reads as the widest extent with a small net bar; nothing in the block carries
a hue.

## 15. CODEX HIGH PACKET

`GEX_4_CODEX_HIGH_PACKET_2026-09-03.md` is the frozen Event-1 input and is
historical (see section 0). This document is the current candidate.

## 16. RECOMMENDATION

BUILD, as corrected. Product-test answers (updated): the ladder answers where
call and put modeled magnitude sit relative to spot, whether it is one-sided
or near-balanced, and whether the three anchors are spikes or ridges; the
most likely false reading ("widest extent = strongest dealer level") is met by
the bounded vocabulary, the absence of directional color, the raw-anchor
legend, and the adjacent qualifier, and is the strongest reason not to ship
if Helm judges copy insufficient. Complexity remains bounded: producer
+35-45 LOC, consumer ~160-200 LOC, no renderer or CSS change, no dependency.
The VISION "does not change a decision" tension is pre-existing for all GEX
context and owner-ruled by doctrine 4.1; if not extended to this slice the
answer is DO NOT BUILD.

Live validation (recorded per Helm; not all pre-build blockers): ordinary
intraday sample; the 13:10 PT observation; a standard monthly-expiration day
(may be post-merge commissioning evidence). Synthetic unit and mutation tests
establish the settlement validity rules regardless.

Next-step authority plan: Event 2 exact-corrected-head confirmation; Helm
design-direction ruling; DESIGN session drafts the PRD (MATERIAL under GOV-2;
FILES = tools/gex_snapshot.py, cuttingboard/delivery/gex_card.py,
tests/test_gex_snapshot.py, tests/test_gex_card.py, docs/SCHEMA_MAP.md,
docs/CALL_SITE_MAP.md, registry/index); fresh-context PRD review; Gate A;
IMPLEMENT session with the validate-then-fix rule.

## 17. ANOMALIES / FUTURE (recorded, not acted on)

- A1 (finding, current card): the largest-call-magnitude and
  largest-put-magnitude anchors coincide at 8000 on both samples because
  both magnitudes are large there; the PRD-309 "wall" labels imply more than
  that. Relabel is proposed in section 12 (text-only) for Helm's ruling.
- A2 (finding, producer): PRD-306.md:274-275 expects a zero same-day
  numerator outside market hours; expiry-day post-close feeds still carry the
  expired rows (504 rows, 2.5%, 18:42 ET; 522 rows, 7.6%, 16:41 ET on
  2026-08-20) with degenerate model gammas. Whether the 13:10 PT run sees them
  is UNKNOWN. The core 0DTE semantics are NOT changed by GEX-4 (Helm R6
  boundary); a core correction needs its own PRD.
- A3 (stale map): `docs/CALL_SITE_MAP.md:68` says the renderer emits
  `market_state_panel.render_fragment`; `rg market_state_panel
  cuttingboard/delivery/dashboard_renderer.py` returns nothing. Fix in the
  next PR that touches the map.
- A4 (stale snapshot): `ui/dashboard.html` on main predates PRD-318+ and has
  no GEX block; regenerate only via the pipeline.
- FUTURE (not v0): 0DTE per-strike overlay from an intraday sample; expiry
  facet; core same-day handling post-close; SPY GEX as its own underlying
  (never a mapped SPX ladder); an above-the-fold one-line magnitude figure
  once the ladder proves useful.
