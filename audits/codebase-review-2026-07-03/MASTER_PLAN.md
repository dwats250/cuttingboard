# MASTER PLAN — Codebase Hardening

Source: `audits/codebase-review-2026-07-03/mentor-review.md` (the full review).
This file is the RAILS. The review is the REFERENCE. You work from this file;
you open the review only when a step tells you to.

---

## How to use this file (read this every session — it's short)

1. **Open this file. Find the first unchecked `[ ]` box. That is your only
   task.** Do not scan ahead. Do not reorder. If a step feels wrong, write why
   in the Parking Lot at the bottom and do it (or skip it) next session with
   fresh eyes.
2. **One step per sitting.** Steps are sized 25–60 minutes. If a step is done
   and you have energy, you may start the next one — but finishing a step and
   stopping is a full win.
3. **Every step has a DONE WHEN.** You may only check the box when that exact
   check passes. Not "basically done" — the check passes or the box stays open.
4. **When you finish a step: check the box, commit this file** with message
   `plan: complete step N.N`. The plan's own git history becomes your progress
   log — you never have to remember where you were.
5. **STOP rules.** If you are stuck for 30 minutes: write one sentence in the
   Parking Lot about where you're stuck, commit, and stop. If a step spawns a
   new idea: Parking Lot, one line, keep moving. Ideas are not tasks until they
   have a box.

**Delegation model.** Steps marked `[AGENT]` are built to hand to Claude Code /
Opus 4.8: each has a copy-paste prompt in a block. Steps marked `[YOU]` are
deliberately yours — they're the code-reading reps the review said to build.
Do not delegate `[YOU]` steps; that defeats the plan.

**PRD numbers** below assume `next_prd = 226` in `docs/prd_index.json`. If
other work lands first, keep the letters (A, B, C…) and take whatever numbers
are next — the letters are stable, the numbers aren't.

---

## Progress tracker

| Wave | What | Status |
|---|---|---|
| 0 | Land the plan, set the anchor | ☐ |
| 1 | Correctness fixes (PRD A–E) | ☐ |
| 2 | Tests + docs (PRD F–G) + process change (H) | ☐ |
| 3 | Structural refactors (PRD I–M) — gated | ☐ |
| ∞ | Weekly module read (ongoing habit) | ☐ started |

---

## Wave 0 — Land the plan (do this first, ~30 min total)

### Step 0.1 `[YOU]` — Merge the review branch
- **Why:** the review and this plan only count once they're on `main`, where
  your hooks, PROJECT_STATE pointer, and future sessions can see them.
- **Do:** open a PR from `claude/codebase-review-mentorship-0zpui1` to `main`.
  Read the review's Executive Summary and Metrics table one more time while
  the PR sits there (that's the "full attention" pass). Merge it yourself —
  no auto-merge queue for this one; the point is that you read it.
- **DONE WHEN:** `git log main --oneline -3` on a fresh pull shows the audit
  commit, and `audits/codebase-review-2026-07-03/` exists on `main`.
- [x] done (audit folder on `main`; verified 2026-07-05)

### Step 0.2 `[YOU]` — Set the attention anchor
- **Why:** you asked for this to be brought back to your attention. Your
  repo already has an attention mechanism: the `Next step` line in
  `docs/PROJECT_STATE.md`. Point it here.
- **Do:** edit `docs/PROJECT_STATE.md` → set the Next step line to:
  `Work the master plan: audits/codebase-review-2026-07-03/MASTER_PLAN.md
  (find the first unchecked box)`. Commit directly as bookkeeping via a small
  PR per your normal flow.
- **DONE WHEN:** the line is on `main`. Every future session that reads
  PROJECT_STATE (yours and your agents') now gets routed to this file.
- [x] done (Next-step line pointed here through the window; now points at Block 4 → this file, #106)

### Step 0.3 `[YOU]` — Read one section of the review, out loud pace
- **Why:** codifying the knowledge is a stated goal. One section, properly,
  beats the whole document skimmed.
- **Do:** read ONLY "Final Mentor Notes" (3 ideas) in `mentor-review.md`.
  Write, in your own words, one sentence for each of the three ideas at the
  top of the Parking Lot below. No AI assistance for the sentences.
- **DONE WHEN:** three sentences exist in the Parking Lot, committed.
- [ ] done

---

## Wave 1 — Correctness (PRD A–E, one at a time, in order)

Every PRD in this wave follows the same 5-step ritual. The ritual IS the rails:

> **Ritual:** (1) scaffold Stage 0 → (2) red test first → (3) implement →
> (4) verify + review per lane → (5) close. One PRD fully closed before the
> next one opens. No exceptions — a half-open PRD is attention debt.

### PRD-A (≈226) — Wire the contract validator into production
`CLASS: CONTRACT · LANE: HIGH-RISK`

- **Why (1 line):** your strongest invariant checker, `assert_valid_contract`
  (`contract.py:537`), currently protects nothing — it's called only by tests.

#### Step A.1 `[YOU]` — Stage 0 scaffold (~15 min)
- **Do:**
  ```bash
  scripts/prd_open.sh --prd 226 \
    --title "Wire assert_valid_contract into _run_pipeline + system_state guard" \
    --lane HIGH-RISK --class CONTRACT \
    --summary "Contract validator is test-only; runtime injects unguarded system_state keys" \
    --commit
  ```
  Then edit the scaffold: FILES = `cuttingboard/contract.py`,
  `cuttingboard/runtime/__init__.py`, `tests/test_contract.py`, plus any test
  file your grep sweep finds (run: `rg -l "assert_valid_contract" tests/`).
  FAIL condition: *a contract missing a required `system_state` key, or
  carrying an undeclared one, must make the run exit non-zero BEFORE any
  artifact is written.*
- **DONE WHEN:** Stage-0 commit exists; FILES list includes every file the
  grep sweep surfaced.
- [x] done (PRD-233 stage 0, merged via #102, 2026-07-04)

#### Step A.2 `[AGENT]` — Red test, then implementation
- **Prompt to paste:**
  ```
  Work PRD-226 (docs/prd_history/PRD-226.md). Scope-locked to its FILES list.
  1. RED TEST FIRST: add a test that builds a valid contract, deletes
     system_state.permission, runs the pipeline finalization path, and asserts
     non-zero exit / raised error BEFORE artifact writes. Also a test that an
     UNDECLARED system_state key fails validation. Run them; show me they fail.
  2. Then implement: call assert_valid_contract in _run_pipeline before
     artifact writes; extend it with a system_state key whitelist covering the
     keys runtime legitimately injects (outcome, permission, reason,
     stay_flat_reason, session_type — verify the real set by reading
     runtime/__init__.py:900-960, do not trust this list).
  3. Run the full suite. Report: the red-test-before output, the green-after
     output, and the exact whitelist you derived with line references.
  ```
- **DONE WHEN:** you have seen the red test fail, then pass; full suite green.
- [x] done (PRD-233 red-then-green recorded in its review artifact; #102)

#### Step A.3 `[YOU]` — Review + close (~20 min)
- **Do:** read the diff yourself, end to end (it should be small). Check one
  thing personally: the whitelist in the validator matches what
  `runtime/__init__.py` actually injects — open both files side by side.
  Then run your lane's review gate (Claude review artifact + Codex
  cross-review per the CONTRACT matrix row), open the PR, close out with
  `scripts/prd_close.sh`.
- **DONE WHEN:** PR merged, closeout row on `main`.
- [x] done (PRD-233 COMPLETE @ #102; review-leg compression per signed Deviation 2)

### PRD-B (≈227) — Kill the VALIDATED fail-open default
`CLASS: CONTRACT · LANE: HIGH-RISK`

- **Why:** `output.py:305-312` treats a symbol *missing* from `chain_results`
  as VALIDATED — a safety gate that passes on absence of evidence.

#### Step B.1 `[YOU]` — Stage 0 (~15 min)
- **Do:** scaffold as in A.1 (`--class CONTRACT --lane HIGH-RISK`). FILES:
  `cuttingboard/output.py` + every test file from
  `rg -l "chain_results|MANUAL_CHECK|VALIDATED" tests/` that asserts on the
  render path. FAIL condition: *a TRADE-outcome contract whose setup symbol is
  absent from chain_results must render that setup as MANUAL_CHECK with a
  visible warning line — never as validated.*
- [x] done (PRD-234 stage 0; #102)

#### Step B.2 `[AGENT]` — Red test + implement
- **Prompt to paste:**
  ```
  Work PRD-227. Scope-locked to FILES. Red test first: TRADE contract, one
  setup symbol deliberately absent from chain_results; assert the rendered
  report marks it MANUAL_CHECK with a warning, and assert the current code
  FAILS this (it renders VALIDATED). Then change the default in
  output.py:305-312 from a synthesized VALIDATED result to MANUAL_CHECK +
  warning line. Full suite. Report red-then-green.
  ```
- [x] done (PRD-234 red-then-green; #102)

#### Step B.3 `[YOU]` — Review + close
- **Do:** same as A.3. Personal check: read the rendered report from the new
  test — does the warning line actually tell future-you what happened and what
  to do about it? If you'd have to look up what it means, reword it now.
- [x] done (PRD-234 COMPLETE @ #102; Deviation 2)

### PRD-C (≈228) — Qualification: no silent loosening, no vanishing symbols
`CLASS: EXECUTION · LANE: HIGH-RISK`

- **Why:** Gates 9/10 (`qualification.py:427,444`) pass when data is missing,
  and NEUTRAL-direction symbols (`:183-214`) disappear from all output —
  three silent behaviors in the module that most needs to be loud.

#### Step C.1 `[YOU]` — Stage 0. FILES from
  `rg -l "GATE_|excluded|soft_failures" tests/` + `cuttingboard/qualification.py`.
  FAIL conditions (three, all observable): missing-data gate pass emits a
  `gate skipped: missing data` marker in the qualification summary; NEUTRAL
  symbols appear in `excluded` with reason `NEUTRAL_NO_DIRECTION`; both are
  visible in the rendered report.
- [x] done (PRD-235 stage 0; #102)

#### Step C.2 `[AGENT]` — Red tests (three) + implement. Prompt as before:
  red-first, scope-locked, full suite, report red-then-green per fail
  condition.
- [x] done (PRD-235 three red tests; #102)

#### Step C.3 `[YOU]` — Review + close. Personal check: qualify a symbol with
  `metrics=None` in a REPL or test and read the summary yourself — is the
  degradation obvious at a glance?
- [x] done (PRD-235 COMPLETE @ #102; Deviation 2)

### PRD-D (≈229) — Single-source the duplicated constants
`CLASS: EXECUTION (touches qualification-adjacent tuning) · LANE: STANDARD`

- **Why:** `EXTENSION_ATR_MULTIPLIER` lives in BOTH `market_map.py:112` and
  `config.py:110`. First tuning change desynchronizes the map's "extended"
  grade from the qualification gate. Also: `_iso()` duplicated byte-identically
  (`contract.py:434`, `market_map.py:606`), four float-coerce reimplementations.

#### Step D.1 `[YOU]` — Stage 0. FILES: `market_map.py`, `config.py`,
  `contract.py`, `chain_validation.py`, `output.py`, `time_utils.py` (new
  shared helpers land here), + test files from
  `rg -l "EXTENSION_ATR_MULTIPLIER|_safe_float|_optional_float|_iso" tests/ cuttingboard/`.
  FAIL condition: *`rg "EXTENSION_ATR_MULTIPLIER\s*=" cuttingboard/` returns
  exactly one line, in config.py.*
- [ ] done

#### Step D.2 `[AGENT]` — Implement (this one is mechanical; no red test
  possible for a deletion — the FAIL condition above is the check, plus:
  full suite green and a fixture-mode run producing byte-identical
  `logs/latest_contract.json` before/after).
- [ ] done

#### Step D.3 `[YOU]` — Review + close. Personal check: run the rg command
  from D.1 yourself. One command, your own terminal. (This is the review's
  "sub-agent sweep re-verification" rule — you re-run the decisive grep.)
- [ ] done

### PRD-E (≈230) — Lockfile, pinned actions, debug-log hygiene
`CLASS: INFRA · LANE: HIGH-RISK (touches .github/workflows/**)`

- **Why:** deps are `>=` floors with no lockfile on a runner that holds your
  Telegram token — your own PRD-198 invariant 6, still open. Plus
  `telegram_debug.yml` prints chat IDs/message text to public Actions logs.

#### Step E.1 `[YOU]` — Stage 0. FILES: `pyproject.toml`, new lockfile,
  `.github/workflows/ci.yml`, `cuttingboard.yml`, `hourly_alert.yml`,
  `macro_awareness.yml`, `pages.yml`, `dashboard_preview.yml`,
  `telegram_debug.yml`. FAIL conditions: CI installs with `uv sync --locked`
  (fails on drift by construction); every `uses:` line is SHA-pinned with a
  version comment (pattern already correct at `codex-review.yml:100`);
  telegram_debug prints booleans/counts only.
- [ ] done

#### Step E.2 `[AGENT]` — Implement. Prompt: scope-locked; generate the
  lockfile; convert installs; SHA-pin every action copying the
  codex-review.yml style; strip message text from telegram_debug; then
  dispatch the CI workflow and confirm green — *CI is where truth is
  determined, a local pass does not count* (invariant 5).
- [ ] done

#### Step E.3 `[YOU]` — Review + close. Personal check: open one workflow file
  and one Actions run log; confirm the pinned SHA in the log matches the file.
- [ ] done

**WAVE 1 EXIT CHECK:** all 15 boxes above checked, five PRDs closed on `main`,
CI green. Update the Progress tracker. Take a real break before Wave 2.
- [ ] Wave 1 complete

---

## Wave 2 — Tests, docs, and the process change

### PRD-F (≈231) — Cover the two blind spots
`CLASS: EXECUTION (test-only) · LANE: STANDARD`
- **Why:** `confirmation.py` (directional level-cross logic) has ZERO tests;
  `ingestion.py`'s retry/timeout/empty-frame paths are mocked away everywhere.
- `[YOU]` Stage 0. FILES: `tests/test_confirmation.py` (new),
  `tests/test_ingestion_errors.py` (new). Zero production lines.
- `[AGENT]` Prompt: write `test_confirmation.py` covering `_crosses_level` /
  `_reclaims_level` both directions + boundary-touch cases; write ingestion
  tests where a stubbed yfinance client (a) raises, (b) exceeds
  FETCH_TIMEOUT_SECONDS, (c) returns an empty frame — asserting retry counts
  and `fetch_succeeded=False`. Every test must be shown failing against a
  deliberately broken assertion first (no can't-fail tests — invariant 4).
- `[YOU]` Review: read `test_confirmation.py` in full — it doubles as your
  first guided read of `confirmation.py`. Close.
- [ ] F done

### PRD-G (≈232) — Make architecture.md true
`CLASS: GOVERNANCE (docs) · LANE: STANDARD`
- **Why:** the doc omits the entire 5-stage decision layer, mislabels the flow
  gate, and calls the contract "frozen dataclasses" (it's a mutable dict).
  Your VISION principle: the system must match its documentation.
- `[AGENT]` Prompt: rewrite `docs/architecture.md` against the REAL order in
  `runtime/__init__.py::_run_pipeline` (read it, list every stage call in
  sequence, then document that). Fix: flow gate runs inside qualify_all;
  contract is a validated dict, not dataclasses; add the decision layer
  (trade_decision → execution_policy → trade_thesis → invalidation →
  entry_quality). Also fix `qualification.py` "9 gates" docstrings (11 exist)
  and `output.py:17` "runtime.py" reference. Also remove line numbers from
  docs/CALL_SITE_MAP.md, keep file+function granularity.
- `[YOU]` Review: read the new architecture.md top to bottom. This is the
  single most useful document read in the whole plan — it's your system, as
  it actually is, in one file. If anything surprises you, that surprise is
  real knowledge: write it in the Parking Lot. Close.
- [ ] G done

### PRD-H (≈233) — Right-size the ceremony (GOVERNANCE, MANUAL MERGE)
`CLASS: GOVERNANCE · LANE: HIGH-RISK by policy — this changes the rules`
- **Why:** the review's #1 leverage item. Cosmetic changes currently pay the
  same freight as regime-logic changes; closeout is a separate PR doubling
  your commit count.
- `[YOU]` (not delegable — these are YOUR rules): edit `docs/PRD_PROCESS.md`
  and `CLAUDE.md` to add exactly two rules:
  1. *Changes touching only ui-rendering copy, CSS, or layout require at most
     a 10-line MICRO note; cosmetics batch into at most one polish PRD per
     week.*
  2. *Closeout bookkeeping lands in the SAME PR as the implementation. The
     separate closeout commit is retired.*
- **Per your own CLAUDE.md governance rule: open the PR and merge it BY HAND.
  No auto-merge. Read your own diff.**
- [x] H done (PRD-229, Dustin's hand-merge of #99, 2026-07-04 — Deviation 1 signed)

**WAVE 2 EXIT CHECK:** F, G, H closed. From here on, every PRD you do is
cheaper because of H. Update tracker.
- [ ] Wave 2 complete

---

## Wave 3 — Structural (GATED — do not start until the gate passes)

> **GATE:** Wave 1 fully closed (especially PRD-A — the validator must be live
> in production, because it is the regression net for everything below) AND
> you have done at least 3 weekly module reads (see below). If either is
> false, you are not ready — go do those.
- [x] Gate passed on date: 2026-07-04 (PRD-A live on main via #102; Deviation 2 signed in-session; suite green at 2874/1 xfailed on main CI)

Order is mandatory. Each item gets its own work order generated fresh at start
time — do NOT write detailed instructions now; the repo will have moved.
The prompt to generate each work order:

```
Read audits/codebase-review-2026-07-03/mentor-review.md (Refactor Plan +
Bugs sections) and MASTER_PLAN.md Wave 3 item <letter>. Inspect the CURRENT
state of the files involved. Produce a Stage-0-ready PRD: FILES (with grep
sweep), red-test-first spec, and the behavior-preservation check. For any
behavior-preserving refactor the FAIL condition is: a fixture-mode run before
and after produces byte-identical latest_run.json, latest_contract.json, and
rendered report.
```

- **I (≈234)** — Extract the decision-gate chain + contract finalization from
  `_run_pipeline` into named functions. EXECUTION/HIGH-RISK.
  Behavior-preserving; byte-identical check applies. — [x] done (PRD-236 @ #104; byte-identical proof)
- **J1 (≈235)** — Typed contract: define TypedDicts for contract / candidate /
  system_state; adopt in `contract.py` + `payload.py`. CONTRACT/T0, full
  consumer audit per your matrix. **`[YOU]`: read the J1 schema diff yourself,
  line by line. This is the one diff in the plan worth your personal hour.**
  — [x] done (PRD-237 @ #105; Dustin's line-by-line read at the PR, his merge)
- **J2 (≈236)** — Adopt the types in renderer + notifications; retire
  SCHEMA_MAP's field-lookup role (keep it as prose overview or delete).
  — [x] done (PRD-238 @ #106; M's design map also landed there — docs/renderer_decomposition_map.md — M execution stays open below)
- **K (≈237)** — Fixture mode via injected fetch provider; delete
  `unittest.mock.patch` from `runtime/__init__.py`. INFRA. Byte-identical
  fixture-run check. — [ ] done
- **L (≈238)** — Notification dedup state injected (kill module globals +
  `PYTEST_CURRENT_TEST` coupling in `output.py:91`). CONTRACT. — [ ] done
- **M (≈239+)** — Renderer decomposition: `RenderContext` object replaces the
  22-kwarg signature; per-section render functions. CONSUMER, split into 2–3
  PRDs, byte-identical check per stage. Do LAST. — [ ] done

**WAVE 3 EXIT CHECK:** the review's Metrics table re-scored. Ask for a fresh
review of just Architecture / Maintainability / Data flow — target: every 6
becomes ≥8.
- [ ] Wave 3 complete

---

## The weekly habit (runs alongside everything — this is the actual mentorship)

One module per week. Read it top to bottom, alone, no agent. Then write THREE
sentences in the log below: what it does / what's ugliest / what you'd change.
15–30 minutes. The order is chosen so each read supports the next wave's work:

1. `contract.py` (before PRD-A review)          — [ ] read, 3 sentences logged
2. `output.py` (before PRD-B)                    — [ ] done
3. `qualification.py` (before PRD-C)             — [ ] done
4. `confirmation.py` (with PRD-F)                — [ ] done
5. `runtime/__init__.py` — just `_run_pipeline`, 611–1061 (before Wave 3 gate) — [ ] done
6. `flow.py` + the qualify_all flow-gate loop    — [ ] done
7. `market_map.py`                               — [ ] done
8. `regime.py`                                   — [ ] done
9. `intraday_state_engine.py`                    — [ ] done
10. `delivery/payload.py` (before J1)            — [ ] done

### Module-read log
(3 sentences per module, dated. No AI. Bad sentences count; absent ones don't.)

---

## Parking Lot
(One line per item. Ideas, stuck-points, surprises. Review at each Wave exit —
promote to a box, or delete. Nothing in here is a commitment.)

- **[FABLE WINDOW sign-off — Dustin]** Two deviations per
  `FABLE_WINDOW_PLAN.md` (this folder): Deviation 1 — PRD-H drafted by Fable,
  hand-merged by Dustin (spirit kept: your rules, your merge). Deviation 2 —
  Wave-3 gate's 3-module-reads clause deferred to the post-window learning
  stint, replaced in-window by byte-identical fixture checks + your
  line-by-line J1 schema-diff read. **Deviation 1: SIGNED 2026-07-04 (Dustin's
  hand-merge of PR #99). Deviation 2: SIGNED 2026-07-04 — Dustin's explicit
  in-session confirmation ("Signed — open Block 3") after PRD-233 (PRD-A)
  reached main via PR #102. Block 3 opened; the J1 line-by-line schema-diff
  read remains Dustin's non-negotiable seam.**
- 2026-07-04 (Fable): the drop-list's "audits/ sediment that nothing reads"
  premise is wrong — every dated recon folder except `inventory-audit-brief.md`
  has inbound refs (DECISIONS.md, PRD history, CLAUDE.md:295, one test
  docstring). Purge re-scoped: delete only the unreferenced item + stop new
  sediment; disposition of the referenced folders is yours at Block-1 review.
- Step 0.3 sentences go here first:
  1.
  2.
  3.

---

## If you come back after a long gap and remember nothing

Read this section only. You are hardening a good codebase per a full review.
The review is `mentor-review.md` in this folder — read its Executive Summary
(2 minutes). Then find the first unchecked box above and do only that. The
plan's git history (`git log --oneline -- audits/codebase-review-2026-07-03/`)
shows exactly what you've done so far. You don't need to remember anything;
that's what this file is for.
