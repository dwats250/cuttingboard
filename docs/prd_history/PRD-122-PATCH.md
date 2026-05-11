# PRD-122-PATCH — Payload validator must permit optional oil driver

## STATUS
PATCH

## CLASS
PATCH

## TIER
T1

## LANE
STANDARD

## ROOT CAUSE
Hidden dependency. `cuttingboard/delivery/payload.py:_require_macro_drivers`
is a parallel shape-enforcer that duplicates the exact-set equality
`contract.assert_valid_contract` used to encode. PRD-122 relaxed the
contract-side validator via `_OPTIONAL_MACRO_DRIVERS` but did not surface
or update this payload-side duplicate. Live pipeline payload-write fails
with `ValueError: macro_drivers must have exact driver keys` whenever the
new `oil` driver is present in `contract.macro_drivers`.

## GOAL
Bring `_require_macro_drivers` into structural alignment with PRD-122
optional-driver semantics. Restore payload-write for the merged PRD-122
universe.

---

# FILES

```text
cuttingboard/delivery/payload.py
tests/test_payload_macro_drivers.py
docs/prd_history/PRD-122-PATCH.md
docs/PRD_REGISTRY.md
docs/PROJECT_STATE.md
```

---

# REQUIREMENTS

- **R1.** `_require_macro_drivers` requires every driver in
  `{"volatility", "dollar", "rates", "bitcoin"}` to be present and
  raises on absence. The `oil` driver is allowed but not required.
  Any driver key outside `{"volatility","dollar","rates","bitcoin","oil"}`
  raises.
  - **FAIL:** Validator raises when given exactly the four required
    drivers; OR raises when given the four required drivers plus a
    valid oil block; OR fails to raise when a required driver is
    missing; OR fails to raise when an unknown driver key is present.

- **R2.** Per-block expected field sets remain:
  `{"symbol","level","change_pct"}` for `volatility`/`dollar`/`bitcoin`/`oil`;
  `{"symbol","level","change_pct","change_bps"}` for `rates`. The
  finite-float check on numeric fields is unchanged.
  - **FAIL:** Any driver's expected field set differs from these.

- **R3.** Live pipeline run completes through payload-write without
  raising, given a successful contract-assembly run that includes a
  valid `oil` block in `contract.macro_drivers`.
  - **FAIL:** `python3 -m cuttingboard --mode live` halts at
    `_write_payload_artifacts` with `macro_drivers must have exact
    driver keys`.

- **R4.** `tests/test_payload_macro_drivers.py` exercises
  `_require_macro_drivers` directly with five focused cases:
  required four pass; required four plus oil pass; missing required
  driver raises; unknown extra driver raises; invalid oil field shape
  raises.
  - **FAIL:** Any of the five cases is unasserted, OR the tests do
    not exercise `_require_macro_drivers` directly.

---

# DATA FLOW

```
contract.macro_drivers  (may include "oil" per PRD-122)
  └─ build_report_payload → payload.macro_drivers
       └─ assert_valid_payload
            └─ _require_macro_drivers   ← patched: accepts optional oil
                 └─ runtime._write_payload_artifacts (succeeds)
                      └─ dashboard_renderer reads payload (OIL slot rendered)
```

---

# FAIL CONDITIONS

- `_require_macro_drivers` raises on a payload containing only the four
  required drivers.
- `_require_macro_drivers` raises on a payload containing the four
  required drivers plus a valid oil block.
- `_require_macro_drivers` fails to raise when a required driver is
  missing.
- `_require_macro_drivers` fails to raise when an unknown driver key
  (e.g. `"gold"`) is present.
- Live pipeline payload-write fails on macro_drivers shape again.

---

# VALIDATION

1. `python3 -m pytest tests/test_payload_macro_drivers.py -q`
2. `python3 -m pytest tests/test_dashboard_renderer.py
    tests/test_contract.py tests/test_contract_macro_drivers.py -q`
3. `python3 -m pytest tests -q`
4. `python3 -m cuttingboard --mode live` — must complete payload-write.
5. Re-render `ui/dashboard.html` and `ui/index.html`; confirm `OIL`
   slot appears in the macro tape when oil data is present.

---

# COMMIT PLAN

1. Single implementation commit: `PRD-122-PATCH: payload validator accepts optional oil driver`.
2. Backfill registry hash and PROJECT_STATE in a follow-up close commit.
