# PRD-335 MATERIAL packet - independent review records (Astra / Codex)

This file carries the two GOV-2 bounded-cycle review events for the PRD-335
"Market Context Completion + Second Editorial Pass" MATERIAL packet. Both events
were performed by Astra (Codex, medium reasoning) occupying the Adversary /
fresh-context independent-reviewer seat, commissioned by Helm's `/plan` charge
(2026-09-05). The reviewer operated in a session separate from packet authorship
(Fable authored the plan; the orchestrator relayed only findings, not verdicts)
and used no prior review verdict.

--------------------------------------------------------------------------------
## EVENT 1 - INITIAL PACKET REVIEW
--------------------------------------------------------------------------------

- Event type: INITIAL PACKET REVIEW
- Reviewer: Astra (Codex 0.153.3, medium reasoning), Adversary / independent
  fresh-context reviewer seat
- Reviewed revision: plan v1, packet SHA-256
  154e013ca05ec628290589ff9c9a8fc5ba90e2494a62c423bacd259c130bb86a
- Repository base: fa101cc68963ed1c9704f94c6f54a182bfc86bac (PRD-334 merged)
- Review date: 2026-09-05
- Verdict: CHANGES-REQUIRED
- Independence: separate session from authorship; no prior verdict consulted;
  memory consulted only for read-only review conventions; no files modified;
  two failures (payload guard, false-green mutation) reproduced in-session.

Findings and dispositions (author adjudication applied as ONE consolidated
correction; corrected packet SHA-256 in Event 2):

1. MATERIAL (axis C/H) - hidden coupling: delivery/payload.py:318-337
   independently whitelists the seven driver keys and rejects unknowns;
   runtime/__init__.py:~2859 validates before delivery and swallows the
   failure -> fresh payload generation fails silently while contract artifacts
   survive (reproduced: "macro_drivers has unexpected driver keys:
   ['rates_30y']"). DISPOSITION: ACTIONED - delivery/payload.py added to scope
   and FILES; both-guard round-trip + end-to-end build_report_payload /
   assert_valid_payload present-and-absent tests + a guard-sync test asserting
   the two whitelists cannot drift; producer-to-consumer inventory refreshed.

2. MATERIAL (axis C) - false-green RED test: _COMPONENT_FIELDS governs only
   container validation / field lookup (macro_pressure.py:41-44,:61); voting
   flows through _COMPONENT_KEYS classification (:118-121) and a four-value
   aggregation (:126-133). The v1 mutation (add rates_30y to _COMPONENT_FIELDS)
   changed nothing (reproduced). DISPOSITION: ACTIONED - s7 rewritten with a
   positive control (F-2a), per-driver classification-reach invariance asserting
   the exact result key set (F-2b), an aggregation-reach spy on _overall_pressure
   asserting exactly four inputs (F-2c), and a one-time 3-site semantic mutation
   demo enumerating the expected RED set (F-2d).

3. MATERIAL (axis G) - price-surface loss: movement_card renders percent change
   only (movement_card.py:86-93,126-129); Trend Structure prints no rows under
   unhealthy-lineage / inactive sessions, so deleting the tradables grid loses
   the ETF price surface for GLD/GDX/SLV/XLE. DISPOSITION: ACTIONED - default
   flipped to a captioned "TRADE VEHICLES / ETF last price" grid; grid deletion
   is now explicit Helm decision D-3, not a default.

4. MATERIAL (axis A/B) - over-certified freshness: fetch clock != observation
   time; provenance is dropped (contract.py:574-580), so an older weekend /
   holiday observation can pass as freshly fetched. DISPOSITION: ACTIONED - the
   "without as_of is by construction fetch-cadence" claim deleted; cells framed
   as "latest available observations with potentially different observation
   times"; RATES captioned as "selected maturities" (not a complete curve);
   new missing/invalid previous-close case (R-6).

5. MINOR (axis D/G) - inert attributes / lost context: data-macro-pressure is
   invisible to an operator; deleting pressure prose and moving the regime word
   to data-regime can remove page-visible reasons (WHY may remain merely
   "setups gated"). DISPOSITION: ACTIONED (a real RISK_OFF/LONG veto fixture
   must keep a VISIBLE causal reason after deletion, STOP if none survives) plus
   HELM decisions D-4 (BTC removal vs muted demotion) and D-5 (regime-line
   removal vs compact retention); BTC kept inspectable (it feeds aggregate
   pressure that vetoes/resizes).

6. MINOR (axis A) - wrong unit token: DXY uses index_level; USDJPY is a rate
   (JPY per USD), not an index. DISPOSITION: ACTIONED - honest token
   jpy_per_usd introduced; Astra's three sub-dismissals accepted (the (1.0,8.0)
   ^TYX yield-point bound is correct; no decision reader needs 30Y change_bps;
   failed optional fetches are excluded in normalization so they do not degrade
   data quality, though a successful-but-stale optional quote still faces the
   global age check).

7. NIT (axis E/F) - DISMISSED (validates the plan): GEX synthetic identity
   stays outside the single disclosure and moving NET*+footnote inside preserves
   PRD-333 isolation; the PRD-110 six-tuple and explicit IWM ban are confirmed
   (test_trend_structure.py:414-439), RSP absent from the universe. No change.

8. MINOR (axis H) - notification growth is a real declared display change (not a
   new notification decision input); H1 history relocation would revisit prior
   owner ruling G2 (dashboard_renderer.py:3506-3509). DISPOSITION: ACTIONED -
   notification present/absent acceptance tests added; H1-leave retained as
   Helm decision D-2.

False-green check (Event 1): F-2 confirmed inert under the v1 mutation. Apart
from the payload guard, no other direct driver-key voting was found in the named
consumers (trade_explanation, invalidation, trade_thesis, notifications all use
aggregate pressure).

Scope judgment (Event 1): one bounded MATERIAL PRD is defensible under Option B
with the payload consumer added, the grid fallback selected, and the test /
cadence claims corrected. Cut line: keep the 2Y carrier + as-of schema out of
this PRD; retain H1-leave and the PRD-110 six.

--------------------------------------------------------------------------------
## EVENT 2 - EXACT-CORRECTED-HEAD CONFIRMATION
--------------------------------------------------------------------------------

- Event type: EXACT-CORRECTED-HEAD CONFIRMATION
- Reviewer: Astra (Codex, medium reasoning), independent fresh-context seat
- Corrected revision: plan v2, packet SHA-256
  383e696f4ce78b38231e92c2b5ce6503edb6a523b73f1754c709011fc6467290
- Confirmation date: 2026-09-05
- Prior finding identifiers confirmed: findings 1-8 above.
- SHA check: MATCH (reviewer recomputed
  383e696f4ce78b38231e92c2b5ce6503edb6a523b73f1754c709011fc6467290).
- Verdict: NOT-CONFIRMED - 7 of 8 findings RESOLVED; finding 2 PARTIALLY
  RESOLVED. No new material boundary omission (so GOV-2 s7 DESIGN-INCOMPLETE is
  NOT triggered). Astra assigns disposition of the single residue to Helm.

Per-finding confirmation:
- 1 RESOLVED - payload consumer, both guards, present/absent/unknown-key tests,
  end-to-end build_report_payload/assert_valid_payload, and guard-sync are in
  scope; whitelist edit correctly at delivery/payload.py:321-329, rejection
  :335-337 (plan:186-203,608-615,733-734).
- 2 PARTIALLY-RESOLVED - the SHIPPING guard tests are sound and breach-
  detecting: F-2a is a sensitive positive control, F-2b asserts the exact
  result key-set (classification reach), F-2c's spy was verified in-memory to
  intercept macro_pressure.py:126 (aggregation reach). The residue is the F-2d
  one-time DEMO recipe only (plan:592-600): its three edits raise
  ValueError("Unsupported driver 'rates_30y'") at macro_pressure.py:90 BEFORE
  aggregation, so the demo would crash rather than produce the four documented
  RED failures. FIX (Astra-prescribed, to apply at IMPLEMENT time when the demo
  is performed): the mutation must ALSO add classification support at
  macro_pressure.py:57-90; with it, one RISK_OFF + four NEUTRAL inputs produce
  MIXED (:98-109) and change LONG sizing (execution_policy.py:299-304).
  Taxonomy: regression-discrimination / evidence gap on an implementation-time
  demo, not a hole in the shipping fence. Helm owns disposition.
- 3 RESOLVED - captioned-grid default; deletion is explicit Helm D-3
  (plan:425-441; movement_card.py:86-93 percent-only; renderer :3725-3733
  suppresses rows in unhealthy/inactive).
- 4 RESOLVED - freshness certification removed; "latest available observations
  with potentially different observation times" + "selected maturities" +
  missing-prev-close case (plan:231-235,529-548).
- 5 RESOLVED - surviving-visible-veto-reason-or-STOP; BTC removal = D-4, regime
  line = D-5, loss disclosed not hidden behind data-* (plan:271-286,323-333).
- 6 RESOLVED - jpy_per_usd honest token; three dismissals retained (plan:177-181,826).
- 7 RESOLVED - GEX anchors + PRD-110 six unchanged (plan:350-368,403-406).
- 8 RESOLVED - notification present/absent acceptance; H1-leave = D-2
  (plan:668-673,719-720,378-386).

NEW MATERIAL OMISSION: none.

FREEZE DISPOSITION (orchestrator): the packet completed the full GOV-2 bounded
cycle (one review, one consolidated correction, one exact-head confirmation).
It is FROZEN but NOT certified review-clean: one minor, well-specified,
Helm-owned residue remained on the F-2d implementation-time demo recipe. No
further correction round was taken (charge: adjudicate once, then freeze; Astra
routed the residue to Helm).

POST-RULING NOTE (2026-09-05, after Helm's design-direction ruling): Helm
authorized correcting the F-2d recipe residue WHILE authoring the Stage-0 PRD,
without reopening this packet cycle. The correction now lives in PRD-335.md R8
(the F-2d demo must also add a classification branch at macro_pressure.py:57-90
so it reaches aggregation instead of raising ValueError at :90). PLAN.md is left
BYTE-IDENTICAL to the confirmed revision (sha 383e696f...) so this record's
SHA pin stays valid; the frozen plan was not mutated. Helm ruled D-1 = Option A
(build the actual 2Y), CLASS=CONSUMER, LANE=HIGH-RISK. PRD-335.md was authored
from the ruling (revision sha 4b3f0dc4...) and sent for the GOV-2 step-7
fresh-context PRD review; Gate A not yet granted.
