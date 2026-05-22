# 02 — Sidecar Discipline

Read-only sidecar check against VISION.md operating principle:
*Read-only sidecars by default. New observational features extend through
sidecars rather than mutating core contracts.*

Per-sidecar finding shape: inputs / outputs / discipline verdict.

---

## `market_map.py`

- Inputs: `DerivedMetrics`, `NormalizedQuote`, `RegimeState`,
  `StructureResult`, `WatchSummary`, `IntradayMetrics`.
- Outputs: dict tree under
  `logs/market_map.json` (built and consumed in the same run; see
  PRD-135 milestone). Schema `market_map.v1`
  ([market_map.py:19](cuttingboard/market_map.py#L19)).
- Downstream consumers in-runtime: `build_visibility_map`
  ([trade_visibility.py](cuttingboard/trade_visibility.py)) and
  `apply_overnight_policy`
  ([overnight_policy.py](cuttingboard/overnight_policy.py)).
- Verdict: **READ-ONLY producer** of the dict; consumers read grade/symbols
  fields but do not mutate them in place. Decision-affecting (visibility
  classification, overnight guidance) but the consumers are explicit and
  documented. Aligned with sidecar doctrine — the sidecar produces a
  contract-shaped value, not a side effect on RuntimeState.

---

## `market_map_lifecycle.py`

This was the open verification point from the 2026-05-22 cleanup.

- Inputs: `current_map: dict`, `previous_map: dict | None`.
- Output: a new dict (deep-copied — never mutates inputs at
  [market_map_lifecycle.py:47](cuttingboard/market_map_lifecycle.py#L47))
  with two additions:
  - per-symbol `lifecycle` block (previous_grade, grade_transition,
    setup_state_transition, is_new, is_removed)
    ([market_map_lifecycle.py:71-80](cuttingboard/market_map_lifecycle.py#L71-L80)).
  - top-level `removed_symbols` list
    ([market_map_lifecycle.py:87-98](cuttingboard/market_map_lifecycle.py#L87-L98)).
- Quiet behavior: backfills `current_price` from `previous_map` when the
  current symbol has `current_price is None`
  ([market_map_lifecycle.py:82-85](cuttingboard/market_map_lifecycle.py#L82-L85)).
  This carries a *prior-run* price into the current map. It is **not**
  derived from current data.
- Downstream consumers of the `lifecycle` block:
  - `delivery/dashboard_renderer.py` (renders lifecycle CSS class via
    `lifecycle-new` / `lifecycle-upgraded`).
  - `notifications/__init__.py` lifecycle alert lines.
  - **No decision module reads `lifecycle`.** `overnight_policy` and
    `trade_visibility` read grade / symbols / setup_state but not the
    transition annotations.

**Finding: ANNOTATE-ONLY.** The lifecycle module annotates a copy of the
current market_map for renderer and notifier consumption; it does not
mutate engine state or feed decision modules with transition data. The
`current_price` backfill is the one borderline behavior — it propagates
prior-run pricing into a current-run artifact. Downstream impact:
renderers display the carried value instead of `N/A`. This is a
description-side accommodation, not a forecast, but it is worth a one-line
note in `docs/sidecar_doctrine.md` so future readers know the carry is
intentional rather than accidental.

---

## `trend_structure.py`

- Inputs: `NormalizedQuote`, OHLCV DataFrames per symbol, generated_at.
- Outputs: `logs/trend_structure_snapshot.json` (schema v1,
  `source="trend_structure"`).
- Downstream consumers: dashboard renderer only (renderer-only sidecar per
  PRD-135 milestone). Not consumed by `qualification.py`,
  `execution_policy.py`, `trade_decision.py`.
- Discipline: explicit "no network, no file I/O, no datetime.now()" at top
  of file ([trend_structure.py:1-7](cuttingboard/trend_structure.py#L1-L7)).
  Pure deterministic builder.

**Finding: READ-ONLY ANNOTATIONAL.** Aligned.

---

## `watchlist_sidecar.py`

- Inputs: `NormalizedQuote` map, generated_at.
- Outputs: `logs/watchlist_snapshot.json` (schema v1).
- Downstream consumers: per PROJECT_STATE.md PRD-135 milestone, *no v1
  consumer*.
- Discipline: explicit "Observe-only producer", "WATCHLIST_SYMBOLS
  insertion order is serialization-only" ([watchlist_sidecar.py:1-10](cuttingboard/watchlist_sidecar.py#L1-L10)).

**Finding: READ-ONLY OBSERVATIONAL.** Aligned with sidecar doctrine; a
TENSION against "system serves the trader" rule remains until a consumer
exists. Flagged for Q-coverage in `01-module-alignment.md`.

---

## `macro_pressure.py`

- Inputs: `macro_drivers` dict, optional `market_map`.
- Outputs: dict with per-component classification +
  `overall_pressure`.
- Downstream consumers: `execution_policy.py`
  (`POLICY_MACRO_PRESSURE_CONFLICT`) and dashboard renderer.
- Discipline: pure classification with explicit thresholds
  ([macro_pressure.py:67-89](cuttingboard/macro_pressure.py#L67-L89)).
  Note at module top blocks adding `oil` to pressure synthesis — guard
  against decision-coupling drift
  ([macro_pressure.py:14-17](cuttingboard/macro_pressure.py#L14-L17)).

**Finding: READ-ONLY PRODUCER.** Decision-affecting via execution_policy
but the gate is explicit and traceable through `decision_trace`. Aligned.

---

## Cross-cutting observations

- All five sidecars are pure builders over already-computed runtime
  objects, with no fetch, file write, or wall-clock side effects in the
  builder layer itself (writes happen in `runtime.py` helpers).
- The `current_price` backfill in `market_map_lifecycle.py` is the only
  cross-run carry; it is bounded (lifecycle-only) and renderer-facing.
- `manual_journal.py` and `review_scorecard.py` are not "sidecars" in the
  doctrine sense (they describe trader process, not market context) but
  they enforce the same discipline via "must NOT be imported by runtime"
  guards — strong precedent worth preserving.

## Open question

Does `docs/sidecar_doctrine.md` document the `current_price` carry in
`market_map_lifecycle.py`? If not, add a one-line note so the behavior
isn't rediscovered as drift in a future audit.
