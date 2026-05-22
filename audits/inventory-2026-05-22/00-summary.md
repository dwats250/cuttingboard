# 00 — Executive Summary

Audit date: 2026-05-22. Branch `main` @ `2937d68`. Read-only.

## Repo size

| Metric | Value |
|---|---|
| Total files (excl. `.git`, caches, venvs) | 566 |
| Production Python (`cuttingboard/*.py`) | 60 modules / ~18.3k LOC |
| Tests (`tests/test_*.py`) | 85 files / ~30k LOC / 2524 passing (per PROJECT_STATE.md) |
| Markdown | 247 files |
| JSON | 57 |
| Parquet (OHLCV cache) | 40 |
| Shell scripts | 14 |
| PRDs in registry / on disk | 158 rows / 177 PRD-prefixed files |

## Headline findings

1. **`run_intraday.py` is fully orphaned.** CODEX.md explicitly labels it "unscheduled legacy, not invoked by any workflow." Zero inbound imports. Listed in `03-dead-code.md`.
2. **Backtesting + ORB reference sit in conflict with VISION.md.** `backtesting/run_orb_backtest.py`, `algos/orb_reference.py`, and three root `mockup*.html` files exist alongside a VISION that says "not a backtesting framework." None are referenced from production code. See `05-architectural-flags.md § A,B,J`.
3. **Polygon footprint is wide but mechanically simple.** 77 references across `.py / .md / .toml / .sh / .yml`. Concentrated in `config.py:54,175,220–223` and `ingestion.py:35,99–100,359–448` plus `contract.py:475`, `runtime.py:1149,2017`. Tagged `SCHEDULED-FOR-DELETION` per VISION.md.
4. **ntfy is mostly removed but documentation is stale.** PRD-006 cut the code path. Lingering references: `README.md:45,97`; `CODEX.md:37` ("notifications/ = ntfy alert formatting" — wrong); `docs/architecture.md` (9 lines); `docs/engine_doctor.md:93`; one function name `format_ntfy_alert` in `notifications/formatter.py:58`. Tests in `test_prd006_notification_transport.py` *enforce* removal — keep those.
5. **PRD-142 has not landed.** Registry says `IN PROGRESS`; `hourly_alert.yml` does not contain the `git add -f logs/last_hourly_slot.json` change the PRD specifies. VISION.md schedules PRD-142 for kill — registry needs to flip to `DEPRECATED`.
6. **PRD-053 / 053-PATCH carry non-canonical `READY` status.** `CLAUDE.md § lifecycle states` permits only PROPOSED / IN PROGRESS / COMPLETE / PATCH / DEPRECATED. PRD-054 ("Add trade framing to market map sidecar") is COMPLETE — suggesting PRD-053 was de-facto absorbed. Registry needs reconciliation.
7. **CODEX.md is materially drifted.** "830 tests passing (2026-04-27)" vs. actual 2524 in `PROJECT_STATE.md`. `notifications/` description outdated. Consider deprecating CODEX.md in favor of PROJECT_STATE.md as the single source of truth.
8. **Two production orchestrators**: `runtime.cli_main` and `alert_runner.main`. Deliberate (the hourly dedup gate must run before the heavy pipeline) but worth confirming the split is intentional.
9. **`runtime.py` is ~2100 LOC** and edited by every notification-path PRD. Already documented as known debt in PROJECT_STATE.md.
10. **No secrets committed.** `.env` is correctly gitignored and not tracked. No high-entropy strings found in scanned files.

## Counts

| Bucket | Count |
|---|---|
| Orphan production modules (0 inbound prod imports) | 2 (`run_intraday.py`, `notify_test.py`) plus `time_utils` undercounted-but-actually-5 |
| `[STALE]` modules (mtime >30d + ≤1 inbound) | ~4 (`notify_test.py`, `run_intraday.py`, `sector_router.py`, `algos/orb_reference.py`) |
| Root-level stale files | 7 (3× mockup HTML, `traceback.txt`, `repo_snapshot.md`, `fix_workflow.sh`, `.cb_commit_msg`) |
| PRDs flagged for status reconciliation | 4 (PRD-053, 053-PATCH, 054, 142) |
| PRDs scheduled for kill | 1 (PRD-142) |
| PRDs in active draft | 1 (PRD-150) |
| TODO / FIXME / XXX / HACK in `*.py` | 0 |
| Stale git branches (>60 days) | 0 (oldest remote = 39 days) |
| Stale-by-purpose branches (post-merged PRD branches) | ~12 on origin, similar locally |
| Modules missing module docstring | 6 |
| Declared deps not directly imported by `cuttingboard/` | 2 (`numpy`, `pyarrow` — both likely transitive via pandas; verify) and 1 unconfirmed (`pytest-mock`) |

## Open questions for Dustin

1. **PRD-053 vs PRD-054**: did PRD-053 land as part of PRD-054, or is the "Graded market map sidecar" actually still pending? `READY` status in the registry is non-canonical.
2. **`market_map_lifecycle.py`**: confirm it annotates only and does not mutate sidecar state — VISION.md says sidecars must be read-only.
3. **`tools/macro_collector.py`**: an LLM-call-driven macro snapshot sidecar exists (PRD-139) with no runtime consumer. Does this satisfy "description, not prediction" given its current state, or is it a future-prediction-engine in disguise that should be killed before it grows a consumer?
4. **`backtesting/run_orb_backtest.py` + `algos/orb_reference.py`**: keep as reference/experimentation, move out of repo, or delete?
5. **`alert_runner.py` vs `runtime.py`**: confirm the two-entrypoint split is deliberate.
6. **`CODEX.md`**: deprecate in favor of PROJECT_STATE.md, or refresh? Currently drifted on test count and notifications description.
7. **`config/` directory** (empty except `__pycache__`): delete?
8. **`.cb_commit_msg`**: 46-byte file of unclear provenance. Delete?
9. Should PRD-142 be flipped to `DEPRECATED` as part of this cleanup, or does it stay `IN PROGRESS` until the "consolidated cleanup commit set" (VISION.md Phase 1 step 2)?

## Known limits of this analysis

- **No call-graph tool was run.** Defined-but-uncalled functions/classes are mostly unflagged; recommend `vulture` during the cleanup pass.
- **PRD-to-code conformance was not verified per PRD.** "COMPLETE-AND-MATCHES" is a presumption based on registry status, not behavioral comparison against each PRD's FAIL conditions. Spot-checking each PRD's `FILES` list against the live tree would surface reverse drift — out of scope for an inventory.
- **`numpy` and `pyarrow` direct usage** could not be confirmed by grep in `cuttingboard/`. Both are likely consumed transitively (parquet I/O, pandas internals). Verify before removing.
- **Dynamic imports / reflection / fixture-mode paths** are invisible to static grep. Any "orphan" flag should be cross-checked against `runtime.py`'s fixture-mode branches and the workflow YAML files before deletion.
- **PRD-142 implementation status** was inferred from absence in `hourly_alert.yml`; it's possible the workflow change exists on a branch not yet merged.
- **Branch staleness threshold (60 days)** produced zero hits. Lowering to 30 days surfaces the 12+ post-merge PRD branches.
- **Secrets scan is pattern-based**, not entropy-based. A high-entropy string with no `key=`/`token=` prefix would not match. Recommend `gitleaks` during the cleanup pass for completeness.

## Reading order

`00-summary.md` (this file) → drill into:

- `03-dead-code.md` for deletion candidates
- `04-prd-drift.md` for registry reconciliation
- `05-architectural-flags.md` for VISION-alignment items
- `01-structure.md`, `02-dependencies.md`, `06-hygiene.md` for reference / lookup

Decisions on flagged items belong to Dustin (and Claude project-lead as VISION.md § "How we work" defines). This audit does not propose deletions or fixes.
