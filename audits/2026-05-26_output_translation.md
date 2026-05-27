# Output Translation Auditor Baseline

**Date:** 2026-05-26  
**PRD:** PRD-158  
**Source:** output-translation-auditor  
**Purpose:** Baseline dashboard output audit before Dashboard Output Surface Realignment Pass 1.

## Summary

| Verdict | Count |
|---|---:|
| KEEP | 7 |
| TRANSLATE | 13 |
| CUT | 21 |
| CONTRADICTS | 11 |

## Verdict Table

| field | current_value_example | decision_changed | action_implied | verdict | why |
|---|---|---|---|---|---|
| System State header | `SYSTEM STATE - NO TRADE` | skip | `do not trade now` | KEEP | Binary go/no-go gate is a concrete action. |
| Action line | `ACTION: MONITOR — SYSTEM ACTIVE` | none | none | CUT | `Monitor` with no trigger or level is not an executable verb. |
| Regime | `RISK_ON` | none | none | TRANSLATE | Internal classification; needs to be expressed as a permission, not a label. |
| Confidence | `0.375` | none | none | TRANSLATE | Bare scalar with no stated cause; needs a decision-language equivalent like `do not size up`. |
| Outcome | `NO_TRADE` | skip | `do not trade now` | CONTRADICTS | Conflicts with `RISK_ON` and `RISK_ON FRESH` badges shown on same screen without on-screen resolution. |
| Permission | `STAY_FLAT posture` | skip | `do not enter` | CONTRADICTS | Conflicts with Regime `RISK_ON` on the same screen; no on-screen reconciliation. |
| SOURCE: OK — system block | `SOURCE: OK` | none | none | CUT | Pipeline status leakage; trader takes no action from `OK`. |
| Run snapshot timestamp | `2026-05-22 12:23:51 PT` | wait | `trust freshness up to threshold` | TRANSLATE | Useful only if rendered as staleness with a freshness threshold. |
| Macro Tape header | `Macro Tape` | none | none | KEEP | Section anchor for spot prices used to read tape. |
| MACRO SOURCE: OK | `MACRO SOURCE: OK` | none | none | CUT | Pipeline status leakage. |
| Macro Bias | `MACRO BIAS: SHORT ↓` | skip | `avoid long-side entries today` | CONTRADICTS | Conflicts with Regime `RISK_ON` and bullish biases on SPY/QQQ/XLE cards on the same screen. |
| Spot metals row | `XAU ↓ 4510.4` | entry | `read directional tape before entry` | KEEP | Live spot with direction informs side selection in the next 5 minutes. |
| Macro drivers row | `VIX ↓ 16.6` | entry | `read risk-on/off tape` | KEEP | Live drivers are scanned before pulling the trigger. |
| Tradables row | `SPY 746.18` | entry | `read price before entry` | KEEP | Live price is the entry reference. |
| Macro Pressure / Volatility | `RISK_ON` | none | none | TRANSLATE | Per-driver label without trigger; translate to decision language or cut. |
| Macro Pressure / Dollar | `RISK_OFF` | none | none | TRANSLATE | Internal label; needs decision-language. |
| Macro Pressure / Rates | `NEUTRAL` | none | none | CUT | `NEUTRAL` by definition implies no action. |
| Macro Pressure / Bitcoin | `RISK_OFF` | none | none | TRANSLATE | Internal label; needs decision-language. |
| Macro Pressure / Overall | `MIXED` | none | none | CONTRADICTS | `MIXED` overall versus `MACRO BIAS SHORT` on same screen without reconciliation. |
| Trend Structure header badge | `FRESH` | none | none | CUT | Lifecycle/internal-state label; default CUT. |
| Trend Structure SOURCE: OK | `SOURCE: OK` | none | none | CUT | Pipeline status leakage. |
| TREND SYMBOLS count | `6/6` | none | none | CUT | Coverage count is internal; no trade action follows. |
| Symbol cell | `SPY` | entry | `read row for that symbol` | KEEP | Row anchor. |
| Status column | `PARTIAL` | none | none | CUT | Internal pipeline status; default CUT. |
| Price | `746.18` | entry | `compare to levels before entering` | KEEP | Concrete reference price. |
| vs VWAP | `DATA UNAVAILABLE` | none | none | CONTRADICTS | DATA UNAVAILABLE must be resolved into a trade consequence or suppressed. |
| vs SMA50 | `DATA UNAVAILABLE` | none | none | CONTRADICTS | DATA UNAVAILABLE must be resolved into a trade consequence or suppressed. |
| vs SMA200 | `DATA UNAVAILABLE` | none | none | CONTRADICTS | DATA UNAVAILABLE must be resolved into a trade consequence or suppressed. |
| Alignment | `DATA UNAVAILABLE` | none | none | CONTRADICTS | DATA UNAVAILABLE must be resolved into a trade consequence or suppressed. |
| Entry Context | `DATA UNAVAILABLE` | none | none | CONTRADICTS | DATA UNAVAILABLE must be resolved into a trade consequence or suppressed. |
| RVOL | `—` | none | none | CONTRADICTS | Missing-value placeholder must be resolved into a trade consequence or suppressed. |
| SMA Composite | `Structure unavailable` | none | none | CONTRADICTS | NOT COMPUTED equivalent; must be resolved into a trade consequence or suppressed. |
| Intraday Context | `Intraday context unavailable` | none | none | CONTRADICTS | NOT COMPUTED equivalent; must be resolved into a trade consequence or suppressed. |
| Market Map header | `Market Map / Developing Setups` | none | none | KEEP | Section anchor for setup list. |
| MARKET MAP SOURCE | `OK - setups 6` | none | none | CUT | Pipeline status plus count; no action. |
| Idle summary | `NO ACTIONABLE SETUPS / Market is not offering structure` | skip | `stand down` | KEEP | Concrete stand-down instruction. |
| Tier header | `D/F — FAILING (6)` | none | none | CUT | Internal grading bucket; default CUT. |
| Card SYMBOL | `GDX` | entry | `identify which name failed` | KEEP | Row/card anchor. |
| Card GRADE | `F` | none | none | TRANSLATE | Internal label; needs to be expressed as tradeable/developing/skip or cut. |
| Card BIAS | `BEARISH` | none | none | CONTRADICTS | GDX bearish versus bullish SPY/QQQ/XLE alongside macro short, with no on-screen resolution. |
| Card STRUCTURE | `UNKNOWN` | none | none | CONTRADICTS | NOT COMPUTED equivalent; must be resolved into a trade consequence or suppressed. |
| Card FAILURE REASON | `Market data unavailable for this run.` | skip | `do not trade this name today` | KEEP | Concrete skip with stated cause. |
| Card VALIDATION | `Market data unavailable for this run.` | none | none | CUT | Duplicate of failure reason; no incremental action. |
| Card level diagram | `SVG with lines` | entry | `read entry level vs current price` | TRANSLATE | Rendered despite unavailable data; translate to concrete entry/invalidation pair or hide when unavailable. |
| Changes Since Last Run — Regime | `RISK_OFF -> RISK_ON` | none | none | TRANSLATE | Delta of an internal label; translate to permission flip or cut. |
| Changes Since Last Run — Confidence | `0.25 -> 0.375` | none | none | CUT | Delta of a bare scalar; no action follows. |
| History — Time | `11:25` | none | none | CUT | Log breadcrumb; no decision in next 5 minutes. |
| History — Regime | `NEUTRAL` | none | none | CUT | Historical internal label. |
| History — Posture | `Stay Flat` | none | none | CUT | Historical state. |
| History — Conf | `0.125` | none | none | CUT | Historical scalar. |
| Artifact diagnostics — lineage_state | `COHERENT` | none | none | CUT | Pipeline status leakage. |
| Artifact diagnostics — payload path/ts | `logs/latest_hourly_payload.json @ ...` | none | none | CUT | Engineering breadcrumb. |
| Artifact diagnostics — generation_ids | `hourly-20260522T192351Z` | none | none | CUT | Engineering breadcrumb. |
| Artifact diagnostics — run/market_map/contract paths | `logs/latest_hourly_run.json @ ...` | none | none | CUT | Engineering breadcrumb. |
