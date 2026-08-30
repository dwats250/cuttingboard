# Intraday Session-Candle Card - MATERIAL Packet (A1)

Date: 2026-08-30
Status: MATERIAL packet, DESIGN-ONLY. Ready for independent review -> owner
ruling -> Stage-0 -> Gate A. No implementation authorized by this document.
Baseline inspected: `main` at `85beb03` (PR #289 README truth-sync MERGED
2026-08-30; its only diff is `README.md`, touching no A1 code seam, so every
seam anchor below remains valid).

## 0. Authority and the superseded-memo relationship (honest record)

- Accepted direction: Helm (Dustin) selected A1 - current-session,
  hourly-fresh 1-minute session candles for the primary setup symbol + SPY,
  co-produced within the existing hourly run, no cross-run persistence.
  Delivered as the session charge (Mode DESIGN) and confirmed in-session on
  2026-08-30.
- Superseded memo: the only committed intraday artifact is a read/design-only
  feasibility memo, `audits/intraday-feasibility-2026-08/INTRADAY_FEASIBILITY_MEMO_2026-08-28.md`,
  present ONLY on branch `claude/intraday-feasibility-memo-2026-08` (`d1e90a4`),
  NOT on `main`. It uses Option A/B/C labels (not A0/A1) and RECOMMENDS the
  daily-anchored path (Option A) while flagging the hourly-fresh path (Option B)
  as "a separate, explicit owner decision ... NOT recommended as a default"
  (memo:76-78). Per the expansion doctrine, that memo is evidence, not
  authority; an explicit Helm ruling outranks it (CLAUDE.md Precedence 1). This
  packet records that Helm's A1 ruling SUPERSEDES the memo's recommendation. The
  memo is retained as evidence, not deleted.
- No A0-vs-A1 adjudication is committed anywhere in the repo. Section 12 gives
  the exact `docs/DECISIONS.md` entry that must land (at Stage-0) to make this
  ruling canonical.

## 1. GOV-2 s1 materiality

MATERIAL. This introduces a new persisted schema surface
(`logs/intraday_bars_snapshot.json`) with a reader, and a carrier that crosses
runtime + persistence + dashboard. It follows the full order: packet ->
independent/Codex review -> owner ruling -> Stage-0 scaffold -> Gate A. Same
classification the feasibility memo reached (memo:44-48).

## 2. Accepted product behavior (A1)

- On each in-session hourly run, co-produce a snapshot of CURRENT-SESSION
  1-minute candles for two symbols at most: the primary setup symbol + SPY,
  deduped (one symbol when the primary setup symbol IS SPY).
- Render an intraday candle card on the dashboard for a symbol when its
  current-session snapshot is present and fresh; otherwise that symbol falls
  back to the existing daily setup chart + level ladder. Per-symbol omission on
  fetch failure. Absence/stale/invalid = byte-identical baseline dashboard.
- Honest caption: session date + through-time (timestamp of the last bar).
- Same-run co-production only; NO cross-run persistence (each hourly run writes
  its own fresh snapshot; the artifact is never restored from a prior run).
- No decision, regime, qualification, sizing, or notification effect.

## 3. Feasibility correction (the acquisition-cost resolution)

The charge phrase "from existing in-session hourly runs" does NOT imply reuse:
the hourly run (`_execute_notify_run`) fetches ZERO guaranteed intraday session
bars today. The only hourly intraday fetch is `fetch_intraday_bars(symbol)` at
`runtime/__init__.py:1730`, gated to SHORT candidates inside
`_apply_intraday_short_permission`. `fetch_intraday_session_bars("SPY")` runs
ONLY in the daily `_run_pipeline` (`runtime/__init__.py:1250`). So SPY 1m is not
paid in the hourly run.

Resolution (Helm-confirmed, Acceptance #4 "otherwise" branch): A1 adds same-run
1-minute fetches for the primary setup symbol + SPY via the EXISTING
`fetch_intraday_session_bars` (no new fetch function, no new scheduler).
Cost: at most 2 logical 1m fetches per hourly slot; ~18 logical fetches/day
(fewer when primary == SPY, or when a qualifying session frame is already paid
this run). This is far below the memo's six-symbol Option B (~54 ops/day), which
is the A2 expansion and is explicitly out of scope.

## 4. Confirmed seams (file:line)

Producer (reuse, no new function):
- `cuttingboard/ingestion.py:281 fetch_intraday_session_bars(symbol)` ->
  `retain_full_session=True`, complete 09:30-16:00 current-session 1m frame,
  columns Open/High/Low/Close/Volume, `None` on per-symbol failure. (Wraps
  `fetch_intraday_bars`, ingestion.py:195, yfinance period=7d interval=1m,
  filtered to the latest regular session.)

Same-run co-production seam:
- `cuttingboard/runtime/__init__.py:780-802` - the hourly sidecar block inside
  `_execute_notify_run` (528). Primary + SPY data are in memory here; today it
  writes price_bars / trend_structure / watchlist snapshots. The new intraday
  fetch + write attach here.

Persistence template (clone exactly):
- `cuttingboard/runtime/__init__.py:2552 _write_price_bars_snapshot(...)`;
  `PRICE_BARS_PATH` imported at 165; atomic tmp+`.replace` at 2592-2594;
  per-symbol omission of absent/malformed/zero-row frames (2574-2577);
  catch-and-log isolated so it never breaks the seam.
- Run-local mechanism (workflow, not code): `.github/workflows/hourly_alert.yml`
  force-adds `logs/price_bars_snapshot.json` at line 244 (publish) but it is
  ABSENT from the startup restore list at line 105 (`ci_restore_publish_state.sh`).
  The new artifact must copy this asymmetry: force-added, never restored.

Dashboard render seam + fallback:
- `cuttingboard/delivery/dashboard_renderer.py` - `_load_price_bars_snapshot`
  (1152, soft), `_price_bars_by_symbol` (1187, per-symbol omission + age guard),
  `_render_candidate_card` (2111) picks the primary full-width chart slot
  (3111-3143). Existing daily fallback that remains: `_render_setup_chart_block`
  (2098) + `_render_level_ladder` (1951).
- Suppression model (GEX R1): `cuttingboard/delivery/gex_card.py` - pure builder
  returns `None`/`""` to suppress; renderer guards emission `if frag:` so
  absent/stale/invalid = byte-identical baseline.
- Chart body: `cuttingboard/delivery/setup_chart.py render_setup_chart_svg` is
  interval-agnostic (PRD-321); it captions from `as_of` and carries
  `source.interval`. Reuse; edit only if an intraday through-time caption needs
  a tweak (flagged open, Section 11).

## 5. Proposed schema (`logs/intraday_bars_snapshot.json`, schema_version 1)

```
{
  "schema_version": 1,
  "generated_at": "<ISO-8601 UTC>",          # = run_at_utc of the hourly run
  "session_date": "YYYY-MM-DD",              # regular-session date the bars belong to
  "source": {"producer": "hourly", "provider": "yfinance",
             "interval": "1m", "adjusted": false},
  "columns": ["Open","High","Low","Close","Volume"],
  "symbols": {
    "SPY":       {"through": "<ISO ts of last bar>", "row_count": N, "bars": [[ts,o,h,l,c,v], ...]},
    "<PRIMARY>": { ... }
  }
}
```

- schema_version: integer, strict-equality checked by the consumer, bool-rejected
  first (gex_card.py:113 convention). Start at 1.
- Per-symbol omission: a symbol whose frame is absent/malformed/zero-rows is
  OMITTED entirely (never a partial entry), mirroring 2574-2577.
- No derived/analytic field. Description, not prediction (doctrine G1).

## 6. Provenance / freshness / degradation

- Provenance: `source.provider="yfinance"`, `source.interval="1m"`,
  `producer="hourly"`, `generated_at`, per-symbol `through`.
- Freshness (consumer): the daily 5-day age guard is WRONG for intraday. The
  intraday card renders for a symbol only if BOTH:
  (a) `session_date` equals the renderer-clock current regular-session date, AND
  (b) `generated_at` age <= INTRADAY_MAX_AGE (recommend 90 min; hourly cadence
      is ~60 min, so >90 min means a missed/failed slot -> suppress).
  Otherwise suppress that symbol's intraday card (fall back to daily chart).
- Degradation ladder (all baseline-neutral): missing artifact -> no intraday
  cards; stale/invalid schema -> suppress; per-symbol fetch failure -> that
  symbol omitted; empty snapshot -> byte-identical baseline dashboard.

## 7. Symbol selection at the runtime seam

The renderer selects the primary card as the highest-grade-tier candidate with
usable bars (dashboard_renderer.py:3111-3143). The runtime seam has no single
"primary" variable, so it must pick the top-ranked candidate from
`market_map["symbols"]` by the same grade-tier ordering the renderer uses
(`_TIER_DEFS`), take that symbol + "SPY", dedupe -> 1 or 2 symbols, and fetch 1m
for them. Recommended: extract the tier-ordering into a shared helper so runtime
selection and renderer selection cannot drift. If they still differ for a given
run, the rendered primary card simply lacks an intraday entry and falls back to
its daily chart - acceptable under the per-symbol omission contract. (Open
decision 11.1.)

## 8. Opportunistic reuse (Helm: only if a qualifying fetch is already paid)

If the primary symbol or SPY was already fetched intraday this run, reuse that
frame instead of re-fetching. Caveat: the only paid hourly intraday fetch today
is `fetch_intraday_bars` (line 1730), a truncated trailing window
(MAX_INTRADAY_RETURN_BARS), not the full `fetch_intraday_session_bars` frame a
candle chart wants. Recommended policy: reuse ONLY a session-shaped paid frame;
otherwise fetch `fetch_intraday_session_bars`. In practice the hourly run holds
no session frame today, so reuse rarely applies and A1 fetches for primary+SPY.
Documented as an optimization, not a dependency. (Open decision 11.3.)

## 9. FILES (proposed lock; exact lock set at Stage-0)

Production:
1. `cuttingboard/runtime/__init__.py` - fetch primary+SPY 1m at the 780-802
   seam; new `_write_intraday_bars_snapshot(...)` writer cloned from 2552.
2. module defining `PRICE_BARS_PATH` - add `INTRADAY_BARS_PATH`
   (`logs/intraday_bars_snapshot.json`) beside it.
3. `cuttingboard/delivery/dashboard_renderer.py` - `_load_intraday_bars_snapshot`,
   `_intraday_bars_by_symbol` (freshness guard), and a prefer-intraday branch in
   `_render_candidate_card` with the existing daily block as fallback.
4. `cuttingboard/delivery/setup_chart.py` - reuse; touch only if an intraday
   caption tweak is required (Section 11.5).
5. `.github/workflows/hourly_alert.yml` - add `logs/intraday_bars_snapshot.json`
   to the publish force-add list (~244). DO NOT add to the restore list (105).
6. `docs/artifact_flow_map.md` - record the new artifact writer + reader (G5).
7. `docs/SCHEMA_MAP.md`, `docs/CALL_SITE_MAP.md` - update the recon cache.

Tests (PRD-158 sweep at Stage-0; add every asserting file):
- `tests/test_intraday_bars_sidecar.py` (NEW) - writer envelope, per-symbol
  omission, producer tag, run-local (asserts not in the restore list). Template:
  `tests/test_price_bars_sidecar.py`.
- `tests/test_dashboard_renderer.py` - intraday-preferred, daily-fallback,
  suppression on stale/missing (baseline-identical).
- `tests/test_setup_chart.py` - only if setup_chart is touched.
- runtime co-production + SHORT-path non-interference test (existing
  `tests/test_gap_down_permission_integration.py` patches the fetcher; ensure the
  new fetch does not perturb SHORT permission).

## 10. Implementation ceiling

- <= ~120 net production LOC (in line with PRD-311 ~137 / PRD-312 ~137).
- <= 4 production files + 1 workflow + 2 map docs.
- <= 3 test files.
- No new dependency, no new fetch function, no new scheduler/cron, no schema on
  an existing pipeline artifact, no decision/regime/sizing/notification change.
- Every guard ships a mutation-verified red test.

## 11. Doctrine compliance (expansion doctrine G-invariants)

- G1 description-not-prediction: raw observed candles + provenance only.
- G2 observation-not-permission: snapshot is written to a NEW artifact and read
  ONLY by the renderer; no decision/regime/qualification/sizing/notification
  path reads it.
- G5 additive artifact: one new versioned path, one writer, recorded in
  `artifact_flow_map.md`.
- G6 honest absence: per-symbol omission + suppress-to-baseline; honest caption.
- G8 one bounded question: display current-session candles for primary+SPY.
  Not cadence (reuses the existing hourly cron), not the A2 six-symbol
  expansion, not decision coupling.
- Same-PR producer+consumer: justified by precedent PRD-311 (movement_card) and
  PRD-312 (mkt-state), which co-produced a run-local snapshot AND its render in
  one MATERIAL CONSUMER PRD. This differs from the GEX/news producer-first gates
  (G3/G4) because the intraday provider (yfinance 1m) is already evidenced and
  used in the daily run - there is no unproven external provider to gate.

## 12. Rejected alternatives

1. Daily-anchored zero-cost (memo Option A): free (the daily run already fetches
   and discards a 1m session frame per symbol), but yields ONE pre-market
   snapshot, not current-session hourly-fresh candles. Fails the accepted A1
   behavior. Rejected by Helm ruling.
2. Six-symbol hourly (memo Option B, ~54 ops/day): this is the A2 expansion.
   Out of scope; cost unjustified before A1 usefulness is shown.
3. Cross-run intraday cache: adds a persisted-across-runs carrier with its own
   freshness key - larger MATERIAL surface and a charge novel-stop
   (cross-run persistence). Run-local co-production suffices; rejected.

## 13. Unresolved decisions for Gate A

11.1 Primary-symbol parity: shared tier-ordering helper so the runtime-selected
     primary matches the rendered primary card (recommend yes; accept daily
     fallback on residual divergence).
11.2 Freshness threshold INTRADAY_MAX_AGE (recommend 90 min).
11.3 Opportunistic-reuse policy: reuse only a session-shaped paid frame vs never
     reuse (recommend reuse-only-if-session-shaped).
11.4 Bar granularity: raw 1m (up to ~390 bars/symbol) vs 5m-resampled (memo's
     ~20-25 KB projection). Recommend deciding at Gate A; 1m for two symbols is
     bounded, 5m matches the memo size projection and improves legibility.
11.5 Whether `setup_chart.py` renders intraday byte-for-byte via its existing
     interval-agnostic path or needs a small caption edit.

## 14. Required docs/DECISIONS.md entry (to land at Stage-0)

```
## 2026-08-30 - Intraday session-candle card: A1 selected over daily-anchored
(ruled: Dustin)

Helm selects A1: current-session, hourly-fresh 1-minute session candles for the
primary setup symbol + SPY, co-produced in the existing hourly run, run-local
(no cross-run persistence), display-only. This SUPERSEDES the recommendation in
audits/intraday-feasibility-2026-08/INTRADAY_FEASIBILITY_MEMO_2026-08-28.md
(branch claude/intraday-feasibility-memo-2026-08, d1e90a4), which recommended the
daily-anchored path; the memo is retained as evidence, not authority. Accepted
acquisition cost: at most 2 logical 1m fetches per hourly slot (~18/day) via the
existing fetch_intraday_session_bars, with opportunistic reuse only when a
qualifying session frame is already paid. MATERIAL under GOV-2 s1: full packet ->
review -> Stage-0 -> Gate A. No implementation authorized by this entry.
```

## 15. STOP / next order

DESIGN boundary reached. Next, in order: independent/Codex review of this packet
at its committed head -> Helm ruling -> Stage-0 scaffold (allocate the PRD number
via tooling; land the DECISIONS.md entry in Section 14) -> Gate A. No
implementation, no PR merge, no PRD number allocated by this packet.
