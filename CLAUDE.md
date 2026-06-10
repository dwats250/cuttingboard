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
- **Pre-implementation grep sweep.** Before declaring a PRD's FILES set for any
  change that deletes, renames, or translates a rendered field / contract key /
  enum value, grep all of `tests/` for the affected token. Add every test file
  that asserts on the token to FILES in the initial PRD, not as reactive
  amendments after the test suite breaks. PRD-158 hit this loop three times
  before adopting the rule.
- **PRD file lands at Stage 0.** For any PRD, the first commit is the
  PRD-NNN.md scaffold plus the IN PROGRESS registry row plus the prd_index.json
  entry — *before* any implementation commit. Authoring a PRD in chat and only
  filing it at closeout is what produces sequencing-gate noise and forces
  reconstruction of the spec from chat history. (See `scripts/prd_open.sh` once
  it exists; until then, do the three edits by hand.)

## Workflow patterns

- Start work on a PRD by reading the PRD file, the related modules, and any
  prior decisions in `docs/DECISIONS.md`.
- When drift is discovered mid-task (code doesn't match docs, undocumented
  dependencies surface), pause and surface the drift before proceeding.
- **Reach for `Explore` (or `general-purpose`) reflexively for code-recon
  questions.** If the question is "where is X computed/called/asserted, and
  what depends on it?" — dispatch a subagent before reading files inline.
  Cost is small; the gain is preserved main-context window and parallelism
  while the recon runs. Going inline for this class of question burns context
  on detail the user does not need to see. PRD-158 had at least six missed
  opportunities of this shape.
- **Use `TaskCreate` upfront for any work with ≥3 distinct stages.** Update
  status as each stage starts/completes. Tracks progress visibly and reduces
  the size of per-step reports to a delta-against-tasks rather than a full
  re-statement.
- **Sequencing-gate fires are actionable, not boilerplate.** If the
  `UserPromptSubmit` sequencing-gate hook fires repeatedly for the same
  out-of-order PRD, the right response is to close the underlying registry
  inconsistency (typically a 10-minute bookkeeping commit), not to re-state
  the skip reason on every prompt. Repeating the skip reason is a signal that
  closeout is overdue.
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
   this tradable, what invalidates) AND isn't an explicitly-named
   VISION.md phase deliverable (e.g. Phase 2 trade evaluation)?

If all three answers are "no," document the check in
`docs/DECISIONS.md` and move on. If any answer is "yes," scope a full
alignment audit. Drift is a function of time, not a bug — these checks
make it visible early.

### PRD-author disciplines

Four checks every PRD author should run before submitting for review.
The first three surfaced from the PRD-150 review arc (2026-05-22); see
`docs/DECISIONS.md` and `audits/recon-2026-05-22/prd-150-vision-review.md`
for context. The fourth surfaced from the sub-agent flow audit
(2026-06-10).

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
- **Sub-agent sweep re-verification.** Any sub-agent grep/recon sweep
  whose output feeds a PRD FILES boundary or a "nothing else
  reads/calls this" claim must be re-verified before the claim counts:
  the main agent re-runs the single decisive `rg` itself. One command;
  it closes the false-all-clear path where an incomplete delegated
  sweep manufactures a clean result.

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
