# cuttingboard-clock (Cloudflare Worker) — DEPLOYED 2026-08-28

Deployed by Dustin 2026-08-28 ~22:58 UTC (owner-held credential acts:
`wrangler login` / `wrangler deploy -c wrangler.example.toml` /
`wrangler secret put GH_DISPATCH_TOKEN -c wrangler.example.toml`; no
`wrangler.toml` created). Live cron set verified equal to the reviewed
four expressions; secret present by name only. Evidence:
`audits/post-prd321-commissioning-2026-08/`. CF-E1 first-real-fire
capture pending the next weekday cron (Monday 2026-08-31 12:50 UTC).
The deployment-mechanics text below is retained for redeploys.

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
- On a Cloudflare cron trigger, resolves the full weekday cadence from
  `event.scheduledTime`: **PRE** (12:50 UTC) and **06:00 PT OPEN** POST
  `workflow_dispatch` to `.github/workflows/cuttingboard.yml` on `main` with
  `{ mode, slot, source }` (OPEN→live, PRE→prefetch); the **06:30 / 06:45 /
  07:00–13:00 PT** routine snapshots POST to `.github/workflows/hourly_alert.yml`
  with `{ kind: routine, slot, source }`. `source` is provenance only.
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
Until deployed, the seasonal GitHub fallback crons (`20 13` / `20 14 * * 1-5`,
the 06:20 PT pair; the off-season twin no-ops via the season gate) are the sole
automatic OPEN trigger and the board publishes ~20 min later than the 06:00 PT
target — an owner-accepted rollout consequence (DECISIONS 2026-08-11; retimed
by PRD-319).

## Coordination (all GitHub-native; no persisted state)
- CF OPEN succeeds → the 06:20 PT seasonal GH fallback's first-success pre-check
  sees the in-window success → no-op.
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
