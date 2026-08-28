# cuttingboard-clock (Cloudflare Worker) — UNDEPLOYED

PRD-299 / PRD-319. The preferred punctual **clock** for the full Cuttingboard
weekday cadence (pipeline 06:00 PT board + hourly 06:30/06:45/07:00-13:00 PT
snapshots). PT slot identity resolves from `event.scheduledTime` via the pure
exported `resolveSlot()` (America/Los_Angeles lookup; owner time-basis
extension ruling 2026-08-28); dual-offset UTC crons make PT wall-clock hold
across DST, with off-season twins no-oping inside the Worker. The production
gate is Node-executed by `tests/test_worker_clock_gate.py`. It only
POSTs a GitHub `workflow_dispatch`; GitHub remains the executor / observation /
validation / rendering / publication authority. **Dispatch acceptance is
*attempt authorization* only — never observation or publish success.**

This directory ships the Worker source **undeployed**. Deployment and the GitHub
credential are owner-held and performed out-of-band (CF-D5); nothing here is
active until then.

## What it does (and only this)
- On a Cloudflare cron trigger, resolves **PRE** (12:50 UTC) or **OPEN** (13:00 UTC).
- POSTs `workflow_dispatch` to `.github/workflows/cuttingboard.yml` on `main`
  with `{ mode, slot, source }` (OPEN→live, PRE→prefetch; `source` is provenance
  only).
- Logs accepted (HTTP 204) vs rejected dispatch.

## What it must NOT do
Market logic, board-freshness logic, `latest_run` interpretation, dedup /
idempotency state, KV / Durable Objects. First-success coordination lives in the
GitHub workflow (`scripts/check_open_slot_satisfied.py`), never here.

## Credential (owner-held)
A fine-grained GitHub PAT: repository `dwats250/cuttingboard`, **Actions: Read and
write** only (write is required to dispatch); no other permission. Stored as the
Worker secret `GH_DISPATCH_TOKEN`. **No credential value is committed to this
repo** (CF-D5).

## Deploy (owner, out-of-band)
```sh
cp wrangler.example.toml wrangler.toml
wrangler secret put GH_DISPATCH_TOKEN   # paste the fine-grained Actions-write PAT
wrangler deploy
```
Until deployed, the GitHub fallback cron (`5 13 * * 1-5`, ~13:05 UTC) is the sole
automatic OPEN trigger and the board publishes ~5 min later than today — an
owner-accepted rollout consequence (DECISIONS 2026-08-11).

## Coordination (all GitHub-native; no persisted state)
- CF OPEN succeeds → the 13:05 GH fallback's first-success pre-check sees the
  in-window success → no-op.
- CF OPEN fails / never fires → the GH fallback executes.
- Duplicate CF dispatch → serialized by the dedicated OPEN concurrency group
  (`queue: max`, non-evicting); the first completed successful OPEN satisfies the
  slot, later ones no-op.
- Proof uncertainty (Actions API error) → the fallback executes rather than risk
  a missing board (fail toward availability).

## Testing
The Worker is transport-only and undeployed; it has no market logic to unit-test.
Its dispatch semantics (accepted vs rejected logging, Actions-write-only scope)
are verified by inspection and, once deployed by the owner, by CF-E1 (the real
CF→GitHub dispatch trigger capture). The GitHub-side coordination it feeds is
fully tested in `tests/test_open_slot_coordination.py`.
