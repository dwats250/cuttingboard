# engine_doctor.py — Cuttingboard Pipeline Inspector

A standalone developer diagnostic tool for the cuttingboard options trading engine. Run it any time to get a full picture of module health, dependency structure, and test status — without touching the pipeline itself.

---

## Location

```
tools/engine_doctor.py
```

Run from the project root:

```bash
python3 tools/engine_doctor.py
```

---

## Usage

```bash
# Full health report (import check + dependency graph + runtime files)
python3 tools/engine_doctor.py

# Full report + run the test suite
python3 tools/engine_doctor.py --tests

# Show blast radius of a specific module
python3 tools/engine_doctor.py --impact regime

# Skip import check (faster, just graph + files)
python3 tools/engine_doctor.py --no-import-check

# Combine flags freely
python3 tools/engine_doctor.py --impact qualification --tests
```

---

## What It Reports

### 1. Pipeline Layers

Lists all 23 modules across L1–L11 (core pipeline) and support modules. For each:

- Attempts a live `import` and reports success/failure + load time in ms
- Shows key exported symbols
- Prints the exact exception if import fails

**Example output:**
```
    1  config               ✓ ok   14ms   constants, get_flow_data_path
    2  ingestion            ✓ ok  648ms   RawQuote, fetch_all, fetch_quote
    7  regime               ✓ ok    2ms   RegimeState, compute_regime
   —   notifications        ✓ ok    2ms   format_notification, format_run_alert
```

### 2. Dependency Graph

Built from AST analysis (no imports required). For each module shows:

- What it directly imports from other cuttingboard modules (`←`)
- What other modules use it (`used by:`)

Also detects and flags **circular dependencies**.

**Example:**
```
regime           ← normalization
                   used by: audit, contract, notifications, options,
                             output, qualification, run_intraday, runtime, watch
```

### 3. Runtime Files

Checks existence and size of:

| File | Purpose |
|------|---------|
| `logs/audit.jsonl` | Append-only per-run audit log |
| `logs/last_notification_state.json` | Notification dedup state |
| `.env` | Secrets (Telegram, Polygon) |
| `config.toml` | Static config |

### 4. Impact Analysis (`--impact <module>`)

Performs a BFS on the reverse dependency graph to show exactly what would break if a module is changed or removed. Splits results into:

- **Direct dependents** — modules that import it directly
- **Transitive dependents** — modules downstream through the chain

**Example — `--impact regime`:**
```
Direct dependents (9):
  audit, contract, notifications, options, output,
  qualification, run_intraday, runtime, watch

Transitive dependents (5):
  chain_validation, delivery, flow, notify_test, sector_router
```

### 5. Test Suite (`--tests`)

Runs `pytest --tb=line -q` and shows the last 12 lines of output, color-coded:

- Green for passing summary
- Red for failures and error lines
- The known pre-existing failure (`test_sunday_mode_fixture_run_is_end_to_end_and_offline`) shows up in red — expected and documented

---

## Current State (as of 2026-04-24)

| Check | Result |
|-------|--------|
| Modules importable | 23 / 23 |
| Tests passing | 802 / 803 |
| Known broken test | `test_sunday_mode_fixture_run_is_end_to_end_and_offline` (pre-existing fixture failure) |
| Audit log | Present (53 KB) |
| Notification state | Not found (created on first live Telegram send) |
| Circular dependencies | 2 detected (pre-existing, non-breaking) |

### Known Circular Dependencies

Both are managed via lazy/function-level imports and do not break anything currently:

- `qualification → flow → qualification`
- `output → delivery → output`

---

## Design Notes

- **No pipeline coupling.** The tool is a standalone script in `tools/`. It imports the pipeline modules for health checking but is not imported by anything in the engine.
- **AST-based graph.** The dependency graph is derived by parsing source files, not by running the code — so it works even when modules are broken.
- **Zero new dependencies.** Uses only the Python standard library (`ast`, `importlib`, `subprocess`, `argparse`) plus what the project already installs.
