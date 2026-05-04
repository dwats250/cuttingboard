# PRD Process

Rules and lifecycle for all PRDs in the cuttingboard decision engine.

---

## Lifecycle States

| State | Meaning |
|-------|---------|
| PROPOSED | Drafted. Not approved for implementation. |
| IN PROGRESS | File exists in prd_history/. Implementation has begun. |
| COMPLETE | Implementation merged. Commit hash recorded in registry. |
| PATCH | Corrective PRD targeting a specific defect in a prior PRD. |
| DEPRECATED | Requirement superseded or withdrawn before completion. |

No other status values are permitted in PRD_REGISTRY.md.

---

## Rules

### File Existence
A PRD is not active until a file exists at `docs/prd_history/PRD-NNN.md`.
Create the file with status `IN PROGRESS` before writing any implementation code.

### Template
All PRDs MUST be created from `docs/PRD_TEMPLATE.md`.
Section names and order MUST NOT deviate:
`GOAL → SCOPE → OUT OF SCOPE → FILES → REQUIREMENTS → DATA FLOW → FAIL CONDITIONS → VALIDATION`

### Scope Compression

Keep PRDs under 100 lines total. To stay within that limit:

- Write one `FAIL:` line per requirement, not multiple. If a requirement needs more than one FAIL line, split the requirement.
- `OUT OF SCOPE` and `FAIL CONDITIONS` sections must not repeat each other. OUT OF SCOPE states what won't be built; FAIL CONDITIONS state what breaks the build. Do not copy the same point into both.
- `VALIDATION` steps are acceptance criteria, not a third restatement of requirements. Write steps only, not explanations.
- `DATA FLOW` should be one short paragraph or a numbered list under 6 items. Not prose.

If a draft exceeds 100 lines, identify which FAIL lines restate the requirement body and remove the duplicates before implementation starts.

---

### Per-Requirement Fail Conditions
Every requirement (R1, R2, ...) MUST include an inline `FAIL:` line.
FAIL lines MUST be:
- Observable — a human or script can confirm it
- Binary — pass or fail, no partial states
- Non-subjective — no words like "unclear", "poor", or "insufficient"

### Scope Lock
The `FILES` section defines a hard boundary.
Any file modified during implementation that does not appear in `FILES` is a scope violation.
Scope violations require either a PRD amendment (add the file to FILES before touching it) or a separate PRD.

### Registry Maintenance
1. Add a row to `PRD_REGISTRY.md` with status `IN PROGRESS` before implementation begins.
2. After merge: set status to `COMPLETE` and record the commit hash.
3. The `File` column MUST link to the prd_history file. Rows without a file show `—`.

---

## Patch PRD Rules

A PATCH PRD corrects a defect in a prior PRD's implementation.
Every PATCH PRD file MUST include a `ROOT CAUSE` section identifying exactly one of:
- `missing fail condition` — the original PRD had no FAIL line covering this case
- `ambiguous requirement` — the requirement text permitted multiple interpretations
- `hidden dependency` — an undocumented external constraint was violated

If a single PRD accumulates more than one PATCH PRD, the root causes MUST be documented and reviewed before the next PRD in sequence begins.

---

## Starting a New PRD

1. Copy `docs/PRD_TEMPLATE.md` to `docs/prd_history/PRD-NNN.md`
2. Set status to `IN PROGRESS`
3. Add registry row with `IN PROGRESS` and file link
4. Fill all sections before writing any implementation code
5. Write FAIL lines before writing requirement bodies
6. After merge: update status to `COMPLETE` and record commit hash
