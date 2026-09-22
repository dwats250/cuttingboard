# Prompt-Surface Compaction MATERIAL Packet (2026-09-22)

STATUS: PROVISIONAL rev 2 (one consolidated correction after Codex EVENT 1 @ bcb859bd).
NOT review-clean until the EXACT-CORRECTED-HEAD CONFIRMATION lands. Authorizes NOTHING: no
design-direction ruling, no Stage-0, no Gate A, no implementation, no merge is implied.
CLASS GOVERNANCE / LANE HIGH-RISK / MATERIAL (owner ruling R2). Reserved number: PRD-347
(NOT opened; Stage-0 waits for the design-direction ruling, R5). Base: main @ 73a13762;
branch claude/prompt-surface-compaction-packet (rev 1 = bcb859bd, Codex record = f127d33).
Seats (R4): Fable = AUTHORITY: DESIGN / Navigator (this author: provisional design and
proposed wording only). Codex = AUTHORITY: REVIEW (packet review + mechanical
parser/consumer/dependency audit; exact-corrected-head confirmation). Astra = AUTHORITY:
REVIEW, confined to the fresh-context PRD review after the ruling (no other Astra seat is
commissioned by this packet). Builder after Gate A: Opus 4.8 via Claude Code. GOV-2 s11
restricted-model identity: NOT inferred (UNKNOWN).
Non-claims: the author does NOT certify boundary completeness (GOV-2 line 14: "No agent
certifies the completeness of the boundary it chose"); author self-verification is not
independent review (GOV-2 s3). All line counts/estimates below are `ESTIMATED SURFACE -
NOT YET APPROVED` (GOV-2 s5). CI on this docs branch confirms only that the branch
preserves the current green baseline; it does not validate the proposed edits (GOV-2 s8).
GOV-2 s6 status: EVENT 1 F1 was the FIRST omitted-class discovery; section 2A below is the
one permitted complete inventory refresh. A further omitted class found at exact-head
confirmation returns this packet to DESIGN INCOMPLETE (GOV-2 s6/s7).

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
f127d33 (tree identical to 73a13762 outside this packet directory).

## 1. Objective and non-goals

Objective: a semantic-no-op compaction of the LIVE agent-facing Markdown instruction surface
that removes (a) restatements of policy whose authoritative text lives in a canonical source
(replace with a by-name citation), (b) historical explanation / rationale narrative, (c)
ritualized procedure proven to have no consumer, and (d) obsolete model handholding, while
preserving every authority, scope, review, security, fail-closed, parser/interface, and
owner-held constraint, byte-for-byte where a consumer depends on the literal (section 4).

Non-goals: no governance redesign; no change to precedence, owner holds, the merge wall, lanes,
or review gates; no edit to any code, test, tool, hook, settings, or workflow file; no rewording
of ratified or owner-authored text (R3); no seating change; no side-finding fixes (R6). Q3 and
Q6 in section 10 are contract-changing alternatives, not part of this contract.

## 2. Payload boundary (ESTIMATED SURFACE - NOT YET APPROVED)

Candidates decided deliberately. IN = payload. OUT = excluded (reason in section 3).

| File (wc -l @ HEAD) | Decision | Compaction intent (one line) | Est. post |
|---|---|---|---|
| CLAUDE.md (184) | IN | Already cut 483->184 by V1; residual: prose glosses that restate a named canonical source (e.g. :131-132 topic list duplicates PRD_PROCESS headings; :85 rationale pointer). Modest gain; every heading and rule unit frozen (A14, A15, A19). | ~165 |
| docs/CLAUDE_HOOKS.md (87) | IN | Drop pure history: :40-47 (PRD-254 allow-path story), :63-69 (PRD-243 detector retirement story). PRESERVE :48-53 (current Bash-not-covered decision), :9-13 table, :19-38, :55-61, :71-79, :81-87 (A18). | ~55 |
| .claude/skills/prd-authoring-verified/SKILL.md (180) | IN | Drop restated PRD_PROCESS policy (:83-91 lane criteria -> cite), retired-row explanation text at :115 (marker kept), shared boilerplate. PRESERVE :65-66 hard rule, :143-161 recon chain + helper thresholds (A20), V-table :106-115, report :120-133, refusals :173-180. | ~160 |
| .claude/skills/prd-closeout-verified/SKILL.md (240) | IN | Drop restated Same-PR Closeout / PRD-242 policy (:20-36 -> cite PRD_PROCESS by section); keep script contract :51-93, registry-row invariant :111-124, two-phase :126-182, V-table :162-173, report :184-199, refusals :217-240. | ~205 |
| .claude/skills/prd-review-claude/SKILL.md (288) | IN | Drop retired-mechanism narrative (e.g. :106-110 prd_eval retirement story; the slot-lock rule and refusal stay); keep stage-locked paths :99-114, review structure :115-170, two-phase :171-222, V-table :210-222, report :224-243, refusals :277-288. HIGH-RISK file. | ~240 |
| .claude/skills/scope-lock-precommit/SKILL.md (263) | IN | Drop PRD-276/277/278 narrative (:121-130 connector story, :132-140 "why the carve-out has a carve-out" rationale); keep FILES parsing :73-93, allowlist :95-115 incl. the GOVERNANCE exception :107-114, protected-set procedure :141-176, V-table :198-206, report :211-224, refusals :250-263 verbatim. | ~230 |
| docs/PRD_REVIEW_TEMPLATE.md (255) | IN | Drop PRD-120 "Why this exists" narrative (:237-249) and rationale asides; keep section order :25-82, checklist :83-108, Review Independence :144-191, REVIEWED STATE :157, Filename convention :12-13, Mapping-Table checklist :192-255, LANE literals :166-170. HIGH-RISK file. | ~210 |
| AGENTS.md (84) | OUT | Overlap with CLAUDE.md is by design: Codex loads AGENTS.md, not CLAUDE.md (:3-4), so the wall restatement cannot be replaced by a citation without moving rules out of Codex's load set (forbidden, s6). Residual gain < 10 lines. See Q1. | - |
| CODEX.md (15) | OUT | Already a 15-line pointer; the only remaining transform is deletion, a different change class. Follow-up (s8). | - |
| docs/contract/MODE_*.md (5 files, 207) + CHARGE_TEMPLATE.md (37) | OUT | Each is the binding Layer-2 session contract; the shared preamble :3-4 is load-bearing (A14); estimated gain < 15 lines total. See Q1. | - |
| docs/AGENT_WORKFLOW.md (51) | OUT | Interface file: heading + table parsed verbatim by two skills (:6-7); only :3-13 preamble is compactable (~6 lines). Not worth the parser risk. | - |
| .claude/skills/session-handoff/SKILL.md (105) | OUT | No canonical-source duplication found; gain marginal. | - |
| docs/PRD_TEMPLATE.md (68), docs/PRD_MICRO_TEMPLATE.md (81) | OUT | Shape mirrored by scripts/prd_open.sh:89-143 and the validator (D15 has no template-vs-script test: SILENT divergence). MICRO_TEMPLATE.md:66 enters ONLY if Q2 = repoint (1-line ceiling). | - |
| docs/tools/GITNEXUS.md (39) | OUT | Its status conflicts with prd-authoring :115/:143 ("GitNexus removed", PRD-243) and .claude/settings.local.json enabling the MCP; resolving that is semantic, not compaction. Follow-up. | - |
| docs/dev_workflow.md (68) | OUT | Self-scoped OPS RUNBOOK (:5-8): human recovery/push commands (:10-25), failure FAQ (:27-43), artifact-tracking check (:45-68); no authority, scope, gate, or review rule; its :6-8 pointers into payload are frozen inbound refs (A18). Gain nil. | - |

Payload total: 7 files, 1497 lines; estimated post ~1265 (about -230 lines, -15%; rev 1 said
~1245 before F4 moved CLAUDE_HOOKS :48-53 and prd-authoring :143-161 to PRESERVED). ESTIMATED
SURFACE - NOT YET APPROVED. Proposed ceiling form (Q4): no payload file grows; each file's
post-edit count <= its estimate + 10%; zero non-payload diff. NO code, test, tool, hook,
settings, or workflow file is in the payload. The GOVERNANCE HIGH-RISK FILES set
(PRD_PROCESS.md:458; validator :38-45) intersects the payload at CLAUDE.md, the prd-review-claude
skill, and docs/PRD_REVIEW_TEMPLATE.md, so LANE: HIGH-RISK is forced and CI-enforced (PRD >= 276).

## 2A. Complete instruction-surface inventory refresh (GOV-2 s6, first discovery; EVENT 1 F1)

Method (re-runnable): `git ls-files '*.md' | grep -v -E '^(docs/prd_history/|audits/|reports/|
logs/|docs/session_resume/|docs/superpowers/)' | sort` at f127d33 = 59 files (excluded groups:
prd_history 627, audits 202, session_resume 1, superpowers 1, reports/logs 0). Plus every
non-Markdown tracked file that carries agent instructions: `.github/campaign/charge_prompt.md`
(the only non-yml/json file under .github), `.claude/settings.json` (hooks/permissions, not
prose). Every file classified; nothing left unclassified.

| Class | Files | Decision |
|---|---|---|
| Payload | the 7 IN files of section 2 | IN |
| Decided OUT candidates | AGENTS.md, CODEX.md, docs/contract/{MODE_RECON,MODE_DESIGN,MODE_IMPLEMENT,MODE_REVIEW,MODE_STEWARD,CHARGE_TEMPLATE}.md, docs/AGENT_WORKFLOW.md, .claude/skills/session-handoff/SKILL.md, docs/PRD_TEMPLATE.md, docs/PRD_MICRO_TEMPLATE.md, docs/tools/GITNEXUS.md, docs/dev_workflow.md | OUT (reasons in s2) |
| R3 ratified / owner / binding plans | docs/PRD_PROCESS.md, docs/governance/*.md (3), docs/DECISIONS.md, VISION.md, docs/plans/*-v0.1.md (3) | OUT (R3) |
| Seating | docs/AGENT_SEATING.md | OUT (charge) |
| State / data (parser-bound) | docs/PROJECT_STATE.md, docs/PRD_REGISTRY.md (+ docs/prd_index.json) | OUT (s3) |
| Recon cache / engineering reference (describe the system, not agent authority) | docs/SCHEMA_MAP.md, docs/CALL_SITE_MAP.md, docs/architecture.md, docs/sidecar_doctrine.md, docs/audit_doctrine.md, docs/artifact_flow_map.md, docs/decision_quality_map.md, docs/system_logic_map.md, docs/renderer_decomposition_map.md, docs/regime_model.md, docs/trade_qualification.md, docs/universe_taxonomy.md, docs/manual_trade_journal_schema.md, docs/review_scorecard_schema.md, docs/engine_doctor.md, docs/knowledge_systems.md (:3-6 declares itself non-authoritative over runtime) | OUT (not instruction; architecture.md:287 inbound cite frozen in A14) |
| Human ops / deployment records | docs/runbook.md, workers/cuttingboard-clock/README.md, pinescripts/README.md, README.md (:137-143 human summary; path refs frozen in A2/A3) | OUT |
| Ratified owner product program (R3-analogous: owner-ratified text, never reworded by compaction) | docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md and docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md (both :4 "RATIFIED", owner Dustin; the program's s10 stop conditions bind their own governed lane, not the payload) | OUT (ratified; untouched) |
| Product / historical records | docs/product/ASTROLOGY_MODE_CONCEPT_RECORD_v0.1.md (:4 "not implementation authority"), docs/milestones/ENGINE_MILESTONE_2026-05-12.md, docs/audit/gate_recon_2026-06-12.md (2026-06-12 recon; its Codex/Claude role text is dated history), docs/session_resume/2026-07-23.md, docs/superpowers/plans/2026-08-27-*.md | OUT (history; untouched) |
| CI-bound prompt | .github/campaign/charge_prompt.md (tests/test_campaign_control.py phrase locks) | OUT (s3) |
Newly IN as a result of the refresh: none. Newly classified: docs/dev_workflow.md OUT.

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
- Everything else per the section-2 and 2A tables.

## 4. Frozen interface set (STOP if a compaction would alter one; consumer never patched)

Rule: any proposed edit that changes an item below is a STOP and a report, never a consumer
patch. Verification is by exact bytes (s9 step 3), not occurrence counts. SILENT = no red
signal. 4A = literal/structure PRESENT IN PAYLOAD (must be byte-identical pre/post). 4B =
EXTERNAL canonical literal that payload only REFERENCES (the reference text is frozen; the
literal itself lives outside the payload and is never copied or paraphrased into it).

### 4A. Present in payload

| ID | Frozen item (payload location) | Consumers (file:line) | Failure mode |
|---|---|---|---|
| A1 | Paths `CLAUDE.md`, `.claude/skills/prd-review-claude/SKILL.md`, `docs/PRD_REVIEW_TEMPLATE.md` (no rename/move) | tools/validate_prd_registry.py:38-45; tests/test_prd_registry.py:919-926, :966-972, :1012-1047 (fixture literals, stay green on a move); PRD_PROCESS.md:458, :518 | Live lane enforcement drops: SILENT |
| A2 | Skill directory names + `SKILL.md` filename (4 payload skills) | harness skill loader; .claude/settings.local.json:173 `Skill(prd-authoring-verified)`; scripts/pre_commit_sanity.sh:23, :32 (scope-lock-precommit reminder); MODE_IMPLEMENT.md:14 (prd-closeout-verified); PRD_PROCESS.md:59 (scope-lock), :189, :205, :215 (prd-review-claude); AGENT_WORKFLOW.md:5; prd-review-claude :97 -> prd-authoring-verified; tests/test_prd_open.py:104 (comment); DECISIONS.md:2853-2856; README.md:140-141 (docs/contract/) | Skill silently not loaded; permission entry, reminder, and cross-skill fallback go stale: SILENT |
| A3 | Repo-root path `CLAUDE.md` | decisive: harness loader (system-prompt injection); .claude/hooks/canonical_read_guard.sh:24-31 (compares realpaths, no existence check) + tests/test_canonical_read_guard_hook.py:46-49 (passes the constructed path; stays green if the file moves); AGENTS.md:4, :50-51; VISION.md:79-80; README.md:140 | Contract silently not injected: SILENT (test stays green) |
| A4 | YAML frontmatter `name:` / `description:` (lines 1-4) of the 4 payload skills | harness trigger matching | Trigger behavior changes: SILENT (no test) |
| A5 | Review filename forms in payload: prd-review-claude :62, :77, :99-114 (`.review.claude.md`, `.review.codex.md`, refusal regex :113); REVIEW_TEMPLATE :12-13 (`.review.claude.md`, `.review.<model>.md`), :151 | validator :596-607 (loud only when a COMPLETE HIGH-RISK PRD lacks an artifact); .claude/hooks/prd_eval.sh:58 (`.review.` exclusion); scripts/prd_close.sh:337-338 (hard-codes `${PRD_ID}.review.codex.md`, conditionally stages it); tests/test_prd_eval_hook.py:53-61, :143-156 (assert hook behavior on fixtures; stay green when only payload prose changes, so they do NOT protect payload/hook agreement) | Prose drift -> misnamed artifact -> validator red later (delayed-loud) or artifact unstaged by prd_close (SILENT) |
| A6 | Annotation forms in scope-lock :90, :108-113: `(PRD-NNN row)`, `(active PRD pointer)`, pointer/bookkeeping parentheticals | validator :86-89 `_POINTER_ANNOTATION_RE` (whole-form `PRD-NNN row` or pointer/bookkeeping word); :817-839 lane-downgrade branch; PRD_PROCESS.md:59; PRD_MICRO_TEMPLATE.md:30-31 | GOVERNANCE PRD (>= 276) with a wrong annotation: validator error (loud). Skill prose drift for any other case: SILENT |
| A7 | LANE / CLASS literals in payload: `LANE: HIGH-RISK` (prd-authoring :110; scope-lock :204; REVIEW_TEMPLATE :166), `LANE: MICRO` (scope-lock :170; REVIEW_TEMPLATE :170), `LANE: STANDARD` (REVIEW_TEMPLATE :170), "LANE header" (prd-authoring :113 V8); CLASS name `GOVERNANCE` (scope-lock :107-114, :132) - the other five CLASS names do NOT occur in payload | validator :56 `_CLASS_HEADER_RE`, :60-62 KNOWN_CLASSES, :78-79 `_LANE_HEADER_RE`/KNOWN_LANES; :788-795 (unknown CLASS -> ERROR); :817-839 (GOVERNANCE payload without HIGH-RISK -> ERROR, PRD >= 276); AGENT_WORKFLOW.md:50 | LOUD branch: a PRD declaring an unknown CLASS, or a GOVERNANCE payload PRD >= 276 with a non-HIGH-RISK lane, fails CI. SILENT/process-only branch: skill prose that steers an agent to a valid-but-wrong lane for a non-GOVERNANCE class, or a pre-276 PRD, has no validator branch |
| A8 | FILES syntax section scope-lock :73-93 (`^[AMD] <path>`; backtick list under `Modified:` / `New:`) | validator :75 `_FILE_ENTRY_RE`, :70 section-header regex; scripts/prd_open.sh:89-91; tests/test_prd_open.py:104; PRD_MICRO_TEMPLATE.md:27-33 | Zero entries -> skill stop (loud); misparse -> wrong protected-set verdict: SILENT |
| A9 | Closeout forms in closeout skill :3, :62, :80, :100, :132, :162-165: `STATUS: COMPLETE @ <hash>`, `Status: COMPLETE`, commit cell `#NNN` | validator :94-95 COMMIT_RE, :97 DOC_STATUS_RE; scripts/prd_close.sh | Misquoted form -> hand-written closeout fails CI (loud) |
| A10 | PROJECT_STATE literals quoted in payload: `- **Active PRD:**` (closeout :63, :146, :169; scope-lock :53 as `**Active PRD:**`), `none in progress` (closeout :63, :146, :169, :192), `**Next step` (closeout :88-89, :170), `Test baseline` (closeout :64, :147, :220, :232). NOTE: `**Last updated:**` is NOT in payload (scripts/prd_close.sh:208-213 only) | scripts/prd_close.sh:230-235, :253-258, :267-272; scripts/pre_commit_sanity.sh:29 | Skill quotes a wrong literal -> agent edits the wrong line: SILENT |
| A11 | AGENT_WORKFLOW references in payload: heading text `## Auto-Approval Policy` / `Auto-Approval Policy` (scope-lock :147, :157, :230, :255; prd-authoring :110); path `docs/AGENT_WORKFLOW.md` (scope-lock :146, :154, :164, :185, :204, :218, :244, :255; prd-authoring :110); fail-closed rule scope-lock :154-158, :204, :218, :255 | AGENT_WORKFLOW.md:6-7 (declares itself parsed verbatim); the protected-set verdict of every scope-lock run | Heading text changed in skill -> parse fails -> refusal (loud) ONLY while the fail-closed rule survives; dropping that rule makes it SILENT |
| A12 | Mode-contract forms: CLAUDE.md:70-74 (`AUTHORITY: <MODE>`, `docs/contract/MODE_<name>.md`, mode list RECON/DESIGN/IMPLEMENT/REVIEW/STEWARD); prd-review-claude :203 `docs/contract/MODE_REVIEW.md` | AGENTS.md:36; CHARGE_TEMPLATE.md:13, :17; the five mode filenames; MODE_REVIEW.md:37 | Mode contract not found / DRIFT CHECK basis lost: SILENT |
| A13 | Blocker vocabulary CLAUDE.md:151-152: `CI is running`, `Held for your merge`, `Held for your decision` ("used verbatim") | MODE_STEWARD.md:40; docs/plans/agent-work-charge-template-v0.1.md:175, :203-206; owner pattern-matching | SILENT |
| A14 | CLAUDE.md headings and quoted phrases cited inbound by name: "The wall" :19 (PRD_PROCESS.md:159, :573; all five MODE_*.md:3-4 "The wall, owner holds, precedence, and the common escalation block"); "Owner holds" :45 (MODE_*:3-4; AGENTS.md:47-50); "Precedence" :55 (MODE_*:3-4; CLAUDE.md:8); ESCALATION bullet :39-43 = the "common escalation block" (MODE_*:3-4; CHARGE_TEMPLATE.md:12); "Roles" :104 (PRD_PROCESS.md:137); "Retained invariants" :83 + "Publish safety" :99 (docs/architecture.md:287; MODE_STEWARD.md:21); "Context and output hygiene" :154 + phrase "Recon goes to subagents" :156 (PRD_PROCESS.md:198, :343; prd-authoring :159; AGENTS.md:51-53); "Canonical sources" :124 (workplan-v0.1:75; VISION.md:79-80) | as listed | Dangling citation: SILENT (precedent: s7 lists 6 already dangling) |
| A15 | CLAUDE.md content carriers that excluded binding docs require to exist: HELM bullet :21-26 (GOV-1 universal manual merge; OWNER_MERGE:11; doctrine-v0.1:438-439 and workplan-v0.1:76 "manual-merge-only carve-out"); plans pointer :143-144 (doctrine-v0.1:132, :437; workplan-v0.1:75, :93 "all three paths resolve from CLAUDE.md"); GOV-2 pointer :133-134 (GOV-2:334-335 ratification effect); owner-conventions pointer :135-137 + product holds :51-53 (PRODUCT_DELIVERY:11-13); harness-seat statements :118-122 (DECISIONS.md:792-797 "binding invariants live in CLAUDE.md"; AGENT_SEATING.md:4, :41); Ratification :11-17 | as listed | Binding doc's stated carrier vanishes: SILENT |
| A16 | Review-artifact structure: prd-review-claude :115-170 (fixed heading set incl. VERDICT, REQUIRED EDITS, RECOMMENDED EDITS, RATIONALE, DRIFT CHECK :157), Verification Report :224-243; REVIEW_TEMPLATE sections :25-82, Review Independence :144-191, REVIEWED STATE :157, Filename convention :12-13, Mapping-Table checklist :192-255 | prd-review-claude :54, :106, :124 (cross-file); DECISIONS.md:2853-2856 (Second-Model Disposition + DRIFT CHECK output load-bearing on HIGH-RISK closes); MODE_REVIEW.md:37; PRD_PROCESS.md:189, :215; PROJECT_STATE.md:246 (missing REVIEWED STATE treated as no review); every historical review artifact | Review artifacts drift / gate evidence unreadable: SILENT |
| A17 | V-row tables with exact ranges: prd-authoring V1-V10 (:106-115), closeout V1-V12 (:162-173), prd-review V1-V13 (:210-222), scope-lock V1-V9 (:198-206); retired markers prd-authoring V10 :115 and prd-review V9 :218 ("never reused"); Verification Report line formats (prd-authoring :120-133, closeout :184-199, prd-review :227-243, scope-lock :211-224) | historical `*.review.claude.md` artifacts cite V-numbers (prd-review :218); prd-review :97 -> prd-authoring fallback chain | Renumbering rewrites the meaning of history: SILENT |
| A18 | CLAUDE_HOOKS.md operative content: wired-hooks table :9-13; hook behavior :19-38 (incl. two-scopes rule :30-38); Bash-not-covered decision :48-53 (OPERATIVE, not history); :55-61; :71-79; :81-87 | .claude/settings.json:167-207 (truth); .claude/hooks/protect_files.sh:6 (points here for the Bash decision); AGENT_WORKFLOW.md:13; dev_workflow.md:8; CLAUDE.md:141 | Documented hook boundary changes: SILENT |
| A19 | CLAUDE.md rule blocks, every unit: wall :19-43, owner holds :45-53, precedence :55-66, modes :68-81, retained invariants :83-102, roles :104-122, canonical sources :124-144, session start :146-152, hygiene :154-169, anti-patterns :171-184 | every Claude session; MODE_*:3-4; AGENTS.md:47-53 | Weakening or scope change: SILENT |
| A20 | Operative procedure blocks in skills: prd-authoring :53-74 hard rule (incl. :65-66) + :143-161 recon chain and helper thresholds; scope-lock :73-93, :95-115, :141-176, :178-209; closeout :94-124, :126-182; prd-review :84-114, :171-222 | prd-review-claude :94-97 reuses the prd-authoring chain; each skill's own V-rows and report lines; PRD_PROCESS.md:59 (scope-lock "enforces" the declaration policy) | Verification weakened without touching a literal: SILENT |

### 4B. External canonical literals referenced by payload (reference text frozen)

| ID | External literal (where it lives) | Payload reference that must stay exact | Failure mode |
|---|---|---|---|
| B1 | `SECOND-MODEL: instrument not commissioned, merging on Claude-review + human judgment.` (PRD_PROCESS.md:285-286; validator :23-25, :601 matches the text after the prefix) - NOT present in any payload file | closeout :20-22 and prd-review :25 refer by name ("second-model disposition per PRD-242", "Second-Model Disposition"); never copy or paraphrase the sentence into payload | A paraphrase later copied into a PRD fails CI: delayed-loud |
| B2 | `## Auto-Approval Policy` heading (AGENT_WORKFLOW.md:15) and "Never auto-approve" table (:33-48) | A11 references; AGENT_WORKFLOW.md itself byte-identical to main (s9) | see A11 |
| B3 | PRD_PROCESS.md section names: "Second-Model Disposition" (prd-authoring :18; prd-review :25), "Registry Maintenance" (prd-authoring :46; prd-review :273; REVIEW_TEMPLATE :20), "LANE Axis" (prd-authoring :89, :112), "Cosmetic Carve-Out" (prd-authoring :83; scope-lock :169), "Same-PR Closeout" (closeout :26-27; CLAUDE.md:132), "Lane Downgrade Prohibition" (scope-lock :133), "CLASS/LANE matrices" and "Review Dispatch" (CLAUDE.md:131-132); GOV-2 topic names (CLAUDE.md:133-134). No payload file cites OWNER_MERGE s2/s3 (rev-1 row withdrawn) | the cited strings, exactly as written | Citation stops resolving: SILENT |
| B4 | PROJECT_STATE line forms owned by scripts/prd_close.sh:208-272 and pre_commit_sanity.sh:29 | A10 quotations | see A10 |
| B5 | Mode filenames `docs/contract/MODE_{RECON,DESIGN,IMPLEMENT,REVIEW,STEWARD}.md`; `AUTHORITY:` line form (CHARGE_TEMPLATE.md:13) | A12 | see A12 |

Codex is asked to falsify: (a) no code/test/CI reference to any payload path or phrase exists
beyond A1-A11 (author's `rg` for instruction-doc paths, skill names, and review-filename forms
over scripts tests tools cuttingboard .github .claude/hooks .claude/settings.json
.claude/settings.local.json workers pyproject.toml hit only: tools/validate_prd_registry.py,
tests/test_prd_registry.py, .claude/hooks/canonical_read_guard.sh +
tests/test_canonical_read_guard_hook.py, .claude/hooks/prd_eval.sh + tests/test_prd_eval_hook.py,
.claude/hooks/protect_files.sh:6, scripts/prd_close.sh:337, scripts/pre_commit_sanity.sh:23,:32,
.claude/settings.local.json:173 (plus stale historical allow strings :147-:401 naming retired
CLAUDE.md sections, s8), scripts/prd_open.sh + tests/test_prd_open.py (PRD_TEMPLATE, excluded),
and .github/workflows/campaign_control.yml + tests/test_campaign_control.py (charge_prompt.md,
excluded)); (b) no test asserts a heading, phrase, or line count in any payload file (author:
none found); (c) the inbound-citation sweep (`rg` by payload path and by `CLAUDE.md`/section
name over PRD_PROCESS, governance/*, plans/*, contract/*, AGENTS.md, dev_workflow, README,
VISION, architecture, AGENT_SEATING, AGENT_WORKFLOW, templates, DECISIONS, PROJECT_STATE) found
no dependency beyond A2, A3, A12-A18, B3.

## 5. Preservation contract

Preserved classes: authority (wall, owner holds, precedence, modes, commission); scope (FILES
hard boundary, STOP/renewal); review (gates, slots, independence, one-cycle rule, DRIFT CHECK);
security; every fail-closed/refusal condition ("refuse", "STOP", "fail closed", "exit
non-zero"); parser/interface literals (section 4); owner-held decisions; retained invariants;
every "Does NOT do" / "Failure modes to refuse" list; every operative procedure (A20).

Rule unit (what the ledger enumerates): (i) every sentence carrying MUST / NEVER / must not /
may not / only / requires / refuse / STOP / fail closed / "is a STOP"; (ii) every structural
unit: negation, quantifier (every / any / all / only / exactly / at least / at most), exception
or carve-out, default ("if none is named", "silence defaults to"), closed list or enumeration,
ordered row or step, trigger condition, syntax-defining example, heading, table row; (iii) every
operator-less authority or role statement (e.g. CLAUDE.md:118-122, :143-144, :3-9); (iv) every
consumer-depended literal (section 4). Operator grep is a starting aid only; the ledger is
complete when every line of the pre-edit file is either a rule unit, part of one, or logged
as non-normative with its removal class.

Semantic no-op, operationally: for every rule unit R in the pre-edit text, the post-edit text
either (i) contains R with EQUAL force and EQUAL scope in the same file (not stronger: a
narrowed permission, widened stop, or permission-turned-obligation is a semantic change), or
(ii) keeps the operative instruction locally and replaces only the restated policy/rationale
with a by-name citation to a canonical source (CLAUDE.md:124-144) that states R at a verified
file:line AND is proven loaded on the same trigger, naming the load path (system-prompt
injection for CLAUDE.md; charge `AUTHORITY:` for a mode file; the named trigger in
CLAUDE.md:78-81 for PRD_PROCESS / GOV-2 / the maps; the skill's own `Read` step for a file the
skill already opens); AND no rule unit is added, no ordering, default, exception, or scope
qualifier changes, and every section-4 item is byte-identical. Anything else is not a no-op.

Proof: a per-file pre/post NORMATIVE RULE LEDGER, produced during implementation and committed
with the PRD in this packet directory as RULE_LEDGER_PRD-347.md. Pre-edit: enumerate every rule
unit (id = file:line[:unit]) per the definition above. Post-edit: map each id to its new line,
to "CITED -> <canonical file:line> via <load path>", or to "REMOVED (class Pn, s6)" with the
reason; frozen items map to a sha256 of the extracted literal/section, equal pre and post.
Precedent shape: PRD-244.review.claude.md ("67/67 rules survive"). Who reviews the ledger is an
owner decision (Q7); this packet commissions no one for it.

## 6. Permitted removal classes and forbidden transforms

Permitted (each logged in the ledger; an example is illustrative, not pre-approved):
- P1 Duplicate policy: text restating a canonical source's rule -> cite by name. Example:
  prd-closeout-verified/SKILL.md:26-32 restates PRD_PROCESS Same-PR Closeout.
- P2 Historical explanation / rationale (why a rule existed, what it replaced, connector ids),
  with NO current-decision content. Verified examples: docs/CLAUDE_HOOKS.md:40-47 (pre-PRD-254
  allow-path history; :48-53 is a current decision and is PRESERVED, A18); scope-lock
  SKILL:121-130 (PRD-277 connector story; the annotation-obliges-fresh-context-review rule
  at :116-119 stays).
- P3 Ritualized procedure with no consumer, PROVEN: the ledger must show that no invoking
  agent, cross-reference (any file), refusal condition, fallback chain, report line, or
  V-row consumes the procedure. No example is offered; prd-authoring :143-161 is NOT P3
  (consumed by :65-66, prd-review-claude :94-97, and V4) and is PRESERVED (A20).
- P4 Obsolete model handholding (retired-mechanism stories kept as reassurance), where the
  live rule they decorate is kept. Example: prd-review-claude SKILL:106-110 (prd_eval
  retirement story; the slot-lock rule :102-104 and refusal :110, :113-114 stay).
- P5 Pure formatting (blank-line runs, repeated "see above").

FORBIDDEN transforms (any one is a STOP, not a judgment call): merging two rule units into one
weaker or wider rule; MUST/NEVER -> should/prefer, or the reverse; dropping or softening any
stop, refuse, or fail-closed condition; changing a default, exception, quantifier, or closed
list; replacing a section-4 literal, heading, path, or quoted phrase with a paraphrase; moving
a rule into an excluded doc or one the reading agent does not load on the same trigger
(CLAUDE.md rule -> AGENTS.md; skill rule -> PRD_PROCESS without a cite and load path); changing
precedence, owner holds, the merge wall, mode list, or commission text; deleting a retired
V-row instead of keeping its one-line RETIRED marker (A17); adding or removing a row in the
CLAUDE_HOOKS wired-hooks table (A18); editing any file outside the payload (no "while I am
here" consumer patches); adding new rule units, pointers to non-canonical docs, or defaults.

## 7. Pre-existing defects inside the candidate surface (owner question Q2)

Dangling CLAUDE.md section references (verified absent from CLAUDE.md @ HEAD: `rg -i
'Test-suite discipline|Strict scope locking|Working practices|Codex mechanics|grep sweep|
Visible-String|GitNexus' CLAUDE.md` returns nothing). Five inside candidate files:
- D-a prd-authoring-verified/SKILL.md:115 "the CLAUDE.md pre-implementation grep sweep" ->
  current home docs/contract/MODE_IMPLEMENT.md:22-25.
- D-b scope-lock-precommit/SKILL.md:243 "CLAUDE.md `Strict scope locking`" -> CLAUDE.md:29-30
  (wall, SCOPE) + MODE_IMPLEMENT.md:17-21.
- D-c docs/PRD_MICRO_TEMPLATE.md:66 "CLAUDE.md s Test-suite discipline" (glyph in source) ->
  MODE_IMPLEMENT.md:43-48 (full suite once before review). OUT of payload unless Q2 = repoint.
- D-d docs/PRD_REVIEW_TEMPLATE.md:122-123 "CLAUDE.md s Working practices, 'Codex mechanics'" ->
  nearest current: MODE_REVIEW.md:21-26 (one findings-and-correction cycle). Exact home UNKNOWN.
- D-e docs/PRD_REVIEW_TEMPLATE.md:96-97 "CLAUDE.md `Visible-String Pre-Edit Audit`" ->
  MODE_IMPLEMENT.md:22-25 (pre-implementation grep sweep, PRD-158).
Outside payload (R3 / state; follow-up only, NOT repaired here): docs/PRD_PROCESS.md:339-340
'CLAUDE.md "Codex mechanics"' -> AGENTS.md:57-62; docs/PROJECT_STATE.md:37-38 "CLAUDE.md s How
work lands / s Review gates" (current-state text; neither section exists). Soft, not dangling:
prd-authoring :24 "review path defined in CLAUDE.md".
Options: (A) preserve as-is (pure compaction; refs stay broken); (B) repoint each in-payload
ref to its current canonical location, ledger-logged as "REPOINTED", with PRD_MICRO_TEMPLATE.md
entering the payload for exactly line 66. Author recommendation (non-authority): B; a citation
repoint keeps the rule unit and only fixes its target, and the refs are already false today.
D-d target to be confirmed by the fresh-context PRD reviewer.

## 8. Out-of-slice findings / follow-ups (NOT in payload; none repaired by this slice)

- PROJECT_STATE.md:71-73 three `- **Active PRD:**` bullets; :71 claims PRD-274 held though
  merged at #345 (73a13762); prd_close.sh and pre_commit_sanity read only the first (R6).
- PROJECT_STATE.md:37-38 cites nonexistent CLAUDE.md sections "How work lands" / "Review
  gates" (EVENT 1 F2.9); PROJECT_STATE.md:242 "CLAUDE.md s GitNexus" sits in a historical
  PRD-243 entry. Out-of-slice debt.
- CLAUDE_HOOKS.md:9-13 omits the SessionStart `scripts/dev_bootstrap.sh` hook wired at
  .claude/settings.json:207 (R6; a row addition is outside this contract, A18; see Q3).
- Dual review format: PRD_REVIEW_TEMPLATE sections 1-4 vs prd-review-claude VERDICT structure,
  the skill claiming (:124) to BE the template's Review Independence attestation (R6).
- AGENTS.md:80-82 says CI literal-matches the `SECOND-MODEL:` sentence; validator :601 matches
  only the text after the prefix (prefix unenforced). Correctness, not compaction.
- PRD_PROCESS.md:339-340 dangling "Codex mechanics" citation (s7); PRD_PROCESS.md:205-208
  "owed a follow-up edit" note on prd-review-claude: currency UNKNOWN.
- scripts/prd_open.sh:91 comment claims .claude/hooks/protect_files.sh parses A/M/D FILES lines;
  protect_files.sh contains no FILES parsing (verified). D15: tests/test_prd_open.py:102-118
  checks the scaffold against a hardcoded list, not docs/PRD_TEMPLATE.md (SILENT divergence).
- tests/test_prd_eval_hook.py and tests/test_canonical_read_guard_hook.py exercise fixtures or
  constructed paths only; neither binds payload prose to hook behavior (A3, A5).
- scripts/prd_close.sh:337 hard-codes the `.review.codex.md` slot; a non-codex second-model
  artifact (e.g. `.review.astra.md`, precedent PRD-337) is never auto-staged.
- GITNEXUS.md "opt-in" vs prd-authoring :115/:143 "GitNexus removed (PRD-243)" vs
  settings.local.json enabling the MCP: three-way inconsistency. CODEX.md deletion candidate.
- session-handoff/SKILL.md:35-36 names `audits/recon-<date>/SESSION_RESUME.md` as a convention
  while CLAUDE.md:181-182 forbids session notes accumulating in audits/ (PRD-230).
- GOVERNANCE HIGH-RISK FILES set excludes AGENTS.md, docs/contract/*, AGENT_WORKFLOW.md and
  four skills: an equivalent Codex-side edit rides a lighter lane (governance question, R3).
- .codex/ hook mirror drifts silently; settings.local.json carries ~60 stale allow rules naming
  retired CLAUDE.md sections (:147, :150, :309); untracked root shadow-instruction files; stale
  worktree copies.

## 9. Implementation verification plan (for PRD-347, after Gate A)

1. `python tools/validate_prd_registry.py` and the full pytest suite green at CI (CI parity;
   local green is unverified); report with GOV-2 s8 docs-only language. Note: no test binds
   payload prose (A3, A5), so green CI proves baseline preservation only.
2. No-code-diff: `git diff --name-only main` lists only payload paths (+ Stage-0 bookkeeping
   and the ledger); `git diff --name-only main | grep -v '\.md$'` is empty.
3. Frozen-item check by exact bytes (script committed with the ledger, run pre and post): for
   each 4A row, extract the named line range / heading / literal from the pre-edit file and
   from the post-edit file (by content anchor, not by line number) and compare sha256; all
   equal. `head -4` frontmatter byte-identical for the 4 skills. `grep '^#'` heading lists
   identical pre/post. AGENT_WORKFLOW.md, PRD_TEMPLATE.md, mode files, AGENTS.md byte-identical
   to main. For 4B rows, the payload reference strings are extracted and hashed the same way.
4. Rule ledger (s5) committed; every pre-edit rule unit resolved; zero lost rows; every
   "CITED" row names the canonical file:line and load path.
5. Per-file line counts vs the Gate A ceiling; no payload file grows.
6. Fresh-context PRD review (Astra, R4 seat, before Gate A) focus: semantic weakening or
   widening, authority drift, parser/interface loss (A1-A20, B1-B5), fail-closed regressions,
   rule moved out of a load set, unnecessary retained ritual, D-d repoint target.
7. GOV-2-required implementation review after build, pinned to the exact head, by a
   fresh-context reviewer Dustin commissions (independent of Astra's PRD-review seat); second-
   model disposition per PRD_PROCESS Second-Model Disposition (artifact or the B1 sentence).
   Whether that reviewer also reviews the ledger is Q7.

## 10. Owner questions for the design-direction ruling

- Q1 Boundary: (a) the 7-file payload as tabled; (b) add AGENTS.md with a <=10-line ceiling;
  (c) add the 5 mode files + CHARGE_TEMPLATE; (d) add CODEX.md deletion. Rec (non-authority): a.
- Q2 Dangling refs (s7): preserve (A) or repoint (B, adds PRD_MICRO_TEMPLATE.md:66 only). Rec: B.
- Q3 CONTRACT-CHANGING ALTERNATIVE: add the missing SessionStart row to CLAUDE_HOOKS.md inside
  PRD-347. Selecting it changes the s5/s6 contract (A18 forbids table changes) and requires a
  revised packet and renewed independent review. Rec: do NOT select; file a follow-up MICRO
  before PRD-347 closes so the compacted doc is not merged knowingly incomplete.
- Q4 Ceiling form: per-file post-edit ceilings (estimate + 10%, no growth) vs one net LOC
  ceiling. Rec: per-file, as PRD-294 used.
- Q5 CLAUDE.md Ratification SHAs (:11-17): keep verbatim (rec; invariant 6) or reduce to names.
- Q6 CONTRACT-CHANGING ALTERNATIVE: drop retired V-row markers instead of keeping them.
  Selecting it changes A17/s6 and requires a revised packet and renewed independent review.
  Rec: do NOT select; keep the one-line RETIRED markers (the current contract).
- Q7 Ledger review seat (PROPOSED, uncommissioned): who reviews RULE_LEDGER_PRD-347.md: (a) the
  GOV-2-required implementation reviewer as part of that review; (b) a separately commissioned
  fresh-context reviewer; (c) Astra under a widened commission. Rec: a.

## 11. Review record slots (GOV-2 s2, s7)

- INITIAL PACKET REVIEW (Codex gpt-5.6-sol, AUTHORITY: REVIEW) @ bcb859bd: CHANGES REQUIRED,
  7 findings. Record: CODEX_EVENT_1_REVIEW_2026-09-22.md (this directory), dispositions
  appended at its end.
- Consolidated author correction (one cycle): THIS rev 2. Dispositions: F1 ACTIONED (s2A, s2);
  F2 ACTIONED (A2, A3, A5, A13-A17, s8); F3 ACTIONED (s4 rebuilt; B1, A7, A10, B3, A17);
  F4 ACTIONED (s2, s6 P2/P3, A18, A20); F5 ACTIONED (s5, s6, s9.3); F6 ACTIONED (A3, A7);
  F7 ACTIONED (header, s5, s9.6-7, Q3, Q6, Q7).
- EXACT-CORRECTED-HEAD CONFIRMATION (Codex): PENDING. CODEX_EVENT_2_CONFIRMATION_<date>.md
  naming the corrected SHA and every prior finding id + disposition. If it finds another
  omitted class, this packet returns to DESIGN INCOMPLETE (GOV-2 s6/s7).
- Design-direction ruling (Dustin): PENDING; then Stage-0 PRD-347, Astra PRD review, Gate A.

## Rev 2 change log (EVENT 1 finding -> section)

- F1 BOUNDARY-RESET -> s2A (complete inventory refresh, method + 59-file classification);
  docs/dev_workflow.md classified OUT in s2 with reason; header s6 status line.
- F2 COMPLETENESS -> A2 (settings.local.json:173, pre_commit_sanity.sh:23/:32), A5
  (prd_close.sh:337-338, test_prd_eval_hook.py), A13 (charge-template-v0.1 consumers), A14
  (five MODE_*:3-4, architecture.md:287), A15 (plans doctrine/workplan carriers, DECISIONS
  :792-797, GOV-2:334-335), A16 (DECISIONS:2853-2856), s8 (PROJECT_STATE:37-38 debt); s4
  trailer (c) records the inbound-citation re-sweep.
- F3 FACTUAL -> s4 rebuilt row-by-row from HEAD and split 4A/4B; B1 (waiver literal is
  external, not in payload), A7 (only `GOVERNANCE` occurs in payload; exact lines), A10
  (`**Last updated:**` removed), B3 ("Review Dispatch" added; OWNER_MERGE row withdrawn), A17
  (exact V-row ranges V1-V10 / V1-V12 / V1-V13 / V1-V9).
- F4 CONTRACT -> s2 intents and A18/A20 mark CLAUDE_HOOKS :48-53 and prd-authoring :143-161
  PRESERVED; s6 P2 examples replaced with verified pure-history ranges; P3 redefined to require
  proof of no consumer and offers no example.
- F5 CONTRACT -> s5 rule-unit definition (structural units, operator-less authority), equal
  force AND equal scope, load-path proof for citations; s6 forbids default/exception/quantifier
  changes; s9.3 verifies by sha256 of extracted content, not rg counts.
- F6 FACTUAL -> A3 (SILENT; harness loader decisive; test stays green); A7 split into loud
  validator branches (:788-795, :817-839) vs silent/process-only cases.
- F7 GOVERNANCE -> Q3 and Q6 marked contract-changing alternatives requiring a revised packet
  and renewed review; Astra confined to the R4 PRD-review seat (header, s9.6); ledger review
  is PROPOSED/uncommissioned (s5, Q7); GOV-2-required implementation review stated as
  independent of Astra (s9.7).
