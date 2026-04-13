# Cuttingboard — Trade Qualification

## Overview

Every trade candidate passes through 11 gates in sequence. Gates 1–4 are **hard stops**: failure immediately rejects the symbol with no watchlist eligibility. Gates 5–11 are **soft stops**: exactly one failure puts the symbol on the watchlist; two or more failures reject it.

There is no partial credit. Every gate either passes or fails.

```
Gates 1–4 (HARD):   fail → REJECT immediately, no watchlist
Gates 5–11 (SOFT):  1 miss → WATCHLIST
                   2+ misses → REJECT
```

---

## The 11 Gates

### Gate 1 — REGIME (Hard)

**Rule:** Posture must not be STAY_FLAT.

```python
if regime.posture == STAY_FLAT:
    → REJECT
```

This gate is also checked at the system level in `qualify_all()` before any per-symbol work runs. If posture is STAY_FLAT, the qualification loop short-circuits immediately — no symbols are evaluated, no CHOP symbols are logged from qualification. (CHOP detection in the structure layer still runs independently.)

**Failure message:** `REGIME: posture is STAY_FLAT (regime=NEUTRAL)`

---

### Gate 2 — CONFIDENCE (Hard)

**Rule:** Regime confidence must be ≥ 0.50.

```python
if regime.confidence < 0.50:   # config.MIN_REGIME_CONFIDENCE
    → REJECT
```

This is the minimum signal strength required to consider any trade. Below 0.50, the vote model is essentially split and no directional bias is reliable.

Note: Gate 1 already catches STAY_FLAT posture (which is assigned when confidence < 0.50), so Gate 2 is a belt-and-suspenders check at the per-candidate level. It can fire independently if a candidate reaches `qualify_candidate()` directly.

**Failure message:** `CONFIDENCE: confidence 0.42 < 0.50 minimum`

---

### Gate 3 — DIRECTION (Hard)

**Rule:** Candidate direction must match the regime's expected direction.

```python
expected = direction_for_regime(regime)
# RISK_ON → "LONG", RISK_OFF → "SHORT", NEUTRAL uses net_score, CHAOTIC → None

if expected is not None and candidate.direction != expected:
    → REJECT
```

When `expected` is None (`NEUTRAL` with `net_score = 0`, or `CHAOTIC`), this gate always passes — no directional constraint is imposed.

In practice, candidates are generated with the correct direction by `generate_candidates()`, which already calls `direction_for_regime()`. Gate 3 exists as a validation layer in case candidates are constructed manually or passed in from external sources.

**Failure message:** `DIRECTION: SHORT direction incompatible with RISK_ON regime`

---

### Gate 4 — STRUCTURE (Hard)

**Rule:** Symbol structure must not be CHOP.

```python
if structure.structure == CHOP:
    → REJECT
```

CHOP means EMA alignment is broken or price is outside the tradeable zone relative to the EMAs. There is no setup in a CHOP structure — no level to lean on, no trend to follow.

CHOP symbols are also excluded before qualification in `qualify_all()` (they never become candidates) and logged at that point. Gate 4 handles the case where a candidate is explicitly provided for a CHOP symbol.

**Failure message:** `STRUCTURE: CHOP structure — automatic disqualification`

---

### Gate 5 — STOP_DEFINED (Soft)

**Rule:** Stop price must be defined and must not equal the entry price.

```python
if candidate.stop_price <= 0 or abs(entry - stop) == 0:
    → soft failure
```

This checks that a meaningful stop exists. A stop at zero or at the entry price means there is no defined risk — the position is untradeable from a risk management perspective.

**Failure message:** `STOP_DEFINED: stop price not defined or equals entry`

---

### Gate 6 — STOP_DISTANCE (Soft)

**Rule:** Stop must be ≥ 1% from entry price AND ≥ 0.5× ATR14 (if ATR is available).

```python
stop_pct = risk / entry_price
if stop_pct < 0.01:
    → soft failure: "stop distance {X}% below 1.0% minimum"

if atr14 is available and risk < 0.5 × atr14:
    → soft failure: "stop distance {X} below 0.5× ATR14 ({Y})"
```

**Why both conditions?**
- The 1% floor prevents entering trades where the stop is so tight that normal intraday volatility will trigger it. A 0.5% stop on a $100 stock means a $0.50 move takes you out — not a trade, just noise.
- The 0.5× ATR condition is stronger: it ensures the stop is placed at a level that reflects actual recent price movement. A stop tighter than half the typical daily range has a very high probability of being hit by random fluctuation before the trade has a chance to develop.

When ATR is unavailable (insufficient history), only the 1% check runs. The ATR check is skipped — it does not cause a failure by itself.

**Failure message:** `STOP_DISTANCE: stop distance 0.6% below 1.0% minimum`
or: `STOP_DISTANCE: stop distance 1.20 below 0.5× ATR14 (1.50)`

---

### Gate 7 — RR_RATIO (Soft)

**Rule:** Reward-to-risk ratio must be ≥ 2.0.

```python
risk   = abs(entry_price - stop_price)
reward = abs(target_price - entry_price)
rr     = reward / risk

if rr < 2.0:   # config.MIN_RR_RATIO
    → soft failure
```

An R:R below 2.0 means you need to be right more than 50% of the time just to break even accounting for bid/ask spread and commissions. With options spreads (which have transaction costs on both entry and exit), 2.0 is the minimum viable ratio.

Gate 7 and Gate 6 are the most commonly failing soft gates. A tight stop + distant target will fail Gate 6; a close target + distant stop will fail Gate 7.

**Failure message:** `RR_RATIO: R:R 1.8 below 2.0 minimum`

---

### Gate 8 — MAX_RISK (Soft)

**Rule:** Spread must fit within the $150 target risk budget (at least 1 contract).

```python
spread_cost = spread_width × 100    # options multiplier
max_contracts = floor(150 / spread_cost)

if max_contracts < 1:
    → soft failure
```

`spread_width` is the estimated net debit per share (not the strike distance). `× 100` converts to per-contract cost. The target dollar risk is $150 (`config.TARGET_DOLLAR_RISK`).

| spread_width | spread_cost | max_contracts | dollar_risk |
|-------------|-------------|---------------|-------------|
| $0.50 | $50 | 3 | $150 |
| $0.75 | $75 | 2 | $150 |
| $1.00 | $100 | 1 | $100 |
| $1.50 | $150 | 1 | $150 |
| $2.00 | $200 | 0 | → FAIL |

When the gate passes, `max_contracts` and `dollar_risk` are set on the `QualificationResult` and carried through to the `OptionSetup`. These values represent the maximum size — you should never exceed them.

**Failure message:** `MAX_RISK: 1 contract at $2.00 width = $200 — exceeds $200 maximum`

---

### Gate 9 — EARNINGS (Soft, Fail-Open)

**Rule:** Symbol must not have earnings within 5 calendar days. Unknown = passes.

```python
if candidate.has_earnings_soon is True:
    → soft failure
# None (unknown) or False → PASS
```

This gate is **fail-open**: if earnings data is unavailable (`has_earnings_soon = None`), the gate passes. The system will not block a trade simply because it lacks earnings calendar data.

`has_earnings_soon` is not set automatically by the current system — it defaults to `None` on all generated candidates. This means Gate 9 always passes in the current implementation. It is implemented as a properly guarded soft gate so that if you add an earnings calendar feed, you just need to set `has_earnings_soon=True` on the relevant candidates.

**Failure message:** `EARNINGS: earnings within 5 calendar days`

---

## Outcome Logic

```
Hard gate fails (Gate 1–4):
    qualified=False, watchlist=False
    hard_failure = "{GATE}: {reason}"
    max_contracts = None, dollar_risk = None

All soft gates pass:
    qualified=True, watchlist=False
    hard_failure = None, watchlist_reason = None

Exactly 1 soft gate fails:
    qualified=False, watchlist=True
    watchlist_reason = the single failure reason

2+ soft gates fail:
    qualified=False, watchlist=False
    hard_failure = "N soft gates failed: {reason1}; {reason2}"
```

---

## Position Sizing Formula

```
spread_cost   = spread_width × 100
max_contracts = floor(TARGET_DOLLAR_RISK / spread_cost)
dollar_risk   = max_contracts × spread_cost
```

Where `TARGET_DOLLAR_RISK = 150` (configured in `config.py`).

This is the maximum number of contracts and maximum dollar risk. You can trade fewer contracts if you want to reduce risk, but never more. The `max_contracts` field on `QualificationResult` and `OptionSetup` is the ceiling, not a recommendation.

**Example:** SPY with estimated debit of $1.50/share:
- spread_cost = $1.50 × 100 = $150/contract
- max_contracts = floor(150 / 150) = 1
- dollar_risk = 1 × $150 = $150

**Example:** AAPL with estimated debit of $0.75/share:
- spread_cost = $0.75 × 100 = $75/contract
- max_contracts = floor(150 / 75) = 2
- dollar_risk = 2 × $75 = $150

---

## Worked Examples

### Gate 10 — EXTENSION (Soft)

**Rule:** Price must not be excessively extended relative to EMA21 and ATR14.

```python
extension = abs(entry_price - ema21) / atr14
if extension > 1.5:   # config.EXTENSION_ATR_MULTIPLIER
    → soft failure
```

This gate prevents chasing entries after the move is already stretched. If EMA21 or ATR14 is unavailable, the gate passes fail-open.

**Failure message:** `EXTENSION: price 1.8× ATR from EMA21 (max 1.5×) — entry extended`

---

### Gate 11 — TIME (Soft)

**Rule:** New entries must not be opened after the late-session cutoff.

```python
if current_time_et >= 15:30:   # config.LATE_SESSION_CUTOFF
    → soft failure
```

This gate preserves execution discipline without changing the underlying signal logic.

**Failure message:** `TIME: entry blocked after 3:30 PM ET`

---

### Example A — Fully Qualified Setup (all 11 gates pass)

**Conditions:** RISK_ON regime, AGGRESSIVE_LONG posture, confidence=0.75.
**Symbol:** QQQ, structure=TREND, iv_environment=NORMAL_IV.
**Candidate:** direction=LONG, entry=$480, stop=$475.20 (1% below), target=$489.60 (2× risk), spread_width=$1.50.

| Gate | Check | Result |
|------|-------|--------|
| 1 REGIME | posture=AGGRESSIVE_LONG ≠ STAY_FLAT | ✓ PASS |
| 2 CONFIDENCE | 0.75 ≥ 0.50 | ✓ PASS |
| 3 DIRECTION | LONG = RISK_ON expected LONG | ✓ PASS |
| 4 STRUCTURE | TREND ≠ CHOP | ✓ PASS |
| 5 STOP_DEFINED | stop=475.20 > 0, risk=4.80 > 0 | ✓ PASS |
| 6 STOP_DISTANCE | 4.80/480 = 1.0% ≥ 1%; 4.80 ≥ 0.5×ATR (ATR=7.2, half=3.6) | ✓ PASS |
| 7 RR_RATIO | reward=9.60, risk=4.80, RR=2.0 ≥ 2.0 | ✓ PASS |
| 8 MAX_RISK | spread_cost=$150, max_c=floor(150/150)=1 | ✓ PASS |
| 9 EARNINGS | has_earnings_soon=None → fail-open | ✓ PASS |
| 10 EXTENSION | entry close enough to EMA21 relative to ATR14 | ✓ PASS |
| 11 TIME | run occurs before 3:30 PM ET | ✓ PASS |

**Outcome:** `qualified=True`, max_contracts=1, dollar_risk=$150.

---

### Example B — Watchlist (one soft gate fails)

Same conditions as Example A, but the R:R is marginal:
**Candidate:** entry=$480, stop=$475.20, target=$487.20 (1.5× risk).

| Gate | Check | Result |
|------|-------|--------|
| 1–5 | (same as above) | ✓ PASS |
| 6 STOP_DISTANCE | stop_pct=1.0% ≥ 1%; risk=4.80 ≥ half-ATR 3.6 | ✓ PASS |
| 7 RR_RATIO | reward=7.20, risk=4.80, RR=1.5 < 2.0 | ✗ FAIL |
| 8 MAX_RISK | (computed, max_c=1) | ✓ PASS |
| 9 EARNINGS | None → pass | ✓ PASS |
| 10 EXTENSION | entry close enough to EMA21 relative to ATR14 | ✓ PASS |
| 11 TIME | run occurs before 3:30 PM ET | ✓ PASS |

**Outcome:** `watchlist=True`, `watchlist_reason="R:R 1.5 below 2.0 minimum"`.

This setup will appear in the WATCHLIST section. The target is too close. Wait for QQQ to move further from the entry, or find a higher target level.

---

### Example C — Reject (two soft gates fail)

Same conditions, but with a tight stop AND earnings coming:
**Candidate:** entry=$480, stop=$479.04 (0.2% below), target=$490, spread_width=$0.75. has_earnings_soon=True.

| Gate | Check | Result |
|------|-------|--------|
| 1–4 | (pass) | ✓ PASS |
| 5 STOP_DEFINED | stop > 0, risk > 0 | ✓ PASS |
| 6 STOP_DISTANCE | 0.96/480 = 0.2% < 1.0% | ✗ FAIL |
| 7 RR_RATIO | reward=10, risk=0.96, RR=10.4 ≥ 2.0 | ✓ PASS |
| 8 MAX_RISK | spread_cost=$75, max_c=2 | ✓ PASS |
| 9 EARNINGS | has_earnings_soon=True | ✗ FAIL |
| 10 EXTENSION | entry close enough to EMA21 relative to ATR14 | ✓ PASS |
| 11 TIME | run occurs before 3:30 PM ET | ✓ PASS |

Two soft gate failures → **REJECT**. The hard_failure message will read:
`"2 soft gates failed: stop distance 0.2% below 1.0% minimum; earnings within 5 calendar days"`

---

## What "Watchlist" Actually Means

A watchlist symbol is not a failed trade — it is a **conditional trade**. The single missing gate tells you exactly what needs to change:

| Watchlist reason | What to do |
|-----------------|-----------|
| R:R below minimum | Check back after more price movement; target may be closer to a resistance level |
| Stop distance below 1% | Wait for a wider ATR day or a pullback that gives a cleaner entry |
| Stop below 0.5× ATR14 | Same as above — the current ATR is too large relative to the stop distance |
| Earnings within 5 days | Wait until after the earnings announcement |
| Spread width exceeds budget | Consider a narrower spread if available |

The system does not automatically promote watchlist symbols to trades on the next run. Every run is evaluated fresh. If conditions change and the previously-failing gate now passes, the symbol will qualify.
