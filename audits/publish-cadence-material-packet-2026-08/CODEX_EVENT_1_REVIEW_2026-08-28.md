# Codex Event-1 review — publish cadence MATERIAL packet (Lane B)

```
GOV-2 sec2 step 3 artifact. Reviewed packet revision: 000b13a7c2172fabd211ea3c87cf54bc28f48222
Invocation: codex exec -s read-only, prompt via stdin; captured verbatim 2026-08-28.
VERDICT: DESIGN INCOMPLETE (findings F1-F8 as numbered 1-8 below).
```

---

VERDICT: DESIGN INCOMPLETE — the packet omits the cross-workflow coordination boundary created when the punctual daily pipeline, the existing 06:00 hourly alert, and the existing 06:30 GitHub heartbeat overlap. It also treats start-time slot reassignment and post-send dedup persistence as if they guaranteed one delivery per intended cadence slot; the code does not provide that guarantee.

Review head verified: `000b13a7c2172fabd211ea3c87cf54bc28f48222`.

1. **MATERIAL-BOUNDARY — The target design creates peer-clock and cross-workflow races that sec2/sec5 do not enumerate.**

   The packet dispatches the daily OPEN/live pipeline at 06:00 PT while retaining the hourly `(6,0)` slot ([packet:108-123](/home/dustin/Projects/cuttingboard/audits/publish-cadence-material-packet-2026-08/PUBLISH_CADENCE_MATERIAL_PACKET_2026-08-28.md:108)). The hourly workflow already fires at both UTC offsets for 06:00 and 06:30 PT ([hourly_alert.yml:3-19](/home/dustin/Projects/cuttingboard/.github/workflows/hourly_alert.yml:3)), with only per-hourly-workflow serialization ([hourly_alert.yml:21-28](/home/dustin/Projects/cuttingboard/.github/workflows/hourly_alert.yml:21)). Consequently:

   - At 06:00, the CF daily pipeline and existing hourly path can both send Telegram independently. Daily uses content-state dedup ([runtime/__init__.py:1060-1089](/home/dustin/Projects/cuttingboard/cuttingboard/runtime/__init__.py:1060)); hourly sends through a separate path and slot store ([runtime/__init__.py:659-692](/home/dustin/Projects/cuttingboard/cuttingboard/runtime/__init__.py:659), [alert_runner.py:92-111](/home/dustin/Projects/cuttingboard/cuttingboard/alert_runner.py:92)). There is no cross-path notification dedup.
   - At 06:30, CF and the existing GitHub 06:30 cron fire nominally together. That is a same-slot peer-clock race, not the claimed Worker “front-run” followed by a delayed fallback. It recreates the exact topology rejected for OPEN/live in the binding ruling: preferred CF clock and GitHub resilience fallback must not race at the same instant ([DECISIONS.md:403-416](/home/dustin/Projects/cuttingboard/docs/DECISIONS.md:403)).
   - Both the daily and hourly workflows fully overwrite generated `ui/` artifacts; concurrent publish retries preserve audit deltas but explicitly accept last-writer overwrite of generated UI/regime state ([ci_push_artifacts.sh:5-19](/home/dustin/Projects/cuttingboard/tools/ci_push_artifacts.sh:5), [ci_push_artifacts.sh:97-115](/home/dustin/Projects/cuttingboard/tools/ci_push_artifacts.sh:97)). Pages then triggers on both workflow completions ([pages.yml:3-16](/home/dustin/Projects/cuttingboard/.github/workflows/pages.yml:3)).

   Missing boundary: define ownership and fallback timing for the 06:00 daily-vs-hourly overlap and 06:30 CF-vs-GitHub overlap, including which notification and generated dashboard is authoritative. This requires a producer-to-final-consumer inventory refresh under GOV-2 §6.

2. **CORRECTNESS — The `(6,45)` slot-resolution analysis admits a missed 06:30 delivery, not “one send per slot.”**

   `alert_runner` resolves the slot from the wall clock when the Python process starts, after checkout, Python setup, package installation, and publish-state restore ([hourly_alert.yml:47-107](/home/dustin/Projects/cuttingboard/.github/workflows/hourly_alert.yml:47), [alert_runner.py:68-74](/home/dustin/Projects/cuttingboard/cuttingboard/alert_runner.py:68)). `routine_pt_slot` selects the latest eligible configured slot at or before that start time ([hourly_slot.py:52-76](/home/dustin/Projects/cuttingboard/cuttingboard/notifications/hourly_slot.py:52)).

   With `(6,45)` added:

   - A 06:30 dispatch whose runner reaches `alert_runner` at 06:44 is labeled 06:30.
   - The same dispatch reaching it at 06:45 is labeled 06:45.
   - The real 06:45 arrival then suppresses as the same slot.

   Thus the 06:30 owner slot receives zero delivery, while 06:45 receives one delivery based on the delayed 06:30 invocation. The packet itself describes this reassignment but incorrectly concludes it is “one send per slot” ([packet:115-123](/home/dustin/Projects/cuttingboard/audits/publish-cadence-material-packet-2026-08/PUBLISH_CADENCE_MATERIAL_PACKET_2026-08-28.md:115)). It is one send for the later dedup key, not one send for each intended cadence slot.

   A read-only simulation of the proposed set confirmed the actual mapping: `06:30→06:30`, `06:44→06:30`, `06:45→06:45`, `06:46→06:45`, `06:55→06:45`.

3. **CORRECTNESS — Existing hourly dedup does not guarantee exactly one send after a successful transport.**

   Hourly Telegram delivery happens first ([runtime/__init__.py:688-692](/home/dustin/Projects/cuttingboard/cuttingboard/runtime/__init__.py:688)). Slot persistence occurs substantially later, after artifact and market-map work ([runtime/__init__.py:734-769](/home/dustin/Projects/cuttingboard/cuttingboard/runtime/__init__.py:734)), and persistence errors are caught and swallowed ([runtime/__init__.py:770-777](/home/dustin/Projects/cuttingboard/cuttingboard/runtime/__init__.py:770)). Cross-run visibility requires the resulting file to survive the later commit and push sequence ([hourly_alert.yml:177-216](/home/dustin/Projects/cuttingboard/.github/workflows/hourly_alert.yml:177)).

   Therefore a transport-success followed by slot-save failure, readiness failure, commit failure, or publish failure allows the queued cron/CF twin to restore the old slot and send again. Serialization prevents simultaneous sends; it does not make notification delivery and persisted dedup state atomic.

   The packet’s assertion that the second arrival is always a no-op ([packet:98-104](/home/dustin/Projects/cuttingboard/audits/publish-cadence-material-packet-2026-08/PUBLISH_CADENCE_MATERIAL_PACKET_2026-08-28.md:98)) and its requested “exactly one send” proof ([packet:184-191](/home/dustin/Projects/cuttingboard/audits/publish-cadence-material-packet-2026-08/PUBLISH_CADENCE_MATERIAL_PACKET_2026-08-28.md:184)) overstate the existing guarantee. Validation must cover successful-send/failing-persistence and successful-send/failing-publish cases and state the intended retry/duplicate policy.

4. **MATERIAL-BOUNDARY — The Worker PT-gate contract is unspecified and does not simply “honor” the binding time-basis ruling.**

   The current Worker has no PT gate; it maps the received UTC cron string directly to one slot ([index.js:22-38](/home/dustin/Projects/cuttingboard/workers/cuttingboard-clock/src/index.js:22)). The proposed design says it will compute the “current PT wall-clock” and match a “slot’s PT window,” but does not define:

   - Whether the authority timestamp is `event.scheduledTime` or handler execution time.
   - Exact window bounds and inclusivity.
   - Behavior when Worker execution is delayed across a minute/window boundary.
   - How shared UTC triggers are represented—for example, `14:00Z` is the winter twin for 06:00 and the summer primary for 07:00.
   - Whether a delayed first twin can overlap the second twin’s acceptance window.

   Exact punctual dual-cron firing gives one match in ordinary PST and PDT regimes, and the transitions occur on Sunday outside weekday cadence. But zero/two dispatches under delayed handler execution cannot be ruled out without the missing timestamp/window contract.

   Moreover, the binding 2026-08-11 ruling says trigger/window mechanics are UTC-anchored and PT is authoritative for trading-date identity ([DECISIONS.md:419-422](/home/dustin/Projects/cuttingboard/docs/DECISIONS.md:419)). A PT eligibility gate changes the window basis; it may be a reasonable new direction, but it requires an explicit superseding/extension ruling. Packet sec4’s claim that it honors the ruling “by construction” is unsound ([packet:125-140](/home/dustin/Projects/cuttingboard/audits/publish-cadence-material-packet-2026-08/PUBLISH_CADENCE_MATERIAL_PACKET_2026-08-28.md:125)).

5. **CORRECTNESS — Request-cost arithmetic mixes logical calls, provider requests, and Cboe requests.**

   The current maximum first-attempt hourly logical operations are:

   - 23 base-universe quote fetches: the configured universe is 7 macro + 3 indices + 6 commodities + 7 high-beta symbols ([config.py:258-265](/home/dustin/Projects/cuttingboard/cuttingboard/config.py:258), [ingestion.py:69-80](/home/dustin/Projects/cuttingboard/cuttingboard/ingestion.py:69)).
   - 2 observe-only quote fetches on a healthy hourly run ([config.py:267-274](/home/dustin/Projects/cuttingboard/cuttingboard/config.py:267), [runtime/__init__.py:783-789](/home/dustin/Projects/cuttingboard/cuttingboard/runtime/__init__.py:783)).
   - Up to 23 OHLCV downloads when all base quotes validate and the cache is cold ([derived.py:47-68](/home/dustin/Projects/cuttingboard/cuttingboard/derived.py:47)).
   - 1 Cboe GEX invocation ([hourly_alert.yml:141-150](/home/dustin/Projects/cuttingboard/.github/workflows/hourly_alert.yml:141)).

   That is up to **48 yfinance logical fetches + 1 Cboe invocation = 49 total logical provider operations**, not “49 yfinance + 1 Cboe.” The packet’s `~534 yfinance + 9 Cboe` total is produced by counting the Cboe operation inside the hourly 49 and then labeling all 49 as yfinance ([packet:84-89](/home/dustin/Projects/cuttingboard/audits/publish-cadence-material-packet-2026-08/PUBLISH_CADENCE_MATERIAL_PACKET_2026-08-28.md:84), [packet:168-180](/home/dustin/Projects/cuttingboard/audits/publish-cadence-material-packet-2026-08/PUBLISH_CADENCE_MATERIAL_PACKET_2026-08-28.md:168)).

   These are not verified HTTP-request counts: quote and OHLCV operations retry up to three times ([ingestion.py:293-327](/home/dustin/Projects/cuttingboard/cuttingboard/ingestion.py:293), [ingestion.py:383-418](/home/dustin/Projects/cuttingboard/cuttingboard/ingestion.py:383)), and a yfinance operation can make more than one underlying HTTP request. Cache savings are “up to 23 logical OHLCV fetches per healthy warm run,” not an unconditional 23. The validation plan needs measured/instrumented logical-call and retry/cache-hit accounting, with wire-request counts labeled unavailable unless actually captured.

6. **MATERIAL-BOUNDARY — The claimed “full participant set,” falsifier, and FILES cone are incomplete.**

   The proposed falsifier searches only `force-slot|ALLOWED_PT_SLOTS|routine_pt_slot|CB-SLOT` ([packet:164-166](/home/dustin/Projects/cuttingboard/audits/publish-cadence-material-packet-2026-08/PUBLISH_CADENCE_MATERIAL_PACKET_2026-08-28.md:164)). It cannot discover several decisive participant classes:

   - Daily content dedup: `cuttingboard/notifications/state.py`.
   - Actual hourly send and post-send slot persistence: `cuttingboard/runtime/__init__.py`.
   - Cross-workflow restore/publish/race behavior: `tools/ci_restore_publish_state.sh` and `tools/ci_push_artifacts.sh`.
   - The third Pages-triggering writer: `.github/workflows/macro_awareness.yml`.
   - Cache semantics and logical request producers: `cuttingboard/config.py`, `cuttingboard/ingestion.py`, and `cuttingboard/derived.py`.
   - GEX producer/isolation contract: `tools/gex_snapshot.py` and its exact workflow guards.
   - Daily/hourly generated-UI ownership and Pages deployment behavior.

   The FILES estimate also omits the likely home for the mandated hourly failure/race regressions, [test_hourly_slot_idempotency.py](/home/dustin/Projects/cuttingboard/tests/test_hourly_slot_idempotency.py:1). There is currently no Worker test/package surface at all—the Worker directory contains only the source, README, and example TOML—yet sec7 requires table-driven tests of the new gate. A mirrored Python table would not exercise the JavaScript decision actually deployed. The cone must identify an executable Worker-test surface or explicitly include the production JS gate in a test harness.

7. **MATERIAL-BOUNDARY — The ruling questions omit the decisions needed to close the discovered boundary.**

   Before direction can be soundly ruled, sec11 needs material questions covering:

   - Whether the existing 06:00 hourly notification remains when the daily board moves to 06:00, and which notification/dashboard owns that instant.
   - Whether the existing 06:30 GitHub cron is retimed into a delayed fallback, retained as a peer clock, or removed for the CF-only first slice.
   - Whether a late 06:30 run is allowed to consume the 06:45 identity, thereby losing the 06:30 owner slot.
   - The authoritative Worker timestamp/window basis and whether that supersedes the UTC-window ruling.
   - The accepted behavior after notification success but dedup-persistence/publish failure.
   - Whether request ceilings mean logical provider operations, retry attempts, or measured HTTP requests.

   Q5’s “separate micro-slice” alternative must also be reclassified rather than assumed: it touches a high-risk workflow and a shared cross-run cache seam, and MATERIAL work is ineligible for MICRO ([GOV-2:51-63](/home/dustin/Projects/cuttingboard/docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:51)).

8. **RECOMMENDED — “UNDEPLOYED” is repository-recorded status, not independently verified external state.**

   The repository consistently records the Worker as undeployed and transport-only ([README.md:1-22](/home/dustin/Projects/cuttingboard/workers/cuttingboard-clock/README.md:1), [index.js:1-15](/home/dustin/Projects/cuttingboard/workers/cuttingboard-clock/src/index.js:1)); DECISIONS records CF-E1/E2 as authorized but incomplete ([DECISIONS.md:363-383](/home/dustin/Projects/cuttingboard/docs/DECISIONS.md:363)). That verifies the canonical repository status. No Cloudflare-account evidence was available in this read-only review, so the packet should say “repository-recorded as undeployed; no CF-E1 completion evidence” rather than claim live external status was independently verified.

Claims that held:

- `hourly_alert.yml` manual `workflow_dispatch` has no inputs and always adds `--force-slot` ([hourly_alert.yml:19](/home/dustin/Projects/cuttingboard/.github/workflows/hourly_alert.yml:19), [hourly_alert.yml:101-107](/home/dustin/Projects/cuttingboard/.github/workflows/hourly_alert.yml:101)).
- `ALLOWED_PT_SLOTS` is exactly the nine listed slots, and `routine_pt_slot` uses latest-eligible-within-25-minutes semantics ([hourly_slot.py:25-36](/home/dustin/Projects/cuttingboard/cuttingboard/notifications/hourly_slot.py:25), [hourly_slot.py:52-76](/home/dustin/Projects/cuttingboard/cuttingboard/notifications/hourly_slot.py:52)).
- `hourly_alert.yml` currently contains no `actions/cache`.
- A 06:00 PT OPEN/live dispatch satisfies the existing first-success dispatch predicate in both regimes: 13:00Z in PDT and 14:00Z in PST are both at or after 12:55Z and before 09:30 ET ([check_open_slot_satisfied.py:48-52](/home/dustin/Projects/cuttingboard/scripts/check_open_slot_satisfied.py:48), [check_open_slot_satisfied.py:141-175](/home/dustin/Projects/cuttingboard/scripts/check_open_slot_satisfied.py:141)).
- CF-D3 really authorizes two post-open dispatches, OPEN and OPEN+1 ([DECISIONS.md:351-362](/home/dustin/Projects/cuttingboard/docs/DECISIONS.md:351)).
- Exact-SHA proof, revision drift, runtime readiness, freshness/readiness, publish ownership, and daily notification-ownership guards are not directly weakened by the proposed text. The missing problem is coordination around them, not removal of those guards.

Validation performed: the targeted existing slot, first-success, and idempotency suites passed, `98 passed`. Those tests validate the current implementation, not the proposed Worker gate or the new 06:45/cross-workflow race behavior.

Independence/read-only attestation: I did not author the packet, made no repository changes, created no review artifact, and performed no implementation. The checkout remained clean at the exact review head before and after review. GitNexus was indexed against a different temporary checkout and an older SHA; refreshing it would have written index artifacts contrary to the read-only charge, so no graph-derived claim was treated as evidence.


