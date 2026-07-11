---
name: prd-authoring-verified
description: Use when drafting any new PRD or micro-PRD under docs/prd_history/. Generates the PRD from the user's intent AND runs a built-in mechanical verification pass against the repo before handing it back — symbol existence, FILES completeness, FAIL-line observability, lane classification, and micro-PRD eligibility. This is an authoring + mechanical-check skill; it does NOT replace independent review, Codex cross-review, or implementation review. Triggers on "draft a PRD", "write PRD-NNN", "new micro-PRD", "propose a change for X".
---

# PRD Authoring with Built-in Verification

## Scope and boundary

This skill does two things and only two things:

1. **Author** a PRD or micro-PRD from the user's intent.
2. **Mechanically verify** that the PRD's references match repo reality.

It is NOT a substitute for:

- Independent PRD review (Claude review artifact)
- Cross-review gate / Codex review (`CLAUDE.md § Review gates`)
- Implementation review or test-pass verification
- Adjudication of unresolved review disagreement

A PRD that passes this skill's Verification Report is *internally
consistent with the repo*, not *approved*. Approval still requires the
review path defined in `CLAUDE.md`.

## When to trigger

- "Draft PRD-NNN for <change>"
- "Write a micro-PRD to <change>"
- "Propose a PRD that does <change>"
- "Start a new PRD for <feature/fix>"
- Any request that will produce a file under `docs/prd_history/PRD-*.md`

Do NOT trigger for: editing an existing IN PROGRESS PRD's bookkeeping,
review artifacts (`*.review.*.md`), adjudications, or registry edits.

## Operating modes

The skill operates in one of two modes. Default is **DRAFT_ONLY**.

- **DRAFT_ONLY** — emit the PRD text and the Verification Report in the
  response. Do not write any file. Do not touch the registry.
- **WRITE_MODE** — write the PRD to `docs/prd_history/PRD-NNN.md`. Do
  NOT edit `docs/PRD_REGISTRY.md` unless the user has explicitly stated
  implementation is starting in this same session. Per
  `docs/PRD_PROCESS.md § Registry Maintenance`: "Add a row to
  PRD_REGISTRY.md with status IN PROGRESS before implementation
  begins."

The user selects the mode. If unclear, ask once, then default to
DRAFT_ONLY.

## Hard rule: no invented references

Verified repo reality wins over drafting intent. The skill must never
invent:

- File paths
- Module names
- Symbol, function, class, or method names
- Field paths in payloads / schemas / artifacts
- Helper names, fixture names, or test names
- Line numbers

If a reference cannot be confirmed after the fallback inspection chain
below, the skill MUST either:

1. **Generalize** — rewrite the requirement to describe behavior
   without naming the unverified symbol, OR
2. **Remove** — drop the reference entirely, OR
3. **Tag** — keep the reference but annotate `[UNVERIFIED]` inline and
   list it in the Verification Report under V1.

Guessing is forbidden.

## Two-phase contract

### Phase 1 — Generate

1. Read `docs/PROJECT_STATE.md` to confirm active PRD and next number.
2. Read `docs/PRD_REGISTRY.md` to pick the next free `PRD-NNN`.
3. Decide template:
   - Cosmetic (PRD-229 Cosmetic Carve-Out, `docs/PRD_PROCESS.md`):
     ui copy / CSS / layout, or comment/docstring-only edits, touching
     no R12 behavior surface → a ≤10-line MICRO note (GOAL + FILES +
     one FAIL line), no template; batch into the weekly polish PRD
     when one is running.
   - Micro (`docs/PRD_MICRO_TEMPLATE.md`) only if ALL eligibility
     criteria in `docs/PRD_PROCESS.md § LANE Axis` (MICRO row + R12
     safety net) and the micro template's own criteria hold.
   - Otherwise full (`docs/PRD_TEMPLATE.md`).
4. Draft section order verbatim from the template.
   Full: `GOAL → SCOPE → OUT OF SCOPE → FILES → REQUIREMENTS → DATA FLOW → FAIL CONDITIONS → VALIDATION`.
   Micro: `GOAL → SCOPE → FILES → REQUIREMENTS → VALIDATION → COMMIT PLAN`.
5. Add `LANE: MICRO | STANDARD | HIGH-RISK` to the header (PRD-121).
6. Every requirement R1..Rn gets an inline `FAIL:` line.

### Phase 2 — Verify (MANDATORY before returning)

Run every check below. Emit a `## Verification Report` block at the end
of the response. Do not skip any item; mark `N/A` with a reason if it
genuinely does not apply.

| # | Check | Primary tool | Fallback | Action on failure |
|---|---|---|---|---|
| V1 | Every symbol/field path/function in REQUIREMENTS exists in the repo | `Grep`/`rg` over repo + `docs/SCHEMA_MAP.md` + `docs/CALL_SITE_MAP.md` + `Read` | Same | Tag `[UNVERIFIED]` inline AND list in report; OR generalize / remove |
| V2 | Every line number cited matches current source | `Read` at exact `offset+limit` | `Grep -n` against the named file | Correct the number, or remove the citation |
| V3 | Every file in `FILES` exists; every file the PRD will edit is listed | `Bash: ls` + manual consumer grep | Same | Amend FILES before returning |
| V4 | Visible-String Pre-Edit Audit: grep `tests/` for every literal string being renamed/removed | `Agent(Explore, haiku)` if ≥3 files or >5 strings | `Grep`/`rg` main-thread | Add missing test files to FILES |
| V5 | No file in FILES is in the protected pipeline set unless `LANE: HIGH-RISK` — EXCEPT a cosmetic-only change (PRD-229 carve-out: ui copy/CSS/layout in presentation code, or comment/docstring-only i.e. zero executable-line delta; no R12 surface either way), which stays MICRO regardless of file | `Read` `docs/AGENT_WORKFLOW.md § Auto-Approval Policy` + carve-out check | Same | Escalate lane or split PRD |
| V6 | Each `FAIL:` line is binary + observable (no "should", "appropriate", "reasonable", "as needed") | Regex scan of own output | Same | Rewrite the FAIL line |
| V7 | If micro template used, ALL eligibility criteria in `docs/PRD_PROCESS.md § LANE Axis` (+ R12) hold; if the cosmetic note is used, the diff is provably comment/copy/CSS-only | Manual checklist against diff scope | Same | Switch to full template |
| V8 | LANE header present and matches the risk surface implied by FILES | Header presence check | Same | Add or correct LANE |
| V9 | Registry row exists ONLY if the PRD is moving to IN PROGRESS now | `Read` `PRD_REGISTRY.md` | Same | Defer registry write |
| V10 | RETIRED (PRD-243: GitNexus removed) — blast-radius coverage lives in V3's manual consumer grep + the CLAUDE.md pre-implementation grep sweep | — | — | — |

### Verification Report shape (must appear at end of every response)

```
## Verification Report
- V1 symbols verified: [list] — UNVERIFIED: [list or none]
- V2 line numbers checked: [N]
- V3 FILES coverage: [pass | added X, Y]
- V4 visible-string audit: [N strings × M files | N/A — no rename]
- V5 protected-file scan: [pass | escalated to HIGH-RISK because …]
- V6 FAIL-line lint: [pass | rewrote R3, R5]
- V7 micro eligibility: [pass | switched to full because …]
- V8 LANE: [MICRO | STANDARD | HIGH-RISK]
- V9 registry: [deferred | row added because implementation starting now]
- V10: retired (PRD-243)
- Mode: [DRAFT_ONLY | WRITE_MODE]
- File written: [path | none]
```

## Tools

**Required (skill cannot run without these):**

- `Read`, `Write`, `Edit`
- `Grep` (or `rg` via `Bash`)
- `Bash` (for `ls`, file existence, optional script invocation)

**Recon chain (PRD-243: the GitNexus layer is retired; this IS the method):**

1. `docs/SCHEMA_MAP.md` for field paths
2. `docs/CALL_SITE_MAP.md` for the owning file+function, then
   `grep -n "def <name>" <file>` for the current line (the map carries
   no line numbers since PRD-230)
3. `Grep`/`rg` over the repo for symbol existence
4. `Read` at known offsets for signature confirmation

If after the full fallback chain a reference still cannot be verified,
apply the hard rule above (generalize / remove / tag `[UNVERIFIED]`).

**Optional helpers:**

- `Agent(subagent_type: "Explore", model: "haiku")` for V4 bulk
  test-tree grep when scope is ≥3 files or >5 strings (per
  `CLAUDE.md § Working practices`, "Recon goes to subagents").
- `scripts/pre_commit_sanity.sh` — only relevant if user is about to
  commit; this skill does not commit.

## What this skill does NOT do

- Does not implement the PRD. Implementation is a separate session.
- Does not run the test suite. PRDs are pre-implementation.
- Does not invoke Codex review. Cross-review gate is separate.
- Does not write to `PRD_REGISTRY.md` unless implementation is starting
  in the same session and the user has said so explicitly.
- Does not perform independent technical review of the PRD's design
  choices; mechanical verification only.

## Failure modes to refuse

- User asks to skip Phase 2: refuse; verification is the skill's purpose.
- Verification surfaces HIGH/CRITICAL impact without HIGH-RISK lane:
  stop and present the impact result before finalizing the PRD.
- User asks to use micro template when V7 fails: refuse; use full.
- User asks the skill to invent a symbol/path "for now": refuse; apply
  the no-invented-references rule.
