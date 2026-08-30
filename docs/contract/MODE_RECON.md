# MODE: RECON (Layer 2)

Deltas from the standing wall (`CLAUDE.md` / `AGENTS.md`). The wall, owner
holds, precedence, and the common escalation block still bind. Default mode when
a charge names none.

## Allowed
- Read, search, targeted tests, and evidence gathering across the repo.
- Commit a findings artifact to its own non-`main` branch (the recon-artifact
  clause): the artifact IS the deliverable, not a seam surrender. A charge that
  wants even the deliverable left uncommitted must say so; silence defaults to
  committable-to-branch. The branch -> `main` merge stays Helm-held.

## Forbidden (beyond the wall)
- Mutating source, contracts, or `main`.
- Any semantic or product ruling; PRD-number allocation.

## Edits / commits / PR / merge
- Edits: the findings artifact only. Commits: its own branch only. PR: draft,
  held. Merge: never.

## Evidence standard
Every load-bearing claim carries: authority path and symbol/section; current
consumer/path reachability; unavailable/failure behavior; a falsifier; and a
disposition - `CONFIRMED`, `FALSIFIED`, `NARROWED`, or `NOT REPRODUCED`.
Sampling cannot support an exhaustive claim; a network-disabled pass cannot
claim to evaluate a live provider. A sub-agent sweep does not count until the
main agent re-runs the single decisive `rg` itself.

## Escalate (additions)
- Required evidence is unavailable, or a claim needs exhaustive proof that
  sampling cannot give. Uncertainty is reported as `UNKNOWN` / `ESCALATE`, never
  resolved into a conclusion.
