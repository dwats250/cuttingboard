# ORB Shadow Beta Roadmap

## Current Phase

Pre-beta observational system.

The ORB 0DTE path is currently operating as an observational subsystem only. Its role is to collect deterministic post-session ORB outputs and operational health artifacts without changing live trading behavior.

## Beta Definition

Beta means the ORB shadow system is doing the following reliably:

- Operating automatically on each eligible market day
- Producing reliable durable artifacts
- Producing observational output that is useful enough to review and compare across sessions
- Requiring no manual intervention for normal daily collection

At beta, the system is still observational. Beta does not imply promotion into the active qualification or execution path.

## Beta Exit Criteria

The shadow observer can be considered ready to exit beta only when all of the following are satisfied:

- A meaningful sample of real sessions has been collected
  - Suggested threshold: 10 to 20 real PT sessions
- No operational failures across the review window
  - No missing ledger record when a run was attempted
  - No missing daily status record
  - No ambiguous failure state
- Output has been validated as useful
  - Observation fields are consistently interpretable
  - Qualification and exit audit output are informative
  - Reviewers can explain what happened on a session from the artifacts alone

## Near-Term Goals

- Maintain automatic daily collection
- Confirm ledger and status artifact durability
- Tighten operational review discipline
- Accumulate real sessions for review

## Next Phases

### Phase 1: Observation Review

- Review collected sessions for consistency
- Identify repeated failure modes
- Determine whether observation output is sufficient for human evaluation

### Phase 2: Candidate Promotion Assessment

- Assess whether the ORB observer has enough evidence quality to inform future qualification-layer work
- Define explicit criteria for any future promotion
- Keep promotion separate from the current beta effort

### Phase 3: Possible Qualification-Layer Integration

- Only after a separate design decision
- Only after explicit review of collected evidence
- Only through a scoped change that preserves testability and operational clarity

### Phase 4: Instrument Expansion

- Evaluate expansion to additional instruments later
- Preserve deterministic qualification standards during any expansion

This phase is not in scope for the current repository state.

## Non-Goals for This Phase

- No ORB rule expansion
- No execution behavior changes
- No new instruments
- No promotion into live qualification logic
