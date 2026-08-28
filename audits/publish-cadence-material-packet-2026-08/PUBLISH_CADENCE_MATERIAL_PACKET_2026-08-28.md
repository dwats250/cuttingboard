# Reliable market cadence — MATERIAL design packet (Lane B)

```
STATUS: PROVISIONAL MATERIAL PACKET — 2026-08-28 — DESIGN ONLY
AUTHORIZES NO IMPLEMENTATION, NO PRD NUMBER, NO WORKER DEPLOY, NO WORKFLOW
EDIT, NO GATE A, NO MERGE.
GOV-2 PACKET-REVIEW CYCLE: EVENT 1 COMPLETE (DESIGN INCOMPLETE at 000b13a —
  CODEX_EVENT_1_REVIEW_2026-08-28.md, findings F1-F8; the ONE consolidated
  correction is APPLIED in this revision — see ## CORRECTION CYCLE).
AWAITING: Event-2 exact-corrected-head confirmation (GOV-2 sec7).
Ceilings below are ESTIMATES (GOV-2 sec5), not constraints.
```

> Upstream MATERIAL design packet for the owner-charged Lane B (owner charge
> 2026-08-27, "LANE B — CLOUDFLARE / PUBLISH CADENCE"): a reliable weekday
> cadence — PRE ~06:00 PT, OPEN ~06:30 PT, POST-OPEN ~06:45 PT, then hourly
> through the trading window — without streaming data, without peer
> schedulers racing, and without weakening any publication guard.
>
> Sequence position: provisional packet -> Event-1 Codex review -> ONE
> consolidated correction -> Event-2 exact-corrected-head confirmation ->
> Dustin design-direction ruling -> Stage-0 PRD(s) -> reviews -> Gate A ->
> implementation -> Dustin merge. Separately: the Worker DEPLOY itself is
> already authorized and owner-held (CF-D5 / CF-E1) and is a Dustin console
> act, not a repo change.

---

## sec0 — Intake classification (GOV-2 sec1)

**MATERIAL — fires on the merits** (classified 2026-08-28 at main `4fe7d67`):
- **Selects coordination seams shared across pipeline layers (fires):** the
  design touches the Cloudflare Worker dispatch transport, both scheduled
  workflows' cron/dispatch surfaces, the PT slot-dedup machinery
  (`cuttingboard/notifications/hourly_slot.py`), and the first-success OPEN
  coordination — seams spanning scheduling, runtime, notification, and
  publication.
- **Crosses two or more enumerated layers (fires):** runtime (slot gate),
  notification (alert dedup semantics), delivery/publication (publish
  cadence), plus CI workflow surfaces.
- **Establishes FILES/LOC ceilings (fires):** sec8/sec9.
- **Consumer/coordination enumeration (fires):** sec5 claims to enumerate
  every scheduler, dispatcher, and slot consumer after the change.
Lane estimate for the downstream PRD: STANDARD unless R11 fires on a
touched file (no HIGH-RISK FILE is expected in the cone; the PRD decides).
MICRO is unavailable (MATERIAL).

## sec1 — Verified current state (all decisive claims re-verified)

Full recon: fresh-context sweep 2026-08-28, re-verified where decisive.
1. **Clocks.** GitHub crons only: `cuttingboard.yml` PRE `50 12 * * 1-5`
   (cache-warm, publishes nothing), OPEN fallback `5 13 * * 1-5` (the daily
   board publish), Sunday `30 23 * * 0`; `hourly_alert.yml` 13 crons/weekday
   PT-gated down to 9 effective slots (`ALLOWED_PT_SLOTS`,
   `cuttingboard/notifications/hourly_slot.py:26-36`; gate `:52-76`,
   `max_lag_minutes=25`).
2. **The Worker exists in-repo and is repository-recorded as undeployed
   (no CF-E1 completion evidence; live Cloudflare account state was not and
   cannot be verified from a read-only checkout — Event-1 F8)**
   (`workers/cuttingboard-clock/README.md`; only `wrangler.example.toml`;
   no CF-E1 completion entry — `docs/DECISIONS.md:373,381`). It is
   transport-only (no KV/DO state) and dispatches `cuttingboard.yml` with
   `{mode, slot, source}` (`src/index.js:26-29,48-61`). Deploy is
   owner-held (CF-D5).
3. **Binding rulings.** DECISIONS 2026-08-11: OPEN heartbeat = delayed
   GitHub fallback; "a fixed UTC cron is NOT to be described as a
   year-round fixed PT wall-clock time"; dedicated `cb-open-coordination`
   concurrency group. DECISIONS 2026-08-09 CF-D3: a post-open second
   dispatch ("OPEN and OPEN+1") is ALREADY AUTHORIZED and never built.
   PRD-299 built the OPEN first-success machinery
   (`scripts/check_open_slot_satisfied.py`, fail-toward-availability).
4. **Observed reality (origin/publish audit rows, 2026-08-19..27):** GitHub
   cron delivery ran 45-55 min late; the daily board actually published
   ~06:52-07:00 PT; the 06:00 PT hourly slot never landed in that window
   (late fires hit `outside_routine_window`); several weekdays show missing
   hourly slots and one weekday has zero hourly rows. The dominant failure
   mode is SILENT-GREEN suppression (exit 0, publish tail skipped,
   suppression rows never reach the published audit), the exact 2026-07-07
   incident class (`docs/DECISIONS.md:2588-2596`).
5. **No 06:45 PT slot exists**; a 06:45 fire resolves to slot 06:30 within
   the 25-min lag rule and is `suppressed_same_slot`
   (`hourly_slot.py:26-36,66-76`).
6. **`hourly_alert.yml` `workflow_dispatch` takes NO inputs and always
   forces** (`--force-slot`, bypassing both the PT window and dedup —
   `hourly_alert.yml:103-107`, `alert_runner.py:51,70-71`). A Worker
   dispatch of the hourly today would force-send unconditionally — unusable
   as a routine clock without a new input.
7. **Request cost today** (yfinance sole quote/bars provider; Cboe one GET
   per hourly for GEX): hourly run ≈ 25 quotes + ~23 six-month OHLCV
   downloads + 1 Cboe ≈ 49 requests (the hourly job has NO `actions/cache`
   step, so the OHLCV cache is cold every run — unlike the pipeline's
   cached job); daily live ≈ 47+ plus option chains; prefetch ≈ 46. Full
   PDT day if every slot lands: ~534 yfinance + 9 Cboe.
8. **Notification/dedup hazards a cadence change can trip:** slots <25 min
   apart collapse to the earlier slot; slot state persists only post-send
   and survives only via the publish-branch restore; the daily path's
   `should_send` content-dedup suppresses an adjacent second daily run;
   Pages deploys via `workflow_run` on all three writers.

## sec2 — Design principle

Cloudflare becomes the punctual clock it was already built and authorized
to be; GitHub crons remain the delayed fallback heartbeats; every existing
guard (first-success, PT gate, slot dedup, exact-SHA proof, revision drift,
readiness, publish ownership) is preserved unchanged. No peer scheduler is
created: the Worker front-runs the same workflows the GitHub crons fire,
the GitHub crons that would coincide with a Worker slot are retimed into
DELAYED fallbacks (sec3), and the existing suppression machinery no-ops
the second arrival on the HEALTHY path (first-success for the pipeline,
same-slot dedup for the hourly). On failure paths the existing
at-least-once semantics apply unchanged — stated precisely in sec3's
duplicate policy, never claimed away. Streaming is out of scope; snapshots
stay the data model.

## sec3 — Target cadence mapping (corrected per Event-1 F1/F2: one owner
per instant, no same-instant peers, slot identity carried by the dispatch)

| Owner slot | Owner | Mechanism | Change required |
|---|---|---|---|
| PRE ~06:00 PT (pre-market board + premarket alert) | DAILY PIPELINE, exclusively | CF dispatches OPEN/live at 06:00 PT; existing 13:05Z GitHub fallback + first-success unchanged | Worker cron/gate (sec4). **`(6,0)` is REMOVED from `ALLOWED_PT_SLOTS`** — the hourly's 06:00 board is superseded by the punctual daily board, which eliminates the same-instant daily-vs-hourly double-notification path Event-1 F1 identified (the two paths have no cross-path dedup). GitHub's 13:00Z/13:05Z hourly crons then resolve to no slot before 06:30 and no-op |
| OPEN ~06:30 PT | HOURLY, CF-primary | CF routine dispatch carrying EXPLICIT slot identity `06:30`; **GitHub `30 13` and `30 14` heartbeats RETIMED to `40 13` / `40 14`** — delayed fallbacks (06:40 wall-clock in their respective seasons), the exact pattern the 2026-08-11 ruling set for OPEN/live. No same-instant CF-vs-GitHub peer race remains | `hourly_alert.yml` dispatch inputs + cron retime |
| POST-OPEN ~06:45 PT | HOURLY, CF-only | CF routine dispatch with explicit slot `06:45`; `(6,45)` added to `ALLOWED_PT_SLOTS`; implements the authorized CF-D3 "OPEN+1". No GitHub heartbeat in slice 1 (ruling Q4) | slot set + dispatch |
| HOURLY 07:00..13:00 PT | HOURLY, GitHub crons as today | Unchanged; CF extension is a follow-up (ruling Q3) | none |

**Slot identity under delay (Event-1 F2).** Start-time inference
(`routine_pt_slot`) lets a delayed 06:30 start at 06:45+ be relabelled
(6,45), suppressing the real 06:45 and losing the 06:30 slot. Correction:
a ROUTINE dispatch carries its intended slot explicitly
(`hourly_alert.yml` inputs `kind: routine|forced`, `slot: "HH:MM"`;
runner flag `--routine-slot HH:MM`). The runner then resolves EXACTLY that
slot: it verifies the slot is allowed and that `now - slot` is within the
existing `max_lag_minutes` (else audits `outside_routine_window` and
no-ops), and applies the existing same-slot dedup. CF dispatches therefore
can never shift identity. Cron/heartbeat arrivals keep today's inference
path unchanged; a heartbeat that starts so late it crosses into the next
slot's identity is the pre-existing inference semantic, now confined to
the fallback path that only matters when CF failed — documented, with the
06:30-loss case named in ruling Q9 rather than claimed away. `max_lag`
is not widened (PRD-250 decision) or narrowed (silent-green class).

**Duplicate policy (Event-1 F3).** Hourly delivery is transport-first;
slot persistence is post-send, swallowed on error, and cross-run visible
only via the publish restore. The existing guarantee is therefore
AT-LEAST-ONCE per slot with a bounded duplicate window when a send
succeeds and persistence/publish then fails — serialization prevents
simultaneous sends, not send/persist atomicity. This packet PRESERVES that
existing semantic (making send+persist atomic is its own MATERIAL slice,
out of scope) and states it honestly: the validation plan (sec7) gains the
send-success/persist-failure and send-success/publish-failure regression
cases asserting today's bounded behavior, and the accepted residual is put
to the ruling (Q10). No text in this packet claims "exactly one send" —
first-success (pipeline) and slot dedup (hourly) suppress the second
ARRIVAL in the healthy path; failure paths can duplicate, today as after
this design.

## sec4 — DST without a peer scheduler (Worker gate contract, corrected per
Event-1 F4)

Cloudflare cron triggers are UTC-only; PT fidelity comes from dual-offset
crons gated inside the Worker. The gate CONTRACT:
- **Authority timestamp: `event.scheduledTime`** — the scheduled cron
  minute, fixed by the platform regardless of handler execution delay.
  Handler-time is never consulted, so a delayed handler can neither miss
  its own window nor drift into another (the F4 zero/two-dispatch hazard
  under delayed execution is structurally closed).
- **Mapping table, not window arithmetic:** a static table maps each
  (cron expression, PT UTC-offset in effect at `scheduledTime`) pair to
  exactly one intended PT slot or to NO-OP. Example: `0 13 * * 1-5` maps
  to slot 06:00 when the offset is -07:00 (PDT) and to NO-OP when -08:00;
  its twin `0 14 * * 1-5` maps to 06:00 under PST and NO-OP under PDT.
  A shared trigger that is one slot's winter twin and another's summer
  primary (the 14:00Z case) is disambiguated by the same lookup — the
  offset picks exactly one row. Equality on the scheduled minute; no
  inclusivity bounds exist because no window exists.
- At any `scheduledTime` at most one row matches, so two dispatches for
  one slot cannot occur even across DST transitions (which fall on
  Sundays, outside the weekday crons entirely); and even a Worker bug
  double-dispatching is absorbed by first-success / same-slot dedup.
- The Worker stays transport-only: the table and an offset lookup
  (`Intl.DateTimeFormat`, `America/Los_Angeles`) are pure computation, no
  state.
- **Ruling extension required (F4):** the 2026-08-11 ruling anchors
  trigger/window mechanics in UTC with PT authoritative for trading-date
  identity. This design adds a PT-eligibility LOOKUP on top of UTC
  triggers. The packet does NOT claim the ruling already covers this; it
  requests an explicit extension ruling (Q8). GitHub fallback crons stay
  fixed-UTC and seasonally drifting, exactly as that ruling states.

## sec5 — Coordination and dispatch surfaces (the full participant set)

1. Worker (`workers/cuttingboard-clock/`): cron set extended per sec3/sec4;
   gains the hourly dispatch target with `{kind: "routine"}`.
2. `cuttingboard.yml`: NO predicate/guard change; keeps `5 13 * * 1-5`
   fallback, `cb-open-coordination`, first-success proof, all publish
   guards. (Optionally, ruling Q2: a second fallback cron for PST-season
   punctuality — default recommendation is NO change.)
3. `hourly_alert.yml`: `workflow_dispatch` gains input
   `kind: routine|forced` (default `forced`, preserving today's manual
   behavior byte-for-byte); `routine` runs WITHOUT `--force-slot`, so a CF
   routine dispatch obeys the PT window and slot dedup exactly like a cron
   arrival. GitHub hourly crons unchanged as heartbeats.
4. `cuttingboard/notifications/hourly_slot.py`: `(6,45)` added to
   `ALLOWED_PT_SLOTS`; `max_lag_minutes` untouched.
5. `cuttingboard/alert_runner.py`: no semantic change (the force flag is
   already a CLI argument; the workflow chooses it).
6. Consumers of slot semantics enumerated for regression (widened per
   Event-1 F6): dedup persistence (`last_hourly_slot.json`
   restore/force-add), audit reasons (`outside_routine_window`,
   `suppressed_same_slot`), the freshness gate (`fresh=false` tail-skip),
   Pages `workflow_run` triggers — ALL THREE writers including
   `.github/workflows/macro_awareness.yml` (dispatch-only today, still a
   Pages trigger), notification ownership (PRD-295/296/300), the DAILY
   content-dedup path (`cuttingboard/notifications/state.py`
   `should_send`), the hourly send + post-send slot persistence
   (`cuttingboard/runtime/__init__.py:688-692,734-777`), cross-workflow
   restore/publish machinery (`tools/ci_restore_publish_state.sh`,
   `tools/ci_push_artifacts.sh` — last-writer overwrite of generated `ui/`
   accepted by design), request producers and cache semantics
   (`cuttingboard/config.py`, `cuttingboard/ingestion.py`,
   `cuttingboard/derived.py`), and the GEX producer/guards
   (`tools/gex_snapshot.py` + its workflow step).
Falsifier (widened): `rg -n "force-slot|ALLOWED_PT_SLOTS|routine_pt_slot|\
CB-SLOT|should_send|last_hourly_slot|ci_push_artifacts|ci_restore_publish|\
gex_snapshot|workflow_run" .github/ workers/ cuttingboard/ tools/ scripts/
tests/` must enumerate a superset of the participants above; any hit
outside them is an omission to disposition before Gate A.

## sec6 — Request volume (corrected per Event-1 F5: LOGICAL provider
operations, first-attempt; not HTTP requests)

Units: one "logical operation" = one fetch call at the ingestion seam.
Each may issue >1 HTTP request (yfinance internals) and retries up to 3x
on failure (`FETCH_RETRIES`); wire counts are NOT claimed — the PRD's
validation records measured logical-call counts with cache-hit and retry
tallies, and labels HTTP counts unavailable unless instrumented.

- Hourly run ceiling today: 23 base quotes + 2 observe-only quotes + up to
  23 cold OHLCV downloads = up to 48 yfinance logical ops, plus 1 Cboe
  invocation.
- Cadence delta: `(6,0)` removed and `(6,45)` added — hourly-class run
  count per day UNCHANGED (9 effective slots), so ≈ +0 yfinance logical
  ops; +0 Cboe (the 06:45 run's GEX refresh replaces the retired 06:00
  run's; still one per hourly-class run, within the "best-effort hourly
  refresh" authorization — flagged for the ruling regardless, per the GEX
  cadence boundary in DECISIONS/PROJECT_STATE).
- Recommended companion fix (cost-negative): add the pipeline's existing
  `actions/cache` pattern for `data/cache` to `hourly_alert.yml` — each
  WARM hourly run avoids up to 23 OHLCV logical ops; across ~9 slots, up
  to ~-200 logical ops/day, conditional on cache health (trading-day-keyed
  freshness makes the first run of the day the cache-filler).
- Worker dispatches: free-tier Cloudflare cron + one GitHub API POST per
  dispatched slot (~3-4/day in slice 1). No new data provider anywhere.

## sec7 — Validation plan the implementation must satisfy (charge-mandated)

- Simulate every slot: unit fixtures over `routine_pt_slot` for the new set
  in PST and PDT, including the 15-min-late collapse cases.
- Prove no duplicate publication: CF dispatch + cron arrival same slot ->
  exactly one send (dedup test), pipeline CF+fallback -> first-success
  no-op test (existing suite extended).
- Prove failed-preferred -> fallback executes; successful-preferred ->
  fallback no-op (existing `tests/test_open_slot_coordination.py` already
  covers the pipeline side; hourly side gets equivalents).
- Prove hourly isolation from OPEN coordination (no shared state touched).
- Worker PT-gate: table-driven tests executing the ACTUAL production JS
  gate under Node (the PRD-250 precedent — its client-side staleness
  verdict is tested by Node-executing the shipped JS, not a Python
  mirror); a mirrored table alone is insufficient (Event-1 F6).
- Send-success/persist-failure and send-success/publish-failure
  regressions asserting today's bounded at-least-once behavior (Event-1
  F3), in `tests/test_hourly_slot_idempotency.py`.
- Explicit-slot dispatch: in-window resolves the named slot; out-of-window
  audits `outside_routine_window`; same-slot dedup unchanged; forced path
  byte-identical to today.
- Request-volume figures recomputed as measured logical-call counts with
  retry/cache-hit tallies (sec6 units).
- The mutation-verified red-test discipline applies to every new guard.

## sec8 — FILES cone (estimate)

`M workers/cuttingboard-clock/src/index.js`,
`M workers/cuttingboard-clock/wrangler.example.toml`,
`M workers/cuttingboard-clock/README.md`,
`A workers/cuttingboard-clock/test/` (Node harness for the production
gate) or the equivalent test entry point,
`M .github/workflows/hourly_alert.yml` (dispatch inputs, cron retimes
30 13->40 13 / 30 14->40 14, cache step),
`M cuttingboard/notifications/hourly_slot.py` (drop (6,0), add (6,45)),
`M cuttingboard/alert_runner.py` (`--routine-slot`),
`M tests/test_hourly_slot_idempotency.py` (F3 failure-path regressions +
slot-set changes; per Event-1 this file is the existing idempotency home),
`A tests/test_worker_clock_gate.py` (Node-executed gate table),
`M tests/test_open_slot_coordination.py`,
`M tests/test_ci_artifact_hygiene.py` (workflow-shape assertions),
`M docs/PROJECT_STATE.md` / DECISIONS entry at closeout.
`cuttingboard.yml` expected UNTOUCHED (any discovered need = STOP and
reclassify before edit).

## sec9 — LOC ceiling (estimate)

<=200 net production LOC (worker gate/table + workflow + slot set +
runner flag), <=650 net test LOC (Node gate harness included).
STOP-AND-RENEW on breach.

## sec10 — Risks

- Worker deploy remains owner-held: until CF-E1/E2 are performed by Dustin,
  the design delivers no punctuality change; the repo changes are inert but
  safe (routine input defaults to today's behavior; (6,45) simply never
  fires without a 06:45 arrival — GitHub's `30 13`/`45 13`? NO new GitHub
  cron is added by default, so 06:45 exists only when CF dispatches it;
  ruling Q4 offers a GitHub 06:45 heartbeat as an alternative).
- Silent-green class: unchanged in structure (deliberately — PRD-250 ruled
  the mitigation), but materially rarer because the punctual clock stops
  feeding the late-fire suppression path.
- A Worker bug double-dispatching is absorbed by existing dedup (sec4);
  a Worker outage degrades to exactly today's behavior.

## sec11 — Ruling questions

**Q1 — Cadence set.** Recommend: 06:00 PT board (CF-dispatched OPEN/live),
06:30 + new 06:45 + existing hourly slots via routine hourly dispatch.
Alternative: also move the 12:50Z cache-warm under CF (not recommended —
zero operator-visible value).
**Q2 — PST-season pipeline punctuality.** Recommend: accept the existing
single 13:05Z fallback (05:05 PST when CF is down); alternative adds a
second winter fallback cron with predicate work — more surface, marginal
value while CF is healthy.
**Q3 — CF as primary for ALL hourly slots.** Recommend: yes for
06:30/06:45 only in slice 1 (smallest change proving the pattern); extend
to 07:00-13:00 in a follow-up once observed. Alternative: all slots at
once.
**Q4 — 06:45 GitHub heartbeat.** Recommend: none in slice 1 (06:45 is
CF-only; a CF outage costs only the post-open snapshot). Alternative: add a
`45 13`+`45 14` GitHub cron pair as heartbeat.
**Q5 — Hourly `actions/cache` companion fix.** Recommend: include in the
same PRD (cost negative, isolated). The "separate slice" alternative is
NOT a micro-slice (Event-1 F7: it touches a scheduled workflow and a
shared cross-run cache seam, and this packet's MATERIAL classification
makes MICRO unavailable); if separated it takes its own lane per matrix.
**Q6 — Worker deploy.** The design assumes Dustin performs CF-E1/E2 per
the standing authorization once the implementation lands; confirm or
re-sequence.
**Q7 — 06:00 ownership (added per Event-1).** Recommend: the daily
pipeline exclusively owns 06:00 (premarket alert + board) and hourly
`(6,0)` is retired. Alternative: keep `(6,0)` and accept the dual
notification paths at the same instant (not recommended — no cross-path
dedup exists).
**Q8 — Worker time-basis extension ruling (added per Event-1).** The PT
slot-lookup on UTC triggers (sec4) extends the 2026-08-11 time-basis
ruling; issue or decline the extension. Declining reverts the Worker to
single-offset UTC crons with accepted seasonal drift (the owner charge
disprefers this).
**Q9 — Late-heartbeat identity shift (added per Event-1).** On the
fallback path only (CF failed), a GitHub 06:40 heartbeat that starts
>5 min late can be relabelled (6,45), costing the 06:30 slot its send.
Recommend: accept (rare, fallback-only, self-limiting). Alternative:
carry explicit slot identity on heartbeat crons too via per-cron dispatch
wrappers (more surface).
**Q10 — Duplicate-on-failure residual (added per Event-1).** Hourly
send/persist is not atomic; a send-success + persist/publish-failure can
re-send next arrival — today's behavior, preserved. Recommend: accept and
pin with regressions. Alternative: an atomic send+persist redesign — its
own MATERIAL slice, not this one.
**Q11 — Ceiling units (added per Event-1).** Recommend: request ceilings
are MEASURED LOGICAL provider operations (retry/cache tallies recorded;
HTTP counts labeled unavailable unless instrumented).

## sec12 — Evidence index

- Recon sweep 2026-08-28 (fresh-context subagent; decisive claims
  re-verified): current clocks, coordination machinery, observed publish
  latency from `origin/publish` audit rows, request-cost tables — folded
  into sec1/sec6.
- `CODEX_EVENT_1_REVIEW_2026-08-28.md` — Event-1 verdict (DESIGN
  INCOMPLETE at 000b13a), captured verbatim.
- Prior art: PRD-299 (OPEN coordination), PRD-149/141 (PT slot machinery),
  PRD-194 (publish ownership), DECISIONS 2026-08-09/2026-08-11 (CF-D
  bundle and supersession), `audits/cf-clock-executor-coordination-2026-08/`
  (historical packet; its "current state" section is STALE — PRD-299
  landed after it — and is superseded by sec1 here),
  `audits/cloudflare-morning-brief-evidence-2026-08/` (CF-E2 evidence
  harness, date-locked/expired; its parent-packet citation is broken —
  noted, not relied upon).

## CORRECTION CYCLE (GOV-2 sec2 step 4 — the ONE consolidated correction)

Event-1 verdict: DESIGN INCOMPLETE at `000b13a`
(`CODEX_EVENT_1_REVIEW_2026-08-28.md`). All eight findings dispositioned in
this single revision:
- **F1 (MATERIAL, same-instant overlaps):** APPLIED — sec3 redesigned:
  one owner per instant. 06:00 belongs exclusively to the daily pipeline
  and hourly `(6,0)` is retired (kills the dual-notification path); the
  GitHub 06:30 heartbeats are retimed to 06:40-wall-clock delayed
  fallbacks (`30 13`->`40 13`, `30 14`->`40 14`), eliminating the
  same-instant CF-vs-GitHub peer race per the 2026-08-11 pattern; the
  `ui/` last-writer-overwrite and three-writer Pages triggers are
  enumerated in sec5. Ownership put to the ruling as Q7.
- **F2 (slot-identity shift):** APPLIED — routine dispatches carry an
  EXPLICIT intended slot (`kind` + `slot` inputs, `--routine-slot`);
  start-time inference remains only on the fallback path and its
  residual 06:30-loss case is named in Q9, not claimed away.
- **F3 (send/persist non-atomicity):** APPLIED — sec2/sec3 no longer
  claim "second arrival always no-op"/"exactly one send"; the
  at-least-once residual is stated, pinned with new failure-path
  regressions (sec7), and put to the ruling as Q10.
- **F4 (Worker gate contract):** APPLIED — sec4 now specifies
  `event.scheduledTime` authority, a static (cron, offset)->slot lookup
  table with no windows, shared-trigger disambiguation (the 14:00Z case),
  and requests an explicit time-basis extension ruling (Q8) instead of
  claiming the 2026-08-11 ruling is honored "by construction".
- **F5 (cost arithmetic):** APPLIED — sec6 recomputed in logical
  provider operations (48 yfinance + 1 Cboe per hourly ceiling), delta
  corrected to ≈+0 (a slot retired for a slot added), retry/HTTP caveats
  and measured-accounting requirement added; units put to the ruling
  (Q11).
- **F6 (participants/falsifier/FILES):** APPLIED — sec5 enumerates
  `state.py`, runtime send/persist sites, both CI transport scripts,
  `macro_awareness.yml`, config/ingestion/derived, `gex_snapshot.py`;
  falsifier widened; sec8 adds `tests/test_hourly_slot_idempotency.py`,
  a Node harness executing the PRODUCTION worker gate (PRD-250
  precedent), `alert_runner.py`, and the cron retimes; sec9 re-estimated.
- **F7 (missing ruling questions):** APPLIED — Q7-Q11 added; Q5's
  "micro-slice" alternative reclassified (MICRO unavailable).
- **F8 (RECOMMENDED, deploy-status wording):** APPLIED — sec1.2 now says
  "repository-recorded as undeployed; no CF-E1 completion evidence".
No new material class was introduced: every seam the correction touches
(hourly crons, slot set, dispatch inputs, worker gate) was inside the
reviewed design's surface; the correction assigns ownership and contracts
on that same surface.
