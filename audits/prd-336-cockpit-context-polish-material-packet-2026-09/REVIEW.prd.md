# Fresh-context independent review — PRD-336 (Cockpit context polish)

Reviewer seat: Adversary / fresh-context independent review. Worktree
/tmp/cuttingboard-prd336 @ cf693992, read-only. Judgment built from PRD-336.md,
the PRD-336 PLAN packet, PRD-335 (predecessor), and the tree at this checkout.

## VERDICT: CHANGES-REQUIRED

One blocking finding (R11 partial-price-gap). Everything else is verified sound
or covered by RECOMMENDED (non-blocking) edits. The PRD is well-constructed,
honest about its uncertainties (R3), and its decision-authority fence is
correct and complete. The single blocking item is a spec gap in R11's
suppression predicate that would let a conforming implementation ship a
real regression from today's behaviour while passing R11's own FAIL line.

---

## OBSERVATIONAL-ONLY DETERMINATION: CONFIRMED

The five new drivers (rates_5y, eurusd, usdcad, natgas, ethereum) CANNOT reach
any decision. Independently verified the six vote sites are the complete set of
by-key/by-symbol decision reads:

1. macro_pressure._COMPONENT_KEYS (macro_pressure.py:18-23) — 4 keys only.
2. macro_pressure._COMPONENT_FIELDS (:25-30).
3. macro_pressure._classify_driver (:57-90; raises for unknown at :90).
4. macro_pressure aggregation list (:126-133; exactly 4 inputs:
   volatility/dollar/rates/bitcoin).
5. regime.py reads valid_quotes by SYMBOL (:162-164: DX-Y.NYB, ^TNX, BTC-USD)
   + raw_votes (:167-176: SPY/QQQ/IWM/VIX/DXY/TNX/BTC).
6. macro_tape_layout.MACRO_BIAS_DRIVERS (macro_tape_layout.py:99).

Grep of every macro_drivers read across cuttingboard/ (non-test): the ONLY
by-key decision consumer is macro_pressure (sites 1-4). regime consumes quotes
by symbol (site 5). All renderer reads are display-only:
- dashboard_renderer.py:2092-2095 reads dollar/rates/volatility/bitcoin by key
  to build a DISPLAY header-context string — not a decision, and it reads the
  four EXISTING keys, never the new keys.
- 3676/1755/1775/1820 are tape rendering; 1512/2056/2719/3656 are
  "MARKET MAP UNAVAILABLE" display guards.
No read in trade_explanation / invalidation / execution_policy / data_quality /
trade_thesis / primary_selection touches a macro-driver key or a new symbol.

New symbols (DGS5, EURUSD=X, USDCAD=X, NG=F, ETH-USD) collide with NONE of
regime's symbol read set. R13's added regime symbol-absence assertion is the
correct closure for site 5 (which the current fence checks only by key at
sites 1/2/6, not by symbol). Observational-only holds.

---

## VERIFICATION (symbols / lines / FILES / FAIL-lines / LANE)

Spot-checked > 8 named symbols; all present at this tree:
- macro_pressure._COMPONENT_KEYS / _COMPONENT_FIELDS / _classify_driver /
  aggregation list — present (macro_pressure.py:18-133). [OK]
- regime.py reads :162-164 + raw_votes :167-176. [OK]
- macro_tape_layout.MACRO_BIAS_DRIVERS :99. [OK]
- ingestion._fred_csv_url :441-442 (currently UNBOUNDED — no cosd, matches R3
  premise); _parse_fred_dgs2_csv :453-491 (currently positional parts[1], keyed
  by index not header — matches R3's stated need to generalize);
  _FRED_SERIES_BY_SYMBOL :434 = {"DGS2":"DGS2"}; _try_fred_quote catches parse
  ValueError at :529-532 -> RawQuote fetch_succeeded=False (fail-closed real). [OK]
- fence test _NEW_DRIVERS line 49 = ("rates_2y","rates_30y","usdjpy");
  _new_block symbol map line 73; guard-sync F-5 :362-369; F-4 :276-278;
  _full_macro_drivers :291-301; _quotes_with_new :331-336. [OK]
- contract._MACRO_DRIVER_SYMBOLS :50, _DAILY_MACRO_DRIVERS :70 ({rates_2y});
  contract_types._OPTIONAL_MACRO_DRIVERS :49; payload
  _MACRO_DRIVER_FIELD_WHITELIST :346 / _DAILY_MACRO_DRIVER_KEYS. [OK]
- Renderer: _MACRO_FAMILIES :323-336, _MUTED_MACRO_FAMILY :336, _macro_driver_cell
  :3669-3689, .macro-drivers-row :1038 (flex-wrap), dead .macro-tape-grid
  :1028-1029, tradables grid :3722-3733, Trend Structure :3786-3910, degraded
  branches :3794-3809, market-context card :3588-3598 (uses .kv-grid :3593),
  details-history :3917. [OK]
- R11 health vars (unhealthy_lineage :2707, inactive_session :2834, _ts_records
  :2865, _ts_health :2880) are all computed BEFORE the grid emission at :3722, so
  R11's conditional needs NO reorder and stays contained to the renderer. [OK]

Minor line drift (non-blocking): R10 cites SCOREBOARD :3991 / MARKET CONTROL
:3928; actual h2 MARKET CONTROL :3929, SCOREBOARD rows :3994. Symbols
unambiguous.

FILES completeness: 8 production files listed. normalization.py and
runtime/_constants.py correctly OMITTED — as_of threading (normalization :92,
:36) and the fixture optional-field set already ship from PRD-335, so no change.
No unlisted production edit is implied. notifications/__init__.py IS listed
(consumes MACRO_ROW_2 growth). LANE = HIGH-RISK (dashboard_renderer CONSUMER
lane-floor) and CLASS = CONSUMER are correct, consistent with PRD-335.

FAIL-line observability: R1/R2/R3/R13 FAIL lines are binary and observable
(browser matrix, new carrier test, fence RED test, golden diff). R11 FAIL line
is observable but INCOMPLETE — see REQUIRED-1.

---

## REQUIRED EDITS (blocking)

### REQUIRED-1 — R11 suppression predicate misses the partial-snapshot price gap
Tie: SCOPE line ("the live view loses no price"); R11 (PRD:303-315); FAIL line
:312-315; PLAN axis E (:633-635).

The Trade Vehicles grid and the Trend Structure Price column read from TWO
DIFFERENT sources:
- Grid: market_map["symbols"][sym]["current_price"]
  (_build_tape_value_slots, dashboard_renderer.py:1828-1834).
- Trend table: _ts_records[sym]["current_price"] (the trend_structure_snapshot),
  rendered at :3838; a symbol MISSING from _ts_records renders Price = "--"
  (:3835-3841, the `_rec is None` branch) while STILL reaching the table (the
  healthy `else` branch at :3808+).

R11 suppresses the grid whenever the Trend table "renders live per-symbol
prices," but the table can render with a HEALTHY lineage / active session /
_ts_records not None and yet be missing one or more of the six symbol records —
each such symbol shows "--" while market_map still holds its real price. In that
state the current build shows the real price via the grid; after R11 that price
is lost. R11's FAIL line only catches the TOTAL case ("NEITHER ... renders"), so
a conforming implementation can ship this partial gap and pass its own test.

Fix (choose one, and make the FAIL line observable for it):
(a) Also render the grid whenever any of the six TREND_STRUCTURE_SYMBOLS is
    absent from _ts_records (i.e. any Price cell would be "--"), not only under
    the four coarse degraded flags; OR
(b) Explicitly declare a per-symbol "--" in the table an accepted surface,
    delete the SCOPE "loses no price" claim, and rewrite R11's predicate/FAIL to
    the per-symbol level so the accepted behaviour is stated and testable.
Preferred: (a) — it keeps the D-3 invariant the PRD asserts. Add a fixture
(healthy lineage, partial _ts_records) to the R11 test set.

---

## RECOMMENDED EDITS (non-blocking)

- REC-1 (axis G, notification breadth): the four new slots enter MACRO_ROW_2,
  which notifications/__init__ consumes (+4 rows), growing the Discord/text macro
  tape. The charge targets the dashboard cockpit. Confirm Helm wants the new
  peripheral drivers in the notification tape, or route them to a dashboard-only
  slot row. Harmless either way, but it is scope the charge did not name.
- REC-2 (R3 parser): the existing parser is positional (parts[1]); for
  observation_date,DGS2 and observation_date,DGS5 the value is always column 1,
  so positional already works. R3's "key by header, not position" is a clarity/
  robustness nicety, not a correctness fix — state it as such so the implementer
  does not treat header-keying as load-bearing.
- REC-3 (R10 line refs): update SCOREBOARD/MARKET CONTROL citations to :3994 /
  :3929 to match the tree.
- REC-4 (R1 legibility): the widest cells (EURUSD/USDCAD label 6ch; .4f value
  "1.0823" 6ch; BTC "K") in ~81px stacked columns are plausible but unproven;
  R1's FAIL line already makes this browser-matrix-provable — keep the 390px
  true-device-metrics acceptance as the gate (measure.py), do not accept a
  desktop-only check.

---

## RISK-AXIS FINDINGS

(A) Fence completeness beyond the six sites — CLEAR. The six sites are the
    complete by-key/by-symbol decision surface (see determination). All other
    macro_drivers reads are display. R13's regime symbol-absence assertion
    correctly closes site 5 at the symbol level.

(B) R3 honesty — CLEAR. The "not deterministically reproducible / mitigation not
    proven fix" framing is honest and matches the code: UA is already sent
    (ingestion.py:448), the fail-closed net is real (parse ValueError caught at
    :529-532 -> fetch_succeeded=False -> "--"). Per-symbol two-request design
    (two bounded requests, NOT id=DGS2,DGS5) is the correct choice — a combined
    id request would couple the two series' failure and break the per-symbol
    never-raises isolation. R3-STOP escape and "no futures proxy" are sound.

(C) R1 four-across — CLEAR (provable at gate). repeat(4, minmax(0,1fr)) +
    stacked cell is sound and cannot force horizontal overflow (minmax floor 0);
    legibility is the open risk, gated by the 390px browser matrix. Removing
    _MUTED_MACRO_FAMILY loses only BTC's visual demotion (D-4 presentation),
    nothing semantic; Helm ruled the un-mute. See REC-4.

(D) R11 completeness — FINDING (blocking): a partial _ts_records under an
    otherwise-healthy Trend table leaves a per-symbol price gap the four coarse
    degraded states do not cover. See REQUIRED-1.

(E) R9 WATCHING freeze — CLEAR. R1 edits .macro-drivers-row (macro-tape-scoped,
    not shared with WATCHING). R8 recomposes the market-context card which uses
    the SHARED .kv-grid (:3593). The mitigation (scope via new class/child
    selector) plus the byte-identical #watching-zone FAIL line (golden-enforced)
    is sufficient — a global .kv-grid edit would be caught. Keep R8 off a global
    .kv-grid change.

(F) Breadth — FINDING (acceptable): 9 changes / 8 production files is at the
    upper bound of "one bounded PRD," but every item is CONSUMER/display-only or
    a display-only carrier fix, no item crosses a decision boundary (the fence
    guarantees it), and the "last pre-live pass" framing is cohesive. Not a
    two-in-disguise split. See REC-1 for the one out-of-cockpit ripple.

(G) Golden / frozen-control surface — CLEAR. The four authorized re-pin regions
    (macro-tape, spy/market-context, details-history, market-structure) map
    exactly to R1/R7+R8/R10/R11 and are minimal. Frozen controls (SVG oracle
    a1c_golden_embedded_svg_sha256, _STALENESS_JS_SHA, #today-zone, gex_reference
    _v1.json, #system-state, #watching-zone) are genuinely untouched by any
    requirement — no requirement edits the verdict, GEX, today-zone, or the SVG
    oracle. The neutralized-macro protocol (_NEUTRAL_MACRO_PATH) keeps values out
    of the diff.

---

## NET
Approve after REQUIRED-1 is folded into R11 (predicate + FAIL line + a partial-
snapshot fixture). The observational-only guarantee is independently confirmed;
the fence, LANE, FILES, and frozen-control surface are correct.

---

## AUTHOR CORRECTION-CYCLE DISPOSITION (added by the PRD author, post-review)

One correction cycle applied (charge: one cycle maximum). Reviewed revision was
PRD-336.md before this cycle; the corrected revision SHA-256 is recorded in the
packet README.

- REQUIRED-1 (R11 partial-price-gap) - RESOLVED. R11's predicate now suppresses
  the Trade Vehicles grid ONLY when the Trend table renders a finite live price
  for ALL SIX config.TREND_STRUCTURE_SYMBOLS (table not degraded AND every symbol
  present in _ts_records with a finite current_price); every other state (degraded
  OR any symbol absent) shows the grid. The R11 FAIL line is rewritten to the
  per-symbol level and requires a partial-snapshot fixture (some of the six
  symbols absent from _ts_records, grid still visible). SCOPE/PLAN synced.
- Non-blocking: notification-tape ripple recorded as an explicit GATE-A
  CONFIRMATION ITEM in PRD-336.md (default INCLUDED via MACRO_ROW_2, matching the
  PRD-335 precedent; Helm may rule cockpit-only). R3 header-keying kept as a
  clarity improvement. R10 line citations are grep-verified at cf693992
  (id="scoreboard" :3991, id="market-control-card" :3928); left as grep-truth.
- OBSERVATIONAL-ONLY = CONFIRMED by the independent review; carried into the PRD's
  GATE-A CONFIRMATION ITEMS block.

Author is the PRD author, not an independent reviewer. This disposition records
what changed; it is NOT a second independent review. Helm's Gate A remains the
authorization; a final second-model/fresh-context review may still be commissioned
per GOV-2 (see the packet README recommendation).
