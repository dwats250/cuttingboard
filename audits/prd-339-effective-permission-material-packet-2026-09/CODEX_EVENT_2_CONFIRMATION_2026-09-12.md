# CODEX EVENT 2 -- EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 s2/s7)

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION
REVIEWER: gpt-5.6-sol (Codex), fresh-context independent.
RUN-ISOLATION / INDEPENDENCE EVIDENCE (GOV-2 s2): dispatched via `cbagent` as a systemd
--user transient unit running a fresh `codex exec` with NO shared memory/context with the
authoring session, read-only sandbox, exact-SHA guard verifying HEAD == the confirmed SHA
before launch. cbagent job id: codex-20260912T225240Z-2e0e.
EXACT CONFIRMED SHA: e006141c14a6733854ffb537f35b540303bc1e55 (packet rev 2).
DATE: 2026-09-12.

## Prior findings confirmed at this head
- F1 RESOLVED (delivery payload / report / CLI class inventoried, s4 D/E/F).
- F2 RESOLVED (premarket/postmarket readers, s4 G).
- F3 RESOLVED (reuse-vs-new is now owner choice Q6; "reuse impossible" removed, s6).
- F4 RESOLVED (F8 Telegram live seam correctly traced to notifications/__init__.py, s3/s4C).
- F5 RESOLVED (atomic publish bundles enumerated, s7).
- F6 RESOLVED (estimated surface rebuilt by output class, s9).

## VERDICT: DESIGN INCOMPLETE (GOV-2 s6 boundary reset -- SECOND discovery)

REMAINING OMISSION / BOUNDARY-RESET: YES.
A further previously-omitted end-to-end permission-consumer class remains: the MARKET-MAP
decision-guidance artifact/schema and candidate-card renderer.
- `cuttingboard/market_map.py:187-225` assigns GRADE_A_PLUS / SETUP_ACTIONABLE from
  market/regime proxies.
- `cuttingboard/market_map.py:479-509` converts that proxy into
  `trade_framing.if_now = "TAKE"` INDEPENDENT of canonical outcome / effective permission.
- `cuttingboard/delivery/dashboard_renderer.py:2410-2421` renders that field as the
  human-facing `IF NOW` directive; `:2465-2480` renders `preferred_trade_structure` as
  `PLAY`.
- `logs/market_map.json` is persisted and PUBLISHED in the daily bundle; packet rev-2 s4
  class A inventoried only the A+ tier LABEL, not this action-bearing artifact/schema/
  renderer SEAM, and Q8 omitted `market_map` from its consumer-scope alternatives.

## GOV-2 s6/s7 consequence (STOP; owner choice)

This is a further omitted class discovered AFTER the one permitted s6 first-discovery
inventory refresh (packet rev 2). Per GOV-2 s6 and s7, the packet returns to DESIGN
INCOMPLETE and the bounded correction cycle STOPS -- no further incremental patching. Dustin
chooses whether to:
- REBUILD the packet from a fresh frame (perform a truly exhaustive producer-to-final-
  consumer permission inventory FIRST, then re-frame the boundary); OR
- NARROW the packet's claim to a well-defined authoritative subset (e.g. a named set of
  served decision surfaces) with everything else explicitly documented as non-authoritative
  analytical context; OR
- PARK the packet.

Two independent boundary resets in one cycle (delivery/report/CLI/premarket/postmarket, then
market_map/candidate-card) indicate the permission-consumer surface is genuinely sprawling
and the discovery boundary -- including the provisional PRD-339 design's boundary at
0348cee1 -- was materially incomplete. This is a design-direction signal for the owner, not
a defect to patch here.

## Confirmed non-defects
- Owner questions Q1/Q3/Q4/Q6/Q7/Q8 remain genuine owner decisions, not matters settled by
  code (Q8 must be extended to include market_map on any rebuild).
- The Astra ACCEPT and prior Sol CLEAN consultations are accurately framed as provisional
  design consultations that satisfy neither this packet review nor the post-ruling PRD
  review.

## Downstream authority

The MATERIAL packet is NOT review-clean (GOV-2 s2: a corrected head that reopens as DESIGN
INCOMPLETE is not review-clean). Therefore:
- No design-direction ruling may be issued "from a review-clean packet" (s2 step 6) yet.
- No PRD drafting/review, no Gate A, no implementation may proceed (s4).
- What IS ready for Dustin now is the s6 rebuild/narrow/park decision.

PRD-339 remains PROVISIONAL and non-authoritative; not modified by this cycle.
