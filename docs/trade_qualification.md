# Cuttingboard — Trade Qualification

## Overview

Every trade candidate passes through 11 gates in sequence. Gates 1–4 are **hard stops**: failure immediately rejects the symbol with no watchlist eligibility. Gates 5–11 are **soft stops**: exactly one failure puts the symbol on the watchlist; two or more failures reject it.

There is no partial credit. Every gate either passes or fails.

```
Gates 1–4 (HARD):   fail → REJECT immediately, no watchlist
Gates 5–11 (SOFT):  1 miss → WATCHLIST
                   2+ misses → REJECT
```

The 11 gates above describe the **DIRECT** entry mode — the default path
through `qualify_candidate()`. Two further entry-mode systems exist and are
documented in [Entry Modes](#entry-modes) below: **CONTINUATION** (an
EXPANSION-only breakout path with its own gate sequence in
`_qualify_continuation_candidate()`) and **PULLBACK_IMBALANCE** (an FVG-based
upgrade applied post-hoc to an already-qualified DIRECT result in
`_resolve_entry_mode()`).

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

**Rule:** Stop must be ≥ 1% from entry price (`config.MIN_STOP_PCT = 0.01`) AND ≥ 1.0× ATR14 (`config.STOP_ATR_FLOOR_K = 1.0`, if ATR is available).

```python
stop_pct = risk / entry_price
if stop_pct < config.MIN_STOP_PCT:
    → soft failure: "stop distance {X}% below 1.0% minimum"

if atr14 is available and risk < config.STOP_ATR_FLOOR_K × atr14:
    → soft failure: "stop distance {X} below 1× ATR14 ({Y})"
```

**Why both conditions?**
- The 1% floor prevents entering trades where the stop is so tight that normal intraday volatility will trigger it. A 0.5% stop on a $100 stock means a $0.50 move takes you out — not a trade, just noise.
- The ATR condition is stronger: it ensures the stop sits outside the typical daily range. A stop tighter than one full ATR has a high probability of being hit by random fluctuation before the trade has a chance to develop. (PRD-240 raised this floor from 0.5× to 1.0×; every practitioner convention surveyed by the 2026-07-05 tuning audit starts at ≥ 1×.)

When ATR is unavailable (insufficient history), only the 1% check runs. The ATR check is skipped — it does not cause a failure by itself.

`MIN_STOP_PCT` is also the continuation path's stop floor (see [CONTINUATION](#continuation)) — one shared constant, per PRD-240 R3.

**Failure message:** `STOP_DISTANCE: stop distance 0.6% below 1.0% minimum`
or: `STOP_DISTANCE: stop distance 5.00 below 1× ATR14 (7.20)`

---

### Gate 7 — RR_RATIO (Soft)

**Rule:** Reward-to-risk ratio must meet the regime-tiered minimum, selected by `_min_rr_for_regime()`:

| Regime | Minimum R:R | Constant |
|--------|-------------|----------|
| NEUTRAL | 3.0 | `config.NEUTRAL_RR_RATIO` |
| EXPANSION | 2.0 | `config.EXPANSION_RR_RATIO` |
| all others (RISK_ON / RISK_OFF / CHAOTIC) | 2.0 | `config.MIN_RR_RATIO` |

```python
risk   = abs(entry_price - stop_price)
reward = abs(target_price - entry_price)
rr     = reward / risk

if rr < _min_rr_for_regime(regime):
    → soft failure
```

An R:R below 2.0 means you need to be right more than 50% of the time just to break even accounting for bid/ask spread and commissions. With options spreads (which have transaction costs on both entry and exit), 2.0 is the minimum viable ratio.

**Why the tiers:** NEUTRAL is the low-information regime — a directional trade taken there carries the weakest environmental backing, so it must pay more when right (3.0). EXPANSION previously carried a *discount* (1.5); PRD-240 removed it — the momentum/breakout literature surveyed by the 2026-07-05 tuning audit associates continuation setups with lower win rates needing *higher* R:R, so an unsupported discount was the wrong direction. EXPANSION now matches the default.

The same tier selection is reused by the PULLBACK_IMBALANCE upgrade's R:R re-check (see [Entry Modes](#entry-modes)) and, against a synthetic reward, by the CONTINUATION path — one helper, no silent divergence (PRD-240 R4).

Gate 7 and Gate 6 are the most commonly failing soft gates. A tight stop + distant target will fail Gate 6; a close target + distant stop will fail Gate 7.

**Failure message:** `RR_RATIO: R:R 1.80 below 2.0 minimum` (NEUTRAL appends `(NEUTRAL stricter gate)`)

---

### Gate 8 — MAX_RISK (Soft)

**Rule:** Spread must fit within the $150 target risk budget (at least 1 contract).

```python
spread_cost = spread_width × 100    # options multiplier
max_contracts = floor(150 / spread_cost)

if max_contracts < 1:
    → soft failure
```

`spread_width` is the estimated net debit per share (not the strike distance). `× 100` converts to per-contract cost. The per-trade risk budget is `config.ACCOUNT_EQUITY × config.MAX_RISK_PCT_PER_TRADE × REGIME_RISK_MULTIPLIER[regime]` (PRD-157, 2026-05-24). At default settings (`ACCOUNT_EQUITY=15000`, `MAX_RISK_PCT_PER_TRADE=0.01`) under RISK_ON, the budget is $150.

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
spread_cost      = spread_width × 100
effective_target = ACCOUNT_EQUITY × MAX_RISK_PCT_PER_TRADE × REGIME_RISK_MULTIPLIER[regime]
max_contracts    = floor(effective_target / spread_cost)
dollar_risk      = max_contracts × spread_cost
```

`ACCOUNT_EQUITY` and `MAX_RISK_PCT_PER_TRADE` are manually-maintained static
constants in `config.py` (no broker integration). Defaults are
`ACCOUNT_EQUITY=15000`, `MAX_RISK_PCT_PER_TRADE=0.01`, giving an effective
per-trade risk budget of $150 under RISK_ON. The regime multiplier applies
on top (CHAOTIC=0.0 zeros sizing; NEUTRAL=0.6 halves it). See PRD-157
(2026-05-24) for the migration rationale.

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
if current_time_et >= 15:30:   # config.ENTRY_CUTOFF_ET
    → soft failure
```

This gate preserves execution discipline without changing the underlying signal logic.

**Failure message:** `TIME: entry blocked after 3:30 PM ET`

---

## Entry Modes

`QualificationResult.entry_mode` names which of three entry systems produced
the setup. DIRECT is the default; the other two exist for specific structures.

### DIRECT

The 11-gate sequence above, run by `qualify_candidate()` on a candidate with a
real `target_price` from level analysis. Everything in this document up to
here describes DIRECT.

### CONTINUATION

An **EXPANSION-regime-only** breakout path (`_qualify_continuation_candidate()`),
run inside `qualify_all()` after the DIRECT pass — only when the regime is
EXPANSION, and only for non-CHOP symbols that did not already qualify or
watchlist via DIRECT. It is LONG-only by construction and uses its own gate
sequence — first failure wins, one deterministic rejection reason per candidate:

| # | Check | Constant(s) | Rejection reason |
|---|-------|-------------|------------------|
| 1 | Daily OHLCV + ATR14 present | — | `DATA_INCOMPLETE` |
| 2 | VIX not spiking: `vix_pct_change ≤ +1%` | `CONTINUATION_VIX_SPIKE_BLOCK = 0.01` | `VIX_BLOCKED` |
| 3 | Close clears the prior 5-bar high | `CONTINUATION_BREAKOUT_BARS = 5` | `NO_BREAKOUT` |
| 4 | Close 1 completed bar ago also held above the breakout level | `CONTINUATION_HOLD_CANDLES = 1` | `NO_HOLD_CONFIRMATION` |
| 5 | Last candle range ≥ 0.75× ATR14 AND close in the top quartile of its range (`close_location ≥ 0.75`, PRD-240 R5 — a wick-dominated candle is not momentum) | `CONTINUATION_MOMENTUM_K = 0.75` | `INSUFFICIENT_MOMENTUM` |
| 6 | Entry ≤ 2.5× ATR14 from EMA21 | `CONTINUATION_MAX_EXTENSION_ATR = 2.5` | `EXTENDED_FROM_MEAN` |
| 7 | Stop = the breakout level; risk ≥ 1% of entry | `MIN_STOP_PCT = 0.01` | `STOP_TOO_TIGHT` |
| 8 | Synthetic R:R ≥ 2.0 (see below) | `EXPANSION_RR_RATIO = 2.0` | `RR_BELOW_THRESHOLD` |
| 9 | Before the 3:30 PM ET cutoff | `ENTRY_CUTOFF_ET` | `TIME_BLOCKED` |
| 10 | Sizing fits the equity budget (spread_width = max($0.50, 0.05× ATR14); no regime multiplier — EXPANSION is 1.0) | `ACCOUNT_EQUITY`, `MAX_RISK_PCT_PER_TRADE` | `STOP_TOO_TIGHT` |

**The synthetic reward is a fixed ATR multiple, not a target estimate:**
`reward = CONTINUATION_REWARD_ATR_MULTIPLE × ATR14 = 3.0× ATR14` (PRD-240 R3).
The R:R check therefore functions as a **stop-width ceiling**: with
`EXPANSION_RR_RATIO = 2.0`, a candidate qualifies only when
`risk = entry − breakout_level ≤ 1.5× ATR14`. Combined with check 7, the
qualifying band is `1% of entry ≤ risk ≤ 1.5× ATR14`.

**Deliberate asymmetry vs. Gate 6:** the continuation stop has **no ATR
floor**. The stop anchors to the structural breakout level rather than being
chosen, so the chosen-stop ATR convention does not map — and adding a 1.0×ATR
floor would shrink the band above to ~0.5×ATR wide, a de facto path shutdown.
Retained and documented in-code per PRD-240 R6.

### PULLBACK_IMBALANCE

A Fair Value Gap (FVG) **upgrade applied post-hoc** by `_resolve_entry_mode()`
to a result that has already fully qualified through the DIRECT gates. It
never rescues a failed candidate and never demotes a qualified one — if any
condition below fails, the result simply stays DIRECT.

1. **FVG detection** (`detect_fvg`, last `FVG_LOOKBACK_CANDLES = 6` completed
   daily bars): a displacement candle with body ≥ 1.2× ATR14
   (`FVG_DISPLACEMENT_K`) closing in the outer quartile of its range
   (`close_location ≥ 0.75` LONG / `≤ 0.25` SHORT), leaving a gap
   ≥ 0.3× ATR14 (`FVG_GAP_K`).
2. **Proximity:** current close within 1.5× ATR14 of the zone midpoint
   (`FVG_PROXIMITY_K`); farther and the zone is stale.
3. **Zone R:R re-check:** risk is re-measured from the zone midpoint to the
   zone's far bound (lower bound for LONG, upper bound for SHORT), reward from
   the midpoint to the candidate's real target; the ratio must clear the
   **same regime-tiered minimum as Gate 7** (`_min_rr_for_regime()`, PRD-240 R4).

On upgrade, `entry_mode = PULLBACK_IMBALANCE` and `imbalance_zone` carries the
zone bounds; sizing and all gate results are unchanged from the DIRECT pass.

---

## Worked Examples

### Example A — Fully Qualified Setup (all 11 gates pass)

**Conditions:** RISK_ON regime, AGGRESSIVE_LONG posture, confidence=0.75.
**Symbol:** QQQ, structure=TREND, iv_environment=NORMAL_IV.
**Candidate:** direction=LONG, entry=$480, stop=$472.80 (1.5% below), target=$494.40 (2× risk), spread_width=$1.50.

| Gate | Check | Result |
|------|-------|--------|
| 1 REGIME | posture=AGGRESSIVE_LONG ≠ STAY_FLAT | ✓ PASS |
| 2 CONFIDENCE | 0.75 ≥ 0.50 | ✓ PASS |
| 3 DIRECTION | LONG = RISK_ON expected LONG | ✓ PASS |
| 4 STRUCTURE | TREND ≠ CHOP | ✓ PASS |
| 5 STOP_DEFINED | stop=472.80 > 0, risk=7.20 > 0 | ✓ PASS |
| 6 STOP_DISTANCE | 7.20/480 = 1.5% ≥ 1%; 7.20 ≥ 1×ATR (ATR=7.2) | ✓ PASS |
| 7 RR_RATIO | reward=14.40, risk=7.20, RR=2.0 ≥ 2.0 | ✓ PASS |
| 8 MAX_RISK | spread_cost=$150, max_c=floor(150/150)=1 | ✓ PASS |
| 9 EARNINGS | has_earnings_soon=None → fail-open | ✓ PASS |
| 10 EXTENSION | entry close enough to EMA21 relative to ATR14 | ✓ PASS |
| 11 TIME | run occurs before 3:30 PM ET | ✓ PASS |

**Outcome:** `qualified=True`, max_contracts=1, dollar_risk=$150.

---

### Example B — Watchlist (one soft gate fails)

Same conditions as Example A, but the R:R is marginal:
**Candidate:** entry=$480, stop=$472.80, target=$490.80 (1.5× risk).

| Gate | Check | Result |
|------|-------|--------|
| 1–5 | (same as above) | ✓ PASS |
| 6 STOP_DISTANCE | stop_pct=1.5% ≥ 1%; risk=7.20 ≥ 1×ATR 7.2 | ✓ PASS |
| 7 RR_RATIO | reward=10.80, risk=7.20, RR=1.5 < 2.0 | ✗ FAIL |
| 8 MAX_RISK | (computed, max_c=1) | ✓ PASS |
| 9 EARNINGS | None → pass | ✓ PASS |
| 10 EXTENSION | entry close enough to EMA21 relative to ATR14 | ✓ PASS |
| 11 TIME | run occurs before 3:30 PM ET | ✓ PASS |

**Outcome:** `watchlist=True`, `watchlist_reason="R:R 1.50 below 2.0 minimum"`.

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
| Stop below 1× ATR14 | Same as above — the current ATR is too large relative to the stop distance |
| Earnings within 5 days | Wait until after the earnings announcement |
| Spread width exceeds budget | Consider a narrower spread if available |

The system does not automatically promote watchlist symbols to trades on the next run. Every run is evaluated fresh. If conditions change and the previously-failing gate now passes, the symbol will qualify.
