# 04 — Non-Goals Check

VISION.md non-goals, each with status + evidence.

## 1. Not an automated execution engine

**Status: CLEAN.**

Evidence:
- No broker integration in repo. Sole execution-policy module
  (`execution_policy.py`) gates allow/block status on `TradeDecision`
  records; it never places orders.
- `chain_validation.py` explicitly notes "Manual broker confirmation
  (Moomoo) occurs outside this system"
  ([chain_validation.py:13](cuttingboard/chain_validation.py#L13)).
- No `requests.post` to a broker endpoint, no `ccxt`, no `ib_insync`,
  no FIX adapter.

## 2. Not a backtesting framework

**Status: CLEAN.**

Evidence:
- `backtesting/` directory deleted in 2026-05-22 cleanup.
- `tests/test_phase6.py` (backtest harness) deleted.
- PROJECT_STATE.md constraints explicitly: "no backtesting".
- `evaluation.py` is **same-session forward-window evaluation** of the
  current run's decisions against forward 1-minute bars
  ([evaluation.py:1-7](cuttingboard/evaluation.py#L1-L7)) — this is
  downstream-only evaluation, not historical replay of decision logic.

## 3. Not a machine learning system

**Status: CLEAN.**

Evidence:
- No `sklearn`, `xgboost`, `torch`, `tensorflow`, `lightgbm`,
  `transformers`, or `prophet` imports anywhere in `cuttingboard/`.
- `numpy` retained only as a transitive test dep
  (`tests/test_derived.py`) per 2026-05-22 cleanup notes.
- All classifications (regime, structure, intraday state, macro
  pressure) are explicit deterministic thresholds reviewable inline.

## 4. Not a multi-agent orchestration platform

**Status: CLEAN.**

Evidence:
- Pipeline is a single Python process (`cuttingboard.runtime`) with one
  orchestration function per notify mode. No queue, no message bus, no
  agent registry.
- Anthropic API usage scope: per recent history, `tools/macro_collector.py`
  was the only LLM-touching code and was deleted in the 2026-05-22
  cleanup. Cross-verified: no `anthropic` import remains under
  `cuttingboard/` (only test/tool surface, since removed).
- "Claude / Codex" in CLAUDE.md / CODEX.md describes human-operated
  workflow assistance, not in-process agents.

## 5. Not a generalized financial operating system

**Status: CLEAN.**

Evidence:
- Universe is narrow and explicit: `MACRO_DRIVERS + INDICES +
  COMMODITIES + HIGH_BETA` at
  [config.py:149-155](cuttingboard/config.py#L149-L155) — 23 symbols.
  Adding a new symbol requires touching `config.py` (PRICE_BOUNDS,
  SYMBOL_SOURCE_PRIORITY) and is mechanically gated.
- No generic plugin loader, no symbol registry, no instrument-type
  abstraction beyond `OptionSetup` (spreads only).

## 6. Not a high-frequency signal factory

**Status: CLEAN.**

Evidence:
- Quote freshness window: 300s (`FRESHNESS_SECONDS`); intraday bar
  cadence is 1-minute aggregation, not tick.
- `INTRADAY_ALERT_COOLDOWN = 90` minutes; PT-anchored hourly alert slots
  are the cadence ceiling (PRD-149).
- `EXECUTION_POLICY_MAX_TRADES_PER_DAY = 2`. The system is explicitly
  built around low trade frequency, not signal-firing.

## 7. Not a regulated-infrastructure project requiring aircraft-grade process

**Status: CLEAN.**

Evidence:
- Solo-developer cadence per VISION.md.
- PRD lane classification (MICRO / STANDARD / HIGH-RISK) per PRD-121
  explicitly calibrates ceremony to risk. Recent MICRO PRDs (PRD-140,
  PRD-148) ran with proportionate weight.
- No audit-trail compliance framework, no SOX/ITAR/HIPAA-shaped artifact
  requirements.

## Headline

All seven non-goals: **CLEAN.** The 2026-05-22 cleanup pass directly
removed two of the closest creep vectors (backtesting harness, LLM macro
sidecar). No minor creep observed.
