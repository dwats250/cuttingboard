# Cuttingboard — System Architecture

## What This System Does

Cuttingboard is a macro-driven trade signal engine. Every trading day it runs two scheduled jobs:

- **Premarket (13:00 UTC / 06:00 PT):** Fetches all 20 symbols, computes regime, structure, and options setups, writes a markdown report, and commits it to git. Sends an ntfy alert with the day's trades.
- **Intraday (every 30 min, 14:00–21:00 UTC):** Runs the data spine and regime engine only. Sends an ntfy alert if the regime shifts or VIX spikes — no report written.

The system always produces one of three terminal states: **TRADE**, **NO TRADE**, or **HALT**.

---

## Layer Diagram

```
GitHub Actions — cron: Mon–Fri
  ├── 13:00 UTC ──► run_premarket.py ──► Layers 1–9 + Audit
  └── */30 14-21 UTC ► run_intraday.py ──► Layers 1–5 only


L1  INGESTION          ingestion.py
    In:  20 symbol tickers
    Out: dict[str, RawQuote]
    ─────────────────────────────────────────────────────────
    yfinance primary, Polygon.io fallback (free tier).
    ThreadPoolExecutor(1) per fetch with 10s timeout.
    3 retries, 2s exponential backoff.
    OHLCV cached to data/cache/{SYMBOL}_ohlcv.parquet (12h TTL).
         │
         ▼
L2  NORMALIZATION       normalization.py
    In:  dict[str, RawQuote]
    Out: dict[str, NormalizedQuote]
    ─────────────────────────────────────────────────────────
    Converts pct_change to decimal (detects and corrects
    percentage-format values where |v| > 2.0).
    Adds UTC tzinfo to naive datetimes.
    Attaches units (usd_price / index_level / yield_pct).
         │
         ▼
L3  VALIDATION          validation.py
    In:  dict[str, NormalizedQuote]
    Out: ValidationSummary
    ─────────────────────────────────────────────────────────
    7 hard rules per symbol (type, NaN/Inf, positive price,
    freshness ≤300s, timestamp age ≤900s, price bounds,
    pct_change bounds ±25%).
    If any HALT_SYMBOL fails → system_halted=True → pipeline
    stops immediately. No derived metrics, no regime, no trades.
         │
         ├── system_halted=True ──► HALT report + audit + exit(1)
         │
         ▼
L4  DERIVED METRICS     derived.py
    In:  dict[str, NormalizedQuote]  (valid_quotes only)
    Out: dict[str, DerivedMetrics]
    ─────────────────────────────────────────────────────────
    Loads 6-month OHLCV from cache. Computes per-symbol:
      EMA9, EMA21, EMA50 (adjust=False)
      ATR14 (Wilder's RMA: ewm alpha=1/14)
      momentum_5d = (close[-1] - close[-6]) / close[-6]
      volume_ratio = today_vol / 20d_avg_vol
    Symbols with < 21 bars: sufficient_history=False,
    all metrics None. Never raises — returns sentinel.
         │
L5  REGIME ENGINE       regime.py
    In:  dict[str, NormalizedQuote]  (valid_quotes only)
    Out: RegimeState
    ─────────────────────────────────────────────────────────
    8-input vote model. Each input votes RISK_ON / RISK_OFF /
    NEUTRAL. confidence = abs(net_score) / total_votes.
    CHAOTIC override fires if VIX pct_change > 15%.
    See regime_model.md for full threshold table.
         │
         ├── posture == STAY_FLAT ──► NO TRADE (regime
         │                            short-circuits qualify_all)
         ▼
L6  STRUCTURE ENGINE    structure.py
    In:  dict[str, NormalizedQuote], dict[str, DerivedMetrics],
         vix_level (from RegimeState)
    Out: dict[str, StructureResult]
    ─────────────────────────────────────────────────────────
    Classifies each symbol: TREND | PULLBACK | BREAKOUT |
    REVERSAL | CHOP.
    Also classifies IV environment from VIX level:
    LOW_IV (<15) | NORMAL_IV (15-20) | ELEVATED_IV (20-28) |
    HIGH_IV (>28).
    CHOP = automatic disqualification at Layer 7.
         │
         ▼
L7  TRADE QUALIFICATION qualification.py
    In:  RegimeState, dict[str, StructureResult],
         dict[str, TradeCandidate], dict[str, DerivedMetrics]
    Out: QualificationSummary
    ─────────────────────────────────────────────────────────
    9 gates (4 hard stops, 5 soft stops).
    Hard stop failure → REJECT, no watchlist eligibility.
    Exactly 1 soft stop failure → WATCHLIST.
    2+ soft stop failures → REJECT.
    See trade_qualification.md for full gate table.
         │
         ▼
L8  OPTIONS EXPRESSION  options.py
    In:  list[QualificationResult], dict[str, StructureResult],
         dict[str, DerivedMetrics]
    Out: list[OptionSetup]
    ─────────────────────────────────────────────────────────
    Maps each qualified trade to a spread strategy using
    direction × IV environment matrix.
    Selects DTE from structure + momentum_5d.
    Strike labels are relative (ATM, 1_ITM) — never absolute.
    See options_framework.md for full matrix.
         │
         ▼
L9  OUTPUT ENGINE       output.py
    In:  All above results
    Out: Terminal print, reports/YYYY-MM-DD.md, ntfy alert
    ─────────────────────────────────────────────────────────
    Three write destinations per run. Report written even on
    NO TRADE days. ntfy skipped silently if not configured
    in .env.
         │
         ▼
L10 AUDIT               audit.py
    In:  All above results + ntfy_sent status
    Out: One JSON record appended to logs/audit.jsonl
    ─────────────────────────────────────────────────────────
    Append-only. sort_keys=True. Never overwritten.
    Every run writes exactly one record regardless of outcome.
```

---

## Data Contracts

Key frozen dataclasses and their layer of origin:

| Dataclass | Module | Key Fields |
|-----------|--------|------------|
| `RawQuote` | ingestion | symbol, price, pct_change_raw (decimal), source, fetch_succeeded |
| `NormalizedQuote` | normalization | symbol, price, pct_change_decimal, fetched_at_utc (UTC), units |
| `ValidationSummary` | validation | system_halted, halt_reason, valid_quotes, invalid_symbols |
| `DerivedMetrics` | derived | ema9/21/50, ema_aligned_bull/bear, atr14, momentum_5d, volume_ratio, sufficient_history |
| `RegimeState` | regime | regime, posture, confidence, net_score, vote_breakdown, vix_level |
| `StructureResult` | structure | symbol, structure, iv_environment, is_tradeable |
| `TradeCandidate` | qualification | symbol, direction, entry/stop/target price, spread_width, has_earnings_soon |
| `QualificationResult` | qualification | qualified, watchlist, gates_passed/failed, max_contracts, dollar_risk |
| `OptionSetup` | options | strategy, long/short_strike, strike_distance, dte, max_contracts, dollar_risk |

All dataclasses are `frozen=True`. All timestamps are UTC-aware `datetime` objects.

---

## Trust Boundary Rules

**Rule 1 — No derived metric computed on unvalidated input.**
`compute_all_derived()` receives only `valid_quotes` from `ValidationSummary`. Symbols that failed validation are never passed downstream.

**Rule 2 — No candidate generated for CHOP symbols.**
`generate_candidates()` skips any symbol where `StructureResult.structure == CHOP` before creating a `TradeCandidate`. The qualification layer would also reject CHOP (Gate 4), but the options engine never creates the candidate in the first place.

**Rule 3 — No trade when regime direction is ambiguous.**
`generate_candidates()` returns an empty dict when `direction_for_regime()` returns `None` (TRANSITION / CHAOTIC regime). No candidates → no qualification → NO TRADE.

**Rule 4 — pct_change is always decimal.**
`0.052` means 5.2%. The normalization layer detects and corrects percentage-format values (`|v| > 2.0` triggers `/100`). All downstream code assumes decimal.

**Rule 5 — Secrets only from `.env`.**
`config.py` loads via `python-dotenv`. No key, token, or credential appears in any source file.

---

## Halt Conditions

The system halts when any **HALT_SYMBOL** fails validation. HALT_SYMBOLS are:

```python
["^VIX", "DX-Y.NYB", "^TNX", "SPY", "QQQ"]
```

These five symbols are required for regime computation. If any of them fails validation (bad data, fetch failure, stale quote, price out of bounds), `ValidationSummary.system_halted = True` and the pipeline:

1. Renders a HALT report (terminal + markdown)
2. Sends an ntfy HALT alert
3. Writes an audit record with `outcome = "HALT"`
4. Exits with code `1`

**No trades are ever evaluated during a HALT.** The audit record preserves the halt reason for forensic review.

---

## File Map

```
cuttingboard/               Python package
  __init__.py               version string only
  config.py                 all constants + secrets (dotenv)
  ingestion.py              L1: RawQuote, fetch_all, fetch_ohlcv
  normalization.py          L2: NormalizedQuote, normalize_all
  validation.py             L3: ValidationSummary, validate_quotes
  derived.py                L4: DerivedMetrics, compute_all_derived
  regime.py                 L5: RegimeState, compute_regime
  structure.py              L6: StructureResult, classify_all_structure
  qualification.py          L7: TradeCandidate, QualificationSummary, qualify_all
  options.py                L8: OptionSetup, generate_candidates, build_option_setups
  output.py                 L9: run_pipeline, render_report, write_markdown
  audit.py                  L10: write_audit_record → logs/audit.jsonl
  run_premarket.py          Orchestrator: L1–10 + writes .cb_commit_msg
  run_intraday.py           Monitor: L1–5 + regime shift alerts

tests/
  test_phase1.py            30 tests: config, normalization, validation
  test_derived.py           19 tests: EMA, ATR, momentum, volume
  test_regime.py            35 tests: votes, posture, CHAOTIC override
  test_structure.py         45 tests: classification, CHOP, IV environment
  test_qualification.py     57 tests: all 9 gates, sizing, watchlist
  test_phase5.py            72 tests: options, audit, output rendering
  test_phase6.py            39 tests: intraday triggers, dedup, commit msg

data/
  cache/                    OHLCV parquet files (gitignored, 12h TTL)

logs/
  audit.jsonl               append-only run record (committed by CI)
  intraday_state.json       regime shift dedup state (committed by CI)

reports/
  YYYY-MM-DD.md             one markdown report per premarket run

.github/
  workflows/
    cuttingboard.yml        GHA: premarket + intraday schedules

docs/                       you are here
  architecture.md           this file
  runbook.md
  data_sources.md
  regime_model.md
  trade_qualification.md
  options_framework.md

.env                        POLYGON_API_KEY, NTFY_TOPIC, NTFY_URL
                            (gitignored — never committed)
pyproject.toml              package metadata + dependencies
```

---

## Execution Paths

**Normal premarket run (TRADE day):**
```
L1 → L2 → L3 → L4 + L5 → L6 → [L7 generate_candidates] → L7 qualify_all
→ L8 → L9 → L10
```

**Normal premarket run (NO TRADE day — STAY_FLAT):**
```
L1 → L2 → L3 → L4 + L5 [posture=STAY_FLAT] → L6 → qualify_all short-circuits
→ L9 → L10
```

**HALT (required symbol failed validation):**
```
L1 → L2 → L3 [system_halted=True] → L9 (HALT report) → L10 → exit(1)
```

**Intraday run:**
```
L1 → L2 → L3 → L4 + L5 → compare to last state → ntfy if trigger → update state
```
