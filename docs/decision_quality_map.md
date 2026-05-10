# Decision Quality Evidence Map — cuttingboard

This document is a field-level extension of the audits in
`docs/system_logic_map.md` and `docs/artifact_flow_map.md`. It enumerates every
decision-quality field currently produced by the pipeline so future PRDs (Sunday
Report sidecar, Threshold Review framework, Trend Structure sidecar) can be scoped
against a known field inventory rather than guessed.

This document is documentation only. No source code, schemas, sidecars,
aggregation, dashboards, notifications, or thresholds are changed by this audit.

---

## Anchors

This document anchors on, and does not duplicate:

- `docs/system_logic_map.md` — runtime decision flow, decision-affecting modules,
  display-only modules, sidecar boundary rules, forbidden mutation paths.
- `docs/artifact_flow_map.md` — artifact inventory, writers, readers, runtime-critical
  vs dashboard vs audit categorization, test isolation requirements.

Where this map needs to assert a normative rule it cites the exact anchor section.
This map does not introduce new architecture rules, sidecar boundaries, or mutation
constraints.

---

## Per-Field Metadata Schema

Every field entry below records the seven items required by PRD-105 R3:

1. **field** — exact key as it appears on disk
2. **writer** — module + function (where known); `unknown` otherwise
3. **readers** — module(s) that read this field today; `no reader` if none
4. **persisted** — `yes` (written to disk) or `no` (in-memory or contract-only)
5. **aggregated** — `no` (not aggregated anywhere) or `yes — <where>`
6. **supports calibration** — `yes` / `no` / `partial` followed by a one-line reason
7. **category** — one of: `decision-affecting`, `decision-adjacent`, `audit-only`,
   `evaluation-only`, `display-only`

Citations: `system_logic_map.md § Decision-Affecting Modules` defines the
"decision-affecting" set; `system_logic_map.md § Display-Only Modules` defines the
"display-only" set; `system_logic_map.md § Sidecar Boundary Rules` constrains
mutation paths.

---

## logs/audit.jsonl

Writer: `audit.write_audit_record` → `audit._build_record` → `audit._append_record`
(audit.py:29–77, 84–235, 300–309). One record per pipeline run, append-only.
Constant `audit.AUDIT_LOG_PATH = "logs/audit.jsonl"`.

Readers (per `artifact_flow_map.md`): `runtime._load_run_history` (reads last N
records for run-context display); indirectly, `evaluation.load_most_recent_prior_run`
extracts ALLOW_TRADE candidates from the most recent record for forward-bar
evaluation.

### Top-level fields (per `audit._build_record`)

- **field:** `run_at_utc` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — needed as a join key against evaluation.jsonl, no value on its own. category: audit-only.
- **field:** `date` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — date bucket key for any future weekly rollup. category: audit-only.
- **field:** `outcome` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — outcome distribution (TRADE / NO_TRADE / HALT) is the most basic calibration signal. category: decision-affecting.
- **field:** `regime` — writer: `audit._build_record` (sourced from `RegimeState.regime`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — regime distribution + per-regime outcome rates are central to threshold review. category: decision-affecting.
- **field:** `posture` — writer: `audit._build_record` (from `RegimeState.posture`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — STAY_FLAT frequency drives whether the system trades at all. category: decision-affecting.
- **field:** `confidence` — writer: `audit._build_record` (rounded to 4 dp). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — confidence histogram informs MIN_REGIME_CONFIDENCE calibration. category: decision-affecting.
- **field:** `net_score` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — vote-net distribution informs the regime classification thresholds. category: decision-affecting.
- **field:** `vix_level` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — VIX bucket vs outcome supports VIX_CHAOTIC_SPIKE and NEUTRAL_PREMIUM band review. category: decision-affecting.
- **field:** `router_mode` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — useful only when correlated with sector_router_state.json continuity. category: decision-adjacent.
- **field:** `energy_score` — writer: `audit._build_record` (rounded to 2 dp). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — needs paired evaluation outcomes to validate. category: decision-adjacent.
- **field:** `index_score` — writer: `audit._build_record` (rounded to 2 dp). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — same as energy_score; useful only as a covariate. category: decision-adjacent.
- **field:** `symbols_validated` — writer: `audit._build_record` (from `ValidationSummary`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — drift in validation count can flag ingestion regressions, not threshold issues. category: audit-only.
- **field:** `symbols_total` — writer: `audit._build_record` (alias of `symbols_attempted`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: no — coverage stat, not a decision signal. category: audit-only.
- **field:** `symbols_failed` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — chronic failures point at HALT_SYMBOL fragility, not gate calibration. category: audit-only.
- **field:** `symbols_qualified` — writer: `audit._build_record` (from `QualificationSummary`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — qualified count vs candidate count is a core funnel metric. category: decision-affecting.
- **field:** `symbols_near_a_plus` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — near-miss count is direct evidence for soft gate friction. category: decision-affecting.
- **field:** `symbols_watchlist` — writer: `audit._build_record` (from `WatchSummary`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — watchlist depth indicates how often gates fire on otherwise-promising candidates. category: decision-affecting.
- **field:** `symbols_excluded` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — paired with `excluded_symbols` keys this is the primary structural-rejection signal. category: decision-affecting.
- **field:** `regime_short_circuited` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — counts STAY_FLAT short-circuit frequency. category: decision-affecting.
- **field:** `regime_failure_reason` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — direct evidence for regime-gate calibration. category: decision-affecting.
- **field:** `qualified_trades` (list) — writer: `audit._build_record` (built from `QualificationSummary.qualified_trades`). readers: `runtime._load_run_history`; `evaluation.extract_allow_trade_candidates` reads `trade_decisions` only. persisted: yes. aggregated: no. supports calibration: yes — full per-candidate context for any future rollup. category: decision-affecting.
- **field:** `trade_decisions` (list) — writer: `audit._build_record`. readers: `runtime._load_run_history`; `evaluation.extract_allow_trade_candidates` filters this list. persisted: yes. aggregated: no. supports calibration: yes — per-candidate decision trail; the only path from audit to evaluation. category: decision-affecting.
- **field:** `watchlist` (list) — writer: `audit._build_record` (from `WatchSummary.watchlist`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — `missing_conditions` per item is direct gate-friction evidence. category: decision-affecting.
- **field:** `near_a_plus` (list) — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — near-miss reasons are the most actionable threshold-review input. category: decision-affecting.
- **field:** `excluded_symbols` (dict, keyed by reason) — writer: `audit._build_record` (`dict(qual.excluded)`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — exclusion-reason histogram is direct hard-gate friction evidence. category: decision-affecting.
- **field:** `suppressed_candidates` (list) — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — useful only with paired suppression source context. category: decision-adjacent.
- **field:** `halt_reason` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — HALT cause distribution informs HALT_SYMBOL and validation calibration. category: decision-affecting.
- **field:** `alert_sent` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — relevant only to notification-path audits, not decision thresholds. category: audit-only.
- **field:** `report_path` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: no — file-path metadata only. category: audit-only.

### Per-candidate sub-fields (within `qualified_trades` and `trade_decisions`)

These are documented once; both lists carry the same per-candidate shape (audit.py:117–182).

- **field:** `symbol` — writer: `audit._build_record`. readers: `runtime._load_run_history`; `evaluation.extract_allow_trade_candidates`. persisted: yes. aggregated: yes — `performance_engine._aggregate` buckets evaluation records by symbol. supports calibration: yes — symbol-level expectancy is the only existing aggregation. category: decision-affecting.
- **field:** `direction` — writer: `audit._build_record`. readers: `runtime._load_run_history`; `evaluation`. persisted: yes. aggregated: no. supports calibration: yes — direction × regime alignment is core gate evidence. category: decision-affecting.
- **field:** `strategy` — writer: `audit._build_record` (from `OptionSetup.strategy`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — useful when paired with structure / dte. category: decision-adjacent.
- **field:** `structure` — writer: `audit._build_record` (from `OptionSetup.structure`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — structure × outcome supports CHOP / TREND / PULLBACK calibration. category: decision-affecting.
- **field:** `dte` — writer: `audit._build_record` (from `OptionSetup.dte`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — DTE distribution informs options layer, not regime gates. category: decision-adjacent.
- **field:** `contracts` — writer: `audit._build_record` (from `QualificationSummary.qualified_trades.max_contracts` or `TradeDecision.contracts`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — contract counts validate sizing rules. category: decision-affecting.
- **field:** `dollar_risk` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — TARGET_DOLLAR_RISK / MAX_DOLLAR_RISK calibration evidence. category: decision-affecting.
- **field:** `entry` — writer: `audit._build_record` (from `TradeDecision.entry`). readers: `runtime._load_run_history`; `evaluation` (consumed in evaluation.jsonl record). persisted: yes. aggregated: no. supports calibration: yes — required for forward-bar resolution. category: decision-affecting.
- **field:** `stop` — writer: `audit._build_record`. readers: `runtime._load_run_history`; `evaluation`. persisted: yes. aggregated: no. supports calibration: yes — stop-distance distribution informs STOP_DISTANCE gate. category: decision-affecting.
- **field:** `target` — writer: `audit._build_record`. readers: `runtime._load_run_history`; `evaluation`. persisted: yes. aggregated: no. supports calibration: yes — feeds R:R analysis. category: decision-affecting.
- **field:** `risk_reward` — writer: `audit._build_record` (from `TradeDecision.r_r`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — direct evidence for MIN_RR_RATIO and NEUTRAL_RR_RATIO calibration. category: decision-affecting.
- **field:** `decision_status` — writer: `audit._build_record`. readers: `runtime._load_run_history`; `evaluation.extract_allow_trade_candidates` filters on `ALLOW_TRADE`. persisted: yes. aggregated: no. supports calibration: yes — status distribution is a primary funnel cut. category: decision-affecting.
- **field:** `block_reason` — writer: `audit._build_record` (from `TradeDecision.block_reason`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — the single most calibration-relevant per-candidate field; no rollup exists today (see Known Gaps). category: decision-affecting.
- **field:** `decision_trace` (dict) — writer: `audit._build_record` (`dict(decision.decision_trace)`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — gate-by-gate trace; needed for any threshold-friction summary. category: decision-affecting.
- **field:** `policy_allowed` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — execution-policy frequency informs `execution_policy.py` calibration. category: decision-affecting.
- **field:** `policy_reason` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — paired with `policy_allowed`, the policy-friction signal. category: decision-affecting.
- **field:** `size_multiplier` — writer: `audit._build_record` (cast to float). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — primarily useful when sizing rules are revisited. category: decision-affecting.
- **field:** `downside_permission` — writer: `audit._build_record` (from `intraday_state_context`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — short-side friction signal. category: decision-affecting.
- **field:** `intraday_state` — writer: `audit._build_record` (from `intraday_state_context`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — same-session permission state at decision time. category: decision-affecting.
- **field:** `intraday_state_available` — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — coverage flag rather than a calibration signal. category: audit-only.
- **field:** `reason` (within `near_a_plus[*]`) — writer: `audit._build_record` (from `qual.watchlist[*].watchlist_reason`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — soft-gate near-miss reasons. category: decision-affecting.
- **field:** `score` (within `watchlist[*]`) — writer: `audit._build_record` (from `WatchSummary.watchlist[*].score`). readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — value-only; needs gate-context to interpret. category: decision-adjacent.
- **field:** `structure_note` (within `watchlist[*]`) — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: partial — text annotation; not aggregable as-is. category: decision-adjacent.
- **field:** `missing_conditions` (within `watchlist[*]`) — writer: `audit._build_record`. readers: `runtime._load_run_history`. persisted: yes. aggregated: no. supports calibration: yes — list-typed gate-miss reasons; high-leverage rollup target. category: decision-affecting.

---

## logs/evaluation.jsonl

Writer: `evaluation.run_post_trade_evaluation` →
`evaluation.build_evaluation_records` → `evaluation.append_evaluation_records`
(evaluation.py:37–73, 135–175, 251–262). Constant
`evaluation.EVALUATION_LOG_PATH = "logs/evaluation.jsonl"`.

Readers: `performance_engine._load_records` (reads to compute the per-symbol
aggregation in `performance_summary.json`). No other readers.

Coverage limit: `evaluation.extract_allow_trade_candidates` filters the prior audit
record to `decision_status == "ALLOW_TRADE"` only. Rejected candidates have no
counterfactual outcome record (see Known Gaps).

- **field:** `evaluated_at_utc` — writer: `evaluation.build_evaluation_records`. readers: `performance_engine._load_records` (filter by validity). persisted: yes. aggregated: no. supports calibration: partial — join key for time-windowed analysis only. category: evaluation-only.
- **field:** `decision_run_at_utc` — writer: `evaluation.build_evaluation_records`. readers: `performance_engine._load_records`. persisted: yes. aggregated: no. supports calibration: yes — ties the outcome back to the originating audit record for any post-hoc rollup. category: evaluation-only.
- **field:** `symbol` — writer: `evaluation.build_evaluation_records`. readers: `performance_engine._aggregate` (bucket key). persisted: yes. aggregated: yes — `performance_engine._aggregate` groups by symbol. supports calibration: yes — only existing per-symbol calibration axis. category: evaluation-only.
- **field:** `direction` — writer: `evaluation.build_evaluation_records`. readers: `performance_engine._load_records`. persisted: yes. aggregated: no. supports calibration: yes — direction × outcome would split symbol buckets but no aggregator does this today. category: evaluation-only.
- **field:** `entry` — writer: `evaluation.build_evaluation_records`. readers: `performance_engine._load_records`. persisted: yes. aggregated: no. supports calibration: partial — needed for re-derivation, not for calibration directly. category: evaluation-only.
- **field:** `stop` — writer: `evaluation.build_evaluation_records`. readers: `performance_engine._load_records`. persisted: yes. aggregated: no. supports calibration: partial — same as entry. category: evaluation-only.
- **field:** `target` — writer: `evaluation.build_evaluation_records`. readers: `performance_engine._load_records`. persisted: yes. aggregated: no. supports calibration: partial — same as entry. category: evaluation-only.
- **field:** `evaluation.result` — writer: `evaluation.evaluate_trade_candidate` → `_build_evaluation_result`. readers: `performance_engine._aggregate` (TARGET_HIT / STOP_HIT / NO_HIT switch). persisted: yes. aggregated: yes — directly drives wins/losses/flats counts in `performance_summary.json`. supports calibration: yes — primary outcome signal for every existing analytic. category: evaluation-only.
- **field:** `evaluation.R_multiple` — writer: `_build_evaluation_result`. readers: `performance_engine._aggregate` (per-symbol R lists). persisted: yes. aggregated: yes — averaged into avg_r_win / avg_r_loss / expectancy. supports calibration: yes — R-distribution is the calibration signal for stop placement and R:R thresholds. category: evaluation-only.
- **field:** `evaluation.time_to_resolution` — writer: `_build_evaluation_result` (or 0 when bars empty). readers: `performance_engine._load_records` (validation only). persisted: yes. aggregated: no. supports calibration: yes — time-to-resolution distribution informs invalidation and DTE selection; not aggregated today. category: evaluation-only.

---

## logs/performance_summary.json

Writer: `performance_engine.run_performance_engine` → `_aggregate` → `_build_summary`
(performance_engine.py:26–38, 85–145). Path constructed as
`LOGS_DIR / "performance_summary.json"`.

Readers: display / reporting only (no automated reader inside the pipeline today).

`_MIN_SAMPLE = 5` floor (performance_engine.py:23): if a symbol's
`total_trades` is below 5, only `total_trades`, `wins`, `losses`, `flats`, and
`insufficient_data: true` are emitted; `win_rate`, `avg_r_win`, `avg_r_loss`, and
`expectancy` are intentionally suppressed below the floor. This must be respected by
any future calibration consumer — buckets with `insufficient_data: true` are not
calibration-grade.

- **field:** `buckets` (dict, keyed by symbol) — writer: `performance_engine._build_summary`. readers: no automated reader. persisted: yes. aggregated: yes — this artifact *is* the aggregation of evaluation.jsonl. supports calibration: yes — only existing aggregated calibration surface in the repo. category: evaluation-only.
- **field:** `buckets[symbol].total_trades` — writer: `performance_engine._aggregate`. readers: no automated reader. persisted: yes. aggregated: yes — count rollup. supports calibration: yes — sample-size gate for every other field. category: evaluation-only.
- **field:** `buckets[symbol].wins` — writer: `performance_engine._aggregate`. readers: no automated reader. persisted: yes. aggregated: yes — count of TARGET_HIT records. supports calibration: yes — input to win_rate. category: evaluation-only.
- **field:** `buckets[symbol].losses` — writer: `performance_engine._aggregate`. readers: no automated reader. persisted: yes. aggregated: yes — count of STOP_HIT records. supports calibration: yes — input to win_rate / expectancy. category: evaluation-only.
- **field:** `buckets[symbol].flats` — writer: `performance_engine._aggregate`. readers: no automated reader. persisted: yes. aggregated: yes — count of NO_HIT records. supports calibration: yes — measures unresolved-window frequency. category: evaluation-only.
- **field:** `buckets[symbol].win_rate` — writer: `performance_engine._aggregate`. readers: no automated reader. persisted: yes (only when `insufficient_data` is false). aggregated: yes — `wins / total`. supports calibration: yes — primary calibration axis. category: evaluation-only.
- **field:** `buckets[symbol].avg_r_win` — writer: `performance_engine._aggregate`. readers: no automated reader. persisted: yes (only when `insufficient_data` is false). aggregated: yes — mean of `evaluation.R_multiple` for TARGET_HIT records. supports calibration: yes — calibration axis for target placement. category: evaluation-only.
- **field:** `buckets[symbol].avg_r_loss` — writer: `performance_engine._aggregate`. readers: no automated reader. persisted: yes (only when `insufficient_data` is false). aggregated: yes — mean abs(R) for STOP_HIT records. supports calibration: yes — calibration axis for stop placement. category: evaluation-only.
- **field:** `buckets[symbol].expectancy` — writer: `performance_engine._aggregate`. readers: no automated reader. persisted: yes (only when `insufficient_data` is false). aggregated: yes — `(win_rate * avg_r_win) − ((1 − win_rate) * avg_r_loss)`. supports calibration: yes — top-line per-symbol calibration metric. category: evaluation-only.
- **field:** `buckets[symbol].insufficient_data` — writer: `performance_engine._aggregate`. readers: no automated reader. persisted: yes. aggregated: no. supports calibration: yes — must be checked before consuming the rest of the bucket. category: evaluation-only.
- **field:** `generated_at` — writer: `performance_engine._build_summary` (UTC isoformat). readers: no automated reader. persisted: yes. aggregated: no. supports calibration: partial — recency stamp; useful only to detect stale summaries. category: evaluation-only.

---

## logs/latest_hourly_run.json

Writer: `runtime._write_hourly_artifacts` (runtime.py).
Constant `runtime.LATEST_HOURLY_RUN_PATH`. Per `artifact_flow_map.md`, this is the
hourly write path; the dashboard renderer reads `logs/latest_run.json` by default and
the CI hourly workflow overrides with `--run logs/latest_hourly_run.json`.

Readers (per `artifact_flow_map.md`): `delivery/dashboard_renderer.py` (via CI `--run`
override); `hourly_alert.yml` (CI workflow).

- **field:** `run_id` — writer: `runtime._write_hourly_artifacts`. readers: `dashboard_renderer` via CI override; `hourly_alert.yml`. persisted: yes. aggregated: no. supports calibration: partial — identifier only, useful as a join key against audit.jsonl. category: audit-only.
- **field:** `run_at_utc` — writer: `runtime._write_hourly_artifacts`. readers: `dashboard_renderer` via CI override. persisted: yes. aggregated: no. supports calibration: partial — same as `audit.run_at_utc`; the artifact mirrors the audit time. category: audit-only.
- **field:** `posture` — writer: `runtime._write_hourly_artifacts`. readers: `dashboard_renderer` via CI override. persisted: yes. aggregated: no. supports calibration: yes — duplicates `audit.posture`; either source can drive a posture-frequency rollup. category: decision-affecting.
- **field:** `outcome` — writer: `runtime._write_hourly_artifacts`. readers: `dashboard_renderer` via CI override. persisted: yes. aggregated: no. supports calibration: yes — duplicates `audit.outcome`; either source can drive an outcome rollup. category: decision-affecting.

Any additional decision-quality fields written into this artifact by `runtime.py`
mirror fields documented elsewhere in this map (notably the audit-record top-level
fields). Calibration consumers should prefer `logs/audit.jsonl` for full per-run
context; `latest_hourly_run.json` is a thin read-side artifact.

---

## logs/latest_hourly_contract.json

Writer: `runtime._write_hourly_artifacts` → `_write_contract_file` (runtime.py),
producing the contract assembled by
`contract.build_pipeline_output_contract`. Constant
`runtime.LATEST_HOURLY_CONTRACT_PATH`.

Readers (per `artifact_flow_map.md`):
`dashboard_renderer._load_contract_entry_context` — render entry prices for display.

### Decision-quality field of interest: `system_state.stay_flat_reason`

Writer: `runtime.py:950, 958` and `contract.build_pipeline_output_contract`. Set on
`contract["system_state"]["stay_flat_reason"]` when the pipeline forces STAY_FLAT
(e.g., `PREMARKET_CONTEXT`, regime-driven flat, kill-switch).

Readers: `dashboard_renderer._load_contract_entry_context`; `runtime.py` itself
re-reads the prior contract via `_load_previous_market_map` indirectly is *not*
applicable here — the contract is not re-read for decisions.

- **field:** `system_state.stay_flat_reason` — writer: `runtime.py` / `contract.build_pipeline_output_contract`. readers: `dashboard_renderer` (display). persisted: yes (in the contract artifact). aggregated: no. supports calibration: yes — STAY_FLAT cause distribution is direct posture-gate evidence. category: decision-affecting.

**Audit-vs-contract divergence (load-bearing):** `stay_flat_reason` is set on
`contract.system_state` and persisted into `logs/latest_hourly_contract.json` (and
the non-hourly equivalent), but it is **not** written into `logs/audit.jsonl` by
`audit._build_record` (audit.py:193–233). A calibration consumer wanting to
aggregate STAY_FLAT reasons across runs must either:

1. read the contract artifacts (which only retain the *latest* hourly run on disk —
   not historical), or
2. extend `audit._build_record` to persist the field per-run (would require a new PRD
   per `system_logic_map.md § Forbidden Mutation Paths`: changing the audit schema
   is a contract change and out of scope for any sidecar).

This divergence is captured under Known Gaps below.

---

## logs/market_map.json

Writer: `runtime._write_market_map_file` (runtime.py); content built by
`market_map.py`. Constant `runtime.MARKET_MAP_PATH`.

Readers (per `artifact_flow_map.md`): `delivery/dashboard_renderer._resolve_market_map`
(display-tier rendering); `runtime._load_previous_market_map` (lifecycle injection
into the next run's market map).

Per `system_logic_map.md § Display-Only Modules`, `market_map.py` is display-only and
its grades are display-only tiers, not qualification gates. Any classification of a
`market_map` field below as `decision-affecting` would contradict that anchor and
require a new PRD per `system_logic_map.md § Forbidden Mutation Paths`.

### Representative record

Symbol used for the per-key audit: **SPY** (selected from the current
`logs/market_map.json`, primary HALT_SYMBOL, present in the `symbols` block).

The 16 keys present in the SPY record are documented below. All keys are
mode-independent and apply to every per-symbol record in the artifact.

- **field:** `asset_group` — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`; `runtime._load_previous_market_map` (lifecycle continuity). persisted: yes. aggregated: no. supports calibration: partial — useful only to slice display tiers by group. category: display-only.
- **field:** `bias` — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`. persisted: yes. aggregated: no. supports calibration: partial — display label; not a gate input. category: display-only.
- **field:** `confidence` — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`. persisted: yes. aggregated: no. supports calibration: partial — display tier; not the regime confidence used for posture. category: display-only.
- **field:** `current_price` — writer: `market_map.py` (per PRD-084). readers: `dashboard_renderer._resolve_market_map`; `runtime._load_previous_market_map` (lifecycle injection). persisted: yes. aggregated: no. supports calibration: partial — display value; calibration consumers should source price from ingestion, not market_map. category: display-only.
- **field:** `fib_levels` (dict: `retracements`, `source`) — writer: `market_map.py`. readers: `dashboard_renderer` (level diagram). persisted: yes. aggregated: no. supports calibration: no — chart-context only per PRD-074. category: display-only.
- **field:** `grade` — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`. persisted: yes. aggregated: no. supports calibration: no — display tier per `system_logic_map.md § Display-Only Modules`; classifying as decision-affecting is a forbidden mutation path. category: display-only.
- **field:** `invalidation` (list) — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`. persisted: yes. aggregated: no. supports calibration: no — human-readable invalidation cues for display only. category: display-only.
- **field:** `lifecycle` (dict) — writer: `market_map.py`; `runtime._load_previous_market_map` provides the prior-run carry forward. readers: `dashboard_renderer._resolve_market_map`; `runtime._load_previous_market_map` (lifecycle injection). persisted: yes. aggregated: no. supports calibration: partial — lifecycle transitions reflect display-tier movement, not gate calibration. category: display-only.
- **field:** `preferred_trade_structure` — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`. persisted: yes. aggregated: no. supports calibration: no — narrative label for display only. category: display-only.
- **field:** `reason_for_grade` — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`. persisted: yes. aggregated: no. supports calibration: no — narrative label for display only. category: display-only.
- **field:** `setup_state` — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`. persisted: yes. aggregated: no. supports calibration: no — display tier, not a gate input. category: display-only.
- **field:** `structure` — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`. persisted: yes. aggregated: no. supports calibration: no — market_map's structure label is display; the gate-relevant structure classification is in `structure.py` and surfaced through `audit.qualified_trades[*].structure`. category: display-only.
- **field:** `symbol` — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`. persisted: yes. aggregated: no. supports calibration: no — identifier only. category: display-only.
- **field:** `trade_framing` (dict) — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`. persisted: yes. aggregated: no. supports calibration: no — narrative framing for display only. category: display-only.
- **field:** `watch_zones` (list of dicts) — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map` (level diagram). persisted: yes. aggregated: no. supports calibration: no — chart-context only. category: display-only.
- **field:** `what_to_look_for` (list) — writer: `market_map.py`. readers: `dashboard_renderer._resolve_market_map`. persisted: yes. aggregated: no. supports calibration: no — narrative cues for display only. category: display-only.

---

## Known Gaps

This section enumerates every gap identified in PRD-105 SCOPE. Each entry records:
the one-line description, the artifact/field/path that exhibits it, whether closing
it requires a new PRD, and a candidate downstream PRD name.

1. **No structured `block_reason` rollup across runs.**
   - Artifact / field / path: `logs/audit.jsonl` → per-candidate `block_reason`
     (within `qualified_trades[*]` and `trade_decisions[*]`).
   - Requires new PRD: yes.
   - Candidate downstream PRD: Sunday Report sidecar (block-reason histogram across
     the prior week of audit records).

2. **No threshold-friction summary.**
   - Artifact / field / path: `logs/audit.jsonl` → `decision_trace`,
     `regime_failure_reason`, `excluded_symbols` (dict keyed by reason),
     `near_a_plus[*].reason`, `watchlist[*].missing_conditions`. None of these are
     consumed by any aggregator today.
   - Requires new PRD: yes.
   - Candidate downstream PRD: Threshold Review framework (gate-friction summary
     producing per-gate hit / miss counts and near-miss distributions).

3. **No weekly decision-quality summary artifact.**
   - Artifact / field / path: no module under `cuttingboard/reports/`
     (`premarket.py`, `postmarket.py`, `levels.py` only) produces a weekly summary;
     `cuttingboard/reports/__init__.py` is the only init entry point.
   - Requires new PRD: yes.
   - Candidate downstream PRD: Sunday Report sidecar (weekly aggregator reading
     `logs/audit.jsonl` + `logs/evaluation.jsonl` + `logs/performance_summary.json`,
     writing a sidecar artifact in a new path that does not shadow existing
     artifacts per `system_logic_map.md § Sidecar Boundary Rules`).

4. **No documented evidence-to-PRD calibration convention.**
   - Artifact / field / path: `CLAUDE.md § PRD documentation rule` defines the PRD
     lifecycle but does not define a "calibration PRD" pathway driven by N weeks of
     audit/evaluation data.
   - Requires new PRD: yes.
   - Candidate downstream PRD: Threshold Review framework (a meta-PRD defining when
     a numeric constant in `config.py` may be re-tuned and what evidence the
     accompanying PRD must cite).

5. **No human-disagreement surface inside the repo.**
   - Artifact / field / path: intentional. The repo records system decisions; a
     decision journal of "system said X, I did Y" lives outside the repo (in the
     Obsidian Cutting Board vault) and must not be merged into the repo per
     `CLAUDE.md § purpose` (decision-engine, not a research platform).
   - Requires new PRD: no.
   - Candidate downstream PRD: not applicable (Obsidian decision-journal workflow,
     out of repo scope).

6. **`evaluation.jsonl` only evaluates ALLOW_TRADE candidates; rejected candidates
   have no counterfactual outcome record.**
   - Artifact / field / path: `evaluation.extract_allow_trade_candidates`
     (evaluation.py:109–132) filters the prior audit record to
     `decision_status == "ALLOW_TRADE"`. Rejected candidates (block_reason set,
     decision_status != ALLOW_TRADE) are never evaluated forward.
   - Requires new PRD: yes (evaluation schema change is out of scope for any
     sidecar per `system_logic_map.md § Forbidden Mutation Paths`).
   - Candidate downstream PRD: Counterfactual Evaluation Extension (would extend
     `evaluation.py` to also forward-evaluate rejected candidates; non-trivial
     scope and ordering risk).

7. **`stay_flat_reason` is set on `contract.system_state` but is not persisted in
   `audit._build_record`.**
   - Artifact / field / path: `runtime.py:950, 958` sets
     `contract["system_state"]["stay_flat_reason"]`; `audit.py:193–233`
     (`_build_record`) does not include this key. The reason persists in
     `logs/latest_hourly_contract.json` (latest run only) but does not enter
     `logs/audit.jsonl` (historical record).
   - Requires new PRD: yes (audit schema change is forbidden without a PRD per
     `system_logic_map.md § Forbidden Mutation Paths`).
   - Candidate downstream PRD: Audit Schema Patch — Persist STAY_FLAT Reason
     (small, scoped patch PRD; should precede the Sunday Report sidecar so the
     weekly STAY_FLAT-cause distribution can be computed from `audit.jsonl`).

---

## Calibration Readiness Snapshot

This is a non-normative summary of where calibration-grade evidence exists today and
where it does not. It does not introduce new architecture rules; see anchors for
authoritative boundaries.

| Calibration axis | Evidence today | Aggregation today | Gap to close |
|---|---|---|---|
| Per-symbol expectancy | `evaluation.jsonl` + `performance_summary.json` | yes (`performance_engine._aggregate`) | sample size; rejected-candidate counterfactual (Gap 6) |
| Block-reason distribution | `audit.qualified_trades[*].block_reason`, `trade_decisions[*].block_reason` | none | Gap 1 (Sunday Report sidecar) |
| Soft-gate near-miss distribution | `audit.near_a_plus[*].reason`, `watchlist[*].missing_conditions` | none | Gap 2 (Threshold Review framework) |
| Hard-gate exclusion distribution | `audit.excluded_symbols` (dict keyed by reason) | none | Gap 2 (Threshold Review framework) |
| STAY_FLAT cause distribution | `contract.system_state.stay_flat_reason` (latest only) | none | Gap 7 (audit-schema patch) precedes Gap 3 (Sunday Report) |
| Regime confidence calibration | `audit.confidence`, `net_score`, `vix_level` | none | Gap 2 (Threshold Review framework) |
| Direction × regime alignment | `audit.qualified_trades[*].direction` × `audit.regime/posture` | none | Gap 2 (Threshold Review framework) |

---

## Suggested Downstream PRD Ordering

Non-binding ordering implied by the gaps above:

1. **Audit Schema Patch — Persist STAY_FLAT Reason** (Gap 7) — small, scoped; unblocks
   STAY_FLAT-cause analysis from `audit.jsonl` history.
2. **Sunday Report sidecar** (Gaps 1, 3) — weekly aggregator reading
   `audit.jsonl` + `evaluation.jsonl` + `performance_summary.json`. Bounded by
   `system_logic_map.md § Sidecar Boundary Rules` (read-only consumer; new artifact
   path; no mutation of contract / payload / qualification / market_map / notification
   / dashboard).
3. **Threshold Review framework** (Gaps 2, 4) — meta-PRD defining the calibration-PRD
   pathway and producing the gate-friction summary the Sunday Report cites.
4. **Counterfactual Evaluation Extension** (Gap 6) — schema-touching; defer until the
   above three are in production and the evidence base motivates the extension.
