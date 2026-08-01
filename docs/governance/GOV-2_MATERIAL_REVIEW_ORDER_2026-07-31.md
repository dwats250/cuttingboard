# GOV-2 — Material review order and bounded correction

Status: RATIFIED UPON DUSTIN'S MERGE OF PR #186

This governance packet addresses the repeated workflow failures observed across
PRs #178–#185 without imposing second-model review on every repository change.

Dustin's merge of PR #186 is the ratifying action. Before that merge, this
document remains a reviewed proposal and is not binding; no agent may treat
this status line or the pending decision entry as advance ratification.

The governing principle is:

> No agent certifies the completeness of the boundary it chose.

## 1. Materiality is decided at intake and re-run on expansion

The proposed work is **MATERIAL** when any one of these is true:

- it claims to enumerate all consumers, callers, renderers, outputs, or schema
  readers;
- it selects an implementation seam or carrier shared across pipeline layers;
- it establishes or changes a production FILES ceiling or LOC ceiling;
- it adds, removes, renames, or changes a contract, audit, report, payload, or
  persisted schema surface that has more than one reader or presentation path;
- it changes a governance guardrail;
- it resolves a Critical or High finding;
- it crosses two or more of runtime, contract, audit, reporting, notification,
  delivery, dashboard, or persistence.

The materiality test applies to the proposed work before a PRD is opened. When
it matches, an upstream material design, reconciliation, or seam-trace packet is
required and must clear the review sequence below before any durable downstream
PRD, decision entry, or implementation authority is opened.

Re-run the MATERIAL classification before continuing whenever scope,
consumers, schemas, ceilings, seams, files, or risk assumptions expand
materially after intake, including during a PRD amendment or boundary
discovery. If the work newly becomes MATERIAL, stop implementation, create or
reopen the MATERIAL packet, and clear the packet review, Dustin
design-direction ruling, fresh-context independent PRD review, and explicit
Gate A sequence before resuming. A PRD or documentation amendment alone cannot
authorize continued implementation.

MICRO bookkeeping, cosmetic edits, local documentation corrections, and narrow
single-surface patches remain under the normal bounded workflow only when none
of the materiality conditions above applies. The materiality conditions take
precedence over the narrow-change exception. Dustin may classify any otherwise
non-material change as material.

A slice classified MATERIAL under this section, whether at intake or on
required reclassification, is therefore ineligible for `LANE: MICRO`,
including MICRO's cosmetic note-only form. The required order
in section 2 includes a PRD with its required independent review (step 7)
and an explicit Gate A (step 8); the collapsed MICRO lifecycle contains none
of these, so materiality operates as an additional MICRO-eligibility
disqualifier alongside the R12 safety net in `docs/PRD_PROCESS.md`. The
slice takes the lane the normal matrix assigns with MICRO unavailable:
STANDARD at minimum, HIGH-RISK only when the Lane Downgrade Prohibition's
own triggers (PRD-121 R11) fire independently. MATERIAL classification never
converts a STANDARD slice into HIGH-RISK and adds no Codex-commissioned
events beyond the two in section 7 (upstream packet review; exact-corrected-
head confirmation).

## 2. Review before design-direction ruling

A MATERIAL packet is provisional until an independent Codex review has
completed and every substantive finding is explicitly dispositioned.

Required order:

1. Author investigates and self-verifies.
2. Author produces a provisional material packet.
3. Codex independently reviews the packet and underlying repository surface.
4. Author performs one consolidated correction.
5. Codex independently confirms the exact corrected head SHA.
6. Dustin may issue a design-direction ruling from the review-clean packet.
7. A PRD is drafted from that ruling and receives review by the
   fresh-context independent reviewer. The reviewer is not the author or
   same-session implementer, reviews the PRD together with the review-clean
   packet and Dustin's ruling, and records a committed verdict against the
   exact reviewed PRD commit SHA or revision.
8. Dustin issues Gate A only on the reviewed PRD; Gate A remains the
   implementation authorization.

A corrected head that has not received independent SHA-pinned confirmation is
not review-clean.

Both Codex packet-cycle events require packet-local durable evidence. The
evidence must be embedded in the committed MATERIAL packet or stored in a
committed review record in the packet's directory and linked from the packet.
For each event, the durable record must state:

- the event type: `INITIAL PACKET REVIEW` or
  `EXACT-CORRECTED-HEAD CONFIRMATION`;
- the reviewer identity and capability role;
- the exact reviewed commit SHA or immutable packet revision;
- the review date;
- the verdict;
- the findings and their explicit dispositions, or `none` only when that is
  the truthful result; and
- confirmation that the reviewer operated in fresh context and was
  independent of the authoring session, including the required memory-
  provenance or equivalent run-isolation evidence.

The exact-corrected-head confirmation record must identify the corrected SHA
and enumerate the prior finding identifiers and dispositions being confirmed.
Its scope is confirmation that those findings are resolved at that exact head,
not a new broad review. A connector comment, resolved thread, external link, or
ephemeral transcript cannot substitute for either committed record.

Codex is required here because the work is material. It is not a standing gate
for every repository change.

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

For MATERIAL work, a design/documentation branch may exist before the
upstream packet is review-clean only to carry the CARD, MATERIAL packet
drafting and review records, or governance/design documentation. The branch's
existence creates no implementation authority.

No production implementation, implementation PRD execution, or other
implementation change may begin until all four conditions hold:

1. the MATERIAL packet is review-clean;
2. Dustin has issued the design-direction ruling;
3. the PRD has been drafted and reviewed by the fresh-context independent
   reviewer; and
4. Dustin has explicitly issued Gate A.

Only after those conditions hold may a branch be opened or used for
implementation work. Disposable local drafting remains non-authoritative and
must be reconciled or discarded after the upstream packet stabilizes.

Normal order:

```
materiality check at intake
-> provisional material packet
-> Codex review
-> one consolidated correction
-> Codex confirmation of exact corrected head
-> Dustin design-direction ruling
-> PRD drafting
-> independent PRD review
-> Dustin Gate A
-> implementation
-> required implementation review
-> Dustin merge
```

## 5. Provisional ceilings

Before the independent material review is clean, FILES and LOC figures are
estimates, not constraints.

Use these labels:

- `ESTIMATED SURFACE — NOT YET APPROVED`
- `REVIEWED DESIGN CEILING`
- `GATE A CEILING`
- `IMPLEMENTATION ACTUAL`

The first binding ceiling is the one Dustin approves at Gate A on the reviewed
PRD. After Gate A, any proposed increase to the FILES or LOC ceiling is a
stop-and-renew event. Before work resumes:

1. the PRD must state the revised ceiling and reason;
2. the relevant MATERIAL packet and canonical authority record must state the
   revised ceiling and consequence;
3. the fresh-context independent reviewer must review the exact amended PRD
   revision and record a verdict against it; and
4. Dustin must explicitly issue an amended Gate A approving the increased
   ceiling.

A documentation amendment alone cannot satisfy the amended Gate A, and no
agent may issue or infer that approval. Reducing the implementation to remain
within the existing Gate A ceiling does not increase the ceiling.

The amended-PRD review is a new authority check on a changed revision and
receives GOV-1's one findings-and-correction cycle for that revision. It is not
a third auto-commissioned Codex packet event and does not reopen the bounded
packet cycle unless the boundary-reset rule in section 6 fires.

An author must not exclude a truthful consumer or schema consequence merely to
preserve a provisional estimate.

## 6. Boundary-reset trigger

A connector finding that reveals a previously omitted consumer class, renderer,
audit carrier, schema surface, or end-to-end seam is not a local wording fix.
It means the discovery boundary was incomplete.

- The first newly discovered class triggers one complete producer-to-final-
  consumer inventory refresh.
- A later review that discovers another previously omitted class returns the
  packet to `DESIGN INCOMPLETE`.
- At that point, stop incremental patching. Dustin chooses whether to rebuild
  the packet from a fresh frame, narrow its claim, or park it.

Local citation, wording, fixture, and assertion corrections may still be fixed
inside the bounded correction cycle.

## 7. Bounded review and connector cycle

For a MATERIAL packet, the normal review sequence is:

1. one independent Codex review;
2. one consolidated author correction;
3. one independent Codex confirmation of the exact corrected head.

If exact-head confirmation finds another material boundary omission, the
packet reopens as `DESIGN INCOMPLETE`; it does not enter an unlimited sequence
of incremental corrections while continuing to call itself complete.

Every substantive connector thread receives one of these truthful dispositions:

- `ACTIONED` — the correcting commit or governed follow-up lands and is cited;
- `DISMISSED` — false positive, out of scope, or already covered, with reason;
- `BLOCKED/PARKED` — the finding is valid, the packet is not review-clean, no
  downstream authority may proceed, and the thread remains unresolved until
  Dustin resumes, narrows, or retires the packet.

`BLOCKED/PARKED` is not a substitute for action on a packet presented as ready.

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

## 9. Closeout policy remains unchanged

GOV-2 does not change the existing same-PR closeout rule.

HIGH-RISK second-model disposition is currently enforced by the validator only
when the PRD is marked `COMPLETE`. Moving HIGH-RISK closeout after merge would
therefore weaken the pre-merge gate. Any future post-merge closeout design
requires a separate code-touching PRD that first adds equivalent pre-merge
enforcement for IN PROGRESS implementation PRDs.

Until that validator change lands, closeout continues to ride the
implementation PR under PRD-229 and `docs/PRD_PROCESS.md`.

## 10. Canonical ruling propagation

When new evidence changes a design-direction ruling or Gate A ruling:

- the governed PRD and canonical decision entry must be corrected together;
- earlier rulings remain as history but are marked `SUPERSEDED`;
- exactly one current ruling is plainly identified;
- supplemental artifacts may preserve provenance but may not compete as
  current authority.

A downstream packet must not present a superseded FILES or schema ruling as
current.

## 11. Temporary authoring-seat restriction

Until Dustin explicitly re-certifies it, the currently restricted model
occupies the `fresh-context independent reviewer` capability role as a
restricted actor. This section constrains that capability-role assignment; it
does not silently redefine the project lead or implementation driver roles.
While restricted, that model may perform:

- evidence gathering;
- provisional design drafting;
- bounded research;
- mechanical reconciliation;
- option generation.

It may not:

- independently drive MATERIAL governed work;
- certify a consumer inventory as complete;
- satisfy its own independent-review gate;
- issue or infer a design-direction ruling or Gate A;
- continue downstream authority after upstream review findings;
- declare a MATERIAL packet merge-ready without the required Codex review.

This is an operational capability restriction, not a permanent vendor or model
judgment. Dustin may lift it after a controlled re-certification task.

## 12. Application to the held CB-02 work

PR #184 and PR #185 predate this proposal and remain parked.

Before either merges:

- PR #184 remains the upstream material packet;
- PR #184 must receive exact-head independent confirmation after its final
  correction;
- PR #185 must contain the final canonical nine-file ruling consistently,
  including `docs/DECISIONS.md`;
- PR #185 receives its required independent PRD review after that correction;
- production implementation remains prohibited until Dustin issues Gate A on
  the reviewed PRD.

## Ratification effect

Dustin's merge of PR #186 ratifies GOV-2 for new work. The same PR links GOV-2
from the injected `CLAUDE.md` governance surface so fresh agents cannot miss it
or follow contradictory review-order instructions.

Before that merge, GOV-2 is held for Dustin's decision and grants no authority.
After it, GOV-2 is ratified and binding; Dustin retains sole design-direction,
Gate A, amended Gate A, Gate B, ratification, and merge authority.
