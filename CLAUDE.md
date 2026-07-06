# CLAUDE.md

The operating model for Cuttingboard: roles, merge and review gates, scope
discipline. Every rule here is binding. Rationale and history live in the
canonical docs below — this file states rules and names owners; it does not
retell origin stories.

## Roles

- **Dustin** makes final decisions. The system serves his trading; he is the
  human at every seam.
- **Claude (project lead, in chat)** drafts and reviews PRDs against VISION
  principles, flags drift, holds architectural direction with Dustin.
- **Claude Code (this agent)** is the primary implementation agent: PRD
  construction, implementation, test maintenance, architectural decisions
  within PRD scope. Invokes Codex for specialist tasks.
- **Codex (or any second model)** is an instrument Dustin may commission for a
  genuinely independent second opinion (PRD-242). Never a standing gate
  requirement; never drives architectural direction.

## Canonical sources

Reference these; do not duplicate them.

- `VISION.md` — what Cuttingboard is, is not, and is becoming. Its Operating
  principles (description-not-prediction, read-only-sidecars-by-default,
  cuts-before-additions, the-system-serves-the-trader, docs-match-code) bind
  every change; apply them from VISION directly.
- `docs/PROJECT_STATE.md` — current state: active work, test baseline, known debt
- `docs/PRD_REGISTRY.md` — work in flight and completed
- `docs/DECISIONS.md` — meaningful decisions and rationale. A decision that
  changes direction gets a dated entry — short notes, not ceremony.
- `README.md` — outsider's entry point
- `docs/PRD_PROCESS.md` — PRD lifecycle, CLASS/LANE matrices, Second-Model
  Disposition spec, Same-PR Closeout, Cosmetic Carve-Out, Review Dispatch
- `docs/architecture.md`, `docs/sidecar_doctrine.md` — structural references
- `docs/CLAUDE_HOOKS.md` — the repo's hooks (file protection, PRD registry-gap
  check, canonical-read guard) and their state files
- `docs/AGENT_WORKFLOW.md` — protected-file set consumed by the PRD skills

## How work lands

- **Everything lands through a PR (PRD-184).** Push the feature branch, open
  the PR, queue `gh pr merge --auto`; `main` branch protection holds the merge
  until the CI `test` check is green. There is no direct-to-main push path;
  force-push is denied by repo settings.
- **Closeout rides the implementation PR** (PRD-229 Same-PR Closeout; owner:
  `docs/PRD_PROCESS.md`). Residual bookkeeping fixes auto-merge as their own
  PR.
- **Scheduled publish workflows never push to `main` (PRD-194).** They publish
  the rendered dashboard and scoreboard state to the dedicated UNPROTECTED
  `publish` branch that GitHub Pages deploys from; `main` receives only
  CI-gated PR merges.
- **Governance changes are MANUAL-MERGE-ONLY (PRD-186).** A PR that changes
  the review-gate skill (`prd-review-claude`) or any governance guardrail in
  this file — the landing/auto-merge policy, the review gates, the
  second-model or bot-thread disposition, the drift check, the Alignment
  check — is opened and HELD for a human merge. Do NOT queue
  `gh pr merge --auto`: auto-merge must not land changes to its own guardrails.

## Review gates

- **Nothing lands without review.** Implementations are reviewed against the
  PRD before they are considered done.
- **Lane declares ceremony.** The PRD header declares LANE (MICRO / STANDARD /
  HIGH-RISK); eligibility and review intensity: `docs/PRD_PROCESS.md`.
- **HIGH-RISK gate (PRD-242).** Before merge: a fresh-context Claude review
  artifact, plus Dustin's manual merge as the human gate.
- **Second-model disposition (PRD-242): artifact or the sentence.** Every
  COMPLETE HIGH-RISK PRD from PRD-242 onward carries, in-tree, EITHER a
  commissioned second-model artifact OR this exact line in its PRD doc:
  `SECOND-MODEL: instrument not commissioned, merging on Claude-review + human judgment.`
  The waiver is a positive act written by the merger, never a silence —
  `tools/validate_prd_registry.py` fails the CI `test` check when a HIGH-RISK
  close carries neither. A commissioned artifact must have ALL of:
  1. **In-tree + durable:** a committed
     `docs/prd_history/PRD-NNN.review.<model>.md` (or the batch's review
     folder) — not an ephemeral comment or external link.
  2. **SHA-pinned:** names the exact commit reviewed; a review of a superseded
     commit does not count for later commits.
  3. **Read-only:** ran with no repo write access (for Codex:
     `codex exec -s read-only`; never `-s workspace-write`, which silently
     re-persists `trust_level=trusted` for the cwd).
  4. **Fresh-context:** reviewed from a clean context, not the authoring
     conversation.
  A connector-only, ephemeral PR comment is NOT a second-model artifact.
  (Arc history: `docs/DECISIONS.md` 2026-06-26..07-05.)
- **Bot-review threads (PRD-228): triage, never gate.** Threads from automated
  PR reviewers (`chatgpt-codex-connector` and any future connector bot) are
  advisory INPUT, never gate-satisfying. Disposition of every substantive
  thread is mandatory: (a) ACTIONED — the fix lands (a bug fix or a
  lane-appropriate PRD) and the thread is resolved in-thread citing the fixing
  commit SHA / PRD number; or (b) DISMISSED with a one-line in-thread reason
  (out-of-scope, false positive, or already-covered with the covering SHA).
  No substantive thread is left dangling. A real defect gets the normal
  treatment — PRD before build when non-trivial, a mutation-verified red test
  per the hardening invariants — never patched silently to clear the thread.
  The thread is not the artifact: resolving it never stands in for the lane's
  fresh-context Claude review or the second-model disposition. This clause is
  itself a governance guardrail (manual-merge-only, per above).
- **Drift check in every review (PRD-186).** Every review artifact records a
  DRIFT CHECK, not just correctness: does the change conflict with a
  `VISION.md` non-goal/principle, and does it leave any
  `docs/PROJECT_STATE.md` claim stale? Carried by the `prd-review-claude`
  skill.
- **Drift review is a post-merge audit under auto-merge (PRD-186)** — the
  per-PRD DRIFT CHECK plus the Alignment check below — not a pre-merge gate.

## Scope and approvals

- **Strict scope locking.** A PRD's `FILES` section is a hard boundary; touch
  only what it authorizes. If a change needs a file not listed, STOP and amend
  the PRD (or open a new one) before editing — never expand FILES silently
  mid-implementation.
- **Pre-implementation grep sweep (PRD-158).** Before declaring FILES for any
  change that deletes, renames, or translates a rendered field / contract key
  / enum value, grep all of `tests/` for the affected token and add every
  asserting test file to FILES in the initial PRD, not as reactive amendments.
- **PRD file lands at Stage 0 (PRD-159).** The first commit for any PRD is the
  `PRD-NNN.md` scaffold + the IN PROGRESS registry row + the `prd_index.json`
  entry — before any implementation commit. `scripts/prd_open.sh` scaffolds
  all three.
- **Approvals.** Read-only inspection (git status/diff/log, grep, find,
  targeted reads, pytest) runs without per-command approval. Mutating
  commands — force-pushes, file deletions, dependency changes, edits outside
  the active PRD's FILES — require explicit approval.
- **Recon-artifact clause.** A read-only charge (recon, audit, charge work)
  forbids mutating source, contracts, and `main` — it does NOT forbid git
  operations on the deliverable it was commissioned to produce. The findings
  artifact MAY be committed and pushed to its own non-`main` branch; that IS
  the deliverable, not a seam surrender. The branch → `main` merge stays
  human-held per the rules above. A charge that wants even the deliverable
  left uncommitted must say so explicitly; silence defaults to
  committable-to-branch.

## PRD rules

- **PRD before build for anything non-trivial** (new module, new external
  dependency, new architectural pattern, change touching multiple pipeline
  layers). Bug fixes and additions within established patterns don't need
  PRDs.
- **Ceremony tiering (PRD-229).** Cosmetic-only changes (ui copy / CSS /
  layout; comment- or docstring-only edits) ride MICRO with a ≤10-line note
  and batch into at most one weekly polish PRD. Owner: `docs/PRD_PROCESS.md`
  (Cosmetic Carve-Out).
- **Author disciplines** — run all four before submitting for review:
  1. **Dead-branch enumeration.** When retiring a code path, enumerate every
     downstream reader of the retired surface; each is removed in the same PRD
     or documented as retained-with-reason. A retired surface with
     un-enumerated readers is hidden drift.
  2. **Downstream-consumer audit.** For any new emission, contract field,
     status value, rejection stage, or artifact path: identify every module
     that reads it and verify compatibility. Postmarket reports, dashboard
     renderers, audit writers, and notification formatters are common
     consumers.
  3. **Realizability check.** Any new output channel (rejection stage,
     classification tier, sidecar field, status literal) must have at least
     one realistic input path under current routing that produces non-trivial
     output. If it is defensive-against-future-routing, declare it as such —
     don't claim it is currently active.
  4. **Sub-agent sweep re-verification.** A delegated grep/recon sweep feeding
     a FILES boundary or a "nothing else reads/calls this" claim does not
     count until the main agent re-runs the single decisive `rg` itself.

## Semantic-failure hardening (PRD-198)

A check is only worth its green if it verifies correspondence to reality, not
the presence of the right words. Six invariants; the rationale and incident
each generalizes are canonical in `docs/prd_history/PRD-198.md` (Part A).

1. **Fail-loud, never silent-fallback.** A missing dependency, an unresolvable
   id, or an unreachable source must exit non-zero — never
   substitute-and-continue.
2. **Assert the resolved, not the requested.** Verify the actual effect — the
   resolved model, the executed test, the CI count — never the declared
   intent.
3. **Authoritative source, not proxy.** Every check names and reads its source
   of truth; never a proxy that can diverge from it.
4. **Every guard ships a red test.** A guard merges only with a negative test
   proving it fails when violated. Banned: `importorskip` on a required dep,
   `WARN`-and-`exit 0`, and any test that cannot fail.
5. **Verify where truth is determined.** Achieve environment parity with the
   gate (CI); local/sandbox green is unverified until reproduced where the
   decision is made.
6. **Pin identities that matter.** Model → dated snapshot, action → commit
   SHA, dependency → declared AND locked. A movable identity changes behavior
   with no diff.

## Working practices

- **Dashboard regeneration = publish from live data, never hand-overwrite the
  snapshot.** "Regenerate the dashboard" means dispatch the `cuttingboard.yml`
  pipeline (`workflow_dispatch`, `mode: live`), which renders from live data
  and publishes to the `publish` branch (the live Pages site). NEVER overwrite
  `main`'s `ui/dashboard.html` / `ui/index.html` from a sandbox render — the
  in-repo `logs/*` are minimal fallbacks, so a local render degrades the
  committed snapshot and does not touch the live site. The local renderer
  (`dashboard-publish-refresh`) stays a read-only DRY_RUN health check at
  most.
- Start work on a PRD by reading the PRD file, the related modules, and prior
  `docs/DECISIONS.md` entries.
- When drift is discovered mid-task (code doesn't match docs, undocumented
  dependencies surface), pause and surface the drift before proceeding.
- **Recon goes to subagents.** Dispatch `Explore` (or `general-purpose`)
  reflexively for code-recon questions ("where is X computed / called /
  asserted, and what depends on it?") and for bookkeeping recon (locating a
  token across `docs/PRD_REGISTRY.md`, `docs/prd_index.json`,
  `docs/PROJECT_STATE.md`). Do NOT use Codex or subagents for simple greps,
  git operations, or mechanical edits.
- **Consult `docs/SCHEMA_MAP.md` and `docs/CALL_SITE_MAP.md` before grepping**
  for where a field or symbol is defined or called — they are the recon cache.
  If a map is stale, fix it as part of the change rather than working around
  it.
- **Use the task list upfront for any work with ≥3 distinct stages.** Update
  status as each stage starts and completes.
- **A registry-gap hook fire is actionable, not boilerplate.** If the
  `UserPromptSubmit` hook (`prd_eval.sh`) flags an unregistered prd_history
  file, add the row rather than working past the warning.
- **Codex mechanics.** Invoke Codex only when Dustin commissions a
  second-model review (PRD-242) and the value is a genuinely independent
  second model — PRD cross-review, vision review, structured pre-merge code
  review. All review invocations run sandboxed read-only:
  `codex exec -s read-only - < prompt` (prompt via stdin, verdict from
  stdout). Claude Code writes the review artifact from captured stdout; Codex
  never writes into the repo tree.
- **Independent reviews dispatch in parallel** (owner: `docs/PRD_PROCESS.md`
  § Review Dispatch). When a Codex or subagent artifact materially drives a
  decision, link the artifact path in the `docs/DECISIONS.md` entry.
- Run targeted tests during iteration. Run the full suite once before
  pre-commit review — backgrounded when it is long enough to do other work in
  parallel.

## Alignment check (PRD-230: phase-boundary diff-read)

Trigger: a phase boundary (a wave/batch of related PRDs closes, or a direction
change lands) — not the calendar. A 15-minute read of the diff since the last
check (`git log --oneline <last-audit-sha>..main` + the registry rows it maps
to), answering four questions:

1. Any new prediction logic? (VISION non-goal)
2. Any new sidecar without a documented consumer or observational purpose?
3. Any new module serving none of VISION's four questions?
4. Post-merge drift audit (PRD-186, folded in): does any merged PRD conflict
   with a VISION principle, leave a PROJECT_STATE claim stale, or carry a
   review artifact that skipped its DRIFT CHECK?

Record one DECISIONS.md line per run (PRDs covered; findings or "none").
Remediation: substantive drift → corrective PRD (number recorded); a
review-artifact DRIFT-CHECK miss → append the missing check in place, no PRD
ceremony for retroactive paperwork.

## Anti-patterns

- Do not draft PRDs for features that violate `VISION.md` non-goals without
  explicit override from Dustin.
- Do not refactor the `runtime/` package opportunistically; it is acknowledged
  debt and refactors require their own PRD.
- Do not add documentation that duplicates canonical sources; reference
  instead.
- Do not silently expand a PRD's FILES set mid-implementation. Amend the PRD
  first.
- Do not commit generated artifacts (`logs/*`, `reports/*`) outside the
  workflow-driven force-add allowlist.
- Do not let session recon notes accumulate in `audits/` (PRD-230): a session
  note is working scratch — delete it once the next session confirms nothing
  was lost. Durable findings belong in `docs/DECISIONS.md` or a PRD.
