# PRD-336 MATERIAL packet - Cockpit context polish (final pre-live pass)

STATUS: PRD authored from Helm's charge, fresh-context reviewed, one-cycle
corrected. Carries NO implementation authority. HELD FOR GATE A (Dustin).

- Base repo SHA: cf693992043adfaec6b3e66e60f956044a90bc35 (origin/main; PRD-335
  merged, PR #323). Branch: claude/prd-336-cockpit-context-polish.
- Reserved PRD number: PRD-336 (verified free).
- Design (frozen): PLAN.md, SHA-256
  e345464fa0bf45ed7b4e4b751b468cc78b5397083e32d2ec22b788f1c7f6204e
- PRD (for Gate A): PRD-336.md, corrected revision SHA-256
  6af7e3f5c746632c04554933c034497f6bad6bebbbc4fbbeb31352a6e5cb472e
  (identical to docs/prd_history/PRD-336.md; the delta from the reviewed revision
  is exactly the one R11 correction + the notification Gate-A note).
- Review: REVIEW.prd.md, SHA-256
  3d0677b14d42d9e0c83c3675db2b5254a2f527757b70cb79746c60651fa042c9
  (the fresh-context independent PRD review + the author correction-cycle
  disposition).
- CLASS: CONSUMER. LANE: HIGH-RISK. MATERIAL: YES.
- Test baseline at base: 4562 passing, 1 xfailed (CI truth on main, #323).

## What this pass does

The last bounded cockpit-polish pass before live market use. Five DISPLAY-ONLY
observations (5Y via FRED DGS5 daily; EURUSD, USDCAD, NG, ETH via yfinance) behind
the PRD-335 six-site vote fence; a bounded-window FRED reliability fix + DGS5 + a
new FRED carrier red test; a four-across responsive macro cockpit (stacked cell);
and four renderer-only edits (SPY copy, Market Context strip, History order/
visibility, Trend/Vehicles conditional de-duplication). Adds NO decision authority.

## Provenance chain (all complete except Gate A)

1. Helm charge (2026-09-06): CLASS=CONSUMER, LANE=HIGH-RISK, MATERIAL=YES; R1..R12
   + decision-authority fence + visual acceptance.
2. Base-correct recon at cf693992 (macro tape, drivers/FRED carrier, the six vote
   sites + fence test, layout regions, test/golden/browser harness).
3. Design-time de-risking (read-only probes):
   - FRED PROVEN: unbounded id=DGS2 -> 208776 bytes / 13114 rows; bounded
     &cosd=<recent> -> 198 bytes / 11 rows (~1000x); DGS5 exists and parses.
   - yfinance INCONCLUSIVE from the design env (the known-good control JPY=X also
     returned None) -> symbol resolution is a REQUIRED implementation gate.
4. PLAN.md (design authority) + PRD-336.md authored; mechanical verification pass
   (symbols/lines/FILES/FAIL-lines/lane) via prd-authoring-verified.
5. Fresh-context independent review (REVIEW.prd.md): VERDICT CHANGES-REQUIRED with
   ONE blocking finding (R11 partial-price-gap); OBSERVATIONAL-ONLY = CONFIRMED
   (the six vote sites are the complete decision surface); all other axes CLEAR.
6. One-cycle correction applied (R11 predicate + FAIL line + partial-snapshot
   fixture; notification Gate-A item) -> the corrected revision above.
7. REMAINING: Dustin Gate A on the corrected PRD-336.md -> a separate Opus/Fable
   IMPLEMENT session -> implementation review -> merge. Gate A NOT granted.

## Safety (the load-bearing guarantee), independently confirmed

The five new drivers are DISPLAY-ONLY. A driver acquires a vote only by being
wired into one of six sites: macro_pressure._COMPONENT_KEYS (:18-23),
_COMPONENT_FIELDS (:25-30), the _classify_driver branches (:57-90), the
_overall_pressure aggregation list (:126-133), regime.py reads/raw_votes
(:159-176), and macro_tape_layout.MACRO_BIAS_DRIVERS (:97-99). PRD R2/R4/R5/R6/R13
keep all five new keys out of all six; both driver-key whitelists (contract +
delivery/payload) are kept in sync by a guard-sync test; R13 adds a regime symbol-
absence assertion (site 5) the PRD-335 fence lacked. The independent reviewer
grepped every by-key decision consumer and confirmed macro_pressure is the only
one - OBSERVATIONAL-ONLY CONFIRMED.

## Proposed Gate-A ceiling (ESTIMATED - Gate A sets the binding one)

<= 8 production files; net production LOC roughly flat (~ +73 / -78). Tests ~ +260
/ -40 incl. a NEW FRED carrier test module + the extended display-only fence; two
whole-dashboard goldens regenerate once; a new PRD-336.evidence/measure.py browser
harness. FILES list is in PRD-336.md.

## Fresh-context independent review recommendation (charge deliverable 13)

- The fresh-context PRD review in this packet (REVIEW.prd.md) was performed by a
  Claude subagent with NO authoring context (the Adversary seat), not by the
  author. It satisfies the GOV-2 fresh-context requirement for the DESIGN packet
  and returned OBSERVATIONAL-ONLY CONFIRMED after one correction.
- RECOMMENDED before/at Gate A: because this is a HIGH-RISK CONSUMER MATERIAL PRD
  touching the only non-yfinance carrier and a persisted multi-reader schema, Helm
  may additionally commission a SECOND-MODEL fresh-context review (Codex/Sol) of
  the corrected PRD-336.md at its exact SHA (as PRD-335 did with Astra), focused on:
  the R3 FRED bounding + fail-closed contract, the R11 per-symbol fallback
  predicate, and the decision-authority fence extension (regime site-5 closure).
  This is a recommendation; commissioning is Helm's per PRD-242.

Nothing here authorizes implementation. No merge, no auto-merge. The branch and a
draft PR are held for Dustin's push and Gate A.
