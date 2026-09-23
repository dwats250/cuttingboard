CHARGE 2026-09-23 PRD-347 fresh-context independent PRD review (GOV-2 s2 step 7)
AUTHORITY: REVIEW (owner-commissioned 2026-09-22 ruling R4; seat confirmed by owner ruling Q7
2026-09-23). You are Astra, the fresh-context independent PRD reviewer. You are not the author
or the implementer. Read-only: no edits, no implementation, no merge, no Gate A. Your job is
to try to FALSIFY the PRD as a faithful, executable, non-weakening translation of the
review-clean packet and the owner's design-direction ruling, not to approve it.

## Base
- Run `git rev-parse HEAD`; it must be f6bb1dd5ab1329fe88a3df2eabeeb1e50fca332e. Report the SHA.
- Primary artifact: docs/prd_history/PRD-347.md (read in full).
- Review-clean packet (authority for the PRD): audits/prompt-surface-compaction-material-packet-
  2026-09/PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md, content head e79468a5
  (`git diff --quiet e79468a5 -- <packet>` should hold); its Codex confirmation record
  CODEX_C2_EVENT_4_FINAL_CONFIRMATION_2026-09-23.md. Read the packet in full.
- Owner design-direction ruling Q1-Q7: recorded in the PRD's BASIS section; treat it as given
  (do not relitigate the rulings), but flag any PRD text that misstates, widens, or narrows
  them.
- Canonical authority: docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md,
  docs/PRD_PROCESS.md (LANE Axis, CLASS Matrix, Scope Lock, Second-Model Disposition, Same-PR
  Closeout), docs/contract/MODE_IMPLEMENT.md, MODE_REVIEW.md, CLAUDE.md, AGENTS.md,
  tools/validate_prd_registry.py, and the 7 payload files themselves at HEAD.
- Ignore modified files under logs/ and ui/dashboard.html if present.

## Neutral review question
Is PRD-347 at f6bb1dd5 a faithful, complete, internally consistent and executable
implementation charter for the review-clean packet and the owner ruling, such that an
implementer following it cannot weaken the governing contract without a FAIL line firing?

## Attack these (owner Q7 focus plus translation fidelity)
1. SEMANTIC WEAKENING: can any requirement, ceiling, or permitted removal let a rule lose force
   or scope (MUST->should, dropped stop/refusal/fail-closed condition, narrowed quantifier,
   changed default or exception) without a FAIL line firing?
2. AUTHORITY DRIFT: does the PRD claim, widen, or narrow any authority (owner holds, merge wall,
   reviewer seats, commissions, Gate A, the ledger exception, Stage-0 bookkeeping, lifecycle
   review records) beyond the packet and rulings?
3. PARSER / INTERFACE LOSS: is every packet s4 frozen unit, s4C seed, and s2B external
   dependency carried into a binding requirement with an observable FAIL line?
4. FAIL-CLOSED REGRESSIONS: is every STOP/refusal condition of the packet preserved as a STOP
   in the PRD?
5. UNNECESSARY RETAINED RITUAL: does the PRD itself add ceremony or checks with no consumer or
   no failure they catch?
6. TRANSLATION FIDELITY: compare the PRD to packet s1-s9 and rulings Q1-Q7 item by item. In
   particular evaluate the two flagged AUTHOR INTERPRETATIONS in BASIS: (a) Q2 x Q1 (D-c
   excluded because Q1 forbids payload expansion); (b) Q2 x Q6 (D-a left unrepointed because it
   sits inside the frozen retired V10 marker). Are they correct readings, or does either
   conflict with a ruling? Also confirm or correct the D-d repoint target (packet s7 names
   docs/contract/MODE_REVIEW.md:21-26 as nearest, exact home UNKNOWN).
7. EXECUTABILITY: can every FAIL line and VALIDATION step be run as written at an
   implementation head? Are the ceilings (packet estimate + 10%, floor) computed correctly? Is
   the relationship between R1's implementation-head diff and the later lifecycle review
   records (PRD-347.review.astra.md, PRD-347.review.codex.md) and closeout bookkeeping
   consistent with PRD_PROCESS and with packet s9.2?
8. FACTUAL: every file:line, literal, SHA, and count in the PRD resolves at HEAD.

## Output (final message; ASCII only; this becomes the committed review record)
# PRD-347 Astra Review
REVIEWED STATE
Reviewed SHA: <git rev-parse HEAD>
Independence: fresh-context
VERDICT: ACCEPT | ACCEPT WITH CHANGES | REJECT
SUMMARY: <3-6 lines>
REQUIRED EDITS: numbered A-R1..A-Rn, each with evidence (file:line) and the smallest correction;
  `none` only if truthful
RECOMMENDED EDITS: numbered, or `none`
INTERPRETATIONS: (a) and (b) each AGREE | DISAGREE with reasoning; D-d target: <confirmed path
  or UNKNOWN with reason>
RATIONALE: one line per attack area 1-8 with the decisive check you ran
