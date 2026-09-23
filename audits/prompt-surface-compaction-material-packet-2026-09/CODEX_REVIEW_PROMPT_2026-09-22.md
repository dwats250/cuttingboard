GOV-2 INITIAL PACKET REVIEW -- Prompt-Surface Compaction MATERIAL Packet (Codex)

AUTHORITY: REVIEW (owner-commissioned 2026-09-22). You are the INDEPENDENT Codex reviewer
for a GOV-2 MATERIAL packet. Fresh context, read-only sandbox, no edits, no implementation,
no merge. Your job is to try to FALSIFY the packet -- its boundary, its frozen interface
set, and its preservation contract -- not to approve it. GOV-2's governing principle: no
agent certifies the completeness of the boundary it chose; you are that independent check.
Your commission explicitly includes the mechanical parser / consumer / dependency audit.

## Base
- Repo is at the exact provisional packet commit. Run `git rev-parse HEAD` and report the
  SHA you reviewed; report any mismatch with the SHA in your launch metadata.
- Packet under review (read in full):
  audits/prompt-surface-compaction-material-packet-2026-09/
  PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md
- Governing authority: docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md (s1-s7),
  docs/PRD_PROCESS.md (CLASS Matrix, LANE Axis, GOVERNANCE HIGH-RISK list), CLAUDE.md,
  AGENTS.md, docs/contract/*.md. Owner rulings of 2026-09-22 are recorded in the packet
  header; treat them as given (do not relitigate R1-R6), but DO flag any packet text that
  misstates, widens, or narrows them.
- Ignore modified files under logs/ and ui/dashboard.html if present (disposable local
  output, outside the packet).

## What is proposed (context, not presumed truth)
A later PRD-347 (not yet opened) would compact the LIVE agent-facing Markdown instruction /
control surface named in the packet's payload list, as a semantic no-op: removing
duplicated policy, historical narrative, ritual procedure and obsolete model handholding
while preserving every authority, scope, review, security, fail-closed, parser/interface
and owner-held constraint. No code, test, tool, hook, settings or workflow file changes.

## Attack these specifically (falsify, do not confirm)
1. PARSER / CONSUMER COMPLETENESS (packet s4). Independently search scripts/, tools/,
   tests/, .claude/hooks/, .claude/settings*.json, .github/, cuttingboard/, workers/,
   pyproject.toml, and the skills themselves for ANY dependency on the literal text, a
   heading, a section name, a path, a table shape, or frontmatter of a payload file. Name
   every dependency the frozen set omits (consumer file:line, literal, failure mode). Also
   check inbound references FROM excluded docs (PRD_PROCESS.md, GOV-2, DECISIONS.md,
   PROJECT_STATE.md, docs/plans/*) INTO payload files by section name or path -- a
   compaction that renames or deletes a cited section silently breaks them.
2. SILENT-FAILURE CLASSIFICATION. For each frozen item, is the stated failure mode right?
   Flag any item marked as loud (red test/CI) that actually fails silently, and vice versa.
3. PAYLOAD BOUNDARY (s2/s3). Is any included file actually ratified/owner-verbatim text
   (R3-excluded in spirit), a machine interface too risky for a no-op claim, or out of the
   original charge's scope (model seating, product behavior)? Is any live agent-facing
   instruction file omitted that the charge's objective requires? Are line counts right?
4. PRESERVATION CONTRACT (s5/s6). Is the "semantic no-op" definition operational and
   falsifiable? Can the rule-ledger method miss a class of weakening (e.g. implicit
   constraints carried by ordering, scope words like "every"/"only", examples that define
   a rule, stop conditions in prose, fail-closed defaults)? Does any PERMITTED removal
   class allow deleting something load-bearing? Is any needed FORBIDDEN transform missing?
5. AUTHORITY / GOVERNANCE CONSISTENCY. Does the packet correctly apply GOV-2 s1/s2/s4/s5,
   the HIGH-RISK lane rule, PRD-255 ordering, and the commissions? Does it claim or imply
   any authority it lacks (implementation, ceiling approval, completeness certification)?
6. FACTUAL DEFECTS. Every file:line citation and quoted literal must resolve at HEAD.
   Report each one that does not.

## Output (your final message; ASCII only)
EVENT: INITIAL PACKET REVIEW
REVIEWER: <model id> (Codex), fresh-context independent
EXACT REVIEWED SHA: <git rev-parse HEAD>
DATE: <UTC date>
VERDICT: one of CLEAN | CLEAN WITH NITS | CHANGES REQUIRED | DESIGN INCOMPLETE (GOV-2 s6)
FINDINGS: numbered F1..Fn, each with CLASS (BOUNDARY-RESET | COMPLETENESS | FACTUAL |
  CONTRACT | GOVERNANCE | NIT), evidence (file:line), and the smallest correction.
  Write `none` only if that is the truthful result.
NON-FINDINGS: one line per attack area (1-6) you checked and found sound, with the
  decisive search you ran.
Do not propose wording for the compaction itself; review the boundary.
