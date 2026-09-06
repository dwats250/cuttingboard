# PRD-336 PROVISIONAL PLAN - Cockpit context polish (final pre-live pass)

Design packet (Layer 2 DESIGN). Carries NO implementation authority. The wall,
owner holds, precedence and escalation still bind. This plan is the design
record behind PRD-336.md; Gate A on the reviewed PRD is the first binding
FILES/LOC ceiling and the only implementation authorization.

- Base repo SHA: cf693992043adfaec6b3e66e60f956044a90bc35 (origin/main; PRD-335
  merged, PR #323). Branch: claude/prd-336-cockpit-context-polish.
- Reserved PRD number: PRD-336 (verified free; PRD-335 is the highest used).
- CLASS: CONSUMER. LANE: HIGH-RISK. MATERIAL: YES.
- Test baseline at base: 4562 passing, 1 xfailed (CI truth on main, #323).

--------------------------------------------------------------------------------
## 1. OBJECTIVE
--------------------------------------------------------------------------------

Complete peripheral market context and remove the final small presentation
irritants, so the dashboard is used in a live market session after this pass.
PRD-336 is the LAST bounded cockpit-polish pass before live use. It adds NO
decision authority: every new observation is display-only, fenced out of every
vote site by the same five/six-step mechanism PRD-335 shipped.

Five new display-only observations: 5Y (FRED DGS5, daily), EURUSD (EURUSD=X),
USDCAD (USDCAD=X), NG (NG=F front-month), ETH (ETH-USD). Plus a bounded-window
reliability fix to the existing FRED DGS2 carrier; a responsive four-across macro
cockpit; and four contained renderer-only presentation edits (SPY session copy,
Market Context strip, History order/visibility, Trend/Vehicles de-duplication).

--------------------------------------------------------------------------------
## 2. LINEAGE AND AUTHORITY (what this pass narrows)
--------------------------------------------------------------------------------

PRD-336 is a direct successor to PRD-335 and REPLAYS its mechanisms (the FRED
carrier, the display-only driver fence, the twin driver-key whitelists, the
as_of daily-cadence contract). The charge issues new Helm design direction that
NARROWS three PRD-335 rulings. A charge may narrow a higher authority; these are
recorded so the change is not silent:

- Supersedes D-4 (muted trailing CRYPTO): R1/R6 merge VOLATILITY + CRYPTO into a
  single un-muted top family "VOL / CRYPTO" (VIX, BTC, ETH). BTC's ingestion and
  its macro-pressure vote are UNCHANGED; only its presentation moves.
- Supersedes D-2 (keep History placement, no reshuffle without evidence): R10 is
  the evidence - reorder History to SCOREBOARD, MARKET CONTROL and make both
  visible by default.
- Narrows D-3 (keep the Trade Vehicles grid, captioned): R11 makes the grid a
  CONDITIONAL fallback - shown only when Trend Structure prints no live prices -
  preserving D-3's stated reason (the grid is the sole ETF-price surface when the
  trend snapshot is degraded) while removing the redundancy in the live view.

Frozen by the charge and NOT touched: WATCHING (R9), the SPY Levels toggle and
chart interaction, verdict composition (absent a genuine semantic bug), live-GEX
acquisition and GEX substance (R12), PRD-333 synthetic/SPX GEX safety, PRD-110
Trend membership (SPY QQQ GDX GLD SLV XLE; no RSP, no IWM).

--------------------------------------------------------------------------------
## 3. SCOPE
--------------------------------------------------------------------------------

IN (renderer + data-registration + one carrier fix):
- Register 5 display-only macro drivers behind the full fence; add their tape
  slots and value formats; add DGS5 to the FRED carrier and bound the FRED
  request window.
- Restructure the macro cockpit to four cells across on desktop AND 390px, with
  a stacked (two-line) cell and the existing per-driver as_of line.
- Renderer-only: SPY session copy haircut (R7); Market Context low-height strip
  in the SPY region (R8); History reorder + un-hide SCOREBOARD/MARKET CONTROL
  (R10); Trend Vehicles conditional de-duplication (R11).
- Extend the decision-authority mutation fence for the 5 new drivers, and add a
  regime.py absence assertion (the fence currently omits site 5).

OUT / MUST NOT CHANGE:
- Any decision boundary: macro_pressure (_COMPONENT_KEYS/_COMPONENT_FIELDS/
  _classify_driver/_overall_pressure/build list), regime.py vote reads/raw_votes,
  execution_policy._apply_macro_pressure, MACRO_BIAS_DRIVERS, invalidation,
  trade_thesis, trade_explanation, primary_selection, setup_chart. Any edit ->
  STOP (scope breach).
- WATCHING hierarchy/selector/card/typography/lifecycle/chart (R9); SPY Levels
  toggle, chart interaction, SPY calculations, A1/intraday substitution, primary
  selection (R7).
- Verdict composition (#system-state) absent a genuine semantic bug.
- GEX acquisition/arithmetic/admission/freshness; PRD-333 gex_reference_v1.json,
  synthetic/SPX isolation, single-disclosure rule (R12).
- config.TREND_STRUCTURE_SYMBOLS (PRD-110 six); no RSP, no IWM, no breadth
  platform, no composite, no heatmap, no scoring change (R11).
- The trading universe (ALL_SYMBOLS / TRADABLES_ROW): no tradable removed.
- REQUIRED_SYMBOLS / HALT_SYMBOLS: the new drivers are optional; a fetch failure
  never halts.
- The byte-frozen SVG oracle (setup_chart_legacy_oracle.json,
  a1c_golden_embedded_svg_sha256), _STALENESS_JS_SHA, the #today-zone seam SHA.
- No new provider platform, no paid feed, no API key. FRED public CSV (bounded)
  and the existing yfinance provider only. No futures price labelled as a yield.

--------------------------------------------------------------------------------
## 4. MATERIALITY DECLARATION (GOV-2 s1)
--------------------------------------------------------------------------------

MATERIAL = YES. Triggers:
- delivery/dashboard_renderer.py is a HIGH-RISK CONSUMER file (lane-floor rule,
  Helm 2026-09-05).
- New macro-driver KEYS on a persisted, multi-reader schema
  (logs/macro_drivers_snapshot.json + payload), crossing config, contract,
  contract_types, persistence, delivery, notification.
- A change to the repo's only non-yfinance carrier (FRED), with its own network
  failure modes and a new daily series (DGS5) on the as_of contract.
- One new daily driver (rates_5y) extends the as_of daily-cadence contract and
  its 5-calendar-day staleness literal (enforced in three layers).

Because MATERIAL, this packet enters the GOV-2 upstream review order: fresh-
context independent review of the PRD against its exact revision, then Dustin
Gate A. No implementation before Gate A; no merge; no auto-merge.

Single-PRD justification (charge: aim for ONE bounded PRD-336): every item is
CONSUMER/display-only presentation plus a display-only carrier fix. No item
crosses a decision-authority boundary (the fence guarantees it), so no genuine
authority boundary forces a split. Breadth is flagged as review axis H (s13).

--------------------------------------------------------------------------------
## 5. CURRENT-STATE RECON (deliverable 1; all file:line at cf693992)
--------------------------------------------------------------------------------

Renderer: cuttingboard/delivery/dashboard_renderer.py (single renderer).

Macro cockpit:
- _MACRO_FAMILIES :323-336 = VOLATILITY(VIX) / RATES(2Y,10Y,30Y "selected
  maturities") / FX(DXY,USDJPY) / COMMODITIES(XAU->GC, XAG->SI, OIL->CL "front-
  month futures") / CRYPTO(BTC); _MUTED_MACRO_FAMILY="CRYPTO" :336.
- Cell builder _macro_driver_cell :3669-3689 (single line: label+arrow, then
  value; optional as_of span). Family loop :3699-3707.
- CSS: .macro-drivers-row :1038 = flex-wrap, .macro-tape-slot flex:1 1 90px :1039.
  NO @media rule touches any macro class -> today a 4-member family wraps 3+1 at
  390px; there is no 2x2 collapse and no fixed column count. .macro-tape-grid
  :1028-1029 is DEAD css.
- as_of marker .macro-tape-asof :1050 renders on its own line (PRD-335 5640404e);
  gated by _admit_daily_macro_drivers :1748-1761 / _RENDER_DAILY_MACRO_DRIVERS
  :1726 (only rates_2y today) / _MACRO_DAILY_MAX_AGE_DAYS=5 :1727.
- Value format _format_tape_value :1785-1809; non-finite -> "--" :1786.
- Slots in macro_tape_layout.py: MACRO_ROW_1 :34-41, MACRO_ROW_2 :43-57,
  TRADABLES_ROW :59-69 (SPY QQQ GLD GDX SLV XLE).
- Tradables grid rendered :3722-3733 inside #macro-tape (MARKET STRUCTURE),
  caption "TRADE VEHICLES / ETF last price"; .macro-tradables-grid 2-col :1040.
- Cell markup is byte-pinned by two targeted asserts
  (test_dashboard_renderer_macro_tape.py:42-43, test_dashboard_renderer.py:
  3716-3717) and the two whole-dashboard goldens.

Drivers / acquisition:
- config.MACRO_DRIVERS :263-266, SYMBOL_SOURCE_PRIORITY :292-307 (DGS2->fred),
  PRICE_BOUNDS :313-341, SYMBOL_UNITS :347-357.
- contract._MACRO_DRIVER_SYMBOLS :50-64 (10 keys), _DAILY_MACRO_DRIVERS :70
  ({rates_2y}); contract_types._OPTIONAL_MACRO_DRIVERS :49-51 ({oil,gold,silver,
  rates_2y,rates_30y,usdjpy}).
- payload._MACRO_DRIVER_FIELD_WHITELIST :346-357, _DAILY_MACRO_DRIVER_KEYS :24.
- FRED carrier: _fred_csv_url :441-442 builds fredgraph.csv?id=<series> with NO
  cosd/coed (FULL history); _fetch_fred_csv :445-449 (UA "cuttingboard/1.0",
  urlopen); _parse_fred_dgs2_csv :453-491 (latest/prior non-"." rows);
  _try_fred_quote :507-520 (FETCH_RETRIES=3, per-attempt 30s wrapping 10s
  urlopen, 2s backoff); _FRED_SERIES_BY_SYMBOL :434; _FRED_MAX_ASOF_AGE_DAYS=5
  :438. as_of stamped from CSV row date, distinct from fetched_at_utc.
- as_of threading: RawQuote.as_of :43 -> normalization :92 -> contract.
  _build_macro_drivers :611-616 -> snapshot -> renderer re-gate; and
  notifications _macro_row :102-117. Fixture loader admits as_of via
  runtime/_constants._FIXTURE_OPTIONAL_QUOTE_FIELDS :92-94.
- NO dedicated FRED carrier test exists (gap; PRD-198 #4 unmet for the carrier).

Vote sites (a driver votes iff present at one of these; all must stay ABSENT for
display-only):
1. macro_pressure._COMPONENT_KEYS :18-23
2. macro_pressure._COMPONENT_FIELDS :25-30
3. macro_pressure build list :126-133 (exactly 4 inputs)
4. macro_pressure._classify_driver :57-90 (raises for unknown at :90)
5. regime.py reads :159-164 + raw_votes :167-176
6. macro_tape_layout.MACRO_BIAS_DRIVERS :97-99
Consumer: execution_policy._apply_macro_pressure :292-310.

Layout regions (DOM order assembled :4031-4037): VERDICT / NEXT EVENT / MARKET
STRUCTURE / SPY SESSION / WATCHING / GEX / HISTORY.
- SPY copy _spy_session_lines :340-371 (multi-state prose), clock _spy_clock_line
  :374-383. DO-NOT-TOUCH: Levels toggle :2599-2601, setup_chart :2592-2595.
- Market Context card :3588-3597; source sits in MARKET STRUCTURE but buffers
  into _spy_lines via _active_lines swap :3590/:3598; feed sections.
  market_control_card via _mcc; empty states via _mcc_cell_display :243-251
  ("Unavailable - transition state unavailable", "No active candidates").
  Introduced PRD-289; split PRD-334 R6.
- WATCHING #watching-zone :3177. Shared CSS (regression risk): .kv-grid :1101
  (candidate card + market-context + market-control-card + opportunity-survival),
  .lvl-ladder :1115 (candidate card + SPY chart), .zone-item :1157, .setup-chart.
- History <details id="details-history"> :3917 collapsed by default, summary
  :3918; order MARKET CONTROL :3928, run-delta :3939, SCOREBOARD :3991; padding
  :1199 / :1298.
- Trend Structure #trend-structure :3786-3910; headers Symbol/Price/vs VWAP/
  Alignment/Entry Context/RVOL/SMA 50/200/Intraday :3814-3817 (carries a Price
  column); loops config.TREND_STRUCTURE_SYMBOLS = (SPY,QQQ,GDX,GLD,SLV,XLE)
  config.py:286; degrades to "--"/no-rows under unhealthy_lineage /
  inactive_session / MARKET_CLOSED|AWAITING_DATA / _ts_records is None :3794-3809.
- GEX #gex-zone :3540-3551 (gex_card.render_fragment; gex_reference PRD-333).

Frozen controls: whole-dashboard goldens tests/data/dashboard_pre_gex_golden.html
and dashboard_pre_a1c_chart_golden.html; region-SHA oracle
setup_chart_legacy_oracle.json (details-history, market-structure, system-state);
a1c_golden_embedded_svg_sha256; _STALENESS_JS_SHA; gex_reference_v1.json;
#today-zone SHA. Neutralized-macro protocol _NEUTRAL_MACRO_PATH avoids the dirty-
logs golden-parity trap.

--------------------------------------------------------------------------------
## 6. DECISION-AUTHORITY FENCE (deliverable 4)
--------------------------------------------------------------------------------

The five new drivers (rates_5y, eurusd, usdcad, natgas, ethereum) are
observational/display-only. They MUST NOT affect macro-pressure voting, regime,
posture, permission, ranking, qualification, sizing, candidate generation,
execution policy, HALT, GEX admission, or Trend membership. Existing semantics
of VIX / DXY / 10Y / BTC are unchanged.

A driver acquires decision authority ONLY by being wired into one of the six
vote sites (s5). The fence keeps all five new keys ABSENT from all six, and
PRESENT in the display/registration sites:
- config.MACRO_DRIVERS, SYMBOL_SOURCE_PRIORITY, PRICE_BOUNDS, SYMBOL_UNITS
- contract._MACRO_DRIVER_SYMBOLS; contract_types._OPTIONAL_MACRO_DRIVERS
- payload._MACRO_DRIVER_FIELD_WHITELIST (key-synced with the contract map)
- a macro_tape_layout TapeSlot
- rates_5y ALSO: contract._DAILY_MACRO_DRIVERS, payload._DAILY_MACRO_DRIVER_KEYS,
  dashboard_renderer._RENDER_DAILY_MACRO_DRIVERS (daily-cadence only).

Precedent (proven): oil/gold/silver and PRD-335's rates_2y/rates_30y/usdjpy sit
in the whitelists + optional set but are absent from all six vote sites.

Test extension (mutation-style, not whitelist-only). Extend
tests/test_prd335_display_only_fence.py:
- add the 5 keys to _NEW_DRIVERS :49 and _new_block's symbol map :73 -> F-1,
  F-2b (invariance + exact 5-key pressure result set), F-2d (one-time in-memory
  semantic-mutation-goes-RED demo on a disposable clone; production file never
  edited), and F-3 (sizing invariance) auto-cover via @parametrize;
- hand-extend F-4 injection :276-278, F-5 _full_macro_drivers :291-301 and
  _quotes_with_new :331-336; extend the guard-sync assertion for the new keys;
- ADD a site-5 assertion: each new driver's SYMBOL is absent from regime.py's
  read set / raw_votes (the current fence checks sites 1,2,6 statically but not
  regime); this closes "a whitelist-only test is insufficient" for site 5.
- rates_5y: add to _DAILY_MACRO_DRIVERS and give its _new_block an as_of.

FAIL: any new driver key present in any of the six vote sites; OR the fence test
passes when a new driver is wired to vote (false-green); OR the positive control
(F-2a) ever passes as equal; OR the guard-sync key sets drift.

--------------------------------------------------------------------------------
## 7. PER-ITEM DESIGN
--------------------------------------------------------------------------------

### R1 - Four-across macro cockpit (desktop AND 390px)

New _MACRO_FAMILIES (dashboard_renderer.py:323-336), four families:
  ("VOL / CRYPTO", ("VIX","BTC","ETH"), "")        # top; 3 cells; un-muted
  ("RATES",        ("2Y","5Y","10Y","30Y"), "selected maturities")  # 4 cells
  ("FX",           ("DXY","EURUSD","USDJPY","USDCAD"), "")          # 4 cells
  ("FUTURES",      ("CL","NG","GC","SI"), "front-month futures")    # 4 cells
Remove _MUTED_MACRO_FAMILY (BTC no longer a muted trailing row - supersedes D-4).
FUTURES uses the existing OIL/XAU/XAG slots with display "CL"/"GC"/"SI" (XAU/XAG
already display GC/SI; add display_label "CL" to the OIL slot) plus the new NG
slot.

CSS: change .macro-drivers-row (:1038) from flex-wrap to
  display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:6px 8px;
applied uniformly at all widths (NO media query needed; four narrow columns fit
390px). VOL / CRYPTO (3 cells) renders in columns 1-3 of the same 4-track grid so
its cells align vertically with RATES/FX/FUTURES columns 1-3 (aligned columns,
no fabricated fourth VOL/CRYPTO metric - charge: three meaningful cells over
filler). Remove the dead .macro-tape-grid :1028-1029.

Cell: rewrite _macro_driver_cell (:3669-3689) to a STACKED two-line cell -
line 1 label (e.g. "10Y"), line 2 arrow+value (e.g. up 4.78), line 3 the existing
.macro-tape-asof date for daily cells only. This is the only layout that fits
four across in ~81px columns at 390px; a single-line "USDCAD up 1.38" is ~86px
and overflows. Preserve data-symbol, the up/down/flat/na slot classes, and the
data-* engine attributes on #macro-tape. New .macro-cell CSS: text-align
centered or left, label .62rem muted, value 13px, asof .6rem muted (unchanged).

Ripple: both whole-dashboard goldens regenerate once; the two targeted cell-
string pins (test_dashboard_renderer_macro_tape.py:42-43,
test_dashboard_renderer.py:3716-3717) rewrite to the stacked markup. The SVG
oracle and #today-zone SHA are NOT affected (macro-tape is not in them).

### R2 - Actual 5Y yield (DGS5, daily)

Register rates_5y (label 5Y, symbol pseudo "DGS5", source fred) exactly like
rates_2y: config.MACRO_DRIVERS, SYMBOL_SOURCE_PRIORITY["DGS5"]=["fred"],
PRICE_BOUNDS "DGS5":(0.0,8.0), SYMBOL_UNITS "DGS5":yield_pct;
contract._MACRO_DRIVER_SYMBOLS rates_5y->DGS5; contract._DAILY_MACRO_DRIVERS +=
rates_5y; contract_types._OPTIONAL_MACRO_DRIVERS += rates_5y;
payload._MACRO_DRIVER_FIELD_WHITELIST + _DAILY_MACRO_DRIVER_KEYS += rates_5y;
renderer._RENDER_DAILY_MACRO_DRIVERS += rates_5y; MACRO_ROW_2 slot 5Y after 2Y.
2Y and 5Y are DAILY with explicit as_of; 10Y/30Y keep their existing yfinance
cadence. 5Y value format .2f (like 2Y/10Y/30Y). rates_5y is display-only (fence).
FAIL: a futures price used/labelled as a 5Y yield; OR 5Y presented as intraday;
OR rates_5y in any vote site; OR a stale/missing/future 5Y renders a number
instead of "--".

### R3 - FRED reliability fix (bounded window) + carrier red test

PROBE EVIDENCE (s14): the current request is UNBOUNDED. fredgraph.csv?id=DGS2
returns 208776 bytes / 13114 rows; the same request with &cosd=<recent> returns
198 bytes / 11 rows (about 1000x smaller). DGS5 proven to exist and parse
identically.

Design (smallest bounded acquisition):
- _fred_csv_url (:441-442) appends &cosd=<fetched_at.date() - N days> (N ~ 15, a
  window that guarantees >= 2 non-"." rows across long weekends/holidays while
  staying tiny). Optionally &coed=<fetched_at.date()>.
- Add "DGS5":"DGS5" to _FRED_SERIES_BY_SYMBOL (:434). DGS2 and DGS5 fetch through
  the SAME bounded per-symbol branch (two small bounded requests), preserving
  per-symbol never-raises isolation - do NOT combine into one id=DGS2,DGS5
  request (one failure would kill both, breaking isolation).
- _parse_fred_dgs2_csv (:453-491) is already series-agnostic (parses
  observation_date,<series>); rename to _parse_fred_csv for clarity; it must key
  the value column by header, not position, so DGS2 and DGS5 both parse.
- Preserve unchanged: actual authoritative yield; no API key; never-raises per-
  symbol isolation; 5-calendar-day fail-closed as_of; future/malformed/stale
  rejection (three layers: carrier :483-489, producer :606-616, renderer
  :1748-1761 - keep all three consistent for DGS5); deterministic tests;
  acquisition clock (fetched_at_utc) distinct from as_of.

HONESTY (TRUTH): the live "attempt 1/2/3 failed / fetch unavailable" is NOT
deterministically reproducible from the design environment - the unbounded fetch
usually succeeds in ~0.3s, and the carrier already sends a proper UA
("cuttingboard/1.0", :448), so UA blocking is NOT the cause. The observed tail-
request timeout under repeated hits points to intermittent slowness / FRED
throttling / transient outage - external, not a code-logic bug. Bounding the
payload 1000x is the charge-directed, strict robustness improvement (smaller
transfer window in which a slow/throttled connection can breach the 10s timeout);
it is a MITIGATION, not a proven root-cause fix. The existing safety net is
unchanged: per-symbol never-raises + the daily cell rendering "--" fail-closed,
so even a total FRED outage never touches a decision.

Red test (closes the PRD-198 #4 gap): a new FRED carrier test module (canned CSV,
no network) proving: bounded URL contains cosd; DGS2 and DGS5 both parse latest/
prior; "." gap rows skipped; stale as_of (> 5 days) -> fetch_succeeded=False;
malformed row -> fail-closed; future date -> fail-closed; network failure ->
never-raises (RawQuote fetch_succeeded=False). This is required, not optional.

R3 STOP escape: if reliable bounded FRED retrieval cannot be achieved without
materially larger architecture (a new provider abstraction, a change to the
global freshness model, or the real cause proving to be IP-level blocking that
bounding cannot fix), STOP that subpart and report. Do NOT swap to a futures
proxy. The rest of PRD-336 still ships; 2Y/5Y then render "--" via the existing
fail-closed path.

### R4 - FX peripheral vision (EURUSD, USDCAD)

Add eurusd (EURUSD=X) and usdcad (USDCAD=X) as display-only. Explicit currency-
pair labels DXY / EURUSD / USDJPY / USDCAD (no ambiguous EUR/JPY/CAD).
Registration mirrors usdjpy: MACRO_DRIVERS, SOURCE (yfinance), PRICE_BOUNDS
("EURUSD=X":(0.5,2.0), "USDCAD=X":(1.0,2.0)), SYMBOL_UNITS ("EURUSD=X":
usd_per_eur, "USDCAD=X":cad_per_usd); _MACRO_DRIVER_SYMBOLS; _OPTIONAL_MACRO_
DRIVERS; payload whitelist; FX-family slots. Value format .4f (e.g. 1.0823).
DISPLAY ONLY: EURUSD and USDCAD absent from all six vote sites. DXY keeps its
existing decision semantics; USDJPY stays display-only.
Symbol verification: EURUSD=X / USDCAD=X are hypotheses following Yahoo's
BASEQUOTE=X convention (matching shipped JPY=X). REQUIRED impl gate: mechanically
verify each resolves before wiring (probe or the ingestion path); FAIL if a
symbol does not resolve or returns a value outside its bounds.

### R5 - Futures (add NG)

FUTURES family CL / NG / GC / SI. CL=F (existing OIL slot, display "CL"), GC=F
(XAU slot, display GC), SI=F (XAG slot, display SI) unchanged; ADD natgas (NG=F,
display NG) display-only: MACRO_DRIVERS, SOURCE (yfinance), PRICE_BOUNDS
("NG=F":(0.5,20.0)), SYMBOL_UNITS (usd_price default), _MACRO_DRIVER_SYMBOLS,
_OPTIONAL_MACRO_DRIVERS, payload whitelist, a FUTURES slot. Value .2f. Keep these
as macro observations; do NOT confuse USO/XLE/GLD/SLV/GDX vehicles with the
underlying futures. Symbol verification per R4 (NG=F matches shipped CL=F/GC=F/
SI=F). natgas absent from all six vote sites.

### R6 - Crypto (add ETH)

VOL / CRYPTO family VIX / BTC / ETH. ADD ethereum (ETH-USD, display ETH) display-
only: registration mirrors bitcoin BUT ethereum is absent from all six vote sites
(bitcoin's macro-pressure vote is UNCHANGED; ETH gets no vote). PRICE_BOUNDS
("ETH-USD":(100,20000)), SYMBOL_UNITS usd_price, value .0f (or /1000 "K" >=10000,
mirroring BTC). Do NOT call the row "liquidity"; the visual heading "VOL / CRYPTO"
is the framing. Symbol verification per R4 (ETH-USD matches shipped BTC-USD).

### R7 - SPY session copy haircut (renderer-only)

Reduce _spy_session_lines (:340-371) to one concise operator line per session
state, folding the _spy_clock_line provenance into it. Conceptual target:
  "Pre-open . prior session Sep 4 . bars through Sep 4"
Preserve the meaningful state distinctions (OBSERVED / PRE_OPEN / STALE /
UNAVAILABLE and reason) and all provenance/freshness semantics (prior-session
date, bars-through date, map clock) - only the verbosity and vertical span
shrink. Do NOT modify the Levels toggle, chart interaction, SPY calculations,
A1/intraday substitution, or primary-selection. FAIL: any provenance/freshness
fact is lost, or a state distinction collapses into an ambiguous line.

### R8 - Market Context as a low-height strip in the SPY region

The Market Context card (:3588-3597, already buffered into the SPY region via the
:3590/:3598 _active_lines swap) is recomposed from a heading + kv-grid card into
a compact context STRIP that sits with SPY: when both TRANSITION and INVALIDATION
are unavailable/empty it renders as a single muted low-height line (e.g.
"Context: transition unavailable . no active candidates") rather than a full
card; when populated it renders compact inline rows. WATCHING rises naturally as
the empty card's vertical footprint shrinks. Preserve _mcc semantics and the
_mcc_cell_display value/reason maps (:196-251); do NOT redesign transition/
invalidation logic. Keep the buffer swap intact. FAIL: any transition/
invalidation semantic lost, or the strip claims data it does not have.

### R9 - WATCHING freeze

No change to WATCHING hierarchy/selector/card/typography/lifecycle/chart. The
only permitted contact is an unavoidable SHARED CSS change (.kv-grid :1101,
.lvl-ladder :1115, .zone-item :1157) that also serves WATCHING; if R8's strip or
R1's grid touches a shared class, it must be scoped (new class or a child
selector) so WATCHING's appearance/behavior is byte-preserved. Browser tests must
explicitly prove WATCHING did not regress at 390px and 1366px. FAIL: any WATCHING
visual/behavioral change.

### R10 - History tighter and useful

Reorder and un-hide History (<details id="details-history"> :3917). SCOREBOARD
(:3991) and MARKET CONTROL (:3928) become VISIBLE BY DEFAULT (moved out of the
collapsed <details>, or the section defaults open with these two above the fold);
order: 1 SCOREBOARD, 2 MARKET CONTROL, 3 remaining history/change material
(run-delta) if retained. Reduce excess vertical padding (:1199 / :1298). Do NOT
alter their underlying semantics (SCOREBOARD_LIMIT, _mcc data). Supersedes D-2.
Ripple: the details-history region SHA re-pins (authorized). FAIL: any semantic
change to SCOREBOARD or MARKET CONTROL; or the run-delta content changes.

### R11 - Trend / Vehicles de-duplication (conditional)

Trend Structure (:3786-3910) already carries a Price column over the same six
symbols as the Trade Vehicles grid (:3722-3733). The two price sources DIFFER:
the grid reads market_map.current_price; the table reads _ts_records.current_price.
So a symbol present in market_map but ABSENT from _ts_records reaches the healthy
table branch and renders Price "--" while market_map holds its price (independent
review blocking finding). Correct predicate: suppress the grid ONLY when the table
renders a finite live price for ALL SIX symbols (table not degraded -
unhealthy_lineage / inactive_session / MARKET_CLOSED|AWAITING_DATA / _ts_records
is None - AND every config.TREND_STRUCTURE_SYMBOLS symbol present in _ts_records
with a finite current_price); in EVERY other state (degraded, OR any symbol absent
from _ts_records) show the grid. This removes the redundant weaker price list only
in the fully-priced live view (charge intent) while guaranteeing no per-symbol
price loss (D-3's reason - market_map prices survive a stale/partial trend
snapshot). Gate the grid emission on those signals (available before :3722 in
source order; if not, move the health/coverage computation earlier - contained to
the renderer). Preserve PRD-110 membership (SPY QQQ GDX GLD SLV XLE); no RSP; no
IWM; no scoring change. No trading-universe symbol removed. Ripple: the
market-structure region SHA re-pins (authorized). FAIL: for any of the six
symbols, a state exists where the grid is suppressed while that symbol's Trend
Price is not a finite live price (proven by a partial-snapshot fixture); or the
grid renders alongside a fully-priced Trend Structure; or a universe symbol is
dropped; or Trend membership/scoring changes.

### R12 - GEX hold

Do NOT reopen live-GEX acquisition or redesign GEX. Only a truly cheap density
improvement that falls naturally out of adjacent layout work is permitted (and
only if it changes no GEX arithmetic/admission/freshness). Preserve PRD-333
safety: synthetic, SPX, not current, cannot affect permission/ranking/
qualification/verdict, cannot masquerade as SPY live data; gex_reference_v1.json
and the isolation AST guard unchanged. Record future product preference (non-
binding, to DECISIONS): when live GEX acquisition is revisited, investigate a
SPY-useful operator surface (SPY-specific data alongside SPX), not SPX-only.
FAIL: any GEX arithmetic/admission/freshness/isolation change in this PRD.

--------------------------------------------------------------------------------
## 8. DATA FLOW PER NEW OBSERVATION (deliverable 3)
--------------------------------------------------------------------------------

rates_5y (DGS5, daily, FRED): SYMBOL_SOURCE_PRIORITY fred -> ingestion
_try_fred_quote (bounded URL) -> RawQuote(as_of=row date) -> normalization
(as_of isoformat) -> contract._build_macro_drivers (block {symbol, level,
change_pct, as_of}; daily as_of gate) -> logs/macro_drivers_snapshot.json AND
payload -> both driver-key guards (as_of on the separate date path) -> renderer
#macro-tape RATES family (daily as_of line; "--" if stale/missing) AND
notifications _macro_row. Decision path untouched.

eurusd / usdcad / natgas / ethereum (yfinance, intraday): fetch_quote yfinance
branch -> RawQuote (no as_of) -> NormalizedQuote -> contract._build_macro_drivers
(block {symbol, level, change_pct}) -> snapshot AND payload -> both guards ->
renderer #macro-tape (FX / FUTURES / VOL-CRYPTO families) AND notifications.
Decision path (macro_pressure -> execution_policy; regime) reads only the four
existing voting drivers - UNCHANGED.

--------------------------------------------------------------------------------
## 9. TEST / FIXTURE / GOLDEN PLAN (deliverable 9)
--------------------------------------------------------------------------------

Discipline (PRD-335 pattern): editorial/registration edits land first, each with
targeted unit tests green (commit per validation step, ruff + pytest each);
goldens regenerate ONCE in a final dedicated commit; the golden diff is reviewed
region by region. Any diff outside the authorized regions (#macro-tape,
#spy-session incl. #market-context, #details-history, #market-structure) -> STOP.

Controls that must NOT move (asserted before/after regen): a1c_golden_embedded_
svg_sha256; setup_chart_legacy_oracle.json; _STALENESS_JS_SHA; #today-zone SHA;
#system-state region SHA (verdict frozen); gex_reference_v1.json; #gex-zone bytes;
#watching-zone bytes (R9 - must be byte-identical).

New / updated tests:
- FRED carrier module (NEW): bounded-URL cosd assertion; DGS2 + DGS5 canned-CSV
  parse; "." gaps; stale/malformed/future -> fail-closed; network fail ->
  never-raises. (Closes PRD-198 #4 for the carrier.)
- Fence (extend tests/test_prd335_display_only_fence.py): 5 keys into _NEW_DRIVERS
  + _new_block; F-4/F-5 injection dicts; guard-sync for new keys; NEW site-5
  regime.py absence assertion; rates_5y daily as_of. Positive control (F-2a)
  unchanged. F-2d recorded RED-then-reverted in the PR body.
- Macro tape: test_dash_macro.py (family names/order VOL-CRYPTO/RATES/FX/FUTURES,
  slot count MACRO_ROW_2 7->12 incl. 5Y/EURUSD/USDCAD/NG; VOL-CRYPTO ETH),
  test_dashboard_renderer_macro_tape.py (family order + stacked cell string),
  test_dashboard_renderer.py (stacked cell pin :3716-3717), four-across grid CSS
  assertion.
- Value formats: EURUSD/USDCAD .4f, NG .2f, ETH .0f/K, 5Y .2f (unit tests on
  _format_tape_value).
- Counts/universe: test_config.py universe pins (+5), test_contract_macro_drivers
  .py (_MACRO_DRIVER_SYMBOLS 10->15, optional 6->11), test_macro_tape_layout.py
  slot counts, test_phase1.py:80 driver note.
- R7: SPY copy assertions per state (concise single line; provenance retained).
- R8: market-context strip present/empty; compact footprint; semantics retained.
- R10: History order (SCOREBOARD before MARKET CONTROL) + visible-by-default;
  details-history region SHA re-pin.
- R11: tradables grid present iff Trend Structure degraded; absent when Trend
  renders live prices; market-structure region SHA re-pin; no universe symbol
  lost.
- Honesty (R-1..R-6 carry-over): no "live"/"real-time"/"now" beside a daily
  driver; as_of only from producer; stale daily -> "--".
- Goldens: dashboard_pre_gex_golden.html and dashboard_pre_a1c_chart_golden.html
  regenerate once (structure only, via _NEUTRAL_MACRO_PATH).

Fixtures: extend SECTION_STATE_CASES (tests/preview_fixtures.py) with: all-15
drivers present; each new driver missing (cell "--", payload passes); stale 5Y;
Trend-degraded state (grid fallback visible); Market Context empty (compact
strip); History populated.

--------------------------------------------------------------------------------
## 10. BROWSER ACCEPTANCE MATRIX (deliverable 10)
--------------------------------------------------------------------------------

Per-PRD evidence harness docs/prd_history/PRD-336.evidence/measure.py (CDP,
Emulation.setDeviceMetricsOverride, assert innerWidth/innerHeight - never
--window-size alone; deviceScaleFactor=2, mobile=True for 390px). Widths: 390px
(true device metrics) and 1366px. Rendered via render_dashboard_html over the
rich fixtures.

At 390px specifically prove:
- RATES four columns on ONE line; FX four columns on ONE line; FUTURES four
  columns on ONE line; VOL/CRYPTO three columns aligned to columns 1-3.
- document.scrollWidth <= innerWidth (0 horizontal overflow) on every fixture.
- values legible; labels do not collide; daily as_of line readable under 2Y/5Y.
- WATCHING unchanged and usable (byte-identical zone; no wrap artifacts).
- no interactive target below 44px (controlH >= 44).
- 0 console errors.
Also prove (both widths): SPY copy is shorter (fewer lines); Market Context strip
compact; History order/tightening (SCOREBOARD, MARKET CONTROL visible); Trend
presentation removes the duplicate grid in the live state and shows it only when
degraded; GEX safety/layout unchanged; no auto-refresh regression; interaction
persistence intact (GEX details + any toggle reload state).

--------------------------------------------------------------------------------
## 11. FILES + LOC CEILING (deliverable 2; ESTIMATED - Gate A sets the binding one)
--------------------------------------------------------------------------------

Production (<= 8 files):
  cuttingboard/config.py                       +18  (5 drivers x bounds/units/
                                                     source/universe)
  cuttingboard/contract.py                     +6   (5 keys + rates_5y daily)
  cuttingboard/contract_types.py               +5   (5 optional keys)
  cuttingboard/ingestion.py                    +12 / -4  (cosd bounding; DGS5
                                                     series; parser rename/generalize)
  cuttingboard/delivery/payload.py             +6   (whitelist +5; daily +1)
  cuttingboard/delivery/macro_tape_layout.py   +6   (4 slots + OIL display_label)
  cuttingboard/delivery/dashboard_renderer.py  +90 / -70  (families, grid CSS,
                                                     stacked cell, daily set, value
                                                     formats, R7 SPY copy, R8
                                                     strip, R10 history, R11 grid
                                                     conditional)
  cuttingboard/notifications/__init__.py       +4   (new rows via MACRO_ROW_2)
  production net                               ~ +73 / -78 (net roughly flat;
                                                     net-positive only from the
                                                     new drivers + carrier)
Tests (approx +260 / -40): NEW FRED carrier module (~120); fence extension (~40);
macro-tape/format/count updates (~60); R7/R8/R10/R11 renderer tests (~40); two
regenerated golden HTML files; PRD-336.evidence/measure.py + screenshots.
Docs/bookkeeping: docs/prd_history/PRD-336.md; docs/PRD_REGISTRY.md;
docs/prd_index.json; docs/SCHEMA_MAP.md (5 driver keys + DGS5 carrier + bounded
URL); docs/PROJECT_STATE.md; docs/DECISIONS.md (D-2/D-3/D-4 narrowings + the R12
future-GEX preference).

normalization.py and runtime/_constants.py are EXPECTED unchanged (the as_of
field and the fixture quote-field set already exist from PRD-335); verify at
implementation and add to FILES only if a change is actually required.

--------------------------------------------------------------------------------
## 12. FAIL / STOP LINES (deliverable 11)
--------------------------------------------------------------------------------

FAIL (a red test must catch each):
- Any new driver key present in any of the six vote sites (fence false-green).
- Payload generation fails on a valid new driver, or a whitelist rejects it, or
  the two whitelists' key sets drift.
- A futures price used/labelled as a 2Y/5Y yield; or a daily value shown as
  intraday/"live".
- A stale/missing/malformed/future daily (2Y/5Y) renders a number instead of "--".
- RATES/FX/FUTURES not four-across on one line at 390px, or any horizontal
  overflow, or a tap target < 44px, or a console error.
- WATCHING bytes change (R9 regression).
- Any provenance/freshness fact lost from the SPY copy (R7); any transition/
  invalidation semantic lost (R8); any SCOREBOARD/MARKET CONTROL semantic changed
  (R10); a state with NO ETF price surface, or a universe symbol dropped (R11).
- Any GEX arithmetic/admission/freshness/isolation change (R12); any frozen
  control SHA moves (SVG oracle, _STALENESS_JS_SHA, #today-zone, gex_reference).
- A regenerated golden diff touches a region other than #macro-tape /
  #spy-session(+#market-context) / #details-history / #market-structure.

STOP (stop and report to Helm; do not self-authorize past):
- R3: reliable bounded FRED retrieval needs materially larger architecture (new
  provider abstraction, freshness-model change) or the real cause is IP-level
  blocking bounding cannot fix. 2Y/5Y then render "--"; the rest ships.
- Any required edit to a decision-boundary file (scope breach).
- A shared CSS change cannot be scoped without regressing WATCHING (R9).
- The verdict shows a genuine semantic bug (verdict is otherwise frozen).
- Any new MATERIAL surface emerges (re-apply GOV-2 s1).

--------------------------------------------------------------------------------
## 13. OPEN QUESTIONS FOR INDEPENDENT REVIEW (deliverable 13 axes)
--------------------------------------------------------------------------------

A  Fence completeness. Does anything BESIDES the six named sites turn a macro
   driver key into a decision/explanation input (trade_explanation, invalidation,
   notifications text, data_quality)? Is the site-5 regime.py absence assertion
   the right closure, or is a broader symbol-level fence needed?
B  R3 honesty. Is bounding-as-mitigation (not proven fix) the right disposition
   given the failure is not reproducible? Is cosd = today-15d the right window
   (holiday density, DST, the 5-day staleness interaction)? Is a per-symbol
   two-request design correct vs one combined request?
C  Four-across legibility. Does the stacked cell + repeat(4) grid stay legible
   for the widest labels (EURUSD/USDCAD) and values (.4f FX, BTC "K") at 390px?
   Is un-muting the merged VOL/CRYPTO family (superseding D-4) the right call, or
   should BTC/ETH stay visually demoted?
D  Symbol correctness. EURUSD=X / USDCAD=X / NG=F / ETH-USD - any Yahoo quirk
   (inverse quote, session gaps, weekend prints, front-month roll) that makes a
   "--" or stale-looking cell likely? Are the PRICE_BOUNDS right?
E  R11 fallback. Are the four degraded Trend states the complete set where the
   grid must still show? Is there a state where Trend renders SOME rows but not
   all six, leaving a partial price gap the conditional misses?
F  R8 strip. Does folding Market Context into the SPY region risk a shared-class
   (.kv-grid) regression into WATCHING or the candidate card? Is the compact
   empty-strip wording honest (no implied data)?
G  Breadth (axis H from PRD-335). Nine effective changes across 8 production
   files - one PRD or two in disguise? Is the notification tape growth (MACRO_ROW_2
   +4 rows) in-charge, or should new slots live in a row the notification path
   does not consume?
H  Golden regen surface. Four regions re-pin (macro-tape, spy/market-context,
   details-history, market-structure). Is that the minimal authorized set, and
   is the neutralized-macro protocol sufficient to keep VALUES out of the diff?

--------------------------------------------------------------------------------
## 14. PROBE EVIDENCE (design-time de-risking, read-only)
--------------------------------------------------------------------------------

FRED (proven): GET fredgraph.csv?id=DGS2 -> http 200, 208776 bytes, 13114 rows,
~0.32s (UNBOUNDED, current code). GET ...?id=DGS2&cosd=2026-08-20 -> http 200,
198 bytes, 11 rows. GET ...?id=DGS5&cosd=2026-08-20 -> http 200, 198 bytes, 11
rows (DGS5 exists, parses identically: observation_date,DGS5). Bounding = ~1000x
payload reduction. A later repeated request timed out at 10.08s (intermittent /
throttle signature) - the carrier already sends UA "cuttingboard/1.0", so UA
blocking is excluded.

yfinance (INCONCLUSIVE from the design env): Ticker.fast_info returned last=None
for EURUSD=X, USDCAD=X, NG=F, ETH-USD AND for the known-good control JPY=X (which
ships in PRD-335 and works in production). None here is a sandbox/Yahoo-access
artifact, not a symbol-validity signal. Symbol resolution is therefore a REQUIRED
implementation-time verification gate, not a design-time proven fact.

STATUS: PROVISIONAL PLAN. No implementation authority. Held for fresh-context
independent review of PRD-336.md, then Dustin Gate A.
