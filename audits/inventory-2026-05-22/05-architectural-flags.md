# 05 — Architectural Flags

Each item below is **flagged, not judged**. Citations point to `VISION.md` line ranges (`V:L`) for the principle potentially in tension. Conservative bias — over-flag and let Dustin decide.

## A. Backtesting code present

- `backtesting/run_orb_backtest.py` (2026-04-28)
- `backtesting/README.md`
- `data/backtests/` directory

**Tension with:** `V:11` "Not a backtesting framework".

Flag: a backtest script exists at top level with its own data directory. Possibly aspirational / experimental rather than active, but its presence contradicts the stated non-goal. **Decide: delete, document as inactive reference, or move out of repo.**

## B. ORB algorithm reference module

- `algos/orb_reference.py` (test-only inbound)
- `tests/test_orb_reference.py`
- `pinescripts/0dte Momentum Setup`

**Tension with:** `V:54` "Description, not prediction." `V:53` "Cuts before additions" + `V:55` "The system serves the trader, not the other way around."

Flag: appears to be a reference implementation of an entry-signal algorithm. If consumed by `intraday_state_engine.py` / `confirmation.py` via test parity, that's legitimate. If standalone, it's a research-library remnant. **Decide: confirm production wiring or remove.**

## C. Intraday state mini-pipeline

- `cuttingboard/intraday_state_engine.py`
- `cuttingboard/confirmation.py`
- `cuttingboard/watch.py`
- `cuttingboard/run_intraday.py` (CODEX.md: "unscheduled legacy, not invoked by any workflow")

**Tension with:** `V:54` (description vs prediction), `V:53` ("cuts before additions"), `V:5` (the four questions).

Flag: a parallel intraday classification engine exists alongside the main pipeline. `run_intraday.py` is the legacy entrypoint and is dead. `intraday_state_engine.py` + `confirmation.py` are imported by `runtime.py` (`compute_intraday_state`) — so the engine *is* live, but `run_intraday.py` is not. Worth a focused review to confirm the live path is descriptive (ORB classification, VWAP×RVOL context) and not crossing into prediction.

## D. `runtime.py` size + spans

- `cuttingboard/runtime.py` ~2100 LOC.

**Tension with:** `V:50` PRD-before-build / single-responsibility ethos.

Already documented as known technical debt in `PROJECT_STATE.md`. Listed here for completeness — every notification-path PRD edits this file. Not strictly an architecture violation under VISION.md, but the size compromises the audit's ability to evaluate sub-module isolation.

## E. Sidecars — mutation check

Per `V:50` "Read-only sidecars by default" and `docs/sidecar_doctrine.md`, sidecars should not mutate pipeline state.

Sidecars in the tree:

- `market_map.py` + `market_map_lifecycle.py` (PRD-053, 056)
- `trend_structure.py` (PRD-107)
- `watchlist_sidecar.py` (PRD-114)
- `macro_pressure.py` (PRD-060)
- `correlation.py` (PRD-023; "advisory `risk_modifier`, no qualification mutation" per registry)

Spot check via import edges:

- `market_map.py` is **read into `runtime.py`** and consumed by `build_visibility_map` / `apply_overnight_policy`. PROJECT_STATE.md milestone note: "market_map built pre-contract and consumed in-runtime by build_visibility_map/apply_overnight_policy". This is read-only consumption, but the market_map *is* an input to a decision-adjacent module (`overnight_policy`). The sidecar is observational; the consumer is overnight-policy. Flag for Dustin to confirm this is intentional and within the read-only-sidecar principle (the lifecycle hook in particular may be writing back into market_map state — verify).
- `market_map_lifecycle.py` — name implies state mutation. Worth a targeted review during cleanup: does it mutate `market_map` artifacts after first emission, or only annotate during initial build?
- `trend_structure.py`, `watchlist_sidecar.py` — PROJECT_STATE.md flags these as observe-only with no live consumer ("renderer-only" / "no v1 consumer"). Aligned with VISION.md.
- `correlation.py` — registry: "advisory risk_modifier, no qualification mutation". Aligned.

**Flag:** `market_map_lifecycle.py` — verify it's annotation-only, not lifecycle mutation.

## F. ML / forecasting / signal-generation imports

Grep for `sklearn`, `tensorflow`, `torch`, `xgboost`, `lightgbm`, `prophet`, `statsmodels`, `darts`, `keras`: **none found** in the package.

`numpy` and `pandas` are present and used for descriptive metrics (EMA, ATR, ratios). No predictive modeling detected.

`tools/macro_collector.py` (PRD-139) calls Anthropic Claude for **summarization** of macro RSS feeds into a structured bias label. This is description, not prediction (no forecast horizon, no PnL claim) — but it does introduce an LLM into a sidecar output (`logs/macro_regime_snapshot.json`). No runtime consumer per PROJECT_STATE.md.

**Tension with:** `V:11` "Not a machine learning system" (literal reading) vs `V:54` "Description, not prediction" (the LLM produces descriptive labels).

Flag: LLM-in-the-loop sidecar. Currently observe-only with no consumer; decide whether that satisfies the "not an ML system" non-goal or whether the LLM call itself crosses the line.

## G. Multi-agent orchestration

`alert_runner.py` and `runtime.py` are both entrypoints; `runtime.cli_main` covers all daily/intraday/notify modes while `alert_runner.main` handles the dedicated hourly Telegram path.

**Tension with:** `V:14` "Not a multi-agent orchestration platform".

Flag: not multi-agent in the AI sense, but two distinct orchestrators exist. Verify this is a deliberate split (hourly's dedup gate must run before the heavyweight pipeline, hence the separate entrypoint) and not accidental orchestration creep.

## H. External execution interfaces

Grep for broker/execution names — `interactive_brokers`, `alpaca`, `tradier`, `tda_api`, `ib_insync`, `etrade`, `schwab`, `td_ameritrade`, `moomoo`: **none found**.

Telegram out is *notification* (PRD-006 path), not execution. No execution interface detected.

**Aligned with:** `V:11` "Not an automated execution engine."

## I. Modules without justification under the four questions

The four questions (`V:5`): *what environment, what matters today, is this actually tradable, what invalidates*.

| Module | Earns keep under which question? | Notes |
|---|---|---|
| `manual_journal.py` (PRD-070) | *what invalidates* (post-hoc) | Worth confirming live use. |
| `review_scorecard.py` (PRD-071) | *what invalidates* (post-hoc) | Same. |
| `sector_router.py` | *is this actually tradable* | Single inbound; verify the call is live and meaningful. |
| `evaluation.py` (PRD-047) | *what invalidates* | Live. |
| `performance_engine.py` (PRD-075) | *what invalidates* | Live via runtime. |
| `correlation.py` (PRD-023) | *what matters today* | Advisory; aligned. |
| `notify_test.py` | none — ad-hoc smoke | Already flagged for deletion in `03-dead-code.md`. |
| `cuttingboard/run_intraday.py` | dead | Already flagged. |
| `algos/orb_reference.py` | unclear | Flagged in B above. |
| `backtesting/run_orb_backtest.py` | none under VISION | Flagged in A above. |

## J. Multiple HTML mockups in repo root

- `mockup.html`, `mockup_echofi.html`, `mockup_zeex.html` (all 2026-04-28, commit `1a07e2c`).

**Tension with:** `V:53` "Cuts before additions" + general repo hygiene. Not a VISION principle directly, but a presentation-pass concern (`V:65–66`).

Flag: theme exploration artifacts in the repo root. Already shipped (PRD-033 UI theme layer is COMPLETE). Likely safe to delete.

## K. "Temporary" patches in place >30 days

Grep didn't surface `TODO/FIXME/HACK` in any `cuttingboard/*.py` file. No legacy `# TEMP:` markers detected.

`fix_workflow.sh` (2026-04-21) is named like a temporary patch and has been in place for ~31 days. Verify whether it has any current invocation.

**Honest limit:** "temporary patches" framed as such in code comments would surface here; ones disguised as normal code would not.

## L. Two dashboard-related artifact pipelines

`ui/dashboard.html` and `ui/index.html` are paired outputs (`feedback_dashboard_publish.md` skill exists to keep them byte-identical). `cuttingboard/delivery/dashboard_renderer.py` is the producer; `cuttingboard/delivery/html_renderer.py` is a smaller auxiliary.

**Aligned with VISION** — these are observation surfaces, not decision logic — but `html_renderer.py` having only 2 inbound imports may be vestigial. Verify scope vs. `dashboard_renderer.py`.

## Summary

Most architectural drift is **historical-artifact drift** (mockup HTMLs, run_intraday, notify_test, backtesting harness, ORB reference) rather than active principle violations. The two items closest to live concern:

1. **`market_map_lifecycle.py`** — verify read-only sidecar discipline.
2. **`tools/macro_collector.py` LLM call** — confirm "description, not prediction" is satisfied even with an LLM in the path.
