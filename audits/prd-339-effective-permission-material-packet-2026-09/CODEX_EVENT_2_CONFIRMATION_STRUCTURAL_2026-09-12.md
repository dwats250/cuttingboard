# CODEX EVENT 2 -- EXACT-CORRECTED-HEAD CONFIRMATION (STRUCTURAL) (GOV-2 s2/s7)

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION (STRUCTURAL)
REVIEWER: gpt-5.6-sol (Codex), fresh-context independent.
RUN-ISOLATION / INDEPENDENCE EVIDENCE (GOV-2 s2): cbagent systemd --user transient unit, fresh
codex exec, no shared session memory, read-only sandbox, exact-SHA guard verified HEAD == the
confirmed SHA. cbagent job id: codex-20260913T005740Z-477f.
EXACT CONFIRMED SHA: c69ccd56270e0dbaac7ffb00dfa07d21e947712f (structural packet, corrected).
DATE: 2026-09-12.
VERDICT: DESIGN INCOMPLETE (mechanism unsound). STRUCTURAL COMPLETENESS SOUND: NO.

## Prior-finding status at this head
- F1/F5 PARTIAL (mechanism gaps remain -- see residuals below).
- F2 PARTIAL (namespace-not-strip recreates the semantic classification problem).
- F3 RESOLVED.
- F4 NOT RESOLVED (resolver placement still wrong -- see residual 1).
- F6 RESOLVED.

## Residual findings (verified against source before recording)

R1 [AUTHORITY_BYPASS -- omitted output channel + resolver-placement]: the daily Markdown report
   is an authoritative human-facing output channel OUTSIDE the finite set and written BEFORE the
   resolver. In _run_pipeline: `render_report(...)` at runtime/__init__.py:1464 and
   `_write_markdown_report(...)` at :1483 execute BEFORE `_build_and_finalize_contract(...)` at
   :1488 (writer def :2259). VERIFIED (call order confirmed). The packet's finite channel set
   (s12) listed only transport.deliver_html/deliver_json and placed the resolver inside
   finalization (~1136-1147, which is inside _build_and_finalize_contract called at :1488) --
   AFTER the report is already rendered and written. This falsifies both "every output channel"
   and "before publication," and shows F4 (resolver placement) is NOT resolved. There is also an
   execute_run report write at :417/:481 (NOT RUN / error paths).

R2 [PROVENANCE_FORGERY]: provenance is asserted, not made unforgeable. EffectivePermission is a
   plain frozen dataclass (packet s3) whose constructor is callable, and a serialized JSON
   provenance field is ordinary forgeable data. No private-construction capability, signature,
   MAC, or validator-verifiable derivation is specified. So the output-channel validator cannot
   actually distinguish a resolver-issued projection from a hand-built one.

R3 [SEMANTIC RECURRENCE of F1/F2]: the s12 alternative of moving proxies to a "non-authoritative
   namespace" (rather than stripping them) does not remove decision-derivability -- a sink can
   map namespaced grade/tradable/candidate evidence to a synonymous authoritative claim, and
   deciding whether the result is "decision-bearing" recreates the semantic classification
   problem the correction was meant to remove.

## CLOSABILITY (Sol's prescription -- the precise spec for a sound mechanism)

Sol states these are architecturally closable with, and only with, these constraints (none
presently in the corrected mechanism):
1. Move resolution BEFORE every render/write (before render_report:1464 and the execute_run
   writes :417/:481), at the point where outcome/HALT/operator-lock/safety have converged --
   NOT at contract finalization (:1488).
2. Include the Markdown report writer (and every pre-finalization authoritative writer) in the
   CLOSED output-channel registry.
3. Use validator-issued OPAQUE OUTPUT CAPABILITIES or equivalent VERIFIABLE/UNFORGEABLE
   provenance (private construction / signature / MAC) -- not a plain dataclass + JSON field.
4. PROHIBIT decision-capable proxies from REACHING authoritative renderers (STRIP, do not
   namespace); remove the s12 namespace alternative.

## GOV-2 disposition (STOP)

The bounded structural cycle (initial review -> one consolidated correction -> exact-corrected-
head confirmation) is EXHAUSTED and ended DESIGN INCOMPLETE (GOV-2 s7). Per the owner's charge
("do not force a clean verdict") and s7 ("does not enter an unlimited sequence of incremental
corrections"), NO further correction is made in this cycle. Decision returns to Dustin.

IMPORTANT DISTINCTION for the owner decision: unlike the three earlier ENUMERATION resets
(unbounded -- each sweep found unknown new consumers), R1-R3 are BOUNDED, CONVERGING mechanism
findings with an exact closable spec (above). F3/F6 are resolved. The completeness-by-
construction approach is working; it is approximately one more correction from a sound
mechanism. Recommended: Dustin authorizes one more bounded correction cycle applying constraints
1-4 verbatim (or rules the mechanism directly). PRD-339 design (0348cee1) remains provisional;
no ruling / PRD / Gate A / implementation until a mechanism-sound, review-clean packet exists.
