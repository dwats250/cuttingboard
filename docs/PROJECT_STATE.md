# Project state

Cuttingboard - pre-market options decision-support engine. This is the current
snapshot; it changes fast. Evergreen purpose lives in `VISION.md`, the operating
model in `CLAUDE.md`, full PRD history in `docs/PRD_REGISTRY.md`, and rationale in
`docs/DECISIONS.md`.

**Last updated:** 2026-06-16

## Current state

- **Active PRD:** PRD-189 (live-pipeline mode resolution + per-surface freshness observability) — IMPLEMENTING (reduced scope). The run-mode resolver (scripts/resolve_run_mode.py) is scoped to the dedicated premarket crons that write fresh, publish-safe artifacts — **live + sunday** — via a cron-string lookup. After Codex review, the intraday/orb slots and their crons were removed (notify path is runtime `_execute_notify_run`, not cli_main; hourly_alert.yml already covers the window → PRD-192), AND the 12:50 `prefetch` cron was dropped to noop (its publish trips the PRD-119 freshness gate on a stale payload, and its `data/cache` warm-up never persists → PRD-193). Renderer live-state/scoreboard age tokens landed too (LIVE STATE sources logs/latest_run.json, not the hourly --run override; cuttingboard.yml aggregates regime_history before render so SCOREBOARD is fresh on the scheduled publish). The now-noop prefetch + intraday crons are left in `on.schedule` (parked dead-noop, prune in a future tidy-up). On the feature branch with tests; HIGH-RISK review (Claude + Codex) done, holding for human merge. PRD-190 and PRD-191 remain Stage-0 IN PROGRESS, not yet started.
- **Deferred dependency (PRD-189 → PRD-192):** correctly homing the intraday/orb slots (route through alert_runner/`_execute_notify_run` or hourly_alert.yml) + a per-slot audit dedup marker (runtime/audit.py). Allocated PROPOSED; HIGH-RISK; not opened at Stage 0.
- **Deferred dependency (PRD-189 → PRD-193):** publish-safe prefetch with real OHLCV cache persistence — make the warm-up cache (`data/cache`) persist to the live run (commit or actions/cache) and the prefetch slot publish-safe, then re-add the 12:50 cron to the resolver. Allocated PROPOSED; distinct from PRD-192 (notify routing). Not opened at Stage 0.
- **Proposed / next:** PRD-192 (intraday slot wiring + audit dedup marker) and PRD-193 (publish-safe prefetch + OHLCV cache persistence) — both PROPOSED, deferred from PRD-189; PRD-188 (macro-awareness SHOCK banner + scheduled activation) — PROPOSED, gated on the PRD-187 materiality eval; PRD-179 (preview fixture / all-section-state coverage) still unstarted.
- **Test baseline:** 2719 passing, 1 xfailed (`python -m pytest tests -q` on the PRD-189 branch; in this sandbox 5 git-commit-signing tests — 1 in test_prd_open (test_commit_flag_creates_stage0_commit), 4 in test_prd_registry (R6) — fail environmentally and pass in CI).
- **Parked (future cleanup, surfaced in PRD-189 review):** `hourly_alert.yml` renders the dashboard BEFORE it runs the `regime_history` aggregation, so hourly publishes show a 1-cycle-stale scoreboard. Pre-existing and out of PRD-189 scope (PRD-189 fixed only the `cuttingboard.yml` scheduled-publish path, which now aggregates before rendering). Reorder hourly_alert.yml (aggregate-then-render) in a future cleanup.
- **Recently landed and live:**
  - The market-stress kill switch forces a terminal HALT (PRD-180). The
    thresholds and conflict resolution are canonical in
    `docs/system_logic_map.md`.
  - The SHORT permission gate fails closed during the 09:30-09:45 ET open window
    when intraday state is unavailable (PRD-181); LONG side and post-09:45 gating
    are unchanged.

## Recent ships

| PRD | Title | Completed |
|-----|-------|-----------|
| PRD-187 | Macro-Awareness Producer + Materiality Eval | 2026-06-15 |
| PRD-186 | Drift-review gate: per-PRD drift check + post-merge audit teeth + governance auto-merge carve-out | 2026-06-14 |
| PRD-185 | Bump GitHub Actions to Node 24 majors (checkout v6, setup-python v6, upload-artifact v7) | 2026-06-14 |
| PRD-184 | Auto-merge-via-PR landing flow (Claude push enablement) | 2026-06-14 |
| PRD-183 | Realign closeout tooling to the new PROJECT_STATE format | 2026-06-14 |
| PRD-182 | CI merge gate + pre-push full-suite + cuttingboard.yml env-default lint fix | 2026-06-14 |
| PRD-181 | Short-gate fail-closed during the open window | 2026-06-13 |
| PRD-180 | Kill switch forces real HALT (HaltCause primitive; cause-labeled banner) | 2026-06-13 |
| PRD-178 | Dashboard fresh-data preview loop (CI preview workflow + local script) | 2026-06-13 |
| PRD-177 | Dashboard realignment pass 2 (cuts, four-questions reorder, macro evidence) | 2026-06-10 |
| PRD-176 | Red-folder economic-calendar loader | 2026-06-10 |
| PRD-175 | Historical regime scoreboard aggregation sidecar | 2026-06-10 |
| PRD-174 | Trend-structure OHLCV on STAY_FLAT hourly runs | 2026-06-10 |
| PRD-173 | runtime/ package skeleton (Stage A of the runtime split) | 2026-06-10 |

Full history: `docs/PRD_REGISTRY.md`.

## Known technical debt

- **The `runtime/` package split is mid-way.** The skeleton landed (PRD-173); the
  leaf-extraction stages (B through I) from the PRD-170 cut-line roadmap are not
  yet scheduled, so every notification-path change still edits one large
  `runtime/__init__.py`. **Re-evaluate by 2026-08-15** (per the VISION principle
  that acknowledged debt carries a re-evaluation date).

## Parked (reopen only under the stated condition)

Deliberately deferred during the 2026-06-10 dashboard-batch scoping:

- **near-miss-surface** - "the closest setup that failed qualification, and which
  gate killed it." High learning value, but needs qualification introspection and
  flirts with signal-engine creep. Earn it after the regime scoreboard proves the
  learning-layer concept.
- **red-folder-entry-gate** - fail-closed entry gating on red-folder event
  windows. Out of PRD-176 (render-only). Needs its own fail-closed design first.
- **section-registry-refactor** - replace the renderer's inline section sequence
  with a data-driven registry. HIGH-RISK renderer work; reopen only if a
  post-PRD-177 renderer PRD shows continued section churn.

## Alignment cadence

Active per `CLAUDE.md`. Last check ran 2026-05-29 (PASS, no drift; see
`docs/DECISIONS.md`). Next check by 2026-07-03, or at the next phase boundary,
whichever comes first.
