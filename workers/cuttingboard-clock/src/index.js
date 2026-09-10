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
// PRD-319 R1 / owner time-basis extension ruling (2026-08-28): UTC triggers;
// PT from event.scheduledTime (America/Los_Angeles) is authoritative for slot
// eligibility and identity; handler execution time is never authority. Dual
// UTC triggers cover both DST offsets -- at most one resolves per instant.
// PRE (12:50Z) is the one UTC-anchored weekday row (cache warm-up, not PT
// cadence).
//
// Completion PR (2026-09-09): this Worker is the AUTHORITATIVE routine clock.
// The GitHub schedule is a liveness PROBE only (never an execution fallback),
// so a REJECTED / ERROR dispatch here is a MISSED slot until the owner acts.
// The Sunday session (23:30 UTC, existing pipeline mode=sunday, no slot) is
// dispatched from here as well (owner ruling "Wire up Sunday session to
// cloudflare"). Logging is bounded transport metadata: workflow, slot/mode,
// scheduledTime, HTTP status, error class. Never the credential, request
// headers, or response bodies.
// Credential: Actions-write-only token in the GH_DISPATCH_TOKEN secret.

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
  const utcDay = d.getUTCDay();
  // Sunday session: UTC-anchored 23:30 Sunday, year-round (matches its SUN
  // cron). Existing pipeline mode=sunday contract: no slot input.
  if (utcDay === 0 && d.getUTCHours() === 23 && d.getUTCMinutes() === 30) {
    return {
      workflow: PIPELINE_WORKFLOW,
      inputs: { mode: "sunday", source: SOURCE },
    };
  }
  // PRE: UTC-anchored warm-up, weekday-gated in UTC (matches its MON-FRI cron).
  if (d.getUTCHours() === 12 && d.getUTCMinutes() === 50) {
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

// Safe log identity for one resolution: workflow + slot (or mode for the
// slot-less Sunday session) + the authoritative scheduledTime. No secrets.
function dispatchIdentity(workflow, inputs, scheduledTimeMs) {
  const slot = inputs.slot !== undefined ? `slot=${inputs.slot}` : `mode=${inputs.mode}`;
  return `workflow=${workflow} ${slot} scheduledTime=${new Date(scheduledTimeMs).toISOString()}`;
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
    const identity = dispatchIdentity(workflow, inputs, event.scheduledTime);

    const token = env.GH_DISPATCH_TOKEN;
    if (!token) {
      // A missing credential is a DISPATCH failure: the slot is MISSED (no
      // GitHub execution fallback exists). Owner action: bind the secret.
      console.error(
        `cuttingboard-clock: dispatch REJECTED reason=missing_secret ${identity}`,
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
        console.log(`cuttingboard-clock: dispatch ACCEPTED status=204 ${identity}`);
      } else {
        // Bounded metadata only: the response body is never logged (it can
        // echo request material). 401/403 = credential/access problem;
        // 422 = schema/ref rejection; anything else = GitHub-side failure.
        console.error(
          `cuttingboard-clock: dispatch REJECTED status=${resp.status} ${identity}`,
        );
      }
    } catch (err) {
      // Network/transport error contacting GitHub -> dispatch failure. Log the
      // error CLASS only; the message can carry URL/header material.
      const cls = err && err.name ? err.name : typeof err;
      console.error(`cuttingboard-clock: dispatch ERROR error=${cls} ${identity}`);
    }
    // Dispatch acceptance != execution success != observation validity.
    // Duplicates are absorbed by first-success (pipeline) / slot dedup
    // (hourly). A rejected or errored dispatch is NOT retried and is NOT
    // covered by any GitHub schedule: the liveness probe surfaces the gap.
  },
};
