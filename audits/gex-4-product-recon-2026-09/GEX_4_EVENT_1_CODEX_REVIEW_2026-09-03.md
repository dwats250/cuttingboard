# GEX-4 Provisional MATERIAL Package - Event 1 Codex Review (durable record)

- **Event type:** INITIAL PACKET REVIEW (quantitative / semantic falsification)
- **Reviewer:** Codex (codex-cli 0.150.1), fresh-context independent reviewer, `-s read-only`, `model_reasoning_effort=high`
- **Reviewed commit (frozen head):** `e25996425870b871c45db7982870de31af4aa47f` (PR #309)
- **Package under review:** `GEX_4_PRODUCT_RECON_2026-09-03.md` + `GEX_4_CODEX_HIGH_PACKET_2026-09-03.md` (treated together per the Helm Event-1 commission)
- **Date:** 2026-09-03
- **Verdict:** APPROVE WITH REQUIRED EDITS (8 REQUIRED, 0 BLOCKING, 5 RECOMMENDED)
- **Context:** fresh, read-only, independent (not the packet author or same-session implementer); commissioned by Helm ("GEX-4 EVENT-1 CODEX HIGH ADVERSARIAL REVIEW")
- **Tokens used (reported by codex):** 115,179
- **Findings:** verbatim Codex stdout reproduced below without paraphrase or weakening. No packet edit, no correction, no PRD, no production code was made in response; adjudication is Helm-held.

Packet defect confirmed by the reviewer (Q8): the packet's question text calls 7750 "the widest bin"; the 31-bin table in the same packet shows 8000 (72.57B) as widest and 7750 (47.53B) as widest at spot. Recorded here, not corrected, pending Helm adjudication.

---

## Verbatim Codex stdout

```
GEX-4 CODEX HIGH - EVENT 1

REVIEWED HEAD: e25996425870b871c45db7982870de31af4aa47f

1. VERDICT (APPROVE / APPROVE WITH REQUIRED EDITS / REJECT-REDESIGN)

APPROVE WITH REQUIRED EDITS.

No BLOCKING finding requires a different fundamental representation. Net over gross can be an honest descriptive view, but the frozen proposal is not safe to ship unchanged. Its current labels, palette, anchor semantics, window disclosure, and post-settlement behavior make the model look more like measured dealer exposure and actionable price structure than the evidence supports.

The strongest justified description of the 8000 structure is: "a large, near-balanced call-contract and put-contract modeled-magnitude concentration at the same strike and across several expirations." It is consistent with multiple strategies, including box or synthetic financing, but is not diagnostic of any strategy, participant, pairing, or position direction.

No files were edited. Final status remained clean at the reviewed head.

2. REQUIRED FINDINGS (exact and finite)

R1 - REQUIRED - Remove position-identity overclaim.

The recon's statement that the 8000 OI is "box-spread / synthetic-forward financing paper" is unsupported. Aggregate OI provides no trade-level pairing, opening/closing direction, account identity, participant side, or second-strike box legs. Identical call/put gamma at the same strike and expiration is provider-model behavior, not identity evidence. Remove "financing paper," "footprint," and any claim that the current walls were "captured by" a known strategy.

R2 - REQUIRED - Bound net and gross to their actual arithmetic.

"Net" is call modeled magnitude minus put modeled magnitude under the configured option-type sign convention. It is not measured net dealer gamma. "Gross" is call plus put modeled magnitude and is independent only of that configured sign assignment; it is not participant gross exposure and does not establish that any positions offset.

At raw strike 8000, 38.06B call and 32.94B put produce 71.00B magnitude and +5.12B model net, or 7.2% |net|/magnitude. At the 7700 bin, 19.78B and 19.75B produce 39.53B magnitude and only +0.03B model net, or about 0.08%. Those are honest arithmetic facts. "Cancellation," "offset," and "two-sided position" are too strong unless explicitly qualified as within-bin arithmetic under the convention.

No additional quantity is required for v0. The two side magnitudes plus model net already expose balance. The defect is claim strength, not missing arithmetic.

R3 - REQUIRED - Remove directional trading color semantics and loaded nouns.

Blue-positive/right and red-negative/left, combined with an SPX spot line, makes the unmeasured convention look bullish/bearish or long/short gamma even if a footnote denies it. Use one non-directional net color for both signs; preserve sign through geometry and explicit plus/minus values. Render call/put headings in neutral text.

Replace standalone "Net," "Gross," "Call wall," "Put wall," and "Dominant" with model-bounded labels. The smallest faithful set is:

- "MODEL NET*" or "CALL-MINUS-PUT MODEL"
- "CALL+PUT MODELED MAGNITUDE"
- "Largest call-contract magnitude strike"
- "Largest put-contract magnitude strike"
- "Largest raw-strike |model net|"

The adjacent, not remote, qualifier must say: "Configured call-plus / put-minus convention; participant and dealer positioning are not measured."

R4 - REQUIRED - Define bin semantics and raw-anchor reconciliation exactly.

A 25-point bin can create apparent cancellation across different strikes. Raw 7700 is -0.92B, while the 7700 bin becomes +0.03B after neighboring strikes are aggregated. Therefore a thin net bar means only "near-balanced aggregate modeled magnitudes within this 25-point interval."

Define bins as half-open intervals `[b - 12.5, b + 12.5)`, with an exact upper-half boundary assigned to the higher bin. The claim that no half-bin tie is possible is false at the producer-contract level: the parser permits three-decimal strikes and enforces no 5-point grid.

C/P/D remain raw-strike anchors. Their legend must say "raw-strike anchor placed in containing 25-point bin," preferably including the raw strike in accessible text. Otherwise the marker falsely appears to identify the bin-level maximum.

R5 - REQUIRED - Strengthen window and outlier disclosure.

"80% within window" does not identify the denominator or admit what is hidden. Use: "WINDOW SHOWS 80% OF CHAIN CALL+PUT MODELED MAGNITUDE; 20% OUTSIDE."

If the material-outlier list is capped, disclose both counts: "6 of 9 outside bins at or above 2% shown; 3 more." This handles far-dominant, multiple-outlier, asymmetric, shifted-spot, and distributed sub-threshold cases. The shifted-spot evidence falls to 34% in-window, so a quiet percentage plus six rows is not sufficient.

R6 - REQUIRED - Resolve settlement contamination before profile display.

The proposed 24-hour freshness contract permits a post-close profile containing 504 expired same-day contracts and 14.8B, or 2.5%, of chain modeled magnitude. This is not confined to the existing 0DTE number; it contaminates the ladder, chain total, window coverage, scaling, and anchors.

As proposed, this is a required precursor. A safely separable alternative is an explicit profile-only validity gate based on the provider observation timestamp and same-day per-root presence. A 16:00 ET-only guard handles the observed PM-settled contamination but does not resolve AM-settled SPX during the session. A conservative v0 may suppress the profile for the relevant observation whenever same-day SPX rows cannot be established as unsettled, and suppress after 16:00 ET when any same-day rows remain. Do not call the current 24-hour surface "intraday only."

R7 - REQUIRED - Make expiry/root aggregation visible and bounded.

All-expiry summation is dimensionally legitimate because each row is the same instantaneous modeled-gamma-notional unit. SPX and SPXW also share the SPX strike coordinate. The display must nevertheless say:

"All expirations combined; expiry mix hidden. SPX and SPXW combined; AM/PM settlement timing not modeled."

"All expirations; SPX+SPXW" is too terse for a phone surface because the different settlement mechanics directly affect whether same-day rows remain valid.

R8 - REQUIRED - Use a deterministic reconciliation carrier and fail coherently.

Construct sorted union-strike arrays first, filling absent sides with 0.0. Compute `gex_total_1pct_usd` from those exact arrays in their serialized order, preferably with the same `math.fsum` expression used by validation. After a JSON round trip, require exact equality to the recomputed total. Recompute wall/dominant strikes from those arrays with the existing lowest-strike tie rule. Do not use a broad `isclose`.

An absent `by_strike` block is compatible with an old producer and omits only the profile. A locally malformed block may also suppress only the profile. However, if a present domain-valid block disagrees with the core total or C/P/D anchors, the whole card must suppress: that conflict makes the existing core fields untrustworthy.

3. RECOMMENDED FINDINGS

- RECOMMENDED - Carry OCC strike mills into binning, using `((strike_mills + 12500) // 25000) * 25000`. This eliminates unnecessary float-boundary dependence. If floats remain serialized, validate that each producer strike converts exactly to admitted strike mills before binning.

- RECOMMENDED - Test the mobile surface without hover. SVG `<title>` is not reliably discoverable on a phone. Each bar should have accessible text containing bin interval, call magnitude, put magnitude, and model net.

- RECOMMENDED - Test the profile against an ordinary intraday sample, the 13:10 PT workflow observation, and a standard-monthly expiration day. The available evidence is post-close and cannot validate claimed intraday usefulness or AM-settlement behavior.

- RECOMMENDED - Keep all 809 producer strikes, including zero-magnitude strikes, because that is the exact existing intermediate and preserves the admitted strike domain. Removing the 140 zero-magnitude strikes does not change nonzero sums or argmaxes, but it weakens the carrier's exact-intermediate claim without a product benefit.

- RECOMMENDED - State that the window recenters in 25-point steps as spot crosses a half-bin boundary. Otherwise entry and exit of edge bins between runs can look like a change in underlying structure.

4. ATTACK MATRIX (Q1..Q10 plus Helm A..K, each with disposition + one-line evidence)

Q1 - NARROWED - REQUIRED - Per-contract and side arithmetic is faithful, but dict-order versus sorted-array sums are not exact by construction, and 25-point aggregation changes raw 7700 from -0.92B to bin +0.03B.

Q2 - NARROWED - REQUIRED - Wide magnitude plus thin model net honestly exposes arithmetic balance at 8000 and 7700, but it neither proves participant offset nor identifies economically neutral financing.

Q3 - CONFIRMED - REQUIRED - Red/blue directional bars, colored call/put headings, spot geometry, and C/P/D markers make the configured sign look like measured directional positioning.

Q4 - NARROWED - REQUIRED - Cross-expiry addition is dimensionally valid, but "all expirations" must say combined and hidden-mix, and expired same-day rows make the current 24-hour surface invalid.

Q5 - NARROWED - REQUIRED - SPX and SPXW share a strike coordinate, so addition is not a mapping error; AM/PM settlement makes the root aggregation materially less reliable around expiration.

Q6 - CONFIRMED - REQUIRED - A fixed crop can show only 34% after the tested spot shift, while the six-item cap and 2% threshold hide location and amount unless outside mass and list counts are explicit.

Q7 - CONFIRMED - REQUIRED - "Gross," "Net," "wall," "Dominant," "within window," and unqualified C/P/D ordinarily communicate stronger exposure or level claims than the quantities establish.

Q8 - NARROWED - REQUIRED - Spot is inside the center bin by construction, but the packet's example calling 7750 the widest bin is false; 8000 is widest at 72.57B versus 47.53B, while the common side scale itself is honest.

Q9 - NARROWED - REQUIRED - Binning, call+put magnitude, and outlier selection are new derived semantics and need explicit provenance; the additive optional field does not itself require schema v2.

Q10 - NARROWED - REQUIRED - The strongest no-ship case is a trader reading the widest bar as an actionable dealer level; the proposal survives only with the finite corrections above.

A - FALSIFIED - REQUIRED - Matched aggregate call/put OI and identical model gamma cannot establish a box, financing intent, common ownership, trade pairing, or the box's other strike legs.

B - NARROWED - REQUIRED - `call + abs(put)` is useful modeled magnitude, but "gross exposure" and participant offset are unsupported; no additional v0 quantity is necessary.

C - CONFIRMED - REQUIRED - Calls +1 / puts -1 is configured arithmetic, and the proposed red/blue encoding creates unacceptable dealer-gamma and bullish/bearish implications.

D - NARROWED - REQUIRED - Twenty-five-point bins are acceptable for an overview but structurally lose 5-point location and can net different strikes; exact half-bin and raw-marker rules are missing.

E - CONFIRMED - REQUIRED - Far, multiple, asymmetric, shifted, and distributed sub-2% structure can be hidden; a denominator-free "% within window" is insufficient.

F - NARROWED - REQUIRED - All-expiry aggregation is a legitimate descriptive instantaneous sum, but only under explicit combined/hidden-mix labeling and a settlement-valid snapshot.

G - NARROWED - REQUIRED - SPX+SPXW addition is strike-aligned, but the profile magnifies the existing AM/PM caveat enough that it must be visible and enforced at the validity seam.

H - CONFIRMED - REQUIRED - The 2026-09-03 post-close sample contains 504 already-expired contracts and 14.8B modeled magnitude; the proposed profile has no boundary preventing their display.

I - NARROWED - REQUIRED - Schema v1 is wire-compatible in both directions, but a present profile that contradicts core totals or anchors must suppress the whole card, not only the profile.

J - CONFIRMED - REQUIRED - Existing dict insertion order and proposed sorted serialization can differ by floating summation order; one canonical ordered carrier permits exact reconciliation without a loose tolerance.

K - CONFIRMED - REQUIRED - Most proposed labels are materially stronger than the data; only an explicitly model-bounded, combined, settlement-qualified vocabulary is acceptable.

5. NET-OVER-GROSS VERDICT (faithful / misleading / conditionally acceptable)

CONDITIONALLY ACCEPTABLE.

The representation faithfully shows two facts at once: the magnitude of call-contract and put-contract modeled contributions, and their configured call-minus-put arithmetic. At 8000 it prevents net-only from hiding 71.00B of modeled magnitude; at the 7700 bin it prevents +0.03B from falsely reading as "nothing there."

It becomes misleading if called dealer gross, participant exposure, true cancellation, offsetting positions, or economic neutrality. The wide neutral extent must mean only "call+put modeled magnitude in this bin." The thin overlay must mean only "small call-minus-put model net in this bin."

6. 25-POINT / 31-BIN VERDICT

Twenty-five-point bins are structurally lossy but acceptable for a phone overview. They aggregate five observed 5-point strikes per ordinary bin, discard within-bin location, and can manufacture a near-zero bin net from opposing model contributions at different strikes. They must never be described as exact levels or same-strike cancellation.

The exact bin contract must be `[b - 12.5, b + 12.5)`, upper boundary to the higher bin. Integer strike-mill arithmetic is preferred.

The 31-bin window is acceptable only with explicit shown-versus-outside modeled magnitude and uncensored outlier counts. The current "n% within window" wording is insufficient. Window recentering is deterministic but can make edge structure appear or disappear between runs.

7. ALL-EXPIRY + SPX/SPXW VERDICT

Conditionally acceptable as a descriptive aggregate.

All expirations have the same instantaneous output unit, so summation is not an arithmetic category error. No expiry-facet architecture is required for v0. The surface must state that expirations are combined and that the expiry mix is hidden.

SPX and SPXW share the SPX strike coordinate, so no SPY-style mapping error exists. Their different settlement mechanics become a material validity problem near expiration, not a strike-alignment problem. The visible label must state that AM/PM settlement timing is not modeled.

8. POST-CLOSE 0DTE DISPOSITION (blocking / precursor / separable / other)

PRECURSOR AS CURRENTLY PROPOSED.

The profile must not ship with the proposed 24-hour freshness behavior because expired same-day rows contaminate every profile quantity. This is not a fundamental-model BLOCKING finding, but it is a required pre-ship correction.

It becomes separable only if GEX-4 explicitly adopts a profile-only observation/session validity gate. "Intraday only" is not presently true, and a 16:00 ET guard alone does not solve AM-settled SPX contamination during regular hours.

9. SCHEMA VERSION VERDICT (v1 additive / v2 required)

V1 ADDITIVE.

Old producer to new consumer is safe because absent `by_strike` leaves the existing card and omits the profile. New producer to old consumer is safe because the current consumer reads required keys and ignores extras. The artifact is run-local and producer/consumer deploy together.

V2 is not required for wire compatibility. The governing schema documentation must explicitly define `by_strike` as an optional v1 extension for consumers and always emitted by the new producer. Reconciliation disagreement with existing core fields is a whole-card integrity failure.

10. LABEL / COLOR VERDICT

REJECT THE CURRENT LABEL AND COLOR SET.

Acceptable with these minimum replacements:

- "Gross" -> "CALL+PUT MODELED MAGNITUDE"
- "Net" -> "MODEL NET*" or "CALL-MINUS-PUT MODEL"
- "call-side" -> "CALL-CONTRACT MAG"
- "put-side" -> "PUT-CONTRACT MAG"
- "Dominant" -> "Largest raw-strike |model net|"
- "Call wall" -> "Largest call-contract magnitude strike"
- "Put wall" -> "Largest put-contract magnitude strike"
- "within window" -> "of chain call+put modeled magnitude shown"
- "all expirations" -> "all expirations combined; expiry mix hidden"
- "SPX+SPXW" -> "SPX and SPXW combined; AM/PM settlement timing not modeled"
- C/P/D -> "raw-strike anchors placed in containing 25-point bin"
- "SPX <value>" -> "SPX cash spot <value>"

Use neutral text for both option sides and one non-directional overlay color for positive and negative model net. Preserve sign using left/right geometry and printed plus/minus values. Red versus blue is not acceptable here.

11. STRONGEST REASON NOT TO SHIP

The widest gray bar plus C/P markers at 8000 will look like the strongest actionable dealer-gamma level on a phone, even though the evidence establishes only large, near-balanced aggregate call/put OI-gamma magnitudes and cannot identify ownership, strategy, true position signs, participant-level offset, or hedging behavior.

That false precision is amplified by a spot-centered ladder, directional colors, loaded "wall" language, mixed expirations, mixed settlement mechanics, and post-close expired contracts. A footnote is too weak to reverse the first-glance claim.

12. MINIMUM CORRECTION SET (if one exists)

1. Delete every box/financing/strategy-identity assertion and replace it with the strongest justified matched-magnitude description.

2. Rename net, gross, call/put sides, walls, dominant, C/P/D, coverage, expiry, and root labels as specified above.

3. Replace red/blue directional encoding with a single non-directional net color and neutral side labels.

4. Define exact half-open bin boundaries; state that bin net can cancel across different strikes; identify C/P/D as raw-strike markers mapped into bins.

5. Show both in-window and outside percentages of chain call+put modeled magnitude, plus "shown of total material outliers" when the list is capped.

6. Add a profile validity correction before ship: settlement-aware producer handling, or conservative profile-only suppression based on provider observation time and per-root same-day presence.

7. Canonicalize sorted-array reconciliation with an exact post-JSON invariant; suppress the whole card on total or anchor contradiction.

8. Retain schema v1, but amend the v1 contract to define the optional additive extension and its old/new compatibility behavior.

With these corrections, the leading net-over-gross, 31-by-25-point, all-expiry SPX/SPXW v0 can proceed to design without claiming more than the evidence knows.


```

---

## Appendix - commission prompt as piped to `codex exec` (stdin)

```
You are a fresh-context, read-only, independent adversarial reviewer (Codex HIGH) for Cuttingboard.
Repo: /home/dustin/Projects/cuttingboard. Branch claude/gex-4-product-recon, frozen head e25996425870b871c45db7982870de31af4aa47f. Main a76e7a433174db5d7ceddc6d87078650609dd00e.
Event: GEX-4 EVENT-1 CODEX HIGH ADVERSARIAL REVIEW (quantitative / semantic). NOT a general repository review. Do not edit any file. Emit your entire review on stdout.

START by reading, in this order:
1. audits/gex-4-product-recon-2026-09/GEX_4_CODEX_HIGH_PACKET_2026-09-03.md  (the frozen packet; it contains the current formula, sign convention, admissibility, proposed field, proposed aggregation, selection rule, real rows, the 31-bin table, labels, forbidden claims, and questions Q1-Q10)
2. audits/gex-4-product-recon-2026-09/GEX_4_PRODUCT_RECON_2026-09-03.md  (the recon report; the packet's companion)
Direct repo spot checks are permitted only when necessary to test a packet claim and should be limited to: tools/gex_snapshot.py, cuttingboard/delivery/gex_card.py, docs/prd_history/PRD-306.md, docs/prd_history/PRD-307.md, docs/prd_history/PRD-309.md, and audits/gex-4-product-recon-2026-09/evidence/*. No history archaeology. Do not rediscover the repository.

HELM PRELIMINARY DISPOSITION (not final approval): leading candidate is a NET OVER GROSS SPX STRIKE LADDER - 31 x 25-point bins centered on SPX spot; neutral call-side / put-side gross extent; signed configured-assumption net overlaid; existing C/P/D anchors; explicit within-window coverage; bounded material outlier disclosure; all-expiry v0; 0DTE remains a number; no SPY coordinate mapping; no permission/trade coupling.

PRIMARY REVIEW QUESTION: try to prove that the proposed GEX-4 profile would mislead Dustin (a solo discretionary index trader reading it on a phone). Do not optimize the design. Attack it.

MANDATORY ATTACKS: every question Q1-Q10 in the packet, PLUS Helm attack points A-K:

A. BOX-SPREAD / POSITION-IDENTITY OVERCLAIM. The recon describes the large matched Sep-18 8000 call/put OI as "box-spread financing paper". Attack that statement. Determine what can actually be established from aggregate OI, same strike, same expiration, approximately matched call/put OI, identical provider-model gamma, without trade-level pairing, account identity, or the other legs of a box. Classify the strongest justified description. The design must NOT depend on knowing the actual strategy that generated the OI.

B. NET + GROSS SEMANTICS. Determine whether gross_b = call_b + abs(put_b) is an honest useful descriptive magnitude. Attack whether a wide neutral gross extent with a thin signed net overlay: correctly communicates cancellation; overstates economically meaningful structure when matched spread/financing positions dominate; implies gross dealer exposure; implies those positions actually offset within one participant; or can be made honest through labeling. Use 8000 and 7700 as concrete cases. If another descriptive quantity is required, state exactly why.

C. SIGN CONVENTION. Attack every visual implication of calls +1 / puts -1. The profile must never make the configured convention look like measured dealer inventory. Determine whether blue/red signed net bars themselves create an unacceptable bullish/bearish or long/short-gamma implication. If color or copy must change, identify the smallest correction.

D. 25-POINT BINNING. Attack bin(K) = floor((K + 12.5) / 25) * 25. Check exact half-bin boundaries, fractional strikes if present, floating-point edge behavior, 5-point strike aggregation, information loss, marker reconciliation when C/P/D raw strikes sit within a bin, and whether integer strike-mills should be used instead of float arithmetic. Determine whether 25-point bins are acceptable or structurally lossy.

E. FIXED 31-BIN WINDOW. Attack center +/- 15 bins plus "outside gross >= 2% chain gross, cap 6". Can it systematically hide relevant structure? Attack: far dominant outlier; multiple material outliers; asymmetric chain; low gross chain; shifted spot; dense nearby paper. The rendered "% within window" is intended as the honesty mechanism; determine whether it is sufficient.

F. ALL-EXPIRY AGGREGATION. Attack combining all expirations at each strike. Is it a legitimate descriptive cross-expiry structural profile; materially misleading because long-dated and near-dated gamma/OI have different trading significance; or acceptable only with stronger labeling? Do not propose an expiry-facet architecture merely because it is possible. The question is whether the v0 aggregate is honest enough.

G. SPX + SPXW AGGREGATION. Attack summing SPX and SPXW at the same strike (AM vs PM settlement, same-day treatment, different expiration mechanics). Does the existing aggregation remain defensible for the profile, or does the visual surface make an existing caveat materially more important?

H. POST-CLOSE SAME-DAY CONTRACT CONTAMINATION. The 2026-09-03 post-close sample still contained 504 contracts expiring that same day, ~2.5% of gross modeled magnitude after their expiration/settlement period; PRD-306's expectation that the numerator becomes zero outside market hours is falsified on expiry days. Determine whether this is (1) BLOCKING for GEX-4; (2) a required precursor correction; (3) safely handled by suppressing the profile after an explicit session boundary; (4) safely separable because GEX-4 acceptance will be intraday only; (5) something else. Be precise. Do not silently redesign the existing producer.

I. SCHEMA VERSION. Attack retaining schema_version == 1 while adding optional by_strike. Consider old producer -> new consumer and new producer -> old consumer. Proposed behavior: old snapshot -> existing card renders, profile absent; new snapshot -> old consumer ignores additive field; new consumer validates the profile independently and suppresses only the profile if by_strike is absent/invalid, unless core-card integrity is affected. Is that genuinely additive-compatible, or does semantic versioning require schema_version 2?

J. FLOAT RECONCILIATION. Attack reconciliation between existing dict insertion-order sums, sorted serialized arrays, recomputed totals, wall/dominant argmaxes, and Python floating arithmetic. Do not accept a test that becomes flaky or requires a tolerance so broad that a real mismatch could pass. Recommend the narrowest deterministic invariant.

K. VISUAL CLAIM STRENGTH. Review every proposed visible label, especially: Gross, call-side, put-side, Net, C / P / D, within window, all expirations, SPX + SPXW. Determine whether each is descriptive enough. Reject any label whose ordinary trader interpretation is materially stronger than the underlying quantity.

EXPLICITLY OUT OF SCOPE: broad Cboe licensing/provider research (a separate owner hold exists). This review is quantitative and semantic.

VERDICT FORMAT. For every attack: CONFIRMED / FALSIFIED / NARROWED with concise evidence. Classify findings BLOCKING / REQUIRED / RECOMMENDED / OPTIONAL. BLOCKING only if the product should not proceed without a different fundamental model or representation. REQUIRED may be repairable through one bounded packet correction.

FINAL RETURN, exactly these headed sections:
GEX-4 CODEX HIGH - EVENT 1
REVIEWED HEAD: <sha>
1. VERDICT (APPROVE / APPROVE WITH REQUIRED EDITS / REJECT-REDESIGN)
2. REQUIRED FINDINGS (exact and finite)
3. RECOMMENDED FINDINGS
4. ATTACK MATRIX (Q1..Q10 plus Helm A..K, each with disposition + one-line evidence)
5. NET-OVER-GROSS VERDICT (faithful / misleading / conditionally acceptable)
6. 25-POINT / 31-BIN VERDICT
7. ALL-EXPIRY + SPX/SPXW VERDICT
8. POST-CLOSE 0DTE DISPOSITION (blocking / precursor / separable / other)
9. SCHEMA VERSION VERDICT (v1 additive / v2 required)
10. LABEL / COLOR VERDICT
11. STRONGEST REASON NOT TO SHIP
12. MINIMUM CORRECTION SET (if one exists)
Plain ASCII only. Do not edit the packet. Do not write files.
```
