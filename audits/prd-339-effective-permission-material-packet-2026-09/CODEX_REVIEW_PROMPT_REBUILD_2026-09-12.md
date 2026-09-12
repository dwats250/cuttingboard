GOV-2 INITIAL PACKET REVIEW -- PRD-339 DECISION-AUTHORITY FRESH-FRAME REBUILD (gpt-5.6-sol)

Independent Codex reviewer, fresh context, read-only, no edits, no implementation. Your job
is to try to FALSIFY the packet's completeness -- NOT to approve it. GOV-2 principle: no
agent certifies the completeness of the boundary it chose; you are that check. The prior
(failed) packet reached DESIGN INCOMPLETE after TWO boundary resets; this is a fresh-frame
REBUILD. Judge whether the boundary is now genuinely complete.

## Base
- Repo at the exact committed rebuild-packet SHA. Confirm HEAD (git rev-parse HEAD) and
  report it; if the tree does not match the SHA you were told, report the mismatch.
- Packet under review: audits/prd-339-effective-permission-material-packet-2026-09/
  PRD_339_DECISION_AUTHORITY_REBUILD_PACKET_2026-09-12.md (read in full).
- You MAY and SHOULD read source to test claims.

## The decisive question (GOV-2 completeness)
Does the packet enumerate the COMPLETE decision-authority surface -- every code path that can
tell Dustin (or a downstream component) to trade / not-trade / take / play / stay-flat /
observe-only / that a setup is ready/permitted/prohibited/qualified/actionable, by SEMANTICS
not literal field names? Try hard to find a code path that bypasses the packet's six seams
(S1 runtime outcome, S2 contract system_state, S3 market_map trade_framing, S4 qualification/
grade tier, S5 market_control_card, S6 operator-lock/HALT). If you find a previously-omitted
consumer CLASS / renderer / audit carrier / schema surface / end-to-end seam or a genuine
bypass path, name it (file:line) and mark BOUNDARY-RESET -- that returns the packet to DESIGN
INCOMPLETE (do not soften it to a nit).

## Also attack
1. The A/B/C/D/E/F classification (s3): any surface mis-classified (e.g. an INFERS consumer
   called presentation-only, or a real origin called derived)?
2. The duplicate/conflicting-origin cluster (s5): are A5-vs-A6, tradable-vs-outcome,
   _action_label, the two permission tables, and the 4-site lock/kill duplication all real
   and correctly described against source?
3. The restore/regression seams (s6): are the plain-overwrite vs monotonic carrier claims
   accurate? Is any permission-bearing carrier mis-labeled?
4. The root-cause clusters (s8) and minimum implementation boundaries (s9): coherent, and do
   they actually close the cited defects? Any missing root cause?
5. FILES/LOC estimate (s11): plausibly complete for the stated scope; labeled as estimate?
6. Owner vs factual (s12): are Q1/Q3/Q4/Q6/Q7/Q8/Q9/Q10 genuine owner choices, or is any
   "owner question" actually settled by code? Is any factual defect miscast as an owner choice?
7. Completeness-test answer (s2): is "no live path bypasses the seams / Telegram is the only
   outbound channel" TRUE? Search for a counterexample (other channels, other renderers, other
   persisted artifacts consumed by UI, preview/debug leakage to prod).

## Constraints
- No edits. Read-only. Cite file:line for every source claim. Distinguish traced from
  hypothesis. Do not require the packet to answer the owner questions.

## Return (end with exactly this)
EVENT: INITIAL PACKET REVIEW (REBUILD)
REVIEWER: gpt-5.6-sol (Codex), fresh-context independent, run-isolated (cbagent transient
  unit, read-only sandbox, exact-SHA verified)
EXACT REVIEWED SHA: <SHA>
DATE: 2026-09-12
VERDICT: CLEAN | CLEAN WITH NITS | REQUIRED CHANGES | DESIGN INCOMPLETE (boundary reset)
FINDINGS: numbered; each file:line or packet section, the issue, and whether it is a factual
  defect / completeness gap / boundary-reset class / owner choice. (empty only if truthfully none)
BOUNDARY-RESET TRIGGERED: YES (name the omitted class/bypass file:line) / NO
