# CODEX EVENT 1 -- INITIAL PACKET REVIEW (STRUCTURAL / completeness-by-construction) (GOV-2 s2)

EVENT: INITIAL PACKET REVIEW (STRUCTURAL)
REVIEWER: gpt-5.6-sol (Codex), fresh-context independent.
RUN-ISOLATION / INDEPENDENCE EVIDENCE (GOV-2 s2): cbagent systemd --user transient unit, fresh
codex exec, no shared session memory, read-only sandbox, exact-SHA guard verified HEAD == the
reviewed SHA. cbagent job id: codex-20260913T004847Z-09a9.
EXACT REVIEWED SHA: e5fdc624c6dedefa50541d07d432a2f5d559bf47 (structural packet, provisional).
DATE: 2026-09-12.
VERDICT: DESIGN INCOMPLETE (mechanism unsound). STRUCTURAL COMPLETENESS SOUND: NO.

NOTE: this is a MECHANISM-SOUNDNESS verdict, NOT an enumeration boundary reset. The reframed
review question ("can a sink emit authoritative action without consuming EffectivePermission?")
worked as intended: the reviewer attacked the mechanism instead of trying to enumerate
consumers. The finding is that the chosen mechanism (typed carrier + AST/vocabulary guard) does
not enforce the ruled invariant; it is corrected within the same ruled method.

## Findings and dispositions (verified against source; all ACTIONED)

F1 (mechanism gap): an AST/vocabulary guard constrains spellings, not semantics -- a sink can
   assemble ("".join / .format), synonymize (GO / DO NOT ENTER), or proxy-derive (grade /
   tradable / candidate presence) an authoritative verdict without importing the carrier or
   containing a banned literal; rule (iv)'s sink registry re-introduces enumeration.
   DISPOSITION: ACTIONED -- primary mechanism replaced by the DATA/OUTPUT-CHANNEL BOUNDARY
   (packet s12); AST/lexical demoted to defense-in-depth.
F2 (schema ambiguity): "authoritative vocabulary" not precisely separable from analytical
   evidence (ACTIONABLE_CANDIDATES market_control_card.py:66; market_map.py:489). DISPOSITION:
   ACTIONED -- enforcement moved off vocabulary to data/capability (s12).
F3 (non-Python gap): app.js derives TRADE_READY from status+tradable (ui/app.js:87); workflow
   derives "N trades" from chain classification (cuttingboard.yml:497); Q9(c)
   monitored-not-guaranteed contradicts the ruling. DISPOSITION: ACTIONED -- s12 strips those
   proxies from the authoritative carriers + mandatory companion boundary checks; Q9(c) dropped.
F4 (factual): resolver cannot be at runtime:1051 (inside the non-HALT path the HALT branches
   :1300/:1303 skip). DISPOSITION: ACTIONED -- corrected to the converged finalization boundary
   ~1136-1147 (packet s3; verified against source).
F5 (mechanism gap): "guard passing == migration complete" false; unmigrated/new sinks rename or
   assemble and pass. DISPOSITION: ACTIONED -- completeness now rests on the FINITE output-
   channel set + the no-alternate-decision-field data invariant (s12), not a sink registry.
F6 (owner vs factual + estimate): Q1/Q3/Q4/Q6/Q7 genuine owner choices; Q9(c) insufficient
   (dropped); estimate omits test surface + contract/SCHEMA_MAP/CALL_SITE_MAP. DISPOSITION:
   ACTIONED -- estimate expanded (s12/s8).

## GOV-2 handling

This is a bounded MECHANISM correction within the owner's ruled method (completeness-by-
construction; the owner listed schema/dependency constraints among the mechanism options and
delegated the choice). It is NOT an enumeration boundary reset (s6). One consolidated
correction applied (packet s12), then the exact-corrected-head confirmation.

## Next

Exact-corrected-head confirmation (Sol) -> CODEX_EVENT_2_CONFIRMATION_STRUCTURAL_2026-09-12.md.
Confirmation question: is the DATA/OUTPUT-CHANNEL mechanism sound (can a sink emit authoritative
action without a provenanced EffectivePermission projection)? If still unsound -> DESIGN
INCOMPLETE, STOP, to Dustin (no forced clean verdict).
