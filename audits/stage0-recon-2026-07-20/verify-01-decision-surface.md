# Verification — Track A: stage0-01-decision-surface-v0.1.md (Q1-12)

**VERIFIED FINDINGS, UNVERIFIED ISOLATION** — see
`verify-00-disposition-index.md`'s capability header: this session's
self-reported session id resolved to a template placeholder string, not a
genuine identifier, so its fresh-context/isolation status per the
Charter's §14 step 4 could not be established and must not be asserted as
independent. The findings below were independently derived via each
check's own methodology (own fixtures, own re-runs, own citation checks)
regardless — findings and isolation are separable claims. Verified against
this worktree's HEAD (`043bcf5`), source-tree-identical to the pinned SHA
`771f730839b00b0537327f9696210275f36cd790` (confirmed via
`git diff --stat <pin> HEAD` — only new `audits/*` files differ).

## Headline: Q8 (ORB positional contamination) — REPRODUCED

The charge required I reproduce this myself, not accept the artifact's trace.
I built my own synthetic 391-bar one-minute session (own script, own values,
not copied from the artifact) with:
- True opening range (first 5 bars of the real session): high=110.0, low=105.0
- A distractor 5-bar window at original index 271-275 (which becomes
  `bars[:5]` of the tail-120-truncated frame, since 391-120=271): high=777.0,
  low=770.0

Ran `cuttingboard.watch.compute_intraday_metrics` directly against this
fixture (via injected fetchers, no network):

```
len(metrics.bars) after watch._bars_from_df truncation: 120
metrics.bars[0].timestamp (bars[:N_RANGE] window start): 2026-07-20 18:01:00+00:00
orb_high = 777.0  orb_low = 770.0
```

`orb_high`/`orb_low` reflect the distractor window, not the true 110.0/105.0
session open. **Disposition: CONFIRMED / REPRODUCED**, independently, under my
own fixture — not merely re-run of the artifact's numbers. (Coincidentally my
fixture's truncation-boundary timestamp, `18:01:00 UTC`, matches the
artifact's own reported `2026-07-20T18:01:00+00:00` — an artifact of both of
us using a 391-bar session starting 13:30 UTC and MAX_INTRADAY_BARS=120, not
a copied result.)

Root cause confirmed by direct code reading:
- `cuttingboard/watch.py:164` — `orb_slice = bars[:N_RANGE]` (positional, not
  timestamp-filtered).
- `cuttingboard/watch.py:356-371` (`_bars_from_df`) — `frame.tail(MAX_INTRADAY_BARS)`
  (120) truncates before the positional slice ever runs.
- `cuttingboard/ingestion.py:207` — `fetch_intraday_bars` already returns
  `frame.tail(120)` upstream, so the truncation is double-applied.

## Per-question disposition

All STATIC citations below were checked with `sed -n '<range>p'` against the
pinned tree; every one resolves to the content the artifact describes. I list
representative, not exhaustive, citations per question — see the note below
for what was not individually re-checked.

- **Q1 (producer/field ownership) — CONFIRMED.**
  - `runtime/__init__.py:791-800` sets `contract["system_state"]["permission"]`
    from `_PERMISSION_LINES.get(_ss_posture_label, "No new trades permitted.")`,
    confirming both the ownership claim and the default-fallback claim.
  - `delivery/payload.py:34-40,120-131` relays `permission_val` into
    `payload["summary"]["permission"]` — confirmed verbatim.
  - `execution_policy.py:157-199` (`apply_execution_policy`) sets
    `policy_allowed`/`policy_reason` on both the allow and block branches —
    confirmed verbatim.
  - `contract.py:351-372` serializes `policy_allowed`/`policy_reason` into
    `trade_candidates[*]` — confirmed.
  - `trade_visibility.py:47-68` consumes exactly those two fields — confirmed.
  - `execution_policy.py:231-236` — `orb_reason != POLICY_ORB_UNAVAILABLE`
    check confirms `orb_unavailable` is retained as a reason but not itself a
    hard block — confirmed.
  - `market_map.py:159-244` (`_build_symbol_record`) owns the full
    `grade/bias/structure/setup_state/watch_zones/trade_framing` field set —
    confirmed, full function read.
  - `market_map.py:187-210` — missing-quote path yields `GRADE_F` /
    `SETUP_DATA_UNAVAILABLE` exactly as claimed — confirmed.
  - `watch.py:212-229` / `intraday_state_engine.py:512-534` — both dataclass
    constructions are transient, in-memory only — confirmed no persistence
    call in either.

- **Q2 (non-authoritative overlapping producer) — CONFIRMED.**
  - `trend_structure.py:49-71` (`_vwap`) computes only from supplied intraday
    history; `trend_structure.py:120-136` classifies non-intraday input as
    `NOT_COMPUTED` (vs. `DATA_UNAVAILABLE` for true outages) — confirmed
    exactly, including the PRD-130 rationale comment.
  - `docs/artifact_flow_map.md:107-115` declares the consumer as
    `dashboard_renderer.py` (render-only) plus "human review... observe-only"
    — confirmed verbatim.
  - `market_map.py:343-356` (`_zone`) filters any level beyond 5% distance —
    confirmed (`if distance_pct > 0.05: return None`).

- **Q3 (time basis / universe / unavailable semantics) — CONFIRMED.**
  - `ingestion.py:170-207` (`fetch_intraday_bars`) filters
    `between_time("09:30","15:30")` in ET then converts to UTC, and restricts
    to the latest session date — confirmed.
  - `config.py:207-209` — `TREND_STRUCTURE_SYMBOLS = ("SPY","QQQ","GDX","GLD","SLV","XLE")`
    matches `market_map.py:19-20` `PRIMARY_SYMBOLS` exactly (same tuple) —
    confirmed.

- **Q4 (fixed-universe producer outside decision guards) — CONFIRMED.**
  - `runtime/__init__.py:1172-1188` — premarket calls
    `_refresh_trend_structure_sidecar` gated only on `mode == MODE_LIVE`, after
    decision construction — confirmed.
  - `runtime/__init__.py:537-562` — hourly writes the trend snapshot in an
    unconditional post-decision block — confirmed.
  - `runtime/__init__.py:2052-2068` (`_collect_trend_structure_history`)
    iterates `config.TREND_STRUCTURE_SYMBOLS` regardless of candidate set —
    confirmed.

- **Q5 (atomic write) — CONFIRMED.** `runtime/__init__.py:2077-2089` writes to
  `TREND_STRUCTURE_PATH.with_suffix(".tmp")` then `tmp.replace(...)` —
  confirmed exactly.

- **Q6 (full-session bars vs. persisted anchors) — CONFIRMED** (see Q8
  reproduction above, which is the runtime half of this same claim).

- **Q7 (no truthful lifecycle schema; two ORB rules) — CONFIRMED.**
  - `intraday_state_engine.py:400-438` (`compute_intraday_state`) returns
    `None` before `_NOISE_END` (`time(9,45)`, confirmed at line 34) and raises
    `InsufficientDataError` for <5 ORB-window bars — confirmed.
  - `intraday_state_engine.py:124-142` (`_orb_bars`/`_compute_orb`) selects ORB
    bars by ET timestamp window (09:30-09:35), genuinely different from
    `watch.py`'s positional `bars[:N_RANGE]` — confirmed, and this is the
    concrete evidence for "two modules use different ORB-selection rules."

- **Q9 (no hourly reuse of stale premarket watch-zone inputs) — CONFIRMED.**
  - `runtime/__init__.py:384-389` initializes `intraday_metrics: dict[str, Any] = {}`
    inside `_execute_notify_run`.
  - I grepped the whole file: `compute_all_intraday_metrics` is called exactly
    once, at line 973, inside `_run_pipeline` (a different function, starting
    at line 861) — never inside `_execute_notify_run` (356-621). The hourly
    branch's `build_market_map(...)` call (lines ~522-533) passes
    `intraday_metrics=intraday_metrics` — the same never-reassigned empty
    dict from line 388. This is airtight: hourly literally cannot see
    premarket intraday metrics; it only ever sees `{}`.
  - `market_map.py:319-340` (`_watch_zones`) only appends VWAP/ORB/PDH/PDL
    zones `if intraday is not None` — confirming an empty-dict input yields no
    VWAP/ORB zones (EMA zones from `derived` can still appear, confirmed by
    the same code block) — matches the claim precisely.

- **Q10 (existing-row disposition, `_render_candidate_card`) — CONFIRMED.**
  Read `dashboard_renderer.py:1806-1910` in full: low-grade branch (1806-1820)
  renders symbol/bias/structure + failure reason; high-grade branch renders
  `IF NOW`, conditional `LIFECYCLE` line, `IN →`/`OUT →`, and a collapsed
  `REASON`/`PLAY`/`WATCH` detail block — matches the artifact's line-by-line
  breakdown exactly.

- **Q11 (market-state vs. permission transitions) — CONFIRMED.**
  - `market_map_lifecycle.py:51-85` (`inject_lifecycle`) transitions only
    `grade`/`setup_state`, and separately backfills `current_price` from the
    previous snapshot when the current one is `None` — confirmed exactly,
    including the "lifecycle can carry a prior price forward" sub-claim used
    in Q10's row-disposition recommendation.
  - `runtime/__init__.py:1319-1342,1348-1380` — the opening-window
    fail-closed SHORT gate reads `intraday_state_engine`'s bounds
    (`_ORB_START`, `_NOISE_END`) rather than redefining them, and
    fails closed only inside `[09:30, 09:45)` ET — confirmed.

- **Q12 (statements unavailable in v1) — CONFIRMED** as a synthesis of the
  Q1-Q11 evidence above; no new citations to independently check beyond those
  already verified.

## Not independently re-checked

A small number of Q1-Q11 sub-bullets cite ranges I did not individually pull
(e.g. the exact byte range of `runtime/__init__.py:2099-2108` for the Sunday
skip vs. `2077-2089` for the writer — both were in fact read together and
both confirmed). I did not find any citation, across the ranges I did check,
that failed to match its described content — there is no basis in what I
checked to suspect the handful of unchecked sub-bullets diverge.
