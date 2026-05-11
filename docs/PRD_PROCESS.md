# PRD Process

Rules and lifecycle for all PRDs in the cuttingboard decision engine.

---

## Lifecycle States

| State | Meaning |
|-------|---------|
| PROPOSED | Drafted. Not approved for implementation. |
| IN PROGRESS | File exists in prd_history/. Implementation has begun. |
| COMPLETE | Implementation merged. Commit hash recorded in registry. |
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

### Registry Maintenance
1. Add a row to `PRD_REGISTRY.md` with status `IN PROGRESS` before implementation begins.
2. After merge: set status to `COMPLETE` and record the commit hash.
3. The `File` column MUST link to the prd_history file. Rows without a file show `—`.

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
6. After merge: update status to `COMPLETE` and record commit hash

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
| GOVERNANCE | T3 | Claude; Codex iff CLAUDE.md cross-review gate triggers | Doc cross-check; throwaway skeleton draft | Production modules, tests, fixtures, payloads, dashboard, notifications | `docs/PRD_TEMPLATE.md`, `docs/PRD_PROCESS.md`, `docs/PRD_MICRO_TEMPLATE.md`, `CLAUDE.md`, `docs/PRD_REGISTRY.md`, `docs/PROJECT_STATE.md` |
| SIDECAR | T1 | Claude + Codex required | Targeted tests on writer/reader; artifact path + schema check | `cuttingboard/runtime.py` decision logic; `cuttingboard/output.py` payload writer; decision-bearing sections of `cuttingboard/delivery/dashboard_renderer.py` | `cuttingboard/trend_structure.py`, `cuttingboard/evaluation.py`, any new `cuttingboard/<name>_sidecar.py` |
| CONSUMER | T2 | Claude required; Codex iff dashboard/notification semantics shift | Manual UI/notification render; targeted tests on consumer path | Decision logic, regime engine, qualification, payload writers | `cuttingboard/delivery/dashboard_renderer.py`, `cuttingboard/notifications/formatter.py`, `ui/dashboard.html`, `ui/index.html`, `ui/app.js` |
| EXECUTION | T0 | Claude + Codex required | Full pytest suite; targeted regression on regime/qualification/sizing | Sidecar mutation, renderer-derived semantics, payload schema redefinition | `cuttingboard/runtime.py`, `cuttingboard/qualification.py`, `cuttingboard/execution_policy.py`, `cuttingboard/regime.py`, `cuttingboard/trade_decision.py`, `cuttingboard/trade_policy.py` |
| CONTRACT | T0 | Claude + Codex required; **adjudication artifact mandatory on any reviewer disagreement** | Full suite; schema-diff review; full consumer audit | Silent fallback, partial malformed recovery, threshold→label synthesis | `cuttingboard/output.py`, payload-shape definitions, `ui/contract.json`, any module defining `TradeDecision` shape |
| INFRA | T1 (T0 if hooks/CI gate runtime) | Claude required; Codex iff CI/hooks/artifact-push semantics shift | Hook/CI dry-run; artifact-push rebase contract check | Runtime decision modules, payload writers, dashboard sections | `scripts/pre_push_check.sh`, `scripts/clean_generated_artifacts.sh`, `.github/workflows/**`, `.claude/**` hooks/settings, `cuttingboard/notifications/state.py` |

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
| MICRO | All micro-PRD criteria in `docs/PRD_MICRO_TEMPLATE.md` hold (docs-only / hook-only / test-helper-only / process-only, ≤ 20 production-code lines, no HIGH-RISK FILES intersect, one deterministic FAIL condition) AND the R12 safety-net behavior surfaces are NOT touched | A typo fix, a registry-gap hook exclusion, a docs cross-link |
| STANDARD | Does NOT qualify for MICRO; `FILES` list does NOT intersect any HIGH-RISK FILES entry in the CLASS Matrix row for the PRD's CLASS | A renderer-only sidecar feature, a notification-formatter tweak, a docs/process expansion that touches several files |
| HIGH-RISK | `FILES` intersects any HIGH-RISK FILES entry in the CLASS Matrix row for the PRD's CLASS, OR CLASS is `EXECUTION` or `CONTRACT`, OR default Tier is T0 | A regime-input change, a payload schema migration, a publish-gate hardening |

### Lane intensity

Required review intensity per lane. Lane intensity is **additive** to
the existing CLASS Matrix `Required reviewers` column — it does not
override or replace it. A `HIGH-RISK CONTRACT` PRD inherits the
CONTRACT row's `Claude + Codex required; adjudication artifact
mandatory on any reviewer disagreement` requirement AND the
HIGH-RISK lane's fresh-context-or-different-model requirement.

| LANE | Structured Claude review | Review Independence | Codex review |
|------|--------------------------|---------------------|--------------|
| MICRO | Optional | `same-context` acceptable | Not required unless CLAUDE.md cross-review gate also triggers |
| STANDARD | Required | `same-context` acceptable | Required when CLAUDE.md cross-review gate triggers (unchanged) |
| HIGH-RISK | Required | `same-context` INSUFFICIENT; must be `fresh-context` OR `different-model` | Required per the CLASS Matrix row; INHERITS the CLASS row's reviewer requirements in addition to the Independence rule |

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
- **All other classes:** Follow the CLAUDE.md cross-review gate —
  adjudication artifact is required only when unresolved disagreement
  remains after review iteration.

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
