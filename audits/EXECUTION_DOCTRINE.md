# Execution Doctrine - one slice of work, end to end

**Date:** 2026-07-10 (r3, after operator revisions)
**Status:** CANONICAL - adopted 2026-07-10, merged to main on Dustin's
authorization. Written against
origin/main governance as of PRD-250 (PRD-229 same-PR closeout, PRD-242
second-model disposition, PRD-244 CLAUDE.md refactor, 2026-07-07 merge/review
decisions in docs/DECISIONS.md).

**This is the STANDING execution doctrine.** It governs any single slice of
work - a bug fix, a feature, a config knob, a doc correction, a future PRD of
any shape. `audits/BUILD_PLAN.md` is its first application, not its
definition. It codifies how the operator already works - cuts before
additions, PRD before build, stop-and-report seams between steps, mechanical
bulk retrieval delegated down, every merge held personally - it does not
invent process. Where a rule already lives in CLAUDE.md or
docs/PRD_PROCESS.md, this doctrine cites it and adds only ordering and
ownership.

ASCII-only on purpose: sections of this file get quoted into charges and
clipboards.

---

## Operator environment

How the operator actually works, codified so the two-checkout ambiguity this
doctrine was first drafted under does not recur:

- **asher (local clone over SSH) is the PRIMARY working copy** for the
  current stretch; work happens there directly.
- **The cloud web harness is a SEPARATE checkout.** It and asher meet ONLY
  through origin; neither auto-syncs to the other.
- **FETCH-FIRST RULE (invariant, not a suggestion):** `git fetch origin` at
  the start of every session, review what came in, fast-forward before
  working. Why: cloud sessions push to origin, and asher does not have that
  work until it fetches - skipping the fetch is how a session builds on a
  stale main and manufactures divergence.
- **Remote-control is the bridge** when a cloud session should act on asher
  hands-free.

This is why the deliverables-are-tracked rule (section 4) exists: tracked
files travel through origin to whichever checkout is active. Nothing that
must survive a checkout switch may be gitignored.

---

## 0. Cast and tiering

**Model tier is chosen per SLICE, by risk - not per stage.** The normal case
is ONE agent (the driver) assigned the whole slice, running it end-to-end and
doing its own retrieval, greps, and test runs as it goes. There is no
mandatory fetch->build->review relay inside a slice.

| Actor | Role in a slice |
|---|---|
| **Driver (Sonnet 5 by default)** | Owns the slice end-to-end: recon, authoring, build, verify, closeout. Runs its own greps and targeted tests. Every lane has exactly one driver. |
| **Haiku (optional subcontractor)** | Pulled in ONLY for a genuinely separable bulk job: a large call-site/token sweep, a long full-suite run backgrounded while the driver keeps working. Never a required stage; never edits source. |
| **Operator (Dustin)** | At most two touches per slice: Gate A (direction, when not already decided) and Gate B (merge, always). Everything else runs unattended. |
| **Fresh-context reviewer (heavy Claude model)** | HIGH-RISK only: the fresh-context Claude review leg. |
| **Second model (Codex or other non-Claude)** | HIGH-RISK only, and only when Dustin commissions it (PRD-242). |

Tier by lane: MICRO/STANDARD -> Sonnet runs the whole slice. HIGH-RISK ->
Sonnet still builds end-to-end; what changes is the close: a separate
fresh-context heavy-model review, plus the second-model disposition.

Two-leg precision (PRD-242 + the 2026-07-07 DEFINITIONS entry): a
fresh-context Claude review - however heavy the model - discharges ONLY the
**Claude review leg**. The **second-model leg** requires a committed
non-Claude `docs/prd_history/PRD-NNN.review.<model>.md` OR the verbatim
waiver sentence. `.review.claude.md` never double-counts.

---

## 1. Slice lifecycle

Stages are checkpoints in one driver's run, not handoffs. The full path is
the HIGH-RISK superset; lower lanes SKIP stages outright (section 3).

### CARD - what the slice is
Pull the slice's spec: a build-plan card, a bug report, an operator ask, a
review finding. Confirm any ordering constraints and interaction flags it
declares. Branch `claude/<slug>` (or `claude/prd-NNN-<slug>` once numbered)
from fresh `origin/main`.

### SWEEP - only when the change touches asserted surfaces
Required only when the slice deletes, renames, or re-derives a token that
tests or consumers assert (PRD-158): grep `tests/` for the token, consult
`docs/SCHEMA_MAP.md` / `docs/CALL_SITE_MAP.md`, enumerate downstream
consumers (author discipline 2). The driver does this itself; delegate to
Haiku only when the sweep is genuinely bulk (dozens of files), and then
re-run the ONE decisive `rg` personally before relying on it (discipline 4).
A doc fix or additive change with no asserted-token contact skips this stage.

### STAGE 0 - the PRD scaffold (non-trivial slices only)
`scripts/prd_open.sh --prd NNN --title ... --lane ... --class ... --commit`,
then author the PRD via `prd-authoring-verified`: FAIL lines before
requirement bodies, FILES from the sweep, MAX EXPECTED DELTA, lane per the
PRD_PROCESS matrix (Lane Downgrade Prohibition R11 applies). Trivial changes
within established patterns need no PRD (CLAUDE.md); MICRO uses the micro
template or, for cosmetics, the 10-line note.

### GATE A - direction (only when direction is not already decided)
The operator approves the PRD/approach, or edits/kills it. Gate A is
PRE-SATISFIED when the slice's direction is already operator-decided in a
durable record - an approved plan card, a DECISIONS ruling - and the driver
is executing it faithfully. Whoever gives Gate A (or the commissioning
message, when Gate A is pre-satisfied) names the slice's future PR and
authorizes opening it once green: that is the per-PR confirmation the
2026-07-07 decision requires. For HIGH-RISK, Gate A is also where Dustin
commissions the second model or defaults to the waiver.

### BUILD - red first, then green
Write the proving test; it MUST fail against pre-change code (a proving test
that cannot fail is a halt trigger, not something to paper over). Implement
to green. Run any mutation check the card names. One concern per commit; each
commit green on ruff + targeted tests (section 4).

### VERIFY - once, just before landing
1. `ruff` + the FULL pytest suite (background it - or hand the run to Haiku -
   and keep working).
2. Scope check: committed paths vs the PRD FILES section plus the
   registry-maintenance carve-out. A stray path is a halt, not a cleanup.
CI remains the deciding run (hardening invariant 5); VERIFY exists to avoid
burning a CI round-trip, not to substitute for it.

### REVIEW - by lane
- **MICRO:** nothing beyond VERIFY. No review artifact.
- **STANDARD:** one structured Claude review of the implementation against
  the PRD, same-context acceptable - the driver writes
  `docs/prd_history/PRD-NNN.review.claude.md` (via `prd-review-claude`),
  DRIFT CHECK included.
- **HIGH-RISK:** dispatch the fresh-context reviewer with a clean context (no
  implementation summary, no PR body). Artifact per the 2026-07-07 decision:
  in-tree, pinned to the reviewed SHA, merge base, fresh-context attestation,
  DRIFT CHECK. Plus the second-model disposition in the PRD doc: the
  commissioned non-Claude artifact, or the verbatim line
  `SECOND-MODEL: instrument not commissioned, merging on Claude-review + human judgment.`
  Default is the waiver; do not run a second model un-commissioned.
This is the ONLY review event in the slice (section 6, cut 1). Findings
within FILES and against the PRD: fix in place. Anything else: halt clause.

### LAND - Gate B, always
1. Push the branch; open the PR (authorized at Gate A / commissioning).
2. Push the closeout commit INTO the open PR (PRD-229 same-PR closeout):
   registry COMPLETE with the PR number `#NNN` in the commit cell,
   PROJECT_STATE baseline from the CI summary (PRD-196), index counters
   (`scripts/prd_close.sh` / `prd-closeout-verified`).
3. **The operator merges.** The agent never merges and never queues
   auto-merge (2026-07-07). MICRO/STANDARD: operator queues auto-merge or
   clicks merge; CI `test` is the gate. HIGH-RISK and governance: human-held
   merge - the review artifact and disposition are already in the PR, so it
   is never openable-and-mergeable without its second leg visible.
4. After merge: confirm CI green on `main` (the registry validator already
   enforced bookkeeping consistency - do not re-check by hand); delete
   session scratch (PRD-230). Next slice.

Bot-review threads (PRD-228) arriving on the PR are triaged by the driver -
ACTIONED with the fixing SHA or DISMISSED with a one-line in-thread reason -
and never gate anything.

---

## 2. Failure contract - inherited by reference

This section and section 4 are UNIVERSAL INVARIANTS. Every agent working a
slice inherits them by reference, regardless of model or task - a slice
charge cites this doctrine and does not restate them. Copy the clause
verbatim into a prompt ONLY when the executing agent cannot read the repo.

```
STOP-AND-REPORT CLAUSE (audits/EXECUTION_DOCTRINE.md sec 2)
If any trigger below fires, STOP immediately: no further edits, no commit,
no workaround, no "fixing" the trigger itself. Report exactly three things:
(1) which trigger fired, (2) the evidence - file, command, output - verbatim,
(3) the smallest question whose answer unblocks you.
TRIGGERS:
 T1  The code you find does not match the slice's FILES list or stated
     approach (wrong symbol, moved logic, contradicting comment/doc).
 T2  Completing the task requires touching ANY file not in FILES.
 T3  A doctrine or policy question surfaces that the card, the PRD, and
     CLAUDE.md do not answer.
 T4  The proving test cannot be made to FAIL against pre-change code.
 T5  The change is growing past the card: new files, new dependencies, or
     the PRD's MAX EXPECTED DELTA would be exceeded.
 T6  A hook, permission gate, or CI check blocks an action.
 T7  The full suite shows failures unrelated to your change (baseline
     drift).
 T8  Your sweep contradicts a "nothing else reads/calls this" claim you
     were given.
A partial result with verified evidence is a success. A guessed completion
is a failure.
```

Driver's response to a halt: T1/T3 -> surface to the operator (a judgment
seam; may ride the next batched gate). T2/T5 -> amend the PRD (re-touch
Gate A if the amendment changes direction or lane) or spawn a follow-up per
the amend-vs-spawn bar; never expand FILES silently. T4 -> the card's claim
about current behavior is wrong; back to SWEEP, and the finding goes in the
PRD as a factual-drift note. T6 -> never bypass (`--no-verify`, sandbox
overrides) without operator approval. T7 -> quarantine the slice; fix the
baseline first as its own concern. T8 -> re-run the sweep wider; the claim
is unproven until one decisive `rg` passes.

### The thin charge

A per-slice charge stays THIN - slice, card, lane, nothing else. Everything
procedural is inherited from this doctrine. Example:

```
SLICE CHARGE
Doctrine: audits/EXECUTION_DOCTRINE.md is binding by reference - lifecycle
(sec 1), failure contract (sec 2), commit discipline (sec 4).
Slice: <one line: the change and why>
Card: <path or ref, if any>
Lane: <MICRO|STANDARD|HIGH-RISK>   Class: <CLASS>
Branch: claude/<slug>
PR: authorized on green - this message is the per-PR confirmation.
Constraints: <ordering / interaction flags, only if any>
```

If a charge needs more than this, the missing content belongs in the card or
in this doctrine - not in the charge.

---

## 3. Ceremony tiers - lanes SKIP stages, they don't just thin them

Lane is declared per the PRD_PROCESS matrix and is not negotiable downward
(R11), except the PRD-229 cosmetic carve-out. The per-lane path:

| Lane | Path | Operator touches |
|---|---|---|
| **MICRO** | CARD -> BUILD -> VERIFY -> LAND | 1 (Gate B; commissioning doubles as Gate A + PR authorization) |
| **STANDARD** | CARD -> [SWEEP] -> STAGE 0 -> [GATE A] -> BUILD -> VERIFY -> REVIEW (same-context) -> LAND | 1-2 (Gate A only if direction not pre-decided) |
| **HIGH-RISK** | all stages | 2 (Gate A incl. commission-or-waive; Gate B human-held) |

Bracketed stages fire only on their trigger (SWEEP: asserted-token contact;
GATE A: direction not already decided). MICRO carries its micro note or
10-line cosmetic note inside BUILD's first commit - the note, the red-first
proving change, and the registry row are the whole ceremony.

Overlay: **governance changes** (CLAUDE.md guardrails, `prd-review-claude`,
`tools/validate_prd_registry.py`, this doctrine once canonical) are
MANUAL-MERGE-ONLY regardless of lane.

**Worked MICRO example** - re-add the `.gitnexus/` line the upstream
drop-list removed from `.gitignore`: CARD (the operator's one-line ask) ->
BUILD (micro note + the one-line change + a FAIL condition: `git status
--short` shows `.gitnexus/` untracked pre-change, clean post-change) ->
VERIFY (ruff no-op, suite untouched, scope = 2 files) -> LAND (PR, operator
queues auto-merge). Four stages, one operator touch, zero review artifacts.
The operator's test applies at every lane: "would I actually follow every
stage on this, or route around it?" - a doctrine stage that would get routed
around is a bug in the doctrine, and the fix is skipping it officially.

**Stress test - the budget-cap knob ($150 -> $400,**
`cuttingboard/config.py`, one line): honesty requires flagging that by the
LETTER of current governance this one-liner cannot ride MICRO - it alters
sizing behavior (R12 safety net) and its CLASS is EXECUTION, which forces
LANE: HIGH-RISK via R11 regardless of diff size. The collapsed path this
doctrine gives it: CARD (the decision is already recorded in the approved
plan - Gate A pre-satisfied) -> STAGE 0 (micro-sized PRD, FILES =
`config.py` + the asserting test) -> BUILD (red-first: effective budget
asserts 400) -> VERIFY -> REVIEW (a short fresh-context review + the waiver
sentence) -> LAND (human-held merge). That is the floor current governance
permits. If the operator wants operator-decided constant changes with a
recorded consequence to ride MICRO outright, that is a PRD_PROCESS amendment
(a knob carve-out parallel to the cosmetic carve-out) - to commission
separately, not something this doctrine can grant (section 7: PRD_PROCESS
wins).

**Noted, not queued - knob carve-out.** A PRD_PROCESS amendment could grant
a knob carve-out (operator-decided config changes with recorded consequences
ride MICRO), parallel to the cosmetic carve-out. NOT queued - deferred until
recurring knob-friction justifies weakening the R11/R12 sizing-safety guard.
Revisit with real instances.

The bias everywhere: ceremony concentrates where blast radius lives - the
decision path and the guardrails themselves. MICRO and STANDARD run
near-bare because the CI validator, the red-first rule, and Gate B already
catch the real failure classes there.

---

## 4. Commit discipline - inherited by reference

**Branch:** `claude/<slug>` (or `claude/prd-NNN-<slug>`), cut from fresh
`origin/main`.

**Message format:**
- Subject <= 72 chars, imperative, prefixed:
  - `PRD-NNN: stage 0 - <title>` (the STAGE 0 scaffold)
  - `PRD-NNN: <what changed>` (implementation commits)
  - `PRD-NNN: closeout (COMPLETE via #<PR>)` (the LAND bookkeeping commit)
  - Non-PRD housekeeping only: `bookkeeping:` / `decisions:` / `chore:`
- Body: WHY, only when the subject can't carry it. No restating the diff.
- Trailer: the building agent's `Co-Authored-By:` line per the harness.

**One concern per commit.** A commit is one requirement (or one coherent
requirement group) plus the tests that prove it - test and code that make one
FAIL line pass travel together. Never two slices in one commit; never
implementation mixed into the stage-0 or closeout commits. Every commit is
green on ruff + targeted tests, so bisect always lands on a working tree.

**Every commit on a slice branch carries the slice's prefix.** A commit that
can't honestly take the prefix does not belong on the branch - that is T5.

**Staging rules:**
- Explicit paths only: `git add <path> <path>`. Never `git add -A` / `.`.
- Never staged: `logs/*`, `reports/*`, regenerated `ui/dashboard.html` /
  `ui/index.html`, `.claude/state/*`, anything the workflow force-add
  allowlist owns. Runtime droppings in the tree are left alone.
- `docs/PRD_REGISTRY.md` / `docs/prd_index.json` are implicitly authorized
  (PRD_PROCESS scope-lock carve-out) but ride ONLY the stage-0 and closeout
  commits.
- **Deliverables are tracked, never gitignored.** `audits/` is tracked on
  origin/main; every audit/plan/doctrine deliverable commits with a plain
  `git add`. This is load-bearing, not style: the operator works across two
  disconnected checkouts (the asher clone over SSH and the cloud web
  harness), and anything gitignored exists in only one of them and never
  crosses through origin. A deliverable that can't survive a checkout switch
  isn't durable. (A stale local `.gitignore` once claimed `audits/` was
  ignored; that artifact is corrected.) What STAYS committed is governed by
  the PRD-230 sediment rule - session scratch is deleted, never committed.

**Commit-to-slice mapping:** stage 0 (1 commit, when a PRD exists) ->
implementation (1 commit per concern, typically 1-3) -> review artifact when
in-tree (1) -> closeout (1). A typical slice is 3-6 commits, each
independently green; a MICRO can be as few as 2.

---

## 5. Closeout

**Definition of done:**
- **MICRO:** PR merged, CI `test` green, registry row COMPLETE with `#NNN`,
  micro note in-tree.
- **STANDARD:** MICRO + `.review.claude.md` in-tree with DRIFT CHECK.
- **HIGH-RISK:** STANDARD + fresh-context SHA-pinned review artifact +
  second-model disposition (artifact or verbatim waiver in the PRD doc) +
  human-held merge. The CI validator fails the close if either leg is absent.
- **All lanes:** PROJECT_STATE refreshed (baseline from the CI summary, never
  a sandbox count); `docs/DECISIONS.md` entry ONLY if the slice changed
  direction or a review materially drove a decision - closing a planned slice
  as planned is not a decision.

**Artifact of record:** the registry row + the PRD doc's STATUS line. The PR
is the evidence trail; the review artifacts are the review trail. Nothing
else is authoritative.

**Pruned after close:** session scratch and runway notes (PRD-230: delete
once the next session confirms nothing lost); the slice's task-list entries.
A resume note is written ONLY when a slice pauses mid-flight - a completed
slice's state is fully captured by the registry and needs no note.

**When the slice came from a plan or batch:** the source card gets a
one-line `LANDED as PRD-NNN (#PR)` annotation at the batch's phase boundary,
in the same commit as the Alignment-check DECISIONS entry - not per-slice.

---

## 6. Anti-redundancy - double-checks cut by this doctrine

1. **One review event per slice, not two.** Reviewing the PRD draft AND the
   implementation as separate ceremonies is cut: `prd-authoring-verified`
   already mechanically checks the draft (symbols exist, FAIL lines
   observable, lane correct) and Gate A holds direction - the single REVIEW
   stage covers implementation-against-PRD. A separate pre-build PRD review
   is dispatched only if the operator asks at Gate A.
2. **Full suite runs twice, not three-plus times.** Targeted tests per
   commit; ONE full local run at VERIFY; CI is the deciding run (invariant
   5). Never full-suite-per-commit, never a second "confirm" full run after
   review.
3. **Scope is checked mechanically once.** The VERIFY diff-vs-FILES check is
   THE scope verification; the reviewer reads its output and spot-checks
   flagged exceptions; `protect_files.sh` stays a backstop, not a step.
4. **Bookkeeping consistency is CI's job.** `prd_close.sh` writes the
   four-way state; `tools/validate_prd_registry.py` verifies it on the merge
   path. No manual four-way re-read after landing.
5. **Sweep re-verification is one command.** Author discipline 4 requires
   re-running the decisive `rg` - exactly one. Re-running a delegated sweep
   in full duplicates the work the delegation existed to save.
6. **Second-model review is not a default.** PRD-242 demoted it to a
   commissioned instrument; the default HIGH-RISK disposition is the
   verbatim waiver. Running Codex "to be safe" on every decision-path slice
   re-creates the standing gate PRD-242 removed.
7. **No per-slice drift audit.** The review artifact's DRIFT CHECK plus the
   phase-boundary Alignment check are the drift machinery; a third per-slice
   pass would triple-cover the same question.
8. **No per-slice resume notes.** Registry + PR already carry a completed
   slice's state; notes are for mid-flight pauses only (PRD-230).
9. **Delegation is for separability, not ceremony.** A mandatory
   fetch->build->review relay inside every slice pays three context
   spin-ups to do one agent's job. One driver end-to-end is the default;
   subcontract only work that is genuinely bulk and separable, and only the
   review legs that governance requires to be independent.
10. **Charges don't restate the doctrine.** A slice charge is slice + card +
    lane (section 2, "The thin charge"); restating the failure contract or
    commit rules per-charge is drift waiting to happen - the doctrine is the
    single copy.

---

## 7. Adoption

Adopted 2026-07-10: reviewed by Dustin through three revisions (r1-r3) and
merged to main on his explicit authorization. Standing rules: if any clause
here conflicts with CLAUDE.md or docs/PRD_PROCESS.md, those win and this file
gets corrected - it is doctrine ABOUT the process, not a source of truth OVER
it. Changes to this file are governance-adjacent and ride MANUAL-MERGE-ONLY,
per section 3's overlay.
