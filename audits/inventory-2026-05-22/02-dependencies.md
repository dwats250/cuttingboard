# 02 — Dependency Analysis

## Internal dependency graph

Direction: `A → B` means A imports B. Edges derived by grep across `cuttingboard/*.py`. Indirect / transitive edges omitted. `__init__.py` re-exports are folded into their package name.

```
__main__              → runtime
runtime               → config, time_utils, audit, contract, chain_validation,
                        derived, ingestion, intraday_state_engine, market_map,
                        trend_structure, watchlist_sidecar, trade_visibility,
                        trade_explanation, market_map_lifecycle, evaluation,
                        performance_engine, execution_policy, macro_pressure,
                        normalization
alert_runner          → output
output                → config, time_utils, audit, chain_validation, options,
                        qualification, regime, universe, validation, watch
contract              → config, time_utils, trade_decision, overnight_policy,
                        qualification, regime
notifications/__init__ → delivery.macro_tape_layout, normalization,
                        qualification, regime, universe, validation, watch,
                        notifications.formatter
notifications/formatter → qualification, regime, validation, watch
delivery/dashboard_renderer → config, delivery.macro_tape_layout,
                              macro_pressure, trade_decision
delivery/html_renderer → delivery.dashboard_renderer
delivery/transport    → delivery.payload
qualification         → config, time_utils, derived, flow, regime, structure
options               → config, derived, normalization, qualification, regime,
                        structure
trade_decision        → chain_validation, options, qualification
trade_explanation     → execution_policy, trade_decision, trade_visibility
trade_thesis          → qualification, structure, trade_decision
trade_visibility      → execution_policy, trade_decision
trade_policy          → correlation
entry_quality         → qualification, structure, trade_decision
invalidation          → trade_decision
execution_policy      → config, trade_decision
overnight_policy      → config, time_utils
correlation           → config
derived               → config, ingestion, normalization
structure             → config, derived, normalization
regime                → config, normalization
normalization         → config, ingestion
validation            → config, ingestion, normalization
universe              → config
flow                  → config, universe
ingestion             → config
evaluation            → config, audit, ingestion
chain_validation      → normalization, options
market_map            → derived, normalization, regime, structure, watch
watch                 → derived, ingestion, regime, structure
intraday_state_engine → confirmation
sector_router         → qualification
trend_structure       → normalization
watchlist_sidecar     → normalization
run_intraday          → derived, ingestion, notifications, normalization,
                        output, regime, validation
notify_test           → config, output
audit                 → options, qualification, regime, trade_decision,
                        validation, watch
```

### Inbound-count (modules imported by N other production modules)

```
0   notify_test, time_utils*, run_intraday
1   alert_runner, confirmation, evaluation, manual_journal, notifications.formatter,
    review_scorecard
2   delivery.html_renderer, entry_quality, intraday_state_engine,
    notifications.state, performance_engine, sector_router, trade_explanation,
    trade_policy, trade_thesis, trend_structure, watchlist_sidecar
3   delivery.fixtures, delivery.macro_tape_layout, invalidation, macro_pressure,
    market_map_lifecycle, overnight_policy, reports.levels, reports.postmarket
4   flow, reports.premarket, trade_visibility
5   correlation, delivery.transport, market_map, universe
6   execution_policy
7   audit, contract
8   notifications.hourly_slot
19  config*
5   time_utils* (corrected: imported via `from cuttingboard import config, time_utils`)
```

\* `config` and `time_utils` undercount in the raw grep because of the `from cuttingboard import config, time_utils` pattern; verified counts are 19 / 5.

### Circular imports

None detected by inspection. `runtime.py` is a sink; leaf modules (`config`, `time_utils`, `normalization`, `ingestion`) have no internal imports or only depend on lower layers.

## External dependencies — declared vs. used

Source: `pyproject.toml`.

### Declared runtime (`[project] dependencies`)

| Package | Imported in `cuttingboard/` | Notes |
|---|---|---|
| `yfinance>=0.2.40` | ✅ `ingestion.py`, others (×2 direct imports) | Primary quote/OHLCV source. |
| `pandas>=2.0.0` | ✅ 8 modules | Heavy use. |
| `numpy>=1.26.0` | ⚠️ — not directly imported in `cuttingboard/` | Pulled in transitively by pandas; no `import numpy` found in production package. Likely transitive-only. **Candidate for removal if no test/script directly imports it** — verify before cutting. |
| `requests>=2.31.0` | ✅ `ingestion.py`, `output.py` (Telegram, Polygon HTTP) | |
| `python-dotenv>=1.0.0` | ✅ via `dotenv` import in `config.py` | |
| `pyarrow>=14.0.0` | ⚠️ — not directly imported | Required by pandas to read/write parquet (OHLCV cache). Transitive-only direct usage. Keep, but flag rationale. |

### Declared dev (`[project.optional-dependencies] dev`)

| Package | Used | Notes |
|---|---|---|
| `pytest>=7.0.0` | ✅ | Test runner. |
| `pytest-mock>=3.0.0` | needs verification | Not grep-confirmed in tests; ambiguous. |
| `ruff>=0.4.0` | ✅ | Referenced in `pre_push_check.sh`. |

### Declared optional (`[project.optional-dependencies] chain`)

| Package | Used | Notes |
|---|---|---|
| `yahooquery>=2.3.0` | ✅ `chain_validation.py` (fallback path) | Conditional import; optional dependency intentional. |

### Imports without a declared dependency

External top-level names imported by `cuttingboard/`:

```
argparse, collections, concurrent, contextlib, copy, dataclasses, datetime,
dotenv, enum, hashlib, html, json, logging, math, os, pandas, pathlib,
requests, statistics, subprocess, sys, threading, time, tomllib, types,
typing, unittest, yfinance, zoneinfo
```

All non-stdlib names (`dotenv`, `pandas`, `requests`, `yfinance`) are declared. **No undeclared third-party imports detected.**

`tools/macro_collector.py` is a sidecar (PRD-139); it calls Anthropic via raw HTTP through `requests` (no `anthropic` SDK declared/imported), but it's outside the `cuttingboard/` package.

### Flags

- **`numpy`** declared but no direct `import numpy` in the package source. Investigate before removal — may be used in tests, scripts, or via `pandas.DataFrame.values` patterns that don't surface as imports.
- **`pyarrow`** declared but no direct import. Required transitively by pandas parquet I/O (`data/cache/*.parquet`). Likely necessary; document rationale.
- **`pytest-mock`** declared but no grep hit for `mocker` or `pytest_mock` in `tests/`. Unable to determine whether actually used — possible drop candidate.

## Cross-package note: `algos/` and `backtesting/`

`algos/orb_reference.py` and `backtesting/run_orb_backtest.py` live outside the `cuttingboard/` package. They appear to be standalone scripts. `algos/orb_reference.py` is consumed by `tests/test_orb_reference.py`. `backtesting/run_orb_backtest.py` has no test coverage detected. Neither module is imported by any production module under `cuttingboard/`.
