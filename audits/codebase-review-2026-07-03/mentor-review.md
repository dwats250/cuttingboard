# Cuttingboard — Full Codebase & Mentorship Review

Date: 2026-07-03
Reviewed at: main @ 94abe87 ("PRD-225 closeout bookkeeping")
Scope: entire repository — source (`cuttingboard/`, ~19.4k lines / 63 modules), tests
(`tests/`, ~36.3k lines / 102 files / ~2,350 test functions), docs (~60k lines),
CI workflows, hooks, scripts, and the development process itself.
Method: five parallel deep-dive reviews (architecture/data-flow, core-module code
quality, test suite, security/performance/ops, workflow/process), plus direct
reads of the runtime spine.

---

## Executive Summary

The blunt read: **you have built a genuinely good system wrapped in a process
that has started eating the project.**

The product half is far better than "beginner" code. The upstream pipeline
(ingestion → normalization → validation → regime → qualification) is typed with
frozen dataclasses, pure functions, and disciplined `replace()`-based updates.
The test suite is real — ~2,350 tests, ~24% of them targeting error/edge paths,
zero `importorskip`, zero empty tests, one exemplary `strict=True` xfail. The
security posture (env-only secrets, escaped HTML, timeouts on every network
call, fail-loud HALT semantics, freshness-gated publishing) is better than most
professional teams ship. Performance is correctly a non-concern and correctly
not optimized.

Three structural problems hold it back:

1. **The downstream half abandons the discipline of the upstream half.** From
   `contract.py` onward, everything is an untyped `dict[str, Any]` that
   `runtime` mutates in place across module boundaries — and the one strong
   validator you wrote (`assert_valid_contract`) is never called in production.
2. **Two god modules concentrate all risk.** `runtime/__init__.py` (2,291
   lines, imports 44 internal modules, with a 451-line `_run_pipeline`) and
   `delivery/dashboard_renderer.py` (2,880 lines, with an 841-line render
   function taking 22 keyword parameters).
3. **The process is now ~3× the size of the product and growing faster than
   it.** 227 PRDs + 70 review artifacts + 41 decision entries — 52k lines of
   PRD history against 19k lines of code. Recent history shows 115-line PRD
   specifications for CSS padding tweaks, a 344-line CI workflow whose sole
   purpose is authenticating the AI reviewer, and a multi-PRD arc (205, 206,
   207, 210, 212 — two voided, one premise-falsified) spent governing the
   governance.

On your progress: the discipline, documentation instinct, and review-gate
thinking on display here are years ahead of a typical beginner. The risk is not
that you're learning too slowly — it's that you're optimizing the meta-game
(specs, gates, audits) faster than the object-level game (reading code, judging
designs, knowing which ten lines matter). The next stage of your growth is
mostly about rebalancing that.

---

## Metrics

| Area | Score | One-line verdict |
|---|---|---|
| Architecture | 7/10 | Excellent typed upstream; untyped mutated-dict downstream + two god modules |
| Code clarity | 7/10 | Clean small modules; worst functions are 200–840 lines |
| Maintainability | 6/10 | Duplication (triplicated validation, duplicated constants), stale core docs |
| Testing | 8/10 | Strong, doctrine-compliant suite; ingestion error paths and `confirmation.py` untested |
| Error handling | 7/10 | Fail-loud is real at the ops layer; several fail-open safety gates and silent swallows inside |
| Performance | 9/10 | A non-issue at this scale, and correctly treated as one |
| Security | 8/10 | Strong posture; deps unpinned/no lockfile violates your own doctrine |
| Developer workflow | 4/10 | Process output exceeds product output ~3:1; ceremony tax on trivial changes |
| Documentation | 6/10 | Extraordinary volume; `architecture.md` materially wrong about the decision layer |
| Beginner growth trajectory | 8/10 | Exceptional discipline and self-correction; under-invested in code-reading fluency |

### Area detail

**1. Code quality — 7/10.**
Working: frozen dataclasses everywhere upstream (`RegimeState`,
`QualificationResult`, `ChainValidationResult`, `TradeDecision`), good constant
vocabularies (`GATE_*`, `VALIDATED`), no TODO/FIXME litter, `chain_validation.py`
is the best-organized large module in the repo.
Not working: function size at the hot spots —
`dashboard_renderer.render_dashboard_html` (841 lines, 22 kwargs),
`runtime._run_pipeline` (451 lines), `qualification.qualify_candidate` (222
lines of seven near-identical gate stanzas), `output.render_report` (225 lines).
Stringly-typed comparisons bypass the constants that exist:
`watch.py:466` and `output.py:433` compare `posture == "STAY_FLAT"` as a raw
literal; `qualification.py` compares `direction == "LONG"/"SHORT"` throughout
with no constant defined at all; `evaluation.py:128` compares
`"ALLOW_TRADE"` as a literal while the imported constant exists elsewhere.
Fix: decompose the four giants into section/gate helpers; define
`LONG`/`SHORT` constants and use the existing status constants everywhere.

**2. Architecture and structure — 7/10.**
Working: layered upstream pipeline, genuinely honored sidecar doctrine (the
observe-only sidecars really are pure — verified), delivery layer correctly
consumes only the contract plus pure helpers.
Not working: `runtime/__init__.py` is a god orchestrator (fan-out 44 — next
highest module is 11) owning all wiring, all artifact I/O, and all contract
mutation. The documented "L8 Flow Gate" actually runs *inside* `qualify_all`
(`qualification.py:249`), creating a flow↔qualification coupling cycle.
`notifications/__init__.py:13` imports layout constants from
`delivery/macro_tape_layout` — two sibling presentation packages co-own a
schema. Production fixture mode monkey-patches live modules with
`unittest.mock.patch` (`runtime/__init__.py:1538`) instead of injecting a
data source — test machinery living inside the product.
Fix: see Refactor Plan.

**3. Maintainability — 6/10.**
Working: small modules are small; test-to-code ratio ~1.9:1; scope discipline
keeps diffs contained.
Not working: macro-driver validation is triplicated
(`contract._build_macro_drivers`, `contract.assert_valid_contract:598`,
`payload._require_macro_drivers:253` — with `_OPTIONAL_MACRO_DRIVERS` literally
defined twice); `EXTENSION_ATR_MULTIPLIER = 1.5` defined in both
`market_map.py:112` and `config.py:110`; `_iso` timestamp formatting duplicated
byte-identically in `contract.py:434` and `market_map.py:606`; four float-coerce
helpers reimplemented across modules; `_PartialPipelineResult` mirrors ~20
fields of `PipelineResult` by hand.
Fix: single source of truth for each duplicated constant/schema; one shared
`_coerce_float` util; kill the Partial mirror or generate it.

**4. Testing — 8/10.**
Working: the PRD-198 doctrine is *enforced, not decorative* — zero
`importorskip`, zero `assert True`, zero empty bodies, meta-tests policing the
doctrine itself; builders return real dataclasses so schema drift fails loudly;
the shared corpus between `tests/preview_fixtures.py` and
`scripts/preview_fixtures.py` makes fixture/preview drift structurally
impossible; ordering assertions on stable DOM ids instead of raw HTML matching.
Not working: `confirmation.py` (146 lines of directional level-cross logic) has
**zero** tests; `ingestion.py`'s yfinance retry/timeout/empty-frame paths are
monkey-patched away in every test that touches them — the highest-value
untested error surface in the repo; exact-copy label assertions
(`"A+ — ACTIONABLE"` etc., `test_dash_candidates.py:94-97`) break on any copy
edit; `test_dashboard_renderer.py` is a 3,841-line outlier.
Fix: write `test_confirmation.py`; test `_try_yfinance_quote` /
`_fetch_ohlcv_from_yfinance` against a stubbed client that raises/times
out/returns empty frames; convert copy-string asserts to id/token asserts.

**5. Error handling — 7/10.**
Working: ops layer is genuinely fail-loud — `alert_runner` sends a HALT
notification on any exception; the hourly workflow proves payload freshness
before publishing anything; runtime artifact writes isolate side effects with
logged exceptions.
Not working: **fail-open safety gates** — `output.render_report:305-312`
defaults a symbol missing from `chain_results` to VALIDATED; qualification
Gates 9/10 pass on missing data, so a data outage silently *loosens*
qualification; `output._alert_context_line` renders "UNKNOWN | UNKNOWN | 0.00"
instead of failing on contract corruption. Silent swallows:
`dashboard_renderer.py:231` returns `""` on any timestamp parse error, no log;
`market_map.py:368` bare `except Exception: return None` around fib levels;
`contract.py:228` `except Exception: pass`.
Fix: invert the fail-open defaults on safety-relevant gates (missing chain
result → MANUAL_CHECK, not VALIDATED); log every swallow.

**6. Data flow and state management — 6/10.**
Working: upstream is immutable and typed end-to-end; persisted cross-run state
(notification dedup, execution-policy session, market-map backfill) is
explicit, file-backed, and funneled through `safe_write_latest`.
Not working: the contract is a mutable `dict[str, Any]` that runtime mutates in
place after construction (`contract["outcome"]` at `runtime:902`,
`system_state` keys at 908–919, `artifacts.notification_sent` at 952,
overnight-policy injection into candidates) — the consumed contract is a
superset of what `contract.py` builds, documented only in `SCHEMA_MAP.md`.
`assert_valid_contract` (contract.py:537) is called **only from tests** — the
strongest invariant surface in the codebase is dead in production, and it
doesn't guard `system_state` keys anyway. Module-global mutable notification
state in `output.py` is keyed partly off `PYTEST_CURRENT_TEST`
(`output.py:91-93`) — production behavior coupled to the test harness.
Fix: this is the #1 refactor (see Highest-Leverage Actions).

**7. Performance — 9/10.**
Working: ~24 symbols, batch cadence; parquet OHLCV cache keyed by trading day
plus CI cache warming; renderer accumulates lines and joins once; run-history
growth is capped (`prune_run_history.sh`). Nothing worth optimizing, and —
credit where due — nobody tried.
Not working (minor): `_run_with_timeout` (`ingestion.py:368-375`) can't cancel
a hung yfinance thread; the executor exit can block past the deadline.
Fix: nothing urgent. Leave performance alone.

**8. Security — 8/10.**
Working: env-only secrets, never logged, none committed (gitleaks-scanned);
no `pull_request_target`; the codex-review workflow is exemplary least-privilege
(key isolated to a `contents:read` job; the one third-party action SHA-pinned);
consistent `html.escape` on every dashboard interpolation; all outbound HTTP has
timeouts + TLS + bounded retry; no `shell=True` / `os.system` / `verify=False`
anywhere.
Not working: **deps are `>=` floors with no lockfile** (`pyproject.toml`) and CI
does bare `pip install -e .` — non-reproducible builds and an open supply-chain
surface on a runner holding `TELEGRAM_BOT_TOKEN`; this violates your own
PRD-198 invariant 6. First-party `actions/*` are tag-pinned, not SHA-pinned.
`telegram_debug.yml:33-49` prints chat IDs and message previews to public
Actions logs. Non-atomic `write_text` for `ui/dashboard.html`
(`dashboard_renderer.py:2688`) vs. the correct tmp+rename in
`regime_history.py:147`.
Fix: add a lockfile this week (`uv lock` or `pip-compile`); SHA-pin actions;
stop printing message text in the debug workflow.

**9. Developer workflow — 4/10.**
Working: auto-merge behind CI, protected-file hooks, `engine_doctor` as a real
health authority, scope-locking that demonstrably prevents sprawl, review gates
that killed bad work before build (PRD-150, PRD-019), a doctrine (PRD-198) with
each invariant tied to a real incident.
Not working: 52k lines of PRD history vs 19k of code; ~3.6 PRDs per source
module; ~19% of visible commits are pure closeout bookkeeping; PRDs 213–225
(near-all dashboard cosmetics) shipped as twelve 80–163-line specs in two days —
a CSS min-width tweak (PRD-225) carried a 115-line specification plus a
registry row, an index entry, and a separate closeout PR; the registry's own
commit hashes are unreachable after squash-merges, so the audit trail the
process exists to guarantee runs with `--skip-commit-resolvability`; five
alignment-cadence checks have all passed with "no drift," which means the ritual
currently detects nothing.
Fix: see What I Should Drop.

**10. Documentation and readability — 6/10.**
Working: README correctly delegates to canonical sources; VISION.md is the best
single document in the repo — sharp, honest, and load-bearing; SCHEMA_MAP /
CALL_SITE_MAP are a genuinely good idea; conftest docstrings explain *why* at a
professional level.
Not working: `docs/architecture.md` is materially wrong — it omits the entire
five-stage decision layer (`trade_decision` → `execution_policy` →
`trade_thesis` → `invalidation` → `entry_quality`), mislabels the flow gate as a
post-qualification layer when it runs inside `qualify_all`, and calls the output
contract "frozen dataclasses" when it is a plain mutable dict.
`qualification.py`'s docstring says "9 gates"; 11 are implemented. `output.py`
says "Consumed by runtime.py," which no longer exists. CALL_SITE_MAP line
numbers have drifted up to 59 lines. Four overlapping process docs restate the
same commit-discipline rules.
Fix: one PRD to rewrite `architecture.md` against the real `_run_pipeline`
order; fix the two stale docstrings; merge the overlapping process docs.

**11. Overengineering — present, concentrated in process.**
In code it's mild: the five-module decision gate chain (each module contributing
one `apply_*_gate` call, all hand-threaded through runtime) is a lot of surface
for a fixed linear sequence; `_PartialPipelineResult` is a hand-maintained
mirror; the dead `TRANSITION` regime branch and the documented-as-never-called
notification suppression function (`notifications/__init__.py:408`) are kept
shape-stability ballast. In process it's severe: the Codex-authenticity
apparatus (344-line workflow + 5 PRDs + 16 review artifacts) and full PRD
ceremony for CSS tweaks.

**12. Missing abstractions.**
The big one: **a typed contract boundary object.** Every downstream consumer
re-derives the contract's shape from string keys, and the docs institutionalize
the workaround ("consult SCHEMA_MAP before using a field"). A `TypedDict` (or
dataclass) for the contract, candidates, and system_state would delete a whole
class of runtime-only failures and most of SCHEMA_MAP's job. Second: a shared
numeric-coercion helper. Third: a gate-registry list for the decision chain so
adding a gate doesn't mean editing the god function.

---

## Progress Assessment (beginner-focused)

**Where you actually are.** Calling yourself a beginner undersells one axis and
oversells another. On *system direction* — specifying behavior, defining
invariants, catching drift, designing review gates — you are operating at a
level many mid-career engineers never reach. PRD-198 alone (six invariants,
each generalizing a real incident) is senior-engineer thinking. On *code-level
fluency* — reading a 400-line function and feeling where it should split,
noticing that a constant is defined twice, sensing that a validator is never
called — the evidence says this muscle is underdeveloped, because those defects
sat in a repo with 227 PRDs and 70 review artifacts and none of them caught
`EXTENSION_ATR_MULTIPLIER` living in two places.

**Skills you are clearly developing:** invariant thinking (fail-loud, assert
the resolved not the requested); test discipline (your suite bans the exact
pathologies most teams tolerate); scope control; honest self-documentation
(VISION's "the trap to watch for" section is rare self-awareness).

**Concepts you understand well:** immutability and why it matters (the frozen
dataclass upstream is consistent, not accidental); the difference between a
check that verifies words vs. reality; secrets hygiene; fail-loud operations.

**Concepts you're still shaky on:**
- *Type boundaries* — you type the easy half (per-layer carriers) and give up at
  the hard half (the contract), which is exactly where typing pays most.
- *Fail-open vs. fail-closed defaults* — several safety gates default to "pass"
  on missing data, which is backwards for a discipline tool.
- *When a function is too big* — the four giant functions grew by accretion,
  each addition locally reasonable, with no reflex saying "split this."
- *Proportionality* — the instinct that a CSS tweak and a regime-logic change
  deserve different amounts of ceremony.

**Bad habits forming:** process as displacement activity (governing the
reviewer instead of shipping the product); writing documentation instead of
making code self-describing (SCHEMA_MAP exists *because* the contract is
untyped); letting agents' local additions accrete without periodically reading
whole modules yourself.

**Good habits showing up:** every guard ships a red test; decisions are
recorded with rationale; killed work is recorded as killed; the repo prunes its
own machinery (the 2026-06-13 "cut net-negative machinery" entry is a great
sign).

**Your next stage of growth** looks like: reading code more than specifying it
for a while. Pick one module per week, read it top to bottom without an agent,
and write three sentences: what it does, what's ugliest, what you'd change.
When you can predict what my review found before reading it, you've leveled up.

---

## Highest-Leverage Actions (ranked)

**1. Cut the process weight by ~70% for small changes.**
- What: raise the MICRO-lane bar dramatically — cosmetic/CSS/copy changes get a
  one-paragraph PRD or none; batch cosmetics into one PRD per week; fold
  closeout bookkeeping into the implementation PR (one commit, not two).
- Why: this is where most of your hours are going. Twelve dashboard-cosmetic
  PRDs in two days at 80–163 lines of spec each is time not spent on the trap
  VISION itself names — turning awareness into changed trading behavior.
- Difficulty: easy (it's a policy change). Payoff: hours per week, permanently.
- First step: add one line to `docs/PRD_PROCESS.md`: "Changes touching only
  `ui/`-rendering copy, CSS, or layout require at most a 10-line MICRO note and
  land closeout in the same PR."

**2. Type the contract boundary and run the validator in production.**
- What: define `TypedDict`s (or dataclasses) for the contract, trade candidate,
  and system_state; make runtime's post-build mutations part of the builder's
  declared schema; call `assert_valid_contract` in `_run_pipeline` before
  writing artifacts, and extend it to guard `system_state`.
- Why: the entire downstream half is one typo away from a runtime-only failure,
  and your strongest invariant checker currently protects nothing. This also
  obsoletes most manual SCHEMA_MAP maintenance.
- Difficulty: medium (mechanical but wide). Payoff: eliminates the largest
  latent-bug class in the repo.
- First step: one PRD: "wire `assert_valid_contract` into `_run_pipeline` +
  add `system_state` key guard." That's a 20-line change with a red test, and
  it makes every later typing step safer.

**3. Fix the fail-open safety gates.**
- What: `output.render_report:305-312` (missing chain result must not default
  to VALIDATED); decide explicitly whether qualification Gates 9/10 should pass
  on missing data, and if yes, surface a "gate skipped: no data" marker in the
  report instead of a silent pass; make the NEUTRAL-direction symbol skip in
  `qualify_all:183-214` visible in output.
- Why: this is a *discipline* tool. A data outage that silently loosens the
  gates is the exact failure mode the system exists to prevent.
- Difficulty: easy. Payoff: correctness where it counts most.
- First step: red test — chain_results missing a symbol must yield
  MANUAL_CHECK in the rendered report.

**4. Add a lockfile and SHA-pin actions.**
- What: `uv lock` (or `pip-compile`) committed, CI installs from it;
  SHA-pin `actions/*` the way `openai/codex-action` already is.
- Why: your own PRD-198 invariant 6 names this as an open incident; the current
  setup resolves fresh deps on a runner holding your Telegram token.
- Difficulty: easy. Payoff: reproducible builds, closed supply-chain gap.
- First step: `uv lock` today; swap `pip install -e .` for a locked install in
  `ci.yml` and `cuttingboard.yml`.

**5. Break up `_run_pipeline` (451 lines) — not the whole runtime, just the
function.**
- What: extract the existing phases into named functions:
  `_run_market_read()`, `_run_qualification()`, `_run_decision_gates()`,
  `_build_and_finalize_contract()` — each taking/returning explicit values.
- Why: every future stage lands in this function; it's the highest-traffic
  code in the repo and currently the hardest to read.
- Difficulty: medium. Payoff: every subsequent change gets cheaper; the
  contract-mutation cluster (lines 902–952) becomes one visible function
  instead of scattered statements.
- First step: extract just the decision-gate chain (lines ~789–821) — it's
  already a clean linear sequence.

**6. Single-source the duplicated constants and schemas.**
- What: delete `market_map.EXTENSION_ATR_MULTIPLIER` (import from config);
  unify `_OPTIONAL_MACRO_DRIVERS` and the macro-driver schema into one module
  both contract and payload import; one shared `_iso()` and one
  `_coerce_float()`.
- Why: `EXTENSION_ATR_MULTIPLIER` is a live correctness bug waiting for the
  first tuning change — the map's "extended" grade and the qualification
  extension gate will silently diverge.
- Difficulty: easy. Payoff: kills a latent bug and a drift hazard.
- First step: grep both names, pick config as the owner, delete the copy.

**7. Test the two blind spots: `confirmation.py` and ingestion error paths.**
- What: `test_confirmation.py` covering `_crosses_level`/`_reclaims_level`
  directionally; ingestion tests where the stubbed yfinance client raises,
  times out, and returns an empty frame, asserting retry counts and the
  resulting `fetch_succeeded=False`.
- Why: confirmation logic is directional trading logic with zero coverage; the
  ingestion failure path is what runs on the worst morning of the year.
- Difficulty: easy-medium. Payoff: coverage where failures are expensive.

**8. Rewrite `architecture.md` against reality.**
- What: document the actual `_run_pipeline` order including the five-gate
  decision layer; fix "flow is L8," "contract is frozen dataclasses," the
  9-vs-11 gate docstring, and the `runtime.py` references.
- Why: your own VISION principle: "the system must match its documentation."
  Right now the single most important architecture doc would mislead any agent
  or human reading it.
- Difficulty: easy. Payoff: every future agent session starts less wrong.

---

## Bugs and Risks

Ranked by likely impact. Each has file refs, a fix, and a proving test.

1. **Missing chain result renders as VALIDATED (fail-open safety gate).**
   `output.py:305-312` constructs a default `ChainValidationResult(...VALIDATED)`
   for any setup absent from `chain_results`. A partial chain-validation failure
   silently upgrades to validated. Fix: default to `MANUAL_CHECK` with a
   rendered warning. Test: build a TRADE contract with one symbol missing from
   `chain_results`; assert the report shows MANUAL_CHECK, not a validated setup.

2. **`assert_valid_contract` never runs in production; runtime injects
   unguarded keys.** `contract.py:537` is test-only; `runtime:902-952` mutates
   `outcome`, `system_state.*`, `artifacts.notification_sent` after build, and
   the validator wouldn't catch bad `system_state` keys anyway. Fix: call it in
   `_run_pipeline` before artifact writes; add a `system_state` key whitelist.
   Test: corrupt a contract in a fixture run; assert the run exits non-zero
   (fail-loud) instead of writing artifacts.

3. **`EXTENSION_ATR_MULTIPLIER` defined twice** (`market_map.py:112`,
   `config.py:110`, both 1.5). First tuning change desynchronizes the map's
   "extended" grade from the qualification gate. Fix: import from config.
   Test: `assert market_map.EXTENSION_ATR_MULTIPLIER is config.EXTENSION_ATR_MULTIPLIER`
   — or better, delete the duplicate so the test is unnecessary.

4. **Qualification gates fail open on missing data.** Gates 9 (earnings,
   `qualification.py:427`) and 10 (extension, `:444`) pass when data is absent;
   combined with `.get(symbol)` → None metrics, an outage loosens the system.
   Fix: emit an explicit "gate skipped: missing data" soft-failure marker so
   the report shows degraded confidence. Test: qualify with `metrics=None`;
   assert the skip marker appears in the qualification summary.

5. **Symbols silently vanish in `qualify_all` when direction is NEUTRAL**
   (`qualification.py:183-214`): not qualified, not watchlisted, not excluded,
   not logged. Fix: append to `excluded` with reason `NEUTRAL_NO_DIRECTION`.
   Test: net_score=0 symbol → appears in excluded with that reason.

6. **Production notification dedup is coupled to pytest env.**
   `output.py:91-93` embeds `PYTEST_CURRENT_TEST` in the dedup scope key;
   module-global `sent_message_hashes` / `_LAST_SEND_TS` are process-global
   mutable state. Fix: inject a scope/clock into the notification sender;
   remove the pytest branch from production code. Test: existing suite keeps
   passing with the conftest fixture switched to the injected seam.

7. **No lockfile; `>=` dep floors; tag-pinned actions** (`pyproject.toml`,
   `ci.yml:20`). Your PRD-198 invariant 6 names this exact gap. Fix: commit a
   lockfile, install from it in CI, SHA-pin `actions/*`. Test: CI asserts
   `pip freeze` matches the lock (or use `uv sync --locked`, which fails on
   drift by construction).

8. **`architecture.md` materially stale** — omits the decision layer, wrong
   about the flow gate and "frozen" contract; `qualification.py` docstring says
   9 gates (11 exist); `output.py:17` references dead `runtime.py`;
   CALL_SITE_MAP line numbers drift up to 59 lines. Fix: rewrite against
   `_run_pipeline`. Test (cheap guard): a doc test asserting the gate-count
   string in the qualification docstring matches `len(GATES)`.

9. **Fixture mode monkey-patches production modules**
   (`runtime/__init__.py:1538` uses `unittest.mock.patch` on
   `cuttingboard.derived.fetch_ohlcv`). Fragile: any refactor of import sites
   silently breaks fixture mode. Fix: pass a fetch function (or small provider
   object) down explicitly; fixture mode supplies the cache-only variant.
   Test: fixture-mode run with the patch removed still produces identical
   artifacts.

10. **Silent exception swallows in rendering/parsing.**
    `dashboard_renderer.py:231` (timestamp → `""`), `market_map.py:368`
    (fib levels → None), `contract.py:228` (`pass`),
    `output.py:738` (falls back to slicing `generated_at[11:16]`). Fix: log
    every swallow; replace the string-slice fallback with a real parse.
    Test: feed a malformed timestamp; assert a log record is emitted.

11. **`telegram_debug.yml` prints chat IDs and message previews to public
    Actions logs** (`:33-49`). Fix: print booleans/counts only. Test: n/a —
    delete the message-text lines.

12. **Registry audit trail can't validate** — 19 COMPLETE hashes unreachable
    post-squash; CI runs `validate_prd_registry.py --skip-commit-resolvability`.
    Fix: record the *merge* commit (which survives squash) at closeout going
    forward; annotate historical rows as pre-fix. Test: validator runs without
    the skip flag on all new rows.

13. **Untested: `confirmation.py` (entirely) and ingestion retry/timeout
    paths** — see Highest-Leverage Action 7.

14. **Dead code kept without a decision:** notification suppression function
    documented as never called (`notifications/__init__.py:408`); `TRANSITION`
    regime branched on but unreachable (`regime.py:325`). Fix: delete or record
    a retained-with-reason note per your own dead-branch discipline.

---

## What I Should Drop

1. **Full PRD ceremony for cosmetic changes.** A CSS min-width tweak does not
   need a 115-line spec, a registry row, an index entry, and a separate
   closeout PR. This is the single biggest time leak in the repo.
2. **The separate closeout bookkeeping commit.** Fold registry/index/state
   updates into the implementation PR. That deletes ~19% of your commit volume
   and the entire sequencing-gate noise class your own CLAUDE.md complains
   about.
3. **The Codex-authenticity arms race.** You spent 5 PRDs, a 344-line workflow,
   and 16 review artifacts making the second AI reviewer tamper-evident — for a
   solo project where *you* merge everything anyway. Keep the simple read-only
   `codex exec` review for HIGH-RISK PRDs; drop the authenticity
   infrastructure. It caught one real issue (model laundering) and you fixed
   it; the marginal return is now negative.
4. **The alignment-cadence ritual in its current form.** Five runs, five
   passes, zero findings. Replace with: run it only at phase boundaries, and
   make it a 15-minute read of the diff-since-last-audit, not a documented
   ceremony.
5. **Accumulating `audits/` session sediment.** Eight dated recon folders plus
   a 128 KB gate-recon that nothing reads. Keep writing session notes if they
   help you resume; delete them after the next session confirms nothing was
   lost, or move them out of the repo.
6. **Hand-maintained line numbers in CALL_SITE_MAP.** They're already 59 lines
   stale. Keep the map at file/function granularity; drop line numbers
   entirely — `grep` is free.
7. **Duplicated process docs.** `dev_workflow.md`, `AGENT_WORKFLOW.md`,
   `CLAUDE_HOOKS.md`, and CLAUDE.md restate the same rules; per your own
   anti-duplication rule, merge to one owner and reference it.

## What I Should Keep Doing

1. **The PRD-198 semantic-failure invariants.** Best thing in the repo's
   process. Each invariant generalizes a real incident. Keep, enforce, extend.
2. **Every guard ships a red test.** Your suite has zero can't-fail tests.
   Most professional teams cannot say this.
3. **VISION.md as a kill-gate.** It demonstrably killed bad features
   (PRD-150). "Does this change what I will actually do?" is the right question
   for every feature, and you actually ask it.
4. **Scope-locked FILES sections** for substantive changes. It's why a 63-module
   repo with 225 PRDs has almost no sprawl in the source tree.
5. **DECISIONS.md with dates and rationale.** 41 entries in six weeks, and they
   record *reversals* honestly (PRD-212 "premise falsified"). That honesty is a
   durable asset.
6. **The frozen-dataclass upstream style.** Extend it downstream rather than
   diluting it.
7. **Fail-loud operational design** — HALT notifications, freshness-gated
   publish, prefetch that proves cache freshness with the engine's own check.
8. **The shared test/preview corpus pattern** (`preview_fixtures.py`) —
   structurally drift-proof; use this trick anywhere two artifacts must agree.
9. **engine_doctor and the protected-file hooks** — the two pieces of process
   automation that pay real rent.

---

## Suggested Development Workflow

A leaner loop sized to one person plus agents:

**Planning a session (5 minutes, before any agent runs).** Write three lines in
your session note: (1) the one outcome this session must produce, (2) the files
you expect to touch, (3) what "done" looks like as an observable check. If you
can't write line 3, the task isn't ready — that's your existing FAIL-condition
discipline, minus the ceremony.

**Choosing what to work on.** Alternate deliberately: one session on product
(something that changes a trading decision), then at most one on
debt/process — never two process sessions in a row. Your registry shows the
inverse pattern lately. VISION's own test — "does this change what I will
actually do?" — applies to your *engineering* backlog too, not just features.

**Avoiding scope sprawl.** Keep FILES-locking for STANDARD/HIGH-RISK work.
For cosmetics, batch: collect UI nits in a running list all week, then one
"dashboard polish" PR lands them together with one line of description each.

**Using tests.** Keep the red-test-first rule for guards. Add one habit: when
an agent implements something, *you* write (or at least specify) the failing
test before it starts. It's the highest-signal way to stay fluent in your own
system while delegating implementation.

**Using code review.** Redirect the review budget you free up from cosmetic
PRDs into one weekly deep read: pick one module, read every line yourself, log
three observations. The defects this review found (duplicate constant, dead
validator, fail-open default) are exactly the kind that per-PRD diff review
structurally misses — they live *between* diffs.

**Preventing technical debt.** Your acknowledged-debt-with-a-date rule is good;
add a size trigger: any function crossing ~80 lines or any module crossing ~800
gets a debt entry automatically. Both god modules grew because nothing ever
said "stop."

**Knowing when a feature is done.** Done = the observable check from your
session plan passes in CI, the docs it touches are updated in the same PR, and
the closeout row lands in the same PR. One PR, one done.

---

## Refactor Plan

**Immediate (this week, small PRs):**
- Wire `assert_valid_contract` into `_run_pipeline`; add `system_state` guard.
- Fix the VALIDATED fail-open default in `output.render_report`.
- Delete `market_map.EXTENSION_ATR_MULTIPLIER`; import from config.
- Commit a lockfile; install from it in CI.
- Fix the "9 gates" docstrings and dead `runtime.py` references.
- Stop printing message text in `telegram_debug.yml`.

**Short-term cleanup (next 2–4 weeks):**
- `test_confirmation.py` + ingestion error-path tests.
- Extract the decision-gate chain and contract-finalization from
  `_run_pipeline` into named functions.
- Unify macro-driver schema into one module; shared `_iso` and float-coerce
  helpers.
- Surface the NEUTRAL-symbol skip and gate-skipped-on-missing-data markers.
- Rewrite `architecture.md` against the real pipeline.
- Adopt the MICRO-lane widening + same-PR closeout policy.

**Medium-term architecture (next quarter, one PRD each):**
- TypedDict/dataclass contract boundary; retire SCHEMA_MAP's field-lookup role.
- Decompose `render_dashboard_html` into per-section renderers (the 22-kwarg
  signature becomes a small `RenderContext` object).
- Replace fixture-mode `mock.patch` with an injected fetch provider.
- Move notification dedup state out of module globals into an injected store;
  remove the pytest coupling.
- Decide the notifications↔delivery layout ownership (move `macro_tape_layout`
  to a neutral module or fold notifications' tape rendering into delivery).

**Avoid touching for now:**
- The `runtime/` package split beyond the function extractions above — it's
  acknowledged debt, and a full restructure isn't worth it until the typed
  contract lands (do that first; it makes the split mechanical).
- Performance anything.
- The regime model's inline thresholds — centralizing them in config is nice-
  to-have, but touching regime tuning values invites churn with no behavior
  change; do it opportunistically when regime logic next changes for a real
  reason.
- The five decision-gate modules' structure — a gate registry would be
  elegant, but the current chain works and is tested; fold this into the
  `_run_pipeline` extraction rather than doing it standalone.

---

## Final Mentor Notes

Three things I want you to actually internalize, because they'll change how you
see every codebase, not just this one.

**1. Discipline that isn't wired in is decoration.** You wrote a rigorous
contract validator — and never called it in production. You wrote a doctrine
saying deps must be pinned and locked — and your own pyproject floats every
dependency. You wrote a dead-branch enumeration rule — and carry a suppression
function whose docstring admits it never runs. The pattern: you are excellent
at *stating* invariants and inconsistent at *enforcing* them mechanically. The
fix is a habit, not a skill: every time you write a rule, immediately ask
"what runs, on every commit, that fails when this rule is broken?" If the
answer is "an agent remembers to check," the rule doesn't exist yet. You
already know this — it's PRD-198 invariant 4 — you just haven't applied it to
your own process layer.

**2. The seam between typed and untyped is where your bugs live.** Notice
where this review's findings cluster: not in the frozen-dataclass upstream, not
in the well-tested gates — at the boundary where `PipelineResult` becomes
`dict[str, Any]` and discipline hands off to convention. That's not a
coincidence; it's a general law. When you read any codebase from now on, find
the point where the types stop, and look there first. In yours, the fact that
you needed to write SCHEMA_MAP.md at all was the system telling you the
contract should be typed — documentation is often a compile error you chose to
prose over.

**3. Process is a tool for making decisions cheaper, and yours has started
making them more expensive.** The strongest evidence isn't the line counts —
it's that twelve cosmetic tweaks each paid full ceremony in the same two days,
while a duplicated risk constant, a dead validator, and a fail-open safety gate
sat unnoticed under 70 review artifacts. Ceremony was pointed at the wrong
altitude: heavy on per-diff paperwork, absent on whole-system reading. Rebalance
toward the thing only you can do — reading your own system until you can feel
where it's wrong.

The genuinely encouraging part: nothing in this review required talent you
haven't already demonstrated. The upstream pipeline, the test suite, and
VISION.md prove you can do sustained, disciplined work at a high standard. The
gaps are all attention-allocation, not ability. Point the same rigor at the
downstream half and at your own process budget, and this becomes a codebase
most working engineers would be glad to have written — with a trading tool
inside it, which is, after all, the point.
