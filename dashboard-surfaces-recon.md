# Dashboard Surfaces Recon

Read-only recon. All real keys / representative rows are from the latest in-repo
artifacts: `logs/latest_payload.json`, `logs/latest_run.json`,
`logs/latest_hourly_payload.json`, `logs/market_map.json`,
`logs/trend_structure_snapshot.json`. Nothing fabricated.

---

## 1. SYSTEM STATE age labels (`<1 min old` / `today`)

**(a) module::function** — `cuttingboard/delivery/dashboard_renderer.py`, three formatters:

- `_run_snapshot_freshness_token(value, now)` (256–273) → RUN SNAPSHOT (`<1 min old`, `N minutes old`, `STALE (>5 min)`)
- `_surface_age_token(parsed, now, absent_label)` (276–294) → LIVE STATE (`<1 min old`, `N min/hr/day old`)
- `_scoreboard_age_token(regime_history, now, absent_label)` (297–321) → SCOREBOARD (`today`, `N days old`)

**(b) render source** — `render_dashboard_html()`, SYSTEM STATE block at lines 1903–1993
(RUN SNAPSHOT 1968–1972, LIVE STATE 1984–1989, SCOREBOARD 1990–1992).

**(c) timestamp fields read:**

- RUN SNAPSHOT: `payload["meta"]["timestamp"]` → `payload["timestamp"]` → `payload["generated_at"]`
- LIVE STATE: `run["run_at_utc"]` → `run["timestamp"]` → `run["generated_at"]`
- SCOREBOARD: `regime_history[i]["date"]`, parsed `%Y-%m-%d` (day-granular)

Real values:

```json
meta.timestamp = "2026-05-13T11:25:25Z"
run_at_utc     = "2026-05-13T11:25:25Z"
regime row     = {"date": "2026-06-16", "regime": "NEUTRAL", "posture": "STAY_FLAT"}
```

---

## 2. MACRO TAPE

**(a/b) render:**

- **(i) Tradables block** — layout `macro_tape_layout.py::TRADABLES_ROW` (41–51);
  values via `dashboard_renderer.py::_build_tape_value_slots()` (1090–1115);
  HTML `macro-tradables-grid` (2109–2119).
- **(ii) Driver vote rows** — layout `MACRO_ROW_1` / `MACRO_ROW_2` (22–39) +
  bias maps (`MACRO_BIAS_CONTRA_CYCLICAL` / `PRO_CYCLICAL` / `INTERPRETATION`, 78–94);
  vote tally in `render_dashboard()` (1750–1773); evidence rows `macro-evidence` (2071–2104).

**(c) data shape — direct answer:**

- **Tradables (SPY/QQQ/GLD/SLV/GDX/XLE): PRICE ONLY.** Read from
  `market_map["symbols"][sym]["current_price"]`; no prior-close, no %-change in the
  tape path. A `trade_framing.direction` exists on the symbol but is **not** consumed
  by the tape — discarded.

  ```json
  "QQQ": {
    "current_price": 740.76,
    "trade_framing": {"direction": "NEUTRAL"}
  }
  ```

- **Macro drivers: PRICE + %-CHANGE** (`level` + `change_pct`; `change_bps` only for
  rates). No stored prior-close — %-change is pre-derived. Direction is computed at
  render from the sign of `change_pct` (arrow), with contra/pro-cyclical inversion.

  ```json
  "volatility": {"symbol": "^VIX",  "level": 18.5,  "change_pct": -4.884}
  "rates":      {"symbol": "^TNX",  "level": 4.483, "change_pct": 0.448, "change_bps": 2.009}
  ```

---

## 3. TREND STRUCTURE table

**(a) section renderer** — `dashboard_renderer.py::_render_trend_structure_section()`
(2186–2266); SMA-composite cell via `_trend_structure_composite_display()` (109–119);
RVOL band `_intraday_rvol_band()` (145–156).

**(b) column sources** (per-row cells, 2223–2234):

- `vs SMA50  ← price_vs_sma_50`
- `RVOL      ← relative_volume`
- `SMA Composite ← (price_vs_sma_50, price_vs_sma_200)` token pair

**(c) pipeline source** — `trend_structure.py::_build_record()` (245–281);
`_sma()` returns `None` when `len(closes) < window`; `_classify_sma_unavailable()`
emits `INSUFFICIENT_HISTORY`.

**Verdict: DATA-PIPELINE GAP, not a renderer issue.** `OHLCV_FETCH_MONTHS = 6`
(config.py:97) yields ~126 trading bars; `sma_50` computes but `sma_200` is `null`,
so `price_vs_sma_200 = "INSUFFICIENT_HISTORY"` → "SMA history insufficient". RVOL is
present and valid (~1.6–1.8×). PRD-190 (window bump + shape-aware cache) has **zero
implementation** per PROJECT_STATE.md — confirms the gap.

Real SPY row (same pattern on all 6 symbols):

```json
{
  "symbol": "SPY",
  "sma_50": 721.07,
  "sma_200": null,
  "relative_volume": 1.67,
  "price_vs_sma_50": "ABOVE",
  "price_vs_sma_200": "INSUFFICIENT_HISTORY"
}
```

---

## 4. MARKET MAP level ladder

**(a/b) function** — `dashboard_renderer.py::_render_level_diagram()` (1399–1522),
called from `_render_candidate_card()` (1619); writes SVG directly.

**(c) positioning math:**

```python
_to_y(price) = round(SVG_H * (1.0 - (price - p_min) / p_span))   # SVG_H = 110
label_baseline = y + 4   # static, uniform for every label
```

`p_min` / `p_max` = min/max of all level prices ±12% padding (or
`contract_entry ±0.5%` when range < 0.01). **No collision-avoidance exists** — no
overlap/spacing/de-overlap logic anywhere; `y` is a pure price→pixel linear map, so
near-equal prices produce overlapping labels.

Worked example (SPY): EMA21 (742.08) → y≈39 and fib 0.5 (744.11) → y≈34 sit 5px apart
while text is ~9px tall → collision.

Real levels (SPY):

```json
"watch_zones": [
  {"type": "EMA9",  "level": 752.42},
  {"type": "EMA21", "level": 742.08},
  {"type": "EMA50", "level": 721.07}
],
"fib_levels": {
  "retracements": {"0.618": 740.27, "0.5": 744.11, "0.382": 747.95}
}
```

---

## Ownership map (surface → module → function)

| Surface | Module | Function |
|---|---|---|
| SYSTEM STATE age labels | `delivery/dashboard_renderer.py` | `_run_snapshot_freshness_token` / `_surface_age_token` / `_scoreboard_age_token` |
| MACRO TAPE | `delivery/dashboard_renderer.py` (+ `macro_tape_layout.py`) | `_build_tape_value_slots` / `render_dashboard` vote-tally (1750–1773, 2071–2104) |
| TREND STRUCTURE | `delivery/dashboard_renderer.py` (+ `trend_structure.py`) | `_render_trend_structure_section` / `_build_record` |
| MARKET MAP ladder | `delivery/dashboard_renderer.py` | `_render_level_diagram` |
