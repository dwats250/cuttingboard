# AGENT_SESSION_BOOTSTRAP.md — Session Startup Sequence

Defines the mandatory sequence every agent session must execute before touching any code.
Failure to complete this sequence is a scope violation.

---

## Mandatory Startup Steps

Execute in order. Do not skip.

```
1. Read docs/PROJECT_STATE.md         — active PRD, test baseline, architecture notes
2. Read active PRD (PRD-NNN.md)       — scope, FILES, requirements, fail conditions
3. gitnexus_context / gitnexus_query  — locate affected modules and direct consumers
4. Confirm PRD FILES boundary         — list every file in scope before any edit
5. Confirm test baseline              — record the passing count from PROJECT_STATE.md
```

If there is no active PRD, stop at step 1 and report "no active PRD — awaiting assignment."

---

## Auto-Approval Policy (summary)

LOW_COST actions execute without prompting for approval.
Full policy and protected file list: `docs/AGENT_WORKFLOW.md § Auto-Approval Policy`.

**LOW_COST (auto-approved):**
- grep / find / ls / git status / git diff / git log
- Read targeted snippets (offset + limit, in-scope files only)
- Symbol inspection via gitnexus tools
- Targeted pytest -k runs; full pytest suite (pre-commit only)
- Lint / format checks
- Create or update documentation files
- Mechanical edits to files already in PRD FILES scope

**Always stop for approval:**
- Any edit to: runtime.py, contract.py, execution_policy.py, payload/notification/dashboard/trading logic
- Environment, secrets, CI, dependency files
- Destructive commands, file deletion, git push
- Changes to test expectations unless explicitly approved
- Any action outside PRD FILES scope

---

## Pre-Edit Checklist

Before writing or editing any file:

- [ ] File is listed in active PRD FILES section
- [ ] `gitnexus_impact` has been run on the target symbol
- [ ] Impact risk level is not HIGH or CRITICAL (or user has approved)
- [ ] Blast radius has been reported

---

## Pre-Commit Checklist

Before requesting commit approval:

- [ ] Full `pytest` suite passes (matches or exceeds baseline)
- [ ] `git status` is clean (only PRD-scoped files modified)
- [ ] `gitnexus_detect_changes()` output reviewed — no unexpected symbols changed
- [ ] Build report drafted (use `docs/AGENT_BUILD_REPORT_TEMPLATE.md`)

---

## Failure Conditions

| FAIL | Condition |
|---|---|
| FAIL | Session begins without reading PROJECT_STATE.md |
| FAIL | Code is touched before active PRD is read |
| FAIL | File edited that is not listed in PRD FILES section |
| FAIL | gitnexus_impact skipped before symbol edit |
| FAIL | Commit requested without full pytest pass |
