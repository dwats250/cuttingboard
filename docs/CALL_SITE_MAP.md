# CALL_SITE_MAP.md — Key Function Boundaries

Reference for PRD reviewers and implementers. Use to locate injection points
without full-file reads. Update when new high-value boundaries are identified.

---

## runtime.py

| Function | Line | Purpose |
|---|---|---|
| `cli_main` | 256 | Entry point; resolves command and runtime mode |
| `_run_pipeline` | 634 | Orchestrates regime → qualification → output → artifacts |
| `_resolve_effective_mode` | 1879 | Handles live/sunday mode resolution |

---

## cuttingboard/contract.py

| Function | Line | Purpose |
|---|---|---|
| `build_pipeline_output_contract` | 52 | Assembles and returns the canonical contract dict |

---

## cuttingboard/delivery/payload.py

| Function | Line | Purpose |
|---|---|---|
| `build_report_payload` | 21 | Converts contract dict to dashboard payload dict |

---

## cuttingboard/delivery/dashboard_renderer.py

| Function | Line | Purpose |
|---|---|---|
| `render_dashboard_html` | 511 | Renders full dashboard HTML from payload + run artifacts |

Note: the candidate board reads `market_map["symbols"]` directly, not payload
candidates.

---

## cuttingboard/output.py

| Function | Line | Purpose |
|---|---|---|
| `build_notification_message` | 811 | Formats Telegram alert title and body from contract |

---

## Macro-tape metals (gold/silver) surface — PRD-211

The `gold`/`silver` macro_drivers are **display-only** (front-month futures
`GC=F`/`SI=F`), fenced from every decision path. Producer → display call graph:

| Function / symbol | File:Line | Purpose |
|---|---|---|
| `_build_macro_drivers` | contract.py:502 | Producer; builds `macro_drivers` per driver. Optional drivers (`oil`/`gold`/`silver`, set at contract.py:59) **silently skip** on fetch failure (`continue`, contract.py:510-511 / 521-522) → key absent (write is FRESH, so absence renders `N/A`, not a stale value) |
| `_write_macro_snapshot` | runtime/__init__.py:1962 | Writes `logs/macro_drivers_snapshot.json` (FRESH, atomic). Renderer fallback fires only when the **whole** macro_drivers dict is empty (all-or-nothing), never per-key |
| `_build_tape_slots` / `_build_tape_value_slots` | dashboard_renderer.py:1036 / 1091 | Render the tape arrow/value per slot; absent driver key → `N/A` (per-key `.get`) |
| `_format_tape_value` | dashboard_renderer.py:1067 | Value formatting dispatch, keyed on slot **label** (`XAU`→.1f, `XAG`→.2f) |
| `_macro_row` | notifications/__init__.py:89 | Notification tape line per slot; visible text is `slot.display` (`GC`/`SI`), level keyed on slot label |
| **FENCE** `_COMPONENT_FIELDS` | macro_pressure.py:25 | macro_pressure components — excludes gold/silver (no decision read) |
| **FENCE** `MACRO_BIAS_DRIVERS` | macro_tape_layout.py:93 | bias-vote drivers — excludes gold/silver (no decision read) |
| `TapeSlot.display` | macro_tape_layout.py:17 | Visible label (`GC`/`SI` for metals); `label`/`data-symbol` stay `XAU`/`XAG` (PRD-211) |

---

## Usage rules

- Before broad file scan, check this map for the target function's line number.
- If the target function is listed here, use `offset+limit` Read to go directly
  to it.
- If a function is not here but is discovered during implementation, add it.
- Line numbers drift as code changes; re-verify with grep if the entry is more
  than one PRD old.
