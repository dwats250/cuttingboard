# Artifact Flow Map — cuttingboard

This document audits every artifact written by the pipeline, their writers, readers,
consumers, and test isolation requirements. It is documentation-only. No source
behavior is changed here.

---

## Artifact Inventory

The pipeline produces two artifact families — **hourly** and **non-hourly** — that must
be documented separately because they write to different paths and the dashboard renderer
defaults differ.

**Hourly artifact family** (written by `runtime.py:_write_hourly_artifacts` and related functions):
- `logs/latest_hourly_contract.json`
- `logs/latest_hourly_payload.json`
- `logs/latest_hourly_run.json`

**Non-hourly artifact family** (written by non-hourly pipeline runs):
- `logs/latest_payload.json`
- `logs/latest_run.json`

**Path-split families (hourly vs non-hourly):**
- logs/latest_payload.json vs logs/latest_hourly_payload.json — payload write path differs by mode; dashboard renderer defaults differ accordingly
- logs/latest_run.json vs logs/latest_hourly_run.json — run summary write path differs by mode; dashboard renderer defaults differ accordingly

**Shared / mode-independent artifacts:**
- `logs/market_map.json`
- `logs/macro_drivers_snapshot.json`
- `logs/audit.jsonl`
- `logs/evaluation.jsonl`
- `logs/performance_summary.json`
- `logs/sector_router_state.json`

**Dashboard / published artifacts:**
- `reports/output/dashboard.html`
- `reports/output/report.html`
- `ui/dashboard.html`
- `ui/index.html`

---

## Artifact Writers

### logs/latest_hourly_contract.json
- **Writer:** `runtime.py:_write_hourly_artifacts` → `_write_contract_file`
- **Constant:** `runtime.LATEST_HOURLY_CONTRACT_PATH`
- **Consumers:** `delivery/dashboard_renderer.py` (reads entry prices via `_load_contract_entry_context`)
- **Category:** Runtime-critical, hourly family
- **Test isolation:** monkeypatch `runtime.LATEST_HOURLY_CONTRACT_PATH` to `tmp_path`

### logs/latest_hourly_payload.json
- **Writer:** `runtime.py:_write_hourly_artifacts` via `deliver_json(payload, output_path=str(LATEST_HOURLY_PAYLOAD_PATH))`
- **Constant:** `runtime.LATEST_HOURLY_PAYLOAD_PATH`
- **Path note:** This is the **hourly** write path. The dashboard renderer's default read path is
  `logs/latest_payload.json` (see below). The CI hourly workflow overrides the renderer with
  `--payload logs/latest_hourly_payload.json` to reconcile these paths.
- **Consumers:** `delivery/dashboard_renderer.py` (via CI `--payload` override)
- **Category:** Runtime-critical, hourly family
- **Test isolation:** monkeypatch `runtime.LATEST_HOURLY_PAYLOAD_PATH` to `tmp_path`

### logs/latest_hourly_run.json
- **Writer:** `runtime.py:_write_hourly_artifacts`
- **Constant:** `runtime.LATEST_HOURLY_RUN_PATH`
- **Path note:** This is the **hourly** run summary write path. The dashboard renderer's default
  read path is `logs/latest_run.json` (see below). The CI hourly workflow overrides the renderer
  with `--run logs/latest_hourly_run.json`.
- **Consumers:** `delivery/dashboard_renderer.py` (via CI `--run` override); `hourly_alert.yml`
- **Category:** Runtime-critical, hourly family
- **Test isolation:** monkeypatch `runtime.LATEST_HOURLY_RUN_PATH` to `tmp_path`

### logs/latest_payload.json
- **Writer:** `runtime.py:_write_payload_artifacts` via `transport.deliver_json(payload)` (default path)
- **Constant:** `transport._DEFAULT_JSON_PATH = "logs/latest_payload.json"`
- **Path note:** This is the **non-hourly** write path and the dashboard renderer's **default
  read path** (`dashboard_renderer._PAYLOAD_PATH`). The two-path relationship:
  - `logs/latest_payload.json` — non-hourly runs write here; renderer reads here by default
  - `logs/latest_hourly_payload.json` — hourly runs write here; CI passes `--payload` to renderer
- **Consumers:** `delivery/dashboard_renderer.py` (default read, no override)
- **Category:** Runtime-critical, non-hourly family
- **Test isolation:** monkeypatch `transport.deliver_json` to a no-op or redirect; monkeypatch
  `runtime.LOGS_DIR` to `tmp_path / "logs"`

### logs/latest_run.json
- **Writer:** `runtime.py:_write_summary_files` via `safe_write_latest(LATEST_RUN_PATH, ...)`
- **Constant:** `runtime.LATEST_RUN_PATH`
- **Path note:** This is the **non-hourly** run summary write path and the dashboard renderer's
  **default read path** (`dashboard_renderer._RUN_PATH = Path("logs/latest_run.json")`). The
  two-path relationship:
  - `logs/latest_run.json` — non-hourly runs write here; renderer reads here by default
  - `logs/latest_hourly_run.json` — hourly runs write here; CI passes `--run` to renderer
- **Consumers:** `delivery/dashboard_renderer.py` (default read, no override)
- **Category:** Runtime-critical, non-hourly family
- **Test isolation:** monkeypatch `runtime.LATEST_RUN_PATH` and `runtime.LOGS_DIR` to `tmp_path`

### logs/market_map.json
- **Writer:** `runtime.py:_write_market_map_file`
- **Constant:** `runtime.MARKET_MAP_PATH`
- **Consumers:** `delivery/dashboard_renderer.py` (reads market context for candidate board);
  next run reads previous market_map via `runtime._load_previous_market_map` for lifecycle injection
- **Category:** Runtime-critical (previous run read-back), dashboard display
- **Test isolation:** monkeypatch `runtime.MARKET_MAP_PATH` and `runtime.LOGS_DIR` to `tmp_path`

### logs/macro_drivers_snapshot.json
- **Writer:** `runtime.py:_write_macro_snapshot`; path constructed as `LOGS_DIR / "macro_drivers_snapshot.json"`
- **Consumers:** `delivery/dashboard_renderer.py` (`_MACRO_SNAPSHOT_PATH`) — fallback when payload
  has no macro_drivers field
- **Category:** Dashboard display, fallback only; not runtime-critical for decisions
- **Test isolation:** monkeypatch `runtime.LOGS_DIR` to `tmp_path`

### logs/audit.jsonl
- **Writer:** `audit.py:write_audit_record` (one record per pipeline run);
  `audit.py:write_notification_audit` (notification events);
  constant: `audit.AUDIT_LOG_PATH = "logs/audit.jsonl"`
- **Consumers:** `runtime.py:_load_run_history` (reads last N records for run context);
  `run_intraday.py`; `performance_engine.py` (indirectly via evaluation)
- **Category:** Audit-only; append-only; never read for decision logic
- **Test isolation:** monkeypatch `audit.AUDIT_LOG_PATH` to `str(tmp_path / "logs" / "audit.jsonl")`

### logs/evaluation.jsonl
- **Writer:** `evaluation.py` via `run_post_trade_evaluation` called from `runtime.py`
- **Constant:** `evaluation.EVALUATION_LOG_PATH = "logs/evaluation.jsonl"`
- **Consumers:** `performance_engine.py:run_performance_engine` (reads to compute performance summary)
- **Category:** Audit / evaluation; downstream only; no pipeline feedback
- **Test isolation:** monkeypatch `runtime.LOGS_DIR` to `tmp_path`

### logs/performance_summary.json
- **Writer:** `performance_engine.py:run_performance_engine`; written to `LOGS_DIR / "performance_summary.json"`
- **Consumers:** display / reporting only
- **Category:** Audit / evaluation; downstream only; no pipeline feedback
- **Test isolation:** monkeypatch `runtime.LOGS_DIR` to `tmp_path`

### logs/sector_router_state.json
- **Writer:** `runtime.py:_sector_router_state_path` → `LOGS_DIR / "sector_router_state.json"`
- **Consumers:** subsequent runs read prior sector router state for continuity
- **Category:** Runtime state; not a decision gate but carries session continuity
- **Test isolation:** monkeypatch `runtime.LOGS_DIR` to `tmp_path`

### reports/output/report.html
- **Writer:** `delivery/transport.py:deliver_html(payload)` — default path
- **Constant:** `transport._DEFAULT_HTML_PATH = "reports/output/report.html"`
- **Note:** This is the **non-hourly transport default HTML output**. It is distinct from
  `reports/output/dashboard.html` (the dashboard renderer default) and `ui/dashboard.html` (CI).
- **Consumers:** local development / manual inspection; not consumed by any automated workflow
- **Category:** Dashboard (local); not runtime-critical
- **Test isolation:** monkeypatch `transport.deliver_html` to a no-op or redirect

### reports/output/dashboard.html
- **Writer:** `delivery/dashboard_renderer.py` when invoked without `--output` override
- **Constant:** `dashboard_renderer._OUTPUT_PATH = Path("reports/output/dashboard.html")`
- **Note:** This is the **default local renderer output**. In CI the hourly workflow overrides
  with `--output ui/dashboard.html`; `reports/output/dashboard.html` is only produced in local runs.
- **Consumers:** local development / manual inspection
- **Category:** Dashboard (local default); not runtime-critical
- **Test isolation:** monkeypatch `dashboard_renderer._OUTPUT_PATH` or pass explicit output path

### ui/dashboard.html
- **Writer:** `delivery/dashboard_renderer.py` invoked with `--output ui/dashboard.html`
- **Note:** `ui/dashboard.html` is produced **only** when explicitly passed as an output path.
  It is not the renderer's default. The CI hourly workflow passes `--output ui/dashboard.html`.
  Local runs without `--output` produce `reports/output/dashboard.html` instead.
- **Consumers:** GitHub Pages (served as live dashboard); `ui/index.html` (copied from this file)
- **Category:** Dashboard artifact (published); live Pages artifact
- **Test isolation:** do not write to `ui/` in tests; pass explicit `--output` to tmp_path

### ui/index.html
- **Writer:** Shell copy step in CI: `cp ui/dashboard.html ui/index.html` (see `.github/workflows/`)
- **Note:** `ui/index.html` is a **published copy target**, not a Python writer artifact. It is
  commonly produced by a shell copy or publish workflow, not by any Python function. It mirrors
  `ui/dashboard.html` exactly and exists because GitHub Pages serves `index.html` as the root.
- **Consumers:** GitHub Pages (root entry point)
- **Category:** Dashboard artifact (published); live Pages artifact
- **Test isolation:** do not write to `ui/` in tests

---

## Artifact Readers

| Artifact | Reader | Permitted operations |
|----------|--------|---------------------|
| `logs/latest_hourly_contract.json` | `dashboard_renderer._load_contract_entry_context` | Render entry prices for display — no new logic |
| `logs/latest_hourly_payload.json` | `dashboard_renderer` (via `--payload` CI override) | Render dashboard from payload — no new logic |
| `logs/latest_hourly_run.json` | `dashboard_renderer` (via `--run` CI override) | Render run metadata — no new logic |
| `logs/latest_payload.json` | `dashboard_renderer._PAYLOAD_PATH` (default) | Render dashboard from payload — no new logic |
| `logs/latest_run.json` | `dashboard_renderer._RUN_PATH` (default) | Render run metadata — no new logic |
| `logs/market_map.json` | `dashboard_renderer._resolve_market_map`; `runtime._load_previous_market_map` | Display tiers (renderer); lifecycle injection for next run (runtime) |
| `logs/macro_drivers_snapshot.json` | `dashboard_renderer._MACRO_SNAPSHOT_PATH` | Fallback macro display when payload has no macro_drivers — no new logic |
| `logs/audit.jsonl` | `runtime._load_run_history` | Load last N run records for run context display |
| `logs/evaluation.jsonl` | `performance_engine.run_performance_engine` | Compute performance summary — downstream only |

**Reader rule:** Readers are only permitted to render, report, or display existing fields.
Readers must not derive new qualification logic, modify trade decisions, or alter contract fields.

---

## Runtime-Critical Artifacts

These artifacts are read back by subsequent pipeline runs and can affect run behavior
if missing or malformed.

| Artifact | Why critical |
|----------|-------------|
| `logs/market_map.json` | Read by `runtime._load_previous_market_map`; used for lifecycle injection into the next run's market map |
| `logs/sector_router_state.json` | Read by sector router to carry session continuity state across runs |
| `logs/latest_run.json` | Read by dashboard renderer (default) and by run history loading |
| `logs/latest_hourly_run.json` | Read by CI hourly workflow and renderer (via `--run` override) |

If any runtime-critical artifact is missing, the pipeline degrades gracefully (returns None /
empty) rather than halting, except where explicitly documented.

---

## Dashboard Artifacts

These artifacts feed the live dashboard or local renderer. They are display-only and must
not be read back into decision logic.

| Artifact | Path type | Publisher |
|----------|-----------|-----------|
| `reports/output/dashboard.html` | Local default | `dashboard_renderer` (no `--output`) |
| `reports/output/report.html` | Local default | `transport.deliver_html` (non-hourly) |
| `ui/dashboard.html` | CI published | `dashboard_renderer --output ui/dashboard.html` (CI hourly) |
| `ui/index.html` | CI published | Shell copy of `ui/dashboard.html` in CI publish step |
| `logs/latest_hourly_payload.json` | CI pipeline | Consumed by renderer via `--payload` override |
| `logs/macro_drivers_snapshot.json` | Fallback | Consumed by renderer when payload lacks macro_drivers |
| `logs/latest_hourly_contract.json` | CI pipeline | Consumed by renderer for entry price display |
| `logs/market_map.json` | Runtime | Consumed by renderer for candidate board display |

---

## Audit Artifacts

These artifacts are written for observability, evaluation, and performance tracking.
They have no feedback into the decision pipeline.

| Artifact | Writer | Purpose |
|----------|--------|---------|
| `logs/audit.jsonl` | `audit.write_audit_record` | One record per pipeline run; append-only |
| `logs/evaluation.jsonl` | `evaluation.run_post_trade_evaluation` | Per-signal evaluation records |
| `logs/performance_summary.json` | `performance_engine.run_performance_engine` | Aggregated performance buckets |

---

## Test Isolation Requirements

Tests must not leave modified files under `logs/`, `reports/`, or `ui/` after full-suite
execution. The required isolation pattern is:

**1. Isolate runtime log paths:**
```python
monkeypatch.setattr(runtime, "LOGS_DIR", tmp_path / "logs")
monkeypatch.setattr(runtime, "LATEST_RUN_PATH", tmp_path / "logs" / "latest_run.json")
monkeypatch.setattr(runtime, "LATEST_HOURLY_RUN_PATH", tmp_path / "logs" / "latest_hourly_run.json")
monkeypatch.setattr(runtime, "LATEST_HOURLY_CONTRACT_PATH", tmp_path / "logs" / "latest_hourly_contract.json")
monkeypatch.setattr(runtime, "LATEST_HOURLY_PAYLOAD_PATH", tmp_path / "logs" / "latest_hourly_payload.json")
monkeypatch.setattr(runtime, "MARKET_MAP_PATH", tmp_path / "logs" / "market_map.json")
```

**2. Isolate audit writes:**
```python
monkeypatch.setattr(audit, "AUDIT_LOG_PATH", str(tmp_path / "logs" / "audit.jsonl"))
```

**3. Isolate transport delivery (lazy imports):**
```python
monkeypatch.setattr(transport, "deliver_json", lambda payload, output_path=...: None)
monkeypatch.setattr(transport, "deliver_html", lambda payload, output_path=...: None)
```

**Why transport needs separate monkeypatching:** `runtime._write_payload_artifacts` and
`runtime._write_hourly_artifacts` perform lazy imports of `transport` inside the function body.
Monkeypatching `runtime.LOGS_DIR` alone does not intercept these delivery calls. Both
`runtime.LOGS_DIR` and `transport.deliver_*` must be patched when running full pipeline tests.

**Rule:** Tests must isolate artifact writes to `tmp_path` and must not leave modified files
under `logs/`, `reports/`, or `ui/` after full-suite execution.

See `tests/test_sunday_mode.py` and `tests/test_hourly_alert.py` for canonical isolation examples.
