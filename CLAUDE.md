# CLAUDE.md — cuttingboard

## purpose

Build and refine a constraint-driven options trading decision engine.

- Improve trade decisions
- Enforce clarity and discipline
- Prevent system drift

**System type:** Decision engine with a fixed pipeline. Not a research library. Not a feature-rich platform.

**Output contract:** Every run produces exactly one of: `TRADES | NO TRADE | HALT`

---

## system state

See `docs/PROJECT_STATE.md` for current test baseline, active PRD, and pipeline status. Pipeline architecture is indexed by GitNexus — use `gitnexus_query` or `gitnexus_context` to navigate modules rather than reading this file.

---

## session mode

Operate REPO-FIRST. Memory hierarchy (strict):

1. Active PRD (`docs/prd_history/PRD-NNN.md`)
2. `docs/PROJECT_STATE.md`
3. This file (CLAUDE.md)
4. Repo source code via GitNexus
5. Chat context — last resort only

**Startup sequence every session:**
1. Read `docs/PROJECT_STATE.md` — identifies active PRD and test baseline
2. Read the active PRD — defines exact scope, files, and requirements
3. Use GitNexus to locate affected modules and consumers before touching any code

**Constraints:**
- Do not rely on chat history for system understanding
- Do not ask for project summaries — query the repo
- Read only the minimum files needed
- No scope drift, no inferred features, no modifications outside PRD FILES section
- Raise errors instead of silently handling invalid states
- All changes must preserve contract integrity, notification behavior, and decision logic

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

## PRD documentation rule

Canonical process: `docs/PRD_PROCESS.md`. Summary below.

### Lifecycle states

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

### Scope lock

The `FILES` section defines a hard boundary. Any file modified during implementation that is not listed in `FILES` is a scope violation. Resolve by amending the PRD before touching the file, or write a separate PRD.

### Closing a PRD

After merge: set registry status to `COMPLETE`, record commit hash, and ensure the `File` column links to the prd_history file.

### Patch PRDs

A PATCH PRD corrects a defect in a prior implementation. Must include a `ROOT CAUSE` section identifying exactly one of: `missing fail condition`, `ambiguous requirement`, or `hidden dependency`.

A PRD is not complete until the registry reflects it.

---

## final rule

When uncertain: simplify → reduce → constrain.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **cuttingboard** (5710 symbols, 11998 relationships, 141 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/cuttingboard/context` | Codebase overview, check index freshness |
| `gitnexus://repo/cuttingboard/clusters` | All functional areas |
| `gitnexus://repo/cuttingboard/processes` | All execution flows |
| `gitnexus://repo/cuttingboard/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
