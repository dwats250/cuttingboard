# Engine Milestone Checkpoint — 2026-05-12

**Governing PRD:** [PRD-135](../prd_history/PRD-135.md) — Engine Milestone Review and Consolidation Checkpoint
**Lane / Class:** STANDARD / GOVERNANCE
**Scope:** Read-only observational checkpoint. No runtime, contract, sidecar, renderer, notifier, CI, or source code change accompanies this document.

This milestone records the shape of the cuttingboard decision engine at the close of the PRD-122 → PRD-134 arc (WTI macro driver, sidecar boundary hardening, hourly alert language, CI artifact hygiene, dashboard display layers, daily market-map coherence repair). It is intended as a durable architecture reference, not a change proposal.

---

## Current Engine Flow

The hourly run is a single linear pipeline orchestrated from `cuttingboard/runtime.py`:

1. **CLI entry** — `cli_main()` (`runtime.py:264`) parses mode arguments and dispatches to `execute_run()`.
2. **Pipeline orchestrator** — `_run_pipeline()` (`runtime.py:686`) executes the fixed phase order:
   - **Input load:** raw quote fetch → normalization → validation.
   - **Regime computation:** 8-input vote model (`regime.py`) → `RISK_ON | RISK_OFF | NEUTRAL | CHAOTIC`.
   - **Qualification:** per-symbol hard/soft gates (`qualification.py`) → candidate trades, watchlist, rejections.
   - **Decision gates:** thesis, invalidation, entry-quality, chase-filter overlays.
   - **Sidecar build (in-runtime):** `build_market_map()` is called at `runtime.py:888`, **before** contract assembly. Its output is consumed in-runtime by `build_visibility_map(trade_decisions, market_map)` (`runtime.py:903`) and by `apply_overnight_policy(...)` (`runtime.py:966`). Trend structure (`trend_structure.py`) and watchlist (`watchlist_sidecar.py`) are written for downstream consumers.
   - **Contract assembly:** `build_pipeline_output_contract()` (`contract.py:59`, invoked at `runtime.py:928` and re-applied through `apply_overnight_policy` at `runtime.py:966`).
   - **Payload assembly:** `build_report_payload()` (`delivery/payload.py:21`).
   - **Artifact write:** `_write_hourly_artifacts()` writes the hourly JSON family to `logs/`; default-mode runs write the non-prefixed `latest_*` family.
   - **Evaluation and performance (downstream-only):** `run_post_trade_evaluation()` (`runtime.py:1030`, from `cuttingboard/evaluation.py`) reads prior `logs/audit.jsonl` records and appends `logs/evaluation.jsonl`; `run_performance_engine()` (`runtime.py:1031`, from `cuttingboard/performance_engine.py`) reads evaluation output and writes `logs/performance_summary.json`. Neither feeds back into the contract or decision pipeline.
   - **Report render:** markdown render → optional HTML render via `delivery/html_renderer.py`.
   - **Notification (notify-only runs):** `_execute_notify_run()` (`runtime.py:437`) → `format_hourly_notification()` (`runtime.py:541`) → Telegram transport. The hourly notification is formatted **before** the hourly contract/payload are assembled (`runtime.py:540-605`).
3. **Output contract** — every run resolves to exactly one of `TRADES | NO TRADE | HALT`, enforced at the contract layer rather than synthesized at the renderer.

Workflow drivers in `.github/workflows/` (`cuttingboard.yml`, `hourly_alert.yml`, `pages.yml`, `telegram_debug.yml`) wrap the same `runtime.py` entry; mode flags select live, fixture, sunday, or notify-only behavior.

---

## Major Artifacts

The pipeline produces two distinct artifact families plus append-only audit/evaluation streams. Hourly runs and default runs write to different latest-pointer filenames; full catalogue and flow edges are in `docs/artifact_flow_map.md`.

**Hourly artifact family** (`logs/latest_hourly_*`) — written by `_write_hourly_artifacts()` and consumed by the CI publish path:

| Artifact | Producer | Purpose |
|---|---|---|
| `logs/latest_hourly_run.json` | `_write_hourly_artifacts()` | Run-level metadata: `generation_id`, status, outcome, regime summary, notification state. |
| `logs/latest_hourly_contract.json` | `build_pipeline_output_contract()` | Full decision contract: `system_state`, `market_context`, `trade_candidates`, `rejections`, `audit_summary`, `correlation`, `regime`, `macro_drivers`. |
| `logs/latest_hourly_payload.json` | `build_report_payload()` | Renderer/notifier-facing canonical form: `summary`, `sections`, `meta.generation_id`. |

**Default (non-hourly) latest family** (`logs/latest_*`) — written by default-mode runs and read by the local dashboard renderer when no hourly override is supplied:

| Artifact | Producer | Purpose |
|---|---|---|
| `logs/latest_run.json` | runtime default-mode writer | Default run metadata. |
| `logs/latest_payload.json` | runtime default-mode writer | Default render payload. |
| `logs/latest_contract.json` | runtime default-mode writer | Default contract snapshot. |

**Sidecar artifacts:**

| Artifact | Producer | Purpose |
|---|---|---|
| `logs/market_map.json` | `build_market_map()` + `market_map_lifecycle.inject_lifecycle()` | Symbol-level grade/setup_state lifecycle, watch zones, `removed_symbols`, `generation_id`. |
| `logs/trend_structure_snapshot.json` | `build_trend_structure_snapshot()` | Per-symbol VWAP / SMA-50 / SMA-200 / relative-volume context, `data_status`, `reason`. |
| `logs/watchlist_snapshot.json` | `build_watchlist_snapshot()` | Curated watchlist with `sector_theme`, `watch_reason`, `current_price`. Observe-only; no v1 consumer per `docs/artifact_flow_map.md:118-124`. |
| `logs/macro_drivers_snapshot.json` | macro driver writer | Macro tape values for dashboard / notifier consumption. |

**Append-only / evaluation streams:**

| Artifact | Producer | Purpose |
|---|---|---|
| `logs/audit.jsonl` | `cuttingboard/audit.py` (`write_notification_audit()` and related) | Append-only audit records, including notification transport events written by `send_notification()` / `send_telegram()` (`cuttingboard/output.py:700-733`, `cuttingboard/audit.py:242-307`). |
| `logs/evaluation.jsonl` | `run_post_trade_evaluation()` (`cuttingboard/evaluation.py:37-71`) | Per-decision evaluation records derived from prior audit entries. |
| `logs/performance_summary.json` | `run_performance_engine()` (`cuttingboard/performance_engine.py`) | Aggregated performance summary derived from evaluation stream. |

**Rendered outputs:**

| Artifact | Producer | Purpose |
|---|---|---|
| `reports/output/hourly_report.html` | `delivery/html_renderer.deliver_html()` | Per-run HTML report. |
| `reports/output/dashboard.html` | `delivery/dashboard_renderer.render_dashboard_html()` (local default `--output`) | Local-render dashboard target. |
| `ui/dashboard.html`, `ui/index.html` | CI publish path — see § Dashboard Publish Path | Published Pages artifact pair. |

Renderer and notifier are downstream consumers of these artifacts. The contract is the canonical decision boundary, but downstream consumers read multiple artifacts (contract + payload + run + sidecars), not the contract alone.

---

## Sidecars

Three deterministic sidecars exist. Each has a distinct producer / consumer relationship — they are not uniformly "downstream of the contract":

- **`market_map`** — `cuttingboard/market_map.py` (`build_market_map()`, lines 116–156). Top-level keys: `schema_version`, `generated_at`, `session_date`, `source.{mode, run_at_utc}`, `primary_symbols`, `symbols`, `context`, `data_quality`. Lifecycle (`grade`, `setup_state` transitions, `removed_symbols`) is injected by `market_map_lifecycle.inject_lifecycle()`. Carries `generation_id` (injected from runtime). **Built in-runtime before contract assembly** (`runtime.py:888`) and consumed in-runtime by `build_visibility_map(trade_decisions, market_map)` (`runtime.py:903`) and `apply_overnight_policy(...)` (`runtime.py:966`); then consumed downstream by the dashboard renderer and by next-run lifecycle injection.
- **`trend_structure`** — `cuttingboard/trend_structure.py` (`build_trend_structure_snapshot()`, lines 284–313). Per-symbol records expose `current_price`, `vwap`, `sma_50`, `sma_200`, `relative_volume`, `price_vs_vwap`, `price_vs_sma_50`, `price_vs_sma_200`, `trend_alignment`, `entry_context`, `data_status`, `reason`. Refreshed in MODE_LIVE via `_refresh_trend_structure_sidecar()` (`runtime.py:1917`). No `generation_id` (deterministic snapshot, no lineage token). **Renderer-consumed only.**
- **`watchlist_sidecar`** — `cuttingboard/watchlist_sidecar.py` (`build_watchlist_snapshot()`, lines 35–58). Per-symbol `sector_theme`, `watch_reason`, `current_price`. No `generation_id`. **Observe-only**; no v1 consumer per `docs/artifact_flow_map.md:118-124`.

None of the three mutates the contract or calls back into qualification, regime, or sizing. The market_map sidecar deliberately participates in pre-contract runtime steps (visibility, overnight policy) without being a decision-gate input — its grades remain display-tier signals, not qualification gates.

---

## Dashboard Publish Path

`cuttingboard/delivery/dashboard_renderer.py` is the sole renderer of the published dashboard pair, but the **local** and **published** paths use different artifact inputs and different output targets.

- **Entry function:** `render_dashboard_html()` (`dashboard_renderer.py:1381`).
- **Local default path:** the renderer reads `logs/latest_payload.json`, `logs/latest_run.json`, `logs/market_map.json`, `logs/macro_drivers_snapshot.json`, `logs/trend_structure_snapshot.json`, and (where present) `logs/latest_contract.json`, writing to `reports/output/dashboard.html` by default. This is the local render target, **not** the Pages artifact.
- **CI hourly publish path** (`.github/workflows/hourly_alert.yml:57-62`): the workflow invokes
  ```
  python3 -m cuttingboard.delivery.dashboard_renderer \
      --payload logs/latest_hourly_payload.json \
      --run    logs/latest_hourly_run.json \
      --output ui/dashboard.html
  ```
  then shell-copies `ui/dashboard.html` → `ui/index.html`. The hourly contract is copied separately by the workflow to `ui/contract.json`. The `ui/` pair is the actual Pages-published artifact.
- **Coherence gate:** `validate_coherent_publish()` (`dashboard_renderer.py:360`) extracts `generation_id` from exactly three artifacts via `_coherent_generation_ids()` (line 328) — `payload.meta.generation_id`, `run.generation_id`, `market_map.generation_id` — and fails closed (line 423) on any missing or mismatched token. The **contract carries `generation_id`** (`contract.py:90-97`) but is **not** part of this equality gate. The gate also blocks fixture-mode artifacts and gates by output path under `ui/`.
- **Display layers added in PRD-130 → PRD-132:** trend-structure unknown-state normalization (PRD-130), SMA Composite display column (PRD-131), and Intraday Context (VWAP × RVOL) display column (PRD-132). All three are renderer-local; none feeds back into decision logic.

---

## Generation_id and Lineage Protections

`generation_id` is the canonical lineage token for a run, formatted as `<mode>-<ISO8601Z>` (e.g. `hourly-20260512T215018Z`).

- **Produced** by `_generation_id()` (`runtime.py:2126`), delegating to `_run_id()` with mode, timestamp, and (where applicable) fixture file.
- **Propagated** into the contract (`contract.py:97`), attached to the payload meta block via `_attach_generation_id_to_payload()` (`runtime.py:2136`), and injected into `market_map.json` (`runtime.py:619`/`901`).
- **Validated** at the dashboard publish boundary by `validate_coherent_publish()`. The renderer refuses to publish if payload / run / market_map tokens diverge — the protection installed by PRD-118 and reinforced by PRD-134 against the daily-pipeline mismatch that produced the failed Cuttingboard Pipeline runs cited in `docs/PROJECT_STATE.md`. The **contract is not part of the equality gate** (it carries `generation_id` but `validate_coherent_publish()` does not read the contract).
- **Not present** on `trend_structure_snapshot.json` or `watchlist_snapshot.json` — these are deterministic timestamp-only artifacts, refreshed in-place per run.

The lineage protection model is therefore: **payload, run, and market_map** participate in publish coherence enforcement; the contract carries `generation_id` but is not gated by `validate_coherent_publish()`; trend_structure and watchlist are coupled by timestamp and per-run regeneration rather than by token.

---

## Notifier and Evaluation Boundaries

`cuttingboard/notifications/__init__.py` and `cuttingboard/notifications/formatter.py` provide the hourly Telegram surface, invoked from `runtime.py`'s notify-run path.

- **Entry:** `_execute_notify_run()` (`runtime.py:437`) → `format_hourly_notification()` (`runtime.py:541`, from `cuttingboard/notifications/__init__.py:511-588`) → Telegram transport.
- **Inputs:** `format_hourly_notification()` accepts **regime, validation, qualification, candidate lines, market_map, and normalized_quotes** (`cuttingboard/notifications/__init__.py:511-588`). It does **not** receive the canonical contract/payload pair. The hourly notification is formatted in `_execute_notify_run()` (`runtime.py:540-605`) **before** the hourly contract/payload are assembled.
- **Market_map source:** the run's freshly built `market_map` (`runtime.py:606`) or a previous-run map loaded via `_load_previous_market_map()` (`runtime.py:620`).
- **Lifecycle alerts:** `_append_lifecycle_alerts()` (line 395) and `_lifecycle_alert_lines()` (line 359) consume `market_map["symbols"]` and `market_map["removed_symbols"]` to render UPGRADED / DOWNGRADED transitions and removals.
- **Decision boundary:** the notifier is downstream of qualification but is **not** a contract consumer in the strict sense — it is assembled from raw qualification / regime / market_map state. It does not invoke qualification, regime, sizing, or contract assembly; it does not mutate the contract.
- **Write boundary:** notification transport **does** write append-only records to `logs/audit.jsonl` via `send_notification()` / `send_telegram()` / `write_notification_audit()` (`cuttingboard/output.py:700-733`, `cuttingboard/audit.py:242-307`). It does not write the per-run JSON family (`latest_*`) or any sidecar artifact.
- **No generation_id guard:** unlike the renderer, the notifier does not enforce token coherence between the run state and market_map. Its consumption of market_map is restricted to lifecycle text, which fails gracefully if a field is absent rather than halting the alert.

`cuttingboard/evaluation.py` and `cuttingboard/performance_engine.py` follow the same downstream-only contract — they are also runtime-active rather than purely doctrinal:

- `run_post_trade_evaluation()` (`cuttingboard/evaluation.py:37-71`, called at `runtime.py:1030`) reads prior `logs/audit.jsonl` records and appends `logs/evaluation.jsonl`.
- `run_performance_engine()` (`cuttingboard/performance_engine.py`, called at `runtime.py:1031`) reads the evaluation stream and writes `logs/performance_summary.json`.

Neither feeds back into qualification, regime, sizing, or the contract.

---

## Known Strengths

- **Single canonical decision contract.** `build_pipeline_output_contract()` (`contract.py:59`) is the single producer of the per-run trade decision. There is no second source of truth for `TRADES | NO TRADE | HALT`. Downstream consumers (renderer, notifier, evaluation) read multiple artifacts (contract, payload, run, market_map, trend_structure, macro_drivers) rather than the contract alone, but no consumer redefines the decision itself.
- **Lineage-gated publish.** PRD-118 / PRD-134 collapsed dashboard freshness to a single, fail-closed `generation_id` equality check across payload, run, and market_map. Stale or mismatched runs cannot reach the Pages artifact.
- **Sidecar-first display growth.** PRD-130 → PRD-132 added three dashboard display layers (unknown-state normalization, SMA Composite, Intraday Context) entirely within the renderer, with no schema, contract, or runtime change. The sidecar doctrine has held.
- **Determinism at every layer.** Sidecars are pure functions of validated inputs; the renderer is a pure function of artifacts; the notifier is a pure function of regime / validation / qualification / market_map state and previous-run state. This review surfaced documentation drift, but no hidden coupling between sidecars and the decision pipeline.
- **Hard test floor.** 2407 passing tests across 82 test files; the renderer alone has 302 dedicated tests; the hourly alert path has 1157 lines of test coverage. PRD-132 added 76 net new renderer tests pinning eleven display cells.
- **Strict governance scaffolding.** PRD-121 LANE classification, PRD-113 governance hardening, the PRD_REGISTRY / PROJECT_STATE / FILES-allowlist triple, and the cross-review gate together produce a near-zero rate of scope drift across the PRD-122 → PRD-134 arc.
- **Macro-aware HALT discipline.** The `HALT_SYMBOLS` (`^VIX`, `DX-Y.NYB`, `^TNX`, `SPY`, `QQQ`) pre-empt per-symbol work when macro inputs degrade. STAY_FLAT short-circuits all qualification.

---

## Known Risks

These are *observational* risks recorded for follow-up consideration. No implementation directive is implied.

- **Trend_structure has no `generation_id`.** The renderer reads `trend_structure_snapshot.json` alongside payload/run/market_map but does not verify any lineage relationship between them. A stale or unrefreshed trend_structure file (e.g. if `_refresh_trend_structure_sidecar()` silently fails in MODE_LIVE) would render without raising the publish gate. The current mitigation is in-place per-run regeneration, not token coherence.
- **Watchlist sidecar lineage is similarly unguarded.** Same posture as trend_structure: no `generation_id`, no coherence check.
- **Notifier reads market_map without generation_id validation.** A divergent or stale market_map would still produce lifecycle alert text rather than halting the notification. The body content uses contract/payload, but the lifecycle overlay is sourced from market_map directly.
- **`runtime.py` is now ~2100+ lines.** A single orchestration module hosts CLI parsing, the pipeline, generation_id production, sidecar refresh, payload attachment, notify-run dispatch, and a number of write helpers. Module-internal coupling is high; the cost of cross-cutting changes scales with this surface.
- **Artifact file naming is bifurcated.** Some files use the `latest_hourly_*` prefix (`latest_hourly_run.json`, `latest_hourly_contract.json`, `latest_hourly_payload.json`); others use `latest_*` (`latest_payload.json`, `latest_run.json`); sidecars use neither (`market_map.json`, `trend_structure_snapshot.json`, `watchlist_snapshot.json`, `macro_drivers_snapshot.json`). The renderer reads from the unprefixed forms; the writers produce the `hourly_` forms. There may be a copy or rename step worth re-auditing.
- **CALL_SITE_MAP.md and SCHEMA_MAP.md decay risk.** Both are referenced by CLAUDE.md as authoritative spot-read targets. Any drift between these maps and the code raises the cost of every PRD that depends on them.
- **Display-layer accretion in the renderer.** PRD-130 / PRD-131 / PRD-132 added three columns and an unknown-state normalization step within one renderer module. The dashboard renderer is now well over 1000 lines and growing per display PRD. Each new column adds at least one MISSING-row dash and one isolation invariant.
- **No automated freshness test on the watchlist sidecar.** Coverage exists for market_map and trend_structure freshness paths; watchlist_sidecar's per-run regeneration relies on the runtime to call it.

---

## Recommended Next Review Targets

- Whether trend_structure and watchlist snapshots should carry `generation_id` and join the publish coherence gate.
- Whether `runtime.py` should be split along pipeline-phase boundaries (input/regime/qualification/sidecar/contract/payload/notify) without altering behavior.
- Whether artifact filename prefixes (`latest_`, `latest_hourly_`, no prefix) should be normalized.
- Whether the notifier should adopt a lineage check analogous to `validate_coherent_publish()` before emitting lifecycle text.
- Whether `docs/CALL_SITE_MAP.md` and `docs/SCHEMA_MAP.md` need a scheduled freshness audit cadence.
- Whether dashboard display-layer PRDs should consolidate around a shared renderer-local display helper to bound per-column accretion.

These are candidates for future PRDs, not directives.

---

## Validation Status

This is a documentation-only milestone PRD with zero production LOC and zero source-module modifications. Per `CLAUDE.md § Test-suite discipline`, no targeted or full-suite test run is required for documentation-only work that does not alter executable code.

- **Targeted tests run for PRD-135:** none.
- **Full suite run for PRD-135:** none.
- **Rationale:** read-only documentation; no executable code changed; no shared helper, fixture, or `conftest.py` touched; no infrastructure-level change.
- **Inherited test baseline:** 2407 passing tests as of 2026-05-12 (from PRD-134 closeout, recorded in `docs/PROJECT_STATE.md`).
- **No tests are skipped, expected-to-fail, or marked xfail by this PRD.**

---

## Git HEAD at Checkpoint

```
bad2d53d863d5e0618ef28457e129c590449d80f
bad2d53 docs: improve agent workflow approval and triage discipline
```

This SHA is the HEAD of `main` at the time of milestone authoring and is the parent commit of the eventual `docs: record engine milestone checkpoint` commit (PRD-135 R7).
