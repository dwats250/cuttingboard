# PROJECT_STATE.md

Project: Cutting Board — constraint-driven options trading decision engine

---

## Git Hygiene

See `CLAUDE.md § git hygiene and artifact discipline` and `scripts/` for pre-commit sanity checks and artifact cleanup helpers.

---

## Current State

**Last updated:** 2026-05-12
**Last completed PRD:** PRD-132 - Intraday VWAP × RVOL Context Display Layer (commit e5e512c)
**Last work completed:** 2026-05-12 — PRD-132 (LANE: HIGH-RISK, CLASS: CONSUMER): Added a deterministic, read-only "Intraday Context" column to the dashboard trend-structure panel that flattens `(price_vs_vwap, relative_volume)` into one short positional phrase using strictly mechanical threshold-position vocabulary. Closed 11-string vocabulary: nine R1 cells (3 VWAP comparison tokens × 3 RVOL bands, symmetric — no AT_LEVEL collapse) with literal threshold predicates `"RVOL >= 1.5x"`, `"RVOL < 1.5x"`, `"RVOL unavailable"`, plus two R2 unknown-state strings `"Intraday context unavailable"` (DATA_UNAVAILABLE) and `"VWAP not applicable"` (NOT_COMPUTED). VWAP unknown-state precedence wins over RVOL banding. Magnitude adjectives (`elevated`, `normal`, `high`, `low`, `heavy`, `light`) are forbidden alongside the full PRD-131 narrative vocabulary list. Renderer (`cuttingboard/delivery/dashboard_renderer.py`) gained `_INTRADAY_RVOL_THRESHOLD = 1.5` (renderer-local, NOT `config.py` — display classification only, not a decision input), `_TREND_STRUCTURE_INTRADAY_DISPLAY` 9-entry mapping, two unknown-state constants, a pure `_intraday_rvol_band(rvol)` classifier ({AT_OR_ABOVE, BELOW, UNAVAILABLE}; threshold-inclusive at 1.5; None/NaN/non-finite → UNAVAILABLE), and a pure `_trend_structure_intraday_display(record)` helper with defensive totality (any non-comparison VWAP token routes through DATA_UNAVAILABLE branch). The new "Intraday Context" header is appended after PRD-131's "SMA Composite" header; the new per-row cell is appended after the `_trend_structure_composite_display(_rec)` call in `_cells`; MISSING records grow by exactly one dash (10 → 11 cells). PRD-131 isolation enforced by six explicit R6 invariant sub-checks: (a) non-delivery module diff allowlist, (b) PRD-131 symbols present unmodified, (c) `"SMA Composite"` header retained with `"Intraday Context"` immediately after, (d) `_cells` tuple call order preserved, (e) all 12 PRD-131 display strings present byte-identically, (f) MISSING-record dash count grows by exactly one. R4 vocabulary leak gate inherits PRD-131's Round-3 machine-readable artifact scope with explicit `*.html` exclusion and visible failure-message surfacing. No changes to artifact path, field set, field types, runtime decision logic, qualification, regime, sizing, payload schema, contract schema, market_map, notifier, `config.py`, or any other non-delivery module. Independent Codex cross-review returned REJECT on Round 1 (R6 isolation too narrow — only protected symbol names, not header literal / `_cells` order / 12 PRD-131 vocab strings / MISSING dash count; plus O1 expand grep to literal set, O2 surface `--exclude=*.html` in R4(c) failure message) and ACCEPT on Round 2 after expanding R6 into six explicit invariant sub-checks with concrete detection mechanisms. Generated UI artifacts (`ui/dashboard.html`, `ui/index.html`) were intentionally NOT refreshed: they are outside PRD-132 FILES and regenerate on the next pipeline run; no schema/template skeleton/data-contract change forces a publish artifact bump in this PRD. Validation for implementation commit e5e512c: `ruff check cuttingboard/ tests/` clean; `python3 -m pytest tests/test_dashboard_renderer.py -q` → 302 passed; `python3 -m pytest tests -q` → 2400 passed (baseline 2324 + 76 net new tests covering R1 9-cell mapping, R1 forbidden-vocabulary plus magnitude deny-set, R2 ×2 precedence over RVOL, R3 ×2 short-circuits, R4 a/b/c leak gates, R5 ×10 RVOL band edge cases including 1.5 boundary, R5 threshold/displayed-literal lock-step, R6 b/c/d/e/f isolation guards, and in-panel render order); production diff 45 net lines (under 60-line MAX EXPECTED DELTA cap); local dashboard render dry-run validated all 6 distinct vocabulary branches plus the threshold-boundary `rvol=1.5` classifying as AT_OR_ABOVE and the MISSING row containing exactly 11 cells.
**Active PRD:** none
**Deferred PRD:** none

**System direction:** deterministic, macro-aware, visibility-first, sidecar-oriented ecosystem.
Canonical architecture references: `docs/system_logic_map.md`, `docs/artifact_flow_map.md`,
`docs/universe_taxonomy.md`, `docs/sidecar_doctrine.md`, `docs/knowledge_systems.md`.

---

## Test Baseline

- **2400 passing** (as of 2026-05-12; PRD-132 added 76 net new tests in `tests/test_dashboard_renderer.py` covering R1 9-cell intraday mapping, R1 forbidden-vocabulary plus magnitude deny-set, R2 ×2 VWAP unknown-state precedence over RVOL, R3 ×2 short-circuits, R4 a/b/c leak gates with `*.html` exclusion, R5 RVOL band classifier edge cases including the 1.5 boundary, R5 threshold/displayed-literal lock-step, R6 b/c/d/e/f PRD-131 isolation guards, and in-panel render order)
- 0 pre-existing failures
- 0 skipped

---

## Recent PRD History (reverse order)

| PRD | Title | Status | Completed |
|-----|-------|--------|-----------|
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
