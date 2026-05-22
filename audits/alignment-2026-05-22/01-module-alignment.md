# 01 — Module Alignment

Per-module evaluation of `cuttingboard/` against VISION.md.

Excluded from alignment grid (utility/dispatch with no alignment question):
`__init__.py`, `__main__.py`, `time_utils.py`. `config.py` evaluated for
non-goal violations only (see also `04-non-goals-check.md`).

Status codes per principle column:
- **A** = ALIGNED, **N** = NEUTRAL/N-A, **T** = TENSION, **V** = VIOLATION,
  **?** = AMBIGUOUS.
- Principles (left to right): **D** Description-not-prediction,
  **S** Read-only sidecars (sidecar modules only — `N` if not a sidecar),
  **C** Cuts-before-additions (earns keep), **U** Serves user
  (decision-changing output), **M** Matches documentation.

VISION.md four questions cited as: **Q1** environment, **Q2** what matters,
**Q3** tradable, **Q4** invalidation.

---

## Top-level `cuttingboard/`

### `ingestion.py`
- Purpose: Layer 1 raw fetches (yfinance quotes + OHLCV). No math.
- Q-coverage: foundational for all four; no direct Q.
- D A · S N · C A · U A · M A
- Notes: post-cleanup Polygon paths removed; `RawQuote.source` correctly
  documents `"yfinance"` ([ingestion.py:36](cuttingboard/ingestion.py#L36)).
  `block_live_data()` guard correctly prevents Sunday-mode regressions.

### `normalization.py`
- Purpose: Layer 2 — units, tz-awareness, age. No business logic.
- Q-coverage: foundational.
- D A · S N · C A · U A · M A
- Notes: docstring explicitly forbids business logic here
  ([normalization.py:10](cuttingboard/normalization.py#L10)). Clean.

### `validation.py`
- Purpose: Layer 3 — HALT-symbol enforcement.
- Q-coverage: Q3 (gates whether system can produce a tradable view).
- D A · S N · C A · U A · M A
- Notes: docstring asserts criticality ("Do not weaken it"). Aligned.

### `derived.py`
- Purpose: Layer 4 — EMAs, ATR, volume_ratio, momentum_5d.
- Q-coverage: Q2 (structural context).
- D A · S N · C A · U A · M A
- Notes: explicit rejection of estimation/interpolation
  ([derived.py:5](cuttingboard/derived.py#L5)). Aligned.

### `regime.py`
- Purpose: Layer 5 — 8-input vote model → regime + posture.
- Q-coverage: Q1 (the core environment classifier).
- D A · S N · C A · U A · M A
- Notes: vote weights and thresholds are deterministic and inspectable
  ([regime.py:163-173](cuttingboard/regime.py#L163-L173)). No ML, no
  smoothing, no probabilistic outputs — confidence is computed as
  `abs(net_score)/total_votes`. EXPANSION precedence is documented and
  observable. Aligned.

### `structure.py`
- Purpose: Layer 6 — per-ticker structure classification.
- Q-coverage: Q2.
- D A · S N · C A · U A · M A
- Notes: classification thresholds are local constants
  ([structure.py:39-43](cuttingboard/structure.py#L39-L43)); CHOP is
  deterministic disqualification. No prediction. Aligned.

### `qualification.py`
- Purpose: Layer 7 — 9 gates (4 hard, 5 soft) per candidate.
- Q-coverage: Q3.
- D A · S N · C A · U A · M A
- Notes: gates are explicit, named, and short-circuit on STAY_FLAT /
  CHAOTIC ([qualification.py:53-55](cuttingboard/qualification.py#L53-L55)).
  Aligned.

### `flow.py`
- Purpose: PRD-013 flow-alignment soft gate.
- Q-coverage: Q3.
- D A · S N · C A · U A · M A
- Notes: downgrades PASS→WATCHLIST when speculative flow opposes.
  Descriptive trigger, deterministic logic. Aligned.

### `options.py`
- Purpose: Layer 8 — strategy mapping (structure×regime×IV → spread).
- Q-coverage: Q3.
- D A · S N · C A · U A · M A
- Notes: "estimated" usages all refer to debit cost approximation, not
  future-state forecasts ([options.py:13-26](cuttingboard/options.py#L13-L26)).
  Description-side of the line. Aligned.

### `chain_validation.py`
- Purpose: Layer 10 — late-stage option chain liquidity gate.
- Q-coverage: Q3 (final tradability check).
- D A · S N · C A · U A · M A
- Notes: deterministic classifications (TOP_TRADE_VALIDATED /
  WATCHLIST_OPTIONS_WEAK / DISQUALIFIED_OPTIONS_INVALID / NEEDS_MANUAL_CHECK).
  "Unpredictable fills" is a hazard description, not a forecast.

### `confirmation.py`
- Purpose: level-confirmation primitive for intraday engine.
- Q-coverage: Q3.
- D A · S N · C A · U A · M A
- Notes: small dataclass + state machine, no prediction. Aligned.

### `intraday_state_engine.py`
- Purpose: ORB classification, gap classification, downside-short
  permission state machine (PRD-151 retrospective).
- Q-coverage: Q3, Q4.
- D A · S N · C A · U A · M A
- Notes: pure classification of observed bars
  ([intraday_state_engine.py:182-260](cuttingboard/intraday_state_engine.py#L182-L260)).
  `downside_short_permission` is a permission gate over observed state,
  not a forecast of direction. Now formally documented via PRD-151;
  matches code.

### `correlation.py`
- Purpose: GLD–DXY correlation policy (PRD-023).
- Q-coverage: Q3 (risk modulation, not gate).
- D A · S N · C A · U A · M A
- Notes: explicitly advisory ("modulates risk sizing but does not alter
  qualification" — [correlation.py:6-7](cuttingboard/correlation.py#L6-L7)).

### `trade_policy.py`
- Purpose: lifts CorrelationResult into PolicyContext for sizing.
- Q-coverage: Q3.
- D A · S N · C A · U A · M A · Single function. Aligned.

### `sector_router.py`
- Purpose: compatibility shim — currently returns MIXED and pass-through.
- Q-coverage: none.
- D A · S N · C **T** · U **T** · M A
- Notes: every function is a stub
  ([sector_router.py:35-50](cuttingboard/sector_router.py#L35-L50));
  consumed only by runtime imports. **Kill candidate** unless a routing
  policy is actually planned. Flagged.

### `entry_quality.py`
- Purpose: PRD-069 chase / staleness / extension filter.
- Q-coverage: Q3, Q4.
- D A · S N · C A · U A · M A · Aligned.

### `invalidation.py`
- Purpose: PRD-068 deterministic invalidation status → may BLOCK_TRADE.
- Q-coverage: Q4 (this is the explicit Q4 module).
- D A · S N · C A · U A · M A · Aligned.

### `trade_thesis.py`
- Purpose: PRD-067 thesis-gate; INCOMPLETE/CONFLICTED → BLOCK_TRADE.
- Q-coverage: Q3, Q4.
- D A · S N · C A · U A · M A · Aligned.

### `trade_decision.py`
- Purpose: TradeDecision dataclass + ALLOW/BLOCK constants + decision_trace.
- Q-coverage: Q3.
- D A · S N · C A · U A · M A · Aligned.

### `trade_visibility.py`
- Purpose: PRD-064 — ACTIVE / NEAR_MISS / BLOCKED visibility classification.
- Q-coverage: Q3.
- D A · S N · C A · U A · M A
- Notes: explicitly read-only, no mutation.

### `trade_explanation.py`
- Purpose: PRD-066 — block_reasons, macro_alignment, required_changes per
  candidate. Templated, deterministic.
- Q-coverage: Q4 (explains why a trade was blocked).
- D A · S N · C A · U A · M A · Aligned.

### `execution_policy.py`
- Purpose: final pre-materialization gate (cooldowns, loss lockout, ORB
  range, macro-pressure conflict).
- Q-coverage: Q3.
- D A · S N · C A · U A · M A · Aligned.

### `overnight_policy.py`
- Purpose: PRD-058 EOD overnight guidance — ALLOW_HOLD/REDUCE/FORCE_EXIT.
- Q-coverage: Q4.
- D A · S N · C A · U A · M A · Aligned.

### `evaluation.py`
- Purpose: downstream-only post-trade evaluation (TARGET_HIT/STOP_HIT/NO_HIT)
  against forward 1-minute bars; appends to `logs/evaluation.jsonl`.
- Q-coverage: closes the explanation→behavior loop (VISION trap).
- D A · S N · C A · U **A (precursor)** · M A
- Notes: read-only over prior pipeline audit
  ([evaluation.py:1-7](cuttingboard/evaluation.py#L1-L7)). Same-session
  evaluation constraint preserved per PROJECT_STATE.md constraints.
  Strict superset of Phase 2 ambitions — a healthy precedent.

### `performance_engine.py`
- Purpose: aggregates `logs/evaluation.jsonl` → `logs/performance_summary.json`.
- Q-coverage: review.
- D A · S N · C A · U A · M A · Aligned.

### `manual_journal.py`
- Purpose: append-only manual trade journal (PRD-070).
- Q-coverage: review.
- D A · S N · C A · U A · M A
- Notes: explicit guard "must NOT be imported by any runtime, contract, or
  delivery module" ([manual_journal.py:6](cuttingboard/manual_journal.py#L6)).
  Strong sidecar discipline.

### `review_scorecard.py`
- Purpose: PRD-071 daily process-quality scorecard from manual_journal.
- Q-coverage: review (decision-changing post-hoc).
- D A · S N · C A · U A · M A
- Notes: explicit "must NOT be imported by runtime…" guard
  ([review_scorecard.py:6](cuttingboard/review_scorecard.py#L6)).

### `audit.py`
- Purpose: single audit JSONL writer per run.
- Q-coverage: provenance.
- D A · S N · C A · U A · M A · Aligned.

### `output.py`
- Purpose: Layer 9 — terminal + markdown + Telegram render and delivery.
- Q-coverage: delivery for Q1–Q4.
- D A · S N · C A · U A · M A · Aligned.

### `watch.py`
- Purpose: intraday WATCH layer; never weakens qualification.
- Q-coverage: Q2, Q3.
- D A · S N · C A · U A · M A · Aligned.

### `alert_runner.py`
- Purpose: hourly Telegram entrypoint with slot-based idempotency
  (PRD-141, PRD-149).
- Q-coverage: Q3 delivery.
- D A · S N · C A · U A · M A · Aligned.

### `universe.py`
- Purpose: tradability helper + execution-filter compatibility shims.
- Q-coverage: Q3.
- D A · S N · C **T** · U N · M A
- Notes: `filter_execution_dict` / `filter_execution_items` /
  `log_universe_configuration` are no-op pass-throughs
  ([universe.py:20-37](cuttingboard/universe.py#L20-L37)). Useful only as
  import compatibility — review for inlining.

### `market_map.py` (sidecar) — see `02-sidecar-discipline.md`
- Q-coverage: Q1, Q2.
- D A · **S A** · C A · U A · M A · Aligned.

### `market_map_lifecycle.py` (sidecar) — see `02-sidecar-discipline.md`
- Q-coverage: Q1, Q2.
- D A · **S A** · C A · U A · M A · ANNOTATE-ONLY.

### `trend_structure.py` (sidecar) — see `02-sidecar-discipline.md`
- Q-coverage: Q2.
- D A · **S A** · C A · U A · M A · Aligned.

### `watchlist_sidecar.py` (sidecar) — see `02-sidecar-discipline.md`
- Q-coverage: Q2.
- D A · **S A** · C A · U **T** · M A
- Notes: explicit observe-only, no v1 consumer per PROJECT_STATE.md
  PRD-135 milestone. Earns its keep only if a consumer materializes —
  watch for VISION's "system serves the trader" rule.

### `macro_pressure.py` (sidecar)
- Q-coverage: Q1.
- D A · **S A** · C A · U A · M A · Aligned (pure classifier).

### `runtime.py` — see `06-runtime-monolith.md`
- D A · S N · C **T** · U A · M A
- Notes: known debt; informational treatment per audit brief.

---

## `cuttingboard/delivery/`

### `payload.py`
- Purpose: contract → ReportPayload; deterministic, JSON-safe.
- Q-coverage: delivery.
- D A · S N · C A · U A · M A · Aligned.

### `dashboard_renderer.py`
- Purpose: PRD-055 renderer; reads payload + run + market_map.
- D A · S N · C A · U A · M A
- Notes: explicit "no computation, inference, or engine logic permitted"
  ([dashboard_renderer.py:8-9](cuttingboard/delivery/dashboard_renderer.py#L8-L9)).
  ~90 KB but boundary discipline is enforced via documented sidecar
  inputs ([dashboard_renderer.py:28-37](cuttingboard/delivery/dashboard_renderer.py#L28-L37)).

### `transport.py`
- Purpose: HTML/JSON/CLI write transport for payload.
- D A · S N · C A · U A · M A · Aligned.

### `html_renderer.py`
- Purpose: minimal `<pre>`-wrapped report HTML.
- D A · S N · C **?** · U **?** · M A
- Notes: small renderer; dashboard is the primary HTML. Verify a consumer
  exists — listed in scope only because it's a transport target.

### `fixtures.py`
- Purpose: hardcoded fixture symbols for demo/fixture mode (PRD-078).
- D A · S N · C A · U A · M A · Aligned.

### `macro_tape_layout.py`
- Purpose: PRD-138 — pure-data shared row/slot definitions for
  dashboard + notifications.
- D A · S N · C A · U A · M A · Aligned.

---

## `cuttingboard/notifications/`

### `__init__.py`
- Purpose: notify-mode public API (NOTIFY_PREMARKET, NOTIFY_HOURLY, etc.),
  lifecycle alert formatter.
- D A · S N · C A · U A · M A · Aligned.

### `formatter.py`
- Purpose: shared alert text formatting; was previously `format_ntfy_alert`,
  renamed `format_telegram_alert` during 2026-05-22 cleanup.
- D A · S N · C A · U A · M A · Aligned.

### `hourly_slot.py`
- Purpose: PRD-141/PRD-149 PT-anchored slot resolver + cross-run
  idempotency.
- D A · S N · C A · U A · M A · Aligned.

### `state.py`
- Purpose: PRD-018 — notification-state-key dedup + priority.
- D A · S N · C A · U A · M A · Aligned.

---

## `cuttingboard/reports/`

### `premarket.py`
- Purpose: premarket scenario builder from prior runs + key levels.
- Q-coverage: Q1, Q2.
- D **?** · S N · C A · U A · M A
- Notes: scenario expected_behavior lines read prescriptively
  ([reports/premarket.py:22-35](cuttingboard/reports/premarket.py#L22-L35))
  but are constructed from observed gap/regime — see
  `03-prediction-vs-description.md`. Edge case, not a violation.

### `postmarket.py`
- Purpose: postmarket reconciliation against the day's prior runs.
- D A · S N · C A · U A · M A · Aligned.

### `levels.py`
- Purpose: prior-day / current-price / gap_direction / range_mid derivation.
- D A · S N · C A · U A · M A · Aligned (descriptive derivation only).

---

## Counts

- Modules evaluated: 39 (excluding utility/`__init__`/`time_utils`).
- ALIGNED across all applicable principles: 34
- TENSION present (at least one column T or ?): 4 (`sector_router.py`,
  `universe.py` compatibility shims, `html_renderer.py`,
  `reports/premarket.py` scenario wording, `runtime.py` C-column).
- VIOLATION: 0.
- KILL CANDIDATES (recommend explicit decision): `sector_router.py`,
  `universe.py` compatibility shims if no longer imported.
