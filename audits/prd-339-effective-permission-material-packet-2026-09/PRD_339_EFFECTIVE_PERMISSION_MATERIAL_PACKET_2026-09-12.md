# PRD-339 Effective-Permission MATERIAL Packet (2026-09-12)

STATUS: DESIGN INCOMPLETE (GOV-2 s6/s7 -- SECOND boundary reset). NOT review-clean. Grants
no downstream authority: no design-direction ruling, no PRD drafting/review, no Gate A, no
implementation may proceed. The bounded packet cycle (one review + one refresh + one
confirmation) is EXHAUSTED. What is ready for Dustin now is the s6 rebuild / narrow / park
decision (see s12).

BOUNDARY-RESET HISTORY (GOV-2 s6):
- INITIAL PACKET REVIEW (Sol @ d35220461a93ede62a3719ab1da89d1a3f0d61c9): DESIGN INCOMPLETE
  -- omitted permission-consumer CLASS (delivery payload + text/HTML report + CLI +
  premarket/postmarket + the live notification seam). First discovery -> one complete
  inventory refresh (this rev 2). See CODEX_EVENT_1_REVIEW_2026-09-12.md.
- EXACT-CORRECTED-HEAD CONFIRMATION (Sol @ e006141c14a6733854ffb537f35b540303bc1e55):
  F1-F6 all RESOLVED, but a FURTHER omitted class found -- the MARKET-MAP decision-guidance
  artifact/schema + candidate-card renderer (market_map.py:187-225,479-509 emits
  trade_framing.if_now="TAKE" from proxies; dashboard_renderer.py:2410-2421,2465-2480
  renders IF NOW / PLAY; logs/market_map.json is published). This SECOND discovery returns
  the packet to DESIGN INCOMPLETE per s6/s7; incremental patching STOPS.
  See CODEX_EVENT_2_CONFIRMATION_2026-09-12.md.

Author capability: provisional drafting / mechanical reconciliation / option generation
(GOV-2 s11). This author does NOT certify boundary completeness; the independent Codex
confirmation does.

Repository base: `main` @ 1e91f897 (unchanged, nothing pushed). Provisional PRD-339 design
head: 0348cee1 on branch `claude/prd-339-effective-permission-design` (NON-AUTHORITATIVE
provisional drafting, GOV-2 s4; not modified by this packet cycle).

Docs-only CI boundary (GOV-2 s8): CI on this documentation branch confirms only that the
branch preserves the current green baseline. It does not execute or validate the proposed
runtime design, consumer inventory, or regression plan.

---

## 0. Evidence provenance (synthesized, not imported wholesale)

Inputs: research dossier `/home/dustin/cuttingboard-ultra-permission/ULTRA_REVIEW/`
(read-only, out of repo); provisional PRD-339 design at 0348cee1; bounded source recon at
1e91f897; and the GOV-2 boundary-reset inventory refresh (2026-09-12) that completed the
consumer surface. Line numbers verified against the working tree.

PROVISIONAL DESIGN CONSULTATION (NOT this packet review, NOT the post-ruling PRD review):
during design drafting, gpt-6-astra returned ACCEPT and gpt-5.6-sol returned CLEAN on the
DESIGN head 0348cee1. IMPORTANT: those consultations reviewed the boundary the design
author CHOSE (board / directives / viewer / Telegram formatter / publisher). The GOV-2
initial packet review then proved that boundary INCOMPLETE (s3 below). The design
consultations therefore remain useful evidence for the surfaces they covered but do NOT
establish consumer-inventory completeness and do NOT satisfy the post-ruling PRD review.

No credentials or credential-shaped literal values are reproduced here.

---

## 1. Why this work is MATERIAL (GOV-2 s1)

Matches multiple s1 triggers (any one sufficient): claims to enumerate all permission
consumers; selects a carrier/seam shared across pipeline layers; establishes FILES/LOC
ceilings; adds a persisted schema surface with many readers/presentation paths; resolves
High findings; and crosses runtime + contract + notification + delivery + dashboard +
reporting + persistence. MATERIAL, ineligible for LANE: MICRO. CLASS (CONTRACT vs
EXECUTION) and lane (HIGH-RISK) are owner rulings (Q7); not presumed here.

---

## 2. Exact existing production problem

Cuttingboard has a canonical decision PRODUCER but NO canonical carrier of EFFECTIVE
PERMISSION over time. The daily pipeline materializes the finalized contract + post-gate
decisions (`runtime/__init__.py:1012-1055`, actionable-TRADE select :1051-1055, permission
baked :1146) and a daily run summary (`_build_run_summary` :1705-1769). But every surface
that ASSERTS permission independently reconstructs it from a PROXY -- `system_state.tradable`,
regime posture, candidate/`top_trades` presence, `notify_mode`, filename, or publish arrival
order -- instead of reading one resolved effective state. Under the fail-closed operator
lock (`config.py:79-115`, absent CB_OPERATOR_AVAILABILITY => CANNOT_MONITOR) the positive
variants are masked; an AVAILABLE unlock would expose them.

---

## 3. Confirmed empirical reproductions (dossier F1-F9) + corrected traces

Reproduced offline at 1e91f897 (dossier 02/03). CORRECTIONS from the initial packet review
are marked [CORRECTED].

- F7 HOURLY PLACEHOLDER (MEDIUM): daily TRADE + benign hourly NO_TRADE placeholder renders
  STAY FLAT. Hourly `_build_hourly_*` (:2357-2530) hard-codes the placeholder (:2377, :739);
  renderer reads selected `--run` outcome (:2766) mapped to STAY FLAT (:2989-3002). CONTROL:
  current hourly HALT renders HALT.
- F2 RESTRICTION CONTINUITY (HIGH): a later benign hourly artifact replaces a prior HALT;
  hourly entry recomputes without prior restriction state (:627-669); latest hourly artifacts
  overwrite prior safety evidence (:2537-2547).
- F1 STALE PUBLICATION (HIGH, reproduced with real `ci_push_artifacts.sh` + local remote):
  newer HALT then delayed older TRADE ended with TRADE on `publish`; publisher overlays by
  completion order, no semantic comparison (attempt_publish :90-178, retry :180-198).
- F5 NON-ATOMIC BUNDLE + SAME-SECOND IDENTITY (HIGH): older/newer interleaving splits
  latest_run vs latest_contract; same-second `generation_id` (mode+second, :3127-3134)
  collided.
- F3 CONTRACT-VIEWER INFERENCE (HIGH, real ui/app.js): `derivePosture(status, tradable)`
  returns TRADE_READY (ui/app.js:87-93) -> renderSignalBar (:120-138); renderPrimaryTrade
  (:140-164) shows a trade card on candidate presence; renderNoTrade/renderWatchlist
  (:166-208) on posture; outcome badge (:518-530, :561) is resolved.
- F8 ACTION LANGUAGE ESCAPES VERDICT (MEDIUM): renderer directives key on operator_locked
  alone (:2420-2421, :2479-2480, :3452-3460, :2533/:3445); A+ tier "ACTIONABLE" is a grade
  proxy (:972-977). [CORRECTED] Telegram: the LIVE hourly seam is
  `notifications/__init__.py:format_hourly_notification` (:532-578) via `_action_label`
  (:150-169), invoked at `runtime/__init__.py:675-684` WITHOUT passing `canonical_outcome`
  (so the title derives from posture/qualification proxy). `notifications/formatter.py`
  `_format_hourly` (:122-158) contains the "READY"/"Tradable" wording but is a
  dispatch/formatting layer, not the sole live seam -- the initial packet mis-cited it as
  the production reproduction. The conclusion (Telegram must consume the carrier) stands;
  the seam is now correctly traced.
- F6 STALE/FUTURE ADMISSION (HIGH static, partial): coherent publish gate accepted a
  future-dated timestamp; no live stale-page incident reproduced.
- F4 SPLIT EXECUTION/INPUT LANES (HIGH conditional, code+handoff, not concurrently
  reproduced): local cron (L6) + hidden external-trigger Worker (L13); present rejection is
  accidental containment, not an authority boundary.
- F9 SEND-BEFORE-DURABLE (LOW for permission correctness): notification precedes durable
  writes (daily :1164-1200 before latest writes :408-437; hourly send :675-684 before
  `_write_hourly_artifacts` :2543-2547). A delivery guarantee, not a permission-origin defect.

---

## 4. COMPLETE producer-to-final-consumer authority map (GOV-2 s6 inventory refresh)

PRODUCER (positive-permission origin): daily gates + actionable select (:1012-1055) ->
finalized contract (`_build_and_finalize_contract` :1066-1217) + daily summary (:1705-1769);
`system_state.permission/tradable` + `trade_candidates` set in `contract.py`; operator lock
zero-sizes an allowed decision (`execution_policy.py:287-288`); daily HALT bypasses decision
production (:1300-1318). Hourly observation recompute (:627-669) -> hourly bundle
(:2357-2530), NO_TRADE placeholder, no daily decision chain.

CONSUMERS that assert/project permission (COMPLETE inventory; P=reads a PROXY,
R=reads resolved outcome/permission):

(A) Dashboard board -> ui/dashboard.html, ui/index.html
- dashboard_renderer decision-state + permission (R): :2766-2775 reads run.outcome/
  permission; :2989-3009 emits HALT/TRADE PERMITTED/STAY FLAT/OBSERVE ONLY/STATE UNAVAILABLE;
  :3032-3034 headline + data-raw-permission; `_verdict_sentence` :2045-2079.
- dashboard_renderer `_regime_to_permission_verb`/`_key` (P): :1875-1928, fed as
  `regime_permission` :2017.
- A+ tier "ACTIONABLE" grade label (P): `_TIER_DEFS` :972-977.
- dashboard_integrator screen-verdict directives (P): :40-107 from regime_permission +
  qualifying directions; verdict literals :33-39, :139-166.
- market_control_card values ACTIONABLE/NO_ACTIVE_CANDIDATES (P): market_control_card.py,
  surfaced via dashboard_renderer `_MCC_VALUE_DISPLAY` :197-213.

(B) Contract viewer -> ui/app.js (reads ui/contract.json + latest_payload.json)
- derivePosture(status, tradable) TRADE_READY (P): :87-93; renderSignalBar :120-138.
- renderPrimaryTrade (P, candidate presence): :140-164; renderNoTrade/renderWatchlist
  (P, posture): :166-208.
- outcome badge (R): _outcomeBadgeClass/_renderOutcomeBadge :518-530, :561; top_trades table
  (P): :547-552.

(C) Telegram
- Daily `build_notification_message` (R + candidate fallback): output.py:1144-1210,
  reads contract.outcome/permission (+ candidate presence :1159-1165); sent at
  runtime :339, :1187.
- Hourly `format_hourly_notification` (P): notifications/__init__.py:532-578 via
  `_action_label` :150-169; invoked runtime:675-684 (no canonical_outcome passed).
- Shared `notifications/formatter.py` (P): format_telegram_alert :92-119; _format_hourly
  "READY"/"NO SETUP"/"STAY FLAT" :122-158; setup-ready/forming :255-293.
- Notification GATE `notifications/state.py` (P): notification_state_key (tradable ->
  TRADE_READY/STAY_FLAT) + classify_notification_priority (tradable -> HIGH) :50-115; called
  runtime:340-341, :1171-1172 -- DECIDES WHETHER TELEGRAM SENDS.

(D) JSON payload artifact(s)
- `build_report_payload` (R summary + P top_trades): payload.py:63-184 emits
  summary{outcome,permission,tradable} + sections.top_trades.
- transport `deliver_json` -> latest_payload.json / latest_hourly_payload.json :34-41.
- daily summary dict (R) -> latest_run.json (:1755-1769 via safe_write_latest :2312);
  error/halt permission :2495-2506; failure permission :3186.

(E) Text / HTML report artifact(s)
- `render_report` (R): output.py:293-630 SYSTEM HALT / NO TRADE / A+ TRADES body ->
  reports/<date>.md.
- `render_report_from_payload` (R-from-P): output.py:633-720 reconstructs TRADE from
  top_trades presence :665-670; operator-lock from summary.permission :718.
- `html_renderer.render_html` :15-23 wraps it -> report.html via deliver_html
  (transport.py:22-31).

(F) CLI stdout
- `deliver_cli` (P + R mix): transport.py:44-63 prints TRADABLE / EXECUTION: OBSERVATION
  ONLY / TOP_TRADES.

(G) Premarket / postmarket reports (carried in PipelineResult; feed reports + audit)
- build_premarket_report (P): premarket.py:370-419 reads tradable, operator-lock string,
  candidate/no-entry language; built runtime:1547.
- postmarket (P): postmarket.py:31-33 posture->tradable; :129-149 operator-lock;
  :201-223 "qualified for execution"/"met analytical qualification"; built runtime:1548,
  carried :1689-1690.

(H) Other permission-adjacent
- notifications/hourly_slot.py (hourly-slot gating token, upstream of hourly Telegram).
- alert_runner.py (delivery/send entrypoint carrying outcome-derived text).

PUBLISHER / SERVE:
- ci_push_artifacts.sh: bootstrap direct-push :57-68; changed-set overlay :98-146; retry
  :180-198; origin/main static ui/* sync excludes ui/dashboard.html|index.html|contract.json
  (they publish via the changed-set overlay). No semantic comparison.
- pages.yml deploys the `publish` checkout on any upstream completion (no conclusion gate).

SCOPE CONSEQUENCE (design-direction input): the provisional PRD-339 design at 0348cee1
addressed only (A) board/directives, (B) viewer, (C) Telegram formatter, and the publisher.
The complete inventory adds classes (C: notification GATE state.py + daily builder),
(D) payload, (E) text/HTML report, (F) CLI, (G) premarket/postmarket, and several (A)
proxy sub-consumers (integrator, regime-verb, A+ tier, market_control_card). Whether the
correction must reach ALL of these or a narrower authoritative subset is an owner
design-direction choice (Q8 below), not settled by code.

---

## 5. Current permission carriers and why none is a sufficient effective-permission carrier

| Carrier | Role | Why insufficient |
|---|---|---|
| finalized latest_contract.json + post-gate decisions | best decision record | decision record, not effective permission over time; latest-write not transactional with summary/payload |
| latest_run.json daily summary (outcome/permission) | projection | NOT restored by either lane (s6 evidence); generation_id = mode+second (collides) |
| system_state.permission (text) | human text | posture-derived; direction under NO_TRADE; never a grant |
| system_state.tradable | regime posture | not post-policy permission; read as a grant by viewer, notification gate, premarket/postmarket, CLI |
| top_trades / trade_candidates presence | candidate list | presence read as permission by report adapter, viewer primary-trade, CLI, payload |
| hourly latest_hourly_* | current observation | no decision chain; placeholder; overwrites prior safety evidence |
| ui/contract.json | viewer input | meaning alternates daily/hourly; filename carries no authority |
| publish branch / Pages | transport/serve | commit order is transport order, not semantic authority |
| generation_id (mode+second) | identity | collides same-second; not unique invocation/order identity |

No existing carrier represents effective permission that is temporally constrained,
restriction-continuous, publication-safe, AND consumed uniformly by every surface in s4.

---

## 6. Reuse vs new carrier -- an OWNER CHOICE, not a proven necessity [CORRECTED]

The initial packet asserted "reuse cannot satisfy the invariant." The initial review
correctly flagged this as an overstatement, and the dossier itself says its probes do NOT
prove a new persisted file necessary and that reuse/extension remains a real design option
(ULTRA_REVIEW/02_temporal_forensics_summary.md:19-25). CORRECTED position:

FACTS (verified): the daily lane restore step does NOT restore latest_run.json or
latest_contract.json (`.github/workflows/cuttingboard.yml:242-248`); the hourly lane
restores latest_run.json read-only and reverts it (`hourly_alert.yml:108-124, :216-222`);
`ci_restore_publish_state.sh` restores listed paths from origin/publish and cleanly skips a
first-use-absent path. These restore lists are CHANGEABLE WIRING.

TWO REAL OPTIONS for the owner (Q6):
- REUSE/EXTEND an existing run/contract carrier: add the effective-permission fields to it,
  add it to BOTH lanes' restore + force-add sets, and change its ownership/admission rules.
  Requires the same category of workflow change a new file requires.
- NEW dedicated accepted-authority file: single-purpose, restored+written by both lanes.
  Cleaner separation; avoids overloading a multi-purpose carrier's revert semantics.

AUTHOR RECOMMENDATION (NOT authority): the dedicated file, for separation and to avoid
changing latest_run/latest_contract revert semantics. But reuse is viable; Q6 is a genuine
owner choice, and this packet no longer presents "reuse impossible" as fact.

---

## 7. The confirmed defect boundary + the atomic publish bundles

Defects a fix must close: restriction-continuity (F2/F7); recovery semantics (owner Q1/Q4);
publication non-regression (F1); hourly placeholder authority (F7); consumer inference across
the COMPLETE s4 inventory (F3/F8), NOT just board+viewer+Telegram-formatter; identity/
same-second collision (F5); action-language consistency (F8).

ATOMIC PUBLISH BUNDLES (Finding 5, enumerated):
- DAILY (`.github/workflows/cuttingboard.yml:512-538`): forces `logs/` (incl.
  latest_run.json, latest_contract.json, latest_payload.json, market_map.json), `reports/`;
  copies latest_contract.json -> ui/contract.json; renders ui/dashboard.html + ui/index.html;
  reverts latest_hourly_contract.json to HEAD. Permission-STATE files in this bundle:
  latest_run.json, latest_contract.json, latest_payload.json, ui/contract.json,
  ui/dashboard.html, ui/index.html (+ the reports/<date>.md and report.html if published).
- HOURLY (`hourly_alert.yml:228-256`): force-stages latest_hourly_run.json,
  latest_hourly_contract.json, latest_hourly_payload.json, audit/regime/etc; stages
  ui/contract.json, ui/dashboard.html, ui/index.html; explicitly does NOT stage the
  pipeline-owned latest_run.json/latest_payload.json/market_map.json.
A publication non-regression guard must define WHICH files form each admitted atomic bundle,
and which it compares vs overwrites vs leaves untouched -- across BOTH bundles, including the
payload artifacts (now authority-bearing per s4-D/E).

---

## 8. Code correctness vs owner-operational cleanup vs live commissioning (kept separate)

CODE (eventual PRD): the effective-permission carrier + composition; monotonic restriction +
recovery; consumer fidelity across the s4 inventory (scope per Q8); publication
non-regression across both bundles; identity/atomicity.
OWNER-OPERATIONAL (not code; dossier 07): retire local cron (L6); dispose hidden Worker +
credentials (L13); revoke credential-named binding; decide CB_OPERATOR_AVAILABILITY
(`config.py:61-71, 79-115` fail-closed, no expiry/auto-unlock today). The code guard rejects
lower/older authority regardless of source; a stray writer forging a HIGHER authority is
prevented only by the owner single-authorized-writer boundary.
LIVE COMMISSIONING (separate; not code, not this packet): CF-E1 natural cycle; any
production AVAILABLE run. Manual downstream proof is not CF routine proof.
DEFERRED: served-Pages ordering (F1 extension, unproven); F9 delivery atomicity;
operator-channel docs; ui/contract.json alternation (A2); empty entry ladder (A1);
M4/M5/M11; PRD-336 disposition.

---

## 9. Estimated implementation surface (GOV-2 s5 -- ESTIMATED SURFACE, NOT YET APPROVED)

ESTIMATED SURFACE -- NOT YET APPROVED (not a constraint until Gate A on the reviewed PRD).
The boundary reset materially EXPANDED this from the provisional design's ~11 files.

Core carrier + producer + publisher (all options): new `cuttingboard/effective_permission.py`,
new `tools/publish_authority_guard.py`; edits `runtime/__init__.py`, `contract_types.py`,
`tools/ci_push_artifacts.sh`, `.github/workflows/cuttingboard.yml`,
`.github/workflows/hourly_alert.yml` (+ reuse would edit an existing carrier instead of the
new file). ~8 files.

Consumer fidelity, by class (scope set by Q8):
- (A) board: `dashboard_renderer.py`, `dashboard_integrator.py`, `market_control_card.py`
- (B) viewer: `ui/app.js`
- (C) Telegram: `notifications/__init__.py`, `notifications/formatter.py`,
  `notifications/state.py`, `output.py` (daily builder)
- (D) payload: `delivery/payload.py`, `delivery/transport.py`
- (E) report: `output.py` (render_report/render_report_from_payload), `delivery/html_renderer.py`
- (F) CLI: `delivery/transport.py`
- (G) reports: `reports/premarket.py`, `reports/postmarket.py`

FULL-SCOPE estimate: ~18-24 production files; LOC materially larger than the provisional
~300-500 (estimate only, pending Q8 scope + Q6 carrier). NARROWED-SCOPE (Q8) would be
smaller. Tests scale with scope. These are ESTIMATES; the first binding ceiling is Gate A.
An author must not shrink a truthful consumer/schema consequence to preserve an estimate.

---

## 10. Owner design-direction questions (do NOT presume answers)

Q1 -- SESSION VALIDITY: carry admitted AM permission through the session unless an
authoritative restriction/new decision changes it, VS OBSERVE-ONLY until reconfirmation.
Author recommendation (NOT authority): carry, with monotonic restrictions. Owner decides.

Q3 -- STRUCTURE: one PRD VS ordered PRDs with a safe fail-closed intermediate. Author
recommendation: split (now stronger given the expanded consumer scope). Owner decides.

Q4 -- RECOVERY AUTHORITY: confirm only a full daily redecision (higher decision sequence +
validated recovery basis + satisfied restrictions) lowers restriction / restores permission;
no auto-unlock; a still-CANNOT_MONITOR setting is not cleared by a redecision.

Q6 -- CARRIER: reuse/extend an existing carrier VS a new dedicated accepted-authority file
(s6). Genuine owner choice; author recommends the dedicated file but reuse is viable.

Q7 -- CLASSIFICATION / REVIEW PROVENANCE: confirm MATERIAL; rule CLASS (CONTRACT vs
EXECUTION) and lane (HIGH-RISK); set the PRD-242 / commissioned-review record for the
post-ruling fresh-context independent PRD review.

Q8 -- CONSUMER SCOPE (NEW, surfaced by the boundary reset): must the correction bring EVERY
permission-asserting surface in s4 (board + integrator + market-control-card + viewer +
daily/hourly Telegram + notification gate + payload + text/HTML report + CLI + premarket/
postmarket) under the one carrier, VS a narrower authoritative subset (e.g. the served
decision surfaces: board + viewer + Telegram + payload) with the rest explicitly documented
as non-authoritative analytical context? This sets the true FILES/LOC surface (s9) and is
the central owner design-direction choice this boundary reset exposes. Author recommendation
(NOT authority): define one resolved effective-permission field at the producer and have
every ACTION/PERMISSION-asserting surface consume it; surfaces that emit only analytical
context (grades, posture) may remain if they carry no action/permission claim -- but that
line is Dustin's to draw.

If the review surfaces another TRUE owner choice, it is added. No preference question is
invented for matters already determined by code.

---

## 11. GOV-2 sequence status (this packet)

1. Author investigation + self-verification: DONE.
2. Provisional MATERIAL packet: rev 1 @ d3522046.
3. INITIAL PACKET REVIEW (Sol @ d3522046): DESIGN INCOMPLETE / boundary reset ->
   CODEX_EVENT_1_REVIEW_2026-09-12.md.
4. ONE consolidated correction = the s6 inventory refresh: THIS rev 2.
5. EXACT-CORRECTED-HEAD CONFIRMATION (Sol @ e006141c): DONE. F1-F6 RESOLVED, but a SECOND
   omitted class (market_map/candidate-card) found -> DESIGN INCOMPLETE (s6/s7).
   CODEX_EVENT_2_CONFIRMATION_2026-09-12.md.
6. STOP. The bounded cycle is exhausted and the packet is NOT review-clean, so the s2-step-6
   design-direction ruling cannot be issued yet. Instead, the s6 rebuild/narrow/park owner
   decision is now required (s12).

PRD-339 remains PROVISIONAL and non-authoritative; the post-ruling fresh-context independent
PRD review (GOV-2 s2 step 7) has NOT run and is not run here.

---

## 12. DESIGN INCOMPLETE -- owner decision required (GOV-2 s6)

The bounded MATERIAL cycle found TWO independent omitted permission-consumer classes (the
delivery payload/report/CLI/premarket-postmarket class at the initial review; the
market_map decision-guidance artifact/candidate-card class at the confirmation). Per GOV-2
s6, incremental patching stops and Dustin chooses ONE of:

- REBUILD (recommended): commission a truly EXHAUSTIVE producer-to-final-consumer
  permission inventory FIRST (all of s4 A-H PLUS market_map/if_now/PLAY, and any surface a
  fresh exhaustive sweep finds), then re-frame the boundary and re-open the packet cycle.
  The two resets indicate the surface is large enough that the boundary must be established
  by exhaustive inventory, not incremental discovery.
- NARROW: restrict the packet's authoritative claim to a named subset of served decision
  surfaces (e.g. board decision-state + contract viewer + Telegram + payload summary) and
  DOCUMENT every other surface (reports, CLI, premarket/postmarket, market_map if_now/PLAY,
  A+ tier, market_control_card) as explicitly NON-AUTHORITATIVE analytical context that must
  not assert current permission. This makes the boundary small and provable but requires
  the owner to accept those surfaces as non-authoritative.
- PARK: shelve the packet.

Q8 (consumer scope) must, on any rebuild, be extended to include the market_map
`trade_framing.if_now` / `preferred_trade_structure` (PLAY) seam and its published artifact.

This packet makes no recommendation on Q1/Q3/Q4/Q6/Q7 beyond those already stated as
author recommendations (non-authority), and issues no ruling. The provisional PRD-339 design
(0348cee1) is now known to rest on an incomplete boundary and must be reconciled to whatever
frame Dustin selects before it can become authoritative.
