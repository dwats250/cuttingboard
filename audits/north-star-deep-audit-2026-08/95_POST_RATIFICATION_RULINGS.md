# Post-Ratification Rulings

Dustin ratified the North Star deep-audit synthesis and correction plan on
merge of PR #190 (`bf7c6d4513039760eaef3d50b749ead4c71ec0eb`). Per
`00_AUDIT_CHARTER.md` §13, `92_DISPUTE_LOG.md` became a historical,
non-living record at that instant — it is not edited for rulings that land
after ratification. Per `93_CLOSED_CORRECTION_PLAN.md` CP-008's acceptance
test (the naming convention this file follows), a dispute-log entry ruled
after ratification is instead recorded here, in a new dated entry, one entry
per ruling, in the order rulings land.

This file is itself a living record: append a new dated entry per ruling. Do
not edit `92_DISPUTE_LOG.md` to record a post-ratification ruling.

---

## DR-001 — Runway promotion and CB-01 deferral (ruled 2026-08-03, Dustin)

**Question (`92_DISPUTE_LOG.md` DR-001, frozen text):** Which runway does
Dustin promote — Option A (resume CB-02 chain) or Option B (NS-2 product
slice) — and, in either case, is CB-01 (open Critical kill-switch bypass,
falsely reporting clear) explicitly deferred by owner ruling or scheduled
ahead of new product work?

**Affected matrix rows (informational; `90_NORTH_STAR_TRUTH_MATRIX.md` itself
is not edited by this ruling):** TM-040 (primary); TM-017, TM-037.

**Ruling (Dustin, verbatim):**

> I approve DR-001 as follows.
>
> Runway:
> Promote Option A and resume the bounded CB-02 / NS-1E chain under the
> existing GOV-2 sequence. NS-2 is not promoted at this time.
>
> CB-01:
> CB-01 must be fixed first. I do not authorize silent or explicit deferral
> of the hourly kill-switch bypass.
>
> The CB-01 remediation must be a narrow change that makes the hourly alert
> path evaluate and report the kill switch consistently with the existing
> daily path. It must merge before CB-02 reaches implementation Gate A.
>
> Parallel work:
> The owner rulings for PRD-268 and OPT-0 may proceed while CB-01 is being
> fixed.
>
> Scope limit:
> Promoting CB-02 authorizes completion of the already-defined
> smallest-contract refusal path only. It does not authorize broader options
> architecture, additional infrastructure, schema expansion beyond the
> accepted contract, or adjacent work.
>
> Completion:
> After CB-01 is merged and the PRD-268 and OPT-0 rulings are complete,
> resume the existing CB-02 sequence through exact-head confirmation,
> fresh-context PRD review, Gate A, implementation, review, and merge.
>
> After CB-02 lands, the runway must be reassessed before any further
> platform or infrastructure work is authorized.

**Disposition:**
- Option A / CB-02 chain: promoted, resumes under the existing GOV-2
  sequence.
- NS-2: not promoted at this time.
- CB-01: not deferred. Must merge before CB-02 reaches implementation
  Gate A. See "CB-01 remediation status" below — this ruling authorizes and
  requires the fix; it does not itself authorize implementation, which
  remains gated on its own required review sequence.
- DR-002 (PRD-268 disposition) and DR-004 (OPT-0 approval): may proceed in
  parallel with CB-01 remediation. Not decided by this entry.
- CB-02 scope ceiling: this promotion authorizes completion of the
  already-defined smallest-contract refusal path only — no broader options
  architecture, no additional infrastructure, no schema expansion beyond the
  accepted contract, no adjacent work.
- Runway reassessment: required after CB-02 lands, before any further
  platform or infrastructure work is authorized.

**CB-01 remediation status (recorded by the implementing session, not part
of Dustin's ruling text above):** `FINDING_STATUS_MATRIX.md` carries CB-01 at
**Critical** severity. Under GOV-2 §1, "the proposed work is MATERIAL when
... it resolves a Critical or High finding" — CB-01's remediation matches
this trigger unconditionally; GOV-2 grants no discretion to declassify a
change that already matches a listed trigger (the same reading DR-005 applies
to a different guardrail-change trigger). MATERIAL classification does not
force `LANE: HIGH-RISK` by itself (GOV-2 §1: "STANDARD at minimum, HIGH-RISK
only when the Lane Downgrade Prohibition's own triggers fire independently"),
but it does require GOV-2 §2's full upstream sequence — provisional MATERIAL
packet, independent Codex packet review, one consolidated correction,
independent exact-corrected-head confirmation, and only then a
design-direction ruling — to complete and be review-clean *before* a Stage-0
PRD may be drafted (GOV-2 §4: "No downstream authority before upstream
review-clean"). This ruling promotes the runway and fixes CB-01's required
outcome and sequencing (must merge before CB-02 Gate A); it does not, and
under GOV-2 §2 step 6 cannot, substitute for CB-01's own upstream MATERIAL
packet review — no such packet has been opened or Codex-reviewed for CB-01
specifically. CB-01 Stage-0/PRD drafting therefore remains held pending that
packet sequence; see the PR that carries this entry for the full reasoning
and options.

**Thread disposition (PRD-228, `93_CLOSED_CORRECTION_PLAN.md` CP-006 phase
3):** comment 7's confirmed-but-unresolved finding (CB-01 non-blocking
ordering) may now be replied to on PR #187, citing this ruling. That reply is
administrative follow-up and is not performed by this entry.
