# Intraday Session-Candle Card - MATERIAL Packet (A1 = A1-P producer + A1-C consumer)

Date: 2026-08-30 (corrected after Codex review of `0fda661`)
Status: MATERIAL packet, DESIGN-ONLY, decomposed into two ordered units.
Ready for independent review -> owner ruling -> Stage-0 (x2) -> Gate A (x2). No
implementation authorized by this document.
Baseline: `main` at `85beb03`; packet branch `claude/intraday-a1-packet-2026-08`.

## 0. Authority, Helm rulings, and corrections

Accepted direction is Helm's (Dustin), delivered by charge and confirmed
in-session 2026-08-30. It SUPERSEDES the daily-anchored recommendation in the
feasibility memo (`audits/intraday-feasibility-2026-08/INTRADAY_FEASIBILITY_MEMO_2026-08-28.md`,
branch `claude/intraday-feasibility-memo-2026-08` `d1e90a4`, NOT on `main`);
the memo is retained as evidence, not authority.

Helm rulings incorporated (this revision):
1. Split A1 into producer THEN consumer; NO G3/G4/G8 override.
2. Canonical primary = the exact existing chartable-primary selection, shared by
   producer and consumer (one definition, no parity approximation).
3. Persist validated 1-minute source bars; consumer deterministically renders
   full-session 5-minute bars.
4. Freshness = current ET session + per-symbol `through`; max age 90 min; max
   future skew 5 min; any structural failure omits the whole symbol.
5. Drop the opportunistic-reuse policy.

Precedent correction (Codex REQUIRED #1, #9): the prior draft wrongly cited
PRD-311/312 as a same-PR producer+consumer precedent. They added NO persisted
producer artifact (PRD-311 reused an existing artifact; PRD-312 added no
producer/artifact/cadence). The correct structural precedent is the price-bars
lineage, which WAS split: SIDECAR producer PRD-320 + CONSUMER PRD-321. A1 mirrors
that split. PRD-311's ~230 net LOC (not ~137) is not used as a ceiling anchor;
ceilings below are ESTIMATED SURFACE ranges.

## 1. Materiality and why two units

MATERIAL under GOV-2 s1: a new persisted schema surface with a reader, and a
carrier crossing runtime + persistence + dashboard (GOV-2 s1). Because doctrine
G3 (producer ships before consumer), G4 (no consumer bundling), and G8 (one
bounded question per PRD) bind and Helm declined an override, A1 is TWO ordered
implementation units, each its own Stage-0 + Gate A:

- A1-P (SIDECAR producer): acquire + validate + persist 1m source bars. Safe to
  merge with A1-C absent (its artifact has no reader yet).
- A1-C (HIGH-RISK CONSUMER): read the artifact, derive 5m display bars, render on
  the canonical-primary card. Lands only after A1-P is on `main`.

## 2. Accepted behavior (A1)

Per hourly in-session run, co-produce a run-local snapshot of current-session
1-minute candles for the canonical primary setup symbol + SPY (deduped), and
render a full-session 5-minute intraday chart on the primary card when the
snapshot is fresh; otherwise fall back to the existing daily chart + level
ladder. Honest caption (ET session date + through-time). No cross-run
persistence. No decision/regime/qualification/sizing/notification effect.

## 3. Feasibility basis (unchanged, re-confirmed by Codex)

The hourly run pays for NO guaranteed intraday session bars today:
`fetch_intraday_session_bars("SPY")` is daily-only (`runtime/__init__.py:1247-1251`);
the only hourly intraday fetch is SHORT-gated (`runtime/__init__.py:1726-1733`).
A1-P therefore adds at most 2 logical 1m fetches per hourly slot (~18/day) via
the EXISTING `fetch_intraday_session_bars` (no new fetch function, no scheduler).
Correction (Codex RECOMMENDED #1): at the co-production seam the run holds
normalized quotes + market map + candidate DAILY frames only - NOT a SPY session
frame; A1-P must fetch it.

## 4. Canonical primary - the single shared definition (Codex #5; Helm ruling 2)

One pure function, `select_chartable_primary(...)`, added in A1-P and living in
`cuttingboard/delivery/setup_chart.py`: the first candidate, in the renderer's
`_TIER_DEFS` grade order over the same integrator-filtered candidate set
(`dashboard_renderer.py:2500-2513`), whose `render_setup_chart_svg(...)` is
non-empty (the renderer's actual chartability gate,
`dashboard_renderer.py:2277-2319,3111-3143`). No `_TIER_DEFS`-only approximation.

- A1-P calls it at the seam and RECORDS the result as `primary_symbol` in the
  sidecar, then fetches 1m for `[primary_symbol, "SPY"]` deduped.
- A1-C rewires the renderer's chart-slot selection (3111-3143) to call the SAME
  function (behavior-preserving, golden-identical), and renders the intraday
  chart for the sidecar's recorded `primary_symbol` when fresh.

Because the consumer reads the producer's recorded selection (both grounded in
the identical function), producer/consumer agreement is by construction, not
approximation. If `primary_symbol` is not a rendered candidate this pass,
intraday is omitted for it (honest absence) and the primary card shows its daily
chart. Bounded Stage-0 implementation item (not a product decision): confirm the
selector's inputs (candidate order, daily bars, level context, price) are
available at the `780-802` seam without duplicating heavy renderer prep; if level
context is not cheaply available pre-render, the recorded `primary_symbol` (the
producer's single computation) remains the authority the consumer trusts.

## 5. A1-P - SIDECAR producer

Objective: acquire, strictly validate, and persist current-session 1m source
bars for `[canonical primary, SPY]` as a run-local additive artifact; record the
canonical `primary_symbol`. No reader.

Seam: `runtime/__init__.py:780-802` (the existing sidecar block). New writer
`_write_intraday_bars_snapshot(...)` clones `_write_price_bars_snapshot`
(`:2552`, atomic tmp+`.replace` `:2592-2594`, catch-and-log isolation
`:2595-2596`).

Schema `logs/intraday_bars_snapshot.json`, schema_version 1 (Codex #3 corrected -
`ts` column included, six-value bars):
```
{
  "schema_version": 1,
  "generated_at": "<ISO-8601 UTC>",
  "session_date": "YYYY-MM-DD",             # ET regular-session date of the bars
  "primary_symbol": "<canonical primary>",  # recorded selection (Section 4)
  "source": {"producer":"hourly","provider":"yfinance","interval":"1m","adjusted":false},
  "columns": ["ts","Open","High","Low","Close","Volume"],
  "symbols": {
    "SPY":       {"through":"<ISO ts last bar>","row_count":N,"bars":[[ts,o,h,l,c,v], ...]},
    "<PRIMARY>": { ... }
  }
}
```
Strict WHOLE-SYMBOL validation (Codex #3; no cleaned-subset rendering): a symbol
entry is written only if source/columns match, timestamps are timezone-aware,
strictly ordered, all within the ET regular session, `row_count == len(bars)`,
`through == last ts`, OHLCV finite and coherent (H>=max(O,C), L<=min(O,C), V>=0),
and `session_date` consistent. Any violation OMITS the whole symbol; never a
partial record.

Acquisition isolation (Codex #6): the fetch + write are wrapped in their own
per-symbol guard positioned so a raised fetch (incl. the pre-retry
LIVE_DATA_FORBIDDEN raise at `ingestion.py:213-214`) CANNOT reach the post-send
failure path (`runtime/__init__.py:806-815`) and cannot emit a second failure
notification. Red test proves a raised intraday fetch leaves hourly status,
artifacts, and exactly-once notification unchanged.

Staging (Codex #7; Acceptance #6): `logs/intraday_bars_snapshot.json` is UNTRACKED
(`.gitignore`), unlike tracked `price_bars_snapshot.json`. Staging must be
CONDITIONAL - present => `git add -f` it; absent => no-op (never fail the publish
step on a missing path). Not in the startup restore list
(`hourly_alert.yml:104-105`) => run-local. Regression in test_ci_artifact_hygiene.

FILES (A1-P):
- `cuttingboard/runtime/_constants.py` - add `INTRADAY_BARS_PATH` beside
  `PRICE_BARS_PATH` (`:59`).
- `cuttingboard/runtime/__init__.py` - import it; `_write_intraday_bars_snapshot`;
  seam fetch/validate/write + record `primary_symbol`; acquisition isolation.
- `cuttingboard/delivery/setup_chart.py` - add pure `select_chartable_primary`
  (used by A1-P now; renderer rewire is A1-C).
- `.github/workflows/hourly_alert.yml` - CONDITIONAL staging (238-247 block); NOT
  in restore (105).
- `docs/artifact_flow_map.md` - new artifact + its one writer (G5).
- `docs/SCHEMA_MAP.md`, `docs/CALL_SITE_MAP.md` - producer entries.

Tests (A1-P):
- `tests/test_intraday_bars_sidecar.py` (NEW) - envelope incl `ts`,
  whole-symbol validation, per-symbol omission, `primary_symbol` recorded,
  producer tag, run-local. Template: `tests/test_price_bars_sidecar.py:259-327`.
- `tests/test_ci_artifact_hygiene.py:34-45,856-875` - conditional-staging (missing
  => no-op green; present => staged) and no-restore.
- `tests/test_hourly_alert.py:1717-1721` - network-free stub for the new fetch.
- `tests/test_observe_only_isolation.py:91-116` - fetch cannot perturb the
  decision pipeline / notification (isolation red test).
- `tests/test_runtime_package_surface.py:43-55` - new facade/patch surface.
- `tests/test_setup_chart.py:188-192` - `select_chartable_primary` unit tests.

ESTIMATED SURFACE - NOT YET APPROVED (Codex #9; binding ceiling only at Gate A):
production ~90-140 net LOC over 3 code files + 1 workflow + 3 doc/map files;
tests ~6 files. Lane: SIDECAR.

Acceptance (A1-P): valid schema-versioned run-local sidecar with strict
whole-symbol validation and recorded `primary_symbol`; acquisition failure omits
the whole symbol and cannot trigger a second failure notification; missing
sidecar => staging no-op; dashboard output byte-identical to pre-A1-P (renderer
untouched); each guard ships a mutation-red test. SAFE-TO-MERGE-ALONE: the
artifact has no reader; only new cost is ~18 fetches/day.

## 6. A1-C - HIGH-RISK CONSUMER

Objective: on a fresh valid sidecar, render a deterministic full-session 5m
intraday chart (derived from the validated 1m truth) on the canonical-primary
card; otherwise baseline-identical.

Derivation (Helm ruling 3): a pure, deterministic 1m -> 5m resample (right-closed
regular-session bins; O=first, H=max, L=min, C=last, V=sum) over the validated 1m
bars. No provider call; consumer reads only the sidecar.

Freshness admission (Helm ruling 4; Codex #4): admit a symbol only if
`session_date` == current ET regular session AND `generated_at` age <= 90 min AND
per-symbol `through` is within the current ET session, not older than 90 min, not
more than 5 min in the future. Any structural failure omits the whole symbol.
Missing/stale/invalid sidecar => byte-identical baseline (GEX R1 model:
`gex_card.py:108-137,170-174`, emit guarded `if frag:` at
`dashboard_renderer.py:3181-3189`).

Rendering: rewire the chart-slot primary selection (`3111-3143`) to call
`select_chartable_primary` (behavior-preserving; golden-identical test). On a
fresh sidecar, the primary card's single chart slot shows the 5m intraday chart
(honest ET session/through caption) INSTEAD of the daily chart; the daily chart +
level ladder remain the fallback off the intraday branch and whenever intraday is
absent. `setup_chart.render_setup_chart_svg` is extended to render the supplied
full-session 5m window (Codex #2: it is NOT interval-agnostic today - it has a
trailing 40-bar contract at `setup_chart.py:86-98,138`); the daily path is
unchanged.

FILES (A1-C):
- `cuttingboard/delivery/dashboard_renderer.py` - `_load_intraday_bars_snapshot`,
  `_intraday_by_symbol` (freshness), rewire selection to the shared helper, render
  intraday on the primary card.
- `cuttingboard/delivery/setup_chart.py` - full-session 5m rendering path + the
  pure 1m->5m derivation helper; daily path untouched.
- `docs/artifact_flow_map.md` - add the reader.
- `README.md:43` - correct the "daily-candle chart" product truth (Codex #8).
- `docs/SCHEMA_MAP.md`, `docs/CALL_SITE_MAP.md` - consumer entries.
- `docs/PROJECT_STATE.md`, `docs/DECISIONS.md`, `docs/PRD_REGISTRY.md`,
  `docs/prd_index.json` - lifecycle/closeout bookkeeping (per PRD_PROCESS).

Tests (A1-C):
- `tests/test_dashboard_renderer.py` - intraday-preferred on fresh sidecar;
  suppression on stale/missing/invalid (baseline-identical golden); selection
  rewire golden-identical.
- `tests/test_dash_candidates.py:831-925` - primary-chart selection via the shared
  helper; fallback behavior.
- `tests/test_setup_chart.py` - deterministic 1m->5m derivation; full-session
  render; daily path unchanged.

ESTIMATED SURFACE - NOT YET APPROVED: production ~120-190 net LOC over 2 code
files + doc/bookkeeping; tests ~3 files. Lane: HIGH-RISK / CONSUMER
(`dashboard_renderer.py` is a consumer high-risk file, PRD_PROCESS).

Acceptance (A1-C): fresh valid sidecar => canonical-primary card shows a
deterministic full-session 5m chart from validated 1m truth, honestly captioned;
stale/missing/invalid => byte-identical baseline; daily behavior unchanged off
the intraday branch; renderer selection provably identical to pre-A1-C except the
intraday substitution; each guard mutation-red.

## 7. Codex review disposition (concise; full transcript NOT persisted per charge)

Reviewed head `0fda661`; verdict FINDINGS (design incomplete). All 9 REQUIRED
addressed; 3 RECOMMENDED dispositioned.
- R1 same-PR precedent false -> split into A1-P/A1-C; precedent corrected (Sec 0,1).
- R2 setup_chart not interval-agnostic -> A1-C extends it; test added (Sec 6).
- R3 schema `ts` + strict validation -> schema + whole-symbol validation (Sec 5).
- R4 per-symbol freshness -> Helm ruling 4 admission rules (Sec 6).
- R5 canonical primary -> single shared `select_chartable_primary`, recorded
  primary_symbol, no approximation (Sec 4).
- R6 acquisition isolation -> own guard off the post-send path + red test (Sec 5).
- R7 untracked force-add -> conditional staging; missing => no-op (Sec 5).
- R8 FILES/test sweep -> full inventory across both units, real
  `runtime/_constants.py` home, all asserting tests enumerated (Sec 5,6);
  mechanical cross-file inventory cross-checked with Recon Garden v1
  (call-site classification, deterministically spot-checked, telemetry recorded).
- R9 ceiling label/estimate -> ESTIMATED SURFACE ranges per unit; PRD-311 LOC
  corrected (Sec 0,5,6).
- RECOMMENDED 1 (seam has no SPY session frame) -> corrected (Sec 3).
- RECOMMENDED 2 (drop reuse) -> dropped (Helm ruling 5).
- RECOMMENDED 3 (name all GOV-2 triggers; HIGH-RISK consumer) -> Sec 1, 6.

## 8. Doctrine compliance

G1 description-not-prediction: raw candles + provenance only. G2: sidecar read
only by the renderer; no decision/regime/sizing/notification effect. G3/G4/G8:
satisfied by the producer/consumer split (Helm declined override). G5: additive
artifact, one writer (A1-P), one reader (A1-C), recorded in artifact_flow_map. G6:
whole-symbol omission + baseline-neutral suppression + honest caption. G7:
adjacent price-bars lineage (PRD-320/321) is COMPLETE; no unresolved neighbor.

## 9. Rejected alternatives

1. Daily-anchored zero-cost (memo Option A): one pre-market snapshot, not
   current-session hourly-fresh. Rejected by Helm.
2. Six-symbol hourly (memo Option B, ~54 ops/day): the A2 expansion; out of scope.
3. Cross-run intraday cache: adds persisted-across-runs carrier; rejected -
   run-local suffices.
4. Producer/renderer independently re-deriving primary: rejected as a parity
   approximation (Codex #5); replaced by one recorded canonical selection.

## 10. Remaining genuine Helm decisions

Most are resolved by rulings 1-5. Remaining, low-stakes, for Gate A:
1. Confirm the intraday chart REPLACES the daily chart in the primary card's
   single chart slot when fresh (daily as fallback), rather than showing both.
2. Confirm `primary_symbol` is recorded by the producer and trusted by the
   consumer (Section 4 design) vs. both sites independently computing (still one
   function, but two evaluations). Recommendation: record-and-trust.
Bounded Stage-0 (implementation, not product): selector-input availability at the
producer seam (Section 4).

## 11. DECISIONS.md entry (to land at the appropriate Stage-0)

```
## 2026-08-30 - Intraday session-candle card: A1 selected over daily-anchored,
split producer+consumer (ruled: Dustin)

Helm selects A1 (current-session hourly-fresh 1m candles for the canonical primary
setup symbol + SPY, run-local, display-only) over the daily-anchored recommendation
in audits/intraday-feasibility-2026-08/INTRADAY_FEASIBILITY_MEMO_2026-08-28.md
(branch claude/intraday-feasibility-memo-2026-08 d1e90a4), which is superseded as a
recommendation and retained as evidence. Per G3/G4/G8 (no override), A1 is two
ordered units: A1-P SIDECAR producer (persist validated 1m source bars) then A1-C
HIGH-RISK consumer (deterministic full-session 5m render on the canonical-primary
card). Canonical primary = the exact chartable-primary selection, shared. Freshness:
current ET session + per-symbol through, max age 90m, max future skew 5m, whole-symbol
omission on structural failure. Accepted cost: <=2 logical 1m fetches/hourly slot
(~18/day) via existing fetch_intraday_session_bars. MATERIAL (GOV-2 s1); each unit
takes its own Stage-0 + Gate A. No implementation authorized by this entry.
```

## 12. STOP / next order

DESIGN boundary. Next: independent/Codex review of THIS corrected head -> Helm
ruling -> A1-P Stage-0 + Gate A -> A1-P merge -> A1-C Stage-0 + Gate A. No
implementation, no PRD number allocated, no merge by this packet.
