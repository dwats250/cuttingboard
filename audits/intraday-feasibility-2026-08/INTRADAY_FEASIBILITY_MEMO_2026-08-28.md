# Intraday Market-Map chart feasibility — read/design recon memo
2026-08-28. READ/DESIGN ONLY per owner correction: no carrier, no fetch, no
implementation without a new MATERIAL owner ruling. All anchors verified at
main fdfb43f; still current at main 91b5b13 (the two later merges, PR #285
dashboard renderer + PR #286 evidence/docs, touch no ingestion or runtime
seam cited here).

## Question
Can Cuttingboard add useful intraday candles to the existing static
setup-chart architecture using data it ALREADY acquires, without a new
provider and without a material provider-cost increase?

## Ground truth (verified)
1. ONE function owns all intraday acquisition: `fetch_intraday_bars`
   (`cuttingboard/ingestion.py:195-278`) — yfinance `period=7d, interval=1m`,
   regular session only, post-filtered to the LATEST session; three shapes
   (ORB opening-range union, full-session SPY, contiguous last-120).
2. NO intraday cache or store exists anywhere. `data/cache/` holds 24 daily
   `*_ohlcv.parquet` files and nothing else; `_is_fresh_ohlcv_cache` is
   trading-day-keyed and would mis-judge 1m frames; the hourly workflow
   RESTORES the daily cache but never saves any cache.
3. DAILY live run: ~23 intraday downloads (every validated symbol via
   `compute_all_intraday_metrics`, fetcher = `fetch_intraday_orb_bars`) + 1
   SPY full-session + per-SHORT-candidate + per-evaluation fetches. Frames
   are DISCARDED after scalar extraction (vwap/orb_high/orb_low/pdh/pdl +
   SPY observation); only scalars reach artifacts.
4. HOURLY run: ZERO intraday fetches. `intraday_metrics = {}` is hardcoded
   (`runtime/__init__.py:568`), so all six market-map symbols carry
   `missing_intraday_metrics` on every hourly board — hourly boards have no
   VWAP/ORB/PRIOR zones today.
5. The six market-map symbols get intraday bars once per DAILY live run,
   incidentally, as members of the all-symbols sweep.

## Answer
YES for a daily-anchored slice; NO free path for hourly-fresh intraday.

- **Zero-new-fetch reuse EXISTS at the daily seam**: the daily live run
  already downloads a full latest-session 1m frame per symbol and throws it
  away. Persisting a bounded projection (e.g. 5m-resampled bars for the six
  market-map symbols, ~78 bars/symbol/day resampled to ~26) into a sidecar
  carrier at the existing post-collection point would add ZERO provider
  operations — pure serialization of frames already in hand, the exact
  PRD-320 pattern one interval down.
- **But the carrier is unambiguously MATERIAL** under GOV-2 §1: a new
  persisted schema surface with a reader, a seam/carrier shared across
  runtime + persistence + dashboard (two-plus layers). It requires the full
  packet -> Codex cycle -> owner ruling -> Stage-0 -> Gate A order. No
  shortcut is honest.
- **Freshness tradeoff (the owner decision):**
  - Option A — daily-anchored intraday (zero new fetches): the intraday
    chart view refreshes once per day at the ~06:00 PT live run; hourly
    boards re-serve the morning's session view. Cost delta: 0 logical
    provider ops. Staleness: intraday view is up to a session behind by
    afternoon.
  - Option B — hourly-fresh intraday: requires ~6 NEW 1m downloads per
    hourly run (six market-map symbols) = ~6 ops x 9 hourly slots = ~54
    logical provider ops/day ADDED (vs today's measured hourly ceiling of
    23 quotes + cache-served OHLCV). Also requires either accepting
    per-run downloads or building an intraday cache with its own freshness
    predicate and its own actions/cache key (the daily key is taken; the
    hourly job currently saves no cache at all).
  - Option C — session-state switching (daily chart off-hours, intraday
    during RTH): presentation-side choice layered on A or B; adds no cost
    itself but only makes sense with B's freshness.
- **Publication size**: six symbols x ~26 5m bars x 6 fields ≈ 20-25 KB
  pretty-printed — comparable to the existing 43 KB daily bars sidecar;
  no Pages concern.
- **Provider-risk note**: yfinance 1m is the least stable endpoint in use;
  any intraday carrier should carry per-symbol omission semantics identical
  to PRD-320 R3 (already proven).

## Recommendation
If intraday charts are wanted, commission a MATERIAL packet for Option A
(zero-new-fetch, daily-anchored, PRD-320-pattern carrier at the daily seam,
honest "session of <date>" caption; PRD-321's `interval` field is the
sanctioned extension point). Treat Option B's ~54 ops/day as a separate,
explicit owner decision — it is the only path to hourly-fresh intraday and
is NOT recommended as a default. The future seam is clean: nothing in
PRD-320/321/322 blocks or prejudices this; the chart module is
interval-agnostic already (`source.interval` is carried, the renderer
captions from `as_of`).

STOP — awaiting owner direction; nothing further is authorized.
