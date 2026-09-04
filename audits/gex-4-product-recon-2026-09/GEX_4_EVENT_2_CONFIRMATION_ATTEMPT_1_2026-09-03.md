# GEX-4 Provisional MATERIAL Package - Event 2 Exact-Corrected-Head Confirmation, ATTEMPT 1 (durable record)

- **Event:** EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 s7), attempt 1
- **Reviewer:** Codex (codex-cli 0.150.1), fresh-context independent reviewer, `-s read-only`, `model_reasoning_effort=high`
- **Corrected head under confirmation:** `d85268292b0e298101769d454af5fac33dffe4dc` (PR #309; the ONE consolidated correction after Event 1 under Helm adjudication R1-R8 ACCEPT)
- **Date:** 2026-09-03
- **Verdict:** NOT CONFIRMED - two confirmation defects, both classified by the reviewer as "failure to implement an accepted REQUIRED finding, not a new MATERIAL product boundary"; R1, R4, R5, R6, R7, recommendations, and no-new-MATERIAL-boundary all confirmed YES; checks C0-C2, C4-C7, C9, C10 PASS; C3 and C8 FAIL
- **Tokens used (reported by codex):** 96,835
- **Disposition:** the Event-1 correction budget (one consolidated correction) is spent. No repair was made. Held for Helm: authorize or decline one bounded confirmation repair limited to the two defects below (GEX-1 precedent: `GEX_1_EVENT_2_CONFIRMATION_ATTEMPT_1_2026-08-20.md`, owner-authorized bounded repair, then attempt 2).

Defects as stated by the reviewer:
1. R2/R3 visible vocabulary uses "CALL MAG", "PUT MAG", "LARGEST CALL MAG STRIKE", "LARGEST PUT MAG STRIKE", "LARGEST |MODEL NET| STRIKE" instead of the ruled "CALL MODELED MAGNITUDE", "PUT MODELED MAGNITUDE", "Largest call-contract magnitude strike", "Largest put-contract magnitude strike", "Largest raw-strike |model net|".
2. R8 carrier serializes the put side as the producer's signed non-positive value (`put_gex_1pct_usd <= 0`, model net = call + put) instead of the ruled positive put modeled magnitude (model net = call - put). The fsum exact-reconciliation mechanism itself was confirmed sound.

---

## Verbatim Codex stdout

```
GEX-4 CODEX - EVENT 2 EXACT-HEAD CONFIRMATION

CONFIRMED HEAD: d85268292b0e298101769d454af5fac33dffe4dc

R1 resolved YES - The current design describes only large, near-balanced call-contract and put-contract modeled magnitude, states that multiple strategies may be consistent with it, and identifies none. See GEX_4_PRODUCT_RECON_2026-09-03.md:119-140. Whole-word recon hits for box, financing, footprint, paired, and ownership occur only in the correction mapping, frozen historical description, or forbidden-vocabulary list at lines 24, 40, and 493.

R2 resolved NO - The quantitative definitions correctly bound CALL MAG, PUT MAG, CALL+PUT MODELED MAG, and MODEL NET*, and expressly deny economic offset, participant cancellation, dealer exposure, and true-gamma sign at GEX_4_PRODUCT_RECON_2026-09-03.md:227-255. However, the visible vocabulary still uses "CALL MAG" and "PUT MAG" rather than Helm's ruled "CALL MODELED MAGNITUDE" and "PUT MODELED MAGNITUDE": recon lines 454-481 and proto_corrected_ladder.html:7-17,209-246. The adjacent qualifier defines the arithmetic but does not expand either side label to modeled magnitude.

R3 resolved NO - The color correction passes: the design specifies one non-directional treatment, neutral headings, sign by side of zero and explicit +/- value, and no red/blue/status colors at GEX_4_PRODUCT_RECON_2026-09-03.md:194-201,484-486. The prototype uses only grayscale CSS/SVG colors and contains no whole-word wall, dominant, gross, red, blue, bullish, or bearish label. But the ruled anchor labels were not adopted exactly: "LARGEST CALL MAG STRIKE", "LARGEST PUT MAG STRIKE", and "LARGEST |MODEL NET| STRIKE" at recon lines 454-468 and prototype lines 8-10 omit the required call-contract, put-contract, and raw-strike bounded wording. The marker legend repeats the shortened meanings at prototype line 243.

R4 resolved YES - Integer strike mills, formula ((strike_mills + 12500) // 25000) * 25000, interval [b-12.5,b+12.5), exact upper-boundary assignment to the higher bin, preservation of admitted raw strikes, and cross-strike near-balance semantics are specified at GEX_4_PRODUCT_RECON_2026-09-03.md:261-274. Raw anchors are placed in their containing bin and explicitly denied bin-maximum meaning at lines 298-301 and prototype lines 243-244. The 8000 widest-bin correction is stated at recon lines 171-174.

R5 resolved YES - The 31-bin spot-centered window and 25-point half-boundary recentering are specified at GEX_4_PRODUCT_RECON_2026-09-03.md:276-281. Both in-window and outside percentages name chain CALL+PUT MODELED MAG as denominator at lines 283-285. The 2 percent threshold, capped N of M wording, K more disclosure, and uncapped accessible list are specified at lines 287-293. The prototype visibly shows both percentages at proto_corrected_ladder.html:14 and recentering at line 244.

R6 resolved YES - The three ordered rules are present at GEX_4_PRODUCT_RECON_2026-09-03.md:331-345: same-day admitted SPX rows suppress the profile all day; at or after 16:00 ET same-day admitted SPXW rows suppress it; otherwise the carrier is emitted. The rule is profile-only and leaves the existing core total, anchors, card, and 0DTE semantics unchanged at lines 324-332,347-356. The deterministic typed-unavailable shape is the minimal {"reason":"<token>"} without arrays at lines 372-384. This uses only admitted rows, which are the rows capable of entering the profile carrier.

R7 resolved YES - Adjacent visible copy states "ALL EXPIRATIONS COMBINED, EXPIRY MIX HIDDEN. SPX+SPXW COMBINED, AM/PM SETTLEMENT NOT MODELED." at GEX_4_PRODUCT_RECON_2026-09-03.md:324-329 and proto_corrected_ladder.html:245. The compressed plus sign does not weaken either combined-root or unmodeled-settlement fact.

R8 resolved NO - Sorting, ascending strike mills, absent-side zeroes, all admitted and zero-magnitude strikes, exact post-JSON reconciliation, lowest-strike anchor recomputation, schema v1, and the absent/malformed/contradicting compatibility ladder are otherwise present at GEX_4_PRODUCT_RECON_2026-09-03.md:358-413. However, Helm ruled a carrier of call magnitude and put magnitude. The proposed carrier instead serializes the put side as a non-positive signed contribution: recon lines 234-239 and 375-380 explicitly specify put_gex_1pct_usd <= 0. Consequently its model-net expression is call[i] + put[i] at lines 388-395, rather than call magnitude minus positive put magnitude.

The proposed math.fsum reconciliation itself is genuinely order-independent for the finite same-sign arrays in this Python producer/consumer domain, and Python JSON serialization round-trips each binary float exactly. Using the identical expression on both sides therefore supports exact equality after the JSON round trip; no isclose is proposed. That validates the reconciliation mechanism, but it does not cure the carrier's signed-put semantic mismatch.

Recommendations adopted as ruled YES - Integer strike mills are adopted at GEX_4_PRODUCT_RECON_2026-09-03.md:261-270; all admitted strikes including zero-magnitude strikes at lines 360-363; recentering disclosure at lines 276-281 and prototype line 244; non-hover accessibility at recon lines 212-217 and prototype lines 19-205,209-242; and ordinary intraday, 13:10 PT, and monthly-expiration live validation is recorded without being made universally pre-build at recon lines 548-551. Historical prototypes are marked HISTORICAL / SUPERSEDED and the corrected prototype is identified as current at evidence/README.md:3-9.

NEW MATERIAL boundary NO - The correction adds no provider, fetch, package, workflow, renderer/CSS change, SPY mapping, signal, permission coupling, or core-card semantic change. See GEX_4_PRODUCT_RECON_2026-09-03.md:415-450. Relabeling the existing core rows is text-only at lines 423-430 and 452-459 and is directly required by Helm R3 while preserving the R6 core semantics; it does not need a new Helm semantic call. Normal MATERIAL PRD and Gate authority remains required before implementation, as already recorded at lines 445-448 and 553-558.

CHECKS C0-C10: PASS/FAIL each with citation

C0 PASS - "git rev-parse HEAD" returned "d85268292b0e298101769d454af5fac33dffe4dc"; "git branch --show-current" returned "claude/gex-4-product-recon"; final "git status --short" exited 0 with empty output.

C1 PASS - "git diff --exit-code 1b14f3c HEAD -- audits/gex-4-product-recon-2026-09/GEX_4_EVENT_1_CODEX_REVIEW_2026-09-03.md" exited 0 with empty output. "git diff --exit-code e259964 HEAD -- audits/gex-4-product-recon-2026-09/GEX_4_CODEX_HIGH_PACKET_2026-09-03.md" exited 0 with empty output. Historical handling is also declared at GEX_4_PRODUCT_RECON_2026-09-03.md:38-48.

C2 PASS - Whole-word grep produced only GEX_4_PRODUCT_RECON_2026-09-03.md:24,40,493, respectively the correction mapping, explicit frozen/superseded description, and forbidden-vocabulary list. The operative description at lines 119-140 identifies no strategy, pairing, ownership, or participant.

C3 FAIL - The prototype passes the palette and forbidden-noun portions: proto_corrected_ladder.html:1-3,15-18 uses grayscale colors, and the whole-word forbidden-label grep returned no matches. The model-net sign is shown through geometry and explicit values at lines 19-205. The visible labels nevertheless use unbounded "CALL MAG"/"PUT MAG" and shortened anchor labels at lines 7-17,209-246 instead of Helm's ruled model-bounded side and anchor wording. Event-1 required the bounded labels at GEX_4_EVENT_1_CODEX_REVIEW_2026-09-03.md:48-60.

C4 PASS - Integer mills, formula, half-open intervals, exact upper-boundary rule, and raw-strike preservation are at GEX_4_PRODUCT_RECON_2026-09-03.md:261-274; raw-anchor semantics are at lines 298-301 and prototype lines 243-244; the 8000 widest-bin correction is at recon lines 171-174.

C5 PASS - Centering and recentering are at GEX_4_PRODUCT_RECON_2026-09-03.md:276-281; in/out denominator disclosure and capped N of M/K more wording are at lines 283-293; visible prototype examples are at proto_corrected_ladder.html:14,209,244.

C6 PASS - The exact ordered profile-only rules and reason tokens are at GEX_4_PRODUCT_RECON_2026-09-03.md:331-345; fail-closed scope and no invented settlement precision are at lines 347-353; typed unavailability is at lines 372-384. Existing core semantics are expressly unchanged at lines 324-332,355-356.

C7 PASS - Both required facts are adjacent in GEX_4_PRODUCT_RECON_2026-09-03.md:324-329 and visibly present at proto_corrected_ladder.html:245.

C8 FAIL - The canonicalization, exact fsum reconciliation, anchor checks, compatibility ladder, and schema v1 posture are at GEX_4_PRODUCT_RECON_2026-09-03.md:358-413. The carrier violates Helm's positive put-magnitude contract by serializing put_gex_1pct_usd <= 0 at lines 375-380 and using call[i] + put[i] at lines 388-395. The fsum expression itself provides deterministic exact producer/consumer reconciliation after Python JSON float round-trip; the failure is the carrier's ruled semantic shape.

C9 PASS - The design expressly rejects reliance on SVG title hover and requires a table plus per-row aria-labels at GEX_4_PRODUCT_RECON_2026-09-03.md:212-217. The prototype contains 31 SVG bin groups with bin, interval, call magnitude, put magnitude, and model net in aria-label text at proto_corrected_ladder.html:19-205, followed by the 31-bin plus outside-bin textual table at lines 209-242. There is no SVG title element.

C10 PASS - No new provider, dependency, fetch, workflow, renderer/CSS change, SPY mapping, signal, permission coupling, or core semantic change is introduced; GEX_4_PRODUCT_RECON_2026-09-03.md:415-450. Core-row relabeling is text-only and within Helm's R3/R6 ruling at lines 423-430,452-459.

VERDICT: NOT CONFIRMED

Confirmation defects:

1. MATERIAL TO CONFIRMATION - R2/R3 visible-vocabulary mismatch. The current candidate and corrected prototype retain "CALL MAG", "PUT MAG", "LARGEST CALL MAG STRIKE", "LARGEST PUT MAG STRIKE", and "LARGEST |MODEL NET| STRIKE". These do not implement Helm's ruled "CALL MODELED MAGNITUDE", "PUT MODELED MAGNITUDE", "Largest call-contract magnitude strike", "Largest put-contract magnitude strike", and "Largest raw-strike |model net|" vocabulary. This is a failure to implement accepted REQUIRED findings, not a new MATERIAL product boundary.

2. MATERIAL TO CONFIRMATION - R8 carrier-shape mismatch. The current candidate serializes puts as signed non-positive gex contributions and computes per-strike model net with addition. Helm ruled a carrier containing positive put modeled magnitude, for which model net is call magnitude minus put magnitude. The exact reconciliation mechanism is sound, but it reconciles the wrong ruled carrier representation. This is a failure to implement an accepted REQUIRED finding, not a new MATERIAL product boundary.
```

---

## Appendix - confirmation prompt as piped to `codex exec` (stdin)

```
You are a fresh-context, read-only, independent reviewer (Codex) for Cuttingboard.
Repo: /home/dustin/Projects/cuttingboard. Branch claude/gex-4-product-recon. EXACT CORRECTED HEAD under confirmation: d85268292b0e298101769d454af5fac33dffe4dc. Do not edit any file. Emit your entire result on stdout, plain ASCII.

Event: GEX-4 EVENT 2 - EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 s7). This is NOT a fresh design review and NOT an optimization cycle. It answers only whether the ONE consolidated correction at the exact head resolves the Event-1 REQUIRED findings as adjudicated by Helm, whether the ruled recommendations were adopted, and whether the correction introduced any NEW MATERIAL boundary.

Read, in this order:
1. audits/gex-4-product-recon-2026-09/GEX_4_EVENT_1_CODEX_REVIEW_2026-09-03.md  (Event-1 findings R1-R8 and the 5 recommendations; the "Verbatim Codex stdout" section is the authority for what each finding demanded)
2. audits/gex-4-product-recon-2026-09/GEX_4_PRODUCT_RECON_2026-09-03.md  (the corrected current candidate design; section 0 is the author's R1-R8 mapping - verify it, do not trust it)
3. audits/gex-4-product-recon-2026-09/evidence/README.md and evidence/proto_corrected_ladder.html (corrected prototype; verify no red/blue hue and the visible labels)
Spot checks permitted only to test a claim: tools/gex_snapshot.py, cuttingboard/delivery/gex_card.py, docs/prd_history/PRD-306.md, docs/prd_history/PRD-309.md. Confirm the head with `git rev-parse HEAD` and `git status --short` (must be clean). No history archaeology.

HELM ADJUDICATION that this correction had to implement:
R1 ACCEPT - remove/supersede all box spread / synthetic financing / financing paper / footprint / known paired position / common ownership / known strategy identity language from the current design; strongest allowed: "large, near-balanced call-contract and put-contract modeled magnitude at the same strike / interval"; may be consistent with multiple strategies, none identified.
R2 ACCEPT - replace unqualified Net / Gross / cancellation / offset / two-sided position with: CALL MODELED MAGNITUDE, PUT MODELED MAGNITUDE, CALL+PUT MODELED MAGNITUDE (= call + |put|), MODEL NET* (= call - put under the configured call-plus / put-minus convention); adjacent qualifier "Configured call-plus / put-minus convention; participant and dealer positioning are not measured"; a thin model-net bar means only that aggregated call and put modeled magnitudes inside the bin are near-balanced under the configured arithmetic; no economic offset / participant cancellation claim.
R3 ACCEPT - drop blue-positive / red-negative; one non-directional net treatment for both signs; sign via position relative to zero and explicit +/- value; neutral call/put headings; no bullish/bearish colors; loaded anchor labels replaced with model-bounded descriptions (MODEL NET*, CALL+PUT MODELED MAGNITUDE, Largest call-contract magnitude strike, Largest put-contract magnitude strike, Largest raw-strike |model net|); C/P/D may stay as compact markers only with a nearby legend giving the full bounded meanings.
R4 ACCEPT - integer strike mills; bin = ((strike_mills + 12500) // 25000) * 25000, interval [b-12.5, b+12.5), exact upper boundary to the higher bin; preserve every admitted raw strike; C/P/D are RAW-STRIKE anchors displayed in the containing bin and NOT the bin maximum, stated in accessible text/legend; correct the packet defect: 8000, not 7750, is the widest example bin.
R5 ACCEPT - keep 31 x 25-pt bins centered on the containing SPX spot bin; show BOTH in-window and outside-window percentages of chain CALL+PUT MODELED MAGNITUDE; outside threshold 2% of chain modeled magnitude; if capped disclose "N of M qualifying outside bins shown, K more"; never silently cap; state that the window recenters in 25-point steps at half-bin boundaries.
R6 ACCEPT WITH NARROW BOUNDARY - do NOT redesign the existing core GEX card; the profile gets its own fail-closed validity: (1) any SAME-DAY SPX-root rows in the observation -> profile unavailable; (2) observation time >= 16:00 ET and SAME-DAY SPXW rows remain -> profile unavailable; (3) otherwise the optional carrier may be emitted; core total / wall / dominant / 0DTE semantics unchanged; prefer omitting the carrier on invalid observations; a minimum typed availability/reason shape may be proposed; no invented settlement precision.
R7 ACCEPT - visible adjacent copy must communicate "All expirations combined; expiry mix hidden. SPX and SPXW combined; AM/PM settlement timing not modeled." compressed for phone without weakening; no implication that the ladder is expiration-specific.
R8 ACCEPT - one canonical sorted union-strike carrier (strike, call magnitude, put magnitude; absent side 0.0; ALL admitted strikes incl. zero-magnitude; strictly ascending); core total computed from that carrier with the same deterministic math.fsum expression used for validation; after JSON round trip: exact total reconciliation, exact call/put/dominant anchor recomputation, lowest-strike tie preserved; no broad isclose; compatibility: ABSENT carrier -> card valid, profile absent; MALFORMED without core contradiction -> profile suppresses; PRESENT + domain-valid but contradicting core total or anchors -> WHOLE CARD suppresses; schema_version remains 1 unless a concrete wire-compatibility failure is proven.
ACCESSIBILITY (adopted recommendation) - no reliance on SVG <title> hover; each rendered bin has accessible textual content with bin/interval, call magnitude, put magnitude, model net; the visual may stay compact.
ARTIFACT HANDLING - Event-1 record NOT rewritten; the frozen Event-1 packet stays historical and unedited; superseded prototypes/evidence marked HISTORICAL / SUPERSEDED in the current recon rather than a rebuilt gallery.
RECOMMENDATIONS ruled: strike-mills adopted; accessibility adopted; keep all 809 admitted strikes adopted; recentering statement adopted; live validation (intraday sample, 13:10 PT observation, monthly-expiration day) RECORDED but not all pre-build blockers.

Checks you must perform (each PASS / FAIL with a file:line or quoted-line citation):
- C0 head is d85268292b0e298101769d454af5fac33dffe4dc and tree clean.
- C1 GEX_4_EVENT_1_CODEX_REVIEW_2026-09-03.md and GEX_4_CODEX_HIGH_PACKET_2026-09-03.md are byte-unchanged since commit 1b14f3c and e259964 respectively (`git diff 1b14f3c HEAD -- <path>` empty for both).
- C2 no current-design text in the recon asserts a strategy identity (grep the recon for box, financing, footprint, paired, ownership; any hit must be inside the explicitly historical/superseded/forbidden context).
- C3 the recon's visible vocabulary (section 12) and the corrected prototype use only model-bounded labels; the prototype HTML contains no red/blue hex or directional color and no "wall"/"dominant"/"gross" label.
- C4 bin contract uses integer mills, half-open interval, upper boundary to higher bin; raw-anchor legend present; 8000-widest correction stated.
- C5 coverage shows in and out percentages with the denominator named; capped-list wording with N of M and K more; recentering statement present.
- C6 R6 rule (1)(2)(3) present exactly, fail-closed, profile-only, core card untouched; typed unavailable carrier shape minimal and deterministic.
- C7 R7 copy present adjacent and both facts intact.
- C8 R8 carrier + fsum exact reconciliation + compatibility ladder (absent / malformed / contradicting -> whole card) + schema v1 stated; note whether the proposed fsum expression is genuinely order-independent and exact after JSON round trip.
- C9 accessibility: full-bin textual table specified and present in the prototype; no hover reliance.
- C10 no NEW MATERIAL boundary introduced by the correction (e.g., a new provider, dependency, workflow, renderer/CSS change, SPY mapping, signal, permission coupling, a core-card semantic change); note if relabeling the existing core rows (text-only) is within Helm's R3/R6 boundary or needs a Helm call.

FINAL RETURN, exactly these headed sections:
GEX-4 CODEX - EVENT 2 EXACT-HEAD CONFIRMATION
CONFIRMED HEAD: <sha> (or NOT CONFIRMED)
R1 resolved YES/NO - evidence
R2 resolved YES/NO - evidence
R3 resolved YES/NO - evidence
R4 resolved YES/NO - evidence
R5 resolved YES/NO - evidence
R6 resolved YES/NO - evidence
R7 resolved YES/NO - evidence
R8 resolved YES/NO - evidence
Recommendations adopted as ruled YES/NO - evidence
NEW MATERIAL boundary YES/NO - evidence
CHECKS C0-C10: PASS/FAIL each with citation
VERDICT: CONFIRMED / NOT CONFIRMED (list every confirmation defect exactly; classify each as material or non-material to the confirmation)
Do not propose design optimizations. Do not edit files.
```
