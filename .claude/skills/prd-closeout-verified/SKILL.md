---
name: prd-closeout-verified
description: Use when closing out a completed PRD — flips registry status to COMPLETE, writes the bookkeeping commit, resets PROJECT_STATE, and verifies four-way consistency across PRD_REGISTRY.md, PROJECT_STATE.md, prd_history/PRD-NNN.md, and prd_index.json. Wraps scripts/prd_close.sh and patches the gaps it leaves (an existing IN PROGRESS registry row is updated in place; the Active PRD pointer is reset; the Next step line is reset). Triggers on "close PRD-NNN", "run bookkeeping for PRD-NNN", "complete PRD-NNN", "finish closeout".
---

# PRD Closeout with Built-in Verification

## Scope and boundary

This skill does two things and only two things:

1. **Apply** the mechanical closeout edits across the four bookkeeping
   artifacts.
2. **Verify** that all four artifacts agree on PRD number, status, and
   commit hash after the edits land.

It is NOT a substitute for:

- Implementation review or test-pass verification
- The cross-review gate (Codex / Claude review artifacts)
- Pushing to `origin` — push is a separate, explicit human/agent action
  outside this skill

Closeout is the *last* step. If the implementation commit has not
landed yet, refuse and direct the user to land it first.

Dashboard/UI artifact refresh, if required by the PRD, must be
completed before closeout. This skill does not detect or perform UI
refreshes.

## When to trigger

- "Close PRD-NNN"
- "Run bookkeeping for PRD-NNN"
- "Complete PRD-NNN"
- "Finish closeout"
- After a successful implementation commit when the user signals done

Do NOT trigger for:
- A PRD still in PROPOSED state
- A PRD whose implementation commit has not landed
- Adjudication or review artifacts

## Operating modes

Default is **DRAFT_ONLY**.

- **DRAFT_ONLY** — emit the planned closeout diff (registry row,
  PROJECT_STATE deltas, PRD-NNN.md STATUS line, prd_index.json entry)
  and the Verification Report. Do not write or commit.
- **WRITE_MODE** — invoke `scripts/prd_close.sh --commit` with the
  args (plus optional `--next`). As of PRD-164 the script produces a
  **complete single-commit closeout**: it flips the existing registry
  row in place to `COMPLETE @ <hash>`, sets both PRD-doc status markers
  (`Status: COMPLETE` header + `STATUS: COMPLETE @ <hash>` trailing),
  and resets `**Active PRD:**` to `none`. No separate "registry/state
  fixup" commit is required. Phase 2 then verifies the script's output.

Push to `origin` is intentionally out of scope. If the user wants the
closeout pushed, they perform `git push` themselves after the skill
returns.

If unclear, ask once, then default to DRAFT_ONLY.

## Inputs required

The skill needs these arguments before Phase 1:

- `prd` — three-digit PRD number (e.g. `140`)
- `hash` — short implementation commit hash (e.g. `1dbc886`)
- `title` — PRD title, exact match to the PRD header
- `tests` — total passing test count after PRD lands
- `added` — net new tests added (0 for docs-only PRDs)
- `summary` — one-paragraph what + why, suitable for the
  PROJECT_STATE "Last work completed" line
- `next` — *optional*; the new `**Next step` text. Passed through to
  `prd_close.sh --next`. When omitted, the `**Next step` line is left
  unchanged (the script never clobbers it with a canned string).

If any of the required args are missing, ask. Do NOT invent or guess.

## Hard rule: no invented references

Verified repo reality wins over drafting intent. The skill must never
invent:

- Commit hashes (must resolve via `git rev-parse <hash>^{commit}`)
- PRD titles (must match the PRD-NNN.md `# PRD-NNN — <title>` header
  byte-for-byte after `— `)
- Test counts (must be supplied; never inferred from a sample)
- Net-new test counts (must be supplied; never inferred from a diff)

If any of the above cannot be verified, stop and request the value
from the user. Do not proceed with a placeholder.

## Registry-row invariant

A PRD whose implementation commit has landed MUST already have a
registry row in `docs/PRD_REGISTRY.md` (typically with status
`IN PROGRESS`). This skill does not create a missing row.

If the row is missing at preflight, stop and report the inconsistency.
Resolve it manually before re-invoking the skill. Silent creation of a
missing row during closeout would mask a deeper bookkeeping break
(implementation started without registering the PRD) and is forbidden.

Note: `scripts/prd_close.sh` will *append* a row when one is missing.
This skill's preflight runs **before** invoking that script precisely
to intercept the missing-row case.

## Two-phase contract

### Phase 1 — Apply

1. **Preflight (every check must pass; otherwise stop):**
   a. `git rev-parse <hash>^{commit}` succeeds (commit exists)
   b. The implementation commit's subject contains `PRD-<NNN>`
   c. Working tree clean (`git status --short` empty)
   d. `docs/prd_history/PRD-NNN.md` exists
   e. PRD-NNN registry row exists in `docs/PRD_REGISTRY.md`
      (status is typically `IN PROGRESS`; any non-`COMPLETE` value is
      acceptable to proceed)
2. **Invoke `scripts/prd_close.sh --commit`** with the six args (plus
   `--next "<text>"` if the next step should change).
3. **Capture script output.** As of PRD-164 the script flips the
   existing registry row in place to `COMPLETE`, sets both PRD-doc
   status markers, and resets `**Active PRD:**` to `none` — all in the
   single `Close PRD-NNN bookkeeping` commit. There is no second
   "fixup" commit.
4. **Do not hand-patch the registry row, status markers, or Active PRD
   pointer.** The script owns those. If Phase 2 finds any of them
   wrong, that is a `prd_close.sh` regression — stop and investigate
   the script, do not silently paper over it with a manual edit.

### Phase 2 — Verify (MANDATORY before returning)

Run every check below. Emit a `## Verification Report` block at the end
of the response. Do not skip any item.

| # | Check | Action on failure |
|---|---|---|
| V1 | `git rev-parse <hash>^{commit}` succeeds | Stop; bad hash |
| V2 | Implementation commit subject contains `PRD-<NNN>` | Stop; hash points to wrong commit |
| V3 | Registry row exists, status `COMPLETE`, hash column matches `<hash>` | Script owns this (R2); failure = `prd_close.sh` regression — investigate |
| V4 | PRD-NNN.md header is `Status: COMPLETE` and last non-blank line is `STATUS: COMPLETE @ <hash>` | Script owns this (R3); failure = `prd_close.sh` regression — investigate |
| V5 | `prd_index.json` contains entry for PRD-NNN with matching hash | Re-run prd_close.sh |
| V6 | `PROJECT_STATE.md` "Last completed PRD" line names PRD-NNN with `(commit <hash>)` | Re-run prd_close.sh |
| V7 | `PROJECT_STATE.md` "Last work completed" has a fresh dated entry for PRD-NNN | Re-run prd_close.sh (it prepends the entry) |
| V8 | `PROJECT_STATE.md` `**Active PRD:**` line == `none` (or matches a user-named next PRD) | Script owns this (R4); failure = `prd_close.sh` regression — investigate |
| V9 | `PROJECT_STATE.md` `**Next step:**` is not stale (does not still reference PRD-NNN as in-flight) | Re-run with `--next "<text>"` |
| V10 | All four artifacts agree on the hash: `grep -h <hash> docs/PRD_REGISTRY.md docs/PROJECT_STATE.md docs/prd_history/PRD-NNN.md docs/prd_index.json` returns ≥ 4 matches | Identify divergent file; re-patch |
| V11 | Working tree clean after final commit | Investigate untracked / unstaged remainder |
| V12 | No file outside the bookkeeping allowlist is staged or committed in any closeout commit | Stop; treat as scope violation |

Bookkeeping allowlist (V12):
- `docs/PRD_REGISTRY.md`
- `docs/PROJECT_STATE.md`
- `docs/prd_history/PRD-NNN.md`
- `docs/prd_index.json`

### Verification Report shape (must appear at end of every response)

```
## Verification Report
- V1 commit exists: [pass | fail — <hash> not found]
- V2 commit subject names PRD-NNN: [pass | fail — subject: "..."]
- V3 registry row: [COMPLETE @ <hash> | flipped from IN PROGRESS | missing — STOP]
- V4 PRD-NNN.md STATUS line: [present | appended]
- V5 prd_index.json entry: [present @ <hash> | added]
- V6 Last completed PRD line: [pass | patched]
- V7 Last work completed entry: [pass | added]
- V8 Active PRD: [none | <next PRD if user named one>]
- V9 Next step: [reset to idle | retained user-specified value]
- V10 four-way hash agreement: [pass | divergent in <file>]
- V11 working tree: [clean | unexpected: <list>]
- V12 scope: [pass | violation: <files>]
- Commits this turn: [hashes + subjects]
- Mode: [DRAFT_ONLY | WRITE_MODE]
```

## Tools

**Required:**

- `Read`, `Edit`, `Write`
- `Grep` (or `rg` via `Bash`)
- `Bash` (for `git`, `scripts/prd_close.sh`, file ops)

**Preferred:** none — closeout is mechanical; no GitNexus dependency.

**Optional:**

- `Agent(subagent_type: "Explore", model: "haiku")` only if the user
  asks for a multi-PRD closeout batch (≥3 PRDs in one turn); never for
  a single closeout — the work is too small.

## What this skill does NOT do

- Does not write the implementation commit. That happened earlier.
- Does not run tests. Test baseline must be supplied as input.
- Does not refresh dashboard/UI artifacts. Dashboard/UI artifact
  refresh, if required by the PRD, must be completed before closeout.
- Does not push to `origin`. Push is a separate, explicit action the
  user performs after this skill returns.
- Does not invoke Codex or Claude cross-review.
- Does not create a missing registry row.

## Failure modes to refuse

- Implementation commit not landed yet: refuse; instruct user to land
  it first.
- Test baseline not supplied: refuse; ask for the count.
- Working tree not clean at preflight: refuse; ask user to stash or
  commit existing work first.
- Registry row missing for PRD-NNN at preflight: refuse; report the
  bookkeeping inconsistency and stop.
- A staged or committed file in the closeout commit is outside the
  bookkeeping allowlist: refuse; this is a scope violation.
- User asks to skip Phase 2: refuse; verification is the point.
- User asks the skill to push: refuse; push is out of scope.
