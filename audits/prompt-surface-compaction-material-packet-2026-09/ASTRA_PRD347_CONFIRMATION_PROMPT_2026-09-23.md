CHARGE 2026-09-23 PRD-347 exact-corrected-head confirmation (fresh-context PRD reviewer)
AUTHORITY: REVIEW (owner ruling R4; seat confirmed by owner ruling Q7). You are Astra in a
fresh context. Read-only: no edits, no implementation, no merge, no Gate A.

## Base
- Run `git rev-parse HEAD`; it must be 8b8ebe94218e000e690e43851a8e084a62ff9517. Report it.
- Prior review: docs/prd_history/PRD-347.review.astra.md (REJECT at f6bb1dd5; required edits
  A-R1..A-R9 and one recommended edit; author dispositions appended at its end). Read in full.
- Corrected PRD: docs/prd_history/PRD-347.md (read in full). `git diff f6bb1dd5..8b8ebe94`
  shows the complete correction.
- Authority as before: the packet at content head e79468a5
  (audits/prompt-surface-compaction-material-packet-2026-09/), owner rulings R1-R7 and Q1-Q7
  (Q1-Q7 summarized in the PRD BASIS), docs/PRD_PROCESS.md, GOV-2, MODE_IMPLEMENT/MODE_REVIEW,
  tools/validate_prd_registry.py, .claude/skills/scope-lock-precommit/SKILL.md.
- Ignore modified files under logs/ and ui/dashboard.html if present.

## Scope (confirmation, not a new broad review)
1. For each of A-R1..A-R9 and the recommended edit: RESOLVED | PARTIALLY RESOLVED | NOT
   RESOLVED, verified against the repository at HEAD (re-run checks; do not trust the
   dispositions), with evidence.
2. GATE A ITEM G1: the PRD surfaces the missing carrier for the Q7 implementation-review record
   as an owner decision and STOPs without approval. Confirm it is surfaced correctly and that no
   other part of the PRD silently assumes the answer. (Do not decide G1; it is Dustin's.)
3. Any NEW defect introduced by the correction (a citation, count, stage definition, FAIL line,
   or annotation that does not resolve or contradicts the packet, the rulings, or the validator),
   and whether the corrected PRD is under 100 lines and passes
   `python tools/validate_prd_registry.py --skip-commit-resolvability`.

## Output (final message; ASCII only)
# PRD-347 Astra Confirmation
REVIEWED STATE
Reviewed SHA: <git rev-parse HEAD>
Independence: fresh-context
PRIOR FINDINGS: A-R1..A-R9 and REC-1 each -> RESOLVED | PARTIALLY RESOLVED | NOT RESOLVED, with evidence
G1: CORRECTLY SURFACED | NOT CORRECTLY SURFACED, with evidence
NEW DEFECTS: numbered with evidence, or `none`
VERDICT: CONFIRMED-CLEAN | CONFIRMED-CLEAN WITH NITS | NOT CONFIRMED
(Nits = non-substantive wording only; any contradiction, missing requirement, or authority
issue is NOT CONFIRMED.)
