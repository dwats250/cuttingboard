# Diag 2 — QQQ trend "closes-None" (DATA_UNAVAILABLE): the real cause of F08

**Charge:** PART B — NARROW DIAGNOSTIC (read-only). Resolve why the trend builder
saw closes-None for QQQ at the 15:30 slot while derived saw real data the same run.
No fix scoped/built. **Date:** 2026-06-24. **Branch:** `claude/qqq-closes-none-diag-<id>` (no PR).
**Injection hygiene:** CI logs / artifacts treated as data.

---

## TL;DR — the original diag's truncated-cache cause is REFUTED; real cause found

The premarket pipeline builds the trend snapshot from a **candidate-scoped** OHLCV
dict and **does not apply the PRD-174 `_collect_trend_structure_history` fallback**
that the hourly path uses. A `TREND_STRUCTURE_SYMBOL` that is not a current trade
candidate therefore has **no OHLCV history** → `_close_series(None)` →
`DATA_UNAVAILABLE` (closes-None). QQQ was excluded from candidates that run
(structure = CHOP), so QQQ alone went unavailable while the other five trend
symbols (all candidates) resolved.

This is a **render/path-coverage bug**, not a data/cache bug. PRD-209's bar-count
floor is **irrelevant to F08**.

---

## The divergence, in two lines of runtime/__init__.py

- **Hourly / lightweight path** (`_run_lightweight`, line 549):
  `history_by_symbol=_collect_trend_structure_history(ohlcv)` — the PRD-174 helper
  (line 1881-1898) iterates EVERY `config.TREND_STRUCTURE_SYMBOLS`, reusing
  `ohlcv.get(symbol)` else falling back to `fetch_ohlcv(symbol)`. Non-candidate
  trend symbols still get history. ✓
- **Premarket / full path** (`_run_pipeline` → `_refresh_trend_structure_sidecar`,
  line 1015): `history_by_symbol=ohlcv` — passes the **raw candidate dict
  directly**, NO `_collect_trend_structure_history`, NO `fetch_ohlcv` fallback. ✗

And `ohlcv` is candidate-scoped (line 741):
```
candidates = generate_candidates(...)          # line 737
ohlcv = {symbol: df                            # line 741
         for symbol in candidates
         if (df := fetch_ohlcv(symbol)) is not None}
```
So on the premarket path, the trend snapshot only ever has history for symbols that
are current trade candidates. PRD-174 fixed the hourly path; the premarket path was
never wired to the helper.

## Why QQQ specifically (CI run 28109897263, the 15:30 slot)

- The live log shows `structure — CHOP QQQ: price outside tradeable EMA zone`.
  CHOP structure is not a tradeable candidate → QQQ ∉ `candidates` → QQQ ∉ `ohlcv`.
- The other five trend symbols (SPY, GDX, GLD, SLV, XLE) are NOT logged CHOP →
  they were candidates → in `ohlcv` → trend resolved with full sma_50/sma_200.
- QQQ ∉ `ohlcv` → `_refresh_trend_structure_sidecar(history_by_symbol=ohlcv)`
  builds QQQ with no history → `_close_series(None)` → `DATA_UNAVAILABLE`.

This also resolves the derived-vs-trend puzzle: `derived` (`compute_all_derived`,
line 392) runs over ALL valid quotes via `fetch_ohlcv` (cache) → real QQQ metrics;
the premarket trend snapshot uses the candidate-only `ohlcv` (no fallback) → QQQ
absent. Different sources by construction; the old diag fused them.

## The heal pattern is path-based, not cache-rollover (git-verified)

| publish commit | type | QQQ | path |
|---|---|---|---|
| 74ec0b4 | **CB report** (premarket, `_run_pipeline`) | DATA_UNAVAILABLE | line 1015 raw ohlcv |
| 5107416 | **CB hourly** (`_run_lightweight`) | BULLISH (sma50=694.99) | line 549 fallback |
| 40b0ad7 | **CB hourly** | BULLISH | line 549 fallback |
| f41289e | **CB report** (premarket) | DATA_UNAVAILABLE | line 1015 raw ohlcv |
| dbfd6b2 | **CB report** (premarket) | DATA_UNAVAILABLE | line 1015 raw ohlcv |

Perfect correlation: every premarket "CB report" → QQQ unavailable; every "CB
hourly" → QQQ resolved. The prior diag mis-read this as a cache that goes stale at
premarket and heals by the hourly — it is simply the two code paths.

---

## Ranked causes for the closes-None state

| rank | cause | verdict | evidence |
|---|---|---|---|
| **1** | **Premarket trend snapshot built from candidate-only `ohlcv` (line 1015), bypassing the PRD-174 `_collect_trend_structure_history` fallback; a non-candidate trend symbol (QQQ=CHOP) has no history → DATA_UNAVAILABLE** | **CONFIRMED** | line 1015 vs 549 divergence; `ohlcv` candidate-scoped (741); `CHOP QQQ` log; premarket-vs-hourly publish correlation; derived (fetch_ohlcv) vs trend (candidate ohlcv) source split. |
| 2 | Truncated cache (21–49 bars) served as fresh (original diag) | **REFUTED** | would yield INSUFFICIENT_HISTORY (short closes), not DATA_UNAVAILABLE (closes-None); derived read a real QQQ frame from fresh cache; heal pattern is path-based, not rollover. |
| 3 | Transient per-symbol `fetch_ohlcv→None` (provider gap / retry exhaustion) | **REFUTED** | no `QQQ: OHLCV ... failed` / `cache stale` log; on the premarket trend path `fetch_ohlcv` is NEVER CALLED for a non-candidate symbol (no fallback to call it). |
| 4 | derived-vs-trend df divergence as an unexplained mystery | **RESOLVED (not a bug in itself)** | derived = `fetch_ohlcv` over all valid quotes; premarket trend = candidate-only `ohlcv`. Expected difference; the missing fallback is the defect. |
| 5 | `_collect_trend_structure_history`'s "fetch None → omit" silently swallowing QQQ | **REFUTED (helper not even invoked)** | the premarket path doesn't call the helper; on the hourly path the helper's `fetch_ohlcv` fallback SERVES QQQ (it resolves). The swallow path is not implicated. |

## Single confirm/refute

**Compare line 1015 (`history_by_symbol=ohlcv`) to line 549
(`_collect_trend_structure_history(ohlcv)`) and the publish-commit-type
correlation above.** Both already confirm cause #1. The original parquet-row-count
check is now **MOOT** — the closes-None is fully explained by candidate-scoping +
the missing fallback, independent of any cache bar count. (If desired, the
one-shot refutation of truncation: the SAME run's `derived — QQQ: EMA50=696.58`
proves QQQ's cached frame was usable; a truncated/empty cache could not produce
that.)

---

## Recommendation

- **F08's real fix is a small, single-concern PATH-DIVERGENCE fix**, NOT a
  count-floor: make the premarket path apply the PRD-174 fallback — i.e. line 1015
  should pass `_collect_trend_structure_history(ohlcv)` (mirroring line 549), or
  `_refresh_trend_structure_sidecar` should call the collector internally so BOTH
  paths share one trend-history source. This restores PRD-174's invariant ("trend
  renders for every TREND_STRUCTURE_SYMBOL, independent of the candidate set") on
  the premarket path. Scope/build only after human review (NOT done here).
- **PRD-209 (OHLCV bar-count floor) is NOT the F08 fix.** Decouple it (see the
  PRD-209 motivation amendment). The count-blind gates it targets are a *verified
  latent fail-silent hole* (PRD-198 #1) worth recording, but no real
  truncation-served-as-fresh event is confirmed — so PRD-209 is a **speculative
  guard to re-evaluate, not build** until/unless a real short-frame incident is
  observed.
- **PRD-208 (presentation) is unaffected** — it renders whatever token the builder
  emits; once the path fix lands, QQQ will simply render the arrow cell on
  premarket runs too.
