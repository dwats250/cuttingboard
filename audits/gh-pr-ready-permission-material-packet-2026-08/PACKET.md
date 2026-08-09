# MATERIAL packet -- Agent PR-ready permission boundary (2026-08-08)

Deliberately tiny upstream MATERIAL packet for a one-line agent-permission
change. Classified MATERIAL by Dustin (2026-08-08) under GOV-2 section 1
("changes a governance guardrail"); LANE STANDARD (no validator-forced
HIGH-RISK -- `.claude/settings.json` is not a GOVERNANCE_PAYLOAD_FILE). Scope is
exactly one deny line; this packet is intentionally proportional and is NOT a
permissions redesign. The settings.json change is commit `66c2b27` on branch
`governance/allow-gh-pr-ready-draft-transition` (PR #234, DRAFT/held); this
packet rides the same branch (its own commit above the change).

## 1. CURRENT BOUNDARY
- `.claude/settings.json` `permissions.deny` contains `Bash(gh pr ready*)` --
  agents cannot mark a draft PR Ready for review.
- `.claude/settings.local.json` `permissions.allow` already contains
  `Bash(gh pr *)`, but **deny overrides allow** in Claude Code, so the deny
  wins for `gh pr ready` -- adding a local allow does nothing.
- The merge deny (`Bash(gh pr merge:*)`) and the gh-api mutation denies
  (`Bash(gh api -X*)`, `-f*`, `-F*`, `--field*`, `--method*`, `--raw-field*`,
  and the `* -X*` etc. variants) are **separate deny entries** -- unrelated to
  this line.

## 2. OBSERVED FRICTION
- Agents already prepare a branch, run proof/validation, drive review, and
  complete same-PR closeout (owner-authored Owner-Merge/Closeout Convention).
- Agents CANNOT transition a completed draft PR from Draft to Ready for review,
  so a fully-prepared PR cannot even reach the merge button without an owner UI
  action.
- This has recurred (blocked on PR #232 and PR #233 preparation) and tripped
  the campaign's recurring-friction rule; the Sol campaign review (Q10) flagged
  it explicitly.

## 3. PROPOSED CHANGE
Delete ONLY `Bash(gh pr ready*)` from `.claude/settings.json` `permissions.deny`.
Nothing else. (Diff: one deleted line; `deny` count 80 -> 79; JSON valid.)

## 4. AUTHORITY AFTER CHANGE
- **AGENT MAY:** transition an already-prepared PR between draft and ready. The
  enabled command `gh pr ready <n>` marks a draft Ready for review; its only
  other operation is `gh pr ready --undo <n>` (revert Ready back to draft).
  Under the reviewed `gh` 2.46.0 there is NO merge, close, or base-changing
  operation on `gh pr ready` -- the capability is bounded to the draft<->ready
  transition (both directions).
- **OWNER ONLY:** merge; enable auto-merge; any broader PR/API state mutation
  not separately authorized.

## 5. NEGATIVE BOUNDARY (state of the world after the change)
Unchanged by this one-line deletion:
- `Bash(gh pr merge:*)` deny -- REMAINS (merge stays owner-only).
- All `gh api` mutation denies (`-X`/`-f`/`-F`/`--field`/`--method`/
  `--raw-field`, incl. `* -X*` variants) -- REMAIN, so **PR title/body editing
  via `gh api` PATCH stays denied**; no gh-api broadening.
- `git checkout`/`switch`/`restore`/`reset`/`rebase`/`worktree`/`push --force`
  denies -- REMAIN.

PRE-EXISTING authorization, NOT introduced and NOT touched by this proposal
(recorded for accuracy, out of scope for this tiny packet): the local
`Bash(gh pr *)` allow already permits `gh pr edit` (which can change title,
body, and base) and `gh pr close` / `gh pr reopen`, with no matching deny; the
`gh api` denies do not gate those `gh pr` subcommands. `gh pr edit` currently
fails only on an unrelated GitHub `projectCards` API bug (a runtime error, not
a permission block). Tightening that pre-existing `gh pr *` breadth (e.g. a
narrow `gh pr edit`/`close`/`reopen` deny) is a SEPARATE decision; it is
deliberately NOT bundled here to keep this change one line.

## 6. FAILURE / REVERSION
- FAIL CONDITION: if removing the deny enables any behavior beyond the
  draft<->ready transition (including `--undo`) -- e.g. the glob
  `Bash(gh pr ready*)` (a `*` arbitrary-suffix matcher) turns out to have gated
  a command other than `gh pr ready`, or a future `gh` version adds a
  side-effectful `gh pr ready` flag -- STOP.
- BOUNDED ROLLBACK: restore the single deny line `"Bash(gh pr ready*)",` to
  `.claude/settings.json` `permissions.deny` -- one-line revert, no other state.

## MATERIALITY / GOVERNANCE PATH
MATERIAL (GOV-2 section 1, governance-guardrail change), owner-ruled. LANE
STANDARD (no GOVERNANCE_PAYLOAD_FILE touched; merge boundary untouched).
Sequence: this packet -> independent second-model review (Sol, per the standing
model-utilization ruling; via the Codex CLI) -> one correction cycle if needed
-> exact-corrected-head confirmation -> owner design-direction ruling ->
Stage-0 PRD -> fresh-context independent PRD review -> Gate A -> owner merge. No
PRD allocated and no Gate A at this stage.
