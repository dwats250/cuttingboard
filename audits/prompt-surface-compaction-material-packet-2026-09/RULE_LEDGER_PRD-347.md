# RULE_LEDGER_PRD-347 - prompt-surface compaction rule ledger

EVIDENCE ARTIFACT, NOT PAYLOAD (packet s5 proof carrier; PRD-347 FILES `A`). Authored by the
PRD-347 IMPLEMENT Builder (Claude Code, Opus 5.5 - owner-authorized in place of Opus 4.8 by the
2026-09-23 Builder model amendment; no other Gate A authority changed). The Builder does NOT
certify this ledger (PRD Q7): it is input to the stage-R fresh-context Codex gpt-5.6-sol review of
the exact implementation commit I, which independently verifies R2-R11, the I-stage portion of
R1, and the checker's assumptions. The embedded checker is evidence, not self-authenticating.

- PRD: `docs/prd_history/PRD-347.md` (Gate A GRANTED on 188ae139b6e8594def8f13b5d7c0e8cb06dfcf19).
- Packet: `audits/prompt-surface-compaction-material-packet-2026-09/PROMPT_SURFACE_COMPACTION_MATERIAL_PACKET_2026-09-22.md`
  at e79468a58f4a7920103711d3ccdeb1de2dc171e5 ("pN" = packet section N below). Both byte-identical at M.
- M = 05c9c0c2ff6433d0740149e1e7ff318997a03df2 (merge of PR #346); branch `implement/prd-347`.
- I = the commit that adds this file. Nothing here depends on I's SHA; every I-side number below
  was measured on the final worktree, which is byte-identical to I for the payload and this ledger.
- File codes (p4): CM CLAUDE.md, CH docs/CLAUDE_HOOKS.md, PA prd-authoring-verified, PC
  prd-closeout-verified, PR prd-review-claude, SL scope-lock-precommit, RT docs/PRD_REVIEW_TEMPLATE.md.

## 1. Stage ordering and provenance (PRD STAGES, owner stage-ordering ruling)

All times UTC, 2026-09-23. Scratch artifacts lived in the session scratchpad (never committed).

| Step | Time | Evidence |
|---|---|---|
| Worktree at M, clean (`git status` showed only the untracked hook lock `.dev_bootstrap.lock`) | 22:08Z | HEAD = origin/main = M |
| X2 before-hash captured (owner X2 ruling, absolute path) | 22:08:54Z | section 2 |
| PRE class-H manifest v0 generated from M (`git show M:<path>`) | 22:16:32Z | 558 IDs, sha256(PRE0.tsv) e63235c50390b3b13aa9ff0ab6a2779b6e4604306b7770b1a4d1082c2a24269c |
| PRE rule-unit inventory generated from M (one row per pre-edit line) | 22:16:47Z | 1497 rows, sha256 a3e536f09871017ec853c95cd1cd67b7b104749b9ff77b1e3496813de5562355; embedded as columns 1-4 of section 4.6 |
| First payload edit (CLAUDE.md; its mtime, edited once) | 22:17:56Z | after both PRE artifacts |
| Last payload edit (prd-review-claude SKILL.md mtime) | 22:24:00Z | - |
| X2 after-hash captured on the final 7-file payload worktree | 22:26:45Z | section 2 |
| Final PRE/POST manifests, checker run, ledger finalized | after 22:26:45Z | sections 5, 6 |

PRE manifest v0 vs final PRE (disclosed; C2-F2 "never silently"). The checker's literal set was
corrected twice during implementation, both times to match the packet row definitions, before
the final PRE was generated (the PRE side always reads commit M, so it is reproducible at any
time). Net 558 -> 553 IDs:
- B5: a catch-all literal `MODE_` (3 occurrences: CM:63, CM:72, PR:203) was replaced by the
  exact B5/A12 payload references. Each of those three lines stays frozen by a specific literal:
  CM:63 `docs/contract/MODE_*.md` (new, 1 ID), CM:72 `docs/contract/MODE_<name>.md` (s4C seed),
  PR:203 `docs/contract/MODE_REVIEW.md` (s4C seed). Reason: p4B B5 says the payload references
  of the mode filenames are the A12 occurrences, and p7 names `docs/contract/MODE_IMPLEMENT.md`
  as the D-b/D-e repoint target. A new reference that an authorized Q2 repoint introduces is
  therefore not an occurrence of a pre-existing frozen payload reference.
- B6: the hook-name literals were scoped to CM and CH, the payload locations p4B B6 names
  ("the path/name strings quoted in CLAUDE.md:95-102 and CLAUDE_HOOKS.md (A18)"). This dropped
  PR:107 `prd_eval.sh`, which sits inside the p6 P4 example removal (prd-review-claude
  :106-110). It also dropped RT:15 `prd_eval.sh` and `.claude/hooks/`, which stay frozen by the
  A5 literal `.claude/hooks/prd_eval.sh` (same line, same bytes).
- Every other v0 ID is in the final PRE with identical file, sha256, line, heading path and key.

## 2. External dependencies (R5, p2B)

X2 = `/home/dustin/Projects/cuttingboard/.claude/settings.local.json` (owner X2 ruling: the live
untracked file in the primary checkout; not copied, symlinked, recreated, modified, or committed;
absent from the implementation tree: `ls .claude/settings.local.json` -> No such file).

| Capture | Command | sha256 |
|---|---|---|
| before first edit (22:08:54Z) | `sha256sum /home/dustin/Projects/cuttingboard/.claude/settings.local.json` | a0fdaf721d910552561bbd99e651e3fde009c4cfb21552637692b870c07bd1e4 |
| final worktree, before I (22:26:45Z) | same | a0fdaf721d910552561bbd99e651e3fde009c4cfb21552637692b870c07bd1e4 |

Identical: R5 X2 PASS (Builder observation; verified independently at stage R). Tracked X1,
X3-X9 on the final worktree: `git diff --quiet M -- <X>` exit 0 for `.claude/settings.json`,
`.claude/hooks/canonical_read_guard.sh`, `.claude/hooks/prd_eval.sh`,
`.claude/hooks/protect_files.sh`, `scripts/dev_bootstrap.sh`,
`.github/workflows/campaign_control.yml`, `.github/campaign/charge.schema.json`,
`.github/workflows/cuttingboard.yml` (stage R re-checks as `git diff --quiet M I -- <X>`).
Payload statements describing a p2B surface: section 4.4.

## 3. Size table (R11, Q4 ceilings)

Commands (repo root): `git show M:<p> | wc -l` and `git show I:<p> | wc -l` (pre-I the I column
was measured as `wc -l <p>` on the final worktree; payload is frozen from I).

| File | M | I | Delta | Ceiling | Within |
|---|---|---|---|---|---|
| CLAUDE.md | 184 | 181 | -3 | 181 | yes |
| docs/CLAUDE_HOOKS.md | 87 | 59 | -28 | 60 | yes |
| .claude/skills/prd-authoring-verified/SKILL.md | 180 | 176 | -4 | 176 | yes |
| .claude/skills/prd-closeout-verified/SKILL.md | 240 | 225 | -15 | 225 | yes |
| .claude/skills/prd-review-claude/SKILL.md | 288 | 264 | -24 | 264 | yes |
| .claude/skills/scope-lock-precommit/SKILL.md | 263 | 253 | -10 | 253 | yes |
| docs/PRD_REVIEW_TEMPLATE.md | 255 | 231 | -24 | 231 | yes |
| Total | 1497 | 1389 | -108 | - | - |

How the 108 lines split by removal class (from section 4): P5 line-rewrap of prose with words
unchanged accounts for CM 2, PR 14 and part of CH (CH-3, CH-4, CH-5 and CH-6 rewrap kept
paragraphs to 100 columns). P5 thematic-break removal accounts for RT 12. Everything else is
P1/P2/P4 removal, logged per unit in section 4.2. The packet's s2 size estimates assumed
removals that p4 class-H freezes rule out (e.g. CM:131-132 carries CLASS/LANE matrices, Same-PR
Closeout, Cosmetic Carve-Out and Review Dispatch; PA :115 is the frozen V10 row), so several
ceilings are met with P5 rewrap. Anyone can reproduce the reflow-only claim:
`git diff --word-diff=porcelain M I -- <p>` shows no removed or added words in a hunk marked
REFLOW.

## 4. Class-L normative rule ledger (R3, R6, p5, p6)

### 4.1 Method and mapping vocabulary

The PRE rule-unit inventory lists every pre-edit line of the 7 files: kind, operator tokens (a
starting aid only, p5), and the count of class-H IDs on the line. Lines are aligned M -> final
worktree with `difflib.SequenceMatcher` (autojunk off). The result:
- 1356 lines are KEPT byte-identical and carry every rule unit on them unchanged (section 4.6
  names each line's I-line).
- 141 lines fall in 43 hunks. 13 hunks are REFLOW: whitespace-normalized text identical, P5.
  30 are CONTENT. Every content hunk is split into rule units in 4.2, and each unit maps to one of:
  - KEPT @I:n - same words, equal force and scope (a rewrap or join may change line breaks).
  - SURVIVES @I:n - the unit is a duplicate; an equal-force carrier already present in the same
    file at M survives at I:n (P1, in-file duplicate).
  - CITED -> canonical file:line via load path - the restated canonical policy was replaced by
    the by-name citation that stays at the same step; the local operative instruction is kept.
  - REPOINTED - Q2 D-b/D-e only: the reference target changes, the rule does not.
  - REMOVED (Pn) - non-operative content with its p6 class and reason.

No unit is weakened, widened, merged into a weaker or wider unit, re-ordered, or moved out of
its load set. No default, exception, quantifier, closed list, stop, refuse, or fail-closed
condition changed. No rule unit or pointer was added beyond the two Q2 repoints and the
`(per ...)` wrapper that keeps the PA registry citation grammatical.

### 4.2 Content-hunk unit ledger (M line -> I line)

CM (CLAUDE.md)
- CM-1 M:49-50 -> I:49. REFLOW P5: owner-hold bullet "every merge and every lane, without
  exception (auto-merge is not a landing path)" joined onto one line. Words identical.
- CM-2 M:77-78 -> I:76.
  - u1 "plus exactly one mode file is the complete session contract": KEPT @I:76 (A19 unit).
  - u2 "- a mode file lists only its deltas": SURVIVES @I:71-72 "lists only its deltas from this
    wall" (same paragraph). P1.
  - u3 "so Layer 1 still binds and is not restated there": SURVIVES. The Layer-1 surface is
    part of the complete session contract @I:75-76, so it binds. A mode file lists only its
    deltas @I:71-72, so Layer 1 is not restated there. Every MODE_*.md preamble :3-4 (external,
    loaded with the mode file) also states "The wall, owner holds, precedence, and the common
    escalation block still bind". P1. Nothing cites the removed wording: `rg "Layer 1 still
    binds"` outside history = CLAUDE.md:78 only at M.
- CM-3 M:175-176 -> I:173. REFLOW P5: anti-pattern "No opportunistic `runtime/` refactor..."
  joined. Words identical.
- Byte-identical at I (checked): Ratification :13-17 (A15, SHAs R9), the wall, owner holds,
  precedence, every heading (A14), Permissions (X1/X2), Publish safety (X9), roles,
  canonical-source pointers, session start (A13), hygiene, and the other anti-patterns.

CH (docs/CLAUDE_HOOKS.md; every class-H unit - table rows :9-13, paths, headings - is unchanged
per the checker)
- CH-1 M:3-5 -> I:3-4.
  - u1 "The hooks wired for this repo and what each actually does.": REMOVED (P5). A
    non-normative restatement of the H1 title and `## Wired hooks`; no rule.
  - u2 "Wiring lives in `.claude/settings.json`; scripts live in `.claude/hooks/`.": KEPT @I:3
    (X1 fact).
  - u3 "This documents the hooks that are live, not every script that has ever existed.": KEPT
    @I:3-4.
- CH-2 M:21-23 -> I:20-21.
  - u1 "This is the real backstop.": REMOVED (P1). It restates the next sentence ("the only
    thing standing between an accidental edit and a secret, env file, or CI workflow"); the
    history of the phrase is in DECISIONS.md:4348.
  - u2 "`.claude/settings.json` auto-approves `Write` and `Edit`, so this hook is the only thing
    standing between an accidental edit and a secret, env file, or CI workflow.": KEPT @I:20-21
    (X1/X5 facts exact).
- CH-3 M:25-28 -> I:21-24. KEPT: the "**What it does:**" paragraph is joined to the preceding
  paragraph (P5 paragraph join) and rewrapped. Words identical. Units kept: intercepts
  Write/Edit; protected match blocked **unconditionally** (PRD-254); no PRD, FILES entry, or
  state file can allow it through; non-protected paths pass untouched; ordinary `docs/` and
  source edits are not gated (X5 exact).
- CH-4 M:30-53 -> I:26-36.
  - u1 M:30-38 "**Protected patterns:**" paragraph: KEPT @I:26-32, rewrapped (P5). Words
    identical: hardcoded hard-block subset, see the script header for the literal list,
    deliberately NARROWER than the AGENT_WORKFLOW "Never auto-approve" table, two scopes by
    design (PRD-230), do not "sync" (X5 exact).
  - u2 M:40-46 "**Why unconditional, not PRD-gated (PRD-254):**" paragraph: REMOVED (P2). This
    is the p6 P2 verified example: the pre-PRD-254 allow-path history. Its one current-state
    clause ("the hook now blocks every protected-path match through Write/Edit, full stop")
    SURVIVES @I:22-23 ("blocked **unconditionally** ... no PRD, FILES entry, or state file can
    allow it through"). Rationale carrier: DECISIONS.md PRD-254 entries.
  - u3 M:48-49 "**The matcher is deliberately not extended to `Bash` (PRD-254, decided, not
    deferred).**": KEPT @I:34 (the Bash decision, X5; protect_files.sh:3-7 points here for it).
  - u4 M:49 "The hook catches accidents, not intent.": KEPT @I:34-35.
  - u5 M:49-51 "Nobody accidentally `sed -i`'s a protected file; a PRD that genuinely needs to
    touch one does it through Bash": KEPT @I:35-36. The current sanctioned path is unchanged.
  - u6 M:51 "today and did before this change too": REMOVED (P2, history). The present tense
    "does it through Bash" keeps the current fact.
  - u7 M:51-53 "Extending the matcher to Bash would add a knob chasing a threat model this
    project doesn't have - recorded here so a future audit doesn't re-find it as a gap.":
    REMOVED (P2). Rationale for the kept decision u3; the decision stays recorded here, so a
    future audit still finds it.
- CH-5 M:57-69 -> I:40-44.
  - u1 M:57-61 registry-gap paragraph: KEPT @I:40-43, rewrapped (P5). Words identical
    (injects context only; never blocks; single remaining job; sidecars excluded; empty unless
    a real gap). X4 exact.
  - u2 M:63 "The former keyword detectors ... were retired by PRD-243": KEPT @I:43. The
    parenthetical "(PRD-body review-mode injection, non-sequential implementation gate)" is
    REMOVED (P2, what the retired detectors were).
  - u3 M:64-66 "they had no channel discrimination and misfired on subagent task notifications
    (six times in one audited session)": REMOVED (P2). Carrier: DECISIONS.md:3400-3401.
  - u4 M:66-68 "their sequencing concern is enforced where truth is determined -
    `tools/validate_prd_registry.py` on the CI merge path (PRD-200) with same-PR closeout
    (PRD-229)": KEPT @I:43-44 with "where truth is determined -" -> "by". P1: the phrase
    restates CLAUDE.md retained invariant 5. The enforcement locus, the validator path (A18 H)
    and the PRD tags are unchanged.
  - u5 M:68-69 "The 108->143->145 exclusion-list repair chain was this detector's
    false-positive class regenerating.": REMOVED (P2). Carrier: DECISIONS.md:3401.
- CH-6 M:73-78 -> I:48-52. REFLOW P5 (canonical_read_guard paragraph). Words identical; X3 exact.
- CH-7 M:83-87 -> I:57-59.
  - u1 commit/push gating sentence: KEPT @I:57-59, rewrapped (P5). X1 exact: allows plain `git
    push`, denies the three force-push forms outright, other mutating commands prompt.
  - u2 "(An older `git_gate.sh` "APPROVE COMMIT" hook was retired as redundant with this.)":
    REMOVED (P2). Carrier: DECISIONS.md:4339.
- The wired-hooks table (A18) is byte-identical, keeps exactly its 3 rows, and adds no
  SessionStart row (Q3 not selected).

PA (prd-authoring-verified)
- PA-1 M:45-48 -> I:44-46.
  - u1 "Do NOT edit `docs/PRD_REGISTRY.md` unless the user has explicitly stated implementation
    is starting in this same session": KEPT @I:43-45.
  - u2 citation `docs/PRD_PROCESS.md § Registry Maintenance`: KEPT @I:45-46 as "(per
    `docs/PRD_PROCESS.md § Registry Maintenance`)". B3 literal cardinality unchanged.
  - u3 quoted sentence "Add a row to PRD_REGISTRY.md with status IN PROGRESS before
    implementation begins.": CITED -> docs/PRD_PROCESS.md:62 (the verbatim source). Load
    path: the by-name citation stays at the same WRITE_MODE step (a named trigger, CLAUDE.md
    Modes "other canonical docs open only on a named trigger"). In-file: V9 row @I:110
    (byte-identical) keeps "moving to IN PROGRESS now". P1.
- PA-2 M:83-87 -> I:81-83.
  - u1 "Cosmetic (PRD-229 Cosmetic Carve-Out, `docs/PRD_PROCESS.md`)" template-choice
    trigger: KEPT @I:81 (B3 literal unchanged).
  - u2 criteria gloss "ui copy / CSS / layout, or comment/docstring-only edits, touching no R12
    behavior surface": CITED -> docs/PRD_PROCESS.md:601-611 (Cosmetic Carve-Out definition),
    via the by-name citation at the same step. It also SURVIVES in-file, byte-identical: V5 row
    @I:106 (ui copy/CSS/layout in presentation code, or comment/docstring-only i.e. zero
    executable-line delta; no R12 surface) and V7 row @I:108. P1.
  - u3 "-> a <=10-line MICRO note (GOAL + FILES + one FAIL line), no template; batch into the
    weekly polish PRD when one is running": KEPT @I:81-83.
- D-a (PA V10 row, M:115 -> I:111) is byte-identical (A17 H-ID; R7).

PC (prd-closeout-verified)
- PC-1 M:20-22 -> I:20-21.
  - u1 "second-model disposition per PRD-242": KEPT @I:20-21.
  - u2 "- the registry validator enforces artifact-or-sentence for HIGH-RISK closes at CI":
    CITED -> docs/PRD_PROCESS.md:287-288 ("`tools/validate_prd_registry.py` enforces this on the
    CI merge path: a HIGH-RISK close carrying neither fails the required `test` check"). Load
    path: the "per PRD-242" citation stays (PRD_PROCESS "## Second-Model Disposition (PRD-242)",
    listed in CLAUDE.md canonical sources). P1. It describes CI, not a skill step.
- PC-2 M:26-36 -> I:25-29.
  - u1 "Closeout is the *last* step of the implementation PR (PRD-229 Same-PR\nCloseout,
    `docs/PRD_PROCESS.md`)": KEPT @I:25-26. The two-line B3 occurrence "Same-PR\nCloseout"
    keeps its bytes (H-B3-PC-001).
  - u2 "implementation commits are on the branch, the PR is open (so its number exists), and
    the closeout commit is pushed into that same PR before merge": CITED ->
    docs/PRD_PROCESS.md:63 (Registry Maintenance step 2: once the PR is open, push the closeout
    commit into it before merge) and :66-70 (Same-PR Closeout), via the by-name citation at
    the same step. It also SURVIVES in-file: preflight 1a/1b @I:115-121 (same-PR mode requires
    an OPEN PR numbered NNN and a branch commit naming PRD-<NNN>) and input `hash` @I:66-69. P1.
  - u3 "If the implementation commits have not landed on the branch yet, refuse and direct the
    user to land them first.": KEPT @I:26-27.
  - u4 "Hex-hash mode (closing out after a hand-merge, recording the merge SHA) remains
    supported for that flow only.": KEPT @I:28-29.
  - u5 M:34-35 "Dashboard/UI artifact refresh, if required by the PRD, must be completed before
    closeout.": SURVIVES @I:206-207. The same sentence was already at M:221-222. P1.
  - u6 M:35-36 "This skill does not detect or perform UI refreshes.": merged into the
    pre-existing Does-NOT-do item @I:206 (see PC-7). P1.
- PC-3 M:59-61 -> I:52-54, and PC-4 M:65-71 -> I:58.
  - u1 "As of PRD-164": REMOVED (P2, provenance).
  - u2 "the script produces a **complete single-commit closeout**: it flips ... sets both
    PRD-doc status markers ... resets the bulleted `- **Active PRD:**` line to `none in
    progress`, updates the `Test baseline` line, and prepends a `## Recent ships` row": KEPT
    @I:52-58. Every A9/A10 literal is kept (checker).
  - u3 "(PRD-183 realigned these edits to the new PROJECT_STATE format)": REMOVED (P2).
  - u4 "No separate "registry/state fixup" commit is required.": SURVIVES @I:134 ("There is no
    second "fixup" commit."). P1.
  - u5 "Phase 2 then verifies the script's output.": KEPT @I:58.
  - u6 M:69-71 "Push to `origin` is intentionally out of scope. If the user wants the closeout
    pushed, they perform `git push` themselves after the skill returns.": SURVIVES @I:22-23
    ("Pushing to `origin` - push is a separate, explicit human/agent action outside this
    skill"), @I:208-209 ("Does not push to `origin`. Push is a separate, explicit action the user
    performs after this skill returns.") and refusal @I:225 ("User asks the skill to push:
    refuse; push is out of scope."). P1.
- PC-5 M:86-87 -> I:73.
  - u1 "`summary` - one-paragraph what + why; recorded in the closeout commit body": KEPT @I:73
    (V7 row unchanged).
  - u2 "(the new PROJECT_STATE format has no prose summary line)": REMOVED (P2, rationale).
- PC-6 M:117-120 -> I:103-105.
  - u1 "stop and report", "Resolve it manually before re-invoking", "Silent creation of a
    missing row during closeout ... is forbidden.": KEPT @I:103-105.
  - u2 "would mask a deeper bookkeeping break (implementation started without registering the
    PRD)": REMOVED (P2, rationale).
- PC-7 M:221-222 -> I:206-207. The Does-NOT-do item "Does not refresh dashboard/UI artifacts.
  Dashboard/UI artifact refresh, if required by the PRD, must be completed before closeout."
  becomes "Does not detect or perform dashboard/UI artifact refreshes. Dashboard/UI artifact
  refresh, if required by the PRD, must be completed before closeout." This is the union of
  M:221-222 and M:35-36 (PC-2 u5/u6): refresh = perform, plus detect. Equal force and scope,
  same list position (item 3).

PR (prd-review-claude)
- PR-1 M:12-16 -> I:12-14.
  - u1 Generate + AGREE/DISAGREE/EXTEND on the prior review's REQUIRED findings as adjudication
    input for Dustin, not a review of its prose, per GOV-1: KEPT @I:12-14, rewrapped.
  - u2 quoted gloss "reviews target the change, never another review's prose": CITED ->
    docs/PRD_PROCESS.md:199-201 ("A review targets the change - the diff and the PRD - never
    another review's prose"), via the "per GOV-1" citation kept at the same step. It also
    SURVIVES in-file: frontmatter description (A4, byte-identical) "never a review of its prose,
    per GOV-1" and Phase 1 step 3 @I:163-164 "do not review its prose (GOV-1)". P1.
- PR-2 M:32-38 -> I:30-33.
  - u1 input-envelope sentences (receives only: artifact, exact SHA, neutral question,
    canonical authority; no author conclusion, acceptance list, or prior verdict as presumed
    truth): KEPT @I:30-33, rewrapped.
  - u2 "Where a prior second-model review coexists, its REQUIRED findings are enumerated for
    AGREE/DISAGREE/EXTEND (adjudication input), never reviewed as prose.": SURVIVES @I:12-14
    (scope item 1), @I:163-165 (Phase 1 step 3), @I:63-65 (input `mode`: "treating no prior
    verdict as presumed truth") and the frontmatter. P1.
- PR-10 M:105-110 -> I:91-93.
  - u1 Codex slot path + "per `docs/PRD_REVIEW_TEMPLATE.md`'s Filename convention": KEPT @I:91-92.
  - u2 "The `prd_eval.sh` keyword detector that once enforced this hook-side was retired by
    PRD-243 (retired, not fictional -": REMOVED (P4). This is the p6 P4 example
    (prd-review-claude SKILL:106-110); the slot-lock rule and refusal stay.
  - u3 "the slot-lock rule itself still stands as skill-side discipline, just not
    hook-enforced since": KEPT @I:92 as "the slot-lock is skill-side discipline, not
    hook-enforced". Equal: the rule stands and is enforced by the skill, not a hook. This keeps
    the X4 fact.
  - u4 "The skill refuses to write here even if explicitly asked.": KEPT @I:92-93.
- PR-11 M:176-182 -> I:159-162.
  - u1 capture REVIEWED STATE; merge base from THAT SAME SHA; never hardcode `HEAD` once the
    reviewed SHA is known: KEPT @I:159-162, rewrapped.
  - u2 "or a review of a non-checked-out ref silently pairs one commit's SHA with a different
    commit's merge base": REMOVED (P2, rationale). The rule is u1, and V12 @I:198 is
    byte-identical.
  - u3 "Record the independence line the dispatch specifies.": KEPT @I:162.
- PR-3..PR-9, PR-12, PR-13 are REFLOW P5 (words identical). They are listed in 4.6.
  "Does NOT do" items: none removed (the list keeps all 7 items, in order).

SL (scope-lock-precommit)
- SL-1 M:121-131 -> (none). REMOVED (P2). This is the p6 P2 verified example (PRD-277
  connector story). Units: u1 "Verifying the claim against staged hunks IS the right fix and
  is not abandoned - PRD-277.review.fable.md item 4 upholds it, and the precedent already
  exists in V7's cosmetic carve-out" (history/intent); u2 "attempted here as prose and
  reverted (connector 3689272946)" plus the reason a prose-only check is not a check (history
  and rationale); u3 "Re-scheduled as a PRD-278 requirement ..." (roadmap history); M:131
  blank (P5). The live rule the story decorated, "Using any of those annotations obliges ONE
  `fresh-context` structured review regardless of lane ... that review is what does.", is
  byte-identical @I:116-119. The "Why the carve-out has a carve-out" paragraph (M:132-139,
  carrying the class-H `GOVERNANCE` and `Lane Downgrade Prohibition`) is byte-identical @I:121-128.
- SL-2 M:243 -> I:232-233: D-b REPOINTED (section 4.3).

RT (docs/PRD_REVIEW_TEMPLATE.md)
- RT-1, RT-2, RT-4, RT-6, RT-7, RT-8 (M:23-24, :81-82, :108-109, :125-126, :142-143,
  :190-191): the six `---` thematic breaks, each with its following blank line. REMOVED (P5,
  pure formatting). The heading lines, section order and fences are unchanged (checker).
- RT-3 M:95-99 -> I:91-95: D-e REPOINTED (section 4.3). The checklist item's rule text is
  otherwise unchanged; its lines rewrap within the item.
- RT-5 M:117-119 -> I:111.
  - u1 "Review artifact length budget: ~400 lines.": KEPT @I:111.
  - u2 "Anything longer means the review is duplicating PRD content or producing prose where a
    bullet would suffice.": REMOVED (P2, rationale for the kept budget).
- RT-9 M:237-246 -> (none). "Why this exists: PRD-120's Trend Structure mapping ..." plus
  blank: REMOVED (P2). This is the p2 RT intent: a historical incident narrative. Every
  sub-check rule @I:197-221 and the not-applicable form @I:223-231 are byte-identical.
- D-d (M:122-123 -> I:114-115, "(see CLAUDE.md § Working practices, "Codex mechanics")") is
  byte-identical (R7).

### 4.3 Repoints (R7, Q2) and unchanged D-a/D-c/D-d

- D-b SL M:243 -> I:232-233: "(per CLAUDE.md `Strict scope locking`)" -> "(per CLAUDE.md The
  wall, SCOPE, and `docs/contract/MODE_IMPLEMENT.md` Scope discipline)". These carriers are the
  ones p7 names (CLAUDE.md:29-30 wall SCOPE; MODE_IMPLEMENT.md:17-21). At I: CLAUDE.md:29-30
  "SCOPE. The active FILES/scope is a hard boundary. Crossing it requires STOP and authority
  renewal, never silent expansion." and MODE_IMPLEMENT.md:16-21 "## Scope discipline - FILES is
  a hard boundary. A change that needs an unlisted file is a STOP: before Gate A, amend the PRD
  ... Never expand FILES silently." The skill's own rule ("the user amends the PRD first, then
  re-runs this skill") is unchanged; only its reference target changed.
- D-e RT M:96-97 -> I:92-93: "per CLAUDE.md `Visible-String Pre-Edit Audit`" -> "per
  `docs/contract/MODE_IMPLEMENT.md` Pre-implementation grep sweep". This is the carrier p7
  names (MODE_IMPLEMENT.md:22-25: "Pre-implementation grep sweep (PRD-158): ... grep all of
  `tests/` for the token and add every asserting test file to FILES up front"). The checklist
  rule is unchanged.
- D-a (PA V10 row), D-c (docs/PRD_MICRO_TEMPLATE.md:66, file untouched: `git diff --quiet M --
  docs/PRD_MICRO_TEMPLATE.md` exit 0) and D-d (RT "Codex mechanics") are byte-identical to M.

### 4.4 Payload statements describing a p2B surface (R5 third clause, A18, B6)

| Surface | Statement(s) at I | Status |
|---|---|---|
| X1 settings.json | CM:93-95 union rule; CH:3 wiring; CH:8-12 table; CH:20 auto-approves Write/Edit; CH:57-59 push allow/deny | byte-identical, or same words rewrapped (CH-2 u2, CH-7 u1) |
| X2 settings.local.json | CM:93-95 union rule; skill dir name `prd-authoring-verified` | byte-identical (A2 H-IDs) |
| X3 canonical_read_guard.sh | CH:12 table row; CH:48-53 | row byte-identical; paragraph same words (CH-6) |
| X4 prd_eval.sh | CH:11 row; CH:40-44 (registry-gap only); RT:12-18 pointer sentence; PR:92 slot-lock skill-side | row and RT byte-identical; CH-5 u1/u2/u4 kept; PR-10 u3 equal |
| X5 protect_files.sh | CH:10 row; CH:20-36 (unconditional; non-protected pass; NARROWER; two scopes; Bash decision) | row byte-identical; units kept (CH-2..CH-4) |
| X6 dev_bootstrap.sh | none (no row added; Q3 not selected) | unchanged |
| X7/X8 campaign | none in payload | unchanged |
| X9 cuttingboard.yml | CM:97-100 publish safety | byte-identical |

### 4.5 R8, R9, R10

- R8: headings are identical PRE/POST in every file (checker `grep '^#'` check), so every A14
  heading and in-payload section name resolves. B3/B7 literals and paths keep their
  cardinalities (checker). The removed text had no inbound citers. An
  `rg -i "Why unconditional|real backstop|git_gate|3689272946|Why this exists|PRD-120's Trend|keyword detector|exclusion-list repair|Layer 1 still binds|PRD-183 realigned|As of PRD-164|registry/state fixup|non-checked-out ref|Anything longer means"`
  outside docs/prd_history/ and audits/ hits only CH:43 (kept text), historical PROJECT_STATE /
  DECISIONS entries (the rationale carriers), and a dated recon record. The new repoint targets
  resolve (4.3).
- R9: `5fe8ad7`, `daa7065`, `8224033`, `1e1212d` and the whole Ratification paragraph are
  class-H IDs H-A15-CM-* (byte-identical).
- R10: every A17 V-row, retired marker (PA V10, PR V9), report label line and fence, and every
  A18 table row and path, is a class-H ID (byte-identical, same role and cardinality).

### 4.6 Per-line accounting (all 1497 pre-edit lines)

Columns 1-4 are the PRE rule-unit inventory generated from M before the first edit. H_ids counts
come from manifest v0 (section 1); the final PRE of section 5 is authoritative for class H.
Column 5 is the disposition: KEPT byte-identical -> I:n, or the content/reflow hunk id of
section 4.2 with its I-range ("(none)" = removed in full). Operator tokens are a scan aid only (p5).

```tsv
pre_line	kind	operators	H_ids	disposition
CM:1	heading		1	KEPT byte-identical -> I:1
CM:2	blank		0	KEPT byte-identical -> I:2
CM:3	prose		0	KEPT byte-identical -> I:3
CM:4	prose	every	0	KEPT byte-identical -> I:4
CM:5	prose		0	KEPT byte-identical -> I:5
CM:6	prose		0	KEPT byte-identical -> I:6
CM:7	prose	does not	0	KEPT byte-identical -> I:7
CM:8	prose		0	KEPT byte-identical -> I:8
CM:9	prose		0	KEPT byte-identical -> I:9
CM:10	blank		0	KEPT byte-identical -> I:10
CM:11	heading		1	KEPT byte-identical -> I:11
CM:12	blank		0	KEPT byte-identical -> I:12
CM:13	prose	binding	1	KEPT byte-identical -> I:13
CM:14	prose	required	2	KEPT byte-identical -> I:14
CM:15	prose		2	KEPT byte-identical -> I:15
CM:16	prose		3	KEPT byte-identical -> I:16
CM:17	prose		1	KEPT byte-identical -> I:17
CM:18	blank		0	KEPT byte-identical -> I:18
CM:19	heading		1	KEPT byte-identical -> I:19
CM:20	blank		0	KEPT byte-identical -> I:20
CM:21	list	every	0	KEPT byte-identical -> I:21
CM:22	list	only	0	KEPT byte-identical -> I:22
CM:23	list		0	KEPT byte-identical -> I:23
CM:24	list		0	KEPT byte-identical -> I:24
CM:25	list	Every	0	KEPT byte-identical -> I:25
CM:26	list		0	KEPT byte-identical -> I:26
CM:27	list	Never	0	KEPT byte-identical -> I:27
CM:28	list		0	KEPT byte-identical -> I:28
CM:29	list	STOP,requires	0	KEPT byte-identical -> I:29
CM:30	list	never	0	KEPT byte-identical -> I:30
CM:31	list		0	KEPT byte-identical -> I:31
CM:32	list		0	KEPT byte-identical -> I:32
CM:33	list	never	0	KEPT byte-identical -> I:33
CM:34	list	any,only	0	KEPT byte-identical -> I:34
CM:35	list		0	KEPT byte-identical -> I:35
CM:36	list	never	0	KEPT byte-identical -> I:36
CM:37	list	never	0	KEPT byte-identical -> I:37
CM:38	list		0	KEPT byte-identical -> I:38
CM:39	list	any,every,stop	1	KEPT byte-identical -> I:39
CM:40	list		0	KEPT byte-identical -> I:40
CM:41	list		0	KEPT byte-identical -> I:41
CM:42	list	Never	0	KEPT byte-identical -> I:42
CM:43	list		0	KEPT byte-identical -> I:43
CM:44	blank		0	KEPT byte-identical -> I:44
CM:45	heading		1	KEPT byte-identical -> I:45
CM:46	blank		0	KEPT byte-identical -> I:46
CM:47	list		0	KEPT byte-identical -> I:47
CM:48	list		0	KEPT byte-identical -> I:48
CM:49	list	every,exception	0	CM-1 -> I:49-49
CM:50	list		0	CM-1 -> I:49-49
CM:51	list		0	KEPT byte-identical -> I:50
CM:52	list		1	KEPT byte-identical -> I:51
CM:53	list	stop	0	KEPT byte-identical -> I:52
CM:54	blank		0	KEPT byte-identical -> I:53
CM:55	heading	STOP	1	KEPT byte-identical -> I:54
CM:56	blank		0	KEPT byte-identical -> I:55
CM:57	list		0	KEPT byte-identical -> I:56
CM:58	list		0	KEPT byte-identical -> I:57
CM:59	list		0	KEPT byte-identical -> I:58
CM:60	list		0	KEPT byte-identical -> I:59
CM:61	list		0	KEPT byte-identical -> I:60
CM:62	list		0	KEPT byte-identical -> I:61
CM:63	list		1	KEPT byte-identical -> I:62
CM:64	list		0	KEPT byte-identical -> I:63
CM:65	blank		0	KEPT byte-identical -> I:64
CM:66	prose	may not	0	KEPT byte-identical -> I:65
CM:67	blank		0	KEPT byte-identical -> I:66
CM:68	heading		1	KEPT byte-identical -> I:67
CM:69	blank		0	KEPT byte-identical -> I:68
CM:70	prose	Every	0	KEPT byte-identical -> I:69
CM:71	prose	if	1	KEPT byte-identical -> I:70
CM:72	prose	binding	2	KEPT byte-identical -> I:71
CM:73	prose	only	1	KEPT byte-identical -> I:72
CM:74	prose	any,never	0	KEPT byte-identical -> I:73
CM:75	prose	requires	0	KEPT byte-identical -> I:74
CM:76	prose		0	KEPT byte-identical -> I:75
CM:77	prose	exactly	0	CM-2 -> I:76-76
CM:78	prose	do not,only	0	CM-2 -> I:76-76
CM:79	prose		0	KEPT byte-identical -> I:77
CM:80	prose	only	0	KEPT byte-identical -> I:78
CM:81	prose		0	KEPT byte-identical -> I:79
CM:82	blank		0	KEPT byte-identical -> I:80
CM:83	heading	every	1	KEPT byte-identical -> I:81
CM:84	blank		0	KEPT byte-identical -> I:82
CM:85	prose		0	KEPT byte-identical -> I:83
CM:86	list	never	0	KEPT byte-identical -> I:84
CM:87	list		0	KEPT byte-identical -> I:85
CM:88	list		0	KEPT byte-identical -> I:86
CM:89	list	every	0	KEPT byte-identical -> I:87
CM:90	list	Every	0	KEPT byte-identical -> I:88
CM:91	list		0	KEPT byte-identical -> I:89
CM:92	list		0	KEPT byte-identical -> I:90
CM:93	list		0	KEPT byte-identical -> I:91
CM:94	blank		0	KEPT byte-identical -> I:92
CM:95	prose		1	KEPT byte-identical -> I:93
CM:96	prose		1	KEPT byte-identical -> I:94
CM:97	prose	only	0	KEPT byte-identical -> I:95
CM:98	blank		0	KEPT byte-identical -> I:96
CM:99	prose	never	1	KEPT byte-identical -> I:97
CM:100	prose		0	KEPT byte-identical -> I:98
CM:101	prose	never	2	KEPT byte-identical -> I:99
CM:102	prose		2	KEPT byte-identical -> I:100
CM:103	blank		0	KEPT byte-identical -> I:101
CM:104	heading		1	KEPT byte-identical -> I:102
CM:105	blank		0	KEPT byte-identical -> I:103
CM:106	list	every	0	KEPT byte-identical -> I:104
CM:107	list		0	KEPT byte-identical -> I:105
CM:108	list		0	KEPT byte-identical -> I:106
CM:109	list		0	KEPT byte-identical -> I:107
CM:110	list		0	KEPT byte-identical -> I:108
CM:111	list	never	0	KEPT byte-identical -> I:109
CM:112	list	every,required	0	KEPT byte-identical -> I:110
CM:113	list		0	KEPT byte-identical -> I:111
CM:114	list		0	KEPT byte-identical -> I:112
CM:115	list	any,never	0	KEPT byte-identical -> I:113
CM:116	list	any,never	0	KEPT byte-identical -> I:114
CM:117	list		0	KEPT byte-identical -> I:115
CM:118	list		0	KEPT byte-identical -> I:116
CM:119	list		0	KEPT byte-identical -> I:117
CM:120	list		0	KEPT byte-identical -> I:118
CM:121	list		0	KEPT byte-identical -> I:119
CM:122	list		0	KEPT byte-identical -> I:120
CM:123	blank		0	KEPT byte-identical -> I:121
CM:124	heading	do not	1	KEPT byte-identical -> I:122
CM:125	blank		0	KEPT byte-identical -> I:123
CM:126	list		0	KEPT byte-identical -> I:124
CM:127	list	every	0	KEPT byte-identical -> I:125
CM:128	list		0	KEPT byte-identical -> I:126
CM:129	list		0	KEPT byte-identical -> I:127
CM:130	list		0	KEPT byte-identical -> I:128
CM:131	list		2	KEPT byte-identical -> I:129
CM:132	list		3	KEPT byte-identical -> I:130
CM:133	list		1	KEPT byte-identical -> I:131
CM:134	list		0	KEPT byte-identical -> I:132
CM:135	list		1	KEPT byte-identical -> I:133
CM:136	list		1	KEPT byte-identical -> I:134
CM:137	list		0	KEPT byte-identical -> I:135
CM:138	list		0	KEPT byte-identical -> I:136
CM:139	list		0	KEPT byte-identical -> I:137
CM:140	list	if	0	KEPT byte-identical -> I:138
CM:141	list		1	KEPT byte-identical -> I:139
CM:142	list		0	KEPT byte-identical -> I:140
CM:143	list	binding	1	KEPT byte-identical -> I:141
CM:144	list		0	KEPT byte-identical -> I:142
CM:145	blank		0	KEPT byte-identical -> I:143
CM:146	heading		1	KEPT byte-identical -> I:144
CM:147	blank		0	KEPT byte-identical -> I:145
CM:148	prose	only	0	KEPT byte-identical -> I:146
CM:149	prose	Do not	0	KEPT byte-identical -> I:147
CM:150	prose		0	KEPT byte-identical -> I:148
CM:151	prose	verbatim	2	KEPT byte-identical -> I:149
CM:152	prose		2	KEPT byte-identical -> I:150
CM:153	blank		0	KEPT byte-identical -> I:151
CM:154	heading	every	1	KEPT byte-identical -> I:152
CM:155	blank		0	KEPT byte-identical -> I:153
CM:156	list		1	KEPT byte-identical -> I:154
CM:157	list		0	KEPT byte-identical -> I:155
CM:158	list		0	KEPT byte-identical -> I:156
CM:159	list		0	KEPT byte-identical -> I:157
CM:160	list		0	KEPT byte-identical -> I:158
CM:161	list		0	KEPT byte-identical -> I:159
CM:162	list		0	KEPT byte-identical -> I:160
CM:163	list	unless	0	KEPT byte-identical -> I:161
CM:164	list	never	0	KEPT byte-identical -> I:162
CM:165	list		0	KEPT byte-identical -> I:163
CM:166	list		0	KEPT byte-identical -> I:164
CM:167	list	Never,never	0	KEPT byte-identical -> I:165
CM:168	list	stop	0	KEPT byte-identical -> I:166
CM:169	list	any	0	KEPT byte-identical -> I:167
CM:170	blank		0	KEPT byte-identical -> I:168
CM:171	heading		1	KEPT byte-identical -> I:169
CM:172	blank		0	KEPT byte-identical -> I:170
CM:173	list		0	KEPT byte-identical -> I:171
CM:174	list		0	KEPT byte-identical -> I:172
CM:175	list		0	CM-3 -> I:173-173
CM:176	list		0	CM-3 -> I:173-173
CM:177	list		0	KEPT byte-identical -> I:174
CM:178	list		0	KEPT byte-identical -> I:175
CM:179	list		0	KEPT byte-identical -> I:176
CM:180	list		0	KEPT byte-identical -> I:177
CM:181	list		0	KEPT byte-identical -> I:178
CM:182	list		0	KEPT byte-identical -> I:179
CM:183	list		0	KEPT byte-identical -> I:180
CM:184	list		0	KEPT byte-identical -> I:181
CH:1	heading		1	KEPT byte-identical -> I:1
CH:2	blank		0	KEPT byte-identical -> I:2
CH:3	prose		0	CH-1 -> I:3-4
CH:4	prose		2	CH-1 -> I:3-4
CH:5	prose	every	0	CH-1 -> I:3-4
CH:6	blank		0	KEPT byte-identical -> I:5
CH:7	heading		1	KEPT byte-identical -> I:6
CH:8	blank		0	KEPT byte-identical -> I:7
CH:9	table		1	KEPT byte-identical -> I:8
CH:10	table		1	KEPT byte-identical -> I:9
CH:11	table		2	KEPT byte-identical -> I:10
CH:12	table		2	KEPT byte-identical -> I:11
CH:13	table		2	KEPT byte-identical -> I:12
CH:14	blank		0	KEPT byte-identical -> I:13
CH:15	prose		0	KEPT byte-identical -> I:14
CH:16	prose		2	KEPT byte-identical -> I:15
CH:17	prose	does not,only	0	KEPT byte-identical -> I:16
CH:18	blank		0	KEPT byte-identical -> I:17
CH:19	heading		2	KEPT byte-identical -> I:18
CH:20	blank		0	KEPT byte-identical -> I:19
CH:21	prose		1	CH-2 -> I:20-24
CH:22	prose	only	0	CH-2 -> I:20-24
CH:23	prose		0	CH-2 -> I:20-24
CH:24	blank		0	KEPT byte-identical -> I:25
CH:25	prose	If	0	CH-3 -> I:26-32
CH:26	prose		0	CH-3 -> I:26-32
CH:27	prose		0	CH-3 -> I:26-32
CH:28	prose		0	CH-3 -> I:26-32
CH:29	blank		0	KEPT byte-identical -> I:33
CH:30	prose		0	CH-4 -> I:34-36
CH:31	prose		3	CH-4 -> I:34-36
CH:32	prose		0	CH-4 -> I:34-36
CH:33	prose	Never	0	CH-4 -> I:34-36
CH:34	prose		1	CH-4 -> I:34-36
CH:35	prose		0	CH-4 -> I:34-36
CH:36	prose		0	CH-4 -> I:34-36
CH:37	prose	Do not	0	CH-4 -> I:34-36
CH:38	prose		0	CH-4 -> I:34-36
CH:39	blank		0	CH-4 (blank, P5) -> I:34-36
CH:40	prose		0	CH-4 -> I:34-36
CH:41	prose	if	0	CH-4 -> I:34-36
CH:42	prose	never,only	0	CH-4 -> I:34-36
CH:43	prose		0	CH-4 -> I:34-36
CH:44	prose	never	0	CH-4 -> I:34-36
CH:45	prose	every	0	CH-4 -> I:34-36
CH:46	prose	stop	0	CH-4 -> I:34-36
CH:47	blank		0	CH-4 (blank, P5) -> I:34-36
CH:48	prose		0	CH-4 -> I:34-36
CH:49	prose		0	CH-4 -> I:34-36
CH:50	prose		0	CH-4 -> I:34-36
CH:51	prose		0	CH-4 -> I:34-36
CH:52	prose		0	CH-4 -> I:34-36
CH:53	prose		0	CH-4 -> I:34-36
CH:54	blank		0	KEPT byte-identical -> I:37
CH:55	heading		2	KEPT byte-identical -> I:38
CH:56	blank		0	KEPT byte-identical -> I:39
CH:57	prose	every,never,only	0	CH-5 -> I:40-44
CH:58	prose	any	0	CH-5 -> I:40-44
CH:59	prose		0	CH-5 -> I:40-44
CH:60	prose	unless	0	CH-5 -> I:40-44
CH:61	prose		0	CH-5 -> I:40-44
CH:62	blank		0	CH-5 (blank, P5) -> I:40-44
CH:63	prose		0	CH-5 -> I:40-44
CH:64	prose		0	CH-5 -> I:40-44
CH:65	prose		0	CH-5 -> I:40-44
CH:66	prose		0	CH-5 -> I:40-44
CH:67	prose		1	CH-5 -> I:40-44
CH:68	prose		0	CH-5 -> I:40-44
CH:69	prose		0	CH-5 -> I:40-44
CH:70	blank		0	KEPT byte-identical -> I:45
CH:71	heading		2	KEPT byte-identical -> I:46
CH:72	blank		0	KEPT byte-identical -> I:47
CH:73	prose	every	0	CH-6 -> I:48-52
CH:74	prose		0	CH-6 -> I:48-52
CH:75	prose		0	CH-6 -> I:48-52
CH:76	prose	never	0	CH-6 -> I:48-52
CH:77	prose	All	0	CH-6 -> I:48-52
CH:78	prose	NOT	0	CH-6 -> I:48-52
CH:79	prose		0	KEPT byte-identical -> I:53
CH:80	blank		0	KEPT byte-identical -> I:54
CH:81	heading		1	KEPT byte-identical -> I:55
CH:82	blank		0	KEPT byte-identical -> I:56
CH:83	prose		0	CH-7 -> I:57-59
CH:84	prose		1	CH-7 -> I:57-59
CH:85	prose		0	CH-7 -> I:57-59
CH:86	prose		0	CH-7 -> I:57-59
CH:87	prose		0	CH-7 -> I:57-59
PA:1	frontmatter		1	KEPT byte-identical -> I:1
PA:2	frontmatter		2	KEPT byte-identical -> I:2
PA:3	frontmatter	NOT,any	1	KEPT byte-identical -> I:3
PA:4	frontmatter		1	KEPT byte-identical -> I:4
PA:5	blank		0	KEPT byte-identical -> I:5
PA:6	heading		1	KEPT byte-identical -> I:6
PA:7	blank		0	KEPT byte-identical -> I:7
PA:8	heading		1	KEPT byte-identical -> I:8
PA:9	blank		0	KEPT byte-identical -> I:9
PA:10	prose	only	0	KEPT byte-identical -> I:10
PA:11	blank		0	KEPT byte-identical -> I:11
PA:12	list		0	KEPT byte-identical -> I:12
PA:13	list		0	KEPT byte-identical -> I:13
PA:14	blank		0	KEPT byte-identical -> I:14
PA:15	prose	NOT	0	KEPT byte-identical -> I:15
PA:16	blank		0	KEPT byte-identical -> I:16
PA:17	list		0	KEPT byte-identical -> I:17
PA:18	list		1	KEPT byte-identical -> I:18
PA:19	list		0	KEPT byte-identical -> I:19
PA:20	list		0	KEPT byte-identical -> I:20
PA:21	blank		0	KEPT byte-identical -> I:21
PA:22	prose		0	KEPT byte-identical -> I:22
PA:23	prose	requires	0	KEPT byte-identical -> I:23
PA:24	prose		0	KEPT byte-identical -> I:24
PA:25	blank		0	KEPT byte-identical -> I:25
PA:26	heading		1	KEPT byte-identical -> I:26
PA:27	blank		0	KEPT byte-identical -> I:27
PA:28	list		0	KEPT byte-identical -> I:28
PA:29	list		0	KEPT byte-identical -> I:29
PA:30	list		0	KEPT byte-identical -> I:30
PA:31	list		0	KEPT byte-identical -> I:31
PA:32	list	Any	0	KEPT byte-identical -> I:32
PA:33	blank		0	KEPT byte-identical -> I:33
PA:34	prose	NOT	0	KEPT byte-identical -> I:34
PA:35	prose		0	KEPT byte-identical -> I:35
PA:36	blank		0	KEPT byte-identical -> I:36
PA:37	heading		1	KEPT byte-identical -> I:37
PA:38	blank		0	KEPT byte-identical -> I:38
PA:39	prose	Default	0	KEPT byte-identical -> I:39
PA:40	blank		0	KEPT byte-identical -> I:40
PA:41	list		0	KEPT byte-identical -> I:41
PA:42	list	Do not,any	0	KEPT byte-identical -> I:42
PA:43	list		0	KEPT byte-identical -> I:43
PA:44	list	NOT,unless	0	KEPT byte-identical -> I:44
PA:45	list		0	PA-1 -> I:45-46
PA:46	list		1	PA-1 -> I:45-46
PA:47	list		0	PA-1 -> I:45-46
PA:48	list		0	PA-1 -> I:45-46
PA:49	blank		0	KEPT byte-identical -> I:47
PA:50	prose	If,default	0	KEPT byte-identical -> I:48
PA:51	prose		0	KEPT byte-identical -> I:49
PA:52	blank		0	KEPT byte-identical -> I:50
PA:53	heading		1	KEPT byte-identical -> I:51
PA:54	blank		0	KEPT byte-identical -> I:52
PA:55	prose	never	0	KEPT byte-identical -> I:53
PA:56	prose		0	KEPT byte-identical -> I:54
PA:57	blank		0	KEPT byte-identical -> I:55
PA:58	list		0	KEPT byte-identical -> I:56
PA:59	list		0	KEPT byte-identical -> I:57
PA:60	list		0	KEPT byte-identical -> I:58
PA:61	list		0	KEPT byte-identical -> I:59
PA:62	list		0	KEPT byte-identical -> I:60
PA:63	list		0	KEPT byte-identical -> I:61
PA:64	blank		0	KEPT byte-identical -> I:62
PA:65	prose	If	0	KEPT byte-identical -> I:63
PA:66	prose	MUST	0	KEPT byte-identical -> I:64
PA:67	blank		0	KEPT byte-identical -> I:65
PA:68	list		0	KEPT byte-identical -> I:66
PA:69	list		0	KEPT byte-identical -> I:67
PA:70	list		0	KEPT byte-identical -> I:68
PA:71	list		0	KEPT byte-identical -> I:69
PA:72	list		0	KEPT byte-identical -> I:70
PA:73	blank		0	KEPT byte-identical -> I:71
PA:74	prose	forbidden	0	KEPT byte-identical -> I:72
PA:75	blank		0	KEPT byte-identical -> I:73
PA:76	heading		1	KEPT byte-identical -> I:74
PA:77	blank		0	KEPT byte-identical -> I:75
PA:78	heading		1	KEPT byte-identical -> I:76
PA:79	blank		0	KEPT byte-identical -> I:77
PA:80	list		0	KEPT byte-identical -> I:78
PA:81	list		0	KEPT byte-identical -> I:79
PA:82	list		0	KEPT byte-identical -> I:80
PA:83	list		1	PA-2 -> I:81-83
PA:84	list	only	0	PA-2 -> I:81-83
PA:85	list		0	PA-2 -> I:81-83
PA:86	list		0	PA-2 -> I:81-83
PA:87	list		0	PA-2 -> I:81-83
PA:88	list	if,only	0	KEPT byte-identical -> I:84
PA:89	list		2	KEPT byte-identical -> I:85
PA:90	list		0	KEPT byte-identical -> I:86
PA:91	list		0	KEPT byte-identical -> I:87
PA:92	list	verbatim	0	KEPT byte-identical -> I:88
PA:93	list		0	KEPT byte-identical -> I:89
PA:94	list		0	KEPT byte-identical -> I:90
PA:95	list		3	KEPT byte-identical -> I:91
PA:96	list	Every	0	KEPT byte-identical -> I:92
PA:97	blank		0	KEPT byte-identical -> I:93
PA:98	heading		1	KEPT byte-identical -> I:94
PA:99	blank		0	KEPT byte-identical -> I:95
PA:100	prose	every	1	KEPT byte-identical -> I:96
PA:101	prose	Do not,any,if	0	KEPT byte-identical -> I:97
PA:102	prose	does not	0	KEPT byte-identical -> I:98
PA:103	blank		0	KEPT byte-identical -> I:99
PA:104	table		1	KEPT byte-identical -> I:100
PA:105	table		1	KEPT byte-identical -> I:101
PA:106	table	Every	1	KEPT byte-identical -> I:102
PA:107	table	Every	1	KEPT byte-identical -> I:103
PA:108	table	Every,every	1	KEPT byte-identical -> I:104
PA:109	table	every,if	1	KEPT byte-identical -> I:105
PA:110	table	EXCEPT,only,unless	5	KEPT byte-identical -> I:106
PA:111	table		1	KEPT byte-identical -> I:107
PA:112	table	If,if,only	3	KEPT byte-identical -> I:108
PA:113	table		4	KEPT byte-identical -> I:109
PA:114	table	ONLY,if	1	KEPT byte-identical -> I:110
PA:115	table		1	KEPT byte-identical -> I:111
PA:116	blank		0	KEPT byte-identical -> I:112
PA:117	heading	every	2	KEPT byte-identical -> I:113
PA:118	blank		0	KEPT byte-identical -> I:114
PA:119	fence		1	KEPT byte-identical -> I:115
PA:120	fence		2	KEPT byte-identical -> I:116
PA:121	fence		1	KEPT byte-identical -> I:117
PA:122	fence		1	KEPT byte-identical -> I:118
PA:123	fence		1	KEPT byte-identical -> I:119
PA:124	fence		1	KEPT byte-identical -> I:120
PA:125	fence		1	KEPT byte-identical -> I:121
PA:126	fence		1	KEPT byte-identical -> I:122
PA:127	fence		1	KEPT byte-identical -> I:123
PA:128	fence		3	KEPT byte-identical -> I:124
PA:129	fence		1	KEPT byte-identical -> I:125
PA:130	fence		1	KEPT byte-identical -> I:126
PA:131	fence		1	KEPT byte-identical -> I:127
PA:132	fence		1	KEPT byte-identical -> I:128
PA:133	fence		1	KEPT byte-identical -> I:129
PA:134	blank		0	KEPT byte-identical -> I:130
PA:135	heading		1	KEPT byte-identical -> I:131
PA:136	blank		0	KEPT byte-identical -> I:132
PA:137	prose		0	KEPT byte-identical -> I:133
PA:138	blank		0	KEPT byte-identical -> I:134
PA:139	list		0	KEPT byte-identical -> I:135
PA:140	list		0	KEPT byte-identical -> I:136
PA:141	list		0	KEPT byte-identical -> I:137
PA:142	blank		0	KEPT byte-identical -> I:138
PA:143	prose		0	KEPT byte-identical -> I:139
PA:144	blank		0	KEPT byte-identical -> I:140
PA:145	list		0	KEPT byte-identical -> I:141
PA:146	list		0	KEPT byte-identical -> I:142
PA:147	list		0	KEPT byte-identical -> I:143
PA:148	list		0	KEPT byte-identical -> I:144
PA:149	list		0	KEPT byte-identical -> I:145
PA:150	list		0	KEPT byte-identical -> I:146
PA:151	blank		0	KEPT byte-identical -> I:147
PA:152	prose	If	0	KEPT byte-identical -> I:148
PA:153	prose		0	KEPT byte-identical -> I:149
PA:154	blank		0	KEPT byte-identical -> I:150
PA:155	prose		0	KEPT byte-identical -> I:151
PA:156	blank		0	KEPT byte-identical -> I:152
PA:157	list		0	KEPT byte-identical -> I:153
PA:158	list		0	KEPT byte-identical -> I:154
PA:159	list		1	KEPT byte-identical -> I:155
PA:160	list	if,only	1	KEPT byte-identical -> I:156
PA:161	list	does not	0	KEPT byte-identical -> I:157
PA:162	blank		0	KEPT byte-identical -> I:158
PA:163	heading	NOT	1	KEPT byte-identical -> I:159
PA:164	blank		0	KEPT byte-identical -> I:160
PA:165	list	Does not	0	KEPT byte-identical -> I:161
PA:166	list	Does not	0	KEPT byte-identical -> I:162
PA:167	list	Does not	0	KEPT byte-identical -> I:163
PA:168	list	Does not,unless	0	KEPT byte-identical -> I:164
PA:169	list		0	KEPT byte-identical -> I:165
PA:170	list	Does not	0	KEPT byte-identical -> I:166
PA:171	list	only	0	KEPT byte-identical -> I:167
PA:172	blank		0	KEPT byte-identical -> I:168
PA:173	heading	refuse	1	KEPT byte-identical -> I:169
PA:174	blank		0	KEPT byte-identical -> I:170
PA:175	list	refuse	0	KEPT byte-identical -> I:171
PA:176	list		0	KEPT byte-identical -> I:172
PA:177	list	stop	0	KEPT byte-identical -> I:173
PA:178	list	refuse	0	KEPT byte-identical -> I:174
PA:179	list	refuse	0	KEPT byte-identical -> I:175
PA:180	list		0	KEPT byte-identical -> I:176
PC:1	frontmatter		1	KEPT byte-identical -> I:1
PC:2	frontmatter		2	KEPT byte-identical -> I:2
PC:3	frontmatter		2	KEPT byte-identical -> I:3
PC:4	frontmatter		1	KEPT byte-identical -> I:4
PC:5	blank		0	KEPT byte-identical -> I:5
PC:6	heading		1	KEPT byte-identical -> I:6
PC:7	blank		0	KEPT byte-identical -> I:7
PC:8	heading		1	KEPT byte-identical -> I:8
PC:9	blank		0	KEPT byte-identical -> I:9
PC:10	prose	only	0	KEPT byte-identical -> I:10
PC:11	blank		0	KEPT byte-identical -> I:11
PC:12	list		0	KEPT byte-identical -> I:12
PC:13	list		0	KEPT byte-identical -> I:13
PC:14	list	all	0	KEPT byte-identical -> I:14
PC:15	list		0	KEPT byte-identical -> I:15
PC:16	blank		0	KEPT byte-identical -> I:16
PC:17	prose	NOT	0	KEPT byte-identical -> I:17
PC:18	blank		0	KEPT byte-identical -> I:18
PC:19	list		0	KEPT byte-identical -> I:19
PC:20	list		0	KEPT byte-identical -> I:20
PC:21	list		0	PC-1 -> I:21-21
PC:22	list		0	PC-1 -> I:21-21
PC:23	list		0	KEPT byte-identical -> I:22
PC:24	list		0	KEPT byte-identical -> I:23
PC:25	blank		0	KEPT byte-identical -> I:24
PC:26	prose		1	KEPT byte-identical -> I:25
PC:27	prose		0	PC-2 -> I:26-29
PC:28	prose		0	PC-2 -> I:26-29
PC:29	prose	If	0	PC-2 -> I:26-29
PC:30	prose	refuse	0	PC-2 -> I:26-29
PC:31	prose		0	PC-2 -> I:26-29
PC:32	prose	only	0	PC-2 -> I:26-29
PC:33	blank		0	PC-2 (blank, P5) -> I:26-29
PC:34	prose	if,required	0	PC-2 -> I:26-29
PC:35	prose	does not	0	PC-2 -> I:26-29
PC:36	prose		0	PC-2 -> I:26-29
PC:37	blank		0	KEPT byte-identical -> I:30
PC:38	heading		1	KEPT byte-identical -> I:31
PC:39	blank		0	KEPT byte-identical -> I:32
PC:40	list		0	KEPT byte-identical -> I:33
PC:41	list		0	KEPT byte-identical -> I:34
PC:42	list		0	KEPT byte-identical -> I:35
PC:43	list		0	KEPT byte-identical -> I:36
PC:44	list		0	KEPT byte-identical -> I:37
PC:45	blank		0	KEPT byte-identical -> I:38
PC:46	prose	NOT	0	KEPT byte-identical -> I:39
PC:47	list		0	KEPT byte-identical -> I:40
PC:48	list		0	KEPT byte-identical -> I:41
PC:49	list		0	KEPT byte-identical -> I:42
PC:50	blank		0	KEPT byte-identical -> I:43
PC:51	heading		1	KEPT byte-identical -> I:44
PC:52	blank		0	KEPT byte-identical -> I:45
PC:53	prose	Default	0	KEPT byte-identical -> I:46
PC:54	blank		0	KEPT byte-identical -> I:47
PC:55	list		0	KEPT byte-identical -> I:48
PC:56	list		0	KEPT byte-identical -> I:49
PC:57	list	Do not	0	KEPT byte-identical -> I:50
PC:58	list		0	KEPT byte-identical -> I:51
PC:59	list		0	PC-3 -> I:52-54
PC:60	list		0	PC-3 -> I:52-54
PC:61	list		0	PC-3 -> I:52-54
PC:62	list		2	KEPT byte-identical -> I:55
PC:63	list		3	KEPT byte-identical -> I:56
PC:64	list		1	KEPT byte-identical -> I:57
PC:65	list		0	PC-4 -> I:58-58
PC:66	list	required	0	PC-4 -> I:58-58
PC:67	list		0	PC-4 -> I:58-58
PC:68	blank		0	PC-4 (blank, P5) -> I:58-58
PC:69	prose	If	0	PC-4 -> I:58-58
PC:70	prose		0	PC-4 -> I:58-58
PC:71	prose		0	PC-4 -> I:58-58
PC:72	blank		0	KEPT byte-identical -> I:59
PC:73	prose	If,default	0	KEPT byte-identical -> I:60
PC:74	blank		0	KEPT byte-identical -> I:61
PC:75	heading	required	1	KEPT byte-identical -> I:62
PC:76	blank		0	KEPT byte-identical -> I:63
PC:77	prose		0	KEPT byte-identical -> I:64
PC:78	blank		0	KEPT byte-identical -> I:65
PC:79	list		0	KEPT byte-identical -> I:66
PC:80	list		1	KEPT byte-identical -> I:67
PC:81	list	default	0	KEPT byte-identical -> I:68
PC:82	list		0	KEPT byte-identical -> I:69
PC:83	list		0	KEPT byte-identical -> I:70
PC:84	list		0	KEPT byte-identical -> I:71
PC:85	list	only	0	KEPT byte-identical -> I:72
PC:86	list		0	PC-5 -> I:73-73
PC:87	list		0	PC-5 -> I:73-73
PC:88	list		1	KEPT byte-identical -> I:74
PC:89	list		1	KEPT byte-identical -> I:75
PC:90	list	never	0	KEPT byte-identical -> I:76
PC:91	blank		0	KEPT byte-identical -> I:77
PC:92	prose	If,NOT,any,required	0	KEPT byte-identical -> I:78
PC:93	blank		0	KEPT byte-identical -> I:79
PC:94	heading		1	KEPT byte-identical -> I:80
PC:95	blank		0	KEPT byte-identical -> I:81
PC:96	prose	never	0	KEPT byte-identical -> I:82
PC:97	prose		0	KEPT byte-identical -> I:83
PC:98	blank		0	KEPT byte-identical -> I:84
PC:99	list		0	KEPT byte-identical -> I:85
PC:100	list		1	KEPT byte-identical -> I:86
PC:101	list		0	KEPT byte-identical -> I:87
PC:102	list	never	0	KEPT byte-identical -> I:88
PC:103	list		0	KEPT byte-identical -> I:89
PC:104	list		0	KEPT byte-identical -> I:90
PC:105	list	never	0	KEPT byte-identical -> I:91
PC:106	list	never	0	KEPT byte-identical -> I:92
PC:107	blank		0	KEPT byte-identical -> I:93
PC:108	prose	If,any,stop	0	KEPT byte-identical -> I:94
PC:109	prose	Do not	0	KEPT byte-identical -> I:95
PC:110	blank		0	KEPT byte-identical -> I:96
PC:111	heading		1	KEPT byte-identical -> I:97
PC:112	blank		0	KEPT byte-identical -> I:98
PC:113	prose	MUST	0	KEPT byte-identical -> I:99
PC:114	prose		0	KEPT byte-identical -> I:100
PC:115	prose	does not	0	KEPT byte-identical -> I:101
PC:116	blank		0	KEPT byte-identical -> I:102
PC:117	prose	If,stop	0	KEPT byte-identical -> I:103
PC:118	prose		0	KEPT byte-identical -> I:104
PC:119	prose		0	PC-6 -> I:105-105
PC:120	prose	forbidden	0	PC-6 -> I:105-105
PC:121	blank		0	KEPT byte-identical -> I:106
PC:122	prose		0	KEPT byte-identical -> I:107
PC:123	prose		0	KEPT byte-identical -> I:108
PC:124	prose		0	KEPT byte-identical -> I:109
PC:125	blank		0	KEPT byte-identical -> I:110
PC:126	heading		1	KEPT byte-identical -> I:111
PC:127	blank		0	KEPT byte-identical -> I:112
PC:128	heading		1	KEPT byte-identical -> I:113
PC:129	blank		0	KEPT byte-identical -> I:114
PC:130	list	every,stop	0	KEPT byte-identical -> I:115
PC:131	list		0	KEPT byte-identical -> I:116
PC:132	list		1	KEPT byte-identical -> I:117
PC:133	list		0	KEPT byte-identical -> I:118
PC:134	list		0	KEPT byte-identical -> I:119
PC:135	list	at least	0	KEPT byte-identical -> I:120
PC:136	list		0	KEPT byte-identical -> I:121
PC:137	list		0	KEPT byte-identical -> I:122
PC:138	list		0	KEPT byte-identical -> I:123
PC:139	list		0	KEPT byte-identical -> I:124
PC:140	list	any	0	KEPT byte-identical -> I:125
PC:141	list		0	KEPT byte-identical -> I:126
PC:142	list		0	KEPT byte-identical -> I:127
PC:143	list	if	0	KEPT byte-identical -> I:128
PC:144	list		0	KEPT byte-identical -> I:129
PC:145	list		0	KEPT byte-identical -> I:130
PC:146	list		3	KEPT byte-identical -> I:131
PC:147	list	all	1	KEPT byte-identical -> I:132
PC:148	list		0	KEPT byte-identical -> I:133
PC:149	list		0	KEPT byte-identical -> I:134
PC:150	list	Do not	0	KEPT byte-identical -> I:135
PC:151	list	If,any	0	KEPT byte-identical -> I:136
PC:152	list	stop	0	KEPT byte-identical -> I:137
PC:153	list	do not	0	KEPT byte-identical -> I:138
PC:154	blank		0	KEPT byte-identical -> I:139
PC:155	heading		1	KEPT byte-identical -> I:140
PC:156	blank		0	KEPT byte-identical -> I:141
PC:157	prose	every	1	KEPT byte-identical -> I:142
PC:158	prose	Do not,any	0	KEPT byte-identical -> I:143
PC:159	blank		0	KEPT byte-identical -> I:144
PC:160	table		1	KEPT byte-identical -> I:145
PC:161	table		1	KEPT byte-identical -> I:146
PC:162	table	Stop	2	KEPT byte-identical -> I:147
PC:163	table	Stop	2	KEPT byte-identical -> I:148
PC:164	table		1	KEPT byte-identical -> I:149
PC:165	table		3	KEPT byte-identical -> I:150
PC:166	table		1	KEPT byte-identical -> I:151
PC:167	table		1	KEPT byte-identical -> I:152
PC:168	table		1	KEPT byte-identical -> I:153
PC:169	table		4	KEPT byte-identical -> I:154
PC:170	table	does not	2	KEPT byte-identical -> I:155
PC:171	table	All	1	KEPT byte-identical -> I:156
PC:172	table		1	KEPT byte-identical -> I:157
PC:173	table	Stop,any	1	KEPT byte-identical -> I:158
PC:174	blank		0	KEPT byte-identical -> I:159
PC:175	prose		0	KEPT byte-identical -> I:160
PC:176	list		0	KEPT byte-identical -> I:161
PC:177	list		0	KEPT byte-identical -> I:162
PC:178	list		0	KEPT byte-identical -> I:163
PC:179	list		0	KEPT byte-identical -> I:164
PC:180	blank		0	KEPT byte-identical -> I:165
PC:181	heading	every	2	KEPT byte-identical -> I:166
PC:182	blank		0	KEPT byte-identical -> I:167
PC:183	fence		1	KEPT byte-identical -> I:168
PC:184	fence		2	KEPT byte-identical -> I:169
PC:185	fence		1	KEPT byte-identical -> I:170
PC:186	fence		1	KEPT byte-identical -> I:171
PC:187	fence	STOP	1	KEPT byte-identical -> I:172
PC:188	fence		1	KEPT byte-identical -> I:173
PC:189	fence		1	KEPT byte-identical -> I:174
PC:190	fence		1	KEPT byte-identical -> I:175
PC:191	fence		1	KEPT byte-identical -> I:176
PC:192	fence		2	KEPT byte-identical -> I:177
PC:193	fence		1	KEPT byte-identical -> I:178
PC:194	fence		1	KEPT byte-identical -> I:179
PC:195	fence		1	KEPT byte-identical -> I:180
PC:196	fence		1	KEPT byte-identical -> I:181
PC:197	fence		1	KEPT byte-identical -> I:182
PC:198	fence		1	KEPT byte-identical -> I:183
PC:199	fence		1	KEPT byte-identical -> I:184
PC:200	blank		0	KEPT byte-identical -> I:185
PC:201	heading		1	KEPT byte-identical -> I:186
PC:202	blank		0	KEPT byte-identical -> I:187
PC:203	prose		0	KEPT byte-identical -> I:188
PC:204	blank		0	KEPT byte-identical -> I:189
PC:205	list		0	KEPT byte-identical -> I:190
PC:206	list		0	KEPT byte-identical -> I:191
PC:207	list		0	KEPT byte-identical -> I:192
PC:208	blank		0	KEPT byte-identical -> I:193
PC:209	prose		0	KEPT byte-identical -> I:194
PC:210	blank		0	KEPT byte-identical -> I:195
PC:211	prose		0	KEPT byte-identical -> I:196
PC:212	blank		0	KEPT byte-identical -> I:197
PC:213	list	if,only	0	KEPT byte-identical -> I:198
PC:214	list	never	0	KEPT byte-identical -> I:199
PC:215	list		0	KEPT byte-identical -> I:200
PC:216	blank		0	KEPT byte-identical -> I:201
PC:217	heading	NOT	1	KEPT byte-identical -> I:202
PC:218	blank		0	KEPT byte-identical -> I:203
PC:219	list	Does not	0	KEPT byte-identical -> I:204
PC:220	list	Does not	1	KEPT byte-identical -> I:205
PC:221	list	Does not	0	PC-7 -> I:206-207
PC:222	list	if,required	0	PC-7 -> I:206-207
PC:223	list	Does not	0	KEPT byte-identical -> I:208
PC:224	list		0	KEPT byte-identical -> I:209
PC:225	list	Does not	0	KEPT byte-identical -> I:210
PC:226	list	Does not	0	KEPT byte-identical -> I:211
PC:227	blank		0	KEPT byte-identical -> I:212
PC:228	heading	refuse	1	KEPT byte-identical -> I:213
PC:229	blank		0	KEPT byte-identical -> I:214
PC:230	list	refuse	0	KEPT byte-identical -> I:215
PC:231	list		0	KEPT byte-identical -> I:216
PC:232	list	refuse	1	KEPT byte-identical -> I:217
PC:233	list	refuse	0	KEPT byte-identical -> I:218
PC:234	list		0	KEPT byte-identical -> I:219
PC:235	list	refuse	0	KEPT byte-identical -> I:220
PC:236	list	stop	0	KEPT byte-identical -> I:221
PC:237	list		0	KEPT byte-identical -> I:222
PC:238	list	refuse	0	KEPT byte-identical -> I:223
PC:239	list	refuse	0	KEPT byte-identical -> I:224
PC:240	list	refuse	0	KEPT byte-identical -> I:225
PR:1	frontmatter		1	KEPT byte-identical -> I:1
PR:2	frontmatter		2	KEPT byte-identical -> I:2
PR:3	frontmatter	every,never	3	KEPT byte-identical -> I:3
PR:4	frontmatter		1	KEPT byte-identical -> I:4
PR:5	blank		0	KEPT byte-identical -> I:5
PR:6	heading		1	KEPT byte-identical -> I:6
PR:7	blank		0	KEPT byte-identical -> I:7
PR:8	heading		1	KEPT byte-identical -> I:8
PR:9	blank		0	KEPT byte-identical -> I:9
PR:10	prose	only	0	KEPT byte-identical -> I:10
PR:11	blank		0	KEPT byte-identical -> I:11
PR:12	list		0	PR-1 -> I:12-14
PR:13	list		0	PR-1 -> I:12-14
PR:14	list		0	PR-1 -> I:12-14
PR:15	list	never	0	PR-1 -> I:12-14
PR:16	list		0	PR-1 -> I:12-14
PR:17	list	every	0	KEPT byte-identical -> I:15
PR:18	list		0	KEPT byte-identical -> I:16
PR:19	blank		0	KEPT byte-identical -> I:17
PR:20	prose	NOT	0	KEPT byte-identical -> I:18
PR:21	blank		0	KEPT byte-identical -> I:19
PR:22	list		1	KEPT byte-identical -> I:20
PR:23	list		0	KEPT byte-identical -> I:21
PR:24	list		0	KEPT byte-identical -> I:22
PR:25	list		1	KEPT byte-identical -> I:23
PR:26	list	only	0	KEPT byte-identical -> I:24
PR:27	list		0	KEPT byte-identical -> I:25
PR:28	list		0	KEPT byte-identical -> I:26
PR:29	blank		0	KEPT byte-identical -> I:27
PR:30	heading		1	KEPT byte-identical -> I:28
PR:31	blank		0	KEPT byte-identical -> I:29
PR:32	prose	only	0	PR-2 -> I:30-33
PR:33	prose	if	0	PR-2 -> I:30-33
PR:34	prose	does not	0	PR-2 -> I:30-33
PR:35	prose		0	PR-2 -> I:30-33
PR:36	prose		0	PR-2 -> I:30-33
PR:37	prose	never	0	PR-2 -> I:30-33
PR:38	prose		0	PR-2 -> I:30-33
PR:39	blank		0	KEPT byte-identical -> I:34
PR:40	heading		1	KEPT byte-identical -> I:35
PR:41	blank		0	KEPT byte-identical -> I:36
PR:42	list		0	KEPT byte-identical -> I:37
PR:43	list		0	KEPT byte-identical -> I:38
PR:44	list		0	KEPT byte-identical -> I:39
PR:45	list		0	KEPT byte-identical -> I:40
PR:46	blank		0	KEPT byte-identical -> I:41
PR:47	prose	NOT	0	KEPT byte-identical -> I:42
PR:48	list	if	0	PR-3 -> I:43-44
PR:49	list		0	PR-3 -> I:43-44
PR:50	list	if	0	PR-3 -> I:43-44
PR:51	list		0	KEPT byte-identical -> I:45
PR:52	list		0	PR-4 -> I:46-46
PR:53	list		1	PR-4 -> I:46-46
PR:54	list		2	KEPT byte-identical -> I:47
PR:55	blank		0	KEPT byte-identical -> I:48
PR:56	heading		1	KEPT byte-identical -> I:49
PR:57	blank		0	KEPT byte-identical -> I:50
PR:58	prose	Default	0	KEPT byte-identical -> I:51
PR:59	blank		0	KEPT byte-identical -> I:52
PR:60	list		0	PR-5 -> I:53-55
PR:61	list	Do not	0	PR-5 -> I:53-55
PR:62	list		2	PR-5 -> I:53-55
PR:63	list	Refuse,if	0	PR-5 -> I:53-55
PR:64	list	if	1	PR-5 -> I:53-55
PR:65	list	never	0	KEPT byte-identical -> I:56
PR:66	blank		0	KEPT byte-identical -> I:57
PR:67	prose	If,default	0	KEPT byte-identical -> I:58
PR:68	blank		0	KEPT byte-identical -> I:59
PR:69	heading	required	1	KEPT byte-identical -> I:60
PR:70	blank		0	KEPT byte-identical -> I:61
PR:71	list		0	KEPT byte-identical -> I:62
PR:72	list		0	PR-6 -> I:63-65
PR:73	list		0	PR-6 -> I:63-65
PR:74	list		0	PR-6 -> I:63-65
PR:75	list		0	PR-6 -> I:63-65
PR:76	list	only	0	KEPT byte-identical -> I:66
PR:77	list		2	PR-7 -> I:67-70
PR:78	list	refuses	0	PR-7 -> I:67-70
PR:79	list		0	PR-7 -> I:67-70
PR:80	list	default,only	0	PR-7 -> I:67-70
PR:81	list	every,if	0	PR-7 -> I:67-70
PR:82	list	Default,only	0	PR-7 -> I:67-70
PR:83	blank		0	KEPT byte-identical -> I:71
PR:84	heading		1	KEPT byte-identical -> I:72
PR:85	blank		0	KEPT byte-identical -> I:73
PR:86	prose	never	0	KEPT byte-identical -> I:74
PR:87	blank		0	KEPT byte-identical -> I:75
PR:88	list	any	0	KEPT byte-identical -> I:76
PR:89	list		0	KEPT byte-identical -> I:77
PR:90	list	only	0	PR-8 -> I:78-78
PR:91	list		1	PR-8 -> I:78-78
PR:92	list		0	KEPT byte-identical -> I:79
PR:93	blank		0	KEPT byte-identical -> I:80
PR:94	prose	If	0	PR-9 -> I:81-82
PR:95	prose		0	PR-9 -> I:81-82
PR:96	prose		0	PR-9 -> I:81-82
PR:97	prose		1	KEPT byte-identical -> I:83
PR:98	blank		0	KEPT byte-identical -> I:84
PR:99	heading		1	KEPT byte-identical -> I:85
PR:100	blank		0	KEPT byte-identical -> I:86
PR:101	prose		0	KEPT byte-identical -> I:87
PR:102	blank		0	KEPT byte-identical -> I:88
PR:103	list		2	KEPT byte-identical -> I:89
PR:104	list	only	0	KEPT byte-identical -> I:90
PR:105	list		2	PR-10 -> I:91-93
PR:106	list		2	PR-10 -> I:91-93
PR:107	list		1	PR-10 -> I:91-93
PR:108	list		0	PR-10 -> I:91-93
PR:109	list		0	PR-10 -> I:91-93
PR:110	list	if,refuses	0	PR-10 -> I:91-93
PR:111	blank		0	KEPT byte-identical -> I:94
PR:112	prose	If	0	KEPT byte-identical -> I:95
PR:113	prose	refuse	1	KEPT byte-identical -> I:96
PR:114	blank		0	KEPT byte-identical -> I:97
PR:115	heading		1	KEPT byte-identical -> I:98
PR:116	blank		0	KEPT byte-identical -> I:99
PR:117	prose	Every	0	KEPT byte-identical -> I:100
PR:118	blank		0	KEPT byte-identical -> I:101
PR:119	fence		1	KEPT byte-identical -> I:102
PR:120	fence		2	KEPT byte-identical -> I:103
PR:121	fence		2	KEPT byte-identical -> I:104
PR:122	fence		2	KEPT byte-identical -> I:105
PR:123	fence		3	KEPT byte-identical -> I:106
PR:124	fence		2	KEPT byte-identical -> I:107
PR:125	fence		1	KEPT byte-identical -> I:108
PR:126	fence		1	KEPT byte-identical -> I:109
PR:127	fence		1	KEPT byte-identical -> I:110
PR:128	fence		1	KEPT byte-identical -> I:111
PR:129	blank		1	KEPT byte-identical -> I:112
PR:130	fence		1	KEPT byte-identical -> I:113
PR:131	blank		1	KEPT byte-identical -> I:114
PR:132	fence		2	KEPT byte-identical -> I:115
PR:133	fence		2	KEPT byte-identical -> I:116
PR:134	blank		1	KEPT byte-identical -> I:117
PR:135	fence		2	KEPT byte-identical -> I:118
PR:136	fence		1	KEPT byte-identical -> I:119
PR:137	blank		1	KEPT byte-identical -> I:120
PR:138	fence		2	KEPT byte-identical -> I:121
PR:139	fence		1	KEPT byte-identical -> I:122
PR:140	fence		1	KEPT byte-identical -> I:123
PR:141	blank		1	KEPT byte-identical -> I:124
PR:142	fence		2	KEPT byte-identical -> I:125
PR:143	fence		1	KEPT byte-identical -> I:126
PR:144	blank		1	KEPT byte-identical -> I:127
PR:145	fence		2	KEPT byte-identical -> I:128
PR:146	fence	required	1	KEPT byte-identical -> I:129
PR:147	fence		1	KEPT byte-identical -> I:130
PR:148	blank		1	KEPT byte-identical -> I:131
PR:149	fence		2	KEPT byte-identical -> I:132
PR:150	fence		1	KEPT byte-identical -> I:133
PR:151	fence		1	KEPT byte-identical -> I:134
PR:152	fence		1	KEPT byte-identical -> I:135
PR:153	fence		1	KEPT byte-identical -> I:136
PR:154	fence		3	KEPT byte-identical -> I:137
PR:155	fence		1	KEPT byte-identical -> I:138
PR:156	blank		1	KEPT byte-identical -> I:139
PR:157	fence		2	KEPT byte-identical -> I:140
PR:158	fence		1	KEPT byte-identical -> I:141
PR:159	fence		1	KEPT byte-identical -> I:142
PR:160	fence		1	KEPT byte-identical -> I:143
PR:161	fence	any	1	KEPT byte-identical -> I:144
PR:162	fence		1	KEPT byte-identical -> I:145
PR:163	blank		1	KEPT byte-identical -> I:146
PR:164	fence	only	2	KEPT byte-identical -> I:147
PR:165	fence		1	KEPT byte-identical -> I:148
PR:166	fence		1	KEPT byte-identical -> I:149
PR:167	fence	unless	1	KEPT byte-identical -> I:150
PR:168	fence		1	KEPT byte-identical -> I:151
PR:169	fence		1	KEPT byte-identical -> I:152
PR:170	blank		0	KEPT byte-identical -> I:153
PR:171	heading		1	KEPT byte-identical -> I:154
PR:172	blank		0	KEPT byte-identical -> I:155
PR:173	heading		1	KEPT byte-identical -> I:156
PR:174	blank		0	KEPT byte-identical -> I:157
PR:175	list		0	KEPT byte-identical -> I:158
PR:176	list		1	PR-11 -> I:159-162
PR:177	list	if	0	PR-11 -> I:159-162
PR:178	list		0	PR-11 -> I:159-162
PR:179	list	never	0	PR-11 -> I:159-162
PR:180	list		0	PR-11 -> I:159-162
PR:181	list		0	PR-11 -> I:159-162
PR:182	list		0	PR-11 -> I:159-162
PR:183	list	only	1	KEPT byte-identical -> I:163
PR:184	list	do not	0	KEPT byte-identical -> I:164
PR:185	list	Refuse,if	0	KEPT byte-identical -> I:165
PR:186	list	If	0	KEPT byte-identical -> I:166
PR:187	list		0	KEPT byte-identical -> I:167
PR:188	list		0	KEPT byte-identical -> I:168
PR:189	list		2	KEPT byte-identical -> I:169
PR:190	list		0	KEPT byte-identical -> I:170
PR:191	list		0	KEPT byte-identical -> I:171
PR:192	list		0	KEPT byte-identical -> I:172
PR:193	list		0	KEPT byte-identical -> I:173
PR:194	list		0	KEPT byte-identical -> I:174
PR:195	list		0	KEPT byte-identical -> I:175
PR:196	list		0	PR-12 -> I:176-181
PR:197	list		0	PR-12 -> I:176-181
PR:198	list		0	PR-12 -> I:176-181
PR:199	list		0	PR-12 -> I:176-181
PR:200	list		0	PR-12 -> I:176-181
PR:201	list	any	0	PR-12 -> I:176-181
PR:202	list		0	PR-12 -> I:176-181
PR:203	list		2	PR-12 -> I:176-181
PR:204	list	every	0	PR-12 -> I:176-181
PR:205	blank		0	KEPT byte-identical -> I:182
PR:206	heading		1	KEPT byte-identical -> I:183
PR:207	blank		0	KEPT byte-identical -> I:184
PR:208	table		1	KEPT byte-identical -> I:185
PR:209	table		1	KEPT byte-identical -> I:186
PR:210	table	Every	1	KEPT byte-identical -> I:187
PR:211	table	Every	1	KEPT byte-identical -> I:188
PR:212	table		1	KEPT byte-identical -> I:189
PR:213	table		1	KEPT byte-identical -> I:190
PR:214	table	every,required,unless	1	KEPT byte-identical -> I:191
PR:215	table	Refuse	2	KEPT byte-identical -> I:192
PR:216	table	Refuse,does not	1	KEPT byte-identical -> I:193
PR:217	table		1	KEPT byte-identical -> I:194
PR:218	table	never	3	KEPT byte-identical -> I:195
PR:219	table		1	KEPT byte-identical -> I:196
PR:220	table	does not,if,refuse	2	KEPT byte-identical -> I:197
PR:221	table	if,refuse	2	KEPT byte-identical -> I:198
PR:222	table	If	1	KEPT byte-identical -> I:199
PR:223	blank		0	KEPT byte-identical -> I:200
PR:224	heading		2	KEPT byte-identical -> I:201
PR:225	blank		0	KEPT byte-identical -> I:202
PR:226	fence		1	KEPT byte-identical -> I:203
PR:227	fence		2	KEPT byte-identical -> I:204
PR:228	fence	all	1	KEPT byte-identical -> I:205
PR:229	fence		1	KEPT byte-identical -> I:206
PR:230	fence		2	KEPT byte-identical -> I:207
PR:231	fence		1	KEPT byte-identical -> I:208
PR:232	fence		1	KEPT byte-identical -> I:209
PR:233	fence	refused	1	KEPT byte-identical -> I:210
PR:234	fence	refused	1	KEPT byte-identical -> I:211
PR:235	fence		1	KEPT byte-identical -> I:212
PR:236	fence	never	1	KEPT byte-identical -> I:213
PR:237	fence		1	KEPT byte-identical -> I:214
PR:238	fence		1	KEPT byte-identical -> I:215
PR:239	fence		1	KEPT byte-identical -> I:216
PR:240	fence		1	KEPT byte-identical -> I:217
PR:241	fence		1	KEPT byte-identical -> I:218
PR:242	fence		1	KEPT byte-identical -> I:219
PR:243	fence		1	KEPT byte-identical -> I:220
PR:244	blank		0	KEPT byte-identical -> I:221
PR:245	heading		1	KEPT byte-identical -> I:222
PR:246	blank		0	KEPT byte-identical -> I:223
PR:247	prose		0	KEPT byte-identical -> I:224
PR:248	list		0	KEPT byte-identical -> I:225
PR:249	list	only	0	KEPT byte-identical -> I:226
PR:250	blank		0	KEPT byte-identical -> I:227
PR:251	prose		0	KEPT byte-identical -> I:228
PR:252	list		0	KEPT byte-identical -> I:229
PR:253	list		0	KEPT byte-identical -> I:230
PR:254	blank		0	KEPT byte-identical -> I:231
PR:255	prose		0	KEPT byte-identical -> I:232
PR:256	list		0	KEPT byte-identical -> I:233
PR:257	list		0	KEPT byte-identical -> I:234
PR:258	blank		0	KEPT byte-identical -> I:235
PR:259	heading	NOT	1	KEPT byte-identical -> I:236
PR:260	blank		0	KEPT byte-identical -> I:237
PR:261	list	Does not	0	KEPT byte-identical -> I:238
PR:262	list	Does not	0	KEPT byte-identical -> I:239
PR:263	list		0	KEPT byte-identical -> I:240
PR:264	list	Does not	0	KEPT byte-identical -> I:241
PR:265	list		0	KEPT byte-identical -> I:242
PR:266	list	does not	0	KEPT byte-identical -> I:243
PR:267	list	Does not	0	KEPT byte-identical -> I:244
PR:268	list	Does not	0	PR-13 -> I:245-247
PR:269	list		0	PR-13 -> I:245-247
PR:270	list		0	PR-13 -> I:245-247
PR:271	list		0	PR-13 -> I:245-247
PR:272	list	Does not,do not	0	KEPT byte-identical -> I:248
PR:273	list		1	KEPT byte-identical -> I:249
PR:274	list	Does not	0	KEPT byte-identical -> I:250
PR:275	list	mandatory	0	KEPT byte-identical -> I:251
PR:276	blank		0	KEPT byte-identical -> I:252
PR:277	heading	refuse	1	KEPT byte-identical -> I:253
PR:278	blank		0	KEPT byte-identical -> I:254
PR:279	list	refuse	0	KEPT byte-identical -> I:255
PR:280	list	refuse	0	KEPT byte-identical -> I:256
PR:281	list	refuse	0	KEPT byte-identical -> I:257
PR:282	list	refuse,require	0	KEPT byte-identical -> I:258
PR:283	list		0	KEPT byte-identical -> I:259
PR:284	list	refuse	0	KEPT byte-identical -> I:260
PR:285	list	refuse	0	KEPT byte-identical -> I:261
PR:286	list		0	KEPT byte-identical -> I:262
PR:287	list		0	KEPT byte-identical -> I:263
PR:288	list	refuse	0	KEPT byte-identical -> I:264
SL:1	frontmatter		1	KEPT byte-identical -> I:1
SL:2	frontmatter		2	KEPT byte-identical -> I:2
SL:3	frontmatter	any,only,refuses	1	KEPT byte-identical -> I:3
SL:4	frontmatter		1	KEPT byte-identical -> I:4
SL:5	blank		0	KEPT byte-identical -> I:5
SL:6	heading		1	KEPT byte-identical -> I:6
SL:7	blank		0	KEPT byte-identical -> I:7
SL:8	heading		1	KEPT byte-identical -> I:8
SL:9	blank		0	KEPT byte-identical -> I:9
SL:10	prose	only	0	KEPT byte-identical -> I:10
SL:11	blank		0	KEPT byte-identical -> I:11
SL:12	list	every	0	KEPT byte-identical -> I:12
SL:13	list		0	KEPT byte-identical -> I:13
SL:14	list		2	KEPT byte-identical -> I:14
SL:15	blank		0	KEPT byte-identical -> I:15
SL:16	prose	NOT	0	KEPT byte-identical -> I:16
SL:17	blank		0	KEPT byte-identical -> I:17
SL:18	list		0	KEPT byte-identical -> I:18
SL:19	list		0	KEPT byte-identical -> I:19
SL:20	list		0	KEPT byte-identical -> I:20
SL:21	blank		0	KEPT byte-identical -> I:21
SL:22	prose		0	KEPT byte-identical -> I:22
SL:23	blank		0	KEPT byte-identical -> I:23
SL:24	heading		1	KEPT byte-identical -> I:24
SL:25	blank		0	KEPT byte-identical -> I:25
SL:26	list		0	KEPT byte-identical -> I:26
SL:27	list		0	KEPT byte-identical -> I:27
SL:28	list		0	KEPT byte-identical -> I:28
SL:29	list		0	KEPT byte-identical -> I:29
SL:30	blank		0	KEPT byte-identical -> I:30
SL:31	prose	NOT	0	KEPT byte-identical -> I:31
SL:32	list		0	KEPT byte-identical -> I:32
SL:33	list		1	KEPT byte-identical -> I:33
SL:34	list		0	KEPT byte-identical -> I:34
SL:35	list		0	KEPT byte-identical -> I:35
SL:36	blank		0	KEPT byte-identical -> I:36
SL:37	heading		1	KEPT byte-identical -> I:37
SL:38	blank		0	KEPT byte-identical -> I:38
SL:39	prose	Default	0	KEPT byte-identical -> I:39
SL:40	blank		0	KEPT byte-identical -> I:40
SL:41	list	do not	0	KEPT byte-identical -> I:41
SL:42	list	default	0	KEPT byte-identical -> I:42
SL:43	list	if	0	KEPT byte-identical -> I:43
SL:44	list	If,any,refuse	0	KEPT byte-identical -> I:44
SL:45	list		0	KEPT byte-identical -> I:45
SL:46	list	never	0	KEPT byte-identical -> I:46
SL:47	blank		0	KEPT byte-identical -> I:47
SL:48	prose	If,default	0	KEPT byte-identical -> I:48
SL:49	blank		0	KEPT byte-identical -> I:49
SL:50	heading	required	1	KEPT byte-identical -> I:50
SL:51	blank		0	KEPT byte-identical -> I:51
SL:52	list		0	KEPT byte-identical -> I:52
SL:53	list		1	KEPT byte-identical -> I:53
SL:54	list	only	0	KEPT byte-identical -> I:54
SL:55	list	Never	0	KEPT byte-identical -> I:55
SL:56	blank		0	KEPT byte-identical -> I:56
SL:57	prose	If,refuse	0	KEPT byte-identical -> I:57
SL:58	prose		0	KEPT byte-identical -> I:58
SL:59	blank		0	KEPT byte-identical -> I:59
SL:60	heading		1	KEPT byte-identical -> I:60
SL:61	blank		0	KEPT byte-identical -> I:61
SL:62	prose	never	0	KEPT byte-identical -> I:62
SL:63	blank		0	KEPT byte-identical -> I:63
SL:64	list		0	KEPT byte-identical -> I:64
SL:65	list		0	KEPT byte-identical -> I:65
SL:66	list		0	KEPT byte-identical -> I:66
SL:67	list		0	KEPT byte-identical -> I:67
SL:68	list		0	KEPT byte-identical -> I:68
SL:69	blank		0	KEPT byte-identical -> I:69
SL:70	prose	If	0	KEPT byte-identical -> I:70
SL:71	prose	Do not,stop	0	KEPT byte-identical -> I:71
SL:72	blank		0	KEPT byte-identical -> I:72
SL:73	heading		1	KEPT byte-identical -> I:73
SL:74	blank		0	KEPT byte-identical -> I:74
SL:75	prose		0	KEPT byte-identical -> I:75
SL:76	prose		0	KEPT byte-identical -> I:76
SL:77	prose		0	KEPT byte-identical -> I:77
SL:78	prose		0	KEPT byte-identical -> I:78
SL:79	blank		0	KEPT byte-identical -> I:79
SL:80	list		0	KEPT byte-identical -> I:80
SL:81	list	every	1	KEPT byte-identical -> I:81
SL:82	list		0	KEPT byte-identical -> I:82
SL:83	list		0	KEPT byte-identical -> I:83
SL:84	list	every	0	KEPT byte-identical -> I:84
SL:85	list		3	KEPT byte-identical -> I:85
SL:86	list	If,only	1	KEPT byte-identical -> I:86
SL:87	list		1	KEPT byte-identical -> I:87
SL:88	list	any	0	KEPT byte-identical -> I:88
SL:89	list		1	KEPT byte-identical -> I:89
SL:90	list		2	KEPT byte-identical -> I:90
SL:91	list		0	KEPT byte-identical -> I:91
SL:92	list	If,stop	0	KEPT byte-identical -> I:92
SL:93	list	do not	0	KEPT byte-identical -> I:93
SL:94	blank		0	KEPT byte-identical -> I:94
SL:95	heading		1	KEPT byte-identical -> I:95
SL:96	blank		0	KEPT byte-identical -> I:96
SL:97	prose		0	KEPT byte-identical -> I:97
SL:98	prose		0	KEPT byte-identical -> I:98
SL:99	blank		0	KEPT byte-identical -> I:99
SL:100	list		0	KEPT byte-identical -> I:100
SL:101	list		0	KEPT byte-identical -> I:101
SL:102	list	only	0	KEPT byte-identical -> I:102
SL:103	blank		0	KEPT byte-identical -> I:103
SL:104	prose	if,only	0	KEPT byte-identical -> I:104
SL:105	prose		0	KEPT byte-identical -> I:105
SL:106	blank		0	KEPT byte-identical -> I:106
SL:107	prose	Exception	1	KEPT byte-identical -> I:107
SL:108	prose		1	KEPT byte-identical -> I:108
SL:109	prose	NOT	0	KEPT byte-identical -> I:109
SL:110	prose	if	0	KEPT byte-identical -> I:110
SL:111	prose		2	KEPT byte-identical -> I:111
SL:112	prose	verbatim	1	KEPT byte-identical -> I:112
SL:113	prose	STOP,if	0	KEPT byte-identical -> I:113
SL:114	prose	does not	1	KEPT byte-identical -> I:114
SL:115	blank		0	KEPT byte-identical -> I:115
SL:116	prose	any	0	KEPT byte-identical -> I:116
SL:117	prose		0	KEPT byte-identical -> I:117
SL:118	prose	does not	0	KEPT byte-identical -> I:118
SL:119	prose		0	KEPT byte-identical -> I:119
SL:120	blank		0	KEPT byte-identical -> I:120
SL:121	prose		0	SL-1 -> (none)
SL:122	prose		0	SL-1 -> (none)
SL:123	prose		0	SL-1 -> (none)
SL:124	prose		0	SL-1 -> (none)
SL:125	prose		0	SL-1 -> (none)
SL:126	prose		0	SL-1 -> (none)
SL:127	prose		0	SL-1 -> (none)
SL:128	prose		0	SL-1 -> (none)
SL:129	prose		0	SL-1 -> (none)
SL:130	prose		0	SL-1 -> (none)
SL:131	blank		0	SL-1 -> (none)
SL:132	prose		1	KEPT byte-identical -> I:121
SL:133	prose		1	KEPT byte-identical -> I:122
SL:134	prose		0	KEPT byte-identical -> I:123
SL:135	prose		0	KEPT byte-identical -> I:124
SL:136	prose		0	KEPT byte-identical -> I:125
SL:137	prose	every	0	KEPT byte-identical -> I:126
SL:138	prose	only	0	KEPT byte-identical -> I:127
SL:139	prose		0	KEPT byte-identical -> I:128
SL:140	blank		0	KEPT byte-identical -> I:129
SL:141	heading	fail-closed	1	KEPT byte-identical -> I:130
SL:142	blank		0	KEPT byte-identical -> I:131
SL:143	prose	NOT	0	KEPT byte-identical -> I:132
SL:144	prose		0	KEPT byte-identical -> I:133
SL:145	blank		0	KEPT byte-identical -> I:134
SL:146	list		1	KEPT byte-identical -> I:135
SL:147	list		3	KEPT byte-identical -> I:136
SL:148	list		0	KEPT byte-identical -> I:137
SL:149	list	verbatim	0	KEPT byte-identical -> I:138
SL:150	list		0	KEPT byte-identical -> I:139
SL:151	blank		0	KEPT byte-identical -> I:140
SL:152	prose		0	KEPT byte-identical -> I:141
SL:153	blank		0	KEPT byte-identical -> I:142
SL:154	list	If,all,refuse	1	KEPT byte-identical -> I:143
SL:155	list	Do not,stop	0	KEPT byte-identical -> I:144
SL:156	list		0	KEPT byte-identical -> I:145
SL:157	list	If	1	KEPT byte-identical -> I:146
SL:158	list	refuse,stop	0	KEPT byte-identical -> I:147
SL:159	list		0	KEPT byte-identical -> I:148
SL:160	list	If,refuse,stop	0	KEPT byte-identical -> I:149
SL:161	list		0	KEPT byte-identical -> I:150
SL:162	blank		0	KEPT byte-identical -> I:151
SL:163	prose	never	0	KEPT byte-identical -> I:152
SL:164	prose		1	KEPT byte-identical -> I:153
SL:165	blank		0	KEPT byte-identical -> I:154
SL:166	prose	If	0	KEPT byte-identical -> I:155
SL:167	prose		2	KEPT byte-identical -> I:156
SL:168	prose		0	KEPT byte-identical -> I:157
SL:169	prose	exception	1	KEPT byte-identical -> I:158
SL:170	prose		2	KEPT byte-identical -> I:159
SL:171	prose	only	0	KEPT byte-identical -> I:160
SL:172	prose		0	KEPT byte-identical -> I:161
SL:173	prose	only	0	KEPT byte-identical -> I:162
SL:174	prose		0	KEPT byte-identical -> I:163
SL:175	prose	Any	0	KEPT byte-identical -> I:164
SL:176	prose	exception	0	KEPT byte-identical -> I:165
SL:177	blank		0	KEPT byte-identical -> I:166
SL:178	heading		1	KEPT byte-identical -> I:167
SL:179	blank		0	KEPT byte-identical -> I:168
SL:180	heading		1	KEPT byte-identical -> I:169
SL:181	blank		0	KEPT byte-identical -> I:170
SL:182	list		0	KEPT byte-identical -> I:171
SL:183	list		0	KEPT byte-identical -> I:172
SL:184	list		1	KEPT byte-identical -> I:173
SL:185	list		1	KEPT byte-identical -> I:174
SL:186	list	only	0	KEPT byte-identical -> I:175
SL:187	list		0	KEPT byte-identical -> I:176
SL:188	list		0	KEPT byte-identical -> I:177
SL:189	list		1	KEPT byte-identical -> I:178
SL:190	list		0	KEPT byte-identical -> I:179
SL:191	list		0	KEPT byte-identical -> I:180
SL:192	list		0	KEPT byte-identical -> I:181
SL:193	blank		0	KEPT byte-identical -> I:182
SL:194	heading		1	KEPT byte-identical -> I:183
SL:195	blank		0	KEPT byte-identical -> I:184
SL:196	table		1	KEPT byte-identical -> I:185
SL:197	table		1	KEPT byte-identical -> I:186
SL:198	table	Stop	1	KEPT byte-identical -> I:187
SL:199	table	Stop	1	KEPT byte-identical -> I:188
SL:200	table	Stop	3	KEPT byte-identical -> I:189
SL:201	table	Stop	1	KEPT byte-identical -> I:190
SL:202	table	Every,Refuse	2	KEPT byte-identical -> I:191
SL:203	table	Refuse	1	KEPT byte-identical -> I:192
SL:204	table	If,Refuse,all,fail closed,refuse,unless	4	KEPT byte-identical -> I:193
SL:205	table	Refuse,only,unless	1	KEPT byte-identical -> I:194
SL:206	table	If,Refuse	1	KEPT byte-identical -> I:195
SL:207	blank		0	KEPT byte-identical -> I:196
SL:208	heading		2	KEPT byte-identical -> I:197
SL:209	blank		0	KEPT byte-identical -> I:198
SL:210	fence		1	KEPT byte-identical -> I:199
SL:211	fence		2	KEPT byte-identical -> I:200
SL:212	fence		1	KEPT byte-identical -> I:201
SL:213	fence		1	KEPT byte-identical -> I:202
SL:214	fence		3	KEPT byte-identical -> I:203
SL:215	fence		1	KEPT byte-identical -> I:204
SL:216	fence		1	KEPT byte-identical -> I:205
SL:217	fence		1	KEPT byte-identical -> I:206
SL:218	fence		2	KEPT byte-identical -> I:207
SL:219	fence		3	KEPT byte-identical -> I:208
SL:220	fence		1	KEPT byte-identical -> I:209
SL:221	fence		1	KEPT byte-identical -> I:210
SL:222	fence		1	KEPT byte-identical -> I:211
SL:223	fence	only	1	KEPT byte-identical -> I:212
SL:224	fence		1	KEPT byte-identical -> I:213
SL:225	blank		0	KEPT byte-identical -> I:214
SL:226	heading		1	KEPT byte-identical -> I:215
SL:227	blank		0	KEPT byte-identical -> I:216
SL:228	prose		0	KEPT byte-identical -> I:217
SL:229	list		0	KEPT byte-identical -> I:218
SL:230	list		0	KEPT byte-identical -> I:219
SL:231	blank		0	KEPT byte-identical -> I:220
SL:232	prose		0	KEPT byte-identical -> I:221
SL:233	list	only	0	KEPT byte-identical -> I:222
SL:234	list		0	KEPT byte-identical -> I:223
SL:235	blank		0	KEPT byte-identical -> I:224
SL:236	prose		0	KEPT byte-identical -> I:225
SL:237	blank		0	KEPT byte-identical -> I:226
SL:238	heading	NOT	1	KEPT byte-identical -> I:227
SL:239	blank		0	KEPT byte-identical -> I:228
SL:240	list	Does not	0	KEPT byte-identical -> I:229
SL:241	list	Does not,If	0	KEPT byte-identical -> I:230
SL:242	list	requires	0	KEPT byte-identical -> I:231
SL:243	list		0	SL-2 -> I:232-233
SL:244	list	Does not	1	KEPT byte-identical -> I:234
SL:245	list		0	KEPT byte-identical -> I:235
SL:246	list	Does not,any	0	KEPT byte-identical -> I:236
SL:247	list	Does not	0	KEPT byte-identical -> I:237
SL:248	list	Does not	2	KEPT byte-identical -> I:238
SL:249	blank		0	KEPT byte-identical -> I:239
SL:250	heading	refuse	1	KEPT byte-identical -> I:240
SL:251	blank		0	KEPT byte-identical -> I:241
SL:252	list	refuse	0	KEPT byte-identical -> I:242
SL:253	list	refuse	0	KEPT byte-identical -> I:243
SL:254	list	refuse	2	KEPT byte-identical -> I:244
SL:255	list		2	KEPT byte-identical -> I:245
SL:256	list	all,fail closed,refuse	0	KEPT byte-identical -> I:246
SL:257	list	refuse,require	0	KEPT byte-identical -> I:247
SL:258	list		0	KEPT byte-identical -> I:248
SL:259	list	refuse	0	KEPT byte-identical -> I:249
SL:260	list	refuse	0	KEPT byte-identical -> I:250
SL:261	list	refuse	0	KEPT byte-identical -> I:251
SL:262	list		0	KEPT byte-identical -> I:252
SL:263	list	refuse	0	KEPT byte-identical -> I:253
RT:1	heading		1	KEPT byte-identical -> I:1
RT:2	blank		0	KEPT byte-identical -> I:2
RT:3	prose		0	KEPT byte-identical -> I:3
RT:4	prose		0	KEPT byte-identical -> I:4
RT:5	blank		0	KEPT byte-identical -> I:5
RT:6	prose	Every,MUST	0	KEPT byte-identical -> I:6
RT:7	prose		0	KEPT byte-identical -> I:7
RT:8	prose		0	KEPT byte-identical -> I:8
RT:9	prose	MUST	0	KEPT byte-identical -> I:9
RT:10	prose		0	KEPT byte-identical -> I:10
RT:11	blank		0	KEPT byte-identical -> I:11
RT:12	prose		2	KEPT byte-identical -> I:12
RT:13	prose		1	KEPT byte-identical -> I:13
RT:14	prose		0	KEPT byte-identical -> I:14
RT:15	prose		3	KEPT byte-identical -> I:15
RT:16	prose	does not	0	KEPT byte-identical -> I:16
RT:17	prose	only	0	KEPT byte-identical -> I:17
RT:18	prose	requires	0	KEPT byte-identical -> I:18
RT:19	blank		0	KEPT byte-identical -> I:19
RT:20	prose	NOT	1	KEPT byte-identical -> I:20
RT:21	prose	NOT	0	KEPT byte-identical -> I:21
RT:22	blank		0	RT-1 -> (none)
RT:23	prose		0	RT-1 -> (none)
RT:24	blank		0	KEPT byte-identical -> I:22
RT:25	heading		1	KEPT byte-identical -> I:23
RT:26	blank		0	KEPT byte-identical -> I:24
RT:27	heading		1	KEPT byte-identical -> I:25
RT:28	blank		0	KEPT byte-identical -> I:26
RT:29	prose		0	KEPT byte-identical -> I:27
RT:30	list		0	KEPT byte-identical -> I:28
RT:31	list		0	KEPT byte-identical -> I:29
RT:32	list		0	KEPT byte-identical -> I:30
RT:33	list		0	KEPT byte-identical -> I:31
RT:34	list		0	KEPT byte-identical -> I:32
RT:35	blank		0	KEPT byte-identical -> I:33
RT:36	prose		0	KEPT byte-identical -> I:34
RT:37	prose		0	KEPT byte-identical -> I:35
RT:38	blank		0	KEPT byte-identical -> I:36
RT:39	heading		1	KEPT byte-identical -> I:37
RT:40	blank		0	KEPT byte-identical -> I:38
RT:41	prose		0	KEPT byte-identical -> I:39
RT:42	prose		0	KEPT byte-identical -> I:40
RT:43	list		0	KEPT byte-identical -> I:41
RT:44	list		0	KEPT byte-identical -> I:42
RT:45	list		0	KEPT byte-identical -> I:43
RT:46	list		0	KEPT byte-identical -> I:44
RT:47	list		0	KEPT byte-identical -> I:45
RT:48	list		0	KEPT byte-identical -> I:46
RT:49	blank		0	KEPT byte-identical -> I:47
RT:50	heading		1	KEPT byte-identical -> I:48
RT:51	blank		0	KEPT byte-identical -> I:49
RT:52	prose		0	KEPT byte-identical -> I:50
RT:53	blank		0	KEPT byte-identical -> I:51
RT:54	fence		1	KEPT byte-identical -> I:52
RT:55	fence		1	KEPT byte-identical -> I:53
RT:56	fence		1	KEPT byte-identical -> I:54
RT:57	fence		1	KEPT byte-identical -> I:55
RT:58	fence		1	KEPT byte-identical -> I:56
RT:59	fence		1	KEPT byte-identical -> I:57
RT:60	fence		1	KEPT byte-identical -> I:58
RT:61	blank		0	KEPT byte-identical -> I:59
RT:62	prose	every	0	KEPT byte-identical -> I:60
RT:63	prose		0	KEPT byte-identical -> I:61
RT:64	prose		0	KEPT byte-identical -> I:62
RT:65	blank		0	KEPT byte-identical -> I:63
RT:66	prose	If	0	KEPT byte-identical -> I:64
RT:67	prose	do not	0	KEPT byte-identical -> I:65
RT:68	blank		0	KEPT byte-identical -> I:66
RT:69	heading		1	KEPT byte-identical -> I:67
RT:70	blank		0	KEPT byte-identical -> I:68
RT:71	prose		0	KEPT byte-identical -> I:69
RT:72	prose	any,if	0	KEPT byte-identical -> I:70
RT:73	prose		0	KEPT byte-identical -> I:71
RT:74	prose	All	0	KEPT byte-identical -> I:72
RT:75	prose	Do not	0	KEPT byte-identical -> I:73
RT:76	blank		0	KEPT byte-identical -> I:74
RT:77	prose		0	KEPT byte-identical -> I:75
RT:78	prose		0	KEPT byte-identical -> I:76
RT:79	prose		0	KEPT byte-identical -> I:77
RT:80	blank		0	KEPT byte-identical -> I:78
RT:81	prose		0	RT-2 -> (none)
RT:82	blank		0	RT-2 -> (none)
RT:83	heading		1	KEPT byte-identical -> I:79
RT:84	blank		0	KEPT byte-identical -> I:80
RT:85	prose		0	KEPT byte-identical -> I:81
RT:86	blank		0	KEPT byte-identical -> I:82
RT:87	list	Every	0	KEPT byte-identical -> I:83
RT:88	list		0	KEPT byte-identical -> I:84
RT:89	list		0	KEPT byte-identical -> I:85
RT:90	list		0	KEPT byte-identical -> I:86
RT:91	list	Every	0	KEPT byte-identical -> I:87
RT:92	list	Every	0	KEPT byte-identical -> I:88
RT:93	list		0	KEPT byte-identical -> I:89
RT:94	list	Every	0	KEPT byte-identical -> I:90
RT:95	list	Every	0	KEPT byte-identical -> I:91
RT:96	list		0	RT-3 -> I:92-95
RT:97	list		0	RT-3 -> I:92-95
RT:98	list		0	RT-3 -> I:92-95
RT:99	list		0	RT-3 -> I:92-95
RT:100	list	every	0	KEPT byte-identical -> I:96
RT:101	list		0	KEPT byte-identical -> I:97
RT:102	list	only	0	KEPT byte-identical -> I:98
RT:103	list		0	KEPT byte-identical -> I:99
RT:104	list		0	KEPT byte-identical -> I:100
RT:105	list	only	0	KEPT byte-identical -> I:101
RT:106	list		0	KEPT byte-identical -> I:102
RT:107	blank		0	KEPT byte-identical -> I:103
RT:108	prose		0	RT-4 -> (none)
RT:109	blank		0	RT-4 -> (none)
RT:110	heading		1	KEPT byte-identical -> I:104
RT:111	blank		0	KEPT byte-identical -> I:105
RT:112	list	only	0	KEPT byte-identical -> I:106
RT:113	list		0	KEPT byte-identical -> I:107
RT:114	list		0	KEPT byte-identical -> I:108
RT:115	list	do not	0	KEPT byte-identical -> I:109
RT:116	list		0	KEPT byte-identical -> I:110
RT:117	list		0	RT-5 -> I:111-111
RT:118	list		0	RT-5 -> I:111-111
RT:119	list		0	RT-5 -> I:111-111
RT:120	list	Do not	0	KEPT byte-identical -> I:112
RT:121	list	does not,require	0	KEPT byte-identical -> I:113
RT:122	list	unless	0	KEPT byte-identical -> I:114
RT:123	list		0	KEPT byte-identical -> I:115
RT:124	blank		0	RT-6 -> (none)
RT:125	prose		0	RT-6 -> (none)
RT:126	blank		0	KEPT byte-identical -> I:116
RT:127	heading		1	KEPT byte-identical -> I:117
RT:128	blank		0	KEPT byte-identical -> I:118
RT:129	prose	If	0	KEPT byte-identical -> I:119
RT:130	prose		0	KEPT byte-identical -> I:120
RT:131	blank		0	KEPT byte-identical -> I:121
RT:132	fence		1	KEPT byte-identical -> I:122
RT:133	fence		1	KEPT byte-identical -> I:123
RT:134	blank		1	KEPT byte-identical -> I:124
RT:135	fence		1	KEPT byte-identical -> I:125
RT:136	fence	must not,only	1	KEPT byte-identical -> I:126
RT:137	fence		1	KEPT byte-identical -> I:127
RT:138	fence		1	KEPT byte-identical -> I:128
RT:139	blank		0	KEPT byte-identical -> I:129
RT:140	prose	only	0	KEPT byte-identical -> I:130
RT:141	blank		0	RT-7 -> (none)
RT:142	prose		0	RT-7 -> (none)
RT:143	blank		0	KEPT byte-identical -> I:131
RT:144	heading	required	1	KEPT byte-identical -> I:132
RT:145	blank		0	KEPT byte-identical -> I:133
RT:146	prose	every	0	KEPT byte-identical -> I:134
RT:147	prose		0	KEPT byte-identical -> I:135
RT:148	prose		1	KEPT byte-identical -> I:136
RT:149	prose		0	KEPT byte-identical -> I:137
RT:150	prose		0	KEPT byte-identical -> I:138
RT:151	prose		2	KEPT byte-identical -> I:139
RT:152	prose		0	KEPT byte-identical -> I:140
RT:153	prose	required	0	KEPT byte-identical -> I:141
RT:154	prose		0	KEPT byte-identical -> I:142
RT:155	blank		0	KEPT byte-identical -> I:143
RT:156	fence		1	KEPT byte-identical -> I:144
RT:157	fence		2	KEPT byte-identical -> I:145
RT:158	fence		2	KEPT byte-identical -> I:146
RT:159	fence		2	KEPT byte-identical -> I:147
RT:160	fence		3	KEPT byte-identical -> I:148
RT:161	fence		1	KEPT byte-identical -> I:149
RT:162	blank		0	KEPT byte-identical -> I:150
RT:163	prose		0	KEPT byte-identical -> I:151
RT:164	list	Exactly	0	KEPT byte-identical -> I:152
RT:165	list	MUST	0	KEPT byte-identical -> I:153
RT:166	list		2	KEPT byte-identical -> I:154
RT:167	list	required	0	KEPT byte-identical -> I:155
RT:168	list		0	KEPT byte-identical -> I:156
RT:169	list		0	KEPT byte-identical -> I:157
RT:170	list		4	KEPT byte-identical -> I:158
RT:171	list	MUST	0	KEPT byte-identical -> I:159
RT:172	list		0	KEPT byte-identical -> I:160
RT:173	list	MUST	0	KEPT byte-identical -> I:161
RT:174	list	if	0	KEPT byte-identical -> I:162
RT:175	list		0	KEPT byte-identical -> I:163
RT:176	list		0	KEPT byte-identical -> I:164
RT:177	list		0	KEPT byte-identical -> I:165
RT:178	list		0	KEPT byte-identical -> I:166
RT:179	list		1	KEPT byte-identical -> I:167
RT:180	list		0	KEPT byte-identical -> I:168
RT:181	list		0	KEPT byte-identical -> I:169
RT:182	list		0	KEPT byte-identical -> I:170
RT:183	list		0	KEPT byte-identical -> I:171
RT:184	list	refused	1	KEPT byte-identical -> I:172
RT:185	list		0	KEPT byte-identical -> I:173
RT:186	blank		0	KEPT byte-identical -> I:174
RT:187	prose		0	KEPT byte-identical -> I:175
RT:188	prose	if	0	KEPT byte-identical -> I:176
RT:189	blank		0	KEPT byte-identical -> I:177
RT:190	prose		0	RT-8 -> (none)
RT:191	blank		0	RT-8 -> (none)
RT:192	heading	required	1	KEPT byte-identical -> I:178
RT:193	blank		0	KEPT byte-identical -> I:179
RT:194	prose	any	0	KEPT byte-identical -> I:180
RT:195	prose		0	KEPT byte-identical -> I:181
RT:196	prose		0	KEPT byte-identical -> I:182
RT:197	prose		0	KEPT byte-identical -> I:183
RT:198	prose	MUST,all	0	KEPT byte-identical -> I:184
RT:199	blank		0	KEPT byte-identical -> I:185
RT:200	fence		1	KEPT byte-identical -> I:186
RT:201	fence		1	KEPT byte-identical -> I:187
RT:202	blank		1	KEPT byte-identical -> I:188
RT:203	fence		1	KEPT byte-identical -> I:189
RT:204	blank		1	KEPT byte-identical -> I:190
RT:205	fence	any,if	1	KEPT byte-identical -> I:191
RT:206	fence		1	KEPT byte-identical -> I:192
RT:207	fence	if	1	KEPT byte-identical -> I:193
RT:208	fence		1	KEPT byte-identical -> I:194
RT:209	fence		1	KEPT byte-identical -> I:195
RT:210	blank		0	KEPT byte-identical -> I:196
RT:211	prose		0	KEPT byte-identical -> I:197
RT:212	blank		0	KEPT byte-identical -> I:198
RT:213	list		0	KEPT byte-identical -> I:199
RT:214	list		0	KEPT byte-identical -> I:200
RT:215	list		0	KEPT byte-identical -> I:201
RT:216	list		0	KEPT byte-identical -> I:202
RT:217	list	NOT	0	KEPT byte-identical -> I:203
RT:218	list		0	KEPT byte-identical -> I:204
RT:219	blank		0	KEPT byte-identical -> I:205
RT:220	list	any,if	0	KEPT byte-identical -> I:206
RT:221	list		0	KEPT byte-identical -> I:207
RT:222	list		0	KEPT byte-identical -> I:208
RT:223	list		0	KEPT byte-identical -> I:209
RT:224	list		0	KEPT byte-identical -> I:210
RT:225	blank		0	KEPT byte-identical -> I:211
RT:226	list		0	KEPT byte-identical -> I:212
RT:227	list		0	KEPT byte-identical -> I:213
RT:228	list		0	KEPT byte-identical -> I:214
RT:229	list	every	0	KEPT byte-identical -> I:215
RT:230	list	at least	0	KEPT byte-identical -> I:216
RT:231	list		0	KEPT byte-identical -> I:217
RT:232	blank		0	KEPT byte-identical -> I:218
RT:233	list	at least	0	KEPT byte-identical -> I:219
RT:234	list		0	KEPT byte-identical -> I:220
RT:235	list		0	KEPT byte-identical -> I:221
RT:236	blank		0	KEPT byte-identical -> I:222
RT:237	prose		0	RT-9 -> (none)
RT:238	prose		0	RT-9 -> (none)
RT:239	prose		0	RT-9 -> (none)
RT:240	prose	all	0	RT-9 -> (none)
RT:241	prose	any	0	RT-9 -> (none)
RT:242	prose		0	RT-9 -> (none)
RT:243	prose		0	RT-9 -> (none)
RT:244	prose		0	RT-9 -> (none)
RT:245	prose	all	0	RT-9 -> (none)
RT:246	blank		0	RT-9 -> (none)
RT:247	prose	If	0	KEPT byte-identical -> I:223
RT:248	blank		0	KEPT byte-identical -> I:224
RT:249	fence		1	KEPT byte-identical -> I:225
RT:250	fence		1	KEPT byte-identical -> I:226
RT:251	blank		1	KEPT byte-identical -> I:227
RT:252	fence		1	KEPT byte-identical -> I:228
RT:253	fence		1	KEPT byte-identical -> I:229
RT:254	blank		0	KEPT byte-identical -> I:230
RT:255	prose	do not	0	KEPT byte-identical -> I:231
```

## 5. Class-H one-to-one manifest (R4, p4, p4C, p9.3)

### 5.1 Checker definition and assumptions (for stage-R verification)

- Inputs: PRE = `git show <ref>:<path>`; POST = `<work>/<path>`, for the 7 payload paths.
- Occurrence counting is the s4C method (`str.find` loop = Python `str.count`, non-overlapping).
- Literal set: (a) the s4C seed, with every file the seed does not list asserted as 0.
  --check fails unless the seed equals the PRE counts. The two-line "Same-PR\nCloseout" (PC 1)
  is its own literal. B1's `SECOND-MODEL:` and `instrument not commissioned` are asserted 0 in
  all files. (b) Row-definition literals enumerated by the generator (the `EXTRA` list): every
  `LANE` and `GOVERNANCE` token (A7 complete sweep, catch-all), the A5 filename strings and
  regex, the A6 annotation words, the A8 FILES-syntax literals, `**Active PRD:**`, the two-line
  A12 mode list "RECON, DESIGN, IMPLEMENT, REVIEW,\nSTEWARD", A13 "used verbatim", the A14
  ESCALATION label and "Publish safety:", the A16 closed sets and REVIEWED STATE labels, the
  A15 SHAs, the A1 paths, B6 hook/file names scoped to CM/CH, the B7 qualifier forms, and B5
  `docs/contract/MODE_*.md`. (c) Whole lines: every line starting with `#` outside fences
  (headings; row A14/A16/A17/A18 by file), every table row `|...` (A17 V-tables, A18 hooks
  table, A16 RT), every line of every fenced block including the fence lines (A16 in PR/RT,
  A17 elsewhere: review structure, Verification Report shapes, templates), skill frontmatter
  lines 1-4 (A4), CM Ratification paragraph lines (A15), and the A16 PR review-structure label
  lines.
- ID: `H-<row>-<file>-<nnn>`, nnn = occurrence index within (row, file) in file order, ties by
  literal. Structural context: heading path = all enclosing `#` headings outside fences. Key =
  `ROW:<first cell>` for a table row; `LI:<n>` for a top-level list item (n = item ordinal
  since the last heading; continuation lines inherit it); `F<k>:<offset>` for fence k line
  offset; `FM:<line>` for frontmatter; `HDG` for heading lines; empty for other prose.
- --check fails non-zero on any of: missing/added ID, changed sha256, heading path, key or
  per-file cardinality (line numbers may differ), a seed mismatch, or a `grep '^#'`
  heading-list difference PRE vs POST. Output: `ID file sha256 heading-path key line
  cardinality` (TSV).
- Known limits, stated for the reviewer: a literal the list does not name is unprotected by
  hash and falls to the class-L ledger (p5). Prose keys carry no paragraph ordinal, so moving
  an H-bearing sentence within the same heading section is not flagged. Whole fences are
  frozen, which is stricter than p4 requires.

### 5.2 Red tests (retained invariant 4)

Each case copies the 7 final payload files into a scratch tree, applies one mutation, and runs
the checker with `--ref M --check`. Result at authoring: every mutation exits 1 and the no-op
control exits 0.

| Mutation | rc | First failure reported |
|---|---|---|
| drop a `LANE` token (SL "auto-escalate LANE") | 1 | MISSING H-A7-SL-022 |
| rename a CM heading (`## Roles`) | 1 | HEADINGS CM |
| alter one byte of a PC V-row | 1 | CHANGED H-A17-PC-024 sha |
| rewrap the two-line "Same-PR\nCloseout" | 1 | CHANGED H-B3-PC-001 sha |
| add one `#NNN` occurrence in PC | 1 | ADDED H-A9-PC-011 |
| edit an RT fence line | 1 | CHANGED H-A16-RT-051 sha |
| alter Ratification SHA `8224033` | 1 | HEADINGS CM (the line starts `#220`) + MISSING |
| alter PA frontmatter `name:` | 1 | MISSING H-A2-PA-001 |
| alter SL `## Verification Report shape` | 1 | HEADINGS SL |
| alter a CH hooks-table row | 1 | CHANGED H-A18-CH-007 sha |
| add an `audits/EXECUTION_DOCTRINE.md` occurrence in PR | 1 | ADDED H-B7-PR-005 |
| reorder two PC Does-NOT-do items | 1 | CHANGED H-A10-PC-016 key |
| truncate the PC item carrying `Test baseline` | 1 | MISSING H-A10-PC-017 |
| alter the PR `DRIFT CHECK` structure line | 1 | MISSING (A16) |
| insert the B1 `SECOND-MODEL:` prefix into RT | 1 | ADDED H-B1-RT-001 |
| seed mismatch (`#NNN` seed PC 6 -> 5, checker copy) | 1 | SEED |
| no-op control | 0 | - |

### 5.3 Result on the final worktree

`python3 h_manifest.py --ref M --work . --out-pre PRE.tsv --out-post POST.tsv --check`:
`PRE ids=553 POST ids=553 errors=0`, exit 0 (checker file sha256 b5ab90116a273ee7a96d11ca2d3a199aba6a3c4b4976317ea58c36bb92b7856e; the fenced
block in section 6 is byte-identical to it). sha256(PRE.tsv) f418f5a277b1c041e153ee0e4ff97373592b835b9de41157cedbadc7f4081bd7, sha256(POST.tsv)
c31d9b5f8653b70a164f69482f2516408983ab7da1e90203b4f341c76c08a36b. PRD VALIDATION command (repo root):

```sh
M=05c9c0c2ff6433d0740149e1e7ff318997a03df2
awk '/^```python h_manifest/{f=1;next} /^```/{f=0} f' audits/prompt-surface-compaction-material-packet-2026-09/RULE_LEDGER_PRD-347.md > /tmp/h_manifest.py && python3 /tmp/h_manifest.py --ref "$M" --work . --out-pre /tmp/PRE.tsv --out-post /tmp/POST.tsv --check
```

### 5.4 PRE manifest (from M)

```tsv
H-A11-CM-001	CLAUDE.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:10	141	1
H-A12-CM-001	CLAUDE.md	2ab9818f93b1cb302e3004a42db83b7795de9ddb396a685db7536c16926a8a7a	# CLAUDE.md > ## Modes (Layer 2)		71	1
H-A12-CM-002	CLAUDE.md	dd24f4039d494cc1f0a47b5d33d2ef9c2503cd7cad56a109041fabf83d1dee2d	# CLAUDE.md > ## Modes (Layer 2)		72	1
H-A12-CM-003	CLAUDE.md	a56cc5066bfa8699a7ff3dcbb3b5e837010a0b4a4f0e9d933e0b0df2bf6fb525	# CLAUDE.md > ## Modes (Layer 2)		73	1
H-A13-CM-001	CLAUDE.md	4c6a5dbb16174b3d545952f69df203330ad34889e288b31b5c3b56bc1409f1f9	# CLAUDE.md > ## Session start		151	1
H-A13-CM-002	CLAUDE.md	270f1d910823c3ad2a27bd2ad9fb5a0864ad297764d2fd7f890e2fd27e9d1a95	# CLAUDE.md > ## Session start		151	1
H-A13-CM-003	CLAUDE.md	ea5ca4ca3591e50f7b9f33faf16e3d99e243a65e35521bfb13344b693872075a	# CLAUDE.md > ## Session start		152	1
H-A13-CM-004	CLAUDE.md	32107fe5eebe12df8280125d5ff78519f86854704e7bf94227110ee17a74c09f	# CLAUDE.md > ## Session start		152	1
H-A14-CM-001	CLAUDE.md	b2788d7144b6d2cda95eda69f4456c3666f40ecb566f82d038a10ae9a97af2d5	# CLAUDE.md	HDG	1	1
H-A14-CM-002	CLAUDE.md	61e9f61ec5d02b78d9604b8f72e7aca071031cfe7c8442a944f76aa0cd39ba66	# CLAUDE.md > ## Ratification	HDG	11	1
H-A14-CM-003	CLAUDE.md	daf799c4481a60a0bc68c75e9f0d11071a292f44d03f2ed1a2ff8dfced4ed121	# CLAUDE.md > ## The wall (absolute; no charge, mode, or prompt overrides it)	HDG	19	1
H-A14-CM-004	CLAUDE.md	b5611ac15c0cfd03def2c4874be8fbff2622c099b8f28d9c270823e7b9345db0	# CLAUDE.md > ## The wall (absolute; no charge, mode, or prompt overrides it)	LI:7	39	1
H-A14-CM-005	CLAUDE.md	30493a431f3c4180181e60113018c96c24f9f8c6b01bc8725e3e8a01a21b02ae	# CLAUDE.md > ## Owner holds (exclusive to Dustin; no agent issues or infers these)	HDG	45	1
H-A14-CM-006	CLAUDE.md	a504e08469469107fca398daa452db1de42e1a7c556947fada935b61092a03da	# CLAUDE.md > ## Precedence (on genuine conflict between two applicable authorities, STOP)	HDG	55	1
H-A14-CM-007	CLAUDE.md	ffa00a4b3e57de48cda12355dc2838559a83c5daffecbd020c16c3f98a0235b1	# CLAUDE.md > ## Modes (Layer 2)	HDG	68	1
H-A14-CM-008	CLAUDE.md	ac6d273c773446e61c4ba100be863aeb8d56261042f6665457b7ab6e7f80c957	# CLAUDE.md > ## Retained invariants (bind in every mode)	HDG	83	1
H-A14-CM-009	CLAUDE.md	993e9a76aaf48701540a8971f515a7bf73a89f9d32160d275b9baf28a15a4634	# CLAUDE.md > ## Retained invariants (bind in every mode)		99	1
H-A14-CM-010	CLAUDE.md	0119af1db59c8e66643e70c3a687926478085db6b66e92c869e026e537168cd7	# CLAUDE.md > ## Roles	HDG	104	1
H-A14-CM-011	CLAUDE.md	040e5ebc4f912a6cc3175fc4d8327026f7cb5c4aa0a4478541c92fac27472840	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	HDG	124	1
H-A14-CM-012	CLAUDE.md	3288bad4a0f3a97491e231111c3fe0ab9a5f272912303df130feb71300f4e40a	# CLAUDE.md > ## Session start	HDG	146	1
H-A14-CM-013	CLAUDE.md	16b40b8d2a484e2b54b2d0e57f0e4a448d762959c9064ebcc90836298775aa1d	# CLAUDE.md > ## Context and output hygiene (standing behavior, every session)	HDG	154	1
H-A14-CM-014	CLAUDE.md	1edd85bf9a67ed33fb2eea914f2d83f115a9fdb1ff8d260d4f7fc808377efe9e	# CLAUDE.md > ## Context and output hygiene (standing behavior, every session)	LI:1	156	1
H-A14-CM-015	CLAUDE.md	2d7b716cde65fe0b172d6533a5e686a76e8eebe67b01ea6378e15fcc7dcba2d0	# CLAUDE.md > ## Anti-patterns	HDG	171	1
H-A15-CM-001	CLAUDE.md	94391f153aba278bd2c23573c32372b39b43113a2df356384ced5d6d20937eff	# CLAUDE.md > ## Ratification		13	1
H-A15-CM-002	CLAUDE.md	3025f5ddb307c7360f922179dfca5facd9c9a507aa9e362d9b0f23b8946a8dcc	# CLAUDE.md > ## Ratification		14	1
H-A15-CM-003	CLAUDE.md	a95b4dbd83a143a60a9b0a7dbce6a73a35cacaf35d9d2f096b3f20dbb2e34179	# CLAUDE.md > ## Ratification		14	1
H-A15-CM-004	CLAUDE.md	3bb2effa2aebfbb6801541c74805773681e430eae83899f9df917b7c6e95fba3	# CLAUDE.md > ## Ratification		15	1
H-A15-CM-005	CLAUDE.md	55bd2626a625d18651842113017d91d307a778fa1b191a629db63ef0274c78b0	# CLAUDE.md > ## Ratification		15	1
H-A15-CM-006	CLAUDE.md	7bba5c85e56370cb29c215ec94775b5d9a3bf0d5e4b80851800b20abf0d68f6c	# CLAUDE.md > ## Ratification		16	1
H-A15-CM-007	CLAUDE.md	8d7884e50a2f4a8b00910d19bfa2802ffe555f5db10e209d4e8e61878f61559d	# CLAUDE.md > ## Ratification		16	1
H-A15-CM-008	CLAUDE.md	0e783d1a821909ef2bccb4f0d99b1c29e592579b16ea5e33fae1750e0a1f0887	# CLAUDE.md > ## Ratification		16	1
H-A15-CM-009	CLAUDE.md	4ae32277a536f23c349afb21ded2fdef251061be1940f29d37166af965508d84	# CLAUDE.md > ## Ratification		17	1
H-A15-CM-010	CLAUDE.md	d37469a2ee1629aae9ddda1af8a4afd07c3e9dcbde5b42bc338dfbb9143a545d	# CLAUDE.md > ## Owner holds (exclusive to Dustin; no agent issues or infers these)	LI:4	52	2
H-A15-CM-011	CLAUDE.md	88191af5f0ad451de905236f651ad4680eff0bc794ed4a171e7e8140b16fb1d8	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:6	133	1
H-A15-CM-012	CLAUDE.md	d37469a2ee1629aae9ddda1af8a4afd07c3e9dcbde5b42bc338dfbb9143a545d	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:7	135	2
H-A15-CM-013	CLAUDE.md	1414b45aca9a69e1ddcebd592b76818fac5216d12f58e7c6bf604f98216e1efc	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:7	136	1
H-A15-CM-014	CLAUDE.md	09b23593d9f9580cf4e4c4f7a35610dccc9db17a31725a7bf108f056f558fba0	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:11	143	1
H-A18-CM-001	CLAUDE.md	f27ac6f39d89fe021c56900069198aa7d9968f2cd6645c00b11ffd1b78fcf546	# CLAUDE.md > ## Retained invariants (bind in every mode)		95	1
H-A7-CM-001	CLAUDE.md	1ec7904fb1ae4e2f91ca730f6cb6be360132dee919f6a21386d041ddd39d6cae	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:5	131	1
H-A7-CM-002	CLAUDE.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:5	131	1
H-B3-CM-001	CLAUDE.md	fb93b282e8608b68723b814facb03e068db62e4be93ade88c97197cbdf0d01d4	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:5	132	1
H-B3-CM-002	CLAUDE.md	919061e6c7c6dd81bb22c3c0db2a36f5e1ab54b4ebfb3b96978bf5c51d3445f5	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:5	132	1
H-B3-CM-003	CLAUDE.md	bf2b3717dfefb295aa556908f1382c03a7533a5a1e7e991a3a2413d28faf7e6d	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:5	132	1
H-B5-CM-001	CLAUDE.md	28b06784002a6f371bb4e99efa2b40da696c00e7f409fc48d231fb6e36e5354a	# CLAUDE.md > ## Precedence (on genuine conflict between two applicable authorities, STOP)	LI:6	63	1
H-B6-CM-001	CLAUDE.md	fca16cae5b0e32edfa6b55eaa32a98ffbf4a0c7d885fb585785fc83b6ea2d9c3	# CLAUDE.md > ## Retained invariants (bind in every mode)		96	1
H-B6-CM-002	CLAUDE.md	c114278ca2d65f625aedda9a17c8bef83d097f002880a43b4e81ad7bf0b1e3ec	# CLAUDE.md > ## Retained invariants (bind in every mode)		101	1
H-B6-CM-003	CLAUDE.md	7d39790f142e05b8308584856a366a2b729053f1420b4ee544da9e90ee2bbc72	# CLAUDE.md > ## Retained invariants (bind in every mode)		101	1
H-B6-CM-004	CLAUDE.md	77cf032cbbc45b8e2c8f49c7035505045f5500db9dd048c347739134633c2506	# CLAUDE.md > ## Retained invariants (bind in every mode)		102	1
H-B6-CM-005	CLAUDE.md	88636d2769930e3e701c64fbf0ef7d46810b89d9798446fee7e9c2d47597ddf8	# CLAUDE.md > ## Retained invariants (bind in every mode)		102	1
H-A11-CH-001	docs/CLAUDE_HOOKS.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard		34	1
H-A18-CH-001	docs/CLAUDE_HOOKS.md	27519bb40111622567febbcb6fc0f1c84ac74484c1559efa7e440c6b6edefd19	# Claude Code Hooks - Workflow Reference	HDG	1	1
H-A18-CH-002	docs/CLAUDE_HOOKS.md	f27ac6f39d89fe021c56900069198aa7d9968f2cd6645c00b11ffd1b78fcf546	# Claude Code Hooks - Workflow Reference		4	3
H-A18-CH-003	docs/CLAUDE_HOOKS.md	dfc54351aa6127d5f66bd281ff41483e440380f6ad7d5fec4d60a19789fa8122	# Claude Code Hooks - Workflow Reference > ## Wired hooks	HDG	7	1
H-A18-CH-004	docs/CLAUDE_HOOKS.md	c7bfd735700fc3f158ee2fdad2fca24752ffabae63dbc46d619e2396d2f3926d	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:Script	9	1
H-A18-CH-005	docs/CLAUDE_HOOKS.md	4da1ec6f47782090102dc16bda978efb5655fbf2ddce0f84ecf1faf79a930f2d	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:---	10	1
H-A18-CH-006	docs/CLAUDE_HOOKS.md	63f7c625cf69c1e6e78b3267f6a286fc4a1b73c6d4a38ef747dc007c64c2b1e1	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`protect_files.sh`	11	1
H-A18-CH-007	docs/CLAUDE_HOOKS.md	c9b57726f9b9e37a1e56c0efb803cce5812fe355d1ff61311c61845a85ffef55	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`prd_eval.sh`	12	1
H-A18-CH-008	docs/CLAUDE_HOOKS.md	03f1d2676a5ee27d57f2e89342ef1d5b5cf17e6b7372f84b8a3be2a7e23442ef	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`canonical_read_guard.sh`	13	1
H-A18-CH-009	docs/CLAUDE_HOOKS.md	f242e294cd8bf8e73e3c6a5f4d6317cd97575293a68b93eb6c8841c797d4f88a	# Claude Code Hooks - Workflow Reference > ## Wired hooks		16	1
H-A18-CH-010	docs/CLAUDE_HOOKS.md	9b5c7a8ea53163aa7fa627192315e1aa846922c450111ab5f0fc2128a497f9c7	# Claude Code Hooks - Workflow Reference > ## Wired hooks		16	1
H-A18-CH-011	docs/CLAUDE_HOOKS.md	50bba48fb4687d404479049d0fe89a3a43f663569837cd647b6866664bd9aacb	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard	HDG	19	1
H-A18-CH-012	docs/CLAUDE_HOOKS.md	f27ac6f39d89fe021c56900069198aa7d9968f2cd6645c00b11ffd1b78fcf546	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard		21	3
H-A18-CH-013	docs/CLAUDE_HOOKS.md	c42f14bd214bdcd26e9cbf9c6edb75cc6dcfc8f729cd1b5b253a43f05ebdc67b	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard		31	1
H-A18-CH-014	docs/CLAUDE_HOOKS.md	2f401cee56370841fd312ee9a02caf63b4d28b809fb6b277d3e26cbb64b7a466	# Claude Code Hooks - Workflow Reference > ## prd_eval.sh - registry-gap check	HDG	55	1
H-A18-CH-015	docs/CLAUDE_HOOKS.md	387294ffdae67c6c11733980388841d4415be458c2f345b148a6e2f5c2a8da69	# Claude Code Hooks - Workflow Reference > ## prd_eval.sh - registry-gap check		67	1
H-A18-CH-016	docs/CLAUDE_HOOKS.md	a64c32b7517eea07d265d841050ae7ada6136b3291e587ac2fbe43800a8569b2	# Claude Code Hooks - Workflow Reference > ## canonical_read_guard.sh - redundant canonical-doc re-read reminder	HDG	71	1
H-A18-CH-017	docs/CLAUDE_HOOKS.md	c065296ded4cf2ebc1df0cc1723ac3a5d7ed98c3879e3c261c0a42d6d5a58f9c	# Claude Code Hooks - Workflow Reference > ## Commit / push	HDG	81	1
H-A18-CH-018	docs/CLAUDE_HOOKS.md	f27ac6f39d89fe021c56900069198aa7d9968f2cd6645c00b11ffd1b78fcf546	# Claude Code Hooks - Workflow Reference > ## Commit / push		84	3
H-B6-CH-001	docs/CLAUDE_HOOKS.md	1b18c0911b9309b7818ba961d4d3ac4c2c9be7d914224646629fc6f12ecc7c3c	# Claude Code Hooks - Workflow Reference		4	2
H-B6-CH-002	docs/CLAUDE_HOOKS.md	6015fa7d4a3a31de670b0ee8772016e8f90f824eae3e156ad8d1cda4a5f7a201	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`protect_files.sh`	11	3
H-B6-CH-003	docs/CLAUDE_HOOKS.md	45e83e4cb495b00a7da3623fb5bfe43bbabce862262b26cbc119bd93d9130b29	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`prd_eval.sh`	12	2
H-B6-CH-004	docs/CLAUDE_HOOKS.md	d6140f5e5e98af2e060b03bf084910a46781d67b811aa2e9c8ab6987fdc4e74c	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`canonical_read_guard.sh`	13	2
H-B6-CH-005	docs/CLAUDE_HOOKS.md	6015fa7d4a3a31de670b0ee8772016e8f90f824eae3e156ad8d1cda4a5f7a201	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard	HDG	19	3
H-B6-CH-006	docs/CLAUDE_HOOKS.md	1b18c0911b9309b7818ba961d4d3ac4c2c9be7d914224646629fc6f12ecc7c3c	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard		31	2
H-B6-CH-007	docs/CLAUDE_HOOKS.md	6015fa7d4a3a31de670b0ee8772016e8f90f824eae3e156ad8d1cda4a5f7a201	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard		31	3
H-B6-CH-008	docs/CLAUDE_HOOKS.md	45e83e4cb495b00a7da3623fb5bfe43bbabce862262b26cbc119bd93d9130b29	# Claude Code Hooks - Workflow Reference > ## prd_eval.sh - registry-gap check	HDG	55	2
H-B6-CH-009	docs/CLAUDE_HOOKS.md	d6140f5e5e98af2e060b03bf084910a46781d67b811aa2e9c8ab6987fdc4e74c	# Claude Code Hooks - Workflow Reference > ## canonical_read_guard.sh - redundant canonical-doc re-read reminder	HDG	71	2
H-A11-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	110	1
H-A11-PA-002	.claude/skills/prd-authoring-verified/SKILL.md	f4f1f60a1a29b4b24265e0be159d690d6e342b65c3833d7b2f06b0dbfad60137	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	110	1
H-A14-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	1edd85bf9a67ed33fb2eea914f2d83f115a9fdb1ff8d260d4f7fc808377efe9e	# PRD Authoring with Built-in Verification > ## Tools	LI:8	159	1
H-A17-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	be0c4c3e4d16347f0c0bbf1722d1aeec9afdd8cc887f0ea9b7766428671743f0	# PRD Authoring with Built-in Verification	HDG	6	1
H-A17-PA-002	.claude/skills/prd-authoring-verified/SKILL.md	c31df17b020896f4408b594dcc87b654acc34d6cffea342410e54300430ff505	# PRD Authoring with Built-in Verification > ## Scope and boundary	HDG	8	1
H-A17-PA-003	.claude/skills/prd-authoring-verified/SKILL.md	0632f7b817601f2c4399f83a1a85ede2ad5c99cacf601e68d5b3471191771451	# PRD Authoring with Built-in Verification > ## When to trigger	HDG	26	1
H-A17-PA-004	.claude/skills/prd-authoring-verified/SKILL.md	90e48a7f751783169d5e801f211330144685188ec27ea465b4e6e633a858f180	# PRD Authoring with Built-in Verification > ## Operating modes	HDG	37	1
H-A17-PA-005	.claude/skills/prd-authoring-verified/SKILL.md	18a8b5df2208e00d1ba8e7bc8fb538a3625dbfb4e8dc25158debce2a964c237d	# PRD Authoring with Built-in Verification > ## Hard rule: no invented references	HDG	53	1
H-A17-PA-006	.claude/skills/prd-authoring-verified/SKILL.md	a2d449b06e0d38d92f7ffe6f9919e3cccb1587c59c57ce2ccd1c42f408f2991a	# PRD Authoring with Built-in Verification > ## Two-phase contract	HDG	76	1
H-A17-PA-007	.claude/skills/prd-authoring-verified/SKILL.md	b2dc9baa601a8d4b7464fcf623c472e29427f0554626f54b9de95bf9b64bda4d	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	HDG	78	1
H-A17-PA-008	.claude/skills/prd-authoring-verified/SKILL.md	0da21edcb876fd89fc8bb92d7c2e872bbf93feb24097ad037a23ab3fcb97cf93	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	HDG	98	1
H-A17-PA-009	.claude/skills/prd-authoring-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)		100	3
H-A17-PA-010	.claude/skills/prd-authoring-verified/SKILL.md	0610a4eb29cfa5edd7b763f1128ea544350f7480fec7c8f82cd55d6e104b971e	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:#	104	1
H-A17-PA-011	.claude/skills/prd-authoring-verified/SKILL.md	12af00ef4beed04e98324a76d971f94419a92b77311cf21629020e3449b8f457	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:---	105	1
H-A17-PA-012	.claude/skills/prd-authoring-verified/SKILL.md	79f77ecad50bf2b2c2bd1546d8e215aa369dd8f6a9ba87b92c3b93d9ab0d6d49	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V1	106	1
H-A17-PA-013	.claude/skills/prd-authoring-verified/SKILL.md	982414182e279823a7339e0214e04dc409ca532a9b5e95dba0b7700a51dcfd87	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V2	107	1
H-A17-PA-014	.claude/skills/prd-authoring-verified/SKILL.md	762573c2622c85f53fa0149fc843389b4dbaea8ec61207ecb2306aec3ab957bd	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	108	1
H-A17-PA-015	.claude/skills/prd-authoring-verified/SKILL.md	0b2ade07bbfcca905eee7bc31ae89c406fb619457e0eb4c0822ae9ec9c8bf90e	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	109	1
H-A17-PA-016	.claude/skills/prd-authoring-verified/SKILL.md	6816f0b71f9c5027bed363429eeb6a925e0dd692b3f363027f5823f8a460a640	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	110	1
H-A17-PA-017	.claude/skills/prd-authoring-verified/SKILL.md	96eb43aca7aacf44bf34ea18939fb3fc46e3b24c7958d506a9eabe4416197142	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V6	111	1
H-A17-PA-018	.claude/skills/prd-authoring-verified/SKILL.md	d5460698e6520239f9ebb11a6cacf5e98c0d8861610aa0302ebd1a23122f88f8	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	112	1
H-A17-PA-019	.claude/skills/prd-authoring-verified/SKILL.md	16b6a19e5a3e6a4c1e899ee6e9642055ab6b860f34a63eccb6a6cb0f07132084	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	113	1
H-A17-PA-020	.claude/skills/prd-authoring-verified/SKILL.md	03b6fa2d01d8efa45d0df4e9da005ff7d5272c3862234dd323226a7a16e9e90a	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	114	1
H-A17-PA-021	.claude/skills/prd-authoring-verified/SKILL.md	47ff84a3ed75a35740ad31be122c60287278ae5bbbf8d67e3030c423bd6c76c9	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V10	115	1
H-A17-PA-022	.claude/skills/prd-authoring-verified/SKILL.md	458bea3f0da685f2ef0c57edb796ada73a563e370ed8402891fc30b20daae05c	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	HDG	117	1
H-A17-PA-023	.claude/skills/prd-authoring-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	HDG	117	3
H-A17-PA-024	.claude/skills/prd-authoring-verified/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:0	119	2
H-A17-PA-025	.claude/skills/prd-authoring-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:1	120	3
H-A17-PA-026	.claude/skills/prd-authoring-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:1	120	1
H-A17-PA-027	.claude/skills/prd-authoring-verified/SKILL.md	d1efd8b4efafd24b7e2a9b15296d9957b48fb37ab57820ca3806de27c456e3b0	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:2	121	1
H-A17-PA-028	.claude/skills/prd-authoring-verified/SKILL.md	fa444269c66fb5b00cfbc1cf26ddf044e8eb8428375d10ccbd4ccfb6621db612	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:3	122	1
H-A17-PA-029	.claude/skills/prd-authoring-verified/SKILL.md	1e96a3450bd6f864e588e5ba0d77a1c11f9537bc16ce19e101604995514068c6	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:4	123	1
H-A17-PA-030	.claude/skills/prd-authoring-verified/SKILL.md	c83a969e63c6e00130ed9b3cea9bbf3a01d88b9a7653d65e34c57f6ac34d706d	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:5	124	1
H-A17-PA-031	.claude/skills/prd-authoring-verified/SKILL.md	04bb0f68fd83c5ed89bf88ef6598934e008657b5b1c607bd6080b59fdca1541d	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:6	125	1
H-A17-PA-032	.claude/skills/prd-authoring-verified/SKILL.md	39929edabcb560d5efc9e0b20394a23c2541c574361becc0e830d856601fbfff	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:7	126	1
H-A17-PA-033	.claude/skills/prd-authoring-verified/SKILL.md	0e6d7cad41ca0c729879f20e23b8dd008dc2a0623df242fa32713d7915205dc5	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:8	127	1
H-A17-PA-034	.claude/skills/prd-authoring-verified/SKILL.md	e7e7bd3dcdc913023962ec22b0b1e0c0d6f582fe1e0bc528c6fc50ed016cda63	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:9	128	1
H-A17-PA-035	.claude/skills/prd-authoring-verified/SKILL.md	c121ca6605bb3eb1dec0b74f09748139217d972817059c520583ae24b8b071b6	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:10	129	1
H-A17-PA-036	.claude/skills/prd-authoring-verified/SKILL.md	a5397ccce07ecbbc4b875d096acff6637f74f38a8d8be1af01c75f3371e81ddf	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:11	130	1
H-A17-PA-037	.claude/skills/prd-authoring-verified/SKILL.md	25327f96b1d34b2e754c0d72d665cd130bb77444b3efbaa6b1f1a29bfd3ffa4a	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:12	131	1
H-A17-PA-038	.claude/skills/prd-authoring-verified/SKILL.md	79774aa24d8b2b479ef54df31da1bb6f08c1cdd525a89858f61b438c23ab81e2	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:13	132	1
H-A17-PA-039	.claude/skills/prd-authoring-verified/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:14	133	2
H-A17-PA-040	.claude/skills/prd-authoring-verified/SKILL.md	0b27734b46fbf7ef264d7dcff4505a08b8773717141fac872ecc4d1c686ca54c	# PRD Authoring with Built-in Verification > ## Tools	HDG	135	1
H-A17-PA-041	.claude/skills/prd-authoring-verified/SKILL.md	affc2a67f81380dd1f23e749e47a8b45c95dfb2f2e815012a28119d036c6cd55	# PRD Authoring with Built-in Verification > ## What this skill does NOT do	HDG	163	1
H-A17-PA-042	.claude/skills/prd-authoring-verified/SKILL.md	ca79336e7086c6fc25a1ff0b3a745146033570abe9134ea0e68c07bdb0119e5d	# PRD Authoring with Built-in Verification > ## Failure modes to refuse	HDG	173	1
H-A18-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	9b5c7a8ea53163aa7fa627192315e1aa846922c450111ab5f0fc2128a497f9c7	# PRD Authoring with Built-in Verification > ## Tools	LI:9	160	1
H-A2-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	c048ac3c4a18743bf74b2d17c61494a35186ca195090f476afd0b895b2651a19		FM:2	2	1
H-A4-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:1	1	2
H-A4-PA-002	.claude/skills/prd-authoring-verified/SKILL.md	cd2d75f1625cc38b0c106ca6e5f53eed265af52ef6f3addb478ce1775f7c1cdd		FM:2	2	1
H-A4-PA-003	.claude/skills/prd-authoring-verified/SKILL.md	1cacbef42fdc90d456025c6042c6af936e31f7b5270213c96becf7acb23de165		FM:3	3	1
H-A4-PA-004	.claude/skills/prd-authoring-verified/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:4	4	2
H-A7-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:3	89	7
H-A7-PA-002	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:5	95	7
H-A7-PA-003	.claude/skills/prd-authoring-verified/SKILL.md	ab09c3574ac3612c4c7df9bc5e8a9b249d929a9c84c47430663b7ff90ac092e8	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:5	95	1
H-A7-PA-004	.claude/skills/prd-authoring-verified/SKILL.md	9c45c0a6411d868922cd494cba23ba9f4617ef1da45f2a2e3c887e5420be8b6c	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:5	95	1
H-A7-PA-005	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	110	7
H-A7-PA-006	.claude/skills/prd-authoring-verified/SKILL.md	53cdc2de6c3318c5af0384ae74ee89290a9763cce5df85f376c2cae82e277f0f	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	110	1
H-A7-PA-007	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	112	7
H-A7-PA-008	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	113	7
H-A7-PA-009	.claude/skills/prd-authoring-verified/SKILL.md	2e08a2f61c97d2ce57edb668f939bbf35345df37c00bc43047a981d49976b327	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	113	1
H-A7-PA-010	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	113	7
H-A7-PA-011	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:9	128	7
H-A7-PA-012	.claude/skills/prd-authoring-verified/SKILL.md	3d9c4ec3dc63a4674a48370eca6b17dcf0eee65079d68635cf71aa4bafea0945	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:9	128	1
H-B3-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	25caba23f113243c9ffd3a8b655d4d69c21aa2f200cde7fc3c5fada758d76e0c	# PRD Authoring with Built-in Verification > ## Scope and boundary	LI:4	18	1
H-B3-PA-002	.claude/skills/prd-authoring-verified/SKILL.md	e8570a6b4d4f80332858d79571880ccba2318e37d35c78fe04702faad089aefd	# PRD Authoring with Built-in Verification > ## Operating modes	LI:2	46	1
H-B3-PA-003	.claude/skills/prd-authoring-verified/SKILL.md	919061e6c7c6dd81bb22c3c0db2a36f5e1ab54b4ebfb3b96978bf5c51d3445f5	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:3	83	1
H-B3-PA-004	.claude/skills/prd-authoring-verified/SKILL.md	6fc8c32d994ec9261fc787a1408c13028c33f9d820d6c646ff910527cbfa6be2	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:3	89	2
H-B3-PA-005	.claude/skills/prd-authoring-verified/SKILL.md	6fc8c32d994ec9261fc787a1408c13028c33f9d820d6c646ff910527cbfa6be2	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	112	2
H-A10-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	9b68c213e154acbb8d23477d85d499f461992e7faffcbb3dbf6f2fbf1b997892	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	63	3
H-A10-PC-002	.claude/skills/prd-closeout-verified/SKILL.md	2af26bb547d12e44140698bf128c3283699804e4c13232346e8512351738f7ca	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	63	3
H-A10-PC-003	.claude/skills/prd-closeout-verified/SKILL.md	1ac4288857b9816947948e54dcb02eae94c40d359db766f4f4e57434a97582d6	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	63	4
H-A10-PC-004	.claude/skills/prd-closeout-verified/SKILL.md	25a4bbc2d9a9c0b23f1e20d92e87155fe2ff8675a40f4666d08eebd838deb727	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	64	4
H-A10-PC-005	.claude/skills/prd-closeout-verified/SKILL.md	5d4285ad69f6aead75320e61bcfa20f3f719dc1b0a790e8d94b021d4d4b38eb4	# PRD Closeout with Built-in Verification > ## Inputs required	LI:7	88	3
H-A10-PC-006	.claude/skills/prd-closeout-verified/SKILL.md	5d4285ad69f6aead75320e61bcfa20f3f719dc1b0a790e8d94b021d4d4b38eb4	# PRD Closeout with Built-in Verification > ## Inputs required	LI:7	89	3
H-A10-PC-007	.claude/skills/prd-closeout-verified/SKILL.md	9b68c213e154acbb8d23477d85d499f461992e7faffcbb3dbf6f2fbf1b997892	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	LI:3	146	3
H-A10-PC-008	.claude/skills/prd-closeout-verified/SKILL.md	2af26bb547d12e44140698bf128c3283699804e4c13232346e8512351738f7ca	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	LI:3	146	3
H-A10-PC-009	.claude/skills/prd-closeout-verified/SKILL.md	1ac4288857b9816947948e54dcb02eae94c40d359db766f4f4e57434a97582d6	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	LI:3	146	4
H-A10-PC-010	.claude/skills/prd-closeout-verified/SKILL.md	25a4bbc2d9a9c0b23f1e20d92e87155fe2ff8675a40f4666d08eebd838deb727	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	LI:3	147	4
H-A10-PC-011	.claude/skills/prd-closeout-verified/SKILL.md	9b68c213e154acbb8d23477d85d499f461992e7faffcbb3dbf6f2fbf1b997892	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	169	3
H-A10-PC-012	.claude/skills/prd-closeout-verified/SKILL.md	2af26bb547d12e44140698bf128c3283699804e4c13232346e8512351738f7ca	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	169	3
H-A10-PC-013	.claude/skills/prd-closeout-verified/SKILL.md	1ac4288857b9816947948e54dcb02eae94c40d359db766f4f4e57434a97582d6	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	169	4
H-A10-PC-014	.claude/skills/prd-closeout-verified/SKILL.md	5d4285ad69f6aead75320e61bcfa20f3f719dc1b0a790e8d94b021d4d4b38eb4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	170	3
H-A10-PC-015	.claude/skills/prd-closeout-verified/SKILL.md	1ac4288857b9816947948e54dcb02eae94c40d359db766f4f4e57434a97582d6	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:9	192	4
H-A10-PC-016	.claude/skills/prd-closeout-verified/SKILL.md	25a4bbc2d9a9c0b23f1e20d92e87155fe2ff8675a40f4666d08eebd838deb727	# PRD Closeout with Built-in Verification > ## What this skill does NOT do	LI:2	220	4
H-A10-PC-017	.claude/skills/prd-closeout-verified/SKILL.md	25a4bbc2d9a9c0b23f1e20d92e87155fe2ff8675a40f4666d08eebd838deb727	# PRD Closeout with Built-in Verification > ## Failure modes to refuse	LI:2	232	4
H-A17-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	ce50f088ae119feb2befc374f3a148cf3ad12067bbf1a5bf36df11d0f079c025	# PRD Closeout with Built-in Verification	HDG	6	1
H-A17-PC-002	.claude/skills/prd-closeout-verified/SKILL.md	c31df17b020896f4408b594dcc87b654acc34d6cffea342410e54300430ff505	# PRD Closeout with Built-in Verification > ## Scope and boundary	HDG	8	1
H-A17-PC-003	.claude/skills/prd-closeout-verified/SKILL.md	0632f7b817601f2c4399f83a1a85ede2ad5c99cacf601e68d5b3471191771451	# PRD Closeout with Built-in Verification > ## When to trigger	HDG	38	1
H-A17-PC-004	.claude/skills/prd-closeout-verified/SKILL.md	90e48a7f751783169d5e801f211330144685188ec27ea465b4e6e633a858f180	# PRD Closeout with Built-in Verification > ## Operating modes	HDG	51	1
H-A17-PC-005	.claude/skills/prd-closeout-verified/SKILL.md	d6d846b406f2b7653084c5785ef74be2a9ad7a246c40752bc2ac844011ff9281	# PRD Closeout with Built-in Verification > ## Inputs required	HDG	75	1
H-A17-PC-006	.claude/skills/prd-closeout-verified/SKILL.md	18a8b5df2208e00d1ba8e7bc8fb538a3625dbfb4e8dc25158debce2a964c237d	# PRD Closeout with Built-in Verification > ## Hard rule: no invented references	HDG	94	1
H-A17-PC-007	.claude/skills/prd-closeout-verified/SKILL.md	153fcd7e47264aed03bb3078a27d4840dbea3d032dd5593a6df85770dcf393ae	# PRD Closeout with Built-in Verification > ## Registry-row invariant	HDG	111	1
H-A17-PC-008	.claude/skills/prd-closeout-verified/SKILL.md	a2d449b06e0d38d92f7ffe6f9919e3cccb1587c59c57ce2ccd1c42f408f2991a	# PRD Closeout with Built-in Verification > ## Two-phase contract	HDG	126	1
H-A17-PC-009	.claude/skills/prd-closeout-verified/SKILL.md	5fafae0a9befdabc8e40acbd0043129c6a04fbc2aad3ea17350a432aae749c14	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	HDG	128	1
H-A17-PC-010	.claude/skills/prd-closeout-verified/SKILL.md	0da21edcb876fd89fc8bb92d7c2e872bbf93feb24097ad037a23ab3fcb97cf93	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	HDG	155	1
H-A17-PC-011	.claude/skills/prd-closeout-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)		157	3
H-A17-PC-012	.claude/skills/prd-closeout-verified/SKILL.md	e089e155302888e26b0348392644b1ca9d0bc643663bd8829188d2005fd5f22d	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:#	160	1
H-A17-PC-013	.claude/skills/prd-closeout-verified/SKILL.md	23cca02b74f386463efa24796c7a9011b0d2c93f0c38b4d15d5d276205b59b43	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:---	161	1
H-A17-PC-014	.claude/skills/prd-closeout-verified/SKILL.md	0505013ef31e7d7ef46f7273546ae32ab51f01c6caf61e0c029077b0a6266398	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V1	162	1
H-A17-PC-015	.claude/skills/prd-closeout-verified/SKILL.md	d6775dcbd35a8d988c9357d45d8857e676d005e12ce9ebe6d232fe38c62dec22	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V2	163	1
H-A17-PC-016	.claude/skills/prd-closeout-verified/SKILL.md	0001768f9f45495f6904c3eba65f6c71fa1a24cfbef213b92ea4c98049aec425	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	164	1
H-A17-PC-017	.claude/skills/prd-closeout-verified/SKILL.md	2cc4cfde350cb0d5739aebf12c854ad5855a428e7db8f8886bb8462e49215472	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	165	1
H-A17-PC-018	.claude/skills/prd-closeout-verified/SKILL.md	19d09a49f4b8c1f8048172098bb6c8db0e0a23a98edc2f512abba776513eba0f	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	166	1
H-A17-PC-019	.claude/skills/prd-closeout-verified/SKILL.md	d10d17150b32b37e373b8442f44aa31d3e4aef3d9f6ce7deedc820b12a3f3c2b	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V6	167	1
H-A17-PC-020	.claude/skills/prd-closeout-verified/SKILL.md	1f6a01b16c0a2c562d7b5d111bd361db8174981c1f2f43462e36ab5bd696d0cb	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	168	1
H-A17-PC-021	.claude/skills/prd-closeout-verified/SKILL.md	9c130f0a5456a9466de5d773896b0c8f2f3cf6536de9b709d1ef88a17603c530	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	169	1
H-A17-PC-022	.claude/skills/prd-closeout-verified/SKILL.md	cdc1273a02be3af53359e5f98387cdc628eca9399e4e5cffe4b701f0704f579f	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	170	1
H-A17-PC-023	.claude/skills/prd-closeout-verified/SKILL.md	2d2e07aa4729de5223058f5c65b33c832d416dd00105feff3f57902308843c9e	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V10	171	1
H-A17-PC-024	.claude/skills/prd-closeout-verified/SKILL.md	8781b2a5acbfe23a1781696caab3a9189d8c74a3c647953f5cb5cd7886332904	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V11	172	1
H-A17-PC-025	.claude/skills/prd-closeout-verified/SKILL.md	0df7b88214ec94aa2ecd386aa7b51811e0b85c87510fd3836471d298c7927b95	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V12	173	1
H-A17-PC-026	.claude/skills/prd-closeout-verified/SKILL.md	458bea3f0da685f2ef0c57edb796ada73a563e370ed8402891fc30b20daae05c	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	HDG	181	1
H-A17-PC-027	.claude/skills/prd-closeout-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	HDG	181	3
H-A17-PC-028	.claude/skills/prd-closeout-verified/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:0	183	2
H-A17-PC-029	.claude/skills/prd-closeout-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:1	184	3
H-A17-PC-030	.claude/skills/prd-closeout-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:1	184	1
H-A17-PC-031	.claude/skills/prd-closeout-verified/SKILL.md	276b874af3c4200a39638b55b0d3c3d9222558f7dc87d848095f93c041a418d6	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:2	185	1
H-A17-PC-032	.claude/skills/prd-closeout-verified/SKILL.md	1764884c2bc08add433b5084b1da6a640392c2af70bb37109bf33884fcb7e587	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:3	186	1
H-A17-PC-033	.claude/skills/prd-closeout-verified/SKILL.md	246bb107e8b78f864ae0448ac9b81096cbf48e0bb077e90ad08b79145a374b05	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:4	187	1
H-A17-PC-034	.claude/skills/prd-closeout-verified/SKILL.md	28fded3950455b2a20f630ab84e87866513f9265760ae11ff2f50f63e67182d4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:5	188	1
H-A17-PC-035	.claude/skills/prd-closeout-verified/SKILL.md	d0d0997b01f902f977bde37641795cb46f1c45cccea2a524a72498813b12a182	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:6	189	1
H-A17-PC-036	.claude/skills/prd-closeout-verified/SKILL.md	8567059c423ca10434a1fc03605bee40fa57feb247d961b12b330b4d67af902f	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:7	190	1
H-A17-PC-037	.claude/skills/prd-closeout-verified/SKILL.md	7caec08de65afcad5cb2e5f3783af913e975c78e3bed0044161231eeafde653a	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:8	191	1
H-A17-PC-038	.claude/skills/prd-closeout-verified/SKILL.md	ebecc5bb953f489e096be29be1f356bf58fb170daab427b31a4570afdd462cff	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:9	192	1
H-A17-PC-039	.claude/skills/prd-closeout-verified/SKILL.md	01df726bafc3870f636bf6fac84f0f2385937019195e1c969b2ebf0437f84196	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:10	193	1
H-A17-PC-040	.claude/skills/prd-closeout-verified/SKILL.md	be542613cedd801ea0fc98ca34a44f009b3e2a48658d2e8ff5bc044c6ec454f5	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:11	194	1
H-A17-PC-041	.claude/skills/prd-closeout-verified/SKILL.md	d6449a7e884f47cb08909684e9459ed9271b7e8b222084782d2e40e58a59bc7f	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:12	195	1
H-A17-PC-042	.claude/skills/prd-closeout-verified/SKILL.md	2e0e8068ff33e24ceed71a887521d99bd0e61ccb9fd0306199d0ef8f5544560b	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:13	196	1
H-A17-PC-043	.claude/skills/prd-closeout-verified/SKILL.md	37cae2bb02c08ef4abcdaba7a8666619559a3c1fb7258c6572446cd0d9fc478c	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:14	197	1
H-A17-PC-044	.claude/skills/prd-closeout-verified/SKILL.md	25327f96b1d34b2e754c0d72d665cd130bb77444b3efbaa6b1f1a29bfd3ffa4a	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:15	198	1
H-A17-PC-045	.claude/skills/prd-closeout-verified/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:16	199	2
H-A17-PC-046	.claude/skills/prd-closeout-verified/SKILL.md	0b27734b46fbf7ef264d7dcff4505a08b8773717141fac872ecc4d1c686ca54c	# PRD Closeout with Built-in Verification > ## Tools	HDG	201	1
H-A17-PC-047	.claude/skills/prd-closeout-verified/SKILL.md	affc2a67f81380dd1f23e749e47a8b45c95dfb2f2e815012a28119d036c6cd55	# PRD Closeout with Built-in Verification > ## What this skill does NOT do	HDG	217	1
H-A17-PC-048	.claude/skills/prd-closeout-verified/SKILL.md	ca79336e7086c6fc25a1ff0b3a745146033570abe9134ea0e68c07bdb0119e5d	# PRD Closeout with Built-in Verification > ## Failure modes to refuse	HDG	228	1
H-A2-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	ecbea080fb90dd2680696622a2b0aa7d3de42cf8b7f236253e134ca4fd44aed1		FM:2	2	1
H-A4-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:1	1	2
H-A4-PC-002	.claude/skills/prd-closeout-verified/SKILL.md	8fe4e531ea7c6157ed5e12ea37a560d4b27fe91e29bbe9b143de32aef498df1a		FM:2	2	1
H-A4-PC-003	.claude/skills/prd-closeout-verified/SKILL.md	e522eb73f9813313c817ef7c32fcfdc006b1635e44f7f1823ac758f7050952a9		FM:3	3	1
H-A4-PC-004	.claude/skills/prd-closeout-verified/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:4	4	2
H-A9-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1		FM:3	3	6
H-A9-PC-002	.claude/skills/prd-closeout-verified/SKILL.md	d7bfe6c1794b0065c412f65d62141245ec33d6d7b8e64990548b199a5bad23d5	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	62	2
H-A9-PC-003	.claude/skills/prd-closeout-verified/SKILL.md	8de6eb13239f2ed8672520035a4cb93da1cd89315c32d687166bcec568cb0ee2	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	62	2
H-A9-PC-004	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1	# PRD Closeout with Built-in Verification > ## Inputs required	LI:2	80	6
H-A9-PC-005	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1	# PRD Closeout with Built-in Verification > ## Hard rule: no invented references	LI:1	100	6
H-A9-PC-006	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	LI:1	132	6
H-A9-PC-007	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V1	162	6
H-A9-PC-008	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V2	163	6
H-A9-PC-009	.claude/skills/prd-closeout-verified/SKILL.md	d7bfe6c1794b0065c412f65d62141245ec33d6d7b8e64990548b199a5bad23d5	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	165	2
H-A9-PC-010	.claude/skills/prd-closeout-verified/SKILL.md	8de6eb13239f2ed8672520035a4cb93da1cd89315c32d687166bcec568cb0ee2	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	165	2
H-B3-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	040dda40127e339900b58614c9040c10ad64e9ed3cea9eda5a3dac75c472381e	# PRD Closeout with Built-in Verification > ## Scope and boundary		26	1
H-A1-PR-001	.claude/skills/prd-review-claude/SKILL.md	46ba65a1df3f0ca724f22d2cb920d60c87059a5cf31779499c646a53bdfb9b30	# Claude PRD Review with Built-in Verification > ## When to trigger	LI:6	54	3
H-A1-PR-002	.claude/skills/prd-review-claude/SKILL.md	46ba65a1df3f0ca724f22d2cb920d60c87059a5cf31779499c646a53bdfb9b30	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:2	106	3
H-A1-PR-003	.claude/skills/prd-review-claude/SKILL.md	46ba65a1df3f0ca724f22d2cb920d60c87059a5cf31779499c646a53bdfb9b30	# Claude PRD Review with Built-in Verification > ## Review structure	F1:5	124	3
H-A12-PR-001	.claude/skills/prd-review-claude/SKILL.md	f7a90bca65e2295fb589472ee0481a6db96a0b7188fe5c368dad3f51b08f43e8	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:7	203	1
H-A16-PR-001	.claude/skills/prd-review-claude/SKILL.md	ec06e591a54738495adfe2182fb383f7fb19b76d35adfc90a4948ea6057d6dff	# Claude PRD Review with Built-in Verification	HDG	6	1
H-A16-PR-002	.claude/skills/prd-review-claude/SKILL.md	c31df17b020896f4408b594dcc87b654acc34d6cffea342410e54300430ff505	# Claude PRD Review with Built-in Verification > ## Scope and boundary	HDG	8	1
H-A16-PR-003	.claude/skills/prd-review-claude/SKILL.md	f66a57b1a2a0be5b15a2c5c70f89aae65690371a0ead45bb97ed63ebd7f3ea4b	# Claude PRD Review with Built-in Verification > ## Independence (input envelope)	HDG	30	1
H-A16-PR-004	.claude/skills/prd-review-claude/SKILL.md	0632f7b817601f2c4399f83a1a85ede2ad5c99cacf601e68d5b3471191771451	# Claude PRD Review with Built-in Verification > ## When to trigger	HDG	40	1
H-A16-PR-005	.claude/skills/prd-review-claude/SKILL.md	90e48a7f751783169d5e801f211330144685188ec27ea465b4e6e633a858f180	# Claude PRD Review with Built-in Verification > ## Operating modes	HDG	56	1
H-A16-PR-006	.claude/skills/prd-review-claude/SKILL.md	d6d846b406f2b7653084c5785ef74be2a9ad7a246c40752bc2ac844011ff9281	# Claude PRD Review with Built-in Verification > ## Inputs required	HDG	69	1
H-A16-PR-007	.claude/skills/prd-review-claude/SKILL.md	18a8b5df2208e00d1ba8e7bc8fb538a3625dbfb4e8dc25158debce2a964c237d	# Claude PRD Review with Built-in Verification > ## Hard rule: no invented references	HDG	84	1
H-A16-PR-008	.claude/skills/prd-review-claude/SKILL.md	9666b278eaa42ae85b612d7b00d4e4b0b1662aefec4bdafafa1352ef19c3d8ad	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	HDG	99	1
H-A16-PR-009	.claude/skills/prd-review-claude/SKILL.md	760043d3b8f68ef9f291e3d4c3ab1d3b34a1f15709c64eeabf87fabe11bba4ca	# Claude PRD Review with Built-in Verification > ## Review structure	HDG	115	1
H-A16-PR-010	.claude/skills/prd-review-claude/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Claude PRD Review with Built-in Verification > ## Review structure	F1:0	119	4
H-A16-PR-011	.claude/skills/prd-review-claude/SKILL.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# Claude PRD Review with Built-in Verification > ## Review structure	F1:1	120	1
H-A16-PR-012	.claude/skills/prd-review-claude/SKILL.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# Claude PRD Review with Built-in Verification > ## Review structure	F1:1	120	4
H-A16-PR-013	.claude/skills/prd-review-claude/SKILL.md	7fed46854b57d36b7e9d1e21c7b3c8dfba6b580cd629d427e83ad4cfe43126a4	# Claude PRD Review with Built-in Verification > ## Review structure	F1:2	121	1
H-A16-PR-014	.claude/skills/prd-review-claude/SKILL.md	36c86fa017851c89910d324ab67f4fc1a7b61f623fe00a179bdc332e1bdda2a8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:2	121	1
H-A16-PR-015	.claude/skills/prd-review-claude/SKILL.md	ce04d5c2a7222e0d9e12cc0bc7db23aadfe321175463c27d72fe9ec440f2d6fe	# Claude PRD Review with Built-in Verification > ## Review structure	F1:3	122	1
H-A16-PR-016	.claude/skills/prd-review-claude/SKILL.md	72b4e29e40c010c4dd85eb29e04482be685022b1ea3ba191f54a37e55bab7383	# Claude PRD Review with Built-in Verification > ## Review structure	F1:3	122	1
H-A16-PR-017	.claude/skills/prd-review-claude/SKILL.md	1984dbbb744cc37eb3cbba12ddc08b260ecb70e936cf4778d5a9bb4c3d989d5d	# Claude PRD Review with Built-in Verification > ## Review structure	F1:4	123	1
H-A16-PR-018	.claude/skills/prd-review-claude/SKILL.md	6d80bd100c49a1b843eadc1ea154a42c8b0f0cf6d4e7cb42721cd6afd572ffbb	# Claude PRD Review with Built-in Verification > ## Review structure	F1:4	123	1
H-A16-PR-019	.claude/skills/prd-review-claude/SKILL.md	99c728a8afee3a9bd73e07473d10ac90cd145a1f90234b0107e21be62d7bd903	# Claude PRD Review with Built-in Verification > ## Review structure	F1:4	123	1
H-A16-PR-020	.claude/skills/prd-review-claude/SKILL.md	0f55ec5e10e8b3ac5a16e1d06dd9431e8df079397da4ff2d4866eff79d7b0870	# Claude PRD Review with Built-in Verification > ## Review structure	F1:5	124	1
H-A16-PR-021	.claude/skills/prd-review-claude/SKILL.md	53a699c1082ef45eacf6b3f1dfe275c94ee04e1be1b6e54a1b293f3286ede919	# Claude PRD Review with Built-in Verification > ## Review structure	F1:6	125	1
H-A16-PR-022	.claude/skills/prd-review-claude/SKILL.md	56e4546a4cfc2d0350c9ddf55a340429220f1779ebbd3d1b1f5f1b4e002192cd	# Claude PRD Review with Built-in Verification > ## Review structure	F1:7	126	1
H-A16-PR-023	.claude/skills/prd-review-claude/SKILL.md	f8f747ebd48b0a8e4b9c4f787fc33faae7e4d2611d4430712b8cfb7bb1fd442f	# Claude PRD Review with Built-in Verification > ## Review structure	F1:8	127	1
H-A16-PR-024	.claude/skills/prd-review-claude/SKILL.md	e93703c88549b358b6d163e0984778f802fea3210359df70ed99eddbf9e82c0b	# Claude PRD Review with Built-in Verification > ## Review structure	F1:9	128	1
H-A16-PR-025	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:10	129	9
H-A16-PR-026	.claude/skills/prd-review-claude/SKILL.md	f2ec9958bdcf241947fa4d3d593ccab8f88f4d32e42968e9f29968a76cc0f469	# Claude PRD Review with Built-in Verification > ## Review structure	F1:11	130	1
H-A16-PR-027	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:12	131	9
H-A16-PR-028	.claude/skills/prd-review-claude/SKILL.md	b5a12b170c05f093fd1c3b6cf544dfae7e6cfd1b1a9c8fcb6590332d9dd7608e	# Claude PRD Review with Built-in Verification > ## Review structure	F1:13	132	2
H-A16-PR-029	.claude/skills/prd-review-claude/SKILL.md	b5a12b170c05f093fd1c3b6cf544dfae7e6cfd1b1a9c8fcb6590332d9dd7608e	# Claude PRD Review with Built-in Verification > ## Review structure	F1:13	132	2
H-A16-PR-030	.claude/skills/prd-review-claude/SKILL.md	1ffeda7a5ddd500d8995e256d63d210b759531f3767440d47c40d1f8c9c19014	# Claude PRD Review with Built-in Verification > ## Review structure	F1:14	133	1
H-A16-PR-031	.claude/skills/prd-review-claude/SKILL.md	bf264d523e4506562741536867cca7e68083d6195ffb5eac623e0c977535bebd	# Claude PRD Review with Built-in Verification > ## Review structure	F1:14	133	2
H-A16-PR-032	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:15	134	9
H-A16-PR-033	.claude/skills/prd-review-claude/SKILL.md	6997c676311472227ac618a1d67cd14c978422f0bdd33c1b69ffd68876e2ab88	# Claude PRD Review with Built-in Verification > ## Review structure	F1:16	135	2
H-A16-PR-034	.claude/skills/prd-review-claude/SKILL.md	6997c676311472227ac618a1d67cd14c978422f0bdd33c1b69ffd68876e2ab88	# Claude PRD Review with Built-in Verification > ## Review structure	F1:16	135	2
H-A16-PR-035	.claude/skills/prd-review-claude/SKILL.md	cf7a3ff5f2256d2ea5e80cc7179ef07be02e2759c7f54d986bf9cc1b159c42c5	# Claude PRD Review with Built-in Verification > ## Review structure	F1:17	136	1
H-A16-PR-036	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:18	137	9
H-A16-PR-037	.claude/skills/prd-review-claude/SKILL.md	d09b7be99a6b9b560d5469be428b91cc1e56fdcdb1642646f5332583daca7d68	# Claude PRD Review with Built-in Verification > ## Review structure	F1:19	138	2
H-A16-PR-038	.claude/skills/prd-review-claude/SKILL.md	d09b7be99a6b9b560d5469be428b91cc1e56fdcdb1642646f5332583daca7d68	# Claude PRD Review with Built-in Verification > ## Review structure	F1:19	138	2
H-A16-PR-039	.claude/skills/prd-review-claude/SKILL.md	fb5243df404a965eebe41a769f22c9c3d059c3bb9372ebd9e4af2db9387079cd	# Claude PRD Review with Built-in Verification > ## Review structure	F1:20	139	1
H-A16-PR-040	.claude/skills/prd-review-claude/SKILL.md	75dd8998159fd9c6deaf6494c7c07f9b84bee8820e0eb9c8913e44eda0eaf9eb	# Claude PRD Review with Built-in Verification > ## Review structure	F1:21	140	1
H-A16-PR-041	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:22	141	9
H-A16-PR-042	.claude/skills/prd-review-claude/SKILL.md	2f059f70133dc7d1fcc020a9d9aaf240c1e6d3555a63667a00c96f14eeeb517c	# Claude PRD Review with Built-in Verification > ## Review structure	F1:23	142	2
H-A16-PR-043	.claude/skills/prd-review-claude/SKILL.md	2f059f70133dc7d1fcc020a9d9aaf240c1e6d3555a63667a00c96f14eeeb517c	# Claude PRD Review with Built-in Verification > ## Review structure	F1:23	142	2
H-A16-PR-044	.claude/skills/prd-review-claude/SKILL.md	0491ebf582d1bee52683be36b514e83a15861c2cd4214571d7fa0d8a8b1fcf7b	# Claude PRD Review with Built-in Verification > ## Review structure	F1:24	143	1
H-A16-PR-045	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:25	144	9
H-A16-PR-046	.claude/skills/prd-review-claude/SKILL.md	70aa3bc4e4317e48a590f57ef3357ed13d85ff34ac93e62e5facc6679c8068c7	# Claude PRD Review with Built-in Verification > ## Review structure	F1:26	145	2
H-A16-PR-047	.claude/skills/prd-review-claude/SKILL.md	70aa3bc4e4317e48a590f57ef3357ed13d85ff34ac93e62e5facc6679c8068c7	# Claude PRD Review with Built-in Verification > ## Review structure	F1:26	145	2
H-A16-PR-048	.claude/skills/prd-review-claude/SKILL.md	d2025475a0e797d2debf9e849114eacb6f957380658c63b39342cbcddfe812ce	# Claude PRD Review with Built-in Verification > ## Review structure	F1:27	146	1
H-A16-PR-049	.claude/skills/prd-review-claude/SKILL.md	35db501a705cb77a0b907fe42438882d44a996d609eb279f4e057c69b4c7e4d5	# Claude PRD Review with Built-in Verification > ## Review structure	F1:28	147	1
H-A16-PR-050	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:29	148	9
H-A16-PR-051	.claude/skills/prd-review-claude/SKILL.md	616c644b0d62fe67ed149abb8966678edfa30c1bc2b59ce20ee29dd63d65c7ce	# Claude PRD Review with Built-in Verification > ## Review structure	F1:30	149	2
H-A16-PR-052	.claude/skills/prd-review-claude/SKILL.md	616c644b0d62fe67ed149abb8966678edfa30c1bc2b59ce20ee29dd63d65c7ce	# Claude PRD Review with Built-in Verification > ## Review structure	F1:30	149	2
H-A16-PR-053	.claude/skills/prd-review-claude/SKILL.md	3dae5ac04da0db42fd70a7516e57a594816c3f8e8e8d0ef8e632a6bc944a199d	# Claude PRD Review with Built-in Verification > ## Review structure	F1:31	150	1
H-A16-PR-054	.claude/skills/prd-review-claude/SKILL.md	34c48bd8e307fae990aa1316c0e3cc83d1abd39d8b356b337a27e350e4d1b6d0	# Claude PRD Review with Built-in Verification > ## Review structure	F1:32	151	1
H-A16-PR-055	.claude/skills/prd-review-claude/SKILL.md	b8880601f5e861b3bcbe6a1d1ef0443126e1570ed0d8f1c3d535fa55fc988bf1	# Claude PRD Review with Built-in Verification > ## Review structure	F1:33	152	1
H-A16-PR-056	.claude/skills/prd-review-claude/SKILL.md	cc6d0823798cb71ee3080db22dd8064e63bd1508d265fbaf6e9cf7c2d2af4547	# Claude PRD Review with Built-in Verification > ## Review structure	F1:34	153	1
H-A16-PR-057	.claude/skills/prd-review-claude/SKILL.md	f89eeb36f7ebe9ce24570ded724767d594b417441009b2a9f728f553fee68de8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:35	154	1
H-A16-PR-058	.claude/skills/prd-review-claude/SKILL.md	de74dba29bda1f745ffeb03c8715cc461539a32835c097d93570595667b22bf8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:36	155	1
H-A16-PR-059	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:37	156	9
H-A16-PR-060	.claude/skills/prd-review-claude/SKILL.md	f1eedfb0a1479dd1fc5abf5bd2bcf343734e5eb75b15a1bc50fb0072a9349e8d	# Claude PRD Review with Built-in Verification > ## Review structure	F1:38	157	2
H-A16-PR-061	.claude/skills/prd-review-claude/SKILL.md	f1eedfb0a1479dd1fc5abf5bd2bcf343734e5eb75b15a1bc50fb0072a9349e8d	# Claude PRD Review with Built-in Verification > ## Review structure	F1:38	157	2
H-A16-PR-062	.claude/skills/prd-review-claude/SKILL.md	20a3260cbf38a0992695c8a6e467c9b566b86e38b719ea50b65058639747bd62	# Claude PRD Review with Built-in Verification > ## Review structure	F1:39	158	1
H-A16-PR-063	.claude/skills/prd-review-claude/SKILL.md	5c27541966ef12bb8096ff83b839561e4161edc3c086b7025f291a215db4ca32	# Claude PRD Review with Built-in Verification > ## Review structure	F1:40	159	1
H-A16-PR-064	.claude/skills/prd-review-claude/SKILL.md	73cc46f937442b3ae102e8d0b8adcc06065a35128d7625cadd7f03995bdbbfc8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:41	160	1
H-A16-PR-065	.claude/skills/prd-review-claude/SKILL.md	6c0e0d16592619bcc84c0994221684a9d240e5bcb848e3574e0b599bd0ad95a6	# Claude PRD Review with Built-in Verification > ## Review structure	F1:42	161	1
H-A16-PR-066	.claude/skills/prd-review-claude/SKILL.md	abc74caadaae7b00e664bd2412644a1f8a65594cc26fa4bd5ee760df31eb2341	# Claude PRD Review with Built-in Verification > ## Review structure	F1:43	162	1
H-A16-PR-067	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:44	163	9
H-A16-PR-068	.claude/skills/prd-review-claude/SKILL.md	91d5a6aa3e3909829b21227cb0308c9451041d74962029c895d09e112518b4d8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:45	164	2
H-A16-PR-069	.claude/skills/prd-review-claude/SKILL.md	91d5a6aa3e3909829b21227cb0308c9451041d74962029c895d09e112518b4d8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:45	164	2
H-A16-PR-070	.claude/skills/prd-review-claude/SKILL.md	00145fcec1566295879857064d0cc9334a5851caf388b3822f687e56ba0b2774	# Claude PRD Review with Built-in Verification > ## Review structure	F1:46	165	1
H-A16-PR-071	.claude/skills/prd-review-claude/SKILL.md	b5014b97f53bd9531adcf67a079a35d494ac7c0b135ff2b022813152a262bc33	# Claude PRD Review with Built-in Verification > ## Review structure	F1:47	166	1
H-A16-PR-072	.claude/skills/prd-review-claude/SKILL.md	9890c8f4ef393cde9262e107a8cc61ab4ef5aa2c6bd2af37ea7478bcb4c6f743	# Claude PRD Review with Built-in Verification > ## Review structure	F1:48	167	1
H-A16-PR-073	.claude/skills/prd-review-claude/SKILL.md	3ad23695a1d7bf99cb0c82b998f83175e45b9f8468a2d6241d8465df191dbba7	# Claude PRD Review with Built-in Verification > ## Review structure	F1:49	168	1
H-A16-PR-074	.claude/skills/prd-review-claude/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Claude PRD Review with Built-in Verification > ## Review structure	F1:50	169	4
H-A16-PR-075	.claude/skills/prd-review-claude/SKILL.md	a2d449b06e0d38d92f7ffe6f9919e3cccb1587c59c57ce2ccd1c42f408f2991a	# Claude PRD Review with Built-in Verification > ## Two-phase contract	HDG	171	1
H-A16-PR-076	.claude/skills/prd-review-claude/SKILL.md	b2dc9baa601a8d4b7464fcf623c472e29427f0554626f54b9de95bf9b64bda4d	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	HDG	173	1
H-A16-PR-077	.claude/skills/prd-review-claude/SKILL.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:2	176	4
H-A16-PR-078	.claude/skills/prd-review-claude/SKILL.md	0da21edcb876fd89fc8bb92d7c2e872bbf93feb24097ad037a23ab3fcb97cf93	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	HDG	206	1
H-A16-PR-079	.claude/skills/prd-review-claude/SKILL.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V11	220	4
H-A16-PR-080	.claude/skills/prd-review-claude/SKILL.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V12	221	4
H-A16-PR-081	.claude/skills/prd-review-claude/SKILL.md	ec0d4965ad1012046dfbee08f8c1e46ab29f1694b0b824c24c1adf6aed6d6824	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	HDG	224	1
H-A16-PR-082	.claude/skills/prd-review-claude/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:0	226	4
H-A16-PR-083	.claude/skills/prd-review-claude/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:1	227	1
H-A16-PR-084	.claude/skills/prd-review-claude/SKILL.md	adf9288481d28b924834f0949e9b5e22839d0bac573505acae5cb828853dc3a3	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:2	228	1
H-A16-PR-085	.claude/skills/prd-review-claude/SKILL.md	5a86a869bbfa1a68e0a22ade048eca69dd74abf3fd58eafa9a7f5b048b805698	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:3	229	1
H-A16-PR-086	.claude/skills/prd-review-claude/SKILL.md	fda08c51847a7a20e09146fab13b22ab454147e6555c394616bd5fd86c2b780a	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:4	230	1
H-A16-PR-087	.claude/skills/prd-review-claude/SKILL.md	bf264d523e4506562741536867cca7e68083d6195ffb5eac623e0c977535bebd	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:4	230	2
H-A16-PR-088	.claude/skills/prd-review-claude/SKILL.md	f4dec5e720350c31ae34c0207918030bfe93f2cbd200b24cdadf3bd38db568ff	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:5	231	1
H-A16-PR-089	.claude/skills/prd-review-claude/SKILL.md	112738a7c08c52b4ecf78f7d95fd001fb95329b65d4992650457c29228dea7b0	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:6	232	1
H-A16-PR-090	.claude/skills/prd-review-claude/SKILL.md	3b5828f1c28d17a89826e572a362a41cf9fb2ff629260e50c2bce721f3a12430	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:7	233	1
H-A16-PR-091	.claude/skills/prd-review-claude/SKILL.md	c658c2e934a208cbce7fed333885ce63698fd9cfedaf15fc5633b7a08893fae1	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:8	234	1
H-A16-PR-092	.claude/skills/prd-review-claude/SKILL.md	58c16f4b94ec28f898dbf857c3d9f0f6d6728cc1c0ed9c3ed2a8d9d6af0b2010	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:9	235	1
H-A16-PR-093	.claude/skills/prd-review-claude/SKILL.md	e2a195df7256ecb52aaa5bcedbc9e2c0e0cc06cc074208dc799862ccefa62b4d	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:10	236	1
H-A16-PR-094	.claude/skills/prd-review-claude/SKILL.md	70a492de08ee89b91c07ba370762f629e9db5b9726f24c62888b177a292e633f	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:11	237	1
H-A16-PR-095	.claude/skills/prd-review-claude/SKILL.md	633c164ff59f8e13f419ca6022a54ccac6dcd537e7a064445ac32cbde1f8659b	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:12	238	1
H-A16-PR-096	.claude/skills/prd-review-claude/SKILL.md	128700814b7c862a0c345c5213e92c12ad18b5f8721109ae49723621244971d0	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:13	239	1
H-A16-PR-097	.claude/skills/prd-review-claude/SKILL.md	d984c3ce5decc3ff14f6fd4dd00f78b7d9d90c7720089d9b95a3c85912b4aa5b	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:14	240	1
H-A16-PR-098	.claude/skills/prd-review-claude/SKILL.md	25327f96b1d34b2e754c0d72d665cd130bb77444b3efbaa6b1f1a29bfd3ffa4a	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:15	241	1
H-A16-PR-099	.claude/skills/prd-review-claude/SKILL.md	79774aa24d8b2b479ef54df31da1bb6f08c1cdd525a89858f61b438c23ab81e2	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:16	242	1
H-A16-PR-100	.claude/skills/prd-review-claude/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:17	243	4
H-A16-PR-101	.claude/skills/prd-review-claude/SKILL.md	0b27734b46fbf7ef264d7dcff4505a08b8773717141fac872ecc4d1c686ca54c	# Claude PRD Review with Built-in Verification > ## Tools	HDG	245	1
H-A16-PR-102	.claude/skills/prd-review-claude/SKILL.md	affc2a67f81380dd1f23e749e47a8b45c95dfb2f2e815012a28119d036c6cd55	# Claude PRD Review with Built-in Verification > ## What this skill does NOT do	HDG	259	1
H-A16-PR-103	.claude/skills/prd-review-claude/SKILL.md	ca79336e7086c6fc25a1ff0b3a745146033570abe9134ea0e68c07bdb0119e5d	# Claude PRD Review with Built-in Verification > ## Failure modes to refuse	HDG	277	1
H-A17-PR-001	.claude/skills/prd-review-claude/SKILL.md	e089e155302888e26b0348392644b1ca9d0bc643663bd8829188d2005fd5f22d	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:#	208	1
H-A17-PR-002	.claude/skills/prd-review-claude/SKILL.md	23cca02b74f386463efa24796c7a9011b0d2c93f0c38b4d15d5d276205b59b43	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:---	209	1
H-A17-PR-003	.claude/skills/prd-review-claude/SKILL.md	5c575e6a52fa6fbaaddba63e707175fe732c46332c43afb9985039be92a10020	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V1	210	1
H-A17-PR-004	.claude/skills/prd-review-claude/SKILL.md	aa0379907976e3e3ff7cb323736d9e31db7f12d4be546adbd248db7b4b56b7a4	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V2	211	1
H-A17-PR-005	.claude/skills/prd-review-claude/SKILL.md	177ff681e9d39670f4e2ca34ef6e4e39c647a2d63ba72b083fbbea2bcae0ee1f	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	212	1
H-A17-PR-006	.claude/skills/prd-review-claude/SKILL.md	8e7e82139ca65d8a1a13fcad51f16451a0acfda029dfbd67ac7ef543da89ca0a	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	213	1
H-A17-PR-007	.claude/skills/prd-review-claude/SKILL.md	80afaa8140cf077dca5e6dd2e134a65324259136afd82a8ee1a7d2c08eb39bd6	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	214	1
H-A17-PR-008	.claude/skills/prd-review-claude/SKILL.md	93443ecbb7087094f96d1a7c19c331449cee547efaacec428d3429529e4057f7	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V6	215	1
H-A17-PR-009	.claude/skills/prd-review-claude/SKILL.md	49b656d00aaca4ba99f49be31d11fe9bafaa1a975e463919ae91bb8dbc20aacc	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	216	1
H-A17-PR-010	.claude/skills/prd-review-claude/SKILL.md	f2831b2cfa941935cae5e208e85c80277af4c4e25be5f69aa521527fbdce3416	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	217	1
H-A17-PR-011	.claude/skills/prd-review-claude/SKILL.md	bc7c69efbde77eccb081abd5b0855f21a62d43bfd1cbed0be4bd265bf4002be1	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	218	1
H-A17-PR-012	.claude/skills/prd-review-claude/SKILL.md	642806c3de654990f08e15805285a5d539ee07367cf3db5f384d80d037d725e7	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V10	219	1
H-A17-PR-013	.claude/skills/prd-review-claude/SKILL.md	559368082ee095af2a825c0d8c1758ad64252d9751bfe9d7de9d9ea87a68e3aa	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V11	220	1
H-A17-PR-014	.claude/skills/prd-review-claude/SKILL.md	78374bc32a63d0ef9ae25f4b56993bc785dc4419696fd00b4471ac1126ede4a0	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V12	221	1
H-A17-PR-015	.claude/skills/prd-review-claude/SKILL.md	ebba0855fc1c15fb9e94dab36f7faf70cbeda79433c0d09f7fe9bc3a4933e8ac	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V13	222	1
H-A17-PR-016	.claude/skills/prd-review-claude/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	HDG	224	2
H-A17-PR-017	.claude/skills/prd-review-claude/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:1	227	2
H-A2-PR-001	.claude/skills/prd-review-claude/SKILL.md	3f48209fc3b8c4afd0c163a813f88fd3933298a954b6590b71c1e033459214ca		FM:2	2	1
H-A2-PR-002	.claude/skills/prd-review-claude/SKILL.md	c048ac3c4a18743bf74b2d17c61494a35186ca195090f476afd0b895b2651a19	# Claude PRD Review with Built-in Verification > ## Scope and boundary	LI:3	22	2
H-A2-PR-003	.claude/skills/prd-review-claude/SKILL.md	c048ac3c4a18743bf74b2d17c61494a35186ca195090f476afd0b895b2651a19	# Claude PRD Review with Built-in Verification > ## Hard rule: no invented references		97	2
H-A4-PR-001	.claude/skills/prd-review-claude/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:1	1	2
H-A4-PR-002	.claude/skills/prd-review-claude/SKILL.md	05b2c1ed6181f073f91f9afb64a5848c52ef21a3464dafa05e0127b60ca9e271		FM:2	2	1
H-A4-PR-003	.claude/skills/prd-review-claude/SKILL.md	423e8a65d37daaf593cc8d1327620d80dcacc065505f28036e60f74e2060bb55		FM:3	3	1
H-A4-PR-004	.claude/skills/prd-review-claude/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:4	4	2
H-A5-PR-001	.claude/skills/prd-review-claude/SKILL.md	b3377ae9582134d6ffae99dc1710caed1b9c09a1b5eb977d1a58e9641d91be77		FM:3	3	4
H-A5-PR-002	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514		FM:3	3	6
H-A5-PR-003	.claude/skills/prd-review-claude/SKILL.md	a8ce16a33fe58bfdfdbb35184c54e4508ca4bb43a1f327d8c604ea29c7aa34ec	# Claude PRD Review with Built-in Verification > ## When to trigger	LI:6	53	4
H-A5-PR-004	.claude/skills/prd-review-claude/SKILL.md	851833bccec8dac2405286643c443217562a118de745165c42795adf60206374	# Claude PRD Review with Built-in Verification > ## When to trigger	LI:6	54	2
H-A5-PR-005	.claude/skills/prd-review-claude/SKILL.md	b3377ae9582134d6ffae99dc1710caed1b9c09a1b5eb977d1a58e9641d91be77	# Claude PRD Review with Built-in Verification > ## Operating modes	LI:2	62	4
H-A5-PR-006	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# Claude PRD Review with Built-in Verification > ## Operating modes	LI:2	62	6
H-A5-PR-007	.claude/skills/prd-review-claude/SKILL.md	20108fbf02a3552fa81f746251cb11266473769362df8a8097d503b914c4d4a1	# Claude PRD Review with Built-in Verification > ## Operating modes	LI:2	64	1
H-A5-PR-008	.claude/skills/prd-review-claude/SKILL.md	b3377ae9582134d6ffae99dc1710caed1b9c09a1b5eb977d1a58e9641d91be77	# Claude PRD Review with Built-in Verification > ## Inputs required	LI:3	77	4
H-A5-PR-009	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# Claude PRD Review with Built-in Verification > ## Inputs required	LI:3	77	6
H-A5-PR-010	.claude/skills/prd-review-claude/SKILL.md	a8ce16a33fe58bfdfdbb35184c54e4508ca4bb43a1f327d8c604ea29c7aa34ec	# Claude PRD Review with Built-in Verification > ## Hard rule: no invented references	LI:3	91	4
H-A5-PR-011	.claude/skills/prd-review-claude/SKILL.md	b3377ae9582134d6ffae99dc1710caed1b9c09a1b5eb977d1a58e9641d91be77	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:1	103	4
H-A5-PR-012	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:1	103	6
H-A5-PR-013	.claude/skills/prd-review-claude/SKILL.md	383b98bbab9f34d2541c89a47932737d58713f0465eec933bd8bb66b41de5aae	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:2	105	1
H-A5-PR-014	.claude/skills/prd-review-claude/SKILL.md	a8ce16a33fe58bfdfdbb35184c54e4508ca4bb43a1f327d8c604ea29c7aa34ec	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:2	105	4
H-A5-PR-015	.claude/skills/prd-review-claude/SKILL.md	851833bccec8dac2405286643c443217562a118de745165c42795adf60206374	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:2	106	2
H-A5-PR-016	.claude/skills/prd-review-claude/SKILL.md	1077bb30aea03fd3852fedb7385a0f92c567ce3ebb241c1767778bc171550108	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths		113	2
H-A5-PR-017	.claude/skills/prd-review-claude/SKILL.md	a8ce16a33fe58bfdfdbb35184c54e4508ca4bb43a1f327d8c604ea29c7aa34ec	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:3	183	4
H-A5-PR-018	.claude/skills/prd-review-claude/SKILL.md	1077bb30aea03fd3852fedb7385a0f92c567ce3ebb241c1767778bc171550108	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V6	215	2
H-A5-PR-019	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	218	6
H-A5-PR-020	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	218	6
H-B3-PR-001	.claude/skills/prd-review-claude/SKILL.md	25caba23f113243c9ffd3a8b655d4d69c21aa2f200cde7fc3c5fada758d76e0c	# Claude PRD Review with Built-in Verification > ## Scope and boundary	LI:5	25	1
H-B3-PR-002	.claude/skills/prd-review-claude/SKILL.md	e8570a6b4d4f80332858d79571880ccba2318e37d35c78fe04702faad089aefd	# Claude PRD Review with Built-in Verification > ## What this skill does NOT do	LI:6	273	1
H-B7-PR-001	.claude/skills/prd-review-claude/SKILL.md	067db46ccfae6e6003b029e847a9393ada8d727e0c764bb47e4fffb7ae271f32	# Claude PRD Review with Built-in Verification > ## Review structure	F1:35	154	2
H-B7-PR-002	.claude/skills/prd-review-claude/SKILL.md	859cd70e5e497c79653d0e32e00adb43df1a68adf82d1dc284d16516abe10205	# Claude PRD Review with Built-in Verification > ## Review structure	F1:35	154	1
H-B7-PR-003	.claude/skills/prd-review-claude/SKILL.md	067db46ccfae6e6003b029e847a9393ada8d727e0c764bb47e4fffb7ae271f32	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:4	189	2
H-B7-PR-004	.claude/skills/prd-review-claude/SKILL.md	58abaf96ebf7e4c85df72f06d5e974ad8440c9dadaa59b6bf5ce8ff020b9bd7f	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:4	189	1
H-A10-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	2af26bb547d12e44140698bf128c3283699804e4c13232346e8512351738f7ca	# Scope-Lock Pre-Commit > ## Inputs required	LI:1	53	1
H-A11-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:1	146	8
H-A11-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	8161c9a80a3d0064495637883cda8877cbef7d7e57dc419b3631cf7e0509c03f	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:2	147	1
H-A11-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	f4f1f60a1a29b4b24265e0be159d690d6e342b65c3833d7b2f06b0dbfad60137	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:2	147	4
H-A11-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	f4f1f60a1a29b4b24265e0be159d690d6e342b65c3833d7b2f06b0dbfad60137	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:2	147	4
H-A11-SL-005	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:4	154	8
H-A11-SL-006	.claude/skills/scope-lock-precommit/SKILL.md	f4f1f60a1a29b4b24265e0be159d690d6e342b65c3833d7b2f06b0dbfad60137	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:5	157	4
H-A11-SL-007	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		164	8
H-A11-SL-008	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 1 — Detect	LI:4	185	8
H-A11-SL-009	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	204	8
H-A11-SL-010	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:8	218	8
H-A11-SL-011	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## What this skill does NOT do	LI:3	244	8
H-A11-SL-012	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Failure modes to refuse	LI:4	255	8
H-A11-SL-013	.claude/skills/scope-lock-precommit/SKILL.md	f4f1f60a1a29b4b24265e0be159d690d6e342b65c3833d7b2f06b0dbfad60137	# Scope-Lock Pre-Commit > ## Failure modes to refuse	LI:4	255	4
H-A17-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	d81084e9c9851e20ecfe79c1ca662ee37c4d1f7a0ff5df11c5d1df95fb81efb2	# Scope-Lock Pre-Commit	HDG	6	1
H-A17-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	c31df17b020896f4408b594dcc87b654acc34d6cffea342410e54300430ff505	# Scope-Lock Pre-Commit > ## Scope and boundary	HDG	8	1
H-A17-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	0632f7b817601f2c4399f83a1a85ede2ad5c99cacf601e68d5b3471191771451	# Scope-Lock Pre-Commit > ## When to trigger	HDG	24	1
H-A17-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	90e48a7f751783169d5e801f211330144685188ec27ea465b4e6e633a858f180	# Scope-Lock Pre-Commit > ## Operating modes	HDG	37	1
H-A17-SL-005	.claude/skills/scope-lock-precommit/SKILL.md	d6d846b406f2b7653084c5785ef74be2a9ad7a246c40752bc2ac844011ff9281	# Scope-Lock Pre-Commit > ## Inputs required	HDG	50	1
H-A17-SL-006	.claude/skills/scope-lock-precommit/SKILL.md	18a8b5df2208e00d1ba8e7bc8fb538a3625dbfb4e8dc25158debce2a964c237d	# Scope-Lock Pre-Commit > ## Hard rule: no invented references	HDG	60	1
H-A17-SL-007	.claude/skills/scope-lock-precommit/SKILL.md	daed579e65f463e99a19362034490bddea10ae7a920bf10dd76c5d26c5fa456c	# Scope-Lock Pre-Commit > ## FILES parsing rule	HDG	73	1
H-A17-SL-008	.claude/skills/scope-lock-precommit/SKILL.md	1708d56e5bdcc5c838c437da676ed17cdd701caa75b765f6fcd1d04309cd660c	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)	HDG	95	1
H-A17-SL-009	.claude/skills/scope-lock-precommit/SKILL.md	94f5224b21d7c6966622036fa19e0ed5769259df6cd2187c06c212423ef921fb	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	HDG	141	1
H-A17-SL-010	.claude/skills/scope-lock-precommit/SKILL.md	a2d449b06e0d38d92f7ffe6f9919e3cccb1587c59c57ce2ccd1c42f408f2991a	# Scope-Lock Pre-Commit > ## Two-phase contract	HDG	178	1
H-A17-SL-011	.claude/skills/scope-lock-precommit/SKILL.md	3eea3e224342278946b671706d450553283ef08b70b85ba3f26d289dddf096b7	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 1 — Detect	HDG	180	1
H-A17-SL-012	.claude/skills/scope-lock-precommit/SKILL.md	0da21edcb876fd89fc8bb92d7c2e872bbf93feb24097ad037a23ab3fcb97cf93	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	HDG	194	1
H-A17-SL-013	.claude/skills/scope-lock-precommit/SKILL.md	e089e155302888e26b0348392644b1ca9d0bc643663bd8829188d2005fd5f22d	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:#	196	1
H-A17-SL-014	.claude/skills/scope-lock-precommit/SKILL.md	23cca02b74f386463efa24796c7a9011b0d2c93f0c38b4d15d5d276205b59b43	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:---	197	1
H-A17-SL-015	.claude/skills/scope-lock-precommit/SKILL.md	9d44061a9fffd8a44e829e6c795494eba2f29bb08280cccf17c9b646d5656153	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V1	198	1
H-A17-SL-016	.claude/skills/scope-lock-precommit/SKILL.md	35471e76fb375db6a134b23eb0750864b4f01ecedb0c4733d8caa6f2a23a29d6	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V2	199	1
H-A17-SL-017	.claude/skills/scope-lock-precommit/SKILL.md	39e88f6b61ed85817bf3c5fc407fa14091d7529756e04456486a76e71b37965a	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	200	1
H-A17-SL-018	.claude/skills/scope-lock-precommit/SKILL.md	048a87a71f91ec57ad172489a47dfd6d1cb424b9d538ba874f7a56fb6fc10c01	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	201	1
H-A17-SL-019	.claude/skills/scope-lock-precommit/SKILL.md	09960e426ddde585bbfc9bb22748f42e27ecec43035023907a009ea5afbfce70	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	202	1
H-A17-SL-020	.claude/skills/scope-lock-precommit/SKILL.md	2c76cc6af71f3d087801491399a2bbfddb73a50ea744e2efe5794cb4a9f59dc8	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V6	203	1
H-A17-SL-021	.claude/skills/scope-lock-precommit/SKILL.md	e01150607dd7b7362f6b0739f9b5b9341b372a62d548d918c30ce6aa34156425	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	204	1
H-A17-SL-022	.claude/skills/scope-lock-precommit/SKILL.md	03a45befe5f291d13eec7c7a49255c2df164bad366da2114e89e3505c2d2a87a	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	205	1
H-A17-SL-023	.claude/skills/scope-lock-precommit/SKILL.md	9123fac54442e7f70bf55284722ad79a59db72bf77fb479c2addc0e6c91b6b16	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	206	1
H-A17-SL-024	.claude/skills/scope-lock-precommit/SKILL.md	ec0d4965ad1012046dfbee08f8c1e46ab29f1694b0b824c24c1adf6aed6d6824	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	HDG	208	1
H-A17-SL-025	.claude/skills/scope-lock-precommit/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	HDG	208	2
H-A17-SL-026	.claude/skills/scope-lock-precommit/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:0	210	2
H-A17-SL-027	.claude/skills/scope-lock-precommit/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:1	211	2
H-A17-SL-028	.claude/skills/scope-lock-precommit/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:1	211	1
H-A17-SL-029	.claude/skills/scope-lock-precommit/SKILL.md	0faf1c4ba861f507fb43bc4e6a7f86dcba9fe37e26d1652919345a06681fc549	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:2	212	1
H-A17-SL-030	.claude/skills/scope-lock-precommit/SKILL.md	b857e923b458a66dcd9eb5a56e2872a5f12c20fb773a4ed2f74e422f42af78c8	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:3	213	1
H-A17-SL-031	.claude/skills/scope-lock-precommit/SKILL.md	726e3b873ec122af6b1026458d002898874701d4f898ceaab47a612b9dd7a8a5	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:4	214	1
H-A17-SL-032	.claude/skills/scope-lock-precommit/SKILL.md	8eaac250774801b2a228d5d3635afd0761450015c3b973a2c311a26956354cbf	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:5	215	1
H-A17-SL-033	.claude/skills/scope-lock-precommit/SKILL.md	241faf47960a1f359d6194ac5d68f48dee2bc38920d85865406c43bee5aaf671	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:6	216	1
H-A17-SL-034	.claude/skills/scope-lock-precommit/SKILL.md	e9b1b2c232e84ef05ead127c8d1b12d32a822b69b956fde8405f0717b93a1022	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:7	217	1
H-A17-SL-035	.claude/skills/scope-lock-precommit/SKILL.md	545f479b2a104f41aa71ed3a62035e01120815a7cc95f80b053a2363bad56420	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:8	218	1
H-A17-SL-036	.claude/skills/scope-lock-precommit/SKILL.md	f3da69a487f3cd25390472e1f39709f5204ec23d869e7baf1247bb5763aae545	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:9	219	1
H-A17-SL-037	.claude/skills/scope-lock-precommit/SKILL.md	2feb72b347d4b8b9174d40127c1763617d34943bd59636458d8d17ef524f4e35	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:10	220	1
H-A17-SL-038	.claude/skills/scope-lock-precommit/SKILL.md	82e605f23431cbcdec8cb4bb8ecf82c244d5949788ab1ee9ca2dc9c63bd96936	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:11	221	1
H-A17-SL-039	.claude/skills/scope-lock-precommit/SKILL.md	6f35d5b597cf4e3cf3a10f39238199ee311d07994ba07dc7b774dc05d639064d	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:12	222	1
H-A17-SL-040	.claude/skills/scope-lock-precommit/SKILL.md	a86dac84b5398a828b85df0bfa4b1cf04a8ca6d054e20e6fd266b5be004b3eb8	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:13	223	1
H-A17-SL-041	.claude/skills/scope-lock-precommit/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:14	224	2
H-A17-SL-042	.claude/skills/scope-lock-precommit/SKILL.md	0b27734b46fbf7ef264d7dcff4505a08b8773717141fac872ecc4d1c686ca54c	# Scope-Lock Pre-Commit > ## Tools	HDG	226	1
H-A17-SL-043	.claude/skills/scope-lock-precommit/SKILL.md	affc2a67f81380dd1f23e749e47a8b45c95dfb2f2e815012a28119d036c6cd55	# Scope-Lock Pre-Commit > ## What this skill does NOT do	HDG	238	1
H-A17-SL-044	.claude/skills/scope-lock-precommit/SKILL.md	ca79336e7086c6fc25a1ff0b3a745146033570abe9134ea0e68c07bdb0119e5d	# Scope-Lock Pre-Commit > ## Failure modes to refuse	HDG	250	1
H-A2-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	f2242a71e777c85dcc9fba6d371d732f3f32551a90854c806728dfb699e9f6bc		FM:2	2	1
H-A2-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	ecbea080fb90dd2680696622a2b0aa7d3de42cf8b7f236253e134ca4fd44aed1	# Scope-Lock Pre-Commit > ## When to trigger	LI:6	33	1
H-A4-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:1	1	2
H-A4-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	182a564dd9617d15098e67e21603946f3bbab6ce67468c3b99ff04ae619f29a0		FM:2	2	1
H-A4-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	b71a2f0efca203eb5e443dae9313869291e722d23721c969e5a1534af2342a93		FM:3	3	1
H-A4-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:4	4	2
H-A6-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	d2a6bb6e34d587c3fd575afc1e25929310cec1497282fd247e42d9f3511288e5	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:3	90	2
H-A6-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	83a28728464fde3e0166373cd8ff4c390f1f345184106db6ff262d6e7afaef65	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:3	90	1
H-A6-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	ee4f8c9f94deb34635c3b2dd737bc2bf3e23a31278dc279dbfbccc866c03a948	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		111	1
H-A6-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	a806a984810f37ec7f36f9a61aff2cedc4e542ef1b766f90279a87f7a57e8329	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		111	3
H-A6-SL-005	.claude/skills/scope-lock-precommit/SKILL.md	d2a6bb6e34d587c3fd575afc1e25929310cec1497282fd247e42d9f3511288e5	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		112	2
H-A6-SL-006	.claude/skills/scope-lock-precommit/SKILL.md	a806a984810f37ec7f36f9a61aff2cedc4e542ef1b766f90279a87f7a57e8329	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 1 — Detect	LI:6	189	3
H-A6-SL-007	.claude/skills/scope-lock-precommit/SKILL.md	a806a984810f37ec7f36f9a61aff2cedc4e542ef1b766f90279a87f7a57e8329	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	202	3
H-A7-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Scope and boundary	LI:2	14	10
H-A7-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	34d88201e28c8dffd715ff4dde242d49a07119689d0df2d9499fb69d242e3ce0	# Scope-Lock Pre-Commit > ## Scope and boundary	LI:2	14	2
H-A7-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	c9766ca413f9e0a07788482d1b3c294c39a054add780c4bb639f98815a2da0ec	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		107	4
H-A7-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	c9766ca413f9e0a07788482d1b3c294c39a054add780c4bb639f98815a2da0ec	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		108	4
H-A7-SL-005	.claude/skills/scope-lock-precommit/SKILL.md	c9766ca413f9e0a07788482d1b3c294c39a054add780c4bb639f98815a2da0ec	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		114	4
H-A7-SL-006	.claude/skills/scope-lock-precommit/SKILL.md	c9766ca413f9e0a07788482d1b3c294c39a054add780c4bb639f98815a2da0ec	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		132	4
H-A7-SL-007	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		167	10
H-A7-SL-008	.claude/skills/scope-lock-precommit/SKILL.md	53cdc2de6c3318c5af0384ae74ee89290a9763cce5df85f376c2cae82e277f0f	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		167	2
H-A7-SL-009	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		170	10
H-A7-SL-010	.claude/skills/scope-lock-precommit/SKILL.md	ab09c3574ac3612c4c7df9bc5e8a9b249d929a9c84c47430663b7ff90ac092e8	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		170	1
H-A7-SL-011	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 1 — Detect	LI:3	184	10
H-A7-SL-012	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	200	10
H-A7-SL-013	.claude/skills/scope-lock-precommit/SKILL.md	2e08a2f61c97d2ce57edb668f939bbf35345df37c00bc43047a981d49976b327	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	200	2
H-A7-SL-014	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	204	10
H-A7-SL-015	.claude/skills/scope-lock-precommit/SKILL.md	53cdc2de6c3318c5af0384ae74ee89290a9763cce5df85f376c2cae82e277f0f	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	204	2
H-A7-SL-016	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:4	214	10
H-A7-SL-017	.claude/skills/scope-lock-precommit/SKILL.md	3d9c4ec3dc63a4674a48370eca6b17dcf0eee65079d68635cf71aa4bafea0945	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:4	214	1
H-A7-SL-018	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:9	219	10
H-A7-SL-019	.claude/skills/scope-lock-precommit/SKILL.md	34d88201e28c8dffd715ff4dde242d49a07119689d0df2d9499fb69d242e3ce0	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:9	219	2
H-A7-SL-020	.claude/skills/scope-lock-precommit/SKILL.md	0ed3a02e2c7d0260668207f20092953b14cb1127e27441373323a618706d1658	# Scope-Lock Pre-Commit > ## What this skill does NOT do	LI:6	248	1
H-A7-SL-021	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## What this skill does NOT do	LI:6	248	10
H-A7-SL-022	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Failure modes to refuse	LI:3	254	10
H-A7-SL-023	.claude/skills/scope-lock-precommit/SKILL.md	2e08a2f61c97d2ce57edb668f939bbf35345df37c00bc43047a981d49976b327	# Scope-Lock Pre-Commit > ## Failure modes to refuse	LI:3	254	2
H-A8-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	c30b534a6c044c34b2731c31e32200bdbe2491861a909ab01841d2f7b4a7e5f7	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:1	81	1
H-A8-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	4579e65a7499f2d166fd474db5a78e56aba3eb3815190ba5b0104763b7cd8c59	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:2	85	1
H-A8-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	c1f4e8d5e6068247621a6de76e2c1527ae7683559b0ec19707d4749c1e37b81a	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:2	85	2
H-A8-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	ba550776ddb0f13bfc9b6cd372a35f79a31dda6e14cdf6ae62eef2c7f36ab1b2	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:2	85	2
H-A8-SL-005	.claude/skills/scope-lock-precommit/SKILL.md	ba550776ddb0f13bfc9b6cd372a35f79a31dda6e14cdf6ae62eef2c7f36ab1b2	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:2	86	2
H-A8-SL-006	.claude/skills/scope-lock-precommit/SKILL.md	c1f4e8d5e6068247621a6de76e2c1527ae7683559b0ec19707d4749c1e37b81a	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:2	87	2
H-A8-SL-007	.claude/skills/scope-lock-precommit/SKILL.md	5dcc10778c78fe1bf47e0e8753804f568e6e45b160afdee55e11cf117782ead5	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:3	89	1
H-B3-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	ef3033de9e9b7096ae4837801cba57c4341b721c4e46598716170f64a960fd7c	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		133	1
H-B3-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	919061e6c7c6dd81bb22c3c0db2a36f5e1ab54b4ebfb3b96978bf5c51d3445f5	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		169	1
H-A16-RT-001	docs/PRD_REVIEW_TEMPLATE.md	3673fc649802a6c38cbe756df29eb3263f481f494ed94bdc1202713f473a8c75	# PRD Review Template	HDG	1	1
H-A16-RT-002	docs/PRD_REVIEW_TEMPLATE.md	d7537f84dc2a577d3e85664613fd6241c3b450979c263b8413bf1b27d38f716d	# PRD Review Template > ## Required sections (in order)	HDG	25	1
H-A16-RT-003	docs/PRD_REVIEW_TEMPLATE.md	36524c47b7c0d00f2814e313bd4d439ebc2c5b505e0ccfbb5c1adf820624712b	# PRD Review Template > ## Required sections (in order) > ### 1. Strengths	HDG	27	1
H-A16-RT-004	docs/PRD_REVIEW_TEMPLATE.md	4597748d300dc2646515bfa4bd6419c754cafa8e8d7de43001fdeb0cbace4f4a	# PRD Review Template > ## Required sections (in order) > ### 2. Cohesiveness	HDG	39	1
H-A16-RT-005	docs/PRD_REVIEW_TEMPLATE.md	d3c20477920a5f402f4958057fa3a2ce1c4094ac8d003ae5202ca0a6474fff3b	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	HDG	50	1
H-A16-RT-006	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:0	54	10
H-A16-RT-007	docs/PRD_REVIEW_TEMPLATE.md	a58f105d8871794efd215614e752675e4d95072a963699480e20accdd9bfe278	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:1	55	1
H-A16-RT-008	docs/PRD_REVIEW_TEMPLATE.md	d224178d0744e1bfa3bd5a95fd816c64348a4e43ea752c878433a5a31770ec97	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:2	56	1
H-A16-RT-009	docs/PRD_REVIEW_TEMPLATE.md	74240630ae75836f14eae0149a20722b12219ad1492ce510be47426c712a6831	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:3	57	1
H-A16-RT-010	docs/PRD_REVIEW_TEMPLATE.md	2a3b91bc2f99cf5a850a1fb3391382867ce9827b4aa7555abf896a5e6220ce9f	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:4	58	1
H-A16-RT-011	docs/PRD_REVIEW_TEMPLATE.md	0aef7a862f47aef7f27b49ed290e8656744bebf98b12735e222f0ae806f4aedd	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:5	59	1
H-A16-RT-012	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:6	60	10
H-A16-RT-013	docs/PRD_REVIEW_TEMPLATE.md	c5b7b6a4318b677d9a6cb2515c64518719db31e9f63a2c2c74ce45b56fe9ae69	# PRD Review Template > ## Required sections (in order) > ### 4. Revised PRD	HDG	69	1
H-A16-RT-014	docs/PRD_REVIEW_TEMPLATE.md	35cd446265fa521fb65d8dffd69ced9ff051b5207f2c6f2ae6ecaf3e8df6b735	# PRD Review Template > ## Pre-publish checklist (reviewer must answer "yes" to each)	HDG	83	1
H-A16-RT-015	docs/PRD_REVIEW_TEMPLATE.md	a27adc9c998492c3954561dfb8c365db7b972952d0c0f846b4b85b8526759fd7	# PRD Review Template > ## Token discipline	HDG	110	1
H-A16-RT-016	docs/PRD_REVIEW_TEMPLATE.md	cf89d213c1aa08ce57bf3f75a5ce137339b66429b9d2030b6e6c91afc138db9c	# PRD Review Template > ## When to skip the Revised PRD section	HDG	127	1
H-A16-RT-017	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## When to skip the Revised PRD section	F2:0	132	10
H-A16-RT-018	docs/PRD_REVIEW_TEMPLATE.md	297877e6ba7dd30cc1903ba18db2eba9d95a78231314d74e79e12e0c0619dd13	# PRD Review Template > ## When to skip the Revised PRD section	F2:1	133	1
H-A16-RT-019	docs/PRD_REVIEW_TEMPLATE.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# PRD Review Template > ## When to skip the Revised PRD section	F2:2	134	4
H-A16-RT-020	docs/PRD_REVIEW_TEMPLATE.md	d932370c8fd108584cca04db7721690a8ae11a4f37681ad48508adf12724ccc9	# PRD Review Template > ## When to skip the Revised PRD section	F2:3	135	1
H-A16-RT-021	docs/PRD_REVIEW_TEMPLATE.md	bed1130336b9f4e72cc57cd1aa464b76092834b84c9984871c8377ac075884bd	# PRD Review Template > ## When to skip the Revised PRD section	F2:4	136	1
H-A16-RT-022	docs/PRD_REVIEW_TEMPLATE.md	cdd077c9756800ae322f9613f761472f1848fdb6030cba88d8196c8afb6b96c6	# PRD Review Template > ## When to skip the Revised PRD section	F2:5	137	1
H-A16-RT-023	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## When to skip the Revised PRD section	F2:6	138	10
H-A16-RT-024	docs/PRD_REVIEW_TEMPLATE.md	856b142238a2aacd1d57d3ecaf5f32847c1367c39e2bb73c39f11197a9ffce02	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	HDG	144	1
H-A16-RT-025	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:0	156	10
H-A16-RT-026	docs/PRD_REVIEW_TEMPLATE.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:1	157	1
H-A16-RT-027	docs/PRD_REVIEW_TEMPLATE.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:1	157	2
H-A16-RT-028	docs/PRD_REVIEW_TEMPLATE.md	7fed46854b57d36b7e9d1e21c7b3c8dfba6b580cd629d427e83ad4cfe43126a4	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:2	158	1
H-A16-RT-029	docs/PRD_REVIEW_TEMPLATE.md	36c86fa017851c89910d324ab67f4fc1a7b61f623fe00a179bdc332e1bdda2a8	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:2	158	1
H-A16-RT-030	docs/PRD_REVIEW_TEMPLATE.md	ce04d5c2a7222e0d9e12cc0bc7db23aadfe321175463c27d72fe9ec440f2d6fe	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:3	159	1
H-A16-RT-031	docs/PRD_REVIEW_TEMPLATE.md	72b4e29e40c010c4dd85eb29e04482be685022b1ea3ba191f54a37e55bab7383	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:3	159	1
H-A16-RT-032	docs/PRD_REVIEW_TEMPLATE.md	1984dbbb744cc37eb3cbba12ddc08b260ecb70e936cf4778d5a9bb4c3d989d5d	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:4	160	1
H-A16-RT-033	docs/PRD_REVIEW_TEMPLATE.md	6d80bd100c49a1b843eadc1ea154a42c8b0f0cf6d4e7cb42721cd6afd572ffbb	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:4	160	1
H-A16-RT-034	docs/PRD_REVIEW_TEMPLATE.md	99c728a8afee3a9bd73e07473d10ac90cd145a1f90234b0107e21be62d7bd903	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:4	160	1
H-A16-RT-035	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:5	161	10
H-A16-RT-036	docs/PRD_REVIEW_TEMPLATE.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:5	179	2
H-A16-RT-037	docs/PRD_REVIEW_TEMPLATE.md	6e817fadc50fd0d18d5dd1bba51b424c51716583837df24efca931a19ae8c679	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	HDG	192	1
H-A16-RT-038	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:0	200	10
H-A16-RT-039	docs/PRD_REVIEW_TEMPLATE.md	c516eaca8548ab007ef61ce81d431a0bf66bf61c26ab8733fa1d0ce6f51a1b64	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:1	201	2
H-A16-RT-040	docs/PRD_REVIEW_TEMPLATE.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:2	202	4
H-A16-RT-041	docs/PRD_REVIEW_TEMPLATE.md	0bf7abe4ecc1549f5a2ed04282c1a1c1ac8c21989f56cfbaa027141d8af334ff	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:3	203	1
H-A16-RT-042	docs/PRD_REVIEW_TEMPLATE.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:4	204	4
H-A16-RT-043	docs/PRD_REVIEW_TEMPLATE.md	5d5b07cb393712f36b1d15b1af6ec033dae2ca4b8cb1257c0715914a7c1ce19b	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:5	205	1
H-A16-RT-044	docs/PRD_REVIEW_TEMPLATE.md	a94a8c3aecb6b73638cc5e318fdce6a304ef3b726f639bd46e402b06eaa03c17	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:6	206	1
H-A16-RT-045	docs/PRD_REVIEW_TEMPLATE.md	0011fdb6831bb88e458380123f3b4b60cfc52145ad90213acce85e288a5db03d	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:7	207	1
H-A16-RT-046	docs/PRD_REVIEW_TEMPLATE.md	a268cb5b97216ab1f8af44a07eae9369cfbe144ca3f5dfa743bb5d2f75116c82	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:8	208	1
H-A16-RT-047	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:9	209	10
H-A16-RT-048	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F5:0	249	10
H-A16-RT-049	docs/PRD_REVIEW_TEMPLATE.md	c516eaca8548ab007ef61ce81d431a0bf66bf61c26ab8733fa1d0ce6f51a1b64	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F5:1	250	2
H-A16-RT-050	docs/PRD_REVIEW_TEMPLATE.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F5:2	251	4
H-A16-RT-051	docs/PRD_REVIEW_TEMPLATE.md	45a3564ce64c71491dca64c025dcba292ce9b484b4b427dcbed13670531846da	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F5:3	252	1
H-A16-RT-052	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F5:4	253	10
H-A2-RT-001	docs/PRD_REVIEW_TEMPLATE.md	3f48209fc3b8c4afd0c163a813f88fd3933298a954b6590b71c1e033459214ca	# PRD Review Template > ## Review Independence (required, PRD-121 R4)		148	2
H-A2-RT-002	docs/PRD_REVIEW_TEMPLATE.md	3f48209fc3b8c4afd0c163a813f88fd3933298a954b6590b71c1e033459214ca	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:5	184	2
H-A5-RT-001	docs/PRD_REVIEW_TEMPLATE.md	851833bccec8dac2405286643c443217562a118de745165c42795adf60206374	# PRD Review Template		12	1
H-A5-RT-002	docs/PRD_REVIEW_TEMPLATE.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# PRD Review Template		12	1
H-A5-RT-003	docs/PRD_REVIEW_TEMPLATE.md	bf4d4f07ca20ecf326cb39537e81d8c7ffc0eb455aca91ff7c784cba0c7403db	# PRD Review Template		13	1
H-A5-RT-004	docs/PRD_REVIEW_TEMPLATE.md	e67d48636eb40d75b05f6059ff92b3ff77da83687f90195a3cb209b26f9b2c85	# PRD Review Template		15	1
H-A5-RT-005	docs/PRD_REVIEW_TEMPLATE.md	4b71304c195ae124a9413429409034b44c58f6560e3f10bb65cd2433c31aa66c	# PRD Review Template > ## Review Independence (required, PRD-121 R4)		151	1
H-A5-RT-006	docs/PRD_REVIEW_TEMPLATE.md	a8ce16a33fe58bfdfdbb35184c54e4508ca4bb43a1f327d8c604ea29c7aa34ec	# PRD Review Template > ## Review Independence (required, PRD-121 R4)		151	1
H-A7-RT-001	docs/PRD_REVIEW_TEMPLATE.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:2	166	3
H-A7-RT-002	docs/PRD_REVIEW_TEMPLATE.md	53cdc2de6c3318c5af0384ae74ee89290a9763cce5df85f376c2cae82e277f0f	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:2	166	1
H-A7-RT-003	docs/PRD_REVIEW_TEMPLATE.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:3	170	3
H-A7-RT-004	docs/PRD_REVIEW_TEMPLATE.md	ab09c3574ac3612c4c7df9bc5e8a9b249d929a9c84c47430663b7ff90ac092e8	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:3	170	1
H-A7-RT-005	docs/PRD_REVIEW_TEMPLATE.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:3	170	3
H-A7-RT-006	docs/PRD_REVIEW_TEMPLATE.md	4b69257cb09896c40149b7ce1e1d6209c713552d0b60035acd7d0d73ebf88ddd	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:3	170	1
H-B3-RT-001	docs/PRD_REVIEW_TEMPLATE.md	e8570a6b4d4f80332858d79571880ccba2318e37d35c78fe04702faad089aefd	# PRD Review Template		20	1
```

### 5.5 POST manifest (final worktree = I)

```tsv
H-A11-CM-001	CLAUDE.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:10	139	1
H-A12-CM-001	CLAUDE.md	2ab9818f93b1cb302e3004a42db83b7795de9ddb396a685db7536c16926a8a7a	# CLAUDE.md > ## Modes (Layer 2)		70	1
H-A12-CM-002	CLAUDE.md	dd24f4039d494cc1f0a47b5d33d2ef9c2503cd7cad56a109041fabf83d1dee2d	# CLAUDE.md > ## Modes (Layer 2)		71	1
H-A12-CM-003	CLAUDE.md	a56cc5066bfa8699a7ff3dcbb3b5e837010a0b4a4f0e9d933e0b0df2bf6fb525	# CLAUDE.md > ## Modes (Layer 2)		72	1
H-A13-CM-001	CLAUDE.md	4c6a5dbb16174b3d545952f69df203330ad34889e288b31b5c3b56bc1409f1f9	# CLAUDE.md > ## Session start		149	1
H-A13-CM-002	CLAUDE.md	270f1d910823c3ad2a27bd2ad9fb5a0864ad297764d2fd7f890e2fd27e9d1a95	# CLAUDE.md > ## Session start		149	1
H-A13-CM-003	CLAUDE.md	ea5ca4ca3591e50f7b9f33faf16e3d99e243a65e35521bfb13344b693872075a	# CLAUDE.md > ## Session start		150	1
H-A13-CM-004	CLAUDE.md	32107fe5eebe12df8280125d5ff78519f86854704e7bf94227110ee17a74c09f	# CLAUDE.md > ## Session start		150	1
H-A14-CM-001	CLAUDE.md	b2788d7144b6d2cda95eda69f4456c3666f40ecb566f82d038a10ae9a97af2d5	# CLAUDE.md	HDG	1	1
H-A14-CM-002	CLAUDE.md	61e9f61ec5d02b78d9604b8f72e7aca071031cfe7c8442a944f76aa0cd39ba66	# CLAUDE.md > ## Ratification	HDG	11	1
H-A14-CM-003	CLAUDE.md	daf799c4481a60a0bc68c75e9f0d11071a292f44d03f2ed1a2ff8dfced4ed121	# CLAUDE.md > ## The wall (absolute; no charge, mode, or prompt overrides it)	HDG	19	1
H-A14-CM-004	CLAUDE.md	b5611ac15c0cfd03def2c4874be8fbff2622c099b8f28d9c270823e7b9345db0	# CLAUDE.md > ## The wall (absolute; no charge, mode, or prompt overrides it)	LI:7	39	1
H-A14-CM-005	CLAUDE.md	30493a431f3c4180181e60113018c96c24f9f8c6b01bc8725e3e8a01a21b02ae	# CLAUDE.md > ## Owner holds (exclusive to Dustin; no agent issues or infers these)	HDG	45	1
H-A14-CM-006	CLAUDE.md	a504e08469469107fca398daa452db1de42e1a7c556947fada935b61092a03da	# CLAUDE.md > ## Precedence (on genuine conflict between two applicable authorities, STOP)	HDG	54	1
H-A14-CM-007	CLAUDE.md	ffa00a4b3e57de48cda12355dc2838559a83c5daffecbd020c16c3f98a0235b1	# CLAUDE.md > ## Modes (Layer 2)	HDG	67	1
H-A14-CM-008	CLAUDE.md	ac6d273c773446e61c4ba100be863aeb8d56261042f6665457b7ab6e7f80c957	# CLAUDE.md > ## Retained invariants (bind in every mode)	HDG	81	1
H-A14-CM-009	CLAUDE.md	993e9a76aaf48701540a8971f515a7bf73a89f9d32160d275b9baf28a15a4634	# CLAUDE.md > ## Retained invariants (bind in every mode)		97	1
H-A14-CM-010	CLAUDE.md	0119af1db59c8e66643e70c3a687926478085db6b66e92c869e026e537168cd7	# CLAUDE.md > ## Roles	HDG	102	1
H-A14-CM-011	CLAUDE.md	040e5ebc4f912a6cc3175fc4d8327026f7cb5c4aa0a4478541c92fac27472840	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	HDG	122	1
H-A14-CM-012	CLAUDE.md	3288bad4a0f3a97491e231111c3fe0ab9a5f272912303df130feb71300f4e40a	# CLAUDE.md > ## Session start	HDG	144	1
H-A14-CM-013	CLAUDE.md	16b40b8d2a484e2b54b2d0e57f0e4a448d762959c9064ebcc90836298775aa1d	# CLAUDE.md > ## Context and output hygiene (standing behavior, every session)	HDG	152	1
H-A14-CM-014	CLAUDE.md	1edd85bf9a67ed33fb2eea914f2d83f115a9fdb1ff8d260d4f7fc808377efe9e	# CLAUDE.md > ## Context and output hygiene (standing behavior, every session)	LI:1	154	1
H-A14-CM-015	CLAUDE.md	2d7b716cde65fe0b172d6533a5e686a76e8eebe67b01ea6378e15fcc7dcba2d0	# CLAUDE.md > ## Anti-patterns	HDG	169	1
H-A15-CM-001	CLAUDE.md	94391f153aba278bd2c23573c32372b39b43113a2df356384ced5d6d20937eff	# CLAUDE.md > ## Ratification		13	1
H-A15-CM-002	CLAUDE.md	3025f5ddb307c7360f922179dfca5facd9c9a507aa9e362d9b0f23b8946a8dcc	# CLAUDE.md > ## Ratification		14	1
H-A15-CM-003	CLAUDE.md	a95b4dbd83a143a60a9b0a7dbce6a73a35cacaf35d9d2f096b3f20dbb2e34179	# CLAUDE.md > ## Ratification		14	1
H-A15-CM-004	CLAUDE.md	3bb2effa2aebfbb6801541c74805773681e430eae83899f9df917b7c6e95fba3	# CLAUDE.md > ## Ratification		15	1
H-A15-CM-005	CLAUDE.md	55bd2626a625d18651842113017d91d307a778fa1b191a629db63ef0274c78b0	# CLAUDE.md > ## Ratification		15	1
H-A15-CM-006	CLAUDE.md	7bba5c85e56370cb29c215ec94775b5d9a3bf0d5e4b80851800b20abf0d68f6c	# CLAUDE.md > ## Ratification		16	1
H-A15-CM-007	CLAUDE.md	8d7884e50a2f4a8b00910d19bfa2802ffe555f5db10e209d4e8e61878f61559d	# CLAUDE.md > ## Ratification		16	1
H-A15-CM-008	CLAUDE.md	0e783d1a821909ef2bccb4f0d99b1c29e592579b16ea5e33fae1750e0a1f0887	# CLAUDE.md > ## Ratification		16	1
H-A15-CM-009	CLAUDE.md	4ae32277a536f23c349afb21ded2fdef251061be1940f29d37166af965508d84	# CLAUDE.md > ## Ratification		17	1
H-A15-CM-010	CLAUDE.md	d37469a2ee1629aae9ddda1af8a4afd07c3e9dcbde5b42bc338dfbb9143a545d	# CLAUDE.md > ## Owner holds (exclusive to Dustin; no agent issues or infers these)	LI:4	51	2
H-A15-CM-011	CLAUDE.md	88191af5f0ad451de905236f651ad4680eff0bc794ed4a171e7e8140b16fb1d8	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:6	131	1
H-A15-CM-012	CLAUDE.md	d37469a2ee1629aae9ddda1af8a4afd07c3e9dcbde5b42bc338dfbb9143a545d	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:7	133	2
H-A15-CM-013	CLAUDE.md	1414b45aca9a69e1ddcebd592b76818fac5216d12f58e7c6bf604f98216e1efc	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:7	134	1
H-A15-CM-014	CLAUDE.md	09b23593d9f9580cf4e4c4f7a35610dccc9db17a31725a7bf108f056f558fba0	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:11	141	1
H-A18-CM-001	CLAUDE.md	f27ac6f39d89fe021c56900069198aa7d9968f2cd6645c00b11ffd1b78fcf546	# CLAUDE.md > ## Retained invariants (bind in every mode)		93	1
H-A7-CM-001	CLAUDE.md	1ec7904fb1ae4e2f91ca730f6cb6be360132dee919f6a21386d041ddd39d6cae	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:5	129	1
H-A7-CM-002	CLAUDE.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:5	129	1
H-B3-CM-001	CLAUDE.md	fb93b282e8608b68723b814facb03e068db62e4be93ade88c97197cbdf0d01d4	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:5	130	1
H-B3-CM-002	CLAUDE.md	919061e6c7c6dd81bb22c3c0db2a36f5e1ab54b4ebfb3b96978bf5c51d3445f5	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:5	130	1
H-B3-CM-003	CLAUDE.md	bf2b3717dfefb295aa556908f1382c03a7533a5a1e7e991a3a2413d28faf7e6d	# CLAUDE.md > ## Canonical sources (reference by name; do not duplicate)	LI:5	130	1
H-B5-CM-001	CLAUDE.md	28b06784002a6f371bb4e99efa2b40da696c00e7f409fc48d231fb6e36e5354a	# CLAUDE.md > ## Precedence (on genuine conflict between two applicable authorities, STOP)	LI:6	62	1
H-B6-CM-001	CLAUDE.md	fca16cae5b0e32edfa6b55eaa32a98ffbf4a0c7d885fb585785fc83b6ea2d9c3	# CLAUDE.md > ## Retained invariants (bind in every mode)		94	1
H-B6-CM-002	CLAUDE.md	c114278ca2d65f625aedda9a17c8bef83d097f002880a43b4e81ad7bf0b1e3ec	# CLAUDE.md > ## Retained invariants (bind in every mode)		99	1
H-B6-CM-003	CLAUDE.md	7d39790f142e05b8308584856a366a2b729053f1420b4ee544da9e90ee2bbc72	# CLAUDE.md > ## Retained invariants (bind in every mode)		99	1
H-B6-CM-004	CLAUDE.md	77cf032cbbc45b8e2c8f49c7035505045f5500db9dd048c347739134633c2506	# CLAUDE.md > ## Retained invariants (bind in every mode)		100	1
H-B6-CM-005	CLAUDE.md	88636d2769930e3e701c64fbf0ef7d46810b89d9798446fee7e9c2d47597ddf8	# CLAUDE.md > ## Retained invariants (bind in every mode)		100	1
H-A11-CH-001	docs/CLAUDE_HOOKS.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard		29	1
H-A18-CH-001	docs/CLAUDE_HOOKS.md	27519bb40111622567febbcb6fc0f1c84ac74484c1559efa7e440c6b6edefd19	# Claude Code Hooks - Workflow Reference	HDG	1	1
H-A18-CH-002	docs/CLAUDE_HOOKS.md	f27ac6f39d89fe021c56900069198aa7d9968f2cd6645c00b11ffd1b78fcf546	# Claude Code Hooks - Workflow Reference		3	3
H-A18-CH-003	docs/CLAUDE_HOOKS.md	dfc54351aa6127d5f66bd281ff41483e440380f6ad7d5fec4d60a19789fa8122	# Claude Code Hooks - Workflow Reference > ## Wired hooks	HDG	6	1
H-A18-CH-004	docs/CLAUDE_HOOKS.md	c7bfd735700fc3f158ee2fdad2fca24752ffabae63dbc46d619e2396d2f3926d	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:Script	8	1
H-A18-CH-005	docs/CLAUDE_HOOKS.md	4da1ec6f47782090102dc16bda978efb5655fbf2ddce0f84ecf1faf79a930f2d	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:---	9	1
H-A18-CH-006	docs/CLAUDE_HOOKS.md	63f7c625cf69c1e6e78b3267f6a286fc4a1b73c6d4a38ef747dc007c64c2b1e1	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`protect_files.sh`	10	1
H-A18-CH-007	docs/CLAUDE_HOOKS.md	c9b57726f9b9e37a1e56c0efb803cce5812fe355d1ff61311c61845a85ffef55	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`prd_eval.sh`	11	1
H-A18-CH-008	docs/CLAUDE_HOOKS.md	03f1d2676a5ee27d57f2e89342ef1d5b5cf17e6b7372f84b8a3be2a7e23442ef	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`canonical_read_guard.sh`	12	1
H-A18-CH-009	docs/CLAUDE_HOOKS.md	f242e294cd8bf8e73e3c6a5f4d6317cd97575293a68b93eb6c8841c797d4f88a	# Claude Code Hooks - Workflow Reference > ## Wired hooks		15	1
H-A18-CH-010	docs/CLAUDE_HOOKS.md	9b5c7a8ea53163aa7fa627192315e1aa846922c450111ab5f0fc2128a497f9c7	# Claude Code Hooks - Workflow Reference > ## Wired hooks		15	1
H-A18-CH-011	docs/CLAUDE_HOOKS.md	50bba48fb4687d404479049d0fe89a3a43f663569837cd647b6866664bd9aacb	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard	HDG	18	1
H-A18-CH-012	docs/CLAUDE_HOOKS.md	f27ac6f39d89fe021c56900069198aa7d9968f2cd6645c00b11ffd1b78fcf546	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard		20	3
H-A18-CH-013	docs/CLAUDE_HOOKS.md	c42f14bd214bdcd26e9cbf9c6edb75cc6dcfc8f729cd1b5b253a43f05ebdc67b	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard		27	1
H-A18-CH-014	docs/CLAUDE_HOOKS.md	2f401cee56370841fd312ee9a02caf63b4d28b809fb6b277d3e26cbb64b7a466	# Claude Code Hooks - Workflow Reference > ## prd_eval.sh - registry-gap check	HDG	38	1
H-A18-CH-015	docs/CLAUDE_HOOKS.md	387294ffdae67c6c11733980388841d4415be458c2f345b148a6e2f5c2a8da69	# Claude Code Hooks - Workflow Reference > ## prd_eval.sh - registry-gap check		44	1
H-A18-CH-016	docs/CLAUDE_HOOKS.md	a64c32b7517eea07d265d841050ae7ada6136b3291e587ac2fbe43800a8569b2	# Claude Code Hooks - Workflow Reference > ## canonical_read_guard.sh - redundant canonical-doc re-read reminder	HDG	46	1
H-A18-CH-017	docs/CLAUDE_HOOKS.md	c065296ded4cf2ebc1df0cc1723ac3a5d7ed98c3879e3c261c0a42d6d5a58f9c	# Claude Code Hooks - Workflow Reference > ## Commit / push	HDG	55	1
H-A18-CH-018	docs/CLAUDE_HOOKS.md	f27ac6f39d89fe021c56900069198aa7d9968f2cd6645c00b11ffd1b78fcf546	# Claude Code Hooks - Workflow Reference > ## Commit / push		58	3
H-B6-CH-001	docs/CLAUDE_HOOKS.md	1b18c0911b9309b7818ba961d4d3ac4c2c9be7d914224646629fc6f12ecc7c3c	# Claude Code Hooks - Workflow Reference		3	2
H-B6-CH-002	docs/CLAUDE_HOOKS.md	6015fa7d4a3a31de670b0ee8772016e8f90f824eae3e156ad8d1cda4a5f7a201	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`protect_files.sh`	10	3
H-B6-CH-003	docs/CLAUDE_HOOKS.md	45e83e4cb495b00a7da3623fb5bfe43bbabce862262b26cbc119bd93d9130b29	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`prd_eval.sh`	11	2
H-B6-CH-004	docs/CLAUDE_HOOKS.md	d6140f5e5e98af2e060b03bf084910a46781d67b811aa2e9c8ab6987fdc4e74c	# Claude Code Hooks - Workflow Reference > ## Wired hooks	ROW:`canonical_read_guard.sh`	12	2
H-B6-CH-005	docs/CLAUDE_HOOKS.md	6015fa7d4a3a31de670b0ee8772016e8f90f824eae3e156ad8d1cda4a5f7a201	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard	HDG	18	3
H-B6-CH-006	docs/CLAUDE_HOOKS.md	1b18c0911b9309b7818ba961d4d3ac4c2c9be7d914224646629fc6f12ecc7c3c	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard		27	2
H-B6-CH-007	docs/CLAUDE_HOOKS.md	6015fa7d4a3a31de670b0ee8772016e8f90f824eae3e156ad8d1cda4a5f7a201	# Claude Code Hooks - Workflow Reference > ## protect_files.sh - protected-file guard		27	3
H-B6-CH-008	docs/CLAUDE_HOOKS.md	45e83e4cb495b00a7da3623fb5bfe43bbabce862262b26cbc119bd93d9130b29	# Claude Code Hooks - Workflow Reference > ## prd_eval.sh - registry-gap check	HDG	38	2
H-B6-CH-009	docs/CLAUDE_HOOKS.md	d6140f5e5e98af2e060b03bf084910a46781d67b811aa2e9c8ab6987fdc4e74c	# Claude Code Hooks - Workflow Reference > ## canonical_read_guard.sh - redundant canonical-doc re-read reminder	HDG	46	2
H-A11-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	106	1
H-A11-PA-002	.claude/skills/prd-authoring-verified/SKILL.md	f4f1f60a1a29b4b24265e0be159d690d6e342b65c3833d7b2f06b0dbfad60137	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	106	1
H-A14-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	1edd85bf9a67ed33fb2eea914f2d83f115a9fdb1ff8d260d4f7fc808377efe9e	# PRD Authoring with Built-in Verification > ## Tools	LI:8	155	1
H-A17-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	be0c4c3e4d16347f0c0bbf1722d1aeec9afdd8cc887f0ea9b7766428671743f0	# PRD Authoring with Built-in Verification	HDG	6	1
H-A17-PA-002	.claude/skills/prd-authoring-verified/SKILL.md	c31df17b020896f4408b594dcc87b654acc34d6cffea342410e54300430ff505	# PRD Authoring with Built-in Verification > ## Scope and boundary	HDG	8	1
H-A17-PA-003	.claude/skills/prd-authoring-verified/SKILL.md	0632f7b817601f2c4399f83a1a85ede2ad5c99cacf601e68d5b3471191771451	# PRD Authoring with Built-in Verification > ## When to trigger	HDG	26	1
H-A17-PA-004	.claude/skills/prd-authoring-verified/SKILL.md	90e48a7f751783169d5e801f211330144685188ec27ea465b4e6e633a858f180	# PRD Authoring with Built-in Verification > ## Operating modes	HDG	37	1
H-A17-PA-005	.claude/skills/prd-authoring-verified/SKILL.md	18a8b5df2208e00d1ba8e7bc8fb538a3625dbfb4e8dc25158debce2a964c237d	# PRD Authoring with Built-in Verification > ## Hard rule: no invented references	HDG	51	1
H-A17-PA-006	.claude/skills/prd-authoring-verified/SKILL.md	a2d449b06e0d38d92f7ffe6f9919e3cccb1587c59c57ce2ccd1c42f408f2991a	# PRD Authoring with Built-in Verification > ## Two-phase contract	HDG	74	1
H-A17-PA-007	.claude/skills/prd-authoring-verified/SKILL.md	b2dc9baa601a8d4b7464fcf623c472e29427f0554626f54b9de95bf9b64bda4d	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	HDG	76	1
H-A17-PA-008	.claude/skills/prd-authoring-verified/SKILL.md	0da21edcb876fd89fc8bb92d7c2e872bbf93feb24097ad037a23ab3fcb97cf93	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	HDG	94	1
H-A17-PA-009	.claude/skills/prd-authoring-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)		96	3
H-A17-PA-010	.claude/skills/prd-authoring-verified/SKILL.md	0610a4eb29cfa5edd7b763f1128ea544350f7480fec7c8f82cd55d6e104b971e	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:#	100	1
H-A17-PA-011	.claude/skills/prd-authoring-verified/SKILL.md	12af00ef4beed04e98324a76d971f94419a92b77311cf21629020e3449b8f457	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:---	101	1
H-A17-PA-012	.claude/skills/prd-authoring-verified/SKILL.md	79f77ecad50bf2b2c2bd1546d8e215aa369dd8f6a9ba87b92c3b93d9ab0d6d49	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V1	102	1
H-A17-PA-013	.claude/skills/prd-authoring-verified/SKILL.md	982414182e279823a7339e0214e04dc409ca532a9b5e95dba0b7700a51dcfd87	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V2	103	1
H-A17-PA-014	.claude/skills/prd-authoring-verified/SKILL.md	762573c2622c85f53fa0149fc843389b4dbaea8ec61207ecb2306aec3ab957bd	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	104	1
H-A17-PA-015	.claude/skills/prd-authoring-verified/SKILL.md	0b2ade07bbfcca905eee7bc31ae89c406fb619457e0eb4c0822ae9ec9c8bf90e	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	105	1
H-A17-PA-016	.claude/skills/prd-authoring-verified/SKILL.md	6816f0b71f9c5027bed363429eeb6a925e0dd692b3f363027f5823f8a460a640	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	106	1
H-A17-PA-017	.claude/skills/prd-authoring-verified/SKILL.md	96eb43aca7aacf44bf34ea18939fb3fc46e3b24c7958d506a9eabe4416197142	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V6	107	1
H-A17-PA-018	.claude/skills/prd-authoring-verified/SKILL.md	d5460698e6520239f9ebb11a6cacf5e98c0d8861610aa0302ebd1a23122f88f8	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	108	1
H-A17-PA-019	.claude/skills/prd-authoring-verified/SKILL.md	16b6a19e5a3e6a4c1e899ee6e9642055ab6b860f34a63eccb6a6cb0f07132084	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	109	1
H-A17-PA-020	.claude/skills/prd-authoring-verified/SKILL.md	03b6fa2d01d8efa45d0df4e9da005ff7d5272c3862234dd323226a7a16e9e90a	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	110	1
H-A17-PA-021	.claude/skills/prd-authoring-verified/SKILL.md	47ff84a3ed75a35740ad31be122c60287278ae5bbbf8d67e3030c423bd6c76c9	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V10	111	1
H-A17-PA-022	.claude/skills/prd-authoring-verified/SKILL.md	458bea3f0da685f2ef0c57edb796ada73a563e370ed8402891fc30b20daae05c	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	HDG	113	1
H-A17-PA-023	.claude/skills/prd-authoring-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	HDG	113	3
H-A17-PA-024	.claude/skills/prd-authoring-verified/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:0	115	2
H-A17-PA-025	.claude/skills/prd-authoring-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:1	116	3
H-A17-PA-026	.claude/skills/prd-authoring-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:1	116	1
H-A17-PA-027	.claude/skills/prd-authoring-verified/SKILL.md	d1efd8b4efafd24b7e2a9b15296d9957b48fb37ab57820ca3806de27c456e3b0	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:2	117	1
H-A17-PA-028	.claude/skills/prd-authoring-verified/SKILL.md	fa444269c66fb5b00cfbc1cf26ddf044e8eb8428375d10ccbd4ccfb6621db612	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:3	118	1
H-A17-PA-029	.claude/skills/prd-authoring-verified/SKILL.md	1e96a3450bd6f864e588e5ba0d77a1c11f9537bc16ce19e101604995514068c6	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:4	119	1
H-A17-PA-030	.claude/skills/prd-authoring-verified/SKILL.md	c83a969e63c6e00130ed9b3cea9bbf3a01d88b9a7653d65e34c57f6ac34d706d	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:5	120	1
H-A17-PA-031	.claude/skills/prd-authoring-verified/SKILL.md	04bb0f68fd83c5ed89bf88ef6598934e008657b5b1c607bd6080b59fdca1541d	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:6	121	1
H-A17-PA-032	.claude/skills/prd-authoring-verified/SKILL.md	39929edabcb560d5efc9e0b20394a23c2541c574361becc0e830d856601fbfff	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:7	122	1
H-A17-PA-033	.claude/skills/prd-authoring-verified/SKILL.md	0e6d7cad41ca0c729879f20e23b8dd008dc2a0623df242fa32713d7915205dc5	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:8	123	1
H-A17-PA-034	.claude/skills/prd-authoring-verified/SKILL.md	e7e7bd3dcdc913023962ec22b0b1e0c0d6f582fe1e0bc528c6fc50ed016cda63	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:9	124	1
H-A17-PA-035	.claude/skills/prd-authoring-verified/SKILL.md	c121ca6605bb3eb1dec0b74f09748139217d972817059c520583ae24b8b071b6	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:10	125	1
H-A17-PA-036	.claude/skills/prd-authoring-verified/SKILL.md	a5397ccce07ecbbc4b875d096acff6637f74f38a8d8be1af01c75f3371e81ddf	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:11	126	1
H-A17-PA-037	.claude/skills/prd-authoring-verified/SKILL.md	25327f96b1d34b2e754c0d72d665cd130bb77444b3efbaa6b1f1a29bfd3ffa4a	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:12	127	1
H-A17-PA-038	.claude/skills/prd-authoring-verified/SKILL.md	79774aa24d8b2b479ef54df31da1bb6f08c1cdd525a89858f61b438c23ab81e2	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:13	128	1
H-A17-PA-039	.claude/skills/prd-authoring-verified/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:14	129	2
H-A17-PA-040	.claude/skills/prd-authoring-verified/SKILL.md	0b27734b46fbf7ef264d7dcff4505a08b8773717141fac872ecc4d1c686ca54c	# PRD Authoring with Built-in Verification > ## Tools	HDG	131	1
H-A17-PA-041	.claude/skills/prd-authoring-verified/SKILL.md	affc2a67f81380dd1f23e749e47a8b45c95dfb2f2e815012a28119d036c6cd55	# PRD Authoring with Built-in Verification > ## What this skill does NOT do	HDG	159	1
H-A17-PA-042	.claude/skills/prd-authoring-verified/SKILL.md	ca79336e7086c6fc25a1ff0b3a745146033570abe9134ea0e68c07bdb0119e5d	# PRD Authoring with Built-in Verification > ## Failure modes to refuse	HDG	169	1
H-A18-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	9b5c7a8ea53163aa7fa627192315e1aa846922c450111ab5f0fc2128a497f9c7	# PRD Authoring with Built-in Verification > ## Tools	LI:9	156	1
H-A2-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	c048ac3c4a18743bf74b2d17c61494a35186ca195090f476afd0b895b2651a19		FM:2	2	1
H-A4-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:1	1	2
H-A4-PA-002	.claude/skills/prd-authoring-verified/SKILL.md	cd2d75f1625cc38b0c106ca6e5f53eed265af52ef6f3addb478ce1775f7c1cdd		FM:2	2	1
H-A4-PA-003	.claude/skills/prd-authoring-verified/SKILL.md	1cacbef42fdc90d456025c6042c6af936e31f7b5270213c96becf7acb23de165		FM:3	3	1
H-A4-PA-004	.claude/skills/prd-authoring-verified/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:4	4	2
H-A7-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:3	85	7
H-A7-PA-002	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:5	91	7
H-A7-PA-003	.claude/skills/prd-authoring-verified/SKILL.md	ab09c3574ac3612c4c7df9bc5e8a9b249d929a9c84c47430663b7ff90ac092e8	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:5	91	1
H-A7-PA-004	.claude/skills/prd-authoring-verified/SKILL.md	9c45c0a6411d868922cd494cba23ba9f4617ef1da45f2a2e3c887e5420be8b6c	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:5	91	1
H-A7-PA-005	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	106	7
H-A7-PA-006	.claude/skills/prd-authoring-verified/SKILL.md	53cdc2de6c3318c5af0384ae74ee89290a9763cce5df85f376c2cae82e277f0f	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	106	1
H-A7-PA-007	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	108	7
H-A7-PA-008	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	109	7
H-A7-PA-009	.claude/skills/prd-authoring-verified/SKILL.md	2e08a2f61c97d2ce57edb668f939bbf35345df37c00bc43047a981d49976b327	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	109	1
H-A7-PA-010	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	109	7
H-A7-PA-011	.claude/skills/prd-authoring-verified/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:9	124	7
H-A7-PA-012	.claude/skills/prd-authoring-verified/SKILL.md	3d9c4ec3dc63a4674a48370eca6b17dcf0eee65079d68635cf71aa4bafea0945	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:9	124	1
H-B3-PA-001	.claude/skills/prd-authoring-verified/SKILL.md	25caba23f113243c9ffd3a8b655d4d69c21aa2f200cde7fc3c5fada758d76e0c	# PRD Authoring with Built-in Verification > ## Scope and boundary	LI:4	18	1
H-B3-PA-002	.claude/skills/prd-authoring-verified/SKILL.md	e8570a6b4d4f80332858d79571880ccba2318e37d35c78fe04702faad089aefd	# PRD Authoring with Built-in Verification > ## Operating modes	LI:2	46	1
H-B3-PA-003	.claude/skills/prd-authoring-verified/SKILL.md	919061e6c7c6dd81bb22c3c0db2a36f5e1ab54b4ebfb3b96978bf5c51d3445f5	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:3	81	1
H-B3-PA-004	.claude/skills/prd-authoring-verified/SKILL.md	6fc8c32d994ec9261fc787a1408c13028c33f9d820d6c646ff910527cbfa6be2	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:3	85	2
H-B3-PA-005	.claude/skills/prd-authoring-verified/SKILL.md	6fc8c32d994ec9261fc787a1408c13028c33f9d820d6c646ff910527cbfa6be2	# PRD Authoring with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	108	2
H-A10-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	9b68c213e154acbb8d23477d85d499f461992e7faffcbb3dbf6f2fbf1b997892	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	56	3
H-A10-PC-002	.claude/skills/prd-closeout-verified/SKILL.md	2af26bb547d12e44140698bf128c3283699804e4c13232346e8512351738f7ca	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	56	3
H-A10-PC-003	.claude/skills/prd-closeout-verified/SKILL.md	1ac4288857b9816947948e54dcb02eae94c40d359db766f4f4e57434a97582d6	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	56	4
H-A10-PC-004	.claude/skills/prd-closeout-verified/SKILL.md	25a4bbc2d9a9c0b23f1e20d92e87155fe2ff8675a40f4666d08eebd838deb727	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	57	4
H-A10-PC-005	.claude/skills/prd-closeout-verified/SKILL.md	5d4285ad69f6aead75320e61bcfa20f3f719dc1b0a790e8d94b021d4d4b38eb4	# PRD Closeout with Built-in Verification > ## Inputs required	LI:7	74	3
H-A10-PC-006	.claude/skills/prd-closeout-verified/SKILL.md	5d4285ad69f6aead75320e61bcfa20f3f719dc1b0a790e8d94b021d4d4b38eb4	# PRD Closeout with Built-in Verification > ## Inputs required	LI:7	75	3
H-A10-PC-007	.claude/skills/prd-closeout-verified/SKILL.md	9b68c213e154acbb8d23477d85d499f461992e7faffcbb3dbf6f2fbf1b997892	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	LI:3	131	3
H-A10-PC-008	.claude/skills/prd-closeout-verified/SKILL.md	2af26bb547d12e44140698bf128c3283699804e4c13232346e8512351738f7ca	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	LI:3	131	3
H-A10-PC-009	.claude/skills/prd-closeout-verified/SKILL.md	1ac4288857b9816947948e54dcb02eae94c40d359db766f4f4e57434a97582d6	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	LI:3	131	4
H-A10-PC-010	.claude/skills/prd-closeout-verified/SKILL.md	25a4bbc2d9a9c0b23f1e20d92e87155fe2ff8675a40f4666d08eebd838deb727	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	LI:3	132	4
H-A10-PC-011	.claude/skills/prd-closeout-verified/SKILL.md	9b68c213e154acbb8d23477d85d499f461992e7faffcbb3dbf6f2fbf1b997892	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	154	3
H-A10-PC-012	.claude/skills/prd-closeout-verified/SKILL.md	2af26bb547d12e44140698bf128c3283699804e4c13232346e8512351738f7ca	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	154	3
H-A10-PC-013	.claude/skills/prd-closeout-verified/SKILL.md	1ac4288857b9816947948e54dcb02eae94c40d359db766f4f4e57434a97582d6	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	154	4
H-A10-PC-014	.claude/skills/prd-closeout-verified/SKILL.md	5d4285ad69f6aead75320e61bcfa20f3f719dc1b0a790e8d94b021d4d4b38eb4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	155	3
H-A10-PC-015	.claude/skills/prd-closeout-verified/SKILL.md	1ac4288857b9816947948e54dcb02eae94c40d359db766f4f4e57434a97582d6	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:9	177	4
H-A10-PC-016	.claude/skills/prd-closeout-verified/SKILL.md	25a4bbc2d9a9c0b23f1e20d92e87155fe2ff8675a40f4666d08eebd838deb727	# PRD Closeout with Built-in Verification > ## What this skill does NOT do	LI:2	205	4
H-A10-PC-017	.claude/skills/prd-closeout-verified/SKILL.md	25a4bbc2d9a9c0b23f1e20d92e87155fe2ff8675a40f4666d08eebd838deb727	# PRD Closeout with Built-in Verification > ## Failure modes to refuse	LI:2	217	4
H-A17-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	ce50f088ae119feb2befc374f3a148cf3ad12067bbf1a5bf36df11d0f079c025	# PRD Closeout with Built-in Verification	HDG	6	1
H-A17-PC-002	.claude/skills/prd-closeout-verified/SKILL.md	c31df17b020896f4408b594dcc87b654acc34d6cffea342410e54300430ff505	# PRD Closeout with Built-in Verification > ## Scope and boundary	HDG	8	1
H-A17-PC-003	.claude/skills/prd-closeout-verified/SKILL.md	0632f7b817601f2c4399f83a1a85ede2ad5c99cacf601e68d5b3471191771451	# PRD Closeout with Built-in Verification > ## When to trigger	HDG	31	1
H-A17-PC-004	.claude/skills/prd-closeout-verified/SKILL.md	90e48a7f751783169d5e801f211330144685188ec27ea465b4e6e633a858f180	# PRD Closeout with Built-in Verification > ## Operating modes	HDG	44	1
H-A17-PC-005	.claude/skills/prd-closeout-verified/SKILL.md	d6d846b406f2b7653084c5785ef74be2a9ad7a246c40752bc2ac844011ff9281	# PRD Closeout with Built-in Verification > ## Inputs required	HDG	62	1
H-A17-PC-006	.claude/skills/prd-closeout-verified/SKILL.md	18a8b5df2208e00d1ba8e7bc8fb538a3625dbfb4e8dc25158debce2a964c237d	# PRD Closeout with Built-in Verification > ## Hard rule: no invented references	HDG	80	1
H-A17-PC-007	.claude/skills/prd-closeout-verified/SKILL.md	153fcd7e47264aed03bb3078a27d4840dbea3d032dd5593a6df85770dcf393ae	# PRD Closeout with Built-in Verification > ## Registry-row invariant	HDG	97	1
H-A17-PC-008	.claude/skills/prd-closeout-verified/SKILL.md	a2d449b06e0d38d92f7ffe6f9919e3cccb1587c59c57ce2ccd1c42f408f2991a	# PRD Closeout with Built-in Verification > ## Two-phase contract	HDG	111	1
H-A17-PC-009	.claude/skills/prd-closeout-verified/SKILL.md	5fafae0a9befdabc8e40acbd0043129c6a04fbc2aad3ea17350a432aae749c14	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	HDG	113	1
H-A17-PC-010	.claude/skills/prd-closeout-verified/SKILL.md	0da21edcb876fd89fc8bb92d7c2e872bbf93feb24097ad037a23ab3fcb97cf93	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	HDG	140	1
H-A17-PC-011	.claude/skills/prd-closeout-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)		142	3
H-A17-PC-012	.claude/skills/prd-closeout-verified/SKILL.md	e089e155302888e26b0348392644b1ca9d0bc643663bd8829188d2005fd5f22d	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:#	145	1
H-A17-PC-013	.claude/skills/prd-closeout-verified/SKILL.md	23cca02b74f386463efa24796c7a9011b0d2c93f0c38b4d15d5d276205b59b43	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:---	146	1
H-A17-PC-014	.claude/skills/prd-closeout-verified/SKILL.md	0505013ef31e7d7ef46f7273546ae32ab51f01c6caf61e0c029077b0a6266398	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V1	147	1
H-A17-PC-015	.claude/skills/prd-closeout-verified/SKILL.md	d6775dcbd35a8d988c9357d45d8857e676d005e12ce9ebe6d232fe38c62dec22	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V2	148	1
H-A17-PC-016	.claude/skills/prd-closeout-verified/SKILL.md	0001768f9f45495f6904c3eba65f6c71fa1a24cfbef213b92ea4c98049aec425	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	149	1
H-A17-PC-017	.claude/skills/prd-closeout-verified/SKILL.md	2cc4cfde350cb0d5739aebf12c854ad5855a428e7db8f8886bb8462e49215472	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	150	1
H-A17-PC-018	.claude/skills/prd-closeout-verified/SKILL.md	19d09a49f4b8c1f8048172098bb6c8db0e0a23a98edc2f512abba776513eba0f	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	151	1
H-A17-PC-019	.claude/skills/prd-closeout-verified/SKILL.md	d10d17150b32b37e373b8442f44aa31d3e4aef3d9f6ce7deedc820b12a3f3c2b	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V6	152	1
H-A17-PC-020	.claude/skills/prd-closeout-verified/SKILL.md	1f6a01b16c0a2c562d7b5d111bd361db8174981c1f2f43462e36ab5bd696d0cb	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	153	1
H-A17-PC-021	.claude/skills/prd-closeout-verified/SKILL.md	9c130f0a5456a9466de5d773896b0c8f2f3cf6536de9b709d1ef88a17603c530	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	154	1
H-A17-PC-022	.claude/skills/prd-closeout-verified/SKILL.md	cdc1273a02be3af53359e5f98387cdc628eca9399e4e5cffe4b701f0704f579f	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	155	1
H-A17-PC-023	.claude/skills/prd-closeout-verified/SKILL.md	2d2e07aa4729de5223058f5c65b33c832d416dd00105feff3f57902308843c9e	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V10	156	1
H-A17-PC-024	.claude/skills/prd-closeout-verified/SKILL.md	8781b2a5acbfe23a1781696caab3a9189d8c74a3c647953f5cb5cd7886332904	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V11	157	1
H-A17-PC-025	.claude/skills/prd-closeout-verified/SKILL.md	0df7b88214ec94aa2ecd386aa7b51811e0b85c87510fd3836471d298c7927b95	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V12	158	1
H-A17-PC-026	.claude/skills/prd-closeout-verified/SKILL.md	458bea3f0da685f2ef0c57edb796ada73a563e370ed8402891fc30b20daae05c	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	HDG	166	1
H-A17-PC-027	.claude/skills/prd-closeout-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	HDG	166	3
H-A17-PC-028	.claude/skills/prd-closeout-verified/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:0	168	2
H-A17-PC-029	.claude/skills/prd-closeout-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:1	169	3
H-A17-PC-030	.claude/skills/prd-closeout-verified/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:1	169	1
H-A17-PC-031	.claude/skills/prd-closeout-verified/SKILL.md	276b874af3c4200a39638b55b0d3c3d9222558f7dc87d848095f93c041a418d6	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:2	170	1
H-A17-PC-032	.claude/skills/prd-closeout-verified/SKILL.md	1764884c2bc08add433b5084b1da6a640392c2af70bb37109bf33884fcb7e587	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:3	171	1
H-A17-PC-033	.claude/skills/prd-closeout-verified/SKILL.md	246bb107e8b78f864ae0448ac9b81096cbf48e0bb077e90ad08b79145a374b05	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:4	172	1
H-A17-PC-034	.claude/skills/prd-closeout-verified/SKILL.md	28fded3950455b2a20f630ab84e87866513f9265760ae11ff2f50f63e67182d4	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:5	173	1
H-A17-PC-035	.claude/skills/prd-closeout-verified/SKILL.md	d0d0997b01f902f977bde37641795cb46f1c45cccea2a524a72498813b12a182	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:6	174	1
H-A17-PC-036	.claude/skills/prd-closeout-verified/SKILL.md	8567059c423ca10434a1fc03605bee40fa57feb247d961b12b330b4d67af902f	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:7	175	1
H-A17-PC-037	.claude/skills/prd-closeout-verified/SKILL.md	7caec08de65afcad5cb2e5f3783af913e975c78e3bed0044161231eeafde653a	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:8	176	1
H-A17-PC-038	.claude/skills/prd-closeout-verified/SKILL.md	ebecc5bb953f489e096be29be1f356bf58fb170daab427b31a4570afdd462cff	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:9	177	1
H-A17-PC-039	.claude/skills/prd-closeout-verified/SKILL.md	01df726bafc3870f636bf6fac84f0f2385937019195e1c969b2ebf0437f84196	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:10	178	1
H-A17-PC-040	.claude/skills/prd-closeout-verified/SKILL.md	be542613cedd801ea0fc98ca34a44f009b3e2a48658d2e8ff5bc044c6ec454f5	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:11	179	1
H-A17-PC-041	.claude/skills/prd-closeout-verified/SKILL.md	d6449a7e884f47cb08909684e9459ed9271b7e8b222084782d2e40e58a59bc7f	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:12	180	1
H-A17-PC-042	.claude/skills/prd-closeout-verified/SKILL.md	2e0e8068ff33e24ceed71a887521d99bd0e61ccb9fd0306199d0ef8f5544560b	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:13	181	1
H-A17-PC-043	.claude/skills/prd-closeout-verified/SKILL.md	37cae2bb02c08ef4abcdaba7a8666619559a3c1fb7258c6572446cd0d9fc478c	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:14	182	1
H-A17-PC-044	.claude/skills/prd-closeout-verified/SKILL.md	25327f96b1d34b2e754c0d72d665cd130bb77444b3efbaa6b1f1a29bfd3ffa4a	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:15	183	1
H-A17-PC-045	.claude/skills/prd-closeout-verified/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Verification Report shape (must appear at end of every response)	F1:16	184	2
H-A17-PC-046	.claude/skills/prd-closeout-verified/SKILL.md	0b27734b46fbf7ef264d7dcff4505a08b8773717141fac872ecc4d1c686ca54c	# PRD Closeout with Built-in Verification > ## Tools	HDG	186	1
H-A17-PC-047	.claude/skills/prd-closeout-verified/SKILL.md	affc2a67f81380dd1f23e749e47a8b45c95dfb2f2e815012a28119d036c6cd55	# PRD Closeout with Built-in Verification > ## What this skill does NOT do	HDG	202	1
H-A17-PC-048	.claude/skills/prd-closeout-verified/SKILL.md	ca79336e7086c6fc25a1ff0b3a745146033570abe9134ea0e68c07bdb0119e5d	# PRD Closeout with Built-in Verification > ## Failure modes to refuse	HDG	213	1
H-A2-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	ecbea080fb90dd2680696622a2b0aa7d3de42cf8b7f236253e134ca4fd44aed1		FM:2	2	1
H-A4-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:1	1	2
H-A4-PC-002	.claude/skills/prd-closeout-verified/SKILL.md	8fe4e531ea7c6157ed5e12ea37a560d4b27fe91e29bbe9b143de32aef498df1a		FM:2	2	1
H-A4-PC-003	.claude/skills/prd-closeout-verified/SKILL.md	e522eb73f9813313c817ef7c32fcfdc006b1635e44f7f1823ac758f7050952a9		FM:3	3	1
H-A4-PC-004	.claude/skills/prd-closeout-verified/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:4	4	2
H-A9-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1		FM:3	3	6
H-A9-PC-002	.claude/skills/prd-closeout-verified/SKILL.md	d7bfe6c1794b0065c412f65d62141245ec33d6d7b8e64990548b199a5bad23d5	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	55	2
H-A9-PC-003	.claude/skills/prd-closeout-verified/SKILL.md	8de6eb13239f2ed8672520035a4cb93da1cd89315c32d687166bcec568cb0ee2	# PRD Closeout with Built-in Verification > ## Operating modes	LI:2	55	2
H-A9-PC-004	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1	# PRD Closeout with Built-in Verification > ## Inputs required	LI:2	67	6
H-A9-PC-005	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1	# PRD Closeout with Built-in Verification > ## Hard rule: no invented references	LI:1	86	6
H-A9-PC-006	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 1 — Apply	LI:1	117	6
H-A9-PC-007	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V1	147	6
H-A9-PC-008	.claude/skills/prd-closeout-verified/SKILL.md	cbc670f960da961d0669e94206fd14a50bb4e0abe60b6a8be875b7ae686827e1	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V2	148	6
H-A9-PC-009	.claude/skills/prd-closeout-verified/SKILL.md	d7bfe6c1794b0065c412f65d62141245ec33d6d7b8e64990548b199a5bad23d5	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	150	2
H-A9-PC-010	.claude/skills/prd-closeout-verified/SKILL.md	8de6eb13239f2ed8672520035a4cb93da1cd89315c32d687166bcec568cb0ee2	# PRD Closeout with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	150	2
H-B3-PC-001	.claude/skills/prd-closeout-verified/SKILL.md	040dda40127e339900b58614c9040c10ad64e9ed3cea9eda5a3dac75c472381e	# PRD Closeout with Built-in Verification > ## Scope and boundary		25	1
H-A1-PR-001	.claude/skills/prd-review-claude/SKILL.md	46ba65a1df3f0ca724f22d2cb920d60c87059a5cf31779499c646a53bdfb9b30	# Claude PRD Review with Built-in Verification > ## When to trigger	LI:6	47	3
H-A1-PR-002	.claude/skills/prd-review-claude/SKILL.md	46ba65a1df3f0ca724f22d2cb920d60c87059a5cf31779499c646a53bdfb9b30	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:2	91	3
H-A1-PR-003	.claude/skills/prd-review-claude/SKILL.md	46ba65a1df3f0ca724f22d2cb920d60c87059a5cf31779499c646a53bdfb9b30	# Claude PRD Review with Built-in Verification > ## Review structure	F1:5	107	3
H-A12-PR-001	.claude/skills/prd-review-claude/SKILL.md	f7a90bca65e2295fb589472ee0481a6db96a0b7188fe5c368dad3f51b08f43e8	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:7	180	1
H-A16-PR-001	.claude/skills/prd-review-claude/SKILL.md	ec06e591a54738495adfe2182fb383f7fb19b76d35adfc90a4948ea6057d6dff	# Claude PRD Review with Built-in Verification	HDG	6	1
H-A16-PR-002	.claude/skills/prd-review-claude/SKILL.md	c31df17b020896f4408b594dcc87b654acc34d6cffea342410e54300430ff505	# Claude PRD Review with Built-in Verification > ## Scope and boundary	HDG	8	1
H-A16-PR-003	.claude/skills/prd-review-claude/SKILL.md	f66a57b1a2a0be5b15a2c5c70f89aae65690371a0ead45bb97ed63ebd7f3ea4b	# Claude PRD Review with Built-in Verification > ## Independence (input envelope)	HDG	28	1
H-A16-PR-004	.claude/skills/prd-review-claude/SKILL.md	0632f7b817601f2c4399f83a1a85ede2ad5c99cacf601e68d5b3471191771451	# Claude PRD Review with Built-in Verification > ## When to trigger	HDG	35	1
H-A16-PR-005	.claude/skills/prd-review-claude/SKILL.md	90e48a7f751783169d5e801f211330144685188ec27ea465b4e6e633a858f180	# Claude PRD Review with Built-in Verification > ## Operating modes	HDG	49	1
H-A16-PR-006	.claude/skills/prd-review-claude/SKILL.md	d6d846b406f2b7653084c5785ef74be2a9ad7a246c40752bc2ac844011ff9281	# Claude PRD Review with Built-in Verification > ## Inputs required	HDG	60	1
H-A16-PR-007	.claude/skills/prd-review-claude/SKILL.md	18a8b5df2208e00d1ba8e7bc8fb538a3625dbfb4e8dc25158debce2a964c237d	# Claude PRD Review with Built-in Verification > ## Hard rule: no invented references	HDG	72	1
H-A16-PR-008	.claude/skills/prd-review-claude/SKILL.md	9666b278eaa42ae85b612d7b00d4e4b0b1662aefec4bdafafa1352ef19c3d8ad	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	HDG	85	1
H-A16-PR-009	.claude/skills/prd-review-claude/SKILL.md	760043d3b8f68ef9f291e3d4c3ab1d3b34a1f15709c64eeabf87fabe11bba4ca	# Claude PRD Review with Built-in Verification > ## Review structure	HDG	98	1
H-A16-PR-010	.claude/skills/prd-review-claude/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Claude PRD Review with Built-in Verification > ## Review structure	F1:0	102	4
H-A16-PR-011	.claude/skills/prd-review-claude/SKILL.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# Claude PRD Review with Built-in Verification > ## Review structure	F1:1	103	1
H-A16-PR-012	.claude/skills/prd-review-claude/SKILL.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# Claude PRD Review with Built-in Verification > ## Review structure	F1:1	103	4
H-A16-PR-013	.claude/skills/prd-review-claude/SKILL.md	7fed46854b57d36b7e9d1e21c7b3c8dfba6b580cd629d427e83ad4cfe43126a4	# Claude PRD Review with Built-in Verification > ## Review structure	F1:2	104	1
H-A16-PR-014	.claude/skills/prd-review-claude/SKILL.md	36c86fa017851c89910d324ab67f4fc1a7b61f623fe00a179bdc332e1bdda2a8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:2	104	1
H-A16-PR-015	.claude/skills/prd-review-claude/SKILL.md	ce04d5c2a7222e0d9e12cc0bc7db23aadfe321175463c27d72fe9ec440f2d6fe	# Claude PRD Review with Built-in Verification > ## Review structure	F1:3	105	1
H-A16-PR-016	.claude/skills/prd-review-claude/SKILL.md	72b4e29e40c010c4dd85eb29e04482be685022b1ea3ba191f54a37e55bab7383	# Claude PRD Review with Built-in Verification > ## Review structure	F1:3	105	1
H-A16-PR-017	.claude/skills/prd-review-claude/SKILL.md	1984dbbb744cc37eb3cbba12ddc08b260ecb70e936cf4778d5a9bb4c3d989d5d	# Claude PRD Review with Built-in Verification > ## Review structure	F1:4	106	1
H-A16-PR-018	.claude/skills/prd-review-claude/SKILL.md	6d80bd100c49a1b843eadc1ea154a42c8b0f0cf6d4e7cb42721cd6afd572ffbb	# Claude PRD Review with Built-in Verification > ## Review structure	F1:4	106	1
H-A16-PR-019	.claude/skills/prd-review-claude/SKILL.md	99c728a8afee3a9bd73e07473d10ac90cd145a1f90234b0107e21be62d7bd903	# Claude PRD Review with Built-in Verification > ## Review structure	F1:4	106	1
H-A16-PR-020	.claude/skills/prd-review-claude/SKILL.md	0f55ec5e10e8b3ac5a16e1d06dd9431e8df079397da4ff2d4866eff79d7b0870	# Claude PRD Review with Built-in Verification > ## Review structure	F1:5	107	1
H-A16-PR-021	.claude/skills/prd-review-claude/SKILL.md	53a699c1082ef45eacf6b3f1dfe275c94ee04e1be1b6e54a1b293f3286ede919	# Claude PRD Review with Built-in Verification > ## Review structure	F1:6	108	1
H-A16-PR-022	.claude/skills/prd-review-claude/SKILL.md	56e4546a4cfc2d0350c9ddf55a340429220f1779ebbd3d1b1f5f1b4e002192cd	# Claude PRD Review with Built-in Verification > ## Review structure	F1:7	109	1
H-A16-PR-023	.claude/skills/prd-review-claude/SKILL.md	f8f747ebd48b0a8e4b9c4f787fc33faae7e4d2611d4430712b8cfb7bb1fd442f	# Claude PRD Review with Built-in Verification > ## Review structure	F1:8	110	1
H-A16-PR-024	.claude/skills/prd-review-claude/SKILL.md	e93703c88549b358b6d163e0984778f802fea3210359df70ed99eddbf9e82c0b	# Claude PRD Review with Built-in Verification > ## Review structure	F1:9	111	1
H-A16-PR-025	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:10	112	9
H-A16-PR-026	.claude/skills/prd-review-claude/SKILL.md	f2ec9958bdcf241947fa4d3d593ccab8f88f4d32e42968e9f29968a76cc0f469	# Claude PRD Review with Built-in Verification > ## Review structure	F1:11	113	1
H-A16-PR-027	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:12	114	9
H-A16-PR-028	.claude/skills/prd-review-claude/SKILL.md	b5a12b170c05f093fd1c3b6cf544dfae7e6cfd1b1a9c8fcb6590332d9dd7608e	# Claude PRD Review with Built-in Verification > ## Review structure	F1:13	115	2
H-A16-PR-029	.claude/skills/prd-review-claude/SKILL.md	b5a12b170c05f093fd1c3b6cf544dfae7e6cfd1b1a9c8fcb6590332d9dd7608e	# Claude PRD Review with Built-in Verification > ## Review structure	F1:13	115	2
H-A16-PR-030	.claude/skills/prd-review-claude/SKILL.md	1ffeda7a5ddd500d8995e256d63d210b759531f3767440d47c40d1f8c9c19014	# Claude PRD Review with Built-in Verification > ## Review structure	F1:14	116	1
H-A16-PR-031	.claude/skills/prd-review-claude/SKILL.md	bf264d523e4506562741536867cca7e68083d6195ffb5eac623e0c977535bebd	# Claude PRD Review with Built-in Verification > ## Review structure	F1:14	116	2
H-A16-PR-032	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:15	117	9
H-A16-PR-033	.claude/skills/prd-review-claude/SKILL.md	6997c676311472227ac618a1d67cd14c978422f0bdd33c1b69ffd68876e2ab88	# Claude PRD Review with Built-in Verification > ## Review structure	F1:16	118	2
H-A16-PR-034	.claude/skills/prd-review-claude/SKILL.md	6997c676311472227ac618a1d67cd14c978422f0bdd33c1b69ffd68876e2ab88	# Claude PRD Review with Built-in Verification > ## Review structure	F1:16	118	2
H-A16-PR-035	.claude/skills/prd-review-claude/SKILL.md	cf7a3ff5f2256d2ea5e80cc7179ef07be02e2759c7f54d986bf9cc1b159c42c5	# Claude PRD Review with Built-in Verification > ## Review structure	F1:17	119	1
H-A16-PR-036	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:18	120	9
H-A16-PR-037	.claude/skills/prd-review-claude/SKILL.md	d09b7be99a6b9b560d5469be428b91cc1e56fdcdb1642646f5332583daca7d68	# Claude PRD Review with Built-in Verification > ## Review structure	F1:19	121	2
H-A16-PR-038	.claude/skills/prd-review-claude/SKILL.md	d09b7be99a6b9b560d5469be428b91cc1e56fdcdb1642646f5332583daca7d68	# Claude PRD Review with Built-in Verification > ## Review structure	F1:19	121	2
H-A16-PR-039	.claude/skills/prd-review-claude/SKILL.md	fb5243df404a965eebe41a769f22c9c3d059c3bb9372ebd9e4af2db9387079cd	# Claude PRD Review with Built-in Verification > ## Review structure	F1:20	122	1
H-A16-PR-040	.claude/skills/prd-review-claude/SKILL.md	75dd8998159fd9c6deaf6494c7c07f9b84bee8820e0eb9c8913e44eda0eaf9eb	# Claude PRD Review with Built-in Verification > ## Review structure	F1:21	123	1
H-A16-PR-041	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:22	124	9
H-A16-PR-042	.claude/skills/prd-review-claude/SKILL.md	2f059f70133dc7d1fcc020a9d9aaf240c1e6d3555a63667a00c96f14eeeb517c	# Claude PRD Review with Built-in Verification > ## Review structure	F1:23	125	2
H-A16-PR-043	.claude/skills/prd-review-claude/SKILL.md	2f059f70133dc7d1fcc020a9d9aaf240c1e6d3555a63667a00c96f14eeeb517c	# Claude PRD Review with Built-in Verification > ## Review structure	F1:23	125	2
H-A16-PR-044	.claude/skills/prd-review-claude/SKILL.md	0491ebf582d1bee52683be36b514e83a15861c2cd4214571d7fa0d8a8b1fcf7b	# Claude PRD Review with Built-in Verification > ## Review structure	F1:24	126	1
H-A16-PR-045	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:25	127	9
H-A16-PR-046	.claude/skills/prd-review-claude/SKILL.md	70aa3bc4e4317e48a590f57ef3357ed13d85ff34ac93e62e5facc6679c8068c7	# Claude PRD Review with Built-in Verification > ## Review structure	F1:26	128	2
H-A16-PR-047	.claude/skills/prd-review-claude/SKILL.md	70aa3bc4e4317e48a590f57ef3357ed13d85ff34ac93e62e5facc6679c8068c7	# Claude PRD Review with Built-in Verification > ## Review structure	F1:26	128	2
H-A16-PR-048	.claude/skills/prd-review-claude/SKILL.md	d2025475a0e797d2debf9e849114eacb6f957380658c63b39342cbcddfe812ce	# Claude PRD Review with Built-in Verification > ## Review structure	F1:27	129	1
H-A16-PR-049	.claude/skills/prd-review-claude/SKILL.md	35db501a705cb77a0b907fe42438882d44a996d609eb279f4e057c69b4c7e4d5	# Claude PRD Review with Built-in Verification > ## Review structure	F1:28	130	1
H-A16-PR-050	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:29	131	9
H-A16-PR-051	.claude/skills/prd-review-claude/SKILL.md	616c644b0d62fe67ed149abb8966678edfa30c1bc2b59ce20ee29dd63d65c7ce	# Claude PRD Review with Built-in Verification > ## Review structure	F1:30	132	2
H-A16-PR-052	.claude/skills/prd-review-claude/SKILL.md	616c644b0d62fe67ed149abb8966678edfa30c1bc2b59ce20ee29dd63d65c7ce	# Claude PRD Review with Built-in Verification > ## Review structure	F1:30	132	2
H-A16-PR-053	.claude/skills/prd-review-claude/SKILL.md	3dae5ac04da0db42fd70a7516e57a594816c3f8e8e8d0ef8e632a6bc944a199d	# Claude PRD Review with Built-in Verification > ## Review structure	F1:31	133	1
H-A16-PR-054	.claude/skills/prd-review-claude/SKILL.md	34c48bd8e307fae990aa1316c0e3cc83d1abd39d8b356b337a27e350e4d1b6d0	# Claude PRD Review with Built-in Verification > ## Review structure	F1:32	134	1
H-A16-PR-055	.claude/skills/prd-review-claude/SKILL.md	b8880601f5e861b3bcbe6a1d1ef0443126e1570ed0d8f1c3d535fa55fc988bf1	# Claude PRD Review with Built-in Verification > ## Review structure	F1:33	135	1
H-A16-PR-056	.claude/skills/prd-review-claude/SKILL.md	cc6d0823798cb71ee3080db22dd8064e63bd1508d265fbaf6e9cf7c2d2af4547	# Claude PRD Review with Built-in Verification > ## Review structure	F1:34	136	1
H-A16-PR-057	.claude/skills/prd-review-claude/SKILL.md	f89eeb36f7ebe9ce24570ded724767d594b417441009b2a9f728f553fee68de8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:35	137	1
H-A16-PR-058	.claude/skills/prd-review-claude/SKILL.md	de74dba29bda1f745ffeb03c8715cc461539a32835c097d93570595667b22bf8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:36	138	1
H-A16-PR-059	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:37	139	9
H-A16-PR-060	.claude/skills/prd-review-claude/SKILL.md	f1eedfb0a1479dd1fc5abf5bd2bcf343734e5eb75b15a1bc50fb0072a9349e8d	# Claude PRD Review with Built-in Verification > ## Review structure	F1:38	140	2
H-A16-PR-061	.claude/skills/prd-review-claude/SKILL.md	f1eedfb0a1479dd1fc5abf5bd2bcf343734e5eb75b15a1bc50fb0072a9349e8d	# Claude PRD Review with Built-in Verification > ## Review structure	F1:38	140	2
H-A16-PR-062	.claude/skills/prd-review-claude/SKILL.md	20a3260cbf38a0992695c8a6e467c9b566b86e38b719ea50b65058639747bd62	# Claude PRD Review with Built-in Verification > ## Review structure	F1:39	141	1
H-A16-PR-063	.claude/skills/prd-review-claude/SKILL.md	5c27541966ef12bb8096ff83b839561e4161edc3c086b7025f291a215db4ca32	# Claude PRD Review with Built-in Verification > ## Review structure	F1:40	142	1
H-A16-PR-064	.claude/skills/prd-review-claude/SKILL.md	73cc46f937442b3ae102e8d0b8adcc06065a35128d7625cadd7f03995bdbbfc8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:41	143	1
H-A16-PR-065	.claude/skills/prd-review-claude/SKILL.md	6c0e0d16592619bcc84c0994221684a9d240e5bcb848e3574e0b599bd0ad95a6	# Claude PRD Review with Built-in Verification > ## Review structure	F1:42	144	1
H-A16-PR-066	.claude/skills/prd-review-claude/SKILL.md	abc74caadaae7b00e664bd2412644a1f8a65594cc26fa4bd5ee760df31eb2341	# Claude PRD Review with Built-in Verification > ## Review structure	F1:43	145	1
H-A16-PR-067	.claude/skills/prd-review-claude/SKILL.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# Claude PRD Review with Built-in Verification > ## Review structure	F1:44	146	9
H-A16-PR-068	.claude/skills/prd-review-claude/SKILL.md	91d5a6aa3e3909829b21227cb0308c9451041d74962029c895d09e112518b4d8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:45	147	2
H-A16-PR-069	.claude/skills/prd-review-claude/SKILL.md	91d5a6aa3e3909829b21227cb0308c9451041d74962029c895d09e112518b4d8	# Claude PRD Review with Built-in Verification > ## Review structure	F1:45	147	2
H-A16-PR-070	.claude/skills/prd-review-claude/SKILL.md	00145fcec1566295879857064d0cc9334a5851caf388b3822f687e56ba0b2774	# Claude PRD Review with Built-in Verification > ## Review structure	F1:46	148	1
H-A16-PR-071	.claude/skills/prd-review-claude/SKILL.md	b5014b97f53bd9531adcf67a079a35d494ac7c0b135ff2b022813152a262bc33	# Claude PRD Review with Built-in Verification > ## Review structure	F1:47	149	1
H-A16-PR-072	.claude/skills/prd-review-claude/SKILL.md	9890c8f4ef393cde9262e107a8cc61ab4ef5aa2c6bd2af37ea7478bcb4c6f743	# Claude PRD Review with Built-in Verification > ## Review structure	F1:48	150	1
H-A16-PR-073	.claude/skills/prd-review-claude/SKILL.md	3ad23695a1d7bf99cb0c82b998f83175e45b9f8468a2d6241d8465df191dbba7	# Claude PRD Review with Built-in Verification > ## Review structure	F1:49	151	1
H-A16-PR-074	.claude/skills/prd-review-claude/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Claude PRD Review with Built-in Verification > ## Review structure	F1:50	152	4
H-A16-PR-075	.claude/skills/prd-review-claude/SKILL.md	a2d449b06e0d38d92f7ffe6f9919e3cccb1587c59c57ce2ccd1c42f408f2991a	# Claude PRD Review with Built-in Verification > ## Two-phase contract	HDG	154	1
H-A16-PR-076	.claude/skills/prd-review-claude/SKILL.md	b2dc9baa601a8d4b7464fcf623c472e29427f0554626f54b9de95bf9b64bda4d	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	HDG	156	1
H-A16-PR-077	.claude/skills/prd-review-claude/SKILL.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:2	159	4
H-A16-PR-078	.claude/skills/prd-review-claude/SKILL.md	0da21edcb876fd89fc8bb92d7c2e872bbf93feb24097ad037a23ab3fcb97cf93	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	HDG	183	1
H-A16-PR-079	.claude/skills/prd-review-claude/SKILL.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V11	197	4
H-A16-PR-080	.claude/skills/prd-review-claude/SKILL.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V12	198	4
H-A16-PR-081	.claude/skills/prd-review-claude/SKILL.md	ec0d4965ad1012046dfbee08f8c1e46ab29f1694b0b824c24c1adf6aed6d6824	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	HDG	201	1
H-A16-PR-082	.claude/skills/prd-review-claude/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:0	203	4
H-A16-PR-083	.claude/skills/prd-review-claude/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:1	204	1
H-A16-PR-084	.claude/skills/prd-review-claude/SKILL.md	adf9288481d28b924834f0949e9b5e22839d0bac573505acae5cb828853dc3a3	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:2	205	1
H-A16-PR-085	.claude/skills/prd-review-claude/SKILL.md	5a86a869bbfa1a68e0a22ade048eca69dd74abf3fd58eafa9a7f5b048b805698	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:3	206	1
H-A16-PR-086	.claude/skills/prd-review-claude/SKILL.md	fda08c51847a7a20e09146fab13b22ab454147e6555c394616bd5fd86c2b780a	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:4	207	1
H-A16-PR-087	.claude/skills/prd-review-claude/SKILL.md	bf264d523e4506562741536867cca7e68083d6195ffb5eac623e0c977535bebd	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:4	207	2
H-A16-PR-088	.claude/skills/prd-review-claude/SKILL.md	f4dec5e720350c31ae34c0207918030bfe93f2cbd200b24cdadf3bd38db568ff	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:5	208	1
H-A16-PR-089	.claude/skills/prd-review-claude/SKILL.md	112738a7c08c52b4ecf78f7d95fd001fb95329b65d4992650457c29228dea7b0	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:6	209	1
H-A16-PR-090	.claude/skills/prd-review-claude/SKILL.md	3b5828f1c28d17a89826e572a362a41cf9fb2ff629260e50c2bce721f3a12430	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:7	210	1
H-A16-PR-091	.claude/skills/prd-review-claude/SKILL.md	c658c2e934a208cbce7fed333885ce63698fd9cfedaf15fc5633b7a08893fae1	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:8	211	1
H-A16-PR-092	.claude/skills/prd-review-claude/SKILL.md	58c16f4b94ec28f898dbf857c3d9f0f6d6728cc1c0ed9c3ed2a8d9d6af0b2010	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:9	212	1
H-A16-PR-093	.claude/skills/prd-review-claude/SKILL.md	e2a195df7256ecb52aaa5bcedbc9e2c0e0cc06cc074208dc799862ccefa62b4d	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:10	213	1
H-A16-PR-094	.claude/skills/prd-review-claude/SKILL.md	70a492de08ee89b91c07ba370762f629e9db5b9726f24c62888b177a292e633f	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:11	214	1
H-A16-PR-095	.claude/skills/prd-review-claude/SKILL.md	633c164ff59f8e13f419ca6022a54ccac6dcd537e7a064445ac32cbde1f8659b	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:12	215	1
H-A16-PR-096	.claude/skills/prd-review-claude/SKILL.md	128700814b7c862a0c345c5213e92c12ad18b5f8721109ae49723621244971d0	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:13	216	1
H-A16-PR-097	.claude/skills/prd-review-claude/SKILL.md	d984c3ce5decc3ff14f6fd4dd00f78b7d9d90c7720089d9b95a3c85912b4aa5b	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:14	217	1
H-A16-PR-098	.claude/skills/prd-review-claude/SKILL.md	25327f96b1d34b2e754c0d72d665cd130bb77444b3efbaa6b1f1a29bfd3ffa4a	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:15	218	1
H-A16-PR-099	.claude/skills/prd-review-claude/SKILL.md	79774aa24d8b2b479ef54df31da1bb6f08c1cdd525a89858f61b438c23ab81e2	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:16	219	1
H-A16-PR-100	.claude/skills/prd-review-claude/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:17	220	4
H-A16-PR-101	.claude/skills/prd-review-claude/SKILL.md	0b27734b46fbf7ef264d7dcff4505a08b8773717141fac872ecc4d1c686ca54c	# Claude PRD Review with Built-in Verification > ## Tools	HDG	222	1
H-A16-PR-102	.claude/skills/prd-review-claude/SKILL.md	affc2a67f81380dd1f23e749e47a8b45c95dfb2f2e815012a28119d036c6cd55	# Claude PRD Review with Built-in Verification > ## What this skill does NOT do	HDG	236	1
H-A16-PR-103	.claude/skills/prd-review-claude/SKILL.md	ca79336e7086c6fc25a1ff0b3a745146033570abe9134ea0e68c07bdb0119e5d	# Claude PRD Review with Built-in Verification > ## Failure modes to refuse	HDG	253	1
H-A17-PR-001	.claude/skills/prd-review-claude/SKILL.md	e089e155302888e26b0348392644b1ca9d0bc643663bd8829188d2005fd5f22d	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:#	185	1
H-A17-PR-002	.claude/skills/prd-review-claude/SKILL.md	23cca02b74f386463efa24796c7a9011b0d2c93f0c38b4d15d5d276205b59b43	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:---	186	1
H-A17-PR-003	.claude/skills/prd-review-claude/SKILL.md	5c575e6a52fa6fbaaddba63e707175fe732c46332c43afb9985039be92a10020	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V1	187	1
H-A17-PR-004	.claude/skills/prd-review-claude/SKILL.md	aa0379907976e3e3ff7cb323736d9e31db7f12d4be546adbd248db7b4b56b7a4	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V2	188	1
H-A17-PR-005	.claude/skills/prd-review-claude/SKILL.md	177ff681e9d39670f4e2ca34ef6e4e39c647a2d63ba72b083fbbea2bcae0ee1f	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	189	1
H-A17-PR-006	.claude/skills/prd-review-claude/SKILL.md	8e7e82139ca65d8a1a13fcad51f16451a0acfda029dfbd67ac7ef543da89ca0a	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	190	1
H-A17-PR-007	.claude/skills/prd-review-claude/SKILL.md	80afaa8140cf077dca5e6dd2e134a65324259136afd82a8ee1a7d2c08eb39bd6	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	191	1
H-A17-PR-008	.claude/skills/prd-review-claude/SKILL.md	93443ecbb7087094f96d1a7c19c331449cee547efaacec428d3429529e4057f7	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V6	192	1
H-A17-PR-009	.claude/skills/prd-review-claude/SKILL.md	49b656d00aaca4ba99f49be31d11fe9bafaa1a975e463919ae91bb8dbc20aacc	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	193	1
H-A17-PR-010	.claude/skills/prd-review-claude/SKILL.md	f2831b2cfa941935cae5e208e85c80277af4c4e25be5f69aa521527fbdce3416	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	194	1
H-A17-PR-011	.claude/skills/prd-review-claude/SKILL.md	bc7c69efbde77eccb081abd5b0855f21a62d43bfd1cbed0be4bd265bf4002be1	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	195	1
H-A17-PR-012	.claude/skills/prd-review-claude/SKILL.md	642806c3de654990f08e15805285a5d539ee07367cf3db5f384d80d037d725e7	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V10	196	1
H-A17-PR-013	.claude/skills/prd-review-claude/SKILL.md	559368082ee095af2a825c0d8c1758ad64252d9751bfe9d7de9d9ea87a68e3aa	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V11	197	1
H-A17-PR-014	.claude/skills/prd-review-claude/SKILL.md	78374bc32a63d0ef9ae25f4b56993bc785dc4419696fd00b4471ac1126ede4a0	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V12	198	1
H-A17-PR-015	.claude/skills/prd-review-claude/SKILL.md	ebba0855fc1c15fb9e94dab36f7faf70cbeda79433c0d09f7fe9bc3a4933e8ac	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V13	199	1
H-A17-PR-016	.claude/skills/prd-review-claude/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	HDG	201	2
H-A17-PR-017	.claude/skills/prd-review-claude/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Verification Report shape	F2:1	204	2
H-A2-PR-001	.claude/skills/prd-review-claude/SKILL.md	3f48209fc3b8c4afd0c163a813f88fd3933298a954b6590b71c1e033459214ca		FM:2	2	1
H-A2-PR-002	.claude/skills/prd-review-claude/SKILL.md	c048ac3c4a18743bf74b2d17c61494a35186ca195090f476afd0b895b2651a19	# Claude PRD Review with Built-in Verification > ## Scope and boundary	LI:3	20	2
H-A2-PR-003	.claude/skills/prd-review-claude/SKILL.md	c048ac3c4a18743bf74b2d17c61494a35186ca195090f476afd0b895b2651a19	# Claude PRD Review with Built-in Verification > ## Hard rule: no invented references		83	2
H-A4-PR-001	.claude/skills/prd-review-claude/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:1	1	2
H-A4-PR-002	.claude/skills/prd-review-claude/SKILL.md	05b2c1ed6181f073f91f9afb64a5848c52ef21a3464dafa05e0127b60ca9e271		FM:2	2	1
H-A4-PR-003	.claude/skills/prd-review-claude/SKILL.md	423e8a65d37daaf593cc8d1327620d80dcacc065505f28036e60f74e2060bb55		FM:3	3	1
H-A4-PR-004	.claude/skills/prd-review-claude/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:4	4	2
H-A5-PR-001	.claude/skills/prd-review-claude/SKILL.md	b3377ae9582134d6ffae99dc1710caed1b9c09a1b5eb977d1a58e9641d91be77		FM:3	3	4
H-A5-PR-002	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514		FM:3	3	6
H-A5-PR-003	.claude/skills/prd-review-claude/SKILL.md	a8ce16a33fe58bfdfdbb35184c54e4508ca4bb43a1f327d8c604ea29c7aa34ec	# Claude PRD Review with Built-in Verification > ## When to trigger	LI:6	46	4
H-A5-PR-004	.claude/skills/prd-review-claude/SKILL.md	851833bccec8dac2405286643c443217562a118de745165c42795adf60206374	# Claude PRD Review with Built-in Verification > ## When to trigger	LI:6	47	2
H-A5-PR-005	.claude/skills/prd-review-claude/SKILL.md	b3377ae9582134d6ffae99dc1710caed1b9c09a1b5eb977d1a58e9641d91be77	# Claude PRD Review with Built-in Verification > ## Operating modes	LI:2	54	4
H-A5-PR-006	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# Claude PRD Review with Built-in Verification > ## Operating modes	LI:2	54	6
H-A5-PR-007	.claude/skills/prd-review-claude/SKILL.md	20108fbf02a3552fa81f746251cb11266473769362df8a8097d503b914c4d4a1	# Claude PRD Review with Built-in Verification > ## Operating modes	LI:2	55	1
H-A5-PR-008	.claude/skills/prd-review-claude/SKILL.md	b3377ae9582134d6ffae99dc1710caed1b9c09a1b5eb977d1a58e9641d91be77	# Claude PRD Review with Built-in Verification > ## Inputs required	LI:3	67	4
H-A5-PR-009	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# Claude PRD Review with Built-in Verification > ## Inputs required	LI:3	67	6
H-A5-PR-010	.claude/skills/prd-review-claude/SKILL.md	a8ce16a33fe58bfdfdbb35184c54e4508ca4bb43a1f327d8c604ea29c7aa34ec	# Claude PRD Review with Built-in Verification > ## Hard rule: no invented references	LI:3	78	4
H-A5-PR-011	.claude/skills/prd-review-claude/SKILL.md	b3377ae9582134d6ffae99dc1710caed1b9c09a1b5eb977d1a58e9641d91be77	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:1	89	4
H-A5-PR-012	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:1	89	6
H-A5-PR-013	.claude/skills/prd-review-claude/SKILL.md	383b98bbab9f34d2541c89a47932737d58713f0465eec933bd8bb66b41de5aae	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:2	91	1
H-A5-PR-014	.claude/skills/prd-review-claude/SKILL.md	a8ce16a33fe58bfdfdbb35184c54e4508ca4bb43a1f327d8c604ea29c7aa34ec	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:2	91	4
H-A5-PR-015	.claude/skills/prd-review-claude/SKILL.md	851833bccec8dac2405286643c443217562a118de745165c42795adf60206374	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths	LI:2	92	2
H-A5-PR-016	.claude/skills/prd-review-claude/SKILL.md	1077bb30aea03fd3852fedb7385a0f92c567ce3ebb241c1767778bc171550108	# Claude PRD Review with Built-in Verification > ## Stage-locked file paths		96	2
H-A5-PR-017	.claude/skills/prd-review-claude/SKILL.md	a8ce16a33fe58bfdfdbb35184c54e4508ca4bb43a1f327d8c604ea29c7aa34ec	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:3	163	4
H-A5-PR-018	.claude/skills/prd-review-claude/SKILL.md	1077bb30aea03fd3852fedb7385a0f92c567ce3ebb241c1767778bc171550108	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V6	192	2
H-A5-PR-019	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	195	6
H-A5-PR-020	.claude/skills/prd-review-claude/SKILL.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	195	6
H-B3-PR-001	.claude/skills/prd-review-claude/SKILL.md	25caba23f113243c9ffd3a8b655d4d69c21aa2f200cde7fc3c5fada758d76e0c	# Claude PRD Review with Built-in Verification > ## Scope and boundary	LI:5	23	1
H-B3-PR-002	.claude/skills/prd-review-claude/SKILL.md	e8570a6b4d4f80332858d79571880ccba2318e37d35c78fe04702faad089aefd	# Claude PRD Review with Built-in Verification > ## What this skill does NOT do	LI:6	249	1
H-B7-PR-001	.claude/skills/prd-review-claude/SKILL.md	067db46ccfae6e6003b029e847a9393ada8d727e0c764bb47e4fffb7ae271f32	# Claude PRD Review with Built-in Verification > ## Review structure	F1:35	137	2
H-B7-PR-002	.claude/skills/prd-review-claude/SKILL.md	859cd70e5e497c79653d0e32e00adb43df1a68adf82d1dc284d16516abe10205	# Claude PRD Review with Built-in Verification > ## Review structure	F1:35	137	1
H-B7-PR-003	.claude/skills/prd-review-claude/SKILL.md	067db46ccfae6e6003b029e847a9393ada8d727e0c764bb47e4fffb7ae271f32	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:4	169	2
H-B7-PR-004	.claude/skills/prd-review-claude/SKILL.md	58abaf96ebf7e4c85df72f06d5e974ad8440c9dadaa59b6bf5ce8ff020b9bd7f	# Claude PRD Review with Built-in Verification > ## Two-phase contract > ### Phase 1 — Generate	LI:4	169	1
H-A10-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	2af26bb547d12e44140698bf128c3283699804e4c13232346e8512351738f7ca	# Scope-Lock Pre-Commit > ## Inputs required	LI:1	53	1
H-A11-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:1	135	8
H-A11-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	8161c9a80a3d0064495637883cda8877cbef7d7e57dc419b3631cf7e0509c03f	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:2	136	1
H-A11-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	f4f1f60a1a29b4b24265e0be159d690d6e342b65c3833d7b2f06b0dbfad60137	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:2	136	4
H-A11-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	f4f1f60a1a29b4b24265e0be159d690d6e342b65c3833d7b2f06b0dbfad60137	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:2	136	4
H-A11-SL-005	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:4	143	8
H-A11-SL-006	.claude/skills/scope-lock-precommit/SKILL.md	f4f1f60a1a29b4b24265e0be159d690d6e342b65c3833d7b2f06b0dbfad60137	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	LI:5	146	4
H-A11-SL-007	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		153	8
H-A11-SL-008	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 1 — Detect	LI:4	174	8
H-A11-SL-009	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	193	8
H-A11-SL-010	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:8	207	8
H-A11-SL-011	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## What this skill does NOT do	LI:3	234	8
H-A11-SL-012	.claude/skills/scope-lock-precommit/SKILL.md	69e5adefb513e2b7250cb64407a01ef5bc15da3d960fb04b2587bf378c9ffe3a	# Scope-Lock Pre-Commit > ## Failure modes to refuse	LI:4	245	8
H-A11-SL-013	.claude/skills/scope-lock-precommit/SKILL.md	f4f1f60a1a29b4b24265e0be159d690d6e342b65c3833d7b2f06b0dbfad60137	# Scope-Lock Pre-Commit > ## Failure modes to refuse	LI:4	245	4
H-A17-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	d81084e9c9851e20ecfe79c1ca662ee37c4d1f7a0ff5df11c5d1df95fb81efb2	# Scope-Lock Pre-Commit	HDG	6	1
H-A17-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	c31df17b020896f4408b594dcc87b654acc34d6cffea342410e54300430ff505	# Scope-Lock Pre-Commit > ## Scope and boundary	HDG	8	1
H-A17-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	0632f7b817601f2c4399f83a1a85ede2ad5c99cacf601e68d5b3471191771451	# Scope-Lock Pre-Commit > ## When to trigger	HDG	24	1
H-A17-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	90e48a7f751783169d5e801f211330144685188ec27ea465b4e6e633a858f180	# Scope-Lock Pre-Commit > ## Operating modes	HDG	37	1
H-A17-SL-005	.claude/skills/scope-lock-precommit/SKILL.md	d6d846b406f2b7653084c5785ef74be2a9ad7a246c40752bc2ac844011ff9281	# Scope-Lock Pre-Commit > ## Inputs required	HDG	50	1
H-A17-SL-006	.claude/skills/scope-lock-precommit/SKILL.md	18a8b5df2208e00d1ba8e7bc8fb538a3625dbfb4e8dc25158debce2a964c237d	# Scope-Lock Pre-Commit > ## Hard rule: no invented references	HDG	60	1
H-A17-SL-007	.claude/skills/scope-lock-precommit/SKILL.md	daed579e65f463e99a19362034490bddea10ae7a920bf10dd76c5d26c5fa456c	# Scope-Lock Pre-Commit > ## FILES parsing rule	HDG	73	1
H-A17-SL-008	.claude/skills/scope-lock-precommit/SKILL.md	1708d56e5bdcc5c838c437da676ed17cdd701caa75b765f6fcd1d04309cd660c	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)	HDG	95	1
H-A17-SL-009	.claude/skills/scope-lock-precommit/SKILL.md	94f5224b21d7c6966622036fa19e0ed5769259df6cd2187c06c212423ef921fb	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)	HDG	130	1
H-A17-SL-010	.claude/skills/scope-lock-precommit/SKILL.md	a2d449b06e0d38d92f7ffe6f9919e3cccb1587c59c57ce2ccd1c42f408f2991a	# Scope-Lock Pre-Commit > ## Two-phase contract	HDG	167	1
H-A17-SL-011	.claude/skills/scope-lock-precommit/SKILL.md	3eea3e224342278946b671706d450553283ef08b70b85ba3f26d289dddf096b7	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 1 — Detect	HDG	169	1
H-A17-SL-012	.claude/skills/scope-lock-precommit/SKILL.md	0da21edcb876fd89fc8bb92d7c2e872bbf93feb24097ad037a23ab3fcb97cf93	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	HDG	183	1
H-A17-SL-013	.claude/skills/scope-lock-precommit/SKILL.md	e089e155302888e26b0348392644b1ca9d0bc643663bd8829188d2005fd5f22d	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:#	185	1
H-A17-SL-014	.claude/skills/scope-lock-precommit/SKILL.md	23cca02b74f386463efa24796c7a9011b0d2c93f0c38b4d15d5d276205b59b43	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:---	186	1
H-A17-SL-015	.claude/skills/scope-lock-precommit/SKILL.md	9d44061a9fffd8a44e829e6c795494eba2f29bb08280cccf17c9b646d5656153	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V1	187	1
H-A17-SL-016	.claude/skills/scope-lock-precommit/SKILL.md	35471e76fb375db6a134b23eb0750864b4f01ecedb0c4733d8caa6f2a23a29d6	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V2	188	1
H-A17-SL-017	.claude/skills/scope-lock-precommit/SKILL.md	39e88f6b61ed85817bf3c5fc407fa14091d7529756e04456486a76e71b37965a	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	189	1
H-A17-SL-018	.claude/skills/scope-lock-precommit/SKILL.md	048a87a71f91ec57ad172489a47dfd6d1cb424b9d538ba874f7a56fb6fc10c01	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V4	190	1
H-A17-SL-019	.claude/skills/scope-lock-precommit/SKILL.md	09960e426ddde585bbfc9bb22748f42e27ecec43035023907a009ea5afbfce70	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	191	1
H-A17-SL-020	.claude/skills/scope-lock-precommit/SKILL.md	2c76cc6af71f3d087801491399a2bbfddb73a50ea744e2efe5794cb4a9f59dc8	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V6	192	1
H-A17-SL-021	.claude/skills/scope-lock-precommit/SKILL.md	e01150607dd7b7362f6b0739f9b5b9341b372a62d548d918c30ce6aa34156425	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	193	1
H-A17-SL-022	.claude/skills/scope-lock-precommit/SKILL.md	03a45befe5f291d13eec7c7a49255c2df164bad366da2114e89e3505c2d2a87a	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V8	194	1
H-A17-SL-023	.claude/skills/scope-lock-precommit/SKILL.md	9123fac54442e7f70bf55284722ad79a59db72bf77fb479c2addc0e6c91b6b16	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V9	195	1
H-A17-SL-024	.claude/skills/scope-lock-precommit/SKILL.md	ec0d4965ad1012046dfbee08f8c1e46ab29f1694b0b824c24c1adf6aed6d6824	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	HDG	197	1
H-A17-SL-025	.claude/skills/scope-lock-precommit/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	HDG	197	2
H-A17-SL-026	.claude/skills/scope-lock-precommit/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:0	199	2
H-A17-SL-027	.claude/skills/scope-lock-precommit/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:1	200	2
H-A17-SL-028	.claude/skills/scope-lock-precommit/SKILL.md	df2f540f325563ebf8e98d9df4c739a3a141668de3177da88ef5d3b9cc4bfde4	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:1	200	1
H-A17-SL-029	.claude/skills/scope-lock-precommit/SKILL.md	0faf1c4ba861f507fb43bc4e6a7f86dcba9fe37e26d1652919345a06681fc549	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:2	201	1
H-A17-SL-030	.claude/skills/scope-lock-precommit/SKILL.md	b857e923b458a66dcd9eb5a56e2872a5f12c20fb773a4ed2f74e422f42af78c8	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:3	202	1
H-A17-SL-031	.claude/skills/scope-lock-precommit/SKILL.md	726e3b873ec122af6b1026458d002898874701d4f898ceaab47a612b9dd7a8a5	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:4	203	1
H-A17-SL-032	.claude/skills/scope-lock-precommit/SKILL.md	8eaac250774801b2a228d5d3635afd0761450015c3b973a2c311a26956354cbf	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:5	204	1
H-A17-SL-033	.claude/skills/scope-lock-precommit/SKILL.md	241faf47960a1f359d6194ac5d68f48dee2bc38920d85865406c43bee5aaf671	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:6	205	1
H-A17-SL-034	.claude/skills/scope-lock-precommit/SKILL.md	e9b1b2c232e84ef05ead127c8d1b12d32a822b69b956fde8405f0717b93a1022	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:7	206	1
H-A17-SL-035	.claude/skills/scope-lock-precommit/SKILL.md	545f479b2a104f41aa71ed3a62035e01120815a7cc95f80b053a2363bad56420	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:8	207	1
H-A17-SL-036	.claude/skills/scope-lock-precommit/SKILL.md	f3da69a487f3cd25390472e1f39709f5204ec23d869e7baf1247bb5763aae545	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:9	208	1
H-A17-SL-037	.claude/skills/scope-lock-precommit/SKILL.md	2feb72b347d4b8b9174d40127c1763617d34943bd59636458d8d17ef524f4e35	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:10	209	1
H-A17-SL-038	.claude/skills/scope-lock-precommit/SKILL.md	82e605f23431cbcdec8cb4bb8ecf82c244d5949788ab1ee9ca2dc9c63bd96936	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:11	210	1
H-A17-SL-039	.claude/skills/scope-lock-precommit/SKILL.md	6f35d5b597cf4e3cf3a10f39238199ee311d07994ba07dc7b774dc05d639064d	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:12	211	1
H-A17-SL-040	.claude/skills/scope-lock-precommit/SKILL.md	a86dac84b5398a828b85df0bfa4b1cf04a8ca6d054e20e6fd266b5be004b3eb8	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:13	212	1
H-A17-SL-041	.claude/skills/scope-lock-precommit/SKILL.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:14	213	2
H-A17-SL-042	.claude/skills/scope-lock-precommit/SKILL.md	0b27734b46fbf7ef264d7dcff4505a08b8773717141fac872ecc4d1c686ca54c	# Scope-Lock Pre-Commit > ## Tools	HDG	215	1
H-A17-SL-043	.claude/skills/scope-lock-precommit/SKILL.md	affc2a67f81380dd1f23e749e47a8b45c95dfb2f2e815012a28119d036c6cd55	# Scope-Lock Pre-Commit > ## What this skill does NOT do	HDG	227	1
H-A17-SL-044	.claude/skills/scope-lock-precommit/SKILL.md	ca79336e7086c6fc25a1ff0b3a745146033570abe9134ea0e68c07bdb0119e5d	# Scope-Lock Pre-Commit > ## Failure modes to refuse	HDG	240	1
H-A2-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	f2242a71e777c85dcc9fba6d371d732f3f32551a90854c806728dfb699e9f6bc		FM:2	2	1
H-A2-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	ecbea080fb90dd2680696622a2b0aa7d3de42cf8b7f236253e134ca4fd44aed1	# Scope-Lock Pre-Commit > ## When to trigger	LI:6	33	1
H-A4-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:1	1	2
H-A4-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	182a564dd9617d15098e67e21603946f3bbab6ce67468c3b99ff04ae619f29a0		FM:2	2	1
H-A4-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	b71a2f0efca203eb5e443dae9313869291e722d23721c969e5a1534af2342a93		FM:3	3	1
H-A4-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b		FM:4	4	2
H-A6-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	d2a6bb6e34d587c3fd575afc1e25929310cec1497282fd247e42d9f3511288e5	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:3	90	2
H-A6-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	83a28728464fde3e0166373cd8ff4c390f1f345184106db6ff262d6e7afaef65	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:3	90	1
H-A6-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	ee4f8c9f94deb34635c3b2dd737bc2bf3e23a31278dc279dbfbccc866c03a948	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		111	1
H-A6-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	a806a984810f37ec7f36f9a61aff2cedc4e542ef1b766f90279a87f7a57e8329	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		111	3
H-A6-SL-005	.claude/skills/scope-lock-precommit/SKILL.md	d2a6bb6e34d587c3fd575afc1e25929310cec1497282fd247e42d9f3511288e5	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		112	2
H-A6-SL-006	.claude/skills/scope-lock-precommit/SKILL.md	a806a984810f37ec7f36f9a61aff2cedc4e542ef1b766f90279a87f7a57e8329	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 1 — Detect	LI:6	178	3
H-A6-SL-007	.claude/skills/scope-lock-precommit/SKILL.md	a806a984810f37ec7f36f9a61aff2cedc4e542ef1b766f90279a87f7a57e8329	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V5	191	3
H-A7-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Scope and boundary	LI:2	14	10
H-A7-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	34d88201e28c8dffd715ff4dde242d49a07119689d0df2d9499fb69d242e3ce0	# Scope-Lock Pre-Commit > ## Scope and boundary	LI:2	14	2
H-A7-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	c9766ca413f9e0a07788482d1b3c294c39a054add780c4bb639f98815a2da0ec	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		107	4
H-A7-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	c9766ca413f9e0a07788482d1b3c294c39a054add780c4bb639f98815a2da0ec	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		108	4
H-A7-SL-005	.claude/skills/scope-lock-precommit/SKILL.md	c9766ca413f9e0a07788482d1b3c294c39a054add780c4bb639f98815a2da0ec	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		114	4
H-A7-SL-006	.claude/skills/scope-lock-precommit/SKILL.md	c9766ca413f9e0a07788482d1b3c294c39a054add780c4bb639f98815a2da0ec	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		121	4
H-A7-SL-007	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		156	10
H-A7-SL-008	.claude/skills/scope-lock-precommit/SKILL.md	53cdc2de6c3318c5af0384ae74ee89290a9763cce5df85f376c2cae82e277f0f	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		156	2
H-A7-SL-009	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		159	10
H-A7-SL-010	.claude/skills/scope-lock-precommit/SKILL.md	ab09c3574ac3612c4c7df9bc5e8a9b249d929a9c84c47430663b7ff90ac092e8	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		159	1
H-A7-SL-011	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 1 — Detect	LI:3	173	10
H-A7-SL-012	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	189	10
H-A7-SL-013	.claude/skills/scope-lock-precommit/SKILL.md	2e08a2f61c97d2ce57edb668f939bbf35345df37c00bc43047a981d49976b327	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V3	189	2
H-A7-SL-014	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	193	10
H-A7-SL-015	.claude/skills/scope-lock-precommit/SKILL.md	53cdc2de6c3318c5af0384ae74ee89290a9763cce5df85f376c2cae82e277f0f	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Phase 2 — Verify (MANDATORY before returning)	ROW:V7	193	2
H-A7-SL-016	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:4	203	10
H-A7-SL-017	.claude/skills/scope-lock-precommit/SKILL.md	3d9c4ec3dc63a4674a48370eca6b17dcf0eee65079d68635cf71aa4bafea0945	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:4	203	1
H-A7-SL-018	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:9	208	10
H-A7-SL-019	.claude/skills/scope-lock-precommit/SKILL.md	34d88201e28c8dffd715ff4dde242d49a07119689d0df2d9499fb69d242e3ce0	# Scope-Lock Pre-Commit > ## Two-phase contract > ### Verification Report shape	F1:9	208	2
H-A7-SL-020	.claude/skills/scope-lock-precommit/SKILL.md	0ed3a02e2c7d0260668207f20092953b14cb1127e27441373323a618706d1658	# Scope-Lock Pre-Commit > ## What this skill does NOT do	LI:6	238	1
H-A7-SL-021	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## What this skill does NOT do	LI:6	238	10
H-A7-SL-022	.claude/skills/scope-lock-precommit/SKILL.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# Scope-Lock Pre-Commit > ## Failure modes to refuse	LI:3	244	10
H-A7-SL-023	.claude/skills/scope-lock-precommit/SKILL.md	2e08a2f61c97d2ce57edb668f939bbf35345df37c00bc43047a981d49976b327	# Scope-Lock Pre-Commit > ## Failure modes to refuse	LI:3	244	2
H-A8-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	c30b534a6c044c34b2731c31e32200bdbe2491861a909ab01841d2f7b4a7e5f7	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:1	81	1
H-A8-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	4579e65a7499f2d166fd474db5a78e56aba3eb3815190ba5b0104763b7cd8c59	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:2	85	1
H-A8-SL-003	.claude/skills/scope-lock-precommit/SKILL.md	c1f4e8d5e6068247621a6de76e2c1527ae7683559b0ec19707d4749c1e37b81a	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:2	85	2
H-A8-SL-004	.claude/skills/scope-lock-precommit/SKILL.md	ba550776ddb0f13bfc9b6cd372a35f79a31dda6e14cdf6ae62eef2c7f36ab1b2	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:2	85	2
H-A8-SL-005	.claude/skills/scope-lock-precommit/SKILL.md	ba550776ddb0f13bfc9b6cd372a35f79a31dda6e14cdf6ae62eef2c7f36ab1b2	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:2	86	2
H-A8-SL-006	.claude/skills/scope-lock-precommit/SKILL.md	c1f4e8d5e6068247621a6de76e2c1527ae7683559b0ec19707d4749c1e37b81a	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:2	87	2
H-A8-SL-007	.claude/skills/scope-lock-precommit/SKILL.md	5dcc10778c78fe1bf47e0e8753804f568e6e45b160afdee55e11cf117782ead5	# Scope-Lock Pre-Commit > ## FILES parsing rule	LI:3	89	1
H-B3-SL-001	.claude/skills/scope-lock-precommit/SKILL.md	ef3033de9e9b7096ae4837801cba57c4341b721c4e46598716170f64a960fd7c	# Scope-Lock Pre-Commit > ## Bookkeeping allowlist (always permitted)		122	1
H-B3-SL-002	.claude/skills/scope-lock-precommit/SKILL.md	919061e6c7c6dd81bb22c3c0db2a36f5e1ab54b4ebfb3b96978bf5c51d3445f5	# Scope-Lock Pre-Commit > ## Protected pipeline set (dynamic, fail-closed)		158	1
H-A16-RT-001	docs/PRD_REVIEW_TEMPLATE.md	3673fc649802a6c38cbe756df29eb3263f481f494ed94bdc1202713f473a8c75	# PRD Review Template	HDG	1	1
H-A16-RT-002	docs/PRD_REVIEW_TEMPLATE.md	d7537f84dc2a577d3e85664613fd6241c3b450979c263b8413bf1b27d38f716d	# PRD Review Template > ## Required sections (in order)	HDG	23	1
H-A16-RT-003	docs/PRD_REVIEW_TEMPLATE.md	36524c47b7c0d00f2814e313bd4d439ebc2c5b505e0ccfbb5c1adf820624712b	# PRD Review Template > ## Required sections (in order) > ### 1. Strengths	HDG	25	1
H-A16-RT-004	docs/PRD_REVIEW_TEMPLATE.md	4597748d300dc2646515bfa4bd6419c754cafa8e8d7de43001fdeb0cbace4f4a	# PRD Review Template > ## Required sections (in order) > ### 2. Cohesiveness	HDG	37	1
H-A16-RT-005	docs/PRD_REVIEW_TEMPLATE.md	d3c20477920a5f402f4958057fa3a2ce1c4094ac8d003ae5202ca0a6474fff3b	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	HDG	48	1
H-A16-RT-006	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:0	52	10
H-A16-RT-007	docs/PRD_REVIEW_TEMPLATE.md	a58f105d8871794efd215614e752675e4d95072a963699480e20accdd9bfe278	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:1	53	1
H-A16-RT-008	docs/PRD_REVIEW_TEMPLATE.md	d224178d0744e1bfa3bd5a95fd816c64348a4e43ea752c878433a5a31770ec97	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:2	54	1
H-A16-RT-009	docs/PRD_REVIEW_TEMPLATE.md	74240630ae75836f14eae0149a20722b12219ad1492ce510be47426c712a6831	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:3	55	1
H-A16-RT-010	docs/PRD_REVIEW_TEMPLATE.md	2a3b91bc2f99cf5a850a1fb3391382867ce9827b4aa7555abf896a5e6220ce9f	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:4	56	1
H-A16-RT-011	docs/PRD_REVIEW_TEMPLATE.md	0aef7a862f47aef7f27b49ed290e8656744bebf98b12735e222f0ae806f4aedd	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:5	57	1
H-A16-RT-012	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Required sections (in order) > ### 3. Critical Problems	F1:6	58	10
H-A16-RT-013	docs/PRD_REVIEW_TEMPLATE.md	c5b7b6a4318b677d9a6cb2515c64518719db31e9f63a2c2c74ce45b56fe9ae69	# PRD Review Template > ## Required sections (in order) > ### 4. Revised PRD	HDG	67	1
H-A16-RT-014	docs/PRD_REVIEW_TEMPLATE.md	35cd446265fa521fb65d8dffd69ced9ff051b5207f2c6f2ae6ecaf3e8df6b735	# PRD Review Template > ## Pre-publish checklist (reviewer must answer "yes" to each)	HDG	79	1
H-A16-RT-015	docs/PRD_REVIEW_TEMPLATE.md	a27adc9c998492c3954561dfb8c365db7b972952d0c0f846b4b85b8526759fd7	# PRD Review Template > ## Token discipline	HDG	104	1
H-A16-RT-016	docs/PRD_REVIEW_TEMPLATE.md	cf89d213c1aa08ce57bf3f75a5ce137339b66429b9d2030b6e6c91afc138db9c	# PRD Review Template > ## When to skip the Revised PRD section	HDG	117	1
H-A16-RT-017	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## When to skip the Revised PRD section	F2:0	122	10
H-A16-RT-018	docs/PRD_REVIEW_TEMPLATE.md	297877e6ba7dd30cc1903ba18db2eba9d95a78231314d74e79e12e0c0619dd13	# PRD Review Template > ## When to skip the Revised PRD section	F2:1	123	1
H-A16-RT-019	docs/PRD_REVIEW_TEMPLATE.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# PRD Review Template > ## When to skip the Revised PRD section	F2:2	124	4
H-A16-RT-020	docs/PRD_REVIEW_TEMPLATE.md	d932370c8fd108584cca04db7721690a8ae11a4f37681ad48508adf12724ccc9	# PRD Review Template > ## When to skip the Revised PRD section	F2:3	125	1
H-A16-RT-021	docs/PRD_REVIEW_TEMPLATE.md	bed1130336b9f4e72cc57cd1aa464b76092834b84c9984871c8377ac075884bd	# PRD Review Template > ## When to skip the Revised PRD section	F2:4	126	1
H-A16-RT-022	docs/PRD_REVIEW_TEMPLATE.md	cdd077c9756800ae322f9613f761472f1848fdb6030cba88d8196c8afb6b96c6	# PRD Review Template > ## When to skip the Revised PRD section	F2:5	127	1
H-A16-RT-023	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## When to skip the Revised PRD section	F2:6	128	10
H-A16-RT-024	docs/PRD_REVIEW_TEMPLATE.md	856b142238a2aacd1d57d3ecaf5f32847c1367c39e2bb73c39f11197a9ffce02	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	HDG	132	1
H-A16-RT-025	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:0	144	10
H-A16-RT-026	docs/PRD_REVIEW_TEMPLATE.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:1	145	1
H-A16-RT-027	docs/PRD_REVIEW_TEMPLATE.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:1	145	2
H-A16-RT-028	docs/PRD_REVIEW_TEMPLATE.md	7fed46854b57d36b7e9d1e21c7b3c8dfba6b580cd629d427e83ad4cfe43126a4	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:2	146	1
H-A16-RT-029	docs/PRD_REVIEW_TEMPLATE.md	36c86fa017851c89910d324ab67f4fc1a7b61f623fe00a179bdc332e1bdda2a8	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:2	146	1
H-A16-RT-030	docs/PRD_REVIEW_TEMPLATE.md	ce04d5c2a7222e0d9e12cc0bc7db23aadfe321175463c27d72fe9ec440f2d6fe	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:3	147	1
H-A16-RT-031	docs/PRD_REVIEW_TEMPLATE.md	72b4e29e40c010c4dd85eb29e04482be685022b1ea3ba191f54a37e55bab7383	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:3	147	1
H-A16-RT-032	docs/PRD_REVIEW_TEMPLATE.md	1984dbbb744cc37eb3cbba12ddc08b260ecb70e936cf4778d5a9bb4c3d989d5d	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:4	148	1
H-A16-RT-033	docs/PRD_REVIEW_TEMPLATE.md	6d80bd100c49a1b843eadc1ea154a42c8b0f0cf6d4e7cb42721cd6afd572ffbb	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:4	148	1
H-A16-RT-034	docs/PRD_REVIEW_TEMPLATE.md	99c728a8afee3a9bd73e07473d10ac90cd145a1f90234b0107e21be62d7bd903	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:4	148	1
H-A16-RT-035	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	F3:5	149	10
H-A16-RT-036	docs/PRD_REVIEW_TEMPLATE.md	36fd4ee7b4f9ecf25741186313797043a24edb9d651e144eaae38f0fd9ce5838	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:5	167	2
H-A16-RT-037	docs/PRD_REVIEW_TEMPLATE.md	6e817fadc50fd0d18d5dd1bba51b424c51716583837df24efca931a19ae8c679	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	HDG	178	1
H-A16-RT-038	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:0	186	10
H-A16-RT-039	docs/PRD_REVIEW_TEMPLATE.md	c516eaca8548ab007ef61ce81d431a0bf66bf61c26ab8733fa1d0ce6f51a1b64	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:1	187	2
H-A16-RT-040	docs/PRD_REVIEW_TEMPLATE.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:2	188	4
H-A16-RT-041	docs/PRD_REVIEW_TEMPLATE.md	0bf7abe4ecc1549f5a2ed04282c1a1c1ac8c21989f56cfbaa027141d8af334ff	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:3	189	1
H-A16-RT-042	docs/PRD_REVIEW_TEMPLATE.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:4	190	4
H-A16-RT-043	docs/PRD_REVIEW_TEMPLATE.md	5d5b07cb393712f36b1d15b1af6ec033dae2ca4b8cb1257c0715914a7c1ce19b	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:5	191	1
H-A16-RT-044	docs/PRD_REVIEW_TEMPLATE.md	a94a8c3aecb6b73638cc5e318fdce6a304ef3b726f639bd46e402b06eaa03c17	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:6	192	1
H-A16-RT-045	docs/PRD_REVIEW_TEMPLATE.md	0011fdb6831bb88e458380123f3b4b60cfc52145ad90213acce85e288a5db03d	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:7	193	1
H-A16-RT-046	docs/PRD_REVIEW_TEMPLATE.md	a268cb5b97216ab1f8af44a07eae9369cfbe144ca3f5dfa743bb5d2f75116c82	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:8	194	1
H-A16-RT-047	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F4:9	195	10
H-A16-RT-048	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F5:0	225	10
H-A16-RT-049	docs/PRD_REVIEW_TEMPLATE.md	c516eaca8548ab007ef61ce81d431a0bf66bf61c26ab8733fa1d0ce6f51a1b64	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F5:1	226	2
H-A16-RT-050	docs/PRD_REVIEW_TEMPLATE.md	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F5:2	227	4
H-A16-RT-051	docs/PRD_REVIEW_TEMPLATE.md	45a3564ce64c71491dca64c025dcba292ce9b484b4b427dcbed13670531846da	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F5:3	228	1
H-A16-RT-052	docs/PRD_REVIEW_TEMPLATE.md	f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5	# PRD Review Template > ## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)	F5:4	229	10
H-A2-RT-001	docs/PRD_REVIEW_TEMPLATE.md	3f48209fc3b8c4afd0c163a813f88fd3933298a954b6590b71c1e033459214ca	# PRD Review Template > ## Review Independence (required, PRD-121 R4)		136	2
H-A2-RT-002	docs/PRD_REVIEW_TEMPLATE.md	3f48209fc3b8c4afd0c163a813f88fd3933298a954b6590b71c1e033459214ca	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:5	172	2
H-A5-RT-001	docs/PRD_REVIEW_TEMPLATE.md	851833bccec8dac2405286643c443217562a118de745165c42795adf60206374	# PRD Review Template		12	1
H-A5-RT-002	docs/PRD_REVIEW_TEMPLATE.md	991edd60e51954731a5e9057264280cdfcfc95a9bc653a03709c798184794514	# PRD Review Template		12	1
H-A5-RT-003	docs/PRD_REVIEW_TEMPLATE.md	bf4d4f07ca20ecf326cb39537e81d8c7ffc0eb455aca91ff7c784cba0c7403db	# PRD Review Template		13	1
H-A5-RT-004	docs/PRD_REVIEW_TEMPLATE.md	e67d48636eb40d75b05f6059ff92b3ff77da83687f90195a3cb209b26f9b2c85	# PRD Review Template		15	1
H-A5-RT-005	docs/PRD_REVIEW_TEMPLATE.md	4b71304c195ae124a9413429409034b44c58f6560e3f10bb65cd2433c31aa66c	# PRD Review Template > ## Review Independence (required, PRD-121 R4)		139	1
H-A5-RT-006	docs/PRD_REVIEW_TEMPLATE.md	a8ce16a33fe58bfdfdbb35184c54e4508ca4bb43a1f327d8c604ea29c7aa34ec	# PRD Review Template > ## Review Independence (required, PRD-121 R4)		139	1
H-A7-RT-001	docs/PRD_REVIEW_TEMPLATE.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:2	154	3
H-A7-RT-002	docs/PRD_REVIEW_TEMPLATE.md	53cdc2de6c3318c5af0384ae74ee89290a9763cce5df85f376c2cae82e277f0f	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:2	154	1
H-A7-RT-003	docs/PRD_REVIEW_TEMPLATE.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:3	158	3
H-A7-RT-004	docs/PRD_REVIEW_TEMPLATE.md	ab09c3574ac3612c4c7df9bc5e8a9b249d929a9c84c47430663b7ff90ac092e8	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:3	158	1
H-A7-RT-005	docs/PRD_REVIEW_TEMPLATE.md	09687989c242d7778678f4f2646c51ff2101e757b643971cf62394099fc448f1	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:3	158	3
H-A7-RT-006	docs/PRD_REVIEW_TEMPLATE.md	4b69257cb09896c40149b7ce1e1d6209c713552d0b60035acd7d0d73ebf88ddd	# PRD Review Template > ## Review Independence (required, PRD-121 R4)	LI:3	158	1
H-B3-RT-001	docs/PRD_REVIEW_TEMPLATE.md	e8570a6b4d4f80332858d79571880ccba2318e37d35c78fe04702faad089aefd	# PRD Review Template		20	1
```

## 6. Checker (embedded verbatim; run only by awk extraction, p5/p9.3)

```python h_manifest
#!/usr/bin/env python3
"""PRD-347 class-H one-to-one manifest checker (packet s4, s4C, s9.3).

PRE text  = `git show <ref>:<path>` for each of the 7 payload paths.
POST text = the working file <work>/<path>.
Emits one TSV line per class-H occurrence:
  ID  file  sha256(bytes)  heading-path  row-or-list-key  line  per-file-cardinality
--check exits non-zero unless: PRE and POST ID sets are identical; every ID's
sha256, heading-path and row/list key are identical (line may differ); every
per-file cardinality is identical; the s4C seed counts (and the zero-count
negatives) equal the PRE counts; and the `grep '^#'` heading list of every file is
identical PRE vs POST. Stdlib only; no network; reads git via subprocess.
"""
import argparse
import hashlib
import re
import subprocess
import sys

FENCE = "`" * 3

FILES = {
    "CM": "CLAUDE.md",
    "CH": "docs/CLAUDE_HOOKS.md",
    "PA": ".claude/skills/prd-authoring-verified/SKILL.md",
    "PC": ".claude/skills/prd-closeout-verified/SKILL.md",
    "PR": ".claude/skills/prd-review-claude/SKILL.md",
    "SL": ".claude/skills/scope-lock-precommit/SKILL.md",
    "RT": "docs/PRD_REVIEW_TEMPLATE.md",
}
SKILLS = ("PA", "PC", "PR", "SL")

# s4C seed: exact per-file occurrence counts at the packet seed SHA (unlisted file = 0).
SEED = [
    ("A7", "LANE: HIGH-RISK", {"PA": 1, "SL": 2, "RT": 1}),
    ("A7", "LANE: MICRO", {"PA": 1, "SL": 1, "RT": 1}),
    ("A7", "LANE: STANDARD", {"RT": 1}),
    ("A7", "LANE: MICRO | STANDARD | HIGH-RISK", {"PA": 1}),
    ("A7", "LANE: [MICRO | STANDARD | HIGH-RISK]", {"PA": 1, "SL": 1}),
    ("A11", "docs/AGENT_WORKFLOW.md", {"CM": 1, "CH": 1, "PA": 1, "SL": 8}),
    ("A11", "## Auto-Approval Policy", {"SL": 1}),
    ("A11", "Auto-Approval Policy", {"PA": 1, "SL": 4}),
    ("A10", "- **Active PRD:**", {"PC": 3}),
    ("A10", "none in progress", {"PC": 4}),
    ("A10", "**Next step", {"PC": 3}),
    ("A10", "Test baseline", {"PC": 4}),
    ("A6", "(PRD-NNN row)", {"SL": 2}),
    ("A6", "(active PRD pointer)", {"SL": 1}),
    ("A5", ".review.claude.md", {"PR": 6, "RT": 1}),
    ("A5", ".review.codex.md", {"PR": 4, "RT": 1}),
    ("A5", ".review.<model>.md", {"RT": 1}),
    ("A12", "docs/contract/MODE_REVIEW.md", {"PR": 1}),
    ("B7", "audits/EXECUTION_DOCTRINE.md", {"PR": 2}),
    ("A13", "CI is running", {"CM": 1}),
    ("A13", "Held for your merge", {"CM": 1}),
    ("A13", "Held for your decision", {"CM": 1}),
    ("A14", "Recon goes to subagents", {"CM": 1, "PA": 1}),
    ("A9", "STATUS: COMPLETE @", {"PC": 2}),
    ("A9", "Status: COMPLETE", {"PC": 2}),
    ("A9", "#NNN", {"PC": 6}),
    ("A15", "docs/plans/*-v0.1.md", {"CM": 1}),
    ("A15", "GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md", {"CM": 1}),
    ("A15", "PRODUCT_DELIVERY_OPERATING_RULE_2026-08-06.md", {"CM": 2}),
    ("A15", "OWNER_MERGE_AGENT_CLOSEOUT_CONVENTION_2026-08-06.md", {"CM": 1}),
    ("A18", ".claude/settings.json", {"CM": 1, "CH": 3}),
    ("B6", ".claude/settings.local.json", {"CM": 1}),
    ("A18", "scripts/pre_commit_sanity.sh", {"CH": 1, "PA": 1}),
    ("A18", ".claude/hooks/protect_files.sh", {"CH": 1}),
    ("A18", "scripts/install_hooks.sh", {"CH": 1}),
    ("A18", "tools/validate_prd_registry.py", {"CH": 1}),
    ("B6", "cuttingboard.yml", {"CM": 1}),
    ("B6", "mode: live", {"CM": 1}),
    ("A2", "prd-authoring-verified", {"PA": 1, "PR": 2}),
    ("A2", "prd-closeout-verified", {"PC": 1, "SL": 1}),
    ("A2", "prd-review-claude", {"PR": 1, "RT": 2}),
    ("A2", "scope-lock-precommit", {"SL": 1}),
    ("A12", "AUTHORITY: <MODE>", {"CM": 1}),
    ("A12", "docs/contract/MODE_<name>.md", {"CM": 1}),
    ("A17", "## Verification Report", {"PA": 3, "PC": 3, "PR": 2, "SL": 2}),
    ("B3", "Second-Model Disposition", {"PA": 1, "PR": 1}),
    ("B3", "Registry Maintenance", {"PA": 1, "PR": 1, "RT": 1}),
    ("B3", "LANE Axis", {"PA": 2}),
    ("B3", "Cosmetic Carve-Out", {"CM": 1, "PA": 1, "SL": 1}),
    ("B3", "Same-PR Closeout", {"CM": 1}),
    ("B3", "Same-PR\nCloseout", {"PC": 1}),
    ("B3", "Lane Downgrade Prohibition", {"SL": 1}),
    ("B3", "Review Dispatch", {"CM": 1}),
    # B1: the SECOND-MODEL sentence must never be copied into payload (count 0 everywhere).
    ("B1", "SECOND-MODEL:", {}),
    ("B1", "instrument not commissioned", {}),
]

# Row-definition literals enumerated by the generator (s4C last bullet); cardinality
# is taken from PRE and must be identical in POST.
EXTRA = [
    ("A7", "LANE"),  # every LANE literal (A7 "complete rg sweep"), catch-all
    ("A7", "GOVERNANCE"),  # the only CLASS name in payload (A7)
    ("A7", "LANE header"), ("A7", "LANE policy"), ("A7", "auto-escalate LANE"),
    ("A7", "CLASS/LANE matrices"),
    ("A5", "docs/prd_history/PRD-NNN.review.claude.md"),
    ("A5", "docs/prd_history/PRD-NNN.review.codex.md"),
    ("A5", ".review.claude.v2.md"),
    ("A5", "PRD-<NNN>\\.review\\.claude(\\.v\\d+)?\\.md"),
    ("A5", "PRD-252.review.codex.md"),
    ("A5", "Filename convention"),
    ("A5", ".claude/hooks/prd_eval.sh"),
    ("A6", "`pointer`"), ("A6", "`bookkeeping`"),
    ("A8", "`^[AMD] <path>`"), ("A8", "`` ^- `<path>` ``"), ("A8", "`Modified:`"),
    ("A8", "`New:`"), ("A8", "(`*`, `?`, `[`)"),
    ("A10", "**Active PRD:**"),
    ("A12", "RECON, DESIGN, IMPLEMENT, REVIEW,\nSTEWARD"),
    ("A13", "used verbatim"),
    ("A14", "- ESCALATION (inherited by every mode)."),
    ("A14", "Publish safety:"),
    ("A16", "ACCEPT | ACCEPT WITH CHANGES | REJECT"),
    ("A16", "fresh-context | different-model | same-context"),
    ("A16", "Reviewed SHA:"), ("A16", "Merge base:"), ("A16", "Independence:"),
    ("A16", "REVIEWED STATE"),
    ("A15", "5fe8ad7"), ("A15", "daa7065"), ("A15", "8224033"), ("A15", "1e1212d"),
    ("A1", ".claude/skills/prd-review-claude/SKILL.md"),
    ("A1", "docs/PRD_REVIEW_TEMPLATE.md"),
    # B6 payload references are CLAUDE.md:95-102 and CLAUDE_HOOKS.md only (packet s4B B6).
    ("B6", "protect_files.sh", ("CM", "CH")), ("B6", "prd_eval.sh", ("CM", "CH")),
    ("B6", "canonical_read_guard.sh", ("CM", "CH")), ("B6", ".claude/hooks/", ("CM", "CH")),
    ("B6", "ui/dashboard.html", ("CM",)), ("B6", "ui/index.html", ("CM",)),
    ("B7", "EXECUTION_DOCTRINE.md` sec 1"), ("B7", "EXECUTION_DOCTRINE.md`\n   sec 1"),
    ("B5", "docs/contract/MODE_*.md"),  # B5 payload refs = the A12 occurrences (+ this CM path)
]

# Whole lines frozen by row: A15 Ratification paragraph (CLAUDE.md), A16 review
# structure line literals.
WHOLE_LINES = [
    ("A16", "PR", "VERDICT"), ("A16", "PR", "SUMMARY"), ("A16", "PR", "REQUIRED EDITS"),
    ("A16", "PR", "RECOMMENDED EDITS"), ("A16", "PR", "RATIONALE"),
    ("A16", "PR", "IMPLEMENTATION VERDICT"), ("A16", "PR", "DRIFT CHECK"),
    ("A16", "PR", "CROSS-REVIEW NOTES (cross-review mode only)"),
]


def git_show(ref, path):
    out = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True)
    if out.returncode != 0:
        sys.exit(f"FAIL: git show {ref}:{path}: {out.stderr.decode().strip()}")
    return out.stdout.decode("utf-8")


def read_work(work, path):
    try:
        with open(f"{work}/{path}", encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        sys.exit(f"FAIL: cannot read {work}/{path}: {exc}")


def structure(text):
    """Per line: (heading_path, key). Fences, frontmatter, tables, list items."""
    lines = text.split("\n")
    info = []
    path = []
    in_fence = False
    fence_n = 0
    fence_off = 0
    front = lines[:1] == ["---"]
    front_end = None
    if front:
        for i in range(1, len(lines)):
            if lines[i] == "---":
                front_end = i
                break
    item_n = 0
    cur_item = None
    for i, ln in enumerate(lines):
        if front_end is not None and i <= front_end:
            info.append(("", f"FM:{i + 1}"))
            continue
        if ln.startswith(FENCE):
            if not in_fence:
                in_fence = True
                fence_n += 1
                fence_off = 0
            else:
                in_fence = False
            info.append((" > ".join(path), f"F{fence_n}:{fence_off}"))
            fence_off += 1
            continue
        if in_fence:
            info.append((" > ".join(path), f"F{fence_n}:{fence_off}"))
            fence_off += 1
            continue
        m = re.match(r"^(#{1,6}) ", ln)
        if m:
            lvl = len(m.group(1))
            path = path[: lvl - 1] + [ln]
            item_n = 0
            cur_item = None
            info.append((" > ".join(path), "HDG"))
            continue
        hp = " > ".join(path)
        if ln.startswith("|"):
            cells = [c.strip() for c in ln.strip("|").split("|")]
            info.append((hp, f"ROW:{cells[0] if cells else ''}"))
            cur_item = None
            continue
        if re.match(r"^(- |\d+\. )", ln):
            item_n += 1
            cur_item = f"LI:{item_n}"
            info.append((hp, cur_item))
            continue
        if ln.strip() == "":
            info.append((hp, ""))
            continue
        if ln.startswith(" ") and cur_item is not None:
            info.append((hp, cur_item))
            continue
        cur_item = None
        info.append((hp, ""))
    return lines, info


def occurrences(code, text):
    """Return list of (row, literal, offset) for every class-H occurrence in text."""
    occ = []
    seen = set()
    for row, lit, _ in SEED:
        if (row, lit) in seen:
            continue
        seen.add((row, lit))
        start = 0
        while True:
            j = text.find(lit, start)
            if j < 0:
                break
            occ.append((row, lit, j))
            start = j + len(lit)
    for spec in EXTRA:
        row, lit = spec[0], spec[1]
        if len(spec) > 2 and code not in spec[2]:
            continue
        start = 0
        while True:
            j = text.find(lit, start)
            if j < 0:
                break
            occ.append((row, lit, j))
            start = j + len(lit)
    lines, info = structure(text)
    offs = []
    pos = 0
    for ln in lines:
        offs.append(pos)
        pos += len(ln) + 1
    for i, ln in enumerate(lines):
        hp, key = info[i]
        whole = None
        if key.startswith("FM:") and code in SKILLS:
            whole = "A4"
        elif key == "HDG":
            whole = {"CM": "A14", "CH": "A18", "PR": "A16", "RT": "A16"}.get(code, "A17")
        elif key.startswith("ROW:"):
            whole = {"CH": "A18", "RT": "A16"}.get(code, "A17")
        elif key.startswith("F"):
            whole = "A16" if code in ("PR", "RT") else "A17"
        elif code == "CM" and front_is_ratification(lines, i):
            whole = "A15"
        for row, fc, lit in WHOLE_LINES:
            if fc == code and ln == lit:
                occ.append((row, "LINE:" + lit, offs[i]))
        if whole:
            occ.append((whole, "LINE:" + ln, offs[i]))
    return occ, lines, info, offs


def front_is_ratification(lines, i):
    # CLAUDE.md "## Ratification" paragraph: the non-blank lines after that heading.
    try:
        h = lines.index("## Ratification")
    except ValueError:
        return False
    j = h + 1
    while j < len(lines) and lines[j].strip() == "":
        j += 1
    k = j
    while k < len(lines) and lines[k].strip() != "":
        k += 1
    return j <= i < k


def manifest(code, text):
    occ, lines, info, offs = occurrences(code, text)
    occ.sort(key=lambda t: (t[0], t[2], t[1]))
    card = {}
    for row, lit, _ in occ:
        card[(row, lit)] = card.get((row, lit), 0) + 1
    rows = []
    per_row = {}
    for row, lit, off in occ:
        per_row[row] = per_row.get(row, 0) + 1
        line_i = max(k for k in range(len(offs)) if offs[k] <= off)
        hp, key = info[line_i]
        data = lit[5:] if lit.startswith("LINE:") else lit
        rows.append({
            "id": f"H-{row}-{code}-{per_row[row]:03d}",
            "file": FILES[code],
            "sha": hashlib.sha256(data.encode("utf-8")).hexdigest(),
            "hp": hp,
            "key": key,
            "line": line_i + 1,
            "card": card[(row, lit)],
            "lit": lit,
        })
    headings = [ln for ln in lines if ln.startswith("#")]
    return rows, headings


def write_tsv(path, allrows):
    with open(path, "w", encoding="utf-8") as fh:
        for r in allrows:
            fh.write("\t".join([r["id"], r["file"], r["sha"], r["hp"], r["key"],
                                str(r["line"]), str(r["card"])]) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out-pre", required=True)
    ap.add_argument("--out-post", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    pre_all, post_all, errors = [], [], []
    for code, path in FILES.items():
        pre_text = git_show(a.ref, path)
        post_text = read_work(a.work, path)
        pre_rows, pre_h = manifest(code, pre_text)
        post_rows, post_h = manifest(code, post_text)
        pre_all += pre_rows
        post_all += post_rows
        for row, lit, want in SEED:
            got = pre_text.count(lit)
            exp = want.get(code, 0)
            if got != exp:
                errors.append(f"SEED {code} {row} {lit!r}: seed {exp} != PRE {got}")
        if pre_h != post_h:
            errors.append(f"HEADINGS {code}: grep '^#' list differs PRE vs POST")
        pm = {r["id"]: r for r in pre_rows}
        qm = {r["id"]: r for r in post_rows}
        for i in sorted(set(pm) - set(qm)):
            errors.append(f"MISSING {i} {pm[i]['lit']!r} (PRE line {pm[i]['line']})")
        for i in sorted(set(qm) - set(pm)):
            errors.append(f"ADDED {i} {qm[i]['lit']!r} (POST line {qm[i]['line']})")
        for i in sorted(set(pm) & set(qm)):
            p, q = pm[i], qm[i]
            for f in ("sha", "hp", "key", "card"):
                if p[f] != q[f]:
                    errors.append(f"CHANGED {i} {f}: PRE {p[f]!r} POST {q[f]!r}")
    write_tsv(a.out_pre, pre_all)
    write_tsv(a.out_post, post_all)
    print(f"PRE ids={len(pre_all)} POST ids={len(post_all)} errors={len(errors)}")
    if a.check and errors:
        for e in errors:
            print("FAIL: " + e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
