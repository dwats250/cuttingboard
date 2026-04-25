# engine_doctor.py — Cuttingboard Pipeline Inspector

A standalone developer diagnostic tool for the cuttingboard pipeline. Verifies module importability, dependency graph integrity, runtime file presence, and test suite status — without touching the pipeline itself.

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

# Machine-readable JSON output
python3 tools/engine_doctor.py --json

# Validate against known-good baseline
python3 tools/engine_doctor.py --baseline tools/baseline.json

# Strict mode: treat warnings as failures (used in CI)
python3 tools/engine_doctor.py --strict --baseline tools/baseline.json

# Full CI-equivalent check
python3 tools/engine_doctor.py --json --tests --strict --baseline tools/baseline.json

# Show blast radius of a specific module
python3 tools/engine_doctor.py --impact regime

# Skip import check (faster, just graph + files)
python3 tools/engine_doctor.py --no-import-check
```

---

## What It Checks

### 1. Pipeline Modules

Attempts a live `import` of every module in the pipeline catalog and support modules (23 total). For each:

- Reports success/failure and load time in ms
- Lists key exported symbols
- Prints the exact exception on import failure

**Example output:**
```
    1  config               ✓ ok   14ms   constants, get_flow_data_path
    2  ingestion            ✓ ok  648ms   RawQuote, fetch_all, fetch_quote
    7  regime               ✓ ok    2ms   RegimeState, compute_regime
   —   notifications        ✓ ok    2ms   format_notification, format_run_alert
```

### 2. Dependency Graph

Built from AST analysis (no imports required). For each module:

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
| `.env` | Secrets (Polygon, ntfy) |

### 4. Test Suite (`--tests`)

Runs `pytest --tb=line -q` and shows the last 12 lines of output. The known pre-existing failure (`test_sunday_mode_fixture_run_is_end_to_end_and_offline`) is documented in `tools/baseline.json` as an expected failure and does not block CI.

### 5. Impact Analysis (`--impact <module>`)

BFS on the reverse dependency graph showing what would break if a module changes:

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

---

## JSON Output Structure

With `--json`, the tool prints a single JSON object to stdout:

```json
{
  "status": "OK" | "WARN" | "FAIL",
  "modules": {
    "total": 23,
    "importable": 23,
    "failed": []
  },
  "tests": {
    "passed": 802,
    "failed": 1,
    "expected_failures": ["test_sunday_mode_fixture_run_is_end_to_end_and_offline"]
  },
  "runtime_files": {
    "missing": [],
    "present": ["logs/audit.jsonl", ".env"]
  },
  "dependencies": {
    "circular": [["qualification", "flow"], ["output", "delivery"]],
    "new_circular": []
  },
  "impact": {}
}
```

`status` is the top-level result: `OK`, `WARN`, or `FAIL`.

---

## Exit Codes

| Code | Meaning | Trigger |
|------|---------|---------|
| 0 | OK | All checks passed |
| 1 | Test failure | Unexpected test failures (not in expected_failures baseline) |
| 2 | Import failure | One or more modules cannot be imported |
| 3 | Circular dependency | New circular dependency detected (not in baseline) |
| 4 | Missing file | Required runtime file missing (as defined in baseline) |
| 5 | Baseline mismatch | Any deviation from `tools/baseline.json` in strict mode |

Priority order when multiple codes apply: 5 > 3 > 2 > 1 > 4. The highest-priority code is the process exit code.

---

## CI Integration

Every pull request runs the engine doctor via `.github/workflows/`:

```yaml
- name: Engine Doctor
  run: python3 tools/engine_doctor.py --json --tests --strict --baseline tools/baseline.json
```

CI fails (non-zero exit) on:
- Any import failure (exit 2)
- New circular dependency not in baseline (exit 3)
- Unexpected test failure (exit 1)
- Required runtime file missing (exit 4)
- Any baseline mismatch in strict mode (exit 5)

The baseline file (`tools/baseline.json`) is committed and defines the known-good state. Passing CI means the engine matches the baseline exactly.

---

## Runtime Guard

When enabled, the engine doctor runs at the start of each pipeline execution as a pre-flight check. A failing pre-flight aborts the run before any data is fetched.

The runtime guard is configured in `config.py`. It uses `--no-import-check` mode (fast, no live imports) to minimize latency at startup.

---

## Current State (as of 2026-04-24)

| Check | Result |
|-------|--------|
| Modules importable | 23 / 23 |
| Tests passing | 802 / 803 |
| Known broken test | `test_sunday_mode_fixture_run_is_end_to_end_and_offline` (pre-existing fixture failure) |
| Audit log | Present |
| Circular dependencies | 2 detected (pre-existing, non-breaking) |

### Known Circular Dependencies

Both are managed via lazy/function-level imports and do not break anything:

- `qualification → flow → qualification`
- `output → delivery → output`

---

## Design Notes

- **No pipeline coupling.** The tool lives in `tools/`. It is not imported by anything in the engine.
- **AST-based graph.** Dependency graph is derived by parsing source files — works even when modules are broken.
- **Zero new dependencies.** Uses only Python standard library (`ast`, `importlib`, `subprocess`, `argparse`) plus what the project already installs.
