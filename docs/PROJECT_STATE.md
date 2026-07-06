# Project state

Cuttingboard - pre-market options decision-support engine. This is the current
snapshot; it changes fast. Evergreen purpose lives in `VISION.md`, the operating
model in `CLAUDE.md`, full PRD history in `docs/PRD_REGISTRY.md`, and rationale in
`docs/DECISIONS.md`.

**Last updated:** 2026-07-05 (PR #115)

## Current state

- **Active PRD:** none in progress.
- **PRD-243 — COMPLETE (2026-07-05, PR #115):** lifecycle-audit subtraction block (P3/P4/P7), nothing added. `prd_eval.sh` keyword detectors retired — the hook now carries ONLY the registry-gap check (behavior-proven: the six-misfire notification shapes emit 0 bytes post-edit; the gap check still fires; +3 red tests). Entire GitNexus surface deleted (12 stale skills, `gitnexus-analyze.sh`, the `pre_commit_sanity.sh` detect-changes step with its fabricated "CLAUDE.md § GitNexus" citation) with all live inbound references reconciled (authoring/review skills' recon chains, `knowledge_systems.md` retirement record); commit path behavior-proven (script exit 0 on a real staged diff). Phantom-SHA debt closed WONTFIX-HISTORICAL (29 PRDs / 35 tokens; see Known technical debt). Rides PR #115 with PRD-242.
- **PRD-242 — COMPLETE (2026-07-05, PR #115):** HIGH-RISK gate Option A from the lifecycle audit (`audits/prd-lifecycle-audit-2026-07-05/`). The second review leg is now the fresh-context Claude review + Dustin's manual merge; a second-model review (Codex or other) is an instrument Dustin may commission, never a requirement owed. Every COMPLETE HIGH-RISK PRD ≥ 242 must carry either a commissioned `PRD-NNN.review.<model>.md` artifact or the verbatim `SECOND-MODEL: instrument not commissioned, merging on Claude-review + human judgment.` line in its PRD doc — enforced by `tools/validate_prd_registry.py` on the CI `test` check (+8 tests, mutation-verified). The connector-bot post-merge net (PRD-228 disposition clause) is unchanged. Governance change: MANUAL-MERGE-ONLY, rides PR #115.
- **PRD-241 — COMPLETE (2026-07-05, PR #113):** qualification doc truth. `system_logic_map.md` gate count fixed (11 = 4 hard + 7 soft); `trade_qualification.md` now documents the post-PRD-240 Gate 6 floors, all three Gate 7 regime R:R tiers, and — for the first time — the CONTINUATION and FVG PULLBACK_IMBALANCE entry modes (gate tables, rejection taxonomy, the synthetic-reward stop-width-ceiling arithmetic, the deliberate continuation no-ATR-floor asymmetry). All 16 documented values verified against config.py.
- **PRD-240 — COMPLETE (2026-07-05, PR #111):** qualification tuning from the 2026-07-05 audit, approved by Dustin same day. EXPANSION_RR_RATIO 1.5→2.0 (discount removal); Gate-6 ATR stop floor 0.5→1.0× as `STOP_ATR_FLOOR_K`; shared `MIN_STOP_PCT`; `CONTINUATION_REWARD_ATR_MULTIPLE=3.0` replaces the disguised-constant reward expression; `_min_rr_for_regime()` shared by Gate 7 and `_resolve_entry_mode`; continuation momentum now requires close_location ≥ 0.75; continuation stop-floor asymmetry retained + documented in-code (R6). Amendment 1 added `tests/test_account_equity_sizing.py` (Gate-8 fixture geometry hit by the new floor). +4 mutation-verified red tests; mutation checks run independently three times (implementer / lead / reviewer). HIGH-RISK gate: fresh-context Claude review ACCEPT (`PRD-240.review.claude.md` @ `da214f7`); Codex leg = Dustin's manual merge records the waiver (no codex CLI in the remote container, Fable-window pattern) — **PR #111 merged manually by Dustin 2026-07-05.** Deferred non-blocking review recommendations: (1) `runtime/__init__.py` carries a third min-RR tier duplicate feeding `min_rr_applied` — not converted to the shared helper (runtime refactors require their own PRD); (2) name the 0.75 close-location literal (next polish batch).
- **Next step:** Work the master plan: `audits/codebase-review-2026-07-03/MASTER_PLAN.md` (find the first unchecked box — the post-window queue is consolidated in DECISIONS 2026-07-05: D/E/F, K/L/M execution per `docs/renderer_decomposition_map.md`, plus the review-surfaced follow-ups).
- **PRD-226/PRD-227 — COMPLETE (2026-07-05):** level-diagram NOW anchor now draws from the live current price (`now_price`, required, non-finite/absent suppresses the diagram) rather than the contract's planned entry — the contract entry now renders its own amber ENTRY line, coinciding silently with NOW when equal (PRD-226); PRD-221's phantom pre-squash SHA corrected to its true squash-merged commit (PRD-227). Predates the Fable window (opened 2026-07-03 from the codex-connector review audit); held for manual merge per its HIGH-RISK/CONSUMER lane. Full gate satisfied pre-window: fresh-context Claude review ACCEPT + durable Codex cross-review APPROVE (`gpt-5.5`, read-only), both SHA-pinned to `3ffa027`. **Post-window integration:** merged `main` in to resolve the registry/index conflicts left by the Fable window's PRDs 228–239 (two bookkeeping-only hunks, both resolved to main's side; zero code conflicts — the window's contract-typing edit and this PR's `now_price` edit are in disjoint regions of `dashboard_renderer.py`). The `3ffa027` review pin covers all code; the integration merge adds no code delta, only conflict resolution, so no re-review was required — Dustin's manual merge is the waiver for the merge commit itself, per the window's established artifact-or-waiver pattern. Merged via PR #95.
- **PRD-228 — COMPLETE (2026-07-04):** bot-review-thread disposition clause in CLAUDE.md — connector-bot review threads are advisory input, never gate-satisfying; every substantive thread is ACTIONED (fix + cite SHA/PRD + resolve) or DISMISSED with an in-thread reason. Merged by hand per the governance carve-out as PR #96 (`a11481b`); registry row reconciled to COMPLETE in this closeout.
- **PRD-204 — COMPLETE (2026-06-23):** non-destructive scoreboard aggregate. `regime_history.aggregate()` now PRESERVES last-known-good `spy_close_change_pct` (with an always-present observable `spy_close_change_pct_stale` marker) instead of overwriting it with `null` when `data/cache/SPY_ohlcv.parquet` is absent — the prior wipe blanked the published scoreboard's "SPY next" column for all historical rows (PRD-198 invariant #1; restored the gain-only docstring). The publish workflows now restore `logs/regime_history.jsonl` before aggregating so the preserve reads the live scoreboard, not main's frozen fallback (Amendment 1, env-parity-guarded), and absent/partial-source gaps are logged loudly (Amendments 2–3). The stale-tail-cache warning P2 was declined as already covered by the OHLCV cache freshness self-heal (then the PRD-190 `OHLCV_STALE_HOURS` TTL; retired by PRD-193, which replaced it with a trading-day freshness model that re-fetches every new weekday). Merged via PR #52 (`9c1fb37`); Claude review ACCEPT; Codex P1 + two R3 P2s dispositioned. Distinct from PRD-193 (cache persistence, defense-in-depth). (The originally-planned PRD-206 protected-glob follow-up was voided; PRD-206 is now a skipped number.)
- **PRD-189 — COMPLETE (2026-06-17):** PR #15 (`b6e036e`) merged 2026-06-16; closeout was held pending PRD-194's publish decoupling. Closed once live run 27665400742 (2026-06-17) published a fresh scoreboard row to the `publish` branch, confirming the queue-delay-tolerant resolver + per-surface freshness work reaches the live site. (Earlier run 27637384167 verified the resolver but hit the GH006 push blocker that PRD-194 resolved.)
- **PRD-190 — COMPLETE (2026-06-19):** OHLCV fetch window 6→12 (`config.py`) so `sma_200` resolves and the Trend Structure SMA 50/200 cell renders real 50/200 alignment (renamed from "SMA Composite" by PRD-208); merged via PR #35 (`0573152`). R4 gate CLEAN; real Codex (gpt-5.5, `codex exec -s read-only`) cross-review CONCERNS dispositioned (HIGH stale-cache accepted via the code-enforced OHLCV cache freshness self-heal — `sma_200` populates within ≤1 session; manual cache `rm` optional). _Registry + index reconciled to COMPLETE @ `0573152`._ (The `OHLCV_STALE_HOURS` TTL referenced here was retired by PRD-193, which replaced it with a trading-day freshness model — the self-heal is preserved, re-fetching every new weekday.)
- **PRD-199 — COMPLETE (2026-06-19):** MACRO TAPE tradables (SPY/QQQ/GLD/SLV/GDX/XLE) now show a monochrome daily %-change ↑/↓ arrow — additive `daily_change_pct` in `trend_structure._build_record` → `_pct_arrow`, freshness-gated on `_ts_health == "OK"` (dash when the trend snapshot isn't usable; price stays fresh from market_map); dead `_direction_arrow` tradables branch retired. Merged via PR #37 (`fd27d79`). HIGH-RISK gate satisfied: Claude review ACCEPT + durable Codex (`gpt-5-codex`, read-only, via the PRD-197 CI workflow) APPROVE.
- **Process/tooling -- COMPLETE (2026-06-20):** registry/index/state consistency is now a blocking CI check -- PRD-200 wired `tools/validate_prd_registry.py --skip-commit-resolvability` into the required `test` job (19 historical unresolvable hashes deferred at the time — later grown to 29/35 and closed WONTFIX-HISTORICAL by PRD-243; see Known technical debt). PRD-201 added a non-blocking `PreToolUse(Read)` hook (`.claude/hooks/canonical_read_guard.sh`) that reminds against re-reading the injected canonical docs (CLAUDE.md, MEMORY.md). PRD-202 added recon-efficiency Workflow-pattern guidance to CLAUDE.md (consult SCHEMA_MAP/CALL_SITE_MAP before location-greps; delegate bookkeeping recon).
- **PRD-191 — COMPLETE (2026-06-24):** direction-aware macro-evidence rationale. `MACRO_BIAS_INTERPRETATION` reshaped from a flat `payload_key->string` map to direction-keyed `{rising, falling}` forms that bake in each driver's cyclicality (contra-cyclical volatility/dollar/rates: rising favors caution; pro-cyclical bitcoin: rising favors risk); `dashboard_renderer` now selects the rationale by the rendered arrow so the macro-evidence prose always agrees with the risk-on/off vote (neutral string on the no-vote branch). +4 tests assert vote/prose agreement via a disjoint risk/caution substring contract. Merged via PR #56 (`6f38429`). HIGH-RISK gate: Claude review ACCEPT + Codex APPROVE (gpt-5.5, read-only, @ `7e8346d`).
- **PRD-192 — COMPLETE (2026-06-24):** notify-mode tag on the hourly notification audit + INTERFACE_LOCK reconciliation (folded from the PRD-189 intraday-slot deferral). Recon found `hourly_alert.yml` already covers the intraday window and PRD-141 already dedups on the canonical PT-hour slot, so the realizable deliverable was an optional `notify_mode` threaded through `output.py`/`runtime`/`alert_runner` onto the notification audit record (observability) plus the `INTERFACE_LOCK.md` reconciliation; the original "slot wiring + per-slot dedup marker" framing was cut. The `alert_runner` backstop send is retained untagged by design (the lazy-import `NOTIFY_HOURLY` could be unbound in the except path). +4 tests. Merged via PR #57 (`a26a70c`). HIGH-RISK gate: Claude review ACCEPT WITH CHANGES (both REQUIRED edits remediated) + Codex APPROVE (gpt-5.5, read-only, @ `a5d2917`).
- **PRD-193 — COMPLETE (2026-06-24):** OHLCV cache trading-day freshness + publish-safe prefetch persistence — the last of the three-PRD 190s backfill. Re-scoped at Stage 0 after a realizability check found the original "persist `data/cache`" plan inert (the 12h `OHLCV_STALE_HOURS` TTL rejected every daily cache at the pre-market slots, so the live run re-fetched regardless of persistence). Load-bearing fix: `_is_fresh_ohlcv_cache` rewritten to trading-day freshness (fresh iff the cache's last bar is the most recent completed session) + `time_utils.most_recent_completed_session_date`; `OHLCV_STALE_HOURS` retired. Then `actions/cache` persistence (12:50 prefetch saves on a real warm-proof, 13:00 live restores), publish-safe prefetch (no `PUBLISH_READY`), 12:50 cron re-enabled. Merged via PR #59 (`3ce4179`). HIGH-RISK gate: Claude review ACCEPT WITH CHANGES + Codex `gpt-5.5` APPROVE-WITH-CHANGES (read-only @ `2f77869`); all REQUIRED/P2 remediated, incl. Codex P2-1 (gate the cache save on a fresh-parquet proof so a halted prefetch cannot poison the day key, PRD-198 #2). **Live cross-run cache-hit confirmation pending** the next scheduled 12:50/13:00 UTC cycle (2026-06-24): the 13:00 live run should log "OHLCV from fresh cache" (PRD-198 #5 env-parity).
- **PRD-207 — COMPLETE (2026-06-26):** *(historical — the workflow described here was retired by PRD-230, 2026-07-04)* repaired the hollow Codex cross-review gate — `codex-review.yml` fail-closed on a served-vs-requested model mismatch (job-log capture, honor gate) instead of laundering a fallback substitution into a certified `resolved-model=gpt-5-codex` (PRD-198 #2/#3). Merged via PRs #68/#69 (`1968b50`, `55f9cd2`, `13c5d4a`). First bootstrap Codex-waiver of the arc; live run 28277644046 confirmed the repaired gate fail-closes on a substituted model.
- **PRD-210 — COMPLETE (2026-07-01):** premarket trend-structure path coverage — applies the PRD-174 history fallback on `_run_pipeline` so the F08 closes-None case renders real trend structure. Impl `55b2f67`; +2 tests. HIGH-RISK gate satisfied in-tree: Claude BUILD review + binding Codex cross-review committed. (Closed here — the 2026-06-26 "close in-order when 205-209 land" deferral was superseded once 205/206 were voided and 209 went HELD.)
- **PRD-211 — COMPLETE (2026-07-01, MICRO):** honest futures label for macro-tape metals + recon-map fill. Merged via PR #71 (`57dfd12`); +1 test.
- **PRD-212 — COMPLETE, PREMISE SUPERSEDED (2026-07-01):** *(historical — the workflow this configured was retired by PRD-230, 2026-07-04)* pinned `codex-version: 0.142.1` believing the gate outage was CLI-alias drift. **That diagnosis was wrong:** `gpt-5-codex` was deprecated by OpenAI 2026-04-01 — a retired model no CLI pin can serve. The Phase-4 live dispatches (2026-07-01, on main under 0.142.1) fail-closed on the model-metadata fallback every run, falsifying the premise; both waiver legs are void (no Claude-review artifact; the "Phase-4 stand-in" was recorded before any Phase-4 run existed). **The real fix is PR #76:** retarget the requested model to `gpt-5.5` + `ALLOWED_CODEX_MODELS = "gpt-5.5 gpt-5.5-*"`, validated end-to-end by run **28560459040** (resolved-model=gpt-5.5, exit 0, artifact landed at [`docs/prd_history/PRD-212.review.codex.md`](prd_history/PRD-212.review.codex.md)). The 0.142.1 pin is retained (it serves gpt-5.5), so the row stays COMPLETE, not reverted. **PRD-207 is NOT superseded** — its fail-closed honor gate correctly detected the real fallback. Auth is API-key (not ChatGPT sign-in). See DECISIONS 2026-07-01.
- **PRD-208 — COMPLETE (2026-07-02):** trend-structure SMA alignment presentation. The SMA composite cell renders a compressed 3-state arrow vocabulary (↑/↓/= vs SMA50 and SMA200) under the pinned "SMA 50/200" header; the redundant granular "vs SMA50"/"vs SMA200" columns are cut (trend table 10→8 columns); unavailable states keep "Structure unavailable"/"SMA history insufficient" and are guarded against ever rendering "NULL"/"None"/prose. Pure presentation change in `dashboard_renderer.py` (CLASS CONSUMER; no data/schema/gate/count/regime touched). Impl `0f72e32`; +2 net tests (sandbox 2862 passed / 1 xfailed; CI truth on the PR). HIGH-RISK gate SATISFIED in-tree: Claude review (`PRD-208.review.claude.md`) + genuine Codex cross-review (`PRD-208.review.codex.md`; resolved-model=gpt-5.5, honored/allowlist-verified, read-only, SHA-pinned @ `0f72e32`, run 28563373849) — APPROVE WITH EDITS, the one recommended edit (stale PRD-190 wording) applied. The invalid stage-0 Codex artifact (claimed gpt-5-codex, body self-reported gpt-4.1) is superseded. See DECISIONS 2026-07-02.
- **Proposed / next:** `prd_index.json` reads `next_prd: 244` (243 and 242 merged via PR #115; 240 merged via PR #111, 241 via PR #113 — all COMPLETE above, drafted from the qualification tuning audit; full ten-finding disposition: DECISIONS 2026-07-05. 226/227 merged via PR #95, closed same-PR per PRD-229; 229–232 merged via the Block-1 batch PR #99; 233–235 via PR #102, which carried the stack — the authoring PRs #100/#101 are closed as contained; 236 via PR #104; 237 via PR #105; 238 rides PR #106; 239 rides PR #108). **MICRO follow-up filed at PRD-238 review (RECOMMENDED, non-blocking):** `reports/levels.py::derive_key_levels` is a contract consumer still typed `dict` — annotate with `PipelineContract` in the next polish batch. Other open items, none in progress: **PRD-209** (OHLCV bar-count floor) — SHELVED, reopen-on-incident (F08 refuted; latent PRD-198 #1 hole documented, not built; see DECISIONS 2026-07-01). **PRD-188** (macro-awareness SHOCK banner + scheduled activation) — PROPOSED, parked; the 2026-07-15 go/no-go is advisory/soft and NOT wired (eval gate unstarted — corpus unlabeled, T unset; see DECISIONS 2026-07-01). **PRD-205/206** are VOID (numbers skipped, filed out of order); PR #51 (PRD-205 codex-review-router scaffold) was CLOSED as orphaned 2026-07-01 (router idea dropped; see DECISIONS 2026-07-01).
- **Test baseline:** 2884 passing, 1 xfailed on `main` through #110 (#95 added 5 mutation-verified tests; #110 was docs-only). PR #111 (PRD-240) adds 4 mutation-verified red tests — 2888 passed, 1 xfailed on the branch; CI on `main` is truth once merged.
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
| PRD-239 | Make architecture.md true: real _run_pipeline stage order, decision layer, typed-dict contract (master-plan G) | 2026-07-05 |
| PRD-226/227 | Level diagram NOW anchor = current price (contract entry is a separate ENTRY level) + PRD-221 provenance fix | 2026-07-05 |
| PRD-238 | J2: typed contract adopted at every consumer seam; SCHEMA_MAP field-lookup role retired; M-map renderer decomposition design | 2026-07-05 |
| PRD-237 | Typed contract boundary (J1): TypedDicts for contract / trade candidate / system_state, adopted in contract.py + payload.py | 2026-07-05 |
| PRD-236 | Extract the decision-gate chain + contract finalization from _run_pipeline into named functions | 2026-07-04 |
| PRD-235 | Qualification loudness: NEUTRAL symbols excluded visibly, missing-data gate passes emit skip markers | 2026-07-04 |
| PRD-234 | Kill the VALIDATED fail-open default: missing chain evidence renders MANUAL CHECK, never validated | 2026-07-04 |
| PRD-233 | Wire assert_valid_contract into _run_pipeline + system_state key guard | 2026-07-04 |
| PRD-232 | Guardrail tightening: skills learn PRD-229 rules, prd_open scaffold aligned to template, CLAUDE.md/CODEX.md dedup | 2026-07-04 |
| PRD-231 | Doc-truth micro-fixes: qualification gate count (9→11), output.py dead runtime.py reference | 2026-07-04 |
| PRD-230 | Process drop-list: Codex-authenticity teardown, cadence right-sizing, sediment stop, map de-line-numbering, process-doc dedup | 2026-07-04 |
| PRD-229 | Ceremony tiering: cosmetic MICRO carve-out + same-PR closeout | 2026-07-04 |
| PRD-228 | Bot-review-thread disposition clause (governance guardrail) | 2026-07-04 |
| PRD-225 | Trend-structure mobile rows: uniform wrap (alignment-cell min-width + tighter gap) | 2026-07-02 |
| PRD-224 | Macro-tape glyph alignment (GC/SI pad) + PRD-223 review fast-follows | 2026-07-02 |
| PRD-223 | Numeric entry→stop risk band on the level ladder (from contract trade_candidates) | 2026-07-02 |
| PRD-212 | Pin the Codex cross-review identity (CLI version 0.142.1) — end the alias-drift gate outage | 2026-07-01 |
| PRD-211 | Macro-tape metals display correctness | 2026-07-01 |
| PRD-210 | Premarket trend-structure path coverage — apply the PRD-174 history fallback on _run_pipeline (F08 closes-None fix) | 2026-07-01 |
| PRD-193 | OHLCV cache trading-day freshness + publish-safe prefetch persistence | 2026-06-24 |
| PRD-192 | Notify-mode tag on hourly notification audit + INTERFACE_LOCK reconciliation (folded from PRD-189 intraday-slot deferral) | 2026-06-24 |
| PRD-191 | Direction-aware macro-evidence rationale | 2026-06-24 |
| PRD-204 | Non-destructive scoreboard aggregate (preserve-prior + staleness marker) | 2026-06-23 |
| PRD-203 | prd_close.sh rebuilds the PROJECT_STATE baseline line (canonical, no stale provenance) | 2026-06-20 |
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
- **Phantom-SHA debt — CLOSED WONTFIX-HISTORICAL (PRD-243, 2026-07-05).**
  29 PRDs' recorded COMPLETE hashes (35 hash tokens; the "19" first counted at
  PRD-200 had grown through the PRD-208..222 era) are unreachable from a clean
  checkout — squash-merged/rebased away under the pre-#NNN provenance
  convention. Disposition: the class is dead, not the item open. The `#NNN`
  commit-cell convention (PRD-229) ended new instances; these rows closed
  under a convention that no longer exists, and rewriting their cells now
  would fabricate history against a rule that was not in force — the same
  logic as the PRD-242 validator's >=242 floor. CI keeps
  `--skip-commit-resolvability` permanently for historical rows; full-mode
  resolvability failures on rows <= PRD-222 are expected and are NOT a work
  item. (Supersedes the prior "triage/fix the 19 hashes, re-enable
  resolvability by 2026-07-31" follow-up, whose date anchored to the retired
  alignment cadence.)

## Parked (reopen only under the stated condition)

Deliberately deferred during the 2026-06-10 dashboard-batch scoping:

- **present-MANUAL_CHECK render visibility** (filed at PRD-234 closeout, per
  its review) - setups PRESENT in chain_results but classified MANUAL_CHECK
  render nowhere in the TRADE report body (dropped, not upgraded) - and
  fixture mode classifies every setup MANUAL_CHECK, so fixture TRADE renders
  show "A+ TRADES (0)" with all setups invisible. PRD-234's new
  missing-evidence block makes the asymmetry more visible. Reopen when a
  report-surface PRD next touches render_report's TRADE branch.
- **near-miss-surface** - "the closest setup that failed qualification, and which
  gate killed it." High learning value, but needs qualification introspection and
  flirts with signal-engine creep. Earn it after the regime scoreboard proves the
  learning-layer concept.
- **red-folder-entry-gate** - fail-closed entry gating on red-folder event
  windows. Out of PRD-176 (render-only). Needs its own fail-closed design first.
- **section-registry-refactor** - replace the renderer's inline section sequence
  with a data-driven registry. HIGH-RISK renderer work; reopen only if a
  post-PRD-177 renderer PRD shows continued section churn.

## Alignment check

Phase-boundary diff-read per `CLAUDE.md` (PRD-230 retired the scheduled
4-6-week ceremony). Last check: 2026-07-05 (#5, PASS, no drift — the
Fable-window close boundary; PRDs 191–239 covered; see `docs/DECISIONS.md`).
Next check: the next phase boundary (likely the post-window Opus wave
closing D/E or K/L/M).
