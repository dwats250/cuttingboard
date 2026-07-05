# Cuttingboard — System Architecture

This document describes the system as the code executes it. The source of
truth for stage order is `cuttingboard/runtime/__init__.py::_run_pipeline`;
if this document and that function disagree, the function wins and this
document is the bug.

---

## What This System Does

Cuttingboard is a deterministic market interpretation and trade qualification
engine. Every run produces one of three terminal states: **TRADE**,
**NO TRADE**, or **HALT**. It describes and qualifies; it never predicts
(see `VISION.md` non-goals).

CLI entrypoints (`python -m cuttingboard` → `runtime.cli_main`):

- `python -m cuttingboard` — live mode (default)
- `python -m cuttingboard --mode fixture --fixture-file PATH` — deterministic fixture mode
- `python -m cuttingboard --mode sunday` — Sunday premarket context (no fetch, forced STAY_FLAT framing)
- `python -m cuttingboard --mode verify --file PATH` — run-summary verification only (no pipeline)
- `python -m cuttingboard --mode prefetch` — L1–L4 warm-up (fetch/normalize/validate/derive; no report, no notification)
- `--notify-mode` and `--date` modify any pipeline-running mode

Separate hourly entrypoint: `python -m cuttingboard.alert_runner` (PRD-141)
runs the slot-idempotent hourly alert path (`runtime._execute_notify_run`),
which builds its own hourly contract/summary/payload artifacts.

Before any pipeline-running mode (live, fixture, sunday), `cli_main` calls
`_run_engine_health_gate` — an opt-in (`runtime_gate_enabled` in config)
engine_doctor check that aborts the run on failure. Verify and prefetch
return before the gate.

---

## The Pipeline, In Execution Order

`runtime.execute_run` wraps `_run_pipeline` and owns artifact persistence and
the error path. `_run_pipeline` runs these stages in this order:

### 1. Ingest → normalize → validate

| Stage | Call | Module |
|---|---|---|
| Ingestion | `fetch_all` (via `_load_inputs`) | `ingestion.py` |
| Normalization | `normalize_all` (via `_load_inputs`) | `normalization.py` |
| Validation | `validate_quotes` | `validation.py` |

Sunday non-fixture runs skip the fetch entirely (empty quotes, non-halted
`ValidationSummary`). Fixture mode substitutes fixture quotes and a fixture
validation clock.

### 2. Regime, halt gates

- `compute_regime` (`regime.py`) runs whenever validation did not halt —
  it is needed for the kill switch and for HALT display.
- **Validation HALT:** any `config.HALT_SYMBOLS` failure sets
  `system_halted=True`; outcome becomes `HALT` and everything from
  correlation through the decision gates is skipped.
- **Kill switch (PRD-180):** `_kill_switch` in `runtime/__init__.py` trips on
  market stress (VIX level > 35, VIX pct_change > 0.15, or |SPY pct_change|
  > 0.03 — strict `>`). A trip rebuilds the `ValidationSummary` as halted
  (`HaltCause.MARKET_STRESS`), so downstream consumers treat it exactly like
  a validation halt.

### 3. Analysis stages (non-halt; skipped in Sunday mode except correlation/policy)

In order, inside `_run_pipeline`:

1. `compute_correlation` (`correlation.py`) → `evaluate_policy`
   (`trade_policy.py`) — GLD–DXY correlation state → `PolicyContext`
   (risk modifier for sizing).
2. `compute_all_derived` (`derived.py`) — EMAs, ATR14, momentum_5d,
   volume_ratio from cached OHLCV.
3. `resolve_sector_router` (`sector_router.py`) — router state
   (ENERGY/INDEX/MIXED); state model only, no routing application surface.
4. `classify_all_structure` (`structure.py`) — TREND / PULLBACK / BREAKOUT /
   REVERSAL / CHOP plus IV environment from VIX level.
5. `compute_all_intraday_metrics` + `classify_watchlist` (`watch.py`) —
   intraday WATCH layer (fixture mode passes empty metrics).
6. `generate_candidates` (`options.py`) — one `TradeCandidate` per non-CHOP
   symbol; returns `{}` when `direction_for_regime` is `None`.
7. `_apply_intraday_short_permission` (live only) — ORB-state gate on SHORT
   candidates via `intraday_state_engine.py`.
8. `fetch_ohlcv` per surviving candidate (`ingestion.py`).
9. `qualify_all` (`qualification.py`) — the 11 gates (1–4 hard, 5–11 soft;
   see `docs/trade_qualification.md`). **The flow gate runs INSIDE
   `qualify_all`,** not as a pipeline stage: when a flow snapshot is loaded
   (`runtime._load_flow` from config's flow_data_path), `qualify_all` calls
   `flow.apply_flow_gate` on each PASS result after the per-symbol and
   continuation passes; opposing speculative flow downgrades PASS →
   WATCHLIST. EXPANSION regime adds a continuation-candidate pass first.
10. `build_option_setups` (`options.py`) — only if qualified trades exist;
    strategy × IV matrix, DTE, relative strikes, sizing with the
    `PolicyContext.risk_modifier`.
11. `validate_option_chains` (`chain_validation.py`) — live OI / spread /
    bid-ask liquidity check per setup (fixture mode synthesizes VALIDATED
    results). Classifies TOP_TRADE_VALIDATED / NEEDS_MANUAL_CHECK /
    DISQUALIFIED_OPTIONS_INVALID.

### 4. The decision layer — `_run_decision_gates` (PRD-236)

Extracted from `_run_pipeline`; skipped entirely when there are no option
setups (defaults flow through). For each setup, in order:

1. `create_trade_decision` (`trade_decision.py`) — materializes a
   `TradeDecision` from candidate + qualification + setup + chain result.
2. `apply_execution_policy_to_decisions` (`execution_policy.py`) — the final
   deterministic ALLOW/BLOCK + sizing pass (regime, posture, session state,
   ORB states, overall macro pressure). Does not execute orders.
3. `apply_thesis_gate` (`trade_thesis.py`) — builds a thesis per candidate;
   INCOMPLETE/CONFLICTED thesis converts ALLOW_TRADE → BLOCK_TRADE.
4. `apply_invalidation_gate` (`invalidation.py`) — invalidation/exit
   guidance; TRIGGERED invalidation converts ALLOW_TRADE → BLOCK_TRADE.
5. `apply_entry_quality_gate` (`entry_quality.py`) — chase filter; extended /
   stale / chased entries convert ALLOW_TRADE → BLOCK_TRADE.

Outcome derivation (PRD-162): `outcome = TRADE` iff any decision satisfies
`decision_is_actionable` (tradable symbol, ALLOW_TRADE, positively sized);
otherwise NO_TRADE. This is the same rule the payload's top_trades gate
applies, so the two derivations agree.

### 5. Observational builds and report render

Run on every path, including halts:

1. `build_market_map` (`market_map.py`) — read-only graded market map sidecar.
2. `build_visibility_map` (`trade_visibility.py`) — ACTIVE / NEAR_MISS /
   BLOCKED per decision.
3. `build_explanation_map` (`trade_explanation.py`) — fixed-template
   explanation per candidate.
4. `render_report` (`output.py`) + `_write_markdown_report` —
   `reports/YYYY-MM-DD.md` (written even on NO TRADE and HALT days;
   verification stamp rewritten later by `execute_run`).

### 6. Contract build, finalize, validate, notify — `_build_and_finalize_contract` (PRD-236)

1. `derive_run_status` + `build_pipeline_output_contract` (`contract.py`).
2. Runtime injections: top-level `outcome`; `system_state.outcome` /
   `.permission` / `.reason`; `apply_overnight_policy`
   (`overnight_policy.py`, attaches per-candidate `overnight_policy` in the
   EOD window); Sunday-only `system_state.stay_flat_reason` /
   `.session_type`.
3. `artifacts["notification_sent"] = False`, then
   **`assert_valid_contract(contract, finalized=True)`** (PRD-233) — a
   corrupt contract fails loud BEFORE any user-visible side effect.
4. Exactly one notification send per run (live/sunday, non-fixture-backed):
   `notifications.state` dedup/suppression (`should_send`, priority,
   state key) around `output.send_notification`; suppressions are recorded
   via `write_notification_audit`; dedup state persists only on confirmed
   send.
5. `notification_sent` flipped to the real result, then
   `assert_valid_contract(finalized=True)` **again** before any artifact
   write.

### 7. Post-contract bookkeeping (still inside `_run_pipeline`)

1. `build_premarket_report` / `build_postmarket_report` (`reports/`).
2. `write_audit_record` (`audit.py`) — one append-only JSONL record per run,
   every outcome.
3. `run_post_trade_evaluation` (`evaluation.py`) →
   `run_performance_engine` (`performance_engine.py`).
4. `_build_run_summary` — the JSON run summary.
5. `_refresh_trend_structure_sidecar` (live mode only) —
   `logs/trend_structure_snapshot.json`.

### 8. Artifact persistence — `execute_run`

After `_run_pipeline` returns: write timestamped + `logs/latest_run.json`
summaries; `verify_run_summary` and fold its verdict into the summary status
and the markdown report's verification stamp; `_write_contract_file`
(`logs/latest_contract.json`); `_write_payload_artifacts` (delivery payload
JSON + rendered HTML via `delivery/payload.py` and `delivery/transport.py` —
failures here never corrupt contract artifacts); market-map lifecycle
injection (`market_map_lifecycle.inject_lifecycle`) + `logs/market_map.json`;
`logs/macro_drivers_snapshot.json`.

On any pipeline exception, `execute_run` writes `build_error_contract`
output (status ERROR, outcome HALT), a failure summary, and a failure
report — so `logs/latest_contract.json` never holds a half-built contract.

---

## Analysis-Stage Module Mapping

| Module | Role |
|---|---|
| `ingestion.py` | RawQuote per symbol, `fetch_all`, `fetch_ohlcv`, yfinance + parquet cache |
| `normalization.py` | NormalizedQuote; decimal pct_change (|v| > 2.0 auto-corrected /100), UTC enforcement |
| `validation.py` | ValidationSummary, hard per-symbol rules, HALT_SYMBOL gate, HaltCause |
| `derived.py` | DerivedMetrics: EMA9/21/50, ATR14, momentum_5d, volume_ratio |
| `regime.py` | RegimeState: vote model, posture, confidence, CHAOTIC override |
| `structure.py` | StructureResult: TREND/PULLBACK/BREAKOUT/REVERSAL/CHOP + IV environment |
| `qualification.py` | TradeCandidate, QualificationSummary, `qualify_all` (11 gates, continuation path, flow gate applied internally) |
| `flow.py` | FlowPrint/FlowSnapshot, `apply_flow_gate`, `load_flow_snapshot` — called from inside `qualify_all` |
| `options.py` | `generate_candidates`, `build_option_setups`: strategy, DTE, relative strikes |
| `chain_validation.py` | ChainValidationResult: live OI/spread/bid-ask check |
| `output.py` | `render_report`, `send_notification`, outcome constants |

## Decision-Layer Module Mapping

Each module contributes one call in `_run_decision_gates`, in this order:

| Module | Call | Effect |
|---|---|---|
| `trade_decision.py` | `create_trade_decision` | TradeDecision from candidate + qual + setup + chain |
| `execution_policy.py` | `apply_execution_policy_to_decisions` | final ALLOW/BLOCK + sizing pass |
| `trade_thesis.py` | `apply_thesis_gate` | thesis map; INCOMPLETE/CONFLICTED → BLOCK |
| `invalidation.py` | `apply_invalidation_gate` | invalidation guidance; TRIGGERED → BLOCK |
| `entry_quality.py` | `apply_entry_quality_gate` | chase filter; extended/stale/chased → BLOCK |

---

## The Output Contract

The contract is a **validated plain dict**, not frozen dataclasses.

- **Schema:** the TypedDicts in `cuttingboard/contract_types.py` (PRD-237) —
  `PipelineContract`, `SystemState`, `ContractCandidate`, `DecisionTrace`,
  `OvernightPolicyDecision`. A leaf module; derived from the producers, not
  from prose. `NotRequired` placement encodes which keys are
  runtime-injected vs built.
- **Producers:** `contract.build_pipeline_output_contract` (normal runs),
  `contract.build_error_contract` (exception path), plus the runtime
  injections in `runtime._build_and_finalize_contract`.
- **Runtime enforcement:** `contract.assert_valid_contract` (PRD-233),
  called twice per run with `finalized=True` (pre-notification and
  pre-artifact-write). It checks required keys, per-candidate invariants
  (`_assert_trade_candidates_valid`), and rejects any `system_state` key
  outside **`contract.SYSTEM_STATE_ALLOWED_KEYS`** — the enforced whitelist
  (built keys ∪ declared runtime injections). A new injection anywhere must
  be declared there or the run fails.
- **Test enforcement:** the sync guards in `tests/test_contract_types.py`
  fail the suite if a producer key and a TypedDict key drift apart (the repo
  runs no static type checker; the guards make the types load-bearing).
- **Consumers:** `delivery/payload.py` (dashboard payload),
  `notifications` (message building from the canonical contract),
  `reports/premarket.py` / `reports/postmarket.py`, the hourly path, and
  `logs/latest_contract.json` readers. Field-level layout: see
  `docs/SCHEMA_MAP.md`.

The intermediate stage objects (`RawQuote`, `NormalizedQuote`,
`ValidationSummary`, `DerivedMetrics`, `RegimeState`, `StructureResult`,
`TradeCandidate`, `QualificationResult`, `OptionSetup`, `TradeDecision`, …)
ARE frozen dataclasses with UTC-aware timestamps; only the cross-layer
output contract is a dict.

---

## Support and Sidecar Modules

Not pipeline stages; imported by stages or run alongside them.

| Module | Role |
|---|---|
| `config.py` | All constants; secrets via dotenv `.env`. Never hardcode. |
| `contract.py` | Contract builders + `assert_valid_contract` + `SYSTEM_STATE_ALLOWED_KEYS`. |
| `contract_types.py` | The contract's TypedDict schema (PRD-237). Leaf module. |
| `audit.py` | Append-only JSONL to `logs/audit.jsonl`; one record per run. |
| `runtime/` | Sole production orchestrator (package, PRD-173): `cli_main`, `execute_run`, `_run_pipeline`, hourly path, verify. Constants/dataclasses in `runtime/_constants.py` / `runtime/_types.py`. |
| `correlation.py` + `trade_policy.py` | GLD–DXY correlation → PolicyContext risk modifier. |
| `confirmation.py` | Confirmation primitives for the intraday engine. |
| `universe.py` | Symbol tradability check (`is_tradable_symbol`). |
| `sector_router.py` | Router state model and resolver; no routing application surface. |
| `time_utils.py` | ET timezone helpers, market hours. |
| `watch.py` | Intraday watchlist classification, session phase, intraday metrics. |
| `intraday_state_engine.py` | ORB classification engine (feeds short permission + execution policy). |
| `overnight_policy.py` | EOD overnight exit guidance injected into the contract. |
| `market_map.py` / `market_map_lifecycle.py` | Read-only graded market map sidecar + lifecycle transitions. |
| `trade_visibility.py` / `trade_explanation.py` | Per-decision visibility status and templated explanations. |
| `trend_structure.py` / `watchlist_sidecar.py` / `macro_pressure.py` | Pure snapshot builders (sidecars; see `docs/sidecar_doctrine.md`). |
| `evaluation.py` / `performance_engine.py` | Post-trade evaluation of prior runs → `logs/evaluation.jsonl` → performance summary. |
| `reports/` | Premarket/postmarket report builders (consume the contract). |
| `red_folder.py` | Static macro-event calendar loader (read-only). |
| `manual_journal.py` / `review_scorecard.py` | Manual trade journal writer + process-quality scorecard. |
| `alert_runner.py` | Hourly alert entrypoint with slot idempotency (PRD-141). |
| `notifications/` | Telegram formatting, priority classification, dedup/suppression state. |
| `delivery/` | Dashboard payload + HTML renderer + transport. Read-only consumer of the contract; no influence on decisions. |

## Delivery Clarification

Delivery is NOT part of the decision pipeline. Telegram send + terminal
output live in `output.py` (invoked from `_build_and_finalize_contract`);
the HTML dashboard is rendered from the contract-derived payload by
`delivery/` and published to the `publish` branch by the scheduled workflows
(never hand-overwritten on `main` — see CLAUDE.md Workflow patterns). None
of it influences qualification, options selection, decisions, or any
upstream stage. Sidecar rules: `docs/sidecar_doctrine.md`.

---

## Trust Boundary Rules

**Rule 1 — No derived metric computed on unvalidated input.**
`compute_all_derived` receives only `validation_summary.valid_quotes`.

**Rule 2 — No candidate generated for CHOP symbols.**
`generate_candidates` skips CHOP before creating a `TradeCandidate`;
qualification's Gate 4 would also reject it.

**Rule 3 — No trade when regime direction is ambiguous.**
`generate_candidates` returns `{}` when `direction_for_regime` is `None`
(NEUTRAL with net_score 0, or CHAOTIC). `qualify_all` records such symbols
as excluded `NEUTRAL_NO_DIRECTION` (PRD-235) rather than dropping them.

**Rule 4 — pct_change is always decimal.**
`0.052` means 5.2%. Normalization corrects percentage-format values
(|v| > 2.0 → /100). All downstream code assumes decimal.

**Rule 5 — Secrets only from `.env`.**
`config.py` loads via python-dotenv; no credential in source.

**Rule 6 — `block_reason == decision_trace["reason"]` for BLOCK_TRADE
candidates.** `contract._assert_trade_candidates_valid` enforces it; any
code synthesizing BLOCK_TRADE entries must set both together.

**Rule 7 — The contract fails loud, not late (PRD-233).**
`assert_valid_contract(finalized=True)` runs before the notification send
and again before artifact writes; `execute_run` converts a raise into the
minimal error contract, so a corrupt contract never reaches
`logs/latest_contract.json` or the audit log.

---

## Halt Conditions

Two halt causes, one downstream shape:

1. **Validation halt:** any `config.HALT_SYMBOLS`
   (`["^VIX", "DX-Y.NYB", "^TNX", "SPY", "QQQ"]`) fails validation.
2. **Kill switch (PRD-180):** market stress per `runtime._kill_switch`
   (thresholds above), escalated into the same halted `ValidationSummary`
   with `HaltCause.MARKET_STRESS`.

On either: outcome HALT, no candidates/qualification/decisions, HALT report
+ contract (status STAY_FLAT via `derive_run_status`) + audit record still
written, non-zero exit from `cli_main`. No trades are ever evaluated during
a halt.

---

## Key Artifacts

- `logs/latest_run.json` — canonical machine-readable run summary
  (+ timestamped `logs/run_*.json`).
- `logs/latest_contract.json` — the validated output contract.
- `logs/audit.jsonl` — append-only per-run audit record.
- `reports/YYYY-MM-DD.md` — human-readable report.
- Sidecar snapshots: `logs/market_map.json`,
  `logs/trend_structure_snapshot.json`, `logs/watchlist_snapshot.json`
  (hourly path), `logs/macro_drivers_snapshot.json`,
  `logs/evaluation.jsonl`, `logs/performance_summary.json`.
- Hourly path artifacts: `logs/latest_hourly_*.json`,
  `reports/output/hourly_report.html`.
- Dashboard payload/HTML via `delivery/transport.py`, published to the
  `publish` branch by the scheduled workflows.

---

## What Is Deliberately NOT Here

- **No prediction.** No forecasting, no price targets beyond deterministic
  R:R framing, no ML. Every gate is a deterministic function of observed
  inputs. See `VISION.md` non-goals — they are enforced by review, not
  restated here.
- **No order execution.** `execution_policy.py` materializes permissions;
  nothing places orders.
- **No decision-influencing delivery.** Dashboard, notifications, and
  sidecars are read-only consumers.

