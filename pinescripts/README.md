# pinescripts/

TradingView Pine indicators for visual analysis alongside the Cuttingboard system. **Detached tools** — not part of the production pipeline, not consumed by any Python code, not subject to PRD discipline. Their job is to render the same metrics Cuttingboard reasons about, on a chart, so visual and systematic analysis tell the same story.

## Current state

Empty. Prior artifacts (`0dte Momentum Setup`, `algos/orb_reference.py`) were removed during the 2026-05-22 cleanup as unused legacy. See `docs/DECISIONS.md` for context.

## Intended rebuilds

Two indicators planned. Neither is on the current roadmap — these are notes-to-self for when there's time and the need is real.

### 1. ORB indicator (clean, study-grounded)

A minimal Opening Range Breakout indicator. Single timeframe, single setup, no indicator soup.

- Grounded in a specific study from SSRN rather than improvised parameters
- Renders only what the setup actually requires (opening range high/low, breakout level, invalidation)
- No layered alternatives, no "kitchen sink" overlays
- Aligned with Cuttingboard's intraday state engine — same conceptual frame, visual rendering

### 2. Multi-tool monitoring utility

A single Pine script bundling several TA layers (ATR, RSI, EMAs/MAs, VWAP) with toggle switches, used as a utility while monitoring setups surfaced by Cuttingboard.

- Works around TradingView's free-tier 2-indicator limit by combining several into one toggleable script
- Layers correspond to the metrics Cuttingboard uses internally — same periods, same thresholds, no drift between chart and system
- Toggle layers based on the question being asked:
  - *What environment* → regime layers
  - *Is this tradable* → entry-quality layers
  - *What invalidates* → structure/level layers
- Detached from Cuttingboard's Python pipeline — pure visual aid, no shared state

## Principles

- These are visual aids, not signal generators. They render context; they do not decide trades.
- Parameter values (ATR period, EMA lengths, RSI bounds) should mirror Cuttingboard's configuration so chart and system agree on what they're measuring.
- Keep each script narrow. Resist the temptation to add indicators "because they might be useful."
- If a rebuild lands, add it back to this directory with a short header explaining its intent and parameter sources.
