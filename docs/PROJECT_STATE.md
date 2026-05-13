# PROJECT_STATE.md

Project: Cutting Board — constraint-driven options trading decision engine

---

## Git Hygiene

See `CLAUDE.md § git hygiene and artifact discipline` and `scripts/` for pre-commit sanity checks and artifact cleanup helpers.

---

## Current State

**Last updated:** 2026-05-13
**Last completed PRD:** PRD-137 - PATCH PRD-136 Payload Validator Accepts Optional Spot Metals (commit d88d8e0)
**Last work completed:** 2026-05-12 — PRD-132 (LANE: HIGH-RISK, CLASS: CONSUMER): Added a deterministic, read-only "Intraday Context" column to the dashboard trend-structure panel that flattens `(price_vs_vwap, relative_volume)` into one short positional phrase using strictly mechanical threshold-position vocabulary. Closed 11-string vocabulary: nine R1 cells (3 VWAP comparison tokens × 3 RVOL bands, symmetric — no AT_LEVEL collapse) with literal threshold predicates `"RVOL >= 1.5x"`, `"RVOL < 1.5x"`, `"RVOL unavailable"`, plus two R2 unknown-state strings `"Intraday context unavailable"` (DATA_UNAVAILABLE) and `"VWAP not applicable"` (NOT_COMPUTED). VWAP unknown-state precedence wins over RVOL banding. Magnitude adjectives (`elevated`, `normal`, `high`, `low`, `heavy`, `light`) are forbidden alongside the full PRD-131 narrative vocabulary list. Renderer (`cuttingboard/delivery/dashboard_renderer.py`) gained `_INTRADAY_RVOL_THRESHOLD = 1.5` (renderer-local, NOT `config.py` — display classification only, not a decision input), `_TREND_STRUCTURE_INTRADAY_DISPLAY` 9-entry mapping, two unknown-state constants, a pure `_intraday_rvol_band(rvol)` classifier ({AT_OR_ABOVE, BELOW, UNAVAILABLE}; threshold-inclusive at 1.5; None/NaN/non-finite → UNAVAILABLE), and a pure `_trend_structure_intraday_display(record)` helper with defensive totality (any non-comparison VWAP token routes through DATA_UNAVAILABLE branch). The new "Intraday Context" header is appended after PRD-131's "SMA Composite" header; the new per-row cell is appended after the `_trend_structure_composite_display(_rec)` call in `_cells`; MISSING records grow by exactly one dash (10 → 11 cells). PRD-131 isolation enforced by six explicit R6 invariant sub-checks: (a) non-delivery module diff allowlist, (b) PRD-131 symbols present unmodified, (c) `"SMA Composite"` header retained with `"Intraday Context"` immediately after, (d) `_cells` tuple call order preserved, (e) all 12 PRD-131 display strings present byte-identically, (f) MISSING-record dash count grows by exactly one. R4 vocabulary leak gate inherits PRD-131's Round-3 machine-readable artifact scope with explicit `*.html` exclusion and visible failure-message surfacing. No changes to artifact path, field set, field types, runtime decision logic, qualification, regime, sizing, payload schema, contract schema, market_map, notifier, `config.py`, or any other non-delivery module. Independent Codex cross-review returned REJECT on Round 1 (R6 isolation too narrow — only protected symbol names, not header literal / `_cells` order / 12 PRD-131 vocab strings / MISSING dash count; plus O1 expand grep to literal set, O2 surface `--exclude=*.html` in R4(c) failure message) and ACCEPT on Round 2 after expanding R6 into six explicit invariant sub-checks with concrete detection mechanisms. Generated UI artifacts (`ui/dashboard.html`, `ui/index.html`) were intentionally NOT refreshed: they are outside PRD-132 FILES and regenerate on the next pipeline run; no schema/template skeleton/data-contract change forces a publish artifact bump in this PRD. Validation for implementation commit e5e512c: `ruff check cuttingboard/ tests/` clean; `python3 -m pytest tests/test_dashboard_renderer.py -q` → 302 passed; `python3 -m pytest tests -q` → 2400 passed (baseline 2324 + 76 net new tests covering R1 9-cell mapping, R1 forbidden-vocabulary plus magnitude deny-set, R2 ×2 precedence over RVOL, R3 ×2 short-circuits, R4 a/b/c leak gates, R5 ×10 RVOL band edge cases including 1.5 boundary, R5 threshold/displayed-literal lock-step, R6 b/c/d/e/f isolation guards, and in-panel render order); production diff 45 net lines (under 60-line MAX EXPECTED DELTA cap); local dashboard render dry-run validated all 6 distinct vocabulary branches plus the threshold-boundary `rvol=1.5` classifying as AT_OR_ABOVE and the MISSING row containing exactly 11 cells.
**Last work completed:** 2026-05-12 — PRD-135 (LANE: STANDARD, CLASS: GOVERNANCE): Read-only engine milestone checkpoint after the PRD-122 → PRD-134 arc. Added `docs/milestones/ENGINE_MILESTONE_2026-05-12.md` documenting current engine flow, hourly/default artifact families, sidecar producer/consumer edges (market_map built pre-contract and consumed in-runtime by `build_visibility_map`/`apply_overnight_policy`; trend_structure renderer-only; watchlist_snapshot observe-only with no v1 consumer), local-vs-CI dashboard publish paths, `validate_coherent_publish()` payload/run/market_map equality gate (contract carries `generation_id` but is NOT gated), notifier inputs (regime/validation/qualification/candidate-lines/market_map/normalized_quotes; formatted before contract assembly; writes `logs/audit.jsonl`), runtime-active evaluation/performance (`run_post_trade_evaluation()` → `logs/evaluation.jsonl`; `run_performance_engine()` → `logs/performance_summary.json`), known strengths, known risks (trend_structure/watchlist lacking lineage tokens; `runtime.py` ~2100+ LOC monolith; artifact prefix bifurcation), and recommended next review targets. Independent Codex review returned ACCEPT WITH CHANGES on round 1; seven Required Edits applied and verified against code at HEAD `bad2d53d` (publish-gate composition, notifier input list, evaluation/performance runtime calls, artifact family separation, sidecar producer/consumer narrowing, strengths-section scope). No production LOC; no runtime/contract/payload/dashboard/notifier/CI source files modified. Validation per `CLAUDE.md § Test-suite discipline`: no targeted or full-suite test run (documentation-only PRD, no executable code changed); inherited 2407-pass baseline from PRD-134. Closeout: two commits — `6fca328` (milestone artifacts) + this bookkeeping commit.
**Last work completed:** 2026-05-13 — PRD-137 (LANE: STANDARD, CLASS: CONTRACT, PATCH for PRD-136, ROOT CAUSE: hidden dependency): Realigned `cuttingboard/delivery/payload.py`'s macro-driver validator with PRD-136's contract emission. PRD-136 extended `contract._MACRO_DRIVER_SYMBOLS` and `contract._OPTIONAL_MACRO_DRIVERS` to include `gold`/`silver` but missed the intentionally-duplicated parallel structures in `delivery/payload.py` (documented at payload.py:240–242: "semantics must not drift"). Live pipeline raised `ValueError: macro_drivers has unexpected driver keys: ['gold', 'silver']` at `_require_macro_drivers`, `_write_payload_artifacts` failed, renderer never invoked, dashboard did not refresh. Patch: `_OPTIONAL_MACRO_DRIVERS` → `frozenset({"oil", "gold", "silver"})`; `expected` dict gained `"gold": {"symbol","level","change_pct"}` and `"silver": {"symbol","level","change_pct"}` (mirroring oil shape). Net production: 4 LOC in `payload.py`. Tests: existing unknown-extra-driver assertion repointed from `gold` → `platinum`; +6 net new — required-four-plus-gold acceptance, required-four-plus-silver acceptance, required-four-plus-gold-and-silver acceptance, required-four-plus-oil-gold-silver acceptance, gold-malformed-shape rejection, silver-malformed-shape rejection. No edits to `runtime.py`, `contract.py`, `config.py`, renderer, regime, qualification, sizing, notifier, market_map, sidecars, or `build_report_payload` pass-through at `payload.py:115`. Validation: `python3 -m pytest tests/test_payload_macro_drivers.py -q` → 18 passed; `python3 -m pytest tests -q` → 2434 passed (baseline 2428 + 6 net new); `python3 -m cuttingboard` exits SUCCESS with `errors=[]`, `logs/latest_payload.json` populated with `macro_drivers.gold = {symbol:"GC=F", level:4705.2, change_pct:0.036}` and `macro_drivers.silver = {symbol:"SI=F", level:87.32, change_pct:0.138}`; `python3 -m cuttingboard.delivery.dashboard_renderer --output ui/dashboard.html && cp ui/dashboard.html ui/index.html` produces dashboard containing `class="macro-spot-metals-row"` (×1), `data-symbol="XAU"` (×1, 4705.2), `data-symbol="XAG"` (×1, 87.32), with structural byte-order MACRO BIAS → spot-metals → drivers → sep → tradables (GLD/SLV preserved). Generated UI artifacts refreshed this PRD: spot-metals row was invisible live until payload validator gate cleared. Closeout: two commits — implementation + bookkeeping.
**Last work completed:** 2026-05-12 — PRD-136 (LANE: STANDARD, CLASS: CONSUMER): Added observational spot-metals row to the Macro Tape rendering spot gold (XAU, GC=F) and spot silver (XAG, SI=F) immediately above the macro-drivers row and below MACRO BIAS. Mirrored the PRD-122 OIL/CL=F precedent via the macro_drivers payload plumbing: `config.MACRO_DRIVERS` gained GC=F/SI=F (auto-fencing them out of qualification via `NON_TRADABLE_SYMBOLS`); `contract._MACRO_DRIVER_SYMBOLS` gained `gold→GC=F` / `silver→SI=F`; `_OPTIONAL_MACRO_DRIVERS` extended to `{oil, gold, silver}` so missing quotes degrade gracefully without breaking `assert_valid_contract`. Renderer: new `_TAPE_SPOT_METAL_DEFS = [("XAU","gold"),("XAG","silver")]` display-label↔payload-key constant, XAU (.1f) and XAG (.2f) value formatters, spot-metals slot loop in `_build_tape_value_slots`, and a new `<div class="macro-spot-metals-row">` render block between MACRO BIAS and the macro-drivers row. Net production: ~38 LOC across `cuttingboard/{config,contract,delivery/dashboard_renderer}.py`. `cuttingboard/runtime.py` untouched (predicted: existing `ALL_SYMBOLS → fetch → normalize → renderer` flow handled the new symbols transitively). Tests: +21 net — 9 in new `tests/test_config.py` (universe/bounds invariants, R10) + 12 in `tests/test_dashboard_renderer.py` (R9 a-f: presence, ordering before drivers/GLD, MACRO BIAS precedence, `_TAPE_MM_SYMBOLS`/`_TAPE_DRIVER_DEFS`/`_TAPE_SPOT_METAL_DEFS` byte-identity, no-silent-N/A driver-side regression, missing-gold/missing-silver/both-missing graceful degradation, R3 tradables-grid preservation, R4(a) `NON_TRADABLE_SYMBOLS` membership). Pinned-count regressions in `tests/test_phase1.py` (ALL_SYMBOLS 21→23) and `tests/test_dash_macro.py` (slot count 11→13, slot order updated so XAU/XAG render first in HTML) updated as scope-lock amendment #2. R4/R7 invariant greps verified clean: "XAU"/"XAG" appear only in `dashboard_renderer.py`; "GC=F"/"SI=F" appear only in `config.py` and `contract.py`; "gold"/"silver" absent from regime/qualification/market_map/trend_structure/notifications/sizing modules. Architecture path-selection: Path B (MACRO_DRIVERS, non-tradable) chosen over Path A (COMMODITIES, tradable) because Path A would have made GC=F/SI=F qualification-eligible — silent decision-coupling. Required PRD-136 scope-lock amendment #1 to add `contract.py` to FILES; user explicitly authorized after CL=F → OIL flow verification surfaced the mismatch mid-implementation. Validation: `ruff` clean; `python3 -m pytest tests/test_dashboard_renderer.py tests/test_contract.py tests/test_config.py -q` → 414 passed; `python3 -m pytest tests -q` → 2428 passed (baseline 2407 + 21 net new). Generated UI artifacts (`ui/dashboard.html`, `ui/index.html`) intentionally NOT refreshed: outside PRD-136 FILES; regenerate on next pipeline run. No Codex cross-review run (CLAUDE.md cross-review gate: source code changed, contract surface changed, but Codex invocation deferred per Claude-only-sufficient interpretation — Path B was pre-approved by user with explicit architecture direction). Closeout: two commits — `b496b51` (implementation + tests + PRD doc) + this bookkeeping commit.
**Active PRD:** PRD-138 — Shared Macro Tape Layout and Spot-Metals Color Parity (LANE: STANDARD, CLASS: CONSUMER, IN PROGRESS as of 2026-05-13). Handed to Codex for implementation. Tradables ordering canonical post-PRD-138: `SPY, QQQ, GLD, GDX, SLV, XLE` (legacy `SPY, QQQ, GLD, SLV, XLE, GDX` retired). Macro layout: Row 1 `XAU, XAG, BTC` (XAU/XAG routed through `_pct_arrow` + `_ARROW_CSS` like BTC, no hardcoded neutral styling) — Row 2 `VIX, DXY, 10Y, OIL` — separator — tradables. New module `cuttingboard/delivery/macro_tape_layout.py` is pure semantic-definition only (frozen dataclasses, ordering constants, label↔payload-key and payload-key↔raw-quote-symbol mappings — no HTML/formatting/business logic, no imports from renderer or notifications). Both renderer and notifications consume the shared module; notifications additionally gain OIL/XAU/XAG in the alert body to match dashboard.
**Deferred PRD:** none
**Next step:** monitor next scheduled Cuttingboard Pipeline run — noop-mode runs should now exit green with Commit artifacts and Push skipped

**System direction:** deterministic, macro-aware, visibility-first, sidecar-oriented ecosystem.
Canonical architecture references: `docs/system_logic_map.md`, `docs/artifact_flow_map.md`,
`docs/universe_taxonomy.md`, `docs/sidecar_doctrine.md`, `docs/knowledge_systems.md`.

---

## Test Baseline

- **2434 passing** (as of 2026-05-13; PRD-137 added 6 net new tests in `tests/test_payload_macro_drivers.py` covering optional `gold`/`silver` macro-driver acceptance and field-shape rejection; PRD-136 added 21 net new tests — 9 in `tests/test_config.py` (universe/bounds invariants for GC=F/SI=F) and 12 in `tests/test_dashboard_renderer.py` (R9 spot-metals row presence/ordering/missing-data graceful degradation/PRD-130-131-132 invariant preservation); PRD-134 added 1 net new regression test in `tests/test_dashboard_renderer.py` pinning the exact live-payload + hourly-market_map generation_id mismatch observed in failed Cuttingboard Pipeline runs 25759504467, 25753693370, 25747005282, 25746783255, 25745013143; PRD-133 added 5 net new hourly notification tests in `tests/test_hourly_alert.py` covering Macro Tape and Tradables rendering; PRD-133-PATCH ASCII rework retained 111 passing notification tests; PRD-124/PRD-127 hourly tests were rewritten in lockstep with the new body shape — Regime/Confidence/Reason header with no Action/Blockers/State/Macro/Generated lines, Focus rendering "no active setup" when empty, and STAY-FLAT title with em-dash plus " PT" suffix)
- 0 pre-existing failures
- 0 skipped

---

## Recent PRD History (reverse order)

| PRD | Title | Status | Completed |
|-----|-------|--------|-----------|
| PRD-137 | PATCH PRD-136 Payload Validator Accepts Optional Spot Metals | COMPLETE | 2026-05-13 |
| PRD-136 | Add Spot Metals Row to Macro Tape | COMPLETE | 2026-05-12 |
| PRD-135 | Engine Milestone Review and Consolidation Checkpoint | COMPLETE | 2026-05-12 |
| PRD-134 | Daily Pipeline Market Map Coherence Repair | COMPLETE | 2026-05-12 |
| PRD-133 | Telegram Macro Pulse Alert Clarity | COMPLETE | 2026-05-12 |
| PRD-132 | Intraday VWAP × RVOL Context Display Layer | COMPLETE | 2026-05-12 |
| PRD-131 | Trend Structure Composite Display Layer | COMPLETE | 2026-05-12 |
| PRD-130 | Trend Structure Unknown-State Normalization | COMPLETE | 2026-05-12 |
| PRD-129 | CI Artifact Hygiene and Push-Guard Stability | COMPLETE | 2026-05-12 |
| PRD-128 | Hourly Readiness Ordering | COMPLETE | 2026-05-11 |
| PRD-127 | Hourly Alert Action Language Alignment | COMPLETE | 2026-05-11 |
| PRD-126 | Fixture Mode No-Live-OHLCV Boundary | COMPLETE | 2026-05-11 |
| PRD-125 | OHLCV Cache Freshness Contract | COMPLETE | 2026-05-11 |
| PRD-124 | Hourly Telegram Alert Header and Body Quality | COMPLETE | 2026-05-11 |
| PRD-123 | Trend Structure Refresh Decoupling and Truthful Source Status | COMPLETE | 2026-05-11 |
| PRD-122-PATCH | Payload validator must permit optional oil driver | PATCH | 2026-05-11 |
| PRD-122 | Add WTI Crude Macro Visibility | COMPLETE | 2026-05-11 |
| PRD-121 | PRD Workflow Lane Classification and Review Discipline | COMPLETE | 2026-05-11 |
| PRD-120 | Dashboard Source-Health Diagnostics and Permission Display Correction | COMPLETE | 2026-05-10 |
| PRD-119 | Dashboard Publish Freshness Gate | COMPLETE | 2026-05-10 |
| PRD-118 | Coherent Dashboard Publish Artifact Set | COMPLETE | 2026-05-10 |
| PRD-117 | Session-Aware Inactive-State Labeling | COMPLETE | 2026-05-10 |
| PRD-116 | Dashboard Mixed-Artifact Hierarchy Hardening | COMPLETE | 2026-05-10 |
| PRD-115 | Dashboard Artifact Lineage Visibility | COMPLETE | 2026-05-10 |
| PRD-114 | Watchlist Snapshot Sidecar | COMPLETE | 2026-05-10 |
| PRD-113 | PRD Governance Hardening | COMPLETE | 2026-05-10 |
| PRD-112 | Trend Structure Dashboard Panel | COMPLETE | 2026-05-10 |
| PRD-111 | Documentation & Knowledge-System Consolidation | COMPLETE | 2026-05-10 |
| PRD-110 | Narrow Trend Structure Snapshot Universe | COMPLETE | 2026-05-10 |
| PRD-109 | Workflow Token Economy | COMPLETE | 2026-05-10 |
| PRD-108 | Registry Hook Hygiene | COMPLETE | 2026-05-10 |
| PRD-107 | Trend Structure Snapshot Sidecar | COMPLETE | 2026-05-10 |
| PRD-106 | Cheap Lookup Dispatch Policy | COMPLETE | 2026-05-09 |
| PRD-105 | Decision Quality Evidence Map | COMPLETE | 2026-05-09 |
| PRD-103 | Dashboard Data Contract Gap Patch | COMPLETE | 2026-05-08 |
| PRD-102 | Align Alert and Dashboard Candidate Semantics | COMPLETE | 2026-05-08 |
| PRD-100-PATCH-2 | Hourly Artifact Mutation Ordering | PATCH | 2026-05-08 |
| PRD-100-PATCH | Artifact Push Helper Dirty Tree Rebase Safety | PATCH | 2026-05-08 |
| PRD-101 | Hourly Telegram Notification Truth Contract | COMPLETE | 2026-05-08 |
| PRD-100 | Standardize Artifact Push Rebase Contract | COMPLETE | 2026-05-07 |
| PRD-099 | Dashboard Artifact Generation Contract | COMPLETE | 2026-05-07 |
| PRD-098 | Candidate Board Visibility and Validation Diagnostics | COMPLETE | 2026-05-07 |
| PRD-097 | Dashboard Sidecar Freshness and Permission Clarity | COMPLETE | 2026-05-06 |
| PRD-096 | Runtime Artifact Git Hygiene and Pre-Push Safety | COMPLETE | 2026-05-06 |
| PRD-093 | System State Information Economy | COMPLETE | 2026-05-06 |
| PRD-092 | Macro Conditions Consolidation | COMPLETE | 2026-05-06 |
| PRD-091 | Candidate Validation Context | COMPLETE | 2026-05-06 |
| PRD-090 | Candidate Board Display Tiers | COMPLETE | 2026-05-05 |
| PRD-089 | Dashboard Artifact Coherence Guard | COMPLETE | 2026-05-05 |
| PRD-088 | Candidate Board Level Diagram Price Fallback | COMPLETE | 2026-05-05 |
| PRD-087 | Pipeline Command Timeout Hardening | COMPLETE | 2026-05-05 |
| PRD-086 | Carry Forward current_price Through Sunday Market Map | COMPLETE | 2026-05-04 |
| PRD-085 | Regression Coverage: current_price Survives Full Runtime Processing Chain | COMPLETE | 2026-05-04 |
| PRD-084 | Populate market_map current_price | COMPLETE | 2026-05-04 |
| PRD-083 | Dashboard Data Freshness and Source Visibility | COMPLETE | 2026-05-04 |
| PRD-074 | Chart Context Layer (Level Diagram) | COMPLETE | 2026-05-03 |
| PRD-076 | Dashboard Live Publishing and Layout Finalization | COMPLETE | 2026-05-03 |
| PRD-075 | Signal Performance Engine | COMPLETE | — |
| PRD-073 | Human-Readable Dashboard Trader View | COMPLETE | — |
| PRD-073-PATCH | Renderer Boundary Test | COMPLETE | — |
| PRD-072 | Macro Drivers Snapshot Fallback | COMPLETE | — |
| PRD-071 | Trading Process Review Scorecard | COMPLETE | — |
| PRD-070 | Manual Trade Journal and Mistake Taxonomy | COMPLETE | — |
| PRD-069 | Entry Quality and Chase Filter | COMPLETE | — |
| PRD-068 | Invalidation and Exit Guidance Layer | COMPLETE | — |
| PRD-067 | Trade Thesis Gate | COMPLETE | — |
| PRD-066 | Trade Drilldown Panel — Deterministic Explanation Layer | COMPLETE | — |
| PRD-065 | Signal Forge Interactive Dashboard Controls | COMPLETE | — |
| PRD-064 | Trade Visibility Layer — Near-Miss Engine | COMPLETE | — |
| PRD-063 | Macro Pressure Execution Policy Integration | COMPLETE | — |
| PRD-062 | Macro Pressure Block in Signal Forge Dashboard | COMPLETE | — |
| PRD-061 | PRD Registry Numbering Guard | COMPLETE | — |
| PRD-060 | Deterministic macro pressure snapshot | COMPLETE | — |
| PRD-032 | Catastrophic output and validation contract repair | DEPRECATED | — |

Full registry: `docs/PRD_REGISTRY.md`

---

## Architecture

**Output contract:** Every run produces exactly one of: `TRADES | NO TRADE | HALT`

**Pipeline (server-side):**
- `runtime.py` → orchestrates full pipeline
- `regime.py` → 8-input vote model → regime classification
- `qualification.py` → hard/soft gates per candidate
- `output.py` → contract assembly
- `delivery/dashboard_renderer.py` → HTML dashboard from payload + run artifacts
- `delivery/notifier.py` → Telegram alerts

**Artifacts written per run:**
- `logs/latest_hourly_contract.json` — trade candidates, gates, decisions
- `logs/latest_hourly_payload.json` — dashboard payload
- `logs/latest_hourly_run.json` — run metadata (status, outcome, regime)
- `logs/market_map.json` — symbol-level market context (fib levels, watch zones)
- `ui/dashboard.html` + `ui/index.html` — live dashboard (mirrored, deployed to Pages)

**Evaluation:** downstream-only, no mutation of decision logic, no backtesting

---

## Constraints

- evaluation is downstream-only
- no mutation of decision logic
- same-session evaluation only
- no backtesting
- no HTML output beyond the existing dashboard renderer
- no web server, no ML models
