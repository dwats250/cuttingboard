# CODEX.md — cuttingboard

## PURPOSE

Implement defined systems with precision and minimal scope.

- Constraint-driven options trading decision engine
- Fixed pipeline architecture — not a research library
- Output contract: `TRADES | NO TRADE | HALT` — exactly one per run

---

## SYSTEM STATE (2026-04-27)

All pipeline layers are built and wired. 830 tests passing.

### PIPELINE LAYERS

| Layer | Module | Role |
|---|---|---|
| 1 | `config.py` | Constants and secrets. All from .env. Never hardcode. |
| 2 | `ingestion.py` | RawQuote. yfinance primary, Polygon fallback. OHLCV parquet cache. |
| 3 | `normalization.py` | NormalizedQuote. pct_change → decimal, UTC, units. |
| 4 | `validation.py` | Hard validation gate. HALT_SYMBOL failure stops pipeline. |
| 5 | `derived.py` | EMA9/21/50, ATR14 (Wilder RMA), momentum_5d, volume_ratio. Validated symbols only. |
| 6 | `structure.py` | TREND / PULLBACK / BREAKOUT / REVERSAL / CHOP per ticker. |
| 7 | `regime.py` | 8-vote model → RISK_ON / RISK_OFF / NEUTRAL / CHAOTIC + posture. |
| 8 | `qualification.py` | 9-gate qualification. Hard gates 1–4, soft gates 5–9+. |
| 9 | `options.py` | Spread selection, DTE, strike distance. |
| 10 | `chain_validation.py` | Live chain liquidity gate. OI, spread %, bid/ask sanity. |
| 11 | `output.py` | Pure render + delivery layer. Terminal, markdown, Telegram. No pipeline logic. |
| — | `audit.py` | Append-only JSONL per run. |
| — | `runtime.py` | Sole production orchestrator. All modes routed through `cli_main()`. |
| — | `run_intraday.py` | Unscheduled legacy module. Trigger-based regime monitor (L1–5). Not invoked by any workflow. |
| — | `watch.py` | Intraday watchlist classification and session phase. |
| — | `intraday_state_engine.py` | ORB classification. |
| — | `notifications/` | ntfy alert formatting. |

---

## INSTRUMENT UNIVERSE

**HALT_SYMBOLS (pipeline stops if any fail):** `^VIX`, `DX-Y.NYB`, `^TNX`, `SPY`, `QQQ`

**Required:** `^VIX`, `DX-Y.NYB`, `^TNX`, `BTC-USD`, `SPY`, `QQQ`

**Indices:** `SPY`, `QQQ`, `IWM`

**Commodities:** `GLD`, `SLV`, `GDX`, `PAAS`, `USO`, `XLE`

**High beta:** `NVDA`, `TSLA`, `AAPL`, `META`, `AMZN`, `COIN`, `MSTR`

**Source rules:** `^VIX`, `DX-Y.NYB`, `^TNX` — yfinance only. All others: yfinance primary, Polygon fallback.

**Constraints:** Liquid options chains only. Tight bid/ask. No arbitrary expansion. 5–8 tickers per session.

---

## REGIME ENGINE

8-input vote model. Each input: `RISK_ON | RISK_OFF | NEUTRAL`

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

**CHAOTIC override:** VIX spike > 15% in one interval → CHAOTIC, regardless of votes.

**Classification:** `net = risk_on − risk_off`. RISK_ON if net ≥ 4 and conf ≥ 0.60, or net ≥ 2. RISK_OFF if net ≤ -4 and conf ≥ 0.60, or net ≤ -2. Else NEUTRAL.

**Postures:** CHAOTIC or conf < 0.50 → STAY_FLAT. RISK_ON + conf ≥ 0.75 → AGGRESSIVE_LONG. RISK_ON + conf ≥ 0.55 → CONTROLLED_LONG. RISK_OFF + conf ≥ 0.55 → DEFENSIVE_SHORT. NEUTRAL + VIX 18–25 → NEUTRAL_PREMIUM. All other NEUTRAL → STAY_FLAT.

STAY_FLAT short-circuits all per-symbol qualification — no gates run.

---

## QUALIFICATION GATES

Hard (1–4): immediate REJECT, no watchlist.
Soft (5–11): one miss → WATCHLIST. Two+ → REJECT.

1. **(HARD) REGIME** — posture ≠ STAY_FLAT
2. **(HARD) CONFIDENCE** — conf ≥ 0.50
3. **(HARD) DIRECTION** — direction matches regime (RISK_ON=LONG, RISK_OFF=SHORT)
4. **(HARD) STRUCTURE** — not CHOP
5. **(SOFT) STOP_DEFINED** — stop_price > 0, distance > 0
6. **(SOFT) STOP_DISTANCE** — stop ≥ 1% of entry AND ≥ 0.5× ATR14
7. **(SOFT) RR_RATIO** — R:R ≥ 2.0 (NEUTRAL: ≥ 3.0)
8. **(SOFT) MAX_RISK** — 1 contract fits within TARGET × regime_multiplier
9. **(SOFT) EARNINGS** — no earnings within 5 days (None → pass)
10. **(SOFT) EXTENSION** — |entry − ema21| / atr14 ≤ 1.5
11. **(SOFT) TIME** — no entries at or after 3:30 PM ET

---

## KEY CONSTANTS

```
MIN_RR_RATIO            = 2.0
NEUTRAL_RR_RATIO        = 3.0
MIN_REGIME_CONFIDENCE   = 0.50
TARGET_DOLLAR_RISK      = $150
MAX_DOLLAR_RISK         = $200
FRESHNESS_SECONDS       = 300
EXTENSION_ATR_MULTIPLIER= 1.5
VIX_CHAOTIC_SPIKE       = 0.15
EMA periods             = 9 / 21 / 50
ATR period              = 14 (Wilder RMA)
LATE_SESSION_CUTOFF     = 15:30 ET
REGIME_RISK_MULTIPLIER  = RISK_ON:1.0 / RISK_OFF:1.0 / NEUTRAL:0.6 / CHAOTIC:0.0
```

---

## CORE RULES

1. **NO SCOPE EXPANSION** — implement only what is requested
2. **NO BLOAT** — no speculative logic, no unused abstractions, no dead helpers
3. **SURGICAL CHANGES** — smallest correct patch first; full file only when necessary
4. **SINGLE RESPONSIBILITY** — one module, one purpose, no mixed concerns
5. **PRD REQUIRED** — OBJECTIVE, SCOPE, REQUIREMENTS, DATA FLOW, FAIL CONDITIONS before any code

---

## CODE STANDARDS

- No placeholders
- No dead code
- No unused imports
- No overlapping logic across modules
- All dataclasses frozen=True unless documented otherwise
- All timestamps UTC with tzinfo — never naive
- Never silently catch exceptions that hide data failures
- No derived metric on unvalidated input — ever
- PRICE_BOUNDS must be updated periodically (current market levels)

---

## TOKEN DISCIPLINE

- Read only necessary files
- No full repository scans
- Output minimal and direct
- Do not repeat explanations

---

## GITNEXUS — IMPACT ANALYSIS POLICY

This project is indexed by GitNexus. Use MCP tools to navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` first.

**Skip `gitnexus_impact` for low-risk edits:**
- Constants, config thresholds, or numeric values (e.g. in `config.py`)
- String literals, log messages, or error text
- Comments or docstrings
- PRD bookkeeping files (`PRD_REGISTRY.md`, `PROJECT_STATE.md`, `prd_history/`)
- Test assertions or test data fixtures

**Always run `gitnexus_impact({target, direction: "upstream"})` before editing:**
- Any function or method signature or return type
- Any validation, qualification, regime, or derived metric logic
- Any module in the execution pipeline (layers 1–11 above)
- Any symbol flagged HIGH or CRITICAL in a prior impact report
- Any rename or structural refactor

**Always run `gitnexus_detect_changes()` before every commit** — no exceptions.

**Warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding.

**Never:**
- Ignore HIGH or CRITICAL risk warnings
- Rename symbols with find-and-replace — use `gitnexus_rename`
- Commit without running `gitnexus_detect_changes()`

---

## VALIDATION

Always report:

```
VALIDATION:
- command(s) run
- result
- what is proven
- what remains unverified
```

If not run: state explicitly.

---

## OUTPUT

Always include:

```
SUMMARY:
- files changed
- logic added or modified
- integration points

RUN:
- exact command(s) to execute or test
```

---

## FAILURE CONDITIONS

Reject or flag output that:

- Expands scope beyond request
- Duplicates existing logic
- Introduces unnecessary complexity
- Weakens validation
- Missing or unclear verification

---

## PRIORITY ORDER

1. correctness
2. scope control
3. simplicity
4. execution relevance
5. maintainability
6. validation honesty
7. speed
8. convenience

---

## ASSUMPTIONS

- Narrowest reasonable interpretation only
- Do not infer new architecture, features, or systems
- If an assumption affects behavior: state it in SUMMARY, do not expand beyond it

---

## PRD DOCUMENTATION RULE

Canonical process: `docs/PRD_PROCESS.md`. Summary below.

### Lifecycle States

| State | Meaning |
|-------|---------|
| PROPOSED | Drafted. Not approved for implementation. |
| IN PROGRESS | File exists in prd_history/. Implementation has begun. |
| COMPLETE | Implementation merged. Commit hash recorded in registry. |
| PATCH | Corrective PRD targeting a specific defect in a prior PRD. |
| DEPRECATED | Requirement superseded or withdrawn before completion. |

No other status values are permitted in `PRD_REGISTRY.md`.

### Starting a PRD

1. Copy `docs/PRD_TEMPLATE.md` to `docs/prd_history/PRD-NNN.md` before writing any code.
2. Section order is fixed: `GOAL → SCOPE → OUT OF SCOPE → FILES → REQUIREMENTS → DATA FLOW → FAIL CONDITIONS → VALIDATION`
3. Add registry row with `IN PROGRESS` and file link immediately.
4. Every requirement (R1, R2, …) must have an inline `FAIL:` line — observable, binary, non-subjective.

### Scope Lock

The `FILES` section defines a hard boundary. Any file modified during implementation that is not listed in `FILES` is a scope violation. Resolve by amending the PRD before touching the file, or write a separate PRD.

### Closing a PRD

After merge: set registry status to `COMPLETE`, record commit hash, and ensure the `File` column links to the prd_history file.

### Patch PRDs

A PATCH PRD corrects a defect in a prior implementation. Must include a `ROOT CAUSE` section identifying exactly one of: `missing fail condition`, `ambiguous requirement`, or `hidden dependency`.

A PRD is not complete until the registry reflects it.

---

## GIT HYGIENE AND ARTIFACT DISCIPLINE

**Before starting work:**
- Verify branch: `git branch --show-current`. Default to `main` unless otherwise specified.
- Check status: `git status --short`. Do not start with unresolved conflicts.

**Generated artifacts:**
- Do not commit `logs/*` or `reports/*` unless the user explicitly requests it.
- Never use `git add .` — stage explicit files only.
- Run `scripts/clean_generated_artifacts.sh` to restore tracked log files to HEAD if needed.

**Before committing:**
- Show staged: `git diff --cached --name-only`
- Warn if `logs/*` or `reports/*` are staged.
- Run `scripts/pre_commit_sanity.sh` for a compact checklist.

**Workflow reruns:** match issue to workflow — Pipeline / Deploy to GitHub Pages / Hourly Alert. Use `--ref main` unless another branch is required.

---

## FINAL RULE

When uncertain: reduce scope → patch minimally → validate honestly.
