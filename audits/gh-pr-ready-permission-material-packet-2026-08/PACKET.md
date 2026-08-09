# MATERIAL packet -- Agent PR-ready permission boundary (2026-08-08)

Deliberately tiny upstream MATERIAL packet for a one-line agent-permission
change. Classified MATERIAL by Dustin (2026-08-08) under GOV-2 section 1
("changes a governance guardrail"); LANE STANDARD (no validator-forced
HIGH-RISK -- `.claude/settings.json` is not a GOVERNANCE_PAYLOAD_FILE). Scope is
exactly one deny line; this packet is intentionally proportional and is NOT a
permissions redesign. Change staged on branch
`governance/allow-gh-pr-ready-draft-transition` (PR #234, DRAFT/held), head
`66c2b27`.

## 1. CURRENT BOUNDARY
- `.claude/settings.json` `permissions.deny` contains `Bash(gh pr ready*)` --
  agents cannot mark a draft PR Ready for review.
- `.claude/settings.local.json` `permissions.allow` already contains
  `Bash(gh pr *)`, but **deny overrides allow** in Claude Code, so the deny
  wins -- adding a local allow does nothing.
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
- **AGENT MAY:** mark an already-prepared draft PR Ready for review
  (`gh pr ready <n>`; the command performs only the draft<->ready transition).
- **OWNER ONLY:** merge; enable auto-merge; any broader PR/API state mutation
  not separately authorized.

## 5. NEGATIVE BOUNDARY (confirm unchanged by the change)
- `Bash(gh pr merge:*)` deny -- REMAINS (merge stays owner-only).
- All `gh api` mutation denies (`-X`/`-f`/`-F`/`--field`/`--method`/
  `--raw-field`, incl. `* -X*` variants) -- REMAIN (PR title/body editing stays
  owner/UI-only; no gh-api broadening).
- `git checkout`/`switch`/`restore`/`reset`/`rebase`/`worktree`/`push --force`
  denies -- REMAIN.
- PR title/body update -- REMAINS owner/UI-only (unchanged).

## 6. FAILURE / REVERSION
- FAIL CONDITION: if the removed deny enables any behavior beyond the
  draft->ready transition (e.g. `gh pr ready` turned out to accept a
  merge/close/base side effect, or the glob over-matched another command),
  STOP.
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
