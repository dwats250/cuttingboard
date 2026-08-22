# Market State Provenance Panel + Macro-Tape daily-change de-duplication — MATERIAL PACKET (v0.1, PROVISIONAL)

**Status: PROVISIONAL — NOT REVIEW-CLEAN — NO IMPLEMENTATION AUTHORITY —
awaiting Codex INITIAL PACKET REVIEW (GOV-2 Event-1).**
This is the initial provisional MATERIAL packet (GOV-2 §2 step 2) for a new
hourly-first, provenance-first MARKET STATE presentation block bundled with the
Macro-Tape tradables daily-change-arrow de-duplication, authored against Dustin's
2026-08-22 owner ruling ("BUILD; owner rulings 1-10"). All FILES/LOC are
`ESTIMATED SURFACE — NOT YET APPROVED` (GOV-2 §5). No PRD-312 allocated; no
implementation performed. Gate A is neither requested nor granted.

**Code baseline `main` @ `731b5ee` (== origin/main, clean tree).** Every carrier,
cadence, and cut fact below is verified against source at this SHA (§16).

---

## 0. GOV-2 order

```
Stage-0 product report (REVISE-then-BUILD) ............ DONE (2026-08-22)
owner design ruling (BUILD; rulings 1-10; 3 corrections) DONE (2026-08-22)
provisional MATERIAL packet (this v0.1) ............... DONE   <-- HERE
author self-verification (GOV-2 §3) ................... DONE (§16)
Codex INITIAL PACKET REVIEW (Event-1) ................. PENDING
one consolidated author correction (GOV-2 §2 step 4) .. PENDING
exact-corrected-head confirmation (Event-2) ........... PENDING
Dustin design-direction ruling ....................... PENDING
Stage-0 PRD-312 -> independent PRD review -> Gate A .... PENDING
```

MICRO-ineligible (MATERIAL, GOV-2 §1). Rides **HIGH-RISK** (`dashboard_renderer.py`
is a HIGH-RISK file for CLASS CONSUMER; owner Correction 2; PRD-121 R11).

---

## 0.1 Owner rulings governing v0.1 (Dustin, 2026-08-22)

Three corrections to the Stage-0 report + ten product rulings, restated as binding:

- **Correction 1 (CADENCE).** ENVIRONMENT and PERMISSION ARE available on the
  hourly path — the Stage-0 report wrongly called them full-run-only. Verified:
  `_execute_notify_run` runs `fetch_all` -> `normalize_all` -> `validate_quotes`
  -> `compute_regime` when not halted, and the hourly summary/contract carry
  regime + permission (§3, §16 [C1]).
- **Correction 2 (LANE).** CLASS = CONSUMER; `dashboard_renderer.py` is a
  HIGH-RISK file for CONSUMER under the canonical CLASS matrix; therefore
  **LANE = HIGH-RISK**. STANDARD is not permitted.
- **Correction 3 (MATERIALITY).** No additive-only STANDARD/non-MATERIAL
  shortcut. This slice is MATERIAL. Triggers = the new cross-surface
  delivery/dashboard presentation seam + the completeness/consumer claims
  required to de-duplicate the existing daily-change reader. Materiality does
  NOT depend on whether the arrow cut is bundled (§2, §13).
- **Ruling 1 — new thin block; do NOT reopen PRD-289.** Build a NEW Market State
  provenance block. The frozen Market Control Card contract is not mutated.
- **Ruling 2 — bundle the arrow cut, but re-prove the final-reader claim.** The
  packet must independently falsify the final-reader claim before authorizing
  removal (done, §4.2 / §16 [C-CUT]). If confirmed: remove the tradables-arrow
  branch + the now-orphaned `trend_structure.daily_change_pct` producer + update
  asserting tests. Preserve Trend-Structure `price_vs_vwap` and alignment.
- **Ruling 3 — hourly-first composition.** The panel must remain useful on the
  normal hourly published board. Target axes: ENVIRONMENT, PERMISSION, INTRADAY,
  POSITIONING, PARTICIPATION, EVENT RISK. Each row = value OR honest unavailable.
  No fake all-six fully-populated synchronous snapshot.
- **Ruling 4 — ENVIRONMENT/PERMISSION provenance.** Use the current hourly run's
  regime/permission semantics and the run/capture clock honestly. Do NOT add a
  new serialized regime timestamp.
- **Ruling 5 — INTRADAY carrier.** Prefer the hourly Trend-Structure
  `price_vs_vwap` if it truthfully supplies SPY vs-VWAP (it does, §4.3). Build no
  new producer. If it could not, state the exact reason and use the smallest
  existing alternative.
- **Ruling 6 — POSITIONING.** Existing GEX semantics only; keep its own
  fetched/as-of clock and delayed-source qualifier; absent/suppressed GEX ->
  POSITIONING unavailable.
- **Ruling 7 — PARTICIPATION.** Existing Market Movement semantics only; use its
  `generated_at` capture clock; absent/suppressed movement -> PARTICIPATION
  unavailable. No age-gate work.
- **Ruling 8 — EVENT RISK.** Existing red-folder/render-time schedule semantics;
  do not invent a feed capture timestamp where none exists.
- **Ruling 9 — provenance contract.** Make heterogeneous provenance LEGIBLE; must
  NOT imply six independent data clocks. Honest provenance type per axis:
  run/captured clock; observed bar time; fetched time + delayed qualifier;
  render-time/static-calendar; unavailable. No single global "as of" implying
  synchronous state.
- **Ruling 10 — absolute cuts.** No composite score, bullish/bearish verdict,
  weighted confluence, prediction, trade-permission mutation, new provider, new
  producer, new schema merely to obtain timestamps, movement age-gate,
  freshness-repair, or maintenance/hygiene work.

---

## 1. Product question and outcome

A read-only **MARKET STATE** block, rendered on the normal hourly published
board, that co-locates six independent market-state axes so they are legible in
one glance WITHOUT collapsing them into a score and WITHOUT implying a single
synchronized as-of. Each axis row shows an existing value (or an honest
`unavailable`) plus that axis's honest provenance clock. The block's genuine
value is (a) co-locating freshness into one read and (b) exposing provenance for
the axes that currently hide it (regime, permission) alongside the one axis whose
clock genuinely diverges from the run (GEX, a ~15m-delayed Cboe fetch).

Bundled with it: the Macro-Tape tradables **daily-change arrow** is cut as a
genuine duplicate of the Market Movement card's signed value (§4). The arrow's
sole data producer (`trend_structure.daily_change_pct`) is then removed. The
tradables PRICE tape and notifications tradables block are PRESERVED.

No new production data. No new fetch, artifact, schema surface, cadence, or
decision coupling. Description, not prediction.

---

## 2. Intake classification (GOV-2 §1)

**MATERIAL: YES** (owner Correction 3; unconditional). Triggers, each matched:
- **New cross-surface presentation seam** — the panel composes six carriers from
  six distinct producers (regime, permission, trend-structure snapshot, GEX
  snapshot, watchlist snapshot, red-folder view) into ONE new rendered block:
  crosses delivery + dashboard (GOV-2 §1 "crosses two or more of ... delivery,
  dashboard ...").
- **Completeness / consumer claim** — the arrow cut requires enumerating every
  reader of `trend_structure.daily_change_pct` and of `TRADABLES_ROW` to prove
  safe removal (GOV-2 §1 bullet 1, "claims to enumerate all consumers ...
  renderers").
- **Removes/changes a rendered surface with more than one asserting test** — the
  tradables arrow is asserted by the PRD-199 test block and baked into a golden
  fixture (GOV-2 §1 bullet 4).

**LANE: HIGH-RISK** — `dashboard_renderer.py` is a HIGH-RISK file for CLASS
CONSUMER (owner Correction 2; PRD-121 R11). MICRO-ineligible.

**Governed by the decision-support expansion doctrine** as "presentation work
attached to" the GEX and movement tracks (`docs/plans/decision-support-expansion
-doctrine-v0.1.md` scope line): draft + manual-held (GOV-0), one review, and G1
(no prediction), G5 (additive; readers recorded in `artifact_flow_map.md`), G6
(honest absence), G7 (cuts-before-additions — satisfied by the bundled arrow
cut), G8 (one bounded question) all apply.

---

## 3. Verified current state (hourly board, `main` @ `731b5ee`)

The "hourly published board" is the HTML from `.github/workflows/hourly_alert.yml`:
`alert_runner` -> `_execute_notify_run` writes the hourly sidecars
(`hourly_alert.yml:101`); GEX best-effort refresh (`:146-150`); render from
`latest_hourly_payload.json` + `latest_hourly_run.json` (`:159-163`). The renderer
`main()` is source-agnostic: it loads every sidecar from `logs_dir` and always
calls `_resolve_red_folder_view`. So a carrier is "available on hourly" iff the
hourly notify path (or the hourly workflow) produces it.

- Hourly notify path computes regime + permission: `fetch_all`
  (`runtime/__init__.py:549`) -> `normalize_all` (`:550`) -> `validate_quotes`
  (`:552`) -> `compute_regime` (`:570`, guarded `if not
  validation_summary.system_halted:` `:569`). Contract carries regime (`:703` ->
  `:2255`) and permission (`:2246` base, operator-lock `:2284`); summary carries
  `posture`/`regime` (`:2356`) and `permission` (`:2363`). Hourly payload:
  `_write_hourly_artifacts` (`:734`) -> `build_report_payload` (`:2405`) ->
  `deliver_json(..., LATEST_HOURLY_PAYLOAD_PATH)` (`:2408`).
- Trend-structure snapshot is WRITTEN on the hourly path:
  `_write_trend_structure_snapshot` (`runtime/__init__.py:778`, inside
  `if notify_mode in _HOURLY_MODES:`), over every `config.TREND_STRUCTURE_SYMBOLS`
  (includes `"SPY"`, `config.py:278`), regardless of regime posture. SPY
  `price_vs_vwap` set at `trend_structure.py:282` (`_resolve_vwap_field:264`).
- Watchlist snapshot WRITTEN on the hourly path: `_write_watchlist_snapshot`
  (`runtime/__init__.py:787`, PRD-311). GEX snapshot refreshed by the workflow
  (`hourly_alert.yml:146-150`), consumed same-job by the render.
- `SpyObservation` and the Market Control Card are DAILY/full-pipeline only
  (`build_spy_observation` at `runtime/__init__.py:1515`, `build_market_control_card`
  at `:1533`, both inside `_run_pipeline` `:1113`); neither reaches the hourly
  payload. Hence INTRADAY and EVENT must be sourced from hourly-present carriers
  (§4.3, §4.4).

---

## 4. Design

### 4.1 The panel is a pure delivery-layer assembly (no runtime change)

Every one of the six carriers is ALREADY loaded by the renderer on the hourly
board:

- regime + permission: from the hourly payload/run (`dashboard_renderer.py`
  reads `summary.market_regime` `:2102`, `summary.permission` `:2173-2175`).
- INTRADAY: the trend-structure snapshot is already loaded (the arrow reads
  `trend_records`); the panel reads `symbols.SPY.price_vs_vwap`.
- POSITIONING: `gex_card.load_gex_snapshot` (`dashboard_renderer.py:3427`).
- PARTICIPATION: `movement_card.load_watchlist_snapshot`
  (`dashboard_renderer.py:3429`).
- EVENT RISK: `_resolve_red_folder_view` (`dashboard_renderer.py:3433`).

So the panel is assembled entirely from data the renderer already holds. **No
`runtime/__init__.py`, no ingestion, no new artifact, no schema bump.** New pure
module `cuttingboard/delivery/market_state_panel.py` (sibling to `gex_card.py` /
`movement_card.py`) owns validation, honest-absence, per-axis provenance
formatting, and the HTML fragment; `dashboard_renderer.py` gathers the six
already-loaded carriers and emits the block (thin wiring).

### 4.2 The arrow cut (owner Ruling 2) — independent final-reader proof

The tradables-arrow surface, precisely:
- **Builder:** `dashboard_renderer.py:1252-1258` — `for slot in
  TRADABLES_ROW.slots:` reads `rec.get("daily_change_pct")` from the trend-
  structure records and appends `_pct_arrow(...)` to `_tape_arrow_map`.
- **Emitter:** `dashboard_renderer.py:2820-2831` — `_ts_arrow_ok = _ts_health ==
  "OK"` (`:2820`) gates the `<span class="tradable-arrow">` (`:2830`); the label
  and the price value (`:2831`) are independent and ungated.
- **Producer (orphaned by the cut):** `trend_structure.py:254-256` computes the
  record `daily_change_pct`, emitted `:277`.

**Final-reader proof (independent, re-run at `731b5ee`):** `grep daily_change_pct`
across `cuttingboard/` shows the trend-structure record field is read at exactly
ONE non-test site — `dashboard_renderer.py:1254` (plus its `:1248` comment). The
`watchlist_sidecar.py:81-89` and `movement_card.py` `daily_change_pct` are a
SEPARATE field (the watchlist row), not this producer. So removing the arrow
branch orphans `trend_structure.daily_change_pct` with no other reader.

**Preserve `TRADABLES_ROW`** (`macro_tape_layout.py:53`): it is shared by three
surviving surfaces — the tradables PRICE tape builder (`dashboard_renderer.py:1304`,
reads `current_price`), the emit value (`:2831`), and the notifications
`_tradables_block` (`notifications/__init__.py:119`, reads `q.price`). None reads
`daily_change_pct`. Deleting the row would break the price tape and notifications;
the cut removes only the arrow contribution, not the row.

**Cut surface (exact):**
1. Remove the arrow builder branch `dashboard_renderer.py:1252-1258`.
2. Remove `_ts_arrow_ok` (`:2820`) and the `tradable-arrow` span (`:2830`); keep
   label + `macro-tape-value` (price).
3. Remove the orphaned producer `trend_structure.py:254-256, 277`.
4. Regenerate the golden fixture `tests/data/dashboard_pre_gex_golden.html`
   (contains 6 `tradable-arrow` spans).
5. Update/remove the PRD-199 arrow tests and the trend-record test (§10, §8).

### 4.3 INTRADAY carrier decision (owner Ruling 5): A (Trend-Structure hourly)

Candidate A (hourly `trend_structure_snapshot.json -> symbols.SPY.price_vs_vwap`)
is truthfully available on the hourly board and is USED. Candidate B
(`SpyObservation.price_vs_vwap`) is daily/full-pipeline only and is NOT available
hourly. Verdict: use A. Token semantics: `ABOVE` / `BELOW` / `AT_LEVEL`
(`trend_structure.py:106`); `DATA_UNAVAILABLE` (price/df missing);
`NOT_COMPUTED` (df present but non-intraday/daily bars, `_classify_vwap_unavailable`
`:120`). **Honesty nuance (recorded):** on an hourly run whose SPY OHLCV resolves
to daily bars, `price_vs_vwap` is `NOT_COMPUTED` — a typed-honest token, never a
fabricated level. The panel renders `ABOVE/BELOW/AT_LEVEL VWAP` when computed,
else INTRADAY `unavailable`. No new producer (owner Ruling 5).

### 4.4 EVENT RISK carrier (owner Ruling 8): red-folder view

The red-folder block renders unconditionally at render time on the hourly board
(`_resolve_red_folder_view`, `dashboard_renderer.py:3433`; block `:2844`), from
the static committed calendar `data/red_folder_2026.json` via
`red_folder.load_schedule` + `events_in_window` (48h). The MCC EVENT cell is
daily-only and is NOT used. Provenance = render-time window over a static
calendar; no feed capture stamp is invented (owner Ruling 8). Unavailable:
`ok=False` -> EVENT `unavailable`; empty window -> honest "no events in 48h".

---

## 5. Panel shape (ESTIMATED — human-facing; design-direction question)

A compact, mobile-friendly block titled `MARKET STATE`, six rows, each row =
`AXIS LABEL : value-or-unavailable  (provenance)`, reusing the existing
`.kv-grid` / `.block` classes (no new CSS). Proposed rows:

| Axis | Value shown (EXISTING token only; no new metric) | Provenance suffix (honest type) |
|---|---|---|
| ENVIRONMENT | regime posture token, else `unavailable` | `as of HH:MM ET` (run/capture clock) |
| PERMISSION | permission line (existing) | `as of HH:MM ET` (run/capture clock) |
| INTRADAY | `SPY <ABOVE/BELOW/AT> VWAP`, else `unavailable` | `as of HH:MM ET` (run/capture clock; structural) |
| POSITIONING | GEX present -> existing headline (see D-1), else `unavailable` | `fetched HH:MM ET, ~15m delayed (Cboe)` |
| PARTICIPATION | movement present -> `12/12 captured` (availability), else `unavailable` | `captured HH:MM ET` (`generated_at`) |
| EVENT RISK | `N events in 48h` / `no events in 48h`, else `unavailable` | `red-folder calendar (48h window)` |

No global "as of" line; each row carries only its own provenance (owner Ruling 9).
No score, verdict, or confluence anywhere (owner Ruling 10). The exact per-row
"how much existing value vs pure availability" is a bounded design-direction
question (D-1, D-2 §15) for Dustin's post-review ruling; the guardrail is fixed:
only existing tokens/values are re-presented, never a newly computed summary.

---

## 6. Seam trace

```
--- all six carriers already produced on the hourly board ---
regime        runtime:570 compute_regime  -> hourly contract/summary (regime, permission)
trend snap    runtime:778 _write_trend_structure_snapshot -> logs/trend_structure_snapshot.json (SPY.price_vs_vwap)
watchlist     runtime:787 _write_watchlist_snapshot        -> logs/watchlist_snapshot.json
gex           hourly_alert.yml:146-150 tools/gex_snapshot.py -> logs/gex_snapshot.json
red-folder    static data/red_folder_2026.json
--- renderer already loads every carrier ---
dashboard_renderer.main(): payload(regime,permission) + load_gex_snapshot:3427
  + load_watchlist_snapshot:3429 + trend_records + _resolve_red_folder_view:3433
--- NEW: assemble the panel from those already-loaded carriers ---
market_state_panel.build(...) -> render_fragment  [pure; honest-absence per axis]
  -> dashboard_renderer emits the MARKET STATE block (thin wiring)
--- CUT (bundled): tradables daily-change arrow ---
remove arrow builder (dashboard_renderer:1252-1258) + arrow emit (:2820,:2830)
  + orphaned producer (trend_structure:254-256,277); PRESERVE TRADABLES_ROW + price tape + notifications
  -> regenerate golden fixture
--- publish (hourly workflow only) ---
  -> ui/dashboard.html -> ui/index.html -> readiness -> publish branch -> Pages
```

---

## 7. Schema / persistence

**None.** The panel reads existing carriers already in the hourly payload and
sidecars; it adds no artifact, no `schema_version`, no `PAYLOAD_SCHEMA_VERSION`
change, no required-key change, no persisted/published file, no decision
contract. The arrow cut removes one record field (`trend_structure.daily_change_pct`)
whose only reader is deleted in the same slice. `artifact_flow_map.md` gains the
panel as a new READER of the existing sidecars (doctrine G5); no new writer.

---

## 8. FILES cone (ESTIMATED SURFACE — NOT YET APPROVED)

Production:

| Op | File | Purpose |
|---|---|---|
| A | `cuttingboard/delivery/market_state_panel.py` | pure builder/validator: six axes, honest-absence per axis, per-axis provenance, HTML fragment |
| M | `cuttingboard/delivery/dashboard_renderer.py` | wire the panel (gather 6 already-loaded carriers + emit block); CUT the tradables arrow (builder :1252-1258; emit gate/span :2820,:2830) |
| M | `cuttingboard/trend_structure.py` | remove orphaned `daily_change_pct` producer (:254-256, :277) |

Tests:

| Op | File | Purpose |
|---|---|---|
| A | `tests/test_market_state_panel.py` | per-axis value/unavailable, per-axis honest provenance, no global as-of, no score, absent-carrier -> axis unavailable |
| M | `tests/test_dashboard_renderer.py` | panel wiring + presence/suppression; remove PRD-199 arrow tests (keep price-tape tests) |
| M | `tests/test_trend_structure.py` | remove/adjust the record `daily_change_pct` test (:570-586); preserve `price_vs_vwap` tests |
| M | `tests/test_dash_macro.py` | adjust any tradables-arrow assertion (verify scope during impl) |
| M | `tests/data/dashboard_pre_gex_golden.html` | regenerate: tradables-arrow spans removed |

Docs:

| Op | File | Purpose |
|---|---|---|
| M | `docs/artifact_flow_map.md` | record the panel as a new reader of the existing sidecars (G5) |
| M | `docs/SCHEMA_MAP.md` | note the panel's read-only consumption of existing carriers |

**Verified-UNAFFECTED, NOT edited:** `cuttingboard/notifications/__init__.py`
(`_tradables_block` reads `q.price`, never `daily_change_pct`); `TRADABLES_ROW`
(`macro_tape_layout.py:53`, preserved); the tradables PRICE tape
(`dashboard_renderer.py:1304`); `tests/test_notifications.py` (stays green with no
edit). Stage-0 PRD/registry bookkeeping (`PRD-312.md`, `PRD_REGISTRY.md`,
`prd_index.json`, `PROJECT_STATE.md`, workplan ledger) is deferred to the Stage-0
PRD step AFTER this packet is review-clean and Dustin rules — it is NOT part of
this packet (no PRD-312 allocated).

---

## 9. Estimated production/test LOC (ESTIMATED SURFACE — NOT YET APPROVED)

- **Production ~90-130 net.** `market_state_panel.py` ~90-130 (six-row builder +
  per-axis honest provenance + honest-absence + fragment; simpler than
  `gex_card.py` ~200 because inputs are already validated by their own cards);
  renderer wiring ~+15; arrow-cut removal ~-20; trend producer removal ~-8.
  **Proposed ceiling <=150 net production LOC.**
- **Test ~150-220 net.** New `test_market_state_panel.py` ~130-180; arrow-cut test
  edits net ~0 (remove PRD-199 arrow tests, add nothing net); golden regen is
  generated, not hand-written. **Proposed ceiling <=240 net test LOC.**
- **Tripwire (stop-and-renew):** any `runtime/`/ingestion edit; any new artifact
  or `schema_version`/`PAYLOAD_SCHEMA_VERSION` change; any new derived metric;
  any file beyond §8; exceeding either ceiling.

---

## 10. Discriminating test / mutation matrix (ESTIMATED)

| # | Case | Asserted (exact) | Mut? |
|---|---|---|---|
| M1 | ENVIRONMENT present | regime posture token rendered in the ENVIRONMENT row | YES |
| M2 | ENVIRONMENT unavailable | regime None (halt) -> row `unavailable`, never fabricated | YES |
| M3 | PERMISSION present | existing permission line rendered verbatim | YES |
| M4 | INTRADAY present | `SPY.price_vs_vwap in {ABOVE,BELOW,AT_LEVEL}` -> rendered token | YES |
| M5 | INTRADAY not-computed | `price_vs_vwap` `NOT_COMPUTED`/`DATA_UNAVAILABLE` -> row `unavailable`, never a level | YES |
| M6 | POSITIONING present | GEX snapshot valid -> existing headline + `fetched HH:MM ET ~15m Cboe` | YES |
| M7 | POSITIONING unavailable | GEX absent/suppressed (`load_gex_snapshot` None / `render_fragment` "") -> row `unavailable` | YES |
| M8 | PARTICIPATION present | valid watchlist snapshot -> availability + `captured HH:MM ET` from `generated_at` | YES |
| M9 | PARTICIPATION unavailable | movement absent/suppressed -> row `unavailable` | YES |
| M10 | EVENT present | red-folder `ok`, N events -> `N events in 48h`; empty -> `no events in 48h` | YES |
| M11 | EVENT unavailable | red-folder `ok=False` -> row `unavailable` | YES |
| M12 | Per-axis provenance type | each row carries ONLY its own honest provenance; GEX row carries the delayed-Cboe qualifier; no global synchronous "as of" line exists | YES |
| M13 | No score/verdict | panel output contains no composite/score/bullish-bearish/confluence token | YES |
| M14 | No fabrication | an unavailable axis never borrows another axis's value or a zero/neutral placeholder | YES |
| M15 | Arrow cut: arrow gone | rendered board has no `tradable-arrow` span | YES — leaving the arrow reddens |
| M16 | Arrow cut: price tape preserved | tradables PRICE cells still render `current_price`; notifications `_tradables_block` unchanged | YES — removing the price reddens |
| M17 | Producer orphaned + removed | `trend_structure` record has no `daily_change_pct`; `price_vs_vwap` still present | YES |
| M18 | Panel absent-safe | if the panel cannot build, whole block suppressed baseline-neutral (no partial/garbled block) | YES |

Every guard ships a red test (PRD-198 inv. 4); whole-output baselines for
suppression; no guard-with-green-mutation. Mutation-red evidence (M1-M18) is
produced at implementation, not here.

---

## 11. Unavailable / failure semantics

Per-axis independent: any single axis whose carrier is absent/suppressed/typed-
unavailable renders that ROW as `unavailable` (never a fabricated or borrowed
value; owner Ruling 9/10, doctrine G6). The panel as a whole suppresses
baseline-neutral only if it cannot build at all (M18). GEX and movement follow
their existing suppress-to-empty carriers (their own cards already gate that);
INTRADAY follows the trend-snapshot typed tokens; EVENT follows red-folder
`ok`/empty; ENVIRONMENT/PERMISSION are near-total producers (regime None only on
pre-regime halt). No global "as of"; no synchronous-state implication.

---

## 12. Stop-and-amend conditions

1. Any `runtime/__init__.py` or ingestion edit (the panel is delivery-only).
2. Any new artifact, `schema_version`, `PAYLOAD_SCHEMA_VERSION`, or required-key
   change (owner Ruling 10: no new schema merely to obtain timestamps).
3. Any newly computed derived metric, score, verdict, confluence, ranking,
   relative-strength, or bullish/bearish token (owner Ruling 10).
4. Any trade-permission/decision mutation, or any axis feeding a decision surface.
5. Any new provider, producer, cadence, or movement age-gate (owner Rulings 5/7/10).
6. Any global synchronous "as of" line implying one clock (owner Ruling 9).
7. Cutting or mutating `TRADABLES_ROW`, the tradables price tape, or notifications
   (only the arrow contribution is cut; §4.2).
8. Removing/altering Trend-Structure `price_vs_vwap` or alignment (owner Ruling 2).
9. Reopening or mutating the PRD-289 Market Control Card contract (owner Ruling 1).
10. Any file beyond §8 or exceeding a §9 ceiling -> fresh GOV-2 §1 pass.

---

## 13. Materiality / lane

**MATERIAL** (owner Correction 3; cross-surface presentation seam + de-dup
completeness claim + rendered-surface-with-tests change). **HIGH-RISK**
(`dashboard_renderer.py`; owner Correction 2; PRD-121 R11). MICRO-ineligible.
Governance hold: DRAFT + self-named governance/expansion (GOV-0 / PRD-186),
held for Dustin. After review-clean + design-direction ruling: Stage-0 PRD-312 ->
independent PRD review -> Gate A.

---

## 14. What gets ADDED, CUT, and left UNTOUCHED

**ADDED:**
- `market_state_panel.py` (pure builder) + a thin renderer wire-in.
- One new rendered `MARKET STATE` block, six axes, hourly-first, provenance-first.
- `artifact_flow_map.md` reader entry (G5).

**CUT:**
- The Macro-Tape tradables daily-change ARROW (builder + emit gate/span).
- The orphaned `trend_structure.daily_change_pct` producer.
- The PRD-199 arrow tests; regenerate the golden fixture.

**UNTOUCHED (verified):**
- `TRADABLES_ROW`, the tradables PRICE tape, notifications `_tradables_block`.
- Trend-Structure `price_vs_vwap` + alignment.
- The PRD-289 Market Control Card contract.
- `runtime/__init__.py`, ingestion, all decision/universe/permission logic.
- GEX and Movement card internals (the panel consumes their loaders read-only).
- All schema/persistence surfaces.

---

## 15. Open design/review questions

- **D-1 POSITIONING row value.** Show an existing GEX headline (e.g. `net_usd`
  sign or `dominant` strike) vs pure `present/unavailable` + provenance? Default:
  minimal availability + provenance to avoid duplicating the GEX card. Existing
  values only; no new metric. Dustin's design-direction ruling decides.
- **D-2 PARTICIPATION row value.** `12/12 captured` availability vs a compact
  existing summary. Default: availability + provenance. No new metric.
- **D-3 Panel placement.** Above the individual cards (as a legibility header) vs
  inline. Placement is a design-direction choice; no code-boundary impact.
- **D-4 Degenerate all-unavailable.** Confirm the panel still renders (all rows
  `unavailable`) vs suppresses whole. Default: render honest all-unavailable so
  provenance stays legible; suppress only on build failure (M18).

---

## 16. Author self-verification (GOV-2 §3)

All against `main` @ `731b5ee`; correction/verification facts [C]:
- **[C1] CADENCE.** `_execute_notify_run` (`runtime/__init__.py:526`):
  `fetch_all` `:549` -> `normalize_all` `:550` -> `validate_quotes` `:552` ->
  `compute_regime` `:570`; permission carrier `:2246`/`:2284`, summary `:2363`.
  ENVIRONMENT + PERMISSION available hourly. CONFIRMED (owner Correction 1).
- **[C2] INTRADAY carrier A.** Trend snapshot written hourly `:778` over
  `TREND_STRUCTURE_SYMBOLS` (incl. SPY, `config.py:278`); `price_vs_vwap`
  `trend_structure.py:282`. `SpyObservation`/MCC daily-only
  (`:1515`/`:1533` in `_run_pipeline:1113`). CONFIRMED (owner Ruling 5).
- **[C3] GEX/MOVEMENT/EVENT hourly.** GEX render gate `dashboard_renderer.py:2616`
  from `logs/gex_snapshot.json` (`hourly_alert.yml:146-150`); movement written
  `:787`, gate `:2627`; red-folder `_resolve_red_folder_view:3433`, block `:2844`.
  CONFIRMED.
- **[C-CUT] Final-reader.** `trend_structure.daily_change_pct` (`:254-256,277`)
  read only at `dashboard_renderer.py:1254`; the watchlist `daily_change_pct` is a
  separate field. `TRADABLES_ROW` shared by price tape (`:1304`), emit value
  (`:2831`), notifications (`notifications/__init__.py:119`, reads `q.price`) —
  preserved. Golden fixture `tests/data/dashboard_pre_gex_golden.html` has 6
  `tradable-arrow` spans -> regenerate. CONFIRMED (owner Ruling 2, independently
  re-run).
- **[C4] Delivery-only.** All six carriers already loaded by the renderer; the
  panel needs no runtime/ingestion/artifact/schema change. CONFIRMED.
- **[C5] Provenance heterogeneity.** GEX `fetched_at_utc` (~15m delayed Cboe) is
  the one clock diverging from the run; ENV/PERM/INTRADAY/MOVEMENT ride the
  run/capture clock; EVENT is a static-calendar window. Honest per-axis type;
  no global as-of. CONFIRMED (owner Ruling 9).

Author self-verification is NOT independent review. Codex Event-1 (INITIAL PACKET
REVIEW) is PENDING on this v0.1 committed head.

---

## 17. Packet review records (GOV-2 §2, §7)

### INITIAL PACKET REVIEW (Event-1) — PENDING
To be recorded as `MARKET_STATE_EVENT1_CODEX_REVIEW_2026-08-22.md` in this packet
directory: reviewer identity + capability role, exact reviewed SHA, date,
verdict, findings + dispositions, and fresh-context/independence attestation.

### EXACT-CORRECTED-HEAD CONFIRMATION (Event-2) — PENDING
To be recorded as `MARKET_STATE_EVENT2_CODEX_CONFIRMATION_2026-08-22.md`:
corrected SHA, enumerated prior finding ids + dispositions, verdict.

---

## 18. Revision log

- **v0.1 (2026-08-22):** initial provisional MATERIAL packet, authored against
  Dustin's 2026-08-22 BUILD ruling (3 corrections + 10 product rulings). Hourly-
  first six-axis provenance panel (pure delivery-layer assembly, no runtime/
  schema change) + bundled tradables daily-change-arrow de-duplication (final-
  reader claim independently re-proven; `TRADABLES_ROW`/price tape/notifications
  preserved). Baseline `main` @ `731b5ee`.

---

END OF PACKET v0.1 — PROVISIONAL / NOT REVIEW-CLEAN / NO IMPLEMENTATION AUTHORITY.
Codex Event-1 runs on this committed head. Gate A is neither requested nor granted.
