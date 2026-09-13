# CODEX EVENT 4 -- FINAL EXACT-HEAD CONFIRMATION (R3 exclusive-writer; owner Option A) (GOV-2 s2)

EVENT: FINAL EXACT-HEAD CONFIRMATION (R3 exclusive-writer)
REVIEWER: gpt-5.6-sol (Codex), fresh-context independent.
RUN-ISOLATION / INDEPENDENCE EVIDENCE (GOV-2 s2): cbagent systemd --user transient unit, fresh
codex exec, no shared session memory, read-only sandbox, exact-SHA guard verified HEAD == the
reviewed SHA. cbagent job id: codex-20260913T020106Z-7b03.
EXACT REVIEWED SHA: 82446028c1cfc9ed94b460af2228736179709459 (structural packet, s14 / FINAL R3
correction).
DATE: 2026-09-13.

## Result
R3 STATUS: CLOSED.
R1/R2/R4 REGRESSION STATUS: none.
VERDICT: CLEAN.
REVIEW-CLEAN: YES.

1. R3 is closed: s14 mandates one approved resolver/persistence path for every authoritative
   carrier, prohibits all other field/envelope authorship or mutation, makes a second writer
   fail CI, and correctly classifies the ui/contract.json cp as a verbatim carrier copy.
2. No same-project downstream module can manufacture accepted persisted canonical permission
   state without the approved path (exclusive field authorship + R4 proxy removal + fail-closed
   validation).
3. No regression: s14 changes only persisted-origin enforcement; s13's required-EP signatures
   (R1), closed authoritative-channel registry (R2), and proxy stripping (R4) are retained.
4. The Option A structural mechanism is review-clean within the stated same-project trust
   boundary.

## GOV-2 disposition -- DESIGN FROZEN (owner HARD STOP)

Per Dustin's R3 ruling ("If Sol returns CLEAN or CLEAN WITH NITS with no invariant weakness:
freeze the design and STOP. No further correction cycle is authorized."): the design is FROZEN
review-clean at 82446028. No further design correction is made.

This is the first CLEAN verdict of the effort on the MATERIAL packet. Codex packet events on this
completeness-by-construction packet: EVENT-1 (initial, unsound), EVENT-2 (confirmation, unsound),
EVENT-3 (owner correction-2 confirmation, R3 unsound), EVENT-4 (this, owner Option A, CLEAN).
Each correction beyond the standard bounded cycle was explicitly OWNER-AUTHORIZED (GOV-2 s6 /
the owner's rulings). The frozen mechanism: (R1) render/write functions require an
EffectivePermission; (R2) closed authoritative-channel registry incl. the Markdown writer;
(R3) code-enforced exclusive-writer boundary for the persisted canonical field (no crypto);
(R4) proxies stripped from authoritative renderers; fail-closed on absent/invalid; structural
AST/CI tests as the completeness proof; same-project trust boundary.

## What this unblocks (Dustin's next steps -- NOT this charter)

The MATERIAL packet is now review-clean, so (GOV-2 s2) Dustin MAY issue the design-direction
ruling FROM this review-clean packet, then a PRD is drafted and receives the fresh-context
independent PRD review, then Gate A. Open owner design-direction questions remain: Q1 session
validity; Q3 structure (two ordered PRDs recommended); Q4 recovery; Q6 carrier home; Q7
classification/lane/PRD-242. PRD-339 design (0348cee1) remains provisional and must be reconciled
to this frozen architecture. No PRD / Gate A / implementation / push occurs until Dustin rules.
