# PRD-339 Effective-Permission MATERIAL Packet (2026-09-12)

STATUS: PROVISIONAL (GOV-2 s2). Not review-clean. Grants no downstream authority.
No implementation, no Gate A, no design-direction ruling is created by this packet.

Author capability: provisional drafting / mechanical reconciliation / option generation
(GOV-2 s11). This author does NOT certify boundary completeness; the GOV-2 independent
Codex packet review does that (s "No agent certifies the completeness of the boundary it
chose").

Repository base: `main` @ 1e91f897 (session start; unchanged, nothing pushed).
Provisional PRD-339 design head: 0348cee1fb71ac46b8ed2109f82cde9969491fcf on branch
`claude/prd-339-effective-permission-design` (NON-AUTHORITATIVE provisional drafting per
GOV-2 s4; not modified by this packet cycle).

Source line numbers in this packet were verified against the working tree at 1e91f897 by
bounded read-only recon during the design cycle; this packet re-uses that verification and
does NOT open a new broad reconnaissance (per charge).

Docs-only CI boundary (GOV-2 s8): CI on this documentation branch confirms only that the
branch preserves the current green baseline. It does not execute or validate the proposed
runtime design, consumer inventory, or regression plan.

---

## 0. Evidence provenance (synthesized, not imported wholesale)

Durable inputs synthesized here:
- Research dossier (read-only, out of repo): `/home/dustin/cuttingboard-ultra-permission/
  ULTRA_REVIEW/` -- 00_READ_ME_FIRST, 01_astra_authority_review, 02/03 temporal forensics,
  04_execution_authority_map, 05_prd339_original_candidate, 06/07.
- Provisional PRD-339 design at 0348cee1 (this packet reduces, it does not restate, that
  design).
- Bounded source recon at 1e91f897 (verified line numbers below).

PROVISIONAL DESIGN CONSULTATION (not the GOV-2 packet review, not the post-ruling PRD
review): during design drafting, two external models reviewed the PRD-339 DESIGN across
several rounds -- gpt-6-astra returned ACCEPT (authority-invariant) and gpt-5.6-sol
returned CLEAN on the exact design head 0348cee1. These are valuable design evidence. They
do NOT satisfy (a) this upstream MATERIAL packet review, or (b) the required post-ruling
fresh-context independent PRD review (GOV-2 s2 step 7). Both remain pending.

No credentials or credential-shaped literal values are reproduced here (per charge and
the wall's SECURITY clause).

---

## 1. Why this work is MATERIAL (GOV-2 s1)

The proposed work matches multiple s1 triggers, any one of which is sufficient:
- Enumerates all permission-asserting consumers/renderers/outputs (headline, action
  directives, contract viewer, Telegram) and claims completeness across them.
- Selects an implementation seam/carrier shared across pipeline layers (a persisted
  effective-permission carrier read/written by the daily producer, the hourly producer,
  every consumer, and the publisher).
- Establishes a production FILES ceiling and LOC ceiling.
- Adds a persisted schema surface (effective_permission on the run summary + PipelineContract
  + a dedicated accepted-authority file) with MORE THAN ONE reader and presentation path.
- Resolves High-risk findings (reproduced permission defects, ranked HIGH by the dossier).
- Crosses two-or-more of runtime, contract, notification, delivery, dashboard, persistence
  (it crosses all of these).

Therefore the work is MATERIAL and ineligible for LANE: MICRO (GOV-2 s1). It requires the
s2 order to clear before any durable downstream PRD authority, decision entry, or
implementation.

Classification is MATERIAL. The precise CLASS (CONTRACT vs EXECUTION) and lane
(HIGH-RISK) are surfaced to the owner as Q7; this packet does not presume that ruling.

---

## 2. Exact existing production problem

Cuttingboard has a canonical decision PRODUCER but NO canonical carrier of EFFECTIVE
PERMISSION over time. The daily pipeline materializes the finalized contract and post-gate
decision set (`cuttingboard/runtime/__init__.py:1012-1055`, actionable-TRADE select
:1051-1055) and a daily run summary (`_build_run_summary` :1705-1768). But every surface
that ASSERTS permission independently reconstructs it from a proxy -- `notify_mode`,
`system_state.tradable`, posture, filename, or publish arrival order -- rather than reading
one resolved effective state. Under the current fail-closed operator lock
(`config.py:79-115`, absent CB_OPERATOR_AVAILABILITY => CANNOT_MONITOR) the positive-
permission variants are masked; an AVAILABLE unlock would expose them.

---

## 3. Confirmed empirical reproductions (dossier F1-F9; dispositions)

All reproduced offline at 1e91f897 (dossier 02/03; controls preserved). Ranked by the
dossier; HIGH unless noted.

- F7 HOURLY PLACEHOLDER (MEDIUM, reproduced): daily TRADE + a benign hourly NO_TRADE
  placeholder renders STAY FLAT. The hourly `_build_hourly_*` (:2357-2530) hard-codes the
  NO_TRADE placeholder outcome (:2377, :739); the renderer reads the selected `--run`
  outcome (:2766) and maps it to STAY FLAT (:2989-3002). Daily carriers untouched. CONTROL:
  a current hourly HALT correctly renders HALT (same-run precedence intact).
- F2 RESTRICTION CONTINUITY (HIGH, reproduced): a later benign hourly artifact replaces a
  prior HALT; the renderer does not recover it. Hourly entry recomputes without prior
  restriction state (:627-669); latest hourly artifacts overwrite prior safety evidence
  (:2537-2538).
- F1 STALE PUBLICATION (HIGH, reproduced with the real `tools/ci_push_artifacts.sh` + a
  local bare remote): a newer HALT published first, then a delayed older TRADE published
  second, ended with TRADE bytes on `publish`. The publisher overlays by completion order
  with NO semantic comparison (attempt_publish :90-178, retry :180-198).
- F5 NON-ATOMIC LATEST BUNDLE + SAME-SECOND IDENTITY (HIGH, reproduced): older/newer
  helper interleaving splits `latest_run` vs `latest_contract` across generations; two
  same-mode invocations at the same second produced the identical `generation_id`
  (mode+second, :3127-3134).
- F3 CONTRACT-VIEWER INFERENCE (HIGH, reproduced with the real `ui/app.js`):
  `derivePosture(status, tradable)` returns TRADE_READY for an OK + tradable=true contract
  ignoring outcome and lock (ui/app.js:87-93); it feeds renderSignalBar (:120-123). Other
  viewer blocks (renderNoTrade/renderWatchlist :166-207, renderPrimaryTrade/
  renderSecondarySetups :140-235, payload badge :518-562) gate on the same proxy or on
  candidate presence.
- F8 ACTION LANGUAGE ESCAPES VERDICT (MEDIUM, reproduced at the renderer boundary): A+
  ACTIONABLE / IF NOW survive a NO_TRADE/HALT board; directives key on operator_locked
  alone (:2420-2421, :2479-2480, :3452-3460, :2533/:3445), not on the effective verdict.
  Telegram formatter derives `tradable = posture != STAY_FLAT` and emits "READY" /
  "Tradable: Yes" with no permission input (`cuttingboard/notifications/formatter.py:124-125,
  142, 150, 259`).
- F6 STALE/FUTURE ADMISSION (HIGH static, partial): the coherent publish gate accepted a
  future-dated (2099) payload timestamp; no live stale-page incident reproduced.
- F4 SPLIT EXECUTION/INPUT LANES (HIGH conditional, code+handoff confirmed, not
  concurrently reproduced): local cron (L6) and a hidden external-trigger Worker (L13) can
  execute the engine against the working tree / dispatch hourly; present rejection is
  accidental containment, not an authority boundary.
- F9 SEND-BEFORE-DURABLE (LOW for permission correctness, code confirmed): notification
  precedes durable artifact writes (daily notify inside `_build_and_finalize_contract`
  :1164-1200 before the summary/latest writes :408-437; hourly send before
  `_write_hourly_artifacts` :720-746). A delivery guarantee, not a permission-origin defect.

Controls (do not regress): same-run HALT precedence; the main dashboard operator-lock
carrier renders OBSERVE ONLY and suppresses IF NOW; the hourly path does not mutate the
persisted daily decision.

---

## 4. Producer-to-consumer authority map

PRODUCER (positive-permission boundary):
- Daily pipeline: decision gates + actionable select (:1012-1055) -> finalized contract
  (`_build_and_finalize_contract` :1066-1217) + daily run summary (:1705-1768). Operator
  lock zero-sizes an allowed decision (`execution_policy.py:287-288`); daily HALT bypasses
  decision production (:1300-1318).
- Hourly observation: recompute (:627-669) -> hourly bundle (:2357-2530) with a NO_TRADE
  placeholder; carries `notify_mode` (:2490); no daily decision chain.

CONSUMERS that assert permission today (the enumerated set this work must bring under one
carrier):
- Board headline / decision-state (`dashboard_renderer.py` mapping :2989-3002, lock
  override :3008-3009).
- Action directives (IF NOW :2420-2421, PLAY :2479-2480, A+ tier :3452-3460, chart
  neutralization :2533/:3445).
- Contract viewer (`ui/app.js`): signal bar (:87-123), no-trade/watchlist (:166-207),
  primary/secondary trade (:140-235), payload badge (:518-562).
- Telegram (`notifications/formatter.py`) action-bearing formats (:122-166, :259).

PUBLISHER / SERVE:
- `tools/ci_push_artifacts.sh`: bootstrap direct-push (:57-68), changed-set overlay
  (:98-146), retry (:180-198); the origin/main static ui/* sync excludes the three
  generated boards (they publish via the changed-set overlay). No semantic comparison.
- `pages.yml`: deploys the `publish` checkout on any upstream completion (no conclusion
  gate).

---

## 5. Current permission carriers and why they are insufficient

| Carrier | Role | Why insufficient as effective permission |
|---|---|---|
| finalized `latest_contract.json` + post-gate decisions | best decision record | a decision record, not effective permission over time; its latest-write is not transactional with summary/payload |
| `latest_run.json` daily summary | outcome/permission/halt projection | a projection; NOT restored by either lane (see s6); `generation_id` = mode+second (collides) |
| `system_state.permission` (text) | human text | posture-derived; expresses direction even under NO_TRADE; never a grant |
| `system_state.tradable` | regime posture | not post-policy permission; true while locked or blocked |
| hourly `latest_hourly_*` | current observation | no decision chain; NO_TRADE placeholder; overwrites prior safety evidence |
| `ui/contract.json` | viewer input | meaning alternates daily/hourly by producer; filename carries no authority |
| `publish` branch / Pages | transport/serve | commit order is transport order, not semantic authority |
| `generation_id` (mode+second) | identity | collides same-second; not unique invocation/order identity |

No existing carrier represents effective permission that is temporally constrained,
restriction-continuous, and publication-safe.

---

## 6. Dedicated effective-permission carrier evidence (reuse proven insufficient)

The design's most consequential choice is a NEW dedicated persisted accepted-authority
file. Evidence that REUSE cannot satisfy the invariant (verified against source):
- The daily lane "Restore publish state" restores audit/evaluation/last_notification_state/
  market_map/latest_hourly_contract/regime_history/run_*.json -- but NOT `latest_run.json`
  or `latest_contract.json` (`.github/workflows/cuttingboard.yml` restore step ~244). The
  daily decision carriers are never restored, so cross-run continuity cannot ride them.
- The hourly lane restores `latest_run.json` READ-ONLY and reverts it
  (`.github/workflows/hourly_alert.yml:123-124, :222`), writing only `latest_hourly_*`.
- `tools/ci_restore_publish_state.sh` restores explicitly-listed paths from `origin/publish`
  and skips a legitimately-absent path (first use) -- so a dedicated file can be added to
  both lanes' restore + force-add sets and bootstrap cleanly.

Conclusion: no existing restored carrier holds cross-run effective permission; a single
dedicated file, restored+written by BOTH lanes, is the smallest carrier satisfying
restriction continuity + authority-version allocation. This REVERSES the initial
"no new file" preference and is offered to the owner as Q6.

---

## 7. The confirmed defect boundary (what a fix must close)

- RESTRICTION-CONTINUITY: within a session, a HALT/lock must persist so a later benign
  observation cannot clear it (F2/F7). Requires a durable, both-lane accepted-authority
  carrier and monotonic composition.
- RECOVERY SEMANTICS (owner question, Q1/Q4): what event restores permission after a
  restriction? Design answer: only a new admitted full daily decision. The dossier does not
  assert an indefinite HALT latch as existing law; the exact validity/expiry is owner policy.
- PUBLICATION NON-REGRESSION: an older/less-restrictive bundle must not overwrite a newer
  accepted restriction on `publish` (F1). Requires an authority-version compare-and-swap on
  every publish route (overlay, bootstrap, retry), across BOTH daily and hourly state files.
- HOURLY PLACEHOLDER AUTHORITY: the hourly NO_TRADE placeholder must not be read as the
  session verdict (F7). Dissolved at the source once the hourly carries an observation
  projection of the daily effective permission.
- CONTRACT-VIEWER INDEPENDENT INFERENCE: every viewer block must consume the one carrier;
  no TRADE_READY / Primary Trade from tradable or candidate presence (F3).
- IDENTITY / SAME-SECOND COLLISION: a unique run identity + an ordering key that is not a
  second-resolution timestamp (F5).
- ACTION-LANGUAGE CONSISTENCY: renderer + Telegram action directives gate on the effective
  verdict (F8).

---

## 8. Code correctness vs owner-operational cleanup (kept separate)

CODE (belongs in the eventual PRD): the accepted-authority carrier + composition; monotonic
restriction + recovery; consumer fidelity (renderer, viewer, Telegram); publication
non-regression guard; identity/bundle atomicity.

OWNER-OPERATIONAL (NOT code scope; dossier 07): retire local cron (L6); dispose the hidden
external-trigger Worker + credentials (L13); revoke the credential-named binding; decide
CB_OPERATOR_AVAILABILITY. The code guard rejects lower/older authority regardless of writer
source, but a stray writer forging a HIGHER authority is prevented only by the owner
single-authorized-writer boundary. So F4/F5 concurrency is partly code (identity + guard)
and partly owner-operational (retire unauthorized lanes).

LIVE COMMISSIONING (separate, not code, not this packet): CF-E1 natural Cloudflare cycle;
any production AVAILABLE run. Manual downstream proof is not CF routine proof (dossier 06).

DEFERRED (not this work): served-Pages deployment ordering (F1 extension, source-unproven);
F9 delivery atomicity/at-least-once; operator-channel docs; ui/contract.json alternation
(A2); empty entry ladder (A1); M4/M5/M11; PRD-336 disposition.

---

## 9. Estimated implementation surface (GOV-2 s5 -- ESTIMATED SURFACE, NOT YET APPROVED)

ESTIMATED SURFACE -- NOT YET APPROVED (not a constraint until Gate A on the reviewed PRD):
- Production ~11 files: new `cuttingboard/effective_permission.py`,
  `tools/publish_authority_guard.py`; edits `runtime/__init__.py`, `contract_types.py`,
  `delivery/dashboard_renderer.py`, `notifications/formatter.py`, `ui/app.js`,
  `tools/ci_push_artifacts.sh`, `.github/workflows/cuttingboard.yml`,
  `.github/workflows/hourly_alert.yml`.
- Production LOC ~300-500 net (estimate, not a ceiling).
- Tests ~6 files, ~500-800 net LOC (estimate).
These figures are ESTIMATES. The first binding ceiling is the one Dustin approves at Gate A
on the reviewed PRD (GOV-2 s5). An author must not shrink a truthful consumer/schema
consequence to preserve an estimate.

---

## 10. Owner design-direction questions (do NOT presume answers)

Q1 -- SESSION VALIDITY: carry the admitted AM permission through the same session unless an
authoritative restriction or a new admitted decision changes it, VS OBSERVE-ONLY until a
reconfirmation policy. (The carrier + every requirement hold under either; this parameter
sets how composition projects a benign same-session observation.) Author recommendation
(NOT authority): carry, with monotonic restrictions -- it matches the product's decision-
support intent while remaining fail-safe. Owner decides.

Q3 -- STRUCTURE: one PRD, VS two ordered PRDs (carrier + consumer fidelity + fail-closed
UNAVAILABLE; then publication non-regression guard) with a safe fail-closed intermediate.
Author recommendation (NOT authority): split -- the authority-version does double duty but
the publisher guard + workflow wiring is a separable, independently-testable slice behind a
fail-closed intermediate. Owner decides.

Q4 -- RECOVERY AUTHORITY: confirm a full daily redecision (higher decision sequence +
validated recovery basis + satisfied restrictions) is the ONLY event that lowers restriction
/ restores permission; no auto-unlock; a still-CANNOT_MONITOR setting is not cleared by a
redecision. Owner confirms or amends.

Q6 -- CARRIER / SURFACE: approve or reject the dedicated effective_permission carrier (a NEW
persisted file, justified by s6) and the resulting ESTIMATED FILES/LOC. Owner decides.

Q7 -- CLASSIFICATION / REVIEW PROVENANCE: confirm MATERIAL; rule the CLASS (CONTRACT vs
EXECUTION) and lane (HIGH-RISK); and set the PRD-242 / commissioned-review record for the
required post-ruling fresh-context independent PRD review. Owner decides.

If the review surfaces another TRUE owner design choice, it will be added. No preference
question is invented for matters already determined by code.

---

## 11. GOV-2 sequence status (this packet)

1. Author investigation + self-verification: DONE (design cycle + bounded source recon).
2. Provisional MATERIAL packet: THIS DOCUMENT.
3. INITIAL PACKET REVIEW (independent Codex/Sol): pending -> record in
   `CODEX_EVENT_1_REVIEW_2026-09-12.md`.
4. ONE consolidated correction: pending (only if s3 reports substantive findings).
5. EXACT-CORRECTED-HEAD CONFIRMATION (independent Codex/Sol): pending -> record in
   `CODEX_EVENT_2_CONFIRMATION_2026-09-12.md`.
6. STOP for Dustin's design-direction ruling. (Not in this charge's scope to proceed past.)

Boundary-reset (GOV-2 s6): if the review reveals a previously-omitted consumer CLASS,
renderer, audit carrier, schema surface, or end-to-end seam, this packet returns to DESIGN
INCOMPLETE and stops incremental patching for Dustin to choose rebuild/narrow/park.

PRD-339 remains PROVISIONAL and non-authoritative throughout; the required post-ruling
fresh-context independent PRD review (GOV-2 s2 step 7) has NOT run and is not run here.
