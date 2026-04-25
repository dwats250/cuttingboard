# Cuttingboard

Cuttingboard is a deterministic market interpretation and trade qualification engine.

---

## Core Function

The system answers: Should a trade be taken right now?

---

## System Behavior

- Produces TRADE, NO TRADE, or HALT
- Explains reasoning for every outcome
- Defaults to no trade when uncertain

---

## Pipeline Architecture

```
ingestion → normalization → validation → derived → regime → structure → qualification → flow → options → chain_validation → output
```

| Stage | Module | Role |
|---|---|---|
| ingestion | `ingestion.py` | Fetch RawQuote per symbol. yfinance primary, Polygon fallback. |
| normalization | `normalization.py` | Convert pct_change to decimal, enforce UTC timestamps. |
| validation | `validation.py` | 7 hard rules per symbol. HALT_SYMBOL failure stops pipeline. |
| derived | `derived.py` | Compute EMA9/21/50, ATR14 (Wilder RMA), momentum_5d, volume_ratio. |
| regime | `regime.py` | 8-input vote model → RISK_ON / RISK_OFF / NEUTRAL / CHAOTIC + posture. |
| structure | `structure.py` | Classify each symbol: TREND / PULLBACK / BREAKOUT / REVERSAL / CHOP. |
| qualification | `qualification.py` | 11 gates (4 hard, 7 soft) → QUALIFIED / WATCHLIST / REJECT. |
| flow | `flow.py` | Options flow alignment gate. Downgrades PASS → WATCHLIST on direction conflict. |
| options | `options.py` | Select strategy, DTE, and strike distance from direction × IV matrix. |
| chain_validation | `chain_validation.py` | Live chain liquidity gate. Validates OI, spread %, bid/ask. |
| output | `output.py` | Render terminal output, markdown report, and ntfy alert. |

---

## Decision Model

- Regime drives context: RISK_ON, RISK_OFF, NEUTRAL, or CHAOTIC
- Structure classifies price behavior: TREND, PULLBACK, BREAKOUT, REVERSAL, or CHOP
- Qualification enforces hard and soft gates before any trade is considered
- Flow applies directional alignment against live options activity
- Options expresses only risk-defined trades within the $150 target risk budget

---

## Logging and Outputs

| File | Description |
|---|---|
| `logs/audit.jsonl` | Append-only record of every run, regardless of outcome |
| `logs/latest_run.json` | Most recent run summary — canonical machine-readable source of truth |
| `logs/latest_contract.json` | Most recent pipeline output contract |
| `logs/latest_payload.json` | Most recent delivery payload |
| `logs/run_YYYY-MM-DD_HHMMSS.json` | Timestamped per-run archive |

All system behavior is logged and reproducible.

---

## System Health

The engine doctor (`tools/engine_doctor.py`) is the canonical pipeline health authority. It verifies module importability, dependency graph integrity, runtime file presence, and test suite status — without touching the pipeline.

CI gating (PRD-020): every pull request runs the engine doctor in strict + baseline mode. Import failures, new circular dependencies, and unexpected test failures block merge.

Baseline enforcement: `tools/baseline.json` captures the known-good state. Any deviation from baseline fails CI with exit code 5.

---

## Safety Model

- Immutable dataclass boundaries: all pipeline contracts are `frozen=True`
- Strict validation gate: HALT_SYMBOL failure stops the pipeline before any analysis runs
- Default no-trade bias: STAY_FLAT posture short-circuits all qualification — zero candidates evaluated

---

## Current State

- Full pipeline implemented and wired: ingestion through output
- 802 tests passing (1 known pre-existing fixture failure)
- Engine doctor with CI integration and baseline enforcement (PRD-019, PRD-020)
- Append-only audit log on every run
- ntfy alert delivery on TRADE and HALT outcomes
- Intraday regime monitor with deduplication state

---

## Roadmap

- Chain validation against live Polygon options data
- Earnings calendar integration (Gate 9 currently fail-open)
- Sector-aware position sizing via `sector_router.py`
- Intraday alert threshold calibration
- Fixture coverage for flow gate and chain validation layers

---

## Authorship

Author: Dustin Watson
