---
name: tools
description: "Skill for the Tools area of cuttingboard. 33 symbols across 1 files."
---

# Tools

33 symbols | 1 files | Cohesion: 92%

## When to Use

- Working with code in `tools/`
- Understanding how g, r, y work
- Modifying tools-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tools/engine_doctor.py` | g, r, y, c, b (+28) |

## Entry Points

Start here when exploring this area:

- **`g`** (Function) — `tools/engine_doctor.py:46`
- **`r`** (Function) — `tools/engine_doctor.py:47`
- **`y`** (Function) — `tools/engine_doctor.py:48`
- **`c`** (Function) — `tools/engine_doctor.py:49`
- **`b`** (Function) — `tools/engine_doctor.py:50`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `g` | Function | `tools/engine_doctor.py` | 46 |
| `r` | Function | `tools/engine_doctor.py` | 47 |
| `y` | Function | `tools/engine_doctor.py` | 48 |
| `c` | Function | `tools/engine_doctor.py` | 49 |
| `b` | Function | `tools/engine_doctor.py` | 50 |
| `d` | Function | `tools/engine_doctor.py` | 51 |
| `build_dep_graph` | Function | `tools/engine_doctor.py` | 142 |
| `build_reverse_graph` | Function | `tools/engine_doctor.py` | 162 |
| `dfs` | Function | `tools/engine_doctor.py` | 175 |
| `find_cycles` | Function | `tools/engine_doctor.py` | 197 |
| `check_imports` | Function | `tools/engine_doctor.py` | 224 |
| `check_runtime_files` | Function | `tools/engine_doctor.py` | 238 |
| `run_tests` | Function | `tools/engine_doctor.py` | 264 |
| `load_baseline` | Function | `tools/engine_doctor.py` | 276 |
| `main` | Function | `tools/engine_doctor.py` | 575 |
| `all_downstream` | Function | `tools/engine_doctor.py` | 211 |
| `build_report` | Function | `tools/engine_doctor.py` | 289 |
| `escalate` | Function | `tools/engine_doctor.py` | 307 |
| `_determine_exit_code` | Function | `tools/engine_doctor.py` | 70 |
| `_short` | Function | `tools/engine_doctor.py` | 115 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Dfs` | intra_community | 4 |
| `Main → _short` | intra_community | 4 |
| `Main → _extract_deps` | intra_community | 3 |
| `Main → R` | intra_community | 3 |

## How to Explore

1. `gitnexus_context({name: "g"})` — see callers and callees
2. `gitnexus_query({query: "tools"})` — find related execution flows
3. Read key files listed above for implementation details
