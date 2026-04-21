# CLAUDE.md — cuttingboard

## purpose

Build and refine a constraint-driven options trading decision engine.

- Improve trade decisions
- Enforce clarity and discipline
- Prevent system drift

**System type:** Decision engine with a fixed pipeline. Not a research library. Not a feature-rich platform.

**Output contract:** Every run produces exactly one of: `TRADES | NO TRADE | HALT`

---

## system state (as of 2026-04-20)

All pipeline layers are built and wired. 360 tests passing.

**Known broken:** `test_phase5.py` — 13 audit record tests failing (interface mismatch). `test_gap_down_permission_integration.py`, `test_intraday_state.py`, `test_operationalization.py` — collection errors (import issues).

### pipeline layers

| Layer | Module | Role |
|---|---|---|
| 1 | `config.py` | All constants and secrets (from .env). Never hardcode. |
| 2 | `ingestion.py` | RawQuote fetch. yfinance primary, Polygon fallback. OHLCV parquet cache. |
| 3 | `normalization.py` | NormalizedQuote. pct_change → decimal, UTC enforcement, units. |
| 4 | `validation.py` | Hard validation gate. HALT_SYMBOL failure stops the pipeline. |
| 5 | `derived.py` | EMA9/21/50, ATR14 (Wilder RMA), momentum_5d, volume_ratio. Validated symbols only. |
| 6 | `structure.py` | Per-ticker classification: TREND / PULLBACK / BREAKOUT / REVERSAL / CHOP. |
| 7 | `regime.py` | 8-vote macro regime model → RISK_ON / RISK_OFF / NEUTRAL / CHAOTIC + posture. |
| 8 | `qualification.py` | 9-gate trade qualification. Hard gates 1–4, soft gates 5–9. |
| 9 | `options.py` | Options expression engine. Spread selection, DTE, strike distance. |
| 10 | `chain_validation.py` | Live chain liquidity gate. OI, spread %, bid/ask sanity. |
| 11 | `output.py` | Terminal + markdown report + ntfy alert. Writes on every run including NO TRADE. |
| — | `audit.py` | Append-only JSONL audit log per run. |
| — | `run_premarket.py` | Full pipeline runner. Scheduled 13:00 UTC Mon–Fri. |
| — | `run_intraday.py` | Regime watch. Layers 1–5 only. Every 30 min, 14:00–21:00 UTC. |
| — | `watch.py` | Intraday watchlist classification and session phase tracking. |
| — | `intraday_state_engine.py` | ORB classification engine. |
| — | `notifications/` | ntfy alert formatting. |

---

## instrument universe

**Macro drivers (HALT_SYMBOLS — pipeline stops if any fail):**
`^VIX`, `DX-Y.NYB`, `^TNX`, `SPY`, `QQQ`

**Required symbols:** `^VIX`, `DX-Y.NYB`, `^TNX`, `BTC-USD`, `SPY`, `QQQ`

**Indices:** `SPY`, `QQQ`, `IWM`

**Commodities:** `GLD`, `SLV`, `GDX`, `PAAS`, `USO`, `XLE`

**High beta:** `NVDA`, `TSLA`, `AAPL`, `META`, `AMZN`, `COIN`, `MSTR`

**Source rules:** `^VIX`, `DX-Y.NYB`, `^TNX` — yfinance only. All others: yfinance primary, Polygon fallback.

**Constraints:** Liquid options chains only. Prefer tight bid/ask. No arbitrary expansion. 5–8 tickers per session.

---

## regime engine

8-input vote model. Each input casts: `RISK_ON | RISK_OFF | NEUTRAL`

| Input | RISK_ON | RISK_OFF |
|---|---|---|
| SPY pct | > 0.3% | < -0.3% |
| QQQ pct | > 0.3% | < -0.3% |
| IWM pct | > 0.4% | < -0.4% |
| VIX level | < 18 | > 25 |
| VIX pct | < -3% | > +5% |
| DXY pct | < -0.2% | > +0.3% |
| TNX pct | < -0.5% | > +0.8% |
| BTC pct | > 1.5% | < -2.0% |

**CHAOTIC override:** VIX single-interval spike > 15% → CHAOTIC regardless of votes.

**Classification:** `net = risk_on − risk_off`. RISK_ON if net ≥ 4 and conf ≥ 0.60, or net ≥ 2. RISK_OFF if net ≤ -4 and conf ≥ 0.60, or net ≤ -2. Else NEUTRAL.

**Postures:** CHAOTIC or conf < 0.50 → STAY_FLAT. RISK_ON + conf ≥ 0.75 → AGGRESSIVE_LONG. RISK_ON + conf ≥ 0.55 → CONTROLLED_LONG. RISK_OFF + conf ≥ 0.55 → DEFENSIVE_SHORT. NEUTRAL + VIX 18–25 → NEUTRAL_PREMIUM. All other NEUTRAL → STAY_FLAT.

---

## qualification gates

Hard gates (1–4): immediate REJECT, no watchlist.
Soft gates (5–9+): one miss → WATCHLIST. Two+ misses → REJECT.

1. **(HARD) REGIME** — posture not STAY_FLAT
2. **(HARD) CONFIDENCE** — regime.confidence ≥ 0.50
3. **(HARD) DIRECTION** — candidate direction matches regime (RISK_ON=LONG, RISK_OFF=SHORT)
4. **(HARD) STRUCTURE** — not CHOP
5. **(SOFT) STOP_DEFINED** — stop_price > 0, distance > 0
6. **(SOFT) STOP_DISTANCE** — stop ≥ 1% of entry AND ≥ 0.5× ATR14
7. **(SOFT) RR_RATIO** — R:R ≥ 2.0 (NEUTRAL: ≥ 3.0)
8. **(SOFT) MAX_RISK** — 1 contract fits within TARGET_DOLLAR_RISK × regime_multiplier
9. **(SOFT) EARNINGS** — no earnings within 5 days (None = unknown → pass)
10. **(SOFT) EXTENSION** — |entry − ema21| / atr14 ≤ 1.5
11. **(SOFT) TIME** — no entries at or after 3:30 PM ET

STAY_FLAT short-circuits all per-symbol work — no gates run.

---

## key constants

```
MIN_RR_RATIO            = 2.0
NEUTRAL_RR_RATIO        = 3.0
MIN_REGIME_CONFIDENCE   = 0.50
TARGET_DOLLAR_RISK      = $150
MAX_DOLLAR_RISK         = $200
FRESHNESS_SECONDS       = 300   (5 min max quote age)
EXTENSION_ATR_MULTIPLIER= 1.5
VIX_CHAOTIC_SPIKE       = 0.15
EMA periods             = 9 / 21 / 50
ATR period              = 14 (Wilder RMA)
LATE_SESSION_CUTOFF     = 15:30 ET
REGIME_RISK_MULTIPLIER  = RISK_ON:1.0 / RISK_OFF:1.0 / NEUTRAL:0.6 / CHAOTIC:0.0
```

---

## core rules

1. **Execution only.** Every output must affect entry, exit, sizing, or avoidance. Otherwise reject.
2. **No bloat.** No speculative logic, no unused abstractions, no adjacent features.
3. **Constraints first.** Strict rules over flexible logic. Limit conditions and inputs.
4. **Single responsibility.** One module = one purpose. No overlapping logic.
5. **PRD required.** Define OBJECTIVE, SCOPE, REQUIREMENTS, DATA FLOW, FAIL CONDITIONS before coding. No exceptions.

---

## technical rules

1. Build in strict phase order. Do not begin Phase N+1 without passing tests and manual spot-check.
2. Never hardcode secrets. All secrets come from .env via config.py.
3. Never silently catch exceptions that hide data failures. Log explicitly.
4. No derived metric is computed on unvalidated input. Ever.
5. All dataclasses are frozen=True unless documented otherwise.
6. All timestamps are UTC datetime with tzinfo. Never naive datetimes.
7. The validation layer is the most critical layer. Do not weaken it.
8. If a symbol fails validation, exclude it and log why. Never substitute.
9. PRICE_BOUNDS in config.py must be updated periodically to reflect current market levels.
10. No HTML output, no web server, no backtest engine, no ML models.

---

## package

```python
# Package name: cuttingboard
from cuttingboard.xxx import yyy
```

---

## output style

- Concise, structured, direct.
- Do not repeat the prompt.
- Do not over-explain.
- No filler.

**Research format:**
```
INSIGHT: [one sentence, measurable conditions only]
TRADE IMPACT: [entry / exit / sizing / avoidance — one playbook only]
```

---

## failure conditions

Reject or flag output that:
- Adds complexity beyond the request
- Expands scope based on assumptions
- Lacks execution impact
- Introduces vague logic
- Weakens validation

---

## priority order

1. correctness
2. scope control
3. simplicity
4. execution relevance
5. maintainability
6. validation honesty
7. speed
8. convenience

---

## final rule

When uncertain: simplify → reduce → constrain.
