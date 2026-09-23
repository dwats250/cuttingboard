GOV-2 EXACT-CORRECTED-HEAD CONFIRMATION, CYCLE 2 HELM MICRO-CORRECTION -- Prompt-Surface Compaction MATERIAL Packet (Codex)

AUTHORITY: REVIEW (owner-commissioned 2026-09-22, ruling R4). You are the INDEPENDENT Codex
reviewer confirming an exact head after a Helm-authorized micro-correction. Fresh context,
read-only, no edits, no implementation, no merge.

## Base
- Head to confirm: 5f66a841726ab32d5db151139563e7b98a9c23d5. Run `git rev-parse HEAD`; it must
  equal that SHA. Report the SHA you confirmed.
- Prior confirmation: CODEX_C2_EVENT_2_CONFIRMATION_2026-09-22.md (this packet directory) at
  a387d590 (rev 4): NOT CONFIRMED. C2-F1 RESOLVED, C2-F2 RESOLVED, C2-F3 NOT RESOLVED
  (proof-carrier ledger under audits/ contradicted the packet's no-audits-edit wording), plus
  a factual nit ("206 files in 53 directories"; tracked Markdown occupies 47 directory paths).
  Read that record in full.
- Packet: audits/prompt-surface-compaction-material-packet-2026-09/
  PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md.
- `git diff a387d590..5f66a841` is the complete change set of the micro-correction (the
  intervening commit c32974a1 only adds the EVENT 2 record and its prompt).
- Ignore modified files under logs/ and ui/dashboard.html if present.

## Helm ruling (owner, 2026-09-23; the micro-correction's authority)
Option 1 authorized. Exactly two micro-corrections to rev 4:
1. Authorize exactly one new non-payload evidence file:
   audits/prompt-surface-compaction-material-packet-2026-09/RULE_LEDGER_PRD-347.md, and replace
   the contradictory "no audits edits" / forbidden-transform wording with the invariant: "No
   modification, deletion, relocation, or rewriting of any pre-existing audit, review, prompt,
   or evidence file. The only authorized new non-payload evidence file is
   RULE_LEDGER_PRD-347.md in this packet directory."
2. Correct the directory count from 53 to 47.
No other rev-4 text or claim is reopened. This is not a new correction cycle.

## Scope (narrow)
1. C2-F3: is the proof-carrier/boundary contradiction now resolved? Check every packet
   passage governing audits/, evidence files, the ledger, the non-payload diff (s9.2), and
   forbidden transforms for consistency with the ruled invariant. RESOLVED | NOT RESOLVED.
2. The directory count: does "47" reproduce at HEAD? RESOLVED | NOT RESOLVED.
3. Does the micro-correction introduce any new contradiction, or deviate from the ruled
   wording or scope (any change beyond the two ruled edits)?
4. Regression only: confirm C2-F1 and C2-F2 remain resolved (the diff must not have touched
   them). Do not re-litigate them.

## Output (final message; ASCII only)
EVENT: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 cycle 2, Helm micro-correction)
REVIEWER: <model id> (Codex), fresh-context independent
EXACT CONFIRMED SHA: <git rev-parse HEAD>
DATE: <UTC date>
C2-F3: RESOLVED | NOT RESOLVED, with evidence
DIRECTORY COUNT: RESOLVED | NOT RESOLVED, with evidence
C2-F1 / C2-F2 REGRESSION: NONE | describe
NEW DEFECTS FROM THE MICRO-CORRECTION: numbered with CLASS and evidence, or `none`
VERDICT: CONFIRMED-CLEAN | CONFIRMED-CLEAN WITH NITS | NOT CONFIRMED
