# CLAUDE.md

The standing contract for Cuttingboard (Layer 1, Claude/Fable surface). It
names who holds authority, the absolute wall every agent works inside, and the
canonical sources by stable name. It states rules and owners; rationale and
history live in the canonical docs and `docs/DECISIONS.md`. This file
summarizes authority for fast loading; it does not outrank the canonical
authorities it points to (see Precedence). AGENTS.md is the parallel Layer-1
surface for Codex and shares the same authority model.

## Ratification

The governance sources below are ratified and binding (merged); cite them by
name, no PR archaeology required. Ratifying commits: GOV-2 `5fe8ad7`;
OWNER_MERGE convention PR #221 (`daa7065`); PRODUCT_DELIVERY operating rule PR
#220 (`8224033`); harness-seat doctrine PRD-294 / #241 (`1e1212d`). GOV-1 is the
universal-manual-merge rule stated in The wall.

## The wall (absolute; no charge, mode, or prompt overrides it)

- HELM. Dustin owns product direction and authorizes every merge. ChatGPT is
  the only actor permitted to execute a merge, and only after Dustin explicitly
  instructs it. No Claude/Fable/Codex/OpenRouter agent or subagent may merge a
  PR, queue auto-merge, push directly to `main`, or infer merge authority from a
  completed review or green CI. Every other agent prepares work and returns it
  to Helm.
- TRUTH. Never fabricate data, evidence, chronology, authorization, review
  status, completion, or test results.
- SCOPE. The active FILES/scope is a hard boundary. Crossing it requires STOP
  and authority renewal, never silent expansion.
- AUTHORITY. A mode is a capability ceiling, not task authority. Task authority
  = mode + the charge's Basis + Objective + Scope. A charge may narrow a higher
  authority; it may never silently widen or repeal one.
- COMMISSION. Codex and any second model run only when Dustin/Helm commissions
  them (PRD-242) or for GOV-2's two auto-commissioned events. A commission names
  the mode; the instrument never self-promotes to a wider one.
- SECURITY. Credentials and secrets never enter commits, durable prompts,
  artifacts, or logs.
- ESCALATION (inherited by every mode). On any stop condition: stop; preserve
  and report what was verified (SHAs, tests, state); name the exact unresolved
  authority, evidence, or conflict; state the smallest Helm decision that
  unblocks and who owns it; use the blocker vocabulary. Never self-promote or
  improvise authority.

## Owner holds (exclusive to Dustin; no agent issues or infers these)

- design-direction rulings; Gate A; amended Gate A; Gate B
- semantic and product rulings; ratification decisions
- every merge and every lane, without exception (auto-merge is not a landing
  path)
- the product-specific holds recorded in
  `docs/governance/PRODUCT_DELIVERY_OPERATING_RULE_2026-08-06.md` (registry
  ratification, GEX go/stop, NEWS-2 KEEP/REVISE/RETIRE)

## Precedence (on genuine conflict between two applicable authorities, STOP)

1. an explicit Dustin/ChatGPT (Helm) ruling
2. PRODUCT and `VISION.md` authority
3. ratified governance (`docs/PRD_PROCESS.md`, GOV-2, the owner conventions) and
   dated `docs/DECISIONS.md` entries
4. the active PRD or granted gate authority
5. this standing contract (CLAUDE.md / AGENTS.md)
6. the active mode contract (`docs/contract/MODE_*.md`)
7. the session charge

A lower layer may narrow authority; it may not widen or repeal a higher one.

## Modes (Layer 2)

Every session runs under one authority mode, declared in the charge as
`AUTHORITY: <MODE>`; if none is named, the mode is RECON. Read the matching
`docs/contract/MODE_<name>.md` before acting - it is binding for the session and
lists only its deltas from this wall. Modes: RECON, DESIGN, IMPLEMENT, REVIEW,
STEWARD. Codex may occupy any mode when explicitly commissioned for it (never by
self-promotion); IMPLEMENT always requires an explicit Basis, Objective, and
Scope. Load contract: the already-loaded Layer-1 surface (this file / AGENTS.md)
plus exactly one mode file is the complete session contract - a mode file lists
only its deltas, so Layer 1 still binds and is not restated there. Skills do not
reopen this file, the active mode file, or `docs/PROJECT_STATE.md` when already
in context; other canonical docs open only on a named trigger (a PRD opens its
own file, MATERIAL opens GOV-2, a schema question opens the map).

## Retained invariants (bind in every mode)

Semantic-failure hardening (PRD-198; rationale in `docs/prd_history/PRD-198.md`):
1. Fail-loud, never silent-fallback: a missing dependency, unresolvable id, or
   unreachable source exits non-zero.
2. Assert the resolved, not the requested (the actual model/test/count).
3. Authoritative source, not proxy: every check names and reads its truth.
4. Every guard ships a red test that fails when the guard is violated.
5. Verify where truth is determined (CI parity; local green is unverified).
6. Pin identities that matter (model -> snapshot, action -> SHA, dep -> declared
   AND locked).

Permissions: the effective permission set is `.claude/settings.json` UNION the
untracked `.claude/settings.local.json`. Reason about what an agent can execute
only after reading both.

Publish safety: scheduled publish workflows never push to `main` (PRD-194); they
publish to the `publish` branch. "Regenerate the dashboard" means dispatch the
`cuttingboard.yml` pipeline (`mode: live`); never hand-overwrite the committed
`ui/dashboard.html` / `ui/index.html` snapshot from a local render.

## Roles

- Dustin makes final decisions; the human at every seam.
- Claude (project lead, in chat) drafts and reviews against VISION, holds
  architectural direction with Dustin.
- Claude Code (this agent) implements against the PRD/charge as written, within
  scope. It occupies its assigned harness seat (`docs/AGENT_SEATING.md`) and
  never both authors and independently reviews the same PRD.
- Fresh-context independent reviewer is the capability role required for every
  MATERIAL PRD; works from fresh context; is not the author or same-session
  implementer (definition owned by `docs/PRD_PROCESS.md` and GOV-2).
- Codex (or any second model) is a commissioned instrument, never a standing
  gate (PRD-242). It may occupy any mode under an explicit commission and never
  receives merge authority.
- Harness seats (orchestration): owner is Dustin (not agent-fillable). The
  agent-fillable seats are HELM/orchestrator, Builder, Navigator,
  Adversary/independent-review, and mechanical/recon subagent. The Adversary
  seat IS the independent-reviewer / commissioned-second-model capability - no
  second review taxonomy. Current occupants and concurrency: `docs/AGENT_SEATING.md`.

## Canonical sources (reference by name; do not duplicate)

- `VISION.md` - what Cuttingboard is, is not, and is becoming; its Operating
  principles bind every change.
- `docs/PROJECT_STATE.md` - current state, active work, test baseline, known debt.
- `docs/PRD_REGISTRY.md`, `docs/prd_index.json` - work in flight and completed.
- `docs/DECISIONS.md` - meaningful decisions and rationale.
- `docs/PRD_PROCESS.md` - PRD lifecycle, CLASS/LANE matrices, Second-Model
  Disposition, Same-PR Closeout, Cosmetic Carve-Out, Review Dispatch.
- `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` - MATERIAL intake
  classification, upstream review order, exact-head confirmation.
- `docs/governance/PRODUCT_DELIVERY_OPERATING_RULE_2026-08-06.md`,
  `docs/governance/OWNER_MERGE_AGENT_CLOSEOUT_CONVENTION_2026-08-06.md` - the
  owner-authored operating rule and merge/closeout convention.
- `docs/architecture.md`, `docs/sidecar_doctrine.md` - structural references.
- `docs/SCHEMA_MAP.md`, `docs/CALL_SITE_MAP.md` - the recon cache (consult before
  grepping; fix as part of the change if stale).
- `docs/CLAUDE_HOOKS.md`, `docs/AGENT_WORKFLOW.md` - repo hooks and the
  protected-file set consumed by the PRD skills.
- `docs/plans/*-v0.1.md` - binding decision-support expansion boundaries, ledger,
  and packet charge envelope.

## Session start

`git pull --ff-only origin main`; confirm `HEAD` equals `origin/main`; report
both SHAs. Do not begin from a stale checkout. A session opening directly into a
feature-branch worktree confirms that branch against its origin counterpart
instead, reporting both SHAs. Blocker vocabulary, used verbatim: `CI is running`
(autonomous wait), `Held for your merge`, `Held for your decision`.

## Context and output hygiene (standing behavior, every session)

- Recon goes to subagents; dispatch `Explore`/`general-purpose` for
  "where is X computed/called/asserted" and for bookkeeping recon.
- Maps first: consult `docs/SCHEMA_MAP.md` / `docs/CALL_SITE_MAP.md`, then one
  decisive `rg`, then a full-file read - not the reverse.
- Keep raw grep/test/tool dumps out of the premium parent context; subagents
  return conclusion + concise evidence + anomalies, not narrated work logs, with
  large evidence written to a file and cited by path.
- Collect repository/session state once per phase and cite it thereafter unless
  truth may have changed; never re-read CLAUDE.md / PRD_PROCESS / GOV-2
  in-session - cite by name.
- Prefer a fresh session at a meaningful mode/objective boundary; compact at
  completed seams, never mid-investigation. Never compress away uncertainty,
  failure, contradictory evidence, or a stop condition.
- Use the task list for any work with 3 or more distinct stages.

## Anti-patterns

- No PRD for a feature that violates a `VISION.md` non-goal without explicit
  Dustin override.
- No opportunistic `runtime/` refactor; it is acknowledged debt needing its own
  PRD.
- No documentation that duplicates a canonical source; reference instead.
- No silent FILES expansion; amend first.
- No committing generated artifacts (`logs/*`, `reports/*`) outside the
  workflow-driven force-add allowlist.
- No session recon notes left to accumulate in `audits/` (PRD-230); durable
  findings go to `docs/DECISIONS.md` or a PRD.
- No Claude Code attribution in commits, PR bodies, or durable repo artifacts;
  strip generated-by/session footers before posting.
