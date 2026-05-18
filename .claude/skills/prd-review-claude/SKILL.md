---
name: prd-review-claude
description: Use when authoring an independent Claude review of a PRD or a Codex review (cross-review-of-review). Generates a structured review artifact at docs/prd_history/PRD-NNN.review.claude.md with VERDICT, REQUIRED EDITS, RECOMMENDED EDITS, RATIONALE. Verifies every cited line number is current, every named symbol exists, every REQUIRED EDIT is observable, and the output is written to the Claude slot — never the Codex slot. Triggers on "review PRD-NNN", "do the Claude cross-review", "review the Codex review for NNN".
---

# Claude PRD Review with Built-in Verification

## Scope and boundary

This skill does two things and only two things:

1. **Generate** an independent Claude review of a PRD (and optionally
   of a prior Codex review of that PRD).
2. **Verify** every line number, symbol, and file path in the review
   resolves against the current repo state.

It is NOT a substitute for:

- Authoring the PRD (use `prd-authoring-verified`)
- Implementing the PRD
- The cross-review gate's *decision* to invoke Codex — that is the
  human's call per `CLAUDE.md § Cross-review gate`. This skill only
  produces the Claude side of the artifact pair.
- Adjudication when Claude and Codex disagree — that is a separate
  artifact (`PRD-NNN.adjudication.md`) and out of scope here.

## When to trigger

- "Review PRD-NNN"
- "Do the Claude cross-review for PRD-NNN"
- "Review the Codex review for PRD-NNN"
- "Independent review of PRD-NNN"

Do NOT trigger for:
- PRDs in PROPOSED state without an implementation diff if the user
  wants an *implementation* review. The skill reviews the PRD
  document; if an implementation exists, the skill reviews against
  the PRD's stated FILES + REQUIREMENTS, not the code quality.
- Writing the Codex review artifact. The Codex slot
  (`PRD-NNN.review.codex.md`) is stage-locked per
  `project_codex_review_filename.md` memory.

## Operating modes

Default is **DRAFT_ONLY**.

- **DRAFT_ONLY** — emit the review and Verification Report in the
  response. Do not write a file.
- **WRITE_MODE** — write to `docs/prd_history/PRD-NNN.review.claude.md`.
  Refuse if that path already exists; the user can supply
  `.review.claude.v2.md` etc. explicitly if iterating, but the skill
  never overwrites without an explicit target.

If unclear, ask once, then default to DRAFT_ONLY.

## Inputs required

- `prd` — three-digit PRD number
- `mode` — `independent` (Claude is first reviewer) OR `cross-review`
  (a prior Codex review exists and Claude reviews both PRD and Codex
  review)
- `target_path` (WRITE_MODE only, optional) — defaults to
  `docs/prd_history/PRD-NNN.review.claude.md`. The skill validates the
  path is in the Claude slot pattern; refuses anything matching the
  Codex slot.
- `full_codex_coverage` (cross-review mode only, optional, default
  false) — if true, the review must address every Codex finding
  (REQUIRED and recommended). Default is REQUIRED-only.

## Hard rule: no invented references

The skill must never invent:

- Line numbers in the PRD or any cited source file
- Symbol names, function names, file paths
- Codex review findings (only quote / reference what actually exists
  in `PRD-NNN.review.codex.md`)
- A VERDICT not chosen from the fixed set below

If a cited line cannot be confirmed, either remove the citation or
tag the surrounding finding `[UNVERIFIED]` and surface it in the
Verification Report under V1. Same fallback chain as
`prd-authoring-verified`.

## Stage-locked file paths

Two paths are stage-locked and the skill enforces them:

- `docs/prd_history/PRD-NNN.review.claude.md` — Claude review slot.
  This is the only path the skill is permitted to write.
- `docs/prd_history/PRD-NNN.review.codex.md` — Codex slot, owned by
  the cross-review-gate hook (per
  `project_codex_review_filename.md` memory). The skill refuses to
  write here even if explicitly asked.

If WRITE_MODE target resolves to anything other than a path matching
`PRD-<NNN>\.review\.claude(\.v\d+)?\.md`, refuse.

## Review structure

Every review the skill produces has these sections in this order:

```
# PRD-NNN Claude Review

VERDICT
<one of: ACCEPT | ACCEPT WITH CHANGES | REJECT>

SUMMARY
<2-4 sentences: what the PRD is, what is right, what is wrong>

REQUIRED EDITS
<numbered list; each cites exact PRD line or file:line; each ends
with an observable FAIL-style criterion>

RECOMMENDED EDITS
<numbered list; same format; non-blocking>

RATIONALE
<bullets explaining why each REQUIRED edit is required, anchored to
CLAUDE.md, PRD process docs, or existing repo invariants>

CROSS-REVIEW NOTES (cross-review mode only)
<For each Codex REQUIRED finding: AGREE / DISAGREE / EXTEND, with
one-line justification. No silent omissions of REQUIRED findings.
Optional/recommended Codex notes need not be addressed unless they
are load-bearing or the user supplied `full_codex_coverage: true`.>
```

## Two-phase contract

### Phase 1 — Generate

1. Read `docs/prd_history/PRD-NNN.md`.
2. In cross-review mode: read `PRD-NNN.review.codex.md`. Refuse if
   missing — there is nothing to cross-review.
3. If implementation has started (registry status `IN PROGRESS` or
   `COMPLETE`), read the implementation diff. The review still
   targets the PRD document; the diff is *context*, not the subject.
4. Compose the review in the structure above.
5. Each REQUIRED EDIT must:
   - Quote or reference an exact PRD line (`PRD-NNN.md:LL`)
   - State an observable, binary FAIL criterion
   - Map to a CLAUDE.md rule, PRD-process rule, or existing repo
     invariant (cite it)

### Phase 2 — Verify (MANDATORY before returning)

| # | Check | Action on failure |
|---|---|---|
| V1 | Every cited PRD line number resolves to a current line in PRD-NNN.md | Correct the citation or remove the finding |
| V2 | Every cited symbol/file/function exists in the repo | Tag `[UNVERIFIED]` or remove |
| V3 | VERDICT is one of `ACCEPT`, `ACCEPT WITH CHANGES`, `REJECT` | Rewrite |
| V4 | Each REQUIRED EDIT has an observable FAIL line (binary; no "should/appropriate/reasonable/as needed") | Rewrite |
| V5 | In cross-review mode: every Codex **REQUIRED** finding appears in CROSS-REVIEW NOTES with AGREE / DISAGREE / EXTEND. Optional/recommended Codex notes are not required to be addressed unless `full_codex_coverage: true` or the reviewer judges them load-bearing. | Add missing entries for REQUIRED findings |
| V6 | WRITE_MODE target path matches `PRD-<NNN>\.review\.claude(\.v\d+)?\.md` | Refuse |
| V7 | WRITE_MODE target path does not exist (no silent overwrite) | Refuse; ask user for explicit versioned path |
| V8 | No "TODO", "FIXME", "PLACEHOLDER", or "TBD" tokens in the review body | Rewrite |
| V9 | If implementation diff was consulted, the review does not assert "implementation passes/fails" — implementation review is a separate concern | Rephrase to PRD-doc focus |

### Verification Report shape

```
## Verification Report
- V1 PRD line citations: [N checked, all resolve | <list of broken>]
- V2 symbols/paths verified: [list] — UNVERIFIED: [list or none]
- V3 VERDICT: [ACCEPT | ACCEPT WITH CHANGES | REJECT]
- V4 FAIL-line lint: [pass | rewrote items: <list>]
- V5 Codex REQUIRED coverage (cross-review mode): [N/N REQUIRED addressed | missing: <list>] — full_codex_coverage: [false | true]
- V6 target path matches Claude slot: [pass | refused — wrong slot]
- V7 target path free: [pass | refused — exists]
- V8 placeholder tokens: [none | <list>]
- V9 PRD-doc focus preserved: [pass | rephrased item N]
- Mode: [DRAFT_ONLY | WRITE_MODE]
- File written: [path | none]
```

## Tools

**Required:**
- `Read`, `Grep`, `Bash`
- `Write` (WRITE_MODE only)

**Preferred:**
- `gitnexus_context` for V2 symbol verification
- `docs/SCHEMA_MAP.md`, `docs/CALL_SITE_MAP.md` for fast fallback

**Optional:**
- `Agent(subagent_type: "Explore", model: "haiku")` for V2 when the
  review cites many symbols across the tree

## What this skill does NOT do

- Does not write to the Codex slot. Stage-locked.
- Does not overwrite an existing Claude review. The user iterates by
  asking for `.v2`, `.v3` explicitly.
- Does not produce an adjudication artifact. Disagreements that cannot
  be resolved in CROSS-REVIEW NOTES escalate to a separate
  `PRD-NNN.adjudication.md` which this skill does not author.
- Does not invoke Codex. The cross-review gate is a human decision.
- Does not run the test suite or assert implementation correctness.
- Does not update `PRD_REGISTRY.md`. Review artifacts do not get
  registry rows (per `CLAUDE.md § Review artifact discipline`).
- Does not force-address optional/recommended Codex notes. REQUIRED
  Codex findings are mandatory; the rest are judgment calls.

## Failure modes to refuse

- PRD-NNN.md not found: refuse.
- Cross-review mode requested but no Codex review file exists: refuse.
- Target path matches the Codex slot: refuse.
- Target path already exists (WRITE_MODE): refuse; require explicit
  `.vN` suffix.
- User asks to skip Phase 2: refuse.
- User asks the skill to also write the adjudication: refuse; separate
  artifact, separate decision.
- User asks the skill to register the review in `PRD_REGISTRY.md`:
  refuse; reviews are not PRDs.
