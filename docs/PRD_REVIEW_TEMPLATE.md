# PRD Review Template

Canonical structure for both Claude-authored and Codex-authored PRD reviews.
Lives at `docs/prd_history/PRD-NNN.review.<reviewer>.md`.

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
