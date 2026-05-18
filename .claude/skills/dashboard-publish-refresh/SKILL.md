---
name: dashboard-publish-refresh
description: Use when a PRD has touched the dashboard renderer, payload, macro_tape_layout, notifications, or any module that affects rendered HTML output. Detects renderer-relevant changes in the staged or recent diff, runs the renderer command, copies dashboard.html to index.html, and verifies the two outputs are byte-identical and contain user-named markers. Mirrors the `feedback_dashboard_publish.md` discipline. Triggers on "refresh dashboard", "publish UI", "update ui/dashboard.html", or after a renderer-touching implementation commit.
---

# Dashboard Publish Refresh

## Scope and boundary

This skill does two things and only two things:

1. **Render** the dashboard via the canonical pipeline command and
   mirror `ui/dashboard.html` → `ui/index.html`.
2. **Verify** the two artifacts agree byte-for-byte and contain every
   marker the user names.

It is NOT a substitute for:

- Running the full pipeline
- The renderer's own internal validation
- Visual / browser inspection (the skill does not open a browser)

This is a *mechanical artifact refresh*, not a render-quality check.

## When to trigger

- "Refresh the dashboard" / "publish UI"
- "Regenerate ui/dashboard.html"
- After a commit that touched any of:
  - `cuttingboard/delivery/dashboard_renderer.py`
  - `cuttingboard/delivery/payload.py`
  - `cuttingboard/delivery/macro_tape_layout.py`
  - `cuttingboard/notifications/` (any file)
  - Any module the PRD names as renderer-adjacent
- Before closeout for any PRD whose FILES list touches the renderer
  surface

Do NOT trigger for:
- PRDs explicitly stating UI artifacts intentionally NOT refreshed
  (the PRD-132 / PRD-136 pattern). Read the PRD's "Generated UI
  artifacts" note before invoking.
- Non-renderer PRDs.

## Operating modes

Default is **DRY_RUN**.

- **DRY_RUN** — render to a temp path, run verification, do not touch
  `ui/dashboard.html` or `ui/index.html`. Reports what would change.
- **WRITE_MODE** — render to `ui/dashboard.html`, copy to
  `ui/index.html`, stage both. Does NOT commit.
- WRITE_MODE never commits and never pushes. The user reviews the
  diff and commits via their normal flow (or via
  `scope-lock-precommit` in CHECK_AND_COMMIT mode).

If unclear, ask once, then default to DRY_RUN.

## Inputs required

- `markers` — list of `"literal string" : <expected_count>` pairs the
  refreshed HTML must contain. **Required for WRITE_MODE.** No
  markers, no WRITE_MODE — refuse. Examples:
  `"class=\"macro-spot-metals-row\""` : 1, `"data-symbol=\"XAU\""` : 1.
  DRY_RUN proceeds without markers but flags the omission in V4.
- `prd` (optional) — active PRD number, for the report. If supplied,
  the skill reads `docs/prd_history/PRD-NNN.md` and surfaces any
  "Generated UI artifacts NOT refreshed" note.
- `size_delta_override` (WRITE_MODE only, optional) — explicit user
  confirmation to proceed past the V5 25% size-delta stop. Must be
  a literal acknowledgement (e.g. `"confirmed: size drop expected
  because <reason>"`). Never assumed; never inferred.

## Hard rule: no invented references

The skill must never invent:

- The renderer command (canonical only — see below)
- Marker strings (user-supplied or omitted; never guessed)
- Expected counts
- A size-delta override justification
- A commit message

## Canonical renderer command

```
python3 -m cuttingboard.delivery.dashboard_renderer --output ui/dashboard.html
cp ui/dashboard.html ui/index.html
```

In DRY_RUN the `--output` target is a temp file (e.g.
`/tmp/dashboard-dryrun-<pid>.html`) and the `cp` is to a sibling temp
path; the real `ui/*` files are untouched.

If the renderer command exits non-zero, stop. Do not stage or commit
a partial artifact.

## Two-phase contract

### Phase 1 — Render

1. Resolve mode (DRY_RUN | WRITE_MODE).
2. Determine output paths (temp in DRY_RUN, `ui/*` in WRITE_MODE).
3. Run the canonical renderer command. Capture exit code and stderr.
4. Copy primary output to mirror path.
5. In WRITE_MODE: `git add ui/dashboard.html ui/index.html`.

### Phase 2 — Verify (MANDATORY before returning)

| # | Check | Action on failure |
|---|---|---|
| V1 | Renderer command exited 0 | Stop; surface stderr; do not stage |
| V2 | Both output files exist and are non-empty | Stop; treat as render failure |
| V3 | `diff -q <primary> <mirror>` reports identical | Stop; investigate why `cp` produced divergence |
| V4 | Every user-supplied marker appears the expected count. WRITE_MODE refuses entirely if no markers supplied. | Stop in WRITE_MODE; warn in DRY_RUN |
| V5 | Output size is within ±25% of the prior `ui/dashboard.html` size (truncation guard). **DRY_RUN: warn and continue. WRITE_MODE: stop unless `size_delta_override` was supplied with explicit justification.** | Stop (WRITE_MODE) or warn (DRY_RUN) |
| V6 | Both outputs newer than every named renderer source file | Stop; rerun renderer |
| V7 | In WRITE_MODE: only `ui/dashboard.html` and `ui/index.html` are staged | Refuse; unstage extras |
| V8 | The active PRD does not declare "UI artifacts NOT refreshed" (if `prd` input supplied) | Stop; the PRD intentionally defers this refresh |

### Verification Report shape

```
## Verification Report
- V1 renderer exit: [0 | <nonzero> — stderr: <first line>]
- V2 outputs exist: [pass | missing: <files>]
- V3 byte-identical: [pass | divergent: <count> bytes]
- V4 markers: [N/N matched | mismatched: <"<str>" expected X got Y> | NONE SUPPLIED (DRY_RUN warning)]
- V5 size delta: [+X% / -X% — within ±25% bound | WARN (DRY_RUN) | STOP (WRITE_MODE) | OVERRIDDEN: <user justification>]
- V6 mtime: [outputs fresh | stale relative to <file>]
- V7 staged set: [pass | extras staged: <files>]
- V8 PRD UI-refresh policy: [refresh permitted | DEFERRED per PRD-NNN — STOP]
- Mode: [DRY_RUN | WRITE_MODE]
- Action: [report only | staged ui/dashboard.html + ui/index.html | REFUSED — <reason>]
```

## Tools

**Required:**
- `Bash` (for renderer command, `cp`, `git add`, `diff`)
- `Read`, `Grep` for marker assertions and prior-PRD note check

**Optional:**
- `Edit` — never used; this skill does not edit source files

No GitNexus dependency. No subagent dispatch.

## What this skill does NOT do

- Does not edit the renderer or any source module. If the renderer
  output is wrong, that is an implementation issue — fix it via a
  PRD, not via this skill.
- Does not commit. The user commits via their normal flow.
- Does not push.
- Does not run tests.
- Does not validate the data contract the renderer consumed; the
  renderer's own assertions cover that.
- Does not infer a `size_delta_override`. Override requires explicit
  user-supplied justification text.

## Failure modes to refuse

- Renderer command exits non-zero: refuse; surface stderr.
- WRITE_MODE without markers: refuse; require explicit assertions.
- Active PRD declares UI artifacts intentionally NOT refreshed: refuse;
  the PRD has chosen to defer this refresh by design.
- Output size delta exceeds ±25% in WRITE_MODE without explicit
  `size_delta_override`: refuse; suspected truncation or oversize.
- Files other than `ui/dashboard.html` / `ui/index.html` get staged
  as a side effect: refuse; treat as scope leak.
- User asks the skill to commit or push: refuse; out of scope.
- User asks to skip Phase 2: refuse.
