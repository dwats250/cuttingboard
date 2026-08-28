# Codex Event-1 review prompt — operator setup chart MATERIAL packet

GOV-2 sec2 step 3: independent Codex review of the provisional packet and
the underlying repository surface. This is the FIRST of the exactly two
Codex events GOV-2 auto-commissions for this MATERIAL slice (the second is
the exact-corrected-head confirmation). Invocation: `codex exec -s read-only`
with this prompt on stdin; the review artifact is written from captured
stdout by the authoring session. Codex has no repo write access.

---

You are the independent GOV-2 packet reviewer for the Cuttingboard
repository (checked out read-only at the SHA named below). You did not
author the packet. Review the packet AND the repository surfaces it claims
to describe. Do not redesign the product; find what is wrong, missing, or
unverified.

PACKET: audits/operator-setup-chart-material-packet-2026-08/OPERATOR_SETUP_CHART_MATERIAL_PACKET_2026-08-28.md
EVIDENCE: audits/operator-setup-chart-material-packet-2026-08/EVIDENCE_PROTOTYPE_RENDER_2026-08-28.html
REVIEW HEAD: <SHA pinned at dispatch>

Verify, against the actual code:

1. INTAKE CLASSIFICATION (packet sec0) — do the GOV-2 sec1 legs cited
   actually fire? Any leg missed?
2. DATA INVENTORY (sec2) — every file:line claim; especially:
   - `_collect_trend_structure_history` runs on BOTH hourly and daily paths
     with the six-symbol daily OHLCV frames in hand at the claimed seams;
   - TREND_STRUCTURE_SYMBOLS == PRIMARY_SYMBOLS;
   - no renderer input today carries a price series;
   - the parquet cache is absent from a fresh CI checkout;
   - the trend-snapshot transport (tracked fallback + force-add +
     ci_restore_publish_state.sh) works as described for a NEW sidecar.
3. CARRIER DESIGN (sec3) — schema completeness (provenance, staleness,
   failure semantics); the completed-bars-only rule's correctness against
   the trading-day-keyed parquet cache; any reader/writer race with the
   publish machinery (PRD-194) the packet missed.
4. CHART DESIGN (sec4) — does anything create new decision semantics,
   scoring, or inference (VISION description-not-prediction)? Is the
   degradation chain honest (never synthesized OHLC)? Are the PRD-226/223/
   304 semantic contracts correctly carried?
5. CONSUMER ENUMERATION (sec5) — falsify it if you can.
6. CEILINGS (sec7/sec8) — are the FILES cones plausibly complete
   (pre-implementation grep sweep: tests asserting `lvl-diagram` /
   `_render_level_diagram` / candidate-card SVG output)?
7. RULING QUESTIONS (sec9) — is any recommendation unsound or any material
   open question missing?

Return:
- VERDICT: one of DESIGN CLEAN / DESIGN INCOMPLETE (with the specific
  missing boundary) — findings numbered, each with file:line evidence and
  severity (MATERIAL-BOUNDARY / CORRECTNESS / RECOMMENDED).
- Confirm you had no write access and reviewed from a fresh context.
