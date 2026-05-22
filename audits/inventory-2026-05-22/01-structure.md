# 01 — Repo Structure

Audit date: 2026-05-22. Branch: `main` @ `2937d68`.

## Top-level directory tree

```
cuttingboard/
├── AGENTS.md, CLAUDE.md, CODEX.md, README.md, VISION.md       # docs
├── pyproject.toml, config.toml, .env, .gitignore               # config
├── run_daily.sh, validate_cuttingboard.sh, fix_workflow.sh     # entrypoints / helpers
├── traceback.txt, repo_snapshot.md, .cb_commit_msg             # one-off artifacts
├── mockup.html, mockup_echofi.html, mockup_zeex.html           # legacy UI mockups (root)
├── algos/                ORB reference algorithm (1 module)
├── audits/               (this audit)
├── backtesting/          ORB backtest harness — see flags
├── config/               (empty besides __pycache__)
├── cuttingboard/         pipeline package, 60 .py modules
├── cuttingboard.egg-info/ build metadata
├── data/                 OHLCV parquet cache + backtest data
├── docs/                 PRD history, architecture, milestones, superpowers
├── logs/                 generated artifacts (gitignored except whitelist)
├── pinescripts/          TradingView Pine source (1 file)
├── reports/              generated daily/premarket/postmarket reports
├── scripts/              CI/local check scripts (5 sh + 1 py)
├── tests/                85 pytest files, ~30k LOC
├── tools/                engine_doctor, macro_collector, validators
├── ui/                   published dashboard.html / index.html / CSS
├── .claude/, .codex/, .github/, .gitnexus/                     # tool config / workflows
└── .worktrees/, .ruff_cache/, .pytest_cache/, .venv/           # local-only state
```

## File counts

| Category | Count |
|---|---|
| Total files (excl. `.git`, caches, venvs) | 566 |
| Python modules under `cuttingboard/` | 60 |
| Test files under `tests/` | 85 |
| Markdown files | 247 |
| JSON files | 57 |
| Parquet files (data cache) | 40 |
| Shell scripts | 14 |
| HTML files | 9 |

LOC: ~18,288 production / ~29,967 test.

## Top-level directory purposes (one-line)

| Dir | Purpose |
|---|---|
| `cuttingboard/` | Production pipeline package (10-layer decision engine). |
| `tests/` | Pytest suite (2524 passing per PROJECT_STATE.md). |
| `docs/` | PRDs (`prd_history/`), architecture maps, sidecar/system docs, milestones. |
| `scripts/` | Operator helpers — `pre_commit_sanity.sh`, `pre_push_check.sh`, `prd_close.sh`, `clean_generated_artifacts.sh`, `check_readiness.py`. |
| `tools/` | Standalone utilities — `engine_doctor.py`, `macro_collector.py` (PRD-139 sidecar), `validate_prd_registry.py`, `ci_push_artifacts.sh`. |
| `ui/` | Published dashboard HTML + CSS consumed by GitHub Pages. |
| `logs/` | Runtime artifacts: `latest_run.json`, `latest_payload.json`, `latest_contract.json`, `audit.jsonl`, snapshots. Mostly gitignored. |
| `reports/` | Generated markdown reports (daily, premarket, postmarket). |
| `data/` | OHLCV parquet cache + backtest data. |
| `algos/` | `orb_reference.py` — Opening Range Breakout reference. Single module. |
| `backtesting/` | `run_orb_backtest.py` — ORB backtest harness. See `05-architectural-flags.md`. |
| `pinescripts/` | TradingView Pine source: `0dte Momentum Setup`. |
| `config/` | Empty besides `__pycache__`. |
| `cuttingboard.egg-info/` | setuptools metadata. |
| `.github/` | CI workflows (`hourly_alert.yml`, etc.). |
| `.claude/` | Claude Code skills + state. |
| `.codex/` | Codex agent config. |
| `.gitnexus/` | GitNexus index state. |
| `.worktrees/` | git worktree storage. |

## `cuttingboard/` modules — one-line descriptions

| Module | Purpose |
|---|---|
| `__init__.py` | Package init. |
| `__main__.py` | CLI entrypoint shim → `runtime.cli_main`. |
| `alert_runner.py` | Hourly alert runner with slot-dedup gate (PRD-141, 149). |
| `audit.py` | Append-only JSONL audit log writers. |
| `chain_validation.py` | Options chain liquidity gate (yfinance → yahooquery fallback). |
| `config.py` | Constants, env vars, instrument universe, thresholds. |
| `confirmation.py` | Multi-bar confirmation logic for intraday state. |
| `contract.py` | Run-output contract assembly + payload validators. |
| `correlation.py` | GLD–DXY correlation policy (advisory, PRD-023). |
| `delivery/dashboard_renderer.py` | Slim HTML dashboard renderer (read-only). |
| `delivery/fixtures.py` | Fixture-mode demo data for dashboard. |
| `delivery/html_renderer.py` | Auxiliary HTML helpers. |
| `delivery/macro_tape_layout.py` | Shared macro-tape row constants (PRD-138). |
| `delivery/payload.py` | Payload schema + `assert_valid_payload`. |
| `delivery/transport.py` | Payload write transport. |
| `derived.py` | Derived metrics — EMA, ATR14, momentum, volume_ratio. |
| `entry_quality.py` | Entry quality / chase filter (PRD-069). |
| `evaluation.py` | Post-trade evaluation against forward bars (PRD-047). |
| `execution_policy.py` | Execution policy materialization (PRD-051). |
| `flow.py` | Flow-alignment soft gate (PRD-013). |
| `ingestion.py` | yfinance + Polygon raw quote fetch; OHLCV parquet cache. |
| `intraday_state_engine.py` | Opening-range / intraday state classification. |
| `invalidation.py` | Invalidation + exit guidance (PRD-068). |
| `macro_pressure.py` | Macro pressure snapshot (PRD-060). |
| `manual_journal.py` | Manual trade journal + mistake taxonomy (PRD-070). |
| `market_map.py` | Graded market map sidecar (PRD-053). |
| `market_map_lifecycle.py` | Candidate lifecycle tracking (PRD-056). |
| `normalization.py` | RawQuote → NormalizedQuote (units, UTC, decimals). |
| `notifications/__init__.py` | Hourly/run notification formatter + entrypoints. |
| `notifications/formatter.py` | Telegram message formatters. |
| `notifications/hourly_slot.py` | PT-anchored slot resolver + dedup store (PRD-141, 149). |
| `notifications/state.py` | Notification state (suppression / priority). |
| `notify_test.py` | Ad-hoc Telegram smoke-test script. Zero inbound imports. |
| `options.py` | Spread selection, DTE, strikes. |
| `output.py` | Render + delivery (terminal, markdown, Telegram). |
| `overnight_policy.py` | Overnight exit guidance (PRD-058). |
| `performance_engine.py` | Signal performance engine (PRD-075). |
| `qualification.py` | 9-gate qualification (hard 1–4 / soft 5–9+). |
| `regime.py` | 8-vote regime model + posture mapping. |
| `reports/levels.py` | Derived price levels for reports. |
| `reports/postmarket.py` | Postmarket report generator. |
| `reports/premarket.py` | Premarket report generator. |
| `review_scorecard.py` | Trading process review scorecard (PRD-071). |
| `run_intraday.py` | Legacy unscheduled intraday monitor; **not invoked by any workflow** (CODEX.md notes this). |
| `runtime.py` | Sole production orchestrator (~2100 LOC; flagged tech debt). |
| `sector_router.py` | Sector routing helper. |
| `structure.py` | Per-ticker structure classification (TREND/PULLBACK/etc.). |
| `time_utils.py` | UTC / PT / ET helpers. |
| `trade_decision.py` | TradeDecision dataclass + ALLOW/BLOCK constants (PRD-045). |
| `trade_explanation.py` | First-failure explanation per candidate (PRD-046). |
| `trade_policy.py` | Policy layer combining correlation + decision. |
| `trade_thesis.py` | Thesis gate (PRD-067). |
| `trade_visibility.py` | Near-miss engine (PRD-064). |
| `trend_structure.py` | Trend structure snapshot sidecar (PRD-107). |
| `universe.py` | Tradable-symbol filter + universe definitions. |
| `validation.py` | Hard validation gate; HALT_SYMBOL stop. |
| `watch.py` | Intraday watchlist classification + session phase. |
| `watchlist_sidecar.py` | Watchlist snapshot sidecar (PRD-114). |

## Pipeline-layer mapping

Mapping follows `CODEX.md § PIPELINE LAYERS`.

| Layer | Module(s) |
|---|---|
| L1 Config | `config.py` |
| L2 Ingestion | `ingestion.py` |
| L3 Normalization | `normalization.py` |
| L4 Validation | `validation.py` |
| L5 Derived | `derived.py` |
| L6 Structure | `structure.py` |
| L7 Regime | `regime.py` |
| L8 Qualification | `qualification.py`, `flow.py`, `entry_quality.py`, `trade_thesis.py` |
| L9 Options | `options.py` |
| L10 Chain validation | `chain_validation.py` |
| L11 Output / Delivery | `output.py`, `notifications/`, `delivery/`, `alert_runner.py` |
| Audit | `audit.py` |
| Orchestrator | `runtime.py`, `__main__.py` |
| Decision-shape | `trade_decision.py`, `trade_explanation.py`, `trade_visibility.py`, `trade_policy.py`, `execution_policy.py`, `invalidation.py`, `overnight_policy.py` |
| Sidecars | `market_map.py`, `market_map_lifecycle.py`, `trend_structure.py`, `watchlist_sidecar.py`, `macro_pressure.py`, `correlation.py` |
| Reports | `reports/premarket.py`, `reports/postmarket.py`, `reports/levels.py` |
| Evaluation | `evaluation.py`, `performance_engine.py`, `review_scorecard.py`, `manual_journal.py` |
| Intraday / legacy | `intraday_state_engine.py`, `confirmation.py`, `watch.py`, `run_intraday.py` |
| Universe / time | `universe.py`, `sector_router.py`, `time_utils.py` |

### Layer-membership ambiguity flags

- **`run_intraday.py`** — CODEX.md explicitly calls it "Unscheduled legacy module. Trigger-based regime monitor (L1–5). Not invoked by any workflow." Spans L1–L5 but is orphaned. See `03-dead-code.md`.
- **`notify_test.py`** — top-level Telegram smoke test inside the production package. No inbound imports. Layer ambiguous.
- **`runtime.py`** — owns orchestration but also contains macro_drivers construction, fixture-mode plumbing, notify-mode branches, dashboard write hooks. Spans L2 → L11. PROJECT_STATE.md flags ~2100 LOC as known debt.
- **`sector_router.py`** — single inbound (qualification only). Layer placement is "qualification helper" but it lives at top-level alongside pipeline layers.
- **`confirmation.py`**, **`watch.py`**, **`intraday_state_engine.py`** — collectively make up an "intraday state" mini-pipeline that is parallel to the daily pipeline. Not explicitly numbered in CODEX.md layer table.
- **`alert_runner.py`** — sits above runtime: it imports `cuttingboard.output.send_notification` directly and is invoked by `.github/workflows/hourly_alert.yml`, not by `runtime.cli_main()`. A second orchestrator next to `runtime.py`.
- **`algos/orb_reference.py`** — outside `cuttingboard/` package entirely; consumed by `tests/test_orb_reference.py` but no production import found.
- **`backtesting/run_orb_backtest.py`** — outside `cuttingboard/` package; backtesting harness. See `05-architectural-flags.md`.
