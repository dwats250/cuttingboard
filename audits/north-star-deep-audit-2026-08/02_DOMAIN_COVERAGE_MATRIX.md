# North Star Deep Audit — Domain Coverage Matrix

**Accepted scaffold seam SHA:** `e0d481f4e3daeae9d8cba4a7aee7670d27b5a2b5`
(PR seam 1, "North Star deep audit: scaffold", merged as PR #188). This pin
governs the charter, manifest, coverage matrix, amendments procedure, and
domain dispatch contracts used throughout Phase 1. It is separate from and
does not alter the North Star repository source-evidence baseline,
`fdeef90b0a0e0747d1bbf92385d3750b4024f4ae` (Charter §2) — that pin remains
untouched.

Tracks each domain's dispatch status through Phase 1. A domain may read
`COMPLETE` only per the Charter §11 definition. Updated by whoever runs
each Luna dispatch and by Fable during Task 2.1 coverage validation.

| Domain | Owned sources (see manifest) | Status | Attempt count | Blocking amendments |
|---|---|---|---|---|
| A | Governance/authority set | NOT STARTED | 0 | none |
| B | Portfolio/lifecycle set | NOT STARTED | 0 | none |
| C | Findings/debt set | NOT STARTED | 0 | none |
| D1 | As-built product surfaces | NOT STARTED | 0 | none |
| D2 | Proposed product surfaces | NOT STARTED | 0 | none |
| E | ORB/candidate-fidelity set | NOT STARTED | 0 | none |
| F | Freshness/scheduling set | NOT STARTED | 0 | none |
| G | Expansion vocabulary set | NOT STARTED | 0 | none |

Status values: `NOT STARTED | IN PROGRESS | COMPLETE |
BLOCKED-PENDING-AMENDMENT | INCOMPLETE-RETRY-EXHAUSTED` (Charter §11,
execution plan Task 1.11).

Phase 2 (Fable synthesis) does not start until every row reads `COMPLETE`
or is explicitly waived by a logged Dustin ruling in
`03_AMENDMENTS_LOG.md` that meets all four elements of Charter §12
(Definition: WAIVER). A waiver is not equivalent to `COMPLETE` — it is a
formal amendment that must also state the corresponding change to Stopping
Rule condition 2 for this audit run, or that row still blocks closure.
