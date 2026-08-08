# CUTTINGBOARD — ENGINEERING HEALTH PACKET (2026-08-08)

Recon/planning only. No implementation, no PRD, no Gate A, no feature
execution. Evidence: this session's established findings + 3 narrow
lightweight readers (TODO/dead sweep; test/CI facts) + direct
spot-checks. Owner surgical corrections of 2026-08-08 applied.

## 1. EXECUTIVE HEALTH VERDICT

**HEALTHY WITH BOUNDED DEBT.** The repo's truth machinery works: no
importorskip/WARN-exit-0 anywhere in tests, no orphaned scripts, recon
maps (SCHEMA_MAP/CALL_SITE_MAP) updated through PRD-289, conftest is
lightweight, and every debt item found is either already named or small.
The dominant cost is not debt but *friction*: manual mutation-evidence
ceremony, LOC estimation misses, cold dependency installs on every
scheduled run, and harness/orchestration fragility observed repeatedly
this session. Nothing blocks the Cloudflare / Morning Brief path.

## 2. TECHNICAL DEBT REGISTER

| ID | Finding | Evidence | Why it matters / risk | Fix scope | Disposition |
|---|---|---|---|---|---|
| TD-1 | GEX docs-drift cluster: PROJECT_STATE + workplan say "stopped without a verdict"; NS ledger says "never attempted"; system_logic_map:21 claims Polygon fallback (CB-27) — all contradict the packet's §1 `EVIDENCE INCOMPLETE` verdict | GEX packet §2 (this session) | These four documents currently misstate standing GEX authority; a future agent could re-litigate a settled verdict | 4 small docs edits | **FIX NOW** — docs-only truth batch before the next GEX commission; may land independently rather than waiting for GEX closeout |
| TD-2 | Alignment check is DUE (phase boundary passed at PRD-289 close) and its "next check" pointer is stale (July "Opus wave / K/L/M" phrasing) | PROJECT_STATE end; memo §4 | PRD-230's own trigger has fired; drift audit sweeps wider than any PR | owner-run bounded Alignment check + pointer edit | **FIX NOW** (owner act; pointer edit rides it) |
| TD-3 | `resolve_run_mode.py:27,50-52` still says intraday-cron re-homing "deferred to PRD-192" — PRD-192 is COMPLETE and explicitly ratified NOT re-homing those slots | reader:stale-dead | Comment contradicts settled authority; next reader plans phantom work | comment-only edit | **FIX NOW** (cosmetic carve-out / weekly polish batch) |
| TD-4 | SMCI in `EXPANSION_LEADERSHIP_SYMBOLS` is never fetched (absent from ALL_SYMBOLS/PRICE_BOUNDS/UNITS) → `regime.py:119-123`'s `s in valid_quotes` is permanently false — leadership gate silently runs 4-of-5 | verified this session (regime.py:119-123) | Silent degradation of declared config intent (PRD-198 #1 adjacent); conservative direction, so not unsafe | one-line universe add OR one-line list removal + test | **OWNER RULING REQUIRED** (which intent is true), then trivial fix |
| TD-5 | `_OPTIONAL_MACRO_DRIVERS` duplicated in contract.py:64 and payload.py:318-336 with keep-aligned comment | registry recon | Unenforced invariant; drift = silent divergence | single-source the vocabulary in the narrowest already-valid shared authority location + equality/behavior test (~15 LOC); do not introduce a new payload→contract dependency solely for deduplication | **FIX SOON** (quick win) |
| TD-6 | Zero-production-consumer config lists (INDICES/COMMODITIES/HIGH_BETA as names, REQUIRED_SYMBOLS) pinned only by negative-assertion tests | registry recon | Vocabulary noise; misleads recon | deletion rides registry R3 | **DEFER** (sequenced behind registry R2/R3) |
| TD-7 | Twin 6-tuples (TREND_STRUCTURE_SYMBOLS / PRIMARY_SYMBOLS) independently declared | registry recon | The flagship duplication — already the registry lane's job | registry R2 | **DEFER** (planned) |
| TD-8 | Second prior_close mechanism (reports/levels.py) + prose gap fields / None overnight placeholders (reports/premarket.py) | MB packet §2 | Third-mechanism risk for the Morning Brief | unification flagged in MB packet | **DEFER** (handled at MB MATERIAL-packet stage) |
| TD-9 | No pip caching in ANY workflow (5× setup-python, zero `cache:`); every scheduled run cold-installs | reader:test-ci | Avoidable dependency-download/install latency on every run; particularly relevant once scheduled cadence increases | add `cache: 'pip'` to 5 invocations | **FIX NOW** (quick win; sequence BEFORE/WITH CF — shared file) |
| TD-10 | GitHub Actions pinned to floating tags (@v6 etc.), contra invariant #6 "action → commit SHA" | reader:test-ci | Movable identity; the repo's own hardening rule names it | SHA-pin ~8 action refs | **OWNER RULING REQUIRED** (accept float vs pin) |
| TD-11 | ci.yml permanently runs `--skip-commit-resolvability` | reader:test-ci flagged | Ruled WONTFIX-HISTORICAL (PRD-243, phantom-SHA closure) | none | **NOT DEBT** |
| TD-12 | runtime/ split mid-way; re-evaluation date **2026-08-15 (one week)** | PROJECT_STATE known debt | VISION requires dated re-exam; date arrives during CF arc | owner re-rules or re-dates | **OWNER RULING REQUIRED** (calendar, not code) |
| TD-13 | dashboard_renderer.py ~2,880 lines; PRD-238 decomposition designed, never executed; CF adds block #3 | surfaces recon | Growing but functioning; no consumer pressure yet | own PRD if ever | **DEFER** (revisit after CF lands) |
| TD-14 | PROJECT_STATE.md is a snapshot behaving as history: 391 lines, 33 accumulated COMPLETE-PRD narratives | direct check | Every session pays reading cost; "current state" buried | archival convention (narratives → prd_history pointers) | **OWNER RULING REQUIRED** (format convention), then mechanical |
| TD-15 | PRD-283-F1 `qualified_count` semantic contradiction (postmarket vs renderer resolve it oppositely) | state recon | Known MEDIUM ambiguity awaiting ruling | ruling + lane-appropriate PRD | **OWNER RULING REQUIRED** (already queued) |
| TD-16 | macro_awareness.yml is the one workflow force-pushing artifacts to main (PRD-194 tension, documented) | surfaces recon | Standing exception to a stated rule | one ruling (bless or migrate to publish) | **OWNER RULING REQUIRED** |
| TD-17 | CLAUDE.md "~394 entries" settings.local text may predate the PRD-258 prune ruling | DECISIONS 2026-07-14 | Possibly stale owner-authored text; low stakes | owner verifies local file | **OWNER RULING REQUIRED** (verify only) |
| TD-18 | 2026-06-10 parked dashboard items predate two dashboard generations | memo §4 | Stale backlog weight | explicit cut ruling | **OWNER RULING REQUIRED** (cut candidates) |

## 3. FRICTION HEAT MAP (ranked by compounding impact)

| # | Source | Frequency | Cost/occurrence | Compounding | Remedy | Local/systemic |
|---|---|---|---|---|---|---|
| F-1 | LOC estimation misses on validation surfaces | 2 of last 2 MATERIAL PRDs | full GOV-2 §5 stop-and-renew + amended review cycle | every future MATERIAL slice | estimation rule: count vocabularies/validation/typed-unavailable as first-class (already in packets; graduate to PRD_PROCESS) | systemic-process, tiny change |
| F-2 | Manual mutation evidence (16 hand-applied/reverted mutations, hand-built table) | every HIGH-RISK PRD | hours + error-prone byte-identical restores | every future HIGH-RISK slice (CF, GEX-1…) | small `tools/` mutation-runner (apply→pytest→revert→emit table); earned by 3rd use | local utility |
| F-3 | Harness/orchestration fragility: one total-loss workflow run (~500k tokens, permission-handler fault), 3 recurring StructuredOutput cap failures, multi-line `git commit -m` denials | repeatedly this session | minutes-to-major token loss | every orchestrated session | conventions now proven: probe-before-fan-out, light models for recon, transcript salvage, `commit -F`; graduate the proven conventions into the existing canonical agent-workflow guidance, if owner-approved | systemic-harness; mitigate by convention |
| F-4 | Cold dependency install + full pytest before every scheduled pipeline run | 3×/weekday now; 5-6× under CF cadence | avoidable install latency + full-suite runtime per run | every scheduled run forever | TD-9 pip cache now; full-suite-per-run is deliberate (verify-where-truth-is-determined) — only the owner can trade it | local (cache) + owner (suite policy) |
| F-5 | Remote-session env not bootstrapped (pytest unrunnable; 85 misleading collection errors) | every fresh web session | confusion + setup time | every future session | idempotent bootstrap/check hook or documented one-command bootstrap; never blindly reinstall on every session | local |
| F-6 | PROJECT_STATE reading cost (TD-14) | every session start | minutes | grows monotonically | archival convention | local-docs |

## 4. PROJECT POLISH REGISTER

| Improvement | Payoff | Scope | Urgency |
|---|---|---|---|
| audits/ sweep: classify 25 top-level folders as durable evidence vs PRD-230 session-scratch; delete confirmed scratch | recon signal-to-noise | owner confirms list; mechanical deletion | low |
| Reconciliation-folder lifecycle: delete temp planning artifacts once the ChatGPT synthesis absorbs them (as their headers already promise) | keeps temporary synthesis temporary | deletion after handoff | low (after handoff) |
| MB packet nit: drop "artifact_flow_map registration" from its docs row (sections aren't registered — file-level convention only) | prevents invented ceremony at packet stage | 1-line packet edit | with MB packet draft |
| Spell out "Operating Rule lane N" vs "memo rank N" everywhere (normalization rule) | avoids ordinal confusion | convention | ongoing |

## 5. HIGH-LEVERAGE COMBINED MOVES (debt + friction, ranked)

1. **Estimation-rule graduation (F-1):** one PRD_PROCESS line ends the
   repo's most expensive recurring ceremony trigger. Biggest
   leverage-to-cost ratio in this audit.
2. **Mutation-runner utility (F-2):** pays ceremony friction on every
   future HIGH-RISK slice and makes mutation evidence reproducible
   instead of hand-attested.
3. **Pip cache + suite-policy ruling (TD-9/F-4):** removes avoidable
   install latency from the schedule the Morning Brief exists to serve.
4. **PROJECT_STATE archival convention (TD-14/F-6):** one-time convention
   change, permanent per-session reading-cost reduction.

## 6. QUICK-WIN STRIKE LIST (Codex-safe, isolated, no feature-lane coupling)

| ID | Objective | Files | Size | Tests | Independence |
|---|---|---|---|---|---|
| QW-1 | Truth-fix resolve_run_mode's stale PRD-192 comments | scripts/resolve_run_mode.py | comment-only | none (cosmetic carve-out) | total |
| QW-2 | Single-source `_OPTIONAL_MACRO_DRIVERS` without changing dependency direction; pin equality/behavior with a test | narrowest already-valid shared location (implementation-time import-graph inspection decides) | ~15 LOC | 1 test, mutation-verified | total |
| QW-3 | Add `cache: 'pip'` to the 5 setup-python steps | 5 workflow files | ~5 lines | green runs as proof | **shared file with CF** (cuttingboard.yml) — land BEFORE or fold INTO the CF workflow edit |
| QW-4 | GEX docs-drift batch fix (TD-1's four items) | PROJECT_STATE, workplan, NS ledger, system_logic_map | docs-only | registry validator green | total (lands independently, before the next GEX commission) |
| QW-5 | Add an idempotent remote-session bootstrap/check: detect whether the project dev environment is usable; install `.[dev]` only when missing, otherwise no-op. Prefer an explicit bootstrap script + thin SessionStart hook over unconditional installation | .claude/ hook config + small script | small | manual verify | total |

## 7. DEBT THAT SHOULD STAY DEBT

- **Macro track** — dormant by explicit ruling; untouchable.
- **runtime/ refactor** — acknowledged debt with a date; refactors need
  their own PRD; only the re-evaluation ruling is due, not the work.
- **Renderer decomposition (PRD-238)** — designed, unexecuted, no
  consumer pressure; do not start opportunistically.
- **Additive-section wiring pattern** — the Morning Brief is copy #3;
  abstraction is earned only if GEX-2 becomes copy #4. Not before.
- **Watchlist sidecar zero-consumer state** — ruled valid (human reader
  is the consumer); absorption is registry R2's job.
- **Zero-consumer config lists** — deletion sequenced behind registry
  R2/R3; deleting now would race the lane that owns them.
- **ci.yml `--skip-commit-resolvability`** — ruled WONTFIX-HISTORICAL.
- **Full-pytest-before-scheduled-runs** — a deliberate
  verify-where-truth-is-determined posture; only an owner trade-off, not
  cleanup.
- **conftest autouse fixtures** — justified isolation, lightweight.

## 8. GOVERNANCE / PROCESS IMPROVEMENTS (candidates for later canonical adoption — not adopted here)

Worth graduating after owner review: plan adjacent lanes together, then
normalize packets before execution; readiness ≠ priority (owner order
prevails); count validation surfaces as first-class LOC at packet stage;
probe environment health before any agent fan-out; lightweight models for
mechanical recon, expensive reasoning only for classification/design;
salvage failed structured-output agents from transcripts before re-running;
named-debt graduation (adjacent findings leave the lane, never fixed
silently in it); single-owner file seams declared per arc
(payload/renderer); shared infrastructure only after a third real
instance; stop planning when the handoff is mature.

## 9. RECOMMENDED CLEANUP CAMPAIGN

- **Wave A — land bounded cleanup by seam, not as one omnibus batch:**
  - Truth/docs batch: QW-1 + QW-4 + Alignment-check bookkeeping where
    appropriate
  - Workflow/dev-environment batch: QW-3 + QW-5, only if their
    workflow/config surfaces remain naturally cohesive
  - Production dedup: QW-2 as its own tiny tested code change

  Parallel execution is fine; merge each independently when clean. Plus
  the due Alignment check (owner). The QW-3 sequencing rule applies
  (before/with CF's workflow edit).
- **Wave B — high-leverage friction reducers (alongside the CF
  evidence/MATERIAL path and, once separately authorized, CF
  implementation):** mutation-runner utility (small tools/ PRD with
  tests); PROJECT_STATE archival convention (after owner rules format);
  estimation-rule + process-lesson graduation (docs/governance PR, draft,
  owner-held).
- **Wave C — larger items only if still justified:** runtime/ split
  continuation (only per the 2026-08-15 re-ruling); renderer
  decomposition (only if post-CF pressure appears). Registry R2/R3
  consolidations stay feature-lane work, not cleanup.

Parallel-safety: Waves A/B touch docs, tools/, tests, and workflow cache
lines — disjoint from Morning Brief production surfaces except QW-3
(sequenced), fully disjoint from Registry and GEX. **Cleanup does not
take the implementation seat; Cloudflare-first stands** — no
correctness/safety blocker was found (TD-4 is conservative-direction and
one line once ruled).

## 10. CODEX EXECUTION CANDIDATES

| Item | Classification |
|---|---|
| QW-1, QW-4 (docs/comment truth fixes) | lightweight Codex cleanup |
| QW-2, QW-3, QW-5 | lightweight Codex cleanup |
| Mutation-runner utility | standard Codex implementation (small spec first; Fable-lite review of the spec) |
| PROJECT_STATE archival execution | lightweight Codex cleanup after owner rules the convention |
| TD-4 SMCI fix | lightweight Codex cleanup after owner ruling |
| Action SHA-pinning (if ruled) | standard Codex implementation |
| CF / Registry / conditional GEX-1 feature lanes | Opus-led once each lane independently reaches implementation authority; current packet readiness still governs |
| Estimation-rule / process graduation | Fable review first (governance-adjacent wording) |

## 11. FINAL PRIORITIZED BACKLOG

- **P0:** none. No correctness/safety blocker exists.
- **P1:** F-1 estimation-rule graduation; F-2 mutation-runner; TD-9/QW-3
  pip cache (sequenced with CF); TD-4 SMCI ruling+fix; TD-2 Alignment
  check (due); TD-1/QW-4 GEX docs-drift batch (FIX NOW, still P1).
- **P2:** TD-14 PROJECT_STATE archival; TD-5/QW-2 macro-drivers dedup;
  TD-3/QW-1 comment truth; TD-10 action-pinning ruling; QW-5 session
  bootstrap; TD-12 runtime re-ruling (calendar-due).
- **P3:** audits/ sweep; reconciliation-folder lifecycle; MB packet nit;
  terminology conventions; TD-17 settings text verify; TD-18 parked-item
  cuts.

## 12. FINAL RECOMMENDATION

**YES — the repo is healthy enough to proceed immediately with the
Cloudflare / Morning Brief authority-and-evidence path. No
engineering-health finding requires priority over it. Implementation
begins only after the existing CF evidence, owner-ruling, MATERIAL/PRD,
and Gate-A sequence grants that authority.**

Nothing must be cleaned first except by preference: the one
sequencing-relevant item is QW-3 (pip cache), which shares
`cuttingboard.yml` with the CF arc and should land before or inside CF's
workflow edit rather than after. Burn down in parallel: Wave A seam
batches + the due Alignment check immediately; Wave B (mutation-runner,
PROJECT_STATE convention, process graduations) alongside the CF
evidence/MATERIAL path and, once separately authorized, CF
implementation, plus Registry packet drafting; the GEX ruling bundle any
time. Cloudflare-first stands unchallenged.
