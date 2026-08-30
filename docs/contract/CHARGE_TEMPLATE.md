# Session charge template v2 (Layer 3 delta)

A charge carries only what is unique to this work slice. It does not restate the
standing merge/scope/governance wall - "Standing contract: UNCHANGED" is a
complete citation of `CLAUDE.md` / `AGENTS.md` and the named mode contract. If a
task needs unusual authority, state only the DELTA explicitly; a charge may
narrow standing authority but never widen it.

```
CHARGE <id/date>
Standing contract: UNCHANGED
Standing stops + common escalation block apply (CLAUDE.md).
AUTHORITY: <RECON | DESIGN | IMPLEMENT | REVIEW | STEWARD>

Objective: <one sentence, one result>
Basis: <governing PRD + gate, packet, or dated DECISIONS ruling | NONE>
        # NONE is valid only for AUTHORITY: RECON
Baseline: main @ <sha>; branch <name>   # when relevant
Scope: <FILES / seam>                    # for IMPLEMENT: PRD FILES as written
Acceptance:
1. ...
2. ...
3. ...
Delta: <only changed standing behavior, or NONE>
Novel stop: <only task-specific stop conditions, or NONE>
Report: <minimal mode closeout: landed/held, next gate, blocker vocabulary>
```

REVIEW-mode variant: replace `Acceptance` with `Review question:` plus the input
envelope (primary artifact, reviewed SHA, neutral question, canonical
authority). Including author conclusions or another review as presumed truth is
a charge-authoring defect (see `MODE_REVIEW.md`).

The prior packet charge template for decision-support-expansion work,
`docs/plans/agent-work-charge-template-v0.1.md`, is retained for that governed
lane; its per-packet sections (ceilings, discriminating-test table, questions)
live in the PRD/packet rather than in an ordinary session charge.
