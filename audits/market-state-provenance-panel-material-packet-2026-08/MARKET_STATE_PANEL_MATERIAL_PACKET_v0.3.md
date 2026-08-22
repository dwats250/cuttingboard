# Market State Provenance Panel (FIVE-AXIS) + Macro-Tape daily-change de-duplication — MATERIAL PACKET (v0.3, DESIGN-CLEAN CANDIDATE)

**Status: REVIEW-CLEAN — GOV-2 packet cycle COMPLETE — NO IMPLEMENTATION AUTHORITY
— HELD FOR DUSTIN'S DESIGN-DIRECTION RULING FROM THE REVIEW-CLEAN PACKET (GOV-2 §2
step 6).**
Codex EXACT-CORRECTED-HEAD CONFIRMATION (Event-2,
`MARKET_STATE_EVENT2_CODEX_CONFIRMATION_2026-08-22.md`, corrected SHA `e6b8758`)
confirmed **F1-F7 all RESOLVED, five-axis contract internally consistent, NEW
BLOCKING: NONE — VERDICT CLEAN**. Next governed steps: Dustin's design-direction
ruling -> Stage-0 PRD-312 -> independent PRD review -> Gate A.
v0.3 folds Dustin's 2026-08-22 design-direction ruling (D-INTRADAY = Option B;
D-PLACEMENT; D-1; D-2; arrow cut retained) into the single consolidated
correction. It supersedes v0.1 (`MARKET_STATE_PANEL_MATERIAL_PACKET_v0.1.md`) and
the correction record (`MARKET_STATE_CONSOLIDATED_CORRECTION_v0.2.md`), which
remain as evidence. All Codex Event-1 findings F1-F7
(`MARKET_STATE_EVENT1_CODEX_REVIEW_2026-08-22.md`, reviewed `66d9731`) are
dispositioned here (§17). No implementation authority (GOV-2 §4); FILES/LOC are
`ESTIMATED SURFACE — NOT YET APPROVED` (GOV-2 §5). No PRD-312 allocated. Gate A
neither requested nor granted.

**Code baseline `main` @ `731b5ee`.** Packet-cycle commits are docs-only; source
is byte-identical to baseline (verified `git diff 731b5ee..HEAD -- cuttingboard/
tests/` empty). Every carrier/cut fact re-verified at the corrected head (§16).

---

## 0. GOV-2 order

```
Stage-0 product report (REVISE-then-BUILD) ............ DONE
owner BUILD ruling (3 corrections + 10 rulings) ....... DONE
provisional MATERIAL packet v0.1 ...................... DONE (@ 66d9731)
Codex INITIAL PACKET REVIEW (Event-1) ................. DONE (FINDINGS F1-F7)
consolidated correction v0.2 (mechanical + escalation)  DONE
owner design-direction ruling (D-INTRADAY B; placement; D-1/D-2) DONE (2026-08-22)
corrected packet v0.3 (this doc; five-axis) ........... DONE   <-- HERE
exact-corrected-head confirmation (Event-2) ........... PENDING (on this committed head)
Dustin design-direction ruling on the corrected packet  PENDING
Stage-0 PRD-312 -> independent PRD review -> Gate A .... PENDING
```

MICRO-ineligible (MATERIAL, GOV-2 §1). Rides **HIGH-RISK** (`dashboard_renderer.py`).

---

## 0.1 Owner design-direction rulings folded into v0.3 (Dustin, 2026-08-22)

- **D-INTRADAY = Option B — DROP INTRADAY.** The panel is FIVE axes: ENVIRONMENT,
  PERMISSION, POSITIONING, PARTICIPATION, EVENT RISK. Reason: no truthful hourly
  intraday/VWAP carrier exists today. Do NOT render a permanently-unavailable
  INTRADAY row, add an hourly intraday fetch, add a producer, expand runtime, or
  renew the boundary. Intraday/VWAP stays on its existing full-run/dedicated
  surfaces; it is simply not part of this hourly compression panel.
- **D-PLACEMENT — before System State, outside the protected region.** Place the
  block immediately BEFORE the System State block, OUTSIDE the PRD-219 protected
  `system-state`..`candidate-board` region. Do not modify PRD-219 region
  semantics. `tests/test_dash_system_state.py` stays OUT of the FILES cone unless
  the actual corrected seam proves otherwise.
- **D-1 POSITIONING — reuse existing qualified GEX semantics.** Preserve the
  configured dealer-positioning-assumption qualifier, the GEX fetched/as-of time,
  and the ~15m delayed-source qualifier. Absent/suppressed GEX -> POSITIONING
  unavailable. No new GEX interpretation, no score, no trade implication, no
  shortened claim that drops the qualifier.
- **D-2 PARTICIPATION — availability + provenance only.** Expose only movement
  availability, `generated_at`/captured provenance, and honest partial/unavailable
  state where mechanically supported. Never claim "12/12" when any symbol is
  `n/a`. No new breadth/leadership/directional summary or score.
- **ARROW CUT — retained.** Keep bundling the Macro-Tape tradables daily-change
  arrow removal, conditioned on the final-reader proof holding at the corrected
  head (it does, §4.2/§16).
- **Absolute cuts remain:** no composite score, verdict, confluence, prediction,
  decision coupling, new provider/producer/runtime fetch, schema-for-timestamps,
  movement age-gate, freshness repair, or maintenance/hygiene work.
- **Classification remains:** CLASS CONSUMER, LANE HIGH-RISK, MATERIAL YES.

---

## 1. Product question and outcome

A read-only **MARKET STATE** block on the hourly published board that co-locates
FIVE independent market-state axes so their state and freshness are legible in one
glance, WITHOUT a score and WITHOUT a single synchronized as-of. Each row shows an
existing value (or honest `unavailable`) with that axis's own provenance. Bundled:
the Macro-Tape tradables daily-change ARROW is cut as a duplicate of the Market
Movement card's signed value, and its orphaned producer
(`trend_structure.daily_change_pct`) removed; the tradables PRICE tape,
`price_vs_vwap`, trend alignment, and notifications are preserved. No new
production data, fetch, artifact, schema, cadence, or decision coupling.
Description, not prediction.

---

## 2. Intake classification (GOV-2 §1)

**MATERIAL: YES.** Triggers: a new cross-surface delivery/dashboard presentation
seam composing five carriers from five producers into one new rendered block; the
completeness/consumer claim required to de-duplicate the daily-change reader
(arrow cut); and removal of a rendered surface asserted by more than one test.
**LANE: HIGH-RISK** (`dashboard_renderer.py`; PRD-121 R11). MICRO-ineligible.
Governed by the decision-support expansion doctrine (presentation attached to the
GEX/movement tracks): draft + manual-held (GOV-0), G1/G5/G6/G7/G8 apply.

---

## 3. Verified current state (hourly board, `main` @ `731b5ee`)

The hourly board is the HTML from `hourly_alert.yml` (`alert_runner` ->
`_execute_notify_run` writes sidecars `:101`; GEX best-effort refresh `:146-150`;
render from `latest_hourly_payload.json` + `latest_hourly_run.json` `:159-163`).
The renderer `main()` loads every sidecar and always calls
`_resolve_red_folder_view`.

Per-axis hourly carriers (five axes; INTRADAY dropped per D-INTRADAY):

- **ENVIRONMENT:** hourly regime from `compute_regime` (`runtime/__init__.py:570`),
  threaded into the hourly contract/summary (`:703`/`:2255`/`:2356`); renderer
  reads `summary.market_regime` (`dashboard_renderer.py:2102`). Run/capture clock.
- **PERMISSION:** `latest_hourly_run.json.permission` — the hourly RUN summary
  always supplies it (`runtime/__init__.py:2363-2369`); the renderer reads the run
  first, payload as fallback (`dashboard_renderer.py:2172-2175`). NOTE (F2):
  `_build_system_state` carries no permission field (`contract.py:251-259`); the
  hourly contract injects it only for operator-lock (`runtime:2278-2284`), so the
  payload permission is null on a normal run. Run/capture clock.
- **POSITIONING:** `gex_card` from `logs/gex_snapshot.json`
  (`dashboard_renderer.py:3427`; render gate `:2616`/`:2620`). Own `fetched_at_utc`
  (~15m-delayed Cboe); existing card carries the configured-assumption qualifier
  (`gex_card.py:175-191`). Suppress-to-empty on absent/stale/invalid.
- **PARTICIPATION:** `movement_card` from `logs/watchlist_snapshot.json`
  (`dashboard_renderer.py:3429`; written hourly `runtime:787`, PRD-311).
  `generated_at` capture clock. Producer emits all 12 rows even when a row's
  `daily_change_pct` is null (`watchlist_sidecar.py:76-92`); the Movement card
  renders those as `SYM n/a` (`movement_card.py:86-93,126-129`).
- **EVENT RISK:** red-folder view (render-time, `_resolve_red_folder_view`
  `dashboard_renderer.py:3433`; block `:2844`) over the static
  `data/red_folder_2026.json` (48h window). The MCC EVENT cell is daily-only and
  is NOT used.

INTRADAY note (F1, resolved by D-INTRADAY B): the only vs-VWAP carriers are the
hourly trend-structure snapshot (which receives DAILY OHLCV via `fetch_ohlcv`,
`ingestion.py:119-124`, so SPY `price_vs_vwap` is always `NOT_COMPUTED` on the
hourly board) and the daily `SpyObservation` (intraday-session fetch only in
`_run_pipeline`, `runtime:1238`). Neither gives a truthful HOURLY vs-VWAP, so
INTRADAY is excluded from this hourly panel and remains on its existing full-run
surfaces.

---

## 4. Design

### 4.1 Pure delivery-layer assembly (no runtime change)

All five carriers are already loaded by the renderer on the hourly board (regime +
permission from the payload/run; GEX via `load_gex_snapshot`; movement via
`load_watchlist_snapshot`; red-folder via `_resolve_red_folder_view`). The panel is
assembled entirely from data the renderer already holds. **No `runtime/`,
ingestion, new artifact, or schema change.** New pure module
`cuttingboard/delivery/market_state_panel.py` (sibling to `gex_card.py` /
`movement_card.py`) owns validation, honest-absence, per-axis provenance, and the
HTML fragment; `dashboard_renderer.py` gathers the five carriers and emits the
block immediately BEFORE the System State block (D-PLACEMENT), outside the PRD-219
protected region.

### 4.2 The arrow cut — final-reader proof holds at the corrected head

Re-verified at the corrected head (source byte-identical to baseline): the
trend-structure record `daily_change_pct` (`trend_structure.py:254-256,277`) has
exactly one non-test reader — `dashboard_renderer.py:1254` (the tradables arrow;
`:1248` is its comment). `TRADABLES_ROW` (`macro_tape_layout.py:53`) is shared by
the price tape (`dashboard_renderer.py:1304`), the emit value (`:2831`), and
notifications `_tradables_block` (`notifications/__init__.py:119`, reads
`q.price`) — all preserved.

Cut surface (exact):
1. Remove the arrow builder branch `dashboard_renderer.py:1252-1258`.
2. Remove `_ts_arrow_ok` (`:2820`) and the `tradable-arrow` span (`:2830`); keep
   label + `macro-tape-value` (price).
3. Remove the orphaned producer `trend_structure.py:254-256, 277`. Preserve
   `price_vs_vwap` (`:282`) and `trend_alignment`.
4. Update the PRD-199 arrow tests AND `test_prd220_tradables_arrow_before_price`
   (`tests/test_dashboard_renderer.py:4007-4013`, F3); check `tests/test_dash_macro.py`.
5. Regenerate the golden fixture `tests/data/dashboard_pre_gex_golden.html`
   (6 `tradable-arrow` spans).
Preserve notification price rendering (`_tradables_block`, unaffected).

### 4.3 Per-axis provenance types (owner Ruling 9 / D-1 / D-2)

Heterogeneous, each row its own honest type; no global synchronized as-of:
- ENVIRONMENT / PERMISSION: run/capture clock (from the hourly run).
- POSITIONING: GEX `fetched_at_utc` (~15m-delayed Cboe) + the existing
  configured-dealer-positioning-assumption qualifier (reused verbatim from the GEX
  card; no shortened claim).
- PARTICIPATION: `generated_at` capture clock; availability + honest partial state
  only (never "12/12" when any symbol is `n/a`).
- EVENT RISK: render-time 48h calendar window (no invented feed timestamp).

---

## 5. Final five-axis product shape (ESTIMATED; human-facing)

Compact `MARKET STATE` block, placed immediately before System State, reusing the
existing `.kv-grid`/`.block` classes (no new CSS). One row per axis; each row =
`AXIS : value-or-unavailable (own provenance)`:

| Axis | Value (existing token only) | Provenance (honest type) |
|---|---|---|
| ENVIRONMENT | current hourly regime/state, else `unavailable` | `as of HH:MM ET` (run clock) |
| PERMISSION | current hourly permission value, else `unavailable` | `as of HH:MM ET` (run clock) |
| POSITIONING | existing qualified GEX posture/value, else `unavailable` | `fetched HH:MM ET, ~15m delayed (Cboe)` + configured-assumption qualifier |
| PARTICIPATION | movement availability (honest partial where supported), else `unavailable` | `captured HH:MM ET` (`generated_at`) |
| EVENT RISK | `N events in 48h` / `no events in 48h`, else `unavailable` | red-folder calendar (48h window) |

No global "as of"; no score/verdict/confluence; no INTRADAY row. PARTICIPATION
shows availability/provenance, not a re-presented per-symbol table (the Movement
card owns those) and never a "12/12" overclaim.

---

## 6. Seam trace

```
--- five carriers already produced/loaded on the hourly board ---
regime      runtime:570 -> hourly contract/summary (regime)
permission  runtime:2363 -> latest_hourly_run.json.permission (renderer run-first :2172-2175)
gex         hourly_alert.yml:146-150 -> logs/gex_snapshot.json -> load_gex_snapshot:3427
movement    runtime:787 -> logs/watchlist_snapshot.json -> load_watchlist_snapshot:3429
red-folder  static data/red_folder_2026.json -> _resolve_red_folder_view:3433
--- NEW: assemble the panel from those already-loaded carriers ---
market_state_panel.build(...) -> render_fragment  [pure; honest-absence per axis]
  -> dashboard_renderer emits MARKET STATE block immediately BEFORE system-state (outside PRD-219 region)
--- CUT (bundled): tradables daily-change arrow ---
remove arrow builder (:1252-1258) + arrow emit (:2820,:2830) + orphaned producer (trend_structure:254-256,277)
  PRESERVE TRADABLES_ROW + price tape + price_vs_vwap + trend alignment + notifications
  -> regenerate golden fixture
--- publish (hourly workflow only) ---
  -> ui/dashboard.html -> ui/index.html -> readiness -> publish branch -> Pages
```

---

## 7. Schema / persistence

**None.** No artifact, `schema_version`, `PAYLOAD_SCHEMA_VERSION`, required-key, or
decision-contract change. The arrow cut removes one record field
(`trend_structure.daily_change_pct`) whose only reader is deleted in the same
slice. `artifact_flow_map.md` gains the panel as a new READER; `CALL_SITE_MAP.md`
gains the `market_state_panel.py` seam (F5).

---

## 8. FILES cone (ESTIMATED SURFACE — NOT YET APPROVED; five-axis, corrected)

Production:

| Op | File | Purpose |
|---|---|---|
| A | `cuttingboard/delivery/market_state_panel.py` | pure builder/validator: five axes, honest-absence per axis, per-axis provenance, HTML fragment |
| M | `cuttingboard/delivery/dashboard_renderer.py` | wire the panel before System State (outside PRD-219 region); CUT the tradables arrow (builder :1252-1258; emit gate/span :2820,:2830) |
| M | `cuttingboard/trend_structure.py` | remove orphaned `daily_change_pct` producer (:254-256, :277); preserve `price_vs_vwap` + alignment |

Tests:

| Op | File | Purpose |
|---|---|---|
| A | `tests/test_market_state_panel.py` | five-axis value/unavailable, honest per-axis provenance, POSITIONING qualifier preserved, PARTICIPATION no-12/12, no global as-of, no score, exactly-five-rows |
| M | `tests/test_dashboard_renderer.py` | panel wiring + placement-before-system-state; arrow cut incl. `test_prd220_tradables_arrow_before_price` (F3); keep price-tape tests |
| M | `tests/test_trend_structure.py` | remove/adjust the record `daily_change_pct` test (:570-586); preserve `price_vs_vwap` tests |
| M | `tests/test_dash_macro.py` | adjust any tradables-arrow assertion (verify during impl) |
| M | `tests/data/dashboard_pre_gex_golden.html` | regenerate: tradables-arrow spans removed |

Docs:

| Op | File | Purpose |
|---|---|---|
| M | `docs/artifact_flow_map.md` | record the panel as a new reader of the existing sidecars (G5) |
| M | `docs/SCHEMA_MAP.md` | note the panel's read-only consumption of existing carriers |
| M | `docs/CALL_SITE_MAP.md` | record the `market_state_panel.py` load/build/render seam (mirrors the GEX entry; file+function granularity) (F5) |

**NOT in the cone (per D-PLACEMENT):** `tests/test_dash_system_state.py` — the
panel sits BEFORE `id="system-state"`, outside that file's
`system-state`..`candidate-board` extraction region, so its assertions stay green
with no edit. Added only if the actual corrected seam proves otherwise.

**Verified-UNAFFECTED, NOT edited:** `cuttingboard/notifications/__init__.py`
(`_tradables_block` reads `q.price`); `TRADABLES_ROW`; the tradables PRICE tape;
`tests/test_notifications.py`.

**PRD-stage bookkeeping (F5 carve-out):** `docs/PROJECT_STATE.md:224` (PRD-199
arrow claim) must be retired/superseded at the Stage-0 PRD step; §12 tripwire
carves this governed update out of "any file beyond §8". `docs/PRD_REGISTRY.md`,
`prd_index.json`, `PROJECT_STATE.md`, the workplan ledger, and `PRD-312.md` are
Stage-0 bookkeeping, opened only AFTER this packet is review-clean and Dustin
rules — not part of this packet.

---

## 9. Estimated production/test LOC (ESTIMATED SURFACE — NOT YET APPROVED)

- **Production ~85-120 net.** `market_state_panel.py` ~85-120 (five-row builder +
  per-axis honest provenance + GEX qualifier reuse + honest-absence + fragment);
  renderer wiring ~+15; arrow-cut removal ~-20; trend producer removal ~-8.
  **Proposed ceiling <=150 net production LOC.**
- **Test ~140-200 net.** New `test_market_state_panel.py` ~120-170; arrow-cut test
  edits net ~0; golden regen is generated. **Proposed ceiling <=240 net test LOC.**
- **Tripwire (stop-and-renew):** any `runtime/`/ingestion edit; any new artifact,
  `schema_version`, or `PAYLOAD_SCHEMA_VERSION` change; any new derived metric or
  score; any INTRADAY re-introduction; any hourly intraday fetch; any file beyond
  §8 (except the PRD-stage `PROJECT_STATE.md:224` retirement carve-out); exceeding
  either ceiling.

---

## 10. Discriminating test / mutation matrix (five-axis, corrected)

| # | Case | Asserted (exact) | Mut? |
|---|---|---|---|
| M1 | ENVIRONMENT present | regime posture token rendered in the ENVIRONMENT row | YES |
| M2 | ENVIRONMENT unavailable | regime None (halt) -> row `unavailable`, never fabricated | YES |
| M3 | PERMISSION present | existing hourly-run permission value rendered | YES |
| M3b | PERMISSION unavailable | run + payload permission both null -> only PERMISSION row `unavailable` (F6) | YES |
| M4 | POSITIONING present | valid GEX -> existing qualified posture/value + `fetched HH:MM ET ~15m Cboe` | YES |
| M4b | POSITIONING qualifier preserved | the configured-dealer-assumption qualifier is present; removing it reddens (F7/D-1) | YES |
| M5 | POSITIONING unavailable | GEX absent/suppressed (`load_gex_snapshot` None / `render_fragment` "") -> row `unavailable` | YES |
| M6 | PARTICIPATION present | valid watchlist -> availability + `captured HH:MM ET` from `generated_at` | YES |
| M6b | PARTICIPATION partial-absence | some movement rows `n/a` -> no "12/12"/full-capture claim (F7/D-2) | YES |
| M7 | PARTICIPATION unavailable | movement absent/suppressed -> row `unavailable` | YES |
| M8 | EVENT present | red-folder `ok` -> `N events in 48h` / `no events in 48h` | YES |
| M9 | EVENT unavailable | red-folder `ok=False` -> row `unavailable` | YES |
| M10 | Structural exact-five | panel emits EXACTLY the five axis rows and NO aggregate/summary/score/global-as-of row (F6; catches an unlabeled composite) | YES |
| M11 | No fabrication | an unavailable axis never borrows another axis's value or a zero/neutral placeholder | YES |
| M12 | No INTRADAY | the panel renders NO INTRADAY/vs-VWAP row (D-INTRADAY B) | YES |
| M13 | Placement | the MARKET STATE block renders BEFORE `id="system-state"`; `test_dash_system_state.py` region assertions stay green | YES |
| M14 | Arrow cut: arrow gone | rendered board has no `tradable-arrow` span (incl. PRD-220 assertion updated) | YES |
| M15 | Arrow cut: price/notify preserved | tradables PRICE cells still render `current_price`; notifications `_tradables_block` unchanged | YES |
| M16 | Producer orphaned + removed | `trend_structure` record has no `daily_change_pct`; `price_vs_vwap` + alignment still present | YES |
| M17 | Panel absent-safe | if the panel cannot build, whole block suppressed baseline-neutral | YES |

Every guard ships a red test (PRD-198 inv. 4); whole-output baselines for
suppression; no guard-with-green-mutation. Mutation-red evidence produced at
implementation, not here.

---

## 11. Unavailable / failure semantics

Per-axis independent: any axis whose carrier is absent/suppressed renders that ROW
`unavailable` (never fabricated/borrowed; doctrine G6). PARTICIPATION shows honest
partial state, never a "12/12" overclaim. POSITIONING preserves the GEX qualifier.
The panel as a whole suppresses baseline-neutral only if it cannot build (M17). No
global as-of; no synchronous-state implication.

---

## 12. Stop-and-amend conditions

1. Any `runtime/`/ingestion edit (delivery-only).
2. Any new artifact, `schema_version`, `PAYLOAD_SCHEMA_VERSION`, or required-key change.
3. Any new derived metric, score, verdict, confluence, breadth, leadership,
   ranking, or bullish/bearish token.
4. Any trade-permission/decision mutation or axis feeding a decision surface.
5. Any new provider/producer/cadence/hourly-intraday-fetch or movement age-gate.
6. Re-introducing an INTRADAY/vs-VWAP row on the hourly panel (D-INTRADAY B).
7. Any global synchronized "as of" line.
8. Cutting/mutating `TRADABLES_ROW`, the price tape, notifications, `price_vs_vwap`,
   or trend alignment (only the arrow contribution is cut).
9. Placing the panel INSIDE the PRD-219 `system-state`..`candidate-board` region
   or modifying that region's semantics.
10. Dropping the GEX configured-assumption/delayed-source qualifier from POSITIONING.
11. Reopening/mutating the PRD-289 Market Control Card contract.
12. Any file beyond §8 (except the PRD-stage `PROJECT_STATE.md:224` retirement) or
    exceeding a §9 ceiling -> fresh GOV-2 §1 pass.

---

## 13. Materiality / lane

**MATERIAL** (cross-surface presentation seam + de-dup completeness claim +
rendered-surface-with-tests change). **HIGH-RISK** (`dashboard_renderer.py`;
PRD-121 R11). MICRO-ineligible. Governance hold: DRAFT + self-named
(GOV-0/PRD-186), held for Dustin. After review-clean + design-direction ruling:
Stage-0 PRD-312 -> independent PRD review -> Gate A.

---

## 14. What gets ADDED, CUT, and left UNTOUCHED

**ADDED:** `market_state_panel.py` (pure builder) + a thin renderer wire-in before
System State; one new five-axis MARKET STATE block; `artifact_flow_map.md` +
`CALL_SITE_MAP.md` reader/seam entries.

**CUT:** the Macro-Tape tradables daily-change ARROW (builder + emit gate/span);
the orphaned `trend_structure.daily_change_pct` producer; the PRD-199 + PRD-220
arrow assertions; regenerate the golden fixture.

**UNTOUCHED (verified):** `TRADABLES_ROW`, the tradables PRICE tape, notifications
`_tradables_block`; Trend-Structure `price_vs_vwap` + alignment; the PRD-289
Market Control Card contract; the PRD-219 protected region; `runtime/`, ingestion,
all decision/universe/permission logic; GEX and Movement card internals (consumed
read-only); all schema/persistence surfaces; INTRADAY's existing full-run surfaces.

---

## 15. Open design/review questions

None blocking. All prior owner questions (D-INTRADAY, D-PLACEMENT, D-1, D-2) are
ruled and folded. Remaining choices are implementation-local (exact fragment
wording within the ruled semantics) and belong to the Stage-0 PRD.

---

## 16. Author self-verification (GOV-2 §3)

All at `main` @ `731b5ee` / corrected head; source byte-identical to baseline
(`git diff 731b5ee..HEAD -- cuttingboard/ tests/` empty):
- **[F1/INTRADAY]** hourly trend-structure gets daily OHLCV (`ingestion.py:119-124`)
  -> SPY `price_vs_vwap` `NOT_COMPUTED` (committed snapshot); no hourly
  intraday-session fetch (`fetch_intraday_session_bars` only at `runtime:1238` in
  `_run_pipeline`). INTRADAY dropped. CONFIRMED.
- **[F2/PERMISSION]** carrier = `latest_hourly_run.json.permission`
  (`runtime:2363-2369`; renderer run-first `dashboard_renderer.py:2172-2175`);
  `_build_system_state` has no permission (`contract.py:251-259`). CONFIRMED.
- **[F3]** `test_prd220_tradables_arrow_before_price`
  (`tests/test_dashboard_renderer.py:4007-4013`) enumerated in the cut. CONFIRMED.
- **[F4/placement]** panel before `id="system-state"` is outside the
  `test_dash_system_state.py` region (`:82-93,109-127`); file stays out of cone.
  CONFIRMED.
- **[F5]** `CALL_SITE_MAP.md` added (`:3-7,63-69` GEX precedent);
  `PROJECT_STATE.md:224` retirement carved out of the tripwire. CONFIRMED.
- **[F6]** M3b + structural M10 added. **[F7]** M4b (GEX qualifier) + M6b
  (partial-absence) added; `watchlist_sidecar.py:76-92`, `movement_card.py:86-93`,
  `gex_card.py:175-191`. CONFIRMED.
- **[arrow final-reader]** `trend_structure.daily_change_pct` (`:254-256,277`) read
  only at `dashboard_renderer.py:1254`; `TRADABLES_ROW` shared by price tape
  (`:1304`), emit (`:2831`), notifications (`notifications/__init__.py:119`,
  `q.price`) — preserved. Golden fixture has 6 arrow spans. CONFIRMED at the
  corrected head.
- **[delivery-only]** all five carriers already loaded by the renderer; no
  runtime/ingestion/artifact/schema change. CONFIRMED.

Author self-verification is NOT independent review. Event-2 confirmation runs on
this committed head.

---

## 17. Packet review records (GOV-2 §2, §7)

### INITIAL PACKET REVIEW (Event-1) — COMPLETE
Record: `MARKET_STATE_EVENT1_CODEX_REVIEW_2026-08-22.md`. Reviewer: independent
Codex, fresh context, read-only, high. Reviewed SHA `66d9731` (v0.1). Verdict:
FINDINGS (F1-F7). Dispositions folded here:
- **F1 (BLOCKING) — RESOLVED by D-INTRADAY B** (drop INTRADAY; no runtime change;
  intraday stays on existing surfaces).
- **F2 (P1) — ACTIONED** (permission carrier = `latest_hourly_run.json.permission`).
- **F3 (BLOCKING) — ACTIONED** (PRD-220 arrow test enumerated; file in cone).
- **F4 (BOUNDARY) — RESOLVED by D-PLACEMENT** (before System State, outside the
  PRD-219 region; `test_dash_system_state.py` out of cone).
- **F5 (BOUNDARY) — ACTIONED** (`CALL_SITE_MAP.md` in cone; PROJECT_STATE tripwire
  carve-out).
- **F6 (P1) — ACTIONED** (M3b permission-unavailable; M10 structural exact-five).
- **F7 (P1) — ACTIONED by D-1/D-2** (M4b GEX qualifier; M6b partial-absence; no
  12/12 overclaim; no re-presented GEX net without qualifier).

### EXACT-CORRECTED-HEAD CONFIRMATION (Event-2) — PENDING
To be recorded as `MARKET_STATE_EVENT2_CODEX_CONFIRMATION_2026-08-22.md`:
corrected SHA, enumerated F1-F7 dispositions confirmed, five-axis consistency,
placement, GEX qualifier, PARTICIPATION no-overclaim, arrow proof, FILES/LOC
match, no new MATERIAL boundary; verdict.

---

## 18. Revision log

- **v0.3 (2026-08-22):** owner design-direction rulings folded — five-axis panel
  (INTRADAY dropped, D-INTRADAY B), placement before System State (D-PLACEMENT),
  qualified GEX POSITIONING (D-1), availability-only PARTICIPATION (D-2), arrow cut
  retained. F1-F7 dispositioned. Supersedes v0.1 + v0.2.
- **v0.2 (2026-08-22):** consolidated correction of Event-1 F1-F7; mechanical
  findings actioned, owner-blocking findings escalated; DESIGN INCOMPLETE.
- **v0.1 (2026-08-22):** initial provisional MATERIAL packet (six-axis).

---

END OF PACKET v0.3 — DESIGN-CLEAN CANDIDATE / NOT YET REVIEW-CLEAN — NO
IMPLEMENTATION AUTHORITY. Codex Event-2 (EXACT-CORRECTED-HEAD CONFIRMATION) runs on
this committed head. Gate A is neither requested nor granted.
