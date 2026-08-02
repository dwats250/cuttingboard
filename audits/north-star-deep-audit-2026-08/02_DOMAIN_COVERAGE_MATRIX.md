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

**Second Stage 0 review remediation pass (2026-08-02), 9 findings, no
re-dispatch:** all 8 domains remain COMPLETE; attempt counts unchanged
(no domain was re-run). Corrections made directly on the committed
evidence: Domain A's PR #187 disposition work completed for all 29
comments (was blanket UNKNOWN); an ambiguous "blocking: yes" in A/B/D1's
PROPOSED AMENDMENT wording clarified to specify what it blocks (never
domain completion, confirmed by direct Charter §11 application, not by
treating the prior retry as a Dustin ruling); D1's dispatch-contract
provenance corrected to cite the pinned execution-contract SHA instead of
"the worktree" (verified reproducible via commit ancestry, no
re-collection needed); Domain E's 3 rows citing unauthorized Master Ledger
content removed and routed to D2/B, which already owned the same findings;
D2's missing non-match-detail block added and its implementation-absence
overclaim reframed to document-state evidence; Domain A's one invalid
filename citation fixed; Domain B's impossible Ledger line range replaced
with the correct Program range; Domain C's CB-29 row updated from stale
MATCH to PARTIAL per Program's own superseding text. Also caught during
this pass, not separately requested: A-GOV-010/011/012 were missing their
required non-match-detail blocks (Charter §7) despite being MISMATCH/
PARTIAL since Phase 1 attempt 1 — added.

Status values: `NOT STARTED | IN PROGRESS | COMPLETE |
BLOCKED-PENDING-AMENDMENT | INCOMPLETE-RETRY-EXHAUSTED` (Charter §11,
execution plan Task 1.11).

Phase 2 (Fable synthesis) does not start until every row reads `COMPLETE`
or is explicitly waived by a logged Dustin ruling in
`03_AMENDMENTS_LOG.md` that meets all four elements of Charter §12
(Definition: WAIVER). A waiver is not equivalent to `COMPLETE` — it is a
formal amendment that must also state the corresponding change to Stopping
Rule condition 2 for this audit run, or that row still blocks closure.
