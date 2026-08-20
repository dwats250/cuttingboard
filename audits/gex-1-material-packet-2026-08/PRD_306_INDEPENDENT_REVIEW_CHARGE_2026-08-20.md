# PRD-306 Fresh-Context Independent Review Charge (GOV-2)

Status: READY TO DISPATCH (turnkey). Prepared 2026-08-20.
This charge does NOT authorize implementation. It requests the GOV-2
fresh-context independent PRD review that must precede Dustin's Gate A.

## Pinned target (SHA)

- Review-candidate PRD content SHA (PRD-306.md frozen here):
  `1286cb01a49a0f0764e26ba42fdeac4d1051c46d`
- Branch: `claude/gex-1-prd-306-authority`
- The reviewer records the committed verdict against the EXACT head reviewed.
  Any later commit on this branch adds only this charge and the Ultracode
  implementation charter; it does NOT alter `docs/prd_history/PRD-306.md`, so
  the PRD content is byte-identical at the pinned SHA and at branch head. If
  in doubt, diff `docs/prd_history/PRD-306.md` between the two.

## Who may perform this review

- Capability role: fresh-context independent reviewer (GOV-2 requirement for
  every MATERIAL PRD). Must be a FRESH context: NOT the PRD author, NOT a
  same-session implementer, NOT a subagent spawned from the authoring session.
- Default recommendation: a fresh Claude/Fable session using the
  `prd-review-claude` skill, writing to the Claude review slot.
- A qualified fresh-context second-model reviewer may fill this role, BUT
  selecting Codex for it requires a SEPARATE Dustin commission under PRD-242;
  it is NOT one of GOV-2's two auto-commissioned Codex packet-cycle events
  (those two were the upstream packet review and the Event-2 exact-head
  confirmation, both already spent and CONFIRMED).

## What to read (review inputs; a confirmation of design fidelity, not a
## re-opening of settled design)

1. `docs/prd_history/PRD-306.md` (at the pinned SHA).
2. The review-clean MATERIAL packet (deep design + rationale):
   `audits/gex-1-material-packet-2026-08/GEX_1_MATERIAL_DESIGN_PACKET_2026-08-20.md`
   with Event-1 review (`GEX_1_EVENT_1_CODEX_REVIEW_2026-08-20.md`) and
   Event-2 confirmation (`GEX_1_EVENT_2_CONFIRMATION_2026-08-20.md`).
3. Dustin's design-direction ruling: `docs/DECISIONS.md`, 2026-08-20
   "GEX-1 DESIGN DIRECTION APPROVED".
4. Current relevant repository surfaces the PRD names (FILES cone, the two
   doc M-edit targets, `tools/` and `tests/` conventions).

Do NOT re-open the upstream MATERIAL packet unless a genuinely NEW MATERIAL
boundary is discovered (new consumer, schema, ceiling, seam, or risk not
already settled). A new material-boundary omission returns the packet to
DESIGN INCOMPLETE; a mere design preference does not.

## Review focus (answer each)

1. Fidelity: does PRD-306 faithfully implement the review-clean design
   (provider/scope, producer architecture, P0 outputs, formulas/units, sign
   convention, structural definitions, 0DTE, admissibility F-contract,
   provenance, explicit cuts)?
2. Authority/scope drift: does any language accidentally create decision
   authority, or expand scope beyond the settled _SPX manual/local-first slice?
3. FILES completeness: is any surface the implementation must touch missing
   from the FILES cone? Is anything in the cone that should not be?
4. Acceptance discrimination: is any acceptance criterion a proxy or
   non-discriminating (green without verifying correspondence to reality)?
   Are the R1-R37 FAIL lines binary and observable?
5. Ceiling: is `<= 400` net production LOC plausible for the frozen design,
   or does the PRD understate first-class validation/provenance/coverage
   surface?
6. Isolation posture: does the PRD keep implementation isolated
   (no cuttingboard coupling either direction), manual, local-first, one
   provider, stdlib-only, no workflow/cadence/consumer?
7. DRIFT CHECK (PRD-186): does PRD-306 conflict with a VISION non-goal or
   principle, and does it leave any PROJECT_STATE claim stale?

## Verdict vocabulary (choose one)

- ACCEPT
- ACCEPT-WITH-NITS
- REQUIRED-CHANGES

Follow the repository's ordinary bounded PRD review/correction rule (GOV-1):
findings once, author addresses once, gate closes. A second round happens only
because Dustin asks.

## Output artifact

- Write the review to: `docs/prd_history/PRD-306.review.claude.md`
  (Claude slot). A commissioned second-model review would instead use
  `docs/prd_history/PRD-306.review.<model>.md` per GOV-1 naming.
- Record: VERDICT, the pinned SHA reviewed, REQUIRED CHANGES, RECOMMENDED
  CHANGES, RATIONALE, and the DRIFT CHECK.
- The review artifact is durable and in-tree; it is not an ephemeral comment.

## After the review

- If ACCEPT / ACCEPT-WITH-NITS: the package is ready for Dustin's Gate A
  (Dustin's act only; no agent issues or infers Gate A).
- If REQUIRED-CHANGES: the author applies the single bounded correction cycle
  to the exact reviewed revision, then re-pins.
- Implementation authority comes SOLELY from the reviewed PRD-306 + Dustin's
  explicit Gate A. The Ultracode implementation charter
  (`PRD_306_ULTRACODE_IMPLEMENTATION_CHARTER_2026-08-20.md`) may be dispatched
  only after both are satisfied.
