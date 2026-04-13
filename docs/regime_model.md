# Cuttingboard — Regime Model

## Overview

The regime engine translates current market conditions into a single **regime** (directional bias) and **posture** (how aggressively to act). It uses an 8-input vote model — each input casts one vote — to produce a net score, then maps that score to a regime label and confidence value.

The regime is computed fresh on every run. It has no memory of yesterday's regime. A single large VIX move can flip the regime in one interval.

`NEUTRAL` is an active regime, not a pass-through state. It allows selective trades only with defined risk and `R:R >= 3.0` when posture resolves to `NEUTRAL_PREMIUM`.

`TRANSITION` remains as a legacy constant in code for compatibility, but the engine does not return it.

---

## The 8 Inputs

| # | Input | Instrument | Vote Logic | RISK_ON when | RISK_OFF when |
|---|-------|-----------|------------|--------------|---------------|
| 1 | SPY pct_change | S&P 500 ETF | Higher = risk-on | > +0.3% | < −0.3% |
| 2 | QQQ pct_change | Nasdaq ETF | Higher = risk-on | > +0.3% | < −0.3% |
| 3 | IWM pct_change | Russell 2000 ETF | Higher = risk-on | > +0.4% | < −0.4% |
| 4 | VIX level | Volatility Index | Lower = risk-on | < 18 | > 25 |
| 5 | VIX pct_change | VIX single-interval move | Lower = risk-on | < −3% | > +5% |
| 6 | DXY pct_change | US Dollar Index | Lower = risk-on | < −0.2% | > +0.3% |
| 7 | TNX pct_change | 10-yr yield | Lower = risk-on | < −0.5% | > +0.8% |
| 8 | BTC pct_change | Bitcoin | Higher = risk-on | > +1.5% | < −2.0% |

Between the thresholds, the input votes **NEUTRAL**.

**Why these thresholds?** Small price moves are noise. The thresholds are set to filter out sub-signal moves:
- Equities (SPY/QQQ): ±0.3% filters out the typical ±0.1-0.2% intraday drift
- IWM: slightly higher at ±0.4% because small-cap is noisier
- VIX level: 18 and 25 are conventional "calm" and "elevated" breakpoints
- VIX pct_change: −3% for falling VIX (good), +5% for rising VIX (bad, asymmetric)
- DXY: ±0.2-0.3% because FX moves slowly
- TNX: −0.5% / +0.8% captures meaningful yield moves without reacting to basis-point noise
- BTC: +1.5% / −2.0% reflects that crypto is noisier and only provides signal at larger moves

---

## Vote Counting

```
net_score  = risk_on_votes − risk_off_votes
total_votes = risk_on_votes + risk_off_votes + neutral_votes
confidence  = abs(net_score) / total_votes
```

Range: `net_score` ∈ [−8, +8]. `confidence` ∈ [0.0, 1.0].

If a symbol is missing from `valid_quotes` (failed validation), its vote is **skipped** — not counted as NEUTRAL. `total_votes` reflects only cast votes, so confidence degrades gracefully when data is missing.

**Example:** If IWM fails validation, 7 votes are cast. net_score = 6, confidence = 6/7 = 0.857. The missing vote doesn't penalize confidence — it just narrows the denominator.

---

## CHAOTIC Override

Before any vote counting, the engine checks VIX pct_change:

```python
if vix_pct_change > 0.15:   # VIX spiked > 15% in one interval
    regime = CHAOTIC
    posture = STAY_FLAT
```

This fires first — regardless of vote counts. A 15% single-interval VIX spike indicates a flash crash or gap event. No trade is safe in these conditions.

When CHAOTIC fires, the vote breakdown is still computed and stored in `RegimeState.vote_breakdown` for audit purposes, but the regime is locked to CHAOTIC.

---

## Regime Classification

After CHAOTIC is checked:

```
net_score ≥ 4  AND  confidence ≥ 0.60  →  RISK_ON
net_score ≥ 2                           →  RISK_ON
net_score ≤ −4 AND  confidence ≥ 0.60  →  RISK_OFF
net_score ≤ −2                          →  RISK_OFF
otherwise                               →  NEUTRAL
```

The two-tier threshold (score alone vs. score + confidence) means:
- A strong, unanimous signal (≥4 votes one way, high confidence) → clear regime
- A moderate signal (≥2 votes one way) → regime even without high confidence
- A split signal (±1 or 0) → NEUTRAL regardless

---

## Posture Mapping

| Regime | Condition | Posture |
|--------|-----------|---------|
| Any | `confidence < 0.50` | `STAY_FLAT` |
| CHAOTIC | Any | `STAY_FLAT` |
| RISK_ON | `confidence ≥ 0.75` | `AGGRESSIVE_LONG` |
| RISK_ON | `0.55 ≤ confidence < 0.75` | `CONTROLLED_LONG` |
| RISK_ON | `confidence < 0.55` | `STAY_FLAT` |
| RISK_OFF | `confidence ≥ 0.55` | `DEFENSIVE_SHORT` |
| RISK_OFF | `confidence < 0.55` | `STAY_FLAT` |
| NEUTRAL | `VIX 18–25` | `NEUTRAL_PREMIUM` |
| NEUTRAL | `VIX < 18 or > 25 or unknown` | `STAY_FLAT` |

**The minimum confidence floor is 0.50.** Below this, the signal-to-noise ratio is too low to trade regardless of regime. A confidence of 0.50 on 8 votes means only 2 more votes one way than the other — a very weak signal.

**NEUTRAL_PREMIUM** is the posture that allows selective trading during NEUTRAL. It requires VIX to be in the 18–25 range. Direction comes from `net_score`: positive is LONG, negative is SHORT, zero means no trade. NEUTRAL + VIX 18–25 resolves to `NEUTRAL_PREMIUM`; NEUTRAL + VIX outside that band resolves to `STAY_FLAT`. NEUTRAL trades also use the stricter `R:R >= 3.0` rule.

---

## How Confidence Behaves at Different Score Levels

| net_score | total_votes | confidence | Regime |
|-----------|-------------|------------|--------|
| +6 | 8 | 0.75 | RISK_ON + AGGRESSIVE_LONG |
| +5 | 8 | 0.625 | RISK_ON + CONTROLLED_LONG |
| +4 | 8 | 0.50 | RISK_ON + STAY_FLAT (conf < 0.55) |
| +3 | 7 | 0.43 | RISK_ON + STAY_FLAT |
| +2 | 6 | 0.33 | RISK_ON + STAY_FLAT |
| +1 | 5 | 0.20 | NEUTRAL + STAY_FLAT |
| 0 | 4 | 0.00 | NEUTRAL + STAY_FLAT |
| −2 | 8 | 0.25 | RISK_OFF + STAY_FLAT |
| −4 | 7 | 0.57 | RISK_OFF + DEFENSIVE_SHORT |
| −6 | 8 | 0.75 | RISK_OFF + DEFENSIVE_SHORT |

**Key insight:** The regime can be RISK_ON with a STAY_FLAT posture. This happens when the directional signal is weak (net_score = +2 or +3) but not unanimous enough to justify trading. This is a feature, not a bug — it prevents trading on ambiguous signals.

---

## Worked Examples

### Example 1: Strong Bull Day

Market is up broadly: SPY +0.8%, QQQ +1.1%, IWM +0.6%. VIX falls to 13 from 14 (−7%). Dollar down 0.3%. Yields flat at +0.2%. BTC +2%.

| Input | Value | Vote |
|-------|-------|------|
| SPY pct_change | +0.008 | RISK_ON |
| QQQ pct_change | +0.011 | RISK_ON |
| IWM pct_change | +0.006 | RISK_ON |
| VIX level | 13.0 | RISK_ON (< 18) |
| VIX pct_change | −0.07 | RISK_ON (< −0.03) |
| DXY pct_change | −0.003 | RISK_ON (< −0.002) |
| TNX pct_change | +0.002 | NEUTRAL |
| BTC pct_change | +0.02 | RISK_ON (> 0.015) |

Result: risk_on=7, risk_off=0, neutral=1, total=8, net=+7, confidence=7/8=0.875
Regime: RISK_ON / AGGRESSIVE_LONG ✓

---

### Example 2: Market Selloff

SPY −1.2%, QQQ −1.5%, IWM −0.8%. VIX spikes to 28 from 21 (+33%). Dollar up 0.4%. Yields up 1.2%. BTC −2.5%.

CHAOTIC check: VIX pct_change = +0.33 > 0.15 → **CHAOTIC override fires immediately.**
Regime: CHAOTIC / STAY_FLAT. Vote counting still runs for the audit record but doesn't change the outcome.

---

### Example 3: Mixed Signal (NEUTRAL)

SPY +0.1%, QQQ +0.2%, IWM −0.1%. VIX flat at 20. DXY flat. TNX flat. BTC +0.5%.

| Input | Value | Vote |
|-------|-------|------|
| SPY pct_change | +0.001 | NEUTRAL |
| QQQ pct_change | +0.002 | NEUTRAL |
| IWM pct_change | −0.001 | NEUTRAL |
| VIX level | 20.0 | NEUTRAL (between 18 and 25) |
| VIX pct_change | 0.00 | NEUTRAL |
| DXY pct_change | 0.001 | NEUTRAL |
| TNX pct_change | 0.002 | NEUTRAL |
| BTC pct_change | +0.005 | NEUTRAL |

Result: risk_on=0, risk_off=0, neutral=8, total=8, net=0, confidence=0.00
Regime: NEUTRAL / STAY_FLAT. VIX is 20, which is in the 18–25 range, so NEUTRAL_PREMIUM would apply if confidence were high enough. With confidence at 0.00, posture correctly remains STAY_FLAT.

---

### Example 4: Moderate Bull with Low Confidence

SPY +0.4%, QQQ +0.5%, IWM +0.3%. VIX at 19 (stable). DXY down 0.1%. TNX up 0.3%. BTC up 0.8%.

| Input | Value | Vote |
|-------|-------|------|
| SPY pct_change | +0.004 | RISK_ON |
| QQQ pct_change | +0.005 | RISK_ON |
| IWM pct_change | +0.003 | NEUTRAL (< 0.004 threshold) |
| VIX level | 19.0 | NEUTRAL (between 18 and 25) |
| VIX pct_change | 0.00 | NEUTRAL |
| DXY pct_change | −0.001 | NEUTRAL (−0.001 > −0.002 threshold) |
| TNX pct_change | +0.003 | NEUTRAL (< 0.008 threshold) |
| BTC pct_change | +0.008 | NEUTRAL (< 0.015 threshold) |

Result: risk_on=2, risk_off=0, neutral=6, total=8, net=+2, confidence=2/8=0.25
Regime: RISK_ON (net ≥ 2) / **STAY_FLAT** (confidence 0.25 < 0.55)

This is an important pattern: technically RISK_ON by vote count, but the signal is weak. The system correctly produces NO TRADE. A human trader might feel like conditions are "pretty good" and enter — the system correctly identifies this as insufficient signal.

---

## Recalibrating Thresholds

Thresholds should be reviewed if you see systematic issues:

**Too many STAY_FLAT days in clearly trending markets:**
- Lower the RISK_ON confidence thresholds in `_determine_posture()`
- Or lower the vote thresholds in `_classify_regime()` (e.g., net ≥ 1 instead of ≥ 2)

**Too many trades in choppy, ranging markets:**
- Raise the confidence minimum in `_determine_posture()` (e.g., CONTROLLED_LONG requires 0.65 instead of 0.55)

**VIX votes firing too often/rarely:**
- Adjust `risk_on_lt=18` and `risk_off_gt=25` in the `_vote_lvl_low()` call in `compute_regime()`

**CHAOTIC fires too easily:**
- Raise `VIX_CHAOTIC_SPIKE` in `config.py` (default 0.15)

All thresholds except `VIX_CHAOTIC_SPIKE` are hardcoded in `regime.py` because they are tightly coupled to the specific vote inputs. If you find yourself changing them often, they should be moved to `config.py`.

The key file to edit: `cuttingboard/regime.py`:
- Vote helper calls in `compute_regime()` → adjust per-input thresholds
- `_classify_regime()` → adjust net_score and confidence thresholds
- `_determine_posture()` → adjust confidence gates per regime
