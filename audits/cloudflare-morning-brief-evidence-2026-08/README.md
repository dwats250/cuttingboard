# CF-E2 diagnostic capture -- hardened staging (planning evidence, non-production)

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

The harness is deliberately locked to this single campaign date. It validates
the date, weekday, and selected PT window both before provider access and after
the provider response. A capture that starts or completes outside its window
refuses with exit 3 and writes no evidence. A later date requires a reviewed
source change; there is no capture CLI override.

## How to run

From the repo root, in an environment where `yfinance` is installed and has
network egress to the quote provider:

```
python3 audits/cloudflare-morning-brief-evidence-2026-08/cf_e2_capture.py --slot premarket   # ~6:00 PT
python3 audits/cloudflare-morning-brief-evidence-2026-08/cf_e2_capture.py --slot open         # ~6:32 PT
```

Explicit `--slot` chooses the intended observation but does not bypass the
authorization guard. `--slot auto` (the default) selects the matching window.
Every mode refuses outside the authorized date/window with exit 3 and writes
nothing.

## Discipline (guaranteed by the harness)

- **No credentials** used or emitted (public yfinance quote path).
- **No fabricated values.** Provider/runtime failure is written as
  `UNAVAILABLE` with its reason and exits non-zero, but only while the capture
  remains inside its authorized window. Absence of a bar at ~6:32 is itself
  real evidence and is recorded as `ABSENT`.
- Writes exactly one timestamped JSON evidence file per run into this folder,
  with UTC + PT provenance and the provider field path. Touches nothing else.

## Evidence outcomes

Premarket evidence preserves selected raw values from both `Ticker.fast_info`
and `Ticker.info`. A difference between `last_price` and `previous_close` is
recorded but is explicitly not classification evidence.

- `status: OK`, `classification: PROVIDER_IDENTIFIED_PREMARKET` requires the
  provider itself to report `marketState=PRE`, a positive `preMarketPrice`, and
  a valid `preMarketTime` on the authorized date within the US premarket
  session, plus a valid previous close. The derived displacement uses that
  provider-labeled premarket price.
- `status: INCONCLUSIVE`, `classification: INCONCLUSIVE` means those provider
  session/timestamp semantics were insufficient. Raw observations and the
  exact reason remain in the artifact for owner inspection.
- `status: UNAVAILABLE` is reserved for provider/runtime acquisition failure.

Each requested OPEN bar has an independent `outcome`:

- `PRESENT`: exact timestamp found and finite positive Open/Close values parsed.
- `ABSENT`: no row for the exact timestamp was returned.
- `UNPARSEABLE`: a matching row was malformed or duplicated. Raw/error detail
  remains visible, and the overall record is `status: INVALID`, never `OK`.

## Behavior checks

From the repo root:

```
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest \
  audits/cloudflare-morning-brief-evidence-2026-08/test_cf_e2_capture.py \
  -q -p no:cacheprovider
```

These tests inject time only in-process; the ordinary capture CLI has no clock
or authorization bypass.

## After capture

The two JSON evidence files are the CF-E2 deliverable. They feed the CF
MATERIAL packet (with CF-E1 trigger-path evidence and the CF-D rulings) and
resolve **CF-D1b**. Do not draft the CF MATERIAL packet or request Gate A until
CF-E1 + CF-E2 evidence and the owner rulings are all in hand.
