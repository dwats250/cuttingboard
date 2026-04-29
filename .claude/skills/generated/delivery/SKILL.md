---
name: delivery
description: "Skill for the Delivery area of cuttingboard. 4 symbols across 2 files."
---

# Delivery

4 symbols | 2 files | Cohesion: 55%

## When to Use

- Working with code in `cuttingboard/`
- Understanding how test_run_delta_correct_previous_selection_by_timestamp work
- Modifying delivery-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `cuttingboard/delivery/dashboard_renderer.py` | _load_json, _req, _resolve_previous_run |
| `tests/test_dashboard_renderer.py` | test_run_delta_correct_previous_selection_by_timestamp |

## Entry Points

Start here when exploring this area:

- **`test_run_delta_correct_previous_selection_by_timestamp`** (Function) — `tests/test_dashboard_renderer.py:528`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_run_delta_correct_previous_selection_by_timestamp` | Function | `tests/test_dashboard_renderer.py` | 528 |
| `_load_json` | Function | `cuttingboard/delivery/dashboard_renderer.py` | 46 |
| `_req` | Function | `cuttingboard/delivery/dashboard_renderer.py` | 55 |
| `_resolve_previous_run` | Function | `cuttingboard/delivery/dashboard_renderer.py` | 79 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _req` | cross_community | 4 |
| `Main → _load_json` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_run_delta_correct_previous_selection_by_timestamp"})` — see callers and callees
2. `gitnexus_query({query: "delivery"})` — find related execution flows
3. Read key files listed above for implementation details
