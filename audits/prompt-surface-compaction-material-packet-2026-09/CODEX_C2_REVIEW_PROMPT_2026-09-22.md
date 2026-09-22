GOV-2 INITIAL PACKET REVIEW, CYCLE 2 -- Prompt-Surface Compaction MATERIAL Packet (Codex)

AUTHORITY: REVIEW (owner-commissioned 2026-09-22, ruling R4). You are the INDEPENDENT Codex
reviewer for a NEW bounded GOV-2 cycle on a MATERIAL packet whose governed claim was
narrowed by owner ruling R7. Fresh context, read-only, no edits, no implementation, no
merge. Try to FALSIFY the narrowed packet; do not approve it.

## Base
- Run `git rev-parse HEAD` and report the SHA you reviewed.
- Packet (read in full): audits/prompt-surface-compaction-material-packet-2026-09/
  PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md (rev 3).
- Cycle-1 history (read for context; do not re-litigate): CODEX_EVENT_1_REVIEW_2026-09-22.md
  and CODEX_EVENT_2_CONFIRMATION_2026-09-22.md in the same directory. Cycle 1 ended DESIGN
  INCOMPLETE; the owner then narrowed the claim (R7). This is a fresh cycle.
- Governing authority: docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md (s1-s7),
  docs/PRD_PROCESS.md, CLAUDE.md, AGENTS.md, docs/contract/*.md. Owner rulings R1-R7 are
  given; flag any packet text that misstates, widens, or narrows them.
- Ignore modified files under logs/ and ui/dashboard.html if present.

## The governed claim (R7, verbatim)
"Complete inventory and semantic-no-op compaction of Cuttingboard's LIVE agent-facing
Markdown instruction/control surface." It is NOT a claim to enumerate every agent-control
surface of every file type. Non-Markdown controls are outside the payload; the packet must
record and freeze the specifically discovered ones as external dependencies, without
claiming completeness about non-Markdown surfaces.

## Attack these (falsify, do not confirm)
1. MARKDOWN INVENTORY COMPLETENESS: is any live agent-facing Markdown instruction/control
   file (tracked, or untracked-but-loaded where the packet claims to cover it) unclassified
   or misclassified by s2A? Re-run its method and reasonable variants.
2. PARSER / CONSUMER COMPLETENESS for the Markdown payload: any dependency (code, test,
   hook, settings, CI, skill, or inbound Markdown citation by path or section name) on a
   payload literal, heading, section name, path, table shape, or frontmatter that the frozen
   set omits or misclassifies (loud vs SILENT).
3. EXTERNAL NON-MARKDOWN DEPENDENCIES: for each surface R7 names, is the recorded
   dependency accurate (file:line) and is every payload Markdown statement that depends on
   or describes it protected? Do NOT report the mere existence of further non-Markdown
   surfaces as a boundary omission (R7 excludes that claim); DO report a payload Markdown
   statement whose rewrite could break or misdescribe a non-Markdown control.
4. PRESERVATION CONTRACT: is the no-op definition operational and executable? In
   particular, do the frozen items and the s9.3 hash check protect the real invariants
   WITHOUT forbidding the removals s2 proposes (the cycle-1 whole-range contradiction)?
   Can any permitted removal delete something load-bearing?
5. AUTHORITY / GOVERNANCE CONSISTENCY: GOV-2 s1/s2/s4/s5/s6/s7, HIGH-RISK lane, PRD-255,
   commissions, truthful cycle history (no softening of cycle 1). Any authority claimed
   that the packet lacks?
6. FACTUAL DEFECTS: every file:line and quoted literal must resolve at HEAD.

## Output (final message; ASCII only)
EVENT: INITIAL PACKET REVIEW (GOV-2 cycle 2)
REVIEWER: <model id> (Codex), fresh-context independent
EXACT REVIEWED SHA: <git rev-parse HEAD>
DATE: <UTC date>
VERDICT: CLEAN | CLEAN WITH NITS | CHANGES REQUIRED | DESIGN INCOMPLETE (GOV-2 s6)
FINDINGS: C2-F1..C2-Fn, each with CLASS (BOUNDARY-RESET | COMPLETENESS | FACTUAL |
  CONTRACT | GOVERNANCE | NIT), evidence (file:line), and the smallest correction.
  `none` only if truthful.
NON-FINDINGS: one line per attack area (1-6) with the decisive search you ran.
