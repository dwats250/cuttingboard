# Trade Qualification — Tuning Audit

**Date:** 2026-07-05
**Reviewed commit:** `d5071302a3aa527a11a2e3274ba8157a4a245a3d`
**Scope:** `cuttingboard/qualification.py`, `cuttingboard/config.py`, plus the
regime/derived/structure inputs those gates read. Read-only — no code, config,
or PRD changes made. This report feeds a human PRD decision; it is not itself
a PRD.

**Out of scope (per charge, not analyzed):** Gate 5 (stop defined), Gate 8
(sizing/budget), Gate 11 (3:30 PM cutoff). No algorithm/ML/structural
recommendations are made — findings are limited to threshold values and one
wiring/consistency observation directly tied to an in-scope threshold.

---

## 0. System-shape confirmation (read against source, not the prompt's summary)

- **11 gates, not 9** — confirmed directly in `qualification.py`. The
  module docstring (`qualification.py:4`), `HARD_GATES`/`SOFT_GATES` set
  literals (`qualification.py:53-55`, 4 + 7 = 11), and
  `qualify_candidate`'s docstring (`qualification.py:303`) all say 11. **The
  "docstring says 9" premise in the audit brief is stale** — it was true
  before PRD-231 (`docs/PRD_REGISTRY.md:251`, status COMPLETE), which fixed
  exactly this drift in `qualification.py`, `docs/trade_qualification.md`,
  and `output.py`. See §6 for where the "9 gates" claim is *still* alive
  elsewhere in the docs tree (PRD-231 did not sweep every file).
- **HARD gates 1–4 / SOFT gates 5–11, one-miss-watchlist / two-miss-reject** —
  confirmed exactly as summarized, in `qualify_candidate` (`qualification.py:296-524`).
- **Two 1% stop floors, exact locations:**
  - Gate 6 (DIRECT/base path): `qualification.py:375` — `if stop_pct < 0.01:`
  - Continuation path: `qualification.py:669` — `min_risk = entry_price * 0.01`
  Both are bare float literals, not `config.*` references — confirmed
  outside `config.py`. They currently carry the *same* value (0.01) but are
  two independent literals with no shared source; a future edit to one will
  not touch the other. Noted in §4.
- **Three entry-mode systems confirmed distinct:** DIRECT (`qualify_candidate`,
  real `target_price`), CONTINUATION (`_qualify_continuation_candidate`,
  EXPANSION-only, synthetic reward), and PULLBACK_IMBALANCE (an upgrade
  applied post-hoc to an already-qualified DIRECT result via
  `_resolve_entry_mode`, `qualification.py:730-766`, gated by FVG detection).
  Confirmed as summarized.

---

## 1. Regime confidence floor — `MIN_REGIME_CONFIDENCE`

**Current value:** `0.50` — `config.py:62`
**Consumed at:** Gate 2, `qualification.py:327` (`if regime.confidence < config.MIN_REGIME_CONFIDENCE`);
also `qualification.py:722` (`_check_regime_gates`, the system-level short-circuit)
and `regime.py:310` (`_determine_posture`'s own floor check).

**Finding: the "single floor across all regimes" premise is true in the
config file but not in the live decision path — the floor is regime-dependent
in practice, just not through a second named constant.**

Tracing where confidence actually binds, by regime:

- **CHAOTIC** — `regime.py:310` forces `STAY_FLAT` unconditionally
  (`regime == CHAOTIC or confidence < floor`); the confidence *value* is
  irrelevant here regardless of what it is. Floor is moot.
- **EXPANSION** — `regime.py:139-154` returns `confidence=1.0` as a hardcoded
  literal, bypassing `_determine_posture` (and thus the floor check)
  entirely. `1.0 < 0.50` can never be true. Floor is vacuous — EXPANSION's
  real gating happens upstream in `detect_expansion_regime`'s four structural
  conditions (breadth, leadership, VIX, index alignment), not via any
  confidence score.
- **RISK_ON / RISK_OFF** — `regime.py:313-323`: posture is `STAY_FLAT` for
  confidence in `[0.50, 0.55)`, and only above 0.55 does a tradeable posture
  (`CONTROLLED_LONG`/`DEFENSIVE_SHORT`, then `AGGRESSIVE_LONG` at ≥0.75)
  emerge. Since Gate 1 (`posture == STAY_FLAT`) is checked *before* Gate 2
  (`qualification.py:317-334`), a RISK_ON/RISK_OFF candidate with confidence
  in `[0.50, 0.55)` is already rejected at Gate 1 for every production path.
  Gate 2's literal `0.50` comparison never fires as the deciding factor for
  these two regimes — it is dead-but-harmless, exactly as
  `docs/trade_qualification.md:45` already documents ("belt-and-suspenders...
  It can fire independently if a candidate reaches `qualify_candidate()`
  directly" — true only for the direct-call/test path, not the
  `qualify_all()` production path, which always runs Gate 1's system-level
  twin first, `qualification.py:718-727`).
- **NEUTRAL** — `regime.py:325-330`: posture logic branches on **VIX level**,
  not on a second confidence tier. `0.50` is therefore the *only* confidence
  gate NEUTRAL ever passes through, and it is a real, live-firing constraint
  for that regime — not belt-and-suspenders.

**Net:** the codebase already has an effectively regime-specific confidence
floor — it's just implemented as a *side effect* of the posture tiers in
`regime.py` (0.55 / 0.75) rather than as an intentional, named per-regime
config knob. `MIN_REGIME_CONFIDENCE=0.50` as a standalone literal is
functionally a **NEUTRAL-only threshold** in production. If it is retuned in
isolation without also considering `regime.py`'s 0.55/0.75 tiers, only
NEUTRAL trade frequency is actually affected.

**SSRN grounding:** no paper was found that validates `0.50` as a calibrated
cutoff for this vote-count confidence formula (`abs(net_score)/total_votes`)
— it does not appear to derive from a specific study. The regime-switching
literature searched (Dai/Zhang/Zhu on trend-following under regime
switching, SSRN 1762118; Shu/Yu/Mulvey's statistical jump-model approach,
SSRN 4719989) treats "how confident before acting" as an optimization
problem solved per application (threshold curves, cross-validated jump
penalties) rather than a single fixed constant — and in at least one applied
construction, different regime dimensions get different confidence bars.
This is directionally consistent with what the code already does
de facto (§ above) — it argues against literally reusing one constant across
regimes if the goal is a principled design, even though the current
*behavior* already differs by regime through the posture layer.

**Verdict:** leave the `0.50` literal as-is; **it is not the four-regime
universal floor the audit brief assumes it to be**, so there is no live
"single floor across RISK_ON/OFF/NEUTRAL/EXPANSION" problem to fix by
splitting it into four constants — three of those four regimes already get a
different effective floor via `regime.py`, or don't use one at all. The one
real design question is narrower: **is 0.50 the right binding floor for
NEUTRAL specifically**, since that's the only regime where the literal does
real work. No literature basis found either way for that narrower question.
**Confidence: medium** (the tracing is exact against source; the "what value
should NEUTRAL's floor be" question itself has no empirical anchor either
direction).

---

## 2. Direction alignment — NEUTRAL `net_score` tiebreak

**Current logic:** `direction_for_regime`, `qualification.py:578-597`.
`net_score > 0 → LONG`, `net_score < 0 → SHORT`, `net_score == 0 → None`
(excluded as `NEUTRAL_NO_DIRECTION`, `qualification.py:191-194`).

**Finding: the "±1 tiebreak" is real in code but structurally near-unreachable
under normal (full 8-vote) data — the confidence floor in §1 pre-empts it.**

`_classify_regime` (`regime.py:284-301`) only returns `NEUTRAL` when
`net_score ∈ {-1, 0, 1}` (≥2 or ≤-2 promote to RISK_ON/RISK_OFF). For the
directional cases (`net_score = ±1`) with the full 8-vote model,
`confidence = 1/8 = 0.125`, which is far below the 0.50 floor from §1 — so
`_determine_posture` returns `STAY_FLAT` (`regime.py:310`) and the candidate
never reaches Gate 3 at all; it's rejected at Gate 1/system short-circuit
first. A `net_score=±1` directional NEUTRAL trade can only reach Gate 3 in
production if enough of the 8 vote inputs are *skipped* (missing quotes,
`regime.py:178-181`) that `total_votes` shrinks to 1 or 2 — e.g. 6-7 of 8
macro symbols unavailable — which pushes `confidence` back up to
`0.50`–`1.0` despite the directional signal itself being exactly as thin (a
single net vote). This is a genuine edge case (a partial-data-outage
scenario, not a normal trading day), and it is the inverse of the
"soundness" concern the confidence floor is meant to prevent: **the fewer
votes that are cast, the easier it becomes for a one-vote margin to look
confident.** Nothing in `compute_regime` re-weights confidence for a
low-`total_votes` sample size (e.g. no minimum-votes-cast floor separate
from the vote-count-based confidence ratio itself).

**Verdict:** sound as designed for the mainline (full-data) case — no change
needed there. The narrower gap is a missing minimum-sample-size guard (e.g.
requiring `total_votes` above some floor before trusting the ratio at all),
which is a distinct knob from anything the brief asked to tune and isn't a
regime/RR/extension/stop threshold — **flagging for awareness, not proposing
a value**. **Confidence: medium** (the mechanism is exact; how often the
degraded-data path actually occurs in production is not something this
audit can observe from source alone).

---

## 3. CHOP rejection (Gate 4)

**Current logic:** hard-reject when `structure.structure == CHOP`
(`qualification.py:347-355`, `qualification.py:180-184` at the `qualify_all`
level). CHOP itself is defined upstream in `structure.py:146-213` from EMA
alignment + price zone, using three structure-layer-local constants not in
`config.py`: `_REVERSAL_SPREAD_MAX = 0.002`, `_REVERSAL_MOMENTUM_MIN =
0.003`, `_TREND_MOMENTUM_MIN = 0.005` (`structure.py:41-43`, explicitly
commented "structure-layer specific, not in config").

**Finding:** Gate 4 itself is a pure pass-through of an upstream binary
classification — there is no threshold to tune *in qualification.py* for
CHOP; the numeric levers live entirely in `structure.py` and were flagged by
the audit brief as in-scope conceptually ("CHOP rejection") but the actual
adjustable constants are outside the two files this audit was scoped to
(`qualification.py`, `config.py`). Treating CHOP as a **hard** gate (no
watchlist) rather than soft is consistent with the system's own framing
(`structure.py:9`: "automatic disqualification... never promoted to
output") — there is no partial-credit path for "structure is broken" the way
there is for, say, a marginal R:R. No SSRN search was run against this
item's structure-layer constants since they sit outside the FILES this audit
covers; if CHOP calibration is wanted, the follow-up PRD should expand scope
to `structure.py`. **Confidence: high** (Gate 4 has no independent
threshold; this is a scope-boundary observation, not a soundness verdict on
`structure.py`'s own constants).

---

## 4. Stop distance (Gate 6) — 1% floor + 0.5× ATR14

**Current value:** `stop_pct < 0.01` (`qualification.py:375`) **AND**
(when ATR available) `risk < 0.5 * dm.atr14` (`qualification.py:373, 380`).
Fail-open on the ATR half only when `dm is None` or `dm.atr14 is None`
(the 1% check still always runs).

**Documented rationale exists** (`docs/trade_qualification.md:116-118`) —
narrative, not empirical: the 1% floor is framed as an anti-noise floor,
the 0.5×ATR condition as reflecting "actual recent price movement."

**SSRN grounding:** no paper found calibrating a minimum-ATR-multiple stop
floor specifically. Practitioner-convention sources (non-SSRN, secondary)
consistently center ATR stop multiples in the **1×–2× range** for
day/swing trading (day trading ~1.5×–2×; swing ~2×–3×), with one backtest
reporting profit factor 1.16 at 2.0×ATR vs. 1.08 at 1.5×ATR vs. 1.01 at
3.0×ATR (i.e. even 1.5× already ran tight relative to 2.0× in that dataset).
**No source located supports a floor as low as 0.5× ATR** — every
convention found starts at 1× or higher.

**Verdict — proposed adjustment, not "leave as-is":** the *combination* (1%
OR-equivalent floor plus a 0.5×ATR floor, whichever governs) partially
mitigates this — a $480 stock's 1% floor ($4.80) already exceeds 0.5×ATR
when ATR is roughly ≤$9.60, which is the common case for large-cap
underlyings, so the ATR check as coded functions less as "the" floor and
more as a widening check on *volatile* names specifically. But taken purely
on its own terms, **0.5× is on the narrow side of every practitioner
reference this search found** (all clustering ≥1×). This is the one item in
this audit where the literature and convention point in a consistent
direction against the current value. **Confidence: medium** (the number
itself is unusually low vs. every source found, but no source directly
backtested *this* combined 1%-or-0.5×ATR construction, so the practical
effect of raising it can't be quantified from the literature alone).

**Related maintainability note (not a threshold-value finding):** the two
1% floors (`qualification.py:375` and `:669`, §0) are independent literals
that happen to share a value today. Neither references the other or a
common `config.*` constant, so a future retune of one (e.g., raising the
DIRECT-path floor per the finding above) would silently leave the
continuation-path floor unchanged unless someone remembers the second
location. Noted for awareness only, per the "no structural changes" scope.

---

## 5. R:R minimums — NEUTRAL (3.0) / EXPANSION (1.5) / default (2.0)

**Current values:** `config.py:61,111,112` — `MIN_RR_RATIO=2.0`,
`NEUTRAL_RR_RATIO=3.0`, `EXPANSION_RR_RATIO=1.5`. Consumed at Gate 7
(`qualification.py:390-408`) and reused for the CONTINUATION path's own R:R
check (`qualification.py:679`, against `EXPANSION_RR_RATIO`) and the FVG
PULLBACK_IMBALANCE path (`qualification.py:758`, see finding below).

**SSRN grounding — this is the strongest finding in the audit.** The
literature located (Zarattini/Barbon/Aziz's Opening Range Breakout day-trading
study, SSRN 4729284, 2016–2023 across ~7,000 US stocks; Costa's breakout
false-signal study, SSRN 6592020; general trend-following/mean-reversion
win-rate literature) is **consistent and points the opposite direction from
the current config**: momentum/continuation/breakout setups conventionally
carry **lower win rates and therefore need higher R:R** to stay profitable
(the ORB paper's own profit target sits at ~10× the stop distance), while
range-bound/mean-reverting conditions carry **higher win rates and can
tolerate lower R:R** (often cited near 1:1–2:1, "at best up to 3:1" in
practitioner sources).

The system currently does the reverse: **EXPANSION (momentum continuation)
gets the *lowest* R:R floor (1.5), and NEUTRAL (choppy/range) gets the
*highest* (3.0).** No source found in this search supports assigning
momentum/continuation trades a *lower* R:R requirement than range-bound
trades — every source located argues the opposite association (higher win
rate → tolerate lower R:R; lower win rate → require higher R:R), and
continuation/breakout setups are consistently characterized as the
*lower*-win-rate side of that pairing.

**Caveat before treating this as a clean reversal-and-fix:** the literature
speaks to win-rate-implied R:R for momentum/breakout strategies in general;
this repo's own CONTINUATION path additionally requires breakout + hold +
momentum confirmation (§7) before a trade qualifies at all, which plausibly
raises its win rate above a naive breakout entry — that's a real,
system-specific consideration the general literature can't speak to
directly, and this audit has no in-repo win-rate data to check it against
(no backtest/live-performance artifact was found in the reviewed paths).
**Verdict: proposed adjustment — the current NEUTRAL(3.0) > default(2.0) >
EXPANSION(1.5) ordering is not supported by the literature found and runs
contrary to the general momentum/mean-reversion R:R pattern; the specific
magnitude to use instead is not something this audit can derive from source
alone.** **Confidence: medium-high on the directional finding** (literature
agreement is consistent across multiple independent sources); **low on any
specific replacement number** (no source calibrates this exact vote/gate
construction, and the repo's own confirmation gates are a real mitigating
factor the general literature doesn't capture).

**Separate wiring observation, in-scope because it's an R:R threshold
question:** `_resolve_entry_mode`'s own R:R check
(`qualification.py:758`) reads
`min_rr = config.NEUTRAL_RR_RATIO if regime.regime == NEUTRAL else
config.MIN_RR_RATIO` — it has no `EXPANSION_RR_RATIO` branch. A base
DIRECT-path candidate that already qualified under EXPANSION's 1.5 R:R
floor (Gate 7) can be *upgraded* to PULLBACK_IMBALANCE mode and re-checked
against `MIN_RR_RATIO=2.0` instead of `EXPANSION_RR_RATIO=1.5` — a stricter
bar than the regime it's actually in received everywhere else. This may be
intentional (the FVG zone RR is a different, tighter-entry RR calculation,
arguably warranting its own bar), but as written it silently omits the third
config constant that exists specifically to handle this regime. Flagging
per the "STOP-AND-REPORT if a gate's behavior contradicts the summary"
instruction — this is a real behavior worth a human decision, not a
guess on my part about intent. **Confidence: high** that the omission
exists as coded; **not scored** on whether it's a bug, since intent isn't
recoverable from source alone.

---

## 6. Extension — `EXTENSION_ATR_MULTIPLIER` (1.5×) vs. continuation's `CONTINUATION_MAX_EXTENSION_ATR` (2.5×)

**Current values:** `config.py:110` (`EXTENSION_ATR_MULTIPLIER = 1.5`, Gate
10, `qualification.py:451-465`, fail-open when `dm`/`ema21`/`atr14`
unavailable) and `config.py:140` (`CONTINUATION_MAX_EXTENSION_ATR = 2.5`,
continuation path, `qualification.py:661-665`, **not** fail-open — if
`dm.ema21` is `None` the check is simply skipped for that call but
`dm.atr14` is already required non-`None`/`>0` earlier in the same function,
`qualification.py:632`, so this path's fail-open surface is narrower than
Gate 10's).

**SSRN grounding:** no paper found deriving either multiplier from a
calibration study. Keltner Channel convention (secondary sources —
StockCharts, TrendSpider, LiteFinance) places the standard ATR multiplier at
**1.5×–2×**, with **2×–3×** cited as a wider, "more selective" band
typically associated with mean-reversion setups specifically (not momentum
continuation). Bollinger Bands (2 standard deviations, not ATR-based) are a
philosophically parallel but distinct convention.

**Verdict:** both values sit within the practitioner-convention range as
*numbers* — 1.5× at the conventional low end for standard entries, 2.5×
within the 2–3× "wider/more selective" band for continuation. **Leave both
as-is on the number itself.** One directional mismatch worth noting: the
literature associates the *wider* band (2–3×) with mean-reversion
selectivity, not momentum continuation — the repo uses the wider band for
continuation (which chases an already-extended breakout by design, so a
looser extension cap makes intuitive sense operationally), which is a
different rationale than the literature's, even though the number itself
isn't out of range. **Confidence: medium** (numbers are in-range against
convention; no source validates the momentum-specific rationale for using
the wider band here, so this is convention-consistent rather than
empirically validated).

---

## 7. Continuation path K-values (EXPANSION-only)

All values: `config.py:136-140`.

| Constant | Value | Gate use | file:line |
|---|---|---|---|
| `CONTINUATION_BREAKOUT_BARS` | 5 | lookback window for breakout high | `qualification.py:608, 613` |
| `CONTINUATION_HOLD_CANDLES` | 1 | bars that must hold above breakout | `qualification.py:650-654` |
| `CONTINUATION_MOMENTUM_K` | 0.75 | last candle range ≥ K×ATR14 | `qualification.py:656-659` |
| `CONTINUATION_VIX_SPIKE_BLOCK` | 0.01 (+1%) | blocks continuation if VIX pct_change exceeds this | `qualification.py:638-643` |
| `CONTINUATION_MAX_EXTENSION_ATR` | 2.5 | see §6 | `qualification.py:661-665` |

**SSRN grounding — breakout hold window (5-bar lookback + 1-bar hold + 0.75×ATR
range confirmation):** the closest direct precedent found is an NSE
intraday-breakout study (SSRN 5198458) that empirically tests holding
periods of N=2, 3, 5 bars alongside volume-surge thresholds — implying some
multi-bar persistence measurably affects performance versus a single-bar
trigger, but it does not validate "1 bar" specifically over "2" or "3." A
second paper (SSRN 6592020) documents that a large majority (>75% in FX) of
unconfirmed breakouts are false/liquidity-sweep events, which supports
*some* confirmation filter existing, without pinning this one. **No source
found validates the exact 5+1+0.75×ATR combination**, and specifically no
source was found validating range-expansion-as-a-volume-proxy (the papers
located use actual volume thresholds, not an ATR-range stand-in — this
system has no intraday volume gate in the continuation path at all).
**Verdict: leave as-is; no empirical basis to move any of the three numbers
in a specific direction, but the single-bar hold sits at the thin end of
what the one directly-relevant study tested (2/3/5), and the substitution
of range-for-volume as the momentum proxy is untested in the literature
found.** **Confidence: low** (absence of evidence, not evidence of a
problem — genuinely no basis to recommend a specific change).

**Soundness finding — synthetic reward is not sensitive to the trade at
all, only its label suggests otherwise:**
`reward = dm.atr14 * ((CONTINUATION_BREAKOUT_BARS + max(1,
CONTINUATION_HOLD_CANDLES)) / 2.0)` (`qualification.py:674-677`). Since
`CONTINUATION_BREAKOUT_BARS` (5) and `CONTINUATION_HOLD_CANDLES` (1) are
both static config constants, this expression is arithmetically identical,
for every single continuation candidate under current config, to
`reward = 3.0 * atr14` — a fixed multiple of that symbol's own ATR14, with
zero sensitivity to how far price actually broke out, how strong the hold
was, or any other per-trade signal. The "formula" reads as if it responds to
breakout structure; it does not — it degenerates to a constant coefficient
given the current config, and would only start varying per-trade if
`CONTINUATION_BREAKOUT_BARS`/`CONTINUATION_HOLD_CANDLES` were themselves
made dynamic (out of scope here). This directly answers audit flag #2: **the
continuation path's R:R gate (`qualification.py:679`,
`rr = reward/risk`, checked against `EXPANSION_RR_RATIO`) is really only
measuring how tight the stop (`entry_price - breakout_level`) is relative to
`3.0×ATR14` — it is not comparing risk to any independent reward estimate
the way the DIRECT path's real `target_price` does.** This is architecturally
different from the DIRECT path's R:R gate in a way the config values alone
don't reveal — flagging as a **soundness concern about what the gate name
implies vs. what it measures**, not a threshold-value question, since it
isn't fixable by changing a number in `config.py`. **Confidence: high** (this
is arithmetic, verified directly against the constants above — not an
opinion).

**Related asymmetry vs. Gate 6 (stop distance, §4):** the continuation
path's own stop check (`qualification.py:667-672`,
`STOP_TOO_TIGHT`) enforces only the 1%-of-price floor
(`min_risk = entry_price * 0.01`) — it has **no ATR-based floor**
equivalent to Gate 6's `0.5×ATR14` check. A DIRECT-path candidate with an
identical stop distance would face a stricter test (both 1% AND 0.5×ATR)
than a CONTINUATION candidate (1% only). Whether this is intentional
(continuation stops are anchored to a structural breakout level rather than
chosen freely, so an independent volatility floor may be less necessary) or
an oversight is not something source alone resolves — flagging per the
"contradicts this summary" instruction, since the audit brief's framing
("two hardcoded 1% stop floors... these are tunable") implicitly assumed
parity between the two floors that doesn't actually exist in the
surrounding gate logic. **Confidence: high** on the asymmetry as coded;
not scored on intent.

---

## 8. FVG PULLBACK_IMBALANCE K-values

All values: `config.py:113-116`.

| Constant | Value | Use | file:line |
|---|---|---|---|
| `FVG_DISPLACEMENT_K` | 1.2 | displacement candle body ≥ K×ATR14 | `qualification.py:789, 796` |
| `FVG_GAP_K` | 0.3 | minimum gap size ≥ K×ATR14 | `qualification.py:564` |
| `FVG_PROXIMITY_K` | 1.5 | max distance from price to zone midpoint ≥ K×ATR14 (rejects if exceeded) | `qualification.py:751` |
| `FVG_LOOKBACK_CANDLES` | 6 | scan window (daily bars) | `qualification.py:540` |

No SSRN grounding was specifically sought for these four (the audit brief's
SSRN-search instruction was scoped to the gates named in "IN SCOPE," and FVG
detection is a candidate-recognition mechanism feeding into gates already
covered above, e.g. the RR check in §5 and the displacement-vs-range
question in §9, rather than an independent qualification threshold). No
soundness issue identified in these four values themselves beyond the
momentum-definition question addressed next.

---

## 9. Momentum definition: continuation (candle RANGE) vs. FVG displacement (candle BODY)

**Continuation:** `candle_range = High - Low` compared against
`CONTINUATION_MOMENTUM_K * atr14` (`qualification.py:656-659`) — wick-inclusive,
no check on where the close landed within that range.

**FVG displacement:** `body = |close - open|` compared against
`FVG_DISPLACEMENT_K * atr14`, **plus** a `close_location` check requiring
the close sit in the outer quartile of the bar's range
(`close_location >= 0.75` for LONG / `<= 0.25` for SHORT,
`qualification.py:769-798`) — body-based *and* directionally conviction-gated.

**Finding: these should not simply be reconciled to use the same measure —
they answer different questions, but the continuation check is the weaker
of the two as currently constructed.** FVG displacement is explicitly
testing "did this candle show real directional conviction" (a big range with
a weak, centered close — i.e., long wicks both ways — would fail the
close-location filter even with a big range). Continuation's momentum check
tests only "was this candle volatile," with no equivalent filter: a candle
with `High - Low ≥ 0.75×ATR14` but a close sitting near the open (long
wicks on both sides, i.e., a rejection/indecision candle by the FVG
definition's own standard) still passes continuation's momentum gate,
because the current-close check that determines the breakout
(`current_close <= breakout_level → reject`, `qualification.py:617`) is a
separate condition from the range check and doesn't test *where in the
day's range* that close falls. A candle could close only marginally above
the breakout level with a large intrabar range in the other direction and
still register as "sufficient momentum."

**Verdict: proposed adjustment, not "leave as-is" and not "reconcile to be
identical."** The two measures are legitimately answering different
questions (raw volatility-expansion vs. directional-conviction), so making
them identical would lose information the FVG gate deliberately encodes.
But continuation's momentum check would be more consistent with its own
stated intent ("insufficient momentum" as the rejection label,
`qualification.py:658`) if it incorporated some analogue of FVG's
close-location filter, since a wick-dominated candle is arguably the
opposite of momentum even when its total range is large. No SSRN source
speaks to this specific reconciliation question (it's an internal-consistency
finding, not a literature-calibration one). **Confidence: medium** (the
logical gap is clear from source; whether it produces materially different
qualification outcomes in practice can't be assessed without backtest data
this audit doesn't have access to).

---

## 10. Two fail-open gates compounding (earnings Gate 9 + extension Gate 10)

**Mechanism confirmed:** `qualification.py:441-449` (earnings, `None` →
pass + `gates_skipped` marker) and `qualification.py:451-465` (extension,
missing `dm`/`ema21`/`atr14` → pass + marker). Both can fire on the same
candidate in the same pass — nothing in `qualify_candidate` special-cases
the both-unknown case; each gate is evaluated independently
(`qualification.py:441` and `:451` don't reference each other).

**This was already investigated and partially addressed by PRD-235**
(`docs/prd_history/PRD-235.md`, COMPLETE): both markers accumulate into
`QualificationResult.gates_skipped` (a tuple, not a single value — confirmed
it does not silently overwrite when both fire, `qualification.py:109, 310,
447, 465, 491`), and `output.py:361-366` renders **all** skipped-gate names
on one line for a qualified TRADE setup: `"Gate skipped (missing data):
EARNINGS, EXTENSION"` when both are unknown simultaneously. So the
compounding case you're asking about is not silent — a human reading the
TRADE report sees both flags together, not one gate's absence masking the
other's.

**Real, documented gap (not something I derived — the project's own
PRD-235 review already flagged this and left it non-blocking):**
`docs/prd_history/PRD-235.review.claude.md` RECOMMENDED-1 notes that
`gates_skipped_for` in `output.py:319-330` is built only from
`qualified_trades` — a **WATCHLIST** result (one real soft-gate failure
elsewhere, plus one or both of Gates 9/10 fail-open on missing data) renders
only its `watchlist_reason`; the skip marker(s) are silently dropped from
that render path. So the double-unknown compounding case is visible for a
fully-qualified trade, but invisible for a watchlist trade carrying the same
double-unknown condition alongside a genuine miss elsewhere — a case that
arguably needs the visibility *more*, since it's already one soft-gate-miss
away from rejection and the reader has no way to see that two more
market-condition reads (earnings, extension) were also unverified on top of
that.

**Verdict:** the compounding scenario is real and reachable, but the
project already treats it as a visibility question rather than an outcome
question by design (`gates_skipped` docstring, `qualification.py:106-108`:
"Never affects the outcome — visibility only"), and that design choice
itself is not something this in-scope, no-structural-changes audit should
relitigate. The concrete, actionable gap is narrower than "two fail-opens
compound": **it's that the existing visibility fix (PRD-235) doesn't cover
the WATCHLIST render path**, a gap the project's own review process already
identified and consciously deferred as non-blocking. Flagging it here
because it's the most direct, literature-independent answer to the audit
brief's flag #1. **Confidence: high** (directly confirmed against source
and against the project's own prior review artifact — not a new discovery,
but worth surfacing since the tuning-audit brief asked about it directly).

---

## Doc drift (separated per instructions)

1. **`docs/system_logic_map.md:27`** still reads *"qualification.py — 9–11
   gates per candidate (4 hard, 5–7 soft)"* — stale. `qualification.py`
   itself says 11 (4 hard + 7 soft) unconditionally; this file was not
   swept by PRD-231 (which fixed `qualification.py`, `output.py`, and
   `docs/trade_qualification.md`'s "9 gates" wording per the PRD-231
   changelog) and still carries the range-hedged "9–11" / "5–7" phrasing
   that predates the fix.
2. **`docs/trade_qualification.md` is materially incomplete, not just
   stale on the gate count.** Gate 7's documented rule is a flat *"R:R
   ratio must be ≥ 2.0"* (`docs/trade_qualification.md:127-144`) — the doc
   has no mention anywhere of `NEUTRAL_RR_RATIO` (3.0) or
   `EXPANSION_RR_RATIO` (1.5), i.e. it documents only the default branch of
   Gate 7's three-way regime-tiered logic (`qualification.py:390-396`).
   More significantly, **the entire CONTINUATION entry mode and the FVG
   PULLBACK_IMBALANCE entry mode are absent from this document** — a grep
   for `CONTINUATION`, `FVG`, `PULLBACK_IMBALANCE`, and `entry_mode` across
   the file returns zero matches. A reader of this doc would not learn that
   two of the system's three entry-mode systems exist at all, let alone
   what their thresholds are. This is a larger gap than the "9 gates"
   fix PRD-231 already closed and is worth its own documentation PRD if
   `docs/trade_qualification.md` is meant to be the authoritative gate
   reference (its own header positions it that way).

---

## Summary table

| # | Threshold | Value | file:line | Verdict | Confidence |
|---|---|---|---|---|---|
| 1 | `MIN_REGIME_CONFIDENCE` | 0.50 | config.py:62 | leave as-is (already de facto regime-specific via posture tiers; only NEUTRAL binds on it live) | medium |
| 2 | NEUTRAL direction tiebreak | net_score ±1 | qualification.py:591-596 | leave as-is for full-data case; missing-data edge case flagged for awareness | medium |
| 3 | CHOP hard-reject | n/a (structure.py constants) | qualification.py:347-355 | no independent threshold here; out of the audited files | high |
| 4 | Stop distance | 1% + 0.5×ATR14 | qualification.py:375, 380 | proposed adjustment — 0.5×ATR floor is narrow vs. every convention found (≥1×) | medium |
| 5 | R:R minimums | NEUTRAL 3.0 / default 2.0 / EXPANSION 1.5 | config.py:61,111,112 | proposed adjustment — ordering contradicts literature (momentum should need higher R:R, not lower) | medium-high (direction) / low (magnitude) |
| 5b | FVG pullback RR branch | missing EXPANSION_RR_RATIO case | qualification.py:758 | flag for human decision — not scored as bug or intentional | high (as-coded) |
| 6 | Extension multipliers | 1.5× (direct) / 2.5× (continuation) | config.py:110,140 | leave as-is — both in-range vs. Keltner convention | medium |
| 7 | Continuation K-values | 5 bars / 1 hold / 0.75×ATR / +1% VIX block | config.py:136-139 | leave as-is — no basis to move; single-bar hold is thin end of the one directly relevant study | low |
| 7b | Continuation reward formula | `atr14 × 3.0` (always, given current config) | qualification.py:674-677 | soundness flag, not a value question — the "formula" is a disguised constant | high |
| 7c | Continuation stop floor | 1% only, no ATR floor | qualification.py:667-671 | asymmetry vs. Gate 6 flagged — intent unclear from source | high (as-coded) |
| 8 | FVG K-values | 1.2 / 0.3 / 1.5 / 6 bars | config.py:113-116 | no issue found | n/a |
| 9 | Momentum definition (range vs body) | — | qualification.py:656-659 vs 769-798 | proposed adjustment — continuation check should consider close-location like FVG does, not just raw range | medium |
| 10 | Double fail-open (Gates 9+10) | — | qualification.py:441-465 | already handled for QUALIFIED renders (PRD-235); known, deferred gap for WATCHLIST renders | high |

---

## Note on SSRN access

Direct SSRN.com abstract pages returned HTTP 403 to the research agent's
fetches (bot-blocked); findings above rely on search-result snippets and
secondary sources describing each paper's content, not full-text
verification. Paper identifiers (author, year, SSRN abstract ID) are
reported as returned by search — treat citations as pointers to verify
independently before using them to justify a PRD, not as confirmed
full-text reads.

---

## Handoff prompt — for Claude (project lead) to draft the follow-up PRD

The findings above are not equally strong. The prompt below is written to
carry that gradient forward rather than let a PRD draft treat all ten
findings as equally backed.

```
ROLE: You are Claude acting as project lead for Cuttingboard — draft (or decide
not to draft) a PRD from a completed tuning audit. Do not implement code.

CONTEXT: A read-only audit of the trade-qualification gates (cuttingboard/
qualification.py, cuttingboard/config.py) has been committed to
audits/qualification-tuning-2026-07-05/findings.md on branch
claude/qualification-system-audit-sp0wat (commit d5071302a3aa527a11a2e327
4ba8157a4a245a3d). Read that file in full before deciding anything — this
prompt summarizes it but the file has the exact file:line citations,
worked-example tracing, and full SSRN source list you need to write FAIL
conditions and cite rationale correctly.

The audit found 10 numbered findings. They are NOT equally strong — weight
them accordingly:

STRONG (literature confluence across independent sources, clear directional
finding):
  - R:R minimums (config.py:61,111,112 — NEUTRAL 3.0 / default 2.0 /
    EXPANSION 1.5). Momentum/breakout literature (ORB study SSRN 4729284,
    breakout-failure study SSRN 6592020, general trend-following/mean-
    reversion win-rate literature) consistently says LOWER win-rate
    momentum trades need HIGHER R:R, not lower. Current ordering is
    backwards from every source found. This is the audit's headline
    finding — decide whether it's real enough to act on, and if so, what
    the new ordering/magnitude should be (the audit found no source
    calibrating the specific numbers, only the direction).

MODERATE (convention-consistent but not calibration-backed; one has a real
code-level asymmetry as leverage):
  - Stop distance floor (qualification.py:375,380 — 1% + 0.5×ATR14). Every
    practitioner source found clusters ATR-stop multiples at ≥1×; 0.5× is
    narrow relative to all of them.
  - Momentum definition mismatch (qualification.py:656-659 vs 769-798) —
    continuation's momentum check uses wick-inclusive candle RANGE with no
    close-location filter; FVG's displacement check uses candle BODY plus a
    close-location filter. Not a "reconcile to match" case — they answer
    different questions — but continuation's check is weaker against its
    own stated intent ("insufficient momentum") than it needs to be.

CODE-BEHAVIOR FLAGS (no literature angle at all — these are pure "does this
wiring match its own apparent intent" questions, need a human/Dustin
decision, not a literature review):
  - qualification.py:758 — the FVG pullback R:R check has no
    EXPANSION_RR_RATIO branch; an EXPANSION-regime pullback entry gets
    checked against the stricter default (2.0) instead of the regime's own
    1.5, with no comment explaining why.
  - qualification.py:674-677 — the continuation path's "synthetic reward"
    formula is, given current config, arithmetically identical to a
    constant `3.0 × ATR14` for every trade (both terms inside it are static
    config constants) — it looks sensitive to breakout structure and isn't.
  - qualification.py:667-671 vs 375,380 — the continuation stop check
    enforces only the 1% floor, no ATR floor equivalent to Gate 6's
    0.5×ATR — an unexplained asymmetry between the two entry-mode systems.

LEAVE-AS-IS (audit found no basis to change, or the finding was that the
audit's own framing was wrong):
  - MIN_REGIME_CONFIDENCE=0.50 (config.py:62) — turns out to already be
    de facto regime-specific via posture tiers in regime.py; only NEUTRAL
    actually binds on the literal 0.50 in production. Don't split it into
    four constants — that would duplicate logic regime.py already has.
  - Extension multipliers (1.5× / 2.5×, config.py:110,140) — both in-range
    against Keltner Channel convention.
  - Continuation K-values (5 bars / 1 hold / 0.75×ATR / VIX block,
    config.py:136-139) — no basis found to move any of them.
  - NEUTRAL net_score ±1 direction tiebreak — sound for the mainline case;
    only reachable in a degraded-data (most-votes-missing) edge case, which
    is a separate, smaller finding than what was originally asked about.

DOC DRIFT (separate from the threshold questions — decide if these need
their own MICRO-lane doc PRD alongside or instead of a threshold PRD):
  - docs/system_logic_map.md:27 still says "9–11 gates... 4 hard, 5–7 soft"
    (PRD-231 fixed this everywhere else but missed this file).
  - docs/trade_qualification.md documents only Gate 7's default R:R branch
    (≥2.0) — it has zero mentions of NEUTRAL_RR_RATIO, EXPANSION_RR_RATIO,
    the CONTINUATION entry mode, or the FVG PULLBACK_IMBALANCE entry mode.
    If this doc is meant to be the authoritative gate reference, it's
    missing two of the system's three entry-mode systems entirely.

YOUR TASK:
1. Read the full audit file — do not rely on this summary for citations.
2. Decide which findings (if any) warrant a PRD. You do not have to act on
   all of them — "leave as-is" is explicitly a valid finding per the audit,
   and the audit itself declined to recommend specific replacement
   magnitudes for several items (it found direction, not calibration).
3. If drafting a PRD: classify lane (STANDARD vs. HIGH-RISK vs. MICRO per
   docs/PRD_PROCESS.md — these are live trading thresholds, not cosmetic,
   but also not a contract/architecture change; use your judgment on
   whether the R:R reordering alone crosses into HIGH-RISK given it changes
   qualification outcomes for real capital).
   Apply the pre-implementation grep sweep discipline (CLAUDE.md) before
   finalizing FILES: grep tests/ for every constant name you intend to
   change (NEUTRAL_RR_RATIO, MIN_RR_RATIO, EXPANSION_RR_RATIO, the two 0.01
   literals, CONTINUATION_MOMENTUM_K, etc.) and add every asserting test
   file to FILES up front, not reactively.
4. If you decide the doc drift is a separate, smaller MICRO-lane fix, say
   so explicitly and scope it separately from any threshold-value PRD.
5. Where the audit flagged something as a code-behavior question with "not
   scored, human decision needed" (the FVG RR branch, the synthetic reward
   formula, the stop-floor asymmetry) — make an explicit call on each
   rather than silently folding it into "leave as-is." These read as real
   gaps against the system's own internal consistency even without any
   SSRN angle.

Do not treat SSRN full-text as verified — the audit's citations come from
search snippets (direct SSRN.com fetches were bot-blocked), useful for
confluence/directional confidence, not as confirmed primary-source reads.
```
