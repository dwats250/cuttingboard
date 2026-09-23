# CODEX CYCLE 2 EVENT 4 -- EXACT-CORRECTED-HEAD CONFIRMATION (FINAL HELM PROPAGATION)

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 cycle 2, final Helm-authorized propagation of
the C2-F3 exception; not a new correction cycle)
REVIEWER: Codex, resolved model gpt-5.6-sol (codex exec banner in the job stderr.log;
self-report below says "GPT-5"), reasoning effort low (unmodified runner, config default).
CAPABILITY ROLE: GOV-2 independent material-packet reviewer, AUTHORITY: REVIEW
(owner-commissioned 2026-09-22, ruling R4).
EXACT CONFIRMED SHA: e79468a58f4a7920103711d3ccdeb1de2dc171e5.
AUTHORITY FOR THE CHANGE: Helm ruling 2026-09-23 "FINAL MICRO-CORRECTION": exactly two edits
propagating the already-approved RULE_LEDGER_PRD-347.md exception to the s2 Q4 ceiling form
and the s6 forbidden transform; owner accepted the completed semantic sweep reported at
d9282cf7; final stop rule: any further substantive defect parks PRD-347.
PRIOR RECORD: CODEX_C2_EVENT_3_MICRO_CONFIRMATION_2026-09-23.md @ 5f66a841 (NOT CONFIRMED).
DATE: 2026-09-23 UTC (run 04:31:27Z-04:33:23Z).
VERDICT: CONFIRMED-CLEAN.

RUN-ISOLATION / INDEPENDENCE EVIDENCE: cbagent systemd --user transient unit, fresh
`codex exec` session 01a0cc88-6dc3-7e91-ae2c-a5065d59e407 (no resume), no shared context
with the authoring session, read-only sandbox, exact-SHA guard (launch refused unless
HEAD == e79468a5). cbagent job id: codex-20260923T043127Z-9f9d. Prompt:
CODEX_C2_FINAL_CONFIRMATION_PROMPT_2026-09-23.md (this directory; held uncommitted until
after the run so the confirmed head is exactly e79468a5).
MEMORY PROVENANCE: Codex memories feature enabled in CODEX_HOME; binary-inclusive search of
~/.codex/memories and ~/.codex/memories_1.sqlite for "prompt-surface", "PRD-347",
"compaction material" at record time: no match.

## Finding dispositions confirmed at this head
- Cycle 2: C2-F1 RESOLVED (confirmed at a387d590; no regression here); C2-F2 RESOLVED
  (confirmed at a387d590; no regression here); C2-F3 RESOLVED (this event, items 1-3, 6);
  EVENT 2 directory-count nit RESOLVED (47; confirmed at 5f66a841 and again here, item 4);
  EVENT 3 incomplete-propagation defect RESOLVED (items 1, 6).
- Cycle 1 (F1-F7, DESIGN INCOMPLETE at 3224360a) was superseded by owner ruling R7's
  narrowed claim and the new cycle 2; it is history, not re-confirmed here.
- Packet status at e79468a5: review-clean under GOV-2 cycle 2 per this record. The next step
  is owner adjudication (design-direction ruling). No Stage-0 PRD-347, Gate A, or
  implementation is authorized by this record.

## Verbatim reviewer output

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 cycle 2, final Helm propagation)
REVIEWER: GPT-5 (Codex), fresh-context independent
EXACT CONFIRMED SHA: e79468a58f4a7920103711d3ccdeb1de2dc171e5
DATE: 2026-09-23 UTC

SCOPE ITEM 1: PASS
C2-F3 is internally consistent across the entire packet. The general evidence-file prohibition expressly permits the sole new ledger (PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md:100-107); the Q4 ceiling permits the ledger and Stage-0 bookkeeping (lines 131-137); the ledger is explicitly evidence, not payload (lines 397-407); the forbidden-transform rule contains the same two exceptions and protects every other non-payload file (lines 428-443); and the verification plan names the same permitted diff (lines 511-538). No remaining contradiction, missing exception, or conflicting wording found.

SCOPE ITEM 2: PASS
RULE_LEDGER_PRD-347.md is consistently identified as the only authorized new non-payload evidence file (PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md:104-106, 133-134, 397-405, 438-442, 516-523).

SCOPE ITEM 3: PASS
Stage-0 bookkeeping is the only other permitted non-payload diff. It is consistently limited to docs/prd_history/PRD-347.md, docs/PRD_REGISTRY.md, docs/PROJECT_STATE.md, and docs/prd_index.json (PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md:242-244, 516-520). The forbidden-transform rule incorporates that definition by reference to s9.2 (lines 438-442). No broader bookkeeping exception was found.

SCOPE ITEM 4: PASS
The packet defines the audits/ measure as 206 tracked Markdown files in 47 directories (PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md:178). Reproduced at exact HEAD with:
git ls-files 'audits/*.md' | xargs -n1 dirname | sort -u | wc -l
Result: 47.

SCOPE ITEM 5: PASS
No C2-F1 or C2-F2 regression. C2-F1's complete no-prefilter Markdown inventory remains intact (PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md:139-206). C2-F2's per-occurrence identity and one-to-one verification contract remains intact (lines 255-265, 524-538). The exact e79468a5 commit changes neither area; it changes only the two C2-F3 prohibition passages at lines 133-134 and 438-442.

SCOPE ITEM 6: PASS
The two edits implement exactly the Helm-ruling scope and introduce no contradiction. The Q4 blanket prohibition now contains the ledger and Stage-0 exceptions (PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md:131-135). The forbidden-transform passage now contains the same two exceptions while continuing to prohibit modification, deletion, relocation, or rewriting of every other non-payload file (lines 428-443). The e79468a5 commit modifies only this packet and only those two passages.

NEW DEFECTS: none

VERDICT: CONFIRMED-CLEAN
