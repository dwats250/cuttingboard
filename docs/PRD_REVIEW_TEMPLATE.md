# PRD Review Template

Canonical structure for both Claude-authored and Codex-authored PRD reviews.
Lives at `docs/prd_history/PRD-NNN.review.<reviewer>.md`.

Every review MUST begin with the **Review Independence** attestation
block below (PRD-121 R4). Reviews of PRDs that contain mapping tables
(precedence-ordered classifier rows, gate ordering, state-transition
tables) MUST also include the **Mapping-Table Reachability Checklist**
block (PRD-121 R5).

Filename convention:
- `PRD-NNN.review.claude.md` — Claude-authored independent review.
- `PRD-NNN.review.codex.md` — Codex-authored review-of-review, OR
  Claude-authored review invoked through the `SYSTEM INSTRUCTION — PRD
  REVIEW MODE ACTIVE` hook (filename stage-locked, not model-locked).
- `PRD-NNN.adjudication.md` — only when genuine unresolved disagreement
  requires explicit adjudication.

Per CLAUDE.md `Review artifact discipline`, review files are NOT PRDs and
do NOT get rows in `PRD_REGISTRY.md`.

---

## Required sections (in order)

### 1. Strengths

Bullet list of what the PRD gets right:
- Scope control (FILES list bounded, OUT OF SCOPE explicit).
- Requirement clarity (each Rn has one binary FAIL line).
- Binary FAIL conditions (observable, deterministic, non-subjective).
- Data-flow coherence (DATA FLOW matches REQUIREMENTS).
- Accurate field / module references (verified against actual code).

This is not a generic compliment section. Each bullet must cite a specific
PRD passage or verified codebase reference.

### 2. Cohesiveness

Assess whether `GOAL → SCOPE → REQUIREMENTS → FAIL CONDITIONS → DATA FLOW`
forms a tight, non-contradictory chain. Call out:
- Internal gaps (e.g., a mapping table missing a precedence row).
- Ambiguities (e.g., "first match wins" not stated, or two rows that
  could fire simultaneously without precedence ordering).
- Contradictions (e.g., a FAIL condition that contradicts a REQUIREMENT,
  or an unreachable branch — a precedent row that makes a later row's
  condition impossible to satisfy).

### 3. Critical Problems

For each problem, use this exact format:

```
- **Problem:** [one-sentence statement]
- **Root cause:** [specific cause — wrong field name, missing file,
  undefined behavior, scope violation, unreachable branch, ambiguous
  precedence, etc.]
- **Fix:** [exact change to make to the PRD text or mapping]
```

Cross-check every field name, constant, file path, and module reference
against the actual codebase before listing as correct. Use grep / Read
on `cuttingboard/` and `docs/SCHEMA_MAP.md` / `docs/CALL_SITE_MAP.md`.

If there are no critical problems, state that explicitly under this
heading with one sentence — do not omit the section.

### 4. Revised PRD

A complete, corrected PRD. Same section order as the original
(`GOAL → SCOPE → OUT OF SCOPE → FILES → TERMINOLOGY → MAPPING (if any) →
REQUIREMENTS → DATA FLOW → FAIL CONDITIONS → VALIDATION → COMMIT PLAN →
CODEX REVIEW REQUIREMENT`). All issues from Critical Problems resolved.
Do not add scope beyond what the original intended.

When mapping tables are involved, state precedence explicitly:
"each block evaluates the rows below in order; the first matching row
wins" (or equivalent).

---

## Pre-publish checklist (reviewer must answer "yes" to each)

Before saving the review file:

- [ ] Every PRD-cited symbol (function, class, constant, field path)
      was looked up in the actual codebase or in
      `docs/SCHEMA_MAP.md` / `docs/CALL_SITE_MAP.md` — not assumed from
      memory.
- [ ] Every file path in the PRD's FILES list exists.
- [ ] Every mapping-table row is reachable under the stated precedence
      (no row shadowed by an earlier row that always fires first).
- [ ] Every FAIL condition is observable, deterministic, and binary.
- [ ] Every user-visible string the PRD changes was greped across
      `tests/` to identify regression assertions — per CLAUDE.md
      `Visible-String Pre-Edit Audit`. Surprises become amendments to
      the FILES list before implementation, not scope-lock violations
      mid-implementation.
- [ ] The OUT OF SCOPE list explicitly names every protected symbol
      that prior PRDs introduced and that this PRD relies on as
      read-only intermediates (e.g., `validate_coherent_publish`).
- [ ] Determinism requirements (R-something) name the exact monkeypatch
      targets, not just "freeze the clock".
- [ ] ASCII-only constraint is enforced both in REQUIREMENTS and in a
      VALIDATION step that scans the FILES set.

---

## Token discipline

- Read only the minimum files needed. Use `offset+limit` Read calls
  pointed at the specific function or symbol, not full-file reads.
- A single targeted grep against `cuttingboard/` for each PRD-cited
  symbol is sufficient verification; do not list grep output in the
  review, just confirm the symbol exists.
- Review artifact length budget: ~400 lines. Anything longer means the
  review is duplicating PRD content or producing prose where a bullet
  would suffice.
- Do not re-review previously-accepted findings in a revision pass.
  Mechanical incorporation of accepted findings does not require a new
  full review unless something materially changed (see CLAUDE.md
  § Cross-review gate).

---

## When to skip the Revised PRD section

If no Critical Problems were found AND no improvements to Cohesiveness
are recommended, the Revised PRD section may be replaced by:

```
## Verdict

Approve for implementation. Implementation must stay inside the FILES
allowlist and must not touch the read-only protected symbols in
OUT OF SCOPE.
```

Use this only when the original PRD is genuinely ready as-is.

---

## Review Independence (required, PRD-121 R4)

Place this block at the very top of every review file. Tick exactly
one of the three checkboxes:

```
## Review Independence

- [ ] fresh-context   (separate session; PRD draft text not in context window at review time)
- [ ] different-model (model architecture/vendor different from the PRD draft author)
- [ ] same-context    (same instance, same session as PRD draft — lower independence)
```

Rules:
- Exactly one checkbox MUST be ticked.
- For `LANE: HIGH-RISK` PRDs, `same-context` is INSUFFICIENT — at
  least one of `fresh-context` or `different-model` must be ticked.
  Selecting `same-context` for a HIGH-RISK PRD is a R2/R4 violation
  and blocks merge.
- For `LANE: MICRO` and `LANE: STANDARD` PRDs, `same-context` is
  permitted but MUST be accompanied by a one-line justification (e.g.,
  "Lane MICRO permits same-context review per PRD-121 R2.").

The Independence attestation is the load-bearing artifact for review
honesty. Reviews that omit it are treated as if no review occurred.

---

## Mapping-Table Reachability Checklist (required when PRD contains mapping tables, PRD-121 R5)

A mapping table is any tabular precedence structure inside the PRD
where rows are evaluated in order and the first match wins (source
classification, gate ordering, regime vote matrix, state transitions,
freshness/staleness mapping). For each row of each mapping table the
reviewer MUST confirm all four sub-checks below:

```
## Mapping-Table Reachability Checklist

For each mapping-table row in PRD-NNN:

| Table | Row | (1) raw input or one-step derivation | (2) derivation function if any | (3) precedence order | (4) reachable fixture in R14 (or equivalent) |
|-------|-----|---------------------------------------|--------------------------------|-----------------------|-----------------------------------------------|
| <Block X> | <Row N condition> | <input parameter name> | <fn name or "none"> | <"row 1 wins if A; else row 2 if B; ..."> | <test name where this row is the matching row> |
| ... | ... | ... | ... | ... | ... |
```

Sub-check guarantees:

1. **(1) raw input or one-step derivation**: each row condition is
   expressed in terms of an input parameter (something passed into
   the function under test) or a one-step-derivable predicate from
   inputs (e.g., `payload.meta.timestamp` directly, or
   `_compute_timestamp_freshness(payload.meta.timestamp)`). NOT a
   downstream variable computed from multiple earlier mapping rows.

2. **(2) derivation function if any**: if the row references a
   derived value (e.g., `_ts_records`, `_mm_status`), the derivation
   function is named and verified to be a pure function of inputs,
   not a downstream-state variable that may be set or shadowed by
   an earlier row.

3. **(3) precedence order**: the table's evaluation order is
   explicit ("first match wins", or numbered ordering). The reviewer
   walks down the table top-to-bottom and confirms no row's condition
   is implied by an earlier row's match condition — that is, every
   row has at least one input combination under which it is the
   matching row.

4. **(4) reachable fixture**: at least one named test in the PRD's
   test list (e.g., R14 in PRD-120) constructs inputs that drive
   this row to be the matching row. The test name is cited.

Why this exists: PRD-120's Trend Structure mapping originally listed
`_ts_records is None → MISSING` at precedence position 4 and
`usable_count == 0 → FALLBACK` at position 7. Because
`_trend_structure_records` is all-or-nothing, the row-4 condition
shadowed row 7 — any input that would have produced FALLBACK
produced MISSING instead. The PRD-120 implementation surfaced this
as test failure mid-implementation. The reachability checklist would
have caught it during review at sub-check (1) — the row-4 condition
referenced a derived all-or-nothing variable, not a raw input.

If the PRD contains no mapping tables, the reviewer may state:

```
## Mapping-Table Reachability Checklist

Not applicable — no mapping tables in this PRD.
```

Use this exact line; do not omit the section.
