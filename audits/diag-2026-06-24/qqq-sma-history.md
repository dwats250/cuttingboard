# Diagnosis — QQQ trend-structure SMA history recurringly null (recon F08)

**Charge:** PART A — DIAGNOSE (read-only). No fix, no PRD. Diagnosis feeds a
separate fix PRD AFTER human review.
**Date:** 2026-06-24. **Branch:** `claude/qqq-sma-history-diag-<id>` (no PR).
**Injection hygiene:** all CI logs / artifacts treated as data.

---

## TL;DR

The proximate cause is **NOT** a per-symbol fetch failure. QQQ's daily-OHLCV
**cache is truncated** — it holds **21 ≤ N < 50 daily closes** while peers hold
~250. The trend builder's `_sma(closes, 50)` / `_sma(closes, 200)` require
`len(closes) ≥ window`, so both return `None` → "DATA UNAVAILABLE". Meanwhile the
`derived` layer's `ewm`-based EMAs have **no length floor**, so they compute
normally and **mask** the truncation everywhere except the SMA-based trend row.

The truncated frame survives because **two gates lack a bar-count floor**:
1. `_fetch_ohlcv_from_yfinance` accepts any **non-empty** frame (`if df.empty:
   raise` — a short-but-nonempty yfinance response is accepted and cached).
2. `_is_fresh_ohlcv_cache` validates only the **last bar's date**, not the bar
   count — a short-but-recent cache is served as "fresh" and never re-fetched
   within a trading day.

"Why QQQ": a one-off short yfinance response for QQQ was cached, then persisted
into the Actions cache. "Why those slots / recurring": date-only freshness keeps
serving the short frame until a session rollover (or a cache miss) forces a full
re-fetch that overwrites it — which is exactly the observed heal pattern.

---

## The path, end to end (line evidence)

Trend snapshot is a **pure** builder fed OHLCV from the runtime:

- `runtime/__init__.py:547` → `_write_trend_structure_snapshot(..., history_by_symbol=_collect_trend_structure_history(ohlcv))`.
- `runtime/__init__.py:1892` `_collect_trend_structure_history`: for each
  `config.TREND_STRUCTURE_SYMBOLS` (`SPY, QQQ, GDX, GLD, SLV, XLE`, `config.py:192`),
  reuse `candidate_ohlcv.get(symbol)` else `fetch_ohlcv(symbol)`; **a symbol whose
  fetch returns None is omitted** → builder resolves it to the unavailable
  sentinel.
- `ingestion.fetch_ohlcv` (`ingestion.py:119`): **cache-first** — if
  `_is_fresh_ohlcv_cache(df)` returns the cached parquet; else live fetch.
- `trend_structure._sma` (`trend_structure.py:33-35`):
  `if closes is None or len(closes) < window: return None` ← **the SMA length floor**.
- `trend_structure._close_series` (`:23-29`): `df["Close"].dropna()`; `None` if
  empty/missing.

vs. the derived layer that does **not** floor on length:
- `derived.compute_derived` (`derived.py:62-69`): `df = fetch_ohlcv(symbol)`;
  warns + returns insufficient **only** when `len(df) < config.OHLCV_MIN_BARS`
  (`OHLCV_MIN_BARS = 21`, `config.py:96`).
- `derived.py:102`: `ema50 = float(close.ewm(span=config.EMA_TREND, adjust=False).mean().iloc[-1])`
  — `ewm` produces a value for any `len ≥ 1`.

The two count-blind gates:
- `_fetch_ohlcv_from_yfinance` (`ingestion.py:339`): `if df.empty: raise
  ValueError(...)` — **the only accept gate is non-empty**; no `len(df) ≥ K` check.
- `_is_fresh_ohlcv_cache` (`ingestion.py:158-167`): rejects only
  `None/empty/index.empty`; otherwise `return last_bar.date() >=
  most_recent_completed_session_date(...)` — **date-only**, no bar-count check.

---

## Live evidence — CI run 28109897263 (the 15:30 UTC slot, QQQ unavailable)

Job 83234145322, step "Run live pipeline". Quotes and **derived metrics for QQQ
both succeed**, but the published trend snapshot has QQQ `sma_50=null,
sma_200=null`:

```
yfinance QQQ: price=717.1900 pct=+0.0016 vol=14902483.0 attempt=1 duration=0.18s
derived — QQQ: EMA9=725.8191 EMA21=720.8370 EMA50=696.5778 ATR14=16.2068 mom5d=-0.0397 vol_ratio=1.08x
```

- No `QQQ: OHLCV all attempts failed` and no `QQQ: OHLCV ... attempt N/3 failed`
  line anywhere in the run → **fetch did not fail** (refutes the provider-gap /
  retry-exhaustion hypothesis as the proximate cause).
- No `derived` insufficient-history warning for QQQ → **QQQ ≥ OHLCV_MIN_BARS (21)**.
- Trend `sma_50` null → **QQQ < 50**. Bound: **21 ≤ QQQ closes < 50.**
- Peers resolve in the SAME run: published `trend_structure_snapshot.json` has
  `SPY sma_200=685.48`, `GLD sma_200=408.64`, etc. → peers hold **≥ 200** bars.
  This is a **QQQ-specific** truncation, not a global outage.
- The only OHLCV INFO fetch line that run was `^TNX: OHLCV cache stale — live
  refresh required` / `^TNX: OHLCV fetched 253 bars` → every other symbol
  (incl. QQQ) was served from the restored cache (`OHLCV from fresh cache` is
  `logger.debug`, suppressed at CI INFO). So QQQ's null came from the **cached**
  frame, not a live fetch.
- Cache steps: "Restore OHLCV cache" ran (step 6); "Run prefetch" / "Save OHLCV
  cache" were **skipped** (steps 13-15) → the run consumed the restored Actions
  cache as-is and did not rewrite it.

## Heal pattern (published trend snapshots, git-verified)

| publish commit | generated_at | QQQ alignment | QQQ sma_50 |
|---|---|---|---|
| 74ec0b4 | 2026-06-23 15:44 | DATA_UNAVAILABLE | null |
| 5107416 | 2026-06-23 16:00 | BULLISH | 694.99 |
| 40b0ad7 | 2026-06-23 17:10 | BULLISH | 694.99 |
| f41289e | 2026-06-24 14:38 | DATA_UNAVAILABLE | null |
| dbfd6b2 | 2026-06-24 15:30 | DATA_UNAVAILABLE | null |

Recurs at the early/pre-market slot, heals once a later run does a full
re-fetch that overwrites the short parquet (06-23 16:00). On 06-24 both same-day
slots stayed short — the restored cache was never refreshed between them (each is
date-fresh). Consistent with date-only freshness persisting a truncated frame.

---

## Ranked root-cause hypotheses

| rank | hypothesis | verdict | evidence |
|---|---|---|---|
| **1** | **QQQ cache truncated (21–49 bars) + count-blind accept/freshness** | **TOP — strongly evidenced** | QQQ derived EMA/ATR/vol_ratio computed (valid non-empty short series) but trend sma_50 AND sma_200 null; peers resolve sma_200 (≥200); no fetch-failure log; `_sma` floors on `len<window`, `ewm`/derived do not; `_fetch_ohlcv_from_yfinance` accept = empty-only; `_is_fresh_ohlcv_cache` = date-only; heals on rollover/refetch. |
| 2 | Symbol-specific transient provider gap + retry exhaustion (`fetch_ohlcv→None`) | **Refuted as proximate cause** (plausible *originating* event of the short cache) | No `QQQ: OHLCV all attempts failed` line; QQQ derived metrics present → df was not None this slot. |
| 3 | Slot-timing race vs provider publish (early slot = short series for all) | **Refuted** | Peers resolve sma_200 in the same early slot; QQQ quote+derived present. |
| 4 | Cache-key collision | **Refuted** | `_ohlcv_cache_path("QQQ") = "QQQ_ohlcv.parquet"` (`ingestion.py:378-381`); unique among the 6 trend symbols. |
| 5 | Partial-batch truncation in the fetch call | **Refuted** | `_fetch_ohlcv_from_yfinance` is single-symbol `yf.download(symbol, ...)` (`ingestion.py:330-338`); not a batched download. |

---

## The single confirm/refute check

**Count the rows of the restored `data/cache/QQQ_ohlcv.parquet` at a failing slot,
against `SPY_ohlcv.parquet`.**

- **Confirms** hypothesis 1 if QQQ is in **[21, 49]** rows and SPY is **~250**.
- **Refutes** if QQQ has **≥ 200** rows (then the null originates elsewhere —
  e.g. a `Close`-column NaN hole; re-examine `_close_series`).

Cheapest in-pipeline form (still read-only-ish — a one-line observability bump,
NOT a fix): promote the existing `ingestion.py:132` `logger.debug("%s: OHLCV from
fresh cache (%d bars)")` to INFO (or emit per-symbol cache bar counts) and
re-dispatch a pre-market slot; the failing run will print `QQQ: ... (~30 bars)`
vs `SPY: ... (~250 bars)`.

---

## Notes for the fix PRD (do NOT build here)

- The real fix target is a **bar-count floor** shared by both gates: reject/repair
  a cached or freshly-fetched daily frame with fewer usable closes than the
  largest consumer needs (sma_200 ⇒ ≥ 200), so a truncated frame is never served
  as "fresh" and a short fetch is never accepted as complete (PRD-198 #1
  fail-loud, #2 assert-the-resolved). PRD-190 raised `OHLCV_FETCH_MONTHS` 6→12
  for ≥200 bars *when the fetch is full*; it did not add a floor against a
  *short* frame, which is the gap here.
- Corroborating, separate: the same run logged `regime_history: SPY series
  resolved no next-session return for 1 date(s) (2026-06-19) ... partial/truncated
  SPY cache` — the recon F15 Juneteenth-mislabel, unrelated to QQQ but the same
  count-blind-cache family.
