# Board-state recon — 2026-06-30

**Supersedes `board-state-20260626` — stale on PRD-207/210/211** (that doc predates
PRD-207 landing, PRD-210's merge-to-main via PR #62, and PRD-211 via PR #71). One
canonical board state; treat 0626 as historical.

READ-ONLY charge. No mutation of source, contracts, or `main`. This artifact is the
sole deliverable (Recon-artifact clause, CLAUDE.md). Branch → `main` stays human-held.

- **main:** `a9ec4b2` — *chore: alignment cadence #5 — PASS (no drift) (#72)*
- **Validator (`tools/validate_prd_registry.py`):** GREEN as-is.
- **Counters (`docs/prd_index.json`):** `latest_complete=207`, `next_prd=208`.

---

## 205–211 registry inventory (verified against the tree)

| # | Registry row (main) | Impl landed? | Live branch(es) | Verdict |
|---|---|---|---|---|
| **205** | DEPRECATED (void) | No | `claude/codex-review-router-prd205`, `codex-review/PRD-205-2118426be05a` | **Real parked proposal, not a void** — codex-review channel-router wrapper; PRD-205.md + Claude review + Codex review, no `.py`. Void row contradicts the branch. |
| **206** | DEPRECATED (void) | No | `claude/narrow-regime-glob-prd206` | **Real parked proposal, not a void** — narrow `*regime*` protected glob; GOVERNANCE → manual-merge-only; no `.py`. |
| **207** | COMPLETE (`1968b50, 55f9cd2, 13c5d4a`) | Yes, on main | — | Done. |
| **208** | **No row** | **Yes — full impl on branch** | `claude/prd-208-stage-0`, `codex-review/PRD-208-{7cbe06,b42ec9}` | **Real pending HIGH-RISK work** — `dashboard_renderer.py` (+53) + tests (+148) + PRD-208.md + in-tree Claude **and** Codex reviews. Not void-fill. Review-pin caveat below. |
| **209** | **No row** | No | `claude/prd-209-stage-0` | **PROPOSED — HELD** (OHLCV bar-count floor; decoupled from F08; explicitly do-NOT-implement; no Codex review). Real decision, invisible on main. |
| **210** | IN PROGRESS | **Yes — on main** (PR #62, `55b2f67` + reviews) | `claude/prd-210-closeout` (broken — see finding) | Impl landed; row not yet flipped. |
| **211** | IN PROGRESS | **Yes — on main** (PR #71, `3317456`) | none | Impl landed; row not yet flipped. |

`claude/claude-md-prd-208-cvg7ux` carries the prior `board-state-20260626.md` recon doc
(not impl); it is the doc this file supersedes.

### 208 review-pin caveat
`claude/prd-208-stage-0` HEAD is `ceceedb` (a `main`-merge); its in-tree Codex review is
SHA-pinned to `7cbe061` (= impl head `830f9eb` + Claude review). Under the gate's
"review of a superseded commit does not satisfy later commits" rule, reviving 208 must
first confirm `ceceedb` carries no impl delta beyond `7cbe061` (it is the PRD-207
gate `main`-merge — expected doc/non-impl, but verify).

---

## FINDING (2026-06-30) — the 210/211 closeout is GATED on the 208/209 row gap

Closing PRD-210 and/or PRD-211 **cannot be landed without resolving the rowless 208/209
gap**, which is exactly the carve-out the closeout charge held out of scope. The validator
makes the two mutually exclusive:

- `validate_prd_registry.py:111` sets `expected_latest = max(complete_numbers)`. Flipping
  210 (or 211) to COMPLETE forces `latest_complete` to 210/211 — it is the **max**, not a
  contiguous tail, so it cannot stay at 207.
- `:121-123` then forces `next_prd = latest_complete + 1`.
- `:125-127` requires **every** number in `range(56, latest_complete+1)` to have an entry.
  With `latest_complete` advanced past 207, that range now includes **208 and 209**, which
  are rowless → `Missing PRD number: PRD-208 … PRD-209 …`.

Verified in a throwaway working tree (read-only, nothing committed):
1. 210+211 → COMPLETE, counters untouched → `Bad latest_complete: 207 but expected 211`.
2. + counters bumped to `211/212` → `Missing PRD number: PRD-208`, `PRD-209`.

The pre-existing `claude/prd-210-closeout` branch is **itself broken**: it flips 210 →
COMPLETE without bumping counters and was cut from an older base, so it fails the validator
(`Bad latest_complete: 204 but expected 210`). It is not mergeable as-is.

**Consequence:** 207 was the last PRD closeable without resolving 208/209. The closeout
"leave 208/209 alone" framing is unachievable under the current validator. To land the
210/211 closeouts, 208 and 209 must first receive registry/index entries (any status) — i.e.
the held 208/209 decisions must be made first. No edit to the validator or counters can
square this without those rows; that would be editing to satisfy the gate.

### Resolution paths (decisions — held for Dustin)
1. **Resolve 208/209 rows first, then close 210/211 in the same pass.** Minimal unblock:
   give 208 a row (its real impl exists on-branch — IN PROGRESS or HELD pending the revive
   decision) and 209 a HELD/PROPOSED row. Then 210/211 → COMPLETE, counters → `211/212`,
   range-fill satisfied. This is one reconcile pass, not "closeouts only."
2. **Keep 210/211 IN PROGRESS** until the 208/209 decisions land independently. Validator
   stays GREEN as-is; registry under-states reality (impl on main, row IN PROGRESS) but is
   internally consistent.

Path 1 is the real shape of the reconcile; path 2 defers. Either way the 208/209 decisions
gate the 210/211 closeout — they are not separable.
