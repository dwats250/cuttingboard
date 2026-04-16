## claude.md — cutting board

## purpose

Claude builds and refines a constraint-driven trading system.

Goal:

improve trade decisions
- enforce clarity and discipline
- prevent system drift

system type:- Decision engine supported by minimal tools
not a research library
- not a feature-rich platform

---

## instrument universe

## core (primary)

spy, qqq
gld, iau
slv, sivr

## high liquidity options

nvda, tsla, aapl, msft, amzn, meta, goog, pltr

## high beta / volatility

mstr, coin, smci, mu

## macro / context (reference)

xle, uso, gdx
dxy
us10y (preferred) or ^tnx fallback
vix

## constraints

- trade only liquid instruments
- prefer tight spreads and high open interest
- do not expand universe without justification
- focus on 5–8 tickers per session

---

## core rules

## 1. execution only

- all outputs must affect:- entry
  - exit
  - sizing
  - avoidance
otherwise:reject

## 2. no bloat

do not add features, signals, or abstractions
- default to the simplest working solution

## 3. constraints first

- prefer strict rules over flexible logic
- limit number of conditions and inputs

## 4. single responsibility

- each component has one purpose
- no overlapping logic

---

## output

be:- concise
structured
- direct

do not:- repeat prompt
over-explain
- add filler

---

## prd requirement

always define before building:- OBJECTIVE
scope (include + exclude)
- requirements
- data flow
- fail conditions

no coding without this.

---

## research rule

only output:INSIGHT:

one sentence

conditions:- measurable only

TRADE IMPACT:

entry / exit / sizing / avoidance

integration:- one playbook only

Reject if unclear.

---

## failure conditions

Reject or correct if:

adds complexity
- expands scope
- lacks execution impact
- introduces vague logic

---

## priority order

when rules conflict, prioritize:1. correctness
2. scope control
3. simplicity
4. execution relevance
5. maintainability
6. validation honesty
7. speed
8. convenience

---

## assumptions

use the narrowest reasonable interpretation of the request
- do not expand scope based on assumptions
- if an assumption materially affects logic or structure:- state it briefly
  - proceed without expanding beyond it

---

## documentation expectation

Document only what improves:

decision clarity
- system behavior
- integration understanding

do not:- add general explanations
repeat known information
- create essay-style documentation

---

## package

the python package is named `cuttingboard`.
all imports use:`from cuttingboard.xxx import yyy`

## technical rules

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

## final rule

When uncertain:
→ simplify
→ reduce
→ constrain