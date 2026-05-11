# PROJECT_STATE.md

Project: Cutting Board — constraint-driven options trading decision engine

---

## Git Hygiene

See `CLAUDE.md § git hygiene and artifact discipline` and `scripts/` for pre-commit sanity checks and artifact cleanup helpers.

---

## Current State

**Last updated:** 2026-05-11
**Last completed PRD:** PRD-123 - Trend Structure Refresh Decoupling and Truthful Source Status (commit 0b1ee7b)
**Last work completed:** 2026-05-11 — PRD-123: decoupled trend-structure sidecar refresh from hourly-notify gating. A new private helper `_refresh_trend_structure_sidecar(mode, normalized_quotes, history_by_symbol, generated_at)` in `cuttingboard/runtime.py` gates on `mode == MODE_LIVE` and delegates to `_write_trend_structure_snapshot`; `_run_pipeline` now calls it just before returning `PipelineResult`, inside a defense-in-depth `if mode == MODE_LIVE:` block. `PipelineResult` shape is unchanged — DataFrames stay local to `_run_pipeline`. Renderer `_trend_symbols_usable` tightened to require `data_status != "MISSING"` in addition to required-field presence — count now reflects usable data, not shape presence. `_trend_structure_source_health` precedence extended with `MARKET_CLOSED` (inactive_session + fresh snapshot + 0 usable) and `AWAITING_DATA` (active session + fresh snapshot + 0 usable); previous `FALLBACK` return removed; PRD-117 snapshot-None coherence preserved (`INACTIVE_SESSION` still wins over `MISSING` under inactive_session). Panel renders the human label `MARKET CLOSED — AWAITING INTRADAY DATA` plus `Last snapshot: <iso>` for the two new states. PRD-120 R14-7 test updated to assert `AWAITING_DATA` instead of `FALLBACK`. Six new tests in `tests/test_runtime_trend_structure_refresh.py` cover helper mode-gating + exception-swallow + static `_run_pipeline` integration; five new renderer tests cover all four health states + degraded-label invariants. Codex cross-review (ACCEPT WITH CHANGES) findings 1-3 applied before implementation. Live verification at 2026-05-11 02:07Z produced fresh 6-symbol snapshot and `SOURCE: OK` / `TREND SYMBOLS: 6/6` (intraday available at run time). Notification policy unchanged.
**Active PRD:** none
**Deferred PRD:** none

**System direction:** deterministic, macro-aware, visibility-first, sidecar-oriented ecosystem.
Canonical architecture references: `docs/system_logic_map.md`, `docs/artifact_flow_map.md`,
`docs/universe_taxonomy.md`, `docs/sidecar_doctrine.md`, `docs/knowledge_systems.md`.

---

## Test Baseline

- **2247 passing** (as of 2026-05-11; PRD-123 added 12 tests: 7 runtime, 5 renderer)
- 0 pre-existing failures
- 0 skipped

---

## Recent PRD History (reverse order)

| PRD | Title | Status | Completed |
|-----|-------|--------|-----------|
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
