# PRD lifecycle audit — Phase 1 reconstruction (2026-07-05)

Read-only audit charge (branch `claude/prd-lifecycle-audit-phase-0-uyc92f`).
Phase 0 model confirmed by Dustin 2026-07-05 with corrections; this file is the
Phase 1 deliverable: full-lifecycle reconstruction + diagnosis of where the
circular work comes from. Prescriptions are deferred to Phase 3 by charge.

Evidence base: five delegated Explore reconstructions over the full unshallowed
`main` history (1,056 non-merge commits, 2026-04-10 → 2026-07-05), plus direct
reads of CLAUDE.md, PRD_PROCESS.md, hooks, skills, ci.yml, prd_open/close.

---

## 1. Headline numbers (commit census, full history)

| Category | Count | % of 1,056 |
|---|---:|---:|
| Product implementation | 350 | 33.1% |
| PRD closeout bookkeeping | 127 | 12.0% |
| Reconciliation/repair of bookkeeping | 55 | 5.2% |
| Process/governance/tooling/docs | 173 | 16.4% |
| Review artifacts | 58 | 5.5% |
| Bot artifact publishes | 271 | 25.7% |
| Handoff/audit notes + other | 22 | 2.1% |

- **Bookkeeping tax = 17.2% of all commits (≈22.4% of human commits).**
  One reconciliation-repair commit for every ~2.3 closeout commits.
- **The two most-churned files in the entire repository are ledgers:**
  `PRD_REGISTRY.md` (350 revisions) and `PROJECT_STATE.md` (252) — each 2–3×
  the busiest source file (`dashboard_renderer.py`, 123). Four ledgers total
  804 file-revisions across 1,056 commits (~0.76 ledger-touches per commit).
- Separate-closeout commits by month: Apr 1 → May 77 → Jun 46 → Jul 7.
  The July collapse is PRD-229 same-PR closeout working as designed.
- Process-PRD share: ~50 of ~228 PRDs (22–24%), heavily back-loaded — roughly
  half of all PRDs since 2026-06-13 are process work (DECISIONS 2026-07-04:
  "process output was ~3× product output").

## 2. The named loops (where the circular work comes from)

Each loop is stated with its mechanism, evidence, and **current live status** —
per the charge, weight goes to what is live now.

### Loop 1 — SHA-provenance loop. STATUS: KILLED (by PRD-229)
Registry stored the implementation SHA; pre-push rebases invalidated it;
a separate "backfill/correct hash after rebase" commit followed. ~20 of the 55
reconciliation commits are this exact shape (PRDs 017/018/020/074/079/080/104/
105/112–117/119/127/134/139/141/160…). PRD-229's `#NNN` commit-cell convention
removes the movable identity; no post-229 instance observed. Residue: 19
historical unresolvable hashes (known debt, CI skips resolvability).

### Loop 2 — Format↔tooling coupling. STATUS: PARTIALLY LIVE
Prose ledger formats are parsed by regex tooling; every format evolution
silently broke a parser, and every parser fix was its own PRD. The closeout
spine: **147 → 164 → 171 → 172 → 183 → 196 → 203**, where PRD-203 repaired a
bug PRD-196 itself introduced, and PRD-183's root cause was "the doc was
restructured without updating the tooling, so each closeout silently skipped
five edits." Zero of these were triggered by product work. Mitigations that
took: fail-loud closeout (196), CI-gated consistency (200), same-PR closeout
(229). Still live: `PROJECT_STATE.md` remains a prose ledger whose claims only
an LLM read can check; the validator covers registry/index/doc-STATUS, not
PROJECT_STATE prose.

### Loop 3 — Rule-change → enforcement-surface lag. STATUS: LIVE
A rule lives in ≥4 surfaces at once: CLAUDE.md text, PRD_PROCESS.md, skills,
hooks/scripts. Every rule change requires N-surface sync; the lag is itself a
PRD generator. Instances: 108→143→145 (hook exclusion list patched three
times), 121→183 (PROJECT_STATE reformat orphaned the tooling), **229→232
(PRD-232 exists solely because 229 changed rules the skills didn't yet
encode — one PRD of pure enforcement-surface catch-up, one day later)**.
Live today: `docs/CLAUDE_HOOKS.md` claims settings.json "denies git push
outright" while settings.json allows `Bash(git push:*)` (denies only force) —
the same class, currently drifted.

### Loop 4 — External-identity gate (Codex). STATUS: LIVE as a waiver ritual
Arc: PRD-197 built the CI gate (2026-06-17, host-SPOF driver) → PRD-207
repaired it (hollow requested-vs-served resolution; the one real catch: model
laundering) → PRD-212 pinned the CLI on a **falsified premise** (diagnosed
alias-drift; actual cause was OpenAI's 2026-04-01 retirement of `gpt-5-codex`;
both waiver legs later voided) → retarget to gpt-5.5 (PR #76) → **PRD-230
deleted the whole apparatus 2026-07-04** (−344-line workflow, −355-line tests;
peak 699 LOC, ~8 PRs, 17 days of life, one real catch).

**Current state, verified:** no codex workflow in `.github/workflows/`; CI
`test` job = registry validation + pytest only. The surviving CLAUDE.md gate
text requires a durable `codex exec -s read-only` artifact — producible only
on a host with the codex CLI. The remote container has none; the connector bot
is out of credits. **Last genuine Codex review: PRD-228 @ `225e93b`
(2026-07-03, git-only); last landed on main: PRD-226 @ `3ffa027`. All 8
HIGH-RISK PRDs closed since PRD-230 (232–238, 240) took the waiver.**
Net: the HIGH-RISK second-review gate is currently satisfied by Dustin's
manual merge alone, every time, while the gate text still describes an
artifact requirement no available machine can produce. Ossification vs.
restore-vs-rewrite is the Phase 3 call; Phase 1 records the divergence as the
top-line drift finding.

### Loop 5 — Doc-restatement drift. STATUS: LIVE, ACCELERATING
Docs that restate code facts (gate counts, stage orders, constants) drift and
are re-fixed by doc-truth PRDs. Interval is shrinking: early fixes ~2–3 weeks
apart (04-24, 05-10, 05-18, 06-13); then **five doc-truth items inside
07-04→07-05** (PRD-230 map de-line-numbering, 231, 238, 239, 241), including
two next-day recurrences of the same defect class: gate-count fixed 3 places
by PRD-231 (07-04) and still wrong in `system_logic_map.md` the next day
(PRD-241); `architecture.md` corrected 06-13 (`f369ee6`) and again by PRD-239.
PRD-238's retirement of SCHEMA_MAP's field-lookup role is the one structural
(not corrective) move in this loop so far.

### Loop 6 — Hook false positives. STATUS: LIVE (observed 4× in this session)
`prd_eval.sh` keys on PRD-NNN tokens + section keywords in the "prompt". In
this audit session it injected **PRD REVIEW MODE once and PRD IMPLEMENTATION
REQUEST three times — all on subagent task-notification traffic, none on an
actual PRD submission.** This is the same false-positive family PRD-108/143/
145 patched by exclusion-list whack-a-mole; the detector remains keyword-based
so the class regenerates against every new message shape. Cost: injected gate
instructions consume attention/context on every PRD-token-bearing message and
train the operator to ignore gate output (CLAUDE.md itself already carries a
"sequencing-gate fires are actionable, not boilerplate" apology clause — a
documented symptom of gate fatigue).

### Loop 7 — Delegated-recon false all-clear. STATUS: MITIGATED, residual
Eight documented incidents of context lost at delegation/sweep seams:
PRD-158's three FILES-amendment loops + six missed Explore dispatches;
the PRD-194 glob-read misses (two extra closure sweeps); the 2026-06-10
sub-agent flow audit's false-all-clear path (→ re-verification rule);
PRD-223's missed contract overlay (deferral built on incomplete recon);
PRD-240's fixture-geometry miss (token sweep insufficient → full-suite-at-
scoping rule) and the stale-`__pycache__` phantom result; the retired
`test_gate.sh` false "all passed". Mitigations landed (re-verification rule,
full-suite-at-scoping, cache-invalidation rule) are the correct shape:
**verify-at-the-seam, not more delegation ceremony.** Confirmed: no custom
sub-agents exist and none should — consistent with the no-multi-agent
non-goal; the residual risk is seam discipline, not missing agent types.

## 3. Necessary infrastructure vs. avoidable rework (H2 separation)

**Necessary investment (kept its value):** PRD-028 (template/registry
foundation), 061+200 (machine index + CI-gated consistency — drift detection
moved from manual to merge-gate), 121 (lanes), 184 (auto-merge landing flow),
186 (drift-check discipline), 198 (semantic-hardening doctrine — its
invariants correctly predicted several later incidents), 229/230 (ceremony
reduction — measurable: July closeout-commit collapse; ~19% commit-volume
reclaim).

**Avoidable rework (machinery repairing itself):** the entire closeout-script
spine after 147 (six repairs, one self-inflicted regression); the hook
exclusion whack-a-mole (108/143/145); 146/148 index backfills (drift from a
crashed/skipped closeout script); PRD-232 (pure enforcement-lag catch-up);
and the Codex apparatus' repair tail (207 was a legitimate catch; **212 is
the clearest avoidable unit** — a pin built on an undiagnosed premise,
violating PRD-198 #2/#6 which the repo had already adopted).

**The 21-PRD lifecycle-machinery chain contains zero PRDs triggered by product
work.** All were net-new machinery or machinery repairing machinery. That is
the structural signature of H1: the ledger system generates its own workload.

## 4. Point findings (verified directly, not delegated)

1. **CI merge gate** = `test` job: `validate_prd_registry.py
   --skip-commit-resolvability` + ruff/pytest. Nothing Codex-shaped gates any
   merge. (Read `ci.yml` directly.)
2. **`active_prd.txt`** is written by the agent by convention ("you, on PRD
   approval" — CLAUDE_HOOKS.md); no script writes it; `prd_open.sh` confirmed
   not to. Fresh-clone absence ⇒ `protect_files.sh` fails closed on protected
   paths — safe by design, but the unlock path depends on an unenforced
   convention, and in remote containers the practical state is
   "permanently fail-closed unless remembered."
3. **CLAUDE_HOOKS.md drift**: claims settings.json denies `git push`; actual
   settings allow it (deny force-push only). Loop-3 instance, live.
4. **GitNexus skills (12 files): delete-safe subtraction candidate.**
   All single-commit, never regenerated. `generated/*` measurably stale
   (claims 78 test files vs 105 actual; 12 cuttingboard files vs 44; all six
   spot-checked line refs wrong) and point at `gitnexus_*` MCP tools that are
   not configured. Four of `gitnexus/*` have trigger descriptions that fire on
   ordinary prompts ("How does X work?", "Why is X failing?", "Rename this
   function") and would route to an uninstalled tool. Dangling references to
   reconcile on deletion: `docs/knowledge_systems.md` (GitNexus doctrine),
   `scripts/gitnexus-analyze.sh`, `scripts/pre_commit_sanity.sh:52-62`
   (`npx --no-install gitnexus detect-changes` silently no-ops today),
   `.gitignore` lines, incidental mentions in five PRD skills.
5. **Truth-store count**: 4 hard-synchronized stores at closeout (registry,
   index, PROJECT_STATE, PRD-doc STATUS) enforced by validator+skill; a full
   lifecycle touches up to 7 (adding DECISIONS, review artifacts, resume
   notes).
6. **Closeout latency** (the known soft spot): median 0–1 day, but the tail is
   the cost center — PRDs 190/207/210 each needed 2–3 separate reconcile
   commits over 1–6 days, and closeouts batched across PRDs ("190s backfill",
   "210/211/212") are exactly the done-in-spirit-before-rows-close pattern.
   Post-229 this class is structurally closed for new PRDs.

## 5. Hypothesis verdicts

- **H1 (bookkeeping fan-out) — CONFIRMED, primary.** 17.2% commit tax, ledgers
  as the repo's most-churned files, a 21-PRD self-repairing machinery chain
  with zero product triggers, and a dominant sub-loop (SHA backfill) that the
  #NNN reform demonstrably killed — proof the loop was structural, not
  behavioral.
- **H2 (process-on-process) — CONFIRMED with the required split.** Not all
  waste: foundation + enforcement-at-CI + ceremony-reduction PRDs carried
  their cost. The avoidable fraction is concentrated in (a) format↔tooling
  coupling repairs, (b) enforcement-surface lag, (c) the Codex repair tail.
- **H3 (doc-truth drift) — CONFIRMED, accelerating.** Interval between
  doc-truth fixes is shrinking; same-class recurrence within 24h twice on
  07-04/05.

## 6. Open questions carried to Phase 2/3

1. Codex gate: rewrite the clause to match waiver reality, restore a real
   second-review mechanism, or tier it — Phase 3 decision (Dustin).
2. PROJECT_STATE.md: it is the one hard-synchronized store with no mechanical
   validation (prose). Whether to shrink it toward pointers (registry/index
   own status; PROJECT_STATE owns only narrative) is a Phase 3 design.
3. prd_eval.sh: exclusion-list patching has failed three times; the detector
   likely needs a channel gate (fire only on genuine user prompts / explicit
   markers), not a fourth exclusion. Phase 3.
4. GitNexus deletion + dangling-reference reconciliation: candidate for a
   single subtraction PRD. Phase 3.
5. CLAUDE_HOOKS.md git-push claim: one-line doc fix; fold into whatever
   Phase 3 lands.

---
*Phase 1 complete. No source, contract, or `main` mutation. Delegated
reconstructions re-verified at the decisive points per CLAUDE.md sweep
re-verification: ci.yml jobs, workflows directory, prd_open.sh, settings.json,
CLAUDE_HOOKS.md state-file table all read directly by the main agent.*
