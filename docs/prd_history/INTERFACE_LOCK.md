# Interface Lock — Cuttingboard Ground Truth

**Established:** 2026-04-23 (PRD-016.1)  
**Authority:** This document supersedes any prior assumed interfaces. All future PRDs operate from this baseline.

---

## Production Entrypoint

```
python -m cuttingboard [flags]
```

Resolves to: `cuttingboard/__main__.py` → `runtime.cli_main()`

No other entrypoint is active in any scheduled workflow.

---

## CLI Flags (Complete and Verified)

| Flag | Type | Values | Usage |
|------|------|--------|-------|
| `--mode` | choice | `live`, `fixture`, `sunday`, `verify`, `prefetch` | Run mode. Defaults to `live`. |
| `--notify-mode` | choice | `premarket`, `orb_trajectory`, `post_orb`, `midmorning`, `power_hour`, `market_close`, `hourly` | Notification mode. Optional. |
| `--fixture-file` | path | Any valid path | Fixture JSON for `--mode fixture`. |
| `--file` | path | Any valid path | Run summary JSON for `--mode verify`. |
| `--date` | string | YYYY-MM-DD | Override the resolved run date. |

**No other flags exist.** The flag list above is complete and exhaustive.

---

## Config Sources

| Source | Purpose | Access |
|--------|---------|--------|
| `config.toml` | Flow data path, runtime constants | `config.get_flow_data_path()`, module-level constants |
| `.env` (via dotenv) | API secrets | `os.getenv()` in `config.py` only — POLYGON_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID |

No other config sources. No ENV reads for non-secret config. No YAML config.

---

## Module Roles (Locked)

| Module | Role | Constraints |
|--------|------|-------------|
| `runtime.py` | Sole orchestrator. Mode dispatch, flow loading, pipeline execution, notification routing. | Must not be bypassed. |
| `output.py` | Pure render + delivery. Telegram, terminal, markdown. | Must not load data. Must not call pipeline functions. |
| `flow.py` | Flow ingestion + validation. | `load_flow_snapshot()` is the only loader. Called only from `runtime._load_flow()`. |
| `config.py` | Constants and secret access. | `get_flow_data_path()` is the only config.toml reader for flow. |
| `qualification.py` | 9-gate qualification logic. | `qualify_all()` always receives `flow_snapshot` from runtime. Never called with `flow_snapshot=None` in production. |

---

## Single-Source Rules

| Resource | Single Source |
|----------|---------------|
| Flow data | `runtime._load_flow()` → `flow.load_flow_snapshot()` |
| qualify_all calls | All in `runtime.py` only (lines 425, 454, 601) |
| Notification dispatch | `output.send_notification()` only |
| Config (non-secret) | `config.toml` via `tomllib` |
| Config (secrets) | `.env` via `dotenv` → `os.getenv()` in `config.py` |

---

## Scheduled Workflows

| Workflow | File | Command |
|----------|------|---------|
| Premarket (13:00 UTC M–F) | `cuttingboard.yml` | `python -m cuttingboard --mode live --notify-mode premarket` |
| Prefetch (12:50 UTC M–F) | `cuttingboard.yml` | `python -m cuttingboard --mode prefetch --notify-mode premarket` — cache-warm only (PRD-193): warms `data/cache` and persists it via `actions/cache` for the 13:00 live run; sets no `PUBLISH_READY`, so it renders/publishes nothing and cannot trip the PRD-119 freshness gate. (PRD-189 had dropped this slot to noop; PRD-193 re-enabled it publish-safe.) |
| Sunday report (10:00 UTC) | `cuttingboard.yml` | `python -m cuttingboard --mode sunday --notify-mode premarket` |
| Intraday slots: ORB / post-ORB / mid-morning / power-hour | `hourly_alert.yml` | Folded into the hourly-alert window — no dedicated cron. PRD-189 dropped the `cuttingboard.yml --mode <slot>` invocations (they ran the full live pipeline, not the intended slot scan, and overlapped the hourly coverage); PRD-192 ratifies the fold-in. The hourly run within the routine PT window provides intraday coverage; per-run notify_mode is recorded on the notification audit record. |
| Hourly alert (every 30 min) | `hourly_alert.yml` | `python -m cuttingboard --mode live --notify-mode hourly` |

---

## Unscheduled Modules

| Module | Status | Notes |
|--------|--------|-------|
| `run_intraday.py` | UNSCHEDULED | Legacy trigger-based regime monitor (L1–5). No workflow calls it. CHAOTIC/REGIME_SHIFT/VIX_SPIKE logic exists but is not active in production. |

---

## Failure Contract

- Missing required data → raises exception, never silent fallback
- Invalid flow file → `ValueError` or `FileNotFoundError` from `load_flow_snapshot()`
- Pipeline HALT → `outcome = HALT`, exit code 1, notification sent
- `qualify_all(flow_snapshot=None)` is only valid when no flow path is configured in config.toml; it is never hardcoded to None in production code
