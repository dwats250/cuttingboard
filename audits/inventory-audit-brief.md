# Cuttingboard Inventory Audit Brief

**For:** Claude Code, executing against the cuttingboard repo on `asher`
**Output location:** `audits/inventory-YYYY-MM-DD/` (create this directory)
**Mode:** Read-only. Do not modify, delete, or refactor any code during this audit. Produce reports only.

---

## Context

Read `VISION.md` in the repo root before beginning. It defines what Cuttingboard is, what it is not, and the principles the system should reflect. This audit serves Phase 1 of that document.

The purpose of this audit is **delineation, not judgment**. Produce an accurate, complete map of the codebase as it exists today, with mechanical flags for likely dead code, drift from PRDs, and architectural concerns. Final decisions on what to cut, refactor, or preserve will be made by Dustin in a subsequent review session, not by you in this audit.

Three modules are already scheduled for deletion and should be flagged as such without deep analysis:
- Polygon integration (any module, config, env var, or reference)
- ntfy alerts (topic `cuttingboard86`, any dispatch logic, env vars)
- PRD 142 and any code that exists solely to serve it

Inventory these but mark them `SCHEDULED-FOR-DELETION`. Do not spend analytical depth on them.

---

## Deliverables

Produce the following files in `audits/inventory-YYYY-MM-DD/`:

### 1. `00-summary.md`

A short executive summary (1-2 pages max) covering:
- Repo size: total files, total LOC by language, number of modules, number of tests
- Headline findings: most significant dead code candidates, most significant drift, anything surprising
- Counts: how many modules appear orphaned, how many PRDs appear stale, how many TODOs/FIXMEs
- Open questions for Dustin's review

This file is the entry point. Write it last, after the other files are complete. Assume Dustin reads this first and only drills into other files for items flagged here.

### 2. `01-structure.md`

The repo's actual structure as it exists:
- Full directory tree, excluding `.git`, `__pycache__`, virtual environments, build artifacts, caches
- For each top-level directory: one-sentence description of its purpose based on contents
- For each Python module under `cuttingboard/`: one-line description of what it does, derived from docstrings or code inspection
- Map of which modules belong to which pipeline layer (L1 Ingestion through L10 Audit). Flag any module that doesn't clearly belong to a layer or appears to span layers.

### 3. `02-dependencies.md`

Module dependency analysis:
- Internal dependency graph: which modules import which (text format is fine, no need for visualization)
- External dependencies: contents of `requirements.txt` / `pyproject.toml` with notes on which are actually imported anywhere in the codebase
- Flag any declared dependency not imported by any module (candidate for removal)
- Flag any imported module that isn't a declared dependency
- Flag circular imports if any exist

### 4. `03-dead-code.md`

Candidates for removal:
- Modules with no inbound imports from anywhere except tests
- Modules with no inbound imports at all
- Functions/classes that are defined but never called (best-effort; static analysis limits acknowledged)
- Config options never referenced
- Environment variables declared but never read
- Test files for modules that no longer exist
- Scheduled-for-deletion items (Polygon, ntfy, PRD 142 code) listed separately with `SCHEDULED-FOR-DELETION` tag

For each candidate, include: file path, last-modified date (from git), brief note on why it's flagged. Do not delete. Flag only.

### 5. `04-prd-drift.md`

PRD-to-code reconciliation:
- List every PRD in the repo (or wherever PRDs live)
- For each PRD, classify as: `COMPLETE-AND-MATCHES`, `COMPLETE-BUT-DRIFTED` (code exists but differs from PRD), `IN-FLIGHT`, `STALLED`, `APPEARS-ABANDONED`, or `SCHEDULED-FOR-KILL`
- For `COMPLETE-BUT-DRIFTED`: brief note on what differs
- For `APPEARS-ABANDONED`: brief note on why (no recent commits referencing it, no code matching its specs, etc.)
- Flag any code that appears to implement a feature with no corresponding PRD (reverse drift)

### 6. `05-architectural-flags.md`

Items that may violate principles declared in `VISION.md`. Flag, don't judge:
- Sidecars that appear to mutate state rather than being read-only
- Any code that performs prediction, forecasting, or signal generation in the institutional sense (vs. observation/contextualization)
- Any ML or backtesting code or imports
- Multi-agent orchestration patterns
- External execution interfaces
- Modules whose existence isn't justified by any of the four questions Cuttingboard answers (what environment, what matters, is it tradable, what invalidates)
- "Temporary" patches that have been in place for more than 30 days

For each flag, cite the specific VISION.md principle it may violate. Be conservative — flag liberally, let Dustin and Claude (project lead) judge.

### 7. `06-hygiene.md`

Repo cleanliness check:
- TODOs and FIXMEs across the codebase (file, line, content)
- Files with no docstrings or module headers
- Branches in `.git` that appear stale (no commits in 60+ days)
- Files in unusual locations (Python files outside `cuttingboard/`, configs in unexpected places, etc.)
- Anything in `.gitignore` that's been accidentally committed
- Secrets check: scan for patterns suggesting committed API keys, tokens, or credentials. Flag any finding immediately and prominently.

---

## Constraints

- **Read-only.** Make no modifications to any file outside `audits/inventory-YYYY-MM-DD/`. No refactors, no deletions, no "while I'm here" cleanups.
- **No new dependencies.** Use only tools already available in the repo's environment plus standard Unix utilities (grep, find, git, etc.).
- **No interpretation beyond what's asked.** This audit produces an inventory. Recommendations and decisions come later in a separate review session.
- **If something is ambiguous, flag it as ambiguous.** Do not guess. "Unable to determine" is a valid finding.
- **Honesty about limits.** Static analysis can't catch dynamic imports, reflection, or runtime-only references. Where your analysis has known blind spots, state them in `00-summary.md`.

## Tone

Plain, factual, no hedging beyond what's warranted by actual uncertainty. No marketing language. No optimistic framing. This audit serves a project realignment that depends on accurate information; flattery or softening makes the audit less useful.

## When complete

Commit the `audits/inventory-YYYY-MM-DD/` directory to the repo. Notify Dustin that the audit is ready for review. Do not begin any cleanup work until Dustin and Claude (project lead) have reviewed the audit and produced explicit decisions on flagged items.
