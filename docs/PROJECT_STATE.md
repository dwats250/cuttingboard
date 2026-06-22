# Project state

Cuttingboard - pre-market options decision-support engine. This is the current
snapshot; it changes fast. Evergreen purpose lives in `VISION.md`, the operating
model in `CLAUDE.md`, full PRD history in `docs/PRD_REGISTRY.md`, and rationale in
`docs/DECISIONS.md`.

**Last updated:** 2026-06-22 (PRD-206 PROPOSED — narrow the *regime*.py protected glob)

## Current state

- **Active PRD:** none in progress.
- **PRD-189 — COMPLETE (2026-06-17):** PR #15 (`b6e036e`) merged 2026-06-16; closeout was held pending PRD-194's publish decoupling. Closed once live run 27665400742 (2026-06-17) published a fresh scoreboard row to the `publish` branch, confirming the queue-delay-tolerant resolver + per-surface freshness work reaches the live site. (Earlier run 27637384167 verified the resolver but hit the GH006 push blocker that PRD-194 resolved.)
- **PRD-190 — COMPLETE (2026-06-19):** OHLCV fetch window 6→12 (`config.py`) so `sma_200` resolves and the Trend Structure SMA Composite renders real 50/200 alignment; merged via PR #35 (`0573152`). R4 gate CLEAN; real Codex (gpt-5.5, `codex exec -s read-only`) cross-review CONCERNS dispositioned (HIGH stale-cache accepted via the code-enforced OHLCV_STALE_HOURS TTL self-heal — `sma_200` populates within ≤1 session; manual cache `rm` optional). _Registry + index reconciled to COMPLETE @ `0573152`._
- **PRD-199 — COMPLETE (2026-06-19):** MACRO TAPE tradables (SPY/QQQ/GLD/SLV/GDX/XLE) now show a monochrome daily %-change ↑/↓ arrow — additive `daily_change_pct` in `trend_structure._build_record` → `_pct_arrow`, freshness-gated on `_ts_health == "OK"` (dash when the trend snapshot isn't usable; price stays fresh from market_map); dead `_direction_arrow` tradables branch retired. Merged via PR #37 (`fd27d79`). HIGH-RISK gate satisfied: Claude review ACCEPT + durable Codex (`gpt-5-codex`, read-only, via the PRD-197 CI workflow) APPROVE.
- **Process/tooling -- COMPLETE (2026-06-20):** registry/index/state consistency is now a blocking CI check -- PRD-200 wired `tools/validate_prd_registry.py --skip-commit-resolvability` into the required `test` job (19 historical unresolvable hashes deferred; see Known technical debt). PRD-201 added a non-blocking `PreToolUse(Read)` hook (`.claude/hooks/canonical_read_guard.sh`) that reminds against re-reading the injected canonical docs (CLAUDE.md, MEMORY.md). PRD-202 added recon-efficiency Workflow-pattern guidance to CLAUDE.md (consult SCHEMA_MAP/CALL_SITE_MAP before location-greps; delegate bookkeeping recon).
- **Deferred dependency (PRD-189 → PRD-192):** correctly homing the intraday/orb slots (route through alert_runner/`_execute_notify_run` or hourly_alert.yml) + a per-slot audit dedup marker (runtime/audit.py). Allocated PROPOSED; HIGH-RISK; not opened at Stage 0.
- **Deferred dependency (PRD-189 → PRD-193):** publish-safe prefetch with real OHLCV cache persistence — make the warm-up cache (`data/cache`) persist to the live run (commit or actions/cache) and the prefetch slot publish-safe, then re-add the 12:50 cron to the resolver. Allocated PROPOSED; distinct from PRD-192 (notify routing). Not opened at Stage 0.
- **Proposed / next:** PRD-206 (narrow AGENT_WORKFLOW.md's `*regime*.py` protected glob to `regime.py` so the PRD-175 read-only sidecar stops false-positiving the scope gate — governance, manual-merge; queued after PRD-204); PRD-192 (intraday slot wiring + audit dedup marker) and PRD-193 (publish-safe prefetch + OHLCV cache persistence) — both PROPOSED, deferred from PRD-189; PRD-188 (macro-awareness SHOCK banner + scheduled activation) — PROPOSED, gated on the PRD-187 materiality eval (go/no-go by 2026-07-15); PRD-179 (preview fixture / all-section-state coverage) still unstarted.
- **Test baseline:** 2819 passing, 1 xfailed (CI truth on `main` -- `test` job of run 27865518359 for `b1f2598`, the PRD-201 merge; PRD-202 added no tests. This sandbox now matches CI at 2819.).
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
| PRD-202 | Agent-efficiency guidance: consult recon maps + delegate bookkeeping recon | 2026-06-20 |
| PRD-201 | Canonical read-guard hook (warn on redundant re-read of injected docs) | 2026-06-20 |
| PRD-200 | Enforce registry/index/state consistency on the CI merge path | 2026-06-20 |
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
- **19 historical registry commit hashes are unreachable from `main`.** PRD-076,
  081, 083, 085, 086, 088, 090, 096, 100, 102, 125, 126, 133, 139, 158, 161, 167,
  168, 169 record COMPLETE commits that were squash-merged/rebased away, so the
  validator's commit-resolvability check cannot pass in a clean CI checkout.
  PRD-200 CI-skips that check (`--skip-commit-resolvability`) and enforces
  consistency only; resolvability is unaffected relative to before (the validator
  ran nowhere automatically). Follow-up: triage/fix the 19 hashes to their on-main
  commits, then re-enable resolvability in CI (drop the flag, re-add
  `fetch-depth: 0`). **Re-evaluate by 2026-07-31** (next alignment cadence).

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

Active per `CLAUDE.md`. Last check ran 2026-06-20 (#4, PASS, no drift; reviewed
PRD-200/201/202; one stale test-baseline annotation remediated in place -- see
`docs/DECISIONS.md`). Next check by 2026-07-31, or at the next phase boundary,
whichever comes first.
