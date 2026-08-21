# GEX-2 FREE Board Card MATERIAL Packet -- Event 2 Exact-Corrected-Head Confirmation (durable record)

- **Event:** EXACT-CORRECTED-HEAD CONFIRMATION -- ATTEMPT 2 (GOV-2 sec7)
- **Reviewer:** Codex (`gpt-5.6-sol`, high), fresh-context independent
- **Head confirmed against:** `bed44ab699be57ce7e213c5e493b46a2636d62b7`
- **Verdict:** NOT CONFIRMED -- F7 only (all other checks PASS; F8 PASS = no new material class)
- **Date:** 2026-08-21
- **Context:** fresh, read-only, independent; a confirmation against the Event-1 findings list, not a fresh-scope review.

ATTEMPT 2 followed the single bounded confirmation repair (packet r3) of the
ATTEMPT-1 F4/F7 non-material defects. F4 now PASS. F7 remains FAIL on TWO
residual same-defect instances the r3 repair missed: (1) the sec6 R18 table
row still says "or a dedicated pipeline test"; (2) sec8 still labels the
producer-docstring conditional "Q4" instead of "Q5". F8 PASS -- no new material
boundary class, so the packet is NOT DESIGN INCOMPLETE. Per the charge-template
rule (at most one bounded correction pass before escalating) and the packet r3
stop commitment, the ONE bounded confirmation repair is spent; a further repair
is escalated to Dustin (the authority who authorizes confirmation repairs, as
in the GEX-1 precedent). No ATTEMPT 3 was run autonomously.

---

## Verbatim Codex stdout (ATTEMPT 2)

```
CONFIRMED COMMIT: bed44ab699be57ce7e213c5e493b46a2636d62b7
CONFIRMATION: NOT CONFIRMED

F1: PASS -- Sec0 forces CONSUMER / HIGH-RISK under PRD-121 R11, withdraws STANDARD, resolves sec9 Q1, and sec10 carries the HIGH-RISK Second-Model Disposition obligation.
F2: PASS -- D7 adds zero rules to unconditional `_CSS`, places any unavoidable rule inside the conditional fragment, and R1 mutates on adding an unconditional card rule; `_CSS` is emitted unconditionally at renderer line 2264.
F3: PASS -- Sec3/D10 truthfully inventory both force-add sites and the absent CI producer-invocation/restore seam; GEX-3 is optional producer invocation, and F3 remains the sole newly discovered class.
F4: PASS -- D5a freezes exact source/data-delay identity, bool-first and finite/range checks, reason/value coherence including the contradictory 0DTE pair, timestamp rules, unknown-token rejection, and honest zero, with R3/R5/R15/R16 red mutations.
F5: PASS -- D7 adds one tz-aware `_utcnow()` clock threaded main -> write_dashboard -> render_dashboard_html -> gex_card; the current render signature has no `now`, and feed/session-gate freshness is rejected.
F6: PASS -- R17 is the required AST/path-literal isolation guard, and R18 specifies a controlled absent-versus-valid artifact run byte-comparing all named decision-output surfaces.
F7: FAIL -- Although sec7 pins R18 and labels the sole producer conditional Q5, R18 at line 602 still allows “a dedicated pipeline test” and sec8 line 669 still labels the producer-docstring conditional Q4, so the FILES ceiling remains internally conditional/inconsistent.
F8: PASS(no new class) -- Exact-head checks revealed no omitted consumer class, renderer, audit carrier, schema surface, or end-to-end seam beyond F3's publish-staging seam.

INDEPENDENCE / PROVENANCE: fresh context, read-only, not author; exact HEAD verified before and after inspection, with only the untracked charge present and no tree writes; GitNexus had no available index and was not rebuilt under the read-only constraint.

```
