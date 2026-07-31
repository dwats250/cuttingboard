# Evidence Index — 2026-07-30

```
STATUS: READ-ONLY RECONCILIATION
AUTHORIZES NO IMPLEMENTATION
```

Immutable references for every row in `FINDING_STATUS_MATRIX.md`. Line ranges are
given where they are reliable at the pinned SHA; symbols are given always, because
symbols survive the next refactor and line numbers do not. This index exists so a
future reader never repeats the archaeology.

## Pins

| Label | Repository | SHA |
|---|---|---|
| `CB@HEAD` | `dwats250/cuttingboard` (`main`) | `9e6b7728b7e9f1c3b63c0fc23f02e3ec031c2f94` |
| `CB@publish` | `dwats250/cuttingboard` (`origin/publish`) | read via `git show origin/publish:<path>`; fetched 2026-07-30 |
| `CB@7f1ff20` | `dwats250/cuttingboard` (historical) | `7f1ff20` — the SHA `audits/FINDINGS.md` was authored against |
| `STRAT@934ae8b` | `dwats250/strategy` | `934ae8b7a19c501875618b79a388438e2add2bd1` |
| `BRIEF@bb81e0b5` | not in any repository | SHA-256 `bb81e0b5c34f08a42b06b4f444d272341b133daaac192736fe7f5ab11df0c7aa` |

Unless a row says otherwise, every `path:line` below is at `CB@HEAD`.

---

## CB-01 — Hourly channel never evaluates the kill switch

| Kind | Reference |
|---|---|
| Symbol (definition) | `cuttingboard/runtime/__init__.py::_kill_switch` — `:2194` |
| Symbol (call site 1) | `cuttingboard/runtime/__init__.py::_run_pipeline` — `:937` (daily) |
| Symbol (call site 2) | `cuttingboard/runtime/__init__.py::_build_run_summary` — `:1256` (daily) |
| Defect site 1 | `cuttingboard/runtime/__init__.py::_build_hourly_run_summary` (def `:1903`) — literal `"kill_switch": False` at `:1975` |
| Defect site 2 | `cuttingboard/runtime/__init__.py::_failure_summary` (def `:2335`) — literal `"kill_switch": False` at `:2366` |
| Truthful contrast | `:1288` — `"kill_switch": kill_switch` (daily, evaluated) |
| Decisive search | `rg -n "_kill_switch" cuttingboard/runtime/__init__.py` → exactly 3 hits; `rg -n '"kill_switch":' cuttingboard/` → 3 hits, 2 literal |
| Relevant test | **None found.** No test asserts hourly kill-switch evaluation. |
| PRD | Planned as BUILD_PLAN "PRD-253"; that number is `docs/prd_history/PRD-253.md` (contract/audit sizing) — unrelated |
| Thresholds | `cuttingboard/runtime/__init__.py:2185-2187` (`KILL_SWITCH_*`); documented `docs/system_logic_map.md:72-75` |

## CB-02 — One-contract floor breaches the correlation-adjusted budget

| Kind | Reference |
|---|---|
| Defect site | `cuttingboard/options.py::build_option_setups` — `:228-236` (`effective_risk`, `raw_adjusted`, `max(1, min(...))`, `final_dollar_risk`) |
| Max-loss formula | `cuttingboard/options.py::_max_loss_for_strategy` — `:414-426` |
| Strike distances | `cuttingboard/options.py:65-67` (`_MAX_STRIKE_DIST_ETF = 5.0`, `_MAX_STRIKE_DIST_STK = 2.50`, `_DEBIT_PCT_OF_WIDTH = 0.30`) |
| Budget constants | `cuttingboard/config.py:70-71` (`ACCOUNT_EQUITY = 15000.0`, `MAX_RISK_PCT_PER_TRADE = 0.026667`) |
| Correlation modifiers | `cuttingboard/config.py:271,274-276` (`CORRELATION_ENABLED = True`; ALIGNED 1.0 / NEUTRAL 0.7 / CONFLICT 0.4) |
| Why NEUTRAL is the default | `cuttingboard/correlation.py:58-70` — NEUTRAL whenever GLD or DXY is flat, missing, or stale |
| Correct contrast (Gate 8 refuses) | `cuttingboard/qualification.py:464-492`, refusal at `:480-487` |
| Owner ruling | `docs/DECISIONS.md:106-139` — 2026-07-24, "refuse the trade"; same entry, "**NOT IMPLEMENTED**" |
| Original statement | `docs/prd_history/PRD-259.first-fire-consumers.proposal.md` — Finding D, 2026-07-14 |
| Relevant test | **None found** asserting the floor respects the correlation-adjusted budget |

## CB-03 — Size multiplier never materialises

| Kind | Reference |
|---|---|
| Produced | `cuttingboard/execution_policy.py:184` (`size_multiplier=result.size_multiplier`), `:198`, `:215` (`size_multiplier_for_confidence`, def `:59`) |
| Recorded, never applied | `cuttingboard/contract.py:362`; `cuttingboard/audit.py:146,187`; `cuttingboard/trade_decision.py:58` |
| Validated only | `cuttingboard/contract.py:689-700` (type/finite/non-negative assertions) |
| Read as a boolean only | `cuttingboard/trade_decision.py:96-115` — `is_actionable_trade`, `size_multiplier > 0`; docstring at `:102-104` calls it "a **defensive invariant**" that never fires |
| Renders pre-policy | `cuttingboard/output.py:361-362` (`setup.max_contracts`, `setup.dollar_risk`) |
| Absent literal | `size_rounds_to_zero` — **zero occurrences** in any production file; the only tree hit is `docs/plans/decision-support-workplan-v0.1.md` |
| Decisive search | `rg -n "size_multiplier" cuttingboard/` (no multiplication into size); `rg -rn "size_rounds_to_zero" --glob '!audits/**' .` |
| Operator decision | `audits/BUILD_PLAN.md` § Operator decisions, item 2 (2026-07-10) |
| Misread source (see Contradictions) | `docs/prd_history/PRD-073.md:56` — "UI PATH ONLY", inside a `RULE — FIELD AVAILABILITY` block whose FILES are `dashboard_renderer.py`, `ui/app.js`, `ui/index.html`, `ui/styles.css` |

## CB-04 — Recommendations counted as trades

| Kind | Reference |
|---|---|
| Cross-run defect | `cuttingboard/execution_policy.py::load_execution_session_state` — `:94-103` (sums `decision_status == ALLOW_TRADE`) |
| Hypothetical-loss source | `cuttingboard/execution_policy.py::_load_consecutive_losses` — `:105-109` |
| Gates that consume it | `cuttingboard/execution_policy.py:224-229` (`session_trade_limit`, `loss_lockout`, `cooldown`) |
| **Live evidence** | `CB@publish:logs/audit.jsonl` — 56 pipeline records, 764 notification records, 2026-05-07 → 2026-07-30 |
| Aggregate | 6 `TRADE` / 50 `NO_TRADE` outcomes; 54 trade_decisions → 6 ALLOW, 48 BLOCK (88.9 %) |
| Cooldown blocks (5) | 2026-06-23 (ALLOW AAPL → blocked META); 2026-06-30 (ALLOW SPY → blocked QQQ, IWM, NVDA); 2026-07-23 (ALLOW SPY → blocked SLV) — **every one in the same run as its ALLOW** |
| Reproduce | `git show origin/publish:logs/audit.jsonl`, then group `trade_decisions[]` by `block_reason` and compare each cooldown block's `run_at_utc` to the same record's ALLOW |
| Operator decision | `audits/BUILD_PLAN.md` § Operator decisions, item 3 (2026-07-10) — "fully dormant, including the same-run in-run counter" |
| Relevant test | **None found** asserting dormant session state |

## CB-05 — Macro-pressure fail-open

| Kind | Reference |
|---|---|
| Defect site | `cuttingboard/runtime/__init__.py::_compute_overall_pressure` — `:1384-1391` (bare `except Exception` → `logger.warning` → `return "UNKNOWN"`) |
| Consumer | `cuttingboard/execution_policy.py::_apply_macro_pressure` — `:239-241` (`if pressure in ("UNKNOWN", "NEUTRAL"): return PolicyDecision(True, reason, size)`) |
| Contrast (real constraint) | same function, `:242-246` — MIXED cuts size 25 %; RISK_OFF blocks LONG |
| Diagnostic to run | count `build_macro_pressure failed, defaulting to UNKNOWN` in workflow logs |
| Doctrine context | `docs/sidecar_doctrine.md` (see CB-16) |
| Relevant test | **None found** asserting a pressure-computation failure blocks |

## CB-06 — Hourly broken-but-green

| Kind | Reference |
|---|---|
| Always-zero exit | `cuttingboard/alert_runner.py:43` (docstring: "convert all runtime failures to exit 0"), returns `0` at `:81`, `:95`, `:122`; `sys.exit(main(...))` `:126` |
| Presence-not-status readiness | `scripts/check_readiness.py:15-16` — key-name tuples `("meta","run_status","schema_version","sections")` and `("status","outcome")` |
| Fail-loud pattern already in repo | `.github/workflows/dashboard_preview.yml` — exits 1 on the same condition |
| Viewer-layer mitigation | `docs/prd_history/PRD-250.md` (client-side staleness banner) |
| Incident precedent | 2026-07-07 hourly freeze — `docs/PROJECT_STATE.md` PRD-250 entry |

## CB-07 — Opening range from mid-session bars

| Kind | Reference |
|---|---|
| Truncation 1 | `cuttingboard/ingestion.py::fetch_intraday_bars` — `:207` (`frame.tail(120)`) |
| Truncation 2 | `cuttingboard/watch.py::_bars_from_df` — `:30`, `:357` |
| Slice | `cuttingboard/watch.py:164-166` (`bars[:5]`) |
| Gate consumer | `cuttingboard/execution_policy.py` — `orb_inside_range` BLOCK_TRADE |
| Reproduction record | `docs/prd_history/PRD-271.md:36-45` — two independent reproductions, expected ORB high 110.0 vs actual 777.0 |
| Merge state | PR #173, merge commit `9e6b772` — **Stage-0 scaffold; GOAL/SCOPE/FILES are TODO under `GATE A REQUIRED BEFORE AUTHORING`** |
| Registry | `docs/PRD_REGISTRY.md:291` — PRD-271, commit cell `—`, status IN PROGRESS |

## CB-08 — Spread economics estimated, never live

| Kind | Reference |
|---|---|
| Single-leg selection | `cuttingboard/chain_validation.py:233-240` (near-ATM filter → one `best_row`) |
| Entry point | `cuttingboard/chain_validation.py::validate_option_chains` — `:143`; reads `setup.symbol` `:156`, `setup.dte` `:202`, `setup.strategy` `:223` |
| Never read | `setup.long_strike`, `setup.short_strike` — no occurrence in the file |
| Absent tokens | `net_credit`, `net_debit` — zero occurrences in `chain_validation.py` |
| The estimate | `cuttingboard/options.py::_max_loss_for_strategy` `:414-426`; `_estimated_debit` `:402-412`; `_DEBIT_PCT_OF_WIDTH = 0.30` `:67` |
| Seam left by A1a | the `max_loss` field on `TradeCandidate` / `OptionSetup` (`options.py:388`) |
| Misattributed PRD | `docs/prd_history/PRD-256.md` — delivered continuation-path ATR-proxy bounding, a different concern; COMPLETE @ #146 |

## CB-09 — Non-atomic writes

| Kind | Reference |
|---|---|
| Non-atomic | `cuttingboard/runtime/__init__.py::safe_write_latest`, `::_write_summary_files`, `::_rewrite_summary_file` (bare `write_text`) |
| Wedge | `cuttingboard/runtime/__init__.py::_load_previous_market_map` (raises on malformed JSON) |
| Atomic contrast | temp+rename used for the lower-criticality snapshots in the same file |
| Unlocked appends | `cuttingboard/audit.py` (append), `cuttingboard/evaluation.py` (append) |
| Banked corrections (do NOT build) | `audits/RECONCILED_FINDINGS.md` F-06 — impossible line cite `hourly_alert.yml:386-388` in a 216-line file; cross-workflow concurrency portion is wrong (separate runner filesystems) |

## CB-10 — Qualification doc understates the risk budget

| Kind | Reference |
|---|---|
| Stale site 1 | `docs/trade_qualification.md:174` — "`# $150 under RISK_ON`" |
| Stale site 2 | `docs/trade_qualification.md:181` — "`MAX_RISK_PCT_PER_TRADE=0.01` … the budget is $150" |
| Stale site 3 | `docs/trade_qualification.md:249` — "`MAX_RISK_PCT_PER_TRADE=0.01`, giving an effective…" |
| Truth | `cuttingboard/config.py:70-71` → effective ≈ $400.005 |
| NOT stale (do not "fix") | `:113` `MIN_STOP_PCT = 0.01`; `:321` `CONTINUATION_VIX_SPIKE_BLOCK = 0.01`; `:326` `MIN_STOP_PCT` |
| Change that created the drift | `docs/prd_history/PRD-252.md` (COMPLETE @ #133) |
| Missed sweep | `docs/prd_history/PRD-247.md` — doc-truth pass over this same file |

## CB-11 — `system_candidate_id` never emitted

| Kind | Reference |
|---|---|
| Definition | `cuttingboard/manual_journal.py:59` |
| Tests only | `tests/test_manual_journal.py`, `tests/test_review_scorecard.py` |
| Absent from | `cuttingboard/audit.py::_build_record` — `:90-243`; the contract (`cuttingboard/contract_types.py`) |
| Generator | **none** |
| Prior inventory | `docs/decision_quality_map.md` (PRD-105) — 7 calibration axes, 7 gaps, 4 proposed PRDs, **none of which exist** |

## CB-12 — HIGH-RISK gate bypasses

| Kind | Reference |
|---|---|
| Lane regex (no `IGNORECASE`) | `tools/validate_prd_registry.py:26` — `re.compile(r"^LANE\b[:\s]*\n?\s*HIGH-RISK", re.MULTILINE)` |
| Docless skip, second-model leg | `tools/validate_prd_registry.py:525-527` (`if not doc.exists(): continue`, then the lane check) |
| Artifact leg = existence + filename | `tools/validate_prd_registry.py:528+` — `has_artifact` from `history.glob(f"PRD-NNN.review.*.md")`, filtered by name prefix, **contents never read** |
| Other docless skips | `:328`, `:489` |
| **Closed** by PRD-269 | `tools/validate_prd_registry.py:483-499` — doc-status disagreement now errors (`_scan_doc_status_lines`) |
| Test gap | `tests/test_prd_registry.py` — no hit for `High-Risk` casing or `IGNORECASE` |
| Pending (NOT production) | PR #174, branch `claude/prd-273-stated-limitation` — scaffolds PRD-275 (artifact append-only + merged-commit SHA pinning) |

## CB-12b — Manual-merge backstops

| Kind | Reference |
|---|---|
| Absent | `.github/CODEOWNERS` (does not exist at HEAD) |
| Absent | changed-path governance check in `.github/workflows/ci.yml` |
| Absent | `CLAUDE.md` / `.claude/skills/` in `.claude/hooks/protect_files.sh` protected set |
| **Closed** | `enforce_admins` true on `main` since 2026-07-19 — `docs/DECISIONS.md` (observed-enforcement class ruling) |
| Premise superseded | `docs/DECISIONS.md:19` — GOV-1 (2026-07-25), universal manual merge; `.claude/settings.json` denies `Bash(gh pr merge:*)` |
| Plan record | `audits/BUILD_PLAN.md:122-137` — "Wave 3 NEVER RODE" |

## CB-13 — Credit-spread max loss (FIXED)

| Kind | Reference |
|---|---|
| Fix | `cuttingboard/options.py::_max_loss_for_strategy` — `:414-426`, `return round(strike_distance - debit_proxy, 4)` for `BULL_PUT_SPREAD` / `BEAR_CALL_SPREAD` |
| Consumers | `cuttingboard/qualification.py:472-475` (Gate 8); `cuttingboard/options.py:229` (final resize) |
| **Discriminating test** | `tests/test_phase5.py::test_non_continuation_result_ignores_stale_candidate_max_loss_prd256` — `:600-618`. Sets `candidate.max_loss = 999.0` deliberately wrong; asserts `setup.dollar_risk == _max_loss_for_strategy(BULL_PUT_SPREAD, 5.0) * 100`. Red on revert. |
| Why the neighbouring test does not count | its own comment `:601-606`: the prior fixture's `max_loss` already equalled the recomputed figure, so it could not discriminate |
| PRDs | `docs/prd_history/PRD-251.md` (@ #132); `docs/prd_history/PRD-256.md` (@ #146, R2 ruled FIX, R3 removed the continuation exclusion) |

## CB-14 — pct_change fails loud (FIXED)

| Kind | Reference |
|---|---|
| Fix | `cuttingboard/ingestion.py::_yfinance_quote_raw` — `:303-311`, `raise ValueError(f"fast_info.previous_close invalid: {prev_close!r}")` for None / non-finite / non-positive |
| **Discriminating tests** | `tests/test_phase1.py:340` `test_missing_previous_close_raises` (parametrised); `:348` `test_wrapper_converts_missing_previous_close_to_fetch_failure`, asserting `"previous_close" in quote.failure_reason` (`:358`) |
| Twins also fixed | `cuttingboard/normalization.py` (NaN drop); `cuttingboard/regime.py` (fixed 16-symbol breadth denominator) |
| PRD | `docs/prd_history/PRD-262.md` (@ #151) |
| Declared residual | `_kill_switch`'s own `0.0` defaults for missing SPY/VIX — recorded in PRD-262 as shielded (halt symbols, halt-guarded call sites) |

## CB-15 — Regime quorum floor (FIXED)

| Kind | Reference |
|---|---|
| Fix | `cuttingboard/regime.py:201-209` — `missing = len(raw_votes) - total_votes`; sign-clamped `bounded_net`; `confidence = abs(bounded_net) / len(raw_votes)`; `_classify_regime(bounded_net, ...)` `:208`; `_determine_posture(regime, confidence, ...)` `:209` |
| Truthfulness preserved | `:221` stores raw `net_score`; `:227` stores real `total_votes` |
| **Discriminating test** | `tests/test_regime.py::test_vix_only_synthetic_is_bounded_to_stay_flat` — `:285-301`; asserts `confidence == 0.0`, `regime == NEUTRAL`, `posture == STAY_FLAT`, while `net_score == 1` and `total_votes == 2` stay truthful |
| Proof | PRD-263 carries an exhaustive 3^8 × 3 enumeration that a skipped vote never out-permits full coverage |
| Disclosed limit | 247-day replay contained **zero** partial-vote days; synthetic tests are the only dropout evidence |
| PRDs | `docs/prd_history/PRD-263.md` (@ #152), `PRD-265.md` (@ #154), `PRD-267.md` (@ `724d84a`) |

## CB-17 — Raw `net_score` readers (unreachable)

| Kind | Reference |
|---|---|
| Raw storage | `cuttingboard/regime.py:221` |
| Bounded classification | `cuttingboard/regime.py:206-208` |
| Raw readers (decision-bearing) | `cuttingboard/qualification.py:649-653` (`direction_for_regime` NEUTRAL branch); `cuttingboard/market_map.py:407-409`; `cuttingboard/watch.py:453-455` |
| Unreachability chain | `_classify_regime` `:308-316` returns NEUTRAL only for `|bounded_net| ≤ 1` → `confidence ≤ 0.125` → `_determine_posture` `:324-325` global floor `confidence < MIN_REGIME_CONFIDENCE` (`config.py:62` = `0.50`) → `STAY_FLAT` → `qualification.py:368-373` Gate 1 halts before per-symbol work |
| Repo already documents it | `tests/test_regime.py:285-292` — "NEUTRAL_PREMIUM is unreachable via compute_regime at any coverage… the posture branch is retained untouched (parking list, PRD-263 OUT OF SCOPE)" |
| Dead output channel | `cuttingboard/regime.py:344` (`NEUTRAL_PREMIUM`), with trader-facing copy at `cuttingboard/output.py:203`, `cuttingboard/runtime/_constants.py:85`, `cuttingboard/notifications/formatter.py:313,471` |

## CB-18 … CB-30 — remaining rows

| Row | Primary references |
|---|---|
| CB-16 | `docs/sidecar_doctrine.md` — declaration vs prohibition sections; consumer risk is CB-05 |
| CB-18 | `cuttingboard/ingestion.py`, `cuttingboard/validation.py` — `fetched_at_utc = datetime.now()`; no exchange timestamp read |
| CB-19 | `cuttingboard/runtime/__init__.py::_resolve_run_date` — `:2249-2250`; no raw-input snapshot writer anywhere |
| CB-20 | `cuttingboard/manual_journal.py::append_record`; `JOURNAL_PATH = logs/manual_trades.jsonl` (never existed); `cuttingboard/review_scorecard.py::generate_scorecard`; `cuttingboard/runtime/__init__.py::build_parser` `:164-180` (5 args, no `journal`); doctrine: `docs/decision_quality_map.md` Gap 5 |
| CB-21 | `cuttingboard/evaluation.py:31` (`EVALUATION_LOG_PATH`); `cuttingboard/performance_engine.py:28-36`; neither artifact exists on `CB@HEAD` or `CB@publish` |
| CB-22 | `cuttingboard/performance_engine.py:23` (`_MIN_SAMPLE = 5`); aggregation `:85-102`, keyed on symbol only |
| CB-23 | `cuttingboard/evaluation.py:128` — `decision_status == "ALLOW_TRADE"` filter; `docs/decision_quality_map.md` Gap 6 |
| CB-24 | `cuttingboard/config.py:191` (`EVALUATION_WINDOW_BARS = 78`), `EVALUATION_TIMEFRAME = "1m"`; DTE tiers `cuttingboard/options.py:72-74` (7/14/21) |
| CB-25 | `QualificationResult.gates_passed/_failed/_skipped` in `cuttingboard/qualification.py`; absent from `cuttingboard/audit.py::_build_record` `:127-152`; `stay_flat_reason` → `logs/latest_hourly_contract.json` only; `excluded_symbols` prose observed in `CB@publish:logs/audit.jsonl` 2026-05-07 |
| CB-26 | audit record fields `run_at_utc`, `date`; no `run_id` |
| CB-27 | `cuttingboard/runtime/_constants.py:87` vs `cuttingboard/config.py:123`; `docs/runbook.md:94` vs `config.py:124`; `docs/system_logic_map.md:21` (no Polygon code in tree); `cuttingboard/derived.py:8-9` vs `config.py:108`; layer numbering in module docstrings vs `tools/engine_doctor.py:79-95` vs `docs/system_logic_map.md:14-33`. **Dropped from the brief's list:** `docs/regime_model.md:46` is correct. |
| CB-28 | `docs/PROJECT_STATE.md:8` (dated `724d84a`), `:189` (PRD-271 "UNMERGED" — merged @ #173), `:22` ("none in progress" vs registry `:288,291,292,293`), `:207` (baseline pinned to `724d84a`, run 30189828258). Confirmed accurate: `docs/prd_index.json` `latest_complete: 270`, `next_prd: 271` |
| CB-29 | CuttingBoard: zero hits for `dwats250/strategy` or `EA-ENGINE-AUDIT-PROGRAM-REV3`. `STRAT@934ae8b`: `CLAUDE.md:11-14`, `audits/cuttingboard-engine-strategy-audit/`, `plans/EA-ENGINE-AUDIT-PROGRAM-REV3.md`, `docs/INTERFACE_CHARTER_v0.1.md`, `docs/gap-register-2026-07-29.md`, `docs/appraisal-2026-07-29.md`, `docs/owner-decisions-2026-07-30.md` (the three dated docs last touched at `e0e8b759a300923d4c2755cf76410ae603f6a9a4`). CuttingBoard-side half-conversation: `docs/audit/gate_recon_2026-06-12.md:5`, `audits/stage0-recon-2026-07-20/`, `audits/FINDINGS.md:6`. **No CuttingBoard `docs/DECISIONS.md` entry adopts any strategy-side owner decision.** |
| CB-30…CB-47 | `audits/RECONCILED_FINDINGS.md` Tiers 6–7 and § "Additional Codex misses"; `audits/FINDINGS.md` F-09 … F-23. One row per finding; see the matrix table for the ID→finding mapping. Historical citations are at `CB@7f1ff20` and are presumptively stale — re-resolve by symbol before acting on any of them. |

---

## Recon-cache status

`docs/SCHEMA_MAP.md` and `docs/CALL_SITE_MAP.md` were spot-checked on six entries
(`build_pipeline_output_contract`, `build_report_payload`, `render_dashboard_html`,
`_build_macro_drivers`, `_write_macro_snapshot`, `_build_tape_slots`). **All six
resolve correctly at `CB@HEAD`.** No staleness detected in the sample; the maps
were used as the recon cache per `CLAUDE.md` rather than worked around. This is
not a finding.

## Pull requests referenced

| PR | State | Bearing |
|---|---|---|
| #174 | **OPEN**, non-draft, docs-only | Scaffolds PRD-274/275; PRD-275 would close CB-12's artifact-content leg. **Pending evidence, not production.** |
| #173 | MERGED → `9e6b772` | PRD-271 Stage-0 scaffold (CB-07). Contains no fix. |
| #172, #171, #170, #167, #166 | MERGED | Governance and bookkeeping; bear on CB-12b, CB-28 |
| #169 | MERGED (`4a1cb22`) | PRD-273 ruff pin |
| #168 | **CLOSED unmerged** | Superseded PRD-273 attempt; its review artifact recorded ten required edits against a commit that is not an ancestor of `main` |
| #163 | MERGED | PRD-269 — the doc-status leg of CB-12 that DID close |
| #152, #151, #146, #133, #132 | MERGED | CB-15, CB-14, CB-13 |
