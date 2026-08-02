# North Star Deep Audit — Domain Coverage Matrix

**Three distinct, non-interchangeable pins govern Phase 1:**

- **North Star repository source-evidence baseline:**
  `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`. Every repository source-
  evidence read is `git show fdeef90b0a0e0747d1bbf92385d3750b4024f4ae:<path>`
  (Charter §2). Unaltered by anything below.
- **Accepted scaffold seam merge SHA:** `e0d481f4e3daeae9d8cba4a7aee7670d27b5a2b5`
  (PR seam 1, "North Star deep audit: scaffold", merged as PR #188). This
  remains the accepted PR seam 1 merge; it is not superseded or replaced
  by the SHA below.
- **Authorized Phase 1 execution-contract SHA:**
  `41bfcd6888b7c28da9c0478c9534bdb66a9a2600`. A bounded pre-dispatch
  correction carried on the evidence branch — commits the evidence schema
  (risk/assumptions fields, full row template, non-match-detail block)
  that was missing after PR seam 1 merged. Does not retroactively change
  the PR seam 1 merge and does not create a fourth PR seam; it will be
  reviewed as part of PR seam 2. **Every Luna dispatch in Phase 1 uses the
  charter, manifest, schema, and coverage rules from exactly this SHA.**
  Every repository evidence read remains pinned to the baseline SHA above,
  regardless of this contract SHA.

Tracks each domain's dispatch status through Phase 1. A domain may read
`COMPLETE` only per the Charter §11 definition. Updated by whoever runs
each Luna dispatch and by Fable during Task 2.1 coverage validation.

| Domain | Owned sources (see manifest) | Status | Attempt count | Blocking amendments |
|---|---|---|---|---|
| A | Governance/authority set | COMPLETE | 2 | AMENDMENT-002 (logged, non-blocking to this pass) |
| B | Portfolio/lifecycle set | COMPLETE | 2 | AMENDMENT-003 (logged, non-blocking to this pass) |
| C | Findings/debt set | COMPLETE | 1 | none |
| D1 | As-built product surfaces | COMPLETE | 2 | AMENDMENT-004 (logged, non-blocking to this pass) |
| D2 | Proposed product surfaces | COMPLETE | 1 | none |
| E | ORB/candidate-fidelity set | COMPLETE | 1 | none |
| F | Freshness/scheduling set | COMPLETE | 1 | AMENDMENT-005 (logged, non-blocking) |
| G | Expansion vocabulary set | COMPLETE | 1 | none |

All 8 domains COMPLETE as of this dispatch. A, B, D1 required their one
permitted retry (Global Constraint #6) — not because attempt 1's evidence
was wrong, but because each self-declared `IN PROGRESS` over out-of-scope
dependencies it had already correctly logged as a PROPOSED AMENDMENT and
correctly declined to investigate. Retry 2 re-examined attempt 1 strictly
against Charter §11 without redoing any evidence-gathering; all three
qualified as COMPLETE under that definition, with the underlying evidence
tables unchanged (one immaterial citation-filename typo introduced by A's
retry was discarded in favor of attempt 1's correct citation — logged in
the evidence-seam commit, not a substantive change).

Status values: `NOT STARTED | IN PROGRESS | COMPLETE |
BLOCKED-PENDING-AMENDMENT | INCOMPLETE-RETRY-EXHAUSTED` (Charter §11,
execution plan Task 1.11).

Phase 2 (Fable synthesis) does not start until every row reads `COMPLETE`
or is explicitly waived by a logged Dustin ruling in
`03_AMENDMENTS_LOG.md` that meets all four elements of Charter §12
(Definition: WAIVER). A waiver is not equivalent to `COMPLETE` — it is a
formal amendment that must also state the corresponding change to Stopping
Rule condition 2 for this audit run, or that row still blocks closure.
