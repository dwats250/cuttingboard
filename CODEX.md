# CODEX.md -- CUTTING BOARD

## PURPOSE

Codex implements defined systems with precision and minimal scope.

System:

- Constraint-driven trading decision engine
- Options-focused execution
- Limited, high-liquidity instrument universe

---

## INSTRUMENT CONTEXT

Primary:
SPY, QQQ
GLD, IAU
SLV, SIVR

Secondary:
NVDA, TSLA, AAPL, MSFT, AMZN, META, GOOG, PLTR

High Beta:
MSTR, COIN, SMCI, MU

Context:
XLE, USO, GDX
DXY
US10Y (preferred) or ^TNX fallback
VIX

Constraints:

- Favor liquid options chains
- Avoid wide bid/ask spreads
- No arbitrary ticker expansion

---

## CORE RULES

1. NO SCOPE EXPANSION

- Only implement what is requested
- Do not add adjacent features or improvements

2. NO BLOAT

- No speculative logic
- No unnecessary abstractions
- No unused helpers

3. SURGICAL CHANGES

- Smallest correct patch first
- Full files only when necessary

4. SINGLE RESPONSIBILITY

- One function = one purpose
- No mixed concerns across modules

---

## TOKEN DISCIPLINE

- Read only necessary files
- Avoid full repository scans
- Keep output minimal and direct
- Do not repeat explanations

---

## CODE STANDARDS

- No placeholders
- No dead code
- No unused imports
- Clear and readable logic preferred over cleverness

---

## VALIDATION

Always report:

VALIDATION:

- command(s) run
- result
- what is proven
- what remains unverified

If not run:

- state explicitly

---

## OUTPUT

Always include:

SUMMARY:

- files changed
- logic added or modified
- integration points

RUN:

- exact command(s) to execute or test

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

- Use the narrowest reasonable interpretation
- Do not infer new architecture, features, or systems
- If an assumption affects behavior or structure:
  - state it in SUMMARY
  - do not expand beyond it

---

## DOCUMENTATION RULE

Document only what affects:

- behavior
- usage
- validation
- integration

Do not:

- add broad commentary
- duplicate existing documentation
- document unused or speculative features

---

## FAILURE CONDITIONS

Reject or correct output if:

- scope expands beyond request
- logic duplicates existing code
- unnecessary complexity is introduced
- validation is missing or unclear

---

## FINAL RULE

When uncertain:
-> reduce scope
-> patch minimally
-> validate honestly
