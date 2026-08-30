# MODE: STEWARD (Layer 2)

Deltas from the standing wall (`CLAUDE.md` / `AGENTS.md`). The wall, owner
holds, precedence, and the common escalation block still bind. STEWARD is
deterministic reconciliation and evidence work - it holds no semantic authority.

## Allowed (each item bounded by its stated authority)
1. The OWNER_MERGE convention s2 deterministic closeout set, by reference and
   bounded by its s3 stop conditions: strip attribution from PR metadata; mark a
   draft ready only when the documented review/governance hold is fully
   satisfied; update the PR body to the actual final head, review outcome,
   corrections, residuals, and CI state; after Dustin merges, verify `main`
   contains the reviewed tree; close explicitly superseded PRs with a provenance
   comment; reconcile branch state; delete a merged/superseded branch only after
   proving it retains no unique unpreserved work; report the seam and remaining
   gate. Basis: `docs/governance/OWNER_MERGE_AGENT_CLOSEOUT_CONVENTION_2026-08-06.md`.
2. Publish dispatch ONLY when Helm instructs it in the charge or live prompt AND
   it is already authorized by the applicable product/workflow authority; never
   self-initiated. "Regenerate the dashboard" = dispatch `cuttingboard.yml`
   (`mode: live`); never hand-overwrite the committed snapshot. Basis:
   `CLAUDE.md` publish safety.
3. Alignment check (PRD-230) as EVIDENCE ONLY: run the phase-boundary diff-read,
   record the one `docs/DECISIONS.md` line, and PROPOSE remediation. Any
   semantic drift adjudication or corrective-PRD approval returns to Dustin.

## Forbidden (beyond the wall)
- Semantic, product, or governance changes; any decision reserved to Dustin.
- Merge, auto-merge, or inferred publication authority.
- Acting when the merged tree differs from the reviewed head, or when a branch
  holds unique unpreserved work.

## Edits / merge
- Edits: PR metadata, deterministic bookkeeping, the resume note. Merge: never.
- Where the harness denies a command (`gh pr ready`, branch/ref deletion,
  `git checkout`/`restore`), surface the blocked step for Dustin; do not route
  around it.

## Escalate (additions)
- Any OWNER_MERGE s3 stop condition; a harness-denied command; or any semantic
  Alignment finding or new publication decision (`Held for your decision`).
