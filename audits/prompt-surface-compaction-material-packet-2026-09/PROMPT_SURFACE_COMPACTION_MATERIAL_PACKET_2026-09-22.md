# Prompt-Surface Compaction MATERIAL Packet (2026-09-22)

STATUS: PROVISIONAL rev 1 (GOV-2 s2 step 2). NOT review-clean. Authorizes NOTHING: no
design-direction ruling, no Stage-0, no Gate A, no implementation, no merge is implied.
CLASS GOVERNANCE / LANE HIGH-RISK / MATERIAL (owner ruling R2). Reserved number: PRD-347
(NOT opened; Stage-0 waits for the design-direction ruling, R5). Base: main @ 73a13762 on
branch claude/prompt-surface-compaction-packet (no other commit; nothing pushed).
Seats (R4): Fable = AUTHORITY: DESIGN / Navigator (this author: provisional design and
proposed wording only). Codex = AUTHORITY: REVIEW (packet review + mechanical
parser/consumer/dependency audit; exact-corrected-head confirmation). Astra = AUTHORITY:
REVIEW (fresh-context PRD review after the ruling). Builder after Gate A: Opus 4.8 via
Claude Code. GOV-2 s11 restricted-model identity: NOT inferred (UNKNOWN).
Non-claims: the author does NOT certify boundary completeness (GOV-2 line 14: "No agent
certifies the completeness of the boundary it chose"); author self-verification is not
independent review (GOV-2 s3). All line counts/estimates below are `ESTIMATED SURFACE -
NOT YET APPROVED` (GOV-2 s5). CI on this docs branch confirms only that the branch
preserves the current green baseline; it does not validate the proposed edits (GOV-2 s8).

Owner rulings 2026-09-22 (Dustin), recorded as minimum provenance:
- R1 Proceed now as a bounded governance-maintenance window (explicit owner priority decision);
  does not retire, supersede, or reorder the product-priority lanes
  (PRODUCT_DELIVERY_OPERATING_RULE_2026-08-06.md:80); product delivery resumes after this slice.
- R2 MATERIAL / CLASS GOVERNANCE / LANE HIGH-RISK; full GOV-2 sequence. PRD-294's
  owner-boundary precedent is NOT an exemption; "frozen boundary" is used inside GOV-2.
- R3 Excluded: docs/governance/*, docs/PRD_PROCESS.md (possible later slice), docs/DECISIONS.md
  (lifecycle owner-ruling provenance only; history never compacted), VISION.md,
  docs/plans/*-v0.1.md. Historical PRDs, reviews, audits, evidence untouched.
- R4 Seats as above; Fable does not independently drive the MATERIAL implementation.
- R5 PRD-347 reserved. PRD-255 ordering (PRD_PROCESS.md:88): PRD-347 cannot close until the
  PRD-346 document lands on main (absent on main today). PRD-346 stays parked, untouched.
- R6 Side findings (stale PROJECT_STATE Active PRD pointer, missing dev_bootstrap hook row in
  CLAUDE_HOOKS.md, dual review format) are follow-ups, not payload, unless proven necessary.
Also out of scope per the charge: product behavior, model seating (docs/AGENT_SEATING.md),
unrelated cleanup. Evidence base: the author's re-verification of every file:line below at
73a13762; session recon notes are scratchpad-only and not relied on for any citation.

## 1. Objective and non-goals

Objective: a semantic-no-op compaction of the LIVE agent-facing Markdown instruction surface
that removes (a) restatements of policy whose authoritative text lives in a canonical source
(replace with a by-name citation), (b) historical explanation / rationale narrative, (c)
ritualized procedure with no consumer, and (d) obsolete model handholding, while preserving
every authority, scope, review, security, fail-closed, parser/interface, and owner-held
constraint byte-for-byte where a consumer depends on the literal (section 4).

Non-goals: no governance redesign; no change to precedence, owner holds, the merge wall, lanes,
or review gates; no edit to any code, test, tool, hook, settings, or workflow file; no rewording
of ratified or owner-authored text (R3); no seating change; no side-finding fixes (R6) except
as the owner rules in section 10.

## 2. Payload boundary (ESTIMATED SURFACE - NOT YET APPROVED)

Candidates decided deliberately. IN = payload. OUT = excluded (reason in section 3).

| File (wc -l @ 73a13762) | Decision | Compaction intent (one line) | Est. post |
|---|---|---|---|
| CLAUDE.md (184) | IN | Already cut 483->184 by V1; residual: prose glosses that restate a named canonical source (e.g. :131-132 topic list duplicates PRD_PROCESS headings; :85 rationale pointer). Modest gain. | ~165 |
| docs/CLAUDE_HOOKS.md (87) | IN | Drop PRD-254/PRD-243 rationale narrative (:40-53, :63-69); keep wired-hooks table (:9-13), each hook's behavior, and the two-scopes rule (:30-38). | ~50 |
| .claude/skills/prd-authoring-verified/SKILL.md (180) | IN | Drop restated PRD_PROCESS policy (:83-91 lane rules -> cite), retired-row explanation (:115, :143 narrative), shared boilerplate; keep V-table rows, report shape, refusal list. | ~155 |
| .claude/skills/prd-closeout-verified/SKILL.md (240) | IN | Drop restated Same-PR Closeout / PRD-242 policy (:20-36 -> cite PRD_PROCESS by section); keep script-contract, V-rows, report, refusals. | ~205 |
| .claude/skills/prd-review-claude/SKILL.md (288) | IN | Drop history markers and retired-mechanism narrative (e.g. :106-110 prd_eval retirement story); keep stage-locked paths (:99-114), review structure (:115-170), V-table, refusals. HIGH-RISK file. | ~235 |
| .claude/skills/scope-lock-precommit/SKILL.md (263) | IN | Drop PRD-276/277/278 narrative (:116-140); keep FILES parsing rule (:73-93), allowlist (:95-115), protected-set procedure (:141-176), V-table, refusals verbatim. | ~225 |
| docs/PRD_REVIEW_TEMPLATE.md (255) | IN | Drop PRD-120 "Why this exists" narrative (:237-249) and rationale asides; keep section order (:25-82), checklist (:83-108), Review Independence (:144-191), REVIEWED STATE (:157), Filename convention (:12-13), Mapping-Table checklist. HIGH-RISK file. | ~210 |
| AGENTS.md (84) | OUT | Overlap with CLAUDE.md is by design: Codex loads AGENTS.md, not CLAUDE.md (:3-4), so the wall restatement cannot be replaced by a citation without moving rules out of Codex's load set (forbidden, s6). Residual gain < 10 lines. See Q1. | - |
| CODEX.md (15) | OUT | Already a 15-line pointer; the only remaining transform is deletion, a different change class. Follow-up (s8). | - |
| docs/contract/MODE_*.md (5 files, 207) + CHARGE_TEMPLATE.md (37) | OUT | Each is the binding Layer-2 session contract; the shared 2-line preamble is load-bearing ("Layer 1 still binds"); estimated gain < 15 lines total. See Q1. | - |
| docs/AGENT_WORKFLOW.md (51) | OUT | Interface file: heading + table parsed verbatim by two skills (:6-7); only :3-13 preamble is compactable (~6 lines). Not worth the parser risk. | - |
| .claude/skills/session-handoff/SKILL.md (105) | OUT | No canonical-source duplication found; gain marginal. | - |
| docs/PRD_TEMPLATE.md (68), docs/PRD_MICRO_TEMPLATE.md (81) | OUT | Shape mirrored by scripts/prd_open.sh:89-143 and the validator (D15 has no template-vs-script test: SILENT divergence). MICRO_TEMPLATE.md:66 enters ONLY if Q2 = repoint (1-line ceiling). | - |
| docs/tools/GITNEXUS.md (39) | OUT | Its status conflicts with prd-authoring :115/:143 ("GitNexus removed", PRD-243) and .claude/settings.local.json enabling the MCP; resolving that is semantic, not compaction. Follow-up. | - |

Payload total: 7 files, 1497 lines; estimated post ~1245 (about -250 lines, -17%). ESTIMATED
SURFACE - NOT YET APPROVED. Proposed ceiling form (Q4): no payload file grows; each file's
post-edit count <= its estimate + 10%; zero non-payload diff. NO code, test, tool, hook,
settings, or workflow file is in the payload. The GOVERNANCE HIGH-RISK FILES set
(PRD_PROCESS.md:458; validator :38-45) intersects the payload at CLAUDE.md, the prd-review-claude
skill, and docs/PRD_REVIEW_TEMPLATE.md, so LANE: HIGH-RISK is forced and CI-enforced (PRD >= 276).

## 3. Exclusions with reasons

- R3 set (above). docs/governance/* are owner-authored "verbatim/faithful" records
  (PRODUCT_DELIVERY:3-7; OWNER_MERGE:3-7); rewording them would falsify that status.
- docs/AGENT_SEATING.md (seating, per the charge); generated artifacts (logs/*,
  ui/dashboard.html dirty set: never staged).
- .github/campaign/charge_prompt.md: CI-bound Codex prompt with test-locked phrases
  (tests/test_campaign_control.py); under the protected `.github/` policy set.
- .codex/ (gitignored local hook mirror), untracked root ASTRA_EXECUTION_PLAN.md /
  OWNER_INTENT_NEXT.md (outside git), .claude/worktrees/*/CLAUDE.md (4 stale copies): not
  the working checkout's loaded surface.
- docs/PROJECT_STATE.md, docs/PRD_REGISTRY.md, docs/prd_index.json: state/data, parser-bound
  (scripts/prd_close.sh:208,230,253,267; pre_commit_sanity.sh:29; validator :98-99); PRD-347
  Stage-0 touches them only as annotated bookkeeping `(PRD-NNN row)` / `(active PRD pointer)`.
- docs/SCHEMA_MAP.md, docs/CALL_SITE_MAP.md: recon cache data, not instructions.
- AGENTS.md, CODEX.md, docs/contract/*, AGENT_WORKFLOW.md, session-handoff skill, the two PRD
  templates, GITNEXUS.md: per the section-2 table.

## 4. Frozen interface set (must survive byte-identical; STOP if a compaction would alter one)

Rule: if a proposed edit would change any item below, the implementer STOPS and reports; the
consumer is never patched to fit the compaction. SILENT = breaks with no red signal.

| ID | Frozen literal / structure | Location in payload | Consumer (file:line) | Failure mode |
|---|---|---|---|---|
| F1 | Paths `CLAUDE.md`, `.claude/skills/prd-review-claude/SKILL.md`, `docs/PRD_REVIEW_TEMPLATE.md` (no rename/move) | file paths | tools/validate_prd_registry.py:38-45 GOVERNANCE_PAYLOAD_FILES; PRD_PROCESS.md:458 | Lane enforcement drops: SILENT |
| F2 | `SECOND-MODEL: instrument not commissioned, merging on Claude-review + human judgment` referenced by name, never paraphrased into a payload file | closeout SKILL:20-22 (by name) | validator :23-25, :601; PRD_PROCESS.md:286 | A paraphrase copied into a future PRD fails CI later: delayed-loud |
| F3 | Annotations `(PRD-NNN row)`, `(active PRD pointer)`, `(pointer)`, `(bookkeeping)` | scope-lock SKILL:90, :108-113 | validator :86-89; PRD_PROCESS.md:59 | Future GOVERNANCE PRD CI red / bypass: SILENT until then |
| F4 | `LANE: HIGH-RISK`, `LANE: MICRO` literal forms; CLASS names GOVERNANCE/SIDECAR/CONSUMER/EXECUTION/CONTRACT/INFRA | prd-authoring :110-112; scope-lock :170, :204 | validator :56, :60-62, :78-79; AGENT_WORKFLOW.md:50 | Lane guard miss: SILENT |
| F5 | FILES syntax: `^[AMD] <path>` and backtick list under `Modified:` / `New:` | scope-lock SKILL:73-93 (whole section) | validator :75; scripts/prd_open.sh:89-91; PRD_MICRO_TEMPLATE.md:28-33 | Zero entries -> stop (loud); misparse: SILENT |
| F6 | `STATUS: COMPLETE @ <ref>` form | closeout SKILL description :3 and procedure | validator :97 DOC_STATUS_RE | CI error (loud) |
| F7 | `docs/prd_history/PRD-NNN.review.claude.md`, `PRD-NNN.review.<model>.md`, `.review.` sidecar exclusion, refusal regex :113 | prd-review-claude :99-114; REVIEW_TEMPLATE :12-13 | validator :596-607; .claude/hooks/prd_eval.sh:58 | CI red (validator); hook: SILENT |
| F8 | Repo-root path `CLAUDE.md` | file path | .claude/hooks/canonical_read_guard.sh:26; tests/test_canonical_read_guard_hook.py:47 | Test red |
| F9 | Harness-loaded filenames `CLAUDE.md` (root), `.claude/skills/<dir>/SKILL.md`; skill directory names cited by MODE_IMPLEMENT.md:14, PRD_PROCESS.md:59,189,205,215, AGENT_WORKFLOW.md:5 | file paths | harness loader | Contract/skill silently not loaded: SILENT |
| F10 | YAML frontmatter `name:` and `description:` of every payload SKILL.md (lines 1-4) | 4 skills | harness skill trigger | Trigger behavior changes: SILENT (no test) |
| F11 | `## Auto-Approval Policy` heading and the "Never auto-approve" table (AGENT_WORKFLOW.md:15, :33-48) and every reference to them | scope-lock :141-176, :185, :204, :218, :230, :244, :255; prd-authoring :110 | AGENT_WORKFLOW.md:6-7 (declares itself parsed verbatim) | Heading gone -> fail-closed refusal (loud); table reword -> changed protected set: SILENT |
| F12 | PROJECT_STATE literals `- **Active PRD:**`, `**Next step`, `Test baseline`, `**Last updated:**` as quoted in skills | closeout :63-64, :88-89, :146-147, :169-170; scope-lock :53 | scripts/prd_close.sh:208,230,253,267; pre_commit_sanity.sh:29 | Skill quotes a wrong literal -> agent edits wrong line: SILENT |
| F13 | `docs/contract/MODE_<name>.md` path form and `AUTHORITY: <MODE>` charge line; `docs/contract/MODE_REVIEW.md` path | CLAUDE.md:70-73; prd-review-claude :203 | AGENTS.md:36; CHARGE_TEMPLATE.md:13; MODE_* filenames | Mode contract not found: SILENT |
| F14 | Blocker vocabulary `CI is running`, `Held for your merge`, `Held for your decision` ("used verbatim") | CLAUDE.md:151-152 | MODE_STEWARD.md:40; owner pattern-matches | SILENT |
| F15 | Inbound section names into CLAUDE.md: "The wall" (PRD_PROCESS.md:159, :573), "Roles" (:137), "Context and output hygiene" (:198, :343; prd-authoring :159 quoting "Recon goes to subagents"), "Owner holds" and "context/output hygiene" (AGENTS.md:47-53), "publish safety" (MODE_STEWARD.md:21), "Precedence" (CLAUDE.md:8) | CLAUDE.md headings :19, :45, :55, :104, :154 and the quoted phrase :156 | as listed | Dangling citation: SILENT (precedent: 5 already dangling, s7) |
| F16 | Outbound section names cited from payload into excluded docs: PRD_PROCESS "Second-Model Disposition", "Registry Maintenance", "LANE Axis", "Cosmetic Carve-Out", "Same-PR Closeout", "Lane Downgrade Prohibition", "MICRO Eligibility Safety Net"; GOV-2 s-numbers; OWNER_MERGE s2/s3 | prd-authoring :18, :46, :83, :89, :112; prd-review-claude :25, :273; closeout :26-27; scope-lock :133, :169-170; REVIEW_TEMPLATE :20 | the named headings in PRD_PROCESS.md / GOV-2 | Citation must keep the exact heading text; SILENT |
| F17 | Review-artifact structure: VERDICT / REQUIRED EDITS / RECOMMENDED EDITS / RATIONALE / DRIFT CHECK (:157) / Verification Report; REVIEW_TEMPLATE sections 1-4 (:27-82), "Review Independence" (:144), "REVIEWED STATE" (:157), "Filename convention" (:12) | prd-review-claude :115-170, :224-243; REVIEW_TEMPLATE | prd-review-claude :54, :106, :124; validator :596-607 (filename only); adjudication readers | Review artifacts drift: SILENT |
| F18 | V-row numbering (V1..V10) and "never reused" retired markers (prd-review-claude :218 V9; prd-authoring :115 V10); report-line formats | all 4 skills | historical review artifacts cite V-numbers | Renumbering rewrites history meaning: SILENT |
| F19 | CLAUDE_HOOKS.md wired-hooks table (:9-13) script names/events; inbound path refs from protect_files.sh:6, AGENT_WORKFLOW.md:13, dev_workflow.md:8, CLAUDE.md:141 | CLAUDE_HOOKS.md | .claude/settings.json:167-207 (truth) | Doc/truth divergence: SILENT |
| F20 | CLAUDE.md "Retained invariants" 1-6 (:85-93), Permissions (:95-97), Publish safety (:99-102), Session start (:148-152), Anti-patterns (:173-184): every rule sentence | CLAUDE.md | every session; MODE_STEWARD.md:21 cites publish safety | Weakening: SILENT |

Codex is asked to falsify: (a) no code/test/CI reference to any payload path or phrase exists
beyond F1-F8 (author's `rg` for instruction-doc paths over scripts tests tools cuttingboard
.github .claude/hooks workers pyproject.toml hit only: tools/validate_prd_registry.py,
tests/test_prd_registry.py, .claude/hooks/canonical_read_guard.sh +
tests/test_canonical_read_guard_hook.py, .claude/hooks/prd_eval.sh, .claude/hooks/protect_files.sh:6,
scripts/prd_open.sh + tests/test_prd_open.py (PRD_TEMPLATE, excluded), and
.github/workflows/campaign_control.yml + tests/test_campaign_control.py (charge_prompt.md,
excluded)); (b) no test asserts a heading, phrase, or line count in any payload file (author:
none found).

## 5. Preservation contract

Preserved classes: authority (wall, owner holds, precedence, modes, commission); scope (FILES
hard boundary, STOP/renewal); review (gates, slots, independence, one-cycle rule, DRIFT CHECK);
security; every fail-closed/refusal condition ("refuse", "STOP", "fail closed", "exit
non-zero"); parser/interface literals (section 4); owner-held decisions; retained invariants;
every "Does NOT do" / "Failure modes to refuse" list.

Semantic no-op, operationally: for every normative rule R in the pre-edit text (a sentence
carrying MUST / NEVER / must not / may not / only / requires / refuse / STOP / fail closed, or a
consumer-depended literal), the post-edit text either (i) contains R with equal or stronger
force in the same file, or (ii) keeps the operative instruction locally and replaces only the
restated policy/rationale with a by-name citation to a canonical source (CLAUDE.md:124-144)
that states R at a verified file:line and that the reading agent already opens on the same
trigger; AND no rule is added, no ordering/precedence changes, and every section-4 item is
byte-identical. Anything else is not a no-op and is out of scope.

Proof: a per-file pre/post NORMATIVE RULE LEDGER, produced during implementation and committed
with the PRD (this packet dir, RULE_LEDGER_PRD-347.md). Pre-edit: enumerate every rule line
(id = file:line) by `rg -n` over the operator list, then hand-add operator-less rules. Post-edit:
map each id to its new line, to "CITED -> <canonical file:line>", or to "REMOVED (class Pn,
s6)" with reason. Precedent shape: PRD-244.review.claude.md ("67/67 rules survive"). Astra
reviews the ledger itself, not the author's summary of it.

## 6. Permitted removal classes and forbidden transforms

Permitted (each logged in the ledger):
- P1 Duplicate policy: text restating a canonical source's rule -> cite by name. Example:
  prd-closeout-verified/SKILL.md:26-32 restates PRD_PROCESS Same-PR Closeout.
- P2 Historical explanation / rationale (why a rule exists, what it replaced, connector ids).
  Example: docs/CLAUDE_HOOKS.md:40-53 (PRD-254 allow-path history); scope-lock SKILL:121-130.
- P3 Ritualized procedure with no consumer (nothing read by code, test, hook, or reviewer).
  Candidate: prd-authoring SKILL:143-162 "Recon chain" narrative (the decisive-rg rule itself,
  MODE_RECON.md:26-28 / MODE_IMPLEMENT.md:35-36, stays cited).
- P4 Obsolete model handholding (retired-mechanism stories kept as reassurance). Example:
  prd-review-claude SKILL:106-110 (prd_eval retirement story; the slot-lock rule stays).
- P5 Pure formatting (blank-line runs, repeated "see above").

FORBIDDEN transforms (any one is a STOP, not a judgment call): merging two rules into one weaker
rule; MUST/NEVER -> should/prefer; dropping or softening any stop, refuse, or fail-closed
condition; replacing a section-4 literal, heading, path, or quoted phrase with a paraphrase;
moving a rule into an excluded doc or one the reading agent does not load (CLAUDE.md rule ->
AGENTS.md; skill rule -> PRD_PROCESS without a cite); changing precedence, owner holds, the
merge wall, mode list, or commission text; deleting a retired V-row instead of keeping its
one-line RETIRED marker (F18); editing any file outside the payload (no "while I am here"
consumer patches); adding new rules, pointers to non-canonical docs, or defaults.

## 7. Pre-existing defects inside the candidate surface (owner question Q2)

Dangling CLAUDE.md section references (verified absent from CLAUDE.md @ 73a13762: `rg -i
'Test-suite discipline|Strict scope locking|Working practices|Codex mechanics|grep sweep|
Visible-String' CLAUDE.md` returns nothing). Five inside candidate files (recon said four):
- D-a prd-authoring-verified/SKILL.md:115 "the CLAUDE.md pre-implementation grep sweep" ->
  current home docs/contract/MODE_IMPLEMENT.md:22-25.
- D-b scope-lock-precommit/SKILL.md:243 "CLAUDE.md `Strict scope locking`" -> CLAUDE.md:29-30
  (wall, SCOPE) + MODE_IMPLEMENT.md:17-21.
- D-c docs/PRD_MICRO_TEMPLATE.md:66 "CLAUDE.md s Test-suite discipline" (glyph in source) ->
  MODE_IMPLEMENT.md:43-48 (full suite once before review). OUT of payload unless Q2 = repoint.
- D-d docs/PRD_REVIEW_TEMPLATE.md:122-123 "CLAUDE.md s Working practices, 'Codex mechanics'" ->
  nearest current: MODE_REVIEW.md:21-26 (one findings-and-correction cycle). Exact home UNKNOWN.
- D-e docs/PRD_REVIEW_TEMPLATE.md:96-97 "CLAUDE.md `Visible-String Pre-Edit Audit`" ->
  MODE_IMPLEMENT.md:22-25 (pre-implementation grep sweep, PRD-158). Not in the recon list.
Outside payload (R3, follow-up only): docs/PRD_PROCESS.md:339-340 'CLAUDE.md "Codex mechanics"'
-> AGENTS.md:57-62. Soft, not dangling: prd-authoring :24 "review path defined in CLAUDE.md".
Options: (A) preserve as-is (pure compaction; refs stay broken); (B) repoint each to its current
canonical location, ledger-logged as "REPOINTED", with PRD_MICRO_TEMPLATE.md entering the
payload for exactly line 66. Author recommendation (non-authority): B; a citation repoint is a
no-op under s5 and the refs are already false today. D-d target to be confirmed by Astra.

## 8. Out-of-slice findings / follow-ups (NOT in payload)

- PROJECT_STATE.md:71-73 three `- **Active PRD:**` bullets; :71 claims PRD-274 held though
  merged at #345 (HEAD 73a13762); prd_close.sh and pre_commit_sanity read only the first (R6).
- CLAUDE_HOOKS.md:9-13 omits the SessionStart `scripts/dev_bootstrap.sh` hook wired at
  .claude/settings.json:207 (R6; adding a row is an addition, not compaction; see Q3).
- Dual review format: PRD_REVIEW_TEMPLATE sections 1-4 vs prd-review-claude VERDICT structure,
  the skill claiming (:124) to BE the template's Review Independence attestation (R6).
- AGENTS.md:80-82 says CI literal-matches the `SECOND-MODEL:` sentence; validator :601 matches
  only the text after the prefix (prefix unenforced). Correctness, not compaction.
- PRD_PROCESS.md:339-340 dangling "Codex mechanics" citation (s7); PRD_PROCESS.md:205-208
  "owed a follow-up edit" note on prd-review-claude: currency UNKNOWN.
- scripts/prd_open.sh:91 comment claims .claude/hooks/protect_files.sh parses A/M/D FILES lines;
  protect_files.sh contains no FILES parsing (verified). D15: tests/test_prd_open.py:102-118
  checks the scaffold against a hardcoded list, not docs/PRD_TEMPLATE.md (SILENT divergence).
- GITNEXUS.md "opt-in" vs prd-authoring :115/:143 "GitNexus removed (PRD-243)" vs
  settings.local.json enabling the MCP: three-way inconsistency. CODEX.md deletion candidate.
- session-handoff/SKILL.md:35-36 names `audits/recon-<date>/SESSION_RESUME.md` as a convention
  while CLAUDE.md:181-182 forbids session notes accumulating in audits/ (PRD-230).
- GOVERNANCE HIGH-RISK FILES set excludes AGENTS.md, docs/contract/*, AGENT_WORKFLOW.md and
  four skills: an equivalent Codex-side edit rides a lighter lane (governance question, R3).
- .codex/ hook mirror drifts silently; settings.local.json carries ~60 stale allow rules naming
  retired CLAUDE.md sections; untracked root shadow-instruction files; stale worktree copies.

## 9. Implementation verification plan (for PRD-347, after Gate A)

1. `python tools/validate_prd_registry.py` and the full pytest suite green at CI (CI parity;
   local green is unverified); report with GOV-2 s8 docs-only language.
2. No-code-diff: `git diff --name-only main` lists only payload paths (+ Stage-0 bookkeeping);
   `git diff --name-only main | grep -v '\.md$'` is empty.
3. Frozen-literal check (script committed with the ledger, run pre and post): per section-4
   literal, `rg -c` per payload file post >= pre; `grep '^#'` heading lists identical pre/post
   unless the ledger marks a heading REMOVED (none expected); `head -4` frontmatter
   byte-identical for the 4 skills; AGENT_WORKFLOW.md, PRD_TEMPLATE.md, mode files unchanged.
4. Rule ledger (s5) committed; every pre-edit id resolved; zero lost rows. Per-file line counts
   vs the Gate A ceiling; no payload file grows.
5. Astra fresh-context focus: semantic weakening (MUST->should), authority drift,
   parser/interface loss (F1-F20), fail-closed regressions, rule moved out of a load set,
   unnecessary retained ritual, D-d repoint target, ledger completeness.
6. Implementation review pinned to the exact head; second-model disposition per PRD_PROCESS
   Second-Model Disposition (artifact or the F2 sentence verbatim).

## 10. Owner questions for the design-direction ruling

- Q1 Boundary: (a) the 7-file payload as tabled; (b) add AGENTS.md with a <=10-line ceiling;
  (c) add the 5 mode files + CHARGE_TEMPLATE; (d) add CODEX.md deletion. Rec (non-authority): a.
- Q2 Dangling refs (s7): preserve (A) or repoint (B, adds PRD_MICRO_TEMPLATE.md:66 only). Rec: B.
- Q3 CLAUDE_HOOKS.md missing SessionStart row: leave as follow-up MICRO (per R6) or permit the
  one-row addition inside PRD-347 as a truth fix. Rec: follow-up MICRO, filed before PRD-347
  closes, so the compacted doc is not merged knowingly incomplete.
- Q4 Ceiling form: per-file post-edit ceilings (estimate + 10%, no growth) vs one net LOC
  ceiling. Rec: per-file, as PRD-294 used.
- Q5 CLAUDE.md Ratification SHAs (:11-17): keep verbatim (rec; invariant 6) or reduce to names.
- Q6 Retired V-rows (F18): keep one-line RETIRED markers (rec) or drop.

## 11. Review record slots (GOV-2 s2, s7)

- INITIAL PACKET REVIEW (Codex, AUTHORITY: REVIEW): PENDING. Record to be committed in this
  packet directory as CODEX_EVENT_1_REVIEW_<date>.md and linked here (reviewer identity/role,
  exact SHA, date, verdict, findings + dispositions, fresh-context/memory-provenance evidence).
- Consolidated author correction (one cycle): PENDING.
- EXACT-CORRECTED-HEAD CONFIRMATION (Codex): PENDING. CODEX_EVENT_2_CONFIRMATION_<date>.md
  naming the corrected SHA and every prior finding id + disposition.
- Design-direction ruling (Dustin): PENDING; then Stage-0 PRD-347, Astra PRD review, Gate A.
