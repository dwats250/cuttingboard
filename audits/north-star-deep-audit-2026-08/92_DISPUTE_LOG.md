# Dispute / Owner-Ruling Log (Phase 2 synthesis — Fable)

**Scope discipline:** entries below are only genuine open Dustin-held decisions, authority conflicts, or unresolved factual conflicts. Explicitly excluded, per the settled rules: comments 20/21 (ruled 2026-08-01 — closed), the BLOCKED/PARKED administrative holds themselves (settled rules 4–5 — administrative, not disputes), AMENDMENT-001 (closed) and AMENDMENT-006 (ruled), the deferred-by-design owner items tracked in `91` §5 (macro track, fidelity disposition, Q27/Q28, CB-16, NS-3/4/6/7 vocabulary — already recorded as parked with no pending question in this audit), and AMENDMENT-005 (gates nothing; carried inside DR-007 for one-touch closure rather than as its own dispute). Eight entries, matching the eight open-ruling flags in the Truth Matrix.

---

## DR-001 — Runway promotion and CB-01 deferral
- **Question:** Which runway does Dustin promote — Option A (resume CB-02 chain) or Option B (NS-2 product slice) — and, in either case, is CB-01 (open Critical kill-switch bypass, falsely reporting clear) explicitly deferred by owner ruling or scheduled ahead of new product work?
- **Affected matrix rows:** TM-040 (primary); TM-017, TM-037.
- **Options:** (a) schedule CB-01 remediation ahead of any promotion; (b) promote a runway with an explicit, recorded CB-01 deferral ruling; (c) no promotion yet.
- **Consequences:** (a) delays product delivery but closes the safety bypass first; (b) delivers product sooner but must be a positive recorded act — the current docs place CB-01 non-blocking by classification, not by ruling (the exact gap the P1 connector comment raised, itself still in the TM-080 queue); (c) preserves the status quo, NOW slot stays vacant.
- **Recommended default:** none forced — this is precisely the promotion authority TM-026 reserves to Dustin. The evidence does establish that silent deferral is not an available option (Program's own stop exception for unsafe execution).
- **Can work proceed meanwhile:** yes — all corrections (PR-A…PR-E) are doc/administrative and independent of runway choice. Only product implementation waits.

## DR-002 — PRD-268 disposition
- **Question:** Approve, return to PROPOSED, or deprecate PRD-268 (unruled design fork; L0 closure depends on it)?
- **Affected matrix rows:** TM-020 (primary); TM-037.
- **Options:** approve / return / deprecate — exactly the three the Ledger, registry, and Program all preserve (B-015, C-053).
- **Consequences:** approve → HIGH-RISK implementation path opens under normal gates; return → fork re-drafted; deprecate → L0 closes without it. Until any of the three, CB-02's chain (DR-004) cannot fully clear and comment 14's PARKED-label residual keeps needing the CP-004 qualifier.
- **Recommended default:** none — genuine design fork; evidence is neutral among the three.
- **Can work proceed meanwhile:** yes for all corrections (CP-004's qualifier deliberately encodes "IN PROGRESS / DECISION REQUIRED", which is true under all three outcomes).

## DR-003 — PRD-271 Gate A and NS-2 ordering confirmation
- **Question:** (i) Dustin's Gate A ruling on PRD-271's session-correct-ORB design; (ii) confirmation that the NS-2 MATERIAL packet review precedes that Gate A, per GOV-2 §2, overriding the Program's current entry-condition ordering.
- **Affected matrix rows:** TM-021, TM-018 (primary); TM-043, TM-030, TM-031, TM-058, TM-063.
- **Options:** (ii-a) confirm GOV-2-first ordering and land CP-005; (ii-b) rule an explicit documented exception keeping Gate A first (would need its own GOV-2-consistent rationale). (i) is Gate A itself — approve/amend/reject the ORB design when reached.
- **Consequences:** (ii-a) removes the false-permission window comment 18 identified; (ii-b) creates a recorded exception rather than a silent contradiction. Without (i), NS-2B, CB-07 closure, and the ORB remedy all stay held.
- **Recommended default:** (ii-a). GOV-2 is ratified and binding (TM-016); the Program is planning text with no authority (TM-007). Authority precedence resolves the text conflict; only the confirmation and the Gate A ruling itself are Dustin's.
- **Can work proceed meanwhile:** PR-A yes; PR-B (CP-005) waits for (ii); all ORB implementation waits for (i).

## DR-004 — OPT-0 approval and CB-02 resumption
- **Question:** Does Dustin approve OPT-0's carrier, reason semantics, and implementation seam (after exact-head independent confirmation), and thereby permit the ordered CB-02 resumption sequence (which also requires DR-002's L0 closure)?
- **Affected matrix rows:** TM-022, TM-037 (primary); TM-038, TM-054.
- **Options:** approve and resume under the ordered GOV-2 sequence / narrow the packet / retire the packet.
- **Consequences:** approval unblocks OPT-1 and eventually ODATA; narrowing or retiring keeps the smallest-contract refusal question open and the parked options-data backlog parked. Any resumption before this ruling would be exactly the premature-advance risk TM-022 records.
- **Recommended default:** none — owner approval is the defined exit condition itself; evidence cannot substitute for it.
- **Can work proceed meanwhile:** yes — nothing in the correction plan touches the CB-02 chain.

## DR-005 — Was PR #187 itself MATERIAL under GOV-2?
- **Question:** GOV-2 §1 classifies any governance-guardrail change as unconditionally MATERIAL; PR #187's Ledger imposes new guardrails (one-NOW invariant, packet template, ratification points), and no North-Star MATERIAL packet or review artifact exists in Domain A's owned/cited sources. Did PR #187 require GOV-2 MATERIAL intake, and if so what remediation applies?
- **Affected matrix rows:** TM-078 (primary); TM-016.
- **Options:** (a) rule it was MATERIAL and record a documented retroactive exception (this completed North Star deep audit itself being the substantive compensating review); (b) rule it was MATERIAL and commission a formal retroactive GOV-2 sequence; (c) rule it was not MATERIAL, with a recorded reason.
- **Consequences:** (a) closes the precedent gap cheaply and honestly; (b) is the maximal-integrity path at real cost; (c) requires a reasoned reading of GOV-2 §1 that future intakes will inherit — the riskiest option for the process spine if the reasoning is thin.
- **Recommended default:** (a) — but stated as a recommendation only; the classification power is Dustin's, and Domain A's own confidence here is MEDIUM (an undocumented review outside its sources cannot be excluded).
- **Can work proceed meanwhile:** yes — corrections and rulings DR-001..004 are unaffected; this settles precedent, not current authority.

## DR-006 — NS-9C freshness-vocabulary sequencing
- **Question:** Program §4 names NS-2A + NS-9C as shared substrate while all of NS-9 sits LATER behind the NEXT NS-2 slice. Should the bounded NS-9C freshness-vocabulary contract be split/promoted as a prerequisite for the first freshness-consuming packet, or is a compatibility requirement inside the NS-2A packet sufficient?
- **Affected matrix rows:** TM-070 (primary); TM-030, TM-069.
- **Options:** (a) split/promote NS-9C ahead of NS-2 (the connector comment's ask, which Domain A found supported); (b) keep NS-9 LATER and bind NS-2A's packet to explicit NS-9C-forward-compatibility acceptance language (Domain F's reading: no blocking conflict, coherence note only).
- **Consequences:** (a) adds a packet before the product win but guarantees one freshness vocabulary; (b) preserves the runway but accepts a bounded rework risk if NS-2A's local freshness handling later diverges from NS-9C.
- **Recommended default:** (b), operationalized at NS-2 MATERIAL intake (where Dustin rules design direction anyway) — F's arrow-direction analysis is the more careful textual reading, and (b) converts A's supported risk into an enforceable acceptance condition rather than a resequencing.
- **Can work proceed meanwhile:** yes — the decision naturally lands at NS-2 intake; nothing else waits on it.

## DR-007 — CITED-grant amendments and the bounded routed-queue adjudication packet
- **Question:** Does Dustin (i) grant AMENDMENT-002 (workplan + doctrine sections → Domain A CITED), AMENDMENT-003 items 1–3 (workplan, stage0-01, stage0-03/verify-03 → Domain B CITED) and decide item 4 (PR #184/#185 content via `gh` access) and item 5 (OPT-0 findings-artifact path — currently not enumerable; needs Dustin's pointer or stays open), (ii) grant AMENDMENT-004 (five named files → D1 seams), (iii) defer/decline AMENDMENT-005 (gates nothing), and (iv) authorize one bounded post-audit adjudication packet (CP-007) that uses those grants to disposition the 18 routed PR #187 comments and close the TM-003 coverage residual?
- **Affected matrix rows:** TM-080, TM-003 (primary); confidence uplifts only for TM-022, TM-036, TM-060.
- **Options:** grant all and authorize CP-007 / grant selectively (CP-007 then dispositions only what its grants reach, recording the remainder as permanently BLOCKED/PARKED-by-ruling) / decline all (the 18 comments stay in the routed queue indefinitely, which Dustin's existing ruling already permits).
- **Consequences:** full grant closes the last UNKNOWN queue and lifts three MEDIUM-confidence rows; selective grant is fully workable and bounded; declining leaves no substantive blocker but leaves the PRD-228 record permanently partial for 18 threads.
- **Recommended default:** grant AMENDMENT-002, -003 items 1–3, and -004 (each names exact artifacts, no open-ended sweep; each was correctly logged and left un-investigated); defer item 4 unless Dustin wants PR-packet verification; leave item 5 open pending his pointer; defer AMENDMENT-005; authorize CP-007 as a single bounded packet.
- **Can work proceed meanwhile:** yes — everything except CP-007 (PR-E).

## DR-008 — CB-29 recording mode
- **Question:** `FINDING_STATUS_MATRIX.md` (2026-07-30) still records CB-29 as OPEN/Low while the Program's later text moves it to PARTIAL (fidelity-delta pointer merged, `f6d508f`). Is the matrix a frozen historical snapshot receiving a dated addendum, or is it updated in place?
- **Affected matrix rows:** TM-050 (primary).
- **Options:** (a) dated addendum on the CB-29 row pointing to Program's superseding PARTIAL status, matrix otherwise frozen; (b) in-place row update; (c) declare the Program the sole live-status source and leave the matrix untouched.
- **Consequences:** (a) preserves audit-artifact immutability while fixing the misleading read; (b) is simplest but erodes the snapshot property of a dated audit artifact; (c) costs nothing now but leaves a documented trap for any reader who consults the matrix first.
- **Recommended default:** (a) — consistent with how this audit treats its own frozen artifacts. (CB-29's remaining substance — the missing canonical adoption record for the strategy-repo relationship — is existing tracked debt, deliberately not opened here.)
- **Can work proceed meanwhile:** yes — only PR-C (CP-008) waits.
