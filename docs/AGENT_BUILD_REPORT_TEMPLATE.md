# AGENT_BUILD_REPORT_TEMPLATE.md — Build Report Format

Every agent session that produces a commit must end with a build report in this format.
Omit empty sections. Never pad with filler.

---

## Build Report

```
PRD:              PRD-NNN — <title>
COMMIT:           <hash or "pending">
TEST_BASELINE:    <N> passing (before) → <M> passing (after)
LINT:             pass | fail
BUILD_STATUS:     CLEAN | DEGRADED
```

---

## Enforcement Summary

```
LOW_COST violations:          [count]
High-cost misclassifications: [count]
File over-reads:              [count]
Approval violations:          [count]
```

If any count > 0: set `BUILD_STATUS` to `DEGRADED` and complete the block below.

```
ROOT_CAUSE:        <which rule was violated and why>
CORRECTIVE_ACTION: <exact change to prevent recurrence>
```

**Violation definitions:**

| Metric | Increments when |
|---|---|
| LOW_COST violations | Agent prompted for approval on a LOW_COST read-only action (F9) |
| High-cost misclassifications | LOW_COST action triggered architecture reasoning or speculative output (F5) |
| File over-reads | File read in full before target symbol located via grep (F2), or same file re-read without new scope (F3) |
| Approval violations | Mutation auto-approved outside scoped files (F10), protected file bypassed (F11), or commit pushed without approval (F12) |

---

## Files Modified

List every file touched, with one-line description of the change.

```
<file path>    — <what changed>
```

---

## Requirements Delivered

| Req | Description | Status |
|---|---|---|
| R1 | ... | PASS / FAIL |
| R2 | ... | PASS / FAIL |

---

## Fail Conditions Verified

List each PRD FAIL condition and its observed outcome.

```
FAIL: <condition text>    → VERIFIED PASS / TRIGGERED (describe)
```

---

## Auto-Approved Actions

All LOW_COST actions that executed without approval prompts.

```
- grep <pattern> <file>
- git status
- pytest -k <pattern>
- Read <file> (lines N–M)
- ...
```

---

## Approval-Gated Actions

Actions that required and received explicit user approval before executing.

```
- Edit <file> — <reason approval was required>
- ...
```

---

## Risks / Notes

Any HIGH or CRITICAL impact warnings encountered, deferred work, or scope boundary decisions.

```
<note>
```

---

## Milestone Snapshot

```
Latest completed PRD:  PRD-NNN
Active PRD:            none | PRD-NNN
Test baseline:         <N> passing
Next PRD slot:         PRD-NNN
```
