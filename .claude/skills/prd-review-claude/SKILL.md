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
  human's call per `CLAUDE.md § Review gates` (second-model
  disposition). This skill only produces the Claude side of the
  artifact pair.
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
  `docs/PRD_REVIEW_TEMPLATE.md`'s Filename convention.

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
- `docs/prd_history/PRD-NNN.review.codex.md` — Codex slot, per
  `docs/PRD_REVIEW_TEMPLATE.md`'s Filename convention. The
  `prd_eval.sh` keyword detector that once enforced this hook-side was
  retired by PRD-243 (retired, not fictional — the slot-lock rule
  itself still stands as skill-side discipline, just not hook-enforced
  since). The skill refuses to write here even if explicitly asked.

If WRITE_MODE target resolves to anything other than a path matching
`PRD-<NNN>\.review\.claude(\.v\d+)?\.md`, refuse.

## Review structure

Every review the skill produces has these sections in this order:

```
# PRD-NNN Claude Review

REVIEWED STATE
Reviewed SHA: <commit hash this review targets, verified with `git cat-file -e <sha>^{commit}`>
Merge base: <output of `git merge-base <the same reviewed SHA> origin/main` at review time>
Independence: <fresh-context | different-model | same-context> — <one-line justification>
(This IS `docs/PRD_REVIEW_TEMPLATE.md`'s Review Independence
attestation, per PRD-121 R4 — the canonical block, not a duplicate of
one. That template no longer defines a separate checkbox form.)

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

IMPLEMENTATION VERDICT
<Only when an implementation diff was consulted (registry status `IN
PROGRESS` or `COMPLETE`): per REQUIREMENT (R1, R2, ...), state PASS or
FAIL against its FAIL line, each evidenced by real command/test
output — REVIEW covers implementation-against-PRD
(`audits/EXECUTION_DOCTRINE.md` sec 1), not the PRD document alone.
Omit this section entirely when no implementation diff exists yet.>

DRIFT CHECK
<two lines, always recorded (even when "none"):
- VISION: does the change conflict with a VISION non-goal or principle?
  (no / yes + which non-goal or principle)
- PROJECT_STATE: does the change leave any PROJECT_STATE claim stale?
  (no / yes + which claim)>

CROSS-REVIEW NOTES (cross-review mode only)
<For each Codex REQUIRED finding: AGREE / DISAGREE / EXTEND, with
one-line justification. No silent omissions of REQUIRED findings.
Optional/recommended Codex notes need not be addressed unless they
are load-bearing or the user supplied `full_codex_coverage: true`.>
```

## Two-phase contract

### Phase 1 — Generate

1. Read `docs/prd_history/PRD-NNN.md`.
2. Capture REVIEWED STATE: `git rev-parse HEAD` (or the reviewed
   branch tip, if reviewing a ref other than the checked-out HEAD) for
   the reviewed SHA. Then compute the merge base from THAT SAME SHA —
   `git merge-base <reviewed SHA> origin/main` — never hardcode `HEAD`
   once the reviewed SHA is known, or a review of a non-checked-out ref
   silently pairs one commit's SHA with a different commit's merge
   base. Record the independence line the dispatch specifies.
3. In cross-review mode: read `PRD-NNN.review.codex.md`. Refuse if
   missing — there is nothing to cross-review.
4. If implementation has started (registry status `IN PROGRESS` or
   `COMPLETE`), read the implementation diff and, per REQUIREMENT,
   determine whether it satisfies the requirement's FAIL line — REVIEW
   covers implementation-against-PRD (`audits/EXECUTION_DOCTRINE.md`
   sec 1), not the PRD document alone. Cite the exact command/test
   output evidencing each verdict.
5. Compose the review in the structure above.
6. Each REQUIRED EDIT must:
   - Quote or reference an exact PRD line (`PRD-NNN.md:LL`)
   - State an observable, binary FAIL criterion
   - Map to a CLAUDE.md rule, PRD-process rule, or existing repo
     invariant (cite it)
7. DRIFT CHECK (lightweight, always recorded): read `VISION.md` non-goals /
   principles and the `docs/PROJECT_STATE.md` current-state claims; record
   (i) whether the change conflicts with a VISION non-goal/principle and
   (ii) whether it leaves any PROJECT_STATE claim stale. This is drift, not
   correctness — keep it to the two recorded lines. Per `CLAUDE.md § Review
   gates`, under auto-merge drift-review is a post-merge audit, so this
   recorded check is the standing pre-merge drift signal.

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
| V9 | RETIRED (PRD-255, 2026-07-11) — this number is never reused. Historical `*.review.claude.md` files (e.g. `PRD-254.review.claude.md:14`) cite "V9" describing the pre-PRD-255 prohibition on asserting implementation pass/fail; that citation is immutable evidence of what those reviews asserted at the time and is not reinterpreted by this table | n/a |
| V10 | DRIFT CHECK present: the review records a VISION-conflict line and a PROJECT_STATE-staleness line (each "none" or with specifics) | Add the DRIFT CHECK section |
| V11 | REVIEWED STATE's reviewed SHA resolves to a real commit — `git cat-file -e <sha>^{commit}` (bare `-e <sha>` also passes for blobs/trees and does not prove it is a commit) | Correct the SHA, or refuse if it does not resolve to a commit |
| V12 | REVIEWED STATE's stated merge base equals `git merge-base <the same reviewed SHA> origin/main` computed at review time — not `HEAD` if the reviewed SHA differs from checked-out HEAD, and not asserted from memory | Recompute and correct, or refuse if they diverge |
| V13 | If an implementation diff was consulted, IMPLEMENTATION VERDICT is present and states PASS/FAIL per REQUIREMENT, each evidenced by real command/test output — REVIEW covers implementation-against-PRD, not the PRD document alone | Add the missing verdict(s), evidenced by cited command/test output |

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
- V9: RETIRED (PRD-255) — never reused; see V13
- V10 drift check: [VISION: none | <conflict>; PROJECT_STATE: none | <stale claim>]
- V11 reviewed SHA resolves to a commit (`git cat-file -e <sha>^{commit}`): [pass | fail — <sha> unresolvable or not a commit]
- V12 merge base matches `git merge-base <reviewed SHA> origin/main`: [pass | fail — stated <X>, computed <Y>]
- V13 implementation verdict present & evidenced: [pass | missing/rewrote item N | n/a — no implementation diff]
- Mode: [DRAFT_ONLY | WRITE_MODE]
- File written: [path | none]
```

## Tools

**Required:**
- `Read`, `Grep`, `Bash`
- `Write` (WRITE_MODE only)

**Preferred:**
- `docs/SCHEMA_MAP.md`, `docs/CALL_SITE_MAP.md` for V2 symbol lookup
  (then `grep -n` for current locations)

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
- Does not run the test suite itself; asserts implementation-against-PRD
  PASS/FAIL per requirement from the diff and whatever command/test
  output the implementer already produced (IMPLEMENTATION VERDICT; see
  Review structure and V13).
- Does not update `PRD_REGISTRY.md`. Review artifacts do not get
  registry rows (per `docs/PRD_PROCESS.md § Registry Maintenance`).
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
