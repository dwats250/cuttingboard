# PRD-335 — fresh-context MATERIAL PRD review (GOV-2 step 7)

- Event type: MATERIAL PRD REVIEW (GOV-2 s2 step 7)
- Reviewer: Codex, medium reasoning, independent fresh-context seat (not the
  author or same-session implementer)
- Reviewed PRD revision: PRD-335.md SHA-256
  4b3f0dc414c391e46e0a3b9cb6a41cc626522fa944446aa37477e3e6e84a3f9a
- Backing packet: PLAN.md (383e696f...), REVIEW.astra.md (prior two Codex events)
- Repository base: fa101cc68963ed1c9704f94c6f54a182bfc86bac
- Review date: 2026-09-05
- Verdict: CHANGES-REQUIRED. Gate-A readiness: READY-AFTER-LISTED-FIXES.
- SHA check by reviewer: MATCH.

Independence: fresh session, not author/implementer; HEAD tracked tree equals the
base; dirty logs not used as evidence; no files modified.

KEY CONFIRMATIONS
- OBSERVATIONAL-ONLY: YES. The reviewer confirmed all four wiring sites
  (macro_pressure.py:18-30, :57-90, :118-133) and ran independent in-memory
  full-wiring demos for EACH of rates_2y, rates_30y, usdjpy: each produced
  changed result keys, changed equality, five aggregation inputs, and LONG sizing
  1.0 -> 0.75 (execution_policy.py:299-302). The proposed fence CAN go RED; the
  new drivers cannot vote as specified. BTC remains a voter (D-4 presentation-only).
- RULING FIDELITY: D-1..D-6 faithfully retained; R4-R7 preserve decision values,
  raw verdict state, visible veto causality, compact regime, grid visibility, and
  synthetic GEX identity.
- GOVERNANCE: HIGH-RISK and MATERIAL correct; CLASS=CONSUMER per Helm; 12
  production files plausible; net LOC an estimate not a precise ceiling.
- No additional mutable production macro_drivers consumer and no third
  driver-key whitelist were found (producer-to-consumer boundary otherwise
  complete).

FINDINGS (all ACTIONED as the single authorized one-cycle correction):
1. MATERIAL [hidden coupling] FILES omitted tests/test_dash_core.py, whose :233
   asserts the macro-pressure-line prose R4 removes. ACTIONED: added to FILES;
   R4 now migrates that assertion to a data-* engine-data invariant.
2. MINOR [factual drift] FILES omitted docs/SCHEMA_MAP.md (PLAN had it).
   ACTIONED: added to FILES (new keys, as_of, both guards).
3. MATERIAL [stale-data ambiguity] R2/R9 lacked a fully testable daily-date
   contract; both guards (contract.py:688-696, payload.py:344-351) reject extra
   fields and require finite-float non-symbol fields, so a dated 2Y block would
   be INERT. ACTIONED: R2 now adopts the 5-calendar-day rule + ISO date +
   mandatory valid producer date, SEPARATE date validation in BOTH guards,
   missing/malformed/future/stale cases; fetched_at_utc stays acquisition time;
   validation.py unchanged; carrier bounded (no provider abstraction) -> R3 holds.
4. MINOR [hidden coupling] as_of flow omitted the fixture loader and misstated
   the notification branch (notifications reads NormalizedQuote directly, not
   snapshot/payload; fixture loader runtime/__init__.py:2131-2148 +
   runtime/_constants.py:77-86 quote-field set rejects extra fields). ACTIONED:
   added runtime/_constants.py to FILES; R2 + DATA FLOW + CHANGE SURFACE corrected;
   this is a quote-field whitelist, not a third driver-key whitelist.
5. MINOR [scope creep] R8's F-2d mutation instruction conflicted with the
   decision-module STOP (it implied editing macro_pressure.py). ACTIONED: F-2d
   now runs on a disposable in-memory copy / monkeypatched clone; no production
   edit to macro_pressure.py.

FILES-COMPLETENESS (reviewer): NO on the reviewed revision (omitted
tests/test_dash_core.py, docs/SCHEMA_MAP.md; plus the fixture quote-field
boundary). RESOLVED by the correction (added test_dash_core.py, SCHEMA_MAP.md,
PROJECT_STATE.md, runtime/_constants.py).

GOVERNANCE/DRIFT (reviewer): no VISION conflict; PROJECT_STATE.md "Active PRD:
none in progress" needs activation bookkeeping when commissioned (added
docs/PROJECT_STATE.md to FILES).

ONE-CYCLE CORRECTION (author/orchestrator, GOV-1 one cycle on this revision; no
new broad cycle per Helm): all five findings applied in place. Corrected PRD
revision SHA-256:
c92c69c51910d22d7ece423966127cd453c4179dfe6d55b6d373ed6047212c69
The corrected deltas are exactly the reviewer's ACTION items (FILES additions +
the daily-date contract + the fixture/guard date-validation + the in-memory F-2d
demo). PLAN.md unchanged (383e696f...).

GATE-A RECOMMENDATION (orchestrator): the reviewer recommended
ready-after-listed-fixes; the listed fixes are applied at c92c69c5. Recommend
Gate A on the corrected PRD revision c92c69c5, with the proposed ceiling of <= 12
production files and the FILES list as amended. Gate A remains Dustin's; not
granted.

PRD REVIEW COMPLETE (recorded by orchestrator from the committed reviewer output;
raw transcript retained in the session job tmp).
