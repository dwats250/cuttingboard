# NS-4C Leadership v0 — owner ratification sheet

Status: STAGE-0 / OWNER INPUT REQUIRED
Date: 2026-09-06 PT

## Product target

Build the smallest observe-only NS-4C Leadership slice on top of the existing NS-4A registry (PRD-308) and NS-4B movement snapshot/card (PRD-311).

The v0 product question is deliberately narrow:

> Which observed instruments are leading or lagging their owner-assigned benchmark on the same daily-change observation?

No prediction, scoring, trade permission, sizing, execution, breadth, participation, ranking persistence, provider expansion, or new fetch path.

## Why owner input is required

The current `UniverseInstrument` registry has exactly six fields and intentionally omitted `benchmark` in PRD-308. NS-4C's North Star definition requires relative performance versus an **assigned benchmark**. The governing universe doctrine makes those assignments human-authored; they must not be inferred by an agent.

Therefore implementation stops at this sheet until Dustin ratifies the benchmark relationship for every enabled v0 symbol.

## Proposed smallest benchmark map — NOT AUTHORITY UNTIL RATIFIED

This proposal minimizes new semantics and uses only instruments already present in the 12-symbol observation set.

| Symbol | Group | Proposed benchmark | Rationale | Owner disposition |
|---|---|---|---|---|
| SPY | INDEX | SPY | market baseline; relative value = 0 by definition | RATIFY / CHANGE |
| QQQ | INDEX | SPY | large-cap growth/tech relative to broad market | RATIFY / CHANGE |
| GDX | METALS | GLD | miners relative to gold ETF | RATIFY / CHANGE |
| GLD | METALS | SPY | gold relative to broad market | RATIFY / CHANGE |
| SLV | METALS | GLD | silver relative to gold/metals anchor | RATIFY / CHANGE |
| XLE | ENERGY | SPY | energy sector relative to broad market | RATIFY / CHANGE |
| UCO | ENERGY | XLE | crude-oil proxy relative to energy sector | RATIFY / CHANGE |
| NVDA | TECH | QQQ | semiconductor bellwether relative to tech-heavy index | RATIFY / CHANGE |
| META | TECH | QQQ | large-cap tech relative to tech-heavy index | RATIFY / CHANGE |
| AMZN | TECH | QQQ | large-cap tech relative to tech-heavy index | RATIFY / CHANGE |
| GOOG | TECH | QQQ | large-cap tech relative to tech-heavy index | RATIFY / CHANGE |
| TSLA | HIGH_BETA | QQQ | high-beta growth name relative to tech-heavy index | RATIFY / CHANGE |

## Proposed v0 semantics — safe to ratify separately from the map

For a symbol and benchmark whose `daily_change_pct` values are both finite floats in the **same accepted PRD-311 snapshot**:

`relative_pct = symbol.daily_change_pct - benchmark.daily_change_pct`

Display only:
- `> +0.05 pp`: `LEADING`
- `< -0.05 pp`: `LAGGING`
- otherwise: `INLINE`
- missing/null either side: `n/a`

The 0.05 percentage-point deadband is presentation noise suppression only; it carries no decision authority and does not persist state.

## Binding implementation boundary once ratified

1. Add a human-authored benchmark relationship to the NS-4A substrate with no derived/inferred assignments.
2. Reuse the existing PRD-311 watchlist snapshot only; no second fetch and no wall clock.
3. Build a pure display consumer that computes the one-period relative spread above.
4. Render a compact `LEADERSHIP` block near `MARKET MOVEMENT`.
5. Suppress/fail neutral on malformed or incomplete snapshot data.
6. No edits to regime, qualification, macro pressure, execution policy, candidate selection, GEX, or provider acquisition.
7. NS-4D participation/breadth remains explicitly out of scope.

## Owner decision

Implementation may begin only after Dustin ratifies or edits the 12 benchmark assignments above. A simple approval of the table is sufficient; changed rows can be supplied as `SYMBOL -> BENCHMARK`.