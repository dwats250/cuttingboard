# GEX-4 Provisional MATERIAL Package - Event 2 Exact-Head Confirmation, ATTEMPT 3 / FINAL MECHANICAL (durable record)

- **Event:** EXACT-HEAD CONFIRMATION of the Helm-ruled final mechanical repair (sole residual from attempt 2: outside-bin label must be exactly MODEL NET*)
- **Reviewer:** Codex (codex-cli 0.150.1), fresh context, `-s read-only`, `model_reasoning_effort=medium`, run from an ISOLATED scratch directory containing only the repair diff and the literal-check output (no repository access)
- **Repaired head under confirmation:** `10b0a6b293ca88fc7e3f4fcb75f5cbc34574ade4` (PR #309; diff base 632919a)
- **Date:** 2026-09-03
- **Tokens used (reported by codex):** 22,385
- **Deterministic pin:** `evidence/check_outside_bin_label.py` -> "PIN OK: outside-bin label == MODEL NET* in recon section 12, generator, generated prototype" (exit 0). Mutation evidence at this head: reverting the generator literal to "model net" -> 2 pin failures; reverting the recon line to "NET <y>B" -> 2 pin failures.
- **Verdict:** YES - the sole prior residual is resolved at this exact head without adjacent semantic change.
- **Chain of heads:** e259964 (recon, Event-1 input) -> 1b14f3c (Event-1 record) -> d852682 (consolidated correction) -> 006f93b (attempt-1 record) -> f3833a4 (bounded repair) -> 632919a (attempt-2 record) -> 10b0a6b (final mechanical repair, CONFIRMED) -> this record.
- **Disposition:** GEX-4 current candidate design is review-clean under the Event-1 / Event-2 sequence. It still carries NO implementation authority: Helm design-direction ruling, provider-rights hold, Stage-0 PRD, fresh-context PRD review, and Gate A remain ahead. PR body cleanup ("box-spread financing paper" sentence) is still required before merge.

---

## Verbatim reviewer stdout

```
GEX-4 TINY EXACT-HEAD CONFIRMATION
HEAD: 10b0a6b293ca88fc7e3f4fcb75f5cbc34574ade4
ANSWER: YES
EVIDENCE: GEX_4_PRODUCT_RECON_2026-09-03.md @@ -514,7 +514,7 @@ changes only the outside-line label from NET to MODEL NET*.
EVIDENCE: check_outside_bin_label.py @@ -0,0 +1,39 @@ adds a deterministic literal pin for MODEL NET* and rejects the superseded forms.
EVIDENCE: proto_corrected_ladder.html @@ -206,7 +206,7 @@ changes only the generated outside-bin label from model net to model net*.
EVIDENCE: proto_generator_corrected.py @@ -57,7 +57,7 @@ changes only the outside-line generator literal from model net to model net*.
```

---

## Literal-check output at the repaired head

```
PIN OK: outside-bin label == MODEL NET* in recon section 12, generator, generated prototype
exit 0
```

## Appendix - confirmation prompt (stdin)

```
You are a fresh-context independent reviewer. TINY exact-head confirmation only. You have NO repository; do not explore, do not run git, do not read anything except the two files named below in this directory. No recommendations, no optimization, no design review. Plain ASCII on stdout.

CONTEXT
- Cuttingboard GEX-4 design packet, PR #309. Event-2 attempt 2 (prior head f3833a4) resolved every substantive design question and returned NOT CONFIRMED on ONE residual, quoted verbatim:
  "the outside-bin visible quantity remains shortened to "NET" in the section-12 contract and "model net" in the prototype instead of the Helm-authorized exact label "MODEL NET*"."
- Helm authorized a mechanical repair limited to that residual: make the outside-bin quantity label exactly MODEL NET* in the recon section-12 contract line, the prototype generator, and the generated prototype; add the narrowest deterministic literal pin; change nothing else.
- EXACT REPAIRED SHA: 10b0a6b293ca88fc7e3f4fcb75f5cbc34574ade4 (diff base 632919a).

FILES IN THIS DIRECTORY
1. repair.diff - the complete git diff 632919a..10b0a6b (three one-line content changes plus one new verification script evidence/check_outside_bin_label.py)
2. literal_check_output.txt - the deterministic pin output at the repaired head

ANSWER EXACTLY ONE QUESTION
"Is the sole prior residual resolved at this exact head without any adjacent semantic change? YES / NO."
Cite the diff hunks you relied on in one line each. If NO, state the exact residual.

FINAL RETURN, exactly:
GEX-4 TINY EXACT-HEAD CONFIRMATION
HEAD: 10b0a6b293ca88fc7e3f4fcb75f5cbc34574ade4
ANSWER: YES or NO
EVIDENCE: <one line per hunk>
```
