# System Logic Map — cuttingboard

This document audits the decision logic, module responsibilities, sidecar boundaries, and
mutation rules of the cuttingboard pipeline. It is documentation-only. No source behavior
is changed here.

---

## Runtime Decision Flow

Every run is orchestrated by `runtime.py:cli_main()` → `execute_run()` → `_run_pipeline()`.
The pipeline executes in strict layer order:

```
1. config.py             — load constants and secrets from .env
2. ingestion.py          — fetch RawQuote (yfinance primary, Polygon fallback)
3. normalization.py      — produce NormalizedQuote (pct_change, UTC, units)
4. validation.py         — hard gate: HALT_SYMBOL failure stops the pipeline
5. derived.py            — EMA9/21/50, ATR14 (Wilder RMA), momentum_5d, volume_ratio
6. structure.py          — classify each symbol: TREND/PULLBACK/BREAKOUT/REVERSAL/CHOP
7. regime.py             — 8-vote model → RISK_ON/RISK_OFF/NEUTRAL/CHAOTIC + posture
8. qualification.py      — 9–11 gates per candidate (4 hard, 5–7 soft)
9. options.py            — spread selection, DTE, strike distance
10. chain_validation.py  — live chain liquidity gate (OI, spread %, bid/ask sanity)
11. contract.py          — assemble pipeline output contract (build_pipeline_output_contract)
    output.py            — render to terminal/markdown/Telegram
    delivery/            — payload, dashboard HTML, transport
    audit.py             — append one record to logs/audit.jsonl
```

**Output contract:** Every run produces exactly one outcome:
- `TRADE` — defined in `output.py:OUTCOME_TRADE`
- `NO_TRADE` — defined in `output.py:OUTCOME_NO_TRADE`
- `HALT` — defined in `output.py:OUTCOME_HALT`

STAY_FLAT posture short-circuits all per-symbol qualification; no gates run.

---

## Decision-Affecting Modules

These modules can influence whether the outcome is TRADE, NO_TRADE, or HALT,
or which candidates qualify and at what position size.

| Module | Role in decision |
|--------|-----------------|
| `validation.py` | HALT_SYMBOL failure → pipeline halts entirely |
| `regime.py` | computes posture (STAY_FLAT → no trades possible) and confidence |
| `qualification.py` | hard gates 1–4 reject immediately; soft gates 5–11 build WATCHLIST or REJECT |
| `execution_policy.py` | session-level permission state; can block LONG or SHORT entries |
| `trade_policy.py` | policy context evaluation; can force NO_TRADE for a candidate |
| `trade_decision.py` | ALLOW_TRADE / block decision per candidate |
| `trade_thesis.py` | thesis gate; rejects candidates with insufficient conviction |
| `invalidation.py` | invalidation gate; rejects candidates whose setup is broken |
| `entry_quality.py` | entry quality gate; rejects chase or low-quality entries |
| `overnight_policy.py` | applies overnight carry rules |
| `contract.py` | assembles `build_pipeline_output_contract`; the final decision record |
| `runtime.py` | orchestrates all layers; computes `_kill_switch` which can force HALT |

**Fields that are decision-affecting** (changing them changes the outcome):
- `regime.posture`, `regime.confidence`, `regime.classification`
- `qualification.hard_gate_result`, `qualification.soft_gate_results`
- `trade_decision.decision` (`ALLOW_TRADE` / block)
- `contract.outcome` (`TRADE` / `NO_TRADE` / `HALT`)
- `contract.trade_candidates` (list of qualified candidates)
- `contract.system_halted` (bool)

---

## Display-Only Modules

These modules consume existing decisions and render or deliver them.
They must not derive new trade logic or mutate qualification outcomes.

| Module | Role |
|--------|------|
| `delivery/payload.py` | `build_report_payload` — transforms contract into dashboard payload; render only |
| `delivery/dashboard_renderer.py` | reads payload + run + market_map artifacts; renders HTML; no decision logic |
| `delivery/transport.py` | writes JSON/HTML to disk paths; delivery only |
| `output.py` | `render_report`, `send_notification` — terminal and Telegram rendering; no decision logic |
| `notifications/formatter.py` | formats ntfy alert messages; render only |
| `trade_explanation.py` | builds human-readable explanations of existing decisions; no new logic |
| `trade_visibility.py` | builds near-miss/watchlist visibility map from existing qualification data |
| `market_map.py` | builds symbol-level market context (fib levels, watch zones); no qualification gates |
| `review_scorecard.py` | post-trade review scoring; downstream evaluation only |
| `performance_engine.py` | reads `evaluation.jsonl` and computes performance summary; no pipeline decisions |

**Fields that are display-only** (changing them does not change the outcome):
- `contract.market_context`, `contract.macro_drivers` (display fields)
- payload fields built by `delivery/payload.py`
- market_map grades (used for display tiers; not qualification gates)
- run summary metadata (`run_at_utc`, `run_id`, `generation_id`)

---

## Sidecar Boundary Rules

A **sidecar** is any module, job, or artifact that runs alongside the main pipeline
without participating in the TRADE / NO_TRADE / HALT decision.

**Sidecars are permitted to:**
- Read existing artifacts (payload, contract, market_map, audit records)
- Write new sidecar-specific artifacts in separate paths
- Render supplementary output for human review

**Sidecars must not mutate:**
- contracts
- payloads
- trade decisions
- qualification gates
- market_map grades
- notifications
- existing dashboard artifacts

Any change to a protected boundary requires an explicit PRD that scopes the mutation.

**Current sidecar-like artifacts:**
- `logs/market_map.json` — built from symbol OHLCV data; used by dashboard renderer for display;
  not a qualification input (market_map grades are display-only tiers, not gates)
- `logs/macro_drivers_snapshot.json` — fallback snapshot for dashboard renderer; display only
- `logs/evaluation.jsonl` — downstream performance evaluation; no pipeline feedback
- `logs/performance_summary.json` — aggregated performance; no pipeline feedback

---

## Forbidden Mutation Paths

The following changes require an explicit new PRD with clear scope and fail conditions.
No agent, sidecar, or downstream process may make these changes without a PRD:

- Sidecars must not mutate contracts — `contract.py:build_pipeline_output_contract` output is final
- Sidecars must not mutate payloads — `delivery/payload.py:build_report_payload` output is final
- Sidecars must not mutate trade decisions — `trade_decision.py:TradeDecision` is set during qualification
- Sidecars must not mutate qualification gates — hard/soft gate logic in `qualification.py` is protected
- Sidecars must not mutate market_map grades — grade tiers in `market_map.py` are display-only; changing
  them to affect qualification is a forbidden path without a PRD
- Sidecars must not mutate notifications — `notifications/formatter.py` and `output.py` send behavior
  is protected; adding/removing notification events requires a PRD
- Sidecars must not mutate existing dashboard artifacts — `ui/dashboard.html`, `ui/index.html`,
  `reports/output/dashboard.html` content and schema are protected; changes require a PRD

---

## Future Sidecar Guidance

The following sidecars are planned but not yet implemented. This list is illustrative,
not exhaustive. None of these are implemented by this document.

When introducing a new sidecar:
1. Write a PRD scoping exactly what the sidecar reads, what it writes, and confirming it
   does not touch any forbidden mutation path.
2. The sidecar must write to a new artifact path that does not shadow any existing artifact.
3. The sidecar must not be called from within the main decision pipeline.
4. The sidecar may be scheduled independently or triggered post-run.
5. Tests for the sidecar must isolate all artifact writes to `tmp_path`.

**Planned sidecars (illustrative):**

| Sidecar | Reads | Would write |
|---------|-------|-------------|
| Sunday report | `logs/audit.jsonl`, `logs/market_map.json` | sidecar artifact (TBD) |
| Trend structure | OHLCV data, `logs/market_map.json` | sidecar artifact (TBD) |
| Custom watchlist | user config, `logs/market_map.json` | sidecar artifact (TBD) |
| Calendar context | external calendar source | sidecar artifact (TBD) |
| News context | external news source | sidecar artifact (TBD) |
| Daily brief / recap | `logs/audit.jsonl`, `logs/latest_hourly_run.json` | sidecar artifact (TBD) |
