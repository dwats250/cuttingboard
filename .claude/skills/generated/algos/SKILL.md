---
name: algos
description: "Skill for the Algos area of cuttingboard. 5 symbols across 1 files."
---

# Algos

5 symbols | 1 files | Cohesion: 59%

## When to Use

- Working with code in `algos/`
- Understanding how detect_breakout, execute_trade work
- Modifying algos-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `algos/orb_reference.py` | detect_breakout, execute_trade, _prepare_day_frame, _normalize_frame, _iso |

## Entry Points

Start here when exploring this area:

- **`detect_breakout`** (Function) — `algos/orb_reference.py:40`
- **`execute_trade`** (Function) — `algos/orb_reference.py:79`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `detect_breakout` | Function | `algos/orb_reference.py` | 40 |
| `execute_trade` | Function | `algos/orb_reference.py` | 79 |
| `_prepare_day_frame` | Function | `algos/orb_reference.py` | 202 |
| `_normalize_frame` | Function | `algos/orb_reference.py` | 236 |
| `_iso` | Function | `algos/orb_reference.py` | 271 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _normalize_frame` | cross_community | 6 |
| `Main → _iso` | cross_community | 5 |

## How to Explore

1. `gitnexus_context({name: "detect_breakout"})` — see callers and callees
2. `gitnexus_query({query: "algos"})` — find related execution flows
3. Read key files listed above for implementation details
