# PRD-016 / PRD-016.1 Audit Report — Pre-UI Readiness + Ground Truth Lock

**Date:** 2026-04-23  
**Scope:** Contract/payload consumption, qualification wiring, runtime entrypoints, delivery layer purity, legacy path elimination, interface lock.

---

## Canonical Data Flow

```
config.toml
  └─ config.get_flow_data_path()
       └─ runtime._load_flow()
            └─ flow.load_flow_snapshot(path)      ← SINGLE call site

python -m cuttingboard
  └─ __main__.cli_main()
       └─ runtime.execute_run()
            ├─ runtime._execute_notify_run()      ← non-premarket notify modes
            └─ runtime._run_pipeline()            ← premarket / sunday / fixture
                 ├─ qualify_all(..., flow_snapshot=_load_flow())
                 ├─ output.render_report()        ← pure render, no pipeline logic
                 ├─ output.write_terminal()
                 ├─ output.write_markdown()
                 └─ output.send_notification()
```

---

## Acceptance Criteria Results

| AC | Requirement | Status | Notes |
|----|-------------|--------|-------|
| AC1 | `load_flow_snapshot()` — exactly one production call site | PASS | `runtime.py:373` inside `_load_flow()` |
| AC2 | `output.py` does not call `load_flow_snapshot()` | PASS | Zero matches |
| AC3 | All `qualify_all()` calls include `flow_snapshot` | PASS | All three call sites in runtime.py pass `flow_snapshot=_load_flow()` or `flow_snapshot=flow_snapshot` |
| AC4 | No `os.getenv` for flow config | PASS | Flow reads via `config.get_flow_data_path()` → `tomllib`. `os.getenv` in config.py is for API secrets only (POLYGON, TELEGRAM) — not config. |
| AC5 | No unreachable functions | PASS | `output.run_pipeline()` and `run_premarket.py` deleted |
| AC6 | Invalid flow file raises exception | PASS | `load_flow_snapshot()` raises `ValueError`/`FileNotFoundError`, never swallows |
| AC7 | Single payload object into output layer | PASS | `runtime._run_pipeline()` passes typed args to `render_report()` |
| AC8 | CLI surface fully verified | PASS | All 5 flags verified: `--mode`, `--notify-mode`, `--fixture-file`, `--file`, `--date`. Flag list is complete and exhaustive. |

---

## qualify_all() Call Sites

| Location | Passes flow_snapshot? |
|----------|-----------------------|
| `runtime.py:425` (`_execute_notify_run`, qualify-only modes) | YES — `flow_snapshot=flow_snapshot` |
| `runtime.py:454` (`_execute_notify_run`, hourly modes) | YES — `flow_snapshot=flow_snapshot` |
| `runtime.py:601` (`_run_pipeline`) | YES — `flow_snapshot=_load_flow()` |

---

## load_flow_snapshot() Call Sites

| Location | Role |
|----------|------|
| `flow.py:154` | Definition |
| `runtime.py:373` | Single production call site inside `_load_flow()` |

---

## Output Layer Consumers

All output rendering and delivery goes through:
- `output.render_report()` — pure render, no data loading
- `output.render_report_from_payload()` — pure render from contract dict
- `output.write_terminal()` — write to stdout
- `output.write_markdown()` — write to reports/
- `output.send_notification()` — Telegram delivery

Called from: `runtime.py`, `run_intraday.py` (send_notification only), `delivery/html_renderer.py` (render_report_from_payload only)

---

## Deleted Legacy Paths

| Item | Reason |
|------|--------|
| `output.run_pipeline()` | Full pipeline duplicate; used `flow_snapshot=None`; never called from production workflows |
| `run_premarket.py` | Legacy entrypoint; called deleted function; replaced by `python -m cuttingboard --mode live --notify-mode premarket` |
| `output.py` dead imports | 15 pipeline imports removed after deleting `run_pipeline()` |
| `ntfy_title()` | Defined in notifications/__init__.py, never called |
| `_format_premarket()` | Old premarket formatter, unreachable after switching to hourly format |

---

## Test Changes

| File | Change |
|------|--------|
| `tests/test_watch_tradability.py` | Removed pipeline-integration tests that patched `output.run_pipeline()`; kept `test_is_tradable_symbol_rules()` |
| `tests/test_phase6.py` | Removed `TestWriteCommitMsg`; kept all `run_intraday` tests |
| `tests/test_notifications.py` | Removed `test_notification_omits_focus_and_watch_when_empty` (tested deleted `_format_premarket` path) |

---

## Config Source

- Flow path: `config.toml` `[flow]` `data_path` → `config.get_flow_data_path()` → `runtime._load_flow()`
- API secrets: `.env` via `dotenv` → `os.getenv()` in `config.py` (POLYGON_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
- No alternate config sources. No `os.getenv` for non-secret config.

---

## Entrypoints

| Command | Role | Status |
|---------|------|--------|
| `python -m cuttingboard` | Primary production entrypoint → `runtime.cli_main()` | ACTIVE |
| `python -m cuttingboard.run_intraday` | Legacy trigger-based regime monitor (L1–5 only) | UNSCHEDULED — no workflow calls this |

---

## Failure Contract

- `load_flow_snapshot()` raises `FileNotFoundError` on missing file
- `load_flow_snapshot()` raises `ValueError` on invalid JSON, missing fields, empty symbols
- `_load_flow()` propagates all exceptions — no silent fallback
- `qualify_all()` receives `None` when no flow path configured (intentional — gate skips cleanly)

---

## End State

- One execution path: `__main__` → `runtime.execute_run()` → `runtime._run_pipeline()`
- One flow ingestion path: `runtime._load_flow()` → `flow.load_flow_snapshot()`
- One output contract: typed args → `output.render_report()` → string
- Zero hidden logic in output layer
- 712 tests passing (1 pre-existing failure in `test_operationalization.py`, unrelated to this PRD)
