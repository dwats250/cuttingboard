# Board-state recon — 2026-06-26

READ-ONLY charge. No mutation of source, contracts, or `main`. This artifact is
the sole deliverable (Recon-artifact clause, CLAUDE.md). Branch → `main` stays
human-held. Verdicts reported inline; held for triage.

Method: three `Explore` sub-agents fanned out (branch reconciliation, VWAP
classification, scoreboard cap-site). Every decisive claim below was
re-verified by the main agent with the single deciding command
(sub-agent sweep re-verification discipline, CLAUDE.md).

---

## STEP 0 — checkout truth

- **HEAD:** `0c9b1da` — *governance: add Recon-artifact clause (read-only git-ops scope) (#63)*
- **next_prd (`docs/prd_index.json`):** `205`
- **Registry highest COMPLETE (`docs/PRD_REGISTRY.md`):** **PRD-204** (Non-destructive scoreboard aggregate)
- **`0c9b1da` (recon-artifact clause) in this history?** **YES** — it *is* HEAD; `git merge-base --is-ancestor 0c9b1da HEAD` → true. `git merge --ff-only origin/main` → already up to date.

Registry tail is clean and contiguous through 204 (…200, 201, 202, 203, 204 all COMPLETE).

---

## STEP 1 — parked stage-0 cluster reconciliation

Nine branches carry PRD numbers 205–210. **None are merged to `main`** —
`git log origin/main --grep` for any of 205–210 returns zero, and no
`docs/prd_history/PRD-20[5-9|10].md` exists on `main`. Registry/index are
untouched by them (ceiling 204, next_prd 205).

### Per-branch facts (diff vs `origin/main`, .py = implemented)

| Branch | HEAD | Subject | files / +/- | .py touched? |
|---|---|---|---|---|
| `claude/codex-review-router-prd205` | `33096b8` | PRD-205: revise R3 + CHANGE SURFACE; add Claude review | 5 / +320 −2 | **NO** (docs/PRD/review) |
| `claude/narrow-regime-glob-prd206` | `253a905` | PRD-206: stage 0 (PROPOSED) — narrow `*regime*.py` glob | 4 / +119 −3 | **NO** (governance docs) |
| `claude/prd-208-stage-0` | `b42ec9a` | PRD-208: resolve blocking review flag + should-fixes; add Claude review | 4 / +248 | **NO** (PRD + review + registry) |
| `claude/prd-209-stage-0` | `20f0cfe` | PRD-209: status hygiene IN PROGRESS → PROPOSED (parked) | 3 / +273 | **NO** (PRD only, HELD) |
| `claude/prd-210-stage-0` | `627839f` | PRD-210: bring binding Codex cross-review in-tree | 7 / +363 −1 | **YES** → `cuttingboard/runtime/__init__.py` (+7/−1), `tests/test_runtime_trend_structure_refresh.py` (+35) |
| `codex-review/PRD-205-2118426be05a` | `fc142c9` | Codex cross-review artifact (reviewed `2118426`) | 1 / +27 | NO (review artifact) |
| `codex-review/PRD-208-b42ec9aa7ebe` | `f08ac0f` | Codex cross-review artifact (reviewed `b42ec9a`) | 1 / +29 | NO (review artifact) |
| `codex-review/PRD-210-74c86b2471d2` | `adaeb7d` | Codex cross-review artifact (reviewed `74c86b2`, earlier iter) | 1 / +26 | NO (review artifact) |
| `codex-review/PRD-210-7e836b9765cd` | `b099e75` | Codex cross-review artifact (reviewed `7e836b9`, later iter) | 1 / +28 | NO (review artifact) |

Re-verified (main agent): `git diff --stat origin/main...origin/claude/prd-208-stage-0`
shows **no .py**; the same for 205/206/209. Only `prd-210-stage-0` touches `.py`
(`runtime/__init__.py` + a test). No `207` branch exists.

### 205–210 reconciliation (against next_prd=205, ceiling=204)

| # | Verdict | Note |
|---|---|---|
| **205** | **PARKED-SCOPE-ONLY** | Codex-review channel-router tooling. Claude + Codex review artifacts exist. STANDARD/EXECUTION. |
| **206** | **PARKED-SCOPE-ONLY** | Narrow `*regime*.py` protected glob to the decision engine (frees `delivery/regime_history.py`, a read-only sidecar, from protection). GOVERNANCE → **manual-merge-only**. |
| **207** | **ABSENT** | No branch, no file, no row. Unclaimed gap. |
| **208** | **PARKED-SCOPE-ONLY** | SMA-compression dashboard work (below). Claude + Codex review artifacts exist; no code. HIGH-RISK. |
| **209** | **PARKED-SCOPE-ONLY (HELD)** | OHLCV bar-count floor. Explicitly *do-not-implement*, decoupled from F08, awaiting a build decision. No Codex review. |
| **210** | **PARKED-IMPLEMENTED** | Premarket trend-structure path coverage (PRD-174 history fallback on `_run_pipeline`, the closes-None / F08 fix). Only cluster member with real `.py`. Full review chain in-tree (Claude + 2 Codex iterations). Most mature. |

### Critical calls

- **Does the SMA-compression work (208) exist as scope-only?** **YES — scope-only.**
  `prd-208-stage-0` (`b42ec9a`) touches only `docs/prd_history/PRD-208.md`
  (+230), its Claude review (+11), and registry/index. The intended
  implementation — rewrite `_trend_structure_composite_display` in
  `cuttingboard/delivery/dashboard_renderer.py` to emit compressed arrow cells
  (e.g. `↑50 ↓200`) and guard bare `NULL`/`None` — **is not written**. A Codex
  cross-review artifact for the exact HEAD (`b42ec9a`) exists on
  `codex-review/PRD-208-b42ec9aa7ebe`, so the review gate is pre-satisfied for
  that commit.

- **Would reviving 208 collide with the next free number (205)?** **NO collision,
  but a numbering decision is teed up.** `next_prd=205` is canonical and
  unblocked (204 COMPLETE). 205/206/208/209/210 are all parked at their own
  numbers; 207 is an unused gap. Reviving 208 does **not** require renumbering —
  its branch, PRD file, and Codex review are all already keyed to 208. The live
  question is **ordering, not collision**: 205, 206, 208, 209, 210 each hold a
  number ahead of `next_prd`'s 205 cursor. **Recommendation: revive-208 in place**
  (keep the number; the scope doc + SHA-pinned Codex review already exist —
  renumbering would orphan the `b42ec9a` review pin for no benefit). Renumber
  only if Dustin wants a strict contiguous 205→206→207… close order.

---

## STEP 2 — intraday "VWAP not applicable" classification

**Verdict: (b) POPULATION GAP** — correct-by-design, but *permanent* and
phase-independent under the current data-loading path. (This refines the
sub-agent's lean toward (a); the main-agent re-verification below is decisive.)

- The trend-structure VWAP is computed in `cuttingboard/trend_structure.py`:
  `_vwap()` returns `None` when `not _is_intraday(df)` (`:55`), and the cell is
  classified `NOT_COMPUTED` at `:134–135` — the "not applicable" string.
- **Decisive evidence — the source frame is daily-only, always.**
  `history_by_symbol` for trend-structure is built from
  `_collect_trend_structure_history(ohlcv)` (`runtime/__init__.py:549`), where
  `ohlcv` is the **daily** `fetch_ohlcv()` (6-month daily bars,
  `ingestion.py:119`). The intraday source `fetch_intraday_bars()` (1-minute,
  `ingestion.py:170`) feeds **only** entry-trigger evaluation
  (`evaluation.py:160`) and `runtime/__init__.py:1177` — **never** the
  trend-structure VWAP path. So `_is_intraday(df)` is structurally always false
  here.
- **Confirming artifact:** `logs/trend_structure_snapshot.json`
  (`generated_at` 2026-06-12T17:21:10Z) shows **every** row `"vwap": null` /
  `NOT_COMPUTED` — uniform, not a session-phase artifact.
- **Why not (a):** PRD-107 *documents* "daily bars → vwap=null" as intended, but
  that documents the gap; it does not make the cell fill during market hours. The
  source is daily regardless of phase, so the cell never changes phase-to-phase.
- **Why not (c):** cross-checked `prd-210-stage-0` — its `.py` change wires the
  PRD-174 history fallback for missing *daily* trend-structure history
  (closes-None fix); it does **not** switch the VWAP source to intraday bars. 210
  will not change the "not applicable" string.

**Triage implication:** the uniform string is *honest* under current design. It
only changes if a future PRD deliberately routes intraday bars into the
trend-structure frame — a feature decision (description-of-reality, not
prediction), not a bug to patch.

---

## STEP 3 — scoreboard source + cap site

- **Row source:** the publish-branch accumulating state
  `logs/regime_history.jsonl` (PRD-175 sidecar aggregate; PRD-194 publish-branch
  authority; PRD-204 non-destructive aggregate). One row per calendar date,
  appended each run. Current count on `origin/publish`: **~11 rows**
  (2026-05-07 … 2026-06-26).
- **Render site:** `cuttingboard/delivery/dashboard_renderer.py:2441` —
  `_board_rows = list(regime_history)[-SCOREBOARD_LIMIT:][::-1]`, with
  `SCOREBOARD_LIMIT = 10` at `:174` (PRD-177 R4).
- **Two candidate cap sites for ~5:**
  - **A — RENDER-TIME SLICE (MICRO, recommended).** Change `SCOREBOARD_LIMIT`
    `10 → 5` at `dashboard_renderer.py:174`. Display-only; the slice at `:2441`
    already exists. No state write. Mirrors the PRD-195 dual-cap pattern (storage
    cap ≠ display cap).
  - **B — ACCUMULATING-STATE TOUCH (riskier).** Prune rows before
    `_write_history(...)` in `cuttingboard/delivery/regime_history.py:264`.
    Mutates the authoritative publish-branch archive; lossy; breaks the
    append-only model. Not recommended.
- **Recommendation:** target **Site A** — a one-line MICRO, display-only, fully
  reversible, leaves the full archive intact on `publish`.

---

## Triage summary — decisions teed up

1. **SMA numbering (208).** Revive-208 **in place** (number, PRD doc, and
   SHA-pinned `b42ec9a` Codex review all already exist). Renumber only if a
   strict contiguous close order is wanted. Implementation is still unwritten —
   reviving means *building* `_trend_structure_composite_display`, not just
   merging.
2. **Cluster close order.** 205 (tooling), 206 (governance, manual-merge-only),
   208 (HIGH-RISK dashboard, review pre-satisfied), 209 (HELD — leave parked),
   210 (IMPLEMENTED + fully reviewed — closest to merge-ready). 207 is a free
   gap. Decide whether to drive 210 to merge first (most mature) or honor numeric
   order.
3. **VWAP cell.** No fix indicated. If the uniform "not applicable" is
   *unwanted*, that is a new feature (route intraday bars into trend-structure),
   not a defect — scope a PRD, don't patch.
4. **Scoreboard ~5 cap.** One-line MICRO at `dashboard_renderer.py:174`
   (`SCOREBOARD_LIMIT = 5`). No PRD needed beyond the established pattern; confirm
   the desired count.

**STOP — held for triage. No scope, no build, no Codex dispatch.**
