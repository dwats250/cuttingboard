# Alignment check #6 — whole-repo architectural alignment audit

- **Date:** 2026-07-01
- **Audited state:** `main` @ `c38edf7` (post PR #74/#75 merges)
- **Charge:** audit-and-scope pass. Findings + PRD-ready remediation scopes only;
  nothing executed. Every remediation below waits on Dustin's decision.
- **Method:** six parallel recon sweeps (VISION drift, CLAUDE.md↔reality,
  registry/index/DECISIONS coherence, HIGH-RISK surfaces, runtime-split map,
  unreachable-hash trace); every decisive receipt re-verified by the main agent
  per the CLAUDE.md sub-agent sweep re-verification rule.
- **Out of scope by charge:** PRD-208 revive (parked; noted only where its
  status is load-bearing).

## Cadence three questions (CLAUDE.md § Alignment cadence)

1. **New prediction logic entered the codebase?** **NO.** Zero ML imports, zero
   `.fit(`/`.predict(`, zero backtest/replay frameworks, zero broker/order
   automation, zero agent orchestration inside `cuttingboard/` (sweep across
   `cuttingboard/`, `runtime/`, `scripts/`, `tools/`, `pinescripts/`,
   workflows). Closest borderline items are catalogued in F-10 and F-11 — both
   backward-looking/descriptive, neither a forecast.
2. **New sidecar without a documented consumer / observational purpose?**
   **NO.** The only merges since cadence #5 (`a9ec4b2`, 2026-06-30) are PRD-212
   (workflow infra: `daedf10`, `0e1c6e9`, merge `39811bf`) and bookkeeping PRs
   #73/#74/#75. No new sidecar.
3. **New module not serving one of VISION's four questions?** **NO.** No new
   product module since cadence #5.

**Post-merge drift audit window (PRD-186):** PRDs merged since the cadence-#5
DECISIONS entry = PRD-212 + bookkeeping. PRD-212 carries a review-artifact
process miss — see F-1. No substantive VISION drift in the window.

Because this session is commissioned read-only-except-artifact, the
`docs/DECISIONS.md` cadence entry for check #6 is **not** written here; it is
part of proposed scope R-F below (main edit, Dustin's seam).

---

## Findings, severity-ranked

Severity scale: HIGH (gate/contract integrity), MEDIUM (rulebook↔reality
divergence), LOW (stale claim / hygiene), INFO (recorded observation, no action
required).

### F-1 — MEDIUM-HIGH · PRD-212's claimed stand-in Claude review does not exist in-tree

- **Claim:** `docs/DECISIONS.md:106-113` waives the PRD-212 Codex leg under the
  bootstrap precedent, stating "(Claude review + the recorded Phase-4 live
  validation stand in)".
- **Reality:** `docs/prd_history/` contains only `PRD-212.md` — no
  `PRD-212.review.claude.md`, no `PRD-212.review.codex.md` (verified by
  directory listing).
- **Clause violated:** CLAUDE.md § Review and commit discipline ("Nothing lands
  without review… a Claude review artifact"); the drift-check rule (PRD-186)
  that every review artifact records a DRIFT CHECK.
- **Commit:** PRD-212 landed at `daedf10` / merge `39811bf` (2026-07-01),
  manual-merged by Dustin.
- **Aggravating context:** PRD-212 is a HIGH-RISK repair *of the review gate
  itself* and is the second consecutive bootstrap Codex-waiver; DECISIONS
  itself flags it "for the next alignment-cadence audit to confirm the pattern
  is not masking drift" — this audit is that check. **Substance verdict: the
  change itself is sound and drift-free** — the pin exists
  (`.github/workflows/codex-review.yml:111`, `codex-version: 0.142.1`), the
  rationale comment exists (`:104-110`), and the tripwire test exists
  (`tests/test_codex_review.py:331`, `test_prd212_codex_version_pinned_tripwire`).
  The failure is process (missing artifact + overstated DECISIONS wording), not
  substance. The waiver is not masking drift.
- **Classification under PRD-186 remediation scaling:** review-artifact process
  miss → remediate **in place**, no corrective PRD required.
- **Proposed scope (R-B):** author a retroactive
  `docs/prd_history/PRD-212.review.claude.md` (SHA-pinned to `daedf10`,
  including the DRIFT CHECK section, honestly labeled retroactive), or — if
  Dustin prefers not to backfill — a one-line DECISIONS correction stating the
  Claude leg was informal (chat-only) and the waiver rested on the Phase-4 live
  validation alone. Either lands as a bookkeeping PR.

### F-2 — MEDIUM · CLAUDE.md still describes the Codex gate as a local `codex exec` CLI; the gate is a GitHub Actions workflow

- **Stale text:** `CLAUDE.md:219-223` — "All Codex review invocations run
  sandboxed read-only: `codex exec -s read-only - < prompt` … The review
  artifact … is written by Claude Code from captured stdout … (Verified
  2026-06-10)". Also the literal CLI syntax embedded in gate property #4 at
  `CLAUDE.md:55-57` ("`codex exec -s read-only`; never `-s workspace-write`").
- **Reality:** the gate is `.github/workflows/codex-review.yml` (PRD-197, then
  PRD-207 honor-gate, then PRD-212 pin): `workflow_dispatch`-only; Codex runs
  via `openai/codex-action@e0fdf01… # v1.8` with `sandbox: read-only`
  (`codex-review.yml:96-100`); the artifact is assembled by the `resolve` job
  and committed by `github-actions[bot]` to a `codex-review/*` branch
  (`codex-review.yml:249-274`, `:327-333`) — not written by Claude Code from
  stdout. The "Verified 2026-06-10" stamp predates all three PRDs that changed
  the mechanism.
- **Clause violated:** VISION § Operating principles — "The system must match
  its documentation… never left to drift."
- **Not divergent (important):** the mechanism-independent properties block
  (`CLAUDE.md:45-65`) is still satisfied by the actual workflow on all five
  properties (in-tree artifact, SHA-pinned checkout `codex-review.yml:91` +
  header `:265`, honor-gate allowlist `:204-241`, `sandbox: read-only` `:100` +
  `contents: read` `:83-84`, fresh-context `:88`, `:116-118`). The properties
  design did exactly its job across the mechanism change; only the concrete
  "how it runs" prose rotted.
- **Proposed scope (R-A, governance → manual-merge-only):** MICRO doc PRD
  rewriting `CLAUDE.md:219-223` to describe the workflow-dispatch mechanism
  (and pointing at `codex-review.yml` as source of truth), and updating
  property #4's parenthetical so the read-only requirement is stated
  mechanism-neutrally (e.g. "`sandbox: read-only` in the CI gate; `codex exec
  -s read-only` if ever run locally"). Bundled with F-4/F-5 as one
  doc-truth-reconciliation PRD since all three are operating-doc staleness;
  split if Dustin prefers strict single-file scopes.

### F-3 — MEDIUM-LOW · codex-review.yml contradicts itself about the codex-version pin

- **Stale text:** `.github/workflows/codex-review.yml:28-30` header comment —
  "`codex-version` is intentionally left unpinned there so the action installs
  a current sandbox-capable Codex CLI."
- **Reality:** same file, `:104-111` — `codex-version: 0.142.1` with the
  PRD-212 rationale comment.
- **Receipt:** PRD-212's FILES section (`docs/prd_history/PRD-212.md:55`)
  instructed revising "the 'intentionally unpinned' comment"; the inline
  step comment was revised, the top-of-file header comment was missed.
  Commit `daedf10`.
- **Clause:** VISION "system must match its documentation";
  CLAUDE.md invariant #6 hygiene (the stale comment actively asserts the
  anti-pattern the PRD closed).
- **Proposed scope (R-C):** MICRO, comment-only edit to
  `codex-review.yml:28-30`. Note the file is under the `protect_files.sh`
  workflow-glob protection and the change re-triggers nothing (comment-only);
  still lands via PR per the landing flow.

### F-4 — LOW · CLAUDE.md names two hooks that don't exist and omits the two that do

- **Stale text:** `CLAUDE.md:31-32` — "the repo's Claude Code hooks (file
  protection, **test gate, session snapshot**)".
- **Reality:** `.claude/hooks/` contains exactly `protect_files.sh`,
  `canonical_read_guard.sh`, `prd_eval.sh`; `docs/CLAUDE_HOOKS.md:9-13` and
  `.claude/settings.json` wire those three. No test-gate or session-snapshot
  hook exists.
- **Proposed scope:** fold into R-A (same doc-truth PRD).

### F-5 — LOW · CLAUDE_HOOKS.md claims settings.json "denies `git push` outright"; it allows it

- **Stale text:** `docs/CLAUDE_HOOKS.md:64-65`.
- **Reality:** `.claude/settings.json:33` allows `Bash(git push:*)`; only the
  force variants are denied (`:41-43`). The allow is *correct* behavior — the
  PRD-184 landing flow requires Claude to push feature branches
  (`CLAUDE.md:70-80`) — so the doc line, which predates PRD-184, is the stale
  side.
- **Proposed scope:** fold into R-A.

### F-6 — LOW · PROJECT_STATE's Alignment-cadence section is one check behind

- **Stale text:** `docs/PROJECT_STATE.md:105-106` — "Last check ran 2026-06-20
  (#4, PASS…)".
- **Reality:** cadence #5 ran 2026-06-30 — commit `a9ec4b2` ("chore: alignment
  cadence #5 — PASS (no drift) (#72)"), which touched only `docs/DECISIONS.md`
  (verified via `git show --stat a9ec4b2`) and left the PROJECT_STATE section
  unrefreshed. ("Next check by 2026-07-31" at `:107` remains correct.)
- **Clause:** the PRD-186 drift definition — "leaves a PROJECT_STATE claim
  stale."
- **Proposed scope (R-F):** bookkeeping commit updating the section to
  reference check #5 and (once Dustin accepts this audit) check #6, alongside
  the check-#6 DECISIONS entry. Root-cause note: the cadence procedure has no
  step to refresh the PROJECT_STATE pointer — add one line to the cadence
  procedure in CLAUDE.md (governance file → manual merge) or accept as-is.

### F-7 — LOW · DECISIONS.md cites a recon artifact that is not in-tree

- **Stale refs:** `docs/DECISIONS.md:191` and `:198` cite
  `recon/board-state-20260626.md` "(commit `c25f9e5`)". No such file exists;
  `recon/` contains only `recon-2026-06-17`, `recon-2026-06-22`,
  `recon-2026-06-24` (verified by listing).
- **Clause:** CLAUDE.md workflow rule — "link the artifact path in the
  `docs/DECISIONS.md` entry so the audit trail survives"; a dangling path
  defeats the survival purpose. (The commit pin means the content is
  recoverable from history if `c25f9e5` still resolves; that mitigates but
  does not cure a dead in-tree path.)
- **Proposed scope (R-F):** bookkeeping — either restore the file at the cited
  path from `c25f9e5`, or annotate the two DECISIONS lines with the surviving
  location. No corrective PRD.

### F-8 — LOW-MEDIUM · The literally-named invariant-#1 incident (`engine_doctor` swallow) is still live in cuttingboard.yml

- **Code:** `.github/workflows/cuttingboard.yml:173-174` —
  `python3 tools/engine_doctor.py … > engine_doctor.json || true` (×2). The
  `|| true` swallows even a hard crash of the doctor.
- **Clause:** CLAUDE.md § Semantic-failure hardening invariant #1 names
  "`engine_doctor` WARN→exit 0" as the incident it generalizes
  (`CLAUDE.md:143-145`).
- **Mitigation (why not higher):** the outputs are diagnostic artifacts
  uploaded `if: always()` for human review and gate nothing downstream — a
  swallowed failure cannot mask a green. But the rulebook presents the
  incident as closed while the literal pattern persists undocumented.
- **Proposed scope (R-D):** MICRO with a decision fork for Dustin —
  (a) make the step fail-loud (drop `|| true`, accept that a doctor crash
  reddens the scheduled run), or (b) keep it and add an in-file comment
  declaring it a knowingly-retained diagnostic exception to invariant #1
  (mirrors the `codex --version` provenance-only treatment, which the gate file
  documents correctly at `codex-review.yml:130`). Recommend (b): the artifact
  is advisory, and a red scheduled pipeline for a diagnostics crash inverts the
  severity.

### F-9 — LOW-MEDIUM · The registry validator's `_commit_exists` fail-silently passes when git is unavailable

- **Code:** `tools/validate_prd_registry.py:266-268` — on
  `FileNotFoundError/OSError` the comment says "git binary unavailable — do
  not flag (treat as resolvable)" and returns `True`.
- **Clause:** invariant #1 ("a missing dependency … must exit non-zero — never
  substitute-and-continue") and invariant #4 (no red test covers this branch).
- **Blast radius today:** zero — CI passes `--skip-commit-resolvability`
  (`.github/workflows/ci.yml:19`) so the branch is unreachable on the merge
  path. It becomes load-bearing the day resolvability is re-enabled (Debt-6
  scope), which is exactly when a silently-absent git would fake a green.
- **Proposed scope:** fold into the Debt-6 remediation PRD (R-H step 3) — flip
  to fail-loud + one negative test — rather than a standalone PRD.

### F-10 — LOW · Doctrine tension: performance_engine computes win_rate/expectancy while the regime-history doctrine forbids exactly that vocabulary

- **Code:** `cuttingboard/performance_engine.py:121-134` computes and emits
  `win_rate`, `avg_r`, `expectancy` over realized evaluation outcomes;
  `cuttingboard/evaluation.py:1-8` scores same-day ALLOW_TRADE decisions
  against observed forward 1-minute bars from `logs/audit.jsonl`.
- **Contrast:** `cuttingboard/delivery/regime_history.py:9-10` — "Description,
  not prediction: … It computes no hit-rate, accuracy, or grade" — the standard
  VISION-adjacent docs hold up as the model sidecar posture.
- **Verdict:** **not a VISION violation.** Both are backward-looking
  descriptions of realized outcomes of the system's own real recommendations —
  no synthetic replay, no strategy optimization, no forecast. But the repo
  applies opposite standards to "may a sidecar grade realized outcomes?" with
  no recorded rationale, which is a "system must match its documentation" gap
  and will confuse a future PRD author.
- **Proposed scope (R-G):** a DECISIONS entry (no code change) recording the
  distinction Dustin wants: e.g. "post-trade accountability sidecars
  (evaluation/performance_engine) may compute realized-outcome statistics;
  regime-level sidecars may not grade the regime engine" — or, if he wants the
  stricter reading, a cuts-before-additions review of
  `performance_engine`'s expectancy block. Dustin's call; both directions
  scoped, neither executed.

### F-11 — INFO · Renderer forecast-vocabulary posture (recorded, no action proposed)

- The single most forecast-adjacent rendered string is the Sunday "Monday
  Watch" copy, `cuttingboard/delivery/dashboard_renderer.py:1369-1376`
  ("watch for rejection at resistance"). It is conditional watch-instruction
  framing, not a price forecast, and is red-tested against manufacturing a
  decision (`tests/test_sunday_report_expansion.py:242-260` asserts
  `monday_watch` never contains `ALLOW_TRADE`/`TRADE ACTIVE`).
- There is no mechanical forecast-vocabulary guard on rendered output
  (`tests/test_dashboard_renderer.py:39` guards temp-path leakage only). Given
  "cuts before additions," this audit does **not** propose building one;
  recorded so the next renderer PRD's reviewer knows the principle is
  discipline-enforced, not test-enforced.

### F-12 — INFO · First-party `actions/*` remain on movable @vN tags (acknowledged debt, no drift)

- `actions/checkout@v6`, `setup-python@v6`, `upload/download-artifact@v7`,
  `cache/{restore,save}@v4`, `upload-pages-artifact@v3`, `deploy-pages@v4`
  across all workflows (e.g. `ci.yml:15-16`, `hourly_alert.yml:50,55,206`,
  `pages.yml:31-38`). Only the third-party, secret-adjacent
  `openai/codex-action` is SHA-pinned (`codex-review.yml:96`).
- This matches CLAUDE.md invariant #6's own incident text verbatim — the
  rulebook already declares it open debt, so it is accurate-as-debt, not
  divergence. No red test asserts SHA-pinning. Left with the debt ledger;
  scope only if Dustin wants invariant #6 closed for first-party actions.

### F-13 — INFO · Two phrasing imprecisions in the hash-debt records (fold into Debt-6 PR)

- `docs/PROJECT_STATE.md:79-81` and `docs/prd_history/PRD-200.md` say the
  hashes were "squash-merged/rebased away" — the squash half is wrong for this
  repo (evidence below: pure rebase-on-push).
- "19 hashes" undercounts: it is **19 PRDs, 25 hash tokens** (PRD-158 alone
  carries 7).

---

## Debt 5 — runtime/ package split: map and build sequence (not executed)

**As-built state.** `cuttingboard/runtime/` contains exactly three files:
`__init__.py` (2,290 lines, 66 top-level functions — verified by count),
`_constants.py` (120 lines), `_types.py` (91 lines). PRD-173 (Stage A) did the
`git mv` + carved the two L0 leaves + added guards; **zero functions moved**.
Stages B–I from the PRD-170 cut-line roadmap (`docs/prd_history/PRD-170.md`,
COMPLETE @ `c4e9537`) are unscheduled. Debt re-eval date 2026-08-15
(`docs/PROJECT_STATE.md:74-78`) — not yet due.

**Dependency graph (summary).**
- Internal: trivially acyclic — `__init__` → `_constants`
  (`__init__.py:124-154`), `__init__` → `_types` (`:155-158`); both leaves
  import no runtime code.
- Inbound (who imports `cuttingboard.runtime`): 22 files — 3 production/tooling
  (`cuttingboard/__main__.py:1`, `cuttingboard/alert_runner.py:56`,
  `tools/engine_doctor.py:97`) and 19 test files. `scripts/` has zero.
- Outbound: `__init__.py:29-119` imports ~30 non-runtime `cuttingboard.*`
  modules; `_constants` imports only `cuttingboard.notifications`; `_types`
  imports 10 field-type modules.
- Circulars: none as-built. One latent cycle (`ids_and_time ↔ fixtures`) is
  pre-resolved by PRD-170's design (`PRD-170.md:86-91`: `_is_fixture_backed` →
  L0, `_deterministic_run_at` → fixtures).

**The ordering constraint is test patch-targets, not imports.** The bulk of
the ~50 test patch sites target orchestrators/collaborators that stay in
`__init__` (facade-preserved for free). Six symbols destined for relocation are
patched at their facade path and must migrate patch targets in the same PRD
that moves them: `_apply_intraday_short_permission`
(`tests/test_gap_down_permission_integration.py:230,391` — `wraps=` pattern,
fragile), `_resolve_effective_mode` (`tests/test_sunday_premarket.py:6`),
`_data_status` (`tests/test_fixture_mode.py:12`), `_run_engine_health_gate`
(`tests/test_engine_doctor_gate.py:16`), `_write_trend_structure_snapshot`
(`tests/test_runtime_trend_structure_refresh.py:29`), and the `WATCHLIST_PATH`
const-binding case (`tests/test_watchlist_sidecar.py:216`, PRD-170 R3(ii)'s
explicitly flagged at-risk case).

**Proposed build sequence — eight single-concern HIGH-RISK PRDs, each carrying
the PRD-170 R4 gate (pytest pass-count parity + layering guard + surface guard
+ byte-identical artifact diff under `tests/fixtures/2026-04-12.json`):**

| # | PRD | Moves | Depends on | Risk note |
|---|-----|-------|-----------|-----------|
| 1 | B (L0) | `_iso_z` → `_timeutil.py`; `_is_fixture_backed` → `_constants` | — | zero patch migration; safest first move |
| 2 | C (L1) | `ids_and_time.py` (10 resolver/id fns) | B | 1 patch migration |
| 3 | D (L1) | `intraday_permission.py` (4 fns) | — | `wraps=` patch ×2; elevated |
| 4 | E (L1) | `fixtures.py` (6 fns, keep `_deterministic_run_at` inside) | B | audit `_load_inputs` patch sites |
| 5 | F (L2) | `artifacts.py` (14 writers) | C | **riskiest step**: WATCHLIST_PATH const-binding + touches every byte-identity-gated artifact; a binding error fails as silent output drift, not an import error |
| 6 | G (L2) | `summary.py` (8 fns) | C | 1 patch migration |
| 7 | H (L2) | `failure_handling.py` (3 fns) | B | 1 patch migration |
| 8 | I (L3) | `hourly.py` (4 builders) | G | largest behavior cluster, well-isolated by then |

Orchestrators (`_run_pipeline`, `_execute_notify_run`, `execute_run`,
`cli_main`, `execute_prefetch`) and the re-export facade stay in `__init__`
(L4) permanently — external consumers never change their imports. Approve the
sequence as a whole or per-PRD; each row is independently shippable in the
listed order.

## Debt 6 — 19 unreachable registry hashes: cause, verdict, triage scope (not executed)

**The check and the skip.** `_validate_commit_resolvable`
(`tools/validate_prd_registry.py:272-296`, PRD-164 R6(a)) runs
`git cat-file -e <sha>^{commit}` per COMPLETE-row hash. CI opts out via
`--skip-commit-resolvability` (`.github/workflows/ci.yml:19`; gate at
`validate_prd_registry.py:340-344`, PRD-200). The flag is negative-tested
(`tests/test_prd_registry.py:385-425` — consistency checks still fail with the
flag on). Documented at `docs/PROJECT_STATE.md:79-87` with re-eval 2026-07-31.

**True count.** 25 unresolvable hash tokens across exactly the 19 PRDs
PROJECT_STATE names (076, 081, 083, 085, 086, 088, 090, 096, 100, 102, 125,
126, 133, 139, 158×7, 161, 167, 168, 169). Verified in a full (non-shallow)
clone during this audit — the sandbox clone is shallow and useless for this
question. All resolvable registry hashes are ancestors of `main`.

**Cause — pre-PRD-194 rebase-on-push races, not squash, not force-push, not
fabrication.** Evidence chain (all re-checkable by Dustin from a full clone /
the GitHub API):

1. GitHub has never stored these objects: `GET
   /repos/dwats250/cuttingboard/commits/{391f84c,3a4ee24,7b1d7ad,c7a3863}` all
   return 422 "No commit found for SHA". A squashed-then-deleted branch would
   leave unreachable-but-stored objects; 422 means the SHAs were never pushed —
   they are pre-rebase **local** SHAs.
2. Every affected PRD's surviving twin on `main` carries the rebase signature
   (committer date > author date), e.g. PRD-133 impl `6b22915` (authored 05-12
   12:52, committed 12:56) whose closeout `30ff583` recorded the pre-rebase
   `391f84c`; PRD-158's whole 05-27 stack re-stamped 05-28 12:52.
3. The era's mechanism: before PRD-184/194, scheduled workflows pushed
   directly to `main` (167 `github-actions[bot]` commits 2026-05-01→06-16), so
   every human push raced the bot and required `git pull --rebase` — the
   closeout recorded the local impl SHA, the rebase rewrote it.
4. The repo self-diagnosed this four times and fixed those instances on main:
   `eed2997` (PRD-134), `de5fdab` (PRD-127), `03fbcfb` (PRD-141), `cf66780`
   (PRD-160). The 19 are the uncorrected residue of the same mechanism.
5. Every affected PRD has matching impl + closeout commits on `main`
   (e.g. PRD-076 → `0b36ae4`, PRD-090 → `1e82b0f`, PRD-133 → `6b22915`), and
   the PRD docs' own STATUS lines carry the same pre-rebase hashes as the
   registry — internally consistent, recorded honestly at closeout time.

**Verdict: the CI-skip is BENIGN — bookkeeping decay, not a masked integrity
problem.** No review-of-a-nonexistent-commit pattern; the work verifiably
landed. Two caveats keep it from fully clean: (a) SHA-pinned verification
against those 25 hashes is permanently impossible from any clone — the mapping
to surviving commits rests on message/author-date correlation, not
cryptographic identity; (b) while the flag is on, a *newly* mis-recorded hash
(typo — the race itself cannot recur post-PRD-194) sails through CI, and the
one guard that would catch it is the one skipped. The re-eval deadline
(2026-07-31) is doing its job.

**Proposed triage scope (R-H) — one data-only reconciliation PRD, three
steps:**
1. Re-point the 25 tokens across the 19 PRDs to their identified on-main twins
   (registry + `prd_index.json` + each PRD doc's STATUS line together, keeping
   the R6(b) doc/registry-agreement check green). PRD-158's 7-token →
   stage-commit mapping is by position/message; annotate any token whose twin
   identification is correlation-only.
2. Drop `--skip-commit-resolvability` from `ci.yml:19` and add
   `fetch-depth: 0` to the `ci.yml` checkout (both already named as the
   follow-up in `PROJECT_STATE.md:83-87`).
3. Fold in F-9 (make `_commit_exists` fail-loud on missing git,
   `validate_prd_registry.py:266-268`, + one negative test) and F-13 (correct
   "squash-merged" → "rebase-on-push" and "19 hashes" → "19 PRDs / 25 tokens"
   in PROJECT_STATE + PRD-200 notes).
   *Alternative (rejected-by-default, available if Dustin prefers the
   historical record untouched):* keep old hashes and teach the validator a
   `superseded_by` mapping — preserves honest history at the cost of a schema
   + validator change. *Optional hardening:* `prd_close.sh` verifies
   `git merge-base --is-ancestor <recorded> origin/main` before writing a row.

---

## Clean list — axes audited, zero drift

1. **VISION non-goals (code):** zero ML (no sklearn/torch/xgboost, no
   `.fit(`/`.predict(`), zero backtesting framework, zero execution automation
   (explicit human-seam disclaimers at `cuttingboard/config.py:66`,
   `chain_validation.py:13`), zero multi-agent orchestration in the product,
   zero HFT surface. `pinescripts/` is empty post the 2026-05-22 cleanup.
2. **Codex-gate properties block (`CLAUDE.md:45-65`):** all five properties
   verified against the actual workflow (receipts under F-2). The
   mechanism-independent design survived two mechanism changes intact.
3. **Auto-merge model:** `ci.yml` `test` job is the real merge gate (PR +
   push-to-main triggers, `ci.yml:6-22`); `gh pr merge:*` allowed; no workflow
   pushes to `main` (`tests/test_ci_artifact_hygiene.py:598-603` red-tests
   this); no force-push anywhere; force-push denied in
   `.claude/settings.json:41-43`.
4. **Publish-branch discipline (PRD-194):** all three scheduled publishers
   target `publish` only, ref-guarded to `refs/heads/main` and
   checkout-pinned (`cuttingboard.yml:49,355`; `hourly_alert.yml:39,199`;
   `macro_awareness.yml:25,83`), test-anchored
   (`test_ci_artifact_hygiene.py:324-332`).
5. **Registry/index coherence:** contiguity 180–212 with no gaps or duplicate
   rows; every registry↔index status pair matches (incl. DEPRECATED 205/206,
   PROPOSED 188/208/209); `latest_complete: 212` and `next_prd: 213` correct
   (`docs/prd_index.json:3-4`); **the previously-caught PRD-209 stale STATUS
   line is resolved** — registry is now 242 lines, PRD-209 appears once at
   `PRD_REGISTRY.md:230` as PROPOSED, coherent with the by-design shelve note
   (`DECISIONS.md:53-54`).
6. **PROJECT_STATE substance:** Active-PRD pointer ("none in progress")
   correct; test baseline (2,860 passing / 1 xfailed @ `39811bf`, run
   28480130785) commit-consistent; no known-debt re-eval date past due;
   "Proposed / next" is current post-#74/#75 (F-6's cadence pointer is the
   sole stale line found in the file).
7. **Review artifacts ≥ PRD-200:** every extant review carries a DRIFT CHECK
   section; HIGH-RISK 200 and 210 carry both Claude + Codex artifacts; 207's
   Codex absence is a documented waiver (`DECISIONS.md:164-172`). Sole gap is
   PRD-212 (F-1).
8. **Renderer decision surfaces:** HALT/kill-switch precedence and PRD-168
   verdict gating are asserted on meaning, with genuine red tests
   (`tests/test_dashboard_renderer.py:880-900`,
   `test_dash_system_state.py:135-169`, `test_dash_candidates.py:329-364`),
   and match current renderer code (`dashboard_renderer.py:190-193`,
   `:1298-1305`, `:1920-1948`, `:2300-2315`). No test↔code contract drift
   found.
9. **No hidden disabled checks:** no `if: false` / `continue-on-error` /
   commented-out jobs in any workflow; the only skips are the documented
   resolvability flag (Debt 6) and legitimate publish-freshness guards.
10. **Hooks:** the three wired hooks match `docs/CLAUDE_HOOKS.md` and
    `.claude/settings.json` exactly (except the F-5 line); `protect_files.sh`
    patterns match their documentation.
11. **Codex honor gate (PRD-207):** fail-closed, reads the authoritative
    `--json` JSONL `item.error` (not prose), allowlist-gated
    (`codex-review.yml:171-241`) — invariants #1/#2/#3 satisfied where the
    decision is made; red-tested including reworded-fallback
    (`tests/test_codex_review.py:304`).
12. **PRD-208:** parked, registry/index PROPOSED, no PRD file (registry File
    col "—") — status noted per charge; not audited further.

## Remediation scope index (for accept/modify/reject)

| ID | Findings | Shape | Lane | Merge seam |
|----|----------|-------|------|-----------|
| R-A | F-2, F-4, F-5 | Doc-truth reconciliation of CLAUDE.md + CLAUDE_HOOKS.md | MICRO | **manual-merge (governance file)** |
| R-B | F-1 | Retroactive PRD-212.review.claude.md (SHA-pinned `daedf10`, DRIFT CHECK) or DECISIONS wording fix | in-place (PRD-186 scaling) | auto-merge PR |
| R-C | F-3 | codex-review.yml:28-30 comment fix | MICRO | auto-merge PR |
| R-D | F-8 | engine_doctor step: fail-loud OR declared-retained comment (recommend the latter) | MICRO | auto-merge PR |
| R-F | F-6, F-7 | Bookkeeping: cadence pointer refresh + DECISIONS dangling-ref fix + check-#6 DECISIONS entry | bookkeeping commit | auto-merge PR |
| R-G | F-10 | DECISIONS doctrine note: realized-outcome statistics — where allowed and why | decision note | auto-merge PR |
| R-H | Debt 6 + F-9 + F-13 | Hash re-point + CI flag drop + fetch-depth 0 + fail-loud `_commit_exists` | STANDARD PRD (data + 1 guard) | auto-merge PR |
| R-I…R-P | Debt 5 | Runtime split PRDs B→I per the sequence table | 8 × HIGH-RISK | auto-merge PR + full R4 gate each |

Nothing above is executed. This artifact is the deliverable of a read-only
charge; per the recon-artifact clause it is committed to a non-`main` branch
only, and the branch→`main` merge stays human-held.
