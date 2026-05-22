# Branch Cleanup — 2026-05-22

Phase 1 cleanup, Commit 9. Git operations only; no file changes.

## Remote branches deleted from `origin`

```
prd-044-real-macro-driver-payload
prd-045-trade-decision-materialization
prd-046-decision-trace
prd-047-post-trade-evaluation
prd-049-alert-optimization
prd-049-patch-02-guidance
prd-050-alert-fallback
prd-051-execution-policy
prd-053-market-map
prd4-trade-policy
```

Two branches the brief named were already absent from origin and required no action:

- `prd-062-evaluation` — local-only.
- `prd061-main` — local-only.

## Local branches deleted

PRD-tagged branches from the brief:

```
prd-044-real-macro-driver-payload
prd-045-trade-decision-materialization
prd-046-decision-trace
prd-047-post-trade-evaluation
prd-049-alert-optimization
prd-049-patch-02-guidance
prd-050-alert-fallback
prd-051-execution-policy
prd-053-market-map
prd-062-evaluation
prd061-main
prd4-trade-policy
```

Other clearly-post-merge local branches (caught by the brief's "delete other clearly post-merge local branches if confirmed merged" instruction):

```
feature/candidate-carousel
feature/candidate-surfacing-ui
feature/candidate-surfacing-ui-v2
feature/ui-decision-layer
milestone/dashboard-stable
```

The brief listed these as locally stale during the inventory audit; all were past their merged PRDs and behind main by hundreds of commits.

`integrate-*` branches required worktree pruning first:

```
integrate-gitignore         (worktree /tmp/cuttingboard-ignore-fix — prunable)
integrate-hourly-pages      (worktree /tmp/cuttingboard-hourly-pages — prunable)
integrate-main-deploy       (worktree /tmp/cuttingboard-main-deploy — prunable)
```

`git worktree prune` removed the orphaned worktree refs (all four were `prunable` — gitdir files pointed to non-existent `/tmp/*` directories); the branches were then deletable with `git branch -D`. A fourth stale worktree (`/tmp/cuttingboard-prd053-audit`, detached HEAD) was pruned in the same pass.

## Branches not touched

Remote `feature/*` branches were not on the brief's explicit deletion list and are not deleted by this cleanup:

```
origin/feature/candidate-carousel
origin/feature/candidate-surfacing-ui
origin/feature/ui-decision-layer
origin/milestone/dashboard-stable
```

The corresponding *local* branches were deleted (above); the remote refs remain. Surface for follow-up if Dustin wants origin pruned to match.

## Final state

Local:

```
* main c47cf40
```

Origin:

```
origin/feature/candidate-carousel
origin/feature/candidate-surfacing-ui
origin/feature/ui-decision-layer
origin/main
origin/milestone/dashboard-stable
```
