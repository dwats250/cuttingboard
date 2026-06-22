# Dashboard render/logic recon — 2026-06-22

Recon-only pass. No feature code touched. Each lead was adjudicated against
source; screenshots treated as leads, not findings. File:line citations are the
proof. Verdicts: **confirmed bug / works-as-designed / cosmetic / spec-gap /
can't-determine**.

Method: five parallel `Explore` sweeps + main-context re-verification of the
single decisive call for each correctness claim (CLAUDE.md sub-agent
re-verification discipline). The Lead-1 verdict below **corrects** the first
sweep's "works-as-designed" read, which only explained the most-recent row.

---

## Lead 1 — Scoreboard "SPY next" goes all-`n/a` on Sunday — **CONFIRMED BUG (correctness)**

**Verdict:** confirmed bug. Not a stale capture, and not the benign "next
session's close doesn't exist yet" the first sweep proposed (that explains only
the *latest* row, not historical 05-13 / 06-17). The whole column drops because
the Sunday publish run **rebuilds the committed scoreboard from an empty SPY
cache and overwrites the good values with `None`.**

**Call chain / proof:**

- Render + `n/a`: `cuttingboard/delivery/dashboard_renderer.py:2439-2446`
  → `_fmt_pct_signed` returns `"n/a"` for non-finite input
  (`dashboard_renderer.py:1015-1020`).
- Value source: `logs/regime_history.jsonl`, field `spy_close_change_pct`,
  written by `regime_history.aggregate()`
  (`cuttingboard/delivery/regime_history.py:118-145`). `aggregate()` is a **full
  destructive rebuild** — `_write_history(...)` at `:144` overwrites the file,
  recomputing every row's `spy_close_change_pct` from `spy_closes`.
- `spy_closes` comes from `_load_spy_close_series()`
  (`regime_history.py:69-88`), which **silently returns `[]`** when
  `data/cache/SPY_ohlcv.parquet` is missing (`:74-76`). Empty series →
  `_next_session_change()` returns `None` for *every* date
  (`regime_history.py:91-104`, `:96` `date not in dates`).
- The cache is missing on Sunday because **the entire OHLCV-fetch block is
  session-gated**: `runtime/__init__.py:705` `if mode != MODE_SUNDAY:` wraps the
  only `fetch_ohlcv(...)` calls (`runtime/__init__.py:741-745`; lightweight path
  `:409-412`, `:432-435`). Sunday mode leaves `ohlcv = {}` (`:668`) and never
  writes a parquet.
- The parquet does not survive across runs: `data/cache/*.parquet` is gitignored
  ("regenerated at runtime", `.gitignore`), the Commit step stages only
  `reports/ logs/ ui/` (`cuttingboard.yml:264-270`), and **no `actions/cache`**
  restores it (verified: zero hits for `actions/cache` in `.github/workflows/`).
- The destructive rebuild then runs on Sunday: `cuttingboard.yml:263`
  (`python3 -m cuttingboard.delivery.regime_history`) inside the Commit step,
  which fires for both `live` and `sunday` (`:250-252`, `PUBLISH_READY=true`).
  Sunday's `SUNDAY_PREMARKET` is in `INACTIVE_SESSION_TYPES`, so the PRD-119
  freshness gate is relaxed and the clobbered scoreboard publishes.

**Net effect:** Friday's `live` run commits a good `regime_history.jsonl`
(returns populated). Sunday's run checks it out, rebuilds it from `audit.jsonl` +
an empty SPY series, writes `None` everywhere, renders `n/a` for all rows, and
publishes that to the `publish` branch. Self-heals on Monday's `live` run. A
real, weekly, published-artifact regression.

**Type:** code bug **+** doc/code drift. The `aggregate()` docstring
(`regime_history.py:124-129`) claims the rebuild "is idempotent by construction…
a prior day gains its reference move once the next session's close exists." When
the parquet is absent the rebuild does the **opposite** — a prior day *loses* its
already-computed move. This is a PRD-198 invariant #1 violation
(silent-fallback: `:76` returns `[]` and `aggregate` writes `None` rather than
failing loud or preserving prior truth).

**Blast radius:** `logs/regime_history.jsonl` (committed), the published
dashboard scoreboard, every historical row. Overlaps the *known* deferred
debt **PRD-193** ("data/cache doesn't persist… no actions/cache") — but PRD-193
is scoped to the **prefetch** slot and says nothing about the Sunday destructive
rebuild. The correctness defect (overwrite-good-with-None) is **not** captured by
any open PRD.

---

## Lead 2 — Contra-cyclical rationale captions are direction-blind — **CONFIRMED BUG (correctness); already scoped as PRD-191**

**Verdict:** confirmed. The vote is direction-aware and correct; the italic
caption is a static per-driver string with no direction term.

**Proof:**
- Static caption map: `cuttingboard/delivery/macro_tape_layout.py:87-94`
  (`MACRO_BIAS_INTERPRETATION`: `"rates": "easing yields favor risk"`, etc.) —
  one string per driver, no rising/falling form.
- Caption lookup ignores direction: `dashboard_renderer.py:2094`
  `_interp = MACRO_BIAS_INTERPRETATION.get(_slot.payload_key, "")`.
- Vote IS direction-aware: `dashboard_renderer.py:2081-2093` — arrow ±
  contra-cyclical flip (`MACRO_BIAS_CONTRA_CYCLICAL`, `macro_tape_layout.py:78`),
  "no vote" when flat. Underlying classifier confirms sign inversion
  (`macro_pressure.py:66-77`).
- The two are decoupled: vote reads `_arrow`/`_risk_on`; caption reads only
  `payload_key`. On a rising 10Y: vote = risk-OFF (correct), caption = "easing
  yields favor risk" (implies risk-ON) — visible contradiction. Same for rising
  VIX and rising DXY.
- Guard gap: `test_prd177_r3_macro_evidence_rows_present`
  (`tests/test_dashboard_renderer.py:3553-3554`) only asserts the caption is
  non-empty, so an inverted caption passes CI.

**Type:** code bug. **Already drafted as PRD-191** (PROPOSED, HIGH-RISK, MINIMAL
SCOPE, FILES + RED-test requirement complete). No new PRD — implement PRD-191.

**Blast radius:** `macro_tape_layout.py` (one map), `dashboard_renderer.py:2094`
(one lookup), one test. PRD-191's grep sweep confirms `MACRO_BIAS_INTERPRETATION`
has exactly one consumer.

---

## Lead 3 — Empty "SUNDAY PRE-MARKET CONTEXT — NO CASH SESSION" card — **WORKS-AS-DESIGNED (spec gap / decision)**

**Verdict:** works-as-designed; not a stub-with-missing-body and not redundant in
code. Whether the title-only banner *should* exist next to the populated card is
a presentation decision, not a bug.

**Proof:**
- Title-only banner by design: `dashboard_renderer.py:1851-1854` emits only an
  `<h2>` inside `#premarket-banner` (per PRD-077 R5: banner, "no other layout
  changes").
- Populated card: `dashboard_renderer.py:2009-2032` (`#sunday-macro-context`),
  fed by `_build_sunday_context()` (`:1335-1387`) which guarantees every field
  non-`None` via fallbacks ("unavailable"/"flat"/"UNKNOWN") — body is never
  empty (per PRD-080).
- Both gated identically by `sunday_coherent` (`:1813-1817`); test
  `test_prd116_r8_coherent_sunday_renders_sunday_blocks` asserts both render.

**Type:** spec gap. **Open decision for Dustin** (below).

---

## Lead 4 — No absolute capture/run timestamp in the render — **CONFIRMED (cosmetic / enhancement)**

**Verdict:** confirmed. Only relative freshness tokens are rendered.

**Proof:**
- RUN SNAPSHOT: `dashboard_renderer.py:1965-1972` →
  `_run_snapshot_freshness_token` (`:256-273`) returns `"<1 min old"` /
  `"N minute(s) old"` / `"STALE (>5 min)"` — never a wall-clock time.
- LIVE STATE: `:1987-1989` → `_surface_age_token` (`:276-294`) returns relative
  ages only.
- An absolute-timestamp formatter **exists but is unused** by this renderer:
  `format_dashboard_timestamp()` (`:210-231`, "YYYY-MM-DD HH:MM:SS PT"), called
  only from `html_renderer.py`. Natural attach point: the System State block
  beside the relative token (`:1971-1992`).

**Type:** presentation/enhancement (spec choice — relative-only may be
deliberate). Decision for Dustin whether to add it.

---

## Lead 5 — LIVE STATE staleness not visually flagged — **CONFIRMED (correctness / observability gap)**

**Verdict:** confirmed gap. 34 min is well past the 5-min staleness threshold,
yet LIVE STATE renders identically to fresh data.

**Proof:**
- Threshold: `DASHBOARD_STALE_AFTER_SECONDS = 300` (`dashboard_renderer.py:175`).
- RUN SNAPSHOT emits a `"STALE (>5 min)"` **text** token past threshold
  (`:256-273`) — but applies **no CSS class** (`:1965-1972`, `class="value"`
  only).
- LIVE STATE has **no staleness branch at all**: `_surface_age_token`
  (`:276-294`) just returns `"34 min old"` for sub-hour ages; rendered with
  `class="value"` (`:1987-1989`). No `.warn`/`.halted` applied, though both
  classes exist (`:655-656`) and are used elsewhere.
- The `_ts_health` freshness gate (`:1881-1887`) governs the **Trend Structure**
  source, **not** the System State surface — so it is genuinely not wired to
  LIVE STATE. Confirmed by `test_prd189_frozen_pipeline_reads_stale_per_surface`
  (`tests/test_dashboard_renderer.py:757-776`), which asserts plain-text age.

**Type:** code gap (observability/correctness). The PRD-189 "loudly stale by the
age value itself" design works for >1h ages but leaves the 5–60 min window
visually indistinguishable from fresh.

**Blast radius:** System State block only (`:1965-1992`), `_surface_age_token`.

---

## Lead 6 — Mobile horizontal overflow — **CONFIRMED (cosmetic / CSS)**

**Verdict:** confirmed for MACRO PRESSURE; marginal for Trend Structure.

**Proof:**
- **MACRO PRESSURE summary overflow:** `.pressure-grid` uses
  `grid-template-columns: max-content max-content max-content max-content`
  (`dashboard_renderer.py:707`) — four non-wrapping fixed columns. At phone
  width the row exceeds the viewport with no wrap/scroll affordance. Real
  overflow.
- **Trend Structure rightmost column:** the table is
  `display:block;overflow-x:auto` (`:2204-2206`) with 10 `white-space:nowrap`
  cells (`:2269`). It is technically horizontally scrollable, so the rightmost
  column (Intraday Context / SMA Composite) is *off-initial-viewport*, not truly
  clipped — but there is no visible scroll affordance, so it reads as a clip.
  Page is constrained by `.wrap{max-width:640px}` (`:639`).

**Type:** presentation/CSS only.

---

## Lead 7 — XAU/XAG/OIL header-only; ETF arrows unlabeled — **WORKS-AS-DESIGNED + minor wiring/UX gap**

**Verdict:**
- XAU/XAG/OIL **decorative by design — confirmed.** Header rows
  `macro_tape_layout.py:22-39` include XAU/XAG/OIL; vote-casting drivers are only
  volatility/dollar/rates/bitcoin (`macro_pressure.py:18-30`); module comments
  state spot metals + oil are "visibility-only, deliberately excluded from the
  bias arithmetic" (`macro_tape_layout.py:71-77`, `macro_pressure.py:14-18`; per
  PRD-122/PRD-160). Correctly absent from the ETF grid, which carries GLD/SLV
  ETFs not the GC=F/SI=F futures (`macro_tape_layout.py:41-51`).
- ETF arrow reference period **unlabeled — minor gap.** Arrow = sign of
  `daily_change_pct` = (current − prior close)/prior close
  (`trend_structure.py:250-256` → `ingestion.py:294-302` → `_pct_arrow`
  `dashboard_renderer.py:1007`). The baseline is **prior close**, but no label,
  tooltip, or `title`/`aria-label` surfaces it (per PRD-199).

**Type:** XAU/XAG/OIL = no action (by design). Arrow label = spec gap / UX
decision.

---

## Scoping recommendation

Correctness and presentation are kept unbundled per CLAUDE.md ("don't bundle a
correctness fix with a CSS fix").

### Correctness (do these)
1. **PRD-191 — direction-aware captions (Lead 2).** Already drafted, HIGH-RISK,
   minimal scope, RED-test required. **Implement as-is. Sequence first** — clean,
   pre-reviewed, self-contained.
2. **Lead 1 — Sunday scoreboard destructive wipe.** Highest severity (corrupts a
   published artifact weekly). Two independent fixes; the second stands alone and
   fixes the published regression even without cache work:
   - (a) **Cache persistence** so Sunday has a SPY parquet — this is
     **PRD-193's** territory (already PROPOSED).
   - (b) **Non-destructive / fail-loud aggregate** — when `_load_spy_close_series`
     is empty, do not overwrite populated `spy_close_change_pct` with `None`
     (preserve prior, or fail loud per PRD-198 invariant #1). Small, independent
     of (a).
   **Open decision for Dustin (below):** fold (b) into PRD-193, or open a small
   standalone "non-destructive scoreboard aggregate" correctness PRD. *Recommend
   standalone* — it is independent of the prefetch/cache redesign and fixes the
   visible regression immediately.
3. **Lead 5 — LIVE STATE staleness flag.** Small observability PRD: wire a
   staleness threshold + `.warn` styling to `_surface_age_token`/the System State
   block. *Optionally bundle with Lead 4* — both touch the same freshness/time
   surface and neither is a CSS-layout change (Lead 4 is a render addition, not
   styling), so they coexist cleanly as a single "System State freshness surface"
   PRD without violating the no-CSS-bundling rule.

### Presentation (separate lane)
4. **Lead 4 — absolute timestamp** (if Dustin wants it) — render-addition; see
   bundling note above.
5. **Lead 6 — mobile overflow** — pure CSS PRD: make `.pressure-grid` wrap (or
   `auto-fit`/`minmax`) and add a scroll affordance to the Trend Structure table.
   Keep standalone — pure CSS, no correctness coupling.

### Spec gaps — decisions for Dustin (no PRD until decided)
- **Lead 3:** Keep the title-only Sunday pre-market banner above the populated
  Macro Context card, or collapse/merge them? (Code is correct either way.)
- **Lead 7 (arrow label):** Add a labeled reference period ("vs prior close") to
  the ETF/macro-tape arrows, or accept the unlabeled glyphs? (XAU/XAG/OIL
  decorative status needs no change.)

### Suggested sequence
PRD-191 → Lead 1(b) standalone correctness PRD → Lead 5 (+maybe Lead 4) →
Lead 6 CSS → (PRD-193 cache work + Lead 1(a) on its own cadence). Spec-gap
decisions (3, 7) gate their own small PRDs.

---

## Drift called out
- **`regime_history.aggregate()` docstring vs behavior** (`regime_history.py:124-129`):
  claims idempotent gain-only rebuild; actually destroys prior returns when the
  SPY parquet is absent. Doc/code drift + PRD-198 invariant #1 (silent fallback).
- **PRD-193 scope vs Lead 1:** PRD-193 knows the cache doesn't persist but frames
  it as a prefetch-efficiency problem; it does not capture the Sunday
  published-scoreboard correctness regression. The destructive-rebuild defect is
  currently un-owned.
- No new prediction logic, no undocumented sidecar, no VISION non-goal conflict
  surfaced in any lead (VISION alignment intact for the audited paths).
