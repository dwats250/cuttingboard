# 03 — Prediction vs Description

VISION.md operating principle: *Description, not prediction. Features that
explain or contextualize are welcome. Features that forecast are not.*

Scan target: forecasting language, predicted-value variables, probability
outputs, future-state estimates.

## Method

`grep` across `cuttingboard/` for `predict|forecast|estimat`, plus targeted
reads of the modules most at risk of drift: `regime.py`, `structure.py`,
`qualification.py`, `intraday_state_engine.py`, `macro_pressure.py`,
`reports/premarket.py`, `delivery/dashboard_renderer.py`, ML-adjacent code.

## Findings

### CLEAN: `regime.py`
- 8-input vote model, deterministic thresholds, no smoothing or
  probabilistic emission. `confidence = abs(net_score)/total_votes` —
  pure description of vote agreement, not a probability of future state.
- EXPANSION detection uses observed-state thresholds (breadth, leadership)
  not predicted breadth ([regime.py:84-122](cuttingboard/regime.py#L84-L122)).

### CLEAN: `structure.py`
- Per-ticker structure labels (TREND/PULLBACK/BREAKOUT/REVERSAL/CHOP) are
  classifications of current EMA/price/momentum/volume state, never of
  expected next-bar behavior
  ([structure.py:39-43](cuttingboard/structure.py#L39-L43)).

### CLEAN: `qualification.py`
- All 9 gates are deterministic threshold checks against current state.
  No expected-value computation, no probability of trade success emitted.

### CLEAN: `intraday_state_engine.py`
- `classify_gap`, `downside_short_permission` — all conditioned on
  observed open/prev_close, observed bars, observed acceptance closes
  ([intraday_state_engine.py:182-260](cuttingboard/intraday_state_engine.py#L182-L260)).
  Permission is a description of *what is currently allowed*, not a
  forecast of *what the market will do*.

### CLEAN: `macro_pressure.py`
- Per-driver classification (`RISK_ON`/`RISK_OFF`/`NEUTRAL`/`UNKNOWN`) is
  thresholded on observed `change_pct`/`change_bps`. Aggregation is
  rules-based, not probabilistic.

### CLEAN: `options.py` "estimat*" references
- Every match refers to cost estimation (estimated net debit per share
  for spread sizing) — backward-looking accounting, not forward-looking
  price prediction
  ([options.py:13-26](cuttingboard/options.py#L13-L26)).

### CLEAN: `chain_validation.py` "unpredictable"
- Single occurrence: "Near-zero bid: market-maker interest is nearly
  absent — fills unpredictable"
  ([chain_validation.py:583](cuttingboard/chain_validation.py#L583)).
  This is a *hazard description* used to justify a hard gate, not a
  forecast of fill price.

### CLEAN: `derived.py`
- Explicit "Never estimated or interpolated"
  ([derived.py:5](cuttingboard/derived.py#L5)). Missing history →
  `sufficient_history=False`, all fields None — refuses to fabricate.

### CLEAN: `dashboard_renderer.py`
- Documented "no computation, inference, or engine logic permitted"
  ([dashboard_renderer.py:8-9](cuttingboard/delivery/dashboard_renderer.py#L8-L9)).
  Renderer-only.

### EDGE CASE — NOT A VIOLATION: `reports/premarket.py`
- Scenario builders emit prescriptive-sounding strings such as
  *"Continuation long above prior_high; size normally"* and *"Wait for
  range_mid reclaim; high false-signal risk until then"*
  ([reports/premarket.py:22-40](cuttingboard/reports/premarket.py#L22-L40)).
- These read like forecasts but are **decision-tree branches** keyed on
  observed regime + gap_direction. The output is structurally:
  *"if today's regime is RISK_ON and gap is UP, the scenario worth
  watching is X"* — context, not prediction of where price will go.
- Recommendation: keep, but in a future doc pass consider tightening the
  wording (e.g. *"Continuation-long setup is operative above prior_high"*
  rather than *"Continuation long…size normally"*) so the description
  posture is clearer to readers. Not blocking.

### CLEAN: ML-adjacent code
- None present. No imports of `sklearn`, `xgboost`, `torch`, or other ML
  libraries. `numpy` import limited to `tests/test_derived.py` per
  2026-05-22 cleanup decision.

## Headline

System-wide: **CLEAN.** No prediction surface detected. The one wording
edge case in `reports/premarket.py` is documentation polish, not a
substantive violation.
