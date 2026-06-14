# CLAUDE.md

The operating model for Cuttingboard: who does what, how work is reviewed and
committed, and the disciplines that keep the codebase aligned with `VISION.md`.

## Roles

- **Dustin** makes final decisions. The system serves his trading; he is the
  human at every seam.
- **Claude (project lead, in chat)** drafts PRDs and reviews them against VISION
  principles, flags drift, and holds architectural direction with Dustin.
- **Claude Code (this agent)** is the primary implementation agent: PRD
  construction, code implementation, test maintenance, and architectural
  decisions within PRD scope. Invokes Codex for specialist tasks.
- **Codex** is a specialist invoked by Claude Code for a genuinely independent
  second opinion - cross-referencing, structured analysis, code review. It does
  not drive architectural direction.

## Canonical sources

Repo state lives in source-of-truth documents. Reference these; do not duplicate
them.

- `VISION.md` - what Cuttingboard is, is not, and is becoming
- `docs/PROJECT_STATE.md` - current state: active work, test baseline, known debt
- `docs/PRD_REGISTRY.md` - work in flight and completed
- `docs/DECISIONS.md` - meaningful decisions and rationale
- `README.md` - outsider's entry point
- `docs/architecture.md`, `docs/PRD_PROCESS.md`, `docs/sidecar_doctrine.md` -
  structural references
- `docs/CLAUDE_HOOKS.md` - the repo's Claude Code hooks (file protection, test
  gate, session snapshot) and their state files

Decisions that meaningfully change direction are recorded in `docs/DECISIONS.md`
with date and rationale - short notes, not ceremony.

## Review and commit discipline

- **Nothing lands without review.** Implementations are reviewed against the PRD
  before they are considered done.
- **HIGH-RISK review gate.** A HIGH-RISK lane PRD (per `docs/PRD_PROCESS.md`)
  requires independent review before merge: a Claude review artifact, plus a
  Codex cross-review for contract / decision-surface changes. The lane is
  declared in the PRD header; STANDARD and MICRO lanes are lighter.
- **Auto-merge via PR after CI (PRD-184).** ALL work - implementation and
  bookkeeping/closeout alike - lands through a pull request: Claude pushes the
  feature branch, opens the PR, and queues `gh pr merge --auto`; `main` branch
  protection holds the merge until the CI `test` check is green. The harness
  blocks direct-to-main pushes (verified during PRD-184 closeout), so there is no
  direct-push path - bookkeeping PRs auto-merge the same way. Force-push is denied
  by repo settings.
- **Surgical edits, scope-locked.** Touch only what the active PRD's `FILES`
  section authorizes (see Operational rules).
- Read-only inspection (git status/diff/log, grep, find, targeted reads, pytest)
  may run without per-command approval. Mutating commands - force-pushes, file
  deletions, dependency changes, edits outside the active PRD's FILES allowlist -
  require explicit approval.

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
  change requires touching a file not listed, stop and amend the PRD (or open a
  new one) before editing.
- **Pre-implementation grep sweep.** Before declaring a PRD's FILES set for any
  change that deletes, renames, or translates a rendered field / contract key /
  enum value, grep all of `tests/` for the affected token. Add every test file
  that asserts on the token to FILES in the initial PRD, not as reactive
  amendments after the suite breaks. PRD-158 hit this loop three times before
  adopting the rule.
- **PRD file lands at Stage 0.** The first commit for any PRD is the PRD-NNN.md
  scaffold plus the IN PROGRESS registry row plus the `prd_index.json` entry -
  before any implementation commit. `scripts/prd_open.sh` (PRD-159) scaffolds all
  three. Authoring a PRD in chat and filing it only at closeout produces
  sequencing-gate noise and forces reconstruction from chat history.

## Workflow patterns

- Start work on a PRD by reading the PRD file, the related modules, and any prior
  decisions in `docs/DECISIONS.md`.
- When drift is discovered mid-task (code doesn't match docs, undocumented
  dependencies surface), pause and surface the drift before proceeding.
- **Reach for `Explore` (or `general-purpose`) reflexively for code-recon
  questions.** If the question is "where is X computed / called / asserted, and
  what depends on it?" dispatch a subagent before reading files inline. Cost is
  small; the gain is preserved main-context window and parallelism while the
  recon runs. PRD-158 had at least six missed opportunities of this shape.
- **Use the task list upfront for any work with >=3 distinct stages.** Update
  status as each stage starts and completes; it keeps progress visible and turns
  each report into a delta rather than a full re-statement.
- **Sequencing-gate fires are actionable, not boilerplate.** If the
  `UserPromptSubmit` PRD gate (`.claude/hooks/prd_eval.sh`) fires repeatedly for
  the same out-of-order PRD, close the underlying registry inconsistency
  (typically a 10-minute bookkeeping commit) rather than re-stating the skip
  reason on every prompt. Repetition is a signal that closeout is overdue.
- Invoke Codex when the value is a genuinely independent second model - PRD
  cross-review, vision review of a proposed PRD, structured code review before
  merge. Not for tasks `Explore` can do.
- All Codex review invocations run sandboxed read-only:
  `codex exec -s read-only - < prompt` (prompt via stdin, verdict from stdout).
  The review artifact (`docs/prd_history/PRD-NNN.review.codex.md`) is written by
  Claude Code from captured stdout; Codex never writes into the repo tree.
  (Verified 2026-06-10; see `docs/DECISIONS.md`.)
- Do not invoke Codex or subagents for simple greps, git operations, or
  mechanical edits.
- When two reviews are independent (e.g. Claude vision review + Codex cross-review
  on the same draft), dispatch them in parallel.
- When a Codex or subagent artifact materially drives a decision, link the
  artifact path in the `docs/DECISIONS.md` entry so the audit trail survives.
- Run targeted tests during iteration. Run the full suite once before pre-commit
  review - backgrounded when it is long enough to do other work in parallel.

### Alignment cadence

Every 4-6 weeks, or after any phase boundary, run a scoped alignment check
against `VISION.md`. Three questions:

1. Has any new prediction logic entered the codebase?
2. Has any new sidecar been added without a documented consumer
   (decision-feeding) or without observational purpose?
3. Has any new module been added that doesn't serve at least one of VISION's four
   questions (what environment, what matters today, is this tradable, what
   invalidates)?

If all three answers are "no," document the check in `docs/DECISIONS.md` and move
on. If any answer is "yes," scope a full alignment audit. Drift is a function of
time, not a bug - these checks make it visible early.

### PRD-author disciplines

Four checks every PRD author should run before submitting for review. The first
three surfaced from the PRD-150 review arc (2026-05-22); see `docs/DECISIONS.md`
and `audits/recon-2026-05-22/prd-150-vision-review.md` for context. The fourth
surfaced from the sub-agent flow audit (2026-06-10).

- **Dead-branch enumeration.** When retiring a code path (a short-circuit, a
  status value, a function), enumerate every downstream reader of the retired
  surface. For each reader, either remove it in the same PRD or document it as
  retained-with-reason ("dead branch by design, kept for shape stability"). A
  retired surface with un-enumerated readers is hidden drift.
- **Downstream-consumer audit.** For any new emission, contract field, status
  value, rejection stage, or artifact path: identify every module that reads it
  and verify the change is compatible. Postmarket reports, dashboard renderers,
  audit writers, and notification formatters are common consumers. A PRD that
  adds an emission without updating its consumers leaks under-counting or silent
  drift.
- **Realizability check.** For any new output channel (rejection stage,
  classification tier, sidecar field, status literal), verify there exists at
  least one realistic input path under current routing that produces non-trivial
  output. A channel whose every emission case is pre-empted by an upstream
  channel is dead code with extra steps. If a channel is
  defensive-against-future-routing, declare it as such - don't claim it is
  currently active.
- **Sub-agent sweep re-verification.** Any sub-agent grep/recon sweep whose
  output feeds a PRD FILES boundary or a "nothing else reads/calls this" claim
  must be re-verified before the claim counts: the main agent re-runs the single
  decisive `rg` itself. One command; it closes the false-all-clear path where an
  incomplete delegated sweep manufactures a clean result.

## Anti-patterns

- Do not draft PRDs for features that violate `VISION.md` non-goals without
  explicit override from Dustin.
- Do not refactor the `runtime/` package opportunistically; it is acknowledged
  debt and refactors require their own PRD.
- Do not add documentation that duplicates content in canonical sources;
  reference instead.
- Do not silently expand a PRD's FILES set mid-implementation. Amend the PRD
  first.
- Do not commit generated artifacts (`logs/*`, `reports/*`) outside the
  workflow-driven force-add allowlist.
