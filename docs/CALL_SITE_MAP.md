# CALL_SITE_MAP.md — Key Function Boundaries

Reference for PRD reviewers and implementers. Use to locate injection points
without full-file reads. Update when new high-value boundaries are identified.
File + function granularity only — no line numbers (PRD-230: hand-maintained
line numbers were up to 59 lines stale; `grep -n "def <name>"` is free and
always current).

---

## runtime.py

| Function | Purpose |
|---|---|
| `cli_main` | Entry point; resolves command and runtime mode |
| `_run_pipeline` | Orchestrates regime → qualification → output → artifacts |
| `_resolve_effective_mode` | Handles live/sunday mode resolution |
| `_fetch_intraday_card_bars` | PRD-323 A1-P: the DISTINCT, patchable card-fetch reference (SEPARATE from the daily :1250 SPY fetch) → `fetch_intraday_session_bars(sym, timeout_seconds=25, retries=1)`; conftest autouse defaults it to a no-op so the whole `_execute_notify_run` cone is network-free (R3/R12) |
| `_intraday_symbol_bars` / `_write_intraday_bars_snapshot` | PRD-323 A1-P: whole-symbol validation (R4/R5) + atomic write of `logs/intraday_bars_snapshot.json` (`INTRADAY_BARS_PATH`, R6). Called only from the hourly seam inside the one R7 isolation boundary; no reader (A1-C lands the consumer) |

---

## cuttingboard/delivery/primary_selection.py (PRD-323 A1-P)

| Function | Purpose |
|---|---|
| `select_primary_card_symbol` | Renderer-free shared leaf; picks the canonical primary-card symbol = the renderer's inline chart-slot winner (PARITY-LOCKED via the `tests/test_primary_selection.py` cross-check against the real `_render_candidate_card`). Imports ONLY stdlib + `setup_chart`; MUST NOT import `dashboard_renderer` (R1). `_TIER_DEFS`/`_GRADE_ORDER` are temporarily duplicated here; A1-C removes the duplication when it rewires the renderer to this leaf |

---

## cuttingboard/contract.py

| Function | Purpose |
|---|---|
| `build_pipeline_output_contract` | Assembles and returns the canonical contract dict |

---

## cuttingboard/delivery/payload.py

| Function | Purpose |
|---|---|
| `build_report_payload` | Converts contract dict to dashboard payload dict |

---

## cuttingboard/spy_observation.py / cuttingboard/spy_state.py / cuttingboard/market_control_card.py (PRD-288/289)

| Function | Purpose |
|----------|---------|
| `build_spy_observation` | PRD-288 transient SPY session observation (freshness lifecycle + session VWAP + verbatim ORB); called from `_run_pipeline` on both halt and non-halt daily branches |
| `build_spy_state_outcome` | PRD-289 STATE acquisition seam: exact FRAME A → `list[Bar]` → `compute_intraday_state` READ-ONLY, packet-§5 catch boundary `(KeyError, ValueError, TypeError, InsufficientDataError)`; called only from `_run_pipeline` on eligible daily runs |
| `build_market_control_card` | PRD-289 sole producer of the seven-field card; reads `SpyObservation` + `SpyStateOutcome` + `system_state.permission` + `red_folder.load_schedule()` resolved at `run_at_utc` + invalidation/visibility maps + `outcome`; called only from `_run_pipeline` on eligible daily runs (never `MODE_SUNDAY`) |

## cuttingboard/delivery/dashboard_renderer.py

| Function | Purpose |
|---|---|
| `render_dashboard_html` | Renders full dashboard HTML from payload + run artifacts; carries `contract_entry_map` / `contract_stop_map` (PRD-223) |
| `_render_level_ladder` | PRD-321 R4: candidate-card COMPACT tiered level ladder (replaces the pre-PRD-321 `_render_level_diagram` SVG, whose SVG_H=110 / LINE_W=160 geometry is retired). HTML rows `.lvl-row` in `.lvl-ladder`, ordered high price → low; tier classes `.lvl-t1/.lvl-t2/.lvl-t3`; PRD-223 entry→stop span is the `.lvl-riskband` group (`.lvl-inrisk`, `.lvl-lockrisk` under PRD-304 lock) |
| `_render_setup_chart_block` | PRD-321 R3: emits the chart SVG + `bars through <as_of>` caption; wraps it in `<details class="chart-detail">` for every card after the highest-priority visible setup (ruling Q2) |
| `_load_price_bars_snapshot` / `_price_bars_caption` / `_price_bars_by_symbol` | PRD-321 R2: read-only `logs/price_bars_snapshot.json` loader (never raises) + source provenance caption + 5-calendar-day UTC age guard against `now` |
| `_render_candidate_card` | Renders one candidate card; pair-gates the risk band (stop only draws when the contract entry is the anchor); returns True when it took the single full-width chart slot |
| `_load_contract_entry_context` | Reads `logs/latest_hourly_contract.json` → entry map + stop map (finite, > 0) + alert candidates + generated_at |
| `_mcc_cell_display` / `_mcc_event_display` / `_mcc_location_display` | PRD-289 Market Control Card cell projection (value or typed unavailable token, never a default); block renders iff `sections["market_control_card"]` present |
| `main` / `write_dashboard` / `render_dashboard_html` (GEX seam) | Loads `logs/gex_snapshot.json` via `gex_card.load_gex_snapshot`, threads a tz-aware `now`, and emits `gex_card.render_fragment(...)` as a display-only card (PRD-309); `if frag:` guarded, so absent/stale/invalid emits nothing (byte-identical baseline) |
| `render_dashboard_html` (MARKET STATE seam) | Builds the resolved `GexCard` / `MovementCard` (renderer owns the artifact reads), then emits `market_state_panel.render_fragment(...)` immediately BEFORE `id="system-state"` (outside the PRD-219 protected region; PRD-312). Persistent five-axis panel — always emitted (no suppression). Also the arrow-cut site: the tradables daily-change arrow builder + span are removed here |

Note: the candidate board reads `market_map["symbols"]` directly, not payload
candidates. The chart/ladder anchor and stop come from the contract overlay
(`trade_candidates[i]["entry"/"stop"]`), with current_price as the
anchor-only fallback.

## cuttingboard/delivery/setup_chart.py

| Function | Purpose |
|---|---|
| `render_setup_chart_svg` | PRD-321 R1: the ONLY public entry point — pure, deterministic bars+levels → inline SVG. Fixed closed tier map (`TIER2_TYPES`, `TIER3_TYPES`); Tier 3 draws only inside the price domain and never widens the y-scale; returns `""` when there is nothing honest to draw. No I/O, no clock, no randomness, no `cuttingboard.*` import. Called only from `dashboard_renderer._render_candidate_card` |

---

## cuttingboard/delivery/gex_card.py

| Function | Purpose |
|---|---|
| `load_gex_snapshot` | Soft loader for `logs/gex_snapshot.json` (mirrors `_load_trend_structure_snapshot`; never raises; `None` on missing/malformed/non-dict) |
| `build_gex_card` | Pure model builder (clock injected); validates the D5a admissibility domain + freshness; returns `GexCard` or `None` to suppress |
| `render_gex_card_html` / `render_fragment` | Pure HTML fragment (empty string suppresses). All GEX arithmetic/validation live here; the renderer only loads and emits (PRD-309 R17/R20) |

## cuttingboard/delivery/market_state_panel.py

| Function | Purpose |
|---|---|
| `render_fragment` | Pure builder for the PRD-312 five-axis MARKET STATE block (ENVIRONMENT / PERMISSION / POSITIONING / PARTICIPATION / EVENT RISK). Takes the renderer's resolved carriers (regime, permission, run clock, `GexCard`/`MovementCard` objects, red-folder view) — reads NO raw artifact (keeps `gex_card` the sole `gex_snapshot` reader). Always renders exactly five rows; each is a value or honest `unavailable` with its own provenance. No global as-of, no score/verdict/INTRADAY |
| `_positioning` / `_participation` | Reuse the existing GEX / Movement semantics from the resolved card objects; POSITIONING preserves the configured-assumption + ~15m Cboe qualifiers, PARTICIPATION never claims 12/12 while any symbol is n/a |

---

## cuttingboard/output.py

| Function | Purpose |
|---|---|
| `build_notification_message` | Formats Telegram alert title and body from contract |

---

## Macro-tape metals (gold/silver) surface — PRD-211

The `gold`/`silver` macro_drivers are **display-only** (front-month futures
`GC=F`/`SI=F`), fenced from every decision path. Producer → display call graph:

| Function / symbol | File | Purpose |
|---|---|---|
| `_build_macro_drivers` | contract.py | Producer; builds `macro_drivers` per driver. Optional drivers (`oil`/`gold`/`silver`, set in `_OPTIONAL_MACRO_DRIVERS`) **silently skip** on fetch failure (`continue`) → key absent (write is FRESH, so absence renders `N/A`, not a stale value) |
| `_write_macro_snapshot` | runtime/__init__.py | Writes `logs/macro_drivers_snapshot.json` (FRESH, atomic). Renderer fallback fires only when the **whole** macro_drivers dict is empty (all-or-nothing), never per-key |
| `_build_tape_slots` / `_build_tape_value_slots` | dashboard_renderer.py | Render the tape arrow/value per slot; absent driver key → `N/A` (per-key `.get`) |
| `_format_tape_value` | dashboard_renderer.py | Value formatting dispatch, keyed on slot **label** (`XAU`→.1f, `XAG`→.2f) |
| `_tape_trend_summary` | dashboard_renderer.py | PRD-322 R1. Pure `(ts_records, ts_health)` → `(text, data-derivation)` for the TAPE TREND band. Only `trend_alignment ∈ {BULLISH,BEARISH,MIXED}` rows enter the denominator; all-computed reproduces the pre-PRD-322 `"N of 6 bullish"` / `bullish-row-count` byte-for-byte, every degraded branch is `trend-health`. Sole TAPE-side consumer of `_ts_health` |
| `_build_trend_chips` | dashboard_renderer.py | PRD-322 R4. Pure `ts_records` → six `(symbol, alignment, sma_50, sma_200, vwap, css_class)` rows in `config.TREND_STRUCTURE_SYMBOLS` order. Tokens come only from `_TS_ALIGN_ABBR`, `_trend_structure_composite_display` (split on the ` 50 ` window boundary) and the closed `_TAPE_VWAP_GLYPH` set; a non-computed alignment yields symbol + `—` only. Enumeration only — no breadth metric |
| `_pressure_note` | dashboard_renderer.py | PRD-322 R2. Pure `_build_pressure_snapshot` dict → the TAPE `zone-note`, through the closed four-state `_TAPE_PRESSURE_DISPLAY` map. **FENCE**: never reads `overall_pressure`; `None` → `"Pressure unavailable"` |
| `_macro_row` | notifications/__init__.py | Notification tape line per slot; visible text is `slot.display` (`GC`/`SI`), level keyed on slot label |
| **FENCE** `_COMPONENT_FIELDS` | macro_pressure.py | macro_pressure components — excludes gold/silver (no decision read) |
| **FENCE** `MACRO_BIAS_DRIVERS` | macro_tape_layout.py | bias-vote drivers — excludes gold/silver (no decision read) |
| `TapeSlot.display` | macro_tape_layout.py | Visible label (`GC`/`SI` for metals); `label`/`data-symbol` stay `XAU`/`XAG` (PRD-211) |

---

## Usage rules

- Before a broad file scan, check this map for the owning file, then
  `grep -n "def <name>" <file>` to land on the current line.
- If a function is not here but is discovered during implementation, add it.
