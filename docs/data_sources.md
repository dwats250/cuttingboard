# Cuttingboard — Data Sources

## Symbol Universe

20 symbols across four categories:

| Category | Symbols |
|----------|---------|
| Macro Drivers | `^VIX`, `DX-Y.NYB`, `^TNX`, `BTC-USD` |
| Index ETFs | `SPY`, `QQQ`, `IWM` |
| Commodities | `GLD`, `SLV`, `GDX`, `PAAS`, `USO`, `XLE` |
| High Beta | `NVDA`, `TSLA`, `AAPL`, `META`, `AMZN`, `COIN`, `MSTR` |

**HALT_SYMBOLS** — pipeline stops if any of these fail validation:
`^VIX`, `DX-Y.NYB`, `^TNX`, `SPY`, `QQQ`

These five are required for regime computation. Everything else can fail without halting.

---

## Source Priority

Each symbol has a configured source priority list. Sources are tried in order until one succeeds.

| Symbol | Source Priority | Notes |
|--------|----------------|-------|
| `^VIX` | yfinance only | Not available on Polygon free tier |
| `DX-Y.NYB` | yfinance only | DXY index; not on Polygon free tier |
| `^TNX` | yfinance only | 10-year yield; not on Polygon free tier |
| `BTC-USD` | yfinance only | Crypto ticker format; not on Polygon free tier |
| All others | yfinance → Polygon | Polygon used only when yfinance fails |

Configured in `config.py` under `SYMBOL_SOURCE_PRIORITY`. To add Polygon as primary for a symbol:
```python
SYMBOL_SOURCE_PRIORITY["SPY"] = ["polygon", "yfinance"]
```

---

## yfinance

**What it provides:** Real-time quote data via `Ticker.fast_info` (price, previous close, volume) and historical OHLCV via `yf.download()`.

**Fields used from `fast_info`:**
- `last_price` → `price`
- `previous_close` → used to compute `pct_change = (price - prev_close) / prev_close`
- `three_month_average_volume` → fallback volume if regular volume unavailable

**OHLCV fetch:** `yf.download(symbol, period="6mo", interval="1d", auto_adjust=True)`. The 6-month window (~126 bars) ensures EMA convergence well above the 21-bar minimum.

**Known failure modes:**

| Failure | Symptom | Fix |
|---------|---------|-----|
| Symbol renamed | `fast_info.last_price` returns NaN | Check Yahoo Finance for new ticker; update `ALL_SYMBOLS` in `config.py` |
| Rate limiting | Timeout or empty response | Automatic retry (3 attempts, 2s backoff) handles transient limits |
| Market closed | Stale `previous_close` data | Expected outside market hours; freshness gate rejects quotes > 300s old |
| `fast_info` attribute missing | AttributeError on new yfinance version | Pin yfinance version in `pyproject.toml` |
| VIX returning non-index value | Price outside `[9, 90]` bounds | Validation rejects; check for yfinance API changes |

**Thread model:** Each symbol fetch runs in a `ThreadPoolExecutor(max_workers=1)` wrapper with a 10-second timeout. This prevents any single slow fetch from blocking the pipeline. A fetch that times out is recorded as `fetch_succeeded=False` with reason "timeout after 10s".

---

## Polygon.io

**Tier:** Free. Uses the `/v2/aggs/ticker/{symbol}/prev` endpoint (previous day's OHLCV aggregate).

**What it provides:** Open, high, low, close, volume for the previous trading session. No intraday data on free tier.

**Fields used:**
- `results[0]['c']` → close price (used as `price`)
- `results[0]['o']`, `results[0]['c']` → pct_change = (close - open) / open
- `results[0]['v']` → volume

**Limitations:**
- Previous day's data only — cannot provide real-time quotes.
- No VIX, DXY, TNX, or BTC data on free tier.
- Rate limit: 5 requests/minute on free tier. With 16 eligible symbols and the retry loop, this can cause slowdowns. Consider upgrading or reducing symbol count if Polygon is frequently needed.

**Symbol format for Polygon:** Standard US equity tickers (no `^` prefix). The ingestion layer converts yfinance-format tickers to Polygon format internally: `^VIX` → skipped (yfinance only), `BTC-USD` → skipped.

**Authentication:** Requires `POLYGON_API_KEY` in `.env`. Without it, all Polygon fetches fail with a 403.

---

## Fetch Retry Logic

```
Attempt 1 → fail (timeout / network error / bad data)
  wait 2s
Attempt 2 → fail
  wait 2s  
Attempt 3 → fail
  return RawQuote(fetch_succeeded=False, failure_reason="...")
```

Configured in `config.py`:
```python
FETCH_RETRIES           = 3
FETCH_BACKOFF_SECONDS   = 2
FETCH_TIMEOUT_SECONDS   = 10
```

Each attempt uses a fresh `ThreadPoolExecutor(max_workers=1)` future with the timeout. A Python-level exception (AttributeError, KeyError, etc.) is caught and treated as a fetch failure — it never propagates to the validation layer.

---

## OHLCV Cache

OHLCV data for derived metrics is cached to avoid redundant network calls on repeated runs within the same day.

**Cache location:** `data/cache/{SANITIZED_SYMBOL}_ohlcv.parquet`

**Filename sanitization:**
- `^VIX` → `VIX_ohlcv.parquet` (caret stripped)
- `BTC-USD` → `BTC_USD_ohlcv.parquet` (hyphens → underscores)
- `DX-Y.NYB` → `DX_Y_NYB_ohlcv.parquet`
- Standard tickers → unchanged

**Staleness rule:** Cache is considered fresh for **12 hours** (`OHLCV_STALE_HOURS = 12`). After 12 hours, a new fetch is triggered and the cache is overwritten. This means:
- First premarket run of the day always fetches fresh OHLCV data.
- A second manual run within the same 12-hour window uses cached data.

**Cache is gitignored.** It is never committed. On a fresh CI checkout, the cache is empty and all OHLCV data is fetched from yfinance on first run.

**What happens if OHLCV fetch fails:** `fetch_ohlcv()` returns `None`. `compute_derived()` returns a `DerivedMetrics` sentinel with `sufficient_history=False` and all metric fields as `None`. The structure engine classifies this symbol as CHOP. It never blocks the pipeline.

---

## Normalization Details

**pct_change decimal detection:** If the absolute value of the raw pct_change exceeds 2.0, the value is assumed to be in percentage format and divided by 100.

```
raw = 5.2   → pct_change_decimal = 0.052  (divided by 100)
raw = 0.052 → pct_change_decimal = 0.052  (passed through)
raw = -0.03 → pct_change_decimal = -0.03  (passed through)
```

This handles inconsistency between data sources. yfinance sometimes returns decimal, sometimes percentage depending on the field path used.

**UTC enforcement:** Any `datetime` without tzinfo is assumed to be UTC and has `timezone.utc` added. All downstream timestamps are UTC-aware. If you ever see a naive datetime anywhere in the system, it is a bug.

**Units:**
- `^VIX`, `DX-Y.NYB` → `"index_level"`
- `^TNX` → `"yield_pct"`
- All others → `"usd_price"`

Units are informational. No downstream layer makes decisions based on units — they exist for human readability in reports and audit records.

---

## Staleness and Freshness Rules

| Rule | Threshold | Layer | Consequence |
|------|-----------|-------|-------------|
| Quote freshness | ≤ 300s (5 min) | L3 Validation | Symbol marked INVALID |
| Timestamp sanity | ≤ 900s (15 min) | L3 Validation | Symbol marked INVALID |
| OHLCV cache TTL | ≤ 12 hours | L4 Derived | Cache refreshed from yfinance |
| OHLCV minimum bars | ≥ 21 bars | L4 Derived | `sufficient_history=False` → CHOP |

The 300-second freshness threshold means the system will reject stale quotes even if they arrived successfully. In practice, all yfinance quotes are fresh (< 60s) during market hours. Outside market hours, `previous_close` data may be hours old and will fail the freshness check — this is intentional. The system is designed for market-hours operation.

---

## Adding a New Symbol

1. Add the ticker to the appropriate category list in `config.py`:
   ```python
   HIGH_BETA = [..., "PLTR"]
   ```
   `ALL_SYMBOLS` is computed from the category lists automatically.

2. Add a price bounds entry:
   ```python
   PRICE_BOUNDS["PLTR"] = (5, 200)
   ```
   The system will fail validation for this symbol until bounds are set. Wide bounds are fine — they are just sanity checks.

3. If the symbol is yfinance-only (index, crypto, FX), add to source priority:
   ```python
   SYMBOL_SOURCE_PRIORITY["PLTR"] = ["yfinance"]  # optional — default is yfinance → polygon
   ```

4. Run the spot-check to confirm the symbol validates:
   ```bash
   python3 -c "
   from cuttingboard.ingestion import fetch_quote
   from cuttingboard.normalization import normalize_all
   r = fetch_quote('PLTR')
   print(r.fetch_succeeded, r.price, r.pct_change_raw)
   "
   ```

---

## Removing a Symbol

Remove it from the category list in `config.py`. The system will no longer fetch or validate it. No other changes required — all downstream layers key off `valid_quotes` which is built from `ALL_SYMBOLS`.

If the symbol is a HALT_SYMBOL, remove it from `HALT_SYMBOLS` first or the pipeline will halt if it can't be fetched.
