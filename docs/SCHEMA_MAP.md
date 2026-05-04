# SCHEMA_MAP.md — Canonical Field Paths

Reference for PRD authors and reviewers. Verify field paths here before
proposing new fields. Update when new canonical fields are introduced.

---

## contract (latest_hourly_contract.json)

| Field path | Type | Notes |
|---|---|---|
| `contract["outcome"]` | string | `TRADES \| NO TRADE \| HALT` |
| `contract["status"]` | string | run status derived from outcome + regime |
| `contract["generated_at"]` | string | ISO timestamp (UTC) |
| `contract["session_date"]` | string | YYYY-MM-DD |
| `contract["mode"]` | string | runtime mode |
| `contract["schema_version"]` | string | |
| `contract["system_state"]` | dict | always present |
| `contract["system_state"]["tradable"]` | bool | |
| `contract["system_state"]["stay_flat_reason"]` | string \| null | present when posture is STAY_FLAT or HALT |
| `contract["system_state"]["session_type"]` | string \| absent | conditional; only injected for SUNDAY_PREMARKET runs (runtime.py:911) |
| `contract["regime"]` | dict | |
| `contract["trade_candidates"]` | list | |
| `contract["rejections"]` | list | |
| `contract["macro_drivers"]` | dict | |
| `contract["market_context"]` | dict | |

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

- Before adding a field to a PRD, verify it appears in this map or confirm it
  in source.
- If a field path is not in this map and cannot be confirmed, mark it
  `[UNVERIFIED]` in the PRD.
- After verifying an uncertain field, add it here.
