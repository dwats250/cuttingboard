# PRD lifecycle audit — Phase 2 verification + Phase 3 prescriptions (2026-07-05)

Companion to `phase1-reconstruction.md` (same folder). Phase 2 adversarially
verified Phase 1's load-bearing claims and swept for CURRENTLY-live drift.
Phase 3 converts the verified diagnosis into prescriptions, subtraction-first,
weighted to what is live now. Read-only charge throughout; nothing here
mutates source, contracts, or `main`.

---

# PHASE 2 — What survived verification, what didn't

## 2.1 Claim verdicts (adversarial pass)

| Phase 1 claim | Verdict | Correction |
|---|---|---|
| 21 machinery PRDs, zero product-triggered | **CONFIRMED** | Near-misses examined (143, 196b, 229) do not refute: none repairs product code. |
| 8 post-230 HIGH-RISK PRDs all waived the Codex leg | **CONFIRMED** | All 8 declare `LANE: HIGH-RISK`; zero `.review.codex.md` exist. Sharpened: **PRD-240 is a gate-skip, not a clean waiver** — its own Claude review (`PRD-240.review.claude.md:159-161`) states the Codex leg "is separately required before merge per CLAUDE.md," and it merged anyway. The waiver is environment-forced, not discretionary. |
| Bookkeeping tax 17.2% | **WEAKENED — understates.** | Keyword census missed ~45 "close PRD-NNN"-form commits and the denominator includes 193 bot commits. True separate-commit tax ≈ **21–26% of real dev commits**. Offsetting nuance: the tax is largely a **pre-PRD-229 legacy phenomenon**; post-229, bookkeeping folds into impl commits by design. |
| Doc-truth loop "accelerating" | **WEAKENED — retracted.** | The 07-04/05 cluster is **planned batch-paydown across two deliberate audit windows** (Fable window per `FABLE_WINDOW_PLAN.md`; qualification audit), not organic acceleration. The 231→241 "recurrence" is a **scope-completeness miss** (231 swept module docstrings, not prose docs; 241 self-describes as the gaps "PRD-231 did not sweep") — not the same defect drifting back. The loop is real as a *structural liability* (see 2.3), but the acceleration framing was wrong and is withdrawn. |

Honest-correction note: Phase 1 overstated Loop 5's dynamics and understated
Loop 1's magnitude. Both corrections are carried into the prescriptions.

## 2.2 Current-drift ledger (all live on main today)

Twelve entries; the ones that can cause wrong action, ranked:

1. **PROJECT_STATE self-contradiction (HIGH).** `PROJECT_STATE.md:31` says
   PRD-240/241 are "PROPOSED … held for Dustin's go/no-go — no implementation
   until approved" while lines 13–14 of the same file (and registry + index)
   record both COMPLETE via #111/#113. An agent trusting line 31 could
   re-implement merged work. Also: header "Last updated (commit #95)" vs #113
   rows; "`next_prd: 240`" vs actual `next_prd: 242` (a collision seed).
2. **Skill contradicts a CLAUDE.md ban (HIGH).** `dashboard-publish-refresh`
   documents a WRITE_MODE (render → `ui/dashboard.html` → cp to `index.html`
   → `git add`) that is exactly the sandbox-overwrite `CLAUDE.md:208-216`
   forbids. Default DRY_RUN limits blast radius; the documented mode is the
   hazard.
3. **PRD_PROCESS Review Dispatch vs Codex scoping (HIGH, folded into P1).**
   `PRD_PROCESS.md:112-127` still mandates a parallel Codex cross-review for
   "most PRDs"; CLAUDE.md scopes Codex to HIGH-RISK only. An agent following
   PRD_PROCESS would commission unfulfillable reviews for every draft.
4. **`prd-review-claude` refuses the Codex slot citing a nonexistent owner
   (MED).** The skill says the slot is "owned by the cross-review-gate hook";
   no such hook exists — per CLAUDE.md, Claude Code IS the writer of captured
   codex stdout. The refusal blocks a legitimate action.
5. **Stale debt figure (MED).** "19 unreachable hashes" (PROJECT_STATE ×2,
   PRD_PROCESS) — actual full-validator count today: 29 PRDs / 35–36 lines,
   including the Fable-window-era 208/213–222. The #NNN convention has ended
   the class; the recorded debt never caught up.
6. **CLAUDE_HOOKS.md: "settings.json denies git push outright" (MED)** —
   settings allow `Bash(git push:*)`; only force variants are denied.
7. **Dangling/fabricated cross-refs (LOW).** Skills cite `CLAUDE.md §
   Cross-review gate`, `§ Review artifact discipline` (with an invented
   quoted rule), `§ Cheap-Lookup Dispatch Policy` — none exist as headers.
   `pre_commit_sanity.sh:52` cites "CLAUDE.md § GitNexus … mandatory" — no
   such rule; the step no-ops.
8. **Undefined status vocabulary (LOW).** SHELVED / VOID / HELD / PREMISE
   SUPERSEDED are used in narrative but undefined in PRD_PROCESS's 5-state
   set (the registry status column itself stays clean — validated).
9. **Retired-cadence anchor (LOW).** PROJECT_STATE debt line re-evaluates "by
   2026-07-31 (next alignment cadence)" — the cadence was retired by PRD-230.

Clean negatives (verified, no drift): the 7 hand-written skills do NOT encode
retired closeout/Codex/cadence rules; validator ALLOWED_STATUSES == process
doc; ci.yml matches its documentation; CODEX.md defers correctly;
pre_push_check.sh is live; AGENT_WORKFLOW.md is alive and load-bearing (not
sediment).

## 2.3 Doc-restatement liability (Loop 5, re-characterized)

The live drift is concentrated in **recon/doctrine docs with line numbers and
dead paths**, not the freshly-fixed qualification docs:

| Doc | State today |
|---|---|
| `renderer_decomposition_map.md` | ~200+ line-number cites, SHA-pinned design doc, already drifting (2,880→2,948 lines). Self-disclaimed HOLD — tolerable only because of the disclaimer. |
| `audit_doctrine.md` | 3/3 spot-checks wrong: dead `moomoo_join.py` ref, stale `runtime.py` path, wrong `runtime.py:1004`. Never re-verified since PRD-155. |
| `SCHEMA_MAP.md` | All 5 residual line refs wrong (+20 to +135 lines). PRD-238 retired the field-lookup role but left the cites. |
| `trade_qualification.md`, `system_logic_map.md`, `architecture.md` | Near-accurate today (PRD-241/239 fresh); structurally the densest standing constant-mirrors (~60–70 and ~30–50 restated facts). |
| `CALL_SITE_MAP.md` | **The working model**: PRD-230 de-line-numbered it; "grep -n is free and always current." Zero line numbers confirmed. |

## 2.4 Hook false-positive liveness (Loop 6)

Final session tally: **six `prd_eval.sh` misfires in this audit session** (1×
PRD REVIEW MODE, 5× IMPLEMENTATION REQUEST), every one triggered by subagent
task-notification traffic, zero by an actual PRD submission. Mechanism (full
script read): keyword detector (PRD-NNN + ≥4 section keywords, or an
impl-verb within 30 chars of PRD-NNN) with **no channel discrimination** —
fires on any UserPromptSubmit payload. Meanwhile the sequencing gate's
suppressor list includes `because`, `reason for`, `codex`, `batch` — i.e. it
over-fires on non-prompts and is trivially suppressed on real ones. The CI
validator (PRD-200) now covers the registry-consistency ground truth at the
merge gate, which is where it matters.

---

# PHASE 3 — Prescriptions

Ordering = live cost. Subtraction-first per VISION ("cuts before additions").
Each item names its lane; governance-guardrail changes are MANUAL-MERGE-ONLY
per the CLAUDE.md carve-out. Nothing below prescribes new agents, new hooks,
or new synchronized stores.

## P1 — Make the HIGH-RISK second-review gate honest (Codex decision). [Dustin's call; governance, MANUAL-MERGE-ONLY]

The gate text requires an artifact no available machine can produce; 8/8
HIGH-RISK closes since PRD-230 waived or skipped it; the apparatus that
enforced it caught one real issue in 17 days of life and was deleted at
net-zero LOC.

- **Option A (recommended): requirement → capability.** Rewrite the CLAUDE.md
  gate: the HIGH-RISK second leg is the fresh-context Claude review artifact
  (unchanged, mandatory) + Dustin's manual merge as the human gate. Codex
  cross-review becomes an *available instrument* Dustin can commission when he
  has a codex-capable host — recorded when it happens, never owed, no waiver
  ritual, no per-PRD waiver bookkeeping. Rationale: it codifies what every
  merge since 07-03 has actually been; the solo-repo argument PRD-230 already
  accepted for the CI leg applies identically to the clause residue. Fold in
  the PRD_PROCESS Review Dispatch rewrite (ledger #3) so both docs say one
  thing.
- **Option B: restore a real second model** (codex CLI on the host, or another
  API model driven the same read-only way). Honest only if the host leg is
  actually exercised — otherwise it recreates today's fiction. History prices
  this loop at 5 PRDs / ~8 PRs for one catch; a second model's marginal value
  against a fresh-context Claude review + human merge is unproven here.
- **Option C: tier it** — keep the hard requirement only for EXECUTION-class
  contract changes, Option-A treatment elsewhere. More rules, more lag
  surface (Loop 3); only worth it if Dustin wants a hard external check on
  money-touching changes specifically.

If A: also delete the retained `ALLOWED_CODEX_MODELS`-era vocabulary from any
surviving prose and record the decision in DECISIONS.md as the close of the
197→230 arc.

## P2 — Fix PROJECT_STATE now; shrink its authority next. [bookkeeping commit + STANDARD process PRD]

Immediate (one bookkeeping commit, ~15 min): correct the five live falsehoods
— header #95→current, PRD-240 "pending #111" bullet, the PROPOSED/held line
31, `next_prd: 240` line, debt figure 19→actual (and re-scope its list), the
"next alignment cadence" anchor.

Structural (small PRD): PROJECT_STATE stops carrying *duplicated status
facts*. Status/provenance live only in registry+index (which the CI validator
already guards); PROJECT_STATE bullets reference registry rows instead of
restating COMPLETE/PROPOSED/pending-merge. Add two cheap mechanical checks to
`validate_prd_registry.py`: (a) the header's `#NNN` ≥ the max `#NNN` in any
registry commit cell; (b) no PRD-NNN in PROJECT_STATE carries a status word
that contradicts its registry row (a grep-level check, not prose parsing).
This closes the only synchronized store with zero validation — the store that
is self-contradicting today. Also: either define SHELVED/VOID/HELD/PREMISE-
SUPERSEDED in PRD_PROCESS as *narrative annotations* (registry column stays
5-state) or stop using them; one paragraph settles ledger #8.

Explicitly NOT prescribed: a PROJECT_STATE generator tool. `prd_close.sh`
already rebuilds the baseline line; more generation machinery is Loop-2 bait.

## P3 — Retire prd_eval.sh's detectors; keep the registry-gap check. [MICRO + red test per invariant #4 for what remains]

Evidence: six misfires this session on non-prompts; three historical
exclusion-list repair PRDs (108/143/145) failed to close the class; the
suppressor list makes the sequencing gate advisory-at-best on real prompts;
and PRD-200 + same-PR closeout removed the drift source the gate was built to
nag about (CLAUDE.md itself says repeated fires signal overdue closeout —
post-229 closeout is never "overdue" for new PRDs). Delete the PRD-body and
impl-request detectors; keep (or move to the closeout skill) the registry-gap
check, which is cheap and channel-safe. If any detector is kept, gate it on
an explicit marker in the prompt rather than keyword inference. This is a
hook-family subtraction, consistent with the 2026-06-13 `test_gate.sh`
precedent (net-negative guard → cut).

## P4 — Delete the GitNexus surface. [MICRO/STANDARD subtraction PRD]

Delete: `.claude/skills/generated/*` (6 — stale indexes: 78-vs-105 test
files, all spot-checked line refs wrong, pointing at unconfigured
`gitnexus_*` MCP tools), `.claude/skills/gitnexus/*` (6 — four of them
trigger on ordinary "how/why/what-breaks/rename" prompts toward an
uninstalled tool), `scripts/gitnexus-analyze.sh`, and the
`pre_commit_sanity.sh` detect-changes step with its fabricated "CLAUDE.md §
GitNexus" citation. Reconcile: `docs/knowledge_systems.md` (retire or rewrite
the GitNexus layer as historical), `.gitignore` lines, incidental mentions in
five skills. Keep: nothing — the wrapper has no-op'd in every environment
without the CLI and the indexes were never regenerated after 2026-06-26.

## P5 — Extend PRD-230's de-line-numbering; spot-fix the wrong docs. [one polish-batch MICRO]

(a) Fix `audit_doctrine.md` (dead moomoo ref, runtime path/line) and strip
SCHEMA_MAP's five stale `file:line` cites to file+symbol form — the
CALL_SITE_MAP convention, stated in its own header, becomes the repo rule:
**docs cite file+symbol, never line numbers; grep at use.** (b) Stamp
`renderer_decomposition_map.md`'s disclaimer forward or regenerate at
execution time per its own HOLD terms. (c) For the constant-mirrors
(trade_qualification, system_logic_map, architecture): no new machinery —
extend the existing closeout discipline with one line: a PRD that changes a
constant/gate/stage listed in a mirror doc adds that doc to FILES (this is
the existing pre-implementation grep sweep applied to docs/, not a new
process).

## P6 — One enforcement-surface sync batch + the rule that stops Loop 3. [MICRO batch; the rule line is governance, MANUAL-MERGE-ONLY]

Batch-fix in one PR: CLAUDE_HOOKS git-push line; delete
`dashboard-publish-refresh` WRITE_MODE (CLAUDE.md says DRY_RUN at most —
remove the contradiction in the dangerous direction); fix
`prd-review-claude`'s codex-slot ownership text (slot writable by Claude Code
per CLAUDE.md); repair the dangling `§` references and the invented quote in
the two PRD skills; document `active_prd.txt`'s convention explicitly
("written by the agent at PRD approval; absent ⇒ protected paths fail closed
— expected in fresh containers").

The standing rule (one sentence in PRD_PROCESS): **a PRD that changes a
process rule greps the rule's tokens across `.claude/`, `scripts/`, `docs/`
and adds every surface that encodes the rule to FILES** — the existing
pre-implementation sweep discipline, applied to process PRDs. This is what
would have made PRD-232 unnecessary (the 229→232 lag) and would have caught
ledger items 3, 4, 6, 7 at their source.

## P7 — The do-nothing list (explicit non-actions)

- **No new hooks, no CODEOWNERS (yet), no sub-agents.** PRD-186 R4's
  CODEOWNERS hardening stays parked: solo repo, every merge is already
  Dustin. Sub-agent absence is correct per the non-goal; the delegation-seam
  mitigations already landed (re-verification, full-suite-at-scoping) are
  sufficient — enforce them, don't automate them.
- **Close the phantom-SHA debt as WONTFIX-historical.** Update the count
  (29 PRDs / 35+ hashes), then declare the item closed: the #NNN convention
  ended the class going forward; back-repairing squash-orphaned SHAs buys
  nothing. A standing "triage later" item that only ever grows is sediment.
- **No PROJECT_STATE generator, no doc-generation pipeline, no new
  synchronized store of any kind.** Every loop in this audit traces to a
  synchronized surface; the fix direction is fewer, never more.
- **Don't reflexively re-run this audit on a cadence.** PRD-230 already
  learned this: five cadence runs, zero findings. Phase-boundary trigger only.

## Sequencing suggestion

1. P2-immediate (bookkeeping commit — kills the live self-contradiction).
2. P1 decision (Dustin) → its doc rewrite carries P6's rule line and the
   Review Dispatch fix in the same MANUAL-MERGE-ONLY PR.
3. P3 + P4 (two subtraction PRDs — both remove live noise).
4. P5 + P6-batch (one polish PR).
5. P7: record the WONTFIX and non-actions in DECISIONS.md.

Expected effect, stated falsifiably: after 1–4, the per-PRD overhead surface
drops from 7 touched stores to 5 (registry, index, PRD doc, review artifact,
DECISIONS-when-warranted), the waiver ritual disappears from HIGH-RISK
closes, `prd_eval` misfires go to zero by construction, and the next
phase-boundary alignment check should find no NEW entries in the drift-ledger
classes fixed here. If it does, the Loop-3 rule (P6) failed and should be
revisited — that is the one prescription whose effectiveness is uncertain.

---
*Phase 2–3 complete. Verification honesty: two Phase 1 claims were weakened
under adversarial review and are corrected above (census understatement; the
retracted "accelerating" framing). Six hook misfires were observed live and
counted as primary evidence. All delegated findings load-bearing to a
prescription were re-verified at their decisive point (validator run,
prd_eval.sh full read, settings.json, workflows dir, PROJECT_STATE lines).*
