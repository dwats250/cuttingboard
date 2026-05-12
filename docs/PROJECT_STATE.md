# PROJECT_STATE.md

Project: Cutting Board — constraint-driven options trading decision engine

---

## Git Hygiene

See `CLAUDE.md § git hygiene and artifact discipline` and `scripts/` for pre-commit sanity checks and artifact cleanup helpers.

---

## Current State

**Last updated:** 2026-05-12
**Last completed PRD:** PRD-130 - Trend Structure Unknown-State Normalization (commit d01327c)
**Last work completed:** 2026-05-12 — PRD-130 (LANE: HIGH-RISK, CLASS: SIDECAR): Replaced the legacy `"UNKNOWN"` emission across `cuttingboard/trend_structure.py` state fields (`price_vs_vwap`, `price_vs_sma_50`, `price_vs_sma_200`, `trend_alignment`, `entry_context`) with five deterministic, condition-specific tokens: `AT_LEVEL` (successful equality comparison), `INSUFFICIENT_HISTORY` (valid close series but too short for the SMA window), `DATA_UNAVAILABLE` (None / empty / missing-`Close` / all-NaN inputs), `NOT_COMPUTED` (intentional computation boundary — VWAP on non-intraday/daily bars), plus the renderer-only `SESSION_UNAVAILABLE` branch. Architecture: `_cmp()` is now a pure comparison primitive returning `Optional[str]` (None sentinel for missing inputs); callers (`_resolve_vwap_field`, `_resolve_sma_field`) own causality routing — the runtime/renderer semantic partition is preserved (runtime owns data-state, renderer owns session/presentation semantics). Renderer (`cuttingboard/delivery/dashboard_renderer.py`) gained a `_TREND_STRUCTURE_STATE_DISPLAY` mapping translating the four runtime tokens into compact operator-readable text ("AT LEVEL", "INSUFFICIENT HISTORY", "DATA UNAVAILABLE", "NOT COMPUTED"); `AT_LEVEL` renders affirmatively, never as an unknown-glyph fallback. No changes to artifact path, field set, field types, numeric semantics, badge CSS classes, panel skeleton, runtime decision logic, qualification, regime, sizing, payload schema, contract schema, market_map, or notifier. Independent Codex cross-review returned REJECT twice (governance LANE misclassification STANDARD→HIGH-RISK due to `cuttingboard/trend_structure.py` being a SIDECAR HIGH-RISK FILE per CLASS Matrix; `_cmp()` causality ambiguity for equality and SMA-None routing; SMA `_close_series()` cause partition inaccuracy; post-amendment cleanup gaps) and ACCEPT on the third pass after surgical amendments. Generated UI artifacts (`ui/dashboard.html`, `ui/index.html`) were intentionally NOT refreshed: they are outside PRD-130 FILES and regenerate on the next pipeline run; no schema/template skeleton/data-contract change forces a publish artifact bump in this PRD. Validation for implementation commit d01327c: `ruff check cuttingboard/ tests/` clean; `python3 -m pytest tests/test_trend_structure.py -q` → 30 passed; `python3 -m pytest tests/test_dashboard_renderer.py -q` → 179 passed; `python3 -m pytest tests -q` → 2277 passed (baseline 2271 + 6 net new R2/R4 tests); `grep '"UNKNOWN"' cuttingboard/trend_structure.py` → zero return-site matches.
**Active PRD:** none
**Deferred PRD:** none

**System direction:** deterministic, macro-aware, visibility-first, sidecar-oriented ecosystem.
Canonical architecture references: `docs/system_logic_map.md`, `docs/artifact_flow_map.md`,
`docs/universe_taxonomy.md`, `docs/sidecar_doctrine.md`, `docs/knowledge_systems.md`.

---

## Test Baseline

- **2277 passing** (as of 2026-05-12; PRD-130 added 6 net new R2/R4 trend-structure normalization tests across `tests/test_trend_structure.py` and `tests/test_dashboard_renderer.py`)
- 0 pre-existing failures
- 0 skipped

---

## Recent PRD History (reverse order)

| PRD | Title | Status | Completed |
|-----|-------|--------|-----------|
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
