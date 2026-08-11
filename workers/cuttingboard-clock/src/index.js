// PRD-299: Cloudflare clock for the Cuttingboard pipeline. UNDEPLOYED, transport-only.
//
// Responsibilities (and ONLY these):
//   - on a scheduled (cron) event, resolve PRE or OPEN;
//   - POST a workflow_dispatch to cuttingboard.yml on `main` with {mode, slot, source};
//   - log accepted (HTTP 204) vs rejected dispatch.
//
// Explicitly NOT here: market logic, board-freshness logic, latest_run
// interpretation, dedup/idempotency state, KV / Durable Objects. Cloudflare
// dispatch acceptance is ATTEMPT AUTHORIZATION only -- never observation or
// publish success (the GitHub executor owns those). First-success coordination
// lives in the GitHub workflow (scripts/check_open_slot_satisfied.py), not here.
//
// Credential: a fine-grained GitHub token, Actions: write only, stored as the
// Worker secret GH_DISPATCH_TOKEN. No credential value is committed to the repo.

const REPO = "dwats250/cuttingboard";
const WORKFLOW_FILE = "cuttingboard.yml";
const REF = "main";
const SOURCE = "cloudflare-worker";

// Cloudflare cron triggers are UTC (no timezone support), mirroring the
// workflow's UTC crons. The GitHub crons remain the delayed fallback.
//   12:50 UTC -> PRE  (prefetch warm-up; no first-success suppression this slice)
//   13:00 UTC -> OPEN (preferred punctual clock; GH 13:05 fallback covers a miss)
const CRON_SLOT = {
  "50 12 * * 1-5": { slot: "PRE", mode: "prefetch" },
  "0 13 * * 1-5": { slot: "OPEN", mode: "live" },
};

export default {
  async scheduled(event, env, _ctx) {
    const mapping = CRON_SLOT[event.cron];
    if (!mapping) {
      console.log(`cuttingboard-clock: no slot mapped for cron ${event.cron}; no dispatch`);
      return;
    }
    const { slot, mode } = mapping;

    const token = env.GH_DISPATCH_TOKEN;
    if (!token) {
      // A missing credential is a DISPATCH failure only, never an observation
      // failure. The GitHub fallback cron still covers the slot.
      console.error(`cuttingboard-clock: GH_DISPATCH_TOKEN secret missing; dispatch REJECTED slot=${slot}`);
      return;
    }

    const url = `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`;
    const body = JSON.stringify({ ref: REF, inputs: { mode, slot, source: SOURCE } });
    try {
      const resp = await fetch(url, {
        method: "POST",
        headers: {
          Accept: "application/vnd.github+json",
          Authorization: `Bearer ${token}`,
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "cuttingboard-clock",
          "Content-Type": "application/json",
        },
        body,
      });
      if (resp.status === 204) {
        console.log(`cuttingboard-clock: dispatch ACCEPTED slot=${slot} mode=${mode} cron=${event.cron}`);
      } else {
        const text = await resp.text();
        console.error(`cuttingboard-clock: dispatch REJECTED status=${resp.status} slot=${slot} body=${text}`);
      }
    } catch (err) {
      // Network/transport error contacting GitHub -> dispatch failure only.
      console.error(`cuttingboard-clock: dispatch ERROR slot=${slot}: ${err}`);
    }
    // Dispatch acceptance != execution success != observation validity != board
    // current. The GH fallback cron (5 13 * * 1-5, ~13:05 UTC) covers a
    // missed/failed CF OPEN dispatch; duplicate CF dispatches are deduped by the
    // GitHub-side first-success proof + the dedicated OPEN concurrency group.
  },
};
