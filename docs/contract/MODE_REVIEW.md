# MODE: REVIEW (Layer 2)

Deltas from the standing wall (`CLAUDE.md` / `AGENTS.md`). The wall, owner
holds, precedence, and the common escalation block still bind.

## Input envelope (independence)
The review receives ONLY: the primary artifact under review, the exact reviewed
SHA, a neutral review question, and the applicable canonical authority. It does
not receive an author-side verdict, acceptance criteria, or another review's
prose as presumed truth. Single exception: a GOV-2 exact-corrected-head
confirmation receives the prior findings list, and only that, and is a
confirmation against the named SHA - not a fresh-scope review.

## What a review reads
Its stage's governing input, never another review's prose: an implementation
review reads the diff and the PRD; a GOV-2 packet review reads the packet and
the repository; a GOV-2 PRD review reads the PRD, packet, and design-direction
ruling. No artifact is produced whose subject is another artifact. Reviewer
disagreement is Dustin's to adjudicate, not another round.

## Standing gate and ceremony
The routine gate is one fresh-context review plus the connector bot's advisory
output (GOV-1). Deeper independent review is standing only for MATERIAL work
(GOV-2) or when Dustin commissions it or `docs/PRD_PROCESS.md` Second-Model
Disposition triggers it. Lane declares intensity (`docs/PRD_PROCESS.md`). At
most one findings-and-correction cycle (GOV-1).

## Bot-review threads (PRD-228: triage, never gate)
Connector-bot threads are advisory input. Disposition every substantive thread:
ACTIONED (fix lands, resolve citing the SHA/PRD), DISMISSED (one-line in-thread
reason), or BLOCKED/PARKED under GOV-2. Triaging them does not consume the GOV-1
cycle and never substitutes for the fresh-context review or the second-model
disposition.

## Artifact and drift
One committed artifact in the correct slot, SHA-pinned, fresh-context,
correctly named. Every review records a DRIFT CHECK (PRD-186): does the change
conflict with a `VISION.md` non-goal/principle, and does it leave a
`docs/PROJECT_STATE.md` claim stale? When a prior second review coexists, record
AGREE/DISAGREE/EXTEND per its REQUIRED finding for Dustin's adjudication - this
is adjudication input, not a review of that review.

## Edits / merge
Edits: the review artifact only. Merge: never.

## Escalate (additions)
- Missing primary inputs; an unresolvable reviewed SHA; an artifact-slot
  collision; or inability to establish fresh-context isolation.
