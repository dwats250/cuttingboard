# Claude Code Hooks - Workflow Reference

The hooks wired for this repo and what each actually does. Wiring lives in
`.claude/settings.json`; scripts live in `.claude/hooks/`. This documents the
hooks that are live, not every script that has ever existed.

## Wired hooks

| Script | Event | Trigger | Blocks? |
|---|---|---|---|
| `protect_files.sh` | PreToolUse / Write + Edit | Write or Edit to a protected path | Yes |
| `prd_eval.sh` | UserPromptSubmit | Prompt references a PRD AND an unregistered prd_history file exists | No (injects context) |
| `canonical_read_guard.sh` | PreToolUse / Read | Read of repo-root CLAUDE.md or auto-memory MEMORY.md | No (warns; allows) |

There is also a git-level `.git/hooks/pre-commit` (installed by
`scripts/install_hooks.sh`) that runs `scripts/pre_commit_sanity.sh` -
**informational only, does not block.** Bypass with `git commit --no-verify`.

## protect_files.sh - protected-file guard

This is the real backstop. `.claude/settings.json` auto-approves `Write` and
`Edit`, so this hook is the only thing standing between an accidental edit and a
secret, env file, or CI workflow.

**What it does:** intercepts Write/Edit. If the target path matches a protected
pattern, the write is blocked **unconditionally** (PRD-254) - no PRD, FILES
entry, or state file can allow it through. **Non-protected paths pass through
untouched** - ordinary `docs/` and source edits are not gated by this hook.

**Protected patterns:** the hook's own hardcoded hard-block subset - see the
script header in `.claude/hooks/protect_files.sh` for the literal list
(secrets/env, `.git/*`, lockfiles, workflow files). This is deliberately
NARROWER than the "Never auto-approve" policy table in
`docs/AGENT_WORKFLOW.md`, which is the broad review-policy surface (runtime,
contract, dashboard, trading logic, CI, push) that PRD lanes and skills
enforce. Two scopes by design (PRD-230): the hook is the mechanical last line
for catastrophic writes; AGENT_WORKFLOW.md is the policy boundary. Do not
"sync" one list to the other.

**Why unconditional, not PRD-gated (PRD-254):** before PRD-254, a protected
path was writable if the active PRD's `FILES` section listed it - but that
allow-path never once fired in this repo's history, and the hook only ever
intercepted the `Write`/`Edit` tools. A protected-file write via `Bash`
(`sed -i`, a heredoc) was never caught either way, so the sanctioned path was
decorative. PRD-254 removed it rather than fix it: the hook now blocks every
protected-path match through Write/Edit, full stop.

**The matcher is deliberately not extended to `Bash` (PRD-254, decided, not
deferred).** The hook catches accidents, not intent. Nobody accidentally
`sed -i`'s a protected file; a PRD that genuinely needs to touch one does it
through Bash today and did before this change too. Extending the matcher to
Bash would add a knob chasing a threat model this project doesn't have -
recorded here so a future audit doesn't re-find it as a gap.

## prd_eval.sh - registry-gap check

Fires on every prompt; injects context only, never blocks a tool call. Its
single remaining job: when the prompt mentions a PRD, flag any
`prd_history/*.md` file missing a registry row (review/adjudication/
codex-prompt/impl-notes sidecars excluded). Output is empty unless a real
gap exists.

The former keyword detectors (PRD-body review-mode injection, non-sequential
implementation gate) were retired by PRD-243: they had no channel
discrimination and misfired on subagent task notifications (six times in one
audited session), and their sequencing concern is enforced where truth is
determined — `tools/validate_prd_registry.py` on the CI merge path (PRD-200)
with same-PR closeout (PRD-229). The 108→143→145 exclusion-list repair chain
was this detector's false-positive class regenerating.

## canonical_read_guard.sh - redundant canonical-doc re-read reminder

Fires on every `Read`. When the target is the repo-root `CLAUDE.md` or the
auto-memory `MEMORY.md` - both injected into the system prompt at session start -
it returns a non-blocking `permissionDecision: allow` plus an `additionalContext`
reminder that re-reading is redundant. The Read still proceeds; the hook never
blocks. All other paths pass through with no output. `PROJECT_STATE.md`,
`DECISIONS.md`, and the registry/index are deliberately NOT guarded: they change
mid-session, so re-reads can be legitimate (PRD-201).

## Commit / push

Commit and push gating is handled by the harness's native permission model, not
a hook: `.claude/settings.json` allows plain `git push` but denies the three
force-push forms (`--force`, `--force-with-lease`, `-f`) outright, and other
mutating commands prompt for approval. (An older `git_gate.sh` "APPROVE COMMIT"
hook was retired as redundant with this.)
