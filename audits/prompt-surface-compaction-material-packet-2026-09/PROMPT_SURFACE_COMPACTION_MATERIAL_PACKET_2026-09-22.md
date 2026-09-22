# Prompt-Surface Compaction MATERIAL Packet (2026-09-22)

STATUS: PROVISIONAL rev 3 (narrowed claim per owner ruling R7; GOV-2 cycle 2 pending).
NOT review-clean: cycle 1 ended DESIGN INCOMPLETE (EVENT 2 @ 3224360a); a NEW bounded GOV-2
Codex cycle must run on this narrowed packet. Authorizes NOTHING: no design-direction ruling,
no Stage-0, no Gate A, no implementation, no merge is implied.
GOVERNED CLAIM (R7, verbatim): "Complete inventory and semantic-no-op compaction of
Cuttingboard's LIVE agent-facing Markdown instruction/control surface." It is NOT a claim to
enumerate every agent-control surface of every file type (see s2B for the specifically
discovered non-Markdown frozen dependencies, about which no completeness is claimed).
CLASS GOVERNANCE / LANE HIGH-RISK / MATERIAL (owner ruling R2). Reserved number: PRD-347
(NOT opened; Stage-0 waits for the design-direction ruling, R5). Base: main @ 73a13762;
branch claude/prompt-surface-compaction-packet, HEAD at authoring 98489532 (tree identical to
73a13762 outside this packet directory).
Seats (R4): Fable = AUTHORITY: DESIGN / Navigator (this author: provisional design and
proposed wording only). Codex = AUTHORITY: REVIEW (cycle-2 packet review + mechanical
parser/consumer/dependency audit; exact-corrected-head confirmation). Astra = AUTHORITY:
REVIEW, confined to the fresh-context PRD review after the ruling (no other Astra seat is
commissioned by this packet). Builder after Gate A: Opus 4.8 via Claude Code. GOV-2 s11
restricted-model identity: NOT inferred (UNKNOWN).
Non-claims: the author does NOT certify boundary completeness (GOV-2 line 14: "No agent
certifies the completeness of the boundary it chose"); author self-verification is not
independent review (GOV-2 s3). All line counts/estimates below are `ESTIMATED SURFACE -
NOT YET APPROVED` (GOV-2 s5). CI on this docs branch confirms only that the branch
preserves the current green baseline; it does not validate the proposed edits (GOV-2 s8).

## Packet history (truthful; branch history is provenance and is not rewritten)

1. rev 1 @ bcb859bd (provisional packet, GOV-2 s2 step 2).
2. Cycle-1 EVENT 1 INITIAL PACKET REVIEW (Codex gpt-5.6-sol) @ bcb859bd: CHANGES REQUIRED,
   F1-F7; record committed f127d338 (CODEX_EVENT_1_REVIEW_2026-09-22.md).
3. rev 2 @ 3224360a: the one consolidated correction (F1-F7 all ACTIONED by the author).
4. Cycle-1 EVENT 2 EXACT-CORRECTED-HEAD CONFIRMATION @ 3224360a: DESIGN INCOMPLETE (GOV-2
   s6) - a SECOND omitted class (the live non-Markdown settings / hook / bootstrap control
   surface, incl. the untracked .claude/settings.local.json) plus new defects 2-4; record
   committed 98489532 (CODEX_EVENT_2_CONFIRMATION_2026-09-22.md). F1 and F3 PARTIALLY
   RESOLVED, F2/F4-F7 RESOLVED. Cycle 1 is exhausted; EVENT 2 is NOT an exact-head
   confirmation of the narrowed claim.
5. Owner ruling R7 (2026-09-22): NARROW THE CLAIM to the Markdown surface; record the
   discovered non-Markdown controls as frozen external dependencies; start a new cycle.
6. rev 3 (this revision): narrowed claim; cycle-1 EVENT 2 defects 1-4 fixed; payload
   unchanged (exactly 7 files).
7. Cycle 2 (PENDING): independent Codex review of the narrowed packet; at most one
   consolidated correction; exact-corrected-head confirmation (s11).

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
- R7 (GOV-2 s6 narrow-the-claim, after cycle-1 EVENT 2): the governed claim is exactly the
  sentence quoted in the header; it is NOT a claim to enumerate every agent-control surface
  of every file type. Non-Markdown controls discovered during review are outside the
  compaction payload but are load-bearing EXTERNAL DEPENDENCIES that must be recorded and
  frozen against accidental semantic breakage, at minimum: .claude/settings.json,
  .claude/settings.local.json, hook-injected / model-read text,
  .claude/hooks/canonical_read_guard.sh, .claude/hooks/prd_eval.sh,
  .claude/hooks/protect_files.sh, scripts/dev_bootstrap.sh, and the non-Markdown CI /
  campaign prompt surfaces (.github/workflows/campaign_control.yml :55, :75, :143, :162
  wiring charge_prompt.md; .github/campaign/charge.schema.json). None is edited or compacted
  in this slice; their existence informs the Markdown rewrite wherever a Markdown statement
  depends on or references them; the packet makes NO completeness claim about non-Markdown
  control surfaces beyond these specifically discovered frozen dependencies. Because the
  governed claim materially changed, a NEW bounded GOV-2 Codex cycle starts; cycle-1 EVENT 2
  is not exact-head confirmation for the new claim. Known local defects are fixed before
  rev 3 is presented; the payload is NOT broadened (still exactly the 7 files); branch
  history is kept as provenance. Separately parked by the owner: a cbagent `--effort`
  tooling change made outside this slice was reverted (s8).
Also out of scope per the charge: product behavior, model seating (docs/AGENT_SEATING.md),
unrelated cleanup. Evidence base: the author's re-verification of every file:line below at
98489532.

## 1. Objective and non-goals

Objective (within the R7 governed claim): a semantic-no-op compaction of the LIVE
agent-facing Markdown instruction surface that removes (a) restatements of policy whose
authoritative text lives in a canonical source (replace with a by-name citation), (b)
historical explanation / rationale narrative, (c) ritualized procedure proven to have no
consumer, and (d) obsolete model handholding, while preserving every authority, scope,
review, security, fail-closed, parser/interface, and owner-held constraint: byte-for-byte
where a consumer depends on the literal (s4 class H), and at equal force and equal scope for
every rule unit (s4 class L, s5 ledger).

Non-goals: no governance redesign; no change to precedence, owner holds, the merge wall, lanes,
or review gates; no edit to any code, test, tool, hook, settings, or workflow file (s2B files
included); no rewording of ratified or owner-authored text (R3); no seating change; no
side-finding fixes (R6); no completeness claim about non-Markdown control surfaces (R7). Q3
and Q6 in section 10 are contract-changing alternatives, not part of this contract.

## 2. Payload boundary (ESTIMATED SURFACE - NOT YET APPROVED)

Candidates decided deliberately. IN = payload. OUT = excluded (reason in section 3).

| File (wc -l @ HEAD) | Decision | Compaction intent (one line) | Est. post |
|---|---|---|---|
| CLAUDE.md (184) | IN | Already cut 483->184 by V1; residual: prose glosses that restate a named canonical source (e.g. :131-132 topic list duplicates PRD_PROCESS headings; :85 rationale pointer). Modest gain; every heading (A14) and every rule unit (A19, ledger) preserved. | ~165 |
| docs/CLAUDE_HOOKS.md (87) | IN | Drop pure history: :40-47 (PRD-254 allow-path story), :63-69 (PRD-243 detector retirement story). PRESERVE :48-53 (current Bash-not-covered decision), :9-13 table rows, and every rule unit of :19-38, :55-61, :71-79, :81-87 (A18, s2B). | ~55 |
| .claude/skills/prd-authoring-verified/SKILL.md (180) | IN | Drop restated PRD_PROCESS policy (:83-91 lane criteria -> cite), retired-row explanation text at :115 (marker kept), shared boilerplate. PRESERVE :65-66 hard rule, :143-161 recon chain + helper thresholds (A20), V-table :106-115, report :120-133, refusals :173-180. | ~160 |
| .claude/skills/prd-closeout-verified/SKILL.md (240) | IN | Drop restated Same-PR Closeout / PRD-242 policy (:20-36 -> cite PRD_PROCESS by section); keep script contract :51-93, registry-row invariant :111-124, two-phase :126-182, V-table :162-173, report :184-199, refusals :217-240. | ~205 |
| .claude/skills/prd-review-claude/SKILL.md (288) | IN | Drop retired-mechanism narrative (e.g. :106-110 prd_eval retirement story; the slot-lock rule and refusal stay); keep stage-locked paths :99-114, review structure :115-170, two-phase :171-222, V-table :210-222, report :224-243, refusals :277-288. HIGH-RISK file. | ~240 |
| .claude/skills/scope-lock-precommit/SKILL.md (263) | IN | Drop PRD-276/277/278 narrative (:121-130 connector story, :132-140 "why the carve-out has a carve-out" rationale); keep FILES parsing :73-93, allowlist :95-115 incl. the GOVERNANCE exception :107-114, protected-set procedure :141-176, V-table :198-206, report :211-224, refusals :250-263 verbatim. | ~230 |
| docs/PRD_REVIEW_TEMPLATE.md (255) | IN | Drop PRD-120 "Why this exists" narrative (:237-249) and rationale asides; keep section order :25-82, checklist :83-108, Review Independence :144-191, REVIEWED STATE :157, Filename convention :12-16, Mapping-Table checklist :192-255, LANE literals :166-170. HIGH-RISK file. | ~210 |
| AGENTS.md (84) | OUT | Overlap with CLAUDE.md is by design: Codex loads AGENTS.md, not CLAUDE.md (:3-4), so the wall restatement cannot be replaced by a citation without moving rules out of Codex's load set (forbidden, s6). Residual gain < 10 lines. See Q1. | - |
| CODEX.md (15) | OUT | Already a 15-line pointer; the only remaining transform is deletion, a different change class. Follow-up (s8). | - |
| docs/contract/MODE_*.md (5 files, 207) + CHARGE_TEMPLATE.md (37) | OUT | Each is the binding Layer-2 session contract; the shared preamble :3-4 is load-bearing (A14); estimated gain < 15 lines total. See Q1. | - |
| docs/AGENT_WORKFLOW.md (51) | OUT | Interface file: heading + table parsed verbatim by two skills (:6-7); only :3-13 preamble is compactable (~6 lines). Not worth the parser risk. | - |
| .claude/skills/session-handoff/SKILL.md (105) | OUT | No canonical-source duplication found; gain marginal. | - |
| docs/PRD_TEMPLATE.md (68), docs/PRD_MICRO_TEMPLATE.md (81) | OUT | Shape mirrored by scripts/prd_open.sh:89-143 and the validator (D15 has no template-vs-script test: SILENT divergence). MICRO_TEMPLATE.md:66 enters ONLY if Q2 = repoint (1-line ceiling). | - |
| docs/tools/GITNEXUS.md (39) | OUT | Its status conflicts with prd-authoring :115/:143 ("GitNexus removed", PRD-243) and .claude/settings.local.json:443 enabling the MCP; resolving that is semantic, not compaction. Follow-up. | - |
| docs/dev_workflow.md (68) | OUT | Self-scoped OPS RUNBOOK (:5-8): human recovery/push commands (:10-25), failure FAQ (:27-43), artifact-tracking check (:45-68); no authority, scope, gate, or review rule; its :6-8 pointers into payload are frozen inbound refs (A18). Gain nil. | - |

Payload total: 7 files, 1497 lines; estimated post ~1265 (about -230 lines, -15%). ESTIMATED
SURFACE - NOT YET APPROVED. Proposed ceiling form (Q4): no payload file grows; each file's
post-edit count <= its estimate + 10%; zero non-payload diff. NO code, test, tool, hook,
settings, or workflow file is in the payload. The GOVERNANCE HIGH-RISK FILES set
(PRD_PROCESS.md:458; validator :38-45) intersects the payload at CLAUDE.md, the prd-review-claude
skill, and docs/PRD_REVIEW_TEMPLATE.md, so LANE: HIGH-RISK is forced and CI-enforced (PRD >= 276).

## 2A. Complete LIVE agent-facing MARKDOWN instruction-surface inventory (R7 claim; GOV-2 s6 refresh)

Claim scope: every tracked Markdown file, per R7. Non-Markdown control surfaces are NOT
inventoried here; the specifically discovered ones are frozen in s2B without a completeness
claim. Method (re-runnable, re-verified at 98489532): `git ls-files '*.md' | grep -v -E
'^(docs/prd_history/|audits/|reports/|logs/|docs/session_resume/|docs/superpowers/)' | sort`
= 59 files (excluded groups: prd_history 627, audits 202, session_resume 1, superpowers 1,
reports/logs 0; the two singletons are classified below). `.github/campaign/charge_prompt.md`
is one of the 59 Markdown files (correcting rev 2, which mislabelled it a non-Markdown
carrier); it is classified once, in the last row. Every one of the 59 is classified.

| Class | Files | Decision |
|---|---|---|
| Payload | the 7 IN files of section 2 | IN |
| Decided OUT candidates | AGENTS.md, CODEX.md, docs/contract/{MODE_RECON,MODE_DESIGN,MODE_IMPLEMENT,MODE_REVIEW,MODE_STEWARD,CHARGE_TEMPLATE}.md, docs/AGENT_WORKFLOW.md, .claude/skills/session-handoff/SKILL.md, docs/PRD_TEMPLATE.md, docs/PRD_MICRO_TEMPLATE.md, docs/tools/GITNEXUS.md, docs/dev_workflow.md | OUT (reasons in s2) |
| R3 ratified / owner / binding plans | docs/PRD_PROCESS.md, docs/governance/*.md (3), docs/DECISIONS.md, VISION.md, docs/plans/*-v0.1.md (3) | OUT (R3) |
| Seating | docs/AGENT_SEATING.md | OUT (charge) |
| State / data (parser-bound) | docs/PROJECT_STATE.md, docs/PRD_REGISTRY.md (+ docs/prd_index.json, not Markdown) | OUT (s3) |
| Recon cache / engineering reference (describe the system, not agent authority) | docs/SCHEMA_MAP.md, docs/CALL_SITE_MAP.md, docs/architecture.md, docs/sidecar_doctrine.md, docs/audit_doctrine.md, docs/artifact_flow_map.md, docs/decision_quality_map.md, docs/system_logic_map.md, docs/renderer_decomposition_map.md, docs/regime_model.md, docs/trade_qualification.md, docs/universe_taxonomy.md, docs/manual_trade_journal_schema.md, docs/review_scorecard_schema.md, docs/engine_doctor.md, docs/knowledge_systems.md (:3-6 declares itself non-authoritative over runtime) | OUT (not instruction; architecture.md:287 inbound cite frozen in A14) |
| Human ops / deployment records | docs/runbook.md, workers/cuttingboard-clock/README.md, pinescripts/README.md, README.md (:137-143 human summary; its CLAUDE.md / AGENTS.md / docs/contract/ path refs frozen in A3) | OUT |
| Ratified owner product program (R3-analogous: owner-ratified text, never reworded by compaction) | docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md and docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md (both :4 "RATIFIED", owner Dustin; the program's s10 stop conditions bind their own governed lane, not the payload) | OUT (ratified; untouched) |
| Product / historical records | docs/product/ASTROLOGY_MODE_CONCEPT_RECORD_v0.1.md (:4 "not implementation authority"), docs/milestones/ENGINE_MILESTONE_2026-05-12.md, docs/audit/gate_recon_2026-06-12.md (2026-06-12 recon; its Codex/Claude role text is dated history), docs/session_resume/2026-07-23.md, docs/superpowers/plans/2026-08-27-*.md | OUT (history; untouched) |
| CI-bound Markdown prompt | .github/campaign/charge_prompt.md (Markdown; wired by campaign_control.yml, s2B X7; phrase-locked by tests/test_campaign_control.py) | OUT (s3) |
Newly IN as a result of the refresh: none. The Markdown inventory is complete at 59.

## 2B. External non-Markdown frozen dependencies (R7; outside payload; NOT claimed complete)

These files are never edited in this slice. Rule: the Markdown rewrite may not change any
Markdown statement that these surfaces depend on, or that describes them, except where the
ledger proves the description stays exact (equal force, equal scope, same facts). Discovered
during cycle 1 and by the author's `rg` over the payload for `settings|hooks|pre_commit_sanity|
dev_bootstrap|protect_files|prd_eval|canonical_read|campaign|cuttingboard.yml`; no claim that
other non-Markdown controls do not exist.

| ID | Surface (file:line) and what it reads / injects / enforces | Payload Markdown that depends on it or describes it (file:line) | Must not break |
|---|---|---|---|
| X1 | `.claude/settings.json` (tracked): permission allow/deny lists (:1-158); hook wiring :160-213: PreToolUse Write and Edit -> `.claude/hooks/protect_files.sh` (:161-179), PreToolUse Read -> `canonical_read_guard.sh` (:180-188), UserPromptSubmit -> `prd_eval.sh` (:190-199), SessionStart `startup|resume|clear|fork` -> `scripts/dev_bootstrap.sh` timeout 300 (:201-212) | CLAUDE.md:95-97 (effective permission set = settings.json UNION settings.local.json); CLAUDE_HOOKS.md:3-5 (wiring lives in settings.json), :9-13 (wired-hooks table), :21-22 (auto-approves Write/Edit), :83-87 (allows plain `git push`, denies the three force-push forms) | The union rule and each hook description stay exact; the table keeps exactly its three rows (the SessionStart omission is known debt, s8/Q3, not repaired here) |
| X2 | `.claude/settings.local.json` (untracked, gitignored, LIVE): allow entries incl. :49 `Skill(update-config)`, :173 `Skill(prd-authoring-verified)`, :176 `Skill(schedule)`, :331 `Skill(fewer-permission-prompts)`; enabled MCP `gitnexus` :443; ~60 stale allow strings naming retired CLAUDE.md sections (:147, :150, :309) | CLAUDE.md:95-97 (union rule names this file as live); A2 skill directory name `prd-authoring-verified` | The union statement; the skill directory name |
| X3 | `.claude/hooks/canonical_read_guard.sh`: :26 realpath of repo-root `CLAUDE.md` (no existence check, :24-31); reminder texts :31-33 and :41-42; :48-58 emits `permissionDecision: allow` + model-read `additionalContext` | CLAUDE_HOOKS.md:13 (table row), :71-79 (non-blocking allow + additionalContext; PROJECT_STATE / DECISIONS / registry deliberately NOT guarded, PRD-201); A3 | Root `CLAUDE.md` path; the description of "warns; allows", of what is and is not guarded |
| X4 | `.claude/hooks/prd_eval.sh`: :33 `docs/PRD_REGISTRY.md`; :53-62 sidecar-suffix exclusion list (`.review.`, `.adjudication.md`, `.codex_prompt.md`, `.impl_notes.`, `.proposal.md`) = declared single source of truth; :102-107 emits model-read `additionalContext` (registry gap only) | CLAUDE_HOOKS.md:12, :55-61; PRD_REVIEW_TEMPLATE.md:12-16 (points at prd_eval.sh for the sidecar-suffix set instead of restating it); prd-review-claude :106-110 (keyword detector retired; slot-lock is skill-side); A5 | The "points here rather than restating" relation (never copy the suffix list into Markdown); the registry-gap-only description |
| X5 | `.claude/hooks/protect_files.sh`: :22-33 `is_protected` blocked set (`.env`, `.env.*`, `.git/*`, `*/.git/*`, `*.lock`, `.github/workflows/*`, `secrets*`); :38-39 model-read `[protect_files] BLOCKED: ...` message on stderr + `exit 1`; header :3-7 points to CLAUDE_HOOKS.md for the Bash decision | CLAUDE_HOOKS.md:11 (table row), :19-38 (unconditional block; non-protected paths pass; NARROWER than AGENT_WORKFLOW by design, PRD-230), :48-53 (matcher deliberately not extended to Bash, PRD-254); AGENT_WORKFLOW.md:9-13 (external) | The blocked-set description, "unconditional", the two-scopes rule, and the Bash decision stay exact |
| X6 | `scripts/dev_bootstrap.sh` (311 lines; SessionStart via X1): idempotent venv bootstrap; writes activation lines into `CLAUDE_ENV_FILE` (:142-161); `dev_bootstrap: FAIL [...]` messages on stderr | none: no payload Markdown describes it (CLAUDE_HOOKS.md:9-13 omits it; s8, Q3) | Nothing in payload; recorded so the rewrite does not add an undescribed claim about it (adding the row is Q3) |
| X7 | `.github/workflows/campaign_control.yml` :55, :75, :143, :162 wire `.github/campaign/charge_prompt.md` (Markdown, OUT) into the campaign Codex run; :56, :76, :144, :163 wire `charge.schema.json`; phrase/schema locks in tests/test_campaign_control.py:24-25, :822-848 | none in payload (CLAUDE.md does not mention the campaign) | Nothing in payload; recorded because charge_prompt.md is on the Markdown inventory and this binding is why it is OUT |
| X8 | `.github/campaign/charge.schema.json` (50 lines; `$id` cuttingboard-owner-charge/v1; kept in lockstep with tools/campaign_control.py by drift-guard tests) | none in payload | Nothing in payload |
| X9 | `.github/workflows/cuttingboard.yml` (workflow_dispatch only; input `mode`, default `live`, :24-32) | CLAUDE.md:99-102 ("Regenerate the dashboard" = dispatch `cuttingboard.yml`, `mode: live`; never hand-overwrite the snapshot); MODE_STEWARD.md:19-21 (external, cites CLAUDE.md publish safety) | The workflow name, the `mode: live` literal, and the never-hand-overwrite rule unit |

## 3. Exclusions with reasons

- R3 set (above). docs/governance/* are owner-authored "verbatim/faithful" records
  (PRODUCT_DELIVERY:3-7; OWNER_MERGE:3-7); rewording them would falsify that status.
- docs/AGENT_SEATING.md (seating, per the charge); generated artifacts (logs/*,
  ui/dashboard.html dirty set: never staged).
- .github/campaign/charge_prompt.md: CI-bound Codex prompt with test-locked phrases
  (tests/test_campaign_control.py); under the protected `.github/` policy set; wiring in s2B X7.
- Non-Markdown control surfaces: outside the R7 claim; the discovered ones are frozen in s2B,
  never edited. .codex/ (gitignored local hook mirror), untracked root ASTRA_EXECUTION_PLAN.md /
  OWNER_INTENT_NEXT.md (outside git), .claude/worktrees/*/CLAUDE.md (4 stale copies): not the
  working checkout's loaded surface.
- docs/PROJECT_STATE.md, docs/PRD_REGISTRY.md, docs/prd_index.json: state/data, parser-bound
  (scripts/prd_close.sh:208,230,253,267; pre_commit_sanity.sh:29; validator :98-99); PRD-347
  Stage-0 touches them only as annotated bookkeeping `(PRD-NNN row)` / `(active PRD pointer)`.
- docs/SCHEMA_MAP.md, docs/CALL_SITE_MAP.md: recon cache data, not instructions.
- Everything else per the section-2 and 2A tables.

## 4. Frozen interface set (STOP if a compaction would alter one; consumer never patched)

Rule: any proposed edit that changes an item below is a STOP and a report, never a consumer
patch. Two freeze classes, marked per row: H = extracted literal, heading line, table row,
frontmatter, path, or quoted phrase that a consumer binds to - verified byte-identical by
sha256 of the EXTRACTED unit (s9.3), never of a surrounding prose range. L = rule unit(s)
inside prose that s2 may otherwise compact - verified by the s5 ledger at equal force and
equal scope, not by hash. No row freezes a whole line range. SILENT = no red signal.
4A = present in payload. 4B = external canonical literal that payload only references.

### 4A. Present in payload

| ID | Frozen unit(s) (payload location) | Class | Consumers (file:line) | Failure mode |
|---|---|---|---|---|
| A1 | Paths `CLAUDE.md`, `.claude/skills/prd-review-claude/SKILL.md`, `docs/PRD_REVIEW_TEMPLATE.md` (no rename/move) | H | tools/validate_prd_registry.py:38-45; tests/test_prd_registry.py:919-926, :966-972, :1012-1047 (fixture literals, stay green on a move); PRD_PROCESS.md:458, :518 | Live lane enforcement drops: SILENT |
| A2 | Skill directory names + `SKILL.md` filename (4 payload skills) | H | harness skill loader; .claude/settings.local.json:173 `Skill(prd-authoring-verified)` (s2B X2); scripts/pre_commit_sanity.sh:23, :32 (scope-lock-precommit reminder); MODE_IMPLEMENT.md:14 (prd-closeout-verified); PRD_PROCESS.md:59 (scope-lock), :189, :205, :215 (prd-review-claude); AGENT_WORKFLOW.md:5; prd-review-claude :97 -> prd-authoring-verified; tests/test_prd_open.py:104 (comment); DECISIONS.md:2853-2856 | Skill silently not loaded; permission entry, reminder, and cross-skill fallback go stale: SILENT |
| A3 | Repo-root path `CLAUDE.md` | H | decisive: harness loader (system-prompt injection); .claude/hooks/canonical_read_guard.sh:24-31 (s2B X3; compares realpaths, no existence check) + tests/test_canonical_read_guard_hook.py:46-49 (passes the constructed path; stays green if the file moves); AGENTS.md:4, :50-51; VISION.md:79-80; README.md:139-142 (names CLAUDE.md, AGENTS.md, docs/contract/) | Contract silently not injected: SILENT (test stays green) |
| A4 | YAML frontmatter `name:` / `description:` (lines 1-4) of the 4 payload skills | H | harness trigger matching | Trigger behavior changes: SILENT (no test) |
| A5 | Review filename strings: prd-review-claude :62 and :77 and :103 `docs/prd_history/PRD-NNN.review.claude.md`, :105 `docs/prd_history/PRD-NNN.review.codex.md`, :64 `.review.claude.v2.md`, :113 refusal regex `PRD-<NNN>\.review\.claude(\.v\d+)?\.md`; REVIEW_TEMPLATE :12-13 `.review.claude.md`, `.review.<model>.md`, :151 `PRD-252.review.codex.md`; the pointer sentence REVIEW_TEMPLATE :13-16 to prd_eval.sh (L) | H (+L) | validator :596-607 (loud only when a COMPLETE HIGH-RISK PRD lacks an artifact); .claude/hooks/prd_eval.sh:58 (s2B X4); scripts/prd_close.sh:337-338 (hard-codes `${PRD_ID}.review.codex.md`, conditionally stages it); tests/test_prd_eval_hook.py:53-61, :143-156 (fixture-only; do NOT protect payload/hook agreement) | Prose drift -> misnamed artifact -> validator red later (delayed-loud) or artifact unstaged by prd_close (SILENT) |
| A6 | Annotation strings `(PRD-NNN row)` and `(active PRD pointer)` at scope-lock :90, :112; the words pointer / bookkeeping as annotation forms at scope-lock :108-113 | H | validator :86-89 `_POINTER_ANNOTATION_RE`; :817-839 lane-downgrade branch; PRD_PROCESS.md:59; PRD_MICRO_TEMPLATE.md:30-31 | GOVERNANCE PRD (>= 276) with a wrong annotation: validator error (loud). Skill prose drift for any other case: SILENT |
| A7 | Every LANE literal in payload (complete rg sweep at HEAD): `LANE: MICRO \| STANDARD \| HIGH-RISK` combined form (prd-authoring :95); `LANE: HIGH-RISK` (prd-authoring :110; scope-lock :167, :204; REVIEW_TEMPLATE :166); `LANE: MICRO` (scope-lock :170; REVIEW_TEMPLATE :170); `LANE: STANDARD` (REVIEW_TEMPLATE :170); report/label forms `LANE: [MICRO \| STANDARD \| HIGH-RISK]` (prd-authoring :128 V8; scope-lock :214 V3); "LANE header" rule units (prd-authoring :113 V8; scope-lock :184, :200 V3, :254 refusal); "LANE policy" (scope-lock :14, :219); "Does not auto-escalate LANE" (scope-lock :248); "CLASS/LANE matrices" (CLAUDE.md:131); `LANE Axis` cites (prd-authoring :89, :112, see B3). CLASS names: only `GOVERNANCE` occurs in payload (scope-lock :107-108, :114, :132); SIDECAR / CONSUMER / EXECUTION / CONTRACT / INFRA do NOT occur | H (literals) + L (rule units) | validator :56 `_CLASS_HEADER_RE`, :60-62 KNOWN_CLASSES, :78-79 `_LANE_HEADER_RE` / KNOWN_LANES; :788-795 (unknown CLASS -> ERROR); :817-839 (GOVERNANCE payload without HIGH-RISK -> ERROR, PRD >= 276); AGENT_WORKFLOW.md:50 | LOUD branch: a PRD declaring an unknown CLASS, or a GOVERNANCE payload PRD >= 276 with a non-HIGH-RISK lane, fails CI. SILENT/process-only branch: skill prose steering an agent to a valid-but-wrong lane for a non-GOVERNANCE class, or a pre-276 PRD, has no validator branch |
| A8 | FILES-syntax literals in scope-lock :73-93: `^[AMD] <path>` (:81), `` ^- `<path>` `` (:85), `Modified:` / `New:` (:85-87), glob rejects `*`, `?`, `[` (:89), annotation-as-comment (:90-91); plus the rule units "accept BOTH", "`D` entries authorize deletions", "if `New:` is empty or absent only `Modified:` entries apply", "zero entries -> stop and report" (:75-77, :82-83, :86-87, :92-93) | H (literals) + L (rule units) | validator :75 `_FILE_ENTRY_RE`, :70 section-header regex; scripts/prd_open.sh:89-91; tests/test_prd_open.py:104; PRD_MICRO_TEMPLATE.md:27-33 | Zero entries -> skill stop (loud); misparse -> wrong protected-set verdict: SILENT |
| A9 | Closeout form literals in closeout skill: `STATUS: COMPLETE @ <hash>` and `Status: COMPLETE` (:62, :165), commit cell `#NNN` (:3, :80, :100, :132, :162-163) | H | validator :94-95 COMMIT_RE, :97 DOC_STATUS_RE; scripts/prd_close.sh | Misquoted form -> hand-written closeout fails CI (loud) |
| A10 | PROJECT_STATE literals quoted in payload: `- **Active PRD:**` (closeout :63, :146, :169; scope-lock :53 as `**Active PRD:**`), `none in progress` (closeout :63, :146, :169, :192), `**Next step` (closeout :88-89, :170), `Test baseline` (closeout :64, :147, :220, :232). `**Last updated:**` is NOT in payload (scripts/prd_close.sh:208-213 only) | H | scripts/prd_close.sh:230-235, :253-258, :267-272; scripts/pre_commit_sanity.sh:29 | Skill quotes a wrong literal -> agent edits the wrong line: SILENT |
| A11 | Heading string `## Auto-Approval Policy` / `Auto-Approval Policy` (scope-lock :147, :157, :230, :255; prd-authoring :110) and path string `docs/AGENT_WORKFLOW.md` (scope-lock :146, :154, :164, :185, :204, :218, :244, :255; prd-authoring :110) = H; the fail-closed rule units "if unreadable, refuse all V7 checks" / "if the section cannot be located, fail closed - refuse all commits" (scope-lock :154-158, :204, :218, :255) = L | H + L | AGENT_WORKFLOW.md:6-7 (declares itself parsed verbatim); the protected-set verdict of every scope-lock run | Heading text changed in skill -> parse fails -> refusal (loud) ONLY while the fail-closed rule survives; dropping that rule makes it SILENT |
| A12 | Literals `AUTHORITY: <MODE>` (CLAUDE.md:71), `docs/contract/MODE_<name>.md` (:72), mode list `RECON, DESIGN, IMPLEMENT, REVIEW, STEWARD` (:73-74), default-mode rule unit "if none is named, the mode is RECON" (:71, L); path `docs/contract/MODE_REVIEW.md` (prd-review-claude :203) | H + L | AGENTS.md:36; CHARGE_TEMPLATE.md:13, :17; the five mode filenames; MODE_REVIEW.md:37 | Mode contract not found / DRIFT CHECK basis lost: SILENT |
| A13 | Blocker vocabulary strings `CI is running`, `Held for your merge`, `Held for your decision` and the qualifier "used verbatim" (CLAUDE.md:151-152) | H | MODE_STEWARD.md:40; docs/plans/agent-work-charge-template-v0.1.md:175, :203-206; owner pattern-matching | SILENT |
| A14 | Exact CLAUDE.md heading lines cited inbound by name: `## The wall (absolute; no charge, mode, or prompt overrides it)` :19 (PRD_PROCESS.md:159, :573; all five MODE_*.md:3-4); `## Owner holds (exclusive to Dustin; no agent issues or infers these)` :45 (MODE_*:3-4; AGENTS.md:47-50); `## Precedence (on genuine conflict between two applicable authorities, STOP)` :55 (MODE_*:3-4; CLAUDE.md:8); the ESCALATION bullet label :39 = the "common escalation block" (MODE_*:3-4; CHARGE_TEMPLATE.md:12); `## Roles` :104 (PRD_PROCESS.md:137); `## Retained invariants (bind in every mode)` :83 and the "Publish safety:" label :99 (docs/architecture.md:287; MODE_STEWARD.md:21); `## Context and output hygiene (standing behavior, every session)` :154 and the quoted phrase "Recon goes to subagents" :156 (PRD_PROCESS.md:198, :343; prd-authoring :159; AGENTS.md:51-53); `## Canonical sources (reference by name; do not duplicate)` :124 (workplan-v0.1:75; VISION.md:79-80) | H | as listed | Dangling citation: SILENT (precedent: s7 lists 6 already dangling) |
| A15 | CLAUDE.md content carriers that excluded binding docs require: the HELM rule units :21-26 (GOV-1 universal manual merge; OWNER_MERGE:11; doctrine-v0.1:438-439 and workplan-v0.1:76 "manual-merge-only carve-out") = L; path strings `docs/plans/*-v0.1.md` :143 (doctrine-v0.1:132, :437; workplan-v0.1:75, :93), `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` :133 (GOV-2:334-335), the two owner-convention paths :135-136 and `docs/governance/PRODUCT_DELIVERY_OPERATING_RULE_2026-08-06.md` :52 (PRODUCT_DELIVERY:11-13) = H; the harness-seat rule units :118-122 (DECISIONS.md:792-797; AGENT_SEATING.md:4, :41) and the product-hold list :51-53 = L; Ratification SHAs :14-16 = H (Q5) | H + L | as listed | Binding doc's stated carrier vanishes: SILENT |
| A16 | Review-artifact structure literals: in prd-review-claude :130-169 the fixed heading lines `# PRD-NNN Claude Review`, `VERDICT`, `SUMMARY`, `REQUIRED EDITS`, `RECOMMENDED EDITS`, `RATIONALE`, `IMPLEMENTATION VERDICT`, `DRIFT CHECK`, `CROSS-REVIEW NOTES (cross-review mode only)`, the verdict set `ACCEPT \| ACCEPT WITH CHANGES \| REJECT` (:133); in REVIEW_TEMPLATE the heading lines :25, :27, :39, :50, :69, :83, :133, :144, :192 and the `REVIEWED STATE` block field labels :157-160 (`Reviewed SHA:`, `Merge base:`, `Independence:`), the closed set `fresh-context \| different-model \| same-context` (:160, :164-165), `Filename convention:` :12 = H; the rule units inside those sections (e.g. "Exactly one ... MUST be stated" :164-165; "same-context is INSUFFICIENT for HIGH-RISK" :166) = L | H + L | prd-review-claude :54, :106, :124 (cross-file); DECISIONS.md:2853-2856 (Second-Model Disposition + DRIFT CHECK output load-bearing on HIGH-RISK closes); MODE_REVIEW.md:37; PRD_PROCESS.md:189, :215; PROJECT_STATE.md:246 (missing REVIEWED STATE treated as no review); every historical review artifact | Review artifacts drift / gate evidence unreadable: SILENT |
| A17 | V-row table rows as whole rows (`\| Vn \| ... \|`): prd-authoring V1-V10 (:106-115), closeout V1-V12 (:162-173), prd-review V1-V13 (:210-222), scope-lock V1-V9 (:198-206); retired markers prd-authoring V10 :115 and prd-review V9 :218 ("never reused"); Verification Report label lines (`- Vn ...:` / `- Mode:` / `- File written:` / `- Action:` / `- Commits this turn:`) at prd-authoring :121-133, closeout :185-199, prd-review :228-243, scope-lock :212-224, and the `## Verification Report` heading in each | H (rows and label lines) | historical `*.review.claude.md` artifacts cite V-numbers (prd-review :218); prd-review :97 -> prd-authoring fallback chain | Renumbering or relabelling rewrites the meaning of history: SILENT |
| A18 | CLAUDE_HOOKS.md: table rows :9-13 (header + 3 hook rows) and the script names/paths `.claude/settings.json`, `.claude/hooks/`, `scripts/install_hooks.sh`, `scripts/pre_commit_sanity.sh`, `.claude/hooks/protect_files.sh`, `docs/AGENT_WORKFLOW.md`, `tools/validate_prd_registry.py` = H; every rule unit of :15-17, :19-38, :48-53, :55-61, :71-79, :81-87 (see s2B X1, X3-X5 for the facts each must keep exact) = L | H + L | .claude/settings.json:160-213 (truth); .claude/hooks/protect_files.sh:3-7 (points here for the Bash decision); AGENT_WORKFLOW.md:13; dev_workflow.md:8; CLAUDE.md:141 | Documented hook boundary changes: SILENT |
| A19 | CLAUDE.md rule units (ledger-tracked, equal force and scope), not prose ranges: every wall bullet :21-43; every owner-hold bullet :47-53; the precedence order 1-7 and the narrow-not-widen sentence :57-66; the modes rules :70-81 incl. "exactly one mode file is the complete session contract" and "skills do not reopen"; retained invariants 1-6 :86-93, Permissions :95-97, Publish safety :99-102; role statements :106-122; each canonical-source pointer :126-144 (path strings H, descriptions L); session-start rules :148-152; hygiene rules :156-169; anti-patterns :173-184. Section headings are frozen in A14 | L (+H for paths) | every Claude session; MODE_*:3-4; AGENTS.md:47-53 | Weakening or scope change: SILENT |
| A20 | Operative procedure rule units in skills (ledger-tracked): prd-authoring :53-74 hard rule incl. :65-66 and :143-161 recon chain + helper thresholds; scope-lock :73-93 (A8), :95-115 allowlist incl. the GOVERNANCE exception :107-114, :141-176 protected-set procedure, :178-209 two-phase steps; closeout :94-124, :126-182; prd-review :84-114, :171-222 | L | prd-review-claude :94-97 reuses the prd-authoring chain; each skill's own V-rows and report lines (A17); PRD_PROCESS.md:59 (scope-lock "enforces" the declaration policy) | Verification weakened without touching a literal: SILENT |

### 4B. External canonical literals referenced by payload (reference text frozen, class H)

| ID | External literal (where it lives) | Payload reference that must stay exact | Failure mode |
|---|---|---|---|
| B1 | `SECOND-MODEL: instrument not commissioned, merging on Claude-review + human judgment.` (PRD_PROCESS.md:285-286; validator :23-25, :601 matches the text after the prefix) - NOT present in any payload file | closeout :20-22 and prd-review :25 refer by name ("second-model disposition per PRD-242", "Second-Model Disposition"); never copy or paraphrase the sentence into payload | A paraphrase later copied into a PRD fails CI: delayed-loud |
| B2 | `## Auto-Approval Policy` heading (AGENT_WORKFLOW.md:15) and "Never auto-approve" table (:33-48) | A11 references; AGENT_WORKFLOW.md itself byte-identical to main (s9) | see A11 |
| B3 | PRD_PROCESS.md section names: "Second-Model Disposition" (prd-authoring :18; prd-review :25), "Registry Maintenance" (prd-authoring :46; prd-review :273; REVIEW_TEMPLATE :20), "LANE Axis" (prd-authoring :89, :112), "Cosmetic Carve-Out" (prd-authoring :83; scope-lock :169), "Same-PR Closeout" (closeout :26-27; CLAUDE.md:132), "Lane Downgrade Prohibition" (scope-lock :133), "CLASS/LANE matrices" and "Review Dispatch" (CLAUDE.md:131-132); GOV-2 topic names (CLAUDE.md:133-134). No payload file cites OWNER_MERGE s2/s3 | the cited strings, exactly as written | Citation stops resolving: SILENT |
| B4 | PROJECT_STATE line forms owned by scripts/prd_close.sh:208-272 and pre_commit_sanity.sh:29 | A10 quotations | see A10 |
| B5 | Mode filenames `docs/contract/MODE_{RECON,DESIGN,IMPLEMENT,REVIEW,STEWARD}.md`; `AUTHORITY:` line form (CHARGE_TEMPLATE.md:13) | A12 | see A12 |
| B6 | Non-Markdown surfaces of s2B (X1-X9): hook script names, `.claude/settings.json`, `.claude/settings.local.json`, `cuttingboard.yml`, `mode: live` | the path/name strings quoted in CLAUDE.md:95-102 and CLAUDE_HOOKS.md (A18) | Description diverges from the live control: SILENT |

Codex is asked to falsify: (a) no code/test/CI reference to any payload path or phrase exists
beyond A1-A11 and s2B (author's `rg` for instruction-doc paths, skill names, and
review-filename forms over scripts tests tools cuttingboard .github .claude/hooks
.claude/settings.json .claude/settings.local.json workers pyproject.toml hit only:
tools/validate_prd_registry.py, tests/test_prd_registry.py, .claude/hooks/canonical_read_guard.sh +
tests/test_canonical_read_guard_hook.py, .claude/hooks/prd_eval.sh + tests/test_prd_eval_hook.py,
.claude/hooks/protect_files.sh:6, scripts/prd_close.sh:337, scripts/pre_commit_sanity.sh:23,:32,
.claude/settings.local.json:173 (plus stale historical allow strings :147-:401 naming retired
CLAUDE.md sections, s8), scripts/prd_open.sh + tests/test_prd_open.py (PRD_TEMPLATE, excluded),
and .github/workflows/campaign_control.yml + tests/test_campaign_control.py (charge_prompt.md,
excluded)); (b) no test asserts a heading, phrase, or line count in any payload file (author:
none found); (c) the inbound-citation sweep (`rg` by payload path and by `CLAUDE.md`/section
name over PRD_PROCESS, governance/*, plans/*, contract/*, AGENTS.md, dev_workflow, README,
VISION, architecture, AGENT_SEATING, AGENT_WORKFLOW, templates, DECISIONS, PROJECT_STATE) found
no dependency beyond A2, A3, A12-A18, B3; (d) the payload `rg` for non-Markdown control names
found no dependency beyond s2B X1-X9.

## 5. Preservation contract

Preserved classes: authority (wall, owner holds, precedence, modes, commission); scope (FILES
hard boundary, STOP/renewal); review (gates, slots, independence, one-cycle rule, DRIFT CHECK);
security; every fail-closed/refusal condition ("refuse", "STOP", "fail closed", "exit
non-zero"); parser/interface literals (section 4, class H); owner-held decisions; retained
invariants; every "Does NOT do" / "Failure modes to refuse" list; every operative procedure
(A20); every Markdown description of an s2B surface (A18, B6).

Rule unit (what the ledger enumerates): (i) every sentence carrying MUST / NEVER / must not /
may not / only / requires / refuse / STOP / fail closed / "is a STOP"; (ii) every structural
unit: negation, quantifier (every / any / all / only / exactly / at least / at most), exception
or carve-out, default ("if none is named", "silence defaults to"), closed list or enumeration,
ordered row or step, trigger condition, syntax-defining example, heading, table row; (iii) every
operator-less authority or role statement (e.g. CLAUDE.md:118-122, :143-144, :3-9); (iv) every
consumer-depended literal (section 4 class H). Operator grep is a starting aid only; the
ledger is complete when every line of the pre-edit file is either a rule unit, part of one, or
logged as non-normative with its removal class.

Semantic no-op, operationally: for every rule unit R in the pre-edit text, the post-edit text
either (i) contains R with EQUAL force and EQUAL scope in the same file (not stronger: a
narrowed permission, widened stop, or permission-turned-obligation is a semantic change), or
(ii) keeps the operative instruction locally and replaces only the restated policy/rationale
with a by-name citation to a canonical source (CLAUDE.md:124-144) that states R at a verified
file:line AND is proven loaded on the same trigger, naming the load path (system-prompt
injection for CLAUDE.md; charge `AUTHORITY:` for a mode file; the named trigger in
CLAUDE.md:78-81 for PRD_PROCESS / GOV-2 / the maps; the skill's own `Read` step for a file the
skill already opens); AND no rule unit is added, no ordering, default, exception, or scope
qualifier changes, every section-4 class-H unit is byte-identical (s9.3), and every class-L
unit is ledger-resolved. Anything else is not a no-op.

Proof: a per-file pre/post NORMATIVE RULE LEDGER, produced during implementation and committed
with the PRD in this packet directory as RULE_LEDGER_PRD-347.md. Pre-edit: enumerate every rule
unit (id = file:line[:unit]) per the definition above. Post-edit: map each id to its new line,
to "CITED -> <canonical file:line> via <load path>", or to "REMOVED (class Pn, s6)" with the
reason; class-H units map to the sha256 of the extracted unit, equal pre and post (s9.3).
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
list; replacing a section-4 class-H unit with a paraphrase; moving a rule into an excluded doc
or one the reading agent does not load on the same trigger (CLAUDE.md rule -> AGENTS.md; skill
rule -> PRD_PROCESS without a cite and load path); changing precedence, owner holds, the merge
wall, mode list, or commission text; deleting a retired V-row instead of keeping its one-line
RETIRED marker (A17); adding or removing a row in the CLAUDE_HOOKS wired-hooks table (A18);
changing any Markdown description of an s2B surface unless the ledger proves it stays exact;
editing any file outside the payload (no "while I am here" consumer or s2B patches); adding
new rule units, pointers to non-canonical docs, or defaults.

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
  gates" (cycle-1 F2.9); PROJECT_STATE.md:242 "CLAUDE.md s GitNexus" sits in a historical
  PRD-243 entry. Out-of-slice debt.
- CLAUDE_HOOKS.md:9-13 omits the SessionStart `scripts/dev_bootstrap.sh` hook wired at
  .claude/settings.json:201-211 (R6; s2B X6; a row addition is outside this contract, A18; Q3).
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
  settings.local.json:443 enabling the MCP: three-way inconsistency. CODEX.md deletion candidate.
- session-handoff/SKILL.md:35-36 names `audits/recon-<date>/SESSION_RESUME.md` as a convention
  while CLAUDE.md:181-182 forbids session notes accumulating in audits/ (PRD-230).
- GOVERNANCE HIGH-RISK FILES set excludes AGENTS.md, docs/contract/*, AGENT_WORKFLOW.md and
  four skills: an equivalent Codex-side edit rides a lighter lane (governance question, R3).
- .codex/ hook mirror drifts silently; settings.local.json carries ~60 stale allow rules naming
  retired CLAUDE.md sections (:147, :150, :309); untracked root shadow-instruction files; stale
  worktree copies.
- Non-Markdown control surfaces beyond s2B X1-X9 are not inventoried (R7); a separate slice
  would own that inventory if the owner wants one.
- cbagent --effort pass-through: parked owner finding
  (~/cuttingboard-agent-jobs/PARKED_FINDING_cbagent_effort_flag_2026-09-22.md), reverted;
  cycle-1 Codex runs used effort high via it; cycle-2 runs use the unmodified runner (config
  default).

## 9. Implementation verification plan (for PRD-347, after Gate A)

1. `python tools/validate_prd_registry.py` and the full pytest suite green at CI (CI parity;
   local green is unverified); report with GOV-2 s8 docs-only language. Note: no test binds
   payload prose (A3, A5), so green CI proves baseline preservation only.
2. No-code-diff: `git diff --name-only main` lists only payload paths (+ Stage-0 bookkeeping
   and the ledger); `git diff --name-only main | grep -v '\.md$'` is empty; every s2B file is
   byte-identical to main (`git diff --quiet main -- <path>` for X1, X3-X9; X2 is untracked and
   is not touched).
3. Class-H check by sha256 of EXTRACTED units only (script committed with the ledger, run pre
   and post): for each 4A/4B row marked H, the script extracts the named unit by its content
   anchor (the literal string, the exact heading line, the whole table row, the frontmatter
   lines 1-4, the path string) from the pre-edit and post-edit file and compares sha256; all
   equal, and each unit still present at least once. Removable prose around a unit is NOT
   hashed; it is governed by the ledger (class L). Additionally: `grep '^#'` heading lists
   identical pre/post; AGENT_WORKFLOW.md, PRD_TEMPLATE.md, mode files, AGENTS.md byte-identical
   to main.
4. Rule ledger (s5) committed; every pre-edit rule unit resolved (class L at equal force and
   scope; class H by hash); zero lost rows; every "CITED" row names the canonical file:line and
   load path; every s2B-describing rule unit (A18, B6) shows its facts unchanged.
5. Per-file line counts vs the Gate A ceiling; no payload file grows.
6. Fresh-context PRD review (Astra, R4 seat, before Gate A) focus: semantic weakening or
   widening, authority drift, parser/interface loss (A1-A20, B1-B6), s2B description drift,
   fail-closed regressions, rule moved out of a load set, unnecessary retained ritual, D-d
   repoint target.
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
- Q5 CLAUDE.md Ratification SHAs (:14-16): keep verbatim (rec; invariant 6) or reduce to names.
- Q6 CONTRACT-CHANGING ALTERNATIVE: drop retired V-row markers instead of keeping them.
  Selecting it changes A17/s6 and requires a revised packet and renewed independent review.
  Rec: do NOT select; keep the one-line RETIRED markers (the current contract).
- Q7 Ledger review seat (PROPOSED, uncommissioned): who reviews RULE_LEDGER_PRD-347.md: (a) the
  GOV-2-required implementation reviewer as part of that review; (b) a separately commissioned
  fresh-context reviewer; (c) Astra under a widened commission. Rec: a.

## 11. Review record slots (GOV-2 s2, s7)

Cycle 1 (history; exhausted):
- INITIAL PACKET REVIEW (Codex gpt-5.6-sol, AUTHORITY: REVIEW) @ bcb859bd: CHANGES REQUIRED,
  F1-F7. Record: CODEX_EVENT_1_REVIEW_2026-09-22.md (dispositions appended at its end).
- Consolidated author correction: rev 2 @ 3224360a.
- EXACT-CORRECTED-HEAD CONFIRMATION (Codex gpt-5.6-sol) @ 3224360a: DESIGN INCOMPLETE (second
  omitted class; new defects 1-4). Record: CODEX_EVENT_2_CONFIRMATION_2026-09-22.md. Not an
  exact-head confirmation of the R7-narrowed claim.
Cycle 2 (new bounded cycle on the narrowed claim, per R7):
- INITIAL PACKET REVIEW (Codex, AUTHORITY: REVIEW): PENDING. Record to be committed as
  CODEX_C2_EVENT_1_REVIEW_2026-09-22.md (reviewer identity/role, exact SHA, date, verdict,
  findings + dispositions, fresh-context/memory-provenance evidence).
- Consolidated author correction (at most one): PENDING.
- EXACT-CORRECTED-HEAD CONFIRMATION (Codex): PENDING. Record as
  CODEX_C2_EVENT_2_CONFIRMATION_2026-09-22.md naming the corrected SHA and every prior finding
  id + disposition. Another omitted class returns the packet to DESIGN INCOMPLETE (GOV-2 s6/s7).
- Design-direction ruling (Dustin): PENDING; then Stage-0 PRD-347, Astra PRD review, Gate A.

## Rev 3 change log (R7 + cycle-1 EVENT 2 defects -> section)

- Rev 2 change log (cycle-1 F1-F7 -> sections) is preserved in the committed rev 2 @ 3224360a.
- R7 NARROW THE CLAIM -> header (governed claim verbatim; STATUS rev 3; cycle 2 pending);
  "Packet history (truthful)"; owner rulings (R7 recorded); s1 objective/non-goals scoped to
  the claim; s2A retitled and re-scoped to Markdown; new s2B external non-Markdown frozen
  dependencies X1-X9 with the never-edit / description-exactness rule; B6; s3; s6 forbids s2B
  description drift; s8 (non-Markdown inventory not claimed; cbagent --effort parked line);
  s9.2 s2B files byte-identical; s11 cycle-1 history + cycle-2 slots with the C2 filenames.
- EVENT 2 defect 1 (BOUNDARY-RESET, non-Markdown class + settings.local.json) -> s2B X1-X6
  (settings.json :160-213 incl. SessionStart dev_bootstrap; settings.local.json :173 and
  :443; canonical_read_guard :26/:48-58; prd_eval :53-62/:102-107; protect_files :22-33/:38-39;
  dev_bootstrap), X7-X9 (campaign workflow + schema; cuttingboard.yml referenced by
  CLAUDE.md:99-102); s2A charge_prompt.md mislabel corrected (Markdown, classified once).
- EVENT 2 defect 2 (A7 LANE locations) -> A7 rebuilt from a complete `rg -n 'LANE'` sweep of
  the 7 payload files: adds prd-authoring :95 combined form and scope-lock :167, plus every
  other occurrence (:14, :89, :112, :113, :128, :170, :184, :200, :204, :214, :219, :248,
  :254, REVIEW_TEMPLATE :166/:170, CLAUDE.md:131).
- EVENT 2 defect 3 (A2 README cite) -> README.md:139-142 moved from A2 to A3 (it names
  CLAUDE.md / AGENTS.md / docs/contract/, not the skills); s2A README row corrected.
- EVENT 2 defect 4 (whole-range freezes vs s2 intents vs 9.3 hashes) -> s4 preamble defines
  class H (extracted unit, sha256) vs class L (rule unit, ledger); rows changed: A5 (exact
  filename strings + regex instead of :99-114), A6 (exact annotation strings), A7 (literals H
  + rule units L), A8 (five syntax literals H + four rule units L instead of the :73-93
  range), A9 (exact form literals), A11 (heading + path strings H; fail-closed rule L), A12
  (literals H; default-mode rule L), A14 (exact heading lines), A15 (path strings H; HELM,
  harness-seat, product-hold rule units L), A16 (exact heading/label lines and closed sets H;
  in-section rules L instead of whole sections), A17 (whole V-rows and report label lines H
  instead of ranges), A18 (table rows + path strings H; hook-description rule units L instead
  of whole ranges), A19 (rule units L, headings via A14; no :19-184 range), A20 (rule units
  L). s5 and s9.3 made executable accordingly (hash only extracted H units; prose by ledger).
