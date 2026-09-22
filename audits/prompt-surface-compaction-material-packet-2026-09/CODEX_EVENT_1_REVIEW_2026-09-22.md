# CODEX EVENT 1 -- INITIAL PACKET REVIEW (GOV-2 s2)

EVENT: INITIAL PACKET REVIEW
REVIEWER: Codex, resolved model gpt-5.6-sol (from the codex exec banner in the job
stdout.log; the reviewer's self-report below says "GPT-5"), reasoning effort high.
CAPABILITY ROLE: GOV-2 independent material-packet reviewer, AUTHORITY: REVIEW
(owner-commissioned 2026-09-22, ruling R4), including the mechanical
parser/consumer/dependency audit.
EXACT REVIEWED SHA: bcb859bd5148d92b9e6707981ca094dbc5053965 (packet rev 1).
DATE: 2026-09-22 (run 23:06:51Z-23:22:49Z UTC).
VERDICT: CHANGES REQUIRED.

RUN-ISOLATION / INDEPENDENCE EVIDENCE: dispatched via ~/cuttingboard-agent-jobs/cbagent
as a systemd --user transient unit running a fresh `codex exec` (new session
01a0cb5f-485b-71c3-a8a5-7c09ff49be53, no resume) with no shared context with the
authoring session (Claude orchestrator + Fable Navigator author). Sandbox read-only
(no edits possible). The runner's exact-SHA guard refused launch unless repo HEAD ==
bcb859bd before starting; the prompt did not restate the SHA, which is why the
reviewer's LAUNCH SHA CHECK line below says none was supplied in metadata.
cbagent job id: codex-20260922T230651Z-7312.
MEMORY PROVENANCE: the Codex memories feature is enabled in CODEX_HOME
(~/.codex/config.toml [features] memories = true). A binary-inclusive search of
~/.codex/memories and memories_1.sqlite* for "prompt-surface", "PRD-347" and
"compaction material" returned no match, so no Codex memory could carry this packet
or the authoring session's framing (the packet was first written in this session).

Findings dispositions: see "Dispositions" at the end of this record (added with the
one consolidated correction).

## Verbatim reviewer output

EVENT: INITIAL PACKET REVIEW
REVIEWER: GPT-5 (Codex), fresh-context independent
EXACT REVIEWED SHA: bcb859bd5148d92b9e6707981ca094dbc5053965
LAUNCH SHA CHECK: No reviewed SHA was supplied in launch metadata. The packet's 73a13762 evidence base is the parent main commit; bcb859bd5148d92b9e6707981ca094dbc5053965 is the provisional packet commit reviewed.
DATE: 2026-09-22
VERDICT: CHANGES REQUIRED

FINDINGS:

F1
CLASS: BOUNDARY-RESET
Evidence: The objective claims the live agent-facing Markdown instruction surface at audits/prompt-surface-compaction-material-packet-2026-09/PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md:39-44, but docs/dev_workflow.md is neither IN nor explicitly OUT. It identifies itself as the standard validation/push workflow at docs/dev_workflow.md:1-8, contains executable agent instructions at :10-25 and :45-68, and points into the payload at :8. The packet itself notices that inbound reference in F19 at packet:122, so this is not an undiscoverable file.
Failure mode: The packet can call its boundary deliberate while leaving a live operational instruction surface unclassified; overlapping instructions can remain stale after compaction.
Smallest correction: Perform GOV-2 section 6's first complete instruction-surface inventory refresh and explicitly classify docs/dev_workflow.md as IN or OUT with a reason. This is the initial-review omission, so CHANGES REQUIRED rather than DESIGN INCOMPLETE; another new class at exact-head confirmation would trigger the latter.

F2
CLASS: COMPLETENESS
Evidence: The frozen consumer inventory omits these concrete dependencies found in the commissioned search:

1. .claude/settings.local.json:173 names Skill(prd-authoring-verified). Changing that skill name or directory silently leaves the permission/dispatch entry stale.
2. scripts/pre_commit_sanity.sh:23-32 names scope-lock-precommit as the scope gate. F9 does not list this consumer; a rename silently turns the reminder into a dead instruction.
3. scripts/prd_close.sh:337-338 hard-codes docs/prd_history/${PRD_ID}.review.codex.md and conditionally stages it. F7 lists the validator and prd_eval hook but omits this consumer. A filename-convention change can silently leave the review artifact unstaged.
4. tests/test_prd_eval_hook.py:53-61 and :143-156 assert the .review.claude.md and .review.codex.md forms. Those tests remain green against the old hook convention if only payload prose changes, so they do not protect payload/hook agreement.
5. docs/plans/decision-support-expansion-doctrine-v0.1.md:132 and :437-439 plus docs/plans/decision-support-workplan-v0.1.md:75-77 and :93 require the plans and landing constraint to remain discoverable from CLAUDE.md. The operative payload carrier is CLAUDE.md:21-26 and :143-144, but neither F15 nor F20 freezes that plan pointer/content as an inbound dependency.
6. docs/plans/agent-work-charge-template-v0.1.md:175 and :203-206 consume the blocker literals in CLAUDE.md:151-152. F14 freezes the literals but omits this consumer.
7. All five mode files refer to "The wall", owner holds, precedence, and the common escalation block at docs/contract/MODE_DESIGN.md:3-4, MODE_IMPLEMENT.md:3-4, MODE_RECON.md:3-4, MODE_REVIEW.md:3-4, and MODE_STEWARD.md:3-4. F15's consumer list omits these inbound section-name dependencies.
8. docs/DECISIONS.md:792-797 records that the binding harness-seat invariants live in CLAUDE.md, whose carrier is CLAUDE.md:118-122. Those operator-less role statements are not in F20. docs/DECISIONS.md:2853-2856 also records prd-review-claude's Second-Model Disposition and DRIFT CHECK output as load-bearing, but F17 lists only generic adjudication readers.
9. docs/PROJECT_STATE.md:37-38 contains current-state inbound citations to nonexistent CLAUDE.md sections "How work lands" and "Review gates". This is an already-dangling excluded-doc dependency omitted from section 7's defect inventory.

Smallest correction: Add the omitted consumers and exact carriers to F7/F9/F14/F15/F17/F20, including their silent or delayed-loud failure modes. Record the existing PROJECT_STATE dangling citations as out-of-slice debt without repairing them in this compaction.

F3
CLASS: FACTUAL
Evidence: Several frozen rows do not resolve as written:

1. Packet F2 at packet:105 locates the complete SECOND-MODEL waiver literal at prd-closeout-verified/SKILL.md:20-22. Those lines contain only a prose reference to PRD-242; the literal exists at docs/PRD_PROCESS.md:285-286 and nowhere in the payload.
2. Packet F4 at packet:107 claims the six CLASS literals GOVERNANCE/SIDECAR/CONSUMER/EXECUTION/CONTRACT/INFRA occur at prd-authoring :110-112 and scope-lock :170/:204. The authoring lines contain V5-V7 and no CLASS vocabulary. The scope skill contains GOVERNANCE at :107-114 but none of the other five CLASS names.
3. Packet F12 at packet:115 includes **Last updated:** "as quoted in skills", but neither cited skill contains that literal. It exists in scripts/prd_close.sh:208-213, outside the payload.
4. Packet F16 at packet:119 claims an outbound OWNER_MERGE section 2/3 citation at docs/PRD_REVIEW_TEMPLATE.md:20; that line cites PRD_PROCESS Registry Maintenance. No payload file cites OWNER_MERGE sections 2/3. Conversely, CLAUDE.md:131-132 cites PRD_PROCESS "Review Dispatch", which F16 omits.
5. Packet F18 at packet:121 describes "V-row numbering (V1..V10)" across all four skills. The actual ranges are V1..V10 at prd-authoring:106-115, V1..V12 at prd-closeout:162-173, V1..V13 at prd-review:210-222, and V1..V9 at scope-lock:198-206.

Smallest correction: Rebuild the frozen table row-by-row from current HEAD. Distinguish literals actually present in payload from external canonical literals merely referenced by payload, and state each skill's real V-row range.

F4
CLASS: CONTRACT
Evidence: The permitted-removal classes already designate operative behavior as removable narrative.

1. P2 names docs/CLAUDE_HOOKS.md:40-53 as historical/rationale text. Lines :48-53 state the current, deliberately decided limitation that protect_files.sh does not cover Bash and explain that protected writes use Bash. Removing that range changes the documented hook boundary.
2. P3 names prd-authoring-verified/SKILL.md:143-162 as ritualized procedure with no consumer. Lines :143-153 are the actual fallback inspection chain required by the hard rule at :65-66; prd-review-claude/SKILL.md:94-97 explicitly reuses that chain. Lines :155-161 also define the subagent threshold and when pre_commit_sanity applies.

Failure mode: An implementer can ledger these operative instructions as P2/P3 removals while satisfying the packet's stated examples, weakening verification without violating a frozen item.
Smallest correction: Split rationale from operative behavior. Mark CLAUDE_HOOKS :48-53 and prd-authoring :143-161 as preserved unless a rule-by-rule proof establishes an equivalent locally loaded instruction. Define P3 as requiring proof that no invoking agent, cross-reference, refusal, fallback, or report contract consumes the procedure.

F5
CLASS: CONTRACT
Evidence: The semantic-no-op proof is not sufficiently falsifiable.

1. Packet:143-150 permits "equal or stronger force". Stronger force can narrow authority, expand a stop, or turn permission into obligation; that is a semantic change even if no sentence is nominally added.
2. Packet:143-155 starts from an operator grep and then says to "hand-add operator-less rules" without an exhaustive criterion. It can miss negation, defaults, exceptions, closed lists, quantifiers such as every/any/exactly, trigger conditions, row order, examples defining syntax, and descriptive authority such as CLAUDE.md:118-122 and :143-144.
3. Packet:234-237 proposes per-file rg counts where post >= pre. Deleting one load-bearing occurrence and duplicating another preserves the count. It does not prove byte identity or location/role preservation.
4. Packet:152-157 maps line IDs, but does not require proof that a cited replacement is loaded on the same trigger beyond author judgment, nor that ordering and scope qualifiers survive.

Smallest correction: Require equal force and equal scope, not "equal or stronger"; inventory structural rule units as well as operator-bearing sentences; explicitly include negation, quantifiers, exceptions, defaults, ordered rows, examples, headings, and operator-less authority; and verify every frozen item with exact pre/post bytes or hashes rather than occurrence counts.

F6
CLASS: FACTUAL
Evidence: Two silent-failure classifications are wrong or overbroad.

1. F8 says renaming/moving repo-root CLAUDE.md causes "Test red". canonical_read_guard.sh:24-31 compares the requested realpath to the constructed root/CLAUDE.md path without checking file existence. tests/test_canonical_read_guard_hook.py:46-49 passes that constructed path and asserts only that a reminder appears. The test remains green if CLAUDE.md is moved; harness injection is what fails, silently.
2. F4 says changed LANE/CLASS vocabulary causes a silent lane-guard miss. For GOVERNANCE payload PRDs, unknown CLASS values are explicit validator errors at tools/validate_prd_registry.py:788-795, and a missing/non-HIGH-RISK lane produces the lane-downgrade error at :817-839. Other cases may be silent, but the row cannot classify the entire failure as SILENT.

Smallest correction: Mark F8 SILENT and name the harness loader as the decisive consumer. Split F4 by path: loud validator failure for guarded GOVERNANCE payload cases, silent or process-only drift where no validator branch applies.

F7
CLASS: GOVERNANCE
Evidence: The packet mixes owner questions and reviewer assignments with a preservation contract that currently forbids them.

1. F19 at packet:122 requires the CLAUDE_HOOKS wired-hooks table to survive byte-identical, while Q3 at packet:251-253 offers adding the missing SessionStart row inside PRD-347.
2. F18 and packet:178-179 make deletion of retired V-row markers a STOP, while Q6 at packet:257 offers dropping them.
3. The recorded R4 seat at packet:10-12 assigns Astra the fresh-context PRD review after the design-direction ruling. Packet:152-157 says the implementation-time rule ledger is produced during implementation and that "Astra reviews the ledger itself"; packet:240-242 again assigns Astra the implementation-focused semantic review. That is wider than the recorded R4 PRD-review seat unless separately commissioned.

Smallest correction: Mark Q3 and Q6 as scope/contract-changing alternatives that require a revised packet and renewed independent review if selected; they cannot remain inside the current semantic-no-op contract. Describe the implementation-ledger reviewer as proposed and uncommissioned, or confine Astra to the R4 PRD-review seat until Dustin separately commissions the later review.

NON-FINDINGS:

1. PARSER / CONSUMER COMPLETENESS: No executable test directly reads payload body text or asserts payload line counts/headings. The decisive path/literal rg across scripts/, tools/, tests/, .claude/hooks/, both settings files, .github/, cuttingboard/, workers/, pyproject.toml, and all skills found only the dependencies reported in F2 plus the packet's already-listed consumers.
2. SILENT-FAILURE CLASSIFICATION: F1, F2, F6, F7, and F9-F20 are otherwise consistent with the inspected consumers after the F6 exceptions; this was checked against validator branches, hook bodies, tests, and loader conventions.
3. PAYLOAD BOUNDARY: The seven stated counts are exact at HEAD: 184 + 87 + 180 + 240 + 288 + 263 + 255 = 1497, and the estimated posts total 1245. git diff 73a13762..HEAD contains only the two packet files. The only boundary defect found is F1.
4. PRESERVATION CONTRACT: The contract correctly forbids weakening STOP/refusal/fail-closed rules, moving rules outside a load set, changing precedence/owner holds, and editing non-payload files. The defects are the permitted-removal examples and proof gaps in F4-F5 plus the conflicting options in F7.
5. AUTHORITY / GOVERNANCE: MATERIAL, CLASS GOVERNANCE, and LANE HIGH-RISK are correctly applied; GOV-2 steps 1-5, the no-downstream-authority rule, provisional ceiling labels, and PRD-255's lower-number-document ordering are stated correctly. PRD-346.md is absent, so the stated closeout hold is current. No implementation or merge authority is claimed.
6. FACTUAL DEFECTS: All remaining packet file paths, line counts, cited authority sections, and quoted literals checked with nl/rg resolve at bcb859bd5148d92b9e6707981ca094dbc5053965. The non-resolving or misclassified items are exhaustively listed in F2, F3, and F6.

