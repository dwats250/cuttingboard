# MODE: IMPLEMENT (Layer 2)

Deltas from the standing wall (`CLAUDE.md` / `AGENTS.md`). The wall, owner
holds, precedence, and the common escalation block still bind. Applies equally
to Claude/Fable and to Codex when explicitly commissioned for IMPLEMENT (with an
explicit Basis, Objective, and Scope).

## Allowed
- Edit code within the explicitly authorized FILES, plus the lifecycle
  bookkeeping `docs/PRD_PROCESS.md` makes implicit (`docs/PRD_REGISTRY.md`,
  `docs/prd_index.json`, `docs/PROJECT_STATE.md`) at the applicable step.
- Commit and prepare/update a PR where the charge permits; the PR is a DRAFT
  held for Helm. Same-PR closeout rides the implementation PR (PRD-229) and runs
  only through the `prd-closeout-verified` skill, never a hand-rolled call.

## Scope discipline
- FILES is a hard boundary. A change that needs an unlisted file is a STOP:
  before Gate A, amend the PRD; after Gate A, an added file raises the approved
  ceiling (amend the PRD and the MATERIAL/authority record, obtain fresh-context
  review of the exact amended revision, and receive Dustin's amended Gate A)
  before continuing. Never expand FILES silently.
- Pre-implementation grep sweep (PRD-158): before declaring FILES for a change
  that deletes, renames, or translates a rendered field / contract key / enum,
  grep all of `tests/` for the token and add every asserting test file to FILES
  up front.

## Author disciplines (run all before submitting for review)
1. Dead-branch enumeration: every downstream reader of a retired surface is
   removed in the same PRD or documented as retained-with-reason.
2. Downstream-consumer audit: for any new emission/field/status/stage/path,
   identify every reader and verify compatibility (reports, dashboard,
   audit writers, notifiers).
3. Realizability check: any new output channel has at least one realistic input
   path today, or is declared defensive-against-future-routing.
4. Sub-agent sweep re-verification: a delegated sweep feeding a FILES boundary
   does not count until the main agent re-runs the single decisive `rg`.

Bounded look-ahead before a behavioral edit: inspect the narrow dependency cone
(direct callers/consumers, shared helpers, sibling outputs, fallback/error
paths, post-write ops, structural-assumption tests). Solve the bounded behavior,
smallest robust diff, preserve unrelated behavior.

## Validation
`git diff --check`; targeted tests; `ruff`; `python
tools/validate_prd_registry.py`; the full suite once before review (backgrounded
if long); confirm the diff contains only allowed files. Assert resolved behavior
at the authoritative seam, not a proxy. Every new guard ships a mutation-verified
red test.

## Escalate (additions)
- FILES must expand; a ceiling is exceeded; the work reclassifies MATERIAL; or a
  validation failure has no explained cause.
