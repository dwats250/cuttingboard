GOV-2 EXACT-CORRECTED-HEAD CONFIRMATION -- Prompt-Surface Compaction MATERIAL Packet (Codex)

AUTHORITY: REVIEW (owner-commissioned 2026-09-22, ruling R4). You are the INDEPENDENT Codex
reviewer performing the GOV-2 s2 step-5 EXACT-CORRECTED-HEAD CONFIRMATION. Fresh context,
read-only, no edits, no implementation, no merge.

## Base
- Corrected head to confirm: 3224360a396f755c8d5500b943f88edbdd715ead (packet rev 2).
  Run `git rev-parse HEAD`; it must equal that SHA. Report the SHA you confirmed and any
  mismatch. (The launcher also refuses to start unless HEAD equals it.)
- Initial review: bcb859bd5148d92b9e6707981ca094dbc5053965 (rev 1), verdict CHANGES
  REQUIRED, findings F1-F7. The record with your verbatim prior findings and the author's
  dispositions is audits/prompt-surface-compaction-material-packet-2026-09/
  CODEX_EVENT_1_REVIEW_2026-09-22.md. Read it in full.
- Corrected packet: audits/prompt-surface-compaction-material-packet-2026-09/
  PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md. Read it in full.
- `git diff bcb859bd..3224360a` shows exactly what changed.
- Ignore modified files under logs/ and ui/dashboard.html if present (disposable local
  output, outside the packet).

## Scope (GOV-2 s2)
This is confirmation that the prior findings F1-F7 are resolved at this exact head, NOT a
new broad review. For each of F1..F7: verify the correction against the repository at HEAD
(re-run the searches needed; do not trust the disposition text) and state RESOLVED,
PARTIALLY RESOLVED, or NOT RESOLVED with evidence (file:line).

Two mandatory checks remain in scope because GOV-2 s6/s7 make them decisive:
1. F1 was the first omitted-class discovery; packet s2A is the one permitted complete
   instruction-surface inventory refresh. Re-run its stated method (and any reasonable
   variant needed to test it) and report whether ANY live agent-facing instruction/control
   surface remains unclassified or misclassified. If one does, say so explicitly as
   REMAINING OMISSION / BOUNDARY-RESET: YES, with evidence; GOV-2 then returns the packet to
   DESIGN INCOMPLETE and the correction cycle stops.
2. Any NEW defect introduced by the correction itself (a rev-2 citation that does not
   resolve, a new internal contradiction, or text that widens/narrows owner rulings R1-R6
   or claims authority the packet lacks).

## Output (your final message; ASCII only)
EVENT: EXACT-CORRECTED-HEAD CONFIRMATION
REVIEWER: <model id> (Codex), fresh-context independent
EXACT CONFIRMED SHA: <git rev-parse HEAD>
DATE: <UTC date>
PRIOR FINDINGS: F1..F7 each -> RESOLVED | PARTIALLY RESOLVED | NOT RESOLVED, with evidence
REMAINING OMISSION / BOUNDARY-RESET: YES | NO, with evidence
NEW DEFECTS FROM THE CORRECTION: numbered list with CLASS and evidence, or `none`
VERDICT: one of CONFIRMED-CLEAN | CONFIRMED-CLEAN WITH NITS | NOT CONFIRMED |
  DESIGN INCOMPLETE (GOV-2 s6)
