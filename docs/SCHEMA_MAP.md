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
| `payload["sections"]["spy_observation"]` | dict \| absent | PRD-288; DAILY path only — present iff `build_report_payload(spy_observation=...)` receives the transient observation; JSON-safe mirror incl. the verbatim PRD-271 ORB sub-object (`_project_spy_observation`) |
| `payload["sections"]["market_control_card"]` | dict \| absent | PRD-289; DAILY eligible runs only (halted included, never MODE_SUNDAY) — seven closed-vocabulary cells (`location`/`state`/`permission`/`event`/`transition`/`invalidation`/`candidate_implication`) mirrored from the frozen `MarketControlCard` (`_project_market_control_card`); additive, no required-key/schema change |

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

## gex_snapshot (logs/gex_snapshot.json)

Producer `tools/gex_snapshot.py` is authoritative for the full schema; the
display-only consumer `cuttingboard/delivery/gex_card.py` (PRD-309) reads only
the paths below. The identity-guard constants must match the producer exactly.

| Field path | Type | Notes |
|---|---|---|
| `schema_version` | int | strict `== 1` (bool-first: `True` rejected) |
| `source` | string | identity guard `== "cboe_delayed_quotes"` |
| `data_delay` | string | identity guard `== "~15 min delayed (REPORTED; Cboe delayed_quotes posture)"` |
| `gex_total_1pct_usd` | float | net GEX, signed; rendered `/1e9` as `$B` |
| `spot.value` | float > 0 | distance basis; suppresses if not finite/positive |
| `fetched_at_utc` | ISO-8601 tz-aware | capture clock; freshness (STALE_MAX 24h) + absolute ET display; naive/future → suppress |
| `dominant_net_gamma.{strike,reason}` | float\|null / null\|token | REQUIRED anchor; null strike (reason `all_net_gamma_zero`) → whole card suppressed |
| `call_wall.{strike,reason}` | float\|null / null\|token | optional row; null strike (`no_eligible_calls`/`no_nonzero_call_gex`) → row omitted |
| `put_wall.{strike,reason}` | float\|null / null\|token | optional row; null strike (`no_eligible_puts`/`no_nonzero_put_gex`) → row omitted |
| `zero_dte.{share,reason}` | float[0,1]\|null / null\|token | optional row; null share (`zero_abs_gex_denominator`) → row omitted; honest 0.0 shown |

DISPLAY-ONLY: no `cuttingboard` decision module reads this artifact; the card
suppresses to a byte-identical baseline dashboard on absent/stale/invalid
(PRD-309 R1/R17-R20).

---

## watchlist_snapshot (logs/watchlist_snapshot.json)

Producer `cuttingboard/watchlist_sidecar.py:build_watchlist_snapshot`; the
display-only consumer `cuttingboard/delivery/movement_card.py` (PRD-311, the
MARKET MOVEMENT card) reads the paths below and suppresses the whole card
(byte-identical baseline) on any contract violation.

| Field path | Type | Notes |
|---|---|---|
| `schema_version` | int | strict `== 2` (bool-first; PRD-311 bump from 1) |
| `source` | string | identity guard `== "watchlist"` |
| `generated_at` | ISO-8601 tz-aware\|null | capture clock; card requires tz-aware (naive/malformed → suppress); rendered `captured HH:MM ET` |
| `symbols` | dict | MUST contain exactly the 12 enabled registry symbols (full-12 identity; missing/extra → suppress) |
| `symbols[S].symbol` | string | must equal its key |
| `symbols[S].sector_theme` | string | legacy coarse theme (unchanged) |
| `symbols[S].watch_reason` | string | registry rationale (unchanged) |
| `symbols[S].current_price` | float\|null | `NormalizedQuote.price` passthrough (unchanged) |
| `symbols[S].daily_change_pct` | float\|null | `round(pct_change_decimal*100, 1)` or null (n/a hook; NEVER fabricated 0.0); honest 0.0 shown as `0.0%` |
| `symbols[S].primary_group` | string | fine registry group ∈ {INDEX, METALS, ENERGY, TECH, HIGH_BETA}; unknown → suppress |
| `symbols[S].registry_index` | int | 0-based enabled-registry position; unique in-range; drives group-internal order |

DISPLAY-ONLY: no `cuttingboard` decision module reads this artifact. Observe-only
UCO/GOOG (PRD-311) reach the rows only via the runtime merge at the hourly write
seam and never any decision surface.

---

## price_bars_snapshot (logs/price_bars_snapshot.json)

Producer `cuttingboard/runtime/__init__.py:_write_price_bars_snapshot` (path
constant `PRICE_BARS_PATH`), co-written at BOTH existing sidecar seams — the
hourly block and the daily MODE_LIVE block — from the frames
`_collect_trend_structure_history` already bound for the trend sidecar. No new
fetch, no new provider. CONSUMER: none — the operator setup chart lands in
PRD-321.

| Field path | Type | Notes |
|---|---|---|
| `schema_version` | int | `1` |
| `generated_at` | ISO-8601 tz-aware | the run's `run_at_utc`, verbatim |
| `source.producer` | string | `"hourly"` \| `"daily"` — which seam wrote this copy |
| `source.provider` | string | `"yfinance"` |
| `source.interval` | string | `"1d"` — the ruled Q1 extension point for deferred intraday |
| `source.adjusted` | bool | `true` |
| `columns` | list[string] | exactly `["date","open","high","low","close","volume"]` — the bar-row order |
| `symbols` | dict | subset of `config.TREND_STRUCTURE_SYMBOLS`; a symbol whose frame is absent, malformed, or has zero completed rows is OMITTED (never partial) |
| `symbols[S].as_of` | `YYYY-MM-DD` | session date of the LAST written bar — the reader's age basis |
| `symbols[S].bars` | list[list] | <=40 rows `["YYYY-MM-DD", open, high, low, close, volume]`; OHLC float, volume int |

COMPLETED SESSIONS ONLY: rows are filtered to session date <=
`time_utils.most_recent_completed_session_date(generated_at)` FIRST, then the
last 40 are taken — so the window slides back rather than shrinking. Between the
ET close and 00:00 UTC that cutoff is still the prior weekday; that is the ruled
Q5(b) behavior, and `as_of` carries it.

DISPLAY-ONLY: no `cuttingboard` decision module reads this artifact (PRD-320 R6).
Transport: hourly force-adds it; NO workflow restores it from `publish` — it is
co-produced fresh state, never revived.

---

## MARKET STATE panel (PRD-312) — introduces NO new schema

`cuttingboard/delivery/market_state_panel.py` is a display-only five-axis panel
(ENVIRONMENT / PERMISSION / POSITIONING / PARTICIPATION / EVENT RISK). It defines
no artifact and no new field: it reads only carriers the renderer already
resolves — `summary.market_regime`, `run.permission` (run-first), the resolved
`GexCard` / `MovementCard` objects, and the red-folder view. It never reads a raw
snapshot (keeps `gex_card` the sole `gex_snapshot` reader). Related cut: the trend
record's `daily_change_pct` field (produced by `trend_structure._build_record`,
its only reader the retired Macro-Tape tradables arrow) is REMOVED — distinct from
the watchlist row's `daily_change_pct` above (PRD-311), which is unchanged.

---

## Usage rules

- For **contract** fields, verify against `cuttingboard/contract_types.py`
  (the typed schema) — not this map. This map only carries the untyped
  artifacts (payload, market_map, run, gex_snapshot) and the `dict[str, Any]` interiors
  above.
- Before adding a field to a PRD, verify it appears in this map or confirm it
  in source.
- If a field path is not in this map and cannot be confirmed, mark it
  `[UNVERIFIED]` in the PRD.
- After verifying an uncertain field, add it here.
