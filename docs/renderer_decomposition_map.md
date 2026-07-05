# MASTER-PLAN ITEM M — Renderer Decomposition Design Doc (DESIGN ONLY)

**Provenance:** produced under PRD-238 (2026-07-04) by a fresh-context read
of the module at `main` commit `5ebc7c9` (post-PRD-237). Line numbers are
pinned to that SHA; PRD-238's own J2 edit already shifts them slightly
(+1 after the import block, +5 after `_load_contract_entry_context`'s
head), and K/L will shift them further — the re-verify checklist at the
bottom is mandatory before execution. Load-bearing claims re-verified by
the main agent at authoring time: the five dead params + dead
`resolved_market_map_source` block + dead `_sys_health`/`_tape_health`/
`_mm_health`/`_mm_setup_count` locals (single decisive `rg`), and the
`tests/preview_fixtures.py::SECTION_STATE_CASES` corpus location.

**Target:** `cuttingboard/delivery/dashboard_renderer.py` (2,880 lines)
**Focus symbol:** `render_dashboard_html` — `dashboard_renderer.py:1785-2623` (~839 body lines).
**Master-plan cell:** MASTER_PLAN.md:364-366 — *"M (≈239+) — Renderer decomposition: RenderContext object replaces the 22-kwarg signature; per-section render functions. CONSUMER, split into 2–3 PRDs, byte-identical check per stage. Do LAST."*
**Audience:** Dustin + a future Opus session executing K / L / M.
**Status:** Design only. No repo file is modified by this document. All line numbers are current-as-read and MUST be re-verified at execution (the file will have shifted under K/L and PRD-238 J2 by then).

> **Signature-count correction.** The audit prose (mentor-review.md:79, LEARNING_COMPANION.md:171) says "22 kwargs." The **actual** signature (`:1785-1807`) is **20 parameters**: 2 positional (`payload`, `run`) + 18 keyword-only. Use 20 as the real number; the "22" is a rounding in the audit.

---

## 0. Ground truth read from the module

- The function is a **two-phase** function: a **prologue** (`:1812-1985`, pure computation + one file-I/O fallback) that derives ~40 locals, followed by a **linear HTML-accumulation** phase (`:1987-2621`) that appends to a single `lines: list[str]` via a closure `w()` and returns `"\n".join(lines)`.
- **No mutable module-level state.** Every module global is an immutable lookup table / constant (`_GRADE_ORDER`, `_GRADE_CSS`, `_HIGH_GRADES` frozenset, `_TIER_DEFS`, `_CSS`, `_ARROW_CSS`, `_SYS_VERDICT_CLS`, `_POSTURE_LABELS`, `_PT` zoneinfo, the `_*_PATH` Path constants, etc.). No caches, no `lru_cache`, no `global`, no dedup store. This is the clean contrast to item **L** (`output.py` module globals). The renderer's decomposition therefore has **no shared-state hazard** of its own.
- The `CHAIN UNVERIFIED` block the task names is **NOT in this module** — it lives in `cuttingboard/output.py:309,376` (the notification path). It is a *sibling consumer of the same contract artifact* the renderer reads (`logs/latest_hourly_contract.json`). See Hazard H5.

---

## 1. RenderContext design

### 1.1 The 20 parameters (signature `:1785-1807`)

| # | param | type | default | kind |
|---|-------|------|---------|------|
| 1 | `payload` | `dict` | — | positional |
| 2 | `run` | `dict` | — | positional |
| 3 | `previous_run` | `dict \| None` | None | kw |
| 4 | `history_runs` | `list[dict] \| None` | None | kw |
| 5 | `market_map` | `dict \| None` | None | kw |
| 6 | `market_map_path` | `Path \| None` | None | kw |
| 7 | `macro_snapshot_path` | `Path \| None` | None | kw |
| 8 | `contract_entry_map` | `dict \| None` | None | kw |
| 9 | `contract_stop_map` | `dict \| None` | None | kw |
| 10 | `alert_candidates` | `list[dict] \| None` | None | kw |
| 11 | `contract_generated_at` | `object \| None` | None | kw |
| 12 | `payload_source` | `str \| Path` | `_PAYLOAD_PATH` | kw |
| 13 | `run_source` | `str \| Path` | `_RUN_PATH` | kw |
| 14 | `market_map_source` | `str \| Path \| None` | None | kw |
| 15 | `contract_source` | `str \| Path` | `_HOURLY_CONTRACT_PATH` | kw |
| 16 | `trend_structure_snapshot` | `dict \| None` | None | kw |
| 17 | `regime_history` | `list[dict] \| None` | None | kw |
| 18 | `red_folder` | `dict \| None` | None | kw |
| 19 | `pipeline_run` | `dict \| None` | None | kw |
| 20 | `fixture_mode` | `bool` | False | kw |

### 1.2 kwarg → section usage matrix (built by reading the body)

Sections abbreviated: **PRO**=prologue compute · **SYS**=system-state · **ALW**=alert-watchlist · **SUN**=sunday-macro-context · **TAP**=macro-tape(+tradables) · **RF**=red-folder · **TS**=trend-structure · **CB**=candidate-board · **RD**=run-delta · **SB**=scoreboard.

| param | consumed at | sections | notes |
|-------|-------------|----------|-------|
| `payload` | 1829-1846,1884-1904,1973 | PRO, SYS, TAP, SUN | timestamp, market_regime, generation_id, validation_halt→stay_flat_reason, macro_drivers, permission fallback, session_type |
| `run` | 1830-1847,1896-1905,2121,2476,2564-2576 | PRO, SYS, CB, RD | status/system_halted/kill_switch/errors/outcome/permission/regime/posture; run_timestamp label in CB STALE branch; pipeline_run fallback |
| `previous_run` | 2558-2576 | RD | **only** consumer (regime flip, posture Δ, system_halted Δ) |
| `history_runs` | — | **NONE** | **DEAD in body.** Passed through signature (`:1790`) but never read. See H6. |
| `market_map` | 1813-1848,1909-1955,2020,2055,2082-2085,2148,2176,2459-2502,2544 | PRO, SYS, SUN, TAP, CB | resolution+status, lineage gen-id, integrator input, `_hg_count`, tape values, tiers/removed_symbols, fixture override |
| `market_map_path` | 1815-1823 | PRO | `_resolve_market_map()` when `market_map` is None (I/O in helper) |
| `macro_snapshot_path` | 1893 | PRO | `_load_macro_snapshot()` fallback — **FILE I/O inside render** (H2) |
| `contract_entry_map` | 1881-1882,2537 | PRO, CB | nulled if `contract_stale_for_run`; per-card `contract_entry` |
| `contract_stop_map` | 2538 | CB | per-card `contract_stop` (risk band pairing) |
| `alert_candidates` | 2098,2133-2137 | SYS, ALW | "candidates gated" ctx reason; the whole ALW section |
| `contract_generated_at` | 1845 | PRO | `contract_timestamp` → `contract_stale_for_run` gate |
| `payload_source` | — | **NONE** | **DEAD in body.** Signature `:1798` only. H6. |
| `run_source` | — | **NONE** | **DEAD in body.** Signature `:1799` only. H6. |
| `market_map_source` | 1820-1827 | PRO(dead) | Computes `resolved_market_map_source`, which is itself **never read**. Whole block dead. H6. |
| `contract_source` | — | **NONE** | **DEAD in body.** Signature `:1801` only. H6. |
| `trend_structure_snapshot` | 1908,2028-2048 | PRO, TAP, TS | tape arrows, `_ts_records`/`_ts_health`/`_ts_generated_at_raw`; tradables arrow gate |
| `regime_history` | 2596-2597 | SB | **only** consumer |
| `red_folder` | 2294-2314 | RF | **only** consumer |
| `pipeline_run` | 2121-2124 | SYS | UPDATED timestamp (PRD-189 pipeline source) |
| `fixture_mode` | 2018-2022,2443 | PRO, CB | market_map FIXTURE_SYMBOLS override; DEMO MODE header |

**Findings that shape the RenderContext:**
- **5 of 20 params are dead in the body**: `history_runs`, `payload_source`, `run_source`, `market_map_source`, `contract_source`. They do not affect a single output byte. RenderContext may omit them (or retain as inert provenance fields). Dropping them is a *code* change, not an *output* change — byte-identity is unaffected. Recommend: **keep them out of RenderContext's render-consumed surface; if kept for provenance, mark them clearly inert.** (`market_map_source` also drags the dead `resolved_market_map_source` block `:1820-1827` — remove together.)
- **7 params are single-section consumers** (`previous_run`→RD, `regime_history`→SB, `red_folder`→RF, `contract_stop_map`→CB, `pipeline_run`→SYS, and the two source-of-truth pairs). These are the natural leaves for per-section extraction — a section fn takes exactly its slice.

### 1.3 Proposed frozen dataclass — grouped sub-contexts

Group by cohesion (each sub-context = the inputs one cluster of sections reads). All frozen; renderer already promises "No payload or run mutation" (`:1810`).

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class RunMeta:            # identity + freshness of the run itself
    payload: dict
    run: dict
    previous_run: dict | None = None
    pipeline_run: dict | None = None
    contract_generated_at: object | None = None

@dataclass(frozen=True)
class MarketData:         # the market-map + macro + trend inputs
    market_map: dict | None = None
    market_map_path: Path | None = None          # resolution seam (I/O in helper)
    macro_snapshot_path: Path | None = None       # fallback I/O
    trend_structure_snapshot: dict | None = None

@dataclass(frozen=True)
class DecisionData:       # contract-derived, decision-bearing (see H4)
    contract_entry_map: dict | None = None
    contract_stop_map: dict | None = None
    alert_candidates: list[dict] | None = None

@dataclass(frozen=True)
class HistoryData:        # scoreboard + red-folder sidecars
    regime_history: list[dict] | None = None
    red_folder: dict | None = None

@dataclass(frozen=True)
class RenderContext:
    run_meta: RunMeta
    market: MarketData
    decision: DecisionData
    history: HistoryData
    fixture_mode: bool = False
    # Inert provenance (dead in body today — see §1.2). Keep OR drop; no byte impact.
    # history_runs / payload_source / run_source / market_map_source / contract_source
```

Rationale for the grouping: it mirrors the **section clusters** in §2, so each extracted section fn takes exactly one sub-context (`render_scoreboard(ctx.history, w)`, `render_run_delta(ctx.run_meta, w)`), never the whole 20-field bag. The prologue's derived-locals bundle (lineage state, `_ts_health`, integrator result, macro-bias, tape slots) is a SEPARATE, computed **`DerivedState`** object built once from RenderContext — see §2's "Derived block."

### 1.4 Constructor seam — who builds RenderContext

**Every runtime + test call site of `render_dashboard_html` (repo-wide):**

Runtime (production) path — one chain:
- `python3 -m cuttingboard.delivery.dashboard_renderer` → `main()` (`:2779`) → `write_dashboard()` (`:2626`) → `render_dashboard_html()` (call at `:2665`).
- Invoked by: `.github/workflows/hourly_alert.yml:145`, `.github/workflows/cuttingboard.yml:327`, `.github/workflows/dashboard_preview.yml:73`, `scripts/preview_dashboard.sh:28`.

Preview-corpus harness (the byte-identity oracle):
- `scripts/preview_fixtures.py:53` → `render_dashboard_html(case.payload, case.run, market_map=…, fixture_mode=…, **case.render_kwargs)`.

Tests calling `render_dashboard_html` / `write_dashboard` directly (kwarg façade must survive or be migrated):
- `tests/test_preview_fixtures.py:45`, `tests/test_dash_macro.py:39,44,52`, `tests/test_dash_boundary.py:43,52`, `tests/test_dash_candidates.py` (≈14 calls: `:18,23,30,44,55,71,78,93,107,120,127,148,172,186`), plus other `tests/test_dash_*.py` under the same import. (Full enumeration lives in the persisted grep result; the executing session re-runs the grep.)

**Seam recommendation:** introduce `RenderContext` as an ADDITIVE overload, do NOT break the kwarg call convention in the same PR.
- Add `render_dashboard_html(ctx: RenderContext, w=None)` as the new core, and keep the current 20-kwarg signature as a thin **adapter** that builds a `RenderContext` from kwargs and delegates. `write_dashboard` and `main()` keep passing kwargs (or migrate to build `RenderContext` directly — a later, separate PRD). Tests keep working untouched. This preserves byte-identity trivially (the adapter reconstructs today's exact locals) and lets the section-extraction stages proceed independently of the call-convention swap.

---

## 2. Ordered seam map

### 2.1 Structure of the body (section-by-section)

Two phases. **Prologue (compute)** `:1812-1985` and **derived source-health block** `:2024-2057` produce locals; the emit phase `:1987-2621` appends HTML.

| id | section | line range | inputs consumed | pure? | cross-section deps (produced→consumed) |
|----|---------|-----------|-----------------|-------|----------------------------------------|
| **PRO** | prologue compute | 1812-1966 | payload, run, market_map(+path), macro_snapshot_path, contract_generated_at, trend_structure_snapshot | **impure** (I/O: `_resolve_market_map` at 1816, `_load_macro_snapshot` at 1894) | produces: `_mm_status`, lineage (`artifact_lineage_state`,`unhealthy_lineage`,`disabled_class`), `contract_stale_for_run` (nulls `contract_entry_map`!), `macro_drivers`, `tape_slots`/`tape_value_slots`/`pressure`, `long_votes`/`short_votes`/`macro_bias(_css)`, `integrator_result`→`integrator_suppress/verdicts/skips`, `title`, run scalars |
| — | `lines`+`w()` closure | 1968-1971 | — | pure | the accumulator all sections close over |
| — | session flags | 1973-1985 | payload session_type, lineage, timestamp | pure (`_is_sunday_pt`) | `sunday_coherent`, `inactive_session` → SUN, TS, CB |
| **S0** | doc head + `.wrap` open | 1987-1997 | `_CSS`, `_DASHBOARD_REFRESH_SECONDS` | pure | — |
| **S1** | artifact-warning (MIXED) | 1999-2011 | `artifact_mixed`, gen-ids | pure | reads PRO lineage |
| **S2** | premarket-banner | 2013-2016 | `sunday_coherent` | pure | reads session flags |
| **M0** | fixture_mode mm override | 2018-2022 | fixture_mode | **mutates local `market_map`** | rebinds `market_map`, sets `_mm_status="FRESH"` for all LATER sections (H3) |
| **DRV** | source-health derived block | 2024-2057 | lineage, `_mm_status`, trend snapshot, macro_drivers, tape_value_slots | pure | produces `_ts_records`,`_ts_health`,`_ts_generated_at_raw`,`_ts_arrow_ok`(2270). **`_sys_health`,`_tape_health`,`_mm_health`,`_mm_setup_count` are computed but NEVER consumed — dead (H6).** |
| **S3** | system-state | 2059-2130 | run scalars, market_regime, `_hg_count`(market_map), alert_candidates, pipeline_run, first_error/stay_flat_reason, title | **impure**? no — pure of inputs (`format_dashboard_timestamp` pure) | reads PRO+market_map |
| **S4** | alert-watchlist | 2132-2144 | alert_candidates | pure | single-input |
| **S5** | sunday-macro-context | 2146-2169 | `sunday_coherent`, macro_drivers, market_regime, market_map (via `_build_sunday_context`) | pure | reads session flags + PRO |
| **S6** | macro-tape + tradables | 2171-2286 | macro_drivers, `macro_bias(_css)`, `integrator_suppress`, `long/short_votes`, `pressure`, `tape_slots`/`tape_value_slots`, `_ts_arrow_ok` | pure | heaviest PRO+DRV consumer |
| **S7** | red-folder | 2288-2316 | red_folder | pure | single-input |
| **S8** | trend-structure | 2318-2439 | `disabled_class`,`unhealthy_lineage`,`inactive_session`,`_ts_health`,`_ts_records`,`_ts_generated_at_raw`, `config.TREND_STRUCTURE_SYMBOLS` | pure | reads PRO+DRV |
| **S9** | candidate-board | 2441-2553 | `disabled_class`,`unhealthy_lineage`,`_mm_status`,`inactive_session`, market_map, `integrator_verdicts/skips`, `contract_entry_map`,`contract_stop_map`, fixture_mode, run_timestamp labels | pure (calls `_render_candidate_card`→`_render_level_diagram`, both pure) | reads PRO+DRV; the decision-bearing section (H4) |
| **S10** | run-delta | 2555-2587 | previous_run, run (regime/posture/system_halted) | pure | single dep (previous_run) |
| **S11** | scoreboard | 2589-2616 | regime_history, `SCOREBOARD_LIMIT` | pure | single-input |
| **S12** | `.wrap` close + `return "\n".join(lines)` | 2618-2623 | — | pure | — |

**Key extraction-order facts:**
1. Every S-section is **pure of RenderContext + the DerivedState bundle** once PRO/DRV run — EXCEPT for the ordering coupling introduced by **M0** (`fixture_mode` rebinds `market_map` at 2018-2022, BEFORE S3/S5/S6/S9 read it). Any section extraction that moves S3–S9 must receive the **post-M0** `market_map`, not the parameter. Treat M0's output as part of DerivedState.
2. PRO's `contract_stale_for_run` **nulls `contract_entry_map`** at 1881-1882. S9 must read the *nulled* value. So `contract_entry_map` cannot be handed to S9 straight from RenderContext — it flows through DerivedState.
3. The prologue's I/O (`_resolve_market_map`, `_load_macro_snapshot`) is the ONLY impurity. Isolating it into a `build_derived_state(ctx) -> DerivedState` factory makes every S-section a **pure function of `(DerivedState, w)`** — the decomposition target.

### 2.2 Extraction ORDER — 2–3 independently-mergeable / revertible stages

**FAIL condition, all stages (the shared oracle):** render the full preview corpus + healthy baseline and diff byte-for-byte against a pre-change capture. Concretely: `tests/preview_fixtures.py::SECTION_STATE_CASES` (12 cases incl. `healthy_baseline`, `candidate_no_candidates`, `trend_*`, `red_folder_*`, `sunday_premarket`, `session_inactive`, `macro_tape_no_data`, `coherence_mixed`, `lineage_missing`) rendered via `render_dashboard_html` — every case's HTML string must be **byte-identical** pre/post. This corpus is shared by `scripts/preview_fixtures.py` and `tests/test_preview_fixtures.py`, so it cannot drift (per its own module docstring). A stage FAILS if any corpus case's rendered bytes differ, or any existing `tests/test_dash_*.py` assertion changes. Add a transient golden-capture harness (render corpus → dict of strings) as the mechanical gate; discard after the stage lands.

The stages are ordered leaf-first so each is a strict superset-free slice; **earlier stages do NOT force later ones** (each is a self-contained, revertible PRD).

---
**STAGE M1 — Leaf sections (single-input, zero cross-deps).** *(PRD ≈239)*
- **Sections moved:** S4 alert-watchlist (2132-2144), S7 red-folder (2288-2316), S10 run-delta (2555-2587), S11 scoreboard (2589-2616). Optionally S1 (1999-2011) + S2 (2013-2016) trivially.
- Each becomes `def _render_alert_watchlist(alert_candidates, w)`, `_render_red_folder(red_folder, w)`, `_render_run_delta(run, previous_run, w)`, `_render_scoreboard(regime_history, w)`. Pure, no DerivedState needed.
- **Why first:** these read exactly one RenderContext leaf and no PRO/DRV derived value → smallest possible blast radius, proves the `w`-closure-passing pattern.
- **FAIL:** corpus byte-identity (above). The `red_folder_*`, `candidate_no_candidates`(unaffected), and healthy_baseline cases directly cover these branches.
- **Est. line delta:** neutral-to-slightly-negative in body (~-95 lines moved out, +~110 in new fns incl. signatures/docstrings). Net module ≈ +15.

**STAGE M2 — DerivedState + display sections.** *(PRD ≈240)*
- Introduce `@dataclass(frozen=True) DerivedState` and `build_derived_state(ctx) -> DerivedState` that runs today's PRO (1812-1966) + DRV (2024-2057) + M0 (2018-2022) verbatim, returning the exact locals (lineage, `_mm_status` post-M0, `market_map` post-M0, macro-bias, integrator result, tape slots, `_ts_*`). Then extract **S3 system-state, S5 sunday-context, S6 macro-tape+tradables, S8 trend-structure** as `def _render_X(derived, w)`.
- **Why second, why mergeable alone:** M1 does not depend on M2 and vice-versa; either can revert independently. M2 carries the I/O-isolation win.
- **FAIL:** corpus byte-identity — `macro_tape_no_data`, `trend_awaiting_data`, `trend_no_data`, `sunday_premarket`, `session_inactive` cases pin S6/S8/S5; healthy_baseline pins S3. **Extra guard:** the derived block must preserve M0/`contract_stale_for_run` ordering exactly — the golden capture catches any reorder.
- **Est. line delta:** +40 to +70 (DerivedState dataclass + factory boilerplate). This is the "gets slightly bigger before smaller" stage.

**STAGE M3 — candidate-board + RenderContext top-level assembly.** *(PRD ≈241, do LAST)*
- Extract **S9 candidate-board** (2441-2553, the decision-bearing section, H4) as `_render_candidate_board(derived, w)` (it already delegates cards to `_render_candidate_card`). Then collapse `render_dashboard_html` into: build `ctx`/`derived` → S0 → ordered `_render_*` calls → S12. Optionally introduce the `RenderContext` adapter seam from §1.4 here.
- **Why last:** S9 has the most branches (lineage/status/inactive/tier gating/removed-symbols) and touches the H4 decision semantics; move it only after the pattern is proven on M1/M2.
- **FAIL:** corpus byte-identity — `candidate_no_candidates`, `lineage_missing`, `coherence_mixed`, healthy_baseline all exercise S9 branches; the `tests/test_dash_candidates.py` ~14 assertions are the fine-grained net.
- **Est. line delta:** -10 to +20 (S9 out ≈ -113, fn back ≈ +120; the orchestrator shrinks to a readable ~60-line spine).

**Net across M1–M3:** module grows ~+50-100 lines (dataclasses + signatures), but the 839-line function collapses to a ~60-line orchestrator + ten ~40-110-line pure section fns. The *maintainability* win (each section independently testable, a real signature per section) is the goal, not raw LOC.

---

## 3. Hazards

- **H1 — closure over locals (`w`).** Every section appends via the nested `def w(line)` (`:1970-1971`) closing over `lines`. Extraction MUST pass `w` (or a list) explicitly into each section fn; `_render_candidate_card`/`_render_level_diagram` already take `w` as arg 1 — follow that exact convention. Do not return-and-join per section (would change join semantics / trailing newlines → byte diff).
- **H2 — `_load_contract_entry_context` and in-render file I/O.** `_load_contract_entry_context` (`:2691`) runs in **`main()` (`:2811`), NOT inside `render_dashboard_html`** — good, it's already outside the render flow. BUT the render flow still does I/O in the prologue: `_resolve_market_map(market_map_path)` (`:1816`) and `_load_macro_snapshot(_snap)` (`:1893-1894`) read files mid-render. These are the reason PRO is impure. M2's `build_derived_state` must keep them exactly where they are (same call order, same fallback conditions) or freshness/`_mm_status` bytes shift. Do NOT "clean up" by hoisting I/O to the caller in the same PRD — that changes which artifact wins and is a behavior change, not a refactor.
- **H3 — `fixture_mode` mutates a local (`market_map`).** `:2018-2022` rebinds `market_map` to `{**market_map, "symbols": FIXTURE_SYMBOLS}` and forces `_mm_status="FRESH"` AFTER the prologue but BEFORE S3/S5/S6/S9. Any section fn reading market_map must get the **post-override** value via DerivedState, never the RenderContext field. Miss this and fixture renders (DEMO MODE cases) diverge. `test_healthy_baseline_has_no_demo_banner` and the fixture cases guard it.
- **H4 — decision-bearing values the CONSUMER matrix forbids re-semanticizing.** The renderer is pinned **translation-only / no computation** (module docstring `:8`, DECISIONS.md:1077). The following are decision-bearing and must be **moved verbatim, never re-derived**, during extraction: `contract_stale_for_run` nulling `contract_entry_map` (`:1881-1882`); the `_render_candidate_card` risk-band gate `band_stop = contract_stop if contract_entry is not None else None` (`:1779`); the macro-bias vote tally cyclicality logic (`:1922-1944`, PRD-160); the integrator suppress/skip gating (`:1953-1966`, PRD-158); grade→action / tier ordering (`_GRADE_ORDER`, `_TIER_DEFS`, `_HIGH_GRADES`). M is a **CONSUMER-class** PRD (MASTER_PLAN.md:365) precisely because it must preserve these consumers' semantics byte-for-byte.
- **H5 — the PRD-234 CHAIN UNVERIFIED block (sibling consumer, out of scope but coupled).** `CHAIN UNVERIFIED` is emitted by `cuttingboard/output.py:309,376` (the notification/report path), reading the SAME `logs/latest_hourly_contract.json` that `_load_contract_entry_context` (`:2691`) parses for the renderer. The two paths apply the SAME entry/stop guards (bool-before-coerce, finite, >0 — renderer `:2704-2728`). **Hazard:** if M "tidies" `_load_contract_entry_context` guard logic, it can silently desync the renderer's `alert_candidates`/entry-map from output.py's CHAIN-UNVERIFIED classification. Keep `_load_contract_entry_context` OUT of M's FILES scope; M touches only `render_dashboard_html`'s body, not the contract loader.
- **H6 — dead code that must not be "helpfully" removed inside M.** Five params are unread in the body (`history_runs`, `payload_source`, `run_source`, `market_map_source`, `contract_source`); `market_map_source`'s `resolved_market_map_source` block (`:1820-1827`) is dead; and the DRV block computes `_sys_health`,`_tape_health`,`_mm_health`,`_mm_setup_count` (`:2035-2057`) that are **never consumed**. Removing them is byte-neutral for OUTPUT but is a real code change that widens the diff and invites review noise. Recommendation: **leave them exactly as-is in M** (the refactor's contract is byte-identical HTML, not dead-code cleanup); file a separate MICRO-PRD for dead-code removal so its diff is independently reviewable. If retained in RenderContext, mark inert.
- **H7 — `html.escape` discipline (`_esc`).** All user/artifact strings go through `_esc` (`:1028`, wraps `html.escape`). Section extraction must not drop, double-apply, or reorder `_esc` calls — e.g. `_tape_label_padded` (`:2227-2232`) applies `_esc` THEN pads with `&nbsp;` (order-sensitive: padding pre-escape would be escaped away). A byte diff will catch any double-escape, but reviewers should spot-check that each moved f-string keeps its exact `_esc`/raw split.
- **H8 — non-`_esc` literal HTML + CSS coupling.** `_CSS` (`:637`) is injected once in S0 (`:1994`); class names in section fns (`sys-verdict`, `macro-tape-slot`, `tier-group`, etc.) are string-coupled to it. Extraction is safe as long as literals move verbatim; do not "normalize" whitespace/attribute order in the moved lines (indentation like `'  <div ...>'` is part of the output bytes).

---

## 4. Sizing note for Opus

Each stage is scoped so **one session** can execute it under the byte-identical gate:
- **M1** — ~4 leaf functions, each a mechanical cut-paste of a single-input branch (2132-2144, 2288-2316, 2555-2587, 2589-2616). No DerivedState. A session can extract all four, wire `w`, run the corpus golden-diff, and land — comfortably inside one context window. Lowest risk; do it first to prove the harness.
- **M2** — one `DerivedState` dataclass + `build_derived_state` factory (verbatim lift of 1812-1966 + 2018-2057) + 4 display-section fns. Larger but still single-session: the factory is a copy-move (no logic change), and the 4 sections are pure of DerivedState. The golden-diff over the `trend_*`/`macro_tape_no_data`/`sunday`/`session_inactive` cases is the acceptance oracle.
- **M3** — one section fn (candidate-board, the branchiest) + the orchestrator collapse + optional RenderContext adapter. Single-session because S9 is already card-delegated (`_render_candidate_card` is untouched). `tests/test_dash_candidates.py` + corpus give a dense net.

**Execution protocol for each stage (put in the PRD):** (1) capture golden = {case.name: render(case)} over `SECTION_STATE_CASES` on the base commit; (2) perform the extraction; (3) re-render, assert every case byte-identical; (4) run `pytest tests/test_dash_*.py tests/test_preview_fixtures.py`; (5) if any diff, the stage FAILS — the extraction changed behavior. Because each stage is leaf-first and additive (adapter preserves the kwarg convention, §1.4), any stage can be reverted without disturbing the others.

---

### Re-verify-at-execution checklist (line numbers WILL move under K/L/J2)
- `render_dashboard_html` def + signature span (was 1785-1807).
- Section boundaries in §2.1 (re-grep the `# --- <name> ---` comment banners and the `w('<div class="block" id="...">` anchors).
- The 5 dead params + dead DRV locals (H6) — confirm still unread before deciding keep/drop.
- `_load_contract_entry_context` still in `main()` only, still out of render flow (H2/H5).
- Corpus case set in `tests/preview_fixtures.py::SECTION_STATE_CASES` (was 12 cases).
