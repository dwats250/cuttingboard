# CLAUDE.md — CUTTING BOARD

## PURPOSE

Claude builds and refines a constraint-driven trading system.

Goal:

- Improve trade decisions
- Enforce clarity and discipline
- Prevent system drift

System type:

- Decision engine supported by minimal tools
- Not a research library
- Not a feature-rich platform

---

## INSTRUMENT UNIVERSE

### CORE (PRIMARY)

SPY, QQQ
GLD, IAU
SLV, SIVR

### HIGH LIQUIDITY OPTIONS

NVDA, TSLA, AAPL, MSFT, AMZN, META, GOOG, PLTR

### HIGH BETA / VOLATILITY

MSTR, COIN, SMCI, MU

### MACRO / CONTEXT (REFERENCE)

XLE, USO, GDX
DXY
US10Y (preferred) or ^TNX fallback
VIX

### CONSTRAINTS

- Trade only liquid instruments
- Prefer tight spreads and high open interest
- Do not expand universe without justification
- Focus on 5–8 tickers per session

---

## CORE RULES

### 1. EXECUTION ONLY

- All outputs must affect:
  - entry
  - exit
  - sizing
  - avoidance
- Otherwise: reject

### 2. NO BLOAT

- Do not add features, signals, or abstractions
- Default to the simplest working solution

### 3. CONSTRAINTS FIRST

- Prefer strict rules over flexible logic
- Limit number of conditions and inputs

### 4. SINGLE RESPONSIBILITY

- Each component has one purpose
- No overlapping logic

---

## OUTPUT

Be:

- concise
- structured
- direct

Do not:

- repeat prompt
- over-explain
- add filler

---

## PRD REQUIREMENT

Always define before building:

- OBJECTIVE
- SCOPE (include + exclude)
- REQUIREMENTS
- DATA FLOW
- FAIL CONDITIONS

No coding without this.

---

## RESEARCH RULE

Only output:

INSIGHT:

- one sentence

CONDITIONS:

- measurable only

TRADE IMPACT:

- entry / exit / sizing / avoidance

INTEGRATION:

- one playbook only

Reject if unclear.

---

## FAILURE CONDITIONS

Reject or correct if:

- adds complexity
- expands scope
- lacks execution impact
- introduces vague logic

---

## PRIORITY ORDER

When rules conflict, prioritize:

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

- Use the narrowest reasonable interpretation of the request
- Do not expand scope based on assumptions
- If an assumption materially affects logic or structure:
  - state it briefly
  - proceed without expanding beyond it

---

## DOCUMENTATION EXPECTATION

Document only what improves:

- decision clarity
- system behavior
- integration understanding

Do not:

- add general explanations
- repeat known information
- create essay-style documentation

---

## PACKAGE

The Python package is named `cuttingboard`.
All imports use: `from cuttingboard.xxx import yyy`

## TECHNICAL RULES

1. Build in strict phase order. Do not begin Phase N+1 until Phase N has passing tests.
2. Never hardcode secrets. All secrets come from .env via config.py.
3. Never silently catch exceptions that hide data failures. Log them explicitly.
4. No derived metric is computed on unvalidated input. Ever.
5. When in doubt, refer to PRD.md. Do not improvise architecture.
6. All dataclasses are frozen=True unless documented otherwise.
7. All timestamps are UTC datetime with tzinfo. Never naive datetimes.
8. The validation layer is the most important layer. Do not weaken it.
9. If a symbol fails validation, exclude it and log why. Never substitute.
10. The system always produces one of three outputs: TRADES | NO TRADE | HALT.
11. No HTML output, no web server, no backtest engine, no ML models.

Do not advance a phase without passing unit tests and manual spot-check against real market data.

---

## FINAL RULE

When uncertain:
→ simplify
→ reduce
→ constrain
