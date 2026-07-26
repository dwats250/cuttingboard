# CuttingBoard Agent Work Charge Template v0.1

Status: APPROVED FOR MANUAL MERGE — EFFECTIVE WHEN MERGED

Use this template for every work packet governed by
`decision-support-expansion-doctrine-v0.1.md`.

Delete bracketed instructions when filling the charge. Do not omit a section.
If a section does not apply, write `N/A` and explain why.

---

# [PACKET] — [Exact bounded title]

## Authority

- Operator ruling: [exact dated `docs/DECISIONS.md` entry or `NONE`]
- Governing plan:
  `docs/plans/decision-support-expansion-doctrine-v0.1.md`
- Workplan packet:
  `docs/plans/decision-support-workplan-v0.1.md#[anchor]`
- Governing PRD: [exact path or `READ-ONLY / NO PRD`]
- Related evidence: [exact paths]
- Precedence on conflict:
  `VISION.md` → `CLAUDE.md` / `docs/PRD_PROCESS.md` →
  expansion doctrine → dated operator decision → active PRD → work charge.

If two higher authorities conflict, STOP and report the conflict. Do not choose.

## Objective

[One sentence describing one result.]

## Work type

- Mode: [READ-ONLY RECON | DOCS-ONLY | IMPLEMENTATION | REVIEW]
- Lane/class: [N/A or exact values]
- Mutation permission: [exactly what may be changed]
- Merge permission: NONE

## Mandatory preflight

Report each exact value before work:

1. Repository: `dwats250/cuttingboard`
2. Expected branch: `[branch]`
3. Actual branch: `git branch --show-current`
4. Expected starting SHA: `[full SHA]`
5. Actual HEAD: `git rev-parse HEAD`
6. Remote counterpart SHA: `[command and result]`
7. Working tree: `git status --short` must be empty
8. PR state, if applicable: [open/draft/unmerged/head SHA]
9. Required authority files read: [list]

STOP if branch, SHA, cleanliness, PR state, or authority differs. A user may
explicitly authorize a branch switch, but no reset, rebase, force-push,
cherry-pick, or workaround is implied.

## Questions to answer

[For recon: numbered closed questions. Each must have a direct answer.]

## In scope

- [Exact behavior or artifact]
- [Exact behavior or artifact]

## Out of scope

- [Explicit neighboring feature]
- [Explicit neighboring feature]
- Opportunistic cleanup
- New dependencies unless named
- New workflows/cadence unless named
- New abstractions unless named
- PRD-number allocation unless named
- Merge or auto-merge

## Allowed files

[For implementation, copy the PRD FILES exactly.]

- `path`
- `path`

Lifecycle bookkeeping explicitly made implicit by `docs/PRD_PROCESS.md` is
also authorized when the packet reaches its applicable Stage-0 or same-PR
closeout step:

- `docs/PRD_REGISTRY.md`
- `docs/prd_index.json`
- `docs/PROJECT_STATE.md`

Those paths may change only for required lifecycle bookkeeping, never for
unrelated prose. No other tracked file may change. If another file is required,
STOP and request a PRD amendment before editing.

## Change-surface ceiling

- Production files: [number]
- Test files: [number]
- Net production LOC: [number]
- Total file line cap, where applicable: [number]

Exceeding any ceiling is a stop condition, not permission to expand.

## Required invariants

- [Behavior that must remain unchanged]
- [Contract that must remain unchanged]
- [Baseline-neutral missing-data behavior]

## Requirements and discriminating tests

| Requirement | Observable behavior | Test | Mutation that must turn it red |
|---|---|---|---|
| R1 | [binary result] | `[test]` | [specific reversal] |
| R2 | [binary result] | `[test]` | [specific reversal] |

Tests must assert resolved behavior at the authoritative seam, not a proxy,
constant, requested value, or presence of prose.

## Evidence standard

Every load-bearing recon claim must include:

- authority path and symbol/section;
- current consumer/path reachability;
- unavailable/failure behavior;
- falsifier; and
- disposition: `CONFIRMED`, `FALSIFIED`, `NARROWED`, or
  `NOT REPRODUCED`.

Sampling cannot support an exhaustive claim. A network-disabled pass cannot
claim to evaluate a live provider.

## Validation order

1. `git diff --check`
2. [targeted tests]
3. [lint/static checks]
4. `python tools/validate_prd_registry.py --skip-commit-resolvability`
5. [full suite, if implementation]
6. `git status --short`
7. Confirm diff contains allowed files only

Record exact commands, exit codes, pass counts, xfails, and environment
qualification. Do not explain away a failed test as environmental without a
reproduced CI-parity result and a concrete cause.

## Review

- Review target SHA: [full immutable SHA]
- Reviewer: [fresh context, not author]
- Mode: read-only
- Review question: [exact scope]
- Required artifact path: [exact path, if governed by a PRD]
- Maximum correction cycles: ONE

The reviewer reviews the packet's actual deliverable or change, not prior
review prose. For an implementation packet this means the implementation; for
recon, docs-only, provider-evidence, or decision packets it means the
commissioned artifact and its load-bearing claims. If the first correction
creates new substantive uncertainty, STOP for Dustin rather than starting
recursive review.

## Landing

- Commit count: [exact ceiling]
- Push count: [exact ceiling]
- PR state: DRAFT
- Auto-merge: FORBIDDEN
- Merge: FORBIDDEN
- Other PRs/branches: DO NOT TOUCH
- Final hold phrase: `Held for your merge` or `Held for your decision`

## Stop conditions

Stop immediately if:

- authority conflicts;
- preflight differs;
- a real identifier cannot be resolved;
- required evidence is unavailable;
- FILES must expand;
- a ceiling is exceeded;
- a dependency/workflow/schema change becomes necessary but is not authorized;
- validation fails for an unexplained reason;
- the active branch is not the PR branch;
- the requested work has already been superseded; or
- the task would create prediction, execution automation, or decision coupling
  forbidden by doctrine.

## Final report format

1. Starting branch and SHA
2. Authority read
3. Exact files changed
4. Requirement-by-requirement result
5. Exact validation results
6. Commit and pushed SHA, if authorized
7. PR state
8. Remaining blockers using exactly:
   - `CI is running`
   - `Held for your merge`
   - `Held for your decision`
9. Explicit confirmation: no merge, no auto-merge, no other PR touched

Do not include a claim that work is complete if any requirement, validation,
review, or landing condition remains unmet.
