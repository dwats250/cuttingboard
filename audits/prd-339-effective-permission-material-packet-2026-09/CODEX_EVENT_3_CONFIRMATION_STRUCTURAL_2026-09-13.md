# CODEX EVENT 3 -- EXACT-HEAD CONFIRMATION (owner-authorized correction 2) (GOV-2 s2)

EVENT: EXACT-HEAD CONFIRMATION (STRUCTURAL correction 2)
REVIEWER: gpt-5.6-sol (Codex), fresh-context independent.
RUN-ISOLATION / INDEPENDENCE EVIDENCE (GOV-2 s2): cbagent systemd --user transient unit, fresh
codex exec, no shared session memory, read-only sandbox, exact-SHA guard verified HEAD == the
confirmed SHA. cbagent job id: codex-20260913T012605Z-3684.
EXACT CONFIRMED SHA: 941bbf240122c73c48078d171c1e651a5cd62295 (structural packet, correction 2 / s13).
DATE: 2026-09-13.

## Result
R1 STATUS: CLOSED. R2 STATUS: CLOSED. R4 STATUS: CLOSED. R3 STATUS: NOT.
NEW STRUCTURAL BYPASS CLASS FOUND: NO.
VERDICT: DESIGN INCOMPLETE (single residual: R3 cross-process provenance).

A. R1/R2/R4 structurally closed by s13; R3 remains unsound.
B. No -- an authoritative channel cannot emit actionability before resolution (required-EP
   signatures); absence yields UNAVAILABLE.
C. YES -- after serialization the in-process construction capability is gone; a downstream
   same-project process can write a syntactically valid, current-session, non-stale canonical
   field while omitting alternate decision-bearing fields, and the read-boundary validator
   cannot distinguish it from resolver-produced output. "Single write path + shape validation"
   does not prove ORIGIN.
D. No -- with R4 implemented literally, authoritative renderers receive neither the proxies nor
   a carrier containing them; authoritative wording derives only from EffectivePermission.
E. Yes -- the mechanism discovers/enforces a previously-unknown sink of an already-governed
   channel class (assuming T1/T2 inspect actual writer behavior, not literal strings). This does
   not repair R3.

## R3 residual -- precise gap and resolution space (for Dustin's ruling)

GAP: cross-process origin cannot be proven by data shape + freshness alone. Some
NON-self-assertable cross-process provenance is required. Sol names two sufficient options;
crypto is NOT necessarily required:
- OPTION A (non-crypto; recommended, matches the stated same-project trust boundary): elevate
  s13's "single write path" to a CODE-ENFORCED EXCLUSIVE-WRITER / PRIVILEGE BOUNDARY -- a
  structural test asserts that NO module other than the resolver's persistence path writes the
  authoritative field to ANY carrier (latest_run/contract/payload, ui/contract.json, the report
  files), so no downstream code path can self-assert it. This is Sol's explicitly-named
  "genuinely exclusive writer/privilege boundary." It closes R3 for the in-scope threat (a
  downstream CODE PATH), without a secret or signature.
- OPTION B (integrity): authenticated integrity (MAC/signature) over the projection -- required
  ONLY if the trust boundary is actually stronger than same-project (e.g. an untrusted external
  writer could write the carrier). The owner ruled against introducing crypto/secrets unless the
  boundary requires it; Sol confirms it is not necessarily required. So Option A is preferred
  unless Dustin identifies an out-of-same-project writer as in-scope.

## GOV-2 disposition (STOP per owner charter)

Per Dustin's authorization ("No second correction after this confirmation without Dustin's
explicit ruling"; STOP conditions: if one of R1-R4 still unsound, STOP), R3 unsound -> STOP. No
further correction is made. This is the tightest state to date: R1/R2/R4 CLOSED, no new bypass
class, and R3 is a SINGLE precise residual with a clear non-crypto resolution (Option A).
DECISION returns to Dustin: (1) authorize a correction adopting Option A (exclusive-writer
boundary) for R3 + one fresh confirmation; or (2) rule Option B (integrity) if an out-of-
same-project writer is in scope; or (3) rule the mechanism directly; or (4) park. PRD-339 design
(0348cee1) remains provisional; no ruling / PRD / Gate A / implementation until a review-clean,
mechanism-sound packet exists.
