GOV-2 EXACT-CORRECTED-HEAD CONFIRMATION, FINAL HELM PROPAGATION -- Prompt-Surface Compaction MATERIAL Packet (Codex)

AUTHORITY: REVIEW (owner-commissioned 2026-09-22, ruling R4). You are the INDEPENDENT Codex
reviewer confirming one exact head. Fresh context, read-only, no edits, no implementation,
no merge.

## Base
- Head to confirm: e79468a58f4a7920103711d3ccdeb1de2dc171e5. Run `git rev-parse HEAD`; it must
  equal that SHA. Report the SHA you confirmed.
- Prior record: audits/prompt-surface-compaction-material-packet-2026-09/
  CODEX_C2_EVENT_3_MICRO_CONFIRMATION_2026-09-23.md at 5f66a841: NOT CONFIRMED because two
  blanket prohibitions still forbade the owner-authorized ledger (packet s2 Q4 "zero
  non-payload diff"; s6 "editing any file outside the payload"). Read it in full.
- Packet: audits/prompt-surface-compaction-material-packet-2026-09/
  PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md (read in full).
- `git diff 5f66a841..e79468a5` is the complete change (the intervening commit d9282cf7 only
  adds the EVENT 3 record and its prompt).
- Ignore modified files under logs/ and ui/dashboard.html if present.

## Helm ruling (owner, 2026-09-23; authority for this change; not a new cycle)
The prior owner-authorized exception for exactly one new non-payload evidence file,
audits/prompt-surface-compaction-material-packet-2026-09/RULE_LEDGER_PRD-347.md, was
incompletely propagated. Authorized: EXACTLY two edits.
1. s2 / Q4: "zero non-payload diff" -> "zero non-payload diff except RULE_LEDGER_PRD-347.md
   (the only authorized new non-payload evidence file) and Stage-0 bookkeeping".
2. s6 forbidden transform "editing any file outside the payload": add the same narrow
   exception - RULE_LEDGER_PRD-347.md is the only authorized new non-payload evidence file;
   normal Stage-0 bookkeeping remains permitted; no pre-existing audit, review, prompt,
   evidence, or other non-payload file may be modified, deleted, relocated, or rewritten.
No other substantive claim altered.

## Confirmation scope (exactly these)
1. C2-F3 is internally consistent across the ENTIRE packet: search every passage governing
   the payload boundary, non-payload files, audits/evidence files, the ledger, Stage-0
   bookkeeping, forbidden transforms, and the s9 verification plan. Any remaining
   contradiction, missing exception, or conflicting wording?
2. RULE_LEDGER_PRD-347.md is the sole new non-payload evidence file the packet permits.
3. Stage-0 bookkeeping is the only other permitted non-payload diff, and the packet's
   definition of it is consistent everywhere it appears.
4. The audits/ directory count remains 47 (reproduce at HEAD).
5. C2-F1 and C2-F2 show no regression (regression check only; do not re-litigate).
6. The two edits introduced no contradiction and changed nothing beyond the ruled scope.

## Output (final message; ASCII only)
EVENT: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 cycle 2, final Helm propagation)
REVIEWER: <model id> (Codex), fresh-context independent
EXACT CONFIRMED SHA: <git rev-parse HEAD>
DATE: <UTC date>
SCOPE ITEMS 1-6: each PASS | FAIL, with evidence (file:line)
NEW DEFECTS: numbered with CLASS and evidence, or `none`
VERDICT: CONFIRMED-CLEAN | CONFIRMED-CLEAN WITH NITS | NOT CONFIRMED
(Nits must be non-substantive wording only; anything that is a contradiction, missing
exception, or required contract change is NOT CONFIRMED.)
