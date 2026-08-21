# GEX-2 FREE Board Card MATERIAL Packet -- Event 2 Exact-Corrected-Head Confirmation, ATTEMPT 1 (durable record)

- **Event:** EXACT-CORRECTED-HEAD CONFIRMATION -- ATTEMPT 1 (GOV-2 sec7)
- **Reviewer:** Codex (`gpt-5.6-sol`, high), fresh-context independent
- **Candidate SHA:** `e9b4cce953230bf3c294ab41becd065c33269cc3`
- **Verdict:** NOT CONFIRMED (F4, F7 FAIL; all others PASS; F8 no new material class)
- **Date:** 2026-08-21
- **Context:** fresh, read-only, independent; a confirmation against the Event-1 findings list, not a fresh-scope review.

Durable ATTEMPT-1 record. The confirmation returned NOT CONFIRMED on exactly
two checks -- F4 and F7 -- both NON-MATERIAL confirmation defects (a domain
precision tightening and a doc label/conditional cleanup); F8 PASS confirms NO
new material boundary class, so the packet does NOT return to DESIGN INCOMPLETE
(GOV-2 sec6/sec7). One bounded confirmation repair for those two defects only
was applied (charge-template "at most one bounded correction pass before
escalating"); the ATTEMPT-2 confirmation record is a separate file. This is NOT
a second author correction cycle.

---

## Verbatim Codex stdout (ATTEMPT 1)

```
CONFIRMED COMMIT: e9b4cce953230bf3c294ab41becd065c33269cc3
CONFIRMATION: NOT CONFIRMED

F1: PASS -- Sec0 forces CONSUMER / HIGH-RISK under PRD-121 R11, withdraws STANDARD, sec9 Q1 is resolved, and sec10 carries the required Second-Model Disposition.
F2: PASS -- D7 adds zero unconditional `_CSS` rules and R1 mutates on adding one; `_CSS` is emitted unconditionally at renderer line 2264.
F3: PASS -- Sec3/D10 truthfully inventory both force-add sites and the absent CI producer invocation/restore seam; GEX-3 is optional producer invocation, and F3 is recorded as the sole new class.
F4: FAIL -- D5a accepts any non-empty `data_delay` rather than its exact producer identity and does not reject/test a non-null `zero_dte.share` paired with the recognized unavailable reason.
F5: PASS -- D7 adds one tz-aware `_utcnow()` clock threaded main -> write_dashboard -> render_dashboard_html -> gex_card; current render signature has no `now`, and feed/session freshness is rejected.
F6: PASS -- R17 is the required AST/path-literal isolation guard, and R18 specifies the controlled absent-versus-valid artifact decision-output byte comparison across all named surfaces.
F7: FAIL -- The R18 test location remains conditional between two files, and the producer-docstring conditional is mislabeled Q4 rather than Q5, so the stated sole remaining Q5 conditional is not achieved.
F8: PASS(no new class) -- Exact-head searches revealed no omitted consumer class, renderer, audit carrier, schema surface, or end-to-end seam beyond F3's publish-staging seam.

INDEPENDENCE / PROVENANCE: fresh context, read-only, not author; exact HEAD verified before and after inspection, with only the untracked charge present and no tree writes; GitNexus had no available index, so it was not rebuilt under the read-only constraint.

```
