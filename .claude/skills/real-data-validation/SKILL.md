---
name: real-data-validation
description: Use when implementing or closing out a CONSUMER-class PRD that ingests an external data format we don't control (broker statements, exchange feeds, third-party CSVs, etc.). Runs the validate-then-fix discipline mechanically — drives `scripts/validate_consumer_prd.py` against a real-data fixture, scaffolds the defect log at `docs/prd_history/PRD-NNN.validation.md`, and walks each surfaced defect through the amend-vs-spawn bar. Triggers on "validate against real data", "run real-data validation for PRD-NNN", "validation gate for the consumer PRD", "validate-then-fix pass on PRD-NNN".
---

# Real-data validation for CONSUMER-class PRDs

## Scope and boundary

This skill does three things and only three things:

1. **Drive** the harness `scripts/validate_consumer_prd.py` against a
   real-data fixture for an in-flight CONSUMER-class PRD.
2. **Surface** the captured output and route each observable defect
   through the amend-vs-spawn bar.
3. **Land** the resolved defect log at
   `docs/prd_history/PRD-NNN.validation.md` and either amend the PRD
   (in NOTES) or draft follow-up PRD stubs.

It is NOT a substitute for:

- The synthetic-fixture unit tests that establish structural
  confidence.
- Independent PRD review or Codex cross-review.
- Closeout (the `prd-closeout-verified` skill still runs after).

This skill assumes the synthetic-fixture tests are already green.
Running it before unit tests pass is a category error — the harness
will surface noise instead of real defects.

## When to trigger

- "Run real-data validation for PRD-NNN."
- "Validate the consumer against the real fixture before closeout."
- "Validation gate on PRD-NNN."
- Any explicit "validate-then-fix" instruction tied to a
  CONSUMER-class PRD.

Do NOT trigger for:

- INTERNAL PRDs (no external data format involved).
- A consumer whose only "external" input is a fixture we author.
- Re-running the harness on the same fixture without intervening
  code or fixture changes (the previous log is the answer).

## Inputs the user must (or you must extract) provide

| Input | Where it usually lives |
|---|---|
| PRD identifier (`PRD-NNN`) | The PRD file under `docs/prd_history/` |
| Consumer module (dotted path) | The PRD's FILES section, or the symbol named in R1 |
| Consumer entry-point function | Public function exported by the module (e.g. `parse_statement`) |
| Real-data fixture path | `private/<source>/...` per CLAUDE.md convention; the PRD itself should name it |

If the PRD does not name a real-data fixture, **stop and surface
that gap** — a CONSUMER PRD without a named real-data sample is
itself a defect (see PRD-153 closeout, `docs/DECISIONS.md`
2026-05-22).

## Procedure

### Step 1 — Confirm preconditions

Use TodoWrite to track the procedure. Before invoking the harness:

- [ ] Synthetic-fixture unit tests are green (`pytest` on the
      relevant `tests/test_<consumer>*.py`).
- [ ] The PRD is `IN PROGRESS` (not COMPLETE — validation lives in
      the implementation window).
- [ ] A real-data fixture path exists and is readable.
- [ ] The consumer module exports a single-argument entry-point
      callable accepting the fixture path.

If any precondition fails, surface it and stop. Do not paper over.

### Step 2 — Run the harness

```
.venv/bin/python scripts/validate_consumer_prd.py \\
    --prd PRD-NNN \\
    --module <dotted.module.path> \\
    --fn <entry_point_function> \\
    --fixture <path/to/real/fixture>
```

The harness writes `docs/prd_history/PRD-NNN.validation.md` with the
captured output (or traceback) and a scaffolded defects section.

If the harness exits non-zero with a traceback, that *is* the first
defect — go to Step 3 with that as Defect 1.

### Step 3 — Compare output against expected behavior

Read the harness output. For each observable defect (wrong row,
missing row, malformed field, etc.), fill in one entry in the
scaffolded defects section:

- **Where** — file:line in the fixture or row identifier.
- **Observed** — what the consumer produced.
- **Expected** — what should have been produced, with the reasoning.
- **Root cause** — one-line, identified after a brief code read.

Do not skip the root-cause field. "Looks wrong, will fix" is the
shape of drift that the discipline exists to prevent.

### Step 4 — Classify each defect via amend-vs-spawn

For each defect, apply the bar from `docs/DECISIONS.md`
(2026-05-22, PRD-153 closeout):

- **Amend the in-flight PRD** if all three hold:
  - Same domain as an existing requirement.
  - Fits inside the existing requirement shape.
  - < ~10 LOC to fix.
- **Spawn a follow-up PRD (or PATCH PRD)** otherwise.

Record the classification and one-line rationale in the defect
entry. When in doubt, prefer spawn — silent scope expansion is
worse than an extra small PRD.

### Step 5 — Resolve

For each amend-class defect:

- Implement the fix (parser change, normalization tweak, etc.) in
  the consumer module.
- Add a unit test exercising the real-data case (extract a minimal
  synthetic row that reproduces the defect — do not commit the
  full real fixture).
- Record the amendment in the PRD's NOTES section, citing the
  defect ID.

For each spawn-class defect:

- Draft a stub PRD (use the `prd-authoring-verified` skill).
- Link the stub from the validation log's defect entry.
- Do not block the in-flight PRD's closeout on the follow-up
  implementing — only on the follow-up being drafted.

### Step 6 — Re-run

After resolving amend-class defects, re-run the harness against
the same fixture and confirm the defects no longer appear. Capture
the clean run by overwriting the validation log (the harness writes
fresh each invocation).

### Step 7 — Closeout the validation log

Mark all the closeout checkboxes in the validation log. Stage the
log alongside the consumer changes. The validation log is part of
the PRD's bookkeeping and lands in the same commit as its fixes,
not separately.

Then hand off to `prd-closeout-verified` for the normal PRD
closeout flow.

## Failure modes this skill prevents

- **Synthetic-only confidence.** Unit tests green ≠ consumer
  correct against real input. PRD-153 shipped with green synthetics
  and six real-data defects.
- **Silent scope expansion.** Defect surfaces, gets quietly fixed
  without PRD amendment, FILES list drifts. The skill forces an
  explicit amend-vs-spawn call per defect.
- **Defect amnesia.** Without a validation log, "what real-data
  defects did this consumer surface and how were they resolved" is
  unrecoverable history. The log is the audit trail.

## What this skill does NOT do

- It does not decide whether output is correct. Output → expectation
  is a human/Claude judgment per defect.
- It does not diff against a golden file. CONSUMER outputs are
  often too long and irregular to lock down with a fixture file;
  the defect log is the actual contract.
- It does not commit. Staging and committing follow the normal
  scope-lock + closeout path.
