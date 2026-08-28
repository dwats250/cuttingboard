// PRD-299 / PRD-319: Cloudflare clock for the Cuttingboard pipeline.
// Transport-only. Deploy remains owner-held (CF-D5 / CF-E1).
//
// Responsibilities (and ONLY these):
//   - on a scheduled (cron) event, resolve the intended slot from
//     event.scheduledTime via resolveSlot() below;
//   - POST a workflow_dispatch for that slot; log accepted vs rejected.
//
// Explicitly NOT here: market logic, board-freshness logic, dedup/idempotency
// state, KV / Durable Objects. Dispatch acceptance is ATTEMPT AUTHORIZATION
// only. First-success coordination lives in the GitHub pipeline workflow;
// hourly slot dedup lives in cuttingboard/notifications/hourly_slot.py.
//
// PRD-319 R1 / owner time-basis extension ruling (2026-08-28): UTC remains the
// trigger basis; Pacific Time resolved from event.scheduledTime using
// America/Los_Angeles is authoritative for weekday slot ELIGIBILITY and
// intended slot IDENTITY. Handler execution time is never scheduling
// authority -- a delayed handler can neither miss its own slot nor drift into
// another, because scheduledTime is fixed by the platform. Dual UTC triggers
// cover both DST offsets; for any scheduledTime the PT lookup makes AT MOST
// ONE row eligible, so the off-season twin no-ops here. PRE (12:50Z) is the
// one UTC-anchored row: a cache warm-up, not a PT cadence slot.
//
// Credential: a fine-grained GitHub token, Actions: write only, stored as the
// Worker secret GH_DISPATCH_TOKEN. No credential value is committed.

const REPO = "dwats250/cuttingboard";
const PIPELINE_WORKFLOW = "cuttingboard.yml";
const HOURLY_WORKFLOW = "hourly_alert.yml";
const REF = "main";
const SOURCE = "cloudflare-worker";

// PT cadence slots the hourly workflow owns (06:00 belongs to the pipeline).
const HOURLY_PT_SLOTS = new Set([
  "06:30", "06:45", "07:00", "08:00", "09:00",
  "10:00", "11:00", "12:00", "13:00",
]);

// Pure: epoch ms -> {weekday, hhmm} in America/Los_Angeles.
function ptWallClock(scheduledTimeMs) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    hour12: false,
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).formatToParts(new Date(scheduledTimeMs));
  const get = (type) => parts.find((p) => p.type === type).value;
  // hour12:false can yield "24" for midnight in some ICU versions; normalize.
  const hh = get("hour") === "24" ? "00" : get("hour");
  return { weekday: get("weekday"), hhmm: `${hh}:${get("minute")}` };
}

const PT_WEEKDAYS = new Set(["Mon", "Tue", "Wed", "Thu", "Fri"]);

// Pure resolver (PRD-319 R1): scheduledTime -> exactly one dispatch or null.
// Exported for the Node test harness (tests/test_worker_clock_gate.py), which
// executes THIS production function over a both-season instant table.
export function resolveSlot(scheduledTimeMs) {
  const d = new Date(scheduledTimeMs);
  // PRE: UTC-anchored warm-up, weekday-gated in UTC (matches its 1-5 cron).
  if (d.getUTCHours() === 12 && d.getUTCMinutes() === 50) {
    const utcDay = d.getUTCDay();
    if (utcDay === 0 || utcDay === 6) return null;
    return {
      workflow: PIPELINE_WORKFLOW,
      inputs: { mode: "prefetch", slot: "PRE", source: SOURCE },
    };
  }
  const pt = ptWallClock(scheduledTimeMs);
  if (!PT_WEEKDAYS.has(pt.weekday)) return null;
  if (pt.hhmm === "06:00") {
    return {
      workflow: PIPELINE_WORKFLOW,
      inputs: { mode: "live", slot: "OPEN", source: SOURCE },
    };
  }
  if (HOURLY_PT_SLOTS.has(pt.hhmm)) {
    return {
      workflow: HOURLY_WORKFLOW,
      inputs: { kind: "routine", slot: pt.hhmm, source: SOURCE },
    };
  }
  return null;
}

export default {
  async scheduled(event, env, _ctx) {
    // scheduledTime, never event.cron and never handler wall-clock (PRD-319 R1).
    const resolution = resolveSlot(event.scheduledTime);
    if (resolution === null) {
      console.log(
        `cuttingboard-clock: no slot for scheduledTime=${new Date(event.scheduledTime).toISOString()} (off-season twin or off-cadence); no dispatch`,
      );
      return;
    }
    const { workflow, inputs } = resolution;

    const token = env.GH_DISPATCH_TOKEN;
    if (!token) {
      // A missing credential is a DISPATCH failure only, never an observation
      // failure. The GitHub fallback crons still cover the slot.
      console.error(
        `cuttingboard-clock: GH_DISPATCH_TOKEN secret missing; dispatch REJECTED workflow=${workflow} inputs=${JSON.stringify(inputs)}`,
      );
      return;
    }

    const url = `https://api.github.com/repos/${REPO}/actions/workflows/${workflow}/dispatches`;
    const body = JSON.stringify({ ref: REF, inputs });
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
        console.log(
          `cuttingboard-clock: dispatch ACCEPTED workflow=${workflow} inputs=${JSON.stringify(inputs)}`,
        );
      } else {
        const text = await resp.text();
        console.error(
          `cuttingboard-clock: dispatch REJECTED status=${resp.status} workflow=${workflow} body=${text}`,
        );
      }
    } catch (err) {
      // Network/transport error contacting GitHub -> dispatch failure only.
      console.error(`cuttingboard-clock: dispatch ERROR workflow=${workflow}: ${err}`);
    }
    // Dispatch acceptance != execution success != observation validity. The
    // delayed GitHub fallbacks cover a missed/failed CF dispatch; duplicates
    // are absorbed by first-success (pipeline) / slot dedup (hourly).
  },
};
