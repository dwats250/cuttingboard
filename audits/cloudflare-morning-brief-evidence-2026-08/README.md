# CF-E2 diagnostic capture -- staging (planning evidence, non-production)

Prepared under the 2026-08-08 execution-campaign charge (owner item 4: "Stage
the CF-E2 diagnostic harness NOW -- preparation only, no fabricated evidence,
no feature implementation, make the next valid ~6:00 / ~6:32 PT market window
execution-ready").

This folder holds the CF-E2 evidence capture for the Cloudflare / Morning Brief
planning packet
(`audits/reconciliation-2026-08/CLOUDFLARE_CLOCK_MORNING_BRIEF_PLANNING_PACKET_2026-08-08.md`,
section 3 / CF-E2 and section 14). It is NOT production code and is NOT wired
into any pipeline.

## What CF-E2 must answer (the two open provider questions)

1. **Premarket quote semantics (~6:00 PT):** does the SPY quote's last price
   reflect premarket trades, or echo the prior close? This gates **CF-D1b**
   (the premarket-displacement banner), which is deferred until this evidence
   exists.
2. **First-bar availability latency (~6:32 PT):** is the 09:30 ET (OPEN) and
   09:31 ET (OPEN+1) 1-minute bar published yet at capture time? This is the
   latency the OPEN / OPEN+1 observations depend on.

## Next valid execution window

It is Saturday evening PT as of staging (2026-08-09 UTC). The next valid market
day is **Monday 2026-08-10** (the system is holiday-unaware by design; confirm
2026-08-10 is a normal trading session before relying on the capture).

- Run 1 -- premarket: **Mon 2026-08-10, ~6:00 PT**
- Run 2 -- open:      **Mon 2026-08-10, ~6:32 PT**

Trigger times are observation intents; the observations are bar-window /
quote-snapshot defined, so a few minutes' slippage is harmless (it changes when
the capture lands, not what it records).

## How to run

From the repo root, in an environment where `yfinance` is installed and has
network egress to the quote provider:

```
python3 audits/cloudflare-morning-brief-evidence-2026-08/cf_e2_capture.py --slot premarket   # ~6:00 PT
python3 audits/cloudflare-morning-brief-evidence-2026-08/cf_e2_capture.py --slot open         # ~6:32 PT
```

`--slot auto` (the default) detects the window from the current PT time and
**refuses to run outside a capture window** (exit 3), so a mistimed run cannot
produce misleading evidence.

## Discipline (guaranteed by the harness)

- **No credentials** used or emitted (public yfinance quote path).
- **No fabricated values.** Missing/unusable data is written as `UNAVAILABLE`
  with its reason and the process exits non-zero. Absence of a bar at ~6:32 is
  itself real evidence (bar not yet published), recorded truthfully.
- Writes exactly one timestamped JSON evidence file per run into this folder,
  with UTC + PT provenance and the provider field path. Touches nothing else.

## After capture

The two JSON evidence files are the CF-E2 deliverable. They feed the CF
MATERIAL packet (with CF-E1 trigger-path evidence and the CF-D rulings) and
resolve **CF-D1b**. Do not draft the CF MATERIAL packet or request Gate A until
CF-E1 + CF-E2 evidence and the owner rulings are all in hand.
