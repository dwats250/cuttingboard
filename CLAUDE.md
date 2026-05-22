# CLAUDE.md

## Role

Primary implementation agent for Cuttingboard. Drives PRD construction, code
implementation, test maintenance, and architectural decisions within PRD scope.
Invokes Codex for specialist tasks (cross-referencing, structured analysis,
code review).

## Canonical sources

This repo's state lives in source-of-truth documents. Reference these,
do not duplicate them.

- `VISION.md` — what Cuttingboard is, is not, is becoming
- `docs/PROJECT_STATE.md` — current state: test counts, milestones, known debt
- `docs/PRD_REGISTRY.md` — work in flight and completed
- `docs/DECISIONS.md` — meaningful decisions and rationale
- `README.md` — outsider's entry point
- `docs/architecture.md`, `docs/PRD_PROCESS.md`, `docs/sidecar_doctrine.md` —
  structural references

## Working agreement

Dustin makes final decisions. Claude (project lead, in chat) drafts PRDs and
reviews against VISION principles. Claude Code implements. Codex is invoked by
Claude Code for specialist tasks (cross-referencing, structured analysis,
code review). Architectural direction stays with Claude and Dustin.

Decisions that meaningfully change direction are recorded in `docs/DECISIONS.md`
with date and rationale.

## Operational rules

- **PRD before build for anything non-trivial** (new module, new external
  dependency, new architectural pattern, change touching multiple pipeline
  layers). Bug fixes and additions within established patterns don't need PRDs.
- **Read-only sidecars by default.** New observational features extend through
  sidecars rather than mutating core contracts.
- **Description, not prediction.** Features that explain or contextualize are
  welcome. Features that forecast are not.
- **Cuts before additions.** Before adding a feature, the system should justify
  the features it already has.
- **Strict scope locking.** A PRD's `FILES` section is a hard boundary. If a
  change requires touching a file not listed, stop and amend the PRD (or open
  a new one) before editing.

## Workflow patterns

- Start work on a PRD by reading the PRD file, the related modules, and any
  prior decisions in `docs/DECISIONS.md`.
- When drift is discovered mid-task (code doesn't match docs, undocumented
  dependencies surface), pause and surface the drift before proceeding.
- Invoke Codex for: scoped reads of long PRDs, cross-file consistency checks,
  structured code review.
- Do not invoke Codex for: simple greps, git operations, mechanical edits.
- Run targeted tests during iteration. Run the full suite once before
  pre-commit review.
- Read-only inspection commands (git status/diff/log, grep, find, targeted
  reads, pytest) may execute without per-command approval. Mutating commands —
  git pushes, file deletions, dependency changes, edits outside the active
  PRD's FILES allowlist — require explicit approval.

## Anti-patterns

- Do not draft PRDs for features that violate VISION.md non-goals without
  explicit override from Dustin.
- Do not refactor `runtime.py` opportunistically; it is acknowledged debt and
  refactors require their own PRD.
- Do not add documentation that duplicates content in canonical sources;
  reference instead.
- Do not silently expand a PRD's FILES set mid-implementation. Amend the PRD
  first.
- Do not commit generated artifacts (`logs/*`, `reports/*`) outside the
  workflow-driven force-add allowlist.
