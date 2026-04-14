# Production Roadmap

## Phase 4 - Evidence Gathering

This is the current phase.

- The ORB shadow system runs automatically on eligible sessions.
- The repository is collecting real session data.
- The goal is reliable evidence collection, not feature expansion.
- No active execution behavior is in scope.

This phase should remain operationally quiet. The system should run, record, and explain outcomes without requiring manual intervention.

## Phase 5 - Review Layer

The next phase is a review layer built on top of the existing artifacts.

- Build a ledger digest for recent sessions
- Summarize daily session outcomes
- Identify repeated behavior patterns
- Improve review efficiency without changing qualification logic

The review layer should consume existing outputs rather than introduce parallel logic.

## Beta Definition

The system qualifies as beta when all of the following are true:

- It runs automatically every eligible session
- It writes consistent ledger and status artifacts
- It produces outputs that are easy to interpret from the stored fields
- It has no operational failures across a meaningful sample of real sessions

Beta here means operational reliability and useful evidence, not live execution.

## Post-Beta

After beta, the ORB module can take one of two paths:

- Promote the ORB logic into a future qualification layer
- Refine the ORB observer further if the evidence is not yet strong enough

Broader expansion may later include:

- Additional instruments
- Metals
- Trend-oriented extensions

Any expansion should preserve the same deterministic architecture and auditability standard.

## Dashboard

Any future dashboard is presentation only.

- It should consume existing outputs
- It should not contain trade logic
- It should not become a second source of truth
