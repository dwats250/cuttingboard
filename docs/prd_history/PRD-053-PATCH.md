# PRD-053 PATCH — Market Map Input Plumbing + Usefulness Calibration

STATUS
READY

GOAL
Keep the PRD-053 market map sidecar isolated, but make `logs/market_map.json` produce useful graded visibility when existing runtime data is already available.

PROBLEM
PRD-053 is structurally correct but not useful enough for trader-facing review. Fixture/runtime output can grade all primary symbols `F` with empty `watch_zones` and null `fib_levels` because primary-symbol OHLCV and intraday inputs are not consistently retained and passed into the market-map builder.

SCOPE
- Retain and pass deterministic primary-symbol OHLCV windows into the market-map builder when already fetched or otherwise available in runtime.
- Retain and pass intraday metrics for primary symbols when already available in runtime.
- Add a fixture/test path with populated derived, structure, intraday, and OHLCV inputs so output is not all `F`.
- Fix defensive missing-data handling so malformed or mocked derived input degrades to `F` / `DATA_UNAVAILABLE` instead of crashing.
- Populate `watch_zones` from existing VWAP, EMA, ORB, PDH/PDL, prior high, and prior low data when available.
- Populate `fib_levels` from a deterministic bar window when available.
- Preserve `F` only for truly unavailable or structurally invalid data.

OUT OF SCOPE
- Dashboard changes
- Alert or notification changes
- Contract schema changes
- Payload schema changes
- Trade decision changes
- Execution policy changes
- Qualification changes
- New gates or trade blocking logic
- New data providers
- New fetches
- Paper trading or execution simulation

FILES
M `cuttingboard/market_map.py`
M `cuttingboard/runtime.py`
M `tests/test_market_map.py`
M `tests/test_operationalization.py`
M `docs/PRD_REGISTRY.md`

---

REQUIREMENTS

R1 — Sidecar-only boundary remains intact
The patch MUST keep PRD-053 sidecar-only. The market map may write only `logs/market_map.json`.

FAIL:
- Contract fields change.
- Payload fields change.
- Dashboard output changes.
- Alerts or notification text changes.
- `trade_candidates`, `trade_decisions`, execution policy, or qualification outputs change.

---

R2 — Existing data only
The patch MUST use only data already available through runtime or test fixtures.

Allowed inputs:
- normalized quotes
- derived metrics
- structure results
- intraday metrics
- regime state
- watch summary
- already available OHLCV/bar windows

FAIL:
- `market_map.py` imports or calls ingestion functions.
- Runtime adds a new provider or new market-data fetch solely for market-map output.
- Cache refresh behavior changes for the sidecar.

---

R3 — Primary-symbol OHLCV plumbing
Runtime MUST retain and pass deterministic OHLCV/bar windows for primary market-map symbols when those windows are already available in the run.

Primary symbols:
- `SPY`
- `QQQ`
- `GDX`
- `GLD`
- `SLV`
- `XLE`

FAIL:
- Existing primary-symbol bar windows are discarded before market-map construction.
- A symbol with an available deterministic bar window still emits `fib_levels: null`.
- Runtime fetches a new bar window only for market-map construction.

---

R4 — Intraday metrics plumbing
Runtime MUST pass available primary-symbol intraday metrics into the market-map builder.

FAIL:
- Existing primary-symbol intraday metrics are dropped before market-map construction.
- A symbol with available VWAP/ORB/PDH/PDL metrics emits empty `watch_zones`.

---

R5 — Useful fixture coverage
Tests MUST include a deterministic fixture/builder path with populated:
- normalized quote
- derived metrics
- structure result
- intraday metrics
- OHLCV/bar window

That fixture MUST prove at least one primary symbol grades above `F`.

FAIL:
- All fixture primary symbols grade `F`.
- The test only validates unavailable-data behavior.

---

R6 — Watch zone usefulness
When deterministic level data exists, `watch_zones` MUST include at least one object with:
- `type`
- `level`
- `context`

Allowed level sources:
- VWAP
- EMA9
- EMA21
- EMA50
- ORB_HIGH
- ORB_LOW
- PRIOR_HIGH
- PRIOR_LOW

FAIL:
- Deterministic level data exists but `watch_zones` is empty.
- A watch-zone level is non-numeric.
- A watch zone is invented from unavailable data.

---

R7 — Fibonacci usefulness
When a deterministic bar window exists, `fib_levels` MUST be populated with:
- `source`
- `swing_high`
- `swing_low`
- `retracements.0.382`
- `retracements.0.5`
- `retracements.0.618`

Swing selection MUST be mechanical, such as high/low over the fixed input window.

FAIL:
- Deterministic bars exist but `fib_levels` is null.
- Fib values are subjective, random, or manually seeded.
- Fib values are computed from fetched data unavailable to the builder input.

---

R8 — Defensive missing-data behavior
Malformed, mocked, or incomplete derived input MUST degrade to:
- `grade: "F"`
- `setup_state: "DATA_UNAVAILABLE"`
- a deterministic `reason_for_grade`

The builder MUST NOT raise `AttributeError` for missing derived attributes.

FAIL:
- A mocked derived object crashes the builder.
- Missing derived attributes produce fabricated grades above `F`.

---

R9 — Grade calibration
`F` MUST be reserved for truly unavailable or structurally invalid data.

If quote, derived, structure, and deterministic level data are available, the symbol MUST receive a grade based on those inputs rather than defaulting to `F`.

FAIL:
- Valid complete inputs still produce `F`.
- All valid primary symbols collapse to the same unavailable-data output.

---

R10 — Determinism
The same fixture run MUST produce identical `market_map.json` except explicitly allowed timestamp fields.

Allowed timestamp fields:
- `generated_at`
- `source.run_at_utc`

FAIL:
- Symbol ordering changes.
- Watch-zone ordering changes.
- Grades or guidance strings differ for identical inputs.
- Randomness or wall-clock logic affects non-timestamp fields.

---

R11 — Existing artifact isolation
The patch MUST not mutate existing artifacts or user-facing outputs. The sidecar file `logs/market_map.json` is the only artifact this patch may add or replace, and it is excluded from this existing-artifact failure check.

The following MUST remain unchanged for equivalent fixture input:
- `logs/latest_contract.json`
- `logs/latest_payload.json`
- dashboard output
- notification output
- markdown report content
- `trade_candidates`
- `trade_decisions`
- execution policy state
- qualification results

FAIL:
- Any existing artifact changes because of market-map plumbing.
- Existing tests need contract/payload/dashboard expectation changes for this patch.

---

VALIDATION

Automated:
- `python3 -m pytest tests/test_market_map.py -q`
- `python3 -m pytest tests/test_operationalization.py -q`
- `python3 -m pytest tests/ -q`

Required test evidence:
- At least one valid fixture symbol grades above `F`.
- At least one valid fixture symbol has a populated `watch_zones` list.
- At least one valid fixture symbol has populated `fib_levels` from a fixed OHLCV window.
- Missing or malformed derived input returns `F` / `DATA_UNAVAILABLE`, not an exception.
- Same fixture run twice produces identical market-map content except allowed timestamp fields.
- Existing contract, payload, dashboard, alerts, decisions, policy, and qualification behavior remain unchanged.

MANUAL AUDIT
- Run the deterministic fixture path twice.
- Confirm `logs/market_map.json` is valid JSON.
- Confirm graded symbols are exactly `SPY`, `QQQ`, `GDX`, `GLD`, `SLV`, `XLE`.
- Confirm `USO` is not graded.
- Confirm at least one primary symbol is above `F` when valid fixture inputs exist.
- Confirm `watch_zones` and `fib_levels` are populated when deterministic inputs exist.
- Confirm no forbidden language appears: `NO_TRADE`, `STAY_FLAT`, `BLOCKED`, `REJECTED`.
- Confirm existing output artifacts are unchanged except for `logs/market_map.json`.
