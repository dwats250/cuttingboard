# North Star Deep Audit — Domain Coverage Matrix

Tracks each domain's dispatch status through Phase 1. A domain may read
`COMPLETE` only per the Charter §10 definition. Updated by whoever runs
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
BLOCKED-PENDING-AMENDMENT | INCOMPLETE-RETRY-EXHAUSTED` (Charter §10,
execution plan Task 1.11).

Phase 2 (Fable synthesis) does not start until every row reads `COMPLETE`
or is explicitly waived by a logged Dustin ruling in
`03_AMENDMENTS_LOG.md` that meets all four elements of Charter §12
(Definition: WAIVER). A waiver is not equivalent to `COMPLETE` — it is a
formal amendment that must also state the corresponding change to Stopping
Rule condition 2 for this audit run, or that row still blocks closure.
