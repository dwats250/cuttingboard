---
name: scope-lock-precommit
description: Use before any PRD-scoped commit to verify staged files match the active PRD's FILES section. Catches scope-lock violations (the PRD-136 mid-implementation amendment pattern) before they land. Reads the active PRD from PROJECT_STATE.md, parses its FILES section, diffs against `git diff --cached --name-only`, and refuses commit when staged files fall outside FILES or the bookkeeping allowlist. Triggers on "scope check", "verify scope", "commit PRD-NNN", "stage and commit", or as a pre-commit gate.
---

# Scope-Lock Pre-Commit

## Scope and boundary

This skill does two things and only two things:

1. **Detect** every file currently staged (`git diff --cached`).
2. **Verify** each staged file is permitted by the active PRD's
   `FILES` section, the bookkeeping allowlist, or the LANE policy.

It is NOT a substitute for:

- The implementation review itself
- Test-pass verification
- The cross-review gate

This is a *mechanical scope gate*, not a code reviewer.

## When to trigger

- "Scope check before commit"
- "Verify scope for PRD-NNN"
- "Commit PRD-NNN" / "stage and commit" — run scope check first
- After staging files, before invoking `git commit`

Do NOT trigger for:
- A non-PRD commit (the active PRD is `none`)
- The bookkeeping commit produced by `prd-closeout-verified`
  (closeout has its own V12 allowlist)
- A merge or revert commit

## Operating modes

Default is **CHECK_ONLY**.

- **CHECK_ONLY** — run the diff, emit the Verification Report, do not
  commit. Recommended default.
- **CHECK_AND_COMMIT** — run the check; if it passes, commit with the
  user-supplied message. If any V check fails, refuse to commit and
  surface the violation. The user must supply the commit message; the
  skill never invents one.

If unclear, ask once, then default to CHECK_ONLY.

## Inputs required

- `prd` — three-digit PRD number, OR `auto` to read from
  `PROJECT_STATE.md` `**Active PRD:**` line.
- `message` (CHECK_AND_COMMIT only) — exact commit message string.
  Never inferred.

If `prd: auto` resolves to `none`, refuse and ask for an explicit
PRD number — this skill is PRD-scoped.

## Hard rule: no invented references

The skill must never invent:

- The active PRD number (must come from PROJECT_STATE or user)
- A `FILES` entry "the PRD probably meant to include"
- The bookkeeping allowlist (it is fixed; see below)
- The protected pipeline set (it is read dynamically; see below)
- A commit message

If the active PRD's `FILES` section cannot be parsed (malformed,
missing, ambiguous), stop and report. Do not guess at coverage.

## FILES parsing rule

Parse the `FILES` section of `docs/prd_history/PRD-NNN.md` literally:

- Collect every line matching `` ^- `<path>` `` under both
  `Modified:` and `New:` subheadings (paths in backticks).
- Strip backticks. Reject any line whose path contains a glob
  wildcard (`*`, `?`, `[`) — the FILES section is a literal list.
- Treat the parenthetical `(PRD-NNN row)` / `(active PRD pointer)`
  annotations as comments; the path before them is the entry.

If `New:` is empty or absent, only `Modified:` entries apply.

## Bookkeeping allowlist (always permitted)

Independent of the PRD's FILES section, these are always permitted in
a PRD-scoped commit because they are governance bookkeeping:

- `docs/PRD_REGISTRY.md`
- `docs/PROJECT_STATE.md`
- `docs/prd_history/PRD-NNN.md` (only the active PRD's file)

Note: `docs/prd_index.json` is **closeout-only**; if it appears in a
non-closeout commit, that is a violation.

## Protected pipeline set (dynamic, fail-closed)

This skill does NOT carry an inline copy of the protected pipeline
set. It would drift. Instead, at runtime:

1. Read `docs/AGENT_WORKFLOW.md`.
2. Locate the `## Auto-Approval Policy` (or `§ Auto-Approval Policy`)
   section.
3. Parse the protected-file list defined there verbatim. Apply that
   list — and nothing else — as the protected pipeline set for V7.

Fail-closed rules:

- If `docs/AGENT_WORKFLOW.md` cannot be read, refuse all V7
  evaluation and stop the skill. Do not silently allow staged files
  through.
- If the `Auto-Approval Policy` section cannot be located or its
  protected list cannot be parsed unambiguously, refuse and stop. Do
  not guess the protected set.
- If the parsed set is empty, refuse and stop. An empty protected set
  is almost certainly a parse failure, not a policy state.

The skill must never duplicate the protected list inside this file.
The single source of truth is `docs/AGENT_WORKFLOW.md`.

V7 applies the parsed set against the staged file set. If
`LANE: HIGH-RISK` is declared in the active PRD header, staged files
in the protected set are permitted; otherwise they are a violation —
with ONE exception (PRD-229 Cosmetic Carve-Out,
`docs/PRD_PROCESS.md`): a `LANE: MICRO` PRD/note that declares itself
cosmetic-only admits protected-set files IFF the staged diff for each
such file is provably cosmetic — ui copy/CSS/layout hunks in
presentation code, or comment/docstring-only hunks (zero
executable-line delta; verify with `git diff --cached` on the file,
not the PRD's claim). Any staged hunk outside those forms voids the
exception for the whole commit: escalate the lane or split.

## Two-phase contract

### Phase 1 — Detect

1. Resolve active PRD number (input or `PROJECT_STATE.md`).
2. Read `docs/prd_history/PRD-NNN.md`, parse `FILES` section.
3. Read PRD header to determine `LANE`.
4. Read `docs/AGENT_WORKFLOW.md` and parse protected pipeline set.
5. Run `git diff --cached --name-only`.
6. For each staged file, classify as:
   - `in_files` — listed in PRD `FILES`
   - `bookkeeping` — in the bookkeeping allowlist above
   - `protected_pipeline` — in the dynamically-parsed protected set
   - `logs_or_reports` — under `logs/` or `reports/`
   - `out_of_scope` — none of the above

### Phase 2 — Verify (MANDATORY before returning)

| # | Check | Action on failure |
|---|---|---|
| V1 | Active PRD resolved (not `none`) | Stop; ask for PRD |
| V2 | `docs/prd_history/PRD-NNN.md` exists and FILES section parses | Stop; report parse error |
| V3 | LANE header present | Stop; PRD is malformed |
| V4 | At least one file is staged | Stop; nothing to check |
| V5 | Every staged file classified `in_files` or `bookkeeping` | Refuse commit; list `out_of_scope` |
| V6 | No staged file classified `logs_or_reports` | Refuse commit; list offenders |
| V7 | Protected pipeline set parsed successfully from `docs/AGENT_WORKFLOW.md`; no staged file classified `protected_pipeline` unless `LANE: HIGH-RISK` | Refuse commit; suggest lane escalation OR remove file. If protected set cannot be parsed, fail closed — refuse all commits. |
| V8 | `docs/prd_index.json` not staged (unless invoked by closeout skill) | Refuse commit; closeout-only |
| V9 | If CHECK_AND_COMMIT: working tree clean apart from staged set | Refuse; investigate unstaged remainder |

### Verification Report shape

```
## Verification Report
- V1 active PRD: PRD-NNN (source: [PROJECT_STATE | user])
- V2 FILES parse: [<count> entries | error: <message>]
- V3 LANE: [MICRO | STANDARD | HIGH-RISK]
- V4 staged file count: [N]
- V5 in-scope: [<files>] | out-of-scope: [<files or none>]
- V6 logs/reports staged: [none | <files>]
- V7 protected pipeline set: [parsed N entries from docs/AGENT_WORKFLOW.md | PARSE FAILED — FAIL CLOSED]
       protected staged: [none | <files> — LANE policy: <result>]
- V8 prd_index.json staged: [no | YES — VIOLATION]
- V9 working tree clean apart from staged: [pass | n/a — CHECK_ONLY]
- Mode: [CHECK_ONLY | CHECK_AND_COMMIT]
- Action: [report only | committed <hash> | REFUSED — <reason>]
```

## Tools

**Required:**
- `Read`, `Bash` (for `git`)
- `Grep` / `rg` for FILES-section and Auto-Approval-Policy parsing

**Optional:**
- `Edit` only in CHECK_AND_COMMIT mode (to invoke commit — actually
  done via `Bash: git commit`, no file edits)

No GitNexus dependency. No subagent dispatch — single PRD, small diff.

## What this skill does NOT do

- Does not stage files. Staging is the user's decision.
- Does not amend PRD FILES section. If the staged set genuinely
  requires a file not in FILES, the user amends the PRD first (per
  CLAUDE.md `Strict scope locking`), then re-runs this skill.
- Does not duplicate or override `docs/AGENT_WORKFLOW.md`. The
  protected pipeline set is read dynamically each invocation.
- Does not run tests, lint, or any quality gate other than scope.
- Does not push.
- Does not auto-escalate LANE.

## Failure modes to refuse

- Active PRD is `none`: refuse; this skill is PRD-scoped.
- FILES section unparseable or missing: refuse; PRD is malformed.
- LANE header missing: refuse; PRD is malformed per PRD-121.
- `docs/AGENT_WORKFLOW.md` unreadable or Auto-Approval Policy
  unparseable: refuse all commits (fail closed).
- Out-of-scope file staged: refuse commit; require PRD amendment or
  unstage.
- `logs/*` / `reports/*` staged: refuse; CLAUDE.md hygiene rule.
- Protected pipeline file staged without HIGH-RISK lane: refuse.
- User asks to skip Phase 2: refuse; verification is the point.
- User asks the skill to bypass V7 because "the protected list looks
  wrong": refuse; fix the policy doc, then re-run.
