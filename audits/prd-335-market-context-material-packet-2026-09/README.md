# PRD-335 MATERIAL packet - Market Context Completion + Second Editorial Pass

STATUS: PRD authored from Helm's ruling, fresh-context reviewed, one-cycle
corrected. Carries NO implementation authority. HELD FOR GATE A (Dustin).

- Base repo SHA: fa101cc68963ed1c9704f94c6f54a182bfc86bac (PRD-334 merged, PR #322)
- Reserved PRD number: PRD-335 (verified free)
- Design (frozen): PLAN.md, SHA-256
  383e696f4ce78b38231e92c2b5ce6503edb6a523b73f1754c709011fc6467290
- PRD (for Gate A): PRD-335.md, corrected revision SHA-256
  c92c69c51910d22d7ece423966127cd453c4179dfe6d55b6d373ed6047212c69
  (reviewed revision was 4b3f0dc4...; the delta is exactly the PRD reviewer's
  five ACTION items)
- Reviews: REVIEW.astra.md (packet: 2 Codex events), REVIEW.prd.md (the PRD
  fresh-context review + one-cycle correction record)
- Authoring: Fable 5.1 (plan) + Opus orchestrator (PRD from the ruling); recon
  and adversarial/independent review by Codex (Astra) subagents.

## Provenance chain (all complete except Gate A)

1. MATERIAL packet (PLAN.md) - GOV-2 bounded cycle: Astra INITIAL REVIEW
   CHANGES-REQUIRED (8 findings) -> one Fable correction -> EXACT-HEAD CONFIRM
   7/8 resolved, no new omission (REVIEW.astra.md).
2. Helm design-direction ruling 2026-09-05: D-1..D-6 (below); CLASS=CONSUMER,
   LANE=HIGH-RISK, MATERIAL=YES; correct the F-2d residue while authoring.
3. PRD-335.md authored from the ruling (4b3f0dc4).
4. Fresh-context MATERIAL PRD review (Codex): CHANGES-REQUIRED /
   ready-after-listed-fixes; 5 bounded findings; OBSERVATIONAL-ONLY = YES
   (independently proven); D-1..D-6 faithfully retained (REVIEW.prd.md).
5. One-cycle correction applied (all 5 findings) -> c92c69c5.
6. REMAINING: Dustin Gate A on c92c69c5 -> separate Opus IMPLEMENT session ->
   implementation review -> merge. Gate A NOT granted.

## Helm ruling (D-1..D-6), now encoded in PRD-335.md

- D-1 2Y: BUILD NOW - actual US 2Y via a bounded FRED/DGS2 daily carrier with
  observation-date + mixed-cadence honesty; 2Y/10Y/30Y all present; STOP-and-
  report if materially larger than the bounded carrier; no futures as yield.
- D-2 History: KEEP PRD-334 R6 placement.
- D-3 Tradables grid: KEEP, captioned; macro-underlying vs trade-vehicle
  distinction explicit.
- D-4 BTC: muted demotion; ingestion + macro-pressure vote preserved.
- D-5 Regime under STAY_FLAT: RETAIN compact; remove duplicated permission prose.
- D-6 Trend set: KEEP the PRD-110 six; Trend Structure recorded PROVISIONAL.

## Safety (the load-bearing guarantee), independently confirmed

2Y/30Y/USDJPY are DISPLAY-ONLY. A driver can vote only if wired into ALL FOUR of
macro_pressure._COMPONENT_KEYS (:18-23), _COMPONENT_FIELDS (:25-30), a
_classify_driver branch (:57-90; :90 raises for strangers), AND the aggregation
list (:126-133). PRD R1/R8 keep the new keys out of all four; both driver-key
whitelists (contract + delivery/payload) are updated and kept in sync by a
guard-sync test. The PRD reviewer wired each new driver in-memory and observed
LONG sizing 1.0 -> 0.75, proving the R8 fence can go RED.

## Proposed Gate-A ceiling (ESTIMATED - Gate A sets the binding one)

<= 12 production files; net production LOC approx +40 (subtractive editorial
approx -160 offset by the actual-2Y FRED carrier + as_of plumbing approx +200);
tests approx +300/-60 incl. the new fence module; two whole-dashboard goldens
regenerate once. FILES list is in PRD-335.md.

Nothing here authorizes implementation. No branch, no merge, no auto-merge.

## Post-Gate-A FILES amendment (GOV-2 renewal; Helm ruling 2026-09-05, F1)

The implementation's authorized R1/R4/R5/R6 changes broke pins in five
test/oracle files co-located with the changed surfaces. Helm judged all five
required consequences (no production-ceiling increase) and ordered a mechanical
GOV-2 renewal. The FILES list in this packet's `PRD-335.md` (and the canonical
`docs/prd_history/PRD-335.md`) now adds exactly:
`tests/data/setup_chart_legacy_oracle.json` (golden_regions SHAs re-pin; the
byte-frozen SVG oracle sha + `cases` unchanged), `tests/test_dash_system_state.py`,
`tests/test_dash_candidates.py`, `tests/test_phase1.py`,
`tests/test_optional_macro_drivers_dedup.py`. Production FILES remain 12 / <= 12;
NO new production or design surface is authorized. Amended Gate A pending a
fresh-context PRD-amendment review scoped to these three questions: (1) are the
five files required consequences of PRD-335, (2) does the amendment broaden any
production/design authority, (3) does the final FILES list cover the
Stage-0 -> implementation diff.
