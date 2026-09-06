# PRD-335 PROVISIONAL PLAN - Market Context Completion + Second Editorial Pass

STATUS: PROVISIONAL PACKET. Carries NO implementation authority. Every FILES /
LOC figure below is "ESTIMATED SURFACE - NOT YET APPROVED". Base: main
fa101cc68963ed1c9704f94c6f54a182bfc86bac (PRD-334 merged, PR #322).
Author: Fable 5.1 (planning lead, DESIGN mode). ASCII only.
REVISION: v2 - the ONE consolidated correction after Astra's CHANGES-REQUIRED
review of v1 (reviewed-packet SHA
154e013ca05ec628290589ff9c9a8fc5ba90e2494a62c423bacd259c130bb86a). Dispositions
in s12. No further design round; open items are Helm decisions (s3, list D).

All file:line citations are against the base above and were spot-verified in
this session unless marked [brief] (taken from the recon brief, not re-read).

--------------------------------------------------------------------------------
## 1. OBJECTIVE
--------------------------------------------------------------------------------

Complete the market-context observations the operator actually reads (RATES:
10Y + 30Y, FX: DXY + USDJPY) as DISPLAY-ONLY drivers behind the existing
oil/gold/silver vote fence, and make a second, strictly subtractive editorial
pass over the PRD-334 presentation: delete interpretation prose from TAPE, say
the verdict once, put the GEX reference's explanatory text behind its one
disclosure, and caption the tradables grid so futures and ETF trade vehicles
are visibly distinct. No decision semantics move; the pass nets out negative
in display prose and in production LOC.

--------------------------------------------------------------------------------
## 2. SCOPE
--------------------------------------------------------------------------------

IN SCOPE
- Register ^TYX (label "30Y") and JPY=X (label "USDJPY") as optional,
  display-only macro drivers via the five-step fence (brief A).
- Renderer-only TAPE editorial: family regroup VOLATILITY / RATES / FX /
  COMMODITIES, BTC demoted to a muted trailing row, MACRO BIAS + Risk votes +
  pressure-phrase prose deleted (engine untouched; state kept as data-*).
- Verdict dedup in #system-state: one verdict + one reason; raw state stays in
  data-* attributes.
- GEX reference: _GUIDE and _FOOTNOTE (and the NET* / 0DTE rows that the
  footnote explains) move INSIDE "Full GEX details".
- Keep the #macro-tape tradables grid and caption it as trade vehicles; the
  grid's deletion is a Helm decision (D-3), not a default.
- Update the INDEPENDENT payload whitelist delivery/payload.py:318-337
  (_require_macro_drivers) - a second producer-to-consumer guard that the
  contract guard does not cover (Astra finding 1).
- Decision-authority RED test for the new drivers (classification AND
  aggregation reach, with positive controls); pin/golden regeneration; static
  fixture + browser + notification acceptance.
- 2Y: STOP-and-flag for Helm with the Option A carrier spec attached (s5).

OUT OF SCOPE / MUST NOT CHANGE (charge, verbatim intent)
- TRADE/NO_TRADE/HALT semantics; regime classification; macro-pressure
  DECISION semantics (macro_pressure._COMPONENT_KEYS/_COMPONENT_FIELDS,
  execution_policy._apply_macro_pressure); ranking; qualification; grades;
  setup eligibility; primary setup selection; MANUAL_CHECK; SPY session
  calculations; A1 behavior; GEX arithmetic/admission/freshness; GEX provider
  acquisition; Cloudflare scheduling; trade automation.
- config.TREND_STRUCTURE_SYMBOLS (PRD-110) - advisory only, see s4 item 6.
- The trading universe: no symbol is removed from ALL_SYMBOLS / TRADABLES_ROW.
- REQUIRED_SYMBOLS / HALT_SYMBOLS (config.py:265 / :166): new drivers are
  optional; their fetch failure can never halt.
- The byte-frozen SVG oracle (setup_chart_legacy_oracle.json,
  a1c_golden_embedded_svg_sha256) and gex_reference_v1.json.
- Notification decision content (the notification macro tape gains the two
  new rows mechanically via MACRO_ROW_2; nothing else in notifications moves).

STOP CONDITIONS (charge s12, restated as tripwires for the implementer)
- Any edit to macro_pressure.py, execution_policy.py, invalidation.py,
  trade_thesis.py, trade_explanation.py -> STOP (decision-scoring boundary).
- Any new provider, API key, paid feed, or a 2Y path larger than the Option A
  carrier in s5 -> STOP and flag.
- ZT=F or any futures contract labelled as a yield -> STOP (never mislabel).
- A second PRD, a dashboard epic, a heatmap, a composite score, or reopening
  GEX acquisition -> STOP.
- A regenerated golden whose diff touches any region other than #macro-tape,
  #system-state, #gex-reference -> STOP (unexplained drift).

--------------------------------------------------------------------------------
## 3. MATERIALITY DECLARATION
--------------------------------------------------------------------------------

MATERIAL under GOV-2 s1. Triggers (each sufficient alone):
- T1: adds keys to a PERSISTED schema surface with MULTIPLE readers -
  macro_drivers -> logs/macro_drivers_snapshot.json (runtime/__init__.py:2827
  _write_macro_snapshot [brief]) -> contract guard (contract.py:675-696) ->
  dashboard_renderer + macro_tape_layout + notifications.
- T2: crosses >= 2 pipeline layers (config/contract, persistence,
  delivery/dashboard, notification).

Remaining upstream order that still owes before any build:
  1. Astra (Codex) adversarial review of THIS plan (axes A-H, s11)
  2. ONE consolidated Fable correction
  3. Codex exact-corrected-head confirmation
  4. DUSTIN design-direction ruling on the consolidated Helm-decision list:
       D-1  2Y fork: Option B (recommended) or Option A (s5)
       D-2  H1 history: leave (recommended) or move Market Control (item 5)
       D-3  tradables grid: keep captioned (DEFAULT) or delete accepting lost
            ETF price coverage in closed/inactive/unhealthy states (item 7)
       D-4  BTC presentation: muted trailing CRYPTO row (plan default) or
            removal from the visible tape (item 2)
       D-5  regime context line under STAY FLAT / OBSERVE ONLY: remove
            (data-regime only) or retain compactly (item 3)
       D-6  trend set: T-a keep PRD-110 six (recommended) / T-b / T-c (item 6)
     The plan proceeds on its stated defaults if Helm rules nothing else.
  5. Stage-0 PRD-335 authored from the frozen plan; fresh-context independent
     PRD review
  6. DUSTIN Gate A
  7. Separate post-Gate-A IMPLEMENT session (Opus); fresh-context impl review;
     Dustin merge.

LANE: STANDARD (MATERIAL removes MICRO; MATERIAL never promotes to HIGH-RISK).
Downgrade-prohibition check: no decision-semantics change, no persisted FIELD
shape change under Option B (only two more optional driver KEYS of the existing
shape), no new external source, no JS change. No independent trigger fires.
If Helm rules Option A in, the PRD author re-runs the lane matrix in
docs/PRD_PROCESS.md for "new external data carrier + new persisted field"
before assuming STANDARD still holds (do not pre-decide here).

--------------------------------------------------------------------------------
## 4. PER-ITEM DESIGN
--------------------------------------------------------------------------------

### Item 1 - RATES / FX completion (30Y + USDJPY now; 2Y per s5)

Current state
- Universe config.py:258 MACRO_DRIVERS (7 symbols); :265 REQUIRED_SYMBOLS and
  :166 HALT_SYMBOLS carry ^TNX only; PRICE_BOUNDS :317 "^TNX": (1.0, 8.0);
  SYMBOL_UNITS :332 "^TNX": "yield_pct"; SYMBOL_SOURCE_PRIORITY :287.
- contract.py:50 _MACRO_DRIVER_SYMBOLS (7 keys); contract_types.py:45
  _OPTIONAL_MACRO_DRIVERS = {oil, gold, silver} [brief].
- contract.py:551-583 _build_macro_drivers: optional driver absent -> skipped
  silently (:558-561); block = {symbol, level, change_pct} (+change_bps only for
  driver == "rates", :579-580).
- Guard contract.py:675-696: unexpected keys rejected (:680-681); per-block
  exact field set (:688-691).
- SECOND, INDEPENDENT guard (Astra finding 1, verified): delivery/payload.py:
  318-337 _require_macro_drivers hard-codes the seven driver keys with their
  field sets and raises "macro_drivers has unexpected driver keys" for any
  other key. runtime/__init__.py:2854-2863 runs assert_valid_payload before
  deliver_json / deliver_html and CATCHES the exception ("Payload artifact
  generation failed - contract artifacts unaffected", :2862-2863). Updating
  the contract guard alone therefore ships a run whose contract and snapshot
  succeed while the dashboard/JSON payload silently stops regenerating - a
  silent-fallback failure the PRD-198 invariants forbid.
- Layout macro_tape_layout.py:43-51 MACRO_ROW_2 = VIX, DXY, 10Y, OIL.
- Format dispatch keyed on slot label: dashboard_renderer.py:1736
  (`if symbol == "10Y": .2f`), notifications/__init__.py:81 (same).
- Ingestion is symbol-opaque (ingestion.py:87-116 fetch_quote -> yfinance).
- Probe evidence (this session, yfinance fast_info): JPY=X and USDJPY=X return
  the IDENTICAL quote (last 156.22, prev 156.12, currency JPY); ^TYX returns
  5.246 / prev 5.243 (yield points, same units as ^TNX 4.784).
- Units vocabulary config.py:329-334 SYMBOL_UNITS = {^VIX: index_level,
  DX-Y.NYB: index_level, ^TNX: yield_pct}, DEFAULT_UNITS = "usd_price".
  USDJPY is JPY per USD - neither an index level nor a USD price.
- Acquisition already fails loud on a missing/invalid previous close
  (ingestion.py:391-399, PRD-262) and normalization drops failed quotes
  (normalization.py:67-68), so a new optional driver with no usable previous
  close becomes an ABSENT key ("--" cell), never a fabricated 0.0 change.

Target
- Symbols: "^TYX" (30-year Treasury yield index) and "JPY=X". Decision: use
  JPY=X (Yahoo's canonical listing; USDJPY=X is an alias to the same quote).
  Display label "USDJPY" via TapeSlot.display_label - the same mechanism that
  shows GC for XAU (macro_tape_layout.py:16-25). data-symbol / label stays
  "USDJPY" (new slot, no legacy id to preserve).
- Driver keys: "rates_30y" -> "^TYX"; "usdjpy" -> "JPY=X". Block shape is the
  plain {symbol, level, change_pct}. Deliberately NO change_bps for 30Y: the
  only consumer of change_bps is macro_pressure (fenced), and the arrow uses
  change_pct (renderer :1718). Adding a field with no reader is not
  subtractive. (Astra axis A may challenge.)

Exact edits (Option B)
- config.py:258 MACRO_DRIVERS += ["^TYX", "JPY=X"] (ALL_SYMBOLS :264 derives
  from it, so fetch_all_quotes picks them up; NON_TRADABLE_SYMBOLS :259
  follows). PRICE_BOUNDS: "^TYX": (1.0, 8.0) yield points (mirror ^TNX, not a
  price bound); "JPY=X": (80.0, 250.0). SYMBOL_UNITS: "^TYX": "yield_pct";
  "JPY=X": NEW honest token "jpy_per_usd" (Astra finding 6: DXY's
  index_level would misstate the unit; usd_price would invert it). The
  implementer confirms NormalizedQuote.units is a free string with no enum
  consumer before adding the token (recon found none; verify at build).
  SYMBOL_SOURCE_PRIORITY: two explicit ["yfinance"] rows mirroring :287.
  REQUIRED_SYMBOLS and HALT_SYMBOLS: UNCHANGED.
- contract.py:50 _MACRO_DRIVER_SYMBOLS += rates_30y, usdjpy.
- contract_types.py:45 _OPTIONAL_MACRO_DRIVERS |= {rates_30y, usdjpy}.
- delivery/payload.py:321-329 `expected` gains "rates_30y" and "usdjpy" with
  field set {symbol, level, change_pct}. Better (subtractive, preferred if the
  implementer confirms no other reader of the literal dict): derive
  `expected` from contract._MACRO_DRIVER_SYMBOLS + the same rates-only
  change_bps rule, so the two guards cannot drift again; otherwise mirror the
  literal and add a sync test asserting set(payload expected) ==
  set(contract._MACRO_DRIVER_SYMBOLS).
- Producer-to-consumer inventory for macro_drivers (GOV-2 boundary reset,
  refreshed this revision): producer contract._build_macro_drivers -> readers
  (1) contract guard :675-696, (2) delivery/payload._require_macro_drivers
  :318-337 via runtime :2859 assert_valid_payload, (3) runtime
  _write_macro_snapshot -> logs/macro_drivers_snapshot.json -> renderer macro
  fallback, (4) dashboard_renderer tape/value/arrow loops :1715/:1757/:2712/
  :3634, (5) macro_pressure (aggregate, four fixed keys), (6) notifications
  (reads normalized quotes via MACRO_ROW_1/2, not macro_drivers). Astra
  confirmed no other direct driver-key reader (trade_explanation,
  invalidation, trade_thesis use AGGREGATE pressure). docs/SCHEMA_MAP.md is
  updated with this inventory as part of the change.
- macro_tape_layout.py:43-51 MACRO_ROW_2 slots: insert
  TapeSlot("30Y","rates_30y","^TYX") after 10Y and
  TapeSlot("USDJPY","usdjpy","JPY=X",display_label="USDJPY") after DXY.
  Appending to ROW_2 (not a new row) means zero loop edits in the renderer
  (:1715, :1757, :2712, :3634) and notifications (:108); missing-value
  fallback is "--" (renderer :1761). The notification tape gains two rows
  mechanically - this is the T2 layer crossing and is flagged in s11 axis H.
- Format: dashboard_renderer.py:1736 and notifications/__init__.py:81 replace
  `== "10Y"` with `in _YIELD_LABELS` where
  _YIELD_LABELS = frozenset({"2Y","10Y","30Y"}) lives in macro_tape_layout.py
  (one definition, both consumers). USDJPY takes each surface's default
  (renderer .2f -> "156.22"; notification .1f -> "156.2").
- runtime/__init__.py _write_macro_snapshot: NO edit expected (dumps the
  dict); implementer verifies the snapshot round-trips the two new keys.

Display-only guarantee
- NOT added to macro_pressure._COMPONENT_KEYS / _COMPONENT_FIELDS
  (macro_pressure.py:18-30) nor to MACRO_BIAS_CONTRA_CYCLICAL /
  MACRO_BIAS_PRO_CYCLICAL (macro_tape_layout.py:91-93). Enforced by the RED
  test in s7. The vote loop at renderer :2712 iterates rows but tallies only
  MACRO_BIAS_DRIVERS [brief :2700-2734]; verified by the s7 tally test.
- Optional => a failed ^TYX / JPY=X fetch yields an absent key, "--" in the
  cell, no halt, no contract failure, no payload failure (payload guard
  updated). Failed optional fetches are excluded at normalization
  (normalization.py:67-68) and so do not degrade data quality; a SUCCESSFUL
  but old optional quote is still subject to the global age check, exactly as
  CL=F is today - the new symbols inherit that precedent unchanged.
- Freshness is NOT certified per driver (Astra finding 4): fetched_at_utc is
  the fetch clock, not the observation time, so a weekend/holiday observation
  passes as freshly fetched for every driver today. The RATES family caption
  reads "selected maturities" (10Y/30Y are two points, not a curve), and no
  cell claims an observation time (s6).

### Item 2 - TAPE editorial suppression (renderer only)

Current state (dashboard_renderer.py)
- :3561-3582 MACRO BIAS headline + "Risk votes: n off / m on" tally (gated by
  integrator_suppress["macro_bias"]).
- :3584-3606 per-component pressure phrases ("VIX permits longs" ...) or
  "Macro pressure unavailable".
- Helpers: _PRESSURE_COMPONENT_LABELS :1782, _PRESSURE_DECISION_PHRASES :1824,
  _pressure_decision_phrase :1840; CSS .macro-bias :1051,:1065-1067,
  .macro-pressure-line :1086-1087, .macro-tally :1129; macro_bias_css
  assignments :2728-2734.
- Engine values long_votes / short_votes / macro_bias computed :2700-2734 also
  feed the integrator (Rule 3 "Mixed tape" candidate-board line) - KEEP.
- Families :323-328 (VOLATILITY / RATES-FX / COMMODITIES / CRYPTO), rendered
  :3636-3642 via label lookup with silent skip of unknown labels.

Target
- Delete :3561-3606 entirely (46 lines) and the three helpers + their CSS
  (approx 75 lines). Keep the :2700-2734 computation; drop only the
  macro_bias_css variable.
- Preserve machine state without prose: the #macro-tape div (:3555) gains
  data-macro-bias="{macro_bias}" data-risk-off="{short_votes}"
  data-risk-on="{long_votes}" data-macro-pressure="{overall_pressure or
  UNKNOWN}". Tests that today assert the tally arithmetic in prose
  (test_dash_macro.py:237, :388) move to these attributes, so the arithmetic
  guard survives the prose deletion.
- _MACRO_FAMILIES :323-328 becomes:
    ("VOLATILITY", ("VIX",), ""),
    ("RATES", ("2Y","10Y","30Y"), "selected maturities, yield %"),   # 2Y label silently skipped under Option B
    ("FX", ("DXY","USDJPY"), ""),
    ("COMMODITIES", ("XAU","XAG","OIL"), "front-month futures"),
    ("CRYPTO", ("BTC",), ""),
  plus _MACRO_MINOR_FAMILIES = frozenset({"CRYPTO"}) -> the family div gets an
  extra class "macro-family-minor" (muted color, smaller cap; ~2 CSS lines).
  BTC stays visible because bitcoin_pressure can still veto/resize a trade
  (execution_policy.py:292 [brief]) and trade_explanation may cite it; a
  driver with veto power must remain inspectable. Full removal from display is
  Helm decision D-4; the plan does not decide it.
- The per-cell markup (_macro_driver_cell :3617-3626) is unchanged.
- VISIBLE VETO REASON REQUIREMENT (Astra finding 5): the pressure phrases are
  in some states the only page-visible causal reason for a macro veto
  (RISK_OFF + LONG => block), and data-macro-pressure is inert to a human
  reader. Before the prose is deleted, the implementer pins a RISK_OFF /
  LONG-candidate veto fixture and asserts that a VISIBLE causal reason
  survives the deletion elsewhere on the page - the expected carrier is the
  ALERT WATCHLIST block_reason (dashboard_renderer.py:3195-3203 [Astra]),
  with the WHY line allowed to remain the generic "N setups gated". If the
  fixture shows NO surviving visible reason, that is a STOP back to Helm
  (retain one compact pressure line vs accept the loss), not a silent
  retention and not a silent deletion.

Display-only guarantee: no engine symbol is touched; the integrator still
receives macro_bias; the notification path is unaffected by this item.

### Item 3 - VERDICT dedup (#system-state)

Current state (dashboard_renderer.py :2947-3033; d2-seam pins at
tests/test_dashboard_d2_seam.py:64-75)
- Up to five lines: .decision-state word (:2947, data-raw-state);
  .sys-verdict sentence (:2949, data-raw-title / data-raw-permission);
  .sys-why (:3026); .sys-context "<Regime> regime" (:3029); optional
  "Kill switch active" (:3031); .sys-permission (:3033).
- _verdict_sentence :1978-2008 returns "No new trades permitted" for STAY FLAT
  and OBSERVE ONLY, "System halted" for HALT - each a paraphrase of the state
  word already shown above it. Fixture "stay_flat" today renders: STAY FLAT /
  No new trades permitted / WHY: no qualified setups / Risk-on regime (4 lines,
  two of which restate the first).

Target rule - exactly one verdict, exactly one reason, plus independent locks
  1. .decision-state word - always; now carries ALL three raw attributes
     (data-raw-state, data-raw-title, data-raw-permission) so machine state is
     unconditional.
  2. .sys-verdict - rendered ONLY when the sentence adds information the state
     word lacks: TRADE PERMITTED (directional verb / "Trades permitted") and
     STATE UNAVAILABLE with mixed artifacts ("Inputs out of sync").
     _verdict_sentence returns "" for STAY FLAT, OBSERVE ONLY, HALT and the
     generic unavailable case; the renderer omits the div when empty. The
     existing guard "never a direction verb under no-trade" survives as
     `== ""` (test_dash_verdict_translation.py:110,:142,:195,:207-208 re-pin).
  3. ONE reason line, first match wins for the visible line:
     WHY (when computed, :3025 condition unchanged) -> else operator-lock
     permission (config.OPERATOR_LOCK_PERMISSION, verbatim) -> else
     "<Regime> regime" (.sys-context).
  4. Independent locks stay as their own lines: .sys-permission when operator
     locked AND a WHY line was also rendered (two genuinely distinct reasons);
     "Kill switch active" always when set.
  5. The regime word is ALWAYS carried as data-regime on the #system-state
     block. Whether the visible "<Regime> regime" line is ALSO retained
     compactly when a WHY / permission line displaces it is Helm decision D-5
     (Astra finding 5: under STAY FLAT the regime word is otherwise visible
     nowhere in #system-state). Plan default pending D-5: remove.
- Resulting fixtures under the default: stay_flat = 2 lines (STAY FLAT /
  WHY: no qualified setups); locked = 2 (OBSERVE ONLY /
  operator-cannot-monitor); permitted = 2 (TRADE PERMITTED / Longs allowed +
  Risk-on regime); halt = 3 (HALT / WHY: operational halt / Kill switch
  active); mixed = 2. Under D-5 "retain": +1 compact line on stay_flat,
  locked, halt.
- _FORBIDDEN vocabulary guard (d2 seam :30) unchanged and still asserted.

Guarantee: no decision-state logic moves; only which already-computed strings
are printed. The regime helper, WHY computation (:2978-3017) and
OPERATOR_LOCK_PERMISSION text are untouched.

### Item 4 - GEX reference summary-first

Current state (gex_reference.py, verified :159-206)
- _render builds: heading :187, identity :188-190, kv-grid of ALL
  gex_card._core_rows :191-193 (MODEL NET*, LARGEST RAW-STRIKE |MODEL NET|,
  call wall, put wall, 0DTE), <details class="gex-full"> :200 wrapping only
  _profile_block :201, </details> :202, then _GUIDE :203 and _FOOTNOTE :204
  OUTSIDE the disclosure. Docstrings :5-6 and :210-211 still say "details"
  container (stale since PRD-334 R7).

Target (closed-by-default footprint = identity + three anchor rows + the
existing one-sentence head label at :170-171)
- Top level keeps: heading, scenario/instrument/observation-date line, source
  line, and three rows built locally with gex_card._row: LARGEST RAW-STRIKE
  |MODEL NET|, LARGEST CALL-CONTRACT MAGNITUDE STRIKE, LARGEST PUT-CONTRACT
  MAGNITUDE STRIKE.
- Inside <details class="gex-full">, in order: MODEL NET* row and 0DTE row
  (gex_card._kv), _profile_block, _GUIDE, _FOOTNOTE. Rationale: NET* carries
  the asterisk the footnote explains; they travel together, so no dangling
  asterisk sits above a hidden footnote.
- gex_card._core_rows is NOT edited (shared with the current card, PRD-309
  bytes frozen); gex_reference composes its rows from the already-imported
  gex_card._row/_kv/_fmt_net. No new imports (test_gex_isolation_ast stays
  green by construction).
- Fix the two stale docstrings (:5-6, :210-211) to say "section".
- Unchanged: _unavailable :177-179 (test_gex_reference.py:194 keeps asserting
  no "MODEL NET*" in the unavailable fragment), SYNTHETIC / SPX / "Observation
  date: none (synthetic)" identity, the single-disclosure rule (still exactly
  one <details>), gex_reference_v1.json, PRD-333 isolation.

### Item 5 - HISTORY audit

Current state [brief]: #details-history :3844 = MARKET CONTROL card :3855
(LOCATION/STATE/EVENT + CANDIDATE-IMPLICATION counts - current-state facts),
Changes Since Last Run :3866, Scoreboard :3918 (<= SCOREBOARD_LIMIT rows).
PRD-334 R6 deliberately split the Market Control card here (transition /
invalidation went to #market-context).

Target: NO code change by default. The only misplacement is the one R6 chose
one PRD ago under an explicit owner ruling (G2, recorded at
dashboard_renderer.py:3506-3509); re-litigating it silently would violate
the brief's caution. Raise as Helm decision D-2 (H1) with two options:
  H1-leave (recommended, 0 LOC): HISTORY = Market Control + run-delta +
  scoreboard, as R6 ruled.
  H1-move (~12 LOC move, no logic): relocate the Market Control card lines
  :3855-3861 to #market-context beside transition/invalidation; HISTORY becomes
  run-delta + scoreboard only.
Changes Since Last Run stays (it is compact and backward-looking).

### Item 6 - TREND STRUCTURE (advisory; PRD-110 collision - do not build)

Current state: config.py:278 TREND_STRUCTURE_SYMBOLS = SPY,QQQ,GDX,GLD,SLV,XLE
[brief]; rendered :3713-3775 as the "curated watch set" table with a Price
column (:3742, :3773). tests/test_trend_structure.py:414-439 pins the exact
6-tuple AND explicitly bans IWM [brief]. RSP is absent from ALL_SYMBOLS
(config.py:264: MACRO_DRIVERS + INDICES + COMMODITIES + HIGH_BETA; INDICES =
SPY,QQQ,IWM).

Charge assumption that is WRONG: "SPY/QQQ/RSP/IWM via existing equity path" -
IWM is fetched but ratified-banned from this table; RSP is not in the universe
at all (needs ALL_SYMBOLS + PRICE_BOUNDS + SOURCE_PRIORITY + market_map.py:20
PRIMARY_SYMBOLS + PRD-110 test rewrite). Neither is a low-risk drop-in.

Recommendation: constant UNCHANGED in PRD-335. Record the alternatives for a
Helm ruling that would explicitly reopen PRD-110:
  T-a  keep PRD-110 six (status quo; metals/energy tilt reflects the trading
       universe, not breadth).
  T-b  breadth set SPY / QQQ / IWM / RSP (equal-weight vs cap-weight + small
       caps; loses GDX/GLD/SLV/XLE context that the tradables grid deletion in
       item 7 also removes from TAPE - so T-b would leave the metals ETFs with
       no price surface except Market Movement).
  T-c  hybrid SPY / QQQ / IWM / GDX / XLE (drops GLD/SLV as near-duplicates of
       GC/SI; adds small caps; still a PRD-110 reopen).
Astra challenges representativeness (axis F). No composite, no score.

### Item 7 - GOLD / SILVER dedup (and the real duplicate)

Current state: GC/SI/OIL futures in the COMMODITIES family (:326, :3636),
then <div class="sep"> :3645 and the macro-tradables-grid :3651-3660 printing
SPY,QQQ,GLD,GDX,SLV,XLE label+price from market_map. Verified: those six are
EXACTLY config.TREND_STRUCTURE_SYMBOLS, whose table (:3760 loop, Price column
:3773) sits in the same #market-structure region a few lines below. The
tradables grid is therefore a pure duplicate of the Trend Structure Price
column, and it is also what makes GLD/SLV appear next to GC/SI.

Price-surface fact (Astra finding 3, verified): Market Movement renders
PERCENT chips only (movement_card.py:86-93 _chip, :126-129), never a price;
Trend Structure prints no rows under unhealthy-lineage / inactive-session
states (:3725-3733). So in those states the tradables grid is the ONLY
price surface for GLD/GDX/SLV/XLE. Symbol coverage is not price coverage;
v1's deletion default would have lost information.

Target (DEFAULT): keep the grid; make the distinction visually explicit
with two captions and no new data: the grid gets a family-style cap
"TRADE VEHICLES <span class=label>ETF last price</span>" (reusing
.macro-family-cap markup so it aligns with the families above), and the
COMMODITIES note becomes "front-month futures" (item 2). ~4 LOC. The sep
:3645 stays. TRADABLES_ROW and _build_tape_value_slots are untouched.
Helm decision D-3: delete the grid (:3644-3660 plus the tradables half of
_build_tape_value_slots, ~ -20 LOC) ONLY if Dustin explicitly accepts losing
the ETF price surface in closed/inactive/unhealthy states. Not a plan
default.

### Item 8 - Process

Fable authors this one plan -> Astra one adversarial pass (axes A-H) -> Fable
adjudicates once (one consolidated correction) -> Codex exact-head confirm ->
freeze -> Dustin design-direction ruling -> Stage-0 PRD + fresh-context PRD
review -> Gate A -> separate Opus IMPLEMENT session. No second design round;
disagreements that survive adjudication go to Dustin as the named decisions
D-1..D-6 (s3). Astra's pass and this adjudication are recorded in s12.

--------------------------------------------------------------------------------
## 5. THE 2Y DECISION FORK
--------------------------------------------------------------------------------

Facts that bound both options (verified): no non-yfinance source exists
(ingestion.py:96-101 warns and skips any source other than "yfinance");
RawQuote (ingestion.py:29-37) has fetched_at_utc = fetch clock time and no
observation date; _build_macro_drivers drops all provenance; the contract
guard rejects any extra per-block field (contract.py:691 exact-set assert);
freshness is global (FRESHNESS_SECONDS=300 from fetch clock [brief]) so a
daily observation fetched now reads FRESH trivially. Yahoo has no ^-series 2Y
yield; ZT=F is a futures price and is forbidden as a stand-in.

OPTION A - small daily carrier + minimal per-driver as-of plumbing
- Source: FRED series DGS2 via the public CSV endpoint
  (fredgraph.csv?id=DGS2), no key, no paid tier. Pseudo-symbol "DGS2" with
  SYMBOL_SOURCE_PRIORITY["DGS2"] = ["fred"] so it never reaches yf.Ticker;
  new branch `elif source == "fred"` in fetch_quote (ingestion.py:97-101), so
  the Sunday live-data guard (:75) and the never-raises contract are
  inherited. Carrier parses the last two non-"." rows: price = latest yield,
  pct_change_raw = (latest - prev) / prev, source="fred", as_of = row date.
  Staleness rule inside the carrier: as_of older than 5 calendar days ->
  fetch_succeeded=False, failure_reason "DGS2 as-of stale" (fail-loud; the
  optional driver then renders "--", never a stale number).
- Plumbing: RawQuote.as_of: Optional[date] = None; NormalizedQuote carries it
  (normalization.py [brief :25-89]); _build_macro_drivers adds "as_of":
  ISO date only when present; guard :688-691 allows {"as_of"} for
  _DAILY_MACRO_DRIVERS = {"rates_2y"} and asserts ISO-date string;
  snapshot dumps it; renderer _macro_driver_cell appends
  <span class="macro-tape-asof">Sep 4</span> when block.as_of exists;
  notification _macro_row appends " (Sep 4)". TapeSlot("2Y","rates_2y","DGS2")
  in MACRO_ROW_2 before 10Y; PRICE_BOUNDS "DGS2": (0.0, 8.0); SYMBOL_UNITS
  yield_pct; MACRO_DRIVERS += "DGS2"; optional.
- Estimated extra surface: production ~ +100..130 LOC across ingestion.py,
  normalization.py, contract.py, contract_types.py, config.py,
  macro_tape_layout.py, dashboard_renderer.py, notifications/__init__.py;
  tests ~ +130 (canned-CSV carrier tests incl. "." gaps, stale as-of, network
  failure; guard accept/reject; as-of marker present/absent; notification
  marker). Adds a NEW persisted field (schema-shape change, not just keys) and
  the repo's FIRST non-yfinance carrier with its own failure modes.

OPTION B - ship 30Y + USDJPY now; STOP-and-flag 2Y
- Everything in s4 item 1 as written. RATES family renders 10Y / 30Y (the
  "2Y" label in _MACRO_FAMILIES is skipped by the existing label lookup, or
  omitted until ruled - implementer's call, zero behavior difference).
- 2Y goes to Helm as a named STOP with this Option A spec attached as the
  ready-to-rule design. If Helm rules A-in before Gate A, the PRD absorbs it
  as an amendment within the same single PRD (charge: no multiple PRDs); if
  after, it is a Helm-commissioned follow-on.

RECOMMENDATION: OPTION B.
1. The charge names 2Y acquisition as its own STOP candidate; Option A is
   exactly the thing it warns about - not because the CSV fetch is big
   (~40 LOC) but because honest cadence needs a new schema FIELD threaded
   through six files and two display surfaces. It turns a subtractive
   editorial pass (net roughly -100 production LOC) into a net-positive
   ingestion feature and doubles the MATERIAL review surface.
2. Per-driver as-of is the right long-term fix for EVERY driver, not a 2Y
   bolt-on; it deserves its own design attention with the freshness model
   (validation.py) in scope, which this charge forbids reopening.
3. RATES with 10Y + 30Y is already honest and useful (10s30s slope visible);
   nothing is mislabelled and nothing daily is presented as intraday.
4. Option B keeps the fresh-context reviewers' attention on the risky part of
   this pass (verdict/TAPE deletions and pin regeneration) instead of on a
   new network carrier.

--------------------------------------------------------------------------------
## 6. MIXED-CADENCE HONESTY RULE (binding under either option)
--------------------------------------------------------------------------------

R-1  The renderer and the notification never print "live", "real-time", or
     "now" beside any driver cell. The block keeps the single existing page
     timestamp; no per-driver time is invented.
R-2  A driver whose observation cadence differs from the fetch cadence MUST
     carry an as-of DATE marker at its cell, sourced ONLY from a per-block
     as_of field written by the producer - never inferred by the renderer from
     symbol name, label, or family.
R-3  A block without as_of displays nothing extra, and the page makes NO
     claim about its observation time: fetched_at_utc is the fetch clock
     (ingestion.py:325,347 [brief]) and provenance is dropped at
     contract.py:574-580, so a weekend/holiday print passes as freshly
     fetched. Cells are "latest available observations with potentially
     different observation times" (this wording, or none, is the only
     permitted framing - e.g. as the tape's single help/label line); the
     renderer never asserts synchronization across cells (no "as of HH:MM" on
     a family caption) and never certifies observation freshness. RATES is
     captioned "selected maturities".
R-4  A daily observation older than the carrier's staleness window renders
     "--", never the stale number with a date.
R-5  Guards: a static test asserts none of the R-1 words appear inside
     #macro-tape or the notification macro block for the rich fixture; under
     Option A, a fixture with as_of -> marker present on exactly that cell and
     absent on all others; a fixture without -> no marker anywhere.
R-6  Missing / invalid previous close for a new driver (ingestion.py:391-399
     raises; normalization.py:67-68 drops) is exercised as an acceptance case:
     the driver key is absent, the cell reads "--", no 0.0 change is ever
     fabricated, and the payload guard accepts the absence.
Under Option B the R-1/R-5 static guard ships now so the rule is inherited by
whichever daily series arrives first.

--------------------------------------------------------------------------------
## 7. DECISION-AUTHORITY GUARANTEE + RED TEST
--------------------------------------------------------------------------------

New test module tests/test_prd335_display_only_fence.py (mirrors the
oil/gold/silver precedent in tests/test_contract_macro_drivers.py).

F-1 Fence membership (static): assert "rates_30y" and "usdjpy" (and "rates_2y"
    under A) are NOT in macro_pressure._COMPONENT_FIELDS, NOT in
    _COMPONENT_KEYS.values(), NOT in macro_tape_layout.MACRO_BIAS_DRIVERS; and
    ARE in contract_types._OPTIONAL_MACRO_DRIVERS and
    contract._MACRO_DRIVER_SYMBOLS.
Mechanism facts (Astra finding 2, verified): _COMPONENT_FIELDS governs only
container validation (macro_pressure.py:41-44) and the per-driver field
lookup (:61); classification iterates _COMPONENT_KEYS (:118-121); aggregation
hard-codes exactly four component values (:126-133). v1's "add rates_30y to
_COMPONENT_FIELDS" mutation therefore changes NOTHING - a false-green RED
test. The corrected tests reach both the classification step and the
aggregation step, and carry positive controls proving the harness can see a
vote.

F-2a Positive control (proves sensitivity): base = four voting drivers all
    NEUTRAL. Control variant flips two REAL voting drivers (volatility and
    dollar) to extreme RISK_OFF moves. Assert build_macro_pressure differs
    (overall RISK_OFF) AND execution_policy._apply_macro_pressure for a LONG
    candidate returns a DIFFERENT (blocked, size) result than base. If this
    control ever passes as equal, the fixture is too weak and the fence tests
    prove nothing.
F-2b Invariance per new driver (the fence): for EACH of rates_30y and usdjpy
    independently, and then both together, add the driver to base with the
    same extreme move used in F-2a. Assert build_macro_pressure(variant) ==
    build_macro_pressure(base) key-for-key, AND the exact result key set ==
    {volatility_pressure, dollar_pressure, rates_pressure, bitcoin_pressure,
    overall_pressure} (a new component key is RED here - classification
    reach), AND _apply_macro_pressure output is identical to base.
F-2c Aggregation reach (executable): monkeypatch macro_pressure._overall_
    pressure with a recording spy (the call at :126 resolves the module
    global at call time). Assert it is called exactly once with exactly the
    four component values in the fixed order. Any edit that feeds a fifth
    component into aggregation is RED here without touching source.
F-2d One-time semantic mutation demo (recorded in the PR body, then
    reverted): the implementer adds "rates_30y_pressure": "rates_30y" to
    _COMPONENT_KEYS, "rates_30y": "change_pct" to _COMPONENT_FIELDS, AND
    appends result["rates_30y_pressure"] to the aggregation list at :126-133.
    Expected RED set: F-2b key-set assert (classification), F-2b equality
    (overall flips on the extreme move), F-2c spy (five inputs), F-3 policy
    output. Recording all four failures is the evidence that the fence is
    load-bearing; a partial mutation that leaves any of them green is itself
    a finding.
F-3 Sizing invariance (end-to-end): feed base and each F-2b variant pressure
    dict through execution_policy._apply_macro_pressure for a LONG candidate
    and assert identical (blocked, size_multiplier); F-2a's control proves
    the policy path is sensitive to a real vote.
F-4 Display tally invariance: render the rich fixture with and without the new
    drivers; assert data-risk-off / data-risk-on / data-macro-bias on
    #macro-tape are byte-identical (the MACRO_BIAS_DRIVERS fence).
F-5 Guard round-trip, BOTH guards: contract guard (:675-696) AND
    delivery/payload._require_macro_drivers (:318-337) each accept a
    macro_drivers dict with the new keys present, accept their absence
    (optional), and still reject an unknown key. Plus an end-to-end delivery
    test: build_report_payload + assert_valid_payload on a contract carrying
    each new driver present AND absent succeeds (the runtime :2859 path); a
    guard-sync test asserts the payload whitelist key set equals
    set(contract._MACRO_DRIVER_SYMBOLS) so the two guards cannot drift.
Existing pins updated, not weakened: test_contract_macro_drivers.py:96-97
(count 7 -> 9, optional 3 -> 5), test_config.py:22-41 universe pins.

--------------------------------------------------------------------------------
## 8. TEST / FIXTURE / GOLDEN REGENERATION PLAN
--------------------------------------------------------------------------------

Regeneration discipline: all editorial edits land first, each with the
targeted unit tests green (commit per validation step); pins regenerate ONCE in
a final dedicated commit, whose golden HTML diff is reviewed region by region.
Diff outside #macro-tape / #system-state / #gex-reference => STOP (s2).
Controls that must NOT change (asserted before and after the regen commit):
  - a1c_golden_embedded_svg_sha256 (test_dashboard_renderer.py:4830) and
    tests/data/setup_chart_legacy_oracle.json (test_setup_chart.py:411) -
    the byte-frozen SVG oracle; no chart change is in scope.
  - _STALENESS_JS_SHA (test_dashboard_d2_seam.py:77) - no JS change.
  - _BASE 2nd slot (#today-zone SHA) for every fixture - verdict/TAPE/GEX
    edits are all outside #today-zone.
  - tests/test_trend_structure.py - constant untouched (Option B and item 6).
  - tests/data/gex_reference_v1.json and test_gex_card.py - untouched.

Regenerates, and why:
  (a) universe/count: test_config.py:22-41; test_contract_macro_drivers.py:
      96-97 (two new optional keys); test_macro_tape_layout.py (MACRO_ROW_2
      4 -> 6 slots, payload-key maps).
  (b) TAPE HTML: test_dash_macro.py:81 (family names/order), :97 slot count
      13 -> 15 (9 drivers + 6 tradables; 9 only under Helm D-3 deletion),
      :237 and :388 rewritten from prose to data-* attributes;
      test_dashboard_renderer_macro_tape.py:21 (family order);
      test_dash_core.py (1 prose ref); test_dashboard_renderer.py (4 prose
      refs). New: the RISK_OFF/LONG veto fixture asserting a visible causal
      reason survives (item 2).
  (b2) payload: tests for delivery/payload._require_macro_drivers and the
      end-to-end build_report_payload + assert_valid_payload path with each
      new driver present and absent; guard-sync test (s7 F-5).
  (c) verdict: test_dash_verdict_translation.py:110,:142,:195,:207-208 re-pin
      to ""; test_dashboard_d2_seam.py _R1_AUTHORITY :64-75 re-pinned to the
      new line sets in s4 item 3; _FORBIDDEN :30 unchanged.
  (d) GEX: test_gex_reference.py structure asserts (guide/footnote/NET*/0DTE
      inside <details>, three anchor rows outside, still exactly one
      <details>); :194 unchanged.
  (e) whole-page: tests/data/dashboard_pre_gex_golden.html and
      dashboard_pre_a1c_chart_golden.html regenerate under the PRD-334
      neutralized-macro protocol (_NEUTRAL_MACRO_PATH, test_dashboard_
      renderer.py:4767-4771 -> "NO LIVE MACRO DATA"); they change for
      STRUCTURE only (new family wrappers/cells with "--", grid caption,
      deleted prose, verdict lines, GEX reorder) - the protocol insulates VALUES, not
      shape. Frozen-region SHAs at :4810 re-pin EXCEPT the embedded-SVG SHA
      (control). test_dashboard_d2_seam.py _GOLDEN_BELOW_SEAM (2 SHAs) and
      _BASE slots 1 (below-seam), 3 (#system-state shape) and 4
      (#market-structure shape) for all 15 fixtures re-pin; slot 2 is the
      control.
  (f) notifications: MACRO_ROW_2 growth adds "30Y" and "USDJPY" rows to the
      notification macro tape - a DECLARED display change (notifications/
      __init__.py:105-114; a missing quote omits its row, :90-97). New
      acceptance tests: _macro_tape_block with both new quotes present (two
      extra rows, "30Y" formatted .2f, "USDJPY" .1f, 3-char padding intact)
      and with each absent (row omitted, no placeholder, no exception).
      Implementer greps tests/ for pinned notification tape text before
      touching the layout (none surfaced in this recon beyond
      test_macro_tape_layout.py and test_dashboard_renderer.py).
  (g) new: tests/test_prd335_display_only_fence.py (s7); the R-5 honesty guard
      (may live in test_dash_macro.py).
Fixtures: add two SECTION_STATE_CASES to the d2 seam (or a sibling fixture
module): "macro_new_drivers_missing" (base macro + 30Y/USDJPY absent) and,
under A only, "macro_daily_2y_stale". The rich fixture for static inspection
extends the existing macro snapshot fixture with the two new blocks.

--------------------------------------------------------------------------------
## 9. ACCEPTANCE
--------------------------------------------------------------------------------

Static rich-fixture inspection (render each to /tmp, headless Chrome using
DevTools device metrics and asserting innerWidth/innerHeight, never
--window-size alone):
  1. normal macro (all 9 drivers present)  -> RATES "selected maturities"
     10Y/30Y, FX DXY/USDJPY, COMMODITIES front-month futures, muted CRYPTO
     last (D-4 default), no prose lines, captioned TRADE VEHICLES grid (D-3
     default); JSON + HTML payload regenerated (payload guard passes).
  1b. missing previous close for 30Y and for USDJPY (R-6) -> key absent,
     "--", payload passes, no 0.0 fabricated.
  1c. RISK_OFF + LONG-candidate veto fixture -> a visible causal reason
     survives the prose deletion (item 2 requirement), else STOP.
  2. missing 2Y  (B: n/a by construction; A: cell "--", no as-of marker).
  3. stale/daily 2Y (A only: fresh -> marker "Sep 4"; stale -> "--").
  4. missing 30Y -> cell "--", family intact, data-risk-* unchanged vs 1.
  5. missing USDJPY -> same as 4 for FX.
  6. mixed freshness (A: marker on 2Y only; B: no marker anywhere; both: no
     R-1 word in #macro-tape).
  7. GEX reference present -> closed by default; visible = heading + 2
     identity lines + source + 3 anchor rows + head label; guide/footnote/NET*
     /0DTE/ladder appear only after opening.
  8. current GEX absent / present -> reference identical bytes in both;
     current card unchanged bytes vs main.
  9. populated candidate board / WATCHING with multiple setups -> verdict
     region shows exactly the s4 item 3 line set; integrator "Mixed tape"
     line (candidate board) still appears when Rule 3 fires.
Browser matrix (390px and 1366px): document.scrollWidth <= innerWidth on every
fixture (0 overflow); zero console errors; interaction persistence (open the
GEX details and any radio-tab selector, reload, state as the page defines it);
GEX closed-by-default concise summary; populated RATES family; WATCHING with
multiple setups readable without wrap artifacts; the TRADE VEHICLES caption
aligns with the family caps at 390px (aligned columns, no ragged wrap).
Notification acceptance: the rendered notification text for fixture 1 shows
the two new rows; for 1b the corresponding row is omitted. CI parity: the
full suite runs where truth is determined; local green is reported as
unverified.

--------------------------------------------------------------------------------
## 10. ESTIMATED FILES + LOC  (ESTIMATED SURFACE - NOT YET APPROVED)
--------------------------------------------------------------------------------

Option B production (approx, +added / -deleted):
  cuttingboard/config.py                         +8   / -0
  cuttingboard/contract.py                       +2   / -0
  cuttingboard/contract_types.py                 +1   / -1
  cuttingboard/delivery/macro_tape_layout.py     +4   / -0   (2 slots, _YIELD_LABELS)
  cuttingboard/delivery/payload.py               +4   / -0   (whitelist; or
                                                 +3/-9 if derived from contract)
  cuttingboard/delivery/dashboard_renderer.py    +42  / -155 (prose+helpers+CSS
                                                 -125, verdict +18/-10, grid
                                                 caption +4, families/attrs/
                                                 format/minor-css +20)
  cuttingboard/notifications/__init__.py         +2   / -1
  cuttingboard/delivery/gex_reference.py         +10  / -6
  runtime/__init__.py                            0 expected (verify)
  ---------------------------------------------------------------
  production net                                 ~ +73 / -163  (net ~ -90)
  (Helm D-3 deletion would add ~ -20; D-5 retain ~ +2.)
Tests:  tests/test_prd335_display_only_fence.py (+130 new: F-1..F-5 incl.
  positive control, per-driver variants, aggregation spy, both guards,
  end-to-end payload delivery, guard-sync); veto-reason fixture + notification
  acceptance (+40); updates in test_config, test_contract_macro_drivers,
  test_macro_tape_layout, test_dash_macro, test_dashboard_renderer_macro_tape,
  test_dash_core, test_dash_verdict_translation, test_dashboard_d2_seam,
  test_gex_reference, test_dashboard_renderer (+~120 / -~60); two
  regenerated golden HTML files.
Docs/bookkeeping: docs/prd_history/PRD-335.md (+ review artifacts),
  docs/PRD_REGISTRY.md, docs/prd_index.json, docs/SCHEMA_MAP.md
  (macro_drivers keys + the producer-to-consumer inventory incl. the payload
  guard), docs/CALL_SITE_MAP.md if it lists the macro guards,
  docs/DECISIONS.md (Helm rulings D-1..D-6 as ruled).
Option A adds: ingestion.py +55, normalization.py +6, contract.py +10,
  contract_types.py +3, config.py +6, layout +1, renderer +12, notifications
  +5 (~ +100..130 production) and ~ +130 tests; Option A total lands net
  positive (~ +40).

--------------------------------------------------------------------------------
## 11. OPEN QUESTIONS FOR ASTRA (adversarial axes)
--------------------------------------------------------------------------------

A  Rates-source correctness. Is JPY=X the right documented symbol given it
   is identical to USDJPY=X (probe evidence above) - any Yahoo quirk (JPY per
   USD vs USD per JPY, session gaps, weekend prints) that makes a "--" or a
   stale-looking FX cell likely? Is ^TYX bound (1.0, 8.0) right? Is
   omitting change_bps for 30Y a mistake for any reader? Does
   _compute_data_quality treat a failed optional symbol identically to CL=F?
B  Mixed-cadence honesty. Under Option B, does showing 10Y/30Y without 2Y
   mislead by omission? Under Option A, is a 5-calendar-day staleness window
   right for DGS2 (holidays), and is a date-only marker sufficient honesty?
C  Accidental decision-authority expansion. Does anything besides
   _COMPONENT_FIELDS / MACRO_BIAS_DRIVERS iterate macro_drivers by key
   (trade_explanation, notifications, invalidation) such that two new keys
   change any decision or explanation text? Is F-2's fixture strong enough
   that a fence breach is guaranteed RED, not coincidentally equal?
D  TAPE hierarchy. Is a muted trailing CRYPTO row the right demotion, or
   should BTC leave the tape entirely given its vote is already hidden by
   the prose deletion? Does deleting the pressure phrases remove the ONLY
   page-visible explanation of a macro veto (RISK_OFF + LONG => block), and
   is data-macro-pressure enough?
E  GEX default density. Are three anchor rows + identity the right closed
   footprint, or should "LARGEST RAW-STRIKE |MODEL NET|" also go inside
   (leaving only walls)? Does moving NET* inside weaken PRD-333's
   "unmistakably synthetic" reading in any way?
F  Trend-set representativeness. Challenge T-a/T-b/T-c; is there a breadth
   set that does NOT require reopening PRD-110? (Note IWM ban and RSP
   absence are ratified/structural facts, not preferences.)
G  Duplicated info. [ANSWERED in v2: Market Movement is percent-only, so the
   grid is the sole ETF price surface in closed/inactive/unhealthy states;
   captioned grid is the default, deletion is Helm D-3.] Remaining: is the
   two-caption distinction (front-month futures / TRADE VEHICLES ETF last
   price) sufficient, or is the GC-GLD adjacency still confusing at 390px?
   Regime-line visibility under STAY FLAT is Helm D-5.
H  Breadth of the pass. Nine items across seven production files: is this
   one PRD or two in disguise? Is the notification tape growth (two rows via
   MACRO_ROW_2) inside the charge, or should new slots live in a row the
   notification path does not consume? Should H1 be dropped from the packet
   entirely as R6-settled?

--------------------------------------------------------------------------------
## 12. ASTRA REVIEW DISPOSITIONS (GOV-2 durable disposition record)
--------------------------------------------------------------------------------

Reviewed packet: v1, SHA 154e013ca05ec628290589ff9c9a8fc5ba90e2494a62c423bacd259c130bb86a.
Astra verdict: CHANGES-REQUIRED. Fable adjudicated once; every finding was
spot-verified at the cited lines before disposition. This is the single
consolidated correction; no second design round.

| # | Axis | Finding (substance)                                   | Disposition          | Note |
|---|------|-------------------------------------------------------|----------------------|------|
| 1 | C/H  | Hidden consumer: payload.py:318-337 independently     | ACTIONED             | Verified; runtime :2862 swallows the failure. payload.py added to scope/FILES; both-guard + end-to-end delivery + guard-sync tests (s7 F-5); inventory refreshed (s4 item 1); SCHEMA_MAP update. |
|   |      | whitelists 7 keys; new keys break payload generation  |                      | |
| 2 | C    | F-2 mutation inert: _COMPONENT_FIELDS is validation   | ACTIONED             | Verified (:41-44, :61, :118-121, :126-133). s7 rewritten: positive control F-2a, per-driver F-2b with exact key set, aggregation spy F-2c, one-time full semantic mutation demo F-2d, F-3 sensitivity via control. |
|   |      | only; classification/aggregation untouched            |                      | |
| 3 | G    | Grid deletion loses ETF price surface; Market         | ACTIONED + HELM D-3  | Verified (movement_card.py:86-93 percent-only; renderer :3725-3733). Default flipped to captioned grid; deletion is Helm decision D-3 accepting the loss. Slot count 13->15. |
|   |      | Movement is percent-only                              |                      | |
| 4 | A/B  | Over-certified freshness ("by construction            | ACTIONED             | Claim deleted from R-3; "latest available observations with potentially different observation times" wording; RATES "selected maturities"; R-6 missing-prev-close case (ingestion :391-399 verified). |
|   |      | fetch-cadence"); fetch clock != observation time      |                      | |
| 5 | D/G  | data-* attrs inert to humans; prose deletion may       | ACTIONED (fixture)   | Veto-reason fixture requirement added with STOP if none survives; BTC stays inspectable. Regime-line removal -> Helm D-5; BTC removal -> Helm D-4 (not decided here, per orchestrator). |
|   |      | remove only visible veto reason; regime line lost     | + HELM D-4 / D-5     | |
| 6 | A    | Wrong unit token (index_level) for USDJPY             | ACTIONED             | Verified SYMBOL_UNITS :329-334. New token "jpy_per_usd"; implementer confirms units is enum-free. Astra dismissals ACCEPTED: ^TYX (1.0,8.0) sanity bound kept; no 30Y change_bps; failed optional fetches excluded at normalization :67-68 (stale-but-successful still under global age check) - text corrected accordingly. |
| 7 | E/F  | GEX anchors + identity outside disclosure OK;         | DISMISSED (validates)| No change. PRD-110 six + IWM ban + RSP absence confirmed by Astra; anchor-count left to Helm preference (not added as a decision - plan default stands). |
|   |      | PRD-110 six confirmed                                 |                      | |
| 8 | H    | Notification tape growth is a real declared change;   | ACTIONED             | Notification present/absent acceptance tests added (s8 f, s9). H1-leave retained as D-2 default, citing owner ruling G2 at :3506-3509. One bounded PRD under Option B confirmed defensible. |
|   |      | H1 revisits an owner ruling                           |                      | |

Net effect on the plan: scope +1 production file (payload.py); the RED test
is now load-bearing; the pass remains subtractive (net ~ -90 production LOC);
2Y carrier stays out (D-1 default Option B); six named Helm decisions.

END OF PLAN
