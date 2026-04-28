# Claude Code Hooks — Workflow Reference

Hooks are shell scripts triggered by Claude Code lifecycle events.  They
enforce mechanical constraints that cannot be left to judgment: commit gating,
file protection, test coverage, and state capture.

---

## Hook Overview

| Script | Event | Trigger | Blocks? |
|---|---|---|---|
| `git_gate.sh` | PreToolUse/Bash | Any Bash call containing `git commit` or `git push` | Yes |
| `protect_files.sh` | PreToolUse/Write + Edit | Write or Edit to a protected path | Yes |
| `test_gate.sh` | PostToolUse/Write + Edit | Write or Edit to `cuttingboard/*.py` or `tests/*.py` | On failure |
| `stop_snapshot.sh` | Stop | Session end or compaction | No |

---

## git_gate.sh — Commit/Push Gate

**What it does:** Intercepts every Bash tool call and blocks any command
containing `git commit` or `git push`.

**Approval override:** The hook reads the session transcript and searches
user-role messages for the exact phrase `APPROVE COMMIT`.  If found, the
command is allowed.  If not found, the hook exits non-zero and prints an
explanation.

**Dirty repo guard (R5):** Before checking for approval, the hook runs
`git status --short` and compares dirty/untracked files against the FILES
section of the active PRD.  If unrelated files are dirty, the hook blocks
and lists them — even if `APPROVE COMMIT` is present.

**To approve a commit or push:**
1. Confirm tests pass and the repo is clean of unrelated files.
2. Type exactly `APPROVE COMMIT` in the chat.
3. Claude will retry the commit or push.

**State files read:**
- `.claude/state/active_prd.txt` — to resolve the active PRD for dirty file comparison
- Session transcript at `transcript_path` — to find `APPROVE COMMIT`

---

## protect_files.sh — Protected File Guard

**What it does:** Intercepts Write and Edit tool calls.  If the target path
matches a protected pattern, it checks whether the path is listed in the
active PRD's FILES section.  If not listed, it blocks.

**Protected patterns:**
- `.env` and `.env.*`
- `.git/*`
- `*.lock`
- `.github/workflows/*`
- `secrets*`

**Fail-closed behavior:** If `.claude/state/active_prd.txt` is missing or
empty, the hook blocks the write regardless of which file is targeted.

**State files read:**
- `.claude/state/active_prd.txt` — resolves the active PRD document

---

## test_gate.sh — Pytest Gate

**What it does:** After any Write or Edit tool call, checks if the modified
path matches `cuttingboard/*.py` or `tests/*.py`.  If it matches, runs
`.venv/bin/pytest -q tests/` and emits results.

**Debounce:** If pytest ran within the last 10 seconds (tracked in
`.claude/state/pytest_last_run`), the hook skips the run and prints the
elapsed time.  This prevents duplicate runs from rapid sequential edits.

**On failure:** The hook exits non-zero and prints a summary.  Implementation
must not proceed to commit approval while tests are failing.

**State files written:**
- `.claude/state/pytest_last_run` — epoch timestamp of last pytest run

---

## stop_snapshot.sh — State Snapshot

**What it does:** On session Stop, writes `.claude/state/snapshot.json`
capturing the current task state.  At session start or after compaction,
Claude reads this file and restores context.

**Snapshot fields:**

| Field | Source |
|---|---|
| `active_prd` | `.claude/state/active_prd.txt` or `"none"` |
| `branch` | `git rev-parse --abbrev-ref HEAD` |
| `commit` | `git rev-parse --short HEAD` |
| `timestamp` | Current UTC time (ISO 8601) |
| `next_action` | `.claude/state/next_action.txt` or `"unknown"` |

**State files read:**
- `.claude/state/active_prd.txt`
- `.claude/state/next_action.txt`

**State files written:**
- `.claude/state/snapshot.json`

---

## State File Conventions

All runtime state lives under `.claude/state/`.  These files are not
committed to git.

| File | Written by | Read by | Purpose |
|---|---|---|---|
| `active_prd.txt` | Claude (on PRD approval) | `protect_files.sh`, `git_gate.sh`, `stop_snapshot.sh` | Identifies the active PRD |
| `next_action.txt` | Claude (at session end) | `stop_snapshot.sh` | Next required action after restore |
| `pytest_last_run` | `test_gate.sh` | `test_gate.sh` | Debounce timestamp |
| `snapshot.json` | `stop_snapshot.sh` | Claude (on session start) | Full task state restore |

**active_prd.txt format:** Single line, exactly `PRD-XXX`.  Written by Claude
immediately after Dustin approves a PRD for implementation.

---

## Manual Commit/Push Workflow

1. Implementation complete, all tests pass.
2. Claude runs `git status --short` and confirms no unrelated dirty files.
3. Claude states implementation is complete and asks for approval.
4. Dustin types `APPROVE COMMIT` in the chat.
5. Claude runs `git add` for scoped files, then `git commit`.
6. Dustin types `APPROVE COMMIT` again (or in the same session) for push.
7. Claude runs `git push`.

Claude must not attempt step 5 or 7 without the `APPROVE COMMIT` phrase
appearing in a user message in the current session.
