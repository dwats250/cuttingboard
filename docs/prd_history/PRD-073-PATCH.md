# PRD-073-PATCH — Renderer Boundary Test

**Status:** IN PROGRESS
**Patches:** PRD-073 (R4)
**Root cause:** missing fail condition

---

## ROOT CAUSE

`missing fail condition` — PRD-073 R4 requires the server renderer to never read `contract.json` or reference `contract.py`, but provides no test requirement that would catch a violation. Behavioral checks for "Actionable"/"Blocked" labels are insufficient: they only observe output, not the input boundary.

---

## GOAL

Add an explicit test requirement to PRD-073 R4 that proves `dashboard_renderer.py` does not access `logs/latest_contract.json` or `contract.py` by any means.

---

## SCOPE

- Add a new FAIL condition to PRD-073 R4 (pre-implementation; no code exists yet)
- Add corresponding test requirements to PRD-073 VALIDATION section
- No new files; the test itself lives in `tests/test_dashboard_renderer.py` (already in PRD-073 FILES)

---

## OUT OF SCOPE

- No changes to `contract.py`, `runtime.py`, any delivery module, policy logic, regime logic, or trade decision logic
- No changes to any file outside PRD-073's FILES list
- No behavioral logic changes to `dashboard_renderer.py`

---

## FILES

- M `docs/prd_history/PRD-073.md`
- M `docs/PRD_REGISTRY.md`

---

## REQUIREMENTS

### R4-PATCH — Renderer boundary isolation test

The test suite for `dashboard_renderer.py` MUST include tests that:

1. **Contract file access:** Patch `builtins.open` (or equivalent) to assert `logs/latest_contract.json` is never opened during any render call. The test fails if that path is accessed.
2. **Contract module import:** Assert that `contract` is not present in `dashboard_renderer`'s module namespace (`dir()`, `vars()`, or `sys.modules` inspection). The test fails if `contract.py` is imported by the renderer.
3. **Input boundary:** Assert that the render function only consumes arguments explicitly passed into it. No global file reads, no implicit artifact loading.

Existing behavioral checks (asserting "Actionable"/"Blocked" do not appear) are kept but are not sufficient to satisfy this requirement on their own.

FAIL: Test suite passes even when `logs/latest_contract.json` is opened during a render call.
FAIL: Test suite passes even when `contract.py` is imported by `dashboard_renderer.py`.
FAIL: Render function accesses any file path not explicitly passed as an argument or fixture.

---

## FAIL CONDITIONS

- Test suite passes when `logs/latest_contract.json` is opened during render.
- Test suite passes when `contract` module is present in `dashboard_renderer`'s namespace.
- Render function reads files beyond those passed into it without test detection.

---

## VALIDATION

```
python3 -m pytest tests/test_dashboard_renderer.py -q
python3 -m pytest tests/ -q
grep -n "contract" cuttingboard/delivery/dashboard_renderer.py
```

Expected: `grep` returns no hits. If any hit appears, implementation must be revised before merge.

---

## COMMIT PLAN

```
git add docs/prd_history/PRD-073.md docs/prd_history/PRD-073-PATCH.md docs/PRD_REGISTRY.md
git commit -m "PRD-073-PATCH: renderer boundary test — explicit contract isolation requirement for R4"
```
