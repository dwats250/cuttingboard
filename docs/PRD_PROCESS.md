# PRD Process

Rules and lifecycle for all PRDs in the cuttingboard decision engine.

---

## Lifecycle States

| State | Meaning |
|-------|---------|
| PROPOSED | Drafted. Not approved for implementation. |
| IN PROGRESS | File exists in prd_history/. Implementation has begun. |
| COMPLETE | Implementation merged, or closeout is folded into the implementation PR (PRD-229) and becomes true at merge. Commit cell records the squash SHA (historical / post-merge closeouts) or the PR number `#NNN` (same-PR closeouts). |
| PATCH | Corrective PRD targeting a specific defect in a prior PRD. |
| DEPRECATED | Requirement superseded or withdrawn before completion. |

No other status values are permitted in PRD_REGISTRY.md.

---

## Rules

### File Existence
A PRD is not active until a file exists at `docs/prd_history/PRD-NNN.md`.
Create the file with status `IN PROGRESS` before writing any implementation code.

### Template
All PRDs MUST be created from `docs/PRD_TEMPLATE.md`.
Section names and order MUST NOT deviate:
`GOAL → SCOPE → OUT OF SCOPE → FILES → REQUIREMENTS → DATA FLOW → FAIL CONDITIONS → VALIDATION`

### Scope Compression

Keep PRDs under 100 lines total. To stay within that limit:

- Write one `FAIL:` line per requirement, not multiple. If a requirement needs more than one FAIL line, split the requirement.
- `OUT OF SCOPE` and `FAIL CONDITIONS` sections must not repeat each other. OUT OF SCOPE states what won't be built; FAIL CONDITIONS state what breaks the build. Do not copy the same point into both.
- `VALIDATION` steps are acceptance criteria, not a third restatement of requirements. Write steps only, not explanations.
- `DATA FLOW` should be one short paragraph or a numbered list under 6 items. Not prose.

If a draft exceeds 100 lines, identify which FAIL lines restate the requirement body and remove the duplicates before implementation starts.

---

### Per-Requirement Fail Conditions
Every requirement (R1, R2, ...) MUST include an inline `FAIL:` line.
FAIL lines MUST be:
- Observable — a human or script can confirm it
- Binary — pass or fail, no partial states
- Non-subjective — no words like "unclear", "poor", or "insufficient"

### Scope Lock
The `FILES` section defines a hard boundary.
Any file modified during implementation that does not appear in `FILES` is a scope violation.
Scope violations require either a PRD amendment (add the file to FILES before touching it) or a separate PRD.

Registry and index bookkeeping (`docs/PRD_REGISTRY.md`, `docs/prd_index.json`) is implicit in every PRD lifecycle and is not enumerated in PRD `FILES` sections. Cross-reviewers should treat edits to these two files as authorized by the registry-maintenance step below, not as scope violations.

### Registry Maintenance
1. Add a row to `PRD_REGISTRY.md` with status `IN PROGRESS` before implementation begins.
2. Before merge, in the implementation PR: once the PR is open (its number now exists), push the closeout commit into it — status `COMPLETE`, PR number (`#NNN`) in the commit cell (see Same-PR Closeout below). Work merged by hand outside a normal PR flow may record the merge SHA post-merge instead.
3. The `File` column MUST link to the prd_history file. Rows without a file show `—`.

### Same-PR Closeout (PRD-229)

Closeout bookkeeping — the registry `COMPLETE` flip, `prd_index.json`
counters, `PROJECT_STATE.md` refresh, and the PRD doc's trailing `STATUS`
marker — lands **in the same PR as the implementation**. The separate
post-merge closeout commit/PR is retired: it doubled commit volume (~19%
of visible commits) and generated the sequencing-gate noise of the
prd_eval detectors since retired by PRD-243.

Because a squash-merge SHA does not exist until merge, the commit cell
records the **PR number** (`#NNN`). PR numbers are stable, survive
squash-merges, and resolve on GitHub — recording them also ends the
phantom-SHA class (29 PRDs' historical COMPLETE hashes are unreachable from
`main`; closed WONTFIX-historical by PRD-243 — see PROJECT_STATE known
debt). `tools/validate_prd_registry.py`
accepts `#NNN` tokens in commit cells and exempts them from
git-resolvability; hex SHAs remain valid for historical rows and for
hand-merged work closed out after merge.

Trigger: every PRD closed after PRD-229 merges. Historical rows are not
rewritten.

---

## Patch PRD Rules

A PATCH PRD corrects a defect in a prior PRD's implementation.
Every PATCH PRD file MUST include a `ROOT CAUSE` section identifying exactly one of:
- `missing fail condition` — the original PRD had no FAIL line covering this case
- `ambiguous requirement` — the requirement text permitted multiple interpretations
- `hidden dependency` — an undocumented external constraint was violated

If a single PRD accumulates more than one PATCH PRD, the root causes MUST be documented and reviewed before the next PRD in sequence begins.

---

## Starting a New PRD

1. Copy `docs/PRD_TEMPLATE.md` to `docs/prd_history/PRD-NNN.md`
2. Set status to `IN PROGRESS`
3. Add registry row with `IN PROGRESS` and file link
4. Fill all sections before writing any implementation code
5. Write FAIL lines before writing requirement bodies
6. Before merge, in the implementation PR: push the closeout commit (status `COMPLETE`, PR number `#NNN`) into the open PR (Same-PR Closeout above)

---

## Review Dispatch

Every PRD receives the structured Claude review its LANE requires
(LANE matrix below). A second-model review (Codex or another
independent model) runs only when Dustin commissions one — it is an
instrument, never a standing requirement (PRD-242; see Second-Model
Disposition below and the CLAUDE.md gate text). When a commissioned
second-model review runs alongside the Claude review, **the two are
independent and MUST be dispatched in parallel**, not serially. The
author submits the draft once and the two reviewers work
simultaneously against the same artifact.

**Why parallel:** the reviews answer different questions (vision
alignment vs. structural soundness) from non-overlapping models.
Serial dispatch wastes wall-clock time without improving either
review's quality. The PRD-150 review arc (2026-05-22) ran serially
and the second review's findings did not depend on the first.

**Mechanics:**

- Claude Code dispatches both reviews as parallel subagent calls
  (single message, multiple tool invocations) once the PRD draft is
  ready for review.
- Reviewer artifacts land at
  `docs/prd_history/PRD-NNN.review.claude.md` and
  `docs/prd_history/PRD-NNN.review.<model>.md` respectively (the
  Claude slot enforced by the `prd-review-claude` skill).
- If a review materially drives a decision (KILL, REVISE, scope
  cut), link the artifact path in the `docs/DECISIONS.md` entry so
  the audit trail survives — see CLAUDE.md "Working practices".
- Cross-review-of-review (one reviewer reviewing the other's
  output) is by definition serial and exempt from this rule.
- A second-model artifact saved under any name not matching
  `PRD-NNN.review.<model>.md` exactly (e.g. `PRD-NNN.review-notes.md`,
  `PRD-NNN.reviewed.md`) fails `tools/validate_prd_registry.py`'s
  second-model disposition check exactly as if no artifact existed —
  the check globs the literal `PRD-NNN.review.` prefix, nothing looser.
  The Claude-review leg's filename carries no equivalent CI check
  (`prd-review-claude`'s own stage-lock is process, not CI); a misnamed
  Claude review is a discipline failure, not a build-breaking one.

The parallel-dispatch rule does not change *what* either review
does, only *when* they fire relative to each other.

---

## Second-Model Disposition (PRD-242)

A COMPLETE HIGH-RISK PRD numbered >= 242 MUST carry exactly one of:

1. A commissioned second-model artifact
   `docs/prd_history/PRD-NNN.review.<model>.md` meeting the four
   artifact properties in the CLAUDE.md gate text (in-tree +
   durable, SHA-pinned, read-only, fresh-context); or
2. The disposition line, verbatim, in the PRD doc:
   `SECOND-MODEL: instrument not commissioned, merging on Claude-review + human judgment.`

`tools/validate_prd_registry.py` enforces this on the CI merge path:
a HIGH-RISK close carrying neither fails the required `test` check.
The waiver is a positive act written into the PRD by the merger,
never a silence — this closes the gate-skip class (PRD-240 merged
while its own review artifact said the second leg was still owed).
Historical rows (< 242) are exempt and are not rewritten.

Good reasons to commission a second-model review (the old automatic
triggers, now advisory): contract or decision-surface changes,
dashboard/notification semantics shifts, CI/hooks/artifact-push
semantics shifts, and any reviewer disagreement worth arbitrating.

---

## Governance Compression Principle

Governance must minimize reviewer cognitive load while maximizing drift
resistance. Any governance field that becomes routinely repetitive,
mechanically inferable, or cargo-culted MUST migrate from per-PRD
declaration into process-level convention (the CLASS matrix below).
Author assertions are reserved for decisions that cannot be inferred
from CLASS, FILES, or existing governance docs. This rule is
prospective only; existing template fields are not retroactively
trimmed.

**Inference-first gate:** Any future proposal to add a per-PRD
mandatory field MUST first justify, in the proposing PRD, why the
field cannot be inferred from CLASS, FILES, or the matrix.

---

## PRD Classification

Every PRD declares a `CLASS` from the closed base set:

| Class | Purpose |
|-------|---------|
| GOVERNANCE | Process, template, registry, or workflow doc changes |
| SIDECAR | New or modified observation/research artifact downstream of finalize |
| CONSUMER | Read-only consumers of finalized artifacts (dashboard, notifications) |
| EXECUTION | Decision logic, qualification, regime, sizing |
| CONTRACT | Payload schema, artifact contracts, cross-module shape definitions |
| INFRA | CI, hooks, artifact-push plumbing, scripts, settings |

**PATCH overlay:** Applies on top of any base class. Adds a `ROOT CAUSE`
field with exactly one of: `missing fail condition`, `ambiguous
requirement`, `hidden dependency`. PATCH is not a peer class. Reviewer
set = the base class's reviewer set; no surfaces unlocked beyond the
original PRD's FILES.

---

## Stability Tiers (Reviewer Guidance, Process-Level)

Tiers are used by reviewers to confirm CLASS placement. They are NOT a
mandatory header field.

| Tier | Meaning |
|------|---------|
| T0 | Core contracts and runtime decision pipeline |
| T1 | Sidecars, evaluation, ingestion-adjacent helpers |
| T2 | Consumers (dashboard, notifications, downstream views) |
| T3 | Docs, tests, process artifacts |

Default tier per CLASS (see CLASS Matrix below) is authoritative. A
reviewer may override the default tier ONLY in the review artifact, and
the override MUST be tagged `factual drift` per the failure taxonomy.

---

## CLASS Matrix

For each base class, the matrix specifies: default stability tier,
required reviewers, validation depth, forbidden mutation surfaces, and
HIGH-RISK FILES. Reviewers apply this matrix; authors do not repeat
these fields in PRDs.

| CLASS | Default tier | Required reviewers | Validation depth | Forbidden mutation surfaces | HIGH-RISK FILES |
|-------|--------------|--------------------|------------------|------------------------------|-----------------|
| GOVERNANCE | T3 | Claude; second-model iff commissioned (PRD-242) | Doc cross-check; throwaway skeleton draft | Production modules, tests, fixtures, payloads, dashboard, notifications — EXCEPT the red test that must accompany a governance enforcement-tooling change (PRD-198 invariant 4; declare it in CHANGE SURFACE) | `docs/PRD_TEMPLATE.md`, `docs/PRD_PROCESS.md`, `docs/PRD_MICRO_TEMPLATE.md`, `CLAUDE.md`, `docs/PRD_REGISTRY.md`, `docs/PROJECT_STATE.md` |
| SIDECAR | T1 | Claude required; second-model iff commissioned | Targeted tests on writer/reader; artifact path + schema check | `cuttingboard/runtime.py` decision logic; `cuttingboard/output.py` payload writer; decision-bearing sections of `cuttingboard/delivery/dashboard_renderer.py` | `cuttingboard/trend_structure.py`, `cuttingboard/evaluation.py`, any new `cuttingboard/<name>_sidecar.py` |
| CONSUMER | T2 | Claude required; second-model iff commissioned | Manual UI/notification render; targeted tests on consumer path | Decision logic, regime engine, qualification, payload writers | `cuttingboard/delivery/dashboard_renderer.py`, `cuttingboard/notifications/formatter.py`, `ui/dashboard.html`, `ui/index.html`, `ui/app.js` |
| EXECUTION | T0 | Claude required; second-model iff commissioned | Full pytest suite; targeted regression on regime/qualification/sizing | Sidecar mutation, renderer-derived semantics, payload schema redefinition | `cuttingboard/runtime.py`, `cuttingboard/qualification.py`, `cuttingboard/execution_policy.py`, `cuttingboard/regime.py`, `cuttingboard/trade_decision.py`, `cuttingboard/trade_policy.py` |
| CONTRACT | T0 | Claude required; **adjudication artifact mandatory on any reviewer disagreement**; second-model iff commissioned | Full suite; schema-diff review; full consumer audit | Silent fallback, partial malformed recovery, threshold→label synthesis | `cuttingboard/output.py`, payload-shape definitions, `ui/contract.json`, any module defining `TradeDecision` shape |
| INFRA | T1 (T0 if hooks/CI gate runtime) | Claude required; second-model iff commissioned | Hook/CI dry-run; artifact-push rebase contract check | Runtime decision modules, payload writers, dashboard sections | `scripts/pre_push_check.sh`, `scripts/clean_generated_artifacts.sh`, `.github/workflows/**`, `.claude/**` hooks/settings, `cuttingboard/notifications/state.py` |

---

## LANE Axis

Per PRD-121: every PRD authored after PRD-121's merge commit MUST
declare a `LANE:` value in its header alongside `STATUS:`. Lane is a
coarse ceremony axis that sits on top of the existing CLASS Matrix —
it captures *how much process is required*, not *what change surface
is being touched*. Lane is orthogonal to CLASS and Tier and does not
replace either.

### Lane values and eligibility

| LANE | Eligibility filter | Typical example |
|------|--------------------|------------------|
| MICRO | All micro-PRD criteria in `docs/PRD_MICRO_TEMPLATE.md` hold (docs-only / test-helper-only / process-only, ≤ 20 production-code lines, no HIGH-RISK FILES intersect, one deterministic FAIL condition) AND the R12 safety-net behavior surfaces are NOT touched | A typo fix, a docs cross-link |
| STANDARD | Does NOT qualify for MICRO; `FILES` list does NOT intersect any HIGH-RISK FILES entry in the CLASS Matrix row for the PRD's CLASS | A renderer-only sidecar feature, a notification-formatter tweak, a docs/process expansion that touches several files |
| HIGH-RISK | `FILES` intersects any HIGH-RISK FILES entry in the CLASS Matrix row for the PRD's CLASS, OR CLASS is `EXECUTION` or `CONTRACT`, OR default Tier is T0 | A regime-input change, a payload schema migration, a publish-gate hardening |

### Lane intensity

Required review intensity per lane. Lane intensity is **additive** to
the existing CLASS Matrix `Required reviewers` column — it does not
override or replace it. A `HIGH-RISK CONTRACT` PRD inherits the
CONTRACT row's `adjudication artifact mandatory on any reviewer
disagreement` requirement AND the HIGH-RISK lane's
fresh-context-or-different-model requirement.

| LANE | Structured Claude review | Review Independence | Second-model review (PRD-242) |
|------|--------------------------|---------------------|-------------------------------|
| MICRO | Optional | `same-context` acceptable | Only if commissioned |
| STANDARD | Required | `same-context` acceptable | Only if commissioned |
| HIGH-RISK | Required | `same-context` INSUFFICIENT; must be `fresh-context` OR `different-model` | If commissioned: artifact per the CLAUDE.md properties. If not: the `SECOND-MODEL:` disposition line is mandatory (Second-Model Disposition above) |

### Lane Downgrade Prohibition (PRD-121 R11)

A PRD whose `FILES` list intersects any HIGH-RISK FILES entry for
its CLASS, OR whose CLASS is `EXECUTION` or `CONTRACT`, OR whose
default Tier is T0, MUST declare `LANE: HIGH-RISK`. Authors and
reviewers cannot select MICRO or STANDARD for such changes
regardless of diff size. Lane is a ceremony axis; it cannot be used
to bypass the review intensity required by the existing CLASS
Matrix.

### MICRO Eligibility Safety Net (PRD-121 R12)

`LANE: MICRO` is invalid if the change alters any of the following,
even when the diff is ≤ 20 production-code lines:

- Executable trading-decision behavior (regime classification,
  qualification gates, sizing, posture, contract assembly).
- Artifact contracts or payload / market_map / run schemas.
- Publication gates (`validate_coherent_publish`, freshness windows,
  coherent-generation checks, mixed-artifact gating).
- Runtime artifact write ordering.
- Dashboard truth semantics (renderer-derived decision-bearing
  values, threshold-to-label synthesis, source-health classification,
  lineage classification).
- Notification truth semantics (block reason, decision label,
  artifact correlation).

This rule is additive to the existing
`docs/PRD_MICRO_TEMPLATE.md` eligibility criteria. The criteria
above enumerate the specific *behavior surfaces* that disqualify a
change from MICRO; the line-count and file-scope criteria in the
micro template remain in force.

### Cosmetic Carve-Out (PRD-229)

A change is **cosmetic** iff it touches ONLY:

- ui-rendering copy (label/heading/help text strings), CSS, or
  layout/markup structure in presentation code, and/or
- comments or docstrings (zero executable-line delta) in any module,

AND alters none of the R12 behavior surfaces above. Decision-bearing
values, threshold→label synthesis, source-health/lineage classification,
and every other R12 surface disqualify a change from "cosmetic" no matter
how small the diff — R12 is the hard filter and is unchanged by this
carve-out.

For cosmetic changes only:

- **The Lane Downgrade Prohibition (R11) does not apply** — neither its
  HIGH-RISK-FILES-intersection trigger nor its CLASS trigger. A pure CSS
  tweak in `dashboard_renderer.py`, or a docstring fix in
  `qualification.py`, is MICRO-eligible. (Trigger for this rule: twelve
  cosmetic PRDs paid full HIGH-RISK ceremony in two days, 2026-07-01/02.)
- **Ceremony is at most a 10-line MICRO note** — GOAL, FILES, one FAIL
  line. The full template is not used; review intensity is the MICRO row.
- **Cosmetics batch.** Nits accumulate in a running list and land as at
  most **one polish PRD per week**, one description line each. A lone
  urgent cosmetic fix may land alone and counts as that week's polish PRD.

If any file in the diff carries a non-cosmetic hunk, the whole change is
non-cosmetic: classify by the full R11/R12 rules.

### Retroactive application

PRD-001 through PRD-120 are NOT amended. Lane declaration is
required for every PRD whose draft commit lands strictly after
PRD-121's merge commit. PRD-121 itself declares `LANE: MICRO` as
the eligibility proof-of-concept.

---

## CHANGE SURFACE Trigger

The optional `CHANGE SURFACE` section in `docs/PRD_TEMPLATE.md` becomes
**mandatory** iff at least one of the following holds:

1. The PRD's CLASS default stability tier is T0 or T1.
2. Any entry in the PRD's `FILES` section matches the HIGH-RISK FILES
   column for the PRD's CLASS in the matrix above.

For T2/T3 PRDs whose FILES do not intersect HIGH-RISK FILES, CHANGE
SURFACE remains optional.

---

## Binding MAX EXPECTED DELTA

`MAX EXPECTED DELTA` declared in the PRD header is binding. An
implementation that exceeds the declared ceiling MUST:

1. Stop implementation.
2. Amend the PRD: revise the ceiling and record the reason for the revision.
3. Re-trigger review per the CLASS matrix before resuming.

Advisory interpretation is not permitted. The ceiling is the unit of
drift visibility.

---

## Adjudication Trigger

- **CONTRACT-class PRDs:** Any reviewer disagreement REQUIRES an
  adjudication artifact (`PRD-NNN.adjudication.md`), regardless of
  whether the disagreement is later resolved.
- **All other classes:** adjudication artifact is required only when
  unresolved disagreement remains after review iteration.

This stricter rule for CONTRACT reflects its highest-blast-radius
position in the matrix (T0, full consumer audit, schema-diff review).

---

## Forbidden Patterns Catalog

PRDs MUST NOT introduce any of the following. Reviewers tag violations
using the matching label from the Review Failure Taxonomy.

| Pattern | One-line definition |
|---------|--------------------|
| hidden coupling | Cross-module data flow not declared in imports or `docs/artifact_flow_map.md` |
| payload mutation | Modifying a payload after the contract has finalized it |
| renderer-derived semantics | Computing decision-bearing values inside a presentation layer |
| threshold→label synthesis | Producing a categorical label inside a renderer from numeric thresholds owned upstream |
| wall-clock dependence | Decision logic whose output depends on the current wall-clock time at run |
| partial malformed recovery | Silently repairing or partially accepting malformed inputs instead of failing loudly |
| silent fallback | Substituting a default value when validation fails, without explicit logging |
| sidecar mutation | A sidecar writing back into pipeline state, payloads, or upstream modules |
| while-we're-here mutations | Edits outside the PRD's `FILES` boundary made opportunistically during implementation |

---

## Review Failure Taxonomy

Findings in `*.review.*.md` artifacts MUST be tagged with one of the
following labels:

| Label | Meaning |
|-------|---------|
| hidden coupling | Undeclared cross-module dependency |
| schema ambiguity | Payload/artifact shape admits multiple interpretations |
| consumer contamination | Consumer logic leaking into producer or contract layer |
| ownership violation | Module mutates state owned by another module |
| non-determinism | Output depends on inputs not declared in the PRD |
| derived semantics | Semantics computed in the wrong layer (e.g. renderer derivation) |
| stale-data ambiguity | Freshness contract is unclear or unenforced |
| scope creep | Edits or requirements expand beyond the PRD's stated boundary |
| factual drift | A claim, reference, or default in the PRD diverges from current repo state |
