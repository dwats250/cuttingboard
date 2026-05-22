# 03 — Dead Code Candidates

All flags below are **candidates only**. Static analysis cannot prove unreachability; dynamic imports, reflection, fixture-mode paths, and operator scripts may keep code alive in ways grep cannot see. Final decisions belong to Dustin / Claude (project lead).

Tag legend: `[ORPHAN]` no inbound imports, `[TEST-ONLY]` only imported by tests, `[STALE]` mtime > 30 days plus zero-or-near-zero current usage, `[SCHEDULED-FOR-DELETION]` per `VISION.md` known cleanup list.

---

## A. Scheduled for deletion (per VISION.md)

These are listed without depth per the brief's instructions.

### Polygon integration

- `cuttingboard/config.py:54` — `POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")`
- `cuttingboard/config.py:175` — `"default": ["yfinance", "polygon"]` source-priority entry
- `cuttingboard/config.py:220–223` — `POLYGON_PREV_URL` constant + comment
- `cuttingboard/ingestion.py` — `_try_polygon_quote`, `_polygon_quote_raw`, `"polygon"` source branch (`:35, 99–100, 359–448`)
- `cuttingboard/contract.py:475` — `if any(...source == "polygon"...)` fallback flag
- `cuttingboard/runtime.py:1149, 2017` — polygon-fallback-used branches
- `.env` — `POLYGON_API_KEY` env var
- 77 references total across `.py / .md / .toml / .sh / .yml` (excluding `.git/`, `audits/`).
- All tagged `SCHEDULED-FOR-DELETION`.

### ntfy alerts

ntfy code is **already largely removed** (PRD-006). Remaining references are documentation-only and a few test guards that *enforce* removal:

- `README.md:45, 97` — outdated doc lines mentioning ntfy.
- `CODEX.md:37` — pipeline table still labels `notifications/` as "ntfy alert formatting" (drift).
- `docs/architecture.md:23, 41, 45, 190, 195, 200, 259, 323, 365` — multiple outdated lines.
- `docs/engine_doctor.md:93` — `.env` doc lists ntfy.
- `tests/test_hourly_alert.py` — uses `format_ntfy_alert` (function still named with `ntfy` suffix in `notifications/formatter.py:58`).
- `tests/test_prd006_notification_transport.py` — actively asserts ntfy *removal* (these tests should be **kept**).
- `.claude/skills/generated/notifications/SKILL.md` — references `format_ntfy_alert`.
- `cuttingboard/notifications/formatter.py:58` — function name `format_ntfy_alert` is the last live ntfy-named symbol; it no longer talks to ntfy. Tagged `SCHEDULED-FOR-DELETION` (rename or remove).
- Topic string `cuttingboard86` — no grep hits in the repo. Already gone.

### PRD-142 code-only-for-PRD-142

PRD-142 (`docs/prd_history/PRD-142.md`) is `IN PROGRESS` per registry and proposes adding a conditional `git add -f logs/last_hourly_slot.json` to `.github/workflows/hourly_alert.yml`. **No code or workflow change has landed yet** — `hourly_alert.yml` does not contain `last_hourly_slot.json` in any `git add` line. VISION.md schedules PRD-142 for kill. Nothing to delete in source; only the PRD document and registry row to be closed as DEPRECATED. Tagged `SCHEDULED-FOR-DELETION` at the PRD level.

---

## B. Orphan / near-orphan production modules

| Module | Last commit | Inbound (prod) | Inbound (test) | Note |
|---|---|---|---|---|
| `cuttingboard/notify_test.py` | 2026-04-24 | 0 | 0 | Ad-hoc Telegram smoke-test script inside the production package. `[ORPHAN]` + `[STALE]`. |
| `cuttingboard/run_intraday.py` | 2026-04-28 | 0 | 0 | CODEX.md explicitly: "Unscheduled legacy module. … Not invoked by any workflow." `[ORPHAN]` + `[STALE]`. |
| `cuttingboard/sector_router.py` | 2026-04-21 | 1 (`qualification.py`) | unverified | One inbound; verify whether call is live. `[STALE]`. |
| `algos/orb_reference.py` | 2026-04-28 | 0 (outside cuttingboard) | 1 (`tests/test_orb_reference.py`) | `[TEST-ONLY]`. |
| `backtesting/run_orb_backtest.py` | 2026-04-28 | 0 | 0 | Backtest harness. Conflicts with VISION ("Not a backtesting framework"). `[ORPHAN]` + see `05-architectural-flags.md`. |

## C. Root-level files with no apparent runtime role

| File | Last commit | Note |
|---|---|---|
| `mockup.html` | 2026-04-28 (commit 1a07e2c) | UI theme mockup. Not referenced from any Python module or workflow. `[STALE]`. |
| `mockup_echofi.html` | 2026-04-28 | Same. `[STALE]`. |
| `mockup_zeex.html` | 2026-04-28 | Same. `[STALE]`. |
| `traceback.txt` | 2026-05-02 | One-shot debug artifact; committed by accident? |
| `repo_snapshot.md` | 2026-04-24 | "Repo Snapshot for code review" — frozen-in-time doc. |
| `fix_workflow.sh` | 2026-04-21 | Originated in PRD-004 patch; not invoked by current CI. |
| `.cb_commit_msg` | (no log) | 46-byte file; provenance unclear. |
| `validate_cuttingboard.sh` | (verify) | 9.2KB shell script at root; verify whether referenced by any workflow / docs. |

## D. Empty / near-empty directories

- `config/` — contains only `__pycache__/`. No `config/*.py` exists; `cuttingboard/config.py` is the real config. **`config/` looks dead.**
- `cuttingboard.egg-info/` — setuptools build metadata; shouldn't be committed long-term.
- `.worktrees/` — local git worktree storage; not for repo content.

## E. Modules with low inbound count worth a second look

(Not necessarily dead — flagged for Dustin's judgment whether each earns its keep.)

| Inbound | Module |
|---|---|
| 1 | `alert_runner.py` — invoked only by `hourly_alert.yml` (workflow), not imported by other code. Confirmed-live via CI. |
| 1 | `confirmation.py` — used only by `intraday_state_engine.py`. Both are part of the intraday mini-pipeline. |
| 1 | `evaluation.py` — used only by `runtime.py`. Live via `run_post_trade_evaluation()`. |
| 1 | `manual_journal.py` (PRD-070) — used only by tests? Verify production wiring. |
| 1 | `review_scorecard.py` (PRD-071) — verify production wiring. |
| 1 | `notifications/formatter.py` — used by `notifications/__init__.py`. Internal. |
| 2 | `delivery/html_renderer.py` — auxiliary HTML helpers; verify usage. |
| 2 | `entry_quality.py` (PRD-069) — verify. |
| 2 | `intraday_state_engine.py` — verify production wiring vs `run_intraday`. |
| 2 | `notifications/state.py` | |
| 2 | `performance_engine.py` (PRD-075) | |
| 2 | `sector_router.py` | (also flagged above) |
| 2 | `trade_explanation.py` (PRD-046) | |
| 2 | `trade_policy.py` | |
| 2 | `trade_thesis.py` (PRD-067) | |
| 2 | `trend_structure.py` (PRD-107) | |
| 2 | `watchlist_sidecar.py` (PRD-114) | |

For each: best-effort check is whether `runtime.py` calls into the module. Several PRD-tagged modules (review_scorecard, manual_journal, entry_quality, trade_thesis) are flagged in VISION.md's "cuts before additions" principle as candidates for the "earn-your-keep" review.

## F. Config options never referenced

Audit deferred — `config.py` is 200+ lines of constants; verifying each requires a grep per symbol. Recommend producing this list as a follow-up grep matrix during the cleanup pass. Known no-longer-needed:

- `POLYGON_API_KEY`, `POLYGON_PREV_URL`, `"polygon"` entries in source-priority maps (`SCHEDULED-FOR-DELETION`).

## G. Env vars declared but never read

From `cuttingboard/config.py` declarations vs `os.getenv` / `os.environ` calls across `cuttingboard/`:

| Env var | Declared | Read | Status |
|---|---|---|---|
| `POLYGON_API_KEY` | `config.py:54` | `ingestion.py` | `SCHEDULED-FOR-DELETION`. |
| `TELEGRAM_BOT_TOKEN` | `config.py:55` | `output.py` (Telegram path) | Live. |
| `TELEGRAM_CHAT_ID` | `config.py:56` | `output.py` | Live. |
| `CUTTINGBOARD_FORCE_SLOT` | not in config.py | `alert_runner.py:45` | Live (PRD-141/149). |
| `FIXTURE_MODE` | not in config.py | `runtime.py:1875, 1989`, `delivery/dashboard_renderer.py:409, 2193` | Live. |
| `PYTEST_CURRENT_TEST` | (pytest-set) | `output.py:93` | Live (test guard). |
| `ANTHROPIC_API_KEY` | `tools/macro_collector.py` reads directly via `os.environ` | sidecar use | Outside `cuttingboard/`. |

No declared env var is unread inside `cuttingboard/` other than Polygon.

## H. Test files for modules that no longer exist

Grep showed every `tests/test_<x>.py` has a matching cuttingboard module or a documented PRD subject. **No orphan test files found.** The test names that don't map one-to-one (e.g. `test_phase1.py`, `test_phase5.py`, `test_phase6.py`, `test_prd006_notification_transport.py`, `test_prd_eval_hook.py`) are PRD- or phase-scoped suites, not module-mapped. They cover live code.

## I. Defined-but-uncalled functions/classes

Out of scope for this pass — no whole-program call-graph tool was run. The two areas most likely to harbor uncalled symbols:

- `runtime.py` (~2100 LOC monolith) — internal helpers may be dead.
- `cuttingboard/notifications/formatter.py` — historical AUDIT_PRD016 flagged `ntfy_title()` as never-called; status today **unverified**.

Recommend running `vulture` or equivalent during the cleanup pass.
