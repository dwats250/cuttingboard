# 06 — Repo Hygiene

## TODOs / FIXMEs

Grep across all `.py` under the repo (excluding `.git/`, `.venv/`, `audits/`) returned **zero matches** for `TODO`, `FIXME`, `XXX`, `HACK`. The codebase is rigorous about not leaving inline markers — debt is captured in `PROJECT_STATE.md § Known technical debt` instead.

One unstructured debt note exists out of band: `cuttingboard/runtime.py` ~2100 LOC monolith (recorded in PROJECT_STATE.md, not in code).

## Files missing module docstrings

Files under `cuttingboard/*.py` whose first 5 lines do not include `"""`:

- `cuttingboard/trade_decision.py`
- `cuttingboard/__main__.py` (CLI shim — docstring optional)
- `cuttingboard/notifications/formatter.py`
- `cuttingboard/reports/postmarket.py`
- `cuttingboard/reports/premarket.py`
- `cuttingboard/reports/levels.py`

All others carry module-level docstrings. Six missing in a 60-module package is acceptable; flag for tidy-up if and when those files are next touched.

## Branches in `.git`

### Local

```
  feature/candidate-carousel                22ac254 [ahead 2]
  feature/candidate-surfacing-ui            94970f4
  feature/candidate-surfacing-ui-v2         d3b9aab
  feature/ui-decision-layer                 5bf36b4 [ahead 1]
+ integrate-gitignore                       b56827a [behind 490]
+ integrate-hourly-pages                    008bc95 [behind 487]
+ integrate-main-deploy                     817e87a [behind 491]
* main                                      2937d68
  milestone/dashboard-stable                03e6849
  prd-044-real-macro-driver-payload         a5b1c85
  prd-045-trade-decision-materialization    578e7ca
  prd-046-decision-trace                    7e04913
  prd-047-post-trade-evaluation             775280e
  prd-049-alert-optimization                e43f194
  prd-049-patch-02-guidance                 1fbdfa6
  prd-050-alert-fallback                    603eb38
  prd-051-execution-policy                  da44636
  prd-053-market-map                        67e9589 [ahead 1]
  prd-062-evaluation                        f28b380
  prd061-main                               fcc3278 [behind 486]
  prd4-trade-policy                         77054b3
```

### Remote (origin) — last commit per branch

```
2026-04-13  origin/prd4-trade-policy
2026-04-19  origin/feature/candidate-carousel
2026-04-20  origin/feature/candidate-surfacing-ui
2026-04-28  origin/feature/ui-decision-layer
2026-04-28  origin/prd-044-real-macro-driver-payload
2026-04-28  origin/prd-045-trade-decision-materialization
2026-04-28  origin/prd-046-decision-trace
2026-04-28  origin/prd-047-post-trade-evaluation
2026-04-29  origin/prd-049-alert-optimization
2026-04-29  origin/prd-049-patch-02-guidance
2026-04-29  origin/prd-050-alert-fallback
2026-04-29  origin/prd-051-execution-policy
2026-05-01  origin/prd-053-market-map
2026-05-04  origin/milestone/dashboard-stable
2026-05-20  origin/main
```

### Stale (no commit in 60+ days)

Today is 2026-05-22. 60 days → 2026-03-23. **No branch crosses the 60-day threshold** — the oldest remote branch (`prd4-trade-policy`) is 39 days old. All `prd-*` branches are post-PRD-merge leftovers from April; none are active.

### Recommendations (for cleanup batch, not this audit)

- Remote PRD branches `prd-044` through `prd-053-market-map` correspond to merged PRDs and can be deleted from origin.
- Local-only branches `integrate-*` are behind main by ~490 commits — long-abandoned. Delete after confirming nothing unique remains.
- `prd061-main`, `prd4-trade-policy` are stale by inspection.

## Python files in unusual locations

| Path | Note |
|---|---|
| `algos/__init__.py`, `algos/orb_reference.py` | Outside `cuttingboard/` package. See `03-dead-code.md` + `05-architectural-flags.md`. |
| `backtesting/run_orb_backtest.py` | Outside package. Conflicts with VISION non-goal. |
| `scripts/check_readiness.py` | Operator script. OK. |
| `tools/engine_doctor.py`, `tools/macro_collector.py`, `tools/validate_prd_registry.py` | Sidecars / utilities. OK. |

No Python files were found at the repo root.

## Files in `.gitignore` that are tracked anyway

`.gitignore` ignores `logs/` and `*.json`; the following are tracked via explicit `git add -f` (workflow-driven, intentional):

- `logs/audit.jsonl`
- `logs/last_hourly_slot.json`
- `logs/latest_contract.json`
- `logs/latest_hourly_contract.json`
- `logs/latest_hourly_payload.json`
- *(and other `logs/latest_*.json` listed in the working-tree `git status`)*
- `reports/.gitkeep`

These are explicitly force-added by `.github/workflows/hourly_alert.yml` (`git add -f` allowlist). Not accidental commits — but the pattern is fragile (PRD-142 exists precisely because the allowlist was incomplete). Flag for the cleanup pass to reconcile gitignore vs. force-add allowlist.

## Secrets scan

Pattern grep for `(api_key|api-key|apikey|secret|token|password|bearer)\s*[=:]\s*['"][A-Za-z0-9_-]{16,}` across `*.py`, `*.toml`, `*.yml`, `*.sh`, `*.json` (excluding `.git/`, `.venv/`, `audits/`): **zero matches.**

`.env` file content:

```
POLYGON_API_KEY
```

The file is a single line. The variable name is present without a value (or with an empty value). No secret material is committed.

`.gitignore` correctly excludes `.env` and `.env.*` (lines 2–3). Verified: `.env` is NOT tracked (`git ls-files .env` → empty). The local file exists at 28 bytes for this developer's machine only; production secrets come from GitHub Actions secrets / the runner's env, not the repo.

No action needed on `.env` handling.

## Untracked working-tree files at audit time

Per `git status --short` at the start of this audit:

```
M docs/PRD_REGISTRY.md
 M logs/audit.jsonl
 M logs/latest_contract.json
 M logs/latest_payload.json
 M logs/latest_run.json
 M logs/macro_drivers_snapshot.json
 M logs/market_map.json
 M logs/trend_structure_snapshot.json
?? VISION.md
?? audits/
?? docs/prd_history/PRD-150.md
?? docs/prd_history/PRD-150.review.codex.md
```

`VISION.md` is untracked. This audit does not stage or commit it. PRD-150 and its review file are intentional in-progress drafts.

## Tracked artifacts that look stale

| File | Last commit | Note |
|---|---|---|
| `traceback.txt` | 2026-05-02 (during PRD-069 close-out) | Single-shot debug capture; safe to delete in cleanup. |
| `repo_snapshot.md` | 2026-04-24 | "Repo Snapshot for code review" — frozen, not regenerated. Delete or document as time-capsule. |
| `mockup*.html` (×3) | 2026-04-28 | See `03-dead-code.md § C` and `05-architectural-flags.md § J`. |
| `fix_workflow.sh` | 2026-04-21 | Originated as PRD-004 patch. Verify no current invocation. |
| `.cb_commit_msg` | (no log) | 46-byte file. Unclear purpose. Gitignored but already tracked. |

## Cache / build artifacts in the tree

- `cuttingboard.egg-info/` — setuptools metadata. Should be gitignored (currently absent from `.gitignore`).
- `data/cache/*.parquet` — correctly gitignored.
- `.gitnexus/` — gitignored. `.venv/`, `.pytest_cache/`, `.ruff_cache/` — gitignored.
