# Fable window — state of play (2026-07-04, end of session 1)

Companion: `audits/codebase-review-2026-07-03/FABLE_WINDOW_PLAN.md` (committed
on PR #99). Blocks 1 and 2 are fully staged; Block 3 is gated on Dustin.

## The merge queue (Dustin, in this order — each merge collapses the next diff)

| PR | What | Gate state |
|----|------|-----------|
| #98 | Registry reconciliation (226/227 reservations, 228 closeout) | MERGED (auto) |
| #99 | Block-1 batch: PRD-229 (ceremony tiering) + 230 (drop-list) + 231 (doc-truth) + 232 (guardrails) | Manual merge = your batch pass + Deviation-1 sign-off. All bot threads actioned+resolved. |
| #100 | PRD-233 = PRD-A (validator live in _run_pipeline, pre-notification) | **Your explicit go required (rail 3).** Personal check: whitelist vs runtime injections. Codex artifact or waiver needed. |
| #101 | PRD-234 = PRD-B (CHAIN UNVERIFIED, fail-open killed) | Personal check: read the warning text. Codex artifact/waiver. |
| #102 | PRD-235 = PRD-C (NEUTRAL exclusion + gate-skip markers) | Personal check: qualify metrics=None, eyeball summary. Codex artifact/waiver. |
| #95 | Pre-window codex-connector cleanup (PRD-226/227) | Yours, pre-existing; reservation rows on main match its branch. |

Codex gate note: no `codex` CLI in the remote container and the connector bot
ran out of review credits mid-window. For #100/#101/#102 either run
`codex exec -s read-only` from a host session against each head SHA (artifact
to `docs/prd_history/PRD-NNN.review.codex.md`) or record a waiver. Every PR
carries a fresh-context Claude review artifact in-tree, ACCEPT WITH CHANGES,
all REQUIRED edits remediated.

## Block 3 gate (do not start structural work until BOTH hold)
1. PRD-233 merged (validator live in production = the regression net).
2. Deviation 2 re-confirmed by Dustin (module-reads deferral; the Parking-Lot
   entry in MASTER_PLAN.md marks it NOT yet signed).
Then: I (extract decision-gate chain from _run_pipeline, byte-identical
fixture check), J1 (TypedDict contract — Dustin reads the schema diff line by
line), J2, M-map design only. Fresh work orders at start time; numbers float
(next free after this window: 236).

## Queued follow-ups surfaced by reviews (next session, small)
- PRD-233 hourly-path follow-up: extend finalize-validation to
  `_build_hourly_contract` AND retire the sibling synthesize-VALIDATED at
  `runtime/__init__.py:785` (enumerated in PRD-234 OUT OF SCOPE).
- Parked (PROJECT_STATE): present-MANUAL_CHECK render invisibility
  (systematic in fixture mode).
- PRD-235 retained silent path: missing-candidate fall-through
  (`qualification.py` ~:196) — absence semantics belong upstream.
- Master-plan D (single-source constants) and E (lockfile + SHA-pinning):
  explicitly NOT Fable work — Opus, after July 7. F, K, L, M execution: same.
- Wave-1 exit note: A–C in-window, D–E next week — the tracker must not read
  as falsely closed (window plan Block 2 deviation, recorded).

## Facts the next session should not re-derive
- Same-PR closeout (PRD-229) is live: COMPLETE rows record `#NNN`; validator
  accepts it; closeout commit goes INTO the open PR once its number exists.
- The stacked branches: fable-window-plan-bsy92m (#99) ⊂ prd-233 (#100) ⊂
  prd-234 (#101) ⊂ prd-235 (#102). Registry conflicts across the stack were
  pre-resolved by merging each predecessor in.
- Local suite on the full stack: 2873 passed, 1 xfailed. Baselines in each
  closeout cite the branch count; re-anchor from CI on main after the queue
  merges (PRD-196/198#5).
- The connector bot caught 5 real defects this window (all actioned in-thread
  with fixing SHAs): PRD-229 dogfood gap, PRD-231 registry mismatch + grep
  variants, scope-lock carve-out nullification, scope-lock A/M/D parser gap,
  and the P1 validate-before-notification ordering on #100.
- audits/ purge premise is FALSE (inbound refs everywhere except the one
  deleted file) — Dustin dispositions the referenced folders at the #99 read.

## Window bookkeeping
- Delete `FABLE_WINDOW_PLAN.md` when the window closes (its own instruction);
  the master plan continues as written. Master-plan checkboxes are Dustin's
  to tick (H box: DONE WHEN passes at #99 merge; A box at #100; B at #101;
  C at #102 — noting D–E split out).
- This note is session scratch under the PRD-230 sediment rule: delete it
  once the next session confirms nothing was lost.
