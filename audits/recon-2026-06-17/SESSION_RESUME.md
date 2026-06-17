# Session resume note — 2026-06-17 (evening stand-down)

Durable checkpoint for the Codex-gate / semantic-failure arc. Nothing here is
merged, discharged, or closed — **#25, #26, and PRD-197 all remain at Dustin's
seam.** Pick up from the priority list below.

## Persistence + drift check (this session's own lesson, applied)

- **Working tree:** clean.
- **Held branches pushed:** `claude/prd-197-provenance-hardening` (PR #25) and
  `claude/prd-198-semantic-failure-doctrine` (PR #26) — both pushed, no unpushed
  commits on any branch. Nothing half-written.
- **PRD-197 recorded state matches reality:** registry row IN PROGRESS, index
  IN PROGRESS; only `PRD-197.review.claude.md` exists (no `.review.codex.md`) —
  i.e. the **bootstrap Codex waiver is UNdischarged**, consistent with IN PROGRESS.
- **PRD-198:** registry + index rows IN PROGRESS (Stage-0); held via #26.

### Divergences flagged (recorded ≠ reality) — NOT corrected; for Dustin
Protected bookkeeping files — left untouched per charge. Each is itself an
instance of the recon's stale-bookkeeping signature.

1. **`docs/PROJECT_STATE.md` says "Active PRD: none in progress"** while the
   registry + index show **197 and 198 both IN PROGRESS.** `prd_open.sh` by design
   does not touch the Active-PRD pointer, and both PRDs were authored scoped/held,
   so the pointer was never set. Correction (if wanted) is a PROJECT_STATE edit —
   protected; report-only here.
2. ~~**`prd_index.json` `next_prd: 195`** is stale — should be 199.~~
   **RETRACTED (false positive; corrected after #26 review).** `next_prd` is
   *defined* as `latest_complete + 1` by `tools/validate_prd_registry.py:118-122`,
   and `latest_complete` is 194, so `next_prd: 195` is **correct** — not drift.
   Recommending 199 was itself the "assert the assumed vs verify the resolved"
   error this PRD warns against (199 would *fail* the validator). `next_prd`
   advances to 195→…→199 only as PRDs are *marked COMPLETE*; `prd_open.sh` rightly
   leaves it untouched when opening in-progress PRDs. No action.
3. **Test baseline `2773`** (PRD-179 era) trails current CI (~2782 after #23/#24) —
   same as recon finding #6. Updates at the next closeout. (Not enforced by
   `validate_prd_registry.py`, so a real-but-quiet staleness, unlike #2.)

None block the parked work. The one real recorded≠reality item is #1 (the
PROJECT_STATE Active-PRD pointer); fold its correction into whichever PRD closes
next (197), rather than a standalone bookkeeping PR. **Do NOT touch `next_prd`.**

## Parked items — priority order

### 1. #25 — provenance hardening — **PENDING DUSTIN'S DECISION**
Branch `claude/prd-197-provenance-hardening`. Held; blocks PRD-197 closeout.

- **The decision:** pick the current Codex model id to replace the stale
  `gpt-5-codex`. Recommended: **`gpt-5.4`** (flagship), or **`gpt-5.3-codex`** for
  the literal `-codex` match that reads cleanest against doctrine invariant #3
  / PRD-#21 property 3.
- **Then the sequence:**
  1. id-swap to the chosen current id.
  2. merge #25 (human seam).
  3. re-dispatch with an **EMPTY `ALLOWED_CODEX_MODELS`** allowlist → fail-closed
     run captures the **authoritative resolved** model id.
  4. set `ALLOWED_CODEX_MODELS` to that resolved id.
  5. re-dispatch → truthful `PRD-197.review.codex.md` artifact lands on a
     `codex-review/PRD-197-<sha>` branch.
  6. human-open the PR for that artifact → discharge the bootstrap waiver.
  7. close PRD-197.
- Open mechanism question still standing: capture the resolved id from the session
  rollout vs direct `--json` capture vs honest-provenance + account check. The
  empty-allowlist fail-closed dispatch (step 3) is the capture mechanism either way.

### 2. #26 — PRD-198 doctrine + recon — **read + manual-merge if accepted**
Branch `claude/prd-198-semantic-failure-doctrine`. CI green (`test` + GitGuardian).
Manual-merge-only (governance guardrail). Two paths:
- accept the doctrine → manually merge #26 (it only files the PRD; the actual
  CLAUDE.md edit is a separate manual-merge follow-up), **or**
- have the per-finding recon fixes (HIGH: codex provenance behavioral test +
  resolved-not-requested; MED: dep lockfile, action SHA-pins, prd_close fail-loud,
  baseline check, engine_doctor; LOW: vacuous skips, soft-dep, version provenance)
  spun into follow-up PRDs.

### 3. PRD-197 — IN PROGRESS; closeout blocked on #25
Closeout (incl. the PROJECT_STATE + `next_prd` corrections above) runs once #25's
truthful artifact discharges the waiver.

## Subscriptions
Subscribed to PR activity for #26 (and #25). `send_later` unavailable → no
scheduled re-check armed; will act on CI / review-comment webhooks as they arrive.
