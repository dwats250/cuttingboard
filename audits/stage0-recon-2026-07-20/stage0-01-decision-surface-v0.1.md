> Orchestrator note: Codex self-reported it could not detect its own
> CLI banner/session id (a known blind spot -- the banner is printed
> by the CLI wrapper, outside the model's own context). The actual
> session id, extracted from stdout by the orchestrator, is
> `019f8315-76ba-7e11-832f-e891729cdff2`. Rollout: `rollout-2026-07-20T22-10-49-019f8315-76ba-7e11-832f-e891729cdff2.jsonl`.
> Verification disposition: CORROBORATED -- every tool call in the
> rollout is a local `exec` (git/rg/sed/python3/pytest); no MCP,
> plugin, browser, or network tool call appears anywhere; the
> self-reported memory-file reads (MEMORY.md, memory_summary.md,
> and any skill files) match the rollout's actual reads exactly.
>
---

## Header
- Repository and inspected SHA: dwats250/cuttingboard @ 771f730839b00b0537327f9696210275f36cd790
- Session/model: Could not detect a CLI banner; best identification: Codex, GPT-5; session id could not be determined.
- Repository access: READ
- Test/trace capability: YES — `PYTHONDONTWRITEBYTECODE=1 pytest --collect-only -q -p no:cacheprovider` failed because the read-only sandbox has no usable temporary directory; `python` was unavailable; an injected-data `PYTHONDONTWRITEBYTECODE=1 python3` trace of `watch.compute_intraday_metrics` succeeded without live fetches or artifact writes.
- Prior findings visible before first pass: YES — the supplied `/home/dustin/.codex/memories/memory_summary.md` contained a prior CuttingBoard audit/commit summary. Before the first source pass, conclusion-bearing content read from `audits/*`: none; `docs/DECISIONS.md`: none; `docs/PROJECT_STATE.md`: none. Later broad-search snippets from `docs/DECISIONS.md:1833,3182` and `docs/audit/gate_recon_2026-06-12.md:657;717-721;766-770;812-829;839;843-861;905-915;928-932;940-975` were not used as evidence.
- Evidence classes used: STATIC@771f730839b00b0537327f9696210275f36cd790, RUNTIME@771f730839b00b0537327f9696210275f36cd790, HYPOTHESIS, OPERATOR
- Questions owned by this artifact: Q1-12
- Explicit out-of-scope tracks: stage0-02-evaluation-v0.1.md, stage0-03-scheduler-v0.1.md, stage0-04-gex-v0.1.md, stage0-05-governance-debt-v0.1.md

## Memory provenance (mandatory -- per docs/DECISIONS.md 2026-07-19: a leg that cannot produce this is not a fresh-context leg)
- Memory surface loaded, enumerated: `/home/dustin/.codex/memories/memory_summary.md` (supplied at session start); `/home/dustin/.codex/memories/MEMORY.md` (queried); `/home/dustin/.agents/skills/gitnexus-exploring/SKILL.md` (queried). No rollout summary was opened.
- Checked against this dispatch's excluded-content list: N/A for a producing/recon leg -- no snapshot-exclusion set was prepared for this dispatch (that mechanism applies only to the separate verification session isolating itself from producer conclusions). The "prior findings visible" line above is this artifact's applicable substitute disclosure.
- Persisted anything back to memory this run: NO
- Session id: could not determine it

## MCP / tool-call audit
- none

## Authority

### Q1. Exact producer and field ownership

- **Global permission statement:** `cuttingboard.runtime._build_and_finalize_contract` owns `contract["system_state"]["permission"]`, plus its paired `outcome` and `reason`, at `cuttingboard/runtime/__init__.py:791-800`.  
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — `delivery/payload.py:34-40,120-131` relays that exact field to `payload["summary"]["permission"]`.
  - Reachability: finalized contract → payload → renderer/consumer.
  - Current unavailable/failure behavior: there is no per-field unavailable token; malformed finalized contracts fail validation before downstream publication at `runtime/__init__.py:810-817`, while unknown posture falls back to “No new trades permitted.”
  - Falsifier: a later finalizer mutates `system_state.permission`, or a consumer bypasses the finalized contract.
  - PRD consequence: HYPOTHESIS — a Control Card may display this only as global posture permission, not as per-symbol authorization.

- **Per-symbol permission statement:** `cuttingboard.execution_policy.apply_execution_policy` owns `TradeDecision.policy_allowed` and `policy_reason` at `cuttingboard/execution_policy.py:157-199`; `contract._build_trade_candidates` serializes them to `trade_candidates[*]` at `cuttingboard/contract.py:351-372`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — `trade_visibility.build_visibility_map` consumes `policy_allowed` and `policy_reason` at `cuttingboard/trade_visibility.py:47-68`.
  - Reachability: execution policy → finalized candidate → visibility/consumer surfaces.
  - Current unavailable/failure behavior: no candidate means no row; `orb_unavailable` is explicitly retained as a policy reason but is not itself a hard block at `execution_policy.py:231-236`.
  - Falsifier: a candidate reaches the contract without those schema-required fields, or another producer overwrites them.
  - PRD consequence: HYPOTHESIS — a card must label this “candidate permission,” never collapse it into global posture.

- **Descriptive market-context statement:** `cuttingboard.market_map._build_symbol_record` owns `symbols[symbol].{grade,bias,structure,setup_state,watch_zones,trade_framing,...}` at `cuttingboard/market_map.py:159-244`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — `_render_candidate_card` consumes the header and framing fields at `cuttingboard/delivery/dashboard_renderer.py:1822-1910`.
  - Reachability: market-map builder → market-map artifact → candidate card.
  - Current unavailable/failure behavior: missing quote/derived/structure yields `grade=F` and `setup_state=DATA_UNAVAILABLE` at `market_map.py:187-210`; missing intraday metrics removes intraday watch zones at `market_map.py:247-262,319-340`.
  - Falsifier: a renderer derives the same fields independently or a different artifact becomes the declared writer.
  - PRD consequence: HYPOTHESIS — retain these only as descriptive context, not as a trade-permission statement.

- **Session-anchor/lifecycle statement:** no current durable single producer owns a card-ready `session_date + ORB + full-session VWAP + lifecycle` record. `watch.IntradayMetrics` holds transient `orb_high`, `orb_low`, and `vwap` at `cuttingboard/watch.py:212-229`; `IntraState` separately holds similar transient fields at `cuttingboard/intraday_state_engine.py:512-534`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — neither inspected path writes those fields to a dedicated observation artifact.
  - Reachability: current fields reach market-map/decision execution in-memory, not a single durable Control Card source.
  - Current unavailable/failure behavior: this proposed statement is unavailable in v1.
  - Falsifier: a pinned source path writes a versioned session-observation artifact with one declared writer and consumers.
  - PRD consequence: HYPOTHESIS — do not scope a card statement until one writer is explicitly assigned.

### Q2. Explicitly non-authoritative overlapping producer

- The overlapping `cuttingboard.trend_structure.build_trend_structure_snapshot` field `symbols[*].vwap` must be non-authoritative for session-anchor claims. It calculates VWAP only from supplied intraday history at `cuttingboard/trend_structure.py:49-71,245-288`, while its normal history collector calls daily `fetch_ohlcv` at `cuttingboard/runtime/__init__.py:2052-2068`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — daily/non-intraday history resolves VWAP as `NOT_COMPUTED` at `trend_structure.py:120-136`; its declared consumer is renderer/human review only at `docs/artifact_flow_map.md:107-115`.
  - Reachability: trend-sidecar artifact → renderer; no session-anchor contract.
  - Current unavailable/failure behavior: `vwap=None` with `NOT_COMPUTED` or `DATA_UNAVAILABLE`, depending on input shape.
  - Falsifier: an explicit schema/ownership transfer makes this producer the proven full-session anchor writer.
  - PRD consequence: HYPOTHESIS — declare trend-structure VWAP non-authoritative for the Control Card.

- `market_map.symbols[*].watch_zones` is also a non-authoritative presentation projection: it filters levels beyond 5% and rounds survivors at `cuttingboard/market_map.py:343-356`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — it reaches the level diagram through `dashboard_renderer.py:1919-1954`.
  - Current unavailable/failure behavior: a legitimate but distant anchor can be omitted.
  - Falsifier: the map schema declares unfiltered session-anchor provenance and becomes the sole writer.
  - PRD consequence: HYPOTHESIS — do not use this list as the source of a session-fact statement.

### Q3. Time basis, universe, and unavailable semantics

- The current intraday input basis is the latest regular session, selected in Eastern time from 09:30 through 15:30 and then converted to UTC at `cuttingboard/ingestion.py:170-207`. The market-map artifact separately carries `generated_at`, `session_date`, and `source.run_at_utc` at `cuttingboard/market_map.py:144-155`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — this supports a time basis of ET session date plus UTC observation timestamps, not an undated rolling buffer.
  - Reachability: provider frame → intraday consumers; market-map provenance → renderer.
  - Current unavailable/failure behavior: `fetch_intraday_bars` returns `None` on per-symbol failure; `watch.compute_intraday_metrics` returns `None` for missing/short/invalid inputs at `watch.py:146-181`.
  - Falsifier: a current producer persists a different session key or all-session history contract.
  - PRD consequence: HYPOTHESIS — a future observation record should carry `session_date` in ET, `observed_at_utc`, and explicit source freshness.

- The fixed six-symbol universe is already shared: `config.TREND_STRUCTURE_SYMBOLS = ("SPY","QQQ","GDX","GLD","SLV","XLE")` at `cuttingboard/config.py:207-209`, matching `market_map.PRIMARY_SYMBOLS` at `cuttingboard/market_map.py:19-20`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — runtime iterates the former independently of candidates at `runtime/__init__.py:2052-2068`.
  - Reachability: fixed universe → sidecar snapshot / market-map records.
  - Current unavailable/failure behavior: absent history remains absent and resolves to existing unavailable sentinels rather than removing the fixed-universe contract.
  - Falsifier: either tuple diverges or a source replaces it with candidate-only enumeration.
  - PRD consequence: HYPOTHESIS — use one declared fixed tuple; do not infer scope from qualified candidates.

- Unavailable must mean absent, incomplete, or unprovable source data, not elapsed time in a rolling buffer.
  - OPERATOR — Charter invariant I4 requires that a formed opening range remains a session fact; source-bar loss is a data deficiency, never `AGED_OUT`.
  - Falsifier: a governing ruling changes I4.
  - PRD consequence: HYPOTHESIS — represent `UNAVAILABLE` with a reason and freshness/provenance, separate from formation state.

## Observation producer

### Q4. Fixed-universe producer outside decision guards in both paths

- The existing trend-sidecar call sites are the demonstrated placement pattern. The premarket path invokes `_refresh_trend_structure_sidecar(...)` after decision construction at `cuttingboard/runtime/__init__.py:1172-1188`; the hourly path invokes `_write_trend_structure_snapshot(...)` in its unconditional hourly-artifact block at `runtime/__init__.py:537-562`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — both calls use `_collect_trend_structure_history(ohlcv)`, which iterates the fixed universe regardless of candidate set/posture at `runtime/__init__.py:2052-2068`.
  - Reachability: premarket MODE_LIVE and hourly path both reach a sidecar writer after, rather than inside, the decision-gate chain.
  - Current unavailable/failure behavior: premarket skips fixture/Sunday modes at `runtime/__init__.py:2099-2108`; writer failures are logged and swallowed at `runtime/__init__.py:2077-2089`.
  - Falsifier: moving either call inside qualification/execution gates or making its symbol set candidate-scoped.
  - PRD consequence: HYPOTHESIS — a new observation-only producer can use these two post-decision call-site seams without feeding decisions.

### Q5. Atomic write pattern

- Yes. `_write_trend_structure_snapshot` writes `<target>.tmp` then calls `replace(target)` at `cuttingboard/runtime/__init__.py:2085-2088`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — this is an existing atomic sidecar pattern.
  - Reachability: builder output → temporary file → canonical snapshot path.
  - Current unavailable/failure behavior: exceptions are logged and no explicit failure record is emitted; the writer does not partially publish its newly built JSON.
  - Falsifier: a proposed writer uses direct target writes or propagates errors into decision execution.
  - PRD consequence: HYPOTHESIS — any observation artifact should use this replacement pattern and expose its own freshness/failure semantics.

### Q6. Full-session bars versus persisted anchors

- The upstream yfinance request can form a whole latest-session frame before truncation, but the current public `fetch_intraday_bars` result is explicitly `frame.tail(120)` at `cuttingboard/ingestion.py:194-207`. `watch._bars_from_df` truncates again with `df.tail(MAX_INTRADAY_BARS)` at `cuttingboard/watch.py:356-371`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — current consumers cannot rely on full-session bars after the opening data drops from the 120-bar window.
  - RUNTIME@771f730839b00b0537327f9696210275f36cd790 — injected 391 one-minute bars with true opening ORB high `110.0`; `watch.py` retained 120 bars beginning `2026-07-20T18:01:00+00:00` and emitted ORB high `777.0`.
  - Reachability: provider → `watch` metrics → market-map watch zones and execution ORB policy state.
  - Current unavailable/failure behavior: missing early bars silently produce a positional substitute rather than an unavailable result.
  - Falsifier: the same trace returns `110.0`, or both truncations are removed/replaced by timestamp-based session selection.
  - PRD consequence: HYPOTHESIS — least invasive preservation is an observation-only per-session record that retains immutable ORB high/low after formation and VWAP cumulative PV/volume plus last-observed timestamp for deduplication. If it starts after the opening window without prior state, report `UNAVAILABLE`; do not invent or label an anchor `AGED_OUT`.

### Q7. Truthful lifecycle schema

- No current schema is authoritative: `compute_intraday_state` returns `None` before 09:45 and raises for fewer than five ORB-window bars at `cuttingboard/intraday_state_engine.py:400-438`; `watch.compute_intraday_metrics` returns bare `None` for several failure modes at `cuttingboard/watch.py:146-181`. These are not durable lifecycle records.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — the two modules also use different ORB-selection rules: timestamp window at `intraday_state_engine.py:124-142` versus first five retained bars at `watch.py:164-166`.
  - Reachability: ephemeral computation paths only.
  - Current unavailable/failure behavior: no card-ready distinction among pre-open, forming, and source failure.
  - Falsifier: a current persisted artifact contains a declared lifecycle schema with those distinctions.
  - PRD consequence: HYPOTHESIS — use two axes, not one overloaded state:
    - `formation_state=PRE_OPEN`: no regular-session observation yet.
    - `formation_state=FORMING`: opening-window bars observed but formation not proven; provisional values are not final anchors.
    - `formation_state=FORMED`: ORB high/low are immutable session facts; VWAP remains a current cumulative observation.
    - `data_status=UNAVAILABLE` with `failure_reason` may coexist with any formation state. After formation it preserves `FORMED` and the already-established ORB; it does not replace it with `AGED_OUT`.

## Suspected defects

### Q8. Runtime trace of positional ORB contamination in `watch.py`

- Yes. `watch.compute_intraday_metrics` takes `bars[:N_RANGE]` as ORB at `cuttingboard/watch.py:156-166`, while `_bars_from_df` first keeps only the latest 120 bars at `watch.py:356-371`.
  - RUNTIME@771f730839b00b0537327f9696210275f36cd790 — the injected trace described in Q6 reproduced `expected_opening_orb_high=110.0` versus `watch_orb_high=777.0` after the retained frame began at 14:01 ET.
  - Reachability: `market_map._watch_zones` copies `intraday.vwap`, `orb_high`, and `orb_low` at `cuttingboard/market_map.py:319-327`; execution policy receives the same `IntradayMetrics` ORB values at `runtime/__init__.py:1403-1425`.
  - Current unavailable/failure behavior: silent false ORB values; no timestamp validation or unavailable state is emitted.
  - Falsifier: an equivalent full-session trace returns the actual opening ORB, or the implementation filters ORB bars by the 09:30–09:35 ET timestamps.
  - PRD consequence: HYPOTHESIS — any scoped remediation must establish timestamp/session provenance before exposing ORB as a card fact.

### Q9. Hourly reuse of stale premarket watch-zone inputs

- No, by static inspection. `_execute_notify_run` initializes `intraday_metrics = {}` at `cuttingboard/runtime/__init__.py:384-389`, never calls `compute_all_intraday_metrics` in its hourly branch, and passes that empty mapping into a newly built hourly market map at `runtime/__init__.py:537-548`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — hourly output reads/writes `LATEST_HOURLY_MARKET_MAP_PATH`, not the shared premarket map, at `runtime/__init__.py:550-557`.
  - Reachability: hourly artifact → its own market-map artifact. Previous hourly map is used only for lifecycle injection.
  - Current unavailable/failure behavior: hourly maps omit intraday VWAP/ORB zones because `_watch_zones` adds them only when `intraday is not None` at `cuttingboard/market_map.py:319-340`; derived EMA zones may still appear.
  - Falsifier: a path merges prior/premarket `watch_zones` into `hourly_market_map`, or passes prior intraday metrics into `build_market_map`.
  - PRD consequence: HYPOTHESIS — a Control Card should distinguish fresh hourly unavailability from stale reuse; the current code supports the former, not the latter.

## Control Card

### Q10. Existing-row disposition

- The current relevant surface is `_render_candidate_card`, not a declared Control Card. It renders header fields at `cuttingboard/delivery/dashboard_renderer.py:1822-1839`, `IF NOW` at `1841-1848`, market-map lifecycle at `1850-1864`, `IN →` / `OUT →` at `1866-1889`, and `REASON` / `PLAY` / `WATCH` details at `1891-1910`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — these fields are reachable only for high-grade cards; low-grade cards instead render symbol/bias/structure and failure reason at `1806-1820`.
  - Current unavailable/failure behavior: rows are conditionally omitted, and the source map can yield `DATA_UNAVAILABLE`.
  - Falsifier: a current source/artifact defines a different Control Card contract.
  - PRD consequence: HYPOTHESIS — row disposition for a new Control Card should be:
    - Retain: symbol identity only; do not treat market-map `current_price` as a guaranteed live anchor because lifecycle can carry a prior price forward at `cuttingboard/market_map_lifecycle.py:82-85`.
    - Absorb: header `grade`, `setup_state`, `bias`, `structure`, and `IF NOW` into one explicitly descriptive market-map-context line.
    - Reduce: `IN →` / `OUT →` and `REASON` / `PLAY` / `WATCH` to secondary descriptive detail, not permission.
    - Remove from the Control Card: the market-map `LIFECYCLE` line. It may remain on the existing candidate card, but it is not session-anchor lifecycle.

### Q11. Market-state versus permission transitions

- `market_map_lifecycle.inject_lifecycle` transitions only `grade` and `setup_state` across artifacts at `cuttingboard/market_map_lifecycle.py:51-80`; the renderer displays those transitions at `dashboard_renderer.py:1850-1864`.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — these are presentation-classification transitions, not genuine market-session transitions.
  - Reachability: current/previous market-map comparison → renderer/notification lifecycle text.
  - Current unavailable/failure behavior: first snapshot yields `UNKNOWN`; missing current price can be backfilled.
  - Falsifier: the lifecycle block begins carrying timestamped source-bar/session-anchor facts.
  - PRD consequence: HYPOTHESIS — do not label grade or setup changes as market-state transitions on the Control Card.

- The genuine market-state classification currently available in memory is `IntraState.state` (`RANGE`, `FAILED_EXPANSION`, `EXPANSION_CONFIRMED`) at `cuttingboard/intraday_state_engine.py:478-534`; a future ORB `PRE_OPEN → FORMING → FORMED` progression would likewise be market state.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — it is unavailable before 09:45 or on insufficient opening bars, and is not a card artifact.
  - Reachability: runtime short-permission path at `runtime/__init__.py:1348-1380`.
  - Falsifier: a source redefines those fields as policy-only values.
  - PRD consequence: HYPOTHESIS — market state and source health need separate fields.

- `IntraState.permission_state`, `trades_allowed`, runtime `downside_permission`, `TradeDecision.policy_allowed`, and `system_state.permission` are permission transitions, not market state.
  - STATIC@771f730839b00b0537327f9696210275f36cd790 — runtime removes short candidates when downside permission is false at `runtime/__init__.py:1371-1380`; execution policy can then block a decision at `execution_policy.py:179-199`.
  - Current unavailable/failure behavior: the opening-window short path fails closed when intraday state is unavailable, then otherwise uses its defined unavailable handling at `runtime/__init__.py:1319-1342`.
  - Falsifier: a policy field is shown to derive solely from immutable session facts without a gate.
  - PRD consequence: HYPOTHESIS — present permissions on a separate axis from market-state transitions.

### Q12. Statements unavailable in v1

- The following remain unavailable as truthful v1 Control Card statements:
  - durable, correct late-day ORB high/low;
  - full-session VWAP and price-versus-VWAP after the rolling window loses early bars;
  - a durable `PRE_OPEN` / `FORMING` / `FORMED` lifecycle;
  - an exact source-failure reason for absent session anchors;
  - a “live NOW price” claim sourced from final market-map data without freshness/provenance.

- STATIC@771f730839b00b0537327f9696210275f36cd790 — current `watch.py` has the positional defect, `trend_structure.py` may truthfully produce `NOT_COMPUTED` VWAP, and neither module writes a single session-observation artifact.
  - Reachability: current anchor-like values are transient or filtered projections, not one canonical card source.
  - Current unavailable/failure behavior: `None`, `NOT_COMPUTED`, `DATA_UNAVAILABLE`, omission, or silent positional substitution, depending on path.
  - Falsifier: a versioned artifact at this SHA with one writer, full provenance, persisted session state, and a renderer consumer.
  - OPERATOR — I4 prohibits replacing any formed opening-range fact with `AGED_OUT`.
  - PRD consequence: HYPOTHESIS — leave these statements visibly unavailable until their authority and lifecycle contract are independently established.

## NO CLAIM
stage0-02-evaluation-v0.1.md — I make no claim about this track.
stage0-03-scheduler-v0.1.md — I make no claim about this track.
stage0-04-gex-v0.1.md — I make no claim about this track.
stage0-05-governance-debt-v0.1.md — I make no claim about this track.

