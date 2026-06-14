# Project state

Cuttingboard - pre-market options decision-support engine. This is the current
snapshot; it changes fast. Evergreen purpose lives in `VISION.md`, the operating
model in `CLAUDE.md`, full PRD history in `docs/PRD_REGISTRY.md`, and rationale in
`docs/DECISIONS.md`.

**Last updated:** 2026-06-14 (commit 84ca562)

## Current state

- **Active PRD:** none in progress.
- **Proposed / next:** PRD-179 (preview fixture / all-section-state coverage, a fast-follow to PRD-178) — unstarted.
- **Test baseline:** 2610 passing, 1 xfailed (`python -m pytest tests -q` at `84ca562`).
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
