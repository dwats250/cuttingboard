// Cloudflare Worker — external cron trigger for cuttingboard hourly_alert (PRD-149).
//
// On each scheduled tick, POST to GitHub's workflow_dispatch API to fire
// .github/workflows/hourly_alert.yml on main. The workflow's `Run hourly alert`
// step checks inputs.scheduler == 'external_cron' and routes through the
// PRD-141 slot dedup gate (does NOT pass --force-slot), so redundant firings
// alongside the GH-native cron collapse to one Telegram alert per PT hour.
//
// Secrets (set via `wrangler secret put GITHUB_TOKEN`):
//   GITHUB_TOKEN — fine-grained PAT scoped to dwats250/cuttingboard with
//                  "Repository permissions → Actions: Read and write".
//
// Cron schedule lives in wrangler.toml [triggers].crons.

const REPO = 'dwats250/cuttingboard';
const WORKFLOW = 'hourly_alert.yml';
const REF = 'main';
const DISPATCH_URL = `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`;

async function dispatch(env) {
  const resp = await fetch(DISPATCH_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'cuttingboard-external-trigger',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ref: REF,
      inputs: { scheduler: 'external_cron' },
    }),
  });
  // GH returns 204 No Content on success. Anything else = log + give up
  // for this tick (next cron tick retries naturally).
  if (resp.status !== 204) {
    const body = await resp.text().catch(() => '<unreadable>');
    console.error(`[external_trigger] dispatch failed: status=${resp.status} body=${body}`);
    return false;
  }
  console.log(`[external_trigger] dispatched ${WORKFLOW}@${REF} scheduler=external_cron`);
  return true;
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(dispatch(env));
  },
  // Optional fetch handler so the Worker URL responds for manual smoke tests.
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return new Response('cuttingboard external trigger — POST to dispatch\n', { status: 200 });
    }
    const ok = await dispatch(env);
    return new Response(ok ? 'dispatched\n' : 'dispatch failed; check logs\n', {
      status: ok ? 200 : 502,
    });
  },
};
