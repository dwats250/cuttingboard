# CODEX EVENT 2 -- EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 s2/s6/s7)

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION
REVIEWER: Codex, resolved model gpt-5.6-sol (codex exec banner in the job stderr.log;
self-report below says "GPT-5"), reasoning effort high.
CAPABILITY ROLE: GOV-2 independent material-packet reviewer, AUTHORITY: REVIEW
(owner-commissioned 2026-09-22, ruling R4).
EXACT CONFIRMED SHA: 3224360a396f755c8d5500b943f88edbdd715ead (packet rev 2).
PRIOR REVIEW: CODEX_EVENT_1_REVIEW_2026-09-22.md @ bcb859bd (F1-F7).
DATE: 2026-09-22 (run 23:32:47Z-23:42:53Z UTC).
VERDICT: DESIGN INCOMPLETE (GOV-2 s6).

RUN-ISOLATION / INDEPENDENCE EVIDENCE: dispatched via ~/cuttingboard-agent-jobs/cbagent
as a systemd --user transient unit running a fresh `codex exec` (new session
01a0cb76-fc7e-7471-be0b-f3e09af95367, no resume), no shared context with the authoring
session, read-only sandbox, exact-SHA guard (launch refused unless HEAD == 3224360a).
cbagent job id: codex-20260922T233247Z-8b16. Prompt: CODEX_CONFIRMATION_PROMPT_2026-09-22.md (this directory;
held uncommitted until after the run so the confirmed head is the corrected packet exactly).
MEMORY PROVENANCE: Codex memories feature enabled in CODEX_HOME; binary-inclusive search of
~/.codex/memories and memories_1.sqlite* for "prompt-surface", "PRD-347",
"compaction material" at record time: no match.

## Prior-finding confirmation summary
F1 PARTIALLY RESOLVED; F2 RESOLVED; F3 PARTIALLY RESOLVED; F4 RESOLVED; F5 RESOLVED;
F6 RESOLVED; F7 RESOLVED. REMAINING OMISSION / BOUNDARY-RESET: YES.

## Dispositions (GOV-2 s7)
- New defect 1 (BOUNDARY-RESET: live settings/hook/bootstrap control-surface class and
  .claude/settings.local.json unclassified by the s2A refresh): BLOCKED/PARKED. This is the
  second omitted-class discovery; per GOV-2 s6 incremental patching stops and Dustin
  chooses rebuild-from-fresh-frame, narrow-the-claim, or park.
- New defect 2 (A7 LANE locations), 3 (A2 README cite), 4 (A19 vs 9.3 hash contract):
  BLOCKED/PARKED with the packet. Defects 2-3 are local citation corrections GOV-2 s6
  would permit inside a bounded cycle; defect 4 is a contract defect. None is applied
  while the packet is DESIGN INCOMPLETE.
- The packet is NOT review-clean. No design-direction ruling, Stage-0 PRD-347, or other
  downstream authority may proceed from it.

## Verbatim reviewer output

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION
REVIEWER: GPT-5 (Codex), fresh-context independent
EXACT CONFIRMED SHA: 3224360a396f755c8d5500b943f88edbdd715ead (MATCH; no mismatch)
DATE: 2026-09-22

PRIOR FINDINGS:

F1 -> PARTIALLY RESOLVED
The original omission, docs/dev_workflow.md, is now explicitly classified OUT at audits/prompt-surface-compaction-material-packet-2026-09/PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md:76, and the stated Markdown command reproduces 59 files and the stated excluded-group counts at :88-90. However, the resulting claim that every live instruction surface is classified at :91-107 is false. See REMAINING OMISSION / BOUNDARY-RESET below.

F2 -> RESOLVED
The previously omitted dependencies are now represented in A2, A5, A13-A16 and the debt record: packet:139, :142, :150-153, :267-283. Independent source checks resolve at .claude/settings.local.json:173, scripts/pre_commit_sanity.sh:23-32, scripts/prd_close.sh:337-338, tests/test_prd_eval_hook.py:53-61 and :143-156, docs/plans/decision-support-expansion-doctrine-v0.1.md:132 and :437-439, docs/plans/decision-support-workplan-v0.1.md:75-77 and :93, docs/plans/agent-work-charge-template-v0.1.md:175 and :203-206, docs/contract/MODE_DESIGN.md:3-4 and the equivalent four mode files, docs/DECISIONS.md:792-797 and :2853-2856, and docs/PROJECT_STATE.md:37-38.

F3 -> PARTIALLY RESOLVED
B1 correctly separates the external waiver literal at docs/PRD_PROCESS.md:285-286 from payload references; A10 correctly confines "**Last updated:**" to scripts/prd_close.sh:209-213; B3 adds "Review Dispatch" and withdraws the OWNER_MERGE section claim; A17 gives the correct V1-V10, V1-V12, V1-V13 and V1-V9 ranges. Evidence: packet:147, :154, :163-165; .claude/skills/prd-authoring-verified/SKILL.md:106-115; .claude/skills/prd-closeout-verified/SKILL.md:162-173; .claude/skills/prd-review-claude/SKILL.md:210-222; .claude/skills/scope-lock-precommit/SKILL.md:198-206. A7 is still incomplete as described in NEW DEFECT 2.

F4 -> RESOLVED
The packet now preserves docs/CLAUDE_HOOKS.md:48-53 and .claude/skills/prd-authoring-verified/SKILL.md:143-161 at packet:63-64 and :155-157. P2 uses the historical-only ranges, and P3 requires proof against invoking agents, cross-references, refusals, fallback chains, reports and V-rows at packet:227-235.

F5 -> RESOLVED
The prior proof gaps are corrected at packet:193-218 and :241-250: structural and operator-less rule units are inventoried, force and scope must both remain equal, same-trigger load paths must be demonstrated, and defaults, exceptions, quantifiers and ordering are protected. Step 9.3 replaces occurrence counts with content-anchor extraction and sha256 comparison at packet:316-323. See NEW DEFECT 4 for a contradiction introduced by the corrected hash requirement.

F6 -> RESOLVED
A3 now identifies the harness loader as decisive, classifies a CLAUDE.md move as SILENT, and records that the constructed-path test remains green: packet:140; .claude/hooks/canonical_read_guard.sh:24-33; tests/test_canonical_read_guard_hook.py:46-49. A7 now separates validator-loud unknown CLASS and GOVERNANCE lane cases from silent/process-only cases: packet:144; tools/validate_prd_registry.py:788-795 and :817-839.

F7 -> RESOLVED
Q3 and Q6 are explicitly contract-changing alternatives requiring a revised packet and renewed review at packet:338-347. Astra is confined to the R4 PRD-review seat at :9-13 and :325-327. Ledger review remains proposed and uncommissioned at :214-220 and :348-350, while the implementation review requires a separately commissioned fresh-context reviewer at :328-331.

REMAINING OMISSION / BOUNDARY-RESET: YES
Section 2A claims that its 59 Markdown files plus named extras exhaust the live instruction surface and that nothing remains unclassified at packet:88-107. That method misses a live non-Markdown control-surface class:

- .claude/settings.json:160-213 wires three tracked hook scripts and scripts/dev_bootstrap.sh into PreToolUse, UserPromptSubmit and SessionStart.
- .claude/hooks/canonical_read_guard.sh:48-55 injects model-visible additionalContext.
- .claude/hooks/prd_eval.sh:102-106 injects model-visible additionalContext.
- .claude/hooks/protect_files.sh:38-39 blocks tool use with an operative instruction.
- CLAUDE.md:95-97 declares the effective permission surface to be the union of .claude/settings.json and the ignored-but-live .claude/settings.local.json. The latter contains active permission/dispatch entries, including Skill(prd-authoring-verified) at .claude/settings.local.json:173, but section 2A never classifies the file.
- The section also incorrectly calls .github/campaign/charge_prompt.md a non-Markdown carrier at packet:91-93 even though that file is already one of the 59 Markdown results.

This is a further omitted live instruction/control-surface class after the permitted refresh, so GOV-2 s6 returns the packet to DESIGN INCOMPLETE.

NEW DEFECTS FROM THE CORRECTION:

1. CLASS: BOUNDARY-RESET
   The complete inventory introduced by rev 2 omits the live settings/hook/bootstrap control-surface class. Evidence: packet:88-107; .claude/settings.json:160-213; .claude/hooks/canonical_read_guard.sh:48-55; .claude/hooks/prd_eval.sh:102-106; .claude/hooks/protect_files.sh:38-39; CLAUDE.md:95-97.

2. CLASS: FACTUAL
   A7 does not list all payload locations for the LANE literals it claims to inventory. It omits the combined LANE form at .claude/skills/prd-authoring-verified/SKILL.md:95 and an additional exact `LANE: HIGH-RISK` occurrence at .claude/skills/scope-lock-precommit/SKILL.md:167. Evidence: packet:144.

3. CLASS: FACTUAL
   A2 cites README.md:140-141 as a consumer of the four skill directory names and SKILL.md filename. Those lines name CLAUDE.md, AGENTS.md and docs/contract/, not any payload skill. Evidence: packet:139; README.md:139-142.

4. CLASS: CONTRACT
   The corrected frozen-item proof is internally contradictory. Section 2 proposes compacting CLAUDE.md text inside lines 83-144, including the rationale pointer at CLAUDE.md:85 and the topic list at :131-132 (packet:62). A19 then names essentially every CLAUDE.md section from :19-184 as a frozen range (packet:156), while step 9.3 requires each 4A named range to produce an equal pre/post sha256 (packet:316-321). As written, that check forbids the proposed removals inside A19's ranges; the packet must distinguish extracted rule units from whole named ranges before the proof is executable.

VERDICT: DESIGN INCOMPLETE (GOV-2 s6)