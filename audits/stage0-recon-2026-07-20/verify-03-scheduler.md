# Verification — Track C: stage0-03-scheduler-v0.1.md (Q16-18)

**MEMORY PROVENANCE CORROBORATED; SESSION ID SELF-REPORT INVALID** — see
`verify-00-disposition-index.md`'s capability header: this session's
self-reported session id was a template placeholder, invalid on its own
terms, but its memory provenance is independently corroborated from the
real subagent transcript (agentId `ae66653afaad4b245`): zero memory-file
reads. Isolation stands as verified on the memory dimension. The findings
below were independently derived via each check's own methodology as a
further, separable claim. Verified against
this worktree's HEAD, source-tree-identical to the pinned SHA
`771f730839b00b0537327f9696210275f36cd790`.

## Per-question disposition

- **Q16 (schedule owners, force-slot, dedup) — CONFIRMED.**
  - `.github/workflows/cuttingboard.yml` lines 3-16: exactly the three cron
    strings claimed — `50 12 * * 1-5`, `0 13 * * 1-5`, `30 23 * * 0` — with
    an in-file comment noting the ORB/intraday crons were already removed
    (PRD-189) — confirmed. Lines 73-89 ("Determine run mode") pass
    `github.event.schedule` (`CB_SCHEDULE`) into
    `scripts/resolve_run_mode.py` — confirmed.
  - `scripts/resolve_run_mode.py` `_DEDICATED` dict maps exactly those three
    cron strings to `live`/`sunday`/`prefetch`; `resolve()` returns `NOOP` for
    `workflow_dispatch` misuse or any other schedule string, and is a pure
    cron-string lookup (no wall-clock math) — confirmed, matching the
    module's own docstring about the queue-delay bug this replaced.
  - `.github/workflows/hourly_alert.yml` lines 1-28: the PT-window cron set,
    self-serialized under `concurrency.group: hourly-alert` — confirmed.
    Lines ~98-104: `workflow_dispatch` unconditionally runs
    `python -m cuttingboard.alert_runner --force-slot` — confirmed.
  - `alert_runner.py:42-102` (`main`): `force_slot` bypasses both the
    `routine_pt_slot` window check and the `load_last_slot` equality check,
    going straight to `canonical_slot_utc` + `_execute_notify_run` — confirmed
    exactly, including the two suppression paths
    (`outside_routine_window`, `suppressed_same_slot`) and their audit
    records.
  - `notifications/hourly_slot.py:41-125`: `canonical_slot_utc` floors in
    `America/Vancouver` then converts to UTC (DST-correct); `routine_pt_slot`
    returns `None` outside the allowed window or beyond `max_lag_minutes=25`;
    `save_last_slot`/`load_last_slot` persist/read `slot_utc` — confirmed all
    behaviors exactly as described.
  - `runtime/__init__.py:531-536` — `save_last_slot(slot_utc)` is called only
    `if alert_sent and slot_utc is not None:` — confirmed: a failed send
    genuinely does not persist the slot.
  - `hourly_alert.yml:62-87` — the "Restore publish state" step restores
    `logs/last_hourly_slot.json` (among others) from the `publish` branch
    before the alert runs — confirmed the "dedup is cross-run, not
    runner-local" claim.

- **Q17 (smallest no-product-side-effect dispatch) — CONFIRMED.**
  - `cuttingboard.yml:16-28` exposes `verify` as a `workflow_dispatch` mode
    option — confirmed.
  - `cuttingboard.yml:254-271` ("Verify run" step): runs
    `python -m cuttingboard --mode verify --notify-mode premarket`, gated to
    `job_mode in {live, sunday, verify}`, with an explicit comment that
    verify-only dispatch must leave `PUBLISH_READY` false — confirmed.
  - `cuttingboard.yml:309-358` ("Commit artifacts"/"Push" steps): both gated
    on `env.PUBLISH_READY == 'true'` — confirmed a `verify` dispatch cannot
    reach either.
  - `runtime/__init__.py:191-198` (`cli_main`): `MODE_VERIFY` branches
    directly to `verify_run_summary(...)`, printing PASS/FAIL — confirmed,
    does not call `execute_run`.
  - `runtime/__init__.py:1499-1510` (`verify_run_summary`): reads and
    JSON-validates the target summary file, returning
    `{"pass": False, ...}` on a missing file or invalid JSON — confirmed.

- **Q18 (observed replacement before old-schedule removal) — CONFIRMED as
  REPORTED/OPERATOR** (this question is explicitly non-runtime; its evidence
  is documentary, and I checked the documentary citations directly rather
  than trusting the paraphrase):
  - `docs/DECISIONS.md` "2026-05-24 — Retire hourly Telegram cadence..."
    (lines 2795-2819): confirmed verbatim — "The hourly cadence stays alive
    until the pre-market report has earned trust in production," no
    measurable per-slot threshold stated.
  - `docs/DECISIONS.md` "2026-06-17 — PRD-194 verified end-to-end" (lines
    2288-2311): confirmed verbatim — describes a live dispatch, `publish`
    branch advancement, fresh artifacts, and Pages deployment as the
    standard of "observed."
  - `docs/DECISIONS.md:1239-1257`: confirmed verbatim — describes a ~23-hour
    stretch of green-but-suppressed hourly runs producing no fresh board
    data, directly supporting "green status alone is historically
    insufficient."
  - `docs/PROJECT_STATE.md:180-190` (containing line 182's PRD-189 entry):
    confirmed the "fresh scoreboard row reaching the live site" language.
  - `docs/prd_history/PRD-189.md:163-178`: confirmed — records the ORB/
    intraday `cuttingboard.yml` crons were removed because their real notify
    path is `hourly_alert.yml`, not `cli_main`.
  - `docs/prd_history/PRD-192.md:15-38,128-138`: confirmed — records the
    hourly window as the de facto replacement and the "dropped-slots guard"
    (`tests/test_resolve_run_mode.py`) staying green by design (no slot
    re-wired).

## Assessment

Every STATIC/RUNTIME citation checked resolves exactly to the claimed content
— cron strings, resolver logic, force-slot bypass semantics, the
success-only slot-persistence guard, and the verify-mode publish gating all
match precisely, including exact variable/constant names
(`_DEDICATED`, `PUBLISH_READY`, `max_lag_minutes=25`). The REPORTED/OPERATOR
material in Q18 is honestly labeled as documentary rather than runtime, and
every document citation checked out verbatim.

**Disposition: CONFIRMED across Q16, Q17, Q18. Nothing falsified or narrowed.**
