# FABLE WINDOW PLAN — 2026-07-04 → 2026-07-07

Companion to `audits/codebase-review-2026-07-03/MASTER_PLAN.md`. That file
remains the rails and the checkbox ledger — **this file only changes the
schedule and the executor**, never the DONE WHEN conditions. When the window
closes, delete this file; the master plan continues as written.

Recon basis (verified against `main`, 2026-07-04): `next_prd = 226` — the
plan's numbering assumption holds. God files confirmed at 2,880
(`dashboard_renderer.py`) and 2,290 (`runtime/__init__.py`) lines.
`assert_valid_contract` still test-only. `docs/` = ~6.4k lines across 28 files.

---

## Two deviations from the master plan — sign off before starting

The master plan was written for one-step-per-sitting Opus pace. Compressing it
into a 3-day Fable window changes two rules. These are conscious deviations;
they need your explicit OK, in writing, at the top of the Parking Lot.

**Deviation 1 — PRD-H is Fable-drafted.** The plan marks H `[YOU]`, "not
delegable — these are your rules." Modified: Fable drafts the two ceremony
rules + the CLAUDE.md edits; **you still merge by hand and read the diff**, per
the plan's own manual-merge requirement. The spirit (your rules, your merge)
survives; the drafting doesn't.

**Deviation 2 — the Wave 3 gate is modified, not waived.** The gate requires
Wave 1 closed AND 3 weekly module reads. Wave 1 closed stays HARD — the
validator (PRD-A) must be live before any structural refactor, because it is
the regression net. The 3-module-reads clause is deferred to the post-window
learning stint, replaced inside the window by two mechanical guards:
(a) byte-identical fixture-run checks on every behavior-preserving refactor,
(b) **your line-by-line read of the J1 schema diff — this stays in the window
and is not delegable.** It's the one personal hour the review asked for, and
it's the seam where your "review before and especially after" promise is kept.

---

## Sequence (order is the whole point)

### Block 1 — H first, then the docs/guardrail batch  `[FABLE, high autonomy]`
*Why H jumps from Wave 2 to first: it's the review's #1 leverage item and it
cuts the ceremony cost of every PRD that follows in this window. Process-cost
reduction compounds only if it lands before the work it cheapens.*

- **H (PRD-≈226)** — ceremony tiering (MICRO notes for cosmetics; closeout
  folds into the implementation PR). Fable drafts; **you hand-merge**.
- **Drop-list execution** (review items 3–7, one governance PRD, batch-reviewed):
  - Tear down the Codex-authenticity infrastructure; keep plain read-only
    `codex exec` review for HIGH-RISK lanes only.
  - Alignment cadence → phase-boundary diff-read only; retire the ceremony.
  - Purge `audits/` session sediment (8 recon folders + the 128 KB gate-recon).
  - Strip line numbers from CALL_SITE_MAP (keep file/function granularity).
  - Merge `dev_workflow.md` / `AGENT_WORKFLOW.md` / `CLAUDE_HOOKS.md` overlap
    into one owner; CLAUDE.md references it.
- **Guardrail tightening** — CLAUDE.md, `.claude/hooks/*`, `.claude/skills/*`,
  PRD templates: shorten, de-duplicate, make every rule state its trigger.
  This is the "optimized guardrails outlive the window" work — Opus and Sonnet
  run on these rails after the 7th.
- **Small doc-truth fixes pulled forward from G:** `qualification.py` "9
  gates" docstrings (11 exist), `output.py:17` stale "runtime.py" reference.
- **NOT here:** the full `architecture.md` rewrite. Deferred to Block 4 — if
  written now it documents the mutable-dict contract J1/J2 are about to
  retire, and gets written twice.
- **Your review:** one batch pass at the end of the block + clarifying
  questions inline. No per-file gates. H is the only hand-merge.

### Block 2 — Wave 1 correctness, per-PR seams  `[FABLE-owned]`
*Ritual unchanged: red test first, scope-locked FILES, full suite, you merge.*

- **Warm-up:** if the PR #86 NOW-anchor and PR #89 bool-guard cleanups are
  still open (verify — do not trust recollection), land them first to
  calibrate the faster cadence on small blast radius.
- **A (validator into production)** — the keystone and the Wave 3 gate key.
  Fable derives the real `system_state` whitelist from
  `runtime/__init__.py:900–960`; your personal check (whitelist vs. actual
  injections, side by side) stays.
- **B (kill the VALIDATED fail-open)** — your personal check stays: read the
  warning line; if future-you would have to look it up, reword it now.
- **C (qualification: no silent loosening, three red tests)** — personal
  check stays: qualify `metrics=None` yourself and eyeball the summary.
- **D, E → NOT Fable.** Both are mechanical (single-source constants;
  lockfile + SHA-pinning). Disposition: **Opus, after July 7.** They're on
  the review's easy list and spend window allowance for zero Fable edge.
  Wave 1's exit check is therefore split: A–C in-window, D–E next week —
  note this on the tracker so the wave doesn't read as falsely closed.

### Block 3 — Wave 3 structural, Fable's unique lane  `[FABLE plans + executes the risky cuts]`
*Gate check first: A live in production, suite green, Deviation 2 signed.*

- **I (≈ next number)** — extract decision-gate chain + contract finalization
  from `_run_pipeline` into named functions. Behavior-preserving;
  byte-identical `latest_run.json` / `latest_contract.json` / report check.
  This is the risky first cut of the runtime god file.
- **J1 — typed contract** (TypedDicts for contract / candidate /
  system_state; adopt in `contract.py` + `payload.py`). **Your one personal
  hour: read the schema diff line by line before merge.** Non-negotiable seam.
- **J2 — adopt types in renderer + notifications;** retire SCHEMA_MAP's
  field-lookup role.
- **M-map (design only)** — Fable produces the `RenderContext` design and an
  ordered seam map for the renderer decomposition: independently reviewable,
  independently revertible extractions sized for Opus. **Execution of M, K,
  and L: Opus, after July 7.** Fable's edge is the whole-system design, not
  the mechanical extraction; a 2,880-line rewrite in one branch is stranded
  closeout latency by construction.
- Fresh work orders generated at start time per the master plan's own
  prompt — the repo will have moved by Block 3; do not reuse stale FILES lists.

### Block 4 — Handoff (July 7, protect this time)  `[FABLE]`
- **G — architecture.md rewritten against the now-typed pipeline.** Your
  master-plan read of it top-to-bottom moves to the learning stint — but the
  "if anything surprises you, Parking Lot it" rule applies whenever you read it.
- **State-of-play doc** — what landed, what's open, exact next actions for
  D, E, F, K, L, M — written so Opus resumes on the 8th without re-running
  Fable-priced context.
- **Next-components scoping** — the forward-planning you originally wanted the
  window for, now informed by everything the window surfaced.

### Explicitly NOT in the window
- **F (test blind spots)** — STANDARD-lane test writing; Opus, after. (Its
  paired `confirmation.py` read belongs to your learning stint anyway.)
- **K, L, M execution** — Opus, after, per Block 3.
- **The weekly module-read habit** — deferred whole to the learning stint;
  it is the actual mentorship and no model can do it for you.

---

## Rails for the window itself

1. **Burn order = block order.** If allowance runs dry early you lose Block 3
   execution (recoverable next week at usage-credit prices or on Opus) rather
   than Blocks 1–2 (the cheap-to-lose stuff went first on purpose... no —
   the *guardrails and keystone* went first on purpose; what's lost late is
   what's most recoverable).
2. **Watch the 50% cap** against your weekly limit before each block; decide
   at block boundaries, not mid-PRD.
3. **One hard checkpoint:** nothing flips `assert_valid_contract` on in
   production without your explicit go.
4. **Checkbox discipline unchanged:** master-plan boxes only get checked when
   their DONE WHEN passes. Compressed schedule, uncompressed standards.
5. **Numbering:** letters stable, numbers float — re-read `next_prd` at each
   Stage 0; other work may land between blocks.
6. **If the window closes mid-block:** stop at the last merged PR, write the
   state-of-play immediately (Block 4's doc, early), and nothing is stranded —
   every stage in this plan is a separately mergeable unit by design.

---

*Execution note (2026-07-04, Fable): the recon-basis line above predates the
window's first session. On start, `next_prd: 226` was found to be the
validator-derived `latest_complete + 1`, not the next free number — 226/227
are claimed by open PR #95 and PRD-228 had merged unclosed. Reconciled in
PR #98; the window's PRDs start at 229 (H = PRD-229). Letters stable,
numbers float, per rail 5.*
