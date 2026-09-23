# CODEX CYCLE 2 EVENT 2 -- EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 s2/s6/s7)

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 cycle 2)
REVIEWER: Codex, resolved model gpt-5.6-sol (codex exec banner in the job stderr.log;
self-report below says "GPT-5"), reasoning effort low (unmodified runner, config default).
CAPABILITY ROLE: GOV-2 independent material-packet reviewer, AUTHORITY: REVIEW
(owner-commissioned 2026-09-22, ruling R4).
EXACT CONFIRMED SHA: a387d59088eec307cee5e754a95e05c27684bb2a (packet rev 4).
PRIOR REVIEW: CODEX_C2_EVENT_1_REVIEW_2026-09-22.md @ 394006f0 (C2-F1..C2-F3).
DATE: 2026-09-23 UTC (run 00:15:59Z-00:21:39Z).
VERDICT: NOT CONFIRMED.

RUN-ISOLATION / INDEPENDENCE EVIDENCE: cbagent systemd --user transient unit, fresh
`codex exec` session 01a0cb9e-8ac8-7db3-a29c-7b9154ca371b (no resume), no shared context
with the authoring session, read-only sandbox, exact-SHA guard (launch refused unless
HEAD == a387d590). cbagent job id: codex-20260923T001559Z-d152. Prompt:
CODEX_C2_CONFIRMATION_PROMPT_2026-09-22.md (this directory; held uncommitted until after
the run so the confirmed head is rev 4 exactly).
MEMORY PROVENANCE: Codex memories feature enabled in CODEX_HOME; binary-inclusive search of
~/.codex/memories and ~/.codex/memories_1.sqlite for "prompt-surface", "PRD-347",
"compaction material" at record time: no match (no memories_1.sqlite-wal file present).

## Confirmation summary
C2-F1 RESOLVED; C2-F2 RESOLVED; C2-F3 NOT RESOLVED. REMAINING OMISSION / BOUNDARY-RESET: NO
(the R7 narrowed Markdown inventory reconciles; GOV-2 s6 DESIGN INCOMPLETE not triggered).

## Dispositions (GOV-2 s7)
- C2-F3 / new defect 1 (CONTRACT: the proof-carrier ledger RULE_LEDGER_PRD-347.md under
  audits/ contradicts the packet's own no-audits-edit non-goal and forbidden transform):
  BLOCKED/PARKED. Cycle 2's one consolidated correction is spent; resolving it needs an
  owner decision (Dustin resumes, narrows, or retires the packet). Not applied.
- New defect 2 (FACTUAL: "206 files in 53 directories"; tracked Markdown occupies 47
  distinct directory paths): BLOCKED/PARKED with the packet (local count correction; no
  hidden omission, the 206/894 arithmetic reconciles). Not applied.
- The packet is NOT review-clean. No design-direction ruling, Stage-0 PRD-347, or other
  downstream authority may proceed from it.

## Verbatim reviewer output

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 cycle 2)

REVIEWER: GPT-5 (Codex), fresh-context independent

EXACT CONFIRMED SHA: a387d59088eec307cee5e754a95e05c27684bb2a

DATE: 2026-09-23 UTC

PRIOR FINDINGS:

C2-F1 -> RESOLVED

Evidence:

- Re-ran the no-prefilter inventory at exact HEAD. `git ls-files '*.md' | wc -l` returns 894.
- Reproduced the complete group arithmetic: REST 59 + docs/prd_history 627 + audits 206 + docs/session_resume 1 + docs/superpowers 1 + reports 0 + logs 0 = 894.
- Reproduced the G1 subtotal and inspected all 59 paths.
- Reproduced the docs/prd_history filename breakdown: 335 PRD docs + 246 review sidecars + 4 proposal files + 2 codex_prompt files + 1 impl_notes file + 1 adjudication file + 38 other files = 627.
- Reproduced the audits sweeps: name sweep 28, content sweep 26, union 37.
- Verified the packet directory contains the stated seven tracked Markdown files at HEAD. The three prior prompts are now evidence; the cycle-2 EVENT 2 prompt is not tracked at this SHA.
- Verified `audits/EXECUTION_DOCTRINE.md` is LIVE under the stated test through `.claude/skills/prd-review-claude/SKILL.md:154` and `:189`, is classified OUT under R3, and its two payload references are frozen as B7.
- Rechecked the named untracked and user-level surfaces: both ignored root files and their byte counts, four stale worktree CLAUDE.md copies, empty `/home/dustin/.codex/AGENTS.md`, 72 Claude memory Markdown files, and absence of `/home/dustin/.claude/CLAUDE.md`.
- No LIVE agent-facing Markdown instruction/control file remains unclassified or misclassified under the packet's operational LIVE test.

C2-F2 -> RESOLVED

Evidence:

- Packet lines 252-263 now require a stable ID for every class-H occurrence, exact bytes, file identity, heading/list/table/fence structural context, pre-edit location, and per-file cardinality.
- Packet lines 517-531 require identical PRE/POST ID sets, hashes, structural roles, and cardinalities. The former "at least once" survival test is removed.
- Packet lines 425-436 expressly forbid deleting one class-H occurrence merely because another identical occurrence survives.
- Independently reproduced every explicit 4C seed cardinality, including the previously line-count-sensitive values: `Auto-Approval Policy` in SL = 4 occurrences and `.review.claude.md` in PR = 6 occurrences. All stated 4C seed counts matched HEAD.

C2-F3 -> NOT RESOLVED

Evidence:

- Packet lines 394-404 now name a concrete proof carrier: `audits/prompt-surface-compaction-material-packet-2026-09/RULE_LEDGER_PRD-347.md`, containing the embedded `python h_manifest` checker.
- However, that carrier remains inconsistent with the packet's own boundary:
  - Lines 100-105 declare "no edit to any audits/, review, prompt, or evidence Markdown."
  - Lines 394-402 require committing a new evidence Markdown file under `audits/`.
  - Lines 425-436 make editing any file outside the payload, specifically including `audits/` patches, a forbidden transform and STOP.
  - Lines 509-516 then expressly allow the ledger change under `audits/`.
- The correction therefore identifies an executable carrier but does not provide one that is consistent with its own seven-file payload, non-goals, and forbidden-transform contract. This is the same unresolved carrier/boundary defect identified by C2-F3.

REMAINING OMISSION / BOUNDARY-RESET: NO

Evidence:

The complete no-prefilter Markdown inventory totals 894 and reconciles exactly across all groups. The REST list, docs/prd_history breakdown, audits prompt/charge sweeps, singleton groups, ignored root Markdown, worktree copies, and user-level Markdown were independently rechecked. No additional LIVE Markdown class or unclassified LIVE file was found. The C2-F3 boundary contradiction is a contract defect, not an omitted Markdown class, so GOV-2 s6 DESIGN INCOMPLETE is not triggered.

NEW DEFECTS FROM THE CORRECTION:

1. CLASS: CONTRACT

   Evidence: Rev 4 introduces the audits-local ledger as the required proof carrier at packet lines 394-402 and 509-531, while lines 100-105 and 425-436 prohibit that exact audits/outside-payload change. This newly added internal contradiction overlaps and prevents resolution of C2-F3.

2. CLASS: FACTUAL

   Evidence: Packet line 175 says `audits/` contains "206 files in 53 directories." The 206-file count is correct, but the tracked Markdown paths occupy 47 distinct directory paths including `audits/` itself. The current filesystem contains 49 directories under `audits/`. Neither reproducible interpretation yields 53. This count defect does not hide an omitted Markdown file because the 206-file total, both audits sweeps, their 37-file union, and the overall 894-file arithmetic all reconcile.

VERDICT: NOT CONFIRMED
