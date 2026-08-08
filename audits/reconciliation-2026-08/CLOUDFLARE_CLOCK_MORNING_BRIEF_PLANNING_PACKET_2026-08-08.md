# CUTTINGBOARD — Cloudflare Clock + Morning Brief: Planning Packet

PLANNING ONLY. No implementation, no PRD allocated, no Gate A requested or
granted. Prepared for Dustin + ChatGPT review. Recon basis: `main` lineage at
`7d0805ee` (PRD-289 merge); 6 narrow read-only recon agents + direct reads;
every load-bearing claim cites a file.

**PLANNING DISPOSITION (2026-08-08): ACCEPT WITH MINOR REFINEMENTS — not
implementation-ready until E1/E2 evidence and the owner rulings below close.**

---

## 1. EXECUTIVE PROPOSAL

**Purpose.** Make CuttingBoard exist before Dustin asks for it: a truthful
morning artifact produced on a Pacific-time market-day cadence — ~6:00 brief,
then two post-open refreshes whose **semantic anchors are OPEN and OPEN+1** —
with Cloudflare as the punctual CLOCK and the existing GitHub pipeline as the
unchanged EXECUTOR. The 6:30/6:31 trigger times are **observation intents,
not guaranteed publication timestamps**: GitHub execution may land minutes
later, and the design makes that harmless (observations are bar-window
defined, §5).

**Why it belongs next (three grounded reasons, not freshness abstractions):**

1. **The current clock is wrong half the year.** `cuttingboard.yml`'s cron
   comment says "06:00 PT / 13:00 UTC" — true only in PDT. In PST the live run
   fires at 5:00 AM PT, observing an hour-younger pre-market. The DST defect
   the charge worries about already exists in production.
2. **The shipped Market Control Card never shows its post-open form.** The
   card composes only on MODE_LIVE runs (`market_control_card.py` docstring);
   the only scheduled live run is pre-open. On every normal day the published
   card renders PRE_OPEN/unavailable states all day. The OPEN / OPEN+1
   refreshes are the first scheduled runs that would light up
   STATE/TRANSITION with real open data — this arc completes the value of
   PRD-289, it doesn't sprawl past it.
3. **The open/first-minute observations don't exist anywhere.** The hourly
   workflow re-renders the dashboard at 6:30 PT but runs the notify path
   (`_execute_notify_run`), not the pipeline — daily surfaces (card, premarket
   report, candidate board) are not recomputed.

**User-visible benefit.** At 6:00 Dustin opens a board that is already
current, at true Pacific time, year-round; a promoted GAP UP/DOWN banner only
when overnight displacement is material; within minutes of the open the board
shows what the open and the first minute actually did. No notification
required — the artifact being ready IS the product.

**Why this is not feature sprawl.** No new data source, no new decision
authority, no new schema version, no scheduler framework. The slice reuses:
the existing `workflow_dispatch` entrypoint, the existing full pipeline, the
existing publish path, the existing gap vocabulary and threshold, the
existing prev-close displacement computation, and the twice-proven
additive-section wiring pattern. The genuinely new things are: one dumb
~40-line Cloudflare Worker, one PT gate in tested Python (copied from the
proven `routine_pt_slot` pattern), one new payload section, one renderer
block.

---

## 2. CURRENT SEAM / REUSE MAP

**Workflow entrypoints** (`.github/workflows/cuttingboard.yml`):
- Crons: `50 12 * * 1-5` prefetch, `0 13 * * 1-5` live, `30 23 * * 0` sunday.
- `workflow_dispatch` with one `mode` choice input (live/sunday/verify/
  prefetch); `scripts/resolve_run_mode.py` passes dispatch mode through
  verbatim (slot-keyed for crons — PRD-189 fixed a 33-day silent noop; that
  incident sets this arc's fail-loud bar).
- Concurrency group `cuttingboard-pipeline`, cancel-in-progress: false —
  triggers queue, never overlap. Every run: pip install + ruff + full pytest
  first (~minutes); job timeout 20 min; pipeline step timeout 8 min.
- Publish: live/sunday set PUBLISH_READY → commit → `ci_push_artifacts.sh` to
  the unprotected `publish` branch only (PRD-194), ref-guarded to main.
  `mode=verify` runs with **zero product side effects** (stage0-03 scheduler
  recon Q17) — the ideal end-to-end trigger-path test vehicle.

**Runtime seam:** entry `python -m cuttingboard --mode {…} --notify-mode
premarket` (`runtime/__init__.py:198` cli_main). `run_at_utc` =
`datetime.now(timezone.utc)` captured at pipeline start for all real modes
(`runtime/__init__.py:936`) — a later run truthfully gets a later run_at_utc;
no injection point exists to fake it.

**Artifact seam:** immutable per-run `logs/run_<ts>.json` accumulate;
`safe_write_latest` (monotonic run_at_utc guard, `runtime/__init__.py:1903`)
gives "latest wins" for `latest_run.json`/`latest_contract.json` for free.
Payload sections are additive (`payload.py`; `assert_valid_payload` checks
only required keys; `PAYLOAD_SCHEMA_VERSION` untouched by PRD-288/289
precedent). Renderer blocks gate solely on section presence.

**Time/freshness semantics today:** GitHub cron + PRD-250's client-side
staleness banner (board age vs viewer clock, 90-min threshold) +
`_artifact_lineage_state` per-source FRESH/STALE. Dashboard UPDATED prefers
the pipeline run's timestamp (`dashboard_renderer.py:2447`) — a refresh must
be a real pipeline run to move the displayed time (it is, in this design).

**Existing Pacific-time machinery (the pattern to copy):**
`hourly_alert.yml` runs a dumb over-provisioned UTC cron ladder covering both
DST offsets plus 5-min backups; the authoritative gate is
`routine_pt_slot(now_utc, max_lag_minutes=25)` in tested Python
(`notifications/hourly_slot.py`, ZoneInfo America/Vancouver, DST-correct);
cross-runner dedup via `logs/last_hourly_slot.json` restored from the publish
branch; suppressed fires write an audit row and skip publish via a
freshness check. **This is the "smallest safe mechanism" already proven in
this repo.**

**Existing gap / prior-close logic (reuse, do not reinvent):**
- `intraday_state_engine.py:182` `classify_gap(open_price, prev_close,
  threshold=_GAP_THRESHOLD)` → `UP`/`DOWN`/`FLAT`; `_GAP_THRESHOLD = 0.0025`
  (0.25%) — the repo's only material-gap definition. `IntraState.gap_type`
  already feeds permission logic; **post-open, the engine is the
  authoritative gap producer** — the brief must project it, never recompute.
  Note: `gap_pct` magnitude is computed but not retained on the carrier —
  surfacing magnitude needs one additive field or same-inputs recompute.
- `ingestion.py:361-370`: `fast_info.previous_close` validated fail-loud
  (PRD-262) and `pct_change = (price − prev_close)/prev_close` — the
  pre-open displacement quantity **already exists** in the quote path.
- Duplication warning: `reports/levels.py` computes a second, independent
  `prior_close`; `reports/premarket.py` carries `gap_direction` as prose and
  `overnight_high/low` as None placeholders. This arc must not create a
  third mechanism; the packet should pick one authoritative prev-close
  (recommendation: the one already threaded to the engine, so brief and
  `gap_type` can never disagree).
- Vocabulary style (verified across spy_observation / market_control_card /
  overnight_policy): state values UPPER_SNAKE, reason tokens lower_snake.

**Cloudflare prior art:** a Wrangler/`external_trigger` subsystem existed
early on and was retired as dead code, never used in production
(DECISIONS.md cleanup entries; its stale permission grants were pruned under
PRD-258). No live Cloudflare config exists anywhere in the repo. This arc
reintroduces the concept deliberately, with a product purpose the dead
subsystem never had.

**Data availability (repo side):** intraday fetch is regular-session-only
(`prepost=False`, `between_time("09:30",…)` — `ingestion.py:222,237`);
`watch.py:428` documents that the pre-open live run sees the prior session's
frame and ORB handles it as PRE_OPEN (abstain). The 6:00 brief therefore
CANNOT come from intraday bars without ingestion changes — but it doesn't
need to: the quote path already provides prev_close + last_price +
pct_change at 6:00. First-minute bar latency after 13:30 UTC is
**not documented anywhere in the repo** — external evidence required (E2
below).

---

## 3. SMALLEST VIABLE SLICE

Proves: *CuttingBoard automatically produces a truthful morning artifact on
the intended market-day cadence.*

**~6:00 PT (pre-market brief).** Cloudflare fires → `workflow_dispatch`
(ref=main, `mode=live`) → the exact run that exists today, plus the new
`morning_brief` payload section computed from the already-fetched quote data
(prev_close, reference price, displacement, classification). Notification
behavior unchanged from today's premarket run (no new notification). The
existing 13:00 UTC GH cron is left untouched in this slice as a fallback
heartbeat; a duplicate same-morning live run is safe (verified: monotonic
latest-guard, no-change publish skip, notification state-key dedup).

**6:30 PT trigger — the OPEN observation.** Cloudflare fires → dispatch
carrying scheduled-refresh intent → full live-class pipeline run, PT-gated
in Python, notifications suppressed, publish on. **6:30 is an observation
intent, not a publication guarantee**: with queueing and the test-suite
preamble, execution may land ~6:32–6:38. That is harmless because the OPEN
observation is **defined on the 09:30 ET minute-bar window** (PRD-271
session-scoped-window pattern), not on run wall-clock — run latency changes
only when the artifact arrives, never what it says. The card computes
post-open LOCATION/STATE on the same run.

**6:31 PT trigger — the OPEN+1 observation.** Same refresh-intent dispatch
one minute later. Its brief adds the first-minute observation (09:30 open →
09:31 bar), again bar-window-defined; the same latency caveat applies. It
supersedes the OPEN artifact via the existing latest-wins guard; both
immutable run files persist.

**Refresh-run mechanics — DESIGN OPTION, not locked.** Whether the two
refresh triggers dispatch a new runtime mode (e.g. `refresh`) or reuse
`mode=live` plus an explicit notification-suppression / scheduled-refresh
intent flag is deliberately left open for the MATERIAL packet. A new mode
token must justify itself against reuse of `live`: reuse means fewer new
semantics and no resolver/vocabulary growth; a new mode means cleaner
intent legibility in workflow logs and audit rows. The packet decides with
that trade stated; this plan does not pre-commit.

**What changes:** one new Worker (in-repo `cloudflare/` config, deployed by
Dustin), `cuttingboard.yml` (refresh-intent dispatch path + PT-gate step;
mode-option growth only if the packet chooses a new mode),
`resolve_run_mode.py` awareness if needed, one new brief composer module,
`payload.py` additive section, one renderer block, tests.

**What does NOT change:** the three read-only producers
(`spy_observation.py`, `intraday_state_engine.py`, `red_folder.py`);
`PAYLOAD_SCHEMA_VERSION` and all required payload keys; the decision
contract and `system_state`; ingestion fetch behavior (`prepost` stays
False in this slice); the hourly workflow; notification reach (refreshes are
silent); the publish-branch-only rule; existing GH crons (cutover is a
separate later decision, per the repo's own observed-replacement-before-
retirement precedent, stage0-03 Q18).

Explicitly out: scheduling any OTHER workflow or future sidecar from the
Worker. The Worker knows exactly one repo, one workflow file, three PT
slots.

---

## 4. MORNING BRIEF CONTRACT (proposed minimal shape)

One new additive payload section (working name `morning_brief`; final naming
at packet stage), carrying per-observation cells in the established
value-XOR-typed-unavailable style (PRD-289 pattern):

- `previous_close` — one authoritative source, the same prev-close the
  engine receives (unification with `reports/levels.py`'s independent copy
  is flagged, not silently done).
- `premarket` observation (6:00-class runs): reference price (quote
  `last_price`), `displacement_pct` (the existing PRD-262-validated
  quantity), classification via the existing threshold; typed unavailable
  reasons (e.g. quote invalid/stale) in lower_snake per convention.
- `open` observation (post-open runs): projection of the engine's
  authoritative `gap_type` + magnitude from the same inputs
  (09:30 ET bar open vs prev_close). Never a second classifier.
- `first_minute` observation: 09:30→09:31 bar displacement, present only
  when the 09:31 bar exists; typed unavailable otherwise.

**Observation-slot lineage (required).** Each run's brief section — and
therefore each immutable `logs/run_<ts>.json` — records which observation
slot the run served (PREMARKET / OPEN / OPEN_PLUS_1, exact tokens finalized
against vocabulary conventions at packet stage) clearly enough that later
inspection can distinguish the three morning artifacts without correlating
timestamps by hand. This rides the EXISTING per-run artifact as one
additional field — explicitly NOT a new historical subsystem, index, or
query surface.

**Internal states explicit, display selective:** every cell always carries
one of the closed states (UPPER_SNAKE, e.g. the existing `UP`/`DOWN`/`FLAT`
— exact final tokens verified against vocab conventions at packet stage;
`NO_MATERIAL_GAP`-style names are NOT assumed). The renderer suppresses the
FLAT/ordinary case entirely and promotes only `GAP UP +x.xx%` /
`GAP DOWN −x.xx%`. No SMALL/MODERATE/LARGE/EXTREME tiers. Raw magnitude is
the rating, rendered with fixed precision from the payload value — the
renderer computes nothing.

**Threshold (split per owner direction):**
- **Open-gap banner:** strong preference to reuse the engine's existing
  0.25% `_GAP_THRESHOLD` as the promote threshold — no new constant, no
  optimization. (D1a confirms.)
- **Premarket-displacement banner: HOLD.** Whether the same bar governs the
  pre-market quantity — and whether the quote's premarket semantics support
  a banner at all — is held pending E2 provider-semantics evidence. (D1b.)
No backfitting in either case.

**Deferred:** overnight high/low range (premarket.py's None placeholders
stay None); any gap-fill/retrace language; any second symbol; any hourly
continuation of the brief; promotion of `premarket.py` prose fields to typed
fields beyond what this section needs.

---

## 5. CLOCK / TIME DESIGN

**Principle: dumb clock, smart executor.** All semantic time logic lives in
tested Python; the Worker only fires. Trigger times are intents; semantic
anchors are the bar windows (PREMARKET quote snapshot, OPEN = 09:30 ET bar,
OPEN+1 = 09:31 ET bar).

- **Cloudflare crons (UTC-only, same limitation as GH):** six entries,
  Mon–Fri — 13:00/13:30/13:31 (PDT case) and 14:00/14:30/14:31 (PST case).
- **Worker:** optional 5-line local-time check (skip the wrong-DST-variant
  tick to save runner minutes) — best-effort optimization only, explicitly
  NOT the authority.
- **Executor gate (authoritative):** a PT-slot check in Python mirroring
  `routine_pt_slot` (ZoneInfo, DST-correct, lag-tolerant), with the morning
  slot set {6:00, 6:30, 6:31}; out-of-window dispatch → suppressed audit
  row + publish skipped (the proven hourly suppression flow). Weekends
  excluded by cron day-field AND by the gate (defense in depth).
- **Holidays:** no calendar exists in the repo and the system is
  holiday-unaware by design with safe degradation (`time_utils.py:45`). The
  pipeline already runs on weekday NYSE holidays today and produces a
  truthful degraded artifact (prior-session frame → PRE_OPEN/stale states).
  Slice 1 inherits this — no new holiday risk, no new calendar. Full
  holiday awareness is deliberately out of scope (a calendar is a new
  data-correctness surface deserving its own bounded question, G8).
- **Early closes:** unrepresented today; morning slots are unaffected by
  early closes; out of scope.
- **Determinism:** `run_at_utc` stays `datetime.now` at pipeline start —
  untouched. All brief observations are bar-window-defined, so a
  queue-delayed run yields the same observation, later — the PRD-289
  FAIL-CONDITION-11 (no wall-clock in composers) discipline extends to the
  brief composer, testable with the same fixture technique (M15: run time ≠
  wall clock).
- **DST transition days themselves:** the dual-ladder + authoritative PT
  gate handles them identically to the hourly path's proven behavior; the
  two transition Sundays are non-market days.

---

## 6. SECURITY / TRIGGER CONTRACT

- **Auth:** GitHub fine-grained PAT, scoped to `dwats250/cuttingboard` only,
  single permission (Actions: read/write), stored as an encrypted Cloudflare
  Worker secret. Sent via `Authorization` header. Never in query strings,
  never in the repo, never in artifacts (the POLYGON_API_KEY leak lesson —
  109 historical query-string exposures — is the named precedent).
- **Call:** `POST /repos/dwats250/cuttingboard/actions/workflows/
  cuttingboard.yml/dispatches` with `ref: main` (required — the publish step
  is ref-guarded to main) and `inputs: {mode: live}` or the refresh-intent
  variant per the packet's mode decision (§3).
- **Least privilege:** the PAT cannot push, merge, or read secrets; the
  workflow's own GITHUB_TOKEN does the publishing exactly as today. Rotation
  is a one-secret replacement in the CF dashboard.
- **Replay/duplicates:** a duplicate or stray dispatch is safe by existing
  construction — concurrency queue (never overlap), monotonic latest-guard,
  no-change publish skip, notification state-key dedup, plus the PT gate
  suppressing out-of-window fires with an audit row. No idempotency key
  needed; idempotency is the executor's property, not the clock's.
- **Failure visibility:** a missed fire = artifact age visible on the board
  (PRD-250 banner is the product-level signal); Worker-side logs in the CF
  dashboard; executor-side failures already fail loud and skip publish
  (PRD-287 posture). Deliberately NO new alerting channel (scope wall).
- **Blast radius if the PAT leaks:** an attacker can trigger pipeline runs
  (cost/noise, no data or merge access) — bounded and rotatable.

---

## 7. FILE / SURFACE ESTIMATE

Honest ranges (PRD-288: 195→308; PRD-289: 300→499 — both misses were
validation/vocabulary surfaces; counted here as first-class):

| Surface | Files | Est. LOC |
|---|---|---|
| Brief composer (carrier, closed vocabs, XOR-cell validation, 3 resolvers, slot-lineage field, fail-loud guards) | 1 new module | 150–250 |
| Runtime wiring (refresh-intent handling per packet's mode decision, PT gate, notify suppression, section handoff) | `runtime/__init__.py`, `runtime/_constants.py` (+possibly `notifications/hourly_slot.py` reuse) | 60–120 |
| Payload projection | `delivery/payload.py` | 20–40 |
| Renderer block (presence-gated, projection-only) | `delivery/dashboard_renderer.py` | 40–70 |
| **Production total (governing-metric style, cuttingboard/)** | ~5–6 files | **270–480** |
| Workflow | `.github/workflows/cuttingboard.yml`, `scripts/resolve_run_mode.py` | 40–80 |
| Clock | `cloudflare/wrangler.toml`, `cloudflare/worker.js` (new surface class, in-repo for docs-match-code, deployed by owner) | 50–90 |
| Tests | new `test_morning_brief*.py`, additions to workflow-resolver/slot tests, renderer tests | 400–700 |
| Docs | artifact_flow_map.md registration, PROJECT_STATE, PRD doc, DECISIONS entry | n/a |

Uncertainty is genuinely high on the composer (the PRD-288/289 pattern says
validation dominates); the range is stated rather than a fake-tight ceiling.
The MATERIAL packet should set the Gate-A ceiling at the top of the range
plus margin, not the middle.

## 8. TEST / FALSIFICATION PLAN

Every guard ships a red test (PRD-198 #4); mutation targets marked (M).

- **PT gate:** in-window PDT and PST fixtures resolve to the right slot;
  out-of-window (5:00 PST-variant tick, weekend, random hour) → suppressed
  audit row + no publish (M: remove gate → test red). DST-week fixtures both
  sides of the transition.
- **Determinism:** brief composed from fixtures where run wall-clock ≠
  run_at_utc ≠ bar timestamps — observation values keyed only on run_at_utc
  + bar windows (M: introduce `datetime.now()` in composer → red). Same
  technique as the card's M15.
- **6:00 semantics:** pre-open fixture (prior-session frame) → premarket
  observation populated from quote, open/first-minute cells typed
  unavailable; quote invalid → fail-loud unavailable reason, never a
  fabricated 0.0 (PRD-262 parity; M: substitute default → red).
- **OPEN semantics:** fixture with 09:30 bar present, 09:31 absent → open
  observation populated, first-minute typed unavailable — regardless of the
  fixture's simulated execution delay (observation-intent vs publication
  time pinned by test).
- **OPEN+1 semantics:** both bars present → first-minute populated;
  magnitude arithmetic pinned to exact expected value.
- **Slot lineage:** each fixture run's immutable summary records the
  correct observation slot (PREMARKET / OPEN / OPEN_PLUS_1); two same-slot
  runs are distinguishable from two different-slot runs on artifact
  contents alone (M: drop the field → red).
- **Banner:** FLAT → banner absent from rendered HTML (M: render-on-FLAT →
  red); UP fixture → exact `GAP UP +x.xx%` string; DOWN fixture → exact
  `GAP DOWN −x.xx%`; magnitude formatted from payload value only (M:
  renderer recomputes → red).
- **Threshold correspondence:** brief classification agrees with the
  engine's `gap_type` on identical inputs (M: second classifier drift →
  red).
- **Idempotency/duplicates:** two refresh runs same morning → monotonic
  latest-wins, both immutable run files, no duplicate notification
  (state-key dedup asserted), no-change publish skip.
- **No side effects:** refresh runs send zero notifications (M: un-suppress
  → red); no GEX/news/heatmap/Market-Map imports in the composer (import
  guard test, same pattern as banned-import guards); decision contract
  byte-identical on brief-present vs brief-absent fixtures
  (`assert_valid_payload` untouched; `system_state` untouched).
- **Failure paths:** failed executor run → non-zero exit, publish skipped
  (existing PRD-287 posture extended to the refresh path); trigger absent →
  next slot/cron proceeds independently (no cross-slot state dependency).

## 9. SCOPE WALLS (this arc does NOT include)

GEX in any form; news; registry; heatmap; Market Map retirement/coupling;
macro; any new alerting/notification channel (refreshes are silent); a
generalized scheduler UI/framework or any second scheduled consumer riding
the Worker; AI-generated commentary of any kind; threshold optimization or
backtest-derived tuning; predictive labels or gap-fill "expectations";
SMALL/MODERATE/LARGE tiers; premarket bar ingestion (`prepost` change);
holiday calendar; early-close awareness; retirement of the existing GH crons
(separate, later, observed-replacement-gated decision); changes to the three
read-only producers, the hourly workflow, PAYLOAD_SCHEMA_VERSION, or the
decision contract; any new historical/query subsystem for run inspection
(slot lineage rides the existing per-run artifact only).

## 10. MATERIALITY / GOVERNANCE RECOMMENDATION

**MATERIAL — with two cheap evidence captures BEFORE the packet is
finalized (not a GEX-0-scale provider packet).**

Why MATERIAL (GOV-2 §1 by analogy to PRD-288/289): a new external trigger
authority crossing a trust boundary (Cloudflare → GitHub, owner-held
secret); a new payload section + renderer surface (HIGH-RISK CONSUMER floor
via `dashboard_renderer.py` regardless); workflow/publish-adjacent edits
touching the PRD-194 policy area; refresh-run semantics with
notification-suppression implications. That combination is squarely what
the MATERIAL intake exists for. Expected shape: MATERIAL packet → Codex
review + exact-head confirmation → Dustin design-direction ruling → Stage-0
PRD → independent review → Gate A. Lane: HIGH-RISK / CONSUMER (+INFRA).

Why NOT a provider-evidence packet: no new data provider, no licensing
question, and Cloudflare cron behavior is deterministic and testable
end-to-end with the existing zero-side-effect `mode=verify` dispatch.

**Evidence prerequisites (bounded, read-only, before packet finalization):**
- **E1 — trigger path:** one Cloudflare Worker (throwaway, Dustin-deployed)
  dispatching `mode=verify`; confirms auth, ref targeting, queue latency,
  and end-to-end wiring with zero product side effects (stage0-03 Q17
  baseline).
- **E2 — data at the slots:** one diagnostic capture of (a) what
  `fast_info.last_price`/`previous_close` actually return at ~6:00 PT
  (premarket trade or prior-close echo — the repo cannot answer this), and
  (b) how quickly the 09:30/09:31 ET 1m bars appear via the current
  provider after the open. Both determine final contract semantics — E2
  specifically gates the premarket-displacement banner decision (D1b);
  neither is answerable from the repo.

Workflow-file changes ride the normal PR flow (GOV-1 manual merge covers
them); given the PRD-194 policy adjacency, open the eventual PR as a draft
with the governance-adjacent surface named in the body.

## 11. PARALLEL-LANE RECOMMENDATION

Safely parallel (no file overlap with this arc):
- **Context registry / NEWS-0 consolidation** — docs/data + ratification
  work; zero collision until a registry consumer touches the renderer.
- **Bounded GEX owner decision** (egress grant / fresh commission / §13e
  interpretation) — pure owner decision, no files.
- **Real-use observation of the Market Control Card** — no files; this arc
  AMPLIFIES it (first scheduled post-open card renders). Observation notes
  should feed the later Market Map narrowing decision, not this arc.

Serialize, don't parallelize: anything else touching
`delivery/payload.py` / `delivery/dashboard_renderer.py` while this arc is
in flight (single-owner rule for those seams). Market Map narrowing stays
strictly after this arc's observation window.

## 12. OWNER DECISIONS REQUIRED (smallest set)

1. **D1a — Open-gap banner threshold:** strong preference to reuse the
   engine's existing 0.25% (`_GAP_THRESHOLD`) as the promote threshold for
   v1. Confirm.
2. **D1b — Premarket-displacement banner: HOLD** pending E2
   provider-semantics evidence; ruled only after E2 lands.
3. **D2 — 6:00 content:** include the quote-based pre-market displacement
   observation in v1 (recommended), or ship open/first-minute only?
4. **D3 — Refresh shape:** two dispatches (OPEN + OPEN+1, per the charge;
   recommended) vs one ~6:32 dispatch capturing both bar windows (cheaper,
   one fewer run)? Observations are bar-window-defined either way.
5. **D4 — GH-cron fallback:** keep existing 12:50/13:00 UTC crons through
   slice 1 as heartbeat (recommended), with retirement as a later
   observed-replacement decision?
6. **D5 — Infrastructure ownership:** Dustin holds the Cloudflare account,
   deploys the Worker, and issues/rotates the fine-grained PAT (agents never
   touch the secret). Confirm.
7. **D6 — Notification posture:** refresh runs fully silent (recommended);
   6:00 run keeps today's premarket notification behavior unchanged.
8. **E1/E2 commissioning:** authorize the two bounded evidence captures
   above.

(The refresh-run mode question — new token vs `live` reuse — is a MATERIAL-
packet design decision, not an owner ruling, and is deliberately not locked
here; see §3.)

## 13. RECOMMENDED NEXT ACTION

**Commission E1 + E2** (implementation-class agent, cheap, read-only in
product terms; E1 needs Dustin's PAT + Worker deploy per D5), and in
parallel **answer D1a–D6**. With evidence and rulings in hand, **commission
the MATERIAL packet draft** (design-class model — this is vocabulary/
boundary/failure-semantics work, exactly where PRD-288/289 said expensive
reasoning pays), compiling every semantic choice out of the slice so
implementation can sprint afterward.

**Held:** PRD number, Gate A, all implementation, any GH-cron retirement,
Cloudflare deployment, evidence capture (until commissioned), and the
Cloudflare secret (owner-only).

**Readiness statement:** this plan is NOT implementation-ready. Major
semantic choices remain open by design (D1b–D3, the refresh-mode design
option, plus E2's premarket-price semantics), and pretending otherwise would
repeat the estimate-miss pattern this repo has already paid for twice.
