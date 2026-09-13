GOV-2 INITIAL PACKET REVIEW -- PRD-339 Effective-Permission MATERIAL Packet (gpt-5.6-sol)

You are the INDEPENDENT Codex reviewer for a GOV-2 MATERIAL packet. Fresh context,
read-only, no edits, no implementation. Your job is to try to FALSIFY the packet's
completeness -- not to approve it. GOV-2's governing principle: no agent certifies the
completeness of the boundary it chose; you are that independent check.

## Base
- Repo is checked out at the exact provisional packet commit. Confirm HEAD (git rev-parse
  HEAD) and report the SHA you reviewed; if the working tree does not match the SHA you were
  told, report the mismatch.
- Packet under review: audits/prd-339-effective-permission-material-packet-2026-09/
  PRD_339_EFFECTIVE_PERMISSION_MATERIAL_PACKET_2026-09-12.md (read in full).
- You MAY and SHOULD read the underlying repository surface to test the packet's claims:
  cuttingboard/runtime/__init__.py, cuttingboard/delivery/dashboard_renderer.py,
  cuttingboard/notifications/formatter.py, ui/app.js, tools/ci_push_artifacts.sh,
  tools/ci_restore_publish_state.sh, .github/workflows/cuttingboard.yml,
  .github/workflows/hourly_alert.yml, cuttingboard/contract_types.py, cuttingboard/config.py.
- The out-of-repo research dossier (read-only) is at
  /home/dustin/cuttingboard-ultra-permission/ULTRA_REVIEW/ if you want to check a synthesis
  claim against its source.

## This is a PACKET review, not a design/PRD review
Review the UPSTREAM MATERIAL packet: its problem statement, empirical reproductions,
producer-to-consumer authority map, carrier-insufficiency argument, the dedicated-carrier
evidence, the code-vs-owner boundary, the estimated surface, and the owner questions. The
PRD-339 design itself is provisional and is NOT the object of this review.

## Attack these specifically (falsify, don't confirm)
1. COMPLETENESS of the consumer/permission-surface enumeration (s3, s4, s7). Name any
   permission-asserting consumer, renderer, output, or schema reader the packet OMITS. If
   you find a previously-omitted consumer CLASS or end-to-end seam, say so explicitly and
   flag it as a GOV-2 s6 BOUNDARY-RESET candidate (not a local wording fix).
2. CARRIER / SEAM selection (s6 packet). Is the "reuse cannot satisfy the invariant"
   argument sound against the actual restore lists (cuttingboard.yml restore step;
   hourly_alert.yml restore/revert; ci_restore_publish_state.sh)? Is a dedicated carrier the
   right seam, or is there a reuse path the packet missed?
3. REPRODUCTION claims (s3). Are F1-F9 dispositions accurate against source (line numbers,
   the publisher's lack of semantic comparison, the viewer inference, the placeholder, the
   same-second identity)? Flag any claim not supported by the cited source.
4. PUBLISHER admission (s4/s7). Does the packet correctly describe every publish route
   (bootstrap direct-push, changed-set overlay, retry, static-ui sync exclusions) and the
   both-lane state-file set (daily latest_* AND hourly latest_hourly_*)?
5. ESTIMATED FILES/LOC (s5/s9). Are they labeled as estimates, and are they plausibly
   complete (no obviously-missing production file given the boundary)?
6. OWNER vs FACTUAL. Does the packet correctly separate genuine owner design choices
   (Q1/Q3/Q4/Q6/Q7) from matters already determined by code? Flag any "owner question" that
   is actually settled by code, or any factual defect miscast as an owner choice.
7. CODE vs OWNER-OPERATIONAL boundary (s8). Is anything owner-operational (cron/Worker/
   credentials/variable) smuggled into code scope, or any code obligation misclassified as
   owner containment?

## Constraints
- No edits. Read-only. Cite file:line for every source claim.
- Distinguish traced-in-source from hypothesis.
- Do not require the packet to answer the owner questions; it must NOT presume them.
- Do not treat the prior Astra ACCEPT / Sol CLEAN design consultation as satisfying this
  packet review (the packet says so explicitly; confirm that framing is honest).

## Return (end with exactly this)
EVENT: INITIAL PACKET REVIEW
REVIEWER: gpt-5.6-sol (Codex), fresh-context independent, run-isolated (cbagent transient
  unit, read-only sandbox, exact-SHA verified)
EXACT REVIEWED SHA: <the SHA you confirmed>
DATE: 2026-09-12
VERDICT: CLEAN | CLEAN WITH NITS | REQUIRED CHANGES | REJECT | DESIGN INCOMPLETE (boundary reset)
FINDINGS: numbered; each with file:line or packet section, the exact issue, and whether it
  is a factual defect, a completeness gap, a boundary-reset class, or an owner choice.
  (empty only if truthfully none)
BOUNDARY-RESET TRIGGERED: YES/NO (and which omitted class, if YES)
