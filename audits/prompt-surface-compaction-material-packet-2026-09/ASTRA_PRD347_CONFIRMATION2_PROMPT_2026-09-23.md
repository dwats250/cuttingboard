CHARGE 2026-09-23 PRD-347 exact-head confirmation after owner-authorized micro-correction
AUTHORITY: REVIEW (owner ruling R4; Q7). You are Astra in a fresh context. Read-only: no edits,
no implementation, no merge, no Gate A.

## Base
- Run `git rev-parse HEAD`; it must be 188ae139b6e8594def8f13b5d7c0e8cb06dfcf19. Report it.
- Prior records: docs/prd_history/PRD-347.review.astra.md (REJECT @ f6bb1dd5) and
  docs/prd_history/PRD-347.confirmation1.astra.md (NOT CONFIRMED @ 8b8ebe94: NEW DEFECT 1
  circular evidence / R12 temporal overclaim; A-R2, A-R5, REC-1 partial). Read both in full.
- Corrected PRD: docs/prd_history/PRD-347.md. `git diff 8b8ebe94..188ae139` is the complete
  change (commit 419a1269 in between only adds the confirmation1 record and prompts; this
  commit also adds one registry row for that record).
- Authority: packet at content head e79468a5 (audits/prompt-surface-compaction-material-packet-
  2026-09/, incl. s9.3 checker design), owner rulings R1-R7, Q1-Q7, and the owner ruling below,
  docs/PRD_PROCESS.md, GOV-2, tools/validate_prd_registry.py, CLAUDE.md Precedence.
- Ignore modified files under logs/ and ui/dashboard.html if present.

## Owner ruling 2026-09-23 (authority for this micro-correction; not a second cycle)
1. Stage ordering: before commit I the Builder completes the payload, generates the POST
   manifest and X2 after-hash from the final worktree, finalizes the ledger, runs the checker,
   then commits I. Nothing stored in I may require I to exist; after I, payload and ledger are
   frozen.
2. R12: the review of I verifies R2-R11 and only the I-stage portion of R1; R/C checks are
   verified at C; stage boundaries stay explicit.
3. REC-1: state the exact runnable checker command; no checker redesign.
4. G1 approved: docs/prd_history/PRD-347.review.codex.md is a post-I stage-R review artifact,
   not payload and not present in I; the ledger remains the sole new non-payload evidence file
   inside I; every blanket prohibition must distinguish the I-stage boundary from this artifact.
5. No other design change (7-file payload, D-a/D-c/D-d, Ratification SHAs, ceilings, class-H
   freezes, packet semantics, Q1-Q7).

## Verify exactly
1. The POST manifest and X2 after-hash can truthfully be completed before I.
2. The ledger can therefore be frozen in I without circular evidence.
3. R12 assigns only I-stage obligations to the review of I.
4. R/C checks occur only when those stages exist.
5. The concrete checker command is runnable from the repo root and matches the packet s9.3
   designed proof (paths only differ).
6. docs/prd_history/PRD-347.review.codex.md is consistently authorized as a post-I stage-R
   artifact without widening the I-stage payload, and no remaining PRD vocabulary forbids it.
7. No previously resolved Astra finding (A-R1..A-R9 as resolved in confirmation1) regressed, and
   nothing beyond the owner-ruled scope changed (compare the diff). The PRD stays under 100
   lines and `python tools/validate_prd_registry.py --skip-commit-resolvability` passes.

## Output (final message; ASCII only)
# PRD-347 Astra Confirmation 2
REVIEWED STATE
Reviewed SHA: <git rev-parse HEAD>
Independence: fresh-context
ITEMS 1-7: each PASS | FAIL, with evidence (file:line)
NEW DEFECTS: numbered with evidence, or `none`
VERDICT: CONFIRMED-CLEAN | CONFIRMED-CLEAN WITH NITS | NOT CONFIRMED
(Nits = non-substantive wording only; any contradiction, missing requirement, or authority
issue is NOT CONFIRMED.)
