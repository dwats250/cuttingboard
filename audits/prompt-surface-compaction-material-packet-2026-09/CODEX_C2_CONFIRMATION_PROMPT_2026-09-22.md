GOV-2 EXACT-CORRECTED-HEAD CONFIRMATION, CYCLE 2 -- Prompt-Surface Compaction MATERIAL Packet (Codex)

AUTHORITY: REVIEW (owner-commissioned 2026-09-22, ruling R4). You are the INDEPENDENT Codex
reviewer performing the GOV-2 s2 step-5 EXACT-CORRECTED-HEAD CONFIRMATION for cycle 2 (the
new bounded cycle started after owner ruling R7 narrowed the governed claim). Fresh
context, read-only, no edits, no implementation, no merge.

## Base
- Corrected head to confirm: a387d59088eec307cee5e754a95e05c27684bb2a (packet rev 4).
  Run `git rev-parse HEAD`; it must equal that SHA. Report the SHA you confirmed.
- Cycle-2 initial review: 394006f0839ad27eab9f3b4f455670f58c689a96 (rev 3), verdict CHANGES
  REQUIRED, findings C2-F1..C2-F3. Record with the verbatim findings and the author's
  dispositions: audits/prompt-surface-compaction-material-packet-2026-09/
  CODEX_C2_EVENT_1_REVIEW_2026-09-22.md. Read it in full.
- Corrected packet: audits/prompt-surface-compaction-material-packet-2026-09/
  PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md. Read it in full.
- `git diff 394006f0..a387d590` shows exactly what changed.
- Ignore modified files under logs/ and ui/dashboard.html if present.

## The governed claim (R7, verbatim)
"Complete inventory and semantic-no-op compaction of Cuttingboard's LIVE agent-facing
Markdown instruction/control surface." Not a claim about non-Markdown surfaces beyond the
specifically discovered frozen dependencies (s2B).

## Scope (GOV-2 s2)
Confirm that C2-F1..C2-F3 are resolved at this exact head; this is NOT a new broad review.
For each: verify against the repository at HEAD (re-run the searches; do not trust the
disposition text) and state RESOLVED, PARTIALLY RESOLVED, or NOT RESOLVED with evidence.

Two mandatory checks remain in scope because GOV-2 s6/s7 make them decisive:
1. C2-F1 was the first omitted-class discovery of cycle 2; packet s2A is the one permitted
   complete Markdown inventory refresh. Re-run its method, verify its arithmetic, apply its
   LIVE test, and report whether ANY live agent-facing Markdown instruction/control file
   remains unclassified or misclassified. If one does: REMAINING OMISSION /
   BOUNDARY-RESET: YES, with evidence (GOV-2 then returns the packet to DESIGN INCOMPLETE).
   Do NOT count further non-Markdown surfaces as an omission (excluded by R7).
2. Any NEW defect introduced by the correction itself (a rev-4 citation or count that does
   not resolve, including the 4C seed counts, a new internal contradiction, or text that
   widens/narrows owner rulings R1-R7 or claims authority the packet lacks).

## Output (final message; ASCII only)
EVENT: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 cycle 2)
REVIEWER: <model id> (Codex), fresh-context independent
EXACT CONFIRMED SHA: <git rev-parse HEAD>
DATE: <UTC date>
PRIOR FINDINGS: C2-F1..C2-F3 each -> RESOLVED | PARTIALLY RESOLVED | NOT RESOLVED, with evidence
REMAINING OMISSION / BOUNDARY-RESET: YES | NO, with evidence
NEW DEFECTS FROM THE CORRECTION: numbered list with CLASS and evidence, or `none`
VERDICT: one of CONFIRMED-CLEAN | CONFIRMED-CLEAN WITH NITS | NOT CONFIRMED |
  DESIGN INCOMPLETE (GOV-2 s6)
