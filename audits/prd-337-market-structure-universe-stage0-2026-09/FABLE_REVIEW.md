# Market Structure Universe v1 -- Fable 5.1 adversarial design review

Status: REVIEW RECORD -- design ruling for the Opus IMPLEMENT session. Grants no
Gate A, no merge authority, and does not stand in for GOV-2's commissioned Codex
review or exact-head confirmation events (Helm reconciles reviewer seats).
Date: 2026-09-06 PT.
Reviewer: Fable 5.1 (Claude Code), fresh session, adversarial/architectural seat.
Independence: this reviewer did not author the packet, shares no session with
Astra, and made no production edit. Every claim below was checked against the
inspected head, not taken from the brief.

Reviewed artifact: `ASTRA_REVIEW_BRIEF.md` at branch
`claude/prd-337-ns4c-leadership-v0`, head
`8c403bb4dddee320e938d95d4459db4f9360b210` (== origin; base main
`f87bda756314f47ea9de341ebe26b6512e8cb4c2`). Draft PR #325 remains draft.
Also read: `audits/ns4c-leadership-v0-owner-ratification-2026-09/OWNER_RATIFICATION.md`.

Evidence sources beyond the six fenced files: `cuttingboard/ingestion.py`
(fetch/retry/timeout), `cuttingboard/validation.py` (PRICE_BOUNDS site),
`cuttingboard/normalization.py`, `.github/workflows/hourly_alert.yml`,
`tests/test_observe_only_isolation.py`, `tests/test_hourly_alert.py` (harness),
CI job logs 101451347799 / 101103613660 (cuttingboard.yml live step), yfinance
1.2.1 source in the shared venv, and one bounded live fetch trial (section 4).

---------------------------------------------------------------------------

## 1. VERDICT

**ACCEPT WITH CHANGES -- READY AFTER DESIGN CORRECTIONS.**

Astra's direction is right: one human-authored registry, explicit measurement
membership separate from personal attention, the observation fetch derived (not
hand-listed), exact-projection admission kept strict, one evolved carrier. The
packet is over-built in four places (role ontology, carrier metadata, the
personal-only carrier row and its fetch, the renderer in the fence) and under-
specified in one (the observation fetch has no elapsed-time bound). The corrected
design in section 3 is smaller than Astra's and closes the timing exposure inside
the existing fence. No new owner decision is required to implement it; the
standing owner acts (membership/benchmark ratification via Gate A on the
successor PRD) remain owner-held as GOV-2 already requires.

---------------------------------------------------------------------------

## 2. FINDINGS

Severity key: BLOCKER / REQUIRED BEFORE IMPLEMENTATION / NON-BLOCKING / OPTIONAL.

### F1 -- REQUIRED. Observation fetch has no elapsed-time bound (the timing risk is real, and fixable in-fence)

Evidence:
- `ingestion.py:333-370` `_try_yfinance_quote`: 3 attempts, 2 s backoff, each
  attempt through `_run_with_timeout(fn, 10)`.
- `ingestion.py:616-623` `_run_with_timeout` uses `with ThreadPoolExecutor(...)`;
  the context exit is `shutdown(wait=True)`, so after the 10 s `TimeoutError` is
  raised the caller still blocks until the hung worker returns. The configured
  10 s is NOT an elapsed ceiling. Astra's claim CONFIRMED.
- yfinance 1.2.1 (`.venv`): `fast_info.last_price` triggers
  `history(period="1y")` (one chart request, requests timeout 10 s) plus a
  per-ticker tz lookup (timeout 10 s) and cookie/crumb bootstrap (timeout 30 s,
  cached per process); `YfConfig.network.retries == 0`.
- `runtime/__init__.py:2797-2815`: sequential per-symbol loop, no budget.
- `.github/workflows/hourly_alert.yml`: NO `timeout-minutes` on the job
  (GitHub default 360 min) and `concurrency: group hourly-alert,
  cancel-in-progress: false`, so a stalled run makes the NEXT slot's heartbeat
  queue behind it.
- Sequence in `_execute_notify_run`: notification sent (:703) -> hourly
  contract/summary written (:747) -> market map (:764) -> bars/trend sidecars
  (:797-:808) -> observation fetch + watchlist write (:813) -> A1-P intraday
  producer (:817-:868) -> return. The observation fetch runs AFTER every
  decision-authoritative output of the current run is durable.

Measured cost (nominal):
| Source | Per-symbol | Notes |
|---|---|---|
| CI live pipeline log 101451347799 (2026-09-06) | 0.16-0.28 s | 25 yfinance symbols, all attempt=1 |
| CI live pipeline log 101103613660 (2026-09-04) | 0.17-0.47 s | same |
| Local live trial, the 12 proposed extra symbols | 0.30-0.68 s, 4.76 s total | all succeeded, this session |

Worst cases (derived, not measured):
| Case | Per symbol | 12 extra symbols |
|---|---|---|
| Nominal | ~0.2-0.4 s | ~3-5 s |
| Provider failing fast on every attempt | 3x10 s + 2x2 s = 34 s | ~6.8 min |
| Pathological socket hang (executor waits out inner timeouts) | ~3 x (60-90 s) + 4 s = ~3-5 min | ~40-60 min |

Consequence: the pathological case exceeds the hourly cadence, delays the
dashboard publish and A1-P producer of THIS run, and (via the concurrency group)
delays the NEXT slot's decision-authoritative alert. Quotes stay isolated; wall
clock does not. Note the same pathology already exists for the 31-symbol decision
loop (`fetch_all`, identical mechanism); the design adds ~40% more sequential
fetches to a run, not 6.5x -- Astra's 2 -> 13 framing compares the wrong
baseline. The correct baseline is 33 sequential quote fetches per hourly run
today -> 45 under this design (12 extras after the UCO cut in F4).

Correction (in-fence, `runtime/__init__.py` only): add a best-effort elapsed
budget to `_fetch_observe_only_quotes`, mirroring the existing A1-P pattern
(`_INTRADAY_ACQUISITION_BUDGET_SECONDS`, :2672 / :855-:861):
`_OBSERVE_ONLY_FETCH_BUDGET_SECONDS = 60.0`; check `time.monotonic()` before
EACH symbol; once exceeded, log one warning naming how many of how many were
attempted and STOP issuing fetches (remaining rows render `n/a`). Never raise.
This bounds the incremental exposure to budget + one symbol's worst case
(~6 min pathological, ~5 s nominal), inside the hourly cadence. See section 4
for the explicit ruling. No ingestion.py / provider / workflow change is
required for rollout.

### F2 -- REQUIRED. The five-role tuple is an ontology; two booleans answer the product question

Evidence: brief section 3 proposes `roles: tuple[str, ...]` over PERSONAL,
MARKET_STRUCTURE, CROSS_ASSET, SECTOR_BENCHMARK, LEADERSHIP_CONSTITUENT, plus
the rule that the last three "require MARKET_STRUCTURE", plus `primary_group`
re-scoped to MARKET/SECTORS/REAL_ASSETS/LEADERS/PERSONAL.

Problems:
- CROSS_ASSET, SECTOR_BENCHMARK, LEADERSHIP_CONSTITUENT are 1:1 with the display
  groups REAL_ASSETS, SECTORS, LEADERS. Three of five roles duplicate
  `primary_group`; the "requires MARKET_STRUCTURE" rule exists only to police
  that duplication.
- SECTOR_BENCHMARK is false: sector ETFs are benchmarked TO SPY; they are not
  benchmarks in this design.
- LEADERSHIP_CONSTITUENT and the LEADERS/SELECTED LEADERS label import NS-4C's
  verdict word ("leading") into a static basket. That is exactly the accidental
  semantics the charge forbids.
- An open string vocabulary invites a sixth role without a schema change.

Correction: replace `roles` with two explicit booleans on `UniverseInstrument`:
`personal: bool` (owner attention; no consumer in this precursor) and
`market_structure: bool` (measurement membership; the ONLY field any producer
reads). Keep `primary_group` as the display group for measurement rows, closed
vocabulary MARKET / SECTORS / METALS / MEGACAPS, and `None` for non-measurement
rows. Add `benchmark_symbol: str | None`. No `roles`, no PERSONAL group, no
REAL_ASSETS/LEADERS labels. Full shape in section 3.

### F3 -- REQUIRED. Carrier metadata over-reach (roles, benchmark, rationale in JSON)

Evidence: brief section 6 row keys `symbol, roles, benchmark_symbol,
primary_group, registry_index, rationale, current_price, daily_change_pct`, and
the consumer must validate "exact identity metadata against the current
projection (roles, benchmark, group, rationale, index)".

Consequence: every extra serialized field is an extra rejection surface with no
reader. The artifact is run-local (not restored, not staged;
`tests/test_ci_artifact_hygiene.py:867-876`), so "auditable benchmark context"
has no audience. Persisting `benchmark_symbol` in the carrier also tempts NS-4C
to read relationships from JSON instead of the authored registry projection.

Correction: v3 row keys are exactly `symbol, primary_group, registry_index,
current_price, daily_change_pct`. Relationships (benchmark) and roles live only
in the registry and its sidecar projections. Drop `sector_theme` and
`watch_reason`; do not add `roles`, `benchmark_symbol`, `rationale`.

### F4 -- REQUIRED. Personal-only UCO row in the carrier is a fetch with no reader

Evidence: brief section 4-6: UCO stays enabled/PERSONAL, is serialized as a
personal-only row, is one of the 13 extra fetches, and "No PERSONAL dashboard
card is proposed"; the card renders MARKET_STRUCTURE rows only.

Consequence: one network fetch per hour, one carrier row, one "personal-only row
must be filtered" consumer rule, and Astra's own open question 16, all to carry
data nothing displays.

Correction: the carrier serializes ONLY the measurement projection (22 rows).
The personal projection is a registry/sidecar constant (`PERSONAL_SYMBOLS`, 11)
with no carrier row and no fetch until a consumer PRD asks for one. Extra
fetches drop from 13 to 12. Owner-visible consequence (already implied by
Astra's design): the UCO chip leaves the dashboard.

### F5 -- REQUIRED. `dashboard_renderer.py` does not need to be in the fence

Evidence: `dashboard_renderer.py:3599-3610` derives PARTICIPATION counts from
`movement_card.build_movement_card` and emits `render_fragment`; grep finds no
legacy group token, no `12`, no `/12` in the renderer or `market_state_panel.py`
code (only docstrings). `.kv-grid{grid-template-columns:max-content 1fr}` (:1116)
already wraps the value cell.

Correction: remove `dashboard_renderer.py` from the production fence. The only
rendering change belongs in `movement_card.py:render_movement_card_html`: emit
each chip with its internal space as `&nbsp;` and join chips with a plain space,
so a wrapped SECTORS row breaks between chips, never inside `XLRE +0.8%` (today's
`" &nbsp; "` join allows an intra-chip break). Keep the `MovementCard.groups`
text chips with a plain space so `market_state_panel._participation`'s
`endswith(" n/a")` contract is untouched. If the 390 px browser check shows
horizontal overflow, that is a STOP and fence amendment, not a silent edit.

### F6 -- REQUIRED. Basket label and group vocabulary must be size-descriptive, not verdict-descriptive

Evidence: charge Q4/Q5; brief uses LEADERS / "SELECTED LEADERS".

Ruling: group id and display label `MEGACAPS`. It states what the six are (the
six largest non-TSLA US mega-caps the owner selected), claims nothing about
leadership, and does not mislabel META/GOOG (Communication Services) or AMZN
(Consumer Discretionary) as "technology". Rationales must name the actual GICS
sector per row. The basket is owner-authored, not a rule (no "top-N by weight"
inference); record that in the module docstring so AVGO/TSLA absence is not read
as an error.

### F7 -- REQUIRED. Benchmark map accepted; the product question and the self-weight caveat must be written down

Ruling on each relationship:
- QQQ -> SPY; all 11 sectors -> SPY: correct for "sector/growth relative to broad
  market". Anchors SPY -> null, GLD -> null: correct (no meaningless self-zero).
- SLV -> GLD, GDX -> GLD: correct for "silver / miners relative to gold".
- AAPL/MSFT/NVDA/META/AMZN/GOOG -> QQQ: ACCEPTED, with the product question
  stated explicitly: "is this mega-cap moving with or against the growth complex
  it dominates". Sector ETFs would be LESS truthful, not more: these six are a
  larger share of XLK/XLC/XLY than of QQQ, so a sector benchmark is more
  self-referential. SPY would answer a different question (vs broad market).
  Caveat to record in docs: because the six are a large fraction of QQQ, small
  spreads are partly self-comparison; NS-4C must not over-read them.
- Consequence for NS-4C: `relative_daily_move` is defined only where both rows
  are non-null; anchors produce no comparison. Not built here.

### F8 -- REQUIRED. Registry validation is import-time and must be a pure function with a red test per rule

Evidence: brief section 6 lists closure/duplicate/vocabulary rules without
naming where they run or fail.

Correction: `validate_registry(registry) -> None` in `watchlist_sidecar.py`
(pure; raises `ValueError`), called once at import before building projections
(fail-loud, consistent with the existing `_PRIMARY_GROUP_TO_THEME[...]` KeyError
posture). Rules in section 3.6. Each rule ships a test that constructs a bad
registry tuple and asserts the raise; no cycle detector beyond "chain reaches a
null anchor within 3 hops".

### F9 -- REQUIRED. `trade_eligible` must be explicitly declared non-authoritative

Evidence: Astra proposes `False` for new rows including AAPL while
`config.HIGH_BETA` contains AAPL as a live trade candidate.

Consequence: a field literally named `trade_eligible` that contradicts the
trading config is a TRUTH hazard for any future reader.

Correction: keep Astra's values (existing rows unchanged, new rows False) but
add to the module docstring: "PRD-308 registry-level flag; NO consumer; NOT
synchronized with `config.ALL_SYMBOLS`/`HIGH_BETA`; never read as the tradable
universe", and a test asserting no `cuttingboard` module reads
`.trade_eligible`. OPTIONAL owner cut (later, not here): retire the field.

### F10 -- NON-BLOCKING. Schema bump accepted; `source` rename rejected

`schema_version: 3` is justified (row shape and membership change). Renaming
`source` to `observation_universe` while the path stays
`logs/watchlist_snapshot.json` is inconsistent churn: keep `source: "watchlist"`
and document the file as the observation-universe snapshot in `SCHEMA_MAP.md`.
Exact-set identity already fails closed across versions in both directions.

### F11 -- NON-BLOCKING. Decision-invariance proof must run real decision stages on a non-empty fixture

Existing `test_runtime_observe_only_reaches_watchlist_not_decisions` patches
`normalize_all -> {}` and mocks regime/derived/router; it proves the merge
seam, not decision invariance. Specification in section 3.10 uses
`tests/test_hourly_alert.py:_full_quotes()` (13 real-shaped quotes) with
`validate_quotes`, `compute_regime`, `compute_all_derived`,
`resolve_sector_router` unpatched, paired runs, and byte comparison of every
durable hourly output. If the harness cannot run those stages unpatched, Opus
STOPS and reports; it does not weaken the comparison.

### F12 -- NON-BLOCKING. Membership: 22 accepted as bounded; no additions

- SPY, QQQ: two anchors, both already decision inputs; no new fetch.
- 11 sectors: all required; a sector foundation with a hole is a breadth lie
  later (NS-4D). XLC and XLRE are real Select Sector SPDRs.
- GLD, SLV, GDX: coherent block with an explicit anchor. Group renamed METALS
  (F2); "REAL ASSETS" invites USO/DBC creep with no product question.
- Six mega-caps: accepted as the owner-authored NS-4C substrate; they are 27%
  of the universe and 2 of 12 extra fetches (MSFT, GOOG). Cutting them would
  defer the only single-name leadership question the sequence exists to ask.
- Personal projection (11 = legacy 12 minus TSLA): PRD-308 records the legacy
  12 as owner-ratified on 2026-08-21 (AAPL removed, GOOG/UCO added), so it is
  an owner attention record, not an implementation accident. Carried forward
  by owner rule; zero runtime consumer; pinned by literal test only.
- TSLA: kept as a disabled tombstone per owner wording ("becomes disabled").
  OPTIONAL owner simplification: delete the row; git history is the record.

### F13 -- NON-BLOCKING. Observation fetch derivation location

Astra's derivation is correct and safe (it can only subtract from the
measurement set; it can never add to `ALL_SYMBOLS`). Place it as a module-level
constant in `runtime/__init__.py`, `_OBSERVE_ONLY_FETCH`, computed from
`MARKET_STRUCTURE_SYMBOLS` minus `config.ALL_SYMBOLS`, so a test can assert the
literal 12-tuple. No sidecar -> config import is needed; no config -> sidecar
import is allowed (cycle).

### F14 -- OPTIONAL. Workflow job timeout (outside fence)

`hourly_alert.yml` has no `timeout-minutes`. A 20-30 min job timeout would cap
the pre-existing decision-loop pathology as well. Outside this fence; owner
hygiene item, not a rollout condition.

### F15 -- OPTIONAL. GOV-2 reviewer-seat reconciliation

This review is the adversarial/architectural seat. The successor PRD is
MATERIAL (runtime/delivery seam + schema evolution); Helm decides whether a
commissioned Codex event and exact-head confirmation are still required before
Gate A. Not a design finding.

Nothing in the packet reached BLOCKER: no hidden path into decision authority
was found (imports: registry -> sidecar only; sidecar -> runtime writer seam and
movement_card only; `PRICE_BOUNDS` is consulted only in `validation.py:204`,
which observation symbols never reach; `normalize_quote` needs no per-symbol
config entry).

---------------------------------------------------------------------------

## 3. RATIFIED / REVISED DESIGN (one unambiguous design for Opus)

### 3.1 Registry shape (`cuttingboard/universe_registry.py`)

```python
PRIMARY_GROUPS = frozenset({"MARKET", "SECTORS", "METALS", "MEGACAPS"})
KNOWN_FUNCTIONS = frozenset({"crude_proxy"})           # unchanged

@dataclass(frozen=True)
class UniverseInstrument:
    symbol: str
    trade_eligible: bool          # PRD-308 inert flag; see F9 docstring
    functions: tuple[str, ...]
    primary_group: str | None     # display group iff market_structure, else None
    enabled: bool                 # observation activation only
    rationale: str
    personal: bool                # owner attention; no consumer in this PRD
    market_structure: bool        # measurement membership; the only produced flag
    benchmark_symbol: str | None  # authored relationship; null = anchor / none
```
No field defaults: every row states all nine values.

### 3.2 Final membership (registry order = serialization order, no rank)

| # | Symbol | group | personal | market_structure | benchmark | trade_eligible | enabled |
|---|---|---|---|---|---|---|---|
| 0 | SPY | MARKET | T | T | null | T (legacy) | T |
| 1 | QQQ | MARKET | T | T | SPY | T (legacy) | T |
| 2 | XLK | SECTORS | F | T | SPY | F | T |
| 3 | XLF | SECTORS | F | T | SPY | F | T |
| 4 | XLE | SECTORS | T | T | SPY | T (legacy) | T |
| 5 | XLI | SECTORS | F | T | SPY | F | T |
| 6 | XLY | SECTORS | F | T | SPY | F | T |
| 7 | XLP | SECTORS | F | T | SPY | F | T |
| 8 | XLV | SECTORS | F | T | SPY | F | T |
| 9 | XLU | SECTORS | F | T | SPY | F | T |
| 10 | XLB | SECTORS | F | T | SPY | F | T |
| 11 | XLRE | SECTORS | F | T | SPY | F | T |
| 12 | XLC | SECTORS | F | T | SPY | F | T |
| 13 | GLD | METALS | T | T | null | T (legacy) | T |
| 14 | SLV | METALS | T | T | GLD | T (legacy) | T |
| 15 | GDX | METALS | T | T | GLD | T (legacy) | T |
| 16 | AAPL | MEGACAPS | F | T | QQQ | F | T |
| 17 | MSFT | MEGACAPS | F | T | QQQ | F | T |
| 18 | NVDA | MEGACAPS | T | T | QQQ | T (legacy) | T |
| 19 | META | MEGACAPS | T | T | QQQ | T (legacy) | T |
| 20 | AMZN | MEGACAPS | T | T | QQQ | T (legacy) | T |
| 21 | GOOG | MEGACAPS | T | T | QQQ | T (legacy) | T |
| -- | UCO | None | T | F | null | T (legacy) | T |
| -- | TSLA | None | F | F | null | T (legacy) | F |

Counts: 24 rows, 23 enabled, 22 measurement, 11 personal, 12 extra fetches.
XLE keeps `functions=()`; UCO keeps `("crude_proxy",)`. Rationales: one honest
line each; MEGACAPS rows name the GICS sector (AAPL/MSFT/NVDA Information
Technology; META/GOOG Communication Services; AMZN Consumer Discretionary).

### 3.3 Personal projection rule
`PERSONAL_SYMBOLS = tuple(i.symbol for i in registry if i.enabled and i.personal)`
= `SPY QQQ XLE GLD SLV GDX NVDA META AMZN GOOG UCO` (11; registry order). Pinned
by literal test. Not serialized, not fetched, not rendered.

### 3.4 Benchmark map (as in 3.2)
QQQ->SPY; XLK XLF XLE XLI XLY XLP XLV XLU XLB XLRE XLC -> SPY; SLV, GDX -> GLD;
AAPL MSFT NVDA META AMZN GOOG -> QQQ; SPY, GLD -> null (anchors); UCO, TSLA ->
null. Exposed as `BENCHMARK_BY_SYMBOL: Mapping[str, str | None]` over the 22
measurement symbols (inert until NS-4C).

### 3.5 Sidecar projections (`cuttingboard/watchlist_sidecar.py`)
```text
MARKET_STRUCTURE_SYMBOLS : tuple[str, ...]                 # 22, registry order
MARKET_STRUCTURE_ROWS    : tuple[tuple[str, str, int], ...] # (symbol, primary_group, registry_index)
PERSONAL_SYMBOLS         : tuple[str, ...]                 # 11
BENCHMARK_BY_SYMBOL      : Mapping[str, str | None]        # 22 keys
build_watchlist_snapshot(normalized_quotes, generated_at) -> dict   # v3, 22 rows
validate_registry(registry) -> None                         # raises ValueError
```
`WATCHLIST_SYMBOLS` and `_PRIMARY_GROUP_TO_THEME` are removed; every consumer
(movement_card, tests, docs) is updated atomically. `registry_index` is the
0-based position within `MARKET_STRUCTURE_SYMBOLS`.

### 3.6 Registry validation rules (each with a red test)
1. symbols unique, non-empty, uppercase.
2. `enabled` implies (`personal` or `market_structure`).
3. `market_structure` implies `enabled` and `primary_group in PRIMARY_GROUPS`;
   not `market_structure` implies `primary_group is None`.
4. `benchmark_symbol` non-null implies `market_structure`; target is a
   `market_structure` symbol; target != self; following benchmarks reaches null
   within 3 hops.
5. `functions` subset of `KNOWN_FUNCTIONS`; enabled rows have non-empty rationale.
Literal pins (separate tests, so producer and consumer cannot co-drift): the
exact 22-tuple, the exact 11-tuple, the exact 12-tuple of extra fetches, all
11 sector symbols present, TSLA disabled, AAPL/MSFT measurement-not-personal,
UCO personal-not-measurement.

### 3.7 Observation fetch derivation and seam (`cuttingboard/runtime/__init__.py`)
```python
_OBSERVE_ONLY_FETCH: tuple[str, ...] = tuple(
    s for s in MARKET_STRUCTURE_SYMBOLS if s not in config.ALL_SYMBOLS
)   # == XLK XLF XLI XLY XLP XLV XLU XLB XLRE XLC MSFT GOOG (12)
_OBSERVE_ONLY_FETCH_BUDGET_SECONDS = 60.0
```
`_fetch_observe_only_quotes()`:
- asserts (fail within the observation boundary, log + return {}) that
  `_OBSERVE_ONLY_FETCH` is disjoint from `config.ALL_SYMBOLS`,
  `REQUIRED_SYMBOLS`, `HALT_SYMBOLS`, `NON_TRADABLE_SYMBOLS`,
  `TREND_STRUCTURE_SYMBOLS`;
- iterates `_OBSERVE_ONLY_FETCH` in order; before each symbol checks the
  monotonic budget; on breach logs one warning ("observe-only budget exhausted
  after k/12; remaining render n/a") and breaks;
- per-symbol `normalize_quote(fetch_quote(sym))` inside try/except (unchanged
  best-effort); admits a result only if `nq is not None and nq.symbol == sym`;
- returns a mapping whose keys are a subset of `_OBSERVE_ONLY_FETCH`.
Call site (:813) unchanged in shape: `{**normalized_quotes, **extras}` passed
ONLY to `_write_watchlist_snapshot`; because extras' keys are filtered, no
decision quote (e.g. SPY) can be overwritten in the watchlist mapping.
`config.OBSERVE_ONLY_SYMBOLS` and its comment are deleted. Nothing else in
config changes. HALT / daily / Sunday gating unchanged.

### 3.8 Carrier: `logs/watchlist_snapshot.json`, schema 3
```text
top-level exact keys: schema_version (3), source ("watchlist"), generated_at
                      (ISO-8601 tz-aware or null), symbols (dict)
symbols: exactly the 22 MARKET_STRUCTURE_SYMBOLS, insertion order
row exact keys: symbol, primary_group, registry_index, current_price
                (float | null), daily_change_pct (float | null, one decimal)
```
Missing quote -> both numeric fields null (never 0.0). Not restored, not
staged, hourly-only, atomic tmp+replace (unchanged).

### 3.9 Movement-card acceptance invariant (`cuttingboard/delivery/movement_card.py`)
Accept iff ALL of: `source == "watchlist"`; `schema_version` is int (not bool)
`== 3`; `generated_at` tz-aware; `symbols` is a dict whose key set == set of
`MARKET_STRUCTURE_SYMBOLS` (from the producer projection); for every expected
symbol the row is a dict with `symbol == key`, `primary_group` and
`registry_index` equal to `MARKET_STRUCTURE_ROWS`, `daily_change_pct` KEY
PRESENT and float-or-null (finite, not bool), `current_price` key present and
float-or-null. Any violation -> `None` (whole card suppressed, baseline-neutral).
Group order `("MARKET", "SECTORS", "METALS", "MEGACAPS")`; within group by
`registry_index`. Chip text unchanged (`SYM +X.X%`, `SYM 0.0%`, `SYM n/a`).
Rendering: chips emitted with `&nbsp;` inside and a plain space between (F5).
No wall clock. Coverage line becomes `22/22 captured`, `21/22 captured`, etc.,
derived exactly as today.

### 3.10 Decision-invariance proof (in `tests/test_observe_only_isolation.py`)
Paired runs of `_execute_notify_run(mode=MODE_LIVE, notify_mode=NOTIFY_HOURLY)`
using `tests/test_hourly_alert._setup_tmp_artifacts_with_market_map` and
`fetch_all -> {}`, `normalize_all -> _full_quotes()` (13 non-empty quotes),
`extract_fetch_failures -> {}`, `send_notification` captured; `validate_quotes`,
`compute_regime`, `compute_all_derived`, `resolve_sector_router` and the
qualification entry left REAL, each wrapped by a recording spy that forwards
the call unchanged and records the key set of its quote argument. Fixed clock
via the existing regime `computed_at_utc` fixture; any residual volatile keys
are stripped by a named allowlist asserted to contain only timestamp/id keys.
Runs:
- A: `_fetch_observe_only_quotes -> {}`.
- B: `-> ` all 12 extras with extreme values (price 1e6, pct +0.95) PLUS
  injected `"SPY"` (price 1.0, pct -0.99) and `"ZZZ"`.
- C: `-> raise RuntimeError`.
- D (unit, not paired): `fetch_quote` stub that advances a patched monotonic
  clock by 30 s per call; assert only 3 symbols were requested and no raise.
Assert A == B == C on: captured notification (title, body); files
`latest_hourly_contract.json`, `latest_hourly_run.json`,
`latest_hourly_payload.json`, `latest_hourly_market_map.json`; every spy's
recorded key set (none contains any `_OBSERVE_ONLY_FETCH` symbol or `ZZZ`);
the returned RunResult dict. Assert in B: the watchlist mapping contains the
12 extras, its `SPY` equals the decision SPY, and `ZZZ` is absent. Ordering
proof: a shared call log shows every observe-symbol `fetch_quote` call after
both `send_notification` and `_write_hourly_artifacts`. Static guards: the
runtime source references `_fetch_observe_only_quotes(` exactly once outside its
definition (the watchlist call site); `config.ALL_SYMBOLS`, `REQUIRED_SYMBOLS`,
`HALT_SYMBOLS`, `NON_TRADABLE_SYMBOLS`, `TREND_STRUCTURE_SYMBOLS` equal frozen
literal values captured at this head.

### 3.11 UI groups
Four rows in `MARKET MOVEMENT`, inside the existing MARKET STRUCTURE block:
MARKET (2 chips), SECTORS (11), METALS (3), MEGACAPS (6). No personal row, no
sorting, no badges, no CSS change. Browser matrix: 360x780, 390x844, 1440x900;
full / one-null / all-null / rejected snapshots; assert no horizontal overflow
and no intra-chip line break (use DevTools device metrics per the repo's
headless-Chrome viewport note, not `--window-size`).

### 3.12 Production file fence (FIVE files; `dashboard_renderer.py` removed)
1. `cuttingboard/universe_registry.py` -- shape (3.1), rows (3.2), docstring (F6/F9).
2. `cuttingboard/watchlist_sidecar.py` -- projections, validation, v3 producer (3.5/3.6/3.8).
3. `cuttingboard/config.py` -- delete `OBSERVE_ONLY_SYMBOLS` + comment; nothing else.
4. `cuttingboard/runtime/__init__.py` -- `_OBSERVE_ONLY_FETCH`, budget, filtered
   fetch (3.7); the call-site comment updated; no other edit.
5. `cuttingboard/delivery/movement_card.py` -- v3 admission, groups, chip
   rendering (3.9).
Any other production file (ingestion.py, dashboard_renderer.py,
market_state_panel.py, workflows) is a STOP + fence amendment.
Test files: `tests/test_universe_registry.py`, `tests/test_watchlist_sidecar.py`,
`tests/test_movement_card.py`, `tests/test_observe_only_isolation.py`,
`tests/test_dashboard_renderer.py` (fixture + "UCO" assertion only),
`tests/test_market_state_panel.py` (22-row model). Docs: `docs/universe_taxonomy.md`
(OBSERVE_ONLY section), `docs/SCHEMA_MAP.md` (watchlist_snapshot),
`docs/artifact_flow_map.md` (universe constant). Estimated net production LOC:
150-250 (registry rows dominate); propose Gate A cap 250.

### 3.13 Required tests (discriminating; each mutation in section 6 must redden at least one)
REGISTRY: literal 22/11/12 tuples; all 11 sectors; TSLA disabled; AAPL/MSFT
measurement-not-personal; UCO personal-not-measurement; every benchmark literal;
legacy `trade_eligible` values preserved and new rows False; validation rules
1-5 each raise on a constructed bad tuple; sole production importer is the
sidecar; no module reads `.trade_eligible`.
SIDECAR: v3 envelope exact keys; exactly 22 rows in order; UCO/TSLA absent;
missing quote -> nulls; honest zero; unrequested quotes ignored; byte-determinism;
naive datetime raises; legacy `sector_theme`/`watch_reason` absent.
OBSERVE-ONLY: literal 12-tuple; disjointness from all five config lists;
mismatched `nq.symbol` dropped; injected SPY/ZZZ dropped; partial / all / raised
failures best-effort; budget test D; HALT skips fetch and write.
MOVEMENT CARD: v2 and wrong source rejected; missing/extra/duplicate/injected
row rejected; missing `daily_change_pct` key rejected while explicit null
accepted; bool/int/NaN/Inf rejected; 22 chips in 4 groups, stable order; no UCO
or TSLA; all-null accepted with 22 `n/a`; chip HTML has no breakable space
inside a chip; no clock substrings in source.
RENDERER / PANEL: valid v3 -> `22/22 captured`; one null -> `21/22`; all null
-> `0/22`; invalid -> `not captured`; baseline-neutral outside the block.
DECISION INVARIANCE: section 3.10 A/B/C paired runs + static guards.

---------------------------------------------------------------------------

## 4. PROVIDER / TIMING RULING (the 2 -> 13 expansion)

Ruling: **current mechanism acceptable WITH an in-fence bounded correction;
universe NOT reduced; no separate provider/ingestion slice required before
rollout.**

Basis:
- Measured nominal cost of the identical mechanism in CI is ~0.2 s/symbol
  (two live-pipeline job logs) and ~0.4 s/symbol from this box (12-symbol live
  trial, 4.76 s total, all succeeded). The expansion adds ~3-5 s to a run whose
  decision loop already performs 33 sequential fetches; after the UCO cut the
  extra set is 12, not 13.
- The mechanism's per-symbol worst case is NOT bounded by the 10 s config
  timeout (executor exit waits). Today this unbounded exposure already applies
  to the 31-symbol decision loop; the design must not make it materially worse.
- Isolation of the quotes is structural, but wall clock is shared: the fetch
  precedes the dashboard publish and A1-P producer of the current run and, via
  the workflow concurrency group with no job timeout, can delay the next
  slot's alert. That is the coupling the budget removes.
- Correction: `_OBSERVE_ONLY_FETCH_BUDGET_SECONDS = 60.0` checked before each
  symbol, stop-not-raise on breach (section 3.7). Worst incremental exposure
  becomes budget + one symbol (~6 min pathological), inside the hourly cadence;
  nominal unchanged (~5 s).
- Batching: yfinance exposes `yf.download([...])` / `yf.Tickers`, and the repo
  already uses single-symbol `yf.download` for bars, but no batched quote seam
  exists in `ingestion.py`; adopting one is a provider/ingestion change with its
  own normalization parity questions. Classified as an authority/scope decision
  for a later PRD, NOT needed for this rollout, NOT to be smuggled into the fence.
- Failure stays best-effort per symbol (unchanged), and all-provider failure
  yields 12 `n/a` chips, never fabricated movement.
- Rollout evidence Opus must record in the PR: one local live invocation of
  `_fetch_observe_only_quotes()` with per-symbol and total elapsed, and the
  budget test D green.

Owner decision required on timing: NONE. Optional owner hygiene (F14): a
`timeout-minutes` on the hourly job, outside this fence.

---------------------------------------------------------------------------

## 5. SCOPE CONTROL CHECK

No NS-4C arithmetic, ranking, comparison rendering, or thresholds; no NS-4D
counts/labels; no persistence/history/scores; no trade-eligibility change; no
decision/regime/qualification/permission/execution edit; no provider or
workflow edit. `benchmark_symbol` in the registry is authored data the owner
listed for ratification, exposed as an inert projection; NS-4C will be the
first reader. The words LEADERS / LEADERSHIP do not appear in code or labels.

---------------------------------------------------------------------------

## 6. HIGHEST-VALUE RED MUTATIONS (Opus proves each reddens, then restores)

| # | Mutation | Must redden |
|---|---|---|
| M1 | append `_OBSERVE_ONLY_FETCH` to `config.ALL_SYMBOLS` | frozen-literal ALL_SYMBOLS test; disjointness test; `test_phase1` len==31 |
| M2 | card expects all ENABLED registry rows (23) instead of the measurement projection | literal-22 card test; UCO-absent test |
| M3 | drop XLC from the registry | literal 22-tuple; all-11-sectors test |
| M4 | card drops the exact key-set check | injected-row rejection test |
| M5 | sidecar coerces missing quote to 0.0 | honest-null test |
| M6 | runtime merges extras into `normalized_quotes` before `validate_quotes` | paired-run A/B equality; spy key sets |
| M7 | sidecar serializes personal-only UCO | exact-22-keys test; card rejects |
| M8 | TSLA `enabled=True` | disabled-TSLA test; literal tuples |
| M9 | XLK benchmark -> "XLZ"; SPY benchmark -> "SPY" | validation rule 4 tests |
| M10 | remove the budget check | test D |
| M11 | drop the `nq.symbol == sym` filter / key filter | injected-SPY-override test |
| M12 | card accepts `schema_version == 2` | version rejection test |

---------------------------------------------------------------------------

## OPUS IMPLEMENTATION CONTRACT

AUTHORITY: IMPLEMENT, only after Helm grants Gate A on the successor PRD that
adopts this section verbatim (MATERIAL; GOV-2 reviewer seats per Helm). Basis:
this review at its commit SHA + PRD-337 successor. Branch:
`claude/prd-337-ns4c-leadership-v0` (persistent worktree
`/home/dustin/Projects/cuttingboard/.claude/worktrees/prd-337-ns4c-leadership-v0`);
no /tmp worktrees. Never merge; PR #325 stays draft.

FENCE (production, exactly five): `cuttingboard/universe_registry.py`,
`cuttingboard/watchlist_sidecar.py`, `cuttingboard/config.py` (deletion only),
`cuttingboard/runtime/__init__.py` (fetch seam only),
`cuttingboard/delivery/movement_card.py`. Tests: the six files in 3.12. Docs:
the three files in 3.12. Anything else = STOP.

ORDER (commit per step; ruff + targeted pytest at each):
1. Freeze baselines: add literal tests for `config.ALL_SYMBOLS` (31),
   `REQUIRED_SYMBOLS`, `HALT_SYMBOLS`, `NON_TRADABLE_SYMBOLS`,
   `TREND_STRUCTURE_SYMBOLS`; add the RED literal tests for the 22/11/12
   tuples and registry validation; confirm they fail.
2. Registry: shape 3.1, rows 3.2, docstrings F6/F9. Sidecar: `validate_registry`
   (3.6) called at import, projections 3.5, v3 producer 3.8. Delete
   `WATCHLIST_SYMBOLS` / theme map. Green: registry + sidecar tests.
3. Runtime: `_OBSERVE_ONLY_FETCH`, budget constant, filtered best-effort loop
   (3.7); delete `config.OBSERVE_ONLY_SYMBOLS`. Green: isolation unit tests,
   budget test D, paired-run A/B/C (3.10) with real decision stages.
4. Movement card: v3 admission (3.9), group order, `&nbsp;` chip rendering.
   Update `test_movement_card`, `test_dashboard_renderer` fixture, and
   `test_market_state_panel` 22-row model. Green.
5. Browser matrix (3.11) in the worktree; record evidence paths in the PR.
6. Docs: `universe_taxonomy.md` OBSERVE_ONLY section (ownership -> runtime
   derivation from the measurement projection), `SCHEMA_MAP.md` watchlist v3,
   `artifact_flow_map.md` universe constant.
7. Mutations M1-M12: apply, observe red, restore, note results in the PR body.
8. Full gate: `ruff check .`, `python tools/validate_prd_registry.py`,
   `pytest -q` (venv, package resolving to the worktree), plus one local live
   `_fetch_observe_only_quotes()` timing record. Any unexplained failure = STOP.
9. Commit/push on this lineage; request fresh-context exact-head review; return
   to Helm with `Held for your merge`.

INVARIANTS THAT MUST HOLD AT THE FINAL HEAD:
- `MARKET_STRUCTURE_SYMBOLS` == the 22 in 3.2 order; `PERSONAL_SYMBOLS` == the
  11 in 3.3; `_OBSERVE_ONLY_FETCH` == the 12 in 3.7.
- `config.ALL_SYMBOLS`, `REQUIRED_SYMBOLS`, `HALT_SYMBOLS`, `NON_TRADABLE_SYMBOLS`,
  `TREND_STRUCTURE_SYMBOLS` byte-identical to head 8c403bb4.
- `universe_registry` has exactly one production importer (`watchlist_sidecar`);
  `watchlist_sidecar` is imported only by `runtime` (writer seam) and
  `movement_card`.
- No production module reads `.personal`, `.trade_eligible`, or
  `BENCHMARK_BY_SYMBOL`.
- `_fetch_observe_only_quotes(` appears once outside its definition, at the
  watchlist write under the non-HALT guard.
- Carrier rows: exactly 22, exact five keys each; nulls never coerced.
- Coverage renders `k/22 captured`; suppressed -> `not captured`.

NOT AUTHORIZED: any relative-move arithmetic; any LEADING/LAGGING/INLINE label;
breadth counts; persistence; provider/ingestion/workflow edits; renderer edits;
changes to any decision list; auto-merge.
