# Codex Event-1 review — operator setup chart MATERIAL packet

```
GOV-2 sec2 step 3 artifact. Reviewed packet revision: 3a06ed6959fcb7c307952fae8585d3dbd838cf34
Invocation: codex exec -s read-only, prompt = CODEX_REVIEW_PROMPT_2026-08-28.md
(SHA pinned at dispatch; the dispatch prompt carried a malformed second SHA
"3a06ed6f59..." from a transcription slip — Codex identified it as unresolvable
and reviewed the valid dispatch SHA, which equalled git rev-parse HEAD).
Captured verbatim from codex stdout by the authoring session, 2026-08-28.
VERDICT: DESIGN INCOMPLETE.
```

---

VERDICT: DESIGN INCOMPLETE — the missing boundary is the ownership, restoration, monotonic publication, and freshness contract for the new two-producer persisted sidecar.

Reviewed commit: `3a06ed6959fcb7c307952fae8585d3dbd838cf34`.

The other SHA printed in the prompt, `3a06ed6f59fcb7c307952fae8585d3dbd838cf34`, does not resolve to an object. I used the valid dispatch SHA, which exactly matched `git rev-parse HEAD`.

1. MATERIAL-BOUNDARY — The trend-snapshot transport precedent is described incorrectly, and the new sidecar’s cross-workflow ownership race is not designed.

   - The packet says `trend_structure_snapshot.json` is restored to hourly jobs and the new carrier will use the identical mechanism: `OPERATOR_SETUP_CHART_MATERIAL_PACKET_2026-08-28.md:116-121,166-167`.
   - The hourly restore invocation does not include `logs/trend_structure_snapshot.json`: `.github/workflows/hourly_alert.yml:89-90`.
   - The daily restore invocation also omits it: `.github/workflows/cuttingboard.yml:241-247`.
   - Hourly force-stages the trend snapshot as a co-produced artifact: `.github/workflows/hourly_alert.yml:185-197`.
   - Daily force-stages all of `logs/`: `.github/workflows/cuttingboard.yml:511-530`.
   - PRD-194’s publisher deliberately full-overwrites non-audit artifacts and, after a non-fast-forward, reapplies the older run’s artifact over the new publish tip: `tools/ci_push_artifacts.sh:10-19,97-115,180-194`.
   - Therefore two overlapping daily/hourly runs can publish snapshots out of generation order. An older delayed run can overwrite a newer sidecar. The packet neither assigns a sole publisher nor provides a monotonic `generated_at`/`as_of` conflict rule.
   - This also falsifies sec5’s “exactly one consumer” boundary. Restore workflows and publish machinery are transport readers/writers that must be enumerated. Its proposed falsifier excludes `.github/workflows/` and `tests/`, yet says it will find workflow/tests: `OPERATOR_SETUP_CHART_MATERIAL_PACKET_2026-08-28.md:220-225`.
   - Required correction: enumerate renderer, both producers, both workflow restore/stage sites, and publish overlay as distinct carrier participants; then choose either one publisher or a generation-monotonic merge/overwrite rule. This is an omitted carrier/consumer class under `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:212-219`.

2. CORRECTNESS — The completed-bars rule is not correct against the actual cache.

   - The packet says the cache may contain a partial bar for “today” and directs the writer to drop every row dated the current trading day: `OPERATOR_SETUP_CHART_MATERIAL_PACKET_2026-08-28.md:154-159`.
   - The daily fetch passes `end=<current UTC date>` to yfinance, which is exclusive: `cuttingboard/ingestion.py:383-396`.
   - Cache freshness is explicitly keyed to `most_recent_completed_session_date(...)`, and the implementation says the cache holds completed sessions and “never serves stale data”: `cuttingboard/ingestion.py:147-167`.
   - Thus the claimed partial-current-day cache state is not produced by the normal fetch path. Conversely, unconditionally dropping the current trading date would discard a legitimately completed session if such a frame were supplied after the close.
   - Required correction: define completion using the existing market-session authority—e.g. retain rows whose normalized session date is no later than `most_recent_completed_session_date(generated_at)`—including timezone/index normalization. Do not define completion as merely `row.date != current trading day`.

3. CORRECTNESS — Carrier provenance and staleness semantics are incomplete.

   - The schema provides only `generated_at`, `source.mode`, provider, interval, per-symbol `as_of`, and positional bars: `OPERATOR_SETUP_CHART_MATERIAL_PACKET_2026-08-28.md:135-146`.
   - Both hourly and daily production can run with runtime `mode == "live"`; `mode` alone cannot distinguish producer path: `cuttingboard/runtime/_constants.py:26-29`, `cuttingboard/runtime/__init__.py:526-531,1493-1508`.
   - Actual daily OHLC is adjusted (`auto_adjust=True`), but that material provenance is not represented: `cuttingboard/ingestion.py:389-402`.
   - The degradation chain invokes an undefined “stale-beyond-threshold”: `OPERATOR_SETUP_CHART_MATERIAL_PACKET_2026-08-28.md:204-209`. No threshold, clock source, weekend/holiday rule, or choice between `generated_at` and per-symbol `as_of` is specified.
   - The existing dashboard staleness machinery does not automatically validate this new sidecar; it currently evaluates other timestamps and page/run age: `cuttingboard/delivery/dashboard_renderer.py:315-326,445-490,2473-2479`.
   - A freshly generated sidecar may also contain symbols with differing `as_of` values after per-symbol failures. The packet says failed symbols are omitted, but does not define whether a stale retained symbol record is legal.
   - Required correction: specify producer kind, adjusted/unadjusted basis, canonical positional column order, timestamp/session timezone, exact per-symbol validation, exact freshness threshold/calendar rule, and whether partial-symbol snapshots are accepted. Add this as a ruling question rather than leaving “stale” to implementation judgment.

4. CORRECTNESS — Two data-inventory claims overstate the present seams.

   - Both paths do call `_collect_trend_structure_history`, and the six symbol sets are exactly equal: `cuttingboard/runtime/__init__.py:778-782,1493-1508,2441-2466`; `cuttingboard/config.py:276-278`; `cuttingboard/market_map.py:19-20`.
   - However, the returned history is passed directly into the trend writer. It is not bound as a reusable local value at either seam. Adding a second writer requires explicitly collecting once and threading the same object into both writers; otherwise a second collection can repeat failed fetches and undermines the zero-new-call claim.
   - The statement that hourly maps carry “EMA zones only” is false: `OPERATOR_SETUP_CHART_MATERIAL_PACKET_2026-08-28.md:114-115`. Hourly qualification fetches candidate OHLCV at `cuttingboard/runtime/__init__.py:605-609,628-632`, passes primary-symbol frames into `build_market_map` at `:736-748`, and `market_map` derives fib levels from those bars at `cuttingboard/market_map.py:159-175,359-384`. An hourly primary-symbol candidate can therefore already carry fibs.
   - Required correction: bind one `history_by_symbol` result at each seam and pass it to both writers; qualify the hourly inventory claim as path/state dependent.

5. CORRECTNESS — The no-price degradation behavior does not carry PRD-226 as claimed.

   - The packet says invalid `current_price` reaches the existing `"Chart unavailable — no price data"` sentinel: `OPERATOR_SETUP_CHART_MATERIAL_PACKET_2026-08-28.md:204-209`.
   - `_render_level_diagram` contains that sentinel internally: `cuttingboard/delivery/dashboard_renderer.py:1760-1767`.
   - But the candidate-card caller invokes the function only when `now_price` is already valid and level context exists: `cuttingboard/delivery/dashboard_renderer.py:2141-2164`. The source documentation explicitly says an absent current price suppresses the diagram: `:1752-1758`.
   - The sentinel is therefore unreachable through the current candidate-card path. Changing suppression to a visible sentinel is a new presentation contract, not preservation of existing behavior.
   - Required correction: explicitly rule either PRD-226-compatible suppression or a deliberate new sentinel behavior, then state the matching fallback tests. The chart’s NOW anchor, entry→stop band, signed distances, locked ENTRY→LEVEL and STOP→INVALIDATION transformations otherwise preserve the PRD-226/223/304 contracts. I found no scoring, prediction, setup inference, or decision-path feedback in the proposed chart function.

6. MATERIAL-BOUNDARY — The producer FILES cone is incomplete.

   - `tests/test_ci_artifact_hygiene.py` directly asserts the exact hourly staged-artifact set, restore arguments, cross-workflow ownership, and non-clobber rules: `tests/test_ci_artifact_hygiene.py:28-54,514-595`. Any truthful implementation of finding 1 must modify this file, but sec7 omits it: `OPERATOR_SETUP_CHART_MATERIAL_PACKET_2026-08-28.md:248-259`.
   - The established runtime path convention places sidecar paths in `cuttingboard/runtime/_constants.py:44-58`, re-exports them through the runtime facade, and guards that patch surface in `tests/test_runtime_package_surface.py:43-70`. If `PRICE_BARS_PATH` follows the claimed trend-sidecar pattern, both files are also missing.
   - Full-live test harnesses explicitly redirect `TREND_STRUCTURE_PATH` to prevent tracked-sidecar pollution: `tests/test_notification_ownership.py:54-71` and `tests/test_prd300_delivery_backstop.py:40-51`. A separately bound tracked `PRICE_BARS_PATH` would require equivalent isolation or a design that derives the path from the already-patched `LOGS_DIR`.
   - The consumer grep was otherwise substantially accurate: `_render_level_diagram` has one production call at `cuttingboard/delivery/dashboard_renderer.py:2171`, and direct `lvl-diagram` assertions are concentrated in `tests/test_dash_level_diagram.py` and `tests/test_dashboard_renderer.py`. Candidate-card output is additionally asserted throughout `tests/test_dash_candidates.py`, which sec7 includes.
   - Required correction: add `tests/test_ci_artifact_hygiene.py` unconditionally and disposition the constants/facade and live-test-isolation files explicitly. Re-estimate FILES and LOC only after that choice. The current LOC estimates are not independently falsified, but they are not reviewable as complete while the file cone is incomplete.

7. RECOMMENDED — Prototype provenance and viewport evidence are not independently reproducible from the committed evidence artifact.

   - The packet claims real parquet input and inspected screenshots at 360/390/430: `OPERATOR_SETUP_CHART_MATERIAL_PACKET_2026-08-28.md:210-218,309-315`.
   - The committed evidence is a single generated HTML document. It contains four charts, but no generator, source-bar fixture/hash, viewport screenshots, or recorded overflow measurements.
   - The embedded SPY values are consistent with the local cache sample, but the artifact alone cannot prove its source or the claimed viewport inspections.
   - Recommended correction: include either the deterministic generator plus hashed input fixture, or committed screenshots/measurement output for the three required widths. This need not redesign the chart.

Confirmed repository facts:

- All four cited GOV-2 legs fire: consumer enumeration, shared cross-layer carrier, FILES/LOC ceiling, and crossing runtime/persistence/delivery/dashboard. I found no additional currently applicable GOV-2 leg.
- All six required parquet caches exist locally with 256 rows and `[Open, High, Low, Close, Volume]`, ending `2026-08-26`. No parquet cache is tracked; `.gitignore:27` excludes it, so a fresh CI checkout lacks it.
- `TREND_STRUCTURE_SYMBOLS == PRIMARY_SYMBOLS == ("SPY","QQQ","GDX","GLD","SLV","XLE")`.
- No current renderer input carries daily OHLC price-series data. The renderer cannot obtain the ignored parquet cache in a fresh hourly checkout.
- The proposed display-only sidecar and pure chart function are consistent with `VISION.md:51-54`; no new decision semantics, scoring, forecasting, narrative text-mining, or synthesized OHLC is proposed.
- Deferring intraday capture and refusing to infer a structured anchor from narrative text are sound recommendations. Missing ruling questions are the sidecar publication owner/conflict policy, exact completed-session authority, exact freshness policy, and invalid-current-price presentation behavior.

I reviewed from a fresh context, did not author the packet, and had no repository write access. The worktree was clean before and after review; no files were created or modified. GitNexus was available only for older temporary checkouts and was stale relative to the review SHA, so all decisive findings above were verified directly against source at `3a06ed6959fcb7c307952fae8585d3dbd838cf34`.
