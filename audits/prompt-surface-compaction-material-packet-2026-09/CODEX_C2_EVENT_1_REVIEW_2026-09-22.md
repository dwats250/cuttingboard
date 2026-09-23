# CODEX CYCLE 2 EVENT 1 -- INITIAL PACKET REVIEW (GOV-2 s2, new cycle per owner ruling R7)

EVENT: INITIAL PACKET REVIEW (GOV-2 cycle 2)
REVIEWER: Codex, resolved model gpt-5.6-sol (codex exec banner in the job stderr.log;
self-report below says "GPT-5"), reasoning effort low (unmodified runner, config
default; cycle 1 ran at high via the since-reverted --effort change).
CAPABILITY ROLE: GOV-2 independent material-packet reviewer, AUTHORITY: REVIEW
(owner-commissioned 2026-09-22, ruling R4).
EXACT REVIEWED SHA: 394006f0839ad27eab9f3b4f455670f58c689a96 (packet rev 3, narrowed claim).
DATE: 2026-09-22 (run 23:58:44Z-00:02:15Z UTC, ended 2026-09-23).
VERDICT: CHANGES REQUIRED.

RUN-ISOLATION / INDEPENDENCE EVIDENCE: cbagent systemd --user transient unit, fresh
`codex exec` session 01a0cb8e-bfc0-7f52-87a1-72aea9508117 (no resume), no shared context
with the authoring session, read-only sandbox, exact-SHA guard (launch refused unless
HEAD == 394006f0). cbagent job id: codex-20260922T235844Z-847d. Prompt: CODEX_C2_REVIEW_PROMPT_2026-09-22.md.
MEMORY PROVENANCE: Codex memories feature enabled in CODEX_HOME; binary-inclusive search of
~/.codex/memories and memories_1.sqlite* for "prompt-surface", "PRD-347",
"compaction material" at record time: no match.

Findings dispositions: see "Dispositions" at the end of this record (added with the one
consolidated cycle-2 correction). C2-F1 is the FIRST newly discovered class in cycle 2
(GOV-2 s6: one complete inventory refresh).

## Verbatim reviewer output

EVENT: INITIAL PACKET REVIEW (GOV-2 cycle 2)
REVIEWER: GPT-5 (Codex), fresh-context independent
EXACT REVIEWED SHA: 394006f0839ad27eab9f3b4f455670f58c689a96
DATE: 2026-09-22
VERDICT: CHANGES REQUIRED

FINDINGS:

C2-F1
CLASS: BOUNDARY-RESET
Evidence: The governed claim covers the complete LIVE agent-facing Markdown instruction/control surface, but s2A excludes the entire `audits/` tree before classification and then claims completeness over 59 files (`audits/prompt-surface-compaction-material-packet-2026-09/PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md:128-151`). At this exact HEAD, `audits/prompt-surface-compaction-material-packet-2026-09/CODEX_C2_REVIEW_PROMPT_2026-09-22.md:1-57` is tracked, live, agent-facing Markdown control text: it commissions this review, sets AUTHORITY, constrains reads and behavior, and prescribes the output contract. It was added by the same rev-3 commit being reviewed. The method excludes it without classifying it IN or OUT. Reasonable-variant searches also found other tracked audit-local prompt/charge Markdown files, so the blanket directory exclusion cannot itself establish that all excluded audit files are historical or inactive.
Smallest correction: Refresh the Markdown inventory without silently excluding `audits/`. Define an operational LIVE test, classify the current cycle-2 prompt and every other audit-local Markdown file meeting that test, and classify the remaining audit group OUT with a reproducible reason. This is the first newly discovered Markdown class in cycle 2, so GOV-2 s6 requires the complete inventory refresh; it does not yet establish the later-review condition for DESIGN INCOMPLETE.

C2-F2
CLASS: CONTRACT
Evidence: The class-H verification still permits deletion of a load-bearing occurrence when the same literal occurs elsewhere. Section 9.3 extracts units by content anchor, requires equal hashes, and requires only that each unit remain present "at least once" (`audits/prompt-surface-compaction-material-packet-2026-09/PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md:397-402`). Several frozen units have multiple semantically distinct occurrences, including `LANE: HIGH-RISK` and related LANE forms enumerated at packet:212, repeated report labels and V-row structures at packet:222, and repeated hook/script paths at packet:223. Deleting one occurrence while retaining another identical occurrence can satisfy the stated extraction and hash test while breaking the deleted occurrence's local table, report, or rule role. The class-L ledger does not cure this because these occurrences are expressly class H.
Smallest correction: Give every class-H occurrence a stable ID and extract it with file plus unique structural context, such as heading/table/row identity and occurrence cardinality. Require a one-to-one pre/post manifest with identical bytes and role, not merely one surviving matching literal.

C2-F3
CLASS: CONTRACT
Evidence: The required class-H checker has no executable location consistent with the proposed file boundary. Section 9.3 requires a "script committed with the ledger" (`audits/prompt-surface-compaction-material-packet-2026-09/PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md:397-400`), but section 9.2 permits only payload paths, Stage-0 bookkeeping, and the Markdown ledger, and requires every changed path to be Markdown (`packet:393-396`). The seven-file payload and zero-non-payload rule likewise exclude a checker script (`packet:121-124`). A separate script violates the boundary; an uncommitted ad hoc script is not the specified committed proof; and the packet does not say that executable checker code is embedded in the ledger.
Smallest correction: Specify one consistent proof carrier. Either define a named checker artifact and include it in the provisional boundary, with the required GOV-2 scope consequences, or require executable checker code to be embedded verbatim in `RULE_LEDGER_PRD-347.md` and state exactly how its pre/post inputs and manifest are generated.

NON-FINDINGS:

1. MARKDOWN INVENTORY COMPLETENESS: Re-ran the stated `git ls-files '*.md'` method, filesystem and ignored-file variants, and prompt/charge-name searches. The stated filtered count of 59 is reproducible, but the decisive variant found the live tracked cycle-2 review prompt excluded with all of `audits/`, producing C2-F1. The ignored root `ASTRA_EXECUTION_PLAN.md` and `OWNER_INTENT_NEXT.md` are recorded as outside the loaded working-checkout surface.

2. PARSER / CONSUMER COMPLETENESS: Searched payload paths, skill names, review filename forms, section names, headings, LANE/CLASS literals, frontmatter terms, and hook/workflow names across code, tests, hooks, settings, workflows, canonical Markdown, plans, and templates. No additional payload consumer class was established beyond A1-A20/B1-B6; the remaining verification defect is occurrence identity in C2-F2.

3. EXTERNAL NON-MARKDOWN DEPENDENCIES: Read the recorded settings, hook, bootstrap, campaign workflow/schema, and publication-workflow locations directly. X1-X9 resolve and their described payload relationships are materially accurate; no omitted payload statement depending on those specifically discovered surfaces was found.

4. PRESERVATION CONTRACT: Compared the permitted-removal classes, class-H/class-L split, full rule-unit ledger definition, and s9 verification plan against the seven payload files. The cycle-1 whole-range contradiction is removed, and the named P2/P3 examples preserve the previously load-bearing ranges, but the duplicate-occurrence hash weakness and checker-carrier contradiction remain as C2-F2 and C2-F3.

5. AUTHORITY / GOVERNANCE CONSISTENCY: Checked GOV-2 s1-s7, MODE_REVIEW, PRD_PROCESS HIGH-RISK rules, PRD-255 allocated-number ordering, PRD-346 absence, commissions, and packet history. MATERIAL / CLASS GOVERNANCE / LANE HIGH-RISK, the lack of downstream authority, cycle-1 DESIGN INCOMPLETE history, R7 narrowing, and the new-cycle sequence are stated truthfully. No unauthorized ruling, Gate A, implementation, or merge authority is claimed.

6. FACTUAL DEFECTS: Resolved the packet's named payload counts, LANE sweep, PRD-255 citation, PRD-346 absence, external dependency line ranges, workflow/schema facts, and current branch history at the reviewed SHA. The seven payload counts total 1497 and the filtered inventory totals 59. No separate factual citation defect was established beyond the contract and boundary defects above.