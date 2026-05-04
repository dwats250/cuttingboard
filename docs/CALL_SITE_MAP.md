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

## Usage rules

- Before broad file scan, check this map for the target function's line number.
- If the target function is listed here, use `offset+limit` Read to go directly
  to it.
- If a function is not here but is discovered during implementation, add it.
- Line numbers drift as code changes; re-verify with grep if the entry is more
  than one PRD old.
