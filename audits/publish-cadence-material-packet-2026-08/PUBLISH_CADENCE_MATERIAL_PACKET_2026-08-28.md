# Reliable market cadence — MATERIAL design packet (Lane B)

```
STATUS: PROVISIONAL MATERIAL PACKET — 2026-08-28 — DESIGN ONLY
AUTHORIZES NO IMPLEMENTATION, NO PRD NUMBER, NO WORKER DEPLOY, NO WORKFLOW
EDIT, NO GATE A, NO MERGE.
GOV-2 PACKET-REVIEW CYCLE: NOT STARTED. AWAITING: Event-1 independent Codex
review (GOV-2 sec2 step 3).
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
2. **The Worker exists in-repo and is UNDEPLOYED**
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
created: the Worker only front-runs the same workflows the crons already
fire, and the existing suppression machinery makes the second arrival a
no-op. Streaming is out of scope; snapshots stay the data model.

## sec3 — Target cadence mapping (minimum change)

| Owner slot | Mechanism | Change required |
|---|---|---|
| PRE ~06:00 PT (pre-market board) | The existing OPEN/live daily pipeline, CF-dispatched at 06:00 PT (this is today's 06:05-PDT publish made punctual and DST-stable; "PRE" in the owner cadence = the pre-open board, not the 12:50Z cache-warm, which is untouched) | Worker cron set + PT gate (sec4); no workflow-predicate change expected — a 06:00 PT dispatch satisfies the existing >=12:55Z and before-ET-open predicates in both DST regimes |
| OPEN ~06:30 PT | Existing hourly slot (6,30), CF-dispatched routinely | New routine (non-forced) dispatch input on `hourly_alert.yml` (sec5); slot already allowed |
| POST-OPEN ~06:45 PT | New hourly-class slot | Add `(6,45)` to `ALLOWED_PT_SLOTS` + the same routine dispatch; this also finally implements the authorized CF-D3 "OPEN+1" intent |
| HOURLY 07:00..13:00 PT | Unchanged GitHub crons + gate; optionally CF also dispatches routinely on the hour for punctuality | Optional (ruling Q3) |

Slot-collapse check for the new set {(6,0),(6,30),(6,45),(7,0),...}: gaps
of 15 min sit inside `max_lag_minutes=25`, so the largest-slot-within-lag
rule makes a PUNCTUAL 06:45 fire resolve to (6,45) correctly, and a
15-min-late 06:30 fire also resolves to (6,45) — sending 06:45's content
early-ish and suppressing the real 06:45 arrival as same-slot. That is the
existing collapse semantic doing its job (one send per slot, no duplicate);
the packet accepts it and documents it rather than widening `max_lag`
(rejected by the PRD-250 decision) or shrinking it (would re-create the
silent-green class). CF punctuality makes the late-fire case rare.

## sec4 — DST without a peer scheduler

Cloudflare cron triggers are UTC-only, so PT wall-clock fidelity comes from
firing BOTH offsets and gating in the Worker: for each PT slot, two crons
(e.g. 06:00 PT -> `0 13 * * 1-5` AND `0 14 * * 1-5`), and the Worker
computes the current PT wall-clock (`Intl.DateTimeFormat` with
`America/Los_Angeles`) at fire time and dispatches ONLY when it matches the
slot's PT window; the off-season twin no-ops inside the Worker. This keeps
the Worker transport-only (a clock read, no state), honors the 2026-08-11
time-basis ruling by construction (the PT behavior is real, not a
mislabeled UTC cron), and never double-dispatches: at any real instant at
most one cron of a pair matches the PT gate, and even a bug that dispatched
both is absorbed by first-success (pipeline) / same-slot dedup (hourly) —
the existing guards, not new ones. GitHub fallback crons stay fixed-UTC and
seasonally drifting, exactly as the accepted convention states; punctual PT
is the Worker's property, resilience is GitHub's.

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
6. Consumers of slot semantics enumerated for regression: dedup persistence
   (`last_hourly_slot.json` restore/force-add), audit reasons
   (`outside_routine_window`, `suppressed_same_slot`), the freshness gate
   (`fresh=false` tail-skip), Pages `workflow_run` triggers, notification
   ownership (PRD-295/296/300), GEX per-hourly Cboe GET.
Falsifier: `rg -n "force-slot|ALLOWED_PT_SLOTS|routine_pt_slot|CB-SLOT" \
.github/ workers/ cuttingboard/ scripts/ tests/` enumerates exactly the
surfaces above and their tests.

## sec6 — Request volume (quantified; no paid dependency)

- Added: one hourly-class slot (06:45) ≈ +49 yfinance + 1 Cboe per day.
- Recommended companion fix (same PRD, cost-negative): add the pipeline's
  existing `actions/cache` step for `data/cache` to `hourly_alert.yml` —
  each warm hourly run drops ~23 OHLCV downloads; across 10 slots ≈ −230
  requests/day. Net cadence change: ≈ −180 yfinance requests/day versus
  today, +1 Cboe GET (the 06:45 run's GEX refresh stays within the
  "best-effort hourly refresh" authorization since it IS an hourly-class
  run; flagged for the ruling regardless, per the GEX cadence boundary in
  DECISIONS/PROJECT_STATE).
- Worker dispatches are free-tier Cloudflare cron + one GitHub API POST per
  slot (~4-13/day). No new data provider anywhere.

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
- Worker PT-gate: table-driven tests of the gate function across DST
  boundaries (worker JS is testable via node in CI or a mirrored fixture
  table asserted from Python; the PRD decides the mechanism).
- Request-volume figures recomputed and recorded in the PRD.
- The mutation-verified red-test discipline applies to every new guard.

## sec8 — FILES cone (estimate)

`M workers/cuttingboard-clock/src/index.js`,
`M workers/cuttingboard-clock/wrangler.example.toml`,
`M workers/cuttingboard-clock/README.md`,
`M .github/workflows/hourly_alert.yml` (dispatch input + cache step),
`M cuttingboard/notifications/hourly_slot.py`,
`M tests/test_hourly_slot.py` (or the existing slot-test home),
`M tests/test_open_slot_coordination.py`,
`M tests/test_ci_artifact_hygiene.py` (workflow-shape assertions),
`M docs/PROJECT_STATE.md` / DECISIONS entry at closeout.
`cuttingboard.yml` expected UNTOUCHED (any discovered need = STOP and
reclassify before edit).

## sec9 — LOC ceiling (estimate)

<=180 net production LOC (worker + workflow + slot set), <=450 net test
LOC. STOP-AND-RENEW on breach.

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
**Q5 — Hourly `actions/cache` companion fix.** Recommend: include (cost
negative, isolated). Alternative: separate micro-slice.
**Q6 — Worker deploy.** The design assumes Dustin performs CF-E1/E2 per
the standing authorization once the implementation lands; confirm or
re-sequence.

## sec12 — Evidence index

- Recon sweep 2026-08-28 (fresh-context subagent; decisive claims
  re-verified): current clocks, coordination machinery, observed publish
  latency from `origin/publish` audit rows, request-cost tables — folded
  into sec1/sec6.
- Prior art: PRD-299 (OPEN coordination), PRD-149/141 (PT slot machinery),
  PRD-194 (publish ownership), DECISIONS 2026-08-09/2026-08-11 (CF-D
  bundle and supersession), `audits/cf-clock-executor-coordination-2026-08/`
  (historical packet; its "current state" section is STALE — PRD-299
  landed after it — and is superseded by sec1 here),
  `audits/cloudflare-morning-brief-evidence-2026-08/` (CF-E2 evidence
  harness, date-locked/expired; its parent-packet citation is broken —
  noted, not relied upon).
