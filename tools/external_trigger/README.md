# cuttingboard external trigger (PRD-149)

Cloudflare Worker that fires `.github/workflows/hourly_alert.yml` via the GitHub `workflow_dispatch` API on a coarse weekday UTC heartbeat (every 15 minutes, 12:00–21:45 UTC). Decoupling the trigger from GitHub's own cron service protects the hourly alert path from GH Actions scheduler outages (cf. the 2026-05-19 ~18h scheduler silence that motivated this PRD).

The Worker does **not** mirror the exact cron list in `hourly_alert.yml` — Cloudflare's free plan caps a Worker at 5 cron triggers, and the PRD-141 slot dedup gate (one alert per PT hour) already collapses overlapping firings between the GH-native schedule and this Worker. A coarse heartbeat is sufficient: every dispatched run consults the dedup gate and either sends (new PT slot) or suppresses (slot already alerted).

## How it works

- `worker.js` exposes a `scheduled` handler that POSTs to `POST /repos/dwats250/cuttingboard/actions/workflows/hourly_alert.yml/dispatches` with body `{"ref":"main","inputs":{"scheduler":"external_cron"}}`.
- The workflow's `Run hourly alert` step sees `inputs.scheduler == "external_cron"` and runs `python -m cuttingboard.alert_runner` **without** `--force-slot` — so the PRD-141 slot dedup gate enforces one alert per PT hour even if the GH-native cron also fires.
- Operator manual dispatch (`gh workflow run hourly_alert.yml` with no inputs) defaults to `scheduler == operator` and keeps the `--force-slot` immediate-send behavior.

## One-time deploy

Prerequisite: a Cloudflare account. Free tier covers the firing rate (~20/weekday).

```sh
# 1. Install wrangler globally (or use npx)
npm i -g wrangler

# 2. Authenticate
wrangler login

# 3. From this directory, set the GitHub PAT as a Worker secret
cd tools/external_trigger
wrangler secret put GITHUB_TOKEN
# (paste the PAT when prompted)

# 4. Deploy
wrangler deploy
```

After deploy, `wrangler tail` streams the Worker's logs (look for `[external_trigger] dispatched` per tick).

## GitHub PAT setup

Use a **fine-grained PAT** scoped to this repo:

- **Repository access**: `dwats250/cuttingboard` only.
- **Repository permissions** → **Actions**: `Read and write` (required to call the `workflow_dispatch` endpoint).
- **Expiration**: 1 year (rotate annually; PAT expiry is the most likely silent failure mode for this Worker).

Classic PAT alternative: `actions:write` scope on `dwats250/cuttingboard`. Fine-grained preferred for blast radius.

Store the PAT only in Cloudflare via `wrangler secret put GITHUB_TOKEN`. Do not commit it.

## Verifying it fires

After deploy:

```sh
# Watch the Worker's logs in real time
wrangler tail

# In another shell, check that GH actually received dispatches
gh run list --workflow hourly_alert.yml --limit 5
# Look for event=workflow_dispatch entries on the canonical UTC times.
```

Manual smoke test (one-shot dispatch from the Worker's public URL):

```sh
curl -X POST https://cuttingboard-external-trigger.<your-subdomain>.workers.dev/
# Returns "dispatched\n" on success, "dispatch failed; check logs\n" otherwise.
```

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Worker fires, GH API returns 401 | `GITHUB_TOKEN` missing, expired, or wrong scope | `wrangler secret put GITHUB_TOKEN` with a fresh fine-grained PAT |
| Worker fires, GH API returns 404 | Repo renamed, default branch changed, or workflow file deleted | Update `REPO`/`REF`/`WORKFLOW` constants in `worker.js`, redeploy |
| Worker fires, GH API returns 5xx | GitHub outage | No action; next cron tick retries |
| Worker doesn't fire at all | CF cron triggers disabled or wrangler.toml `[triggers].crons` empty | Check `wrangler tail`; redeploy from this directory |
| Alert sent twice for same PT hour | PRD-141 dedup gate not active (e.g. `--force-slot` accidentally re-introduced) | Check `.github/workflows/hourly_alert.yml` `Run hourly alert` conditional |
| Alert not sent when GH cron is silent | Either the Worker didn't fire OR the dispatched run failed at readiness/contract gate | Check `wrangler tail` for dispatch log, then `gh run view <id>` for the workflow run |

## What this Worker does NOT do

- It does not produce or modify any cuttingboard pipeline artifact.
- It does not call any cuttingboard module directly. It only fires the workflow that calls them.
- It does not retry within a single tick. Failed dispatches wait for the next scheduled tick.
- It does not monitor itself. v1 relies on missed Telegram alerts as the user-visible failure signal.
