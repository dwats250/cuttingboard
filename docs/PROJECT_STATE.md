# PROJECT_STATE.md

Project: Cutting Board — constraint-driven options trading decision engine

---

## Git Hygiene

See `CLAUDE.md § git hygiene and artifact discipline` and `scripts/` for pre-commit sanity checks and artifact cleanup helpers.

---

## Current State

**Last updated:** 2026-05-12
**Last completed PRD:** PRD-131 - Trend Structure Composite Display Layer (commit 82e1415)
**Last work completed:** 2026-05-12 — PRD-131 (LANE: HIGH-RISK, CLASS: CONSUMER): Added a deterministic, read-only "SMA Composite" column to the dashboard trend-structure panel that flattens the two SMA comparison tokens (`price_vs_sma_50`, `price_vs_sma_200`) into one short positional phrase using strictly structural vocabulary. Closed 12-string vocabulary: nine comparison-token cells ("Above SMA50 and SMA200", "Above SMA50, below SMA200", "Below SMA50, above SMA200", "Below SMA50 and SMA200", "At SMA50, above SMA200", "At SMA50, below SMA200", "Above SMA50, at SMA200", "Below SMA50, at SMA200", "At SMA50 and SMA200") plus three unknown-state strings ("Structure unavailable", "SMA history insufficient", "Structure not computed") with explicit R2 precedence (DATA_UNAVAILABLE > INSUFFICIENT_HISTORY > NOT_COMPUTED). The `NOT_COMPUTED`-on-SMA slot is reserved-but-tested for future emitter expansion (`cuttingboard/trend_structure.py` does not currently emit it for SMA fields). VWAP is not consulted by the helper, is not in the vocabulary, and does not modify any composite display string — the raw `price_vs_vwap` cell already exists and intraday-context layering is deferred to a future PRD. Renderer (`cuttingboard/delivery/dashboard_renderer.py`) gained the `_TREND_STRUCTURE_COMPOSITE_DISPLAY` mapping, three unknown-state constants, a pure `_trend_structure_composite_display(record)` helper, one new "SMA Composite" header, and one new per-row cell at the existing render site. No existing column removed, reordered, or modified. MISSING records receive a dash. No changes to artifact path, field set, field types, runtime decision logic, qualification, regime, sizing, payload schema, contract schema, market_map, notifier, or any other non-delivery module. Independent Codex cross-review returned REJECT twice (R1: narrative vocabulary including "recovery attempt"/"pullback"/"inflection", LANE misclassification CONSUMER STANDARD→HIGH-RISK due to `dashboard_renderer.py` being a CONSUMER HIGH-RISK FILE per CLASS Matrix, "AT_LEVEL" mislabeled as inflection; R2: R4(c) over-broad `reports/` grep that would fail a valid local render to `reports/output/dashboard.html`) and ACCEPT on the third pass after restructuring the vocabulary to strictly positional phrasing, narrowing R4(c) to machine-readable artifact paths (`logs/**`, `reports/**/*.json|*.jsonl|*.txt|*.md|*.csv`) with explicit `*.html` exclusion, and renaming "Trend baseline forming" to "SMA history insufficient". Generated UI artifacts (`ui/dashboard.html`, `ui/index.html`) were intentionally NOT refreshed: they are outside PRD-131 FILES and regenerate on the next pipeline run; no schema/template skeleton/data-contract change forces a publish artifact bump in this PRD. Validation for implementation commit 82e1415: `ruff check cuttingboard/ tests/` clean; `python3 -m pytest tests/test_dashboard_renderer.py -q` → 226 passed; `python3 -m pytest tests -q` → 2324 passed (baseline 2277 + 47 net new PRD-131 tests covering R1 nine-cell mapping, R1 forbidden-vocabulary regex, R2 three precedence slots, R2 precedence ordering, R3 inactive-session and snapshot-absent short-circuits, R1/R5 in-panel render, and R4(a/b/c) leak gates); production diff 38 lines (under 60-line MAX EXPECTED DELTA cap). End-to-end CI verification: `Cuttingboard Pipeline` run 25731633181 GREEN on HEAD `fc8d714` (manual workflow_dispatch, 59s); push-triggered `Deploy to GitHub Pages` run on `fc8d714` GREEN.
**Active PRD:** none
**Deferred PRD:** none

**System direction:** deterministic, macro-aware, visibility-first, sidecar-oriented ecosystem.
Canonical architecture references: `docs/system_logic_map.md`, `docs/artifact_flow_map.md`,
`docs/universe_taxonomy.md`, `docs/sidecar_doctrine.md`, `docs/knowledge_systems.md`.

---

## Test Baseline

- **2324 passing** (as of 2026-05-12; PRD-131 added 47 net new tests in `tests/test_dashboard_renderer.py` covering R1 nine-cell composite mapping, R1 forbidden-vocabulary regex, R2 three precedence slots, R2 precedence ordering, R3 inactive-session and snapshot-absent short-circuits, R1/R5 in-panel render, and R4(a/b/c) vocabulary leak gates)
- 0 pre-existing failures
- 0 skipped

---

## Recent PRD History (reverse order)

| PRD | Title | Status | Completed |
|-----|-------|--------|-----------|
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
