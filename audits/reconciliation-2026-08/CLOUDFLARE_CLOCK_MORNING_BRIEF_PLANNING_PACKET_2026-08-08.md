# CUTTINGBOARD — Cloudflare Clock + Morning Brief: Planning Packet

PLANNING ONLY. No implementation, no PRD allocated, no Gate A requested or
granted. Prepared for Dustin + ChatGPT review. Recon basis: `main` lineage at
`7d0805ee` (PRD-289 merge); 6 narrow read-only recon agents + direct reads;
every load-bearing claim cites a file. Normalized 2026-08-08 to the common
14-section packet structure (content preserved from the ACCEPT WITH MINOR
REFINEMENTS revision; no product direction changed).

**PLANNING DISPOSITION (2026-08-08): ACCEPT WITH MINOR REFINEMENTS — not
implementation-ready until CF-E1/CF-E2 evidence and the owner rulings below close.**

**READINESS: PLANNING-READY.** (Not MATERIAL-PACKET-READY: the packet draft
is gated on CF-E1/CF-E2 evidence and rulings CF-D1a–CF-D6. See §13.)

**Supersession note:** this packet supersedes the outsider memo's
(`FABLE_OUTSIDER_MEMO_2026-08-08.md` §3 rank 9 / §4) "probably cut
scheduler/freshness" recommendation. That verdict evaluated the arc as a
staleness framework; the owner's 2026-08-08 product reframing — the clock
for a daily Morning Brief and evolving market artifact — changed its
leverage, and the owner's planning charge directed this packet. The memo
carries a matching annotation.

---

## 1. PURPOSE / USER VALUE

Make CuttingBoard exist before Dustin asks for it: a truthful morning
artifact produced on a Pacific-time market-day cadence — ~6:00 brief, then
two post-open refreshes whose **semantic anchors are OPEN and OPEN+1** —
with Cloudflare as the punctual CLOCK and the existing GitHub pipeline as
the unchanged EXECUTOR / artifact authority. The 6:30/6:31 trigger times
are **observation intents, not guaranteed publication timestamps**; GitHub
execution may land minutes later, harmlessly (observations are bar-window
defined, §4.2). The artifact evolves PRE-MARKET → OPEN → OPEN+1.

User-visible value: at 6:00 the board is already current, at true Pacific
time, year-round; a promoted GAP UP/DOWN banner appears only when overnight
displacement is material; within minutes of the open the board shows what
the open and the first minute actually did. No notification required — the
artifact being ready IS the product. This is deterministic observation and
compression only — explicitly NOT a generic scheduler/freshness framework.

Why it belongs next (grounded, not abstract):
1. **The current clock is wrong half the year.** `cuttingboard.yml`'s cron
   comment says "06:00 PT / 13:00 UTC" — true only in PDT; in PST the live
   run fires at 5:00 AM PT. The DST defect already exists in production.
2. **The shipped Market Control Card never shows its post-open form.** The
   card composes only on MODE_LIVE runs; the only scheduled live run is
   pre-open, so the published card renders PRE_OPEN/unavailable states all
   day. The OPEN/OPEN+1 refreshes are the first scheduled runs that light
   up STATE/TRANSITION with real open data — this arc completes PRD-289's
   value.
3. **The open/first-minute observations don't exist anywhere.** The hourly
   workflow re-renders the dashboard at 6:30 PT but runs the notify path,
   not the pipeline — daily surfaces are not recomputed.

Not feature sprawl: no new data source, no new decision authority, no new
schema version, no scheduler framework. New things: one dumb ~40-line
Cloudflare Worker, one PT gate in tested Python (the proven
`routine_pt_slot` pattern), one new payload section, one renderer block.

## 2. CURRENT TRUTH (seam / reuse map)

**Workflow entrypoints** (`.github/workflows/cuttingboard.yml`):
- Crons: `50 12 * * 1-5` prefetch, `0 13 * * 1-5` live, `30 23 * * 0`
  sunday. `workflow_dispatch` with one `mode` choice input
  (live/sunday/verify/prefetch); `scripts/resolve_run_mode.py` passes
  dispatch mode through verbatim (cron runs are slot-keyed — PRD-189 fixed
  a 33-day silent noop; that incident sets this arc's fail-loud bar).
- Concurrency group `cuttingboard-pipeline`, cancel-in-progress: false —
  triggers queue, never overlap. Every run: pip install + ruff + full
  pytest first (~minutes); job timeout 20 min; pipeline step timeout 8 min.
- Publish: live/sunday set PUBLISH_READY → commit → `ci_push_artifacts.sh`
  to the unprotected `publish` branch only (PRD-194), ref-guarded to main.
  `mode=verify` runs with **zero product side effects** (stage0-03
  scheduler recon Q17) — the ideal end-to-end trigger-path test vehicle.

**Runtime seam:** entry `python -m cuttingboard --mode {…} --notify-mode
premarket` (`runtime/__init__.py:198`). `run_at_utc` =
`datetime.now(timezone.utc)` at pipeline start (`runtime/__init__.py:936`)
— a later run truthfully gets a later run_at_utc; no injection point
exists to fake it.

**Artifact seam:** immutable per-run `logs/run_<ts>.json` accumulate;
`safe_write_latest` (monotonic run_at_utc guard, `runtime/__init__.py:1903`)
gives "latest wins" for `latest_run.json`/`latest_contract.json` for free.
Payload sections are additive; `assert_valid_payload` checks only required
keys; renderer blocks gate solely on section presence (PRD-288/289
precedent). Dashboard UPDATED prefers the pipeline run's timestamp
(`dashboard_renderer.py:2447`) — a refresh must be a real pipeline run to
move the displayed time (it is, in this design).

**Time/freshness today:** GitHub cron + PRD-250's client-side staleness
banner (board age vs viewer clock, 90-min threshold) + per-source
FRESH/STALE lineage.

**Existing Pacific-time machinery (the pattern to copy):**
`hourly_alert.yml` runs a dumb over-provisioned UTC cron ladder covering
both DST offsets plus 5-min backups; the authoritative gate is
`routine_pt_slot(now_utc, max_lag_minutes=25)` in tested Python
(`notifications/hourly_slot.py`, ZoneInfo America/Vancouver, DST-correct);
cross-runner dedup via `logs/last_hourly_slot.json`; suppressed fires
write an audit row and skip publish. **The "smallest safe mechanism" is
already proven in this repo.**

**Existing gap / prior-close logic (reuse, never reinvent):**
- `intraday_state_engine.py:182` `classify_gap(open_price, prev_close,
  threshold=_GAP_THRESHOLD)` → `UP`/`DOWN`/`FLAT`; `_GAP_THRESHOLD =
  0.0025` (0.25%) — the repo's only material-gap definition, live in
  permission logic. **Post-open, the engine is the authoritative gap
  producer**; the brief projects it, never recomputes. (`gap_pct`
  magnitude is computed but not retained on the carrier — surfacing
  magnitude needs one additive field or same-inputs recompute.)
- `ingestion.py:361-370`: `fast_info.previous_close` validated fail-loud
  (PRD-262) and `pct_change = (price − prev_close)/prev_close` — the
  pre-open displacement quantity **already exists** in the quote path.
- Duplication warning: `reports/levels.py` computes a second independent
  `prior_close`; `reports/premarket.py` carries `gap_direction` as prose
  and `overnight_high/low` as None placeholders. This arc must not create
  a third mechanism (§4.1).
- Vocabulary style: state values UPPER_SNAKE, reason tokens lower_snake.

**Cloudflare prior art:** a Wrangler/`external_trigger` subsystem existed
early on and was retired as dead code, never used in production; its stale
permission grants were pruned under PRD-258. No live Cloudflare config
exists. This arc reintroduces the concept deliberately, with a product
purpose the dead subsystem never had.

**Data availability (repo side):** intraday fetch is regular-session-only
(`prepost=False`, `between_time("09:30",…)` — `ingestion.py:222,237`);
`watch.py:428` documents the pre-open live run seeing the prior session's
frame (ORB handles it as PRE_OPEN/abstain). The 6:00 brief therefore comes
from the quote path, not intraday bars. First-minute bar latency after
13:30 UTC is **not documented anywhere in the repo** — external evidence
required (CF-E2).

## 3. UNRESOLVED LOOP

What keeps this lane open right now:
- **CF-E1 (evidence):** the Cloudflare → GitHub dispatch path has never been
  exercised — auth, ref targeting, queue latency unknown in practice.
- **CF-E2 (evidence):** premarket quote semantics at ~6:00 PT (does
  `fast_info.last_price` reflect premarket trades or echo the prior
  close?) and first-bar availability latency after the open — the repo
  cannot answer either; the brief's premarket half (CF-D1b, CF-D2) is gated on
  this.
- **Owner rulings CF-D1a–CF-D6** (§5) — banner threshold confirmation, premarket
  content, refresh shape, cron fallback, infrastructure ownership,
  notification posture.
- **One design option deliberately unlocked:** refresh-run mechanics (new
  runtime mode vs `live` reuse + suppression intent) — a MATERIAL-packet
  decision with the trade stated (§4.2).

## 4. SMALLEST NEXT SLICE

Proves: *CuttingBoard automatically produces a truthful morning artifact
on the intended market-day cadence.*

**~6:00 PT (PRE-MARKET).** Cloudflare fires → `workflow_dispatch`
(ref=main, `mode=live`) → the exact run that exists today, plus the new
`morning_brief` payload section computed from already-fetched quote data.
Notification behavior unchanged. The existing 13:00 UTC GH cron stays as a
fallback heartbeat; a duplicate same-morning live run is safe (monotonic
latest-guard, no-change publish skip, notification state-key dedup).

**6:30 PT trigger (OPEN).** Cloudflare fires → dispatch carrying
scheduled-refresh intent → full live-class pipeline run, PT-gated in
Python, notifications suppressed, publish on. Execution may land
~6:32–6:38; harmless — the OPEN observation is **defined on the 09:30 ET
minute-bar window** (PRD-271 session-scoped-window pattern), so latency
changes when the artifact arrives, never what it says. The card computes
post-open LOCATION/STATE on the same run.

**6:31 PT trigger (OPEN+1).** Same refresh-intent dispatch one minute
later; adds the first-minute observation (09:30 open → 09:31 bar),
bar-window-defined. Supersedes the OPEN artifact via latest-wins; both
immutable run files persist.

**Refresh-run mechanics — DESIGN OPTION, not locked.** New runtime mode
(e.g. `refresh`) vs reuse of `mode=live` plus an explicit
notification-suppression / scheduled-refresh intent flag: reuse means
fewer new semantics; a new mode means cleaner intent legibility in logs
and audit rows. The MATERIAL packet decides with that trade stated.

### 4.1 Morning Brief contract (proposed minimal shape)

One new additive payload section (working name `morning_brief`), cells in
the established value-XOR-typed-unavailable style (PRD-289 pattern):
- `previous_close` — one authoritative source, the same prev-close the
  engine receives (unification with `reports/levels.py`'s copy is flagged,
  not silently done).
- `premarket` observation (6:00-class runs): quote reference price, the
  existing PRD-262-validated `displacement_pct`, classification; typed
  lower_snake unavailable reasons. Content gated on CF-D1b/CF-D2 + CF-E2.
- `open` observation (post-open runs): projection of the engine's
  authoritative `gap_type` + magnitude from the same inputs. Never a
  second classifier.
- `first_minute` observation: 09:30→09:31 bar displacement; present only
  when the 09:31 bar exists; typed unavailable otherwise.
- **Observation-slot lineage (required):** each run's brief section — and
  therefore each immutable `logs/run_<ts>.json` — records the slot served
  (PREMARKET / OPEN / OPEN_PLUS_1; final tokens per vocab conventions) as
  one field on the existing per-run artifact. Explicitly NOT a new
  historical subsystem.

**Compute explicitly, display selectively:** every cell always carries one
closed internal state (existing `UP`/`DOWN`/`FLAT` taxonomy; token names
verified at packet stage, `NO_MATERIAL_GAP`-style names NOT assumed). The
renderer suppresses the FLAT/ordinary case entirely and promotes only
`GAP UP +x.xx%` / `GAP DOWN −x.xx%`. No SMALL/MODERATE/LARGE/EXTREME
tiers; the raw percentage is the magnitude, rendered from the payload
value with fixed precision — the renderer computes nothing. One exact
string detail rides CF-D1a rather than being silently assumed: the ruling's
literal wording shows `GAP UP +x.xx%` / `GAP DOWN -x.xx%`; the packet
assumes a signed minus for the down case — confirm the exact format at
packet stage.

**Threshold:** a canonical material-gap definition EXISTS for the open gap
(`_GAP_THRESHOLD` 0.25%): CF-D1a asks Dustin to confirm reusing it as the
banner-promote bar — no new constant, no optimization. NO canonical
definition exists for pre-market displacement: **OWNER PRODUCT RULING
REQUIRED (CF-D1b), held pending CF-E2.** Nothing is invented in either case.

**Deferred:** overnight high/low range; gap-fill/retrace language; any
second symbol; hourly continuation; promotion of `premarket.py` prose
fields beyond what this section needs.

### 4.2 Clock / time design

**Dumb clock, smart executor.** All semantic time logic lives in tested
Python; the Worker only fires. Semantic anchors are the bar windows
(PREMARKET quote snapshot, OPEN = 09:30 ET bar, OPEN+1 = 09:31 ET bar).
- Cloudflare crons (UTC-only): six entries, Mon–Fri — 13:00/13:30/13:31
  (PDT case) and 14:00/14:30/14:31 (PST case).
- Worker: optional 5-line local-time check to skip the wrong-DST-variant
  tick — best-effort optimization, explicitly NOT the authority.
- Executor gate (authoritative): PT-slot check in Python mirroring
  `routine_pt_slot` for {6:00, 6:30, 6:31}; out-of-window dispatch →
  suppressed audit row + publish skipped (the proven hourly flow).
  Weekends excluded by cron day-field AND gate.
- Holidays: no calendar exists; system is holiday-unaware by design with
  safe degradation (`time_utils.py:45`); the pipeline already runs on
  weekday holidays and produces a truthful degraded artifact. Slice 1
  inherits this; a calendar is deliberately out of scope (G8).
- Determinism: `run_at_utc` untouched; brief observations bar-window
  defined; the PRD-289 no-wall-clock discipline (FAIL CONDITION 11)
  extends to the brief composer (testable with the M15 fixture
  technique).
- DST transition days: handled identically to the hourly path; the two
  transition Sundays are non-market days.

### 4.3 Security / trigger contract

- Auth: GitHub fine-grained PAT scoped to `dwats250/cuttingboard`,
  Actions read/write only, stored as an encrypted Cloudflare Worker
  secret, sent via Authorization header. Never in query strings, the
  repo, or artifacts (the POLYGON_API_KEY leak — 109 query-string
  exposures — is the named precedent).
- Call: `POST .../actions/workflows/cuttingboard.yml/dispatches` with
  `ref: main` (publish is ref-guarded to main) and the mode input per the
  §4 design option.
- Least privilege: the PAT cannot push, merge, or read secrets; the
  workflow's own GITHUB_TOKEN publishes exactly as today. Rotation is one
  CF-dashboard secret replacement.
- Replay/duplicates: safe by existing construction (concurrency queue,
  monotonic latest-guard, no-change publish skip, notification dedup, PT
  gate). Idempotency is the executor's property, not the clock's.
- Failure visibility: missed fire = artifact age on the board (PRD-250
  banner); Worker logs in CF dashboard; executor failures fail loud and
  skip publish (PRD-287 posture). Deliberately NO new alerting channel.
- PAT-leak blast radius: trigger-only (cost/noise, no data or merge
  access) — bounded and rotatable.

**What does NOT change:** the three read-only producers
(`spy_observation.py`, `intraday_state_engine.py`, `red_folder.py`);
`PAYLOAD_SCHEMA_VERSION` and required payload keys; the decision contract
and `system_state`; ingestion (`prepost` stays False); the hourly
workflow; notification reach; the publish-branch-only rule; existing GH
crons.

## 5. OWNER DECISIONS REQUIRED

1. **CF-D1a — Open-gap banner threshold:** confirm reuse of the engine's
   existing 0.25% `_GAP_THRESHOLD` as the promote bar for v1.
2. **CF-D1b — Premarket-displacement banner: HOLD** pending CF-E2
   provider-semantics evidence; ruled only after CF-E2 lands.
3. **CF-D2 — 6:00 content:** include the quote-based pre-market displacement
   observation in v1 (recommended), or ship open/first-minute only?
4. **CF-D3 — Refresh shape:** two dispatches (OPEN + OPEN+1, per the charge;
   recommended) vs one ~6:32 dispatch capturing both bar windows?
   Observations are bar-window-defined either way.
5. **CF-D4 — GH-cron fallback:** keep existing 12:50/13:00 UTC crons through
   slice 1 as heartbeat (recommended); retirement is a later
   observed-replacement decision.
6. **CF-D5 — Infrastructure ownership:** Dustin holds the Cloudflare account,
   deploys the Worker, issues/rotates the PAT (agents never touch the
   secret). Confirm.
7. **CF-D6 — Notification posture:** refresh runs fully silent (recommended);
   the 6:00 run keeps today's premarket notification behavior.
8. **CF-E1/CF-E2 commissioning:** authorize the two bounded evidence captures.

## 6. DEPENDENCIES

- CF-E1 needs CF-D5 first (owner PAT + Worker deploy).
- CF-E2 needs one diagnostic capture at ~6:00 PT and one at ~6:32 PT on a
  market day (read-only in product terms).
- The MATERIAL packet draft needs CF-E1 + CF-E2 + CF-D1a–CF-D6.
- CF-D1b depends on CF-E2 by construction.
- Gate A needs the reviewed PRD after the packet clears GOV-2's sequence.
- No dependency on the registry lane, GEX, or Market Map work.

## 7. PARALLEL-SAFE WORK

Safely parallel: Context Registry / NEWS-0 lane (no shared files);
bounded GEX owner decision (no files); real-use Market Control Card
observation (no files — this arc AMPLIFIES it: first scheduled post-open
card renders). Must serialize: anything else touching
`delivery/payload.py` / `delivery/dashboard_renderer.py` while this arc is
in flight; Market Map narrowing stays strictly after this arc's
observation window.

## 8. SCOPE WALLS (this arc does NOT include)

GEX in any form; news; registry; heatmap; Market Map retirement/coupling;
macro; any new alerting/notification channel; a generalized scheduler
UI/framework or any second scheduled consumer riding the Worker;
AI-generated commentary; threshold optimization or backtest-derived
tuning; predictive labels or gap-fill "expectations";
SMALL/MODERATE/LARGE tiers; premarket bar ingestion (`prepost` change);
holiday calendar; early-close awareness; GH-cron retirement; changes to
the three read-only producers, the hourly workflow,
PAYLOAD_SCHEMA_VERSION, or the decision contract; any new
historical/query subsystem (slot lineage rides the existing per-run
artifact only).

## 9. FILE / SURFACE ESTIMATE

Honest ranges (PRD-288: 195→308→amended 325; PRD-289: 300→499→amended 525 — both misses were
validation/vocabulary surfaces, counted here as first-class):

| Surface | Files | Est. LOC |
|---|---|---|
| Brief composer (carrier, closed vocabs, XOR-cell validation, 3 resolvers, slot-lineage field, fail-loud guards) | 1 new module | 150–250 |
| Runtime wiring (refresh-intent handling per §4 design option, PT gate, notify suppression, section handoff) | `runtime/__init__.py`, `runtime/_constants.py` (+`notifications/hourly_slot.py` reuse) | 60–120 |
| Payload projection | `delivery/payload.py` | 20–40 |
| Renderer block (presence-gated, projection-only) | `delivery/dashboard_renderer.py` | 40–70 |
| **Production total (governing metric, cuttingboard/)** | ~5–6 files | **270–480** |
| Workflow | `cuttingboard.yml`, `resolve_run_mode.py` | 40–80 |
| Clock | `cloudflare/wrangler.toml`, `cloudflare/worker.js` (in-repo for docs-match-code; owner-deployed) | 50–90 |
| Tests | new `test_morning_brief*.py` + resolver/slot/renderer additions | 400–700 |
| Docs | artifact_flow_map registration, PROJECT_STATE, PRD doc, DECISIONS | n/a |

Composer uncertainty is genuinely high (validation dominates); the
MATERIAL packet should set the Gate-A ceiling at the top of the range plus
margin, not the middle.

## 10. TEST / FALSIFICATION PLAN

Every guard ships a red test (PRD-198 #4); mutation targets marked (M).
- PT gate: in-window PDT/PST fixtures resolve correctly; out-of-window
  (5:00 PST-variant tick, weekend, random hour) → suppressed audit row +
  no publish (M: remove gate → red). DST-week fixtures both sides.
- Determinism: fixtures where wall-clock ≠ run_at_utc ≠ bar timestamps —
  observations keyed only on run_at_utc + bar windows (M: `datetime.now()`
  in composer → red). Same technique as the card's M15.
- 6:00 semantics: pre-open fixture → premarket cell populated from quote,
  open/first-minute typed unavailable; invalid quote → fail-loud
  unavailable reason, never a fabricated 0.0 (M: substitute default →
  red).
- OPEN semantics: 09:30 bar present, 09:31 absent → open populated,
  first-minute typed unavailable — regardless of simulated execution
  delay (observation-intent vs publication time pinned by test).
- OPEN+1 semantics: both bars present → first-minute populated; magnitude
  arithmetic pinned exactly.
- Slot lineage: each fixture run's immutable summary records the correct
  slot; runs distinguishable on artifact contents alone (M: drop field →
  red).
- Banner: FLAT → banner absent from rendered HTML (M: render-on-FLAT →
  red); UP → exact `GAP UP +x.xx%`; DOWN → exact `GAP DOWN −x.xx%`;
  magnitude formatted from payload only (M: renderer recomputes → red).
- Threshold correspondence: brief classification agrees with engine
  `gap_type` on identical inputs (M: classifier drift → red).
- Idempotency: two refresh runs same morning → monotonic latest-wins,
  both immutable run files, no duplicate notification, no-change publish
  skip.
- No side effects: refresh runs send zero notifications (M: un-suppress →
  red); no GEX/news/heatmap/Market-Map imports in the composer (import
  guard); decision contract byte-identical brief-present vs brief-absent.
- Failure paths: failed executor run → non-zero exit, publish skipped;
  absent trigger → next slot proceeds independently (no cross-slot state).

## 11. MATERIALITY / GOVERNANCE PATH

**MATERIAL** (GOV-2 §1 by analogy to PRD-288/289): new external trigger
authority crossing a trust boundary (Cloudflare → GitHub, owner-held
secret); new payload section + renderer surface (HIGH-RISK CONSUMER floor
via `dashboard_renderer.py`); workflow/publish-adjacent edits (PRD-194
policy area); refresh-run semantics with notification implications.
Expected shape: CF-E1/CF-E2 evidence → MATERIAL packet → Codex review +
exact-head confirmation → design-direction ruling → Stage-0 PRD →
independent review → Gate A. Lane: HIGH-RISK / CONSUMER (+INFRA). NOT a
provider-evidence packet: no new data provider, no licensing; the trigger
is testable end-to-end with the zero-side-effect `mode=verify` dispatch.
Workflow-file changes ride the normal PR flow as a draft with the
governance-adjacent surface named.

## 12. STOP CONDITIONS

**Boundary reset (stop, re-run GOV-2 classification / amend upstream):**
any seventh-production-file class of growth; any `PAYLOAD_SCHEMA_VERSION`
bump or required-key change; any touch of the three read-only producers;
any notification-reach expansion; any second scheduled consumer proposed
for the Worker; premarket bar ingestion (`prepost`) creeping into the
slice; LOC growth past the Gate-A ceiling (GOV-2 §5 stop-and-renew).

**Lane stops entirely if:** CF-E1 shows the Cloudflare → GitHub dispatch path
cannot be made to work under least-privilege auth (no fallback mechanism
is authorized without fresh recon + owner ruling); Dustin declines CF-D5
(infrastructure ownership) — no agent-held secret alternative exists by
design; CF-E2 shows both premarket quote semantics unusable AND first-bar
latency incompatible with OPEN/OPEN+1 semantics (the premarket half alone
failing only narrows the slice via CF-D1b/CF-D2, it does not stop the lane).

## 13. IMPLEMENTATION READINESS

**PLANNING-READY.** Not MATERIAL-PACKET-READY: CF-E1/CF-E2 evidence outstanding
and CF-D1a–CF-D6 unruled. Not PRD-READY, not IMPLEMENTATION-READY. Major
semantic choices remain open by design (CF-D1b–CF-D3, the refresh-mode design
option, CF-E2's premarket-price semantics); pretending otherwise would repeat
the estimate-miss pattern this repo has paid for twice.

Sequential (hard order): CF-D5 → CF-E1; CF-E2 → CF-D1b; CF-E1+CF-E2+D-rulings → MATERIAL
packet → Codex cycle → ruling → Stage-0 PRD → review → Gate A →
implementation. Intentionally deferred: GH-cron retirement
(observed-replacement-gated); holiday calendar; premarket bars; any
generalization of the clock.

## 14. RECOMMENDED NEXT COMMISSION

**Commission CF-E1 + CF-E2 now** (implementation-class agent; CF-E1 needs Dustin's
PAT + Worker deploy per CF-D5), and in parallel answer CF-D1a–CF-D6. With evidence
and rulings in hand, commission the MATERIAL packet draft (design-class
model — vocabulary/boundary/failure-semantics work), compiling every
semantic choice out of the slice so implementation can sprint afterward.

**Held:** PRD number, Gate A, all implementation, GH-cron retirement,
Cloudflare deployment, evidence capture (until commissioned), the
Cloudflare secret (owner-only).
