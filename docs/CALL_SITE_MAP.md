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
| `_render_level_diagram` | Candidate-card SVG level ladder. Pinned geometry: SVG_H=110, LINE_W=160, yellow `#f5c518` anchor line. PRD-223: optional `contract_stop` draws the entry→stop risk zone (`#e05252`, `opacity="0.08"`, dashed STOP edge) |
| `_render_candidate_card` | Renders one candidate card; pair-gates the risk band (stop only draws when the contract entry is the anchor) |
| `_load_contract_entry_context` | Reads `logs/latest_hourly_contract.json` → entry map + stop map (finite, > 0) + alert candidates + generated_at |
| `_mcc_cell_display` / `_mcc_event_display` / `_mcc_location_display` | PRD-289 Market Control Card cell projection (value or typed unavailable token, never a default); block renders iff `sections["market_control_card"]` present |
| `main` / `write_dashboard` / `render_dashboard_html` (GEX seam) | Loads `logs/gex_snapshot.json` via `gex_card.load_gex_snapshot`, threads a tz-aware `now`, and emits `gex_card.render_fragment(...)` as a display-only card (PRD-309); `if frag:` guarded, so absent/stale/invalid emits nothing (byte-identical baseline) |
| `render_dashboard_html` (MARKET STATE seam) | Builds the resolved `GexCard` / `MovementCard` (renderer owns the artifact reads), then emits `market_state_panel.render_fragment(...)` immediately BEFORE `id="system-state"` (outside the PRD-219 protected region; PRD-312). Persistent five-axis panel — always emitted (no suppression). Also the arrow-cut site: the tradables daily-change arrow builder + span are removed here |

Note: the candidate board reads `market_map["symbols"]` directly, not payload
candidates. The level diagram's anchor/stop come from the contract overlay
(`trade_candidates[i]["entry"/"stop"]`), with current_price as the
anchor-only fallback.

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
| `_macro_row` | notifications/__init__.py | Notification tape line per slot; visible text is `slot.display` (`GC`/`SI`), level keyed on slot label |
| **FENCE** `_COMPONENT_FIELDS` | macro_pressure.py | macro_pressure components — excludes gold/silver (no decision read) |
| **FENCE** `MACRO_BIAS_DRIVERS` | macro_tape_layout.py | bias-vote drivers — excludes gold/silver (no decision read) |
| `TapeSlot.display` | macro_tape_layout.py | Visible label (`GC`/`SI` for metals); `label`/`data-symbol` stay `XAU`/`XAG` (PRD-211) |

---

## Usage rules

- Before a broad file scan, check this map for the owning file, then
  `grep -n "def <name>" <file>` to land on the current line.
- If a function is not here but is discovered during implementation, add it.
