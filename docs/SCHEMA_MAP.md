# SCHEMA_MAP.md — Canonical Field Paths

Reference for PRD authors and reviewers. Verify field paths here before
proposing new fields. Update when new canonical fields are introduced.

---

## contract (latest_hourly_contract.json)

**The authoritative contract schema is `cuttingboard/contract_types.py`
(PRD-237/238).** Top level = `PipelineContract`; `system_state` =
`SystemState`; `trade_candidates[i]` = `ContractCandidate` (with
`DecisionTrace` / `OvernightPolicyDecision` sub-blocks). Field names,
types, and required-vs-conditional presence (`NotRequired`) live there,
kept honest by the sync guards in `tests/test_contract_types.py` — do not
re-derive or restate them here. For presence semantics (which keys are
runtime-injected, Sunday-only, EOD-only), read the module docstring and
per-key comments in `contract_types.py`.

What the TypedDicts intentionally do NOT capture (typed `dict[str, Any]`),
recorded here because this map is the only home for it:

| Field path | Type | Notes |
|---|---|---|
| `contract["macro_drivers"]` | dict | per-driver blocks keyed by driver name (`volatility`, `dollar`, `rates`, `bitcoin`, `oil`, `gold`, `silver`); built by `_build_macro_drivers` (contract.py:502) |
| `contract["macro_drivers"][driver]["symbol"]` | string | source quote symbol (e.g. `gold`→`GC=F`, `silver`→`SI=F`; map at contract.py:50) |
| `contract["macro_drivers"][driver]["level"]` | float | latest price |
| `contract["macro_drivers"][driver]["change_pct"]` | float | percent change (×100) |
| `contract["macro_drivers"][driver]["change_bps"]` | float \| absent | rates only |
| `contract["macro_drivers"]["gold" \| "silver"]` | dict \| absent | OPTIONAL drivers (contract.py:59); the key is **absent** when the `GC=F`/`SI=F` fetch fails (silent skip, contract.py:510/521) → renderer shows `N/A` per-key (dashboard_renderer.py `_build_tape_value_slots`). DISPLAY-ONLY: front-month **futures**, fenced from the decision path (excluded from `_COMPONENT_FIELDS` macro_pressure + `MACRO_BIAS_DRIVERS` vote). Visible tape label is `GC`/`SI` (PRD-211); the slot id / `data-symbol` stays `XAU`/`XAG` |

Consumer notes that outlive the retired field table (semantics, not shape):

- `trade_candidates[i]["entry"]` / `["stop"]` — finite-float-asserted for
  ALLOW_TRADE (`_assert_trade_candidates_valid`). Renderer consumer:
  level-diagram anchor + entry→stop risk band (PRD-223/224) via
  `_load_contract_entry_context`.
- `trade_candidates[i]["target"]` — NOT rendered on the level diagram by
  design (description-not-prediction).
- `system_state["stay_flat_reason"]` — non-null when posture is STAY_FLAT
  or HALT.
- `outcome` — `TRADES | NO TRADE | HALT`.

---

## payload (latest_hourly_payload.json)

| Field path | Type | Notes |
|---|---|---|
| `payload["meta"]` | dict | always present |
| `payload["meta"]["timestamp"]` | string | ISO timestamp; sourced from contract["generated_at"] |
| `payload["meta"]["symbols_scanned"]` | int | qualified + rejected + watchlist count |
| `payload["meta"]["session_type"]` | string \| absent | conditional; only present when session_type exists in system_state |
| `payload["meta"]["fixture_mode"]` | bool \| absent | conditional; only present when fixture_mode=True (payload.py:106–107) |

---

## market_map (market_map.json)

| Field path | Type | Notes |
|---|---|---|
| `market_map["symbols"]` | dict | keyed by symbol string |
| `market_map["symbols"][sym]["grade"]` | string | e.g. `A`, `B`, `F` |
| `market_map["symbols"][sym]["bias"]` | string | e.g. `BULLISH`, `BEARISH`, `NEUTRAL` |
| `market_map["symbols"][sym]["trade_framing"]` | dict | |
| `market_map["symbols"][sym]["trade_framing"]["entry"]` | string | narrative entry guidance |
| `market_map["symbols"][sym]["trade_framing"]["upgrade"]` | string | |
| `market_map["symbols"][sym]["trade_framing"]["downgrade"]` | string | |
| `market_map["symbols"][sym]["invalidation"]` | list[str] | list of invalidation conditions |

---

## run artifact (latest_hourly_run.json)

| Field path | Type | Notes |
|---|---|---|
| `run["status"]` | string | mirrors contract status |
| `run["outcome"]` | string | mirrors contract outcome |

---

## Usage rules

- For **contract** fields, verify against `cuttingboard/contract_types.py`
  (the typed schema) — not this map. This map only carries the untyped
  artifacts (payload, market_map, run) and the `dict[str, Any]` interiors
  above.
- Before adding a field to a PRD, verify it appears in this map or confirm it
  in source.
- If a field path is not in this map and cannot be confirmed, mark it
  `[UNVERIFIED]` in the PRD.
- After verifying an uncertain field, add it here.
