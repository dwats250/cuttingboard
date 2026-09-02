# Codex Event-1 review — Dashboard D3 MATERIAL packet

```
GOV-2 sec2 step 3 artifact. Reviewed packet revision (PRD-328 form): 4372b9e4fdd2a8aa88f9f5c6627b03b94b204e23. Captured verbatim from codex stdout 2026-09-02; original slot docs/prd_history/PRD-328.review.codex.md.
VERDICT: REJECT — 7 REQUIRED, 3 RECOMMENDED. The ONE consolidated correction applied at 2c05ef6 (+ 4ca0013).
```

---

# PRD-328 Review - Sol / Codex (commissioned fresh-context independent design review)

**Reviewed head:** 4372b9e4fdd2a8aa88f9f5c6627b03b94b204e23  **Merge base:** ebf01dd  
**Verdict:** REJECT - 7 REQUIRED, 3 RECOMMENDED

Fresh-context, read-only review. `HEAD` matched the frozen SHA. The merge base resolved to `ebf01dd888b68a8414704ad774f1245973673ce8`. `git diff ebf01dd..4372b9e --stat` contained only `docs/prd_history/PRD-328.md`, `docs/PRD_REGISTRY.md`, and `docs/prd_index.json`. No implementation was expected or reviewed.

## Strengths

- S1's HTML mechanism is technically sound. A closed outer `details.tier-group` hides every descendant except its own summary, even if nested `level-detail` and `chart-detail` elements carry `open`. The CSS changes marker appearance only and has no selector that forces closed details content visible. Evidence: [dashboard_renderer.py:925](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:925), [dashboard_renderer.py:989](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:989), [dashboard_renderer.py:1039](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:1039).
- The decision-state matrix is correctly understood. Non-permitted, lock, and HALT paths have `level-detail`; TRADE PERMITTED omits it; the chart disclosure remains independently available. Evidence: [dashboard_renderer.py:2320](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2320), [dashboard_renderer.py:2355](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2355), [dashboard_renderer.py:2359](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2359).
- The expected D2 hash impact is accurate. Of the 16 pinned fixtures, only `primary_chart_c_grade` has a C tier, and that tier is already open because SPY is its primary. None currently carries `spy_observation`. Evidence: [preview_fixtures.py:267](/home/dustin/Projects/cuttingboard/tests/preview_fixtures.py:267), [preview_fixtures.py:294](/home/dustin/Projects/cuttingboard/tests/preview_fixtures.py:294), [test_dashboard_d2_seam.py:45](/home/dustin/Projects/cuttingboard/tests/test_dashboard_d2_seam.py:45).
- The neutral ladder call is valid. With both contract values `None` and `operator_locked=False`, `_render_level_ladder` emits NOW and valid zone/fib rows without entry, stop, risk-band, lock, neutral, or action classes. The cyan `lvl-vwap` class is structural VWAP styling, not candidate permission. Evidence: [dashboard_renderer.py:2011](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2011), [dashboard_renderer.py:2041](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2041), [dashboard_renderer.py:2057](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2057), [dashboard_renderer.py:2089](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2089).
- Deferring the current-session SPY chart is the correct O4 disposition. The existing A1 consumer requires `snapshot.primary_symbol == primary_symbol`; using SPY independently requires an A1 consumer-contract change, even though the hourly producer already attempts SPY acquisition. Evidence: [intraday_bars.py:49](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/intraday_bars.py:49), [intraday_bars.py:76](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/intraday_bars.py:76), [runtime/__init__.py:839](/home/dustin/Projects/cuttingboard/cuttingboard/runtime/__init__.py:839).
- The production ceiling is credible after correction. The observation emitter is primarily relocated, and S1 requires only two keyword paths and two conditional attributes. No additional production file is inherently necessary.
- Drift check: the feature remains descriptive, read-only, and human-facing, consistent with [VISION.md:49](/home/dustin/Projects/cuttingboard/VISION.md:49). It does not create an execution or prediction surface.

## REQUIRED findings

### REQ-1 - [factual drift] A MATERIAL PRD cannot serve as its own upstream MATERIAL packet

**Claim:** The declared GOV-2 sequence is invalid. PRD-328 says, "this PRD is the packet," but GOV-2 requires a provisional packet, initial independent review, correction, exact-head confirmation, an owner design-direction ruling, and only then a separately drafted and reviewed PRD. This review was not supplied a distinct review-clean packet.

**Evidence:** PRD-328 makes the self-packet claim at [PRD-328.md:19](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:19). GOV-2 requires the packet before any downstream PRD at [GOV-2:31](/home/dustin/Projects/cuttingboard/docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:31) and defines the packet-to-PRD sequence at [GOV-2:65](/home/dustin/Projects/cuttingboard/docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:65). The MATERIAL review contract requires the reviewer to receive the PRD together with the review-clean packet and Dustin's design-direction ruling at [PRD_PROCESS.md:144](/home/dustin/Projects/cuttingboard/docs/PRD_PROCESS.md:144) and [MODE_REVIEW.md:15](/home/dustin/Projects/cuttingboard/docs/contract/MODE_REVIEW.md:15).

**Smallest fix:** Produce and link a separate MATERIAL packet, complete its initial review, consolidated correction, and exact-corrected-head confirmation, then record Dustin's design-direction ruling and revise PRD-328 from that authority. Recommission the fresh-context PRD review on the corrected PRD head. Alternatively, Helm must explicitly resolve the GOV-2 conflict; no exception can be inferred from the present charge.

### REQ-2 - [factual drift] The planned supersession set is incomplete

**Claim:** The three planned propagation notes do not cover every current ruling changed by S1 and S2. At minimum, PRD-318 R1 and R4 and PRD-326 R1/R2 are also changed. Merely preserving the count of four `operator-zone` classes does not preserve PRD-318 R1's exact top-level hierarchy.

**Evidence:**

- PRD-318 R1 specifies the top-level sequence as VERDICT, TAPE, TODAY, WATCHING, DETAILS / HISTORY at [PRD-318.md:51](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-318.md:51). S2 inserts a new first-class top-level section between WATCHING and DETAILS at [PRD-328.md:85](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:85).
- The current PRD-318 R4 clause keys `level-detail` only from decision state at [PRD-318.md:63](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-318.md:63) and [PRD-318.md:66](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-318.md:66). S1 additionally keys its open state from closed-tier membership.
- PRD-326 says no secondary chart opens at [PRD-326.md:95](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-326.md:95), keeps every secondary `chart-detail` closed at [PRD-326.md:237](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-326.md:237), and makes every non-primary card byte-identical with "no secondary chart opens" at [PRD-326.md:260](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-326.md:260).
- The canonical 2026-09-01 decision repeats that secondary charts do not open and Q2 remains unchanged at [DECISIONS.md:56](/home/dustin/Projects/cuttingboard/docs/DECISIONS.md:56).
- GOV-2 requires every changed ruling to be marked and exactly one current ruling to remain at [GOV-2:278](/home/dustin/Projects/cuttingboard/docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:278).

**Smallest fix:** Expand the propagation ledger to cover PRD-318 R1, R4, and R5; PRD-321 ruling Q2 and R3; and every current PRD-326 D1-Q1/R1/R2 clause that forbids secondary opening. The new dated decision entry must quote the resulting current rules and identify PRD-328 as the sole current authority for those clauses. PRD-327's four full-weight-zone rule can remain unchanged because `#spy-session` is not an `operator-zone`.

### REQ-3 - [stale-data ambiguity] The SPY section mixes independent clocks and bypasses existing market-map health

**Claim:** R5 places an unlabeled Market Map NOW price beside the session-observation PRICE and daily-bar caption. These values have separate clocks. The section also proposes reading the SPY map record without applying the renderer's existing lineage/source-health result, so a stale or mixed Market Map can feed a chart that the candidate board would suppress.

**Evidence:**

- The observation PRICE is anchored by `observed_at_utc`, displayed at [dashboard_renderer.py:3303](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:3303) and [dashboard_renderer.py:3316](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:3316).
- Market Map owns a separate `generated_at` and `run_at_utc` at [market_map.py:144](/home/dustin/Projects/cuttingboard/cuttingboard/market_map.py:144).
- The daily-bars caption contains only bar `as_of`, provider, and interval at [dashboard_renderer.py:1189](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:1189).
- The chart renders the Market Map anchor prominently as `NOW` at [setup_chart.py:307](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:307) and [setup_chart.py:333](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:333).
- Existing rendering computes source health at [dashboard_renderer.py:2646](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2646) and suppresses candidate cards under unhealthy lineage or unavailable map state at [dashboard_renderer.py:3137](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:3137). PRD-328 R7 instead declares only the observation, bars entry, and SPY symbol record as inputs at [PRD-328.md:343](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:343).

**Smallest fix:** Reuse the existing market-map health and lineage result as an explicit observational input. Do not render map-derived chart/ladder values when that source is missing, mixed, stale, or unusable under the existing policy. When rendered, label the NOW clock using the existing Market Map timestamp and distinguish it from the session PRICE/OBSERVED AT clock and daily candle `as_of`. Amend R7's pure-input list accordingly while continuing to exclude decision and permission state.

### REQ-4 - [schema ambiguity] SPY availability and unavailable behavior are not fully specified

**Claim:** The recon overstates source guarantees and leaves a crash/ambiguity seam. A canonical `build_market_map` includes a SPY record, but `render_dashboard_html` accepts partial supplied maps. The price-bars producer can omit SPY. The recon also incorrectly says EMA9, EMA21, and EMA50 are always emitted.

**Evidence:**

- The canonical builder enumerates SPY through `PRIMARY_SYMBOLS` at [market_map.py:19](/home/dustin/Projects/cuttingboard/cuttingboard/market_map.py:19) and [market_map.py:130](/home/dustin/Projects/cuttingboard/cuttingboard/market_map.py:130), but the renderer accepts any `market_map: dict | None` at [dashboard_renderer.py:2384](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2384).
- The bars producer writes a symbol only when usable rows exist at [runtime/__init__.py:2638](/home/dustin/Projects/cuttingboard/cuttingboard/runtime/__init__.py:2638), and the reader also drops malformed, empty, or over-age entries at [dashboard_renderer.py:1206](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:1206).
- Watch zones are conditional on valid price and inputs, and each candidate zone is omitted when missing, non-finite, or more than 5 percent from price at [market_map.py:310](/home/dustin/Projects/cuttingboard/cuttingboard/market_map.py:310) and [market_map.py:343](/home/dustin/Projects/cuttingboard/cuttingboard/market_map.py:343). This contradicts the "EMA9/EMA21/EMA50 always" claim at [PRD-328.md:202](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:202).
- R5 and T13 cover absent bars and invalid price but do not explicitly cover missing `symbols`, missing SPY, or a non-dict SPY record at [PRD-328.md:312](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:312) and [PRD-328.md:461](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:461).

**Smallest fix:** Correct the recon table. Specify safe `.get`-style resolution for the symbols map and SPY record. Add exact outcomes and red cases for `market_map=None`, missing/non-dict `symbols`, missing/non-dict SPY, invalid `current_price`, absent SPY bars, empty SVG, and legitimately empty zones/fibs. State explicitly that observation PRE_OPEN/STALE/UNAVAILABLE does not by itself suppress an otherwise healthy daily/map chart, if that is the intended rule.

### REQ-5 - [factual drift] T11's no-rect oracle rejects every valid candlestick chart

**Claim:** The proposed neutrality assertion forbids `<rect`, but the renderer always emits non-risk rectangles for the chart background, candle bodies, and NOW tag. A neutral chart with `contract_entry=None` and `contract_stop=None` still necessarily contains rectangles.

**Evidence:** R5 and T11 prohibit a `<rect` at [PRD-328.md:325](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:325) and [PRD-328.md:458](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:458). The chart always emits a background rect at [setup_chart.py:205](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:205), candle-body rects at [setup_chart.py:268](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:268), and a NOW-tag rect at [setup_chart.py:333](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:333). Only `class="risk-zone"` is gated by the entry/stop pair at [setup_chart.py:213](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:213).

**Smallest fix:** Replace every generic no-`<rect` assertion with absence of `class="risk-zone"` and absence of entry/stop line and text classes. Retain the checks for `ENTRY`, `STOP`, `lvl-entry`, `lvl-stop`, `#e0a552`, and `#e05252`.

### REQ-6 - [factual drift] T1-T16 are not all red tests against the pre-PRD renderer

**Claim:** The validation preamble requires every T1-T16 test to fail before implementation, but several listed cases deliberately assert unchanged behavior and already pass. This makes the test contract self-contradictory.

**Evidence:** The all-red claim appears at [PRD-328.md:446](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:446). T3-T6 and T7 assert existing invariants; current tests already require the open-C sibling and closed-C no-primary cases to contain no nested `open` at [test_dash_candidates.py:1115](/home/dustin/Projects/cuttingboard/tests/test_dash_candidates.py:1115). T9 is byte parity of the existing observation grid. T15's default STAY condition is already the current MCC placement at [dashboard_renderer.py:3326](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:3326). T13's no-observation byte-parity subcase also passes before the change. The single script already exists at [dashboard_renderer.py:2678](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2678), so T6 is pre-green.

**Smallest fix:** Divide validation into change-driving red tests and preserved regression guards. Require pre-implementation red only for the new behavior cases, including T1, T2, T8, T10, chart/ladder presence-positive versions of T11/T12, the new unavailable branches, a non-vacuous T14, and T16. Label T3-T7, T9, T15, and no-observation parity as regression tests. Also replace R5's ambiguous "unavailable state" with named chart-input conditions.

### REQ-7 - [scope creep] The fixture change requires an omitted test file

**Claim:** Adding `spy_session_observed` to the preview catalog necessarily fails the existing exact-catalog contract, but `tests/test_preview_fixtures.py` is absent from FILES.

**Evidence:** PRD-328 authorizes a new fixture at [PRD-328.md:61](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:61) and requires it in T16 at [PRD-328.md:465](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:465). The preview test pins the complete case-name set at [test_preview_fixtures.py:28](/home/dustin/Projects/cuttingboard/tests/test_preview_fixtures.py:28) and asserts exact equality at [test_preview_fixtures.py:81](/home/dustin/Projects/cuttingboard/tests/test_preview_fixtures.py:81). The file is absent from PRD-328's FILES list at [PRD-328.md:122](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:122).

**Smallest fix:** Add `tests/test_preview_fixtures.py` to FILES and the test LOC ceiling. Update `_EXPECTED_CASE_NAMES` and the associated preview-contract commentary. `scripts/preview_fixtures.py` need not change because it already consumes `SECTION_STATE_CASES`.

## RECOMMENDED findings

### REC-1 - [non-determinism] Strengthen R7 against vacuous or coupled byte-identity tests

**Claim:** Byte equality across four renders is useful but does not prove the declared source cone if the section is absent, extraction is incorrect, multiple state fields change together, or forbidden state is read without changing output.

**Evidence:** R7 prohibits both output variation and source reads at [PRD-328.md:343](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:343), while T14 describes only output equality across combined states at [PRD-328.md:463](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:463).

**Smallest fix:** Require `#spy-session` and its chart/ladder markers as positive controls, vary `decision_state`, `operator_locked`, and `outcome` one at a time, and add a source-cone assertion that the new emitter does not reference decision, permission, contract, or candidate variables.

### REC-2 - [schema ambiguity] Explicitly rule the two-SPY-chart co-occurrence

**Claim:** If SPY is also the canonical candidate, the page may contain one candidate `setup-chart` and one observational `spy-chart`. S2-Q2 implicitly permits this but does not explicitly say whether the same-symbol duplication is intentional.

**Evidence:** The committed C-primary fixture makes SPY the sole C candidate at [preview_fixtures.py:294](/home/dustin/Projects/cuttingboard/tests/preview_fixtures.py:294). Candidate chart emission is at [dashboard_renderer.py:2355](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2355), while the proposed observational chart is authorized at [PRD-328.md:312](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:312).

**Smallest fix:** Add one sentence to S2-Q2 stating that one `setup-chart` plus one `spy-chart` is intentional even when both symbols are SPY because their semantics differ. Add a co-occurrence test pinning exactly one of each. If Helm does not accept that duplication, the alternative belongs inside S2-Q2 rather than being inferred during implementation.

### REC-3 - [factual drift] PROJECT_STATE already has a stale active-work pointer

**Claim:** The design head adds PRD-328 as IN PROGRESS while `docs/PROJECT_STATE.md` still says no PRD is active and is dated before PRD-326 through PRD-328.

**Evidence:** [PROJECT_STATE.md:8](/home/dustin/Projects/cuttingboard/docs/PROJECT_STATE.md:8) and [PROJECT_STATE.md:46](/home/dustin/Projects/cuttingboard/docs/PROJECT_STATE.md:46). PRD-328 already lists the state pointer as implicit bookkeeping at [PRD-328.md:132](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:132).

**Smallest fix:** Refresh only the active-work pointer and date during the design correction. Do not duplicate the PRD's requirements into PROJECT_STATE.

## Attack-surface checklist

1. **PASS** - A closed outer native `details` hides the card and both open descendants; only the outer tier summary remains visible. No CSS rule overrides closed-content display. Evidence: [dashboard_renderer.py:989](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:989), [dashboard_renderer.py:3206](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:3206).
2. **PASS** - S1 does not expose a secondary chart before a tier click. TRADE PERMITTED omits `level-detail`; lock and HALT use the non-permitted path; an already-open primary C tier passes `tier_closed=False`, so its sibling remains closed. Evidence: [dashboard_renderer.py:2320](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2320), [dashboard_renderer.py:2359](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2359), [dashboard_renderer.py:3209](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:3209).
3. **PASS** - The intended runtime regression is narrow, and no existing D2 golden/fixture hash should move: the sole C fixture has an already-open primary tier. Canonical propagation is separately FAIL under item 13. Evidence: [preview_fixtures.py:294](/home/dustin/Projects/cuttingboard/tests/preview_fixtures.py:294), [test_dashboard_d2_seam.py:40](/home/dustin/Projects/cuttingboard/tests/test_dashboard_d2_seam.py:40).
4. **FAIL** - SPY observation is daily-only and absent from current fixtures, but SPY bars are conditional, partial renderer maps need not contain SPY, and watch-zone EMAs are not always emitted. Evidence: [payload.py:31](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/payload.py:31), [runtime/__init__.py:2493](/home/dustin/Projects/cuttingboard/cuttingboard/runtime/__init__.py:2493), [market_map.py:343](/home/dustin/Projects/cuttingboard/cuttingboard/market_map.py:343).
5. **FAIL** - Canonical observation states suppress session VWAP/PRICE honestly, and the `1d` caption avoids claiming intraday candles, but the adjacent Market Map NOW clock and stale/mixed-map behavior are unlabeled and ungated. Evidence: [spy_observation.py:82](/home/dustin/Projects/cuttingboard/cuttingboard/spy_observation.py:82), [spy_observation.py:99](/home/dustin/Projects/cuttingboard/cuttingboard/spy_observation.py:99), [setup_chart.py:333](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:333).
6. **NOTE** - The proposed calls can remain decision-independent, and placement below WATCHING does not create a second permission card. R7 needs stronger non-vacuity/source-cone coverage, and map source health must become a declared observational input. Evidence: [PRD-328.md:343](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:343).
7. **PASS** - With both contract values `None`, the ladder emits no entry, stop, risk-band, lock, neutral, or action classes. `lvl-vwap` and tier classes encode level type/weight only. Evidence: [dashboard_renderer.py:2041](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2041), [dashboard_renderer.py:2070](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2070), [dashboard_renderer.py:2089](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2089).
8. **NOTE** - TODAY's compact state plus the full observation is an existing summary/detail pattern, and moving the full block does not remove it. A candidate SPY chart plus observational SPY chart is implicitly permitted by S2-Q2 but should be ruled explicitly. Evidence: [dashboard_renderer.py:2966](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2966), [PRD-328.md:403](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:403).
9. **PASS** - Candidate-only narrowing plus one named non-candidate chart is the smallest honest Q2 change. A default-closed `chart-detail` fallback inside `#spy-session` preserves first-class observation placement while requiring one chart click. Evidence: [PRD-328.md:403](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:403).
10. **FAIL** - The 70-line production ceiling is credible and the four-full-weight-zone test remains unchanged, but `tests/test_preview_fixtures.py` is a required omitted FILES consumer. Evidence: [test_dashboard_renderer.py:4067](/home/dustin/Projects/cuttingboard/tests/test_dashboard_renderer.py:4067), [test_preview_fixtures.py:81](/home/dustin/Projects/cuttingboard/tests/test_preview_fixtures.py:81).
11. **FAIL** - Multiple listed tests are intentionally pre-green, and T11's generic no-rect assertion rejects every real candlestick chart. R5's phrase "unavailable state" is also ambiguous between observation state and chart-input unavailability. Evidence: [PRD-328.md:446](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-328.md:446), [setup_chart.py:205](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:205).
12. **PASS** - No PRD-323/324 surface is needed. The current leaf is primary-symbol-bound, so the named symbol-selectable A1 consumer prerequisite is the correct O4 deferral. Evidence: [intraday_bars.py:76](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/intraday_bars.py:76), [PRD-324.md:318](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-324.md:318).
13. **FAIL** - MATERIAL and HIGH-RISK are correct, but GOV-2 sequencing is unsatisfied and the three planned supersession propagations omit current conflicting clauses in PRD-318 and PRD-326. Evidence: [GOV-2:18](/home/dustin/Projects/cuttingboard/docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:18), [GOV-2:65](/home/dustin/Projects/cuttingboard/docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:65), [GOV-2:278](/home/dustin/Projects/cuttingboard/docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:278).

## Blockers for Helm

- GOV-2 sequencing resolution: the current record has no distinct review-clean MATERIAL packet preceding PRD-328. Helm must decide whether to require the canonical packet sequence or issue an explicit higher-authority exception. No exception is inferred here.
- S2-Q1: STAY in DETAILS / HISTORY or MOVE with the observation group. STAY remains the safer O3 choice.
- S2-Q2: approve or decline the candidate-chart narrowing and the single visible non-candidate `spy-chart`. The same ruling should explicitly cover the two-SPY-chart co-occurrence.
- S1-Q1: confirm or decline the bounded closed-C-tier secondary-opening supersession.
- Gate A remains held until the REQUIRED edits are corrected and the exact corrected head receives the applicable independent confirmation.
