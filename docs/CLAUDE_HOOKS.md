# Claude Code Hooks - Workflow Reference

The hooks wired for this repo and what each actually does. Wiring lives in
`.claude/settings.json`; scripts live in `.claude/hooks/`. This documents the
hooks that are live, not every script that has ever existed.

## Wired hooks

| Script | Event | Trigger | Blocks? |
|---|---|---|---|
| `protect_files.sh` | PreToolUse / Write + Edit | Write or Edit to a protected path | Yes |
| `prd_eval.sh` | UserPromptSubmit | Every prompt; acts when it references a PRD | No (injects context) |
| `canonical_read_guard.sh` | PreToolUse / Read | Read of repo-root CLAUDE.md or auto-memory MEMORY.md | No (warns; allows) |

There is also a git-level `.git/hooks/pre-commit` (installed by
`scripts/install_hooks.sh`) that runs `scripts/pre_commit_sanity.sh` -
**informational only, does not block.** Bypass with `git commit --no-verify`.

## protect_files.sh - protected-file guard

This is the real backstop. `.claude/settings.json` auto-approves `Write` and
`Edit`, so this hook is the only thing standing between an accidental edit and a
secret, env file, or CI workflow.

**What it does:** intercepts Write/Edit. If the target path matches a protected
pattern, the write is blocked unless that exact path is listed in the active
PRD's `FILES` section. **Non-protected paths pass through untouched** - ordinary
`docs/` and source edits are not gated by this hook.

**Protected patterns:** the hook's own hardcoded hard-block subset - see the
script header in `.claude/hooks/protect_files.sh` for the literal list
(secrets/env, `.git/*`, lockfiles, workflow files). This is deliberately
NARROWER than the "Never auto-approve" policy table in
`docs/AGENT_WORKFLOW.md`, which is the broad review-policy surface (runtime,
contract, dashboard, trading logic, CI, push) that PRD lanes and skills
enforce. Two scopes by design (PRD-230): the hook is the mechanical last line
for catastrophic writes; AGENT_WORKFLOW.md is the policy boundary. Do not
"sync" one list to the other.

**Fail-closed:** for a protected path, if `.claude/state/active_prd.txt` is
missing or empty the write is blocked. This applies only to protected paths - it
does not block all writes.

## prd_eval.sh - PRD review + sequencing gate

Fires on every prompt; injects context only, never blocks a tool call. When the
prompt contains a PRD body it injects the PRD-review structure; when it is an
implementation request for a non-sequential PRD it injects a sequencing gate;
and it flags any `prd_history/*.md` file missing a registry row.

## canonical_read_guard.sh - redundant canonical-doc re-read reminder

Fires on every `Read`. When the target is the repo-root `CLAUDE.md` or the
auto-memory `MEMORY.md` - both injected into the system prompt at session start -
it returns a non-blocking `permissionDecision: allow` plus an `additionalContext`
reminder that re-reading is redundant. The Read still proceeds; the hook never
blocks. All other paths pass through with no output. `PROJECT_STATE.md`,
`DECISIONS.md`, and the registry/index are deliberately NOT guarded: they change
mid-session, so re-reads can be legitimate (PRD-201).

## State files

Under `.claude/state/` (gitignored, not committed):

| File | Written by | Read by | Purpose |
|---|---|---|---|
| `active_prd.txt` | you, on PRD approval | `protect_files.sh` | The active PRD id (`PRD-NNN`, or `none`) |

## Commit / push

Commit and push gating is handled by the harness's native permission model, not
a hook: `.claude/settings.json` denies `git push` outright, and mutating
commands prompt for approval. (An older `git_gate.sh` "APPROVE COMMIT" hook was
retired as redundant with this.)
