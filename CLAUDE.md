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
- Use the built-in `Explore` subagent (or `general-purpose`) for codebase
  recon: cross-file consistency checks, scoped reads of long PRDs, "where is
  X used" sweeps. These run locally without an external model call.
- Invoke Codex when the value is a *genuinely independent second model* —
  PRD cross-review, vision review of a proposed PRD, structured code review
  before merge. Not for tasks `Explore` can do.
- Do not invoke Codex or subagents for: simple greps, git operations,
  mechanical edits.
- When two reviews are independent (e.g. Claude vision review + Codex
  cross-review on the same PRD draft), dispatch them in parallel rather than
  serially.
- When a Codex (or subagent) artifact materially drives a decision, link the
  artifact path in the `docs/DECISIONS.md` entry so the audit trail survives.
- Run targeted tests during iteration. Run the full suite once before
  pre-commit review — backgrounded (`run_in_background`) when the suite
  takes long enough to be worth doing other work in parallel.
- Read-only inspection commands (git status/diff/log, grep, find, targeted
  reads, pytest) may execute without per-command approval. Mutating commands —
  git pushes, file deletions, dependency changes, edits outside the active
  PRD's FILES allowlist — require explicit approval.

### Alignment cadence

Every 4-6 weeks, or after any phase boundary, run a scoped alignment
check against VISION.md. Three questions:

1. Has any new prediction logic entered the codebase?
2. Has any new sidecar been added without a documented consumer
   (decision-feeding) or without observational purpose (observation)?
3. Has any new module been added that doesn't serve at least one of
   VISION.md's four questions (what environment, what matters today, is
   this tradable, what invalidates)?

If all three answers are "no," document the check in
`docs/DECISIONS.md` and move on. If any answer is "yes," scope a full
alignment audit. Drift is a function of time, not a bug — these checks
make it visible early.

### PRD-author disciplines

Three checks every PRD author should run before submitting for review.
Surfaced from the PRD-150 review arc (2026-05-22); see
`docs/DECISIONS.md` and `audits/recon-2026-05-22/prd-150-vision-review.md`
for context.

- **Dead-branch enumeration.** When retiring a code path (e.g. a
  short-circuit, a status value, a function), enumerate every
  downstream reader of the retired surface. For each reader, either
  remove it in the same PRD or document it as retained-with-reason
  ("dead branch by design, kept for shape stability"). A retired
  surface with un-enumerated readers is hidden drift.
- **Downstream-consumer audit.** For any new emission, contract field,
  status value, rejection stage, or artifact path: identify every
  module that reads it and verify the change is compatible. Postmarket
  reports, dashboard renderers, audit writers, and notification
  formatters are common consumers. A PRD that adds an emission without
  updating its consumers leaks under-counting or silent drift.
- **Realizability check.** For any new output channel (rejection stage,
  classification tier, sidecar field, status literal), verify there
  exists at least one realistic input path under current routing that
  produces non-trivial output. A channel whose every emission case is
  pre-empted by an upstream channel is dead code with extra steps.
  If a channel is defensive-against-future-routing, declare it as
  such — don't claim it's currently active.

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
