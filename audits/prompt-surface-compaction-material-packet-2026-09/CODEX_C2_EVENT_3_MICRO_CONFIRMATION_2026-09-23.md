# CODEX CYCLE 2 EVENT 3 -- EXACT-CORRECTED-HEAD CONFIRMATION AFTER HELM MICRO-CORRECTION

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 cycle 2, Helm-authorized micro-correction;
not a new correction cycle)
REVIEWER: Codex, resolved model gpt-5.6-sol (codex exec banner in the job stderr.log;
self-report below says "GPT-5"), reasoning effort low (unmodified runner, config default).
CAPABILITY ROLE: GOV-2 independent material-packet reviewer, AUTHORITY: REVIEW
(owner-commissioned 2026-09-22, ruling R4).
EXACT CONFIRMED SHA: 5f66a841726ab32d5db151139563e7b98a9c23d5 (rev 4 + Helm micro-correction).
AUTHORITY FOR THE MICRO-CORRECTION: Helm ruling 2026-09-23 (Option 1): authorize exactly one
new non-payload evidence file RULE_LEDGER_PRD-347.md in this packet directory; replace the
contradictory no-audits-edit / forbidden-transform wording with the invariant "No
modification, deletion, relocation, or rewriting of any pre-existing audit, review, prompt,
or evidence file. The only authorized new non-payload evidence file is RULE_LEDGER_PRD-347.md
in this packet directory."; correct 53 -> 47; reopen nothing else; if any new substantive
defect remains, STOP and do not begin cycle 3.
PRIOR RECORD: CODEX_C2_EVENT_2_CONFIRMATION_2026-09-22.md @ a387d590 (NOT CONFIRMED).
DATE: 2026-09-23 UTC (run 04:07:30Z-04:09:54Z).
VERDICT: NOT CONFIRMED.

RUN-ISOLATION / INDEPENDENCE EVIDENCE: cbagent systemd --user transient unit, fresh
`codex exec` session 01a0cc72-83d2-7cf1-93db-aafbe5ac3f90 (no resume), no shared context
with the authoring session, read-only sandbox, exact-SHA guard (launch refused unless
HEAD == 5f66a841). cbagent job id: codex-20260923T040730Z-b6ce. Prompt:
CODEX_C2_MICRO_CONFIRMATION_PROMPT_2026-09-22.md (this directory; held uncommitted until
after the run).
MEMORY PROVENANCE: Codex memories feature enabled in CODEX_HOME; binary-inclusive search of
~/.codex/memories and ~/.codex/memories_1.sqlite for "prompt-surface", "PRD-347",
"compaction material" at record time: no match.

## Confirmation summary
C2-F3 NOT RESOLVED; DIRECTORY COUNT RESOLVED (47); C2-F1 / C2-F2 regression NONE.

## Dispositions (GOV-2 s7)
- C2-F3 / new defect 1 (CONTRACT: the micro-correction replaced the audits-specific wording
  at s1 and s6 but left two blanket prohibitions that still forbid the authorized ledger:
  packet line 133 "zero non-payload diff" (s2 Q4 ceiling form) and lines 437-440 "editing any
  file outside the payload" (s6 forbidden transforms)): BLOCKED/PARKED. Author-side cause:
  the orchestrator scoped the invariant replacement to passages naming audits/ and did not
  sweep for non-payload/outside-payload phrasing. Per the Helm ruling, STOP; no cycle 3; the
  owner decides. Not applied.
- The packet is NOT review-clean. No design-direction ruling, Stage-0 PRD-347, or other
  downstream authority may proceed from it.

## Verbatim reviewer output

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 cycle 2, Helm micro-correction)
REVIEWER: GPT-5 (Codex), fresh-context independent
EXACT CONFIRMED SHA: 5f66a841726ab32d5db151139563e7b98a9c23d5
DATE: 2026-09-23 UTC
C2-F3: NOT RESOLVED. The non-goal at lines 100-106 now states the ruled invariant and authorizes RULE_LEDGER_PRD-347.md as the sole new non-payload evidence file. Section 9.2 likewise includes that ledger in the permitted diff at lines 513-520. However, two unchanged blanket prohibitions still contradict it: line 133 requires "zero non-payload diff", and lines 437-440 continue to forbid "editing any file outside the payload" before separately allowing the ledger only as an exception to the pre-existing-evidence-file prohibition. Because the ledger is explicitly evidence, not payload (lines 396-404), creating it necessarily produces a non-payload diff and edits outside the payload.
DIRECTORY COUNT: RESOLVED. At exact HEAD, independently enumerating the parent directory of every path returned by `git ls-files 'audits/*.md'`, then sorting uniquely, returns 47 directory paths. The packet now says "47" at line 177.
C2-F1 / C2-F2 REGRESSION: NONE. Commit 5f66a841 changes only the packet, and its diff is limited to the two intended subject areas: audit/evidence boundary wording and 53-to-47. It does not touch the C2-F1 inventory construction or C2-F2 occurrence-ID and manifest requirements.
NEW DEFECTS FROM THE MICRO-CORRECTION:
1. CLASS: CONTRACT. The replacement is incomplete and therefore deviates from the ruled invariant: packet line 133 still requires "zero non-payload diff", while lines 437-440 retain the blanket ban on editing any file outside the payload. Both prohibit the expressly authorized new non-payload RULE_LEDGER_PRD-347.md. This overlaps the unresolved C2-F3 defect rather than reopening C2-F1 or C2-F2.
VERDICT: NOT CONFIRMED
