# gh pr * permission-surface audit (2026-08)

Read-only permission-boundary audit commissioned by Dustin's PR #234
design-direction ruling (2026-08-08), SEPARATE FINDING section. Records the
pre-existing `Bash(gh pr *)` local-allow breadth as its own finding. This
audit is NOT part of PRD-291, is NOT a prerequisite for it, edits NO settings,
and authorizes nothing. Any tightening it proposes is its own later
governance/materiality decision (owner ruling).

## Method
- gh CLI: **2.46.0** (the pinned/reviewed version). Subcommand inventory read
  from `gh pr --help`; mutation flags read from `gh pr edit --help` /
  `gh pr review --help` (all read-only).
- Effective permission set per CLAUDE.md = `.claude/settings.json` UNION
  `.claude/settings.local.json`, deny-overrides-allow. Verified state:
  - `.claude/settings.local.json`: 437 allow / 0 deny; contains the broad
    `Bash(gh pr *)` allow and no offsetting `gh pr` deny.
  - `.claude/settings.json`: holds every `gh pr`-affecting DENY.
- Matching-semantics assumption (flagged, not proven here): `Bash(cmd:*)`
  denies `cmd <anything>` (prefix form), and `Bash(gh pr *)` allows any
  `gh pr <suffix>`. The exact glob behavior for interior flags (e.g.
  `gh pr edit* --base*`) should be tested before any tightening relies on it.

## The gh pr surface vs the current deny carve-outs
Tracked `gh pr` denies: `Bash(gh pr merge:*)`, `Bash(gh pr *-w*)`,
`Bash(gh pr *--web*)`, `Bash(gh pr *http*)`, and the cross-repo guards
`Bash(gh -R*)` / `Bash(gh * -R*)` / `Bash(gh --repo*)` / `Bash(gh * --repo*)`.
Everything else under `gh pr` is reachable through the broad local allow.

| gh pr subcommand | effect | reachable now? | note |
|---|---|---|---|
| merge | merge PR | **NO** | `Bash(gh pr merge:*)` deny — owner-only, correct |
| create | open PR | yes | needed; also explicitly allowed |
| list / status / view / diff / checks | read | yes | needed reads |
| comment | post PR comment | yes | needed (PRD-228 thread disposition, closeout) |
| ready [--undo] | draft<->ready | yes (after PRD-291) | this PRD's grant |
| edit | title / body / **base** / labels / reviewers / assignees / milestone / projects | yes | metadata needed; **--base is consequential** |
| review | **--approve** / --request-changes / --comment | yes | **approving undercuts the review gate** |
| close | close PR | yes | consequential lifecycle state |
| reopen | reopen PR | yes | consequential lifecycle state |
| lock / unlock | lock/unlock conversation | yes | moderation authority |
| checkout | switch local worktree to PR branch | yes | **bypasses the `git *checkout*` deny** |

## Determination 1 - meaningful mutations reachable via Bash(gh pr *)
create, comment, ready, edit (incl. `--base`), review (incl. `--approve`),
close, reopen, lock, unlock, checkout. (merge is NOT reachable — denied.)

## Determination 2 - what the agent workflow intentionally needs
- create (open the PR)
- comment (bot-review-thread disposition per PRD-228; closeout notes)
- ready [--undo] (DRAFT->Ready, PRD-291)
- edit **metadata only** (title/body) — PR-metadata hygiene under the
  Owner-Merge/Closeout Convention
- reads: view / list / status / diff / checks
Nothing in the workflow needs review/close/reopen/lock/unlock/edit-`--base`/
checkout.

## Determination 3 - owner-only by doctrine
Doctrine: "Agents may prepare a PR; Dustin owns consequential landing/state
authority" (GOV-1; Owner-Merge/Closeout Convention).
- merge — already owner-only (denied). Correct.
- review `--approve` / `--request-changes` — approving/gating a PR is review
  authority; an agent approving a PR (potentially one it authored) defeats the
  fresh-context review gate. Owner-only.
- close / reopen — PR lifecycle state. Owner-only.
- edit `--base` — changes the merge-target base branch. Owner-only.
- lock / unlock — conversation moderation. Owner-only.
- checkout — not "landing" authority, but a local-worktree mutation that
  bypasses the deliberate `git checkout` deny; gate it for the same reason
  that deny exists.

## Determination 4 - can the wildcard become a bounded explicit allow without recreating friction?
YES. The real needs (Determination 2) are a small enumerable set. Replace the
single `Bash(gh pr *)` local allow with an explicit tracked allow-list of
exactly those verbs plus explicit denies for the owner-only verbs. The
recurring friction this campaign hit was caused by a DENY on a needed command
(`gh pr ready`), not by the absence of a wildcard; a COMPLETE explicit allow
avoids re-introducing that. Residual friction risk is under-granting (a needed
verb omitted), not over-restricting — mitigated by enumerating from the actual
workflow.

## Determination 5 - minimal proposed target surface (PROPOSAL ONLY)
A future tightening (its own governance/materiality decision) could:

Remove from `.claude/settings.local.json`:
- `Bash(gh pr *)`

Explicit ALLOW (tracked `.claude/settings.json`) — [P] already present:
- `Bash(gh pr create:*)` [P]
- `Bash(gh pr view:*)` [P]
- `Bash(gh pr list *)` [P]
- `Bash(gh pr diff *)` [P]
- `Bash(gh pr checks:*)` [P]
- `Bash(gh pr status:*)` [add]
- `Bash(gh pr ready:*)` [add — an explicit bounded allow that would SUPERSEDE
  PRD-291's deny-removal, replacing an implicit-via-wildcard grant with an
  explicit one]
- `Bash(gh pr comment:*)` [add]
- `Bash(gh pr edit:*)` [add] paired with the base carve-out deny below

Explicit DENY (tracked), keep [K] / add:
- `Bash(gh pr merge:*)` [K]
- `Bash(gh pr review*)` [add]
- `Bash(gh pr close*)` [add]
- `Bash(gh pr reopen*)` [add]
- `Bash(gh pr lock*)` [add]
- `Bash(gh pr unlock*)` [add]
- `Bash(gh pr checkout*)` [add — close the git-checkout bypass]
- `Bash(gh pr edit* --base*)` [add — block base change, allow metadata edit;
  verify matcher semantics first per the Method caveat]
- keep existing `-w`/`--web`/`http` and `-R`/`--repo` guards

## Notes / caveats
- **settings.local.json is the sole source of the breadth.** Any tightening
  MUST remove the local `Bash(gh pr *)` wildcard; adding tracked denies alone
  leaves the wildcard granting everything the deny does not explicitly carve.
- **`gh pr checkout` is a live bypass** of the `git *checkout*` deny today.
- **`gh pr edit`** currently fails at runtime on an unrelated GitHub
  `projectCards` API bug, not a permission block — so the metadata-hygiene use
  is permitted-but-broken, independent of this audit.
- This audit **authorizes nothing** and is **not a prerequisite for PRD-291**.
