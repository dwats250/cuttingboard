# Project state

Cuttingboard - pre-market options decision-support engine. This is the current
snapshot; it changes fast. Evergreen purpose lives in `VISION.md`, the operating
model in `CLAUDE.md`, full PRD history in `docs/PRD_REGISTRY.md`, and rationale in
`docs/DECISIONS.md`.

**Last updated:** 2026-06-18 (commit ba8eb20)

## Current state

- **Active PRD:** none in progress.
- **PRD-189 — COMPLETE (2026-06-17):** PR #15 (`b6e036e`) merged 2026-06-16; closeout was held pending PRD-194's publish decoupling. Closed once live run 27665400742 (2026-06-17) published a fresh scoreboard row to the `publish` branch, confirming the queue-delay-tolerant resolver + per-surface freshness work reaches the live site. (Earlier run 27637384167 verified the resolver but hit the GH006 push blocker that PRD-194 resolved.)
- **PRD-190 — IN PROGRESS, implementation on-branch, HELD for review (re-scoped 2026-06-18):** scope narrowed to **config-only** — bump `OHLCV_FETCH_MONTHS` 6→12 (`cuttingboard/config.py:97`) + one R1 regression guard in `tests/test_trend_structure.py`. The populated path is already built and tested, so sma_200 flips null→populated with NO renderer/record/_data_status change. The length-aware (`shape-aware`) cache is now a **NON-GOAL**: the OHLCV cache key is symbol-only (`ingestion.py:369`), so correctness is guaranteed by the code-enforced OHLCV_STALE_HOURS (12h) TTL self-heal — any pre-bump short cache expires within ≤1 session and the next refetch uses the 12-month window; the one-time `rm data/cache/*_ohlcv.parquet` is OPTIONAL acceleration, not load-bearing. The symbol-only-key gap is recorded in the PRD as a latent defect for a future follow-up. LANE escalated to **HIGH-RISK** (global fetch constant shifts ewm(adjust=False) EMA/ATR seed values on the shared regime/derived/execution path; manual-merge + Codex read-only review per Dustin's directive). **R4 GATE — CLEAN** (2026-06-18, live 6mo-vs-12mo EMA/ATR/SMA diff on an egress-enabled host reusing production _build_record + _compute): sma_200 flips null→populated for all six symbols; sma_50/ema9/21/50/atr14 stable to 4 decimals; no decision-surface flip. Codex cross-review (gpt-5.5, `codex exec -s read-only`, fresh-context) returned CONCERNS, dispositioned: MEDIUM doc-consistency reconciled, HIGH stale-cache accepted via the TTL-guarantee reframe (manual `rm` demoted to optional). Grep sweep (2026-06-18) confirmed **zero existing tests pin the broken live state** — all SMA assertions feed synthetic fixtures. Independent of PRD-194.
- **Deferred dependency (PRD-189 → PRD-192):** correctly homing the intraday/orb slots (route through alert_runner/`_execute_notify_run` or hourly_alert.yml) + a per-slot audit dedup marker (runtime/audit.py). Allocated PROPOSED; HIGH-RISK; not opened at Stage 0.
- **Deferred dependency (PRD-189 → PRD-193):** publish-safe prefetch with real OHLCV cache persistence — make the warm-up cache (`data/cache`) persist to the live run (commit or actions/cache) and the prefetch slot publish-safe, then re-add the 12:50 cron to the resolver. Allocated PROPOSED; distinct from PRD-192 (notify routing). Not opened at Stage 0.
- **Proposed / next:** PRD-192 (intraday slot wiring + audit dedup marker) and PRD-193 (publish-safe prefetch + OHLCV cache persistence) — both PROPOSED, deferred from PRD-189; PRD-188 (macro-awareness SHOCK banner + scheduled activation) — PROPOSED, gated on the PRD-187 materiality eval; PRD-179 (preview fixture / all-section-state coverage) still unstarted.
- **Test baseline:** 2801 passing, 1 xfailed (CI truth on `main` after the PRD-195 merge — `test` job of run 27732171939 for `470aa2b`. In this sandbox the same suite reports 2796 passing because 5 git-commit-signing tests — 1 in test_prd_open (test_commit_flag_creates_stage0_commit), 4 in test_prd_registry (R6) — fail environmentally and pass in CI; the recorded baseline is the CI count.).
- **Fixed (PRD-194):** the `hourly_alert.yml` render-before-aggregate nit (hourly published a 1-cycle-stale scoreboard) is resolved — PRD-194 reordered the hourly Aggregate step to run before the render, so the hourly dashboard reflects the current run.
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
| PRD-198 | Semantic-failure hardening doctrine | 2026-06-18 |
| PRD-195 | Publish-branch run_*.json storage cap/prune | 2026-06-18 |
| PRD-196 | prd_close.sh baseline hygiene (robust bullet matching + CI-sourced baseline) | 2026-06-18 |
| PRD-179 | Preview fixture/all-section-state coverage (fast-follow to PRD-178) | 2026-06-17 |
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
