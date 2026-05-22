# Cuttingboard Cleanup Brief — Phase 1, Step 2

**For:** Claude Code, executing against the cuttingboard repo on `asher`
**Prerequisite:** VISION.md committed to repo root (commit 1 of this brief). Inventory audit at `audits/inventory-2026-05-22/` already complete and reviewed.
**Output:** Ten commits (described below) plus verification artifacts in `audits/cleanup-2026-05-22/`.
**Mode:** Mutating. This brief executes deletions, renames, and rewrites. Each commit is independent and reviewable.

---

## Context

Read `VISION.md` and the inventory audit at `audits/inventory-2026-05-22/` before beginning. This brief is the execution phase of the realignment those documents anchor.

The goal is **alignment between code and stated vision**. Remove what doesn't earn its keep, restructure documentation to a single source of truth, and leave the repo in a state where VISION.md accurately describes what's in the codebase.

You may invoke Codex for any task where its cross-referencing or code-review strengths apply. Default to Codex for: scoped reads of long PRDs, verification tasks with structured deliverables, cross-file consistency checks. Do not invoke Codex for: simple greps, git operations, single-file edits, or anything where the answer is mechanical.

---

## Verification tasks (do these first, before any deletions)

Produce `audits/cleanup-2026-05-22/verifications.md` documenting findings. These results inform later commits.

### V1. `market_map_lifecycle.py` mutation check

Read `cuttingboard/market_map_lifecycle.py`. Determine: does it mutate `market_map` artifacts after first emission, or only annotate during initial build? VISION.md requires sidecars to be read-only. Document finding. If it mutates, flag as a Phase 2 refactor candidate (do not refactor in this cleanup pass).

### V2. PRD-053 / PRD-053-PATCH / PRD-054 reconciliation

Read `docs/prd_history/PRD-053.md`, `docs/prd_history/PRD-053-PATCH.md`, the PRD-054 row in `docs/PRD_REGISTRY.md`, and `cuttingboard/market_map.py`. Determine: does the current `market_map.py` reflect PRD-053's intent? Two possible outcomes:
- **Yes** → PRD-053 and PRD-053-PATCH should flip to `COMPLETE` with a note that they landed under PRD-054
- **No** → PRD-053 and PRD-053-PATCH should flip to `DEPRECATED` with a note that PRD-054 superseded

Document the determination and which path applies. This drives commit 6.

### V3. `fix_workflow.sh` invocation check

Search the repo for any invocation of `fix_workflow.sh` (CI workflows, other shell scripts, docs). If no live invocation exists, mark for deletion. If invocations exist, document them and flag for review before deletion.

### V4. `numpy` and `pytest-mock` direct usage

Search beyond `cuttingboard/` (tests, scripts, tools, top-level scripts) for direct `import numpy` or `mocker`/`pytest_mock` usage. Document findings. If no direct usage anywhere, mark for removal from `pyproject.toml` in commit 8.

### V5. AGENTS.md content analysis

Read `AGENTS.md`. Compare against `CLAUDE.md` and `CODEX.md`. Determine: does AGENTS.md contain content not present in either of the other agent files? If yes, surface the unique content for review before deletion. If content is fully duplicated or generic boilerplate, mark for deletion in commit 7.

### V6. `tests/test_orb_reference.py` parity check (informational)

Already decided to delete `algos/orb_reference.py` and `tests/test_orb_reference.py`. This verification is informational only: confirm the test file doesn't cross-validate any other production module before deletion. If it does, flag before deleting.

### V7. `notifications/formatter.py` rename impact

Search for all callers of `format_ntfy_alert`. Document the call sites. This informs the rename scope in commit 3.

---

## Tooling runs (parallel to verifications, before commits)

Produce these as audit artifacts in `audits/cleanup-2026-05-22/`. Do not act on findings automatically; they are for human review.

### T1. Vulture run

Run `vulture` against `cuttingboard/` with sensible defaults. Save output to `audits/cleanup-2026-05-22/vulture-output.md` with a brief header explaining the tool's limits (dynamic imports, reflection, fixture-mode paths are invisible). Highest-value target: `runtime.py` (2100 LOC monolith likely contains uncalled internals).

### T2. Gitleaks run

Run `gitleaks` against the full repo history. Save output to `audits/cleanup-2026-05-22/gitleaks-output.md`. **If anything is flagged, surface immediately and pause the cleanup** until reviewed — this is the only finding that can interrupt the planned commit sequence.

---

## Commits

Each commit is self-contained and reviewable. Commit messages should be plain, specific, and reference VISION.md or the inventory audit where relevant.

### Commit 1 — VISION.md + DECISIONS.md scaffold

**Files:**
- `VISION.md` (already drafted; should already be committed before this brief runs, but verify)
- `docs/DECISIONS.md` (new)

`docs/DECISIONS.md` structure:
```markdown
# Decisions log

Meaningful decisions and rationale. Date-ordered, newest first. 
Short notes, not ceremony.

---

## 2026-05-22 — Phase 1 realignment

Executed VISION.md-anchored cleanup. See `audits/inventory-2026-05-22/` 
for the audit that surfaced the cleanup scope and 
`audits/cleanup-2026-05-22/` for verification findings.

Key decisions:
- Polygon integration removed (never used in production)
- ntfy references removed (PRD-006 already removed code; this cleans docs)
- Legacy intraday entrypoint `run_intraday.py` deleted (live engine is 
  `intraday_state_engine.py` consumed by `runtime.py`)
- LLM-driven macro sidecar `tools/macro_collector.py` deleted 
  (no consumer; latent risk of crossing description/prediction line)
- Backtesting harness deleted (contradicts VISION non-goal)
- ORB Pine script and reference module deleted; rebuild intent 
  documented at `pinescripts/README.md`
- PRD-142 deprecated; PRD-053/053-PATCH/054 reconciled (see verifications)
- Agent files restructured to lean skeleton; AGENTS.md deleted as redundant
- PROJECT_STATE.md elevated as canonical current-state source
```

**Commit message:** `chore: add VISION.md and DECISIONS.md as realignment anchors`

### Commit 2 — Polygon removal

**Files modified:**
- `cuttingboard/config.py` — remove `POLYGON_API_KEY` (line 54), `"polygon"` from default source-priority list (line 175), `POLYGON_PREV_URL` constant + comment (lines 220-223)
- `cuttingboard/ingestion.py` — remove `_try_polygon_quote`, `_polygon_quote_raw`, `"polygon"` source branch (lines 35, 99-100, 359-448)
- `cuttingboard/contract.py` — remove polygon fallback flag (line 475)
- `cuttingboard/runtime.py` — remove polygon-fallback-used branches (lines 1149, 2017)
- `pyproject.toml` — remove any polygon-related dependency or extra
- `.env` — remove `POLYGON_API_KEY` line (file itself stays; just remove the line)
- `docs/engine_doctor.md` — remove Polygon from `.env` documentation (~line 93)

**Verify:** all 297 tests still pass after this commit. If any test was Polygon-dependent and fails, surface the test for review before continuing.

**Commit message:** `refactor: remove unused Polygon integration`

### Commit 3 — ntfy doc and naming cleanup

**Files modified:**
- `README.md` — remove ntfy references (lines 45, 97)
- `docs/architecture.md` — remove ntfy lines (lines 23, 41, 45, 190, 195, 200, 259, 323, 365)
- `docs/engine_doctor.md` — remove ntfy from `.env` doc
- `cuttingboard/notifications/formatter.py` — rename `format_ntfy_alert` to `format_telegram_alert` (line 58)
- All callers of `format_ntfy_alert` (use V7 findings) — update to new name
- `.claude/skills/generated/notifications/SKILL.md` — update reference if present

**Do not modify:** `tests/test_prd006_notification_transport.py` — these tests enforce ntfy removal and must remain unchanged.

**Verify:** all tests pass.

**Commit message:** `refactor: clean up stale ntfy references in docs and rename formatter`

### Commit 4 — Orphan and legacy module deletions

**Files deleted:**
- `cuttingboard/notify_test.py`
- `cuttingboard/run_intraday.py`
- `tools/macro_collector.py`
- `algos/` directory (entire)
- `tests/test_orb_reference.py`
- `backtesting/` directory (entire)
- `data/backtests/` directory (entire)

**Verify:** all tests pass. If any test imports a deleted module, surface for review before continuing — this would indicate the module wasn't actually orphaned.

**Commit message:** `chore: remove orphan modules, legacy intraday entrypoint, backtesting harness, and unused macro sidecar`

### Commit 5 — Root-level cruft and Pine reset

**Files deleted:**
- `traceback.txt`
- `repo_snapshot.md`
- `.cb_commit_msg`
- `mockup.html`, `mockup_echofi.html`, `mockup_zeex.html`
- `fix_workflow.sh` (only if V3 confirms no invocations)
- `pinescripts/0dte Momentum Setup`
- `config/` directory (empty except `__pycache__`)

**Files added:**
- `pinescripts/README.md` — content provided separately; captures rebuild intent for ORB indicator and multi-tool monitoring utility

**Files modified:**
- `.gitignore` — add `cuttingboard.egg-info/`

**Commit message:** `chore: remove root-level cruft and reset pinescripts with documented rebuild intent`

### Commit 6 — PRD registry reconciliation

**Files modified:**
- `docs/PRD_REGISTRY.md`:
  - Flip PRD-142 to `DEPRECATED` with note "scheduled for kill per VISION.md 2026-05-22 — workflow change never landed"
  - Apply V2 finding to PRD-053, PRD-053-PATCH, PRD-054 (either flip to `COMPLETE` with PRD-054 note, or to `DEPRECATED` with superseded note)
  - Eliminate all `READY` status entries (replace with canonical status based on actual state)
  - Fix PRD-054 row's non-canonical status text
- `tools/validate_prd_registry.py` — add check that all status values are in the canonical set (PROPOSED, IN PROGRESS, COMPLETE, PATCH, DEPRECATED)

**Verify:** run `tools/validate_prd_registry.py` after changes; should pass.

**Commit message:** `docs: reconcile PRD registry — deprecate PRD-142, resolve PRD-053 lineage, eliminate non-canonical READY status`

### Commit 7 — Agent file restructure

**Files modified:**
- `CLAUDE.md` — rewrite to lean skeleton (template below)
- `CODEX.md` — rewrite to lean skeleton (template below) with invocation tiering

**Files deleted:**
- `AGENTS.md` (only if V5 confirms redundancy; otherwise surface unique content for review)

**Skeleton for both agent files:**

```markdown
# [CLAUDE|CODEX].md

## Role
[2-3 sentences specific to this agent's role in this repo]

## Canonical sources
This repo's state lives in source-of-truth documents. Reference these, 
do not duplicate them.

- `VISION.md` — what Cuttingboard is, is not, is becoming
- `PROJECT_STATE.md` — current state: test counts, milestones, known debt
- `docs/PRD_REGISTRY.md` — work in flight and completed
- `docs/DECISIONS.md` — meaningful decisions and rationale
- `README.md` — outsider's entry point

## Working agreement
Dustin makes final decisions. Claude (project lead, in chat) drafts PRDs 
and reviews against VISION principles. Claude Code implements. Codex is 
invoked by Claude Code for specialist tasks (cross-referencing, structured 
analysis, code review). Architectural direction stays with Claude and 
Dustin.

Decisions that meaningfully change direction are recorded in `docs/DECISIONS.md` 
with date and rationale.

## Operational rules
- PRD before build for anything non-trivial (new module, new external 
  dependency, new architectural pattern, change touching multiple pipeline 
  layers). Bug fixes and additions within established patterns don't 
  need PRDs.
- Read-only sidecars by default. New observational features extend through 
  sidecars rather than mutating core contracts.
- Description, not prediction. Features that explain or contextualize are 
  welcome. Features that forecast are not.
- Cuts before additions. Before adding a feature, the system should justify 
  the features it already has.

## Workflow patterns
[Agent-specific guidance]

## Anti-patterns
[Specific failure modes observed for this agent in this repo]
```

**CLAUDE.md-specific content:**

Role: "Primary implementation agent for Cuttingboard. Drives PRD construction, code implementation, test maintenance, and architectural decisions within PRD scope. Invokes Codex for specialist tasks."

Workflow patterns:
- Start work on a PRD by reading the PRD file, the related modules, and any prior decisions in `docs/DECISIONS.md`
- When drift is discovered mid-task (code doesn't match docs, undocumented dependencies surface), pause and surface the drift before proceeding
- Invoke Codex for: scoped reads of long PRDs, cross-file consistency checks, structured code review
- Do not invoke Codex for: simple greps, git operations, mechanical edits

Anti-patterns:
- Do not draft PRDs for features that violate VISION.md non-goals without explicit override from Dustin
- Do not refactor `runtime.py` opportunistically; it is acknowledged debt and refactors require their own PRD
- Do not add documentation that duplicates content in canonical sources; reference instead

**CODEX.md-specific content:**

Role: "Specialist agent invoked by Claude Code for cross-referencing, structured analysis, and code review. Not a primary implementation agent. Should not drive architectural direction."

Workflow patterns:
- Stay within the scope of the invoking task. If asked to drive direction beyond the task, defer to Claude Code or surface the question to Dustin.
- Use scoped reads for long PRDs — read the specific section relevant to the question, not the whole document.
- Prefer structured deliverables (tables, checklists, classified findings) over open-ended prose.

Invocation tiering:

```
| Task | Model tier | Notes |
|------|-----------|-------|
| Complex PRD construction, multi-file architectural reasoning | Premium tier | Use sparingly |
| Code review, cross-referencing, structured analysis | Mid tier | Default for most invocations |
| Scoped reads from long documents | Mid tier with chunked input | Don't load entire PRDs |
| Grep, git status/log/diff, simple commands | Smaller model or direct shell | Don't burn premium tokens on mechanics |
```

Anti-patterns:
- Do not propose architectural changes beyond the scope of the invoking task
- Do not produce open-ended exploration when a structured deliverable was requested
- Observed failure mode: drift when given the reins. Counter by staying narrow.

**Commit message:** `docs: restructure agent files to lean skeleton anchored to canonical sources; delete redundant AGENTS.md`

### Commit 8 — Dependency hygiene

**Files modified:**
- `pyproject.toml`:
  - Remove `numpy` (only if V4 confirms no direct usage)
  - Remove `pytest-mock` (only if V4 confirms no direct usage)
  - Add comment on `pyarrow`: `# transitive, required for parquet I/O via pandas`

**Verify:** all tests pass after dependency changes. If any test fails due to removed dependency, restore it and document why.

**Commit message:** `chore: remove unused dependencies and document transitive requirements`

### Commit 9 — Branch cleanup

Git operations only, no file changes.

- Delete merged PRD branches on origin: `prd-044-real-macro-driver-payload`, `prd-045-trade-decision-materialization`, `prd-046-decision-trace`, `prd-047-post-trade-evaluation`, `prd-049-alert-optimization`, `prd-049-patch-02-guidance`, `prd-050-alert-fallback`, `prd-051-execution-policy`, `prd-053-market-map`, `prd-062-evaluation`, `prd4-trade-policy`, `prd061-main`
- Delete local-only stale branches: `integrate-gitignore`, `integrate-hourly-pages`, `integrate-main-deploy`
- Delete other clearly post-merge local branches if confirmed merged

**Commit message:** N/A (git branch operations, not file commits). Document in `audits/cleanup-2026-05-22/branch-cleanup.md` what was deleted.

### Commit 10 — PROJECT_STATE.md refresh and README update

**Files modified:**
- `PROJECT_STATE.md`:
  - Update test count to current actual passing count
  - Add 2026-05-22 milestone: "Phase 1 realignment cleanup complete"
  - Update known debt list to reflect current state (remove items resolved by this cleanup, retain items deferred)
- `README.md`:
  - Restructure to reference VISION.md as canonical statement of what the system is
  - Reference PROJECT_STATE.md as canonical current state
  - Remove any system descriptions duplicated in canonical sources
  - Keep installation, run instructions, and pointers to canonical docs

**Commit message:** `docs: refresh PROJECT_STATE and README to reflect post-cleanup state`

---

## Constraints

- **No scope expansion.** Stick to this brief. If something surfaces that warrants action but isn't in the brief, flag it in `audits/cleanup-2026-05-22/surfaced-issues.md` for review; do not act on it.
- **Tests must pass after every commit.** If a commit breaks tests, fix or revert before the next commit. Document any test fix in the commit message.
- **No refactoring `runtime.py`** in this pass, even if vulture surfaces uncalled internals. That's a future PRD.
- **Halt on surprises.** If gitleaks finds anything, if a "dead" module turns out to have live consumers, if a PRD reconciliation is genuinely ambiguous — pause and surface for review rather than guessing.
- **Honesty about limits.** If a verification can't be completed (e.g., dynamic imports can't be statically analyzed), document the limit rather than asserting falsely.

## Tone

Plain commit messages. No marketing language. No flourishes. The cleanup serves the system; it isn't the point of the system.

## When complete

1. All ten commits landed on `main` (or on a `realignment/phase-1-cleanup` branch for review before merge — your call based on team conventions)
2. `audits/cleanup-2026-05-22/` directory contains: `verifications.md`, `vulture-output.md`, `gitleaks-output.md`, `branch-cleanup.md`, optionally `surfaced-issues.md`
3. All tests passing
4. VISION.md, PROJECT_STATE.md, agent files, and README internally consistent — no contradictions between source-of-truth documents
5. Notify Dustin that cleanup is complete and ready for Phase 1 step 3 (Gap-Down Permission Gating implementation)
