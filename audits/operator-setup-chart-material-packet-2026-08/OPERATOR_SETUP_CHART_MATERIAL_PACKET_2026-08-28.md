# Operator setup chart — MATERIAL design packet

```
STATUS: PROVISIONAL MATERIAL PACKET — 2026-08-28 — DESIGN ONLY
AUTHORIZES NO IMPLEMENTATION, NO PRD NUMBER, NO PRODUCER BUILD, NO CONSUMER
BUILD, NO GATE A, NO MERGE.
GOV-2 PACKET-REVIEW CYCLE: EVENT 1 COMPLETE (DESIGN INCOMPLETE at 3a06ed6;
  the ONE consolidated correction APPLIED at 64676f5 — ## CORRECTION CYCLE).
  EVENT 2 ATTEMPT 1 (against 64676f5): NOT CONFIRMED on four bounded
  residuals (F1 idempotence overstated, F3 stale-fallback bound, F6
  import-time path binding, F7 evidence reproducibility); F8 PASS — no new
  material class. The bounded confirmation repair is applied in THIS
  revision (## CONFIRMATION REPAIR), per the GEX-2 packet-cycle precedent.
AWAITING: Event-2 ATTEMPT 2 exact-corrected-head confirmation (GOV-2 sec7).
Ceilings below are ESTIMATES (GOV-2 sec5), not constraints.
```

> Upstream MATERIAL design packet required by GOV-2 before any PRD, decision
> entry, or implementation authority for the owner-charged Market Map chart
> (owner charge 2026-08-27, "LANE A — MARKET MAP STATIC CHART"). It defines
> the smallest carrier + chart design that replaces the level-ladder
> visualization with a real static market chart, so Dustin can issue a
> design-direction ruling from a review-clean packet.
>
> Sequence position: provisional packet -> Event-1 independent Codex review
> -> ONE consolidated author correction -> Event-2 exact-corrected-head
> confirmation -> Dustin design-direction ruling -> Stage-0 PRDs ->
> fresh-context PRD review -> Gate A -> implementation -> implementation
> review -> Dustin merge.

---

## sec0 — Intake classification (GOV-2 sec1)

**MATERIAL — fires on the merits.** The owner charge authorizes
implementation but does not classify; classification run 2026-08-28 at main
`4fe7d67`:

- **Selects a carrier shared across pipeline layers (fires).** The design
  adds a new persisted sidecar `logs/price_bars_snapshot.json`, WRITTEN by
  the runtime (both hourly and daily paths) and READ by the delivery-layer
  dashboard renderer, then published to the `publish` branch. That is a new
  runtime -> persistence -> delivery/dashboard -> published-site carrier.
- **Crosses two or more enumerated layers (fires).** Runtime (writer),
  persistence (`logs/` sidecar), delivery/dashboard (reader/renderer) — at
  least three of the sec1 list.
- **Establishes production FILES and LOC ceilings (fires).** sec7/sec8
  propose the implementation cones and ceilings.
- **Consumer enumeration (fires).** sec5 claims to enumerate all consumers
  of the new sidecar and of the replaced level-ladder surface.

Legs that do NOT fire: no governance guardrail change; no Critical/High
finding resolution; no existing contract/audit/payload/notification schema
is added, removed, renamed, or changed (the sidecar is NEW and display-only;
the run/payload/market_map contracts are untouched).

**Downstream lanes (estimate; the PRDs decide under `docs/PRD_PROCESS.md`):**
two slices, in dependency order.
- **PRD-P (producer):** bars-sidecar writer in `cuttingboard/runtime/__init__.py`
  + workflow force-add/restore wiring. Not a CONSUMER-class slice; lane per
  matrix (runtime seam; expect STANDARD unless R11 fires on a touched file).
- **PRD-C (consumer):** chart module + renderer integration.
  CONSUMER / **HIGH-RISK — FORCED** (R11: `cuttingboard/delivery/dashboard_renderer.py`
  touched as payload, per the GEX-2 packet precedent).
A MATERIAL slice is MICRO-ineligible (GOV-2 sec1); neither slice is MICRO.

---

## sec1 — Owner charge and design goal

Owner charge (2026-08-27) accepts the answer-first board but rejects the
Market Map visualization: "Stop treating the existing horizontal level
ladder as a finished visualization... Market information that is inherently
spatial should look like a real market chart." Target: static, deterministic,
non-interactive charts with (1) price path / OHLC candles, (2) prioritized
key levels, (3) subordinate secondary levels, (4) shaded structural zones,
(5) immediate price-relative-to-setup understanding, (6) text supporting the
chart. Mobile-first (390x844 primary; legible 360/390/430; no horizontal
overflow). No new provider; prefer existing cached data; STOP if a new
provider appears necessary (it does not — sec2). Success criterion: "An
operator should understand the setup from the chart before reading all
supporting text."

---

## sec2 — Verified data inventory (all claims re-verified by the author)

1. **Daily OHLCV exists for every market-map symbol and is fetched on BOTH
   pipeline paths.** `_collect_trend_structure_history`
   (`cuttingboard/runtime/__init__.py:2441-2466`) fetches/caches 12-month
   daily OHLCV per `config.TREND_STRUCTURE_SYMBOLS` on every hourly run
   (`runtime/__init__.py:778-782`) and every daily MODE_LIVE run
   (`runtime/__init__.py:1493-1507`), via `fetch_ohlcv`
   (`cuttingboard/ingestion.py:119`, trading-day-keyed parquet cache
   `data/cache/<SYM>_ohlcv.parquet`, `.gitignore:27`). Verified locally:
   23 parquet files; `SPY_ohlcv.parquet` = 256 rows x [Open,High,Low,Close,
   Volume], 2025-08-20 -> 2026-08-26.
2. **The trend symbols ARE the market-map symbols.**
   `config.TREND_STRUCTURE_SYMBOLS` (`cuttingboard/config.py:278`) ==
   `market_map.PRIMARY_SYMBOLS` (`cuttingboard/market_map.py:20`) ==
   ("SPY","QQQ","GDX","GLD","SLV","XLE"). The frames needed for six charts
   are already in hand at the existing snapshot-writer seams. **Zero new
   network calls for daily bars.**
3. **No artifact the renderer receives carries any price time series.**
   Every price field in payload / run / market_map / trend_structure /
   watchlist / GEX snapshots is a scalar (recon sweep, re-verified for
   market_map and trend snapshot). The parquet cache is gitignored and NOT
   in a fresh CI checkout, so the renderer cannot read it directly on the
   hourly job (which fetches OHLCV only for the six trend symbols inside the
   runtime, after which the frames are discarded).
4. **market_map per-symbol fields available to the chart** (producer
   `cuttingboard/market_map.py:159-244`; verified against
   `logs/market_map.json`): `current_price` (scalar), `watch_zones`
   (type/level/context; types VWAP, ORB_HIGH, ORB_LOW, PRIOR_HIGH,
   PRIOR_LOW, EMA9, EMA21, EMA50; +-5% price filter), `fib_levels`
   (retracements 0.382/0.5/0.618 + swing high/low), `grade`, `bias`,
   `structure`, `setup_state`, narrative `invalidation` /`trade_framing`.
   Numeric entry/stop come only from the contract maps
   (`contract_entry_map` / `contract_stop_map`, already renderer inputs).
   Hourly-map level content is PATH/STATE DEPENDENT (Event-1 F4): with no
   candidates the hourly map carries EMA zones only (no intraday metrics on
   the hourly path — `runtime/__init__.py:566`); when hourly qualification
   fetches candidate OHLCV (`runtime/__init__.py:605-609,628-632`) the
   primary-symbol frames reach `build_market_map` (`:736-748`) and fibs are
   derived (`market_map.py:159-175,359-384`), so an hourly candidate can
   carry fibs.
5. **Sidecar transport precedent (corrected per Event-1 F1).**
   `logs/trend_structure_snapshot.json` is git-tracked as a fallback,
   CO-PRODUCED FRESH by both paths (it is NOT in either workflow's
   `ci_restore_publish_state.sh` restore list — restore is for read-back
   state, which a regenerated snapshot does not need), force-add staged by
   the hourly (`.github/workflows/hourly_alert.yml:185-197`) and covered by
   the daily's blanket `git add -f logs/` (`cuttingboard.yml:511-530`), then
   full-overwritten onto the publish tip by `tools/ci_push_artifacts.sh`
   (PRD-194). The new sidecar rides THIS mechanism: co-produced, never
   restored. The resulting two-producer overwrite race is designed for in
   sec3 (content idempotence per completed session + `as_of` truth clock).
6. **Provider.** yfinance only (`cuttingboard/config.py:284-293`). No new
   provider is necessary; the charge's STOP condition does not fire.
7. **Existing chart surface.** `_render_level_diagram`
   (`cuttingboard/delivery/dashboard_renderer.py:1734-1998`): 280x110 SVG of
   horizontal level lines (no price path), with semantic contracts to
   preserve — PRD-226 NOW-anchor rules, PRD-223 entry->stop risk zone,
   PRD-304 lock neutralization (grey palette, STOP->INVALIDATION,
   ENTRY->LEVEL), PRD-221/222 %-distances, deterministic declutter.

## sec3 — Carrier design: `logs/price_bars_snapshot.json`

Display-only, read-only-sidecar-by-default (VISION), one writer, one reader.

```json
{
  "schema_version": 1,
  "generated_at": "<UTC ISO of the writing run>",
  "source": {
    "producer": "hourly|daily",
    "provider": "yfinance", "interval": "1d", "adjusted": true
  },
  "columns": ["session_date", "open", "high", "low", "close", "volume"],
  "symbols": {
    "SPY": {
      "as_of": "<session date of last completed bar written>",
      "bars": [["2026-08-26", 764.73, 767.35, 763.93, 766.08, 28459700], ...]
    }, ...
  }
}
```

(Event-1 F3 dispositions baked in: `source.producer` names the writing PATH
— hourly vs daily — because runtime `mode` cannot distinguish them
(`runtime/_constants.py:26-29`); `adjusted: true` records the
`auto_adjust=True` basis of `fetch_ohlcv` (`ingestion.py:389-402`);
`columns` pins the positional order; `session_date` values are naive
ET-session dates exactly as indexed by the cache.)

- **Writer:** one small function beside `_write_trend_structure_snapshot`
  / `_write_watchlist_snapshot` (`runtime/__init__.py:2469`, `:787`),
  called at BOTH existing seams (`:778` hourly, `:1493` daily). Per Event-1
  F4: each seam binds `_collect_trend_structure_history(ohlcv)` ONCE to a
  local and threads the SAME object into the trend writer and the bars
  writer — never a second collection (which could repeat failed fetches and
  void the zero-new-call property). Serialization only — no new fetch, no
  new provider, no decision-path read.
- **Completed-session rule (corrected per Event-1 F2):** the writer retains
  exactly the rows whose session date is <= `most_recent_completed_session_date(generated_at)`
  — the EXISTING market-session authority the cache itself is keyed by
  (`cuttingboard/ingestion.py:147-167`). It does not use "!= today": the
  normal fetch path (`end=<current UTC date>`, exclusive —
  `ingestion.py:383-396`) already yields completed sessions only, and a
  today-dated row supplied after the close would be a legitimately
  completed session that must be kept. "Where is price now" is answered by
  the existing hourly-fresh `market_map.current_price` NOW line, never by a
  synthesized candle. **Never synthesize OHLC.**
- **Two-producer ownership (Event-1 F1):** BOTH workflows co-produce the
  sidecar fresh each run; NEITHER restores it (it is regenerated state, not
  read-back state). The publish overlay full-overwrites it
  (`tools/ci_push_artifacts.sh:97-115`), and after a non-fast-forward retry
  an older delayed run can overwrite a newer publish. The race guarantee is
  PER-SYMBOL CONTENT IDEMPOTENCE (stated precisely per Event-2 F1: whole-
  snapshot idempotence is FALSE once partial snapshots are legal): for any
  symbol PRESENT in a snapshot, its `bars`/`as_of` are a pure function of
  `most_recent_completed_session_date`, so an overwrite can never replace a
  present symbol's bars with different bars for the same session. What an
  out-of-order overwrite CAN do is (a) regress `generated_at` (provenance
  only, never compared to the page clock — the PRD-250 banner owns page
  age), and (b) replace a complete snapshot with a partial one, dropping a
  symbol whose fetch failed in the older run: that symbol's chart degrades
  to the ladder for at most one publish cycle and self-heals on the next
  successful run. No state can render WRONG bars; the worst outcome is a
  visibly absent chart. Cross-session overlap (a delayed pre-open run
  overwriting after the boundary) shifts `as_of` back by exactly one
  session and is visibly labelled by the `as_of` caption plus rejected by
  the reader guard below when it ever exceeds the age bound — honest,
  bounded, no new locking machinery.
- **Reader age guard (added per Event-2 F3):** the one-session bound holds
  only while the pipeline runs; a frozen pipeline leaves the tracked
  fallback available indefinitely. The RENDERER therefore refuses bars
  whose `as_of` is more than 5 calendar days older than the render clock
  (the existing `now` parameter — no new clock source; 5 days spans
  weekends and holiday gaps without a session calendar): stale-beyond-guard
  is treated exactly as bars-absent and degrades to the ladder. The chart
  never draws a candle series older than the guard, whatever the sidecar
  file says.
- **Per-symbol validation & partial snapshots (Event-1 F3):** the writer
  validates each frame's columns and row shape; a failing symbol is OMITTED
  from `symbols` (never partially written), and a partial-symbol snapshot
  is LEGAL — the chart for an omitted symbol degrades per sec4 while other
  symbols chart normally. All retained symbols in one snapshot share the
  same completed-session authority, so mixed `as_of` values can differ only
  via per-symbol fetch failure, which omission already excludes.
- **Window:** last 40 completed bars per symbol (chart draws ~30; small
  margin for fixtures). ~6-9 KB/symbol, ~50 KB total.
- **Failure semantics:** writer failure is caught-and-logged exactly like
  the trend snapshot writer (PRD-278 R8 pattern); the renderer's chart
  degrades honestly (sec4) — a missing sidecar can never fail the run or
  fabricate a chart.
- **Transport:** tracked fallback copy in `logs/`, added to the hourly
  force-add allowlist and covered by the daily's `git add -f logs/`;
  NOT added to any restore list (sec2.5).
- **Renderer input:** new optional `price_bars_snapshot` parameter loaded in
  the existing `_load_*` style with source provenance, exactly like
  `trend_structure_snapshot`.
- **Path constant:** `PRICE_BARS_PATH` defined in
  `cuttingboard/runtime/_constants.py` DERIVED FROM `LOGS_DIR` (the
  existing pattern), so the full-live test harnesses that patch `LOGS_DIR`
  / sidecar paths (`tests/test_notification_ownership.py:54-71`,
  `tests/test_prd300_delivery_backstop.py:40-51`) isolate it; the facade
  re-export is guarded by `tests/test_runtime_package_surface.py`.

## sec4 — Chart architecture (consumer)

**New module `cuttingboard/delivery/setup_chart.py`** — one pure function:
bars + now_price + entry/stop + watch_zones + fib_levels + operator flags ->
deterministic inline SVG string. No I/O, no clock, no randomness; the
renderer supplies already-loaded facts (the GEX-card assembly pattern).
`dashboard_renderer.py` calls it from `_render_candidate_card` where
`_render_level_diagram` is called today.

- **Layers (bottom to top):** shaded zones -> tier-3 lines -> tier-2 lines
  -> candles -> tier-1 lines -> right-edge price gutter.
- **Fixed, closed tier map (presentation-only; no new setup logic):**
  Tier 1 (strong): NOW (yellow, boxed price tag), contract ENTRY (amber),
  contract STOP (red dashed) with in-plot bold word labels carrying the
  existing signed % distance. Tier 2 (clear, subordinate): VWAP (cyan
  dashed), ORB_HIGH/ORB_LOW, PRIOR_HIGH/PRIOR_LOW (PDH/PDL), EMA9, EMA21
  (structural teal). Tier 3 (faint): EMA50, fib retracements — drawn only
  inside the price domain, never allowed to stretch the scale.
- **Zones (existing structural relationships only):** entry->stop risk band
  (PRD-223 semantics) and the ORB_HIGH-ORB_LOW range band when both levels
  exist. No invented zones.
- **Scale:** y-domain = bars' high/low over the window ∪ tier-1 ∪ tier-2
  levels, 6% pad; x = index-spaced completed daily bars (~30).
- **Authority preservation:** `operator_locked` / non-permitted states reuse
  PRD-304 exactly — grey accents, ENTRY->LEVEL, STOP->INVALIDATION, no
  action colours; the chart inherits the existing `.candidate-observation`
  dimming and (non-permitted) `<details>` LEVEL MAP disclosure introduced by
  PRD-318. The chart is observational rendering; it reads decision state,
  never feeds it.
- **Candidate presentation:** highest-priority visible setup renders one
  full-width chart; lower cards keep their native `<details>` disclosure
  (chart inside), so phones never stack three full charts.
- **Degradation chain (never fabricate; corrected per Event-1 F5):** bars
  present -> candle chart; sidecar absent/unreadable or symbol omitted ->
  the existing `_render_level_diagram` ladder (retained as the fallback
  surface, no longer the primary). There is NO separate chart-staleness
  threshold: the completed-session rule means the sidecar is at most one
  session behind by construction, the chart captions its own `as_of`, and
  page-age staleness stays owned by the PRD-250 banner. No valid
  `current_price` -> the chart is SUPPRESSED exactly as PRD-226 suppresses
  the ladder today (the candidate-card caller gates on a valid price,
  `dashboard_renderer.py:2141-2164`; the in-function sentinel remains the
  unreachable belt-and-suspenders guard it already is). No new sentinel
  presentation is introduced. A compact text level table below the chart is
  available as an optional detail (ruling question Q3).
- **Geometry:** 358x232 viewBox, `width="100%"` + `max-width`, right gutter
  78px. Verified in the prototype: no horizontal overflow at 360/390/430
  (viewBox scaling absorbs the 360px case); labels legible at 390x844.

**Prototype evidence:** `EVIDENCE_PROTOTYPE_RENDER_2026-08-28.html` (this
directory) — four states rendered from REAL SPY/QQQ parquet bars with demo
levels: bullish setup, dense-levels + ORB band, operator-locked
(neutralized), and no-contract observation. Screenshots inspected at
360/390/430; gutter declutter is deterministic and height-aware.

## sec5 — Carrier-participant enumeration and falsifiers (corrected per Event-1 F1)

Participants in the NEW carrier after this design — the full set, not just
the semantic reader:
1. Producer A: hourly runtime seam (`runtime/__init__.py:778` block);
2. Producer B: daily runtime seam (`runtime/__init__.py:1493` block);
3. Transport stage sites: hourly force-add allowlist
   (`.github/workflows/hourly_alert.yml:185-197`) + daily blanket
   `git add -f logs/` (`cuttingboard.yml:511-530`);
4. Publish overlay: `tools/ci_push_artifacts.sh` full-overwrite semantics;
5. Guard tests: `tests/test_ci_artifact_hygiene.py` (asserts the exact
   staged-artifact and restore sets — MUST be updated by PRD-P);
6. Semantic reader: `dashboard_renderer.py` via the new loader (the only
   consumer of the CONTENT); plus humans reading the file.
NOT a participant: either workflow's `ci_restore_publish_state.sh` list
(co-produced state is never restored).
Falsifier: `rg -l "price_bars_snapshot|PRICE_BARS_PATH" cuttingboard/ tools/
scripts/ ui/ .github/ tests/` returns exactly the writer, the constants
module and facade, the loader, the hourly workflow allowlist, and their
tests — nothing else.

Consumers of the REPLACED surface (`_render_level_diagram`): exactly one
call site (`dashboard_renderer.py:2171`, inside `_render_candidate_card`);
tests asserting its output enumerate via
`rg -l "_render_level_diagram|lvl-diagram" tests/`. The function is retained
as the degradation path, so no reader is orphaned.
Falsifier for "no other artifact carries a series": re-run the sec2.3 sweep.

## sec6 — States and fixtures the implementation must prove

From the owner charge: bullish SPY setup near VWAP; pullback anchored to
EMA9; ORB-based setup (band); pre-open (prior completed session bars +
reference levels — the completed-bars rule gives exactly this); missing /
insufficient bar data (ladder fallback); dense-level case; HALT / locked
with chart present (neutralized, subordinate to authority); no candidate.
Tests must prove: SVG bounds; correct source bars (byte-derived from the
sidecar fixture); tier-1 emphasized / tier-3 subdued (stroke/opacity
assertions); entry/invalidation present when carried; no invented values
(every rendered price traces to an input); no horizontal overflow (CSS/
geometry assertions); byte-deterministic output; mutation-verified red
tests per the semantic-failure invariants.

## sec7 — FILES cones (estimates)

PRD-P (producer; corrected per Event-1 F6): `M cuttingboard/runtime/__init__.py`,
`M cuttingboard/runtime/_constants.py` (`PRICE_BARS_PATH` derived from
`LOGS_DIR`), `A logs/price_bars_snapshot.json` (tracked fallback),
`M .github/workflows/hourly_alert.yml` (force-add allowlist; NO restore-list
change), `M tests/test_ci_artifact_hygiene.py` (staged-artifact set
assertions), `M tests/test_runtime_package_surface.py` (facade re-export),
`A tests/test_price_bars_sidecar.py` (writer tests, mirroring
`tests/test_watchlist_sidecar.py` / `tests/test_runtime_trend_structure_refresh.py`),
`M docs/SCHEMA_MAP.md`. (`cuttingboard.yml` needs no edit: its blanket
`git add -f logs/` already stages the new file — verified against
`cuttingboard.yml:511-530`; the hygiene test change is what pins this.)
`M tests/test_notification_ownership.py`, `M tests/test_prd300_delivery_backstop.py`
(corrected per Event-2 F6: a module-level `PRICE_BARS_PATH = LOGS_DIR / ...`
binds at import time and does NOT follow a later `LOGS_DIR` monkeypatch, so
both full-live harnesses must redirect `PRICE_BARS_PATH` explicitly, exactly
as they already redirect `TREND_STRUCTURE_PATH` —
`tests/test_notification_ownership.py:54-71`,
`tests/test_prd300_delivery_backstop.py:40-51`).

PRD-C (consumer): `A cuttingboard/delivery/setup_chart.py`,
`M cuttingboard/delivery/dashboard_renderer.py`, `A tests/test_setup_chart.py`,
`M tests/test_dash_level_diagram.py`, `M tests/test_dashboard_renderer.py`,
`M tests/test_dash_candidates.py`, `M tests/data/dashboard_pre_gex_golden.html`,
`M docs/SCHEMA_MAP.md` / `M docs/CALL_SITE_MAP.md` as the recon maps require.

## sec8 — LOC ceilings (estimates)

PRD-P: <=140 net production LOC (writer + constants + workflow line).
PRD-C: <=360 net production LOC across the two production files (new module
~250 + renderer integration), <=900 net test/golden LOC. Estimates raised
only where Event-1 F6 widened the producer cone; STOP-AND-RENEW on breach,
per standing practice.

## sec9 — Intraday option and ruling questions

**Q1 — Intraday session candles (deferred by recommendation).** The owner's
TIME WINDOW prefers current-session bars during session. The hourly path
computes no intraday metrics (`runtime/__init__.py:566`); session candles
would add ~6 `fetch_intraday_bars` calls per hourly run (~42-54/day,
yfinance, free tier) plus hourly-runtime failure surface. Recommendation:
ship the daily-candles slice first (zero new fetches; coherent with the
EMA/fib/PDH levels, which are daily-frame facts), and scope intraday capture
as a follow-up slice under the same schema (`interval` field already
provided). The ruling may instead order intraday in slice 1.
**Q2 — Chart scope:** primary-symbol full chart + disclosure charts for the
rest (recommended), vs full charts for all six.
**Q3 — Ladder retention:** keep the compact text ladder as an optional
detail below the chart (recommended: drop it; the gutter carries the same
facts) — owner charge allows either.
**Q5 — Carrier contract confirmations (added per Event-1).** The correction
fixed four contract choices; each is severable if the ruling prefers
otherwise: (a) two co-producers + content idempotence + `as_of` truth clock,
instead of a single-publisher lock; (b) completed-session authority =
`most_recent_completed_session_date(generated_at)`; (c) chart freshness =
`as_of` caption + a reader age guard (bars older than 5 calendar days vs
the renderer's `now` degrade to the ladder; page-age staleness stays with
the PRD-250 banner); (d) invalid
`current_price` keeps PRD-226 suppression (no new sentinel).
**Q4 — Anchor emphasis:** the charge suggests emphasizing "the specific
anchor driving the setup". No structured per-setup anchor field exists
(only narrative `trade_framing`). Recommendation: fixed closed tier map
(sec4) now; a structured anchor field would be a market_map schema change —
its own MATERIAL intake if ever wanted. No text-mining of narratives.

## sec10 — Risks

- Stale sidecar on a frozen pipeline: mitigated by provenance (`generated_at`
  + per-symbol `as_of` rendered as the chart's own clock) and the existing
  staleness banner; completed-bars rule bounds the lie to "yesterday".
- yfinance daily-frame shape drift: writer validates columns and drops the
  symbol (fail-quiet per snapshot precedent) rather than writing garbage.
- Renderer size: +~50 KB sidecar, +~10-15 KB SVG per full chart — well
  inside the publish path's existing envelope.
- Determinism: pure function over serialized bars; no clock reads in the
  chart module.

## sec11 — Lane and gate obligations carried downstream

PRD-C is CONSUMER/HIGH-RISK (R11 forced): fresh-context implementation
review artifact + `SECOND-MODEL:` disposition (artifact or the exact waiver
sentence) + Dustin's manual merge. PRD-P takes its matrix lane. Both PRDs
get fresh-context review of the exact PRD revision before Gate A, per GOV-2
step 7-8. Everything lands through PRs Dustin merges (GOV-1).

## sec12 — Evidence index

- `EVIDENCE_PROTOTYPE_RENDER_2026-08-28.html` — four-state prototype from
  real parquet bars (this directory).
- `EVIDENCE_PROTOTYPE_GENERATOR_2026-08-28.py` — the deterministic generator
  that produced the render (added per Event-1 F7). Inputs: the local
  parquet cache, sha256/16 at generation time
  `SPY_ohlcv.parquet ad45fd76b2a773e1`, `QQQ_ohlcv.parquet 5b4260c0b7b3e8fe`
  (gitignored inputs; the hashes pin what the committed render was built
  from). Viewport inspection at 360/390/430 was performed with headless
  Chrome (`--window-size`) by the author; the committed HTML re-renders at
  any width via its viewBox scaling for independent inspection.
- `CODEX_EVENT_1_REVIEW_2026-08-28.md` — Event-1 verdict (DESIGN INCOMPLETE
  at 3a06ed6), captured verbatim.
- Recon sweep 2026-08-28 (fresh-context subagent; every decisive claim
  re-verified by the author per the sub-agent sweep re-verification
  discipline): findings folded into sec2.
- Prior art consulted: GEX-2 packet (`audits/gex-2-free-board-card-2026-08/`),
  trend-snapshot transport (PRD-194/PRD-123), ladder semantics
  (PRD-074/216/221/222/223/226/304).

## CORRECTION CYCLE (GOV-2 sec2 step 4 — the ONE consolidated correction)

Event-1 verdict: DESIGN INCOMPLETE at `3a06ed6`
(`CODEX_EVENT_1_REVIEW_2026-08-28.md`). All seven findings dispositioned in
this single revision:
- **F1 (MATERIAL-BOUNDARY, transport/ownership):** APPLIED — sec2.5
  corrected (co-produced, never restored), sec3 adds the two-producer
  ownership design (content idempotence per completed session; `as_of` as
  the reader's truth clock; publish-overlay race bounded to one session and
  visibly captioned), sec5 rewritten as full carrier-participant
  enumeration with a widened falsifier.
- **F2 (completed-bars rule):** APPLIED — sec3 now defines completion via
  `most_recent_completed_session_date(generated_at)`, not "!= today".
- **F3 (provenance/staleness):** APPLIED — schema adds `source.producer`,
  `adjusted: true`, pinned `columns`, session-date semantics; per-symbol
  validation and partial-snapshot legality specified; no undefined
  staleness threshold remains; surfaced as ruling question Q5.
- **F4 (bind-once history; hourly-fibs claim):** APPLIED — sec3 writer
  binds one collection per seam; sec2.4 claim qualified as path/state
  dependent.
- **F5 (PRD-226 degradation):** APPLIED — sec4 rules PRD-226-compatible
  suppression; no new sentinel presentation.
- **F6 (producer FILES cone):** APPLIED — sec7 adds
  `tests/test_ci_artifact_hygiene.py`, `runtime/_constants.py`,
  `tests/test_runtime_package_surface.py`; `LOGS_DIR`-derived path
  dispositions the live-test isolation files; sec8 re-estimated.
- **F7 (RECOMMENDED, evidence reproducibility):** APPLIED — generator
  committed + input hashes recorded (sec12).
No new material class was introduced by the correction (the carrier
participants enumerated in F1 were present in the reviewed design's
mechanism; the correction names and designs for them).

## CONFIRMATION REPAIR (bounded; after Event-2 ATTEMPT 1 NOT CONFIRMED)

Event-2 attempt 1 (`CODEX_EVENT_2_CONFIRMATION_ATTEMPT_1_2026-08-28.md`,
against `64676f5`) confirmed F2/F4/F5/F8 and returned four bounded
residuals, each repaired in this revision:
- **F1 residual:** the whole-snapshot idempotence claim was overstated once
  partial snapshots are legal. sec3 now states the guarantee precisely as
  PER-SYMBOL content idempotence and names the real worst case (a symbol
  drops to ladder-degrade for one publish cycle, self-healing; wrong bars
  are impossible).
- **F3 residual:** the one-session freshness bound was false under a frozen
  pipeline. sec3 adds the READER AGE GUARD: `as_of` older than 5 calendar
  days versus the renderer's existing `now` is treated as bars-absent
  (ladder). Also folded into ruling question Q5(c).
- **F6 residual:** import-time binding means `LOGS_DIR` patching alone does
  not isolate the new path. sec7's PRD-P cone now includes
  `tests/test_notification_ownership.py` and
  `tests/test_prd300_delivery_backstop.py` with explicit `PRICE_BARS_PATH`
  redirection.
- **F7 residual:** evidence now reproduces from a fresh checkout: the bar
  fixture is COMMITTED (`EVIDENCE_BARS_FIXTURE_2026-08-28.json`), the
  generator loads it via a path relative to its own file (parquet only via
  an explicit `--parquet` flag), and regeneration was verified
  BYTE-IDENTICAL to the committed render; the three inspected viewport
  screenshots are committed
  (`EVIDENCE_SCREENSHOT_{360,390,430}_2026-08-28.png`).
