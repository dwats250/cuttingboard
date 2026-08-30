# MODE: DESIGN (Layer 2)

Deltas from the standing wall (`CLAUDE.md` / `AGENTS.md`). The wall, owner
holds, precedence, and the common escalation block still bind.

## Allowed
- Author bounded design, packets, plans, or a PRD within the commissioned
  scope, on a docs branch.
- PRD before build for anything non-trivial (new module, dependency,
  architectural pattern, or a change across pipeline layers). Ceremony tiering
  and the Cosmetic Carve-Out are owned by `docs/PRD_PROCESS.md` (PRD-229).
- The first PRD commit is the Stage-0 scaffold: `PRD-NNN.md` + the IN PROGRESS
  registry row + the `prd_index.json` entry, before any implementation commit
  (PRD-159; `scripts/prd_open.sh`).

## Forbidden (beyond the wall)
- Any implementation authority - DESIGN creates none by itself.
- Treating branch existence, or a documentation amendment, as implementation
  authorization or as a Gate A.

## Edits / commits / PR / merge
- Edits: docs/packet/PRD files only. Commits and a draft PR: yes, held. Merge:
  never.

## Materiality
Apply GOV-2 s1 to the proposed work before opening a PRD, and re-apply it
whenever scope, consumers, schemas, ceilings, seams, files, or risk expand. If
the work is or becomes MATERIAL, STOP and surface it - enter the GOV-2 upstream
order; never self-authorize past it.

## Escalate (additions)
- Required authority or evidence is unavailable.
- Conflicting or superseded owner rulings are encountered (GOV-2 keeps exactly
  one current ruling; stop rather than pick).
