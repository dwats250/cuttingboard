# cuttingboard-clock (Cloudflare Worker) — the AUTHORITATIVE routine clock

Deployed by Dustin 2026-08-28 ~22:58 UTC (owner-held credential acts:
`wrangler login` / `wrangler deploy -c wrangler.example.toml` /
`wrangler secret put GH_DISPATCH_TOKEN -c wrangler.example.toml`; no
`wrangler.toml` created). Evidence: `audits/post-prd321-commissioning-2026-08/`.
CF-E1 (first real CF -> GitHub dispatch capture) did NOT complete: no accepted
dispatch was ever correlated with a GitHub run, and the last hourly delivery
through any path was 2026-08-26 (DECISIONS 2026-09-09). The reviewed
source/config in this directory must be REDEPLOYED by the owner after merge;
see "Owner post-merge actions" below.

PRD-299 / PRD-319, completion PR 2026-09-09. The **clock** for the full
Cuttingboard cadence (pipeline 06:00 PT board, hourly 06:30/06:45/07:00-13:00
PT snapshots, PRE 12:50 UTC cache warm, and the Sunday 23:30 UTC session). PT
slot identity resolves from `event.scheduledTime` via the pure exported
`resolveSlot()` (America/Los_Angeles lookup; owner time-basis extension ruling
2026-08-28); dual-offset UTC crons make PT wall-clock hold across DST, with
off-season twins no-oping inside the Worker. The production gate and the
scheduled handler are Node-executed by `tests/test_worker_clock_gate.py`. It
only POSTs a GitHub `workflow_dispatch`; GitHub remains the executor /
observation / validation / rendering / publication authority. **Dispatch
acceptance is *attempt authorization* only — never observation or publish
success.**

## Schedule ownership (after the completion PR)
- **Cloudflare (this Worker) = authoritative routine clock.** Every routine
  execution arrival (PRE, OPEN, hourly, Sunday) is a `workflow_dispatch` from
  here.
- **GitHub schedule = liveness probe only.** `hourly_alert.yml` keeps its cron
  arrivals as a `liveness` job that reads the published
  `logs/last_hourly_slot.json` and goes RED when no same-day hourly delivery
  exists at/after 08:00 PT. A probe never runs the alert runner, fetches data,
  sends Telegram, renders, or publishes. There is NO GitHub execution fallback:
  a REJECTED / ERROR dispatch here is a missed slot until the owner acts.
- `cuttingboard.yml` has no schedule triggers; manual `workflow_dispatch`
  (live / prefetch / sunday / verify) is preserved.

## Cron set (wrangler.example.toml)
| cron (UTC) | resolves to |
|---|---|
| `50 12 * * MON-FRI` | PRE cache warm -> `cuttingboard.yml` `{mode: prefetch, slot: PRE}` |
| `0 13-21 * * MON-FRI` | 06:00 PT OPEN -> `cuttingboard.yml` `{mode: live, slot: OPEN}`; 07:00-13:00 PT -> `hourly_alert.yml` `{kind: routine, slot}` (per season) |
| `30 13,14 * * MON-FRI` | 06:30 PT hourly (one of the pair per season) |
| `45 13,14 * * MON-FRI` | 06:45 PT hourly (one of the pair per season) |
| `30 23 * * SUN` | Sunday session -> `cuttingboard.yml` `{mode: sunday}` (no slot; existing contract) |

The weekday field is the explicit `MON-FRI` name range. The earlier numeric
`1-5` form was observed to fire Sunday-Thursday on Cloudflare (2026-09-09
clock/fallback adjudication); every weekday TIME is unchanged from PRD-319.
`source: cloudflare-worker` is provenance only.

## What it does (and only this)
- On a Cloudflare cron trigger, resolves exactly one dispatch (or none) from
  `event.scheduledTime` and POSTs it to `main`.
- Logs `dispatch ACCEPTED status=204` / `dispatch REJECTED status=<n>` /
  `dispatch ERROR error=<class>` with `workflow`, `slot` (or `mode`), and
  `scheduledTime`. Persisted via `[observability]` in the TOML so the lines
  survive the invocation.

## What it must NOT do
Market logic, board-freshness logic, `latest_run` interpretation, dedup /
idempotency state, KV / Durable Objects, retries, credential probing. It never
logs the token, request headers, or response bodies. First-success
coordination lives in the GitHub workflow (`scripts/check_open_slot_satisfied.py`),
never here.

## Credential (owner-held)
A fine-grained GitHub PAT: repository `dwats250/cuttingboard`, **Actions: Read and
write** only (write is required to dispatch); no other permission. Stored as the
Worker secret `GH_DISPATCH_TOKEN`. **No credential value is committed to this
repo** (CF-D5). Secret presence by name is not authentication proof.

## Deploy (owner, out-of-band)
```sh
cp wrangler.example.toml wrangler.toml
wrangler secret put GH_DISPATCH_TOKEN   # paste the fine-grained Actions-write PAT
wrangler deploy
```

## Owner post-merge actions (not performed by any agent)
1. Mint a fresh fine-grained PAT (repo `dwats250/cuttingboard`, Actions
   read/write only).
2. Safe invalid-ref authorization probe with the valid dispatch schema:
   expected HTTP 422 (authenticated, ref invalid). 401/403 means
   authentication/access is still unresolved.
3. Rebind `GH_DISPATCH_TOKEN` and deploy this reviewed source/config.
4. Observe the next valid cron: Worker log `dispatch ACCEPTED status=204` plus
   the correlated GitHub `workflow_dispatch` run; then require downstream
   delivery proof (`_execute_notify_run` entered, fresh hourly artifacts,
   Telegram outcome, publish-branch `last_hourly_slot` updated, Pages deployed).
5. Confirm a Friday fire and the Sunday 23:30 UTC `mode=sunday` dispatch as
   the calendar supplies them.

## Coordination (all GitHub-native; no persisted state)
- Duplicate CF OPEN dispatch -> serialized by the dedicated OPEN concurrency
  group (`queue: max`, non-evicting); the first completed successful OPEN
  satisfies the slot, later ones no-op (`check_open_slot_satisfied.py`).
- Duplicate hourly dispatch -> absorbed by slot dedup
  (`cuttingboard/notifications/hourly_slot.py`).
- A rejected/missing dispatch is NOT covered by anything; the GitHub liveness
  probe makes the resulting starvation visible on its next arrival.

## Testing
`tests/test_worker_clock_gate.py` executes the production `resolveSlot()` over
a both-season instant table (Mon/Fri boundaries, weekend rejection, Sunday
23:30 UTC route, adjacent-minute rejection) and the production `scheduled()`
handler under Node with a stubbed `fetch` (204 / 401 / 403 / 422 / 500 /
missing secret / network error), asserting bounded status logging and no
credential, header, or body leakage. It also parses `wrangler.example.toml`
to pin the exact cron set and the observability block.
