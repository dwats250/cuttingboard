# GOV-2 — Material review order and bounded correction

Status: PROPOSED FOR DUSTIN RATIFICATION

This governance packet is intentionally compact. It addresses the repeated
workflow failures observed across PRs #178–#185 without reopening the full
repository governance model.

It becomes binding only when Dustin merges the PR carrying it. Until then it is
a reviewed proposal.

## Purpose

Prevent high-cost review cascades in which a design is declared complete,
Gate A is issued, downstream authority is opened, and later connector findings
repeatedly expand the consumer graph, schema surface, FILES, and test plan.

The governing principle is:

> No agent certifies the completeness of the boundary it chose.

## 1. Materiality test

A packet is **MATERIAL** when any one of these is true:

- it claims to enumerate all consumers, callers, renderers, outputs, or schema
  readers;
- it selects an implementation seam or carrier shared across pipeline layers;
- it establishes or changes a production FILES ceiling or LOC ceiling;
- it adds, removes, renames, or changes a contract, audit, report, payload, or
  persisted schema surface;
- it changes a governance guardrail;
- it resolves a Critical or High finding;
- it crosses two or more of runtime, contract, audit, reporting, notification,
  delivery, dashboard, or persistence.

MICRO bookkeeping, cosmetic edits, local documentation corrections, and narrow
single-surface patches remain under the normal bounded workflow unless Dustin
explicitly classifies them as material.

## 2. Review before Gate A

A MATERIAL design, reconciliation, or seam-trace packet is provisional until an
independent Codex review has completed and every substantive finding is
explicitly dispositioned.

Required order:

1. Author investigates and self-verifies.
2. Author produces a provisional design packet.
3. Codex independently reviews the packet and underlying repository surface.
4. Author performs one consolidated correction.
5. One confirmation sweep checks the corrected head.
6. Dustin issues Gate A from the review-clean packet.

Gate A must not be issued from author self-verification alone.

The Codex review is required here because the packet is material, not because
Codex is a standing reviewer for every repository change.

## 3. Author verification is not independent review

Author self-verification includes:

- reproducing claims;
- resolving citations, symbols, and paths;
- running tests and validators;
- inspecting the changed-file boundary;
- performing consumer and caller searches;
- designing discriminating regressions and red mutations.

Independent review must attempt to falsify:

- the completeness claim;
- consumer and presentation coverage;
- carrier threading;
- schema classification;
- aggregate and message consistency;
- regression discrimination;
- FILES and LOC estimates.

The authoring agent, a subagent spawned by it, or a same-session second pass may
contribute evidence but cannot satisfy the independent-review requirement.

## 4. No downstream authority before upstream review-clean

A downstream PRD, canonical decision entry, implementation branch, or other
durable authority must not be committed or opened until the upstream MATERIAL
packet is review-clean.

Disposable local drafting is allowed. It carries no authority and must be
reconciled or discarded after the upstream packet stabilizes.

Normal order:

```
material packet
-> Codex review
-> consolidated correction
-> confirmation sweep
-> Dustin Gate A
-> PRD drafting
-> independent PRD review
-> Dustin implementation approval
-> implementation
-> Codex implementation review
-> Dustin merge
```

## 5. Provisional ceilings

Before the independent material review is clean, FILES and LOC figures are
estimates, not constraints.

Use these labels:

- `ESTIMATED SURFACE — NOT YET APPROVED`
- `REVIEWED GATE A CEILING`
- `IMPLEMENTATION ACTUAL`

The first binding ceiling is the one Dustin approves after the material review.
After Gate A, exceeding that ceiling is a stop-and-amend event.

An author must not exclude a truthful consumer or schema consequence merely to
preserve a provisional estimate.

## 6. Boundary-reset trigger

A connector finding that reveals a previously omitted consumer class, renderer,
audit carrier, schema surface, or end-to-end seam is not a local wording fix.
It means the discovery boundary was incomplete.

- The first newly discovered class triggers one complete producer-to-final-
  consumer inventory refresh.
- A later round that discovers another previously omitted class returns the
  packet to `DESIGN INCOMPLETE`.
- At that point, stop incremental patching. Dustin chooses whether to rebuild
  the packet from a fresh frame, narrow its claim, or park it.

Local citation, wording, fixture, and assertion corrections may still be fixed
inside the bounded correction cycle.

## 7. Bounded connector cycle

For a MATERIAL packet, the normal review sequence is:

1. one independent Codex review;
2. one consolidated author correction;
3. one confirmation sweep.

The confirmation sweep is not a new design round. If it finds another material
boundary omission, the packet reopens as `DESIGN INCOMPLETE`; it does not enter
an unlimited sequence of connector corrections while continuing to call itself
complete.

Every substantive connector thread remains subject to the existing ACTIONED or
DISMISSED disposition rule.

## 8. Docs-only CI claim boundary

For a docs-only design, governance, reconciliation, or seam-trace PR, green CI
proves only that the documentation branch preserves the current repository
baseline.

Required reporting language:

> CI confirms this documentation-only branch preserves the current green
> baseline. It does not execute or validate the proposed runtime design,
> consumer inventory, or regression plan.

A docs-only full-suite count must not be offered as evidence that a proposed
implementation is complete.

## 9. Closeout policy

HIGH-RISK or connector-reviewed implementation PRs normally merge with the PRD
still IN PROGRESS. Their closeout occurs in one predictable, mechanical
post-merge closeout PR using the verified closeout skill and the actual merge
identity.

MICRO work may retain same-PR closeout when:

- the final identity is already knowable;
- no review or connector correction follows the closeout commit; and
- the closeout remains the final reviewed branch state.

This replaces the repeated accidental closeout spill with an explicit rule.

## 10. Canonical ruling propagation

When new evidence changes Gate A:

- the governed PRD and canonical decision entry must be corrected together;
- earlier rulings remain as history but are marked `SUPERSEDED`;
- exactly one current ruling is plainly identified;
- supplemental artifacts may preserve provenance but may not compete as current
  authority.

A downstream packet must not present a superseded FILES or schema ruling as
current.

## 11. Temporary authoring-seat restriction

Until Dustin explicitly re-certifies the model currently occupying the Opus 5
seat, that seat may perform:

- evidence gathering;
- provisional design drafting;
- bounded research;
- mechanical reconciliation;
- option generation.

It may not:

- independently drive MATERIAL governed work;
- certify a consumer inventory as complete;
- satisfy its own independent-review gate;
- issue or infer Gate A;
- continue downstream authority after upstream review findings;
- declare a MATERIAL packet merge-ready without the required Codex review.

This is an operational capability restriction, not a permanent vendor or model
judgment. Dustin may lift it after a controlled re-certification task.

## 12. Application to the held CB-02 work

PR #184 and PR #185 predate this proposal and remain parked.

Before either merges:

- PR #184 remains the upstream material packet;
- PR #185 must contain the final canonical nine-file ruling consistently,
  including `docs/DECISIONS.md`;
- the PRD receives a fresh independent review after that correction;
- production implementation remains prohibited until Dustin approves the
  reviewed PRD.

## Ratification effect

Merging this governance PR ratifies GOV-2 immediately for new work.

A later mechanical integration may copy or link these rules into `CLAUDE.md`,
`docs/PRD_PROCESS.md`, and the review skill. That integration must preserve the
substance here and may not delay the rules' effective date after ratification.

Held for Dustin's decision.