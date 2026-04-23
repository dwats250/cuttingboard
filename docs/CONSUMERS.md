# CONSUMERS.md — Contract Consumer Map

Every file that reads from the canonical `PipelineOutputContract` dict (built by `contract.py`).

---

## Contract Builders

| File | Function | Role |
|---|---|---|
| `cuttingboard/contract.py` | `build_pipeline_output_contract()` | Primary builder — translates pipeline objects into contract dict |
| `cuttingboard/contract.py` | `build_error_contract()` | Minimal error-state contract when pipeline fails with exception |

---

## Production Consumers

| File | Access Point | What it reads |
|---|---|---|
| `cuttingboard/runtime.py` | `_write_contract_file()` | Writes full contract to `logs/latest_contract.json` |
| `cuttingboard/runtime.py` | `_write_payload_artifacts()` | Passes contract to `build_report_payload()` → `deliver_json()` / `deliver_html()` |
| `cuttingboard/delivery/payload.py` | `build_report_payload(contract)` | Reads `system_state`, `audit_summary`, `trade_candidates`, `rejections`, `meta` |
| `cuttingboard/delivery/transport.py` | `deliver_json()` / `deliver_html()` | Receives payload derived from contract |
| `cuttingboard/delivery/html_renderer.py` | `render_html(payload)` | Renders HTML via `render_report_from_payload()` |
| `cuttingboard/output.py` | `render_report_from_payload(payload)` | Reads `meta`, `sections`, `run_status` from payload (derived from contract) |

---

## Failure Behaviour

Every consumer must fail loudly on missing or corrupt contract data:

| Consumer | Failure Mode |
|---|---|
| `contract.py / assert_valid_contract()` | `AssertionError` on missing keys, wrong types, bad status |
| `delivery/payload.py / assert_valid_payload()` | `ValueError` on missing keys, wrong types |
| `output.py / render_report_from_payload()` | `ValueError` on unparseable timestamp |
| `delivery/transport.py` | Exception propagates — no silent swallow |

`assert_valid_contract()` must be called immediately after `build_pipeline_output_contract()`. Any consumer receiving a contract dict should call it before reading fields.

---

## FLAGGED

**flow_snapshot — FLAGGED: MISSING DATA SOURCE**

`qualify_all()` accepts a `flow_snapshot: Optional[dict[str, list[FlowPrint]]]` parameter that feeds the PRD-013 flow alignment gate. All three production call sites in `runtime.py` (lines 409, 437, 583) pass `ohlcv=` only. `flow_snapshot` is always `None`. The gate is wired and correct but never supplied live data. Do not add logic to supply it until a data source is identified and tested.

---

## CLI Flags (Verified)

| Flag | Valid Values |
|---|---|
| `--mode` | `live`, `fixture`, `sunday`, `verify`, `prefetch` |
| `--notify-mode` | `premarket`, `orb_trajectory`, `post_orb`, `midmorning`, `power_hour`, `market_close`, `hourly` |

No `--intraday`, `--dry-run`, or other flags found in workflow or production code.
