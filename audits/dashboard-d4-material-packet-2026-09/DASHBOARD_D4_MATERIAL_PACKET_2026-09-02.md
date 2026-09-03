# Dashboard D4 - Proto-B primary-path synthesis + SPY chart LEVELS control - MATERIAL design packet

```
STATUS: PROVISIONAL MATERIAL PACKET - 2026-09-02 - DESIGN ONLY
GOV-2 PACKET-REVIEW CYCLE: EVENT 1 (Sol/Codex, fresh context, HIGH) PENDING.
AUTHORIZES NO IMPLEMENTATION, NO PRD, NO GATE A, NO MERGE.
Every FILES / LOC figure below is ESTIMATED SURFACE - NOT YET APPROVED (GOV-2 sec5).
Repository truth at authoring: main 858147f2057ed967d7d17fbc4a8c2f6cc20bfb71
(renderer, chart module and tests byte-identical to 218fb9a; 858147f adds only
docs/product/ASTROLOGY_MODE_CONCEPT_RECORD_v0.1.md).
Branch: claude/d4-proto-b-levels-design (docs branch; carries this packet only).
```

> Upstream MATERIAL design packet for the owner charge "CUTTINGBOARD D4 -
> PROTO B + CHART LEVELS ARCHITECTURE" (2026-09-02). Sequence: this packet ->
> Event-1 review -> one consolidated correction -> Event-2 exact-head
> confirmation -> Helm design-direction ruling -> Stage-0 downstream PRD.
> Design evidence: the POST-D3 PRODUCT AUDIT (2026-09-02, chat deliverable),
> the D4 visual prototype (Proto A / B / A2, 2026-09-02, chat deliverable) and
> the LEVELS prototype measured in this packet (section 10).
> Substantive deviation from Helm rulings: NONE (section 12).

## 1. OWNER RULINGS RECORDED (charge 2026-09-02, verbatim intent)

- H1. PROTO B is the selected visual direction. A and A2 are not the primary
  basis. B's density, ordering, spacing and OPEN SPY ladder are preserved
  unless this packet proves a direct contradiction (it does not).
- H2. Primary path: VERDICT -> TAPE -> SPY SESSION -> NEXT EVENT -> WATCHING ->
  DETAILS / HISTORY.
- H3. SPY header keeps B's compact treatment with the levels-clock line
  corrected to "Market-map levels 2:24 PM PT . daily bars through Sep 1".
  When a state needs it, the clarifier is "no current price/VWAP read". No
  wording may imply the market-map VWAP is the stale session read. CLOSED is
  NOT inferred in the renderer (later producer slice). ORB wording stays
  compact.
- H4. Chart doctrine: BASE preserves price; LEVELS exposes references; a
  future ASTROLOGY layer exposes observed geometry. None of them changes
  market truth, permission, ranking, candidate selection or trade state.
  LEVELS and ASTROLOGY are independent, orthogonal controls.
- H5. D4 designs ONE real interactive control, LEVELS. OFF = clean chart with
  BASE references only; ON = deterministic reference levels overlaid at their
  true price coordinates with honest collision handling; no y-scale
  distortion; no new data; GEX is not part of D4.
- H6. No dead ASTROLOGY control is rendered. The extension point is reserved
  internally and tested structurally.
- H7. The existing SPY ladder remains useful in its own right; it is not
  removed to save pixels. A change is recommended only if LEVELS creates
  redundancy that materially harms the primary path.
- H8. Interaction boundary: trace the existing script authority first; prefer
  the smallest robust mechanism; the toggle works on mobile tap, preserves
  accessibility, changes no server-derived fact, fetches nothing, persists
  nothing, alters no permission/ranking/state, and degrades safely without
  scripting. No framework, no broad client-state architecture.
- H9. The already-approved D4 primary-path work is carried: SPY (B
  presentation, one heading, compact state/clock language, SPY before
  candidates); NEXT EVENT (compact named-event strip, first event + "+N more in
  DETAILS", unavailable/expiry/Sunday semantics preserved); WATCHING (compact
  screening telemetry, zero qualified/setup count omitted, top rejection
  reason with count, candidate cards untouched, concise permission-honest
  setup header); DETAILS default collapsed; TAPE and VERDICT unchanged.
- H10. Out of scope (section 13) as charged.

## 2. MATERIALITY (GOV-2 sec1, applied at intake)

MATERIAL. Conditions that fire:

- selects an implementation seam shared across layers: the chart-layer
  composition in `cuttingboard/delivery/setup_chart.py` is consumed by
  candidate cards, the SPY section and `primary_selection.py` (section 4.6);
- changes a governance guardrail: PRD-329 R3 (exactly one script; native
  `<details>` only; no `[open]` CSS rule) is narrowed to admit one native
  form control (section 5.2);
- changes LOC ceilings and golden/hash authority in PRD-326 R6, PRD-327
  R5/R8/R9/R10 and PRD-329 R2/R4 (section 7);
- crosses delivery (chart module), dashboard (renderer, CSS) and the test
  seams that pin them.

Lane: STANDARD at minimum (MICRO unavailable under GOV-2 sec1). No PRD-121 R11
trigger is identified by the author; the downstream PRD re-applies the lane
matrix.

## 3. EVIDENCE INDEX

- This packet (provisional; Event-1 head named in the Event-1 record).
- CODEX_REVIEW_PROMPT_2026-09-02.md - Event-1 dispatch prompt (added with the
  Event-1 record).
- CODEX_EVENT_1_REVIEW_2026-09-02.md - Event-1 review (pending).
- Prototype and measurement artifacts (scratch, non-durable, cited for
  provenance only; every load-bearing number is copied into section 10):
  `/tmp/claude-1000/-home-dustin-Projects-cuttingboard/39db22ac-980f-483c-bfb8-49a50ecb4b93/scratchpad/`
  `proto_B_levels.html`, `proto_B_levels_stress.html`, `gen_levels.py`,
  `shoot.py`, `shoot_levels.py`, `proto_B_levels_measure.json`,
  `proto_B_levels_stats.json`, `shot_proto_B_levels_off_y486.png`,
  `shot_proto_B_levels_on_y486.png`, `shot_proto_B_levels_stress_on_y486.png`,
  `live_dashboard.html` (origin/publish 6f22a00, run 2026-09-02 21:24Z),
  `live_spy_chart.svg`, `chart_map.md`, `renderer_map.md`.

## 4. RECON (repository truth at 858147f; every claim carries file:line)

### 4.1 Renderer section map (emission order is document order)

`render_dashboard_html` (`cuttingboard/delivery/dashboard_renderer.py:2454-3811`)
writes five buffers concatenated at `:3798-3803`; no CSS `order` exists and no
sequence-keyed selector crosses a zone boundary (`_CSS` `:854-1102`; the only
sequence-keyed rules are intra-zone: `:1027`, `:1034`, `:1045`, `:1048`,
`:1097`, `:1099`).

| zone | id | lines | notes |
|---|---|---|---|
| VERDICT | `#verdict-zone` / `#system-state` | 2726-2922 | unchanged by D4 |
| TAPE | `#tape-zone` | 2925-3017 | unchanged by D4 |
| TODAY | `#today-zone` | 3019-3050 | EVENT RISK count (3024-3034); SPY SESSION state cell (3036-3044); Sunday cell (3046-3047) |
| WATCHING | `#watching-zone` | 3052-3328 | `#opportunity-survival` 3056-3145; `#candidate-board` header 3172-3175; cards 3177-3312; `#alert-watchlist` 3314-3326 |
| SPY SESSION | `#spy-session` | 3330-3344 (call) + `_render_spy_session` 2392-2452 | six-row kv-grid 2418-2429; chart call 2440-2443; caption 2446; ladder 2450-2451 |
| DETAILS | `#details-history` | 3346-3796 | unchanged by D4 |

Live-document facts that motivate D4 (origin/publish 6f22a00, phone render at
390x844): first candidate card at 845 CSS px; SPY block at 1537 (after
WATCHING) with an unstyled `<h3>` at 15.2 px white (no `#spy-session h3` rule
exists; only `#watching-zone h3,#details-history h3` are styled, `:1036`);
TODAY shows an event count without the event name while `#red-folder` and
MARKET CONTROL both name it; the WATCHLIST count (4) refers to QQQ, PAAS,
NVDA, AAPL held by the 3:30 PM ET gate (`cuttingboard/qualification.py:524-526`)
of which three never appear in the document; CHOP is 4 of 19 rejections.

### 4.2 Chart element classification (packet question B)

Source: `cuttingboard/delivery/setup_chart.py`. Geometry: viewBox 358x232
(`CHART_WIDTH`/`CHART_HEIGHT` `:54-55`), right gutter 78 (`_GUTTER` `:56`), so
the candle plot is 280 wide; pads 8 top / 14 bottom (`:57-58`); 40 bars
(`MAX_BARS` `:59`). The y-domain is bar highs/lows + NOW + contract pair +
Tier-2 levels; Tier-3 (EMA50, fibs) never widens it (`:176-186`, `:234`,
`:243`). The SVG is a flat f-string list joined at `:364`; no `<g>`, no ids, no
data attributes.

| # | element | source input | setup_chart.py | class today | D4 class |
|---|---|---|---|---|---|
| 1 | background rect (plot area) | - | 211 | none | BASE |
| 2 | candle wicks / bodies | bars | 271-282 | `candle-wick` / `candle-body` | BASE |
| 3 | NOW line | now_price | 307-311 | `lvl-t1 lvl-now` | BASE |
| 4 | NOW tag box + label | now_price | 333-340 | `now-tag` / none | BASE |
| 5 | date axis labels | bars first/last | 358-362 | none | BASE |
| 6 | VWAP line + rail label | watch_zones VWAP | 253-260 | `lvl-t2` / none | LEVELS |
| 7 | ORB band (range shading, opacity 0.10) | watch_zones ORB_HIGH+ORB_LOW | 221-227 | `orb-band` | LEVELS |
| 8 | ORB H / ORB L lines + labels | watch_zones | 261-266 | `lvl-t2` / none | LEVELS |
| 9 | PDH / PDL lines + labels | watch_zones | 261-266 | `lvl-t2` / none | LEVELS |
| 10 | EMA9 / EMA21 lines + labels | watch_zones | 261-266 | `lvl-t2` / none | LEVELS |
| 11 | fib 0.382 / 0.5 / 0.618 lines + labels | fib_levels.retracements | 233-241 | `lvl-t3` / none | LEVELS |
| 12 | EMA50 line + label | watch_zones EMA50 | 242-250 | `lvl-t3` / none | LEVELS |
| 13 | leader ticks (displaced labels) | derived | 342-346 | none | LEVELS (redesigned, section 5.3) |
| 14 | risk band, ENTRY/STOP lines, words, tags | contract_entry/stop | 214-220, 285-306 | `risk-zone`, `lvl-t1 lvl-entry/stop` | CANDIDATE ONLY (never emitted for SPY: `dashboard_renderer.py:2440-2443` passes `None, None`) |
| - | exact prices of every level, with % from NOW | market_map record | `_render_level_ladder` `dashboard_renderer.py:1970-2115` | `lvl-ladder` rows | LADDER ONLY (precise text; retained, section 5.4) |

Classification rationale. BASE is "price and the one orientation anchor":
candles, NOW, the date axis. Every reference in rows 6-12 is a deterministic
level derived from existing data and is precisely stated in the ladder, so
none is required for the clean chart to be readable. VWAP and the ORB band are
the two candidates for a BASE promotion (they are the session anchors named in
the SPY header); the author keeps them in LEVELS because on a 40-day daily
chart they sit within 3.7 units of NOW and read as clutter, not orientation
(section 10 numbers). This is Helm's call (section 11, D-2).

### 4.3 Current label placement (setup_chart.py:313-356) and its defects

NOW is pinned at true y. Other rail items are placed at true y if that fits,
else pushed outward from NOW in one pass (above list nearest-first, below list
ascending), pitch = half-heights (11.5 units Tier-2, 10.5 Tier-3, 15 boxed),
clamped to [10, 228]; no back-compression. A leader is emitted only when
displaced > 4 units, as a 2-unit-wide diagonal in `#333` (`:341-346`), which is
invisible against `#0a0a0a`. Live SPY consequence (`live_spy_chart.svg`): the
eleven level lines have true y within 47.6..106.5 (59 units for 771.8..756.0,
3.715 units per dollar); every rail label is displaced (EMA9 -8, fib 0.618 -17,
fib 0.5 -19, fib 0.382 -21; VWAP +13, EMA21 +23, PDH +35, ORB H +38, ORB L +47,
PDL +50, EMA50 +48 units). The rail reads as an evenly spaced list, not as
price-anchored labels; PDL's label sits 50 units below its line with no visible
origin. This is the "visual chaos" of H4.

### 4.4 Interaction authority (packet question E)

- The page emits exactly one `<script>` (`dashboard_renderer.py:2748`), the
  staleness banner `_STALENESS_BANNER_JS` (`:334-388`), whose bytes are
  SHA-pinned (`tests/test_dashboard_d2_seam.py:76,210-212`) and frozen by
  PRD-327 R10 (`docs/prd_history/PRD-327.md:410-417`).
- PRD-329 R3 (`docs/prd_history/PRD-329.md:261-267`): "exactly the one
  pre-existing `<script>`"; disclosures stay native `<details>`; "No new CSS
  selector targets `[open]`"; FAIL if `html.count("<script") != 1` or the diff
  adds `<script`, `onclick`, or a `[open]` CSS rule. Pinned by
  `tests/test_dash_candidates.py:1283-1297`.
- The renderer emits no `<input>`, `<button>`, `<label>`, `onclick`,
  `tabindex` or `aria-*` today (rg, zero hits). No CSP or nonce is emitted
  (`:2675-2679`), so policy, not the platform, is the constraint.
- Older rules in the same family: PRD-098 (diagnostics need no JavaScript,
  `docs/prd_history/PRD-098.md:64-65`), PRD-036/037 (no JavaScript, no external
  assets), PRD-321 (chart is a pure function bars + levels -> SVG string,
  `docs/prd_history/PRD-321.md:62-64`).
- No accessibility rule (aria, focus order, touch target) is recorded anywhere;
  D4 makes the first such decision (section 5.2).

### 4.5 Golden and hash authority (packet question F)

- `tests/data/dashboard_pre_a1c_chart_golden.html` (one candidate SVG) is
  asserted byte-equal by 9 tests (`tests/test_dashboard_renderer.py:5318-5370`)
  and self-seeds when missing (`:5321-5322`).
- `tests/data/dashboard_pre_gex_golden.html` (no SVG) is asserted byte-equal by
  `test_gex_absent_baseline_identical` (`:4707-4719`); any `_CSS` change breaks
  it.
- `tests/test_dashboard_d2_seam.py`: below-seam sha of both goldens (`:40-43`,
  `:320`), 15 fixture below-seam shas and 15 `#today-zone` shas (`:45-59`,
  `:256`, `:326`), `#system-state` and `#tape-zone` shape shas, the Updated
  line bytes (`:75`, `:208`), the staleness-JS sha (`:76`, `:212`), and the
  phone-block equality (`_PRD318_PHONE_BLOCK`).
- `tests/test_dashboard_renderer.py:5701-5711` `_S2_FIXTURE_SHA` hashes
  everything after `#watching-zone` in the `spy_session_observed` fixture;
  `:5510` pins the six-row kv-grid bytes; `:5525` requires the exact substring
  `<div class="spy-chart"><svg`.
- Section-order tests: `:4059-4069` (system-state < tape < today < watching <
  details), `:4072-4079` (exactly four `block operator-zone` before DETAILS),
  `:5496-5507` (watching < spy-session < details).
- `tests/test_setup_chart.py` is regex/substring only; `<g>` wrapping and
  label-y changes survive it; `:354` requires the string to start with `<svg`,
  `:161` requires every numeric `<text>` token to be an input price or fib
  ratio, `:251` requires the minimum font-size to be exactly 7.5.

Consequence: D4 changes bytes in `#today-zone`, below the WATCHING seam, in
`_CSS`, and in the SPY SVG. Both full-document goldens, the D2-seam hashes,
`_S2_FIXTURE_SHA`, the kv-grid byte test and the three order tests all move.
Each is re-pinned under the downstream PRD's authority, in the same PR, never
by deleting a self-seeding golden. VERDICT and TAPE shape hashes, the Updated
line bytes, the staleness-JS sha and the phone block stay untouched.

### 4.6 Data availability (packet question A)

Every LEVELS reference is already an input of `render_setup_chart_svg`:
`watch_zones` (VWAP, ORB_HIGH/LOW, PRIOR_HIGH/LOW, EMA9/21/50 from the market
map record) and `fib_levels.retracements`, plus `now_price`
(`dashboard_renderer.py:2438-2443`). The NEXT EVENT strip reads the existing
red-folder view (`_resolve_red_folder_view` `:3956-3975`; event fields `date`,
`time_et`, `name`, `type` as rendered at `:3569-3572`). The WATCHING line reads
`meta.symbols_scanned`, `sections.rejected`, `sections.watchlist` (`:3061-3131`;
watchlist items carry `symbol`, `reason`, `stage`, `detail`). The SPY header
reads `sections.spy_observation` (`state`, `reason`, `observed_at_utc`, `orb`,
`session_vwap`, `current_price`, `price_vs_vwap`; `cuttingboard/spy_observation.py:64-126`).
No new data, producer, persistence or provider. YES to question A.

Consumers of the chart function (`docs/CALL_SITE_MAP.md:79` is stale and says
one): `dashboard_renderer.py:2328-2337` (candidate, intraday A1-C),
`:2344-2352` (candidate, daily), `:2440-2443` (SPY, neutral), and
`cuttingboard/delivery/primary_selection.py:103-108` (non-emptiness predicate
only). The map is corrected as part of the downstream change.

## 5. DESIGN

### 5.1 Primary path (carried D4 work, H9)

S1 Order. `#spy-session` is emitted between `#today-zone` and
`#watching-zone`; TODAY becomes the NEXT EVENT strip and stays an
`operator-zone` block so PRD-327 R3's four-zone count holds; SPY SESSION stays
a non-operator `section` (PRD-329 R4). New order of ids: `system-state`,
`tape-zone`, `spy-session`, `today-zone`, `watching-zone`, `details-history`.

S2 SPY header (Proto B, H3). One heading (`<h3>SPY SESSION</h3>`, styled like
the zone headings by one CSS rule); the inner `<h2>SPY SESSION OBSERVATION</h2>`
and the six-row kv-grid are removed. Two lines from the observation carrier
plus one clock line for the market-map levels:

| observation state (reason) | line 1 (session clock) | line 2 |
|---|---|---|
| OBSERVED | `SPY 765.16 above session VWAP 765.11 . read 12:59 PM PT` (relation from `price_vs_vwap`; VWAP unavailable -> `SPY 765.16 . session VWAP unavailable . read ...`) | `ORB <lo>-<hi>` (or the closed ORB state word: `Opening range forming` / `unavailable` / `invalid`) |
| PRE_OPEN (pre_open, pre_open_prior_session) | `Pre-open . prior session read 12:59 PM PT` | ORB line as above |
| STALE (observation_lag) | `Session read not current . last 12:59 PM PT` | ORB line |
| STALE (session_mismatch) | `Session read is from another session . last <date> <time>` | ORB line |
| UNAVAILABLE (each reason) | `No session read . <reason text from _SPY_REASON_DISPLAY>` | ORB line |
| clock line, every state with a healthy map | `Market-map levels <PT time> . daily bars through <Mon D>` | - |

The clarifier `no current price/VWAP read` is appended to line 1 only in the
STALE and UNAVAILABLE states, because those are the states where the ladder
below shows a market-map VWAP while the carrier withheld its own; the phrase
"Market-map levels" names the ladder's source in every state so no wording
implies the map VWAP is the session read (H3). The STALE line never derives
CLOSED (H3). ORB stays compact (H3). `_SPY_STATE_DISPLAY` / `_SPY_REASON_DISPLAY`
symbols are kept (PRD-327 R10 pins them by no-diff); line 1 is composed from
them plus the existing reason map, and the raw-enum ban (PRD-329 R8) holds. The
chart caption that today prints the raw ISO map timestamp (`:2446`) is removed;
its two clocks live in the clock line (map time in operator PT via
`_operator_timestamp`; bars `as_of` via the existing `_price_bars_caption`
date). The R5 fail-closed ladder, R6 neutral ladder and R7 purity are
unchanged: the observation subtree stays a pure function of the same inputs and
byte-identical across permission states.

S3 NEXT EVENT strip. `#today-zone` keeps its id and `operator-zone` class;
heading `NEXT EVENT`; one line `NFP . Fri Sep 4 . 8:30 AM ET` from
`events[0]` (`type` when present else `name`, weekday + month-day from `date`,
`time_et`); two or more events append ` . +N more in DETAILS`; none ->
`No scheduled events in the next 48 hours`; expiring appends
` . schedule expiring`; loader failure -> `Event schedule unavailable`
(PRD-327 R6 string, above the fold); the Sunday `#premarket-banner` cell is
kept. The SPY SESSION cell (`:3036-3044`) is removed: it duplicated the SPY
header state and never carried a market fact.

S4 WATCHING. `#opportunity-survival` (h3 + five-row grid) becomes one
caption-weight line directly under `<h2>WATCHING</h2>`:
`23 screened . 4 held by the 3:30 PM cutoff . 19 rejected . top reason CHOP (4)`.
Rules: counts as computed today (`:3093-3108`, PRD-282 R1/R5/R6 semantics
unchanged, block-level fail-closed becomes line-level fail-closed); the
watchlist phrase uses a closed display map keyed on the watchlist `reason`
when every watchlist item shares one mapped reason (initial map: `entry blocked
after 3:30 PM ET` -> `held by the 3:30 PM cutoff`), else `N on watch`; the
QUALIFIED / SETUPS FOUND token appears only when the count is > 0 (`. N
qualified` / `. N setups found` under lock, PRD-304 R7 vocabulary); the top
reason is `top reason <REASON> (n)` with the same sanitisation as PRD-282 R7;
"mostly" is never used. The candidate-board header (`:3172-3175`) becomes one
line `SETUPS . screening grades, not permission`; the A+ lock relabel (PRD-304
R7) and every card are byte-unchanged. `#alert-watchlist` is unchanged.

### 5.2 Chart-control architecture (packet questions C, E, H, I)

Layer model (in `setup_chart.py`):

```
LayerSpec(key, label, default_on, user_control)          # frozen dataclass
CHART_LAYERS = (LayerSpec("levels", "LEVELS", False, True),)   # registry, D4
render_setup_chart_svg(..., layers=None)                 # None -> legacy flat bytes
```

- `layers=None` (every candidate call and `primary_selection`) returns the
  exact bytes it returns today: candidate charts, the A1-C golden's SVG and
  PRD-326 R2/R3 byte pins are untouched. This is the one abstraction the
  packet justifies NOW: an optional keyword that switches the same paint list
  into grouped emission.
- `layers=CHART_LAYERS` (the SPY call only) emits the same elements inside
  `<g class="chart-layer" data-layer="base">` (rows 1-5 of 4.2) and
  `<g class="chart-layer" data-layer="levels">` (rows 6-13, with the section
  5.3 rail). Paint order inside each group is unchanged. The root `<svg`
  string still starts the output (`tests/test_setup_chart.py:354` holds).
- Control emission (renderer, SPY section only), immediately before
  `<div class="spy-chart">` as its sibling:
  `<input type="checkbox" id="spy-levels" class="chart-toggle">` then
  `<div class="chart-controls"><label for="spy-levels" class="chart-toggle-label">LEVELS</label></div>`.
  One control per registry entry with `user_control=True`; with the D4
  registry that is exactly one, so no ASTROLOGY control can be emitted (H6).
- CSS (in `_CSS`): `.chart-layer[data-layer="levels"]{display:none}` and
  `#spy-levels:checked~.spy-chart .chart-layer[data-layer="levels"]{display:inline}`
  plus the label/pill rules and a `:focus-visible` outline. The pattern is
  `#<control-id>:checked~.spy-chart [data-layer="<key>"]`, one rule per layer,
  so a second layer is one registry entry, one render function and one CSS
  rule; the LEVELS contract (ids, classes, selector shape) does not change
  (question H: YES).
- Smallest interaction (question E): a native checkbox and `<label for>`.
  Zero JavaScript, so PRD-329 R3's script count and PRD-327 R10's JS pin hold;
  R3 is narrowed only to admit this one form control. Tap: the label is the
  hit target (25x81 CSS px measured; the downstream PRD may raise the label
  padding toward a 44 px target, section 11 D-5). Keyboard: native checkbox
  focus and space; `:focus-visible` outline. Screen reader: native checkbox
  semantics with the visible label text. No fetch, no storage, no state
  outside the checkbox; a reload returns to OFF. Degrade: with CSS
  unavailable the overlay and the checkbox are both visible, which is honest
  (all references shown, control still functional); with CSS but no scripting
  the control works because it never needed scripting.
- Truth invariants: the SVG content is identical in OFF and ON (only
  `display` changes), so toggling can never change a server-derived fact, a
  price, a permission, a grade or a ranking (H4, H8). R7 purity extends to the
  layered SVG and the control markup: both are pure functions of the same
  observational inputs plus the registry.
- What is premature (question I) and therefore NOT built: a generic
  client-state model, per-layer persistence, a layer manifest in the payload,
  a second toggle, any ASTROLOGY render function, any `data-layer="astrology"`
  string, or a control registry that spans candidate charts. The seam is a
  registry tuple, a `layers` keyword, group emission and the CSS selector
  pattern; nothing more.

### 5.3 Collision policy (packet questions C, D)

Deterministic, y-scale preserving, honest:

1. Level lines are always drawn at true y across the plot; the y-domain rule
   (`setup_chart.py:176-186`) is unchanged, so no label ever moves the scale.
2. Every LEVELS label gets a 3-unit tick at its true y on the rail edge
   (x 280-283) in the level's colour. The tick is the label's origin and is
   never displaced.
3. Label text always contains the price (`<name> <price:.1f>`; fib labels use
   the ratio alone, matching the ladder), so a label's position is never the
   only carrier of its price.
4. Placement: NOW's tag is pinned at true y (as today). Remaining labels are
   placed by an outward sweep from NOW, nearest-first above and below, at true
   y when that fits and otherwise at the first free pitch outward; pitch is
   10 units at the 8.5-unit floor font for every LEVELS label (today Tier-3
   labels are 7.5, below the floor); frame clamps at 2 and height-14 with
   inward re-stacking; ties break by input order (already deterministic:
   fibs sorted high to low, zones in input order).
5. A label displaced by more than 2 units from its true y gets a visible
   leader (`#666`, 0.8 width) from its tick to the label's baseline; a label
   within 2 units gets the tick only.
6. Range shading: only the ORB band (an actual range) is shaded, at the
   existing opacity 0.10; PDH/PDL and fibs stay lines; no other shading.
7. Rail capacity: 232 units at pitch 10 fits 21 labels; the SPY set is 11 +
   NOW. When the set would exceed capacity the outermost labels are clamped
   and stacked, never dropped silently; the ladder still lists them. (Not
   reachable with the current closed level set.)

Measured on the live cluster and on a synthetic stress cluster: section 10.

### 5.4 Ladder relationship (packet question: ladder)

Recommendation: option A, the ladder always remains visible and LEVELS only
changes the chart. Reasons: the ladder is the only precise-price surface
(two decimals, percent from NOW) and the only one readable without any
interaction; with LEVELS ON the rail labels repeat the ladder's names and
one-decimal prices, which is spatial reinforcement, not a second source; H7
holds. The prototype confirms the ladder costs about 200 CSS px and that the
LEVELS control adds 33 CSS px; neither harms the primary path in a way that
justifies removing the ladder. No change to `_render_level_ladder`.

### 5.5 Future ASTROLOGY seam (H4, H6; packet question H)

The registry and the group/selector pattern are the whole seam. Adding the
future layer is: one `LayerSpec("astrology", "ASTROLOGY", False, True)`, one
render function producing elements for `data-layer="astrology"`, one CSS rule
in the same shape, and its own PRD under the concept record's rules
(`docs/product/ASTROLOGY_MODE_CONCEPT_RECORD_v0.1.md`, which records no
control expectation and four VISION tensions). The state matrix BASE / LEVELS /
ASTROLOGY / LEVELS+ASTROLOGY falls out of two independent checkboxes and two
independent selectors; neither reads the other. D4 emits no astrology string,
class, id, control or CSS (FAIL line in section 6).

### 5.6 Candidate charts

Unchanged bytes (H9, H10). Candidate calls keep `layers=None`; the candidate
chart CSS, disclosures, D1 primary-chart rule (PRD-326 R1) and D3 one-tap rule
(PRD-329 R1/R2) are untouched.

## 6. REQUIREMENTS (carried into the downstream PRD; each with a FAIL line)

- R1 Order. Ids appear in the order system-state, tape-zone, spy-session,
  today-zone, watching-zone, details-history; exactly four
  `class="block operator-zone"` blocks precede `#details-history`;
  `#spy-session` is never an operator-zone. FAIL: any other order or count.
- R2 SPY header. Exactly one `SPY SESSION` heading in the document; no `SPY
  SESSION OBSERVATION` string; no kv-grid inside `#spy-observation`; line 1
  and the ORB line are composed only from `sections.spy_observation`; the
  clock line names `Market-map levels` and the bars date; the clarifier
  appears iff state is STALE or UNAVAILABLE; no raw enum outside
  `data-raw-state`; no ISO timestamp text in `#spy-session`. FAIL: any
  violation on the state matrix fixtures.
- R3 Purity. `#spy-session` (header, control, SVG, ladder) is byte-identical
  across TRADE PERMITTED / STAY FLAT / OBSERVE ONLY / HALT / operator lock for
  the same observational inputs. FAIL: one differing byte.
- R4 NEXT EVENT. `#today-zone` renders the first event as `<type or name> .
  <Weekday Mon D> . <time_et> ET`, appends `+N more in DETAILS` iff N > 0,
  keeps the expiring / unavailable / Sunday strings, and contains no SPY
  state text. FAIL: an event count without a name when events exist; a
  missing `+N more`; a lost unavailable/expiring/Sunday string.
- R5 WATCHING line. One `<p class="screen-line">` replaces
  `#opportunity-survival`; the counts equal today's computation; the
  qualified token is absent at zero; the top reason carries its count; the
  word `mostly` never appears; the line is absent under the same fail-closed
  conditions as the old block. FAIL: any count mismatch against the fixture
  payloads; a zero token rendered.
- R6 Setup header. `#candidate-board` opens with exactly one `<h3>` reading
  `SETUPS` plus the clause `screening grades, not permission`; the old
  `candidate-scope` banner is absent; every candidate card's bytes are
  unchanged against the D3 fixtures. FAIL: card byte drift; banner present.
- R7 Layers. The SPY SVG contains exactly two `<g class="chart-layer">` groups
  with `data-layer="base"` and `data-layer="levels"`; base holds only rows 1-5
  of section 4.2; levels holds rows 6-13; the set of level lines, their y
  values and the candle bytes equal the legacy render of the same inputs.
  FAIL: an element in the wrong group; a candle or line byte that differs
  from `layers=None` output.
- R8 Control. Exactly one `<input type="checkbox" id="spy-levels"` and one
  `<label for="spy-levels">` in the document, both siblings preceding
  `<div class="spy-chart">`; unchecked by default; `html.count("<script") == 1`;
  no `onclick`; no `[open]` CSS rule; the two CSS rules of section 5.2 exist.
  FAIL: any count other than one; a second script; a JS handler.
- R9 Toggle semantics (browser-verified at 390x844 device metrics): on load
  the levels group's computed display is `none`; after one tap on the label
  it is not `none`; after a second tap it is `none`; the SVG innerHTML is
  identical before and after; no other element's text changes. FAIL: any
  step.
- R10 Rail honesty. Every LEVELS label's text contains its price; every label
  has a tick at true y; every label displaced > 2 units has a leader whose
  y1 equals the tick y; no label's y is outside [2, height-14]; the y-domain
  of the layered render equals the legacy render's. FAIL: a label without a
  tick or price; a leader whose origin is not the true y; a scale change.
- R11 Legacy path. With `layers=None` the function's output is byte-identical
  to 858147f for every fixture in `tests/test_setup_chart.py` and every
  candidate card in the D3 fixtures. FAIL: one differing byte.
- R12 No dead UI. The document and `_CSS` contain no `astrology` /
  `ASTROLOGY` string; the registry contains exactly one entry; a structural
  test renders with a two-entry registry containing a synthetic
  `LayerSpec("probe", ...)` and asserts an independent group, control and
  selector shape, then asserts the production registry emits none of them.
  FAIL: any astrology string in output; the probe test failing.
- R13 Ladder. `_render_level_ladder` and its call in `_render_spy_session`
  are unchanged. FAIL: a diff hunk in either.
- R14 Responsive. At 360x780, 390x844 and 430x932 device metrics:
  `scrollWidth == innerWidth`; no element's right edge exceeds the viewport;
  the control is tappable at all three. FAIL: overflow at any width.
- R15 Byte freezes kept. `#system-state` and `#tape-zone` shape shas, the
  Updated line bytes, `_STALENESS_BANNER_JS` sha and the phone block equality
  are unchanged. FAIL: any of them edited.

## 7. PREDECESSOR CLAUSES (packet question G)

Changed (SUPERSEDED IN PART by the downstream PRD; propagated per GOV-2 s10):

- PRD-318 R1 order clause (`docs/prd_history/PRD-318.md:51-53`): SPY SESSION
  moves before TODAY; TODAY becomes the NEXT EVENT strip. R3 (`:60-63`) is
  preserved in substance (named event replaces the count; honest empty
  states kept).
- PRD-327 R1 id order (`docs/prd_history/PRD-327.md:299-314`): new id order.
  R5 (`:349-355`) `#today-zone` byte identity: superseded; re-pinned to the
  strip. R8 (`:378-394`) no-new-text-above-the-fold: narrowed to admit the
  strip's event text and the SPY header lines (the banned-token list stays in
  force and the new text contains none of the tokens). R9 (`:395-409`)
  below-seam hashes: re-pinned. R10 (`:410-417`): preserved.
- PRD-329 R3 (`:261-267`): narrowed to admit exactly one native checkbox and
  label for the SPY chart; script count, `[open]` ban and native `<details>`
  rule preserved. R4 (`:270-288`): kv-grid "bytes unchanged" and the
  after-WATCHING position: superseded by sections 5.1 S1/S2. R5 caption rule
  (`:340-350`): the two clocks move from the caption to the clock line; the
  fail-closed ladder (a)-(d) preserved. R9 (`:420-439`): preserved. R10
  phone matrix (`:440-455`): extended with R9/R14 of this packet.
- PRD-282 R1-R7 (`docs/prd_history/PRD-282.md:112-196`): counts and
  fail-closed semantics preserved; presentation (labels, grid, PRIMARY
  REJECTION row) superseded by section 5.1 S4.
- PRD-304 R7 (`docs/prd_history/PRD-304.md:274-293`): SETUPS FOUND vocabulary
  preserved for the non-zero token; the A+ tier relabel preserved.
- PRD-321 R1/R4 ladder rules and ruling Q2 as narrowed by PRD-329: preserved
  (ladder unchanged, one candidate chart, one observational chart). The chart
  module's pure-function rule (`PRD-321.md:62-64`) preserved: `layers` is an
  input, not I/O.
- PRD-326 R1-R5: preserved (candidate charts byte-unchanged). R6 goldens
  (`PRD-326.md:332-345`): re-pinned under the PRD.
- PRD-322 R5 (GEX/PARTICIPATION absence rows): preserved, out of scope.

Preserved without change: VERDICT (PRD-327 R1/R2), TAPE (PRD-327 D2-Q2, R4),
DETAILS content set (PRD-318 R5), MARKET CONTROL placement (PRD-329 R9), the
producer stale rule (`spy_observation.py:33`), A1-C intraday behaviour
(PRD-324), Second-Model and lane rules.

## 8. ESTIMATED SURFACE - NOT YET APPROVED (GOV-2 sec5)

Production FILES:
- `cuttingboard/delivery/setup_chart.py` - `LayerSpec`, `CHART_LAYERS`,
  `layers=` keyword, grouped emission, LEVELS rail policy: about +95 lines.
- `cuttingboard/delivery/dashboard_renderer.py` - S1 move (+2/-2), S2 header
  (-14/+24), caption removal (-1), control emission (+4), CSS rules (+9 lines
  inside `_CSS`), S3 strip (-16/+18), S4 line (-24/+14) and header (-3/+1):
  about +72 / -60, net +12.
- `docs/CALL_SITE_MAP.md` - one row corrected.
- Estimated production ceiling: 120 net lines across the two modules.

Test FILES: `tests/test_setup_chart.py` (R7, R10, R11, R12 probe),
`tests/test_dashboard_renderer.py` (R1-R6, R8, R13, golden regeneration,
`_S2_FIXTURE_SHA` re-pin), `tests/test_dashboard_d2_seam.py` (R5/R9 re-pins,
R15 keeps), `tests/test_dash_candidates.py` (R6 card bytes; the
`count("<script")` assert unchanged), `tests/test_dash_system_state.py`
(PRD-282 presentation tests rewritten to the line), `tests/preview_fixtures.py`
(state-matrix fixtures for R2), `tests/data/dashboard_pre_gex_golden.html` and
`tests/data/dashboard_pre_a1c_chart_golden.html` (regenerated deliberately),
plus one browser acceptance script for R9/R14 in the PRD-327 R11 `measure.py`
style. Estimated test ceiling: 420 lines net.

## 9. TEST CONE (packet question J)

- T1 LEVELS OFF preserves the base chart: layered render's base group equals
  the legacy render minus rows 6-13 (element-by-element).
- T2 LEVELS ON adds only authorized overlays: the levels group's element set
  equals rows 6-13 for the same inputs; no ENTRY/STOP/risk-zone in the SPY
  SVG (kept from D3).
- T3 Toggling never changes facts: innerHTML equality before/after two taps;
  `data-raw-state`, ladder rows and header text unchanged (browser).
- T4 Mobile accessibility: label tap toggles at 360/390/430; checkbox is
  focusable and space toggles it (browser); one `<label for>` bound to the
  input.
- T5 No permission/ranking/state byte change: R3 purity across the five
  permission states; candidate cards byte-identical to the D3 fixtures.
- T6 Extension seam: the probe-registry structural test (R12); production
  registry emits one control and two groups only.
- T7 No dead ASTROLOGY UI: rg-style assertion over the rendered document and
  `_CSS`.
- T8 Rail honesty (R10) on the live SPY level set and on a synthetic 11-level
  cluster within 3 dollars.
- T9 Legacy byte identity (R11) across the existing `test_setup_chart.py`
  fixtures.
- T10 State matrix for the SPY header (R2): OBSERVED with and without VWAP,
  PRE_OPEN both reasons, STALE both reasons, UNAVAILABLE every reason, plus
  map unhealthy / no SPY record / invalid price / no bars.
- T11 NEXT EVENT matrix (R4): 0, 1, 2 events; expiring; unavailable; Sunday.
- T12 WATCHING line (R5): live-shaped payload (23/4/19/CHOP 4), zero rejected,
  mixed watchlist reasons, lock vocabulary, fail-closed suppression.
- T13 Order and count (R1) and responsive (R14).
- T14 Freezes kept (R15).

## 10. VISUAL PROTOTYPE MEASUREMENTS (Proto B + LEVELS, this session)

Method: Chrome 151 headless driven over the DevTools protocol with
`Emulation.setDeviceMetricsOverride` (mobile, DPR 2); each run asserted
`innerWidth`/`innerHeight` equal to the requested viewport and asserted the
levels group's computed display for OFF and ON. Baseline bytes: the published
2026-09-02 21:24Z document. Market facts unchanged.

| measure | 360x780 | 390x844 | 430x932 |
|---|---|---|---|
| viewport asserted | yes | yes | yes |
| rendered SVG width (CSS px) | 322 | 352 | 392 |
| candle plot width (CSS px) | 252 | 275 | 307 |
| annotation rail width (CSS px) | 70 | 77 | 85 |
| minimum rail label font (CSS px) | 7.6 | 8.4 | 9.3 |
| LEVELS labels | 11 | 11 | 11 |
| control (label) height x width (CSS px) | 25 x 81 | 25 x 81 | 25 x 81 |
| horizontal overflow | none | none | none |
| SPY SESSION top / first candidate card top (CSS px) | 509 / 1294 | 494 / 1264 | 461 / 1243 |

Placement on the live SPY set (SVG units; 11 labels, pitch 10, NOW pinned at
72.3): every label is displaced (11 leaders); maximum displacement 40.9 (PDL,
true 93.4 -> 134.3); minimum gap 10.0; no clamp reached. Compared with the
live renderer (maximum displacement 50, invisible leaders, Tier-3 font 7.5),
D4 reduces the fan by 18 percent, adds a true-y tick and a visible leader to
every displaced label, and raises the smallest label to the floor. Synthetic
stress (11 levels within 3.30 dollars of NOW, 0.55 apart): all 11 displaced,
maximum 51.8, minimum gap 10.0, no clamp, no overflow.

Vertical effect: the LEVELS control adds 33 CSS px above the chart (first
candidate 1231 -> 1264 at 390). Against D3 (845) the first candidate sits 419
px lower in this prototype, of which about 600 is the promoted SPY block and
about -180 is the D4 cuts; Helm accepted this cost by selecting B over A2.

Screens (scratch): `shot_proto_B_levels_off_y486.png`,
`shot_proto_B_levels_on_y486.png`, `shot_proto_B_levels_stress_on_y486.png`.
Visual reading: OFF is candles plus NOW and nothing else; ON shows the eleven
lines as the tight band they really are (seven within 0.7 percent of price)
with a legible, price-anchored rail; the stress case fans symmetrically around
NOW and every label keeps its tick.

## 11. OPEN HELM DECISIONS

- D-1 STALE clarifier placement: append `no current price/VWAP read` to line 1
  in STALE and UNAVAILABLE (author's default, +1 wrapped line at 390) or rely
  on the `Market-map levels` attribution alone.
- D-2 BASE membership: candles + NOW + axis only (author's default), or promote
  VWAP and the ORB band into BASE as session anchors.
- D-3 Rail label font floor 8.5 units (8.4 CSS px at 390; 7.6 at 360) or
  raise to 9 with pitch 11 (more displacement, larger text).
- D-4 Ladder relationship: option A (author's recommendation) confirmed.
- D-5 Control hit target: keep the 25 px pill or pad to 44 px.
- D-6 Confirm the narrowing of PRD-329 R3 to admit one native checkbox +
  label, and that this does not reopen D1/D2/D3.
- D-7 Watchlist reason display map: closed map with `N on watch` fallback
  (author's default) or always `N on watch`.

## 12. SUBSTANTIVE DEVIATION FROM HELM RULINGS

NONE. Author-chosen defaults that Helm may override are listed in section 11.

## 13. OUT OF SCOPE (charge section 8, restated)

Astrology Mode implementation; lower-timeframe SPY chart; GEX overlays or
visualization; new indicators, data, persistence, provider work; strategy,
backtesting, prediction, alerts; permission, ranking or candidate changes;
producer CLOSED state; watchlist-name exposure; GEX/PARTICIPATION absence
relocation; any change to VERDICT, TAPE, DETAILS content, candidate cards,
the ladder or the A1-C intraday path.
