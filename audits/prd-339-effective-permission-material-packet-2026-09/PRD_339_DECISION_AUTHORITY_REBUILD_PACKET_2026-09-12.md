# PRD-339 DECISION-AUTHORITY MATERIAL Packet -- FRESH-FRAME REBUILD (2026-09-12)

STATUS: PROVISIONAL (GOV-2 s6 fresh-frame rebuild; owner ruling REBUILD). Not review-clean
until the exact-corrected-head confirmation records it. Grants no downstream authority: no
design-direction ruling, no PRD drafting/review, no Gate A, no implementation.

SUPERSEDES: PRD_339_EFFECTIVE_PERMISSION_MATERIAL_PACKET_2026-09-12.md (that packet reached
DESIGN INCOMPLETE after two boundary resets: initial review found the delivery/report/CLI/
premarket-postmarket consumer class; exact-head confirmation found the market_map
if_now/PLAY class). Per GOV-2 s6 and Dustin's 2026-09-12 ruling, this is a REBUILD FROM A
FRESH FRAME, not another correction. The old packet + its CODEX_EVENT_1/EVENT_2 records
remain for provenance.

FRAME CHANGE: the failed packet framed the problem as "permission consumers" and kept
missing surfaces. This rebuild uses a DECISION-AUTHORITY frame: every code site that can
tell Dustin (or a downstream component) to trade / not-trade / take / play / stay-flat /
observe-only / that a setup is ready/permitted/prohibited/qualified/actionable -- judged by
SEMANTICS, not literal field names. Built by four independent read-only recon sweeps
(producers/restrictors; dashboard+viewer presentation reverse-trace; delivery/messaging/
reports/CLI reverse-trace; and an independent semantic completeness sweep) at
HEAD 2db84314.

Docs-only CI boundary (GOV-2 s8): CI here confirms only that the branch preserves the
current green baseline; it does not execute or validate the proposed design, inventory, or
regression plan.

Repository base: main @ 1e91f897 (unchanged, nothing pushed). PRD-339 design (0348cee1) is
PROVISIONAL and NOT modified; it is now known to rest on an incomplete boundary and must be
reconciled to whatever frame Dustin selects.

---

## 1. Why MATERIAL (GOV-2 s1)

Enumerates ALL decision-authority surfaces; selects a carrier/seam shared across pipeline
layers; sets FILES/LOC ceilings; adds a persisted schema surface with many readers;
resolves High findings; crosses runtime + contract + qualification + market_map +
market_control_card + notification + delivery + dashboard + reporting + persistence.
MATERIAL, ineligible for LANE: MICRO. CLASS (CONTRACT vs EXECUTION) and lane (HIGH-RISK)
are owner rulings (Q7).

---

## 2. The SIX authority seams (the converged boundary)

The completeness sweep established that EVERY outbound surface resolves to one or more of
six seams. This is the boundary:
- S1 RUNTIME OUTCOME: TRADE/NO_TRADE/HALT (runtime/__init__.py:1051-1055; HALT :1300-1318).
- S2 CONTRACT system_state: permission / tradable / outcome / stay_flat_reason
  (contract.py:220-278; runtime :1138-1147).
- S3 MARKET_MAP trade_framing: grade/setup_state/if_now(TAKE)/direction/preferred_trade_structure
  (market_map.py:187-225, 479-509).
- S4 QUALIFICATION / GRADE TIER: qualified / symbols_qualified / grade A+ (qualification.py;
  regime.py:319-347 posture).
- S5 MARKET_CONTROL_CARD: ACTIONABLE_CANDIDATES / permission cell (market_control_card.py).
- S6 OPERATOR-LOCK / HALT restriction: config.py:69-115; execution_policy.py:245-289
  (+ thesis/invalidation/entry-quality/intraday-short gates B5-B8).

COMPLETENESS TEST (GOV-2, answered): "Can any code path tell Dustin to act without passing
through S1-S6?" ANSWER: no live production path bypasses the seams. Telegram is the only
outbound channel (no email/slack/webhook exists). The near-bypass risks are stale committed
UI HTML and unsurfaced reports (s9 F-items), not live bypasses.

---

## 3. Exhaustive decision-authority inventory (classified A/B/C/D/E/F)

Classes: A authoritative origin; B restriction authority; C derived/observational (reads a
proxy); D presentation-only; E delivery-only; F legacy/dead/shadowed. "INFERS" = a consumer
that independently reconstructs actionability from a proxy.

### A -- AUTHORITATIVE ORIGINS
- A1 regime posture (regime.py:319-347) -> root positive-permission origin (feeds S2/S4).
- A2 qualification.qualified / symbols_qualified (qualification.py:99,348) -> "setup ready".
- A3 trade_decision ALLOW_TRADE (trade_decision.py:155) -> per-decision tradable.
- A4 is_actionable_trade / decision_is_actionable / candidate_is_actionable
  (trade_decision.py:96-141) -> THE single canonical actionable rule (PRD-162).
- A5 runtime outcome = TRADE iff any actionable (runtime:1051-1055) -> THE run-level verdict.
- A6 market_map grade=A+/setup=ACTIONABLE (market_map.py:196-198) + if_now=TAKE (:479-509,
  guard actionable_now :490) -> PARALLEL "actionable now" origin from a DIFFERENT computation
  (regime_aligned + strong_structure + near_key_level); NOT lock/HALT/policy constrained.
- A7 market_control_card ACTIONABLE_CANDIDATES (market_control_card.py:241-252) -> derived
  from A5 (shares A5 identity).
- A8 permission-text producer _PERMISSION_LINES (runtime/_constants.py:96-103) -> positive
  permission sentences (contract/summary carriers).

### B -- RESTRICTION AUTHORITIES
- B1 validation system_halted -> HALT (runtime:1300-1302).
- B2 kill_switch -> HALT (runtime:1303-1318; def :3015; ALSO recomputed hourly :584 and in
  summary :1729 -- FOUR sites).
- B3 execution_policy (execution_policy.py:245-289): downgrades ALLOW->BLOCK on confidence/
  CHAOTIC/STAY_FLAT/ORB/macro-pressure/size-zero AND operator lock (:287-288); the primary
  per-decision restrictor.
- B4 operator lock (config.py:79-115, OPERATOR_LOCK_PERMISSION :71): resolved once per
  entrypoint (runtime :547 hourly, :1236 daily); consumed as restrictor at B3 AND as a
  permission-carrier override at FOUR sites (runtime :1141-1144, :1744-1747, :2416-2422,
  :2501-2506) -- precedence logic duplicated, not centralized.
- B5 thesis gate (trade_thesis.py:134); B6 invalidation gate (invalidation.py:129);
  B7 entry-quality gate (entry_quality.py:164); B8 intraday-short permission
  (runtime:1788-1880, open-window fail-closed).
- B10 derive_run_status STAY_FLAT collapse (contract.py:220-232).
- B11 hard halt/error "no permission" overrides (runtime:1139-1140/1742-1743/2502-2503/3186;
  contract.py:184-199 build_error_contract).
- B12 overnight_policy annotations (overnight_policy.py:56-83).

### C -- DERIVED / OBSERVATIONAL (proxies)
- C1 system_state.tradable (contract.py:255-259) = not halted and posture!=STAY_FLAT ->
  IGNORES execution-policy blocks AND operator lock; can be True on a NO_TRADE/locked run.
  Read directly by the viewer, the send-gate, premarket/postmarket, CLI (bypasses the
  permission field).
- C2 stay_flat_reason; C3 _build_trade_candidates projection; C4 trade_visibility
  ACTIVE/NEAR_MISS/BLOCKED (reads market_map grade -> cross-authority coupling);
  C5 market_control_card cells; C6 market_map lower grades / if_now=WAIT;
  C7 market_context flags; C8 dormant execution-session state.

### D -- PRESENTATION (dashboard + viewer)
- Dashboard decision-state HALT/STAY FLAT/TRADE PERMITTED/OBSERVE ONLY/STATE UNAVAILABLE
  (dashboard_renderer.py:2989-3034; TRADE PERMITTED only via outcome==TRADE); IF NOW
  (:2415-2421 <- S3 if_now, lock-suppressed); PLAY (:2479-2480 <- S3, lock-suppressed);
  A+ "ACTIONABLE" tier (:972-977, _tier_label_for :3452-3460 -> "OBSERVATION ONLY" under
  lock but NOT HALT-gated) [D + INFERS grade]; WHY "N setups gated" (:3069-3108 [INFERS
  high-grade count]); "NO ACTIONABLE SETUPS" (:3419-3427 [INFERS no high-grade]); MCC
  display (:197-213, :4019-4026); chart neutralization (:2533/:3445); _regime_to_permission_verb
  (:1875-1928, now only data-raw-permission + inert verdict-sentence).
- dashboard_integrator screen-verdicts RULE2/RULE3 (dashboard_integrator.py:33-166)
  [D + INFERS; restraining only -- never emits a permit].
- market_state_panel PERMISSION cell (delivery/market_state_panel.py:54-129).
- ui/app.js: derivePosture TRADE_READY (:87-93 [INFERS status+tradable]); renderSignalBar
  (:120-138); renderPrimaryTrade (:140-164 [INFERS candidate presence]); renderNoTrade/
  renderWatchlist (:166-208); renderSecondarySetups (:210-237); outcome badge (:518-530,561);
  Signal-Forge table (:404-471 <- payload top_trades). NO lock/freshness gate on the
  TRADE_READY / Primary-Trade derivations; contract.json carries no permission field.

### E -- DELIVERY
- Telegram daily build_notification_message (output.py:1144-1210 [INFERS allowed-candidate
  presence]; lock+HALT constrained); operator-lock message (:1108-1141); hourly
  format_hourly_notification + _action_label (notifications/__init__.py:150-169,532-578
  [INFERS regime+qualification+outcome -- a SECOND independent actionability derivation]);
  formatter.py _format_hourly/_format_setup_ready/_forming ("READY"/"FORMING" [INFERS
  posture/qualified]); send-gate state.py (classify_notification_priority HIGH<-tradable
  ALWAYS-SENDS :84-115; dedup key :50-81); hourly_slot dedup; alert_runner exception
  backstop (:229-233); PRD-300 market-stress resend (runtime:318); lifecycle alerts from
  market_map grade transitions (notifications/__init__.py:342-406). send_telegram
  (output.py:729) = only outbound channel.
- Reports: render_report (output.py:293-630, action-bearing, lock+HALT gated);
  render_report_from_payload (:633-720 [INFERS outcome from top_trades presence; reads disk
  payload -> stale-regression]); html_renderer (:15-23).
- CLI deliver_cli (transport.py:44-63: TRADABLE<-summary.tradable, EXECUTION<-lock,
  TOP_TRADES); deliver_json/deliver_html (E).
- payload build_report_payload (delivery/payload.py:46-184): top_trades = actionable
  candidates (S1/A4), summary{tradable,permission,outcome}; the single projection every
  UI/CLI/HTML consumes; NO lock branch (consumers enforce).

### F -- LEGACY / DEAD / SHADOWED / UNSURFACED
- F1 STALE committed ui/dashboard.html + ui/index.html on main (byte-identical, 2026-06-12
  snapshot) with hardcoded actionability ("Controlled Long / SPY next +0.83%", "Longs
  allowed" badge, "MACRO BIAS: LONG", "VIX permits longs" -- wording since REMOVED by
  PRD-334/335). Overwritten server-side on publish each run, BUT served verbatim by Pages if
  a run fails to regenerate. Closest thing to a bypass authority surface.
- F2 premarket/postmarket reports (reports/premarket.py:370-419, postmarket.py:129-228) --
  computed at runtime:1547-1548, stored in PipelineResult, but NO reader exists; full
  decision language ("no entries permitted", "qualified for execution") reaches no surface.
  Latent bypass if wired later.
- F3 IntradayState.trades_allowed (intraday_state_engine.py:75) -- vestigial, never read
  outside the engine.
- F4 notifications/__init__ _action_label vs formatter.py -- duplicated title/verdict
  authority (a second independent derivation).
- F5 render_report_from_payload -- legacy "backward-compatible" adapter re-deriving outcome.
- F6 output.py _PERMISSION_LINES (:199-206) -- a SECOND divergent permission-text table
  (hyphen + Kill/FLAT suffixes) vs the canonical _constants.py table (A8).

---

## 4. Producer-to-final-consumer graph (condensed)

regime posture (A1) -> qualification (A2/S4) -> chain/thesis/invalidation/entry-quality/
  execution-policy (A3/B3/B5-B8) -> is_actionable_trade (A4) -> runtime outcome (A5/S1)
  -> contract system_state {outcome,permission,tradable} (S2) + trade_candidates
    -> latest_run.json (monotonic) / latest_contract.json (monotonic)
    -> payload build_report_payload -> top_trades + summary (S2 projection)
       -> latest_payload.json (PLAIN OVERWRITE) -> app.js Signal-Forge + render_report_from_payload -> report.html
    -> market_control_card (S5) -> dashboard MCC cell
    -> dashboard_renderer decision-state / directives -> ui/dashboard.html+index.html (published)
    -> ui/app.js signal bar / primary trade (reads contract.json; no permission field)
    -> Telegram daily/hourly (send-gate on tradable) -> api.telegram.org
market_map (A6/S3) if_now=TAKE / grade -> dashboard IF NOW/PLAY/A+ tier + lifecycle Telegram
  alerts + integrator input  [PARALLEL ORIGIN, not lock/HALT/policy constrained]
operator lock / HALT (S6/B) -> overrides permission text at 4 sites; suppresses directives;
  send-gate distinct OPERATOR_LOCKED state
PUBLISH: ci_push_artifacts.sh (bootstrap direct-push :57-68 / changed-set overlay :98-146 /
  retry :180-198; static ui/* sync excludes the 3 generated boards) -> publish branch ->
  pages.yml (any upstream completion, no conclusion gate) -> served board.

---

## 5. Duplicate / conflicting authority origins (the core defect cluster)

1. A5 runtime outcome vs A6 market_map if_now=TAKE -- two independent "actionable now"
   computations, different inputs, different carriers (latest_contract.json vs
   market_map.json). market_map is NOT operator-lock/HALT/execution-policy constrained -> can
   render IF NOW=TAKE / A+ ACTIONABLE while the run outcome is NO_TRADE or the operator is
   locked/HALTed. PRIMARY conflict.
2. C1 system_state.tradable vs A5 outcome -- tradable ignores execution-policy + lock; read
   directly by viewer / send-gate (HIGH->always send) / premarket-postmarket / CLI, bypassing
   the permission field.
3. _action_label (E, notifications) -- a third independent actionability derivation (regime +
   qualification + outcome) for the hourly Telegram title.
4. A8 _constants._PERMISSION_LINES vs F6 output._PERMISSION_LINES -- two divergent
   permission-text tables for identical postures.
5. Operator-lock precedence duplicated at 4 sites; kill_switch recomputed at 4 sites -- no
   centralized restriction resolver.

---

## 6. Restore / regression seams

- PLAIN-OVERWRITE carriers (NO monotonic guard): latest_payload.json, latest_hourly_payload
  .json, report.html, shared market_map.json (deliver_json/deliver_html + _write_market_map
  _file). These are the most permissive stale-regression path -- render_report_from_payload,
  app.js, and lifecycle Telegram alerts read them back.
- MONOTONIC carriers (safe_write_latest, new_ts>old_ts; legacy/missing-ts overwrites):
  latest_run.json, latest_contract.json, latest_hourly_run/contract.json.
- PUBLISHER: ci_push_artifacts.sh overlays by completion order, no semantic comparison; on
  every publish route (bootstrap, overlay, retry). pages.yml deploys on any completion.
- STALE committed ui/*.html (F1): served verbatim if regeneration skipped.
- Send-gate at-least-once: success-only dedup persistence + transport retry + PRD-300 resend
  + alert_runner backstop -> duplicate/extra HALT sends possible (delivery guarantee, not
  permission-origin).
- generation_id = mode+second (runtime:3127-3134) collides same-second; no unique run/
  decision identity or shared ordering key across carriers.

---

## 7. Identity / version requirements (implied by s5/s6)

A coherent fix needs: (a) ONE resolved effective-permission state at the producer that every
surface consumes; (b) a unique per-run identity (breaking the mode+second collision) and a
monotonic authority-version ordering key shared across ALL permission-bearing carriers
(including the plain-overwrite ones); (c) a monotonic write guard on every permission-bearing
carrier + a publication non-regression guard on every publish route; (d) restriction
composition that is monotonic within a session and centralized (lock/HALT/integrity), not
duplicated at 4 sites; (e) the parallel origins (market_map if_now, _action_label, tradable)
either derived from the one resolved state or explicitly demoted to observational.

---

## 8. Candidate architectural root-cause clusters

- RC1 NO CANONICAL EFFECTIVE-PERMISSION PROJECTION: is_actionable_trade (A4) exists but is
  applied per-decision; there is no single resolved effective-permission STATE projected onto
  a carrier and consumed uniformly. Every surface re-derives from proxies.
- RC2 PARALLEL / UNCONSTRAINED ORIGINS: market_map if_now (A6), _action_label, and tradable
  (C1) independently assert actionability outside the S1/S6 restriction path.
- RC3 DECENTRALIZED RESTRICTION: lock/kill precedence duplicated across many sites; no
  cross-run restriction continuity.
- RC4 NON-MONOTONIC CARRIERS + PUBLICATION-ORDER AUTHORITY: plain-overwrite artifacts +
  completion-order publish + stale committed HTML.
- RC5 IDENTITY INSUFFICIENCY: mode+second generation_id; no shared ordering key.
- RC6 DIVERGENT PERMISSION-TEXT TABLES (A8 vs F6).
- RC7 UNSURFACED/VESTIGIAL AUTHORITY (F2/F3): latent bypass risk.

---

## 9. Proposed minimum coherent implementation boundaries (for owner selection)

- MCB-1 ORIGINATION + PROJECTION + FIDELITY: define ONE resolved effective-permission state at
  the producer (built from A4/S1 + restriction set S6), persist it on the contract/summary,
  and make EVERY permission-asserting surface (D + E consumers) consume it. Reconcile the
  parallel origins (RC2): market_map if_now/A+ tier, _action_label, tradable, and the send-gate
  must derive from or be constrained by the resolved state. Fail-closed to UNAVAILABLE when
  absent/malformed. (Closes RC1, RC2, RC6; addresses F1/F2 by making them consume or be
  documented non-authoritative.)
- MCB-2 RESTRICTION CONTINUITY + RECOVERY: centralize lock/HALT/integrity precedence; make
  restriction monotonic within a session with a durable carrier; recovery only by a new daily
  decision. (Closes RC3.)
- MCB-3 IDENTITY + PUBLICATION NON-REGRESSION: unique run identity + monotonic authority
  version shared across all permission-bearing carriers; monotonic write guard on the
  plain-overwrite artifacts; publication non-regression guard on every publish route. (Closes
  RC4, RC5.)

---

## 10. Structure recommendation (GOV-2; owner decides at Q3)

The invariants genuinely separate: ORIGINATION/FIDELITY (MCB-1 + MCB-2) vs NON-REGRESSION
(MCB-3). RECOMMEND TWO ORDERED PRDs with a safe fail-closed intermediate:
- PRD-A = MCB-1 + MCB-2 (carrier + producer + parallel-origin reconciliation + consumer
  fidelity + restriction continuity; consumers fail closed to UNAVAILABLE).
- PRD-B = MCB-3 (identity + monotonic carriers + publication non-regression guard).
A THIRD PRD is justified ONLY if the owner wants restriction-continuity/recovery (MCB-2)
split from the carrier (they are tightly coupled, so folding into PRD-A is cleaner). This is a
recommendation; Q3 is the owner's.

---

## 11. Estimated implementation surface (GOV-2 s5 -- ESTIMATED SURFACE, NOT YET APPROVED)

ESTIMATED SURFACE -- NOT YET APPROVED (not a constraint until Gate A). The decision-authority
frame is materially larger than the failed packet's estimate.

New: cuttingboard/effective_permission.py; tools/publish_authority_guard.py.
Producers/carriers: runtime/__init__.py, contract.py, contract_types.py, trade_decision.py,
execution_policy.py, market_map.py, market_control_card.py, runtime/_constants.py (permission
table unification), config.py (provenance).
Consumers (scope set by Q8): dashboard_renderer.py, dashboard_integrator.py,
delivery/market_state_panel.py, ui/app.js, output.py (daily Telegram + reports + F6 table),
notifications/__init__.py, notifications/formatter.py, notifications/state.py (send-gate),
delivery/payload.py, delivery/transport.py, delivery/html_renderer.py, reports/premarket.py,
reports/postmarket.py.
Publisher/workflows: tools/ci_push_artifacts.sh, .github/workflows/cuttingboard.yml,
.github/workflows/hourly_alert.yml.

FULL-SCOPE estimate: ~26-32 production files, LOC large (well beyond the failed packet's
~300-500). NARROWED authoritative-subset (Q8): ~12-16 files (served decision surfaces:
dashboard decision-state + directives, contract viewer, Telegram daily/hourly + send-gate,
payload summary, market_map if_now reconciliation, publisher), with reports/CLI/premarket/
postmarket/market_state_panel documented as non-authoritative analytical context. Split into
two PRDs (s10) apportions this. Tests scale with scope. ESTIMATE only; first binding ceiling
is Gate A. An author must not shrink a truthful consequence to preserve an estimate.

---

## 12. Owner design-direction questions (do NOT presume answers)

Q1 SESSION VALIDITY: carry admitted AM permission through the session unless an authoritative
restriction/new decision changes it, VS OBSERVE-ONLY-until-reconfirm. Author rec (non-authority):
carry, monotonic restrictions.
Q3 STRUCTURE: one PRD vs TWO ordered (s10). Author rec: two ordered (origination/fidelity;
then non-regression), safe fail-closed intermediate.
Q4 RECOVERY: confirm only a full daily redecision (higher decision sequence + validated
recovery basis + satisfied restrictions) restores permission; no auto-unlock; a still-
CANNOT_MONITOR setting is not cleared by a redecision.
Q6 CARRIER: reuse/extend an existing carrier vs a NEW dedicated effective-permission file.
Genuine choice; author rec: dedicated file (must now serve the FULL consumer set).
Q7 CLASSIFICATION: confirm MATERIAL; rule CLASS (CONTRACT vs EXECUTION) + lane (HIGH-RISK);
set the PRD-242 / commissioned-review record for the post-ruling PRD review.
Q8 CONSUMER SCOPE: bring EVERY decision-authority surface (s3 D+E, incl. market_map if_now,
send-gate, reports, CLI, premarket/postmarket, market_state_panel) under the one carrier, VS a
named authoritative SUBSET (served decision surfaces) with the rest documented as
non-authoritative analytical context. This sets the true FILES/LOC surface. Author rec: one
resolved state; every ACTION/PERMISSION-asserting surface consumes it; pure analytical-context
surfaces may remain if they carry no action/permission claim -- the owner draws that line.
Q9 PARALLEL-ORIGIN RECONCILIATION (NEW): how to resolve the independent origins (RC2) --
market_map if_now=TAKE, _action_label, system_state.tradable: (a) all DERIVE from the one
resolved effective-permission state; (b) each is CONSTRAINED by the restriction set S6; or
(c) demote market_map if_now / A+ "ACTIONABLE" to observational-only vocabulary. Author rec:
(a) + (c) -- one origin, others observational.
Q10 OWNER-OPERATIONAL vs CODE (NEW): the stale committed ui/dashboard.html/index.html (F1) and
the unsurfaced premarket/postmarket + vestigial trades_allowed (F2/F3) -- treat as
owner-operational cleanup (regenerate/retire) or fold a guard into the PRD? Author rec: F1 is
owner-operational (regenerate committed snapshot; do not hand-edit); F2/F3 are cleanup/dead-code
removal, not permission scope, unless Q8 brings reports in.

If the review surfaces another TRUE owner choice, add it. No question is invented for matters
already determined by code.

---

## 13. GOV-2 sequence status (this rebuild)

1. Fresh-frame investigation + four independent inventories: DONE (HEAD 2db84314).
2. Provisional rebuild packet: THIS DOCUMENT.
3. INITIAL PACKET REVIEW (independent Codex/Sol) against the committed rebuild SHA: pending ->
   CODEX_EVENT_1_REVIEW_REBUILD_2026-09-12.md.
4. ONE consolidated correction (if substantive findings): pending.
5. EXACT-CORRECTED-HEAD CONFIRMATION (independent Codex/Sol): pending ->
   CODEX_EVENT_2_CONFIRMATION_REBUILD_2026-09-12.md. If another omitted CONSUMER CLASS is
   found -> DESIGN INCOMPLETE again, STOP (do not force a clean verdict).
6. STOP for Dustin's design-direction ruling from a review-clean packet.

No downstream authority (ruling, PRD review, Gate A, implementation) proceeds until the packet
is review-clean and Dustin rules.
