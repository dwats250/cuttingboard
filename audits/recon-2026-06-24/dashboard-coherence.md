# Dashboard coherence recon — 2026-06-24

**Charge:** RECON (read-only). Verify the live dashboard loads real, fresh,
correctly-ingested data and that surfaced decision language is internally
coherent. Findings for human triage — classify, evidence, blast-radius hint.
No fixes, no PRD, no branch.

**Branch:** `claude/dashboard-coherence-recon-xi8g5e` (no push).
**Live payload inspected:** `origin/publish` @ `dbfd6b2` —
`CB report: 2026-06-24 | RISK_ON | 0 trades [] | SUCCESS`, published
2026-06-24 15:30:27 UTC (a MIDDAY hourly run).
**Injection hygiene:** all rendered/ingested text treated as data. No
directive-looking text found in any artifact.

---

## Contract: freshness window + staleness rule (verbatim "expected")

From `cuttingboard/delivery/dashboard_renderer.py`:

- **Display badge** — `DASHBOARD_STALE_AFTER_SECONDS = 300`.
  `_compute_timestamp_freshness`: `FRESH` if age ≤ 300 s else `STALE`
  (`PARSE_ERROR` on bad ts). RUN-SNAPSHOT token (`_run_snapshot_freshness_token`):
  `<60 s → "<1 min old"`, `≤300 s → "N minute(s) old"`, `>300 s → "STALE (>5 min)"`.
- **Publish gate (PRD-119)** — `LIVE_SESSION_MAX_AGE_MINUTES = 180`;
  `INACTIVE_SESSION_MAX_AGE_HOURS = 72` (only `SUNDAY_PREMARKET`).
  `_allowed_freshness_window(session_type)` → `(max_age_s, label)`; payload age
  `> max_age` → `StalePublishError`, publish blocked. Payload ts must be Zulu UTC
  (`_parse_payload_timestamp`, strict).
- **Coarse pipeline-age tokens (PRD-189)** — `_surface_age_token` (LIVE STATE):
  min/hr/day buckets, `None → absent_label`. `_scoreboard_age_token`:
  day-granular, `≤0 days → "today"`.
- **Scoreboard return rule (PRD-175/204)** — `regime_history`: a date D's
  `spy_close_change_pct` is the **next-session** SPY % change (D scored by D+1's
  close). Null is legitimate only for D ≥ latest cached SPY close (pending);
  null on D < latest close with no prior value is a logged source-gap; an
  already-computed value is preserved + `spy_close_change_pct_stale=True` rather
  than wiped.

**Live freshness verdict:** PASS. Payload/run/market_map/contract all carry the
same `generation_id = live-20260624T153013Z`; `macro_drivers_snapshot` and
`trend_structure_snapshot` both `generated_at 2026-06-24T15:30:13Z`; newest
`regime_history` row is `2026-06-24`. **No section is silently carrying a prior
session's value** — every section traces to the 15:30:13Z generation.

---

## Findings

| ID | section | class | evidence (file · field · observed vs expected) | blast-radius hint | disposition |
|----|---------|-------|-----------------------------------------------|-------------------|-------------|
| F01 | system-state | OK | All source artifacts share `generation_id=live-20260624T153013Z`; payload `meta.timestamp=2026-06-24T15:30:13Z` within 180 m live window; badges FRESH at render. | — | ignore |
| F02 | macro-tape | OK (COHERENT) | `MACRO BIAS: MIXED` = 2 risk-ON (VIX↓, 10Y↓) vs 2 risk-OFF (BTC↓, DXY↑); aggregation matches the 4 displayed evidence votes. | — | ignore |
| F03 | macro-tape | OK | All 6 tradable arrows (SPY↑ QQQ↑ GLD↓ GDX↓ SLV↓ XLE↓) match `trend_structure.daily_change_pct` signs. | — | ignore |
| F04 | red-folder | OK (CORRECT) | `red_folder.load_schedule` loud-error loader returns ok=True; next event `2026-07-02 NFP` is outside the 48 h window; not expiring (last `2026-12-15`). "No events" is genuine, not a load failure. | — | ignore |
| F05 | candidate-board | OK (COHERENT) | SPY card BIAS=BULLISH, "regime aligned" under system regime RISK_ON; `market_map.json generation_id` matches payload. No NEUTRAL-vs-aligned contradiction. | — | ignore |
| F06 | changes-since-last-run | OK (COHERENT) | "Permission flipped to longs": `_resolve_previous_run` → 14:38 run regime=NEUTRAL; current=RISK_ON. Flip is real. | — | ignore |
| F07 | scoreboard | OK | Populated rows trace to `regime_history.jsonl`; nulls explained (see F15). | — | ignore |
| F08 | trend-structure | **INGESTION** | `trend_structure_snapshot.QQQ`: `sma_50=null, sma_200=null, relative_volume=null` → renders "DATA UNAVAILABLE"×3 + RVOL "—", while SPY/GLD/GDX/SLV/XLE all resolve from the same fetch. QQQ quote (`current_price=717.19`) + regime vote (`QQQ pct_change: NEUTRAL`) present → only the OHLCV **history** fetch failed for QQQ. **Recurring:** unavailable on 06-24 14:38 **and** 15:30, and 06-23 15:44 pre-market; resolved on 06-23 16:00/17:10. Not a one-off flake. | One symbol's structure row; price/arrow/regime unaffected. Recurs at pre-market/midday slots despite PRD-190/193 SMA-resolution work. | triage |
| F09 | trend-structure | IMPROVEMENT (SEED) | Unavailable-token + SMA-composite readability. QQQ row repeats "DATA UNAVAILABLE" across 3 columns; SMA Composite already reads "Structure unavailable" (good). Resolved rows render prose ("Above SMA50 and SMA200") vs seed-preferred compressed `↑50/↓200`. Underlying JSON `sma_*=null`. **Open judgment (carry, don't settle):** "NULL" cuts against the decision-language principle (PRD-158); prefer "UNAVAILABLE"/"Structure unavailable" + a compressed alignment cell. | Presentation only. | scope |
| F10 | macro-tape ↔ system-state | COHERENCE (low) | "MACRO BIAS: MIXED" sits directly above tradables while system regime=RISK_ON ("Longs allowed"). Also driver-level divergence: macro-evidence "DXY↑ risk-OFF vote" vs `latest_contract.regime.vote_breakdown["DXY pct_change"]="NEUTRAL"`. Different vote universes (4-driver macro sidecar vs 8-vote regime incl. SPY/QQQ/IWM); by-design per integrator Rule 3. | Reader-facing tension; no decision impact. | triage |
| F11 | macro-tape (internal) | COHERENCE (low) | MACRO PRESSURE detail lists 3 drivers (VIX/DXY/BTC); MACRO EVIDENCE lists 4 (adds 10Y). Same block, inconsistent driver coverage. | Presentation. | triage |
| F12 | system-state (age tokens) | IMPROVEMENT (freshness) | RUN SNAPSHOT / LIVE STATE "<1 min old" and SCOREBOARD "today" are server-rendered **static** text (no client JS; `<meta refresh 30>` re-fetches the same HTML). Between publishes — esp. overnight — the page keeps showing "<1 min old" while hours stale. | Freshness silently overstated between runs; inherent to static publish. | scope |
| F13 | system-state (header/badge) | COHERENCE (low) | Header "SYSTEM STATE - NO TRADE" paired with regime badge "Longs allowed". Badge = regime-direction permission, not trade permission (posture STAY_FLAT, confidence 0.375; payload `permission="No new trades permitted."`). | Decision-language clarity. | triage |
| F14 | payload meta | OK (NOTE) | `payload.meta.symbols_scanned=0` (= qualified+rejected+watchlist of payload sections under the STAY_FLAT regime short-circuit) while `latest_run.candidates_generated=16` and candidate-board renders 6 from `market_map`. Different counters/artifacts; consistent under the short-circuit. | Observability only. | ignore (note) |
| F15 | scoreboard / regime_history | COHERENCE (low, log-only) | `2026-06-19` (Juneteenth — NYSE closed) carries a regime row (RISK_ON/Stay Flat, run_count 2) with "SPY next n/a". Token is **CORRECT** (no 06-19 SPY close exists). But `aggregate()` gap-warning (`null && date < spy_max_date`) would mislabel it as a "partial/truncated SPY cache" gap rather than a holiday (PRD-198 #3, authoritative-source). Also: engine produced an unscoreable read on a market-closed day. | Log-warning semantics + holiday-session row noise; not user-facing. | triage |

---

## Notes for the human at the seam

- **No STALE and no masquerading-as-unavailable defects found.** Every section is
  fresh and traces to the 15:30:13Z generation. The one genuine ingestion gap
  (F08, QQQ) is **fail-loud** — the renderer honestly shows "DATA UNAVAILABLE",
  it does not dress a failure as data.
- **F08 is the load-bearing finding.** QQQ's SMA history is missing on the
  pre-market/midday slots and resolves on later hourly runs — a recurring,
  symbol-specific OHLCV-history gap that survived PRD-190 (window 6→12) and
  PRD-193 (trading-day cache freshness). Recommend triage of QQQ's fetch/cache
  path specifically.
- **F09 (SEED) is presentation, not correctness** — carried per charge; the
  token choice (NULL vs UNAVAILABLE) and SMA-composite compression are flagged
  for scope, not settled here.
- Everything else (F10–F13, F15) is low-severity decision-language / coherence
  polish. Recommend, don't decide.
