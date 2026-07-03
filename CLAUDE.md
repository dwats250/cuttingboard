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
- **What satisfies the Codex cross-review gate (artifact + properties, not
  mechanism).** The Codex cross-review above is satisfied only by a durable
  artifact that has ALL of the following properties — independent of how Codex
  was invoked:
  1. **In-tree + durable:** a committed `docs/prd_history/PRD-NNN.review.codex.md`
     (or the batch's review folder), not an ephemeral comment or external link.
  2. **SHA-pinned:** the artifact names the exact commit it reviewed; a review of
     a superseded commit does not satisfy the gate for later commits.
  3. **Verified-real Codex:** produced by a genuine Codex model, not a routed or
     cheaper substitute model presented under the Codex label.
  4. **Read-only:** the review ran with no repo write access (`codex exec -s
     read-only`; never `-s workspace-write`, which silently re-persists
     `trust_level=trusted` for the cwd and breaks read-only durability).
  5. **Fresh-context:** reviewed from a clean context, not the authoring
     conversation.
  A connector-only, ephemeral PR comment (e.g. a GitHub-app Codex reviewer that
  posts inline comments) does NOT satisfy the gate, however useful: it is not
  in-tree, not durable, and not SHA-pinned. It may inform a review, but the gate
  still requires the artifact above. Defining satisfaction by properties rather
  than by invocation mechanism keeps the gate stable as the available Codex
  surfaces change (CLI egress, GitHub connector, future channels).
- **Bot-review-thread disposition (PRD-228).** Automated PR reviewers - the
  `chatgpt-codex-connector` app and any future connector bot - post inline review
  threads that are advisory INPUT, never gate-satisfying (per the clause above, a
  connector-only ephemeral comment does not satisfy the Codex cross-review gate).
  Disposition of every substantive bot thread is nonetheless mandatory, not
  optional:
  1. **Triage, don't ignore.** Each substantive bot catch is either (a) ACTIONED -
     the fix lands (a bug fix or a lane-appropriate PRD) and the thread is resolved
     in-thread citing the fixing commit SHA / PRD number; or (b) DISMISSED with a
     one-line in-thread reason (out-of-scope, false positive, or already-covered
     with the covering SHA). No substantive thread is left dangling.
  2. **A real defect gets the normal treatment** - PRD before build when
     non-trivial, a mutation-verified red test per the semantic-hardening
     invariants - not patched silently just to clear the thread.
  3. **The thread is not the artifact.** Resolving a bot thread records
     disposition; it never stands in for the Claude review and any durable Codex
     cross-review that PRD's lane / CLASS actually requires (the Codex trigger is
     unchanged - it stays scoped per the gate above, not imposed on every PRD).
  This clause is itself a governance guardrail: a PR that changes it is
  MANUAL-MERGE-ONLY (open and hold for a human merge; do NOT queue `gh pr merge
  --auto`), per the governance carve-out below.
- **Drift check in every review (PRD-186).** Every review artifact records a
  drift check, not just correctness: does the change conflict with a `VISION.md`
  non-goal/principle, and does it leave any `docs/PROJECT_STATE.md` claim stale?
  The `prd-review-claude` skill carries this as a recorded DRIFT CHECK section.
- **Auto-merge via PR after CI (PRD-184).** ALL work - implementation and
  bookkeeping/closeout alike - lands through a pull request: Claude pushes the
  feature branch, opens the PR, and queues `gh pr merge --auto`; `main` branch
  protection holds the merge until the CI `test` check is green. The harness
  blocks direct-to-main pushes (verified during PRD-184 closeout), so there is no
  direct-push path for PRD work - bookkeeping PRs auto-merge the same way. The
  scheduled artifact-publish workflows (cuttingboard / hourly_alert /
  macro_awareness) likewise do NOT push to `main`: they publish the rendered
  dashboard and the accumulating scoreboard state to a dedicated UNPROTECTED
  `publish` branch that GitHub Pages deploys from (PRD-194), so `main` receives
  only CI-gated PR merges. Force-push is denied by repo settings.
- **Drift-review is a post-merge audit under auto-merge (PRD-186).** Because
  auto-merge lands a green PR with no pre-merge human read, VISION/PROJECT_STATE
  drift-review is a post-merge audit - carried by the per-PRD review artifact's
  drift check (above) and the Alignment cadence (below) - not a pre-merge gate.
- **Governance changes are manual-merge-only (PRD-186).** A PR that changes the
  review-gate skill (`prd-review-claude`) or any governance guardrail in this file
  - the auto-merge / review-gate / drift-check policy above, OR the Alignment-cadence
  post-merge audit below - is excluded from auto-merge: open it and hold for a human
  merge - do NOT queue `gh pr merge --auto`. Auto-merge must not land changes to its
  own guardrails without a human read. Enforcement today is this policy
  (agent-honored); the recommended mechanical hardening is CODEOWNERS over a dedicated
  governance file + branch-protection "require Code Owner review" (PRD-186 R4).
- **Surgical edits, scope-locked.** Touch only what the active PRD's `FILES`
  section authorizes (see Operational rules).
- Read-only inspection (git status/diff/log, grep, find, targeted reads, pytest)
  may run without per-command approval. Mutating commands - force-pushes, file
  deletions, dependency changes, edits outside the active PRD's FILES allowlist -
  require explicit approval. **Recon-artifact clause: read-only scopes source,
  contracts, and `main` - not the charge's own deliverable.** A read-only charge
  (recon, audit, charge work) forbids mutation of source, contracts, and `main`;
  it does NOT forbid git operations on the output it was commissioned to produce.
  The findings/recon artifact MAY be committed and pushed to its own non-`main`
  branch - that IS the deliverable, not a seam surrender, and it does not trip
  the read-only clause above. The branch -> `main` merge remains human-held per
  the auto-merge / governance rules above. A charge that wants even the
  deliverable left uncommitted must say so explicitly; silence defaults to
  committable-to-branch.

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

## Semantic-failure hardening (PRD-198)

A check is only worth its green if it verifies *correspondence to reality*, not
the *presence of the right words*. Six invariants close the "passes-on-the-letter,
fails-on-the-meaning" failure class. Each names the incident it generalizes.

1. **Fail-loud, never silent-fallback.** A missing dependency, an unresolvable id,
   or an unreachable source must exit non-zero - never substitute-and-continue.
   *Why:* a step that degrades silently reports a success it never verified.
   *Incident:* `codex --version || echo 'unknown'` and `engine_doctor` WARN->exit 0
   record/emit a non-result as if it were a result.

2. **Assert the resolved, not the requested.** Verify the actual effect - the
   resolved model, the executed test, the CI count - never the declared intent.
   *Why:* intent and effect diverge precisely where it matters.
   *Incident:* provenance recorded the requested `gpt-5-codex` while the served
   model self-reported `gpt-4.1`.

3. **Authoritative source, not proxy.** Every check names and reads its source of
   truth; never a proxy that can diverge from it.
   *Why:* a convenient nearby value is not the value you mean to check.
   *Incident:* parsing the assistant's prose `final-message` as if it were the
   `--json` response-metadata stream.

4. **Every guard ships a red test.** A guard merges only with a negative test
   proving it fails when violated. Banned: `importorskip` on a required dep,
   `WARN`-and-`exit 0`, and any test that cannot fail.
   *Why:* a guard with no failing-case test rots to always-green unnoticed.
   *Incident:* hermetic YAML tests asserted the parser's *logic existed* but never
   that it *worked* against real output - which was, in fact, broken.

5. **Verify where truth is determined.** Achieve environment parity with the gate
   (CI); local/sandbox green is unverified until reproduced where the decision is
   made.
   *Why:* the environment that decides is the only one whose result counts.
   *Incident:* the sandbox suite (2768) differs from CI (2773+); a baseline read
   from the sandbox is wrong.

6. **Pin identities that matter.** Model -> dated snapshot, action -> commit SHA,
   dependency -> declared *and* locked. A movable identity changes behavior with no
   diff.
   *Why:* an alias or floating tag can be re-pointed under you, silently.
   *Incident:* `gpt-5-codex` (an alias, not a snapshot) appears to resolve to a
   fallback; `actions/*` are pinned to movable `@vN` tags; deps are floor-pinned
   (`>=`) with no lockfile.

## Workflow patterns

- **Dashboard regeneration = publish from live data, never hand-overwrite the
  snapshot.** "Regenerate the dashboard" means dispatch the `cuttingboard.yml`
  pipeline (`workflow_dispatch`, `mode: live`), which renders from live data and
  publishes to the `publish` branch (the live Pages site). NEVER overwrite
  `main`'s `ui/dashboard.html` / `ui/index.html` from a sandbox render - the
  in-repo `logs/*` are minimal fallbacks, so a local render degrades the
  committed snapshot and does not touch the live site. The local renderer
  (`dashboard-publish-refresh`) stays a read-only DRY_RUN health check at most.
- Start work on a PRD by reading the PRD file, the related modules, and any prior
  decisions in `docs/DECISIONS.md`.
- When drift is discovered mid-task (code doesn't match docs, undocumented
  dependencies surface), pause and surface the drift before proceeding.
- **Reach for `Explore` (or `general-purpose`) reflexively for code-recon
  questions.** If the question is "where is X computed / called / asserted, and
  what depends on it?" dispatch a subagent before reading files inline. Cost is
  small; the gain is preserved main-context window and parallelism while the
  recon runs. PRD-158 had at least six missed opportunities of this shape.
- **Consult `docs/SCHEMA_MAP.md` and `docs/CALL_SITE_MAP.md` before grepping for
  where a field or symbol is defined or called.** They are the recon cache;
  re-deriving a location they already record is wasted recon. If a map is stale,
  fix it as part of the change rather than working around it.
- **Bookkeeping recon is recon.** Locating a token across `docs/PRD_REGISTRY.md`,
  `docs/prd_index.json`, and `docs/PROJECT_STATE.md` (e.g. during reconciliation
  or closeout) is a recon sweep - dispatch `Explore` rather than running many
  inline greps/reads in the main context.
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

**Post-merge drift audit (PRD-186).** Because auto-merge lands PRDs with no
pre-merge human read, each cadence run is also the post-merge drift audit, with a
defined action - not a label:

- **Trigger:** review every PRD merged since the last audit (the registry rows
  newer than the last audit's DECISIONS entry) against `VISION.md` and
  `docs/PROJECT_STATE.md`.
- **What counts as drift:** a merged change that conflicts with a VISION
  non-goal/principle, leaves a PROJECT_STATE claim stale, or whose review
  artifact skipped the DRIFT CHECK.
- **Remediation (scaled to severity).** *Substantive drift* - a merged change
  that conflicts with a VISION non-goal/principle or leaves a PROJECT_STATE claim
  stale - is remediated by opening a corrective PRD (don't just log it), with its
  number recorded. A *review-artifact process miss* - a merged review that skipped
  the DRIFT CHECK - is remediated in place: append the missing DRIFT CHECK to that
  review and confirm no substantive drift; no corrective PRD is required (forcing
  PRD ceremony for retroactive paperwork is the sprawl this file's PRD-process and
  "cuts before additions" rules guard against). Record each audit in
  `docs/DECISIONS.md` - PRDs reviewed, drift found (or "none"), the remediation
  taken, and the corrective PRD number when applicable.

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
