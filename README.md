# Cuttingboard

A constraint-driven trading signal engine. It now exposes a single public CLI, writes one trusted markdown report plus one JSON run summary per run, and verifies those artifacts without changing engine logic.

---

## What It Does

**`python -m cuttingboard`**
Dispatches `live`, `fixture`, `sunday`, or `verify` from one public entrypoint.

**LIVE (default)**
Fetches live data and runs the full pipeline. Writes `reports/YYYY-MM-DD.md`, `logs/run_*.json`, and `logs/latest_run.json`.

**SUNDAY**
Runs the live spine through regime only. Produces regime context with no candidates.

**FIXTURE**
Loads a normalized snapshot from `tests/fixtures/` and starts at validation with deterministic output.

**VERIFY**
Reads `logs/latest_run.json` or `--file PATH` and returns `PASS` or `FAIL` without rerunning the engine.

---

## Pipeline

```
L1  Ingestion       → RawQuote per symbol (yfinance + Polygon fallback)
L2  Normalization   → NormalizedQuote (decimal pct_change, UTC timestamps)
L3  Validation      → 7 hard rules per symbol; HALT if any core symbol fails
L4  Derived         → EMA9/21/50, ATR14, momentum_5d, volume_ratio
L5  Regime          → 8-input vote model → RISK_ON / RISK_OFF / NEUTRAL / CHAOTIC
L6  Structure       → TREND / PULLBACK / BREAKOUT / REVERSAL / CHOP + IV environment
L7  Qualification   → 11 gates (4 hard, 7 soft) → QUALIFIED / WATCHLIST / REJECT
L8  Options         → Strategy + DTE from direction × IV matrix
L9  Output          → Terminal, reports/YYYY-MM-DD.md, ntfy alert
L10 Audit           → Append-only JSON record to logs/audit.jsonl
Ops Summary         → logs/run_YYYY-MM-DD_HHMMSS.json + logs/latest_run.json
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
python -m cuttingboard
python -m cuttingboard --mode fixture --fixture-file tests/fixtures/2026-04-12.json
python -m cuttingboard --mode verify
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
- `docs/trade_qualification.md` — all 11 qualification gates
- `docs/options_framework.md` — direction × IV strategy matrix
- `docs/runbook.md` — operational procedures
- `docs/data_sources.md` — data source details and fallback logic
