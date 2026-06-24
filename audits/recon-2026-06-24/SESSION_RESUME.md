# Session Resume - 2026-06-24

Fresh-session standup note. The reader has no memory of this session. Scan section
2 (live branches) and section 3 (durable findings) first - they hold what no
structured field captures.

Context: `main` @ `3ce4179`. This session authored PRD-207 (dependency lockfile)
and left it resting. Nothing was pushed or merged.

---

## 1. LANDED THIS SESSION (reached `main`)

- Nothing merged to `main`. This session produced one resting commit on a feature
  branch (see section 2) and this resume note. No PR opened, no push.

---

## 2. LIVE BRANCHES (load-bearing)

### `claude/prd-207-stage-0` @ `344a0d0` - THIS SESSION, RESTING
- **What:** PRD-207 "Dependency lockfile for reproducible CI/local installs" -
  Stage-0 scaffold only. **Planning only - NO implementation.**
  - Adds `docs/prd_history/PRD-207.md` (IN PROGRESS), an IN PROGRESS registry
    row, a `prd_index.json` entry.
  - Flips the Active-PRD pointer in `PROJECT_STATE.md`.
  - `ci.yml` and `pyproject.toml` deliberately NOT touched.
- **State:** committed, NOT pushed, NO PR. Tree clean.
- **Stacked on:** the unmerged PRD-193 closeout (next branch), NOT `main`.
  - PRD-207's PROJECT_STATE edit rewrites the `Active PRD: none in progress.`
    line the closeout commit creates.
  - So the closeout tip is its correct base. On `main`, PRD-193 is still the
    Active PRD.
- **Consistency:** `tools/validate_prd_registry.py --skip-commit-resolvability`
  passes (exit 0) with 207 staged.
  - `latest_complete` (204) / `next_prd` (205) intentionally left unchanged; an
    IN PROGRESS entry above `latest_complete` is legal (see section 3, validator
    gap-rule).
- **EXACT NEXT GATE (in order):**
  1. Land the PRD-193 closeout to `main` first (next branch), so PRD-207's PR diff
     is clean.
  2. Then EITHER push + open the PRD-207 stage-0 PR (bookkeeping, auto-merge),
     OR start implementation in a separate session.
  3. **HIGH-RISK gate owed BEFORE the implementation merges:** Claude review
     artifact (with DRIFT CHECK) + Codex cross-review (`codex exec -s read-only`,
     SHA-pinned, fresh context), both durable under `docs/prd_history/`.
  4. **GOVERNANCE CARVE-OUT:** PRD-207 FILES includes `CLAUDE.md` (R6 edits the
     PRD-198 #6 doctrine text). A PR touching `CLAUDE.md` is manual-merge-only -
     do NOT queue `gh pr merge --auto` for it; hold for a human merge.

### `claude/prd-193-closeout` @ `7ec264f` (+2 over main: `08d61df`, `7ec264f`) - RESTING
- **What:** PRD-193 closeout bookkeeping - marks PRD-193 COMPLETE and reconciles
  PROJECT_STATE prose. On remote too (`origin/claude/prd-193-closeout`).
- **Why it matters:** on `main`, PRD-193 is STILL the Active / IN PROGRESS PRD
  (PROJECT_STATE last-updated `a26a70c`). This closeout is the pending bookkeeping
  that flips it to COMPLETE. PRD-207 is stacked on it.
- **EXACT NEXT GATE:** open / confirm the closeout PR and let CI auto-merge
  (bookkeeping PR, auto-merge per PRD-184). Land BEFORE the PRD-207 PR.

### Everything else under `git branch --no-merged main` is NOT live work
- ~10 local `claude/prd-*` branches (191/192/193-ohlcv/200/201/202 and their
  closeouts) show unmerged-to-`main` but their PRDs are COMPLETE on `main`. They
  are squash-merge leftovers (squash leaves the original branch commits unmerged
  in git's view). Safe to prune; do NOT mistake for live work.

---

## 3. DURABLE FINDINGS NOT IN ANY PRD

- **PRD numbering: trust the reservations, not the bare counter (load-bearing).**
  `prd_index.json` reads `next_prd: 205`, but 205 and 206 are RESERVED:
  `origin/claude/codex-review-router-prd205` (PRD-205, codex-review-router) and
  `origin/claude/narrow-regime-glob-prd206` (PRD-206, narrow the `*regime*.py`
  protected glob; governance follow-up to PRD-204) are scaffolded on remote
  branches, not yet opened at Stage 0 on `main`. `PROJECT_STATE.md` "Proposed /
  next" records the reservation. The next free NON-COLLIDING number was 207. A
  fresh session that trusts `next_prd: 205` blindly would collide with the
  codex-review-router branch.
- **Validator gap-rule (why a 207 stage-0 is legal under a 205 counter).**
  `tools/validate_prd_registry.py` only enforces presence of numbers
  `56..latest_complete`; numbers ABOVE `latest_complete` (an IN PROGRESS 207) may
  exist while 205/206 are absent. So an IN PROGRESS entry is added WITHOUT touching
  `latest_complete` (204) or `next_prd` (205). It also cross-checks registry row
  vs index entry for exact title/status/commit match - keep those identical.
- **OPEN DEBT - `docs/PRD_PROCESS.md` format drift.** The process doc still
  documents the OLD template order (`GOAL -> SCOPE -> OUT OF SCOPE -> FILES ->
  REQUIREMENTS -> DATA FLOW -> FAIL CONDITIONS -> VALIDATION`), but every live PRD
  (191/192/193/207) uses `LANE/CLASS/PROBLEM/SCOPE/DESIGN NOTES/NON-GOALS/RISKS/
  FILES/VERIFICATION/GATE`. The doc is stale vs practice. Not fixed (out of scope
  this session). Candidate cleanup PRD.
- **Unverified claim baked into PRD-207 PROBLEM.** The "Jun-23 audit's pytest
  collection failed on a missing yaml despite PyYAML being declared" incident is
  the user's assertion; it could NOT be corroborated from repo state (no
  PROJECT_STATE / DECISIONS record; not a code symbol). Kept verbatim per user
  instruction. If PRD-207 review wants it sourced or softened, that PROBLEM line is
  where to look.
- **Env quirk.** `python` is NOT on PATH in Bash tool calls (the venv does not
  persist across calls). Use `.venv/bin/python` directly for the validator or any
  python. `source .../activate` in a tool call is a no-op for later calls.

---

## 4. QUEUED / FUTURE SCOPE

- **PRD-207 implementation (next session):** add `pip-tools` to the `[dev]` extra;
  generate `requirements-dev.txt` (fully `==`-pinned transitive closure, compiled
  under py3.11); add `-c requirements-dev.txt` to `ci.yml`; R5 merge-guard test
  asserting full `==`-pinning; R4 README / `docs/dev_workflow.md` constrained-install
  update; R6 PROJECT_STATE debt entry + CLAUDE.md #6 partial-close edits. HIGH-RISK
  reviews owed before merge.
- **PRD-207 NON-GOALS seed two explicit follow-ups:** (a) SHA-pin `actions/* @v6`
  (invariant #6's other half) - a separate PRD; (b) `--generate-hashes` hash
  verification - lockfile v2.
- **PRD-205** (codex-review-router) and **PRD-206** (narrow `*regime*.py` protected
  glob) - scaffolded on remote branches, not at Stage 0 on `main` yet.
- **PRD-188** (macro-awareness SHOCK banner + scheduled activation) - PROPOSED,
  gated on the PRD-187 materiality eval; go / no-go by 2026-07-15.
- **Standing debt (from PROJECT_STATE):** `runtime/` package split re-eval by
  2026-08-15; 19 unreachable historical registry commit hashes, re-eval by
  2026-07-31 (CI skips resolvability via `--skip-commit-resolvability`).

---

## 5. DECISIONS.md CANDIDATES

- **CANDIDATE (recommend promote):** "When assigning a new PRD number, the next
  free number accounts for reservations recorded in PROJECT_STATE 'Proposed /
  next' and scaffolded-on-branch PRDs, not the bare `prd_index.next_prd` counter
  alone." Refines the existing "registry is truth" rule. Left for the user / next
  session to ratify - not promoted here.
- The format-drift, validator gap-rule, and env-quirk findings are note-only
  (observations / debt, not "always / never" rules).
