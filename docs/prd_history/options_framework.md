# Cuttingboard — Options Framework

## Overview

The options layer maps each qualified trade setup to a specific spread strategy. It does not look up actual options chains — there is no options broker integration. Instead, it produces a complete **strategy description** from first principles:

- **What kind of spread** to put on (from the strategy matrix)
- **Which relative strikes** to use (ATM or 1_ITM — never absolute prices)
- **How wide** to make the spread (based on symbol class)
- **Which expiry** to target (from structure + momentum)
- **How many contracts** (from the qualification layer's sizing formula)

You do the final strike lookup at your broker at entry time.

---

## IV Environment Classification

IV environment is classified from the current VIX level and used to select debit vs. credit strategy:

| VIX Level | IV Environment | Meaning |
|-----------|---------------|---------|
| < 15 | `LOW_IV` | Cheap options, debit spreads preferred |
| 15 – 20 | `NORMAL_IV` | Typical conditions, debit spreads preferred |
| 20 – 28 | `ELEVATED_IV` | Higher premium, credit spreads preferred |
| > 28 | `HIGH_IV` | Elevated premium, credit spreads strongly preferred |

**Why switch between debit and credit at elevated IV?**

In LOW/NORMAL IV, you pay less to buy options, so debit spreads have better expected value. In ELEVATED/HIGH IV, option premiums are inflated — you pay more for the long leg of a debit spread, reducing your edge. Credit spreads let you collect that inflated premium instead of paying it.

The IV environment is computed once per run and stored in `StructureResult.iv_environment`. It is the same for all symbols in a given run (VIX is a market-wide measure).

---

## Strategy Selection Matrix

| Direction | IV Environment | Strategy | Type |
|-----------|---------------|----------|------|
| LONG | LOW_IV | `BULL_CALL_SPREAD` | Debit |
| LONG | NORMAL_IV | `BULL_CALL_SPREAD` | Debit |
| LONG | ELEVATED_IV | `BULL_PUT_SPREAD` | Credit |
| LONG | HIGH_IV | `BULL_PUT_SPREAD` | Credit |
| SHORT | LOW_IV | `BEAR_PUT_SPREAD` | Debit |
| SHORT | NORMAL_IV | `BEAR_PUT_SPREAD` | Debit |
| SHORT | ELEVATED_IV | `BEAR_CALL_SPREAD` | Credit |
| SHORT | HIGH_IV | `BEAR_CALL_SPREAD` | Credit |

The crossover is at VIX = 20. Below 20 → debit. At or above 20 → credit.

---

## Strike Selection

Strikes are always expressed relative to the current underlying price. Never as absolute dollar levels.

| Strategy | Long Strike | Short Strike | Notes |
|----------|-------------|--------------|-------|
| `BULL_CALL_SPREAD` | `1_ITM` call | `ATM` call | Buy one strike below price, sell at price |
| `BULL_PUT_SPREAD` | `ATM-{w}` put | `ATM` put | Sell the ATM put, buy the lower put |
| `BEAR_PUT_SPREAD` | `1_ITM` put | `ATM` put | Buy one strike above price (ITM for puts), sell at price |
| `BEAR_CALL_SPREAD` | `ATM` call | `ATM+{w}` call | Sell the ATM call, buy the higher call |

Where `{w}` is the strike distance in dollars (see spread width section below).

**Translating to your broker:**

For a BULL_CALL_SPREAD on QQQ trading at $480 with $5 width:
- Identify the nearest strike at or below $480 → this is "ATM" ($480 or the nearest available strike)
- Find the strike one step below → this is "1_ITM" ($479 on a $1-increment chain, or $475 on a $5-increment chain)
- Long leg: buy the 1_ITM call ($479 or $475)
- Short leg: sell the ATM call ($480 or the strike you identified as ATM)

Use whatever strike increment your broker offers for that expiry. Weekly options on SPY/QQQ typically have $1 increments. Monthly options often have $5 increments. Prefer the increment that gets you closest to the labeled strikes.

---

## Spread Width and Sizing

The system uses two maximum spread widths based on instrument class:

| Symbol Class | Max Strike Distance | Estimated Debit | Contracts | Max Risk |
|-------------|--------------------|-----------------|-----------|-|
| Index ETFs (SPY, QQQ, IWM) | $5.00 | $1.50 | 1 | $150 |
| All other symbols | $2.50 | $0.75 | 2 | $150 |

**What "estimated debit" means:** The system estimates the net debit at approximately 30% of the strike distance. This is a rough approximation for an ATM vertical spread. Actual debit will vary based on IV, time to expiry, and the specific strikes available.

**At your broker:** If the actual debit is materially different from the estimate (e.g., you're looking at $2.10 debit for what should be ~$1.50), check:
1. Are you using the right strike increments?
2. Is the selected expiry reasonable? (DTE in the report is a target — adjust to the nearest available expiry)
3. Has IV changed significantly since the premarket run?

If the real debit would risk more than $150 total (e.g., actual debit × max_contracts × 100 > $150), **reduce contracts by 1** rather than exceeding the budget. Never exceed the `max_contracts` figure from the report.

---

## DTE Selection

Target days-to-expiry is selected from the symbol's market structure, with fine-tuning from recent momentum:

| Structure | Base DTE | Notes |
|-----------|----------|-------|
| `BREAKOUT` | 7 DTE | Fast-momentum play; time decay works against you quickly |
| `REVERSAL` | 7 DTE | Crossover signal — short duration to capture the initial move |
| `PULLBACK` | 14 DTE | Bounce expected within two weeks |
| `TREND` | 21 DTE | Sustained move; give the trade room |

**Momentum compression:** If `|momentum_5d| ≥ 0.03` (3% five-day return), the DTE is compressed one tier:
- PULLBACK with strong momentum: 7 DTE (instead of 14)
- TREND with strong momentum: 14 DTE (instead of 21)
- BREAKOUT/REVERSAL: already at minimum (7 DTE), no further compression

**At your broker:** Find the weekly or monthly expiry at or above the target DTE. Avoid expiries that land on or immediately after a known catalyst (earnings, Fed meeting, major economic data).

**Example:** DTE=14 on a Monday → look for the expiry two weeks out (the following Friday). If that Friday has unusual open interest or a known event, use the next available expiry (21 DTE).

---

## Exit Rules

Every trade uses the same two-condition exit. Set both orders at the time of entry.

**Exit 1: Profit target — close at +50% of maximum profit**

For debit spreads: max profit = (strike distance − net debit) × 100
- 50% profit target = close when spread is worth net_debit + (max_profit × 0.50)
- Example: $1.50 debit on $5-wide spread → max profit = $3.50 → close when spread worth $1.50 + $1.75 = $3.25

For credit spreads: max profit = net credit received × 100
- 50% profit target = close when you can buy back the spread for 50% of what you received
- Example: received $1.50 credit → close (buy back) when spread worth $0.75

**Exit 2: Loss limit — close on full debit loss**

For debit spreads: the spread expires worthless or goes to near zero. Set a GTC order to close if the spread drops to $0.05 (or 5% of debit, whichever is less).

For credit spreads: close if the spread widens to the full spread width minus the initial credit (i.e., full max loss).

**Why 50%?** Closing at 50% of max profit captures most of the available gain while avoiding the asymmetric risk of holding near expiration. The last 50% of profit typically requires holding through gamma acceleration, where small adverse moves can rapidly erode the position.

---

## Pre-Entry Verification Checklist

Before placing any order from the morning report, verify the following at your broker:

**1. Price confirmation**
- [ ] Underlying is trading within 1% of the price used in the report
- [ ] If it's moved more than 1% since market open, recalculate your strikes

**2. Strike availability**
- [ ] Strikes exist at or near the reported labels (1_ITM, ATM)
- [ ] If your broker uses different increments, the nearest available strike is within $1 of the target

**3. Expiry selection**
- [ ] Weekly expiry at or above the target DTE is available
- [ ] No earnings, ex-dividend dates, or major catalysts fall within the expiry window

**4. IV check**
- [ ] IV has not changed by more than 3 points since the premarket run
- [ ] If IV has spiked significantly (VIX up >10% since 13:00 UTC), consider whether the strategy type is still appropriate (elevated IV may favor credit spreads even if the report said debit)

**5. Debit/credit confirmation**
- [ ] Actual debit/credit is within 20% of the report's `spread_width × 100` estimate
- [ ] Total risk (debit × max_contracts × 100) does not exceed the report's `dollar_risk`
- [ ] If actual cost is higher, reduce contracts by 1

**6. Position size**
- [ ] Total risk across all open positions + today's new positions ≤ your personal daily risk limit
- [ ] Number of contracts does not exceed `max_contracts` from the report

**7. Exit orders**
- [ ] Profit target order placed immediately at fill (GTC limit order to sell)
- [ ] Loss limit order placed immediately at fill (GTC stop order)

---

## Why Strikes Are Never Absolute

The options layer intentionally avoids computing absolute strike prices. The reasons:

1. **Data freshness:** The premarket run executes at 13:00 UTC. By the time you look at the report at 06:05 PT, the underlying may have moved. An absolute strike ($479) from 13:00 UTC may be ITM, ATM, or OTM depending on where the stock is now. A relative label (1_ITM) is always meaningful regardless of when you execute.

2. **Strike availability:** Different brokers and expirations have different strike increments. $1 increments, $2.50 increments, $5 increments. A relative label lets you find the closest available strike without confusion.

3. **Simplicity and safety:** Computing "the exact right strike" requires a live options chain feed. The system doesn't have one. It is more honest to say "1_ITM" than to provide a stale absolute strike that might mislead you at execution time.

---

## Extending the Options Layer

### Adding a new strategy type

To add IRON_CONDOR for NEUTRAL_PREMIUM posture:

1. Add the strategy constant in `options.py`:
   ```python
   IRON_CONDOR = "IRON_CONDOR"
   ```

2. Extend `_select_strategy()` to handle the NEUTRAL_PREMIUM case:
   ```python
   if direction == "NEUTRAL":   # new direction type
       return IRON_CONDOR
   ```

3. Add strike formatting in `_format_strikes()`:
   ```python
   if strategy == IRON_CONDOR:
       return f"ATM-{w}", f"ATM+{w}"  # returns put spread + call spread notation
   ```

4. Generate candidates with `direction="NEUTRAL"` from `generate_candidates()` when posture is NEUTRAL_PREMIUM.

### Adding an earnings calendar

To make Gate 9 functional:

1. In `generate_candidates()`, after building the `TradeCandidate`, set `has_earnings_soon` based on a data feed:
   ```python
   has_earnings = check_earnings_calendar(symbol)  # your implementation
   TradeCandidate(..., has_earnings_soon=has_earnings)
   ```

2. Gate 9 in `qualify_candidate()` is already implemented and will correctly handle `True` (fail), `False` (pass), and `None` (pass/unknown).
