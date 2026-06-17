# Project state

Cuttingboard - pre-market options decision-support engine. This is the current
snapshot; it changes fast. Evergreen purpose lives in `VISION.md`, the operating
model in `CLAUDE.md`, full PRD history in `docs/PRD_REGISTRY.md`, and rationale in
`docs/DECISIONS.md`.

**Last updated:** 2026-06-16

## Current state

- **Active PRD:** PRD-194 (production publish decoupling — dedicated unprotected `publish` branch). CLEARED + IMPLEMENTED on branch `claude/prd-194-publish-decouple`; **PR is MANUAL-MERGE-ONLY — held for human merge (do NOT auto-merge)**, plus a one-time out-of-tree rollout (seed `publish` from `main`, leave it unprotected). Resolves the active blocker the 2026-06-16 staleness audit surfaced: the artifact-publish path (`tools/ci_push_artifacts.sh`, invoked by cuttingboard.yml / hourly_alert.yml / macro_awareness.yml) direct-pushes to `main`, which branch protection (PRD-182/184) rejects (GH006, "Required status check 'test'"), so the dashboard / scoreboard / macro sidecar froze. Design: option (b) + state-home b1 — publish `ui/` AND read-back state to `publish`; pipeline checks out `main` for code and restores state at run start; shared `cb-publish` concurrency group serializes the three writers. **Mechanism pivot (review)**: worktree publish that DELTA-APPENDS this run's `audit.jsonl` rows onto the publish tip (never clobbers) + full-overwrites ui/regime_history — the originally-specified rebase-onto-publish would conflict on the append-only audit log. Two binding amendments applied (A1 explicit restore gate; A2 `workflow_run` deploy for all three writers, since a GITHUB_TOKEN push won't fire `on:push`). CLAUDE.md:52-54 corrected. Validation is the manual rollout (R7 guards pin content, not runtime). Finishes the decoupling PRD-178 began. See docs/prd_history/PRD-194.{md,review.claude.md} and docs/DECISIONS.md (2026-06-16).
- **PRD-189 — MERGED, closeout BLOCKED (do NOT mark COMPLETE):** PR #15 (`b6e036e`) merged 2026-06-16 03:04 UTC. The queue-delay-tolerant resolver was verified **live** — run 27637384167 (2026-06-16 17:56 UTC) resolved the slot to `live`, ran the full pipeline, and committed the 2026-06-16 scoreboard row in the runner — but the push to `main` was rejected by branch protection (GH006), so the scoreboard did not un-freeze. First-slot verification therefore **exposed the publish-push blocker** (→ PRD-194). Closeout is held until PRD-194 lands and a scheduled run publishes a fresh scoreboard row; PRD-191 remains Stage-0 IN PROGRESS, not yet started.
- **PRD-190 — implementing (parallel, greenlit 2026-06-16):** OHLCV fetch window 6→12 months + length-aware (`shape-aware`) cache freshness landed with unit tests (commit `7a53fc4`); `tests/test_derived.py` added to FILES by in-implementation amendment for a widened cache fixture. **R4 GATE PENDING** — the six-symbol live 6mo-vs-~12mo EMA/ATR/SMA pre/post diff requires yfinance egress (unavailable in the authoring sandbox: query1.finance.yahoo.com not in allowlist); it must run in a network-enabled environment before merge, and the lane stays provisional STANDARD until the diff confirms no decision-surface field flips. Independent of PRD-194 (its visible effect on the live site rides on PRD-194 landing).
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
