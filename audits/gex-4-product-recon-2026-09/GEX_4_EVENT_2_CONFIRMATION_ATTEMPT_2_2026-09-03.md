# GEX-4 Provisional MATERIAL Package - Event 2 Exact-Corrected-Head Confirmation, ATTEMPT 2 (durable record)

- **Event:** EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 s7), attempt 2, after the Helm-authorized bounded repair limited to the two attempt-1 defects
- **Reviewer:** Codex (codex-cli 0.150.1), fresh-context independent reviewer, `-s read-only`, `model_reasoning_effort=medium` (narrow confirmation, not a design review)
- **Repair head under confirmation:** `f3833a4e54a7db69f61d3a4bfd8fa7d4f8bc6ad6` (PR #309), repairing corrected MATERIAL head `d852682`
- **Evidence handed to the reviewer:** review_prep v0 report for d852682..f3833a4 (`tools/review_prep.py --diff`), the exact recon diff, the attempt-1 record, the Event-1 record, the current recon, the current prototype
- **Date:** 2026-09-03
- **Tokens used (reported by codex):** 85,756
- **Verdict:** NOT CONFIRMED - one residual defect: the outside-bin line labels its model-net value "NET <y>B" in recon section 12 and "model net" in the prototype instead of the exact ruled "MODEL NET*". B (R3 anchors + non-directional), C (positive carrier, ruled field names), D (model net = call - put), E (pinned fsum reconciliation coherent), G (schema v1 additive) = YES; F (regression) = NO; H (new MATERIAL boundary) = NO; SCOPE CHECK = YES.
- **Disposition:** no further repair started (charge: "Do not begin another repair automatically"). Held for Helm: authorize the one-string fix ("NET" -> "MODEL NET*" on the outside-bin line in recon section 12 lines 517-519 and prototype generator/HTML) and an attempt-3 confirmation, or rule the residual immaterial.

---

## Verbatim Codex stdout

```
GEX-4 CODEX - EVENT 2 ATTEMPT 2 EXACT-HEAD CONFIRMATION
CONFIRMED HEAD: f3833a4e54a7db69f61d3a4bfd8fa7d4f8bc6ad6
A. R2 exact quantity vocabulary now resolved NO - GEX_4_PRODUCT_RECON_2026-09-03.md:517-519 specifies the visible outside-bin value as "NET <y>B", and proto_corrected_ladder.html:209 renders "model net -1.7B", not the exact ruled "MODEL NET*".
B. R3 exact anchor vocabulary + non-directional semantics resolved YES - GEX_4_PRODUCT_RECON_2026-09-03.md:491-516 and proto_corrected_ladder.html:8-10,15-17,243-246 contain the exact anchor labels and qualifier; lines 129-139 show both signs with the same grayscale treatment, geometry, and explicit +/- values.
C. R8 carrier stores positive call and put modeled magnitudes (field names as ruled; no signed-negative put; not named put_gex_1pct_usd) YES - GEX_4_PRODUCT_RECON_2026-09-03.md:374-408 requires both sides >= 0, names call_modeled_magnitude_1pct_usd and put_modeled_magnitude_1pct_usd, and expressly forbids put_gex_1pct_usd and signed-negative put values.
D. MODEL NET is exactly call magnitude - put magnitude YES - GEX_4_PRODUCT_RECON_2026-09-03.md:409-410 states "model_net(K) = call_modeled_magnitude(K) - put_modeled_magnitude(K)".
E. canonical fsum / anchor reconciliation is internally coherent (pinned expression, same operand order on both sides, exact after JSON round trip, anchors incl. DOMINANT from call - put, whole-card suppression on contradiction) YES - GEX_4_PRODUCT_RECON_2026-09-03.md:374-443 specifies the ascending union carrier, flattened c(K),-p(K) fsum order for producer and both validations, exact post-JSON equality, carrier-derived anchors with lowest-strike ties, DOMINANT from abs(call-put), and whole-card suppression.
F. previously confirmed R1/R4/R5/R6/R7 regressed NO - git diff 006f93b..HEAD changes only the candidate recon and corrected prototype/generator, and repair_recon.diff shows only authorized vocabulary/carrier substitutions and the directly required prototype update in those previously confirmed areas.
G. schema_version 1 additive compatibility remains valid YES - GEX_4_PRODUCT_RECON_2026-09-03.md:397 and 435-448 retain schema_version 1 and define absent-carrier and old/new-consumer compatibility for the additive by_strike extension.
H. new MATERIAL boundary introduced NO - git diff 006f93b..HEAD contains only the recon, static corrected prototype, and its generator; no provider, dependency, fetch, workflow, production renderer/CSS, SPY mapping, signal, permission, or core-card semantic change is introduced.
SCOPE CHECK - YES - git diff d852682..f3833a4 contains the attempt-1 durable record plus the candidate recon, corrected prototype, and prototype generator; the attempt-1 record is byte-unchanged from 006f93b, and the two frozen Event-1 artifacts are byte-unchanged from d852682.
VERDICT: NOT CONFIRMED - exact residual defect: the outside-bin visible quantity remains shortened to "NET" in the section-12 contract and "model net" in the prototype instead of the Helm-authorized exact label "MODEL NET*".
```

---

## Appendix - confirmation prompt as piped to `codex exec` (stdin)

```
You are a fresh-context, read-only, independent reviewer (Codex) for Cuttingboard.
Repo: /home/dustin/Projects/cuttingboard, branch claude/gex-4-product-recon.
Event: GEX-4 EVENT 2, ATTEMPT 2 - NARROW EXACT-HEAD CONFIRMATION of a Helm-authorized bounded repair. NOT a design review, NOT an optimization pass. Answer only questions A-H. Do not edit files. Emit the result on stdout, plain ASCII.

EXACT REPAIR HEAD under confirmation: f3833a4e54a7db69f61d3a4bfd8fa7d4f8bc6ad6
Prior corrected MATERIAL head: d85268292b0e298101769d454af5fac33dffe4dc

Read, in this order (do not rediscover the repository):
1. /tmp/claude-1000/-home-dustin-Projects-cuttingboard/1f2bca2b-be23-4417-b580-c5627dfd2f61/scratchpad/review_prep_repair.md  - deterministic review evidence for d852682..f3833a4 (inventory, blob identity, inline diffs)
2. /tmp/claude-1000/-home-dustin-Projects-cuttingboard/1f2bca2b-be23-4417-b580-c5627dfd2f61/scratchpad/repair_recon.diff       - the exact recon diff of the repair
3. audits/gex-4-product-recon-2026-09/GEX_4_EVENT_2_CONFIRMATION_ATTEMPT_1_2026-09-03.md  (attempt-1 record: the two residual defects; everything else was confirmed YES at d852682)
4. audits/gex-4-product-recon-2026-09/GEX_4_EVENT_1_CODEX_REVIEW_2026-09-03.md  (Event-1 R1-R8 as originally stated; sections 2 and 12 only)
5. audits/gex-4-product-recon-2026-09/GEX_4_PRODUCT_RECON_2026-09-03.md  (current candidate at the repair head; sections 0, 5, 6, 9, 12 carry the repair)
6. audits/gex-4-product-recon-2026-09/evidence/proto_corrected_ladder.html  (current prototype; check labels and absence of directional color)
Confirm the head with git rev-parse HEAD and git status --short (must be clean). Verify that GEX_4_EVENT_1_CODEX_REVIEW_2026-09-03.md, GEX_4_CODEX_HIGH_PACKET_2026-09-03.md and GEX_4_EVENT_2_CONFIRMATION_ATTEMPT_1_2026-09-03.md are unchanged between d852682/006f93b and HEAD (git diff --exit-code).

HELM AUTHORIZATION for this repair (the only permitted changes):
REPAIR A - exact visible vocabulary: quantity labels CALL MODELED MAGNITUDE, PUT MODELED MAGNITUDE, MODEL NET*, CALL+PUT MODELED MAGNITUDE; anchor labels LARGEST CALL-CONTRACT MAGNITUDE STRIKE, LARGEST PUT-CONTRACT MAGNITUDE STRIKE, LARGEST RAW-STRIKE |MODEL NET|; no shortening (MODELED->MAG, CALL-CONTRACT->CALL, PUT-CONTRACT->PUT, RAW-STRIKE omitted); adjacent qualifier "Configured call-plus / put-minus convention; participant and dealer positioning are not measured"; one non-directional treatment for positive and negative MODEL NET, sign by geometry and explicit +/- only; no red/blue.
REPAIR B - the additive by_strike carrier stores BOTH sides as non-negative modeled magnitudes: fields "strike", "call_modeled_magnitude_1pct_usd", "put_modeled_magnitude_1pct_usd"; put magnitude = absolute value of the producer's existing signed put contribution; no signed-negative put in the carrier; the positive field must NOT be named put_gex_1pct_usd; model_net(K) = call_modeled_magnitude(K) - put_modeled_magnitude(K).
CANONICAL RECONCILIATION (kept from the confirmed R8 architecture): sorted union of all admitted raw strikes, strictly ascending, absent side 0.0, all admitted strikes retained, lowest-strike tie rule, schema_version 1 additive; ONE pinned total expression - conceptually math.fsum over the flattened sequence call(K), -put(K) for each K in ascending strike order - used identically by producer calculation, serialized-carrier validation and post-JSON validation; no isclose; anchors recomputed from the carrier: CALL = argmax call magnitude, PUT = argmax put magnitude, DOMINANT = argmax abs(call - put); a present domain-valid carrier contradicting the core total or anchors suppresses the whole card.
NOT TO BE REOPENED: R1, R4, R5, R6, R7 substance; schema_version 1; 31 x 25-point window; outlier rule; accessibility; profile-only suppression architecture. Touched only where a literal reference had to change from the carrier field rename or the longer labels (a prototype header layout adjustment for the longer labels is a directly required prototype update).

Answer ONLY, each with YES/NO and one line of file:line or quoted evidence:
A. R2 exact quantity vocabulary now resolved YES/NO
B. R3 exact anchor vocabulary + non-directional semantics resolved YES/NO
C. R8 carrier stores positive call and put modeled magnitudes (field names as ruled; no signed-negative put; not named put_gex_1pct_usd) YES/NO
D. MODEL NET is exactly call magnitude - put magnitude YES/NO
E. canonical fsum / anchor reconciliation is internally coherent (pinned expression, same operand order on both sides, exact after JSON round trip, anchors incl. DOMINANT from call - put, whole-card suppression on contradiction) YES/NO
F. previously confirmed R1/R4/R5/R6/R7 regressed YES/NO (YES means a regression exists; cite it)
G. schema_version 1 additive compatibility remains valid YES/NO
H. new MATERIAL boundary introduced YES/NO (provider, dependency, fetch, workflow, renderer/CSS, SPY mapping, signal, permission coupling, core-card semantic change)
Also state: SCOPE CHECK - is the d852682..f3833a4 diff limited to the authorized repair plus directly required prototype/reference updates? YES/NO with evidence.

FINAL RETURN, exactly:
GEX-4 CODEX - EVENT 2 ATTEMPT 2 EXACT-HEAD CONFIRMATION
CONFIRMED HEAD: <sha> (or NOT CONFIRMED)
A..H lines
SCOPE CHECK line
VERDICT: CONFIRMED (only if A-E YES, F NO, G YES, H NO) or NOT CONFIRMED with the exact residual defect(s)
No optimization suggestions unless a genuine correctness defect is found.
```
