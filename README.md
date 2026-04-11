# Cuttingboard

A constraint-driven trading signal engine. Runs two scheduled jobs each trading day and always produces one of three outputs: **TRADE**, **NO TRADE**, or **HALT**.

---

## What It Does

**Premarket (06:00 PT / 13:00 UTC)**
Fetches all symbols, computes regime, structure, and options setups. Writes a daily report to `reports/YYYY-MM-DD.md` and sends an ntfy alert with the day's trades.

**Intraday (every 30 min, 14:00–21:00 UTC)**
Runs ingestion through regime only. Sends an ntfy alert if the regime shifts or VIX spikes.

---

## Pipeline

```
L1  Ingestion       → RawQuote per symbol (yfinance + Polygon fallback)
L2  Normalization   → NormalizedQuote (decimal pct_change, UTC timestamps)
L3  Validation      → 7 hard rules per symbol; HALT if any core symbol fails
L4  Derived         → EMA9/21/50, ATR14, momentum_5d, volume_ratio
L5  Regime          → 8-input vote model → RISK_ON / RISK_OFF / CHAOTIC / STAY_FLAT
L6  Structure       → TREND / PULLBACK / BREAKOUT / REVERSAL / CHOP + IV environment
L7  Qualification   → 9 gates (4 hard, 5 soft) → QUALIFIED / WATCHLIST / REJECT
L8  Options         → Strategy + DTE from direction × IV matrix
L9  Output          → Terminal, reports/YYYY-MM-DD.md, ntfy alert
L10 Audit           → Append-only JSON record to logs/audit.jsonl
```

---

## Instrument Universe

| Category | Symbols |
|---|---|
| Core | SPY, QQQ, GLD, IAU, SLV, SIVR |
| High Liquidity Options | NVDA, TSLA, AAPL, MSFT, AMZN, META, GOOG, PLTR |
| High Beta / Volatility | MSTR, COIN, SMCI, MU |
| Macro / Context | XLE, USO, GDX, DXY, US10Y (^TNX fallback), VIX |

Focus: 5–8 tickers per session.

---

## Halt Conditions

If any core symbol (`^VIX`, `DX-Y.NYB`, `^TNX`, `SPY`, `QQQ`) fails validation, the system halts immediately — no regime, no trades. A HALT report and ntfy alert are sent and the process exits with code `1`.

---

## Setup

```bash
pip install -e .
cp .env.example .env   # fill in POLYGON_API_KEY, NTFY_TOPIC, NTFY_URL
```

Run manually:

```bash
python -m cuttingboard.run_premarket
python -m cuttingboard.run_intraday
```

---

## Tests

```bash
pytest tests/
```

297 tests across all layers.

---

## Docs

- `docs/architecture.md` — full layer diagram and data contracts
- `docs/regime_model.md` — vote thresholds and posture rules
- `docs/trade_qualification.md` — all 9 qualification gates
- `docs/options_framework.md` — direction × IV strategy matrix
- `docs/runbook.md` — operational procedures
- `docs/data_sources.md` — data source details and fallback logic
