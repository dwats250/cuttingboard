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
- **Claude Code (this agent)** implements PRDs against the PRD doc as
  written: implementation, test maintenance, and architectural decisions
  within PRD scope. Occupies whichever seat the model-role lane assigns
  (`docs/PRD_PROCESS.md` § Model-role lane) and never both the drafting
  seat and the second-model review of the same PRD. Invokes Codex only
  for a review Dustin has commissioned (PRD-242), or for the mandatory
  MATERIAL-packet review and exact-corrected-head confirmation that GOV-2
  itself commissions
  (`docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` §2, §7) —
  never otherwise at its own discretion.
- **Fresh-context independent reviewer** is the capability role required for
  every MATERIAL PRD, whether its lane is STANDARD or HIGH-RISK. The reviewer
  works from fresh context; is not the PRD author or same-session implementer;
  reviews the drafted PRD, the review-clean MATERIAL packet, and Dustin's
  design-direction ruling; and records a committed verdict against the exact
  reviewed PRD commit SHA or revision. A qualified fresh-context second-model
  reviewer commissioned under the MATERIAL workflow may fill this role.
  Selecting Codex for this role requires a separate Dustin commission under
  PRD-242; the role does not expand GOV-2's two auto-commissioned Codex
  packet-cycle events.
- **Codex (or any second model)** is an instrument Dustin may commission for a
  genuinely independent second opinion (PRD-242). Never a standing gate
  requirement; never drives architectural direction. GOV-2 adds one bounded
  exception: work classified MATERIAL at intake requires Codex review of the
  upstream packet and independent confirmation of its exact corrected head
  before a design-direction ruling.

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
- `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` — binding
  material-work intake classification, upstream review order, exact-head
  confirmation, bounded correction, and provisional-ceiling rules after
  Dustin ratifies GOV-2.
- `docs/governance/PRODUCT_DELIVERY_OPERATING_RULE_2026-08-06.md` — Dustin's
  owner-authored operating rule: default behavior, Fable escalation triggers,
  the anti-stall choice, the post-TRUTH-SYNC lane order (NS-2E, GEX, context
  registry), and the owner holds. Binding on Dustin's merge of its landing PR.
- `docs/governance/OWNER_MERGE_AGENT_CLOSEOUT_CONVENTION_2026-08-06.md` —
  Dustin's owner-authored convention: Dustin holds every merge, semantic/
  product rulings, Gate A, and ratification; agents own deterministic
  post-review readiness, PR-metadata hygiene, post-merge seam closeout, and
  safe branch reconciliation without re-asking, bounded by explicit stop
  conditions. Binding on Dustin's merge of its landing PR.
- `docs/architecture.md`, `docs/sidecar_doctrine.md` — structural references
- `docs/CLAUDE_HOOKS.md` — the repo's hooks (file protection, PRD registry-gap
  check, canonical-read guard) and their state files
- `docs/AGENT_WORKFLOW.md` — protected-file set consumed by the PRD skills
- `docs/plans/decision-support-expansion-doctrine-v0.1.md` — binding GEX,
  personalized-news, options-data, and macro-awareness expansion boundaries
- `docs/plans/decision-support-workplan-v0.1.md` — the single sequenced ledger
  for existing reconciliation and future scaffolding in those tracks
- `docs/plans/agent-work-charge-template-v0.1.md` — mandatory non-deviation
  charge envelope for every packet governed by those two plans

## How work lands

- **Everything lands through a PR (PRD-184), and Dustin merges every one
  (GOV-1).** Push the feature branch and open the PR; `main` branch protection
  holds the merge until the CI `test` check is green. **Agents never merge a
  PR and never queue `gh pr merge --auto`** — the merge is Dustin's act, on
  every PR, without exception. There is no direct-to-main push path;
  force-push is denied by repo settings.
- **Closeout rides the implementation PR** (PRD-229 Same-PR Closeout; owner:
  `docs/PRD_PROCESS.md`). Residual bookkeeping fixes ride their own PR, held
  for Dustin's merge like any other. GOV-2 does not change this rule; moving
  HIGH-RISK closeout post-merge requires a later code-touching validator PRD.
- **Closeouts run only through the `prd-closeout-verified` skill.** Never a
  hand-rolled `prd_close.sh` call. The skill's preflight distinguishes
  same-PR mode (`#NNN`, requires an OPEN PR) from hex-hash mode (post-merge)
  — a hand-rolled call got this wrong on PRD-266 and was caught late.
- **Scheduled publish workflows never push to `main` (PRD-194).** They publish
  the rendered dashboard and scoreboard state to the dedicated UNPROTECTED
  `publish` branch that GitHub Pages deploys from; `main` receives only
  CI-gated PR merges.
- **Governance changes carry a visible hold (PRD-186).** GOV-1's universal
  manual merge already covers them; what PRD-186 adds is that a PR changing
  the review-gate skill (`prd-review-claude`) or any governance guardrail in
  this file — the landing policy, the review gates, the review-depth or
  bot-thread disposition, the drift check, the Alignment check — is opened as
  a DRAFT and names itself as governance in its body. The hold is stated, not
  merely implied.
- **Decision-support expansion plan PRs carry the same visible hold (GOV-0).**
  Every PR governed by the three `docs/plans/*-v0.1.md` expansion files is
  opened as a draft and held for Dustin. Under GOV-1 this is no longer a
  carve-out from PRD-184 — it is the universal rule, restated here because
  those plans are read on their own.

## Review gates

- **Nothing lands without review.** Implementations are reviewed against the
  PRD before they are considered done.
- **Lane declares ceremony.** The PRD header declares LANE (MICRO / STANDARD /
  HIGH-RISK); eligibility and review intensity: `docs/PRD_PROCESS.md`.
- **The routine gate is one fresh-context review plus the connector's
  (GOV-1).** Every PR gets exactly one structured review by a REVIEWING AGENT
  working from a fresh context — one that did not author the change — plus
  whatever the connector bot posts (advisory only; see bot-review threads
  below). That is the whole standing requirement. Deep independent review is
  NOT standing except for work classified MATERIAL under GOV-2, or when it is
  otherwise commissioned by Dustin or triggered by the conditions named in
  `docs/PRD_PROCESS.md` § Second-Model Disposition.
- **MATERIAL work is classified at intake and reclassified on material scope
  expansion (GOV-2).** Before opening a PRD, apply
  `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` §1 to the
  proposed work. Re-run that classification before continuing whenever
  scope, consumers, schemas, ceilings, seams, files, or risk assumptions
  expand materially after intake. If the work newly becomes MATERIAL, stop
  implementation, create or reopen the upstream MATERIAL packet, and clear
  the required packet review and authority sequence before resuming. A
  MATERIAL match requires independent Codex packet review, one consolidated
  correction, and independent SHA-pinned confirmation of the exact corrected
  head. Only then may Dustin issue a design-direction ruling and downstream
  PRD drafting begin. Gate A remains the later implementation authorization
  on the independently reviewed PRD. A MATERIAL slice is ineligible for
  `LANE: MICRO` — GOV-2's required order includes a PRD, its independent
  review, and an explicit Gate A, none of which MICRO's collapsed path
  contains; it rides STANDARD at minimum, with HIGH-RISK only per R11's own
  triggers (GOV-2 §1).
- **At most one correction cycle (GOV-1).** The reviewing agent produces
  findings once; the authoring agent addresses them once; the gate closes. A
  second round happens only because Dustin asks for one — never because a
  reviewer wants the last word. For MATERIAL packets, GOV-2's exact-head
  confirmation is part of that single bounded cycle; a new material boundary
  omission returns the packet to DESIGN INCOMPLETE instead of creating an
  endless review loop. A post-Gate-A ceiling increase creates a changed
  authority revision and therefore requires the amended-PRD review specified
  by GOV-2 §5. That review receives one findings-and-correction cycle for the
  amended revision; it is not another pass on the prior closed review and is
  not another Codex packet-cycle event.
- **Reviews target the change, never another review's prose (GOV-1).** A
  review reads its stage's governing input, not another review's prose: an
  implementation review reads the diff and the PRD; a GOV-2 upstream
  material-packet review — which runs before any PRD exists — reads the
  packet and the relevant repository surfaces; a GOV-2 PRD review reads the
  PRD, the packet, and the design-direction ruling; a GOV-2 exact-head
  confirmation reads the corrected head SHA and the prior review's findings
  list, and is a confirmation, not a fresh-scope review. No artifact is
  produced whose subject is another artifact.
  Disagreement between reviewers is Dustin's to adjudicate, not a prompt for
  a further round of review-of-review.
- **Capability roles, not model names (GOV-1).** This section and
  `docs/PRD_PROCESS.md` § Review Dispatch name SEATS — authoring agent,
  reviewing agent, independent reviewer, connector bot — not vendors or model
  families. Which model fills a seat is an operational choice recorded
  elsewhere (§ Roles, § Working practices) and may change without a
  governance PR. TWO NAMED EXCEPTIONS, both CI-bound identifiers a docs-only
  change must not touch: the artifact filename
  `docs/prd_history/PRD-NNN.review.<model>.md`, and the literal
  `SECOND-MODEL:` sentence below. `tools/validate_prd_registry.py` matches
  both as literal strings; renaming either breaks the CI `test` check, so
  changing them requires a code-touching PRD, not this policy.
- **HIGH-RISK gate (PRD-242).** Before merge: a fresh-context review
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
  commit SHA / PRD number; (b) DISMISSED with a one-line in-thread reason
  (out-of-scope, false positive, or already-covered with the covering SHA); or
  (c) BLOCKED/PARKED under GOV-2 — the finding is valid, the packet is not
  review-clean, downstream authority is prohibited, and the thread remains
  unresolved until Dustin resumes, narrows, or retires the packet. A real
  defect gets the normal treatment — PRD before build when non-trivial, a
  mutation-verified red test per the hardening invariants — never patched
  silently to clear the thread. The thread is not the artifact: resolving it
  never stands in for the lane's fresh-context review or the second-model
  disposition. Connector output is also not a correction cycle — triaging it
  does not consume the single cycle GOV-1 allows. This clause is itself a
  governance guardrail (per above).
- **Drift check in every review (PRD-186).** Every review artifact records a
  DRIFT CHECK, not just correctness: does the change conflict with a
  `VISION.md` non-goal/principle, and does it leave any
  `docs/PROJECT_STATE.md` claim stale? Carried by the `prd-review-claude`
  skill.
- **Drift review is a post-merge audit (PRD-186)** — the per-PRD DRIFT CHECK
  plus the Alignment check below — not a pre-merge gate. PRD-186 scoped it
  that way because auto-merge was then the default; under GOV-1 it stays
  post-merge for a different reason: Dustin's merge is already the human
  gate, and the drift audit sweeps wider than any single PR.

## Scope and approvals

- **Strict scope locking.** A PRD's `FILES` section is a hard boundary; touch
  only what it authorizes. If a change needs a file not listed, STOP before
  editing. Before Gate A, amend the PRD or open a new one. After Gate A,
  adding a file increases the approved FILES ceiling: amend the PRD and the
  relevant MATERIAL packet/authority record, obtain fresh-context independent
  review of the exact amended PRD revision, and receive Dustin's explicit
  amended Gate A before continuing. Never expand FILES silently, and never
  treat a documentation amendment alone as implementation authorization.
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
  PRDs. GOV-2 runs before this step: qualifying MATERIAL work must clear its
  upstream packet before the Stage-0 PRD is opened.
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

## Execution posture

- **The opening session charter is standing direction.** The session's opening
  prompt sets priorities, task order, and budgets for the whole session; treat
  it as in force without restatement. Later prompts may refer back to it rather
  than repeat it. Only an explicit later instruction from Dustin overrides it;
  silence does not.
- **Bounded look-ahead before behavioral edits.** Before changing behavior,
  inspect the narrow dependency cone the change touches: direct callers, direct
  consumers, shared helpers, sibling outputs, fallback/error paths, post-write
  operations, and tests encoding structural assumptions. Surface hidden sibling
  behavior that could become inconsistent. This extends the Author disciplines
  to behavioral changes — not license for a broad audit or architecture review.
- **Solve the bounded behavior, not the reported line.** Fix the complete
  behavior the defect implicates; prefer the smallest robust diff; preserve
  unrelated behavior. Never expand schemas, architecture, files, or product
  scope without explicit need and authorization — scope locking and VISION's
  `cuts-before-additions` govern.
- **Review economy.** Finish implementation, focused tests, and local
  validation before commissioning a second-model review; commission one
  consolidated review on the review-ready head; handle confirmed findings in
  the single correction pass GOV-1 already allows. Adjacent or pre-existing
  findings become follow-up proposals — they do not block the authorized seam.
  Follow any exact-head confirmation required by GOV-2. Beyond that, a further
  review is justified only by a concrete unresolved runtime, acceptance,
  security, or authority risk introduced or left unresolved by the correction —
  never for reassurance.
- **Product behavior is the work; governance is the guardrail.** Do not reopen
  closed audits or manufacture process work absent a concrete blocking defect.

## Working practices

- **Session start.** Before any work: `git pull --ff-only origin main` and
  confirm `HEAD` equals `origin/main`. Report both SHAs. Do not begin work
  from a stale checkout. This applies to the main checkout at session
  start; a session opening directly into an existing worktree on a feature
  branch instead confirms that branch is current against its own origin
  counterpart, reporting both SHAs the same way.
- **Blocker phrasing.** When reporting a hold, name the blocker as exactly
  one of: `"CI is running"` (autonomous wait, no action needed from Dustin)
  or `"Held for your merge"` / `"Held for your decision"` (Dustin is the
  blocker and must act). Never blur these — a supervised gate reported as
  an autonomous wait makes Dustin stand down when he is the one blocking.
- **No Claude Code attribution in GitHub/repo content.** Do not append Claude
  Code attribution, generated-by text, Claude session URLs, or session
  identifiers to commits, PR bodies, issue comments, review comments, or
  durable repository artifacts. Before posting or updating any of these,
  strip automatically generated attribution while preserving substantive
  content — no `Generated by Claude Code`, no `Generated with Claude Code`,
  no `claude.ai/code/session_...`, no standalone Claude session identifier.
- **The effective permission set is `.claude/settings.json` UNION
  `.claude/settings.local.json`, not `settings.json` alone.** The local file
  is untracked, personal, and accumulates silently from months of
  interactive approvals (currently ~394 entries nobody has ever reviewed
  as a set). Reasoning about what an agent can execute — or auditing
  whether a command "stays gated" — from the tracked file alone is
  unverified; a blanket grant in the local file can silently defeat an
  assumption the tracked file's design depends on (found empirically,
  `docs/DECISIONS.md` 2026-07-14, PRD-258). Read both.
- **Dashboard regeneration = publish from live data, never hand-overwrite the
  snapshot.** "Regenerate the dashboard" means dispatch the `cuttingboard.yml`
  pipeline (`workflow_dispatch`, `mode: live`), which renders from live data
  and publishes to the `publish` branch (the live Pages site). NEVER overwrite
  `main`'s `ui/dashboard.html` / `ui/index.html` from a sandbox render — the
  in-repo `logs/*` are minimal fallbacks, so a local render degrades the
  committed snapshot and does not touch the live site. There is no local
  renderer skill; `.github/workflows/dashboard_preview.yml` is the
  sanctioned pre-merge preview path (ephemeral render, never committed or
  deployed).
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
  second-model review (PRD-242) — PRD cross-review, vision review, or
  structured pre-merge code review — or for exactly the two events GOV-2
  itself auto-commissions on MATERIAL work: the upstream material-packet
  review and the independent confirmation of the exact corrected head
  (GOV-2 §2, §7). MATERIAL classification automatically authorizes no other
  Codex event. The MATERIAL workflow separately commissions the
  fresh-context independent reviewer capability role for the PRD review; a
  qualified fresh-context second-model reviewer may fill that role, but
  selecting Codex requires a separate Dustin commission. The implementation
  review remains the lane-required review. Codex is not a general standing
  gate. All review invocations run sandboxed read-only:
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
