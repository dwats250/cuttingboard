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
- **Codex** (or any second model) is an instrument Dustin may commission for a
  genuinely independent second opinion - cross-referencing, structured
  analysis, code review (PRD-242). It is never a standing gate requirement and
  does not drive architectural direction.

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
- `docs/CLAUDE_HOOKS.md` - the repo's Claude Code hooks (file protection,
  PRD registry-gap check, canonical-read guard) and their state files

Decisions that meaningfully change direction are recorded in `docs/DECISIONS.md`
with date and rationale - short notes, not ceremony.

## Review and commit discipline

- **Nothing lands without review.** Implementations are reviewed against the PRD
  before they are considered done.
- **HIGH-RISK review gate (PRD-242).** A HIGH-RISK lane PRD (per
  `docs/PRD_PROCESS.md`) requires before merge: a fresh-context Claude review
  artifact, plus Dustin's manual merge as the human gate. A second-model
  review (Codex or any other independent model) is an INSTRUMENT Dustin may
  commission for any PRD — never a standing requirement owed by a lane. The
  lane is declared in the PRD header; STANDARD and MICRO lanes are lighter.
- **Second-model disposition (PRD-242: write the sentence).** Every COMPLETE
  HIGH-RISK PRD from PRD-242 onward carries, in-tree, EITHER a commissioned
  second-model artifact OR this exact disposition line in its PRD doc:
  `SECOND-MODEL: instrument not commissioned, merging on Claude-review + human judgment.`
  The waiver is a positive act written by the merger, never a silence —
  `tools/validate_prd_registry.py` fails the CI `test` check when a HIGH-RISK
  close carries neither (this closes the gate-skip class: PRD-240 merged
  while its own review said the second leg was still owed). When a
  second-model review IS commissioned, the artifact must have ALL of these
  properties:
  1. **In-tree + durable:** a committed `docs/prd_history/PRD-NNN.review.<model>.md`
     (or the batch's review folder), not an ephemeral comment or external link.
  2. **SHA-pinned:** the artifact names the exact commit it reviewed; a review of
     a superseded commit does not count for later commits.
  3. **Read-only:** the review ran with no repo write access (for Codex:
     `codex exec -s read-only`; never `-s workspace-write`, which silently
     re-persists `trust_level=trusted` for the cwd and breaks read-only
     durability).
  4. **Fresh-context:** reviewed from a clean context, not the authoring
     conversation.
  A connector-only, ephemeral PR comment is NOT a second-model artifact: not
  in-tree, not durable, not SHA-pinned. (History: PRD-197/207/212 built and
  repaired a mandatory-Codex apparatus that caught one real incident; PRD-230
  retired its CI leg; every HIGH-RISK close 2026-07-03..05 then ran on
  waiver-by-merge, so the mandatory framing was fiction. PRD-242 made the
  instrument framing official and the waiver explicit. DECISIONS
  2026-06-26..07-05.)
- **Bot-review-thread disposition (PRD-228).** Automated PR reviewers - the
  `chatgpt-codex-connector` app and any future connector bot - post inline review
  threads that are advisory INPUT, never gate-satisfying (per the clause above, a
  connector-only ephemeral comment is not a second-model artifact).
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
     disposition; it never stands in for the fresh-context Claude review the
     lane requires, nor for the second-model disposition (artifact-or-sentence,
     PRD-242) above.
  This clause is itself a governance guardrail: a PR that changes it is
  MANUAL-MERGE-ONLY (open and hold for a human merge; do NOT queue `gh pr merge
  --auto`), per the governance carve-out below.
- **Drift check in every review (PRD-186).** Every review artifact records a
  drift check, not just correctness: does the change conflict with a `VISION.md`
  non-goal/principle, and does it leave any `docs/PROJECT_STATE.md` claim stale?
  The `prd-review-claude` skill carries this as a recorded DRIFT CHECK section.
- **Auto-merge via PR after CI (PRD-184).** ALL work lands through a pull
  request: Claude pushes the feature branch, opens the PR, and queues
  `gh pr merge --auto`; `main` branch protection holds the merge until the CI
  `test` check is green. The harness blocks direct-to-main pushes (verified
  during PRD-184 closeout), so there is no direct-push path for PRD work.
  Closeout bookkeeping folds into the implementation PR (PRD-229 same-PR
  closeout; the separate closeout PR is retired - residual bookkeeping fixes
  auto-merge as their own PR). The
  scheduled artifact-publish workflows (cuttingboard / hourly_alert /
  macro_awareness) likewise do NOT push to `main`: they publish the rendered
  dashboard and the accumulating scoreboard state to a dedicated UNPROTECTED
  `publish` branch that GitHub Pages deploys from (PRD-194), so `main` receives
  only CI-gated PR merges. Force-push is denied by repo settings.
- **Drift-review is a post-merge audit under auto-merge (PRD-186).** Because
  auto-merge lands a green PR with no pre-merge human read, VISION/PROJECT_STATE
  drift-review is a post-merge audit - carried by the per-PRD review artifact's
  drift check (above) and the Alignment check (below) - not a pre-merge gate.
- **Governance changes are manual-merge-only (PRD-186).** A PR that changes the
  review-gate skill (`prd-review-claude`) or any governance guardrail in this file
  - the auto-merge / review-gate / drift-check policy above, OR the Alignment-check
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
- **Ceremony tiering (PRD-229).** Cosmetic-only changes (ui copy / CSS /
  layout; comment- or docstring-only edits) ride MICRO with a <=10-line note
  and batch into at most one weekly polish PRD; closeout bookkeeping lands in
  the same PR as the implementation. Owner:
  `docs/PRD_PROCESS.md` (Cosmetic Carve-Out; Same-PR Closeout) - reference,
  don't restate.
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
- **A registry-gap fire is actionable, not boilerplate.** If the
  `UserPromptSubmit` hook (`.claude/hooks/prd_eval.sh`, registry-gap check
  only since PRD-243) flags an unregistered prd_history file, add the row —
  a 10-minute bookkeeping commit — rather than working past the warning.
- Invoke Codex only when Dustin commissions a second-model review (PRD-242),
  and the value is a genuinely independent second model - PRD cross-review,
  vision review of a proposed PRD, structured code review before merge. Not
  for tasks `Explore` can do.
- All Codex review invocations run sandboxed read-only:
  `codex exec -s read-only - < prompt` (prompt via stdin, verdict from stdout).
  The review artifact (`docs/prd_history/PRD-NNN.review.codex.md`) is written by
  Claude Code from captured stdout; Codex never writes into the repo tree.
  (Verified 2026-06-10; see `docs/DECISIONS.md`.)
- Do not invoke Codex or subagents for simple greps, git operations, or
  mechanical edits.
- When two reviews are independent (e.g. Claude vision review + Codex cross-review
  on the same draft), dispatch them in parallel (owner:
  `docs/PRD_PROCESS.md` § Review Dispatch).
- When a Codex or subagent artifact materially drives a decision, link the
  artifact path in the `docs/DECISIONS.md` entry so the audit trail survives.
- Run targeted tests during iteration. Run the full suite once before pre-commit
  review - backgrounded when it is long enough to do other work in parallel.

### Alignment check (PRD-230: phase-boundary diff-read)

Trigger: a phase boundary (a wave/batch of related PRDs closes, or a
direction change lands) - not the calendar. Five scheduled cadence runs
found zero drift; the ceremony detected nothing, so the ceremony is retired
and the read remains.

The check is a 15-minute read of the diff since the last check
(`git log --oneline <last-audit-sha>..main` + the registry rows it maps
to), answering four questions:

1. Any new prediction logic? (VISION non-goal)
2. Any new sidecar without a documented consumer or observational purpose?
3. Any new module serving none of VISION's four questions?
4. Post-merge drift audit (PRD-186, folded in): does any merged PRD
   conflict with a VISION principle, leave a PROJECT_STATE claim stale, or
   carry a review artifact that skipped its DRIFT CHECK?

Record one DECISIONS.md line per run (PRDs covered; findings or "none").
Remediation unchanged: substantive drift -> corrective PRD (number
recorded); a review-artifact DRIFT-CHECK miss -> append the missing check
in place, no PRD ceremony for retroactive paperwork.

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
- Do not let session recon notes accumulate in `audits/` (PRD-230): a session
  note is working scratch - delete it once the next session confirms nothing
  was lost. Durable findings belong in `docs/DECISIONS.md` or a PRD.
