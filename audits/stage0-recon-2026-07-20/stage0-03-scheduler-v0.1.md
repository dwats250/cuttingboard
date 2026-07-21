> Orchestrator note: Codex self-reported it could not detect its own
> CLI banner/session id (a known blind spot -- the banner is printed
> by the CLI wrapper, outside the model's own context). The actual
> session id, extracted from stdout by the orchestrator, is
> `019f8315-8407-7c61-bb73-c5c08ba1b80a`. Rollout: `rollout-2026-07-20T22-10-53-019f8315-8407-7c61-bb73-c5c08ba1b80a.jsonl`.
> Verification disposition: CORROBORATED -- every tool call in the
> rollout is a local `exec` (git/rg/sed/python3/pytest); no MCP,
> plugin, browser, or network tool call appears anywhere; the
> self-reported memory-file reads (MEMORY.md, memory_summary.md,
> and any skill files) match the rollout's actual reads exactly.
>
---

## Header
- Repository and inspected SHA: dwats250/cuttingboard @ 771f730839b00b0537327f9696210275f36cd790
- Session/model: I could not detect a CLI banner; best identification: Codex (GPT-5), session ID unavailable.
- Repository access: READ
- Test/trace capability: YES — pure no-write traces of `scripts/resolve_run_mode.py` returned `live`, `noop`, and `verify`; `routine_pt_slot`/`canonical_slot_utc` traces worked. Targeted `pytest` did not initialize because the read-only sandbox has no usable temporary directory.
- Prior findings visible before first pass: YES — `docs/DECISIONS.md:19-260`, `:527-540`, `:1226-1260`, `:2288-2311`, and `:2795-2819`; `docs/PROJECT_STATE.md:1-194` (scheduler-relevant conclusions at `:182,187`); post-first-pass broad-search excerpts from `audits/FABLE_REVIEW.md:44-53`, `audits/BUILD_PLAN.md:61-69`, and `audits/recon-2026-07-01/staged-queued-items.md:38-46`. Only scheduler-relevant material is used below.
- Evidence classes used: STATIC@771f730839b00b0537327f9696210275f36cd790, RUNTIME@771f730839b00b0537327f9696210275f36cd790, REPORTED, HYPOTHESIS, OPERATOR
- Questions owned by this artifact: Q16-18
- Explicit out-of-scope tracks: stage0-01-decision-surface-v0.1.md, stage0-02-evaluation-v0.1.md, stage0-04-gex-v0.1.md, stage0-05-governance-debt-v0.1.md

## Memory provenance (mandatory -- per docs/DECISIONS.md 2026-07-19: a leg that cannot produce this is not a fresh-context leg)
- Memory surface loaded, enumerated: `/home/dustin/.codex/memories/memory_summary.md` was injected at session start; `/home/dustin/.codex/memories/MEMORY.md` was queried; `/home/dustin/.agents/skills/gitnexus-exploring/SKILL.md` was opened. No rollout summary was opened.
- Checked against this dispatch's excluded-content list: N/A for a producing/recon leg -- no snapshot-exclusion set was prepared for this dispatch (that mechanism applies only to the separate verification session isolating itself from producer conclusions). The "prior findings visible" line above is this artifact's applicable substitute disclosure.
- Persisted anything back to memory this run: NO
- Session id: I could not determine it; no CLI banner or session metadata was exposed.

## MCP / tool-call audit
- none

## Scheduler

### Q16 — Live schedule owners and exact forced-slot/deduplication behavior

At repository scope, the only tracked `on.schedule` owners are `Cuttingboard Pipeline` and `Cuttingboard Hourly Alert`. Remote workflow enablement, delayed delivery, and any out-of-repo scheduler are unavailable in this locked session.

- **Pipeline owner.**
  - **Authority / excerpt:** `.github/workflows/cuttingboard.yml` `on.schedule` at lines 3-16 declares `50 12 * * 1-5`, `0 13 * * 1-5`, and `30 23 * * 0`; `Determine run mode` at lines 73-89 passes `github.event.schedule` into `scripts/resolve_run_mode.py::resolve`. That resolver maps the three exact cron strings at lines 42-62.
  - **Classification:** `STATIC@771f730839b00b0537327f9696210275f36cd790`. `RUNTIME@771f730839b00b0537327f9696210275f36cd790` pure traces returned `live` for `0 13 * * 1-5`, `noop` for an unmapped cron, and `verify` for a dispatch-mode input.
  - **Reachability:** schedule event → `CB_SCHEDULE` → `resolve()` → `job_mode` → prefetch/live/sunday workflow steps.
  - **Current unavailable / failure:** an unknown or absent schedule resolves to `noop`; mode-specific product work and `PUBLISH_READY=true` do not run. The pipeline concurrency group is self-only (`cuttingboard-pipeline`, lines 29-36), so no cross-workflow serialization is claimed.
  - **Falsifier:** a tracked third `on.schedule` owner, a changed resolver map, or a trace at this SHA returning another mode for those inputs.
  - **PRD consequence:** `HYPOTHESIS` — any scheduler-scoped PRD would need to preserve or deliberately replace this cron-string ownership boundary rather than infer pipeline behavior from runner wall-clock time.

- **Hourly owner, force path, and dedup path.**
  - **Authority / excerpt:** `.github/workflows/hourly_alert.yml` lines 3-28 owns the PT-window cron set and self-serializes it as `hourly-alert`; lines 98-104 unconditionally invoke `python -m cuttingboard.alert_runner --force-slot` for `workflow_dispatch`. `cuttingboard/alert_runner.py::main` lines 42-102 chooses force mode from the flag or `CUTTINGBOARD_FORCE_SLOT=1`; `notifications/hourly_slot.py::{routine_pt_slot,canonical_slot_utc,load_last_slot}` lines 41-125 define slots and persistence; `runtime/__init__.py::_execute_notify_run` lines 491-536 saves a slot only after a successful send.
  - **Classification:** `STATIC@771f730839b00b0537327f9696210275f36cd790`. `RUNTIME@771f730839b00b0537327f9696210275f36cd790` pure traces showed an in-window timestamp resolves to its PT slot, a 26-minute-late timestamp resolves to `None`, and forced canonicalization floors to the current PT hour.
  - **Reachability:** scheduled event → `routine_pt_slot()` → `logs/last_hourly_slot.json` comparison → `_execute_notify_run(..., slot_utc=...)` → Telegram/artifacts; workflow dispatch → `--force-slot` → `_execute_notify_run` directly. The workflow restores `last_hourly_slot.json` from `publish` before execution (`hourly_alert.yml:62-87`), making dedup cross-run rather than runner-local.
  - **Current unavailable / failure:** normal runs accept only 06:00, 06:30, and hourly 07:00–13:00 PT slots within 25 minutes; outside/late runs write `outside_routine_window` suppression and return 0 (`alert_runner.py:63-81`). A matching persisted slot writes `suppressed_same_slot` and returns 0 (`:82-95`). Missing or malformed state is treated as no prior slot (`hourly_slot.py:95-111`), so a repeat may run. Force mode skips both checks and may send/write product artifacts. A failed send does not persist the slot (`runtime/__init__.py:533-536`).
  - **Falsifier:** removal or alteration of the force branch, the slot equality check, the success-only persistence condition, or a controlled trace at this SHA showing a normal duplicate proceeds.
  - **PRD consequence:** `HYPOTHESIS` — any scheduler work touching hourly dispatch must treat manual force dispatch as an intentional dedup bypass, not as a safe diagnostic path.

Cloudflare decision-history condition: no additional May record is added here. `docs/DECISIONS.md:527-540` already identifies the retired Wrangler/`external_trigger` subsystem; I treat that as an existing decision-log record and avoid duplicating it.

### Q17 — Smallest diagnostic dispatch with no product side effects

- **Current least-product-side-effecting workflow dispatch:** `Cuttingboard Pipeline` → `workflow_dispatch` → `mode=verify`.
  - **Authority / excerpt:** `.github/workflows/cuttingboard.yml` lines 16-28 exposes `verify`; lines 254-271 invoke `python -m cuttingboard --mode verify --notify-mode premarket` and leave `PUBLISH_READY` false. Commit and push require `PUBLISH_READY == 'true'` at lines 309-358. `cuttingboard/runtime/__init__.py::cli_main` lines 191-198 branches directly to `verify_run_summary`; `verify_run_summary` lines 1499-1510 reads and validates the selected summary.
  - **Classification:** `STATIC@771f730839b00b0537327f9696210275f36cd790`; `RUNTIME@771f730839b00b0537327f9696210275f36cd790` pure resolver trace returned `verify` for `workflow_dispatch` with `CB_DISPATCH_MODE=verify`.
  - **Reachability:** dispatch selection → `resolve()` → Verify run → read/validate `logs/latest_run.json` → process exit result; it does not reach `execute_run`, notification send, artifact commit, or publish.
  - **Current unavailable / failure:** missing, malformed, or invalid summary returns failure from `verify_run_summary`; the workflow still performs checkout, publish-state restore, dependency install, lint/test, engine-doctor artifact upload, and external reads. Thus “no product side effects” means no notification, product artifact generation, commit, or push—not no CI/control-plane activity.
  - **Falsifier:** a verify branch that invokes `execute_run` or sets `PUBLISH_READY=true`, or a controlled dispatch trace that creates product artifacts or sends a notification.
  - **PRD consequence:** `HYPOTHESIS` — this is the current diagnostic baseline, but a future PRD must not claim live no-side-effect behavior without an observed controlled dispatch.

### Q18 — Observed replacement before old schedule removal

- **The explicit retirement authority is trust in production, not workflow success.**
  - **Authority / excerpt:** `docs/DECISIONS.md` § “2026-05-24 — Retire hourly Telegram cadence…” lines 2795-2819 says the hourly cadence remains alive until the replacement pre-market report has “earned trust in production.”
  - **Classification:** `OPERATOR`.
  - **Reachability:** this ruling governs retirement of the existing hourly/daily/Sunday/intraday Telegram schedule stack.
  - **Current unavailable / failure:** the ruling does not define a per-slot measurable threshold or show current completion; this session cannot observe production.
  - **Falsifier:** a later Dustin ruling that retires the cadence or replaces this production-trust condition.
  - **PRD consequence:** `HYPOTHESIS` — a future retirement PRD would need an explicit, per-old-schedule observation threshold before removal.

- **The repository’s historical production proof shows what “observed” needs beyond green status.**
  - **Authority / excerpt:** `docs/DECISIONS.md` § “2026-06-17 — PRD-194 verified end-to-end” lines 2288-2307 reports a live dispatch, publish-branch advancement, fresh artifacts, Pages deployment, and dedup read-back restore; `docs/PROJECT_STATE.md:182` reports a fresh scoreboard row reaching the live site. In contrast, `docs/DECISIONS.md:1239-1257` reports green hourly runs that suppressed, skipped publish, and left the board stale for roughly 23 hours.
  - **Classification:** `REPORTED`; no production trace was reproduced this pass.
  - **Reachability:** replacement dispatch → generated artifacts → `publish` branch → Pages consumer; hourly suppression can terminate before that product path.
  - **Current unavailable / failure:** status success alone is historically insufficient because suppression can be green while no fresh product output reaches the consumer.
  - **Falsifier:** a controlled production trace showing that a green suppressed run always yields a new product timestamp and downstream deployment.
  - **PRD consequence:** `HYPOTHESIS` — “observed replacement” should require the intended route, a newly generated product artifact or notification, downstream consumer visibility, and schedule-specific suppression/dedup evidence; a green workflow alone is insufficient.

- **The old intraday pipeline slots have historical source-level replacement evidence, but not fresh runtime evidence from this leg.**
  - **Authority / excerpt:** `docs/prd_history/PRD-189.md:163-178` records removal of the ORB/intraday pipeline crons because their real notify path was `hourly_alert.yml`; `docs/prd_history/PRD-192.md:15-38,128-138` records the hourly window as the replacement and the dropped-slots guard.
  - **Classification:** `REPORTED`.
  - **Reachability:** removed `cuttingboard.yml` intraday routes → hourly-alert notify path → canonical PT-hour dedup.
  - **Current unavailable / failure:** targeted tests could not initialize in this read-only sandbox, and no live hourly trace was run; this leg therefore cannot upgrade historical replacement assertions to current runtime proof.
  - **Falsifier:** restored old cron/mode reachability in current source, or a controlled trace showing the hourly path fails the claimed covered slot.
  - **PRD consequence:** `HYPOTHESIS` — source-level route replacement and a guard against old-slot reintroduction are necessary context, but not sufficient by themselves to justify a future schedule retirement.

## NO CLAIM

- stage0-01-decision-surface-v0.1.md — I make no claim about this track.
- stage0-02-evaluation-v0.1.md — I make no claim about this track.
- stage0-04-gex-v0.1.md — I make no claim about this track.
- stage0-05-governance-debt-v0.1.md — I make no claim about this track.

