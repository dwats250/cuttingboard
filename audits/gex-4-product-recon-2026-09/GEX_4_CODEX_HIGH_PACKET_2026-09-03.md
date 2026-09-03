# GEX-4 CODEX HIGH PACKET - quantitative / semantic falsification

Frozen 2026-09-03 against main a76e7a4. Purpose: falsify the proposed GEX-4
strike ladder (net + gross per 25-point bin) on arithmetic, aggregation,
labeling and model-honesty grounds. NOT a code review; no code exists. Do not
explore the repo; everything needed is here. Report REQUIRED findings (would
block build) separately from RECOMMENDED ones. Reasoning effort: HIGH.

## 1. Current producer (tools/gex_snapshot.py, PRD-306/307, unchanged by GEX-4)

Endpoint: one keyless GET https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json
Provider fields used: payload.timestamp ("YYYY-MM-DD HH:MM:SS", read as UTC),
data.current_price (spot; SPX cash index level), data.options[i].option (OCC
symbol), .gamma (Cboe model gamma, per share), .open_interest. Nothing else.

Per-contract admissibility, first-failure order: keys option/gamma/open_interest
present -> OCC regex ^([A-Z]+)(\d{6})([CP])(\d{8})$ -> root in {SPX, SPXW} ->
expiry parses as a calendar date -> gamma finite, non-bool, >= 0 -> OI finite,
non-bool, >= 0, integer-valued (2960.0 admitted, 2.5 rejected). Strike =
digits/1000. Zero included -> fail loud, no artifact.

Formula per contract: gex = s * gamma * OI * 100 * spot^2 * 0.01, s = +1 call,
-1 put. Units: USD gamma notional per 1% SPX move.
Sign convention (configured, INFERRED class): "calls:+1 / puts:-1 -- assumed
dealer-long-call/short-put positioning; descriptive assumption, not measured".
Model label: "greeks Cboe-model-computed; GEX derived-of-model".

SPX/SPXW: both roots admitted and summed into the same strike key; nothing
distinguishes them except the 0DTE per_root split. All expirations are summed
into one per-strike value. 0DTE: observation date = feed timestamp converted
to America/New_York .date(); share = sum |gex| over contracts with expiry ==
that date / sum |gex| over all included; stated caveat: AM-settled SPX vs
PM-settled SPXW settlement timing is NOT modeled.

Current serialized outputs: gex_total_1pct_usd (sum of all per-contract gex);
call_wall = argmax over strikes of call sum (lowest strike on ties, null if
max == 0); put_wall = argmax of |put sum|; dominant_net_gamma = argmax of
|call sum + put sum|; zero_dte {share, numerators, per_root}; coverage counts;
provenance lists; spot; timestamps. Nothing per strike survives.

Consumer (gex_card.py): renders only if schema_version == 1, source and
data_delay strings match, spot > 0, fetched_at within 24h and not > 5 min
future, dominant available; rows Net / Dominant / Call wall / Put wall / 0DTE
with distance % from spot; footnote "* net is signed under a configured
positioning assumption; positioning is not measured". Forbidden-vocabulary test
already bans pin, magnet, support, resistance, short/long gamma, regime,
tracks spot, at spot, max pain, "dealers are short".

## 2. Proposed change

Producer adds one additive top-level field (schema_version stays 1):
```
"by_strike": {"strike": [K ascending, unique, one per strike with >= 1 included contract],
              "call_gex_1pct_usd": [sum of gex over calls at K, >= 0],
              "put_gex_1pct_usd":  [sum of gex over puts at K, <= 0]}
```
These are the producer's existing in-memory dicts call_by_strike / put_by_strike
serialized in sorted order; no new arithmetic. Invariants intended as tests:
sum(call)+sum(put) == gex_total_1pct_usd (isclose or exact if the total is
recomputed from sorted arrays); argmax(call) == call_wall.strike; argmax|put|
== put_wall.strike; argmax|call+put| == dominant_net_gamma.strike; strikes
strictly ascending; provenance.derived gains "by_strike"; no forbidden raw keys;
columnar so "no list of objects" stays true.

Consumer adds, when the block is present and valid (else the card is unchanged):
- bin(K) = floor((K + 12.5)/25) * 25; per bin: call_b = sum call, put_b = sum
  put (<= 0), net_b = call_b + put_b, gross_b = call_b + |put_b|.
- center = bin(spot); window = 31 bins center +/- 15*25, all drawn.
- beyond-window: bins with gross_b >= 0.02 * chain gross, listed as text
  ascending (cap 6, "+N more"); chain gross = sum over all K of call + |put|.
- bar scale: 112 SVG units per max over window of max(call_b, |put_b|).
- ladder row: strike | markers C/P/D (bins containing call_wall, put_wall,
  dominant strikes) | gray rect from -|put_b| to +call_b | blue rect 0..net_b
  if net_b > 0, red rect net_b..0 if net_b < 0 | net_b in $B.
- dashed spot line at exact spot, label "SPX <spot>".
- new kv row "Gross <chain gross>B  <n>% within window".
- `<details>` "strike bins by gross": top 8 window bins by gross_b: bin, dist
  %, call-side, put-side, net.
- legend: "31 x 25-pt strike bins around SPX spot; all expirations; SPX+SPXW."
  and "* net is signed under a configured positioning assumption (calls +1 /
  puts -1); positioning is not measured. gray = call-side + put-side gross,
  no sign assumption." Column headers "put-side <", "> call-side".
- tooltip (SVG title): "<bin>: net <x>B (call-side <a>B, put-side <b>B)".
- freshness/suppression identical to the card (24h on fetched_at). Ladder
  omitted if window gross == 0. Zero-denominator guard on the 2% rule.
- No renderer or CSS change; SVG is attribute-styled inside the existing
  fragment; no JS.

## 3. Real rows (provider excerpt, 2026-09-03 22:42:44 UTC feed, spot 7747.71)

| option | OI | gamma | gex (USD/1%) |
|---|---|---|---|
| SPX260918C08000000 | 273400 | 0.0007 | +11.49e9 |
| SPX260918P08000000 | 263216 | 0.0007 | -11.06e9 |
| SPXW260918C08000000 | 3970 | 0.0007 | +0.167e9 |
| SPXW260918P08000000 | 235 | 0.0007 | -0.010e9 |
| SPXW260903C07750000 | 3813 | 0.0331 | +7.58e9 (expired 0DTE, post-close feed) |
| SPXW260903P07750000 | 873 | 0.11 | -5.76e9 (expired 0DTE, post-close feed) |

(gex = s * gamma * OI * 100 * 7747.71^2 * 0.01; 7747.71^2*1 = 60,027,010.)

## 4. Resulting per-strike facts (all expirations)

chain net +80.4B; chain gross 595.5B; |net|/gross 0.135; 809 strikes.

| strike | dist | call-side | put-side | net | gross |
|---|---|---|---|---|---|
| 8000 | +3.26% | +38.06B | -32.94B | +5.12B | 71.00B |
| 7750 | +0.03% | +19.31B | -13.56B | +5.75B | 32.87B |
| 7700 | -0.62% | +13.32B | -14.23B | -0.92B | 27.55B |
| 7000 | -9.65% | +12.37B | -13.87B | -1.50B | 26.23B |
| 7800 | +0.67% | +16.56B | -7.05B | +9.51B | 23.61B |
| 7600 | -1.91% | +8.74B | -10.68B | -1.93B | 19.42B |
| 7900 | +1.97% | +8.76B | -1.21B | +7.55B | 9.98B |
| 7825 | +1.00% | +7.99B | -1.02B | +6.98B | 9.01B |

Producer outputs on this chain: call_wall 8000 (+38.06B), put_wall 8000
(-32.94B), dominant 7800 (+9.51B), 0DTE share 0.025.

## 5. Resulting profile (31 bins, center 7750, window 7375..8125; 80% of chain gross)

| bin | dist | call_b | put_b | net_b | gross_b |
|---|---|---|---|---|---|
| 8125 | +4.87% | +2.89 | -0.06 | +2.83 | 2.96 |
| 8100 | +4.55% | +6.90 | -0.34 | +6.56 | 7.24 |
| 8075 | +4.22% | +2.49 | -0.10 | +2.38 | 2.59 |
| 8050 | +3.90% | +6.40 | -0.19 | +6.21 | 6.60 |
| 8025 | +3.58% | +2.12 | -0.10 | +2.01 | 2.22 |
| 8000 | +3.26% | +39.58 | -32.99 | +6.60 | 72.57 |  C P
| 7975 | +2.93% | +2.11 | -0.18 | +1.93 | 2.29 |
| 7950 | +2.61% | +4.70 | -0.32 | +4.38 | 5.02 |
| 7925 | +2.29% | +2.75 | -0.26 | +2.49 | 3.01 |
| 7900 | +1.97% | +10.87 | -1.30 | +9.57 | 12.17 |
| 7875 | +1.64% | +4.51 | -0.43 | +4.08 | 4.94 |
| 7850 | +1.32% | +8.36 | -1.16 | +7.20 | 9.53 |
| 7825 | +1.00% | +13.30 | -2.69 | +10.62 | 15.99 |
| 7800 | +0.67% | +24.77 | -9.64 | +15.13 | 34.41 |  D
| 7775 | +0.35% | +17.53 | -9.01 | +8.52 | 26.54 |
| 7750 | +0.03% | +28.47 | -19.06 | +9.40 | 47.53 |  <- spot 7747.71
| 7725 | -0.29% | +13.04 | -8.80 | +4.24 | 21.84 |
| 7700 | -0.62% | +19.78 | -19.75 | +0.03 | 39.53 |
| 7675 | -0.94% | +10.16 | -10.35 | -0.19 | 20.51 |
| 7650 | -1.26% | +7.87 | -11.38 | -3.51 | 19.25 |
| 7625 | -1.58% | +4.24 | -6.54 | -2.29 | 10.78 |
| 7600 | -1.91% | +11.83 | -15.02 | -3.18 | 26.85 |
| 7575 | -2.23% | +3.80 | -5.84 | -2.04 | 9.64 |
| 7550 | -2.55% | +6.45 | -9.83 | -3.38 | 16.28 |
| 7525 | -2.87% | +2.57 | -4.05 | -1.48 | 6.63 |
| 7500 | -3.20% | +7.78 | -12.77 | -4.99 | 20.55 |
| 7475 | -3.52% | +1.95 | -3.06 | -1.12 | 5.01 |
| 7450 | -3.84% | +4.36 | -6.18 | -1.82 | 10.55 |
| 7425 | -4.17% | +1.32 | -2.35 | -1.03 | 3.67 |
| 7400 | -4.49% | +3.73 | -6.40 | -2.67 | 10.12 |
| 7375 | -4.81% | +0.51 | -1.45 | -0.94 | 1.96 |
beyond window: 7000 (-9.7%) gross 26.4B net -1.7B. ($B throughout.)

Per-expiry (whole chain, by gross): 2026-09-18 35.6%, 2026-12-18 8.9%,
2026-10-16 8.8%, 2026-09-04 5.6%, 2026-12-31 4.6%, 2026-09-30 4.3%; 0DTE
(2026-09-03, already expired at feed time) 2.5%, 504 contracts.

## 6. Known model limitations (already acknowledged, to be carried into copy)

Greeks are Cboe model outputs (~15 min delayed); OI is prior-close, so 0DTE
positions opened intraday are invisible and expiring ones are counted until the
feed drops them (post-close feeds on expiry days still carry them with
degenerate gammas); sign is a uniform assumption; a same-strike call/put pair
nets to ~0 whether it is a box (true zero gamma) or two same-sign positions
(not zero); SPX and SPXW are summed; AM/PM settlement not modeled; all
expirations summed; bins hide 5-point detail; spot is the cash index at feed
time, not SPY.

## 7. Forbidden claims (must not appear or be implied)

gamma flip, zero gamma, flip, long/short gamma, dealer long/short, support,
resistance, magnet, pin, pinning, expected move, volatility suppression or
expansion, acceleration or reversal zone, price target, bullish/bearish,
"dealers are", hedging pressure, tracks spot, at spot, max pain, regime, any
SPY price or SPY-mapped strike, any drawn line where net changes sign, any
per-expiry claim, relative freshness ("ago").

## 8. Questions to attack (answer each with CONFIRMED / FALSIFIED / NARROWED + evidence)

Q1. Does the proposed profile faithfully represent the arithmetic? Check the
bin function on 5-point strikes, the sign of put_b, the reconciliation
invariants, float-sum order between the sorted arrays and the producer's
dict-order total, and whether serializing every strike (809, including zero
gross) versus nonzero-only (669) changes any invariant.
Q2. Does the gross overlay or the net bar obscure economically meaningful
cancellation, or manufacture it? Use the 8000 and 7700 rows. Is "wide gray,
thin net" the right honest encoding, or does gross overstate box/financing
paper so badly that it misleads more than net-only hides?
Q3. Does anything in the visual (blue right / red left, spot line, C/P/D
markers, column headers) imply measured dealer positioning? Is "call-side /
put-side" itself a positioning claim?
Q4. Is combining all expirations into one bin misleading, given 35.6% of gross
is one monthly expiry and 0DTE gammas are degenerate post-close? Is the
existing caveat sufficient copy, or is the aggregate profile dishonest without
an expiry split?
Q5. Is summing SPX and SPXW at the same strike defensible under the existing
model (both cash-settled on SPX, AM vs PM)? Is there a strike-alignment or
settlement-date reason the sum is wrong for a ladder when it was acceptable
for a single total?
Q6. Is the selection rule (fixed 31 x 25-pt bins around bin(spot), outliers
>= 2% chain gross listed) biased or structurally lossy? Attack: the 2%
threshold, the fixed bin count as SPX drifts, the floor-based bin function,
window re-centring between hourly runs (ladder appears to "move"), the cap of
6 outliers, and whether 20% of gross summarized as one percentage is honest.
Q7. Are any proposed labels stronger than the data? Attack "Gross",
"call-side", "put-side", "largest |net| strike", "within window", the C/P/D
markers inheriting the "wall" rows, and the tooltip wording.
Q8. Is any displayed relationship a visual coincidence? E.g. the spot line
sitting inside the widest bin (7750) - is that a property of the data or of
centring the window on spot and using 25-point bins (strike listing density is
highest at the money)? Does the bar scale (max side in window) create a false
sense of symmetry?
Q9. Does the profile introduce a new model not acknowledged? Candidates:
binning (a new aggregation), gross (a new quantity with no sign assumption but
a positioning-free reading that may itself be a claim), the 2% outlier rule,
the additive schema with schema_version unchanged (should it be 2?).
Q10. Strongest reason NOT to ship: state it and whether the proposal survives.

Also flag anything the packet itself gets wrong.
